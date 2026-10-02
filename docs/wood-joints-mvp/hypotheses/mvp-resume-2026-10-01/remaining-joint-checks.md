# Remaining bolted joints: six nominal-gap same-state screen

## Current all-two-receiver clearance source

The new screen consumes the six saved nominal states from
`two-receiver-frame-attempt03/`, with modeled clearances on all 88 independent
candidate bolts. Finite fixed-force seating is certified for each state;
strict tangent stability and a unique pose are not transferred. The four
continuous candidate bolts and twelve retained bolts remain at zero clearance.

Current output: `remaining-joint-screen-attempt04/all-two-receiver-92ksi/`.
It contains 80 candidate and 12 retained axes, 576 signed plane states and
1104 outer-seat states. The eligible individual comparison peaks at
**0.952117** for all three Fyb scenarios: `rail_front_bolt_left_2`, A12-forward,
**1041.963 N** shear and simultaneous **190.904 N** tie, mode II. No eligible
individual reference exceeds one. These are component comparisons; end-grain,
continuous bolts, partial washer support and complete-joint duties retain
their separate methods and limits.

Current `screen.json` SHA-256:
`5b85139b2acaefd8ff74df916229766438c0caf3bc9c3a1a7b5080f8f393033a`.
The complete source/response binding and bounded-seating distinction remain
in its JSON. Existing source snapshots and older result packets are preserved.

## Preserved six-joint source

The current [all-outer frame](bottom-corner-checks.md) includes both top/bottom
outer corners and both left outer service cleats. Fresh results are in
`remaining-joint-screen-attempt03/grade5-92ksi/`, with the same 80 candidate /
12 retained axes, 576 signed plane states and 1104 outer-seat states. All
eligible individual references are below one at 45/92/106 ksi; these are
component results, not complete joint acceptance.

The 45 ksi peak is **0.755543**, retained `lumber_leg_bolt_left_2` in A12-rear:
1745.986 N shear with simultaneous +461.476 N tie. The 92/106 ksi peak is
**0.700353**, retained `rail_front_bolt_left_2` in A12-left: 784.874 N shear
and simultaneous +78.389 N tie. These states and diameters are distinct.
The bottom-left joint no longer governs after its clearance is included;
its separate [finished component calculation](bottom-corner-checks.md) peaks
at 0.2920 with declared group/end adjustments under 92 ksi.

The original single-shear classifier still emits separate end-grain and
three-receiver rows. Their completed bounded calculations are now in
[end-grain-route.md](end-grain-route.md) and
[three-member-checks.md](three-member-checks.md): the twelve end-grain axes
have a supported NDS individual reference route, while the four continuous
knee bolts use an explicitly conditional asymmetric utilization-sum screen.
Remaining complete detailing, supported axial transfer and group checks are
recorded there. The partial washer seat stays explicit, without full-annulus
capacity transfer.

Current comparison/response hashes are listed in the bottom-corner worksheet.
`screen.json` SHA-256: c3615182a2e0fa8eb8d1da96648b01c27531ab9f710ab1498961ec1b46b10de8.
Earlier outputs and their tables below retain their earlier four-joint scope.

## Preserved four-joint detailed screen

The following preserved screen uses the six saved nominal-gap states in
[top-and-service-frame-attempt02](top-and-service-frame-attempt02/), together
with the unchanged frozen corrected frame model, operators and row identities.
The source now includes circular clearance at both top outer corners and
both upper/lower left outer service cleats. This packet supplies component
references for 80 candidate bolts and twelve retained bolts, not complete
joint acceptance, hardware selection, criterion dispositions or physical release.
The parent owns frame, top-corner and service-joint conclusions.

