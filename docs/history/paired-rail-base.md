# Paired horizontal rails and center-principal base attachment

This candidate replaces the two single 3×6 middle rails with four independent
2×6 rails and adds a direct center-principal-to-header bracket. Vertical members
remain single stock. The preceding all-2×6 and selectively enlarged variants
remain available as historical designs.

The lumber schedule contains thirteen 2×6 members, two single 3×6 members
(center principal and post), and one single 2×10 header. The eight plywood
panels/gussets remain. Hardware comprises 56 panel/kicker screws, 16 bolts,
19 brackets and 114 manufacturer-specified bracket screws.

[Interactive model](https://mckayreedmoore.github.io/mini-moonboard/?model=paired-rail-base-development&view=rear),
[CAD render](../exports/paired-rail-base-development/open-frame.png), and
[geometry audit](../fea/results/paired-rail-base-audit-v1.json).

![Center base connection, cropped CAD detail](../exports/paired-rail-base-development/base-connection.png)

The detail crops the header and principal for visibility; full members remain
in the STEP file and interactive model.

## What the apparent base gap meant

The previous center principal already bears on the header at Z225 mm. The
header occupies Z186.9–225 mm, between the principal and the short center post.
There is no air gap at either bearing interface. However, the principal lacked
a direct fastening connection to the header or post.

The new ML24Z bracket sits on the header top beside the principal's right side.
Those two mounting planes are perpendicular even though the principal's grain
slopes. Three SDS25112 screws enter the header and three enter the principal.
The existing bracket underneath connects the header to the center post. This
adds a visible mechanical connection without a principal housing, header slot,
or doubled vertical member. The bracket is a nominal product model; its actual
installation and resistance in these load directions remain unqualified.

A plywood side gusset was considered but would cross the continuous header.
The angle bracket avoids cutting around or through that obstruction.

## Horizontal panel receivers

Each side of the middle panel seam now has its own 38.1 ×139.7 mm rail. Each
rail has two end brackets; no glue, composite stiffness or automatic load
sharing between the adjacent rails is assumed. Panel screw rows are centered
19.05 mm above and below the seam. Opposing center brackets are staggered
through the frame depth to avoid their screw shafts meeting inside the single
center principal. Hold and LED service pockets remain; bottom rails remain
square-cut and pocket-free.

The upper right center kicker screw moves from Z160 to Z140 mm. Its distance
to the post top increases from 26.9 to 46.9 mm. The previous placement failed
even the 31.75 mm manufacturer end-distance screen; the new position also
exceeds the 44.45 mm reversible-load screen. Full screw checks use actual
receiver grain directions and cut boundaries, rather than only a generic
diameter multiplier. See the [reference record](selective-connection-reference.json)
and [preceding connection audit](../fea/results/selective-connection-strength-v1.json).
The upper-right center-principal panel screw also moves 5 mm downhill,
increasing its top-end distance from 41.9 to 46.9 mm.

This render retains ordinary panel/kicker screws. The current direction is to
develop inserts with machine screws where geometry and resistance support
them; this revision does not install or qualify that separate hardware change.
Nominal insert-space checks are retained and are not pilot-hole instructions.

## What remains unresolved

The bracket closes the missing attachment, but does not establish the header's
load-transfer strength. The principal bearing footprint extends 48.1627 mm
behind the center post. The flat header's grain runs across the frame, so this
rearward transfer cannot be validated using ordinary along-grain beam bending
values. One geometric option is a deeper single post beneath the full bearing
footprint; that option is not installed in this candidate.

Connection forces, bracket combined loading, service-pocket net sections,
panel deflection, leg stability and actual floor behavior still need analysis.
No older floor equilibrium or finite-element result transfers to this revised
assembly. Geometry checks and hardware counts do not constitute a load rating.
The model and exports remain **not build-ready**.

Manufacturer guidance requires checking the supporting wood dimensions,
fastener installation and each connection's application; a catalog bracket
alone does not qualify the joint. See [Simpson's general connector notes](https://www.strongtie.com/products/connectors/wood-construction-connectors/technical-notes/general-notes).

## Verification

The saved audit passes the tested receiver, occupied-hole, wood/hardware
collision, nominal insert-reservation, bearing-coverage and SPAX screw
edge/end/spacing gates. All 56 panel/kicker screws are assessed, and all six
new base-bracket screws have 35.54476 mm gross wood penetration. These gates
leave structural, joint and floor qualification false.

Fifteen targeted tests passed across the new geometry, artifact integrity,
preceding connection evidence, preserved selective model and selector checks.
Independent correctness, testing and consistency reviews identified missing
new-artifact coverage and stale current-design links; both were corrected.
A second independent review pass found no substantive issues. Ruff and diff
checks passed. These are software and nominal CAD checks, not physical tests.
The browser check loaded all 229 entries, exercised default selection and
navigation, selected the center principal, verified the hold grid, and captured
desktop/mobile views without browser or request errors. The full-frame and
cropped base-connection CAD renders were inspected directly.

Reproduce the current geometry checks and artifact authentication with:

```sh
uv run pytest -q tests/test_paired_rail_frame.py tests/test_paired_rail_audit.py \
  tests/test_paired_rail_artifacts.py tests/test_selective_connection_strength.py
```

The [previous full-CI limitations](selective-2x6-layout.md#verification-and-ci-limits)
remain separate; this revision does not claim that unrelated historical
floating-point replay failures have been fixed.
