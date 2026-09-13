# Material and connection stiffness basis for the current response calculation

Published material values are available. This note separates those values from
the additional assumptions required to represent the assembled, shoe-free frame.
It is a source and modeling note, not a report that the following options have
all been implemented or validated. The accepted plywood and T-nut construction
remains the design basis; nothing here establishes a reason to replace it.

## Timber response properties

Retain dry, unincised US Douglas Fir–Larch No. 2. The longitudinal response
reference is the NDS mean bending modulus, 1,600,000 psi (11,032 MPa).
The 580,000 psi minimum modulus belongs in applicable stability calculations;
it should not replace the mean modulus throughout a deflection model.
[AWC 2024 NDS Supplement](https://awc.org/resources/2024-nds-supplement/), Table 4A.

For an orthotropic model, the USDA Forest Products Laboratory provides the
following Douglas-fir ratios at approximately 12% moisture content:

| Property | Ratio to longitudinal modulus |
| --- | ---: |
| Radial modulus, E_R | 0.068 |
| Tangential modulus, E_T | 0.050 |
| Longitudinal/radial shear modulus, G_LR | 0.064 |
| Longitudinal/tangential shear modulus, G_LT | 0.078 |
| Radial/tangential shear modulus, G_RT | 0.007 |

Use independent Poisson ratios nu_LR = 0.292, nu_LT = 0.449 and nu_RT = 0.390;
derive reverse ratios by reciprocity. These are species-average clear-wood
data, rather than guaranteed graded-lumber constants. Assign the grain axis
per member and state the assumed growth-ring orientation. FPL's approximate
10% adjustment from bending to axial modulus concerns its tabulated clear-wood
data; it is not automatically applied to the NDS grade value here.
[FPL Wood Handbook, Chapter 5](https://www.fpl.fs.usda.gov/documnts/fplgtr/fplgtr282/chapter_05_fpl_gtr282.pdf), Tables 5–1 and 5–2.

Using the NDS longitudinal reference with these ratios is an explicit engineering
approximation. Swapping the radial and tangential directions is a physically
interpretable sensitivity where the stock's growth-ring orientation is not
specified. It is preferable to assigning the same stiffness in every direction.

## Lateral fastener slip

Swedish Wood's Eurocode 5 guide gives the serviceability slip modulus
`K_ser = rho_m^1.5 * d / 23`, in N/mm, for bolts and screws in timber-to-timber
and wood-panel-to-timber joints. It applies per fastener and per shear plane;
`rho_m` is mean density in kg/m³ and `d` is outer diameter in mm. For differing
materials, use the geometric mean of their densities. Bolt-hole clearance is
additional displacement, not included in the spring slope.
[Swedish Wood, Design of Timber Structures, Volume 2](https://www.swedishwood.com/siteassets/5-publikationer/pdfer/sw-design-of-timber-structures-vol2-2022.pdf), section 9.2, Table 9.2, page 33.

The following are calculated examples, not measurements or product guarantees:

| Connection reference | Density assumptions | Lateral K_ser |
| --- | --- | ---: |
| 3/8-inch bolt, 9.525 mm | Both timber members 500 kg/m³ | 4,630 N/mm |
| #8 screw, 4.1656 mm | Timber 500 and plywood 550 kg/m³ | 2,175 N/mm |
| 1/4-inch screw, 6.35 mm, timber-to-timber reference only | Both members 500 kg/m³ | 3,087 N/mm |

The mean-density inputs above are declared response assumptions. The existing
600 kg/m³ dead-weight assumption and NDS specific gravity are not automatically
interchangeable with measured mean density in this formula. For example, using
450 and 600 kg/m³ in the equal-density bolt expression produces 3,953 and
6,086 N/mm respectively. Those endpoints illustrate density sensitivity; they
are not statistical bounds or permission to select whichever gives a pass.

These lateral springs can provide an interpretable starting point for explicit
fastener groups. Group rotational response should emerge from their actual
positions and member deformation. The formula does not assign whole-joint
rigidity, preload friction, gap closure, cyclic degradation or connection strength.
Using this European serviceability relationship does not transfer European
strength factors into the separate NDS resistance checks.

## Withdrawal and commercial brackets

The lateral slip expression is **not an axial withdrawal stiffness**. A screw's
published withdrawal capacity, expressed as force or force per penetration
length, is also not a stiffness in N/mm. An assumed allowable-load displacement
must not be invented to convert one into the other.

The SDS manufacturer's public design guidance supplies allowable loads and
installation requirements. It does not provide the complete axial load-slip
law for this particular assembled ML24Z joint. The timber-to-timber screw
reference above must not be described as an authenticated SDS-to-steel value.
[Simpson SDS design guidance](https://www.strongtie.com/products/fastening-systems/technical-notes/joining-composite-lumber-with-sds-wood-screws).

Resolve bracket deformation with its actual geometry and a stated steel elastic
model where practical. Keep wood bearing/contact distinct from screw withdrawal.
If an axial response assumption is necessary, label it explicitly and determine
whether the decision depends on it before using the resulting forces for sizing.
A different manufacturer's screw stiffness or a larger European screw assessment
cannot qualify the selected US SPAX or SDS product by analogy alone.

There is nevertheless a published axial reference suitable for a clearly
labeled engineering analogy. Simpson's European assessment ETA-13/0796
(16 February 2022), Annex A.7.1.6, gives `K_ser,ax = 25 d l_ef` N/mm for
the threaded portion in softwood, with dimensions in mm and a reference mean
density of 420 kg/m³. Its applicability is to screws covered by that assessment,
not automatically the selected US products. The reference permits installation
without predrilling or with a pilot no larger than 75% of the outer diameter.
[Simpson ETA-13/0796, page 36](https://www.strongtie.es/sites/default/files/field_media_file_2/2022/06/24/112106/eta-13-0796.pdf).

For illustration, the expression produces 3,124 N/mm at d = 4.1656 mm and
30 mm engaged thread, or 5,556 N/mm at d = 6.35 mm and 35 mm engaged thread.
Use actual effective engagement in any implementation. This is a better
documented starting assumption than assigning the same arbitrary spring in
every direction. It still requires separate allowance for head-seat deformation
and steel extension in series. An elastic steel `EA/L` calculation with rigid
seating is a stiff reference, not the complete installed axial stiffness.
Factors such as 0.5 and 2 around the analogy can test decision sensitivity,
but are not manufacturer bounds or confidence intervals. If those choices
reverse a design decision, the present response calculation has not closed it.

The implemented defaults refine those illustrations using the selected geometry:
SPAX outer diameter 4.1402 mm and 31.496 mm thread including tip, and SDS
6.35 mm diameter and 25.4 mm nominal thread. Deducting a stated 2D tip allowance
gives 23.2156 mm and 12.7 mm respectively; this is a conservative engagement
idealization, not a measured tip length. The screw dimensions come from
`docs/round-panel-countersink-reference.json` and
`mini_moonboard/selected_hardware.py`.

Axial compliance is combined in series. The panel screw includes threaded-wood
slip, root-diameter steel extension and a projected annular head-seat compression
column through the 18.25625 mm panel. The SDS includes threaded-wood slip and
shank-diameter steel extension, treating its steel head/angle seating as rigid.
The bolt includes steel extension and two wood compression columns, each
38.1 mm long, beneath the modeled washer annulus (21.0058 mm outside diameter,
10.1854 mm bore). The compression-column modulus is the FPL tangential proxy,
0.05 times the longitudinal timber reference, without pressure spreading.
These columns add physically interpretable seat compliance; they do not model
washer bending, countersink contact or establish measured joint stiffness.
Their effective length and pressure-spreading assumptions remain model-form
sensitivities. The plywood seat modulus is likewise an explicit proxy.

## Plywood response

APA publishes directional panel bending stiffness EI, axial stiffness EA and
shear properties by panel classification. Select the row applicable to the
owned Roseburg product; do not silently substitute Structural I. A catalog
listing or 23/32 performance category alone does not determine every panel
property. [APA Panel Design Specification, D510](https://www.apawood.org/guides-tools-training/technical-document-library/technical-guides/panel-design-specification/).

There is a modeling issue to handle separately from panel adequacy: plywood's
effective bending and membrane stiffnesses need not correspond to a single
homogeneous elastic modulus. For unit width, `E_bending = 12 EI / t^3` while
`E_membrane = EA / t`. A homogeneous solid fitted to one does not necessarily
match the other. Use a laminate or section formulation that retains both, or
document the approximation and compare it against the directional panel
references. This is a reason to improve the calculation, not to require thicker
plywood or new panel tests.

For a reproducible conditional reference, APA D510C (2012), Table 9,
provides these sanded Group 1 A-A/A-C 23/32-category values. These are not
separate five-ply and seven-ply product guarantees:

| Section property | Parallel to strength axis | Perpendicular to strength axis |
| --- | ---: | ---: |
| EI, lbf-in² per foot width | 320,000 | 90,500 |
| EA, lbf per foot width | 5,100,000 | 3,150,000 |
| G_v t_v, lbf per inch panel depth | 50,500 | 50,500 |

The last row is membrane shear rigidity: APA's phrase “through the thickness”
describes shear on an edge section. It is not the rolling-shear modulus needed
for out-of-plane panel shear deformation. Table 9's separate 350 lbf/ft
`F_s I b / Q` value is rolling-shear **strength**, not a stiffness. Table 10
multiplies EI, EA and G_v t_v by 0.56 for Group 4; its 0.68 factor applies
to membrane shear strength, not rigidity. [APA D510C, Tables 9–10, pages 23–26
(APA-authored historical PDF hosted by Medeek)](https://design.medeek.com/resources/structural/D510C_2012.pdf).

An effective symmetric layered shell may fit the directional EA and EI
independently without asserting that its mathematical layers reproduce the
actual veneer schedule. Its constitutive matrix must remain positive definite,
and a simple axial and bending coupon calculation must reproduce both target
section properties. State separately any assumed Poisson coupling and
out-of-plane shear modulus; the table above does not supply them.

## Acceptance of a response calculation

A source citation does not authenticate a finite-element result. Before sizing
connections from recovered forces, verify equilibrium, local material axes,
spring directions and units, support lift-off behavior, independent panel seams,
and convergence of the governing resultants. Report numerical and model-form
limitations separately from demonstrated resistance shortfalls. Increase stock
or change hardware only after a credible demand calculation identifies a
controlling deficiency.
