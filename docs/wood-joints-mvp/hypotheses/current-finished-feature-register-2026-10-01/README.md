# Current finished-feature register

This packet prepares source-bound geometry for the reviewed `led-clearance-2x6-runner-seated-blocks-v1` wood-joint candidate. It describes the 44 saved finished timber STEP solids in the [proposed stock frames](../current-stock-envelope-reconciliation-2026-10-01/README.md) and joins their cylindrical patches to the attempt04 fastener axes. It reads existing geometry without regenerating it or running native mechanics.

The [surface register](surfaces.md) covers every trimmed face: **648 patches**, comprising **338 planes** and **310 cylinders**, across 20 frame members and 24 blocks. The [axis correspondence](axis-features.md) keeps the three policies distinct: **92 candidate bolts, 12 starting frame bolts and 66 Hillman panel/kicker screws**. All **278 receiver memberships** match one finite, contained bore-like patch each. No patch is reused by two memberships in this frozen join. The eight moved screw axes remain separately traceable; the 58 unchanged axes remain identified.

Axis correspondence covers 278 of the 310 cylindrical patches. The remaining **32 patches** stay unassigned in this packet, with IDs below. Their presence is neither an instruction to drill additional holes nor evidence that those surfaces can be omitted from section checks. Cylinder patches are trimmed CAD faces, not a count of physical holes. A separate parent comparison associates these patches with the preserved source LED/service passages under the datum alignment below. The source records remain unqualified for machining.

## Coverage by member

“Assigned” means a cylindrical patch matched to one current source receiver membership. The six plywood bodies are outside this timber-only surface register; their screw axes are included only at the timber receivers.

| Member | Planes | Cylinders | Assigned | Unassigned |
| --- | ---: | ---: | ---: | ---: |
| `base_floor_left` | 6 | 4 | 4 | 0 |
| `base_floor_right` | 6 | 4 | 4 | 0 |
| `base_header` | 16 | 22 | 22 | 0 |
| `base_post_center_left` | 8 | 4 | 4 | 0 |
| `base_post_center_right` | 8 | 4 | 4 | 0 |
| `base_post_outer_left` | 8 | 6 | 6 | 0 |
| `base_post_outer_right` | 8 | 6 | 6 | 0 |
| `base_principal_center_left` | 15 | 19 | 18 | 1 |
| `base_principal_center_right` | 15 | 19 | 18 | 1 |
| `base_rail_bottom_left` | 8 | 11 | 6 | 5 |
| `base_rail_bottom_right` | 8 | 11 | 6 | 5 |
| `base_rail_service_lower_left` | 8 | 11 | 6 | 5 |
| `base_rail_service_lower_right` | 8 | 11 | 6 | 5 |
| `base_rail_service_upper_left` | 8 | 11 | 6 | 5 |
| `base_rail_service_upper_right` | 8 | 11 | 6 | 5 |
| `base_rail_top` | 10 | 12 | 12 | 0 |
| `base_side_left` | 15 | 20 | 20 | 0 |
| `base_side_right` | 15 | 20 | 20 | 0 |
| `bottom_center_left_cleat` | 6 | 4 | 4 | 0 |
| `bottom_center_right_cleat` | 6 | 4 | 4 | 0 |
| `bottom_outer_left_cleat` | 6 | 4 | 4 | 0 |
| `bottom_outer_right_cleat` | 6 | 4 | 4 | 0 |
| `center_post_cleat_left` | 6 | 4 | 4 | 0 |
| `center_post_cleat_right` | 6 | 4 | 4 | 0 |
| `center_principal_cleat_left` | 6 | 4 | 4 | 0 |
| `center_principal_cleat_right` | 6 | 4 | 4 | 0 |
| `knee_outer_left_inner_frame_block` | 6 | 4 | 4 | 0 |
| `knee_outer_left_spine` | 6 | 4 | 4 | 0 |
| `knee_outer_right_inner_frame_block` | 6 | 4 | 4 | 0 |
| `knee_outer_right_spine` | 6 | 4 | 4 | 0 |
| `left_service_inner_lower_cleat` | 6 | 4 | 4 | 0 |
| `left_service_inner_upper_cleat` | 6 | 4 | 4 | 0 |
| `left_service_outer_lower_cleat` | 6 | 4 | 4 | 0 |
| `left_service_outer_upper_cleat` | 6 | 4 | 4 | 0 |
| `lumber_leg_left` | 8 | 4 | 4 | 0 |
| `lumber_leg_right` | 8 | 4 | 4 | 0 |
| `top_center_left_cleat` | 6 | 4 | 4 | 0 |
| `top_center_right_cleat` | 6 | 4 | 4 | 0 |
| `top_outer_left_cleat` | 6 | 4 | 4 | 0 |
| `top_outer_right_cleat` | 6 | 4 | 4 | 0 |
| `wj04_lower_full_stock_cleat` | 6 | 4 | 4 | 0 |
| `wj04_upper_g7_crosscut_full_stock_cleat` | 6 | 4 | 4 | 0 |
| `wj06_outer_lower_right_cleat` | 6 | 4 | 4 | 0 |
| `wj06_outer_upper_right_cleat` | 6 | 4 | 4 | 0 |
| **Total** | **338** | **310** | **278** | **32** |

## Unassigned cylindrical patches

The member prefix completes each face ID, for example `base_principal_center_left/facet011`. These identifiers depend on the pinned importer and exact STEP bytes.

