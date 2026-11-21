// Compact formal intent beside its implementation.
// The extractor activates marked Lean comments and comments out all other lines.
// Contracts describe successful returns with pure callbacks.
// decision: keeps specifications local so reviewers see intent beside each operation
// lean: `namespace BatchSpec`

/// An ordered batch containing at least one item.
/// The F# head and tail represent the Lean subtype's sequence in the same order.
///
/// decision: uses a mandatory head because dispatch requires a first item
/// lean: `def Batch (α : Type) := { xs : List α // xs ≠ [] }`
type Batch<'T> = private Batch of head: 'T * tail: 'T list

module Batch =
    /// Interpret a batch as its ordered sequence of items.
    ///
    /// lean: `def Batch.toList (b : Batch α) : List α := b.val`
    let toList (Batch(head, tail)) = head :: tail

    /// Accept exactly nonempty input, preserving every item in order.
    /// xs represents items; result represents the returned option.
    ///
    /// lean: `def ParseContract (xs : List α) (result : Option (Batch α)) : Prop := match result with | none => xs = [] | some b => b.toList = xs`
    let parse items =
        match items with
        | [] -> None
        | head :: tail -> Some(Batch(head, tail))

    /// Transform each item, preserving its position on successful return.
    /// f models the callback; xs and ys represent input and returned batches.
    ///
    /// decision: specifies elementwise correspondence because equal counts permit incorrect results
    /// lean: `def MapContract (f : α → β) (xs : Batch α) (ys : Batch β) : Prop := ys.toList = xs.toList.map f`
    let map f (Batch(head, tail)) =
        let mappedHead = f head
        let mappedTail = List.map f tail
        Batch(mappedHead, mappedTail)

    /// Retain matching items in order, returning None when none remain.
    /// p models keep; xs represents batch; result represents the returned option.
    ///
    /// decision: exposes an empty selection so dispatch must handle it explicitly
    /// lean: `def FilterContract (p : α → Bool) (xs : Batch α) (result : Option (Batch α)) : Prop := ParseContract (xs.toList.filter p) result`
    let filter keep batch = batch |> toList |> List.filter keep |> parse

/// Skip dispatch or send a nonempty batch; case names correspond directly.
///
/// lean: `inductive DispatchPlan (α : Type) where | skip | send (batch : Batch α)`
type DispatchPlan<'T> = Skip | Send of Batch<'T>

/// Plan dispatch after selection, without performing delivery.
/// p models keep; xs represents batch; result represents the returned plan.
///
/// lean: `def PlanContract (p : α → Bool) (xs : Batch α) (result : DispatchPlan α) : Prop := match result with | .skip => xs.toList.filter p = [] | .send b => b.toList = xs.toList.filter p`
let plan keep batch =
    match Batch.filter keep batch with
    | None -> Skip
    | Some remaining -> Send remaining

// lean: `end BatchSpec`

// These checks exercise F# behavior; Lean checks only the specification's formation.
let check name expected actual =
    if expected <> actual then failwithf "%s: expected %A, got %A" name expected actual

let sample =
    match Batch.parse [1; 2; 3] with
    | Some batch -> batch
    | None -> failwith "The sample must be nonempty"

check "empty input" None (Batch.parse ([]: int list))
check "input order" [1; 2; 3] (Batch.toList sample)
check "mapping" [11; 12; 13] (sample |> Batch.map ((+) 10) |> Batch.toList)
check "partial selection" (Some [2; 3])
    (sample |> Batch.filter (fun n -> n > 1) |> Option.map Batch.toList)
check "empty selection" None (Batch.filter (fun _ -> false) sample)
check "skip empty selection" Skip (plan (fun _ -> false) sample)
check "send remaining items" (Send(Batch(2, [3]))) (plan (fun n -> n > 1) sample)
printfn "All seven F# examples passed."
