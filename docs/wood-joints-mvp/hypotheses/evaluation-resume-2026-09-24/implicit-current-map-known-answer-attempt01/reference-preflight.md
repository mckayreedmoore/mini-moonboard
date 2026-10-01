# Independent reference and input preflight

Review date: 2026-09-27. This is a read-only preflight of the offline
reference, generated inputs, source interpretation, and the current runner
draft. It is not native validation, map acceptance, or joint acceptance.

## Reproduced inputs and source binding

`PYTHONDONTWRITEBYTECODE=1 .venv/bin/python prepare.py --check` passes and
reproduces `expected.json` byte-for-byte. The expected contract SHA-256 is
`88521d8367b2ea33c170c3c82a1a417b2fa481cf2afd7afc01558b0b7053172a`; the
producer SHA-256 is `17d327a9372c4476ce0d7fd97e2f681df5e99b95f849892080b5c3ab7ed81009`.
Deck SHA-256 values are:

| Case | Deck SHA-256 | Source body / map |
|---|---|---|
| `direct` | `0f9ff1b41b5d44774bd8d9da049f85d7e8c452a523c4ada99ab56a25b0fb0d94` | M00 A00 body only |
| `mapped_no_carrier` | `fc3bc4c04477979c27375f414c130687bee97181c795d3c6ea3ed37aceab80bb` | M00 plus its six original equations and free REF/ROT nodes |
| `mapped_carrier` | `73eacc181ebd37efe63a10a5e7822e0d5cbc7ae9ce23446185c9f5f6456b620e` | M00 map plus source M03 rigid carrier |

The reviewed design SHA-256 is
`2c49803cdf0b4bb332a11428ff45a26c96623fa55db8a68f165a980a2ce2c63b`; the
pre-run acceptance contract is
`503bd3bfb78d00695f24bd0eed6d1f66e2c094251e3f1f78bac2ae47e055d013`, and
the separate parent method disposition is
`ea83aba45af4c1f48294c1cd4966b178ae3a6454c3c9049aa23824b46faf7f27`.

The common source mesh is pinned by `mesh.inp` SHA
`117fdc67c8d3f7f7e3bf1df41d842c9d8e7fa57e1c941676bccd882878bb4803`,
`mesh.json` SHA
`1043bd4a7ac03e589d6f8819f98231b33a866ee917d1e9c7099d0104092d0a07`, and
`nut-coupling.inp` SHA
`af5b36dce4e85b19a6a5b4805dd6b00259da88ccc1a849769642db2ecbf62903`.
The six original equation rows remain byte-identical; they contain 754 terms
each and six distinct dependent DOFs. They use the existing A00 pivot
`(134.5, 1.178456090256, 410.856889078727) mm` and leave all six REF/ROT
controls free. The positive-density body has 5,490 C3D10 elements and 11,348
nodes. The carrier is the original 519-element, 1,107-node M03 body with zero
density; it adds no mass, load, contact, or independent joint behavior.

The pinned CalculiX 2.23 source archive is SHA-256
`9c88385c10fb04f5dc6c4e98027a51bebdd8aee3920e05190d6c1dd08357d6e7`.
Relevant member pins are `e_c3d.f`
`d009650b48e5ca150080aed9e19d1b65d2b2cf4869ab6d7f2b1a5cd55e2df3fc`,
`gauss.f` `aed2d48b6a63e30894e747a531f6edc32e3cd921338e370902dfb62d8e304df2`,
`rigidmpc.f` `3156cf6eaf43fd6b7a945a8dfae3b47ac49c550892be4ba8f81bcfa7e6c5ab8e`,
`nonlinmpc.f` `a9331e1895c9bcea10c405bb05f75788f4d3a6b45022e54e6a338b69850f4036`,
and `dynresults.f`
`f19b68401463333adad5898b0424b41dc13c6bcbda804c883847295d41c4b00a`.
The fixed-width input readers are pinned in the same archive: `cloads.f`
`a63ca5b5c5feacb9da6100c03084042a95487437a09f25451e208ac33c99dcbb`,
`nodes.f` `1ac1780555b4f77c11bbfa6b018ee7decc6c6c210b7d48bcc8122e2a2e43e312`,
and `equations.f`
`f64789dfa6e20791c6753b3ccc7b821bb00774dc2647b9f456ca0f9f7d106a4a`.
The source quadrature is `gauss3d5`, four points with literal weight
`0.041666666666667` (`gauss.f:339-341`). The independent reference and input
producer both now use that native literal.

## Numerical reference and output semantics

The load is the full consistent C3D10 mass action for
`f(T) = M * (1.2*T * (e_y × (x-p)))`, ramped linearly from zero to the
final-time vector over a 0.01 s step. It is not a lumped-mass, transformed-MPC,
or force-at-a-single-node shortcut. The audited decks contain 22,696 physical
CLOAD components each. The independent extraction audit passes and reports a
maximum per-component difference of `1.3962808739895107e-21 N` between the
serialized loads and a separate source-based reconstruction; all three cases
have identical parser-visible physical load values. It also confirms exact
body element/node membership, the original six equations, and required energy
output cards, including a separate M03 `EL PRINT` block in the carrier case.
The durable audit JSON SHA-256 is
`b3e2241be363ce8c42e375c797f1a11ccd676ddf5c994590e28fdfa2b1bece26`.
Its independent audit script SHA-256 is
`316f56e6aa3db33f98fbc003fb51794fa5bebae9e1ed8378bc6ef4bb1cc6dcfc`.

