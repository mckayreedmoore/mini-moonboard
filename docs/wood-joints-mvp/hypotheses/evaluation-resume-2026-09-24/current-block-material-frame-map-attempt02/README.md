# Current connector-block material frame map — attempt02

## Result

This attempt preserves attempt01 and adds the pinned source-inventory file to
the G7 row's per-member frame lineage, where its WJ04 frame values are read.
No frame values or interpretations changed.

This attempt binds conditional source-frame `X/T/N` axes, a proposed grain
direction, and both right-handed `R/T` assignments to the 24 connector-block
IDs in full-frame input manifest attempt02. It contains 48 transverse
orientation cases. The attempt02 record digest is written in
`material-frame-map.json` after regeneration.

The mapped candidate is
`compact-floor-flush-wood-joints-development`, revision
`led-clearance-2x6-runner-seated-blocks-v1`, reviewed source checkpoint
`b1e8707d`. The selected authority remains
`compact-floor-flush-development`.

## Source frame method

- The 15 common blocks start from the pinned source-inventory frame
  `base_rail_bottom_right.local_axes`. Their per-body axes are transformed by
  the saved exact-solid proper-rotation transforms in the current seven-pattern
  block-design report. That report permits translation and proper rotation,
  excludes reflection, and checks congruence by exact solid intersection.
- The two center-post blocks use the global-axis `makeBox` construction in the
  WJ05 source builder. The two current center-principal blocks, two inner-frame
  blocks, and two runner-seated spines use their pinned current geometry
  builders' global-axis `makeBox` constructions.
- The shortened upper G7 block uses the pinned WJ04 source frame and its
  source-bound upper-G7 builder. Its conditional grain direction is `+N`.
- Each frame record is checked as orthonormal and right-handed. The material
  helper `material_orientation_cases()` generates two cases per block. When
  grain follows source `N`, case A uses `R=X, T_material=+T`; case B uses
  `R=T, T_material=-X`.

The producer reads source files and saved reports only. It does not import CAD,
replay or change geometry, use viewer meshes, create solver inputs, or run a
solver. The JSON lists exact manifest block IDs and preserves each available
owner finished-shape hash without treating a missing hash as a geometry
binding.

## Interpretation and limits

The `+N` and `+Z` grain directions are conditional stock-layout scenarios, not
observations of the delivered boards. Growth-ring orientation is unknown, so
both `R/T` cases remain open; separate physical boards may require different
assignments even within one pattern. The inner-frame `+Z` proposal is the least
directly documented scenario in the current material brief.

This completes a block-only orientation map. It does not complete the
full-frame per-member material map: the 20 frame timber members, six plywood
panels, 92 candidate bolts and their hardware, and 12 retained frame-bolt
stacks remain outside scope. The proposed elastic values are not measured,
grade-specific accepted properties or resistance values. No material
acceptance, capacity, demand, mechanics result, candidate acceptance, or
release is claimed. The attempt02 full-frame manifest remains
`inputs_ready=false`.

## Reproduction

Run read-only source-bound verification from the repository root:

```sh
python3 docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-block-material-frame-map-attempt02/produce.py --verify
```

The producer checks every pinned source hash, authority and revision identity,
all 24 block IDs, all two-case orientations, the canonical record digest, and
the unchanged conditional/release limits. A changed input requires a new
attempt; `--write` refuses to overwrite this attempt's JSON.
