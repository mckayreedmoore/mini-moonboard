# Mass-operator applicability source check

This note records a bounded, read-only source check for the current attempt03
deck. It does not review the attempt03 producer, perform mass integration, or
establish contact equilibrium or mechanical acceptance.

## Finding

For the pinned current deck, `fea.dynamic_momentum.calculix_221_mass` uses the
same untransformed four-point C3D10 reference-volume mass operator as the
native element contribution. The 35 current contact pairs are declared with
`TYPE=SURFACE TO SURFACE`. CalculiX maps that type to `mortar=1`
(`contactpairs.f:115-118`), while the `premortar()` transformed-basis path is
entered only when `mortar>1` (`nonlingeo.c:2626-2633`). In `e_c3d.f`, C3D10
elements use the four `gauss3d5` points (`:576-580`); the ordinary mass
integrand is `rho*N_i*N_j*weight` (`:978-987`), and the `shptil` transformed
integrand is selected only when `mortartrafoflag==1` (`:981-984`). Thus the
current `SURFACE TO SURFACE` path does not turn on the mortar-basis mass
transformation excluded by the helper's contract.

This conclusion concerns the element operator only. Native assembly then
eliminates MPC-dependent DOFs. `mafillsm.f:380-404` expands a single
dependent-DOF endpoint using MPC coefficients; `:431-459` and `:470-505`
expand pairs of dependent endpoints using products of both coefficients. This
is the solver's constrained/reduced assembly (`T^T M T`), not an additional
integration rule and not the full physical-space `M*a` returned when the
helper applies its element blocks to a physical acceleration field.

The deck has 15 positive-density C3D10 section owners: three wood sets and
twelve bolt/head-washer/nut-washer metal sets. The four nut solid sets have
explicit density zero (`materials.inp:5-49`), so they contribute no physical
mass to this reconstruction. They remain kinematic carriers. The current
step is implicit `*DYNAMIC,ALPHA=0` (`pilot.inp:115`); the pinned input files
contain no `*MASS SCALING` or explicit-step card. With this alpha value, the
instantaneous balance does not require a nonzero-HHT history-force weighting
correction.

`resultsforc.c:35-58` recovers an MPC multiplier from the dependent residual
divided by the first MPC coefficient, then removes its coefficient-weighted
contributions from the force vector. The force-restoration path at `:78-111`
adds `coefficient * multiplier` to each term. For rigid-body MPCs,
`rigidmpc.f:86-107` puts the reference-to-node lever-arm coefficients on the
rotational terms. Those are the source semantics that govern generalized
constraint moments: a physical-space angular-momentum or `M*a` vector is not
itself an MPC multiplier or reduced generalized torque. A comparison to a
reduced residual/reaction needs the exact MPC coefficient mapping, or must be
described as a separate full physical-space balance.

The untransformed operator applicability does not qualify the four
zero-density carriers as physical mass, validate any 24 generalized torques,
establish a 35-contact wrench balance, or prove the candidate joint mechanics.
Those remain separate producer/output and mechanical questions.

## Pins

The actual run's `binary-source-index.json` is pinned below; it identifies the
instrumented executable and the CalculiX source archive used by that build.
Source-file digests are given to make the cited routines independently
checkable against that archived source. Current run input hashes pin the
deck whose contact type, sections, and step were checked.

| Artifact | SHA-256 |
| --- | --- |
| Current run `binary-source-index.json` | `b55323a611704378ad84f1e688075e284859bdbd09b75d853c0bb8ef0b9ef19f` |
| CalculiX source archive (hash recorded in binary source index) | `52a20ef7216c6e2de75eae460539915640e3140ec4a2f631a9301e01eda605ad` |
| `contactpairs.f` | `ca9a2fa4af926cc02afaca78c52b7b9bec75c75fd7073314b54f0f4e87b0ede8` |
| `nonlingeo.c` | `0be7d7d6037868c364a621e12a3802a703f189b09ba200de95cf2e9d1b211f1b` |
| `premortar.c` | `64af63205c6d5c378f6a76cd586bf0f3627151ae50ff9a60cc46e9cf1e7b57b6` |
| `e_c3d.f` | `74652da7eb31a1df3c8b0c65c9304819d24f52cafd088288e9865e83dc584d61` |
| `mafillsm.f` | `a9016aba3800106c7657dd11787e22a5696803195217b3576ef1d0da7e46a640` |
| `resultsforc.c` | `d1de9498ac715a7f08da0b7beba3c92c7c2f1030c85c37122d2708f2f480cad0` |
| `rigidmpc.f` | `325223215722ed9622d1c766fe7cbd823fefbbdfa08e2ebf77e0a27c050e1b45` |
| `fea/dynamic_momentum.py` | `f97f0214a8dcd6ae8e539ed3f1377603031776e1b84235bb5dd058e48fd104e3` |

| Current run input | SHA-256 |
| --- | --- |
| `pilot.inp` | `211d0d9b6f96fa2215347306a5c24d37cfe71f1d67a49a99349535321462a4a3` |
| `mesh.inp` | `117fdc67c8d3f7f7e3bf1df41d842c9d8e7fa57e1c941676bccd882878bb4803` |
| `materials.inp` | `e0063d0ebc2232b6699f020488944617b1f44f7bfa38f931f47907d08202a3bb` |
| `nut-coupling.inp` | `af5b36dce4e85b19a6a5b4805dd6b00259da88ccc1a849769642db2ecbf62903` |
| `rigid-carriers.inp` | `a15eebb0537a4a3f096531f2c4e48ecd26b6ec53908d61178ead7dfe3bc27815` |
| `contact-fragment.inc` | `e70fc43593e8e5a5b8e445f88122fb5e675dc788207be6e6031aae9c1f71cac5` |
| `output-sets.inp` | `e86adac9dfbe2a80bc62abcba3ea081efcad2e0262df100db22efc1e5020213c` |
| `pilot-sets.inp` | `7f5c158659658d60f6a3e48f714f4d8239cc7848c42732f747304b47fef9f5e0` |
