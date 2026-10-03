# First-order common-shaft knee witness

> Parent receipt annotation: the coupon matched and the selected witness
> returned exit 0; its independent physical closure was accepted for the local
> method. The original suite's ten closures/fourteen numerical stops are
> preserved. The parent's subsequent contact-entry correction closes all 24:
> bounded K loaded-shaft method COMPLETE, conditional. See the final annotation.
> The preparation record below
> remains the original frozen context; the executable producer is unchanged.

**Prepared source and boundary contract; mechanical execution remains with the
parent.** This packet supplies one engineering coupon and one governing loaded
state. It does not contain a mechanical result or qualify hardware, timber, or
the whole knee group. The finished 24 bearing fields, 96 static endpoint fields
and 96 geometric placement witnesses remain frozen.

## Frozen boundary and finite scope

The selected analytical force source remains `operators-attempt02` assessment
`1a82cd2a`, model `b5f9b87b`, rows `cdf21878`, comparison `bea6cbc3` and response
`06251964`. The parent's separate 50 mm frame work is outside this contract.
[Source](knee-compatible.py) joins all four continuous knee-side bolts and six
saved force states by metadata and signed wrench arithmetic. It prepares only
`a12-left / knee_outer_left_side_1` for mechanical execution, selected by the
existing same-state 92 ksi convex screen peak (`0.9228431822028651`). That screen
value is a selection reference, not a new resistance assertion.

| Physical shaft | Three receivers, head to nut | Grip intervals from head wood face, mm | Current rows: two lateral planes; one axial tie |
| --- | --- | --- | --- |
| `knee_outer_left_side_1` | left spine; left base side; left inner frame block | 0–38.1; 38.1–127.0; 127.0–215.9 | Bound exactly in the machine contract; selected witness has 72/73, 74/75; 1540 |
| `knee_outer_left_side_2` | left spine; left base side; left inner frame block | Same three intervals | 76/77, 78/79; 1541 |
| `knee_outer_right_side_1` | right spine; right base side; right inner frame block | Same three intervals | 88/89, 90/91; 1546 |
| `knee_outer_right_side_2` | right spine; right base side; right inner frame block | Same three intervals | 92/93, 94/95; 1547 |

The machine contract retains the full precision intervals, reference bore
endpoints, source geometry identities, receiver grain vectors and source row
laws for each shaft. Underhead intervals are 1.651–39.751,
39.751–128.651 and 128.651–217.551 mm. Each reference bore is 7.5 mm diameter
around a 6.35 mm shaft, with 0.575 mm radial clearance. These are the frozen
modeled grip and bore dimensions; delivered shank and physical head-to-nut
order are unobserved. The 241.3 mm occupied modeled shaft length does not become
a purchase instruction or elastic grip length.

For the selected witness, `n = (+1,0,0)` and transverse basis
`B = [(0,0,1), (0,-1,0)]`. The common datum is
`(-1174.7500000000002, -106.22808665153461, 331.31555301851245)` mm.

| Receiver | Connector force on receiver, N: X, Y, Z | Connector moment about common datum, Nmm: X, Y, Z |
| --- | --- | --- |
| `knee_outer_left_spine` | +95.460109, −512.957417, +422.165509 | 0, +18765.256889, +22800.957191 |
| `base_side_left` | 0, +502.672780, −545.112270 | 0, −13300.273358, −23258.109315 |
| `knee_outer_left_inner_frame_block` | −95.460109, +10.284637, +122.946761 | 0, −5464.983531, +457.152124 |

The exact unrounded boundary is recovered independently from the current
operator: for each receiver, `F = −Dtransᵀ f` and
`Mdatum = −1000 Drotᵀ f + (body_datum − common_datum) × F` using exactly its
five per-bolt rows. The factor 1000 reverses the operator's scaled rotation
coordinate. These full wrenches are compared with the frozen signed point
wrenches. Moment components along the shaft are only roundoff in this source;
a nonzero shaft torque or middle axial load would require a different input
contract and produces an explicit stop.

