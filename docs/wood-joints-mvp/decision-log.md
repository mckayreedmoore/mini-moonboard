# Wood-joint MVP decision log

## 2026-09-23 — Establish separate wood-joint MVP lane

The owner supplied the wood-and-through-bolt MVP handoff reviewed against
commit `df7f5eca86ae831b35a8bcf9e6dcd7ae8af852bb`. Current HEAD is that same
commit. The working tree also records the owner's newer solid-wood-block
direction in existing bolted-candidate documents. That remains an active
parallel development lane. This handoff's stricter identity and fixed-axis
contract are implemented in a separate lane rather than rewriting that work.

Create `compact-floor-flush-wood-joints-development` as a separate candidate.
`current-candidate.json` continues to select `compact-floor-flush-development`.
`barrel-nut-candidate.json` and its superseded barrel evidence remain preserved
history within the parallel bolted lane. The new lane inherits no geometry
acceptance, case pass, connection capacity, drilling instruction, or release
from either lane.

For this lane, freeze all 66 kerf-right panel/kicker screw axes and the purchased
panel-screw policy. This is stricter than a prior bolted-candidate allowance to
move axes. Preserve the physical climbing surface, panel outlines, hold grid,
kicker geometry, and service function. Hidden-frame changes remain possible
only with exact receiver, edge-support, connection, and full-frame evidence.

Interpret the ordinary 139.7 mm local-N limit from an explicit station datum.
Record the connector body, full installed hardware projection, and tool
envelope. Rear-face mounting does not waive this limit. A noncompliant station
requires a dimensioned exception decision.

Use no primary-member notch or housing as the default. Connector-side shaping
is preferred. The owner's new direction permits investigation of a shallow
primary-member housed seat only when it resolves a named load-transfer or
geometry issue and its exact cut, fabrication, remaining section, splitting,
bearing, and complete joint behavior are evaluated. This supersedes the earlier
development-only blanket exclusion only for such investigated variants; no cut
is approved.

Permitted connector construction is a realizable one-piece solid-wood body, a
mechanically complete multi-piece wood assembly using ordinary through-bolts,
metal nuts, and suitable washers, or a structural-plywood body with explicit
product, layup, axes, and applicable connection evidence. Do not assume glue or
incidental screws create composite action. Custom fabricated steel, new steel
angles, barrel nuts, half-laps, and other interlocking primary-member joinery
remain outside this lane.

All release flags remain false. The imported 36-row criteria migration is a
pending planning record. It is not evidence and does not alter the selected
candidate's frozen criteria or ledger.

## 2026-09-23 — Return outer-node rear-envelope exception

The WJ-03 nominal screen finds a three-piece outer node on each side with all
four legacy duties and three distinct source hosts connected. Finished wood,
provisional installed hardware, diagnostic tool cylinders, and straight bolt
insertion/withdrawal sweeps have no modeled interference. All forty washer
seats have full modeled support. The original six outer-pair clash signatures
are absent and the connectors do not contact the floor. Four detached nut
paths per side are blocked by the under-header link or kicker, so the complete
nominal interference result is false.

Using the handoff canonical `N=(0,-sin(50°),cos(50°))` and the outer
post/header-front-bottom corner as datum, the connector body and permanent
body-plus-hardware envelope reach N = 225.718477 mm. The tool-only envelope
reaches N = 197.875857 mm and remains inside the connector body. Straight bolt
insertion reaches N = 315.648756 mm. The permanent and insertion envelopes
exceed the ordinary 139.7 mm limit by 86.018477 mm and 175.948756 mm. Record
`revise_named_constraint`; do not mark layout advancement or acceptance. The
node also retains a 1.0 mm minimum nominal tool gap, so tolerance-aware
clearance remains incomplete. WJ-04 may proceed independently while WJ-03 is
revised.

## 2026-09-23 — Shorten the under-header link and stage kicker removal

A revised WJ-03 trial shortens each under-header link from 203.2 to 185.2 mm
and increases its post gap from 53.0 to 71.0 mm. Both post-nut straight
removal paths now clear and the smallest modeled post-nut tool gap is 19.0 mm.
The two bridge/link nut paths per side still intersect an installed kicker.
Removing each kicker first makes the nominal detached-hardware screen clear.
That removal operation has not been validated, so layout advancement and all
release flags remain false. Permanent and temporary local-N exceptions are
unchanged, and tolerance-aware clearance remains open.

A diagnostic 100 mm straight forward sweep of each kicker's actual front face
has no positive-volume intersection with retained source wood, changed hosts,
connector bodies, or installed node stacks. Screw removal and operator/tool
access were not included; this does not close the sequence gate.

## 2026-09-23 — Expand the WJ-03 removal diagnostic

A later source-bound sequence screen supersedes the limited front-face sweep
for panel transport. Direct translation of each complete kicker panel hits
the adjacent main-lower panel from 1–18 mm, with a maximum sampled
33.544427 mm³ overlap. The same-side lower panel must be staged first for the
modeled 100 mm kicker path to have no sampled positive-volume hits. The
diagnostic carries source-assigned panel T-nuts, keeps LEDs and wires as
separate services, and records 12 lower-panel plus nine kicker screw axes per
side. Four center-kicker candidate receivers are absent; the other named
receivers have no assessed thread engagement or resistance. At the sampled
lower-panel and kicker staging poses, the nominal distance to a base-floor
member is zero. This is not tolerance clearance or a verified handling route.

A separate provisional short disengagement sweep clears all four bridge/link
nuts and washers with the kicker installed: shaft-tip projection is 23.749 mm,
nut travel 22.198 mm, and washer travel 23.849 mm. No selected hardware,
ratchet swing, capture, or retrieval method supports node-first removal, so
the lower-panel → kicker → node-hardware sequence remains the stated
development route. The permanent body-plus-hardware N maximum remains
225.718477 mm, 86.018477 mm over the ordinary limit. The bolt-stroke N
maximum of 315.648756 mm is temporary assembly workspace, not another
permanent-depth exception. WJ-03 stays partial and all release flags remain
false.

## 2026-09-23 — Prioritize ordinary WJ-04 bolt stack

The owner directed WJ-04 to prioritize one ordinary hex bolt, metal nut, and
two-washer stack. The brass-spacer salvage study is retained as history and is
not the active joint approach. Do not add a blanket smooth-shank-through-all-
wood requirement: classify the actual threaded bearing in each member under
the adopted NDS method, using the limited-thread provision only when its
member-specific one-quarter bearing condition is shown; otherwise use a
verified thread-root diameter or another justified adopted treatment. Record
the bolt's applicable bending-yield properties, verify full nut engagement,
real tools and removal, and all joint checks. The selected baseline's
full-root sensitivity result does not decide this distinct WJ-04 joint and
provides no transferable capacity. This is a development direction only; no
SKU, resistance, drilling, or release is approved.
