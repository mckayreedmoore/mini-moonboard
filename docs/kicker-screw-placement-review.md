# Current kicker screw placement review

Retain the current placement. The nine screws in each independent kicker have useful receiver geometry, a high header row that resists panel peeling, and no identified shaft, hold-hole or modeled wiring-passage conflict. This review changes no screw axes and does not reopen the owner's accepted panel construction or no-slip floor scope.

## Actual current layout

The review reads `compact_spliced_trimmed.connections()` and its raw wood geometry, plus the matching current construction schedules. Coordinates below are measured from the floor and board center, not from the top of a pad. Each plywood half is 1219.2 mm wide, 277 mm high and 18.25625 mm thick.

| Attachment | World X, mm | World Z, mm | Receiver |
| --- | --- | --- | --- |
| Outer post, two per side | ±1200.15 | 112 and 192 | Center of the post's 38.1 mm face |
| Center post, two per side | ±70 | 112 and 192 | Center of the separate post's 38.1 mm face |
| Header, five per side | ±200, ±400, ±600, ±800, ±1000 | 257.95 | Center of the header's 38.1 mm front edge |

There are 18 kicker screws and 48 main-panel screws, 66 total. All remain SPAX XFT08P-2000 #8 × 2 inch. Each kicker remains independently attached; the center seam is not connected by a screw.

The header extends from Z238.9 to Z277 and the posts from Z0 to Z238.9. The header row therefore has **19.05 mm** above and below every axis. Post axes likewise have **19.05 mm** to either side of their receiver faces. Post-row spacing is **80 mm**; header spacing is **200 mm**, with a 400 mm gap across the independent center seam. The nearest header end is 219.2 mm away.

The upper post row is **46.9 mm below the post end**. This is the tightest placement condition: only **2.45 mm nominal reserve** against the product's 44.45 mm loaded-end reference. Mark from the actual post top, use a drilling/positioning template, and verify at least 44.45 mm remains before driving. Do not round the upper row upward or move it nearer the header. Ordinary actual dimensions control over a printed nominal ordinate.

## Reference comparison and installation

[SPAX TER 2010-02](https://www.drjcertification.org/report/download/1936), revised November 4, 2025, Table 19 gives the #8 flat-head reference distances: 9.525 mm edge, 44.45 mm end when loaded toward the end, and 44.45 mm spacing parallel to grain. Current receiver distances exceed these values. These are receiver-grain checks, not an invented plywood edge-capacity rule.

Table 2 lists a 50.8 mm screw and 31.496 mm thread length, including the tip. With the scheduled plywood and flush seating, gross receiver penetration is **32.54375 mm** and the full nominal thread is embedded. Table 10's one-inch embedded-thread condition is met. This does not transfer the SPF-specific plywood lateral table to other lumber species. Sections 9.5–9.6 do not require lead holes and require flush heads without overdriving. Use the specified T20 drive. The modeled 4.1402 mm occupied shaft is not a pilot-bit instruction.

Both post and header wood extend 139.7 mm behind the panel. Screw tips finish 107.15625 mm short of the receiver rear face; there is no backside breakout. The smallest plywood edge distance is 19.05 mm, leaving 14.986 mm from the modeled 8.128 mm head rim to that edge. Establish a flush head seat on an offcut and avoid crushing the face veneer.

## Service and interference observations

A finite-segment clearance calculation against every other current connection finds **5.76216 mm minimum nominal shaft-surface clearance**, between an upper post kicker screw and a perpendicular ML24Z SDS screw. This is a shaft-envelope check; it does not assign structural spacing capacity between different screw products. Retain the existing stagger and avoid angling the kicker screw toward the SDS axis.

The closest kicker hold-hole axis is **54.52486 mm** from a kicker screw, at the right center post's upper screw. Even projecting the 25.4 mm T-nut flange and 8.128 mm screw head into the same plane leaves **37.76086 mm** between their envelopes. Actual holds may extend farther than their mounting hardware; if a hold obscures a screw head, install or remove that hold in the necessary sequence rather than relocating its screw without its receiver.

The current passage schedule contains no LED bores in the header or these four posts. No modeled passage interrupts a kicker screw's embedment. Loose harness routing still follows the build package; the schedule is not a model of every wire bend.

The bottom row at Z112 sits 15 mm below the top of a 127 mm pad **if a pad reaches the board**. This is an access issue, not a reason to remove those screws. Move the pad for inspection or assembly. With the owner's intended rearward pad placement, this row remains exposed.

## Decision

Keep all nine screws per half, especially the high header row. Moving that row down sacrifices leverage against panel peeling, and deleting it would discard the reason it was introduced. Earlier restricted-equilibrium work explains that design choice but is not a fresh strength qualification for this taller kicker. No count reduction or extra kicker framing is warranted by this placement review. The existing package's accepted panel basis and material/installation conditions remain in force.

Checks here cover current raw receiver envelopes, screw axes, catalog distances, head/hold envelopes and the modeled passage schedule. They do not claim a new assembled force solution, equal screw load sharing, hidden hold geometry or manufactured tolerances.
