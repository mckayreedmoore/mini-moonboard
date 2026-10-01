# Normal foot-reaction equilibrium bounds — attempt01

## Engineering result and stop condition

This bounded statics calculation asks which vertical compression-only
resultants are compatible with whole-assembly force and roll/pitch moment
equilibrium over the eight pinned floor-face polygons. It unlocks an outer
equilibrium envelope for each modeled floor face across all 54 existing
load/accessory scenarios, without assigning frame stiffness or local contact
pressure. Stop if any source pin changes, any case has no nonnegative reaction
distribution, or an extreme witness fails force or CoP equilibrium tolerance.

## Results

The standard-library verifier enumerates the basic feasible solutions of the
nonnegative reaction polytope for all 54 case/scenario wrenches. Every CoP has
at least one admissible reaction distribution across the eight modeled faces.
For **each individual face in every scenario**, the statics-only minimum is
zero. Whole-assembly equilibrium therefore does not require any one named
face to carry vertical reaction. Across all cases and faces, the greatest
statically admissible single-face resultant is **3,605.070 N**, at
`base_floor_left` for `a12-left` with `split_12_5_kg_hold_at_kicker_1`.
The total vertical resultant in these scenarios is 4,670.093 N.

The min/max for each face are separate optimizations. Do not combine their
endpoints into one simultaneous reaction vector. The complete source-bound
record and extreme-distribution witnesses are in
[normal-foot-reaction-bounds.json](normal-foot-reaction-bounds.json).

Reproduce from the repository root with:

    python3 docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/normal-foot-reaction-equilibrium-bounds-attempt01/compute_bounds.py --verify

## Method and limits

Each face may carry a nonnegative vertical resultant at any point within its
pinned polygon. A face resultant at an interior point is represented by
nonnegative weights on that face's vertices. The global equations are
`sum(R_i) = N`, `sum(R_i*x_i) = N*x_CoP`, and
`sum(R_i*y_i) = N*y_CoP`. The script enumerates basic feasible solutions of
this small linear equilibrium polytope and takes each face's independent
minimum and maximum. A hand-checkable point-support square fixture verifies
the extrema code.

This is an outer set of whole-assembly statically admissible vertical
reactions conditional on all eight modeled faces being coplanar and available
for compression contact. It does not prove the current frame's stiffness,
closed internal load paths, or which distribution the structure realizes.
The witnesses are not native-solver results. They do not establish local
pressure distribution or peak wood-bearing stress; the sum divided by face
area would be only an average. Horizontal/yaw reaction distributions, floor
resistance, actual floor flatness or engagement, individual member actions,
joint forces, and capacities remain unresolved. The floor gate remains
**BLOCKED**, `mechanical_acceptance=false`, and `native_solve_run=false`.
Missing evidence is not a physical failure finding.

## Source pins

| Source | SHA-256 |
|---|---|
| [AGENTS.md](../../../../../AGENTS.md) | `672203b929d51d340d39d770e71dd43b019794ea33172bc9f4f7be469fc20536` |
| [Pinned global support geometry](../global-equilibrium.json) | `4fe8652f4296827ed8bf06b376cee22194027d24eb64a73a17afa87679ffb381` |
| [Accessory-aware 54-wrench result](../accessory-support-resultant-attempt01/accessory-support-resultant.json) | `adc1507a5540c54a701f95b7291b0e765819b502c39e33df164b3f805af5e76d` |
| [Current full-frame manifest](../../evaluation-resume-2026-09-24/current-full-frame-input-manifest-attempt04/current-full-frame-input-manifest.json) | `9e682e28c3d4c3c0594863f82c6b74d19dee2700f3856d34e1a26f69082e4f11` |

The local inputs, verifier, result and this README are integrity-pinned in
[SHA256SUMS](SHA256SUMS).
