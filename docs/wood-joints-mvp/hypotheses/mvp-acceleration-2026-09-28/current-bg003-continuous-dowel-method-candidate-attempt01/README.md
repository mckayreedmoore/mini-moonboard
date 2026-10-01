# BG003 continuous-dowel method candidate — attempt01

**Finding:** the reviewed NDS/TR12 helpers do not calculate a complete
resistance for BG003's current unequal, non-collinear plane actions. One
bounded next method is a **single continuous dowel beam on nonlinear timber
bearing foundations**, solved per physical bolt with two transverse bending
directions and the two middle-member bearing intervals active together. This
is a research-method candidate, not a current NDS capacity, design pass, or
joint acceptance. Its two-dimensional foundation model has a primary-source
precedent; the required biaxial extension and the BG003 material laws do not
yet have a validated method here.

## Why the reviewed shortcuts stop

The maintained NDS-2024 helper implements the standard's individual-bolt
yield equations and explicitly uses equal side actions for its three-member
double-shear route. The local double-shear helper likewise requires
established symmetric side actions and matching side load-to-grain angles.
The TR12 helper is for two-member, one-plane single shear. Those routes do not
resolve the two simultaneous middle-member bearing zones, the unequal
non-collinear signed actions, or the resulting continuous bolt bending at
BG003. The four plane demands must not be converted to four independent
capacities and summed.

Ian Smith's 1983 thesis is a primary-source precedent for the narrower
two-dimensional method: nonlinear beam-on-foundation models for nonsymmetric
two- and three-piece timber joints, including axial connector force in its
large-displacement formulation. The thesis reports validation against twelve
three-piece specimen types, fifteen replicates each, with reasonably good
mean load-displacement prediction below 4 mm displacement. That evidence
supports testing this model family, but it does **not** validate BG003's
two-axis transverse response, these members, these materials, or these
actions. The current AWC TR12 provides general dowel equations for standard
connection modes; it does not fill that extension gap.

## Proposed bounded method

Analyze **each** `BG003` physical bolt as one continuous beam through the
ordered stack `knee_outer_left_spine` → `base_side_left` →
`knee_outer_left_inner_frame_block`. The pinned model intervals are 38.1 mm,
88.9 mm, and 88.9 mm along the bolt axis. Preserve each member's actual
bearing interval and grain frame. Do not split the middle member into two
independent side-member checks.

The candidate model has one continuous steel beam with transverse displacement
and bending in both global Y and Z directions. Each of the three wood bearing
intervals supplies a local, compression-only, direction-dependent
force-versus-slip foundation law in that member's grain frame. The beam and
all bearing intervals share one compatible displacement/rotation field; the
two middle-member intervals act simultaneously on that same beam. Bolt axial
force is applied from the signed outer-seat tie action. Do not credit
unverified face friction or clamp preload. Internal bolt shear and
moment-curvature are recovered from the solved distributed bearing reactions
and beam equilibrium, not read from a member-wrench datum moment.

Use either the source's individual signed interface actions and exact points,
or the equivalent member force-and-moment wrenches reconstructed from those
actions, as the external member actions for the local equilibrium problem.
Never apply both representations at once. The exported moments are
whole-member wrench moments at their stated datums; they are not internal
bolt moments. Match the source member equilibrium while solving the beam and
bearing compatibility, and obtain the bolt's internal bending from the
continuous beam solution.

The concept couples distributed timber bearing with continuous bolt
bending/shear under the signed actions. A complete physical resistance would
also need sourced limit criteria for splitting, net-section/edge failure,
axial/lateral interaction, and the two-bolt BG003 group. This note does not
define or calibrate those criteria and calculates no capacity. Keep the rest
of the six physical corner bolts in BG001/BG003/BG045 in their source-bound
load path; this method candidate concerns the two BG003 bolts only. Those six
corner bolts are part of 92 new axes, separate from the 12 retained
arrangements. Do not combine their capacities or transfer the retained
arrangement checks.

## Pinned conditional demand and geometry

The source is the accepted conditional a12-rear numerical report at full load,
not an adopted joint demand for other cases. It records two BG003 physical
bolts, four lateral plane actions, and two outer-seat tie actions:

| Physical bolt | Plane action on first member (global N) | Outer-seat tension |
| --- | --- | ---: |
| `knee_outer_left_side_1` | plane-37, on spine: `(0, -292.4238, 385.6081)`; plane-38, on `base_side_left`: `(0, -0.9183937, -65.90672)` | 95.96739 N |
| `knee_outer_left_side_2` | plane-39, on spine: `(0, 230.4513, -64.21217)`; plane-40, on `base_side_left`: `(0, 20.71486, -84.4807)` | 43.50841 N |

At each plane the second member receives the equal-and-opposite vector. The
plane locations are at X = −1219.2 mm and −1130.3 mm, 88.9 mm apart. For
side_1 the two displayed outer lateral actions are 483.948 N and 65.913 N,
37.973° apart; for side_2 they are 239.230 N and 86.983 N, 119.347° apart.
The inputs are unequal and not collinear, and the second bolt's actions oppose
in direction. This is why equal-side NDS double shear and independent plane
capacity addition do not answer the current case.

The tie values are actual signed axial demands in this conditional response;
they are not an assumed installation preload. No current wood, bolt product,
thread interval, material bearing curve, or adjusted resistance is established
by this demand report.

## Input and claim boundary

