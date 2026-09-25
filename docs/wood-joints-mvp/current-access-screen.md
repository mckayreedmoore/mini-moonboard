# Current WJ24 bolt access screens

On September 24, 2026, the live current `led-clearance-2x6-runner-seated-blocks-v1` scene was screened for withdrawal/insertion motions of all 92 candidate axes, limited wrench-envelope poses, and a bounded captured-nut motion hypothesis for four axes. Exact-component attempt03 is the current general component result. The captured-nut attempt02 below adds a local staged CAD path for those four nut-hit axes; it does not establish an installed operation.

## Exact-component screen: attempt03, all 92 candidate axes

The [machine-readable result](hypotheses/evaluation-resume-2026-09-24/access-screen-attempt03-exact-components.json)
records all 92 candidate axes against 1,231 live-scene obstacle entries. It
reports zero unmodeled candidate axes, does not load the archived 104-axis
result, and retains the current scene/source pins. Runtime was 122.16 seconds;
the run records `source_unchanged_after_run: true`. Report SHA-256:
`bd2b97c0677b2e0ab5b09898ba7f2227758088744cd93f7e3c9b266bce5c5215`.
The [parent comparison audit](hypotheses/evaluation-resume-2026-09-24/exact-access-parent-audit.json)
checks the frozen source/report relationship and row deltas; it does not
independently recompute the BRep sweeps.

### Exact component movements

The 92 shafts use exact coaxial-cylinder translation sweeps. Each axis also
has a continuous translation sweep for the four current source-CAD stack
components: 184 cylinder sweeps for heads/nuts and 184 annular-cylinder sweeps
for head/nut washers. “Exact” describes the supplied CAD BReps, not selected
or delivered hardware.

| Moving component | Exact movement method | Axes with modeled-geometry intersection | Current finding |
| --- | --- | ---: | --- |
| Shaft | Coaxial-cylinder sweep | 0 / 92 | Clear under the reported headward-withdrawal exclusions below. |
| Head | Exact source-BRep cylinder sweep | 0 / 92 | Clear under the reported headward-withdrawal exclusions below. |
| Head washer | Exact source-BRep annular-cylinder sweep | 0 / 92 | Clear under the reported headward-withdrawal exclusions below. |
| Nut | Exact source-BRep cylinder sweep | 4 / 92 | Four axial-slide intersections listed below. |
| Nut washer | Exact source-BRep annular-cylinder sweep | 2 / 92 | Two small intersections at the bottom-center pair. |


| Axis | Exact BRep intersection during axial slide |
| --- | --- |
| `bottom_center/clip_horizontal_bottom_left_2/rail_2` | Nut with `wood/center_principal_cleat_left`: 146.412520 mm³; nut washer with the same wood: 0.235256 mm³. |
| `bottom_center/clip_horizontal_bottom_right_1/rail_2` | Nut with `wood/center_principal_cleat_right`: 146.412520 mm³; nut washer with the same wood: 0.235256 mm³. |
| `bottom_outer/clip_horizontal_bottom_left_1/rail_2` | Nut with `wood/knee_outer_left_inner_frame_block`: 87.090910 mm³. |
| `bottom_outer/clip_horizontal_bottom_right_2/rail_2` | Nut with `wood/knee_outer_right_inner_frame_block`: 87.090910 mm³. |

The slide reports use zero terminal allowance. On all four listed axes, the
head-side bolt withdrawal travel is 150.368 mm along the recorded headward
vector `[0, 0.64278761, 0.766044443]`; the axial nut slide is 21.336 mm and the
nut-washer slide is 23.368 mm. Those nut travel distances are derived from the
current shaft-tip and moving-part extrema; thread motion is omitted. The exact
nut slide excludes the active nut and shaft as target roles; the washer slide
excludes the active nut, washer and shaft. Other scene geometry, including the
listed wood, remains an obstacle.

Attempt03's otherwise clear headward withdrawal moves the head, head washer
and shaft together, but excludes all five roles of that stack, including the
nut and nut washer, under the precondition that both were captured and removed.
By itself it does not test a retained-nut route. The captured-nut attempt02
below checks the moving components against the retained nut/washer pair
separately, subject to its boreless-nut/thread compatibility limitation.

### Captured-nut motion probe: attempt02

The [attempt02 report](hypotheses/evaluation-resume-2026-09-24/captured-nut-motion-attempt02/motion.json)
tests an alternate local removal motion on the four nut-hit axes above. It
holds the nut/washer pair at the current receiver, tests headward bolt
withdrawal, then moves the pair laterally beyond the blocker’s global-X bounds
by 1 mm and follows with a declared 25 mm nutward move. The [attempt README](hypotheses/evaluation-resume-2026-09-24/captured-nut-motion-attempt02/README.md)
summarizes the method and comparison with failed attempt01.

