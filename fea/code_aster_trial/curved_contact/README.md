# A09 quadratic curved-contact method screen

This fixture checks a small, representative patch from A09 contact pair 021.
It preserves the source mesh's C3D10/TRIA6 geometry and solves only a crop of
95 slave-side plus 88 master-side contact faces (183 adjacent C3D10 cells,
658 retained nodes). The crop is bounded, has connected retained volumes and
contact patches, and keeps the 110 SCUT and 136 MCUT support nodes disjoint
from their respective contact nodes. It is not a full-joint model or an
acceptance result for the wood-joint candidate.

The crop generator [generate.py](generate.py) validates the pair-021 source
membership against [a09_topology.py](../a09_topology.py), orients both sets of
faces outward from their parent C3D10 volumes, writes
[curved_contact.mail](curved_contact.mail), and creates
[geometry-oracle.json](geometry-oracle.json). It does not invoke Code_Aster.
Coordinates are written at 17 significant digits. The oracle finds the global
nearest point over every source master TRIA6: each quadratic face's six
Bernstein control points give a convex-hull AABB distance lower bound, and
candidate faces are solved with constrained SLSQP from the corner-triangle
projection and simplex landmarks. The signed gap is the slave-to-projection
vector dotted with the outward master unit normal. All 218 retained slave
nodes start with positive gaps from 0.5710310 to 0.5749879 mm; translating the
slave patch by +0.50 mm along the frozen closing direction leaves every node
open, with a minimum gap of 0.0738439 mm. The seed is source node 61143.

The source quadratic curvature is material: 508 of 549 contact edge midside
offsets exceed the recorded 1e-7 mm roundoff floor, and the largest offset
from the straight corner chord is 0.3449731 mm. Both surface sets are outward
oriented; their corresponding projected slave and master outward normals
oppose. The prescribed closing direction is the negative exact master normal
at the seed projection, `[0.8516964641, -0.4014344300, 0.3368434822]`.

The fixed displacement history is `0, -0.10, -0.20, 0, +0.50, +0.60,
+0.65, +0.60, +0.50, 0, -0.10, +0.60 mm` at `INST=0..11`. The first four
distinct states and the +0.50 mm state are geometric opening checks; the
+0.60/+0.65 mm steps exercise closure and the later steps exercise unloading,
reopening and reclosure. Supports impose rigid translation on SCUT and hold
MCUT fixed; they do not prescribe slave contact-node normal displacements.
The material constants are generic fixture values and are not wood
properties. The displacement-controlled force has no analytical load oracle.

The post-run checker
[check_curved_contact.py](check_curved_contact.py) maps Code_Aster's numeric
`NOEUD` table identifiers back to the named `.mail` nodes using their frozen
1-based `COOR_3D` order. It verifies node coverage and exactly one initial
`INST=-1` record plus the 12 screened times in every table; the initial row
values are ignored because that pre-step contact field may be unevaluated.
For each evaluated state it reports all local gaps, statuses and RN vectors.
`CONT=0` is open; any `CONT>0` is treated as active, including intermediate
values that can arise from field interpolation. An unpaired `CONT=-1`, or a
status outside `[-1,2]`, fails.

The frozen screening limits are:

- Open states: maximum difference from the independent geometric gap oracle
  at most 0.02 mm, no negative local `JEU`, sum of local RN vector magnitudes
  at most 0.05 N, and (when the displacement table is supplied) slave rigid
  motion error at most 0.02 mm.
- Every slave node: penetration no greater than 0.01 mm. At active nodes,
  `|JEU|` must be at most 0.01 mm.
- Compression/reclosure: contact RN magnitude and its projection along the
  closing direction must each exceed 0.05 N.
- Force consistency: `||sum(RN) - sum(FORC_NODA at SCUT)||` and
  `||sum(RN) + sum(FORC_NODA at MCUT)||` must each be no greater than
  `max(0.05 N, 0.001 * largest resultant magnitude)`.
- The frozen absolute global nonlinear residual is 1e-9 N; the native log is
  checked separately by the parent.

The force checks are sign and equilibrium consistency checks, not an
analytical pressure oracle. The prior planar primitive found RNX equal in sign
to its independently extracted constrained-end `FORC_NODA`, while the
physical force on the slave body was opposite. This coupon therefore freezes
the expected output convention as `RN = SCUT` and `RN = -MCUT`, and reports
the full signed vectors. Passing these balances does not establish local
pressure accuracy, material response, joint resistance or another pairing's
behavior.

The input history is preserved across attempts. `native_input/` is the first
native snapshot. Its first launch found that an unwrapped TETRA10 record
exceeded the parser's 80-column limit. `native_input_v2/` wraps connectivity
at token boundaries; its copied oracle records the original mail hash and
exact whitespace-token equality, so no node, coordinate or connectivity data
changed. The next run snapshot is `native_input_v3/`, with that same wrapped
mesh and only `ALGO_RESO_GEOM='NEWTON'` changed after the documented geometry
fixed-point iteration failed at the exact-zero opening step. See the latest
attempt's readiness and result files for the parent-reviewed run status.

