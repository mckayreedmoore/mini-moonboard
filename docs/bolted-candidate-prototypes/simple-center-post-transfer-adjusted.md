# PB-02 adjusted two-cleat transfer: one bounded geometry attempt

Status: **conditional loaded-edge failure; no connection or drilling approval**.
This is one adjusted pose based on
[the original two-cleat trial](simple-center-post-transfer.md). Only the right
center box post moves, by +37.8 mm in X to 88.75…126.85 mm. The left post,
upright, header, panels, 4×6 backer, and all 48 panel plus 18 kicker screw
axes stay fixed. The backer still supports both inner kicker edges. No
half-lap, custom steel, or replacement panel fastener is introduced.

## Single adjustment

Try nominal 1/4 in (6.35 mm) ordinary through bolts in 7.30 mm diagnostic
bores. That bore is within the 7.14375…7.9375 mm interval from the
1/32…1/16 in oversize rule described in the
[2024 NDS geometry basis](simple-rail-nds-geometry-basis.md); it is not a
selected drill size. Widen both plain rectangular cleats in X from 38.1 to
50.8 mm, leaving their inward X face at 89.05 mm. Extend the side cleat's
front Y face by 6.0 mm, from −124.9 to −118.9 mm, without entering the
bottom rail. Center the link in the wider X section and center the upright
bolt in the side cleat's deeper Y section. Move the upright bolt up 5.5 mm;
retain the link Z=370 mm so its front tool path clears the modeled rail.
This is one combined pose/cleat-shape alternative, not a parameter sweep.

| Item | Nominal bounds or center, mm |
| --- | --- |
| Rear cleat | X=89.05…139.85, Y=−213.8…−175.7, Z=0…460 |
| Upright-side cleat | X=89.05…139.85, Y=−175.7…−118.9, Z=277…460 |
| Post low/high bores | X=107.8, Y=−213.8…−46, Z=110/190 |
| Upright bore | X=50.95…139.85, Y=−147.3, Z=350 |
| Cleat-link bore | X=114.45, Y=−213.8…−118.9, Z=370 |

The original serial path remains post → rear cleat → side cleat → original
upright. Measured CAD intersections show no positive-volume unintended wood
overlap, no bore intersection with unintended timber or another bore, and
full bore volume in the named receiving pair. Neither cleat, any bore, nor
either post-front seat intersects the full purchased-length envelopes of the
66 fixed panel/kicker screws. This does not prove bolt strength or installed
fit.

## Actual margins and conditional NDS classification

Distances are from nominal bore **centers** to modeled timber boundaries;
they do not include stock, drilling, or assembly tolerances. The grain of
both cleats and the post is vertical. For a 1/4 in bolt, the illustrative
reversible perpendicular-to-grain loaded-edge screen is 4D=25.4 mm; the
unloaded-edge value is 1.5D=9.525 mm. A softwood loaded end under parallel
tension has a 7D=44.45 mm full-value tier; a shorter end may require the
applicable reduced-value or minimum tier. Classification depends on signed
member forces and cannot be assigned from geometry alone.

| Member/group | Actual center distances, mm | Conditional finding |
| --- | --- | --- |
| Post bolts, X edges | 19.05 / 19.05 | Either edge could be loaded on force reversal: **6.35 mm short of 4D**. Fixed 38.1 mm post permits at most 19.05 mm on both sides. |
| Rear cleat at post bolts, X edges | 18.75 / 32.05 | Inward edge is **6.65 mm short of 4D** if loaded in that direction. Widening only the outward edge does not repair this row. |
| Post low/high, Z ends | 110 / 128.9 and 190 / 48.9 | Upper bolt has 4.45 mm nominal reserve to the 7D tier at its top end if loaded in parallel tension toward that end. |
| Cleat link, both cleats' X edges | 25.4 / 25.4 | Exactly 4D on nominal square sides, with **zero tolerance reserve** if either is a loaded edge. Baseline near edge was 16.65 mm. |
| Cleat link, rear/side Z ends | 370 / 90 and 93 / 90 | Both nominal end distances exceed 7D if that full-value tier applies. |
| Upright bolt, side-cleat Y edges | 28.4 / 28.4 | 3.0 mm nominal reserve to 4D if either Y edge is loaded. Baseline was 27.2 / 23.6 mm. |
| Upright bolt, side-cleat Z ends | 73 / 110 | Lower end gains 5.5 mm versus the original pose and exceeds 7D nominally. |

The **original upright's inclined geometry** still needs its own NDS edge
and oblique-end classification. The side-cleat Z distances cannot stand in
for the upright's actual end distance. Force directions, bearing-length
ratio, spacing/group action, and the applicability of the 1/4 in bolt
provisions also remain unverified. Even if every other condition passed,
the fixed-width post prevents a reversible 4D loaded-X-edge finding for
this ordinary through-bolt pose. Merely reducing the bolt from 3/8 to
1/4 in improves the numerical shortfall but cannot produce a pass.

## Hardware accounting and access

The shifted post still intersects the historical
`clip_split_header_center_right` steel by 21,944.06 mm³. The wider side
cleat intersects `clip_split_base_center_right` by 13,986.25 mm³. Ten old
clip screw/wood collisions remain. **Both named clip stations and their
fasteners must be removed/replaced** for this candidate; their header,
base, and upright duties have not been re-proven. A wood-only clearance
result does not retain them silently.

Diagnostic 20 mm diameter washer disks have complete nominal wood bearing
at all eight exposed/seat faces, including the actual inclined upright
left face at Z=350. The post-front pockets remain 25 mm diameter by 10 mm
deep and end flush with the kicker back plane. Straight 20 mm radius by
20 mm tool cylinders clear modeled wood at six ends. Both post-front tool
approaches intersect the right kicker when it is installed, so seat access
requires the assembly order or kicker removal described in the original
trial. Tool withdrawal, socket swing, delivered washer and head dimensions,
cut-washer compliance, shank/thread placement, nut engagement, and real
bolt lengths are not established. Full disk bearing is a geometric screen,
not a washer bearing or pocket net-section capacity.

This bounded attempt is **not viable as a general signed-load detail**.
Reconsidering it would require actual force signs and a qualified geometry
that resolves the post's 19.05 mm loaded-edge limit, plus the displaced
clip duties and complete joint resistance. No structural result is inherited
from the selected candidate.

Reproduce with `.venv/bin/python scripts/simple_center_post_transfer_adjusted.py`
and `.venv/bin/python -m pytest -q
tests/test_simple_center_post_transfer_adjusted.py`.
