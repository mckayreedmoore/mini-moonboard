# Upper-right rail sampled motion

Status: nominal assembly diagnostic, 2026-09-24. The seated subassembly
clears the tested obstacles, but neither sampled straight approach is clear
throughout. This report does not establish assembly, removal, or capacity.

The [motion report](motion.json) consumes the retained
[twelve-duty composition](../wj12-integrated-static/README.md). It moves the
upper-right service rail, its inner G7 and outer WJ06 cleats, and four attached
rail-bolt stacks along the source local N direction. The four principal/side
bolt stacks and the two Hillman screws entering this rail are explicitly
absent. Their later installation and panel support are not demonstrated.

The scene contains 23 moving shapes and 1,046 stationary shapes. Its complete
wood inventory is 26 source members plus sixteen candidate parts: three move
and 39 remain stationary, including all six panels exactly once. Only three
right panels use candidate replacement shapes. Retained services, twelve
frame-bolt assemblies, occupied-axis proxies, other candidate stacks, twelve
legacy clips and 72 SDS envelopes remain obstacles. Temporary frame-bolt
tool envelopes are excluded from physical obstacles and listed separately.

| Signed N offset, mm | Positive-volume overlap pairs | Obstacle categories |
|---:|---:|---|
| −200 | 0 | None |
| −100 | 14 | Wood, T-nut, provisional hold keepout |
| −50 | 8 | Wood, wire, provisional hold keepout |
| −25 | 8 | Wood, wire, provisional hold keepout |
| −10 | 2 | Wood, provisional hold keepout |
| −5 | 2 | Wood, provisional hold keepout |
| 0 | 0 | None |
| +5 | 0 | None |
| +10 | 0 | None |
| +25 | 5 | Wire |
| +50 | 5 | Wire |
| +100 | 0 | None |
| +200 | 0 | None |

At +25 and +50 mm, the moving rail intersects `wire_079_G7_G8`,
`wire_089_H8_H7`, `wire_103_I7_I8`, `wire_113_J8_J7`, and `wire_127_K7_K8`.
Each reported intersection is 478.778720407 mm³. Negative travel also
intersects the upper-right panel. Clear distant poses do not establish a path
through the intervening overlaps. A supported panel/wiring staging sequence
needs investigation before repeating the movement screen; no wire removal,
disconnection, new slot, or physical impossibility is inferred here.

The actual run took 134.53 seconds. Thirteen unique poses are reused for
approach and reverse-order records. This is discrete sampling with a
1e−6 mm³ reporting threshold, not continuous swept-volume or tolerance proof.
Ten focused tests pass. Preflight repairs reconcile the complete source wood
inventory, optional bore-duty tags against pinned family records, and named
versus indexed frame-hardware aliases by per-bolt shape fingerprints.

The [manifest](sha256.json) binds the report and exact producer snapshot.
The report also binds the archived composition/static report hashes and
family source hashes. The source member inventory and all 66 canonical screw
axes are retained; two screw envelopes are absent only for this modeled step.
All release flags remain false. This is WJ12 evidence and must be rechecked
against subsequent complete-layout changes.
