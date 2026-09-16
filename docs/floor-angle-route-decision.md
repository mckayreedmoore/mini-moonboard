# Representative floor-angle route decision

Date: September 14, 2026. Candidate: `compact-floor-flush-development`.

## Decision

The existing ML24Z catalog route and the available independent mechanical route
do **not** establish complete resistance for the representative left outer
rim/header connection. This is a completed, unsupported-route investigation:
it is not proof that the angle or structure fails, and it does not close the
construction-release gate. No connector, geometry, source, or design selection
is changed.

`clip_angle_base_left` is the representative joint. In the saved A12-left case
it has the largest positive separation demand among the six bearing-like ML24Z
stations, and its 7.223 N·m moment projection on the bracket bend line is also
the largest of those stations. The larger 0.4755 listed-force interaction at a
rail-end angle is a different question; this selection governs the missing
bearing-like separation/complete-wrench route, not every ML24Z metric.

One finite next local study is defined below. Do not expand it to other stations
or change the selected assembly unless that one candidate first produces a
supported local result.

## Evidence and coordinate basis

Demand comes from the authenticated A12-left response used by
[floor-flush-a12-left-assessment.json](floor-flush-a12-left-assessment.json).
The assessment records the report digest as
`91831a6abf62ecee7a14795e5100a2587daaa77cfe2709c8b1a9e6ab5c2224ee`.
The response is the 250 lb A12 case with applied force
`(-300, 0, -2224.111) N`, 25 kg equipment allowance, the recorded finite
Coulomb floor scenario, and a converged contact active set. These facts make it
a usable conditional demand witness, not a resistance qualification or a bound
on the other five cases.

World X runs across the board, Y front-to-rear, and Z upward. The left angle's
bend origin is `(-1130.3, -105.85, 277.0) mm`; local flange directions are
`u=(-1,0,0)` and `v=(0,0,1)`, so the bend line `u × v` is `+Y`. The loaded
member for the bearing-like catalog mapping is the upright flange attached to
`base_side_left`. The mapped catalog axes are F1 along `+Y`, separation F2
along `+Z`, and F3/F4 along X.

## Complete recovered connector demand

Forces and moments below are **member on bracket**, reduced at the recorded bend
origin from forces at the six actual screw points. Do not add the two flange
wrenches as if that were connection demand: their near cancellation is the free
angle equilibrium residual and would hide the transfer through the connector.

| Flange / attached member | Force `(Fx, Fy, Fz)`, N | Moment `(Mx, My, Mz)`, N·m | `|F|`, N | `|M|`, N·m | Force-parallel couple, N·m |
| --- | ---: | ---: | ---: | ---: | ---: |
| Beam / `base_header` | `(180.713, 707.316, -192.550)` | `(15.224, 7.223, -6.437)` | 755.002 | 18.039 | 12.052 |
| Upright / `base_side_left` | `(-180.713, -707.316, 192.549)` | `(-15.224, -7.223, 6.437)` | 755.002 | 18.039 | 12.052 |

The six-screw free-body residual is `(-0.000225, 0, -0.001018) N` and
`(-0.000117, 0.000004, -0.000064) N·m`. This confirms equilibrium of the
reported screw resultants within recovery precision. It does not establish
angle resistance.

The force-parallel couple is invariant under translation of the reduction
origin. At this declared origin the upright wrench also has 13.421 N·m of
moment perpendicular to its force, and its projection on the actual `+Y` bend
line is `-7.223 N·m`. These are wrench descriptors, not catalog utilization
ratios. Manufacturer directional loads can have different inherent application
lines, so no residual moment can be calculated until those reference lines are
known.

### Actual screw application points and local demands

Each row gives force on the bracket. “Withdrawal” and “compression” describe
the opposite force on the wood along the screw installation axis. Beam screws
enter the header along `-Z`; upright screws enter the rim along `-X`.

