# Horizontal service candidate: purchasing and assembly draft

This plan describes `horizontal-service-development`. It is a fabrication-planning
draft, not a released construction package. Four added intermediate principals
and their four posts are replaced by four independent horizontal 2x6 rails.
The separated center principals, outer rims, their supports, and direct outer
base angles remain. The current model uses ordinary panel screws; it does not
install threaded inserts.

The manifest-authenticated leg meshes reach rearward to world Y=1476.339 mm,
73.230 mm inside the upper panels' rearward reach and 59.245 mm inside the
top frame rail's reach. Both feet reach Z=0. This checks the undeformed side-view
footprint; the legs extend laterally beyond the panel edges.

The [provisional design-assumption handoff](provisional-design-assumptions.md)
records published stiffness and capacity references, current numerical inputs,
and the checks required from the independent reviewer. It does not establish
a user-weight rating for this assembly.

## Release documents

The export target is `exports/horizontal-service-development/`. The links below
are generated package locations; the export artifact check passed. The 16-page drilling
PDF is generated and checked for text bounds; structural qualification remains open.

- [Timber cutlist](../exports/horizontal-service-development/wood-parts.csv)
- [Complete parts schedule](../exports/horizontal-service-development/parts.csv)
- [Connection axes and hardware lengths](../exports/horizontal-service-development/connections.csv)
- [Full assembly STEP](../exports/horizontal-service-development/horizontal-service-development.step)
- [Complete electrical hookup schematic](horizontal-service-wiring.svg) — external leads are schematic, not measured routes
- [Cable routes and timber cutouts](../exports/horizontal-service-development/wiring.json)
- [Source and artifact manifest](../exports/horizontal-service-development/manifest.json)
- [Drilling PDF](horizontal-service-drilling/drilling.pdf) and [datum explanations](horizontal-service-drilling.md)

Do not use the infill-panel or angle-base cutlists: their intermediate framing
and screw inventories differ. The viewer is an assembly aid; the exported
member datums and connection records govern dimensions.

## Member locations and measuring references

Left and right refer to the climbing-face view. The frame coordinate `s` runs
up the sloping panel from its lower edge; `x=0` is the board centerline. Do not
measure `s` vertically up the room wall. Dimensions below identify modeled
locations, not released manufacturing tolerances.

| Member identity | Position or task |
| --- | --- |
| `base_header` | Continuous horizontal base support; use its own cutlist stock size |
| `base_side_left`, `base_side_right` | Outer sloping rims; preserve their separate leg-bolt patterns |
| `base_principal_center_left`, `base_principal_center_right` | Centerlines x=−70 and +70 mm; 101.9 mm clear between 38.1 mm members |
| `base_post_center_left`, `base_post_center_right` | Corresponding center supports; preserve direct header bearing |
| `base_post_outer_left`, `base_post_outer_right` | Outer supports; retain full modeled header-bearing depth |
| `base_rail_service_lower_left`, `base_rail_service_lower_right` | s=1031.1–1069.2 mm; upper face at s=1069.2 mm |
| `base_rail_service_upper_left`, `base_rail_service_upper_right` | s=1219.2–1257.3 mm; lower face follows the horizontal panel seam |
| `base_rail_bottom_left`, `base_rail_bottom_right`, `base_rail_top` | Remaining edge rails; use their individual exported bounds |
| `lumber_leg_left`, `lumber_leg_right` | Retained independent legs, four bolt axes per side |
| `clip_angle_base_left`, `clip_angle_base_right` | Direct outer rim/header connections; no plywood base gussets |

The four service rails are single 2x6 members with 38.1 mm face width and
139.7 mm depth. Each spans from its outer rim to its corresponding center
principal. The removed `base_principal_left_1/2`, `base_principal_right_1/2`
and matching posts are not part of this layout.

Use the drilling PDF's named pages for `main_lower_left`, `main_lower_right`,
`main_upper_left`, and `main_upper_right`. Lower-panel rows measure down from
the TOP edge; upper-panel rows measure up from the BOTTOM edge. Horizontal
coordinates start at each panel's own left edge. Use the separate rim and leg
pages for structural bolts: their grain directions and end datums differ.
LED7 is in the lower panel despite lighting an upper-panel hold. Do not mirror
front-view coordinates while drilling from behind.

## Purchasing schedule

