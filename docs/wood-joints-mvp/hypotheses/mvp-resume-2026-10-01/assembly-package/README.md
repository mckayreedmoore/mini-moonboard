# Conditional assembly, transport and procurement package

This package reconciles the simpler wood-joint geometry originally supplied
at `b5a044e7` with the isolated two-corner 4×6 proposal and the parent’s
integrated joint batch at `d7a21856`. It preserves the reviewed
panel outlines, 66 purchased Hillman 42605 screws, 24 connector identities and
12 starting frame-bolt arrangements. The proposal changes four top-side bolts
to 5/16 inch and four top-rail grips to 177.8 mm. It does not change the
selected angle-frame candidate or authorize physical work. Main owns the
integrated mechanics and final MVP result; this packet supplies conditional
operations and reconciled quantities, not additional release requirements.

The current analytical mechanics bridge is
`../upper-corner-screw-layout/frame-250-attempt02/`, with all 88 independent
candidate bolt clearances included in its twelve zero/nominal states.
Comparison SHA-256 is
`bea6cbc330af3cdb20499d774a8f6bb24481d687c3150adb01ede18e4c1d50ca`;
response SHA-256 is
`0625196497b0dbc7b297724d7b9947f7c7c61bb282cd4d9681705629302c76c7`.
Nominal seating is bounded and nonunique; the four continuous knee bolts
and twelve retained bolts retain zero modeled clearance. The owner-authorized
[four-upper-screw overlay](../upper-corner-screw-layout/shop-addendum.md)
changes panel stations and two receiver identities, with the 66-screw count
preserved. Member and structural-bolt geometry, all family dimensions and
modeled mass 224.9499553141194 kg are unchanged. Saved old holes remain;
the overlay is not physical drilling authority.

