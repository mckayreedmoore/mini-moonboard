# Exterior-knee contact verification

September 14, 2026. The corrected floor model and revised upper joint now meet all 25 listed conditional criteria in all six current load cases. The separate 5×5 A12-left foot-grid sensitivity also passes. The exterior knee is the selected conditional candidate. The original no-slip search and the first corrected-floor 56 mm joint remain historical diagnostics below; neither supplies the current acceptance evidence.

The implemented correction uses 64 mm upper-bolt pitch, 24 mm leg-top projection and 3.0–3.3528 mm delivered upper-washer thickness. Worst current bolt ratio is 0.985043; washer bending is 0.757756. See the [complete six-case results](clear-space-study.md) and [upper-joint detail](exterior-upper-joint-revision.md).

## Corrected floor model and current result

The old model applied horizontal restraint at each foot centroid whenever any normal contact on that body remained active. Besides switching abruptly at lift-off, this could demand a floor friction moment unavailable from the actual loaded edge or corner. The replacement removes those centroid springs and places horizontal reactions at each normal-contact point. Each point carries at most `mu * max(N, 0)` in the horizontal plane; an unloaded point carries no horizontal force.

The current trial assumes `mu = 0.4` and monotonic loading from zero initial slip. It retains the same loads, elastic reference stiffness, normal-contact tolerance, and global/member equilibrium checks. This is an explicit installation assumption, not measured floor friction or a cyclic slip model. The new floor law must be used consistently for all six load cases before a complete comparison is accepted.

The [fresh A12-left archive](../fea/results/exterior-cells04-verified/a12-left/) converged after 38 native solves. Normal contact passed and the maximum friction-law residual was 0.009539 N, below the unchanged 0.01 N force tolerance plus recorded output rounding. An independent assessment recomputes the force cap from the saved collocated reactions.

The existing 56 mm upper bolt pattern then produced:

| Check | Result |
| --- | --- |
| Upper left bolt #2 lateral demand/reference | 2892.07 / 2811.60 N = **1.02862** |
| Upper left bolt #1 washer bending | **1.59492** |
| Upper left bolt #2 washer bending | **1.34825** |
| Maximum sampled net-member ratio | 0.45007 |

The bolt's governing lateral mode is wood-bearing mode II, so a higher steel grade alone does not address it. The implemented revision spreads the upper pair and provides the required end reserve, together with thicker round washers. Its fresh assembled-frame cases now pass; fixed-force arithmetic was only used to select the trial.

## Historical no-slip verification

## What was checked

The existing controlled attempt restricted simultaneous floor-contact changes
but still changed panel/header contacts together. Its recorded history contained
1,164 panel-seat toggles, compared with 38 post-floor and 16 splice-contact
toggles. This motivated a search that changes only one violating normal contact
at a time, across all contact types. The largest geometric violation is tried
first; previously visited contact sets are skipped. Floor tangential restraint
still exists only while its body has an active normal contact.

The search retained the existing A12-left load (2224.1108 N downward and 300 N
leftward), geometry, stiffnesses and 1e-7 mm contact tolerance. All source files
recorded with the cached native structure matched current files. The only
additional current source identities were the unrelated 2×4 model and its
hardware reference. The cache was used for diagnostic search only; any found
state would have required a fresh normal-run confirmation before acceptance.

All **100** additional native linear solves passed global equilibrium, member
equilibrium and the interpolation-equation check. **None passed contact
admissibility.** The search stopped at its preset limit. No resistance ratios
from these rejected states are adopted and the missing three load cases were not run in that historical batch.

## Historical support difficulty

The closest state by invalid-contact count was cycle 25, with three violations:

| Contact | Residual |
| --- | --- |
| Right outer-post floor corner 1 | 0.00004484009 mm opening while active; −4.484009 N normal reaction |
| Panel seat 109 | 0.0000026 mm opening while active |
| Panel seat 136 | 0.0000030 mm opening while active |

At that state the right outer post had only one active floor corner, with
approximately 50.25 N horizontal spring force. Its negative normal reaction
would require the floor to pull downward on the foot. Releasing the last
normal contact also removed the body's horizontal springs. In the following
solve, that foot penetrated the modeled floor by up to 0.02211349 mm. Neither
state is admissible. These two states demonstrate the support-mode switching
problem; they do not prove that no valid state exists elsewhere.

The diagnostic points toward the coupled foot lift-off and tangential-support
assumptions, rather than an established knee-strength shortfall. The next
engineering question is how that interface carries or releases horizontal
force as normal contact vanishes. A justified contact/slip model or a revised
support detail must resolve that question before the exterior candidate can
be accepted. Increasing bolt size alone does not address this numerical gate.
No tangential restraint was retained on a fully detached foot merely to obtain
a passing result.

## Evidence and runner recess

The [verification archive](../fea/results/clear-space-exterior-trials/single-contact-verification/)
contains the search script and log, source identity comparison, all-iteration
summary, and compressed best/final native inputs and outputs. Its manifest
hashes every archived file. The [current study](clear-space-study.md) separates those earlier attempts from the six revised passing cases.

The proposed [inner-face leg recess](floor-runner-leg-recess.md) can move the
2×6 runners outside the panel edges and eliminate kicker notches geometrically.
It removes 1½ inches from the leg's 3½-inch thickness locally, leaving 2 inches;
the implemented trial passes its sampled actual-section and bolt checks, but local notch-corner resistance remains unqualified. See the [recess assessment](floor-runner-recess-study.md). It is a
separate alternative, not a repair credited in this exterior-brace analysis.
The exterior knees already clear the central climbing corridor without it.
