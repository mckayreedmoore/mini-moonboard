# Six-bolt single-2×8 leg assessment decision

**Source-audit qualification:** The subsequent
[criteria and limits review](wider-leg-criteria-review.md) clarifies that the
4D edge distance below is a conservative screen for this oblique connection,
not an explicit NDS oblique-loading minimum. The full-foot endpoint is a
limiting contact sensitivity, not a demonstrated normal-use condition. The
saved numerical results remain reproducible; neither should be interpreted as
a prediction of actual collapse. This candidate remains unqualified.

**Do not release this candidate for construction.** The requested CAD, hardware
selection and remaining analytical checks have been performed. They expose a
loaded-edge placement failure and a separate full-foot-pressure sensitivity
failure. This is a completed negative assessment of this candidate, not a
claim that the board will physically break at the reference limit.

## Completed design work

The [review package](wider-leg-review/README.md) contains the complete assembly
STEP file, drilling coordinates, lumber schedule and nominal interference
checks. It uses single 2×8 legs and outer rims, six ½-inch catalog bolt stacks
per leg, standard bearing plates and three extra-thick washers per nut. The
new leg detail requires no custom steel fabrication. The isolated assembly
retains historical base components; it is not a fabrication-free redesign of
the entire board.

All twelve stacks fit in nominal CAD. All twenty-four bearing plates are
supported by wood. All twenty-four member bores are contained. These fit
results do not establish adequate loaded-edge distance.

The final calculations use actual modeled mass (194.583 kg), another 25 kg for
holds/electrical equipment, all 142 hold positions, and the revised joint
centroid. The load comparison is a 250 lb climber with twice body weight
downward, up to 300 N rearward force and 100 mm hold projection. All rear
compression is assigned to one leg; feet are assumed not to slide. The local
leg-weight term conservatively repeats a small allowance already included in
global gravity. Member bending also includes the 3.280 mm offset between joint
and stock centerlines. Permanent-only cases use the 0.9 NDS duration factor;
the climbing comparison retains 1.0. No floor-friction test is introduced.

## Numerical decision

Ratios compare demand with the stated analytical reference; 1.0 is the limit.
They are not ultimate breaking-strength ratios. The middle-third column assumes
nonnegative linear pressure over the whole foot. The full-foot column allows
the pressure resultant to reach either end of the actual foot.

| Check | Middle-third pressure | Full-foot endpoints |
| --- | ---: | ---: |
| Bolt lateral resistance | 0.817 | **1.728 — fails** |
| Conservative bolt lateral plus axial interaction | 0.860 | **1.773 — fails** |
| Leg net-section and stability interaction | 0.693 | 0.967 |
| Rim supplemental splitting | 0.596 | 0.719 |
| Bearing-plate plastic bending | 0.822 | 0.855 |
| Individual extra-thick washer bending | 0.131 | 0.136 |
| Minimum loaded-edge/spacing reserve | **−12.755 mm — fails** | **−12.928 mm — fails** |

The rear rim bolts have only 38.045 mm to their loaded rear edge in the
governing middle-third case. The applied 4D criterion requires 50.8 mm for a
½-inch bolt. Thus even the narrower pressure assumption does not produce a
passing connection. This is a structural placement issue, despite nominal
hardware fitting without collisions.

The larger foot also permits greater joint moment when pressure moves toward
its ends. Maximum compression is about 4.245 kN in the middle-third sweep and
4.416 kN in the full-foot sweep. Allowing full-foot pressure raises the
governing lateral ratio to 1.728. Middle-third contact has not been established
as a physical restriction on this assembly.

The original 0.818 feasibility number remains reproducible for its preliminary
screen. That layout centered the enlarged stock on the old axes. Actual CAD
had to keep the panel-facing rim surface fixed, grow the rim rearward and move
the bolt group to support the square bearing plates. The actual loaded-edge
check is therefore essential; the preliminary placement pass cannot transfer.

## Remaining conditions, stated precisely

This candidate cannot be selected merely by confirming the design assumptions.
There are two demonstrated failures and two unresolved qualifications:

1. **Rim loaded-edge distance:** revise stock/bolt/plate geometry to provide the
   required distance. Simply drilling the current CSV does not satisfy it.
2. **Foot-induced joint moment:** provide a connection that passes the full
   pressure range or a mechanically established restraint on that range.
   Assuming centered pressure is insufficient.
3. **Lap-joint prying:** the calculation uses a 2× axial-force amplification;
   equilibrium and geometry alone do not establish it as an upper bound.
4. **Bearing-plate material:** the selected BP1/2 catalog supplies dimensions
   but does not establish the assumed 33 ksi yield floor. Obtain exact-product
   material evidence or select and recheck a catalog plate with declared grade.

Increasing only bolt diameter does not resolve these findings: it increases
required wood distances and does not constrain foot pressure or prying.
Larger single stock remains a possible design route, but this assessment does
not claim an untested 2×10 substitution fixes all four items.

## Reproduction and scope

Run `uv run python -m fea.wider_leg_assessment` to regenerate the
[source-bound result](../fea/results/wider-leg-assessment.json). The result
includes individual governing forces, local wood checks, hardware checks,
pressure scopes and source hashes. Methods are documented in
[wood checks](wider-leg-wood.md) and [hardware checks](wider-leg-hardware.md).
The final focused suite passes 19 tests; Ruff passes and both CAD and
assessment source-hash sets match. Independent review confirmed the loaded-edge
failure and prompted the centerline-moment and permanent-duration corrections.

The selected baseline and viewer remain unchanged. This decision neither
reopens the owner's panel/T-nut acceptance nor supplies whole-frame approval,
a climber failure-weight rating, or a floor qualification.
