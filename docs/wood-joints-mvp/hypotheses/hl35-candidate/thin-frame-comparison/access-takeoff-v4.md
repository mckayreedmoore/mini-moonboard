# Thin v4 access, takeoff and conditional weight

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

October 6 primary listings give the 36 angles **$174.84**, using
[B104ZN at $5.52](https://www.platt.com/p/0151375/eaton-b-line/four-hole-corner-angle-steel-zinc-plated/781011500436/blib104zn)
and [B103ZN at $3.53](https://www.platt.com/p/0151547/eaton-b-line/three-hole-corner-angle-zinc-plated/781011500337/blib103zn).
The cheapest listed pack/single combinations in the report give **$312.01**
for the known partial hardware comparison, or **$287.05** for the 58 new-axis
hardware and angles. The 42 three-inch bolts use one 50-pack at
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
