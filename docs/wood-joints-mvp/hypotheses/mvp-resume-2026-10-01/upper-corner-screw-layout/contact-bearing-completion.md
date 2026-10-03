# N05/N06: saved-state contact and floor bearing arithmetic

Status: **parent attempt02 completed: PASS_CONDITIONAL_BEARING_ARITHMETIC**.
All four named reference checks passed for the six saved simultaneous nominal
states. The parent's attempt01 remains preserved with its area-equality `STOP`,
diagnosed below. Parent owns assessment integration and publication. This packet owns only
`contact-bearing-completion.py`, this file and ignored
`rawlocal/contact-bearing-completion/`. The published common-compatibility
implementation and all existing mechanics evidence remain frozen.

## Frozen API and preparation evidence

Import performs no calculation or write. The callable API is:

```python
prepare(output)  # Standard library: hashes, JSON geometry joins, NPY headers.
build(output)    # Parent: NumPy arithmetic on the six saved nominal states.
```

Each output must be a fresh immediate child of
`rawlocal/contact-bearing-completion/`. Existing attempts cannot be overwritten.
Both calls return the report dictionary and write a receipt. Authentication or
arithmetic failure writes a `STOP` report/receipt with the exact exception and
retains available partial output, then raises. A bearing ratio above one writes
`FAIL_CONDITIONAL_BEARING_ARITHMETIC` with its complete numerical evidence.

Prepared source SHA-256:

```text
4c1240a296f764d2565edf219e2a5aa1b0fae25958840f7cc64a610662bee1ee
```

The applicable preparation is
[prepare-attempt06/report.json](rawlocal/contact-bearing-completion/prepare-attempt06/report.json),
SHA-256 `30ab87112e4af4f3e0431cedcd8255e2a467183e9d155429c381b16dc517285a`.
Its [receipt](rawlocal/contact-bearing-completion/prepare-attempt06/receipt.json)
SHA-256 is `77e2f550e041c04aa11c32b07fae3afe362bcfa037e85b937b46a7888678e279`.
All **172 pins** authenticated before and after preparation. The producer
snapshot matches the source. AST parsing and Ruff lint passed. The retry
preparation used standard-library provenance/geometry/header operations only;
the diagnosis read the parent's saved JSON outputs. No software tests, review,
new array-value consumption or additional engineering build ran here.
Installed runtime metadata identifies Python 3.12.3 and NumPy 2.5.2 without
importing NumPy. The build enforces those saved versions; SciPy is unnecessary.

Earlier preparation receipts are retained locally. Attempts 01/02 exposed
adapter assumptions about repeated connector axis IDs and corrected-row table
fields; these were metadata failures, not mechanics results. Attempts 03/04
precede the original fe5bb08 source. Attempt05 binds that original source and
remains historical; only attempt06 applies to the revised hash above.

Prepared parent CLI form; the completed attempt02 output is now frozen:

```bash
.venv/bin/python docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/upper-corner-screw-layout/contact-bearing-completion.py \
  --output docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/upper-corner-screw-layout/rawlocal/contact-bearing-completion/attempt02
```

The standard-library command adds `--prepare` and chooses another fresh output.
Build writes `bearing-results.json`, `cell-actions.jsonl`,
`geometry-inventory.json`, `report.json`, `producer.py.snapshot` and
`receipt.json`. Bulky state records remain ignored. The receipt binds every
generated file except itself; reports retain the complete source-pin map.

## Parent attempt02: actual arithmetic result

The parent completed the revised source with exit 0 on Python 3.12.3 / NumPy
2.5.2. [The receipt](rawlocal/contact-bearing-completion/attempt02/receipt.json)
has SHA-256
`7e7fdf6195f1611dcf4b020e75cd6ec9c99b04a09e58bdb7631e9e7d51aae326`.
It records **172 source pins**, authenticated before and after, and binds five
output files. Parent independently checked those bindings. Annotation also
rechecked the receipt, all five outputs and the 172 current source hashes;
all matched. Only this Markdown file is changed by the annotation. Source
`4c1240a296f764d2565edf219e2a5aa1b0fae25958840f7cc64a610662bee1ee`
and the raw attempts remain unchanged.

