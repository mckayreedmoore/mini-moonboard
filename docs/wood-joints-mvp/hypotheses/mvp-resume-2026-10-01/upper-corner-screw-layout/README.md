# Upper-corner screw layout and climber-weight comparison

The owner authorized moving the upper screw upward on October 2, 2026,
retained 250 lb as the intended upper limit including dynamic moves, and
reported an actual weight of 140 lb. This child calculation moves four
upper-panel corner axes to the upper horizontal row, retaining 66 Hillman
42605 screws and their purchased/pilot policy. It is a calculated revision,
not an installed change or a board rating. Reviewed source geometry,
selected authority and previous force packets are preserved.

## Four changed stations

Each axis moves 65.95 mm up the panel: global translation
`[0, 42.391842858827275, 50.5206310236966]` mm. Screw direction is unchanged.
New front datums share Y=1537.324502383678 and Z=2130.164909134918 mm.

| Axis | X datum, mm | Previous receiver | New receiver |
| --- | ---: | --- | --- |
| `round_panel_upper_left_rim_4` | −1200.15 | `base_side_left` | Same |
| `round_panel_upper_right_rim_4` | 1196.975 | `base_side_right` | Same |
| `round_panel_upper_left_center_4` | −70 | `base_principal_center_left` | `base_rail_top` |
| `round_panel_upper_right_center_4` | 70 | `base_principal_center_right` | `base_rail_top` |

Lower-panel stations are unchanged. This addresses one recorded layout
difference; it does not establish equivalence to the manufacturer's backing,
hardware or loads. See the [mounting comparison](../panel-attachment/official-pattern-comparison.md).

## Geometry and frame scope

`geometry.py` imports seven saved STEP solids without rebuilding the scene.
Each new nominal screw cylinder intersects its panel and proposed receiver:
245.778618 and 609.103531 mm³ respectively, with zero minimum distance to
both solids. Projected stock-frame receiver overlap is 45.24375 mm; nearest
stock edge is 19.05 mm away. Front-datum to saved panel outer-wire distance
is 26.385473 mm in three dimensions, not the projected in-plane edge distance.
There are no conservative screw/bolt-axis overlap candidates. These nominal
recorded cylinders do not cover delivered heads, tools, holds or complete
installation clearance. Intersection alone does not establish resistance.
Saved old bores remain; no new bores are cut.

`reproject.py` rebuilds 12 connector rows and recomputes their elastic
projections in seven incident members from authenticated saved native
matrices. Receiving-body identities and wrench mapping change for the two
center screws. Filled-bore gross stiffness, all material/contact hypotheses,
frame-bolt layouts and 88 independent two-receiver clearances are retained.
No native solve is launched.

The relocated 250 lb packet completes six zero-gap and six nominal-gap
states. Original balance, contact/spring laws, no-slip floor laws and 10 mm
positive-spring domain checks pass. Nominal states retain rank 296/297 with
finite fixed-force seating bounds; saved poses are representative, not
unique motion envelopes or a strict stability result.

## Head force and weight comparison

`head_check.py` checks all 792 saved screw states. Axial screw force loads
both the head pull-through route and timber thread-withdrawal route. Their
resistances are separate; retained generic references are unadjusted
hypotheses, not measured Hillman capacities.

| Scenario | Downward live force | Horizontal force | Complete states | Peak axial demand |
| --- | ---: | ---: | --- | ---: |
| Preserved layout, 250 lb dynamic | 2224.111 N | 300 N | 12 | 1836.884 N nominal gap |
| Four moved axes, 250 lb dynamic | 2224.111 N | 300 N | 12 | 1871.251 N nominal gap; 1923.816 N zero gap |
| Four moved axes, 140 lb, same acceleration | 1245.502 N | 168 N | 2 of 12; STOP | Returned rear zero-gap state 1084.950 N; no full envelope |
| Four moved axes, 140 lb, fixed horizontal | 1245.502 N | 300 N | 2 of 12; STOP | Returned rear zero-gap state 1158.909 N; no full envelope |

Relocated 250 lb nominal demand governs at the **unmoved** upper-left
`edge_2`, A12-rear: T=1871.251 N, simultaneous V=726.611 N and opening
0.695715 mm. Favorable retained generic head reference is 628.941 N;
demand/reference is 2.97524. Relocation does not close this comparison.
No physical failure is inferred and no 140 lb or 250 lb rating is established.

The [load-origin worksheet](../panel-attachment/load-realism.md) traces
250 lb × 2, 300 N and the 100 mm front-face lever. Dynamic and horizontal/lever
choices remain illustrative sensitivities, not measured bounds on the
owner's moves. Weight comparison scales live loads only; gravity and the
25 kg accessory allowance stay unchanged. `load_components.py` separates
vertical/horizontal nodal loads for correct fixed-300 N wrenches. Original
reconstruction errors are 2.403e−9 mm elastic response and zero rigid wrench.

