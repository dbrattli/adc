# Compact Lean intent in source comments

This example demonstrates the optional `lean:` directive in ADC 0.5.0.
[Batch.fsx](Batch.fsx) writes formal intent as one-line `lean:` comments beside
ordinary F# declarations.
[Batch.rs](Batch.rs) demonstrates the same nonempty model and mapping contract
in Rust; both use the Python tool.
[leanify.py](../../tools/leanify.py) extracts those statements into a checkable
Lean view.
The aim is precise specifications, not proofs of the commented implementation.

## Read the example

```fsharp
    /// Transform each item, preserving its position on successful return.
    /// f models the callback; xs and ys represent input and returned batches.
    ///
    /// decision: specifies elementwise correspondence because equal counts permit incorrect results
    /// lean: `def MapContract (f : α → β) (xs : Batch α) (ys : Batch β) : Prop := ys.toList = xs.toList.map f`
    let map f (Batch(head, tail)) =
        let mappedHead = f head
        let mappedTail = List.map f tail
        Batch(mappedHead, mappedTail)
```

The adjacent `lean:` declaration supplies the formal specification for the F#
declaration governed by that comment.
There is no additional `model:` reference: it would repeat the local connection.
The Lean name need not match the implementation name; `MapContract` describes
what `map` must satisfy, rather than implementing it again.
An explicit reference remains useful when a specification is defined elsewhere,
including in the original companion-file example.

`decision:` preserves rationale; `lean:` supplies a precise definition.
Both are ADC directives; formal specifications remain optional.

The example includes a nonempty `Batch` subtype and one-line contracts for
parsing, mapping, filtering, and dispatch planning.
F# head and tail correspond to the subtype's ordered sequence.
The local prose binds predicate parameters to implementation values.
Namespace markers and `Batch.toList` supply shared Lean context.
There are no duplicate Lean operation implementations or proof scripts.

## Run the example

Requirements: Python 3.10 or newer for extraction, a .NET SDK to run the F#
implementation, and Lean for optional checking.
The [toolchain file](lean-toolchain) pins Lean 4.24.0.
See [tool documentation](../../tools/README.md) for syntax support and limitations.

From this directory:

```sh
dotnet fsi Batch.fsx
python3 ../../tools/leanify.py Batch.fsx Batch.generated.lean --check
python3 -B -m unittest discover -s ../../tools -v
```

For a standalone compiler, prefix the second and third commands with
`LEAN=/absolute/path/to/lean`.
Without `--check`, the extractor only writes the generated view.
It overwrites the chosen `.lean` output after successful extraction; use a
disposable output path and do not edit or commit the generated file.

The F# example runs seven behavior checks.
Lean checks the formation of the extracted types and predicates.
Extractor tests cover comment recognition, indentation, malformed input, and
mapped compiler diagnostics; compiler tests are skipped if Lean is unavailable.

## Rust example

From this directory, using Rust and Lean installed on your system:

```sh
python3 ../../tools/leanify.py Batch.rs Batch-rust.generated.lean --check
rustc --test Batch.rs -o /tmp/adc-batch-tests
/tmp/adc-batch-tests
```

On Windows, choose a local output path ending in `.exe` for the Rust test binary.
The Rust example tests parsing, ordering, and mapping.
Its contracts model `Vec<T>` as `List α` and `Option` as Lean `Option`.
`FnMut` effects and panics are outside the pure callback model.
Rust ownership and borrowing are checked by Rust, not these Lean declarations.
The extractor supports Rust inline comments and fences inside block comments;
see the [supported syntax](../../tools/README.md#supported-source-syntax).

## Extraction rules

- A standalone ``// lean: `CODE` `` or ``/// lean: `CODE` `` line activates
  `CODE` in Lean. Backticks render the specification as inline code in Markdown.
  Host indentation, the comment marker, and the outer backticks are removed.
  Empty statements and unclosed code spans fail extraction.
- Raw `// lean: CODE` and `/// lean: CODE` comments also work. The extractor supports
  one outer backtick pair; use a fenced block when Lean code contains backticks.
- The host recognizer must classify the line as a comment, so supported string
  forms cannot masquerade as specifications. F# interpolation is rejected.
- Every source line produces one generated line. Other source lines receive a
  Lean comment prefix, preserving implementation and rationale in the view.
- All active statements share one Lean compilation unit in source order.
- The extractor records removed prefixes to restore source diagnostic columns.
- Missing specifications fail extraction.

Fenced Lean blocks remain supported for statements that benefit from more space:

````fsharp
module Example =
    (**
    ```lean
    def NonEmpty (xs : List α) : Prop :=
      xs ≠ []
    ```
    *)
    let isNonEmpty items = not (List.isEmpty items)
````

Opening and closing fences occupy standalone lines in an F# comment.
Closing fences match the opening indentation, which must use spaces.
Every nonblank content line includes that indentation prefix; extraction removes
only this prefix, preserving Lean's relative layout. Blank lines become empty.
Missing, empty, unclosed, misindented, or nested fences fail extraction.
Other fenced languages remain comments.

This example uses the F# subset of the Python extractor, not a general Markdown
parser or F# syntax checker. Run F# Interactive separately to check the source language.
Host comment delimiters still apply inside fenced Lean; avoid embedded
`(*` and `*)` delimiters in that format.

## What checking means

With `--check`, the extractor runs Lean with warnings treated as errors and
returns its exit status. Diagnostics refer to the original F# file, line, and
column, including the removed indentation, comment prefix, and opening backtick.

A successful check establishes that names resolve and the specification's types
and propositions are well-formed.
It does not establish satisfiability, the suitability of the requirements, or
conformance of the F# implementation.
Those remain questions for review and implementation tests.

Contracts describe successful results with callbacks corresponding to the Lean
functions. Callback effects, exception behavior, and machine-integer overflow
are outside this model.
The extractor does not verify that a local predicate has the intended parameter
bindings or relationship to the following F# declaration.
