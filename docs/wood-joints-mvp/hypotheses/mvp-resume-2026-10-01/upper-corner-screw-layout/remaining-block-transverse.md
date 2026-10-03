# Remaining twenty cleats: finite transverse assessment

## Scope and source boundary

The owner requested extending the four-corner assessment to every remaining
corner block/cleat. The [completed source census](corner-physical-gravity.md)
identifies twenty distinct registered bodies, completing the 24-body register
with the four outer corners. This phase evaluates their own saved loads and
geometry in six simultaneous cases. It adds no frame solve, CAD change,
native mechanics, new hardware, preload or material resistance.

The authenticated source packets are:

| Source packet under `rawlocal/` | Bodies | Checks SHA-256 |
|---|---:|---|
| `header-cleat-net-sections/attempt01` | 6 | `b70fd818654a4d6509186a2718a81fa0b564cfc7ad808be52946f0eddfead1a2` |
| `knee-spine-net-sections/attempt02` | 2 | `6b6c8df94f1ccab859ee980dd1835ba19286718f44e8a36ce6b9d0014064fc85` |
| `remaining-net-sections/attempt01` | 12 | `80600628f956f5a957efca382d2c4e2ca9110cefbff8c7aee21a1995a430892f` |

Use the frozen `member-screen-attempt02/four-screw-layout01` point-action
archive, member geometry and original conditional references. Retain all
mechanical point forces and free couples at their archived application points.
Their placement is the source idealization: no bore-wall, washer-seat or
contact-pressure distribution is inherited from the four physical corner
calculations. The source's representative seating position is not a motion
envelope or proof of joint compatibility.

The source gravity multiplier is **1.1111358300342407**. It is distinct from
the timber load-duration factor `C_D`; this phase adopts no new duration credit.

## Physical gravity and geometry

Replace the archived discrete gravity actions once with uniform gravity on
the exact retained timber plus the twelve original allocated hardware receiver
point wrenches per body. Preserve each hardware free couple. Require source
load ownership to consist only of that timber and its allocated hardware,
and require every archived discrete force to match the original source node
load at the recorded multiplier. Stop the affected body if another load source
or contradictory shape/mass/centroid is found.

For each body and case, require complete gravity force and moment to agree
within the existing 1e-6 N / N·mm arithmetic tolerance. Original source density
is 600 kg/m³; an incompatible mass/centroid is not normalized into a new field.
All twenty geometries must remain outside the corrected model's separate
wood-mass deltas.

Fourteen bodies have only full transverse cylinders. Their exact clipped
volume and first moments reuse the frozen physical-gravity snapshot
`7666448f5f841d9a6d8a5cccededbb8047ec75df7463a4dd7c4a27a47693cf94`.
The six header/inner-knee bodies also have longitudinal holes. Their clipping
uses [longitudinal-bore-geometry.py](longitudinal-bore-geometry.py), SHA
`faab8b5e5ff13dc4252329ed2f8917d9e2054f05e823a4e5fdbeb11da46accc4`.
Parent's accepted geometry coupon is bound by checks SHA
`b397fbe1a6b673401df4c61666eab2b1a3539a22319bba162af83ea57eef6aee`
and receipt SHA
`9ee33a58d6567d62529dee5bd7338eaf4ffd38ef572da8b4e29435ee6392aee3`.
That saved result supplies the twelve known answers and six full-volume
crosschecks; the producer does not rerun the separate helper coupon.

## Cuts and normal equilibrium

Evaluate grain-, `u`- and `v`-normal cuts for all six cases, preserving the
full signed `[N, Vp, Vq, T, Mp, Mq]` wrench. Finite stations include source
point positions, hardware positions, projected actual contact-patch vertices,
bore centers/tangencies, near-face cuts and interval midpoints. There is no
continuous maximum claim. Contact geometry contributes event locations; the
archived mechanical contact actions remain point wrenches.

The rectangular support hull is valid only after certifying disjoint full
cylinders and retained hull corners. Reuse the frozen exact normal-resultant
lower-bound arithmetic. A positive bound requires normal tensile transfer
within the adopted action placement, but gives neither an actual bolt allocation
nor splitting resistance. A zero bound establishes only unbounded-pressure
normal equilibrium feasibility.

