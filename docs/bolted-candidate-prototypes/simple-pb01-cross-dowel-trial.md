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

## Existing joint and two-pose limit

The retained kerf-right solids put the rail end against the principal at
X=89.05 mm. The rail section at the joint is 38.1 mm in local T by 139.7 mm in
local N; rail grain runs along X. The principal remains inclined. The direct
concept sends each machine bolt in +X through the 38.1 mm principal and 70 mm
into the rail, where it intersects a barrel inserted from a rail T face.

Exactly two poses are evaluated:

| Pose | Bolt rows | Barrel entry | Required thread-axis depth | Outcome |
| --- | --- | --- | ---: | --- |
| Initial | N=265/310, T mid-plane | opposite T faces | 19.05 mm | Fails trial offset. |
| Sole correction | N=265/310, diagonal T | opposite T faces | 12.7 mm | Trial-clear only. |

The geometry sensitivity uses a 10 mm barrel outside diameter, 16 mm barrel
length, 12.7 mm thread-axis offset, and 7.5 mm machine-bolt wood bore. None is
attributed to 801914, and none is a drill size. The correction only shows that
a dimensionally similar part could be arranged without a nominal CAD clash.
`actual_801914_geometry_clear` remains null.

For the correction, the machine-bolt and barrel envelopes are contained in the
intended principal/rail wood, intersect each other, remain separated from the
other fastener, and report no collision with any protected panel/kicker screw
axis. Each barrel is end-accessible from its named T face and each bolt is
inserted from the principal outside face. Delivered parts, a jig, drilling
accuracy, head/washer dimensions, tools, and an actual assembly trial remain
unverified.

## Hole and receiver inventory

The public and diagnostic dimensions stay separate:

| Item | Value used | Status |
| --- | ---: | --- |
| Machine-bolt nominal diameter | 6.35 mm from 1/4-20 | Public nominal thread designation |
| Machine-bolt wood bore | 7.5 mm | Diagnostic envelope; not a drill instruction |
| Barrel internal thread | 1/4-20 | Public listing |
| Barrel outside diameter | 10 mm | Unverified sensitivity |
| Barrel length | 16 mm | Unverified sensitivity |
| Thread axis from entry end | 12.7 mm | Unverified sensitivity |
| Loaded barrel bearing length | unknown | No barrel anchorage calculation |
| Thread minor diameter/engagement | unknown | No stripping calculation |

The script reports radial wood to both T and N faces for the machine bore,
radial wood to N faces for the barrel envelope, wood beyond the inserted barrel
at the opposite T face, bore-to-bore gaps, and the intentional machine-bore to
barrel intersection. These are nominal sensitivity distances. Exact remaining
wood cannot be established until the SKU dimensions and tolerances are known.

## Candidate mechanism and missing mechanics

The intended separation path is principal head/washer to machine-bolt tension,
through the barrel threads, then barrel bearing into the rail. Compression can
cross the existing butt face. Shear in either local direction would require
machine-bolt shank bearing in the principal and in the end-entering rail bore.
Two diagonally separated axes and face contact offer a candidate route for
rotation restraint. No stiffness, contact state, load distribution, or
capacity is assigned to those routes. Tightening friction and optional wooden
dowels/pins receive no capacity credit.

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
gross volume 1.217 L, with four bolts across two interfaces. The direct concept
adds no wood and inventories two barrels, two machine bolts, and two head
washers. This is a part-count/volume comparison, not a strength equivalence.

At the displayed package price, two barrels consume $2.99 of a four-pack and
require a $5.98 initial checkout. Machine bolts, washers, correct lengths,
drill bits, jig, block wood/waste, and shared-stock allocation remain unknown,
so neither complete consumed cost nor checkout-cost savings is established.
The direct concept requires +X end drilling plus barrel holes from opposite T
faces; the longest wood path to a thread axis is 108.1 mm. Both intersecting
bores require a positioning jig or equivalent controlled process.

Assembly would cross-drill the two barrel entries, drill the two aligned +X
paths, insert and orient both barrels, then install the two bolts and washers
from the principal outside face. Removal uses accessible metal threads. Actual
delivered fit, tool motion, wear, and repeat assembly are untested.

## CD-01 decision

**Hold before CD-02.** The sole correction is nominally clear under explicit
unverified sensitivity dimensions, so the basic geometry is not rejected.
The exact 801914 listing lacks barrel geometry. The separate 817828 title
confirms a 16 mm product length, but still lacks outside diameter, thread-axis
position, tolerances, and a metal basis needed to establish alignment,
remaining wood, or a supportable mechanics route. No PB-01 corner-block
reaction is transferred to this changed topology, and neither named
provisional scenario is reanalyzed. There is no structural verdict, hardware
selection, or drilling release.
