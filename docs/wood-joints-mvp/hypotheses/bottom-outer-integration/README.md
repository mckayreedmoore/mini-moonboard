# Bottom-outer two-duty hypothesis

Status: local nominal geometry checked against retained WJ18, 2026-09-24.
The fourth attempt completed in 32.01 seconds; the
[report](attempt-04/geometry.json) clears nominal body/hardware conflicts,
eight receiver-layer stacks, sixteen washer seats, four native host replays,
and both purchased-panel receiver overlays. Seventeen focused tests pass.
The integrated layout still covers eighteen duties; this local pair is not
merged or accepted. Three earlier adapter failures remain preserved.

Two recorded head-tool approaches intersect wires: the left `side_1` tool
hits `wire_001_A1_A2` by 182.434194 mm³, and the right `side_1` tool hits
`wire_121_K1_K2` by 205.919258 mm³. The installed `rail_2` shaft, nut and
nut-side washer on each side also occupy part of the existing WJ03 `side_2`
nut-tool envelope. The new rail nut tools overlap old tool envelopes as well.
These are access findings, separate from the clear installed-hardware screen.
Wiring state and supported operation order require explicit investigation;
neither simultaneous-tool clearance nor physical impossibility is inferred.
Finite paired contact area, tolerances, mechanics, and actual tool operation
remain open. The [execution record](attempt-04/execution.json) and
[manifest](attempt-04/sha256.json) bind this retained-object run.

The source-bound producer consumes WJ-16 or WJ-18 geometry without rebuilding
either family. It replaces exactly `clip_horizontal_bottom_left_1` at
`base_rail_bottom_left` / `base_side_left` and
`clip_horizontal_bottom_right_2` at `base_rail_bottom_right` /
`base_side_right`. Each duty replaces its six original SDS axes and proposes
one full-section 88.9 × 88.9 × 119.7 mm cleat with four through-bolts: two
through the cleat and 38.1 mm rail, and two through the cleat and 88.9 mm
side member. Each family’s rail, faces, and kerf-right length come from its own
measured source datum.

In each rail’s local X/T/N frame, the left cleat is X=0..88.9, T=38.1..127,
N=10..129.7 mm. The right cleat is X=949.175..1038.075, T=38.1..127,
N=10..129.7 mm. The proposed cleat grain is N. Rail-axis centers are at
N=55.45 and 84.25 mm with 28.8 mm spacing. Their nominal grain-end distances
are 45.45 mm against a conditional 7D distance of 44.45 mm for a 6.35 mm
bolt. A ±0.5 mm station allowance reduces that nominal margin to 44.95 mm;
actual stock tolerances and the signed force direction remain unresolved.
Side-axis centers are at rail-local T=68.15 and 96.95 mm and N=69.85 mm.
Bolt and washer dimensions are inherited as provisional WJ-06 envelopes only:
the 127 mm rail grip uses a 152.4 mm nominal length and the 177.8 mm side grip
uses a 203.2 mm nominal length. Length bounds do not establish delivered
thread location, nut engagement, or fit.

The WJ-03 compact outer envelope is checked separately from its installed
hardware and broad tool cylinders. Its spine, rear bridge, and under-header
link are in the collision scene. The existing WJ-03 side-bolt rows remain
separate source hardware; its nominal 50 mm long, 25.4 mm diameter tool
envelopes are not treated as hardware. The screen is only for these recorded
nominal shapes, not an assembly or removal demonstration.

The producer exports raw and finished cleats, eight candidate bore and
hardware records, the twelve replaced source-axis IDs, and separate native
source and purchased panel-screw cut maps. The four existing purchased
receiver cuts in the two bottom rails are replayed from the pinned source and
remain part of the parent’s union-cut obligation. It exports no finished
shared-host replacement; the parent compositor must rebuild each shared
member from raw stock and the complete native, purchased, and candidate cut
union. All 66 panel axes and twelve frame-bolt arrangements remain fixed.

The result is geometry evidence only. Signed member actions, receiver
resistance, thread fit, actual tool access, layer tolerances, transport, and
complete cross-family mechanics remain open. Cutting, drilling, fabrication,
structural approval, and assembly are not released.

The coincident mating-face rectangles are reported as gross nominal areas.
Finite paired contact after the complete shared-host and cleat bore/cut union
has not been calculated; the producer does not treat the gross rectangles as
finished contact or bearing area.

Preflight attempts and exact producer/test snapshots are recorded under
[`preflight/`](preflight/); the archived attempts did not complete the full
bottom-outer integration report.
