# Exact all-bearing floor-stick MPC reaction fixture

This input-only coupon tests the force output needed by an exact tangential
floor constraint. One physical node has only x and z motion. Its x displacement
is the unique dependent DOF in a homogeneous equation tied to a fixed ground
reference; the x load is applied directly to that dependent physical DOF. Two
isolated linear `SPRING2` projections give a known positive-definite structural
matrix, and one straight-line compression-only `SPRINGA` supplies the normal
reaction. There is no frame, corner, or wood joint in this model.

The equation pivots are unique and unclamped:

| Dependent DOF | Equation | Purpose |
| --- | --- | --- |
| `P,1` | `u(P,1) - u(FLOOR_REF,1) = 0` | Exact x stick; `FLOOR_REF,1` is fixed |
| `XZ_PROJECTION,1` | `s = u(P,1) + 0.25 u(P,3)` | Isolated `SPRING2`, `k=20 N/mm` |
| `Z_PROJECTION,3` | `u = u(P,3)` | Isolated `SPRING2`, `k=98.75 N/mm` |
| `NORMAL_Q,3` | `q = -u(P,3)` | Compression-only normal `SPRINGA` coordinate |

The structural stiffness is known by construction:

```text
20 [1, 0.25]^T [1, 0.25] + 98.75 [0, 1]^T [0, 1]
= [[20, 5], [5, 100]] N/mm
```

The normal carrier starts at a 100 mm span, with its first endpoint at
`z=100 mm` and the second endpoint fixed at `z=0`. Its signed coordinate is
`q=-z`; physical compression (`z<0`) makes `q>0` and increases the carrier
length to `100+q`. The one-sided table is force first, elongation second:
`(0 N,-10 mm)`, `(0 N,0 mm)`, `(1000 N,10 mm)`. Thus the closed law is
`f=100 max(q,0) N`; the open branch is zero. The inspected 2.23 `ident.f`
routine selects the interval to the right of an exact table knot, so the
initial closed-side tangent at `q=0` is `100 N/mm`. The table gives positive
native internal force for positive `q`; through `q=-z`, physical floor force
in `+z` equals that internal force. The carrier length is numerical and does
not represent a physical member or floor gap.

| Case | Applied `(Wx,Wz)` N | `z` mm | `s` mm | XZ spring internal N | Z spring internal N | Normal force N | Hand floor `Rx` N |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | `(6,-20)` | `-0.1` | `-0.025` | `-0.5` | `-9.875` | `10` | `-6.5` |
| 2 | `(-4,-40)` | `-0.2` | `-0.05` | `-1` | `-19.75` | `20` | `3` |

The independent physical balances are `Wx + Rx - f_xz = 0` and
`Wz - 0.25 f_xz - f_z + f_normal = 0`, where `f_xz` and `f_z` are the
native generalized internal spring forces. These equations yield the hand
`Rx` values above, including the CLOAD applied on dependent `P,1`.

CalculiX 2.23 section 7.56 says the first term of `*EQUATION` is eliminated
and may not also be an SPC or another dependent term. Section 7.99 defines
`NODE PRINT,RF` as external forces containing reaction forces and applied
concentrated/distributed loads. The reference-node RF sign and whether its
reported value includes the dependent-node CLOAD remain to be observed. The
assessor checks four fixed interpretations—`RFref`, `-RFref`, `RFref-Wx`, and
`-RFref-Wx`—consistently across both cases, then requires one unique map to
match the hand reactions and close both physical balances. It retains the raw
reference and dependent-node RF values. No per-case sign choice or fitted
residual is accepted.

The exact deck uses
`*STEP,NLGEOM,NLGEOM=NO,INC=40`. The official 2.23 source `steps.f` parses the
bare `NLGEOM` first to enable Newton iterations, then `NLGEOM=NO` turns
geometric effects off. The assessor requires Newton-active and explicit
`effects are turned off` evidence for both steps, and rejects output claiming
nonlinear geometric effects were taken into account. This combined option is
a fixture method input; it says nothing about the reviewed frame response.

The 2.23 manual is pinned at
[`fea/generated/ccx_2.23.pdf`](../../../../../fea/generated/ccx_2.23.pdf),
SHA-256 `a0bf3fc03f374912ff2bf28da3f7dfb6a61428dd7f41b281a2e7e1fdb318f330`.
The inspected source archive is
[`ccx_2.23.src.tar.bz2`](https://www.dhondt.de/ccx_2.23.src.tar.bz2),
SHA-256 `9c88385c10fb04f5dc6c4e98027a51bebdd8aee3920e05190d6c1dd08357d6e7`;
`src/ident.f` lines 20–42 document/select the right interval at a knot, and
`src/steps.f` lines 156–185 contain the sequential `NLGEOM` parsing.

Regenerate the inspectable, unfrozen root-level `model.inp` and `model.json`
from the repository root with:

```sh
uv run --no-sync python3 docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/current-exact-floor-mpc-fixture-attempt01/prepare.py
```

`assess.py` is for use only after parent-owned freezing, readiness review, and
the serialized native launch. This packet has no freeze or run result. Passing
the coupon would establish only the bounded output mapping and scalar normal
law in these known-answer cases. It would establish no floor friction,
anchorage, floor history or capacity, member/joint demand, frame acceptance, or
corner acceptance. No floor or complete-joint capacity is assigned.


## Observed result

Failed before mechanics: CalculiX rejected the linear spring card with integer-form stiffness `20`. No mechanical output or physical failure was established. Frozen inputs and execution remain preserved. See the separately formatted [attempt02](../current-exact-floor-mpc-fixture-attempt02/README.md).
