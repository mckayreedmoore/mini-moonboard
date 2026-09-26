# First-knot penalty comparison: motion and energy

At t=0.001 s, reducing the numerical contact penalty from 100000 to
10000 N/mm³ changes the complete loaded-node and nut-controller motion fields
beyond the declared numerical triage limits. The monitored scalar q changes
only 4.19%, which would hide those differences if used alone. The native
energy discrepancy also rises from 1.230541% to 3.905511%. This result does
not justify adopting the lower penalty as a convergence shortcut.

The [comparison script](compare.py) and [JSON report](report.json) bind both
immutable first-knot snapshots and the [comparison contract](../penalty-comparison-contract.md).
Each branch accepted its first increment from zero to 0.001 s on attempt 1;
the baseline took 25 iterations and the child 26. Forces, initial state,
mesh, material scenarios and output time are unchanged. Later adaptive
histories are outside this comparison.

| Quantity | K=100000 | K=10000 | Numerical comparison |
| --- | ---: | ---: | --- |
| q (mm) | 2.3186867121e-5 | 2.4159449446e-5 | 4.1945%; within 5% scalar screen |
| Maximum loaded-node displacement magnitude (mm) | 1.8515880223e-5 | 1.9882482444e-5 | Summary only; field comparison below governs |
| Complete loaded-node displacement field | 331 nodes | same 331 nodes | L∞ difference / baseline L∞ = 14.8991%; flagged |
| Complete nut-controller rotation field | 4 nodes | same 4 nodes | L∞ difference / baseline L∞ = 23.8486%; flagged |
| Internal energy (N·mm) | 4.795230e-8 | 4.952922e-8 | 3.2885%; within 10% screen |
| Kinetic energy (N·mm) | 2.971466e-7 | 3.098743e-7 | 4.2833%; within 10% screen |
| Elastic penalty energy (N·mm) | 4.636793e-9 | 1.463120e-8 | Reported separately; relative change is not a stability criterion |
| Native external work (N·mm) | 3.454843e-7 | 3.599758e-7 | First-increment discrete work is reconstructible |
| Native relative energy discrepancy | 1.230541% | 3.905511% | Above declared 2% screen; flagged |

The largest loaded-field difference is 2.014678e-6 mm at node 9, global
component 1, normalized by the baseline field norm 1.352211e-5 mm. The largest
controller difference is 1.195379e-8 rad at node 116168, component 3, normalized
by 5.012359e-8 rad. These are signed-field comparisons with matching IDs;
they are not percentages of the change in maximum displacement magnitude.
The four controller IDs are explicitly declared `ROT NODE` values in the
hash-checked rigid-body fragment. CalculiX 2.21's `*RIGID BODY` definition
(manual section 7.112) uses those dummy nodes' printed U1–U3 values as angular
coordinates about the reference node. Their radian interpretation does not
come from the generic DAT displacement heading or apply to physical nodes.

The script validates snapshot/file hashes, complete monitor membership,
actual first-step status records and identical unit-force weights. It also
hash-checks both actual pilot decks, verifies all 662 CLOAD components against
the unit weights, checks the ramp, and derives the first-knot force used for
work instead of hardcoding it. It reconstructs q and parses each native energy
summary. Ruff and formatting checks pass. The [independent accounting
review](independent-review.md) records its reviewed scope and code version.
Contact-pair coverage, contact overlap and per-owner momentum
are separate audits; missing results are not filled by these field checks.

These analyst-set screens are not adopted structural checks. Both branches
retain a coarse first step and provisional stiff nut engagement. No time
accuracy, physical contact law, joint capacity or full-frame case is accepted.
