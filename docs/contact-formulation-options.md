# Contact formulation options: CalculiX 2.21

Research only; no deck change or solver launch. This is a proposed numerical
diagnostic, not a material, geometry, friction, or capacity recommendation.

## Decision

`TYPE=MORTAR` is a supported candidate for a controlled comparison with the
current face-to-face penalty contact. Keep the C3D10 timber, C3D8 fixed ground,
linear normal law, friction coefficient, stick slope, and `*STATIC`/`NLGEOM`
unchanged in the first comparison. It is **not a guaranteed moment-conservative
replacement**: the 2.21 mortar manual explicitly says that normals, tangents,
and surface segmentation are updated only once per increment. First investigate
smaller release/load increments in the existing formulation; if the discrepancy
persists, test mortar on a shear coupon before the full frame. The original force
and moment acceptance limits remain unchanged.

The observed distinction motivating this test is reproducible in the
[mu=0.5 independent audit](../fea/results/floor_contact_continuation/full-increment-mu0p5/independent_audit.json):
ground-reaction deformed moment residuals reach 4.8925 Nmm at free gravity and
256.5547 Nmm under load, while moments computed using slave contact resultants
remain below 1 Nmm. Pair forces agree within print uncertainty. This supports a
contact-interface moment-transfer discrepancy. Frozen mapping is a plausible
mechanism, not proof of a solver defect or proof that mortar will fix it.

## Exact-version evidence and minimal changes