A **conditional analytical screen** can use the accepted case's source-bound
signed vectors, points, and member wrenches with the source-bound modeled
stack, plus explicitly declared hypothetical material and hardware scenarios.
For example, the existing packets use DF-L `G=0.50`, `D=0.25 in`,
`Fyb=45 ksi`, and nominal zero gaps as assumptions; these are not observations
of delivered wood, bolts, or installed contact. Any beam/foundation screen
also has to state its assumed bolt stiffness/yield and directional wood
bearing law. Missing upstream evidence may remain a stated assumption or
parameter range. Inspection is not a prerequisite to such a conditional
calculation, and the result must remain conditional on those inputs.

**Physical qualification** would additionally need observed installed member
order, dimensions, gaps/contact and seat conditions; identified delivered
wood and fastener properties; and applicable member, group, brittle-limit,
and design-adjustment checks. None of those observations is established by
the conditional demand report. NDS tabulated `Fe` is a strength input, not by
itself a bearing stiffness or nonlinear load-slip law.

The exact method gap remains: current NDS/TR12 helper routes do not resolve
the actual unequal, non-collinear BG003 actions, while the primary-source
beam-on-foundation precedent is two-dimensional and does not validate the
required biaxial extension. No source-bound 3D known-answer result or BG003
directional foundation law is recorded here. Therefore this candidate gives
no complete BG003 resistance on the current documented assumptions. This is
the boundary of the present evidence, not a requirement to start a new solver
project before making other source-supported conditional screens.

## Source pins

- Conditional full-load report:
  [`corner-demand-report.json`](../current-corner-native-demand-export-attempt03/corner-demand-report.json),
  SHA-256 `812a62fa3cd96a8983649c84a8c78a8d176d639465c887b11d1827a3f8f1ee17`.
  It is bound to the a12-rear conditional zero-gap/ringA/ratio1/zero-accessory
  scenario only.
- Unequal-action screen:
  [`README.md`](../current-bg003-unequal-action-applicability-attempt01/README.md)
  and [`screen.json`](../current-bg003-unequal-action-applicability-attempt01/screen.json),
  SHA-256 `d87f20ca167f0418388dba5afe4ff0b08fbfbcdf60885477775a5ea756049790`.
- Three-member geometry and reviewed symmetric reference:
  [`calculation.json`](../current-knee-three-member-transfer-attempt01/calculation.json),
  SHA-256 `fb7fba30fdcdabf44c90a5ac7cfe167b6a9f659af8543a8070066f15ad45c5b1`.
- Reviewed implementation limits: [`nds_2024_multi_member_bolt_yield.py`](../../../../../mini_moonboard/nds_2024_multi_member_bolt_yield.py),
  SHA-256 `575d7de88d5f138412fef633ef946bccba884c1953b67e8d9211fc028d74ab89`;
  [`bolted_wood_wood_double_shear.py`](../../../../../mini_moonboard/bolted_wood_wood_double_shear.py),
  SHA-256 `46a7be4202f32bdcb4631c6137574204f64aa44365b582ebe2369319052afcbd`;
  [`fea/dowel_yield.py`](../../../../../fea/dowel_yield.py), SHA-256
  `d6c318e75c1a720d0b91f810a892e8309ef89735f66f48820ee853b753f8fe45`.
- ANSI/AWC NDS-2024 Chapter 12 review source is locally pinned at SHA-256
  `5fc837523ff10acc097a162718700a9b4ba64e627d2b0023439146d42fe4ee2a`;
  see the [official NDS-2024 page](https://awc.org/resources/2024-nds/) and
  [official Chapter 12 PDF](https://awc.org/wp-content/uploads/2026/08/AWC_NDS2024_withCommentary_20250328_WebsiteChapter-12-%E2%80%93-Dowel-type-fasteners.pdf).
- AWC, [TR 12 (2026), *General Dowel Equations for Calculating Lateral Connection Values*](https://awc.org/wp-content/uploads/2026/06/TR-12_2026_formatted.V3.pdf),
  Table 1-1. The official PDF is currently HTTP 403 to the browser fetch; the
  AWC search index exposes Table 1-1's solid-section-member single/double
  shear equation table. The local TR12 helper scope above was reviewed
  separately. Do not claim direct full-PDF review from this link alone.
- Smith, I. (1983), [*“Short term” load deformation relationships for timber
  joints with dowel type connectors*](https://researchportal.lsbu.ac.uk/en/publications/short-term-load-deformation-relationships-for-timber-joints-with/),
  PhD thesis, London South Bank University, DOI
  [10.18744/c746a5e5-fdec-43d7-85b7-21ee1c8d240a](https://doi.org/10.18744/c746a5e5-fdec-43d7-85b7-21ee1c8d240a).
  The university abstract identifies a 2D nonlinear beam-on-foundation model
  and the stated three-piece specimen validation; it does not support the
  proposed 3D extension without further validation.
- AWC [TR 12 gap/hinge FAQ](https://awc.org/faq/does-technical-report-12-general-dowel-equations-for-calculating-lateral-connection-values-assume-the-connector-does-not-deform-in-the-gap/)
  states that the TR12 assumption places a hinge in a main or side member,
  not in the gap. This is a scope reminder for any use of the TR12
  comparison; it does not validate the proposed model.

**Disposition:** bounded method candidate and exact applicability gap
recorded. The conditional actions and geometry can support explicitly
assumed scenario screens; full BG003 physical resistance is unavailable on
the current documented assumptions. No capacities are added across BG003
planes or transferred to the 12 retained axes.
