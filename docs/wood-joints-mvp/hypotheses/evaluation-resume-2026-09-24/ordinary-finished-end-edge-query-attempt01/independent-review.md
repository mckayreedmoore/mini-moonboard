# Independent review: ordinary-joint finished end and edge query

Status: review complete; query findings are supported within the stated
geometry-only scope. The producer, result, and frozen inputs were not changed.
I inspected the producer and re-parsed its JSON and hash bindings with
lightweight Python; I did not run CadQuery/OCC, a CAD rebuild, a mesh, Gmsh, or
a native solver.

## Frozen artifacts and provenance

The reviewed query source is [query.py](query.py), SHA-256
`9998d38c46331c464bac4c2261e8ae16577cd44077f0104a19fb4194c792e8c2`. The
[query result](query.json) is SHA-256
`d0d9222923f81d5f42ecdc7bea22d57b013be6fd65f5bdf00cb9cba96f42dffe`; its
[execution record](execution.json), SHA-256
`82926711ea3dad51222f0f34584946362e3523972107b9d25b86ad478f7e4f30`, records
exit code 0 and 2.3708 seconds. The producer hash and result hash agree with
that record. This review is bound to the final
[summary](README.md), SHA-256
`2d9f293e7d2374459a845bdf6c0acb986c18bb4a6bbcc0fa4da4421f788754ee`.

The [frozen inventory](../ordinary-patch-inputs-attempt01/inventory.json),
SHA-256 `70b396e636175abcad7467dc145029d7126c1ea7dff1d053a61f8c5321e1c1d3`,
is covered by its [artifact manifest](../ordinary-patch-inputs-attempt01/sha256.json),
SHA-256 `eec82992ff292e36389dec148b2d168d9c3679b069bd1633eeec1d7a8a908c7f`.
All 28 manifest entries (the inventory and 27 STEP assets) recomputed to their
pinned hashes. The three queried wood STEP files also match the producer's
output pins:

| Queried body | STEP SHA-256 |
| --- | --- |
| `bottom_center_right_cleat` | `757aa41d8cd1c3cb6058a58a5a376b6d0737c76d8803e17e1ec9fc898f0fc60b` |
| `base_rail_bottom_right` | `bc1c963715273d418b29f84371676b583e5f4f4d5b36162b855588cc375a7076` |
| `base_principal_center_right` | `079b349ab932f536d741d1336d81deededa013f5f2e0dcc698b62447c923e250` |

I also recomputed all 68 `geometry_binding.source_inputs_sha256` pins in the
inventory; all matched. Its current source inventory pin
`07af4c3eb642cf3887595fe4415eb65404cdcf74d66c5c7bb182847ef21c2d78`, geometry
snapshot pin `0b92357af648604ee8ce42d2f8906e0a4e5498e9e4b835a07938b81dc151d187`,
and grip-screen attempt02 pin
`9f84a15ed05ca9832f594c4a0b2c8d1322b90e74e462aa7c725b031bad69643a` matched
their corresponding files. The source/helper and artifact pins therefore tie
this result to the described current revision and exact queried bodies; they
do not make the geometry inventory a delivered-hardware inspection.

## Geometry and query checks

The result has exactly 96 rows: four current bolt IDs, two receiver bodies per
bolt, three stations per receiver interval, and four signed directions per
station (`g−`, `g+`, `e−`, `e+`). Each station is at the pinned projected
receiver interval's `lo + 0.01 mm`, midpoint, or `hi − 0.01 mm`. The axis
origin is the inventory's live head-underface/head-washer datum; each ray
origin equals that datum plus the head-to-nut unit axis times the receiver
station. Across all rows, the station arithmetic differs by at most
`2.84e−14 mm` and the rounded ray origins by less than `5e−10 mm`. This verifies
that the head datum was shifted into each receiver's actual axial station,
rather than testing each host from one world-space AABB location.

