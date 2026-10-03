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

## Reused integrations

- Washer annuli use `disk_strip` for the outer disk minus the inner disk.
- Contact cells use `supported_tile_integrals` on each saved trimmed cell and
  its saved circles.
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
`[5, −10/π, 0] N`. Each comparison tolerance is `1e-12` in the declared
units. This coupon exercises existing integration helpers only; it carries no
engineering result.

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

Parent owns both commands and any source-data run. This producer has not been
executed in this preparation turn.

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
