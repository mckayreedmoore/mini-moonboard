# PB02 combined washer-seat and ligament trial

The [integrated script](../../scripts/simple_center_pb02_integrated_trial.py)
checks one current ten-bore assembly. Its primary trial combines the 61.6 mm
right side cleat (Y −175.7 to −114.1, Z 277 to 460), upright axis
Y −144.5/Z 356, header-side cleat top Z 344, and post_cleat_2 Z 176.
The cleat_link stays at Z 370. The post/header block remains the
`shorter_8in_trial` shape; its other axes stay fixed. Z 390 is checked as a
rejected comparison in the same script.

**The Z 370 combination passes the full nominal CAD collision check.** All
ten modeled Ø7.3 mm bores are fully received in their intended wood and all
20 modeled washer seats have full bearing. The new side cleat has no
positive-volume wood or fixed-screw overlap. The full checker finds no
wood, bore, hardware, washer-face, or socket-body overlap in its reported
collision categories. All 66 panel/kicker screw axes match the fixed source
by name, bounds, and modeled volume; both inner kicker edges stay supported.
The header-side cleat has 9,273.165 mm² nominal contact with the header;
its bolt bore is fully received across the two members.

Every bolt has at least one clear modeled straight insertion approach. The
link clears from the rear. Its front insertion envelope intersects the
right lower rail by 2,480.80758 mm³, so that approach is unavailable.
The checks do not prove a complete assembly sequence or tool access.

The two targeted finite shared-member centerline gaps are each 14 mm,
leaving **6.7 mm nominal cylindrical surface ligament** after the modeled
7.3 mm bore diameter: `post_high/post_cleat_2` in the shifted post and
`upright/cleat_link` in the side cleat. All 18 shared-member bore pairs have
positive finite surface gaps; the minimum is 6.7 mm. These are nominal CAD
gaps, not strength or as-drilled guarantees.

| Link Z | Upright/link nominal ligament | Front socket/rail hit | Full nominal CAD |
| ---: | ---: | ---: | --- |
| 370 | 6.7 mm | none | clear |
| 390 | 26.7 mm | 471.14874 mm³ | rejected |

For Z 390 the front socket envelope intersects `base_rail_bottom_right`.
Its rear insertion still clears, but the positive socket collision makes
the full assembly CAD check fail. Moving this link therefore improves the
local ligament while introducing a separate fit failure.

Conditional placement comparisons still fail for the Z 370 trial. The side
Y 4D+5 reserve is 0 mm, the side Z 7D+5 reserve is +29.55 mm, and the post
pair 4D+5 pitch reserve is +0.6 mm. The placement table reports −0.55 mm
at the `post_high` top grain end and −2.9 mm at the vertical header-bolt
pair in each of its two shared members. Its minimum reserve is −2.9 mm.
Inclined-principal and orthogonal-neighbor classifications remain open.
These conditional markers use a 6.35 mm placement diameter and one 5 mm
project allowance; the modeled CAD bore is Ø7.3 mm.

This is a viable **nominal CAD geometry trial** only. It is no strength,
installation, fabrication, or drilling release. Run
`.venv/bin/python -m scripts.simple_center_pb02_integrated_trial` and
`.venv/bin/python -m pytest -q tests/test_simple_center_pb02_integrated_trial.py`.
The 3D viewer's V4 development overlay now draws this working pose's two
revised side cleats and ten bore axes over the unchanged kerf-right baseline.
That partial overlay is not a complete replacement assembly or cut guide.
