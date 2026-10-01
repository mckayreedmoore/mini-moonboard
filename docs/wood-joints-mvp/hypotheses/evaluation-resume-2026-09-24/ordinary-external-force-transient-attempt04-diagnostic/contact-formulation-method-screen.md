# CalculiX 2.23 contact-formulation method screen

## Scope and source pin

This screens documented contact methods after attempt04's complete trace
isolated the generated contact-count gate. It does not change the deck or
select a replacement method. The official source archive pinned in
[`diagnostic-lock.json`](diagnostic-lock.json) has SHA-256
`9c88385c10fb04f5dc6c4e98027a51bebdd8aee3920e05190d6c1dd08357d6e7`.
Source paths below are inside that archive; `src/` abbreviates
`CalculiX/ccx_2.23/src/`. The manual references are from the official
[CalculiX 2.23 PDF](https://www.dhondt.de/ccx_2.23.pdf) and its
[HTML archive](https://www.dhondt.de/ccx_2.23.htm.tar.bz2).

The frozen attempt04 deck uses `TYPE=SURFACE TO SURFACE`, frictionless linear
pressure-overclosure with slope 100000, and implicit `*DYNAMIC,ALPHA=0`
([contact fragment](replay-attempt01/contact-fragment.inc),
[`pilot.inp`](replay-attempt01/pilot.inp)). Its eligible `.cvg` rows pass
residual, displacement, and visco checks but fail the count-derived contact
gate. The results warrant screening methods, not changing that gate.

## Formulations and attempt04 applicability

### `TYPE=MORTAR`

Frictionless unilateral normal contact is supported. Dual-basis Lagrange
multipliers enforce the pressure-overclosure relation weakly. MORTAR does not
use the face-to-face penalty spring-count branch. It is the best documented
static-equilibrium comparison, but it is not allowed in `*DYNAMIC`. A
converged result would not be the attempt04 transient.

### `TYPE=NODE TO SURFACE`

This is penalty contact and remains under contact-element-count stability
checks; for `mortar==0`, any generated count change sets `iflagact`. Dynamic
contact is supported, but the manual advises against this method for
quadratic elements, including C3D10. Its linear law also requires nonzero
tensile traction at large clearance, so it does not exactly preserve strict
unilateral behavior.

### `TYPE=MASSLESS`

This is a separate massless contact explicit-dynamics procedure. It only
applies to explicit dynamic analysis and does not replace attempt04's implicit
dynamics.

CalculiX 2.23 allows only one contact type in an input deck. Thus a full-model
MORTAR comparison would need every contact pair converted together; one MORTAR
pair cannot be inserted among the current face-to-face penalty pairs. The
manual's `*CHANGE CONTACT TYPE` option changes a dynamic step to NODE TO
SURFACE or, for explicit dynamics, MASSLESS. It does not document changing to
MORTAR at a dynamic step. References: manual entries `*CONTACT PAIR`
(node249), `*CHANGE CONTACT TYPE` (node235), and “Face-to-Face Mortar
Contact” (node151); source `src/contactpairs.f:111–118, 141–147`.

NODE TO SURFACE is not a clean count-gate workaround. Source
`src/nonlingeo.c:2352–2356` sets `iflagact` on any generated-element count
change for `mortar==0`, whereas the current face-to-face penalty branch
(`mortar==1`) uses `delcon`. The manual's “Node-to-Face Penalty Contact”
(node143) specifically lists C3D10 among quadratic slave elements for which
convergence may be slower and says node-to-face is generally not recommended
for quadratic elements. Manual `*SURFACE BEHAVIOR` (node357) and
`src/contactpairs.f:193–205` also require a positive large-clearance tension
parameter for the node-to-face linear law. That is not the exact no-tension
unilateral law used by the face-to-face penalty deck. `SMALL SLIDING` applies
only to node-to-face; freezing a pairing does not change its source-level
count gate and is justified only when tangential relative motion is small.

## MORTAR and C3D10

The manual's “Face-to-Face Mortar Contact” (node151) says MORTAR supports hard
or soft contact, with stress-penetration behavior satisfied in a weak sense.
It describes better convergence (usually fewer iterations) than face-to-face
penalty, with greater per-iteration cost. It is available only for `*STATIC`,
is advised for genuine 3D elements, cannot be mixed with penalty contact, and
is unsuitable when slave contact areas are overconstrained by extra MPCs. Do
not add MPCs to slave edge nodes; mounting MPCs belong only at slave corners.
If substantial tangential relative motion is expected, the manual recommends
a small first increment and at least four increments; surface segmentation
and normals are established per increment.

The manual does not name C3D10 as a MORTAR guarantee, but pinned source has a
specific compatible path: `src/getnumberofnodes.f:49–52` identifies a C3D10
element as 10 nodes with 6-node faces; `src/slavintmortar.f:179–194` evaluates
6-node triangular faces with `shape6tri`; and
`src/evalshapefunc.f:19–37` supports the six-node surface interpolation. This
is source evidence of implementation eligibility for a C3D10 face, not a
known-answer validation of this coupon's face ordering, normals, or pairing.
Those remain fixture acceptance checks.

The closest contact-law comparison uses the existing interaction law and
coefficient, with no `*FRICTION` card:

```text
*SURFACE INTERACTION,NAME=WJCP_CURRENT_NUMERICAL_CONTACT
*SURFACE BEHAVIOR,PRESSURE-OVERCLOSURE=LINEAR
100000.
*CONTACT PAIR,INTERACTION=WJCP_CURRENT_NUMERICAL_CONTACT,TYPE=MORTAR
slave-surface,master-surface
```

The source `src/getcontactparams.f:73–79` maps the linear law to
`regmode=1`, `fkninv=1/K`, `p0=0`, and `beta=0`. The manual's `*SURFACE
BEHAVIOR` entry (node357) states that zero overclosure gives zero pressure.
The frictionless normal active/inactive branch is in
`src/stressmortar.c:494–525`; the known-answer must still verify no tensile
contact pressure. This keeps the same nominal unilateral linear normal law
and K=100000, but changes its enforcement from generated penalty springs to
weak dual-basis contact. It is a meaningful alternate discretization, not an
identical rerun.

## What MORTAR convergence checks mean

For penalty methods, `src/nonlingeo.c:2352–2357` derives `iflagact` from the
generated contact spring count. This block has no `mortar==2` count comparison.
MORTAR instead calls `stressmortar` (`src/nonlingeo.c:3101–3121`), which
initializes the flag each iteration (`src/stressmortar.c:121–125`), sets it
when frictionless normal active/inactive status changes
(`src/stressmortar.c:494–525`), and sets it when the normal complementarity
residual exceeds `1e-3` (`src/stressmortar.c:585–592`). The common mechanical
convergence test still requires `iit>1`, acceptable force residual,
`iflagact==0`, and the displacement criterion; it also checks the visco
criterion when enabled (`src/checkconvergence.c:149–162`).

So MORTAR avoids the penalty spring-count criterion by using a different
contact discretization and solver-native active-set/complementarity checks.
The active-set/complementarity flag has an important source caveat:
`src/stressmortar.c:138` initializes `ndiverg` to 14, and line 210 may increase
it to `max(ndiverg,(nhelp/100)+ntie)`. At line 752, source unconditionally
clears `iflagact` when `iit>ndiverg`, regardless of the current active-set or
complementarity result. The shared residual/displacement checks still run,
but native convergence after that threshold cannot establish that the
MORTAR active-set/complementarity checks passed. This source behavior is not
authorized for patching here.

Because `ndiverg` is never below 14, a known-answer coupon must reject any
captured iteration with `iit>14`. That conservative cutoff ensures the
unconditional source override cannot have been reached, even if the coupon's
contact size would raise `ndiverg`. A native convergence message alone is not
the acceptance oracle. Even a coupon accepted at or below 14 iterations
would only validate a static MORTAR result; it would not prove that attempt04's
implicit dynamic contact response is correct or converged.

## MORTAR FRD field limits

The contact fields are diagnostics, not the independent force/compliance
oracle. `src/stressmortar.c:578–580` calls `gap` a weighted dual gap and updates
it using the projected normal displacement. The first stored `cdisp` component
is formed from that dual gap and projected displacement; its sign is set
differently for active and inactive nodes (`src/stressmortar.c:435–467,
500–522`). It is not a direct pointwise geometric clearance.

The multiplier output is also transformed. `cstress` is the Lagrange
multiplier; `stressmortar.c:293–305` applies `Ddtil` to form a transformed
nodal quantity used by the active-set calculation, then lines 713–745 apply
`aut` and project the result onto local slave normals/tangents for the FRD
fields. `src/mortar_prefrd.c:25–60` copies the six `cdisp` values into
temporary slave-node output storage. Treat the resulting gap/stress fields as
diagnostic samples, not direct raw multipliers, integration-point pressure,
or integrated contact force.

The force path is separate: `stressmortar.c:604–619` maps multipliers through
the `Dd`/`Bd` coupling matrices to `cfs`; line 678 passes forces through
`resultsforc`. The coupon's hard oracle must be the independent analytical
total force and series compliance, checked against support reactions and
imposed displacement. FRD fields can help diagnose orientation and active
contact but cannot substitute for that oracle.

## Known-answer acceptance contract before any method change

Before using MORTAR on the full model, require a small, source-pinned static
coupon with one pair of parallel C3D10 triangular faces and the exact
frictionless K=100000 law. Use an axially loaded pair of prismatic members
with free lateral faces and uniform section area `A`, lengths `L1` and `L2`,
and elastic moduli `E1` and `E2`. Prescribe a total axial closure `Delta` in
the linear range. The independent series-compliance answer is
`P=Delta/(L1/(E1*A)+L2/(E2*A)+1/(K*A))`, with contact overclosure
`delta_contact=P/(K*A)`. The fixture must be constructed so this uniform
one-dimensional solution applies; otherwise derive its exact response before
running it. Require:

1. In an open state, verify zero contact pressure and zero contact reaction.
2. In the closed state, verify total force `P`, contact overclosure
   `delta_contact`, displacement partition across both members and contact,
   and support reactions against the closed-form series solution, within a
   predeclared tolerance. Check that no tensile contact traction is present.
3. Unload to positive clearance; verify return to the open state without
   residual contact traction. Check that ordinary residual/displacement
   convergence predicates pass and that every captured iteration has
   `iit<=14`. Do not use a cleared `iflagact` after iteration 14 as proof of
   active-set or complementarity convergence.
4. Independently audit the C3D10 face labels, outward normals, master/slave
   order, and reaction balance. Record FRD contact fields at open, closed,
   and released states as diagnostics only; the analytical force and series
   compliance remain the hard oracle.

Reject the method comparison if it needs a changed K, nonzero friction,
artificial contact restraint, or relaxed equilibrium/active-set tolerance.
Only after this coupon passes should the parent decide whether a full static
MORTAR equilibrium comparison is useful. It cannot be used to infer or replace
an attempt04 dynamic transient, and no transient history should be guessed
from it.

## Primary references

- Pinned source archive and member hashes:
  [`diagnostic-lock.json`](diagnostic-lock.json); official
  [`ccx_2.23.src.tar.bz2`](https://www.dhondt.de/ccx_2.23.src.tar.bz2).
- Manual entries: `*CONTACT PAIR` (node249), `*CHANGE CONTACT TYPE`
  (node235), `*SURFACE BEHAVIOR` (node357), “Node-to-Face Penalty Contact”
  (node143), “Face-to-Face Mortar Contact” (node151), and contact convergence
  criteria in the official [2.23 PDF](https://www.dhondt.de/ccx_2.23.pdf).
- Pinned source methods: `contactpairs.f:111–147, 193–205`,
  `getnumberofnodes.f:49–52`, `slavintmortar.f:179–194`,
  `evalshapefunc.f:19–37`, `getcontactparams.f:73–79`,
  `nonlingeo.c:2352–2357, 3101–3121`, `stressmortar.c:121–125, 494–525,
  138, 210, 293–305, 435–467, 500–525, 578–580, 585–592, 604–619, 678,
  713–752`, `mortar_prefrd.c:25–60`, and
  `checkconvergence.c:149–162`.
