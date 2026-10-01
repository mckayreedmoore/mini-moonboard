# Attempt05 offline test coverage review

Reviewed the attempt05 offline capture package under the repository working
agreements. I did not read earlier review reports. The pins below match the
checked-in inventory; the three archived upstream source members and the three
generated patched members also match their respective hashes in
`source-pins.json`.

## Verification

The documented command passed all 23 tests in 6.172 seconds:

```sh
PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest discover -s tests -v
```

The suite compiles and runs only the standalone sink harnesses. No patched
CalculiX build, Docker invocation, solver, or coupon was run. The result
supports offline reader, sink-harness, and patch-preparation behavior only.

`source-pins.json` SHA-256: `a671a0c53266cfae4986c403d63fb31c9180c8fafbf885e5018e52621efb2570`.

| Reviewed package file | SHA-256 |
| --- | --- |
| `README.md` | `0559cbcd150cf28f419d1a701617e18ebcd83d2e69d6753c38be1469b939f67f` |
| `build/context/Makefile.upstream` | `344fbd0b5c89bdcce2580dcaf46bd50f2ffada01b26ff783b9adbdd2af1613b4` |
| `build/context/base-build-manifest.json` | `496efd407abd71c8ced12e3631ea2d223dee1fe6ec1b1b757a2e5e28dfb19e66` |
| `build/context/base-image-pin.json` | `3b6f8a487a7e343fa51979bbc812f1451f41823a117cdbd62be6159078877b16` |
| `build/context/capture.patch` | `e536c707f83c9ef11ffdfc55480d750ffd7b9dc68a73abd3e72c648eb20b4dba` |
| `build/context/patch-preparation.json` | `807a54891435ed85173885af3da070c34241382da3c3b60866eea9a2e89930da` |
| `build/context/source.tar.bz2` | `9c88385c10fb04f5dc6c4e98027a51bebdd8aee3920e05190d6c1dd08357d6e7` |
| `capture-contract.json` | `6bc77a005a1f21cf83c77d7bf47514030e8fe4e7d35562629b28971b7a12db38` |
| `capture-sink.inc` | `8ca64a40d8f5c4a093cd0750b9c31de85109dc9acc3158cb8502a5b512907a52` |
| `capture_reader.py` | `ab2d466508895e28a4e45656f60bbd0aee6b27997fc5378d6f9044333223a1e4` |
| `prepare_capture.py` | `030745d7701b4517f428bc31010b9b2c2f275d4da0af20df8c4b07f0d8def090` |
| `tests/sink_harness.c` | `ec9dff8b60cce943dc74ae0f21a759aa5dfbb9b5eb34c1555cec4850f6c8aa96` |
| `tests/test_capture.py` | `1de39e927c22806719368bdfc3b5dea3e0f05fc57a48ae624b9a6384957e72b8` |
| `tests/test_patch_policy.py` | `f9f414dc0ed7006a5873b889b2df00ef988899132f72d779d8ba449c7e6f78ec` |

The archived upstream members match the recorded `upstream_sha256` values, and
`prepare_capture.build_delta()` produces the recorded patched-member values:

| Source member | Upstream SHA-256 | Generated SHA-256 |
| --- | --- | --- |
| `CalculiX/ccx_2.23/src/ccx_2.23.c` | `5b3fffaa55699b61f23c86ddb6bbf016b2411e6beb9a002231338bdd041fd144` | `66ddbd1215f69e03a869a32c0ca24c7649649943427d1e57f0d5e423171beebd` |
| `CalculiX/ccx_2.23/src/gencontelem_f2f.f` | `853e2159f37666bc1430516bb4e5c65b6ba484ef1866454930e66cf317fb8afe` | `110dea22c7578330496be81f05d9f406b0eb4635bc2b56adc4cd4766459f5b85` |
| `CalculiX/ccx_2.23/src/nonlingeo.c` | `8684bb6d7fa7097c0a854db5a45eb9e2d11adfde574e688184ecbbbad56ff83f` | `47c5703d96dd66aaf4efe29a9d9199820638732e98dd332934a43dac36c6ec9c` |

## Coverage findings

1. **P2 — The writer's combined candidate-row ceiling is not tested across
   both passes.** The boundary case in `tests/test_capture.py:216-233` creates
   exactly 250,000 pass-1 rows; its over-limit case edits one reader summary.
   `tests/sink_harness.c:108-117` never emits pass 2 in this case. A writer
   regression that resets its counter before optional pass 2 would therefore
   evade these tests, although the contract caps pass 1 plus every observed
   pass 2 together. Add a case below the ceiling in pass 1 whose observed
   pass-2 rows take the combined total above it, and require overflow/incomplete
   publication behavior.

2. **P2 — Reader tests do not reject a provenance hash mismatch.** Positive
   captures and expected bindings all use the same synthetic values
   (`tests/test_capture.py:45-53, 67-85`); the mutation tests alter identity,
   counts, and statuses but not one of the seven input/include/source/patch/
   binary/pair/face hashes. The exact binding comparison is an important guard
   against accepting a sidecar for a different frozen run. Add at least one
   mutation of a valid `RUN_BEGIN` hash or its corresponding expected binding
   and assert `CaptureError`.

3. **P3 — Publication collision and disabled-capture lifecycle paths lack
   runtime cases.** `run_sink_with_status()` always supplies a fresh absent
   destination (`tests/test_capture.py:67-85`), and the harness has no mode that
   removes `CCX_CONTACT_CAPTURE_PATH`. Thus tests do not exercise the documented
   no-overwrite hard-link publication when the destination already exists, or
   the no-path disabled branch. Add an existing-destination case that confirms
   its contents remain unchanged and a no-path case that confirms no sidecar
   is published and generation hooks remain inert. Current code uses `link()`
   and caches path availability in `wjcc_open()`; this is a coverage gap, not a
   reproduced failure.

Positive coverage is otherwise substantial for the stated offline scope: the
tests exercise accepted and rejected iteration links, multi-step sink lifetime,
per-tie optional pass 2, writer pass-2 mismatch rejection, reader identity/
offset mutation rejection, reason/span/join/acceptance mutations, trial force
and energy aggregates, unavailable energy as `NA`, byte-cap overflow, flush/
close injection, additions-only patch generation, and selected Fortran/C caller
policy violations. The patch-policy checks are lexical and structural; the
package correctly limits their claim and does not treat them as a production
solver build or native-runtime validation.
