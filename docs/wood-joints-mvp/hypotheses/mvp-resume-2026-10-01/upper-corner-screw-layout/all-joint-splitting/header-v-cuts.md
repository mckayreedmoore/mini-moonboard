# Header Cleat V-Cut Consumer

## Purpose and authority

This consumer integrates the saved boundary fields over the frozen negative
side of each transverse `v` cut for six header-related cleats and six source
cases. It compares the original source-point wrench with the integrated field
plus its exact source residual. The source authority remains the reviewed 104
bolt axes and original six cases; the available 108-axis proposal remains
unadopted.

The consumer retains all other-interface point forces and free couples. It
replaces only saved `discrete_body_load` points with the existing
retained-timber gravity integral and allocated hardware point wrenches. The
source gravity whole-body wrench and each negative-half cut are checked before
comparison.

## Integrations

- Washer annuli use `disk_strip` for the outer disk minus the inner disk.
- Contact cells use exact rectangle-minus-disk area and both first moments.
  Each disk is clipped to both saved tile coordinates and the cut half-space;
  closed antiderivatives are evaluated between the circle/boundary events.
  This includes circles crossing tile boundaries. Saved disjoint voids and
  pressure laws remain unchanged; no contact law or stiffness is added.
- Lateral bore fields use `coordinate_roots` and `pressure_arc_wrench` for
  each saved half-cosine pressure profile.
- Each saved source action is split into its integrated field and an exact
  residual force/free couple at its original source point. Unsupported fields
  remain as their complete original source point action and are listed by row.
- Every output cut retains all six signed components. The existing normal-hull
  tensile lower bound and finite compression witness are reported for original
  and mapped inventories. No splitting capacity, material value, or joint
  acceptance is calculated.

Tiny source free couples remain exact point residuals. They stay in the
accounting even when their magnitude is near roundoff; they do not become a
new physical blockage by themselves. Larger frictionless-incompatible force
components remain explicit at their source point as well.

## Known-answer coupon

Parent runs this algebra-only coupon before the source consumer:

```sh
uv run python docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/upper-corner-screw-layout/all-joint-splitting/header-v-cuts.py --coupon-only
```

Expected values are: half-annulus area `10.5π mm²`, half-annulus first moment
`−78 mm³`, trimmed-cell area/first moments
`[50−π mm², 125−4π mm³, 0 mm³]`, and half-arc bore force
`[5, −10/π, 0] N`. These comparison tolerances are `1e-12` in the declared
units. The new contact integrator also reproduces the trimmed-cell cut and
checks full, half, quarter and translated clipped disks against analytical
areas and first moments. The disk/rectangle and translated clipped-cell
checks use `1e-11` in the declared units. The coupon carries no engineering
result.

## Frozen consumer command

The boundary output result SHA is mandatory. If the producer receipt is
available, pin it too so the consumer verifies its `result.json` binding and
rechecks overlapping source pins.

```sh
uv run python docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/upper-corner-screw-layout/all-joint-splitting/header-v-cuts.py \
  --boundary-result docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/upper-corner-screw-layout/all-joint-splitting/rawlocal/header-boundary/attempt01/result.json \
  --expected-boundary-result-sha256 <parent-recorded-result-sha256> \
  --boundary-receipt docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/upper-corner-screw-layout/all-joint-splitting/rawlocal/header-boundary/attempt01/receipt.json \
  --expected-boundary-receipt-sha256 <parent-recorded-receipt-sha256> \
  --output docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/upper-corner-screw-layout/all-joint-splitting/rawlocal/header-v-cuts/attempt01
```

Parent owns both commands and any source-data run. A fresh output child is
required; preserve earlier attempts.

## Completed comparison 01

Parent comparison 01 completed 36 body/case states and 3,024 `v`-cut limits
with no body-scope stops. Its 168 unsupported fields remained as exact source
points: 72 washer rows rejected by the boundary producer's opposite-normal
guard and 96 contact cells refused by the reused circle/tile integrator.
Thus the result is a partial placement comparison, not a completed physical
boundary integration or splitting qualification. The largest original and
mapped normal-hull tensile lower bounds are both `55.452556 N`, for the left
inner-knee block in `a12-forward`.

