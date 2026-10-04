# Central washer contact completion

This packet supplies the elastic calculation omitted by the ordinary full-annulus
recipe for the twelve `center_principal_right_2` ends: head on
`center_principal_cleat_right` and nut on `base_principal_center_right`, each in
the existing six cases. **All twelve actual-mask elastic comparisons completed,
with zero numerical stops and zero declared reference exceedances.** The parent
executed the mechanics serially; a separate saved-array audit authenticated its
receipt and integrated all 24 contact forces, first moments and spring energies.
The six recovered-moment static trials remain separate static comparisons.
Actual material/product qualification, complete joint acceptance and all
physical/fabrication release flags remain unresolved or false.

## Frozen geometry, loads and support

The geometry is the reviewed 104-axis layout with 66 Hillman axes. Only the
two unchanged central receivers enter this local model. No four added
internal-v ties or six-bore knee spine geometry is used. The reviewed register
is `rawlocal/working-joint-register/attempt03/register.json`, SHA256
`c34745395481038e32c7474de1798882263de7e54a7cc494949948b4a5e3464c`;
its original frame response remains `frame-250-attempt02/response.npz`, SHA256
`0625196497b0dbc7b297724d7b9947f7c7c61bb282cd4d9681705629302c76c7`.

The twelve prescribed force/moment vectors reuse the exact completed
`washer-end-reference-join/attempt01` rows. These retain the newer **conditional
proposal-gravity comparison**, using 104 global axes, response
`62bd4116cfb577a0846f4de0d43fbeec6bb704bac7feee530ee673ded1820f90` and frame
comparison `c3a8ff024fb494032d947aedfd6f00cda8698587b8751b2cec66e4b3af243729`.
They do not become reviewed104 original-force results. Each input row records
the original reviewed tie T separately without substituting it into this solve.
The existing source basis remains one 250 lb source multiplied once by two,
signed 300 N, 100 mm lever and its recorded permanent loads/no-slip support.
This local calculation adds no demand or duration factor.

| Case | Prescribed newer T, N | Original reviewed104 T, N | Own recovered moment, Nmm |
| --- | ---: | ---: | ---: |
| a1-rear | 4.193089806462 | 4.193471095398 | 7.949370328664e-16 |
| a12-forward | 7.187337242780 | 7.188811222953 | 1.527424020598e-15 |
| a12-left | 9.136758031354 | 9.139026484462 | 1.888246503601e-15 |
| a12-rear | 8.500698927748 | 8.503991288892 | 1.658395643034e-15 |
| k12-rear | 9.304217617441 | 9.306831461449 | 1.847480501915e-15 |
| k12-right | 22.916047963748 | 22.952332643146 | 4.225786387480e-15 |

Both ends retain each case's same T and its own signed moment vector. The
small moment values are preserved rather than rounded to zero. The original
reviewed104 forces exceed the newer values by 0.0091–0.1581%; that difference
is not silently removed or reported as the same force result.

| Mask | Exact supported area | Source and geometry |
| --- | ---: | --- |
| Head wood | 213.627873187505 mm² | Catalog annulus at saved underhead datum `(172.95, -90.30983137880764, 367.01022206613885)`; full support in three saved CAD depth probes |
| Nut wood | 193.547092494488 mm² | Catalog annulus at `(50.95, -90.30983137880766, 367.0102220661388)` minus the saved passage disk |
| Head/nut pressing face | 24.3580923073285 mm² | Existing hypothetical circular land, radii 4.1529–5 mm |

The catalog plate has inner radius 4.1529 mm, outer radius 9.2329 mm and
thickness 1.2954 mm. The nut passage has radius 19.05 mm and center
`(17.354349156787023, -18.833277247291903)` in the fixed chart
`x=global_Y-seat_Y, y=global_Z-seat_Z`. The nut wood domain is
`ri² <= x²+y² <= ro²` and `(x-cx)²+(y-cy)² >= 19.05²`.
The own 3.65 mm bore is entirely inside the washer hole; natural timber edges
are outside the plate. The passage's nearest edge is 6.559876347398426 mm
from the bolt axis, leaving the entire 5 mm pressing land supported.

Independent circular-segment area arithmetic matches all saved nut CAD areas
within 5.4e-11 mm². The head match is within 1.2e-13 mm². The preserved
`/tmp/mini-moonboard-remaining-seats-parent-2026-10-01.json` supplies those
measurements and exact end datums. The elastic wood support uses the entire
actual supported mask. It does not credit the passage void or arbitrarily
remove supported wood outside the old 5 mm static ring.

