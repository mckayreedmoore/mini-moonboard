# HL35 solid-center installed trial — rejected

This is one conditional geometry trial, not a connector selection, capacity
finding, purchase instruction, or drilling release. Regenerate the detailed
numbers with `uv run python -m scripts.hardware_first_center_hl35 --output
docs/bolted-candidate-prototypes/hardware_first_center_hl35.json`.

The trial keeps the original header underside at Z = 238.9 mm and makes a
solid 3.5-in-deep header upward to Z = 327.8 mm. Solid 3.5-in center posts
remain full height to Z = 238.9 mm; solid center principal toes are trimmed
to Z = 327.8 mm. HL35 pairs sit on both X faces of each center member, with
upper and lower angles slid to opposite ends of the available 139.7-mm
header depth. The catalog dimensions support a 127-mm angle length,
31.75/95.25-mm along-bend hole centers, and a 50.8-mm vertical-leg hole
offset from the bend. The model assumes the horizontal-flange hole is also
50.8 mm from the bend; that X offset is **not dimensioned** in the cited
[Simpson HL catalog drawing](https://dhcsupplies.s3.us-east-2.amazonaws.com/Documents/simpson-strong-tie/hl-angles.pdf)
and is not a factory drilling coordinate. All 66 kerf-right panel/kicker
axes are read, never changed. The nominal bore model uses a conditional
14.2875-mm wood hole for a half-inch bolt and full cylinders through each
receiver.

The prior downward-only 4×6 header idea is independently invalid: lowering
its underside to Z = 188.1 mm overlaps the unchanged post by 50.8 mm.
Shortening that post leaves the protected Z = 192-mm upper kicker screw
3.9 mm above the post end. The upward trial avoids this particular failure
and preserves *all* original post material, but still fails installation:

- Maximum possible upper/lower HL35 Y-row separation is 12.7 mm, less than
  the 14.2875-mm nominal bore diameter. All eight corresponding full header
  bore pairs overlap by about 623 mm³ each. They cannot be independent bolts.
- Each lower post's second 14.2875-mm through-bore intersects its protected
  Z = 192-mm kicker screw using the **frozen modeled 50.8-mm occupied**
  envelope. The 63.5-mm purchased *overall* screw length gives the same
  nominal clash if conditionally treated as an occupied cylinder; it is not
  a verified shaft length. The upper
  principal's first through-bore on each face also exits its oblique toe
  (about 12,022 mm³ of each bore outside wood).
- Widening each post preserves its original full-width support footprint,
  yet the physical kerf-right kicker inner edges still overhang the new
  post by 23.9625 mm left and 27.1375 mm right. An axis inside wood is not
  full edge support.

The idealized inner HL35 horizontal seats also fail. A 3.25-in (82.55-mm)
catalog flange reach and an **assumed**, illustrative 4.55-mm plate
thickness give about 29,528 mm³ of left/right inner-plate envelope overlap
at each level. Each inner plate envelope additionally intersects the
opposite principal (upper) or post (lower) by about 18,173 mm³. These are
reproducible ideal rectangular-envelope volumes from the actual CAD timber
solids, **not delivered bracket geometry or measured steel collisions**;
bend radii, holes, coating, and manufacturing tolerances are omitted. The
ideal inner plate envelopes have no volumetric intersection over 0.01 mm³
with the six existing panel/kicker solids. Heads, nuts, washers, outer
plates, and other hardware are not modeled for panel interference.

The older projected Y/Z overlap between a header bolt at X = −139.85 mm
and kicker screw at X = −70 mm is **not** a 3D clash: the axes are 69.85 mm
apart in X, well beyond their 9.2139-mm combined nominal radii. The clashes
reported above come from actual 3D occupied-cylinder intersections.

This installed trial is rejected. A shared upper/lower bolt stack or shifted
posts would be a *different* concept with its own geometry and resistance
checks; catalog loads cannot simply be doubled. Because this trial already
fails plate fit, independent bores, protected screw clearance, and edge
support, no
washer/head/nut/tool/withdrawal sizing, neighboring-frame clash resolution,
NDS joint check, or native solve is claimed. Do not drill or fabricate from
these coordinates.

The reported 66 positive screw/receiver intersections establish only that
each modeled axis reaches some receiver wood. They do **not** establish
required embedment, full screw-body fit, or continuous panel-edge backing.
The kicker overhang values are relative to these two center posts, not every
possible backing arrangement.