External receiver drives are the negatives of the listed connector wrenches.
The two plane vectors remain signed: `(422.165509, 512.957417)` N and
`(−122.946761, 10.284637)` N. The one physical tie is `+95.46010885208088` N.
No lateral resultant is substituted for the full wrench, and no second axial
tie is created. Whole-body loads, neighboring bolt actions and face contact
remain outside this isolated bolt boundary.

## Smallest common-shaft model

One continuous Euler–Bernoulli shaft spans the three frozen receiver intervals.
Eight elements per interval give 24 elements and 25 nodes. Both bending
directions share a circular radial contact law and the same shaft. Each rigid
receiver has two transverse translations and two tilts about the common datum:
112 variables before fixing the middle receiver's four rigid pose coordinates,
108 afterward. That fixation removes the common transverse rigid motion; it
does not discard the middle receiver's bore field or wrench closure.

The single K20 hypothesis reuses the frozen pure `hermite`, `annulus` and
`series_contact` functions from
[upper-right-combined-transfer.py](upper-right-combined-transfer.py). Only
its private Hermite grip scale is set to 215.9 mm. Its pair assembly, force
selection, main program and stiffness sweeps are never called. The constants
remain `Ebolt = 200000 MPa`, bore and wood-seat stiffness `20 MPa/mm`, and
hypothetical head-contact stiffness `10000 MPa/mm`.

At each three-point longitudinal Gauss sample, the relative transverse vector
is the shaft displacement minus the receiver's straight bore line. With
`r = |relative|`, `gap = 0.575 mm` and `a = max(r − gap, 0)`, the integrated
force on wood is `K20 × diameter × weight × a × relative/r`. The force on the
shaft is its opposite. The two components use the same radial penetration;
independent square-clearance springs are not used. This local foundation is
a conditional compliance hypothesis. It does not change the analytical frame's
four existing bilateral lateral row laws.

Both outer ends retain head/nut–rigid-washer and washer–wood compression-only
annular contacts in series. Each end transfers the **full single tie tension**,
with a derived end couple from its relative shaft/receiver tilt. The centered
annuli reuse the frozen hypothetical 5 mm head/nut flat-circle radius,
8.3058 mm maximum washer ID and 18.4658 mm minimum washer OD. This does not
observe delivered bearing profiles or provide washer bending resistance.

The ordinary first-order model omits **all T-dependent geometric stiffness,
geometric shortening and preload stiffness**. It retains beam bending, the
prescribed single axial tie and direct normal compression:

```text
required_outer_opening = T L/(E A) + head_stack_closure + nut_stack_closure
```

The middle receiver has no axial load from this bolt. Its normal pose and the
outer pair's common normal translation are undetermined by this isolated
force boundary. Frame poses are not imposed as a second boundary condition.
No friction, preload, material branch or geometry sweep is introduced.

## Independent physical closure

The witness reconstructs each receiver's force and moment by summing actual
modeled bore sample forces and full annular normal point tractions at the
**reference geometry**, about the same common datum as the source. This is
separate from the energy gradient. Each outer end saves pressure, quadrature
area, reference point and point force for both contact surfaces; all three
receivers save their bore fields.

For an end with normal sign `s` (`+1` head, `−1` nut), the physical annular
offset associated with the scalar contact coordinate is `−s B unit_tilt x`
with its perpendicular circular coordinate. Thus `Σ(offset × normal_force)`
recovers the end couple with its physical sign at each end. The head contact
acts on the shaft; the wood contact acts on the receiver. Their integrated
couples must be opposite after the internal washer moment balance. Reference
point tractions include no displaced-geometry prestress couple.

The output compares all three recovered six-component wrenches to the current
`D` boundary, including the middle receiver. Newton convergence alone cannot
produce the conditional equilibrium status. The inherited local numerical
tolerance is `1e−6 N` in scaled coordinates, `1e−6 N` in recovered force and
`215.9e−6 Nmm` in recovered moment; these are arithmetic closure tolerances,
not new joint qualification criteria. An unsuccessful solve saves its accepted
iterate, fields, residuals and a method/boundary defect. It makes no hardware or
timber failure claim.

## Parent execution: coupon, then one loaded witness

