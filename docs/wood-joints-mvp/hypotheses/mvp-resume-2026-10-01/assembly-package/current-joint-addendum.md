# Current joints and the conditional assembly package

Updated October 2, 2026. Read this addendum with the frozen
[shop guide](shop-guide.md), [assembly reconciliation](README.md),
[hardware engagement specification](hardware-engagement.md) and
[nominal bolt-length screen](hardware-length-fit.md). It bridges their
dimensional and operation records to the current four-upper-screw frame and
completed left/right rigid-cleat calculations. It changes no source solids,
hardware selection, authority or physical-release status.

The current force source is
`../upper-corner-screw-layout/operators-attempt02/` and
`../upper-corner-screw-layout/frame-250-attempt02/`. The completed
[upper-right block](../upper-corner-screw-layout/upper-right-block.md) and
[upper-left block](../upper-corner-screw-layout/upper-left-block.md) each
retain four bolts, thirty-two face cells, six nominal-clearance cases and
one compatible pose per host against a common rigid cleat. Each includes
its exact current mapped cleat weight once. Neither replaces the full-frame
force source, establishes elastic cleat compatibility or releases a joint.

## Four changed screw stations

Use the [66-axis shop overlay](../upper-corner-screw-layout/shop-addendum.md)
for the current analytical screw schedule. Exactly four upper-panel axes
move **+65.95 mm in panel T**, a global translation
`(0,42.391842858827275,50.5206310236966)` mm. Their directions remain
`(0,-0.7660444431189781,0.6427876096865394)`. The other sixty-two axes
retain their front datum, direction, panel and receiver.

All four moved front datums have Y=1537.324502383678 mm and
Z=2130.1649091349177 mm. These are analytical coordinates, not physical
drilling instructions.

| Screw axis | Panel | X after, global mm | Receiver before → after |
| --- | --- | ---: | --- |
| `round_panel_upper_left_rim_4` | `main_upper_left` | -1200.15 | `base_side_left` → same |
| `round_panel_upper_right_rim_4` | `main_upper_right` | 1196.975 | `base_side_right` → same |
| `round_panel_upper_left_center_4` | `main_upper_left` | -70 | `base_principal_center_left` → `base_rail_top` |
| `round_panel_upper_right_center_4` | `main_upper_right` | 70 | `base_principal_center_right` → `base_rail_top` |

The **two receiver changes belong to panel screws**, not structural bolt
stacks. Both moved center screws now transmit into the top rail. The rim
screws remain in their same-side members. The saved geometry check finds
nominal panel/receiver intersection at each new station, 45.24375 mm
projected receiver overlap and 19.05 mm nearest stock-edge clearance.
There are no conservative installed screw/bolt-axis overlap candidates in
that check. These cylinder and stock-envelope facts establish neither
delivered heads/tools nor screw resistance.

Saved old bores remain in the source solids. Do not combine the old and
new moved stations as eight screws or use their coexistence as a cutting
schedule. The previous receiver inventory's 58 retained/eight moved count
and this overlay's 62 retained/four moved count compare different successive
layouts; both retain sixty-six screws. The four earlier center-kicker moves
still enter the center posts. Lower-panel and kicker stations do not change
in this upper-row overlay.

## Inventory and dimensional fit retained

| Item | Current quantity | Effect of this bridge |
| --- | ---: | --- |
| Frame timber bodies / connector blocks | 20 / 24 | Same separate member identities and outlines. |
| Timber blanks | 44 | Same 18 nominal 2×6, 10 nominal 4×6 and 16 nominal 4×4 source classes. |
| Plywood transport bodies | 6 | Four main panels and two whole kickers; not six purchased sheets. |
| Candidate / retained frame bolts | 92 / 12 | Same 104 structural axes and receiver orders. |
| Structural nuts / separate washers | 104 / 208 | One nut and two exterior washers per stack. |
| Hillman 42605 panel/kicker screws | 66 | 48 main-panel screws plus nine on each kicker. |

Candidate diameter quantities remain eighty-eight 1/4-inch and four
5/16-inch bolts; retained quantities remain eight 3/8-inch and four 1/2-inch
bolts. The four 5/16-inch bolts and four corrected 1/4-inch rail bolts are
already included in the ninety-two candidate stacks. There is no additional
top-corner pack in the inventory. The former 144 SDS attachments and twenty-four
ML24Z angles do not belong to this wood-block BOM.

The isolated two-corner 4×6 correction is already part of the assembly
package. Each top cleat remains solid 4×6 with 119.7 mm grain length.
Structural axes, ordered wood lengths, bore envelopes, nominal shaft lengths
and matched stack dimensions do not change with the four Hillman moves or
the new local bolt-force allocations. All eleven candidate and three
retained family specifications remain dimensional inputs, not observations
of received hardware.