Sources inspected were the official [2.21 HTML manual archive](https://www.dhondt.de/ccx_2.21.htm.tar.bz2),
[2.21 source archive](https://www.dhondt.de/ccx_2.21.src.tar.bz2), and
[2.21 test archive](https://www.dhondt.de/ccx_2.21.test.tar.bz2).
Paths below are relative to `CalculiX/ccx_2.21/` inside those archives, not to a
moving online manual. Manual `doc/ccx/node144.html` has SHA256
`5ad1127ad230d538d0479c69f7b095471cf886b4e880f8fa9fee1885c1ab4534`.

For **every** contact pair, replace only `TYPE=SURFACE TO SURFACE` with
`TYPE=MORTAR`. Preserve slave/master ordering and separate LEFT, RIGHT, and
KICKER surfaces. Retain the existing interaction:

```text
*SURFACE BEHAVIOR,PRESSURE-OVERCLOSURE=LINEAR
10000.
*FRICTION
0.5,100.
```

Here 0.5 is the existing sensitivity-run value, not a measured floor property.
For another baseline, preserve its coefficient instead. Do not introduce
`ADJUST`, hard contact, changed stiffness, new frame restraints, or a different
friction value as part of this formulation-only comparison.

| Item | Exact 2.21 evidence and consequence |
| --- | --- |
| Elements and procedure | Manual `node144.html` recommends genuine 3D solids and permits only `*STATIC`. C3D10 and C3D8 are within that category; the precise mixed-order pair still needs a coupon test. Official `test/cubesmortar.inp` demonstrates quadratic C3D20 contact with LINEAR, friction, and `*STEP,NLGEOM`; it does not validate this frame or mixed tetrahedron/brick pair. |
| LINEAR and friction | `src/getcontactparams.f:44-69,92-99` reads mu and the inverse supplied stick/normal slopes for mortar regularization. Existing positive values are supported. Its exponential-law branch explicitly rejects friction; do not substitute EXPONENTIAL. |
| Hard contact | Manual `node347.html` says to omit `*SURFACE BEHAVIOR` for true hard mortar contact. Writing HARD is not the clean comparison with the current finite LINEAR compliance. |
| Quadratic alternatives | Manual `node144.html` distinguishes MORTAR's dual multiplier basis from LINMORTAR, which omits midside multipliers, and PGLINMORTAR. `node240.html` recommends trying MORTAR first. These are separate experiments, not aliases on C3D10. |
| Pair consistency | The manual disallows mixing penalty and mortar, or mixing mortar variants, in one deck; do not convert only the kicker. Avoid surface reuse and extra slave-edge MPCs. Fixed master-ground SPCs are not the prohibited added slave MPCs. |
| Increment limits | Initial gaps can prevent force-driven quasistatic contact. Mortar freezes segmentation and directions per increment; the manual recommends small initial increments and at least four increments for large tangential movement. Four is a starting point, not an accuracy guarantee. |

## Output incompatibility is an acceptance blocker

The current penalty DAT auditor cannot simply be reused on mortar output.
Manual `node241.html` restricts pair `CF/CFN/CFS` resultants to face-to-face
penalty. Source `src/printout.f:386-495` emits the familiar DAT CDIS/CSTR headers
and rows only for node-to-face (`mortar=0`) or face-to-face penalty (`mortar=1`),
not MORTAR (`mortar=2`, assigned in `src/contactpairs.f:115-124`).
`src/printoutcontact.f:79-90` integrates penalty contact elements. Merely having
CF cards accepted, or seeing zero/empty resultants, does not establish mortar
coverage or balance.

The supported alternative is nodal `*CONTACT FILE` output (`CDIS`, `CSTR`; the
official cube example uses the accepted `CDISP` spelling).
`src/mortar_prefrd.c` copies the mortar displacement/stress array into output;
`src/frd.c:1598-1644` writes COPEN, CSLIP1/2, CPRESS, CSHEAR1/2 at slave nodes.
These are not the penalty integration-point rows. Mortar satisfies its
stress/penetration relation weakly (manual `node144.html`); applying the old
pointwise `p=-K*CDIS` test to these nodal fields would be unjustified without
checking the exact regularized variable definitions and multiplier basis.

Before claiming a mortar pass, verify node coverage, signs, local bases, and
active/open behavior against a known coupon; define the appropriate weak-law
audit. Independently check global forces and deformed moments using all external
reactions and applied loads. `mortar_prefrd.c` temporarily adds contact forces
to the nodal-force output buffer: verify actual RF semantics on the coupon and
avoid counting free slave contact forces as additional external supports.
An independent slave-versus-master resultant comparison needs an established
mortar nodal-force extraction path, not penalty CF reconstruction by assumption.

ASCII FRD contact output uses `%12.5E` after a float cast, versus the penalty
DAT's higher precision. Propagate both formatting and float-rounding uncertainty
when checking local fields. Do not enlarge the physical moment gate to hide
insufficient output precision; retain higher-precision evidence where needed.

## Smallest discriminating shear test, not yet implemented

1. Reuse the existing small six-C3D10 cube and fixed C3D8 ground, with unchanged
   material/contact parameters, initial seating, and frozen input provenance.
   Apply a modest centered vertical preload through explicit top nodal loads.
   Constrain top X/Y only during seating, with all actuator reactions reported.
2. Maintain preload and prescribe a nonzero top X translation (Y held), leaving
   top Z free. Choose a bounded displacement schedule that produces actual
   tangential motion/contact redistribution, including sliding if stable; record
   realized slip rather than assuming the requested top motion equals slip.
   Use SPCs at the top, not slave-face MPCs. The actuator is intentional coupon
   loading, not a representation of a free-standing board.
3. Run the same history with penalty and MORTAR, first at a maximum increment
   of 0.25 per unit step, then 0.125. Compare every accepted endpoint. If either
   needs smaller increments, compare both at that common schedule. Stop on
   incomplete output, unsupported requests, instability, or missing reactions.
4. Sum ground plus actuator RF plus applied nodal forces; sum their moments
   about one fixed origin using `x+u` for every force location. If gravity is
   included, integrate its deformed body-force moment using the established
   nodal weights. Require the existing global gates with print-error accounting;
   report moment error versus realized tangential displacement and increment
   size, not convergence alone. Check contact-field coverage/laws using each
   formulation's actual output semantics before calling either a contact pass.
5. Only if the cube comparison is interpretable, repeat on the extracted actual
   left-leg coupon with its real quadratic six-node floor faces and upper-band
   actuator. The lean introduces a less symmetric moment-transfer test. Preserve
   all guide/actuator reactions in balance; a guided coupon cannot establish a
   free full-frame solution. Promote a formulation only after full-frame force,
   moment, contact-law, history, and mesh-sensitivity audits also pass.

A reduction of moment error with increment refinement would support (not prove)
the frozen-geometry hypothesis. A consistent mortar improvement at matched
increments would justify further validation of that formulation. Failure of
both motivates contact mapping/output investigation, not member resizing or a
weaker acceptance threshold.
