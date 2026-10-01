# Independent post-build audit: attempt09 build attempt01

Audit date: 2026-09-29 UTC. Scope: compile/build provenance only for `implicit-bounded-contact-capture-attempt09-build-attempt01`. This review does not qualify capture semantics, the known-answer coupon, native mechanics, or a joint, and it does not assert mechanical acceptance.

**Result: PASS, 35/35 checks. No build-provenance blocker found.** The parent build completed from the frozen attempt09 inputs. The extracted binary and build manifest match the recorded hashes; the image's first 15 filesystem layers match the locked base's 15 layers; the archive contains 1,197 source files whose hashes match the inherited source manifest; and all three attempt09 target hashes match patch preparation.

The reviewer used read-only file hashing, JSON/archive inspection, build-log inspection, and `nm -g` static symbol-table inspection. The reviewer did not invoke Docker, the extracted binary, or a solver. `nm` read the binary's symbol table; it did not execute it. The recorded build itself ran the Docker build recipe, which compiled with `make` and inspected symbols with `nm`. The host created and copied from an extraction container, but the execution record says it was never started. No native solver case ran.

## Primary artifact hashes

| Artifact | SHA-256 |
|---|---|
| `prebuild-input-pins.json` | `b39b0d99abf38521648d96be03fda9ff4e5d54a1fac3a99b7678e1683b83db25` |
| `build_attempt.py` | `e483bfe67cf447a5ac29a81bdf379a770de6716eabc5e4a9323ae7f8ac4e3458` |
| `build-execution.json` | `daa3313293351c40fac693cf8432c6c95963a54562829d7c1a64780bfd49837e` |
| `output/build-manifest.json` | `752d0072004a9a364204a2745aedc00996d8a0ed014f82a2a0e748dc3677f584` |
| `output/ccx-bounded-contact-capture-2.23-attempt09-build01` | `2d80b317a5ee4377e160d212fbfdb403d4b10a92cbc94605f7cd75c0f324f417` |
| `docker-build.log` | `c5001059d2cac0940b4d613c68fbaba619a0d1ecefe21c74d600d59c14536375` |
| `base-image-before.json` | `b6d719be799e6f0ed7b44d31fa82c3c38dbfe2644938ce2b6a3adb566645e4dc` |
| `base-image-locked.json` | `c497ef1510672e29a2ed615447e3bfe62a203e3b899c0ebf51e3b9ab6c9a6c64` |
| `build-image-inspect.json` | `a2b43bb1c6456fd614e8bab409c9b064515233cfbef856bc5e94ecc0078b975b` |
| `parent-build-preflight.json` | `dc513e66b9654416a0ed5dd572d80cc31f999af3016701a9d4d00abc10230767` |
| `context/source.tar.bz2` | `9c88385c10fb04f5dc6c4e98027a51bebdd8aee3920e05190d6c1dd08357d6e7` |
| `context/capture.patch` | `abaaa6d65d709edb53043619e4a974184b2ec278ef0a3e1cba9dde7c92a84e5e` |
| `context/patch-preparation.json` | `9f74479079853fe5cee752378feba8705f3b557f6c9b503d8a1bfd3760803917` |
| `context/base-build-manifest.json` | `496efd407abd71c8ced12e3631ea2d223dee1fe6ec1b1b757a2e5e28dfb19e66` |
| `context/base-image-pin.json` | `825eb60732d2513eaa1df8af46fdf934848b2b61285088e993f0dd4b1726945d` |
| `context/attempt09-base-image-pin.json` | `3b6f8a487a7e343fa51979bbc812f1451f41823a117cdbd62be6159078877b16` |

Recorded base image ID: `sha256:31336f517557f5dd5f97d85b1e6e15947fd1c10b44edc1364dbba4c1a5ab6c38`. Recorded build image ID: `sha256:9040d55065a2dd78790b4c2af1564915d29b968d1fc236fa490ada03e0491e1e`. The built image has 20 layers; its first 15 exactly equal the locked base's 15 layers.

## Exact check results and evidence