| Screw | Point `(X, Y, Z)`, mm | Force on bracket `(Fx, Fy, Fz)`, N | Wood axial demand, N | Concurrent shear, N |
| --- | ---: | ---: | ---: | ---: |
| `beam_1` | `(-1088.057, -67.750, 277.000)` | `(513.870, 218.029, 175.248)` | 175.248 compression | 558.211 |
| `beam_2` | `(-1094.407, -105.850, 277.000)` | `(59.650, 279.011, -143.456)` | 143.456 withdrawal | 285.316 |
| `beam_3` | `(-1088.057, -143.950, 277.000)` | `(-392.807, 210.275, -224.341)` | 224.341 withdrawal | 445.548 |
| `upright_1` | `(-1130.300, -67.750, 312.893)` | `(-116.835, -301.445, -483.917)` | 116.835 withdrawal | 570.127 |
| `upright_2` | `(-1130.300, -105.850, 319.243)` | `(-115.998, -171.845, 65.811)` | 115.998 withdrawal | 184.016 |
| `upright_3` | `(-1130.300, -143.950, 312.893)` | `(52.119, -234.025, 610.654)` | 52.119 compression | 653.962 |

These individual values are response-model demands. They are not six divisible
shares of an ML24Z catalog rating and are not independently qualified SDS
wood-joint capacities.

### Parallel timber contact

The rim/header end contact is a distinct load path. Of its four sampled
compression-only corner springs, only the point
`(-1130.3, -41.4973, 277.0) mm` is active in this case, at 401.9 N compression;
the other three points are open. The saved model uses 1,000,000 N/mm at each
active rim/header bearing point. Contact therefore carries part of the local
interface action and affects the screw wrench. It cannot carry tension.

## Catalog comparison

