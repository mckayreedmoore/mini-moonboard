# Current layout access and service obligations

Status: bounded evidence register for
`led-clearance-2x6-runner-seated-blocks-v1` (owner-reviewed at `b1e8707d`).
This records geometric work still needed; it does not accept an assembly,
select hardware, release fabrication, or establish physical compatibility.
The current inventory is 24 blocks, 92 candidate bolt axes, 12 retained frame
bolt stacks, and 66 panel/kicker screw axes (58 unchanged and 8 moved).

## Current obligations

| Area | What current evidence says | Remaining bounded work |
| --- | --- | --- |
| Candidate-bolt access (92 axes) | The current [attempt03 exact-component screen](current-access-screen.md) covers all 92 candidate axes against 1,231 live-scene obstacles. Exact continuous sweeps of shaft, head and head washer report zero intersections under the headward-withdrawal exclusions; that operation assumes nut and washer already removed. Four exact source-BRep nut slides and two bottom-center nut-washer slides hit wood. Captured-nut attempt02 then found one complete local two-stage CAD motion for each affected axis: headward bolt travel with a 1 mm terminal allowance, followed by an axis-specific lateral nut/washer move and 25 mm local nutward move. | Resolve thread-compatible unthreading, actual tools, counterhold and part capture; the boreless nut display envelope overlaps the shaft by the same 181.794 mm³ before and during withdrawal. The 25 mm nutward segment is a bounded local path, not full-scene extraction or a proven staging location. Verify the reverse assembly path and physical fit before relying on it. |
| Wrench access on candidate bolts | Attempt03's wrench rows are unchanged from attempt02's unselected 22 mm × 3 mm, 100 mm FACOM-profile proxy. At least one synthetic proxy pose overlaps at every head side and nut side: head approach 129/184, discrete turns 427/920 and angular AABBs 322/368; nut approach 147/184, discrete turns 480/920 and angular AABBs 336/368. | Check named candidate tools and actual head/nut access with counterhold, full turning stroke, re-indexing, hand clearance, tolerance and staging. Proxy overlap is not proof a real wrench is blocked; a clear proxy pose would not establish actual tool access either. |
| Retained frame bolts (12 stacks) | Their current identities, receiver pairs, stations and nominal sizes reconcile to the selected construction packet with zero reported origin/direction/diameter/length deltas. The current frame-bolt review still marks all 12 `candidate_recheck_status: required`. General access attempts and the captured-nut probe retain them as obstacles, not target operations. | Screen tool, counterhold, component capture and shaft withdrawal for each retained arrangement in the revised full scene. Separately recompute their demands/resistance under the new runner-seated load path; identity reconciliation is not an access or structural pass. |
| G1/G2 lights and holes | The current revision resolves the former G1 hole-projection and G2 light/body conflicts in CAD. Both 13 mm × 50.8 mm rear paths and light bodies clear checked timber; each has 1.35 mm minimum clearance to its nearest block. G2 moved 5 mm outward, from panel coordinates (1400, 199.2) to (1405, 199.2) mm, and its two adjacent wire endpoints moved with it. | Preserve this geometry result as a narrow nominal check. It does not prove a feed path, connector handling, tolerances, or a permissible patch to a drilled panel. The panel contains the new G2 hole only in CAD. |
| G6/G12 hold-bolt corridors | The current revision report still flags both. Its G6 finding says a middle corner block intersects the provisional clearance envelope behind G6; the G12 finding says the top-right center block retains its overlap with the provisional G12 envelope. These are unresolved envelope clashes, not verified contact with a selected hold bolt or proof that an actual hold cannot fit. | Reconcile each corridor against the present exact panel, block and T-nut datums, then bind an actual hold/bolt product and its removal/access path if product compatibility is being claimed. Keep current installed T-nut fit separate from hypothetical future hold-layout sites. No numeric G6/G12 clearance result is reported by the latest revision summary. |
| Wiring and LED service | The current revision reports a modeled G1–G2 wire intersection with the bottom-right rail, reduced from 532.196 to 515.757 mm³; G2–G3 has no checked intersection. It also records ten modeled wire crossings at the bottom rails and an F1–G1 crossing at the taller right central block. The source-supported initial order is frame, panels, then feed/install LEDs. | Reconcile the current routed wires and full service state against the final scene. For later member movement, test the proposed intact second/third-pack staging on current geometry: open the existing pack 1/2 connection at `wire_050_E2_E3`, keep the pack 2/3 connection at `wire_100_I4_I5`, and resolve the PWR1 endpoint. Check capture, withdrawal, refeed and continuity. Older discrete wire-solid hits are not proof a flexible cable route is physically blocked; this staging hypothesis is not a demonstrated operation. |
| Panel and kicker support / screws | The current [receiver/contact screen](current-receiver-screen.md) reconciles all 66 modeled screw axes: each enters its raw receiver envelope and clears the finished receiver; eight moved axes are recorded and no new receiver axes were added. This is not installed embedment. Raised lower-panel edge support and the center kicker seam remain open. | Evaluate actual panel support/span and load transfer, particularly the eight moved axes, both kicker inner edges and the center seam. Continuous direct backing is not established, but is not prescribed as the required architecture. Track the 66 panel-screw operations apart from the 92 candidate and 12 retained frame-bolt stacks. |
| Individual-member transport and ordinary-N | No current full disassembly/transport sequence or complete local-N envelope disposition is reported. The development plan retains a 139.7 mm ordinary local-N envelope and requires a named datum, connector extent, complete installed-hardware projection and tool envelope at each station. | Map removal and reassembly while preserving individual-member transport and avoiding routine removal of structural wood-engaging threads. Measure permanent connector/hardware extents by named station and local datum; report temporary tool, nut-exit and withdrawal workspace separately. Record any exception as a dimensioned, station-specific request. Include panels and service state, and count the 66 panel-screw operations separately. |

