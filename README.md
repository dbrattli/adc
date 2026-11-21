# Agent Decision Comments

> Preserve the why in agent-written, human-reviewed code.

- Specification version: **0.5.0**
- Canonical repository: <https://github.com/dbrattli/adc>

Agent Decision Comments (ADCs) preserve durable engineering decisions and
constraints beside their implementation. They are local decision records, not
transcripts of private reasoning. Use ordinary comments, documentation comments,
or docstrings; no runtime dependency is required.
Keep ADCs versioned with the code they govern.

## Quick start

Install the compact [adc skill](skills/adc/SKILL.md):

```bash
npx skills add dbrattli/adc \
  --skill adc --global \
  --agent claude-code --agent pi --agent codex
```

Omit `--global` for project installation or agent flags for interactive selection.
For agents without skills, copy `skills/adc/SKILL.md` from a published release to
`ADC.md`; its YAML frontmatter can remain. Reference the exact local path from
`AGENTS.md`, `CLAUDE.md`, or equivalent:

```text
This repository uses Agent Decision Comments. See ADC.md.
Before modifying code, read its active ADCs and justify changes explicitly.
Add ADCs for non-obvious rationale introduced by your change.
Upstream releases: https://github.com/dbrattli/adc/releases
```

Keep the local convention compact: agents read it on every task. Pin copied
instructions to a release and review updates; do not rely solely on a moving
branch such as `main`. This README is the full specification and edge-case
reference; `SKILL.md` is the operational summary.

## The vocabulary

All five labels are optional. Start with `decision:` and `invariant:`; add other
labels only when they convey useful intent.

```text
decision:    A deliberate choice and the reason for it.
invariant:   A falsifiable property that the code must preserve.
assumption:  An external belief that this code does not guarantee.
tradeoff:    A cost accepted in exchange for a benefit.
lean:        A formal specification or supporting declaration written in Lean.
```

### `decision:`

Record the selected approach and why it fits; this does not imply exhaustive
comparison of alternatives.

```text
decision: prepends during the fold to avoid repeatedly copying the accumulated list
```

### `invariant:`

State a property that must survive future changes, specific enough to challenge
and, where practical, test or check with a tool.

```text
invariant: blocks accumulate in reverse order and are reversed exactly once
```

### `assumption:`

State an external belief the code does not guarantee, with its consequence when
useful. Caller obligations are preconditions: express them through types,
contracts, validation, or normal API documentation, not `assumption:`.

```text
assumption: upstream preserves source-line order — otherwise block positions are invalid
```

### `tradeoff:`

State both the accepted cost and the benefit.

```text
tradeoff: performs an O(n) copy per update to enable time-travel debugging
```

### `lean:`

Use Lean types, predicates, or supporting declarations to make intent precise.
Adopting ADC does not require Lean or a verification toolchain.
`invariant:` states a human-readable property; `lean:` can formalize that
property, a precondition, or an input/output contract. Do not require duplicate
prose directives; retain domain meaning, parameter correspondence, and rationale.
A predicate defines a requirement, not evidence that the implementation meets it.
Generate compact `lean:` lines by default, not fenced code blocks. Prefer
predicates describing allowed inputs, outputs, or state transitions; do not add
proofs or duplicate implementation algorithms unless requested. Keep parameter
correspondence and modeling limits brief.

```fsharp
/// Transform each item, preserving its position on successful return.
/// f models the callback; xs and ys model the input and output sequences.
///
/// decision: specifies elementwise correspondence because equal counts permit incorrect results
/// lean: `def MapContract (f : α → β) (xs : List α) (ys : List β) : Prop := ys = xs.map f`
let map f items = List.map f items
```

- Reuse domain type names where practical. Contract names may differ, such as
  `MapContract` for `map`; explain correspondence nearby. Names and adjacency aid
  review but do not verify the connection.
