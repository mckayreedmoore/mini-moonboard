# Bottom-outer finished sections and source cut actions

The four bottom-left bolts now have a source-bound join between their six
finished bore planes and the complete signed point-action cut resultants in
the existing A1/A12/K12 rear responses. The three saved STEP solids and all
eight receiver memberships are preserved. All 63 whole-body states reproduce
the frozen response/audit residuals and their rounding bounds. This closes a
geometry and demand-bookkeeping gap; section resistance and complete joint
acceptance remain open.

The candidate is `compact-floor-flush-wood-joints-development`, reviewed
revision `led-clearance-2x6-runner-seated-blocks-v1`. Neither the selected
angle-frame candidate nor historical cases supply acceptance for this packet.
No geometry, source response, hardware selection, or native run is changed.

## Geometry and coverage

Each finite bore patch is matched to the actual receiver and saved STEP
identity in the current feature register. Its midpoint on the source bolt
axis sets a plane normal to the unchanged model grain axis. Coincident planes
retain both bolt/feature identities; the grouping tolerance is `1e-6 mm`.
The saved solids are imported once each and queried with the secondary's
hash-pinned [section helper](../upper-outer-finished-sections-2026-10-01/section_geometry.py).

| Saved member | Model grain station, mm | Area, mm² | Planar material regions | Bore memberships |
| --- | ---: | ---: | ---: | --- |
| `base_rail_bottom_left` | 45.450 | 4751.07 | 3 | rail 1 and 2 |
| `base_side_left` | 284.368 | 11752.58 | 2 | side 1 |
| `base_side_left` | 317.368 | 11752.58 | 2 | side 2 |
| `bottom_outer_left_cleat` | 43.350 | 7236.46 | 2 | rail 1 |
| `bottom_outer_left_cleat` | 59.850 | 6569.71 | 3 | side 1 and 2 |
| `bottom_outer_left_cleat` | 76.350 | 7236.46 | 2 | rail 2 |

These are analytical station coordinates and modeled bore voids, not shop
dimensions or bit sizes. The [finished-geometry review](finished-geometry-review.md)
independently checks the rectangle-minus-slot areas and four cleat bore-pair
walls of approximately 9.0 mm. Disconnected planar regions belong to a single
three-dimensional timber solid; neither their existence nor their combined
area proves a common strain field or force sharing.

The three response families each provide seven load factors:
`0.1, 0.2, 0.3, 0.45, 0.675, 0.925, 1.0`. Six planes and two one-sided traces
give 252 cut states. The producer keeps every incident physical connection,
selected or released floor action, exact floor tangent reaction, and original
discrete nodal body/gravity load for each member. Body loads are scaled by
the same source load factor. Numerical grounding forces are absent from this
physical boundary. All original response gates and independent body-audit
gates must pass before a state is emitted.

## Wrench and contact interpretation

The internal wrench on each material half is the negative of that half's
external source-action sum. An action in the `1e-6 mm` station band belongs to
the positive half for the trace approached from negative station, and to the
negative half for the other trace. This preserves the point-force jump at a
bore station. Both material halves, their source identities, and their
rounding radii remain available; the two half-body external sums reproduce
the original whole-body residual.

Global moments are transported to the actual finished-section area centroid
with the corresponding force and then projected onto the same model frame.
`N, Vu, Vv` are signed projections along grain/u/v, and `T, Mu, Mv` are
signed moments about those axes. These labels alone do not assign a tension
capacity or turn an external moment into internal bolt bending. For example,
the A1 full-load positive-half wrench at the side member's 317.368 mm plane,
approached from negative station, retains forces
`(767.4411, −461.4632, −95.8620) N` and moments
`(22650.3212, −177516.2294, 8435.2766) Nmm`. These six components come from
one simultaneous source state; they are not six independently selected peaks.

All six planes lie inside at least one finite source contact-patch station
extent. The source law concentrates each contact-cell action at its original
point. A point-action cut therefore does not partition the real patch's
traction or establish a ligament's load. The crossing patch names remain
explicit in every state. No local stress is obtained by spreading these
resultants over the net area or by assuming area-proportional strip sharing.

## Reproduction

Run from the repository root with the locked project environment installed:

```sh
.venv/bin/pytest -q docs/wood-joints-mvp/hypotheses/bottom-outer-finished-sections-2026-10-01
.venv/bin/ruff check --no-cache docs/wood-joints-mvp/hypotheses/bottom-outer-finished-sections-2026-10-01
.venv/bin/python docs/wood-joints-mvp/hypotheses/bottom-outer-finished-sections-2026-10-01/produce.py \
  > /tmp/mini-moonboard-bottom-outer-finished-sections-2026-10-01.json
.venv/bin/python docs/wood-joints-mvp/hypotheses/bottom-outer-finished-sections-2026-10-01/parent_verify.py \
  --report /tmp/mini-moonboard-bottom-outer-finished-sections-2026-10-01.json
```

The synthetic tests do not need private raw response or STEP evidence. They
exercise six-plane/eight-membership identity coverage, altered source bytes,
wrong or ambiguous receiver/bore geometry, nonfinite or nonunit inputs,
finite-footprint interpretation, an equilibrated point-force jump and
centroid transport, and a rectangle-minus-transverse-slot area oracle.
The temporary-source integration fixture also executes the complete producer,
checks every case/increment/member/plane/trace identity and negative acceptance
flag, requires repeatable output, and rejects changed STEP bytes, invalid
model frames and failed source gates.
Full extraction and independent source replay use the locally retained frozen
inputs. Raw output stays local; missing raw data in a public checkout does not
create an engineering, inspection, or fabrication prerequisite.

The [resistance disposition](resistance-disposition.md) routes the unresolved
bolt/material, finished-section, contact and combined-joint requirements.
The [method review](method-review.md) keeps the narrow NDS net-tension method
separate from oblique wrenches, splitting, regional load sharing and bending.
Final verification identities and review receipts are recorded in
[validation.md](validation.md). No formal criterion or joint pass follows
from `PASS_FROZEN_GEOMETRY_AND_POINT_ACTION_DEMAND_JOIN_ONLY`.
