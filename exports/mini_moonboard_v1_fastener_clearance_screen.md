# V1 fastener head-clearance screen

This CAD-derived screen checks the visible nominal fastener **heads, washers,
and nuts** against all physical V1 solids. It intentionally excludes shafts:
their intersection with the fastened material is required. Surface contact is
allowed; a reported value is a material-volume overlap above 0.01 mm³.

## Result

- Total non-shank collisions: **38**.
- Panel-screw countersunk-head collisions: **0**.
- Status: **FAIL — do not treat the viewer fastener representation as an
  installable hardware stack.**

The screen confirms that the face-installed countersunk screw heads have no
material-volume clash with the panels. It also exposes the current structural
fastener problem: the generic through-bolt stack places hardware through the
knee gusset/leg/rail volume. This is a real layout and stack-up issue, not an
allowed shaft intersection. A redesigned, reviewer-approved connection must
define the bolt direction, head/washer/nut locations, actual plate stack, and
edge distances, then make this table empty.

| Fastener | Component | Intruded physical part | Overlap mm³ |
| --- | --- | --- | ---: |
| `analysis_leg_rail_bolt_left_1` | left washer | `leg_knee_gusset_left` | 1710.1 |
| `analysis_leg_rail_bolt_left_1` | head | `leg_knee_gusset_left` | 2714.3 |
| `analysis_leg_rail_bolt_left_2` | left washer | `leg_knee_gusset_left` | 1710.1 |
| `analysis_leg_rail_bolt_left_2` | right washer | `rail_cross_tie_top_left` | 13.2 |
| `analysis_leg_rail_bolt_left_2` | head | `leg_knee_gusset_left` | 2714.3 |
| `analysis_leg_rail_bolt_left_3` | left washer | `leg_knee_gusset_left` | 1710.1 |
| `analysis_leg_rail_bolt_left_3` | head | `leg_knee_gusset_left` | 2714.3 |
| `analysis_leg_rail_bolt_left_4` | left washer | `leg_knee_gusset_left` | 1423.6 |
| `analysis_leg_rail_bolt_left_4` | head | `leg_knee_gusset_left` | 2644.2 |
| `analysis_knee_bolt_left_1` | right washer | `leg_left` | 1710.1 |
| `analysis_knee_bolt_left_1` | nut | `leg_left` | 1447.6 |
| `analysis_knee_bolt_left_1` | nut | `face_rail_1_upper` | 1719.1 |
| `analysis_knee_bolt_left_2` | right washer | `leg_left` | 1710.1 |
| `analysis_knee_bolt_left_2` | nut | `leg_left` | 1447.6 |
| `analysis_knee_bolt_left_2` | nut | `face_rail_1_upper` | 1719.1 |
| `analysis_knee_bolt_left_3` | right washer | `leg_left` | 1710.1 |
| `analysis_knee_bolt_left_3` | nut | `leg_left` | 1447.6 |
| `analysis_knee_bolt_left_4` | right washer | `leg_left` | 1710.1 |
| `analysis_knee_bolt_left_4` | nut | `leg_left` | 1447.6 |
| `analysis_leg_rail_bolt_right_1` | right washer | `leg_knee_gusset_right` | 1710.1 |
| `analysis_leg_rail_bolt_right_1` | nut | `leg_knee_gusset_right` | 3166.7 |
| `analysis_leg_rail_bolt_right_2` | left washer | `rail_cross_tie_top_right` | 13.2 |
| `analysis_leg_rail_bolt_right_2` | right washer | `leg_knee_gusset_right` | 1710.1 |
| `analysis_leg_rail_bolt_right_2` | nut | `leg_knee_gusset_right` | 3166.7 |
| `analysis_leg_rail_bolt_right_3` | right washer | `leg_knee_gusset_right` | 1710.1 |
| `analysis_leg_rail_bolt_right_3` | nut | `leg_knee_gusset_right` | 3166.7 |
| `analysis_leg_rail_bolt_right_4` | right washer | `leg_knee_gusset_right` | 1423.6 |
| `analysis_leg_rail_bolt_right_4` | nut | `leg_knee_gusset_right` | 3084.9 |
| `analysis_knee_bolt_right_1` | left washer | `leg_right` | 1710.1 |
| `analysis_knee_bolt_right_1` | head | `leg_right` | 1447.6 |
| `analysis_knee_bolt_right_1` | head | `face_rail_4_upper` | 1266.7 |
| `analysis_knee_bolt_right_2` | left washer | `leg_right` | 1710.1 |
| `analysis_knee_bolt_right_2` | head | `leg_right` | 1447.6 |
| `analysis_knee_bolt_right_2` | head | `face_rail_4_upper` | 1266.7 |
| `analysis_knee_bolt_right_3` | left washer | `leg_right` | 1710.1 |
| `analysis_knee_bolt_right_3` | head | `leg_right` | 1447.6 |
| `analysis_knee_bolt_right_4` | left washer | `leg_right` | 1710.1 |
| `analysis_knee_bolt_right_4` | head | `leg_right` | 1447.6 |
