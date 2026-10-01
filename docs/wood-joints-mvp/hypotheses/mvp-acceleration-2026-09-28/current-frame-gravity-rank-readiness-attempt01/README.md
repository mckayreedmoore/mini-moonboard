# Current-frame gravity rigid-body rank readiness, attempt 01

This packet screens source-bound rigid-body kinematic branches for the current
wood-joints frame. It does not assemble the 1,903-solid physical stiffness
operator, select an actual unilateral contact state, or authorize a native
frame solve. Its result is `PASS_SOURCE_BOUND_RIGID_BODY_BRANCH_SCREEN_INITIAL_GRAVITY_GAUGE_OPEN`:
the rank screen is reproducible, while the initial gravity gauge remains open.

The pinned scope is candidate `compact-floor-flush-wood-joints-development`,
geometry revision `led-clearance-2x6-runner-seated-blocks-v1`, case
`a12-rear`. No geometry or native model was changed. The audit binds 15 source
and context files; their exact SHA256 values are in `audit.json`.

## Method and limits

The model contains 50 physical bodies, represented by six rigid coordinates
per body. Translation coordinates are in mm; rotational coordinates are
`1000 mm * radians`; each body datum is the arithmetic mean of its source mesh
nodes. The script expands permanent interpolation and projection equations,
substitutes SPC-fixed numerical nodes as zero, and projects bilateral spring
extensions and unilateral source extensions into this 300-coordinate space.
It removes the 200 conditional floor-stick equations for the all-open branch.
For the separate captured-stick screens it applies the pinned 200-by-800
source floor matrix to the same physical rigid-motion map. All 800 matrix
masters map to unique physical-body DOFs, including the 200 pivots of the
conditional floor equations being projected.

The fixed-node inventory has 1,292 SPRINGA numerical grounds, 200 fixed scalar
captured-reference nodes, and 100 fixed nonphysical floor endpoints; all 4,776
translation DOFs are SPCs and no physical body node is fixed. The 200
captured-reference nodes occur only in the conditional floor-stick rows. The
100 floor endpoints are different: they are not element nodes, but each is a
fixed master in three permanent projection equations. The audit traces all
100 floor-normal rows through those equations: each fixed-side projection
eliminates to zero, each body-side projection expands to physical-body DOFs,
and the 100 rows map one-to-one to the 100 fixed endpoints. They therefore
remain the numerical ground path of the unilateral floor-normal springs when
those rows are included. These nodes model an assumed numerical floor
reaction; they are not physical anchors or verification of an actual floor.

The SPRINGA endpoint-axis projection agrees with its source scalar projection
to a maximum absolute coefficient residual of `1.31e-13`. The maximum initial
span residual is `2.42e-13 mm`, and the positive-branch slope residual is
`5.82e-11 N/mm`. The tables have zero force at `q=0`, zero slope on the
negative-`q` side, and positive `k` slope on the positive-`q` side. Thus no
single two-sided tangent is defined at `q=0`; neither the all-open nor
all-active row set alone proves the gravity-start branch.

Before the frame rows are ranked, two small row-builder oracles pass: a free
single body has rank 0/nullity 6; two bodies tied by three translations at
one point and two translations at a second point on the x-axis have rank
5/nullity 7, retaining relative spin about x.

Rows are unit-normalized, then columns are unit-normalized, and dense SVD rank
is reported at relative cutoffs `1e-8`, `1e-10`, `1e-12`, and `1e-14`. Spring
stiffness magnitudes are not used in this kinematic screen. The cutoff
sensitivity is material: the all-open bilateral screen has nullity 80 at
`1e-10`, 74 at `1e-12`, and 67 at `1e-14`; the all-normal-active envelope has
nullity 3 through `1e-12` but 0 at `1e-14`, despite verified rigid-mode row
residuals near `3e-14`. These values are numerical body-rigid mechanism
screens, not full elastic tangent ranks.

## Branch results

| Declared row set | Rows | Rank at `1e-10` | Nullity at `1e-10` | Other cutoffs (`1e-8 / 1e-12 / 1e-14`) |
|---|---:|---:|---:|---|
| 348 bilateral rows; all unilateral and all conditional floor-stick rows open | 348 | 220 | 80 | rank 220 / 226 / 233; nullity 80 / 74 / 67 |
| Bilateral rows plus all 1,292 unilateral rows in an optimistic active-normal envelope; floor-stick rows open | 1,640 | 297 | 3 | rank 297 / 297 / 300; nullity 3 / 3 / 0 |
| Bilateral rows plus 200 conditional floor-stick rows; unilateral rows open | 548 | 235 | 65 | rank 235 / 241 / 250; nullity 65 / 59 / 50 |
| All 1,292 unilateral rows active plus 200 conditional floor-stick rows | 1,840 | 300 | 0 | rank 300 at each cutoff |

At the `1e-10` cutoff, the all-open branch's 80 null directions include six
verified common rigid modes and 74 additional relative-body mechanisms. The
optimistic all-normal-active envelope retains verified global `Tx`, `Ty`, and
`Rz` modes; these span its three-dimensional screen nullspace at `1e-10`.
The conditional floor-stick rows in the all-open counterfactual remove common
`Tx`, `Ty`, and `Rz` modes and 12 additional directions. Common `Tz`, `Rx`,
and `Ry` remain, and the screen still has 65 null directions. Adding all
unilateral rows to those floor-stick rows yields zero kinematic nullity at the
tested cutoffs, but only under the declared all-bearing/captured-reference
condition and the optimistic assumption that all 1,292 unilateral rows are
on their positive tangent. These conditional and optimistic envelopes are
not compatible contact-state evidence.

## Readiness decision

The all-open bilateral branch has additional mechanisms, while unilateral
rows are nonsmooth at zero extension. The current packet does not assemble an
orientation-aware reduced tangent for the orthotropic C3D20 solids, combine
it with a directional unilateral active set, or establish the actual
initial-gravity nullspace. The initial gravity gauge is therefore not ready.
The next readiness gate must establish the actual directional branch and
remove only its demonstrated reaction-free common null modes. Do not assume
six gauge modes after floor normals become active: the all-open screen has
six common modes, the optimistic all-normal-active screen has three, and an
actual active subset may differ. The conditional all-bearing floor-stick
result does not apply to the zero-load start.

## Reproduction

From the repository root, verify the stored result against its pinned inputs
with:

```sh
OPENBLAS_NUM_THREADS=1 uv run --no-sync python3 \
  docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/current-frame-gravity-rank-readiness-attempt01/audit.py \
  --verify
```

Regenerate only this packet's `audit.json` with the same command and `--write`.
No native solver is invoked.
