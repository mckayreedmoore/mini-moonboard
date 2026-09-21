# PB02 combined washer-seat and ligament trial

The [integrated script](../../scripts/simple_center_pb02_integrated_trial.py)
checks the active `ligament_priority` ten-bore assembly. It combines the 61.6 mm
right side cleat (Y −175.7 to −114.1, Z 277 to 460), upright axis
Y −144.5/Z 356, header-side cleat top Z 344, and post_cleat_2 Z 176.
The `cleat_link` is Z328.5. The `post_high` axis is Z202.0, and the two
vertical axes are X/Y 208.35/−130.5 and 236/−117.5. The post/header block
remains the `shorter_8in_trial` shape. Link Z 390 is checked as a rejected
comparison in the same script. The earlier `working_reference` remains a named
historical alternative in the shared trial specification.

**The Z328.5 combination passes the full nominal CAD collision check.** All
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

The candidate-local `CenterTrialSpec` and one ten-bore geometry builder are the
active source for this check, the placement table, stack sensitivity, connected
kinematics, and V4 viewer. Each consumer exposes the same variant identifier and
SHA-256 source fingerprint; regression tests also compare all ten axes/end
planes, receiver identities, wood grips, and the post/header block bounds.

The `post_high/post_cleat_2` finite shared-member centerline gap is 26.0 mm,
leaving **18.7 mm nominal cylindrical surface ligament** after the modeled
7.3 mm bore diameter. The `upright/cleat_link` centerline gap is 27.5 mm,
leaving **20.2 mm nominal surface ligament**. All 18 shared-member bore pairs
have positive finite surface gaps; the overall minimum is 7.2 mm at another
pair. These are nominal CAD gaps, not strength or as-drilled guarantees.

| Link Z | Upright/link nominal ligament | Front socket/rail hit | Full nominal CAD |
| ---: | ---: | ---: | --- |
| 328.5 | 20.2 mm | none | clear |
| 390 | 26.7 mm | 471.14874 mm³ | rejected |

For Z 390 the front socket envelope intersects `base_rail_bottom_right`.
Its rear insertion still clears, but the positive socket collision makes
the full assembly CAD check fail. Moving this link therefore improves the
local ligament while introducing a separate fit failure.

The active conditional placement subset has one negative project-reserve row.
The side Y
4D+5 reserve is 0 mm, the link's lower side-Z 7D+5 reserve is +2.05 mm, and the post pair
4D+5 pitch reserve is +0.6 mm. Each vertical header-bolt pair reserve is
+0.1536 mm. The `post_high` top loaded-end distance is 36.9 mm: 14.675 mm
above the conditional 3.5D minimum, but 7.55 mm below 7D and 12.55 mm below
the separate 7D+5 project comparator. The conditional reduced end-distance
factor is `CΔ = 36.9 / 44.45 = 0.83015`. The Z202 coordinate leaves the
18.7 mm nominal crossed-bore ligament while retaining the existing block and
ordinary-length trial hardware.
Inclined-principal and orthogonal-neighbor classifications remain open.
These conditional markers use a 6.35 mm placement diameter and one 5 mm
project allowance; the modeled CAD bore is Ø7.3 mm.

This is a viable **nominal CAD geometry trial** only. It is no strength,
installation, fabrication, or drilling release. Run
`.venv/bin/python -m scripts.simple_center_pb02_integrated_trial` and
`.venv/bin/python -m pytest -q tests/test_simple_center_pb02_integrated_trial.py`.
The 3D viewer's V4 development overlay now draws this active pose's two
revised side cleats and ten bore axes over the unchanged kerf-right baseline.
That partial overlay is not a complete replacement assembly or cut guide.
