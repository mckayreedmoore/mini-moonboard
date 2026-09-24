# WJ-03 outer-node result

Status: **Partial — current integrated sequence remains diagnostic; permanent envelope and right-panel return remain open**

The current [`wj03-sequence-diagnostic.json`](wj03-sequence-diagnostic.json)
includes the WJ-05 diagnostic backers, shifted posts, bolts, and stacks, and
maps all four center receiver IDs. It is a nominal sampled geometry
diagnostic, not a sequence or layout acceptance. Both staged poses have zero
nominal gap to base-floor wood. The right lower-panel return's terminal LED
hits reflect an inherited source-pose mismatch: the kerf-right panel and its
13 mm service bores shift by `-KERF_EACH_MM` (1.5875 mm), while electrical
parts remain at their earlier source datums. Outbound samples omit the
installed zero position, but reverse samples include it. This is not a new
return-only obstruction or a result of the WJ-05 backers. Resolve the
candidate's service-bore pose convention and regenerate both paths. No LED
removal or disconnection is prescribed as a fix; the selected baseline is
unchanged.

The source-bound left and right `knee_outer_*` assemblies each map
`clip_timber_header_outer_*` and `clip_angle_base_*`. Each node uses three
square-cut nominal 4×4 pieces: an outer spine, rear bridge, and under-header
link. Five changed source hosts retain their selected-candidate service,
panel-screw, and frame-bolt openings, fill the four removed stations' SDS
holes, and add twelve candidate bores. No primary frame member is notched.
Each connector and changed host records exact local X/T/N extrema from the
named node datum. Source binding reconciles all 66 fixed screw axes and twelve
frame-bolt axes by members, origin, direction, occupied length, diameter, and
bolt grip.

## Host and interface map

| Source host | Transfer path per side | Fasteners per side |
|---|---|---:|
| Outer post | Post → spine | 2 |
| Outer side member | Side → spine | 2 |
| Header | Header → under-header link | 2 |
| Internal connector path | Spine → rear bridge → under-header link | 4 |

The pair has six connector parts, twelve interfaces, twenty provisional bolts,
forty washers, and twenty nuts. Nominal lengths are eight 152.4 mm bolts and
twelve 203.2 mm bolts. The 8.0 mm washer openings fully support all forty
modeled seats around 7.5 mm bores. No hardware product, grade, delivered
shank/thread transition, washer product, nut product, or drill bit is selected.

## Nominal clearance result

Finished connector bodies, changed host bodies, installed stacks, 25.4 × 50 mm
diagnostic tools, straight bolt strokes, detached hardware paths, purchased
63.5 mm panel/kicker screw envelopes, and retained frame-bolt stacks, tools,
and withdrawal envelopes, twenty retained ML24Z bodies, and 120 retained SDS
envelopes were screened at a `1e-6 mm³` positive-volume
threshold. Installed stacks, tools, and bolt strokes have no modeled clash. All
washer seats are fully supported. The six historical outer-pair clash
signatures are absent. No connector or installed envelope reaches the physical
floor.

The under-header links are now 185.2 mm long, with a 71.0 mm post gap. This
clears the two post-nut removal paths per side and increases their diagnostic
tool gap to 19.0 mm. Two bridge/link nut paths per side still hit the kicker
when the kicker is installed. With that kicker removed first, the modeled
straight 50 mm detached-hardware paths clear and the conditional replacement
nominal interference result is true. The current WJ-03 sequence report samples
the staged panel and kicker motions, but does not establish continuous motion,
support, actual tool use, or service handling for layout advancement.

The [current sequence diagnostic](wj03-sequence-diagnostic.json) screens 12
same-side lower-panel screws and nine kicker screws per side. All 42 nominal
coaxial tool and shank-withdrawal sweeps have no unrelated-geometry hits. The
four center-kicker screws use WJ-05 diagnostic backers; this does not check
thread engagement, receiver resistance, or backer attachment capacity. Source
panel identity assigns 36 left and 30 right lower-panel T-nuts, plus five
T-nuts to each kicker. LED bodies and wires stay fixed as separate services.
Their handling and reinstallation are not modeled.

