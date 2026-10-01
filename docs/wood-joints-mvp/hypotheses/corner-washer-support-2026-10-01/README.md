# Primary-corner outer washer-seat geometry

Checked 2026-10-01 for `compact-floor-flush-wood-joints-development`, revision
`led-clearance-2x6-runner-seated-blocks-v1`.

The six targeted bolts have twelve outer washer seats. The CAD annulus and both
dimensional extremes of the catalog Type A Wide washer fit completely on the
modeled wood boundary at all twelve seats. The checker found no neighboring
bore or outer-edge clipping in the four exact member STEP solids. Inward
support was 1.0 (within the stated kernel tolerance) and outward prism overlap
was 0.0 at probe depths 0.01, 0.05, and 0.1 mm. Each seat point matched a
coplanar planar BREP face; maximum plane offset was
`2.274e-13 mm`, with minimum absolute normal alignment 1.0. This establishes
geometry-only footprint support in those frozen solids. It does not establish
physical flatness, contact, resistance, or joint acceptance.
The annuli are coaxial with the modeled bolt at the saved nominal seat poses;
washer translation/eccentricity and seat-location tolerances are not varied.

## Annulus checks

The CAD values come from `mini_moonboard/wood_joint_frame.py`; the catalog
bounds come from K.L. Jack `25NWUS` as recorded in the
[hardware/material screen](../hardware-material-specification-2026-09-30/fasteners.md).
The two catalog cases are separate dimensional extremes at that fixed center,
not a selected or received washer. Values are converted at 25.4 mm/in.

| Scenario | OD (mm) | ID (mm) | Annulus area (mm²) | Inward fraction, all seats | Outward overlap, all seats |
| --- | ---: | ---: | ---: | ---: | ---: |
| CAD modeled | 18.6436 | 8.0000 | 222.7262 | 1.0 | 0.0 |
| Catalog minimum-area (`OD 0.727 in`, `ID 0.327 in`) | 18.4658 | 8.3058 | 213.6279 | 1.0 | 0.0 |
| Catalog maximum-envelope (`OD 0.749 in`, `ID 0.307 in`) | 19.0246 | 7.7978 | 236.5067 | 1.0 | 0.0 |

The modeled bore radius at each target receiver is 3.75 mm. Even the smallest
catalog opening radius is 3.8989 mm, so it clears that coaxial bore by
0.1489 mm radially. The Boolean probe uses the full pinned member BREP, so any
neighboring opening or external edge represented in that solid participates
in the support calculation.

## Seat ownership and grain

The checker independently maps the six head and nut seats from the first and
last receiver intervals in the model inputs, checks their seat coordinates
against the earlier seat-screen export, and checks receiver identity and grain
against the current member map. It retains the BG003 middle receiver
`base_side_left` but verifies that it has no outer axial washer seat. Grain
relations below are the source-proposed directions, not inspected lumber.

| Axes | Head washer seat | Nut washer seat |
| --- | --- | --- |
| BG001 `post_1`, `post_2` | `knee_outer_left_spine`; grain perpendicular to axis | `base_post_outer_left`; grain perpendicular to axis |
| BG003 `side_1`, `side_2` | `knee_outer_left_spine`; grain perpendicular to axis | `knee_outer_left_inner_frame_block`; grain perpendicular to axis |
| BG045 `inner_header_1` | `base_header`; grain perpendicular to axis | `knee_outer_left_inner_frame_block`; grain parallel to axis |
| BG045 `inner_header_2` | `knee_outer_left_inner_frame_block`; grain parallel to axis | `base_header`; grain perpendicular to axis |

The geometry source is the saved current-finished member-solids bundle, not a
regenerated model. The checker hash-checks the full bundle manifest and the
four target STEP files, then verifies each imported solid against its manifest
round-trip validity, face count, and volume. Their face inventories include
cylindrical cut surfaces: `knee_outer_left_spine` 4, `base_post_outer_left` 6,
`knee_outer_left_inner_frame_block` 4, and `base_header` 22. The bundle README
records that the export applies current finished-host and panel-replacement
geometry and the current candidate-block map. The support Boolean accounts for
all geometry in each saved BREP, including any neighboring bore or relief
encoded there. The bundle has no semantic per-cut inventory, so this check
does not independently prove that every planned or physical cut was exported;
it says nothing about cuts absent from the frozen solids.

## Hardware bearing-footprint evidence

`25NWUS` is a dimensional/material-description lead, not a selected washer.
Its Type A Wide bounds specify the steel annulus that would face wood if that
washer were used. This checker tests only that annular footprint on the saved
wood surfaces. It does not model washer bending, spreading, pull-through, or
local wood resistance.

