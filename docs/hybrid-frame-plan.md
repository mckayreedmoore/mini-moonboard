# Hybrid lumber and plywood frame plan

Planning proposal, September 2026. No CAD, structural hardware or purchasing
schedule is changed by this document. The current box-frame exports remain
the implemented design. This proposal builds on [relocation-design.md](relocation-design.md).

## Objective and starting design

Reduce sheet cutting and home lamination while retaining the plywood character
and allowing occasional relocation. Preserve the climbing surface, 40-degree
angle, hole datums and 225 mm kicker. Keep the landing space free of added
lower-leg cross members. Do not assume the lighter frame preserves stability.

| Component | Starting proposal | What must be resolved |
| --- | --- | --- |
| Main side framing and top | Graded, dry 2x8 lumber, nominal actual 38.1 x 184.15 mm / 1.5 x 7.25 in | Stiffness, racking and leg connections; compare deeper lumber if needed |
| Straight backing, cross members and blocking | Standard lumber sized to each function; 2x4/2x6 candidates | Orientation, seam support, spans and connection loads; do not make every piece a 2x8 |
| Exterior legs | Retain two-layer shaped plywood concept | Adapt upper attachment to the new frame depth and recheck load path; retain full floor bearing |
| Kicker transition | Plywood cheeks/gussets where the shape is useful, with lumber blocking where practical | Determine thickness and connections; retain the trimmed rear outline |
| Climbing surface | Existing 18 mm plywood panels and hole layout | Recheck screw positions and hold/LED clearance against revised backing |
| Visible finish | Optional single-layer birch plywood facing on visible lumber | Removable, nonstructural, independently attached to each moving module; no structural bolts bearing on decorative skins |

2x8 is a candidate section, not a verified minimum. Its 184.15 mm depth is
considerably smaller than the present 322.8 mm side wall. Define whether the
new rim includes the climbing panel thickness before fixing frame depth.
The current leg-bolt normal datum lies beyond a single 2x8's proposed depth;
it cannot be copied unchanged. Adjust and evaluate the upper leg/frame joint
while keeping the chosen foot location as a starting constraint. Do not add
an unreviewed cantilever block merely to reuse old bolt coordinates.

Thin facing preserves the birch surface appearance but not the full visual
effect of a thick exposed laminated edge. Leave that edge visible on the
retained plywood legs; make added facing optional so it does not recreate the
fabrication workload. Do not count it as bracing or composite reinforcement.

## Corners and detachable interfaces

Interpret the proposed box joints as interlocking fingers at the top-to-side
corners, on both left and right. A fitted glued box joint offers more bonding
area than a plain glued butt joint, but no drawer-joint test supplies a load
rating for this frame. It still needs material, finger-root, splitting and
load-direction checks. Unglued fingers are not automatically a rigid joint.

Default: square-cut members with designed bolted internal corner brackets or
gussets, providing a clear load path through broad faces rather than relying
on screws into end grain. Keep tool access and removable top/side interfaces.
Choose bracket/bolt sizes after load evaluation, including timber bearing,
splitting, connection slip and bracket strength. Avoid excessive new hardware.

Alternative: glued box joints only if the top and sides will stay together as
a permanent transport module, or if the fingers belong to a smaller permanent
subassembly with separate detachable interfaces. This requires an explicit
transport-size decision and a suitable cutting jig/tooling. Do not glue the
large top/side assembly by default.

Panel attachments remain candidates for flush machine screws into engineered
captive hardware. Keep ordinary wood screws at joints that stay assembled.
No fastener-count reduction is assumed. Remove complete LED strips before
panel separation; use releasable retainers and record reinsertion order.

## Implementation sequence and decision gates

1. Inventory the existing part families. Classify each as retained plywood,
   replacement lumber, eliminated by new framing, or optional finish. Produce
   a before/after cut, laminate and hardware count rather than guessing labor
   or dollar savings. Select an available structural lumber species/grade and
   moisture condition with applicable design properties.
2. Lay out the candidate 2x8 frame as a separate CAD variant. Resolve the depth
   datum, panel-bearing faces, seams, upper leg connections, kicker transition,
   tool paths and LED clearance. Keep the current design as a comparison.
3. Establish spans and member orientation. Screen 2x8 stiffness and strength
   with actual material properties and realistic joints. If inadequate, first
   compare deeper sections or a revised bracing layout; do not assume 2x8 is
   sufficient or automatically laminate lumber to recover depth.
4. Check whole-frame unanchored overturning, sliding and lateral/racking
   behavior with revised mass and centre of mass, followed by actual panel,
   corner, leg and rear-member connections. Prior plywood-frame FEA is not
   validation of this variant. Resolve the design load envelope.
5. Build representative corner and panel-attachment samples before the full
   structure. Verify fit, tool access and repeated disassembly; have strength
   acceptance criteria established separately. Confirm any box-joint tooling
   before choosing the glued alternative.
6. Finalize moving modules, dimensions and estimated weights. Check the exit
   route and transport vehicle, label joints/hardware, and develop a supported
   teardown/reassembly sequence including LED removal and reinsertion.
7. Regenerate CAD, viewer, cut list, BOM, connection schedule and drawings for
   the selected variant. Publish a comparison of fabrication operations,
   stock quantities, transport size and remaining structural findings. Replace
   the current default only after that comparison supports the change.

## References

- [SFPA standard lumber sizing](https://www.southernpine.com/resources/specifying-southern-pine-lumber/standard-sizing/).
- [USDA Wood Handbook: fastenings](https://research.fs.usda.gov/treesearch/62253): joints depend on wood properties, grain direction and moisture.
- [WOOD's box-joint comparison](https://www.woodmagazine.com/video/wood-joint-torture-test-ii): evidence for its tested furniture joints only, not structural capacities for this design.
