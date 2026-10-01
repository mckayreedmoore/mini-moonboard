# Implicit bounded contact capture — attempt08 source and reader hardening

Attempt08 is an offline-only source-delta package based on attempt07's exact
archived source input. The archive SHA-256 is
`9c88385c10fb04f5dc6c4e98027a51bebdd8aee3920e05190d6c1dd08357d6e7`;
attempt07 `source-pins.json` is
`04649a3fe41d0b089b0cf9581185a17f10fb6d822a10c6cde94c3b1c4e85b91e`, and its
patch is
`f7ff0f8b679d6d1d6448b368d134bc65ff8e038582ded1686a67f853155294f6`.
Attempt08 preserves the archive and regenerates a complete additions-only patch
against it; it is not layered on top of attempt07's patch. Attempts01–07 and
their review artifacts remain unchanged.

The post-convergence transition now matches the pinned CalculiX 2.23 source.
On success, `checkconvergence` sets `icntrl=1` and resets `icutb=0`, including
after a retry; a cutback increments `icutb`; and the ordinary nonconverged path
increments `iit` while leaving the attempt unchanged. The writer records the
captured sweep identity, validates the live iteration and attempt transition,
and always emits one link and clears pending state, marking invalid transitions
as errors. The reader validates the serialized attempt transition: a
nonconverged link must retain its attempt; a converged link reports either the
successful reset to attempt one or exactly one cutback successor. Offline
controls cover a successful accepted retry reset, an invalid transition that
still closes pending state, and a nonconverged `attempt_after` mutation.

Eligible state joins now run when either candidate set is empty. New points are
counted as new-missing when the old set is empty; old points are counted as
old-missing when the new set is empty. A tie with no candidates on either side
may report six zero counts when the face census supports that empty domain. A
two-generation, two-tie test covers both the empty-old/new-missing case and a
zero-to-zero tie. The production-source policy test checks that the regenerated
`nonlingeo.c` has exactly one iteration-link call and that it follows
`checkconvergence`. Reader mutation controls now cover all four map identity
fields and all six state-join counts. The combined-pass overflow fixture updates
the face spans, map summaries, generation totals, and footer consistently while
keeping each per-summary candidate count below the cap.

Attempt08 read and pinned these attempt07 review artifacts:

- [Correctness review](../implicit-bounded-contact-capture-attempt07-correctness-review/README.md), SHA-256 `3adf5babd28e75151c4c5800fd8d068360321f754049301b8165664435384e3f`.
- [Test-coverage review](../implicit-bounded-contact-capture-attempt07-test-review/report.md), SHA-256 `1ac707b648a72e51e44b20537f2cdb25d7d548e286d965bab09bfa6be348f34f`.

Run the offline controls from this directory with:

```sh
PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest discover -s tests -v
```

The suite contains 37 tests and compiles only standalone sink harnesses. Patch
replay is also checked against the pinned archive with zero fuzz and against
the modified source-member hashes in `patch-preparation.json`. No patched
CalculiX production build, Docker invocation, solver execution, coupon, or
current-joint input freeze was performed.

The sink remains process-local and single-serial: it does not synchronize
concurrent hook calls or aggregate multiple ranks, processes, or jobs into one
sidecar. Use a distinct output path per process/job. Readiness, production
build, solver execution, and native-execution authorization are false; the
packet is ready for fresh independent review and parent-owned validation.

One explicit reader limit remains: the link row serializes the captured
iteration, not the post-hook live `iit`. The writer validates that live value
against the pinned source transition; the reader independently validates the
serialized attempt and accepted flag, but cannot repeat the writer's
post-iteration check from this stream format.
