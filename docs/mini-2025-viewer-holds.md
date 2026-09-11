# Mini MoonBoard 2025 viewer holds

The viewer uses 138 generic visual placeholders: 128 on the main face and ten
on the kicker. These are approximate illustrations for previewing the board,
not scans, faithful reproductions, printable replacement holds, or an
installation guide. They do not establish grip shape, clearance, bolt length,
connection resistance, or frame, panel, and floor adequacy.

## Viewer controls

Choose **Mini MoonBoard 2025** in **Hold setup** (the default). The holds appear
after the selected frame's metadata loads. Use **Show holds** to hide or show
them, and **View holds from front**
to fit the board beside the controls on desktop or below them on a phone.
Click a hold to see its family, grid location, and estimated appearance. The
`holds=off` URL option preserves a hidden preview when changing frame designs.
The `setup=2020` URL option selects the alternative Mini 2020 hold layout;
changing the setup preserves the selected frame and visibility preference.
The connection inspector temporarily hides holds and restores that preference
when returning to the assembly. Hold geometry is excluded from CAD exports,
frame weight, and engineering calculations.

Use [Problem highlights](viewer-problem-highlights.md) to mark start, hand,
foot, and finish holds and share the selection through a link.

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

Every entry selects an original generic edge, pinch, sloper, jug, wedge,
triangle, crescent, or tapered-pinch
primitive. The broad categories and visual directions were chosen by looking
at the product image. Width, height, and depth use deliberately rounded,
reusable millimeter buckets. They are not traced silhouettes or measured
physical dimensions. Rotations are approximate clockwise degrees as viewed
from the front, relative to an upright generic shape with local +Y up; they
are not Moon's numbered orientation marks.
An independent image review checks elongated axes and visible directional tips.
Symmetric generic profiles cannot show every real hold's facing or grip details.

Three additional analytic profiles make selected directional holds easier to
distinguish: a rounded triangle with its tip at local +Y, a crescent opening
toward local +Y, and an elongated pinch with its narrow end toward local +Y.
An independent front-image review checked this limited refinement:

| Position | Generic profile | Clockwise rotation | Visible direction |
| --- | --- | ---: | --- |
| D11 | Triangle | −10° | Tip up, slightly left |
| G11 | Triangle | 180° | Tip down |
| K11 | Crescent | 45° | Opening upper-right |
| H9 | Tapered pinch | 0° | Narrow end up |
| B6 | Crescent | −35° | Opening upper-left |
| K6 | Triangle | 15° | Tip up, slightly right |
| F5 | Tapered pinch | −90° | Narrow end left |
| G2 | Crescent | 0° | Opening up |

F5 swaps its width/height buckets to preserve its horizontal long axis with the
new profile. E10 retains a symmetric pinch because its narrow-end direction is
unclear in this reference. These category cues remain estimates, not measured
gripping surfaces or manufacturer orientation marks.

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

An independent implementation review checked the eight reusable parametric
profiles against that policy: they do not trace distinctive individual hold
outlines and have no branding, mounting bores, countersinks, or replacement-hold
engineering. The review also checked the color layout against the source image;
the identified E3/F3 transcription swap was corrected before publication.
