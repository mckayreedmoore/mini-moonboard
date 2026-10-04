# Surrounding-frame member replacement and assembly energy

The [adapter](joint-frame-member-replacement.py) answers a specific method
question: can a drilled or cracked timber replace the source timber's elastic
contribution while the existing frame redistributes its connection forces?
It reuses the [port reduction](joint-frame-port-reduction.py) and
[compatible-frame solver](joint-frame-compatibility-completion.py).
It supplies the replacement and energy arithmetic, not a new finite-element
kernel, a strength result or a fabrication release.

The starting authority is `frame-attempt08` with twelve accepted fields and
fourteen dispositions, joined to `joint-frame-action-reconciliation/attempt03`.
The reviewed 104 structural axes, 66 Hillman axes, physical datums and
1000 mm rotation scale remain fixed. The source timber stiffness is the
original gross, filled-bore native solid. A new drilled/cracked operator is a
separate analytical branch and cannot inherit that body's old elastic field.

## Complete body replacement

`source_body` extracts the selected body's original native `K`, complete
current-port `B`, twelve external-load columns `F`, rigid basis `R`, labels,
coordinates and source datum. The current port ordering is 1,592 kept old
ports followed by 1,600 continuous-shaft/contact ports. `source_context`
reads the original matrix once for callers selecting several bodies.
`source-export` saves one selected body for later remeshing without factoring
it again; `load_source_body` reads that saved packet.

The body operators are

```text
H_body = B K_plus B.T
e_body = B K_plus F
L_body = F.T K_plus F
D_body = B R
W_body = R.T F
H_revised = H_frame - H_old_body + H_new_body
e_revised = e_frame - e_old_body + e_new_body
L_selected_revised = L_selected - L_old_body + L_new_body
```

Every incident port and cross-port term belongs to the body contribution.
Appending new compliance to the old body would double count it.
`replacement` requires matching old/new `D_body` and `W_body` within
1e-8 and preserves the full frame's `D` and `W` objects. The remeshed rigid
basis must use the **original source datum**, rather than a changed mesh
centroid. Retain the original external gravity/live identity and source
mass allowance; drilling does not silently redefine gravity in this study.

Unit port columns are generally unbalanced. `reduce_body` projects their
rigid span only to define the elastic quotient, factors the original bordered
`K/R` system and reuses the existing audited quotient/refinement helpers.
It retains raw `B/F` and their physical `D/W`. Projection does not balance
an actual physical load. Final equilibrium separately checks every body,
shaft, washer and floor law.

`reduce_body_from_solutions(B,F,R,U_B,U_F,audit,active_ports=None,K=None)`
accepts the already audited localized solid recovery. It checks gauge removal,
reciprocal `H/L`, and agreement between `B U_F` and `U_B.T F`.
Supplying `K` adds a native virtual-work witness. An accepted caller audit
against the original stiffness is mandatory; this adapter does not turn an
unaudited displacement array into a qualified operator.

## Assembly potential

For unchanged external coefficients `c`, the elastic displacement is
`u = R a + K_plus (F c - B.T f)`. The adapter retains the full selected
body-load matrix, including gravity/live cross terms:

```text
chi = 0.5 c.T L c
U_elastic = 0.5 f.T H f - f.T e c + chi
external_work = a.T W c + 2 chi - f.T e c
Pi = U_elastic + U_connector - external_work
   = 0.5 f.T H f + U_connector - a.T W c - chi
G = (Pi_initial - Pi_final) / added_sound_area_mm2
```

`H` includes full-frame timber and the four existing continuous shafts.
`U_connector` uses the actual source laws: linear spring energy,
compression/tension-only positive-part energy and
`0.5 k max(norm(q_pair)-gap,0)^2` for circular bore clearance. Held no-slip
floor tangents have zero stored energy. The linear clearance term reappears
in the independently recovered complementary energy. At equilibrium,
`Pi = -chi - complementary_energy`; a solver objective alone omits `chi`.

Only replaced bodies' `L` matrices need new reductions for a fracture
difference. Unchanged body-load constants cancel at the same external load.
For this scope, the reported elastic energy omits `chi_unchanged`, external
work omits `2 chi_unchanged`, and recorded potential equals true potential
plus `chi_unchanged`. Each output labels these unknown offsets and carries
an unchanged-constant token. It is **total assembly potential up to that
shared constant**, not an absolute total-energy claim.
`energy_release` requires matching constant scope/token, coefficients,
external wrench and connector-law hashes. It does not equate the internally
redistributed interface forces.

## Wider washer branch and saved frame fields

