"""Review a branch of montrek or of an mt_* extension with an LLM.

Run it through ``make ai-review`` (see ``bin/review/ai-review.sh``); ``--help``
lists the options. Progress goes to stderr, the review to stdout or --output.
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path
from typing import Any

from chat_client import ChatClient, ChatClientError
from review_checks import ReviewChecks
from review_provider import ReviewProvider
from review_scope import CORE, ReviewScope, ReviewScopeError
from review_tools import ReviewTools

PROJECT_ROOT = Path(__file__).resolve().parents[2]
PROMPT_FILE = Path(__file__).with_name("review_prompt.md")
MAX_DIFF_CHARS = 80_000


class AiReview:
    def __init__(self, options: argparse.Namespace) -> None:
        self.options = options
        self.provider = ReviewProvider.from_environment()
        self.scope = ReviewScope(
            PROJECT_ROOT,
            repo=options.repo,
            base=options.base,
            include_worktree=options.worktree,
        )
        self.tools = ReviewTools(self.scope)
        self.checks = ReviewChecks(
            self.scope,
            run_tests=options.run_tests,
            coverage_xml=options.coverage_xml,
        )

    @classmethod
    def main(cls, argv: list[str] | None = None) -> int:
        options = cls.parse_arguments(argv)
        try:
            if options.list_models:
                client = ReviewProvider.from_environment().client(options.model)
                print("\n".join(client.list_models()))
                return 0
            review = cls(options)
            if not review.scope.diff.strip():
                print(
                    f"No changes between {options.base} and HEAD in {options.repo}.",
                    file=sys.stderr,
                )
                return 1
            if options.dry_run:
                print(review.prompt())
                return 0
            review.write(review.run())
        except (ReviewScopeError, ChatClientError) as error:
            print(f"Error: {error}", file=sys.stderr)
            return 2
        return 0

    @staticmethod
    def parse_arguments(argv: list[str] | None) -> argparse.Namespace:
        parser = argparse.ArgumentParser(description=__doc__)
        parser.add_argument(
            "--repo", default=CORE, help="'montrek' (core) or an mt_* extension"
        )
        parser.add_argument("--base", default="origin/main", help="target branch")
        parser.add_argument(
            "--worktree",
            action="store_true",
            help="also review uncommitted changes to tracked files",
        )
        parser.add_argument(
            "--run-tests",
            action="store_true",
            help="run the tests of the touched apps and measure patch coverage",
        )
        parser.add_argument(
            "--coverage-xml", type=Path, help="use an existing coverage.xml instead"
        )
        parser.add_argument(
            "--model", help="default: AI_REVIEW_MODEL, or the provider's default"
        )
        parser.add_argument("--max-rounds", type=int, default=25)
        parser.add_argument(
            "--max-input-tokens",
            type=int,
            default=800_000,
            help="stop exploring once this many input tokens are spent",
        )
        parser.add_argument("--output", type=Path, help="write the review here")
        parser.add_argument(
            "--dry-run", action="store_true", help="print the prompt, call no API"
        )
        parser.add_argument("--list-models", action="store_true")
        return parser.parse_args(argv)

    def run(self) -> str:
        client = self.provider.client(self.options.model)
        messages: list[dict[str, Any]] = [
            {"role": "system", "content": PROMPT_FILE.read_text()},
            {"role": "user", "content": self.prompt()},
        ]
        self.log(
            f"Reviewing {self.options.repo} {self.scope.merge_base[:8]}.."
            f"{'worktree' if self.options.worktree else self.scope.head} "
            f"with {client.model}: {len(self.scope.changed_files)} files, "
            f"{len(self.tools.files)} visible"
        )
        for round_number in range(1, self.options.max_rounds + 1):
            message = self.chat(client, messages, round_number)
            tool_calls = message.get("tool_calls") or []
            if not tool_calls:
                return self.finish(client, message.get("content") or "")
            messages.append(
                {
                    "role": "assistant",
                    "content": message.get("content") or "",
                    "tool_calls": tool_calls,
                }
            )
            for call in tool_calls:
                function = call["function"]
                self.log(
                    f"  [{round_number}] {function['name']} {function['arguments']}"
                )
                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": call["id"],
                        "name": function["name"],
                        "content": self.tools.execute(
                            function["name"], function["arguments"]
                        ),
                    }
                )
            if client.prompt_tokens >= self.options.max_input_tokens:
                self.log("  Input token budget reached.")
                break
        else:
            self.log(f"  Round limit ({self.options.max_rounds}) reached.")
        messages.append(
            {
                "role": "user",
                "content": "Stop exploring. Write the review now, in the required "
                "structure, from what you have verified so far.",
            }
        )
        message = self.chat(client, messages, 0, tool_choice="none")
        content = message.get("content") or ""
        if "## Summary" not in content:
            # The forced answer can still be narration ("let me check one
            # more thing"); ask once more for the review itself.
            messages += [
                {"role": "assistant", "content": content},
                {
                    "role": "user",
                    "content": "That was not the review. Reply with the review "
                    "only, starting with '## Summary', in the required structure.",
                },
            ]
            message = self.chat(client, messages, 0, tool_choice="none")
            content = message.get("content") or ""
        return self.finish(client, content)

    def chat(
        self,
        client: ChatClient,
        messages: list[dict[str, Any]],
        round_number: int,
        tool_choice: str = "auto",
    ) -> dict[str, Any]:
        """One request, logged with its own token counts and duration."""
        before = (client.prompt_tokens, client.cached_tokens, client.completion_tokens)
        started = time.monotonic()
        message = client.chat(
            messages, tools=self.tools.definitions, tool_choice=tool_choice
        )
        prompt, cached, completion = (
            client.prompt_tokens - before[0],
            client.cached_tokens - before[1],
            client.completion_tokens - before[2],
        )
        label = f"round {round_number}" if round_number else "final"
        self.log(
            f"  ({label}: {prompt:,} in, {cached:,} cached, {completion:,} out, "
            f"{len(message.get('content') or ''):,} chars text, "
            f"{time.monotonic() - started:.0f}s)"
        )
        return message

    def prompt(self) -> str:
        scope = self.scope
        target = (
            f"`{scope.repo}`, the extension at `montrek/{scope.repo}/`"
            if scope.repo != CORE
            else "`montrek` (core)"
        )
        visible = (
            f"Visible extensions besides core: {', '.join(scope.extensions)}."
            if scope.extensions
            else "Extensions (`montrek/mt_*`) are not visible in a core review."
        )
        parts = [
            "# Pull request to review",
            f"Repository: {target}. Target branch: `{scope.base}`. {visible}",
            "## Commits\n" + (scope.commits or "(uncommitted changes only)"),
            "## Project instructions\n" + self.rulebooks(),
            "## Check results\n" + self.checks.render(),
            "## Changed files\n"
            + "\n".join(f"- `{path}`" for path in scope.changed_files),
            "## Diff\n" + self.inline_diff(),
        ]
        return "\n\n".join(parts)

    def rulebooks(self) -> str:
        candidates = ["montrek/CLAUDE.md"]
        candidates += [f"montrek/{name}/CLAUDE.md" for name in self.scope.extensions]
        books = [
            f'<file path="{path}">\n{(PROJECT_ROOT / path).read_text()}\n</file>'
            for path in candidates
            if path in self.scope.visible_files
        ]
        books.append(
            "The acceptance criteria for code deliveries are in "
            "`CONTRIBUTION_CRITERIA.md`; read them when a change is borderline."
        )
        return "\n\n".join(books)

    def inline_diff(self) -> str:
        """The diff, file by file, until the size budget is used up."""
        chunks = self.scope.diff.split("\ndiff --git ")
        inlined: list[str] = []
        left_out: list[str] = []
        size = 0
        for index, chunk in enumerate(chunks):
            text = chunk if index == 0 else "diff --git " + chunk
            if size + len(text) > MAX_DIFF_CHARS:
                left_out.append(text.split("\n", 1)[0].removeprefix("diff --git "))
                continue
            inlined.append(text)
            size += len(text)
        diff = "```diff\n" + "\n".join(inlined) + "\n```"
        if left_out:
            diff += (
                "\n\nNot inlined because of size; read these with read_file:\n"
                + "\n".join(f"- {name}" for name in left_out)
            )
        return diff

    def finish(self, client: ChatClient, review: str) -> str:
        # Models sometimes narrate before the required structure starts.
        start = review.find("## Summary")
        if start > 0:
            review = review[start:]
        usage = (
            f"AI review by `{client.model}` ({self.provider.name}) · "
            f"{client.prompt_tokens:,} input ({client.cached_tokens:,} cached) / "
            f"{client.completion_tokens:,} output tokens · {self.cost(client)}"
        )
        self.log(usage)
        return f"{review.strip()}\n\n---\n_{usage}_\n"

    def cost(self, client: ChatClient) -> str:
        prices = self.provider.prices(client.model)
        if prices is None:
            return "cost unknown (set AI_REVIEW_PRICE_INPUT/_OUTPUT)"
        price_in, price_out = prices
        uncached = client.prompt_tokens - client.cached_tokens
        cost = (
            uncached * price_in
            + client.cached_tokens * price_in * self.provider.cached_price_factor
            + client.completion_tokens * price_out
        ) / 1_000_000
        return f"≈ {self.provider.currency}{cost:.2f}"

    def write(self, review: str) -> None:
        if self.options.output:
            self.options.output.write_text(review)
            self.log(f"Review written to {self.options.output}")
        else:
            print(review)

    @staticmethod
    def log(text: str) -> None:
        print(text, file=sys.stderr, flush=True)


if __name__ == "__main__":
    sys.exit(AiReview.main())
