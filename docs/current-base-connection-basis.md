# Shoe-free 277 mm candidate: base connection calculation basis

The restored ML24Z angles have published directional capacities. The immediate
task is to calculate which duties they actually carry, separating wood bearing
from connector forces. Neither custom shoes nor a material test is justified
merely because a catalog does not list a general six-component joint rating.
This note establishes conditional resistance mapping, not a construction release.

## Exact current mounting

[`no_shoes_frame.py`](../mini_moonboard/no_shoes_frame.py) translates the
preceding structural frame upward by 52 mm and extends ground-bearing members.
Its outer angle geometry is inherited from
[`angle_base_frame.py`](../mini_moonboard/angle_base_frame.py):

- `clip_angle_base_left/right` connect `base_header` to `base_side_left/right`.
- Bend origins are `(±1181.1, -135, 277) mm`.
- Local flange directions are `u=(∓1,0,0)` and `v=(0,0,1)`; the bend is along Y.
- Each angle uses three SDS25112 screws in each flange, six total.
- The header grain runs along X; the single 2x6 rim grain is 40° from vertical.
- The rim end has restored timber bearing on the header; no shoe gap remains.

X is across the board, Y is horizontal front/rear, and Z is vertical. Dimensions
and station directions come from source inspection; the 52 mm translation does
not itself change bracket resistance or establish load demand.

## Manufacturer reference

Simpson's [L-C-MLZ25 letter, pages 1–2](https://ssttoolbox.widen.net/content/iczmiabsx6/pdf/L-C-MLZ25.pdf)
was downloaded and its installation diagrams visually checked for this review.
It is dated December 23, 2025 and valid through December 31, 2027. The ML24Z
bearing row for DF/SP gives F1/F2/F3/F4 = **595/unlisted/450/750 lbf**, with six
1/4 × 1-1/2 inch SDS screws. The single/end row adds 450 lbf F2. No ML24Z
load-duration increase applies. The letter requires designer consideration of
reinforcement where cross-grain tension or bending cannot be avoided.

The illustration has a horizontal bearing member with grain along the bend.
The current rim is sloping, so the bearing-row analogy is useful but is not an
explicit illustration of this exact grain orientation. An unlisted F2 is not
zero capacity, and the single/end value cannot establish this mounting's uplift
resistance by substitution.

## Actionable outer-angle mapping

The following is a project interpretation of the illustrated bearing axes.
Force refers to action on the rim, after separating any direct wood contact.

| Required action | Resistance basis | How to use it |
| --- | --- | --- |
| Downward compression, −Z | Rim end bearing on header | Check actual bearing area and wood compression at the applicable grain angles. Do not debit vertical compression automatically to an unlisted bracket direction. |
| Front/rear shear, ±Y | F1, 595 lbf = 2646.69 N per angle | Conditional bracket screen, with the stated mounting/grain applicability decision retained. |
| Across-board force, ±X | F3/F4, 450/750 lbf | Use 450 lbf = 2001.70 N for either sign until the loaded-member direction is explicitly mapped. |
| Upward separation, +Z | Bearing F2 unlisted | Establish whether separation is required. If it is, calculate a supported connection detail or obtain applicability guidance for this mounting. |
| Independent bending/torsional couple | No independent catalog moment rating | First resolve the actual force application points and compressive bearing couple; design only the residual moment that this load path requires. |

These are per-angle values, not an automatically doubled pair capacity. Left and
right forces follow the current assembly calculation. Opposite sides of the
board are not Simpson's back-to-back installation. For simultaneous actions,
use applicable directional interaction provisions from the current catalog;
passing separate component comparisons alone is only a screen. The prior
[catalog review](round-structural-base-review.md) records the page 289
simultaneous-force rule and the distinction between force and couple capacity.

## Finite calculation sequence

1. Recover each rim/header force and its application point from the current
   whole-frame model, including asymmetric climbing and lateral cases. Keep
   support no-slip as the owner-selected assumption.
2. Allow compression-only timber contact. Verify the bearing resultant lies
   within an admissible contact region and check wood bearing. Do not assume
   contact carries tension or transfer an arbitrary end moment through a pin.
3. Compare required bracket shear with the mapped directional values. If all
   equilibrium cases can be supported through bearing and rated shear without
   uplift or an independent couple, no uplift test is needed merely because F2
   is unlisted. The adopted grain/mounting applicability still needs documenting.
4. Where uplift or a residual couple is necessary, isolate its magnitude. A
   conventional rated tie or calculated fastener/angle detail can then address
   that specific duty. Manufacturer confirmation is a focused alternative to
   independent connection design, not a mandatory new material-testing program.

A pinned model is useful as a lower rotational-restraint hypothesis when it is
stable and respects the installed bearing geometry. Its zero end moment is an
input, not proof that the installed screw group develops no moment. Conversely,
a high-stiffness model's moment is not automatically an unavoidable design duty.
The decision should use an equilibrated, physically plausible load path rather
than demand every idealization pass simultaneously.

## Remaining current joint families

There are 24 ML24Z stations: the 22 retained in the reinforced candidate plus
these two restored outer angles. The
[existing axis inventory](reinforced-fastener-applicability.json) covers the
other 22; translating origins 52 mm leaves their force axes unchanged.

The sixteen rail-end stations follow the single/end force-axis mapping. The
four header/post and two center-principal/header stations are bearing-like;
their separation directions require the same contact-versus-connector treatment
described above. This is one finite load-path exercise across eight base-region
stations, not eight separate experimental campaigns. The four-bolt leg joints
require current joint forces and standard timber-connection checks separately.
The accepted panel and T-nut construction is unchanged by this review.
