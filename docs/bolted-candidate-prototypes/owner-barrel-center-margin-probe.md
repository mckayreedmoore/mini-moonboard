# Center-principal/header barrel washer-seat margin probe

This bounded Track B CAD sensitivity covers only the left and right
`clip_split_base_center` principal/header duties, with two vertical bolts and
two X-axis barrels per side. It reads the unchanged kerf-right whole-timber
model, exact X = ±180 mm center posts, separate kicker backers, all 66
panel/kicker screw axes, 12 old frame-bolt axes, and panel outlines. It does
not alter the six-duty barrel viewer, assembly, or other four barrel duties.

The header underside seat remains flat at Z = 238.9 mm. Each trial washer is
centered on its bolt; no recess, backer trim, edge move, or panel move is
assumed. The header rear Y edge is −175.7 mm and the fixed backer rear edge
is −124.9 mm. Let `d` be washer OD, `y1` the rear row and `y2` the forward
row. For a common positive reserve `m`, the three seat conditions are:

```text
y1 >= -175.7 + d/2 + m
y2 - y1 >= d + m
y2 <= -124.9 - d/2 - m
```

Thus `3m <= 50.8 - 2d`. The former 25.4 mm washer envelope consumes the
entire span: Y = −163.0/−137.6 mm and `m = 0`. Moving those rows alone
cannot create positive edge, washer-pair, and backer reserve with that OD.

| Washer OD | Y rows, rear / forward | Each Y reserve | Washer-seat screen |
| ---: | ---: | ---: | --- |
| 22.0 mm | −162.433 / −138.167 mm | 2.267 mm | Positive seat reserve |
| 23.0 mm | −162.600 / −138.000 mm | 1.600 mm | Positive seat reserve |
| 24.0 mm | −162.767 / −137.833 mm | 0.933 mm | Positive seat reserve |
| 25.4 mm | −163.000 / −137.600 mm | 0.000 mm | Fails positive reserve |

For a 22.0 mm OD and at least 1.0 mm in each of the three Y gaps, the
**seat-only feasible interval** is `−163.7 <= y1 <= −159.9` mm, with
`y1 + 23.0 <= y2 <= −136.9` mm. The balanced, CAD-checked point is inside
that interval. The interval itself is an exact seat inequality, not a claim
that every continuous pose within it passed 3D CAD.

At each table pose, CAD rebuilt the full nominal 127.0 mm bolt shaft and
7.5 mm bore, 16.002 mm × 10.0076 mm barrel body and cross bore, flat washer,
11 mm head, and both 20 mm × 40 mm access cylinders. Both principal/header
stations retain complete intended core paths (minimum fraction 1.0000000);
each bolt bore intersects its barrel bore by 408.380 mm³. There are no
greater-than-1 mm³ intersections among the two rows, with unrelated whole
timber/backers, or with the protected 142 T-nuts, 142 provisional rear hold
paths, 132 lights, 131 wires, 66 panel screws, and 12 old frame bolts.
Washer seats also remain within the header's X and front Y edges. The same
finite-volume tolerance applies to all reported collision families;
contact/tangency and sub-threshold interference are not a tolerance allowance.

The **full nominal 5 in bolt path fails** a separate receiving-wood check.
Its modeled tip is at Z = 364.249 mm, 59.249 mm beyond the barrel thread
axis. At the 22 mm washer pose, each rear-row full bore has 620.281 mm³
outside the header/principal wood and its tip center is outside the
principal. Both forward-row bores are fully contained and their tip centers
are inside. The rear-row uncontained volumes rise to 629.056, 637.831, and
650.116 mm³ for the 23, 24, and 25.4 mm washer trials. The washer-seat
opportunity therefore **does not qualify the complete modeled joint**.

The failure spans the bounded 22–25.4 mm washer range, not just the four
balanced samples. Even with zero Y reserve, the most forward rear row
permitted by two 22 mm seats is Y = −157.9 mm. At the nominal tip height
Z = 364.249 mm, the principal's rear wood limit is Y = −150.652 mm. The
tip-center shortfall is at least **7.248 mm**; larger ODs or positive reserves
move the rear row farther away. Thus changing only these Y rows and washer
OD cannot receive the full inherited 5 in rear bolt path.

## Nominal bolt-length continuation at the 22 mm seat

The balanced 22 mm seat stays at Y = −162.433/−138.167 mm, with the inherited
1.651 mm trial washer thickness. Each nominal length rebuilds the complete
shaft and 7.5 mm bore; the barrel, head, washer, access, pair, protected,
and unrelated-wood checks are rerun. A **provisional 10 mm nominal tip
overrun past the modeled thread axis** is required. That is about 5 mm past
the nominal barrel outer radius and is only a geometry allowance; actual
threaded span and engagement remain unknown.

| Nominal bolt | Tip past axis | Rear bore outside | Rear shaft outside | Geometry screen |
| ---: | ---: | ---: | ---: | --- |
| 4.0 in | 33.849 mm | 0 mm³ | 0 mm³ | Four paths contained; allowance met |
| 4.5 in | 46.549 mm | 77.114 mm³ per side | 51.387 mm³ per side | Rear breakout |
| 5.0 in | 59.249 mm | 620.281 mm³ per side | 444.645 mm³ per side | Rear breakout |

