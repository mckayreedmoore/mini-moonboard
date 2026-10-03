# Frozen right-cleat applied-action recovery

The six frozen right rail/side pair states recover physical point and sampled
pressure actions with whole-cleat force residuals at most **0.000101402 N**, but
moment residuals reach **2660.691104 N·mm**. The discrepancy from the balanced
rigid dual reaction is exactly the fixed-axis geometric-tension term, together
with recorded beam-gradient residuals and numerical roundoff. The largest
unexplained interface component is **3.2833e-10**, in N or N·mm as appropriate.
**These recovered wood actions cannot be accepted as independent equilibrated
timber-section actions of the current rigid model.**

The original pair and whole-block results remain preserved. Existing dual
complete-host cuts remain equilibrium totals within their recorded scope; they
do not supply the missing spatial wood traction allocation inside this cleat.
No balancing free couple is added. This worksheet does not repeat the
[group-resistance applicability worksheet](block-group-resistance.md).

## Frozen scope and independently recovered actions

[The producer](cleat-traction.py) performs finite arithmetic on six existing
states, both hosts and all four actual right bolts. Its common datum is
`c=[1082.675,1405.0269362284803,2125.1250400802173]` mm. Wrenches are ordered
`[Fx,Fy,Fz,Mx,My,Mz]`, in global N and N·mm. Moment transport is
`M_new=M_old+(c_old-c_new)×F`; every comparison uses this same datum.

For each bolt, `n` is the signed head-to-nut axis, and the columns of `B` form
the saved transverse local2 basis, with `B0×B1=n`:

| Interface | n | B0 | B1 | Host / cleat grip, mm |
| --- | --- | --- | --- | ---: |
| Rail | `[0,-0.642787610,-0.766044443]` | `[1,0,0]` | `[0,-0.766044443,0.642787610]` | 38.1 / 139.7 |
| Side | `[-1,0,0]` | `[0,0,1]` | `[0,1,0]` | 88.9 / 88.9 |

The arithmetic uses the full saved values, not these rounded display values.
For an existing interface point `p`, host grip `h`, cleat grip `k`, and total
grip `L=h+k=177.8 mm`, the recovered actions are:

1. **Bore station resultants.** At every saved bore quadrature station,
   `r=p+(x-h)n` and `F_wood=-force_on_beam_xyz_n`. The signed local2 check is
   `F_wood=-B force_on_beam_in_basis_n`. Each receiver has eight beam elements
   and three quadrature stations per element. These are resultants at the
   requested shaft-axis stations, not a recovered radial bore-wall traction
   field; they do not identify how force divides among timber material regions.
2. **Own outer wood washer pressure.** Recover the saved compression-only
   wood pressure over its own annulus, using eight radial Gauss points and
   32 half-step azimuths. The rail ID/OD are 8.3058/18.4658 mm; the side ID/OD
   are 9.906/22.0472 mm. With saved wood closure `d`, wood tilt `a`, area `Ai`
   and local quadrature coordinates `(xi,yi)`,
   `pi=20 max(d+a xi,0)` MPa and `Ti=Ai pi`. Let `u` be the unit saved
   relative-end slope, and `Ju=[-u1,u0]`. For `sigma=+1` at the cleat nut
   and `sigma=-1` at the host head,
   `ri=rseat+sigma B(u xi+Ju yi)` and `Fi=-sigma Ti n`.
   The nut seat is `p+k n`; the head seat is `p-h n`. The recovered own
   contact centroid is `rseat+sum(Ti*(ri-rseat))/sum(Ti)`. At either end,
   the own wood pressure moment is `n×B(Mwood u)`, where
   `Mwood=sum(Ti xi)`. This is the opposite of the saved beam end moment,
   subject to the retained head/wood series-contact residual. The centroid
   carries the moment through its point arms; no second end couple is added.
3. **Actual face cells.** Apply `compression_n*n` to the cleat at each saved
   cell point, and its opposite to the host. Both finished interfaces retain
   their existing 16 cells, including inactive cells.
