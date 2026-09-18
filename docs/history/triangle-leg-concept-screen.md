# Triangular side-rail concept screen

The owner authorized investigating a triangular side frame as an alternative to
enlarging the upper leg connection. This bounded calculation finds a plausible
catalog-strap geometry for a raised side rail, but does **not** establish that the
assembled rail reduces the upper joint demand. No rail geometry, drilling or
hardware is selected for construction.

The calculation retains the shoe-free 277 mm kicker candidate, its existing
upper four-bolt leg joints and single 2×6 legs. Accepted panels and T-nuts remain
the design basis. Floor supports retain the explicit no-slip assumption. A rail
cannot be credited merely with preventing foot spreading: the existing response
model already prevents that translation at the active feet.

## Proposed physical load path

Use one single 2×6 rail per side, actual section 38.1 × 139.7 mm, with its grain
horizontal in the fore-aft direction. For the left side:

- The rail occupies X = −1219.2 to −1181.1 mm, alongside the existing leg and
  in the same thickness plane as the outer post and rim.
- It extends from Y = −36 to approximately 1510 mm. The front end butts against
  the outer post's rear face; there is no fictitious overlap at that connection.
- Its bottom and top are Z = 99.2 and 238.9 mm. The rail is elevated and has no
  floor contact. Its top aligns with the header underside.
- A proposed rear lap group is centered at approximately Y = 1372.5,
  Z = 169.05 mm on the leg centerline. Four smooth-shank 3/8-inch bolts use a
  parallelogram with 40 mm pitch along the leg and 45 mm pitch along the rail.
  Retain washers, nuts and sufficient smooth shank through both members. This
  is an analytical placement proposal, not a checked drilling schedule.
- A straight LSTA12 strap bridges the front butt joint on a common X side face.
  Its proposed center is Y = −36, Z = 169.05 mm. A 304.8 × 31.75 mm envelope
  occupies Y = −188.4 to 116.4 mm and Z = 153.175 to 184.925 mm. The post spans
  Y = −270.95 to −36 mm and Z = 0 to 238.9 mm, so the gross strap envelope fits
  both receiving faces. Ten SD9112 screws, five in each member, are required by
  the cited connection schedule.

Mirror X for the right rail. In tension the force path is leg → rear bolts →
rail → strap and screws → outer post. In compression, the rail end can bear
against the post rear face. Any response implementation must use finite
fastener stiffness, actual eccentricity, tension-only strap behavior and
unilateral butt bearing. It must not replace these parts with a rigid tie.

The strap envelope fits; the exact hole coordinates, screw tips, installation
access and collisions with existing attachments have not been modeled. One
strap is proposed initially. Opposing straps would require checking screw
interference and actual force sharing, rather than simply doubling capacity.

## Required force scale

The native 250 lb doubled-downward-load plus 300 N rearward case gives the left
upper joint an in-plane moment of −352.772 N·m and resultant
`(−48.938, +678.211, −2864.923) N`.

Holding that force fixed, an equal-stiffness four-bolt calculation using nominal
smooth 3/8-inch shanks reaches its conditional lateral reference at approximately
66.405 N·m in the existing moment direction. This generous upper-connection
comparison therefore requires approximately **286.366 N·m** of moment relief.
It excludes out-of-plane demands and does not qualify the currently installed
threaded-bearing geometry.

If a horizontal rail force and the corresponding change in floor reaction form
a couple over the rail joint height, the required transfer scale is:

| Rail joint height | Horizontal force for 286.366 N·m relief | Comparison with four rear bolts |
| --- | ---: | ---: |
| 69.85 mm: floor-level 2×6 rail center | 4.100 kN | 0.959 |
| 169.05 mm: raised rail center | 1.694 kN | 0.396 |

The rear-bolt comparison uses four times a 1.068 kN single-fastener reference
for pure horizontal loading, horizontal rail grain and actual leg grain. It
uses the existing yield-equation method with G = 0.50, 45 ksi bolt bending yield,
38.1 mm member thicknesses and adjustment factors of one. It is a **force-scale
comparison**, not a group qualification: it excludes joint moments, unequal
distribution, axial demands, local wood failure and installation tolerances.

These calculations hold the upper force and reaction geometry fixed. The rail
would change assembly stiffness and reactions, just as the wider-leg and sole
experiments did. Consequently, 1.694 kN is not a predicted rail force and this
table is not evidence that the upper connection will pass. It explains why a
raised rail is a more credible bounded concept than a floor-level rail, whose
required force already approaches the simple four-bolt reference before the
omitted effects.

## Catalog connection investigation

The initial ML24 angle proposal was rejected geometrically. With the bend line
across the rail thickness, its outer screw stations span 76.2 mm across a
38.1 mm receiver. Rotating the angle places flange holes as far as 42.243 mm
from the corner on a 38.1 mm post face. The proposed top placement also cannot
assume post material above Z = 238.9 mm. Those arrangements do not provide all
six specified screw receivers.

The straight LSTA12 avoids those corner constraints. Simpson lists the
[LSTA12 with ten SD9112 screws](https://www.strongtie.com/products/fastening-systems/technical-notes/sd-connector-screw-approved-connectors).
[ICC-ES ESR-3096](https://icc-es.org/wp-content/uploads/report-directory/ESR-3096.pdf),
Section 3.1.26 and Table 26, documents its 12-inch length, 1¼-inch width,
staggered holes, ten screws split equally between members, and **1,235 lbf
allowable tension at C_D = 1.6**. Section 3.2.2 requires wood specific gravity
at least 0.50, dry-service moisture limits and member thickness at least the
specified screw length.

Crucially, Table 26 expressly states that its loads do not apply to other load
durations. The current assessment uses C_D = 1.0. **No normal-duration capacity
is established by dividing 1,235 lbf by 1.6**, and this screen does not make that
substitution. A suitable normal-duration connection basis, actual post
cross-grain loading and the installed fastener detail remain necessary before
the front connection could be accepted.

The inspected ESR PDF has SHA-256
`ca6a6cd0b714512fa7a90a6e538c0997ee0f8f2223c73af1f752191fd5da27ad`.
The primary report, rather than a reseller's capacity table, governs the
interpretation above.

## Disposition and reproduction

This completes a hand-calculation and catalog-fit investigation of one
triangular side-rail concept. The ML24-ended version is rejected. The raised,
LSTA12-ended version remains a plausible geometry with unresolved connection
resistance and no assembled result. It is not selected, and neither a reduced
upper-joint demand nor a whole-frame rating is claimed.

If the separate pivot investigation succeeds, there is no reason to add this
rail and its connections. If a rail proceeds, the next gate is an actual
connection and assembled-response assessment of this finite detail; do not
simulate an unsupported rigid rail merely to obtain a favorable moment.

```sh
uv run python -m fea.triangle_concept_screen
```

The script reads the committed extract of accepted native `current-response-250`
left-leg forces, retains its original report hash, and reproduces the fixed-resultant moment and transfer estimates, and records
the ML24 fit failure and LSTA12 duration limitation. It does not run CAD or the
native solver. The module's lint check passes.
