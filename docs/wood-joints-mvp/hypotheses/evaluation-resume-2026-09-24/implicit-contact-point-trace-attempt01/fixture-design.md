# Implicit contact point trace fixture design

This preparation proposes a small source-instrumentation known-answer fixture
for the pinned CalculiX 2.23 implicit linear penalty-contact path. It separates
the generator MAP's candidate gaps/kept set from the final corrected TRIAL's
active spring state. It is a trace/law check only. It does not establish a joint
method, equilibrium,
inertial reactions, external work, or physical transient behavior. No native
build or solve has been run for this packet.

The input at [implicit_point_trace.inp](input/implicit_point_trace.inp) reuses
the 2 mm two-block C3D10 face mesh and contact pair from
`contact-energy-known-answer-attempt01/input/penalty_c3d10.inp` (SHA-256
`40cdf59c7184f828dac9275ac10a3c04be10e597cf769ec1af332293ee8cb7dc`). Its
upper slave is elements 1 and 2, S1; its lower master is elements 11 and 12,
S3. The matching flat faces lie at z=0 and have 4 mm² area. The existing
geometry review records the upper outward normal as -z and lower/master outward
normal as +z. The copied body mesh and those face identities are unchanged.

All upper and lower contact-body translational degrees of freedom are set by
direct Dirichlet boundary conditions. The lower body stays fixed; the upper
body's U3 follows a single amplitude with knots at 0, 1, 2, 3, 4, and 5 s:
0, +0.001, 0, -0.001, 0, +0.001 mm. The step uses implicit `*DYNAMIC,DIRECT`,
0.1 s increments, and a 5 s duration. This gives opening, touch, compression,
touch, and reopening endpoints at exact increment times, without prescribed
MPCs or `*EQUATION` cards. Positive density `1e-9` tonne/mm³ is assigned to the
contact bodies for a well-formed dynamic model; their accelerations and
reactions are deliberately outside the oracle.

Because the contact-body DOFs are all prescribed, the input also has one
disconnected, unloaded C3D4 elastic tetrahedron. Its first three nodes are
fixed in all directions and its fourth node is fixed in U1/U2 but free in U3.
This one zero-response elastic equation prevents a zero-equation model; it is
only a fixture witness, not part of the contact result or an attempt to model
the inertia of either contact body. The tetrahedron has positive orientation
from its listed coordinates and connectivity.

The contact interaction is `TYPE=SURFACE TO SURFACE`, linear pressure versus
overclosure with slope `K=100000 N/mm³`, and no friction card. Pinned source
`contactpairs.f` maps this type to mortar mode 1; `dynamics.f` rejects only
massless mode -1 for implicit dynamics. In `gencontelem_f2f.f` the dynamic
active-set branch removes a positive-gap point from the kept spring set.
`springforc_f2f.f` is the applicable mode-1 force path: it computes signed
clearance, linear pressure, spring energy and the point `fnl` vector. The
mortar-only `treatmasterface_mortar.f` path is not used as the force/gap oracle
for this mode-1 pair. These are the exact source targets, not independent
evidence that every production contact problem behaves correctly.

For the event endpoints, the geometric signed gap is
`g = z_upper_slave - z_lower_master`, so positive means open and negative means
overlap. At the compressed endpoint, `g=-0.001 mm` gives pressure
`K*0.001=100 N/mm²`, a 400 N scalar resultant magnitude over 4 mm², and stored
spring energy `0.5*K*4*0.001²=0.2 N mm`. `springforc_f2f.f` computes
`stiff(1)=-A*K*g`, `cstr(4)=stiff(1)/A`, `senergy=-stiff(1)*g/2`, and
`fnl=-stiff(1)*xn`. The `fnl` value is the native spring/assembled internal
resisting-force convention. It is not automatically the physical contact
traction on the slave; the physical traction sign is opposite. The diagnostic
patch emits no `fnl` or `CFN` vector. It binds `CCXPT_TRIAL.corrected_gap` to
`stx(1)=cstr(1)` and `CCXPT_TRIAL.signed_pressure` to `stx(4)=cstr(4)`. The
fixture checks that signed pressure and derives a normal resultant as
`p*A*n_master` from emitted pressure, measured area and master normal. That
vector is not an independently observed force channel. It must not be reported
as `fnl` or `CFN`. Require `energy_enabled=1` and `kscale=1` before comparing
emitted spring energy with `0.5*K*A*g^2/kscale`. The exact open and touch
endpoints have no accepted active spring or energy after a filtering MAP. The
values and proposed pre-run tolerances are in [expected.json](expected.json).

