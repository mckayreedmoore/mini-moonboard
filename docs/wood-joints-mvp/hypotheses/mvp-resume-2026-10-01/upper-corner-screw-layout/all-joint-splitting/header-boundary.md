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

The cleat station inventory comes from the receipt-bound
`remaining-block-transverse/attempt01/cuts.jsonl.gz`, whose rows use `block`
identities and local axis indices 0/1/2. Only transverse indices 1/2 enter the
72-state u/v catalog. The all-joint checks provide matching state identities
and cut counts; the separate `receiver-cuts.jsonl` archive contains frame
receivers and does not supply cleat stations. Both limits at every reused
station and each complete state count remain required. Parent preparation
attempt 02 stopped at the earlier receiver-to-cleat lookup, before evaluating
the boundary fields; its snapshot and stop remain preserved. No new cuts or
relaxed coverage are introduced by the corrected join.

Parent attempt 03 subsequently stopped at the lateral-bore feature join.
The receiver-clearance record and the finished-surface record bind the same
STEP bytes but enumerate faces differently (for example, the first left
center-post header bore is receiver face 8 and surface feature `facet009`).
The corrected join requires the same STEP digest and a unique cylinder with
matching radius, coaxial line and finite endpoints, allowing axis reversal.
It retains the existing direction and geometry tolerances. Face numbers alone
do not select a cylinder. The failed attempt remains preserved; geometry and
pressure laws are unchanged.

Parent attempt 04 stopped because the local support certificate used a
different dictionary key from the pinned bore-pressure helper. The corrected
certificate emits and checks the helper's
`whole_circumference_support_certified` key. Its stock, void-clearance and
complete-cylinder conditions are unchanged; unsupported geometry still
refuses the pressure profile. The failed attempt remains preserved.

## Completed preparation 05 and comparison 01

Parent executed preparation attempt 05 and the first `v`-cut consumer on
October 3, 2026. The preparation covers all 36 cleat/case interfaces, 360
source actions, and 72 transverse states with 4,056 before/after cut limits.
It produced 428 boundary fields and preserved the other-interface actions.
The consumer evaluated all 36 body/case pairs and 3,024 `v`-cut limits with
no body-scope stop. Neither result establishes splitting resistance.

Preparation 05 classified 72 washer rows as unsupported. Their recorded
annular clearances are positive; the rejection comes from an opposite-normal
guard error. The selected face normal points outward and the pressure normal
points inward, so their dot product must be `-1`, not `+1`. The corrected
producer tests that signed opposition and includes a small known-answer
coupon. No stock, hole, washer dimensions or force directions are changed.

The original preparation status also labels 249 nonzero source free-couple
rows as unresolved. All are roundoff under the existing component accounting
tolerance of `1e-5 N·mm`; the largest vector norm is
`5.5454e-11 N·mm`. The corrected producer keeps every raw free couple, records
the raw nonzero count separately, and classifies unsupported couples using
the existing tolerance. It uses a neutral preparation status and an explicit
couple classification. No extra physical couple is inferred from roundoff.

Consumer 01 retains 168 unsupported fields at their exact source points:
the 72 washer rows and 96 contact cells whose bore circles cross the reused
integrator's other-coordinate tile boundary. The comparison is therefore a
partial placement diagnostic. Its largest original and mapped normal-hull
tensile lower bounds are both `55.452556 N`, for the left inner-knee block in
`a12-forward`. These are demand diagnostics, not bolt allocations or fracture
capacity comparisons. Fresh attempts are required after correcting the
washer guard and integrating the complete trimmed contact cells.

Attempts 05 and 01, their snapshots and receipts remain unchanged. The exact
boundary document consumed by comparison 01 is preserved at
`rawlocal/header-v-cuts/source-snapshots/header-boundary-before-attempt01-annotation.md`.

