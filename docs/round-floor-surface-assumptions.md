# Horse-stall mat, hardwood and carpet floor scenarios

This study responds to the owner's request to test several floor surfaces using
default assumptions. It runs new rigid-equilibrium calculations for the current
`round-insert-development` mass and load matrix. It does not measure a surface,
select a floor product, or qualify the frame for climbing.

## Explicit defaults

The starting condition is dry, level flooring with the modeled bare timber
feet. Coefficients below are deliberately labeled analyst assumptions. They
are neither measured material properties nor guaranteed lower bounds. The
lower values explore loss of traction; they are not calibrated wet-floor values.

| Surface | Assumed timber/surface μ | Assumed surface/subfloor μ | Assumed layer thickness | Degraded case |
| --- | ---: | ---: | ---: | --- |
| Horse-stall mats | 0.50 | 0.40 | 19 mm | Lower interface reduced to 0.12 |
| Hardwood floor | 0.30 | Not a separate loose layer | 0 mm | Timber/floor interface reduced to 0.10 |
| Carpet and backing | 0.40 | 0.25 | 10 mm | Backing/subfloor interface reduced to 0.10 |

The timber/rubber assumption alone cannot describe loose mats: sliding may
occur beneath them. Carpet pile and backing likewise cannot be assumed anchored
because the timber grips its top. This study grants no mat/carpet deadweight,
adhesive capacity, tack-strip resistance, expanded footprint or tensile restraint.
It treats the carpet's underlying attachment as an illustrative frictional
interface; it does not model an adhesive or tack strip as Coulomb friction.

