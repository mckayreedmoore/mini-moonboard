# Selected purchase hardware and nominal installation followup

The current viewer applies **`eoere-selected-purchase-hardware-v1`** to the
retained **`eoere-raised-kicker-screws-v1`** timber, panel and screw geometry.
All 100 bolt axes, 66 Hillman axes and climbing surfaces remain fixed.
The [base viewer](https://mckayreedmoore.github.io/mini-moonboard/?model=eoere-selected-hardware-frame-development&view=rear)
keeps the extra grid off. Its separately scoped
[expanded-grid variant](https://mckayreedmoore.github.io/mini-moonboard/?model=eoere-selected-hardware-grid-development&view=rear)
retains the unofficial 264-position main grid. Earlier viewers remain available.
Git publication and successful Pages deployment are separate; see the maintained
[development entry](../../../../../../bolted-frame-development/README.md).

Use the [issued 100-row selection](../shop-assembly-v1/extended-cleat-followup-v1/current-model-followup-v1/hardware-selection.csv)
and [shop instructions](../shop-assembly-v1/extended-cleat-followup-v1/current-model-followup-v1/README.md).
Those frozen records describe the earlier viewer at issue. This new
[geometry receipt](../occupied-selected-hardware-v1.json) applies their override;
it does not edit their results or transfer a mechanics pass. No parts or tools
have been purchased, inspected or physically operated through this work.

## Applied hardware

The overlay replaces 32 nominal shaft cylinders, moves eight nuts outward
12.7 mm, and adds eight annular factory spacers between nut washer and nut.
Six shared local mesh templates supply both variants. The gzip scene is
**21,032 bytes**; base/expanded scenes contain **1,029 / 1,424 parts**.
There remain 100 physical bolts, 200 washers, 100 nuts, 22 angles and 66 screws.
The added eight spacers are distinct parts. Nominal cylinders do not depict
delivered thread forms or establish actual shank, runout, coating or seating.

The producer verifies 1,446 source pins before and after, two cylinder/annulus
known answers and 48 valid exported/reimported changed solids. The actual
Three.js check retains 981 / 1,376 unchanged geometries, verifies changed
world bounds within 0.15 mm of CAD, full selected lengths and all stack roles,
and derives all 48 changed stations directly from the retained axes. All
16 rendered spacer instances preserve the bore and signed annular volume
within quantization-aware limits. Eleven altered-scene, three shifted-station,
three spacer-shape and three hash-option controls reject.
The [verification receipt](verification.json) binds inputs, outputs and checks.

## Nominal wrench, socket and removal method

The [200-side worksheet](access-methods.csv) and [summary](nominal-access.json)
refine the old coarse approach screen against source-bound cached solids.
They check the complete nominal frame before panels, screws, T-nuts, LEDs
and wiring are installed, or after those parts have been removed for access.
They do not model an unloaded frame's temporary supporting arrangement.
Twelve front/rear rail bolt sides have selected tool/removal envelopes below
Z=0, reaching **93.221730 mm below the frame**. The worksheet exposes each
side's minimum Z and required additional reference floor clearance. Those
rows apply to a raised or reoriented, independently supported setup; its
actual clearance and stability remain unqualified.

| Reference operation | Clear nominal sides | Limits |
| --- | ---: | --- |
| Seated 50.8-mm socket body | 176 / 200 | At 24 nut sides this assumed body intrudes into neighboring bolt/nut envelopes. |
| Seated 25.4-mm socket body | 200 / 200 | Seating only; its complete approach/driver is not qualified. |
| Box-wrench axial insertion, complete handle | 200 / 200 | Reference head and 152.4 × 19.05-mm handle; thickness up to 6.35 mm, limited by modeled hex height. |
| Continuous 60° working-handle sweep | 200 / 200 | Use the per-side orientation in the worksheet. The same orientation clears complete axial insertion. |
| Static opposite-side counterhold | 200 / 200 | The worksheet gives a separate clear orientation. |
| Full headward shaft/head withdrawal and nut/spacer removal | 200 / 200 | Source solids and selected lengths; both receivers need separate support before removal. |

Use a matching 9/16-in or 3/4-in wrench at the hex, with a matching tool at
the opposite end. A box wrench supplies a nominal alternative at all 24
long-socket conflicts; do not assume an arbitrary deep socket fits there.
The modeled radial socket/head allowance is 1.5 mm outside hex corners.
Box-end entry includes the selected tip projection; shaft withdrawal uses
the entire selected underhead length, up to 215.9 mm. Nut and spacer removal
each extend until the near face reaches the bolt tip, including that part's
full thickness beyond it. The two tools occupy
opposite axial bands outside the wood/plate stack. No tightening torque,
preload, actual handle envelope or practical retention is assigned.

The continuous sweep is a convex outer bound of the rectangular handle:
two-degree corner samples plus a circumscribed sagitta allowance enclose
every intermediate orientation. Tests independently check containment at
0.1-degree intervals. Production solids also contain transformed handles in
four axial orientations and detect obstacles reached during intermediate
rotation or full axial insertion. Three finite-cylinder and three production-query known
answers precede 7,392
exact nominal intrusion queries. Failed trial orientations and all 24
long-socket conflicts remain in the raw results. No zero-clearance query
establishes a manufacturing tolerance. All Actual/Disposition cells are blank.

The same source bank checks all 48 added hardware envelopes with the optional
grid on. They clear nominal parts, including the added right-column services.
This transfers no grid, connector or changed-section resistance acceptance.

## Drill guide and clamp requirements

The [100-axis / 120-receiver worksheet](drill-fixtures.json) uses the shop
**13/32- and 17/32-in bits**, separately from larger occupied CAD bores.
A 19.05-mm guide plus 6.35-mm backer requires up to **203.2 mm usable bit
projection below the chuck**, and at least that clamp opening before extra
pads, fixtures or chip clearance. Added setup height increases both needs
one for one. The long 17/32-in bit requires the specified reduced 1/2-in shank.

All 120 proposed 38.1-mm square guide rings have full nominal finished-wood
support outside the occupied bore. The first two 25.4-mm pad positions at
±50.8 mm along grain fit 108 receivers. Alternative recorded pad positions
provide two nonoverlapping nominal finished-face lands for all 120, keeping
the pads outside a 25.4-mm radial drill/chuck exclusion. A 0.2-mm inward
probe and an overlap known answer check those lands against cached solids.
Production tests probe both entry directions, reject a recess beneath the
guide and distinguish separate supported pads from unavailable or overlapping lands.
Use independent stops and clamps for each receiver/backer; the coordinates
are fixture candidates, not a claimed clamp-force or assembled drill sweep.

The alignment calculation reserves half the nominal radial bit/shaft gap
for entry alignment. With an assumed **0.02-mm diametral guide play**, the
remaining worst-case budget is only **0.011771 mm** at the longest path.
The relation is `remaining = (bit - shaft)/2 - entry_error - wood*play/guide`.
Bit runout, guide tilt, wood movement and actual dimensions consume that
reserve. A bit-drilled wood guide does not establish this assumed precision.
Actual usable reach, guide fit/rigidity, clamp bodies/retention, drill/chuck
approach and support stability remain required inputs before affected work.
The existing supported circular-saw/pull-saw and hand-finished 1:12 recess
method remains a conditional shop plan; this overlay changes no cuts.

## Bounded mechanics review

The [reproducible review](mechanics-review.json) keeps current resistance
unknown and retains all preceding head/panel/heel reference exceedances.
Its [small standard-library producer](review.py) uses authenticated issued
dimensions and the preserved connected-stack packet. No native solve runs.

| Question | Usable result | Exact missing evidence |
| --- | --- | --- |
| Raised screw ends | Nominal backing; 26.9-mm post-top and 19.05-mm side axis distances. | Hillman-specific end/splitting, head/withdrawal resistance and current simultaneous actions. Generic 5-mm guidance is not its capacity. |
| Eight mixed stacks | Four new header bodies cover nominal far interfaces. Other four shafts retain up to 10.5156 mm potential far-cleat thread/runout exposure, 27.60% of 38.1 mm. | Actual diameter intervals, compatible connected yielding/contact and current member wrenches; old prescribed-action equilibrium is not current resistance. |
| Eight spacer contacts | Nominal projected areas: spacer ring 201.396 mm²; washer overlap 188.036 mm²; ideal hex-nut overlap 93.158 mm². | Actual flatness/chamfers, coating, steel properties, washer bending, eccentricity and axial seat actions. These areas are not allowable capacities. |
| Other thread-bearing rows | 92 selected rows do not establish smooth body through all far wood. | Delivered body/runout/root intervals and an applicable connected bearing/yield treatment. |
| Finished sections and restraint | Existing restored-principal volume and historical support scenario remain recorded. | Current signed demands, cut-aware strength/stability, panel participation and justified physical restraint/applicability. |
| Complete joints | Geometry, catalog windows and nominal access are separate completed checks. | Compatible behavior under simultaneous actions and product-specific angle/joint resistance. All current complete resistances remain null. |

The ideal contact formulas are `pi*(OD²-ID²)/4` for rings and
`sqrt(3)*AF²/2 - pi*spacer_ID²/4` for the nominal hex overlap. They use the
existing modeled 19.05-mm spacer OD, 10.31875-mm ID, 11.1125-mm washer ID
and 14.2875-mm nut flats; they contain no material or allowable stress.
The earlier six-case response remains bound to the extended-cleat revision.
No changed gravity, stiffness, contact or response pass is claimed here.

## Reproduction and retention

Run the receipt's recorded `scripts/eoere_selected_hardware.py` command with
[frozen inputs](inputs.json) and a fresh ignored output directory. Run
`scripts/check_eoere_selected_hardware.mjs OUTPUT.json` for both actual Three.js
variants; its installed shared Three.js bundle and existing alias bank are used.
Run `scripts/eoere_nominal_access.py --out FRESH_IGNORED_DIRECTORY` and
`scripts/eoere_drill_fixture_requirements.py --out FRESH_IGNORED_DIRECTORY`
with the repository Python environment and `PYTHONPATH=.`. Run
`python3 -B review.py --out NEW.json` from this packet directory for the
standard-library mechanics review. No generator overwrites an earlier attempt.

Keep raw `selected-hardware-v1/run-v2`, `access-v6`, `fixture-v6`, `browser-v5`
and all earlier attempts active. Source maps, queries, producer snapshots,
BREPs and screenshots remain ignored reproducible evidence. The earlier
`access-v3` result omits the last 4.1402 mm of spacer travel and cannot
support complete removal. V4 corrects that corridor but omits the portable
floor-setup fields. V5 retains byte-identical v4 queries and reports those
requirements. V6 binds the tested production wrench/finished-face constructors;
its access queries and rows remain byte-identical to V5. Keep preceding
results as limited method evidence. The persistent
recovery kit covers its recorded older scope; it does not claim this new raw
closure. No input, failed experiment or historical viewer is pruned.
No purchasing, physical tests, cutting, drilling, fabrication or climbing
release follows from these conditional development deliverables.
