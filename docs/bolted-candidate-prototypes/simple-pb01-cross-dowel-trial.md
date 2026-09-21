# PB-01 direct cross-dowel CD-01 trial

Status: **bounded geometry sensitivity and procurement screen only.** This is
not a selected joint, structural verdict, purchase instruction, or fabrication
and drilling release.

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
None is attributed to 801914, and none is a drill size. With a nominal 6.35 mm
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
wood cannot be established until the SKU dimensions and tolerances are known.
Barrel bore clearance, alignment method, depth stop/support, removal method,
bottoming clearance, and effective thread engagement remain unresolved.

Both fasteners are also screened against the complete purchased Hillman 42605
proxy envelopes for all 66 screw axes: the 63.5 mm full-length cylinder at the
9.017 mm nominal head diameter and the same envelope with 1 mm added radial
margin. Both cases are clash-free in the retained CAD. This is conditional
clearance only: shaft maximum, head profile/tolerance, total length, and the
installed seating datum are not controlled, so physical clearance is not
accepted.

## Candidate mechanism and missing mechanics

The intended separation path is principal head/washer to machine-bolt tension,
through the barrel threads, then barrel bearing into the rail. Compression can
cross the existing butt face. Shear in either local direction would require
machine-bolt shank bearing in the principal and in the end-entering rail bore.
Two separated axes and face contact offer a candidate route for rotation
restraint. No stiffness, contact state, load distribution, or capacity is
assigned to those routes. Tightening friction and optional wooden dowels/pins
receive no capacity credit.

Wood bearing, barrel bearing length, splitting/tear-out, net sections, machine
bolt bending, head/washer behavior, barrel transverse section, thread stripping,
and barrel bending remain open. An end-entering bolt and transverse barrel are
not treated as the existing two-solid-member PB-01 through-bolt helper.

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

At the displayed package price, two barrels consume $2.99 of a four-pack and
require a $5.98 initial checkout. Machine bolts, washers, correct lengths,
drill bits, jig, block wood/waste, and shared-stock allocation remain unknown,
so neither complete consumed cost nor checkout-cost savings is established.
The direct concept requires +X end drilling plus barrel holes from opposite T
faces; the longest wood path to a thread axis is 108.1 mm. Both intersecting
bores require a positioning jig or equivalent controlled process.

An eventual assembly would require cross-drilling the two barrel entries,
drilling the two aligned +X paths, inserting and orienting both barrels, then
installing the two bolts and washers from the principal outside face. That is
not a fabrication sequence or drilling instruction. Actual alignment,
clearance, depth support, removal, delivered fit, tool motion, wear, and repeat
assembly are unresolved or untested.

## CD-01 decision

**Hold before CD-02.** The one recessed-centered pose is nominally clear under
explicit unverified sensitivity dimensions, so the basic geometry is not
rejected. Both complete purchased-screw proxy envelopes also clear
conditionally, but physical clearance is not accepted.
The exact 801914 listing lacks barrel geometry. The separate 817828 title
confirms a 16 mm product length, but still lacks outside diameter, thread-axis
position, tolerances, and a metal basis needed to establish alignment,
remaining wood, or a supportable mechanics route. No PB-01 corner-block
reaction is transferred to this changed topology, and neither named
provisional scenario is reanalyzed. The cross-dowel is not selected over the
six-inch corner block. There is no structural verdict, hardware selection,
purchase instruction, fabrication release, or drilling release.