The [report](rawlocal/contact-bearing-completion/attempt02/report.json)
SHA-256 is
`81bc8a0d053944442af266b220226df7945d6cf6a55654daa71b5ab031c9003c`;
the [bearing results](rawlocal/contact-bearing-completion/attempt02/bearing-results.json)
SHA-256 is
`bc7a5ec00450be5bc444290990970e1461dd8659a8020cab779fe9525d3c4697`.
The [signed cell actions](rawlocal/contact-bearing-completion/attempt02/cell-actions.jsonl)
SHA-256 is
`73ea6f8a50ec0e654fe9d16ff4738eccf9cc7b1133eb4aabfbfa90d83e43d3e9`.

### Completed census and reference checks

The actual census matches preparation: **648 wood-face states** from 108
wood-involving faces, including **96 base-header timber-face states**;
**48 floor-footprint states** from eight footprints, including 12 floor-rail
states; and **5,736 signed cell records** (5,136 wood-involving contact records
plus 600 floor normal projections). The nine panel/panel faces and 214 cells
remain geometry-only inventory. The 104 global / 108 proposal distinction is
unchanged.

Among the 648 wood-face states, 531 have positive resultants and 117 have zero
resultants. The wood-cell records contain 1,387 positive and 3,749 zero normal
forces. Floor records contain 39 positive and nine zero-resultant footprints,
with 394 positive and 206 zero projected cells. Minimum saved signed normal
force across all 5,736 records is 0 N. There are no force/closure branch
disagreements.

| Named conditional check | Result | Maximum governing ratio to unchanged Fc_perp |
| --- | --- | ---: |
| `base_bearing_average` | True | 0.06733931986708995 |
| `base_bearing_quarter_area_sensitivity` | True | 0.18324581125064732 |
| `flush_face_wood_bearing` | True | 0.21552626107373868, represented cell mean |
| `floor_rail_wood_bearing` | True | 0.09296084140475372, uniform mean over the complete eight-footprint inventory |

The two floor rails alone have maximum uniform-mean ratio
**0.0004833893602429162**. The named floor check also compares the six other
saved footprints to the same conditional reference. These are the producer's
four arithmetic reference results; complete-joint acceptance, physical release,
proposal adoption and global-stability acceptance remain false.

### Mean pressures and witnesses in their saved cases

Every witness below uses its own simultaneous `gap_scale = 1.0` state from the
pinned 62bd response. A row index identifies a saved scalar normal-force row;
it does not establish a continuum pressure peak or a physically qualified
receiver/body pose.

| Represented mean | Case and saved witness | Mean, MPa | Ratio to Fc_perp |
| --- | --- | ---: | ---: |
| Maximum base-header active-area average | `a1-rear`, patch 10, `base_header` / `base_post_outer_left` | 0.2901801667316347 | 0.06733931986708995 |
| Maximum wood-cell mean | `k12-rear`, patch 81, `contact_81_2`, raw row 902, `base_rail_top` / `base_side_right` | 0.9287507877546675 | 0.21552626107373868 |
| Maximum floor uniform mean, all eight footprints | `a12-rear`, `floor/lumber_leg_left` | 0.40058902453405815 | 0.09296084140475372 |
| Maximum floor-rail uniform mean, two-rail subset | `a1-rear`, `floor/base_floor_left` | 0.0020830326981092716 | 0.0004833893602429162 |

For the **base witness**, signed resultant is 1,158.378187530604 N. Three of
four cells are positive, with active area 3,991.927500000022 mm² and supported
area 5,322.570000000019 mm². Raw rows 372–375 (`contact_10_0` through
`contact_10_3`) carry, in order,
`[231.56640851758283, 0, 788.0535143808289, 138.7582646321923]` N.
The zero-force row has saved closure −0.004227907071664316 mm and contributes
no active area. The supported-area mean is 0.21763512504872645 MPa, ratio
0.05050448990031756; the governing active-area mean retains only the three
positive cells.

