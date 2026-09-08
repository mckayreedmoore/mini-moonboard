# Coupled leg/rim connector trial

This trial removes the artificial leg-to-panel and leg-to-rim bonds in addition
to the [previous gusset releases](coupled-gussets.md). It evaluates the resulting
conditional bolt-location transfers in the coupled frame; it is not a physical
joint rating or construction approval.

## Geometry and connection scope

The CAD-audited current-wide leg mesh contains 3,954 left-leg and 3,953 right-leg
elements. Each leg has 405 shared interface nodes, with 148 faces against its
rim and 34 faces against the upper panel edge. All these faces are inventoried
in the [source-bound map](../fea/results/leg-connector-map.json). Both interfaces
are released, not merely the panel-edge bond.

The eight existing leg bolt axes map into the intended rim interfaces. Nearest
face nodes lie 6.484–8.611 mm away; quadratic point interpolation retains the
actual bolt-axis positions instead of snapping them to those nodes. The three
physical bolt members are the rim and two leg plies. The model treats the paired
glued plies as one bonded leg body, not as separately slipping layers.

Duplicating 810 additional nodes leaves every element coordinate, leg shape and
original floor support unchanged. Neither leg shares a solid node with another
body afterward. Each leg joins the rim through four three-axis point springs.
The existing eight gusset connectors remain: altogether 16 connector locations,
48 springs and 96 two-sided interpolation equations.

## Planned loads and numerical checks

The same numerical stiffness sweep—100, 1,000 and 10,000 N/mm per axis—is applied
to leg and gusset connectors together. These are assumed parameters, not
calibrated bolt properties or a bounding demand envelope. Nine X/Y/−Z bases at
A12, K12 and F6 feed the existing 150/200/250/300 lb, one/two-times-weight and
horizontal-force combinations when their numerical gates pass.

The prior coupled-gusset global, gusset, floor, positive-work and bonded-parent
compliance checks remain. Before these solves, additional gates were set at
0.02 N force and 10 N·mm moment residual for each leg, and 1e-5 mm interpolation
error at its connector points. **Leg equilibrium includes its native floor
reactions.** Unlike a gusset, a supported leg's connector forces alone must not
sum to zero. The replay test also checks compliance ordering as stiffness rises.

The reused deck helper internally calls the released endpoint `gusset_nodes`;
for the eight `analysis_leg_wall_bolt_*` entries these are leg nodes. Published
results distinguish `leg_connector_force_on_leg_n` from
`connector_force_on_gusset_n`; the internal field name does not change ownership.

## Remaining limitations

Leg plies remain bonded to each other. Other wood interfaces, including panel
attachments and remaining base junctions, remain ideal bonds. Material remains
isotropic E = 7,000 MPa with Poisson ratio 0.3; gravity is omitted and the floor
remains fixed XYZ, including the kicker. No released interface has unilateral
bearing/contact or friction in this trial. Point springs do not resolve holes,
washers, bolt bending or calibrated slip, and are equally stiff in all axes.

Actual bolt/washer axial resistance, three-member or bonded-laminate connection
resistance, plywood splitting/block shear and glue behavior remain separate
checks. Do not transfer the gusset's two-member bolt reference value directly
to a leg bolt. Unanchored contact and material/installation verification remain
required before use. No CAD, stock or fastener selection changes are made by
this numerical trial.

The run and archive tests retain failed attempts or numerical gates as failures;
only passing basis sets produce scenario vectors. Results and the design
disposition will be recorded after native output and replay verification.

## Verified results

All 27 native bases passed, producing 648 signed-vector load combinations.
The complete CAD/face-map replay, release-topology check and native archive
replay passed. Maximum leg equilibrium residuals over the bases were below
0.00110 N and 1.743 N·mm; maximum leg point-interpolation error was below
9.4e-7 mm. The inherited global and gusset gates also passed.

| Assumed stiffness per axis | Peak leg-connector resultant | Peak gusset-connector resultant | Peak loaded-hold displacement |
| --- | ---: | ---: | ---: |
| 100 N/mm | 364.97 N | 2.924 N | 7.8143 mm |
| 1,000 N/mm | 696.96 N | 4.572 N | 3.6815 mm |
| 10,000 N/mm | 903.48 N | 39.943 N | 2.7803 mm |

These are separate maxima over each stiffness's 216 combinations, not one
simultaneous state. Loaded-hold displacement is not the maximum over every
node in the frame. The spring parameters are not bounds on physical stiffness,
so neither end of this table is an actual demand or deflection bound.

At 10,000 N/mm, peak lateral leg-bolt demand within the trial is 903.13 N and
peak axial demand is 100.52 N; these are separately extracted maxima and
must not be treated as a simultaneous vector. The archive retains every
three-component force for combined-action assessment.

| Climber comparison mass | Peak leg connector at 100 N/mm | At 1,000 N/mm | At 10,000 N/mm |
| --- | ---: | ---: | ---: |
| 150 lb | 202.98 N | 386.86 N | 506.63 N |
| 200 lb | 256.98 N | 490.23 N | 638.91 N |
| 250 lb | 310.97 N | 593.59 N | 771.20 N |
| 300 lb sensitivity | 364.97 N | 696.96 N | 903.48 N |

Rows include the specified one/two-times-weight and horizontal cases. They are
not certified climber limits or an impact-load qualification.

## Design implication

The previous gusset-only release retained bonded legs and had a peak loaded-hold
displacement near 2.50 mm. The released-leg model is substantially more flexible
at the softer assumed stiffnesses. Do not use the earlier bonded-leg response
to establish real attachment stiffness. The conditional leg-connector demand
is also much larger than the gusset-connector demand in these trials.

The next resistance assessment should address the **actual rim plus two-leg-ply
bolt stack**, including whether bonded-laminate behavior can be credited,
actual thread participation, lateral yield modes, axial washer/wood bearing,
spacing/group effects and calibration of slip. An unadjusted two-member gusset
reference is not a leg-joint allowable. Do not increase the allowed climber
weight or reduce bolt count from these results.

Retain the present geometry for review until that comparison is made. The
remaining base bonds, bearing/contact, frame gravity, unanchored support and
panel/end-connector gates stay open. No physical adequacy claim follows from
the passing numerical checks.

The subsequent [leg-bolt resistance checkpoint](leg-bolt-resistance.md) records
the actual stack and a conditional bonded-laminate reference. It does not yet
qualify the physical joint or close the limitations above.

The [native archive](../fea/results/coupled-leg-release.tar.gz) retains all
decks, native results/logs, source hashes, leg-node remaps, basis results and
scenario vectors. The separate map provides member/face/point identities.

```sh
uv run pytest -q tests/test_coupled_leg_release.py
```

Independent correctness, testing and architecture/package reviews found no
substantial issues in the completed implementation and archived results.
The broader connection/recovery regression passed 44 tests; Ruff and
`git diff --check` were clean. Reviewers independently checked archive counts
and numerical maxima. These reviews do not constitute structural approval.
