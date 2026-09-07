# Nominal connection-distance audit

Source inspection only, 2026-09-07; no new CAD run or capacity acceptance.
`product_frame` preserves `transition_frame` backing/bolt axes. S follows the
board uphill; N is rearward normal. All distances below are mm.

## Critical geometry

| Family | Nominal distances to report | Interpretation |
| --- | --- | --- |
| `transition_top_*_bolt_1`, S2375/N63 | Rim uphill end 63.4; steel S ends 15.5/53.4 | Wood end distance differs from steel margin |
| `transition_top_*_bolt_2`, S2415/N63 | Rim uphill end 23.4; steel S ends 55.5/13.4 | Priority wood-end/combined-load review |
| Both top bolts | Steel free N-edge 13.2; inner return 18.9; bolt spacing 40; rim N-edges 81/103.15 | No loaded/unloaded-edge classification without force direction |
| `analysis_leg_wall_bolt_*` | S1540/1620/1740/1820; rim N-edges 92.075/92.075; spacings 80/120/80; nearest rim uphill end 618.4 | Separate plywood-leg contour/strength-axis distances still required |
| Other steel/wood bolts | Per-member grip; hole-to-free-edge ligament; neighboring holes; local grain direction | Rectangular blank bounds cannot replace notches/curved outlines |

The top steel's minimum 13.2-mm center margin leaves **2.6971 mm** beyond the
selected maximum washer radius 10.5029, and **7.64375 mm** beyond the project
11.1125-mm hole radius. These are steel packaging distances, **not** wood-end,
steel tearout, washer-bearing or bolt resistance approval. The Ø36 withdrawal
corridor has only 0.9 mm to the return; it excludes socket engagement.

For the next layout revision, use **7D = 66.675 mm** as a conservative uphill
wood-end screen while load direction remains unqualified. AWC's
[bolted-connection example](https://web-media.awc.org/wp-content/uploads/2021/12/17210649/StructureMag-NDS2015-PracticalSolutions-1611.pdf)
(Table 2, based on the 2015 NDS) identifies 7D for softwood parallel-grain
tension with the full geometry factor. This is a selected screening case, not
a universal minimum or confirmation of current code applicability. Both current
top-rim bolts fall short of that screen. Relocate the bolts and redesign their
steel leaf as needed, while retaining screws inside the top rail; then rerun
geometry, bearing and service checks. Do not infer an acceptable reduced
capacity from the current shorter distances or the failed FEA recovery.

## Nominal penetration, including point

| Screw family | Receiver penetration | Unnotched backing remaining behind tip |
| --- | ---: | ---: |
| R4 face/kicker, 50.8 through 18.25625 | 32.54375 | 5.55625 |
| R4 splice, 60.325–63.5 through 38.1 | 22.225–25.4 | 15.875–12.7 |
| R4 edge / rib-front, 88.9 through 38.1 | 50.8 | Measure actual receiver along axis |
| SDS custom steel, 38.1 through 6 | 32.1 | 6 |
| SD9112 through UK proxy 1.1684 | 36.9316 | Measure each receiver along the screw axis; these screws run in the board plane, not through its 38.1-mm backing depth; US clip thickness unverified |

Penetration is not effective threaded embedment. Intersect threaded-tail
envelopes with actual net receivers, excluding tips, clearance members and
wire/LED reliefs; apply documented product-generation bounds.

Reuse `test_new_bolt_washers_have_full_nominal_bearing_rings` with selected
annuli, `test_every_connection_has_receiving_material_and_open_core`, and
`box_exports.exact_bounds/overlap`. Add per-member local-axis end/edge measurements
and actual net-boundary witnesses, preserving signed distances and unresolved
rule applicability. The [selected screw rules](selected-wood-fasteners.md) and
[bolt stack](selected-bolt-hardware.md) remain authoritative; failed FEA cannot
supply qualified joint demands.
