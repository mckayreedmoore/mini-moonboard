# STI17 isolated build and coupon preparation

Status: source-only preparation. No Docker command, compiler, solver, native
coupon, ledger update, solver-output `.sti`/`.mas` read, candidate export,
CAD, or Git command was run for this packet. All 47 formal criteria remain pending. This packet
does not authorize a native run, candidate export, fabrication, build release,
or climbing use.

The latest source-only checks passed Ruff and 27 tests / 48 subtests with temporary
synthetic fixtures, including temporary `.sti`/`.mas` text samples. They cover
the single-token stiffness patch, rejection of
wider compile plans, parent readiness and freeze pin mismatches, coupon
readiness receipt binding, STI17/MAS14 output precision, generated-freeze
acceptance by the stock runner's `verify()`, and the runner's authorization,
review, terminal-record, ledger-row and launch-command chain. They include
negative cases for broken record hashes, freeze/review/ledger links, resource
limits, image, binary, timeout and output path. The tests use temporary
records and mocked Docker calls; they run no builder, compiler, input freezer
or real solver and read no real solver artifacts.

The later hard-stop fix introduces `launch_sti17_coupon.py`. It retains the
original runner SHA and shares its verifier, ledger and lock, using
`/usr/bin/timeout --signal=KILL 60s` for the native payload. The launcher verifies
that absolute utility's SHA-256 alongside the solver binary before reservation.
Authorization and execution retain both utility path and hash. The launcher
requires its canonical attempt directory, the exact retained coupon deck and
model, and the unchanged reviewed freeze and exact approval bytes under the
shared ledger lock. The coupon invocation sets both memory and memory-plus-swap
to 2 GiB. A
separate read-only mount protects the deck from writes inside the container.
The coupon freeze binds
both launch sources; the checker refuses TERM-only commands and records the
scoped launcher hash. A separate local GNU-timeout known-answer killed a
Python process that ignored TERM. **Fresh source review and qualification in
the pinned container remain pending; native readiness is false.**

The cited parent validation is
`docs/wood-joints-mvp/hypotheses/mvp-integration-2026-10-01/source-next-method-parent-validation.json`
(SHA-256
`5cae8f60ce6f9af80ffd9049fb0643e7cfa44e01cddecf6799fe6f5ee12e87b2`). It
records `ready_for_build_or_native_run=false`, `candidate_export_authorized=false`,
47 formal criteria pending, and the original raw-H27 STOP retained. The
precision preflight source pin is SHA-256
`1cc174760cb658614431a75532fcd0603342b6e1559ebc0df935be6310e65981`.
Those files and the relevant solver, source archive, profile, build manifest,
coupon, and oracle identities are recorded in `pin-receipt.json`.

## Bounded build

The proposed base is the existing immutable image ID
`sha256:31336f517557f5dd5f97d85b1e6e15947fd1c10b44edc1364dbba4c1a5ab6c38`
(`mini-moonboard-fea:ccx-upstream-2.23-v1`). Parent must confirm that tag still
resolves to that ID and that the new tag
`mini-moonboard-fea:ccx-upstream-2.23-sti17-v1` is unused. Build in one
no-network container from that image, with one CPU, 2 GiB memory, and a 60
second outer timeout. Parent readiness is the existing authorization control;
the build script requires its fresh, exact `parent-build-readiness.json` and
refuses to start without it.

The script copies `/opt/ccx-upstream-2.23` with preserved file metadata into a
new `/opt/ccx-sti17` tree. It verifies the archive, upstream source inventory,
old binary, build manifest, compiler versions, and linked libraries against
the pinned records before editing. It applies only the reviewed patch to the
copied `CalculiX/ccx_2.23/src/matrixstorage.c`: the stiffness writer changes
from `%20.13e` to `%20.16e` at source line 304. The mass writer at line 543
stays `%20.13e`. The old tree, old executable, old profile, old build
manifest, and old image tag remain untouched.

The builder verifies the pinned preflight's successful patch dry-run receipt,
then repeats a reversible in-memory exact-byte patch check on the copied
source before writing the one-token change. Its terminal receipt retains the
dry-run record and a unified byte diff showing the single changed line.

