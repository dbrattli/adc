"""Recognize Rust comments, keeping raw strings and nested comments distinct."""

import re

RUST_TOKEN = re.compile(
    r'(?P<raw>(?:br|cr|r)(?P<hashes>\#*)")'
    r'|(?P<string>"(?:[^"\\]|\\.)*")'
    r"|(?P<char>'(?:[^'\\\r\n]|\\(?:u\{[0-9a-fA-F_]+\}|x[0-9a-fA-F]{2}|.))')"
    r"|(?P<open>/\*)|(?P<line>//[^\r\n]*)"
    r"|(?P<space>\s+)|(?P<code>.)",
    re.DOTALL,
)
BLOCK_TOKEN = re.compile(r"/\*|\*/|.", re.DOTALL)
BLOCK_OPEN = "open"


def raw_string_end(token: re.Match, text: str) -> int:
    delimiter = '"' + token.group("hashes")
    end = text.find(delimiter, token.end())
    if end < 0:
        line = text.count("\n", 0, token.start()) + 1
        raise ValueError(f"{line}:1: Unclosed Rust raw string")
    return end + len(delimiter)


def rust_comments(text: str) -> list[bool]:
    """Mark comments; Rust block delimiters nest even within quoted comment text."""
    mask = [False] * len(text)
    position = 0
    depth = 0
    while position < len(text):
        token = (BLOCK_TOKEN if depth else RUST_TOKEN).match(text, position)
        assert token is not None
        position = token.end()
        if depth:
            mask[token.start() : position] = [True] * len(token.group())
            depth += (token.group() == "/*") - (token.group() == "*/")
        elif token.lastgroup in {BLOCK_OPEN, "line"}:
            mask[token.start() : position] = [True] * len(token.group())
            depth = int(token.lastgroup == BLOCK_OPEN)
        else:
            position = code_token_end(token, text)
    return mask


def code_token_end(token: re.Match, text: str) -> int:
    if token.lastgroup == "raw":
        return raw_string_end(token, text)
    if token.lastgroup == "code" and token.group() == '"':
        line = text.count("\n", 0, token.start()) + 1
        raise ValueError(f"{line}:1: Unclosed Rust string")
    return token.end()