The verified current inventory contains 24 wood/plywood parts, 87 panel/kicker
screws, eight leg bolts, 24 ML24Z angles and 144 SDS25112 screws. No inserts are
installed. Electrical visualization contains 132 LEDs and 131 inter-LED wire
segments; this does not count the controller, extensions or unused tail as
purchased components. Geometry checks pass. The [coupled frame/panel diagnostic](horizontal-frame-diagnostic.md)
is complete; structural qualification remains pending.

| Item | Current specification or action | Quantity status |
| --- | --- | --- |
| Lumber | Grade-stamped Douglas Fir–Larch No. 2 or better, dry solid-sawn stock; exact revised cutlist sizes | Eight 2x6 boards and one 2x10 board; lengths and allocation below |
| Main and kicker plywood | APA-trademarked PS 1 Structural I plywood, 23/32 Performance Category, 48/24 span rating, square edges, Exposure 1 or Exterior | Four sheets provisionally; four 1219.2 mm squares and two 1219.2 × 225 mm kicker panels |
| Panel and kicker screws | SPAX XFT08P-2000, #8 × 2 inches, as currently modeled | 87 total panel/kicker screws |
| Commercial angles | Simpson ML24Z at the revised station locations | 24 angles |
| Angle screws | Simpson SDS25112, 1/4 × 1-1/2 inches; purchased separately from angles | 144 screws; six per modeled ML24Z |
| Retained leg bolt assemblies | Eight complete through-bolt stacks: bolt with head, near washer, far washer and nut | Eight bolts, eight nuts, sixteen washers; verify each exported length and product designation |
| MoonBoard LEDs | Owned V5 kit; three 50-LED strings with original controller, supply, extension and boost cables | Do not repurchase; inspect supplied components |
| Threaded inserts and machine screws | Separate removable-panel development selection | None installed or approved for purchase by this draft |
| Holds and matching hold bolts | Inventory owned hold sets and supplied bolts before ordering; match the selected setup and individual hold recesses | Final installed hold count and length-by-length bolt list require kit inventory |
| Hold T-nuts and retention screws | Existing project selection: Escape three-hole screw-in 3/8-16 T-nuts; confirm supplied product and offcut fit | 142 positions: 132 main + 10 kicker; retention-screw specification/count awaits product instructions |

These are selected purchasing specifications, not verified delivered materials.
Record the lumber grade/species stamps and panel trademarks, and measure actual
cross sections and panel thickness when received. Do not substitute SPF,
Stud-grade lumber, OSB, tongue-and-groove panels or a different plywood class
without checking the resulting geometry and resistance. No manufacturer SKU or
store availability is assumed.

