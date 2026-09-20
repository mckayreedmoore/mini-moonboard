# B66 660-mm right-rib bore repair screen

Checked 2026-09-20. This is a **nominal geometry screen for one bottom-right
rail station**, not a connected architecture, capacity, purchase or drilling
release. Reproduce the record with
`uv run python -m scripts.hardware_first_b66_660_rib_repair`.

The prior [B66 trial](hardware_first_b66_660_component_route.md) put the
first upright bolt centerline through 88.9 mm of right rib, but 1,869.507 mm³
of its full 9.525-mm-diameter bore lay outside the sloped rear edge. A
centerline-only check was therefore misleading. The factory-hole offsets,
nominal bolt diameter and 3-in. minimum member thickness remain as recorded
in that trial and its [MiTek ESR-3455](https://www.mitek-us.com/wp-content/uploads/files/pdf/Code%20Evaluation%20Reports/esrESR-3455.pdf).

Two specific, bounded corrections were tested without moving any panel,
kicker, or protected screw:

| Trial | Change | Four full bores | Nominal rail seat | Parent / protected clashes |
| --- | --- | --- | --- | --- |
| Shift bracket forward | Joint Y −60 to −54 mm; no wood change | In receiving wood | Full ideal footprint | None modeled |
| One-piece rib profile | Extend right rib's rear profile 6 mm; bracket stays at −60 mm | In receiving wood | Full ideal footprint | None modeled |

Each trial retains all 66 screw receivers and the ESR's 76.2-mm minimum
wood thickness at all four bores. The ideal rail-seat footprint is 100%
supported, and the reconstructed parent wood, eight header brackets, and
ideal bolt/washer/tool envelopes have no reported overlap. The rib extension
is modeled as a *single continuous timber profile*, not a glued or bolted-on
piece; the extra profile has no modeled parent or header-hardware overlap.
The forward bracket shift is the smaller geometry change and the preferred
next local fit lead. Neither trial checks real bend radii, delivered hole
tolerances, bolt shanks/threads, washer seating, wrench sweep, stock blank,
grain/edge/end distances, fabrication, or service access.

The twelve historical frame-bolt axes are recorded only as an occupancy
diagnostic against the changed right rib and rail; none overlaps them in
this simplified screen, but **none is approved or carried forward**. Five
other rail ends, complete joint action and load sharing, 2024 NDS wood/bolt
checks, formed-angle resistance, and an applicable normal-duration B66
rating remain open. MiTek's published B66 F1/F2 values are at `C_D=1.6` and
may not be converted into this design's ordinary-duration rating. No member
may be cut or drilled from this record.
