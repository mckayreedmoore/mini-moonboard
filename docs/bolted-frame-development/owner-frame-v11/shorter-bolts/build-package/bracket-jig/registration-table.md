# Reuse the marking jig on the 12 horizontal beam flanges

This table is for the corrected print-local V2 jig only. It maps each checked
beam-flange pose to the wood end and width edge that the jig's two stops must
touch. The wood coordinates are the finished receiver's local profile
coordinates from the family check; `V min` or `V max` identifies the physical
width edge, including members whose local V coordinates run from −139.7 to 0.

Use the listed **loose rail before its perpendicular timber is attached**.
The family check found the jig's end stop obstructed by the adjoining timber in
all 12 assembled positions. Do not force the jig into an assembled corner.
Seat the steel beam flange under the mask, put the end stop against the listed
finished end, and put the side stop against the listed finished width edge.
Use the listed fitting orientation, then mark through only the two actual steel
factory holes. The square windows are visibility openings, not drill sizes.

| Joint | Fitting | Timber receiver | End stop against | Side stop against | Mark at local x = 19.05 / 69.85 mm | Pose rotation |
|---|---|---|---|---|---|---|
| horizontal_bottom_left_1 | eoere_clip_horizontal_bottom_left_1 | base_rail_bottom_left | L = 0 | V min = 0 | eoere_bolt_002 / eoere_bolt_029 | A |
| horizontal_bottom_left_2 | eoere_clip_horizontal_bottom_left_2 | base_rail_bottom_left | L max = 1041.25 | V max = 139.7 | eoere_bolt_040 / eoere_bolt_019 | B |
| horizontal_bottom_right_1 | eoere_clip_horizontal_bottom_right_1 | base_rail_bottom_right | L = 0 | V min = 0 | eoere_bolt_025 / eoere_bolt_059 | A |
| horizontal_bottom_right_2 | eoere_clip_horizontal_bottom_right_2 | base_rail_bottom_right | L max = 1077.275 | V max = 139.7 | eoere_bolt_062 / eoere_bolt_014 | B |
| horizontal_lower_left_1 | eoere_clip_horizontal_lower_left_1 | base_rail_service_lower_left | L = 0 | V max = 139.7 | eoere_bolt_030 / eoere_bolt_003 | C |
| horizontal_lower_left_2 | eoere_clip_horizontal_lower_left_2 | base_rail_service_lower_left | L max = 1041.25 | V min = 0 | eoere_bolt_020 / eoere_bolt_041 | D |
| horizontal_lower_right_1 | eoere_clip_horizontal_lower_right_1 | base_rail_service_lower_right | L = 0 | V max = 139.7 | eoere_bolt_060 / eoere_bolt_026 | C |
| horizontal_lower_right_2 | eoere_clip_horizontal_lower_right_2 | base_rail_service_lower_right | L max = 1077.275 | V min = 0 | eoere_bolt_063 / eoere_bolt_015 | D |
| horizontal_upper_left_1 | eoere_clip_horizontal_upper_left_1 | base_rail_service_upper_left | L = 0 | V min = −139.7 | eoere_bolt_031 / eoere_bolt_004 | A |
| horizontal_upper_left_2 | eoere_clip_horizontal_upper_left_2 | base_rail_service_upper_left | L max = 1041.25 | V max = 0 | eoere_bolt_042 / eoere_bolt_021 | B |
| horizontal_upper_right_1 | eoere_clip_horizontal_upper_right_1 | base_rail_service_upper_right | L = 0 | V min = −139.7 | eoere_bolt_061 / eoere_bolt_027 | A |
| horizontal_upper_right_2 | eoere_clip_horizontal_upper_right_2 | base_rail_service_upper_right | L max = 1077.275 | V max = 0 | eoere_bolt_064 / eoere_bolt_016 | B |

The local jig axes are transformed by each row's pose in the pinned family
proof. Rotation labels below describe the transform from print-local axes to
world axes; each has determinant +1. Keep the STL unmirrored. Opposite-end rows
use the 180° in-plane reversal shown by A/B or C/D.

| Rotation | Print-local x axis in world | Print-local y axis in world | Print-local z axis in world |
|---|---|---|---|
| A | (0, −0.766044443, 0.642787610) | (−1, 0, 0) | (0, −0.642787610, −0.766044443) |
| B | (0, 0.766044443, −0.642787610) | (1, 0, 0) | (0, −0.642787610, −0.766044443) |
| C | (0, 0.766044443, −0.642787610) | (−1, 0, 0) | (0, 0.642787610, 0.766044443) |
| D | (0, −0.766044443, 0.642787610) | (1, 0, 0) | (0, 0.642787610, 0.766044443) |

For placement, use the exact pose origin in the source proof if setting up a
model. On the physical rail, the checked stops identify the listed adjacent
finished end and width faces. A failed fit, rocking, blocked window, or mismatch
with actual bracket holes means stop; the checks are nominal CAD evidence, not
a physical fit observation. This table does not extend the jig to post flanges,
other holes, drilling, or fabrication release.

## Bound source files

- Corrected print-local STL: `horizontal_rail_marking_jig.stl`, SHA-256 `4dc4758f37ad6fe2b286c796955587daa8ff7b6efcfa17d4fd23b061d82304c9`.
- Corrected print-local manifest: `print-manifest.json`, SHA-256 `05d8d824f42058d08ec83f536a33f3ad4bfca81265412152de885e6dd804cd37`.
- Twelve-pose family-use proof: `horizontal-rail-family-use-check-v2.json`, SHA-256 `c871105a8818c3a3632b36603dd06cda86e7a3fd71405ac9de4100ed9e4effe8`.