Preparation imports no mechanical helper and performs no mechanical assembly
or solution. Mechanical modes explicitly require the frozen contract. The
coupon checks a quadratic beam field with known constant curvature and exact
endpoint moments, a uniform 0.01 mm bore indentation in all three receivers,
a shared rigid line, direct axial compression, head/nut traction signs and
the `1000 × rotation`/`L × slope` work scales. Known-answer expressions include:

```text
constant-curvature beam: U = 0.5 E I c² L; end scaled moments = ±E I c/L
uniform bore: q = 20 × 6.35 × 0.01 = 1.27 N/mm
receiver forces: 48.387, 112.903, 112.903 N
global/D/local virtual work example: 5.19 Nmm in all three coordinates
```

Preparation below was already executed as metadata arithmetic. For a fresh
reproduction, choose a new preparation child directory and use its contract
path. The parent starts with the coupon command and then runs the witness,
serialized from the repository root. Existing output directories are refused,
so an executed attempt is preserved.

```bash
KNEE_PACKET=docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/upper-corner-screw-layout
.venv/bin/python "$KNEE_PACKET/knee-compatible.py" prepare \
  --out "$KNEE_PACKET/rawlocal/knee-compatible/prepare-attempt02"

.venv/bin/python "$KNEE_PACKET/knee-compatible.py" coupon \
  --input "$KNEE_PACKET/rawlocal/knee-compatible/prepare-attempt02/input-contract.json" \
  --out "$KNEE_PACKET/rawlocal/knee-compatible/coupon-attempt01"

.venv/bin/python "$KNEE_PACKET/knee-compatible.py" run \
  --input "$KNEE_PACKET/rawlocal/knee-compatible/prepare-attempt02/input-contract.json" \
  --coupon "$KNEE_PACKET/rawlocal/knee-compatible/coupon-attempt01/coupon.json" \
  --out "$KNEE_PACKET/rawlocal/knee-compatible/witness-attempt01"
```

The coupon receipt binds its input and executed producer hash. A matching
coupon is the owner's stipulated method check before the witness, not a new
engineering gate. The CLI intentionally exposes only the one selected loaded
state. A full suite is outside this implementation; the parent can decide
whether it is justified after inspecting the coupon and independent physical
closure of this witness.

## Receipts and present disposition

The prepared machine contract contains all direct source paths, SHA256 values,
byte counts, 24 signed per-bolt boundaries, frozen field/witness pointers and
model limits. Each mode saves its exact producer and an execution receipt.
Nested historical geometry sources remain provenance; no CAD materialization
or placement computation is performed.

The final preparation is
[input-contract.json](rawlocal/knee-compatible/prepare-attempt02/input-contract.json),
with [machine receipt](rawlocal/knee-compatible/prepare-attempt02/receipt.json).
The earlier metadata-only `prepare-attempt01` is preserved; its producer lacks
the final guard against helper bytecode writes and is not the parent input.

| Frozen prepared item | SHA256 |
| --- | --- |
| Executable producer | `8bfd4aab145e468f477a04a23073feebab9d9c3a0b4bb4cc1bc2407399fb3413` |
| `prepare-attempt02/input-contract.json` | `f2876952e6b71d59acdbf20dacaef233444402e50bfcc6d3b9ec1967f2cad01f` |
| `prepare-attempt02/receipt.json` | `25acba27d7e5586e4875121a04cd1b3f918f31acb92747101a37b4940b72ed7b` |

All 13 direct source hashes matched. Across the 24 source boundaries, maximum
operator-versus-saved point-wrench differences are `8.640199666842818e−12 N`
and `4.94765117764473e−10 Nmm`. The machine contract is 611,879 bytes;
NumPy 2.5.2 and Python 3.12.3 performed preparation. Ruff passed. Neither
mechanical mode, a native solver, a frame solve, CAD, software tests nor an
agent review was executed.

