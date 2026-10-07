# Coupled panel diagnostics for the finished-floor A12 rear state

The [saved coupled consumer result](panel-coupled-a12-rear-finished-floor-v4.json)
recovers all six panels and 66 simultaneous screw actions from the corrected
finished-floor field. It does not rebuild CAD, assemble stiffness, solve fixed
receivers or transfer historical demands. The independent finished-support and
arithmetic gate passes. Every release flag remains false.

The source is
`compatible-frame-a12-rear-finished-floor-v4.json`, SHA256
`8d90941f9d1cb20d938ddc65992b2db7b0fe0c38420bf6bfc10fc0684281256d`,
state `thin-v4-84ad844f63afddc032cf922c`. This is **A12 rear only**, with the
original 25 kg top accessory placement, CAT23/32 plywood, eight spline
intervals, 150 mm beam stations, 35 mm contact cells, Hillman and bolt spring
scenarios of 1000 N/mm, and 1.5875 mm bolt radial clearance. The floor basis is
`authenticated-finished-timber-horizontal-faces`; its geometry SHA256 is
`e6c7ac4548b943bef4580b7c58efd67c11e29ed3335ae4036998a70c346986fc`.
Spring values and assumed no-slip floor behavior are not measured physical
bounds. Shared shaft, local cut and first-order kinematics limits remain those
of the coupled producer.

The new [consumer](../../../../../scripts/thin_bolted_panel_coupled.py) checks
each exported coefficient vector against its exact slice of global `q`, verifies
the knot/order convention, retains the owner-reported horizontal strength axis,
and authenticates all source pins and the independent support gate. The frozen
[panel methods](panel-mechanics-v4.md) and their JSON geometry/support datums
are reused. Both prior panel and raw-floor reports remain intact.

| Same-axis head witness | Conditional demand or reference comparison |
| --- | ---: |
| Axis / receiver | `round_panel_upper_left_rim_4` / `base_side_left` |
| Axial head/withdrawal tension | 2014.269454 N |
| Simultaneous lateral magnitude | 361.801206 N |
| Signed local `[outward, horizontal, upslope]` force | `[2014.269454, 273.057744, -237.359603]` N |
| Generic head reference, CD1.0 | 580.292408 N |
| Generic head ratio, CD1.0 / conditional CD1.6 | 3.471128 / 2.169455 |
| Generic side-grain wood-screw effective thread required, CD1.0 | 84.962327 mm |
| Nominal length remaining after the panel | 45.243750 mm |
| Mean projected 9/5 mm annulus pressure | 45.797277 MPa |

The generic head equation uses Group 1 plywood ESG0.50, the owner-reported
9 mm head, and the unmeasured 3 mm seat-depth scenario, reducing effective
panel thickness by one-third of that depth. The
[AWC head pull-through paper](https://web-media.awc.org/wp-content/uploads/2021/12/17210650/2018-nds-head-pull-through-paper.pdf)
supports that generic equation's countersunk-head treatment; it does not rate
Hillman 42605. Generic thread demand uses the side-grain wood-screw withdrawal
equation in the [2024 NDS](https://awc.org/resources/2024-nds/), with G0.50 and
nominal #10 diameter0.190 inch. Hillman's effective thread, thread geometry,
screw steel, lateral resistance and any axial/lateral interaction remain
unqualified. Mean pressure does not supply a conical indentation, punching or
edge-rupture capacity. The 5 mm body and 3 mm head height are explicit
unmeasured scenarios. These numerical exceedances are conditional generic
reference results, not an adopted product failure or structural release.

Signed membrane, bending, twisting and rolling-shear fields are recovered
simultaneously at every governing sampled section witness. Net-cut diagnostics
integrate those fields over the actual retained full-bore chords. The upper-left
panel's largest mean net bending, rolling and axial ratios are 0.722942,
0.298155 and 0.027363. Its sampled local bending-X, bending-upslope,
rolling-X and rolling-upslope ratios are 5.274353, 2.271316, 2.628856 and
1.010528. These are global spline resolution diagnostics. The method does
not resolve opening free boundaries, actual hold/T-nut contact footprints,
local seat pressure or point-load stress convergence. Neither small mean cut
ratios nor local sampled peaks establish a panel capacity pass. No punching
capacity is inferred from the
[APA panel specification](https://www.apawood.org/guides-tools-training/technical-document-library/technical-guides/panel-design-specification/)
rolling-shear reference. CAT23/32 reference properties remain explicit;
nominal 3/4 requires a new compatible field. CD1.6 is a conditional
wind/earthquake comparison, with permanent-load duration/creep unresolved.

Actual outward displacement reaches 52.265345 mm on the lower-left panel.
The largest sampled slope is0.125064 on the left kicker; upper-left slope
is0.113936 and its best-affine-removed warp is10.822040 mm. Absolute
displacement/slope include assembly motion. Affine removal is a diagnostic,
not a nonlinear equilibrium solution or an adopted drift criterion. The
lower free-edge regions retain the90.8 mm unsupported strip between their
rims/principals and raised rails. The kicker inner strips remain49.3625 mm
left and52.5375 mm right. Their same-state edge fields are retained in JSON;
they do not assign local edge rupture resistance.

Increasing saved-field sampling from41 to81 points per axis changes the
upper-left displacement peak0.0979%, its bending-X peak0.1667%, and
its rolling-X peak0.1494%. Across all six panels the largest sampled section
change is2.6585% (left kicker rolling-X); the largest net-cut ratio change
is0.4356%. Screw forces are identical because the field is unchanged.
This checks sampling of the **same eight-interval state**, not beam/spline
or contact-quadrature convergence. A finer compatible state is still needed
before claiming converged demands. The source field is not a physical demand
bound, and large first-order motion requires explicit applicability resolution.

The [validation receipt](panel-coupled-validation-v4.json) binds seven new
known-answer/identity tests, the seven reused panel-method controls, all
reference source pins, the source field, consumer and saved sampling comparison.
Reproduction commands are recorded there. The176.7 kB tracked result and
small receipt remain active evidence; the ignored81-point report is retained
as its recoverable raw sampling control. No archive/prune operation occurred.
