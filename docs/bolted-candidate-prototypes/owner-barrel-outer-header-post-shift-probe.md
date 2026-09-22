# Outer-header barrel: inward outer-post shift

The [bounded probe][probe] moves only each hidden outer post inward in X in
memory. It screens six shifts per side (0, 20, 40, 60, 80, 90 mm) against the
exact kerf-right wood, the 20 mm diameter × 40 mm straight top-access
envelope, protected holds/electrical, fixed screw/bolt axes, and neighboring
barrel-trial hardware and paths. It does **not** edit the assembly producer,
viewer, panel, side rim, header, any of the 66 panel/kicker screws, or any of
the 12 original frame-bolt axes. All dimensions are nominal CAD evidence,
not a drilling plan.

## Result

**No post-shift-only pose is viable with the fixed axes.** Both sides have
the same decisive X thresholds:

| Necessary condition | Inward shift |
| --- | ---: |
| Two original kicker-screw centerlines still enter their named outer-post receiver | less than 19.05 mm |
| Two original rail-front bolt centerlines still enter the outer post | less than 40.132 mm |
| Centered 20 mm top tool clears the side rim | at least 79.85 mm |
| Any post/rim X-projection overlap remains | less than 88.9 mm |

The two fixed `round_kicker_{side}_rim_*` screws explicitly name
`base_post_outer_{side}` as their receiver; their axes are at the original
post midpoint. At 20 mm shift their X centerlines already miss the post by
0.95 mm, even though finite-diameter screw cylinders still graze it. A
graze is not retained screw embedment. The two fixed `rail_front_bolt_*`
axes have only 0.132 mm of post-centerline overlap at 40 mm shift and none
by 60 mm. Thus the 79.85 mm tool-clearance threshold cannot coexist with
either original receiver path in this topology.

| Shift per side (mm) | Tool/rim hit per row (mm³) | Post/rim X projection (mm) | Original front-bolt centerline in post (mm) | Original kicker-screw centerline in post (mm) |
| ---: | ---: | ---: | ---: | ---: |
| 0 | 12566.370614 | 38.1 | 38.1 | 32.54375 |
| 20 | 12566.370614 | 38.1 | 20.132 | 0 |
| 40 | 12566.370614 | 38.1 | 0.132 | 0 |
| 60 | 12552.545427 | 28.9 | 0 | 0 |
| 80 | 0 | 8.9 | 0 | 0 |
| 90 | 0 | 0 | 0 | 0 |

The centered candidate's bolt-shaft/rim hit is 52.285878 mm³ per row
through 60 mm, then zero at 80 and 90 mm. At 80 mm the 20 × 40 mm tool and
shaft clear the rim, but only 8.9 mm of the original 38.1 mm post width
still projects under the rim in X. This is **not** a checked bearing area or
a proven support path: the header is between the post and inclined rim.
The post/header horizontal butt footprint remains 5322.57 mm² in all six
shifts because the header spans the moved post, but that alone does not
qualify the post/header/rim load path.

Additional finite conflicts reinforce the negative result. At 80 mm each
shifted post intersects its adjacent fixed kicker T-nut by 804.105091 mm³
and the modeled hold-hole/rear-projection envelope by 4926.938504 mm³.
The left conflict is `hold_tnut_kicker_1`; the right is
`hold_tnut_kicker_10`. Those hold projections are provisional, but the
modeled T-nut solids are part of the protected layout. At the 0 mm
baseline, each post instead intersects its two *intended* kicker-screw
receiver axes by 438.127102 mm³ each, and the neighboring outer-base
bolt-access paths by 1568.970402 mm³ each. At 20–40 mm shifts the moved
post intersects the neighboring outer-base candidate shafts and access
paths. The probe retains the full per-pose finite hit maps, including
protected electrical, unrelated timber, and other barrel paths.

This is a bounded negative result for **moving only the posts with all
existing axes fixed**, not a proof against every barrel-nut topology. A
different post/header arrangement would need an independently checked
receiver for the four fixed kicker screws, a viable connection on the two
original rail-front bolt axes per side (or an explicitly rechecked change),
rim/header support, protected-hold clearance, neighboring barrel paths,
delivered hardware/tool access, and complete structural analysis. No pose
is adopted in the viewer. **No drilling, fabrication, or structural
release.**

[probe]: ../../scripts/owner_barrel_outer_header_post_shift_probe.py
