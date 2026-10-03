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

### Successful network retry

On October 2, a direct HTTP retry reached the owner's
[YouTube reference](https://www.youtube.com/watch?v=wDB6Lg4x_lM&t=99s)
and its official oEmbed metadata. The video is MoonClimbing's *The Best
Boulders on the Mini MoonBoard (Highly Requested!)*. The parent inspected
the supplied storyboard sheet covering 90–170 seconds, including the frames
at 90 and 100 seconds around the requested time. This is a climbing
demonstration. The 320×180 frames show the panel front and timber frame,
but do not establish a complete screw census, exact head dimensions or
rear backing. No video load measurement or hardware capacity is inferred.
The earlier fetch failure in the mounting worksheet is a retained attempt,
superseded by this successful limited inspection.

The downloaded sheet is preserved at
`/tmp/mini-moonboard-official-video-90-170s-storyboard.jpg`, SHA-256
`cd5773c1340937bee5f3cce75e10d3285c1531b9b8f70e34fbd57786f0313e52`.
The official [Mini DIY build guide](https://moonclimbing.com/media/moonboard-pdf/How-to-build-a-MoonBoard_v2.3.pdf)
specifies four upright supports at 813 mm spacing and horizontal 18 mm
plywood braces at the indicated panel joints. Those instructions do not
supply Hillman 42605 design values or a rating for this separate frame.

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

The [head-reference basis](head-reference-basis.md) verifies the equations
and corrects their plywood grade/species applicability. Quoted head values
are ASD design allowances, not breaking loads. An explicit favorable
connection-duration factor of 1.6 raises the largest reference to 1006.306 N;
the saved 1871.251 N nominal demand still exceeds that comparison.
The same worksheet now ingests the prior exact-part retailer head input,
0.355 in = 9.017 mm. Its favorable adjusted references are 930.222 N with
the stated countersink reduction and 984.128 N without it. These are
retailer-nominal geometry branches, not measured Hillman capacities; the
generic 9.2202 mm rows and original force outputs remain preserved.

The [fresh member replay](member-replay.md) restores all 264 balances and
55,176 cut traces. Normal/stability references remain below one under the
declared timber restraints; top-rail face shear/torsion improves to 1.021524,
still above the unchanged reference. The [bolted component replay](bolted-replay.md)
checks both top corners and the 92 axes included by the remaining-bolt method.
These are fresh results for this force source, with their applicability
limits retained. The separate end-grain and lower-service methods now also
use these vectors: their 92 ksi individual lateral ratios peak at 0.052042
and 0.007468. The [fresh header replay](header-replay.md) also checks twelve
axes, 36 interfaces, 42 balances and 1,260 section states, with no first-face
short comparison in its bounded placement method. They do not close
whole-joint qualification.

The remaining fresh replay covers bottom corners, the partial central-seat
scenario and retained pair/washer references in the same
[bolted record](bolted-replay.md). Retained row sensitivity peaks at
0.962538; ideal washer references peak at 0.208053/0.264300 for the
3/8-/1/2-inch families. The [continuous-knee replay](knee-replay.md)
recovers all 24 bearing fields and 96 endpoint constructions, plus 96
straight-shaft placement witnesses. Its conditional 92 ksi endpoint
scenario is below one; the alternative 45 ksi scenario exceeds one in
seven states. These methods preserve their existing limitations rather
than establish new acceptance rules.

The [shop overlay](shop-addendum.md) publishes all 66 axis coordinates with
62 unchanged and four moved records, binding 172 saved geometry source
pins. Body and hardware counts, purchased screw policy and the owner-selected
pilot/countersink sizes remain unchanged. This child schedule is not adopted
by the existing shop guide and does not direct physical drilling.

The [load-origin worksheet](../panel-attachment/load-realism.md) traces
250 lb × 2, 300 N and the 100 mm front-face lever. Dynamic and horizontal/lever
choices remain illustrative sensitivities, not measured bounds on the
owner's moves. Weight comparison scales live loads only; gravity and the
25 kg accessory allowance stay unchanged. `load_components.py` separates
vertical/horizontal nodal loads for correct fixed-300 N wrenches. Original
reconstruction errors are 2.403e−9 mm elastic response and zero rigid wrench.

The completed [main-panel grain comparison](panel-orientation-comparison.md)
matches the conditional three-sheet option's strong-X orientation. All twelve
states return; nominal peak head force falls to 1280.799 N while lower-left
panel demand rises. The favorable declared head references remain below that
peak. This comparison preserves the current strong-T source and its component
replays; actual grain placement and any replacement force source are unselected.

The [matched 20-per-main comparison](count-grain-comparison.md) also completes
all twelve states. Upper-panel axial demand falls to 1030/1122 N, while an
added lower-left screw reaches 2181 N at A1-rear. Same applied load and source
laws; count alone does not close the attachment comparison. The proposed
98-total layout remains separate from the current physical 66-axis policy.

The [signed lower-panel contact account](panel-contact-sharing.md) traces that
peak to changed local tension/compression sharing with the same external
wrench. Approximately 95 mm pressure sampling, a numerical contact penalty
and unmeasured screw laws are explicit assumptions to check before a hardware
conclusion. The [140 lb strong-X comparison](weight-comparison.md) returns two
zero-clearance states with 777.501/656.745 N head peaks, then stops on contact
cycling. It supplies no full lighter-user envelope or replacement 250 lb limit.

The [saved contact-gap recovery](contact-gap-recovery.md) reproduces all
original bottom-rail contact coordinates within 1.42e-10 mm and finds
0.044593/0.010851 mm maximum closure at additional half-spacing samples.
Those largest witnesses lie away from the new peak screw; samples nearest
it remain open. This identifies sampling sensitivity without establishing
a corrected screw allocation or a physical failure.

The [area-preserving patch59 refinement](patch-contact-refinement.md) then
returns A1-rear at nominal clearances for both screw counts. Replacing
22 contact cells with 44 changes peak T from 1213.615 to 1210.324 N and
2180.721 to 2153.579 N, respectively. This one refinement gives modest
force changes and leaves unsampled positive closure in the recovered
surface fields. It neither resolves continuous contact nor replaces the
complete twelve-state force sources.

## Incomplete calculations and numerical limits

The [one hand/foot comparison](paired-load-comparison.md) moves half the
upper-hold vertical force to the saved lower-left A1 hold while preserving
250 lb × 2 and the original resultant forces. Five moments change. A12-rear
nominal demand falls from 1871 to 980 N, demonstrating sensitivity to load
placement. Six zero-gap and two nominal states return, then A12-left nominal
stops on `normal active-set cycle`. This supplies no full nominal envelope
or adopted stance. Even returned demands retain head-reference exceptions.

The [upper-right washer transfer note](upper-right-washer-transfer.md)
reproduces all 24 saved strip demands. Governing rail demand is 206.683 MPa
at a hypothetical 10 mm bearing circle and minimum washer thickness.
Changing that circle to 9 mm raises it to 277.464 MPa. Current catalog
washers supply no numeric yield; neither the circle nor uniform loaded wood
pressure is established by the nominal geometric support check. The next
corner-specific transfer check is the bearing footprint and loaded reaction
together, rather than assigning a material strength alone.

The [local combined bolt/contact response](upper-right-combined-transfer.md)
now returns 72 upper-right states using this README's frozen strong-T forces.
Its largest smooth-shank steel proxy is 267.858 MPa, below the hypothetical
92 ksi reference. Bore and tilted seat reactions are resolved under declared
local laws; rigid washers supply no bending resistance and independent bolt
poses do not establish common-host compatibility. The rail-pair calculation
now supplies a [shared-rail response](upper-right-rail-pair.md): all six cases
balance, with compatible heavy-case rail_2 tension rising to about 406 N and
peak nominal steel proxy 188.629 MPa. It retains the frozen interface wrench,
one K20 branch and sixteen original face cells. The cleat is fixed and washers
are rigid, so complete joint/washer resistance remains unassigned. The
[shared-side response](upper-right-side-pair.md) now completes all six cases:
axial shares change, while side_2 retains the 1,098.757 N peak lateral
demand. Its nominal smooth-bolt stress proxy is 0.31374 of the declared
92 ksi hypothesis. Independent rail/side poses under a fixed cleat do not
establish complete timber-block interaction. The subsequent
[washer-flexure calculation](upper-right-washer-flexure.md) balances all
48 saved end states plus one finer approximation at the governing rail
seat. The latter adds 0.016761 mm head-center closure relative to the
rigid washer. Its edge stress changes substantially between approximations
and leaves a nonzero free-edge traction residual; no washer resistance
or hardware replacement is inferred from that unstable stress proxy.

The [finite footprint/reaction bounds](upper-right-washer-contact-bounds.md)
extend that screen without another solve. A deliberately selected wood
pressure cap gives a 251.231 MPa local strip bound when angular reaction
redistribution is allowed; this is not a predicted physical stress. The note
also verifies the NDS standard-cut-washer detailing route and the official
ASME incorporation of B18.22.1 into B18.21.1. The different standard labels
are therefore not a blocker. Catalog dimensional conformance and complete
axial transfer retain their distinct scopes.

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
