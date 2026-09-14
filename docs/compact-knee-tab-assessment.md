# Compact knee half-width tab assessment

2026-09-13. Scope: the opposite 44.45 mm end tabs in each solid 88.9 ×
139.7 mm knee, using the archived `compact-knee-paired-development` rearward
load case. This assessment does not transfer its forces to subsequent geometry
or stiffness revisions.

**Decision: the current unreinforced square-shouldered tab cannot be qualified
with the repository's existing resistance methods.** The nominal net-section
comparison is favorable, but it does not calculate resistance to splitting at
the abrupt shoulder. This is a specific missing resistance mechanism, not a
prediction that the tab will fail at the modeled load. Changing only the native
stiffness or upper bolt layout cannot close this resistance decision.

## Actual evidence

Inputs are `fea/results/compact-knee-study/paired-rear/report.json.gz`,
`geometry.json` and `knee-checks.json`. The native numerical gates pass. Both
braces use gross constant-section stiffness in this archive; the postprocessor
subtracts actual half-width cut boxes and bolt-hole bounds for stress checks.

| Archived quantity | Left knee | Right knee |
| --- | ---: | ---: |
| Maximum sampled axial tension | 1165.90 N | 164.90 N |
| Peak sampled net tension/bending comparison | 0.29719 | 0.04236 |
| Peak sampled nominal shear comparison | 0.01136 | 0.00361 |
| Maximum axial force × 22.225 mm tab eccentricity | 25.912 N·m | 3.665 N·m |

The eccentricity values illustrate the scale of the required moment transfer;
they are not substitutes for signed, station-matched moments. Both net peaks
occur at −302.89394 mm from the CAD member center near the rim-end bolts. The
left peak includes both bolt-hole bounds and has net area 5221.764 mm². Its
stress comparison already includes centroid eccentricity; adding the same
axial eccentricity again would double count it.

The rim shoulder is at −164.75549 mm and the leg shoulder at +104.75549 mm
from that center. The archived diagnostic records explicitly identify both as
unsampled. Sampling elsewhere inside a tab does not establish the shoulder
stress. The half-width portions extend 250 and 310 mm from the corresponding
physical ends. Before holes, their area and strong-axis second moment are half
those of the blank; weak-axis second moment is one eighth. Consequently the
gross-stiffness solution is a load-path screening result.

## Applicable analytical route and acceptance criteria

