# Central partial-seat transfer: finite static route for gap P

Only `center_principal_right_2` on `base_principal_center_right` is covered.
The smallest declared route is direct compression through the already
supported central ring. A statically admissible washer stress field can carry
the current approximately 23 N axial tie without loading the unsupported
crescent. This is a conditional plastic transfer bound, with an explicit
footprint and ductile material hypothesis. It is not a measured contact field,
an elastic stress bound, an exact-product resistance, or closure of the whole
joint. Parent retains the disposition of gap P.

The trial route uses fixed geometry and small deformation plastic limit
analysis. It gives no result for geometry instability or cyclic shakedown.

## Completed inputs and exact finite masks

The seat is `(50.95, -90.30983137880766, 367.0102220661388)` mm, inward along
global `+X`. The unchanged finished STEP is
`9053a7210a781e919038a4a823f867325dd5c78907bd028d8b9e76dc0b46df58`.
The original [support result](../partial-seat-footprint-attempt02/result.json)
is `ffba33b640e3ae00e61049664a603cdb6fe27cf7561f0068a735878ed8e3bf1b`:
the 10/7.3 mm ring has 36.68595 mm² support at inward depths 0.01, 0.05 and
0.1 mm. The [current saved ring](bolted-replay-results/central-seat-attempt01/result.json)
is `a058f494bc4a733e90c0ee954f38634abadceac4c24273b92dab4434cac42b33`.
It credits the 10/8.3058 mm subset, area 24.3580923073 mm², at those same
three depths. Its six ties are reused without opening a force array or
rerunning placement, CAD, or the frame.

Use coordinates `y=Y-seat_Y`, `z=Z-seat_Z`, with the load direction `+X`.
The [existing cut diagnosis](../../remaining-candidate-washer-seats-2026-10-01/cut-diagnosis-review.md)
binds the finished BREP to F1/G1 passage
`bore_base_principal_center_right_072`: radius 19.05 mm, global center
`(49.95, -72.95548222202063, 348.1769448188469)` mm, through the receiver
from `X=50.95` to `89.05`. The passage center in this seat plane is
approximately `(17.3543491568, -18.8332772473)` mm. Its nearest edge is
**6.5598763474 mm** from the bolt axis, beyond the credited ring's 5 mm radius.

Within the concentric maximum catalog washer radius, 9.5123 mm, the fixed wood
support mask is

```text
S: (y-cy)^2 + (z-cz)^2 >= 19.05^2
   and y^2 + z^2 >= 3.65^2.
```

The saved finished geometry has natural broad-face edge distances 44.45 and
95.25 mm at this seat. Its only opening intervals intersecting this washer's
grain-station span are the target bore (`facet007`) and passage (`facet013`).
The adjacent principal bolt is 53 mm away. Thus the expression retains the
actual local voids; it does not replace the passage with a straight edge or
an area reduction. This mask is for the fixed concentric source geometry,
not an envelope of shifted/tilted hardware or a proof of wood support at
arbitrary depth.

