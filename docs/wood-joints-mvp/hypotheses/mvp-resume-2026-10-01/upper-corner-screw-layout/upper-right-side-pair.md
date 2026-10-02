# Upper-right side pair: shared-host local response

**2026-10-02 — conditional analytical working model. Complete joint and
physical release remain HOLD.** Geometry, source frame forces, hardware
selection and the 47-criterion authority remain unchanged.

## Decision

All **six cases converge and balance** on the first finite run, in
9–12 iterations. A shared side pose changes axial bolt shares, but does
**not produce useful lateral sharing** in this scenario. Side_1's derived
lateral resultant stays below 1.1e-5 N; side_2 retains the original lateral
load within approximately 2.4e-8 N, including **1,098.757 N at K12 rear**.
Do not divide that lateral demand equally between the two side bolts.

At K12 right, tensions change from **491.381/506.755 N** to
**422.565/552.319 N**. At K12 rear they change from
**457.315/527.959 N** to **413.274/549.164 N**. The maximum nominal
smooth-bolt stress proxy is **199.011 MPa**, or **0.31374** of the declared
92 ksi steel hypothesis. That hypothesis is not exceeded.

This completes the finite common-host side-pair check. Together with the
rail packet, it supplies same-state, locally compatible bolt/contact shares
for each host under a rigid cleat assumption. It does not close the shared
timber block or complete joint. The next useful load-transfer check is
**rail washer flexure under the derived end forces and moments**: the rigid
washer assumption still suppresses its deformation and metal stress, while
the rail seat has the larger sampled pressure, 7.146 MPa. Reuse these loads
in the existing washer work under parent ownership; no additional method
or qualification gate is introduced here.

## Finite scope

This extension gives the two upper-right side bolts one common rigid
`base_side_right` pose under each preserved six-component side-interface
wrench. The existing sixteen compression-only cleat-face cells participate.
Bolt tensions, distributed lateral bearing, contact end moments and motion
follow the same frozen energy model used for the
[rail pair](upper-right-rail-pair.md).

The cleat remains fixed. The rail and side calculations have independent
host poses; they share a fixed cleat reference and six case identities,
but do not model elastic deformation or failure of their common timber
block. This is a local compatibility scenario, not complete joint
qualification or a replacement frame response.

## Current sources and datum

Use only the six nominal-gap states of `frame-250-attempt02`, with no
rebinding to subsequent panel-grain or screw-count alternatives.
The side interface contains **22 source rows**: four lateral components
(1812–1815), sixteen face contacts (1852–1867), and two outer-seat ties
(1868–1869). All join `base_side_right` to `top_outer_right_cleat`.

The common datum is the midpoint of the two current side-interface bolt
stations:

```text
cside = [1127.125, 1405.0269362288577, 2125.1250400799] mm
```

The symmetric finished face has its contact-area centroid at the same
point within approximately 3e-10 mm. Retained area is 16,594.855498 mm².
The datum is declared from the current bolt stations; no source geometry
is changed to select it.

The source side-body datum is approximately
`[1171.575,665.810728807,1228.604230900]` mm. Source operator D uses
`[t,1000*theta]`. The extraction and sign convention are:

```text
F_on_side = -D_translation.T * f
M_at_cbody = -1000 * D_rotation.T * f
M_at_cside = M_at_cbody + (cbody-cside) cross F_on_side
external_local_wrench = -(F_on_side, M_at_cside)
```

The signed point-force sum is checked independently. The tiny difference
between point moments and D moments is retained as a source free couple.
Gravity and remote loads are not added a second time.

For K12 right the external force is
`[-36.368432,-1023.735400,395.775804]` N and moment
`[35235.407326,4829.314531,56566.007133]` N·mm. For K12 rear these are
`[-58.447985,-1012.200962,427.452968]` N and
`[35626.419944,9841.730763,52900.191442]` N·mm.

## Chosen assumptions

Only the existing middle stiffness branch is used:

- Current 7.9375 mm smooth side bolt, 9.0 mm bore, 0.53125 mm radial
  clearance in each receiver, 88.9 mm host and 88.9 mm cleat grip.
  The 1.0625 mm total relative gap and 67.85 mm pitch are preserved.
- Hypothetical bolt E=200,000 MPa, wood bore and washer-seat modulus
  K=20 MPa/mm, and head-to-washer modulus K=10,000 MPa/mm.
- Rigid, concentric Bolt Depot 2995 washer scenario: minimum OD
  22.0472 mm, maximum ID 9.9060 mm, with hypothetical 12 mm circular
  head/nut bearing profiles at both ends. No actual washer stress or
  hardware capacity is assigned.
- Two transverse Euler–Bernoulli planes per bolt, eight elements per
  receiver, three bore Gauss points per element; tensile geometric
  stiffness and projected shortening remain included.
- Compression-only bore, head/washer/wood and face contact; positive
  bolt tension only; no preload, friction or adhesion.
- Existing face points, areas and stiffnesses, using their 100 MPa/mm
  normal modulus independently of the 20 MPa/mm seat scenario.
