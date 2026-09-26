# Independent review caveats for attempt 01

These corrections preserve the attempt-01 numerical result and its
`FIRST_STATE_WEAK_BOUND_CONSISTENCY_ONLY_NO_ANGULAR_PASS` status. They clarify
what its output estimate and source pins establish.

The reported inertial output-error quantity is a first-order estimate. Its
cross-product propagation includes terms proportional to `|x|·Δ(Ma)` and
`Δx·|Ma|`, but omits the bilinear `Δx·Δ(Ma)` contribution. It is not a
rigorous interval bound. Recomputing the component ratios from the stored
estimate and residual vectors gives approximately
`[898.7560518, 471.9420211, 333.4114586]`; the stored ratio field is slightly
different. The broad comparison remains about 333–899 times, and the weak
consistency-only conclusion is unchanged.

The frozen reconstruction snapshot reads CLOAD and RAMP_N from the ordinary
transient mass-case `pilot.inp`, SHA-256
`a9f891c92fed7eaa7e3b78f0656c5829d330a28a3df450ea7128b9ea52eb49c4`. That is
not the executed dependent-native `pilot.inp` (SHA-256
`7542af582f91215a3759292726211e15911387640b0f76514946681b8f623da3`). An
independent comparison found all 662 CLOAD rows and 101 RAMP_N points equal.
This explains why the reported load arithmetic is unchanged, while making the
source distinction explicit; the consumed mass-case deck is now included in
the source pins.

The linked full-mesh ACC proposal remains unintegrated into the active CCX
binary and has no native trajectory. Its extracted C helper was applied to a
separate fixture, compiled with warnings as errors, and exercised on two
synthetic acceleration blocks using the pinned C3D10 connectivity. That test
establishes emitter framing and node-map behavior only, not native solver or
mechanics behavior.
