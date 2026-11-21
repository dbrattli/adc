"""Parse multiline Lean fences while preserving relative indentation."""

from dataclasses import dataclass


@dataclass
class Block:
    opening_line: int
    indent: str
    has_content: bool = False


def open_block(number: int, line: str) -> Block:
    indent = line[: len(line) - len(line.lstrip())]
    if any(ch != " " for ch in indent):
        raise ValueError("Lean fence indentation must use spaces")
    return Block(number, indent)


def close_block(block: Block, line: str) -> None:
    if line.rstrip() != block.indent + "```":
        raise ValueError("Closing fence must match the opening fence indentation")
    if not block.has_content:
        raise ValueError("Empty Lean block")


def block_content(block: Block, line: str, comment: bool) -> str:
    if not comment:
        raise ValueError("Lean block leaves its host comment before the closing fence")
    if line.strip().startswith("```"):
        raise ValueError("Unexpected fence inside Lean block")
    if not line.strip():
        return ""
    if not line.startswith(block.indent):
        raise ValueError("Lean content must include the opening fence indentation")
    block.has_content = True
    # invariant: removes only the host prefix so Lean's relative indentation survives
    return line[len(block.indent) :]
