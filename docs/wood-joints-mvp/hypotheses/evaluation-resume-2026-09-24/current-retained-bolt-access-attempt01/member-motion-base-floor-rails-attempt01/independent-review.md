# Independent review of paired base-floor rail motion attempt01

This read-only review covers the paired rail producer, its parent report,
readiness and execution records, the source-pinned helpers and prior leg
reports, and the attempt04 STEP manifest/readback. I did not run CAD, native
analysis, or regenerate geometry. The five focused metadata/bounding-box tests
pass.

The two reports support separate 1.0 mm outboard translations of
`base_floor_left` along `-X` and `base_floor_right` along `+X`, with no
reported positive-volume intersection above the configured `1e-6 mm³`
tolerance in the modeled scenes. These are minimal separation steps for the
already-butting rail locations. They are not full rail extraction travel,
handling paths, or a complete removal sequence, and they establish no positive
clearance margin.

## Route and obstacle accounting

Each direction is derived from that rail's own X-bound midpoint and verified
against a planar face on the exact target STEP shape: the left face normal is
`-X`; the right face normal is `+X`. The paired cases are independent. The
other floor rail remains in its source position in each one.

For each 1.0 mm endpoint, the target BBox is disjoint from all 148 stationary
obstacle BBoxes. Five obstacles whose source boxes overlap the target in
transverse Y/Z are used to calculate endpoint travel; their minimum axial gap
is 1.0 mm. The other 143 have strict transverse BBox separation. These are
endpoint checks, not an extraction-distance or physical handling claim.

The producer builds a convex hull from the source and translated target
vertices, and its report records source and endpoint BRep containment. The
collision helper receives all 148 stationary obstacles for each hull. Its
BBox broadphase rejects all 148, so it runs zero exact BRep intersection
tests. Exact nonconvex refinement is consequently marked not needed. The
result supports no reported positive-volume overlap for each modeled
one-millimeter translation; it does not report a measured gap over the
continuous path, and the report correctly leaves positive clearance false.

The scene counts reconcile to 17 stationary timbers plus 131 modeled wire
BReps, with zero retained hardware roles, for 148 obstacles. Each case starts
from a 191-shape imported subset (target plus imported stationary bodies),
then removes the two prior-moved legs and all current retained bolt-role
families from its obstacle set. The input bundle itself contains 20 timber
members, 60 physical roles for 12 retained frame-bolt stacks, and 131 modeled
wires. The producer verifies all 211 listed STEP file hashes and binds to the
full-export readback result.

## Conditional prior-removal state

The two prior leg reports are hash-pinned. The producer checks that each
report has its expected exact-sweep-clear status, direction, removed retained
axes, and no candidate-axis dependency. The paired run assumes those two
legs were moved outboard, their eight retained axes were removed, and all
four front-floor retained bolt stacks were removed before the rail moves.
Removal of those four stacks is a condition of this scene; this report does
not screen their tool operation or prove their physical removal.

The export contains no candidate connector geometry or candidate wood
corner-cleat bodies. The report explicitly marks cleat removal as unscreened
and assumes each cleat is absent or was independently removed; it also states
that removing bolts does not imply the wood cleats disappear. This screen
therefore says nothing about a rail path while a candidate cleat is present.
The report's statement that all 92 candidate connector axes/stacks were
removed in a separate screened operation is likewise an operation-state
assumption here: this producer pins no prior 92-axis operation report. The
manifest proves those candidate shapes are absent from this export, not that
the operations were performed or that they form a completed sequence. The
top-level `full_removal_sequence_established` and
`actual_tools_or_owner_compatible_transport_established` fields correctly
remain false.

## Provenance and record limits

The report's producer digest matches the on-disk source and pre-run readiness
record (`13568cd8…01fe1e9d`). I verified its manifest, source-inventory,
readback, shared-runner, face-sweep helper, endpoint-helper, prior left/right
leg report pins, and all 211 manifest-listed STEP hashes. Both prior leg
reports have the hashes and statuses required by the producer. The parent
execution record reports return code 0; the report has SHA-256
`2ce63b03…76296e715`. The execution record itself does not store that report
digest, so this review records the current report hash. The parent readiness
record pins the producer, tests, and README before the run.

The screen conditions on the candidate axes/stacks, candidate cleats, prior
legs, and retained bolt stacks being absent as described above. All 131
modeled wires stay stationary, while actual cable routes, panels, holds,
lights, supports, capture surfaces, staging, workspace, tools, and handling
are not represented. The results apply only to the two selected one-millimeter
modeled separation moves and do not establish physical removability or a
whole-frame disassembly sequence.
