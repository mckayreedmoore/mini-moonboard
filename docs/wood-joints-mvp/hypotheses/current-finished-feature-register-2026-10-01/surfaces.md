# Current finished CAD surface register

This register describes every trimmed face in the 44 exact finished STEP solids for `led-clearance-2x6-runner-seated-blocks-v1`, using the proposed stock frames from the reviewed current stock envelope packet. It reads the saved STEP solids as supplied and does not regenerate or change reviewed geometry.

The stock frame origin is the original proposed stock box’s minimum g/q/r corner expressed in global XYZ. Its basis columns are the proposed `g`, `q`, and `r` directions, and its dimensions are the proposed original stock spans in that order. Every raw basis column is checked for unit length, orthogonality, and right-handed orientation. All eight stock-box corners, each feature centroid, and each topological face vertex are checked through global-to-stock-to-global transforms at `1e-7 mm`. This frame is a proposal coordinate system, not a delivered-stock datum.

Each feature ID is `member_id/facetNNN`; the three-digit facet number is the one-based face order returned by the pinned CadQuery import of that exact STEP file. Each row retains area, centroid, global and stock-frame bounds, topological vertices, face parameter bounds, trim wires and edge curves. Planes carry their oriented normal, signed plane equation stations, and absolute angles to g/q/r. No plane is called an approved seat, taper, or cut. Cylinders carry the OCP axis, radius, finite axis interval from the face’s oriented bounding box after aligning the reported axis to local z, and the parameter interval used to cross-check it.

Cylinder `material_side_geometry` is derived from the outward oriented solid-face normal dotted with the radial direction at the trimmed UV midpoint, after OCP face classification confirms that the sample lies inside its trim. The current 310 patches all have valid on-face samples and dot values from `-1.0000000000000002` to `-0.9999999999999999`, so they are recorded as `bore_like` geometry. The synthetic known-answer checks distinguish that case from an exterior cylinder. This field describes face orientation only; it does not establish a drill axis, passing hole, joint role, approved cut, or fastener instruction.

## Result and replay

The register contains **44** member records and **44** exact finished STEP bindings, covering **648** faces: **338 PLANE** and **310 CYLINDER**. There are zero unsupported face kinds and zero ambiguous cylinder-side samples. Every imported solid is valid and has one solid; its path, file SHA-256, byte size, shape-summary digest, face count, bounding box, and volume are checked against the pinned sources.

The raw canonical JSON outputs are ignored local files. Replay with the pinned runtime from the repository root:

```sh
.venv/bin/python docs/wood-joints-mvp/hypotheses/current-finished-feature-register-2026-10-01/surfaces.py --write
.venv/bin/python docs/wood-joints-mvp/hypotheses/current-finished-feature-register-2026-10-01/surfaces.py --verify
```

`--write` is exclusive and refuses to overwrite existing outputs. The focused synthetic tests cover a translated and rotated stock frame with a bore, pocket-floor plane, and taper plane; opposite material-side signs for an exterior cylinder and a bore; point/frame round trips; invalid scaled, mirrored, and non-orthogonal bases; unknown-surface face coverage; source-pin byte changes; and noncanonical output bytes.

## Full artifact hashes

| Artifact | Path | SHA-256 |
| --- | --- | --- |
| Reviewed stock envelopes | `docs/wood-joints-mvp/hypotheses/current-stock-envelope-reconciliation-2026-10-01/envelopes.json` | `0f13d1c697d8c7b3dcb1a5db5a7ab215e05bc9bee4e729fc35763ff449436e01` |
| Reviewed stock source pins | `docs/wood-joints-mvp/hypotheses/current-stock-envelope-reconciliation-2026-10-01/source-pins.json` | `8ba6fb89c1f9e05fd975d742e5bd593a5b3bbdca2ed06d3815d18217d038540d` |
| Reviewed stock envelope producer | `docs/wood-joints-mvp/hypotheses/current-stock-envelope-reconciliation-2026-10-01/envelopes.py` | `a4aa9e6d8d22178bdae28cab4c829d1f45fb5633575dd7119fe57cf03b374b0d` |
| Current manifest04 | `docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-full-frame-input-manifest-attempt04/current-full-frame-input-manifest.json` | `9e682e28c3d4c3c0594863f82c6b74d19dee2700f3856d34e1a26f69082e4f11` |
| Current manifest04 producer | `docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-full-frame-input-manifest-attempt04/produce.py` | `966e4b5918fefe06741ca828a3b4c3f6d353b735a1fc70df6a98a91b4e98b1f4` |
| Member-solids descriptor | `docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-full-frame-member-solids-attempt01/bundle/current-full-frame-member-solids.json` | `8979d678f7b45d3b75fa465e810b0910d72874c5c1c705290d1fcb2bf2b78420` |
| Member-solids producer | `docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-full-frame-member-solids-attempt01/produce.py` | `922e3e294ba9bfc4e3b27476035bc78194c6151f22b282e182015a3d4b58d1d9` |
| This producer | `docs/wood-joints-mvp/hypotheses/current-finished-feature-register-2026-10-01/surfaces.py` | `a58e8f76b0d308352c734b6eab6bdea8c3adb75ab1c538e0905997d0232bab4f` |
| Focused tests | `docs/wood-joints-mvp/hypotheses/current-finished-feature-register-2026-10-01/test_surfaces.py` | `2e7dce60cb030caf330b2ff82db6ad6a84fee53827745a90c58ee8b967c62b1a` |
| Source-pin output | `docs/wood-joints-mvp/hypotheses/current-finished-feature-register-2026-10-01/source-pins.json` | `0e8cb56407f14e93d7ab95741115d4355a954eb845ae503365ba1da1149bd9cd` |
| Feature-register result | `docs/wood-joints-mvp/hypotheses/current-finished-feature-register-2026-10-01/surfaces.json` | `33fff67eee4bc4e96ccef5703f6eebd0d4e004541c6114a4b1da4a5332b2f6eb` |