`apply_joint_update(frame, profile_packet)` authenticates the
[working washer profile](washer-working-profile-completion.py), including its
source closure. It converts original rows 1850, 1851, 1886 and 1887 through
the authenticated non-floor and kept-row maps. Those four tension-only ties
cover eight top-rail seats. Their conditional orthotropic wood-column/steel
series stiffness changes from 3751.291479490876 to
5108.952204674765 N/mm for the 25.4 mm outer diameter, 8.3058 mm inner
diameter and 2.5 mm thickness profile. Directions, datums, counts and other
spring laws remain source-bound; no preload or friction benefit is added.
The plate/contact K20/K10000 hypotheses remain separate from this column law.
The converter binds the exact `preparation01` profile receipt and reuses that
producer's absolute-source-aware authentication. Its three existing frozen
`/tmp` reference sources retain their absolute paths and original hashes;
they are not copied or treated as repository files. The source-only guard
authenticates the profile closure and changes only current ports 1530, 1531,
1566 and 1567. The original frame binder remains unchanged.

`profile-sweep` computes fresh requested equilibria using the original
finite floor-mask search and audits the revised stiffnesses. It exports
five arrays per accepted state: force, relative motion, scaled rigid pose,
continuous-shaft pose and bearing mask. It preserves the established
comparison/receipt schema and exact accepted/STOP disposition rules, with
the applied `washer_joint_update` embedded in `inputs.json`.
Stopped states receive no force field. Original floor stops cannot be
relabelled after a stiffness change. The snapshot's pure floor-summary wrapper
delegates to the existing helper so the unchanged action exporter can validate
its finite stop traces.

## Checks, preparation and method limits

The runnable `coupon` passes analytic load sharing, source remove/reinsert,
crack-energy sign/magnitude, open/closed unilateral contact, circular clearance,
unbalanced unit-column quotient and body-load cross-term checks. Sharing
changes from 7.2/4.8 N to 5.142857/6.857143 N; potentials change from
−0.864 to −1.234285714 N·mm, giving G = 0.185142857 N/mm over 2 mm².
The direct nonzero-body-load reconstruction gives U = 13.375 N·mm,
external work = 29.64 N·mm and Pi = −14.82 N·mm. Primal/complementary
identity error is 1.78e-15 N·mm; an unchanged rest-body constant cancels.
Runtime is Python 3.12.3, NumPy 2.5.2, SciPy 1.18.1 and Clarabel 0.11.1.
The source formulation and pinned solver references remain in the
[compatible-frame method](joint-frame-compatibility-completion.md).

The parent-executed
[left source check](rawlocal/joint-frame-member-replacement/source-check01/check.json)
completed in 4.353 s on the 60-DOF original cleat. Its native projected residual
is 1.02e-15 and virtual-work error 1.73e-18. Removing/reinserting the recovered
body changes H by at most 1.36e-20 and e by 8.47e-22; D/W are exact and all
twelve recorded potentials are unchanged. The roundtrip is an algebraic
preservation check, not an independent decomposition of the complete global
H/e. Native K/B/F provenance, quotient and virtual-work checks establish the
recovered old contribution's method basis. Its frozen initial producer is
preserved in `preparation01/producer.py.snapshot`; later consumers must resolve
that recorded hash rather than substitute revised live code.

The parent freezes `joint_frame_member_replacement_request/v1` before
execution. `source_pin_paths()` supplies the exact required files: original
native stiffness/DOFs and model, K parser, quotient/refinement/known answer,
source operators/projection/rows/coordinates, completed preparation and wood
reduction, frame08 fields/receipt/inputs/comparison, action03 identity records,
both reused adapters, this producer and `uv.lock`.
Include `member_ids`, reviewed counts and unchanged-geometry flags. Any new
mesh, crack, material, footprint or external-load mapping is frozen separately
by the native study producer.

```bash
uv run python docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/upper-corner-screw-layout/joint-frame-member-replacement.py coupon
uv run python docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/upper-corner-screw-layout/joint-frame-member-replacement.py prepare --request REQUEST --expected-sha256 SHA --output FRESH_PREPARATION
uv run python docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/upper-corner-screw-layout/joint-frame-member-replacement.py source-check --preparation FROZEN_PREPARATION --member center_post_cleat_left --output FRESH_CHECK
uv run python docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/upper-corner-screw-layout/joint-frame-member-replacement.py source-export --source-check COMPLETED_CHECK --member center_post_cleat_left --output FRESH_BODY_EXPORT
uv run python docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/upper-corner-screw-layout/joint-frame-member-replacement.py profile-sweep --profile-packet FROZEN_PROFILE --output FRESH_FRAME_BRANCH
```

Fresh outputs belong under ignored `rawlocal/joint-frame-member-replacement`.
The parent serializes source-matrix reads, body reductions and frame/native
equilibria. Source export repeats no factorization; it keeps the previous
old-body operator binding. No all-50 body-load solve is commissioned.

This method remains first-order, elastic and conditional on the source wood,
panel, steel, screw, contact and no-slip assumptions. A free-body quotient
requires exactly six independent rigid modes; an additional crack mechanism
or detached component needs a separately justified method. Mapped contact
footprints, seam-bridging force clouds, mesh/stress convergence, crack resistance
and active-contact stability remain separate questions. A converged operator
or equilibrium is not complete joint resistance. All physical release and
complete acceptance flags remain false.
