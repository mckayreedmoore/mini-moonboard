# Independent correctness review — attempt04

Review date: 2026-09-27. Reviewed the source/build packet in `../implicit-bounded-contact-capture-attempt04/` against its pinned CalculiX 2.23 source archive. No packet, source, queue, manifest, or joint input was changed. No CalculiX, Docker, or offline test suite was run.

## Disposition

The C/Fortran ABI arguments for `istep`, `kscale`, and `ntie` are correct in attempt04. The generation hooks are reachable at the in-loop face-to-face contact regeneration call, while the earlier seed call stays outside the capture lifecycle. The source performs the optional second pass independently per tie, and the reader preserves that meaning and checks its face rows against pass 1.

One confirmed protocol defect remains: the C writer can mark a generation and run complete without checking every pass-2 face identity/status/offset tuple against pass 1. The shipped reader performs that exact comparison and rejects a mismatch, so using `PASS_CAPTURE_STRUCTURE` as the mandatory gate prevents such a stream from being accepted. `GEN_END.complete` and `RUN_END.complete` alone are not sufficient acceptance signals.

The current reader also has a deliberate applicability restriction: because the source generator skips tie entries whose flag is not `C`, the configured global tie roster must consist of contiguous C ties with the expected face rosters. Mixed C/non-C tie lists fail closed. No current-joint input was inspected to determine whether that restriction applies to a planned run.

## Source and build binding

I independently checked the attempt04 packet inventory against `source-pins.json`; all listed packet-file hashes match. The pinned source archive SHA-256 is `9c88385c10fb04f5dc6c4e98027a51bebdd8aee3920e05190d6c1dd08357d6e7`. Its 1,197 files and hashes match `base-build-manifest.json`. I reconstructed the three additions-only patch targets in memory from the archive and `capture.patch`; the resulting hashes match both the preparation pins and build manifest:

| Source member | Upstream SHA-256 | Attempt04 SHA-256 |
|---|---|---|
| `CalculiX/ccx_2.23/src/nonlingeo.c` | `8684bb6d7fa7097c0a854db5a45eb9e2d11adfde574e688184ecbbbad56ff83f` | `70558a65b17afa52cca2b6d7ba70a27d1c4581adec3af3c6616fbd0646891bb3` |
| `CalculiX/ccx_2.23/src/gencontelem_f2f.f` | `853e2159f37666bc1430516bb4e5c65b6ba484ef1866454930e66cf317fb8afe` | `110dea22c7578330496be81f05d9f406b0eb4635bc2b56adc4cd4766459f5b85` |
| `CalculiX/ccx_2.23/src/ccx_2.23.c` | `5b3fffaa55699b61f23c86ddb6bbf016b2411e6beb9a002231338bdd041fd144` | `66ddbd1215f69e03a869a32c0ca24c7649649943427d1e57f0d5e423171beebd` |

The patch SHA-256 is `7aa89782d3026f9d27fbd5f62bb4dbdfb80f11472c861bcc1568f22db3fe474f`; the sink SHA-256 is `4dec9e3b21bcdcba85737bf0d930ef5035e22586ea4ef436b580d3219180b7bc`. The copied binary hashes to `b5a2483cac9d2e208babe8a52c534ec1f3199d34fc8e64accb3005d66507e303`, matching the packet pin, build manifest, and build provenance. The recorded base and built image IDs are internally consistent across those files. I did not query Docker or independently attest the local image IDs, as required by the task constraints. The recorded offline-test-output hash also matches its packet pin; those tests were not rerun.

