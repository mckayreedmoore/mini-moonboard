# Bottom-outer joint method review

## Finding

The row `bottom_outer/clip_horizontal_bottom_left_1/side_1` is a priority
unadjusted-reference flag, not an adopted strength failure or a joint pass.
The pinned single-shear census reports A1 rear, increment 6, at full load:
`661.948743401738 N` lateral resultant divided by a `604.7906633288045 N`
conditional, unadjusted Mode IV reference, or `1.0945088665197509`. It also
records a distinct `197.1248 N` outer-seat tie from source row `SPR1747`; that
axial action is not added to the lateral resultant. The reference producer
explicitly leaves material/hardware unobserved, adjustments unapplied, and
joint acceptance false.

The row is tied to plane `bottom_outer/clip_horizontal_bottom_left_1/side_1/plane-11`,
source rows `SPR1343` and `SPR1344`, at `(-1130.3, 32.3331282441,
473.6550246017) mm`. On `base_side_left`, the signed force is approximately
`(0, 476.4185, -459.5667) N`; the `bottom_outer_left_cleat` receives its
opposite. Both role permutations give the same Mode IV reference and
unadjusted quotient. The producer's 1/4-in diameter, 45-ksi `Fyb`, SG 0.50,
and conditional grain/bearing inputs are arithmetic-scenario values, not
adopted properties.

## Current finished contact geometry

The WJ24 diagnostic's older `bottom_outer_left_cleat` record reports only the
gross candidate rectangles (`10641.33 mm²`) and leaves finite finished paired
area null. That is stale for nominal geometry. The later current geometric
interface graph and face-pair atlas bind the exact current STEP solids and
resolve both block interfaces after the existing bores/cuts:

| Graph pair ID and members | Graph state and area | Exact opposed source faces | Plane / normal evidence |
| --- | --- | --- | --- |
| `pair:base_side_left|bottom_outer_left_cleat` | `finite_opposed_planar_touch`, `10552.97270661779 mm²`, zero separation and zero common volume; members `base_side_left` / `bottom_outer_left_cleat` | `base_side_left/step-face-0003-770bd7c611abef4d`; `bottom_outer_left_cleat/step-face-0008-f4d81f23e647c6a3` | Coplanar at `x=-1130.3 mm`; normals `(1,0,0)` and `(-1,0,0)`; one intersection region, three wires including the two through-bore loops |
| `pair:base_rail_bottom_left|bottom_outer_left_cleat` | `finite_opposed_planar_touch`, `10552.972706617795 mm²`, zero separation and zero common volume; members `base_rail_bottom_left` / `bottom_outer_left_cleat` | `base_rail_bottom_left/step-face-0008-fa792af1a0f62a37`; `bottom_outer_left_cleat/step-face-0004-a73fda4bfedc0eed` | Coplanar offset `0`; normals `(0, 0.64278761, 0.766044443)` and its opposite; one intersection region, three wires including the two through-bore loops |
| `pair:base_rail_bottom_left|base_side_left` | `finite_opposed_planar_touch`, `5322.57 mm²`, nominal separation `6.4e-14 mm`, zero common volume; members `base_rail_bottom_left` / `base_side_left`, no bolt association | `base_rail_bottom_left/step-face-0002-ccfa30bcf5a38caf`; `base_side_left/step-face-0003-770bd7c611abef4d` | Coplanar at `x=-1130.3 mm`; normals `(-1,0,0)` and `(1,0,0)`; one no-hole intersection region |

For the first two rows, the saved intersection-region centroid and extent are
also source-bound. The side/cleat patch is on `x=-1130.3 mm`, has bounds
`y=[-31.512684747, 117.326653595] mm`, `z=[413.734941755, 558.777969627] mm`,
and centroid `(-1130.3, 42.906715329, 486.256134997) mm`. The rail/cleat patch
has bounds `x=[-1130.3, -1041.4] mm`, `y=[-31.512684747, 60.182835094] mm`,
`z=[413.734941755, 490.676618634] mm`, and centroid
`(-1085.85837274, 14.335075174, 452.205780194) mm`. Each has two circular
trim loops at the fastener bores. This is nominal exact-BRep face overlap,
not proof of installed contact, pressure distribution, tolerance fit, bearing
adequacy, or load sharing.

