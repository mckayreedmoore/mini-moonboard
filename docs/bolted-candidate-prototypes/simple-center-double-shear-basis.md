# PB-04 center backer: three-wood-member double-shear method gate

Status: **source and input inventory only**. The proposed ordinary through-bolt
passes through a 38.1 mm side post, a nominal 139.7 mm solid 4×6 central
backer, and a second 38.1 mm side post, creating two shear planes. These are
nominal member dimensions, **not** verified dowel bearing lengths. The earlier
[center-support offset probe](simple-center-support-offset.md) instead drew a
140.0 mm backer to span its particular gap; that geometry difference must be
reconciled before using either trial. The three actual grain directions,
force directions, delivered bolt shank/thread locations, and action symmetry
are still open. There is no numeric capacity, joint rating, or drilling approval.

## Applicable 2024 NDS route

[AWC 2024 NDS Chapter 12, §12.3.1 and Table 12.3.1A][nds12] provide a
**symmetric** three-member double-shear lateral-yield route with four modes:
`Im` (middle-member bearing), `Is` (both side-member bearing contributions),
`IIIs` (side-member bearing with fastener bending), and `IV` (fastener bending
across the two shear planes). Modes `II` and `IIIm` belong to the single-shear
equations and must not be imported here. `Im` uses the one central member's
bearing length; the two side contributions are accounted for together, not as
two independent full-central-member single-shear connections. The minimum of
the four equations would be a *conditional one-bolt reference lateral-yield
component* only if the NDS prerequisites and symmetric actions are established.

Section 12.3.1 requires contacting faces, load perpendicular to the bolt
axis, and qualifying end/edge distances and spacing. Section 12.3.5.4 uses
the **smaller** of unequal side-member bearing lengths for both sides; it
does not resolve unequal side forces or different side-member bearing
properties. Each shear plane needs a consistent load path. If the two side
posts receive unequal, opposite, or eccentric actions, do not apply the
symmetric four-mode result or multiply a single-shear value by two without a
documented whole-fastener bearing/bending analysis. Section 12.3.8's
adjacent-member procedure is for **four or more members**, not this stack.

[`fea/dowel_yield.single_shear`](../../fea/dowel_yield.py) is **not** a
usable double-shear helper: it explicitly models two members and one shear
plane with six single-shear modes. The separate
[`wood_steel_double_shear_reference`](../../mini_moonboard/bolted_steel_wood_double_shear.py)
implements a symmetric **wood-main/steel-side** component; its steel bearing
input and one wood grain angle do not represent three solid DF-L members.
The [wood-to-wood single-shear wrapper](../../mini_moonboard/bolted_wood_wood_yield.py)
is likewise not applicable to this whole stack. No existing helper produces
a qualified wood–wood–wood double-shear result.

## Inputs and checks required before any calculation

1. **Geometry and contact:** actual connected member identities, species
   and grade; center and both side bearing lengths *along the delivered bolt*;
   actual member face contacts/gaps; bolt-axis and hole-center coordinates;
   exact end, edge, row, and neighboring-bore geometry in all three members.
   Verify an ordinary bolt hole and alignment under §12.1.3.2; the nominal
   38.1/139.7/38.1 mm stack is not a substitute for measured bearing lengths.
2. **Same-case actions:** for every adopted candidate load case, determine
   the simultaneous local force vector and moment delivered to **each** side
   post and the backer at **each** bolt. Separate lateral load perpendicular
   to the bolt from bolt-axis tension/prying. Establish whether the side
   actions and support conditions actually meet symmetric double shear;
   resolve eccentricity, slip/contact, load sharing among bolts, and the
   backer-to-header/post load path rather than presuming equal halves.
3. **Wood and bolt properties:** confirm all three pieces are qualifying
   solid DF-L; determine each grain vector, lateral load-to-grain angle, and
   bolt-axis-to-grain orientation. Obtain the delivered bolt's full-body and
   root diameters, shank and thread bearing length in **each** member, bolt
   bending-yield property/moment, grade/product evidence, grip, length, nut
   engagement, and washers. §§12.3.3–12.3.7 govern the bearing and diameter
   inputs. Full-body diameter is permitted for a threaded full-body fastener
   only when thread bearing length is at most one-quarter of the bearing
   length in every member holding threads, absent a detailed analysis.
   Determine both side-member bearing strengths, not just a central DF-L
   value. The Table 12.3.1B reduction term uses the maximum load-to-grain
   angle of the connected members. Axis-parallel-to-grain/end-grain insertion
   needs the special main-member bearing rule (§12.3.3.4) and applicable
   end-grain adjustment (§12.5.2.2); do not silently use side-grain inputs.
4. **Placement and local failure:** classify loaded/unloaded edges and
   end compression/tension in each member from the actual force vectors,
   then check §§12.1.2, 12.1.3.4, and Tables 12.5.1A–D. Section 12.5.1.2
   applies the smallest relevant geometry factor to all fasteners in a
   multiple-shear connection. Assess splitting, cross-grain tension and
   shrinkage restraint, net-section/row/group tear-out, and other local
   stresses (§§12.5.1.3, 12.6); a nominal clear hole is not proof of those
   limits. Do not extrapolate square-cut end distances to an oblique end
   without a justified geometric method.
5. **Full assembly:** §12.1.3.3 requires a standard cut washer or adequate
   metal plate/strap under the head and nut where they bear on wood. Check
   actual washer footprint, wood contact/crushing, local bolt-head/nut seat,
   bolt axial/shear/bending interaction, thread engagement, and tool access.
   Apply applicable 2024 NDS Chapter 11 adjustment and group-action rules
   only after the one-bolt method and complete bolt layout are established.
   A one-bolt lateral-yield minimum alone cannot rate the bolt group, the
   backer/header transfer, the kicker support, or a same-case joint demand.

No bolt size, hole coordinate, capacity, safety factor, or construction
instruction is selected by this note. The fixed kicker/panel screw layout
and kerf-right edge support remain separate geometry obligations.

[nds12]: https://awc.org/wp-content/uploads/2026/08/AWC_NDS2024_withCommentary_20250328_WebsiteChapter-12-%E2%80%93-Dowel-type-fasteners.pdf