1. **PASS — Frozen prebuild pin SHA.** Actual SHA-256 is `b39b0d99abf38521648d96be03fda9ff4e5d54a1fac3a99b7678e1683b83db25`, matching the parent preflight record.
2. **PASS — Prebuild pin count is 12.** `prebuild-input-pins.json` declares exactly 12 file hashes.
3. **PASS — README input pin.** `README.md`: `2be835aec4570c7468dbb39088ca525215afb39b9fa9760ef3f7b068f21a8278`.
4. **PASS — Attempt09 source-pin input.** `attempt09-source-pins.json`: `bcbf1bc560cbf436fb0ad6547ac5e6abf10e83b849829c42eac256f66c60de62`.
5. **PASS — Host wrapper input.** `build_attempt.py`: `e483bfe67cf447a5ac29a81bdf379a770de6716eabc5e4a9323ae7f8ac4e3458`.
6. **PASS — Dockerfile input.** `context/Dockerfile`: `59ead9612f69394f0b5a366c54ebde6235a93f85e031b81425a3ea029d77f76d`.
7. **PASS — Upstream Makefile input.** `context/Makefile.upstream`: `344fbd0b5c89bdcce2580dcaf46bd50f2ffada01b26ff783b9adbdd2af1613b4`.
8. **PASS — Attempt09 base-pin input.** `context/attempt09-base-image-pin.json`: `3b6f8a487a7e343fa51979bbc812f1451f41823a117cdbd62be6159078877b16`.
9. **PASS — Inherited base-build manifest input.** `context/base-build-manifest.json`: `496efd407abd71c8ced12e3631ea2d223dee1fe6ec1b1b757a2e5e28dfb19e66`.
10. **PASS — Derived base-image pin input.** `context/base-image-pin.json`: `825eb60732d2513eaa1df8af46fdf934848b2b61285088e993f0dd4b1726945d`.
11. **PASS — Attempt09 patch input.** `context/capture.patch`: `abaaa6d65d709edb53043619e4a974184b2ec278ef0a3e1cba9dde7c92a84e5e`.
12. **PASS — Attempt09 patch-preparation input.** `context/patch-preparation.json`: `9f74479079853fe5cee752378feba8705f3b557f6c9b503d8a1bfd3760803917`.
13. **PASS — In-image build recorder input.** `context/record_capture_build.py`: `d6d6e0742353699b2c65066db5290491ce7fc6652ec474844aeb83e2992c94de`.
14. **PASS — Pinned source archive input.** `context/source.tar.bz2`: `9c88385c10fb04f5dc6c4e98027a51bebdd8aee3920e05190d6c1dd08357d6e7`.
15. **PASS — Wrapper self-hash matches its declared prebuild pin.** Actual `build_attempt.py` SHA matches check 5 and the pin entry.
16. **PASS — Extracted binary hash agrees with both records.** Actual and recorded SHA-256 is `2d80b317a5ee4377e160d212fbfdb403d4b10a92cbc94605f7cd75c0f324f417`.
17. **PASS — Build-manifest hash agrees with execution record.** Actual and recorded SHA-256 is `752d0072004a9a364204a2745aedc00996d8a0ed014f82a2a0e748dc3677f584`.
18. **PASS — Docker build-log hash agrees with execution record.** Actual and recorded SHA-256 is `c5001059d2cac0940b4d613c68fbaba619a0d1ecefe21c74d600d59c14536375`.
19. **PASS — Source archive digest is consistent.** Archive SHA equals the build manifest and inherited base manifest's upstream archive SHA.
20. **PASS — Base pin digests and identity agree.** Both pin-file hashes match the build manifest; source and derived pins, build manifest, and execution record identify base ID `sha256:31336f517557f5dd5f97d85b1e6e15947fd1c10b44edc1364dbba4c1a5ab6c38`.
21. **PASS — Locked reference matches pin and execution.** All record `mini-moonboard-fea:ccx-upstream-2.23-v1-pinned-31336f517557f5dd5f97d85b1e6e15947fd1c10b44edc1364dbba4c1a5ab6c38`.
22. **PASS — Original base tag and locked alias agree.** Before-build and locked records both resolve to the pinned ID and share the expected base layer list.
23. **PASS — Build image ID and tag agree.** Image inspection ID matches execution record `sha256:9040d55065a2dd78790b4c2af1564915d29b968d1fc236fa490ada03e0491e1e`, with tag `mini-moonboard-fea:ccx-bounded-contact-capture-attempt09-build01`.
24. **PASS — Built-image base-layer prefix matches.** The built image's first 15 layers exactly equal all 15 layers in the locked base record; the built image has 20 layers total.
25. **PASS — Execution record asserts layer-prefix verification.** `base_layer_prefix_verified` is `true`.
26. **PASS — Source file count and inherited manifest count are 1,197.** Build manifest records 1,197 files; inherited source manifest has 1,197 entries.
27. **PASS — Archive files exactly match inherited source manifest.** Read-only tar inspection found 1,197 files, and every member name/hash matches the inherited manifest.
28. **PASS — Three patched targets appear in locked order.** `nonlingeo.c`, `gencontelem_f2f.f`, then `ccx_2.23.c`.
29. **PASS — Target source and modified hashes agree with preparation.** The three archive hashes match recorded upstream target hashes; all three modified hashes match attempt09 patch preparation.
30. **PASS — Nine image-local context hashes match current files and prebuild pins.** All nine manifest context entries agree with both.
31. **PASS — Attempt09 patch-preparation schema.** Schema is `ccx223_bounded_capture_patch_generation/v9`.
32. **PASS — Build does not claim solver execution or mechanical acceptance.** Both flags are `false` in build manifest and execution record.
33. **PASS — No native solver case or extraction-container start is recorded.** Execution record has `solver_executed=false`, `native_solver_case_run=false`, `extraction_container_started=false`; parent preflight reports no visible solver processes and no solver reservation.
34. **PASS — Recorded build command is offline and pinned.** It uses `docker build --pull=false --no-cache --network=none --progress=plain`, passing both locked reference and expected base ID.
35. **PASS — Output directory contains only expected artifacts.** It contains the dedicated binary and `build-manifest.json`, with no extra or overwritten output.

## Static symbol and build-log evidence

`nm -g` found these required global text symbols in the extracted binary: `ccxcap_generation_begin_`, `ccxcap_face_`, `ccxcap_point_`, `ccxcap_trial_`, `ccxcap_iteration_link_`, and `ccxcap_finish_`. It also found `ccxcap_trial_end_`. No binary execution was performed.

The Docker log records the in-image command as `python3 record_capture_build.py`; that recorder invokes `make` and `nm`, not the produced solver executable. The log ends with successful make completion and BuildKit image export. It contains nonfatal compiler warnings in legacy source; compilation and linking completed. The build execution record records the extraction container ID `f65a198e76f9f389c9efc94f3767fd75f5d9b27930bde26b566365f0fbf02dd9`, created and removed without start.
