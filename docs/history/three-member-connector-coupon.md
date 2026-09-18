# Three-member lateral connector coupon

This numerical building block represents **one continuous bending bolt** with
three contiguous wood-bearing regions. Unlike two unrelated rim-to-ply point
springs, it couples the regions through the same bolt. It is not yet connected
to the frame and supplies no calibrated stiffness, load rating or revised plans.

## Formulation and units

The bolt is a straight, constant-EI Euler–Bernoulli beam. Each bearing region
has its own rigid transverse translation and rotation about its midpoint.
Independent region motion permits differential ply motion; no adhesive tie is
present. Distributed linear springs connect the bolt to the local motion of
each region, storing energy

`U = ½ ∫ EI (v″)² dx + ½ Σ ∫ k_i [v − u_i − θ_i(x − c_i)]² dx`.

Lengths and translations are mm; rotations radians; EI is N·mm². The foundation
input `k_i` is N/mm²: force per bolt length per slip. **It is neither NDS dowel
bearing strength in MPa nor a whole-connection point spring in N/mm**, despite
the bearing-strength expression also having N/mm² dimensions. A strength is
not an elastic stiffness merely because units coincide.

The implementation uses cubic Hermite beam elements and four-point Gauss
integration of foundation energy. The bolt ends are free. Internal bolt DOFs
are statically condensed, leaving a 6×6 matrix on three translation/rotation
pairs. Its reactions are work-conjugate forces in N and moments in N·mm.
The retained recovery matrix allows checking the bolt's own equilibrium and
the uncondensed energy, rather than trusting the reduced matrix alone.

Sign convention: `K q` is the **external generalized action needed to impose**
the region motions. The bolt/foundation action on those regions is `−K q`.
Keep that distinction when forming a wood-body free body; a positive work
matrix is not automatically a table of bolt-on-wood forces.

This is our explicit linear coupon formulation, not an AWC-prescribed
three-member allowable. Published bolt load-slip research distinguishes
deformation from yield theory; see
[Heine and Dolan](https://wfs.swst.org/index.php/wfs/article/view/1368).
That paper's two-member validation does not validate this implementation or
the current rim/two-ply connection.

## Checks completed

Three tests cover common rigid translation/rotation, matrix symmetry and
nonnegative energy, zero total force and moment, internal bolt equilibrium,
condensed/uncondensed energy equivalence, refinement and input rejection.
An independent closed-form affine-bolt foundation calculation checks the
large-EI limit. A 4/8/16-element-per-region refinement checks convergence for
the supplied numerical inputs. No fixture reaction is hidden in a restrained
bolt endpoint.

The 38.1/19.05/19.05 mm regression stack matches the nominal leg arrangement,
but the test's foundation values (100/80/80 N/mm²) and EI (3×10⁷ N·mm²) are
**numerical test inputs**, not selected material properties. The separate
dimensionless-sized rigid-bolt test is a mathematical limit check only.

```sh
uv run pytest -q tests/test_three_member_connector.py
```

The coupon and existing yield-kernel regression passed 17 tests. Ruff and
whitespace checks passed. Independent correctness, testing and architecture
reviews found no substantial issues; this is numerical implementation review,
not experimental or structural validation.

## Independent finite-bending check

A subsequent independent finite-bending check solves the continuous piecewise
beam equation with matrix exponentials. Its state is displacement, slope,
moment and shear, augmented by constant/axial-coordinate terms for each region's
linear imposed motion. It enforces zero moment and shear at both bolt ends,
propagates continuity across both material interfaces, and obtains each region's
external force/moment from shear and moment differences. It does not reuse
Hermite element matrices, Gauss integration or the condensation implementation.

All six independent member motions were checked for both the nominal-thickness
coupon and an unequal 20/30/10 mm stack with different bearing stiffnesses.
At 16 elements per region, every stiffness-column relative 2-norm error was
below 1e-5 against that continuous solution. This checks the supplied-input
linear mechanics away from the rigid-bolt limit; it does **not** validate the
physical foundation law or the neglected joint behaviors below. Both methods
share the stated Euler–Bernoulli/linear-foundation idealization.

The expanded coupon/yield regression passed 19 tests. A fresh three-scope
independent review found no substantial issues in the ODE comparison or force
sign convention; Ruff and whitespace checks remained clean.

## Before using it in frame decisions

Obtain an applicable directional wood-bearing load/slip basis and bolt section
properties, including thread/runout effects. Check beam shear deformation,
finite bearing regions and the rigid-region approximation against an independent
appropriate model or test. This coupon omits clearance/slack, nonlinear bearing,
yielding, axial force/washer action, friction, separation/contact, splitting,
group action and cyclic degradation. Positive/negative linear springs do not
resolve unilateral wood contact.

Frame integration must map both translation and rotation consistently, preserve
moments and independently balance each ply with its floor, rim-bolt and stitch
actions. Merely connecting these six DOFs to arbitrary mesh nodes is not a
qualified coupling. Until those steps are verified, retain the existing frame
and its [explicit release gates](current-review-guide.md); do not replace the
archived trial springs or attach capacities to this matrix.
