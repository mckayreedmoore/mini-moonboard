# Post-run impact review — dynamic contact coupon attempt 01

This is a read-only diagnosis of the frozen run. It changes no solver or
physics behavior and does not imply that automatic incrementation would pass.

The execution record is `FAIL_NATIVE_CAPTURE`, exit 201 after 0.621 s, with no
OOM or timeout and 1,034,124 output bytes under the 16 MiB cap. The input hash
is `e9d0ec2252201fdaa249b5e884c9290a128fb31c135afff6e08c566cb504c61b`, freeze
hash `62bf95797e1c583c7f2a82d8d6e05eed8c5b0f3eabb1520f9764109ba66966be`, and
execution-record hash `4918323727be76a3280162935c8ebf8632c731bb0bc4cd02f3b784eae6931191`.
Key output hashes: stdout `d00a9ea18cfbd444f295f8807d42fc1654751fef775b7f4d1c8069f2d2fd9631`,
STA `ce9368853db6d9ee2d471ade001a77f989bc1cd7ad92bd037daa76a2eca24c6f`, CVG
`9b5c2d8a032cea4679ef1bd04e99addaa5e6ed2d95c00646e6d4206e1b5ee5ad`, FRD
`144eb76162fe9084ddac5a6320bb983fbe7c033059a9d0b9ea68e42f6dfcec8f`, and
DAT `782d0ca6bf2b5b1fd03a9a2bde875571472842bca7f0faa33dbd1b13a37bebd9`.
The pinned executable and image hashes are recorded in `output/execution.json`.

There are 19 accepted states through 1.9 s. The STA marks increment 20 as
`1U`; the FRD’s two increment-20 frames at 2.0 s are failed-attempt/error
output, not accepted states. At increment 20 the generated contact count is
0, then 56, then 56 over iterations 1–3. The last iteration passes the
mechanical residual, displacement, visco, and stabilized-count gates, but the
trace reports `contact_energy_eligible=1`, `idivergence=1`, and no final
convergence. All 56 final-iterate trial points are essentially at zero gap
(`−4.44e−19 mm`), with pressure about `4.44e−14 MPa` and summed point spring
energy about `3.94e−32 N mm`. Thus this coupon’s count switch itself carries
negligible trial pressure/penalty energy; it says nothing about forces in the
full joint.

Pinned 2.23 source explains the apparent contradiction. `nonlingeo.c` uses
`iflagact` for count changes between Newton iterations, while
`checkconvergence.c` separately calls `checkimpacts.f` for an implicit
contact-energy check when generated contact elements exist now or at
increment start. A
stable set at iteration 3 clears the former gate but does not clear
`idivergence` from the latter. The logs omit the numeric energy ratios, so the
exact threshold branch/value remains unproven. The “divergence allowed:
number of contact elements stabilized” message is in a separate residual
branch; it does not reset `idivergence`. `*DYNAMIC,DIRECT` then takes the
fixed-increment fatal path, explaining the final “please try automatic
incrementation” error and 1U status.

For this input, `dynamics.f` sets `tmin=tmax=tinc` under `DIRECT`;
`dyna.c`/`nonlingeo.c` normalize those bounds by the 5 s step period. Although
the impact check can request a quarter-step, the bounds clamp it back to
0.1 s. A conditional separate attempt would remove `DIRECT`, preserve
`ALPHA=0`, the 0.1 s initial increment and 5 s period, and explicitly choose
a minimum plus a maximum of 0.1 s. No minimum is justified by this run. The
face-to-face retry path also has a first-cutback guard and assigns
`kscale=kscalemax`; record actual step sizes and `kscale`, and do not treat
that run as a pure step-size comparison or assume it will pass.

No extra output time point is needed to locate this failure: `FREQUENCY=1`,
CVG, and the diagnostic trace already show the 2.0 s attempt. If a future
variable-step capture needs exact output at the re-contact knot, a named
`*TIME POINTS` sequence can be used only after removing `DIRECT`; it outputs
at its listed times and the step end and ignores `FREQUENCY`. That changes
output timing, not convergence or acceptance. To verify the actual impact
decision, an output-only trace at the same rejected iterate must also print
the `checkimpacts` inputs and computed energy ratios (`energy`, `allwk`,
`dampwk`, `energyref`, `emax`, `delta_r_abs`, `delta_r_rel`, `r_rel`,
`r_rel_bc`), with step/increment/attempt/iteration, contact counts, proposed
increment bounds, and `kscale`. The present contact-point trace does not
provide that global energy record or a full pair work history.

Accepted-state stdout reports zero external work at all 19 states and kinetic
energy alternating between `1.6e−14` and near zero; no finite compression
state was reached. This prescribed-motion coupon therefore does not establish
how the impact-energy check behaves once contact stores meaningful energy,
and automatic stepping is not forecast to succeed. If that limitation
persists, a separate force-driven known-answer coupon may be needed; no such
fixture is designed here. The separate [contact-count interpretation](../../ordinary-external-force-transient-attempt04-diagnostic/contact-count-interpretation.md)
remains the applicable evidence boundary for the full-model replay.

The source archive pinned by this fixture has SHA-256
`9c88385c10fb04f5dc6c4e98027a51bebdd8aee3920e05190d6c1dd08357d6e7`; the
pinned 2.23 manual is `fea/generated/ccx_2.23.pdf`, SHA-256
`a0bf3fc03f374912ff2bf28da3f7dfb6a61428dd7f41b281a2e7e1fdb318f330`. Relevant
source members: `dynamics.f` (`d861c936c204853e84e7647b4164e78556c11b6eb0a532b623d4a75622f53e5e`,
lines 117–119, 248–270), `checkimpacts.f`
(`30b2e0c7ca03f741852dfc93b67657291f91acfc3b3db8c1b36ec9589733fd66`, lines
90–108, 148–190), `checkconvergence.c`
(`776ecbeec10de037dc1a18171b81ede973fca52d587a2c4d4342f0d14f362b11`, lines
149–162, 262–295, 328–330, 537–563, 599–706), `dyna.c`
(`308d4044b594198e3d33af94cc387712257c552398ef3e8f1e3caae8d740ac29`, lines
751–756), and `nonlingeo.c`
(`8684bb6d7fa7097c0a854db5a45eb9e2d11adfde574e688184ecbbbad56ff83f`, lines
859–871). See the [official 2.23 manual](https://www.dhondt.de/ccx_2.23.pdf),
`*DYNAMIC` and `*TIME POINTS`.

The preflight-review provenance drift is separate from the native failure:
the frozen review hash is `31f80d8e7390a1e405955ba560067a50859a4541a8d36b31bdd1d4f872774186`
and the current review hash is `fc67100db6b74b1a8ef64ca5ac37307932f8a4f01c07cab12d47b8d485411e24`.
The pre-edit review bytes were not recovered exactly. The frozen manifest and
current review remain preserved; the input, executable, verifier, runner, and
captured output hashes are unchanged.
