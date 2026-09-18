# Curved-leg native section comparison: rejected recovery

Both contact-free CalculiX runs completed normally, but **neither mesh meets
the predeclared section-force recovery checks**. Do not use these native
section vectors to size the legs, joints or fasteners. This is not evidence
that the physical board failed or that deeper lumber is needed.

## What was actually tested

The [prospective protocol](leg-section-protocol.md) was committed before
execution. The original independent-ply leg meshes, nine unit-load cases,
material and fixed-bore fixtures were preserved byte-for-byte except for two
opposed internal surfaces and section-output requests. These are idealized
leg fixtures, **not the new complete perimeter candidate or full-board FEA**.
No contact, anchoring, glue or friction assumption was added.

The [geometry checks](leg-section-geometry.md) had already passed. The two
cuts are different jagged element interfaces; forces and moments are compared
at the same fixed reference, not by equating their scalar areas.

| Check | 40 mm mesh | 25 mm mesh |
| --- | --- | --- |
| Solver completion and owned-container cleanup | Completed | Completed |
| Original equilibrium, displacement and per-ply energy checks | All 9 cases pass | All 9 cases pass |
| Loaded inner-ply section cases | All 6 fail | All 6 fail |
| Unloaded inner-ply sections under outer-only loading | All 3 pass | All 3 pass |
| Largest relative native/integrated area difference | 3.654e−8 | 8.902e−8 |

The original 5% mesh-compliance comparison still passes all nine cases.
Twelve of the eighteen opposed-side section-vector mesh comparisons fail.
Equal-and-opposite section reports and accurate areas are therefore not
sufficient to establish accurate recovered force vectors.

For example, with a +1 N global-X load on the inner ply, the lower-cut force
reference is **(−1, 0, 0) N**. The reported vectors are approximately:

- 40 mm mesh: **(+1.039630, −0.044977, +0.075496) N**.
- 25 mm mesh: **(−0.285617, −0.365987, +1.312691) N**.

The large cross-axis errors and different mesh responses are not repaired by
simply reversing the sign. This experiment does not isolate their cause;
no solver defect, particular interpolation error or physical instability is
proven. The declared gates were not relaxed after observing these results.

## Evidence and next decision

[Archived native inputs, outputs, runtime identity and replay](../fea/results/leg_section_response/manifest.json)
preserve both runs, signed errors and terminal cleanup records. The pinned
existing solver image ran with no network, two-thread limits and a 120-second
per-mesh solver bound. Portable replay checks raw native DAT rather than
substituting synthetic section values; it does not rerun CalculiX.

Keep 2×8-foot100 as the development baseline. Publish and inspect the complete
connection layout, close real hardware/material choices, and obtain a
connection/load-path review before another size sweep. The section-output
route now has an explicit rejection result; it is not a reason for an
unbounded series of solver modifications. A future recovery method must pass
this known-load benchmark before it can supply design demands. Full-board
unanchored contact and physical connection capacity remain separate open gates.
