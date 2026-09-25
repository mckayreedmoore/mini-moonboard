# Resume source-integrity checkpoint, September 24, 2026

Status: read-only provenance audit. Source and report hashes were first
collected at 2026-09-24 21:21:32 UTC and rechecked at 21:25:39 UTC. The WJ24
scene was intentionally regenerated at 21:24:33 UTC, then independently
rechecked at 21:26:50 UTC. This audit covers selected-candidate authority and
preserved A12-left baseline output, the latest WJ24 integrated/static,
provisional hardware-inventory and LED-extraction artifacts, the exported
WJ24 review scene, and the latest archived wood-mesh evidence. It checks bytes
and source bindings only. It does not re-evaluate geometry, mechanics,
hardware suitability, physical conditions, or acceptance.

No source hashes or archived outputs were changed to make a check pass.
Checks were limited to the permitted authority-integrity helper and direct
SHA-256, manifest, JSON-binding, source-archive, and tar-member comparisons.
This audit opened no CAD model, ran no native solve or full test suite, and
regenerated no artifact. The parent separately regenerated the WJ24 scene as
described below.

## Authority and preserved selected baseline

The read-only command
uv run --no-sync python -m scripts.wood_joint_authority_integrity passes
against handoff commit df7f5eca86ae831b35a8bcf9e6dcd7ae8af852bb at the
inspected repository head ec33d9c55cdb084d0b5c34bf28cb748f300b0b9e.
The selected machine authority remains compact-floor-flush-development.
The current and barrel-nut authority files match their handoff bytes; the
selected kerf-right export manifest and all 725 referenced export files also
match. All wood-joint release flags remain false. This establishes byte
preservation only.

The preserved A12-left geometry has an internally valid but older model
fingerprint. Its manifest hashes match geometry.json, report.json.gz, and
sources.zip; the model file inside the ZIP hashes to the geometry's recorded
4cc03e08…. The live model now hashes to 8764bec5…. The geometry JSON itself
hashes to e62f402f…, and the preserved ZIP to b8d1b6d0…. The current
source-inventory.json binds the live model at 8764bec5…. This mismatch is the
known September 17 source change documented in
local-validation-2026-09-24.md: the geometry and its ZIP agree with each
other, while both predate the current model. It is changed-source staleness,
not evidence of archive corruption. Do not rewrite the old geometry hash or
represent its frozen case as a current-model solve.

The selected source inventory is internally consistent with current bytes:
all four connection/stock/profile inputs and all three recorded runtime
modules match. This includes the current model fingerprint above. The
historical geometry's different source fingerprint does not change which
candidate current-candidate.json selects.

## WJ24 static, inventory, extraction, and scene

The latest integrated-static composition and diagnostic have valid manifests,
parent-audit pins, and producer/source bindings. All 68 top-level composition
input hashes and all 226 recorded family-source fingerprints match current
files. The seven producers named by the composition, including the WJ18
upstream compositor/diagnostic and WJ24 compositor/diagnostic, match their
recorded SHA-256 values. The report manifests verify all nine listed files.
The diagnostic's source-provenance record reports no family-input hash
mismatches. These bytes support the recorded unaccepted static status; they do
not turn the composition into an accepted layout.

The WJ24 hardware inventory manifest verifies all six entries. Its producer
snapshot and execution record both hash to the current
scripts/wood_joint_wj24_hardware_inventory.py at
7a42f290…. Its source-provenance section carries the same 68 current
composition inputs and zero family-input mismatches. The 520 component roles
are modeled CAD roles, not inspected or purchased hardware.

The LED-extraction manifest verifies all five entries. Its recorded producer
hash faea52e5… matches the preserved producer snapshot. The original
run path names a temporary /tmp/wj24-led-extraction-probe.py; the live
temporary path is not part of this source tree, so the archived snapshot is
the preserved source for that run. Its report pins the same composition hash
and current input set. The G7 obstruction remains a bounded extraction
finding, not a whole-harness transport conclusion.

The scene was regenerated after WJ24 exact-report recovery, replacing the
earlier 121,231,665-byte export (SHA-256 448839973e083f18871d1556abe481d15123a1b2bdb927bce9a881a104512245)
with a 9,181,070-byte export (SHA-256
b80baec6b4435f4cfad724efdc25df787d04251f1a1b7203ba63782fb4b485f0). The
parent's recovery record reports exact equality to the pinned composition;
the viewer-generation record reports the exact output hash and unchanged
exporter, viewer, and test-source hashes before and after generation
(exporter SHA-256 271d3c267035e7d9087eb25144ca24cb8301b36dffce3215a62aae0d45cc1db2).
The recovery record reports unchanged composition inputs and
exact_report_equal=true. These temporary execution records are at
/tmp/wj24-session-recovery-20260924-attempt01/execution.json and
/tmp/wj24-viewer-resume-20260924-attempt01/execution.json. This is an
intentional output refresh, not source drift or archive corruption. I
independently confirmed that the new scene embeds the current composition and
diagnostic exactly, and pins the current composition, diagnostic, contact
supplement, and LED report hashes. Its selected kerf-right baseline manifest
hash is 42f2a659…; all 725 scene baseline-asset hashes match current export
bytes. Its status is REVISE, with capacity, acceptance, installation,
fabrication, structural, and climbing claims false. The scene has no
self-contained exporter hash; the temporary run record supplies the
before/after producer hashes and exact scene output hash.

## Wood mesh archive

