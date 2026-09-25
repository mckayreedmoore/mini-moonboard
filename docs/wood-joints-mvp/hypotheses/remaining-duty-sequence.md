# Remaining twelve-duty development sequence

Status: parent planning checkpoint, 2026-09-24. The
[twelve-duty static composition](wj12-integrated-static/README.md) leaves
twelve source duties with 72 legacy SDS axes. No replacement is accepted.
The [source inventory](../source-inventory.json) remains the authority for
each duty's six beam/upright axes, host faces, and member identities.

| Group | Source duties | Host pairs |
|---|---|---|
| Top outer | `clip_single_top_left_1`, `clip_single_top_right_2` | `base_rail_top` to matching `base_side_left/right` |
| Top center | `clip_split_top_center_left/right` | `base_rail_top` to matching `base_principal_center_left/right` |
| Bottom outer | `clip_horizontal_bottom_left_1`, `clip_horizontal_bottom_right_2` | Matching `base_rail_bottom_left/right` to side member |
| Bottom center | `clip_horizontal_bottom_left_2`, `clip_horizontal_bottom_right_1` | Matching bottom rail to center principal |
| Left service outer | `clip_horizontal_lower_left_1`, `clip_horizontal_upper_left_1` | Matching left service rail to `base_side_left` |
| Left service inner | `clip_horizontal_lower_left_2`, `clip_horizontal_upper_left_2` | Matching left service rail to `base_principal_center_left` |

Each table row covers two duties and twelve old axes. The part-count review
projects twelve additional cleats and 48 candidate bolt stations; those are
planning counts, not a materialized or accepted layout.

After the bounded cut-section and mechanics review, the proposed next slice
is the left service family. It tests whether the existing right inner/outer
layouts can be reused with explicit source asymmetry. The top-outer pair is
a separate possible starting slice if this reuse is unsuitable. Neither
choice authorizes fabrication or claims reuse without checking it.

The left inner cleat proposal mirrors to X = −177.95 through −89.05 mm.
The left outer cleat must undo the right kerf translation before mirroring:
its proposed X interval is −1130.3 through −1041.4 mm, with rail-bolt X at
−1084.85 mm and the side-bolt start at X = −1041.4 mm directed toward −X.
Directly mirroring the current right outer cleat leaves a 3.175 mm gap from
the actual left-side inner face at X = −1130.3 mm. These coordinates define
an investigation, not an installation instruction.

The upper-left cleat must be screened against actual E7/F7 and A7 service
geometry. Do not inherit the right G7 crosscut merely by mirroring. Left
source members retain their native datums; reconstruction must use their
own cuts. Any slice must merge the existing purchased-length receiver cuts,
retain all 66 axes, and recheck all twelve frame-bolt arrangements against
the composed scene. Full stacks, tools, disassembly, transport, stock/cuts,
and load transfer must be recorded for the completed layout.

The older `wood_joint_wj06_residual_probe.py` exclusion set is not a current
remaining-duty selector. It includes nineteen duties and overlaps three
right-rail duties already in WJ12. Its provisional corridors also lack full
hardware and access evidence. Scope a future producer to explicit duty IDs;
do not publish its unmodified output as a twelve-duty completion report.
