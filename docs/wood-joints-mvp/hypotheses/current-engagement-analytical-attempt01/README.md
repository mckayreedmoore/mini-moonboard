# WJ24 nominal 1/4-20 post-seating engagement tangent

**Attempt:** 01. **Prepared:** 2026-09-25. **Status:** reproducible,
conditional analytical model scenario; not a hardware selection or physical
connection acceptance. The calculation is intentionally limited to one
nominal bolt/nut engagement component. It does not model the four-stack patch
or sum stiffness across bolts.

## Current target and declared inputs

The WJ24 [ordinary hardware basis](../../current-ordinary-hardware-basis.md)
records 92 candidate axes overall and 48 current axes with 152.4 mm modeled
shaft occupancy and 127 mm nominal wood grip. Their 6.35 mm CAD cylinders are
unthreaded analysis envelopes. WJ24 selects no delivered bolt/nut pair,
thread class, surface condition, or functional fit. The 1/4-20 dimensions
below are a nominal Unified geometry hypothesis for response modeling; they
do not assign a SKU or transfer the WJ04 K.L. Jack example.

| Input | Value | Source / scope |
|---|---:|---|
| Nominal major diameter, `D = d` | 0.25 in = 6.35 mm | Current nominal 1/4 in geometry hypothesis |
| Thread series / count | Unified 20 TPI, coarse series (UNC hypothesis) | `n = 20 threads/in`; exact WJ24 class is unresolved |
| Pitch, `p = 1/n` | 0.05 in = 1.27 mm | Computed from nominal thread count |
| Steel Young's modulus, `E_b` | 200,000 N/mm² | Generic reference in [project steel elastic scenario](../../steel-elastic-material-scenario.md), based on AISC 360-22; not a measured WJ24 hardware value |
| Engagement equivalent-length ratio | `L_th/d = 0.85` | Matsubara & Teranishi Eq. (9), inherited from their cited analytical source |
| Thread area used by the stiffness equation, `A_s` | 20.5296315 mm² | NIST Unified tensile stress-area equation evaluated at nominal `D,n`; adaptation described below |

The source model uses `A_s` as the effective cross-sectional area and cites
JIS B1082. For this Unified-size scenario, `A_s` is calculated with the NIST
legacy Unified-thread tensile-stress-area equation

```text
A_s = 0.7854 (D - 0.9743/n)^2 in²
```

