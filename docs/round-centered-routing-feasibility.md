# Centered LED passage routing feasibility

This is a mathematical route feasibility investigation for the current
`round-structural-development` layout. Its adaptive route is now implemented in the candidate wiring module. This
feasibility calculation alone does not release drilling dimensions, establish structural resistance, or demonstrate
that the physical harness can be fed after panel installation.

## Result

Moving the passage axes from local depth N = 35 mm to N = 69.85 mm is compatible
with the modeled 304.8 mm approximate bulb-to-bulb path budget if the cable ramps
are adapted to the actual timber crossings. Simply changing the existing route
plane while retaining its fixed 20 mm endpoint leads is not compatible: 11 of
131 segments reach 319.770 mm, exceeding the approximate budget by 14.970 mm.

For a 139.7 mm deep member and a 38.1 mm diameter passage, a centered axis leaves
50.8 mm nominal wood between the passage and each depth face. This geometrical
observation is not a structural hole-sizing approval.

## Concrete route construction

The calculation uses the existing 132 LED datums and their existing traversal
order, together with all 32 passage records in
`round-structural-drilling/drilling.json`. All 32 current passages are in nominal
2x6 stock. It retains the provisional 8 mm bulb-base depth, 30 mm lateral offset
on vertical runs, 4 mm cable diameter and 8 mm corner radius.

For each segment, define its forward unit vector from the first bulb base to the
second, and let D be the planar separation. The two interior route vertices
have N = 69.85 mm and, for vertical segments, X displaced by +30 mm from the bulb
column. Place these vertices as follows:

- With timber crossings, place the first vertex 10 mm before the first timber
  entry and the second vertex 10 mm after the last timber exit, measured along
  the segment's forward direction. Reverse entry/exit consistently when the
  strand runs downward or leftward.
- Without timber crossings, place each interior vertex `min(60 mm, D/3)` inward
  from its corresponding endpoint.
- Connect the four vertices with straight lines and replace each interior corner
  with an 8 mm circular fillet tangent to both incident segments.

Every fillet's tangent cutback is less than 10 mm, so each crossing retains a
straight cable axis through the whole wood thickness. All incident straight
lengths exceed the fillet cutbacks, including the sum of both cutbacks on the
middle segment. The construction is therefore a realizable centerline, not an
impossible overlapping-fillet length estimate.

| Segment category | Count | Maximum rounded path (mm) | Maximum unrounded polyline (mm) |
| --- | ---: | ---: | ---: |
| Upper service rail crossing | 10 | 273.704 | 274.430 |
| Lower service rail crossing | 10 | 260.863 | 261.971 |
| Bottom rail crossing | 10 | 255.852 | 258.332 |
| Center principal crossing | 2 | 257.252 | 258.798 |
| No timber crossing | 99 | 281.594 | 282.488 |
| All segments | 131 | 281.594 | 282.488 |

Minimum nominal rounded-path budget remaining is **23.206 mm**. Even the
unrounded polyline upper bound remains **22.312 mm** below 304.8 mm. The upper
service rail crossings, which fail with fixed 20 mm leads, retain 31.096 mm
nominal margin with the crossing-specific construction.

For example, A7 to A8 uses local points `(−1019.2, 1199.2, 8)`,
`(−989.2, 1249.2, 69.85)`, `(−989.2, 1307.3, 69.85)` and
`(−1019.2, 1419.2, 8)` before applying the corner fillets. The timber spans
S = 1259.2–1297.3 mm.

## Limits and follow-through

The quoted 304.8 mm pitch is approximate, not guaranteed free cable length.
The 12.7 mm reported maximum harness diameter leaves 12.7 mm nominal radial
clearance in a straight 38.1 mm bore. Connector length, actual bulb projection,
permitted bend radius, strain relief and feeding maneuvers remain provisional;
this clearance does not establish practical intact-strand feeding. The route
margin is not an allowance verified against the actual supplied harness.

This investigation uses datum and passage geometry rather than new solid-model
collision checks. Before adopting it, update the candidate-specific route
implementation and passage depths together, regenerate the wiring solids and
check them against every member, fastener, T-nut and light body. In particular,
adaptive ramps have different envelopes from the existing short ramps. Then
refresh the drilling and viewer artifacts and rerun the candidate geometry
checks. Feeding the lights after the panels remains the intended sequence,
not a demonstrated physical installation result.

The reproducible investigation script and full 131 route records are available
in this working session at `/tmp/centered_route_feasibility.py` and
`/tmp/centered_route_feasibility.json`; run the script from the repository root
with `PYTHONPATH=. uv run python /tmp/centered_route_feasibility.py`. These
session-temporary files are not a released implementation or durable evidence
archive.
