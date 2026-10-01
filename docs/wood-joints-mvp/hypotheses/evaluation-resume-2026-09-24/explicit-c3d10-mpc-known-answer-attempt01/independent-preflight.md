# Independent preflight: explicit C3D10 mass-coordinate fixture

This is an independent source and analytical review of the proposed one-element
fixture. It is preparation evidence only: I did not execute CalculiX, freeze
inputs, or interpret any native output. I reviewed both prepared decks and
their output requests against the pinned source; native-output behavior remains
unobserved until the parent-owned run.

The source authority is the repository-pinned CalculiX 2.23 source archive
[`source.tar.bz2`](../ordinary-external-force-transient-attempt04-diagnostic/build-attempt02/source.tar.bz2)
and local cache `/tmp/ccx_2.23.src.tar.bz2`; both hash to
`9c88385c10fb04f5dc6c4e98027a51bebdd8aee3920e05190d6c1dd08357d6e7`.
The extracted files below are under
`/tmp/ccx223-src/CalculiX/ccx_2.23/src/`.

| Source | SHA-256 | Relevant lines |
| --- | --- | --- |
| `e_c3d.f` | `d009650b48e5ca150080aed9e19d1b65d2b2cf4869ab6d7f2b1a5cd55e2df3fc` | 1921–1974 |
| `mafillsm.f` | `d6073d5bfd9ad56a03a25b8c79ad1bb2dd178e48e3db3b9dd951f612b0197602` | 384–432, 462–550 |
| `add_sm_ei.f` | `1ab496881ebb7cd025c0aa91d0a9a39b379c02e60432d4c1fdf6b8bea0a0dc07` | 33–62 |
| `dynamics.f` | `d861c936c204853e84e7647b4164e78556c11b6eb0a532b623d4a75622f53e5e` | 99–120, 248–270 |
| `nonlingeo.c` | `8684bb6d7fa7097c0a854db5a45eb9e2d11adfde574e688184ecbbbad56ff83f` | 905–906, 1018–1057, 1333–1341, 1418–1435, 2792–2795, 3437–3465 |
| `resultsini.c` | `5dbd3d938722b157568a975091dde7baf738c564bd747ed7e0978f0d84222256` | 89–95 |
| `iniparll.c` | `0ef82bbe88714322ad7e97ce3aa6f03b21ace29fdcf8301fc290373728e45472` | 140–163 |
| `prediction.c` | `dfe7d10315342e7a59af6fcfb0f251f1a6f2b1c53e0f20ad402de6422c587525` | 44–80 |
| `calcresidual.c` | `9f8b0528c2b7853df4b779d142808c74115318e315979dda2b0f3bef1e3af1a7` | 100–109 |
| `tempload.f` | `8933ca0a5bb9fa3db2b55b4ec9344be9dca1297763f5ea28f6ef7c9074ea84aa` | 356–372 |
| `writecvg.f` | `cffd7f25dbae489807f7d06df27b2dc16e8de10a4086a93f08b4be1e7fd44cd4` | 19–83 |
| `printoutelem.f` | `e5da47dd83dd8e796fcbf8ec81e220b5139211b8f411c03adb17a782436e2544` | 63–73, 519–542 |
| `frdheader.c` | `25eb79d5f71a096ef1cacfe20105cc26d64ca17581a69e21ed2a7424556db5cb` | 33–42, 92–156 |
| `openfile.f` | `e5e8215d1e400aa74bfb6e63e335fac69540a7de9a3388ac36ef2d69f33ad860` | 56–84 |
| `noelfiles.f` | `ed85b45d6987882e484f11a0be3dc9c2d716afba07d59483d364e0709107a59f` | 201–220, 350–384, 420–424, 538–548 |
| `nodeprints.f` | `db829506135c873ec4236fbb71296f3c4c252888e02fdc41cf2609be9e711f6b` | 54–74, 106–120 |
| `elprints.f` | `15d4ad6001e3ecb4eeaa05cba39333626b6c079cbe9d696879092dc2c73ff7b7` | 106–120, 237–267 |
| `printout.f` | `ae2b60b4e086846e2833a1d723c37645c0ff6701d2e28dc7e3163d0a4d136f32` | 114–140, 341–385, 575–594 |

The proposed straight tetrahedron has volume `1/6 mm³`. With density
`6 tonne/mm³`, its physical mass is exactly `1 tonne`. CalculiX 2.23's explicit
C3D10 lumping uses `alpha=0.1203` and assigns the corner group the fraction
`alpha/(1+alpha)` and the midside group `1/(1+alpha)` of total element mass.
The resulting nodal masses are:

