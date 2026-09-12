# Kicker upper-header attachment revision

**This separate development patch adds five upper attachments to each kicker, using the existing header as the receiver.** The original `round-structural-development` remains unchanged. This responds to the documented conditional prying failure without adding lumber, connecting panel seams, installing inserts or introducing a new bracket load path.

The model is [`mini_moonboard/kicker_header_reinforcement.py`](../mini_moonboard/kicker_header_reinforcement.py), key `kicker-header-development`. It retains the four existing kicker screws at Z = 60 and 140 mm and adds the same SPAX XFT08P-2000 #8 × 2-inch product at Z = **205.95 mm**. Added X coordinates are −200, −400, −600, −800 and −1000 mm on the left and their positive mirrors on the right. Each kicker therefore has nine screws; the development assembly has 66 panel/kicker screws. All commercial-angle screws, leg bolts, ordinary panel screws and raw timber remain as before.

## Why the existing header is the receiver

The single nominal 2x10 header extends from Z = 186.9 to 225 mm and Y = −270.95 to −36 mm. The kicker plywood back is at Y = −36 mm. A screw at the header's vertical mid-depth can enter its front side directly. The additional attachment does not require another rail, a vertical member or an inferred connection between adjacent plywood edges.

Nominal fit quantities are:

| Quantity | Result |
|---|---:|
| New axis to header top/bottom | 19.05 mm each |
| New axis to kicker upper edge | 19.05 mm |
| Gross screw penetration beyond plywood back | 32.54375 mm |
| New neighboring screw spacing | 200 mm |
| Closest added axis to the independent panel center seam | 200 mm |
| Closest added axis to outside panel edge | 219.2 mm |
| Added row above the 150 mm hold/T-nut row | 55.95 mm |

These are geometric distances, not released spacing/resistance values. The screw's nominal occupied major diameter is 4.1402 mm; its selected countersunk head remains the predecessor's modeled product geometry. New occupied holes are cut in the header and each kicker. They are not pilot-drilling or countersinking instructions.

For the predecessor's existing header SDS screws, all axes are vertical. The nearest old axis lies at |X| = 131.29274 mm, leaving at least **63.46216 mm** separation between the X-projections of old and new occupied cylinders after subtracting their radii. This establishes no intersection for those cylinders. The old post bodies end at Z = 186.9 and the principal bodies start above the header, so the new screws' fully embedded portions remain within the header. Additional hardware introduced by another revision still requires its own collision check.

## Force calculation and limits

The original four-screw arrangement could not meet eleven of 45 conditional pitch cases even with favorable bottom-edge bearing credit. The extra high row increases the available attachment lever arms. Five additions were selected because four did not meet the independent sizing calculation's chosen conservative contact arrangement for the strongest sampled case; that does not prove five is an absolute minimum over every possible support model.

The companion independent equilibrium calculation assigns every screw force separately. Its witness is a statically feasible distribution within conditional single-screw references, not measured force sharing or a stiffness solution. The reference countersunk-head applicability remains unresolved. Neither a favorable witness nor the added screw count qualifies the plywood, receiver or connections.

The new screw reactions enter the existing header. Carry those forces and their moments through the header, its posts and the selected frame/base connections in the integrated revision. Bottom-edge compression, actual contact patches, hold/T-nut transfer, net plywood, combined panel bending/compression, header section/stability and connection resistance remain explicit requirements. Existing 56-screw geometry/reference gates authenticate only the predecessor; they cannot be relabeled as a 66-screw assembly acceptance.

## Integration interface

`added_datums()` and `added_connections()` return only the ten new attachments. `cut_added_connections(parts)` applies their occupied cuts to an already-cut part collection containing `base_header`, `kicker_left` and `kicker_right`; other parts are preserved. This makes the patch composable with a separately developed base-connection change. The standalone `parts()` applies the patch to the predecessor assembly; `wood_parts()` preserves predecessor raw receiver/passage geometry. `connections()` and `attachment_datums()` expose the combined standalone inventory.

Three focused tests check preservation of the original inventory/product, independent nine-screw kickers, nominal receiver containment/penetration, and rejection of an incomplete patch target. The patch remains development geometry pending the integrated analysis and release checks.
