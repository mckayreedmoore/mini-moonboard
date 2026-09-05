# Load and material basis for the next joint/contact study

Research checked 2026-09-05. Applies to **2x8-foot100**, not the historical
all-plywood V1 purchase schedule. One climber, 250 lb intended maximum;
150/200 lb comparisons and 300 lb sensitivity are retained. No anchors,
unspecified ballast or pad support. This is a numerical development basis,
**not a safe user rating or construction release**.

## Sourced requirements versus exploratory loads

The public [CWA design specification](https://www.cwapro.org/file/secure/cwadesignpecfinal2022.pdf)
identifies itself as the January 2009 first edition, despite its 2022 filename.
Table 1 specifies 1.2 kN for an unroped climber; the larger protection-anchor
loads and section 5.3.1 direction rule are not bouldering-surface prescriptions.
Sections 4.5–4.7 require a 1.5 overturning factor and assess worst locations
using utilization-capacity climber loading or an alternative 718 N/m² load.
Dead load supplies restoring weight; opposing live loads cannot be ballast.
Its stationary/temporary scope does not specifically cover portable structures.
Utilization rules, material design, load combinations and local applicability
still require qualified interpretation; our one-person operating intent alone
does not establish compliance. Keep the detailed clause map in
[hybrid-load-basis.md](hybrid-load-basis.md).

[BSI currently lists BS EN 12572-2:2017 as current and under review](https://knowledge.bsigroup.com/products/artificial-climbing-structures-safety-requirements-and-test-methods-for-bouldering-walls).
It covers bouldering-wall calculations and testing, including panel/insert
behavior. Its public overview does not expose the complete normative load and
test procedures. [DIN's 2025 revision is explicitly a draft](https://www.dinmedia.de/de/norm-entwurf/din-en-12572-2/392573759),
not a silently adopted replacement. Obtain the applicable complete standard
before claiming conformity; do not invent missing EN forces or factors.

[Moon's DIY guide](https://moonclimbing.com/media/moonboard-pdf/How-to-build-a-MoonBoard_v2.1.pdf)
warns that frame structural requirements can differ by installation. Its panel
geometry and another frame's appearance do not rate this custom timber design.

## Loads to retain in the next numerical comparison

| Group | Explicit input | Interpretation |
| --- | --- | --- |
| Historical comparison | Six published 1.2/2.4 kN and horizontal/normal cases, unchanged | Preserve both legacy normal-load uplift failures; not all are established governing use cases. |
| Climber static weights | 150: 667.23 N; 200: 889.64 N; 250: 1112.06 N; 300: 1334.47 N downward | Mass-times-gravity comparisons, not new design-load limits. Do not reduce the sourced 1.2 kN comparison because a lighter person is expected. |
| Illustrative movement sensitivity | Twice each static weight, combined with 0 or 300 N horizontal load | Neither 2× nor 300 N is a measured dynamic envelope or normative amplification. 300 lb remains a sensitivity, not an increased rating. |
| Load position | Actual main/kicker holds, governing edge/corner positions, 0/50/100 mm outward hold projection | Projection guesses are not measured bounds for the owned 2025 holds. Include top/side-edge use if permitted; existing hold-only sweeps do not cover it. |
| Dead load | Actual candidate inventory and component centroids; retain 80% uniform-mass sensitivity separately | Assumed densities and frozen-CG scaling are not measured mass bounds. Include gravity before adding climbing loads in contact analyses. |

Apply each full climber resultant independently, not once per hold. For local
panel/joint work use a physical hold/insert load patch and trace its load path.
The historical equal five-node load split is useful for comparison but does
not test a single loaded corner or reproduce hand/foot force sharing.
Representative simultaneous hand/foot loads need a consistent resultant and
couple derived from the assumed climber equilibrium/motion; do not invent
opposing forces merely to achieve a desired frame response.

The next asymmetric comparison should apply the **same 1.2 kN downward total**
to one A12 hold/insert patch, then mirror it at K12, rather than distributing
240 N each to A12/C12/F12/H12/K12 as in the bulk reference. This selects outer
top-row locations to expose lateral load-path/torsional differences; it is a
project comparison, not a claim that either is the unique governing hold or a
new prescribed force. Check other holds before claiming an envelope. Add the
separately labelled horizontal/offset sensitivities only with an explicit
patch resultant and applied moment consistent with the hold projection.

For any reduced contact model, publish which loads and degrees of freedom it
actually represents. Sagittal contact cannot establish lateral/yaw stability.
Use compression-only floor support, explicitly labelled friction bounds and
joint stiffness/clearance bounds where measured values are unavailable.
An assumed friction coefficient is not a floor certification. A global force
ratio cannot determine individual foot sliding or bolt demand; see
[footprint-connection-gates.md](footprint-connection-gates.md).

Two initial studies can answer narrower questions without pretending to close
the material gates:

- A pin/bore contact coupon can test contact engagement, clearance and local
  reaction behavior. Even with all four pins, it is not the complete leg/rim
  joint, its actual load
  demand, or a prediction of timber splitting/capacity.
- A coarse 60 mm bonded-whole-frame run with unilateral floor contact and
  **timber-only gravity** can examine lift-off within its stated restraint and
  friction assumptions. It still bypasses real joint compliance. Its dead mass
  differs from the drilled-timber-plus-steel-angle footprint screen and must be
  reported separately, not substituted without explanation.

These are proposed/limited studies here, not completed or accepted results.
Numerical contact-law and equilibrium checks plus mesh/penalty sensitivity are
needed before interpreting their outputs.

## Material and connection evidence still missing

Use the [foot100 connection schedule](../exports/footprint-frame/2x8-foot100_connections.csv)
as **nominal geometry only**. Old V1 Grade-5 bolt lengths and all-plywood material
descriptions do not specify this hybrid. A307 was previously a candidate family,
not a selected substitute or approved resistance.

| Current evidence | Missing before a resistance/capacity conclusion |
| --- | --- |
| Swaner C-3 birch listing recorded in the [site survey](site-survey.md); leg thickness modelled as two 19.05 mm layers | Actual structural panel designation/certification, veneer layup/strength axes, thickness/defects and applicable directional design properties. Appearance grade and assumed E=7000 MPa are insufficient. |
| 2×8 rims and 2×4/2×6 backing dimensions in candidate CAD | Species, grade stamp, moisture/service condition and applicable lumber properties; do not transfer equal-modulus FEA assumptions into allowable strengths. |
| Two glued plywood layers per leg, nominal 38.1 mm total | Structural adhesive system approved for the application/substrate, bondline design, surface preparation, spread, pressure, cure and inspection; composite action remains unverified. |
| Four through-bolts per leg and custom angle envelopes | Actual bolt/nut/washer or bearing-plate product specifications, thread extent, tolerances, timber edge/end distances, group action, bearing/splitting/net-section checks and angle fabrication/rating. |
| Generic backing screws, including end-grain interfaces | Applicable tested screw provisions or redesigned side-grain/bearing detail; installation and strength/stiffness evidence. Nominal length and collision clearance do not establish withdrawal resistance. |
| Escape 3/8-16 T-nut and LED sample dimensions recorded | Hold-specific bolt engagement and force-transfer details, panel insert/pull-through resistance, installed hold offset and mass. These hold bolts are separate from structural frame bolts. |
| Flat CAD foot faces | Actual floor/interface condition, levelness, bearing capacity, individual friction/contact behavior and assembly stability. No room dimensions or pad support are needed for this numerical milestone. |

APA's [plywood specification guidance](https://www.apawood.org/engineered-wood-products/plywood-osb/plywood/)
explains structural ratings and directional properties; identify the actual
panel before assigning them. Adhesive water resistance is not structural
qualification: [Titebond III's manufacturer excludes structural/load-bearing use](https://www.titebond.com/print/product/e8d40b45-0ab3-49f7-8a9c-b53970f736af).
No adhesive is selected here. A wood fastener group also needs more than a
single-fastener calculation; [AWC's connection example](https://web-media.awc.org/wp-content/uploads/2021/12/17210649/StructureMag-NDS2015-PracticalSolutions-1611.pdf)
illustrates separate net-section and row/group tear-out checks, not a plywood
leg rating.

**Next decision gate:** publish bounded contact/joint behavior with explicit
unresolved inputs, then obtain the material/product evidence and qualified
load-basis review needed for a demand-versus-resistance assessment. Successful
solver convergence alone cannot close those gates or authorize physical use.