[WWPA dimension-lumber grades](https://www.wwpa.org/western-lumber/structural-lumber/dimensional-lumber/)
and the [AWC NDS Supplement](https://awc.org/resources/2024-nds-supplement/)
provide the lumber design-reference route. The
[APA Panel Design Specification](https://www.apawood.org/guides-tools-training/technical-document-library/technical-guides/panel-design-specification/)
provides panel mechanical properties and design capacities. Those directional
panel properties do not automatically define a complete three-dimensional
orthotropic material model. The existing isotropic FEA has not been changed to
represent these purchased materials and does not qualify them.
Do not purchase unspecified bolt lengths from the assembly count alone.

## Sheet sizing and cut allowance

Plan provisionally for one full 1219.2 × 1219.2 mm main panel per sheet: four
sheets, with the two 1219.2 × 225 mm kicker panels cut from suitable offcuts. The
exported thickness is 18.25625 mm for all six panels. This is a conservative allocation concept,
not an unconditional claim that any nominal 4 × 8 sheet fits. Measure the usable
width and length of every purchased sheet, including edge damage and squareness.
A sheet sold as 4 × 8 may be undersized or require trimming.

Each main square needs at least 1219.2 mm of sound usable material in both
finished directions. If the width is exactly 1219.2 mm, both factory edges must
be usable without width trimming. Account separately for the actual saw kerf,
end trimming and the remaining kicker blank. Two exact 1219.2 mm squares cannot
be crosscut from an exactly 2438.4 mm sheet with a nonzero separating kerf. Buy
verified oversized stock if trimming is needed; do not shrink panels or alter
the hole grid to make stock fit. Record sheet thickness as measured, rather
than treating 23/32 Performance Category as a guaranteed 18.25625 mm thickness.

## Timber stock allocation from the generated cutlist

Purchase **two 2x6 × 12 ft, four 2x6 × 10 ft, two 2x6 × 8 ft, and one
2x10 × 12 ft**. This allocation covers all 18 lumber members in the generated
cutlist without joining pieces. It is not a claim of optimum waste or retail
availability. Use the selected DF-L grade for every board.

Allowances are an analyst-selected 3.2 mm saw kerf per released blank plus
12.7 mm total end-trim allowance per board. Confirm these match the saw and
usable stock before cutting. Required lengths below include those allowances;
remaining stock is relative to exact nominal board length, not guaranteed
usable offcut. Rounded displayed lengths do not replace the CSV precision.

| Board | Members cut from that board | Required usable length | Nominal remainder |
| --- | --- | ---: | ---: |
| 2x6 × 12 ft, left | `base_principal_center_left` 2532.626 mm + `base_rail_service_upper_left` 1092.050 mm | 3643.776 mm | 13.824 mm |
| 2x6 × 12 ft, right | `base_principal_center_right` 2532.626 mm + `base_rail_service_upper_right` 1092.050 mm | 3643.776 mm | 13.824 mm |
| 2x6 × 10 ft, left rim | `base_side_left` 2608.024 mm | 2623.924 mm | 424.076 mm |
| 2x6 × 10 ft, right rim | `base_side_right` 2608.024 mm | 2623.924 mm | 424.076 mm |
| 2x6 × 10 ft, left leg | `lumber_leg_left` 1807.972 mm + `base_rail_bottom_left` 1092.050 mm | 2919.122 mm | 128.878 mm |
| 2x6 × 10 ft, right leg | `lumber_leg_right` 1807.972 mm + `base_rail_bottom_right` 1092.050 mm | 2919.122 mm | 128.878 mm |
| 2x6 × 8 ft, lower service | `base_rail_service_lower_left` + `base_rail_service_lower_right`, each 1092.050 mm | 2203.200 mm | 235.200 mm |
| 2x6 × 8 ft, top | `base_rail_top` 2362.200 mm | 2378.100 mm | 60.300 mm |
| 2x10 × 12 ft, base | `base_header` 2438.400 mm + all four `base_post_*` blanks, each 186.900 mm | 3214.700 mm | 442.900 mm |

The two center-principal boards have only about 13.8 mm beyond the allocated
kerf and end trim. If their usable lengths or defects prevent that allocation,
buy longer single boards or separate rail stock; do not shorten a member. Lay
out the full profiles, including sloped end cuts, before crosscutting blanks.

## Hold hardware: inventory before purchase

The 132 LED positions are not the complete hold-hardware count: the model also
has ten kicker hold positions, giving 142 potential T-nut locations. Holds,
installed T-nuts, their retaining screws and hold bolts are not represented by
complete current CAD bodies and are excluded from its modeled mass estimate.

Earlier [materials records](materials.md) identify an owned Mini 2025 hold bundle
and Escape three-hole 3/8-16 T-nuts. Reconcile the actual received kit and loose
hardware before buying replacements; confirmed ownership of the V5 lighting kit
does not establish that the complete DIY panel/hold package was purchased.
The [current complete DIY kit](https://us.moonclimbing.com/products/mini-moonboard-2025-diy-kit)
includes panels with T-nuts, holds and bolts, whereas a separate hold bundle has
different contents. Its listing contains inconsistent metric/imperial wording;
M10 and 3/8-16 threads are not interchangeable.

The project's current nominal hold bore is 11.1125 mm for the selected Escape
route, subject to actual fit and product installation requirements. Moon's
[generic hardware guidance](https://moonclimbing.com/build-your-moonboard)
uses a different 13 mm / half-inch T-nut bore. Do not change drill sizes without
selecting and checking the actual T-nut. Its generic imperial bolt packs include
2.5-inch and 3.5-inch bolts for PE/PU holds and 3.5-inch bolts for wood holds;
these are pack descriptions, not a verified per-hold schedule for this build.
Determine each hold's bolt length, engagement and rear clearance individually,
including conflict with cables and timber. Use the
[hold installation record](v1-hold-installation.md) to record lengths and setup
orientation. T-nut retention screws and any hold anti-rotation screws are
additional items, separate from the 87 panel/kicker attachment screws.

## Assembly sequence to develop and verify

1. Label `base_header`, the four retained support posts, both center principals,
   both outer rims, the four service rails, the remaining edge rails and both
   legs. Reconcile the released cutlist, machined members, connection schedule and
   hardware products. Mark every member using its exported identity. Preserve
   the center service corridor and independent rails; do not laminate members.
2. Make the reviewed timber cuts and open-front cable grooves before installing
   panels. Groove locations and residual sections must match the analyzed model.
   CAD screw cylinders are geometry assumptions, not manufacturer pilot-drill
   instructions. Use the selected fastener's installation requirements.
3. Position the header and its four retained posts, then the outer rims and
   separated center principals. Fit the bottom/top rails, then the lower and
   upper service-rail pairs at the `s` bounds above. Install the matching
   `clip_horizontal_*` station connections from `connections.csv`; lower-service
   and upper-service brackets have different orientations. Keep their screws
   remain accessible. Install all eight complete leg bolt stacks with both ends
   accessible. Confirm bearing and tool access before concealing any connection.
4. Test the owned LED strings using the manufacturer's instructions. Lay out the
   front-open groove routing before closing it with panels. Route LED1 toward
   A1 and the separate boost extension from PWR1 toward the end of string two.
   Protect the harness from screws and sharp groove edges without pinching it
   between plywood and timber. Keep connectors accessible for panel removal.
5. Fit panels and insert the LEDs flush with their climbing faces, following
   A1–A12, B12–B1 and the alternating columns through K12. Verify each adjacent
   cable can follow its complete route without tension. The user's approximate
   304.8 mm bulb-base spacing is a provisional length budget, not a guaranteed
   minimum. Check the shortest supplied segment, bends and connector transitions.
6. Locate the `horizontal_panel_lower_*` and `horizontal_panel_upper_*` axes
   using `connections.csv`, rather than evenly spacing them by eye; the model
   shifts some screws to clear service holes. Install all other panel and kicker
   screws at their own revised axes. Complete the
   manufacturer startup check and inspect for pinched cables. A panel-removal
   trial should demonstrate which connectors must be released and how the
   wiring remains supported.

The [LED reference](led-wiring-reference.md) distinguishes the owned three-string
kit from older two-string instructions. Its [measurement record](led-wiring-reference.json)
documents the approximate cable pitch and remaining physical unknowns. The
published spare-count discrepancy does not justify cutting the supplied tail.

## Removable panels and inserts

Develop an insert-and-machine-screw option for both face and kicker panels where
receiver geometry and connection resistance support it. Reserve suitable space
without drilling insert pilots into the ordinary-screw candidate. An insert
selection must establish installation bore/depth, remaining wood around grooves
and edges, pullout and repeated-removal performance, machine-screw engagement,
and head bearing through the plywood. The coupled panel model must use the
selected attachment behavior; an insert is not automatically equivalent to a
wood screw. A worn-hole repair also needs a separate assessment of the actual
remaining wood.

## What prevents construction release

The modeled frame and represented hardware weigh **167.469 kg (369.205 lb)**
at the assumed densities. Holds, their T-nuts and bolts, lights, wiring and other
unmodeled equipment are excluded; this is not a shipping or complete installed
weight. The viewer identifies these exclusions.

The [current floor screen](../fea/results/horizontal-service-floor-v1.json.gz)
credits four posts and two leg feet, excluding kicker-edge support. All 1,296
sampled cases were feasible at each assumed friction coefficient 0.2 and 0.4.
At 0.1, 720 cases provably exceeded the circular friction bound; another 43
failed only the conservative polygon approximation and remain inconclusive.
These finite rigid-floor results neither measure the actual coefficient nor
qualify a compliant, unanchored frame.

The coupled diagnostic's 1,000 N/mm spring cases reached 21.811 mm maximum
panel displacement at F10 under the doubled 250 lb scenario. The signed
[panel-fastener screen](provisional-connection-assumptions.md) flags two probes
above unadjusted withdrawal references. Verify attachment behavior and material
properties before treating either displacement or local stress as a design
pass/failure. The [assumption handoff](provisional-design-assumptions.md)
defines that independent review.

The revised rail spans and cable grooves have a completed conditional
[coupled frame/panel diagnostic](horizontal-frame-diagnostic.md); applicable
material, residual-section and resistance qualification remains open. Earlier infill-panel reactions cannot
qualify this arrangement. Panel screw withdrawal/head bearing and commercial
angle screw-group resistance still need comparison against current demands.
The unanchored frame needs the applicable floor and stability evidence; a rigid
floor feasibility calculation does not establish frame stiffness or joint strength.
Finally, the owned harness must fit the modeled grooves with measured slack and
accessible connectors. Until these specific items are resolved, this document
remains a planning draft.
