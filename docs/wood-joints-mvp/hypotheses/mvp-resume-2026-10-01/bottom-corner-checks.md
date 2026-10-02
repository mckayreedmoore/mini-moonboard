# Both bottom outer joints in the working frame

## Current all-two-receiver clearance replay

The fresh same-state replay uses `two-receiver-frame-attempt03/` and its six
nominal states with finite fixed-force seating bounds. All 88 independent
candidate bolts include their modeled clearance; the four continuous bolts
and twelve retained bolts remain at zero clearance. Geometry and all 66
conditional Hillman laws are unchanged. A representative returned pose does
not establish a unique position or a movement envelope.

The left adjusted 92 ksi component comparison is **0.281891**, with concurrent
steel allowance **0.283884**, tangent-path **0.037044**, washer wood-pressure
**0.200974** and required washer strip stress **50.491 MPa**. The right lateral
comparison is **0.005684**. Existing bottom cleats and quarter-inch diameters
remain favorable under these explicit component scenarios; complete-joint and
physical-release flags stay false.

Current output: `bottom-corner-component-attempt06/component-results.json`
SHA-256 `e2ea2ce06eb4042e7a64b57f0ddc3c0f0a88113d7d12f327ce01e1e2179c19e9`.
It binds `member-screen-attempt02/all-two-receiver-clearance01/` and
`remaining-joint-screen-attempt04/all-two-receiver-92ksi/` to the same response.
Use these paths with the saved-array commands below. Earlier calculations,
source snapshots and temporary inputs remain preserved.

## Preserved six-joint comparison

Both bottom outer cleats now take up their modeled 1.15 mm relative bolt
clearance in the same frame as the two corrected top corners and the upper/lower
left outer service cleats. The reviewed bottom geometry, four quarter-inch
bolts per cleat, recorded loads and all 66 conditional Hillman paths are retained.
No stronger hardware or bottom-member enlargement is indicated by these
conditional component calculations.

## Coupled result

All twelve states, six zero-gap and six modeled-gap, satisfy the existing
static balance, constitutive, unilateral, no-slip floor-branch and rank gates.
Floor branches may change. The frame still assumes the declared Hillman
lateral/withdrawal stiffness; these springs have no purchased-product
resistance qualification. The other bolted joints retain zero lateral gap.

| Six-case nominal-gap result | Bottom outer left | Bottom outer right |
| --- | ---: | ---: |
| Maximum bolt shear | 251.337 N | 4.893 N |
| Maximum separate outer tie | 186.370 N | 15.850 N |
| Maximum local rail/side movement | 2.4501 mm | 0.1371 mm |
| Maximum local rail/side rotation | 0.2522° | 0.0940° |
| Adjusted individual lateral-reference ratio, 45 ksi scenario | 0.4176 | 0.00815 |
| Adjusted individual lateral-reference ratio, conditional 92 ksi | 0.2920 | 0.00570 |
| Concurrent axial/shear steel-reserve scenario, conditional 92 ksi | 0.2942 | 0.00570 |
| Cleat grain-parallel force / finished tangent-path reference | 0.03833 | 0.000746 |
| Displaced washer mean pressure / conditional wood reference | 0.20994 | 0.01786 |
| Maximum cell-mean contact pressure / conditional wood reference | 0.02055 | 0.00126 |
| Whole host-section N shear / smaller splitting characteristic reference | 0.03689 | 0.02561 |
| Required washer radial-strip bending stress | 52.742 MPa | 4.486 MPa |

Different maxima are not simultaneous. Each calculation uses one saved case
and its signed lateral components, tie, contact reactions and member loads.
The left `side_1` bolt in A1-rear governs the lateral-reference comparison.
Its preceding four-joint frame value was 682.380 N; the new clearance changes
the load distribution rather than the diameter or strength. The new six-joint
zero-gap sensitivity retains 674.670 N at the left corner. Neither sensitivity
is substituted for the nominal-gap working state.

The local motion is an affine fit to interface displacements, with its residual
retained in the frame record. It is not an adopted motion limit or complete
deformed-panel clearance result. Movement compatibility remains to be checked.

## Wood, group and washer calculation

[bottom_corner_checks.py](bottom_corner_checks.py) joins 48 bolt states,
16 finished paths with 32 actual STEP bore-tangent planes, 16 washer seats,
24 interface wrenches/contact states and 36 complete timber-body balances.
It reuses the unchanged geometry and calculation helpers instead of adding a
new contact or finite-element model. Signed host cuts come from the current
[member calculation](member-checks.md), including nodal gravity/climber loads,
all incident connectors, zero reactions and free couples.