- One six-degree rigid side pose; fixed cleat; small rotations, smooth
  section and symmetric hypothetical bearing profiles.

The producer imports the frozen rail producer as a private module and
configures side constants in that private instance. It reuses the pure
mechanics routines and their normal-contact elimination, without modifying
either frozen producer. Side source extraction and result receipts are
separate. Circular annulus quadrature rotates with tilt, as in the rail
model; this is an explicit numerical approximation.

The active normal compatibility condition remains
`q + 0.5*integral(norm(w')^2 dx) = C_host + C_cleat + T*L/(E*A)`.
At zero tension, end contacts carry no force, moment or artificial
stiffness. A converged neutral pose is reported as representative whenever
the tangent has neutral modes.

## Why sharing cannot remove all side-bolt demand

The source side_1 lateral force is effectively zero in every case.
The side_2 source force peaks at **1,098.757 N** in K12 rear.
The two bolt stations also carry a substantial moment about their common
bolt axis. Face normal reactions and the transverse beam end moments
provide no moment about that axis in this model.

Consequently, equilibrium fixes the difference between the two lateral
force components perpendicular to the station-to-station line. Components
parallel to that line can redistribute. A common-host calculation can
change the force magnitudes and axial shares, but equal division of the
whole lateral resultant generally cannot preserve the saved torsional
wrench. The numerical results below retain that wrench.

## Same-state force comparison

Forces are in N. Each arrow is **frozen point-force demand → shared-side
response**. Side_1 V is approximately zero on both sides of the comparison;
its computed residual is below the declared numerical force tolerance.

| Case | T1 | T2 | V2 | Face compression | Maximum steel proxy, MPa |
| --- | ---: | ---: | ---: | ---: | ---: |
| A12 rear | 63.1 → 50.7 | 47.0 → 89.8 | 105.8 → 105.8 | 93.6 → 124.0 | 14.107 |
| A12 forward | 30.6 → 25.3 | 18.6 → 43.1 | 49.6 → 49.6 | 44.5 → 63.6 | 6.581 |
| A12 left | 39.4 → 31.2 | 15.7 → 53.4 | 61.8 → 61.8 | 51.1 → 80.6 | 8.207 |
| K12 right | 491.4 → 422.6 | 506.8 → 552.3 | 1,097.6 → 1,097.6 | 1,034.5 → 1,011.3 | 199.011 |
| K12 rear | 457.3 → 413.3 | 528.0 → 549.2 | 1,098.8 → 1,098.8 | 1,043.7 → 1,020.9 | 198.953 |
| A1 rear | 6.70 → 5.44 | 7.97 → 6.07 | 6.77 → 6.77 | 14.66 → 11.51 | 0.902 |

The machine worksheet retains signed global bore forces and their
components along and across the 67.85 mm pair line. For example, K12 right
side_2 carries host-bore force `[0,1023.735400,-395.775804]` N, with
along-pair/across-pair components **354.863/1,038.627 N**. The corresponding
side_1 resultant is below 7.3e-8 N. The allowed along-pair redistribution
does not occur materially at this load and clearance scenario.

The derived V is the integrated host-bore resultant. Full bolt-host
wrenches also include axial ties and outer-seat moments. All bolt and face
wrenches together balance the preserved simultaneous external wrench;
neither a lone V nor independently chosen peaks reproduce that interaction.

## Contact, steel and local motion

The following are same-case envelopes over the two bolts and their ends.
End moment, pressure and stress need not share one witness.

| Case | Lateral slip at side datum, mm | Side rotation, degrees | Maximum end moment, N·m | Maximum wood-seat pressure, MPa |
| --- | ---: | ---: | ---: | ---: |
| A12 rear | 1.145 | 0.198 | 0.488 | 0.828 |
| A12 forward | 1.104 | 0.0868 | 0.234 | 0.398 |
| A12 left | 1.112 | 0.121 | 0.290 | 0.493 |
| K12 right | 1.533 | 1.414 | 2.667 | 4.555 |
| K12 rear | 1.556 | 1.351 | 2.659 | 4.538 |
| A1 rear | 1.067 | 0.0117 | 0.0330 | 0.0560 |

Normal opening at the datum peaks at **0.1459 mm**, K12 right. Maximum
sampled face pressure is **0.5885 MPa**, also K12 right. The highest sampled
bore pressure is **12.0314 MPa** on side_2 at K12 rear, in the host at
x=87.6476 mm from its outer face. It corresponds to 0.60157 mm local
foundation penetration under the declared 20 MPa/mm elastic law, not an
observed timber indentation or a checked nonlinear bearing capacity.

The nominal steel witness is side_2, K12 right, x=77.7875 mm. Its internal
bending-moment magnitude is approximately **9.124 N·m**, distinct from the
**2.667 N·m** maximum end contact moment. Distributed bore reactions allow
the internal moment to exceed the end moment. The witness uses simultaneous
T=552.319 N and V=1,097.576 N, with the stated smooth-section hypothesis.

