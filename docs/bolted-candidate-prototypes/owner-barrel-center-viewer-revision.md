# Center-principal/header barrel viewer revision

`build_revised_layout(wood)` in `scripts/owner_barrel_center_layout.py` is a
geometry-only alternative to the unchanged `build_layout(wood)`. It changes
only the two `clip_split_base_center_left/right` principal/header duties.
The other four center duties retain their current solids and axes. The
builder returns the same six-station viewer contract, with every station
marked `REVISE`. It does not change the shared assembly or published scene.

At each revised duty, two vertical bolt and cross-dowel axes use balanced
rows Y = −162.433333 and −138.166667 mm. The washer is a **22.0 mm outside-
diameter trial solid**, 1.651 mm thick, and the bolt shaft/bore represents a
**nominal 4.0 in (101.6 mm) full-thread candidate envelope**. The 22 mm
washer is not a selected or verified retail item; no bolt SKU, thread span,
grade, fit, or resistance is established. The cross-dowel thread-axis offset
remains the provisional 8.001 mm pose, not a controlled Hillman dimension.
No block or alternate wood member is introduced.

The revised rows provide about 2.267 mm nominal clearance at each of three
Y gaps: rear header edge to rear washer, washer to washer, and forward washer
to the unchanged kicker backer. The full 4 in bore and embedded shaft are
contained by the header/principal wood at all four bolts; the intended
header, principal, and barrel core fractions are at least 0.999999. Each
bolt bore intersects the corresponding barrel cross bore. The finite
protected-geometry screen reports no intersection over 1 mm³ against the
142 T-nuts, 142 hold-hole/projection envelopes, 132 lights, 131 wires,
66 panel/kicker screws, and 12 retained frame bolts. The nominal trial also
reports no unrelated-timber or same-duty row hits over that threshold.
Tangency, sub-threshold interference, build tolerance, and wire bends are
not thereby cleared.

The kerf-right panel outlines, 66 panel/kicker screws, 12 old frame-bolt
axes, X = ±180 mm center posts, and separate kicker backers are unchanged.
The rest of the 24-duty barrel assembly is not revised here. This is
**not** a complete joint or construction verdict: actual washer dimensions
and bearing, delivered full-thread reach, barrel thread geometry and
strength, wood bearing/splitting/net section, bolt group load sharing,
backer attachment, full load cases, assembly access, and final shop
dimensions remain open. No drilling, fabrication, or structural release.

Verify with
`uv run pytest -q tests/test_owner_barrel_center_viewer_revision.py`.
