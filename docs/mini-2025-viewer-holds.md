# Mini MoonBoard 2025 viewer holds

The viewer uses 138 generic visual placeholders: 128 on the main face and ten
on the kicker. These are approximate illustrations for previewing the board,
not scans, faithful reproductions, printable replacement holds, or an
installation guide. They do not establish grip shape, clearance, bolt length,
connection resistance, or frame, panel, and floor adequacy.

## Viewer controls

The holds appear by default after the selected frame's metadata loads. Use
**Mini MoonBoard 2025 holds** to hide or show them, and **View holds from front**
to fit the board beside the controls on desktop or below them on a phone.
Click a hold to see its family, grid location, and estimated appearance. The
`holds=off` URL option preserves a hidden preview when changing frame designs.
The connection inspector temporarily hides holds and restores that preference
when returning to the assembly. Hold geometry is excluded from CAD exports,
frame weight, and engineering calculations.

## Sources and observed layout

The [official Mini MoonBoard 2025 product page](https://us.moonclimbing.com/products/mini-moonboard-2025-hold-set)
identifies a 138-hold bundle containing Original School Holds, School Set F,
and Wood Sets B and C. Its publicly served
[2025 setup image](https://cdn.shopify.com/s/files/1/0942/2667/8060/files/2025-mini-setup.png?v=1770821238)
shows the A–K, 1–12 main-face grid. The data in
[`site/mini-2025-holds.json`](../site/mini-2025-holds.json) transcribes its occupied
positions and visible color families. C1, D1, H1, and I1 are empty. The face has
40 yellow Original holds, 40 blue School F holds, and 48 wooden holds.

The [Original School Holds page](https://eu.moonclimbing.com/original-school-holds.html)
confirms 40 hand holds and ten footholds. The
[School Set F page](https://moonclimbing.com/new-school-holds-set-f.html)
confirms 40 sky-blue holds. The
[Wood Set B page](https://moonclimbing.com/wood-holds-set-b.html)
confirms 24 wood holds and describes nominal thickness groups. The
[Wood Set C page](https://us.moonclimbing.com/products/moonboard-wood-holds-set-c)
confirms another 24 holds. Those details
support the family inventory; they do not identify each pictured wooden hold.
References were checked on September 11, 2026. Source photographs and artwork
are not included in the repository or loaded by the viewer.

## Estimated appearance

Every entry selects an original generic edge, pinch, sloper, jug, or wedge
primitive. The broad categories and visual directions were chosen by looking
at the product image. Width, height, and depth use deliberately rounded,
reusable millimeter buckets. They are not traced silhouettes or measured
physical dimensions. Rotations are approximate clockwise degrees as viewed
from the front, relative to an upright generic shape with local +Y up; they
are not Moon's numbered orientation marks.

Wooden holds share a `wood` family because the photo alone does not establish
which belong to Set B versus Set C. Grid labels such as A12 identify board
positions, not manufacturer hold numbers. No manufacturer hold IDs have been
invented. Similarly, `KICK1` through `KICK10` identify viewer slots, not
manufacturer part numbers. The setup image does not show the kicker; its ten
placeholders use the viewer's kicker mounting locations and upright generic
wedges. This arrangement and its rotations are illustrative, not a verified
2025 installation schedule.

Use Moon's current app and installation references, together with the actual
holds, to install the physical set. Updating a placeholder with better visual
information must preserve the distinction between observed layout and estimated
geometry. Faithful scans or reproductions remain subject to the project's
[hold scanning and publication policy](hold-scanning-and-ip.md).

An independent implementation review checked the five reusable parametric
profiles against that policy: they do not trace distinctive individual hold
outlines and have no branding, mounting bores, countersinks, or replacement-hold
engineering. The review also checked the color layout against the source image;
the identified E3/F3 transcription swap was corrected before publication.