| Both top corners | Count | Ordered wood grip, mm | Nominal length route | Minimum under-head length, mm | Minimum body end `LB`, mm | Required full-form male-thread window, mm |
| --- | ---: | --- | --- | ---: | ---: | --- |
| Rail bolts, 1/4-20 | 4 | 38.1 rail + 139.7 cleat = 177.8 | 8 in | 191.4144 | 144.9070 | 180.3908–187.6044 |
| Side bolts, 5/16-18 | 4 | 88.9 side + 88.9 cleat = 177.8 | 8 in | 194.2507 | 158.2166 | 181.0512–190.0174 |

These reuse the [top stack fit](../top-corner-hardware/assembly-fit.md) and
hardware engagement worksheet's catalog washer/nut bounds and declared
three-pitch projection option. The option is not a new structural criterion.
Smooth shank, runout, nut active thread, mating class and washer dimensions
still require the stated part profile; nominal eight-inch length alone
does not establish them. Named Grade 8 side and Grade 5 rail purchase routes
remain conditional. The mechanics' hypothetical 92 ksi bolt comparison
does not select a grade or assign washer strength.

All fifty transport identities, finished member envelopes, stock-nesting
scenarios and their quantity/cost basis remain in the assembly reconciliation.
Its 600 kg/m³ body-planning subtotal of 215.797379 kg remains distinct from
the unchanged 224.9499553141194 kg analytical frame mass and separate 25 kg
equipment allowance. The four screw moves do not alter those recorded
geometry/mass scopes or establish an actual carried weight. Unavailable
prices remain unavailable; the new joint responses add no purchase lines.

## What the nominal length receipt still establishes

The completed twelve-route added-occupancy screen remains valid for its
pinned obstacle scene and unchanged axes/endpoints. It found no overlap
or undecided pair: 48,190 positive conservative box separations and two
clear exact STEP intersections among 48,192 pairs. The two exact knee-tip
checks each retain 18.157582 mm clearance to the same-side bottom rail.

| Proposed route | Count | Proposed nominal length | Added tip / travel, mm | Recorded proposed headward travel, mm |
| --- | ---: | --- | ---: | ---: |
| Center post | 4 | 6 in / 152.4 mm | 13.1826 | 150.749 |
| Center principal/header | 4 | 8 in / 203.2 mm | 13.1826 | 201.549 |
| Inner knee/header | 4 | 8 in / 203.2 mm | 0.7 | 201.549 |

The screen includes the same fifty member STEPs and four corrected top
replacement STEPs, plus the recorded installed hardware, wires and other
enclosures. It tests the added tips and additional headward shaft/head/washer
movement only. Its profile arithmetic and unchanged-geometry pair results
remain reusable; it does not select these proposed lengths or establish a
complete nut/tool/thread sequence.

Its sixty-six screw enclosures precede the four-upper-axis relocation.
The new overlay's installed screw/bolt-axis separation does not evaluate
those four relocated screws against the moving length-extension queries.
Do not relabel the older receipt as a complete current-overlay moving-path
screen. This scope distinction does not discard its unchanged pairs,
restart the completed check or impose a new blanket prerequisite.

## Affected operations