Read this dimensional/operation package with that overlay and the
[parent working model summary](../README.md#current-analytical-working-model-for-the-mvp-goal).
The [panel material/placement check](../upper-corner-screw-layout/panel-material-fidelity.md)
also distinguishes the three-sheet width nesting from the model's assumed
grain direction. The sheet counts do not establish matching response axes.
The previous `two-receiver-frame-attempt03/` and six-joint
`all-outer-corner-frame-attempt01/` bridges remain history. Frozen assembly
reconciliation and nominal length-fit outputs are preserved; their geometry
scopes do not establish loaded fit or transfer an access or whole-joint pass.
Current central-seat forces come from the linked fresh component replay;
historical force-dependent purchasing calculations retain their own labels.

The bounded [reconciliation producer](reconcile.py) consumes saved geometry
and inventory records without a CAD rebuild or frame solve. Local raw results
and their input hashes are kept under `rawlocal/`; they are not published
evidence links. The mass basis is analytical, and Actual/Disposition cells
remain blank until observed.

## Parts and hardware

| Scope | Transport parts | Bolts | Nuts | Separate washers | Hillman screws |
| --- | ---: | ---: | ---: | ---: | ---: |
| Original frame timbers | 20 | — | — | — | — |
| Connector blocks | 24 | 92 | 92 | 184 | — |
| Retained starting frame stacks | — | 12 | 12 | 24 | — |
| Panels and kickers | 6 | — | — | — | 66 |
| **Total** | **50** | **104** | **104** | **208** | **66** |

There are 44 timber blanks and six plywood bodies, not 50 timber blanks.
The 144 former SDS attachments are absent from this development BOM. Hold
T-nuts, LEDs, wires and accessory mass are separate from structural stacks.
Transport requires individual members; no glued or permanently connected
subassembly is assumed.

| Diameter / duty | Bolts and nuts | Washers |
| --- | ---: | ---: |
| Candidate 1/4 inch | 88 each | 176 |
| Proposed top-side 5/16 inch | 4 each | 8 |
| Retained front/rear 3/8 inch | 8 each | 16 |
| Retained leg 1/2 inch | 4 each | 8 |
| **Total** | **104 each** | **208** |

The [earlier coverage](../../../current-hardware-coverage.md) supplies exact
axis IDs and catalog leads; the [top-corner packet](../top-corner-hardware/README.md)
supplies the proposal overrides. Neither modeled shaft length nor occupied
bore diameter is a purchase length or drill instruction.

| Working candidate family | Count | Modeled wood grip / bolt length, mm | Conditional catalog length route |
| --- | ---: | --- | --- |
| Ordinary 1/4-inch stacks | 44 | 127 / 152.4 | 6 inch |
| Unchanged side 1/4-inch stacks | 12 | 177.8 / 203.2 | 8 inch |
| Proposed top rail 1/4-inch stacks | 4 | 177.8 / 203.2 proposal envelope | 8 inch |
| Proposed top side 5/16-inch stacks | 4 | 177.8 / 203.2 proposal envelope | 8 inch |
| Outer-post stacks | 4 | 76.2 / 101.6 | 4 inch |
| Center-post stacks | 4 | 127 / 139.217 | 5.75-inch class; named 6-inch alternative |
| Center-principal stacks | 4 | 122 / 139.217 | 5.5 inch |
| Center-post/header stacks | 4 | 167 / 179.217 | 7.5 inch |
| Center-principal/header stacks | 4 | 172.8 / 190.017 | 7.5 inch |
| Knee inner-header stacks | 4 | 177.1 / 202.5 | 7.75-inch class; named 8-inch alternative |
| Continuous knee-side stacks | 4 | 215.9 / 241.3 | 9.25-inch class; unresolved 9.5-inch lead |

The 6-inch ordinary family loses four top-rail axes. The former 16-axis
quarter-inch side family loses four top-side axes. For the Lawson 8-inch
quarter-inch alternative, **12 side + four proposed top rail + four knee
inner-header = 20 bolts**, fitting one 25-piece pack with five surplus. Do
not add separate top-rail and knee packs to the same pooled scenario.

## Individual-member transport sizes and masses

All 50 bodies remain separate transport identities. Dimensions below are
finished oriented envelopes, rounded to 0.01 mm; they are not stock blanks
or machining instructions. Wood uses grain × section-q × section-r, except
the proposed top cleats use grain × X × T; panels use X × T × N.
Mass uses each recorded finished volume at a uniform **600 kg/m³ planning
density**, rounded to 0.001 kg. Delivered material density is unmeasured.
Bolts, nuts, washers, screws, mounted holds, T-nuts, lights and wires are
excluded from these individual wood/panel masses.

| Body | Finished envelope, mm | Planning mass, kg |
| --- | --- | ---: |
| `base_floor_left` | 1815.65 × 139.70 × 38.10 | 5.735 |
| `base_floor_right` | 1815.65 × 139.70 × 38.10 | 5.735 |
| `base_header` | 2435.23 × 38.10 × 139.70 | 7.762 |
| `base_post_center_left` | 238.90 × 139.70 × 38.10 | 0.760 |
| `base_post_center_right` | 238.90 × 139.70 × 38.10 | 0.760 |
| `base_post_outer_left` | 238.90 × 139.70 × 38.10 | 0.756 |
| `base_post_outer_right` | 238.90 × 139.70 × 38.10 | 0.756 |
| `base_principal_center_left` | 2506.17 × 139.70 × 38.10 | 7.839 |
| `base_principal_center_right` | 2506.17 × 139.70 × 38.10 | 7.839 |
| `base_rail_bottom_left` | 1041.25 × 38.10 × 139.70 | 3.190 |
| `base_rail_bottom_right` | 1038.08 × 38.10 × 139.70 | 3.180 |
| `base_rail_service_lower_left` | 1041.25 × 38.10 × 139.70 | 3.190 |
| `base_rail_service_lower_right` | 1038.08 × 38.10 × 139.70 | 3.180 |
| `base_rail_service_upper_left` | 1041.25 × 38.10 × 139.70 | 3.190 |
| `base_rail_service_upper_right` | 1038.08 × 38.10 × 139.70 | 3.180 |
| `base_rail_top` | 2257.43 × 38.10 × 139.70 | 7.200 |
| `base_side_left` | 2539.77 × 139.70 × 88.90 | 18.600 |
| `base_side_right` | 2539.77 × 139.70 × 88.90 | 18.600 |
| `lumber_leg_left` | 1989.03 × 139.70 × 88.90 | 13.039 |
| `lumber_leg_right` | 1989.03 × 139.70 × 88.90 | 13.039 |
| `bottom_center_left_cleat` | 119.70 × 88.90 × 88.90 | 0.558 |
| `bottom_center_right_cleat` | 119.70 × 88.90 × 88.90 | 0.558 |
| `bottom_outer_left_cleat` | 119.70 × 88.90 × 88.90 | 0.558 |
| `bottom_outer_right_cleat` | 119.70 × 88.90 × 88.90 | 0.558 |
| `center_post_cleat_left` | 128.90 × 88.90 × 88.90 | 0.600 |
| `center_post_cleat_right` | 128.90 × 88.90 × 88.90 | 0.600 |
| `center_principal_cleat_left` | 134.70 × 139.70 × 83.90 | 0.936 |
| `center_principal_cleat_right` | 134.70 × 139.70 × 83.90 | 0.936 |
| `knee_outer_left_inner_frame_block` | 139.00 × 133.35 × 88.90 | 0.977 |
| `knee_outer_left_spine` | 276.30 × 139.70 × 38.10 | 0.878 |
| `knee_outer_right_inner_frame_block` | 139.00 × 133.35 × 88.90 | 0.977 |
| `knee_outer_right_spine` | 276.30 × 139.70 × 38.10 | 0.878 |
| `left_service_inner_lower_cleat` | 119.70 × 88.90 × 88.90 | 0.558 |
| `left_service_inner_upper_cleat` | 119.70 × 88.90 × 88.90 | 0.558 |
| `left_service_outer_lower_cleat` | 119.70 × 88.90 × 88.90 | 0.558 |
| `left_service_outer_upper_cleat` | 119.70 × 88.90 × 88.90 | 0.558 |
| `top_center_left_cleat` | 119.70 × 88.90 × 88.90 | 0.558 |
| `top_center_right_cleat` | 119.70 × 88.90 × 88.90 | 0.558 |
| `top_outer_left_cleat` | 119.70 × 88.90 × 139.70 | 0.878 |
| `top_outer_right_cleat` | 119.70 × 88.90 × 139.70 | 0.878 |
| `wj04_lower_full_stock_cleat` | 119.70 × 88.90 × 88.90 | 0.558 |
| `wj04_upper_g7_crosscut_full_stock_cleat` | 86.90 × 88.90 × 88.90 | 0.403 |
| `wj06_outer_lower_right_cleat` | 119.70 × 88.90 × 88.90 | 0.558 |
| `wj06_outer_upper_right_cleat` | 119.70 × 88.90 × 88.90 | 0.558 |
| `kicker_left` | 1217.61 × 223.86 × 192.04 | 3.688 |
| `kicker_right` | 1217.61 × 223.86 × 192.04 | 3.688 |
| `main_lower_left` | 1217.61 × 1219.20 × 18.26 | 16.157 |
| `main_lower_right` | 1217.61 × 1219.20 × 18.26 | 16.173 |
| `main_upper_left` | 1217.61 × 1219.20 × 18.26 | 16.178 |
| `main_upper_right` | 1217.61 × 1219.20 × 18.26 | 16.188 |

The 50-body subtotal is **215.797379 kg**.
The saved frame model instead records **224.949955 kg** including modeled
hardware, plus a separate **25 kg equipment allowance** for its load case.
Its corner mass correction uses 500 kg/m³. Recomputing the same changed
wood volumes at 600 kg/m³ adds 0.635014 kg to the original body inventory,
whereas the saved frame correction is 0.529179 kg: **0.105836 kg difference**.
The transport subtotal and frame total therefore have different scopes and
correction conventions; they are not equal-weight validation targets.
The original modeled hardware groups total 9.258412 kg, before updated
top-bolt envelopes or delivered part identity. No actual carried accessory
weight is inferred from the 25 kg allowance.

Panel outline dimensions come from the source inventory; panel finished
volumes come from the later weight inventory. The source inventory’s uncut
panel shape hash is not a hash of the later finished volume. Neither record
establishes the received sheet or its layup.

## Forward assembly and reverse removal

This is an operation hypothesis for the stated geometry and recorded fit
assumptions. It preserves the [current operation order](../../../transport-operations.md)
and [retained wire dependency](../../../current-retained-wire-sequence.md).
Do not support an assembly by relying on the analytical no-slip floor
condition. Independent support of every member being disconnected remains
part of each transition; no temporary support fixture is modeled here.

| Step | Forward operation | Reverse operation and captured parts |
| ---: | --- | --- |
| 1 | Stage the 20 separate frame timbers, 24 named blocks, six panels and axis-labeled hardware. Support and align the frame members; install the 12 retained stacks while their receiver faces are open. | After all connector stacks are released, keep each member independently supported; remove the 12 retained stacks and separate the original timbers one at a time. Preserve each head washer, nut washer and nut with its named axis. |
| 2 | Place each connector against its named receivers; install the 92 candidate stacks before panels close the work area. Hand-start compatible nuts without pulling misaligned wood together. Complete and capture one named stack at a time. | With adjoining members supported, remove nuts and nut washers, withdraw bolts with their head washers, then separate each block. Use the four captured-nut paths below instead of the intersecting direct slides. |
| 3 | At each proposed top corner, install the two 5/16-inch side bolts from side host into cleat, then two 1/4-inch rail bolts from rail into cleat. Side order is 88.9 + 88.9 mm; rail order is 38.1 + 139.7 mm. | At each corner, remove the two rail nuts/washers and withdraw both rail bolts headward, then release the two side stacks. Capturing both tools, turning and roughly 0.20 m shaft extraction are still conditional. |
| 4 | Install the six panels/kickers and 66 Hillman screws after receivers and edge support are reconciled. Use the owner's recorded pilot and countersink policy in the existing shop checklist; CAD occupancy is not the bit size. | Support panels and manage the intact harness first. Release 66 panel/kicker screws separately from structural bolts. Stage each lower panel before its same-side kicker under the retained sequence hypothesis. Keep each panel's hold T-nuts with that panel. |
| 5 | Feed the intact lighting harness through the passages and seat LEDs after panels are positioned. Keep all source electrical connections and routes. | Manage lights and the continuous harness before moving panels. The two named spans crossing retained leg-bolt extraction must be staged away before those four bolts move. Do not cut, splice, or assume a factory connector isolates a panel. |
| 6 | Reconcile all 104 structural stacks, 66 screw stations and 50 transport parts to the same revision. No tightening torque or preload is invented. | Inventory the same counts after separation; record actual losses, damaged parts or observed fit only when observed. |

Step 3 is the explicit top-corner substep of step 2, not eight additional
bolts. Step 5's harness staging is a prerequisite to reversing steps 4 and 1.
The within-family order is constrained by receiver/tool access; a zero-cycle
proxy graph does not prove arbitrary installation order. A full structural
move involves 104 bolt installs and 104 bolt removals; the separate panel
cycle involves 66 screw installs and 66 screw removals. Those operation
counts do not count turns, re-indexing, LED work or member handling.

### Supported extraction evidence

The [92-axis exact-component screen](../../../current-access-screen.md)
reports clear modeled shafts, heads and head washers with nuts and nut
washers removed. Four direct nut slides intersect adjacent blocks, with two
small washer intersections. Its alternate captured-nut sequence keeps the
nut/washer at the receiver while the bolt unthreads and withdraws, then moves
the captured pair transversely before a 25 mm nutward follow-on:

| Axis suffix / station | Lateral captured-pair move in global X, mm | Headward bolt travel, mm |
| --- | ---: | ---: |
| `bottom_center/clip_horizontal_bottom_left_2/rail_2` | −50.9623 | 151.368 |
| `bottom_center/clip_horizontal_bottom_right_1/rail_2` | +48.9623 | 151.368 |
| `bottom_outer/clip_horizontal_bottom_left_1/rail_2` | +53.9623 | 151.368 |
| `bottom_outer/clip_horizontal_bottom_right_2/rail_2` | −55.9623 | 151.368 |

The common nutward follow-on is `(0, −16.0697, −19.1511)` mm. Reverse these
local movements for insertion only under the same thread-compatible capture
assumption. They are bounded paths, not a demonstrated reachable staging
position. The boreless nut envelope's shaft overlap is not a thread-fit pass.

The [retained twelve-stack screen](../../../current-retained-access.md)
supports source-geometry headward travel of 99.568 mm for four front bolts,
112.268 mm for four rear bolts and 200.025 mm for four leg bolts, with zero
terminal allowance. Front/rear modeled sweeps clear; all four leg sweeps
intersect `wire_010_A10_A11` or `wire_130_K10_K11`. Removing only those two
obstacles from the saved collision map clears all 24 forward/reverse
component checks. This proves which modeled spans cause the intersections;
it does not prove those spans can physically be staged or re-fed.

These access screens bind the reviewed layout before the top-corner
proposal. They provide reusable route evidence at unchanged stations, with
their recorded obstacle set; they do not qualify changed or nearby hardware
in the proposed assembled scene. The top proposal's sixteen 25.4 mm × 50 mm
straight tool approaches clear its declared wood and shaft obstacles. They
do not cover real tool turning, counterhold, installed nuts/washers/heads,
hold hardware or complete shaft travel.

## Fit facts still needed

The [catalog fit worksheet](../top-corner-hardware/assembly-fit.md) separates
bolt body end `LB`, grip gage `LG`, full-form male threads and matched nut
engagement. For the two corners, side bolts need under-head length
≥194.2507 mm, `LB` ≥158.2166 mm and full-form thread over
181.0512–190.0174 mm. Rail bolts need ≥191.4144 mm, `LB` ≥144.9070 mm
and full-form thread over 180.3908–187.6044 mm. These include the declared
three-pitch tip scenario; that allowance is not a universal installation rule.

For other families, the real fit gaps are the exact delivered body/thread
profile and matched nut engagement; center-principal and inner-header
nominal-diameter thread-bearing exceptions; the four 9.5-inch knee-side
product facts; actual nut/washer bearing and supported washer footprint;
installed tools, counterhold and extraction; and the intact harness stage.
The partial nut-seat support at `center_principal_right_2` remains a named
exception: an ideal supported-ring calculation does not establish the
actual washer's metal/contact transfer.
Synthetic wrench intersections do not establish real blockage or access.
Catalog bolt grade does not supply washer yield strength. Actual wood,
hardware and tool measurements remain unobserved, not failed by default.

## Stock, panel quantities and cost scope

The [stock envelope packet](../../current-stock-envelope-reconciliation-2026-10-01/README.md)
contains all 44 timber identities. Replace the two top-cleat 4×4 blanks with
4×6 blanks of the same 119.7 mm grain length. Thus original-section counts
become **18 2×6, ten 4×6 and sixteen 4×4 blanks**. The four existing prepared
section rips remain in their 4×6 source class. The producer re-runs the recorded nesting method with this replacement; no
stock grade or post-rip grade is assigned by nesting arithmetic. Revised
results below use first-fit decreasing, a full 3.2 mm separation kerf for
each blank, and the recorded 0, 10 or 20 mm trim at each stock end. All three
trim cases retain these counts; they do not establish an optimum or purchase
quantity. The four prepared section rips still start from 4×6 stock.

| Nominal stock options | 2×6 sticks | 4×6 sticks | 4×4 sticks | Blanks placed |
| --- | ---: | ---: | ---: | ---: |
| 8 ft | 6 | 3 | 1 | 39/44 |
| 10 ft | 8 | 4 | 1 | 44/44 |
| 12 ft | 6 | 4 | 1 | 44/44 |
| 16 ft | 5 | 3 | 1 | 44/44 |
| 8, 10, 12, 16 ft | 9 | 4 | 1 | 44/44 |

The 8-ft-only result still leaves `base_header`, both center principals and
both side members unplaced. It adds one 4×6 stick relative to the old
4×4-top-cleat result under this heuristic. The complete larger/mixed cases
retain their former stick counts. Revised blank-length sums are 21,135.370 mm
for 18 2×6 blanks, 9,985.178 mm for ten 4×6 blanks, and 1,900.800 mm for
sixteen 4×4 blanks. These are sums within stock classes, not cost or volume
yield. Plywood is separate.

Four main plywood bodies have 1217.6125 × 1219.2 × 18.25625 mm source
envelopes; two kicker bodies have 1217.6125 × 277 × 18.25625 mm envelopes.
Six bodies are not six purchased sheets. The owner identified the purchased
Roseburg AC fir product; binding its actual sheet group and strength-axis
placement to these body envelopes remains open, independently of sheet counts.

For rectangular sheet envelopes, a bounded zero-end-trim layout is possible
without importing the selected candidate's plywood packet:

| Geometric sheet option | Sheet count | Current-envelope placement | Limitation |
| --- | ---: | --- | --- |
| 1219.2 × 2438.4 mm (4×8) | Three | Two sheets each give two main blanks across the 2438.4 mm direction; a half of the third sheet gives both kickers. | Two main widths plus a 3.175 mm kerf equal 2438.4 mm exactly: zero length margin. A 3.2 mm kerf exceeds that length by 0.025 mm. |
| 1219.2 × 1219.2 mm (4×4) | Five | One main blank per sheet on four sheets; both kickers on the fifth. | Two kicker depths plus a 3.175 mm separation kerf require 557.175 mm. Sheet section, tolerances and cleanup remain unassigned. |

These counts cover the six current source envelopes. Their total area
exceeds two 4×8 or four 4×4 sheets, so the counts are minimums for these
full rectangular envelopes under the stated layout. They are conditional
geometry quantities, not compatible sheet products, purchased stock or a
released cutting plan. A nonzero trim/cleanup allowance or a different
delivered sheet/kerf can change the 4×8 result. The panel through-hole and
service machining remains the current candidate's work, not inherited shop
acceptance.

Costs use the recorded September 25 and October 1 listing observations,
not current quotes. Keep quantities and pack surplus visible; tax, freight,
availability and material compatibility are not priced. The [stock price
screen](../../current-stock-package-cost-2026-10-01/source-screen.md) records
MBF rates, not per-stick amounts, and no fully compatible lumber offer.
It also has no verified 2×6×16 rate. The recorded $49 plywood sheet and
$44.10-at-48 tier are comparison listings, not a selected current panel
item; the bulk tier cannot be used for a small sheet count.
Three sheets at the recorded $49 comparison would be $147, separately from
material eligibility, freight and tax. The 4×4 comparable listing has no
numeric price. Neither observation completes the current panel cost.

| Conditional hardware route | Required / listed purchased quantity | Dated listing amount or unresolved price |
| --- | --- | --- |
| Ordinary 6-inch K.L. Jack `25C600HCS5Z` | 44 / 100 bolts; 56 surplus | $82.14 per box |
| Shared quarter-inch Lawson `FA21103`, 8 inch | 20 / 25 bolts; five surplus | Unpriced; one pack for all three duties |
| Top-side Bolt Depot `28650`, Grade 8 | Four / four bolts | $12.20 |
| Top-side `2583` nuts and `2995` washers | Four nuts and eight washers, bought individually | $0.32 + $0.48 |
| Top-rail `2569` nuts and `2994` washers | Four nuts and eight washers, bought individually | $0.28 + $0.48 |
| Center-principal K.L. Jack `25C550HCS5Z` | Four / 100 bolts; 96 surplus | $30.59 per box |
| Two center-header families, HiStrength `104-049` | Eight / eight 7.5-inch bolts | $20.32 |
| Remaining quarter-inch nut/washer pooling scenario | 84 / 100 nuts; 168 / 200 washers; 16 / 32 surplus | $4.71 + 2 × $3.47; common fit remains conditional |
| Outer-post 4-inch bolts | Four / listed 100-piece box; 96 surplus | Reliable price absent |
| Center-post 6-inch alternative | Four needed; listed pack is 50 | $1.23 displayed per item; payable pack basis unresolved |
| Continuous knee-side 9.5-inch lead | Four needed | Product specification, package and price unresolved |
| Twelve retained bolt stacks | Four 1/2-inch and eight 3/8-inch bolts/nuts; eight and sixteen washers | Current package cost not established |
| Panel/kicker screws | 66 purchased Hillman 42605 screws | Purchased policy retained; present acquisition cost not assigned |

In the explicitly hypothetical pooled route above, the priced hardware
terms sum to **$158.46**, plus the unpriced Lawson pack, outer-post,
center-post, knee-side and retained hardware terms. This is a partial listing
sum, not a complete hardware total or purchasing choice. Switching the four
top rails to the recorded Motion each-price adds $13.92, giving $172.38
of priced terms; remaining Lawson demand is 16 in its 25-pack, with nine
surplus. Do not also buy a separate 25-pack for the four top rails.
Exact matched nuts/washers for the pooled remainder are conditional; the
earlier family-specific fit limitations still apply.

Lumber, a compatible plywood item/stock allowance, pads, hold hardware,
lighting/service parts, consumables, freight and tax prevent a complete
cash total. Keep owned/purchased items distinct from new acquisition cost.
No absent price is zero, and historical 28-block/104-candidate cost totals
do not enter this package.

The later [October 2 catalog update](catalog-costs.md) supplies $31.12 of
retained bolts/nuts/washers at displayed piece prices. It is a separate
increment to the historical $158.46 partial sum, giving $189.58 of priced
terms if added once, before freight/tax. Lawson still requires login for
price; the outer-post merchant displays remain conflicting. The conditional
ordinary/center-post 6-inch pooling scenario uses 48 of the same 100-pack,
leaving 52 spare if the exact SKU/profile meets the hardware worksheet.
No fit or product selection follows from those prices or quantities.

## Validation and limits

The implementation worker and parent independently ran the bounded
`--verify` replay against the local frozen inputs. All **164 source pins**
match, all seven ignored output files reproduce byte-for-byte, and the
inventory contains **50 unique bodies and 170 unique fastener stations**:
92 candidate bolts, 12 retained bolts and 66 separate panel/kicker screws.
The body masses sum exactly to the emitted 215.79737871151428 kg subtotal.
The 15 revised stock scenarios reconcile all requested identities. Local
Markdown links and the dated hardware-price arithmetic were checked.

```sh
python3 -B docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/assembly-package/reconcile.py --verify
```

This reads the existing saved records and runs the small stock-nesting
helper; it does not regenerate upstream geometry or mechanics. `--write`
emits the ignored local outputs from the same inputs. If a required local
source is unavailable or a pin differs, the producer reports the exact
missing/mismatched source instead of inventing a quantity or mass.

### Corrected retained catalog labels

The frozen original producer joins retained `catalog_references` strings as
individual characters. Its quantities and published labels remain valid.
[reconcile_catalog_labels.py](reconcile_catalog_labels.py) normalizes that
field to a one-element list before both joins in the unchanged, hash-bound
legacy builder. Corrected exports are separate in
`rawlocal/catalog-labels-attempt01/`; all seven original files remain preserved.

Only three retained family labels in JSON/CSV and twelve retained axis labels
in CSV change. All other fields match, including counts, axes, dimensions,
masses and the 164 source bindings. The four body/stock outputs remain
byte-identical. The CSV retains 15 rows including the separate Hillman family,
and 170 axis rows including the 66 separate Hillman screws. This corrects
formatting; it does not select hardware or change mechanics or prices.

```sh
python3 -B docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/assembly-package/reconcile_catalog_labels.py --write
```

| Corrected artifact | SHA-256 |
| --- | --- |
| `reconcile_catalog_labels.py` | `cce89de7c9b28f16266c194b459c6ac8d790053329d7952c8510743c5c3db2a2` |
| `rawlocal/catalog-labels-attempt01/reconciled-assembly.json` | `d79bedb1edbc0d4cbde095e77fdebc99bbcb3348ee5cca1866eb80737a732590` |
| `rawlocal/catalog-labels-attempt01/hardware-families.csv` | `4b37302b9fb8ff711270da50a361b25a26e0fa1e670e2e788684ca4a72d5bed9` |
| `rawlocal/catalog-labels-attempt01/hardware-axes.csv` | `d6415c095f75c31a210c40e7dd8d8d4a1d0942ffe2095fa19a25c1391eb3d924` |

The existing producer and original export hashes below remain unchanged.

| Artifact | SHA-256 |
| --- | --- |
| Frozen `corner-frame-attempt01/model.json` | `d17dadd7c999e4a1634f53226cf63e131f547cd9cf5d46d87d75c935f2dc807e` |
| Current `two-receiver-frame-attempt03/comparison.json` | `0ff0dfc00c112a906910641141fd242f4a58295aa3324ca569132a3fa2d388a5` |
| Current `two-receiver-frame-attempt03/response.npz` | `774c3bbddf8061f6b9d1cfdd5f22efbeb1025bd57431a249912ae8e60a731f52` |
| Preserved `all-outer-corner-frame-attempt01/comparison.json` | `ec69b49c821a56fdde76d94148405f9f743e4f72add17c89d35af512be76f6a3` |
| Preserved `all-outer-corner-frame-attempt01/response.npz` | `aa70480aa18c33bb1cbd7d3a53ff582a0c7a90c93487f92721619474ec251901` |
| `top-corner-correction/proposal.json` | `5932768c7a7d91535f69a90787b32222eb4d165ac6353d3e2ed4daf9e248e2b2` |
| Top catalog `hardware-inputs.json` | `a2110d7580621dee92017403345f21c458729612547ac1f7b2eb8068d0c723c7` |
| `reconcile.py` | `6b698475a02b172857f7891efd2347e8f7c88415315303a9a30b51c84ba5fd74` |
| `rawlocal/reconciled-assembly.json` | `2bb4e95fbd2a7ec158d24bc12860e0961000fdb9f9af7ffd8504ef966b2aee87` |
| `rawlocal/bodies.csv` | `9e54e5da262074e98e84e2c846e37d81e905791d7f619b3253142f4dd37f14bc` |
| `rawlocal/stock-scenarios.json` | `f10b683f0e23cf303ea9163468fa929f9a5850f649a54cf28752b1ebacf26cf8` |

The saved scene supplies analytical dimensions and masses, not measurements
of a fabricated frame. No native solve, CAD rebuild, review loop, software
test suite, shared authority change, staging or commit is part of this task.
Parent owns joint/member acceptance and the integrated six-case result.
Formal product qualification, actual assembly/transport observations and
physical-release flags remain unchanged.