where `D = 0.25 in` and `n = 20/in`. This gives `0.031820992472 in²`; applying
`25.4² mm²/in²` gives `20.529631503310 mm²`. NIST defines this as an assumed
area for direct tensile-strength calculation. Substituting it for the JIS
`A_s` in an elastic-stiffness equation is an explicit engineering adaptation,
not a claim that the stress area is the true local elastic area of the
engaged thread pair. Current [ASME B1.1-2024](https://www.asme.org/codes-standards/find-codes-standards/b1-1-unified-inch-screw-threads-un-unr-thread-form)
defines Unified profile, series, class, tolerances, and dimensions; it does not
give a spring law for engaged threads.

## Calculation

Matsubara and Teranishi write the bolt contribution as a series combination
of thread engagement, non-engaged threaded length, cylindrical shank, and
head components (Eq. 4); the engagement component is

```text
K_th = A_s E_b / L_th
L_th = 0.85 d
```

For this nominal scenario:

```text
L_th = 0.85 × 6.35 mm = 5.3975 mm
K_th = (20.529631503310 mm² × 200,000 N/mm²) / 5.3975 mm
     = 760,708.902 N/mm = 760.708902 kN/mm
C_th = 1/K_th = 1.314563 × 10⁻⁶ mm/N = 0.001314563 mm/kN
```

At this tangent, 1 kN corresponds to 0.0013146 mm (1.315 μm) of relative
engagement deformation. `L_th` is an equivalent elastic-cylinder length from
the analytical model; it is **not** the physical thread overlap, nut height,
or a claim of 5.3975 mm of full-form engagement.

| `E_b` scenario | `K_th` | `C_th` |
|---:|---:|---:|
| 180,000 MPa | 684.638012 kN/mm | 0.001460626 mm/kN |
| 200,000 MPa | 760.708902 kN/mm | 0.001314563 mm/kN |
| 220,000 MPa | 836.779793 kN/mm | 0.001195058 mm/kN |

The low and high values carry forward the existing analyst-declared `±10%`
elastic-modulus perturbation. They are numerical sensitivity points, not
confidence limits, actual lot-property bounds, or a bracket on thread-fit and
contact effects. The scalar axial law uses `E` and `A_s`; Poisson ratio is not
an independent term in this calculation.

The numerical inputs and outputs are also recorded in
[`calculation.json`](calculation.json).

## What the source validates, and what it does not

Matsubara and Teranishi, [“Evaluation of elastic stiffness in bolted timber
joints for applying turn-of-nut method”](https://link.springer.com/article/10.1186/s10086-022-02038-1),
2022, Eqs. (3)–(10), model a timber joint's elastic tightening stiffness as
the series combination of the bolt and washer embedment. Their Eq. (4)
decomposes the bolt term; Eq. (5) gives `K_th = A_s E_b/L_th`; Eq. (9) gives
`L_th = 0.85d`. They use `E_b = 205,000 MPa` and cite JIS B1082 for the stress
area. The model uses equivalent lengths for the thread-engagement and bolt
head components.

Their tightening tests use M12 SWCH hex bolts, 1.75 mm pitch, 85 mm length,
30 mm thread length, and four timber species, with 12 specimens per species.
The measured and calculated quantity is the **combined timber-joint
tightening stiffness**. The reported agreement supports that composite model
in those tested arrangements. It does not directly isolate `K_th`, test
Unified threads, measure thread clearance, or establish an error interval for
1/4-20. Its tests start when bolt force reaches 10 N and fit the linear
elastic region; the authors report initial low-force slip before the
near-linear region. Thus the published component equation is enough to
calculate a nominal-size model scenario, but that diameter substitution is
not direct validation of the current hardware.

The formula is useful here because its component form is explicit in
effective area, elastic modulus, and a nominal-diameter-scaled effective
length. A paper need not have tested every nominal diameter for the formula to
define a *conditional analytical scenario*. The missing 1/4-20 validation
still prevents relabeling that scenario as a product-specific physical law or
as a complete joint bound. The ASME standard is the authority for Unified
thread geometry and class limits, not for `K_th`.

## Preload-free seating and thread strength remain separate

This calculation only describes the tangent after a load-bearing flank has
made contact. No preload is assumed. Before contact, the relative axial
travel depends on initial geometry, external and internal thread tolerances,
lead error, coatings, nut chamfer, partial threads, and installed orientation.
WJ24 currently has no exact external/internal classes or measured matched
profiles, so no source-bound seating/backlash value is available. Treating
`g = 0` as an initial state is a zero-slack comparator only. The initial-slip
region in the Matsubara timber tightening test does not measure bolt/nut
backlash; its model's `L_s` is the axial length of non-engaged threaded bolt
in the series spring chain.

The law does not provide thread pullout or stripping resistance. The NIST
`A_s` is a stress area, and ASME B1.1 lists a separate nonmandatory appendix
for thread-strength design formulas. Neither elastic modulus nor `K_th`
sets bolt proof/yield strength, nut proof strength, internal/external thread
shear strength, or complete-joint resistance. Those require the actual
material/property classes, full-form engagement, and applicable strength
checks. Keep physical axial engagement `UNRESOLVED_AXIAL_ENGAGEMENT` until
those inputs and a defensible physical engagement treatment are available.

## Source record

1. Doppo Matsubara and Masaki Teranishi, “Evaluation of elastic stiffness in
   bolted timber joints for applying turn-of-nut method,” *Journal of Wood
   Science* 68, 32 (2022), Eqs. (3)–(10), test methods and results. The paper
   directly supports its equivalent-spring form, test setup, initial slip,
   and aggregate agreement; it does not validate the WJ24 size/fit.
2. [ASME B1.1-2024, Unified Inch Screw Threads](https://www.asme.org/codes-standards/find-codes-standards/b1-1-unified-inch-screw-threads-un-unr-thread-form).
   The standard specifies Unified forms, series, classes, allowances,
   tolerances, and dimensions; its Appendix B is for thread-strength design.
   It supplies no engagement-compliance curve.
3. National Bureau of Standards, [Handbook 28 Supplement (1963), screw-thread
   standards](https://nvlpubs.nist.gov/nistpubs/Legacy/hb/nbshandbook28supp1963.pdf),
   tensile stress-area definition and equation for Unified inch threads.
   This is a government standards source for the nominal area calculation,
   not an elastic spring validation.
4. Project [generic steel elastic scenario](../../steel-elastic-material-scenario.md)
   and [current WJ24 ordinary hardware basis](../../current-ordinary-hardware-basis.md).
   These bind the chosen modulus perturbations and the current unselected
   analysis envelope; they do not establish delivered hardware properties or
   fit.
