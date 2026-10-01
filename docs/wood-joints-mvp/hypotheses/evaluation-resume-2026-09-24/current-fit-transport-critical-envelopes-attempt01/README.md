# Current fit and transport critical envelopes — attempt 01

This packet narrows T07 to the six direct candidate nut/nut-washer CAD hits on
four axes and the twelve retained leg-bolt component sweeps against two modeled
wire spans. It joins the exact T07 attempt02 records to the independently
reviewed T07/T08 option crosswalk and the T08 fastener-axis register. It does
not select a product or tool, change geometry, or clear a fit, installation,
service, removal, or transport gate.

## Candidate nut and washer envelopes

The pinned source-CAD/proxy slide screen reports these six direct axial hits.
The volume is the reported intersection volume in the sweep; it is not a
measured physical interference or a tolerance-aware clearance.

| Axis | Component | Modeled obstacle | Sweep intersection (mm³) | Slide (mm) |
| --- | --- | --- | ---: | ---: |
| `bottom_center/clip_horizontal_bottom_left_2/rail_2` | nut | `wood/center_principal_cleat_left` | 146.412520 | 21.336 |
| `bottom_center/clip_horizontal_bottom_left_2/rail_2` | nut washer | `wood/center_principal_cleat_left` | 0.235256 | 23.368 |
| `bottom_center/clip_horizontal_bottom_right_1/rail_2` | nut | `wood/center_principal_cleat_right` | 146.412520 | 21.336 |
| `bottom_center/clip_horizontal_bottom_right_1/rail_2` | nut washer | `wood/center_principal_cleat_right` | 0.235256 | 23.368 |
| `bottom_outer/clip_horizontal_bottom_left_1/rail_2` | nut | `wood/knee_outer_left_inner_frame_block` | 87.090910 | 21.336 |
| `bottom_outer/clip_horizontal_bottom_right_2/rail_2` | nut | `wood/knee_outer_right_inner_frame_block` | 87.090910 | 21.336 |

T07 also contains one two-stage local CAD route for each of the four axes. Each
route moves the nut and nut washer laterally, then 25 mm along the modeled
nutward vector; the external source geometry screen is clear. The lateral
vectors are:

| Axis | Lateral-first displacement (mm) |
| --- | --- |
| `bottom_center/clip_horizontal_bottom_left_2/rail_2` | `[-50.9623, 0, 0]` |
| `bottom_center/clip_horizontal_bottom_right_1/rail_2` | `[48.9623, 0, 0]` |
| `bottom_outer/clip_horizontal_bottom_left_1/rail_2` | `[53.9623, 0, 0]` |
| `bottom_outer/clip_horizontal_bottom_right_2/rail_2` | `[-55.9623, 0, 0]` |

The second move is approximately `[0, -16.069690, -19.151111]` mm for each
axis (the stored vectors retain their small numerical X components). The
separate modeled headward bolt path is also CAD-clear and 151.368 mm, including
its diagnostic 1 mm terminal allowance. These are local CAD paths:
thread-compatible unthreading is assumed, the displayed nut and shaft
envelopes overlap by about 181.794 mm³, and no loose-part capture, support,
full staging, or reverse assembly is established.

The T08 axis rows associate these axes with unselected 1/4-20 bolt leads
`kl-25c600hcs5z`, `hs-104-044`, and `wurth-072-14-6`, and conditional component
leads `kl-25cnfh5z` (nut), `kl-25nwus` (washer), and `mcmaster-91201a029`
(optional spacer). The pinned records state these nominal dimensions:

- K.L. Jack nut lead: 7/16 in across flats (11.1125 mm), 7/32 in nominal
  thickness (5.55625 mm).
- K.L. Jack wide washer lead: 0.312 in ID (7.9248 mm), 47/64 in OD
  (18.653125 mm), and 0.051–0.080 in thickness (1.2954–2.032 mm).
- McMaster spacer lead: 0.281 in ID (7.1374 mm), 0.625 in OD (15.875 mm),
  and 0.120–0.130 in thickness (3.048–3.302 mm). It remains a conditional
  geometry lead, not an accepted support washer.

The listed nut size has 7/16 in FACOM and Wera profile comparators in the
crosswalk. FACOM's published profile is 22 mm wide, 3 mm thick, and 100 mm
long, and it is the synthetic profile used by the earlier T07 proxy. On all
four candidate axes the proxy approach samples had zero clear approaches;
turn-pose clear counts varied and do not qualify access. The Wera 7/16 in
profile is larger (25 mm external width, 6.3 mm thickness, 165 mm overall)
and has not been fit-screened. Neither profile is selected, and no CAD record
binds the conditional component leads to the current BRep nut/washer shapes.

