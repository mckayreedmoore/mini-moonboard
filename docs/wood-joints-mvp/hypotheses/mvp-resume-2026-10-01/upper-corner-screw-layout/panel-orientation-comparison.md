# Four main panels: grain-direction response comparison

Completed October 2, 2026. The conditional strong-X response returns all six
load cases at zero and nominal frame-bolt clearance. It retains the owner's
250 lb upper limit, ×2 downward live force, signed 300 N horizontal force
and 100 mm front-face lever. Only the four main panels' directional elastic
properties change. All 66 Hillman axes, their source stiffness laws, timber,
geometry, contacts, loads and modeled mass remain unchanged.

This is a comparison with the current strong-T packet, not its adoption or a
climber rating. Actual sheet properties and placement remain unobserved.
Complete joints and physical release remain **HOLD**.

## Why this orientation was evaluated

The [material worksheet](panel-material-fidelity.md) found a conditional
layout/model mismatch. The three-sheet nominal 4×8 option places two main
widths along the factory long direction. If face grain follows that direction,
the panels are strong along X, whereas the saved frame assumes strong T along
the board slope. The [placement arithmetic](../assembly-package/panel-placement.md)
also gives four-sheet options preserving strong T. No actual sheet assignment
is inferred from either option.

The reassembly swaps the two in-plane Young's moduli in each main panel's
four source layers. It retains the fitted Group 1 AC-plywood reference family,
layer thicknesses, transverse moduli, zero Poisson proxies and physical
coordinate bases. Kicker grain remains vertical. This tests orientation
without reducing loads or choosing a softer screw law.

## Returned screw demands

[head_check.py](head_check.py) consumed **792 screw states per packet**, 1,584
in total, including both clearance scales and all six panels. Maximum saved
screw-law reconstruction error is 1.33e−8 N in the preserved packet and
4.63e−9 N in the width-grain packet.

The following are separate nominal-clearance envelopes. A panel's peak axial
and peak lateral loads need not occur on the same screw or case.

| Panel | Strong-T peak axial, N | Strong-X peak axial, N | Strong-T peak lateral, N | Strong-X peak lateral, N |
| --- | ---: | ---: | ---: | ---: |
| Upper left | 1871.251 | 1280.799 | 1244.301 | 1051.036 |
| Upper right | 1603.442 | 1174.975 | 1214.711 | 1084.361 |
| Lower left | 987.395 | 1213.615 | 487.515 | 726.757 |
| Lower right | 123.975 | 120.691 | 321.045 | 273.496 |
| Kicker left | 286.166 | 290.636 | 369.163 | 376.374 |
| Kicker right | 262.152 | 264.883 | 348.171 | 341.984 |

The upper-left nominal peak falls **31.55%**, but lower-left demand rises.
Orientation therefore changes sharing; it is not uniformly conservative.
The upper-left peak remains on unchanged `round_panel_upper_left_edge_2`,
A12-rear, into `base_rail_top`: **T=1280.799 N, simultaneous V=523.473 N**,
representative opening **0.476190 mm**. The zero-clearance envelope reaches
T=1377.323 N on that same axis, with V=388.636 N.

Axial tension loads both timber thread withdrawal and panel head
pull-through. The [head-basis worksheet](head-reference-basis.md) retains
favorable retailer-nominal head scenarios of **930.222–984.128 N** with its
explicit 1.6 connection-duration hypothesis. The new nominal demand is still
**1.30–1.38 times** those references. They are conditional ASD allowances,
not measured Hillman capacities or breaking loads. No physical failure is
inferred. The 250 lb dynamic head comparison remains unresolved, and the
140 lb envelope cannot be obtained by multiplying these peaks by 140/250.

## Elastic operator calculation

[panel_orientation.py](panel_orientation.py) uses the existing C3D20 brick
kernel, connector projections and free-body quotient condensation. It first
reassembles the old panel stiffness and compares it directly with each saved
authenticated native matrix. Relative maximum differences are:

| Body | Elements / physical DOFs | Relative matrix difference |
| --- | ---: | ---: |
| `main_lower_left` | 400 / 6567 | 4.212e−12 |
| `main_lower_right` | 324 / 5400 | 6.942e−12 |
| `main_upper_left` | 400 / 6567 | 1.074e−11 |
| `main_upper_right` | 400 / 6567 | 9.468e−12 |

Only those four bodies' compliance H and elastic live-load response e
contributions are replaced. D, W and F arrays are bit-identical; B, row
identities and connection inputs are byte-identical to the source. Updated H
has relative reciprocity error 9.454e−11 and minimum symmetric eigenvalue
−9.904e−18 mm/N, within the existing numerical gates. No native solve runs.
All 109 operator input pins and all 141 completed-frame source pins match.

## Numerical initialization and unchanged acceptance scope

The completed response uses [conic_frame.py](conic_frame.py). The original
frame equations run first. On a normal active-set cycle, a convex fixed-floor
calculation supplies a finite force guess for another original-equation solve:

```text
min_f  1/2 f' (H + diag(1/k)) f - e'f + sum_i gap_i * ||f_pair_i||
subject to D'f = W and compression/withdrawal-only forces >= 0
```

