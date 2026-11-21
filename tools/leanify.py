"""Turn source comments into a Lean compilation unit; optionally check it."""

import argparse
import os
import re
import subprocess
import sys
import tokenize
from pathlib import Path

from lean_extraction import Extraction, extract


def remap_diagnostics(
    text: str, source: Path, generated: Path, extraction: Extraction
) -> str:
    location = re.compile(r"(?m)^" + re.escape(str(generated)) + r":(\d+):(\d+):")

    def remap(match: re.Match) -> str:
        line, column = map(int, match.groups())
        offset = (
            extraction.lines[line - 1].offset
            if 0 < line <= len(extraction.lines)
            else 0
        )
        return f"{source}:{line}:{column + offset}:"

    return location.sub(remap, text)


def check_lean(source: Path, generated: Path, extraction: Extraction) -> int:
    executable = os.environ.get("LEAN") or "lean"
    # decision: inspects nonzero exits to remap compiler diagnostics to editable source
    result = subprocess.run(
        [executable, "-DwarningAsError=true", str(generated)],
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
    )
    print(remap_diagnostics(result.stdout, source, generated, extraction), end="")
    print(
        remap_diagnostics(result.stderr, source, generated, extraction),
        end="",
        file=sys.stderr,
    )
    return result.returncode


def run() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument(
        "--check", action="store_true", help="run Lean and remap diagnostics"
    )
    args = parser.parse_args()
    source = args.source.resolve()
    output = args.output.resolve()
    if output.suffix != ".lean" or source == output:
        raise ValueError("Output must be a separate .lean file")
    extraction = extract(source)
    output.write_text(
        "\n".join(line.text for line in extraction.lines) + "\n", encoding="utf-8"
    )
    print(
        f"Extracted {extraction.blocks} Lean blocks and "
        f"{extraction.inline_lines} lean: comments to {output}"
    )
    if args.check:
        return check_lean(source, output, extraction)
    return 0


if __name__ == "__main__":
    try:
        sys.exit(run())
    except (OSError, ValueError, tokenize.TokenError, IndentationError) as error:
        print(error, file=sys.stderr)
        sys.exit(1)
