# Wider-leg criterion source audit

The current result is a conservative conditional design screen. Its lateral resistance uses recognized wood-connection equations, but several inputs are deliberately conservative approximations. The earlier statement that this oblique joint unequivocally requires 50.8 mm loaded-edge distance was too strong: 50.8 mm is the perpendicular-load rule adopted as the oblique-load screen, not a specifically prescribed oblique-load minimum.

## Edge distances and placement

The locally downloaded **2024 NDS Chapter 12**, section 12.5.1 and Tables 12.5.1A–D, supplies the numerical placement values. For a 12.7 mm bolt, the perpendicular loaded-edge minimum is 4D = 50.8 mm; the unloaded/parallel edge minimum for this thickness ratio is 1.5D = 19.05 mm. The geometry-factor provisions permit qualifying reductions for end distance and along-row spacing. They do not provide a reduced loaded-edge factor. The current 7D requirement at both ends is conservative where load instead bears away from an end; it is not governing this candidate.

The publicly accessible **2018 NDS Commentary C12.5.1** expressly explains that the specification gives neither an oblique-load edge-distance rule nor a reduced-edge geometry factor. It attributes the perpendicular 4D value to early research and calls the unloaded 1.5D value a good-practice recommendation. This is historical explanatory evidence; no 2018 numerical resistance values replace the 2024 calculation. The available 2024 Chapter 12 extract contains the specification, not that commentary passage. [AWC 2018 Commentary, printed page 264, PDF page 72](https://awc.org/wp-content/uploads/2021/10/AWC_NDS2018-withCommentary_20200827_AWCWebsite_Commentary.pdf).

Applying 4D whenever a bolt pushes across grain is a defensible conservative screen for splitting-sensitive timber, but the nonzero-component cutoff is our modeling choice. At the stored lateral-governing middle-third case, rim bolts 5 and 6 have approximately 42.53° and 18.12° load angles to grain, with transverse forces 600 and 214 N. At the whole-foot governing case their angles are 28.72° and 24.96°, with transverse forces 665 and 565 N. These are meaningful transverse loads, not numerical noise. Their 38.045 mm edge distance is about 3D. It falls below the adopted screen; the calculation does not establish that 3D physically breaks or supply a validated capacity for it. Linear interpolation between 1.5D and 4D would be an invented rule and is not used.

## Lateral resistance and conservative choices

[AWC Technical Report 12](https://web-media.awc.org/wp-content/uploads/2021/12/17210714/AWC-TR12-1510.pdf) derives the single-fastener yield equations. The code's zero-gap, two-solid-member equations follow that formulation. Its reference resistance is the smallest mode yield value divided by the applicable NDS reduction term; it is an allowable/reference resistance, not ultimate rupture strength. These reductions already belong to the design method and should not simply be removed.

2024 NDS Table 12.3.1B specifies mode multipliers 4, 3.6 and 3.2, each multiplied by Kθ = 1 + 0.25θ/90. θ is the largest acute force-to-grain angle among the connected members. The present constants 5, 4.5 and 4 assume the worst θ = 90°. Using each bolt's actual angle is an appropriate refinement, not relaxed safety policy.

Recomputing the stored governing cases with that refinement gives:

| Assumptions | Middle-third lateral ratio | Whole-foot lateral ratio |
| --- | ---: | ---: |
| Existing worst-angle reduction, Fyb = 45 ksi | 0.8175 | 1.7283 |
| Actual-angle reduction, Fyb = 45 ksi | 0.8004 | 1.6829 |
| Actual-angle reduction, Fyb = 92 ksi | 0.8004 | 1.6829 |

These rows reproduce the stored governing cases, not a replacement full load sweep. Mode II governs these values. It depends on wood bearing and bolt rotation, so increased steel bending yield strength does not improve them. The specified Grade 5 bolt can have greater yield strength than the generic 45 ksi bolt-table basis; NDS 12.3.6.2 allows bending strength based on the prescribed bending or tensile test methods. Product certification and smooth-body geometry still matter.

The six-fastener group factor is 0.95092. It treats the pattern as a conservative hypothetical six-fastener row using the old smaller member stiffness and maximum pitch. The actual two-by-three group is not literally that row. NDS group action concerns fasteners aligned with load and the participating member areas; the present factor is a screen, not a solved eccentric-group stiffness distribution. Its effect is small: omitting it entirely would reduce the ratio by 4.9%, insufficient by itself to remove the whole-foot exceedance. A valid detailed replacement must also address the unequal bearing stiffness and clearances behind the equal-stiffness elastic bolt allocation.

## Load duration

2024 NDS Appendix B describes normal-duration references as approximately ten years of cumulative maximum load. The current CD = 1 for climber cases is conservative for a brief peak. Appendix B permits connection duration adjustments up to 1.6; the 2.0 impact factor does not apply to connections, and duration increases do not apply to separately checked metal-part capacity or deformation-based perpendicular wood bearing.

A 1.6 sensitivity is reasonable to show the effect of short-duration classification. Automatically granting it because one move lasts seconds is not justified: repeated peak loading accumulates, and longer-duration load combinations must also be checked. A chosen climbing use/load-duration basis is required. Permanent cases correctly retain CD = 0.9. With actual-angle reduction, the whole-foot lateral-only ratio divided by 1.6 is approximately 1.052; this still exceeds unity at the stored governing case and does not address edge geometry or prying.

## Primary numerical references

- [2024 NDS Chapter 12, sections 12.3.1, 12.3.6 and 12.5.1](https://awc.org/wp-content/uploads/2026/08/AWC_NDS2024_withCommentary_20250328_WebsiteChapter-12-%E2%80%93-Dowel-type-fasteners.pdf). Local source: `/tmp/reinforced-NDS2024-ch12.pdf`, extracted `/tmp/reinforced-ch12-plain.txt`.
- 2024 NDS Appendix B, local primary document `/tmp/reinforced-NDS2024-appendix.pdf`, extracted `/tmp/reinforced-appendix-plain.txt`. Use same-edition adjustment provisions with the current material values.
- [AWC 2024 NDS landing page](https://awc.org/resources/2024-nds/).

This audit does not change CAD, select a replacement connection or establish a climber collapse weight. It distinguishes recognized criteria from deliberately conservative modeling choices so the accompanying sensitivity analysis can report meaningful conditional limits.
