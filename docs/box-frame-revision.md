# Box-frame revision

This revision implements the user's September 2026 box-frame direction.
The current CAD, viewer, schedules and tests use `mini_moonboard/box_frame.py`.
Earlier rail-and-spacer drawings, joint dimensions and FEA results do not
describe this assembly. This remains a reviewable design, not a build release.

## Dimensions and layout

- Supports: two glued 19.05 mm / 3/4 in plywood layers, 38.1 mm / 1.5 in
  finished nominal thickness. Birch plywood is assumed. Climbing panels
  retain their separately specified 18 mm thickness.
- Side walls extend 304.8 mm / 12 in perpendicular behind the climbing
  plywood's support surface. Their front edges are flush with the climbing
  face, so the side-wall blank is 322.8 mm deep including panel thickness.
- Main panels retain the controlled 2438.4 mm square layout, 40-degree
  inclination, unchanged T-nut/LED grid, and 225 mm kicker.
- The top closure sits between the walls; the top panel-bearing strip
  completes its front rim. The rear remains open for service access.
- Exterior legs are continuous hockey-stick profiles cut twice and glued.
  This replaces the separate knee plate and its bolts. The upper leg runs
  from row 8 toward row 10, with a rounded knee and an initially 180 mm wide
  member. Both feet are extended then cut at the floor for full-width bearing.
- The kicker support surface is aligned consistently behind its climbing
  face: the visible face remains at Y=-18 mm, meeting the inclined face.
  Floor-reaching cheeks and broad-face splice plates join the kicker to the
  main side walls. Top and bottom kicker strips support its face screws.
- Three rear transverse members meet bearing seats through-bolted to the
  side walls. Six normal ribs connect the central panel-seam supports to
  these members. No cross member spans the lower legs in climber space.

## Panel screws

Each main panel has 24 front-installed screws following its four edges,
25 mm / 0.98 in inboard. Seven screws follow each horizontal edge and five
additional screws follow each vertical edge. That includes the topmost
edge and both sides of the horizontal and vertical panel seams.

The initial regular pattern slides individual screws along the same edge
to keep at least 28 mm from every hold/LED bore centre. This clears the
40 mm relief holes in the backing strips. Adjacent screws on each straight
edge are checked to remain within 250 mm. This is a provisional design
pattern, not a manufacturer-rated fastening schedule.

Main-panel screws are nominal #10 x 50.8 mm / 2 in, with 32.8 mm penetration
into the 38.1 mm backing. CAD includes 5.2 mm face clearance, a 3.2 mm
backing pilot and a matching 10 mm countersink. Screw dimensions and pilot
size still require a selected structural screw product and material basis.

The connection CSV names every fastener's receiving parts, start coordinate,
axis, diameter and length. The cut CSV counts separate 19.05 mm laminations.
Leg blanks are bounding rectangles: the STEP/profile drawings control their
non-rectangular shape. Actual stock, kerf and adhesive procedure remain inputs.

## Joints and analysis limits

Leg bolts pass through one wall and one leg: 76.2 mm wood grip, two nominal
2 mm washers, a 9 mm nut, and a 95.25 mm / 3.75 in under-head bolt length.
The nominal tip projects 6.05 mm past the nut. Seats use the same stack.
Washer envelopes are 25.4 mm OD; adjacent bolts are spaced to clear them.

Some box-end, batten-end and rib joints currently use screws into plywood
edges. Their strength is unverified. Geometric engagement does not establish
withdrawal resistance, splitting resistance or fatigue performance. The
[APA Panel Design Specification](https://www.apawood.org/guides-tools-training/technical-document-library/technical-guides/panel-design-specification/)
describes capacities for qualified structural panels; it does not establish
properties for the purchased C-3 birch material.

Checks cover valid solids, 38.1 mm laminations, true frame depth and angle,
flat foot bearing, pairwise wood overlap, hardware-to-wood and
hardware-to-hardware interference, joint contact, screw receiving material,
perimeter coverage and nominal bolt projection. A passing clearance screen
is only a geometry result. Unanchored uplift, sliding, racking, material
strength, glue and connection flexibility need engineering evaluation.

The earlier fixed-foot beam FEA is historical. Its 169–351 mm displacement
values cannot be applied to this box revision. Current stability screening
uses the current CAD mass and the extreme edges of actual floor-contact
faces; the reported minimum mass is not a ballast prescription.

## Build sequence for review

1. Confirm plywood thickness/grade and adhesive; transfer the per-layer cut
   schedule and profile geometry, allowing saw kerf and clamping access.
2. Laminate matched walls, legs, strips, seats, ribs and cheek splices.
3. Assemble the top and side walls; fit panel-bearing strips and seam supports.
4. Fit rear cross members on their seats; attach the normal seam ribs.
5. Splice the floor-reaching cheeks to the side walls and fit kicker backing.
6. Bolt the exterior legs to the walls and verify coplanar full foot bearing.
7. Install panels from the climbing face using the perimeter screw schedule.
8. Fit the received T-nuts, hold-specific bolts and V5 LEDs; verify access
   through the backing relief bores and route wires behind the frame.
9. Resolve the documented structural/connection and unanchored stability
   findings before any climbing or proof loading.

The source video was reviewed at 0:53–1:08. Its images are local references;
the 12-inch depth and lamination specification are user inputs, not inferred
measurements from the footage.
