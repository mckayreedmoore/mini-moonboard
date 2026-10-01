# External-member balanced-force transient, CalculiX 2.23

The owner-requested 2.23 development profile is used explicitly. The unrun
2.21 input in attempt01 is preserved; geometry and loading are identical.
The unchanged six-fixture comparison in calculix-2.23-upgrade-attempt01
reproduces the earlier method results. No joint result transfers between versions.

## Decision, observation, next step — 2026-09-27

**Decision:** Determine whether a bounded physical-inertia transient can
produce an auditable external-member response on the reviewed ordinary patch,
with the cleat and whole assembly free.

**Observation:** Static startup retained a cleat free mode. The pinned solver
failed the prescribed-MPC dynamic coupon, but balanced nodal loading passed
independent known-answer displacement, velocity and energy checks, including
a homogeneous free-controller case. That supports this loading formulation;
full-patch contact, inertia and engagement behavior still require evaluation.

**Next step:** Freeze and independently audit this input, run serially, retain
all accepted motion/contact/energy states, and recover applied work from actual
nodal force-motion pairs. Reconstruct external projected motion, cleat pose
and contact actions. Check dynamic equilibrium and energy before considering
rate/timestep comparisons or a quasi-static response claim.

## Bounds and interpretation

Keep source-bound attempt 09 mesh, materials, 35 contacts and nut-engagement
scenario unchanged. Remove the old global gauge and prescribed port equations
from the active include closure. Apply its exact n_plus dual force pattern to
the 86 external cap nodes only. Its unit resultant is +1 N on the rail and
−1 N on the principal in the frozen local N direction, with moments translated
to their remote caps from the common joint datum.

Ramp from zero to that pattern over .1 s using 201 tabulated quintic samples,
then hold .025 s. Alpha=0, original density, zero initial velocity, no added
damping or support. Initial dt=.001 s, maximum=.0025 s, minimum=1e-6 s.
This is a small diagnostic load, not a service demand or prescribed motion.

Stop at native completion/failure, 3600 s wallclock, no accepted monitor state
within 600 s, or the first sampled limit: |force-dual q|>1.3 mm, loaded-node
motion>5 mm, or nut-controller rotation>.05 rad. These are diagnostic bounds,
not predicted contact events or physical acceptance limits. Monitor sampling
does not bound unaccepted internal iterations. Stop the named container and
confirm its terminal state before hashing native output.

Record actual deformed-configuration applied moments as well as their initial
balance: fixed global nodal forces are dead loads, so their moments can change
as the assembly deforms. Keep this in the angular-momentum balance. The force
dual coordinate exactly pairs with applied nodal work; section resultants are
separate observations and do not supply all warping work by themselves.

Numerical diagnostic screens are frozen in force-freeze.json. A converged
state or bore contact does not qualify response, capacity, or MVP completion.

## Documentation

[CalculiX 2.23 manual](https://www.dhondt.de/ccx_2.23.pdf): Direct integration
dynamics, *DYNAMIC, *CLOAD, *AMPLITUDE, *NODE PRINT, *SECTION PRINT and contact
convergence. The [method review](../ordinary-solver-practice-review-2026-09-27.md)
and [force coupons](../force-port-known-answer-attempt01/RESULTS.md) give the
supporting observations and applicability limits.
