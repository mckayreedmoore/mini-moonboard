# Provisional standard-stock planning

**Latest owner constraint: [do not use wood packers](owner-no-wood-packers-v1.json).**
The next candidate must assess a packer-free outer-top connection while
retaining the standard 4×6 top and both sides, actual **88.9 × 139.7 mm**.
The solved model still contains two wood packers; a packer-free geometry and
matched analysis are not complete. **Packer machining and the old packer
offcut allocation are on HOLD.**

The **13-board counts below remain provisional** until the new layout confirms
the stock requirements. They describe the prior packer-containing allocation,
not an adopted packer-free cut plan.

The retained solved development revision is
`v10-standard-4x6-top-and-sides-development-v1`, with a standard nominal
**4×6 top and both sides, modeled actual 88.9 × 139.7 mm**.
Its [matched evaluation](standard-side-stock-evaluation.json) has its own six
admitted cases and two independent replays per case. The declared vector
shear/torsion reference reaches **0.998500**; **15 bearing diagnostic case rows
across eight components remain**. These results apply to that solved
packer-containing layout. Complete connection and material
qualification remain unresolved. This stock list grants no purchase, cutting,
drilling, assembly, fabrication, structural or climbing release. The selected
screw-and-bracket baseline retains separate authority.

The [owner's preserved instruction](standard-stock-planning/owner-standard-stock-wood-list-v1.txt)
and [independent dimensional recheck](standard-stock-planning/wood-allocation-independent-recheck-v1.json)
confirmed the following **13-board allocation before credit for usable owned
stock**. All 22 sawn members, including the two packers, were assigned exactly
once against that solved geometry. This is preserved dimensional evidence;
it does not establish the next candidate's member count or allocation.
The prior list has no nominal 4×8 solid timber row.

| Nominal stock | Modeled actual section | Boards | Allocation |
| --- | --- | ---: | --- |
| 2×6 × 8 ft | 38.1 × 139.7 mm | 5 | Two runners with center posts; three boards for paired cross rails |
| 2×6 × 10 ft | 38.1 × 139.7 mm | 3 | Header and two center principals |
| 4×6 × 8 ft | 88.9 × 139.7 mm | 2 | Rear legs, each sharing its board with an outer post |
| 4×6 × 10 ft | 88.9 × 139.7 mm | 3 | Prior top/side allocation; packer lengths and machining are on HOLD pending the new layout |

The [13-board allocation CSV](standard-stock-planning/board-allocation.csv)
allows **25.4 mm trim at each board end plus 3.175 mm kerf per assigned
member**. Its prior length and section budgets fit dimensionally. The tightest
remaining length allowance is about **63.087 mm** on each rear-leg/post board.
Side lengths remain provisional at about 2,539.8 mm. These blank envelopes
are not a cutting sequence or a guarantee of clear grade yield; retain full
stock lengths until the affected operation is cleared.

Specify **grade-stamped DF-L No. 2 or better, dry, untreated solid-sawn wood**;
KD-15 is preferred when available. Kiln drying at manufacture is not a current
moisture reading; the indoor dry-service assumption remains at or below
19 percent. Actual grade, dimensions, defects, moisture and supply remain
unverified. STUD, SPF, Hem-Fir, DF-L(N), green, treated, finger-jointed or
built-up stock is not an automatic substitute.

## Packer hold and plywood

**Do not machine wood packers or act on the old packer offcut allocation.**
The preserved solved model contains two custom **177.8 × 139.6 × 50.8 mm**
packers. The earlier recheck found their lengths and milled section would fit
the top-board remainder, subject to unverified tools/service and finished
grade. That finding remains historical dimensional evidence; it is not a
current procurement or machining instruction. The latest owner direction
requires a packer-free connection assessment. Retain full stock lengths
until its layout and allocation are confirmed; no replacement member or new
cut plan is assumed here.

The cleats require **four 410.3 × 215.9 mm leaves**, modeled nominal 12.7 mm
thick, forming two bonded pairs. Each actual leaf must be at least **11.9 mm**
under the current hypothesis: **PS 1 APA Group 1 sanded plywood, Other
category**, with the 410.3 mm length along the verified face/strength axis.
Two 603.25 mm-square project panels fit two leaves each: after 25.4 mm trim
at every edge, the 413.475 × 438.15 mm nesting envelope including kerf fits
the 552.45 mm usable square. A documented larger panel may replace those two
panels. Nominal half-inch, generic BC or Exposure 1 labeling does not establish
the required thickness, grade or orientation; a 15/32-category example at
11.4554 mm is too thin. Actual plywood and the bond remain unqualified.

**Measure and reconcile existing face plywood before buying more.** The model
has four separate **1,217.6125 × 1,219.2 mm main blanks** and two
**1,217.6125 × 277 mm kicker blanks**, at modeled thickness 18.25625 mm.
Owned sheet count and usable dimensions are unknown; two 4×4 pieces cannot
supply four main blanks. Three nominal 4×8 sheets is only a conditional
replacement-layout allowance. Two main blanks require
`2 × 1217.6125 + 3.175 = 2438.4 mm` exactly, plus the full 1,219.2 mm width,
accepted factory edges and a compatible strength-axis layout; there is no
extra trim allowance. The retained product listing's 1,204.8744 mm width is
too narrow if it describes delivered stock, and its 18.2372 mm thickness
differs from the model. Measure the actual lot.

## Current list and preserved evidence

Use the [current 33-line planning CSV](buying-list-current.csv). Its four solid
timber rows retain the prior **5 / 3 / 2 / 3 board counts provisionally**, with
the packer machining/offcut hold stated explicitly. They do not constitute a
confirmed packer-free allocation; face-plywood purchase quantity stays
unresolved. Other hardware/equipment rows retain the earlier catalog and
inventory observations. Their prices, availability, catalog fit and delivered
properties were not re-researched or accepted by this stock update. Actual
and Disposition cells remain blank.

The original [buying markdown](buying-list.md), [34-line CSV](buying-list.csv)
and [catalog check](catalog-check.json) remain byte-exact historical records
for the earlier standard-top/deeper-side scope. Their two nominal 4×8
starting boards are superseded for current stock intent. The imported owner
instruction also retains earlier pending-analysis and deeper-side wording;
the matched evaluation linked above records completed analysis for the solved
packer-containing layout. The latest no-wood-packers direction controls the
next candidate. The
[source bindings](standard-stock-planning/source-bindings.json) preserve the
prior source hashes, document/CSV snapshot and 22-member dimensional validation;
they do not validate the new packer-free requirement. No frozen source record
was rewritten.
