# WJ-04 full-stock stagger probe

Status: isolated, unaccepted single-station geometry hypothesis. This artifact does not change the active candidate, canonical WJ-04 configuration, or its manifest. It records no accepted replacement duties and grants no purchase, drilling, fabrication, or structural release.

## Reproduction and provenance

Run from the repository root:

```sh
uv run python -m scripts.wood_joint_wj04_full_stock_probe > /tmp/wj04-full-stock-probe.json
```

The archived JSON is the byte-for-byte output from that run. It completed in about 97 seconds with exit code 0. Report SHA-256: `2c247cf249b0dddcd403c1466efe6d8a7ddd32366f8b8b3294657318bd42da6a`. Producer SHA-256: `965b997a2b3f4ecb4c39e161fc9dde1757ff8a4c8d7bc8acc90d851a122f8bde`.

The report binds its source inputs and shape/runtime modules by SHA-256. It does not record a complete Python/CAD-kernel package-version manifest, so matching those hashes alone does not guarantee bit-for-bit recreation across runtime environments. It was generated against the recorded source snapshot; do not treat it as current if any input hash differs.

## What this screen found

- All four modeled installed stacks had no reported component intersections, and all eight head/nut washer annuli were fully supported by the modeled geometry. This is a geometric screen, not physical installation or acceptance.
- With the upper service rail present, its face sits 17.05 mm from the cleat face. The modeled 50 mm axial approach envelope overlaps it by 32.95 mm. Both rail-axis insertion paths also intersect the upper service rail and retained connector/SDS envelopes; no order among the four stacks clears the modeled insertion paths (0 of 24 orders). Upper-rail removal or another assembly pose is not modeled. Broad tool envelopes do not prove physical access or impossibility.
- The placement screen leaves signed load direction unclassified and reports only partial directional witnesses. It omits complete member-specific host face/end-distance checks. The conditional 4D/5D/7D comparisons and `C_delta` value are not NDS acceptance or capacity evidence.
- The 6-inch 1/4-20 bolt SKU remains a provisional candidate. Catalog `Lb` and `Lg` are inspection bounds, not exact full-thread transition locations. Delivered body end, thread transition, nut engagement, and received dimensions require measurement; no thread-fit pass is established.
- Timber stock review found that two 88.9 mm cleats facing across the 105.95 mm upper/lower service-rail gap would overlap by 71.85 mm. Therefore this single-cleat station cannot be copied into a repeated full layout. A shared-cleat topology or alternate pose needs its own analysis.

This probe represents one hypothetical cleat and four provisional bolts only. It does not establish material condition, structural capacity, a complete load path, integrated service clearance, or suitability for fabrication.
