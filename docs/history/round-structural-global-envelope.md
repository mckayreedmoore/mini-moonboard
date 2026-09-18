# Current structural-screw global load sensitivity

**Two of 48 grouped sensitivities fall below the retained 1.5 overturning
comparison. None predicts loss of rigid-body moment equilibrium. This is not a
frame, connection or floor qualification.** The current CAD inventory and all
142 hold positions were recalculated for `round-structural-development`;
historical insert-model mass and demands were not transferred.

The [calculator](../fea/round_structural_global_envelope.py) reuses the existing
analytical support-edge method and saves a
[source-authenticated report](../fea/results/round-structural-global-envelope-v1.json).
Reproduce to a fresh output path:

```sh
uv run python -m fea.round_structural_global_envelope --output /tmp/current-global-envelope.json
uv run pytest -q tests/test_round_structural_global_envelope.py
```

## Inventory and assumed installation

The current drilled wood and modeled hardware have calculated mass **166.616 kg**
at centroid **(−0.012, 628.366, 1011.239) mm**, using assumed wood/plywood density
600 kg/m³ and steel 7850 kg/m³. Fastener components are unioned before mass
integration to avoid double counting overlap. Hold and electrical mass are
excluded. The 80% mass case retains the same centroid; it is a sensitivity,
not a measured or statistical lower mass bound.

Support is level, rigid and unanchored at four posts and two leg feet. Kicker
panel edges, pads and unspecified ballast receive no support credit. No
physical floor measurements or tests are requested. These assumptions do not
establish local floor pressure capacity, individual contact reactions, friction,
joint forces or acceptance of any actual surface.

## Loads and calculation

Every one of the 132 main and 10 kicker holds is considered individually.
Main load points use the current 18.25625 mm panel thickness; kicker points use
the current header-front plane. Each group combines:

- 250 lb intended maximum or 300 lb sensitivity;
- downward weight ×1 or ×2;
- 80% or 100% modeled dead mass;
- outward hold standoff 0, 50 or 100 mm;
- horizontal force 0 or 300 N.

The doubled weight, 300 N horizontal force and offsets are inherited project
sensitivities, not a verified dynamic design envelope. Each support edge uses
its exact worst horizontal direction over all azimuths. Each full resultant is
applied at one hold at a time, not at every hold simultaneously. Top/side-edge
use and simultaneous hand/foot force couples are outside this calculation.

For a counterclockwise support edge, let `d` be signed inward distance, `h` the
load height and `W` dead weight. Restoring moments are `W*d(CG)` from dead load
and `D*d(load) + h*(H dot inward)` from live load. Where live moment overturns,
the comparison factor is dead restoring moment divided by its magnitude.
The [retained CWA source](https://www.cwapro.org/file/secure/cwadesignpecfinal2022.pdf)
provides the 1.5 overturning comparison; its scope and complete load combinations
remain unestablished for this custom equipment. The source identifies itself
as the January 2009 first edition despite the filename.

## Results

46 groups meet the moment comparison only. The two shortfalls both use doubled
weight, 80% dead mass, 100 mm hold standoff and 300 N horizontal force:

| Climber sensitivity | Minimum factor | Remaining net restoring moment |
| --- | ---: | ---: |
| 250 lb | 1.489852 | 364.444 N·m |
| 300 lb | 1.427370 | 331.876 N·m |

Both are governed by the rear foot edge at Y = 1476.339 mm with a row-12 load
and horizontal force toward +Y. A12 is the retained tie witness; all row-12
holds have the same sagittal moment for that edge. Positive net restoring
moment explains why the result is below the 1.5 comparison without predicting
tip-over under the unfactored sensitivity. The 250 lb shortfall is small but
is retained; no mass or force assumption was adjusted to erase it.

The reported horizontal-force/total-weight ratio is only a necessary net
translational friction demand. It does not solve individual sliding or yaw
equilibrium, and is not a measured coefficient or a floor pass.

## Release implication

The installation/load basis and remaining overturning margin need resolution
alongside the panel, member and joint checks. Global equilibrium does not bound
self-equilibrated internal forces in this redundant frame. This result therefore
cannot supply unique bolt, angle or beam demands. The design remains unreleased.
