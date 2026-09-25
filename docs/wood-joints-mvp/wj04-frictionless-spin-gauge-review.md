# Zero-preload frictionless spin-gauge review

Status: bounded mechanics-method review, 2026-09-24. This note derives a
candidate way to distinguish washer axial spin from load-bearing free modes.
It does not change the contact fragment, add restraints, validate a CalculiX
implementation, or accept a response result.

## Scope and current model

The proposed WJ04 patch contains five timber and 32 separate metal bodies.
Its current contact contract declares 76 unilateral, frictionless pairs:
four wood/cleat-host faces, sixteen bolt/wood-bore patches, thirty-two
hardware face seats, sixteen bolt/washer-bore patches, and eight
root/nut-bore radial patches. Preload is zero. The contact fragment does not
yet contain materials, restraints, loads, engagement, or a solver step. See
the [contact contract](../../fea/wood_joint_patch_contact_contract.py) and
[representative response contract](representative-unit-response-contract.md).

Each of the sixteen washers is a separate annular-cylinder body. Its two
bearing interfaces are planar and compression-only; its bore pair is
cylindrical and radial. There is no friction, tangential tie, washer-edge
contact, or direct washer load in the current contract. The C3D10 solid nodes
have translations only; a washer spin appears as a coordinated translational
field. This supports an ideal-continuum spin candidate for each washer. It
does not establish an exact null mode in the finite-element contact
discretization.

## Continuum derivation

For one washer with axis origin `c` and unit axis `e`, define the
unit-angular-displacement field at every washer point `x` as

```text
g(x) = e × (x - c)
```

and set `g = 0` on every other body. This is an infinitesimal rigid rotation
of that washer about its own axis. Its symmetric displacement gradient is
zero, so it produces no linear-elastic strain energy. At a frictionless
contact point, the first-order change in normal gap is

```text
δg_n = n · (g_washer - g_mate)
```

For an axial face, `n` is parallel to `e` and
`n · (e × (x - c)) = 0`. For a coaxial cylindrical bore, `n` is radial and
is again orthogonal to `e × (x - c)`. The same result applies to an inactive
gap: an exact annulus keeps its bore radius and face position under finite
rotation about its axis. Normal contact pressure also does no virtual work in
this direction. Therefore, in the ideal continuum model,

```text
K g = 0,  C_active g = 0,  f · g = 0
```

where `K` is the elastic-plus-contact tangent, `C_active` is the active
normal-compatibility operator, and `f` is applied load. The last equality is
equivalent to zero generalized torque about this washer axis. In this limited
case, the angular coordinate is a symmetry gauge: choosing its representative
does not supply physical stiffness or torque.

That result is specific to spin about the washer's axis. It does not cover
washer translation, washer rocking, another body's spin, or any mode that
changes a normal gap, contact footprint, or force path.

## Tests required before quotienting a discrete mode

Classify the mode as `SYMMETRY_GAUGE_CANDIDATE_UNVERIFIED` until each check
below passes at frozen, reported tolerances. The current contact normal audit
is an ownership/orientation screen; its radial-alignment allowance alone is
not an invariance tolerance.

1. **Bind the candidate.** For each washer, record the exact body and physical
   bolt ID, axis origin/direction, mesh and contact-surface hashes, steel
   material scenario hash, and the exact contact-pair IDs. Confirm that all
   washer connections remain frictionless and normal-only and that no applied
   load, external restraint, tie, spring, preload, torque, or other coupling
   acts on that washer.
2. **Check rigid-body kinematics.** Construct the nodal generator
   `g_i = e × (x_i - c)` on that washer and zero elsewhere. Verify zero
   elastic strain under the generator and evaluate its residual in every
   active normal-contact row. Report each row residual, its scale, the
   normalized `||K g||`, and the Rayleigh quotient `gᵀ K g / (gᵀ g)` from
   the actual active-set tangent. A body-level rigid-mode rank audit is useful
   for screening but cannot replace this flexible-mesh tangent test.
