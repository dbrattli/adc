# Turn source comments into Lean

`leanify.py` extracts ADC `lean:` specifications with Python 3.10 or newer and its
standard library. Extraction does not require .NET or Lean.
Lean is required only for `--check`; run each host compiler separately.

From the repository root:

```sh
python3 tools/leanify.py examples/literate-lean/Batch.fsx examples/literate-lean/Batch.generated.lean
cd examples/literate-lean
python3 ../../tools/leanify.py Batch.fsx Batch.generated.lean --check
```

Run checking from the intended Lean project directory so its toolchain and
imports resolve. The example pins Lean 4.24.0.
The executable is `lean` on `PATH`, or the executable path in `LEAN`.
On Windows, `py -3` can replace `python3`; paths containing spaces must be quoted.
The output must be a separate `.lean` file; successful extraction overwrites it.
Generated views are for inspection, not editing or committing.

## Supported source syntax

- F# (`.fs`, `.fsx`, `.fsi`): standalone `// lean:` and `/// lean:` comments,
  plus bare fenced `lean` blocks inside `(* ... *)` comments.
- Python (`.py`): standalone `# lean:` comments. Python's tokenizer distinguishes
  comments from strings; docstrings and fenced blocks are not extracted.
- Rust (`.rs`): standalone `// lean:`, `/// lean:`, and `//! lean:` comments,
  plus bare fenced `lean` blocks inside `/* ... */` comments.
  Normal, byte, C, and raw strings, character literals, lifetimes, and nested
  block comments are recognized. Fences prefixed with `///` are not extracted.
- Other extensions are rejected. The ADC convention is language-independent.

Each inline value is raw Lean or enclosed in one pair of backticks:

```python
# lean: `def NonEmpty (xs : List α) : Prop := xs ≠ []`
```

The F# recognizer supports regular, verbatim, and triple-quoted strings,
character literals, quoted identifiers, and nested block comments.
It deliberately rejects interpolated strings anywhere outside comments.
It is a bounded lexical recognizer, not the F# compiler tokenizer or a syntax
checker. This is a portability tradeoff from the original .NET spike.
Validate host syntax separately; extend the recognizer and its tests before
using unsupported syntax. Host comment delimiters still apply inside Lean;
avoid embedded `(*` and `*)` in fenced content.

## Layout and diagnostics

Each input line produces one output line. Lean commands become active;
every other line receives a `--` comment prefix, retaining host code and ADCs.
All commands share one compilation unit in source order.

An opening fence defines the host indentation prefix, which must use spaces.
Content and closing fences must include that prefix. Extraction removes only
that prefix, preserving relative Lean indentation. Blank content lines remain
blank. Missing, empty, unclosed, nested, or misindented Lean blocks fail.
Empty inline declarations and malformed backtick spans also fail.
Extraction errors leave any existing output untouched.

`--check` runs Lean with warnings treated as errors and returns its exit status.
Diagnostics map to original source lines and columns, including removed host
indentation and inline markers. This checks specification formation; it does not
prove the host implementation conforms or that the requirements are correct.
Explicit axioms and disabled warnings require review, even if Lean succeeds.

## Development

```sh
python3 -B -m unittest discover -s tools -v
```

Compiler tests run when `LEAN` is set or `lean` is available on `PATH`;
otherwise they are reported as skipped.
`source_comments.py` and `rust_comments.py` recognize host comments;
`lean_blocks.py` handles fenced
layout, `lean_extraction.py` assembles formal content, and `leanify.py` handles
CLI, output, and compiler diagnostics.
