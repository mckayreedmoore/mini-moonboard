# WJ24 backer mechanics input extraction — attempt 01

This archive records the parent-run extraction from the exact composed WJ24
geometry on 2026-09-24. The run reproduced the archived composition exactly,
left its source inputs unchanged, ran no native solve, and did not release the
candidate. See [execution.json](execution.json), the bounded
[geometry input manifest](geometry.json), and the captured
[producer/test snapshots](source/). File sizes and SHA-256 readback checks are
listed in [archive-manifest.json](archive-manifest.json).

The extractor found two actual opposed finished-face pairs. The backer top
faces point along global +Z, the `base_header` underside faces point along
global −Z, and the measured backer-to-header normal is +Z at Z = 238.9 mm. It
bound four through-bolt axes to both finished receiver bores and four fixed
Hillman center-kicker axes to their composed backer cutters. Each modeled
Hillman occupancy cylinder intersects raw backer stock over 45.24375 mm and
has zero overlap with its finished receiver. The inventory diameter is a
historical CAD occupancy value, not a measured screw diameter. These are
geometry measurements only.

The manifest preserves full family/trial/axis bolt identities and stable
signed-wrench owner datums. Fresh case actions remain null. It assigns no
active contact area, pressure, load sharing, stiffness, thread/stack property,
or resistance. The complete backer/header and downstream center-frame load
paths remain unaccepted and require fresh signed actions plus applicable joint
mechanics.
