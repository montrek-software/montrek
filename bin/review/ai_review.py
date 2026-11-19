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
# Changed files are inlined in full up to these sizes, so the model does not
# spend rounds reading them; larger ones it reads with read_file.
MAX_INLINED_FILE_CHARS = 30_000
MAX_INLINED_FILES_CHARS = 120_000
REVIEW_START = "## Summary"
# From this share of the round or token budget on, the model is asked to wrap up.
WRAP_UP_SHARE = 0.6
# HTTP statuses with which an API rejects a request it does not support.
REJECTED_STATUSES = {400, 422}


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
            help="stop exploring once this many input tokens are spent; a cached "
            "token counts with its share of the price (a tenth on Mistral)",
        )
        parser.add_argument("--output", type=Path, help="write the review here")
        parser.add_argument(
            "--dry-run", action="store_true", help="print the prompt, call no API"
        )
        parser.add_argument("--list-models", action="store_true")
        return parser.parse_args(argv)

    def run(self) -> str:
        client = self.provider.client(self.options.model)
        self.started = time.monotonic()
        messages: list[dict[str, Any]] = [
            {"role": "system", "content": PROMPT_FILE.read_text()},
            {"role": "user", "content": self.prompt()},
        ]
        effort = f", reasoning effort {client.reasoning_effort}"
        self.log(
            f"Reviewing {self.options.repo} {self.scope.merge_base[:8]}.."
            f"{'worktree' if self.options.worktree else self.scope.head} "
            f"with {client.model}{effort if client.reasoning_effort else ''}: "
            f"{len(self.scope.changed_files)} files, "
            f"{len(self.tools.files)} visible"
        )
        for round_number in range(1, self.options.max_rounds + 1):
            message = self.chat(client, messages, round_number)
            tool_calls = message.get("tool_calls") or []
            if not tool_calls:
                return self.finish(client, ChatClient.text_of(message.get("content")))
            # The content goes back unchanged: reasoning models need their
            # thinking parts in the history, or they reason it all out again.
            messages.append(
                {
                    "role": "assistant",
                    "content": message.get("content") or "",
                    "tool_calls": tool_calls,
                }
            )
            for index, call in enumerate(tool_calls):
                function = call["function"]
                self.log(
                    f"  [{round_number}] {function['name']} {function['arguments']}"
                )
                output = self.tools.execute(function["name"], function["arguments"])
                if index == len(tool_calls) - 1:
                    output += self.budget_note(client, round_number)
                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": call["id"],
                        "name": function["name"],
                        "content": output,
                    }
                )
            if self.spent_tokens(client) >= self.options.max_input_tokens:
                self.log("  Input token budget reached.")
                break
        else:
            self.log(f"  Round limit ({self.options.max_rounds}) reached.")
        return self.finish(client, self.forced_review(client, messages))

    def forced_review(self, client: ChatClient, messages: list[dict[str, Any]]) -> str:
        """The review after exploration was cut off.

        The answer is prefilled with the start of the required structure, so
        the model cannot reply with narration instead of the review. An API
        without assistant prefixes gets asked again when it narrates.
        """
        messages.append(
            {
                "role": "user",
                "content": "Stop exploring. Write the review now, in the required "
                "structure, from what you have verified so far.",
            }
        )
        prefix = {"role": "assistant", "content": REVIEW_START, "prefix": True}
        try:
            message = self.chat(client, [*messages, prefix], 0, tool_choice="none")
        except ChatClientError as error:
            if error.status not in REJECTED_STATUSES:
                raise
            self.log(f"  Assistant prefix rejected ({error.status}), asking plainly.")
        else:
            content = ChatClient.text_of(message.get("content")).lstrip()
            # Whether the answer repeats the prefix is not documented.
            return (
                content
                if content.startswith(REVIEW_START)
                else REVIEW_START
                + (content if content.startswith("\n") else "\n" + content)
            )
        message = self.chat(client, messages, 0, tool_choice="none")
        content = ChatClient.text_of(message.get("content"))
        if REVIEW_START not in content:
            # The forced answer can still be narration ("let me check one
            # more thing"); ask once more for the review itself.
            messages += [
                {"role": "assistant", "content": message.get("content") or ""},
                {
                    "role": "user",
                    "content": "That was not the review. Reply with the review "
                    f"only, starting with '{REVIEW_START}', in the required "
                    "structure.",
                },
            ]
            message = self.chat(client, messages, 0, tool_choice="none")
            content = ChatClient.text_of(message.get("content"))
        return content

    def budget_note(self, client: ChatClient, round_number: int) -> str:
        """Tells the model how much exploration is left, after a round's tools."""
        rounds = round_number / self.options.max_rounds
        tokens = self.spent_tokens(client) / self.options.max_input_tokens
        note = (
            f"\n\n[Review budget: round {round_number} of {self.options.max_rounds}, "
            f"{max(rounds, tokens):.0%} used.]"
        )
        if max(rounds, tokens) >= WRAP_UP_SHARE:
            note += (
                " Wrap up: only check what a finding you will report still "
                "depends on, then write the review."
            )
        return note

    def spent_tokens(self, client: ChatClient) -> float:
        """Input tokens so far, a cached one weighted with its share of the price."""
        cached = client.cached_tokens
        return (
            client.prompt_tokens - cached + cached * self.provider.cached_price_factor
        )

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
            f"{len(ChatClient.text_of(message.get('content'))):,} chars text, "
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
            "## Changed files in full\n" + self.inline_files(),
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

    def inline_files(self) -> str:
        """The changed files as they are now, with line numbers like read_file.

        Production code first: when the budget runs out, tests are what the
        model reads with read_file.
        """
        inlined: list[str] = []
        left_out: list[str] = []
        size = 0
        paths = sorted(
            self.scope.changed_files,
            key=lambda path: not self.scope.is_production_file(path),
        )
        for path in paths:
            if path not in self.scope.visible_files:
                continue
            text = (self.scope.project_root / path).read_text(errors="replace")
            lines = text.split("\n")
            numbered = "\n".join(
                f"{number:>5}  {line}" for number, line in enumerate(lines, start=1)
            )
            if (
                len(numbered) > MAX_INLINED_FILE_CHARS
                or size + len(numbered) > MAX_INLINED_FILES_CHARS
            ):
                left_out.append(path)
                continue
            inlined.append(
                f'<file path="{path}" lines="{len(lines)}">\n{numbered}\n</file>'
            )
            size += len(numbered)
        parts = inlined or ["(none small enough to inline)"]
        if left_out:
            parts.append(
                "Too large to inline; read the parts you need with read_file:\n"
                + "\n".join(f"- {path}" for path in left_out)
            )
        return "\n\n".join(parts)

    def finish(self, client: ChatClient, review: str) -> str:
        # Models sometimes narrate before the required structure starts.
        start = review.find(REVIEW_START)
        if start > 0:
            review = review[start:]
        usage = (
            f"AI review by `{client.model}` ({self.provider.name}) · "
            f"{client.prompt_tokens:,} input ({client.cached_tokens:,} cached) / "
            f"{client.completion_tokens:,} output tokens · {self.cost(client)} · "
            f"{self.elapsed()}"
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

    def elapsed(self) -> str:
        minutes, seconds = divmod(round(time.monotonic() - self.started), 60)
        return f"{minutes}m{seconds:02d}s"

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
