# Flush floor-beam construction coordinates

**Dimensional packet for `compact-floor-flush-development`. Not a fabrication release.**

This packet is the **kerf-right** presentation: 1/8 in (3.175 mm) removed from the K-side overall width. Official Mini 4×4 sheets are in [floor-flush-construction](../floor-flush-construction/). Six-case evidence remains the official geometry.

Shop instructions are in the [shop checklist](../floor-flush-shop-checklist.md) and
[assembly guide](../floor-flush-assembly-guide.md). Occupied CAD diameters and
`modeled_length_mm` values are analysis envelopes. Use the `shop_*` columns for
finished bolt-hole range, purchased Hillman length and SDS wood-lead-hole rules.

Candidate: `compact-floor-flush-development`. Width option: `kerf-right`. See
[the current package](../floor-flush-build-package.md) for evidence status.

- `stock.csv` gives stock allowances, not finished lengths.
- `stock-profiles.json` records actual trimmed raw timber vertices in world millimetres.
- Eight `*-bolt-sheet.svg` sheets show those actual profiles and relocated bolt axes.
- `bolt-member-datums.csv` and `profile-corner-datums.csv` share a physical corner datum,
  along-grain A and signed cross-grain C. Identify the corner on the sheet before layout.
- Leg taper sheets and `leg-taper-cuts.csv` specify separate inner-face removal.
- `runner-end-geometry.json` records the square front and inclined rear cut endpoints.
- `connection-axes.csv`, `panel-attachment-axes.csv`, `panel-hole-axes.csv` and
  `timber-passages.json` retain the current screw, panel and passage coordinates.
- `bolt-hardware.csv` describes current catalog bolt stacks plus shop hole-range columns.

Use numerical coordinates, not image scale. Left and right use their own physical
minimum-X datum: do not mirror a datum convention blindly. Kickers remain whole.
All timber profiles assume fresh stock; previous holes are not repair instructions.
