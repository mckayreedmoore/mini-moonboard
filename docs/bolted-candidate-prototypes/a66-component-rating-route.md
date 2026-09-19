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

## Remaining G1 decision

Obtain a dimensioned, product-specific factory hole pattern; supported A66
steel material/thickness and bend data; selected bolt properties and grip;
actual member/load geometry for every station; and a checked whole-joint
resistance model or an applicable product-specific manufacturer rating/test.
If those cannot be obtained without contacting anyone, keep A66 as a retail
prototype lead, not a selected structural architecture. No purchase, cut,
drill, or capacity claim follows from this component screen.