For transverse-only bodies, use the existing two grain-end compression bands.
For longitudinal-hole bodies, use four rectangles in both grain-end and
transverse-edge bands, with cut-specific disk chords excluded. Check every
rectangle against the actual cylindrical voids and recover the three normal
resultants exactly. Record a null construction when positive-area support is
unavailable. Compare constructed pressures only with the existing 625 psi /
4.309223308 MPa perpendicular-compression reference. An excessive sufficient
construction does not prove that every possible pressure field fails.

Grain comparisons reuse the prior nominal regional hypotheses and each body's
original CF-only references. Header bodies retain their prior artificial
rectangular subsets around longitudinal holes; those subsets are not a true
local-stress bound. Simultaneous shears and torque remain in the cut exports;
no transverse shear, rolling-shear, fracture or anchorage resistance is supplied.

## Parent execution

API: `build(output)`, with a fresh child of
`rawlocal/remaining-block-transverse/`. Prepared producer SHA-256:
`b7636729f666633feed74eb274968dc92b5d06620b4806ae697c79160869c9c8`.

```sh
.venv/bin/python docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/upper-corner-screw-layout/remaining-block-transverse.py --output docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/upper-corner-screw-layout/rawlocal/remaining-block-transverse/attempt01
```

Formatting/lint passed. The producer saves its snapshot,
all listed signed cuts, same-case witnesses, affected scope stops and source/
output receipt. Unsupported bodies stop without changing their geometry or
transferring another body's result. Splitting capacity remains null, and
complete-joint, formal, fabrication and physical-release flags remain false.

## Completed attempt01

Parent executed the frozen producer successfully. All twenty bodies were
evaluated with **no affected scope stops**. Independent authentication
confirmed all 40 source entries and four outputs in the receipt.

| Coverage or result | Recorded value |
|---|---:|
| Bodies × cases × cut orientations | 20 × 6 × 3 = 360 |
| Full signed cut limits | 19,536 |
| Grain-normal cut limits | 8,472 |
| Transverse cut limits | 11,064 |
| Positive necessary normal-tension cut limits | 5,614 |
| Finite compression witnesses | 5,450 |
| Compression-feasible limits without a finite construction | 0 |
| Constructed pressures above existing compression reference | 0 |
| Maximum necessary normal tensile lower bound | 430.147568 N |
| Maximum constructed pressure | 0.513712400 MPa |
| Maximum whole-gravity force difference | 3.553e-15 N |
| Maximum whole-gravity moment difference | 7.787e-8 N·mm |

The preserved whole-body force residual is at most 4.880e-12 N and its moment
residual at most 7.805e-8 N·mm. Uniform retained-volume density and centroids
matched the original selfweight sources for all twenty bodies. The original
hardware wrenches and source gravity multiplier remained unchanged.

### Recomputed grain comparisons

| Nominal comparison under the recorded hypotheses | Maximum ratio |
|---|---:|
| Longitudinal tension / Ft | 0.134564039 |
| Longitudinal compression / Fc | 0.077157036 |
| Bending / Fb | 0.090305330 |
| Existing axial-plus-bending reference sum | 0.096312712 |
| Simultaneous regional shear/torsion / Fv | 0.382534988 |

All five maxima occur on `knee_outer_right_spine` / K12-right. Tension peaks
at grain station 171.8757131684937 mm before; compression, bending and the
reference sum at 191.61555301851 mm after; shear/torsion at that latter station
before. All computed nominal ratios remain below the original references.
The reference sum remains a diagnostic rather than a new adopted interaction
or stability law. The changed grain cuts were explicitly replayed; their
results are not inherited from the older grain-only packets.

### Body-specific transverse results

These are maxima across each body's own six cases and both transverse
orientations. The normal and pressure maxima need not share a case or cut.
Normal tension is a necessary resultant lower bound under archived mechanical
point-force/free-couple placement. It is not an actual bolt force, a spare
holding force or a force-to-capacity ratio.

