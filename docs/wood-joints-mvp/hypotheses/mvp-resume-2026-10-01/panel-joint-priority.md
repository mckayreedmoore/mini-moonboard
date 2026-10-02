# Upper-panel screw joint: next unresolved load path

The [zero-withdrawal calculation](no-withdrawal-frame-checks.md) establishes
that face contact and in-plane screw action alone cannot balance either
upper panel in any recorded case. The representative A12-rear necessary
statics problem is infeasible. Its original largest individual screw demand
is **1922.134 N** at `round_panel_upper_left_edge_2`, from `main_upper_left`
into `base_rail_top`. This is a demand from unsupported parametric stiffness,
not a measured load or an accepted Hillman connection capacity.

The parent checked the source geometry's normal orientation. The upper panel's
source mesh node mean lies 78.978 mm outward of those of the ordinary rear frame members along
`(0, 0.766044443, -0.642787610)`. Face compression pushes the panel outward;
screw withdrawal restrains it inward. The downward component of the outward
normal makes panel and climber weight require inward restraint. Reversing
contact signs would therefore misrepresent this overhanging geometry.

## A simple reference shows the required evidence

The pinned 2024 NDS Chapter 12, §12.2.2.1–2, gives the side-grain cut/rolled
wood-screw reference `W = 2850 G²D` in lbf per inch of thread penetration.
For the existing conditional `G = 0.50` scenario and a hypothetical standard
No. 10 diameter `D = 0.190 in`, this gives:

| Explicit reference scenario, before end-use adjustments | Value |
| --- | ---: |
| Unit withdrawal reference | 135.375 lbf/in = 602.178 N/in |
| Reference with an optimistic entire 2.5-inch screw length in threaded wood | 1505.445 N |
| Original peak demand / entire-length reference | 1.2768 |
| Thread penetration needed at that unadjusted reference | 3.19197 in = 81.076 mm |
| Illustrative 1.5-inch thread penetration reference | 903.267 N |
| Original peak demand / illustrative 1.5-inch reference | 2.1280 |

The source connection record specifies a purchased nominal length of
63.5 mm, while its old 50.8 mm CAD occupancy is an analysis envelope.
Even the entire-length comparison exceeds the nominal purchased length
needed under this particular reference scenario; actual threaded wood
penetration also excludes the panel, unthreaded portions and tip.

**This is not a Hillman capacity, a physical upper bound or an adopted
resistance check.** Actual Hillman thread geometry, standard applicability,
root strength, panel head transfer, installation and all applicable adjustments
remain unresolved. The 1.5-inch comparison is illustrative, not a measured
thread interval. The generic reference demonstrates why assigning a unit
axial-to-lateral stiffness ratio does not resolve resistance. It does not
prove that a different supported product-specific resistance could not exist.

The exact equation comes from the preserved chapter PDF, SHA-256
`53f6ec05dfd1ceabeccd4d6e88c342111678d3da4631ee7b482b706f77c1780f`,
printed page 83; Table 12.2B, printed page 86, includes No. 10 and G = 0.50.
The source row identity and simultaneous demands are bound in the
[zero-withdrawal results](no-withdrawal-frame-results.json). The generic
calculation uses no product resistance or properties from SPAX or SDS.

## Next finite joint task

Bind actual panel-to-receiver thread penetration and a supported withdrawal/
head-transfer basis for the purchased Hillman policy. Then recompute the
panel connection with that supported model and check simultaneous withdrawal
and lateral demands. If the required load path or adopted resistance fails,
report the specific correction before changing reviewed geometry or hardware.
The 66-axis policy and all other owners' work remain preserved.

The parent's corner work remains useful conditional evidence, but a corner
pass cannot close this panel attachment. The upper-left service-joint agent
continues to own its separate joint. Physical release remains false.
