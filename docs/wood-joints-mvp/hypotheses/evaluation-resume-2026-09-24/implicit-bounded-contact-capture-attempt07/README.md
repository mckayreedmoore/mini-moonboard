# Implicit bounded contact capture — attempt07 lifecycle hardening

Attempt07 is an offline-only source-delta package regenerated against the exact
attempt06 archived source input. The source archive SHA-256 is
`9c88385c10fb04f5dc6c4e98027a51bebdd8aee3920e05190d6c1dd08357d6e7`;
attempt06 `source-pins.json` is
`869b5d7121b8cea80e95f9d87de159f225ec1c1d9b1a0e327e8693bc0e5684c5`, and its
patch is
`e98a5dd69aa1d992b18256a2cbd7dfedce6a2001b4af6085fdcac9c31ba8ba67`.
Attempt07 preserves that archive and creates a new additions-only patch from
it; the patch is not layered over attempt06's generated patch. Attempts01–06
remain unchanged.

The post-convergence call order is now reflected in the writer. The pinned
`nonlingeo.c` path calls `checkconvergence` before the iteration-link hook; on
the ordinary nonconverged path, pinned `checkconvergence.c` increments `*iit`
before returning. The sink therefore records the captured generation's
pre-convergence step/increment/attempt/iteration as its event identity, while
using the post-convergence iteration, cutback and control values only to
validate the transition and derive the outcome. It emits and closes the
pending link even for an invalid transition, marking that capture erroneous
instead of leaving an unlinked generation. Offline controls exercise both the
nonconvergence increment and a cutback transition.

The sink now tracks ownership of its exclusive temporary sibling and removes
it only after this process successfully creates it. A deterministic PID
collision regression proves that an existing `.ccxcap-part-*` file survives a
failed exclusive open. The reader also binds each `MAP_SUMMARY` identity to its
`GEN_BEGIN`, rejects negative state-join measures, independently enforces the
combined pass-1 plus observed pass-2 candidate cap, and requires complete
force rows for every generated force trial regardless of caller permissive
flags. Footer-flush injection occurs after `RUN_END` has been written and
confirms the configured destination remains unpublished.

Attempt07 incorporates these attempt06 review artifacts as its review basis;
the hashes are also recorded in `source-pins.json`:

- Architecture: [attempt06 architecture review](../implicit-bounded-contact-capture-attempt06-architecture-review/README.md), SHA-256 `0fcb4d7c1e006f754247e64751f733602d599589d38762387c78ee08ad4bb85e`.
- Correctness: [attempt06 correctness review](../implicit-bounded-contact-capture-attempt06-correctness-review/README.md), SHA-256 `1ac51cdfbdd5926c1446d85d5408544c2496ef7b79af5811b9515fff5913b833`.
- Tests: [attempt06 test review](../implicit-bounded-contact-capture-attempt06-test-review/report.md), SHA-256 `0c4e7316e01338b6a63513b5f36c3293f7293bf11bb58e9a04ecf43883214dbe`.

The offline controls pass with:

```sh
PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest discover -s tests -v
```

This runs 34 tests and compiles only standalone capture-sink harnesses. It does
not compile the patched CalculiX sources, invoke Docker, run a solver binary,
run a coupon, or freeze a current-joint input. No production build or solver
execution was performed. The attempt07 readiness and native-execution
authorization flags are false; the packet is handed off for three fresh
independent reviews and parent-owned validation.