| Axis | Lateral nut/washer move `(ΔX, ΔY, ΔZ)` mm | 25 mm nutward follow-on `(ΔX, ΔY, ΔZ)` mm | Two-stage local CAD result |
| --- | ---: | ---: | --- |
| `bottom_center/clip_horizontal_bottom_left_2/rail_2` | (−50.9623, 0, 0) | (0, −16.0697, −19.1511) | Clear in CAD probe |
| `bottom_center/clip_horizontal_bottom_right_1/rail_2` | (+48.9623, 0, 0) | (0, −16.0697, −19.1511) | Clear in CAD probe |
| `bottom_outer/clip_horizontal_bottom_left_1/rail_2` | (+53.9623, 0, 0) | (0, −16.0697, −19.1511) | Clear in CAD probe |
| `bottom_outer/clip_horizontal_bottom_right_2/rail_2` | (−55.9623, 0, 0) | (0, −16.0697, −19.1511) | Clear in CAD probe |

For all four, the reported headward bolt travel is 151.368 mm including a
1 mm terminal allowance, with no external scene-object intersections. The
head/head-washer versus retained nut/nut-washer pairs and shaft versus
nut-washer pair report zero additional pair intersections. The shaft and
boreless nut display envelope overlap by 181.793976 mm³ both initially and
during the sweep; this is treated as unchanged coaxial occupancy under an
assumed thread-compatible unthreading step, not as demonstrated physical
passage or fit. Actual unthreading, threads, tool access, capture and support
transfer were not simulated.

The transverse nut and annular-washer sweeps each have one direction per axis
with no external obstacle hits; the opposite-X alternatives hit the original
`base_principal_center_*` or `base_side_*` wood. The 25 mm follow-on is only a
bounded local path after moving beyond the blocker envelope. It is not full
scene extraction or a reachable staging location. The CAD test does not prove
real-tool access, loose-part capture, thread compatibility, or assembly; a
physical route remains unresolved. Test assembly separately by reversing the
motion with selected hardware and tools.

### Conditional order graph and scope

Attempt03 reports no precedence edges or cycles, and no out-of-subset
dependencies. The graph remains incomplete across all build states and does
not model the captured-nut sequence. The 12 retained frame-bolt arrangements
remain obstacles rather than target operations. Wrench results in the
all-92 access-screen attempt02 are unchanged in exact-component attempt03 and
remain synthetic proxy evidence only; see the historical comparison section
below.

## Attempt02: all-92 conservative-envelope screen (prior comparison)

The [attempt02 result](hypotheses/evaluation-resume-2026-09-24/access-screen-attempt02-all92.json)
used the same current scene, 1,231 obstacles and all 92 candidate axes, but
used conservative translation envelopes for head, washer and nut components.
Its component-motion counts below are superseded by attempt03's exact-source
BRep sweeps. Its wrench pose rows are unchanged in attempt03. Attempt02 runtime
was 116.76 seconds; the 16 priority-axis rows match attempt01 exactly, and
`source_unchanged_after_run` was true. Report SHA-256:
`104b2caa98decfcd78d92a1c4686b99583321d8ee2fafb2f47d9df0a4bea28c5`.

### Conservative component movement (superseded)

All 92 modeled shafts had zero intersections during the exact coaxial-cylinder
translation sweep. Head and head-washer translations and nut-side slides used
conservative bounding envelopes in this attempt:

| Moving envelope | Axes with one or more overlaps | Moving-envelope / obstacle pairs | Largest reported overlap |
| --- | ---: | ---: | --- |
| Exact shaft-cylinder sweep | 0 / 92 | 0 | None |
| Head translation enclosure | 32 / 92 | 32 | 739.656 mm³, `bottom_outer/clip_horizontal_bottom_left_1/rail_1` vs `wood/bottom_outer_left_cleat` |
| Head-washer translation enclosure | 32 / 92 | 32 | 3,333.316 mm³, same axis and obstacle |
| Nut axial-slide enclosure | 32 / 92 | 68 | 1,258.780 mm³, `bottom_center/clip_horizontal_bottom_left_2/rail_2` vs `wood/center_principal_cleat_left` |
| Nut-washer axial-slide enclosure | 32 / 92 | 36 | 3,333.316 mm³, `bottom_outer/clip_horizontal_bottom_left_1/rail_2` vs `wood/base_rail_bottom_left` |

### Synthetic wrench-envelope overlaps

The same unselected WJ04 FACOM profile is used: 22 mm head width, 3 mm head
thickness and 100 mm overall length. The two synthetic heading rows per axis
produce these counts. “Pose reports” counts individual tested proxies with an
overlap; it is not a count of failed joints or obstructed real tools.

| Side | Proxy test | Overlapping pose reports | Axes with at least one overlapping report |
| --- | --- | ---: | ---: |
| Head | One-head-width axial approach | 129 / 184 | 70 / 92 |
| Head | Discrete synthetic turn poses | 427 / 920 | 70 / 92 |
| Head | ±30° angular AABB enclosures | 322 / 368 | 92 / 92 |
| Nut | One-head-width axial approach | 147 / 184 | 82 / 92 |
| Nut | Discrete synthetic turn poses | 480 / 920 | 81 / 92 |
| Nut | ±30° angular AABB enclosures | 336 / 368 | 92 / 92 |