## Hypothetical denser-grid midpoint review

The 491-site [midpoint report](hypotheses/midpoint-clearance-2026-09-24/README.md)
is explicitly hypothetical and belongs to
`outer-rear-bridges-under-header-links-removed-v1`, before the current block
consolidation and the 5 mm G2 datum move. It uses a 25.4 mm full-disk flange
proxy plus an 11.1125 mm × 50.8 mm provisional rear projection. It is not a
compatibility result for an actual future hold product or a current-layout
clearance rerun. Its counts are useful only as a screen of that earlier
hypothetical grid:

| Hypothetical sites | Sites | Timber hits | Flange hits |
| --- | ---: | ---: | ---: |
| LED horizontal midpoints | 120 | 14 | 12 |
| LED vertical midpoints | 121 | 21 | 20 |
| Hold T-nut horizontal midpoints | 120 | 15 | 12 |
| Hold T-nut vertical midpoints | 121 | 1 | 0 |
| Kicker T-nut horizontal midpoints | 9 | 0 | 0 |

Notable predecessor results were the right central principal blocking all
F–G horizontal midpoints in rows 1–12 in both grids; the G1–G2 vertical
T-nut midpoint meeting the bottom-right center block at 10 mm; and the G6–G7
vertical LED midpoint meeting the right inner middle block at 20 mm. All 121
vertical LED midpoint sites overlapped existing T-nut envelopes, and all 121
vertical T-nut midpoint sites overlapped existing LED envelopes. No tested
midpoint hit a structural-bolt or panel-screw envelope. Plywood was excluded
because the holes were hypothetical; future hold bodies, retention screws,
diagonals and tool sweeps were not checked. Rear-projection-only hits depend
on the eventual hold-bolt length.

If the denser grid is revisited, rerun these sites against the current G2 datum,
current full geometry, and specified hold/T-nut/bolt products. Until then,
these counts neither approve nor disqualify any actual product or station.

## Evidence limits and closure order

Attempt03 reports zero intersections for exact continuous shaft, head and
head-washer sweeps, four exact source-BRep nut-slide intersections and two
exact source-BRep nut-washer intersections. Captured-nut attempt02 records a
locally clear CAD route on each affected axis, under an assumed unthreaded,
thread-compatible state; it is not physical access or full-scene extraction.
The conditional sequence graph reports no edges or cycles, remains incomplete
across build states, and does not include the alternate captured-nut sequence.
Wrench poses and angular bounds remain synthetic. The 12 retained frame bolts
are obstacles but not target operations. The current access map includes legs,
runners, panels and all 92 candidate-hardware roles as scene obstacles.

The next useful closure is to bind compatible thread geometry, selected tools
and actual capture for the four locally screened nut routes; verify reverse
assembly and whether the staged parts can reach a real handling location. Also
screen the 12 retained frame-bolt arrangements and review wrench-proxy
overlaps with selected tools and tolerance envelopes. Resolve full-build
ordering with all build states and dependencies represented. Keep the separate G1/G2 and
G6/G12 findings, panel support, harness/service state, individual-part
transport, and ordinary-N dimensions visible in the final disposition.
Geometry changes must be identified before they are made and their affected
evidence rerun; none of these access screens transfers a historical capacity
or releases physical work.