All three lengths still intersect the cross bore by 408.380 mm³, and the
full hardware/bore/access screens found no greater-than-1 mm³ protected,
unrelated-wood, or other-row hits. The **4.0 in nominal length is the only
tested geometrically plausible length** at this seat. The necessary
geometric window from 10 mm axis overrun and the rear bore edge is
77.751–108.491 mm (3.061–4.271 in). Only the 4.0 in sample was CAD-checked
inside that continuous window; it is not a product selection or a claim of
thread engagement.

The [Home Depot Everbilt 800666 listing](https://www.homedepot.com/p/204633306)
and [Lowe's Hillman 190055 listing](https://www.lowes.com/pd/1000897796)
identify nominal 1/4-20 × 4.5 in retail leads. The Lowe's listing says
“Full Thread: No”; neither listing supplies a usable threaded-span limit
for this barrel position. The 4.5 in nominal path also breaks out here,
so neither listing qualifies a bolt for this pose. Retail availability of
the 4.0 in candidate is addressed below.

## Ordinary-store 4 in bolt leads and thread reach

[Lowe's Hillman 883149](https://www.lowes.com/pd/3024614) is listed as
1/4-20 × 4 in and “Full Thread: Yes.” The listing also calls it a tap bolt,
but its generic overview mentions a smooth shoulder and its grade is only
“All-purpose.” [Lowe's Hillman 811522](https://www.lowes.com/pd/1000381585)
is listed as 1/4-20 × 4 in, A307, and “Full Thread: Yes,” while its overview
explicitly describes a *partially* threaded shank. These contradictory
retailer fields require inspection of the exact delivered product; neither
listing establishes a controlled complete-thread span or bolt resistance.
[Home Depot Everbilt 804302](https://www.homedepot.com/p/204283058) is a
1/4-20 × 4 in *fully threaded machine-screw* lead with a combo round head;
its head, grade, and strength have not been substituted into the hex-head
CAD trial. It is not a selected equivalent.
The common [Hillman 190052](https://www.lowes.com/pd/1000897808) and the
listed [Grade 5 Hillman 200045](https://www.lowes.com/pd/5005390807)
are both marked “Full Thread: No.” Grade 5 alone therefore does not make
the modeled center connection usable.

At the balanced 22 mm washer pose, the 4 in tip projects 33.849 mm past the
assumed barrel thread axis. To place complete external threads all the way
to the barrel's head-side outer surface, the full-thread span measured back
from the bolt tip would need to reach **33.849 + 10.0076/2 = 38.853 mm**
(1.530 in). With the separate 3/4 in washer lead below, the corresponding
span is 38.917 mm. These are conservative nominal *reach* screens, not an
engagement requirement or an allowance for tip chamfer, thread runout,
barrel chamfer, misalignment, or tolerance. A “Full Thread: Yes” field does
not quantify those features. A fully threaded candidate would also require
thread-root shaft and wood-bearing checks; the 6.35 mm envelope here is
only a collision solid.

## Conflicted 3/4 in washer listing; CAD sensitivity only

The [Lowe's Hillman 811070 listing](https://www.lowes.com/pd/3037537)
states 3/4 in (19.05 mm) OD and 1/16 in (1.5875 mm) thickness. However,
a [Hillman answer on that exact product page](https://www.lowes.com/questions/hillman-811070-flat-washers/3037537/8bdce6ec-9668-5e14-b743-a57321514d80)
reports **0.868–0.905 in OD, 0.370–0.390 in ID, and 0.064–0.104 in
thickness**. That conflicts with the table and gives an unexpectedly large
hole for a nominal 1/4 in washer. Shared retailer Q&A may be mixing
variants; the online evidence cannot establish which dimensions apply to
delivered 811070 stock. Do not source or drill from the 19.05 mm claim.

At the *listing-only* 19.05 mm OD envelope, balanced rows are
Y = −161.942/−138.658 mm and
each Y reserve is 4.233 mm. A separate 4.0 in nominal bolt trial contains
all four embedded shaft and full bore paths, exceeds the provisional 10 mm
axis overrun (33.913 mm), and has no reported protected, unrelated-wood,
or other-row finite hit above 1 mm³. It is only a washer geometry
sensitivity, not a verified retail fit, bearing check, or delivered-part
measurement. The 22 and 23 mm OD trials above partially overlap Hillman's
reported OD range but use a different trial thickness; they are not a
substitute product qualification either.

The 22–24 mm washer ODs remain trial envelopes, and none of the washer
trials is bearing-qualified. The 8.001 mm barrel thread-axis offset,
head/tool sizes, delivered bolt shank and thread span, barrel thread depth
and engagement, drilling fit/tolerances, access in assembly sequence, wood
net section and splitting, joint strength/stiffness, and electrical bend
clearance remain open. No bolt length or washer is selected. No structural,
delivered-hardware, drilling, or fabrication release follows.

Reproduce with `uv run python -m scripts.owner_barrel_center_margin_probe`
and `uv run pytest -q tests/test_owner_barrel_center_margin_probe.py`.
