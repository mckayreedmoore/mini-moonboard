# Twelve end-grain axes: supported NDS route and stock alternative

The twelve exclusions have an explicit **NDS-2024 individual-bolt lateral
reference route without changing grain, geometry or hardware**. The ordinary
six yield modes require the end-grain provisions: use the block as the main
member, its perpendicular dowel bearing strength, and **Ceg = 0.67**. Omitting
Ceg would be incorrect. The former nulls can therefore receive conditional
component references; this does not close complete-joint detailing or acceptance.

[end_grain_route.py](end_grain_route.py) reuses
[remaining_joint_screen.py](remaining_joint_screen.py), its existing lateral
helper and the exact saved nominal-gap arrays in
[top-and-service-frame-attempt02](top-and-service-frame-attempt02/). It reads
[corner-frame-attempt01](corner-frame-attempt01/)'s model/material binding and
1888 row identities. The maintained producer also accepts an explicit clearance
directory and a fresh output directory for the parent's later all-outer-corner
response; the numerical results below preserve the earlier four-joint source.
It does not consume old native force results, solve a
frame, import/rebuild CAD, change member/material/operator authority, run tests,
review agents, or stage/commit anything.

## Applicable primary provisions

The official local [NDS source cache](../upper-block-strength-2026-10-01/source-cache/)
is sufficient. PDF hashes come from `top_corner_local.PINS`; the publisher URLs
and retrieval details are in its [source-bounds.json](../upper-block-strength-2026-10-01/source-cache/source-bounds.json).
The cached files contain specification text, despite their “withCommentary” names.

