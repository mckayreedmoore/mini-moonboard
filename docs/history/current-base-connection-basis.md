# Shoe-free 277 mm candidate: base connection calculation basis

The restored ML24Z angles have published directional capacities. The immediate
task is to calculate the forces they actually carry, distinguishing direct wood
bearing from forces transmitted through the connectors. Neither custom shoes nor
a material test is justified merely because a catalog does not list a general
six-component joint rating. This note explains how the published resistance
values may apply to this mounting, subject to the stated conditions. It does not
authorize construction.

## Exact current mounting

[`no_shoes_frame.py`](../mini_moonboard/no_shoes_frame.py) translates the
preceding structural frame upward by 52 mm and extends ground-bearing members.
Its outer angle geometry is inherited from
[`angle_base_frame.py`](../mini_moonboard/angle_base_frame.py):

- `clip_angle_base_left/right` connect `base_header` to `base_side_left/right`.
- Bend origins are `(±1181.1, -135, 277) mm`.
- Local flange directions are `u=(∓1,0,0)` and `v=(0,0,1)`; the bend is along Y.
- Each angle uses three SDS25112 screws in each flange, for a total of six screws.
- The header grain runs along X; the single 2x6 rim grain is 40° from vertical.
- The rim end has restored timber bearing on the header; no shoe gap remains.

The X axis runs across the board, the Y axis runs horizontally from front to
rear, and the Z axis is vertical. Dimensions and station directions come from
source inspection; the 52 mm translation does not itself change bracket
resistance or establish load demand.

## Manufacturer reference

Simpson's [L-C-MLZ25 letter, pages
1–2](https://ssttoolbox.widen.net/content/iczmiabsx6/pdf/L-C-MLZ25.pdf) was
downloaded and its installation diagrams visually checked for this review. It is
dated December 23, 2025 and valid through December 31, 2027. For Douglas
Fir–Larch and Southern Pine (DF/SP), the ML24Z bearing-installation row lists
**595 lbf for F1, no value for F2, 450 lbf for F3, and 750 lbf for F4**, with
six 1/4 × 1-1/2 inch SDS screws. The single/end installation row also lists 450
lbf for F2. No ML24Z load-duration increase applies. The letter requires
designer consideration of reinforcement where cross-grain tension or bending
cannot be avoided.

The illustration has a horizontal bearing member with grain along the bend. The
current rim is sloping, so the bearing-row analogy is useful but is not an
explicit illustration of this exact grain orientation. An unlisted F2 is not
zero capacity, and the single/end value cannot establish this mounting's uplift
resistance by substitution.

## Application of the outer-angle resistance values

The following is a project interpretation of the illustrated bearing axes. The
forces below act on the rim after accounting separately for forces carried by
direct wood contact.

| Required action | Resistance basis | How to use it |
| --- | --- | --- |
| Downward compression, −Z | Rim end bearing on header | Check actual bearing area and wood compression at the applicable grain angles. Vertical compression should not automatically be assigned to an unlisted bracket direction. |
| Front/rear shear, ±Y | F1, 595 lbf = 2646.69 N per angle | This is a conditional bracket check; its applicability to the mounting and grain orientation must be established. |
| Force across the board, ±X | F3/F4, 450/750 lbf | Use 450 lbf = 2001.70 N for either sign until the loaded-member direction is explicitly mapped. |
| Upward separation, +Z | The bearing-installation row does not list F2. | Establish whether separation is required. If it is, calculate a supported connection detail or obtain applicability guidance for this mounting. |
| Independent bending or torsional couple | The catalog does not provide an independent moment rating. | First resolve the actual force application points and compressive bearing couple; design only the residual moment that this load path requires. |

These are per-angle values, not an automatically doubled pair capacity. Left and
right forces follow the current assembly calculation. Opposite sides of the
board are not Simpson's back-to-back installation. For simultaneous actions, use
applicable directional interaction provisions from the current catalog; passing
separate component comparisons alone is only a screen. The prior [catalog
review](round-structural-base-review.md) records the page 289 simultaneous-force
rule and the distinction between force and couple capacity.

## Finite calculation sequence

1. Recover each rim/header force and its application point from the current
   whole-frame model, including asymmetric climbing and lateral cases. Retain
   the owner-selected assumption that the supports do not slide.
2. Allow compression-only timber contact. Verify the bearing resultant lies
   within an admissible contact region and check wood bearing. Do not assume
   contact carries tension or transfer an arbitrary end moment through a pin.
3. Compare required bracket shear with the mapped directional values. If all
   equilibrium cases can be supported through bearing and rated shear without
   uplift or an independent couple, no uplift test is needed merely because F2
   is unlisted. The basis for applying the catalog values to this grain orientation and mounting
   must still be documented.
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
these two restored outer angles. The [existing axis
inventory](reinforced-fastener-applicability.json) covers the other 22;
translating origins 52 mm leaves their force axes unchanged.

The sixteen rail-end stations follow the single/end force-axis mapping. The four
header/post and two center-principal/header stations are bearing-like; their
separation directions require the same contact-versus-connector treatment
described above. These eight base-region stations can be evaluated together as
part of the load-path calculation; they do not each require a separate
experimental program. The four-bolt leg joints require current joint forces and
standard timber-connection checks separately. The accepted panel and T-nut
construction is unchanged by this review.
