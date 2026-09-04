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
