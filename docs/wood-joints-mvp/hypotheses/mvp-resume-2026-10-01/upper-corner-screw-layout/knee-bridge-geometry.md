# Knee bridge proposal geometry: exported

[Producer](knee-bridge-geometry.py) completed the parent run through
`run(output)`: two valid single solids exported; original stock bounds preserved. Producer SHA-256:
`4df9cac42dc25ca433a7459f4b03fade64f88e691ef8dcde696f69744106c4ff`.
Use a fresh immediate child of `rawlocal/knee-bridge-geometry/`.

The producer authenticates the frozen normal proposal and receipt
(`c9360e7ca4ab167a5cbc505373b2bd1342aa6a830f72a26113da9f7c4a8ad778` /
`991f6742f6aae386552338b1fea79f02766bd0def09bfa8fabea27560ba13819`),
and the original geometry packet
(`6b6c8df94f1ccab859ee980dd1835ba19286718f44e8a36ce6b9d0014064fc85`).
It obtains the two original STEP paths and byte pins from that packet. Left
and right delivered STEP pins are respectively
`081a3930dd1334e317fc0116a24d80b4b70e9cb3f36b928cda403f66194bb5c0` and
`f70ade3760f1615cc31f687bc4cf4c334d27db3b8b41e35e615e15b92c4e1faa`.
All consumed source pins are authenticated before and after execution.

Only those two STEP files are imported. Each spine retains its four original
`u` bores and receives two full `v` cylinders at `(grain,u)=(100,0)` and
`(250,0)` mm through the 139.7-mm depth. The 7.5-mm diameter is a CAD envelope,
not a drill instruction. The pinned existing disjoint-cylinder helper supplies
analytic volumes and centroids for rectangular stock minus four/six bores.
Source and proposed solids must be valid single solids, preserve stock bounds,
and match those analytic properties and the exact two-cylinder removal. Fixed
comparison tolerances are 0.000001 mm and 0.001 mm³. Failure stops the attempt;
there is no tolerance tuning.

The ignored packet contains two `.proposal.step` and two binary
`.proposal.stl` timber exports, `manifest.json`, `receipt.json`, compact input
records, and producer/helper snapshots. The manifest records four added stock
bolt axes in global coordinates with both wood end seats; nominal 6.35-mm
shaft records cover the wood span only. STEP units are mm; STL deflection and
angular settings are 0.1 mm / 0.1 rad. Output hashes are checked again after
receipt creation. Export roundtrip validation is not claimed.

From the repository root, the parent runs:

```sh
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/upper-corner-screw-layout/knee-bridge-geometry.py --output docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/upper-corner-screw-layout/rawlocal/knee-bridge-geometry/attempt01
```

CadQuery 2.8.0 / cadquery-ocp 7.9.3.1.1 are required. The parent owns serialized
CAD execution, mass/BOM reconciliation, staging and commits. The existing
[normal transfer](knee-spine-reinforcement.md), [modified grain](knee-bridge-grain.md),
[washer](knee-bridge-washer.md) and [scene-fit](../assembly-package/knee-bridge-fit.md)
results are reused within their recorded limits. This producer does not repeat
their physics or rebuild the scene. Sources, viewer, authority and current
104-axis files are preserved. All outputs remain proposals; adoption, global
gravity feedback, complete-joint acceptance and physical release flags are
false. The parent imported only the two saved spines and cut/exported the four
new holes. No software tests, agent reviews, full-scene rebuild or native/frame
solve ran. Each removal is **12,343.513885 mm³**; maximum removal-volume error
is below 0.000000002 mm³ and maximum proposed centroid error below 0.000000001 mm.

Saved `rawlocal/knee-bridge-geometry/attempt01/manifest.json` SHA-256:
`254dd58d2f311553b32637b01b85b8bacbc0b474acfee667597333c501afe147`.
Receipt: `92ccabb307b6d9cbcd8f768b8275a7ecf4ef6ae6a55a7be2cd83742d76be9973`.
All seven source pins and nine output artifacts match. The separate
[order/mass reconciliation](../assembly-package/knee-bridge-order.md) is complete;
its results are not global gravity or geometry adoption.

| Proposal timber export | SHA-256 |
| --- | --- |
| `knee_outer_left_spine.proposal.step` | `534ec2db81bbedfddba6cdf92c8703112231e970eff9b10e6a11fd11ce134645` |
| `knee_outer_right_spine.proposal.step` | `847e644efdb36156a74dee1641e52a18cf17d301f03f59d2fa0bb68cd7d2b273` |