These are intersections of synthetic conservative proxies with modeled obstacles. The
angular method uses an axis-aligned bound during rotation, the approach does
not model open-jaw fit or hand clearance, and the discrete angles are samples.
All 92 head sides and all 92 nut sides have at least one sampled proxy
overlap, but the report explicitly does not establish actual-tool blockage or
tool access. Select and screen the intended tools, counterhold, full stroke,
re-indexing, hand/workspace clearance and tolerances before drawing either
conclusion.

### Conditional order graph and exclusions (superseded)

Attempt02 contains 32 assembly precedence edges and 32 removal precedence
edges, with zero cycles in each reported graph. The constraints are conditional
on a conservative envelope overlap representing an actual blockage. Seven
out-of-subset dependency group IDs remain (`bottom_center`, `bottom_outer`,
`left_service`, `top_center`, `top_outer`, `wj04_g7` and `wj06_outer_pair`);
the report marks the graph incomplete for all build states. It does not model
thread travel, counterholding, actual turning, tool-driven precedence, part
capture or support transfer. The no-cycle result is not an assembly or
disassembly sequence proof.

The 12 retained frame-bolt arrangements are included in the live obstacle
scene but are not target axes in this operation map; neither their tool access
nor their withdrawal is screened here. The unchanged legs and runners remain
in the composed source-wood obstacle map. No historical WJ24 pass is loaded.

## Priority 16-axis attempt01 — preserved initial run

The initial run covered the eight exterior 2×6 block stacks and eight stacks
through the trimmed tall center blocks: 16 of 92 candidate axes. It consumed
live current-revision geometry rather than the archived 104-axis WJ24 result.
The complete [attempt01 report](hypotheses/evaluation-resume-2026-09-24/access-screen-attempt01.json)
records its per-axis rows and conditional graph. Attempt02 confirms that the
16 per-axis rows are unchanged.

### Axial movement

All 16 shafts used the exact coaxial-cylinder translation sweep. The swept shaft BRep had zero measured intersections with the current retained-scene BReps on every axis. The separate head, head-washer, nut, and nut-washer movement envelopes also reported zero intersections. Head and washer translations and nut-side slides use conservative bounding envelopes.

The travel values below run from the current shaft envelope to the outermost receiver face on the head side. Each listed axis had zero shaft-sweep hits.

| Current axes | Count | Derived travel per axis | Shaft sweep | Shaft hits |
| --- | ---: | ---: | --- | ---: |
| `center_principal_header_{left,right}_{1,2}` | 4 | 188.366 mm | Exact coaxial cylinder | 0 |
| `center_principal_{left,right}_{1,2}` | 4 | 137.566 mm | Exact coaxial cylinder | 0 |
| `knee_outer_{left,right}_post_{1,2}` | 4 | 99.949 mm | Exact coaxial cylinder | 0 |
| `knee_outer_{left,right}_side_{1,2}` | 4 | 239.649 mm | Exact coaxial cylinder | 0 |

Receiver projections used every ordered receiver in each live bore, including three-member sandwich stacks. The zero-hit result applies to the modeled geometry and a zero terminal-clearance allowance. It does not establish delivered-part fit, dimensional tolerance, bolt capture, support transfer, or a physical withdrawal path.

### Wrench envelopes

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

### Conditional order graph

The axial-motion dependency graph produced zero assembly precedence edges, zero removal precedence edges, and no cycles among the 16 screened axes. This graph only derives conditional ordering from the screened bolt, nut, and washer movement envelopes. It does not derive an order from the wrench-proxy hits and does not cover the other 76 candidate axes or every build state, so it is not a complete assembly sequence.

Within each stack, the modeled removal preconditions remain: counterhold and fully unthread the nut; capture and slide off the nut; capture and slide off the nut washer; then withdraw the head, head washer, and shaft. Assembly reverses that order. Thread travel, part capture, support changes, and actual tightening are not modeled.

### Scope and provenance

The live obstacle map contained 1,231 shape entries. For this run it included the composed finished source wood, all 16 current finished hosts, all 24 current candidate parts, current panel replacements, 66 fixed panel axes, 72 retained frame-bolt shapes, non-duplicate protected families, and all 460 installed candidate-hardware role shapes across the 92 axes. Unchanged source members, including legs and runners, remained in the composed source-wood map.

The attempt01 report identifies revision and trial `led-clearance-2x6-runner-seated-blocks-v1`, and source inventory SHA-256 `07af4c3eb642cf3887595fe4415eb65404cdcf74d66c5c7bb182847ef21c2d78`. Report SHA-256: `83f53ada10afda7566af7a872c246718e88ad145b9ee2dd12ab6f9a878095c81`. The attempt01 collector snapshot SHA-256 was `d1806f8ca0c69fd87b15c2edea4d948d541829be9a0b57ded1695fcf0dc96a24`; attempt02 records its collector and scene hashes in `parent_run`.

These access and staged-motion probes are bounded CAD diagnostics. They do not validate actual tools or workspace, select delivered hardware, prove assembly or disassembly, establish structural behavior, authorize physical work, or release climbing use.
