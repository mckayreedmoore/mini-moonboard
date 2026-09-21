# PB-02 second bolts at the bounded tolerance pose

This geometry-only screen tests second bolts at four serial interfaces using
bolted solid-wood corner blocks (`cleat` in older machine identifiers). It
uses the passing combined pose from
`scripts/simple_center_tolerance_pose_probe.py` (introduced at `1b41438`):
rear cleat Y −190, top Z 348, vertical bolt Y −139, cross bolt Z 312.5,
upright bolt Y −135/Z 360, link bolt X 133.5 mm. It tests four finite
tangential offsets at each of four new serial PB-02 interfaces. The original
first bolt remains at each interface. No continuous search was made.

| Interface | Second-axis offsets, mm | Exact component bounds, mm | Nominal collision fits |
| --- | --- | --- | --- |
| Post–block | Y −35/+35; Z −45/+45 | X 0; Y [−35, +35]; Z [−45, +45] | Z +45 |
| Block–header | X −35/+35; Y −35/+35 | X [−35, +35]; Y [−35, +35]; Z 0 | Y −35 |
| Header–principal block | X −35/+35; Y −35/+35 | X [−35, +35]; Y [−35, +35]; Z 0 | None |
| Principal block–principal | Y −45/+45; Z −30/+30 | X 0; Y [−45, +45]; Z [−30, +30] | None |

The post–block collision fit is a second X axis from
**(88.75, −150, 205)** to **(266.55, −150, 205) mm**, 45 mm from the first.
Its limiting measured marker is the block's upper grain-Z end: 33.9 mm
centerline distance, **10.55 mm below** the conditional 7D = 44.45 mm
marker. The block–header collision fit is a second Z axis from
**(222.1, −165, 110)** to **(222.1, −165, 277) mm**, 35 mm from the first.
Its limiting measured marker is the block's rear Y edge: 10.7 mm
centerline distance, **14.7 mm below** the conditional 4D = 25.4 mm marker.
The corresponding conditional 4D pitch margins are +19.6 and +9.6 mm.

The remaining 14 offsets fail modeled fit or a measured trial marker. For
example, post–block Z −45 mm intersects the inherited post-low bore by
50.87958 mm³ and leaves an incomplete far washer seat. Header–principal
block X ±35 mm loses complete two-wood bore reception and far washer
bearing; Y +35 mm has full reception and bearing but its near hardware and
socket intersect the backer. Principal block–principal has no nominal
collision fit among Y ±45 and Z ±30 mm. The detailed machine output retains
every offset, collision volume, washer fraction, and marker margin.

Each trial checks both intended woods; all eight original bores; all 66 fixed
panel/kicker screw envelopes (48 + 18); unintended wood; bearing at both
10-mm-radius washer seats; 10-mm-radius by 5-mm end hardware; and
7.8486-mm-radius by 24.511-mm socket bodies. New end bodies are screened
against existing hardware and socket bodies. An outward straight insertion
cylinder from each end spans the modeled bolt length plus an illustrative
25 mm allowance. The unchanged tolerance-pose screen separately confirms
all original bore reception, both inner kicker edge supports, fixed screw
receivers, washers, and socket-body geometry.

The nominal bolt D is 6.35 mm. The 4D transverse edge and pitch, 7D grain
end, and 7D distance comparators are **conditional trial markers**, not a
determination of NDS applicability or an NDS verdict. The principal's
oblique grain and end remain unclassified. Load direction, strength, actual
bolt stack, installation sequence, tool swing, delivered tolerances, and
drilling remain unverified.

Within these **16 named offsets**, no second axis has both modeled
collision fit and all measured conditional markers. This is the exact
bounded result; it does not show that other offsets or joint arrangements
are impossible. No connection rating, fabrication, or drilling release
follows.

Run `.venv/bin/python scripts/simple_center_second_bolt_tolerance_probe.py`.
The focused check is `.venv/bin/python -m pytest -q
tests/test_simple_center_second_bolt_tolerance_probe.py`; lint the two new
Python files with `.venv/bin/ruff check`.