The source free couples are retained exactly; all 249 nonzero rows are below
the existing `1e-5 N·mm` component accounting tolerance. They do not establish
a physical moment-transfer blocker. New runs must use the corrected boundary
producer and complete clipped-cell integration. Comparison 01, its snapshot,
cut archive and receipt remain preserved.

| Artifact | SHA256 |
| --- | --- |
| `result.json` | `298b310f90c6556c2eef72338e8d4dc2a6f03bdd41a3b45b48a5e8aa6833cc32` |
| `v-cuts.jsonl.gz` | `df21a56def68448aa02790432709ae41dc922fbb1bb9672980982745aa8403f8` |
| `receipt.json` | `ed7dee7dda8d43662f10d38c8c88ecadf70de86b1c175069b7a644d8b6c2efda` |

## Completed comparison 02

Parent ran the new analytical contact coupons, corrected boundary preparation
06 and comparison 02. All 36 body/case pairs and 3,024 `v` limits complete
with zero unsupported fields and zero body-scope stops. The 72 washer and 96
contact-cell fallbacks in comparison 01 are eliminated. This completes the
header-interface integration at these stations, not a complete-body stress
field or splitting resistance check.

Before annotation, independent authentication matched all 60 comparison input
pins and four output hashes; preparation 06 matched 28 pins and three outputs.
Exact consumed source and document bytes are preserved under
`rawlocal/header-v-cuts/source-snapshots/*-consumed-attempt02.*`. The producer
methods and all earlier attempts remain unchanged.

The original and mapped inventories each have 2,980 positive normal-hull
tension bounds and 44 existing finite compression witnesses. The global peak
remains `55.452555565 N` for the left inner-knee block, `a12-forward`, after
`v=2.796913348 mm`. The largest recorded components of the mapped-inventory
and physical-gravity accounting residual are `8.5269e-14 N` and
`1.0761e-11 N·mm`. These numerical recoveries do not supply fracture resistance.

| Body | Maximum mapped normal-hull tension bound (N) |
| --- | ---: |
| Left center-post cleat | 1.364486 |
| Right center-post cleat | 1.468498 |
| Left center-principal cleat | 25.202581 |
| Right center-principal cleat | 28.539717 |
| Left inner-knee block | 55.452556 |
| Right inner-knee block | 49.262828 |

These are saved normal-transfer diagnostics, not loads assigned to individual
bolts or required manufacturer ratings. Other-interface actions remain exact
source points. All splitting, complete-joint and physical-release flags remain
false. Fresh proposal forces require their own bound adapter; the reviewed
104-axis result is preserved as history and does not qualify the 108-axis
proposal.

| Artifact | SHA256 |
| --- | --- |
| `result.json` | `977f25094bf979db9aff9e234674a050b9644de2d1f40698b114808e8ef77ef8` |
| `v-cuts.jsonl.gz` | `8ad8a43813d940fab688cfc59409017a8a1f3a164f5cab6bf7065fad917a1ead` |
| `receipt.json` | `8adf31c8d3756b333a8c3d6729d2959bf31cbd8c495efa4d2396f851a5ce0fa5` |

## Result criterion and limits

The consumer result is ready for review when all source pins authenticate; the
boundary result has 36 interfaces, 360 source actions, and 72 `u`/`v` cut
states; each supported body/case matches its frozen `v` station catalog and
both limits; all source rows and whole-body inventories recover their full
six-component wrenches within the existing accounting tolerances; and each
cut records original and mapped wrenches, normal-hull bounds, and any existing
finite-pressure witness. Any field that the reused integrator cannot handle
stays at its exact source point and appears as an explicit scope stop. Such a
source gap does not qualify splitting.

The output is an equilibrium and wrench-placement comparison, not proof of
pressure compatibility, local timber stress, splitting resistance, bolt
allocation, or complete joint behavior. `v-cuts.jsonl.gz` stores each signed
cut row under the ignored `rawlocal/header-v-cuts/attempt01` output.
