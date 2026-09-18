# Preferred compact 4×6 development frame

The owner selected the solid-4×6 direction as the preferred development candidate.
`compact-thick-development` implements the requested flush rims, three-bolt leg
joints and smaller kicker base. It is not a released construction design. The
preceding single-pivot comparisons do not transfer to this changed assembly.

## Requested geometry

- Single 88.9 × 139.7 mm (nominal 4×6) legs and outer rims. The rims' outside
  faces align with the plywood edges, at X = ±1219.2 mm.
- The top rail is shortened 101.6 mm overall; the outer ends of the other
  affected horizontal rails are shortened 50.8 mm. Rim-mounted commercial
  angles move to the new receiving faces.
- The header and its supporting posts use nominal 2×6 stock, with a 139.7 mm
  front-to-back depth. The header returns to 2438.4 mm overall length.
- The inclined rim/principal ends are trimmed to Y = −182.7 mm, leaving a
  7 mm rear overhang beyond the base. This preserves a little more wood than
  cutting the ends flush with the back of the 2×6 header.
- The floor-to-main-face datum remains 277 mm, comprising the retained 150 mm
  exposed kicker and 127 mm pad allowance. The 66 panel/kicker screws, panel
  datums and 142 T-nuts remain the accepted construction basis.

The first flush-cut proposal removed approximately 36.89 mm normal to the
139.7 mm members' grain, slightly exceeding the quarter-depth end-cut screen
(34.925 mm). This was a placement/detail concern, not proof that a 2×6 base
cannot carry the load. Retaining 7 mm of rear overhang reduces the nominal
cut depth to approximately 31.53 mm. The remaining approximately 3.39 mm
margin accommodates the study's 3 mm combined cutting/layout allowance.