At the peak side seat, K12 right side_2 cleat end, mean/peak wood pressure
is **1.813/4.555 MPa**, with active wood area **255.242 mm²** (83.8% of
the minimum annulus). The head resultant is at **80.5%** of the hypothetical
6 mm radius, with sampled active head area 13.510 mm². The retained
4.309 MPa timber reference is a mean bearing reference, not an imposed
pointwise cap. These fields do not constitute actual washer metal stress
or a physical seat failure; both actual capacities remain null.

Four side tangents report one neutral mode at the existing relative 1e-12
threshold (A12 forward, A12 left and both K12 cases). A12 rear and A1 rear
report zero at that threshold. Side_1 bore reactions are below the declared
force tolerance in all six cases; a tiny positive sampled contact can affect
the numerical rank. **Zero reported nullity is not evidence that actual
clearance motion is uniquely constrained.** No zero-force contact is
deliberately retained to create stiffness. All motions here are returned
representative poses; no full free-play interval or motion envelope is claimed.

## Both hosts at one common datum

Reuse the frozen rail-pair result, without another solve. Both local poses
use the same fixed cleat reference. Shift side motion to the existing rail
datum `cr=[1082.675,1449.9256507823475,2178.633244417593]` mm:

```text
u_side(cr) = t_side(cside) + theta_side cross (cr-cside)
relative_translation = t_rail(cr) - u_side(cr)
relative_rotation = theta_rail - theta_side
```

The six returned rail-relative-to-side translations are in global XYZ.
These are representative local motions, not adopted frame deflections.

| Case | Relative XYZ at cr, mm | Magnitude, mm | Relative rotation magnitude, degrees |
| --- | --- | ---: | ---: |
| A12 rear | (-0.204, 2.281, -0.946) | 2.478 | 0.546 |
| A12 forward | (-0.128, 2.087, -0.963) | 2.302 | 0.330 |
| A12 left | (-0.103, 2.153, -0.846) | 2.315 | 0.221 |
| K12 right | (-0.067, 4.660, -2.616) | 5.344 | 1.092 |
| K12 rear | (-0.024, 4.605, -2.665) | 5.321 | 1.043 |
| A1 rear | (0.0004, 0.854, -0.664) | 1.082 | 0.0165 |

For example, at K12 right the rail displacement is
`[0.073407,1.732205,-1.132403]` mm and shifted side displacement is
`[0.140546,-2.927487,1.483765]` mm. Subtracting translations at their
different original datums would give a different, invalid comparison.
Four side cases and the A1 rail case have recorded neutral modes; those
five relative poses are expressly nonunique representatives. The other
case is also subject to the near-zero contact/rank caution above.

## Numerical receipts

The first production attempt returns 6 states, 12 bolt records, 960 beam
samples, 576 bore samples and 96 face cells, with 142 scaled unknowns.
Maximum recorded residuals are:

| Quantity | Returned maximum | Declared local tolerance |
| --- | ---: | ---: |
| Mixed scaled gradient | 6.09e-5 N | 1e-4 N |
| Whole-host force component | 1.08e-5 N | 0.001 N |
| Whole-host moment component | 2.58e-4 N·mm | 0.2 N·mm |
| Axial compatibility | 1.65e-16 mm | 1e-9 mm |
| Series-contact moment mismatch | 3.06e-11 N·mm | Existing contact root tolerance |
| Series-contact tilt mismatch | 0 rad | Existing series relation |

Signed D and point-force sums differ by at most 2.28e-13 N; the retained
source free couple is below 2.62e-10 N·mm. All nine source pins and eight
declared producer-output pins were rechecked. Ruff passes. No software
tests, frame/native/CAD solves or review loop were run.

Ignored raw evidence is in `rawlocal/upper-right-side-pair/attempt01/`.
`worksheet-summary.py` reads saved rail/side checks only; it performs no
mechanics solve. Main receipts are:

| Artifact | SHA256 |
| --- | --- |
| `upper-right-side-pair.py` | `ce07e9489d96fb251ee780ecb96cdbb38539b5d204922a74c39066095d9ac0cc` |
| `checks.json` | `b507a5a501737c89814a471eee6a12749a3c54224f5444b2c5d583020e875ba7` |
| `source-pins.json` | `e4363994274653254693c34f5666d96076807b2e231399e43ead4015083e7011` |
| `worksheet-summary.py` | `0b3cda454e229332946c237de687630c3347bdec4a421be61b3d8bb02795125d` |
| `worksheet-summary.json` | `14a199559df658a57844f6d85b134ce3556e16268c0612173797784d3c0e1404` |

## Reproduction and claim boundary

Run the finite local producer from the repository root into a fresh path:

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 .venv/bin/python \
  docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/upper-corner-screw-layout/upper-right-side-pair.py \
  --output docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/upper-corner-screw-layout/rawlocal/upper-right-side-pair/attempt01
```

This is saved-input local analytical postprocessing. No native solve,
frame solve, CAD operation, software tests, review loop, staging or commit
belongs to this worker's deliverable. Hypothetical steel comparisons and
sampled bore/seat pressures do not establish actual bolt, washer, timber,
splitting or complete-joint resistance. Actual capacities and physical
release remain unassigned.
