# Current wood-property scenario, attempt 01

Status: source-verified conditional property inputs for standard nominal
sections; custom ripped sections remain unresolved. Prepared 2026-09-27 for
`led-clearance-2x6-runner-seated-blocks-v1`. This is a specified material
scenario, not a receiving record, resistance calculation, capacity, or
acceptance.

## Conditional product and published values

The named scenario is visually graded, solid-sawn Dimension lumber in the
2024 NDS Supplement Table 4A species group `Douglas Fir-Larch, Douglas Fir,
Western Larch`, commercial grade No. 2 (DF-L No. 2). Table 4A's No. 2 row is
classified `2\" & wider`, lists PLIB and WWPA as grading-rule agencies, and
publishes the following reference values in psi on printed page 34:

| Reference property | Published value | Table 4A label |
| --- | ---: | --- |
| Bending, `Fb` | 900 psi | `Fb` |
| Tension parallel to grain, `Ft` | 575 psi | `Ft` |
| Shear parallel to grain, `Fv` | 180 psi | `Fv` |
| Compression perpendicular to grain, `Fc⊥` | 625 psi | `Fc⊥` |
| Compression parallel to grain, `Fc` | 1,350 psi | `Fc` |
| Modulus of elasticity, `E` | 1,600,000 psi | `E` |
| Modulus of elasticity, minimum, `Emin` | 580,000 psi | `Emin` |

These are the unadjusted Table 4A reference values for normal load duration
and dry service. The table says to use Table 4A adjustment factors and NDS 4.3;
no adjusted value is calculated here. The existing ordinary-patch manifest
already carries dry DF-L No. 2 `Fc⊥ = 625 psi` as a conditional component
reference. This record points to that basis and does not repeat its washer
screen or any mechanics.

The separate Table 4A group `Douglas Fir-Larch (North), Douglas Fir (North),
Western Larch (North)` is not the selected row. Its shared table location is
not a reason to substitute its values. Any product claim must match the
species-group designation of the selected row, not only say “Douglas fir.”

## Standard nominal section scenarios

NDS-2024 §4.1.3.2 classifies nominal 2×6, 4×4 and 4×6 as Dimension lumber;
their Table 4A size classification is `2\" & wider`. For these specified
standard nominal dimensions, Table 4A page 32 directly supplies these size
factors. They are inputs only and are not multiplied into resistance values.

| Conditional nominal section | Current map coverage | `CF` for `Fb` | `CF` for `Ft` | `CF` for `Fc` | `Cfu` for flatwise `Fb` |
| --- | --- | ---: | ---: | ---: | ---: |
| 2×6 (38.1 × 139.7 mm) | 16 frame timbers; 2 connector spines | 1.3 | 1.3 | 1.1 | 1.15 |
| 4×4 (88.9 × 88.9 mm) | 18 connector blocks | 1.5 | 1.5 | 1.15 | 1.0 |
| 4×6 (88.9 × 139.7 mm) | 4 frame timbers | 1.3 | 1.3 | 1.1 | 1.05 |

`CF` applies only to `Fb`, `Ft` and `Fc`; it does not apply to `Fv`, `Fc⊥`,
`E` or `Emin`. `Cfu` is an additional permitted multiplier on size-adjusted
`Fb` when load is applied to the wide face; the actual load face is not selected
here. The factors depend on the named nominal section, not merely the final
measured width and thickness of a ripped piece.

The 20 frame timber IDs and all 24 block IDs are listed in `scenario.json`.
Their conditional longitudinal grain and transverse/ring-orientation cases
remain in the existing frame and block maps cited there; this scenario does
not duplicate those per-member frames or turn them into physical observations.
The block pattern-to-section assignment follows
[`current-material-scenarios.md`](../../../current-material-scenarios.md).

## Custom final sections: no assigned values yet

The proposed 83.9 × 139.7 mm and 88.9 × 133.35 mm final sections are custom
ripped dimensions. The available sources do not establish a final nominal NDS
size classification or the corresponding `CF` basis for either section. Do
not map either one to the source-stock 2×6 or 4×6 factors, and do not transfer
a source board's No. 2 grade or reference values after ripping.

ALSC Voluntary Product Standard PS 20-25 provides the concrete certification
route and limit:

- §3.4.2 (printed p. 11) defines Dimension lumber by nominal thickness from
  2 inches to under 5 inches and nominal width of at least 2 inches.
- §6.1.6 (printed p. 17) requires inspection accordingly when a nonstandard
  size is specified; all other certified grading-rule provisions still apply.
- §§7.3.7–7.3.7.1 (printed p. 21) state that ripping, resawing or surfacing
  graded/grade-marked lumber negates its original grade, grade mark and design
  values; the original mark must be removed or obliterated when the operation
  may alter the grade.
- §8.1.4 (printed p. 21) requires inspection service for standard grades in
  nonstandard sizes under §6.1.6, unless the purchase/sale contract says
  otherwise.

