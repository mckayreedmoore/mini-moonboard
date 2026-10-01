# Attempt06 independent architecture and integration review

Verdict: **REQUEST_CHANGES** for the offline capture package. Four findings are
confirmed below. The highest-impact finding is an integration mismatch that
prevents an ordinary nonconverged native iteration from receiving its required
iteration link. This is a source review and standalone sink reproduction, not a
patched-solver build or native qualification.

The reviewed attempt06 `source-pins.json` SHA-256 is
`869b5d7121b8cea80e95f9d87de159f225ec1c1d9b1a0e327e8693bc0e5684c5`.
The patch SHA-256 is
`e98a5dd69aa1d992b18256a2cbd7dfedce6a2001b4af6085fdcac9c31ba8ba67`.
The complete input inventory, predecessor checks, and archive-member hashes
used for this review are bound in [input-verification.json](input-verification.json).
[SHA256SUMS](SHA256SUMS) binds this report and its evidence files. The assessment
applies only to those exact bytes.

## Confirmed findings

1. **P1 — The iteration-link hook reads an iteration counter after the native
   convergence routine advances it.** Criterion: lifecycle integration.

   [prepare_capture.py](../implicit-bounded-contact-capture-attempt06/prepare_capture.py)
   lines 540–544 insert the link after `checkconvergence()` in `nonlingeo.c`.
   The exact archived `checkconvergence.c` increments `(*iit)++` at line 874 on
   its ordinary no-convergence branch. The sink then requires
   `wjcc_iter == *iter` before emitting the link at
   [capture-sink.inc](../implicit-bounded-contact-capture-attempt06/capture-sink.inc)
   lines 611–621. A generation captured at iteration 1 is therefore compared
   with live iteration 2, returns without a link, and leaves `wjcc_pending=1`.
   The next generation sets the sticky error at line 404. A later seed call can
   also still see that pending state.

   The standalone probe applies exactly this native counter advancement after
   a complete map/corrected/trial lifecycle. It records
   `captured_iter=1 live_iter=2 pending=1 links=0 error=0`; the next generation
   ends with `RUN_END` reporting one link for two generations, `error=1`, and
   `complete=0`. The same fixture without advancement reports two links and
   passes the reader. See [probe-results.json](probe-results.json), probe
   `native-iteration-advance`, and
   [source-lifecycle-evidence.txt](source-lifecycle-evidence.txt) for the pinned
   caller and convergence source excerpts.

   The shipped harness calls the link before it changes `iter`
   (`tests/sink_harness.c`, lines 286–303), so its positive control does not
   represent this native boundary. Capture the pre-convergence iteration
   identity separately and pair it with the post-convergence outcome. Do not
   relax identity checking indiscriminately. Add an offline caller sequence
   that covers no convergence, acceptance, and cutback before considering
   native readiness.

2. **P2 — Cleanup removes a temporary file even when exclusive creation
   failed.** Criterion: publication ownership.

   The sink stores the sibling pathname and calls `fopen(...,"wbx")` at
   lines 172–178. If a file with that pathname already exists, the call fails
   without creating or acquiring it. Nevertheless, `ccxcap_finish_()` reaches
   `remove(wjcc_temp_path)` at lines 642–645. The same cleanup is also reachable
   after pathname validation failed before any open.

   The `temporary-collision` probe creates a review-owned sentinel at the
   process's exact `.ccxcap-part-PID` pathname before invoking the unmodified
   sink. Finalization deletes it (`preexisting_temporary_survives=0`). The
   configured capture path remains unpublished, but this does not preserve
   ownership of the collided sibling. A stale file after PID reuse is one
   concrete trigger. Track successful temporary creation and unlink only a
   file owned by this sink invocation. Add a temporary-path collision control
   alongside the existing final-destination collision test.

3. **P2 — The reader does not bind `MAP_SUMMARY`'s sweep identity to its
   generation.** Criterion: reader boundary.

   [capture_reader.py](../implicit-bounded-contact-capture-attempt06/capture_reader.py)
   lines 220–254 validate generation, tie, pass, counts, and selected values,
   but never compare the summary's step, increment, attempt, and iteration
   fields 2–5 with `GEN_BEGIN`. Other event classes perform that comparison.
   Changing those four fields from 1 to 99 in an otherwise valid stream and
   independently updating the footer byte count still returns
   `PASS_CAPTURE_STRUCTURE`. See probe `map-identity-mismatch` and
   [map-identity-mutated.tsv](map-identity-mutated.tsv).

   This permits contradictory source identities through the claimed strict
   structural contract. Apply the same four-field identity comparison used
   by `TRIAL_SUMMARY` and `STATE_JOIN`, with a rejection control for each field.

