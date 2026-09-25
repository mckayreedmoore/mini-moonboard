# Current hypothetical midpoint clearance screen — attempt 03

This read-only BRep screen evaluates 491 hypothetical nearest-neighbor sites on
`led-clearance-2x6-runner-seated-blocks-v1`. It used the already-live
`g24_outer_2x6` geometry and the current geometry snapshot; it did not rebuild
or change CAD. The attempt completed in 7.27 seconds. The detailed rows are in
[`report.json`](report.json), and the frozen execution record is
[`execution.json`](execution.json).

The report SHA-256 is
`a7f7b15200421ad2f6527cf2248f70e7f424164a357a2e69afdf48ad538582e4`; the
producer SHA-256 is
`6915e1213cf425b1f459594c55c403679f3fab18915cb6d976aa2cae0adae806`. It is
bound to `geometry-snapshot.json` SHA-256
`0b92357af648604ee8ce42d2f8906e0a4e5498e9e4b835a07938b81dc151d187` and the
current revision report SHA-256
`148f97623573558cd6a6c53f8a5399f2b30549d6aa1ed13c326dfe1bc3e9d695`.
Attempts 01 and 02 remain preserved. Attempt 01 stopped before intersections;
attempt 02's geometry findings match this run, while its output-directory
metadata named the wrong attempt folder. Attempt 03 records the correct path.

## Screen definition

The site counts are 120 horizontal and 121 vertical LED midpoints, 120
horizontal and 121 vertical T-nut midpoints, and 9 horizontal kicker T-nut
midpoints. The current G2 LED datum is `(1405.0, 199.2) mm`, a +5 mm X move;
its four neighboring LED midpoint centers were recomputed. Sites remain the
historical nearest-neighbor grid, with no diagonal or extrapolated edge sites.

Each site was checked with a provisional 25.4 mm diameter, 1.86 mm thick full
disk flange and an 11.1125 mm diameter, 50.8 mm long rear projection. The 904
tested obstacle shapes comprise 44 timber solids, 460 components on 92
candidate bolt stacks, 60 physical components on 12 retained frame-bolt
stacks, 66 panel screw-axis solids, 142 existing T-nuts, and 132 existing LED
bodies. The report omits 12 source-axis display proxies, 36 retained-bolt
tool/withdrawal envelopes, and 142 hold-hole/rear-projection envelopes. The
131 modeled wire spans and all six plywood-panel bodies are outside this
midpoint screen; five current panel-replacement bodies are recorded in the
report as out of scope.

## Results

“Timber sites” counts sites with any positive-volume timber intersection at
the report tolerance. “Flange sites” counts the subset with a flange
intersection. Member counts below are sites per member, not separate
intersection counts. All 491 sites have zero modeled structural-hardware
intersections.

| Hypothetical site group | Sites | Timber sites | Flange sites | Existing T-nut/LED overlap sites | Timber members and affected sites |
| --- | ---: | ---: | ---: | ---: | --- |
| LED / horizontal | 120 | 14 | 12 | 0 | `base_principal_center_right` 12; `center_principal_cleat_left` 1; `bottom_center_left_cleat` 1 |
| LED / vertical | 121 | 21 | 20 | 121 T-nuts | `base_rail_bottom_left` 5; `base_rail_service_upper_left` 5; `base_rail_bottom_right` 5; `base_rail_service_upper_right` 5; `wj04_lower_full_stock_cleat` 1 |
| T-nut / horizontal | 120 | 15 | 12 | 0 | `base_principal_center_right` 12; `left_service_inner_lower_cleat` 1; `left_service_inner_upper_cleat` 1; `top_center_left_cleat` 1 |
| T-nut / vertical | 121 | 1 | 0 | 121 LED bodies | `bottom_center_right_cleat` 1 |
| Kicker T-nut / horizontal | 9 | 0 | 0 | 0 | None |

The report's `first_occupied_depth_mm` values are measured from the modeled
rear-projection start plane and apply only to rear-projection/timber
intersections. The horizontal LED sites hit `base_principal_center_right` at
0.0 mm (12 sites), `bottom_center_left_cleat` at 10.0 mm (`LED:E2-F2`), and
`center_principal_cleat_left` at 16.9458 mm (`LED:E1-F1`). The vertical LED
projection-only hit is `wj04_lower_full_stock_cleat` at 20.0 mm
(`LED:G6-G7`); the other 20 vertical LED timber-hit sites intersect flanges
with the four listed rails. Horizontal T-nut sites hit
`base_principal_center_right` at 0.0 mm (12 sites) and the three listed
cleats at 20.0 mm (`T-nut:E6-F6`, `T-nut:E7-F7`, and `T-nut:E12-F12`). The
vertical T-nut hit is `bottom_center_right_cleat` at 10.0 mm
(`T-nut:G1-G2`). There are no kicker timber intersections.

Every vertical LED midpoint intersects an existing T-nut body, and every
vertical T-nut midpoint intersects an existing LED body. These are geometric
overlaps between the provisional probes and the modeled installed bodies.

## Limits

This is a hypothetical grid-clearance screen, not a selected future hold
layout or a product-compatibility result. The probe dimensions are provisional;
the full-disk flange omits holes and supports, and the rear projection does
not establish fit for any future hold, bolt, retainer, or tool. The screen does
not include plywood-panel fit, wiring, service access, future hold bodies,
retention screws, or actual installation methods. A geometric overlap is not
a physical blockage finding, and a no-hit result does not approve a setting.
No joint evaluation or native mechanics run was performed; the report keeps
`candidate_accepted` false.