The current results are
[screen.json](remaining-joint-screen-attempt02/grade5-92ksi/screen.json),
[bolt-states.csv](remaining-joint-screen-attempt02/grade5-92ksi/bolt-states.csv),
[washer-reference-states.csv](remaining-joint-screen-attempt02/grade5-92ksi/washer-reference-states.csv)
and [source-pins.json](remaining-joint-screen-attempt02/grade5-92ksi/source-pins.json).
The maintained producer is [remaining_joint_screen.py](remaining_joint_screen.py).
The current child output adds the requested 92 ksi reference without changing
any saved force, frame input, geometry, exclusion or previous result binding.
All numerical outputs stay ignored. Earlier two-corner results remain intact
in [attempt01's corrected output](remaining-joint-screen-attempt01/partial-support-corrected/),
with their original producer and document snapshots.

### Useful results and next joint work

The governing eligible individual-bolt lateral comparison is
`bottom_outer/clip_horizontal_bottom_left_1/side_1` in **a1-rear**:
682.379935 N shear, simultaneous +207.851824 N outer tie,
and mode IV references of 604.855502 N at 45 ksi,
864.847019 N at the conditional Grade 5 92 ksi scenario, and
928.321292 N at 106 ksi. Ratios are **1.128170 / 0.789018 / 0.735069**.
This remains the only eligible axis exceeding one at 45 ksi; none exceeds
one at 92 or 106 ksi. These references are not adopted joint resistances. Group, finished detailing and complete transfer remain open. The
next component priority is the bottom-left outer side/rail joint at these
saved states; no bolt size, product or timber change is selected here.

The retained front pairs are next among quantified lateral references:
`rail_front_bolt_left_2` reaches 0.701963 in a12-left;
`rail_front_bolt_right_2` reaches 0.668461 in k12-right.
Mode II governs at all three Fyb hypotheses for these front states, so their
45/92/106 ksi references coincide. Knee post pairs reach 0.597459
left and 0.580532 right in their respective lateral cases at 106 ksi.
Their finished detailing, nonuniform group actions, axial transfer and
washer resistance remain open. Retained upper bolts carry the largest
individual lateral forces (1745.24 N left and 1723.06 N right).
Their largest outer ties occur in different states; those maxima must not be
combined into an interaction.

Continuous knee side bolts retain a separate method: largest individual
plane demands are 684.349647 N at left `side_1/plane-37` in a12-left
and 671.809991 N at right `side_1/plane-45` in k12-right.
They are not added across planes or compared with a two-receiver reference.
Their next calculation needs compatible bolt bending, bearing and complete
joint transfer with both signed planes retained.

Center header end-grain interfaces also retain separate lateral-method gaps.
The highest eligible ideal washer pressure comparison is
`center_post_header_left_1` in a12-forward:
+357.488519 N tension, 1.673417 MPa on the declared full
annulus and 0.388334 against the perpendicular receiver's base Fc.
The other outer receiver uses a separate parallel-grain base reference.
This does not qualify the end-grain lateral joint or washer metal transfer.

The `center_principal_right_2` nut seat remains an explicit partial-support
exception. Its full-annulus pressure and ratio are **null**. The parent owns
the separate supported-bearing option and receives the current forces below;
this packet develops no footprint option.

| Saved clearance scenario | Governing bottom-left side shear, N | V/Z at 45 / 106 ksi |
| --- | ---: | ---: |
| Two top corners, preserved attempt01 | 671.840143 | 1.110832 / 0.723772 |
| Two top corners plus two left outer service cleats, current attempt02 | 682.379935 | 1.128170 / 0.735069 |

### Coverage and exclusions

| Item | Coverage |
| --- | ---: |
| Saved nominal-gap cases | 6 |
| Owned candidate / retained physical bolts | 80 / 12 |
| Owned lateral interfaces / simultaneous plane states | 96 / 576 |
| Outer-seat states, including explicit null references | 1104 |
| Two-bolt duties | 46 |
| Candidate transverse two-receiver lateral-reference states | 384 (64 axes) |
| Retained two-receiver lateral-reference states | 72 (12 axes) |
| End-grain method states | 72 (12 axes) |
| Three-receiver method states | 48 (four axes, two planes each) |
| Partial-support nut-seat exception states | 6 |

All six cases are a12-rear, a12-forward, a12-left, k12-right, k12-rear
and a1-rear. The source comparison records twelve zero/gap states passing
its conditional coupled frame laws with dynamic floor bearing masks. This
producer reads only `case_id + '_gap_raw_force_n'`, with `gap_scale=1.0`;
it does not solve or independently recheck frame equilibrium.

These four top outer corner prefixes are excluded before any bolt arithmetic:

- `top_outer/clip_single_top_left_1/rail_`
- `top_outer/clip_single_top_left_1/side_`
- `top_outer/clip_single_top_right_2/rail_`
- `top_outer/clip_single_top_right_2/side_`

Those eight axes match the corrected model's proposed corner axes. The four
axes whose receivers include `left_service_outer_lower_cleat` are also
excluded: the lower-left service worker owns that joint. The remaining
lower-left inner service cleat is a distinct included duty. No excluded
joint's calculations or acceptance claims are duplicated.

### Signed actions, material and hardware assumptions

The reused [bolt demand method](bolt_demands.py) identifies a lateral plane
by two scalar rows and an outer tie by its own row. Here, the saved vectors
have 1888 raw rows; original simple-frame CSV demands are not reused.
For each plane, `q = direction dot (u_second - u_first)`. A positive scalar
force applies `+f * direction` to the first body and its negative to the
second body. Both signed scalar components, their directions, signed global
shear XYZ, member identities, application point and raw row numbers remain
in the CSV. A positive outer tie means tension; its signed raw value is
preserved, and `max(0,T)` is used only for eligible ideal pressure references.

For the governing bottom-left side bolt, the two signed scalar components
are -474.161005 N and -490.727742 N. The force on `base_side_left` is
approximately `(0, +490.727742, -474.161005)` N; the cleat receives its
negative. The +207.851824 N tie belongs to this same case and axis. It spans
outer receivers and is not automatically a local shear-plane axial stress.
No co-located bolt bending or steel interaction is inferred.

Candidate individual lateral arithmetic reuses
[lateral_reference.py](lateral_reference.py) and `fea/dowel_yield.py`:
6.35 mm full smooth-body diameter, two contiguous raw receiving lengths,
zero intermember gap, DF-L specific gravity 0.50, Fe parallel/perpendicular
5600/4450 psi with direction-specific Hankinson bearing, and the existing
six-mode reduction terms. Remaining joints retain the source frame's
zero-clearance lateral assumption; explicit nominal circular clearance now
applies at both top corners and both left outer service cleats. Every reference retains
its own signed-force-derived grain angles and governing mode.

The 12 retained bolts reuse only the frozen geometry register from the
[retained resistance packet](../retained-frame-bolt-current-resistance-basis-2026-10-01/README.md),
its pure `lateral_references` function and the existing diameter-dependent
NDS helper. Their receiving lengths remain 88.9/88.9 mm for the 1/2-inch
upper stacks, 38.1/38.1 mm for 3/8-inch front stacks, and 38.1/50.8 mm
for 3/8-inch rear stacks. Receiver membership, grip, interface point,
original finished STEP identity and modeled grain are checked against the
consumed frame inputs. No old native demands or old acceptance are reused.
These unchanged station references do not establish complete finished
geometry or support on the corrected side members.

The added **Fyb=92 ksi** scenario reuses the same equations and material band:
the pinned fastener inputs specify a 92 ksi minimum machine-test tensile yield
for conditional SAE J429 Grade 5, 1/4 through 1 inch. That value is used as a
declared Fyb scenario under the same conditional ASTM F606 basis as the parent's
top-corner work. Exact product conformity and the applicable Fyb test/evaluation
basis remain unresolved. It does not convert the catalog tensile minimum into
a guaranteed bending capacity or complete joint acceptance. All 456 eligible
candidate/retained states now have the additional individual reference; the
end-grain and continuous three-receiver states retain null lateral references.

Fyb=45 ksi and 106 ksi remain **unadopted hypotheses**. The 45 ksi value is
not a quarter-inch table entitlement; 106 ksi is the existing Grade 5 estimate,
not an exact-product minimum or test-derived Fyb. References precede Cg,
Cdelta and service adjustments. Nominal size and modeled receiving length
do not establish delivered smooth shank, transition position, threads,
nut engagement or a selected product. No preload or friction is credited.

The wood-pressure arithmetic reuses
[top_corner_local.py](top_corner_local.py)'s units and normalization helpers,
the existing material specification and the saved catalog annulus. Its
conditional dry, normal-duration DF-L No.2 base references are Fc perpendicular
625 psi (4.309223 MPa) and Fc parallel 1350 psi (9.307922 MPa), with no factor
increase. The parallel comparison is a base-property reference, not an
adopted local bearing resistance. Wood species, grade, moisture and finished
condition remain unobserved assumptions.

For eligible quarter-inch seats, the declared centered full annulus has
minimum OD 0.727 in, maximum ID 0.327 in and area 213.627873 mm².
Pressure is `max(0,T)/area`. The screen reports each outer receiver's grain
route separately; it creates no middle washer on a three-receiver bolt.
Full support, uniform pressure and the catalog dimensional scenario are
assumptions. A true `full_annulus_reference_applicable` field means only that
this ideal reference has no declared exclusion here; it is not a new geometry
pass or inspection. Actual supported pressures and all washer metal capacities
remain null. Retained washer OD/ID/support are unbound in the consumed
register, so their pressure and ratio fields remain null; quarter-inch washer
references are not transferred to them.

### Partial nut-seat exception and parent force handoff

The reused [remaining seat geometry evidence](../remaining-candidate-washer-seats-2026-10-01/README.md)
records 107 of 108 remaining seats passing its declared geometry screen.
The exception lies beside the retained **38.1 mm F1-G1 service passage**.
Its edge is 6.5598763474 mm from the shaft center. Centered minimum-area
annulus support is 90.6001120577%; centered outer-envelope support is
90.0597697729%; swept containment is 86.7210768952%. Those are different
geometric scenarios. Neither supports a full-annulus wood-pressure claim.

The affected nut-seat records and all six bolt-plane records for
`center_principal_right_2` omit full-annulus pressure and ratio. The opposite
cleat seat may retain its own conditional ideal reference; that does not
resolve the nut-side exception. No scaled supported-area capacity or
uniform pressure on the remaining crescent is invented. The center-principal
right duty retains `PARTIAL_SEAT` regardless of another bolt's reference.
Its axial ties are direct values from raw row 1535 of the same saved nominal-gap
force vectors:

| Case | Signed axial tie, N |
| --- | ---: |
| a12-rear | +59.223495205 |
| a12-forward | +75.750872807 |
| a12-left | +53.129655094 |
| k12-right | +76.463377862 |
| k12-rear | +82.628086746 |
| a1-rear | +6.474296359 |

### Six-case component table

The current [six-case CSV](remaining-joint-screen-attempt02/grade5-92ksi/six-case-component-summary.csv)
and [binding receipt](remaining-joint-screen-attempt02/grade5-92ksi/six-case-component-summary.json)
select existing same-state component records. Shear/tie pairs below belong
to the governing **92 ksi** axis in each case. Other scenario and ideal-pressure
maxima retain their own axes and must not be combined. The receipt preserves
the full signed raw records and the unchanged frame comparison/response hashes.
Partial nut-seat pressure and ratio remain null; its signed tension is shown.

| Case | Peak V/Z, 45 ksi (axis) | Peak V/Z, 92 ksi (axis) | Peak V/Z, 106 ksi (axis) | Same-state 92 ksi shear / tie, N | Peak ideal wood ratio (axis) | center_principal_right_2 tie, N |
| --- | --- | --- | --- | --- | --- | ---: |
| a12-rear | 0.755137 (`lumber_leg_bolt_left_2`) | 0.555907 (`lumber_leg_bolt_left_2`) | 0.539439 (`lumber_leg_bolt_left_2`) | 1745.236690 / +471.552307 | 0.264005 (`top_center/clip_split_top_center_left/rail_2`) | +59.223495 |
| a12-forward | 0.673025 (`knee_outer_left_post_2`) | 0.648808 (`rail_front_bolt_left_2`) | 0.648808 (`rail_front_bolt_left_2`) | 727.199503 / +85.638359 | 0.388334 (`center_post_header_left_1`) | +75.750873 |
| a12-left | 0.750010 (`knee_outer_left_post_2`) | 0.701963 (`rail_front_bolt_left_2`) | 0.701963 (`rail_front_bolt_left_2`) | 786.682818 / +78.942979 | 0.300411 (`center_post_header_left_1`) | +53.129655 |
| k12-right | 0.728790 (`knee_outer_right_post_2`) | 0.668461 (`rail_front_bolt_right_2`) | 0.668461 (`rail_front_bolt_right_2`) | 748.150675 / +76.853575 | 0.303298 (`center_post_header_right_1`) | +76.463378 |
| k12-rear | 0.744542 (`lumber_leg_bolt_right_2`) | 0.547860 (`lumber_leg_bolt_right_2`) | 0.531648 (`lumber_leg_bolt_right_2`) | 1723.055386 / +638.780076 | 0.311326 (`top_center/clip_split_top_center_right/rail_2`) | +82.628087 |
| a1-rear | 1.128170 (`bottom_outer/clip_horizontal_bottom_left_1/side_1`) | 0.789018 (`bottom_outer/clip_horizontal_bottom_left_1/side_1`) | 0.735069 (`bottom_outer/clip_horizontal_bottom_left_1/side_1`) | 682.379935 / +207.851824 | 0.266183 (`bottom_outer/clip_horizontal_bottom_left_1/side_2`) | +6.474296 |

### Per-duty governing cases

Each prefix denotes the two axes obtained by appending `_1` and `_2`.
`case:#n` identifies the physical axis within that prefix. Each column is its
own maximum. The three Fyb maxima are separately located below; combine only
the explicitly retained same-state records. Ideal wood ratios are conditional
base-property references, not adequacy dispositions. A dash means an excluded
reference or only the common gaps, as applicable.

| Duty prefix | Max shear N (case:#) | Max V/Z, 45 ksi (case:#) | Max V/Z, 92 ksi (case:#) | Max V/Z, 106 ksi (case:#) | Max tie N (case:#) | Max ideal wood ratio (case:#) | Additional gap |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `bottom_center/clip_horizontal_bottom_left_2/principal` | 177.06 (a1-rear:#1) | 0.288 (a1-rear:#1) | 0.210 (a1-rear:#1) | 0.204 (a1-rear:#1) | +78.07 (a1-rear:#2) | 0.085 (a1-rear:#2) | — |
| `bottom_center/clip_horizontal_bottom_left_2/rail` | 51.78 (a1-rear:#1) | 0.082 (a1-rear:#1) | 0.057 (a1-rear:#1) | 0.054 (a1-rear:#1) | +98.67 (a1-rear:#2) | 0.107 (a1-rear:#2) | — |
| `bottom_center/clip_horizontal_bottom_right_1/principal` | 51.87 (a12-rear:#1) | 0.084 (a12-rear:#1) | 0.062 (a12-rear:#1) | 0.060 (a12-rear:#1) | +33.24 (a12-rear:#2) | 0.036 (a12-rear:#2) | — |
| `bottom_center/clip_horizontal_bottom_right_1/rail` | 32.14 (a12-rear:#2) | 0.054 (a12-rear:#2) | 0.037 (a12-rear:#2) | 0.035 (a12-rear:#2) | +45.00 (a12-left:#2) | 0.049 (a12-left:#2) | — |
| `bottom_outer/clip_horizontal_bottom_left_1/rail` | 337.78 (a1-rear:#2) | 0.512 (a1-rear:#2) | 0.361 (a1-rear:#2) | 0.351 (a1-rear:#2) | +237.40 (a1-rear:#1) | 0.258 (a1-rear:#1) | — |
| `bottom_outer/clip_horizontal_bottom_left_1/side` | 682.38 (a1-rear:#1) | 1.128 (a1-rear:#1) | 0.789 (a1-rear:#1) | 0.735 (a1-rear:#1) | +245.04 (a1-rear:#2) | 0.266 (a1-rear:#2) | — |
| `bottom_outer/clip_horizontal_bottom_right_2/rail` | 41.45 (k12-rear:#1) | 0.068 (k12-rear:#1) | 0.047 (k12-rear:#1) | 0.044 (k12-rear:#1) | +52.29 (k12-rear:#1) | 0.057 (k12-rear:#1) | — |
| `bottom_outer/clip_horizontal_bottom_right_2/side` | 53.80 (k12-right:#2) | 0.088 (k12-right:#2) | 0.061 (k12-right:#2) | 0.057 (k12-right:#2) | +22.72 (k12-right:#1) | 0.025 (k12-right:#1) | — |
| `center_post_header_left` | 136.68 (a12-forward:#1) | — | — | — | +357.49 (a12-forward:#1) | 0.388 (a12-forward:#1) | END_GRAIN |
| `center_post_header_right` | 117.64 (a12-forward:#1) | — | — | — | +279.21 (k12-right:#1) | 0.303 (k12-right:#1) | END_GRAIN |
| `center_post_left` | 134.57 (a12-forward:#2) | 0.199 (a12-forward:#2) | 0.139 (a12-forward:#2) | 0.135 (a12-forward:#2) | +109.18 (a12-forward:#1) | 0.119 (a12-forward:#1) | — |
| `center_post_right` | 131.68 (a12-forward:#2) | 0.186 (a12-forward:#2) | 0.130 (a12-forward:#2) | 0.124 (a12-forward:#2) | +93.95 (a12-forward:#1) | 0.102 (a12-forward:#1) | — |
| `center_principal_header_left` | 149.22 (k12-rear:#2) | — | — | — | +306.89 (a12-forward:#1) | 0.333 (a12-forward:#1) | END_GRAIN |
| `center_principal_header_right` | 126.81 (k12-right:#2) | — | — | — | +278.60 (a12-forward:#1) | 0.303 (a12-forward:#1) | END_GRAIN |
| `center_principal_left` | 177.80 (a12-forward:#1) | 0.256 (a12-forward:#1) | 0.179 (a12-forward:#1) | 0.174 (a12-forward:#1) | +82.56 (a12-rear:#2) | 0.090 (a12-rear:#2) | — |
| `center_principal_right` | 146.01 (a12-forward:#1) | 0.214 (a12-left:#1) | 0.152 (a12-left:#1) | 0.147 (a12-left:#1) | +82.63 (k12-rear:#2) | 0.031 (a12-left:#1) | PARTIAL_SEAT |
| `knee_outer_left_inner_header` | 112.40 (a12-left:#1) | — | — | — | +123.71 (a12-rear:#1) | 0.134 (a12-rear:#1) | END_GRAIN |
| `knee_outer_left_post` | 486.46 (a12-left:#2) | 0.750 (a12-left:#2) | 0.597 (a12-left:#2) | 0.597 (a12-left:#2) | +171.57 (a12-left:#1) | 0.186 (a12-left:#1) | — |
| `knee_outer_left_side` | 684.35 (a12-left:#1) | — | — | — | +191.97 (a12-left:#1) | 0.209 (a12-left:#1) | MULTI_RECEIVER |
| `knee_outer_right_inner_header` | 114.52 (k12-right:#1) | — | — | — | +118.00 (k12-rear:#1) | 0.128 (k12-rear:#1) | END_GRAIN |
| `knee_outer_right_post` | 472.74 (k12-right:#2) | 0.729 (k12-right:#2) | 0.581 (k12-right:#2) | 0.581 (k12-right:#2) | +200.55 (k12-right:#1) | 0.218 (k12-right:#1) | — |
| `knee_outer_right_side` | 671.81 (k12-right:#1) | — | — | — | +174.10 (k12-right:#1) | 0.189 (k12-right:#1) | MULTI_RECEIVER |
| `left_service/left_service_mirrored_inner_outer_hypothesis/clip_horizontal_lower_left_2/lower_principal` | 44.75 (a1-rear:#1) | 0.072 (a1-rear:#1) | 0.053 (a1-rear:#1) | 0.051 (a1-rear:#1) | +43.61 (k12-right:#1) | 0.047 (k12-right:#1) | — |
| `left_service/left_service_mirrored_inner_outer_hypothesis/clip_horizontal_lower_left_2/lower_rail` | 34.38 (a1-rear:#2) | 0.052 (a1-rear:#2) | 0.036 (a1-rear:#2) | 0.035 (a1-rear:#2) | +21.83 (a12-forward:#1) | 0.024 (a12-forward:#1) | — |
| `left_service/left_service_mirrored_inner_outer_hypothesis/clip_horizontal_upper_left_1/upper_rail` | 0.00 (a1-rear:#2) | 0.000 (a1-rear:#2) | 0.000 (a1-rear:#2) | 0.000 (a1-rear:#2) | +11.13 (k12-right:#2) | 0.012 (k12-right:#2) | — |
| `left_service/left_service_mirrored_inner_outer_hypothesis/clip_horizontal_upper_left_1/upper_side` | 4.92 (a12-rear:#1) | 0.008 (k12-right:#2) | 0.006 (k12-right:#2) | 0.005 (k12-right:#2) | +15.76 (k12-right:#1) | 0.017 (k12-right:#1) | — |
| `left_service/left_service_mirrored_inner_outer_hypothesis/clip_horizontal_upper_left_2/upper_principal` | 46.19 (k12-right:#1) | 0.074 (k12-right:#1) | 0.054 (k12-right:#1) | 0.052 (k12-right:#1) | +23.87 (k12-right:#2) | 0.026 (k12-right:#2) | — |
| `left_service/left_service_mirrored_inner_outer_hypothesis/clip_horizontal_upper_left_2/upper_rail` | 23.18 (a12-rear:#1) | 0.039 (a12-rear:#1) | 0.027 (a12-rear:#1) | 0.025 (a12-rear:#1) | +33.50 (k12-rear:#2) | 0.036 (k12-rear:#2) | — |
| `lumber_leg_bolt_left` | 1745.24 (a12-rear:#2) | 0.755 (a12-rear:#2) | 0.556 (a12-rear:#2) | 0.539 (a12-rear:#2) | +726.30 (a12-left:#2) | — | RETAINED_WASHER |
| `lumber_leg_bolt_right` | 1723.06 (k12-rear:#2) | 0.745 (k12-rear:#2) | 0.548 (k12-rear:#2) | 0.532 (k12-rear:#2) | +880.15 (k12-right:#2) | — | RETAINED_WASHER |
| `rail_front_bolt_left` | 786.68 (a12-left:#2) | 0.702 (a12-left:#2) | 0.702 (a12-left:#2) | 0.702 (a12-left:#2) | +99.74 (k12-rear:#1) | — | RETAINED_WASHER |
| `rail_front_bolt_right` | 748.15 (k12-right:#2) | 0.668 (k12-right:#2) | 0.668 (k12-right:#2) | 0.668 (k12-right:#2) | +100.90 (a12-left:#2) | — | RETAINED_WASHER |
| `rail_rear_bolt_left` | 435.92 (a12-left:#1) | 0.366 (a12-left:#1) | 0.366 (a12-left:#1) | 0.366 (a12-left:#1) | +63.73 (a1-rear:#1) | — | RETAINED_WASHER |
| `rail_rear_bolt_right` | 419.09 (k12-right:#1) | 0.353 (k12-right:#1) | 0.353 (k12-right:#1) | 0.353 (k12-right:#1) | +31.58 (k12-rear:#2) | — | RETAINED_WASHER |
| `top_center/clip_split_top_center_left/principal` | 141.26 (a12-rear:#1) | 0.216 (a12-rear:#1) | 0.151 (a12-rear:#1) | 0.145 (a12-rear:#1) | +150.58 (a12-rear:#1) | 0.164 (a12-rear:#1) | — |
| `top_center/clip_split_top_center_left/rail` | 185.37 (a12-rear:#2) | 0.299 (a12-rear:#2) | 0.209 (a12-rear:#2) | 0.195 (a12-rear:#2) | +243.04 (a12-rear:#2) | 0.264 (a12-rear:#2) | — |
| `top_center/clip_split_top_center_right/principal` | 178.47 (k12-rear:#1) | 0.273 (k12-rear:#1) | 0.191 (k12-rear:#1) | 0.183 (k12-rear:#1) | +201.07 (k12-rear:#1) | 0.218 (k12-rear:#1) | — |
| `top_center/clip_split_top_center_right/rail` | 192.85 (k12-rear:#2) | 0.312 (k12-rear:#2) | 0.218 (k12-rear:#2) | 0.203 (k12-rear:#2) | +286.60 (k12-rear:#2) | 0.311 (k12-rear:#2) | — |
| `wj04_g7/upper_g7_clearance_n86p9_reversed_rail_hypothesis/lower_principal` | 34.54 (a12-rear:#2) | 0.055 (a12-rear:#2) | 0.040 (a12-rear:#2) | 0.039 (a12-rear:#2) | +40.80 (a12-left:#1) | 0.044 (a12-left:#1) | — |
| `wj04_g7/upper_g7_clearance_n86p9_reversed_rail_hypothesis/lower_rail` | 24.80 (a12-rear:#2) | 0.040 (a12-rear:#2) | 0.028 (a12-rear:#2) | 0.026 (a12-rear:#2) | +20.58 (a12-forward:#1) | 0.022 (a12-forward:#1) | — |
| `wj04_g7/upper_g7_clearance_n86p9_reversed_rail_hypothesis/upper_principal` | 33.82 (a12-left:#1) | 0.053 (a12-left:#1) | 0.038 (a12-left:#1) | 0.037 (a12-left:#1) | +24.09 (a12-rear:#2) | 0.026 (a12-rear:#2) | — |
| `wj04_g7/upper_g7_clearance_n86p9_reversed_rail_hypothesis/upper_rail` | 23.21 (a12-left:#1) | 0.038 (a12-left:#1) | 0.027 (a12-left:#1) | 0.025 (a12-left:#1) | +39.42 (a12-rear:#2) | 0.043 (a12-rear:#2) | — |
| `wj06_outer_pair/right_outer_full_4x4_paired_rail_hypothesis/lower_rail` | 94.85 (a12-rear:#2) | 0.153 (a12-rear:#2) | 0.107 (a12-rear:#2) | 0.100 (a12-rear:#2) | +45.99 (a12-rear:#1) | 0.050 (a12-rear:#1) | — |
| `wj06_outer_pair/right_outer_full_4x4_paired_rail_hypothesis/lower_side` | 93.10 (k12-right:#1) | 0.154 (k12-right:#1) | 0.108 (k12-right:#1) | 0.101 (k12-right:#1) | +152.57 (a12-rear:#1) | 0.166 (a12-rear:#1) | — |
| `wj06_outer_pair/right_outer_full_4x4_paired_rail_hypothesis/upper_rail` | 106.27 (a12-rear:#2) | 0.173 (a12-rear:#2) | 0.121 (a12-rear:#2) | 0.112 (a12-rear:#2) | +51.89 (k12-right:#1) | 0.056 (k12-right:#1) | — |
| `wj06_outer_pair/right_outer_full_4x4_paired_rail_hypothesis/upper_side` | 42.94 (a1-rear:#1) | 0.069 (a1-rear:#1) | 0.048 (a1-rear:#1) | 0.045 (a1-rear:#1) | +153.34 (a12-rear:#1) | 0.167 (a12-rear:#1) | — |

### Exact gaps and disposition

Every included duty retains `GROUP_GEOMETRY`, `HARDWARE_AXIAL` and
`WASHER_TRANSFER`; no row is a complete accepted joint. Additional gaps
remain attached to their exact duty prefixes in the table and JSON.

| Gap | Required input or next calculation |
| --- | --- |
| `GROUP_GEOMETRY` | Bind finished loaded edges/ends, spacing and Cdelta; resolve the oblique nonuniform bolt group/Cg, splitting, tear-out, member sections and complete contact/couple transfer at these same states. |
| `HARDWARE_AXIAL` | Specify applicable Fyb/product basis and body/thread transition through each receiver, nut engagement, bolt bending and coupled axial/lateral resistance; no hardware is selected by this screen. |
| `WASHER_TRANSFER` | Resolve actual supported footprint, eccentric contact/wood pressure and washer/head/nut metal spreading or bending; ideal annulus pressure is not a complete axial-transfer check. |
| `END_GRAIN` | The bolt axis is parallel to one receiver's grain. The reused transverse single-shear helper does not establish an applicable end-grain lateral resistance or splitting/detailing treatment. |
| `MULTI_RECEIVER` | A continuous three-receiver bolt has two distinct lateral planes. Resolve compatible bolt bending, receiver bearing and axial/lateral interaction; do not sum plane magnitudes or apply a two-member reference. |
| `PARTIAL_SEAT` | center_principal_right_2 nut seat on base_principal_center_right overlaps the retained 38.1mm F1-G1 service passage. Centered outer-envelope support is 90.0597697729%, centered minimum-area support is 90.6001120577%, and swept containment is 86.7210768952%. Full-annulus pressure/ratios are inapplicable and omitted at this seat and in this bolt's plane rows. Keep signed demand for the parent's separate bearing-footprint work; supported contact/metal/wood transfer remains open. |
| `RETAINED_WASHER` | The consumed retained register has no bound OD/ID/support treatment for its 1/2- and 3/8-inch washer families. The quarter-inch annulus is inapplicable; pressures and ratios stay null. |

The saved frame still depends on the 66 unchanged Hillman axes with
unsupported parametric spring properties, the explicit no-slip floor
assumption, conditional gross member stiffness, omitted preload and the
recorded accessory distribution. None becomes qualified through this screen.
No screw resistance, stiffness or installation policy is transferred.
Geometry remains preserved, and the parent retains frame and top-corner work.

### Source bindings and execution

The producer rechecks 135 pinned files before and after saved-array arithmetic,
including all 122 source pins from the current clearance comparison. It binds
comparison/NPZ bytes, baseline input records and producer snapshots, helper
files, material/catalog inputs and the two existing read-only `/tmp` records.
The retained register's inherited native provenance is recorded without
re-running its old response or acceptance pipeline. No frame/native solve,
CAD operation, tests or review loop runs here. Ruff format and Ruff check pass.

| Consumed source | SHA-256 |
| --- | --- |
| `top-and-service-frame-attempt02/comparison.json` | `4aa32390c80f803faee4fceeb6460c05b665dd8e970beaef89b40985b0b9555b` |
| `top-and-service-frame-attempt02/response.npz` | `227b9381a6ff19286ba4b46c81bc5852bb3b536735ac5c74f727f6869a5f40d6` |
| `top-and-service-frame-attempt02/producer.py.snapshot` | `7417e4812fde42b6108994eca0f3afb8da56ded516793b887befdb1582c4a5b5` |
| `corner-frame-attempt01/model.json` | `d17dadd7c999e4a1634f53226cf63e131f547cd9cf5d46d87d75c935f2dc807e` |
| `corner-frame-attempt01/row-identities.json` | `bec1feb75be61b321220a047a652cc42f09c4c11d1d3c66377c4035bde4826d5` |
| `corner-frame-attempt01/operators.npz` | `f40bf53412afb400df23ff108e90bac66db3c493da26a19af5c05de329c165ad` |
| `corner-frame-attempt01/operator-assessment.json` | `54b48e3c1a027ac7660ec6e9ce0033d28f6be7af4f8939769a3ddb0f12e4fc81` |
| `corner-frame-attempt01/inputs.json` | `27b6431f88d86bb1f6b877e19177ae01c785b851a7edf80c6176674338b68510` |
| `docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/reduced-static-attempt01/model-inputs.json` | `178ab4f9352c8b1f11525ffc6680efa5733ba74cedd609874e9a1966624740f9` |
| `bolt_demands.py` | `b3b5d2676bfd7efc908e9411c1aeddd58b5483fc33dd206d263d99d8fb6ca479` |
| `lateral_reference.py` | `845409d1daf0214bbd41484f0a0a58867cd266bbc7f19060d9eef9d342657e94` |
| `top_corner_local.py` | `4b00bc312607be743ae73a7a34ee1ada0fe7a5d2ffd69d2d18902f3ea65dfd77` |
| `mini_moonboard/nds_2024_multi_member_bolt_yield.py` | `575d7de88d5f138412fef633ef946bccba884c1953b67e8d9211fc028d74ab89` |
| `/tmp/mini-moonboard-retained-frame-bolt-current-resistance-basis-2026-10-01.json` | `c3250f067c4590ee43f7ec7a5765d056d87e6ff5adb42837ed27710d9b4d4eb1` |
| `/tmp/mini-moonboard-remaining-seats-parent-2026-10-01.json` | `64853898bccf71df62119f0977f29aa612b323d436790b370b5616f7b3cb9fe3` |
| `remaining_joint_screen.py` | `74dac1076c2637b6598fc5b7780506f86dfacf945b6d1232104cbf7d6ce04897` |

Python 3.12.3, NumPy 2.5.2; existing environment and helpers only.
Current `screen.json` SHA-256:
`d2cdabdd3177b48b80669a35bda4cf7c7ee5f07f7ca323b56ef3d88456a7fe5e`.
Output CSV, pin-receipt and producer-snapshot hashes are recorded in that report.

The completed current invocation was:

```sh
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 .venv/bin/python -B docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/remaining_joint_screen.py --clearance docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/top-and-service-frame-attempt02 --output docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/remaining-joint-screen-attempt02/grade5-92ksi
.venv/bin/ruff check docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/remaining_joint_screen.py
```

`--clearance` accepts a saved directory or its `comparison.json`, binds its
response and producer, requires twelve passing zero/gap source states, and
checks that model/rows/operators still match the frozen baseline. It invokes
no frame physics. `--output` must name a fresh directory beneath an owned
`remaining-joint-screen-attempt*` path; existing output is refused. The parent
can replay into a new child of attempt02, for example
`--output docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/remaining-joint-screen-attempt02/parent-replay`.

Attempt02/grade5-92ksi is the active final screen. The preceding attempt02
45/106 ksi results, producer, six-case table and document snapshot remain intact. Attempt01's corrected results remain
preserved as the earlier two-corner sensitivity, with producer/document
snapshots. The first output at attempt01's root is also retained: it labeled
the partial-seat quotient counterfactual but did not suppress it; that output
is superseded. Use the corrected results, which omit that reference.
`/tmp` inputs and all frozen frame/geometry files remain unchanged. No raw
record is pruned or archived. This worker changes only the two requested
maintained files and ignored attempt outputs, with no staging, commits or
pushes. The parent owns shared summary updates and all commits.
