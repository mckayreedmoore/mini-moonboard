# Bottom-center contact and provisional hold envelope

This parent-run supplement binds the frozen bottom-center local geometry and
WJ18 composition. It preserves the original failed full-contact-material gate.
The retained CAD session executed `parent_probe.py.snapshot` in 1.186331 seconds;
its required objects are `g18`, `bottom_center_geometry`, `bottom_center`, and
`top_center`. Source hashes were checked before and after execution. The script
is a retained-session probe, not a standalone CLI.

The left rail interface loses exactly 167.835055 mm² to the existing E1–E2
service passage, `service/6/bore_base_rail_bottom_left_049`. Its 19.05 mm radius
and center 11.25 mm outside the cleat edge give that circular-cap area
analytically. The corresponding missing volume in the 0.05 mm diagnostic slab
is 8.391753 mm³; per-cutter attribution leaves no unexplained missing volume.
This is the actual 38.1 mm construction passage, not the older provisional
25.4 mm wiring reference.

Intersections of actual opposed planar faces in both finished members give:

| Interface | Finite common area (mm²) |
|---|---:|
| Left cleat / bottom rail | 10,385.137652 |
| Left cleat / center principal | 10,552.972707 |
| Right cleat / bottom rail | 10,552.972707 |
| Right cleat / center principal | 10,552.972707 |

Each intersection has one common face. The greatest nominal paired-face
distance is 5.86e-14 mm. This explains the material shortfall; it does not
establish contact pressure, bearing resistance, or complete-joint acceptance.
Any mechanical contact model must retain the passage and its reduced footprint.

The existing G1 provisional rear projection is 11.1125 mm in diameter and
50.8 mm long. Its overlap with the right cleat is 745.512902 mm³, beginning
10 mm behind the panel rear and continuing to the proxy end. For this diameter,
unchanged geometry would require a rear projection shorter than 10 mm by the
stated tolerances. That is a geometric bound, not a selected hold-bolt length:
actual hold geometry, thread engagement and installation remain unverified.
Do not shrink the proxy or approve a shorter bolt from this result alone.

No structural solve ran. All capacity, access, fabrication and climbing release
gates remain open. The other recorded timber, wire and tool conflicts remain.
