# Current-wide unanchored floor equilibrium screen

The `wide-principal-development` candidate admits compression-only floor
equilibrium in all 1,296 sampled scenarios at assumed friction coefficients
0.2 and 0.4. This supports retaining its present footprint for continued joint
development; it does not qualify the real floor, connections or climbing use.

## Inputs and scope

The calculation authenticates the existing current-wide stability source closure,
including its manifest, rather than borrowing predecessor mass or floor geometry.
Included mass is 200.0366 kg, with centre at approximately
(-3.958, 610.459, 1003.932) mm. This inventory includes modeled wood and bracket
steel; omitted hardware, holds and other items are not silently assigned mass.
The six actual floor-hull vertices are retained in the result file. Contact may
occur only through nonnegative normal reactions at those vertices.

The finite matrix includes 150/200/250/300 lb climbers, 1×/2× weight, 80%/100%
included frame mass at fixed centre, nine holds (A/F/K at rows 1/6/12), 100 mm
outward hold standoff, and zero or 300 N horizontal force at eight directions.
These illustrative loads are not a validated governing load specification.

The existing linear-programming solver balances all six global force/moment
components, including gravity and yaw, using 16-ray inscribed friction cones.
Every feasible result is independently checked for equilibrium, nonnegative
normal force and circular friction limits. Its reaction distribution is one
possible witness, not a prediction of leg, gusset or bolt forces. No elastic
compatibility, local pressure limit, uneven floor or dynamic response is modeled.

## Results

| Assumed coefficient | Feasible sampled cases | Infeasible polygon cases |
| --- | ---: | ---: |
| 0.1 | 683 | 613 |
| 0.2 | 1,296 | 0 |
| 0.4 | 1,296 | 0 |

Of the 613 cases at 0.1, 504 also violate the necessary aggregate bound
`horizontal force <= coefficient × total normal reaction`. Those cannot balance
under the stated uniform 0.1 Coulomb-friction assumption. The remaining 109
polygon failures are not proven circular-cone failures; do not label all 613
as physical sliding or tipping failures. Maximum aggregate friction demand is
0.134133, which alone does not address yaw or local reaction allocation.

The earlier approximately -561 N fixed-base vertical reaction belongs to a
different no-gravity, fixed-floor elastic model. It is not evidence that this
gravity-inclusive unanchored rigid body must lift off or requires an anchor.
Conversely, equilibrium witnesses here cannot validate that elastic model's
individual joint load sharing.

## Reproduction and next decision

`uv run python -m fea.wide_floor_screen` produces
[`wide-floor-screen.json.gz`](../fea/results/wide-floor-screen.json.gz), refusing
to overwrite existing evidence. The saved source hashes bind geometry, inputs
and calculation code. Regression checks authenticate all sources, reconstruct
all scenarios, check every feasible witness and replay representative statuses.

```sh
uv run pytest -q tests/test_wide_floor_screen.py tests/test_rigid_floor_screen.py tests/test_timber_floor_screen.py
```

All 37 focused tests passed on September 8, 2026. The inherited tests retain
separate predecessor evidence; they do not turn predecessor results into current
candidate results.

Do not add anchoring or ballast based on the fixed-floor reaction alone. Continue
the current candidate's joint assessment, retaining floor-friction verification
and contact/stability validation as explicit gates. The assumed 0.2 coefficient
is a sensitivity input, not a floor-material recommendation or acceptance value.
