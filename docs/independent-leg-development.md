# Independent leg plies: inspection CAD

The separately selectable [independent-leg development model](https://mckayreedmoore.github.io/mini-moonboard/?model=independent-leg-development)
adds the mechanical candidate from the [leg connection development plan](leg-connection-development.md)
to the backing-joint redesign. Each leg comprises two distinct continuous
19.05 mm plywood profiles with separate floor faces. Three new stitch bolts
per leg occupy lower-centreline fractions 0.2, 0.5 and 0.8.

The four upper bolts per leg explicitly connect three members: rim, inner
ply and outer ply. Their original nominal hardware geometry is retained;
this is not a symmetric double-shear assumption. Stitch bolts are internal
connectors, with no adhesive, interface-friction or external-bracing credit.

The six stitch bolts use a **generic, provisional 57.15 mm envelope**, not a
selected product. The existing generic 2 mm washers and 9 mm nut yield
6.05 mm nominal projection through the 38.1 mm timber stack. Actual bolt,
thread, washer and nut specifications remain unresolved. The catalogued
63.5 mm lead is not silently substituted. Neither this geometry nor its
clearance checks establish resistance, load sharing or stability; candidate
FEA has not been run. The material and qualification gates in the linked plan
still apply.

This variant also inherits the backing candidate's
[unresolved front-rib/panel screw spacing and product seating](front-rib-fastener-selection.md).
Separate leg plies do not resolve those backing-joint constraints.

Inspect each ply and stitch independently in the viewer. Separate [STEP and
CSV artifacts](../exports/independent-leg-development/) include the three-member
upper connections; [the manifest](../exports/independent-leg-development/manifest.json)
binds their source and artifact hashes. Reproduce with:

```sh
uv run python -m mini_moonboard.joint_exports --variant independent-leg-development
uv run pytest tests/test_independent_leg_frame.py tests/test_joint_exports.py
```

An optional browser regression checks all four ply selections, six stitches,
provisional metadata, selector navigation and the hidden reference-person
selection behavior. With Playwright and Chromium installed separately, serve
`site/` on port 8766, then run `node scripts/check_development_viewer.cjs`
(or pass the path to an existing Playwright module as its first argument).
It writes inspection screenshots under `/tmp/`.

The original plywood, `2x8-foot100`, and backing-joint design choices remain
available. This inspection candidate is not a fastening schedule or build approval.

## Implementation review

Independent geometry/correctness, test-coverage and publication/architecture
reviews reported no remaining substantial implementation findings. The combined
candidate/export and solver-build evidence suite passed 13 tests; the browser
regression loaded all 293 entries and selected all four plies and six stitches.
These checks do not qualify the unresolved products, screw spacing or structural
behaviour. The existing joint variant's generated geometry and viewer assets
remain byte-identical; its manifest records the shared exporter's updated source.
