# Independent static regression output review

I read the frozen capture without changing packet inputs or rerunning the
solver. The frozen input SHA-256 is
`73f32786bf6dee6c88e78f8e3d4e24f67afb9548225868fd10850c77e27298ab`; the
input-freeze SHA-256 is
`5d0c1a37d39b66bf9c3e04eb2b8275ef95a930dc17aa6d120ac815ee5d888cc8`, and the
native execution record SHA-256 is
`ca546ced71aa2e9a22e59edf3d29523339eb5090a94dfd75b758260b06ae8acc`.
The recorded container exited with code 0, was not OOM-killed, completed in
0.317 seconds, and emitted 1,734,725 bytes. The capture is a completed native
run; its regression verification fails.

I reused the packet verifier's strict FRD normalization, legacy-event,
trace, and CVG parsing/coverage functions. Five of the six required byte-exact
outputs match the baseline: `coupon.12d`, `coupon.cel`, `coupon.dat`,
`coupon.sta`, and `spooles.out`. `coupon.cvg` has the same 16 state identities,
1586-byte length, and contact counts, but is not byte-identical. Exactly five
late-iteration `CORR. DISP` values differ:

| State (step/increment/attempt/iteration) | Captured | Baseline | Difference |
|---|---:|---:|---:|
| 1/2/1/2 | 0.3195E-09 | 0.3194E-09 | +1.0E-13 |
| 1/3/1/2 | 0.2538E-10 | 0.2533E-10 | +5.0E-14 |
| 1/4/1/2 | 0.1231E-12 | 0.1556E-12 | -3.25E-14 |
| 1/5/1/2 | 0.8063E-10 | 0.8077E-10 | -1.4E-13 |
| 1/6/1/2 | 0.9210E-09 | 0.9209E-09 | +1.0E-13 |

The two FRDs have exactly one `1UTIME` record each. `ResultsForLastIterations.frd`
matches after replacing only that clock token. `coupon.frd` does not: after the
same normalization, 288 data rows differ across eight `FORC` field blocks.
The differing rows are force records; the FRD `DISP` and `CONTACT` blocks and
all other FRD lines match. The force components in the differing rows are
near zero (maximum absolute captured/reference component about `1.624E-12`,
largest component difference about `2.461E-12`). This identifies the changed
output field and scale; it does not establish why those values changed.

The captured `solver.stderr` is byte-identical to the empty baseline stderr;
stdout contains the normal completion marker. All 24 inherited attempt04
event records match the baseline lines, order, and digest: 8 contact-count
events and 16 convergence events. The trace parser accepts 1,680 finite
`CCXPT_MAP` rows and 1,680 finite `CCXPT_TRIAL` rows, with no
`CCXPT_UNMAPPED` rows; all map rows have nonzero native `isol`. Trial rows
cover all 16 captured CVG identities, exactly match each captured native
contact-element count, and have unique element and Gauss-point IDs within
each state. The count pattern is 56 rows in each of the two first-increment
states and 112 in each of the other fourteen states. These checks establish
trace coverage, not same-state mapping, contact-force qualification, or
mechanical acceptance.

Thus the fail-closed result is supported: strict CVG byte equality fails, and
the normalized `coupon.frd` comparison also fails. The observed FRD differences
are confined to near-zero force records; the DAT, displacement/contact FRD
fields, and inherited gate events show no other recorded output change in
these comparisons. No causal explanation follows from that observation.

There is also a comparison confound: the frozen baseline execution used
`OMP_NUM_THREADS=2`, `CCX_NPROC_EQUATION_SOLVER=2`, `--cpus 2`, and `--memory 4g`
with image `sha256:1cc1d52946c5acddc9d4eeaf1dd1bf0bc4d3f564eb1c264f5d29b67c6386b7fa`.
This capture used one thread/solver process, one CPU, and 1 GiB, with the
trace-build image `sha256:f00deed9be383c1095cdc03a1556d00cf8982f54100217a05ffae079e8a3bb36`.
That mismatch does not explain the differences, but it prevents attributing
them to the diagnostic patch alone. Preserve this run and its strict failure;
the discriminating follow-up is a fresh, serialized old-versus-new comparison
on the same frozen input with matched execution limits and thread settings,
retaining the byte, one-clock-token, event, and trace-coverage gates.

This review does not qualify force, mechanics, or the current joint.
