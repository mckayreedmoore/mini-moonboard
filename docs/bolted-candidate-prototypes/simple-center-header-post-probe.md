# PB-02 header-to-right-post rear-cleat bolt trial

Status: **rejected nominal geometry** for the single bounded pose below. No
header-to-shifted-post replacement is selected. This addresses only the duty
of displaced `clip_split_header_center_right` after the
[link-edge pose](simple-center-link-edge-probe.md). It does not close the
separate header-to-principal duty of `clip_split_base_center_right`.

## One full-section face-overlap pose

The shifted solid 4×4 right post remains X=88.75…177.65,
Y=−175.7…−86.8, Z=0…238.9 mm. The header is Z=238.9…277 mm and
Y=−175.7…−36 mm. The existing single solid rectangular rear cleat is
X=89.05…177.95, Y=−213.8…−175.7, Z=0…460 mm. Its front face contacts
the post below the joint and the header above it. The prior two post bolts
at X=140, Z=110/190 mm tie that cleat to the post. This trial adds **one
illustrative header through-bolt** at X=140, Z=257.95 mm, along Y=−213.8…−36
mm. Thus the modeled route is header → metal-nut through-bolt → continuous
rear cleat → existing post through-bolts → shifted post. Contact alone is
not counted as a bolted connection.

The 7.30 mm illustrative bore for a nominal 6.35 mm bolt is fully within its
intended timber length:
38.1 mm rear cleat plus 139.7 mm header, with received fractions
0.21428571 and 0.78571429 (total 1.0). It has no positive-volume collision
with unintended wood, any of the 66 fixed panel/kicker screw axes, or the
prior post, link, and upright bores. The right and left inner kicker edges
remain supported in the preceding pose. Both illustrative 20 mm diameter
washer bearing disks are fully received, and the rear 20 mm radius × 20 mm
tool cylinder clears modeled wood. The two old center-right clips and their
structural screws remain removed at their displaced stations.

## Why this pose fails

The header front bolt end is at Y=−36 mm, directly against the installed
right kicker back face. A 10 mm radius × 5 mm outward hardware envelope
overlaps that kicker; a 20 mm radius × 20 mm straight front tool envelope
also intersects the kicker and a small portion of the right lower panel.
The metal-nut interface cannot remain installed there with this fixed panel
layout. Fitting the bolt before the kicker does not solve the finished-state
hardware collision or provide access to both ends for detachment. The rear
end is clear. This is a geometry rejection, independent of strength.

The trial axis is centered in the header's 38.1 mm Z depth, leaving only
19.05 mm to either Z edge. That is **6.35 mm short** of the conditional
loaded-edge 4D=25.4 mm centerline distance for a nominal 6.35 mm bolt.
For perpendicular-to-grain loading, [AWC's NDS table 12.5.1C](https://awc.org/resources/2024-nds/)
uses 4D at the loaded edge and 1.5D=9.525 mm at the unloaded edge, as
identified by the owner. If the new signed actions require reversible ±Z
loading, both Z edges would need 4D: **50.8 mm total**, impossible in this
38.1 mm header without a changed member/detail. One known loaded direction
would need 4D+1.5D=34.925 mm and could allow an offset axis by edge-distance
arithmetic alone; the signed demand and other joint checks are absent, so
that is not a pass. The edge classification is conditional, and this trial
does not adopt old proxy forces as new bolt demands.

No second pose is advanced. A rear-face full-section path already gives the
cleanest continuous timber route in this local geometry, but its header
through-bolt requires the blocked front face. The existing rear and side
cleats, shifted post, header, kicker, and fixed fastener axes are retained.
No half-lap, custom steel, pocket, panel change, or wood-threaded structural
fastener is introduced. Actual wood, nut/washer dimensions, tool swing,
clearances, bolt shank and thread, assembly tolerances, and joint mechanics
remain unverified. No load rating, drilling coordinates, or fabrication
release follows; old clip proxy forces do not qualify this route.

Reproduce with `.venv/bin/python scripts/simple_center_header_post_probe.py`,
`.venv/bin/python -m pytest -q tests/test_simple_center_header_post_probe.py`,
and `.venv/bin/ruff check scripts/simple_center_header_post_probe.py
tests/test_simple_center_header_post_probe.py`.