Circular norms use second-order-cone epigraphs. The pinned Clarabel 0.11.1
interface follows its [official Python documentation](https://clarabel.org/stable/python/getting_started_py/).
An `InsufficientProgress` or `AlmostSolved` seed is only a numerical guess;
it supplies no accepted physical state. Original balance, spring/contact,
floor and domain checks decide the returned result.

If the original disk projection stops, an equivalent small disk QP initializes
the same projection residual and its least-squares refinement. The unchanged
acceptance tolerance remains **1e−8 mm**. The one fallback returns a residual
of 1.110e−16 mm. It changes neither a force law nor a floor assumption.

Three analytic mechanics coupons bind the signs and mappings: a 3/4 N circular
spring at k=1000 N/mm and gap 1.15 mm returns [0.693, 0.924] mm; an unloaded
unilateral spring with negative imposed opening stays open; and the disk
problem W=[3,4], response=2I, radius=1 returns [0.6,0.8]. No software tests
or independent review loop were run.

All twelve final states satisfy the existing equilibrium, finite laws,
nonnegative contact, no-slip floor and 10 mm positive-spring domain checks.
Maximum force/moment residuals are 9.16e−12 N / 1.21e−8 N·mm; maximum finite
law error is 3.35e−7 N. Maximum positive-spring motion is 0.512078 mm.
Zero-clearance states have rank 300. Nominal states retain rank 296/297 and
bounded fixed-force seating certificates; strict stability, force/pose
uniqueness and a full dynamic motion envelope are not established.

### Preserved stopped calculations

| Attempt | Returned states | Stop |
| --- | ---: | --- |
| `panel-width-frame-250-attempt01` | 8 | A12-left nominal normal active-set cycle |
| `attempt02-conic` | 0 | First conic seed `InsufficientProgress` |
| `attempt03-conic` | 7 | A12-forward nominal conic floor-branch cycle |
| `attempt04-conic` | 10 | K12-rear nominal disk residual 2.571e−6 mm |
| `attempt05-conic` | 12 | Complete conditional response |

Earlier attempts retain their own frozen wrapper snapshots and STOP receipts.
Their terminal iterates are not accepted. These numerical stops are not
physical frame failures.

## Next decision and frozen artifacts

Evaluate the owner's proposed 20 screws per main panel with this same
strong-X material scenario. The previous 20-count calculation used strong T;
its added-row projections cannot be attached to the width-grain H matrix
without recomputing all affected panel contributions. The physical 66-screw
policy remains current until a proposal is explicitly adopted.

The [current joint register](joint-register.md) and component replays remain
bound to the earlier strong-T force source. This orientation changes bolt
forces too; for example, the lower-left outer corner's nominal peak lateral
force rises from 243.4 to 434.1 N. No old component ratio transfers to the new
response. Replays must use one coherent selected force/material packet.

Raw packets remain local and ignored. These identities bind the completed
comparison without overwriting the current packet:

| Artifact | SHA-256 |
| --- | --- |
| `panel_orientation.py` | `3268faa94ba050d82d66df1393fc4b8e4d9e4a79b87412fe0f4cfdbf72dd7e93` |
| `conic_frame.py` | `445574a04559e8faa28a3b69bfdbf1a439f6fc25940e0f02837b0927c48f0025` |
| `panel-width-operators-attempt01/operator-assessment.json` | `47e3405e15e3d97f8666ffdead694f1a83fe6f3f76608fc81882112075e98fe0` |
| `panel-width-operators-attempt01/operators.npz` | `bf7cfd24800a0c551fa136465d8d92172ec9dd9b619d86d43930ab7f17b87387` |
| `panel-width-frame-250-attempt05-conic/comparison.json` | `5a49b2076e0e32e5fbae90b1da41be6b77973da9057aee860acebaee9cef05f0` |
| `panel-width-frame-250-attempt05-conic/response.npz` | `ff54c8f662bce93e03b46e47b088408c82471c5956b824e3320afb32b79919ef` |
| `panel-width-frame-250-attempt05-conic/conic-seeding.json` | `4278acc86a848bc45d4f3df558a235e1d95038a64812337501f307c36498b106` |
| `rawlocal/head-check/attempt02-panel-width/comparison.json` | `d01bfd5f7b8e6265233e23050cd399e797fd2cc671fe7f5c3f372cfaa7b606f4` |
| `rawlocal/head-check/attempt02-panel-width/receipt.json` | `e65b8dc6d38aa038034876a126a78493bb0f06fa06072cb13a68e96d77b5fb5f` |

For a fresh serialized response, use NumPy 2.2.6, SciPy 1.15.3, OSQP 1.0.4
and Clarabel 0.11.1:

```sh
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 uv run --no-project \
  --with numpy==2.2.6 --with scipy==1.15.3 --with osqp==1.0.4 \
  --with clarabel==0.11.1 python \
  docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/upper-corner-screw-layout/conic_frame.py \
  --operators docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/upper-corner-screw-layout/panel-width-operators-attempt01 \
  --output <new-output-directory>
```
