# Selected purchase hardware and nominal installation followup

The later [engineering assessment and acceptance decisions](../../../../../completion-ledger.md#engineering-assessment-and-acceptance-decisions)
confirm the recorded six-case load basis and add saved-state contact/effective-length
diagnostics. Screw/panel exceedance resolution is deferred by the owner. Physical
demand applicability, complete-joint resistance and finished-member/stability
acceptance remain open; no release or geometry/hardware change follows.

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

The owner-directed [structural assessment](structural-assessment.json) completes
the feasible reporting/calculation scope for the unchanged raised-screw geometry
and selected hardware, with the extra grid off. Actual build-fit work is excluded
from this continuation; every observation remains blank. Complete resistance and
current response were unknown when that assessment was issued. The later
[current six-case forces](#current-six-case-forces) and
[current joint/member references](#current-joint-and-member-references) add their own bounded evidence.
The assessment itself performs no remedy,
geometry/hardware change, CAD rebuild or native solve.

All **100 stacks / 120 timber intervals** are joined to their selected bolt's
underhead datum, including maximum catalog head-washer thickness and intervening
plates. The calculation bounds possible thread/runout occupancy beyond minimum
smooth body; it does not identify delivered threads. Under
[NDS 2024 §12.3.7.1–.2, printed page 95](https://awc.org/wp-content/uploads/2026/09/AWC_NDS2024_withCommentary_20260911_Website_Chapter-12-Dowel-Type-Fasteners.pdf),
full-body diameter has a limited exception when thread bearing occupies at most
one quarter of the relevant member. Otherwise root diameter or a justified
detailed threaded-part analysis is needed. The archived source digest is recorded
in the assessment; catalog gage length is not substituted for actual thread start.

| Catalog geometric bound | Stacks | Maximum possible fraction in a timber |
| --- | ---: | --- |
| Above one quarter | 68 | 60 short angle stacks: 44.267%; four front frame and four mixed cleat stacks: 27.600%. |
| Within one quarter, with possible exposure | 24 | Sixteen 4¾-in: 11.829%; four rear-runner: 20.700%; four ½-in: 14.629%. |
| Minimum nominal smooth body covers wood | 8 | Four shared-header and four spacer-equipped cleat/post stacks: 0%. |

The **68 above-quarter bounds prevent guaranteeing the diameter exception from
these catalog windows alone**. They do not prove actual thread exposure or a
strength failure. Every stack retains null actual thread fraction and null current
capacity. No longer bolt, changed stack or other remedy is proposed.

The existing spacer areas give ideal mean pressures per 1,000 N centered axial
force of **4.965 MPa** on the ring, **5.318 MPa** over the washer overlap and
**10.735 MPa** over the ideal nut overlap. These unit-force calculations supply
neither current axial actions nor allowable contact, bending or seating resistance.

The assessment authenticates the preceding six-case summary through its existing
JSON-only helper and **1,244-source union**, retaining 40 own-case reference
exceedance rows and the other reported timber sensitivity, shaft, washer and steel
diagnostics. Governing preceding references include generic head **2.572553**,
generic required thread/gross penetration **1.391751**, panel bending X/Y
**4.613408 / 2.684624**, rolling shear X/Y **2.451803 / 1.117058**, and t6/Ri6 heel
**1.107192**. The nominal t6.35/Ri6.35 heel reference is **0.992649**. These are
recorded extended-cleat comparisons, not Hillman-specific resistance or a pass
for the current sections, screws, bolts or spacers. Their complete-joint resistance
stays null. No exceedance is repaired.

The [reproducible review](mechanics-review.json) keeps current resistance
unknown and retains all preceding head/panel/heel reference exceedances.
Its [small standard-library producer](review.py) uses authenticated issued
dimensions and the preserved connected-stack packet. No native solve runs.

| Question | Usable result | Exact missing evidence |
| --- | --- | --- |
| Raised screw ends | Current simultaneous actions and nominal backing; 26.9-mm post-top and 19.05-mm side axis distances. | Hillman-specific end/splitting and combined head/withdrawal/lateral resistance. Generic guidance is not its capacity. |
| Eight mixed stacks | Current own member wrenches and 24 surface bearing trials per case; selected thread windows remain bounded. | Actual diameter intervals and compatible connected yielding/contact; equilibrated bearing trials are not resistance. |
| Eight spacer contacts | All 48 own nut forces and nominal washer-ring comparisons; projected areas remain separate from actual contact. | Flatness/chamfers, coating, steel properties, compatible washer/spacer bending, eccentricity and nut seating resistance. |
| Other thread-bearing rows | 92 selected rows do not establish smooth body through all far wood. | Delivered body/runout/root intervals and an applicable connected bearing/yield treatment. |
| Finished sections and restraint | Current signed demands, 38 exact finished planes/228 comparisons, panel and support screens. | Continuous critical sections/local failure modes, justified bracing, product panel resistance and physical restraint/applicability. |
| Complete joints | Geometry, catalog windows and nominal access are separate completed checks. | Compatible behavior under simultaneous actions and product-specific angle/joint resistance. All current complete resistances remain null. |

The ideal contact formulas are `pi*(OD²-ID²)/4` for rings and
`sqrt(3)*AF²/2 - pi*spacer_ID²/4` for the nominal hex overlap. They use the
existing modeled 19.05-mm spacer OD, 10.31875-mm ID, 11.1125-mm washer ID
and 14.2875-mm nut flats; they contain no material or allowable stress.
The earlier six-case response remains bound to the extended-cleat revision.
That frozen assessment supplies no changed gravity, stiffness, contact or
response pass; the separately bound current force packet follows below.

## Current six-case forces

Owner-directed item 1 is complete for the exact raised-screw geometry and
selected hardware, with the extra grid off. The [source manifest](current-response-v1/inputs.json)
and [six-case result](current-response-v1/result.json) bind fresh conditional
first-order fields for `a12-forward`, `a12-rear`, `a12-left`, `k12-right`,
`k12-rear` and `a1-rear`. All six pass independent saved-field equilibrium,
load-work and recovery checks. Their maximum full-gradient residual is
**5.521612e-6 N**, below the unchanged 1e-5-N numerical gate.

The adapter updates finished receiver/panel sources, the two raised screw
ports, 32 selected shaft lengths, eight separate spacer gravity rows and
eight outward nut capture faces. It reuses the existing mechanics and audit
helpers. No old solved state, force or acceptance is transferred. There are
150 physical owners, 100 shaft bodies, 508 metal gravity roles, 66 screw axes
and 835 applied load rows in each live case. Each case has its own saved
operator bundle and unchanged source capture.

Maximum modeled connection-point motion is **56.603761 mm** and maximum
relative timber/fitting rotation is **0.107845 rad**. These are first-order
diagnostics with no adopted small-motion threshold. Gross-stock timber
stiffness, generic Hillman stiffness, full nominal shaft diameters and flat
nominal fittings remain conditional priors. The fixed two rear-leg centroid
XY restraints and 32 compression-only normal points do not establish physical
floor capacity or exact distributed no-slip restraint. The distributed panel
right-hand side is an authenticated producer capture, not an independently
regenerated distribution. Physical applicability and demand bounds remain open.

Peak modeled screw withdrawal is **1,492.868838 N** at
`round_panel_upper_left_rim_4` in `a12-rear`. The result also retains each
case's eight spacer nut-capture actions; their maximum is **334.929289 N**
at `cleat_post_bolt_left_2` in `a12-left`. These actions do not qualify screw,
washer, spacer, steel, timber or complete-joint resistance. The earlier
thread-window bounds and reference exceedances retain their exact inputs.
No remedy, geometry/hardware change, actual fit work or native FEA is performed.

The [maintained ledger](../../../../../completion-ledger.md#current-geometry-and-selected-hardware-six-case-forces)
records all cases, exact preparation/method/execution references, review and
reproduction details. The bounded component evaluation follows below;
every release flag and current capacity stays false/null.

## Current joint and member references

Items 2 and 3 now have their own [six-case component record](current-response-v1/components.json)
and [frozen calculation inputs](current-response-v1/components-inputs.json).
All calculations consume the current admitted fields. The
[maintained evaluation ledger](../../../../../completion-ledger.md#current-joint-and-finished-member-references)
records scope, witnesses, exact missing inputs and reproduction commands.

Current generic screw-head demand reaches **2.572615**, and required effective
thread length reaches **62.969535 mm** against **45.243750 mm** gross nominal
penetration. These references do not qualify Hillman resistance. Sampled panel
bending reaches **4.613400** and rolling shear **2.451860**. The t6/Ri6 heel
scenario reaches **1.107141**; the nominal t6.35/Ri6.35 scenario reaches
**0.992604**. Every reference exceedance remains recorded without a remedy.

All 100 shafts, 120 timber walls, 200 washer captures and 66 screws are covered
per case. The 92 compatible two-member lateral references remain conditional;
eight mixed stacks have current equilibrated force/couple trials, not a yield
capacity. Eight nut washers now use nominal spacer overlap rings. Maximum
spacer force is **334.929289 N**, with ideal nut-overlap mean **3.595300 MPa**;
actual pressure, product strength and compatible contact remain unknown.

The cached-solid study covers **38 finished planes / 228 same-case comparisons**
across all 22 timbers. Its maximum conditional fully-braced normal index is
**0.524029** and necessary average-shear index **0.153412**. These selected planes
do not establish continuous critical sections, local hole/notch failure or member
stability. Four members exceed the full-span weak-column domain and need justified
restraint/effective lengths. Necessary floor-plane balance screens pass; friction,
floor capacity and first-order physical applicability remain unqualified.
All 24 complete-joint resistances and complete finished-member capacities stay null.

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
Run `uv run python -m scripts.eoere_structural_assessment --out FRESH.json`
from the repository root to reproduce the structural assessment after restoring
its recorded source inputs. It reuses the issued component authenticator and
does not execute a solver. The checked development index binds the issued result;
portable tests independently replay all 100 stack joins from tracked shop tables.

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
The structural assessment is a necessary 138,879-byte permanent record of the
100 stacks, 120 member intervals and preceding own-case exceedance witnesses.
Its raw trials and CI logs remain in ignored
`fea/generated/selected-hardware-followup-v1/ci-diagnosis-v1`; they are active
verification evidence until this continuation closes. Existing frozen packets,
source banks and recovery records remain active; nothing is nominated for pruning.
No purchasing, physical tests, cutting, drilling, fabrication or climbing
release follows from these conditional development deliverables.
