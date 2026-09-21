# PB-02 right header-to-principal: bounded bolt screen

**Result: rejected nominal geometry, no selected replacement.** This checks
only the missing `clip_split_base_center_right` header-to-right-principal duty
on the current [link-edge pose](simple-center-link-edge-probe.md). The
[displaced-clip inventory](simple-center-displaced-clip-duties.md) identifies
the historical station at (89.05, −124.9, 277) mm. Its old clip forces are
old-topology proxies, not demand for this proposed connection.

## One full-section overlap trial

The original header remains X=−1219.2…1219.2, Y=−175.7…−36,
Z=238.9…277 mm. The right principal foot remains X=50.95…89.05 mm,
meeting the header at Z=277. No timber is added or cut; the link-edge
pose's moved post, backer, rear cleat and ripped side cleat stay fixed.
One illustrative 6.35-mm removable bolt with a 7.30-mm occupied bore
is vertical at X=65, Y=−160 mm through the header and principal foot.
The nominal principal top at this center is Z=353.10858 mm. The bore
envelope extends to the high side of the inclined exit, so it is not
fully wood-filled over its length.
The 10-mm-radius flat washer and 20-mm-radius × 20-mm straight tool
envelopes are geometric screens, not selected hardware.

The inherited screen retains 48 panel and 18 kicker screw axes, both
inner kicker supports, four full center-kicker screw receivers, zero
new-wood overlaps and zero existing-bore, fixed-screw, or unintended-wood
hits. The candidate bore intersects both intended timbers and none of
the 66 protected screw axes, other timber, or four existing center bores.
The 38.1-mm header bore segment is 100% received by header wood. The
principal segment from Z=277 to the high-side exit is 94.593680% received
by principal wood; the remaining 5.406320% is the empty wedge above the
inclined face. It is not a fully wood-filled principal bore envelope.
These clearances do not overcome the following exact rejection:

| Item | Nominal result |
| --- | ---: |
| Principal exposed face slope, absolute ΔZ/ΔY | 1.19175354 |
| Height change across a 20-mm flat washer | 23.83507 mm |
| Top straight-tool/principal intersection | 5,902.60414 mm³ |
| Bottom straight-tool/neighbor wood intersection | 0 mm³ |

The principal's top face is inclined relative to this vertical bolt.
An ordinary flat washer cannot bear fully on that face, and the straight
tool envelope from the center exit cuts principal wood. Bevel seating,
angled hardware, pocketing, moving neighboring parts, or a panel change would
be separate concepts outside this trial. This is a rejection of the
**tested pose**, not a proof that every possible rectangular cleat or
full-section connection is impossible.

## Conditional Y-axis header-bolt limit

No Y-axis header bolt is proposed here. For a future 1/4-in Y-axis
bolt loaded perpendicular to header grain, the user-identified
[2024 NDS Table 12.5.1C](https://awc.org/wp-content/uploads/2026/08/AWC_NDS2024_withCommentary_20250328_WebsiteChapter-12-%E2%80%93-Dowel-type-fasteners.pdf)
requires 4D=25.4 mm to the loaded Z edge and 1.5D=9.525 mm to the
unloaded edge. If either Z edge can become loaded, the 38.1-mm header
would need 50.8 mm to give 4D on both sides. Its centered distance is
19.05 mm per side, short by 6.35 mm per potentially loaded edge.
This conditional limit does not classify the as-yet-unknown signed new
demand.

No strength rating, load-path qualification, tolerance budget, hardware
selection, fabrication coordinate, or drilling release follows. Run
`.venv/bin/python scripts/simple_center_header_principal_probe.py`,
`.venv/bin/python -m pytest -q tests/test_simple_center_header_principal_probe.py`,
and `.venv/bin/ruff check scripts/simple_center_header_principal_probe.py
tests/test_simple_center_header_principal_probe.py` to reproduce the screen.