Before compiling, it dry-runs the unchanged `Makefile.upstream` and refuses
unless the only C compile is `matrixstorage.c`, followed by the existing
archive and link commands. It then runs that make target serially with the
same checked-in Makefile and flags. It compares every copied upstream source
and object before and after, requiring the only source-content change to be
the one format token and the only changed object to be `matrixstorage.o`.
Compiler versions, every dynamically linked library hash, and the complete
old and new object maps go into a separate terminal build receipt. Any wider
compile plan, pin mismatch, absent file, old identity change, timeout, or
nonzero result stops the attempt; do not restart in the same container or
reuse its partially changed copy.

Before the build, the parent writes `parent-build-readiness.json` with schema
`ccx223_sti17_parent_build_readiness/v1`, status `READY_STI17_BUILD`, the
cited parent-validation and source-pin hashes, the immutable base ID, the new
unused tag, `base_tag_resolves_to_id=true`, `new_image_tag_unused=true`,
`candidate_export_authorized=false`, `native_run_authorized=false`,
limits of 1 CPU / 2 GiB / 60 seconds, and a Unix creation time no more than 30
minutes old. This is parent-owned readiness within the existing authorization.
The parent then runs `freeze_sti17_build_inputs.py` once. Its
`build-input-freeze.json` captures hashes for the exact builder, pinned
preflight, profile, source records, coupon references, repository instructions,
and readiness file. Readiness also carries `review_binding`: `target` has the
repository-relative path and SHA-256 of the exact final source-review target;
`reviews` maps `correctness`, `testing`, and `architecture` to each report's
repository-relative path, SHA-256 and actual reviewer `agent_id`. Paths,
digests and reviewer identities must all be distinct. These parent-recorded
identities do not independently attest authorship; parent must verify the
actual reviewer assignments and results. The freezer includes those records and
every target file. Both freezer and builder check that the frozen source
hashes equal the reviewed hashes, including the freezer's own source. Parent
must first read and disposition all three reports. The build process refuses
any missing, changed or unreviewed frozen input.

After checking the freeze and confirming that the new tag is unused, the
parent can run the prepared builder in one retained, no-network container
from the immutable image ID. A concrete invocation from the repository root
is:

```sh
docker run --pull=never --name moonboard-sti17-build-attempt01 --network=none --cpus=1 \
  --memory=2g --memory-swap=2g \
  --volume /home/mckay-linux/repos/mini-moonboard:/repo:ro \
  sha256:31336f517557f5dd5f97d85b1e6e15947fd1c10b44edc1364dbba4c1a5ab6c38 \
  /usr/bin/timeout --signal=KILL 60s \
  python3 /repo/docs/wood-joints-mvp/hypotheses/ccx223-sti17-build-coupon-preparation-2026-10-01/build_sti17.py
```

There is deliberately no `--rm`: the parent needs the stopped successful
container to create the separate image. A nonzero exit, timeout, OOM, or
missing terminal receipt ends that attempt; preserve its record and use no
restart. Recheck that the STI17 tag is unused immediately before commit. Only
after a successful terminal receipt should the parent commit that stopped
container to the unused STI17 tag and record the resulting image
ID plus the copied build-receipt hash in
`sti17-image-receipt.json`. The image receipt must name the exact base ID,
new tag and binary path/hash from the build receipt. It never retags the old
2.23 image.

The new executable path is
`/usr/local/bin/ccx-upstream-2.23-sti17`. The parent records its immutable
image ID and binary hash in a separate image receipt and generated solver
profile. The current image is never retagged or overwritten.

## Coupon gate

Only after a successful image receipt and fresh parent readiness, prepare a
new isolated coupon freeze from the existing free C3D20 deck and unchanged
oracle. The custom freeze script writes a separate STI17 solver profile and
binds that image and binary into the freeze packet. It leaves the shared
2.23 profile alone. It calls the stock runner's unchanged `verify()` after
preparing the packet. The current stock `freeze()` reads the repository-level
profile constant, so this packet intentionally constructs the separate
parent-reviewed freeze instead of monkeypatching that constant. The stock
`verify()` and `launch()` consume the profile embedded in the freeze.

