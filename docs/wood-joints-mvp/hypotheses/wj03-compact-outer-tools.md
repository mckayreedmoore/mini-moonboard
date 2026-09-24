# WJ-03 compact outer tool-access screen

Status: operation-specific geometry diagnostic only. It does not select a
tool, confirm physical access, release assembly, or establish structural
capacity. Trial: `compact_bridge_rear_bevel_4x6_spine_137_7` (20 bolt stacks).

## Recorded report

The archived JSON is byte-identical to the frozen tool report. SHA-256:
`57fe095ad53d7dd73d55ca6ef83d3fa9827a0eed58507eea98dd8ac8f5e5e06d`.
Its direct geometry and helper inputs are fingerprinted, including the WJ-05
center-backer transfer probe; the declared pin set is partial, not a recursive
source closure. No tool proxy fell below the analytical global plane `z = 0`;
that plane is not a physical floor model.

Recreate the materialization and report from the repository root (this is a
geometry operation, not a CAD solve):

```sh
uv run python -c "import json; from scripts.wood_joint_wj03_compact_outer_access import materialize_geometry; from scripts.wood_joint_wj03_compact_outer_tools import build_tool_report; print(json.dumps(build_tool_report(materialize_geometry()), indent=2))" > /tmp/wj03-compact-outer-tools.json
```

The report screens the Ko-ken 3305A-7/16 outside cylinder (55 mm long, 17.2 mm
maximum listed outside diameter) and a FACOM 34 7/16-in midget wrench envelope
(100 mm long, 22 mm head width). Neither tool is selected or received. The
socket's ratchet, extension, internal fit and handle are absent. Wrench
head/handle shapes and 15°/75° headings are proxies; the headings are not
catalog jaw orientations.

## Operation results

| Screened operation | Result across 20 stacks |
| --- | --- |
| Coaxial socket approach to bolt head | 20 outside-envelope screens clear |
| Coaxial socket approach to nut | 20 clear |
| Socket plus nut moved axially after unthreading | 16 clear; 4 overlap a WJ-03 under-header link |
| FACOM full-turn axial nut-removal envelope | 0 clear; broad proxy overlaps all 20 |
| Moving-nut wrench envelope vs fixed head-counterhold envelope | 20 clear at each sampled heading and for each bounded operation |
| Wrench bounded nut stroke / exit / reindex / reseat vs surroundings, heading 15° | 4 / 1 / 2 / 4 clear |
| Same wrench operation screens, heading 75° | 4 / 5 / 2 / 1 clear |
| Nut removal after unthreading | 20 clear |
| Nut washer slide to bolt tip | 18 clear; 2 overlap base rails |
| Bolt-only axial withdrawal after nut and washer removal | 20 clear |
| Head washer release after bolt withdrawal | 20 clear |

The four socket-plus-nut exit overlaps are at `knee_outer_left_post_1` and
`knee_outer_left_post_2` against `finished_wood/knee_outer_left_under_header_link`,
and the mirrored right post pair against
`finished_wood/knee_outer_right_under_header_link`. These are links in this
new WJ-03 outer trial, not the earlier WJ-05 center backers. The report records
no tool overlap against a named WJ-05 center post or backer. This does not
screen WJ-05 access or validate its center-receiver hypothesis.

The two nut-washer-slide overlaps are at
`knee_outer_left_side_2` / `finished_wood/base_rail_bottom_left` and the mirrored
right-side stack / rail. The sampled FACOM head-counterhold envelope also
overlaps local geometry at five stations for 15° and two for 75°: neighboring
WJ-03 hex heads at the paired spine, header and post stations, and
`finished_wood/base_side_right` at the right header stations. These are
external-envelope intersections, not proof that a real wrench cannot fit.
Likewise, the full-turn wrench proxy's 20 overlaps are not a physical
impossibility result. One station (`knee_outer_left_header_2`) has a clear
sampled 15° bounded stroke/exit/reindex/reseat path even though its full-turn
proxy overlaps.

## Smallest useful follow-up

Screen the proposed conventional sequence: hold the nut stationary with the
FACOM 34 7/16-in open-end candidate, turn the bolt from its head side using the
Ko-ken 3305A-7/16 socket and a named ordinary 3/8-drive ratchet, withdraw the
bolt through the nut, then remove the loose nut and washer. These remain
unselected tool candidates. The archived report already has clear bolt-only
axial withdrawal for all 20 stations, but it does not screen the fixed nut
counterhold, head-side ratchet/socket and turning sweep, or nut/washer handling
after the bolt is out. Check those motions without assuming a spacer or custom
tool. Capture/support, received tool fit, torque, hand access, thread
engagement and delivered full-form thread ends remain unverified. The report's
precondition also assumes the removable holds and projecting hold bolts have
been removed.
