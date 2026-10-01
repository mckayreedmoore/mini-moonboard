# WJ24 hardware and material requirements

**Status:** conditional, source-bound dimensional requirements for the 92-axis `led-clearance-2x6-runner-seated-blocks-v1` geometry. This is not a product selection, delivered-part acceptance, capacity result, joint pass, or fabrication release.

The producer reads the pinned geometry and local source records only. The complete per-axis receiver intervals, stack envelopes, and class comparisons are in [`requirements.json`](requirements.json). [`source-pins.json`](source-pins.json) records the fixed SHA-256 inputs; both replay modes fail if any source bytes change.

## Geometry and calculation basis

The grip-screen receiver intervals are already measured from the adjacent head bearing face/head-washer headward face. Their field name is `intersection_solid_intervals_from_underhead_mm`, and the source records coincident head/head-washer contact. The producer does not subtract the global datum again. A separate tested conversion rule rebases global-axis intervals only when an explicit underhead scalar is supplied.

For each raw receiver interval `[a,b]`, with `t=b-a`, the nominal-diameter NDS screen requires `LB >= b - t/4`; it therefore caps thread bearing in that member at `t/4`. This direct requirement uses the frozen underhead-relative interval exactly. A separately reported sensitivity shifts the interval by the difference between the published maximum head-washer thickness and the modeled thickness. If a receiver ever contains multiple disjoint intervals, the producer stops and requires member-level gap analysis rather than treating each piece as an independent member. `D = 6.35 mm` is a modeled nominal-diameter assumption. No NDS resistance or joint pass is calculated.

The dimensional ranges used for each washer role are 0.051–0.080 in (1.2954–2.032 mm), from the K.L. Jack 25NWUS catalog lead. The nut's finished outer-height comparison is 0.212–0.226 in (5.3848–5.7404 mm), from the ASME B18.2.2 1/4-in nut envelope. Those are source ranges, not evidence that a selected or delivered washer/nut matches them. The model keeps head washer, shaft, nut washer, and nut as separate roles.

The physical tip target is the worst-case far nut face plus three 1/4-20 pitches (3.81 mm), a documented length-only projection scenario. The existing WJ24 unthreaded CAD allowance is 3.175 mm and is reported separately. Neither projection requires full-form thread through the tail. For sufficient nut-profile coverage, a continuous full-form external-thread interval would span from the earliest possible nut bearing plane through the latest possible nut far face. This envelope uses the published washer/nut dimensions and is deliberately stronger than a claim about the nut's unknown active-thread height. It is not exact thread fit, chamfer capacity, or strength evidence.

ASME `LB,min` and minimum overall length are reported as conditional class boundaries. A class `LB,min` below a geometric bound means the class minimum does not demonstrate the needed body length; an actual part could have a longer body. `LG,max` is kept as a gage-coordinate comparison. It is not the first-full-thread coordinate and does not establish nut engagement. A nominal class length is not a purchase length or delivered shank measurement.

## Family summary

| Family | Axes | Member variants | Minimum `LB` (frozen intervals) (mm) | `LB` with max-head-washer sensitivity (mm) | Largest per-member quarter allowance (mm) | Maximum physical tip target (mm) | Missing profile evidence |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| `candidate_ordinary_48` | 48 | 40 axes: 88.9 → 38.1 mm head to nut; 8 axes: 38.1 → 88.9 mm head to nut | 119.507 | 119.507 | 22.225 | 140.614 | unresolved for every axis |
| `candidate_side_16` | 16 | 16 axes: 88.9 → 88.9 mm head to nut | 157.607 | 157.607 | 22.225 | 191.414 | unresolved for every axis |
| `candidate_outer_post_4` | 4 | 4 axes: 38.1 → 38.1 mm head to nut | 68.326 | 68.707 | 9.525 | 89.814 | unresolved for every axis |
| `candidate_center_post_4` | 4 | 4 axes: 88.9 → 38.1 mm head to nut | 119.126 | 119.507 | 22.225 | 140.614 | unresolved for every axis |
| `candidate_center_principal_4` | 4 | 4 axes: 83.9 → 38.1 mm head to nut | 114.126 | 114.507 | 20.975 | 135.614 | unresolved for every axis |
| `candidate_center_post_header_4` | 4 | 4 axes: 38.1 → 128.9 mm head to nut | 136.426 | 136.807 | 32.225 | 180.614 | unresolved for every axis |
| `candidate_center_principal_header_4` | 4 | 4 axes: 134.7 → 38.1 mm head to nut | 164.926 | 165.307 | 33.675 | 186.414 | unresolved for every axis |
| `candidate_knee_inner_header_4` | 4 | 2 axes: 38.1 → 139.0 mm head to nut; 2 axes: 139.0 → 38.1 mm head to nut | 169.226 | 169.607 | 34.750 | 190.714 | unresolved for every axis |
| `candidate_knee_side_4` | 4 | 4 axes: 38.1 → 88.9 → 88.9 mm head to nut | 195.326 | 195.707 | 22.225 | 229.514 | unresolved for every axis |

