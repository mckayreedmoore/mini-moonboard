# Raised-kicker frame shop plan and hardware selection

This packet describes **`eoere-raised-kicker-screws-v1`**, extra grid off.
It composes the preceding extended-cleat records with the smaller channels,
restored right principal and two Z212 kicker screws. It also selects a
conditional purchase specification for 100 partially threaded bolts and
eight factory spacers. The viewer retains its preceding hardware lengths;
the selected lengths below are a separate shop override on the same axes.
No hardware has been purchased or inspected through this work.

The owner authorized selecting reasonable hardware and assuming a generic
drill, circular saw, pull saw and wrenches/sockets. The result supplies
nominal coordinates, hardware comparisons and practical method requirements.
It does not establish joint resistance, actual tool fit or fabrication or
climbing release. Use the maintained
[development entry](../../../../../../../../bolted-frame-development/README.md)
and [completion ledger](../../../../../../../completion-ledger.md) for the
current status. Preserve the selected baseline and frozen earlier packets.

## Hardware decision

Use zinc-plated **SAE J429 Grade 5, partially threaded, full-body hex cap
screws**, matching Grade 5 plain hex nuts and the existing USS flat washers.
The smooth-body and grip-gaging requirements are part of the specification;
“partially threaded” by itself does not guarantee either dimension.