The diagnostic uses a `1e-4 mm³` positive-volume threshold and moves each
adjacent lower panel outward 250 mm in 25 mm steps without a sampled hit.
Direct +Y kicker translation then hits
the retained main-lower panel at 1–18 mm, with a maximum sampled overlap of
33.544427 mm³ per side. After staging that panel, each 100 mm kicker extraction
and reverse return has no sampled positive-volume hit in 1 mm steps. The lower
panel reverse return is clear on the left. On the right, its sampled reverse
path meets fixed LED bodies `G1` through `K7` (35 modeled lights; 317.86834
mm³ each) at the terminal 250 mm position. This apparent asymmetry comes from
the inherited source-pose mismatch described above: outbound samples omit the
installed zero position and reverse samples include it. Correct the
candidate's service-bore pose convention, then regenerate and review both
directions; this report does not prescribe removing or disconnecting LEDs.
At the sampled 250 mm lower-panel pose and 25 mm staged-kicker pose, each body
is tangent to its same-side base-floor member: the measured separation is
0.0 mm. Positive-volume clearance is therefore not a tolerance margin.
Continuous motion, support and handling, screw-head tool swing, service
operations, and measured-part fit remain open.

Four provisional bridge/link nut stacks have 23.749 mm shaft-tip projection.
A shorter diagnostic route needs 22.198 mm of nut travel and 23.849 mm of
washer travel to disengage; their nominal sweeps and 25.4 × 50 mm coaxial
socket envelopes show no positive-volume hits with the kicker installed.
There is no selected nut, socket, ratchet, or method to capture and retrieve
released hardware. This alternate route does not establish node-first
disassembly. The lower-panel → kicker → node-hardware order remains a
diagnostic development sequence, subject to resolving the source-pose and
service-bore convention and verifying support, service handling, and
continuous motion. Sequence verification remains false.

| Named measurement | Left | Right |
|---|---:|---:|
| Connector to base floor member | 6.35 mm | 6.35 mm |
| Connector to physical floor plane | 146.05 mm | 146.05 mm |
| Connector plus installed hardware to floor plane | 126.251 mm | 126.251 mm |
| Rear bridge to header rear | 6.35 mm | 6.35 mm |
| Post nut tool to shifted link | 19.0 mm | 19.0 mm |
| Side tool to bottom rail | 27.108 mm | 27.108 mm |
| Header tool to bottom rail | 70.412 mm | 70.412 mm |
| Bridge/link tool to outer kicker hardware | 71.819 mm | 73.627 mm |

The 19.0 mm tool gap is a nominal geometry result, not a fabrication or
product tolerance pass.

## Required revisions

The local frame uses the handoff canonical
`N=(0,-sin(50°),cos(50°))`. Its datum is the outer
post/header-front-bottom corner. Both sides have the same exact local-N
extents. Against the ordinary 139.7 mm rearward limit:

| Envelope | N min | N max / rear projection | Amount over ordinary reference |
|---|---:|---:|---:|
| Connector body | -15.903389 mm | 225.718477 mm | 86.018477 mm |
| Installed hardware only | -8.015072 mm | 159.988525 mm | 20.288525 mm |
| Permanent body plus installed hardware | -15.903389 mm | 225.718477 mm | 86.018477 mm |
| Temporary 50 mm tool only | -35.779146 mm | 197.875857 mm | 58.175857 mm |
| Temporary straight bolt stroke only | -8.015072 mm | 315.648756 mm | 175.948756 mm |

The connector body controls the unresolved permanent 86.018477 mm exception.
The tool stays inside that rearward maximum. The 175.948756 mm amount for
straight bolt insertion is a temporary workspace comparison against the
ordinary reference, not another permanent frame-depth exception. Its space
must be verified in the declared assembly state. Layout advancement stays
false while the permanent disposition, movement and support sequence, and
tolerance-aware clearance remain open.

## Reproduce and inspect

```bash
uv run python -m scripts.wood_joint_clearance --write
uv run python -m scripts.wood_joint_wj03_sequence
uv run python -m scripts.export_wood_joint_scene
uv run python -m http.server 8000 --directory site
```

Open `http://localhost:8000/wood-joints-outer-viewer.html`. The scene is an
unreleased WJ-03 development view. It verifies the baseline manifest and every
loaded STL byte against the recorded 725-asset hash set before rendering.