Family variants retain each member's relative interval, maximum threaded-bearing length, exact receiver IDs, and `LB` requirement in `requirements.json`. This is important for the four knee inner-header axes: the `_1` and `_2` receivers have different far-member lengths even though their total grip and hardware class screen match.

## Left outer-corner priority axes

These six exact IDs are the requested corner priorities. Values are geometry-derived from their frozen receiver records; mirrored/right-side peers are also present in the JSON.

| Axis | Receiver IDs head to nut | Per-member `[a,b]` underhead intervals (mm) | Required `LB` (mm) | Tip target (mm) |
| --- | --- | --- | ---: | ---: |
| `knee_outer_left_post_1` | knee_outer_left_spine, base_post_outer_left | knee_outer_left_spine [1.651, 39.751]; base_post_outer_left [39.751, 77.851] | 68.326 | 89.814 |
| `knee_outer_left_post_2` | knee_outer_left_spine, base_post_outer_left | knee_outer_left_spine [1.651, 39.751]; base_post_outer_left [39.751, 77.851] | 68.326 | 89.814 |
| `knee_outer_left_side_1` | knee_outer_left_spine, base_side_left, knee_outer_left_inner_frame_block | knee_outer_left_spine [1.651, 39.751]; base_side_left [39.751, 128.651]; knee_outer_left_inner_frame_block [128.651, 217.551] | 195.326 | 229.514 |
| `knee_outer_left_side_2` | knee_outer_left_spine, base_side_left, knee_outer_left_inner_frame_block | knee_outer_left_spine [1.651, 39.751]; base_side_left [39.751, 128.651]; knee_outer_left_inner_frame_block [128.651, 217.551] | 195.326 | 229.514 |
| `knee_outer_left_inner_header_1` | base_header, knee_outer_left_inner_frame_block | base_header [1.651, 39.751]; knee_outer_left_inner_frame_block [39.751, 178.751] | 144.001 | 190.714 |
| `knee_outer_left_inner_header_2` | knee_outer_left_inner_frame_block, base_header | knee_outer_left_inner_frame_block [1.651, 140.651]; base_header [140.651, 178.751] | 169.226 | 190.714 |

## Length-class comparisons and open conditions

`requirements.json` reports, by family and length option, the source-class minimum overall length versus the physical tip target and modeled CAD endpoint, `LB,min` versus the per-member screen, and `LG,max` versus the earliest nut bearing plane. A negative comparison records a permissive class boundary that does not meet the screen. It is not a product failure finding, because the actual SKU and delivered dimensions are unknown.

No listed source pins a candidate bolt's first full-form thread, last full-form thread, last scratch, transition/runout, or point at an actual axis. The matched nut's active internal-thread interval and chamfers are also unknown. Thus the sufficient profile envelope remains unproven for all 92 axes, regardless of length-class arithmetic.

The 12 retained starting stacks are referenced separately from the 92 current axes by identity and modeled quantity in `requirements.json`. This packet does not requalify those stacks or transfer their prior resistance results.

Source documents include the [current grip screen](../../current-grip-screen.md), [hardware schedule](../../current-hardware-schedule.md), [bolt thread-boundary screen](../../current-bolt-thread-boundary-screen-2026-09-27.md), [ASME dimension correction](../../bolt-dimension-source-correction.md), [thread source research](../../current-bolt-thread-alternative-spec-research-2026-09-27.md), [quarter-thread discussion](../../current-center-sandwich-hardware-options.md), and [physical tip screen](../../current-ordinary-hardware-spacer-option.md).