The upstream stock source-pin file hashes its producer, current manifest04, member-solids descriptor, source inventories, and all source STEP files; this register verifies every entry in that upstream pin document before extraction. Its own source-pin output independently binds the exact 44 STEP files and the producer and tests listed above.

## Exact finished STEP bindings

All paths use this exact prefix from manifest04: `docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-full-frame-member-solids-attempt01/bundle/members/`.

| STEP file | SHA-256 | Bytes | Faces |
| --- | --- | ---: | ---: |
| `base_floor_left.step` | `e36c73da89d5b209231122b44d433a67c444657ec23a49725916a3339733071d` | 36863 | 10 |
| `base_floor_right.step` | `64d0e1aa25f2c223bbc2d19814643bf7e980a4238fe8a1c20a40272b21b58247` | 31821 | 10 |
| `base_header.step` | `41ba159020ed41463ff1c886716cdbf69123e23481be704391a247eee1382082` | 113745 | 38 |
| `base_post_center_left.step` | `02ae8ecc26d2f7637b3b915dd2b1b5eceff9140770475692cce083084670b607` | 34383 | 12 |
| `base_post_center_right.step` | `e7f348058ce6927714ff9bd01130fae1a01adbfa708b00753c99ffe64fb343bd` | 32009 | 12 |
| `base_post_outer_left.step` | `cdf9bb35e7ff2fda58bfdd604f69dedcba88b6b34149f874c03335abe90a1dce` | 42705 | 14 |
| `base_post_outer_right.step` | `d4335f36aaaa271856b4fb42bdadea4cef49c0fea6481afde317d67f9cbd23de` | 42449 | 14 |
| `base_principal_center_left.step` | `ff537b4187c9a9e928eac6e89f44d2f3466c56280c58891e460dbb185bc8c253` | 108562 | 34 |
| `base_principal_center_right.step` | `9053a7210a781e919038a4a823f867325dd5c78907bd028d8b9e76dc0b46df58` | 116008 | 34 |
| `base_rail_bottom_left.step` | `724d46fa7902a949b79b0fd6132c5e57c580be80aad7d059c29e04494ff79923` | 68636 | 19 |
| `base_rail_bottom_right.step` | `9542614527922ed3cf2e7b13b239244e82820e38577f1c88959219906a6f2a7b` | 68492 | 19 |
| `base_rail_service_lower_left.step` | `ae82b9906b29852685bd90d86e6b3add4f6a4e2603b34138cc28b186558e6fda` | 64735 | 19 |
| `base_rail_service_lower_right.step` | `14c6bc16d7c08cd0782ac7766fa8dbea2555ad9c0de59ca580823444d86cb809` | 64670 | 19 |
| `base_rail_service_upper_left.step` | `4b6a3eede080310530a7633e2761a798f5f65a9dece5eb3793cd4aec009b9687` | 64582 | 19 |
| `base_rail_service_upper_right.step` | `87c620c3684cfa1044c7ebe7fb8e654b6b79a91beb5b2f1b1709c2279a49a2b5` | 64529 | 19 |
| `base_rail_top.step` | `79b4f7f66f35928ed383d0e396ce221d9a4302136b088a7bcd41749c52a10a60` | 72285 | 22 |
| `base_side_left.step` | `237c3fa6aa0b52c39124580810d048e38919b99b9a1fb5db5a2423e7eda62fdf` | 124550 | 35 |
| `base_side_right.step` | `ddb6ac20f1f50a9036448eb5680fdc486532ff3826ce52d566baf685a800a59f` | 113489 | 35 |
| `bottom_center_left_cleat.step` | `90f6b6cb0b7dc032108244de4a24cbfd4ea1642849a4aef66672a5ac818c4003` | 37340 | 10 |
| `bottom_center_right_cleat.step` | `6f2f7abd66b36311fcbfe3c977de1f04b3bc183557831c949843da669cecc1d7` | 34887 | 10 |
| `bottom_outer_left_cleat.step` | `28d1b5fee748c38e30e3d2618c8377cfe374c7ccd0b520736c25841720824438` | 35280 | 10 |
| `bottom_outer_right_cleat.step` | `91878e6857d848bda7c266e69d7f97cef152686d6cc6096ebfd8a6c5008d8501` | 37774 | 10 |
| `center_post_cleat_left.step` | `7901f21ed12dbd6fca26b2c8bf67670cc63304549be2d2e81083ac098a8af21b` | 32730 | 10 |
| `center_post_cleat_right.step` | `6ba16357d43dd35aeb4552d4e3a4e4ad594e5286ecedc902182a1f7ac4eb70e3` | 30370 | 10 |
| `center_principal_cleat_left.step` | `dd4bacfe1df31b87e6e24d87d3ab80f22a604bba90531659e97d6a3b5d8f0652` | 33262 | 10 |
| `center_principal_cleat_right.step` | `eef681f8f99c1af026c439692b813a51b0412892d4137ee7dd9748388ed3f0a2` | 30648 | 10 |
| `knee_outer_left_inner_frame_block.step` | `9c7957e22686dff467f533f013172743c9bc8e7a9783331490b8e7c93d92e568` | 33529 | 10 |
| `knee_outer_left_spine.step` | `081a3930dd1334e317fc0116a24d80b4b70e9cb3f36b928cda403f66194bb5c0` | 31339 | 10 |
| `knee_outer_right_inner_frame_block.step` | `4f2d6e8656aab94e1b0fc773325a944041682dfbf4c203ce1f2dd017845046e0` | 35844 | 10 |
| `knee_outer_right_spine.step` | `f70ade3760f1615cc31f687bc4cf4c334d27db3b8b41e35e615e15b92c4e1faa` | 35896 | 10 |
| `left_service_inner_lower_cleat.step` | `632cda5ba7f06bdf1fa4fb0658992259b27237b412dcc74f5ce999529581ce74` | 32887 | 10 |
| `left_service_inner_upper_cleat.step` | `584106340fb39652d97e2c45cc54feca9a61ed3faeb0eeaedaf08a6e0a32747e` | 35113 | 10 |
| `left_service_outer_lower_cleat.step` | `7a2c73ba176e1579e6920598a5b266b22d9bd7e1771b1e72b2de481f29b7c309` | 35814 | 10 |
| `left_service_outer_upper_cleat.step` | `5594cd1293bb181d61deb3aaa549c4e44845db5e365f3e621dbd10579b48938a` | 33099 | 10 |
| `lumber_leg_left.step` | `1416e3aec21eea2993542f8266649ebe0aec50b3ec6444f445f18f88cbffa065` | 46074 | 12 |
| `lumber_leg_right.step` | `e346646efb8bdf9c03d45dfa024900622abcd65fe0d58bf11c6dcd3735bedff4` | 41836 | 12 |
| `top_center_left_cleat.step` | `9fa44336e7f77b443fd735b337d7089b763a5a4b592f915f5a0f022bebba7d86` | 35311 | 10 |
| `top_center_right_cleat.step` | `95408c99e9fda6a274f71f764b95c3298c7077f1d0cf6e91fd45a7efcbb2493d` | 32723 | 10 |
| `top_outer_left_cleat.step` | `c4ecd881a9dc2e78195d028bf360cc42da86e97129ac44db7fafd7c77f50ba88` | 33061 | 10 |
| `top_outer_right_cleat.step` | `70b94b711f629b6b1d955083c7eafddb07b104c04878c46ae032ba4c953be25c` | 35609 | 10 |
| `wj04_lower_full_stock_cleat.step` | `231262125246a456aab725c97175e6035e3112bd7a06e0753f232ca1a80b29b3` | 32863 | 10 |
| `wj04_upper_g7_crosscut_full_stock_cleat.step` | `76d96d84027339baa0daf9cc84f1d0e976b0cd9f4955dde0f0504a1424c0dc04` | 34982 | 10 |
| `wj06_outer_lower_right_cleat.step` | `b12617c11fb72f33d3bc1cade8fa2a1281294c678d7a4d994eda9ab629805459` | 35910 | 10 |
| `wj06_outer_upper_right_cleat.step` | `974eb688e5c59af38bb655c543a6fcf35e8a772c7ce5af568ed99eac7eb5ddca` | 33077 | 10 |

## Limits

This is a geometric inventory of saved analytical STEP faces. The proposed stock frames do not establish actual lumber orientation or delivered datums. The register does not infer or authorize machining, drilling, fabrication, fastener selection, purchasing, or use; it supplies no wood resistance, joint capacity, or solver result. Unsupported surface types are retained with descriptive bounds, vertices, area, centroid, and trim trace and remain explicitly classified `unsupported_descriptive_only`.