For the **wood-cell witness**, row 902 carries signed normal force
1,235.8352701039835 N over 1,330.6425000098448 mm², with saved closure
0.009287507877591472 mm. Force on the first body is
`[-1235.8352701039835, 0, 0]` N and on the second is its negative. Its saved
point is `[1127.125, 1449.1996489739474, 2216.544445560168]` mm. Only this one
of patch 81's four cells is positive, so the active-face average is also
0.9287507877546674 MPa (ratio 0.21552626107373865). The small difference from
the cell mean is arithmetic rounding. The full supported patch is
5,322.570000063124 mm²; it is not substituted for the active-cell area. The
saved normal is parallel to the top rail's grain and perpendicular to the
side member's grain; the existing conditional reference and material limits
remain explicit.

For the **all-footprint floor witness**, signed upward resultant is
2,927.843798952027 N over 7,308.846772218796 mm², with all four projected
cells positive and mean closure 0.004005890245360643 mm. For the **rail
witness**, it is 144.09614280981432 N over 69,176.13100390004 mm², with all
38 projected cells positive and mean closure 0.00002083032697825101 mm.
These full represented areas follow the saved uniform projection law; neither
witness resolves the physical pressure-patch size.

### Quarter-area references, kept separate from means

All three maximum base sensitivities occur in the same `a1-rear` patch-10
witness above, whose largest signed corner force is 788.0535143808289 N.

| Reference calculation | Maximum ratio to Fc_perp | Interpretation |
| --- | ---: | --- |
| Existing `4 max(R_i) / (A_s Fc_perp)` | 0.1374343584379858 | Largest-corner reference on a quarter of supported area |
| Governing `4 max(R_i) / (A_+ Fc_perp)` | 0.18324581125064732 | Same reference on a quarter of active area; named base sensitivity check |
| Separate `4 sum(R_i) / (A_+ Fc_perp)` | 0.2693572794683598 | Hypothetical total-resultant quarter-area bound; no added acceptance criterion |

The base mean is 0.06733931986708995 of Fc_perp, while its governing
quarter-corner reference is 0.18324581125064732. These quantities use different
numerators and area assumptions. No quarter-area reference or largest saved
cell mean is relabeled as an actual wood stress peak.

### Floor active masks and arithmetic closure

| Nominal case | Positive footprints of eight | Positive left/right floor-rail cells |
| --- | ---: | --- |
| `a12-rear` | 6 | 0 / 38 |
| `a12-forward` | 7 | 0 / 38 |
| `a12-left` | 6 | 0 / 38 |
| `k12-right` | 6 | 38 / 0 |
| `k12-rear` | 6 | 38 / 0 |
| `a1-rear` | 8 | 38 / 38 |

Zero-force footprints retain zero represented active area and zero mean
pressure. Positive footprints passed the complete-cell mask, area-weight
projection, normal-law and exact canonical area-closure guards. No smaller
resolved floor patch, friction coefficient, anchor or new support is inferred.

Maximum saved-state arithmetic residuals across the six cases are:

- Contact/footprint compression-law error: 3.470381102488318e-7 N, below the
  unchanged 1e-4 N source gate.
- Floor area-weight force-projection error: 1.1368683772161603e-13 N.
- Signed group `D` / point-wrench force error: 2.580691216280684e-11 N.
- Signed group `D` / point-wrench moment error: 6.83940015733242e-9 N·mm.

These authenticate the saved normal-force arithmetic and point-action mapping.
They do not resolve unsampled contact, a physical pressure distribution, full
shaft compatibility, or global stability.

## Preserved attempt01 STOP and exact diagnosis

