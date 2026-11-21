---
name: adc
description: Apply Agent Decision Comments when changing or reviewing code in repositories that use ADCs.
---

# Agent Decision Comments

- Specification version: **0.5.0** — <https://github.com/dbrattli/adc>
- Purpose: preserve durable engineering intent beside the code it governs.
- Use ordinary comments, documentation comments, or docstrings; no runtime
  dependency. All directives, including Lean, are optional.

## Labels

```text
decision:    A deliberate choice and the reason for it.
invariant:   A falsifiable property that the code must preserve.
assumption:  An external belief that this code does not guarantee.
tradeoff:    A cost accepted in exchange for a benefit.
lean:        A formal specification or supporting declaration written in Lean.
```

Start with `decision:` and `invariant:`. A caller obligation is a precondition,
not an assumption.

## When and how to write

Add ADCs for non-obvious algorithm, architecture, or data choices; ordering,
consistency, concurrency, or lifecycle constraints; boundaries; external
assumptions; accepted limitations; surprising behavior; and local consequences
of RFCs/ADRs. Skip obvious mechanics, type-enforced facts, trivial refactoring,
generic advice, speculation, and comments added only for coverage.

```text
<label>: <statement> [— <reason or consequence>]
```

- Write one directive per physical line; repeated labels are allowed.
- Keep prose concise, present-tense, specific, and falsifiable; do not restate
  code, types, or tests. The em dash is optional formatting, not a delimiter.
- Attach directives to the nearest governed construct. In documentation comments
  or docstrings, put normal prose first, then a blank line and the directives.
  Use ordinary comments when API documentation is unnecessary.

```python
# decision: processes events on one consumer to preserve arrival order
# invariant: handlers observe events in enqueue order
# tradeoff: limits throughput to gain deterministic processing
while queue:
    handle(queue.popleft())
```

## Optional formal intent

Use `lean:` for precise types or contracts. It can formalize an invariant or
another contract without a duplicate prose directive. Explain parameter
correspondence and modeling limits nearby; use consistent domain type names.
An adjacent definition needs no extra reference. `model:` and `ref:` are not
ADC directives.
A model represents program values and states; a contract defines their allowed
relationships.

Generate compact `lean:` lines by default, not fenced code blocks.
Prefer predicates describing allowed inputs, outputs, or state transitions;
do not add proofs or duplicate implementation algorithms unless requested.
Keep parameter correspondence and modeling limits brief.

```rust
// lean: `def MapContract (f : α → β) (xs : List α) (ys : List β) : Prop := ys = xs.map f`
```

Write one Lean command per line, raw or inside one pair of Markdown backticks.
Use fenced blocks only for explicitly requested multiline specifications, with
syntax supported by the adopted extractor; preserve relative indentation.
Imports, namespaces, and declarations share one compilation unit in source order.

Lean checks well-formedness, not satisfiability, correct requirements, or host
implementation conformance. Optional proofs establish model properties under
assumptions. Review those assumptions and the implementation correspondence;
never describe comment extraction as program proof.

Use formal contracts as behavioral targets during refactoring and porting.
Review model correspondence explicitly; omitted behavior is not permission to
change it. Preserve API and compatibility obligations, and surface conflicts
between contracts, documentation, tests, and implementation before editing.

## Before changing code

Read active ADCs from file scope down to the modified site. Each governs its
attached construct and nested constructs; enclosing directives accumulate.
Local decisions may specialize broader ones but never silently cancel an
invariant. Surface conflicts before editing.

- Preserve `invariant:` properties or explicitly justify changes.
- Preserve `lean:` contracts and parameter correspondence; explicitly review
  semantic changes and rerun adopted Lean checks.
- Do not silently reverse `decision:` choices.
- Validate `assumption:` beliefs when the change depends on them.
- Reconsider `tradeoff:` costs and benefits when either changes.

Update or remove stale directives in the same change and report changed
decisions in the review summary. Obsolete directives mislead future readers.
