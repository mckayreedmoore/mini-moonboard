# Attempt08 architecture and integration review

**Assessment:** No architecture blocker was found for attempt08’s documented single-process capture lane. The exact source pins, additions-only delta, call placement, writer ownership, parser policy, disabled path, and process boundary align. This review verifies the offline source package and patch replay only; it does not establish a patched production build or native solver behavior.

The review is hash-bound to source archive `9c88385c10fb04f5dc6c4e98027a51bebdd8aee3920e05190d6c1dd08357d6e7`, patch `abaaa6d65d709edb53043619e4a974184b2ec278ef0a3e1cba9dde7c92a84e5e`, sink `0715f915f4500f5cab1810e4274ad9c18a1e3b785dccd32e4c943237765fdb28`, and reader `8692a22286150cb88afc55e857e9791de81d208ab68af0e4360cc16e1f7638f9`. Complete subject hashes are in [`input-sha256.json`](input-sha256.json); report files are covered by [`SHA256SUMS`](SHA256SUMS).

## Findings

No blocker was identified within the documented single-process, serialized-job boundary.

Attempt08 explicitly disallows concurrent hook calls and sharing one sidecar across processes or ranks. The sink has process-local static state, makes a PID-specific temporary sibling, and publishes to the configured destination with a no-overwrite hard link. With a shared final path, processes would race to publish and there is no aggregation. The pinned build recipe has no `CALCULIX_MPI` definition; preserve the documented per-process path rule if the build boundary changes.

One declared verification limit remains: the writer checks live post-hook `iit`, but the stream does not serialize that value, so the reader cannot independently repeat that check. The README and contract state this plainly; the reader only treats the output as `PASS_CAPTURE_STRUCTURE`, and the writer marks an invalid live transition as an error.

## Evidence

- **Pins and inventory:** Every listed attempt08 inventory file matched its declared digest; no extra or missing candidate files were present. The archive has 1,197 file members, and its changed-source targets matched the pinned upstream hashes. Attempt07’s archive, source-pins, patch, base-build manifest, and the two review-basis documents matched attempt08’s predecessor pins. See [`verification.json`](verification.json).
- **Exact replay:** Applying the checked-in patch to a temporary extraction with `--fuzz=0` succeeded without offsets or fuzz. Each modified member matched the exact `modified_sha256` value. The patch contains additions and no deletion lines. See [`patch-replay.log`](patch-replay.log).
- **Hook placement:** The generation begins before the second `contact()` call, the in-loop regeneration; the first seed call is excluded. The post-results copy precedes the capture snapshot/trial scan, `checkconvergence()` precedes the single iteration-link hook, and the job finalizer appears once after the top-level step loop and `closefile`. `contact.c` reaches the pinned Fortran generator. See line-numbered [`source-callsite-evidence.txt`](source-callsite-evidence.txt), and the generator logic in `prepare_capture.py` around lines 475–564.
- **Writer lifecycle:** Capture state is opened lazily and only becomes owned after the exclusive temporary-file open succeeds. The finalizer flushes and closes before publishing; it removes only an owned temporary sibling. Missing capture-path behavior stays inert: the per-generator activity check is false, per-face/per-point sink calls are guarded, and the post-results spring scan is skipped. Attempt08 states there was no disabled-path benchmark, so its overhead claim is structural only.
- **Build and claim boundary:** The pinned build recipe applies `-Werror=incompatible-pointer-types` to the modified caller and does not enable MPI. Attempt08 has no patched solver binary; production build, Docker, solver, and current-joint freeze flags remain false. Its contract requires parent rebinding of input/include closure, source, patch, binary, ordered tie and face rosters, and law/energy settings. It excludes search completeness and joint capacity/load-path acceptance; no status language I found presents offline structure checks as native mechanics or joint acceptance.

## Verification scope

I independently checked inventory and predecessor pins, replayed the source patch with zero fuzz in `/tmp`, inspected the source and contract, and reran the package’s 37-test offline suite successfully. No patched production build, Docker, solver, or coupon was run.
