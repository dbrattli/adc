# Repository Guidelines

## Project Structure & Module Organization

This is a documentation-first repository for the Agent Decision Comments
convention. `README.md` is the canonical specification: it defines the four
directives, their format, scope, examples, review workflow, and current version.
`LICENSE` contains the MIT license. There are currently no source, test,
generated, or asset directories. Keep new documentation at the repository root
unless a larger collection clearly warrants a focused directory such as
`examples/`.

## Build, Test, and Development Commands

This repository produces no build artifact. Markdown linting is its primary CI
check. Run these commands before submitting a change:

- `npx --yes markdownlint-cli2@0.23.2 --config .markdownlint.jsonc "**/*.md"`
  runs the same linter version as CI.
- `git diff --check` detects trailing whitespace and malformed patches.
- `rg '^#{1,6} ' README.md AGENTS.md` reviews the Markdown heading hierarchy.
- `git diff -- README.md AGENTS.md` gives a focused review of documentation
  changes.

Also render changed Markdown in a previewer and verify that fenced examples,
lists, and headings display correctly.

## Coding Style & Naming Conventions

Write concise Markdown with ATX headings (`## Heading`), fenced code blocks
with language tags, and hyphenated bullets. Follow the existing prose style:
short paragraphs, direct present-tense statements, and one sentence per line
when practical. Use the exact lowercase directive labels `decision:`,
`invariant:`, `assumption:`, and `tradeoff:`. Examples should demonstrate
non-obvious rationale rather than restate code behavior. The Markdownlint
configuration excludes code blocks from `MD013`; directives must remain on one
physical line.

## Testing Guidelines

The workflow in `.github/workflows/markdownlint.yml` lints every Markdown file
on pushes and pull requests. Confirm every new example matches the format and
scope rules in `README.md`, uses valid syntax for its declared language, and
does not contradict another section. Run the local lint command and
`git diff --check`, then inspect the rendered output.

## Commit & Pull Request Guidelines

Recent history uses a Conventional Commit-style subject (`chore: Initial
version`); prefer concise imperative subjects such as `docs: clarify comment
scope`. Keep each commit focused. Pull requests should explain the motivation,
identify affected sections, and call out changes to directive semantics or
examples. For specification changes, state the intended Semantic Versioning
impact; repository-only maintenance does not require a version bump. Link
relevant issues when available. Screenshots are useful only when rendered
Markdown layout changes materially.
