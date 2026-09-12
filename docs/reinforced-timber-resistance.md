# Reinforced candidate: current timber resistance calculations

This calculation consumes the current `round-reinforcement-development` native
member cuts and individual bolt vectors. It does not transfer predecessor
forces. The two cases are F10 at joint stiffness 1,000 N/mm
(`/tmp/reinforced-F10-k1000-v4/report.json`) and 10,000 N/mm
(`/tmp/reinforced-F10-k10000-v5/report.json`). Equilibrium, printed MPC and
contact active-set checks pass for both. The baseline center-post force-only
friction lower bounds are approximately 0.893 and 0.767, exceeding 0.4; the
harder case reaches approximately 2.274 at the left center post. These are
necessary force-only bounds, distinct from sufficient bounds that also
construct yaw-resisting contact tractions. Neither case is **a valid physical
solution for the stated 0.4 friction installation condition**.
Consequently the strength comparisons below are conditional diagnostic results,
not acceptance of the installed structure. Individual recovered member cuts
also retain their printed force and moment residuals (up to approximately
2.25 N and 3,202 Nmm); these are included in the evidence.

## Results and useful revisions

The combined evidence is `fea/results/reinforced-timber-resistance-v3.json`.
Earlier v1/v2 outputs retain their original inputs and source hashes.

The companion `fea/results/reinforced-timber-roundoff-v2.json` binds the
producer's section uncertainty files to the exact native report hashes.
After reducing every action by its printed-precision radius, necessary
fully-braced top-rail interactions remain **at least 1.177 and 1.030**,
respectively. Thus neither top-rail failure is explained by native printing.
The hard-case right-fourth leg bolt has XYZ force uncertainty only
±(0.001, 0.001, 0.00055) N.

| Conditional check | 1,000 N/mm | 10,000 N/mm |
| --- | ---: | ---: |
| Top-rail beam-column interaction | 1.571 | 1.262 |
| Top-rail necessary interaction even fully braced | 1.202 | 1.040 |
| Maximum individual leg-bolt lateral ratio | 0.946 | **1.839** |
| Maximum shoe timber lateral ratio | 0.635 | 0.619 |
| Maximum leg-washer incremental wood-bearing ratio | 0.303 | 0.400 |
| Maximum shoe-plate incremental wood-bearing ratio | 0.082 | 0.176 |
| Conservative Appendix E parallel local-group ratio | 0.326 | 0.568 |


The single 2x6 top rail fails the gross-section biaxial beam-column check:
maximum interaction approximately **1.571**. At the governing cut it has
408 N compression, 8.022 MPa strong-axis bending and 1.599 MPa weak-axis bending.
Even ideal bracing cannot remove the necessary stress interaction of
**1.202**. The failure therefore is not solely a conservative unbraced-length choice.
No LED or fastener hole is needed to produce this failure.

Using the same actions only to screen a possible replacement, a single 2x8
reduces the interaction to approximately 0.976 but retains the excessive
weak-axis compression slenderness. A **single 3x6 top rail** reduces it to
approximately 0.686 and its slenderness to 37.2. This is a useful next geometry
revision, not a qualified substitution: attachment fit, stock availability,
changed stiffness, demands and openings require the revised model. No built-up
vertical member is proposed.

Other initial gross-section stress interactions are at most approximately
0.610; legs reach 0.351 and 0.335. However, the full-unbraced compression
sensitivity gives slenderness approximately 62–64 for rims, center principals,
header and top rail, exceeding the NDS permanent-column limit of 50 wherever
compression occurs. Intermediate lateral and twist restraint must be supplied
and checked; nearby panels or clips do not automatically supply that restraint.
With 38.1 mm weak dimension, the maximum qualifying effective length is
**1,905 mm**. This is a quantitative restraint requirement, not a claim that
merely placing a brace at that spacing qualifies its load path.