| Frozen source | SHA256 |
| --- | --- |
| Joined end receipt | `8f8b06d4a90b6c9462fb5f21fa398e42582a7d9be337c1fb327324b42d035783` |
| Joined end rows | `b5e3160ec167ee9ef00cd7542a7701912ce43ab4db4673abbaa6291e8d0c717e` |
| Existing ordinary consumer | `5501c39ca510f576a77f4ccb3256848f88aff2854263e06cba4fcfd44e469fcf` |
| Existing edge method | `ffe3db3e8c707851d44f0c60c43e6e6ef4aa4845f753dc6880c64186e3c75e61` |
| Existing material/flexure helper | `782ded96afd5e02e27873bd72b77073a643ed7c2a7946703a3240b1f51b21eac` |
| Exact central-mask contract | `e430c138f0e1fb4eacda278fa535d3e14400fcff3514f4a81d3a5f7fc3ac6646` |
| Saved support probes | `64853898bccf71df62119f0977f29aa612b323d436790b370b5616f7b3cb9fe3` |
| Finished head receiver STEP | `eef681f8f99c1af026c439692b813a51b0412892d4137ee7dd9748388ed3f0a2` |
| Finished nut receiver STEP | `9053a7210a781e919038a4a823f867325dd5c78907bd028d8b9e76dc0b46df58` |

## Elastic method and numerical validation

The producer reuses `washer-ordinary-fine-reference.py`'s inert loaders,
`washer-reference-completion.py`'s bindings, and the existing fine
`upper-right-washer-edge.py` radial assembly, energy, Newton iteration and
field recovery. It does not run either the 994 ordinary comparisons or the
48 side comparisons. No native, frame or CAD solver is required.

