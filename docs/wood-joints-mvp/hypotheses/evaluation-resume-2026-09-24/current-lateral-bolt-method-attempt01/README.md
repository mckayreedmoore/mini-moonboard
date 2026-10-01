# Current individual timber-bolt lateral-yield method — attempt01

**Status:** reusable mechanics boundary and source-pinned reference method;
not a current resistance, criterion result, or release. The maintained API is
[`mini_moonboard/nds_2024_multi_member_bolt_yield.py`](../../../../../mini_moonboard/nds_2024_multi_member_bolt_yield.py)
with focused tests at
[`tests/test_nds_2024_multi_member_bolt_yield.py`](../../../../../tests/test_nds_2024_multi_member_bolt_yield.py).
This attempt preserves every earlier criteria and method attempt.

## Method and applicability

The API calculates an **unadjusted individual-bolt reference lateral yield
value** for contacting solid-sawn wood layers, using ANSI/AWC NDS-2024 Chapter
12 and the NDS multi-member procedure where applicable. It returns one
`reference_lateral_lbf` only after the explicitly required synthetic or future
case inputs are complete. Even then, `adjusted_capacity_lbf` is `null`, current
demand is pending, criterion disposition is `pending`, and
`capacity_or_pass_claim` is false.

Member counts are handled as follows:

| Ordered wood members | Calculation | Modes / shear planes |
| --- | --- | --- |
| 2 | NDS §12.3.1A single shear | `Im`, `Is`, `II`, `IIIm`, `IIIs`, `IV`; one adjacent shear plane |
| 3 | NDS §12.3.1A symmetric double shear | `Im`, `Is`, `IIIs`, `IV`; both planes of one symmetric triple |
| 4 or more, even | NDS §12.3.8.1 | all adjacent pairs as single shear; minimum pair Z times `n/2` |
| 5 or more, odd | NDS §12.3.8.2 | all adjacent triples as symmetric double shear; minimum triple Z times `(n−1)/2` |

For double shear, the center layer is main and the two outside layers are side
members. This API accepts only equal side bearing length, species-gravity
input, grain angle, thread exposure, and opposite/equal-magnitude side
actions. For an even multi-member connection each adjacent pair needs an
explicit main/side role. Opposed signs are checked at each analyzed plane.
The lateral action values are **not used as demand or capacity multipliers**;
they only expose the required force directions/symmetric side condition.
Each action source must still be supplied and independently reviewed.

Inputs require: exact NDS edition; current geometry revision and axis ID;
hash/locator references for the actual axis, physical member order, member
material, grain orientation and bearing length, spacing/detail, and bolt
product/Fyb basis; ordered solid-sawn members;
per-member effective bearing length, specific gravity, load-to-grain angle,
bolt-axis orientation, thread-bearing length, and nonzero signed lateral
action; zero gap at every adjacent face; bolt nominal/root diameter, thread
status and positive Fyb; a sourced same-case action binding; confirmation that
load is perpendicular to bolt axis and NDS §12.5 minimum spacing/end/edge
conditions are met; and main/side roles for each single-shear pair. The
geometry-axis, stack, spacing/detail, grain, member-property, product, Fyb,
and action bindings each require a path, locator, and SHA-256. No wood,
product, grain, or action default is inferred. Missing fields return `pending`;
out-of-scope or malformed input raises `ValueError`.

The current adapter
[`current-manifest-axis-inventory.json`](current-manifest-axis-inventory.json)
is read-only and pins
`current-full-frame-input-manifest-attempt04` (file SHA-256
`9e682e28c3d4c3c0594863f82c6b74d19dee2700f3856d34e1a26f69082e4f11`). It
records all 92 modeled axes and receiver intervals: 88 have two receiver IDs
and four knee-side axes have three. The two-member route is potentially
applicable to the first group. The three-member route applies to the second
group only if physical stack order identifies symmetric outside members and
their geometry, wood properties, and actions meet the stated conditions; the
modeled interval lengths alone do not establish that. The manifest does not
establish the physical head-to-nut stack, member order, actual contact/bearing
lengths, bolt product, thread location, wood identity/properties/grain,
verified edge distances, or fresh same-case bolt actions. Therefore **all 92
current axes remain pending**; the modeled CAD interval is not used as a
physical bearing length. The manifest's internal declared SHA is recorded
separately and is not substituted for the verified file-byte SHA.

