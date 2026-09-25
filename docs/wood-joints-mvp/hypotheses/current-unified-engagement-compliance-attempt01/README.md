# Unified 1/4-20 engagement compliance and slack screen

**Prepared:** 2026-09-25. **Status:** reproducible conditional model scenario
and historical fit comparator. The calculation does not establish physical
thread transfer, delivered WJ04 fit, or a WJ24 product basis.

## Reproducible result

The pinned inputs support two separate numerical quantities for a hypothetical
1/4-20 UNC external 2A / internal 2B thread pair:

| Quantity | Result | Meaning |
| --- | ---: | --- |
| Post-seating equivalent engagement tangent | 760.709 kN/mm | One nominal literature-model component at generic `E = 200,000 MPa`; not an isolated 1/4-20 thread-pair measurement. |
| Engagement compliance | 0.00131456 mm/kN | Elastic deformation in that component after a load-bearing flank is seated. |
| Tangent extension at 1 kN | 0.00131456 mm | Excludes any initial fit slack, bolt/nut body extension, washer-seat motion, and timber motion. |
| Ideal fixed-rotation total flank-reversal travel | 0.016131–0.142244 mm | NBS H28 (1969) 2A/2B class-limit comparator with ideal-profile assumptions; not delivered-part slack. |

Reproduce the calculation and its embedded source-pin checks with:

```sh
python3 calculate.py
python3 -m unittest -v test_calculate.py
```

The producer writes [calculation.json](calculation.json). It refuses to run if
any pinned input has drifted. The exact sources and their SHA-256 hashes are
recorded there.

## Conditional one-dimensional law

For fixed relative rotation and an ideal matched pair, the calculation can be
written as a pair of post-seating branches with an initial free interval:

```text
F = 0                                 when -g− < δ < g+
F = Kth (δ − g+)                     when δ ≥ g+
F = Kth (δ + g−)                     when δ ≤ −g−
g+ ≥ 0, g− ≥ 0, and g+ + g− = b
```

Here `Kth = 760.709 kN/mm`, `δ` is relative bolt-to-nut axial motion, and `b`
is the full flank-to-flank reversal travel. H28 gives `b = 0.016131–0.142244
mm` for its reference class limits. With no known initial phase, the
one-direction free travel can range from zero to the pair's full reversal
travel; the calculation does not invent a centered phase. If relative rotation
is allowed, the helix couples rotation to axial advance and the fixed-rotation
class interval does not bound total axial travel.

This combined expression is a transparent conditional diagnostic law, not a
validated physical constitutive curve. Its tangent and gap have different
sources and different limits. Do not use the old Zhang–Gao–Xu M36 verification
as an extrapolation to Unified 1/4-20; it is not used in this calculation.

## Compliance partition and fit limits

The tangent comes from Matsubara and Teranishi's series-model component
`Kth = As Eb / Lth`, `Lth = 0.85d`, with the nominal Unified tensile stress
area from NBS Handbook 28 Supplement (1963) substituted for the paper's JIS
B1082 area. At 1/4-20 and the project's generic steel reference modulus, this
produces the stated result. The paper validates aggregate timber-joint
tightening stiffness with M12 metric fasteners; it does not isolate the
thread component or directly validate a Unified 1/4-20 matched pair. The
stress-area substitution is explicit model adaptation, not proof that the
stress area equals the engaged thread pair's local elastic area. See the
[primary paper](https://link.springer.com/article/10.1186/s10086-022-02038-1)
and the local
[steel modulus scenario](../../steel-elastic-material-scenario.md).

Keep the components separate in a solid model:

- This connector contribution is the source model's post-seating equivalent
  thread-engagement term only. The equivalent length `0.85d` is not physical
  overlap, nut thickness, or a resolved turn count.
- A deformable bolt body already supplies its own axial extension. Do not add
  that body `EA/L` compliance to this connector again. A rigid nut supplies no
  nut-body compliance; that modeling choice does not make a real nut rigid.
- Washer-seat and timber deformation stay in their own represented bodies or
  contacts. The H28 gap is free travel, not compliance. The paper's `Ks` term
  for non-engaged threaded bolt length is not flank backlash.

The slack values are based on the
[NBS Handbook H28 (1969), Part I](https://nvlpubs.nist.gov/nistpubs/Legacy/hb/nbshandbook28-1969p1.pdf)
and its ideal 60-degree functional-diameter relation. The active ASME
[B1.1-2024 record](https://www.asme.org/codes-standards/find-codes-standards/b1-1-unified-inch-screw-threads-un-unr-thread-form)
confirms the current standard covers Unified forms, series, classes,
allowances, tolerances, and dimensions, but its public record does not expose
the numeric 1/4-20 table used here. The H28 numbers are therefore a historical
reference comparator, not current procurement limits or acceptance
dimensions.

The catalog nut thickness interval `5.3848–5.7404 mm` is not its active
female thread height. The exact missing geometric parameter is the axial
overlap of mutually complete male and female thread forms after bolt runout
and nut entry/exit chamfers, measured from the seated nut-bearing plane. The
current hardware basis does not provide the bolt's first-full-thread
coordinate or the nut's active full-form interval. Catalog `LG`, `LB`, overall
length, and nut thickness do not establish that intersection or full-height
functional engagement. The currently documented full-height receiving gate
remains distinct from this ideal class comparator.

## Precise applicability boundary

The calculation makes limited progress: it provides a finite post-seating
analytical scenario and a separate idealized class-fit travel interval using
existing primary-source inputs. It does not meet the evidence-route test for
a physical finite law. No M36 result is transferred. No stiffness bound or
capacity is claimed. A same-product coupon is not a universal prerequisite;
a directly applicable published dataset or a validated analytical/numerical
model may support a finite law if its demonstrated domain covers the declared
Unified profile, fit, engagement, materials, and loading range.

The exact outstanding evidence is:

1. Current B1.1-2024 numeric 1/4-20 UNC-2A/2B pitch-diameter/profile limits
   (or delivered effective profile measurements); the H28 values are only a
   reference-edition comparator.
2. A Unified 1/4-20 thread-pair compliance law validated over the applicable
   normalized profile, nut body, fit, engagement, material, and load domain.
   Existing M12 composite tightening validation does not isolate `Kth`.
3. Actual full-form overlap coordinates after male runout and female
   chamfers, plus initial flank phase and whether relative nut rotation is
   restrained or axial travel is limited by measured stops.

Until those inputs are resolved, physical WJ04 axial transfer remains
`UNRESOLVED_AXIAL_ENGAGEMENT`. Do not transfer the hypothetical 1/4-20 class
scenario to provisional WJ24 stacks, which have no selected thread class or
SKU. The separate source-backed sensitivity route can continue without
claiming this law is physical or requiring a product coupon for every
response calculation.
