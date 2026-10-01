# Proposed starting stock envelopes — 2026-10-01

## Result

This source-bound scenario covers `compact-floor-flush-wood-joints-development`, revision `led-clearance-2x6-runner-seated-blocks-v1`, against `current-full-frame-input-manifest-attempt04`. It emits 44 piece records: 20 frame timbers and 24 proposed connector blocks. All 44 current finished STEP solids fit their proposed original starting-stock boxes by the declared BRep containment checks. The four proposed 4×6-rip blocks also fit their separate prepared sections. This is geometry-only containment evidence; it does not establish real stock, yield, member acceptance, or any build or climbing release.

Frame blank lengths come from the first entry of each source-inventory `source_blank_dimensions_mm`; frame sections come from `actual_source_section_mm`. Four frame rows (`base_floor_left`, `base_floor_right`, `lumber_leg_left`, `lumber_leg_right`) remain source-only geometry. The other 16 have `current_rebuilt_host` composition roles. Their source blank dimensions are proposal inputs, while the exact finished STEP is separately pinned and checked; this does not treat a source raw host as the current finished member.

The 24 block lengths and prepared sections come from the current source-yield proposal and are cross-checked against all 30 attempt02 cut-yield arithmetic scenarios. The four ripped blocks start from original 4×6 stock `[88.9, 139.7]` mm, with the proposed later sections `[83.9, 139.7]` mm for the center principal pair and `[88.9, 133.35]` mm for the inner-frame pair. Their grade remains unassigned after ripping.

Consumer fields are `stock_blank_length_mm`, `original_stock_section_mm`, optional `prepared_section_mm`, `frame_status`, `current_finished_step_path`, `current_finished_step_sha256`, `proposed_frame`, `original_stock_containment`, optional `prepared_section_containment`, and `containment_status`. Stable containment values are `CONTAINED`, `INCOMPATIBLE`, and `AMBIGUOUS`. Use `original_stock_containment.status` and, where `prepared_section_required` is true, `prepared_section_containment.status` as the geometry gates.

## Geometry and limits

The conditional grain axis comes from the pinned frame or block material-frame map. Two perpendicular section directions are derived from planar faces of each exact saved STEP: each plane normal is projected perpendicular to the grain axis, and the resulting directions define the stock `q/r` basis. The source-inventory assembly transform and local extents are not used to place stock. The section dimensions are tried in both `q/r` mappings; the fitting mapping with least surplus is selected, with source dimension order as the deterministic tie-break. Ambiguous plane axes are kept as `AMBIGUOUS` records.

The proposed stock datum is the finished solid’s minimum grain station. Any length surplus is placed at the positive-grain end; section surplus is centered equally across each opposing face. The finished STEP is imported as one valid solid, checked against its pinned bundle bounds and volume, transformed into the proposed axes for oriented extents, then tested with exact kernel `finished.cut(stock)` and `finished.intersect(stock)` operations. Numerical limits are 0.00001 mm for extents and 0.001 mm³ for volume differences, matching the pinned solids bundle tolerances. The run used CadQuery 2.8.0 and OCP 7.9.3.1.1.

The emitted boxes are in-memory analytical proposals. They do not prove raw-host identity, saw kerf, end trim, surfacing or cleanup loss, defects, post-rip grade, receiving condition, delivered lengths, or a nesting/yield schedule. Frame `DF-L No. 2` is a conditional source basis, not a received grade. Block species, grade, moisture, treatment, defects, and material values are unassigned; the four 4×6 rips have no post-rip inspection/grade disposition. No purchasing, cutting, drilling, fabrication, native solve, structural acceptance, or climbing acceptance is implied.

The raw `envelopes.json` and `source-pins.json` outputs are intentionally local-only ignored files. Recreate and verify them from the repository root with:

```sh
./.venv/bin/python docs/wood-joints-mvp/hypotheses/current-stock-envelope-reconciliation-2026-10-01/envelopes.py --write
./.venv/bin/python docs/wood-joints-mvp/hypotheses/current-stock-envelope-reconciliation-2026-10-01/envelopes.py --verify
./.venv/bin/python -m pytest -q docs/wood-joints-mvp/hypotheses/current-stock-envelope-reconciliation-2026-10-01/test_envelopes.py
./.venv/bin/ruff check docs/wood-joints-mvp/hypotheses/current-stock-envelope-reconciliation-2026-10-01/envelopes.py docs/wood-joints-mvp/hypotheses/current-stock-envelope-reconciliation-2026-10-01/test_envelopes.py
```

