# Exact-touch penalty work/output fixture: result

The single frozen CalculiX 2.23 case passes its predeclared method gates.
Five DIRECT endpoints completed in 0.421 seconds with native exit 0, no
cutback, no timeout and no OOM. Their Newton iteration counts are 3, 7, 3,
5 and 2. Parent validation reproduces all ten frozen input hashes, all nine
captured native-output hashes and the passing verifier result. A separate
review of native evidence is pending.

## Work and stored energy

| Segment | Signed reaction work (N·mm) | Observed stored-energy change (N·mm) | Absolute difference (N·mm) |
| --- | ---: | ---: | ---: |
| Initial to open | 1.079e-12 | 2.328e-23 | 1.079e-12 |
| Open to exact touch | −1.079e-12 | −2.328e-23 | 1.079e-12 |
| Touch to compression | +0.99879975 | +0.9991998 | 0.00040005 |
| Compression to touch | −0.99879975 | −0.9991998 | 0.00040005 |
| Touch to reopen | −5.760e-18 | 0 | 5.760e-18 |

All signed segment, analytical-work and cumulative-work gates pass the frozen
`max(3e-6 N·mm, 5% of compared magnitude)` numerical screen. Reaction work is
calculated independently from printed top RF3 and U3. No contact energy is
inferred from a work residual.

At compression the upper and lower body ELSE values are each 0.3998398 N·mm,
and penalty CELS is 0.1995202 N·mm. Their sum is 0.9991998 N·mm against the
1.0 N·mm analytical reference. Each component and the combined endpoint pass
the inherited `1% of reference + 1e-6 N·mm` tolerance. Open and exact-touch
energies are numerically near zero; tiny signed negative body totals after
unloading are retained in the raw evidence and lie within the frozen absolute
allowance. They are not replaced with an inferred positive energy.

## Pair and mechanical outputs

The exact `SLAVE`/`MASTER` CF, CFN and CFS identities are present at all five
accepted states, with finite force and origin-moment components. Compression
CF and CFN are approximately `(0,0,399.5199) N` and origin moments
`(399.5199,−399.5199,0) N·mm`; frictionless CFS is zero. Projection of CFN
on the downward slave normal is −399.5199 N under the writer's tension-positive
convention. The largest exact-touch pair-force magnitude is 6.841e-16 N.
Open-area centroid/mean-normal diagnostics can be undefined and are kept
separate from the required finite resultants.

All inherited force, displacement-profile, interface-gap, compliance and SOF
checks pass. Every endpoint contains complete 54-node DISP/FORC/STRESS output,
with ten opposed section reports and five accepted state identities.

## Applicability and evidence

This qualifies signed trapezoidal work on this two-body path with explicit
touch breakpoints, penalty endpoint energy and pair-resultant output. It does
not qualify quadrature across an unresolved open-gap transition, a current-joint
absolute work floor, shared-edge MPC behavior, curved-bore onset, resistance or
any structural criterion. MORTAR was excluded; its CELS limitation is unchanged.
The current joint and all release/acceptance flags remain false. The frozen
README is the original preparation statement; this result and the execution
record govern the completed run.

| Artifact | SHA-256 |
| --- | --- |
| [Input freeze](input-freeze.json) | `9cf04eb2d38c5a82ddf050535a0a303043176bb17cedf76e09b328d961d9bcc4` |
| [Execution](execution.json) | `c399472c88fb5c225c7774159eec199a935af688d55c4b74d80b74df47ed6c05` |
| [Expected contract](expected.json) | `053039f39b33c5e3c1f1d1d19e88e8fa9967d6da7aea42fd9450bf80b56d1a26` |
| [Verifier implementation](verifier.py) | `f0a4684eee8895d8196206e7431b676cf8c4c76e384cd9c6dfac543de1eee30f` |
| [Verifier result](verifier.json) | `6becb6d9c4cc875bcb06379078e97f86c2108318ef3df76a20f6b3c8be693bcd` |
