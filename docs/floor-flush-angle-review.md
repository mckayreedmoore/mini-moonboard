# Flush-frame commercial-angle disposition

This review concerns `compact-floor-flush-development` and the saved A12-left
assessment in [floor-flush-a12-left-assessment.json](floor-flush-a12-left-assessment.json).
It does not establish an angle failure load, select replacement hardware, or
transfer results from preceding frames.

## Decision

**The present ML24Z catalog comparison does not establish the complete connection
resistance. Keep this gate open. Do not substitute A34 angles or switch catalog
installation rows to declare it closed.** The missing separation rating occurs
at six stations, so an outer-base-only change cannot close the current ledger.

The smallest useful next mechanical study is a complete-wrench check of the
existing connection family, followed by a targeted change only where that check
cannot be supported. More whole-frame load cases cannot supply a missing local
resistance model. Conversely, the current diagnostic does not establish that
every angle must be replaced or reinforced.

## What the current case actually requires

The saved `commercial_angles` ledger contains 24 angles. All 24 listed
force-component interaction values are below one; the maximum is 0.475515 at
`clip_single_top_left_1`. These values omit unlisted positive separation in the
bearing-like installations and do not resolve the full flange moment.

| Bearing-like station | Unlisted separation, N | Listed-force interaction |
| --- | ---: | ---: |
| `clip_angle_base_left` | 192.549 | 0.358 |
| `clip_timber_header_outer_left` | 152.957 | 0.309 |
| `clip_split_base_center_right` | 52.030 | 0.068 |
| `clip_angle_base_right` | 49.571 | 0.027 |
| `clip_split_base_center_left` | 22.042 | 0.011 |
| `clip_split_header_center_left` | 12.785 | 0.042 |

The two other bearing-like stations have no positive separation in this case.
Their unloaded direction in one case is not a permanent exemption. Separation
is along each station's mapped local axis; it is not always global upward load.
These demands belong to the saved friction/contact case and must be recomputed
when support or detail assumptions change.

At the left outer base angle, the loaded upright flange applies this wrench to
the bracket about its recorded bend origin:

| Quantity | X | Y | Z |
| --- | ---: | ---: | ---: |
| Force, N | −180.713 | −707.316 | +192.549 |
| Moment, N·mm | −15,224.455 | −7,222.880 | +6,437.123 |

The beam flange applies the balancing wrench. Across the 24 angles, the largest
all-six-screw force residual is 0.009273 N and the largest moment residual is
0.260705 N·mm. Those small residuals show local equilibrium of the recorded
forces; adding both flanges together would hide the load transferred through
the connector.

## Correct interpretation of the moment diagnostic

For force **F** and moment **M**, the signed parallel moment is
`dot(F, M) / norm(F)`. At the left outer base it is **12.052 N·m**. Moving the
origin changes **M** by a cross product with **F**, whose dot product with **F**
is zero. Thus no change of origin can turn this wrench into one force alone.

**This does not, by itself, demonstrate a moment outside a manufacturer's
combined-direction rating.** Several rated directional loads may have distinct
application lines. Their combined wrench can have a nonzero parallel moment
even though each individual force has none. For example, a unit X force applied
at the origin and a unit Y force applied at `(0, 0, 1)` produce
`F = (1, 1, 0)`, `M = (−1, 0, 0)`, and `dot(F, M) = −1`.

The supported check is therefore:

1. Establish applicable installation, grain directions, fasteners, wood size,
   force signs and allowed application lines for each directional reference.
2. Express those reference loads and their inherent moments at the same origin
   as the recovered flange wrench.
3. Check the directional interaction and compute the residual moment after
   accounting for those reference moments.
4. Establish resistance for any remaining wrench through the physical
   connector/fasteners/contact or a modeled alternate connection.

The published illustrations inspected here do not provide the numerical
application-line coordinates or a general arbitrary flange-moment envelope.
Consequently this review cannot calculate that residual against established
catalog wrenches. The existing `independent_couple_resolved: false` remains an
appropriate unresolved status, rather than proof of zero moment capacity.
Do not divide 12.052 N·m by an invented lever arm and compare the result with an
unused directional allowable.

## Manufacturer basis and bounded alternatives

[Simpson L-C-MLZ25](https://ssttoolbox.widen.net/content/iczmiabsx6/pdf/L-C-MLZ25.pdf)
distinguishes single/end and bearing installations. Its bearing diagram shows
F1 and F3/F4; the repository's source ledger records no bearing F2 allowable.
The same part number and screw count do not establish that the single/end F2
reference applies to reversed bearing load. The source's page-2 installation
illustrations were re-inspected for this review.

[Simpson C-C-2026, page 289](https://ssttoolbox.widen.net/view/pdf/orplhjaqw1/C-C-2026.pdf)
does provide a simultaneous directional-load unity equation. That equation
requires an applicable allowable for each participating direction. It supplies
no independent arbitrary-moment term. The alternative 75% provision is limited
to named roof-to-wall product groups. It is not an ML24Z workaround.

The earlier [A34 study](round-base-angle-remedy.md) identified a catalog bearing
uplift entry but left sloped-grain applicability, complete hardware geometry,
and wrench resistance unresolved. Its receiver-fit result used a preceding
single-2x6 rim/header assembly. It does not qualify placement in the current
4x6-rim frame. A single A34 swap at each outer base is therefore **not selected**:
it addresses only one kind of missing rating at two of six affected stations.

An independent mechanics-based check of the existing angle is possible in
principle, using individual screw loads, angle bending and local bearing/contact.
It must establish steel properties, net sections, bend behavior, screw combined
loading and wood failure modes; treating the angle as rigid and checking only
screws is insufficient. No such resistance calculation is supplied by the
current force-component helper. Adding another angle without a force-sharing
model is equally unsupported.

This is a finite negative disposition of the proposed catalog-only closure:
**retain the current hardware as development geometry; do not release it from
the present catalog ledger.** Resolve all six separation stations and the
applicable full-wrench envelope, then rerun changed physical connections in the
current assembly. No external review or physical floor test is introduced as a
new prerequisite.

## Reproduce the demand inventory

This read-only command uses the checked-in assessment; it does not run a solver:

```sh
python3 - <<'PY'
import json
from math import sqrt
from pathlib import Path

angles = json.loads(Path('docs/floor-flush-a12-left-assessment.json').read_text())['commercial_angles']
for name, row in angles.items():
    flange = 'upright' if row['bearing_like'] else 'beam'
    wrench = row['flange_member_on_bracket_wrenches'][flange]
    force, moment = wrench['force_xyz_n'], wrench['moment_xyz_nmm']
    parallel = sum(f*m for f, m in zip(force, moment)) / sqrt(sum(f*f for f in force))
    assert abs(parallel - wrench['parallel_couple_nmm']) < 1e-6
    if (row['unlisted_separation_demand_n'] or 0) > 0:
        print(name, row['unlisted_separation_demand_n'], row['rated_force_component_unity'])
print('Angles:', len(angles))
PY
```
