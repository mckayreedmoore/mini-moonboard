# Wider-principal assembly and access review

This is an ordered **design-review sequence**, not approved workshop or erection
instructions. It applies only to `wide-principal-development`. Connection
resistance, machining tolerances, tool access and a safe handling/support plan
remain open. The modeled mass is about 200 kg before several hardware and hold
allowances; neither an individual panel nor an incomplete frame should be
assumed safe to lift or leave unsupported.

Use the current [parts/cut schedule](../exports/wide-principal-development/wide-principal-development_parts.csv),
[connection coordinates](../exports/wide-principal-development/wide-principal-development_connections.csv)
and [panel/insert drilling reservations](../exports/wide-principal-development/wide-principal-development_panel_drilling.csv)
together with the [part-local machining package](wide-machining.md). X is across
the board, S follows the inclined board upward, and N
points toward its backing. “Front” means the climbing side, including when the
assembly is lying down. World-coordinate schedules must not be treated as
untransformed measurements along a timber edge.

## Which earlier instructions this replaces

For this variant, the two central principals are actual 88.9 × 139.7 mm nominal
4×6 stock, not 38.1 mm-wide 2×6 receivers. Their centered axes are X −82.55 and
+44.45 mm. The corresponding principal side-edge distance is 44.45 mm, not
19.05 mm. The outer 38.1 mm side rims retain their own narrower geometry; do
not apply the new central dimensions to every receiver.

The four midpoint rail ends adjacent to the principals shorten by 50.8 mm and
their inner clips move accordingly. Four central post blocks replace the earlier
two narrow posts. Do not use an earlier cut list or transfer its inner attachment
axes onto these parts.

The 48 main-panel and eight kicker attachments are **machine screws and inserts**,
not the predecessor's SPAX panel screws. There are 18 ML24Z angles with 108
separately purchased SDS25112 screws, not the narrower insert variant's 16/96.
These changes supersede the affected instructions only for this candidate;
historical documents and analyses remain valid records of their own variants.

## Ordered inspection and assembly sequence

1. **Identify stock and parts before cutting.** Confirm actual thicknesses,
   species/grade stamps and stock condition. Label the two principal blanks and
   their paired short post offcuts. Reserve cutting kerfs and end trimming from
   the documented 10-foot stock allowance. The principal's level lower bearing
   cut (horizontal in the erected board) and its front housing are distinct
   features; neither is a square cut
   measured from an arbitrary end of the finished inclined member.

2. **Review machining with the bare timber accessible.** Establish the principal
   bearing planes and 88.9 mm-along-S × 38.1 mm-deep front housings for the
   continuous lower backing. Check the shortened midpoint rails and hold/LED
   service reservations against the current model. The modeled 40 mm diameter
   × 45 mm straight service spaces are clearance reservations, not a complete
   router setup or proof of cable-bend and hand-tool access.

3. **Dry-fit the inclined frame and lower backing.** Check the full-width top
   rail, paired midpoint rails, principals and side rims as one matched set.
   Keep both sides of the lower backing accessible. Its two through-bolts enter
   from the climbing side, with head washers seated inside the front recesses
   and nuts/washers accessible behind the principals. Fit and inspect these
   stacks before any lower face panel covers them. Do not infer tightening torque
   or beneficial clamp friction from the modeled fit.

4. **Prepare and inspect the base separately.** The full-width header rests on
   the outer posts and two same-width front/rear blocks beneath each principal.
   Preserve the modeled 6.35 mm gap between each central block pair; the header
   bridges it, so this is not uninterrupted direct post bearing. Retain access
   to the six header/post angles from below and beside the posts. Inspect the
   level principal/header bearing and the detachable side-gusset interfaces
   before closing the kicker. Base bearing resistance and assembly retention
   are not established merely by a dry fit.

5. **Install commercial-angle hardware while access is open.** Twelve angles
   connect the upper/mid frame members; six connect header and posts. Use the
   selected factory hole pattern and all six specified SDS25112 screws per
   angle. Do not alter steel holes, substitute the panel machine screws or
   assume a universal pilot/torque from the model. Confirm driver clearance and
   applicable manufacturer installation conditions at each actual orientation.

