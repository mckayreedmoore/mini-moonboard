# Current structural-screw candidate: base connection review

The two outer ML24Z connections are **not released for construction**. This
bounded review found no catalog-only change that establishes their complete
resistance in the actual mounting. It does not establish that they will fail;
it establishes that the required resistance basis is missing. No hardware or
CAD changes were made. This review applies to `round-structural-development`.

## Confirmed geometry and manufacturer limits

The current frame retains the outer angles from
[`angle_base_frame.py`](../mini_moonboard/angle_base_frame.py): bend origins
`(±1181.1, -135, 225) mm`, single 38.1 mm-wide outer rims, and header-top
mounting. Each ML24Z has three SDS25112 screws into each receiver. The rim
grain is 40° from vertical; the header grain runs across the wall. Enlarging
LED bores and changing panel attachments does not create a new bracket rating.

The primary [L-C-MLZ25 letter](https://ssttoolbox.widen.net/content/iczmiabsx6/pdf/L-C-MLZ25.pdf)
was retrieved and its text rechecked for this review. Its ML24Z bearing row
lists no F2 allowable. Its separate single/end row lists 450 lbf F2 for DF/SP;
that value cannot be silently reassigned to this mounting. The letter also
requires designer consideration of reinforcement for unavoidable cross-grain
bending or tension. Six matching screws and adequate tip containment establish
neither the missing direction nor the complete joint resistance.

The current [C-C-2026 catalog](https://www.strongtie.com/resources/literature/wood-construction-connectors-catalog)
was independently downloaded and pages 289, 309–310 and 323 rechecked. Page 289
provides a simultaneous-force unity equation for all connectors, requiring
applicable directional allowables. It supplies no independent-couple rating.
The A34 option uses eight specified #9 × 1½-inch SD Connector screws and has
DF/SP allowables of 640 lbf F1, 495 lbf F2 and 240 lbf uplift. Opposite-side
angle installations require at least 3-inch joist thickness. These facts do
not establish applicability to this sloped rim or authorize an A34 pair on
the current single 2x6. The prior [A34 study](round-base-angle-remedy.md)
also retains unresolved production hole-pattern and complete head/access fit.

## Does the model invent a fixed base moment?

Code inspection of
[`Structure.rigid_angle`](../fea/horizontal_panel_frame.py) and its assembly
shows a freely moving rigid steel body with six independent translation/rotation
coordinates. The body joins timber through six separate finite, three-direction
screw springs. The rim and header rotations are **not directly fixed together**.
Their bearing is a separate compression-only vertical contact assumption.

Consequently, the recovered flange moment is produced by forces at separated
screw positions. A rigid steel plate and assumed screw stiffness may overstate
or redistribute real moment demand, but the model has not merely printed a
fictitious fixed-support reaction. Replacing this connection with a pin changes
its mechanics and potentially the rest of the structure's load path. It is a
new hypothesis requiring a stable, equilibrated model and a physical detail
compatible with the allowed movement.

For a nonzero resultant force F and moment M, the invariant parallel couple is
`dot(M, F) / norm(F)`. Moving the reference point changes M by a cross product
with F and cannot remove that component. Historical insert and ordinary-screw
reports contain such components, but **their numbers are not current
structural-screw design demands**. New source-matched demands are required
before numerical utilization can be issued.

## Smallest defensible closure

1. Obtain one documented applicability decision for the existing ML24Z mounting,
   including concurrent forces and the admissible load application point/couple.
   This can preserve all current parts if the detail is supported.
2. If unsupported, have the connection designer select one conventional detail
   and provide its complete resistance calculation. A bolted gusset or designed
   steel connection is an alternative design basis; neither becomes qualified
   simply because a prior CAD variant used it. Retain the single 2x6 rim and
   existing leg bolts unless the calculation specifically requires change.
3. Check that selected detail against the final global demands and release its
   coordinate schedule, fasteners, receiver species/grade, edge/end distances,
   bearing/splitting provisions, hardware clearance and installation sequence.

An independently calculated steel-angle/fastener-group design could also close
the gap without a manufacturer moment table, but it must establish steel
bending, local prying and wood/screw failure modes; summing SDS withdrawal
capacities is insufficient. No new experimental program is implied by these
three steps. Physical floor testing remains outside the owner's requested scope.

## Exact unresolved question — draft only, not sent

> Can one ML24Z with six SDS25112 screws connect the side of a single
> 38.1 × 139.7 mm DF-L rim, grain 40° from vertical, to the top of a flat
> 38.1 mm-thick header with grain perpendicular to the rim side face, using the
> modeled horizontal bend and full end bearing? Does the single/end F2 value
> cover upward separation in this specific mounting? Identify the applicable
> load directions, combined-force rule, tested force application point and
> treatment of any independent couple. If it does not apply, provide one rated
> alternative or a designed detail retaining the single 2x6 rim, including
> required fasteners, wood size and cross-grain reinforcement. Final
> source-matched simultaneous demands and coordinates must accompany review.

The existing [remedy note](round-base-angle-remedy.md) includes historical
wrenches for explanation. They must be identified as historical in any request;
the insert report is not a validated demand attachment for the current screw
candidate. Until the decision or replacement calculation exists, this is an
actual construction-release blocker, not optional numerical refinement.
