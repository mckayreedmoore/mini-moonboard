# Current floor normal/tangent join contract — attempt 01

## Result

This source-only audit joins all 100 actual floor-normal SPRINGA projections
to the exact 200 conditional tangent equations, two per cell. It preserves the
source row orientation, physical owner, support point, normal law, reference
scalar node, and matrix row position needed by a later state solver. Every
projected tangent coefficient matches its original source-matrix coefficient
exactly; all 200 reference coordinates are unique and source-matched.

The bound model is `compact-floor-flush-wood-joints-development`, case
`a12-rear`, geometry revision `led-clearance-2x6-runner-seated-blocks-v1`.
It has 50 physical bodies, 12,549 physical nodes, and 37,647 physical
translation coordinates. The projection contract has 1,840 rows but only
1,666 distinct textual row IDs, so this audit identifies equations by their
zero-based B row positions and source matrix positions rather than assuming
row IDs are unique.

| Joined class | B row positions | Count | Source identity |
|---|---:|---:|---|
| Floor normal SPRINGA | 1370–1469 | 100 | One source group/element and numerical ground per cell |
| Conditional floor tangent | 1640–1839 | 200 | Two exact source matrix rows and reference scalars per cell |

The 200-by-800 original floor matrix has audited rank 200 over 800 physical
master DOFs. Each tangent contract row was mapped back through the audit's
`(physical node, DOF)` master list and compared across all 37,647 physical
coordinates. Maximum coefficient difference is exactly `0.0`; source rows
0–199 and 200 distinct reference coordinates each appear once. All source
rows use local DOFs 2 and 3, 100 of each. The arbitrary owner-row orientation
was checked per equation; this source happens to use sign `-1` for all 200.

Each normal row has source law `N = k * max(q, 0)` with positive `q` denoting
compression and `N >= 0`. Its physical action on the owned body is
`+normal * N`, equivalently the source restoring action `-B_normal^T * N`
after the exact projected row sign is applied. The 100 source normal
directions are global `+Z`. Each cell's two tangent directions lie at the same
source support point and are perpendicular to its normal. For an exact tangent
row `B_t`, the conditional equation is `B_t * u_physical = r_episode`; its
coefficients are dimensionless, displacement/reference are mm, and the signed
multiplier is N. The first-body action for multiplier `lambda` is the recorded
row orientation sign times its tangent direction times `lambda`.

The adapter's fixed SPRINGA ground and fixed floor-projection endpoint are
separate numerical coordinates for each cell; both are nonphysical and absent
from the physical coordinate vector. The reference node's DOF 1 is a separate
abstract scalar displacement in mm, not a global-X translation. Neither the
source CLOAD correction values nor the adapter's initial fixed-reference
configuration supplies an episode reference.

## Event/reference interface

A later path solver must provide a physical displacement vector of length
37,647, the cell ID, the bracketed event condition `q_event = 0`, event
direction, and prior open/closed episode state. At capture, compute each of
the cell's two references from its exact signed source row:

```text
r_episode,j = B_tangent,j * u_physical(event)   [mm]
```

For positive normal force, retain both tangent equations and solve their
signed multipliers in simultaneous equilibrium. For normal-open motion, remove
both equations and enforce zero tangent multiplier. On re-engagement after an
open episode, capture two new references at the next bracketed event and
replace the earlier episode values. `q = 0` without event direction/history
is ambiguous. An unknown initial `q = 0` remains `AMBIGUOUS`; this packet
chooses no mask and provides no initial gravity state.

The complete 100-cell join, exact source matrix indices, row signs, source
groups/elements, reference nodes, points, directions, and numerical ground
IDs are serialized in [join-contract.json](join-contract.json). The reproducible
builder checks the pinned input hashes, all 100 owner joins, all 200 original
matrix rows, and reference bijection:

```sh
OPENBLAS_NUM_THREADS=1 .venv/bin/python \
  docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/current-floor-normal-tangent-join-contract-attempt01/prepare_join.py \
  --verify
```

## Bounded fixture evidence and provenance

The local state-method oracles remain separate from the current-frame join:

| Evidence | Result retained here | Limit |
|---|---|---|
| Two-cell normal/tangent/reset fixture | Eight stages replay under current controls; each has one normal mask, zero open-cell tangent force, and equilibrium/stick residuals within the fixture tolerance | Small rigid-body mathematics only |
| Synthetic bracketed event/reference fixture | Exact capture, release, reset, and event-refinement checks pass | Synthetic SPD matrix; no frame path/event state |
| Coupled indicator-selector fixture | Eight tiny cases exhaust all masks, including zero-boundary ambiguity, one held nonzero-reference state, an infeasible fixed-reference case, a two-mask case, and four two-cell stages | Supplied small operators/references only; no actual-frame state or 100-cell scalability |
| Staged native capture coupon | Parent's ten-scheduled-step, all-increment output assessment is hash-pinned | Native output/reference mechanics only |
| Nonzero-reference release coupon | Parent's two-step, all-increment release assessment is hash-pinned | Native release mapping only |

The selector's result record reports `NO_ADMISSIBLE_STATE` for its pinned
one-cell fixed-reference counterexample and `MULTIPLE_ADMISSIBLE_MASKS` for
the mirrored two-mask case. Its zero-force event returns both open and closed
masks as `AMBIGUOUS_ZERO_BOUNDARY_MASKS`. These are explicit bounded method
tests, not evidence that the 100-cell frame starts in any one state. The
source-bound result, selector code, and its small fixture dependencies are
hash-pinned by this packet.

The two-cell historical verifier and its original `fixture.json`,
`observed.json`, and checksum manifest are byte-preserved. Its official
full-verifier replay still fails on the original AGENTS pin
`672203b9…`; current `AGENTS.md` is `63c317ea…`. The only difference is the
master-only/shared-staging workflow paragraph introduced after the fixture;
the fixture's model, loads, and source dependencies are unchanged. The
separate [current-controls replay](current-controls-two-cell-replay.json)
imports the immutable mathematical functions, reconstructs the old observed
record under the old pin, reruns the mathematics with the current controls
hash, and confirms the math fields are identical. This is explicitly a
controls-current mathematical replay, not a pass of the historical pinned
full verifier. It does not alter native authorization, freeze ownership, or
execution gates. Reproduce it with:

```sh
OPENBLAS_NUM_THREADS=1 .venv/bin/python \
  docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/current-floor-normal-tangent-join-contract-attempt01/current_controls_two_cell_replay.py \
  --verify
```

Pinned source/output hashes are collected in [source-pins.json](source-pins.json)
and [SHA256SUMS](SHA256SUMS). The staged native coupon, nonzero-release native
coupon, and synthetic event oracle are independent evidence streams; none is
recast as a 100-cell state solution.

## Stop boundary

This join does not assemble or solve the physical frame operator, recover an
actual gravity equilibrium, decide a 100-cell contact mask, locate actual
contact events, establish path-dependent references, or assess uniqueness.
The real initial normal state and every `q = 0` event remain unresolved. The
source floor label and numerical endpoints are not proof of a real floor
anchor, no-slip behavior, resistance, or capacity. The parent still owns the
physical operator and any later state/reduction work. No native solve was
launched for this packet.