4. **Original current mapped W.** Reconstruct all 20 cleat-node forces from
   original load operator `F`, existing native DOF labels, and model-node
   coordinates. For case index `i`, use
   `1.1111358300342407*F[:,2i]+F[:,2i+1]`. Their independently summed wrench
   matches the original six-row cleat block of `W` and the completed
   whole-block mapped load, including original nodal signs and load moments.
   Rotational W entries are converted from N·m to N·mm. The summed load is
   `[0,0,-10.5308411756,-38.5123286663,7.8831187643,0]` to displayed precision.
   It is the original mapped load, not a substituted uniform timber weight.

The recovered nominal outer wood seats also match the completed component
seat points within 1e-7 mm. Repeating the same pressure recovery on the host
head annuli, together with host bore and face actions, independently matches
the saved host wrenches: maximum component error **2.4011e-10 N or N·mm**.
This establishes the pressure signs and end-slope frame convention used here.
No nominal annulus is translated by a beam-end displacement.

There are 1172 retained cleat actions per case: 96 bore stations, 1024 wood
washer samples, 32 face cells and 20 mapped-load nodes, including zeros.
The action inventory contains **7032** entries across six cases.

## Exact geometric-tension identity

For one bending plane, the 34-entry beam vector has
`q[2j]=w(xj)` and `q[2j+1]=L*w'(xj)`. Let `K` be the elastic beam operator,
`G` the unit-tension geometric operator, and `g` the saved beam-only gradient.
The producer independently reconstructs all four terms:

```text
g = Kq + T Gq + g_bore + g_end
g_bore = -sum(Hj^T force_on_beam_local2_j)
g_end[1]  = m_head/L
g_end[33] = m_nut/L
```

The identity sums both planes and both bolts of each interface. `R` maps a
rigid virtual translation/rotation at `c` to the nominal beam centerline:
`delta w=B^T(delta t+delta theta×(r(x)-c))`,
`delta w'=B^T(delta theta×n)`. Therefore,

```text
S = 1/2 q^T Gq = 1/2 integral |w'|^2 dx
delta(T S) = T integral w'·B^T(delta theta×n) dx
           = delta theta·[T n×B(w_L-w_0)]

R^T(T Gq) = [0, A],  A = T n×B(w_L-w_0)
R^T(Kq)   = 0, apart from floating-point roundoff
```

Here `w_L-w_0` is the saved transverse beam **end displacement difference**,
not an end-slope difference. Nominal head/nut axial actions are equal and
opposite along the same nominal `n`, so their combined moment is zero.
The recovered wood bore and own annular pressure moments supply
`R^T(g_bore+g_end)`. Opposed face actions cancel between host and cleat.
With `Q_H` the saved host wrench, `Q_H,physical` its independently recovered
wrench, `Q_C,dual=-Q_H` and `Q_C,physical` the recovered cleat wrench:

```text
Q_C,physical - Q_C,dual
  = -sum_bolts [0,A]
    + sum_bolts R^T g
    - sum_bolts R^T(Kq)
    - (Q_H,physical - Q_H)
```

The producer checks this full identity, retaining the actual gradient
residual and roundoff rather than treating a small solver residual as zero.
Its maximum unexplained component is 3.2833e-10 N or N·mm.

The host end-slope frame term is also independently checked:
`s_head=w'_0-B^T(theta_host×n)` and `s_nut=w'_L`. This supplies the existing
head pressure moment and already reproduces the host wrench. It does not
cancel `A`. The axis basis is held fixed in the shortening operator; the
operator has nonzero work under this common rigid beam rotation.

### Primary equations and exact source locations

