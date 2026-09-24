# WJ-03 compact outer head-withdrawal screen

Diagnostic archive for the compact outer third hypothesis. This report is not an access, fabrication, or structural acceptance.

- Source: `scripts/wood_joint_wj03_head_withdrawal.py` at SHA256 `970513cb82c15355049138bd779c11e6cbd520a2fa2e570c2db7645a7a0564ea`.
- Test: `tests/test_wood_joint_wj03_head_withdrawal.py` at SHA256 `bfe233b4c0893e50bd5d5c837a7aeff39441892d8194bbccca2d6ebb38eb56a1`.
- Run: one compact-access materialization (42.67 s), then 20 stack reports (1,358.75 s); total 1,401.47 s. Source hashes checked before run.
- Archived JSON SHA256: `03cb0201b41b1a7dbded07bb5917301c078f698c950032c3524715583252b9f5`.
- Catalog ratchet dimensions follow Ko-ken's 3725Z drawing. Handle width/thickness remain explicit assumed proxies, not published dimensions or guaranteed bounds. Socket/ratchet fit, bolt thread behavior, manual holding and hardware capture remain unverified.

## Read carefully

The old axial shaft-withdrawal path used `wood_joint_wj04_tool_access.translation_sweep()`, which encloses a moving shape in an oriented box made from bounding-box corners. For a cylindrical shaft moving on its own axis, that box has square cross-section corners. It overlaps drilled circular bores and washer IDs even when the nominal round shaft fits their circular openings. All 20 shaft paths therefore reported hits against only their own receiver timbers and own head/nut washer rings. Treat those hits as conservative-envelope artifacts, not demonstrated blockages or clear paths. The archived JSON preserves these results for provenance; a separate exact coaxial-cylindrical sweep supplements them.

Other broad-envelope results are also diagnostic. Seated socket envelopes were clear for all 20 stacks. Head ratchet strokes and head-tool withdrawal showed proxy hits at four header stacks; stationary counterhold-ratchet envelopes and their short exit showed proxy hits at 18 stacks. Tool-pair stroke and withdrawal screens were clear for all 20 stacks. These ratchet results use assumed D/H handle-box cross-sections and discrete heading samples; no physical ratchet fit or access conclusion follows. Two nut-washer short exits had proxy hits against bottom rails; all head-washer exits were clear in this screen. Full capture/retrieval remains unverified.

See [archived JSON](wj03-head-withdrawal.json). Primary ratchet references: [Ko-ken 3725Z catalog page](https://kokenusa.com/products/z-series-3-8-sq-dr-reversible-ratchet-l-178mm-72-tooth) and [manufacturer drawing](https://www.koken-tool.co.jp/en/panflets/KOKEN202101EN.pdf).