3. **Check the contact orbit.** At the undeformed state and each active
   contact state used by a case, rotate the washer about its bound axis through
   a frozen set of positive and negative phases. Re-evaluate the discretized
   gaps, active contact area, contact normal work, and integrated contact
   wrench without changing any other input. Compare against predeclared
   tolerances. Exact annular CAD geometry is necessary but is not sufficient:
   a non-axisymmetric surface mesh or contact quadrature can break continuous
   spin invariance.
4. **Check load orthogonality.** For every signed case, compute the applied
   generalized torque `fᵀ g` and the summed contact torque about the washer
   axis. Both must be zero within frozen force/moment accounting tolerances.
   Do not infer zero torque from an absent `RF` value; CalculiX does not report
   forces induced by multiple-point constraints as ordinary nodal reactions.
5. **Check output invariance.** With two independently defined spin gauges
   (or two mesh-phase representatives), compare wood and bolt displacement
   fields, interface six-wrenches, contact resultants/opening, and strain
   energy. Compare washer stresses after mapping each result back through the
   inverse spin. A change in an observable beyond the frozen tolerance means
   the discrete mode is not an accepted gauge.
6. **Reconcile nullity.** After the global six-scalar patch gauge, determine
   the full nullspace and project it onto the span of verified washer-spin
   generators. Report the candidate-spin rank and all residual null modes
   separately. A basis vector can mix modes, so classify the subspace by
   projection rather than by inspecting one arbitrary eigenvector. Any
   remaining translation, rocking, opening, axial-engagement, or other
   load-bearing mode stays `FREE_MODE_PRESENT`.

No numerical thresholds are selected here. Freeze absolute and normalized
residual, contact-state, and output tolerances before the eventual solve.
Preserve per-washer values and failed checks; do not report only a pass flag.

## Exact gauge form and boundary

If the checks establish an exact null direction and an independent coordinate
is needed to make the linear system nonsingular, the mathematical quotient is
`V / span(g)`: remove one coordinate for that one washer and no physical
deformation mode. A transparent linear gauge is the homogeneous scalar
condition

```text
Σ_i [e × (x_i - c)] · u_i = 0
```

over that washer's solid-node translations only. It fixes the projection onto
the spin generator; it does not attach the washer to another body. Its
constraint reaction/generalized torque and work must be reconstructed and
reported as zero within the frozen tolerance. The mode count removed must
equal the verified independent spin rank. Do not implement this gauge until
the kinematic, contact, load, output, and full-nullspace tests pass.

The pinned [CalculiX 2.21 manual](../../fea/generated/connection/ccx_2.21.pdf),
SHA-256 `16b6bab5a3f1a40a21fff62379f95c804a58d93758ab2e9a489b18d911dc20c8`,
states in §6.7.1 (printed p. 212) that rotational nodal DOFs are available
only for beam and shell elements. §6.7.2 (p. 212) and §7.55 (pp. 492–493)
describe linear multiple-point relations through `*EQUATION`. Those sections
establish relevant input syntax, not that this particular gauge is numerically
null, reaction-free, or solver-validated. A local 3-2-1 reference-frame gauge
also does not remove independent washer spins.

## Modes that remain physical

- In-plane washer translation before its radial bore clearance closes is
  distinct from rotation: it changes the washer position, clearance, and
  potentially the finite seat footprint. Do not quotient it. If that direction
  remains unrestrained under a case, preserve the free-travel/mechanism result;
  a separately named displacement-controlled seating case must report its
  imposed motion, reactions, and work.
- Washer translation normal to a seat, rocking, or opening changes normal
  gaps and pressure distribution; it is part of the physical contact response.
- Bolt/wood-bore travel within open radial clearance and axial bolt/nut motion
  without a bound thread-engagement law remain separate physical mechanisms.
  A radial-only root/nut cylinder cannot carry axial force.
- Any nonzero generalized washer torque, frictional/tangential contact,
  non-axisymmetric washer geometry/material, external coupling, or
  mesh/contact phase sensitivity invalidates that washer's spin quotient.

Only a verified spin gauge can be removed from the nullspace count. It cannot
convert an under-supported signed load into a valid response, close a physical
clearance, or qualify stiffness, resistance, capacity, or hardware.
