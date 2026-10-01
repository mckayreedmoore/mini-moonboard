# Ordinary external-force transient, attempt04 diagnostic patch

## Decision

The 21 aligned count changes from increment-2 iteration 1→2 through 21→22
each exceed `delcon`. The minimum relative change is 0.122619% at iterations
20→21. On those later iterations the count branch sets `iflagact=1`, making
the contact-change gate fail. The first iteration follows a separate initial
contact-generation path and fails the mechanical `iit>1` prerequisite; its
count difference from the accepted preceding increment does not prove that
the count branch set its flag. This corrects the earlier 22-iteration flag
inference without changing the frozen counts or outputs. Exclude the extra
unaligned, incomplete CEL iteration-23 group.

The trace records the flag and remaining predicates on the same frozen deck.
`iflagact` is the resulting overall flag; a count event does not identify
whether an earlier code path had already set it. No physical response or
joint acceptance follows from this convergence diagnosis.

## Observable

The output-only patch adds two keyed JSON event streams:

- `CCX223_ATTEMPT04_CONTACT`: prior and new contact-element totals, `delcon`,
  and the resulting `iflagact` at the `nonlingeo.c` contact-count branch.
  For the frozen mechanical, face-to-face penalty decks without small
  sliding, this branch runs on iterations greater than one. The separate
  initial contact-generation path is not instrumented with this event.
- `CCX223_ATTEMPT04_CONVERGENCE`: iteration, residual, displacement, visco,
  contact-flag, no-contact and contact-energy-path booleans, plus
  `iconvergence`, `idivergence`, and the final convergence predicate, for
  each completed convergence check, including iteration one.
  `mechanical_gate_ok` is the inner mechanical predicate before `kscale>1`
  can reset `iconvergence`; the trace logs `iconvergence` separately after
  that handling.

Boolean fields are encoded as integer `0` or `1`. The frozen attempt03
`pilot.inp` SHA-256 is recorded with all 44 frozen artifact hashes in
[`attempt03-input-binding.json`](attempt03-input-binding.json). Its
execution record also binds the `.cvg`, stdout and CEL outputs.

## Source basis

The patch applies only to the
[official source archive](https://www.dhondt.de/ccx_2.23.src.tar.bz2) pinned by
[`fea/calculix_223/Dockerfile`](../../../../../fea/calculix_223/Dockerfile).
Its SHA-256 is
`9c88385c10fb04f5dc6c4e98027a51bebdd8aee3920e05190d6c1dd08357d6e7`.

The official 2.23 source maps `TYPE=SURFACE TO SURFACE` to `mortar=1`
(`contactpairs.f:115–116`). For that path, `nonlingeo.c:2352–2356` compares
the old and new total contact-element counts against `delcon`; `ini_cal.c:321`
sets its default to `0.001`. `checkconvergence.c:151–162` requires
`iflagact==0` for the mechanical predicate. Its no-contact energy check and
contact-impact strategy are gated by the prior mechanical predicate at
`checkconvergence.c:223–235` and `:266–288`.

The first contact-generation call is at `nonlingeo.c:1883–1895`, with its
count printed at `:1920–1921`. The later path is inside the `iit!=1` guard
at `:2228`, then the contact-rebuild guard at `:2307–2313`. Only this later
path contains the patch's count event. The
[2.23 manual](https://www.dhondt.de/ccx_2.23.pdf) describes `.cvg` and CEL
iteration output in section 4; the pinned source determines the exact
event cardinality for these face-to-face penalty decks. Do not infer that
cardinality from the manual's separate node-to-face discussion.

The patch only inserts declarations and diagnostic output statements. It
does not replace or delete source text or change the standard 2.23 profile.
The trace calls `printf` and `fflush` synchronously, so it can increase
runtime and stdout volume even though it does not change solver state.

## Static verification

On 2026-09-27, `verify_apply.py` passed against the official archive. It
checks the archive and member hashes, all 44 frozen attempt03 input artifacts,
all nine recorded native outputs, the base image and binary path in the
original execution command, and a zero-fuzz insertion-only patch application.
This check alone validates neither runtime traces nor mechanics. The build
and coupon records below supply the subsequent execution evidence.

```bash
python3 docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/\
ordinary-external-force-transient-attempt04-diagnostic/verify_apply.py \
--source-archive /path/to/ccx_2.23.src.tar.bz2
```

## Build and coupon disposition

[Build attempt01](build-attempt01/build_result.json) failed before compilation:
Docker interpreted a bare local image ID in `FROM` as a registry reference.
[Build attempt02](build-attempt02/build_result.json) used the verified local
2.23 tag with pulling disabled. Its image ID is
`sha256:1cc1d52946c5acddc9d4eeaf1dd1bf0bc4d3f564eb1c264f5d29b67c6386b7fa`;
the diagnostic binary SHA-256 is
`3aec6cfe0ca72a463d87c648ed6b4a83ee1bb6a08bf604a144c8a6553d2f439f`.
Independent review verified the 1,197 source-file hashes, build context,
image layers and binary identities. The unpatched 2.23 and packaged 2.21
executables remain hash-identical to their recorded versions.

[Coupon attempt01](coupon-known-answer-attempt01/verifier.json) exited zero
and reproduced the reference numerical files, allowing only the generated
FRD clock header to differ. Its verifier failed because it incorrectly
required contact events on first iterations: the run has eight contact
events and 16 convergence/CVG/CEL rows. Both the failed execution and the
original verifier are preserved. A new coupon attempt must require exact
convergence/CVG/CEL key equality and exact contact-key equality to the
iterations greater than one, under the explicitly checked deck conditions.
An arbitrary subset of contact rows is insufficient. Check counts, prior
counts, event types, flags and the pinned `delcon`, as well as numerical parity.

## Corrected coupon and joint replay

[Coupon attempt02](coupon-known-answer-attempt02/verifier.json) passed on the
same build02 binary at 2026-09-27 13:04 UTC. All 16 convergence/CVG/CEL keys
and exactly eight later-iteration contact keys match; numerical files are
unchanged apart from the permitted FRD clock header. Docker exited zero with
`OOMKilled=false`. The preserved attempt01 failure is not overwritten.

The parent completed [replay attempt01](replay-attempt01/RESULTS.md) after
its build, coupon, input, binary and zero-active-solver gates passed. It
stopped at 1,021.04 seconds on the 600-second accepted-state/monitor-progress
watchdog; Docker exit 137 followed the requested stop, with `OOMKilled=false`.
All 44 inputs match. The only accepted state is the same under-floor
`0.001 s` startup state as attempt03; `.dat` and `.sta` are byte-identical.

The audited trace has 44 completed convergence/CVG rows. Increment-2
iterations 2–26 fail only the contact-count stability check; residual,
displacement and viscoelastic checks pass in every completed row. Each
increment's first iteration fails `iit>1` instead. A CONTACT/CEL-only
iteration-27 tail remains unresolved. Forty common CVG rows match attempt03
exactly, and four additional completed rows are recorded.

See the [source interpretation](contact-count-interpretation.md) and
[terminal result](replay-attempt01/RESULTS.md). The next decision is a
documented contact-method route with a known-answer check before candidate
changes. The result does not justify relaxing `delcon`, altering the reviewed
geometry, repeating the same pulse, or claiming equilibrium or joint acceptance.
