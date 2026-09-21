# PB-02 bounded center tolerance pose

**A nominal pose reaches the 5 mm conditional reserve target in the tested set.**
It is a development geometry result, not a connection qualification or drilling
release. The script tests five named poses. The reference, grain-Y rear extension
alone, and top/cross-bolt change alone receive arithmetic reserve screens; the
two combined poses receive full solid-model screens. An earlier exploratory
combined pose at upright Z=365 intersected the link bore by 50.87958 mm³, so
the tested combined poses use Z=360. Moving the link X axis from 133.5 to
136.5 mm did not improve the limiting margin.

The independent ideal frictionless circular-bore point screen leaves a free
face-normal twist at each of the four new one-bolt PB-02 serial interfaces.
That screen is not a physical failure verdict, and this tolerance probe makes
no claim that the joint is mechanically approved.

The passing pose keeps the principal cleat at X=−20…50.95 and Y=−190…−45 mm,
with grain along Y, and raises its top from Z=338 to **348 mm**. Its header
bolt moves from Y=−145.3 to **−139 mm** at X=15.475. Its principal cross bolt
moves from Z=307.5 to **312.5 mm** at Y=−95. The inherited upright X bolt moves
from Y=−147.3, Z=350 to **Y=−135, Z=360 mm**. The link bolt remains at
X=133.5, Z=370 mm. All coordinates are global millimeters. The grain-Y rear
extension trial to Y=−196 did not increase the *minimum* margin because the
unchanged header bolt still lies exactly at the 4D+5 marker at the header rear
edge.

| Conditional centerline distance | Passing pose | Excess above marker |
| --- | ---: | ---: |
| Header bolt to rear header Y edge | 36.7 mm | 6.3 mm |
| Vertical bolt to either cleat X edge | 35.475 mm | **5.075 mm** |
| Cross bolt to either cleat Z edge | 35.5 mm | 5.1 mm |
| Vertical bolt to rear cleat grain-Y end | 51 mm | 6.55 mm |
| Cross bolt to front cleat grain-Y end | 50 mm | 5.55 mm |

The markers are 30.4 mm transverse (4 × 6.35 + 5) and 44.45 mm grain-end
(7 × 6.35). They are conditional geometry markers, not a determination of
signed load direction, NDS applicability, strength, splitting, or tolerance
capacity. The 5.075 mm minimum is nominal. The passing geometry leaves the
cleat's lower Z face at 277 mm; no half-lap, pocket, panel screw change, or
custom steel is used.

The complete eight-bore model has full intended wood reception. All 16
illustrative 10-mm-radius washer disks bear fully. There are no bore/bore,
unintended bore/wood, wood/wood, bore/screw, washer/wood, hardware/wood,
hardware/screw, or socket-body collisions in the passing pose. The 66 fixed
panel/kicker axes remain 48 + 18. Ten header screw whole-shaft receiver
fractions remain 0.7125; the four center kicker exposed-shaft fractions remain
1.0. Both inner kicker edges stay supported.

An outward straight insertion cylinder is screened from **both** ends of each
bolt for the modeled wood span plus an illustrative 25 mm protrusion. Every
bolt has at least one clear direction. The post and upright X bolts, principal
cross bolt, two inherited post bolts, and link bolt have only one clear
direction in this assembled-solid screen; the two vertical bolts have two.
Blocked directions are preserved in the machine output. This is a useful
assembly constraint, but an actual purchased bolt, head, nut, washer stack,
clamp path, and order of assembling the separate members have not been checked.

The ordinary [GEARWRENCH 80112 socket](simple-center-combined-small-tool-probe.md)
has listed 0.618-in A/B diameters and 0.965-in overall length. The probe uses
a 7.8486-mm-radius, 24.511-mm-long body cylinder at every exposed end; all
16 clear wood, screws, and other end hardware. It separately screens an
**illustrative** coaxial 7.8486-mm-radius, 100-mm-long cylinder beyond each
socket. That cylinder is blocked at five ends: link front, both inherited post
fronts, principal cleat left, and upright left. The manufacturer dimensions
do not specify a ratchet head, handle swing, extension outside diameter or
length, drive engagement, or hand clearance. Those cannot be claimed from this
screen. Selected hardware and installed access remain open gates.

Run the script with `.venv/bin/python scripts/simple_center_tolerance_pose_probe.py`.
The focused test is `tests/test_simple_center_tolerance_pose_probe.py` under
`.venv/bin/python -m pytest -q`; check the two new Python files with
`.venv/bin/ruff check`. This probe does not authorize cutting, drilling,
fabrication, or a structural rating.