The end-distance scenario uses the minimum rectangular grain-end distance
divided by 7D, capped at one. Component Cg uses the actual 33 mm bolt pitch
and a declared 3D equivalent width at the receiver loaded across grain. The
rail multiplier is 0.96818; the side multiplier is 0.99702. These are explicit
component adjustments, not acceptance of the complete oblique bolt group.
The finished tangent-path comparison uses only signed grain-parallel force.
Other crack paths and combined splitting remain separate from that result.

The supported washer reference uses the smallest saved annulus area with
combined hole/washer offset, 206.013 mm². All sixteen source seats support
the stated geometry scenario. Because the top-corner proposal changes both
side-host STEP files, the four bottom washer sweeps on those copies were
rechecked at 0.01, 0.05 and 0.1 mm inward depth. Their complete outside-bore
sweeps remain supported within the recorded 1e-6 fraction tolerance. This
recheck binds the current side-host copies; it does not transfer old STEP
acceptance by member name.

Some bolt pairs have zero net lateral force while retaining their signed
forces and couple. Their resultant-direction/pitch descriptors are null;
they are not rejected or replaced by an invented resultant direction.

The EN1995 Eq. 8.4 host comparison retains both loaded edges and complete
same-state section shear. Its characteristic values are not adopted design
resistances. The concurrent steel scenario reserves uniform axial stress
and an assumed parabolic shank shear field before recomputing the same
4450/5600 psi lateral helper used by the source screen. The reserve cannot
increase that source reference. It is not a prescribed NDS interaction rule.
The washer strip calculation assumes a 10 mm flat bearing circle; the metal
yield value and actual head/nut footprint remain unspecified.

## Maintained working result and remaining checks

Retain both bottom outer cleats and their existing quarter-inch bolt policy
in the conditional working model. Complete joint acceptance remains HOLD:
finished-section/local splitting transfer, full group applicability, washer
metal/actual footprint, assembly tool/removal routes and returned motion
compatibility are not supplied by these component references. Formal 47
criterion authority, reviewed geometry and physical-release flags are unchanged.

The new member screen retains 264 balances and 54,888 signed section traces.
Applicable elementary normal/shear references remain 0.541500/0.373619 in the
top rail. Its section, torsion and restraint limits remain explicit. The
remaining 92-axis screen now has no eligible individual reference above one
even at the 45 ksi sensitivity; its peak is a retained upper leg bolt at
0.75554. End-grain and continuous three-receiver bolts use their own methods.

## Evidence and reproduction

Local generated evidence is ignored; the maintained producer and this summary
are published. Earlier outputs, source snapshots and referenced temporary
files remain preserved.

- `all-outer-corner-frame-attempt01/comparison.json`: SHA-256
  `ec69b49c821a56fdde76d94148405f9f743e4f72add17c89d35af512be76f6a3`.
- Its `response.npz`: SHA-256
  `aa70480aa18c33bb1cbd7d3a53ff582a0c7a90c93487f92721619474ec251901`.
- `bottom-corner-component-attempt05/component-results.json`: SHA-256
  `5dd27a7397dfaceefdfcfafb8c69b5c050112148e6a868138d3fa3379f69a8d6`.
- Member evidence: `member-screen-attempt02/all-outer-clearance01/`;
  its source/output hashes are in `member-results.json`.
- Remaining axes: `remaining-joint-screen-attempt03/grade5-92ksi/`.

The initial component preflight used a wrong CSV filename; attempt02 then
stopped on the reused nonzero-resultant descriptor. Both source/failure records
are retained. Attempt03 preserves the initial diameter-specific steel reserve;
attempt04 aligns that reserve with the source helper; attempt05 adds the
changed-side-host washer rechecks. No stop was a physical frame or wood failure.
No software tests, native solve or independent review round ran for this work.

From the repository root, use fresh output directories:

```sh
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 uv run --offline --no-project --python 3.12 \
  --with numpy==2.2.6 --with scipy==1.15.3 --with osqp==1.0.4 \
  python docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/both_corner_frame.py \
  --service-joints --bottom-corners --output FRESH_FRAME_DIRECTORY

.venv/bin/python docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/member_screen.py \
  --clearance FRESH_FRAME_DIRECTORY --output FRESH_OWNED_MEMBER_DIRECTORY
.venv/bin/python docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/remaining_joint_screen.py \
  --clearance FRESH_FRAME_DIRECTORY --output FRESH_OWNED_REMAINING_DIRECTORY
.venv/bin/python docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/bottom_corner_checks.py \
  --clearance FRESH_FRAME_DIRECTORY --members FRESH_OWNED_MEMBER_DIRECTORY \
  --lateral FRESH_OWNED_REMAINING_DIRECTORY --output FRESH_COMPONENT_DIRECTORY
```
