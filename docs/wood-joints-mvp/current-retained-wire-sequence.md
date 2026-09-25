# Retained leg-bolt wire-stage follow-up

Status: bounded sequence hypothesis for the four retained lumber-leg bolt
withdrawals flagged by the current access screen. The approved
`led-clearance-2x6-runner-seated-blocks-v1` geometry and wiring route remain
unchanged. This note defines a separate service-state screen; it does not
claim that the harness can be removed, that a bolt path is physically blocked
or clear, or that a transport sequence is established.

## Current finding

The [corrected retained-access screen](current-retained-access.md), using the
1,041-shape live scene, reports modeled wire intersections on the four
200.025 mm head-side lumber-leg bolt sweeps. The
[attempt03 report](hypotheses/evaluation-resume-2026-09-24/retained-access-attempt03/access.json)
has SHA-256 `fffa0027926a57583cc13ffbcef552fc8e5f8da96964d50c64ef63ffd4ce4c97`.
Travel has zero terminal allowance. Left-side bolts withdraw toward +X;
right-side bolts toward −X.
The head, head washer, and shaft each intersect the same modeled wire on each
side:

| Target bolts | Modeled span | Head overlap (mm³; bolts as listed) | Head-washer overlap (mm³; bolts as listed) | Shaft overlap (mm³; bolts as listed) |
| --- | --- | ---: | ---: | ---: |
| `lumber_leg_bolt_left_1`, `lumber_leg_bolt_left_2` | `wire_010_A10_A11` | 289.436 / 226.901 | 277.666 / 331.949 | 163.212 / 43.357 |
| `lumber_leg_bolt_right_1`, `lumber_leg_bolt_right_2` | `wire_130_K10_K11` | 289.437 / 226.901 | 277.665 / 331.947 | 163.212 / 43.357 |

These are source-solid motion-sweep intersection volumes, not snag loads or
proof that a real flexible cable blocks extraction. A possible service-state
screen should therefore answer a narrower question: do the four modeled
withdrawal and reverse-insertion paths clear when the relevant harness parts
are actually staged out of the operation state?

## Which service parts the hits belong to

The source routing map has 132 installed LED datums divided across three
50-LED strings: string 1 is A1–E2 (indices 1–50), string 2 is E3–I4 (51–100),
and the installed portion of string 3 is I5–K12 (101–132). The [modeled
spans](../led-wiring-reference.json) identify
`wire_010_A10_A11` as span 10 within string 1 and `wire_130_K10_K11` as span
130 within string 3. Thus both end strings are implicated. Staging the earlier
[pack 2/3 WJ-04 hypothesis](hypotheses/service-harness-transport-staging.md)
would remove the pack-3-side candidate only; it opens the string 1/2 boundary
at `wire_050_E2_E3` and leaves `wire_010_A10_A11` in pack 1. It cannot by
itself address both sides of the retained leg-bolt finding.

A candidate topology for testing both sides would stage string 1 and the
installed portion of string 3 separately while retaining string 2. That would
require resolving both existing boundaries, `wire_050_E2_E3` and
`wire_100_I4_I5`. This is a candidate state assignment, not a demonstrated
connector operation. `wire_100` is adjacent to the reported PWR1 connection
at the end of string 2 (I4); identify the actual PWR1 extension and its route
before assuming it can remain with string 2 or be disconnected. The model
reports an arithmetic 18-LED unused tail on the third string; its physical
storage and restraint also need to be accounted for.

## Completed geometry-only lower bound

The [lower-bound report](hypotheses/evaluation-resume-2026-09-24/retained-wire-lower-bound-attempt01/report.json)
and its [README](hypotheses/evaluation-resume-2026-09-24/retained-wire-lower-bound-attempt01/README.md)
derive an obstacle subset from the completed retained-access attempt03
collision maps. The derivation excludes only
`protected/wires/wire_010_A10_A11` and
`protected/wires/wire_130_K10_K11`: 1,041 installed obstacle entries become
1,039. All 24 checks (four axes × head, head washer, and shaft × withdrawal
and reverse insertion) have no remaining hit at the source hit threshold;
reverse insertion reuses the identical swept occupancy. The report rows match
the original removed-wire hit maps, and the complete collector loop checks
every non-excluded obstacle without early exit or hit truncation. No other
obstacle IDs are excluded, and the approved geometry remains unchanged.
The derived report SHA-256 is
`5f59dcd1400cdf00f2b5ff0f1960b8598706707572766bf1d50c148b85380620`.

This is an analytic subset of completed exact-source sweeps, not a new CAD
run. It establishes only that the two named modeled wire solids account for
all recorded intersections in these four paths. The two wires have not been
shown removable, and the other components of strings 1 and 3 remain in the
scene for this lower-bound calculation. It does not establish a strand
service state, physical clearance, or an assembly/transport operation.

## Remaining service-state screen

Keep the approved source geometry and route frozen. Once the actual
connection and anchoring map is available, derive a distinct stage with the
physical parts that would leave with strings 1 and 3 removed and all residual
connector pieces, PWR1 wiring, string 2, panels, members, and hardware
retained. Screen service withdrawal and restoration, then repeat the four bolt
paths and their reverse paths in that staged scene. Preserve all unrelated
obstacles and report every excluded shape by ID and reason. If panels must
move, name the exact panels and screw operations, and include panel support,
handling, remaining wire routes, and reinstallation in the sequence; do not
simply suppress panels from the scene.

For the service-state screen, first document the physical build assumptions:
which spans or connectors are attached to a panel or timber, all clips,
adhesive points, ties, strain reliefs, fixed endpoints, free slack and bend
limits, connector mating faces, and the control-box/PWR1 branches. Test whether
the strings can be isolated from mains, disconnected at the two existing
boundaries, LEDs withdrawn from their panel holes, and wires fed out of the
enclosed passages without pulling on LEDs, damaging insulation, or exceeding
bend/slack limits. Record the exact parts carried by each staged string and
where they are restrained. The same conditions must support refeeding,
reconnection, LED reseating, and an electrical continuity/startup check after
bolt reinstallation.

## Limits on the service hypothesis

The current [wiring producer](../../mini_moonboard/round_service_wiring.py)
creates fixed swept wire solids and LED bodies, but no separate cable clips,
strain reliefs, anchors, or slack accommodation. It models connector cylinders
fused into spans 50 and 100 rather than mating connector halves. The wiring
reference marks cable dimensions, connector fit, bend radius, feed access,
and slack as unqualified; it calls for frame, then panels, then feeding the
strand and installing LEDs. That supports the initial assembly order, not its
reverse as a proven service procedure. The nominal 13 mm panel hole also does
not establish LED extraction clearance because LED-body dimensions and
tolerances remain unknown.

Any later physical handling validation would need its own authorized scope;
this note authorizes analysis only. Such validation would need the intended
LED kit, connectors, panels, passages, anchors, and controller leads, with the
route recorded before and after each disconnection. The installation guide's
push-fit joint does not by itself establish post-install release or re-use.
Do not cut or splice the harness, invent a new attachment or route, or infer
clearance by deleting entire string spans from the current scene. The four
bolt paths also remain subject to the separate thread, counterhold, capture,
support-transfer, tool, and tolerance checks in
[current retained access](current-retained-access.md).
