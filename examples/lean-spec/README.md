# Spike: Lean specifications linked from ADCs

This experiment uses Lean to make a domain model and its contracts precise.
F# supplies an executable implementation example.
ADCs connect the implementation's rationale to named Lean declarations.
This experiment proposes an optional `model:` directive alongside ADC 0.4.1.
ADC 0.5.0 adopts inline `lean:` specifications instead.
The `model:` proposal remains historical and applies only to this spike.

The aim is to specify the intended problem more precisely.
Lean does not determine whether these requirements meet a real business need,
and checking this model does not verify the F# implementation.

## Read the example

- [Batch.lean](Batch.lean) defines the model, contract predicates, and examples.
- [Batch.fsx](Batch.fsx) implements the same small domain in F#.
- [lean-toolchain](lean-toolchain) pins the Lean compiler for reproducibility.

A batch contains at least one item, in a defined order.
Dispatch requires a batch; an empty selection produces an explicit skip plan.
The example plans dispatch but performs no external delivery.

```text
ordinary list → parse → Batch → map → Batch → filter → Option Batch
                                                        │
                                        None ───────────┤→ Skip
                                        Some Batch ─────┘→ Send Batch
```

## Propositions and representations

`BatchSpec.NonEmpty xs` means `xs ≠ []`.
Both models represent a batch with a mandatory head and an ordinary list tail.
The interpretation of either representation is:

```text
toList(Batch(head, tail)) = head :: tail
```

Lean proves that its representation always denotes a nonempty list through
`BatchSpec.Batch.nonempty`.
The F# private union controls ordinary construction through the module API.
The connection between these representations is documented here; there is no
verified translation from F# to Lean.

The model captures order and cardinality, not uniqueness or item validity.
Its immutable lists also avoid a mutable alias invalidating a previous check.

## Connect type declarations

Every implementation domain type in this spike has a comment identifying its
Lean type, directly above the declaration.
Keep the domain type names the same in both languages, while using each
language's normal syntax for type parameters, fields, and cases.

```fsharp
/// An ordered batch with at least one item.
///
/// model: Batch.lean#BatchSpec.Batch
type Batch<'T> = private Batch of head: 'T * tail: 'T list

/// Skip dispatch or send a nonempty batch.
///
/// model: Batch.lean#BatchSpec.DispatchPlan
type DispatchPlan<'T> =
    | Skip
    | Send of Batch<'T>
```

The proposed `model:` directive identifies a formal model or contract that the
annotated construct is intended to represent or satisfy.
It does not assert verified conformance.
The reference uses the same relative-path and declaration-name convention as
the operation references below.
Explicit references distinguish matching domain names in different namespaces.

| F# representation | Lean representation | Correspondence |
| --- | --- | --- |
| `Batch<'T>` | `BatchSpec.Batch α` | `'T` corresponds to `α`; head and tail preserve the same ordered items. |
| `DispatchPlan<'T>` | `BatchSpec.DispatchPlan α` | `Skip` corresponds to `skip`; `Send batch` corresponds to `send batch`. |

The same comment convention can accompany a Python class or Rust type.
Matching names identify the intended relationship; representation differences
still need an explicit interpretation, such as a Python tuple corresponding to
a Lean list with the same elements in order.
If a type has no Lean model yet, document that gap instead of inventing a link.

## Specify relationships beyond return types

| Contract | Meaning |
| --- | --- |
| `BatchSpec.ParseContract` | Failure means the input is empty; success retains the exact input sequence. |
| `BatchSpec.MapContract` | The output sequence equals elementwise mapping of the input. |
| `BatchSpec.FilterContract` | Parse the sequence of matching items, preserving their order. |

A `Batch` return type excludes an empty result through ordinary construction.
It does not establish the mapping contract: returning only one transformed
element would still produce a batch.
The Lean file includes a concrete rejected mapping result to expose that gap.

Contracts are propositions that can be stated and type-checked without proving
that an implementation satisfies them for every input.
The file checks concrete examples and proves a representation property and a
relationship between requirements;
it deliberately does not claim general conformance proofs for the operations.
No unproved obligation is introduced as an axiom or filled with `sorry`.

## References from ADCs

The F# mapping operation separates its contract from a named invariant:

```fsharp
// model: Batch.lean#BatchSpec.MapContract
// invariant: mapping preserves item count for downstream accounting — Batch.lean#BatchSpec.PreservesLength
```

For this spike, a reference consists of a path relative to the source file,
followed by `#` and the fully qualified Lean declaration name.
It identifies the specification the implementation is intended to satisfy.
It is neither a proof attachment nor a Markdown source anchor.
There is no reference resolver in this spike; references are reviewed manually.

