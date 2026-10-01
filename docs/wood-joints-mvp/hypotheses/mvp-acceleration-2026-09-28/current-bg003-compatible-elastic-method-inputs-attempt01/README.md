# BG003 compatible elastic method inputs — attempt01

## Finding

A compatible elastic beam-on-foundation calculation is a viable *conditional
per-bolt screening formulation* if each wood receiver is modeled as an
independent rigid body with free transverse translation and rotation, and its
case-specific source wrench is applied to that body. One continuous elastic
beam then couples the three receivers through distributed bearing springs.
For positive bilateral spring stiffness and positive steel bending rigidity,
the energy system is unique up to common rigid transverse translation and
slope. The source wrench sets are self-equilibrated, so those four gauge modes
do no external work.

This packet stops before solving that system. The pinned cases do not provide
an elastic modulus for an actual bolt, a bearing stiffness law for these
members, or the physical contact state. Published values below are useful
non-adopted screening inputs, not BG003 properties. The construction of one
statically admissible bearing profile in the prior profile feasibility packet
is a separate idealization; it is not converted into an elastic law here.

## Source-bound BG003 input

[`inputs.json`](inputs.json) contains all seven increments from each of the
three authenticated numerical corner-demand reports: `a12-rear`, `a1-rear`,
and `k12-rear`. Each increment retains both BG003 bolt IDs, all three physical
member force/moment wrenches, the exact source tie and lateral-plane points and
vectors, and the report’s response gates. The producer checks the report
hashes, case/status identifiers, seven-increment count, all response gates,
five-body balances, and per-bolt wrench sums before writing the register. It
also reconstructs each member wrench from the three exact source action
points/vectors and checks the derived interval midpoint and wrench shift against
the source tie endpoints.
No response force is transferred between cases.

The source geometry is a modeled +X axis with diameter 6.35 mm and proposed
head-to-nut order `knee_outer_left_spine` (38.1 mm), `base_side_left` (88.9 mm),
and `knee_outer_left_inner_frame_block` (88.9 mm). Their intervals from the
modeled underhead are [1.651, 39.751], [39.751, 128.651], and [128.651,
217.551] mm. For each bolt, the report’s spine-to-middle interface point and
the outer-seat tie endpoints pin the modeled interval origin and both ends;
the derived interval midpoints and translated midpoint wrenches are included
in `inputs.json`.

The source proposes outer-member grain along +Z and middle-member grain 40°
from +Z. It records a solid DF-L `G=0.50` scenario, 0.25-in axis, `Fyb=45 ksi`,
and zero modeled gaps. These are conditional scenarios. Physical head-to-nut
order, received-stock grain, active contact law, fit, and bearing stiffness
are not verified. No member density/moisture or steel elastic modulus is
pinned. `G` and NDS bearing `Fe` do not supply the missing elastic foundation
modulus.

## Elastic formulation and load mapping

Let `s` follow the bolt axis, `w(s)=(w_y,w_z)` be bolt transverse displacement,
and `u_j(s)` be receiver `j`’s transverse displacement. A conventional fixed
foundation linearization is

```text
E_s I w''''(s) + K_line,j [w(s) - u_j(s)] = p_beam(s)
```

Here `E_s I` has units N·mm², `K_line` is a 2×2 transverse line stiffness in
N/mm², and `p_beam` is N/mm. The beam section is circular, so its elastic
second moment is `I = π d⁴/64` and both transverse bending axes have the same
`E_s I`. If an embedment stress-slip tangent `K_f` is expressed in N/mm³,
`K_line = d K_f`; the member-level spring relation is
`dF = f_h(u) d ds`, with `f_h` in N/mm² and `d, ds` in mm.

For a per-bolt free-receiver proxy, give each of the three receivers independent
transverse translation `(u_y,u_z)` and bending rotation `(θ_y,θ_z)` at its
interval midpoint. Its rigid transverse field is
`u_j(s)=u_j(mid)+θ_j × ((s-s_mid)e_X)`. Use the source member wrench at that
midpoint for work `F_j·u_j(mid) + M_j·θ_j`. `inputs.json` preserves each exact
source wrench at the bolt-axis datum and derives its midpoint reference by
`M_mid = M_axis − (r_mid−r_axis) × F`. Only the transverse force and bending
moment components enter this lateral screen. Axial tie force and torsion are
separate. Apply the member wrenches to receiver bodies; do **not** also apply
the source interface actions as beam loads or impose them as spring reactions.
The source interface actions remain in the register for point/vector audit.

The corresponding energy is

```text
Π = 1/2 ∫ E_s I |w''|² ds
  + 1/2 Σ_j ∫ (w-u_j)ᵀ K_line,j (w-u_j) ds
  − Σ_j [F_j·u_j(mid) + M_j(mid)·θ_j]
```

With positive bilateral foundation stiffness on all three modeled intervals,
the only zero-energy modes are common Y/Z translations and common Y/Z slopes.
Pin `w(s₀)=0` and `w'(s₀)=0` only to remove that gauge, and verify their
reactions are zero. Across all 42 bolt/increment samples in these three cases,
the largest source sum residual is `2.42e−14 N` in force and `1.63e−12 N·mm`
in moment. This verifies load compatibility with the gauge, not the computed
elastic response.