The end-cut screen follows NDS 4.4.3.1; the changed bearing and shear demands
must also be evaluated. A nominal geometric margin alone does not qualify the
cut. See [AWC's sawn-lumber provisions](https://awc.org/wp-content/uploads/2021/10/AWC_NDS2018-withCommentary_20200827_AWCWebsite_Chapter04.pdf).

## Current verification status

Fresh raw-CAD checks confirm the requested flush rim positions, shortened rail
envelopes, 2×6 base and revised screw tips reaching their wood receivers.
The complete six-bolt receiver audit also passes, including actual 88.9 mm
bearing intervals in both members, hole containment and washer support.

The first assembled case is numerically accepted: A12, twice the downward
force of a 250 lb climber, plus 300 N rearward and the retained equipment
allowance. **The three-bolt joint does not pass its lateral comparison.**

| Comparison | Result |
| --- | ---: |
| Worst individual bolt demand/reference | 7221.7 / 2267.8 N = **3.185** |
| Additional conservative group-factor sensitivity | 3.191 |
| Left joint moment about the bolt axis | 723.15 N·m |
| Minimum adjusted directional edge/end margin | −30.49 mm |
| Maximum sampled rim net-section comparison | 0.698 |
| Header gross-section comparison | 0.445 |
| Maximum conservative end-notch shear comparison | 0.140 |
| Maximum quarter-area header-bearing sensitivity | 0.0215 |
| Maximum timber displacement | 56.66 mm |

The edge result uses the retained conservative 4D loaded-edge rule for oblique
force. The bolt that triggers the worst rim-edge result has only approximately
48 N perpendicular to the rim grain, within approximately 7222 N total lateral
force. Thus that particular placement flag must not be presented as a universal
oblique-load code failure. The lateral demand/reference shortfall is independently
substantial and does not depend on accepting that edge interpretation or the
additional group reduction.

An independent force/coordinate audit reproduced the left joint moment and found
no sign, member-axis or connection-mapping error. Most front posts lift in this
modeled contact state. The large deformation is another reason not to interpret
the linear elastic result as a completed serviceability or physical load rating.
The small base reactions in this upper-hold case do not establish the base's
complete load envelope. A second numerically accepted case applies the same
250 lb doubled downward load and 300 N rearward at A1. It gives header gross
ratio 0.202, conservative end-notch shear ratio 0.242 and quarter-area bearing
sensitivity 0.0634. Its leg-bolt ratio is 0.137 and timber displacement 2.11 mm.
These two cases support retaining the compact 2×6 base for development, while
the upper-hold leg-joint failure still prevents release. They do not constitute
an exhaustive load envelope.

[Archived evidence](../fea/results/compact-thick-study/manifest.json) records the
native report, authenticated producer snapshot, actual CAD receiver report and
recomputable checks. The [bounded layout screen](../fea/results/compact-thick-study/layout-screen.json)
reuses this actual joint wrench for two-, three- and four-bolt families. It is
an optimistic fixed-resultant screen, not an assembled prediction or proof that
all conceivable layouts fail. No passing layout was found in the tested families.
Adding another bolt alone is therefore not the supported next design decision;
reducing the joint moment through the structural layout merits evaluation.

The three noncollinear bolt positions provide a moment-resisting group in the
response model. Individual finite-stiffness connectors transfer the resulting
forces; the group is not assigned the previous pivot's free-rotation assumption.
The calculation must use each bolt's recovered simultaneous force, including
axial demand, rather than dividing an earlier single-bolt force by three.

## Finite build-readiness requirements

1. Establish a supported leg/connection decision for this exact geometry,
   including directional bolt placement, lateral demand, group behavior,
   washer/axial demand and the affected timber sections.
2. Check the compact base's actual partial bearing and trimmed end sections
   using the revised assembly's reactions; do not assign support to the
   7 mm overhang.
3. Match purchasable bolts, nuts and washers to the seven-inch wood grip,
   including nut seating, thread runout, full nut engagement and the actual
   threaded-bearing interpretation used in resistance calculations.
4. Issue matching stock, drilling, trim and assembly instructions, with practical
   tolerances and access, then verify the same configuration in CAD, the viewer
   and the engineering evidence.

These requirements retain the [agreed DIY scope](current-diy-completion-record.md).
They do not add independent professional sign-off, a new panel/T-nut campaign or
floor-friction testing. The no-slip floor premise remains an explicit analytical
assumption; no safe climber weight or physical load-test result is claimed.

## Reproduction

```sh
uv run python -m scripts.compact_thick_results
uv run python -m scripts.compact_joint_screen
uv run python -m mini_moonboard.compact_thick_exports --check
uv run python -m scripts.compact_construction_schedule
```

The matching [construction package](compact-construction-package.md) contains
candidate dimensions and assembly notes. **Do not use its leg drilling as a
released construction detail:** the three-bolt connection has a calculated
shortfall. The preferred 4×6 direction and compact 2×6 base remain development
choices while the connection load path is resolved.

## Software and package verification

393 default tests passed, with 15 historical tests deselected. Ruff, whitespace
checks, the fresh standalone export comparison and the browser interaction check
passed. The browser selects the compact candidate by default and displays all
six complete bolt stacks. The matching construction schedules authenticate the
same exported geometry; an independent review reconstructed all twelve
member-side bolt coordinates from their stated physical corners.

The mesh-based frame mass is approximately 200.31 kg (441.61 lb), excluding the
listed unmodeled equipment. Earlier models and their mass values are preserved.
Software and package consistency do not override the recorded joint failure.

## Follow-up assembled trials

The separate two-bolt `compact-two-development` trial uses two provisional
¾-inch bolts per leg at the saved 77 mm spacing, retaining the compact base
and flush 4×6 rims. Its actual A12 rearward solve is numerically accepted.
The worst nominal lateral demand/reference is **2.208**, approximately 31%
lower than the preferred three-bolt result, but still substantially above 1.
The full thread-root sensitivity is 3.060. Actual receiver fit passes, the
minimum adjusted directional edge/end margin is +1.10 mm, and the listed
steel and washer screens remain below 1. These results do not qualify
the connection or justify releasing its drilling. The two-point model permits
rotation about the line joining its bolts; installed joint behavior remains
unverified. Maximum timber displacement is 58.33 mm.

[Two-bolt evidence](../fea/results/compact-two-study/manifest.json) preserves
the native report, authenticated source snapshot, actual receiver geometry
and recomputable checks (`uv run python -m scripts.compact_two_results`).
The [low-rail trials](compact-rail-study.md) both failed contact convergence
and provide no usable strength conclusion. Neither experiment replaces
the preferred viewer configuration. The compact 2×6 base remains the retained
development choice; the upper leg connection remains the release blocker.

The subsequent [bounded options study](compact-options-study.md) audits load and
resistance assumptions, larger/stronger bolts, bolt layouts and leg geometry.