[Simpson L-C-MLZ25](https://ssttoolbox.widen.net/content/iczmiabsx6/pdf/L-C-MLZ25.pdf)
lists, for one ML24Z with six SDS25112 screws in DF/SP bearing installation,
F1/F2/F3/F4 allowables of 595/unlisted/450/750 lbf and allows no load-duration
increase for the ML24Z values. Using the established conservative 450 lbf
reference for either X sign gives:

| Component | Demand, N | Reference, N | Demand/reference |
| --- | ---: | ---: | ---: |
| F1 | 707.316 | 2646.692 | 0.26725 |
| F3/F4 conservative | 180.713 | 2001.700 | 0.09028 |
| F2 separation | 192.549 | Unlisted | Not calculable |
| Sum of listed-force terms | — | — | 0.35753 |

The [2026 Simpson catalog](https://ssttoolbox.widen.net/view/pdf/orplhjaqw1/C-C-2026.pdf)
supplies a simultaneous-direction unity equation only where each participating
direction has an applicable allowable. It supplies no general arbitrary-moment
term. The 0.35753 result therefore establishes only the two listed force terms.
It cannot create an F2 resistance or qualify the flange moment.

The manufacturer diagrams inspected in the prior
[angle review](floor-flush-angle-review.md) do not give numerical application
coordinates for the directional reference loads. Consequently the complete
recovered wrench cannot be decomposed into catalog forces and a supported
residual couple. Moving the analysis origin or applying the single/end F2 value
to this bearing-like mounting would not solve that applicability gap.

## Independent mechanical-route disposition

Published material properties alone are not enough to complete a mechanics
check. [IAPMO ER-280](https://forms.iapmo.org/ues_reports/reports/er_0280.pdf)
establishes the prior review's 33 ksi yield, 45 ksi tensile, and 0.0975 inch
base-metal thickness basis for these No. 12 ML angles. That resolves a steel
input, but the current response represents the angle as rigid and the six screws
as independent linear springs with unqualified response stiffnesses of
1,988.828 N/mm axial and 3,086.746 N/mm lateral. It does not resolve shell
bending, bend flexibility, local prying, screw-head/plate seating, nonlinear
wood embedment, or redistribution with changing contact.

The generic screw shortcut is also unavailable. As established in
[floor-runner-angle-resolution.md](floor-runner-angle-resolution.md),
[ICC-ES ESR-2236](https://cdn-v2.icc-es.org/wp-content/uploads/report-directory/ESR-2236.pdf)
requires 45 mm minimum penetration for its NDS steel-to-wood route. The current
38.1 mm under-head screw has only 35.5448 mm gross penetration after the nominal
ML24Z plate thickness. The base-header factory pattern's 6.35/38.1 mm adjacent
offsets also do not satisfy the report's separate tested-lateral geometry.
Isolated steel screw strengths or an equal split of the 192.549 N separation
would omit actual group geometry, concurrent shear, moments, splitting, plate
flexibility, and contact redistribution.

Result: no existing catalog or mechanics calculation supports the full demand.
Steel properties are known; catalog force application lines, applicable F2
resistance, actual closely spaced screw-group resistance, and flexible
plate/contact behavior remain blockers.

## One finite next local connection study

Study one **exterior 23/32-inch plywood gusset joining the left outer rim to the
left outer post in `compact-floor-flush-development`**. This is the coplanar
exterior-face route identified in
[floor-runner-angle-free-feasibility.md](floor-runner-angle-free-feasibility.md).
It bypasses the unsupported rim/header ML24Z wrench rather than inventing an
ML24Z moment capacity. It is an investigation candidate, not selected hardware
or released drilling.

The local study must:

1. Freeze one plate outline and one catalog lag-screw/washer product, with at
   least two noncollinear fastener rows in each wood receiver and lengths that
   remain contained in both the 38.1 mm post and 88.9 mm rim directions.
2. Apply the complete saved A12-left rim demand at its physical line, retain
   compression-only rim/header and header/post contact, and model ML24Z and
   gusset load paths together if the angle remains present. No assumed equal
   load sharing is allowed.
3. Check eccentric fastener-group shear and withdrawal, plywood net section and
   block tear-out, plate bending, washer bearing, lag bending/withdrawal,
   receiver splitting, penetration, edge/end distance, and installation access.
   Use actual shank/root and bearing lengths; [AWC TR12](https://web-media.awc.org/wp-content/uploads/2021/12/17210714/AWC-TR12-1510.pdf)
   supplies the established varying-diameter lag calculation framework but does
   not qualify the whole joint by itself.
4. End with one binary local disposition: the frozen gusset and fastener group
   supports the complete local demand with every listed mode and applicability
   condition accounted for, or it is rejected with its governing unmet mode.

Stop after that result. Do not mirror it, remove all 24 angles, rerun six global
cases, or change the selected design in this study. This candidate applies only
to the selected flush geometry, where the exterior rim and post faces are
coplanar. The separate uncut candidate moves the 6x6 post exterior face 88.9 mm
from the rim; this gusset is not a drop-in route for that geometry.

## Value of the first uncut diagnostic solve

After its adapter/preflight dependencies pass, the first uncut A12-left solve
can add useful **branch-specific demand evidence**: changed global stiffness,
contact state, rim-face actions, and ML24Z forces for
`compact-floor-uncut-development`. It cannot establish catalog F2 or arbitrary
moment resistance, validate the present rigid-angle/spring idealization, or
qualify the flush-only gusset route. Continue that solve for the uncut branch
decision, not as a prerequisite to this negative route disposition.

## Reproduce the saved demand

This read-only extraction uses the authenticated response and does not invoke
CAD or the native solver:

```sh
python3 - <<'PY'
import json
from pathlib import Path

assessment = json.loads(Path('docs/floor-flush-a12-left-assessment.json').read_text())
report = json.loads(Path('fea/generated/floor-flush-first/a12-left/block-01/report.json').read_text())
name = 'clip_angle_base_left'
row = assessment['commercial_angles'][name]
assert row['bearing_like'] and row['unlisted_separation_demand_n'] > 0
print(json.dumps(row, indent=2))
for screw, force in report['physical_connection_forces'].items():
    if not screw.startswith(name + '_'):
        continue
    axial = force['axial_along_installation_direction_n']
    print(screw, force['point'], force['force_on_second_xyz_n'],
          {'withdrawal_n': max(0, -axial),
           'compression_n': max(0, axial),
           'shear_n': force['transverse_shear_n']})
PY
```
