# BG001 three-case signed end-distance sensitivity, attempt 01

This packet extends the existing BG001 signed-end-distance arithmetic to both
physical bolts in all 21 accepted rear-case/load-factor states. It produces 42
paired, same-state individual-bolt rows and retains each bolt's simultaneous
outer-seat tie as a separate action. The `CΔ` calculation is reported only as
a **historical NDS-2018 Commentary method sensitivity**. The packet does not
adopt an oblique-grain `CΔ` under NDS-2024, produce an adjusted DCR, or accept
the joint.

## Source boundary and method

The pinned official NDS-2024 Chapter 12 file is specification text and tables;
despite the filename, it contains no Commentary C12.5.1.2. Its checksum is
`5fc837523ff10acc097a162718700a9b4ba64e627d2b0023439146d42fe4ee2a`. AWC's
[2024 NDS page](https://awc.org/resources/2024-nds/) lists the 2024 Commentary
as part of the package, but no authenticated 2024 commentary text supporting
this grain-angle interpolation was present in the reviewed sources. The exact
2024 `CΔ` application therefore remains open.

The available interpolation source is the official [NDS-2018 Commentary,
Chapter 12](https://awc.org/wp-content/uploads/2021/10/AWC_NDS2018-withCommentary_20200827_AWCWebsite_Commentary.pdf),
printed page 263, SHA-256
`3402c7703cddef3e6693741ebaef9bfd0c1b0ddf075762c6f411fe1916751f7d`. The
repository's September 30 [method correction](../../service-upper-frame-joint-review-2026-09-30/method-correction.md)
limits that edition to historical sensitivity and explicitly records that
NDS-2024 Commentary interpolation is unverified. The calculation below uses
the already-reviewed [`end_reference` helper](../../service-upper-frame-joint-review-2026-09-30/end_branch.py)
and its pinned known answers; it does not transfer historical wording to the
2024 edition.

For each signed receiver force, `α = atan2(|Fcross|, |Fgrain|)` selects the
angle and the sign of `Fgrain` selects its `g+` or `g−` loaded end. The
historical sensitivity uses `e_full(α) = D × (7 − 3α/90)` and a half-distance
floor of `e_full/2`, with modeled `D = 6.35 mm`. Where the floor is met, the
member factor is `min(1, e_actual/e_full)`. For each same-state two-bolt pair,
the packet takes the minimum across both receivers on both bolts and scales
each bolt's own raw Mode IV reference by that one group-min sensitivity. This
is the existing conditional arithmetic scope, not a verified 2024 group
factor or group capacity.

The 2018 Commentary C12.5.1.2 defines the end-distance **tension-load** branch
as fasteners bearing toward the member end (printed page 263). For this
historical sensitivity, each signed receiver bearing force selects the
modeled end toward which that receiver is loaded. The cited branch definition
does not require a separate global tension/compression classification of the
whole member. This does not establish that the 2024 edition retains this
definition or interpolation; member stress and local failure checks also
remain separate and uncomputed.

The forces, all six unadjusted single-shear modes, and ties come from the
source-replayed [three-case paired-resultant screen](../current-bg001-three-case-resultant-reference-attempt01/README.md).
The axis positions and end rays bind to the same pinned finished geometry and
three-station profile query. Each selected loaded-end ray has a single
orthogonal planar terminal at all three through-thickness stations. These are
modeled dimensions, not inspected stock; the samples do not establish a
continuous profile minimum.

## Factor-one comparisons

These rows show the six source-signed lateral actions at load factor 1.0. The
last comparison is the historical `CΔ`-only sensitivity; it is not a design
DCR. Each value uses the same state's group-min factor while preserving the
physical bolt's own action, reference, and separate axial tie.

| Case | Bolt | Lateral demand (N) | Raw Mode IV reference (N) | Raw ratio | Group-min historical `CΔ` sensitivity | `CΔ`-only reference sensitivity (N) | `CΔ`-only ratio sensitivity | Separate tie (N) |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| A1 rear | 1 | 108.896 | 767.897 | 0.14181 | 0.725371 | 557.011 | 0.19550 | 44.483 |
| A1 rear | 2 | 146.049 | 667.352 | 0.21885 | 0.725371 | 484.078 | 0.30171 | 47.001 |
| A12 rear | 1 | 301.657 | 712.070 | 0.42363 | 0.703901 | 501.227 | 0.60184 | 64.966 |
| A12 rear | 2 | 335.061 | 682.661 | 0.49082 | 0.703901 | 480.526 | 0.69728 | 18.473 |
| K12 rear | 1 | 24.877 | 592.680 | 0.04197 | 0.963117 | 570.820 | 0.04358 | 56.542 |
| K12 rear | 2 | 68.767 | 574.085 | 0.11978 | 0.963117 | 552.911 | 0.12437 | 13.978 |

In each case the same modeled `post_2` loaded end, `g+`, controls the
historical group-min calculation: its 25.40 mm end is paired with the source
angle for that increment. The group minimum remains constant across the seven
load factors within each case because the source vectors preserve their
direction. Exact per-member angles, signs, distances, factors, raw references,
ratios, force pairs, and ties are included in all 42 rows of
[`screen.json`](screen.json). The A12 factor-one group factor and two scaled
references reproduce the previous A12 calculation as a numerical oracle; the
comparison does not validate that older packet's superseded 2024 source
attribution.

The same-state summed lateral action remains off the modeled `+Z` fastener
row in every increment. Its sine-to-row values are 0.507200 for A1, 0.118462
for A12, and 0.964519 for K12 (minor last-digit variation by increment).
Accordingly, the reviewed group-action helper's row-alignment condition is
not met and `Cg` remains pending. No group factor, force sharing, or group
capacity is inferred.

## Remaining dependencies

- Exact authenticated NDS-2024 Commentary C12.5.1.2 text, or another official
  current-edition source, is needed before this historical interpolation can
  be treated as a current `CΔ` provision.
- A source-bound group-action method for the oblique same-state resultants is
  still required for `Cg`; no `Cg` is applied here.
- Load-duration and other adjustment factors, delivered wood and bolt
  properties, actual bores and fit, and the applicable group/spacing
  classification are not established by these conditional model inputs.
- The lateral resultants and axial ties need their own combined bolt/washer
  and receiver-seat resistance path; ties are not added to lateral actions.
- Local splitting/tension-perpendicular, row or group tear-out, net section,
  member shear, and complete joint transfer remain uncomputed. No capacity
  follows from these individual-bolt comparisons.

The exact direct and transitive local source hashes and the two external
edition identities are in [`source-pins.json`](source-pins.json). Reproduce
and verify from the repository root:

```sh
OPENBLAS_NUM_THREADS=1 .venv/bin/python docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/current-corner-bg001-signed-end-distance-three-case-attempt01/produce.py --write
OPENBLAS_NUM_THREADS=1 .venv/bin/python docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/current-corner-bg001-signed-end-distance-three-case-attempt01/produce.py --verify
```

The producer replays the 42-row three-case packet and the prior A12 signed-end
packet, verifies the corrected 2024 source boundary and historical helper,
checks each loaded-end profile ray, and compares all A12 factor-one arithmetic
to the earlier result. It performs no geometry edits or native solve.