The exact member STEP hashes are `base_side_left.step`
`237c3fa6aa0b52c39124580810d048e38919b99b9a1fb5db5a2423e7eda62fdf`,
`base_rail_bottom_left.step`
`724d46fa7902a949b79b0fd6132c5e57c580be80aad7d059c29e04494ff79923`, and
`bottom_outer_left_cleat.step`
`28d1b5fee748c38e30e3d2618c8377cfe374c7ccd0b520736c25841720824438` under
`docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-full-frame-member-solids-attempt01/bundle/members/`.
The contact graph at
`docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-geometric-interface-map-attempt02-2026-09-28/complete-contact-graph.json`
is SHA-256
`7806242ac48b198becf5db97b16b6a5605021b8d86b964f0f02adb6806aeec26`, with
source-pin file
`590112932d73dc57da015382a8ebf6e0fc85a8c5e8338549f381b8bd7732ba5c`. The
face-pair atlas at
`docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-geometric-interface-face-atlas-attempt01-2026-09-28/face-pair-atlas.json`
is SHA-256
`d455b374b238039a509bc9254fd7ea36cfbf6078af52468fbe20b31ec72e3ee9`, with
source pins
`b92dcec2638fc335951033a0289cdc50bc0a949cb397b46bc03c1ad185e3c30d`.
The graph's exact interface measurement uses the pinned
`scripts/wood_joint_current_receiver_screen.py` (`e827d30f6dfdffed3bd9f17a7f905e03d4c936c56a8a0d0890ca3b1dcfb2caa2`),
`scripts/wood_joint_current_contact_graph.py`
(`8afed27a493719354c55b6c0deb5faeb1cd40068519d4578c365db120f293f7d`),
and `mini_moonboard/wood_joint_geometry.py`
(`e437385d4894c7bcd4bbf4ee66aa9f96a53a8d3570efc6230fb225570abbb90e`).
The atlas pins `scripts/wood_joint_current_face_pair_atlas_attempt01.py`
(`016dbce14bff6408de418fc6cce35fa0590a72ceef43565164aa10f4b4bea3bb`).
The recorded rebuild environment is CadQuery 2.8.0 / OCP 7.9.3.1.1. Face
ordinals identify only these pinned STEP bytes and importer.

## What the comparison can support

The target shaft axis is approximately global X and the extracted signed
lateral force lies in Y/Z, so the perpendicular-load-to-dowel-axis condition
in 2024 NDS Chapter 12 §12.3.1 is met for this source plane. The updated graph
also establishes the nominal opposed planar face regions; it supersedes the
older WJ24 gross-rectangle/null-area field. Section 12.3.1's remaining
conditions still require the specified member faces to be brought into
contact and the applicable edge, end, and spacing minimums to be met. NDS
Chapter 11 §11.1.5 describes the reference-value assumption that contacting
faces are brought together during installation. The source geometry does not
establish delivered fit, contact pressure, or actual installation.

This is not a two-member isolated bolt check for a complete corner. The
`bottom_outer_left_cleat` joins `base_side_left` at `side_1` and `side_2`, and
joins `base_rail_bottom_left` at `rail_1` and `rail_2`; the two host members
also have the separate nominal 5322.57 mm² touch above. The four bolt-axis
actions and these three interfaces define a coupled, three-body load path.
Do not infer equal sharing from two bolts per interface, add the four demand
magnitudes, or treat the target Mode IV reference as the capacity of the
block joint. The same-state ties remain separately tracked.

The current conditional grain frames also change how those three faces may
be checked for contact bearing. The normals of both cleat mating faces are
perpendicular to the proposed grain directions in each paired member. By
contrast, the direct host-to-host face normal is perpendicular to the
proposed `base_side_left` grain but parallel to the proposed
`base_rail_bottom_left` grain. Therefore the conditional No. 2
`Fc⊥=625 psi` Table 4A reference can inform only a bounded comparison for
perpendicular-to-grain receivers when the source-cell pressure is compressive;
it cannot be copied to both receivers of the direct host contact. The
parallel-to-grain rail receiver needs its applicable compression method and
adjustments. These are grain-map scenarios, not observed member orientation,
and no face geometry by itself supplies signed pressure.

The pinned official 2024 NDS Chapter 11 source (SHA-256
`45a3d78de1a4fba573589be0fc776e37bd581e4cedec24e38d63856161092d33`,
`upper-block-strength-2026-10-01/source-cache/chapter11-2024-awc-20260911.pdf`)
sets the group scope: §§11.1.2 and 11.2.2 require local-force evaluation by
engineering mechanics and limit the sum of same-size/type fastener values to
the sum of adjusted individual values; §11.3.1 applies all relevant factors;
§11.3.6 defines the dowel-row group factor. For the source's 1/4-in scenario,
do not set `Cg=1` without checking its row conditions and group geometry.
2024 NDS Chapter 12 §12.5.1.1–.3 (printed pp. 98–99) governs the applicable
edge/end/spacing terms. §§12.6.2–.3 (printed p. 100) call for group load
distribution/local-stress evaluation when multiple fasteners carry angled
loads. No values for `Cg`, `CΔ`, `CD`, or other adjustment terms are selected
here.