The [shop guide's sequence](shop-guide.md#forward-assembly) remains the
conditional operation hypothesis. Support individual members during every
open connection; no-slip floor support is an analytical load assumption,
not an assembly fixture.

| Operation | Current instruction and actual effect |
| --- | --- |
| Stage stock and structural stacks | Use the same forty-four timber blanks, six panels and axis-labeled 104 stacks. No new member or bolt family follows from the upper-row move. |
| Retained and candidate bolt installation | Retain the twelve retained stacks and ninety-two candidate stacks before panel closure. At each top corner install two side bolts, then two rail bolts, with the receiver orders above. No bolt coordinate or stack-order change is introduced here. |
| Upper-panel station layout | Read the four moved rows from the current overlay; two center receivers are now the top rail. Preserve the other sixty-two stations. The overlay does not authorize drilling either saved old or new bores. |
| Purchased panel-screw operation | Retain Hillman 42605, #10 × 2-1/2 in, #2 Phillips. Keep the owner-selected 1/8 in lead pilot through plywood into its named receiver and 3/8 in face countersink, using the recorded Kobalt 80277 #10 insert. The 4.1402 mm CAD cylinder is not the pilot size. |
| Panel and harness removal | Preserve intact-harness staging and release the same sixty-six screws. Stage the lower panel before its same-side kicker. Moving four upper screws does not remove the two named retained leg-bolt wire dependencies. |
| Top-corner bolt removal | Support members; remove rail nuts/washer pairs and withdraw rail bolts headward, then release side stacks. Retain roughly 0.20 m nominal shaft travel and the existing straight-approach scope; no turning/counterhold or full extraction observation is added. |
| Bottom captured-nut paths and member transport | Keep the four named captured-pair routes and twelve retained extraction records. Inventory the same fifty separate bodies and 104 complete stacks; no connected transport subassembly is introduced. |

No tightening torque, preload or new tooling is specified. The purchased
Hillman and owner-selected pilot policy remain separate from generic screw
resistance references. Twenty-screw-per-panel and grain-direction sensitivity
packets do not replace this sixty-six-axis operation schedule.

## Force results and blank observations

Use the current [joint register](../upper-corner-screw-layout/joint-register.md),
[right block](../upper-corner-screw-layout/upper-right-block.md),
[left block](../upper-corner-screw-layout/upper-left-block.md) and
[left component replay](../upper-corner-screw-layout/upper-left-block-components.md)
for current demands and their limits. Historical force ratios in the isolated
top-corner fit worksheet or old assembly source remain labeled history;
reusing their dimensions does not transfer those ratios.

Both current top blocks have finite balanced six-case rigid-cleat responses.
Their conditional lateral, mean-seat and smooth-steel diagnostics do not
establish complete oblique-group/splitting or washer-metal acceptance.
Panel attachment remains on its recorded reference HOLD. The current
central-seat force replay likewise does not prove actual nut/washer transfer.
This addendum neither adds a release gate nor closes an existing open claim.

Keep Actual and Disposition cells blank until the item is observed. CAD,
catalog labels and mechanics convergence are not observations. An
incompatible delivered part or missing intended receiver stops its affected
operation under the existing guide; no physical fit, cut, hole, floor or
climber rating is asserted.

| Record tied to this bridge | Actual | Disposition |
| --- | --- | --- |
| Delivered bolt body/thread and matched nut/washer profile | | |
| Four upper stations and intended receiver identity | | |
| Actual Hillman pilot/countersink/drive trial | | |
| Actual tool turning/counterhold and shaft movement | | |
| Actual harness staging and individual-member separation | | |

## Engineering receipts

The addendum was prepared from saved records only, with no new producer,
mechanics calculation, CAD/native/frame run, software test, review loop,
source/authority change, staging or commit. Paths below are relative to
`mvp-resume-2026-10-01/`; raw outputs remain ignored. Hashes identify the
frozen inputs, not physical observations.

| Receipt | SHA256 |
| --- | --- |
| `upper-corner-screw-layout/operators-attempt02/operators.npz` | `c9483639c69c0696b29f3fd69522e6c9a8e673aa7ce82277788103b14c955ba3` |
| `upper-corner-screw-layout/operators-attempt02/model.json` | `b5f9b87b70c4a9920372a3443a55e37dfe34351fb9ac8210b299c1360fb93626` |
| `upper-corner-screw-layout/operators-attempt02/model-inputs.json` | `e2109cabed9fcbc0a14346ef63b707abb1aed358ebf5fa126b2cba216aa771cc` |
| `upper-corner-screw-layout/frame-250-attempt02/comparison.json` | `bea6cbc330af3cdb20499d774a8f6bb24481d687c3150adb01ede18e4c1d50ca` |
| `upper-corner-screw-layout/frame-250-attempt02/response.npz` | `0625196497b0dbc7b297724d7b9947f7c7c61bb282cd4d9681705629302c76c7` |
| `upper-corner-screw-layout/rawlocal/upper-right-block/attempt01/checks.json` | `0b0b392b9e5e411173395671878c09e0be303abd4885f48d1e7e7b61d8f6a89b` |
| `upper-corner-screw-layout/rawlocal/upper-left-block/attempt01/checks.json` | `5e8c52e529f58f9276c4c67f554fa0b74a990dd501e347e59434aa244e628ed0` |
| `upper-corner-screw-layout/rawlocal/shop-axes/axes.csv` | `46406c559d1f427ad4422edf033759831a83d0ddcef4bbb871579da132853eca` |
| `upper-corner-screw-layout/rawlocal/shop-axes/receipt.json` | `535bcdaeb85ed683e66040c8042dd6c3bdea7d835ca7a9d7c510de99d6cf773d` |
| `upper-corner-screw-layout/rawlocal/attempt01/result.json` | `81b75c3fe8dced195d36d3a2a3f1ca69b1e796b89e048870a16e3864bb5a06d9` |
| `assembly-package/rawlocal/hardware-engagement/hardware-engagement.json` | `93c24fe5fb421152b0294cc35106bfb6d595b558f45e0be826406405084c111a` |
| `assembly-package/rawlocal/hardware-engagement/hardware-engagement-axes.csv` | `9fd9f2f70dbaf347bf174925f21cc3d589c2640a7b42501e3b81f4533ab42cac` |
| `assembly-package/rawlocal/hardware-length-fit/saved-source-attempt02/setup.json` | `c49b72d742e1bce7c876860ec6c8c1d50e1d1c80bab6585636387df5f08a4529` |
| `assembly-package/rawlocal/hardware-length-fit/saved-source-attempt02/result.json` | `df5271e4c65f90a620dff4630cfa5d0dec303456fa1bb4a1185fc950dbaf2aa5` |

Parent owns integration, shared staging and publication. The existing assembly,
hardware and shop files remain frozen.
