# Six Header Cleat Boundary Fields

## Purpose and authority

This packet prepares physical boundary descriptions for the header side of the
six cleats in the current reviewed source. It uses the original
`compact-floor-flush-wood-joints-development` revision
`upper-corner-screw-row-2026-10-02-v1`, with 104 reviewed bolt axes and the six
saved cases. The twelve header axes are a subset of those 104. The separately
available 108-axis proposal remains unadopted.

The six cleats are the left and right center-post cleats, left and right center
principal cleats, and left and right knee outer inner-frame blocks. Each of the
36 body/case interfaces has ten saved header actions: two axial washer-seat
rows, four clipped contact-cell rows, and four lateral bore-component rows.
The producer preserves each source row and its full six-component wrench.

This is boundary preparation for later joint checks. It calculates no
splitting resistance, local timber stress, contact compatibility, or accepted
load path. Numerical source-to-field closure is bookkeeping, not qualification.

## Boundary representations

- **Axial washer seats:** locate the saved target bore axis on the opposite
  finished cleat end face. If the saved face has a supported annular land, place
  the compressive force as a concentric uniform annulus using the frozen
  minimum-area plain-washer envelope (inner radius 4.1529 mm; outer radius
  9.2329 mm). The delivered washer is not inspected. Preserve any source force
  component that cannot act into that face, and preserve every source free
  couple as an explicit residual.
- **Timber contact:** describe each source contact cell as its saved patch
  rectangle minus the two complete bore circles, intersected with its original
  sampler-cell rectangle. Use uniform frictionless normal pressure over the
  exact clipped cell area and centroid. A tensile or tangential source component
  is recorded as unsupported; no balancing traction is invented.
- **Lateral bore actions:** bind each row to its unique saved finished
  cylindrical face. A supported radial force at a bore end is represented by
  two nonnegative half-cosine pressure strips: `+2F` at one-quarter bore span
  and `-F` at one-half span. Their signed resultants preserve the source force
  and first moments. The existing bore helper records each strip as an axial
  Gauss measure; it does not assert an elastic contact state. Any bolt-axis
  force, unsupported wall geometry, or source free couple remains explicit.
- **Other body actions:** keep every non-header source action, including body
  loads, at its exact saved point and free couple. The output reports the
  header-interface wrench at its saved datum and transports it to the cleat
  datum before assembling the full body wrench.

Every pressure field carries global coordinates, the cleat grain/u/v
coordinates, its geometric support description, and a u/v cut capability tag.
For each of the 36 cleat/case pairs, `u_v_cut_catalog` links every frozen
before/after cut station on both transverse axes to the all-joint state and the
remaining-block transverse record. These are the source stations for a later
field integration; this producer does not calculate cut demands.

## Commands and frozen inputs

The producer source pins are declared in `header-boundary.py`. They cover the
header local-transfer input and geometry records, their receipts, the selected
member cache, the six-body transverse archive, the frozen all-joint closure and
cut records, the existing header traction map, its washer-seat basis, the
reused contact/geometry helpers, the bore-wall helper, and each bound finished
STEP. A changed digest stops preparation.

The independent known-answer command checks only boundary algebra: an annular
quadrature wrench, the two-strip wrench, and the reused bore helper coupon.
Parent owns running it:

```sh
uv run python docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/upper-corner-screw-layout/all-joint-splitting/header-boundary.py --coupon-only
```

The full preparation writes to a fresh ignored output directory. Parent owns
running this command after the coupon is accepted:

```sh
uv run python docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/upper-corner-screw-layout/all-joint-splitting/header-boundary.py --output docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/upper-corner-screw-layout/all-joint-splitting/rawlocal/header-boundary/attempt01
```

The frozen preparation criterion is: all pins authenticate; all 36 interfaces
and 360 source actions are present; all 72 washer rows, 144 contact rows, and
144 lateral rows receive a field or an explicit unsupported status; every
source row retains its six-component source wrench and exact force/free-couple
residual; and all 72 u/v cut states resolve to their saved before/after station
catalogs. A source-to-field force or moment residual must meet the producer's
recorded accounting tolerance to be marked numerically closed. An unsupported
field or physical free couple remains a downstream blocker unless another
evidence path resolves it. Passing this preparation criterion does not pass a
splitting criterion or qualify any joint.

## Limits

No new material strength, connector capacity, friction, preload, pressure peak,
native solve, CAD solve, or frame solve is introduced. The washer envelope and
pressure patterns are explicit placement assumptions, not observed contact
states. Other interfaces are retained at their source points. Finished solids
and cut records are saved geometry evidence, not inspection of delivered wood
or hardware. The result cannot authorize drilling, fabrication, or climbing.
