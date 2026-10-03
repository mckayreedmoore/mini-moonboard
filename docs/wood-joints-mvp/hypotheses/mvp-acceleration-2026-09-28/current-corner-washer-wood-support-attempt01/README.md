# Current-corner outer washer support in finished CAD

This read-only result checks the wood-facing annulus at the twelve outer
washer seats for BG001, BG003 and BG045. It binds the saved washer-seat
coordinates to the unique trimmed planar support face on each receiver in the
reviewed attempt04 finished-member STEP bundle. It does not assess the
opposite head/nut-to-washer metal footprint.

## Geometry result

The conditional K.L. Jack 25NWUS Type A Wide dimensional envelope is ID
7.7978–8.3058 mm and OD 18.4658–19.0246 mm. Using the area-extreme
combinations gives 213.627873–236.506729 mm² per washer annulus. At each of
the twelve actual modeled outer-seat centers, the STEP receiver has one
coplanar planar face with the outward normal pointed toward its washer. Exact
OCC intersections of that face with both extreme annuli retain 100% of the
annular area; the annulus-minus-face cut area is zero. The face queries retain
the complete trimmed topology, including any holes or cuts in those support
faces, rather than substituting a gross rectangular member envelope.

| Finished receiver face | Seats | Face area (mm²) | Wires / edges | Annulus support |
| --- | --- | ---: | ---: | --- |
| `knee_outer_left_spine`, face 1 | BG001 posts 1/2 and BG003 sides 1/2 head seats | 38,422.395413 | 5 / 8 | Both bounds fully supported |
| `base_post_outer_left`, face 3 | BG001 post 1/2 nut seats | 33,091.998750 | 5 / 8 | Both bounds fully supported |
| `knee_outer_left_inner_frame_block`, face 8 | BG003 side 1/2 nut seats | 18,447.292707 | 3 / 6 | Both bounds fully supported |
| `base_header`, face 2 | BG045 header 1 head and header 2 nut seats | 339,689.386968 | 13 / 16 | Both bounds fully supported |
| `knee_outer_left_inner_frame_block`, face 3 | BG045 header 1 nut and header 2 head seats | 11,766.457707 | 3 / 6 | Both bounds fully supported |

The modeled wood bore radius is 3.75 mm. The minimum catalog washer opening
radius is 3.8989 mm, leaving 0.1489 mm nominal radial clearance when centered
on the source bolt axis. The saved CAD washer centroids are coaxial with their
seat points to within `4.6e-13 mm`. The source washer thickness is 1.651 mm;
its ideal contact plane derived from the centroid and half-thickness
coincides with the wood support plane to within `1e-12 mm`. The maximum
modeled plane tilt is 0 degrees. These are geometric pose comparisons; they
do not establish physical washer or wood flatness, assembly fit, or contact.

The 25NWUS dimensions are applied to all twelve seats as a catalog geometry
scenario. They do not select a product, and the existing register has no
25NWUS washer lead for the two BG003 side bolts. No washer is assumed
delivered or inspected.

## Same-state conditional average pressures

The source axial register contains 21 load-increment states across A12-rear,
A1-rear and K12-rear, with 126 positive signed tie actions on the six bolts.
Each action is evaluated separately at both outer seats for its own bolt and
state. With the annular-area envelope above, the minimum and maximum
`T / A` averages across these 126 ties are 0.004027339–0.558649011 MPa per
seat. The maximum is the 119.343 N BG045 header-1 action in A12-rear at load
factor 1.0; each of its two outer seats has a conditional average of
0.504607207–0.558649011 MPa. Per-axis maxima are:

| Bolt | Source state | Tie (N) | Conditional average per seat (MPa) |
| --- | --- | ---: | ---: |
| BG001 post 1 | A12-rear, 1.0 | 64.96606 | 0.274690112–0.304108537 |
| BG001 post 2 | A1-rear, 1.0 | 47.00119 | 0.198730878–0.220014314 |
| BG003 side 1 | K12-rear, 1.0 | 99.23822 | 0.419599985–0.464537790 |
| BG003 side 2 | K12-rear, 1.0 | 73.62760 | 0.311312918–0.344653527 |
| BG045 header 1 | A12-rear, 1.0 | 119.34300 | 0.504607207–0.558649011 |
| BG045 header 2 | A1-rear, 1.0 | 98.44241 | 0.416235133–0.460812573 |

These values are uniform averages over the conditional annulus only. They are
not local contact-pressure fields, wood bearing resistances, or joint
capacities. The CAD intersection does not verify actual stock condition,
finished flatness, received cuts, washer flatness, eccentric assembly, or
delivered dimensions. The available Type A Wide dimensions are not used to
infer washer steel strength. Head-to-washer and nut-to-washer metal contact
areas remain a separate unresolved geometry and mechanics problem; this
packet does not replace them with the larger wood-side annulus.

## Sources and reproduction

[`source-pins.json`](source-pins.json) records hashes for the reviewed seat
screen, accepted three-case signed axial register, attempt04 finished STEP
manifest and bundle, centroid and reduced member geometry sources, the prior
reviewed finite-face profile query, and the local washer dimensional packet.
The direct STEP hashes are also checked against the manifest, bundle, and
reduced member-geometry map. The two existing producers were source-verified
before this check. The CAD query uses CadQuery 2.8.0 and the same source-bound
STEP loading and trimmed-face approach as the reviewed BG001 profile query.

Rebuild and byte-verify the result from the repository root with:

```sh
uv run --no-sync python docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/current-corner-washer-wood-support-attempt01/produce.py --write
uv run --no-sync python docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/current-corner-washer-wood-support-attempt01/produce.py --verify
```

The output is [`support-screen.json`](support-screen.json), SHA-256
`0fa052decc7f56d34368a09d3e25b15a2d32d97445d14fddb57d97e7487fd304`; the
source pin file SHA-256 is
`b4c01bf277ca36a134f2be0a7fdd54e8e720a473b7ac12f05bc75fabd67363c9`. It contains the
source hashes, twelve seat/face records, both exact annulus intersections per
seat, and all 126 same-state tie values with both seat-average pressure
ranges. The check changed no shared CAD or source data and ran no native solve
or mesh operation. It establishes no mechanical acceptance or physical
inspection.
