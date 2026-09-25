# Hypothetical denser hold layout: midpoint clearance

The current model was screened at horizontal and vertical nearest-neighbor
midpoints between LEDs and between regular hold T-nuts. The grid is the
current stock-adapted grid, including its nonuniform row-boundary exceptions;
this is not a confirmed future MoonBoard layout. The screen follows removal
of the four outer rear/underside supports, at revision
`outer-rear-bridges-under-header-links-removed-v1`.

Open the [interactive maps](http://localhost:8765/wood-joints-midpoint-review.html)
to inspect any point. [report.json](report.json) binds all 491 sites to the
current model scene/report hashes and identifies each obstruction.

| Midpoints | Positions | Timber obstruction | Flange obstruction |
| --- | ---: | ---: | ---: |
| LEDs, horizontal | 120 | 14 | 12 |
| LEDs, vertical | 121 | 21 | 20 |
| Hold T-nuts, horizontal | 120 | 15 | 12 |
| Hold T-nuts, vertical | 121 | 1 | 0 |
| Kicker T-nuts, horizontal | 9 | 0 | 0 |

The principal findings are:

- The right central principal blocks all F–G horizontal midpoints, rows 1–12,
  in both grids. The T-nut flange itself intersects the timber there.
- At LED horizontal midpoints, E1–F1 meets the left central header block
  16.95 mm behind the panel; E2–F2 meets the bottom left center block at 10 mm.
- At T-nut horizontal midpoints, E6–F6, E7–F7 and E12–F12 meet the corresponding
  left inner corner blocks at 20 mm behind the panel.
- LED vertical midpoints at rows 1–2 and 7–8 encounter the bottom and upper
  middle rails at the flange, in columns A–E and G–K. The G6–G7 midpoint also
  meets the right inner middle block at 20 mm behind the panel.
- The T-nut vertical midpoint G1–G2 meets the bottom right center block at 10 mm.

All 121 vertical LED-midpoint sites overlap existing T-nut envelopes, and all
121 vertical T-nut-midpoint sites overlap existing LED envelopes. Many are
exactly existing stations; the boundary exceptions place others nearby. They
cannot be treated as clear new stations with the current hardware retained.
No structural-bolt or panel-screw envelope hit was found at the tested sites.

## Method and bounds

For each hypothetical new hold, the screen uses a full 25.4 mm diameter flange
disk extending 1.86 mm behind the plywood, plus an 11.1125 mm diameter cylinder
extending 50.8 mm rearward along the local panel normal. These reuse the current
model's flange dimensions and provisional rear-projection envelope. The disk
is conservative around its opening and retention holes. A rear-projection-only
hit is dependent on the eventual hold-bolt length; it does not by itself prove
that every possible bolt will clash.

The screen intersects exact CAD solids after bounding-box rejection, against
44 current timber members, current structural/panel hardware, and existing
LEDs/T-nuts. It excludes plywood intentionally: new panel bores are hypothetical.
No diagonal points, extrapolated edge points, future hold bodies, future LED
stations, retention screws, or tool sweeps are included. The kicker has only
one hold row and no LEDs, so it supplies nine horizontal midpoints only.

Two focused grid tests pass, including the row-boundary exceptions. Two block
congruence tests verify arbitrary rotations and distinct mirrored/changed-hole
parts. CAD geometry was not modified by the screen, and no joint evaluation
or native solve was run. No-hit sites are not an approval of a future setting.
