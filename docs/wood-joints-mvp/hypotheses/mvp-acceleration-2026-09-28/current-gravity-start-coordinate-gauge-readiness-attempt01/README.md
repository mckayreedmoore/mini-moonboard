# Gravity-start coordinate-gauge evidence — attempt 01

## Result

For candidate `compact-floor-flush-wood-joints-development`, geometry
`led-clearance-2x6-runner-seated-blocks-v1`, case `a12-rear`, the reviewed
source operators support a **reaction-free common planar coordinate gauge
candidate**, conditional on the eventual directional tangent retaining those
null modes. They do not establish a complete gravity-start gauge or select a
contact state. No frame solve, native run, factorization, mask selection, or
operator rebuild was performed for this note.

At zero load the source configuration is `a=0`, `f=0`, `q=0`: it is a valid
zero-prestress, zero-reaction initial coordinate state. The 100 floor-normal
spans are initially touching within `2.4158453e-13 mm`, and all normals point
global `+Z`. At this exact boundary, open (`N=0`, `q_n<=0`) and bearing
(`N>=0`, `q_n=0`) are both compatible at `N=q_n=0`; with zero tangential
force, the conditional stick rows also meet their initial zero reference.
Therefore the zero-load state has no unique open/closed floor mask. The
right-hand gravity direction `beta -> 0+` must select it from the preserved
`a12-rear` gravity columns; this note makes no such selection.

## Source-bound common modes

The already reviewed raw map is `D:1840x300`, built from 348 bilateral rows,
1,292 unilateral rows (including all 100 floor normals), and 200 conditional
floor-tangent rows. The 300 coordinates are 50 body rigid-coordinate blocks;
translations are mm and rotations are `1000 mm*radians`. With all 200
conditional floor-tangent rows released, the recorded source row screen
evaluates the common global planar modes:

| Mode | Row-normalized `D` action, bilateral + all unilateral rows | Source gravity virtual work, maximum over six cases |
|---|---:|---:|
| global `Tx` | `2.8533271e-14` | `4.6586309e-15 N·mm` |
| global `Ty` | `2.8875720e-14` | `4.0175814e-13 N·mm` |
| global `Rz` | `2.4923525e-14` | `4.0899171e-10 N·mm` |

The residuals are the saved attempt04 source review values, with rows
normalized before measuring the mode action. The envelope includes every
unilateral row, so it covers the 100 floor normals and all nonfloor
unilateral rows; it excludes only the 200 conditional floor-tangent rows.
Those rows constrain these modes when held (`D` action is about `0.12–0.14`),
but are not valid at the initial zero-load state without a captured sticking
episode. The geometry explains the ideal result: common in-plane translation
or rotation leaves internal connector extensions and vertical floor-normal
gaps unchanged when the floor tangents are released.

The source gravity virtual work is **not bitwise zero**. The largest saved
value is `4.0899171e-10 N·mm` on `Rz`; all six case-specific gravity columns
are within the existing `1e-8 N·mm` orthogonality check. This is a
source-rounding-sized result, not permission to project or edit `W`. Preserve
raw `D.T @ f = W`; a later gauge audit must retain the unmodified source
wrenches and show that the actual gauge multiplier/reaction is zero within
the existing force and moment gates. If the raw load has unsupported work on
any actual null mode, stop unresolved rather than removing that work.

The same saved kinematic rank screen reports nullity 80 for the all-open
bilateral-only row set at relative cutoff `1e-10`: six common rigid modes and
74 additional relative-body mechanisms. The optimistic all-normal,
floor-tangent-open envelope has rank 297/nullity 3 at `1e-10`; its nulls are
the verified common `Tx`, `Ty`, and `Rz`. Rank classifications change at
tighter cutoffs, and the screen is not a stiffness-weighted or actual
directional tangent rank. In particular, do not clamp the 74 relative modes as
coordinate gauge: they can represent physical mechanisms, and their gravity
work and restoration depend on the state selected at `beta -> 0+`.

