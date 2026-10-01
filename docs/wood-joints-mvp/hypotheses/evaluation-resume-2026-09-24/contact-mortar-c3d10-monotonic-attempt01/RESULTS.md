# Monotonic contact discriminator result

**FAIL — both formulations at intermediate states.** Removing the preceding
opening step and reversal does not reproduce the all-state penalty pass from
the earlier fixture. Mortar also fails without that history. Penalty reaches
the correct final force and gap; mortar does not. No formulation is qualified
by this monotonic result, and no full joint run follows from it.

## Native execution and audit

Both frozen decks ran serially on the same unpatched, pinned CalculiX 2.23
binary. Each completed in approximately 0.420 s, exit zero, no OOM, no stop,
and ten accepted increments with no rejected attempt. Mortar records 22 CVG
iterations, maximum three; penalty records 20, maximum two. Complete stdout
iteration identities match CVG; final iteration counts match STA. The mortar
iteration-greater-than-14 override is never reached. Independent read-only review
by `coupon_gate_strategy` confirms every frozen/output hash, native terminal
record, iteration identity and numerical table below. Each case has ten complete,
finite FRD DISP, FORC and CONTACT datasets.

The [frozen verifier](verifier.py) includes the previously documented Fortran
omitted-E parser correction. Its [result](verifier.json) fails both formulations
at total time 0.2 on the unchanged analytical support-force gate. The native
runs were not repeated, and no tolerance was changed after execution.

## Direct native diagnostics

Force magnitudes below are the negated sum of top-face RF3 in DAT. Gap is mean
upper-minus-lower interface U3; the reference faces coincide. The acceptance
reference remains the predeclared linear series solution. The nonlinear
endpoint reference, 399.519872 N and -0.000998799680 mm gap, is explanatory only.

| Time | Linear force (N) | Mortar force (N) | Penalty force (N) | Mortar mean gap (mm) | Penalty mean gap (mm) |
| --- | ---: | ---: | ---: | ---: | ---: |
| 0.1 | 40 | 39.995198 | 39.995198 | -0.000099988 | -0.000099988 |
| 0.2 | 80 | 67.188000 | 72.873790 | -0.000327951 | -0.000271063 |
| 0.5 | 200 | 158.032441 | 150.888170 | -0.000918738 | -0.000990264 |
| 1.0 | 400 | 441.009199 | 399.519900 | -0.000533052 | -0.000998800 |

The earlier [opening/compression/reopening result][prior] remains unchanged:
its penalty control passed all 30 states. This one-step monotonic comparison
shows that the loading schedule affects intermediate contact response even
for penalty. Mortar's failure is not confined to the earlier reversal.
The fail-fast verifier does not independently certify endpoint-only acceptance;
its later-state values above are diagnostics from the same preserved DAT files.

The source gap-history screen identifies scaling of the current mortar gap
by relative step time as a strong candidate mechanism. It does not yet derive
the complete force history or explain the newly observed penalty intermediate
failure. Check the documented initial-overclosure ramp, displacement prediction
and contact gap updates before choosing another input or method. A converged
step or a correct penalty endpoint does not erase the all-state failure.

## Immutable identities

| Artifact | SHA-256 |
| --- | --- |
| Input freeze | `bedd253bb6f5561de034996189bdf2bf4c5883c2601e0474681c1e585c7e852e` |
| Execution | `571fd9aaf231c59ed0e3f7bdd3db5360f2e7baea9cba95c752e3b325b0ef9df3` |
| Verifier | `14cda77c2be147a5952f27d47d790e4495e320de25c22c54cf398b79f81a26bf` |
| Failed audit | `f2e0f0c8163343f5582be687b5217735ab9bf10309dc5c0344ad32b0b7a384d7` |

[Execution](execution.json) binds every native output hash, input deck, toolchain
and terminal state. [Parent review](parent-review.json) records static input and
independent verifier/readiness reviews. The original README, expected contract
and readiness record remain frozen at their pre-run state. No candidate geometry,
capacity, physical observation or release status changes.

[prior]: ../contact-mortar-c3d10-known-answer-attempt01/RESULTS.md
