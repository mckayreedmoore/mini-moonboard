# A1-rear 46-cell selected-floor input proposal

This packet prepares one input-only A1-rear proposal with 46 selected bearing
cells, 54 inactive cells, and 92 active source tangent rows. Its proposed mask
is the stable strict-positive set from the exact rejected 44-cell A1-rear run's
seven-state zero-U 711 normal-interval diagnostic. That diagnostic found two
positive cells that had been released and no selected cells that separated:
`floor_base_floor_left_36` / `SPR1131` and
`floor_base_floor_right_12` / `SPR1173`. The projection retains all 100 normal
law classifications at all seven states and exports no force or RF values.

The original A1-rear all-bearing controls remain the physics authority for
geometry, material directions, source loads, SPRINGA laws, and retained
bilateral rows. The rejected 44-cell run is classification lineage only. The
46-cell proposal is not accepted support; the prepared model is not ready for a
native run and produces no corner demand.

`screen.json` is the shared diagnostic-screen schema projection. Its exact
inputs, method pins, and producer hash are in
[`projection-source-pins.json`](projection-source-pins.json). The prepared
model, deck, adapter audit, case-bound context, source pins, and separate
serialized-input audit are case-local in [`a1-rear/`](a1-rear/).

The source-pinned input adapter returned
`PASS_SELECTED_FLOOR_INPUT_ALGEBRA_AND_SOURCE_PRESERVATION`. The independent
serialized-input check returned
`PASS_PARENT_SELECTED_FLOOR_SERIALIZED_INPUT_AUDIT`; it confirms 50 physical
bodies, the 92 candidate bolt axes, twelve retained leg/runner axes, 66
Hillman axes, unchanged source geometry/laws/loads/material cards, exact
transformed floor equations, and source-point wrench preservation. Both checks
leave the proposal rejected and corner demands unusable.

No freeze or native run was made for this proposal. The commands and exact
source hashes used to create it are recorded in the two source-pin manifests.
The projection producer and adapter are write-once and refuse to overwrite
existing output.