The current patch records generator MAP and final corrected TRIAL only; it has
no retained pre-solve phase. Require at least one positive-gap active TRIAL and
check it using the actual logged row gaps and summed spring area, then report
its observed time and area. A later MAP may filter the old set, so that tensile
TRIAL and a subsequent empty set are separate observations. With the proposed
0.1 s schedule, t=4.1 s is a candidate open trial after the t=4 touch, but an
active old set at exactly that point has not been established. If a complete
4 mm² set is observed there at `g=+0.0001 mm`, the derived values would be
`p=-10 N/mm²`, derived resultant `(0,0,-40) N` from `p*A*n_master` with
`n_master=+z`, and `E=0.002 N mm`; these are conditional arithmetic, not a
required time or area. For any observed active set with measured area `A_set`
and uniform positive gap `g`, check `p=-K*g/kscale`, derive the normal
resultant as `p*A_set*n_master`, and check energy `0.5*K*A_set*g²/kscale`, with
`kscale=1` required by this contract. The derived vector is not observed `fnl`
or `CFN`. For each active TRIAL identity, also compare the summed derived
resultant with the vector sum from the per-row pressure law (Euclidean error at
most 0.004 N) and summed emitted energy with summed analytical energy (error at
most 2e-6 N mm). At the accepted reopened endpoint t=5 s, require final
convergence contact count zero and no active TRIAL rows after the filtering
MAP; this supports the zero accepted contact force and energy interpretation.
Classify a corrected trial as a resolved positive-gap observation only when
`corrected_gap > 1e-9 mm` (the declared gap tolerance), and require its signed
pressure to be negative. The source filter remains exact: any MAP
`raw_signed_gap > 0` must have `native_isol=0`. This input is implicit dynamic,
whose `nmethod` is 4; `nmethod=2` is the separate frequency procedure.

For event gaps, compare against the prescribed flat-face displacement only for
the final converged generator MAP at iteration >=2, joined to the event time.
Earlier MAP records are intermediate geometry and must not be required to equal
the final boundary position. If the trace cannot establish that join, limit
the generator check to finite internally uniform signed gaps and report the
limitation. Keep candidate identities/counts separate from kept-set identities
and the final corrected TRIAL rows; report observed counts rather than imposing
an unverified point-count gate. The verifier binds each trace identity to
accepted `.sta`/FRD state records. It checks every TRIAL's
`relative_time*5 s` against both `.sta` time and FRD `100CL` time, then compares
the corrected gap to the prescribed amplitude at that bound time. Increment
number alone does not establish absolute time. Event endpoints are increments
10, 20, 30, 40 and 50. Require all 50 accepted states, complete finite
displacement output at all 58 fixture nodes, and CVG/TRIAL identity-count
coverage. A zero-contact CVG identity correctly has no TRIAL rows; positive
contact counts must have exactly that many. `*CONTACT PRINT` CELS is secondary
accepted-energy output only; it does not qualify CFN, RF, inertia, or
work-energy semantics.

The pinned source archive is
`ordinary-external-force-transient-attempt04-diagnostic/build-attempt02/source.tar.bz2`,
SHA-256
`9c88385c10fb04f5dc6c4e98027a51bebdd8aee3920e05190d6c1dd08357d6e7`. Relevant
source line anchors in that archive are:

- `contactpairs.f:111-118`: contact type to internal mode mapping.
- `dynamics.f:134-139`: implicit dynamics rejects `mortar=-1` massless
  contact; the chosen mode 1 is not that path.
- `gencontelem_f2f.f:550-560`: dynamic positive-gap active-set filter;
  `gencontelem_f2f.f:672-715`: spring-element generation after filtering.
- `springforc_f2f.f:155-164`: signed normal clearance and `cstr(1)`.
- `springforc_f2f.f:191-200`: linear spring stiffness and stored energy.
- `springforc_f2f.f:248-253`: native internal spring vector `fnl` and signed
  pressure `cstr(4)`; this does not establish CFN or physical traction sign.
- `resultsmech.f:430-436` passes `stx(1,1,i)` as `springforc_f2f`'s `cstr`
  output array. The patch therefore emits `cstr(1)` as corrected gap and
  `cstr(4)` as signed pressure. It emits no `fnl` components. Derive the normal
  resultant from pressure, area and master normal, and label it accordingly.
- `mastruct.c:789-790`: warning when the model has no degrees of freedom, which
  motivates the separate free elastic witness.

The archive's member hashes are repeated in `expected.json`. The local pinned
2.23 manual is `fea/generated/ccx_2.23.pdf`, SHA-256
`a0bf3fc03f374912ff2bf28da3f7dfb6a61428dd7f41b281a2e7e1fdb318f330`; the
`*DYNAMIC` reference describes direct integration, fixed increments for
`DIRECT`, and time/amplitude interpolation. The current input hash is
`e9d0ec2252201fdaa249b5e884c9290a128fb31c135afff6e08c566cb504c61b`.

Parent review remains required before any build or run. The separately frozen
static coupon known-answer attempt remains the unchanged-output numerical
regression; this fixture adds only the dynamic gap/filter/stale-set observation.
