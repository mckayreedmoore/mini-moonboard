# Independent dynamic-fixture preflight review

This review checked the prepared mesh, motion, expected values and patch field
list. The fixture is a sound bounded test of prescribed opening/compression,
the mode-1 MAP filter and corrected retained-spring evaluation. It is not yet
ready to treat every `expected.json` force assertion as an observed-output
gate: the current patch does not emit the requested `fnl` vector, and the
spring-scale/output-presence conditions need explicit gates. No native build
or solve was run for this review.

## Frozen inputs reviewed

- [`fixture-design.md`](fixture-design.md), SHA-256
  `74326718ae6f10721018c9781061f26896fa497387c4c92bcf68900f5d49b766`
- [`expected.json`](expected.json), SHA-256
  `3a170a6571a9481395d7d6ffd8c923536fb34fd06e366cb56c7c18adb51b10e5`
- [`input/implicit_point_trace.inp`](input/implicit_point_trace.inp), SHA-256
  `e9d0ec2252201fdaa249b5e884c9290a128fb31c135afff6e08c566cb504c61b`
- [`diagnostic.patch`](diagnostic.patch), SHA-256
  `8fb9e5a88a72109a095ccb1dab650860535102f7d806f0dd6d230c23127af7ff`
- Pinned source archive SHA-256
  `9c88385c10fb04f5dc6c4e98027a51bebdd8aee3920e05190d6c1dd08357d6e7`;
  the member hashes are in `expected.json`.

## Motion and analytical oracle

The boundary conditions cover every translational DOF on both C3D10 contact
bodies: the lower body is fixed, and the upper body has U1/U2 fixed and U3
prescribed by the listed amplitude. The amplitude value is multiplied by the
unit boundary value, so the upper contact surface translates rigidly through
0, +0.001, 0, -0.001, 0 and +0.001 mm at 0 through 5 seconds. There are no
equations or prescribed MPCs. The separate C3D4 has three fully fixed nodes
and one node with only U3 free; it supplies one unloaded elastic equation and
does not connect to the contact bodies. The specified 0.1 s direct increments
align the amplitude knots with the stated event times; the 60-increment limit
exceeds the 50 increments needed for the five-second step.

For the documented face orientation, the upper slave minus lower master
displacement is the signed gap `g`. Thus compression at 3 s is `g=-0.001 mm`.
With `K=100000 N/mm³`, unit spring scale and the complete 4 mm² interface,
`p=-K*g=100 N/mm²`, scalar normal resultant is 400 N, and stored energy is
0.2 N mm. At exact touch, pressure and energy are zero whether the point set
is retained or empty. A retained positive-gap trial has negative pressure,
positive-z source-internal `fnl`, and positive energy; it is distinct from a
later MAP that filters that spring. These signs and units agree with the
`springforc_f2f.f` formulas cited in the design.

The contact-body motion is fully prescribed, so this does not test how contact
forces alter body motion or establish force equilibrium. Their reactions can
include inertia from the prescribed acceleration. The isolated witness starts
at rest, is unloaded, and should remain at zero U3. Consequently the fixture
does not validate inertial reactions, external work, or a physical transient;
the design correctly excludes those claims.

## Trace coverage and required contract corrections

The patch has useful phase separation: `CCXPT_MAP` is written in
`gencontelem_f2f.f` with the mapped candidate's raw signed gap, filter value,
identities, area and normal; `CCXPT_TRIAL` is written after corrected
`results()` evaluation and before the arrays are freed. The latter is an old
generated spring set evaluated at the corrected iterate. Its spring force
contributes to the subsequent corrected residual/convergence calculation; it
is not the pre-correction Newton tangent/load. The inherited convergence and
contact-count rows can identify a final converged iteration. Earlier MAP rows
must remain intermediate observations, as the design says.

Before any run is used as a known-answer pass, resolve these points in the
expected contract/verifier:

1. **The requested `fnl` is not emitted.** `CCXPT_TRIAL` prints six `stx`
   entries (with `stx[3]` copied to `wjp`), area, conditional energy, normal,
   `kscale` and `reltime`. It prints no `fnl` components or nodal force
   resultant. `*NODE FILE U` and `*CONTACT PRINT CELS` do not supply that
   vector either. Yet `expected.json` requires per-row and aggregate native
   `fnl` checks. To keep that as an observed-output oracle, instrumentation
   must emit the vector at the `springforc_f2f` result point and the fixture
   must be rebuilt/requalified. Otherwise narrow the gate to emitted pressure,
   observed spring area and energy, and describe `fnl` sign only as a
   source-derived implication rather than a measured fixture result.
2. **Bind the oracle to `kscale`.** The source formula is
   `stiff=-A*K*g/kscale`; therefore pressure, resultant and stored energy
   divide by `kscale`. The trace emits that value, while current expected
   formulas assume one. Require `kscale==1` on the tested rows or include the
   observed scale in all three calculations.
3. **Require energy output to be enabled.** The patch initializes
   `wjenergy=0` and fills it only when `nener==1`; `nener` is also emitted.
   Require `nener==1` for rows subject to the energy oracle, so a disabled
   energy request cannot be mistaken for a physical zero. The nonzero
   compression/trial energies also need to remain explicit known-answer gates.
4. **Join event times through native state records.** MAP rows contain step,
   increment, attempt and iteration but no absolute time; TRIAL adds `reltime`,
   which is not an absolute time field. Use the frequency-1 native state
   output's step/increment/time to bind final converged rows to event time, and
   retain the attempt/iteration key for phase matching. Do not infer a trial
   time from `reltime` alone. In particular, count an empty accepted set only
   from the matching final-convergence/contact-count record, not merely from
   the absence of `CCXPT_TRIAL` lines.

The prepared scope remains useful after those contract fixes: a positive-gap
corrected TRIAL is an observed old-set law check, not accepted contact
resistance, and lack of such a row means that particular stale-set behavior
was not observed. Neither outcome is a joint-mechanics acceptance result.
