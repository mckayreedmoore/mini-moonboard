# CalculiX 2.23 contact-count interpretation

## Scope and pinned sources

This is a read-only interpretation of the contact-count gate and the attempt03
contact-element trace. It uses the official source archive pinned in
[`diagnostic-lock.json`](diagnostic-lock.json), SHA-256
`9c88385c10fb04f5dc6c4e98027a51bebdd8aee3920e05190d6c1dd08357d6e7`. The
archive does contain `CalculiX/ccx_2.23/src/gencontelem_f2f.f`; the earlier
attempt03 results note that called this source unavailable is superseded on
that point. This source check does not replace the coupon or independently
validate every full-model surface mapping.

The frozen contact fragment uses `TYPE=SURFACE TO SURFACE`, linear
pressure-overclosure, and no `*FRICTION`. The pinned source dispatches this
contact type to face-to-face penalty generation (`src/contact.c:89–96`; the
keyword mapping is in `src/contactpairs.f:111–118`). References below use
paths inside the archive; `src/` abbreviates `CalculiX/ccx_2.23/src/`. The
[official CalculiX 2.23 manual PDF](https://www.dhondt.de/ccx_2.23.pdf) and [HTML manual
archive](https://www.dhondt.de/ccx_2.23.htm.tar.bz2) provide the corresponding
contact and convergence descriptions.

## What the convergence count measures

For face-to-face penalty contact, `src/nonlingeo.c:2352–2357` compares the current
generated contact spring element count (`ne-ne0`) with the preceding count
(`neold-ne0`). For `mortar==1`, it sets `iflagact` if the new count lies
strictly outside the old count multiplied by `1±delcon`. `src/ini_cal.c:321`
sets the default `delcon` to `0.001`; the manual's convergence section
describes this as the maximum relative change in contact element count.
`src/checkconvergence.c:149–162` requires `iit>1`, the residual gate,
`iflagact==0`, and the remaining mechanical criteria. `src/writecvg.f:80–83`
records `ne-ne0` on each convergence row. That field is a generated-element
count, not force, pressure, or a count of unique physical interfaces.

The manual's face-to-face penalty description explains why the count can be
large and discrete. The overlapping portions of the slave and master faces
are polygons, triangulated for integration; each triangle uses a seven-point
scheme. A slave face may therefore contribute many integration points. The
spring is associated with a slave-face integration point and a master face,
not one spring per physical joint or one spring per face pair (manual,
“Face-to-Face Penalty Contact,” general considerations; source
`src/gencontelem_f2f.f:282–320, 672–716`).

At the start of an increment,
`src/gencontelem_f2f.f:156–180, 284–320, 336–427`
searches for the master face and records the integration-point mapping. On
later iterations it reuses that mapping (`:328–333, 420–427`), updates the
deformed slave/master geometry (`:245–279, 491–552`), and computes signed
clearance along the stored normal (`:530–552`). For this deck's ordinary
linear penalty law, the dynamic branch removes the candidate when
`clear>0` (`:554–561`); the standard contact-generation path otherwise
retains it and creates an `ESPRNGC` spring (`:617–685`). Exact zero is not
filtered by the strict positive-clearance check, though zero penetration does
not establish positive contact pressure. TIED contact has separate handling;
it is not the law in this deck.

Thus an iteration-to-iteration count change is a change in the set of
generated integration-point springs under the clearance test. It is not
itself a measurement of compressive force. Small local movement can change a
point's classification when its signed clearance is near zero; a sign flip
from floating-point rounding is possible because this branch compares
directly with zero. The trace does not record per-point clearance margins, so
it cannot establish that rounding caused the observed changes.

The matching and overlap integration points are frozen within an increment.
Consequently, within-increment turnover is not evidence that the solver
re-triangulated or re-matched the faces on every iteration. The integration
points can gain or lose generated springs as their clearances change. A new
increment rebuilds the matching and integration-point mapping, so a
transition across increments has that additional possibility. The selected
global motion monitors do not bound relative motion or gap at every interface
integration point.

## What the existing trace establishes

The attempt03 result reports 35 mapped ordered contact pairs and, across 38
CVG-aligned transitions, cumulative face-pair signature turnover of 494,338
for bolt-seat families and 96,928 for finite wood-to-wood interfaces; open
bore families stayed at zero generated elements. With the source now
available, the `src/gencontelem_f2f.f:723–768` CEL writer confirms that these
visualization records are emitted from generated contact springs and encode
their master/slave face nodes. That strengthens the interpretation as
generated spring topology mapped to pair families. It does not turn CEL
membership into a pressure, force, gap, or slip measurement, nor does it
identify which changed points carried meaningful load.

The attempt03 `pilot.inp` requests `CDIS`, `CSTR`, `CELS`, `CNUM`, and
per-pair `CF`, `CFN`, and `CFS`. `pilot.dat` contains these contact outputs
only at accepted increment 1; it has no contact-print state for the
unaccepted increment 2 iterations. The trial `.cel` stream stores generated
spring visualization, `.cvg` stores the total generated count and convergence
ratios, and the last-iteration FRD contains displacements only. The manual's
`*CONTACT PRINT` and `*CONTACT FILE` variables can provide additional evidence
at their requested output states:

- `CSTR` gives normal pressure and tangential stresses; `CFN`/`CFS` give
  aggregate normal/shear force for a selected face-to-face pair; `CELS` gives
  contact spring energy. These distinguish force-bearing contact at an
  output state, but do not localize every transition by themselves.
- `CDIS` reports relative contact displacement at active slave integration
  points. Its normal `COPEN` component records penetration only: positive
  clearance is stored as zero. It therefore cannot measure the magnitude of
  an open gap. Its tangential components are calculated only when friction
  is defined; this frozen frictionless deck cannot use them to diagnose
  stick/slip.
- `CNUM` is a scalar total contact-element count, not a pair-local state.
  The manual documents `LAST ITERATIONS` for displacement snapshots and
  `CONTACT ELEMENTS` for the CEL stream; it does not describe those options
  as per-iteration contact-stress output.

The smallest discriminating observation for a replay of these unaccepted
iterations is a source-level trace for each changed integration point:
step/increment/attempt/iteration, contact-pair key, slave face and integration
point key, cached master face, full-precision signed `clear`, and whether the
generator retained/created its spring. This would show whether the switches
occur at near-zero clearance or at a non-negligible positive gap. To claim
contact force or slip, also capture pressure/traction or relative tangential motion at the
same points and iterations; the existing CEL/CVG/FRD streams cannot supply
that. Do not add friction just to obtain a slip field, since that changes the
frozen contact law.

## Documented controls and applicability

The manual documents `delcon` as a user-adjustable convergence threshold,
not as a geometric clearance tolerance. Raising it would change the
acceptance gate; the observed CEL turnover alone does not justify that
change. The manual also states that `SMALL SLIDING` is not an option for
`TYPE=SURFACE TO SURFACE`; face matching is held within an increment by this
formulation. Its generic troubleshooting suggestion to try small sliding
therefore does not apply here.

The face-to-face convergence discussion documents increment/stiffness
reduction in the divergence or slow-convergence paths. The pinned
`src/checkconvergence.c:546–563` only permits its major divergence check for this
contact formulation when the force residual is extreme or the contact count
is stable. Those recovery paths are not a documented way to ignore a
count-change gate. The manual says smaller increments may be needed for
large deformation because the face match is frozen during an increment, but
the current selected monitor motion does not establish that local interface
deformation is the cause. Any increment or contact-law comparison would
change the transient and needs a separately defined, source-bound decision;
the present evidence supports first measuring signed local clearances, not
relaxing controls.

## Source references

- Pinned source archive and source-member hashes:
  [`diagnostic-lock.json`](diagnostic-lock.json);
  official archive [`ccx_2.23.src.tar.bz2`](https://www.dhondt.de/ccx_2.23.src.tar.bz2).
- Convergence count and gate: `src/nonlingeo.c:2307–2317, 2352–2360`,
  `src/checkconvergence.c:149–162, 546–563`, `src/writecvg.f:80–83`, and
  `src/ini_cal.c:321`.
- Contact generation and CEL: `src/contact.c:89–96` and
  `src/gencontelem_f2f.f:156–180, 282–427, 491–552, 554–685, 723–768`.
- Official manual: “Contact” under convergence criteria (Section 6.10.2),
  “Face-to-Face Penalty Contact,” and the `*CONTACT FILE`, `*CONTACT PRINT`,
  and `*CONTROLS` entries in the [2.23 PDF](https://www.dhondt.de/ccx_2.23.pdf).
- Frozen contact law and attempt03 observations: [contact fragment][attempt03-contact]
  and [attempt03 results][attempt03-results].

[attempt03-contact]: ../ordinary-external-force-transient-attempt03/contact-fragment.inc
[attempt03-results]: ../ordinary-external-force-transient-attempt03/RESULTS.md