These sections identify an inspection/regrading route; they do not assign a
Table 4A size classification or a size factor to either custom section. An
MVP-E analysis could conditionally assume that a named final product is
eligible for DF-L No. 2 under an applicable certified rule from a Table 4A
listed grading agency (PLIB or WWPA) for its nonstandard size and
remanufacture, but that premise is not an assertion that
inspection or regrading occurred. Actual inspection/regrade and receiving
conformance remain unobserved and outside this scenario. Keep
`nominal_nds_classification`, `size_factors`, and conditional post-rip grade eligibility
unresolved for both until an explicit, supportable final-size basis is
established.
The current scenario therefore does not mark the full 44-member wood property
set `inputs_ready`.

A fully specified **conditional analysis** can meet the MVP-E `inputs_ready`
definition while actual receiving observations remain blank, after the
custom final sections have a supported NDS classification, conditional
final-grade premise, and all check-specific adjustments are frozen. This
record establishes only the standard 2×6/4×4/4×6 base-property lookup; its
size factors are identified but other check-specific factors remain
unselected, so it does not mark even the standard-section check inputs fully
ready. Neither state verifies physical stock.

## Adjustment inputs still required

Table 4A page 32 supplies the following adjustment information for this row;
none is applied here:

- `CM` when moisture content exceeds 19% for an extended period: `Fb = 0.85`
  subject to the table's `Fb × CF ≤ 1,150 psi` exception; `Ft = 1.0`,
  `Fv = 0.97`, `Fc⊥ = 0.67`, `Fc = 0.8` subject to `Fc × CF ≤ 750 psi`, and
  `E`/`Emin = 0.9`.
- `Cr = 1.15` for the listed repetitive-member uses only when members are in
  contact or no more than 24 inches on center, there are at least three, and
  an adequate load-distributing element joins them.
- The per-member nominal size is needed for `CF`; the load face is needed to
  decide whether `Cfu` applies to `Fb`.
- The load-duration, temperature, geometry/bracing, bearing/contact, notch or
  nonprismatic/connection, and treatment/incising conditions needed to select
  any other applicable NDS-4.3 factors must be frozen by check before a
  resistance comparison. This record does not select those factors or calculate
  any adjusted properties.

Required scenario inputs therefore include the check's load-duration basis;
dry or wet-service condition and measured moisture when available; service
temperature; final nominal section/classification; bending load face; member
spacing, count and load-distribution conditions if `Cr` is claimed; member
stability/bracing; bearing length/contact basis; notch/nonprismatic and
connection conditions; and treatment/incising identity. Do not infer them
from a nominal label or a retail product description.

## Elastic-model boundary and observations

`E = 1,600,000 psi` and `Emin = 580,000 psi` above are published reference
properties in a resistance-input record. The current FEA timber card is a
separate elastic model: it uses the NDS `E` as longitudinal `E_L`, converts it
to MPa, and combines it with species-average clear-wood transverse/shear
ratios as a declared orthotropic scenario. See
[`current-material-scenarios.md`](../../../current-material-scenarios.md).
This record does not create or alter an FEA material card, treat `Emin` as an
FEA modulus, or equate the clear-wood ratios with DF-L No. 2 acceptance limits.

Every physical receipt field remains unobserved: species group, grade mark,
post-rip certificate/regrade, actual dimensions, grain slope/direction, ring
orientation, moisture, treatment, and connection-zone condition are null in
`scenario.json`. Grain directions already present in the two source maps are
conditional geometry/material-frame scenarios only. The original grade and
design values never carry through a rip; no physical grain observation is
claimed.

No demand, mechanics solution, adjusted resistance, capacity, failure
criterion, pass/fail, acceptance, fabrication, or release is produced.

## Primary sources and source pins

- American Wood Council, [2024 NDS Supplement](https://awc.org/resources/2024-nds-supplement/),
  Chapter 4, Table 4A (printed pp. 32 and 34); source PDF path and SHA-256
  are recorded in `scenario.json`.
- AWC, [2024 NDS](https://awc.org/resources/2024-nds/), §§4.1.3.2 and
  4.1.7.1; current [NDS errata and addenda, March 23, 2026](https://awc.org/wp-content/uploads/2026/03/2024-NDS-Errata-and-Addenda-03.23.26.pdf).
  The inspected errata affects other sections and contains no Table 4A,
  §4.1.3.2, or §4.1.7.1 correction.
- AWC, [2024 NDS Supplement addendum, February 12, 2024](https://awc.org/wp-content/uploads/2024/02/2024NDS-Supplement-Updates-Errata_20240212.pdf).
  It adds Red Alder to Table 4A; it does not change the DF-L row used here.
- American Lumber Standard Committee, [PS 20 additional documents](https://alsc.org/lumber-additional-documents-ps-20/)
  (current edition PS 20-25) and the [official PS 20-25 PDF](https://alsc.org/uploaded/PS%2020-25%20Final.pdf),
  §§3.4.2, 6.1.6, 7.3.7–7.3.7.1, 8.1.4.

The machine-readable property values, source locations, unresolved size
classification, member IDs, physical-null fields and local source fingerprints
are in [`scenario.json`](scenario.json).
