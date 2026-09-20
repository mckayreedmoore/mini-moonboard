# B66/UB66 rear-Y center trial: rejected nominal pose

This is one installed-geometry screen, not a connector selection, capacity,
cut list, or drilling release. The companion JSON is reproduced by
`scripts/hardware_first_b66_rear_y.py --output
docs/bolted-candidate-prototypes/hardware_first_b66_rear_y.json`.

The kerf-right panels and their outlines stay fixed. One solid center post
backs both kicker inner edges. A 76.2-mm-thick solid header sits above it;
the two center principals are widened to 88.9 mm and butt onto the header.
One B66 has its vertical flange at the post's accessible rear Y face and
its horizontal flange under the header. One B66 at each principal has its
vertical flange at the rear Y face and its horizontal flange atop the same
header. There are three factory braces, four 3/8-in through bolts per brace,
and no lap joint or custom steel. This is distinct from the earlier rejected
outer-X-face upper B66 pose.

The nominal [MiTek B66 DXF](https://www.mitek-us.com/wp-content/uploads/files/Drawing%20Library/B66_3view.dxf)
circle centers are screened at approximately 25.4 and 126.744 mm from each
leg's free end. The approximately 10.3-mm DXF circle and illustrative
2.66-mm sheet are CAD envelopes, not drill sizes, delivered tolerances, or
a verified bend radius. The [drawing follow-up](mitek-b66-drawing-followup.md)
records the extraction and retail UB66/B66 cross-reference.

The pose fails. Both upper braces' full nominal through-bore paths leave
the sloping principal wood. At each principal, the free-end-side vertical
path has **8,113.368 mm³** outside its assigned wood and the bend-side path
has **1,027.780 mm³** outside. Their vertical flanges also lack a continuous
flat rear bearing face in this idealized alignment. The one-piece header,
extended rearward to Y = -335.1 mm for both seats, overlaps each fixed side
member by **471,575.581 mm³**. Each widened principal overlaps its bottom,
lower service, and upper service rails by **135,193.278 mm³** apiece.
Those overlaps would require changes outside this bounded pose. The ideal
header blank envelope is **2435.225 × 299.1 × 76.2 mm**, and the post is
**184.15 × 139.7 × 238.9 mm**; one-piece stock grade and availability
remain unverified. These are bounding sizes, not procurement or cut data.

All 66 protected panel/kicker screw cylinders still intersect their assigned
receiving timber, and both kicker inner edges have post backing. The 12
old frame axes are retained as protected paths. This nominal model finds no
contact between the new plates or bores and those axes, the panels, or the
66 screws. It finds no distinct-bracket plate collision or bore crossing.
Those clearances do not repair the missing principal wood or adjacent-member
overlaps. The old frame axes are carried as geometry; their revised
connection strength is not established.

[ESR-3455](https://www.mitek-us.com/wp-content/uploads/files/pdf/Code%20Evaluation%20Reports/esrESR-3455.pdf)
requires at least **3 in. actual receiving-member thickness** and four
3/8-in ASTM A307 Grade A or better bolts for B66. The nominal width/depth
envelopes here meet that thickness floor; the full upper bore support does
not. Its B66 F1/F2 values are for `C_D = 1.6`, and the report forbids
conversion to another duration. Ordinary-duration resistance needs a
separate analysis of wood, bolts, load path, and the formed B66 steel. The
report identifies ASTM A653 Structural Steel Grade 40 with at least
**0.099 in. base-steel thickness**. No table value is claimed for this
center assembly.

Delivered bracket geometry, bolt head/washer/nut grip and tool sweep,
edge/end-distance design, access during assembly and removal, wood grade,
and local stock are unverified. Stop at this failed pose; no drilling is
approved.