The baseline directional leg-bolt yield check reaches approximately **0.946**
at left bolt 4. The harder-joint case fails at six of eight leg bolts, with
right bolt 4 reaching **1.839**: 1,323.6 N lateral demand versus 719.6 N
conditional resistance. The governing Mode II is timber bearing and bolt
rotation, not steel rupture. Increasing steel grade alone cannot fix it.
Crediting a full 3/8-inch smooth shank throughout leaves approximately
1.462 under the same actions and conservative Ktheta=1.25 screen.
That figure is not a universal capacity upper bound: the roundoff companion
separately uses best-direction bearing and Ktheta=1 for its optimistic bound. A revised bolt pattern,
additional independently analyzed connection, or changed leg restraint/load
path is needed; selecting one requires a floor-admissible response first.
Shoe wood lateral yield remains below approximately **0.635** in both cases. These
checks assume a verified bolt bending yield strength of at least 45 ksi;
**current A307 identification does not establish that property**. The source
supported route is to specify SAE J429 Grade 1 with the applicable dimensional
and receiving conditions, or obtain a supported bending-yield basis for the
actual bolt. The unused historical 4¼-inch Grade 5 hardware trial is not the
current 3¾-inch leg bolt. Its specifications do not transfer.

The header shoe rows are 130 mm apart across grain. NDS 12.5.1.3 permits at
most 127 mm without special shrinkage detailing. **Current detail fails by
3 mm.** Moving the −210 mm row to −206 mm gives 126 mm nominal and a 1 mm total
spread allowance; both hole-position tolerances must fit inside that allowance.
The CAD is intentionally frozen for this calculation, so no revised row is
represented as already installed or checked.

## Materials and adjustment assumptions

The calculation specifies US Douglas Fir–Larch No. 2, dry-service, unincised
sawn lumber. The actual grade stamp/species remain receiving requirements.
NDS 2024 Supplement Table 4A gives Fb 900 psi, Ft 575 psi, Fv 180 psi,
Fc perpendicular 625 psi, Fc parallel 1,350 psi, E 1,600,000 psi and
Emin 580,000 psi. Table 4A size factors for nominal 2x6 are 1.3 in bending,
1.3 in tension and 1.1 in compression; for the 2x10 header they are 1.1,
1.1 and 1.0. CD, CM and Ct are 1.0. No repetitive-member, flat-use,
short-duration or bearing-area increase is taken.

NDS 3.3.3 beam stability uses the full unsupported length and the table's
unspecified-loading effective length. NDS 3.7 column stability uses pinned-end
full-length effective lengths about both axes. These are stated sensitivities,
not proof of restraint. The program evaluates the NDS 3.9-3 biaxial compression
interaction and 3.9-4 stability condition, plus a conservative tension and
bending check with no tension relief. Section orientation comes from the
native `section_u`/`section_v`: the header's wide horizontal dimension is
explicitly swapped, so its vertical bending is not accidentally checked with
the strong section modulus. Rectangular transverse shear uses a conservative
resultant of the two component peak stresses. Torsion demands are reported;
no torsional resistance or local splitting approval is invented.

## Openings and boring tolerance

The evidence includes both gross checks and a deliberately conservative
net-section sensitivity: every cut in a member having a transverse LED bore
is checked with its worst centered bore section. A transverse cylindrical
hole removes a **rectangle**, not a circle, from its central grain-normal cut.
The net area is `b(d−D)`, strong modulus `b(d³−D³)/(6d)` and weak modulus
`(d−D)b²/6`. These net stresses and gross stability equations are a sensitivity;
they do not establish local stress concentration, splitting, shear flow around
the opening or modified buckling stiffness. At a bored section the shear check
is only the necessary average net-area check. The unbored parabolic shear
formula is not applied through a void. Additional local fastener-hole
interaction with LED holes is not qualified by these equations. The initial
net-section sensitivity reaches a necessary stress interaction of 0.565 and
a necessary average shear ratio of 0.343, both at the left center principal.
The actual bore list contains neither the top rail nor outer rims; the
governing top-rail failure is therefore an unperforated-member failure.

The dimensional rule preserving two 50.8 mm ligaments is:

`actual finished bore diameter <= measured stock depth −101.6 mm −2×maximum centering error`.

For nominal 139.7 mm stock and ±0.5 mm centering, actual bore diameter must be
at most **37.1 mm**. A nominal 38.1 mm bore has zero centering/diameter/depth
margin. The rule uses actual finished diameter, not the label on a drill bit,
and must also retain the harness feeding clearance. It resolves a dimensional
acceptance condition only. Neither this rule nor net section alone qualifies
holes in a loaded principal or beam.

## Bolts, bearing and local group stresses