For context, the USDA *Wood Handbook* gives a typical **kinetic**, not design
static, coefficient range of 0.3–0.5 for smooth dry wood on hard smooth surfaces,
and discusses moisture effects. This supports exploring friction sensitivity;
it does not establish the coefficient of the owner's finish, timber end grain
or flooring. The 0.30 hardwood assumption is a scenario choice, not a value
certified by that reference. [USDA FPL–GTR–190, printed page 4–17, PDF page 96](https://research.fs.usda.gov/download/treesearch/37440.pdf)

Humane's stall-mat installation instructions call for a level, prepared base
and discuss movement allowance around the perimeter. They supply no timber/mat
or mat/subfloor coefficient used here. [Humane installation sheet hosted by its retailer](https://www.greatmats.com/specs/humane/install-horse-stall-mats-straight-edge.pdf)

Shaw's specific CushionWorx/EcoWorx system calls for a sound, clean, level, dry
substrate and product-specific bonding at both layers. That illustrates why
carpet backing and installation matter; it does not identify the owner's carpet
or supply the assumed coefficients or a board-support rating. [Shaw installation instructions](https://pdmsview.shawinc.com/Shaw-Contract-Group-PDMS/SCG-Hard-Surface/Carpet/Cushion-%281%29/Cushion-Installation/CushionWorx-Installation-Guidelines)

## New calculations and contact-loss sensitivity

Each surface runs all 1,296 saved current-candidate load wrenches in four states:
all six supports at nominal friction, all supports at degraded friction, the
entire left rear leg foot unavailable, and the entire right rear leg foot
unavailable. The foot-loss states retain nominal friction. Four post contacts
and the remaining leg foot stay available; kicker edges receive no credit.
The support hull is rebuilt from the retained complete body footprints.

A missing rear foot is a deliberately severe contact-loss sensitivity. It is
not a prediction of how much a mat compresses or a carpet settles. Unevenness,
indentation and rocking need actual contact/compliance evidence. The model
retains a rigid frame at its nominal pose and does not simulate the motion into
a new contact state or a particular physical gap height.

For the layered surfaces, upper and lower interfaces are solved separately.
The lower-interface origin is beneath the upper one, so its applied wrench is
translated by `M_lower = M_upper + [0, 0, thickness] × F`. This retains the
additional overturning moment of horizontal forces at the assumed 19 mm or
10 mm elevation. The same plan-view footprints are used at both interfaces;
no wider support is invented. Both interfaces need feasible witnesses for a
scenario to avoid a demonstrated static failure. Independent interface
feasibility still does not establish compatible reactions within a deformable
mat or carpet; the calculation does not solve shear transfer, peeling, pressure
or coupled layer deformation.

There are **25,920 new linear-program solves**: eight interface/state groups
for mats, four for hardwood and eight for carpet, each with 1,296 loads. For
each feasible solution the solver independently recomputes force/moment
balance, nonnegative normals and circular-friction bounds. For infeasible
solutions, a separate analytic screen distinguishes impossible resultant
friction or support-hull conditions from failures of the inscribed 16-ray
friction polygon alone. A polygon-only failure is not proof that the exact
circular friction cone is infeasible.

## Reproduce and inspect the results

The [runner](../fea/round_floor_surface_assessment.py) reads the current
[insert-floor mass/load evidence](../fea/results/round-insert-floor-v1.json.gz),
checks its source identities, runs the new cases and refuses to overwrite an
existing result:

```sh
uv run python -m fea.round_floor_surface_assessment \
  --output fea/results/round-floor-surfaces-next.json.gz
uv run pytest -q tests/test_round_floor_surface_assessment.py
```

The resulting compressed JSON contains assumed inputs, translated wrenches,
actual retained support polygons, every witness or failure, per-group counts
and residual checks. The [completed report](../fea/results/round-floor-surfaces-v1.json.gz)
contains all **25,920 new solves**. Maximum independent witness residuals were
2.73 × 10⁻¹¹ N in force and 3.73 × 10⁻⁸ Nmm in moment, within the recorded
per-case tolerances.

## Results

Counts below are out of 1,296 loads per row. For mats and carpet, a “witness”
requires a feasible solution at **both** interfaces for the same load. A proven
failure means at least one interface fails an analytic necessary condition.
This joint counting does not turn independent witnesses into a coupled-layer
compatibility solution.

| Surface and state | Witnesses | Analytically proven failures | Additional polygon-only failures |
| --- | ---: | ---: | ---: |
| Mats, nominal and all supports | 1,296 | 0 | 0 |
| Mats, degraded lower friction | 878 | 288 | 130 |
| Mats, left rear foot unavailable | 709 | 587 | 0 |
| Mats, right rear foot unavailable | 733 | 563 | 0 |
| Hardwood, nominal and all supports | 1,296 | 0 | 0 |
| Hardwood, degraded friction | 533 | 720 | 43 |
| Hardwood, left rear foot unavailable | 711 | 585 | 0 |
| Hardwood, right rear foot unavailable | 735 | 561 | 0 |
| Carpet, nominal and all supports | 1,296 | 0 | 0 |
| Carpet, degraded lower friction | 533 | 720 | 43 |
| Carpet, left rear foot unavailable | 711 | 585 | 0 |
| Carpet, right rear foot unavailable | 735 | 561 | 0 |

Under the nominal assumptions, all three surfaces provide the tested static
witnesses. The weakest interface governs degraded friction: the mat underside
at μ = 0.12 proves 288 loads impossible; μ = 0.10 proves 720 for the hardwood
or carpet underside. The remaining polygon-only failures are not claimed as
exact circular-cone impossibilities.

Losing a rear foot produces support-hull failures even at nominal friction.
The higher-friction mat assumptions do not prevent that failure. At full
support, the minimum normal-resultant margin is 86.381 mm at the upper surface,
84.950 mm below the 19 mm mat, and 85.628 mm below the 10 mm carpet. The added
layer height therefore affects overturning even when both interfaces have
adequate assumed friction. In rear-foot-loss cases the worst margins become
negative by roughly 0.93–0.95 m; these indicate impossible static support under
those cases, not predicted physical travel or deformation.

These simulations can compare conditional surface/contact assumptions and
identify failures under them. They cannot select a reliably safe floor product
without knowing actual floor finish, mat/backing construction, interface
condition, flatness and attachment. They also do not address subfloor strength,
local indentation, dynamic climbing loads or unresolved frame/connection gates.