Attempt03 completed in the pinned image. The original all-state
[`contact-audit.json`](../../../docs/wood-joints-mvp/hypotheses/code-aster-candidate-checks-2026-09-27/curved-contact-attempt03/contact-audit.json)
records ten threshold failures, including an apparent open-gap mismatch at
node N000360/source node 58707. A subsequent source-ordered review found that
this compared a quadrature-point `JEU` value stored in a node-indexed slot with
a gap projected from the mesh node. In continuous contact, Code_Aster evaluates
gaps at integration samples; the v17.4 AUTO TRIA6 rule has six interior
samples per face. Its output writer maps those sample values to node slots by
the local contact-point index, and later visits can overwrite an earlier value
at a shared node.

The parent-reviewed
[`parent-contact-sample-gap-review.json`](../../../docs/wood-joints-mvp/hypotheses/code-aster-candidate-checks-2026-09-27/curved-contact-attempt03/parent-contact-sample-gap-review.json)
replays that source ordering and independently projects all 570 samples in
each saved state onto the deformed curved master surface. It passes all 12
states: the maximum sample-matched `JEU` difference is about `1.3e-7 mm`, and
maximum penetration is `0.002635 mm` against the frozen `0.01 mm` limit. The
source review is against the official 17.4.0 tag; exact source-to-runtime
binary identity is not established. The original failure record remains
unchanged; this second audit corrects its comparison basis rather than
changing the frozen screen.

The separate force-resultant check still fails. At +0.60 mm and +0.65 mm, the
sum of reported nodal `RN` differs from the independently extracted cut sides
by 10.02 N and 26.82 N against limits of about 0.12 N and 0.40 N. The cut sides
themselves balance to `1.23e-12 N`. A paired native control now reverses only
the 95 slave `TRIA6` record lines. Across loaded states, SCUT and MCUT
resultants change by at most `5.13e-11 N`, and displacements by at most
`1.09e-13 mm`, while the summed nodal `RN` changes by `0.98–7.00 N`; the
control still fails its RN-to-cut checks by `10.95–33.69 N`. This confirms
order sensitivity of the reported curved nodal force output, but does not
explain the magnitude of its absolute mismatch. See the paired
[order-control audit](../../../docs/wood-joints-mvp/hypotheses/code-aster-candidate-checks-2026-09-27/curved-contact-cell-order-control-attempt01/paired-result-comparison.json)
and its all-state [screen](../../../docs/wood-joints-mvp/hypotheses/code-aster-candidate-checks-2026-09-27/curved-contact-cell-order-control-attempt01/parent-contact-order-control-screen.json).

The output-only [LAGS_C audit](../../../docs/wood-joints-mvp/hypotheses/code-aster-candidate-checks-2026-09-27/curved-contact-attempt03/parent-lags-c-reconstruction-audit.json)
calibrates the reference-area integration and sign on the existing flat
fully-active coupon (analytic `−3000 N`, error `4.6e-13 N`). On the curved
crop its full-face six-point AUTO integral differs from the cuts by
`0.0011–0.329 N` and is invariant to cell order. This is empirical closure,
not a reconstruction of native residual force: source review shows the
`STANDARD` residual uses clipped overlap quadrature, augmented traction with
an active-set gate, and the ray-gap derivative. Do not infer curved pressure
accuracy or force recovery from that integral. The cause of the curved
RN-to-cut mismatch remains unresolved.

The bounded [body-restricted force check](body_restricted_force/README.md)
now validates stable global resultants on both curved bodies and their cuts,
including a first-moment check and paired cell-order control. It does not
resolve local pressure or the `RN` field's discrepancy. The source-aligned next
step is to reproduce the pinned-tag residual path on the existing flat
fully-active coupon, then test a two-face partial-overlap coupon with both
active and inactive residual quadrature points. A faithful replay must recover
the clipped overlap, FPG7 reference weights, projected master geometry,
ray-gap derivative, interpolated multiplier and active-set gate; `AUTO`
output samples and nodal `CONT_NOEU` slots are not substitutes. If this cannot
be validated from the saved fields and source alone, the coupon needs a
narrowly instrumented output path before full-joint translation.

Version 17's [contact pairing and geometry guidance](https://code-aster.org/doc/v17/manuals/man_u/u2/u2.04.04/Appariement.html)
requires outward surface normals and explains both geometry algorithms. Its
continuous-contact warning says curved TRIA6/QUAD8 can violate local contact
conditions because enforcement is averaged, yielding small positive or
negative local gaps. The sample-matched review measures every saved quadrature
sample against the exact curved geometry; convergence alone does not establish
contact accuracy. The
documented `NEWTON` geometry option updates the pairing each iteration and
uses the Newton displacement increment as its geometry criterion. The guide
also says it can be less robust than `POINT_FIXE`, so this single crop and
attempt do not qualify the method generally.

After a parent-reviewed run, invoke the checker with the exact input snapshot
and matching tables, for example:

```sh
.venv/bin/python fea/code_aster_trial/curved_contact/check_curved_contact.py \
  CONTACT.csv SCUT.csv MCUT.csv \
  --oracle fea/code_aster_trial/curved_contact/native_input_v3/geometry-oracle.json \
  --mail fea/code_aster_trial/curved_contact/native_input_v3/curved_contact.mail \
  --displacement-table SDISP.csv --json curved-contact-audit.json
```

Replace the snapshot and table paths with those frozen for the completed
attempt. The generator and checker are independent of the native solver;
readiness review, solver execution, convergence-log review and raw-output
freezing are parent-owned. A passing result is only a bounded method screen
for this extracted pair-021 crop, not a joint or candidate acceptance.