| Body | Maximum necessary normal tensile lower bound (N) | Maximum constructed compression pressure (MPa) |
|---|---:|---:|
| `bottom_center_left_cleat` | 0 | 0.006611 |
| `bottom_center_right_cleat` | 0 | 0.005226 |
| `center_post_cleat_left` | 1.364486 | 0.006779 |
| `center_post_cleat_right` | 1.468498 | 0.006926 |
| `center_principal_cleat_left` | 4.933802 | 0.022880 |
| `center_principal_cleat_right` | 5.172594 | 0.025362 |
| `knee_outer_left_inner_frame_block` | 99.348970 | 0.513712 |
| `knee_outer_right_inner_frame_block` | 96.891539 | 0.315908 |
| `knee_outer_left_spine` | 430.147568 | 0.190883 |
| `knee_outer_right_spine` | 424.262642 | 0.175452 |
| `left_service_inner_lower_cleat` | 0 | 0.005100 |
| `left_service_inner_upper_cleat` | 0 | 0.008248 |
| `left_service_outer_lower_cleat` | 4.138389 | 0.005540 |
| `left_service_outer_upper_cleat` | 4.653660 | 0.006672 |
| `top_center_left_cleat` | 21.123256 | 0.112487 |
| `top_center_right_cleat` | 77.058698 | 0.023240 |
| `wj04_lower_full_stock_cleat` | 0 | 0.003751 |
| `wj04_upper_g7_crosscut_full_stock_cleat` | 0 | 0.013876 |
| `wj06_outer_lower_right_cleat` | 4.179822 | 0.005579 |
| `wj06_outer_upper_right_cleat` | 4.720768 | 0.006781 |

Six bodies have zero necessary normal tension at every listed transverse
limit. Fourteen have at least one positive bound. Every compression-feasible
listed limit has a supported finite construction below the existing
4.309223308 MPa reference. These normal equilibrium results do not establish
the remaining simultaneous shear/torque transfer or local crack resistance.

The deciding normal-tension witness is `knee_outer_left_spine` / A12-left /
`v=5.971913348000001 mm`, after, with full signed wrench:

```text
[N, Vp, Vq, T, Mp, Mq] =
[361.460505326, -319.719714754, -65.271022406,
 12222.472553189, 9502.799720561, -90983.154729319]  (N, N·mm)
```

Its normal resultant is already tensile. The unbounded-pressure hull solution
requires at least 430.147568 N normal tension and 68.687063 N compression.
The source action placement and free couples remain explicit; the result
does not establish a physical failure load or assign an actual reinforcement
force to a bolt. The right spine's maximum across its own six cases is
424.262642 N.

The highest compression construction is
`knee_outer_left_inner_frame_block` / A1-rear /
`v=31.722355784 mm`, before. Its four retained-material rectangles recover
the normal wrench; the peak pressure is 0.513712400 MPa, approximately 11.9%
of the existing perpendicular-compression reference. Simultaneous shears
−28.718178 and 39.015668 N and torque −534.672170 N·mm remain unqualified
by that normal-pressure construction.

### Frozen output authentication

| `rawlocal/remaining-block-transverse/attempt01/` output | SHA-256 |
|---|---|
| `checks.json` | `f3118804d3a03df66d274d783ca93248757ac3d629de4a874d23e85da9a61f19` |
| `cuts.jsonl.gz` | `86757d2db86751aa5cba5343df0065ac3d38cc7d69eeab71f02c55eedc72d4cc` |
| `producer.py.snapshot` | `b7636729f666633feed74eb274968dc92b5d06620b4806ae697c79160869c9c8` |
| `receipt.json` | `dce3437a105cdd269aec9ff98ac831c00d6e64e34a807c42254030ca4fffb519` |

The bounded twenty-body finite assessment is complete. It closes the missing
listed cut-demand census and records supported compression constructions.
Splitting capacity remains null; whole-cleat acceptance is not established.
This point-action scope remains distinct from the four corners' separately
developed physical bore-wall/washer/contact action distributions.
