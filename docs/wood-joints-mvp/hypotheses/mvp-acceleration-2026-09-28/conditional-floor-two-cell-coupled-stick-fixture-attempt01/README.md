# Two-cell normal and tangential contact fixture — attempt01

## Engineering result and stop condition

This known-answer fixture tests the bounded rule needed to combine the reviewed
two-cell normal active-set fixture with conditional no-slip-while-bearing:
solve unilateral normal states, enforce zero tangential displacement only at
positively bearing cells, release tangential force at open cells, and reset a
cell's tangential reference when it re-engages after open motion. The useful
result is a verified local state-selection method for this two-cell rigid-body
case. Stop this method check if any stage lacks exactly one admissible normal
state, an open cell carries tangential force, the re-engagement reference is
wrong, or force/moment/stick residual exceeds tolerance.

## Result

The standard-library verifier passes all eight prescribed stages. Each stage
has exactly one admissible normal state. The sequence exercises both-bearing,
left-only, right-only, complete release, and re-engagement after open motion.
The two-cell shear-and-yaw stage obtains tangent reactions `[0, -20] N` while
both cells remain at their episode reference. Maximum normal equilibrium
residual is `2.274e-13`; maximum tangent equilibrium and stick-slip residuals
are zero at the recorded precision. The deterministic record is in
[observed.json](observed.json), and the frozen input is in
[fixture.json](fixture.json).

Reproduce from the repository root with:

    python3 docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/conditional-floor-two-cell-coupled-stick-fixture-attempt01/verify_fixture.py --verify

## Method and limits

The normal model has vertical translation and pitch about +Y, with contacts at
`x = ±100 mm`. The verifier enumerates all four normal masks, solves each
candidate branch, and accepts a state only when bearing gaps/reactions and open
gaps/reactions satisfy the recorded signs and equilibrium. This extends the
[normal rotation fixture](../conditional-floor-two-cell-rotation-fixture-attempt02/README.md)
with the tangent behavior first checked in the
[single-cell coupled fixture](../conditional-floor-stick-coupled-load-fixture-attempt01/README.md).

The tangent model has global +Y translation and yaw about +Z. Two fixture-only
translation springs form the recorded diagonal carrier stiffness. While a
normal reaction is positive, a KKT solve enforces ideal zero slip relative to
that contact's current episode reference and returns its signed reaction. An
open contact has zero tangent force. A contact newly entering bearing records
the displacement reached during the preceding open stage as its new reference.
This deliberately tests state logic and equilibrium accounting, not a physical
contact law with a resistance limit.

The ideal-stick rule has no force cap and assigns no floor stiffness, friction,
anchor, or resistance. The springs are numerical devices. Normal and tangent
coordinates are separate in this small rigid-body fixture; this does not prove
multidirectional contact uniqueness, structural coupling, actual whole-frame
support reactions, solver convergence, or a real floor's no-slip behavior.
The **floor gate remains BLOCKED** and no full-frame demand transfers from this
fixture. No native solve or mesh was run.

## Source pins

| Source | SHA-256 |
|---|---|
| [AGENTS.md](../../../../../AGENTS.md) | `672203b929d51d340d39d770e71dd43b019794ea33172bc9f4f7be469fc20536` |
| [Option A/B method selection](../option-ab-method-selection-2026-09-29.md) | `d73dc9b2583c88b64fab4a8e61b1910dfbdb2881cc6dde629b30911a5425c76a` |
| [Two-cell normal fixture input](../conditional-floor-two-cell-rotation-fixture-attempt02/fixture.json) | `80b5e26335d22a2d9f11f5a7b1c9ffe8bbcf2774088ae50c2c5191b2088128ad` |
| [Single-cell normal/tangent fixture input](../conditional-floor-stick-coupled-load-fixture-attempt01/fixture.json) | `da7961d07502df2fbb0d17de26db0490fc0c868f152dc108b9eae36b01b41a27` |

The local input, verifier, result and this README are integrity-pinned in
[SHA256SUMS](SHA256SUMS).