## Equation implementation

For solid-sawn members with `D ≥ 1/4 in`, the implementation uses NDS Table
12.3.3 bearing strengths, rounded to the nearest 50 psi:

```text
Fe_parallel = 11,200 G
Fe_perpendicular = 6,100 G^1.45 / sqrt(D)
Fe_theta = Fe_parallel Fe_perpendicular /
           (Fe_parallel sin²(theta) + Fe_perpendicular cos²(theta))
```

For selected `D < 1/4 in`, it uses the Table 12.3.3 value `Fe = 16,600
G^1.84`. The effective `D` is the bolt root diameter when threads bear in any
member, except NDS §12.3.7.2 allows the full-body diameter when thread bearing
is at most one quarter of the full bearing length in **every** affected member.
The January 2025 AWC correction to Table 12.3.1B is applied: `KD = 2.2` for
`D ≤ 0.17 in` and `KD = 10D - 0.5` for `0.17 < D < 0.25 in`. The second
branch yields the corrected value `1.5` at `D=0.20 in`. For threaded nominal
`D ≥ 0.25 in` with
root `Dr < 0.25 in`, the table's small-root note applies `KD × Ktheta`.

For `D ≥ 0.25 in`, the table reductions are `4 Ktheta` (`Im`, `Is`),
`3.6 Ktheta` (`II`), and `3.2 Ktheta` (`IIIm`, `IIIs`, `IV`), where
`Ktheta = 1 + 0.25 theta_max / 90`. For smaller selected diameters, all
single-shear reductions use corrected `KD`; threaded sub-quarter roots use the
additional specified `Ktheta`. The implementation uses the NDS single-shear
yield-mode equations via the maintained TR12-equation helper and the symmetric
double-shear equations in this module. Each pair/triple Z is the minimum
applicable `P/Rd` mode. No capacity adjustment is applied.

Applicability is intentionally narrow: solid-sawn lumber, contacting faces,
the standard NDS lateral-yield bolt range `nominal D = 1/4–1 in`, bolt axis
perpendicular to member grain, load perpendicular to bolt axis, and explicit
end/edge/spacing verification. The API requires source references with a
path, locator, and SHA-256 shape, but it **does not retrieve or authenticate
external product, wood, geometry, or demand sources**. The coordinator or
T11 evidence boundary must resolve and review those sources independently.
Positive test fixtures use synthetic references only and are not candidate
evidence.

## Independent numerical checks

The focused test suite checks two published AWC values against the maintained
implementation:

1. AWC TR12 Example 3.1, zero gap, `D=0.5 in`, `Fyb=45,000 psi`, 1.5-in main
   and side members both parallel to grain (`G=0.43`): the six individual
   values are 900, 900, 414, 550, 550, and 663 lbf, with `Z=414 lbf`. The
   implementation reproduces each to table rounding.
2. NDS-2024 Table 12F, three-member symmetric double shear, 1.5-in main and
   side members, `D=0.5 in`, DF-L `G=0.50`, `Fyb=45,000 psi`, parallel-to-grain
   `Zll=1,050 lbf`. The implementation reproduces the published controlling
   value. NDS Table 12F is the NDS-2024 edition-specific benchmark; TR12 is an
   independent equation/example cross-check, not an edition substitution.

The 4- and 5-member tests additionally verify complete adjacent-pair/triple
coverage and the §12.3.8 multipliers using only synthetic data. Boundary tests
cover contact gaps, edition mismatch, wrong force direction, asymmetric double
shear, invalid grain angles, non-finite and zero action values, source-reference
shape, thread-root selection, the one-quarter thread limit, unsupported
materials, missing roles, duplicate members, unverified §12.5 conditions, and
both boundaries of the corrected small-diameter `KD` interval.
[`known-answer-validation.json`](known-answer-validation.json) records both
independent examples, their source pins, calculated outputs, and the current
criteria inventory status. [`terminal-hashes.json`](terminal-hashes.json)
binds the exact maintained code, tests, attempt outputs, current manifest,
criteria inputs, provenance overlay/reconciliation, and external source pins.