| Term | Frozen primary source |
| --- | --- |
| Wood quadrature, compression pressure and own moment | [combined helper, lines 64–103](upper-right-combined-transfer.py#L64); pressure is lines 89–95 |
| Head/wood series moment equality | [combined helper, lines 106–125](upper-right-combined-transfer.py#L106) |
| Unit geometric operator | [combined helper, lines 146–157](upper-right-combined-transfer.py#L146); element initial-stress matrix is lines 153–155, scaled assembly line 157 |
| Pair operator placement and host bore mapping | [rail helper, lines 161–188](upper-right-rail-pair.py#L161); geometric beam blocks lines 168–172; bore point line 178 |
| Relative head slope frame | [rail helper, lines 182–185](upper-right-rail-pair.py#L182) |
| S in axial compatibility/energy; T Gq and tangent | [rail helper, lines 210–264](upper-right-rail-pair.py#L210); shortening line 212, target line 215, energy line 240, gradient line 241, Hessian line 242, tension derivative line 243 |
| Bore reaction and beam-only gradient | [rail helper, lines 273–303](upper-right-rail-pair.py#L273) |
| Saved end-moment and bore-force global signs | [rail helper, lines 384–397](upper-right-rail-pair.py#L384) |
| Saved beam displacements/slopes | [rail helper, lines 416–417](upper-right-rail-pair.py#L416) |
| Same equations for actual right side | [side adapter](upper-right-side-pair.py), `load_sources` imports the pinned rail helper with side dimensions, basis, datum and rows |

The producer calls only the existing `annulus`, `beam_model(family,1.0)` and
DOF-label parser for this arithmetic. It does not call contact root solving,
axial elimination, pair evaluation/minimization, native mechanics or CAD.

## Six-case independent force and moment account

Values below are the sum of recovered cleat actions plus original mapped W
at `c`. The last column is the largest absolute moment component of the
preserved rigid-dual whole-block residual, independently reproduced here.

| Case | Maximum abs F, N | Mx, N·mm | My, N·mm | Mz, N·mm | Maximum abs dual M, N·mm |
| --- | ---: | ---: | ---: | ---: | ---: |
| a12-rear | 3.12072e-6 | 66.550159 | 8.565190 | 87.156937 | 4.88616e-4 |
| a12-forward | 1.86428e-8 | 15.465221 | 1.805355 | 21.563958 | 5.73632e-5 |
| a12-left | 3.04142e-8 | 21.336543 | −1.309166 | 33.669041 | 2.10150e-4 |
| k12-right | 1.44915e-6 | 2660.691104 | 491.573723 | 1683.363130 | 9.98383e-7 |
| k12-rear | 7.98633e-8 | 2637.885840 | 506.611497 | 1690.840417 | 3.98250e-8 |
| a1-rear | 1.01401e-4 | −0.003241 | −0.026240 | 0.549288 | 1.23682e-6 |

All recovered forces fit the existing 0.002 N whole-block accounting
tolerance. Five cases exceed its 0.6 N·mm moment tolerance. The a1-rear
moment happens to be below that tolerance; its same geometric mechanism
remains, so this is not independent section-action qualification.

For k12-right, the interface physical-minus-dual moment vectors are
rail `[2660.691151,-53.860928,45.194684]` and
side `[-0.000047,545.434651,1638.168446]` N·mm. Their signed sum explains the
whole-cleat defect; neither host is omitted. The corresponding boltwise
`A=T n×B(w_L-w_0)` values are:

| Bolt | Ax, N·mm | Ay, N·mm | Az, N·mm |
| --- | ---: | ---: | ---: |
| rail_1 | −1674.628984 | −11.177205 | 9.378788 |
| rail_2 | −986.062168 | 65.038132 | −54.573472 |
| side_1 | 0 | 64.192201 | 80.197059 |
| side_2 | 0 | −609.626832 | −1718.365442 |

## Cut-action applicability and physical correction limit

The receipt retains finite before/on/after action sums at the four existing
bolt grain planes, using the actual frozen cleat grain direction
`[0,0.766044443,-0.642787610]`, normalized from model inputs. The two side
stations share a grain plane but retain their own identities and moment
datums. On-plane jumps are retained with a 1e-6 mm classification tolerance.

For either limiting cut, the candidate internal wrench obtained from the
negative half and the candidate obtained from the positive half disagree
by the negative full recovered external residual, transported to that cut.
These are inspectable point-action candidates, **not accepted timber-section
loads**. No finished-section stress, hole-wall radial distribution, sharing
among disconnected material regions, or timber resistance is inferred.

A prospective endpoint relocation illustrates the lever-arm issue:
moving the nominal head `+Tn` to `r_head+B w_0` and nut `−Tn` to
`r_nut+B w_L` adds combined moment
`T[(B w_0)×n-(B w_L)×n]=+A`. That algebra alone does not establish actual
wood contact positions. It would also change the host action that already
matches the saved host wrench. The frozen model supplies nominal concentric
annuli, interface opening and relative-end slopes; it supplies no translated
outer wood pressure field tied to those beam-end coordinates. Moving those
seats alone also does not establish consistent deformed bore/face positions
and force directions. **No independently physical correction is established
or adopted by this recovery.**

The parent owns any separate first-order local calculation. Removing the
geometric operator consistently from shortening, axial energy, gradient and
tangent removes this identified operator contribution; resulting states and
physical action balance still require their own evidence. No result from
that separate calculation is imported here. Original loads, assumptions,
mechanics, results and group worksheet leaves remain frozen.

## Producer, command and receipt

The delivered producer is frozen at SHA256
`2834a9a9fd25083da16034b498b3356197a4a6b2b53ffb35663077c5f93f7764`.
Its `wood_seat`, `action` and `wrench` functions may be reused as pinned
arithmetic by the parent's separate calculation. They do not solve mechanics.

Recorded command, from the repository root:

```sh
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1 \
  .venv/bin/python docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/upper-corner-screw-layout/cleat-traction.py \
  --output docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/upper-corner-screw-layout/rawlocal/cleat-traction/attempt01
```

Attempt01 exists and is preserved. The producer requires a fresh owned output
directory; any parent-requested replay must use a new attempt name. Recorded
runtime: Python 3.12.3, NumPy 2.5.2. Ruff format/check passed. No tests,
mechanics solves, model changes, staging or commits were performed.

| Ignored attempt01 artifact | SHA256 |
| --- | --- |
| [checks.json](rawlocal/cleat-traction/attempt01/checks.json) | `86b65abab399237533e047587d4de8de413c57d25c13b70a07e1e1f6ecf03d4f` |
| [applied-actions.jsonl](rawlocal/cleat-traction/attempt01/applied-actions.jsonl) | `e5564a1977efd8655731b9f77555fcad7358a31a74fa4237fb3235d26c149166` |
| [producer.py.snapshot](rawlocal/cleat-traction/attempt01/producer.py.snapshot) | `2834a9a9fd25083da16034b498b3356197a4a6b2b53ffb35663077c5f93f7764` |
| [receipt.json](rawlocal/cleat-traction/attempt01/receipt.json) | `124435dfac4949e556d45aef80db5b1a4eb13ff7f0568ac78ebe0d56cc8eb374` |

The receipt records all 23 source pins, checked before arithmetic and again
before publication of the raw receipt. Principal bindings are:

| Frozen input | SHA256 |
| --- | --- |
| Right whole-block attempt01 checks | `0b0b392b9e5e411173395671878c09e0be303abd4885f48d1e7e7b61d8f6a89b` |
| Right rail pair attempt01 checks | `e0cccb56abb94ed16c322da888cd64a9904c4e49d1e34f573a6903c8b8b98d3d` |
| Right side pair attempt01 checks | `b507a5a501737c89814a471eee6a12749a3c54224f5444b2c5d583020e875ba7` |
| Completed component seat evidence | `401b8876dc3a96b553c847f1029a5a9200ba3f45af5493f64edd61fdc6bc42b6` |
| Current model | `b5f9b87b70c4a9920372a3443a55e37dfe34351fb9ac8210b299c1360fb93626` |
| Current frame comparison | `bea6cbc330af3cdb20499d774a8f6bb24481d687c3150adb01ede18e4c1d50ca` |
| Current frame response | `0625196497b0dbc7b297724d7b9947f7c7c61bb282cd4d9681705629302c76c7` |
| Combined transfer helper | `fba852724b82ee3cd28b0318bfdf156ac1786f85ac26257698d8d103c26c62b0` |
| Pair mechanics helper | `4243b53bbb7377753f0b1fdd73fa1aa6c80e1a96c99d428def88e82a899e6f96` |

The preserved group producer/worksheet pins are respectively
`e5df5f81168a0e700948816a5c292c521593b328ab86fb72b1a2e2f0cd98b3b0`
and `8bcfbef56e69fb203fcc87a95c16df4d6eb16b7c544d83359dbf0b74c66bab77`.
Only this producer, this worksheet and the ignored traction receipt belong to
this task. The remaining genuine timber transfer/resistance requirement is
preserved; this action recovery assigns no capacity or complete-joint release.