The ADC records why the relationship matters.
Normal API documentation states the caller-visible guarantee.
Lean states its mathematical meaning.
There is no need to repeat every type-enforced fact as an ADC.

## Formalize an invariant

Lean defines the referenced property once:

```lean
def PreservesLength (before : Batch α) (after : Batch β) : Prop :=
  after.toList.length = before.toList.length
```

This is a predicate on two batches, not a proof that F# mapping preserves length.
Its ADC keeps the requirement readable and explains why count matters.
The full mapping contract additionally specifies the item at every position.

The theorem `BatchSpec.MapContract.preservesLength` establishes:

```text
MapContract f input output → PreservesLength input output
```

Lean checks that the stronger contract implies this invariant for all modeled
inputs and outputs.
The theorem assumes the contract holds; it does not establish that assumption
for the F# implementation.
A concrete counterexample also shows why the converse fails: `[11, 11, 11]`
preserves the length of `[1, 2, 3]` but is not its mapping by `n ↦ n + 10`.

### Bind parameters to implementation values

References name declarations; their meaning also depends on parameter bindings.
For this spike, the bindings are documented here and reviewed manually:

| F# operation | Lean parameters | Interpretation |
| --- | --- | --- |
| `Batch.parse items` | `ParseContract input result` | `input` represents `items`; `result` represents the returned option. |
| `Batch.map f batch` | `MapContract f input output` | Lean `f` models the callback; `input` represents the input batch; `output` represents the returned batch. |
| `Batch.map f batch` | `PreservesLength before after` | `before` represents the input batch; `after` represents the returned batch. |
| `Batch.filter keep batch` | `FilterContract keep input result` | Lean `keep` models the predicate; `input` represents the input batch; `result` represents the returned option. |

These operation obligations apply on successful return.
They refer to values interpreted through the type correspondence above, not
raw F# objects inside Lean.
Future reference tooling would need explicit, checked bindings; a matching
declaration name alone cannot establish them.

Simple local constraints can still use notation such as
`invariant: 0 <= cursor <= length(items)` without a Lean reference.
Such notation remains a reader-facing constraint unless its semantics are
defined and checked by a tool.
Use named Lean propositions for shared properties and relationships that
benefit from one precise definition.

## Follow the specification through the program

1. Parsing establishes nonemptiness and preserves the input sequence.
2. Mapping must preserve count and positions, not just return a valid batch.
3. Filtering can lose nonemptiness, so its result is optional.
4. Planning handles both outcomes; only the `Send` case carries a batch.

This makes a missing empty-result branch visible in the data model.
It also gives review a specific question: does each implementation satisfy the
contract required by the next operation?
Proving those contracts for the Lean operations would strengthen the model,
but would still leave implementation correspondence as a separate obligation.

## Check the spike

With Lean managed by elan and the .NET SDK installed, run from this directory:

```sh
lean Batch.lean
dotnet fsi Batch.fsx
```

The Lean file prints the axiom dependencies of `Batch.nonempty` and
`MapContract.preservesLength`.
With the pinned compiler, the former reports no axioms and the latter reports
only Lean's standard propositional extensionality axiom, `propext`.
Neither depends on `sorryAx` or a custom axiom.
The F# script raises an exception on a failed check and prints a success message
after its seven examples pass.

| Evidence | What it establishes |
| --- | --- |
| Lean type checking | Model definitions and contract statements are well-formed. |
| Representation theorem | Every Lean batch denotes a nonempty list. |
| Contract implication theorem | The Lean mapping contract implies length preservation. |
| Lean examples | Selected model cases satisfy the stated contracts. |
| F# examples | Selected implementation cases have the expected outcomes. |
| ADC references | A reviewer can find the intended contract. |

The examples use matching concrete values but are maintained independently.
They are not differential tests or a general conformance proof.
A future check could run shared cases against both implementations and resolve
ADC references automatically, without claiming those checks prove conformance.

## Limits and next experiment

Lean's functions here are total and pure.
The F# contracts describe successful returns with callbacks corresponding to
the modeled functions; callback effects and exceptions are outside this model.
The sample uses small positive integers, while Lean `Nat` and F# `int` differ
in range and arithmetic semantics.
It makes no claim about overflow, nulls, unsafe construction, or external I/O.

Rust could implement the same head-and-tail model with encapsulated fields.
Python could use an immutable head-and-tail object with runtime boundary checks.
Each language would need its own correspondence review and evidence.

The next useful experiment is a real domain rule, such as preserving batch
identity across routing, using the same small set of concepts:
a domain representation, named contract propositions, and ADC references.
