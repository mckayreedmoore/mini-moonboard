# Owner barrel native connector inventory

`scripts/owner_barrel_native_connector_inventory.py` builds a source-bound,
preparation-only connector inventory from `build_viewer_assembly()`. That is the
current kerf-right viewer pose, including the provisional outer-header forward
row at Y = −85 mm and its recessed-head envelope. It does not read old ML24Z
case reactions and does not run FEA.

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
The current 5 in shaft envelope is about **33.551 mm short** of the provisional
thread-axis point at both rows of each bottom/lower/upper outer-rail station:
**12 modeled bolts across six stations**. This is a concrete `REVISE` geometry
defect, not an uncertainty that a bolt-strength table can resolve. A longer
ordinary [1/4-20 × 7 in hex bolt at Home Depot][seven] exists, but its
delivered thread span,
washer/head fit, and full joint path have not been established here.

The candidate connection set contains the original 66 panel/kicker screw axes,
the 12 retained frame-bolt axes, and the 48 trial bolts. The 24 legacy angle
stations and 144 SDS axes appear only in `excluded_legacy`; none is a candidate
connector. The four fixed center-kicker screws are assigned to the two separate
inner kicker backers, two screws per backer. Their source axes are preserved.
Both backers have `frame_attachment_status: missing` and zero modeled frame
attachment connections.

`missing_native_inputs` records the contact and connector laws still needed:
compression-only butt-face cells and stiffness; reconciliation of existing
header bearing and floor support; bolt axial tension, lateral bearing and
clearance; barrel-to-wood reaction and stiffness; backer frame attachment; and
recheck of retained frame bolts. The inventory always reports
`native_ready: false`, `native_solve: false`, `capacities_claimed: false`, and
`release_claimed: false`. It supplies names and geometry for a future native
adapter, not force demands, capacities, drilling dimensions, or fabrication
approval.

[seven]: https://www.homedepot.com/p/204281599
