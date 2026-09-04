# Panel artwork and viewer overlays

Moon Climbing's [self-build guide](https://us.moonclimbing.com/blogs/guides/how-to-build-your-moonboard)
links its official [Final Artwork archive](https://moonclimbing.com/media/moonboard-pdf/Final_Artwork.zip)
as the specifications for completing a MoonBoard. The supplied local archive
matches that filename and contains panel image/logo and letter/number artwork.

Use the official archive for the user's private physical panel artwork. It is
not copied into this public repository or GitHub Pages deployment: the page and
archive do not state a redistribution license. A direct official link is not
the same thing as permission to rehost or sublicense the files. Obtain written
permission from Moon before committing or serving the branded artwork here.

The viewer therefore provides a non-logo, data-derived overlay switcher:

- `None` leaves the drilled panel clear.
- `Grid labels` adds A–K and 1–12 at the canonical Mini grid positions.
- `High-contrast grid labels` uses the same geometry with a white treatment.

The labels are display-only decal planes placed 0.5 mm in front of the actual
underside face and rotated to lie on its 40-degree slope. They use
climber-facing coordinates: A begins at climber-left, and rows 1–12 run in the
200 mm in-panel margin at climber-left. They do not alter the STEP model, hole datums, cut list, or FEA
model. A future licensed Moon-artwork overlay can use the same selector without
changing the CAD geometry.

The independent **Overall V1 dimensions** switch shows the CAD assembly AABB:
2762.4 mm / 108.76 in wide, 1636.3 mm / 64.42 in deep, and 2150.8 mm / 84.68
in high. Those values include both exterior legs and exclude the crash pad;
they are provisional V1 geometry, not Moon's official board-only envelope.

The viewer's selectable Mckay figure is a simplified 1727.2 mm / 5 ft 8 in
scale reference. It is not a scanned person, a CAD assembly child, a cut-list
item, a stability mass, or an FEA load.

The viewer reflects the CAD assembly across X for this climber-facing
presentation: the source template's A column and the visible A decal therefore
occupy the same climber-left column. This is a view transform only; the
manufacturing schedules retain the official template's lower-left datum.
