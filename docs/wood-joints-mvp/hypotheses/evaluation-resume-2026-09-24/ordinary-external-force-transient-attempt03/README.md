# External-member balanced-force transient, CalculiX 2.23 — attempt03

## Decision, observation, next step — 2026-09-27

**Decision:** Capture generated contact-element topology and last-iteration
motion for the same bounded diagnostic as attempt02.

**Observation:** Attempt02 retained its exact 42-file freeze and produced only
one accepted state at 0.001 s. The solver exited with code 255; the cause is
unknown. It did not reach the frozen diagnostic force or energy floors.

**Next step:** Repeat the exact force transient with output-only instrumentation
and a persisted terminal runner. Accept no response or joint claim from this
attempt. Preserve the source, geometry, contact, materials, force history,
constraints, step controls, convergence settings and motion stops.

## Exact instrumentation change

`pilot.inp` differs from attempt02 by one output-card header only:

```text
*CONTACT FILE,FREQUENCY=1
```

becomes:

```text
*CONTACT FILE,FREQUENCY=1,LAST ITERATIONS,CONTACT ELEMENTS
```

The data line `CDIS,CSTR,CELS` is unchanged. No geometry, material, contact,
load, constraint, timestep or convergence input changes. This output request
records contact-element topology for solver iterations and displacement data
for the last increment's iterations.

The paired [2.23 known-answer coupon](../contact-output-known-answer-attempt01/README.md)
passed output-path and baseline-equivalence checks: `.sta`, `.cvg` and `.dat`
were byte-identical; normalized `.frd` differed only in its generated UTIME;
all 16 CEL group totals matched their `.cvg` contact-element counts. The
instrumented coupon also wrote `ResultsForLastIterations.frd`. The coupon
verifies output mechanics only. It does not verify full-model convergence,
contact identity for every pair, physical response or joint acceptance.

The pinned [CalculiX 2.23 manual](https://www.dhondt.de/ccx_2.23.pdf),
pp. 435–436, documents the `LAST ITERATIONS` and `CONTACT ELEMENTS` output
parameters. CEL groups identify step, increment, attempt and iteration. They
do not contain contact forces or residual norms.

## Run bounds and interpretation

The explicit solver image, executable and binary hash remain pinned to 2.23.
The job is serial in the project sequence and limited to 2 CPUs, 12 GiB and
3600 seconds. A 600-second watchdog resets only after a new completed accepted
`.sta` row or a complete `PILOT_MONITOR` block. The runner also enforces the
frozen sampled stops: 1.3 mm force-dual travel, 5 mm maximum loaded-node motion,
and 0.05 rad controller rotation. A 2 GiB `pilot.cel` size guard is checked
every two seconds; it requests a stop at the next check, so it is not a hard
disk quota. Any stop kills the named container, confirms it is terminal and
hashes outputs.

The CEL audit compares iteration keys and element totals with `.cvg`, then
reconstructs candidate pair identity from ordered master/slave connectivity
and the frozen 35-pair manifest. The 2.23 coupon directly checks master-first,
slave-second C3D6 connectivity for one small pair. Full-model pair mapping must
be checked on the captured mesh; ambiguous records stay unresolved. Topology
changes do not establish chatter or its cause.

This is a bounded dynamic external-member diagnostic, not a static response,
capacity result or mechanical acceptance. `mechanical_acceptance` and
`joint_acceptance` remain false.
## Reproducible execution and audit

After the independent readiness record matches `force-freeze.json`, launch with
`python3 attempt03-runner.py run .` from this directory. The terminal audit is
`python3 audit_cel.py .`. It requires a terminal container record, both freeze
bindings, unchanged inputs, and hashed `.cel` / `.cvg` outputs.