## Result and producer hashes

All values below are SHA-256 digests over exact local file bytes; the JSON outputs use deterministic canonical UTF-8 JSON bytes with a final newline.

| Artifact | Local path | SHA-256 |
| --- | --- | --- |
| Envelope report | `docs/wood-joints-mvp/hypotheses/current-stock-envelope-reconciliation-2026-10-01/envelopes.json` | `0f13d1c697d8c7b3dcb1a5db5a7ab215e05bc9bee4e729fc35763ff449436e01` |
| Source pins | `docs/wood-joints-mvp/hypotheses/current-stock-envelope-reconciliation-2026-10-01/source-pins.json` | `8ba6fb89c1f9e05fd975d742e5bd593a5b3bbdca2ed06d3815d18217d038540d` |
| Producer | `docs/wood-joints-mvp/hypotheses/current-stock-envelope-reconciliation-2026-10-01/envelopes.py` | `a4aa9e6d8d22178bdae28cab4c829d1f45fb5633575dd7119fe57cf03b374b0d` |
| Focused tests | `docs/wood-joints-mvp/hypotheses/current-stock-envelope-reconciliation-2026-10-01/test_envelopes.py` | `8320761c62ec4a4a01375961edc8418fab87df0a13a3180851f2cdc3e4e49636` |

## Pinned source artifacts and producer files

The local raw source paths below are frozen by `source-pins.json`; all 44 STEP paths are listed separately. The file also pins this producer and its focused tests.

| Role | Local path | SHA-256 |
| --- | --- | --- |
| `block_material_map` | `docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-block-material-frame-map-attempt02/material-frame-map.json` | `8705b8f100a2d3355c236fc19e6798bb7ad4862ba2d51826cf63a88db1285480` |
| `current_manifest` | `docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-full-frame-input-manifest-attempt04/current-full-frame-input-manifest.json` | `9e682e28c3d4c3c0594863f82c6b74d19dee2700f3856d34e1a26f69082e4f11` |
| `cut_inventory` | `docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-timber-cut-inventory-attempt01/inventory.json` | `bacc2c669923c34164e12dc227d414a96dcac1d0861d43fa785f0d3712a25af4` |
| `cut_yield_scenario` | `docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-timber-cut-yield-scenario-attempt02/current-timber-cut-yield-scenarios.json` | `df1f4e2df03f1f65870d71f4a63708fbc06a4dd0a5ca9f9f527ff30a63249c30` |
| `frame_material_map` | `docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-frame-timber-material-frame-map-attempt01/current-frame-timber-material-frame-map.json` | `f867b4926ed23c9f356005c134778e138c8b1230547f0b69be7c3f9bc2a42409` |
| `grade_disposition` | `docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-timber-grade-disposition-attempt01/grade-disposition.json` | `c0e5c0bb9a32403a6fe047a3b995667f2d35df81b1333a68f773c318ed560e86` |
| `member_solids` | `docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-full-frame-member-solids-attempt01/bundle/current-full-frame-member-solids.json` | `8979d678f7b45d3b75fa465e810b0910d72874c5c1c705290d1fcb2bf2b78420` |
| `source_inventory` | `docs/wood-joints-mvp/source-inventory.json` | `07af4c3eb642cf3887595fe4415eb65404cdcf74d66c5c7bb182847ef21c2d78` |
| `timber_source_yield` | `docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-timber-source-yield-attempt01/current-timber-source-yield.json` | `2c710708d5e775d742375e28fadd323ecfe7f8e81c186c6028704c903a65266c` |
| `producer:block_material_map` | `docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-block-material-frame-map-attempt02/produce.py` | `e66e21f8fbd3672ea826fe32f67b45ac3034db385c7b59f2ddbb084cb7f25690` |
| `producer:current_manifest` | `docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-full-frame-input-manifest-attempt04/produce.py` | `966e4b5918fefe06741ca828a3b4c3f6d353b735a1fc70df6a98a91b4e98b1f4` |
| `producer:cut_inventory` | `docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-timber-cut-inventory-attempt01/produce.py` | `fa60c1758ce923ffae03fc27c739e039bf98c216e775bf86b280d2d255a73634` |
| `producer:cut_yield_scenario` | `scripts/build_current_timber_cut_yield_scenario_attempt02.py` | `027479a0f082c036da5bba603defea348c4d97ca4be7f76626177a03e077bc7d` |
| `producer:frame_material_map` | `docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-frame-timber-material-frame-map-attempt01/produce.py` | `d60c904fb9276d55dfd0ab5c86746b354b9e000f8fa126eb35f56d42ffbfac11` |
| `producer:grade_disposition_verifier` | `docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-timber-grade-disposition-attempt01/verify.py` | `f9511af9a94bb07c6874bae38475e9b92e8ba78c03999720822a2bec6431ef5e` |
| `producer:member_solids` | `docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-full-frame-member-solids-attempt01/produce.py` | `922e3e294ba9bfc4e3b27476035bc78194c6151f22b282e182015a3d4b58d1d9` |
| `producer:source_inventory` | `scripts/wood_joint_inventory.py` | `7e3cd529274eb61ada892fb0ad397ec7b9dcb26d3372f8df0b76c7bb06b4077e` |
| `producer:stock_envelopes` | `docs/wood-joints-mvp/hypotheses/current-stock-envelope-reconciliation-2026-10-01/envelopes.py` | `a4aa9e6d8d22178bdae28cab4c829d1f45fb5633575dd7119fe57cf03b374b0d` |
| `producer:timber_source_yield` | `docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-timber-source-yield-attempt01/produce.py` | `8b2b33e591dcb287dc9f7f05405a09b739b0c6770a919a55a30649af2ee44ad6` |
| `test:stock_envelopes` | `docs/wood-joints-mvp/hypotheses/current-stock-envelope-reconciliation-2026-10-01/test_envelopes.py` | `8320761c62ec4a4a01375961edc8418fab87df0a13a3180851f2cdc3e4e49636` |

