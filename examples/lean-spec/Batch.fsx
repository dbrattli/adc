/// An ordered batch with at least one item.
///
/// model: Batch.lean#BatchSpec.Batch
type Batch<'T> = private Batch of head: 'T * tail: 'T list

module Batch =
    /// Interpret a batch as its ordered sequence of items.
    let toList (Batch(head, tail)) = head :: tail

    /// Accept exactly the nonempty inputs, retaining every item in order.
    ///
    /// model: Batch.lean#BatchSpec.ParseContract
    /// decision: establishes a batch at the boundary so dispatch has a first item
    let parse items =
        match items with
        | [] -> None
        | head :: tail -> Some(Batch(head, tail))

    /// Apply a function to each item, retaining count and order on success.
    ///
    /// model: Batch.lean#BatchSpec.MapContract
    /// invariant: mapping preserves item count for downstream accounting — Batch.lean#BatchSpec.PreservesLength
    let map f (Batch(head, tail)) =
        let mappedHead = f head
        let mappedTail = List.map f tail
        Batch(mappedHead, mappedTail)

    /// Retain matching items in order, returning None when none remain.
    ///
    /// model: Batch.lean#BatchSpec.FilterContract
    /// decision: exposes an empty selection so dispatch can skip it explicitly
    let filter keep batch =
        batch |> toList |> List.filter keep |> parse

/// Skip dispatch or send a nonempty batch.
///
/// model: Batch.lean#BatchSpec.DispatchPlan
type DispatchPlan<'T> =
    | Skip
    | Send of Batch<'T>

/// Plan dispatch without performing external effects.
let plan keep batch =
    match Batch.filter keep batch with
    | None -> Skip
    | Some remaining -> Send remaining

// Small executable examples, paired with the examples in Batch.lean.
let check name expected actual =
    if expected <> actual then
        failwithf "%s: expected %A, got %A" name expected actual

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
