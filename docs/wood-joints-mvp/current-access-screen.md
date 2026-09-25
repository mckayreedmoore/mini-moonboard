# Current WJ24 bolt access screen

On September 24, 2026, the current `led-clearance-2x6-runner-seated-blocks-v1` geometry was screened for axial bolt movement and limited wrench-envelope poses. The run covered the eight exterior 2×6 block stacks and eight stacks through the trimmed tall center blocks: 16 of 92 candidate axes. It consumed the live current-revision geometry; it did not reuse the archived 104-axis WJ24 access result.

The complete machine-readable result is [access-screen-attempt01.json](hypotheses/evaluation-resume-2026-09-24/access-screen-attempt01.json). It records all per-axis reports and the conditional order graph.

## Axial movement

All 16 shafts used the exact coaxial-cylinder translation sweep. The swept shaft BRep had zero measured intersections with the current retained-scene BReps on every axis. The separate head, head-washer, nut, and nut-washer movement envelopes also reported zero intersections. Head and washer translations and nut-side slides use conservative bounding envelopes.

The travel values below run from the current shaft envelope to the outermost receiver face on the head side. Each listed axis had zero shaft-sweep hits.

| Current axes | Count | Derived travel per axis | Shaft sweep | Shaft hits |
| --- | ---: | ---: | --- | ---: |
| `center_principal_header_{left,right}_{1,2}` | 4 | 188.366 mm | Exact coaxial cylinder | 0 |
| `center_principal_{left,right}_{1,2}` | 4 | 137.566 mm | Exact coaxial cylinder | 0 |
| `knee_outer_{left,right}_post_{1,2}` | 4 | 99.949 mm | Exact coaxial cylinder | 0 |
| `knee_outer_{left,right}_side_{1,2}` | 4 | 239.649 mm | Exact coaxial cylinder | 0 |

Receiver projections used every ordered receiver in each live bore, including three-member sandwich stacks. The zero-hit result applies to the modeled geometry and a zero terminal-clearance allowance. It does not establish delivered-part fit, dimensional tolerance, bolt capture, support transfer, or a physical withdrawal path.

## Wrench envelopes

The probe used the WJ04 FACOM `facom_34_7_16` profile as an unselected external proxy: 22 mm head width, 3 mm head thickness, and 100 mm overall length. For each head and nut side it screened two synthetic headings, an axial approach proxy, discrete poses at 0° and ±15°/±30°, and separate conservative AABB enclosures for ±30° rotation.

| Side | Motion sample | Reports with proxy overlaps | Largest proxy overlap |
| --- | --- | ---: | --- |
| Head | One-head-width axial approach | 17 / 32 | 40,183.961 mm³: `center_principal_header_left_2`, against `wood/base_principal_center_left` |
| Head | Discrete turn poses | 58 / 160 | 3,181.295 mm³: `center_principal_header_left_2`, +30° pose against `wood/base_principal_center_left` |
| Head | ±30° angular AABB | 49 / 64 | 12,819.924 mm³: `center_principal_header_left_2`, loosening enclosure against `wood/base_principal_center_left` |
| Nut | One-head-width axial approach | 22 / 32 | 40,183.961 mm³: `center_principal_header_right_1`, against `wood/base_post_center_right` |
| Nut | Discrete turn poses | 76 / 160 | 3,274.280 mm³: `center_principal_header_right_1`, +30° pose against `wood/base_post_center_right` |
| Nut | ±30° angular AABB | 56 / 64 | 12,819.924 mm³: `center_principal_header_right_1`, tightening enclosure against `wood/base_post_center_right` |

These are intersections of synthetic wrench-proxy solids with the current scene solids. The approach proxy translates the model along the fastener axis; the tool profile uses circular head envelopes and a full-width handle; the angular result encloses an axis-aligned bounding box during rotation. The reported volumes are geometric overlaps for those proxies, not evidence that a real wrench is blocked. The profile is not a selected or delivered tool, and jaw fit, actual approach, hand clearance, torque, and a full tightening or loosening stroke remain unmodeled.

## Conditional order graph

The axial-motion dependency graph produced zero assembly precedence edges, zero removal precedence edges, and no cycles among the 16 screened axes. This graph only derives conditional ordering from the screened bolt, nut, and washer movement envelopes. It does not derive an order from the wrench-proxy hits and does not cover the other 76 candidate axes or every build state, so it is not a complete assembly sequence.

Within each stack, the modeled removal preconditions remain: counterhold and fully unthread the nut; capture and slide off the nut; capture and slide off the nut washer; then withdraw the head, head washer, and shaft. Assembly reverses that order. Thread travel, part capture, support changes, and actual tightening are not modeled.

## Scope and provenance

The live obstacle map contained 1,231 shape entries. For this run it included the composed finished source wood, all 16 current finished hosts, all 24 current candidate parts, current panel replacements, 66 fixed panel axes, 72 retained frame-bolt shapes, non-duplicate protected families, and all 460 installed candidate-hardware role shapes across the 92 axes. Unchanged source members, including legs and runners, remained in the composed source-wood map.

The raw report identifies revision and trial `led-clearance-2x6-runner-seated-blocks-v1`, and source inventory SHA-256 `07af4c3eb642cf3887595fe4415eb65404cdcf74d66c5c7bb182847ef21c2d78`. Report SHA-256: `83f53ada10afda7566af7a872c246718e88ad145b9ee2dd12ab6f9a878095c81`. Collector: [wood_joint_current_access_screen.py](../../scripts/wood_joint_current_access_screen.py) (SHA-256 `d1806f8ca0c69fd87b15c2edea4d948d541829be9a0b57ded1695fcf0dc96a24`).

This is a bounded geometry diagnostic. It does not validate actual tools or workspace, select delivered hardware, prove assembly or disassembly, establish structural behavior, authorize physical work, or release climbing use.
