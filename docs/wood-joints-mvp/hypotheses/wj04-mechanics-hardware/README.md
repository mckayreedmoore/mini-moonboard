# Conditional representative hardware geometry

The parent exported two explicitly assumed response profiles for the eight
six-inch bolts in the representative WJ16 five-wood patch. Each profile has
32 independent metal solids: eight continuous head/shank bolts, sixteen
annular washers and eight hollow hex nuts. All 64 STEP round trips report zero
measured bidirectional volume difference; the parent independently verified
every file hash in the [bundle](../../../../fea/results/diagnostics/wj04-mechanics-hardware-v1/inventory.json).
Seven focused tests and Ruff pass. This is geometry preparation, not a stable
contact model, structural solve, strength or installation result.

The forty original hardware collision roles remain metadata. Their cylindrical
heads and solid nut envelopes are not reused as physical steel. New underhead
datums derive from fixed wood faces and the chosen washer thickness. Both
profiles use mutually consistent regular hexes, separate washers, a hollow nut
and an explicitly idealized projected root/nut engagement. No wood or washer
tie, preload, friction or silent gap closure is introduced.

One response profile keeps the chosen body diameter through the far wood face;
the other starts the smaller cylindrical root representation at the recorded
127 mm Lb boundary. Neither claims the delivered transition. Lg remains a
gaging marker. The historical NBS basic minor diameters are scenario references,
not manufacturing bounds or catalog part measurements. The parent visually
verified the 1/4-20 row in Table 2, printed page 21 / PDF index 30, in the
[primary NBS publication](https://www.govinfo.gov/content/pkg/GOVPUB-C13-2edad299c8f39c5cc9909c067728f932/pdf/GOVPUB-C13-2edad299c8f39c5cc9909c067728f932.pdf).
The [rendered page](nbs-table2-parent-render.png) is retained; the downloaded PDF
hash is `e31f189b5b24e2ce5832d191e7f4c336d6b789674088b1eb52ea47e990560b34`.

The steel elastic constants are explicit response assumptions. Local fillet,
thread, nut, washer and wood stress resistance remain unsupported. Zero-preload
clearance and frictionless seats can leave free washer/bolt modes; rank,
stabilization reactions and energy need separate evidence before a solve.
Metal-to-wood/cross-stack scene auditing, meshing, contact and response remain
unfinished. G7 LED extraction in the full layout remains open and may change
the final wood geometry. No complete-joint or release claim follows here.