## Retained leg-bolt and wire envelopes

The T07 source-CAD screen sweeps the head, head washer, and shaft together
through a 200.025 mm headward withdrawal. Every component sweep overlaps a
modeled wire span; the same modeled spans appear on the reverse insertion
screen. These are twelve component/obstacle rows, not proof that a flexible
installed cable physically blocks the operation.

| Axis | Modeled wire span | Head sweep (mm³) | Head-washer sweep (mm³) | Shaft sweep (mm³) |
| --- | --- | ---: | ---: | ---: |
| `lumber_leg_bolt_left_1` | `protected/wires/wire_010_A10_A11` | 289.435523 | 277.665999 | 163.212433 |
| `lumber_leg_bolt_left_2` | `protected/wires/wire_010_A10_A11` | 226.901252 | 331.949494 | 43.357046 |
| `lumber_leg_bolt_right_1` | `protected/wires/wire_130_K10_K11` | 289.436544 | 277.665101 | 163.211710 |
| `lumber_leg_bolt_right_2` | `protected/wires/wire_130_K10_K11` | 226.901167 | 331.946791 | 43.357047 |

For each retained axis, the current component envelopes screen clear on the
separate 19.05 mm nut and 22.225 mm nut-washer axial slides, while the longer
head/head-washer/shaft path intersects the modeled wire. Neither result
establishes thread release, capture, tool access, support transfer, or a cable
service route. The T08 references are preserved selected-baseline references
(`#407` bolt, `#2573` nut, and two `#15025` washers), not selected or delivered
WJ hardware. T07's pinned #407 source comparator gives a 3/4 in across-flats
head; T07 used a 7/16 in FACOM proxy on these axes, which is a size mismatch.
A Wera 3/4 in profile comparator is recorded (42 mm external width,
9.5 mm thickness, 246 mm overall), but was not applied to a fit screen.

The existing CAD nut envelope is 11.5316 mm high versus the cited #2573
maximum of 11.3792 mm, a 0.1524 mm nominal discrepancy already marked for
recheck in the source record. This is a source-level warning, not a delivered
part comparison or an accepted fit result. Exact #407/#2573/#15025 dimensions,
lot identity, matched stack, tolerances, and actual tools remain unbound.

## What the records support next

For the candidate axes, a selected delivered bolt/nut/washer stack and its
dimension/tolerance records are needed before comparing the BRep hit volumes
to real hardware. The next CAD screen should bind those records, a selected
size-matched tool and its counterhold, and a clearance allowance to the
existing local route; it must also model how the loose nut and washer are
held and staged and how the operation reverses.

For the retained axes, resolve the current cable's actual installed route and
reversible service state, then screen the wire envelope and stack path in that
state with a selected 3/4 in tool/counterhold profile. The current synthetic
7/16 in profile cannot answer that question. Full member movement, hand
workspace, support, capture, staging, integrated sequence, and transport remain
open for both groups.

This packet does not select a product or tool, assert delivered fit, establish
physical cable blockage or service, clear installation/removal/transport, or
change candidate acceptance. No geometry or native-solver work occurred.

## Reproduction and pins

From the repository root:

```sh
python3 docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-fit-transport-critical-envelopes-attempt01/build_envelopes.py --check
```

The producer verifies the frozen T07/T08/crosswalk review pins and rehashes
all 28 T07, 35 T08, and 74 reviewed-crosswalk source-pin rows (72 unique
source paths). It verifies the axis joins, exact hit counts, source pointers,
and unchanged unresolved-operation boundary before checking the generated
[critical-envelopes.json](critical-envelopes.json). The JSON contains the
full 18-row axis/component/obstacle matrix, conditional dimensions, tool
comparators, route vectors and source pointers.

The main upstream records are [T07 attempt02](../current-fit-transport-closeout-attempt02/evidence-register.json),
its [exact-component candidate screen](../access-screen-attempt03-exact-components.json),
[retained access screen](../retained-access-attempt03/access.json),
[captured local-motion screen](../captured-nut-motion-attempt02/motion.json),
and [focused tool/wire report](../step6-operation-coverage-attempt01/tool-route-feasibility-attempt01/tool-route-feasibility.json);
the option join is the [parent-reviewed crosswalk](../current-fit-transport-option-crosswalk-attempt01/option-crosswalk.json),
and conditional hardware dimensions come from the [T08 axis register](../current-hardware-material-cost-closeout-attempt01/fastener-axis-register.json).
