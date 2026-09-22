# Owner barrel native connector inventory

`scripts/owner_barrel_native_connector_inventory.py` builds a source-bound,
preparation-only connector inventory. Its no-argument default is now the
**current** 46-pair seam-side-post assembly from
`build_integrated_viewer_assembly()`. The historical outward X = ±180 mm
center-post scene with separate kicker backers can be supplied explicitly;
so can the original X = ±70 mm, no-backer detached trial. All poses use the
provisional Y = −85 mm recessed outer-header row. The inventory does not read
old ML24Z case reactions or run FEA.

`build_inventory()` returns exact station-to-connector ownership for 24 former
angle duties. The current integrated pose has **46** diagnostic bolt axes and
46 paired barrel bodies; the historical outward pose has **48** each. Each bolt
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
Both viewer compositions move the six bottom/lower/upper outer-rail barrels to a
60 mm setback and model twelve nominal 6 in shafts. These pass the assumed
thread-axis points by 1.849 mm. The earlier 5 in / 70 mm viewer had twelve
33.551 mm shortfalls; that is preserved in the historical detached length
screen, not in either current viewer inventory. Passing a provisional axis does not
establish delivered thread engagement, washer/head fit, bottoming clearance,
or a complete joint.

The current integrated connection set has **124 names**: 66 original
panel/kicker screw axes, 12 retained frame-bolt axes, and 46 former-angle
trial bolts. The four fixed center-kicker screws land in the widened posts;
there are no separate backers or extra backer fasteners. Each post/header
duty has two trial pairs, while each principal/header duty has **one**.
The integrated pose is checked against the geometric backing trace and its
candidate-only 25.4 mm F1–G1 passage identity. The historical outward set has
130 names, including 48 former-angle and four separate backer-attachment
bolts. The two backers each have two modeled header paths with status
`nominal_geometry_defined_unqualified`. Neither pose has established
stiffness, capacity, delivered fit, or assembly method. The 24 legacy angle
stations and 144 SDS axes appear only in `excluded_legacy`.

For the optional original-post trial, the four center-kicker screws retain
their source post receivers. There are 126 candidate names and no backers or
backer-attachment duties. `center_kicker_screw_landings` records the four
receivers in either pose; `backers`, `backer_screw_landings`, and
`backer_attachment_bolts` are empty in the original trial.

The separate [gross-face contact input](../../scripts/owner_barrel_native_face_contacts.py)
now reads the same integrated assembly. Each of the **24** former-angle timber
pairs has exactly one opposing planar gross contact patch. The 22 two-bolt
faces use four equal-area candidate compression cells each. The two
single-bolt principal/header faces use 16 cells each (**120** total), with
finer front-to-rear resolution near the bolt. All **46** trial bolt
axes cross their own patch within its boundary. Representative gross areas
are 5,322.57 mm² at a top-outer rail, 12,419.33 mm² at a center-post/header
joint, and 5,113.122 mm² at a center-principal/header joint. These are
**uncut** CAD faces: actual bores, edge loss, gaps, partial opening, grain
direction, and delivered contact have not been accounted for. These cells
define locations and tributary gross area, not a verified stiffness or
compression law. In particular, one principal/header bolt plus this face
inventory does not by itself establish a signed moment or twist path.

`missing_native_inputs` records the contact and connector laws still needed:
compression-only butt-face law and stiffness; reconciliation of existing
header bearing and floor support; bolt axial tension, lateral bearing and
clearance; barrel-to-wood reaction and stiffness; and recheck of retained frame
bolts. The historical outward/backer pose also lists its unresolved attachment.
The inventory always reports
`native_ready: false`, `native_solve: false`, `capacities_claimed: false`, and
`release_claimed: false`. It supplies names and geometry for a future native
adapter, not force demands, capacities, drilling dimensions, or fabrication
approval.
