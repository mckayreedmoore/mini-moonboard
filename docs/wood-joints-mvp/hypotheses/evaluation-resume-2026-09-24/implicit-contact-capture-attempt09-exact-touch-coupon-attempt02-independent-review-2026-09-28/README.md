# Independent pre-run audit: attempt09 exact-touch coupon attempt02

Review date: 2026-09-28. **Outcome: no pre-run readiness is granted.** The
frozen inputs and current source/build/known-answer bindings passed this static
audit, but two launch-control gaps block the packet's stated bounded,
single-attempt execution claim. The runner remains fail-closed at the current
snapshot: this packet has no `readiness.json` or `authorization.json`, the
parent ledger has no reservation for
`T02-attempt09-exact-touch-capture-coupon-attempt02`, and the serialized slot
is idle. The review is not a run authorization.

## Verified scope

The 31 paths in `SOURCE-SHA256SUMS` rehashed successfully. The current script
hashes are:

- `run.py`: `f37400cb22c90c921ca999fef9eebd8ef91db81eacc9919cea56ccd7a9534f2f`
- `verify.py`: `5c25890243203d34333f590488ee4916deb70528baa2c46730059f5889f0e354`

The frozen coupon input matches its upstream reference byte for byte and has no
`*INCLUDE` card; the empty include-closure digest is correct. The reader's
seven run bindings match the freeze, the local reader copy matches the frozen
external reader, and both rosters bind the same input hash. The build manifest
and execution record agree with the freeze on source archive, patch, binary,
build manifest, and exact image ID. The host binary hash, source archive, patch,
build records, capture contract, upstream manual, parent review, and build
review all match their frozen hashes.

All four pinned standard outputs (`.cvg`, `.dat`, `.frd`, and `.sta`)
match the frozen baseline. The known-answer JSON and the prior work-fixture
result, review, verifier, and execution pins also match. The expected method
fixture keeps mechanical acceptance, joint acceptance, and native execution
authorization false. The current runner's `run_id` and
`authorization_sha256` fields satisfy the verifier's corresponding
`execution_scope` checks.

## Findings

1. **Blocking for the claimed output bounds:** the 5 MiB stdout/stderr and
   100 MiB aggregate-output thresholds are evaluated after `docker run`
   returns. `subprocess.run(capture_output=True)` buffers the Docker CLI
   output in the host process, and solver files are written into the bind mount
   without a disk quota. An over-limit run is marked failed afterward, but
   these thresholds do not stop memory or disk growth when a limit is crossed.
   The native capture writer does have a compiled 128 MiB cap; Docker also has
   the frozen 60-second, one-CPU, and 1 GiB memory/swap controls. Those controls
   do not make the log and aggregate-output thresholds hard limits. Enforce
   streaming termination and an output-storage cap, or describe these values
   only as post-run acceptance limits before granting readiness.

2. **Blocking for the claimed one-launch serialization:** the runner has no
   atomic process/run lock. It checks for a nonempty output directory and an
   existing fixed-name container, then copies input and starts the container.
   Two concurrent invocations can both pass the checks; the fixed Docker name
   prevents simultaneous name reuse, but `--rm` removes the first container
   after exit, allowing a delayed invocation that already passed preflight to
   start afterward against the same consumed ledger reservation. Parent-owned
   serialized coordination reduces this risk but the runner does not enforce
   at-most-one launch. Add an exclusive lock held across preflight, execution,
   and cleanup, or otherwise make reservation acquisition atomic.

3. **Nonblocking current-value consistency gap:** the freeze's
   `unique_container_name` currently equals the runner's hard-coded
   `CONTAINER`, but the runner does not compare the two. The present value
   agrees; a future frozen-name change would not control the launched
   container. Assert the equality before launch or use the frozen value.

4. **Post-run ledger handoff needs to be explicit:** preflight requires the
   ledger state `reserved_consumed`; `verify.py` later requires a
   `consumed_*` state. The runner does not update the ledger, and the
   README's two-command run/verify sequence does not document a parent-owned
   transition between those commands. The coordinator must perform that
   transition before verification, or the verifier must accept the intended
   consumed reservation state.

5. **Status wording will need refresh:** the packet README still says the
   independent pre-run review is being prepared. This report completes that
   review; its separate statement that readiness, authorization, reservation,
   and launch have not been issued matches the snapshot recorded here.

## Reproduction and limits

From the repository root, validate the 31 frozen source pins:

```sh
cd /home/mckay-linux/repos/mini-moonboard
sha256sum -c docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/implicit-contact-capture-attempt09-exact-touch-coupon-attempt02-independent-review-2026-09-28/SOURCE-SHA256SUMS
```

From this review directory, validate the report and source-manifest hashes:

```sh
sha256sum -c SHA256SUMS
```

This was a static, read-only pre-run audit. Neither `run.py` nor the
output-writing `verify.py` was invoked. No Docker command, coupon binary, or
native solver was run. The audit verifies artifact identity and control wiring;
it does not establish runtime behavior, method acceptance, or engineering
acceptance.
