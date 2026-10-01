# Current finished-surface axis correspondence

This analysis joins the frozen attempt04 source axes to finite, bore-like cylindrical face patches in the exact current finished STEP solids. It is a bounded geometric correspondence report, not a hole inspection, fastener verification, fit check, or joint acceptance. It does not replay or modify STEP geometry.

The join uses the reviewed `led-clearance-2x6-runner-seated-blocks-v1` manifest and the [current finished CAD surface register](surfaces.md). The register contains 20 frame members and 24 candidate blocks. It explicitly excludes the six plywood panels (`kicker_left`, `kicker_right`, `main_lower_left`, `main_lower_right`, `main_upper_left`, `main_upper_right`); panel-member surface coverage is outside this 44-piece wood register.

## Scope and result

The three source groups remain separate by identity and policy:

| Source group | Axes | Receiver memberships | Matched memberships |
| --- | ---: | ---: | ---: |
| Candidate structural bolt axes | 92 | 188 | 188 |
| Retained starting frame-bolt axes | 12 | 24 | 24 |
| Hillman 42605 panel/kicker screw axes | 66 | 66 | 66 |
| **Total** | **170** | **278** | **278** |

Each current receiver membership has one unambiguous, finite, contained `bore_like` CYLINDER patch match. Of the 310 CYLINDER face patches in the surface register, 278 are assigned to these source receiver memberships and 32 remain unassigned to the listed axes. There are no unmatched receiver memberships, receiver gaps, ambiguous side classifications, partial-interval matches, or multiple-patch matches in this frozen result. Patch IDs and full candidate diagnostics remain in the local JSON output. This result says which surface patch corresponds geometrically to a source axis under the recorded bounds; it does not prove a drilled or usable hole.

The eight owner-moved panel/kicker screws remain individually identified and each corresponds to a patch on its current receiver station:

| Axis IDs | Current receiver | Finished STEP face patches |
| --- | --- | --- |
| `round_kicker_left_center_1`, `round_kicker_left_center_2` | `base_post_center_left` | `facet009`, `facet010` |
| `round_kicker_right_center_1`, `round_kicker_right_center_2` | `base_post_center_right` | `facet009`, `facet010` |
| `round_panel_lower_left_edge_1`, `round_panel_lower_left_edge_2` | `base_rail_bottom_left` | `facet004`, `facet006` |
| `round_panel_lower_right_edge_1`, `round_panel_lower_right_edge_2` | `base_rail_bottom_right` | `facet016`, `facet014` |

The face identifiers above are prefixed by the receiver member, for example `base_post_center_left/facet009`. The manifest's 58 unchanged and eight moved status split is retained. A current STEP patch at a moved axis supports its placement correspondence; it does not by itself prove the historical source cutter was regenerated at that revised station.

## Datum and finite-axis semantics

The join transforms each source datum and direction into the receiver's proposed stock `g/q/r` frame. It rejects non-unit, non-orthogonal, or left-handed raw frame bases. The frame origin and dimensions are proposed stock-envelope metadata, not a delivered-lumber datum or grain inspection.

Each group's finite interval follows its source fields:

- Candidate bolts use `shaft_center_global_xyz_mm` as the named center and `modeled_shaft_occupied_length_mm` as a centered interval, `[-L/2, +L/2]` along `axis_head_to_nut_global`.
- The 12 retained bolts use `origin_global_xyz_mm` and `source_occupied_length_mm` as `[0, L]` along `axis_global_xyz`, consistent with the modeled `Connection.start` cylinder envelope. This does not identify an underhead datum or delivered shank length. These are starting arrangements for current recheck; no historical acceptance transfers.
- The 66 Hillman axes use `origin_global_xyz_mm` and the manifest's `purchased_nominal_length_mm`, reconciled for every ID to the current source inventory's `shop_purchased_length_mm`, as `[0, L]` on the current receiver screen axis. For this inventory, `L = 63.5 mm`; the historical `source_occupied_length_mm = 50.8 mm` is retained as provenance but is not used for this current interval. `wood_joint_frame.py` uses `shop_purchased_length_mm` from `Connection.start` for its modeled purchased-envelope cutter. This is source CAD metadata, not observed screw installation or an instruction to buy, cut, pilot, or countersink.