- four corners: `1203/44812 tonne = 0.0268454878157636 tonne` each;
- six midsides: `5000/33609 tonne = 0.148769674789491 tonne` each.

The exact group totals are `1203/11203` and `10000/11203` tonne, which sum to
one. The proposed physical force `f_i=m_i·1 mm/s²` therefore has numerical
value `m_i N` in this unit system because `1 tonne·mm/s² = 1 N`; the ten
applied forces sum to `1 N`. I independently recomputed these sums with exact
rational arithmetic. The reviewed `parent-oracle.py` currently hashes to
`c09b6cde8c19b84645d68bc92e0695b4dab38f0105717374944b828f18b891b0`. It
passes as `PASS_INDEPENDENT_COORDINATE_INVARIANCE_ORACLE` under the repository
`.venv/bin/python`; system `python3` lacks NumPy. The oracle compares the exact
full reduced-mass response with the diagonal-only hypothesis and makes no
native execution or acceptance claim.

For direct coordinates, with U2/U3 fixed on all ten element nodes, constant
U1 acceleration `1 mm/s²` gives the rigid solution
`U1(t)=t²/2 mm`, `V1(t)=t mm/s`, zero strain and zero `ELSE`, and total
kinetic energy `t²/2 N·mm`. For the MPC case, take physical nodes 1–10 and
non-element controller node 11, with node 1 U1 dependent and
`u(1,1)+u(2,1)+u(3,1)+u(4,1)-4u(11,1)=0`. This is a rank-10 coordinate
reparameterization of the ten physical U1 coordinates: every direct physical
motion remains representable, and rigid translation sets controller U1 to
the same displacement.

The failure signature is strong. Let `M` be the stated diagonal physical
lumped mass and `T` map independent coordinates `[u2,u3,u4,u5,…,u10,q11]`
to the ten physical U1 values, with `u1=4q11-u2-u3-u4`. A full reduced solve
`(TᵀMT)q̈=Tᵀf` returns all physical accelerations equal to one. The pinned
source instead assembles MPC-transformed mass entries into diagonal and
off-diagonal storage (`mafillsm.f`; `add_sm_ei.f`) and the ordinary explicit
update divides by `adb` (the diagonal) alone (`nonlingeo.c` 1333–1341).
Under that diagonal-only hypothesis, reduced `q11` has mass `16mc` and force
`4mc`, hence acceleration `0.25`; independent corner coordinates u2–u4 have
zero reduced force and zero acceleration; the six midside accelerations are
one. Expanded physical initial accelerations are therefore
`[1,0,0,0,1,1,1,1,1,1]`, compared with ten ones in the direct case. The
predicted initial momentum rate is `41203/44812 N = 0.9194635 N`, versus the
`1 N` applied force. This prediction is an initial-acceleration diagnostic,
not a claim about the later native history: once mapped motion is nonuniform,
elastic internal forces alter subsequent states.

For `*DYNAMIC,EXPLICIT=2,ALPHA=0`, `dynamics.f` recognizes explicit mode and
the alpha option; `nonlingeo.c` sets `beta=(1-alpha)^2/4=0.25` and
`gamma=0.5-alpha=0.5`. The initial acceleration is computed from force minus
internal force divided by the assembled explicit mass, then seeded through
`resultsini.c`/`iniparll.c` using a tiny special time increment
(`nonlingeo.c` 1418–1424). At each accepted step, `prediction.c` predicts with
the old acceleration and the `resultsini` correction applies the change in
acceleration; for constant acceleration and zero internal force the two
quarter-step terms sum to `0.5·a·dt²`. `tempload.f` confirms that an
unamplified CLOAD stays constant for `nmethod=4`. Leaving DIRECT absent keeps
the adaptive explicit increment logic. For this no-contact fixture, leave the
minimum increment blank: the source substitutes a tiny default floor
(`dynamics.f` 248–270), while `nonlingeo.c` initializes `mscalmethod=0` and
selects increments from the stable increment and user bounds (1018–1057).
The declared small maximum increment should fall below the element's stable
increment, so no increase to a large minimum is requested. This
no-mass-scaling statement is specific to those input controls; explicit
models with another minimum/contact-scaling path require their own check.