The producer queries both finite solid intervals and trimmed-face
intersections. Its pinned helper,
[`connection_geometry.py`](../../../../../mini_moonboard/connection_geometry.py),
SHA-256 `f729bc64e7ea7fb9df9308411df07e02f98fc309efcf26038809a9e7bd4bc4a4`,
uses strict solid-interior classification along the finite ray and merges
only gaps at or below `1e-7 mm`. The producer intersects actual trimmed faces
and matches boundaries at `2e-4 mm`; it queries beyond the projected shape
bounding extent. Every ray has at least one nonempty material interval and
exactly one terminal-face candidate. Across all 332 material-interval
endpoints, each has exactly one matching finite-face hit: 236 `CYLINDER`
boundaries and 96 terminal `PLANE` boundaries. There are no unmatched
endpoints or normal-evaluation errors. Every ray's final material exit is the
one finite terminal plane reported by the summary.

The starting `[0, 3.75] mm` gap is the model's nominal 7.5 mm bolt receiver
bore, not an exterior edge. The other stored void intervals remain separate
from the exterior endpoint. All 140 endpoints of non-initial void intervals
match finite cylindrical faces. The independently counted 236 cylindrical
material boundaries include these bore/cut boundaries; none is classified as
the outside end/edge plane. The reported internal intervals can affect
net-section and complete-joint response, so their exclusion from the end/edge
distances does not imply they are structurally irrelevant.

For each bolt/member/direction, the reported terminal face and distance recur
across the three sampled axial stations; the largest within-group distance
range is `2.8e-8 mm`. This supports the summary's repeated-distance statement
for the sampled stations only. Three stations do not establish the continuous
minimum over receiver thickness or tolerance extremes. The angled
base-principal `g−` foot cut is correctly identified as a geometric profile
boundary, and the summary does not count it as a square-cut NDS end distance.

## Conditional NDS wording

I checked the summary's numeric values against the pinned official AWC
Chapter 12 PDF, SHA-256
`5fc837523ff10acc097a162718700a9b4ba64e627d2b0023439146d42fe4ee2a`, linked
from the [source correction record](../../../bolt-dimension-source-correction.md).
The review copy downloaded from the official [AWC Chapter 12 PDF](https://awc.org/wp-content/uploads/2026/08/AWC_NDS2024_withCommentary_20250328_WebsiteChapter-12-%E2%80%93-Dowel-type-fasteners.pdf)
matched that pin. The [AWC 2024 NDS page](https://awc.org/resources/2024-nds/)
identifies the applicable edition; the [March 2026 errata/addenda](https://awc.org/wp-content/uploads/2026/03/2024-NDS-Errata-and-Addenda-03.23.26.pdf)
changes shear/member-check references and commentary but not the cited
Table 12.5.1A/C distance values.

At nominal `D = 6.35 mm`, `7D = 44.45 mm`, `3.5D = 22.225 mm`, `4D = 25.40
mm`, `2D = 12.70 mm`, and `1.5D = 9.525 mm`. The shortest square-cut
grain-direction distance is `43.350 mm`; the local parallel-grain-tension
ratio `43.350/44.450 = 0.9753` is arithmetically correct. The README now
distinguishes the 2024 Commentary's angle-to-grain interpolation for tension
from §12.5.1.2(b)'s loading-at-an-angle-to-fastener-axis shear-area case. It
also keeps `0.9753` as a preliminary per-axis screen: the connection factor
depends on the smallest relevant fastener/shear-plane case. The `2D` and `4D`
table values are presented as the `CΔ=0.5` floor and `CΔ=1.0` full value for
both parallel compression and perpendicular-to-grain end-distance cases.

The end/edge interpretation remains explicitly conditional on actual timber,
bolt, signed member actions, and complete connection grouping. The report
claims neither an adopted `CΔ` nor capacity or acceptance. Its cross-grain
edge result is a geometric comparison only; loaded-edge direction still
depends on the force sign. No continuous-extrema, splitting, net-section,
member-shear, or full-joint conclusion follows from this query.

No blocker remains in the bounded query or its final summary. The initial
draft's generic “oblique action” sentence was corrected to distinguish the
two NDS angle cases, and the angled foot-cut distance was separated from
square-cut end distances before this review was frozen.
