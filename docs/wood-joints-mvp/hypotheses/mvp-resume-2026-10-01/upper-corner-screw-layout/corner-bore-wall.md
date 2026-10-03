# Corner bore-wall mapping

[The frozen producer](corner-bore-wall.py) supplies one algebraic known answer
and a finite wall route, executed once by the parent in
[attempt01](rawlocal/corner-bore-wall/attempt01/checks.json). It preserves the source
forces and resultants exactly. Load reconstruction, rescaling and new mechanics
are outside this packet. Ruff format/check passed; the
[preparation receipt](rawlocal/corner-bore-wall/preparation.json) authenticates
38 source/producer pins. The completed parent execution receipt is recorded below.

**Engineering result:** every transverse shaft-axis resultant has a finite,
nonnegative radial pressure representation on a supported cylindrical wall
with exactly the same force and moment. The current four cylinders have a
conservative inter-wall clearance bound of at least **8.25 mm**. The parent
run checked the actual stock margins and mapped that representation into
the deciding grain cuts. No balancing couple or resistance is introduced.

## Frozen inputs and deciding cuts

The source is the completed first-order result, SHA256
`b15b57d3879fdca2dac607d11a2ad127acd1008f6c2a6f546333a1b26c754cfe`.
Use its saved `physical_cleat_actions` and matching `bore_fields`, including
signed `F = -force_on_beam`, axial stations and Gauss weights. Each actual
cleat has 119.7 mm grain length, an 88.9×139.7 mm blank and four through
cylinders. Geometry comes from the frozen timber packet; CAD is not opened.

| Actual state | Grain stations s, mm | Saved limits |
| --- | --- | --- |
| Right K12-rear | 62.973880402093315; 59.85000000087682 | Before and after each |
| Left A12-left | 56.39975267961501; 59.85000000074149 | Before and after each |

The first station is each side's existing deciding disconnected-cut witness;
the second is its paired side-bore center. The same-state complete-cut
inventory is SHA256
`0294778e879733fd28c72fe4c2a9e246569d02ce0176ca58b6a0fbd11f650372`.

## Finite pressure preserving the full wrench

For axis point `r0`, transverse force `F`, signed unit bore axis `n`, radius
`R` and original axial quadrature weight `w`, set `e=F/|F|`, `h=n×e`:

```text
er(theta) = e cos(theta) + h sin(theta)
r(theta)  = r0 + R er(theta)
p(theta)  = 2|F|/(pi R w) cos(theta),  -pi/2 <= theta <= pi/2
p(theta)  = 0 elsewhere
dF        = p(theta) R w er(theta) dtheta

C         = 2|F|/pi
F_arc     = C { e[(b-a)/2 + (sin(2b)-sin(2a))/4]
                + h[(sin²(b)-sin²(a))/2] }
M_arc(c)  = (r0-c) × F_arc
```

The pressure is nonnegative and its radial offset has zero moment pointwise:
`R er × dF = 0`. Integration over the loaded half-wall gives exactly `F`
and `(r0-c)×F` at any common datum. The alternative ray point `r0+R e`
also preserves the wrench because its displacement is parallel to F.
The cosine distribution is an explicit MVP placement hypothesis; the ray
is only a concentrated placement witness. Neither specifies a new contact
law or changes the saved scalar bearing-pressure result. The Gauss weight
remains a quadrature measure, not an invented physical strip width.

`wall_support` checks every complete circumference against stock faces and
all other cylinders. Coordinate reach is `R sqrt(1-n_j²)`; the other-bore
clearance bound is `d-R-R_other`. Current orthogonal families give
`16.5-3.75-4.5 = 8.25 mm`; parallel rail and side pairs give 25.5 and
58.85 mm. These bounds establish separation; the run still checks each
station's stock margins with 1e-6 mm rounding tolerance.

An axial force component cannot be supplied by frictionless radial pressure.
If full-wall support fails, the exact missing assumption is a supported
angular pressure domain carrying the prescribed F. Unsupported pressure is
not discarded and renormalized. A conservative certificate failure alone
does not prove impossibility; `partial_wall_obstruction` proves it when all
supported radial normals have nonpositive projection along F.

## Which wall load reaches which cut branch

Exact roots of `A cos(theta)+B sin(theta)=D` split each pressure arc by grain
half, wall branch and retained-region bounds. Every resulting arc retains
its full force and moment. At both paired-bore target planes, regions 0/1/2
run from low to high v:

| Actual side | Bore | Lower wall borders | Upper wall borders |
| --- | --- | ---: | ---: |
| Right | side_1, v=+33.925 mm | Region 1 | Region 2 |
| Right | side_2, v=-33.925 mm | Region 0 | Region 1 |
| Left | side_1, v=-33.925 mm | Region 0 | Region 1 |
| Left | side_2, v=+33.925 mm | Region 1 | Region 2 |

`applied_wall_branch_wrenches` gives the applied boundary load on each
branch. `projection_at_cut_region_ids` separately records geometric
projection: a wall point can project into the cut's bore void while its
wall branch adjoins retained wood. Remote rail bores remain labeled
`remote_bore_end_bridge`, with their full wrenches retained. Empty or multiple
region labels do not cause load deletion or arbitrary division.

The eight saved complete cuts already include face/washer loads and original
nodal W once. Only bore placement changes, at the same cut datum:

```text
Delta          = Q_axis_bore,negative_half - Q_wall_bore,negative_half
I_negative,new = I_negative,saved + Delta
```

