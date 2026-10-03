# Upper outer finished sections

This packet measures sections through the exact saved finished STEP solids for
the upper outer cleat connections. Its fixed scope is the five solids
`top_outer_left_cleat`, `top_outer_right_cleat`, `base_rail_top`,
`base_side_left`, and `base_side_right`; the eight top outer bolt axes named
in the producer; their sixteen host/cleat receiver memberships; and the eight
before/after host bracket planes already recorded in the upper outer
host-action packet. It does not read or redesign the other candidate axes or
other joints.

For each receiver membership, the section station comes from the global
centroid of its uniquely matched bore-like cylindrical face patch in the
finished surface register. The producer retains that point, its grain station,
the source axis datum and its station, and the station difference. The source
host application-plane point from `target_fastener_axes.lateral_plane_xyz_mm`
is retained in a separate record with its host grain station and its own
difference from the saved bore-centroid station. These source application
points are not substituted for the saved cylinder centroids.

Host frames use the exact source model grain, `u`, `v`, and member start in the
static upper outer host-action inventory. Cleat frames use the pinned proposed
stock `g/q/r` frame and its proposed origin from the finished surface register.
Those origins are analytical datums, not measured delivered-stock datums. The
producer checks that each axis-to-feature membership resolves to exactly one
saved cylinder patch, that the patch centroid lies on the source axis line,
and that frame, axis, feature, STEP, candidate, and revision identities agree.
It refuses missing or duplicate memberships, unsupported or ambiguous feature
matches, malformed frames, and missing or changed pinned sources.

Planes are grouped only within the same saved solid and grain frame, using a
declared `1e-6 mm` grain-station tolerance. The deterministic representative
plane and station spread are recorded. Each grouped plane retains every source
axis and feature identity; the per-membership station and source point records
remain separate. If two bore patches share one plane, the kernel reports their
section components and wires on that plane. Plane deduplication does not
assume one bore or one connected wood region per cut. The existing host
bracket planes keep their before/after identity and source terminal-boundary
marker, including one-sided planes at a host end.

Metadata-only preflight verified 97 unique pinned input paths and grouped the
24 requested plane records into 20 section planes. Four groups are coincident
within the declared tolerance: the left and right `base_rail_top` planes each
retain both rail bolt identities, and each cleat side plane retains both
`side_1`/`side_2` bore-feature identities. The two mapped cylinder patches on
each cleat side plane remain distinct source features. Their section component
and wire topology is a kernel result and is not inferred from this metadata
grouping.

The kernel imports each of the five pinned solids once and calls
`section_properties(shape, origin, grain, u, v, tolerance_mm=1e-5)` once per
unique section plane. It records total area, centroid, area covariance
integrals, component count, disconnected-component status, per-component
properties, wire counts, and runtime. These are geometric properties of the
saved BRep. They establish no stress, resistance, capacity, common-strain
response, integrated FE traction, connection acceptance, physical inspection,
or cutting/fabrication authority.

The source-pin closure records path, SHA-256, and byte size for each direct
report, its producer and test, every selected STEP, the section producer and
test, the section kernel and test, and recursively pinned upstream sources.
`sections.json` and `source-pins.json` are ignored local evidence files.

After the source records and kernel are ready, the owner can create the local
section evidence with:

```sh
.venv/bin/python docs/wood-joints-mvp/hypotheses/upper-outer-finished-sections-2026-10-01/produce.py --write
```

Exact replay without writes uses `--verify`. Metadata-only source validation
and plane counts use `--plan-only`; it does not import STEP geometry or call the
section kernel. No native structural solve is part of this packet.
