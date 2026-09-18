# 2×6 leg: standard-hardware development trial

This trial advances the [thread-length checkpoint](solid-leg-connection-next.md)
to an actual CAD connection. It retains the spread 100×50 mm pattern, all wood
parts for either the zero-extension or +300 mm foot candidate. The +300 mm
variant remains the API default. No larger holes or custom steel parts are
required. It is **not build-ready** and not a procurement release. The compact
variant has a separate [geometry viewer](https://mckayreedmoore.github.io/mini-moonboard/?model=lumber-leg-hardware-2x6-e0).
Existing viewer defaults and frozen FE evidence remain unchanged. The new
hardware viewer is not a matching model for the existing joint-spring FEA.

## Proposed hardware per eight leg connections

| Component | Candidate | Quantity |
| --- | --- | ---: |
| Bolt | [37C425HCS5Z](https://boltsandnuts.com/products/3-8-16x4-1-4-hex-cap-screws-grade-5-bolts-zinc-clear), 3/8-16 × 4¼ in, partial thread, SAE J429 Grade 5 | 8 |
| Nut | [37CFHN5Z](https://boltsandnuts.com/products/3-8-16-grade-5-finished-hex-nuts-zinc-clear), 3/8-16, SAE J995 Grade 5 | 8 |
| Washer | [Wrought 014423 USS MCX](https://www.wroughtwasher.com/standard-washers/extra-thick-mil-carb-mcx/), extra-thick hardened, electro-zinc yellow | 32 |

Place **two washers under each head and two under each nut**. Manufacturer
washer bounds are OD 0.995–1.015 in, ID 0.433–0.453 in, thickness 0.110–0.126 in
(2.794–3.2004 mm). Small-quantity availability has not been confirmed; the
manufacturer offers quotation. No order or third-party contact has been made.

A retail sourcing lead checked on 2026-09-08 is
[BoltsandNuts 37UNTX8Y](https://boltsandnuts.com/products/3-8-uss-grade-8-extra-thick-flat-washers-zinc-yellow),
listed in single-piece quantities. Its live product data showed availability
at that check; this is not a stock reservation or a purchase recommendation.
The listed thickness and ID intervals match the MCX intervals, but OD is
0.993–1.030 in, not 0.995–1.015 in. It is therefore **not an approved drop-in
substitution** for the current CAD or bearing footprint. The linked technical
drawing returned an invalid/404 URL during review. Resolve the product drawing
and material basis, then repeat fit and bearing checks before selecting it;
do not silently replace the MCX identity in existing evidence.

The bolt drawing states ASME B18.2.1 and Class 2A threads; the nut drawing
states ASME B18.2.2 and Class 2B. Nut maximum height is 0.337 in (8.5598 mm).
The CAD uses the predecessor's conservative cylindrical head/nut envelopes,
which bound the new dimensions, and four individually modeled washers. The
stack is **not treated as one bonded thick plate** and receives no assumed
increase in washer bending strength.

## Tolerance window, not a favorable nominal fit

Each timber member must be measured within **37.5–38.5 mm** (1.476–1.516 in).
This is a project receiving condition, not a claim about lumber manufacturing
tolerances. Outside that window, recompute the stack before accepting it.

Using the [published body/gaging dimensional rules](https://www.nickel-systems.com/blog/what-are-max-grip-gaging-min-body-lengths),
the 4¼-inch 3/8-16 bolt has minimum body length 74.6125 mm and maximum grip-gaging
length 82.55 mm. The [length tolerance table](https://www.nickel-systems.com/products/bolts-screws/hex-head-cap/)
places 4¼ inches in the **over-4-through-6-inch band**: minimum overall length
is 105.41 mm, not the shorter bolt's 1.524 mm tolerance assumption.

| Worst-case check within the receiving window | Margin |
| --- | ---: |
| Minimum body length beyond required quarter-thread threshold | 0.8367 mm |
| Minimum nut seating plane beyond maximum grip-gaging length | 3.626 mm |
| Minimum bolt end projection beyond maximum nut outer face | 7.0486 mm |

The body requirement is `2 × maximum washer thickness + rim thickness +
0.75 × leg thickness`. The seating plane includes all four washers. Overall
length tolerance is used for tip projection, not subtracted a second time
from the tabulated minimum-body rule. End chamfer and actual complete thread
exposure still need receiving verification.

This is a substantially stronger dimensional basis than inferring shank length
from a nominal one-inch thread. Standards and catalog statements are still not
an individual shipment certificate. Verify markings, full body/runout, thread
engagement, washer identity and stock dimensions when received. Do not use the
vendor's steel-joint torque values as wood installation instructions.

## Model and verification scope

`mini_moonboard.leg_hardware_trial` replaces only eight hardware assemblies.
It shifts their under-head origins to keep the wood bearing planes unchanged.
It does not change the 101 wood/other bodies or the remaining connections.
CAD clearance checks cover all eight new assemblies against every wood body
and all other hardware, at minimum, midpoint and maximum washer thickness,
with nominal 38.1 mm timber. These checks do not constitute a full tolerance
stack CAD assessment for every possible timber dimension or a socket-fit test.

The compact hardware variant uses `parts(extension=0.)` and
`connections(extension=0.)`; the original calls without an extension still
select +300 mm. Both variants reuse their existing spread-frame wood and
non-leg connections. Zero extension means no added foot-centre offset in that
geometry, not a new guarantee that the entire foot, hardware or tool envelope
lies beneath the board's top projection. It does not inherit the extended
candidate's floor equilibrium, joint demands or resistance conclusions.

```sh
uv run pytest -q tests/test_leg_hardware_trial.py
```

Earlier extended-only verification: 28 hardware, spread-frame and thread-screen checks passed;
Ruff and whitespace checks passed. Independent correctness, testing and
package-consistency reviews found no substantial issues. This verifies the
stated implementation scope, not structural adequacy.

Compact-extension update: all 12 tests in `test_leg_hardware_trial.py` passed
(34.88 s), including all eight hardware assemblies against all wood and other
hardware for both extensions at minimum, midpoint and maximum washer thickness.
The update also checks unchanged +300 mm defaults. Ruff passed. These are CAD
fit and arithmetic checks, not a strength check or release of either variant.

## Remaining work toward a complete leg

### Through-bolt axial/lateral load path

For this two-member through-bolt joint, NDS 2024 §12.3.9.1 separates the
component perpendicular to the bolt axis (checked against adjusted lateral
resistance) from the parallel component (requiring adequate bearing area).
The screw-withdrawal interaction equation is not a substitute for this rule.
See [AWC Chapter 12, printed page 96](https://awc.org/wp-content/uploads/2026/08/AWC_NDS2024_withCommentary_20250328_WebsiteChapter-12-%E2%80%93-Dowel-type-fasteners.pdf).

The compact archive's 250 lb family has a maximum absolute bolt-axis spring
transfer of 172.847 N at `lumber_leg_bolt_left_4`, with simultaneous XYZ force
(-172.847, 571.288, -575.779) N. The corresponding 300 lb sensitivity peak is
202.962 N. These are model connector transfers, not demonstrated washer forces
or bolt pretension. The lateral and axial checks must retain each same-case
vector rather than combine unrelated maxima.

The [MCX manufacturer](https://www.wroughtwasher.com/standard-washers/extra-thick-mil-carb-mcx/)
publishes dimensional ranges and RC 38–45 hardness, but that page does not give
a bending allowable or guaranteed tensile yield strength. Before accepting
washer flexure, obtain a suitable material specification or published load
rating and evaluate the actual head/nut/washer contact geometry. Two washers
against one member give one wood-contact footprint; do not double its area or
treat the stack as a bonded double-thickness plate.

The current bilateral spring model omits tightening preload, local member-face
contact and washer separation. A local joint-contact calculation with an
explicit installation condition is therefore the next load-path step. It
must not infer total washer pressure solely from the incremental spring-axis
force. Actual material/stock identity and assembly seating still need human
confirmation; no manufacturer contact or purchase has been made.

1. Finish sourcing/receiving specifications and assess same-case lateral/axial
   connection demand, washer bearing/flexure, group action and splitting. The
   earlier favorable full-body reference remains conditional; a new hardware
   length does not calibrate spring stiffness or establish a physical force bound.
2. Model real restraints. The current legs connect only through four upper
   bolts each; there are no lower longitudinal ties or rear-plane bracing.
   A removable base U (two side ties and a rear cross-tie) plus rear-plane
   triangulation if needed is the next concept to assess. Its connections must
   reach structural base members, not removable panels. Avoid the climbing
   envelope; do not assume a single pin provides anti-roll fixity.
3. Analyze complete-leg bending/compression/buckling with those joints and
   restraints, then compliant unanchored floor behavior. Internal bracing does
   not prevent whole-assembly sliding or tipping when floor equilibrium fails.
4. Publish the selected, checked geometry in the viewer and synchronize cuts,
   drilling, hardware and assembly instructions. Do not promote this trial to
   the default design before those gates are addressed.
