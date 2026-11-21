"""Extract inline Lean and indented fences while retaining diagnostic offsets."""

import re
from dataclasses import dataclass, field
from pathlib import Path

from lean_blocks import Block, block_content, close_block, open_block
from source_comments import comment_lines


@dataclass(frozen=True)
class EmittedLine:
    text: str
    offset: int = 0


@dataclass
class Extraction:
    lines: list[EmittedLine] = field(default_factory=list)
    blocks: int = 0
    inline_lines: int = 0
    block: Block | None = None

    def append(self, number: int, line: str, comment: bool) -> None:
        if self.block is not None:
            self.append_block(line, comment)
            return
        code = INLINE.match(line) if comment else None
        if code:
            self.lines.append(inline_code(code))
            self.inline_lines += 1
            return
        if comment and line.strip() == "```lean":
            self.block = open_block(number, line)
        self.lines.append(EmittedLine("-- " + line))

    def append_block(self, line: str, comment: bool) -> None:
        assert self.block is not None
        if comment and line.strip() == "```":
            close_block(self.block, line)
            self.block = None
            self.blocks += 1
            self.lines.append(EmittedLine("-- " + line))
            return
        content = block_content(self.block, line, comment)
        offset = len(self.block.indent) if content else 0
        self.lines.append(EmittedLine(content, offset))

    def finish(self) -> None:
        if self.block is not None:
            raise ValueError(f"{self.block.opening_line}:1: Unclosed Lean block")
        if not self.blocks and not self.inline_lines:
            raise ValueError("1:1: No Lean blocks found or lean: comments found")


INLINE = re.compile(r"^\s*(?:///|//!|//|#)\s+lean: (?P<code>.*)$")


def inline_code(code: re.Match) -> EmittedLine:
    value = code.group("code").rstrip()
    offset = code.start("code")
    if value.startswith("`"):
        if len(value) < 2 or not value.endswith("`"):
            raise ValueError("Unclosed inline Lean code span")
        value = value[1:-1]
        offset += 1
        if "`" in value:
            raise ValueError("Use a fenced Lean block for code containing backticks")
    if not value.strip():
        raise ValueError("Empty lean: comment")
    return EmittedLine(value, offset)


def extract_lines(lines: list[str], comments: list[bool]) -> Extraction:
    extraction = Extraction()
    for number, (line, comment) in enumerate(zip(lines, comments, strict=True), 1):
        try:
            extraction.append(number, line, comment)
        except ValueError as error:
            raise ValueError(f"{number}:1: {error}") from error
    extraction.finish()
    return extraction


def extract(source: Path) -> Extraction:
    text = source.read_text(encoding="utf-8-sig")
    try:
        comments = comment_lines(source, text)
        return extract_lines(text.splitlines(), comments)
    except ValueError as error:
        raise ValueError(f"{source}:{error}") from error
