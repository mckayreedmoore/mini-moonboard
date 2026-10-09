# Heel comparison assumptions

The `235/1.67 = 140.718563 MPa` comparison has a documented engineering
basis. The chosen **6-mm thickness and 6-mm inside radius are analytical
scenarios**, without delivered-part minima. The small fixed-action study
below shows that the reported 11.35% reference exceedance is sensitive to
those missing dimensions. It supplies a specific measurement question; it
does not settle actual heel resistance. Preserve the issued
[six-case numerical closeout](../fixed-floor-numerical-mvp-v1.json), including
its seven exceeding heel rows and all physical limitations.

[Inputs](inputs.json), [primary-source observations](sources.json),
[calculation](analyze.py) and [result](result.json) form this separate, compact
assumption study. It consumes all six exact raised-rail steel reports through
the closed joint envelope. It reuses the original kernel and known answers,
without copying them, rebuilding candidate geometry, obtaining a new demand field or
reopening the floor or panel work.

The recorded comparison was assembled in the following steps.

| Input | Recorded origin | Interpretation |
| --- | --- | --- |
| Minimum yield 235 MPa | Existing pinned material guide, Table C.2, for plain Q235B at `0<t<=16 mm`; seller describes Q235B | Reasonable conditional base-metal property. Material conformance and finished-part behavior are unverified. |
| Factor 1.67 | Representative strength screen cites Goel (1986), Equation 2 | An elastic equivalent-stress benchmark; not a manufacturer angle rating. |
| Thickness 6 mm | Seller description says `1/4 inch (6 mm)`; its diagram says `1/4 inch` | The original study compares both metric and inch nominals. Neither is a guaranteed minimum metal thickness. |
| Inside radius 6 mm | Original representative calculation samples `Ri=t` and `Ri=2t`; the reusable packet freezes `t6/Ri6` | A generic curvature scenario. The record supplies no product-specific derivation for Ri6. |
| Loads and selfweight | Each own admitted case, its saved half-band root wrench and source body weight | These stay fixed in this study. Full source weight is deliberately overcounted in each heel screen; actual plate load sharing is unqualified. |

The precise source paths and SHA256 bindings are in `inputs.json`. The source
diagram was already preserved in the parent packet; the primary live listing
still describes the conflicting inch/metric nominals and supplies no bend
radius or tolerances. No new part measurement has been made, and the owner
has not purchased these brackets.

