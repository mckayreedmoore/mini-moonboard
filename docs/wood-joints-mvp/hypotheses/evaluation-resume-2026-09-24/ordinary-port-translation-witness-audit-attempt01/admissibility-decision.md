# Ideal N-translation admissibility decision

## Decision

The unchanged `n_plus` 1.0 mm endpoint is admissible as an **idealized
zero-strain, no-wood-bore-bearing kinematic witness** for the frozen port,
nut-equation and declared contact representation. The witness establishes
existence of one feasible motion; it does not establish a unique response,
equilibrium under a physical load, or a native CalculiX contact state. It does
not demonstrate that the endpoint reaches bearing.

The assignment is rail `+0.5 N`, principal `−0.5 N`, cleat translation zero,
all rotations zero, with each complete bolt/washer/nut stack translated
`±0.25 N`. “Cleat translation zero” is only the coordinate chosen for this
witness. The cleat remains free: no cleat restraint or gauge is imposed. The
pinned port audit confirms the prescribed port transformations, boundary
values, nut equations and no port/nut dependent-DOF conflict.

## Contact basis and finite overlap

For the ideal planar representation, all 19 declared planar pairs have normals
perpendicular to global N: the three wood interfaces have maximum
`|n·N| = 1.05e−12`; the 32 oriented normals across the 16 hardware-seat pairs
have maximum `5.79e−13`. With zero rotations, the assigned relative motion is
tangent to these planes and leaves their signed normal gap unchanged. For the
initially coincident ideal faces, the gap therefore remains zero; a zero
contact traction is admissible under the frictionless unilateral law.

A positive *trimmed-face overlap* is not required for that zero-traction
feasibility. If a tangential shift reduces an interface's finite overlap, the
nonoverlapping portion simply has no opposing face patch and cannot transmit
contact force; loss of overlap alone does not create negative normal gap
between coplanar faces. Positive common area is required to claim a continuing
load-transfer patch or force capacity. The existing analytic outer-domain
check retains positive wood-interface envelopes, but it is not an exact
post-motion trimmed Boolean intersection. The 16 washer-seat overlaps likewise
are not claimed as post-motion force-transfer areas.

The reviewed quadratic C3D10-surface radial-envelope calculation bounds the
eight shaft/wood-bore pairs away from contact through the assigned maximum
`0.25 mm` relative shaft motion: minimum computed separation after its
`1e−6 mm` reporting reserve is `0.0931487349 mm`. The eight co-moving
shaft/washer-bore pairs retain at least `0.6725849896 mm`. The curved-surface
bounds and source-bound nut-equation audit support the candidate assignment;
they are geometric calculations, not native contact-law evaluation.

These facts support a zero-strain, no-bearing witness without requiring
solver uniqueness. A free mechanism can admit multiple motions and zero
restoring force before bore closure. Newton nonconvergence on that mechanism
is not itself evidence of physical joint failure.

## Scope limits and next bearing evidence

This conclusion is limited to the idealized planar-contact representation plus
the reviewed curved-surface clearance bounds. It is not an exact native C3D10
contact-gap or contact-law proof. The mesh plane residual reaches about
`2.22e−8 mm`; the radial bound uses floating-point arithmetic rather than
outward-rounded interval arithmetic. The 35-pair manifest intentionally omits
four nut-bore pairs and does not establish thread engagement or exclude every
unpaired whole-body collision. No claim is made for actual hardware motion,
preload, equilibrium, demand, strength, capacity or acceptance.

The 1.0 mm endpoint is not demonstrated to reach wood-bore bearing: the bore
bounds remain positive and the planar motion has no normal component. A bearing
claim needs a physically justified path that closes a wood-bore interface and
complete accepted-state output for a named wood-bore pair. Before execution,
freeze the output threshold and schedule; then report the first accepted state
with a finite resolved CFN on one of `WJCP_020`–`WJCP_027` above that threshold
and subsequent accepted states. Such a threshold crossing establishes first
*observed resolved resultant*, not exact local contact onset; a zero or
sub-threshold net CFN cannot prove that curved-surface local pressure is
absent. No cleat gauge is introduced here. Small method-fixture passes alone
do not justify selecting a heavy retry.

## Pinned evidence

| Evidence | SHA-256 |
| --- | --- |
| [Candidate translation witness](README.md) | `048333d21c377efc9fe72ad8be34ccb8db65d04a85329d05b349191372eccf65` |
| [Frozen N-motion record](../ordinary-port-motion-attempt09-common-map/port-motion_n_plus.json) | `a28c0ba399842f96801ce5ce982dc6b52d459c537c132d283de01298d63b31bc` |
| [N-motion equation/transform audit](../ordinary-port-motion-attempt09-common-map/port-motion_n_plus-audit.json) | `9f1135ed95c48c07d3e82f7c5dcc7a0bef1e1cc22fd8350ec4fc7cdd1b28fdf4` |
| [35-pair contact manifest](../ordinary-port-motion-attempt09-common-map/contact-manifest.json) | `50f7d8c9b85197f43732d49d13e75240fa6d5423673d28274e278829878a594d` |
| [Nut-coupling record](../ordinary-port-motion-attempt09-common-map/nut-coupling.json) | `568ade2437181bc8e9398f64a2818bbf8bd3f46a64dae9639bf363cb68bec960` |
| [Planar contact classification](../ordinary-patch-contact-classification-attempt01/classification.json) | `18bdf1b9736ce6ca2cf2b3dd0488a7651da05f35e531605fd465e7b502363f13` |
| [Quadratic radial-envelope result](../ordinary-n-motion-radial-envelope-attempt01/radial-envelope.json) | `e459e979e33d9deb85ae5064fa27b2d2a78280ec87986bc40fc0ab4335a3ae3f` |
| [Radial-envelope independent review](../ordinary-n-motion-radial-envelope-attempt01/independent-review.md) | `5303e7949deb91ef9518eb3d280418d6bc8f7d0954fa32daffebedfd2ccf69ed` |
| [Pair-output contract source-review record](../current-pair-output-contract-review-2026-09-27/source-review.json) | `73ed00e9a2e0643bfbbc8bc764249ef0dd3e1a35b1d23cdccf987fb3534c4eac` |
| [Pair-output independent review](../current-pair-output-contract-review-2026-09-27/independent-review.md) | `0bd956045ea83d294a8452cb4d55a46be77d9fee2f839def0f5a5fb069692b83` |
