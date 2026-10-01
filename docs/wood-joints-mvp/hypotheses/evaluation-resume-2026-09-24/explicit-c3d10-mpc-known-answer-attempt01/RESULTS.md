# Explicit C3D10 constraint-mass known answer

September 27, 2026. The direct representation passes the frozen known answer.
The equivalent representation with a physical dependent DOF fails. Both native
runs completed normally; this is a measured method failure, not a failed input
read, timeout, or physical joint failure. No current-joint run or acceptance
follows from this result.

## Execution and observations

The parent froze 14 reviewed files and ran the cases sequentially with pinned,
unmodified CalculiX 2.23. Each used one CPU, a 1 GB memory limit, no network, and
a 60-second timeout. Direct completed in 0.82035 s and mapped in 0.73793 s;
both exited zero without OOM. Parent readback verifies all 14 frozen files and
all 16 native output hashes, including matching per-case execution records.

Each case has 100 complete FRD increments from 0.001 to 0.1 s, matching DAT
times, physical U/V/RF coverage on all ten nodes, and the requested scalar
mass/volume/energy records. STA and CVG contain no numeric iteration rows, as
the source review predicted. The native warning that explicit integration
ignores the requested initial increment is expected: the reported volumetric
stable increment is 0.2558639 s, and the maximum-increment input caps the
selected increment at 0.001 s. No mass-scaling or spring-scaling signal occurs.

| Observation | Direct | Physical-dependent mapped |
| --- | --- | --- |
| Frozen aggregate result | PASS | FAIL |
| Largest physical U1 error against `t²/2`, mm | 8.67e−19 | 0.005001278478 |
| Largest physical V1 error against `t`, mm/s | 0 | 0.10005084387 |
| Final controller U1, expected 0.005 mm | Not present | 0.001252579 mm |
| Final native ELSE, expected zero | 1.488188e−33 N·mm | 2.493604e−6 N·mm |
| Final native ELKE, uniform-motion reference 0.005 N·mm | 0.005 N·mm | 0.006641083 N·mm |
| Final applied-force work, uniform-motion reference 0.005 N·mm | 0.005 N·mm | 0.004596484914 N·mm |
| Reported physical mass | 1 tonne | 1 tonne |

At the first time, mapped `V1/t` is approximately
`[1, 0, 0, 0, 1, 1, 1, 1, 1, 1] mm/s²`, and controller displacement is
one-quarter of its rigid-motion reference. The separately computed physical
lumped momentum divided by this first time is 0.9194635217 N, compared with
the 1 N applied load. The source-derived diagonal-only initial prediction is
0.9194635366 N. This close finite-first-step correspondence supports the
diagnosed mass-coordinate mechanism; it is not an exact instantaneous
acceleration measurement or a prediction of the complete later history.

## Interpretation limits

The full transformed mass oracle preserves uniform acceleration under the
invertible coordinate substitution. The native mapped result does not. The
failed physical-motion and controller-motion gates are much larger than
output rounding and do not depend on the energy-output interpretation.
This result does not qualify the current mass-bearing shaft-pivot nut fits
for explicit dynamics. Changing only the external force ports would leave
those internal constraints in place.

The frozen mapped-equation diagnostic also fails its 1e−9 mm absolute gate:
its largest residual reconstructed from printed DAT values is 1.476e−9 mm.
A separate parent decimal-place check finds all 100 residuals within the sum
of their printed-value rounding bounds. Retain the frozen failure; do not
present it as independent evidence that the native equation was violated.
It does not explain the much larger physical-motion discrepancy.

Native ELKE integrates the interpolated continuum velocity field. After
nonuniform mapped motion it is not the kinetic energy of the declared lumped
nodal masses. The parent's independent raw-DAT calculation gives final lumped
physical kinetic energy 0.004593985098 N·mm. Its sum with ELSE is close to
the applied-force work. Therefore subtracting native ELKE from that work does
not by itself demonstrate energy creation. The uniform-motion ELKE known
answer still fails, consistently with the observed incorrect motion.

The subsequent [actual nut-chain source review](../explicit-current-coupling-feasibility-attempt01/README.md)
rules out controller-first ordering with the current `*RIGID BODY` cards:
that dependency graph triggers the pinned explicit mixed-MPC prohibition.
It also identifies an untested stable-increment risk from the active
zero-density nut solids. No alternative representation is selected or
applied. The carriers cannot silently be replaced with elastic springs or
a different rigid-motion assumption. No new joint or coupon run is selected.

## Evidence

- [Frozen input manifest](input-freeze.json): `b83aed658ff4e1d9508eb5f76ff2eaacc5f9618f275fb1afb71c2306258a2e31`
- [Native execution](execution.json): `3651d84181b5daaf31263dca8c5b8bdcdf44ef2a65f44212cfebeeb6f4c64011`
- [Frozen verifier result](verifier.json): `3b6fe7db7c3175baa385f647921d4d9a400ef8a627a491452be143bc1163bed4`
- [Independent input/source review](independent-preflight.md), [parent full-mass oracle](parent-oracle.py), and [parent raw-DAT calculation](parent-raw-audit.json).

The completed [independent post-run review](independent-review.md) confirms
the raw-output inventories, motion failure and energy distinction; its SHA-256
is `0d66250a11076981b8e0a6356d6e7399ea52a4876662c55e6a08da9b0e4404b4`.
All structural, current-joint, work/energy-qualification and release
acceptance flags remain false.
