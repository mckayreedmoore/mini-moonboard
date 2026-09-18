# Complete hybrid comparison candidates

[Matched FEA results and stability limitations](hybrid-frame-fea.md) compare
both complete candidates with the published plywood reference.

**Complete nominal geometry, not build-ready or structurally approved.**
These candidates replace neither the default plywood model nor its evidence.
They supersede the rim-only studies for future whole-frame comparison. Material
grades, rated fastener products, angle fabrication, end-grain connections and
the actual load envelope still need engineering decisions before construction.

## Inspect

| Candidate | Interactive model | CAD | Parts and connections |
| --- | --- | --- | --- |
| 2×12 | [Rotate and select](https://mckayreedmoore.github.io/mini-moonboard/?model=2x12) | [STEP](../exports/hybrid-full/2x12.step) | [Parts](../exports/hybrid-full/2x12_parts.csv), [connections](../exports/hybrid-full/2x12_connections.csv) |
| 2×10 | [Rotate and select](https://mckayreedmoore.github.io/mini-moonboard/?model=2x10) | [STEP](../exports/hybrid-full/2x10.step) | [Parts](../exports/hybrid-full/2x10_parts.csv), [connections](../exports/hybrid-full/2x10_connections.csv) |

### 2×12 front and backing

![2×12 candidate climbing side](../exports/hybrid-full/2x12_front.png)
![2×12 candidate backing](../exports/hybrid-full/2x12_rear.png)

### 2×10 backing

![2×10 candidate backing](../exports/hybrid-full/2x10_rear.png)

The viewer selector reloads either hybrid or the unchanged plywood reference.
Hybrid bolts are red, screws blue and angle brackets grey. Part selection gives
metric and feet/inches dimensions. Profiles govern shaped plywood and angle
parts: their listed dimensions are bounding blanks/envelopes, not rectangular
finished pieces. Angle descriptions specify both leg dimensions and 6 mm steel
thickness. Plywood legs/cheeks/splices use two 19.05 mm layers, 38.1 mm total.

## Geometry and load paths

- Retain all climbing panel, kicker, hold and LED datums and the 40° slope.
  Side rims remain dressed 2×10 or 2×12 with their front flush to the climbing
  face. The 2514.6 mm top cap needs stock longer than eight feet.
- Use dressed 2×4 (38.1 × 88.9 mm) perimeter/mid backing and 2×6
  (38.1 × 139.7 mm) seam backing. Kicker backing is ripped to 50 mm width.
  Rear crossmembers and short normal ribs are 2×4.
- Preserve the main panels' 12-screw perimeter and add **four mid-batten
  attachments per panel**, 64 main-panel screws total. Mid battens lie between
  C/D and I/J columns rather than on the geometric panel centres. These extra
  attachments deliberately differ from passive, unfastened backing in the
  previous C10 sensitivity study.
- Mid and seam backing connect through normal ribs to the rear crossmembers.
  Rib front screws and batten-end screws stay in their backing modules; rear
  rib interfaces use removable bolted angles. Rear beams connect to the side
  rims through another set of bolted angles. No lower-leg crossbar is added.
- Retain four through-bolts per exterior plywood leg, level full-width floor
  cuts and the rim-only candidates' foot centres. Foot bearing lengths differ.
- Top/rim and rear-beam/rim joints use nominal custom 100×100×6 mm angles,
  88.9 mm long. Rib/rear-beam joints use 80×80×6 mm angles, also 88.9 mm long.
  Two bolts per leaf are represented. These are **sharp-corner envelopes**,
  not selected off-the-shelf angles: inside radii, welds/bends, holes, edge
  distances, stock tolerances and local steel capacity need resolution.
- All through-bolts are nominal 9.525 mm diameter, with 25.4×2 mm washers and
  9 mm nut envelopes. Lengths are 63.5, 95.25 or 114.3 mm as the schedule shows.
  These envelopes do not specify a strength grade or locking system.
- Wood screws remain nominal 4.826 mm with a 10 mm countersunk-head envelope.
  In particular, the long batten-end screw lengths are geometry assumptions,
  **not a verified purchasable screw schedule**. End-grain withdrawal/splitting
  must be checked or the joints redesigned; a connected CAD graph is not a
  demonstration of adequate connections. Do not purchase screws from this study.

## LED and service provisions

Main backing is relieved around nearby hold/LED positions. The new kicker top
backing also has 40 mm LED relief notches. This check exposed an omission in
the older plywood backing, which remains unchanged as a comparison reference;
its existing rear LED clearance must not be assumed correct.

Kicker screws remain four per long edge with shared end columns; those columns
now have 50 mm horizontal end inset, and intermediate positions shift around
the reliefs. There are still eight screws per kicker panel, 16 total. The main
panels retain their existing perimeter coordinates exactly.

Tests check 12.7 mm diameter × 31 mm rear LED-body envelopes for all 132 lights,
including kicker lights, against wood, steel and fasteners. They also check
11×2 mm straight main-board wire corridors at N=50–52 mm. These corridors are
space reservations, not the kit's complete electrical route. Connector sizes,
lead bends, strain relief, kicker-to-main routing and removal access remain
human-audit items under the [LED installation guide](v1-led-installation.md).

Bolt access is screened against both parts and other installed fasteners, with
an assumed 36 mm OD socket and 25 mm axial approach, plus straight
bolt-withdrawal corridors. These are not a substitute
for confirming actual tool sizes, simultaneous tool use and assembly access.

The rib front screw and transverse bolts are separated 54 mm along S, leaving
over 46 mm between their idealized screw/bolt-bore envelopes in that direction.
This fixes a crossed-bore near-contact found during review, not a certified
minimum wood ligament. Edge/end distances and directional bearing/splitting
still need material- and load-specific checks.

## Relocation boundaries

The leg interfaces, top angles, rear-beam rim angles and rear-beam rib angles
are bolt-removable. Rear crossmembers can separate without withdrawing rib
wood screws. Angle-to-rib and angle-to-rim bolts may stay with their modules.
Backing grid joints and kicker-cheek splices are intended to remain screwed
together; moving the grid as a large assembly may be awkward. Panel removal
still disturbs ordinary panel screws: reusable panel fasteners are **not**
resolved by this revision. Repeated relocation capability remains provisional.

This is not a teardown sequence. Independently support the board before
removing structural parts, remove/protect LED strips before separating panels,
and resolve lifting, module size/weight and the transport route. Do not assume
the partially dismantled structure is stable or remove the legs first.

## Verification and FEA boundary

`uv run pytest tests/test_hybrid_frame.py` checks solid validity, unintended
part/fastener intersections, screw receiving material/tip containment,
connection graph, floor bearing, tool envelopes, and lighting clearances.
Generate CAD with `uv run python -m mini_moonboard.hybrid_exports`.
The old rim-only and analytical section comparisons remain historical studies.

The comparative bulk FEA uses wood without holes, perfectly bonds every touching
timber interface and fixes floor nodes, matching the prior plywood assumptions.
It omits steel/fastener compliance: direct timber contacts replace actual
angle-mediated joints in this idealization. E=7000 MPa and nu=0.3 for all wood
is an explicitly artificial equal-property geometry comparison, not selection
of lumber properties. It cannot validate screws, brackets or unanchored stability.
Separate rigid-body stability uses assumed wood/steel densities and no measured
floor friction. Neither numerical study authorizes construction or climbing.