This is an isolated single-bolt proxy. The two bolts share timber in the real
joint, so their independent rigid receivers do not capture shared wood
deformation, block/spine flexibility, group load redistribution, or any
joint-level compatibility. A fixed-foundation BOEF remains another option,
but it needs prescribed receiver motion fields rather than this free-receiver
load mapping.

## Published spring inputs and biaxial limit

Gikonyo et al.’s primary beam-on-foundation study models a deformable
one-dimensional fastener beam with receiver-specific orthogonal embedment
springs. Its Eq. (3) defines a nonlinear embedment stress-slip relation, Eq.
(4c-d) gives density-based elastic foundation-modulus regressions, and Eq. (5)
converts stress to spring force using `F=f_h d Δt`. The regressions are:

```text
k_f,el,parallel = 0.1374 ρ − 12.9   N/mm³
k_f,el,perpendicular = 0.0922 ρ − 18.20   N/mm³
```

For the illustrative literature density span 350–550 kg/m³, these evaluate to
35.19–62.67 N/mm³ parallel and 14.07–32.51 N/mm³ perpendicular. The study says
its broader parameter-study database mainly covers solid timber and glulam;
that does not identify the density or load-slip curve of these BG003 members.
Its separate validation subset reports 97.8 N/mm³ parallel and 49.0 N/mm³
perpendicular at 462 kg/m³ CLT; the perpendicular value was inferred from a
general embedment ratio rather than directly measured on that subset. The
paper also models a specimen-specific 0.28 mm initial slip at 10% of the
parallel elastic modulus. None of these values describes BG003 contact or
clearance.

The article explicitly limits its validation/loading discussion to in-plane
directions parallel or perpendicular to the deck-layer grain. It does not
validate the BG003 middle member’s proposed 40° grain frame or simultaneous
unequal Y/Z actions. A rotated two-axis matrix such as
`K_global = R diag(k_parallel,k_perpendicular) Rᵀ` creates cross-axis terms and
is a candidate constitutive assumption only. Circular steel’s equal `EI` does
not remove those wood-foundation terms. Solve both transverse components
together unless the justified foundation matrix is diagonal in the working
axes. Linear superposition also requires the same fixed bilateral contact
state; clearance, seating, compression-only bearing, or nonlinear
embedment changes that state and breaks ordinary component superposition.

The supporting primary sources are:

- Gikonyo, J.W., Schweigler, M., and Bader, T.K. (2024), [“Beam-on-foundation
  modelling of dowel-type single fastener connections in cross laminated
  timber”](https://www.diva-portal.org/smash/get/diva2%3A1829333/FULLTEXT02.pdf),
  *Engineering Structures* 303, 117519, §2.1 and Eqs. (3)–(5). Its methods
  describe the beam and orthogonal springs, material-input units, and its
  parallel/perpendicular loading scope.
- Reynolds, T., Harris, R., and Chang, W.-S. (2013), [“An analytical model for
  embedment stiffness of a dowel in timber under cyclic load”](https://doi.org/10.1007/s00107-013-0716-1),
  *European Journal of Wood and Wood Products* 71, 609–622. This primary study
  distinguishes dynamic foundation stiffness from static initial stiffness
  and limits its model to one-sided vibration about nonzero mean load; its
  dynamic stiffness is not substituted for the BG003 static input.

## Small known-answer fixture

Before a finite three-receiver calculation, validate the linear vector beam
operator against this synthetic infinite-beam point-load solution. Let
`EI=1 N·mm²`, `K_line = [[2.5,1.5],[1.5,2.5]] N/mm²`, and apply
`P=(1,0) N` at `s=0`. The foundation eigenvalues are 4 and 1 N/mm², rotated
45° from the global axes. For each eigenvalue `k`,

```text
β = (k/(4 EI))^(1/4)
g_k(s) = exp(−β|s|)[cos(β|s|)+sin(β|s|)]/(8 EI β³)
```

Project `P` into the eigenbasis, multiply by `g_k(0)`, and rotate back. The
known center displacement is `(0.2392766953, −0.1142766953) mm`. The nonzero
cross-axis displacement catches independent scalar Y/Z implementations that
drop the off-diagonal foundation terms. All values are mathematical fixture
devices, not bolt or wood properties.

## Limits and reproduction

The proxy is not a strength or acceptance check. Its lateral formulation does
not include source axial tie tension, installation preload, actual washer/end
seat compliance, or true receiver contact and clearance. Current zero gaps
and receiver grain directions are modeled proposals. A compression-only
version would require a case-specific active-contact state; the linear
bilateral fixture does not provide one. No steel-yield, wood-bearing,
splitting, group, or design-resistance criterion is evaluated.

The source-pinned packet and its checks reproduce with:

```bash
python3 docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/current-bg003-compatible-elastic-method-inputs-attempt01/prepare_inputs.py
```

The script only verifies and serializes source inputs; it does not solve the
elastic model. `SHA256SUMS` pins the new packet and its producer.