The latest complete mesh archive is WJ04 representative-joint mesh-only
evidence, separate from the WJ24 layout. Its outer manifest verifies all
seven entries. Its contents index matches all six members in the compressed
bundle, including the mesh report and input deck. The report pins the four
mesh-worker sources before and after execution; each current source matches
its archived snapshot. All seven current STEP-bundle inputs also match the
recorded before/after input hashes. The mesh report hashes to
e8af81e6…, the deck to 43f50fd6…, and the compressed archive to b4a92cf5….

That record is mesh preparation only: it has no solver cards and no
structural solve. It does not supply mechanics or acceptance for WJ24 or the
selected baseline.

## Hash snapshot

Full SHA-256 values below identify the bytes observed during this audit. The
WJ24 scene row is the post-regeneration value checked at 21:26:50 UTC; the
other report hashes were rechecked at 21:25:39 UTC. The corresponding archive
manifests and source maps are the complete sets used for the counts in this
audit.

| Object | SHA-256 |
| --- | --- |
| current-candidate.json | f4505746a0a33eac1771708fbc376686b801e2c2af3053d9447fbbc6e22491a4 |
| barrel-nut-candidate.json | 61b76d0648604529988ddf6c6264c158f2dde85d334d235a95864d3595a14e9c |
| docs/wood-joints-mvp/source-inventory.json | 07af4c3eb642cf3887595fe4415eb65404cdcf74d66c5c7bb182847ef21c2d78 |
| fea/results/clear-space-floorflush/a12-left/geometry.json | e62f402f10403e205f279e60fe991ef8d0b9b13ff73efb981ff33090e389e747 |
| fea/results/clear-space-floorflush/a12-left/sources.zip | b8d1b6d095b715780ceaab8fb6e2c98da2f2040c08d745eaf95ad5506b3cf9ac |
| mini_moonboard/compact_floor_flush_frame.py | 8764bec57564efa79f2636e589aa0e35b229c48975c791eec5c47b20183bf17a |
| docs/wood-joints-mvp/hypotheses/wj24-integrated-static/composition.json | c4cebb2870e337ece0b429eb099514c36ea5fac79bc9d321fbdcf45734310dfb |
| docs/wood-joints-mvp/hypotheses/wj24-integrated-static/diagnostic.json | bc3c5e70c2f53db8d491d329d58fa8faaf9524db585ac16fe4d215926ebe7b3b |
| docs/wood-joints-mvp/hypotheses/wj24-integrated-static/parent-audit.json | 66d228a102bff5588c4588588a6dc460a834e9d1c770778ca8ecedb8f78674ea |
| docs/wood-joints-mvp/hypotheses/wj24-integrated-static/sha256.json | 8a44ffec38288c7ad006b680109d78f0e5e128bee57dc14dba15e4ff9d3af6fa |
| docs/wood-joints-mvp/hypotheses/wj24-hardware-inventory/inventory.json | cb11b4f14d9c6cb02bb1ecb5789579d096b6ae436171f91eabea9891f1927624 |
| docs/wood-joints-mvp/hypotheses/wj24-hardware-inventory/sha256.json | 4c6b16d6fa9391d9a084fcef95156498dcd26fe98b096fcceddac62927a0473d |
| docs/wood-joints-mvp/hypotheses/wj24-led-extraction/geometry.json | bca7b306d3fc4beb620c06833273e9119bd3c22346361332a0d38b6ef705806e |
| docs/wood-joints-mvp/hypotheses/wj24-led-extraction/sha256.json | 8cfe4ecd69c50bcd64798887e65ee46c3b7de47a2ac436d462600cd33c078304 |
| site/owner-wood-joints-wj24-scene.json, current | b80baec6b4435f4cfad724efdc25df787d04251f1a1b7203ba63782fb4b485f0 |
| /tmp/wj24-viewer-resume-20260924-attempt01/execution.json | 69139b4221bcd911c39fa0ea2486e6dd66456d1ee8aa13c08e6f628e50fc613d |
| /tmp/wj24-session-recovery-20260924-attempt01/execution.json | 90fd3a523fe4b71545dff7f6056d0d56e7cabf42f64c939d252e2503e19b18dc |
| docs/wood-joints-mvp/hypotheses/wj04-patch-mesh/attempt-03/complete-mesh-evidence.tar.gz | b4a92cf5d0a76082bce736efe576dda1e8732924d4a19013501727ace7c63a58 |
| docs/wood-joints-mvp/hypotheses/wj04-patch-mesh/attempt-03/sha256.json | 946f7a185cd62cec8ee4a19e087c4d3bb66b0a087c04ed744d45496f86b04ee2 |

## Regeneration order if inputs change

Keep the selected-baseline authority and its preserved geometry on their own
lane. Run the authority-preservation check against the pinned handoff; do not
regenerate the stale historical A12-left result as a way to repair its
fingerprint.

For WJ24, freeze and hash the complete source-inventory, runtime modules,
connection/stock inputs, family producers, and upstream WJ18 records first.
Regenerate only the local family integrations affected by a changed input,
then compose WJ24 and produce its full static diagnostic. From that same
composition, regenerate the hardware inventory and LED-extraction report;
refresh the finite-contact supplement when one of its own inputs changes.
Export the WJ24 scene after the composition, diagnostic, and scene supplements
are final, then refresh its recorded output hash.

For the separate WJ04 mesh path, update the geometry producer output and STEP
input bundle before meshing whenever either changes. Then create the mesh
report/deck, run the independent parent audit, and only then rebuild the
compressed bundle, contents index, and outer hash manifest. Changes to WJ24
do not by themselves stale this WJ04 mesh; changes to its bound geometry,
bundle, or mesh producers do.
