# MiTek B66 / Home Depot UB66 drawing follow-up

Checked 2026-09-20. This is factory-bracket evidence for a **nominal fit
trial**, not a selected connector, structural rating, purchase order, or
drilling release. No manufacturer was contacted or part purchased.

[MiTek's Home Depot conversion chart](https://images.thdstatic.com/catalog/pdfImages/2f/2f1009db-047c-4da8-a283-bcda2c494ebe.pdf)
maps retail `UB66`, Home Depot SKU `1005468446`, to MiTek `B66`.
[Home Depot lists that exact retail model](https://www.homedepot.com/p/313507617).
The [MiTek B-series page](https://www.mitek-us.com/products/angles-straps/framing-angles-and-plates/b/)
links an official [B66 three-view DXF](https://www.mitek-us.com/wp-content/uploads/files/Drawing%20Library/B66_3view.dxf).
The manufacturer chart's competing-brand reference number is not a
substitution authorization. Local stock was not verified.

The DXF declares millimeter model units (`$INSUNITS = 4`) and has four
circle entities, two per leg. Its two pairs are approximately 101.344 mm
apart along their respective views; their width centerlines are nominally
19 mm from either side of the roughly 38-mm-wide plate. Relative to the
free-end outlines, the hole positions are approximately **1 and 5 in.**
from each free end. These are extracted *CAD geometry*, not printed factory
dimensions, tolerances, wood-hole or saw instructions. The PDF and catalog
do not establish delivered hole-position variation, bend radius, or a
receiving inspection limit. The brace's nominal reach is 6 in. along each
leg, compared with B88's 8 in.; its plate is 1½ in. wide rather than 2 in.

[ICC-ES ESR-3455](https://www.mitek-us.com/wp-content/uploads/files/pdf/Code%20Evaluation%20Reports/esrESR-3455.pdf)
Table 3 specifies four ⅜-in bolts total, two per leg, at least ASTM A307
Grade A with minimum bolt bending yield strength 45,000 psi, and **3 in.
minimum actual receiving-member thickness** for B66. Section 3.29.2
requires qualifying wood with specific gravity at least 0.50 unless a
product-specific exception applies. Section 3.29.1 and Table 29 identify
12-gauge ASTM A653 Structural Steel Grade 40, G90, with **0.099 in.
minimum base-steel thickness**. These are conditional inputs for a separate
wood/bolt/formed-bracket calculation, not the capacity of an installed
MoonBoard joint.

Table 3's B66 F1/F2 loads, 710/335 lbf, have `C_D = 1.6`. The report
explicitly forbids applying or adjusting them to another load duration.
Do not divide them by 1.6 to invent a climbing capacity. Its installation
and load directions also do not rate an arbitrary combined force, moment,
separation, or gap in the board's center assembly. A fit trial must first
check the full factory-hole pattern against the actual kerf-right panels,
66 protected screw axes, neighboring members, minimum 3-in receiver, bolt
stacks, edge/end geometry, and disassembly path. No fabrication follows
from this drawing.