## Incomplete calculations and numerical limits

Both 140 lb scenarios return A12-rear and A12-forward zero-gap states, then
stop on `normal active-set cycle` at A12-left zero gap. Neither has a complete
force set or nominal-gap comparison. Multiplying the 250 lb peak cannot
establish the 140 lb envelope. Terminal iterates are unaccepted; these STOPs
are calculation outcomes, not physical frame failure claims.

Proportional attempts 01, 03 and 04 retain STOP receipts, partial accepted
responses and unaccepted iterates. Attempt 02 stopped during QP seeding
before that retention path. Relocated 250 lb attempt 01 stopped at a
1.708e−8 mm projection residual, then hit a relative-path receipt error;
its partial files are preserved. Attempt 02 resolves paths and continues
the same projection equations to the original 1e−8 mm tolerance. No force
law or tolerance is relaxed.

`floor_seed.py` then checks 37 fixed floor masks within two changes of the
suggested open rows 1588/1603, using the existing zero-clearance convex QP.
No candidate meets all original spring/floor checks. The best finite guess
has a 0.005174 N finite-law residual and holds one tangent pair whose normal
force is effectively zero; it is explicitly unaccepted. Passing that guess
through the unchanged final method again stops on `normal active-set cycle`.
The search is bounded and not exhaustive, so it proves neither absence of
every mathematical branch nor physical frame failure. It supplies no new
floor law, anchor or resistance. A complete 140 lb result still requires a
consistent contact branch in the declared model.

## Reproduction and local receipts

Use NumPy 2.2.6, SciPy 1.15.3 and OSQP 1.0.4, with parent serialization:

```sh
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 uv run --no-project \
  --with numpy==2.2.6 --with scipy==1.15.3 --with osqp==1.0.4 python \
  docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/both_corner_frame.py \
  --output <new-output-directory> \
  --frame-directory docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/upper-corner-screw-layout/operators-attempt02 \
  --connection-inputs docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/upper-corner-screw-layout/operators-attempt02/model-inputs.json \
  --all-two-receiver-clearances --service-joints --bottom-corners --bounded-freeplay
```

For proportional 140 lb add `--climber-load-scale .56`. For fixed-horizontal
140 lb also provide `--live-components` pointing to `load-components-attempt01`
and `--horizontal-load-scale 1`. Existing output directories are preserved.
Raw artifacts remain local and ignored.

| Local artifact | SHA-256 |
| --- | --- |
| `operators-attempt02/operator-assessment.json` | `1a82cd2adbfece3942bf8c90f593f1e21a150adb65db625135aadd258fd5024a` |
| `operators-attempt02/operators.npz` | `c9483639c69c0696b29f3fd69522e6c9a8e673aa7ce82277788103b14c955ba3` |
| `load-components-attempt01/receipt.json` | `178a745fe832f9521591b82a26cd6952e108aa374f1e27b7e010a876edf19a0e` |
| `frame-250-attempt02/comparison.json` | `bea6cbc330af3cdb20499d774a8f6bb24481d687c3150adb01ede18e4c1d50ca` |
| `frame-250-attempt02/response.npz` | `0625196497b0dbc7b297724d7b9947f7c7c61bb282cd4d9681705629302c76c7` |
| `rawlocal/attempt01/result.json` | `81b75c3fe8dced195d36d3a2a3f1ca69b1e796b89e048870a16e3864bb5a06d9` |
| `rawlocal/head-check/attempt01/receipt.json` | `be53a3e7cfbb674b00a5571df228b318908ead3726dfbb2fa26e49689df659af` |
| `frame-140-proportional-attempt04/stop.json` | `87507c034d5bd67784e1a1150583aa28ad98bb75c7d70bae356600b3bc5c363a` |
| `frame-140-fixed300-attempt01/stop.json` | `95f4e076dfb7d58c923bbab69b4aaaea15b67c84f97198e81cbc45c0ee35c0e8` |
| `rawlocal/floor-seed/attempt-2btt9hm9/report.json` | `e29b488633f3795816debf31bb3fcac049000fb137516f7cbb3fa760ba5f0861` |
| `rawlocal/floor-seed/attempt-2btt9hm9/final-method-replay.json` | `e3bc397e83278107a7497461de6599a2189b8afde3b05280bd3db4e7bfe9410a` |

Formal 47 criteria, release flags and earlier component checks retain their
original authorities. Results do not transfer to the new force source
without applicable recalculation.
