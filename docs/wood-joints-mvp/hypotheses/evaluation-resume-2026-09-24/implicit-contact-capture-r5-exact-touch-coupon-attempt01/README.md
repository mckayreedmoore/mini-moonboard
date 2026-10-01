# R5 exact-touch contact-capture known-answer — attempt 01

## Scope

This is a parent-owned, single-case runtime method check for the reviewed
CalculiX 2.23 output-only capture patch. It uses the two-body C3D10 exact-touch
coupon and its pre-existing, source-pinned upstream 2.23 reference output. It
does not use current candidate geometry, loads, or materials; it does not
select or launch a current-joint case and cannot accept any of the 47 criteria.

The owner authorized native method checks after review of the current revised
model. The parent reviewed the r5 patch/build/offline-control packet before
preparing this freeze, checked that no native solver was running, and reserved
the serialized native slot for this one coupon. The input, rosters, binary,
patch, source archive, run limits, expected outputs, and acceptance tolerances
are frozen in `input-freeze.json` and `readiness.json` before execution.

## What this run can establish

The check compares the patched solver's existing `.dat`, `.frd`, `.cvg`, and
`.sta` files byte-for-byte against the pinned unmodified 2.23 run. It also
validates the capture stream's source-face census, state joins, accepted
iteration links, and generated-spring force/energy summary against the
coupon's independent pair-output and analytical known-answer records.

The output patch captures only the nonlinear-loop contact regeneration. The
pre-loop seed scan remains excluded. Passing this coupon does not prove
runtime geometric-search completeness, a current-joint result, a general
contact-history law, wood-joint resistance, or whole-model energy balance.

The frozen preflight also checks the pinned CalculiX 2.23 manual, source/build
review, source archive, patch, binary, build manifest, capture contract,
contact rosters, known-answer record and all four upstream standard-output
hashes. The runner refuses a changed input, existing attempt output, an active
visible CalculiX process/container or a reused container name. The post-run
verifier checks the five accepted times, standard-output byte parity, capture
structure/bindings, compression slave resultant and stored contact energy. It
preserves a machine-readable failure result.

## Reproduction

After the parent creates the frozen readiness record, run once from the
repository root:

```sh
python3 docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/implicit-contact-capture-r5-exact-touch-coupon-attempt01/run.py
python3 docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/implicit-contact-capture-r5-exact-touch-coupon-attempt01/verify.py
```

The runner uses the pinned local r5 image by digest, with network disabled,
one CPU, 1 GiB memory, a 60-second wall limit, and bounded output. It refuses
to overwrite any prior output. The verifier preserves failures and writes no
solver input or mechanics data.

## Status

The frozen preflight, runner, verifier, pinned source/build review and offline
controls passed before execution. The parent ran this method coupon once on
2026-09-28 UTC (2026-09-27 local). The container returned exit code 139 after
0.332 seconds without timing out. Step 1 converged and was accepted; output
then entered step 2 and stopped. The standard `.cvg`, `.dat`, `.frd`, and `.sta`
files are incomplete and do not match the pinned unmodified reference. The
verifier recorded `FAIL_R5_EXACT_TOUCH_METHOD_COUPON`.

The capture has valid `RUN_BEGIN` bindings and `RUN_END` values of zero
generations, zero face rows, 112 candidate-point callbacks, zero trials, zero
iteration links, no overflow, a write/validation error, and `complete=0`.
Independent source review confirmed that the patched call passes `&ntie` to a
sink parameter expecting `ITG *`; within `nonlingeo`, `ntie` is already an
`ITG *`. The resulting pointer-level error fails the generation tie-count
guard before `GEN_BEGIN`. The review also confirmed that `nonlingeo` is called
once per step and the inserted `ccxcap_finish_()` runs at its end, closing the
capture after step 1. These findings explain the missing generation records
and early footer, but do not establish the cause of exit 139. No core or
backtrace is available, so the crash site remains unresolved.

This is a failed method-coupon implementation check only. It used no current
joint input and accepts none of the 47 criteria. Preserve this attempt and its
outputs unchanged. A new attempt must correct the pointer level and job-scope
finalization, add offline tests for valid/invalid tie counts and multi-step
capture lifecycle, pass independent source/build review, then receive a fresh
parent readiness record before one serialized coupon run. If exit 139 remains,
capture bounded crash diagnostics on that new coupon. Do not prepare or run a
current-joint case from this result.
