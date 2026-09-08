# Current wider-frame asymmetric load diagnostics

These results belong to **`wide-principal-development`**, the current inspection
candidate. They use its authenticated 40 mm bulk mesh, not the predecessor's
mesh or joint node IDs. All nine linear basis cases completed. They generate
216 combined scenarios across three holds, four weights, two weight factors,
and nine horizontal-force directions (including no horizontal force).

**This is conditional stiffness and aggregate load-path evidence, not a
fastener capacity, unanchored-stability or climbing approval.** The mesh retains
ideal wood-to-wood bonds, including leg plies and the upper panel edges touching
the legs. Inserts, bolts, real joint slip, separation and material failure are
not represented. All floor nodes are fixed in XYZ, including the kicker bottom;
frame gravity is absent from these load cases.

## Loaded-point displacement

| Climber reference | Largest displacement among the 54 scenarios at that weight |
| --- | ---: |
| 150 lb / 68.0 kg | 1.384 mm / 0.0545 in |
| 200 lb / 90.7 kg | 1.752 mm / 0.0690 in |
| 250 lb / 113.4 kg | 2.120 mm / 0.0835 in |
| 300 lb / 136.1 kg | 2.488 mm / 0.0980 in |

All four maxima occur at K12, with twice the reference weight acting downward
and 300 N acting in global positive Y (outward). The 300 lb case applies
approximately 2.669 kN downward plus 300 N outward. The factor-two static case
is not a simulated fall or a complete dynamic design-load specification.
These are loaded-node displacements, not maximum displacement everywhere in
the structure. Single-node stresses are not qualified.

A12, K12 and F6 map to current face-mesh nodes within 8.120, 3.631 and 7.596 mm
of their intended hold axes, respectively. No offset/standoff moment for the
hold body is included. The earlier five-equally-loaded-node result of roughly
1.76 mm at 2.4 kN answers a different loading question.

## Aggregate leg and base actions

Ownership was reconstructed from current CAD against the current mesh. Each leg
has 95 floor nodes. The base has 871 unique floor nodes, spread across six post
bottoms and both kicker bottoms. Its eleven-member free body comprises the
header, six posts, two kicker panels and two gussets. Shared contact-boundary
nodes are counted once when recovering its resultant.

The full report contains six-component world and board-local resultants at
explicit moment references for every scenario. Leg references are the centers
of the respective four leg/rim bolt axes on the board interface; the base
reference is the current header's center. A reference near bolts does not turn
an aggregate resultant into a bolt-group demand.

For the 300 lb maximum-displacement scenario, the global vertical floor
resultants are approximately:

- left leg: **+228 N**;
- right leg: **+3,002 N**;
- base, including kicker: **−561 N**.

Their sum balances the applied downward load. The negative base value means
this fixed-floor model supplies a net **downward restraint** at the base.
An unanchored floor cannot supply that tensile restraint. This is not proof of
the real frame's tipping behavior: actual contact redistribution and self-weight
are omitted here. It is direct evidence that this constrained result must not
be treated as the real unanchored support state. Do not add anchors or ballast
silently to make the analysis applicable.

Both legs still transfer load through the ideal rim **and** upper-panel edge
interfaces. Base actions still combine bearing, gusset, backing and kicker
paths. Neither may be divided equally among the visible bolts. Actual fastener
sharing, resistance and independent-ply behavior remain unresolved.

## Verification and evidence

Every basis passes complete load-history and force/moment checks. The largest
absolute residual component among the nine bases is 0.000068 N in force and
0.045 Nmm in moment (rounded upward). Each mapped node has positive, reciprocal
three-axis compliance within the documented numerical tolerances. All 216
aggregate partitions are translated to a common origin and checked against
the full floor reaction wrench.

The [source-bound report](../fea/results/wide-asymmetric/summary.json) includes
the reconstructed ownership, all scenarios, references, scope, source hashes,
and hashes for nineteen compressed replay files. Preparation, ownership and
all results are independently rebuilt in the evidence tests. A separate scalar
test sums nodal forces and reference-point moments for every scenario.

```bash
uv run pytest -q tests/test_wide_asymmetric.py tests/test_wide_joint_ownership.py \
  tests/test_publish_wide_asymmetric.py tests/test_wide_asymmetric_evidence.py
```

The nine actual bases used CalculiX 2.21 in the existing Docker release image,
two OpenMP threads, and a 600-second limit per three-basis hold job. Each job
completed in about 52 seconds. No new solver dependency or CAD redesign was
introduced. The previous incomplete panel-contact attempt remains preserved
separately; these bonded results do not repair or replace it.

The [connection qualification ledger](connection-qualification-ledger.md) still
governs the remaining demand, resistance, stock, installation and physical
validation gates. Additional stiffness is not, by itself, proof that the heavier
principals are necessary or that their complete connection is adequate.
