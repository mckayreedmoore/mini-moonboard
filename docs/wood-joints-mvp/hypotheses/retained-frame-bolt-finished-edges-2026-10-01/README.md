# Retained frame-bolt finished directional boundaries

This packet joins the authenticated current retained-bolt forces to nominal
finished geometry. It preserves the twelve retained bolt arrangements and
their 24 receiver memberships. It does not accept the joints or change the
reviewed candidate. The previous resistance packet's unresolved finished-edge
method is addressed here without changing its historical report.

`produce.py` authenticates the frozen load report and raw receipt, conditional
resistance report, current face/axis source chains, finished STEP bytes and
the 47 pending criteria. It imports only this packet's pure `method.py`.
There is no CAD import, geometry regeneration or native execution.

Each receiver has four rays, in the positive and negative modeled grain and
stock cross-grain directions. They start at the bore centerline at its
midpoint and 0.01 mm inward of each bearing end: 288 distinct queries. The
query origin is an interior geometry sample; the source physical force point
on the member interface is separately recorded. The 252 signed bolt states
yield 504 receiver states. Each receiver uses its own force, including the
opposite force on the second receiver, and its own grain frame. Native RF
rounding intervals determine whether each component's sign is resolved.

The method fills the mapped own bore and its matching planar hole loops for
centerline interpretation. Every other cut remains. Full intersection traces
distinguish the first material exit, which can meet another hole, from an
exterior polygon-face exit. A tangent, corner, unsupported signature or
unresolved origin returns an explicit NULL distance. Stock-box locators stay
separate and never replace missing finished boundaries. Plane normals in the
source register already point outward; the topology-orientation label does
not reverse them a second time.

Distances are from the fastener centerline at the named depth, in millimetres.
They do not subtract a bore radius. The source's proposed stock grain basis is
an analytical datum, not observed delivered grain. Three samples do not
establish a minimum across the bearing depth; that field remains NULL.

The [source evidence](source-evidence.json) pins the official 2024 AWC NDS
Chapter 12 PDF. Sections 12.1.2.1–12.1.2.4, printed page 81/PDF page 3, distinguish
perpendicular-to-grain edge distance, square-cut parallel-to-grain end
distance, center-to-center spacing and a fastener row aligned with load.
Oblique states retain signed component-direction geometric candidates.
Their NDS loaded-edge/end classification remains NULL, as do Cdelta, Cg,
splitting acceptance and complete-joint resistance. A sloped cut, recess,
blind cap or intervening hole is not automatically a square-cut member end.
Numeric placement table factors and historical Commentary interpolation are
not adopted by this packet.

All 288 current queries resolve, and all 1,008 signed component choices are
resolved despite source RF rounding. In 28 queries, another bore is the first
material-loss boundary before the exterior. Finished distances differ from
the stock box in 96 queries. The largest difference is 637.422661 mm for the
second receiver of `lumber_leg_bolt_left_2`, along negative grain at 0.01 mm
inside its head-side bearing end: stock distance 1854.913305 mm versus finished
distance 1217.490644 mm. This is a result at that depth, not a full-depth bound
or an NDS square-cut end classification.

For the first receiver of `rail_front_bolt_left_2`, the negative-grain ray at
mid-depth reaches another bore at 36.032759 mm and the exterior at 98.102859 mm.
Those distinct values must not collapse to a single member end distance.

The integration tests and CLIs require three previously authenticated upstream
artifacts in `/tmp`: `mini-moonboard-retained-frame-bolt-current-load-path-2026-10-01.json`,
the same prefix with `-raw-oracle.json`, and
`mini-moonboard-retained-frame-bolt-current-resistance-basis-2026-10-01.json`.
Restore those frozen stage outputs from their accepted packets before running
this packet on a clean checkout; this packet neither regenerates missing
native evidence nor substitutes a new report. The fixture reports a missing
prerequisite explicitly, and the producer authenticates each artifact's bytes.
The [pinned upstream reproduction sequence](upstream-reproduction.md) gives
the offline commands and required hashes; root replay reproduced all three.

With those frozen artifacts present, run from the repository root:

```sh
.venv/bin/python docs/wood-joints-mvp/hypotheses/retained-frame-bolt-finished-edges-2026-10-01/produce.py --output /tmp/mini-moonboard-retained-frame-bolt-finished-edges-2026-10-01.json
.venv/bin/pytest -q docs/wood-joints-mvp/hypotheses/retained-frame-bolt-finished-edges-2026-10-01/test_finished_edges.py
.venv/bin/python docs/wood-joints-mvp/hypotheses/retained-frame-bolt-finished-edges-2026-10-01/raw_oracle.py --expected-report-sha256 75db902ab8ebb64985592e8f1552333db763facb35d9be1630ec521202fe2332 --expected-oracle-sha256 1faaaa293ff51ec9b42967c6ab646911929719f1197660caf49d1deeae077961 --output /tmp/mini-moonboard-retained-frame-bolt-finished-edges-2026-10-01-raw-oracle.json
.venv/bin/python docs/wood-joints-mvp/hypotheses/retained-frame-bolt-finished-edges-2026-10-01/raw_oracle.py --expected-oracle-sha256 1faaaa293ff51ec9b42967c6ab646911929719f1197660caf49d1deeae077961 --check-receipt /tmp/mini-moonboard-retained-frame-bolt-finished-edges-2026-10-01-raw-oracle.json
```

The [geometry plan](geometry-plan.md) records the accepted metric and limits.
The [primary handoff](PRIMARY-HANDOFF.md) records the numbers, their purpose,
current validation status and request for another bounded assignment.
The [validation](validation.md), [final review disposition](review-final.md)
and [final file pins](final-pins.json) accompany the completed packet.
All 47 criteria remain pending and all release flags remain false.
