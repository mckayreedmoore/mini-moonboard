# First-knot global contact-overlap screen

This read-only audit parses model-wide `CDIS` and `CNUM` from the two immutable first-knot DAT snapshots at `t = 0.001 s`. The source process was still running at both captures, so each result is one accepted state, not a terminal response or history.

## Verification

Both actual decks have SHA-256 `48649259ba8441429a5dd094ae08487e3713d6b5b860ac39ca1acf71b837d963`. Direct card parsing found one global `*CONTACT PRINT` request `CDIS,CSTR,CELS,CNUM` and 35 pair-specific requests `CF,CFN,CFS` in WJCP_001–WJCP_035 order. The parser requires five fields on every face-face CDIS row (slave element, face, normal, tangential 1, tangential 2), finite component values, one target-time CNUM scalar, and equality of CDIS rows to CNUM.

The pinned [CalculiX 2.21 manual, §7.23](https://www.dhondt.de/ccx_2.21.pdf) (local PDF SHA-256 `16b6bab5a3f1a40a21fff62379f95c804a58d93758ab2e9a489b18d911dc20c8`) defines positive normal CDIS as normal material overlap for active face-to-face integration points and CNUM as the scalar total number of contact elements. The corresponding source archive SHA-256 `52a20ef7216c6e2de75eae460539915640e3140ec4a2f631a9301e01eda605ad` is recorded in [`native-contact-recovery-review.md`](../native-contact-recovery-review.md) (file SHA-256 `39f1c66c88cddccc93ba88737d3fb42a409290ea74269499f3d5e0b26ff0ab55`): `printout.f` lines 401–415 and 615–621 writes the face-face heading and CNUM as `ne-ne0+1`; `printoutelem.f` lines 78–90 writes each face-face CDIS row as `ielem, iface, normal, tang1, tang2`. The repeated element/face identifiers are not treated as unique row keys.

## Results

| Branch | CDIS rows | CNUM | Count check | Positive normal rows | Maximum positive overlap (mm) | Record | Contract limit (mm) | Limit exceeded? |
| --- | ---: | ---: | --- | ---: | ---: | --- | ---: | --- |
| K=100000 baseline | 24280 | 24280 | pass | 2049 | 2.616841e-08 | row 2166, element 4846, face 4 | 0.000575 | no |
| K=10000 child | 110318 | 110318 | pass | 942 | 2.273343e-08 | row 4966, element 8228, face 3 | 0.000575 | no |

The largest observed positive normal CDIS is `2.616841e-08 mm` in the K=100000 baseline snapshot, or `4.55102783e-05` of the declared limit. Neither snapshot exceeds the contract’s 0.000575 mm numerical triage threshold.

## Pair-report coverage remains partial

The independent [matched pair-force audit](../aligned-first-knot-penalty-contact-comparison-attempt01/README.md) (JSON SHA-256 `b3161c0652e11ced440990aad681f93f9e3a1e9becc58b3803976ce8dde328df`) remains the source for pair-specific force coverage. K=100000 has 33 complete CF/CFN/CFS triplets, WJCP_034 CF only, and WJCP_035 absent. K=10000 has 34 complete triplets and WJCP_035 CF+CFN only (no CFS). A globally complete CDIS block is not pair-attributed and does not fill those missing fields.

## Limits

The threshold is the contract’s analyst-set numerical screen, not a bearing, strength, mesh-accuracy, or acceptance criterion. Global CDIS records do not identify their WJCP pair in the printed block, so this report makes no per-pair overlap claim. These are two single accepted states, not terminal runs or contact histories.

Machine-readable counts, row locations and hashes are in [`overlap-screen.json`](overlap-screen.json); the concise table is in [`global-overlap-summary.csv`](global-overlap-summary.csv).
