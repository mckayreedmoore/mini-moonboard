# Compact 4×6 development dimensional package

**Current result: the three-bolt leg joint has a calculated lateral shortfall
(ratio 3.185 at A12). Its drilling is not released.** See the
[compact study](compact-thick-study.md) for the two assembled cases and the
bounded layout screen.

This package describes `compact-thick-development`: single 4×6 outer rims and
rear legs, three bolts at each leg joint, flush outer rims, and a single 2×6
header with four single 2×6 posts. It is **development documentation, not a
released construction package**. Changed member, joint and bearing checks
must use this geometry; earlier pivot results do not qualify its three-bolt
connections. Follow the [current design basis](current-design-basis.md) for
assessment assumptions and status.

The main-face datum remains 277 mm above the floor: 150 mm exposed above an
assumed 127 mm pad allowance. The frame bears on the floor, not the pad. The
accepted panel layout, 66 panel/kicker screws and 142 modeled T-nuts remain.
The 139.7 mm-deep header and posts retain 7 mm of inclined-member rear
overhang at the trimmed ends. This is intentional partial bearing, not a
claim that the header covers the entire original inclined-member footprint.

Generate after exporting the frozen candidate:

```sh
uv run python -m mini_moonboard.compact_thick_exports
uv run python scripts/compact_construction_schedule.py
```

The generator rejects a stale source manifest or altered exported inventory.
Its own manifest binds the model sources, inventory and generator to the
resulting dimensional files. Historical packages remain separate.

| File under `docs/compact-construction/` | Meaning |
| --- | --- |
| `stock.csv` | One row per timber or panel blank; dimensions preserve the model's blank-axis convention. |
| `connection-axes.csv` | Installed world-coordinate fastener axes, member ownership and modeled hardware envelopes. |
| `leg-bolt-member-datums.csv` | Bolt centers relative to an actual corner of each member's minimum-X side face, with positive along-grain and cross-grain directions. |
| `panel-attachment-axes.csv` | Panel screw coordinates from each panel's left and lower datum. |
| `panel-hole-axes.csv` | Accepted hold and LED grid centers on each independent panel. |
| `timber-passages.json` | Current enclosed passage geometry and member-local layout coordinates. |
| `stock-profiles.json` | Exact uncut-member vertices in world coordinates, including end profiles and trims. |
| `outer-rim-end-trim.svg` | Cropped outer-rim YZ profile showing the header rear edge and 7 mm rear projection. |
| `manifest.json` | Source and artifact hashes for this generated package. |

For the leg joint, identify the physical corner using the stock profile and
listed world-coordinate origin. Set the indicated positive grain direction
along the member and measure the signed cross-grain coordinate perpendicular
to it on the same side face. The bolt axes run normal to that face. Left and
right members have separate rows; do not infer a drilling jig by mirroring a
world-X coordinate. The corner is a real profile vertex rather than a virtual
intersection beyond a beveled end.

Blank sizes alone do not specify a finished bevel or trim. Use the profile
coordinates and end-trim diagram together. Dimensions describe nominal CAD;
they do not establish cutting tolerances, a jig, field fit, pilot-bit selection
or a released hardware purchase schedule. Screw body diameter is not a pilot
diameter. No future insert pilots are included.

Remaining release details concern the changed members, their connections,
partial bearing, hardware specification and practical fabrication dimensions.
This package does not add panel reassessment or floor-friction qualification
requirements to the owner's accepted scope.
