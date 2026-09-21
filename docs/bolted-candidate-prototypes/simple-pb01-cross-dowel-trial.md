# PB-01 direct cross-dowel CD-01 trial

Status: **PARK — bounded direct-joint alternative.** This is not a selected
joint, structural verdict, purchase instruction, or fabrication/drilling release.
The active [V4 plan](../bolted-candidate-simple-joints-v4.md) can continue with
the corner-block family while this alternative is parked.

The [reproduction script](../../scripts/simple_pb01_cross_dowel_trial.py)
models one direct steel cross-dowel/barrel-nut connection between the existing
PB-01 lower-right rail and principal. It writes no files and does not alter the
baseline, evidence, ledger, viewer, or six-inch corner-block reference. Run:

```sh
uv run --no-sync python -m scripts.simple_pb01_cross_dowel_trial
uv run --no-sync pytest -q tests/test_simple_pb01_cross_dowel_trial.py
```

## Exact retail lead and controlled fields

Home Depot's current page identifies Everbilt model **801914**, Internet
**204276112**, as a **1/4 in.-20 Zinc Plated Cross Dowel Nut (4-Pack)**. The
page displayed **$5.98** when checked on 2026-09-20. It describes zinc-plated
steel, four pieces, Phillips adjustment, and connector bolts sold separately.
Those are the public product fields used here.

The listing does not publish barrel outside diameter, barrel length, either
end-to-thread-axis distance, tolerances, internal thread minor diameter or
engagement, steel grade/strength, transverse metal section, or a wood-joint
rating. The page is therefore a procurement lead and thread/material
description, not an installed dimensional or capacity basis. No manufacturer
contact was made.