The cap-screw and nut evidence describes outside envelopes, not the exact
contact patch against the washer. Lawson/FalconGrip `FA21103`, the BG045
8-inch lead, lists 7/16-inch across flats and 5/32-inch head height. The
hardware screen records that it identifies ANSI B18.2.1 dimensions; that
standard callout remains conditional catalog evidence. BG001 has B18.2.1
catalog leads, while the Ro-Brand BG003 `HC5127` page does not claim that
standard. None of those facts gives a part-specific under-head bearing-face
diameter, chamfer, flatness, or delivered contact ring.

The candidate K.L. Jack `25CNFH5Z` nut lists 7/16-inch nominal across flats
and 7/32-inch nominal thickness. The cited B18.2.2 dimensional envelope is
0.428–0.438 inch across flats, at most 0.505 inch across corners, and
0.212–0.226 inch thick. These are conditional exterior limits, not the nut's
actual bearing-face or chamfer geometry. The hardware packet also says active
thread and nut chamfer geometry are not established. No delivered bolt, nut,
or washer is verified. Therefore the footprint by which the cap head and nut
load the washer remains an open hardware input, even though the washer-to-wood
annulus fits the modeled wood face.

## Reproduction and source pins

Run from the repository root with the existing environment:

```sh
uv run --no-sync python docs/wood-joints-mvp/hypotheses/corner-washer-support-2026-10-01/check_support.py --self-test
uv run --no-sync python docs/wood-joints-mvp/hypotheses/corner-washer-support-2026-10-01/check_support.py --check
```

The self-test covers a fully supported cube, neighboring-bore and wood-edge
clipping, an embedded datum, a reversed seat role, and a protruding wood boss
that blocks the outward probe while leaving inward support full. The replay
checks 36 seat/scenario combinations and three inward plus three outward probe
depths for each. It fails closed on changed hashes, candidate/revision,
ambiguous outer receiver intervals, mismatched seat ownership/grain, invalid
or changed STEP readbacks, wrong datum face, nonfinite/out-of-range support,
and clipping.

| Pinned input | SHA-256 |
| --- | --- |
| Washer seat-screen JSON | `67dda5964a9c2a864cdb5ee0e898bae3c9e6bea212e2eeb71d5b33f765481ef0` |
| Reduced model inputs | `178ab4f9352c8b1f11525ffc6680efa5733ba74cedd609874e9a1966624740f9` |
| Current-finished member bundle manifest | `8979d678f7b45d3b75fa465e810b0910d72874c5c1c705290d1fcb2bf2b78420` |
| Local raw hardware-input JSON | `ac8c5ca36105e3eab48f58c868794fc8a42d77cd54dfa5c76fb41f0934fd2ac2` |
| Hardware/material screen | `aac25eaccfcd123f41c180c93c6449e9f2da11c306c5b78fbf125c0ea81959f6` |
| Hardware requirements JSON | `15ec799c4ad02e1f8900537fad56eef2000afec4c9474d0e6c5591017f6ed100` |
| CAD annulus constants | `77b4a8b28b02088878f1f0e0483610a7918cb85f5694f0551f50cf8888886545` |
| Existing washer support geometry helper | `e437385d4894c7bcd4bbf4ee66aa9f96a53a8d3570efc6230fb225570abbb90e` |
| `knee_outer_left_spine.step` | `081a3930dd1334e317fc0116a24d80b4b70e9cb3f36b928cda403f66194bb5c0` |
| `base_post_outer_left.step` | `cdf9bb35e7ff2fda58bfdd604f69dedcba88b6b34149f874c03335abe90a1dce` |
| `knee_outer_left_inner_frame_block.step` | `9c7957e22686dff467f533f013172743c9bc8e7a9783331490b8e7c93d92e568` |
| `base_header.step` | `41ba159020ed41463ff1c886716cdbf69123e23481be704391a247eee1382082` |

The report records CadQuery/OCP versions and reprints hashes for every used
input, including the four member STEP solids. The local raw hardware JSON and
the already-present STEP bundle are read-only inputs; this packet does not
write replacement data. The current complete corner register was read for
scope context only; its signed demand values are not inputs to this
geometry-only calculation.

Reproduction requires the local frozen JSON and STEP evidence listed above.
The source-only Git checkout publishes this producer and summary, while raw
numerical and geometry evidence remains local under the owner's policy. A
missing local input stops the checker; the published summary is not a
replacement for those authenticated inputs.

No native solver was run, and no candidate geometry or authority was changed.
The report keeps `joint_accepted=false` and
`six_case_envelope_established=false`. The next actionable dependency is a
bound cap-head/nut bearing-face and chamfer scenario, together with washer
geometry and the coupled action/contact assumptions. Conditional analysis
can use explicitly declared, supported scenarios before product selection or
receiving; part-specific drawings or observed fit support stronger product or
actual-piece claims. Physical wood-face condition remains an observation
needed before any claim about contact or fit in built material.