The [parent's existing conditional nut profile](../../mvp-integration-2026-10-01/conditional-nut-profile.json),
SHA-256 `d30a5e94e7adbd4b617ea85af8790955738025dbae26af544efc96b29fecab34`,
already defines finite initial flat lands: inner radius 3.556 mm, outer radius
5.5626 mm for H1 or 5.00635 mm for H2. Both concentric lands contain the
credited ring. Their 45-degree reliefs and clipping remain hypothetical;
the certificate gives no pressure to reliefs or the rest of the initial land.
No head circle is inferred from flats. A later relief contact state is outside
this certificate.

The finite masks are washer metal `W`, nut flat land `N`, and wood support
`S`. Their direct overlap is `D=W intersect N intersect S`. Credit only

```text
P: (8.3058/2)^2 <= y^2 + z^2 <= 5^2, with P contained in D.
```

Use the actual washer opening, not the 7.3 mm wood bore, as P's inner limit.
The declared washer dimensions are ID 8.3058 mm, OD 18.4658 mm and thickness
1.2954 mm, within the existing catalog envelope. This dimensional corner is
an explicit scenario, not a general conservative stress envelope. Assume
full-thickness flat metal columns throughout P. All of `W minus P`, including
the unsupported passage crescent, receives zero trial pressure and stress.
The actual full washer remains present; no smaller washer is introduced.

## Simplest sufficient conditional transfer bound

Let `A=pi*(R^2-a^2)` and `I=pi*(R^4-a^4)/4`, with `R=5` and `a=8.3058/2`.
For inward normal force N and signed moments My/Mz about the seat, choose

```text
q(y,z) = N/A - Mz*y/I + My*z/I on P; q=0 elsewhere.
sigma_XX = -q through the washer thickness; every other stress is zero.
q_min,max = N/A +/- R*sqrt(My^2+Mz^2)/I.
```

The field has zero divergence because q is independent of X. Across the
vertical boundary of P, its traction is zero on both sides; its stress jump
does not introduce a missing shear force. Equal opposing normal tractions on
the two washer faces carry N, My and Mz exactly. For `q_min >= 0`, every trial
contact traction is compressive. Von Mises stress is `abs(q)`. Therefore a
ductile, perfectly plastic washer with a separately declared yield floor
at least `q_max` admits this static field. Thickness does not enter this
equilibrium construction; no thin-plate approximation is used.

This is an application of the static plastic lower-bound theorem, which
requires equilibrium, boundary tractions, and admissible yield stresses.
It can use statically equivalent resultant loading where the pressure
distribution is free to redistribute. It does not establish first yield or
elastic displacement compatibility. [A. F. Bower, sections 6.3.5–6.3.6](https://solidmechanics.org/Text/Chapter6_3/Chapter6_3.php).

For the declared centered axial branch, My and Mz are zero except for recorded
source-coordinate roundoff. The governing saved case is K12-right:
**N=22.9523326431 N**, **q=0.9422877766 MPa**. Its conditional wood mean
comparison remains **0.2186676599** against **4.3092233082 MPa**. The bound
requires a hypothetical ductile washer yield floor of approximately
**0.942288 MPa** for this trial field. That number is a method threshold,
not a procurement specification or an assigned product capacity.

The nut is an explicitly rigid, parallel load spreader, with the stated ring
available for compression. The wood face supplies the declared normal
reaction field. No prescribed preload, pressure outside P, shaft-imposed
rocking, or other local nut wrench is included. Applying a pressure cap to
wood would be an additional constitutive interpretation: the recorded
Fc-perp mean comparison alone does not establish an ideal plastic wood law
or resistance of the passage ligament. Those existing wood duties remain
with their own evidence.

Under these hypotheses an equilibrium route exists. Missing delivered face
coverage and yield are material/profile limitations; they do not demonstrate
that this centered trial route needs a bridging solve. If the parent's
criterion requires an elastic contact field, avoidance of first local yield,
or service motion, this static collapse interpretation is insufficient.
The next method must address that specific requirement; a 3D/native solve is
not automatically a prerequisite.

## Signed demand and exact limitations

[central-seat-transfer.py](central-seat-transfer.py) binds all six saved
states and row 1535, `center_principal_right_2/outer-seat-axial-tie`, from the
current operator row map. It records all six signed wrench components on
the wood receiver about the nut seat:

```text
F = -signed_tie * row.ownership.direction_global_xyz
M = (row.ownership.point_mm - nut_seat_mm) cross F.
```

This is the complete wrench of that source tie, including roundoff, not an
invented local bolt-end wrench. The source supplies an axial spring, not
independent nut rocking moments. The pressure construction carries its normal
force and transverse moments; numerical Fy/Fz/Mx discarded by the axial
idealization are reported and limited to 1e-9 N/Nmm. A meaningful transverse
force or axial torque requires a different transfer field. A negative trial
pressure reports an insufficient ansatz, not an adopted joint failure.

The [product basis](washer-product-basis.md) supplies no guaranteed actual
flat nut bearing circle or centering, and no numerical washer yield.
K.L. Jack `25CNFH5Z` flats 10.8712–11.1252 mm and height 5.3848–5.7404 mm
do not establish those contact quantities. `25NWUS` ID 7.7978–8.3058 mm,
OD 18.4658–19.0246 mm and thickness 1.2954–2.0320 mm remain conditional
envelopes. Its low-carbon description establishes no Fy.

Exact remaining inputs for an actual-product interpretation are:

- Flat nut-land inner/outer radii and flatness at the contact plane, with
  nut/washer/wood offsets and tilt. For an offset nut annulus to contain P,
  sufficient conditions are `r_inner+offset <= a` and `r_outer-offset >= R`.
  The centered H2 radius leaves only 0.00635 mm outer coverage margin; its
  recorded permitted 0.222504 mm nut eccentricity does not guarantee P.
- Washer bore/edge profile throughout its thickness, flat face coverage and
  centering. At maximum washer ID the fixed P has no inner centering margin.
  The recorded 0.97790 mm washer play cannot be silently set to zero for a
  guaranteed delivered route. Required coverage is
  `washer_inner_radius+offset <= a` and `washer_outer_radius-offset >= R`.
- A product-bound ductile yield floor and applicability of the plastic
  interpretation. No 250 MPa default, Grade 5 bolt-to-washer transfer, or
  hardness conversion is used.
- Any preload and simultaneous additional local nut wrench or imposed
  rotation if included in the parent's criterion, and compatibility of the
  wood reaction interpretation with that criterion. No opposite head bearing
  profile is needed to define this isolated source-tie route; a claim about
  the complete bolt assembly would require its own head boundary.

## Owned preparation and next parent command

The producer authenticates direct completed source bytes, retains inherited
provenance without rerunning its producers, and writes only a fresh child of
`rawlocal/central-seat-transfer/`. Outputs are `contract.json`,
`coupon-readiness.json` and a hash receipt. It generates no native deck, mesh,
load history, solver/toolchain setup, or sweep. Without an explicit
`--washer-yield-mpa` hypothesis its numerical yield coverage remains null.
Even with that argument, delivered material and physical-release claims stay
false.

The prepared engineering known-answer specification uses radii 1/2 mm and
`q=3+0.5*y-0.25*z` MPa. Its exact signed wrench is
`[9*pi,0,0,0,-15*pi/16,-15*pi/8]` in N/Nmm, and its pressure extrema are
`3 +/- sqrt(1.25)` MPa. It also specifies refusal of a ring intersecting a
passage, an insufficient nut land, or tensile trial pressure. These are
bounded algebraic coupon inputs. The parent executed the positive signed
known answer and all six current ring integrals below. The three refusal
examples remain specifications; no result for altered geometry is asserted.

## Completed parent algebraic evaluation

The parent prepared the frozen contract once, without assigning a washer
yield value. It then integrated the affine normal pressures using eight
radial Gauss points and 32 angular points. The exact known-answer force and
moments matched within **2.132e-14 N/Nmm**; maximum error against the six
current signed source wrenches was **6.395e-14 N/Nmm**. The unsupported
crescent receives zero trial pressure. These are algebraic engineering
coupons, not a contact solve, software test or actual material qualification.

| Artifact under `rawlocal/central-seat-transfer/` | SHA256 |
| --- | --- |
| `preparation-attempt01/contract.json` | `e430c138f0e1fb4eacda278fa535d3e14400fcff3514f4a81d3a5f7fc3ac6646` |
| Same preparation `receipt.json` | `a1ac28b3b358e1a03a5bd26511774128804a9d45a46e4057cd006bafab1e9ad0` |
| `coupon-attempt01/coupon.json` | `bdc35b60ca03039f6e5acad8c5c81784086368a3472183ae7515f66335fe41bb` |

The executed coupon source is retained as `coupon-attempt01/produce.py`;
the result binds its SHA256 and the unchanged contract. The original
preparation's coupon-pending metadata remains preserved. The finite static
compression route is now demonstrated under its declared hypotheses;
actual flat-land coverage, installed centering, ductile yield and complete
bolt/wood resistance remain unqualified. It does not establish elastic
contact compatibility, first-yield avoidance or cyclic performance.

After parent freeze, the concrete preparation command from the repository
root is:

```sh
python3 -B docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/upper-corner-screw-layout/central-seat-transfer.py \
  --output docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/upper-corner-screw-layout/rawlocal/central-seat-transfer/preparation-attempt01
```

The finite next decision is whether the declared centered footprint and
static plastic route apply to gap P. If they do, parent supplies the explicit
material hypothesis and records that conditional disposition; the positive
signed coupon is already complete. If they do not,
retain this exact mask and obtain the missing signed local nut wrench/contact
boundary before selecting a more detailed transfer method.

The two source leaves and their possible ignored receipts stay active. No raw
run is proposed for archiving or pruning. This worker ran no producer,
coupon, software tests, review loop, mechanics, native solver, CAD or frame
execution; changed no geometry or hardware; and made no shared edits,
staging changes or commit.