| Item | Present disposition |
| --- | --- |
| Current full-wrench force boundary | Available; source operator and saved point-wrench arithmetic joined |
| Frozen bearing/static endpoint/geometric placement results | Reused within their recorded scopes |
| First-order K20 common shaft and both normal end transfers | All 24 current states close with unchanged physics after the parent's numerical contact-entry correction; bounded K method COMPLETE, conditional |
| Engineering known-answer coupon | Original beam/contact coupon and parent's three-case analytic contact-entry coupon matched |
| One governing loaded witness | Parent selected witness closed; original bytes reused in both suites |
| Whole-group force redistribution, full elastic timber and actual hardware/wood acceptance | No result asserted by this packet |

The preparation's coupon and `a12-left / knee_outer_left_side_1` witness were
executed by the parent; subsequent suites now complete the bounded K method.
No finished bolt, seat or placement
requirement is reopened. No frame, native, CAD, test, review, staging or commit
operation is part of this packet.

## Parent coupon and selected witness receipts

The parent executed the stipulated engineering coupon and the single selected
`a12-left / knee_outer_left_side_1` witness using the unchanged producer
`8bfd4aab145e468f477a04a23073feebab9d9c3a0b4bb4cc1bc2407399fb3413` and contract
`f2876952e6b71d59acdbf20dacaef233444402e50bfcc6d3b9ec1967f2cad01f`.

| Parent artifact | SHA256 |
| --- | --- |
| [Matched coupon](rawlocal/knee-compatible/coupon-attempt01/coupon.json) | `c76aacdd80d42adc6ae7a080ea3ae3ab4b614cb1dcce2709a429e764a11fa1cd` |
| [Coupon receipt](rawlocal/knee-compatible/coupon-attempt01/receipt.json) | `515f38a54c30b961f8c9edbd9de0f49f73b8e52f6bd5f4eee71de01778240482` |
| [Selected witness](rawlocal/knee-compatible/witness-attempt01/witness.json) | `866817f4c62ab542b6c79e5912a01777c5322930aaf21a96ea4be7b9125ee246` |
| [Selected receipt](rawlocal/knee-compatible/witness-attempt01/receipt.json) | `7088673c7e3b1afa78e2a53438bff9e9f475444f1014a7fc018329156df2eb27` |

The parent reported exit 0, `conditional_first_order_equilibrium`, and accepted
the local method's three-receiver physical closure. Its 20 Newton history
entries finish with maximum independent force residual
`1.3066188131460876e−9 N` and moment residual `1.7136562746600248e−7 Nmm`.
No solve was repeated to add this annotation.

The required reference outer-center opening is `−0.23879147621049318 mm`.
This is the **rocking center position** of the tilted annuli; compression-only
point pressures remain nonnegative while the single tie remains
`+95.46010885208088 N`. A negative center closure does not mean negative
physical tension. No center-pose bound is introduced.

Cached array arithmetic gives the existing corner smooth-beam envelope proxy
peak `192.47938729087358 MPa` at `x = 60.32499999999993 mm` (element 9), with
same-position bending `4762.395472545951 Nmm` and shear approximately
`28.0067 N`. Its ratios to the exact declared 634.317671 and 310.264078 MPa
sensitivities are `0.3034432053381555` and `0.620372775770947`. This is a smooth
section sensitivity diagnostic, not actual hardware acceptance or inherited
static endpoint capacity.

The separate [finite suite adapter](knee-compatible-suite.md) preserves this
original witness exactly and prepares only 23 new states to cover the four
shafts and six cases. The original source and force contract stay frozen.
The isolated force-boundary limit remains; no shared-group/body-pose claim or
blanket new prerequisite is added.

## Parent finite suite terminal annotation

The parent executed the separate frozen `97984020…990304` suite adapter once:
**exit 2**, `STOP_finite_suite_method_defects`. It reported all 24 states,
reusing this accepted original witness exactly and returning fields for all
23 new API calls. The original `8bfd4aab…fb3413` producer is unchanged.

| Frozen suite artifact | SHA256 |
| --- | --- |
| [Suite result](rawlocal/knee-compatible-suite/suite-attempt01/suite.json) | `0d7dff18b38d82130be212b1fc53fbb18a97c0e6f0c3a8c4a13e58fa3375910f` |
| [Suite receipt](rawlocal/knee-compatible-suite/suite-attempt01/receipt.json) | `3180d95e9b7f146da7bc2dce40ec3d88c10b6152e3da9f06b70e11a9226187f1` |