The packet does not hash-pin a manual. For external documentation context, the official CalculiX 2.23 solver manual was fetched from [dhondt.de/ccx_2.23.pdf](https://www.dhondt.de/ccx_2.23.pdf) and hashed during this review as `a0bf3fc03f374912ff2bf28da3f7dfb6a61428dd7f41b281a2e7e1fdb318f330`. Since that document is not part of the packet pinset, ABI and control-flow conclusions below are bound to the pinned source archive and patch.

## ABI and hook reachability

In pinned `nonlingeo.c`, `istep` and `ntie` are function parameters of type `ITG *`; local `kscale` is `ITG`. The added prototype for `ccxcap_generation_begin_` takes `ITG *` for these scalar arguments. Its production call passes `istep` and `ntie` directly and passes `&kscale`, which is the correct pointer level for the local scalar. The hook copies `*kscale` into its private capture state. The later trial hook also takes `ITG *kscale`, and its call passes `&kscale`. In the pinned default build, `CalculiX.h` defines `ITG` as `int` because `INTSIZE64` is not enabled; the Fortran declarations use default `integer`, matching that build ABI. The production C build rule enables `-Werror=incompatible-pointer-types` for `nonlingeo.o`.

The begin hook is inserted immediately before the `contact()` call inside the nonlinear iteration loop. The earlier pre-loop `contact()` call is not preceded by it. In pinned `contact.c`, the `mortar==1` branch dispatches to `gencontelem_f2f`; that routine reads the pending/activity hook, records faces and point candidates, and calls the generation-end hook at its common tail. After the in-loop contact work, the added hooks snapshot corrected `vold`, inspect generated spring elements for trial summaries, and link the capture to the iteration outcome. The CLI finalizer is inserted once after the top-level step loop and `closefile`. The pending-state guard makes an uninstrumented seed call's generator-end hook a no-op.

## Pass accounting and identities

Pinned `gencontelem_f2f.f` loops over tie index `i`, then `iloop=1,2`. Its exit condition after each pass is `iact!=0 || iprev==0 || nmethod==4`, so pass 2 is conditional for each tie: a tie with no prior contact does not enter it, while another tie in the same call may. The pass-1 face hook is before the dead-element `cycle`, records source face offsets and live/dead status, and therefore retains dead and zero-span faces. Point rows are emitted over the live source spans. This matches the attempt04 reader rule that pass 1 is the required full roster and pass 2 is an observed subset; a tie without pass-2 face rows is unavailable in pass 2, not a zero result.

The reader checks each pass-1 face against the externally bound encoded-face roster, checks tie/ordinal order and contiguous source-wide offsets, and requires the pass-1 span total to equal `nintpoint`. For every observed pass-2 tie, it requires the full per-tie face count and exact `(face, start, end, span, status)` equality to pass 1. Candidate totals are reconciled to live spans and mapped/unmapped/generated/excluded reason partitions. The sink's point key includes tie, pass, face ordinal, encoded slave face, face-local ordinal, and exact binary64 slave coordinates; `igauss` is used only as a sweep-local trial lookup. Cross-sweep joins additionally require exact `vold` state-vector equality and adjacent iteration identity. These invariants bind captured runtime rows; they do not establish geometric search/clipping completeness or prove omitted candidates do not exist.

## Confirmed defect: writer completion is weaker than reader validation

`ccxcap_face_` records pass-2 faces but does not retain pass-1 rows for comparison. `ccxcap_generation_end_` checks pass-2 face count, first/last offsets, and aggregate span against pass 1. It does not compare each pass-2 row's encoded face, status, or individual offsets/spans. If those row identities differ while those aggregates remain equal, the C sink leaves `wjcc_error` clear and can write `GEN_END.complete=1` and `RUN_END.complete=1`. `capture_reader.py` does compare every pass-2 row against its pass-1 lookup and rejects such a stream, so the official reader gate closes the acceptance path. The serialized completion flags themselves are nevertheless weaker than the contract's exact identity language; any consumer must require reader validation, and the writer's completion status should eventually be aligned with that contract.

## Mechanics boundary and limits

The three-source patch is additions-only: every upstream line is preserved in order, and my in-memory reconstruction matched the pinned modified-file hashes. The Fortran changes assign only new `wjcap_*` locals and call capture hooks; the C sink copies source state into private storage, updates private statistics, and writes only the exclusive sidecar. I found no added assignment to solver contact arrays, `isol`, loads, restraints, geometry, or material/contact controls. This supports source-level nonreplacement only. The extra allocations, hashing, loops, and sidecar I/O were not exercised in a native run, so runtime equivalence, instrumentation behavior, mechanics acceptance, and joint acceptance remain unestablished.
