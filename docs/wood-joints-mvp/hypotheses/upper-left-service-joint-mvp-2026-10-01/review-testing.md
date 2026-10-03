# Testing review

The three reviewed files match `review-target.json`. Three substantial gaps remain:

1. **Physical release flags are not protected by the test.** [`test_joint.py`](test_joint.py#L45) checks the HOLD and acceptance fields, but never asserts `fabrication_released`, `drilling_released`, `structural_released`, or `climbing_released` (nor the geometry/native-run flags). A regression that turns a release flag on would still pass. Assert every release and model-state flag remains false.

2. **Whole-cleat wrenches can pass with a wrong state/receiver join.** [`check_joint.py`](check_joint.py#L175) checks only the case/index key set, a producer boolean, a scalar port count, and residual intervals. It does not require each boundary row's load factor to match its increment, or validate the two receiver IDs and the 16 source names. [`test_joint.py`](test_joint.py#L58) checks only that 21 records are returned. A mislabeled or misjoined boundary record can therefore be reported as a same-state receiver wrench. Validate factor and receiver/source identities against the expected state inventory, then test wrong-factor, wrong-receiver, and duplicate/missing-source mutations.

3. **The machine-readable unresolved-gate list omits open shop/transport work.** [`README.md`](README.md#L113) leaves the reversible shop sequence and individual-member transport unresolved; [`check_joint.py`](check_joint.py#L279) has no corresponding gate, while the test only checks that the list has six entries. Add an explicit operational gate and assert the expected gate set, so a count-preserving omission cannot pass.
