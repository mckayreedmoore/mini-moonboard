# Attempt04 diagnostic replay, attempt01

## State

Completed as a bounded diagnostic; see [RESULTS.md](RESULTS.md). The runner
stopped after 1,021.04 seconds without a new accepted state/monitor block for
600 seconds. Docker exit 137 followed the stop request; `OOMKilled=false`.
The one accepted state remains below the diagnostic floor. All 44 frozen
inputs match; 44 complete convergence rows are audited, with an unresolved
CONTACT/CEL-only iteration-27 tail. Mechanical and joint acceptance are false.

## Frozen inputs

This folder contains exactly 44 byte-verified copies listed in
[`input-copy-manifest.json`](input-copy-manifest.json). Their hashes match the
attempt03 input binding and the originals remain in attempt03. The copied
`README.md` and `attempt03-runner.py` are two of those frozen inputs; the new
runner is [`attempt04-runner.py`](attempt04-runner.py).

The runner also checks the source attempt03 execution and output hashes, the
attempt03 force freeze and readiness records, the current monitor source, and
the pinned 2.23 manual. It rejects modified or missing frozen inputs and any
preexisting replay output.

## Launch gates

Before creating the solver container, the runner requires both coupon02 JSON
records to report `PASS`, binds the verifier to the exact execution hash, and
checks the coupon used the pinned diagnostic image and binary. It also requires
numerical-output equivalence, trace alignment, a stopped coupon container,
exit code 0, and `OOMKilled=false`.

The runner verifies build-attempt02's image and binary pins, checks the image
ID and binary SHA-256, and scans host and Docker processes twice. The last
scan runs immediately before solver launch and must find zero active solvers.
The checked observations and coupon/build record hashes are stored in the
launch gate and execution record.

## Frozen run bounds and interpretation

The solver uses the unchanged attempt03 deck, geometry, material, load,
contact, and control inputs in the pinned image
`sha256:1cc1d52946c5acddc9d4eeaf1dd1bf0bc4d3f564eb1c264f5d29b67c6386b7fa`,
with `/usr/local/bin/ccx-attempt04-diagnostic-2.23`. The bounds are 2 CPUs,
12 GiB memory, 3,600 seconds wall time, and 600 seconds without a new accepted
`.sta` increment or monitor block. The sampled 2 GiB CEL and 16 MiB stdout
guards request a stop; both are soft limits polled every 2 seconds.

The source audit found that `CONVERGENCE` is emitted for every completed
iteration, while `CONTACT` is emitted only when execution reaches the later
iteration contact-count branch. Attempt03 has 40 completed `.cvg` rows, which
imply 40 expected `CONVERGENCE` events and 38 expected later-iteration
`CONTACT` events in a fully instrumented replay. Attempt03 itself had no such
diagnostic instrumentation. Do not require equal event counts or interpret the
first iteration as a contact-count comparison. Fresh run counts may differ at
the stop point. The runner records event keys against completed `.cvg` rows and
flags an incomplete terminal line separately without trimming captured files.

This is an output-only convergence diagnostic using attempt03's analyst-chosen
1 N under-floor history. It cannot establish a physical response, load history,
equilibrium, or joint acceptance. Acceptance fields remain false.

## Launch record

The parent started the bounded replay with this command:

```bash
python3 docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/\
ordinary-external-force-transient-attempt04-diagnostic/replay-attempt01/\
attempt04-runner.py run \
docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/\
ordinary-external-force-transient-attempt04-diagnostic/replay-attempt01
```

The captured command and limits are in [`execution.json`](execution.json).
The terminal container exit, OOM state, stop reason and native output hashes
are captured there. The independent [trace audit](trace-audit.json) and
[result](RESULTS.md) preserve the unmatched iteration-27 tail. This directory
must not be reused for another run.
