# A66 component-rating route: partial evidence, no joint rating

Checked September 19, 2026 for the preserved single 1.5-inch Douglas Fir–Larch
No. 2 receivers and the retail Simpson A66 with two 3/8-inch through-bolts per
leg. This is an input and method screen, not a drilling or structural release.
No manufacturer was contacted.

## Published wood inputs

The [2024 NDS Chapter 12](https://awc.org/wp-content/uploads/2026/08/AWC_NDS2024_withCommentary_20250328_WebsiteChapter-12-%E2%80%93-Dowel-type-fasteners.pdf)
provides dowel-bearing values for solid wood, and the [AWC 2024
errata](https://web-media.awc.org/wp-content/uploads/2025/03/31134949/2024-NDS-Errata-and-Addenda-03.28.25.pdf)
assigns Douglas Fir–Larch specific gravity `G = 0.50`. For a nominal
`D = 0.375 in` bolt, the NDS/TR12 expressions give `Fe_parallel = 11,200G =
5,600 psi` and `Fe_perpendicular = 6,100G^1.45 / sqrt(D)`, approximately
`3,650 psi` after the NDS table's rounding. [AWC Technical Report 12, Table
A1](https://awc.org/wp-content/uploads/2021/12/AWC-TR12-1510.pdf) states the
formulas and explains the rounded reference values. Grain-angle interpolation
must use the actual load direction.

These are **bearing stresses**, not force ratings. Even multiplying by the
nominal projected bearing area `D × 1.5 in` gives only unadjusted bearing-mode
forces of about 3,150 lb parallel and 2,053 lb perpendicular. Those products
are **not allowable bolt loads**: the NDS yield-mode equations apply reduction
terms, and fastener bending, steel bearing, and other modes can govern. Full
1.5-inch bearing length and nominal diameter are also conditional on the
delivered bolt's shank/thread position. Do not use either product to pass a
joint or select a bolt count.

[AWC TR12 Table A2](https://awc.org/wp-content/uploads/2021/12/AWC-TR12-1510.pdf)
publishes a 45,000-psi reference bolt bending-yield strength for its stated
low-carbon bolt class. [ICC-ES ESR-3455, §3.29.3.2](https://icc-es.org/wp-content/uploads/report-directory/ESR-3455.pdf)
explicitly pairs ASTM A307 Grade A with minimum `Fyb = 45,000 psi` for the
bolts covered by *that* report. Neither source certifies an unpurchased retail
bolt or supplies A66 steel bearing strength. The input-driven
`steel_wood_single_shear_mode_iv_reference_lbf` helper implements the 2024 NDS
12.3-6 bending-dominated yield mode with separately supplied wood bearing,
steel bearing, and bolt `Fyb`. Its output is **one mode only**, so it cannot
replace the minimum of applicable modes or the formed-angle check.

The narrowly scoped `dfl_dowel_bearing_psi` helper in
`mini_moonboard/bolted_timber_checks.py` reproduces these rounded solid-wood
inputs and the angle-to-grain interpolation. Its tests cover the 0°, 45°, and
90° cases plus inapplicable inputs. It cannot be used for panel or end-grain
bearing, bolt capacity, or complete connection acceptance.

## What combining component data can and cannot do

A defensible **engineered design value** for one defined installation could be
developed from separate primary inputs. [AWC's connection
calculator](https://awc.org/resources/connection-calculator/) explicitly covers
wood-to-steel single- and double-shear bolt connections under the 2024 NDS.
For an A66 on one face of each timber, each leg-to-timber attachment is a
single-shear fastening condition. That calculation requires actual steel-side
bearing strength and thickness, bolt bending-yield strength and bearing
diameter, wood bearing length and grain angle, then the lowest applicable
yield mode and service/geometry/group adjustments. The calculator cannot rate
the complete formed-angle assembly from the wood inputs alone.

The separate limits do **not** add, and simply taking the minimum of unrelated
catalog ratings is not enough. First resolve the specified assembly loads into
each leg, bolt group, and bolt, including eccentricity and possible prying.
Then check the entire load path: wood dowel yield and member splitting/net
section; bolt shear, tension and interaction; hole bearing/tear-out and net
section in the steel; angle-leg and bend-region bending/deformation; washer
bearing and installation; and the supporting frame and anchors. Only
compatible design bases and the same load cases may be compared. The
[Simpson allowable-load notes](https://www.strongtie.com/products/connectors/wood-construction-connectors/technical-notes/allowable-loads)
explain that connector published values can be controlled by assembly testing
or deflection as well as fastener limits. A calculated component design value
would therefore be an independent design, **not** a reconstructed Simpson A66
product rating.

The [current Simpson US catalog, page 314](https://ssttoolbox.widen.net/content/orplhjaqw1/original/C-C-2026.pdf?download=true)
identifies two 3/8-inch through-bolts per A66 leg but publishes dashes for its
F1/F2 allowable loads. The available retail listing confirms 12-gauge G90
steel, not a verified A66-specific steel grade, minimum base-metal thickness,
hole layout, or formed-angle resistance. A published steel grade for a
**different** Simpson angle cannot be transferred to A66. The available
[Lowe's A66 listing](https://www.lowes.com/pd/Simpson-Strong-Tie-6-in-Angle/3036793)
and [Home Depot A66 listing](https://www.homedepot.com/p/100375146) are
procurement evidence only.

The retail [A307 bolt example](https://www.lowes.com/pd/Hillman-3-8-in-x-4-in-Galvanized-Coarse-Thread-Hex-Bolt/1000381863)
establishes availability, not a chosen length, certified bending-yield
property, thread-free shear plane, or installed bolt capacity. No assumption
of clamping friction or pretension is credited.

## Does the wood govern before the bolt?

For **pure lateral shear only**, a conditional component comparison supports
that hypothesis for the nominal 3/8-inch A307 example. With full 1.5-inch
wood bearing length, 2024 NDS Mode I_m gives `D × l × Fe / Rd` = **788 lb**
parallel to grain (`Rd = 4`) or **411 lb** perpendicular (`Rd = 5`). The
[AWC 2024 errata](https://web-media.awc.org/wp-content/uploads/2025/03/31134949/2024-NDS-Errata-and-Addenda-03.28.25.pdf)
reprints the applicable reduction table. These are *individual wood-bearing
yield-mode reference values*, not observed wood failure loads or the final
single-fastener value; other yield modes or adjustments may be lower.

For comparison, [AISC 360-16 Table J3.2 and §J3.6](https://www.aisc.org/globalassets/aisc/publications/standards/a360-16-spec-and-commentary_march-2021.pdf)
give A307 bolts nominal shear stress of 27 ksi and ASD factor `Omega = 2.00`.
At nominal 3/8-inch body area, that is about **2,982 lb nominal** and
**1,491 lb ASD** for one bolt shaft in one shear plane, before any grip-length
reduction or combined tension. [ASTM A307](https://store.astm.org/a0307-00.html)
separately specifies Grade A's minimum tensile strength of 60 ksi. The
[Lowe's candidate listing](https://www.lowes.com/pd/Hillman-3-8-in-x-4-in-Galvanized-Coarse-Thread-Hex-Bolt/1000381863)
calls its example A307, but no delivered bolt, grip or thread position is
selected or verified. The [owner-supplied AIMS grade
chart](https://aimsindustrial.com.au/blogs/product-guides/bolt-grade-chart)
explains common metric/SAE markings but does not list ASTM A307 or rate this
joint; its Australian metric torque table must not be used as an A66 wood
installation instruction. Its Grade 5 row is relevant to identifying the
twelve *retained existing* frame-bolt grade, not an automatic upgrade of the
new preliminary A307 A66 bolt option.

Thus wood bearing can be the lower **screened component** versus bolt-shaft
shear under those assumptions. It does not prove wood is the first physical
failure: the A66 sheet may bend or tear, the bolt may see prying/tension,
wood may split or tear out, and a 3/8-inch bolt on the narrow 1.5-inch face
already fails the conditional loaded-edge 4D geometry screen. Do not double
the single-bolt number for an A66 leg. The reproducible inputs and claim
boundary are in `a66-wood-vs-bolt-screen.json`.

The [2024 NDS Supplement Table 4A](https://awc.org/wp-content/uploads/2026/08/AWC_NDS2024-Supplement_20240719_Chapter-4-Reference-Design-Values_Website-1.pdf)
also gives DF-L No. 2 dimension-lumber references of **575 psi tension
parallel to grain**, **180 psi shear parallel to grain**, and **625 psi
compression perpendicular to grain**. Those enable other conditional wood
checks. For example, with *one* 7/16-inch bore across a 1.5 by 5.5-inch
section, unadjusted net parallel-tension force is `575 × 1.5 ×
(5.5 − 7/16) = 4,366 lb`. A fully supported 1-inch-OD washer around the
same bore has `625 × π/4 × (1² − 0.438²) = 397 lb` of idealized dry
wood contact bearing per plane before preload. Neither number is a joint
rating; the tension check is for member axial action, while washer bearing
concerns bolt-axis action and requires actual washer stiffness/contact. The
0.438-inch published standard cut-washer opening is slightly larger than
the 7/16-inch assumed wood bore, so it governs the idealized net annulus.

[AWC 2024 NDS Appendix E](https://web-media.awc.org/wp-content/uploads/2021/12/17210019/AWC_NDS2024_withCommentary_20240719_AWCWebsite_Appendix.pdf)
provides a nonmandatory parallel-grain row tear-out method. Its E.3-2b
equation gives `2 × 180 × 1.5 × 1.125 = 608 lb` for a *hypothetical*
two-bolt row at the 3D minimum pitch and adequate loaded-end distance.
This is a method demonstration, not the A66 factory pattern or a
multi-bolt acceptance value; full 2024 placement and adjustment checks are
required for an actual layout. The `bolted_timber_checks.py` helpers now
calculate E.2 net section, E.3 one-row, E.4 group, and idealized washer
bearing references from caller-supplied geometry. They do not identify the
critical A66 group, establish full washer contact, or report a connection
pass. The [US Forest
Service's fastener research](https://research.fs.usda.gov/treesearch/27033)
also cautions that bolt-group tear-out and splitting are distinct wood
mechanisms. Published `Ft`, `Fv`, `Fc⊥` and `Fe` therefore give substantial
wood-side data, but no single material number proves the complete joint.

## Remaining G1 decision

Obtain a dimensioned, product-specific factory hole pattern; supported A66
steel material/thickness and bend data; selected bolt properties and grip;
actual member/load geometry for every station; and a checked whole-joint
resistance model or an applicable product-specific manufacturer rating/test.
If those cannot be obtained without contacting anyone, keep A66 as a retail
prototype lead, not a selected structural architecture. No purchase, cut,
drill, or capacity claim follows from this component screen.
