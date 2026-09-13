# Apply automatic Markdown fixes using the repository lint configuration.
format:
    npx --yes markdownlint-cli2@0.23.2 --config .markdownlint.jsonc --fix "**/*.md"
