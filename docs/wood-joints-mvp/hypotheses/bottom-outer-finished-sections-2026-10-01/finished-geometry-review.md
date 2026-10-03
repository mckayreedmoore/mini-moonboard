# Bottom-outer finished section geometry review

## Result

The eight registered receiver memberships reduce to six distinct grain-normal
planes. Exact planar intersections of the three saved finished STEP solids
reproduce the expected net areas and split into 2, 3, or 2 material regions
depending on which modeled bore cuts the section. The cleat’s four
perpendicular bore pairs have a minimum modeled wall of 9.0 mm (within about
2×10⁻⁸ mm across the four pairs).

This is a geometry-only result for candidate
`compact-floor-flush-wood-joints-development`, revision
`led-clearance-2x6-runner-seated-blocks-v1`. The disconnected regions are
separate BREP section components; their geometry does not establish common
strain, compatible deformation, force sharing, integrated traction, strength,
or acceptance.

## Source and method

I read the pinned current-finished-feature-register axis and surface records,
the same three finished STEP solids, and the A1/A12/K12 frozen model geometry
records. All three frozen model records give identical grain frames and member
start/end points for these members. The eight axis memberships are the four
`bottom_outer/clip_horizontal_bottom_left_1/{rail,side}_{1,2}` axes, each
matched to its registered finite cylindrical bore patch in the named
receiver. Their radii are 3.75 mm.

For each membership, I took the midpoint of the registered finite cylinder
patch on the source bolt axis, projected it onto the unchanged model grain
frame, and made a plane through that point normal to the model grain axis.
Memberships at the same physical plane were deduplicated at 1×10⁻⁶ mm: the two
rail memberships in the base rail differ by 2.3×10⁻¹³ mm in station, and the
two cleat side memberships differ by 1.02×10⁻⁸ mm. I imported the pinned STEP
solids read-only and called the existing
[`section_geometry.py`](../upper-outer-finished-sections-2026-10-01/section_geometry.py)
`section_properties()` function. It uses exact OCC planar common geometry and
reports connected planar face components. No geometry was regenerated or
modified.

The frame used by the frozen model has a small serialization difference from
the exact proposed stock frame in the surface/material map: the grain-axis
vector difference is 0 for the rail, 3.17×10⁻¹⁰ for the side, and
3.14×10⁻¹⁰ for the cleat (Euclidean norm; unit vectors). I retained the model
frame and its source-bore midpoint when placing each plane; I did not rotate
the plane to the STEP stock frame. The section helper’s 1×10⁻⁵ mm plane
tolerance accepts the resulting intersections. This is a frame-rounding
detail, not a change to a station or an added geometry adjustment.

## Six exact sections

Areas below are mm². Strip widths are measured across the stated section and
each region spans the full perpendicular stock dimension. Values are
independently checked against rectangle-minus-modeled-bore arithmetic.

| Member | Source grain station and membership | Net area | Disconnected section regions |
| --- | --- | ---: | --- |
| `bottom_outer_left_cleat` | g=43.3500000144 mm; `rail_1` | 7,236.46 | 2 strips, widths 39.7 and 41.7 mm across r; each spans q=88.9 mm. Areas 3,529.33 and 3,707.13. |
| `bottom_outer_left_cleat` | g=59.8499999956 mm; `side_1` and `side_2` | 6,569.71 | 3 strips, widths 24.25, 25.50, and 24.15 mm across q; each spans r=88.9 mm. Areas 2,155.825, 2,266.95, and 2,146.935. |
| `bottom_outer_left_cleat` | g=76.3500000146 mm; `rail_2` | 7,236.46 | 2 strips, widths 39.7 and 41.7 mm across r; each spans q=88.9 mm. Areas 3,529.33 and 3,707.13. |
| `base_rail_bottom_left` | g=45.4499999999998 mm; `rail_1` and `rail_2` | 4,751.07 | 3 strips, widths 49.6, 25.5, and 49.6 mm across r; each spans q=38.1 mm. Areas 1,889.76, 971.55, and 1,889.76. |
| `base_side_left` | g=284.367606047143 mm; `side_1` | 11,752.58 | 2 strips, each 66.1 mm across q and spanning r=88.9 mm. Each area is 5,876.29. |
| `base_side_left` | g=317.367606047420 mm; `side_2` | 11,752.58 | 2 strips, each 66.1 mm across q and spanning r=88.9 mm. Each area is 5,876.29. |

The arithmetic checks are respectively:

