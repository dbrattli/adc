# Repository Guidelines

## Project Structure & Module Organization

This is a documentation-first repository for the Agent Decision Comments
convention. `README.md` is the canonical specification: it defines the five
directives, their format, scope, examples, review workflow, and current version.
`skills/adc/SKILL.md` is the compact operational convention. Skill-aware agents
install it directly; other adopting repositories copy it to `ADC.md`. Agents
read it on every task, so keep it short. Keep it consistent with the full
specification: every rule and example it states must match `README.md`, and both
files must carry the same specification version. `LICENSE` contains the MIT
license. `examples/` contains runnable inline Lean examples.
`tools/` contains the Python extractor and its tests.
Generated Lean views are disposable; do not commit them.
Keep other documentation at the repository root unless a larger collection
clearly warrants a focused directory such as `examples/`.

## Build, Test, and Development Commands

The specification produces no build artifact. Markdown linting is its primary CI
check. Run these commands before submitting a change:

- `npx --yes markdownlint-cli2@0.23.2 --config .markdownlint.jsonc "**/*.md"`
  runs the same linter version as CI.
- `npx --yes skills@latest add . --list` confirms that the skills CLI discovers
  the `adc` skill.
- `python3 -B -m unittest discover -s tools -v` checks the extractor.
  Set `LEAN` to a compiler path to include real Lean checks.
- `git diff --check` detects trailing whitespace and malformed patches.
- `rg '^#{1,6} ' README.md AGENTS.md skills/adc/SKILL.md` reviews the Markdown
  heading hierarchy.
- `git diff -- README.md AGENTS.md skills/adc/SKILL.md` gives a focused review
  of documentation changes.

Also render changed Markdown in a previewer and verify that fenced examples,
lists, and headings display correctly.

## Coding Style & Naming Conventions

Write concise Markdown with ATX headings (`## Heading`), fenced code blocks
with language tags, and hyphenated bullets. Follow the existing prose style:
short paragraphs, direct present-tense statements, and one sentence per line
when practical. Use the exact lowercase directive labels `decision:`,
`invariant:`, `assumption:`, `tradeoff:`, and `lean:`. Examples should demonstrate
non-obvious rationale rather than restate code behavior. The Markdownlint
configuration excludes code blocks from `MD013`; directives must remain on one
physical line. In docstrings and documentation comments, place normal prose
before the directives with a blank line between them. Use ordinary comments for
directive-only examples.

## Testing Guidelines

The workflow in `.github/workflows/markdownlint.yml` lints every Markdown file
and runs extractor tests on Linux and Windows on pushes and pull requests.
Confirm new examples match the format and scope rules in `README.md`, use valid
syntax for their declared language, and agree with `skills/adc/SKILL.md`.
Run linting, skill discovery, extractor tests, and `git diff --check`, then
inspect the rendered output.

## Commit & Pull Request Guidelines

Recent history uses a Conventional Commit-style subject (`chore: Initial
version`); prefer concise imperative subjects such as `docs: clarify comment
scope`. Keep each commit focused. Pull requests should explain the motivation,
identify affected sections, and call out changes to directive semantics or
examples. For specification changes, state the intended Semantic Versioning
impact; repository-only maintenance does not require a version bump. Link
relevant issues when available. Screenshots are useful only when rendered
Markdown layout changes materially.
