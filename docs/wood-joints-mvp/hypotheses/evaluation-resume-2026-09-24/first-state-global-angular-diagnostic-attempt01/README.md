# First accepted-state global angular diagnostic — attempt 01

This freezes a first-state reconstruction for step 1, increment 1 at
`t = dt = 0.0005 s` from the instrumented native run. It is a bounded
consistency diagnostic only. The native execution later terminated with code
201 after the accepted state, so the full step and runtime remain failed and
mechanical acceptance is false.

The reconstructed full-mesh acceleration uses the alpha-zero Newmark relation
for `beta = 0.25`, `gamma = 0.5` and zero initial velocity/acceleration:
`a(1) = 2 v(1) / dt`. That acceleration is inferred from rounded FRD VELO for
all mesh nodes; the hook supplies direct native `accold` only on its 337-node
bolt-fit support. On those 337 nodes the reconstruction differs from the
hook by at most `1.94e-5 mm/s²`.

Using the frozen C3D10 four-point consistent mass operator on the 15
positive-density timber and steel bodies, the reconstructed inertial moment
about the global origin is `[5.6351593e-8, 8.7098937e-8, 4.5122840e-8]`
N·mm. The applied CLOAD moment is `[4.5622038e-10, -3.7828257e-9,
-4.5082378e-9]` N·mm; the sum of all 35 audited contact-pair moments is
`[-1.4859706e-10, 9.2987901e-9, 1.0968683e-8]` N·mm. Including the 24
authored fit-MPC contributions (`Cᵀλ`, with the physical constraint-force
sign handled in the balance) leaves residual
`[5.6045100e-8, 8.1626284e-8, 3.8708934e-8]` N·mm.

The first-order FRD binary32 and decimal-token error estimate in the inertial
moment alone is `[5.0370872e-5, 3.8522873e-5, 1.2906002e-5]` N·mm. Its
propagation omits the bilinear `ΔDISP × Δ(Ma)` term, so it is not a rigorous
interval bound. Recomputing the component ratios from the stored vectors gives
`[898.7560518, 471.9420211, 333.4114586]`; the stored ratio field is slightly
different. The broad comparison remains about 333–899 times, and this remains
only weak output-rounding consistency, not a resolved angular-momentum
closure or a complete angular pass. See
[`review-caveats.md`](review-caveats.md) for the independent review findings.

The DISP-token contribution to that first-state inertial-moment bound is only
`[1.31e-13, 6.06e-14, 7.08e-14]` N·mm. Full-precision current positions are
not needed for this state. For later states, recompute that position term from
each FRD DISP token and the full-precision inertial nodal-force vector; add a
position output only if that term becomes material to the chosen comparison
tolerance.

The snapshot reads CLOAD and RAMP_N from the ordinary transient mass-case
`pilot.inp` (SHA-256
`a9f891c92fed7eaa7e3b78f0656c5829d330a28a3df450ea7128b9ea52eb49c4`), which
is byte-distinct from the executed dependent-native `pilot.inp` (SHA-256
`7542af582f91215a3759292726211e15911387640b0f76514946681b8f623da3`). An
independent comparison found all 662 CLOAD rows and 101 RAMP_N points equal.
The consumed deck is now included in `source-pins.json` and `report.json`.
`report.json` records the values and source pins. The archived
`reconstruction.py.snapshot` is the short calculation used to inspect the
accepted state; run it from the repository root with
`.venv/bin/python <path-to-this-folder>/reconstruction.py.snapshot`. It uses
NumPy and reads the frozen inputs/outputs listed in `source-pins.json`. The
snapshot does not enforce the hashes at runtime; the listed hashes were
verified when this report was written. It performs no CAD or solver work.

The separate [all-node ACC proposal](../all-physical-acc-output-proposal-attempt01/README.md)
captures accepted native `accold` for every frozen mesh node in a separate
file. The full `results.c` derivative has not been integrated into the active
CCX build or run in a native case. Its extracted helper was applied to a
separate fixture, compiled with warnings as errors, and exercised against the
pinned mesh connectivity using synthetic acceleration values; see the
proposal’s [`independent-review.md`](../all-physical-acc-output-proposal-attempt01/independent-review.md).