- Adjacent definitions need no extra reference. For separate models, reference
  the qualified Lean name and file in prose or an `invariant:`. `model:` and
  `ref:` are not ADC directives.
- Write one Lean command per `lean:` line, raw or inside one pair of Markdown
  backticks. Remove the backticks before checking.
- Use fenced `lean` blocks only for explicitly requested multiline
  specifications, in a host comment form supported by the adopted extractor.
  This is a continuation format, not another directive. Remove host prefixes
  and indentation while preserving relative Lean indentation.
- Extract commands into one compilation unit in source order. Imports,
  namespaces, and `end` establish context, not host implementation guarantees.

#### Checking formal intent

[leanify.py](tools/leanify.py) retains host code and ADCs as Lean comments;
`--check` runs Lean and maps diagnostics to the source. Follow its
[documented language/comment support](tools/README.md); extractors must state
these limits even though ADC itself is language-independent.
See the [Rust and F# examples](examples/literate-lean/README.md).

Distinguish the evidence:

- **Well-formedness:** names resolve and types/propositions check; this does not
  establish satisfiability or correct requirements.
- **Model proofs:** theorems establish consequences under their assumptions.
  Existence proofs can show a contract admits results; definitions alone cannot.
- **Implementation conformance:** requires a verified connection to the host
  program and separate evidence. Comment extraction does not establish it.

Review requirements, parameter correspondence, proof assumptions/dependencies,
and tests. State limits such as callback effects, exceptions, mutation, and
integer semantics. Compilation does not justify axioms or guarantee complete
proofs. The bundled checker treats warnings, including ordinary `sorry` warnings,
as errors; it is not a proof-trust auditor.

## Format

```text
<label>: <statement> [— <reason or consequence>]
```

- Use one directive and one statement per physical line; repeat labels as needed.
  `lean:` contains code rather than prose.
- Keep prose present-tense, specific, falsifiable, and concise; follow local line
  length where practical. Do not restate code, types, or tests.
- Attach directives to the nearest governed construct. In documentation comments
  and docstrings, put normal prose first, then a blank line and the directives.
  Use ordinary comments when API documentation is unnecessary.
- Update or remove directives when their governed code or rationale changes.
  The em dash is optional formatting, not a parser delimiter.

```python
def process_events(queue, handle):
    """
    Deliver events to a synchronous handler in enqueue order.
    The caller owns the deque exclusively until processing finishes.

    decision: processes events on one consumer to preserve arrival order
    decision: routes events through a queue to decouple producers from handler timing
    invariant: a handler finishes before the next event is dispatched
    tradeoff: limits throughput to preserve deterministic processing
    """
    while queue:
        handle(queue.popleft())
```

Avoid statements such as `decision: loops over the events` (restates mechanics)
or `decision: uses immutable state because it is better` (unreviewable rationale).

### Public APIs and generated documentation

Use ADCs selectively for API decisions such as portability, lifecycle,
compatibility, or escape hatches. State caller guarantees in normal API prose
first, including guarantees also expressed by `invariant:`, and test them where
practical. ADCs supplement rather than replace consumer documentation.
Documentation comments may appear in generated docs: put consumer-relevant
rationale there and implementation-only rationale in ordinary comments.

### Long-form explanations

When longer prose is needed, including in notebooks and literate programs,
place it before the directives. Use ADCs to capture its durable decisions and
constraints rather than repeat the explanation.

## When to write a comment

Add or update ADCs for:

- Meaningful algorithm, architecture, or data-structure choices.
- Ordering, consistency, concurrency, lifecycle, or boundary constraints.
- External beliefs that could fail and limitations accepted for a benefit.
- Behavior a competent reviewer would question.
- Local consequences of accepted RFCs/ADRs.

Skip obvious mechanics, type-enforced facts, trivial formatting/renaming or
mechanical refactoring, generic advice that does not constrain this code,
speculation that did not affect implementation, and per-function coverage.

## Scope

Collect active ADCs from file → module/namespace → type → function → local block.
Each governs its attached construct and nested constructs:

- File-level directives precede the first declaration.
- A comment immediately before a declaration or block governs that construct.
- A Python docstring governs its containing module, class, or function.

Enclosing directives accumulate. Local directives may clarify or specialize a
broader decision, but never silently cancel an invariant. Surface conflicts
before editing.

### Explicit local departure

Acknowledge departures from broader decisions and contain their effects.
For example, a local accumulator can depart from a module's immutable-state
policy while preserving the caller's input:

```typescript
/**
 * Return trimmed, nonempty lines without modifying the input.
 *
 * decision: mutates a local accumulator despite the module's immutable-state policy to avoid intermediate arrays
 * invariant: the caller's input remains unchanged so it can be reused
 * tradeoff: uses an explicit loop to avoid allocating mapped and filtered arrays
 */
function normalize(lines: readonly string[]): string[] {
  const result: string[] = [];
  for (const line of lines) {
    const trimmed = line.trim();
    if (trimmed !== "") result.push(trimmed);
  }
  return result;
}
```

## Existing comments are active constraints

Before changing code, read its active ADCs:

- Preserve `invariant:` properties or explicitly justify changes.
- Preserve `lean:` contracts and parameter correspondence; explicitly review
  semantic changes and rerun adopted Lean checks.
- Do not silently reverse `decision:` choices.
- Validate `assumption:` beliefs when the change depends on them.
- Reconsider `tradeoff:` costs and benefits when either changes.

Update or remove stale annotations in the same change and report changed
decisions in the review summary. ADCs describe current intent; obsolete ones
mislead future readers.

## Relationship to RFCs and ADRs

Use an RFC/ADR for decisions spanning systems/repositories, requiring discussion
or approval beyond code review, needing alternatives/history/status/ownership,
or significant beyond one implementation site. ADCs complement these records:
project accepted consequences into the code where they constrain changes.

```typescript
// decision: stores money as integer minor units — preserves ADR-004 rounding semantics
// invariant: persisted amounts never use binary floating-point representation
```

## Review workflow

Read ADCs before implementation details: challenge decisions, check invariants,
probe assumptions, reassess tradeoffs, and review formal contracts, parameter
correspondence, and model proofs. Then compare implementation and tests with that
intent. Comments do not replace implementation review.

For a strict review contract, add this policy to agent instructions:

```text
A change introducing a non-obvious decision or constraint is incomplete until
its ADCs are present and consistent with the implementation.
Review comments before implementation details.
```

## Versioning

Use Semantic Versioning: patches clarify without changing meaning; minor releases
add compatible directives/guidance; major releases change existing semantics or
adoption requirements. Repository-only maintenance needs no specification bump.
Publish each specification version as a GitHub release and `vX.Y.Z` tag containing
both the full specification and compact skill so adopters can review updates.

## Relationship to other conventions

Types constrain data/interfaces; tests check behavior; ADCs preserve decisions
and constraints. They complement Conventional Commits (change history) and
Conventional Comments (review feedback) with code-local intent.

## Editor highlighting

In VS Code, add [TODO Highlight][todo-highlight] settings at user or workspace
scope. For languages outside its default file patterns, such as Python and F#,
also configure `todohighlight.include` for the source files.

[todo-highlight]: https://marketplace.visualstudio.com/items?itemName=wayou.vscode-todo-highlight

```json
{
  "todohighlight.keywords": [
    { "text": "decision:", "color": "#c792ea", "backgroundColor": "transparent" },
    { "text": "assumption:", "color": "#82aaff", "backgroundColor": "transparent" },
    { "text": "invariant:", "color": "#ffcb6b", "backgroundColor": "transparent" },
    { "text": "tradeoff:", "color": "#7fdbca", "backgroundColor": "transparent" },
    { "text": "lean:", "color": "#f78c6c", "backgroundColor": "transparent" }
  ]
}
```
