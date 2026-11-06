# AI review

`make ai-review` reviews a branch with an LLM, as a second opinion next to the
human review. It works for core and for any `mt_*` extension checked out under
`montrek/`. The output is a Markdown review: a summary, findings ranked by
severity with `path:line` and the code they are based on, older problems under
"Outside this change", and a verdict.

The model does not only see the diff. It explores the codebase with read-only
tools (`list_files`, `read_file`, `search`), so it can check callers, base
classes, tests and existing helpers before it reports anything.

## Usage

Run from the project root; `git fetch` first, the diff starts at the merge base
with `BASE`.

```bash
make ai-review                                  # core branch against origin/main
make ai-review REPO=mt_example                  # an extension's branch
make ai-review REPO=mt_example WORKTREE=true    # include uncommitted changes
make ai-review TESTS=true OUTPUT=review.md      # run the touched apps' tests first
make ai-review COVERAGE_XML=path/coverage.xml   # use a coverage report from CI
make ai-review DRY_RUN=true                     # print the prompt, call no API
make ai-review AI_REVIEW_PROVIDER=ionos         # use another provider
```

To review a merged pull request after the fact, check out its merge commit `M`
in the repository (`git switch --detach M`) and use `BASE=M^1`; that is the
diff the pull request brought in.

Progress goes to stderr: every tool call, and per round the input, cached and
output tokens and the duration. The last line is the usage and, when the price
is known, a cost estimate; the same line ends the review.

## Configuration

Set in `.env` or the environment:

| Variable | Meaning |
| --- | --- |
| `AI_REVIEW_PROVIDER` | `mistral` (default) or `ionos` |
| `MISTRAL_API_KEY` / `IONOS_API_TOKEN` | key of the chosen provider |
| `AI_REVIEW_MODEL` | model ID; default `mistral-large-4` (Mistral) or `Qwen/Qwen3-Coder-Next` (IONOS) |
| `AI_REVIEW_PRICE_INPUT`, `AI_REVIEW_PRICE_OUTPUT` | price per million tokens, for the cost estimate |
| `AI_REVIEW_BASE_URL` | another OpenAI-compatible endpoint for the provider |

`bin/review/ai-review.sh --list-models` lists the models of the provider, and
`--help` shows the remaining options, e.g.
`--max-rounds` (25) and `--max-input-tokens` (800 000), the limits after which
the model is told to write the review.

## What the model sees

- **Files:** only git-tracked files, so `.env`, `secrets/`, uploads and caches
  are never visible. A core review sees no extension code at all; an extension
  review sees core, the extension and the extensions it imports. Everything
  the model reads is sent to the provider.
- **Rules:** `montrek/CLAUDE.md`, and an extension's own `CLAUDE.md` if it has
  one. The review instructions and the output format are in
  `bin/review/review_prompt.md`; tune the review there.
- **Facts:** ruff on the changed files and, with `TESTS=true` or
  `COVERAGE_XML`, the changed production lines that no test covers. Measured
  facts are handed over because the model judges them well but measures them
  poorly.

## Choosing a model

Four models were compared on three diffs of an extension with known answers: an
accidentally pasted file path in a constant, four German typos in a contract
template, and a change without known errors.

| Model | Provider | Pasted path | Typos | False alarms | Notes |
| --- | --- | --- | --- | --- | --- |
| `mistral-large-4` | Mistral | found, with its consequences | 0 of 4 | none | thorough (about 40 tool calls), about 5 minutes per review, reasoning model |
| `mistral-medium-3-5` | Mistral | found | 0 of 4 | about 4 | |
| `Qwen/Qwen3.5-397B-A17B` | IONOS | found | 0 of 4 | about 3 | hosted in Germany |
| `Qwen/Qwen3-Coder-Next` | IONOS | found | 0 of 4 | about 5 | often reviews the diff without using tools |

`mistral-large-4` is the default: it was the only model whose findings held up
without checking each one. About 13 reviews with the Mistral models, five of
them with Large 4, cost €1.97 together, so a review costs cents to a few tens
of cents. Mistral caches the repeated part of the conversation
(`prompt_cache_key`), which is most of it; IONOS documents no prompt caching.

No model found the typos. Spelling and grammar in text-heavy changes still
need a human eye.
