# WJ-04 paired access screen

This archived materialization is an unaccepted access hypothesis for pairing
the lower and upper right service-rail cleats with their rails. It preserves
the source panel axes and the 12 frame-bolt obligations, and records zero
accepted replacements. The full machine-readable result is in
[`wj04-pair-access.json`](wj04-pair-access.json).

## Reproduction and source pins

Run from the repository root:

```sh
/usr/bin/time -p uv run python -m scripts.wood_joint_wj04_pair_access --materialize > /tmp/wj04-pair-access.json
```

The recorded runtime was about 74 seconds. The archived JSON is copied byte
for byte from that output; its SHA-256 is
`9a81948607ff7dec3c76e5a2d7685212bb75f57ae0f2c5d526badbe4147cafc7`.
The report records hashes for its declared source inputs; this is a partial
transitive closure, not a hash of every dependency. Key pins are inventory
`07af4c3eb642cf3887595fe4415eb65404cdcf74d66c5c7bb182847ef21c2d78`,
WJ-04 config `d1c63e1fa5617999e8af68d683cc0f3074fb84f518b048a087ec5ed276206c0e`,
G7 materializer `94d2b301450c942f1c7a95f89e3e7ee1ed643ce4db43576c78c1bce04f9302b9`,
shared tool helper `91e0a8c4bd1681fe5f10d96d99c8e6b3ef39b8d7a26fb42b4bb77c6f85ae2fc8`,
and producer `a2eb40c664ea134ecc23cd09589577de05f63ea4fb9555b74b17020d5af7c953`.

The focused test command is
`uv run pytest -q tests/test_wood_joint_wj04_pair_access.py` (7 passed at
freeze). The producer's default mode emits a source-bound plan; only
`--materialize` runs the geometry screen.

## Staging assumptions and results

The modeled panel-off state removes the right upper and lower panels, their 60
attached T-nuts, their matching provisional hold-projection envelopes, and 24
panel-fastener envelopes for detachment. The report's 144 removed
panel-owned/protected entries comprise those 60 T-nuts, 60 matching
projection envelopes, and 24 fastener envelopes. It keeps 132 lights and 131
wires fixed. Panel extraction and screw-removal paths are not verified. The
final-fit map restores the panels and their attached hardware/projections;
the 66 panel/kicker screw axes remain obligations throughout.

The two far-end duties, `clip_horizontal_lower_right_2` and
`clip_horizontal_upper_right_2`, remain unresolved, with six legacy SDS axes
each. Their connector and SDS envelopes stay in the obstacle map, and
`base_side_right` is not released. The proposed off-frame rail-to-cleat stack
does not install the principal X-bolts off frame and has no modeled external
environment, temporary support, or stability evidence.

Each rail/cleat pair was screened for one-axis movement in both +N and -N
directions. All four screens report conservative swept-AABB hits: lower pair
1444.439473 mm (+N, 34 obstacle IDs) and 1693.348151 mm (-N, 34); upper pair
1425.191643 mm (+N, 43) and 1695.031387 mm (-N, 43). Hits include retained
far-end connector/SDS geometry, neighboring hardware and wood, and fixed
lights/wires. These AABB hits may be false positives; they do not establish a
physical collision or prove a movement route impossible. No alternate route
was searched.

The principal-bolt screen uses a FACOM 34 7/16 open-end external-envelope
proxy (22 mm head/handle width, 3 mm thickness, 100 mm overall), with two
synthetic headings per each of four X-bolt stacks. Nut-versus-counterhold
proxy envelopes are clear in 8/8 cases. Head-side counterhold is clear in 4/8;
the other cases hit adjacent service-rail or principal-head envelopes. The
30-degree nut-turn diagnostic is clear in 4/8 cases. The 60-degree one-flat
reindex/reseat sequence reports neighboring principal nut/shaft hits in all
8 cases. These envelope screens do not establish exact wrench fit, repeatable
nut removal, human access, or physical impossibility.

## Claim boundary

This report is not an accepted assembly procedure or stable temporary-frame
claim. It establishes no delivered hardware fit, thread engagement, load path,
wood capacity, or structural acceptance. It is a bounded diagnostic of the
listed candidate staging state and proxy geometry only.