If the selected directional tangent retains only common global planar nulls,
a source-defined coordinate gauge may set their displacement components to
zero relative to the reviewed geometry, using the authenticated 50-body datum
map. This is a coordinate convention, not a floor constraint. Apply it only
to modes proven null in that actual tangent, keep all raw `D`, `W`, `e`, and
`H` unchanged, then audit the gauge multipliers and unprojected equilibrium.
If the actual nullspace contains relative mechanisms, or a null mode carries
work above the original force/moment tolerances, the gravity start remains
unresolved; do not add anchors or project `D`/`W`.

The six load pairs remain intact: `a12-rear (gravity, climber)=(0,1)`,
`a12-forward=(2,3)`, `a12-left=(4,5)`, `k12-right=(6,7)`,
`k12-rear=(8,9)`, `a1-rear=(10,11)`. The present question uses only the
`a12-rear` gravity source column for a future first-direction selection; this
evidence does not mix its climber column into the gravity settle.

## Replay and pinned evidence

From the repository root, run this hash-and-record replay:

```sh
.venv/bin/python docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/current-gravity-start-coordinate-gauge-readiness-attempt01/verify_gauge_evidence.py --verify
```

The replay reads saved JSON summaries and hashes only. It does not load or
multiply the large operator arrays, perform an SVD/factorization, or solve a
state. The saved common-mode and gravity-work measurements come from the
source-bound attempt04 operator review; the all-open rank result comes from
the existing rigid-body branch screen.

| Pinned input | SHA-256 |
|---|---|
| `current-springa-frame-input-adapter-attempt01/a12-rear/model.json` | `61f95ec9e670b2bd0e95d426cc14ff381283edfc4f9c87e47c2b344dd4fe50b8` |
| `current-frame-connector-compliance-attempt04/inputs.json` | `3d17f953df265035e95fdb3543e19eb0f7505d81778067f28783e4bb9b0b3208` |
| `current-frame-connector-compliance-attempt04/assessment.json` | `ae30902f9340875a771d60dab83621ab5e0d6dcadb58c06a35bdb1bc8ac9da6c` |
| `current-frame-connector-compliance-attempt04/operators.npz` | `88a2f2f384edb7be7daa0e20cc87c7b8672ed13e975f8e86afd56d8aeb385b79` |
| `current-frame-connector-compliance-attempt04/row-identities.json` | `768d2afe58b48fa482f118f73bb01b8c911d1f937a5891d5c420a0d821b45037` |
| `current-frame-connector-compliance-attempt04-operator-review-attempt01/assessment.json` | `278d4853360b7f1da2e63a781c0b0782db2eb42c86a8832a9f8a824f3f6e2570` |
| `current-frame-connector-compliance-attempt04-operator-review-attempt01/verify_review.py` | `e998750807c3e226470c725d83ee51b428f5baa87f6c544848b80f08aff47e24` |
| `current-frame-gravity-rank-readiness-attempt01/audit.json` | `a8453f861777a307a386a6398c3dd976965b7c6c6872b149f1826cfec08a5718` |
| `current-frame-gravity-rank-readiness-attempt01/audit.py` | `8034554eaee03b9884bbc9cd9f6a6da51392beac2182d38339a787dfb30c2d90` |
| `current-frame-physical-connector-projection-contract-attempt01/projection-contract.json` | `4ceca771e26e1f1d0bf8efca8e3d77dc6d94194553d95e1fd75652ecf2f3f2d3` |
| `current-floor-normal-tangent-join-contract-attempt01/join-contract.json` | `607ec82a8f830101a5bed07a9d1214aa85ac09179dafe` |
| `current-frame-pure-solid-matrix-export-preflight-attempt01/source-load-maps.json` | `9cd59d7bbafd65c740d2b0200e3dd88a6a49e6dca0bead0a38bc7826e337548c` |
| `current-gravity-settle-climber-ramp-scenario-attempt01/decomposition.json` | `39d1530ee888bb824c2bd1624072890385c19a1448f4d146567a041aff5d14dc` |
| `current-gravity-direction-initial-selector-contract-attempt01/README.md` | `162ca31e203958b972fbee1be9f923af81589b14edf42280f926123a57941ddc` |

