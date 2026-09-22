# Owner-review corner-block viewer — full inventory, geometry REVISE

The [interactive viewer][scene]
shows one kerf-right full-frame layout study. It is **not** a build, drill,
hardware-selection, or structural release. The source-bound
[scene exporter](../../scripts/export_owner_corner_scene.py) includes all
24 proposed replacement blocks, both original-width center posts moved to
X = ±180 mm, two separate kicker-screw backers, and 92 diagnostic new bolt
paths. It hides the original 24 angle and 144 SDS visuals plus the two old
center-post poses. All 66 panel/kicker screw axes and twelve original frame
bolt arrangements remain visible. The backers' frame attachments are not
designed or credited.

The current scene deliberately exposes unresolved geometry. Red marks a
source family with a known local `REVISE` finding or an integrated
block/stack clash; amber is a layout trial, not a strength pass. The
[compact rail study](simple-pb09-owner-layout-screen.md) reports remaining
LED, T-nut, wire, and tool intersections. The
[bottom-center studies](owner-layout-bottom-center-revision.md) retain a
front-face 77 mm block pose with E1/G1 installed nut/tool conflicts; the
rear trial is not a selected substitute. The outer-base and outer-header
families have six symmetric integrated clashes: each outer-base header
bolt's shaft, head, and near washer intersect the neighboring outer-header
block. The scene reports those intersections rather than hiding them.

The integrated cross-family screen currently checks block–block and
block–generic-stack intersections only. It is **not** a complete screen of
all bores, tools, moved posts, backers, delivered hold bolts, actual wire
bends, panel-screw heads, or retained frame-bolt heads/stacks. The shown
new bolt axes are diagnostic bore envelopes, not purchased bolt lengths or
drilling dimensions. The PB09 wire channel is a modeled physical cut, but
its owner approval, fabrication feasibility, and net-section/joint
resistance remain open. The next layout revision must close the reported
clashes and all protected-volume gates before this can be selected for
detailed mechanics or translated into a drilling plan.

[scene]: https://mckayreedmoore.github.io/mini-moonboard/?model=owner-corner-layout&view=rear