6. **Match the removable panels and receivers.** Transfer the current matched
   axes without forcing misaligned parts. Panel machine-screw clearance and
   countersinking are separate from receiver insert pilots. Install the inserts
   from the exposed front of the receiver, flush with that timber surface—not
   flush with the outer face of the plywood. Kicker inserts enter the front post
   faces behind the kicker. Resolve the installation-depth and engagement items
   below before machining production parts.

7. **Complete the rear-of-panel and wiring access review before closing.**
   T-nuts and their three flange-retention screw positions must be accessible
   from the rear of each face panel. Do not confuse those screws with the
   removable panel attachments. Check the selected MoonBoard LED hardware,
   connectors and detachable cable routing against each service opening. Wire
   routing must permit panel removal without pulling on bulbs or conductors;
   bend radii, clips, strain relief and disconnect locations are not yet a full
   specified harness design.

8. **Offer up and retain the panels from the climbing side.** Each main panel
   has 12 machine screws; each kicker half has four. Inserts stay in the timber.
   Check flush head seating, no screw bottoming and no trapped wiring. The lower
   main panels now conceal the backing-bolt heads. Establish the independently
   supported handling/erection sequence before joining the base and legs or
   changing the assembly's orientation; this document does not prescribe a
   lifting method or credit an unfinished frame with stability.

## Removal and transport are different operations

For **panel service**, support the panel, isolate/disconnect its wiring as
planned, then remove its machine screws. Leave inserts, ML24Z/SDS connections,
leg bolts and gusset bolts in place. No diaphragm or stability credit for the
remaining partly panelled frame has been established. Remove the appropriate
lower main panel before attempting to hold a recessed backing-bolt head; rear
nut access alone does not make that bolt accessible at both ends.

For **leg removal**, independently support the frame and each leg before releasing
the four leg-to-rim through-bolts per side. The three stitch bolts per leg retain
the two plywood plies as their own assembly and are not routine panel-service
fasteners. The current design does not establish a stable leg-free board or
a tool-clearance envelope for every wrench/socket position.

For **base separation**, the side gussets have four through-bolts each: two meet
the side rim and two meet the outer post. Which bolts remain with which transport
subassembly must be decided in the handling plan. The lower-backing bolts join
the backing to the principals; they are not the base-gusset transport connection.
Do not repeatedly remove manufacturer angle screws merely because other joints
are demountable. Published capacities for repeated wood-screw installation are
not established here.

## Machining and access items still unresolved

| Feature | Current model or source datum | What still needs resolution |
| --- | --- | --- |
| Backing bolt front seat | 28.575 mm recess diameter; 12.032 mm depth along N; 11.1125 mm through bore | Actual cutter/socket envelope, tolerances, seating and counterbore ligament resistance; do not enlarge for a socket without revisiting the detail |
| Receiver insert pilot | Manufacturer inch datum 23/64 in, 9.128125 mm | Stock/tool-specific pilot and drill-point depth; the model's 17 mm reservation is not a finished machining depth |
| Display insert cut | Nominal OD 11.5062 mm plus the documented tolerance reservation | Not the installation pilot diameter; do not copy the displayed cut as a drilling operation |
| Panel clearance and head | Provisional 7 mm clearance and nominal 82° countersink concept | Actual seating depth, plywood damage, flush surface and complete usable thread engagement; CAD uses an 80° maximum-head clearance envelope |
| Hand and power tools | Nominal hardware bodies clear the modeled parts | Socket/driver outside diameters, approach lengths and removal paths are not comprehensively modeled |
| Lower frame/base | Housed backing, level bearing cuts and paired posts | Machining tolerances, complete joint resistance, temporary supports and a safe assembly/transport sequence |

The [insert selection record](panel-insert-selection.md),
[current through-bolt fit audit](current-fastener-fit-audit.md) and
[connection qualification ledger](connection-qualification-ledger.md) retain
the governing limits. A visual fit, supported washer annulus or completed
assembly sequence is not construction or climbing approval.
