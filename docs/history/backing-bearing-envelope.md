# Conditional backing-washer wood-bearing envelope

Checked against the **2024 NDS and its matching 2024 Supplement** on
2026-09-08. This isolates wood compression beneath the two washer bearing planes
of a backing bolt. It is not a bolt, washer, housed connection or board capacity.

## Verified reference values and applicability

The 2024 Supplement, Table 4A, printed page 34, gives **625 psi** compression
perpendicular to grain for visually graded Douglas Fir-Larch / Douglas Fir /
Western Larch, including No.2. The listed northern group also has 625 psi.
Table 4A covers nominal 2–4 inch thickness: both a nominal 2×4 backing and a
nominal 4×6 principal fall within that thickness scope. Do not switch the 4×6
to the 5-inch-and-larger timber table merely because its width is six inches.
Actual grade/species stamps still must establish applicability; an unspecified
“fir” or mixed-species stamp is insufficient.
[2024 Supplement, Table 4A, p.34](https://awc.org/wp-content/uploads/2026/08/AWC_NDS2024-Supplement_20240719_Chapter-4-Reference-Design-Values_Website-1.pdf).

The same Supplement's Table 4A adjustment factors, printed page 32, give a
compression-perpendicular wet-service factor of **0.67** when moisture exceeds
19% for an extended period. Dry service is assumed for the first calculation;
kiln-dried purchase condition alone does not establish future service moisture.
[Table 4A adjustment factors, p.32](https://awc.org/wp-content/uploads/2026/08/AWC_NDS2024-Supplement_20240719_Chapter-4-Reference-Design-Values_Website-1.pdf).

NDS §3.10.2 requires the net bearing area. Section 3.10.4 allows a bearing-area
increase only for bearings shorter than six inches and not nearer than three
inches to a member end; round washers use their diameter as bearing length.
**No such increase is used here: Cb=1.0.** The near-end/housed principal detail
has not been qualified for an increase.
[2024 NDS §§3.10.2–3.10.4, p.26](https://web-media.awc.org/wp-content/uploads/2021/12/17210019/AWC_NDS2024_withCommentary_20240718_AWCWebsite_Chapter-3-Design-Provisions-and-Equations.pdf).

NDS §4.3.2 excludes compression perpendicular to grain from load-duration
increases. Section 4.2.6 explains that the tabulated value corresponds to a
0.04 inch (1.016 mm) deformation basis, not ultimate crushing strength. Its
optional 0.02 inch deformation basis uses 0.73 times the reference value.
For this simple ASD envelope assume ordinary-temperature, untreated/unincised
stock and no optional increases; unusual treatment, temperature or material
conditions require their applicable adjustments.
[2024 NDS §§4.2.6–4.3.4, p.30; adjustment table p.31](https://web-media.awc.org/wp-content/uploads/2021/12/17210008/AWC_NDS2024_20241011_AWCWebsite_Chapter4.pdf).

## Geometry and arithmetic

Using the current selected washer's minimum outside diameter **20.447 mm**
and modeled wood bore **11.1125 mm**, the maximum available net annular wood
contact area under the stated full-contact assumption is:

`A = π/4 × (20.447² − 11.1125²) = 231.3721 mm²`

This subtracts the wood hole, not merely the smaller washer hole. The area is
based on the larger unsupported diameter: maximum selected washer ID 10.6426 mm
versus modeled wood bore 11.1125 mm. The latter governs here; actual drilling
tolerance is unresolved and an enlarged bore would reduce the available area.
The area is
available only if the annulus lands fully on sound wood and the washer can
distribute pressure over it. The front washer bears on the counterbore floor in
the backing; the rear washer bears on the principal. The bolt/washer load
direction is normal to both members' longitudinal grain directions.

| Conditional wood-bearing case, per plane | Stress | Force from `A × stress` |
| --- | ---: | ---: |
| Dry, no optional increases | 625 psi / 4.3092 N/mm² | 997.03 N / 224.14 lbf |
| Wet-service factor only | 418.75 psi / 2.8872 N/mm² | 668.01 N / 150.18 lbf |
| Dry, optional 0.02-inch deformation basis | 456.25 psi / 3.1457 N/mm² | 727.83 N / 163.62 lbf |

These are alternative conditional cases, not additive allowances. Both washer
planes carry the same axial bolt action in series: **two washers do not double
997 N into 1,994 N**. Nor may two backing bolts be assumed to share demand equally.
Widening the principal improves its geometric edge distance but leaves these
washer areas unchanged; the same envelope therefore applies to narrow and wide
principals under identical material/contact assumptions.

## What this does and does not settle

It is defensible to report approximately **1.00 kN per bearing plane under the
dry assumptions as a wood-bearing-only envelope**. It is not defensible to call
that a qualified axial joint load. Washer flexure, incomplete contact, local
pressure concentration, counterbore-floor ligament failure, splitting, prying,
bolt bending, net section and combined lateral/axial loading remain unchecked.
Assembly preload also produces bearing pressure; this figure is not an additional
external-load allowance on top of an unspecified preload.

The current FE models do not recover an independently qualified force for each
backing bolt. A demand comparison therefore remains pending. Establish the actual
washer stiffness/contact area, stock identity/service conditions, acceptable
deformation and local load path before using this envelope to select hardware
or claim a connection passes. No CAD, procurement or historical result changes
are made by this calculation.

Reproduce the arithmetic independently of CAD with:

```python
from fea.backing_bearing import envelope

dry_fc_perp = 625 * 0.006894757293168361  # psi to N/mm²
dry = envelope(20.447, 11.1125, dry_fc_perp)
wet = envelope(20.447, 11.1125, dry_fc_perp * 0.67)
print(dry, wet)
```

This helper computes an assumed bearing envelope, not an actual qualified limit.
