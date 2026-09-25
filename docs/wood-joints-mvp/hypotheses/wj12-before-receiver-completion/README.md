# Twelve-duty integration before receiver completion

Status: preserved failed diagnostic, 2026-09-24. No joint, layout, capacity,
machining, or assembly is accepted by this record.

The [composition](composition.json) combines the compact outer family, right
four-duty rails, center posts at X = ±190 mm, and two kicker receiver backers.
It contains twelve former duties, sixteen connector pieces, 56 proposed bolt
stations, and 280 installed bolt components. It removes 72 legacy SDS axes
and retains twelve other angle duties with 72 SDS axes. All 66 fixed screw
axes and twelve original frame-bolt arrangements remain represented. The
frame-bolt inventory distinguishes sixty installed components from twelve
occupied-axis proxies.

All eleven shared source hosts reconstruct with zero reported symmetric-
difference volume. The [combined diagnostic](diagnostic.json), run in
132.23 seconds, reports no candidate-body, installed-component, cross-stack,
or peer-bore intersections above its stated tolerance. Its frame-bolt identity
and changed-host machining checks pass. These are nominal geometric checks,
not complete-joint or structural rechecks.

The fixed-screw receiver check fails for twelve axes on five source members
outside the eleven joint hosts:

| Receiver | Fixed axes affected |
| --- | ---: |
| `base_rail_top` | 4 |
| `base_rail_bottom_left` | 2 |
| `base_rail_bottom_right` | 2 |
| `base_rail_service_lower_left` | 2 |
| `base_rail_service_upper_left` | 2 |

Each affected 63.5 mm screw occupancy intersects 157.513719 mm³ of the
source-finished receiver. These members retain the shorter native modeled
holes and have no candidate purchased-length cutter in this composition.
The four redirected center kicker axes already have their cuts in the two
new backers. All 66 axes encounter raw receiver material; that observation
does not establish required embedment, edge support, or load transfer.

The next correction adds only candidate receiver-envelope machining on those
five members, preserving their source cuts, fixed axes, and the selected
baseline. CAD occupied diameters and lengths remain analysis envelopes, not
Hillman pilot, countersink, or drilling instructions. Recompose and repeat
the affected combined checks before treating this diagnostic gap as closed.

The two `.py.snapshot` files preserve the exact producers used for these
reports. The earlier [right-rail report](right-rail-integration.json) is also
retained before the six-inch minimum-length correction documented in the
[outer-pair archive](../wj06-outer-pair.md). [SHA-256 records](sha256.json)
bind the archived files; the
diagnostic also records its producer hashes and the composition-report hash.
These files are historical evidence, not maintained producers. All release
flags remain false. No native solve or physical inspection was performed.