| Bolt diameter / UNC thread × underhead length | Installed | Catalog lead | Purchase quantity |
| --- | ---: | --- | ---: |
| 3/8-16 × 2½ in | 60 | [Bolt Depot 363](https://boltdepot.com/Product-Details?product=363) | 60 |
| 3/8-16 × 3½ in | 4 | [Bolt Depot 366](https://boltdepot.com/Product-Details?product=366) | 4 |
| 3/8-16 × 4 in | 4 | [Bolt Depot 367](https://boltdepot.com/Product-Details?product=367) | 4 |
| 3/8-16 × 4½ in | 8 | [Bolt Depot 368](https://boltdepot.com/Product-Details?product=368) | 8 |
| 3/8-16 × 4¾ in | 16 | [Zoro G0341148 / N01200.037.0475](https://www.zoro.com/zoro-select-grade-5-38-16-hex-head-cap-screw-zinc-plated-steel-4-34-in-l-10-pk-n012000370475/i/G0341148/) | Two ten-packs |
| 3/8-16 × 6½ in | 4 | [Grainger 38WP04 / N01200.037.0650](https://www.grainger.com/product/Hex-Head-Cap-Screw-Steel-38WP04) | One ten-pack |
| 1/2-13 × 8½ in | 4 | [Zoro G0340956 / N01200.050.0850](https://www.zoro.com/zoro-select-grade-5-12-13-hex-head-cap-screw-zinc-plated-steel-8-12-in-l-5-pk-n012000500850/i/G0340956/) | One five-pack |

Use 96 [3/8-in nuts, 2571](https://boltdepot.com/Product-Details?product=2571),
four [1/2-in nuts, 2573](https://boltdepot.com/Product-Details?product=2573),
192 [3/8-in USS washers, 15023](https://boltdepot.com/Product-Details?product=15023)
and eight [1/2-in USS washers, 15025](https://boltdepot.com/Product-Details?product=15025).
Keep one own washer at the head and one at the nut side of every stack.

Add **eight [factory steel spacers, Bolt Depot 13731](https://boltdepot.com/Product-Details?product=13731)**:
½ in long, ¾ in OD, 13/32 in ID, zinc plated. One ten-pack supplies two
spares. Place each spacer **after the nut washer and before the nut**.
The four shared-header axes are `eoere_bolt_065`, `_066`, `_079`, `_080`;
the four dedicated corner axes are `cleat_post_bolt_left_1`, `_left_2`,
`_right_1`, `_right_2`. Only those eight receive a spacer. See the
[stack drawing](hardware-stacks.svg) and [100 exact assignments](hardware-selection.csv).

Keep the owner's [Eoere eight-hole angle](https://www.amazon.com/dp/B0C7V7VS89)
layout: **22 installed angles**, supplied by six four-packs with two spares.
The nominal model is 3½ × 3½ × 3½ in with ¼-in material and the existing
far factory-hole pairs. This is a catalog shape selection, not a rated
connector. Actual hole dimensions, minimum formed thickness, heel radius
and material resistance remain unknown. The 66 purchased Hillman 42605
screws retain their existing policy.

### Why these lengths

Twenty-four preceding stacks fell short of the retained two-tip-pitch
target at the catalog extremes. The 4¾-, 6½- and 8½-in sizes resolve that
comparison with less protrusion than the next common whole-inch sizes.
The four shared-header bolts increase from 3 to 3½ in; four dedicated
cleat/post bolts increase from 4 to 4½ in. These eight need longer smooth
bodies at their loaded timber/plate interfaces. Their spacers move the
nuts beyond the permitted grip-gaging lengths without packing washers.

For the shared headers, the far plate ends at **53.4416 mm** from under
the head with the maximum head washer. The 3½-in bolt's minimum body is
**55.626 mm**, leaving 2.1844 mm. For the cleat/post stack, both timbers
end at **78.8416 mm** and the 4½-in minimum body is **81.026 mm**, giving
the same reserve. With the specified spacer, the minimum nut-seating
comparison is **3.2512 mm**. Those are nominal timber/plate comparisons,
not delivered-part margins or woodworking tolerances.

Across all 100 selected rows, the smallest catalog two-tip-pitch margin is
**1.016 mm** and the smallest nominated smooth-body margin is **2.1844 mm**.
The nominated target is stated per row. **The other 92 rows do not establish
smooth body through every far wood surface.** Thread/runout bearing in
wood still needs its own resistance treatment; a fully threaded bolt or
the historical whole-root sensitivity is not adopted by this selection.

The [48 changed-envelope checks](hardware-envelope-review.json) cover the
32 shaft extensions, eight spacers and eight translated nuts against the
current nominal parts. Bounding boxes suffice for 36; twelve shared-header
queries use the existing ideal-angle helper. This checks added occupied
volume only. Formed-product tolerance, complete tools, insertion and
withdrawal paths remain separate.

The [ASME full-body comparison](../../bolt-window-followup-v1/inputs.json)
records B18.2.1-2012 Tables 12/13 and their limits. A
[manufacturer's table](https://www.nickel-systems.com/wp-content/uploads/2025/04/Hex-Head-Cap-Screws-Min-Body-and-Max-Grip-Gaging-Lengths-table-1.pdf)
corroborates Lb and Lg. Lb is minimum smooth body; Lg is grip-gaging length,
not the first actual full thread. The saved standard comparison is for
uncoated dimensions. Applicable edition, zinc finish, body style and actual
conformance must match the receiving specification. No supplier sorting,
thread reworking, bolt trimming or extra washer packing is assumed.

The dated fastener basket is **$148.51 before tax/shipping**, including the
listed pack spares and ten-pack of spacers. It reuses the preceding $109.93
basket, removes 24 superseded bolts, adds $55.94 of intermediate packs,
$0.52 for corner upgrades, $0.48 for header upgrades and $18.04 for spacers.
The complete scenario is `$148.51 + 6*C4 + U`: C4 is the unpriced angle
four-pack and U contains unpriced wood, services, tooling and other items.
These are October 8–9 observations and earlier retained prices, not a live
quote or stock confirmation. The 4¾-in source retains its recorded access
limit. Unknown costs are not zero; nothing has been ordered.

## Matching current records

| Use | Current record | Reused unchanged record |
| --- | --- | --- |
| All 28 wood/panel source identities | [Members](members.csv), [profiles](current_profiles.json) | Raw end geometry in [end datums](../member-end-datums.csv) |
| All 66 screw axes | [Current screw table](../../../../../../../../../fea/generated/thin-bolted-current-contact-v1/eoere-successor-v1/kicker-clearance-v1/run-v1/panel-screw-datums.csv) | Preceding 64 untouched axes retain their identities |
| Panel layout and 340 machining datums | [Current table](panel-machining.csv), [plate 1](panel-layout-1.svg) | [Plate 2](../panel-layout-2.svg) |
| Two extended cleats | [Current plate](extended-cleats.svg) | Their [raw outlines and cuts](../member-end-datums.csv) |
| Base wiring channels | [Section and principal instruction](current-channels.svg), [32 receiver/route datums](service-channel-datums.csv) | Original passage routes retained; eleven F-column arc cuts omitted |
| 100 shaft axes / 120 receiver occurrences | Current geometry, unchanged axes | [Receiver holes](../receiver-holes.csv) |
| Selected hardware / receiving observations | [100-stack purchase table](hardware-selection.csv), [stack details](hardware-stacks.svg) | Old [bolt table](../bolt-stacks.csv) is a viewer/model datum record only |
| Tool sides and reach requirements | [200 access requirements](access-requirements.csv), [100 drilling requirements](drilling-requirements.csv) | [Nominal installed sides](../access-sides.csv) |
| Stock and recesses | Same 13-stick / 150-board-foot scenario | [Nesting](../stock-nesting.json), [recess section](../rear-recess.svg), [definitions](../rear-recesses.json), [paired fixture concept](../paired-drilling-fixture.svg) |

The four raw member projections remain [1](../member-projections-1.svg),
[2](../member-projections-2.svg), [3](../member-projections-3.svg),
[4](../member-projections-4.svg). They are dimensioned projections, not
marking templates. The two kicker screws move only from Z192 to **Z212 mm**;
`round_panel_lower_right_rim_1` stays fixed. Do not use the two old Z192
holes or the preceding packet's clearance-hold caption as current instructions.

The channel table supplies board, world and current receiver L/U/V control
coordinates. Use the source's rounded route and clip its swept envelope to
the raw receiver; the vertices are not sharp finished corners or a saw path.
The common straight section has R6.35, center N8, front opening
20.427677 mm and rear depth N14.35. The right principal keeps only its
original transverse `wire_072_F1_G1` passage and all bolt bores. Do not
reintroduce the eleven filled F-column cuts. The optional extra grid,
lifted cables and its additional cuts are outside this packet.

Planning mass is **219.164616 kg** with retained viewer hardware and the
existing 25-kg accessory allowance, excluding pads. The selected longer
shafts and eight spacers add about **0.353219 kg** in a separate nominal
steel-cylinder estimate, giving approximately **219.517834 kg** combined.
These are saved-volume estimates, not measured weight or a new gravity vector.

## Mechanical change review

The [bounded review](mechanical-change-review.json) confirms that the right
principal restores **97,352.067293 mm³** of wood without removing old volume
or changing its outside envelope beyond 0.00001 mm. At the preceding
500-kg/m³ and g=9.80665 scenario, that is **0.048676 kg / 0.477349 N** added
at its recorded centroid. The preceding gross-stock Timoshenko operator
does not resolve those internal cuts, so its declared beam stiffness would
remain the same. That does not qualify the physical finished net section.
The changed domain, gravity and panel/screw coupling need current bindings
before any matching response claim.

At the two raised screws, full modeled backing and 45.24375-mm penetration
remain; the maximum wood-bore/screw gap is **3.94375 mm**. Axis distances
are **26.9 mm to post top**, 19.05 mm to post side, 65 mm to the kicker's
modeled top envelope,
and 152 mm to the lower outer screw. The latter was 132 mm. A pure equal
pair carrying an unchanged couple would have force ratio 132/152; it is
not a new panel-load result. Translating an unchanged force 20 mm adds
moment `[-20*Fy, 20*Fx, 0]`; the twelve saved trials make that limit explicit.

The corrected [AWC small-screw commentary](https://web-media.awc.org/wp-content/uploads/2021/12/17210141/AWC-2015NDS-Updates-Errata_20240109.pdf)
(PDF page 13, printed 248, C12.1.5.7) does not prescribe specific placement
requirements below ¼ in. Its prebored wood-side guidance gives generic
5D compression / 10D tension ends and 2.5D edges. At modeled D=5 mm,
the comparisons are +1.9 / −23.1 mm at the post top and +6.55 mm at the
side. All twelve preserved old-geometry post forces point downward in Z;
their signs do not qualify the new layout or Hillman end resistance.
Do not transfer SPAX properties, capacities or installation rules.

The earlier six-case numerical admission, generic head/panel/heel reference
exceedances, eight mixed-stack unknowns and null complete-joint resistances
remain within their original geometry and method limits. No new frame/native
solve or structural pass is supplied here. Panel/screw strength remedies
remain paused beyond the two owner-authorized clearance moves.
Using the selected purchase override in mechanics also requires its own
shaft, capture, contact, thread-bearing and gravity bindings; the viewer's
retained hardware response is not silently transferred to the longer bolts.

## Generic tools and practical methods

Plan around a **½-in-chuck drill**, suitable wood-cutting bits, a supported
circular saw, a pull saw, clamps/stops, and 9/16- and ¾-in wrenches/sockets.
A sharp wood chisel and a flat/round rasp are ordinary finishing additions
needed for the recess and curved front-open channels; they were not reported
as owned. Use deep six-point sockets where needed and a same-size wrench
for counterholding. Nominal nut-side usable cavity needs reach up to
28.4988 mm for 3/8-in sets and 33.7312 mm for ½-in sets. A shallow socket
that bottoms on the tip cannot seat the nut.

| Nominal wood path | ¾-in guide + ¼-in backer travel | Required usable bit projection |
| ---: | ---: | ---: |
| 38.1 mm / 1½ in | 25.4 mm | 63.5 mm / 2½ in |
| 76.2 mm / 3 in | 25.4 mm | 101.6 mm / 4 in |
| 88.9 mm / 3½ in | 25.4 mm | 114.3 mm / 4½ in |
| 127 mm / 5 in | 25.4 mm | 152.4 mm / 6 in |
| 177.8 mm / 7 in | 25.4 mm | 203.2 mm / 8 in |

Use the per-axis table for diameters and receivers. The NDS reference wood
hole ranges remain 13/32–7/16 in for 3/8-in bolts and 17/32–9/16 in for
½-in bolts. The nominal starting choices are **13/32 and 17/32 in**;
actual hole diameter and alignment must stay within the recorded range.
Factory steel holes are separate and must not be enlarged or used as
qualified drill bushings. See the preceding
[installation source and tolerance discussion](../README.md#matched-drilling-and-tolerance-disposition).

For shorter 13/32-in paths, the retained
[FISCH 013P1032150](https://www.fisch-tools.com/assets/documents/013P-Pen_Drill.pdf)
has nominal 120-mm working length, 150-mm overall length and a 10-mm shank.
It cannot reach a 152.4-mm setup. A long-flute dimensional lead is
[Champion 1200-13/32](https://www.championcuttingtool.com/item/1200/12-In-Longboy-Drills/),
9-in flute / 12-in overall. Its product page lists metal applications;
the manufacturer's [general 118-degree wood-use and operating guidance](https://www.championcuttingtool.com/wcm/connect/www.championcuttingtool.com-23970/492482fc-5b42-4bf7-9f71-8929c1f4ed1e/Twist%2BDrill%2BOperating%2BGuidelines.pdf?MOD=AJPERES)
supports considering a guided wood operation, not claiming this fixture qualified.
For the four ½-in upper bolts, select the
[Champion 1212-17/32 pattern](https://www.championcuttingtool.com/item/1212/12-In-1-2-In-Shank-Longboy-Drills/):
9-in flute, 12-in overall and **½-in reduced shank**, with explicit wood
application. A straight 17/32-in shank will not fit a ½-in chuck.
These catalog dimensions establish plausible reach, not actual projection,
guide compatibility, hole accuracy or observed equipment. Any guide flange,
chip gap or clamp stand-off increases required reach one for one.

1. Mark raw cuts on both broad and thickness faces from the same datum.
   Prefer the pull saw for the 88.9-mm solid 4×6 cuts; choose adequate free
   blade depth and clamp clearance. A rigid fence registers the saw plane.
2. For each rear recess, support the circular-saw shoe fully on coplanar
   rails and clamp the leg independently. Keep the 38.1-mm maximum depth,
   50.8-mm retained thickness and 457.2-mm 1:12 return. Full depth ends at
   L180.342661; taper ends at L637.542661. Make controlled waste-side relief
   cuts, leave finishing stock and finish with the chisel/rasp. The rough
   depth must be shallower than the finished law over the whole kerf footprint.
   A centered ⅛-in kerf consumes 0.132292 mm of taper depth allowance before
   setting/tilt errors. The 2-mm nominal pad clearance is not a cut tolerance.
3. Locate both drilling receivers at their intended seats with positive
   stops and separate clamps. Keep the registered paired-hole setup between
   holes. Use an independent compatible guide, a backer and a controlled
   breakthrough stop. Follow the bit maker's chip-clearing procedure without
   moving the registered parts. A short bit or two independently marked
   opposite-face holes does not qualify a common shaft path.
4. Lay out service cuts from the current receiver coordinates and section,
   preserving the rounded turns. Support the saw for any straight relief
   cuts wholly inside waste; finish curves and depth by hand. Do not overcut
   the envelope or create the omitted principal arcs. The nominal envelope
   has no adopted machining-error budget or qualified jig.
5. The Hillman policy stays **⅛-in lead pilot, ⅜-in face countersink and
   #2 Phillips**, including the two Z212 positions. These owner-selected bit
   sizes are not Hillman-published instructions or CAD void diameters.

The access worksheet uses a 50.8-mm axial outboard approach capsule and a
hex-corner radius plus 1.5-mm nominal wall allowance against 1,029 nominal
obstruction bounds, including selected extensions, shifted nuts and spacers.
Forty sides have a positive conservative separation; 160 need finer tool
geometry. **Those 160 are unresolved screens, not observed clashes.** The
screen does not include full socket engagement, handle swing or a continuous
removal sweep. All 200 actual tool/removal dispositions stay blank.

Assembly retains the preceding supported sequence: runners/legs/sides and
posts, header/principals/rails, seated exterior cleats and their angles,
then the powered-off harness, kickers, lower panels and upper panels.
At the eight spacer stacks, stage all shared fittings before inserting the
bolt; keep the nut washer against its original supporting face. Hand-start
the nut and preserve the head/nut directions. Do not use tightening to draw
misaligned holes or an incorrectly cut recess into place. No torque,
preload, washer friction or locking capacity is assigned.

For dismantling, unload and independently support each part, then manage
the harness and remove upper panels, lower panels and kickers. At each
supported joint remove the nut, spacer where present and nut washer, then
withdraw the bolt toward its head. The selected headward shaft travel is
63.5–215.9 mm, plus head/tool handling space. A shared shaft releases both
angles; preserve each labeled matched set. No old withdrawal corridor,
transport assembly or lift rating transfers to this layout.

## Conditional operation limits and verification

The four corner operations no longer have the modeled bore/screw conflict.
Their selected stack arithmetic and nominal added-volume screens are
resolved here. Actual screw/end resistance, installed tolerances, contact
and spacer resistance, complete joints and continuous tool/removal fit
still stop any affected operation lacking its required evidence. In
particular, factory spacer strength/tolerances are unpublished; the spacer
does not fully back the larger washer annulus. Delivered bolt fillets must
seat correctly in their washers, including the retained ½-in fillet/washer
corner. No blanket external sign-off or physical-test prerequisite is added.
All Actual/Disposition cells remain blank until observations exist.

[Inputs](inputs.json), [result](result.json) and [verification](verification.json)
bind the changed records and preceding immutable companions. The producer
checks its 1,217 source pins and replays all preceding shop bytes through the
old helper, which checks its own 864 pins. The saved union audit verifies
all **1,230 distinct pins** unchanged and all 14 issued files byte-identical.
The 100-axis identity stays unchanged; only changed current companions are
composed. The producer reuses
existing datum/drawing, catalog-window, bounds and ideal-angle helpers.
Permanent additions are compact tables, SVGs and receipts; CAD, mesh,
manual and dependency copies are excluded. The active raw run is
`fea/generated/thin-bolted-current-contact-v1/eoere-successor-v1/current-shop-followup-v1/run-v6/`;
failed/intermediate attempts remain recoverable. No pruning is authorized.

From the repository root, reproduce into a fresh ignored directory:

```sh
PYTHONPATH=. .venv/bin/python -B scripts/eoere_current_shop_followup.py \
  --inputs-sha256 8ce489dad7c7f3c9e7d3f80ebdd7dd6e674df240dc1a89fcde4acb125497e320 \
  --out fea/generated/thin-bolted-current-contact-v1/eoere-successor-v1/current-shop-followup-v1/NEW_RUN
```

Replace `--out` with `--check` and the packet directory to compare exact
current bytes. Run `uv run pytest -q tests/test_eoere_current_shop_followup.py`
for the small independent Decimal/coordinate/envelope/guard checks. Full
source replay requires the retained ignored inputs and pinned CADQuery;
the Git-only tests do not require a new solve or full CAD rebuild.
