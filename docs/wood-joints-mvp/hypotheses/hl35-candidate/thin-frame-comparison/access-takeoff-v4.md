# Thin v4 construction coordinates, access and takeoff

The candidate-specific [construction manifest](build-planning-v4/manifest.json)
now coordinates the twenty timber datums, raw profiles and end-cut planes,
seventy bolt stacks, thirty-six fittings, sixty-six Hillman axes and their
receiving members. Fifteen CSVs contain 1,248 source-bound rows. Independent
readback checks every source scalar, all 282 dependencies and all 2,496 blank
Actual/Disposition cells. This is a nominal build-planning packet for the
reviewed thin B103/B104 candidate. Joint resistance, current contact response
and physical fit remain open in the [completion sequence](../../../completion-ledger.md#build-package-completion).
The selected ML24Z/SDS candidate and its shop packet remain separate.

## Reading the construction coordinates

All linear coordinates below are millimetres. For each member, the datum and
three proper local unit vectors are in [member-datums.csv](build-planning-v4/member-datums.csv).
The local L direction follows nominal grain; U/V define geometry and do not
identify actual radial/tangential wood directions. A local point maps to world
coordinates as `datum + L*l + U*u + V*v`. Use the member's own raw vertices and
plane equation, rather than a neighbouring member's datum.

| Operation or identification | Coordinated table | Meaning and limit |
| --- | --- | --- |
| Lay out the twenty nominal blanks and profiles | [Raw vertices](build-planning-v4/member-raw-vertices.csv), [end planes](build-planning-v4/member-end-cut-planes.csv), [plane/vertex links](build-planning-v4/member-end-cut-plane-vertices.csv) | A plane is `normal · local_point = offset`; its normal points outward. The reported normal-to-grain angle is not automatically a saw setting. The stock nesting below includes kerf and end allowances. |
| Identify the retained tapered rear recess | [Recess parameters](build-planning-v4/recess-parameters.csv), [profile vertices](build-planning-v4/recess-profile-vertices.csv) | Keep the recorded 1:12 cut and the right cutter's −3.175-mm translation. A stale unshifted right cutter does not describe this candidate. |
| Locate each physical structural bolt | [Bolt axes and stacks](build-planning-v4/bolt-axes-and-stacks.csv), [wood receivers](build-planning-v4/wood-receiver-bearing.csv) | Entry/exit L/U/V values belong to each finished receiver. Occupied bore diameters and modeled bolt lengths are analysis envelopes; they are not bit selections or delivered lengths. |
| Match fittings and shared shafts | [Fittings and duties](build-planning-v4/fittings-and-duties.csv), [hole ownership](build-planning-v4/fitting-hole-ownership.csv), [steel intervals](build-planning-v4/steel-bearing-thread-windows.csv) | Thirty-six fittings cover all twenty-four former angle duties. Seventy-two steel bearing intervals include fourteen shafts shared by multiple fittings. Do not count a shared shaft twice when purchasing. |
| Locate the sixty-six purchased screws | [Hillman receiver axes](build-planning-v4/Hillman-receiver-axes.csv) | These are this candidate's panel/kicker stations, with their own receiver coordinates. Do not substitute baseline stations, SDS screws or SPAX resistance. |
| Identify each washer's support side | [Washer receiving planes](build-planning-v4/washer-receiving-planes.csv) | All 140 head/nut roles retain their own material, body and flange. A pressure datum is not a measured contact area or recovered washer moment. |
| Trace reusable stock, access, price and mass evidence | [Reference tables](build-planning-v4/reference-tables.csv), [source hashes](build-planning-v4/source-sha256.csv) | Frozen source paths and JSON pointers preserve the original comparison's date and scope. Updated merchant observations below are a separate receipt. |

Keep Actual and Disposition blank until the corresponding part, dimension or
operation is observed. The current layout assumes CAT 23/32 panel thickness
18.25625 mm and kerf-right main-panel widths 1217.6125 mm. The owner's nominal
3/4-inch description does not establish delivered thickness. A true 1219.2-mm
square is 1.5875 mm wider than this model's main-panel blank. Resolve actual
thickness and widths before transferring panel coordinates; neither the
existing panels nor the model have been recut or silently changed.

The owner's existing Hillman pilot policy remains a 1/8-inch lead hole plus
a 3/8-inch face countersink using the recorded #10 insert, with a #2 Phillips
driver and flush head. The [baseline checklist](../../../../floor-flush-shop-checklist.md)
records that policy and the offcut trial. These are owner-selected bit sizes,
not Hillman-published strength or pilot qualifications. Bolted fitting holes
need compatible delivered hardware and a separately checked installation
choice; the maximum CAD bore envelope is not a drill instruction.

The four starting half-inch ×8-inch comparison bolts require an underhead
length at least **199.436892 mm** to expose two threads with the frozen
washers and comparison nut's maximum height. The comparison's shortest
allowed length is **198.628 mm**, leaving a **0.808892-mm** shortfall. Washer
tolerances, smooth-shank reach and thread runout remain separate checks.
The table's separate frozen CAD nut envelope requires **199.589292 mm**;
it uses a different nut height from the catalog comparison.
Measure delivered stacks or qualify a replacement before that operation;
a longer nominal bolt has not been inserted into the reviewed access model.
The twelve restricted B103 head washers use their own modeled **3.0734-mm**
thickness, rather than the earlier generic 3.3528-mm washer window.

Eaton's [fitting catalog, page 106](https://www.eaton.com/content/dam/eaton/products/support-systems/strut-systems-%26-accessories/strut-fittings-and-accessories/strut-fittings-catalog-section.pdf)
describes 33-ksi minimum-yield steel and a factor of 2.5 for specified channel
assemblies. That factor relates ultimate load to design load with channel
nuts and short cap screws. It does not rate these wood-supported through-bolt
joints or convert the calculated flange first-yield indices into allowable
loads. The [source-bound manufacturer scope](../../../../../fea/generated/thin-bolted-build-planning-v4/manufacturer-scope-v1/manufacturer-scope.json)
records purchase targets and the unresolved catalog/SKU dimensional conflicts.
Match the actual hole centers, plate thickness, leg lengths and formed heel
before applying the nominal coordinate packet. The manufacturer's channel
bolt torque is not an adopted wood-joint tightening instruction.

The [source-bound access/takeoff report](access-takeoff-v4.json) checks the
reviewed v4 solids from the [shared cache](native-geometry-v4.json). The
[final free-fitting step](free-fitting-release-v4.json) preserves the first
diagonal trial's eight blocked paths and resolves them after timber separation.
The geometry is unchanged. These are conditional nominal initial-separation
checks, not a demonstration of physical demountability, inspected hardware,
fabrication instructions or structural acceptance.

## Checked sequence and scope

1. Support the unloaded members separately; remove holds/hold bolts, switch
   power off and disconnect the harness. All 66 screw axes have clear front
   driver corridors bounded by 10 mm diameter and 150 mm length. Actual bits,
   screw recesses, unplugging strokes and hands are unverified.
2. Remove the upper panels first. Each lower main panel first moves 0.5 mm
   upslope, releasing its nominal kicker miter, then moves 100 mm outward.
   Remove the kickers afterward. All six assemblies and their 132 LED and
   142 T-nut bodies clear the checked corridors. Direct lower-panel pulls
   encounter the kicker seam; this motion order resolves that nominal issue.
3. Lift the harness from the front-open channels before exposing the frame.
   The existing v4 cutter/known-answer check supplies the 8 mm timber
   depth-to-front corridor. **Complete harness body paths, connector release,
   bend radius and slack remain unverified.**
4. All 140 head/nut sides clear a conditional pass-through ring-tool body:
   half-inch bolt sides require OD ≤30 mm and axial depth ≤12 mm; three-eighth
   sides require OD ≤22 mm and depth ≤10 mm. Entry travel is 30 mm. The handle
   must fit the recorded 40° continuous sector, radius up to 215 mm, supporting
   a 20° indexed stroke. These are explicit maximum outline conditions;
   no actual wrench, torque capacity, grip or hand space is qualified.
   The larger, long socket/extension profile clears only 89/140 sides.
5. All 350 continuous metal-role withdrawal corridors are checked. Twelve
   B103 post stacks require their shared beam stacks to leave first;
   deleting only those physical preceding stacks clears all 70 bolt stacks.
   The complete dependency table is in the report.
6. Remove 28 angles, then follow the recorded 200 mm routes for all 20
   individual timbers. The remaining eight free angles move 100 mm along
   their local width axes. All 36 fittings have a checked initial route.
   Reverse these paths for nominal assembly on separately supported members.

Metal withdrawal corridors are exact continuous prismatic sweeps. Panel,
bracket and stock bounds conservatively contain the carried bodies; curved
holes are not omitted to manufacture a clear result. Parts are deleted only
after their checked 100/200 mm initial travel. Subsequent free handling,
storage, support stability, tolerances and removal under load are unverified.
The independent scoped audit checked source pins, coverage and mass
conservation without repeating unchanged CAD.

## Physical quantities and price limits

| Item | Nominal quantity |
| --- | ---: |
| New half-inch bolts, 3 / 5 inch | 42 / 16 |
| Starting half-inch bolts, 8 inch | 4 |
| Starting three-eighth bolts, 4 / 4½ inch | 4 / 4 |
| Half-inch / three-eighth nuts | 62 / 8 |
| New large USS / restricted small SAE half-inch washers | 102 / 14 |
| Starting half-inch / three-eighth washers | 8 / 16 |
| B104ZN / B103ZN angles | 24 / 12 |
| Hillman 42605 screws | 66 |

The starting half-inch washer envelope is **OD 34.925 / ID 14.2875 /
t 3.175 mm**. The frozen JSON's cost-gap prose incorrectly says 38.1 mm;
its numerical `washer_envelopes` are correct. The starting three-eighth
envelope is OD 25.4 / ID 11.1125 / t 2.032 mm. Compatible delivered products
for those 24 starting washers remain unqualified.

October 7 local-time primary listings give the 36 angles **$177.00**, using
[B104ZN at $5.59](https://www.platt.com/p/0151375/eaton-b-line/four-hole-corner-angle-steel-zinc-plated/781011500436/blib104zn)
and [B103ZN at $3.57](https://www.platt.com/p/0151547/eaton-b-line/three-hole-corner-angle-zinc-plated/781011500337/blib103zn).
The same pack/single comparison now gives **$314.17** for known partial
hardware, or **$289.21** for the 58 new-axis hardware and angles. The separate
[price observations](../../../../../fea/generated/thin-bolted-build-planning-v4/price-observations.json)
retain the verified product pages and calculations. The frozen October 6
takeoff retains its original **$174.84 / $312.01 / $287.05** figures. The
42 three-inch bolts use one 50-pack at
[$43.98](https://boltdepot.com/Product-Details?product=397), including eight
spares; the 16 five-inch bolts use
[individuals at $1.89](https://boltdepot.com/Product-Details?product=401).
The 14 restricted washers use
[3051 individuals at $0.25](https://boltdepot.com/Product-Details?product=3051).
Exact product selection, lumber, plywood/screw receipts, the 24 starting
washers, T-nuts/electrical/holds/pads, tools, machining, shipping and tax are
unquoted. **Complete installed cost is not established.**

All frozen nominal tips exceed two threads; the minimum is 3.848 threads on
the starting half-inch ×8-inch stacks. The
[priced 8-inch product](https://boltdepot.com/Product-Details?product=407)
permits −0.18 inch length tolerance. At that shortest length and the frozen
stack, the minimum becomes 1.508 threads; using the
[comparison nut's maximum height](https://boltdepot.com/Product-Details?product=2586)
gives 1.586 before washer tolerances. That SKU is a price comparison and
does not qualify delivered fit. Its ¾-inch hex flats also differ from the
frozen ⅞-inch occupancy; bearing-face area, thread runout and smooth shank
at loaded planes remain separate inputs.

A delivered bolt's length can be screened at its seated stack. Let S be the
underhead-to-nut-near distance, H the nut height, p the thread pitch and W the
usable blind socket well. The recorded two-thread target requires
**S + H + 2p ≤ L**; the assumed socket well requires **L ≤ S + W**. A
pass-through ring has no blind-well limit from its 12-mm body thickness.
With the frozen leg S=184.150 mm, comparison nut H=11.3792 mm and assumed
48-mm well, the length window is **199.436892–232.150 mm**. Measured washers,
wood grip, nut, complete threads and actual tools determine the delivered
window; the shop Actual cells remain blank.

The existing [8½-inch Grade 5 comparison](https://cdefasteners.com/order-online/coarse-thread-hex-cap-screw-grade-5-zinc/197474)
has a **211.328–215.900-mm** length range under its
[published tolerance sheet](https://cdefasteners.com/sites/default/files/product-specs/capscrewgr5-8.pdf).
It fits that algebraic window and the earlier frozen-profile serial access
supplement through 215.900 mm. It remains an unselected comparison. Using
the unselected [USS washer thickness extrema](https://boltdepot.com/Product-Details?product=15025)
at unchanged nominal wood grip narrows the worst-case window to
**199.792492–230.168800 mm**; the 8½-inch comparison needs at most a
**33.7312-mm** usable well. Its washer maximum OD differs from CAD, so
this tolerance screen is separate from the reviewed geometry. A 9-inch
comparison needs additional thread-seat and withdrawal evidence.

The four starting [⅜-inch ×4-inch comparisons](https://boltdepot.com/Product-Details?product=367)
and four [⅜-inch ×4½-inch comparisons](https://boltdepot.com/Product-Details?product=368)
have minimum length margins **8.0772 / 7.0612 mm** against the frozen
two-thread targets. Corresponding unselected USS thickness extrema retain
**6.858 / 5.842 mm** margins. Length fit does not settle smooth-shank reach;
the front stacks remain dependent on their delivered thread transition.
These calculations change no part selection, shaft length, model mass or
mechanical result.

The stock plan places all 20 timbers once: two 4×6×10-foot, two 4×6×8-foot,
three 2×6×10-foot and six 2×6×8-foot sticks, totaling 150 nominal board feet.
With the stated 3.175 mm kerfs and 12.7 mm allowances at each end, the tightest
principal/post nesting retains only 2.649 mm. Delivered usable lengths need
checking. The six panel blanks need three nominal 4×8 CAT 23/32 sheets;
the main-panel layout consumes the full sheet dimensions without trimming
allowance. The seller's usable-width discrepancy remains unresolved.

## Conditional dead mass and reproduction

At 500 kg/m³, finished timber is **106.704814 kg** and panels **60.061258 kg**.
The 350 bolt-role bodies contribute **12.758322 kg** at 7850 kg/m³. Catalog
angles are 25.44 lb / **11.539390 kg**; the conflicting current B104 SKU
weight gives the alternative **10.015320 kg** angle scenario. Catalog angle
weight replaces ideal CAD angle volume; it is not added to it.

The 66 displayed screw envelopes add **0.676903 kg** and 142 displayed
T-nuts add **1.530098 kg**, separately from the original 25 kg allowance for
holds/hold bolts/electrical equipment. These give **216.746714–218.270785 kg**
conditional dead-mass scenarios. Pads are absent from CAD and have no mass
input; complete board weight is not established. The 706 local gravity rows
split shafts/screws by receiving stock and preserve each body's volume and
centroid; exterior pieces go to the nearest actual receiver, T-nuts to their
source panels. The independent audit found maximum per-body volume error
1.25×10⁻⁹ mm³.

```sh
.venv/bin/python -m pytest tests/test_thin_bolted_access_takeoff.py -q
.venv/bin/python -m scripts.thin_bolted_access_takeoff --out /tmp/thin-access-takeoff-reproduced.json
.venv/bin/python -m scripts.thin_bolted_free_fitting_access --out /tmp/thin-free-fitting-reproduced.json
```

Eight known-answer tests and Ruff pass. Existing unchanged CAD checks were
reused within the session; reproduction computes them from the authenticated
shared BREP cache. The two JSON reports total about 740 KB because they retain
every checked corridor and the local gravity rows needed by frame mechanics.
The ignored shared cache remains active. No meshes/manuals were copied and
no raw cache was pruned.

The distinct [unused B104 near-hole proposal](b104-near-hole-proposal-v4.json)
screens the existing 24 B104 fittings against the same cached finished bodies.
It preserves a failed initial additional-bolt layout; it changes no current
geometry or accepted input. Run
`.venv/bin/python -m scripts.thin_bolted_near_hole_proposal` to reproduce it.
All source pins and 46-axis coverage checks pass; the producer passes Ruff.
No global CAD reconstruction or mechanics solve was run.

The 48 additional flange attachments produce 46 physical axes, including two
shared axes. Every proposed 14.2875mm half-inch bore and 11.1125mm three-eighth
bore is fully backed through its intended finished receiver. Raw grips are
38.1 or 88.9mm; recorded width-edge distances are at least 51.85mm. This does
not qualify the additional rows: the 47.625mm along-grain pitch is below the
half-inch 4D full-value spacing of 50.8mm, while exceeding the 3D minimum of
38.1mm. Under NDS Table 12.5.1B this spacing component is 0.9375; it is a
conditional geometry reduction rather than categorical impossible spacing.
Ten near axes have raw closest-grain-end rays
of 20.6375 or 26.9403mm, below the three-eighth 3.5D tension reference of
33.3375mm. These rays do not classify the actual square/oblique end or signed
load; a compression-specific condition cannot be silently assumed.

The initial half-inch large-washer poses have 24 head-washer intersections
with their B104 heel and two header nut-washer intersections with other B104
steel. Two outer header near stacks intersect adjacent side timbers in both
diameter scenarios. Twelve rail near nuts and washers intersect opposite
B103 beam flanges. Those B103 unused near holes coincide with the new shaft
lines, so they would need explicit additional flange attachments and an
after-plate stack; the initial failed poses intentionally retain this
omission. Adding their 5.55625mm steel thickness moves the washers/nuts and
changes twelve three-eighth nominal length requirements from 2½ to 3 inches.
That correction was identified, not adopted or rerun. B103 short post flanges
retain their single factory hole.

Only six initial half-inch and 32 initial three-eighth axes avoid all current
occupied bodies. New-axis-to-new-axis interference, installation, tool entry,
continuous removal, altered shaft/contact resistance and the complete force
couple remain unchecked. The three-eighth washer reference has only 84.541%
of its annulus backed on each head's 14.2875mm factory opening; the washer
must span that opening. Its steel radial shaft clearance is 2.38125mm, so
existing stiffness or no-slip behavior cannot be inherited. Mixed-diameter
near/far spacing is also unqualified; reducing only the added bolt is not a
qualified 4D repair. Conservatively applying each fastener's diameter leaves
the retained half-inch far bolt's 0.9375 spacing component controlling the
group under NDS section 12.5.1.2; no special mixed-diameter exemption was found.

The failed half-inch census adds 36 three-inch and ten five-inch bolts,
46 nuts and 92 washers. Using the primary prices already recorded above,
the minimum separate pack/single purchase comparison is $94.73 before
shipping/tax; reoptimizing with the current planned packs gives a $69.96
increment. These large-washer purchases do not solve the recorded clashes.
The initial three-eighth census is 34 bolts at 2½ inches, two at three inches
and ten at 4½ inches. Primary comparisons are
[Bolt Depot #363](https://boltdepot.com/Product-Details?product=363) at $0.52,
[#368](https://boltdepot.com/Product-Details?product=368) at $0.94,
[#2571 nuts](https://boltdepot.com/Product-Details?product=2571) at $0.11 and
[#3062 Grade 8 USS washers](https://boltdepot.com/Product-Details?product=3062)
at $13.75 per 100. This totals $45.89 plus two unverified three-inch bolt
unit prices; the B103 after-plate correction would instead total $39.65 plus
14 three-inch bolt unit prices. The priced #3062 tolerance envelope differs
from the existing nominal three-eighth washer, so this is a cost comparison,
not a compatible product selection. Stock, six panels and 66 screws remain
unchanged. A full-width opposing plate/couple at the B103 short flange has
not been designed or qualified; no custom plate is selected by this screen.
