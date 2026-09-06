# Material selection for the next frame comparison

Primary references checked 2026-09-06. Recommendation: **keep 2x8-foot100 as the
provisional geometry baseline, specify traceable structural stock, and resolve
the leg construction before buying deeper rims.** This is a procurement and
analysis plan, not an allowable climber weight or a construction release. It
extends [the existing load/material basis](load-contact-basis.md); original CAD,
purchase references and numerical results remain unchanged.

## Preferred procurement paths

| Component | Preferred specification path | Evidence needed before relying on it |
| --- | --- | --- |
| 2×8 rims and dimensional backing | Quote identified, grade-stamped structural lumber of one documented species combination and grade. No. 2 or better Douglas Fir–Larch is a candidate specification to price and evaluate, not a demonstrated required or sufficient grade. Retain actual dimensions and stamps. | Applicable species/grade/size design values, moisture/service assumptions, defects near connections, member orientation and applicable adjustments. A different species or grade requires reassessment. |
| Climbing surface and cut plywood components | Quote structural plywood carrying a recognized product standard and third-party mark, with documented thickness, strength axes and directional design data. Select a face finish compatible with holds and the qualified lamination process. | Panel identity/layup; concentrated hold/insert and fastener behavior; actual support spacing and edge support. A roof/floor span rating alone does not rate a climbing panel or a narrow profiled leg. |
| Two-layer plywood legs, if retained | Have the selected structural panels laminated under a specified, qualified structural bonding process, preferably by a fabricator able to document that process and inspect the bond. | Product-specific adhesive approval, process controls and design of the complete profiled, drilled leg. Panel certification does not certify the later face-to-face glue joint. |
| Separate no-adhesive-credit leg path | Evaluate two mechanically connected 19.05 mm structural plywood plies, nominally 38.10 mm total, as separate load-carrying members. Glue, if used, is assembly-only and receives no design credit. | Demonstrated load introduction/sharing, individual-ply stability, and designed mechanical connections. See the conditional route below; this does not validate an arbitrary bolt or stitch pattern. |
| Alternative when qualified leg lamination is impractical | Evaluate a leg redesign using traceable structural composite lumber such as LVL/PSL, or an appropriately specified factory-made glulam member. Prefer a geometry compatible with published product rules. | Member orientation, dimensions, design values and permission for every profile cut/hole/notch; connection and floor details must be redesigned and checked. This is a separate candidate, not a drop-in material substitution. |