| Artifact | SHA256 |
| --- | --- |
| Preparation 05 `result.json` | `dd465c0a0a108a3d01589179a4da0a05efcfad6563f53c78f08d995c333bd2ef` |
| Preparation 05 `receipt.json` | `142b58af3b9dd0b581e4b839f3136813d2102a7b10f935ec78dad671c934508f` |
| Comparison 01 `result.json` | `298b310f90c6556c2eef72338e8d4dc2a6f03bdd41a3b45b48a5e8aa6833cc32` |
| Comparison 01 `receipt.json` | `ed7dee7dda8d43662f10d38c8c88ecadf70de86b1c175069b7a644d8b6c2efda` |

## Completed preparation 06 and comparison 02

Parent ran both analytical coupons, preparation 06 and comparison 02 with
the corrected normal guard and exact circle/tile integration. Preparation 06
has 500 fields, all 360 source actions, 36 interfaces and 72 transverse states
with 4,056 linked cut limits. It has zero unsupported boundary rows and zero
above-tolerance free-couple rows. All 249 raw nonzero free couples remain;
their maximum absolute component is `5.5424152402e-11 N·mm`, below the existing
`1e-5 N·mm` accounting tolerance.

Comparison 02 evaluates all 36 body/case pairs and 3,024 `v` limits with zero
unsupported fields and zero body-scope stops. Independent verification before
these annotations matched preparation's 28 source pins and three outputs,
and comparison's 60 source pins and four outputs. Exact consumed PY and MD
bytes are preserved under `rawlocal/header-v-cuts/source-snapshots/` with
`*-consumed-attempt02.*` names. The executed source hashes remain
`5108639d6a1afa955f4f0a1db44aa10e194ad93d24b525011bb13b09b887d43c`
and `6614559cf623c643818cb66eca39324b04ee775165d6c1c695034c62f9e17537`.

Complete header-field integration does not remove the opening diagnostic:
2,980 limits retain positive normal-hull tension bounds and 44 have the
existing finite compression witness. The largest original and mapped bounds
remain `55.452555565 N` at the left inner-knee block, `a12-forward`, after
`v=2.796913348 mm`. These are not splitting capacities or per-bolt demands.
Other interfaces remain at their recorded source points. The preparation and
comparison still set splitting qualification and complete-joint acceptance
false; no historical result transfers to the fresh 108-axis proposal.

| Artifact | SHA256 |
| --- | --- |
| Preparation 06 `result.json` | `7316c7bda88727c0509d5071e8a49f2b79345734f2a910d17a29c6c59f2ca9c8` |
| Preparation 06 `receipt.json` | `155fe658358779e409c747ab499eb36bd20ff06549a30f59cc3f5718ee39ffd8` |
| Comparison 02 `result.json` | `977f25094bf979db9aff9e234674a050b9644de2d1f40698b114808e8ef77ef8` |
| Comparison 02 `receipt.json` | `8adf31c8d3756b333a8c3d6729d2959bf31cbd8c495efa4d2396f851a5ce0fa5` |

## Commands and frozen inputs

The producer source pins are declared in `header-boundary.py`. They cover the
header local-transfer input and geometry records, their receipts, the selected
member cache, the six-body transverse archive, the frozen all-joint closure and
cut records, the existing header traction map, its washer-seat basis, the
reused contact/geometry helpers, the bore-wall helper, and each bound finished
STEP. A changed digest stops preparation.

Parent preparation attempt 01 stopped at a mistyped receiver-cut digest. The
original all-joint receipt, still authenticated at its frozen digest, binds
`receiver-cuts.jsonl` to
`9ed12678cc317fac8e0797d295ee8c986e0c7033707fd27361f2c64252077381`;
the saved file matches that binding. The consumer literal is corrected to that
original value without repinning changed evidence. The same audit corrected
two header-map output paths that used the producer-file constant instead of
the existing output-directory constant; their expected digests are unchanged.
The nominal annulus-radius guard uses the existing geometry tolerance while
retaining the saved radii (`9.232899999999999 mm` is the recorded outer radius).
The failed attempt snapshot and stop remain preserved. Use a fresh attempt
with the corrected producer.

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