The parent ran the original source
`fe5bb08ce377c3a690ca90ad8a6b8702c6fea39adeed24c38fd548f471b3d5e5`.
[Attempt01's receipt](rawlocal/contact-bearing-completion/attempt01/receipt.json)
has SHA-256 `762d2dc09ebd060a94ff726e02d9f492da1cf4a7b3cdda3a40ccf0e9224adc8f`.
It preserves the exact terminal exception:

```text
ValueError: STOP: floor projection unexpectedly selects a partial area
```

The receipt binds its report, producer snapshot, geometry inventory and
932 partial cell-action records. All four output hashes were rechecked. Before
editing the owned adapter, all 172 original source pins were rechecked and
matched. The STOP receipt itself records before/after authentication as false
because execution terminated before its final authentication stage; this
diagnostic does not rewrite that receipt or turn the failed run into a pass.

The failing group is **`a12-rear / floor/base_floor_right`**, raw rows
1376–1413. Its saved values are:

| Quantity | Saved/diagnostic value |
| --- | ---: |
| Positive normal cells | 38 of 38; zero/negative cells: 0/0 |
| Signed resultant `R_b` | 83.33156912944172 N |
| Minimum/maximum signed cell force | 2.192936029722149 / 2.192936029722153 N |
| Footprint mean closure | 0.000012046289366662616 mm |
| Represented area: inventory's Python `sum` | 69,176.13100390004 mm² |
| Old repeated-addition active-area accumulator | 69,176.13100390008 mm² |
| Accumulator minus represented area | 0.000000000043655745685100555 mm²; 3 ulps |
| Ordered positive-cell `sum` and `math.fsum` | Both 69,176.13100390004 mm² |
| Maximum `R_i − (k_i / sum(k_i)) R_b` magnitude | 0.0000000000000004440892098500626 N |
| Footprint normal-law error magnitude | 0.000000004472383352549514 N |
| Saved local mean pressure range | 0.0012046289366016093–0.0012046289366016095 MPa |
| `R_b / represented_area` | 0.0012046289366016093 MPa |

Every area term matches the receipt-bound geometry inventory. The positive
mask and the area-weighted force projection support full represented area
under the already declared uniform mean-footprint law. There is no partially
selected floor area in these saved values. The failure arose because the old
guard compared repeated floating-point addition against Python 3.12's
compensated `sum` with exact equality.

The revision changes only floor active-area accumulation and its guard
authentication. It uses the identical ordered explicit area terms and `sum`
operation used by the geometry inventory, and also requires all projected
normal cells to be positive when the signed resultant is positive, or all zero
when it is zero. The exact area-equality guard remains. Genuine partial masks
still stop, with case/member/resultant/count or area details. No area rounding,
equality tolerance, force clipping, pressure alteration, additional support,
floor-law change or partial-contact hypothesis is introduced. Timber-contact
arithmetic is unchanged.

## Applicability and source closure

The force state is the saved simultaneous nominal state (`gap_scale = 1.0`),
in this order: `a12-rear`, `a12-forward`, `a12-left`, `k12-right`, `k12-rear`,
`a1-rear`. The six zero-clearance comparison states are authenticated but do
not supply qualification forces or an alternate passing state.

| Frozen input | SHA-256 |
| --- | --- |
| Gravity attempt01 `operator-assessment.json` | `ce69ba58e3c6265d31ab0dfdec1ffac4c019b93fc1106c8f9677ed9b5b2c3f95` |
| Frame attempt02 `response/comparison.json` | `c3a8ff024fb494032d947aedfd6f00cda8698587b8751b2cec66e4b3af243729` |
| Frame attempt02 `response/response.npz` | `62bd4116cfb577a0846f4de0d43fbeec6bb704bac7feee530ee673ded1820f90` |
| Gravity attempt01 `row-identities.json` | `cdf218780bdabdb8774174c79b37d7c9f554abc6be2e1f817999635e56868b27` |
| Existing carrier model with explicit cell areas | `61f95ec9e670b2bd0e95d426cc14ff381283edfc4f9c87e47c2b344dd4fe50b8` |
| Saved finite contact geometry | `034067430fff5207cdb40819fa8118a367edeb29a8d83926928cc96a0e87d151` |
| Corrected top-corner contact geometry | `987af6908d6677165b6a712537ecca0c02827d558ca386ced96f4c1f6436008f` |
| Conditional material inputs | `0f33ad8fd517673a4ebbed36c4a30c1cfe07e0d8163165bdc804af91d958fc5a` |

The producer binds the gravity/frame receipts, their output files, their source
maps, saved contact-geometry source maps and current gravity model-input source
map. Conflicting hashes stop consumption. No source is repinned. Neither the
washer attempt02 receipt nor the common-compatibility leaves are consumed.

The authenticated modeled mass is 225.19791414318078 kg, with dead-load factor
1.1110134616260479 and unchanged saved live-load scales. No load, stiffness,
gap, contact area, supported footprint, geometry or receiver allocation is
adjusted. The current global response still has **104 structural bolt axes**;
the **108-axis proposal** contains four internal ties absent from these global
rows. These arithmetic checks do not qualify their passive law or common pose,
or establish changed-hole elastic stiffness.

## Reused methods and necessary authentication

The preparation reuses the pure `dot`, `norm`, `sub`, `cross` and `angle`
definitions from `retained_group_checks.py`. Build reuses `wrench` from
`top_corner_actions.py`. Only authenticated function definitions are loaded;
their module workflows are not imported or executed.

The two bearing expressions are extracted directly from
`scripts/compact_thick_results.py:base_comparisons`. Its unrelated notch/shear
calculation and historical member inventory are not run. The local cell-mean
comparison preserves the method in
`scripts/floor_flush_checks.py:face_contact_check`, with an explicit signed
nonnegative-force gate preceding division. Its historical six-interface census
is replaced by the authenticated current contact inventory.

The floor adapter follows the saved `simple_frame.py:lump_floor` mapping:
nonfloor rows retain their raw ordering; sorted floor members receive one
normal and two assumed no-slip tangent coordinates. Normal weights are the
saved stiffness fractions, independently checked against explicit area
fractions. The dense floor operator transformation is not rerun.

The finite build performs only these checks:

1. Consume the nominal force and displacement arrays from the same pinned
   response. Resolve each contact row to the exact cell area, member pair,
   point, signed compression direction and source law. Sum cells back to
   extracted face areas, preserving holes and corrected top-corner areas.
2. Authenticate the signed raw `D` row against its two body columns and actual
   point; reject hidden body actions or undeclared free couples. Recover group
   force/moment about the saved face datum with the existing wrench helper.
3. Verify signed normal forces are nonnegative, with no absolute-value
   conversion or force clipping. Verify `f = k max(q, 0)` against the existing
   0.0001 N law gate and positive 10 mm source-state domain. Verify floor
   resultants and raw-cell area-weight projections against the same law gate.
   Require the complete positive/zero normal-cell mask dictated by the saved
   uniform projection, and sum active floor areas identically to the inventory
   before applying the retained exact area-closure guard.
4. Compute means and declared sensitivities, retain each signed cell action,
   and compare only to the unchanged conditional reference. Do not solve a
   frame, fit a pose, evaluate stability or sample another load state.

The 1,106 inherited normal-contact/floor rows retain their serialized
`[-10, 10]` mm native tables. The 64 corrected contact rows serialize the
explicit mathematical compression law and stiffness, without table/domain
fields. The adapter records that absence and uses the explicit law under the
saved frame's positive-domain gate; it does not invent a native table.

## Census and bearing definitions

| Inventory | Per state | Six nominal states |
| --- | ---: | ---: |
| Timber/timber faces | 82 | 492 |
| Timber/panel faces, wood side only | 26 | 156 |
| Wood-involving contact cells | 856 | 5,136 |
| Base-header timber faces, subset of the above | 16 | 96 |
| Floor footprints | 8 | 48 |
| Floor normal projection cells | 100 | 600 |
| Floor rails, subset of the eight footprints | 2 | 12 |

The nine panel/panel faces, containing 214 cells, remain in the authenticated
geometry inventory and receive no wood-capacity comparison. The body census is
44 timber plus six panels, with 1,888 raw rows, 1,588 nonfloor coordinates,
1,612 lumped coordinates and 300 rigid columns. All sixteen base-header timber
faces retain four saved corner cells; their actual cell areas need not be equal.
The two additional base-header/panel faces are included in the wood-side flush
inventory, not the timber/timber base subset.

For a face, let `R_i` be the saved signed normal force, `a_i` its explicit cell
area, `A_s = sum(a_i)` and `A_+ = sum(a_i for R_i > 0)`. Positive saved force
defines represented active area without a fitted engagement threshold. Saved
closure signs and all force/closure branch disagreements are retained alongside
the source tolerances; this does not resolve a continuum active patch.

The unchanged conditional reference is
`Fc_perp = 625 psi = 4.309223308230226 MPa`.

- Active-face average: `sum(R_i) / (A_+ Fc_perp)`.
- Full supported-area mean, explicitly labeled: `sum(R_i) / (A_s Fc_perp)`.
- Local cell mean: `R_i / (a_i Fc_perp)`. The maximum of these represented
  means supplies the flush-face check, **not a stress-peak claim**.
- Existing base quarter-corner sensitivity:
  `4 max(R_i) / (A_s Fc_perp)`.
- Required active-area extension of the same base sensitivity:
  `4 max(R_i) / (A_+ Fc_perp)`. This is at least as demanding as the existing
  supported-area formula. The base sensitivity gate uses this extension.
- Separately labeled total-resultant quarter-active-area bound:
  `4 sum(R_i) / (A_+ Fc_perp)`. This is reported as a sensitivity; it is not
  silently substituted for the adopted largest-corner formula or made another
  acceptance criterion.

A zero-force face has zero active area and zero ratios. Nonzero force with no
area stops. A ratio above one fails the relevant conditional arithmetic check;
the implementation never changes input values to obtain a pass.

## Eight saved floor footprints

| Member | Normal cells | Saved supported area, mm² |
| --- | ---: | ---: |
| `base_floor_left` | 38 | 69,176.13100390004 |
| `base_floor_right` | 38 | 69,176.13100390004 |
| `base_post_center_left` | 4 | 5,322.569999999999 |
| `base_post_center_right` | 4 | 5,322.569999999999 |
| `base_post_outer_left` | 4 | 5,322.570000000019 |
| `base_post_outer_right` | 4 | 5,322.570000000019 |
| `lumber_leg_left` | 4 | 7,308.846772218796 |
| `lumber_leg_right` | 4 | 7,308.846772218796 |

These areas are sums of the actual saved extracted-floor cells, not whole
member-face rectangles or fabricated extra runner contacts. The two
`base_floor_*` footprints are identified as floor rails; all eight receive
signed normal reaction/area records and the conditional reference comparison.
The build reports maxima for both the eight-footprint inventory and the
two-rail subset.

For footprint `b`, `R_b = sum(R_i)`,
`R_i = (k_i / sum(k_i)) R_b`, and `k_i = 100 a_i`. Consequently the saved
uniform mean model makes every positive projected cell have the same pressure
`R_b / sum(a_i)`. A positive mean footprint uses its full supported area only
under this explicit model hypothesis; an open/zero-force footprint has zero
represented active area. This is not evidence that every physical point bears
or that a smaller uplifted pressure patch was resolved.

Normal-to-grain angles are retained for each timber side. The floor rails have
90° normals; post footprints are end-grain (0°), and leg footprints are oblique
(about 13.8365°). All comparisons use the existing 625 psi conditional envelope;
the packet does not invent oblique-grain resistance or qualify actual stock.

## Remaining limits and parent result

Parent attempt02 completed the declared N05/N06 arithmetic for the saved six
global states: all four named conditional reference checks are true. Attempt01
remains a preserved failed adapter run; its diagnosis and source correction
are not substituted for attempt02's actual result. The completed arithmetic cannot
establish continuum pressure peaks, contact refinement, plywood resistance,
actual delivered-material resistance, new-tie compatibility, changed-hole
stiffness, global stability or permanent acceptance.

Finite floor friction, anchors and floor tests remain outside the adopted
no-slip assumption. No serviceability threshold is introduced. Parent owns
stability and permanent assessment; the splitting peer owns its normal
anchorage child. This packet supplies neither duplicate evaluation.

The source/doc leaves, preparation evidence and both actual attempts stay active
for parent assessment integration and publication. Earlier preparation attempts
remain recoverable in ignored storage; no source/evidence file is pruned or
replaced. Publication does not expand the saved-state or conditional-material
claim boundary.
