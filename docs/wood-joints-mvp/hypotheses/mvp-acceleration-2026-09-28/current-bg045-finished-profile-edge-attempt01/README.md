# BG045 finished-profile edge query, attempt 01

This source-bound CAD query checks whether the finished modeled block and
header profiles change the conditional edge-distance arithmetic for the two
BG045 left-header bolts. It queries only the two receiving timber solids and
the two bolt centerlines. It does not assign the NDS loaded edge or resolve
splitting resistance.

The query binds the three accepted signed-action case exports in
`current-bg045-edge-splitting-applicability-attempt02` to the current finished
member STEP bundle and input manifest. Its [`source-pins.json`](source-pins.json)
pins those packets, the exact header and block STEP solids, and the reviewed
finite-trimmed-face query precedent. At runtime, the producer verifies every
direct source pin and the prior packet's nested input hashes. The STEP geometry
revision is `led-clearance-2x6-runner-seated-blocks-v1`; no geometry was edited.

For each receiving member, the actual shaft-overlap intervals in the input
manifest are header Z=238.9–277.0 mm (38.1 mm) and block Z=277.0–416.0 mm
(139.0 mm). The queried bolt centerlines are at X=−1085.85 mm, with axis 1 at
Y=−62.35 mm and axis 2 at Y=−155.70 mm. Five stations span each interval:
0.01 mm in from both ends and at the quarter, middle, and three-quarter
points. At each of the 20 member/axis/station combinations, the producer casts
four exact rays along ±X and ±Y and retains every positive intersection with
the finite trimmed STEP faces. The own modeled bore wall is recorded at
3.75 mm radius and excluded from the external timber-edge choice.

All 80 rays found an orthogonal planar outer profile face. The same trimmed
face was hit at all five stations for each direction, and its BRep bounds span
the full receiver interval. The exact trimmed-face classifier reports the
projected centerline inside the selected face for all 80 rays. These face
numbers refer to the face ordering in the pinned STEP file, not persistent CAD
identifiers. At the sampled centerline projections, the finished-profile
perpendicular distances equal the former rectangular-envelope distances
exactly (0 mm difference):

| Receiver / axis | −Y | +Y | −X | +X |
| --- | ---: | ---: | ---: | ---: |
| Header / 1 | 113.35 mm (face 38) | 26.35 mm (face 16) | 133.35 mm (face 1) | 2301.875 mm (face 15) |
| Header / 2 | 20.00 mm (face 38) | 119.70 mm (face 16) | 133.35 mm (face 1) | 2301.875 mm (face 15) |
| Inner block / 1 | 113.35 mm (face 2) | 20.00 mm (face 5) | 44.45 mm (face 1) | 44.45 mm (face 8) |
| Inner block / 2 | 20.00 mm (face 2) | 113.35 mm (face 5) | 44.45 mm (face 1) | 44.45 mm (face 8) |

For the specific conditional arithmetic carried in the prior packet, the
finished modeled inner-block axis-2 minus-Y profile remains 20.00 mm at each
of the five tested stations. Compared with the named 4D value for modeled
D=6.35 mm (25.40 mm), the arithmetic remains 5.40 mm short. This says only
that the finished modeled profile did not change that distance. It does not
decide whether minus-Y is the NDS-required loaded edge for the applicable
signed action, whether the 4D comparator applies to this orientation, or
whether a geometric edge check is the controlling splitting check.

The intermediate-hit list in `profile-edge-query.json` retains the own-bore,
neighboring BG045-bore, and other cylindrical cut intersections before each
outer face. Across the five ray stations, the extra cylinder face-hit counts
are: header axis 1, −Y (10 neighboring-bore hits) and +X (10 non-target
parallel-cylinder and 20 transverse-cylinder hits); header axis 2, +Y (10
neighboring-bore hits) and +X (10 non-target parallel-cylinder hits); inner
block axis 1, −Y (10 neighboring-bore hits); inner block axis 2, +Y (10
neighboring-bore hits). These are hit counts, not unique-cut counts; each ray
also has its own bore-wall hit. The JSON gives the location, radius, axis,
face identity, surface bounds, and ordered intersections, including
noncylindrical hits.

This result concerns the pinned BRep model, its modeled 6.35 mm bolt axis, and
its 3.75 mm-radius bore only. It does not establish the as-built stock profile,
cuts or holes, delivered bolt, installed centerline, or grain. Although the
outer-face bounds span each receiver interval, the trimmed-face projection was
tested at five stations only; a continuous minimum over every point of the
span is not proven. No net-section, shear-out, tear-out, splitting, group
resistance, or NDS acceptance is calculated.

Reproduce and verify from the repository root:

```sh
uv run --no-sync python docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/current-bg045-finished-profile-edge-attempt01/query.py --write
uv run --no-sync python docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/current-bg045-finished-profile-edge-attempt01/query.py --verify
```

The JSON result records observed source hashes, all station coordinates,
trimmed-face bounds and hit sequences, per-direction summaries, and numerical
oracles. It records no stock inspection, NDS edge assignment, geometry change,
native solve, or mesh.