The receiver-screen source maps all eight owner-moved IDs to their revised receiver station while carrying the same 63.5 mm shop-length envelope. The pinned WJ24 compositor validates the source-inventory cutter maps; it does not establish that a moved-axis cut was regenerated at each revised station. The exact current finished STEP patch correspondence is recorded separately from that cutter provenance. Neither source proves installation or load transfer.

For each receiver, an association requires a coaxial axis and cylinder line, a finite cylinder-patch interval wholly contained in the source axis interval, and `material_side_geometry = bore_like`. The producer's pinned geometric tolerances are axis direction sine error `1e-6`, centerline distance `1e-5 mm`, and patch containment `1e-5 mm`. Partial, outside, missing, or unresolved intervals and exterior/ambiguous cylinder classifications are retained as nonmatches rather than inferred assignments. Cylinder radius and source diameter are reported only as context; radius is not used as a drill-bit size or a match requirement.

## Provenance and replay

The report binds all source-axis IDs to the exact attempt04 manifest and validates each receiver against its path and STEP SHA in that manifest. The finished-member bundle has one valid, round-trip-checked solid for each receiver. Both axis write and verify check every path, byte size and SHA-256 in the surface pin document, including the 44 STEP files and extraction dependencies. This byte check needs no CAD runtime; the separate surface replay additionally re-extracts the geometry. The source-pin record also pins the surface report/producer, member-solids bundle, source inventory, current `wood_joint_frame.py` and `box_frame.py`, receiver-screen source, WJ24 compositor, and manifest producer. The source pin records their roles and limits.

The raw report and pin file are ignored, local-only artifacts. From the repository root, the standard-library synthetic suite needs no CAD runtime:

```sh
python3 -m unittest discover \
  -s docs/wood-joints-mvp/hypotheses/current-finished-feature-register-2026-10-01 \
  -p 'test_axis_features.py' -v
```

Create outputs exclusively, then replay them read-only:

```sh
python3 docs/wood-joints-mvp/hypotheses/current-finished-feature-register-2026-10-01/axis_features.py --write
python3 docs/wood-joints-mvp/hypotheses/current-finished-feature-register-2026-10-01/axis_features.py --verify
```

`--write` refuses to overwrite either output. `--verify` reconstructs canonical report bytes from the current pinned inputs and requires exact equality with both saved outputs.

| Artifact | SHA-256 |
| --- | --- |
| attempt04 input manifest | `9e682e28c3d4c3c0594863f82c6b74d19dee2700f3856d34e1a26f69082e4f11` |
| finished surface report | `33fff67eee4bc4e96ccef5703f6eebd0d4e004541c6114a4b1da4a5332b2f6eb` |
| finished surface producer | `a58e8f76b0d308352c734b6eab6bdea8c3adb75ab1c538e0905997d0232bab4f` |
| finished surface source pins | `0e8cb56407f14e93d7ab95741115d4355a954eb845ae503365ba1da1149bd9cd` |
| current finished member-solids bundle | `8979d678f7b45d3b75fa465e810b0910d72874c5c1c705290d1fcb2bf2b78420` |
| axis correspondence producer | `e9787320589db65f1443b2c40607ed347cd5c4e8d5c8a2b9be73a5619275104f` |
| focused synthetic tests | `1357949b7434f51089346d1186e2cd04406e51f055b0e338232cb518197b57e7` |
| local `axis-features.json` report | `bebb4274cdecfb6ad0b0f26850d85a16570c245ea9f7d478c0b05c12b4513e19` |
| local `axis-source-pins.json` | `7a501047c003174c15461ae12e3cd47af4e4bf59b1d40d3c8e5b76d8e1904d34` |

The report and source pins remain ignored local evidence and are not included in version control. This metadata establishes no approved machining, drilling, purchasing, fastener fit, member capacity, joint capacity, inspection, fabrication release, or climbing release.
