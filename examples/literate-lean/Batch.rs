// Compact formal intent beside Rust types and operations.
// Contracts model successful returns with pure callbacks; panics and effects are outside the model.
// decision: keeps formal contracts beside operations so reviewers can compare intent and implementation
// lean: `namespace RustBatchSpec`

/// An ordered batch containing at least one item.
/// The head followed by the tail corresponds to the Lean subtype's list.
///
/// decision: stores a mandatory head because dispatch requires a first item
/// lean: `def Batch (α : Type) := { xs : List α // xs ≠ [] }`
#[derive(Debug, PartialEq)]
struct Batch<T> {
    head: T,
    tail: Vec<T>,
}

impl<T> Batch<T> {
    /// Accept exactly nonempty input, preserving all items in order.
    /// xs represents items; result represents the returned Option.
    ///
    /// lean: `def ParseContract (xs : List α) (result : Option (Batch α)) : Prop := match result with | none => xs = [] | some b => b.val = xs`
    fn parse(items: Vec<T>) -> Option<Self> {
        let mut items = items.into_iter();
        let head = items.next()?;
        Some(Self {
            head,
            tail: items.collect(),
        })
    }

    /// Transform every item, preserving its position on successful return.
    /// f models the callback; xs and ys model self and the returned batch.
    ///
    /// decision: specifies elementwise correspondence because equal lengths permit incorrect results
    /// lean: `def MapContract (f : α → β) (xs : Batch α) (ys : Batch β) : Prop := ys.val = xs.val.map f`
    fn map<U>(self, mut f: impl FnMut(T) -> U) -> Batch<U> {
        let head = f(self.head);
        let tail = self.tail.into_iter().map(f).collect();
        Batch { head, tail }
    }

    /// Interpret the batch as its ordered sequence.
    /// xs represents self; ys represents the returned Vec.
    ///
    /// lean: `def IntoVecContract (xs : Batch α) (ys : List α) : Prop := ys = xs.val`
    fn into_vec(self) -> Vec<T> {
        std::iter::once(self.head).chain(self.tail).collect()
    }
}

// lean: `end RustBatchSpec`

#[cfg(test)]
mod tests {
    use super::Batch;

    #[test]
    fn rejects_empty_input() {
        assert_eq!(Batch::parse(Vec::<i32>::new()), None);
    }

    #[test]
    fn preserves_input_order() {
        assert_eq!(
            Batch::parse(vec![3, 1, 2]).unwrap().into_vec(),
            vec![3, 1, 2]
        );
    }

    #[test]
    fn maps_each_item_in_order() {
        let batch = Batch::parse(vec![3, 1, 2]).unwrap();
        assert_eq!(batch.map(|item| item + 10).into_vec(), vec![13, 11, 12]);
    }
}
