# Purchased plywood and remaining lumber specification

## Purchased face plywood: exact product, not a leg-ply selection

The owner identified the purchased **face-panel plywood** as
[Roseburg at Lowe’s, item 12235 / model 119055](https://www.lowes.com/pd/Roseburg-23-32-CAT-PS1-09-Square-Structural-Plywood-Douglas-Fir-Application-as-4-x-8/1000015973).
On September 11, 2026, the owner reconfirmed **AC fir plywood** and this
previously supplied product link. Retain that identification; the remaining
unknowns concern the delivered sheet dimensions, layup and applicable properties,
not whether to buy a different face-panel product.
The listing specifies **23/32 CAT**, PS1-09 and Exterior exposure. The category
converts to **18.25625 mm**; its listed “actual thickness” of **0.718 inch
(18.2372 mm)** is product data, not a measurement of the purchased sheets.
The listed width, **3.953 feet (47.436 inches)**, conflicts with the nominal
4-foot description: verify usable width before committing the fixed-grid cuts.

[Roseburg’s exterior-core page](https://www.roseburg.com/softwood-plywood/exterior-core/)
identifies APA-trademarked PS 1 products. Its
[sanded-plywood brochure](https://www.roseburg.com/wp-content/uploads/2026/03/SandedPlywood_Brochure.pdf)
describes AC exterior plywood with western-wood core/back veneers and **5- or
7-ply 23/32-inch** options. This does not establish this lot’s ply count,
all-Douglas-fir veneers, Structural I designation or design values. Do not
replace the listing’s PS1-09 designation with a newer standard by assumption.

Keep this face-panel purchase. Before final cutting, check actual thickness,
usable sheet dimensions and stamp/strength-axis identification; a stamp photo
is optional assistance. The **selected-hardware-development** and
**top-joint-development** candidates model these faces at **23/32 CAT
(18.25625 mm)**, while the preserved earlier candidates retain **18 mm** faces.
Reconcile measured stock with the chosen candidate, including screw penetration
and hold hardware; category thickness is not a measurement. The **19.05 mm leg
and splice plies are separate, unpurchased material selections**. This material
record does not assign plywood strengths or change existing acceptance gates.

## Selected remaining lumber

The species/grade guidance below remains the procurement basis. The size table
in this section describes the historical `lower-transition-development` layout.
For current sizes and quantities, use the [insert-candidate build
draft](round-insert-build-plan.md#materials-and-hardware) and its matching wood
schedule; do not combine the historical table with the current frame.

Use **grade-stamped No. 2 or better Douglas Fir–Larch (DF-L), kiln-dried,
untreated, solid-sawn lumber**, dressed on four sides. Prefer KD-15 when readily
available; otherwise KD is acceptable for procurement, with moisture checked
before assembly. Do not substitute STUD, appearance-only lumber, Hem-Fir, SPF,
DF-L(N), pressure-treated or finger-jointed stock without reviewing that change.

WWPA identifies species, grade, mill, agency and seasoning on the grade mark.
KD denotes at most 19% moisture at manufacture; KD-15 denotes at most 15%.
Neither establishes present moisture after storage. No. 2 is a structural
grade; STUD is a separate classification. See [WWPA grade stamps](https://www.wwpa.org/western-lumber/interpreting-grade-stamps/overview/)
and [dimension-lumber grades](https://www.wwpa.org/western-lumber/structural-lumber/dimensional-lumber/).

This stock selection follows the existing
[transition schedule](../exports/lower-transition-development/lower-transition-development_parts.csv),
not a new lumber-size optimization:

| Members | Nominal stock / required finished section |
| --- | --- |
| Side rims and top cap | 2×8; modeled 38.1 × 184.15 mm |
| Horizontal panel seam | 2×6; modeled 38.1 × 139.7 mm |
| Panel edges, mid-battens and rear crossmembers | 2×4; modeled 38.1 × 88.9 mm |
| Kicker battens | 2×4 remanufactured to 38.1 × 50 mm |
| Vertical panel-seam battens | 2×8 remanufactured to 38.1 × 165.1 mm |
| Twelve solid ribs | Supplier-machined 63.5 × 89.95 mm; 300, 350 or 420 mm long, grain along the rib's board-slope length |

Specify **4×6 starting stock for the ribs**, subject to measured machining
allowance: ordinary dressed 4×4 at 88.9 mm cannot supply the 89.95 mm dimension.
Require the supplier to establish the finished remanufactured members' grade;
do not assume ripping or planing transfers the parent stamp unchanged. The
wire chases, holes and other net-section deductions still need design review.
No glued buildup replaces these solid ribs.

Use the schedule for quantities and nesting. The top cap is **2514.6 mm
(99 inches)** long, so select 10-foot stock for it, not an 8-foot board.
Several other pieces require a full 2438.4 mm; allow end trimming and saw kerf
when selecting lengths rather than assuming every nominal 8-footer yields a
clean finished 8-foot part. These are procurement dimensions, not capacity checks.

## Service assumptions and limits

The selected basis is protected, dry indoor service: no weather exposure,
ground contact or persistent wetting; maintain lumber at no more than 19%
moisture in service. Store it dry and check moisture and fit before assembly.
This is an explicit project assumption, not a measured site condition.
AWC's [NDS commentary, Part 2](https://awc.org/wp-content/uploads/2021/12/Part02DesignValuespp7to19.pdf)
explains that design values require adjustments for service and loading
conditions. That historical commentary is background only, not the current
design-value basis for this project.

Grade selection does not establish member capacity, connection resistance,
ply load sharing or whole-board stability. No material model, FEA result,
hardware approval or existing qualification gate changes here. Sources above
were opened on 2026-09-06; actual-product identification remains necessary
before assigning design values.
