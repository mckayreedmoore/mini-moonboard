# Outer-base barrel axes: inward clearance trial

The [bounded probe][probe] rebuilds only the two `base_outer_side` duties on
the exact, uncut kerf-right owner assembly. The original side rims, header,
outer posts, center posts at X = ±180 mm, kicker backers, 66 panel/kicker
screws, and 12 frame bolts stay fixed. The production layout and viewer are
unchanged. This is a nominal geometry result, not a fit or drilling plan.

The inherited axes are at each side rim's X midpoint, with rows at Y = −135
and −75 mm. At both sides and both rows, the inherited 20 mm diameter × 40 mm
straight bolt-access cylinder penetrates the outer post by 1,568.970 mm³.
The probe moves only the bolt/thread axes inward in X; the cross-bore still
enters from the original outside rim face. The provisional 5-inch bolt,
16.002 mm barrel, 7.5 mm machine bore, and row Y/Z datums are unchanged.

| Inward shift, each side | 20 mm access gap to post | Result |
| ---: | ---: | --- |
| 0 mm | −3.65 mm | Access and provisional washer hit the post |
| 5 mm | 1.35 mm | Access clears; 25.4 mm washer still hits the post |
| 10 mm | 6.35 mm | Bounded nominal geometry screen clear |
| 15 mm | 11.35 mm | Bounded nominal geometry screen clear |

At 10 and 15 mm, all four trial machine bores, barrel bores, and barrel
bodies have full modeled coverage in their intended header/rim wood, and all
four provisional washer seats have full modeled header-face support. No
positive-volume hit above 1 mm³ was found against the maintained T-nuts,
50.8 mm trial hold projections, lights, wires, 66 screws, 12 frame bolts,
unrelated timber, the other row or side, or the other 22 barrel duties'
installed shafts/barrels and drill/access paths. This is a finite-solid
screen, not a toleranced clearance proof. The 10 mm shift is the smaller
screen-clear lead; it is **not** selected in the viewer or approved for a cut.

The washer is a **provisional 25.4 mm OD envelope**, not a verified Hillman
811070 dimension. The reported online table and same-page Q&A conflict, so
19.05 mm is not assumed to be a controlled retail fit either. The 11 mm ×
4 mm head and 20 mm × 40 mm straight access volume are likewise diagnostic.
Actual purchased head/washer geometry, wrench or bit swing, insertion order,
clearance tolerances, delivered bolt shank/thread length, barrel thread axis,
thread engagement, edge/end/net-section resistance, and all load cases remain
open. The existing outer-header/side-rim conflict elsewhere in the viewer
also remains open. No layout, drilling, fabrication, or structural release.

Reproduce with
`uv run pytest -q tests/test_owner_barrel_outer_base_clearance_probe.py`
or inspect the complete JSON from
`uv run python -m scripts.owner_barrel_outer_base_clearance_probe`.

[probe]: ../../scripts/owner_barrel_outer_base_clearance_probe.py
