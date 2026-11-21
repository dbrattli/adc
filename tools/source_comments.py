"""Recognize standalone comments without interpreting comment-like string contents."""

import io
import re
import tokenize
from pathlib import Path

from rust_comments import rust_comments

# decision: uses a bounded F# lexer to keep extraction independent of .NET
# Unsupported interpolation fails closed instead of guessing where its strings end.
FSHARP_TOKEN = re.compile(
    r'(?P<interpolation>\$+@?"|@\$+")'
    r'|(?P<triple>""".*?""")'
    r'|(?P<verbatim>@"(?:[^"]|"")*")'
    r'|(?P<string>"(?:[^"\\]|\\.)*")'
    r"|(?P<char>'(?:[^'\\\r\n]|\\(?:u[0-9a-fA-F]{4}|[0-9]{3}|.))')"
    r"|(?P<identifier>``[^\r\n]*?``)"
    r"|(?P<open>\(\*)|(?P<close>\*\))"
    r"|(?P<line>//[^\r\n]*)|(?P<space>\s+)|(?P<code>.)",
    re.DOTALL,
)

BLOCK_OPEN = "open"

COMMENT_TOKEN = re.compile(r'"(?:[^"\\]|\\.)*"|\(\*|\*\)|.', re.DOTALL)


def fsharp_comments(text: str) -> list[bool]:
    """Mark comment characters; reject ambiguous or unsupported string syntax."""
    mask = [False] * len(text)
    depth = 0
    position = 0
    while position < len(text):
        pattern = COMMENT_TOKEN if depth else FSHARP_TOKEN
        token = pattern.match(text, position)
        assert token is not None
        kind = token.lastgroup
        if depth:
            mask[token.start() : token.end()] = [True] * len(token.group())
            depth += (token.group() == "(*") - (token.group() == "*)")
        elif kind in {BLOCK_OPEN, "line"}:
            depth = int(kind == BLOCK_OPEN)
            mask[token.start() : token.end()] = [True] * len(token.group())
        else:
            reject_unsupported_token(token, text)
        position = token.end()
    return mask


def reject_unsupported_token(token: re.Match, text: str) -> None:
    if token.lastgroup == "interpolation":
        line = text.count("\n", 0, token.start()) + 1
        raise ValueError(
            f"{line}:1: F# interpolated strings are not supported by this extractor"
        )
    if token.lastgroup == "code" and token.group() == '"':
        line = text.count("\n", 0, token.start()) + 1
        raise ValueError(f"{line}:1: Unclosed F# string")


def python_comments(text: str) -> list[bool]:
    """Use Python's tokenizer; docstrings remain strings, not extraction markers."""
    offsets = [0]
    for line in text.splitlines(keepends=True):
        offsets.append(offsets[-1] + len(line))
    mask = [False] * len(text)
    for token in tokenize.generate_tokens(io.StringIO(text).readline):
        if token.type == tokenize.COMMENT:
            start = offsets[token.start[0] - 1] + token.start[1]
            end = offsets[token.end[0] - 1] + token.end[1]
            mask[start:end] = [True] * (end - start)
    return mask


def comment_lines(source: Path, text: str) -> list[bool]:
    match source.suffix.lower():
        case ".fs" | ".fsx" | ".fsi":
            mask = fsharp_comments(text)
        case ".rs":
            mask = rust_comments(text)
        case ".py":
            mask = python_comments(text)
        case _:
            raise ValueError("Supported source extensions: .fs, .fsx, .fsi, .py, .rs")
    result = []
    offset = 0
    for line in text.splitlines(keepends=True):
        result.append(
            all(ch.isspace() or mask[offset + i] for i, ch in enumerate(line))
        )
        offset += len(line)
    return result