The net-section route is [NDS §§3.1.2 and 3.9](https://awc.org/wp-content/uploads/2021/10/AWC_NDS2018-withCommentary_20200827_AWCWebsite_Chapter03.pdf):
use the remaining section, its shifted centroid, and actual axial and biaxial
bending actions. For a revised physical-stiffness solution, evaluate both sides
of each shoulder and each bolt station. The adopted tension/bending interaction
and applicable shear comparison must each be at most 1.0; compression cases
also need the applicable stability interactions and positive stability
denominators. Keep the adopted material values and Cd = 1. These are necessary
section checks, not a splitting criterion.

The ordinary beam-notch provision does not supply the missing acceptance.
[NDS §4.4.3.1](https://awc.org/wp-content/uploads/2021/10/AWC_NDS2018-withCommentary_20200827_AWCWebsite_Chapter04.pdf)
addresses end notches for bearing over a support, limited to one quarter of
beam depth. This detail is a bolted lap with an abrupt width reduction. It
preserves the 139.7 mm strong-axis depth, so comparing 44.45 to that depth is
not an appropriate automatic rejection. Conversely, under weak-axis bending,
the 88.9 mm dimension is the bending depth and its reduction is 50%; calling
the cut a width rebate does not create an exemption. The ordinary beam-notch
permission therefore does not establish a pass for the eccentric lap.

A square re-entrant shoulder under tension and eccentric bending requires a
local splitting or fracture assessment beyond nominal net stress. [AWC's NDS
commentary addendum](https://web-media.awc.org/wp-content/uploads/2021/12/17210638/AWC-1991NDS-Updates-Errata.pdf)
explains that sawn-lumber perpendicular-to-grain tensile design values are not
published because checking and splitting affect them, and recommends
considering mechanical reinforcement when that stress cannot be avoided.
The archive actually places the knees in tension, so an assumed
compression-only transfer is contradicted by the available result.

For the unreinforced shoulder, acceptance would require a substantiated
notch/fracture resistance model applicable to this species, grade, moisture,
tab dimensions and loading, with demand/resistance at most 1.0. No such model
or calibrated resistance input exists in the current implementation. A mesh
peak stress, an invented perpendicular tensile allowance, or simply applying
the ordinary end-bearing-notch shear equation cannot replace it. The result
for this mechanism is therefore **NOT SUBSTANTIATED**, even when the nominal
section comparison is below 1.0.

## Smallest targeted physical change

The least disruptive detail to investigate is mechanical reinforcement across
the potential grain-parallel split at each tab shoulder, preserving the knee
position, host members and lap faces. This would be an explicitly designed
reinforcement fastener or connection across the full-width region adjacent to
the shoulder, with its anchorage on both sides of the potential split and all
required edge distances. It is not an extra bolt placed arbitrarily in the
existing tab, and no reinforcement SKU, count or drilling is selected here.

That route has a concrete acceptance condition: use the actual local
opening/shear demand and design the reinforcement and its two anchorage zones
to carry it without credit for unestablished wood tension across the split;
every applicable resistance ratio must be at most 1.0. Net section, bolt
group, bearing, and physical-stiffness checks still apply. A manufacturer or
published engineered reinforcement method must support that force-transfer
model. A cosmetic fillet or taper alone is not claimed to qualify a 50%
weak-axis reduction.

## Bounded through-bolt reinforcement route

The requested pair of 3/8-inch through-bolts near each shoulder has a useful
analytical route that avoids assigning wood perpendicular tensile strength:
**assume complete separation along the knee's X midplane.** The remaining
pieces are two unnotched 44.45 × 139.7 mm timber segments with a central overlap
of 269.51098 mm. The four added through-bolts must transmit the full load
between those segments. This treats the reinforcement as an actual timber
splice designed to remain effective after the potential split, rather than
assigning an unsupported fracture resistance to the original notch.

One bounded placement is 72 and 112 mm into the overlap from each shoulder,
at the member's depth center. Successive bolt spacings are 40, 45.51098 and
40 mm. For 9.525 mm bolts, these exceed 4D = 38.1 mm. The nearest end distance
of 72 mm exceeds 7D = 66.675 mm by 5.325 mm before construction tolerance.
Actual machining, spacing and washer access still have to match this placement.

A deliberately conservative preliminary single-bolt force envelope uses the
entire old left-knee axial force, 1165.904 N, as lateral demand in **each** tie,
and 1165.904 × 22.225 / 40 = 647.806 N as axial opening demand. Reusing the
existing pure `bolt_check` with two 44.45 mm bearing lengths, G = 0.5,
parallel bearing 5600 psi, Fyb = 45 ksi and the fixed maximum Ktheta reduction
produces the following illustrative results:

| Comparison | Result |
| --- | ---: |
| Single-bolt lateral reference, Mode IV | 1433.272 N |
| Lateral demand/reference | 0.81346 |
| Combined direct steel demand/reference | 0.14728 |
| Washer wood-bearing demand/reference | 0.36691 |
| Washer bending demand/reference | 0.49629 |

Hardware inputs for these numbers are the existing provisional Grade 5
3/8-inch assumptions: tensile area 0.0775 in², root diameter 0.298 inch,
steel yield 92 ksi with factor 2, two 25.4 mm OD × 11.1125 mm ID × 2.032 mm
washers, 33 ksi washer yield with factor 1.67, and 625 psi wood bearing.
These dimensions/material assumptions are not a delivered catalog guarantee.
The shorter full knee width is an 88.9 mm wood grip; the endpoint bolt length
must not be reused without checking nut seating and thread-bearing coverage.

**The envelope above is a feasibility calculation, not a complete splice
assessment.** P × 22.225 / 40 alone omits recovered transverse forces, applied
moments, torsion and contact-dependent prying. Its nominal 40 mm couple arm is
not an established contact resultant. It cannot be promoted to an opening
force bound merely because the direct steel and washer ratios are small.

The finite acceptance route is to analyze the two independent, physically
located timber segments and their four real bolts, with compression-only
contact across the split and no tensile or composite wood tie. Use recovered
individual bolt forces for all yield modes, steel, washer and applicable group
checks; require each ratio at most 1.0 and actual geometry acceptance. Check
each uninterrupted segment's net section and stability with its own eccentric
attachments and all bolt holes. Numerical equilibrium and contact gates must
pass. This supplies a defined load path even if the shoulder splits completely;
the force-only P × e / a arithmetic does not.

No reinforcement is selected or implemented by this assessment. The existing
unreinforced tab remains unsubstantiated. The complete-split splice route is
the specific next assessment for the proposed through-bolt reinforcement,
without another survey of brace variants or an invented wood tensile value.

## Selected resolution

The selected [unnotched splice detail](compact-splice-study.md) replaces the
notched brace with two separately modeled standard 2×6 pieces per side. Its
six current assembled cases pass the listed conditional criteria. The optional
notched-tab mesh helper remains development tooling; no executed native tab
run is claimed as evidence for the selected detail.
