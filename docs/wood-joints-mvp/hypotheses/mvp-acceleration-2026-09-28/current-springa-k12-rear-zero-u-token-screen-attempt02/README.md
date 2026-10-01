# K12-rear rejected-branch screen projection

floor-diagnostic-screen.json projects the refined K12-rear all-bearing
normal-law inventory into the current_case_bound_floor_diagnostic_screen/v1
contract consumed by the immutable attempt02 case-bound floor input adapter.
The projection is source-pinned to the original K12 controls model, deck, DAT,
execution, freeze, authorization, parent input/terminal checks, and original
ambiguous screen. It also pins the refined screen producer, zero-U parser,
case-bound wrapper, format proof, and SPC-only precursor proof.

The projected status remains REJECTED_ALL_BEARING_SUPPORT_BRANCH. All 100
floor cells are checked at seven states: 16 strictly positive and 84 strictly
separated at each state. This is an input mask proposal only. The screen's
diagnostic forces are not adopted, and it supplies no physical corner demand,
floor qualification, support acceptance, stability claim, or joint acceptance.

projection_verification.json independently compares all 700 cell/state rows
against both the preserved original screen and the refined screen. The source
group, cell identity, physical owner, normal-force center, and projected-q
center are identical for every row. The original first state retains its one
unresolved row, SPR1110 (16/83/1); the refined screen resolves it as separated
(16/84/0). Only projected-q radii change in the screen rows because zero-U
component radii changed; all normal-force radii are unchanged. The pinned DAT
comparison records 91,476 zero-U radius changes, 358,071 unchanged nonzero-U
components, and all 449,547 RF components/values/radii unchanged.

transformed_floor_coupon_replay.json compares the baseline and refined
parsers on the existing 12-state transformed source-reaction floor coupon.
Parsed U/RF values are identical; 480 exact-zero U radii change from 5e-7 to
zero, 96 nonzero U radii remain unchanged, and all 576 RF radii remain
unchanged. The coupon exercises a nonidentity source-row/pivot permutation;
it does not contain a CalculiX *TRANSFORM coordinate card. Its prior native
known-answer checks passed, and this replay does not rerun them.

The screen producer is project_k12_rear_screen.py; the projection comparison
is verify_k12_projection.py; the transformed-coupon replay is
replay_transformed_floor_coupon.py. All are read-only and start no solver.
