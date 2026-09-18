# Completed conservative assessment of the support legs

> Follow-up completed: [larger bolts and wider patterns](leg-bolt-pattern-decision.md).
> No candidate passed the tested placement and lateral checks with the single
> 2×6 members retained.

**Decision: the existing leg connection does not meet the selected assessment
case. The single 2×6 member does.** A longer-bolt and plate-washer revision was
also calculated and modeled; it fits, but does not meet the connection bending
case. It is not selected for construction.

This completes a finite pass/fail assessment under the assumptions below. It
is a negative connection result, not a completed passing redesign or a physical
breaking-load prediction. Owner confirmation can approve the design basis; it
cannot change a failed calculation into a passing one.

## Assumptions selected for confirmation

| Item | Assessment basis |
| --- | --- |
| Climber | 250 lb; twice body weight downward, plus 300 N rearward horizontal force |
| Hold | Current hold positions, up to 100 mm projection; use the governing load position |
| Dead load | Current modeled assembly, plus 25 kg equipment and 2 kg hardware allowance |
| Load sharing | Assign all calculated rear-support compression to one leg |
| Timber | Dry, unincised US Douglas Fir–Larch No. 2; actual 38.1 × 139.7 mm leg |
| Leg span | 1,612 mm between the foot center and bolt-group center |
| Feet | No sliding; full rectangular face contact with nonnegative linear pressure |
| Pressure location | Both ends of the middle third of the foot length, allowing finite triangular pressure rather than requiring uniform pressure |
| Local force model | Force delivered along the leg axis; calculate the required joint moment from equilibrium at each foot-pressure location |
| Scope | Support legs and their integral connection; owner-specified panel construction remains the design basis |

The foot is 144.68 mm long in the fore-aft direction. Linear, nonnegative
pressure over its entire face permits its resultant to lie up to 24.11 mm from
center. These are explicit design assumptions, not measured contact behavior.
The axial force is recalculated using the actual pressure-resultant lever arm
for each case. The existing four-bolt joint is not silently treated as a
moment-free pin. No floor-friction coefficient or test is introduced.

The local calculation adds the leg's own gravity after the global calculation
already included it. This small intentional duplicate allowance is conservative
for the reported negative comparison. The member check also carries the full
joint moment throughout its length in addition to the existing gravity bending,
net-section and weak-axis eccentricity allowances.

## Results

A demand/reference ratio at or below 1 meets the individual comparison.

| Check | Worst result | Outcome |
| --- | ---: | --- |
| Compression assigned to one leg | 4.154 kN | Input to the following checks |
| Joint sagittal moment | −85.1 to +108.3 N·m | Calculated from the two full-contact pressure cases |
| Single 2×6 compression/buckling/biaxial bending | 0.932 | Passes this member comparison |
| Existing thread-root bolt reference | 1.918 | Does not pass |
| Proposed smooth-shank bolt reference | 1.520 | Does not pass |
| Supplemental EC5 rim splitting | 0.851 | Passes this supplemental comparison |

Existing bolt end, edge and row-spacing checks also pass. Splitting uses the
solid-timber expression documented in the [primary-source splitting note](leg-splitting-research.md),
with its own EC5 factors and an additional 1.5 multiplier on the sum of absolute
cross-grain bolt forces. It is separate from the NDS allowable-stress checks;
no NDS cross-grain tensile strength has been invented.

A more extreme sensitivity allowing pressure to approach the foot edges also
fails, but **the decision above does not rely on that sensitivity**. The
full-face pressure cases already fail the connection check while the member
passes. The result does not establish that actual use produces these contact
states, nor that exceeding a reference value predicts collapse.

## Investigated hardware revision

The review candidate replaces the eight leg bolts with 3/8-16 × 5-inch Grade 5
bolts, two 38.1 mm diameter × 6.35 mm A36 plate washers per bolt, a 19.05 mm
nut-side steel spacer, and a matching nut. It retains the existing wood holes
and single 2×6 legs. Full smooth shank through the wood is an explicit receiving
requirement, supported by a checked dimensional acceptance window.

All 48 modeled hardware components clear wood and neighboring hardware; all
16 plate washers have full wood-face support. The additional modeled hardware
mass is 1.213 kg, below the 2 kg allowance. The drawing and exact dimensional
margins are in the [hardware review](leg-smooth-hardware-review/README.md), with
[a standalone STEP model](leg-smooth-hardware-review/hardware.step).

The separate lap/prying screen balances both axial bolt-group moment components
and applies an explicit 2× amplification. At the preceding 4.072 kN axial
comparison, the proposed plate washers pass wood bearing and plate bending.
That amplification is an assumed screen, not a demonstrated universal prying
bound. No combined-action bolt qualification is claimed: passing such a check
could not rescue the failed lateral connection criterion above. The hardware
revision is therefore rejected as a complete solution, despite passing fit and
individual washer screens.

## What this settles

Keep the single 2×6 size as the development basis for this selected member
case. Do not represent either the existing four-bolt connection or the isolated
hardware revision as verified for construction. A passing design would require
a distinct connection/load-path revision, such as a properly designed physical
hinge, followed by its own calculations and fabrication detail. That revision
has not been designed here; a nominal-pin assumption does not install a hinge.

There is no further missing scalar assumption needed to decide this assessed
case: it fails its connection criterion. Replacing that failed result with a
passing design is new implementation work, not another confirmation of the
same bolt-count calculation.

## Evidence and validation

- [Reproducible assessment](../fea/leg_completion_assessment.py)
- [Current result and source hashes](../fea/results/leg-completion-assessment-v2.json)
- [Smooth-bolt and washer equations](../fea/leg_smooth_bolt_check.py)
- [Independent connection review](leg-connection-closure-research.md)

The numerical checks use the primary NDS/TR12 sources recorded in the existing
[timber notes](reinforced-timber-resistance.md) and the separate Swedish Wood
EC5 sources recorded in the splitting note. Independent review checked moment
signs and the pressure-location lever-arm correction. Tests check load and
moment equilibrium, member behavior, splitting-force cancellation, full axial
bolt-group moment recovery, and the candidate hardware geometry. These verify
the calculations and CAD; they do not measure installed behavior.
