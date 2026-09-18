# One knee-brace load-path trial

This bounded study adds one solid 4×6 knee per side to the higher225 refined
three-bolt frame. The compact 2×6 base, flush 4×6 rims, existing upper bolts,
panel attachments and no-slip floor assumption remain. It is a development
trial, not a construction release or a change to the viewer default.

The rim attachment is at slope station 1400 mm; the leg attachment is at
1050 mm above the floor. Each brace has 110 mm of stock beyond each bolt.
Opposite 44.45 mm end tabs allow the brace to contact the adjacent rim and leg
planes without notching either host. The revised detail uses two ⅜-inch bolts
at each brace end, spaced 50 mm along that host's grain; the upper leg joint
retains three half-inch bolts. Heads face the thin tabs so
ordinary partial threads can lie in the thicker receiving members.

The first geometric trial used a 160 mm leg-side tab reach and interfered with
each leg by 16,675 mm³. Its source and geometry are preserved in
`fea/results/compact-knee-study/first-fit-*`. The revised reach is 200 mm;
the rim-side reach is 140 mm. This changes the brace alone.

## Screening limits

The first native calculation uses the full gross brace section for stiffness.
Actual tab bearing lengths and machined net sections are checked separately.
Those checks cannot correct the gross-section force distribution or establish
tab shoulder resistance. The explicit machining inventory includes every tab
rebate and bolt hole; unsampled notch boundaries remain identified.

The half-width rebate preserves strong-axis depth but halves weak-axis depth.
The ordinary end-notch provision for bearing over a support does not directly
qualify this eccentric bolted lap. Actual tab stiffness, eccentricity and
transition splitting/shear require resolution before construction release.
See [NDS §4.4.3](https://awc.org/wp-content/uploads/2021/10/AWC_NDS2018-withCommentary_20200827_AWCWebsite_Chapter04.pdf).

The revised provisional ⅜×6-inch bolt stack has 133.35 mm of wood grip. Actual
thread transition, nut seating and material conformity require acceptance;
the preceding 8-inch upper-joint bolt is not interchangeable. The screen uses
the specified 90 ksi bending-yield reference with Grade 5 material conformity
required. Washers retain an explicit material assumption; nominal CAD fit is
not a delivered-product certificate. The earlier ½×6½-inch concept has a
catalog example in [Bolt Depot 28656](https://boltdepot.com/Product-Details?product=28656),
but that product does not specify the revised ⅜-inch stack.

## Result

The single-bolt-per-end calculation converged its contact set in 11 iterations
but failed global and member equilibrium. Its approximately 2.48 billion mm
maximum timber displacement is an invalid numerical result, not a predicted
physical deflection. Two point attachments leave rotation about their connecting
line unrestrained in this connector model. Its archived forces are not used
for resistance comparisons. The paired end bolts explicitly provide
noncollinear attachment points; a rigid-body rank check verifies that this
rolling mode is removed without adding artificial supports.

The paired-bolt assembly passes all 28 actual bolt-receiver checks. Its native
A12 case is numerically accepted after 12 contact iterations, including global
and member equilibrium. The doubled 250 lb downward load and 300 N rearward
load remain unchanged.

| Comparison | Paired-knee result |
| --- | ---: |
| Worst actual-angle individual bolt ratio, Cd=1, specified Fyb=90 ksi | 0.472 |
| Worst knee-to-rim bolt ratio | 0.403 |
| Worst knee-to-leg bolt ratio | 0.308 |
| Original maximum-angle full-root sensitivity | 0.763 |
| Minimum upper-joint directional edge/end margin | −30.55 mm |
| Minimum knee-connection directional edge/end margin | +3.82 mm |
| Worst sampled knee net-section ratio | 0.297 |
| Worst sampled rim net-section ratio | 0.532 |
| Worst sampled leg net-section ratio | 0.267 |
| Nominal washer bending ratio | 0.196 |
| Maximum timber displacement | 6.38 mm |

Relative to the unbraced higher225 refined assembly, the worst actual-angle
bolt ratio decreases from 0.770 to 0.472, and maximum timber displacement from
15.63 to 6.38 mm. This supports investigating the braced load path. It does
not establish completed frame acceptance.

The remaining placement failure is **upper left bolt 2 in the leg**, not a
brace bolt: its adjusted loaded-edge distance is 20.25 mm against the retained
50.80 mm reference. The failing member/bolt has changed from the unbraced
assembly. Smaller demand does not waive that placement requirement. The right
upper group also has only 0.145 mm minimum reserve in this case, below the
3 mm screening reserve used to select earlier layouts.

The finite next design work is to revise the upper bolt placement under this
braced load path, retaining at least two upper bolts, and resolve the actual
brace-tab stiffness and local transition detail. Increasing bolt grade alone
does not address either issue. Additional load cases and construction release
should follow that resolution. No knee design is selected as build-ready, and
the viewer retains its preceding candidate.

Evidence: [paired native archive](../fea/results/compact-knee-study/paired-rear/manifest.json),
[all-bolt and sampled net checks](../fea/results/compact-knee-study/paired-rear/knee-checks.json),
[rejected single-bolt archive](../fea/results/compact-knee-study/single-bolt-rejected/manifest.json).

## Reproduction

```sh
uv run python -m scripts.compact_knee_study --output fea/generated/compact-knee-paired-a12
uv run python -m scripts.compact_knee_results --archive fea/results/compact-knee-study/paired-rear
```

The native output directory must be new; the shown path identifies the completed
local job. Recomputing the archived checks does not rerun the native solver.

Verification: 426 default tests passed, 15 historical tests deselected. Ruff
passed. Numerical acceptance and software checks do not override the remaining
placement failure or qualify the brace tabs.