The input audit covers CalculiX fixed-width parsing. `cloads.f:267` reads
numeric CLOAD data from characters 1-20 with `F20.0`; the producer now guards
every generated numeric comma field at 20 characters. It records both the
full-precision load digest and the actual values consumed by that parser.
`nodes.f:140,150,160` reads coordinates through the first 20 characters, and
`equations.f:415` reads equation coefficients the same way. Eight original
coordinate tokens exceed 20 characters; each deck keeps exactly the
parser-visible prefix. The maximum source-token versus consumed-coordinate
difference is `6.94e-18 mm`. The original equation rows are byte-preserved.
Their residual gate must account for lexical output rounding token by token:
sum each original coefficient magnitude times the actual DAT token's half-ULP,
plus the declared arithmetic allowance. A coarse field-maximum times
coefficient-L1 estimate is not the acceptance rule.

The pinned quadrature reference reports M00 volume `5361.124664780609 mm^3`,
mass `4.208482861852779e-5 tonne`, and pivot-axis modal inertia
`Iyy=0.1538312437671736 tonne mm^2`; the updated source-literal arithmetic in
the reproducible producer is within its independently quantified
approximately `8e-15` relative representation difference. M03 volume is
`741.7892075330269 mm^3`, with zero density and zero mass/energy. These are
fixture references, not material qualification or joint properties.

For `*DYNAMIC,DIRECT,ALPHA=0`, `dt=0.001 s`, and `T=0.01 s`, the linearized
average-acceleration Newmark reference uses
`omega_y=c*t^2/2` and `theta_y=c*(t^3/6+t*dt^2/12)`, with `c=1.2 rad/s^3`.
At the final state it predicts `omega_y=6e-5 rad/s`,
`theta_y=2.01e-7 rad`, and `ELKE=2.7689623878091253e-10 N mm`.
The high-precision constrained-rigid Newmark calculation uses the finite
rotation and the fixed mass/reference forcing. Comparing its fitted controls
and all 11,348 body-node fields with the linearized reference gives maximum
terminal component differences of `[1.2956e-13, 6.5855e-13, 8.2978e-13] mm`
in U and `[7.6199e-11, 3.8733e-10, 4.8804e-10] mm/s` in V. This comparison
addresses the small finite-rotation correction for this selected mode. It
does not bound elastic FE response, arbitrary rotation histories, or all
numerical error.

The carrier velocity convention is source-established, while its native
output remains to be tested. `rigidmpc.f:78-107` creates the dependent
displacement relation. `nonlinmpc.f:91-177` forms the Rodrigues rotation
matrix from the total axis-angle vector and its derivative with respect to
that vector. `dynresults.f:127-181` reconstructs dependent velocity from the
converged MPC coefficients. Therefore the acceptance quantity is
`REF_velocity + dR/dw * w_dot * (x_reference-p)` using measured REF/ROT
controls. For the fixture's fixed global-Y axis this specializes to
`omega_y * e_y × (R_y(theta_y)*(x_reference-p))`. This source reading does not
prove the native output matches it; that is the fixture's test.

The pre-run limits in `acceptance.json` separate per-case reference checks
from cross-case parity. Cross-case checks include both output tokens' lexical
half-ULPs for DAT E13.6 and FRD E12.5, in addition to the declared numerical
allowance; one-record FRD rounding allowance is not reused as a two-record
parity allowance. The floors qualify this small fixture and do not assert a
guaranteed error bound. The `ELSE` limit is a nearly-rigid-response test
against positive-body reference kinetic energy, not an assumed upper bound on
elastic response. A failure remains a failed fixture qualification; no
threshold adjustment follows the native result. The scope disposition in
`parent-method-disposition.md` correctly keeps reference qualification and
map/carrier preservation as separate questions.

## Runner review and disposition

I reviewed runner snapshot SHA-256
`e0303cdecf805b98938f836af722b449433b05bc2f5f61286536504c51918f2d` as a
draft. Its freeze requires `acceptance.ready_for_native` and parent readiness,
binds the static packet and external source dependencies, refuses replacement
of an existing freeze/output, verifies the exact requested freeze before each
case and after capture, and executes cases serially. Each case is capped at
120 seconds, one CPU, 1 GiB, no network, and 64 MiB of captured native output.
The runner checks the pinned image/binary identity, output-file presence,
normal process/container exit, completion marker, output byte cap, and hashes
all files by relative path. Parent intentionally retains stopped named
containers for failure inspection; no live process remains after a completed
case.

This input/reference review finds no blocker in the reviewed runner draft.
The runner is not declared terminal here: the independent verifier has not yet
been reviewed, and the parent asked to add its self-test to pre-run packet
validation. The current acceptance remains `ready_for_native: false`; no
freeze or native execution was performed for this preflight. Passing offline
preparation and input audits establishes only that the three proposed decks,
their inputs, and the numerical reference are reproducible and source-bound.
