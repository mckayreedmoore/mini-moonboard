# Owner barrel native connector inventory

`scripts/owner_barrel_native_connector_inventory.py` builds a source-bound,
preparation-only connector inventory from the active `build_viewer_assembly()`:
outward X = ±180 mm center posts, two kicker backers, and their nominal
header-to-backer attachment duties. An original X = ±70 mm, no-backer assembly
can be supplied explicitly as a detached trial. The provisional outer-header
forward row is Y = −85 mm with a recessed-head envelope. The inventory does
not read old ML24Z case reactions or run FEA.

`build_inventory()` returns exact station-to-connector ownership for 24 former
angle duties, 48 diagnostic bolt axes, and 48 paired barrel bodies. Each bolt
record has its timber pair, start, direction, nominal length and diameter,
paired barrel name, and a provisional body-midpoint axis point. Actual barrel
body intersection with exactly one station timber identifies the receiving
member; shaft intersection order identifies the entry member. Ambiguous hosts
fail closed. Each barrel record has its recovered cylindrical body axis.
The midpoint is a **provisional viewer thread-axis pose**, not a controlled barrel
drawing or a resolved wood-bearing reaction. Producer and input file hashes,
plus a digest of the returned record, bind this inventory to its source.
Per-bolt modeled shaft reach to that point is recorded as a diagnostic, and
shortfall does not become a load-bearing connector or native-ready claim.
The current viewer moves the six bottom/lower/upper outer-rail barrels to a
60 mm setback and models twelve nominal 6 in shafts. These pass the assumed
thread-axis points by 1.849 mm. The earlier 5 in / 70 mm viewer had twelve
33.551 mm shortfalls; that is preserved in the historical detached length
screen, not in this current inventory. Passing a provisional axis does not
establish delivered thread engagement, washer/head fit, bottoming clearance,
or a complete joint.

The active candidate connection set has 130 names: 66 original panel/kicker
screw axes, 12 retained frame-bolt axes, 48 former-angle trial bolts, and four
nominal header-to-backer trial bolts. The four fixed center-kicker screws are
mapped to the two separate backers, two per backer. Both backers have two
modeled header-attachment paths, with status
`nominal_geometry_defined_unqualified`. No stiffness, capacity, delivered fit,
or assembly method is established. The 24 legacy angle stations and 144 SDS
axes appear only in `excluded_legacy`.

For the optional original-post trial, the four center-kicker screws retain
their source post receivers. There are 126 candidate names and no backers or
backer-attachment duties. `center_kicker_screw_landings` records the four
receivers in either pose; `backers`, `backer_screw_landings`, and
`backer_attachment_bolts` are empty in the original trial.

`missing_native_inputs` records the contact and connector laws still needed:
compression-only butt-face cells and stiffness; reconciliation of existing
header bearing and floor support; bolt axial tension, lateral bearing and
clearance; barrel-to-wood reaction and stiffness; and recheck of retained frame
bolts. The active outward/backer pose also lists its unresolved attachment.
The inventory always reports
`native_ready: false`, `native_solve: false`, `capacities_claimed: false`, and
`release_claimed: false`. It supplies names and geometry for a future native
adapter, not force demands, capacities, drilling dimensions, or fabrication
approval.
