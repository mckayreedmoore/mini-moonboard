# Round-passage members and structural connections

The [assessment](../fea/results/round-member-connection-assessment-v1.json)
recovers member cut forces and structural-joint forces from the three authenticated
`round-bore-service-development` native runs. It identifies a specific unresolved
load direction at the outer base angles and quantifies the remaining bolt and
bored-member demands. It does not pass member or connection strength.

This evidence belongs to the 56 ordinary-panel-screw assembly. A later
insert/machine-screw candidate changes panel attachment behavior; its demands
cannot inherit this assessment without a matching mechanics analysis.

## Evidence and sign conventions

[The runner](../fea/round_member_connection_assessment.py) authenticates the
three-case summary, every native artifact, source snapshots and the reconstructed
input deck. Current geometry producers and references must match the frozen
inputs. Output-only export/drilling code may differ. The original sources,
native solutions and historical result files are preserved.

Each case supplies 24 angles with three SDS25112 screws in each flange, eight
leg bolts and 32 bore-center member cuts. All force vectors retain their actual
world coordinates. For a connector, the force on its second member is the
negative of the force on its first member. Wood attachment ownership comes from
the original interpolation equations, not part-name guesses or equal division
of the applied climbing load. Original member gravity loads are retained.

Both flange force and moment resultants are calculated about the same bend
origin. The largest recovered whole-angle imbalance is 0.0166 N and
0.708 N·mm, within the runner's 0.1 N / 2 N·mm rejection limits. These small
residuals are consistent with the native displacement output precision. An equilibrium
failure stops the assessment.

The spring forces are reconstructed from printed displacements, not independently
printed native element forces. Investigation of expanded S8 shell output found
panel-level residuals beyond ordinary rounding; its averaged surface-node output
may not recover every attachment displacement. Whole-angle and global equilibrium
do not bound that error. Timber-only bolt/bracket recoveries use solid attachment
nodes, but the member cuts also include panel forces. All cut values below remain
reported-force diagnostics pending independent force recovery; three decimal
places identify reproducible arithmetic, not physical or solver accuracy.

The load resisted by an angle is the negative of its force on the loaded wood.
This distinction controls the F3/F4 and uplift signs. The JSON records both
flange wrenches and the sign convention used for manufacturer comparisons.

## Outer rim/header ML24Z angles