The opposite-half internal account receives the same correction because the
full bore wrench is unchanged. Existing closure residuals and whole-cleat
equilibrium are preserved. Within a hole the cut allocation can change;
the returned `cosine_wall_complete_cut_grain_u_v_n_nmm` is conditional on
this explicit angular pressure shape.

### Explicit MVP section and sharing hypotheses

For a longitudinal section screen, the parent may assume
`sigma_grain = a + b*u + c*v` over the actual retained net area and determine
the coefficients from one state's N and both bending moments. At a cut with
separate ligaments, this additionally assumes the continuous grain-end
bridges maintain a common longitudinal strain plane. It is an explicit MVP
compatibility hypothesis, not a measured strain field. Torque and transverse
shear remain separate actions; longitudinal plane-section arithmetic does
not dispose of them.

A stated static regional route can also be used as an MVP hypothesis. With
regional datum `c_j` and common cut datum c, its complete same-state wrenches
obey `sum_j [F_j; M_j + (c_j-c)×F_j] = Q_cut(c)` and route through retained
wood. The branch table supplies local applied loads; end-bridge sharing is
the stated hypothesis. This packet leaves regional internal wrenches
unassigned. It supplies no capacity, Ft-perp/F90 conversion or group/splitting
acceptance. Existing applicable resistance bases remain in the frozen timber
worksheet.

## One known answer and mapping API

The prepared coupon uses `r0=[3,4,5] mm`, a Z-axis cylinder, `R=2 mm`,
`w=5 mm`, `F=[10,0,0] N` and datum zero. Expected pressure peak is
`2/pi MPa`; full wrench is `[10,0,0,0,50,-40] N/N·mm`. The ray point
`[5,4,5]` gives the same wrench. The positive-y pressure half carries
`[5,10/pi,0,-50/pi,25,30/pi-20]`. Above the X=4 mm cut, the force is
`[20/3 + 5 sqrt(3)/pi,0,0] N`. The same coupon checks that normals confined
to nonpositive X cannot carry positive-X F. The parent run returned these
analytical answers with maximum arithmetic component error 1.77636e-15.

The module has no import-time arithmetic. Public functions are
`pressure_profile`, `pressure_arc_wrench`, `ray_wall_resultant`,
`wall_support`, `partial_wall_obstruction`, `state_profiles`,
`cut_pressure_arcs`, `map_state_cut` and `algebraic_coupon`. Actual-state
profiles use the support certificate. The section helper is the frozen
`corner-timber-sections.py`, SHA256
`d0e2c5cb94b056cab71072fcab52cc7be8760fb7d32368c097a45050b3493633`.

## Parent execution receipt and frozen producer

The completed run contains 12 actual block states, 1152 bore samples and
all eight deciding cut limits. Every sample's complete wall-support
certificate passed. Maximum absolute change in a complete state bore-wrench
component was **2.27374e-13 N** for force and **1.45519e-11 N·mm** for moment.
The original whole-cleat moment residuals were retained: maximum absolute
components **0.000981443 N·mm left / 0.00449957 N·mm right**. There are zero
added balancing free couples; the saved nonbore actions and original W
remain counted once.

| Execution artifact | SHA256 |
| --- | --- |
| [Checks and all eight cut mappings](rawlocal/corner-bore-wall/attempt01/checks.json) | `b95e7fc3d1d60c94ae449c681d4cec12221345a5ba0eb865f3ca225086350caf` |
| [Receipt](rawlocal/corner-bore-wall/attempt01/receipt.json) | `465d7caf7a37889b24970062f9739d2f450573c97139f82167b5c17dac70ad3b` |
| [Executed producer snapshot](rawlocal/corner-bore-wall/attempt01/producer.py.snapshot) | `0ad9c88be2496f1b2ae9b06cb31f0cb7d9d95a236ffb4b2dc586873b7cf4a185` |

For the existing deciding witnesses, the mapped complete cuts are below.
Vectors use `[N, V_u, V_v, T, M_u, M_v]`, in N and N·mm; both paired-bore
center limits are also retained in the checks file.

| Actual witness | Cosine-wall complete cut, rounded |
| --- | --- |
| Right K12-rear, s=62.973880402093315 mm, after | `[578.447877, -499.294359, -697.076245, -20060.198873, -29971.795201, -37370.105751]` |
| Left A12-left, s=56.39975267961501 mm, before | `[505.806148, -445.073947, -614.223865, 20758.139911, 26529.503846, 33484.841225]` |

This receipt establishes the chosen physical wall placement and its same-state
cut correction. Regional internal sharing and net-plane-section use remain
the explicit working hypotheses described above; formal group/splitting and
elastic qualification are unestablished. This run assigns no new capacity.

Producer SHA256:
`0ad9c88be2496f1b2ae9b06cb31f0cb7d9d95a236ffb4b2dc586873b7cf4a185`.
The parent executed the following command, including the coupon and finite
mapping; it is retained for reproduction, not a request to rerun:

```sh
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1 \
  .venv/bin/python docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/upper-corner-screw-layout/corner-bore-wall.py \
  --output docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/upper-corner-screw-layout/rawlocal/corner-bore-wall/attempt01
```

Use a fresh output child. The CLI reauthenticates sources, writes
`checks.json`, its producer snapshot and hashed receipt, and keeps them in
the ignored owned raw folder. Parent owns execution and integration.
The source-only preparation receipt SHA256 is
`2de48264d645adf8db0d2cbe211ed370b95c81e0143d8965910b0f31b294d504`;
its producer snapshot matches the frozen source above. Preparation used
Python 3.12.3, NumPy 2.5.2 and Ruff 0.16.6. All preceding traction,
timber-section and group leaves remain frozen.