The parent supplies `parent-coupon-readiness.json` using schema
`ccx223_sti17_coupon_readiness/v1`, status
`READY_FOR_STI17_COUPON_FREEZE`, the exact image ID and terminal build-receipt
SHA, scope `free-c3d20-sti17-output-precision-coupon-only`,
`candidate_export_authorized=false`, `native_run_authorized=false`,
`image_receipt_sha256`, limits of 1 CPU / 2 GiB / 60 seconds / one native run,
and a creation time no more than 30 minutes old. The script refuses a
mismatched image, binary, receipt, old profile, manual, deck, oracle, or
readiness record. After it writes the freeze,
the parent obtains an independent review bound to that exact `freeze.json`
hash. The native runner then checks that review and reserves the existing
single slot under one never-reused run ID.

The parent must review that exact freeze and reserve the existing single
native slot for one run ID, one CPU, 2 GiB, and a 60-second native payload.
After the pending source/runtime qualification, invoke
`launch_sti17_coupon.launch(FREEZE_DIR, run_id, review_path)` with that freeze
and matching independent review. Its resources are fixed; it shares the
existing ledger and consumes the run once. This is one free-C3D20 coupon run;
there is no retry or broader rerun. The post-run checker requires finite
STI17 values (16 digits after the decimal), finite MAS14 values (13 digits
after the decimal), all 60 `.dof` equations, unique symmetric triplets, six
rigid modes and no negative modes, the analytical shear-energy answer
`2.0e-5 N·mm`, and unit translational mass `1`. It also binds the raw output
hashes to the existing runner's execution record. The checker requires exactly
one `consumed_terminal` ledger row for the run ID, with the exact scope,
attempt directory, freeze SHA, one consumed launch, and authorization and
execution file hashes. It also requires authorization and execution to record
the same scoped Docker command, pinned STI17 image and binary, no network,
one CPU, 2 GiB memory, the exact attempt output mount, and
`/usr/bin/timeout --signal=KILL 60s`, including the separate read-only deck
mount and the qualified utility identity. Docker startup/preflight and terminal cleanup are
separate control phases; this payload timer does not claim a 60-second total
duration for the entire Docker workflow.
It writes a separate `coupon-result.json` exclusively in that attempt directory
after checking that the path does not alias a source, freeze, or native record.

A pass supports only this formatting/build path and free-coupon oracle. It
does not authorize exporting any candidate matrix or establish why the A12
force interval missed. Keep the saved-arithmetic result and original raw-H27
STOP unchanged. The parent must decide separately whether any later bounded
method step is ready; solver convergence and coupon success are not joint
acceptance.

## Prepared files

- `pin-receipt.json` records the source and method pins checked while
  preparing this packet, plus data that must be measured only inside the
  future isolated build.
- `freeze_sti17_build_inputs.py` creates the parent-owned, one-attempt
  `build-input-freeze.json` after parent readiness; it has not been run.
- `build_sti17.py` is intended to run inside the isolated base-image
  container. It has not been run.
- `prepare_sti17_coupon.py` prepares the separate profile and coupon freeze
  from a terminal image receipt. It has not been run.
- `check_sti17_coupon.py` checks raw coupon outputs after the single parent
  run. It has not been run on solver artifacts.
- `launch_sti17_coupon.py` is the scope-locked hard-stop invocation. Its
  preserved kernel shares the original verifier/ledger and is tied to the
  original runner SHA. No real run was launched.
- `test_hard_stop_launcher.py` exercises source/scope refusal, forced-KILL
  command generation, terminal ledger bookkeeping and killed-exit disposition
  with temporary records and mocked Docker calls.
- `test_sti17_preparation.py` exercises pure checks and a synthetic temporary
  freeze against the stock runner verifier, ledger provenance, bounded launch
  command, and output-path protections. It has no build or native execution
  path.

The freeze copies the exact cited preflight pins and patch, coupon deck, and
independent oracle into its source snapshot. Existing source and result
records stay at their original paths.
