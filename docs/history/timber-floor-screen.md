# Timber-frame unanchored equilibrium screen

This supplements, but does not replace, the [bulk FEA](timber-structural-results.md).
The physical design is unchanged. **These results do not establish joint strength,
an approved climber weight or construction readiness.**

## What was tested

The source-bound current drilled model supplies its six floor-support hull
vertices, 176.360 kg included mass and center of gravity. The vertices are actual
floor-contact extreme points, not anchors. Reactions act upward with bounded
horizontal friction. A rigid whole-frame assumption permits any compatible
reaction distribution; it does not predict the real distribution or foot pressure.

There are 1,296 load cases, each evaluated at three assumed friction coefficients:

- 150, 200, 250 and 300 lb climbers, at 1× and 2× body weight downward;
- 80% and 100% included frame mass, at the same center of gravity;
- a single hold A/F/K on rows 1, 6 and 12 carrying the entire prescribed load;
- 100 mm hold standoff along the climbing-face normal;
- no horizontal force, or 300 N horizontally at eight 45-degree directions.

These are sensitivity cases, not certified design loads. They do not exhaust
all holds, directions, standoffs, multi-hold loading, upward force, impacts or
loss of a floor support. Friction coefficients are deliberately hypothetical;
none has been measured for the intended feet/floor.

## Results

| Assumed friction coefficient | Feasible cases | Infeasible in polygon model |
| --- | ---: | ---: |
| 0.10 | 590 | 706 |
| 0.20 | 1,296 | 0 |
| 0.40 | 1,296 | 0 |

At 0.10, 576 cases already exceed the necessary global sliding limit
`horizontal force <= coefficient × total downward force`. The remaining 130
polygon failures cannot be classified as actual circular-cone failures from this
calculation alone; spatial friction/moment constraints and cone approximation
need to be distinguished. A passing edge-moment calculation therefore does not
settle the unanchored-floor question.

The largest independently recomputed feasible force residual is below
5e-12 N; the largest moment residual is below 7e-9 N·mm. These demonstrate
numerical equilibrium, not physical accuracy. A lighter climber can be more
demanding for sliding in this study because the same 300 N horizontal force is
paired with less downward force. This is not a recommendation to add ballast.

## Method and reproducibility

At each support vertex, nonnegative weights multiply 16 force rays
`(mu cos(theta), mu sin(theta), 1)`. Six equations balance all external force
and moment components, including gravity and asymmetric-load yaw. The friction
polygon lies inside the circular Coulomb cone. A feasible witness is therefore
admissible for that assumed circular cone; polygon infeasibility alone does not
prove circular-cone infeasibility. No finite contact-pressure cap is imposed.

The implementation uses [SciPy's HiGHS linear-programming interface](https://docs.scipy.org/doc/scipy/reference/generated/scipy.optimize.linprog.html).
Each feasible solution is independently rechecked using summed forces and cross
products, nonnegative normals and circular friction limits. Solver failures are
errors, not infeasible structural cases. Witness forces are **one admissible
allocation, not predicted joint demands**; do not divide them among bolts.

The compressed [evidence](../fea/results/timber-floor-screen.json.gz) contains
every load wrench, feasible witness, summary and source hashes. Tests replay
inputs and independently audit the witnesses. Historical FEA files are unchanged.

```bash
uv run pytest -q tests/test_rigid_floor_screen.py tests/test_timber_floor_screen.py
# In a separate working copy with the published output absent:
uv run python -m fea.timber_floor_screen
```

The runner refuses to overwrite existing evidence and checks the inherited
timber source identity before and after solving.

## Next connection work

1. Recover aggregate six-component leg and lower-base resultants from the current
   accepted mesh, then add asymmetric FE load cases with matching equilibrium
   audits. Those fixed-floor, bonded-frame forces remain conditional demands.
2. Resolve lower-backing bolt edge distance and qualify actual gusset, angle and
   leg connections against those demands. Four collinear leg-bolt centers cannot
   alone resist every moment component: face/washer bearing and bolt action need
   an explicit model, not equal division by four.
3. Establish actual foot/floor friction and support contact behavior before using
   an unanchored model for design decisions. A validated local contact coupon is
   preferable to repeating the earlier unqualified whole-frame contact runs.

This increment completes the finite equilibrium screen, not those connection
checks or full nonlinear contact FEA. It does not justify reducing timber or
replacing through-bolts with [threaded inserts](threaded-insert-options.md).
