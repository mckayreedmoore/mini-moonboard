# Current geometric interface map — attempt 02

This append-only packet preserves the nominal BRep contact graph and panel/kicker receiver screen for `led-clearance-2x6-runner-seated-blocks-v1`. It is a geometry observation only.

The full graph contains 50 member nodes and 1225 unordered pairs. The collector evaluated 147 pairs by exact BRep after a 147-pair AABB broadphase; 1078 AABB-separated pairs were not evaluated exactly. Geometry states: {'finite_opposed_planar_touch': 115, 'separated': 1104, 'zero_area_touch_or_unresolved': 6}.

Axis inventory joins: 92 candidate bolt axes, 12 retained frame-bolt axes, and 66 Hillman panel/kicker axes (58 unchanged, 8 moved). The receiver screen is the current 66-axis map; it is not an installed-fastener result.

## Six unresolved exact-BRep pairs

These are preserved as `zero_area_touch_or_unresolved`; no contact is inferred:

- `pair:center_principal_cleat_left|kicker_left`: `center_principal_cleat_left, kicker_left`
- `pair:center_principal_cleat_right|kicker_right`: `center_principal_cleat_right, kicker_right`
- `pair:kicker_left|main_lower_right`: `kicker_left, main_lower_right`
- `pair:kicker_right|main_lower_left`: `kicker_right, main_lower_left`
- `pair:main_lower_left|main_upper_right`: `main_lower_left, main_upper_right`
- `pair:main_lower_right|main_upper_left`: `main_lower_right, main_upper_left`

## Provenance and validation

The collectors were run on a rebuild from `build_current_geometry()` and were passed the exact pinned `site/owner-wood-joints-review-report.json` report. The returned contact-graph body matches `complete-contact-graph-attempt02.json` after excluding only that prior driver wrapper's `parent_run` metadata. The receiver-screen JSON matches `receiver-screen-attempt04.json` exactly. A diagnostic run passed the builder's construction report instead; its only graph difference was the report provenance hash. That run is rejected and retained only as a documented diagnostic in `scope-summary.json`.

`source-pins.json` binds the frozen report, 68 geometry source-input hashes, producer modules, current attempt04 manifest, all 50 current STEP files, and upstream comparator outputs. `scope-summary.json` is deterministically reconstructed from the preserved JSON. Quick verification checks pins, joins, pair list, output hashes, and checksums:

```sh
python3 verify_packet.py --verify
sha256sum -c SHA256SUMS
```

Full nominal-BRep regeneration uses the repository CadQuery environment and takes about five minutes:

```sh
.venv/bin/python verify_packet.py --rebuild
```

## Limits

Every value is a nominal CAD/BRep observation. This packet establishes no active bearing, face ownership, load transfer, stiffness, fastener engagement, resistance, response, mechanical equivalence, capacity, acceptance, fabrication release, or climbing release. The 1,078 AABB-separated pairs remain unmeasured by exact BRep. The graph's preserved `parent_run.seconds` is metadata from the pinned prior live run; it is not a timing claim for the reconstruction performed for this packet.

Artifact hashes: graph `7806242ac48b198becf5db97b16b6a5605021b8d86b964f0f02adb6806aeec26`, receiver screen `851495f2ccc80f286a7eae97fc54bcf602a478bb7d4e13eb28e2ae44cfb87991`, source pins `590112932d73dc57da015382a8ebf6e0fc85a8c5e8338549f381b8bd7732ba5c`.
