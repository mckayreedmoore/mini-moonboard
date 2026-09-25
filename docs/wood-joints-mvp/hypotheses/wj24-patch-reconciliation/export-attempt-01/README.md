# WJ24 baseline representative five-body export, attempt 01

Status: source-bound diagnostic export completed 2026-09-24. Parent ran the prepared exporter once against retained live WJ16 and complete WJ24 geometry objects. No CAD rebuild was performed during archival.

The exported bundle is preserved as [baseline-wj24-five-body-export.tar.gz](baseline-wj24-five-body-export.tar.gz); [bundle-contents.json](bundle-contents.json) records each member's exact byte count and SHA-256. Its seven members are the source-bound reconciliation report, original export hash index, and five separate STEP solids. The archived `reconciliation.json` member has SHA-256 `256af45c2a6b2b48726d86f95e2f4febdd8cad726d690738e9cb1fad87a89711`.

The parent execution record, launcher snapshot, producer snapshot and test snapshot are retained beside the bundle. Source hashes before and after export are equal. [readback-verification.json](readback-verification.json) records a successful in-memory readback of every archive member against the contents index, and the five STEP export readbacks passed solid count, volume, centroid, bounds and symmetric-difference identity checks.

Four of the five exported bodies match their archived WJ16 shapes exactly. `base_principal_center_right` is the changed body; its symmetric difference is 13,676.889460908 mm³. See the reconciliation report for source-cut replay, replacement screw-axis removal and added candidate-bore provenance. The G7 relief is excluded: this is the retained WJ24 baseline lower cleat, with no relief variant exported.

This is a geometry/export diagnostic only. No mesh, native solve, capacity, fabrication or structural release was produced.
