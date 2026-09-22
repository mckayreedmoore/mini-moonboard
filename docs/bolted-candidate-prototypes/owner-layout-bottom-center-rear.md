# Bottom-center rear-face 77 mm owner-layout trial

This source-distinct trial is for the unified 24-duty assembly only. PB02's
`upright_side_cleat` and rear-return chain are historical partial-candidate
geometry and are **not** in this assembly. The original kerf-right frame
timber, 66 panel/kicker screw axes, 12 frame-bolt axes, E1/G1 holds and
T-nuts, LEDs, and existing wiring are not moved or cut. The original
bottom-center bracket duties remain identifiable. This is no drilling or
structural release. **The N-shifted block is a detached exception, not an
owner-compliant layout:** its high N = 399.7 mm projects 50.159032 mm beyond
the adjacent 2×6 rear envelope's N high = 349.540968 mm. No exception has
been approved.

Analytic bounds, before the finite CAD screen:

- Each block is 77 mm X × 57.15 mm local T × 139.7 mm local N at its
  same-side bottom rail/principal butt. X spans [−166.05,−89.05] and
  [89.05,166.05] mm. The block is on the rail rear T face,
  T = [183.474134,240.624134] mm, N = [260,399.7] mm.
- The original bottom rail has T = [240.624134,278.724134] mm and
  N = [209.840968,349.540968] mm. The proposed rear block therefore has
  89.540968 mm N overlap at the rail contact face. No frame member cut is
  proposed. X rows are 26/51 mm from the butt; the rail bore row is
  N = 294.840968 mm, 34.840968 mm above the block's low N edge and
  54.7 mm below the rail's high N edge. The left E1–E2 service passage is
  still present.
- The actual current `wire_072_F1_G1` crosses the right block's X extent
  near T = 219.824134 mm. An initial endpoint-depth estimate put its center
  at N = 253.840968 mm. That was **not** the complete installed route:
  the existing kerf-right STL spans N = [216.246318,281.690590] mm because
  the route ramps into the centered timber passage. Starting the block at
  N = 260 therefore overlaps the routed solid's local-N bound by 21.690590
  mm. Neither the wire nor its channel is moved. This was the only current
  protected LED/T-nut/wire STL AABB candidate against the shifted blocks.
- Original timber stock AABB screening found only each block's intended
  bottom rail as a positive-volume bounding-box candidate. The principal
  is at the intended X butt face. This is not a replacement for exact
  contact and unrelated-timber intersection checks.

The one bounded focused CAD suite found **REVISE**, not a clean nominal pose:
one static test passed and two positive-clearance expectations failed in
35.36 s. Both block-to-rail contact areas are 6894.654525 mm². The
left/right block-to-principal contacts are 5098.76214/3958.670312 mm².
All four rail bores and both principal-1 bores have complete intended host
coverage, but **both principal-2 bores are incomplete**. Their center row
N = 349.7 mm lies 0.159032 mm beyond the original principal's N high edge
349.540968 mm, before accounting for bore radius. The right block has an
exact positive-volume intersection of **533.4042 mm³** with the retained
`wire_072_F1_G1`. No right PB02 cleat was included or used as a blocker.

An upward N shift alone does not give a credible two-row rescue at this
same T/X pose. To clear the actual wire bound requires block low N above
281.690590 mm. With a conservative 4D = 25.4 mm edge at each end and 4D
pitch for two 6.35 mm principal bolts inside wood ending at N = 349.540968
mm, the block low N must be at most 273.340968 mm. Those conditions differ
by 8.349622 mm before tolerances. This is a layout screen, not a claim that
4D alone qualifies a joint.

## Full-envelope rear block with explicit wire relief — analytic only

An owner-envelope-compliant rear block would occupy
N = [209.840968,349.540968] mm at the same X and T bounds. With no
relief, it necessarily intersects the F1–G1 wire. Clipping the existing
wire STL triangles to the right block X = [89.05,166.05] mm gives a routed
occupied envelope T = [217.824157,221.824112] mm and
N = [226.493005,281.690590] mm. This is a 55.197585 mm N sweep, not a
single 4 mm cable at constant depth. A simple front-T-open rectangular
relief would have to span the block's 77 mm X width, at least that N range,
and T from the front face 240.624134 down to at least 217.824157 mm:
22.799977 mm depth before tool, cable, and routing tolerances. It would
leave at most 34.350023 mm rear T web. A rear-T-open relief instead needs
at least 38.349979 mm depth and leaves only 18.800021 mm front web.

The currently drawn principal bore row at T ≈ 212.049134 mm has nominal
radius 3.75 mm, ending at T ≈ 215.799134 mm: just 2.025023 mm before
that front-open relief. The rail bore row N = 294.840968 mm ends at
N = 291.090968 mm on its low side, 9.400378 mm above the relief's high
N bound. Thus the **core bores might remain geometrically separate** from
the exact-minimum rectangular relief, and rail/principal face contact would
remain positive but smaller. This is not an installed-joint pass: the
25.4 mm principal washer reaches T ≈ 224.749134 mm into the proposed
relief, so its full wood bearing seat would be lost. Moving the principal
row rearward enough to seat that washer is a further bolt-row revision and
would need its own edge, bore, contact, tool, and strength check. The stated
relief also has zero modeled wire clearance until explicit allowance is
added, which would remove still more wood.

Neither rectangle is a small local nick. They would change the block's
load-bearing section and the principal washer seats/bolt rows; the existing
full-block bore/contact result cannot transfer. A path-following narrower
channel would be a different, non-simple machined geometry. No relief was
cut in the retained source, no wire was moved, and no completed CAD screen
of a relieved block exists. This is an
unselected **REVISE / owner-and-strength-approval-open** concept, not a
viewer-ready joint or drilling instruction.

The existing 77 mm *front* pose remains REVISE from far nut/tool clashes
with E1/G1 services. The rear pose moves those principal far stacks to
local T ≈ 212.05 mm, away from G1 hold T = 299.824 mm, but introduces the
wire and bore failures above. The focused run printed its exact binding
constraints; installed stack/tool clearances not listed there still require
an integrated 24-duty screen. Delivered hold-bolt length, wiring bend/slack,
tool sequence, purchased hardware, tolerances, and load direction remain
unverified. No native solve, drilling, fabrication, or structural release.
