# Independent review: current mass source-to-topology map

The attempt 03 map is consistent with its pinned mass, geometry, and receiver
sources for its stated inventory-only purpose. I verified the supplied hashes
for the JSON (`308a329a0b40db454d5b0e27c9ec2eca92d66eec96bfb222df5f7b7185bef4d4`),
builder (`16645507e1910e038e83b5acc0026b9fb12940db0f194732b355b4ef76a982f9`),
focused tests (`6249737d78113f44bc39e1e06ebd53fa93c1d99ea171197b0f8ef4ba6576090b`),
canonical note (`311ee2ab272c152cb85a2747e289e57a7ae7de6d3d356efada455d1b7d4c5eb4`),
and attempt README (`e0a4db4bf84d473fd3c7065df284e76218b034ea55df54f6a5e79c1920d879d9`).
All seven JSON source pins also match their current files.

The 778 map rows cover the 778 distinct board-weight inventory and centroid
export identities exactly once. Their category counts are 50 physical
members, 460 candidate hardware components, 60 retained frame-bolt
components, 142 T-nuts, and 66 screw-envelope proxies. Every mapped row
retains its exported mass, center, gravity force, and origin moment; the
unique source-entity IDs also total 778. Independently summing the source
rows gives `224.4207766683882 kg`, center
`[-1.6445371504, 697.8575810, 1033.6090566] mm`, gravity force
`[0, 0, -2200.816009515] N`, and origin moment
`[-1535856.136568, -3619.323688877, 0] N·mm`, matching the map and centroid
export. The separate 25 kg equipment allowance is excluded from the 778 rows.

Geometry references also reconcile: 50 physical-member nodes, 92 candidate
bolt axes, and 12 retained bolt axes agree with the current graph and scene;
candidate receiver sets and retained member pairs agree without assigning
head-to-nut order. All 66 current screw axes use 63.5 mm CAD envelope lengths;
their centers match each current axis midpoint. The eight moved axes match
their current starts and unchanged directions. The inventory’s 50.8 mm
`source_occupied_length_mm` remains separately labeled as a historical
analysis field. These are mass-envelope proxies, not detailed purchased
Hillman screw bodies or engagement measurements.

The attempt 03 wording correctly makes the 728 one-carrier-per-nonmember-row
count illustrative. Optional carriers are not required where a documented
aggregate or condensed representation preserves the exact source gravity
force and first moments and the inertia and attachment behavior relevant to
the intended analysis. The map keeps every source row for accounting and
allows each row to be represented once; it does not implement or prescribe
that reduced representation. All `solver_dof_id` values are null, the
solver-DOF mapping and reduced mass-transfer flags are false, and implemented
carrier count is zero. Graph member references do not claim solver
attachments or a load split. T-nut/slot, hardware, and screw connections
remain outside this map unless a later intended local interaction model
requires them.

The owner report pin resolves to the actual
[site/owner-wood-joints-review-report.json](../../../../../site/owner-wood-joints-review-report.json)
and its SHA-256 matches `148f97623573558cd6a6c53f8a5399f2b30549d6aa1ed13c326dfe1bc3e9d695`.
All five local links in the canonical note and the local integration-note
link in the attempt README resolve. In the source table the owner report is
identified by label and hash; the exact filename is supplied by the JSON
source pin and linked above.

This review used read-only JSON and Markdown checks with independent
resultant recomputation. No CAD, native solve, Git command, mesh, or model
attachment was used. The map is a source-inventory and topology reference;
it does not establish a solver mass-transfer route, resolved member demand,
joint capacity, or mechanical acceptance.
