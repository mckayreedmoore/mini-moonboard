# Current outer-corner local wood screen — attempt01

This bounded screen converts the current introduced corner-bolt geometry into
candidate net-section inputs for the outer knee spine and inner frame block.
It covers only BG001, BG003, and BG045 (six introduced axes). The twelve
retained original frame/runner bolt arrangements are outside scope.

The pinned finished-member manifest gives axis-aligned XY envelopes of
38.1 × 139.7 mm for `knee_outer_left_spine` and 88.9 × 133.35 mm for
`knee_outer_left_inner_frame_block`. The existing 48-ray BG001 and 72-ray BG003
queries show modeled 7.5 mm bores. The screen treats each X-axis bore crossing a
section normal to the proposed +Z grain as a full-width strip. For the inner
block it also subtracts both BG045 Z-axis bore circles present in the same XY
section planes at BG003's two X-bore center stations. Their centers are independently reconstructed from
the BG003 mid-depth `e±` ray void intervals and agree with the BG045 axis
centers. The circle centers are more than one bore diameter from each BG003
strip center, so this simple union does not double-subtract an overlap. The
BG045 circles do not physically intersect the BG003 X bores; they are simply
present in the same XY section planes, where the modeled voids are spatially
disjoint.

| Member / section plane | Candidate area after modeled bores (mm²) | Uniform +Z tension coefficient (MPa/N; MPa/kN) |
|---|---:|---:|
| Spine, at each BG001 or BG003 X-bore center | 5,036.820 | 0.000198538; 0.198538 |
| Inner block, at either BG003 X-bore center, including both BG045 Z bores | 11,099.708 | 0.0000900925; 0.0900925 |
| Inner block, within BG045 Z bores and away from BG003 X-bore center planes | 11,766.458 | 0.0000849873; 0.0849873 |

The coefficients are geometry-only: a hypothetical uniform axial tensile force
`N_z` in newtons divided by the candidate net area gives stress in MPa. They do
not supply an actual `N_z`, wood strength, section bending stress, or a
capacity. The areas use the modeled rectangular section envelopes and
ray-confirmed bore tracks as a simple section screen; they are not a complete
CAD-integrated stress analysis or approved strength ligaments.

BG003 remains one three-member physical stack. Its intermediate `base_side_left`
member has the profiled oblique `g−` terminal at global z = 277 mm
(`|n·g| = 0.766044`), and bolt 1's `e+` ray terminates at the oblique-end/side
corner. Those features are explicitly retained as applicability limits; no
rectangular base-side row or split capacity is inferred from them. The
inner-block section accounts for the two orthogonal Z-axis holes crossing
the same section plane as the BG003 X-bore. The bore voids are disjoint;
the profile rays encounter their separate void intervals.

NDS-2024 Appendix E.2 gives a possible net-tension form `Z′_NT = F′_t A_net`
only where the member action, material, and section meet that method's
applicability. Here no signed member force is available, and no adjusted
member-specific `F′_t` is bound for these current members. The task therefore
stops at area and per-unit stress only. There is no section modulus or bending
interaction result.

Splitting stays pending. The existing source screen identifies first-generation
EN 1995-1-1:2004 §8.1.4, corrected by AC:2006, as limited to softwood and the
Figure 8.1 arrangement. Applicability is not demonstrated for BG001's changed
block connection, BG003's three-member stack with orthogonal bore families and
oblique middle-member end, or BG045's end-grain-axis block/header connection.
No EC5 edition, jurisdiction, National Annex, authenticated complete
clause/figure/factor set, or signed two-sided joint shears are bound. NDS does
not provide a general splitting equation for these new topologies. No splitting
demand, resistance, pass, or failure is reported.

| Still needed before an accepted wood/joint check | Why it blocks this screen from becoming capacity |
|---|---|
| `Fx,Fy,Fz,Mx,My,Mz` interface wrenches at stated datums, with equal/opposite signs: post↔spine (BG001); separate spine, `base_side_left`, and block cuts in the BG003 three-member stack; block↔header (BG045). Transport moments to common datums and include simultaneous neighboring-group actions on shared members. | No member `N_z`, local shear, bending, torsion, or force sharing is established. |
| Actual finished member identity, species/grade (including post-rip status), moisture/service condition, and applicable adjusted `F′_t`/`F′_v` | Current grain/material maps and elastic scenarios are conditional; they do not bind design strengths. |
| Actual hole/cut/section conformance and loaded-end/edge/row classification for each group | Modeled axes and geometry are not installed parts; 3-member BG003 cannot be silently reduced to independent pairs. |
| Applicable splitting method and topology mapping, or supported replacement; method factors and per-side shear demands | The Figure 8.1 condition and complete source set are unresolved; NDS has no general formula here. |
| Washer/plate dimensions, bearing/pull-through, bolt tension and engagement, and complete transfer across both sides of each stack | No axial connector/contact path or full group transfer capacity is covered by `A_net`. |

Reproduce the pinned geometry arithmetic from the repository root:

```sh
python3 docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/current-corner-local-wood-screen-attempt01/produce.py
python3 docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/current-corner-local-wood-screen-attempt01/produce.py --verify
```

The producer uses only the Python standard library, verifies pinned input
hashes, checks the bore-union geometry observations, and recalculates the
table. It performs no CAD query/rebuild, mesh, native solve, or geometry edit.
