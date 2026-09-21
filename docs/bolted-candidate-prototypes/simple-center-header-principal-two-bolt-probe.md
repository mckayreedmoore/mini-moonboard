# PB-02 header–principal corner block: two bolts per serial face

**Bounded result: none of three rectangular revisions is a complete fit.**
This is a geometry co-design attempt for a bolted solid-wood corner block at
the passing tolerance pose in
`simple-center-tolerance-pose-probe.md`: rear Y −190, block top Z 348,
vertical bolt Y −139, cross bolt Z 312.5, upright Y −135/Z 360, and link
X 133.5 mm. The inherited first header bolt is vertical at X 15.475,
Y −139; the first block–principal bolt is crosswise at Y −95, Z 312.5.
The proposed block remains solid, rectangular, grain along Y, with plain
rips and crosscuts only. All coordinates below are global millimeters.

| Trial | Block X; Y; Z bounds | Second header bolt | Second principal bolt | Combined outcome |
| --- | --- | --- | --- | --- |
| Left and front | −55…50.95; −190…−5; 277…348 | X −19.525, Y −139 | Y −50, Z 312.5 | Rejected |
| Left and rear | −55…50.95; −225…−45; 277…348 | X −19.525, Y −139 | Y −140, Z 312.5 | Rejected |
| Left and tall | −55…50.95; −190…−45; 277…385 | X −19.525, Y −139 | Y −95, Z 352.5 | Rejected |

The two axes on each face are spaced 35 mm at the header and 45 mm at the
principal, exceeding the conditional 4D = 25.4 mm pitch marker for the
illustrative 6.35 mm bolt. The widened X face seeks a full transverse
reserve for the second vertical axis. The front/rear Y extensions seek a
second grain-separated principal axis; the taller trial seeks Z separation.
The first two axes are retained and their occupied bore spans are adjusted
to the revised block faces. The widened block itself, however, occupies the
left principal: about 38,777–54,326 mm³ across the three trials. It also
puts the original cross-bolt's left washer, end hardware, and socket inside
the left principal. Thus even the second header axes' isolated collision
fits do not form an admissible combined arrangement.

In the front trial, the extended block additionally intersects both lower
main members; the second principal bore intersects the left principal by
169.50817 mm³. The rear trial's second principal bore intersects the first
header bore by 238.42571 mm³ and its right end hardware/socket meets the
upright side cleat. The tall trial's block obstructs the original upright
bolt's left hardware/socket. All three proposed principal bores intersect
the left principal by 169.50817 mm³. These are modeled occupied-volume
collisions, not a claim that every shorter extension or coordinate is
impossible.

The script checks each new full 7.30 mm occupied bore against both intended
woods, the 66 fixed panel/kicker screw envelopes, all eight inherited bores,
unintended wood, and the other new bore. It checks 10 mm radius washer seats,
10 mm radius by 5 mm exposed hardware, and 7.8486 mm radius by 24.511 mm
socket bodies at both ends against wood, screws, and other hardware. Each
new insertion path spans the modeled bolt length plus 25 mm from both ends;
at least one clear end is required. It also rechecks original bolt bores,
washers, hardware, sockets, and insertion against the changed block. The
unchanged pose retains 48 panel and 18 kicker axes, both inner kicker
supports, and the previously screened screw receivers. These are nominal
solid-model envelopes, not selected tooling or installation proof.

Conditional centerline markers use 4D for transverse edges, 7D for grain
ends, and 4D for bolt pitch. The new block's Y boundaries are grain ends,
not transverse edges. The principal is inclined: its oblique grain and end
classification is **unresolved**, so its box-coordinate marker is not a
substitute for a directional end-distance or NDS check. Signed loads,
strength, actual stock quality, washer bearing, tolerance stack, full tool
swing, and assembly sequence remain open. No native solve, drilling
coordinate, fabrication release, or strength verdict follows.

Reproduce with `.venv/bin/python
scripts/simple_center_header_principal_two_bolt_probe.py`; test with
`.venv/bin/python -m pytest -q
tests/test_simple_center_header_principal_two_bolt_probe.py`; lint the two
new Python files with `.venv/bin/ruff check`.