[Goel's paper](https://ej.aisc.org/index.php/engj/article/download/467/466/466)
uses the von Mises interaction with a 1.67 factor to address combined normal
and shear stress. This supports keeping a rational elastic-yield comparison.
It does not establish the curved three-dimensional stress field of this part.
The paper's concluding empirical interaction is distinct from the Equation 2
benchmark used here.

The official indexed [AISC 360-16](https://www.aisc.org/globalassets/aisc/publications/standards/a360-16w-rev-june-2019.pdf)
F1/H3.3 provisions corroborate 1.67 as an ASD factor for applicable flexural
and torsional strengths. They apply it within specific limit-state methods.
They do not turn every computed peak stress into a complete connector
allowable. The direct PDF fetch was blocked; this is corroboration from
official indexed excerpts, not a new full-code review. The source
[NPTEL solution](https://archive.nptel.ac.in/content/storage2/courses/105106049/lecnotes/mainch10.html)
is for an ideal unholed annular sector in pure bending. Added end-force,
torsional and other-bending terms retain their component-screen limits.

Common connector evaluation uses an applicable static model supported by
tests. [EOTA's worked angle example](https://www.eota.eu/sites/default/files/uploads/Technical%20reports/eota-tr017-am.pdf)
uses net-section plastic bending for plane parts and tested rib capacities.
That illustrates a different strength method, not plastic reserve we may
automatically credit here. [Simpson's published approach](https://www.strongtie.com/products/connectors/wood-construction-connectors/technical-notes/allowable-loads)
normally uses at least three wood-assembly tests and the lower of ultimate
load divided by three, deflection limits and fastener calculations. Its
ultimate-test factor is distinct from an elastic-yield factor. No comparator
capacity or test factor is transferred to eoere.

The numerical question is whether the same reference outcome persists when
the unspecified dimensions vary. The calculation first reproduces **all
528 issued heel comparisons exactly**, including the seven exceedances.
It verifies **647 distinct direct and inherited source pins before and
after**, then evaluates 16 thickness/radius combinations. Additional
pure-bending fixtures recover the prescribed 25,000-Nmm moment to
`1.27e-9 Nmm`, with zero-force error below `4.41e-11 N` and surface radial
stress error below `2.28e-13 MPa`. These fixtures verify the ideal solution;
they do not validate the manufactured angle.

All rows below keep the original neutral datum, 44.45-mm half-band width,
root force/free-couple vectors and source gravity envelope. None is a new
compatible response or product thickness/radius observation.

| Thickness scenario mm | Inside radius scenario mm | Worst screen MPa | Ratio to 140.718563 MPa | Exceeding case/band rows |
| ---: | ---: | ---: | ---: | ---: |
| 6.00 | 3.00 | 183.105601 | 1.301219 | 13 |
| 6.00 | 6.00 | 156.689841 | 1.113498 | 7 |
| 6.00 | 12.00 | 141.320205 | 1.004275 | 1 |
| 6.35 | 3.00 | 166.549070 | 1.183561 | 9 |
| 6.35 | 6.00 | 141.983371 | 1.008988 | 1 |
| 6.35 | 8.00 | 135.008100 | 0.959419 | 0 |

The worst witness remains A12-left, `eoere_clip_single_top_left_1`,
`arm-z/far-plus`. Scalar equality occurs at thickness **6.382860 mm** with
Ri6; at radius **6.291923 mm** with thickness6.35; or at radius
**12.459141 mm** with thickness6. These are mathematical sensitivity
boundaries, **not receiving limits, purchase specifications or design
acceptance**. Actual radius changes can move hole/tangent geometry and change
stiffness and demands. The sampled radii are illustrative, not an asserted
manufacturing range. No factor was relaxed to obtain a lower ratio.

For the issued worst row, the unadjusted conditional base-metal yield index
is **0.666765**. Exceeding the reduced 140.718563-MPa benchmark is therefore
distinct from reaching the assumed 235-MPa first-yield level. Both statements
remain conditional on the ideal stress screen and assumed material.

The smallest next check is dimensional: obtain a supplier drawing with
minimum **metal** thickness, inside/outside radius, bend thinning and the
hole/heel datums, or measure a sample with a micrometer and radius/profile
gauge. Coating-inclusive caliper readings and perspective pixels cannot
establish those minima. The published picture already available does not
resolve them. This is the useful next input before another frame solve or
redesign decision based only on the heel screen.

If a sample becomes available, a small component test can investigate whether
the assumed deformation mode is credible. [EAD 130186-00-0603](https://www.eota.eu/download?file=/2016/16-13-0186/ead+for+ojeu/ead+130186-00-0603_ojeu2020.pdf),
2.2.1.2.2–2.2.1.2.3, describes model calibration over relevant force positions
and a known-eccentricity flange bending fixture. The following is a proposed
elastic diagnostic, not that standard's qualification program:

1. Measure the bracket first. Restrain one flange using the intended active
   far-hole pair; record the actual fasteners, support and clamp conditions.
2. Apply controlled opening and closing force through the other far-hole
   pair, first symmetrically, then off center. An initial load/unload sequence
   of **0, 25, 50, 100, 50, 25, 0 N** gives **0, 1.63, 3.25, 6.51 Nm** at an
   actually measured 65.09-mm arm. Use actual eccentricity in `M=F*e`.
3. Measure both flange sides and fixture movement separately with a dial
   indicator capable of resolving about **0.001 mm**. Record force,
   displacement, rotation, slip and residual opening; repeat three cycles.
   Stop the diagnostic if permanent opening or fixture/bolt slip appears.

The force levels are a low-load investigation proposal, not a guaranteed
elastic range or proof load. They can expose wrong stiffness or support
assumptions, but cannot establish material yield strength or whole-joint
capacity. A subsequent strength test would need its own specimen, failure
criterion, loading combination and interpretation.

A centered test alone misses an important mode. In the frozen A12-left
report, the same angle's whole `arm-z` flange root has approximately
**30.0 Nm torsion, 10.4 Nm out-of-plane bending and 24.6 Nm in-plane
bending**. The reported **29.1 Nm** out-of-plane moment belongs to one
half-band; the other band partly opposes it. Those saved vectors explain
why width sharing and twisting require attention, and why a uniform
full-width shelf-bending substitution would not resolve this study.

The study's conclusion is to retain the existing reference and closed
exceedances, while identifying unverified geometry and three-dimensional
behavior as the next uncertainties. This study does not justify a heel-driven
frame redesign or an actual bracket pass by itself. Complete timber joints,
bolts, washers, panels and the rest of the recorded limitations retain their
own dispositions.

Reproduce from the repository root into a new output path:

```sh
.venv/bin/python -B docs/wood-joints-mvp/hypotheses/hl35-candidate/thin-frame-comparison/eoere-successor-v1/heel-assumptions-v1/analyze.py --out /tmp/moonboard-heel-assumptions-reproduced.json
```

Pinned versions are Python3.12.3, NumPy2.5.2 and SciPy1.18.1. Output files are
never overwritten. Keep this compact method/result packet active, together
with the existing closed reports and shared sources it consumes. It adds no
bulky raw run, CAD export, native solve, duplicated manual or archive/prune
operation. The current development summary and evidence ledger should link
this study; the issued baseline and numerical closure remain immutable.