4. **P2 — A caller can bypass the frozen force-completeness invariant.**
   Criterion: reader contract ownership.

   The contract's `conservation_and_validation.trial_partition` requires law 2
   and complete finite force rows for generated trials. The sink enforces
   force completeness at lines 585–595, but the reader makes that check
   conditional on `expected.get("require_force", True)` at lines 399–400.
   Thus the contract is enforced differently on the two sides of the boundary.

   The `missing-force` probe changes a generated trial summary to
   `force_rows=0` and replaces its four force aggregates with `NA`, retaining
   the other independent fields and correcting the byte count. The ordinary
   expectation rejects it; the same expectation with `require_force=False`
   returns `PASS_CAPTURE_STRUCTURE` and a missing force resultant. See
   [missing-force-mutated.tsv](missing-force-mutated.tsv). Make the frozen
   force/law requirement unconditional, as attempt06 already does for energy
   when `nener==1`. If a permissive diagnostic API is needed, give it a result
   that does not claim this frozen contract passed.

## Verified architecture and boundaries

| Area | Assessment | Evidence and limit |
| --- | --- | --- |
| Exact predecessor and source | Verified | Attempt05 source pins, patch, archive, base-build manifest, base-image pin, and Makefile hashes match the asserted inheritance. All 1,197 archive member hashes match the inherited base-build manifest. No predecessor review reports were read. |
| Patch ownership | Verified for this delta | The complete patch regenerates byte-for-byte from the attempt06 archive and sink. Exactly three target files change: 702 added lines in `nonlingeo.c`, 77 in `gencontelem_f2f.f`, and four in `ccx_2.23.c`. Every original line remains byte-preserved and ordered. This is not a patch stacked on attempt05. |
| Mechanics separation | Sound source boundary | Added caller assignments use capture scratch; sink pointer arguments are read and copied into private state. No native mechanics array assignment, law, load, control, geometry, or contact decision change was identified. Regex policy tests support the exact reviewed delta; they are not a general C/Fortran semantic proof. |
| Hook placement | Mixed | Exactly the second `contact()` call is preceded by generation begin, gated by `iexpl<=1 && mortar==1`; `contact.c` routes that branch to `gencontelem_f2f`. Face census precedes the dead-face skip; point outcomes precede spring creation. Corrected/trial hooks occur before `stx` is freed. The post-convergence link has finding 1. |
| Run lifetime | Sound main boundary | One finalizer follows the complete top-level step loop and `closefile`; no per-step finalizer was added. Buffers persist across steps and final pointer/length cleanup is paired. The seed call is excluded and generator activity is guarded by pending state. Finding 1 prevents that pending lifecycle from working on normal nonconverged iterations. |
| Publication | Mostly sound; finding 2 | Capture writes an exclusive sibling, checks generation/footer flush and final close, then publishes through a no-overwrite hard link. Final-destination collision and injected flush/close failures pass their controls. Structurally invalid captures may be published with incomplete footers; consumers must always use the reader. Successful publication alone is not acceptance or a durability guarantee. |
| Resource bounds | Explicit finite storage | Writer ceilings are 64 sweeps, 250,000 combined-pass candidate records per generation, two retained point generations, two state snapshots of at most 1,000,000 doubles each, bounded index/hash tables, 128 ties, 13,001 pass-1 face records, 2,048-byte lines, and 128 MiB output with footer reserve. The reader applies the byte cap before byte-input decoding and enforces sweep/face/candidate checks. It materializes text and row objects; file size is not a resident-memory bound or benchmark. |
| Disabled path | Source guards verified | Cached absence of the capture path leaves sink allocation/output inactive, skips per-face/per-point capture bodies, and avoids the spring scan. Explicit-only steps do not initiate capture. No timing or runtime-equivalence claim was established. |
| Consumer contract | Needs changes | Seven externally frozen hashes, exact ordered face rosters, span/count conservation, event coverage, energy completeness, and terminal footer are checked. Findings 3 and 4 show that a successful reader result does not yet establish all documented invariants. Hashes supplied through the environment are declarations checked against independent expected bindings; they are not self-authentication of the running binary. |
| Readiness and engineering claims | Correctly limited | README, contract, and pins state offline-only work, no frozen current-joint input, no production build or solver execution, and false parent readiness/native authorization. Search completeness, force-history demand, joint capacity, first local contact, and whole-model energy balance remain outside the claim. |

## Validation and next actions

The exact shipped command
`PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest discover -s tests -v`
passed all 30 tests; see [offline-tests.log](offline-tests.log). It compiled only
standalone sink harnesses. Independent review controls are reproducible with
`PYTHONDONTWRITEBYTECODE=1 python3 -B reproduce.py` from this review directory.
That command compiles a temporary standalone harness which includes the pinned
sink and test helpers without modifying them. Its TSV files are synthetic
review evidence, not native solver output.

Resolve findings 1–4 in a new bounded revision, preserve attempt06, and rerun
the relevant offline controls. In particular, keep the source-realistic
convergence sequence and both destination and temporary collision controls.
Then repeat the hash-bound review on the replacement bytes. The observed
offline passes do not make attempt06 ready for a production build, native
coupon, current-joint run, or engineering acceptance. This review grants no
new authorization and adds no external-signoff prerequisite.

Only this new review directory was written. No attempt06 or predecessor file,
production build file, Docker artifact, solver, native coupon, or candidate
geometry was modified or executed. Input hashes were rechecked at completion.
