# Outer base-angle uplift: closure options

No base-angle substitution has been made. The existing ML24Z ledger remains
failed to establish an applicable complete-wrench resistance. This note records
the specific manufacturer questions and the bounded alternative under study.

## What the manufacturer documents establish

[Simpson L-C-MLZ25](https://ssttoolbox.widen.net/content/iczmiabsx6/pdf/L-C-MLZ25.pdf)
lists 450 lbf F2 for a single/end ML24Z installation but leaves F2 blank for
the bearing installation. The letter does not state that a bearing-mounted
connector may switch to the single/end row when the load reverses. The same
steel and six SDS25112 screws do not by themselves establish equivalence of
the wood grain, force direction, end distances and tested restraint.

The [current primary C-C-2026 catalog](https://ssttoolbox.widen.net/content/orplhjaqw1/pdf/C-C-2026.pdf),
page 289, supplies a general unity equation for simultaneous directional loads:
the sum of applicable demand/allowable ratios must be below one. Therefore,
the broader statement that Simpson has no simultaneous-load rule would be
incorrect. Every participating direction still needs an applicable allowable
value. The alternative 75% rule is restricted to specified roof-to-wall product
groups and is not assigned here to ML24Z or A34. The unity equation has no
separate moment term or an allowance for an unlisted uplift direction.

## Concrete alternate connector to investigate

Catalog pages 309–310 show an **A34 with eight #9 × 1½-inch Strong-Drive SD
Connector screws** in the bearing-style installation. Its DF/SP references are
640 lbf F1, 495 lbf F2 and **240 lbf uplift (1,067.573 N)**. These are distinct
from the nail-installed A34 values. The screw model must be the specified SD
product; the present six SDS25112 screws cannot be substituted into eight holes.

The nominal A34 bend length is 2½ inches (63.5 mm), with 1⁷⁄₁₆-inch
(36.5125 mm) flange reaches. Its overall footprint is smaller than the present
ML24Z envelope. That makes a **single A34 replacing each outer ML24Z** a
reasonable bounded fit study, not an approved replacement. Exact US product
hole axes, screw receivers, other hardware clearances and installation access
must be checked. The catalog requires at least 3-inch member thickness when
angles are installed on both sides of a joist; a pair on opposite faces of
the current 38.1 mm rim is therefore not the proposed remedy.

The explicit uplift entry addresses the missing *kind* of directional rating.
It does not settle the present mounting's grain orientation, combined demands
or moment. The current rim is 40 degrees from vertical; its grain is therefore
50 degrees from the horizontal bracket bend. The catalog bearing illustration
shows a horizontal carried member. No explicit permission for this sloped-grain
adaptation was found in the inspected product material. Footnote 2 on page 310
also calls for consideration of reinforcement where cross-grain tension or
bending cannot otherwise be avoided.

## Manufacturer CAD pattern comparison

The [extracted source data](a34-base-cad-data.json) preserve the actual US
[front DXF](https://ssttoolbox.widen.net/content/ltsehsicjl/original/C_A34_2DO_Cad_FR_Prod.dxf),
[top DXF](https://ssttoolbox.widen.net/content/mk3xaivdr6/original/C_A34_2DO_Cad_T_Prod.dxf),
[right DXF](https://ssttoolbox.widen.net/content/veqd5zqcku/original/C_A34_2DO_Cad_R_Prod.dxf)
and [SAT](https://ssttoolbox.widen.net/content/jfkfj566ja/original/C_A34_3d_Cad_MULT_Prod.sat)
identities and numeric hole centers. No UK A34E geometry was substituted.

Their extracted hole patterns do not coincide. Comparing all six pairwise
hole-center distances within each flange avoids an arbitrary origin, rotation,
reflection, inside/outside datum or a flat-versus-formed rigid flange placement.
Both sources use the same 2½-inch width and 0.148-inch hole diameter; their
differences cannot be reconciled by changing unit scale.

| Best corresponding flange sets | Largest mismatch between sorted pairwise distances |
| --- | ---: |
| Front DXF / SAT Y flange | 2.430 mm |
| Top DXF / SAT X flange | 2.137 mm |

These are disagreements between the extracted source geometries, not a claim
that a manufactured product is defective. Different drawing or product
revisions remain possible. The [bounded fit helper](../fea/a34_base_fit.py)
therefore probes both pattern families, flange swaps and mirrored width
directions independently. It never combines holes from different families or
claims to establish the received part's exact pattern.

For shaft occupancy the study uses SD9112's 0.177-inch major diameter and
1½-inch length from the manufacturer's
[C-F-2025TECHSUP](https://ssttoolbox.widen.net/content/zpm9nibpvz/pdf/C-F-2025TECHSUP.pdf),
pages 33–34. The engineering head diameter is 0.378 inch; complete head height
and profile were not established, so the study does not assert a full head or
tool-access pass. Generic wood-to-wood screw edge/end tables are not substituted
for an A34 installation qualification.

## Completed bounded receiver study

The [eight-variant fit result](../fea/results/a34-base-fit-v1.json) checks both
extracted CAD families, both flange assignments and both width orientations.
All 16 proposed screw axes per variant have continuous nominal receiver
penetration, and their 4.4958 mm major-diameter shafts remain inside the actual
round-bored timber. Minimum candidate-to-candidate shaft-envelope gaps are
11.949 mm for DXF and 12.473 mm for SAT. The minimum gap to retained fastener
shaft envelopes ranges from 0.353 to 7.009 mm depending on the selected family
and orientation. These are geometric shaft gaps, not required wood spacing or
head/access clearance. Neither a common physical production pattern nor a
complete hardware clearance pass follows from this study.

This establishes room for a concrete A34 replacement study on the existing
single rim and header. It does not authorize the swap: the sloped-grain rating,
actual purchased hole pattern, full bracket/head fit, independent couple and
redistributed native forces remain unresolved. The current ML24Z geometry and
failed resistance ledger are preserved.

## Exact question for Simpson engineering or the connection designer

The following is a draft technical question, not a sent message. Final demand
attachments must use the independently validated current insert/contact run;
the historical numbers below only identify the issue already found.

> We have a single 38.1 × 139.7 mm DF-L No.2 rim, grain 40° from vertical,
> with a level end bearing on a flat single 38.1 mm-thick header. The header
> grain runs horizontally across the wall. One ML24Z joins the rim's side
> face to the header's top face. The bend is horizontal and perpendicular
> to the header grain. Three SDS25112 screws run horizontally through the
> angle into the rim side; three run vertically downward into the header.
> No opposite-side angle, built-up rim or gusset is present.
>
> Does L-C-MLZ25's single/end F2 rating apply when this exact bearing-mounted
> assembly sees upward separation? If so, identify the permitted mounting,
> grain orientation, load application line and necessary wood reinforcement.
> If it does not, does the A34 installation with eight SD9112 screws and the
> published 240 lbf uplift value cover this same sloped-rim condition?
>
> Please identify the rated detail and allowable concurrent force/moment
> envelope, including any independent couple, and the force application line
> already inherent in the tabulated test. If an additional connector is
> required, specify its model, placement, fasteners, minimum wood size and
> force-sharing assumptions for this 38.1 mm single rim. The header's local
> bearing, cross-grain tension and connection to the rest of the frame remain
> separately checked components of the load path.

For the preserved F10 ordinary-screw diagnostic, the applied wrench resisted
by the **right** angle about its bend origin `(1181.1, −135, 225) mm` is:

| Component | Recovered diagnostic value |
| --- | ---: |
| Force X | +268.367 N |
| Force Y | −249.253 N |
| Force Z | +257.560 N uplift |
| Moment X | +5,532.942 N·mm |
| Moment Y | +10,185.913 N·mm |
| Moment Z | −10,921.418 N·mm |

These are the negatives of the bracket's forces on the rim. Opposite signs
apply to the bracket reaction. Moving a force's application point can remove
only the moment perpendicular to that force; the parallel component is an
independent couple. The right-angle wrench above has approximately
8,636 N·mm of such invariant parallel moment, so simply moving its force to
the screw-group centroid cannot remove the entire moment demand. Across all
six historical outer-angle states this quantity is approximately
1,944–10,086 N·mm. Those are reported-force diagnostics, subject to the
[force-recovery limits](round-member-connections.md#evidence-and-sign-conventions).

The manufacturer response should reference the submitted final coordinate
schedule and validated simultaneous wrench, not just the 258 N uplift
component. Adding a rated uplift connector changes stiffness and force
sharing; its actual forces and both connections must be modeled and checked.

## Current validated demand attachment

The [current insert/contact assessment](round-insert-member-connections.md)
now supplies the three completed v3 cases for the drafted question. In F10,
the right-angle applied force at the same bend origin is
`(+272.988, −246.285, +260.829) N` and its moment is
`(+5488.920, +10352.024, −9596.274) N·mm`. Its independent parallel couple is
7,884 N·mm. These supersede the historical diagnostic above for the current
insert candidate; all six current outer-angle wrenches remain in the linked
JSON. The A34 swap has not been applied or qualified.