Exactly ten states close: all three A12 cases on both left shafts (six), and
both K12 cases on both right shafts (four). Exactly fourteen stop: both K12
cases on both left shafts (four), all three A12 cases on both right shafts
(six), and A1-rear on all four shafts (four). The
[suite execution annotation](knee-compatible-suite.md#parent-finite-execution-annotation-10-closures-14-method-stops)
lists the full PASS/STOP census and each stopped residual witness.

All fourteen stops save `Local iteration budget exhausted; compatibility has
not been established`. The largest independent force residual is
`80.91779812923494 N`, at right side 2 / A12-left / `base_side_right` Z;
the largest independent moment residual is `9929.93028164206 Nmm`, at left
side 2 / A1-rear / `base_side_left` Y. These retained-iterate method defects
make no physical failure claim.

Restricted to the ten physically closed states, the same-state peak remains
this reused original witness: **192.47938729087358 MPa** at
`x = 60.32499999999993 mm`, with declared 92 ksi and 45 ksi sensitivity ratios
**0.3034432053381555** and **0.620372775770947**. Stopped-iterate stress and
pressure are not accepted equilibrium predictions. The negative outer-center
opening remains the rocking-center position with positive physical tie and
nonnegative annular pressure; no pose bound is added.

At that frozen original-suite terminal, the finite K requirement remained
open for the exact fourteen stopped states. The subsequent numerical correction
and completion are recorded below. Only cached
hashes and saved arrays were inspected for these annotations; neither code,
physics nor results were changed, and no mechanics were repeated.

## Parent contact-entry completion: bounded K method COMPLETE, conditional

The parent-owned frozen `knee-contact-entry.py` producer
`dd20bb23b96e7e7e5f913a573108e1274b13179a7420c5fae01e3653fcae6bd8` changes
only the loaded-neutral numerical step: exact forward entry into an inactive
circular bore followed by the unchanged Armijo/Newton rules. All laws,
stiffnesses, gauge, tolerances and first-order physics remain unchanged.
Its three-case analytic circular-foundation coupon matched with maximum pose
error `3.774758283725532e−15 mm`.

The parent's corrected suite reports `conditional_first_order_equilibrium_all24`:
ten accepted old state files reused exactly and fourteen new closed states,
covering four shafts and all six cases. Each state retains two signed lateral
planes, one physical axial tie and independently recovered full wrenches for
all three receivers. Maximum receiver residuals are
**8.178873613928772e−7 N** and **4.6654471134388587e−5 Nmm**.

| Frozen corrected artifact | SHA256 |
| --- | --- |
| [All-24 suite](rawlocal/knee-contact-entry/suite-attempt01/suite.json) | `b707952e5ad740ad2ebc0306bce17a37e4718e88c1164cba568d9a39a6e8b79a` |
| [Terminal receipt](rawlocal/knee-contact-entry/suite-attempt01/receipt.json) | `63224d7d4e25bd8705123f75dc60663f6b4fcb8ab998d149ed2507ec79ee5e43` |

The accepted all-24 same-state peak remains the original byte-identical
selected witness: **192.47938729087358 MPa**, with exact declared 92 ksi / 45 ksi
sensitivity ratios **0.3034432053381555 / 0.620372775770947**.
The [contact-entry evidence](knee-contact-entry.md) records all four shafts'
bore and seat pressure maxima, full-annulus mean indices and exact raw hashes.
The negative reference center opening remains a rocking-center position with
positive tension and nonnegative annular compression; no pose bound is added.

**The bounded K loaded-shaft method is COMPLETE, conditional.** The preserved
fourteen numerical stops introduce no remaining state requirement here.
The isolated force-boundary limit remains; no shared-group/body-pose claim,
other capacity inheritance, actual hardware/wood acceptance or physical
release is asserted. No code or mechanical execution was changed for these
final documentation annotations. Publication returns to the parent.