AWC identifies species combinations from grade stamps and publishes separate
design-value tables in the [2024 NDS Supplement](https://awc.org/resources/2024-nds-supplement/).
Its [published supplement corrections](https://awc.org/wp-content/uploads/2024/02/2024NDS-Supplement-Updates-Errata_20240212.pdf)
also state the dry-service/normal-duration basis and refer to the applicable
adjustment factors. The grade/species recommendation above is a project choice;
no numerical allowable has been assigned to unidentified stock.

For panels, APA distinguishes grade, thickness, strength direction and bond
classification. Exposure 1 addresses limited moisture exposure; Exterior covers
longer weather exposure. Neither classification is a strength upgrade or decay
treatment. Require the actual mark and relevant directional capacities rather
than a generic “exterior” sales description. [APA plywood guidance](https://www.apawood.org/engineered-wood-products/plywood-osb/plywood/).
Structural I is an available structural panel category with enhanced cross-panel
and racking properties; it is not automatically necessary or sufficient for this
leg. [APA Rated Sheathing data sheet](https://www.apawood.org/Data/Sites/1/documents/product-support/rated-sheathing-datasheet.pdf).

## What the C-3 birch reference establishes

The [site survey](site-survey.md) records Swaner C-3 birch, Home Depot 165921,
with received-sheet dimensions still unresolved. Keep this stock reference,
but do not assign structural design values from the words “birch” or “C-3.”
Hardwood face/back grading addresses veneer characteristics and appearance;
another manufacturer's grading guide is not a set of design values for this
particular Swaner panel. [Columbia's hardwood plywood grading guide](https://cdn.columbiaforestproducts.com/GRADING%20GUIDE%20AS%20PDF%20%281%29.pdf).

Swaner says it supplies both custom domestic and stocked domestic/imported
plywood. Its general page does not identify the layup, structural certification
or directional allowables of the recorded retail SKU. Do not infer that this SKU
has the glue, core or properties of another panel on that page.
[Swaner manufacturer information](https://www.swanerhardwood.com/products/hardwood-plywood/).
Obtain the actual sheet/lot identification and written product data. If suitable
structural evidence is unavailable, reserve it for nonstructural uses or a
separately qualified application; buying thicker unknown-grade panels does not
close the evidence gap.

## Material models and lamination

The current E=7,000 MPa, ν=0.3, density=600 kg/m³ model is an equal-property
geometry comparison. Wood has different longitudinal, radial and tangential
stiffnesses; USDA describes nine independent elastic constants. Its clear-wood
tables describe species-average test specimens, not allowable strengths of
graded, drilled lumber or commercial plywood. Do not replace the current scalar
E with a clear-birch strength table and call the model validated.
[USDA Wood Handbook, chapter 5, pp. 5–1–5–3](https://www.fpl.fs.usda.gov/documnts/fplgtr/fplgtr282/chapter_05_fpl_gtr282.pdf).

For the next material-aware model, identify each lumber grain direction and
each panel strength axis. Obtain compatible directional elastic/shear properties
and applicable resistance values separately. Plywood bending, in-plane loading,
through-thickness shear and drilled connection behavior are different checks.
Use a justified product/laminate representation rather than inventing a full
three-dimensional orthotropic tensor from one published bending modulus.

The manufactured bonds inside a plywood sheet and the workshop bond joining
two sheets are separate interfaces. USDA explains that bond performance depends
on substrate, adhesive and interfacial condition, and covers moisture, surface
preparation, spreading, pressing, cure and quality assurance.
[USDA Wood Handbook, chapter 10](https://www.fpl.fs.usda.gov/documnts/fplgtr/fplgtr282/chapter_10_fpl_gtr282.pdf).
The project therefore needs an actual process specification: adhesive system
and substrate approval, service environment, preparation, spread, assembly time,
uniform pressure, cure, inspection and acceptance criteria. “Waterproof” and
successful small offcut bonding do not establish structural composite action.
In particular, [Titebond III's manufacturer expressly excludes structural/load-bearing applications](https://www.titebond.com/print/product/e8d40b45-0ab3-49f7-8a9c-b53970f736af).
No replacement glue brand is selected without its application-specific evidence.

Factory glulam provides a route with documented manufacturing, adhesive and
inspection requirements under ANSI A190.1; it does not turn arbitrary shop-glued
plywood into certified glulam. [APA's A190.1 scope](https://www.apawood.org/what-we-do/standards-development/ansi-a1901-standard-for-structural-glued-laminated-timber/).
Likewise, an engineered beam's published properties do not authorize cutting
the present bent leg outline from it. Weyerhaeuser requires evaluation when
openings exceed its published limitations. [Manufacturer hole guidance](https://www.techsupport.weyerhaeuser.com/hc/en-us/articles/201758910-Where-Can-I-Drill-a-Hole-in-a-Beam).

## Conditional route: two mechanically connected 3/4-inch leg plies

**Qualified structural face-to-face bonding is not the only possible route.**
The requested two 19.05 mm plies can instead be evaluated with zero adhesive
strength, stiffness, or composite-action credit. This is a separate design
candidate, not permission to reuse the perfectly bonded solid model. Confirm
actual panel thickness: a nominal/performance-category description does not
guarantee exactly 19.05 mm. The structural-panel evidence requirements above
still apply; this route does not establish C-3 stock strength.

The following section-property comparison is an analytical derivation, not a
published plywood allowable. For identical, aligned rectangular sections of
in-plane depth `h` and single-ply thickness `t`:

| Bending direction | Independent plies, summed about their own axes | Fully composite homogeneous stack |
| --- | --- | --- |
| In the panel plane | `2(t h³/12)` | `(2t) h³/12`: equal |
| Out of the panel plane | `2(h t³/12)` | `h(2t)³/12`: four times the independent sum |

Thus two plies **can** retain the same in-plane bending stiffness as the bonded
stack when their material/orientation, loading and supports produce the required
sharing. The identity follows because thickness is linear in that bending
inertia; no separation-of-centroids contribution is needed. It does not force
each real ply to receive half the demand. Different bolt engagement, one-sided
loading, unequal floor seating or panel properties can invalidate that split.

The one-quarter out-of-plane ratio is exact for these geometric inertias and
for a homogeneous equal-E illustration, not necessarily for real plywood EI.
Veneer layup affects each panel's bending rigidity and the bonded stack's
parallel-axis contribution differently. Use product/laminate properties;
do not divide every strength, torsional rigidity or buckling capacity by four.
APA explicitly distinguishes directional panel bending, axial and shear
properties rather than assigning one universal modulus.
[APA panel property guidance](https://www.apawood.org/engineered-wood-products/plywood-osb/plywood/).

### Load path and checks required before selecting this route

- Resolve how each rim/leg bolt or bracket introduces load into each ply, including
  eccentricity and fit. A through-bolt spanning both sheets does not itself prove
  equal bearing forces. Design any transfer from the initially loaded ply into
  its neighbor; check plausible unequal-sharing cases rather than imposing 50/50.
- Specify the actual mechanical stitch system only after calculating its demands:
  fastener bending and shear planes, panel bearing, slip, group action, net sections,
  edge/end distances, tear-out, washer/head bearing and pull-through. Reversing
  lateral loads and opening/prying need explicit treatment. Do not credit clamping
  friction from an unspecified tightening torque.
- Check each ply's out-of-plane buckling between **verified** restraints, global
  sway and lateral-torsional behavior, combined axial/biaxial bending, and the
  restraint stiffness/strength supplied by stitches. A neighboring flexible ply
  is not automatically a fixed lateral brace. Include twist, inter-ply separation,
  and local floor/contact load imbalance.
- Internal veneer bonds still carry stresses: no external adhesive credit does
  not eliminate panel delamination, rolling shear, or local drilling damage.
  Assembly glue must not be needed to retain the intended load path after its
  stiffness is removed. Validate both members and connections under that assumption.

USDA explains that bolt-hole condition affects bearing and deformation and that
multi-fastener forces depend on member stiffness, connection slip, spacing and
fabrication variation; total force is not generally shared equally among bolts.
Its fastening chapter points to APA for plywood-specific fastener information.
These observations motivate the checks above; the handbook's lumber examples
are not a stitch schedule for these profiled legs.
[USDA 2021 Wood Handbook, chapter 8, pp. 8–6, 8–16, 8–24](https://www.fpl.fs.usda.gov/documnts/fplgtr/fplgtr282/chapter_08_fpl_gtr282.pdf).

AWC's **2018** explanatory manual, M3.6 and M15.2–15.3, distinguishes built-up
and spaced columns and explains why interlamination slip affects stability.
Its spaced-column system includes specified blocking and end connectors; two
touching plywood sheets are not that system. This is useful mechanics guidance,
not evidence that a lumber-column factor or fastening pattern applies to a
drilled, profiled plywood leg under combined loads. A project design must verify
the scope of the governing standard/product data, not silently transplant a
prescriptive lumber detail.
[AWC 2018 Manual, pp. 7 and 90](https://web-media.awc.org/wp-content/uploads/2022/01/17210413/AWC-2018-Manual-1810.pdf).
Likewise APA's all-plywood beam supplement is expressly for **staple-glued**
beams; it is not a no-glue bolted-leg qualification.
[APA Supplement 5-23 scope](https://www.apawood.org/guides-tools-training/technical-document-library/technical-guides/plywood-design-specification-supplement-5-23-design-and-fabrication-of-all-plywood-beams/).

Next evidence: identified panels and axes, as-built bolt/bracket geometry,
fastener/washer specifications and hole tolerances, floor seating of both plies,
connection load-slip/resistance data, and a justified independent-ply stability
model. A structural reviewer can then select and verify a stitch detail; none is
specified here. This route may remove the need for a qualified workshop glue
process, but not the need for a verified leg assembly. It neither requires deeper
rims nor establishes that 2×8 rims suffice; retain the existing geometry baseline
until member-specific demand/resistance identifies what governs.

## Floor friction is a separate material input

USDA reports that wood friction depends on moisture, surface roughness and the
opposing material; static and kinetic friction are distinct. Its often-quoted
0.3–0.5 range concerns **kinetic friction of smooth, dry wood against hard,
smooth surfaces**. It is not a certified lower bound for the actual plywood
edge, finish, flooring or contamination. [Wood Handbook, chapter 4, pp. 4–19–4–20](https://www.fpl.fs.usda.gov/documnts/fplgtr/fplgtr282/chapter_04_fpl_gtr282.pdf).

Retain μ=.3 and .5 as numerical sensitivities, not procurement specifications.
The project needs the actual foot/floor materials and finishes, representative
normal load and contact orientation, levelness and repeated start/sliding
measurements under credible use conditions. Select any design lower bound with
the review/testing basis; a single pull test is not a lifetime guarantee.
An added friction pad would change the interface and its compliance, durability
and retention requirements; it is a new detail to characterize, not an assumed
source of support or ballast.

## Decision rule: retain 2×8 or evaluate deeper rims

The existing [fixed-floor comparison](physical-footprint-results.md) gives
sampled 1.2 kN downward displacements of 0.84622 mm for 2x8-foot100, 0.54483 mm
for the 2×10 candidate and 0.38900 mm for 2×12. These are whole-candidate,
isotropic, perfectly bonded results, not an isolated rim-depth experiment or a
material-capacity ranking. No allowable displacement was established.

Retain 2×8 as the baseline while addressing contact equilibrium, leg/joint load
paths and traceable materials. Evaluate deeper rims only if an accepted load
path plus product-specific member checks shows rim bending, shear, bearing,
stability or an agreed serviceability limit governs. If leg lamination, bolt-group
splitting, insert pull-through, floor sliding or opening governs, deeper rims
alone do not resolve that mechanism. A selected higher-grade lumber or engineered
leg must be rechecked with its real mass/centroid and connections; neither extra
weight nor extra stiffness is automatically favorable for every unanchored load.

The next procurement evidence packet should contain sheet and lumber marks,
lot/product data, actual thicknesses/dimensions and mass, grain/strength-axis
orientation, service moisture assumptions, lamination process, connection/insert
specifications and floor-interface characterization. Until demand and resistance
are compared for those actual inputs, **2×8 remains a development preference,
not a rated minimum, and no deeper size is selected as a substitute for missing
material or connection evidence**.
