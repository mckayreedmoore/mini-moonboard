# PB-02 right header-to-principal: one cleat reserve revision

**Nominal geometry accepted for this single trial; no fabrication or drilling release.**
This follows the [first rectangular side-cleat probe](simple-center-header-principal-cleat-probe.md)
at `clip_split_base_center_right` in the inherited right-only post-move/link-edge pose.
It changes only the new header-to-principal cleat and its two illustrative bolt axes.
The 66 panel/kicker screw axes, their receivers, and inner kicker support remain fixed.

## Rectangular solid-stock pose

Rip/crosscut one ordinary solid nominal 4×6 blank with at least 145 mm of clear length.
Use an 88.9 × 139.7 mm nominal cross section to obtain a 70.95 mm X width and
103 mm Z height; the finished Y length is 145 mm. Grain runs along **Y**.
Set the cleat at X=−20…50.95, Y=−190…−45, Z=277…380 mm. It bears on the
header top over the shared Y=−175.7…−45 footprint and against the right
principal's left X face. The cleat overhangs the header's rear by 14.3 mm;
the header extends 9 mm farther forward than the cleat.
This is a full-section rectangular piece, with no lap, pocket, custom steel,
panel alteration, or new structural wood-thread fixing.

| Through-bolt | Nominal occupied bore axis (mm) | Intended wood |
| --- | --- | --- |
| Vertical, 1/4 in | X=15.475, Y=−145.3, Z=238.9…380 | Header and new cleat |
| Crosswise, 1/4 in | Y=−95, Z=330, X=−20…89.05 | New cleat and right principal |

The vertical bolt crosses the cleat grain and exits a flat cleat top. The
crosswise bolt also crosses cleat grain and exits the principal's exposed
right face. The 7.30-mm occupied bores, 10-mm-radius washer seats, and
20-mm-radius × 20-mm straight tool envelopes are CAD screens, not bit,
washer, socket, or bolt-length specifications.

The CAD screen finds 100% of each new bore in its two intended wood members,
no new solid overlap, no unintended wood or existing-bore intersection, and
no hit on any fixed screw envelope. All four washer seats have full modeled
bearing; all four straight tool envelopes clear wood and panel/kicker solids.
The inherited pose retains 48 panel and 18 kicker axes, all four center-kicker
screw receiver fractions at 1.0, and both inner kicker edges supported.

## Grain and conditional edge screen

For D=6.35 mm, the conditional reversible transverse loaded-edge marker is
4D=25.4 mm. Centerline distances are nominal, from the actual modeled wood
faces or, for the principal Z section, a thin CAD ray at the cross-bolt Y.
The table classifies the edges rather than applying 4D to grain ends.

| Member and bolt | Edge class | Opposite centerline distances (mm) | Least reserve beyond 4D |
| --- | --- | ---: | ---: |
| Cleat, vertical | X transverse sides; grain Y | 35.475 / 35.475 | 10.075 |
| Header, vertical | Y transverse sides; grain X | 30.4 / 109.3 | **5.0** |
| Cleat, crosswise | Z transverse faces; grain Y | 53 / 50 | 24.6 |
| Principal, crosswise | Z section, conservative transverse coordinate screen; inclined grain | 53 / 100.585 | 27.6 |

The cleat's Y boundaries are **grain ends**, not transverse edges: the
vertical bolt is 44.7 / 100.3 mm from them, and the crosswise bolt is
95 / 50 mm from them. The vertical bolt's rear cleat end distance is only
0.25 mm beyond the conditional softwood tension-end 7D=44.45 mm marker.
The crosswise bolt is 87.7 mm forward of the principal's rear Y boundary;
its inclined grain and sloped end require a separate directional end check.
The header's X grain ends are remote from this local joint. For the vertical
bolt, the cleat's Z faces are entry/exit faces; for the crosswise bolt, the
cleat's X faces are entry/exit faces, so neither pair is counted as a
transverse loaded edge. The principal's Z distances are an axis-aligned
conservative screen, not a final inclined-grain NDS classification.

The header underside tool circle ends at Y=−125.3; the backer begins at
Y=−124.9, leaving only **0.4 mm nominal gap**. The 5-mm 4D reserve is exactly
at the header rear edge. Any stock error, cut error, drill wander, tool-size
increase, or washer change can consume these tiny clearances. The prior
20-mm-radius underside tool requirement bounds the vertical center at
Y≤−144.9; 4D+5 mm at the header rear bounds it at Y≥−145.3. Thus the
entire nominal Y window is only 0.4 mm. This pose is a geometry finding,
not a practical tolerance or assembly qualification.

Signed new loads, applicable loaded-edge and end classifications, bolt
mechanism and moment transfer with one bolt at each interface, wood bearing,
splitting, washer bearing, delivered shank/length, and installation sequence
remain unproved. Historical clip forces are not new demand. Reproduce with
`.venv/bin/python scripts/simple_center_principal_cleat_reserve_probe.py`
and `.venv/bin/python -m pytest -q
tests/test_simple_center_principal_cleat_reserve_probe.py`.
