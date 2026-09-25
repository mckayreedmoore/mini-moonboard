# WJ24 viewer review archive

This folder preserves the WJ24 viewer export record and final browser evidence. The [manifest](manifest.json) lists the archived files, byte sizes, SHA-256 digests, and their roles.

## Snapshot provenance

The export record in [execution.json](export-evidence/execution.json) records the viewer HTML hash as `1305b49ad5122e17be103b513963e441239f9fe5417d025dd939d9ca2daef626` before and after the scene export. The matching file in [export-time-snapshots](export-time-snapshots/) is that export-time source snapshot; it is not the final reviewed viewer.

After export, the viewer received accessibility and responsive-layout updates. The separately captured [final-review HTML snapshot](final-review-snapshots/wood-joints-wj24-viewer.html.snapshot) has SHA-256 `4e505823957e5271963bac629fa87e282e6e368d3a58e8fd5a577b9148ccd16d`. That HTML version was used for the final browser review. The accompanying [scene payload snapshot](final-review-snapshots/owner-wood-joints-wj24-scene.json.snapshot) has SHA-256 `b80baec6b4435f4cfad724efdc25df787d04251f1a1b7203ba63782fb4b485f0` and is 9,181,070 bytes.

The export record reports that composition exactly reproduced its archived report, source hashes stayed unchanged during export, and no native solve, release, or publication occurred. The earlier mobile-overflow result and screenshots remain under `browser-evidence/intermediate/`, labeled as pre-final responsive fixes. They are retained for provenance and are superseded by the final results below.

## Final browser evidence

[browser-check.json](browser-evidence/final/browser-check.json) records a successful Chromium render and interaction review. It confirms 538 pinned baseline assets rendered once, 187 replaced baseline visuals suppressed, six finding cards displayed, and the source identity plus `REVISE` / false-release status visible. All five layer controls changed the rendered scene; the left, right, and full-frame views were distinct; arrow rotation and plus/minus zoom changed the render. No page errors, failed requests, console errors, or HTTP error responses occurred.

The final responsive screenshots and checks cover 390×844 and 320×568. At both sizes the canvas resized to the viewport and the expanded inspection panel stayed within its bounds without horizontal overflow. The buttons and scene-layer labels retained 44-pixel targets. Camera, layer, and keyboard screenshots are in the same `browser-evidence/final/` folder. [keyboard-minus-check.json](browser-evidence/final/keyboard-minus-check.json) records the final down-arrow and minus-key check.

This archive documents browser presentation and control behavior. It does not establish joint acceptance, capacity, installation, fabrication, structural release, or climbing release. Screen-reader verification remains pending.
