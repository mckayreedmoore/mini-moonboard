# STI17 source architecture review

## Scope and input pins

This is a source-only review of the isolated STI17 build and the free C3D20
coupon path for `led-clearance-2x6-runner-seated-blocks-v1`. The source-review
target manifest SHA-256 is
`8bec53f223af3d770ea8df541d2b0cb47eeac89fee721103ae046ca55703f7e8`.
All 15 listed files matched both their manifest SHA-256 and byte length; no
input drift was found.

The reviewed packet pins the preserved CalculiX source archive as
`9c88385c10fb04f5dc6c4e98027a51bebdd8aee3920e05190d6c1dd08357d6e7`, its
`matrixstorage.c` member as
`2b2a502637761a7663e50e43a7f5afe9322c6c775aa6c44fd7b433976bbe59c4`, and the
base image as
`sha256:31336f517557f5dd5f97d85b1e6e15947fd1c10b44edc1364dbba4c1a5ab6c38`.
Those identities are bound in the reviewed sources and receipts; the archive
inside the image was not read in this audit.

## Assessment

The build narrows the source edit to the stiffness formatting token, checks
the compile plan and object delta, and keeps the old toolchain separate. Coupon
preparation builds a separate profile and freeze, and the result checker joins
the output hashes to the runner’s authorization, execution, review, and ledger
records. The following provenance gaps prevent this source pass from approving
readiness for the isolated build or coupon launch.

## Findings

### 1. High: build freeze is not bound to the reviewed source set

`freeze_sti17_build_inputs.py:38-68,80-171` hashes the files that exist when it
runs. Its input list omits the source-review target and this freeze script
itself. `build_sti17.py:109-159,162-227` checks readiness against the parent
validation and source-pin hashes, then accepts any freeze whose file map
contains `REQUIRED_BUILD_FILE_PINS`. The builder checks those live files
against the freeze, but does not compare them with the hashes reviewed in the
target manifest.

As a result, a source change after this review but before freeze creation can
be hashed into a fresh freeze and accepted as the reviewed build. The freeze
also cannot establish which version of its own producer created it.

**Fix:** Carry the exact source-review target SHA-256 and this review report
SHA-256 in parent build readiness. Have the freezer record them and have the
builder require those exact values, validate every target-manifest entry
against its listed digest, and require the canonical build input set. Pin the
freeze producer to the reviewed digest as part of that same chain.

### 2. Medium: coupon launch can pass a changed freeze through its second check

`launch_sti17_coupon.py:65-73` records the freeze digest and checks that the
review approves it. Under the ledger lock, line 139 calls `verify(directory)`
again, but does not compare the current `freeze.json` digest with the earlier
reviewed digest. `verify()` checks a freeze against its own current hashes; it
does not establish that the freeze is the one approved by the review. The
launcher then mounts the mutable attempt directory at lines 117-128. A
replacement freeze and matching `model.inp` between the review check and the
locked check can therefore be executed while authorization and ledger records
still cite the earlier digest. The post-run checker would reject the mismatch,
after the one launch has already been consumed.

**Fix:** Under the ledger lock, require the current freeze digest to equal the
reviewed digest after verification and use the packet returned by that exact
verification. Run the reviewed deck from an immutable input snapshot or
read-only input mount so it cannot be replaced between verification and the
solver opening it.

## Limits

No tests or Ruff checks were run in this review; the 20 tests / 42 subtests and
Ruff result are prior checks recorded by the handoff. No Docker, build,
compiler, solver, CAD, mesh, freeze, ledger mutation, or native output reading
was performed. The final STI17 image does not yet exist, so the base-image
timeout known-answer does not qualify the final image. That receipt pins
`/usr/bin/timeout` at SHA-256
`4fccd5b0192653a2446b745d5385ea547b78e466150e07ade9e2caff2b7f4e08`; the
coupon launcher currently invokes the PATH-resolved name `timeout`. Confirm
the final image resolves that command to the qualified utility and preserves
the forced-kill behavior before coupon readiness.

The original raw-H27 STOP and all 47 pending criteria remain unchanged. This
review makes no candidate, geometry, capacity, mechanical-acceptance, or
release claim.