Source: [Home Depot Everbilt 801914](https://www.homedepot.com/p/204276112).
Local price and stock can vary.

An identifiable closer match is **Hillman 880543**, Lowe's item **137362** and
Home Depot Internet **202242356**. Both retailers identify a 1/4-20 steel
barrel nut; Lowe's calls it zinc-plated steel and lists one piece at **$1.48**
on 2026-09-21. In a Lowe's product Q&A, **Hillman customer service** gives
outside diameter **0.394 in = 10.0076 mm** and overall length **0.630 in =
16.002 mm**. Home Depot's specifications call the outside diameter **3/8 in**,
apparently a nominal size; the Hillman answer is more specific and is larger
than 3/8 in (0.375 in), so a nominal 3/8 in hole cannot be assumed to accept
the stated OD. Neither is a tolerance or a drill-bit instruction.
The title's 5/8 in likewise is nominal. The actual-piece limits, thread-axis
offset from either end, usable internal-thread span, steel strength/grade,
and joint resistance remain unreported. The retailer's “all-purpose” or “not
graded” category is not a mechanical strength value. This is a supported
nominal **diameter/length/material route**, not a capacity specification.

Sources: [Lowe's Hillman 880543 listing](https://www.lowes.com/pd/Hillman-20-x-5-8-in-Slotted-Drive-Zinc-plated-Barrel-Nut/3012559),
[Hillman customer-service dimension answer on Lowe's](https://www.lowes.com/questions/hillman-880543-specialty-nuts/3012559/0d07d7d4-94c9-59c7-b300-30a2fd0be7bd),
[Home Depot Hillman 880543 listing](https://www.homedepot.com/p/202242356).
No manufacturer was contacted.

A second current Home Depot lead, Everbilt **817828** (Internet 204281673),
publishes **16 mm** in its title: “1/4 in. x 16 mm Type F Zinc Cross Dowel
Nut.” That corroborates only the trial barrel length. Its public page does not
control the outside diameter, thread-axis position, tolerances, or metal
resistance needed here. Those trial inputs therefore remain unverified rather
than being transferred from a differently identified product.

Source: [Home Depot Everbilt 817828](https://www.homedepot.com/p/204281673).

## Existing joint and one-pose limit

The retained kerf-right solids put the rail end against the principal at
X=89.05 mm. The rail section at the joint is 38.1 mm in local T by 139.7 mm in
local N; rail grain runs along X. The principal remains inclined. The direct
concept sends each machine bolt in +X through the 38.1 mm principal and into
the rail, where it intersects a barrel inserted from a rail T face.

Exactly one `recessed_centered_receiver_pair` pose is evaluated. Each 16 mm
barrel is recessed 11.05 mm from its entry face, putting its body from 11.05 to
27.05 mm through the 38.1 mm rail thickness and leaving 11.05 mm of wood beyond
the far end. The trial thread axis is separately located 8 mm from the barrel
end, so it is 19.05 mm from the timber face. The complete transverse cross-bore
path is therefore 27.05 mm deep. The two barrels enter from opposite T faces.

The geometry sensitivity uses a 10 mm barrel outside diameter, 16 mm barrel
length, centered 8 mm thread-axis offset, and 7.5 mm machine-bolt wood bore.
None is attributed to 801914, and none is a drill size. Hillman 880543's
published nominal dimensions differ from the 10 × 16 mm diagnostic cylinders
by only **+0.0076 mm in diameter and +0.002 mm in length**. Re-centering a
16.002 mm body in 38.1 mm timber would put each body end **11.049 mm** from
its adjacent face. If, and only if, its thread were centered at 8.001 mm
from either end, the thread axis would still be 19.05 mm from that face. The
model has not been rerun for 880543; the dimensional closeness cannot establish
delivered fit, because its axis offset and tolerances are unknown. With a nominal 6.35 mm
thread major diameter, the centered trial leaves 4.825 mm of barrel metal from
the thread radius to each barrel end. This only shows that a dimensionally
similar part could be arranged without a nominal CAD clash;
`actual_801914_geometry_clear` remains null.

The complete machine-bolt, barrel-body, and barrel cross-bore envelopes are
contained in the intended wood and report no collision with any of the 66
protected historical panel/kicker screw axes. The gaps between paired
envelopes are 37.5 mm for the machine bores, 35 mm for the barrel bodies, and
35 mm for the complete barrel cross-bores. Each barrel is accessible from its
named T face and each bolt is inserted from the principal outside face.
Delivered-part fit, a jig, drilling accuracy, alignment, clearance, depth
support, removal method, head/washer dimensions, tools, and an actual assembly
trial remain unverified.

## Hole and receiver inventory

The public and diagnostic dimensions stay separate:

| Item | Value used | Status |
| --- | ---: | --- |
| Machine-bolt nominal diameter | 6.35 mm from 1/4-20 | Public nominal thread designation |
| Machine-bolt wood bore | 7.5 mm | Diagnostic envelope; not a drill instruction |
| Barrel internal thread | 1/4-20 | Public listing |
| Barrel outside diameter | 10 mm | Unverified sensitivity |
| Barrel length | 16 mm | Unverified sensitivity |
| Hillman 880543 OD / length | 10.0076 / 16.002 mm | Nominal; no tolerances |
| Barrel insertion from timber face | 11.05 mm | Unverified sensitivity |
| Thread axis from barrel end | 8 mm | Unverified centered sensitivity |
| Thread axis from timber face | 19.05 mm | Sum of insertion and barrel offset |
| Complete barrel cross-bore depth | 27.05 mm | Insertion plus barrel length |
| Wood beyond barrel body | 11.05 mm | Nominal geometry sensitivity |
| Metal beyond thread major radius | 4.825 mm each end | Nominal geometry sensitivity |
| Loaded barrel bearing length | unknown | No barrel anchorage calculation |
| Thread minor diameter/engagement | unknown | No stripping calculation |

The script reports radial wood to both T and N faces for the machine bore,
radial wood to N faces for the barrel envelope, wood beyond the inserted barrel
at the opposite T face, bore-to-bore gaps, and the intentional machine-bore to
barrel intersection. These are nominal sensitivity distances. Exact remaining
wood cannot be established until the chosen SKU dimensions and tolerances are known.
Barrel bore clearance, alignment method, depth stop/support, removal method,
bottoming clearance, and effective thread engagement remain unresolved.

Both fasteners are also screened against the complete purchased Hillman 42605
proxy envelopes for all 66 screw axes: the 63.5 mm full-length cylinder at the
9.017 mm nominal head diameter and the same envelope with 1 mm added radial
margin. Both cases are clash-free in the retained CAD. This is conditional
clearance only: shaft maximum, head profile/tolerance, total length, and the
installed seating datum are not controlled, so physical clearance is not
accepted. The script's `actual_801914_geometry_clear` field concerns 801914
only; it is not a finding for Hillman 880543.

## Candidate mechanism and missing mechanics

The intended separation path is principal head/washer to machine-bolt tension,
through the barrel threads, then barrel bearing into the rail. Compression can
cross the existing butt face. Shear in either local direction would require
machine-bolt shank bearing in the principal and in the end-entering rail bore.
Two separated axes and face contact offer a candidate route for rotation
restraint. No stiffness, contact state, load distribution, or capacity is
assigned to those routes. Tightening friction and optional wooden dowels/pins
receive no capacity credit.

The barrel receives axial bolt tension as a lateral force into the rail,
nominally parallel to its X grain. The two 10 mm trial cross-bores are 45 mm
apart along local N and their axes are 70 mm from the rail butt end. The
Hillman nominal OD × length is about 160.14 mm² of **gross projected area**;
it is not an effective bearing area or capacity. Neither that area nor the
end distance establishes a loaded bearing length: the intersecting 7.5 mm
bolt bore interrupts contact, and wood deformation can concentrate load.
Check bearing **at the actual barrel
contact**, end tear-out, splitting along X, reduced/net rail section and
group interaction. Also check principal head/washer bearing and any cross-grain
tension there. These are not covered by a simple bolt-in-two-solid-members
yield result.

For transverse shear, trace each direction through bolt-to-principal bearing,
bolt bending/shear, bolt-to-rail-end-bore bearing, and local wood splitting;
the barrel is not automatically a shear key. The two N-separated bolts can
form a couple for one bending direction, conditional on contact and tension
state; they do not establish all-axis moment or torsion resistance. Butt-face
compression is one-sided and tightening friction gets no resistance credit.
Changed-topology simultaneous PB-01 actions, bolt-group distribution, slip,
and rotation stiffness are still absent. Steel checks need a documented
strength basis for the barrel's transverse section, bending and thread
stripping, plus the compatible bolt's steel/root and washer seat. A calculation
route using supported inputs is sufficient; an assembled-joint product rating
is not inherently required.

[AWC TR12](https://awc.org/wp-content/uploads/2021/12/AWC-TR12-1510.pdf)
provides single-fastener lateral dowel yield equations and separately identifies
member strength, spacing, geometry, group action, fabrication, and tolerances as
design considerations. Its yield model does not supply an 801914 barrel
anchorage rating; beneficial friction is not credited here.

[USDA FPL-RP-586](https://research.fs.usda.gov/treesearch/6003) studied a
44.5 mm dowel-nut in 127 mm Douglas-fir peeler cores for a space-frame detail.
Its reported scale, specimens, geometry, moisture and grain variables are not
the 10 mm sensitivity or Everbilt furniture barrel. None of its load values is
scaled or transferred to this joint.

## Reference, cost, and assembly

The reference remains the 139.7 × 57.15 × 152.4 mm six-inch corner block,
gross volume **1,216,739.502 mm³**, with four bolts across two interfaces. The
direct concept adds no wood and inventories two barrels, two 127 mm trial
machine bolts, and two head washers. Each complete 127 mm bolt reaches 18.9 mm
past its thread axis and 13.9 mm past the trial barrel's far surface. Those
reach values do not establish effective thread engagement, clearance against
bottoming, or bolt suitability. This is a part-count/volume comparison, not a
strength equivalence or evidence that the cross-dowel is preferable.

At the displayed Everbilt package price, two barrels consume $2.99 of a
four-pack and require a $5.98 initial checkout. The closer Hillman lead is
**$2.96 for two singles**. For a rough *illustration*, two [Home Depot Everbilt
800676 1/4-20 × 5-in bolts](https://www.homedepot.com/p/204633308) at $0.62
each and two [Lowe's Hillman 490687 washers](https://www.lowes.com/pd/Hillman-1-4-in-Zinc-plated-Standard-Flat-Washer-16-Count/3035987)
from a $1.98/16 pack add $1.24 and $0.2475 allocated. That is **about $4.45
consumed** or **$6.18 initial checkout** for these three hardware lines before
tax/shipping; it mixes retailers and assumes the unused washers have another
use. The bolt's usable threads, seat, head, and washer adequacy have not been
qualified, so these are price leads, not a buyable joint BOM. Correct hardware,
drill bits, depth stop/jig, wasted stock, labor, and delivery/tax could change
the total. Corner-block wood checkout/allocated yield and its four complete
bolt stacks are also unresolved here; two barrels and no added block are not
proof of installed savings.
The direct concept requires +X end drilling plus barrel holes from opposite T
faces; the longest wood path to a thread axis is 108.1 mm. Both intersecting
bores require a positioning jig or equivalent controlled process.

**Insertion is not engagement.** The 11.05 mm recess positions the *barrel
body* from a T face; it says nothing about threads used by the bolt. In the
trial, a 127 mm under-head bolt reaches 18.9 mm beyond the barrel thread axis,
13.9 mm beyond the nominal barrel far surface along X. A 10 mm outside
diameter gives at most a 10 mm geometric intersection along the bolt axis,
before entry/exit chamfers, the bolt's first complete thread, washer thickness,
and thread runout. The model's 127 mm bore envelope does not prove a 127 mm
usable under-head bolt or a threaded tip, and the overrun needs a compatible
blind hole with no bottoming. Measuring the bolt's full-thread start and the
barrel's complete-thread span, then checking worst-case seat and tip position,
is necessary before any thread-stripping calculation. The 1/4-20 designation
alone cannot supply effective engaged turns.

An eventual assembly would require cross-drilling the two barrel entries,
drilling the two aligned +X paths, inserting and orienting both barrels, then
installing the two bolts and washers from the principal outside face. One
barrel enters each opposite T face. Recessed placement needs a controlled
depth stop/support and an extraction method; a slotted/Phillips alignment end
does not by itself retrieve a barrel recessed 11 mm. Removing the two machine
bolts would avoid routine structural wood-thread removal, but repeated removal
of the buried barrels, clearing chips, re-alignment, access with panels off,
and wear have not been demonstrated. This is not a fabrication/drilling
instruction.

## CD-01 decision

**PARK.** Hillman 880543 supplies a permitted-retailer, steel, nominally
near-matching barrel diameter and length, so this direct joint is a credible
bounded geometry alternative. It has no established bolt engagement,
anchorage, shear/rotation resistance, or complete installed-cost advantage.
The script remains the original geometry sensitivity and prints its historical
`hold_before_CD-02` label; this document records the current disposition.
No PB-01 corner-block reaction is transferred to the changed topology, and
neither named provisional scenario is reanalyzed. This alternative does not
block the active corner-block work.

**Reopen only when** a retailer-supported 880543 drawing or measured sample
establishes outside/body limits, thread-axis offset, usable thread span and
fit, **and** a traceable steel-strength basis or conservative applicable
specification permits barrel section/thread calculations with the actual bolt
stack. Then run the changed-topology PB-01 demand and wood/metal/contact
checks plus a priced, repeatable drill/removal trial before selection. An
assembled-joint rating is not the trigger. No purchase, fabrication, drilling,
or structural acceptance follows from this screen.