The scenario's 45-ksi `Fyb` is not established for a quarter-inch bolt by
2024 NDS Table 12A (printed p. 101): the printed table's 45-ksi entry begins
at 1/2-in diameter. The source register separately records 106-ksi only as
an empirical estimate, not a guaranteed minimum. No resistance is adopted in
this review.
The receiver grain maps are proposed conditional inputs, not observations;
their source pins are `f867b4926ed23c9f356005c134778e138c8b1230547f0b69be7c3f9bc2a42409` (frame map) and
`8705b8f100a2d3355c236fc19e6798bb7ad4862ba2d51826cf63a88db1285480` (block
map). The 10-axis end-grain cohort, the upper owner's 32-axis cohort, and the
mechanics owner's six-axis exclusions remain outside this one-row review.

## Bounded next calculation

For a conditional engineering disposition, continue from the frozen exact
source cells and all-body actions: form a signed free body for the complete
cleat and its connected host groups, preserving the four bolt-plane vectors,
separate tie loads, moments about stated datums, and the three possible
contact interfaces. Check contact-cell pressure/bearing and per-member local
stresses from the actual source geometry and its conditional material basis.
Then evaluate individual NDS lateral-yield modes and all supported adjustment
and group terms from the applicable spacing, edge/end geometry, hardware
specification, grain/material basis, and declared service conditions. If a
required design input is not yet specified, report that dependency without
substituting a favorable factor or treating unobserved Actual fields as
checked. This is a bounded engineering-input dependency, not a blanket
physical inspection, received-product test, or external sign-off prerequisite.

For a perpendicular-to-grain contact receiver, Table 4A's conditional No. 2
`Fc⊥` base value is 625 psi under its normal-load-duration, dry-service row
(official 2024 NDS Supplement, printed p. 34; pinned file below). The direct
base-rail receiver is parallel-to-grain under the proposed frame, so leave its
`Fc⊥` comparison inapplicable until a supported parallel-grain method is
specified. Apply only factors that match each member, orientation, and
declared service case.

The resulting calculation may classify this axis within the complete
bottom-outer joint only after those group and alternate load paths are
accounted for. Until then, `1.0945088665` flags that the source demand exceeds
the current conditional unadjusted reference; it does not by itself establish
an adopted failure, a joint acceptance, or the status of any excluded cohort.

## Frozen source identities

- Single-shear producer: `remaining-single-shear-reference-2026-10-01/produce.py`, SHA-256 `5f2a7fdca2ef0c56c661fa10e4122189f8a7a1ae0725062cb8c56d95dd911edf`.
- Producer report: `/tmp/mini-moonboard-remaining-single-shear-reference-2026-10-01.json`, SHA-256 `6551861db1112c91b87c5705bbceb3bb26f55f0d7e70029a74d828519425145e`.
- Source demand producer: `remaining-candidate-washer-demands-2026-10-01/produce.py`, SHA-256 `0c58a7dc6c82ccc2624ee9d3355e2840f738be01961ddaf3f64486700e89e6c9`. The reused helpers are `fea/dowel_yield.py` (SHA-256 `d6c318e75c1a720d0b91f810a892e8309ef89735f66f48820ee853b753f8fe45`) and `mini_moonboard/bolted_timber_checks.py` (SHA-256 `a1414547d9eaa3d60e81482b4a2cac2d49e88f31aafa341dca5be9ec8ef4aa13`); they implement individual-fastener reference arithmetic, not the complete cleat group disposition.
- Current geometric contact graph and exact face atlas: paths and hashes above. Both are nominal geometry records; neither carries contact load or resistance.
- Pinned official AWC 2024 NDS Chapter 12: `hardware-material-specification-2026-09-30/materials-source/AWC_NDS2024_withCommentary_20250328_WebsiteChapter-12-Dowel-type-fasteners.pdf`, SHA-256 `5fc837523ff10acc097a162718700a9b4ba64e627d2b0023439146d42fe4ee2a`.
- Pinned official AWC 2024 NDS Supplement Chapter 4/Table 4A source for conditional No. 2 material inputs: `hardware-material-specification-2026-09-30/materials-source/AWC_NDS2024-Supplement_20240719_Chapter-4-Reference-Design-Values_Website-1.pdf`, SHA-256 `1f65975633f111c308944c470b6cc10e9207b6c45e8a0804b8bdec3378bbc71b`.
