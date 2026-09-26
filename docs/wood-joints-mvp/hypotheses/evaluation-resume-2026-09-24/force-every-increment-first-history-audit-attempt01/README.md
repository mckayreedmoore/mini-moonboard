# Early force-driven work and impulse audit

The first two accepted increments, at 0.001 and 0.002 s, have complete
monitor and native-work records in this immutable output prefix. Neither
increment has a rejected attempt. The live run continues separately; this
is not its terminal outcome or a contact-force audit.

Reconstructed cumulative applied-force work at 0.002 s is
1.1834758553228786e-5 N mm, compared with the native value 1.183476e-5 N mm.
The residual is -1.4467712e-12 N mm against a reported output-print bound of
1.8912754e-11 N mm. Both accepted states agree within their reported bounds.
This confirms that the force-driven formulation includes the applied work
in the early native records. It does not establish complete energy closure,
time accuracy, contact seating or joint acceptance.

The scalar force-pattern impulse is 8.9e-5 N s through 0.002 s. Exact
integration of the piecewise-linear amplitude and endpoint trapezoids agree
on these two intervals, whose endpoints happen to coincide with ramp knots.
That agreement cannot be transferred to later adaptive increments that cross
knots. This scalar coefficient multiplies the frozen nodal force pattern;
it is not a net force vector or a transmitted contact impulse.

Each output was copied only through its size at open. The files are not an
atomic capture of one instant. Snapshot hashes and sizes are recorded in
[snapshot.json](snapshot.json), and the adapter checks all 27 source input
artifact hashes before using the existing history evaluator. It reads no
live outputs. The [report](report.json) has SHA-256
`fad4f7c2256de031503f5ffdd72e15747293a72132ae670cc5cf1ed1abce240f`.

From the repository root, reproduce with:

```sh
PYTHONPATH=. .venv/bin/python docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/force-every-increment-first-history-audit-attempt01/audit.py
```

[Independent review](independent-review.md) reproduced the input checks and
work/impulse arithmetic without discrepancies. No geometry, physical load definition,
criterion status or candidate selection changes follow from this audit.