- Cleat rail planes: `88.9×88.9 − 7.5×88.9 = 7,236.46`.
- Cleat side plane: `88.9×88.9 − 2×(7.5×88.9) = 6,569.71`.
- Rail plane: `38.1×139.7 − 2×(38.1×7.5) = 4,751.07`.
- Side planes: `139.7×88.9 − 7.5×88.9 = 11,752.58`.

These values describe only the modeled 7.5 mm bore voids at the stated
planes. They do not add a bolt clearance, actual drill tolerance, wood damage,
or hardware bearing footprint.

## Cleat bore-pair wall

I independently computed closest points between the finite cylinder axes
recorded for each cleat rail/side pair, checked that both closest-point
parameters fall inside the finite cylinder intervals, and subtracted the two
3.75 mm radii from each axis separation.

| Rail bore face | Side bore face | Centerline separation | Modeled wall |
| --- | --- | ---: | ---: |
| `facet009` | `facet006` | 16.4999999813 mm | 8.9999999813 mm |
| `facet009` | `facet007` | 16.4999999915 mm | 8.9999999915 mm |
| `facet010` | `facet006` | 16.5000000190 mm | 9.0000000190 mm |
| `facet010` | `facet007` | 16.5000000088 mm | 9.0000000088 mm |

All closest-point parameters are interior to the registered roughly 0.1–89.0
mm finite cylinder spans. Thus the 9.0 mm minimum is not a ray-slice estimate.
It is the minimum separation between these modeled cylindrical cut surfaces
in the saved cleat solid.

## Pins and limits

| Input | SHA-256 |
| --- | --- |
| `docs/wood-joints-mvp/hypotheses/current-finished-feature-register-2026-10-01/axis-features.json` | `bebb4274cdecfb6ad0b0f26850d85a16570c245ea9f7d478c0b05c12b4513e19` |
| `docs/wood-joints-mvp/hypotheses/current-finished-feature-register-2026-10-01/surfaces.json` | `33fff67eee4bc4e96ccef5703f6eebd0d4e004541c6114a4b1da4a5332b2f6eb` |
| `docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-full-frame-member-solids-attempt01/bundle/members/base_rail_bottom_left.step` | `724d46fa7902a949b79b0fd6132c5e57c580be80aad7d059c29e04494ff79923` |
| `docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-full-frame-member-solids-attempt01/bundle/members/base_side_left.step` | `237c3fa6aa0b52c39124580810d048e38919b99b9a1fb5db5a2423e7eda62fdf` |
| `docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-full-frame-member-solids-attempt01/bundle/members/bottom_outer_left_cleat.step` | `28d1b5fee748c38e30e3d2618c8377cfe374c7ccd0b520736c25841720824438` |
| `docs/wood-joints-mvp/hypotheses/upper-outer-finished-sections-2026-10-01/section_geometry.py` | `8672daac3cef4aa55641a3e1bf6cee636d779be48145858282ffb0ed4d76f8d3` |
| `docs/wood-joints-mvp/hypotheses/upper-frame-joint-review-2026-09-30/freeze.json` | `d4ba1c78eb358d25e32819201e9c59e05d425a06d9e4e5cca3dc09d7139ffd73` |
| `docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/current-springa-selected-floor-a1-rear-attempt02/model.json` | `72d043e1a70702d8d464c21a039e897036e17c95e368ec776063584dac74f5fd` |
| `docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/current-springa-selected-floor-a12-rear-attempt03/model.json` | `8a90452d8afa1f1722b3253b18d5aeec72c432033a22d5d0828082022cc1cda8` |
| `docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/current-k12-rear-spr489-direct-native-attempt01/model.json` | `8f1d9bce9b62b18b3694f81816ef5c4c7cbe5e94b4c459a640fce7a98db68dbd` |
| `docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-frame-timber-material-frame-map-attempt01/current-frame-timber-material-frame-map.json` | `f867b4926ed23c9f356005c134778e138c8b1230547f0b69be7c3f9bc2a42409` |
| `docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-block-material-frame-map-attempt02/material-frame-map.json` | `8705b8f100a2d3355c236fc19e6798bb7ad4862ba2d51826cf63a88db1285480` |

The proposed stock and material frames are analytical coordinate references,
not observations of delivered lumber or its grain. The source STEP cuts are
not evidence of drilled or inspected holes. A net area or disconnected-region
map cannot establish force distribution among regions. These sections do not
cover any additional contact-patch boundary cuts that may be selected for
separate source-action comparison, and they establish no capacity, strength
pass/fail, member acceptance, or joint acceptance.