Run:

```sh
./.venv/bin/python -m pytest -q tests/test_nds_2024_multi_member_bolt_yield.py
```

The current exact47 snapshot is in
[`current-criteria-inventory/current-aggregate.json`](current-criteria-inventory/current-aggregate.json): 47 pending, zero failed, zero conditional-pass, and zero justified N/A. Its source overlay is accepted for provenance only. The same snapshot preserves the historical/current method-map hashes and reconciliation-review binding. This method attempt did not edit criteria or their sources.

## Excluded scope and current missing inputs

This method does not calculate or resolve:

- bolt-group action/effective-number factors, group stiffness, load sharing,
  or signed per-bolt demand;
- splitting, row/group tear-out, net section, block shear, member shear,
  bearing, or any other brittle/member limit state;
- NDS end-use/design-value adjustment factors;
- axial bolt force, lateral/axial interaction, withdrawal, or tension;
- washer bending, spreading, or wood bearing under washers;
- steel connector, block, cleat, panel/plywood, or panel-fastener resistance;
- product/wood/source authenticity or physical inspection;
- current governing case, criterion comparison, pass/fail, engineering
  disposition, fabrication, or climbing release.

Exact next dependency: a reviewed physical stack/order plus the selected
bolt/thread geometry and per-member wood species/grade/G/grain/bearing-length
source bindings for each intended axis. Then the independent demand manifest
must provide current governing-case member actions and an accepted bolt-group
distribution method. Only after that can this individual-bolt reference be
fed into the separately scoped group, adjustment, splitting/member, washer,
connector, and full-duty checks. The current axis manifest supplies none of
those missing actual inputs, so no current reference calculation is emitted.

## Source pins

- ANSI/AWC NDS-2024, [AWC standard page](https://awc.org/resources/2024-nds/),
  exact governing edition. The official Chapter 12 PDF
  [Dowel-Type Fasteners](https://awc.org/wp-content/uploads/2026/08/AWC_NDS2024_withCommentary_20250328_WebsiteChapter-12-%E2%80%93-Dowel-type-fasteners.pdf)
  is pinned in the repository at SHA-256
  `5fc837523ff10acc097a162718700a9b4ba64e627d2b0023439146d42fe4ee2a`.
- AWC, [2024 NDS Errata and Addenda, 2026-03-23](https://awc.org/wp-content/uploads/2026/03/2024-NDS-Errata-and-Addenda-03.23.26.pdf),
  SHA-256 `b3f4f8b3b2e2ffa5eb618de9e1182614c329d9e4a135096667364dc9a8e473c0`.
- AWC, [January 2025 NDS Errata, Table 12.3.1B](https://web-media.awc.org/wp-content/uploads/2025/03/31134949/2024-NDS-Errata-and-Addenda-03.28.25.pdf),
  SHA-256 `2ecba75d6603994cafca68fbb049d0b9ff00f5e9df8dd0783e5150c3ca6460d8`;
  this is the direct pin for the corrected `KD = 10D - 0.5` term.
- AWC, [TR12-2015, General Dowel Equations for Calculating Lateral
  Connection Values](https://web-media.awc.org/wp-content/uploads/2021/12/17210714/AWC-TR12-1510.pdf),
  SHA-256 `95abb7d382aadf6984121f8731a5b91c2b633516e7f134991ad0a34a1b916be2`.
  Its Table 1-1 supplies the generalized single-shear equation form and
  Example 3.1 supplies the independent zero-gap numerical check above.

The AWC NDS-2024 Chapter 12 PDF is the method authority. The January 2025
erratum supplies the corrected `KD` term. TR12 supplies an AWC-published equation/example
check only; it is not treated as the adopted standard edition.