Actual raw-stock ray intersections establish end and edge distances, including
the shoe's 9.525 mm rim trim. The report asserts the resulting rim minimum Z
of 234.525 mm. The current two four-bolt leg groups and shoe groups satisfy
the conservative 7D softwood loaded-end and 4D loaded-edge distances at each
bolt. The narrowest shoe rim edge is 39.7 mm versus 38.1 mm required; nominal
margin is only 1.6 mm. Row spacing and the separate maximum cross-grain spread
rule must also be preserved when laying out holes.

Single-shear TR12 yield equations use 0.298-inch root diameter throughout,
1.5-inch timber thickness, and no gap. NDS Table 12B supplies A36 steel dowel
bearing Fe 87,000 psi. Timber bearing uses 5,600 psi parallel and 3,650 psi
perpendicular with same-case directional Hankinson interpolation for each leg
member. Shoe timber uses the lower 3,650 psi at all angles. The reduction
terms bound Ktheta at 1.25; the opposite square plate is not credited as an
extra lateral shear plane. End-use factors are explicitly unity, subject to
the passing minimum end/edge geometry and dry-service assumptions.

Group action follows NDS 11.3-1 including the corrected `D^1.5` exponent.
A deliberately penalized four-fastener-row calculation with the largest
relevant pitch is used for these two-by-two groups; it is a conservative
screen rather than an equal-sharing assertion. Each native bolt vector is
compared separately. NDS Appendix E parallel-grain net tension, row tear-out
and group tear-out capacities are also calculated. The sum of absolute
parallel forces across all four bolts is conservatively compared even with
one two-bolt row capacity. This cannot validate perpendicular-grain splitting.

For bolt-axis force, NDS 12.3.9.1 requires adequate bearing area. Shoe plate
wood bearing uses `32²−π(11.1125)²/4` mm². Existing leg washers use the
**CDE minimum OD 0.805 inch**, subtracting the larger of maximum washer ID
0.419 inch and actual timber bore 11.1125 mm. Neither a 25.4 mm washer nor
maximum washer OD is used. One wood-contact footprint is counted on each
side. These ratios use incremental axial force, not tightening preload.
Washer/plate flexure and preload contact belong to the corresponding steel
and installation checks; a favorable average wood bearing ratio does not
establish them.

## Reproduction and sources

Run `python -m fea.reinforced_timber_resistance --native PATH/report.json
--output NEW.json` in the project environment. Output paths must not exist.
The report rejects a native/current CAD source mismatch, then hashes the calculator, TR12 implementation and current model source
closure before and after calculation, plus each input report. Primary PDF
SHA-256 values are embedded. Seven focused arithmetic/schema tests cover the
stability equation, deliberate failures, net section, boring tolerance,
group formula, header-axis swap and minimum washer footprint.

Primary publications used:

- [AWC Technical Report 12](https://web-media.awc.org/wp-content/uploads/2021/12/17210714/AWC-TR12-1510.pdf), Table 1-1 single-shear equations.

- [AWC NDS 2024 Chapter 3](https://web-media.awc.org/wp-content/uploads/2021/12/17210019/AWC_NDS2024_withCommentary_20240718_AWCWebsite_Chapter-3-Design-Provisions-and-Equations.pdf), sections 3.3, 3.7, 3.9 and 3.10.
- [AWC NDS 2024 Supplement Chapter 4](https://awc.org/wp-content/uploads/2026/08/AWC_NDS2024-Supplement_20240719_Chapter-4-Reference-Design-Values_Website-1.pdf), printed pages 32 and 34.
- [AWC NDS 2024 Chapter 12](https://awc.org/wp-content/uploads/2026/08/AWC_NDS2024_withCommentary_20250328_WebsiteChapter-12-%E2%80%93-Dowel-type-fasteners.pdf), tables 12.3.3, 12.5.1A–D and 12B; sections 12.3.9 and 12.5.1.3.
- [AWC NDS 2024 Appendices](https://web-media.awc.org/wp-content/uploads/2021/12/17210019/AWC_NDS2024_withCommentary_20240719_AWCWebsite_Appendix.pdf), nonmandatory Appendix E and Table I1.
- [AWC March 2025 errata](https://web-media.awc.org/wp-content/uploads/2025/03/31134949/2024-NDS-Errata-and-Addenda-03.28.25.pdf), corrected group-action equation.
- [CDE SAE washer dimensional sheet](https://cdefasteners.com/sites/default/files/product-specs/washerssae.pdf), 3/8-inch row.