The source-backed accepted-state contract is FRD-based. `frdheader.c` documents
that its `1PSTEP` record carries the FRD loadcase counter, increment (`iinc`),
and step (`istep`) at columns written on lines 33–42; its `100CL` record carries
the actual output time and FRD counter on lines 92–156. In `nonlingeo.c`, the
accepted-increment branch advances `iinc` and `jprint` at lines 1520–27. The
explicit branch is selected at lines 3461–78. With `FREQUENCY=1`, the output
condition `jout[0]==jprint && icutb==0` at lines 3626–30 selects each accepted
increment; lines 3724–32 pass `ttime+time`, `istep`, and `iinc` to FRD. Thus
FRD `(step, increment, time)` records—not a presumed 100 increments—are the
canonical accepted-state sequence. Require step 1, increment 1 followed by
contiguous increments with unique and strictly increasing times, every expected
field block and all ten physical node records at every frame, and terminal time
0.1 s after normal native completion.
Join DAT print/energy tables to those frames by actual time and require matching
complete coverage. This deck has one `*STEP`, so its step is known from the
input; DAT headings include actual time (`printout.f` lines 114–140 and
341–385), but do not independently identify the FRD increment. The verifier
must not claim a DAT increment identity it cannot parse from printed output.

STA/CVG and stdout cannot supply a per-increment gate for this explicit branch.
`openfile.f` lines 56–84 opens `.sta` and `.cvg` with only their column headers;
the `writecvg` call at `nonlingeo.c` lines 3437–38 is inside the `iexpl<=1`
implicit branch, before the explicit `else` at 3461. The per-increment stdout
table is likewise guarded by `iexpl<=1` at lines 1607–15. A verifier should
allow header-only STA/CVG files and no stdout iteration trace; require terminal
process/container success and source-backed FRD/DAT completeness instead.

The reviewed refreshed deck hashes are `direct=5929594f1e415d82d392990ce26c63944a685a6a9fe27ae2cc1aeecfee20cbc4`
and `mapped=7de9a6fa810bba7a3ce8676d4d4fa1322527df1949fe6501de2cdbd44585a286`.
Both contain the same physical C3D10 connectivity, material, ten source-derived
constant CLOAD values, U2/U3 restraints, `*DYNAMIC,EXPLICIT=2,ALPHA=0` with
initial/max step 0.001 s, total period 0.1 s, blank minimum, no `DIRECT`, and no
mass-scaling card or load amplitude. The mapped deck adds node 11, the single
five-term equation with physical node 1 U1 as first/dependent term and free
controller U1, fixes only its unused U2/U3 components, and requests controller
U in DAT. That matches the intended physical-coordinate reparameterization.
Both request physical U/RF/V in DAT and FRD and ELSE/ELKE/EMAS/EVOL totals in
DAT; mapped controller U is DAT-only; both request ENER in FRD. The final
`*EL FILE,FREQUENCY=1` card omits an `ELSET` selector because the pinned 2.23
file parser has no such `*EL FILE` parameter; with one element in this fixture,
the unfiltered request covers the intended element. Pinned parser source
recognizes the requested labels (`nodeprints.f` 54–74, `noelfiles.f` 350–384
and 420–24, `elprints.f` 237–67). `FREQUENCY=1` is parsed into the cadence by
the DAT node/element print parsers (`nodeprints.f` and `elprints.f` lines
106–20) and by the FRD file parser (`noelfiles.f` lines 201–20).

One DAT parser detail is material: `EMAS` output includes more than its total
mass. `printout.f` lines 575–94 emits the total-mass scalar, then inertia and
center-of-gravity tables; parse the first scalar under “total mass” as the
1-tonne oracle, and do not treat later rows in that block as duplicate mass
values. The exact printed ENER block has not been observed; its role remains a
zero-strain diagnostic rather than kinetic-energy evidence.

After the preparation refresh, read-only `.venv/bin/python prepare.py --check`
returned `PASS_PREPARATION_ONLY`. The refreshed expected contract SHA-256 is
`4af0ab473cf4eeb0b8750fe07b38af9bcd14381af4ace5ca57726cf5c85331fb`; it binds
the FRD state sequence and DAT-by-time join described above. The refreshed
deck SHA-256 values are `direct=5929594f1e415d82d392990ce26c63944a685a6a9fe27ae2cc1aeecfee20cbc4`
and `mapped=7de9a6fa810bba7a3ce8676d4d4fa1322527df1949fe6501de2cdbd44585a286`.
The packet remains preparation-only; this check does not freeze inputs or run
CalculiX.

This fixture only checks explicit integration under a harmless
coordinate-reparameterization of one declared lumped element. It does not
qualify general MPC behavior, contact, the 19-body joint model, current-joint
mechanics, or engineering acceptance. Deck cards and output requests have
passed this independent source review. No native results were reviewed, and
this note does not authorize freezing or execution.