| Primary provision | Application here |
| --- | --- |
| [NDS Chapter 12](https://awc.org/wp-content/uploads/2026/09/AWC_NDS2024_withCommentary_20260911_Website_Chapter-12-Dowel-Type-Fasteners.pdf), §12.3.1 and Tables 12.3.1A–B, printed pp. 91–92 | Use the minimum of the six single-shear modes. Member faces must be in contact, the lateral component perpendicular to the bolt, and placement satisfy §12.5. |
| §12.3.3.4, p. 92 | For D ≥ 1/4 in with the main-member bolt axis parallel to fibers, use Fe⊥ for that member. Every excluded receiver satisfies this declared geometry. |
| Table 12.3.3 and Table 12.3.3A, pp. 93–94; §12.3.4, p. 95 | Conditional DF-L SG 0.50 gives the existing rounded Fe║/Fe⊥ = 5600/4450 psi. The header uses its actual lateral-force angle to horizontal grain. The block's lateral angle is 90°, so Kθ = 1.25. |
| §12.3.5 and §§12.3.6–.7, p. 95 | Use receiving lengths along the bolt. Fyb and smooth-body diameter remain explicit conditional inputs; modeled occupancy does not establish delivered shank/thread coverage. |
| §12.5.2.2, p. 100 | Multiply the minimum lateral reference Z by Ceg = 0.67 once. This is an end-grain **lateral** provision, not a lag-screw withdrawal rule. |
| §12.3.9.1, p. 96 | Assess lateral and axial components separately, with ample bearing area for the axial component. §12.4's screw/nail withdrawal interactions are not a through-bolt interaction formula. |
| [NDS Chapter 11](https://awc.org/wp-content/uploads/2026/09/AWC_NDS2024_withCommentary_20260911_Website_Chapter-11-Mechanical-Connections.pdf), §§11.1.2–.3, 11.2.3 and 11.3; Chapter 12 §12.6.3 | Local/eccentric member stresses, metal parts, placement and group/service adjustments remain necessary. [Appendix E](https://awc.org/wp-content/uploads/2026/09/AWC_NDS2024_withCommentary_20260911_Website-Appendix.pdf), E.1, concerns parallel-grain local action; its parallel tear-out formula is not an end-grain splitting capacity. |

“Main” and “side” are the yield-model member roles. They do not change physical
head/nut direction, receiving geometry, or force sign. The thick block is main;
the 38.1 mm header is side. Adjacent saved raw receiving intervals meet without
a gap. Full smooth-body bearing and zero face separation remain conditional
scenarios; the route does not claim observed fabrication or load-dependent
contact opening is already qualified. Fyb = 45/92/106 ksi retains the parent's
existing hypotheses. The 92 ksi Grade 5 tensile-yield scenario is not a
guaranteed, product-qualified bending capacity.

## Latest six-joint parent integration

The parent has calculated the 72 states from
`all-outer-corner-frame-attempt01/` into a fresh `end-grain-route-attempt02/`.
This source includes both bottom outer clearances as well as the top corners
and left outer services. The same applicable NDS route peaks at
**0.368424 / 0.257668 / 0.241692** for 45/92/106 ksi. The governing axis remains
`center_principal_header_left_2` in K12-rear: **146.621 N** lateral force,
zero simultaneous outer tie, and **569.032 N** conditional 92 ksi reference
after Ceg. The force on its cleat is `(134.235199, -58.980838, approximately 0) N`.
Other required adjustments and complete-joint checks remain separate.

Its `route.json` SHA-256 is
`f95fdb55eeee89d68be2e516e017d8d40d1ef4f7f9960c93e4895f53541c7f28`.
The parent also read the pinned Chapter 12 text at §§12.3.3.4 and 12.5.2.2,
confirming the perpendicular main-member bearing route and Ceg = 0.67.
No grain reorientation is selected: the existing geometry already has a
supported individual reference. The four-joint table below stays historical.

## Exact receivers and preserved four-joint signed results

Every axis below has direction ±global Z. **Only the listed block has grain
parallel to the bolt**: both its frozen descriptor and the frame's material
orientation assign L = global Z. The other receiver is `base_header`, with
grain global X. The condition is present in the source material map, not a
measurement of delivered lumber.

| Exact axes | Parallel-grain receiver | Main / side bearing lengths, mm |
| --- | --- | ---: |
| `center_post_header_left_1`, `_2` | `center_post_cleat_left` | 128.9 / 38.1 |
| `center_post_header_right_1`, `_2` | `center_post_cleat_right` | 128.9 / 38.1 |
| `center_principal_header_left_1`, `_2` | `center_principal_cleat_left` | 134.7 / 38.1 |
| `center_principal_header_right_1`, `_2` | `center_principal_cleat_right` | 134.7 / 38.1 |
| `knee_outer_left_inner_header_1`, `_2` | `knee_outer_left_inner_frame_block` | 139.0 / 38.1 |
| `knee_outer_right_inner_header_1`, `_2` | `knee_outer_right_inner_frame_block` | 139.0 / 38.1 |

[six-case-signed-states.csv](end-grain-route-attempt01/six-case-signed-states.csv)
contains **72 simultaneous states**: a12-rear, a12-forward, a12-left,
k12-right, k12-rear and a1-rear for each axis. It preserves raw row numbers,
both signed scalars/directions, XYZ forces on both named bodies, force on the
end-grain block, and the signed outer tie with its own bodies/direction.
Positive scalar force acts in its row direction on the first body; the second
receives its negative. The first body is **not always the header**. The axial
tie is a separate action, not an invented local shear-plane axial stress.

| Axis | Governing case at 92 ksi | V, N | Same-state T, N | V/(0.67 Z), 92 ksi |
| --- | --- | ---: | ---: | ---: |
| `center_post_header_left_1` | a12-forward | 136.678 | +357.489 | 0.241885 |
| `center_post_header_left_2` | a12-forward | 105.897 | +82.768 | 0.190406 |
| `center_post_header_right_1` | a12-forward | 117.637 | +251.009 | 0.206431 |
| `center_post_header_right_2` | k12-right | 72.222 | +56.233 | 0.130135 |
| `center_principal_header_left_1` | k12-rear | 112.444 | +187.716 | 0.199985 |
| `center_principal_header_left_2` | k12-rear | 149.217 | 0 | **0.262126** |
| `center_principal_header_right_1` | a12-rear | 109.454 | +180.799 | 0.194642 |
| `center_principal_header_right_2` | k12-right | 126.813 | +7.526 | 0.223742 |
| `knee_outer_left_inner_header_1` | a12-left | 112.403 | +122.429 | 0.195808 |
| `knee_outer_left_inner_header_2` | a1-rear | 77.376 | +83.534 | 0.141847 |
| `knee_outer_right_inner_header_1` | k12-right | 114.519 | +114.538 | 0.199519 |
| `knee_outer_right_inner_header_2` | k12-right | 47.121 | +50.384 | 0.082432 |

The governing state applies **(+137.184214, −58.704905, approximately 0) N**
to `center_principal_cleat_left`, with the opposite force on the header.
At 45/92/106 ksi, 0.67Z is **398.126081 / 569.256877 / 607.287898 N**;
ratios are **0.374799 / 0.262126 / 0.245711**. Those are also the maxima
over all 72 states. No state exceeds these component references. They precede
Cdelta, Cg and any other applicable adjustment; they are not adopted Z′ values.

The finite next calculation is finished placement and complete transfer for
these six block/header joints using the supplied simultaneous actions: bind
end/edge/spacing and Cdelta, the nonuniform group treatment, perpendicular
local/splitting and member stresses, axial seats, and steel/contact/couple
transfer. Ordinary end-grain reference applicability itself is no longer a
missing input. No stock change is needed merely to obtain this reference.

## Separate stock/grain alternative with identical shapes and axes

Fresh full 4×6 blanks **can** produce all six existing finished shapes with
grain global Y. Each block has both Z header bolts and X companion bolts;
perpendicularity to both fixes the new grain to ±Y. Grain X would make the
companion bolts end-grain. An oblique grain would not give perpendicular
bolts in both families. This proposal re-cuts stock; rotating an already cut
block would change its occupied shape.

The stock assumption is a sound DF-L blank with an actual **88.9 × 139.7 mm**
cross section in global X/Z, with its long grain along Y. Crosscut to the Y
length below, rip the X/Z amounts, and reproduce the same finished faces and
holes. Dimensions are envelopes, not instructions to cut the reviewed model.

| Both left/right members | Existing finished X × Y × Z, mm | Minimum finished grain length Y, mm | Total trim from blank X / Z, mm |
| --- | --- | ---: | ---: |
| `center_post_cleat_*` | 88.9 × 88.9 × 128.9 | 88.9 | 0 / 10.8 |
| `center_principal_cleat_*` | 83.9 × 139.7 × 134.7 | 139.7 | 5 / 5 |
| `knee_outer_*_inner_frame_block` | 88.9 × 133.35 × 139.0 | 133.35 | 0 / 0.7 |

Cut lengths require ordinary kerf/finishing allowance. The post and knee
blanks retain the full 88.9 mm X thickness; the knee blank has only 0.7 mm
total Z allowance. Undersized delivered stock cannot supply that envelope.
No laminations, larger finished blocks, changed axes or new hardware are needed
for this geometric fit. Conditional DF-L No.2 remains the final-piece member
strength assumption; ripping does not authenticate grade, knot placement or
old size factors. Connection bearing uses SG 0.50 without a grade premium
(§11.2.1.1). Ring orientation remains unobserved: parent can retain alternatives
L/R/T = (Y, X, −Z) and (Y, Z, X), with both checked independently when integrated.

[stock-grain-proposal.json](end-grain-route-attempt01/stock-grain-proposal.json)
enumerates **all 24 affected physical bolt axes and every receiver's old/new
grain**. The twelve Z axes change block alignment from parallel to perpendicular.
These twelve X companion axes stay perpendicular to both old and proposed grain:

- `center_post_left_1`, `_2`; `center_post_right_1`, `_2`.
- `center_principal_left_1`, `_2`; `center_principal_right_1`, `_2`.
- `knee_outer_left_side_1`, `_2`; `knee_outer_right_side_1`, `_2`.

The last four remain continuous three-receiver bolts; grain reorientation
does not establish a symmetric double-shear route. No Hillman receiver in
the consumed connection inventory is one of these six blocks. All 66 panel
axes, bolt axes, surfaces and finished envelopes stay at their source locations.
The twelve Z-bolt block washer normals change from parallel to perpendicular
grain, so their wood-pressure basis changes as well. All load-to-grain angles,
group/local sections and contact bearing must follow the proposed grain.

Placement changes are real. For Y grain, the header pairs' minimum grain-end
distances are **26.95 mm** at post blocks, **35.7 mm** at principal blocks,
and **20.0 mm** at knee blocks. Conservative 7D comparisons are
0.606299, 0.803150 and 0.449944. The knee value is below the softwood
parallel-tension minimum 3.5D = **22.225 mm**. Fourteen of the 24 saved knee
axis/case states have a signed Y component toward that short end; exact cases
and signs are in the proposal. These are explicit component placement
comparators; no unverified 2024 intermediate-angle interpolation is asserted.

Thus Y grain is a valid stock-envelope proposal, not an automatic twelve-axis
side-grain detailing pass. A finite alternative if the parent selects it is
to move each knee header axis toward the block's Y center: **2.225 mm** reaches
the 3.5D component minimum without tolerance, **5.4 mm** provides 25.4 mm ends
with conservative Cdelta = 4/7, and **24.45 mm** provides full 44.45 mm (7D)
ends. The latter reduces pair spacing from 93.35 to 44.45 mm. These are
unapplied geometric options requiring new header passages, bore/washer
clearance and changed joint actions; no saved force is acceptance for moved
axes. The smaller current-model route is the explicit end-grain provision above.

Parent integration of Y grain would also change six orthotropic orientations
and their stiffness; the current saved forces cannot become forces for that
new model. This packet makes that proposal concrete and leaves source inputs
and operators intact.

## Reproduction and retention

Run `uv run python docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/end_grain_route.py`
from the repository root into an absent `end-grain-route-attempt01/`. The
producer preserves an existing attempt. The initial source guard stopped
before output creation when the shared remaining-joint helper gained one
additional frame-scope label; that change did not alter the reused functions.
The completed run binds the updated helper and the same requested force source.

For the later parent-frozen source containing both bottom corners, both top
corners and both left outer service cleats, use a new parent-owned output:

```sh
uv run python docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/end_grain_route.py \
  --clearance docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/all-outer-corner-frame-attempt01 \
  --output docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/end-grain-route-attempt02
```

The producer recognizes `coupled_outer_corner_frame_clearance/v1`, binds the
same corrected model/row identities, and pins that source's comparison to
`ec69b49c821a56fdde76d94148405f9f743e4f72add17c89d35af512be76f6a3`
and response to
`aa70480aa18c33bb1cbd7d3a53ff582a0c7a90c93487f92721619474ec251901`.
Both files were read for metadata/hash binding by the worker; the parent later
executed the command above, with its result summarized in the latest-integration
section. The original attempt01 result files remain byte
unchanged. Its original [producer snapshot](end-grain-route-attempt01/producer.py.snapshot)
matches the `producer_sha256` in its result, preserving reproducibility after
the CLI addition. Any later replay receives its own producer/source hashes;
the preserved table above must not be promoted to the new source's result.

[route.json](end-grain-route-attempt01/route.json) records consumed source
hashes, Python/NumPy versions, output hashes, all governing states and claim
limits. Outputs remain ignored and compact. The producer, this applicability
record, signed states and stock proposal remain active for parent integration;
there are no new raw/native runs to archive or prune. Parent owns summaries,
frame integration, bottom-left outer work and commits.
