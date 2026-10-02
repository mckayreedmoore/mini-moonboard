# Purchased plywood and saved response assumptions

The October 2 read-only material check found no demonstrated numerical
contradiction between the purchased product family and the saved conditional
AC-plywood references. It does identify which assumptions affect screw
sharing. Keep the current flexible operator while resolving those assumptions;
the rigid-panel diagnostic is not a replacement response.

## Product identity and reference scope

The [purchase record](../../../../purchased-materials.md) identifies Roseburg
AC fir, Lowe's item 12235 / model 119055, 23/32 CAT, PS1-09 Exterior.
Procurement identity is known. Actual sheet group, placement and elastic
properties are not bound to the model. The saved
`product_or_layup_identified: false` field therefore needs that distinction;
this note does not rewrite the frozen model or claim that the purchase is unknown.

Roseburg lists AC 23/32 panels with five or seven plies and western-wood
core/back veneers. That family information does not establish model 119055's
veneer group or measured constants. Marine-product species claims do not
transfer to this AC purchase. [Roseburg sanded-plywood brochure, AC page](https://www.roseburg.com/wp-content/uploads/2026/03/SandedPlywood_Brochure.pdf).

APA D510C (2012), covering PS1-09, supplies directional family minima rather
than one measured layup. Exact ply count is not necessary to use the
applicable family references. Group 2/3/4 EA and EI multipliers are
0.83/0.67/0.56; stiffness wet-service multiplier is 0.85. These are conditional
reference scenarios, not bounds on redistributed screw forces.
[APA D510C, sections 4.2/4.5 and Tables 9/10](https://design.medeek.com/resources/structural/D510C_2012.pdf).
APA's [current specification catalog](https://www.apawood.org/guides-tools-training/technical-document-library/technical-guides/panel-design-specification/)
identifies D510F (2020); the frozen helpers use the stated 2012 references.

## What the saved operator actually uses

### Owner-reported cuts and directional behavior

On October 2, the owner reported cutting a sheet down the middle into two
roughly 4×4 pieces. This establishes the reported cut, not the measured
dimensions, kerf or installed strength-axis direction of each piece.
Cutting does not change the veneers' directions; either square half can
subsequently be rotated in its plane.

Cross-lamination gives plywood strength and stiffness in both directions,
but does not make those properties equal. APA explicitly distinguishes
properties by stress direction relative to the strength axis.
[APA plywood properties and selection guidance](https://www.apawood.org/engineered-wood-products/plywood-osb/plywood/).
The table below has an along/across bending-stiffness ratio of about 3.54;
that is the declared family-reference scenario, not a measurement of the
owner's purchased panels. Both main-panel orientations now have complete
twelve-state analytical comparisons. The reported cut alone does not
establish a deficient blank or require re-cutting.

The current `operators-attempt02/model.json` retains Group 1 and thickness
18.25625 mm. Its targets are:

| Section stiffness | Across assumed face grain | Along assumed face grain |
| --- | ---: | ---: |
| EA, N/mm | 45,970.794252 | 74,428.904980 |
| EI, N mm | 852,093.918917 | 3,012,928.774070 |
| Membrane shear GA, N/mm | 8,843.905180 | 8,843.905180 |

The frozen native deck uses four equal 4.5640625 mm solid layers, splitting
the fitted half-thickness core into two quarters. Outer/core directional
moduli are 1401.281549/3634.888996 MPa across grain and
6563.750009/1590.049921 MPa along grain. These reproduce the independent
membrane and bending targets. The declared homogeneous `PANEL` card is not
the material assignment used by the panel elements.

Through-thickness E3=551.580583 MPa, G13=G23=77.221282 MPa and zero Poisson
couplings are explicit proxies. They are not measured Roseburg values.
Main-panel width is global X; assumed face grain follows the slope,
`[0, -0.642787609686799, -0.766044443118760]`. Kicker face grain is assumed
vertical. STEP alignment verifies geometric axes, not the purchased sheet's grain.

The [count comparison](../panel-attachment/README.md#owner-requested-12-versus-20-screw-and-model-check)
keeps a useful fixed-receiver diagnostic: upper-left rear peak 396.794 N with
rigid plywood versus 2130.507 N with its elastic operator at twelve screws.
The full current frame gives 1871.251 N. These are different models: the
diagnostic omits frame response, seams and in-plane reactions. It demonstrates
sensitivity to local bending and compliance, not an accepted lower demand.

## Finite next decision

The [three-sheet 4×8 envelope scenario](../assembly-package/README.md#stock-panel-quantities-and-cost-scope)
places two main-panel widths along the factory 2438.4 mm dimension:
`2 × 1217.6125 + 3.175 = 2438.4`. Each panel's 1219.2 mm slope dimension
then follows the factory short direction. If factory face grain follows the
long dimension, that placement makes X the strong direction, perpendicular
to the saved strong-slope assumption. Rotating those same blanks loses the
required slope dimension; this is not merely a label swap.

No physical sheet-to-body mapping or released wood-joint cutting plan was
found. The assembly table is explicitly grain-blind geometry arithmetic.
Thus this is a conditional scenario/model-axis incompatibility, not evidence
of how the owner's sheets were actually placed. A 4×4 count likewise does
not establish grain. The selected baseline's kerf-right sheets are a
different candidate's instructions.

Bind the sheet's strength-axis placement to the conditional cutting layout.
Where the sheet group or orientation remains unknown, label the chosen APA
reference/orientation scenario explicitly. Keep the transverse proxies
separate. A lower reference stiffness is not automatically conservative for
each screw's force, and equal screw count does not establish equal sharing.
This check changes no hardware, geometry, load, operator or release flag.

The subsequent [orientation response](panel-orientation-comparison.md) completes
all twelve states after replacing only the four main panels' directional
elastic contributions. The upper-left nominal head demand falls from 1871.251
to 1280.799 N; lower-left demand increases. Thus orientation matters, but this
comparison does not close the declared head references or adopt sheet placement.
The [grain-aware rectangular options](../assembly-package/panel-placement.md)
bind the three-/four-/five-sheet arithmetic to explicit material axes.

## Frozen source identities

| Source | SHA-256 |
| --- | --- |
| `operators-attempt02/model.json` | `b5f9b87b70c4a9920372a3443a55e37dfe34351fb9ac8210b299c1360fb93626` |
| `fea/current_response_materials.py` | `72af0456272d91282928014d8fde557d347e36df6b7bdf23bcc41ef923d0d135` |
| `fea/wood_joint_reduced_materials.py` | `0ac465879e48f6ab93e200cce5edfbb7e0f00703b8726b4f04964dbab5b0cba2` |
| `docs/purchased-materials.md` | `3a1e09c02e223cdec91ad96e258046e73322a23c6417252453f818624c3b8bad` |
| `../../mvp-acceleration-2026-09-28/current-frame-pure-solid-matrix-export-native-attempt01/model.inp` | `71dc0b73450b597aba35c0458befff5ca3b85dd87f3cfbed9992f4755b5124d5` |
| `../panel-attachment/count-comparison.json` | `bf002f4a1ef3a5473c87ccbd23b54d064ed125a01a9832fb61dc3979ffdf2249` |

The support worker traced the saved native material assignment and primary
sources read-only; parent checked the published tables and frozen pins.
No software tests, frame/native solve or review loop was performed for this note.