## Current finished STEP solids

| Piece ID | Local STEP path | SHA-256 |
| --- | --- | --- |
| `base_floor_left` | `docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-full-frame-member-solids-attempt01/bundle/members/base_floor_left.step` | `e36c73da89d5b209231122b44d433a67c444657ec23a49725916a3339733071d` |
| `base_floor_right` | `docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-full-frame-member-solids-attempt01/bundle/members/base_floor_right.step` | `64d0e1aa25f2c223bbc2d19814643bf7e980a4238fe8a1c20a40272b21b58247` |
| `base_header` | `docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-full-frame-member-solids-attempt01/bundle/members/base_header.step` | `41ba159020ed41463ff1c886716cdbf69123e23481be704391a247eee1382082` |
| `base_post_center_left` | `docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-full-frame-member-solids-attempt01/bundle/members/base_post_center_left.step` | `02ae8ecc26d2f7637b3b915dd2b1b5eceff9140770475692cce083084670b607` |
| `base_post_center_right` | `docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-full-frame-member-solids-attempt01/bundle/members/base_post_center_right.step` | `e7f348058ce6927714ff9bd01130fae1a01adbfa708b00753c99ffe64fb343bd` |
| `base_post_outer_left` | `docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-full-frame-member-solids-attempt01/bundle/members/base_post_outer_left.step` | `cdf9bb35e7ff2fda58bfdd604f69dedcba88b6b34149f874c03335abe90a1dce` |
| `base_post_outer_right` | `docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-full-frame-member-solids-attempt01/bundle/members/base_post_outer_right.step` | `d4335f36aaaa271856b4fb42bdadea4cef49c0fea6481afde317d67f9cbd23de` |
| `base_principal_center_left` | `docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-full-frame-member-solids-attempt01/bundle/members/base_principal_center_left.step` | `ff537b4187c9a9e928eac6e89f44d2f3466c56280c58891e460dbb185bc8c253` |
| `base_principal_center_right` | `docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-full-frame-member-solids-attempt01/bundle/members/base_principal_center_right.step` | `9053a7210a781e919038a4a823f867325dd5c78907bd028d8b9e76dc0b46df58` |
| `base_rail_bottom_left` | `docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-full-frame-member-solids-attempt01/bundle/members/base_rail_bottom_left.step` | `724d46fa7902a949b79b0fd6132c5e57c580be80aad7d059c29e04494ff79923` |
| `base_rail_bottom_right` | `docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-full-frame-member-solids-attempt01/bundle/members/base_rail_bottom_right.step` | `9542614527922ed3cf2e7b13b239244e82820e38577f1c88959219906a6f2a7b` |
| `base_rail_service_lower_left` | `docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-full-frame-member-solids-attempt01/bundle/members/base_rail_service_lower_left.step` | `ae82b9906b29852685bd90d86e6b3add4f6a4e2603b34138cc28b186558e6fda` |
| `base_rail_service_lower_right` | `docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-full-frame-member-solids-attempt01/bundle/members/base_rail_service_lower_right.step` | `14c6bc16d7c08cd0782ac7766fa8dbea2555ad9c0de59ca580823444d86cb809` |
| `base_rail_service_upper_left` | `docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-full-frame-member-solids-attempt01/bundle/members/base_rail_service_upper_left.step` | `4b6a3eede080310530a7633e2761a798f5f65a9dece5eb3793cd4aec009b9687` |
| `base_rail_service_upper_right` | `docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-full-frame-member-solids-attempt01/bundle/members/base_rail_service_upper_right.step` | `87c620c3684cfa1044c7ebe7fb8e654b6b79a91beb5b2f1b1709c2279a49a2b5` |
| `base_rail_top` | `docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-full-frame-member-solids-attempt01/bundle/members/base_rail_top.step` | `79b4f7f66f35928ed383d0e396ce221d9a4302136b088a7bcd41749c52a10a60` |
| `base_side_left` | `docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-full-frame-member-solids-attempt01/bundle/members/base_side_left.step` | `237c3fa6aa0b52c39124580810d048e38919b99b9a1fb5db5a2423e7eda62fdf` |
| `base_side_right` | `docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-full-frame-member-solids-attempt01/bundle/members/base_side_right.step` | `ddb6ac20f1f50a9036448eb5680fdc486532ff3826ce52d566baf685a800a59f` |
| `bottom_center_left_cleat` | `docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-full-frame-member-solids-attempt01/bundle/members/bottom_center_left_cleat.step` | `90f6b6cb0b7dc032108244de4a24cbfd4ea1642849a4aef66672a5ac818c4003` |
| `bottom_center_right_cleat` | `docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-full-frame-member-solids-attempt01/bundle/members/bottom_center_right_cleat.step` | `6f2f7abd66b36311fcbfe3c977de1f04b3bc183557831c949843da669cecc1d7` |
| `bottom_outer_left_cleat` | `docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-full-frame-member-solids-attempt01/bundle/members/bottom_outer_left_cleat.step` | `28d1b5fee748c38e30e3d2618c8377cfe374c7ccd0b520736c25841720824438` |
| `bottom_outer_right_cleat` | `docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-full-frame-member-solids-attempt01/bundle/members/bottom_outer_right_cleat.step` | `91878e6857d848bda7c266e69d7f97cef152686d6cc6096ebfd8a6c5008d8501` |
| `center_post_cleat_left` | `docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-full-frame-member-solids-attempt01/bundle/members/center_post_cleat_left.step` | `7901f21ed12dbd6fca26b2c8bf67670cc63304549be2d2e81083ac098a8af21b` |
| `center_post_cleat_right` | `docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-full-frame-member-solids-attempt01/bundle/members/center_post_cleat_right.step` | `6ba16357d43dd35aeb4552d4e3a4e4ad594e5286ecedc902182a1f7ac4eb70e3` |
| `center_principal_cleat_left` | `docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-full-frame-member-solids-attempt01/bundle/members/center_principal_cleat_left.step` | `dd4bacfe1df31b87e6e24d87d3ab80f22a604bba90531659e97d6a3b5d8f0652` |
| `center_principal_cleat_right` | `docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-full-frame-member-solids-attempt01/bundle/members/center_principal_cleat_right.step` | `eef681f8f99c1af026c439692b813a51b0412892d4137ee7dd9748388ed3f0a2` |
| `knee_outer_left_inner_frame_block` | `docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-full-frame-member-solids-attempt01/bundle/members/knee_outer_left_inner_frame_block.step` | `9c7957e22686dff467f533f013172743c9bc8e7a9783331490b8e7c93d92e568` |
| `knee_outer_left_spine` | `docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-full-frame-member-solids-attempt01/bundle/members/knee_outer_left_spine.step` | `081a3930dd1334e317fc0116a24d80b4b70e9cb3f36b928cda403f66194bb5c0` |
| `knee_outer_right_inner_frame_block` | `docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-full-frame-member-solids-attempt01/bundle/members/knee_outer_right_inner_frame_block.step` | `4f2d6e8656aab94e1b0fc773325a944041682dfbf4c203ce1f2dd017845046e0` |
| `knee_outer_right_spine` | `docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-full-frame-member-solids-attempt01/bundle/members/knee_outer_right_spine.step` | `f70ade3760f1615cc31f687bc4cf4c334d27db3b8b41e35e615e15b92c4e1faa` |
| `left_service_inner_lower_cleat` | `docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-full-frame-member-solids-attempt01/bundle/members/left_service_inner_lower_cleat.step` | `632cda5ba7f06bdf1fa4fb0658992259b27237b412dcc74f5ce999529581ce74` |
| `left_service_inner_upper_cleat` | `docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-full-frame-member-solids-attempt01/bundle/members/left_service_inner_upper_cleat.step` | `584106340fb39652d97e2c45cc54feca9a61ed3faeb0eeaedaf08a6e0a32747e` |
| `left_service_outer_lower_cleat` | `docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-full-frame-member-solids-attempt01/bundle/members/left_service_outer_lower_cleat.step` | `7a2c73ba176e1579e6920598a5b266b22d9bd7e1771b1e72b2de481f29b7c309` |
| `left_service_outer_upper_cleat` | `docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-full-frame-member-solids-attempt01/bundle/members/left_service_outer_upper_cleat.step` | `5594cd1293bb181d61deb3aaa549c4e44845db5e365f3e621dbd10579b48938a` |
| `lumber_leg_left` | `docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-full-frame-member-solids-attempt01/bundle/members/lumber_leg_left.step` | `1416e3aec21eea2993542f8266649ebe0aec50b3ec6444f445f18f88cbffa065` |
| `lumber_leg_right` | `docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-full-frame-member-solids-attempt01/bundle/members/lumber_leg_right.step` | `e346646efb8bdf9c03d45dfa024900622abcd65fe0d58bf11c6dcd3735bedff4` |
| `top_center_left_cleat` | `docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-full-frame-member-solids-attempt01/bundle/members/top_center_left_cleat.step` | `9fa44336e7f77b443fd735b337d7089b763a5a4b592f915f5a0f022bebba7d86` |
| `top_center_right_cleat` | `docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-full-frame-member-solids-attempt01/bundle/members/top_center_right_cleat.step` | `95408c99e9fda6a274f71f764b95c3298c7077f1d0cf6e91fd45a7efcbb2493d` |
| `top_outer_left_cleat` | `docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-full-frame-member-solids-attempt01/bundle/members/top_outer_left_cleat.step` | `c4ecd881a9dc2e78195d028bf360cc42da86e97129ac44db7fafd7c77f50ba88` |
| `top_outer_right_cleat` | `docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-full-frame-member-solids-attempt01/bundle/members/top_outer_right_cleat.step` | `70b94b711f629b6b1d955083c7eafddb07b104c04878c46ae032ba4c953be25c` |
| `wj04_lower_full_stock_cleat` | `docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-full-frame-member-solids-attempt01/bundle/members/wj04_lower_full_stock_cleat.step` | `231262125246a456aab725c97175e6035e3112bd7a06e0753f232ca1a80b29b3` |
| `wj04_upper_g7_crosscut_full_stock_cleat` | `docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-full-frame-member-solids-attempt01/bundle/members/wj04_upper_g7_crosscut_full_stock_cleat.step` | `76d96d84027339baa0daf9cc84f1d0e976b0cd9f4955dde0f0504a1424c0dc04` |
| `wj06_outer_lower_right_cleat` | `docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-full-frame-member-solids-attempt01/bundle/members/wj06_outer_lower_right_cleat.step` | `b12617c11fb72f33d3bc1cade8fa2a1281294c678d7a4d994eda9ab629805459` |
| `wj06_outer_upper_right_cleat` | `docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-full-frame-member-solids-attempt01/bundle/members/wj06_outer_upper_right_cleat.step` | `974eb688e5c59af38bb655c543a6fcf35e8a772c7ce5af568ed99eac7eb5ddca` |

The full per-piece stock basis, oriented extents, BRep outside/intersection volumes, source dimensions, status, and identity digest are in the generated local `envelopes.json`. Its 44-item semantic identity digest is ``a4d4ef98b3d1aedbc68f0dfa69c33d290123ae5804903ac452f53f89f39517a4`.
