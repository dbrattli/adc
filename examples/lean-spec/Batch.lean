-- decision: models ordered values and successful results so domain contracts can be reviewed independently of runtime behavior
-- tradeoff: omits callback effects and failures to keep the model focused on data relationships
-- invariant: proofs use no unfinished obligations or custom axioms so their dependencies remain auditable
namespace BatchSpec

/-- A sequence contains at least one item; its elements need not be distinct. -/
def NonEmpty (xs : List α) : Prop :=
  xs ≠ []

-- decision: models a batch as head and tail because dispatch requires a first item
structure Batch (α : Type) where
  head : α
  tail : List α
  deriving DecidableEq, Repr

/--
Interpret the representation as an ordered sequence, including duplicates.

decision: compares batches through their sequences so contracts can also describe other language representations
-/
def Batch.toList (batch : Batch α) : List α :=
  batch.head :: batch.tail

/--
Every modeled batch denotes a nonempty sequence.
An empty interpretation would equate a list constructor with the empty list.
This establishes a property of the Lean representation only.
-/
theorem Batch.nonempty (batch : Batch α) : NonEmpty batch.toList := by
  intro empty
  cases empty

def parse (xs : List α) : Option (Batch α) :=
  match xs with
  | [] => none
  | head :: tail => some ⟨head, tail⟩

/--
Accept exactly nonempty input and retain its complete ordered sequence.

decision: specifies exact sequence equality so parsing cannot silently drop or reorder items
-/
def ParseContract (input : List α) (result : Option (Batch α)) : Prop :=
  match result with
  | none => input = []
  | some batch => batch.toList = input

/--
The output contains the transformed input item at each original position.

decision: specifies elementwise correspondence because nonemptiness and equal counts alone permit incorrect mappings
-/
def MapContract (f : α → β) (input : Batch α) (output : Batch β) : Prop :=
  output.toList = input.toList.map f

/--
Input and output contain the same number of items, possibly of different types.

decision: names count preservation separately so downstream accounting can reference its own requirement
-/
def PreservesLength (before : Batch α) (after : Batch β) : Prop :=
  after.toList.length = before.toList.length

/--
Any input and output satisfying the mapping contract also preserve item count.
The caller supplies evidence of the contract; this theorem does not establish it.

decision: derives the weaker requirement from the contract so their logical relationship is checked independently of an implementation
-/
theorem MapContract.preservesLength (f : α → β) (input : Batch α)
    (output : Batch β) (contract : MapContract f input output) :
    PreservesLength input output := by
  change output.toList.length = input.toList.length
  -- Equal sequences have equal lengths; List.map retains the input length.
  calc
    output.toList.length = (input.toList.map f).length :=
      congrArg List.length contract
    _ = input.toList.length := List.length_map f

/--
Retain precisely the matching items, or return none if no items match.

decision: reuses the parsing contract so empty-result handling has one definition
-/
def FilterContract (keep : α → Bool) (input : Batch α)
    (result : Option (Batch α)) : Prop :=
  ParseContract (input.toList.filter keep) result

-- Executable model operations support the concrete checks below.
-- They are not translations of the corresponding F# implementation.
def map (f : α → β) (batch : Batch α) : Batch β :=
  ⟨f batch.head, batch.tail.map f⟩

def filter (keep : α → Bool) (batch : Batch α) : Option (Batch α) :=
  parse (batch.toList.filter keep)

/--
A selection either skips dispatch or supplies a nonempty batch to send.

decision: represents skipping explicitly so an empty selection cannot disappear from the dispatch workflow
-/
inductive DispatchPlan (α : Type) where
  | skip
  | send (batch : Batch α)
  deriving DecidableEq, Repr

def plan (keep : α → Bool) (batch : Batch α) : DispatchPlan α :=
  match filter keep batch with
  | none => .skip
  | some remaining => .send remaining

-- Concrete specification checks; these do not prove the F# implementation.
-- decision: uses the same small values as the F# examples to make the intended correspondence easy to review
def sample : Batch Nat := ⟨1, [2, 3]⟩

example : ParseContract ([] : List Nat) (parse []) := by rfl
example : ParseContract [1, 2, 3] (parse [1, 2, 3]) := by rfl
example : MapContract (fun n => n + 10) sample (map (fun n => n + 10) sample) := by rfl
example : FilterContract (fun n => n > 1) sample (filter (fun n => n > 1) sample) := by rfl
example : FilterContract (fun _ => false) sample (filter (fun _ => false) sample) := by rfl
example : plan (fun _ => false) sample = .skip := by rfl
example : plan (fun n => n > 1) sample = .send ⟨2, [3]⟩ := by rfl

-- A nonempty return type alone cannot establish the mapping contract.
-- decision: retains a dropped-item counterexample to expose the gap between a valid representation and a correct operation
example : ¬ MapContract (fun n => n + 10) sample ⟨11, []⟩ := by
  simp [MapContract, sample, Batch.toList]

-- Preserving length is necessary, but not sufficient, for correct mapping.
example : PreservesLength sample (⟨11, [11, 11]⟩ : Batch Nat) := by rfl
-- decision: retains a same-length counterexample so count preservation cannot replace elementwise correspondence
example : ¬ MapContract (fun n => n + 10) sample ⟨11, [11, 11]⟩ := by
  simp [MapContract, sample, Batch.toList]

-- Inspect transitive proof dependencies, including any hidden unfinished proof.
#print axioms Batch.nonempty
#print axioms MapContract.preservesLength

end BatchSpec