The inspected [Simpson L-C-MLZ25 letter](https://ssttoolbox.widen.net/content/iczmiabsx6/pdf/L-C-MLZ25.pdf)
specifies six SDS25112 screws for one ML24Z. Its DF/SP bearing-installation
references are F1 = 595 lbf, F3 = 450 lbf and F4 = 750 lbf. **It lists no F2
uplift value for that installation.** The ML24Z entries have no load-duration
increase. The letter also requires consideration of reinforcement when
cross-grain bending or tension cannot be avoided.

The two outer angles use the previously inspected bearing-installation analogy:
F1 along the bend, F3 away from the angle face, F4 toward that face. This
geometric analogy is not manufacturer approval of the assembly. The native
frame produces the following applied vertical demands resisted by the angles:

| Native case | Left angle vertical demand (N) | Right angle vertical demand (N) |
| --- | ---: | ---: |
| F10 | +253.116 uplift | +257.560 uplift |
| C6 | −123.051 downward | +52.457 uplift |
| C10 | +151.873 uplift | +97.844 uplift |

Five of the six sampled outer-angle states therefore require an **unlisted
uplift direction**. This is a missing applicable resistance, not a demonstrated
zero physical capacity or a confirmed physical failure. The largest listed-axis
component ratio is only 0.134, but that does not assess uplift, simultaneous
axes or the nonzero flange moments. The general catalog does provide a
directional unity equation (page 289), but that equation needs an applicable
resistance in every direction and does not assign a free-moment resistance.
All six complete wrench checks remain unassessed. The
[base-angle remedy study](round-base-angle-remedy.md) identifies the A34/SD
uplift-rated alternative and the exact manufacturer applicability questions.

The other 22 angles per case now have explicit flange and individual-screw
demands. Their loaded member, supporting member and grain orientation still
need a tested installation mapping; a scalar vector magnitude cannot be
compared with an arbitrary table direction. The largest flange resultant is
1,692.894 N at `clip_split_top_center_left` in F10, accompanied by a
43,394.840 N·mm moment about the bend origin. The greatest individual SDS
withdrawal component is 647.456 N at that angle's `beam_3` screw. No standalone
SDS capacity is inferred from a whole-connector table, and screws are not
assumed to share load equally.

## Eight leg bolts

Each current bolt is nominal 3/8 inch through two 38.1 mm members. The runner
uses the existing [directional dowel-yield calculation](../fea/lumber_leg_resistance.py)
with [AWC TR12](https://web-media.awc.org/wp-content/uploads/2021/12/17210714/AWC-TR12-1510.pdf).
The conditional calculation assumes DF-L specific gravity 0.50, a 0.298-inch
effective diameter throughout the shear plane, 45,000 psi steel bending yield,
no gap and the existing conservative reduction terms. Bearing references are
resolved separately against the rim and leg grain directions.

| Native case | Controlling bolt | Lateral demand (N) | Conditional lateral reference (N) | Ratio |
| --- | --- | ---: | ---: | ---: |
| F10 | right 4 | 560.473 | 787.430 | 0.712 |
| C6 | left 1 | 411.554 | 825.143 | 0.499 |
| C10 | left 4 | 726.992 | 792.800 | 0.917 |

These are individual lateral reference ratios before unresolved end-use
adjustments, bolt-group action and splitting. Axial bolt components also occur:
their greatest absolute magnitudes are 315.517 N, 288.530 N and 269.468 N in
F10, C6 and C10 respectively. Washer bearing/pull-through, axial bolt resistance,
the delivered bolt's steel and thread dimensions, combined axial/lateral action
and group resistance remain separate. Ratios below one therefore do not pass
the complete leg joint, and references are not multiplied by eight.

## Round-bore member sections

The [2024 NDS, Chapter 3](https://web-media.awc.org/wp-content/uploads/2021/12/17210019/AWC_NDS2024_withCommentary_20240718_AWCWebsite_Chapter-3-Design-Provisions-and-Equations.pdf),
§3.1.2.1, requires removed material and load eccentricity to be considered in
net-section capacity. Section 3.8.2 addresses avoiding perpendicular-to-grain
tension and considering reinforcement where it cannot be avoided. Neither
provision turns an enclosed-hole fit check into a general bore-strength approval.

At the center of a transverse 25.4 mm passage, the cross section perpendicular
to grain loses a **38.1 × 25.4 mm rectangle**, rather than a circular area.
The projection passes through the full member width. For the 38.1 × 139.7 mm
members with the bore centered 35 mm behind the panel-contact face:

| Section quantity | Value |
| --- | ---: |
| Front ligament | 22.300 mm |
| Rear ligament | 92.000 mm |
| Gross area | 5,322.570 mm² |
| Isolated-bore net area | 4,354.830 mm², 81.818% of gross |
| Net centroid behind front face | 77.594 mm |
| Net second moment about section u | 7,167,754.885 mm⁴ |
| Net second moment about section v | 526,792.898 mm⁴ |

Those properties exclude other fastener holes and oblique end effects. They
describe the two remaining ligaments of one perforated member; they do not
establish local load transfer around the opening. The native stiffness model
retains only the continuous rear 38.1 × 92.0 mm rectangle, approximately
65.855% of gross area, and omits local bore geometry from its stress mesh.

For each bore, the runner cuts the frozen member at the bore center and sums
the reported upper-grain connector forces and original gravity loads. Moments use the
net-section centroid, including its eccentricity. A discrete load exactly at
the cut is rejected. The largest absolute nominal normal stresses from that
section-equilibrium calculation are:

| Native case | Controlling isolated bore section | Nominal stress magnitude (MPa) |
| --- | --- | ---: |
| F10 | center-left principal, passage 060 | 1.300 |
| C6 | lower-left service rail, passage 018 | 3.768 |
| C10 | upper-left service rail, passage 017 | 0.795 |

The JSON retains axial force, both shears, both bending moments and torsion for
every cut. These stresses assume plane-section behavior. They do not include
hole-edge stress concentrations, local shear flow, perpendicular-to-grain
splitting, torsional strength or instability. They also do not replace the
native retained-prism integration-point peaks elsewhere: the largest grain
normal magnitudes are 7.936 MPa in F10, 9.580 MPa in C6 and 4.456 MPa in C10.
The different quantities cannot be used to claim that the bores reduce stress.

The original frame has clamped feet, isotropic 7,000 MPa material, analyst-chosen
1,000 N/mm connector stiffness and finite load probes. Material grade/species,
moisture, restraint, wood adjustments and applicable local resistance still
govern a design check. No member strength or unanchored-floor approval follows
from these demand recoveries.

## Reproduce

Expand the preserved native archive to its recorded three-case directory, then:

```sh
uv run python -m fea.round_member_connection_assessment \
  --directory fea/generated/round-frame-batch-v1 \
  --output /tmp/round-member-connection-assessment.json
uv run pytest tests/test_round_member_connection_assessment.py -q
```

The assessment runs no solver. Unit checks independently cover transverse-bore
projection/inertia, eccentric tensile force and moment signs, interpolation
ownership, bolt action/reaction and retained gravity. The inspected Simpson
and NDS PDF byte hashes are recorded in the result; vendor PDFs are not
redistributed.
