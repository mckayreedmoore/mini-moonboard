# Separate backing-joint development candidate

`joint-development`, 2026-09-06. **Geometry proposal, not a selected product
schedule, FEA-validated assembly or construction approval.** The original
`2x8-foot100` remains intact. This candidate changes the complete rib-to-batten
and rib-to-crossmember layout together; it does not deepen the perimeter rims
or change the legs, footprint, climbing panels or panel screw locations.

## Geometry to inspect

| Change | Metric | Imperial |
| --- | --- | --- |
| Twelve solid-stock rib blanks, grain along board slope S | 63.5 X × 89.95 N × 300 S mm | 2.5 × 3.5413 × 11.811 in |
| Two vertical seam battens, ripped from graded 2×8 stock | 165.1 mm wide × 38.1 mm thick | 6.5 × 1.5 in |
| Seam rib centres | X = ±54 mm | ±2.126 in |
| Twelve custom rear angles | 80 × 80 × 6 mm, 180 mm long | 3.150 × 3.150 × .236 in, 7.087 in long |
| Rib through-bolt nominal length / diameter | 88.9 / 9.525 mm | 3.5 / .375 in |
| Rib through-bolt nominal timber-plus-steel grip | 69.5 mm | 2.736 in |

The rib blank is **not** obtainable by laminating ordinary 2× stock and calling
it solid lumber. One possible cutting envelope is dressed 4×6 solid stock,
ripped in both cross-grain dimensions. Actual obtainable dimensions, structural
grade/species, moisture and machining effects need confirmation. No product
resistance is assigned yet. The two-layer plywood legs are unchanged and retain
their unresolved material and composite-action assumptions.

Front rib screws move to each rib's S centre, except the row-1 and row-3 left
seam screws move 30 mm uphill to clear existing backing reliefs. They enter
side grain. Their current
4.826 mm diameter, 88.9 mm long generic envelope remains provisional: it is
**not** a claim that a particular manufacturer's screw has been selected.
The existing panel screws still drive from the climbing face into the backing;
the separate rib screws are installed through the front of the battens before
the climbing panels are fitted. Service removal therefore requires that panel
access, not an imagined unobstructed tool corridor through the finished face.

Rear rib bolts run across X at mid-depth N = 83.075 mm. Their stations are
S ±35 mm, except the left seam ribs use S ±70 mm. The stagger separates opposing
seam nuts and their socket envelopes. Rear beam bolts move outward with the
angle; their old holes are removed by rebuilding the crossmembers before
drilling. No extra abandoned holes are intended in new stock.

The enlarged left seam ribs intersect the existing vertical wiring corridor
unless a chase is cut. The candidate explicitly cuts an open front-edge chase
where required: 15 mm wide around the wire centre and back to N = 56 mm. It
provides 2 mm lateral and 4 mm rear allowance around the existing 11 × 2 mm
straight corridor at N = 50–52 mm. The **net notched shape**, reduced front
bearing area and local fastener distances must be used in subsequent analysis.
This is not a full harness layout or a bend-radius qualification.

## Manufacturer screen, not a capacity transfer

Page 47 of the [2025 Simpson fastening technical guide](https://www.strongtie.com/resources/literature/fastening-systems-technical-supplement)
gives the SDWS16312 perpendicular-load spacing screen discussed in
[the prior detail study](rib-batten-detail.md): 101.6 mm end and 25.4 mm edge
distances. The enlarged block provides at least 120 mm screw end distance; the wider
seam batten provides 28.55 mm outside-edge distance at the seam screw. This
removes the prior simple rectangular-distance obstacle, **not** the need to
select and check a product for both connected members, combined loading,
effective threads, head seating, installation and any notches/reliefs. Do not
transfer SDWS capacities to the generic screw envelope. In particular, the
SDWS16312's [2025 catalog](https://www.strongtie.com/resources/literature/fastening-systems-catalog)
(page 58) thread/head diameters are 5.461/11.43 mm, larger than the
generic 4.826/10 mm shaft/head envelopes; a product substitution requires new
hole, countersink and clearance checks, not a label change.

Independent review identified only 20.1378 mm screw-axis-to-relief-boundary
clearance at the first centred row-1/row-3 left seam positions. Moving those
screws 30 mm uphill removes that known obstacle. Regression checks now require
at least 25.4 mm from every front rib screw axis to the modelled 40 mm backing
reliefs and retain a 25 mm minimum crossed-bore ligament screen. These are
necessary project geometry checks, not manufacturer permission to treat an
internal hole or chase as an exterior edge. The left seam rib's chase edge is
27.3 mm from its screw axis; its actual net-section effect remains to be checked.

Custom steel angles are sharp-corner CAD envelopes, not rated catalog products.
Inside bend radius, fabrication method, hole tolerances, steel specification,
washer/head/nut products, corrosion protection and bolt bearing/tear-out remain
design work. No glue or tightening-friction capacity is credited to these joints.

## Checks and next gates

`uv run pytest tests/test_joint_frame.py` checks every station using actual CAD:
solid validity, body and hardware overlaps, receiving members and connection
graph, nominal socket/withdrawal envelopes, LED bodies and straight wiring
corridors, floor seating, unchanged baseline inventory, shaft clearance and
removal of superseded bores. The reused socket envelope is 36 mm diameter with
25 mm approach; these are declared tool assumptions, not measured tools.

Passing these tests does not establish material resistance, connection stiffness,
fatigue performance or manufacturing tolerance. Next: select actual fasteners
and steel detail; check full edge/end/spacing rules including reliefs; qualify
interface demands and contact; then compare this actual new geometry using
explicit connector/contact behaviour. The existing foot100 FEA does **not**
apply unchanged to these larger blocks, wider battens and relocated joints.

## Implementation review record

Independent design/correctness, testing and software-architecture reviews
checked this candidate. Findings corrected: the two relief-adjacent screw
positions; misleading generic-versus-product screw diameter wording; tests that
could miss blocked bolt bores; and tests that could pass after connections were
omitted. The final testing rereview confirmed the exact 220-connection inventory
and member-pair checks resolve the omission gap. Correctness and architecture
reviews reported no remaining substantial findings. These are implementation
reviews, not professional structural sign-off.

The seven geometry tests passed in 87.30 seconds before the final inventory
assertion strengthening; the strengthened inventory test was rerun separately.
Repository lint and whitespace checks passed. Candidate FEA and actual product
checks remain unfinished, as listed above.