The isotropic Mindlin energy follows the same primary
[NGSolve plate derivation](https://docu.ngsolve.org/ngs24/SaS/plates_derivation.html).
E = 200,000 MPa, nu = 0.3, hypothetical Fy = 250 MPa, Kwood = 20 MPa/mm,
Khead = 10,000 MPa/mm and shear correction 5/6 remain unchanged. Wood contact
is `Kwood*max(w,0)` on the supported mask; head contact is
`Khead*max(h-w,0)` on the pressing annulus. Both have zero pressure outside
their domains. The rigid head plane has three free normal displacement/tilt
coordinates. There is no preload, friction or artificial added stiffness.

The existing four inner/twelve outer radial elements and Fourier order eight
are retained. The original cosine sector is supplemented with the corresponding
sine sector. Angular orthogonality gives identical plate Gram blocks for each
positive mode, with zero cross-sector energy. This permits an arbitrary
off-center support mask and both prescribed pressure moments. The model has
2,198 unknowns. It retains the free radial boundary and existing axisymmetric
trial-space convention. Sparse block assembly uses
[SciPy block_diag](https://docs.scipy.org/doc/scipy/reference/generated/scipy.sparse.block_diag.html);
the existing Newton method retains diagonally scaled
[SuperLU](https://docs.scipy.org/doc/scipy/reference/generated/scipy.sparse.linalg.splu.html).

The nut contact quadrature splits angular intervals where each radial element
edge meets the passage circle, then integrates the exact supported radial
interval. It uses 24 angular Gauss points per interval and six radial points.
The head/full-annulus grid remains the original 128 angular stations. A run
must reproduce analytical supported areas within 1e-6 mm² and contain zero
wood-contact points in the passage. Forces and both first moments are
integrated independently at each contact; their world-coordinate vectors are
recovered about that same end's seat.

The geometry-only audit independently integrates Cartesian strips through the
outer disk, own hole and passage void. It compares the mask integrals of `1`,
`x`, `y`, `x²`, `xy` and `y²` with the saved polar method at 12, 24, 48 and 96
angular Gauss points per split interval. At the adopted 24-point rule, area and
first-moment residuals are at most 1.28e-13 in their corresponding units; second
moments differ by at most 4.55e-12 mm⁴. Every sampled order satisfies the
declared geometric tolerances. This qualifies supported-domain quadrature;
it does not establish solution, active-set or stress convergence.

Before the twelve solves, two known-answer method examples evaluate exact
affine, zero-strain plate poses. Matching full-face springs have the exact
solution `w=c+tx*x+ty*y`, `h=(1+Kwood/Khead)*w`. For full compression,
`T=Kwood*c*A`, `Mx_pressure=Kwood*tx*I`, `My_pressure=Kwood*ty*I`.
The first example exercises nonzero moments in both directions. The second
uses `c=ty=0`, `tx>0` and unilateral contact on exactly half the annulus;
`T=Kwood*tx*2*(ro³-ri³)/3`, `Mx_pressure=Kwood*tx*I/2`.
The examples check numerical forces/moments, active area, plate strain and
energy gradient at their known exact poses. They validate assembly and
lift-off behavior, not current-mask stress convergence.

Both examples passed before the own-end solves. The fully compressed two-axis
pose gives 12.8176723913 N and first moments `(5.47384151358,
-2.73692075679)` Nmm; its maximum gradient is 9.39e-13 N. The half-annulus
pose has exact force 0.0953931416865 N and moment `(0.547384151358, 0)` Nmm.
Its 128-station angular rule returns a 9.58e-6 N force residual and the exact
106.813936594 mm² active area, within the unchanged tolerances. Maximum sampled
strain across both examples is 3.49e-19. No tolerance was relaxed.

The existing tolerances remain 1e-4 N scaled gradient, 0.001 N contact force,
0.02 Nmm first moment, 100 Newton steps and 50 Armijo backtracks. Each returned
state must also have nonnegative pressure, zero inactive pressure, the declared
spring law, and matching signed world forces and moments. Stops retain their
diagnostics and count as incomplete qualification.

Steel results retain the same sampled face bending/midplane shear proxy:
face stresses from `6M/t²` and parabolic midplane shear from `3Q/(2t)`.
The producer samples both radial edges, element boundaries, the pressing-band
boundary and radial/angular interiors. Wood pressure is masked during recovery;
both contact quadrature and recovered field peaks are retained, taking the
larger for the conditional wood comparison. Actual delivered material yield,
thickness and pressing profile remain unverified. These numerical comparisons
do not include contact sigmaZZ, three-dimensional edge stress, plasticity,
finite rotations or feedback into shaft/frame behavior.

## Parent command and outputs

Import is inert. API: `prepare(output: Path)` for source-only preparation;
`build(output: Path)` for serialized numerical mechanics. Both require a fresh
immediate child of this packet's raw directory and preserve previous outputs.

```sh
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 uv run --no-sync python docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/upper-corner-screw-layout/washer-restricted-contact-completion.py --output docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/upper-corner-screw-layout/rawlocal/washer-restricted-contact-completion/attempt03
```

The parent command performs one fine radial assembly, two support instances,
two known-answer evaluations and twelve own-end solves. It writes
`input-plan.json`, `known-answers.json`, `mask-validation.json`, twelve
compressed pose/contact arrays, `end-states.jsonl`, a summary and a receipt.
Every end is flushed as it completes. The receipt pins every consumed source
before/after execution, the producer snapshot and every output. Existing
source packets, frozen outputs and `/tmp` remain unchanged.

Source-only `preparation01` completed with **358 authenticated pins / twelve
ends**. Its receipt SHA256 is
`831136b6ae3798b1ccb6a110b0922f946e2f8964699f077c7916e161034817d7`;
the prepared producer SHA256 is
`063c6346adfde2ed123a362181bf941a1d04f0e3efaafb54f3a33af09e62ecea`.
The parent executed `attempt01` serially. It stopped in the first known-answer
field evaluation, before any of the twelve end solves. Its producer snapshot
retains the preceding SHA256; its input-plan SHA256 is
`25ce92f99bcb13cd1f016b3d9374f391c49bc7ff73b899d2a966b59737e8949c`.
The parent preserves the terminal trace. The saved `field_values()` expects
NumPy angle arrays, but the known-answer wrapper passed a Python list;
`mode*angles` at mode zero became an empty list and produced the recorded
`(2,2), (2,0), (2,2)` broadcasting error. This is an implementation error,
not a mechanical failure or a qualified numerical result.

The owned wrapper now converts both coordinate inputs into one-dimensional
NumPy arrays before calling the unchanged saved field helper. No radial or
Fourier basis, contact mask, material law, prescribed wrench or tolerance
changed. The corrected producer SHA256 is
`7b3bb62a896a2974505661ced9a038a24b6dd6252fbae4e62c71544ddc9b1dfb`.

`preparation02` authenticated that correction; receipt SHA256
`cc1e1e40da40209e7a5e5ee553773810792b038c3fa529535db2f47e36c2ec48`.
The parent's `attempt02` passed both examples and masks, saved the first head
JSON row and head/nut pose/contact arrays, then stopped while serializing the
nut record: `wood_supported` in an unnormalized sampled witness was a NumPy
boolean. It has no complete receipt and does not qualify all twelve states.
Those bytes remain unchanged. The final producer normalizes the entire record
through the existing pinned `json_value()` helper before writing. A saved-record
check reproduces the old exception and verifies a native-boolean JSON roundtrip;
no load, basis, mask, contact law or tolerance changed.

`preparation03` authenticated the final producer; receipt SHA256
`bca810c77a8a17414f4d030e472509ae6c10d405cc2f0f58e9937e4c94d88bff`.
Its producer snapshot and the completed `attempt03` snapshot have SHA256
`d79e0a408f60184b074de08157427bfaedf57d20c5e8b51828868614eb9cade4`.
All three input plans retain SHA256
`25ce92f99bcb13cd1f016b3d9374f391c49bc7ff73b899d2a966b59737e8949c`.

## Completed actual-mask comparisons

`attempt03` completed twelve states with one fine plate assembly and two
supported-mask instances. It retained all six existing static trials. The head
states converge in two Newton steps and the nut states in three. The maximum
scaled gradient is 6.77e-12 N; maximum energy-identity residual is 1.85e-14 Nmm.
Every supported wood quadrature point is active. Pressing-face lift-off remains
in the returned solution: head/nut active pressing areas are respectively
21.5605998542 and 21.6087300653 mm², within the full 24.3580923073 mm² land.
No unsupported wood point acquires pressure.

| End / receiver | States | Maximum sampled steel proxy | Proxy / hypothetical 250 MPa | Maximum supported wood pressure | Pressure / conditional 4.30922330823 MPa reference |
| --- | ---: | ---: | ---: | ---: | ---: |
| Head / center principal cleat right | 6 | 9.250588689 MPa | 0.037002355 | 0.123136840 MPa | 0.028575182 |
| Nut / base principal center right | 6 | 9.046291301 MPa | 0.036185165 | 0.154642293 MPa | 0.035886349 |

Both maxima occur in `k12-right`, with prescribed **T = 22.91604796374847 N**
and each end's own signed moment magnitude 4.225786387479502e-15 Nmm. The
reviewed104 original value **22.952332643146 N** remains a different source
state; neither its rigid/static comparison nor the newer elastic comparison is
relabeled as the other. Zero reference exceedances in these twelve comparisons
does not erase the preserved ordinary/side-washer steel exceedances.

The independent `audit01` reauthenticates 358 source pins and all 19 saved
output pins, integrates both contact pressure arrays in each state and checks
their active areas and spring energies. The maximum force residual is
1.18e-12 N and the maximum signed first-moment residual is 7.46e-11 Nmm.
It also replays the supported-domain quadrature and serialization checks.
It performs no plate assembly, contact solve, native solve, frame run or CAD
operation. Replay into a fresh output child:

```sh
uv run --no-sync python docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/upper-corner-screw-layout/rawlocal/washer-restricted-contact-completion/audit-replay.py --output docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/upper-corner-screw-layout/rawlocal/washer-restricted-contact-completion/audit02
```

| Completed output | SHA256 |
| --- | --- |
| `attempt03/receipt.json` | `bb235d56e850b93183a4bd9dc803e30850f0281ce51f6ae61e331985a3ab5804` |
| `attempt03/washer-restricted-contact-completion.json` | `32929970cc3fb04d9735e49af41d6da0d7ad4af8031a4369f251aca2c4cdd2c8` |
| `attempt03/end-states.jsonl` | `7dbfdae3c9921f67339b3ba36d58e4747863f1e2565c1ec8aa7434a420c5c9ce` |
| `attempt03/known-answers.json` | `12ae85e89c19afc0f87daabd1ecc8db7965c16fb13be19e803b77c1aa8743670` |
| `attempt03/mask-validation.json` | `3981c03ccced3361b9d98f9144c24710b22080bcd680436dd6106568484dccf3` |
| `audit01/receipt.json` | `d44080318b1160c0c7fad1c8382eac691f0663a7208c51a34174be75cba58fb6` |
| `audit01/audit.json` | `30098625b390851cd5ece89868118578a2316f9c297c83ff3b19ed7a0bf1580d` |
| `audit01/replay.py.snapshot` | `ca991b11cdb4028b97ead9ec8838431aa73168db78fa9a59eb9c15e27014156d` |

The mechanics runtime is 11.2106 seconds under Python 3.12.3, NumPy 2.5.2 and
SciPy 1.18.1. The authenticated `uv.lock` pins those same installed NumPy/SciPy
versions; the shared environment was not synchronized. The known examples and
mask integration establish their stated checks, while stress convergence,
three-dimensional edge behavior, product strength, the hypothetical 5 mm
pressing land and wood contact stiffness remain limits. The force prescription
is isolated from shaft/frame compatibility. These are conditional numerical
comparisons, not delivered washer resistance or a complete joint strength pass.

Active retained files are these two owned leaves, the ignored reproducible
audit helper and this packet's ignored inputs, successful arrays/receipts and
failed attempts. No source or historical run is a pruning candidate here.