| Member | Patch IDs |
| --- | --- |
| `base_principal_center_left` | `facet011` |
| `base_principal_center_right` | `facet013` |
| `base_rail_bottom_left` | `facet010`, `facet011`, `facet012`, `facet014`, `facet015` |
| `base_rail_bottom_right` | `facet004`, `facet005`, `facet006`, `facet008`, `facet009` |
| `base_rail_service_lower_left` | `facet010`, `facet011`, `facet012`, `facet013`, `facet015` |
| `base_rail_service_lower_right` | `facet004`, `facet005`, `facet006`, `facet007`, `facet009` |
| `base_rail_service_upper_left` | `facet010`, `facet011`, `facet012`, `facet013`, `facet015` |
| `base_rail_service_upper_right` | `facet004`, `facet005`, `facet006`, `facet007`, `facet008` |

## Source LED/service passage correspondence

A separate read-only source comparison, outside the fastener-join producer, matched all 32 unassigned cylindrical patches one-to-one to the 32 `bore_*` records in `docs/floor-flush-construction/timber-passages.json`. Each source record is a 38.1 mm diameter passage with a 40.1 mm modeled cutter and 1 mm overrun at each end; the matched face intervals correspond to source stations `[1, 39.1] mm`. These patches geometrically correspond to named LED/service passages and remain outside the connection-axis memberships.

The comparison uses each source-inventory member's `local_to_global_transform` and `actual_shape_extents_local_mm` to transform its eight X/T/N bounding-box corners into global XYZ. It projects those corners into the current proposed stock g/q/r basis and reconstructs their minimum corner. The alignment translates the source passage start by `current proposed stock origin - projected source bounding-box minimum corner`; it leaves direction unchanged. Twenty-two records need only numerical roundoff translation (less than 2e-9 mm); ten passages on `base_rail_bottom_left` and `base_rail_bottom_right` use `[0, 49.430367184, 58.908817675] mm`. This is an explicit geometric alignment, not a recovered delivered-stock datum or proof of a historical machining operation.

For each source row, the parent required exactly one unassigned face on its member with line distance, radius error and both finite endpoint errors below `1e-5 mm`, and absolute axis-dot departure from one below `1e-6`. The resulting 32 distinct face IDs equal the entire unassigned set. Source directions and current member orientation are compatible for this comparison; no rotation correction was inferred. The pairing below supplies a compact trace. The full source name is `bore_<member>_<suffix>`.

| Member | Source suffix → current facet |
| --- | --- |
| `base_principal_center_left` | `060→011` |
| `base_principal_center_right` | `072→013` |
| `base_rail_bottom_left` | `001→015`, `023→014`, `025→012`, `047→011`, `049→010` |
| `base_rail_bottom_right` | `073→009`, `095→008`, `097→006`, `119→005`, `121→004` |
| `base_rail_service_lower_left` | `006→015`, `018→013`, `030→012`, `042→011`, `054→010` |
| `base_rail_service_lower_right` | `078→009`, `090→007`, `102→006`, `114→005`, `126→004` |
| `base_rail_service_upper_left` | `007→015`, `017→013`, `031→012`, `041→011`, `055→010` |
| `base_rail_service_upper_right` | `079→008`, `089→007`, `103→006`, `113→005`, `127→004` |

The passage records all say `qualified_for_machining: false`. Preserve their effect in the exact finished geometry and applicable section checks; this correspondence authorizes no drilling, passage enlargement, removal or transfer of historical acceptance. It does not make these faces additional bolts or screws.

| Additional comparison input | SHA-256 |
| --- | --- |
| `docs/floor-flush-construction/timber-passages.json` | `5c86941458a6a92432941fdf7e13b2b21ef2f933332e0e1ec602d4d57796f15f` |
| `docs/floor-flush-construction/manifest.json` | `5411ac7fb69479fbd2eac163c637553dcac8d57e46425fd7fe8ee92717a867ec` |
| `docs/wood-joints-mvp/source-inventory.json` | `07af4c3eb642cf3887595fe4415eb65404cdcf74d66c5c7bb182847ef21c2d78` |

The construction manifest pins the exact passage artifact. Current surface and axis result hashes are published in their respective notes.

## Use and limits

Use `surfaces.json` for global and proposed-stock g/q/r coordinates, face bounds, plane equations, cylinder axes/radii/finite intervals, trim traces and exact STEP bindings. Use `axis-features.json` for per-axis source datums, finite modeled extents, receiver joins and nonmatch diagnostics. The [surface note](surfaces.md) and [axis note](axis-features.md) publish full artifact hashes and replay commands; raw JSON remains ignored and local.

Exact geometry replays require the local frozen evidence set, including ignored envelope/manifest/member-solids JSON and STEP inputs. A clean checkout can run the focused synthetic tests but cannot replay the saved geometry results without those inputs. The separate passage comparison is documented by its method, source hashes and pairing table; it is not a producer CLI output.

The proposed stock origin is the minimum g/q/r corner of the analytical blank, not an observed lumber datum. Plane descriptions do not identify approved seats, tapers or machining operations. Modeled axis lengths and cylinder diameters do not supply drill bits, pilots, purchased bolt lengths, usable shank or installation instructions. The Hillman metadata envelope uses the reconciled 63.5 mm shop length, retaining historical 50.8 mm occupancy as provenance only. Revised-station surface correspondence and compositor cutter provenance remain separate.

This packet supplies geometric evidence for later finished-section reconciliation and drawing preparation. It does not close resistance, assembly access, a cut or drilling recipe, material specifications, physical receiving observations or any complete joint. All existing engineering and owner-directed model boundaries remain in force.

## Validation

The parent ran the 18 focused synthetic tests and both read-only exact replays. Independent review and its final disposition are recorded in [review.md](review.md).
