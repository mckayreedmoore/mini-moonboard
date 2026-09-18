# Current response: resistance assumption audit

These comparisons explain the sensitivity of the shoe-free model's connection
results to resistance assumptions. They do not establish physical failure or
select different hardware. The current response calculation and its mesh and
joint assumptions must be considered alongside these values.

## Leg-bolt distribution and diameter

The existing single-fastener kernel returns a root-diameter lateral reference
before its inherited group factor. The inherited factor of 0.991516 assumes
four fasteners in a row with a 70 mm pitch. The current CAD instead uses two
bolts in each grain-parallel row, with 70 mm leg pitch and 50 mm rim pitch. The earlier 100 mm description
confused the historical spread-leg factory with the downstream revised drilling;
the response model uses the actual 70 × 50 mm axes. This documentation correction
does not change its solved forces or resistance values.
For the matching member axial stiffnesses in this reference calculation, the
NDS equation gives a factor of 1.0 for either two-fastener row.

The [AWC NDS commentary, C11.3.6](https://awc.org/wp-content/uploads/2021/10/AWC_NDS2018-withCommentary_20200827_AWCWebsite_Commentary.pdf)
explains that group action accounts for nonuniform row loading. Applying another
distribution reduction to individually resolved FE bolt forces is therefore an
additional conservative assumption, not an independent failure mechanism. This
is an interpretation of the calculation method, not a general waiver of NDS
group requirements. The postprocessor now displays the individual-force ratio
without a second group factor, alongside the historical reduced comparison.

The current joint has two solid 38.1 mm members. With the modeled 95.25 mm bolt,
25.4 mm reference thread length and 2.032 mm head-side washer, the nominal
threaded bearing in the nut-side member is 8.382 mm, or 22% of that member.
The historical pair of separate 19.05 mm plywood leg plies must not be used to
calculate this current solid-member fraction.

[2024 NDS Section 12.3.7.2](https://awc.org/wp-content/uploads/2026/08/AWC_NDS2024_withCommentary_20250328_WebsiteChapter-12-%E2%80%93-Dowel-type-fasteners.pdf)
permits nominal diameter for threaded full-body fasteners when threaded bearing
occupies no more than one quarter of the member bearing length. The locally
inspected primary PDF has SHA256
`5fc837523ff10acc097a162718700a9b4ba64e627d2b0023439146d42fe4ee2a`.
The nominal current stack satisfies this condition by only 1.143 mm. Bolt length
tolerance, thread length, thread runout and delivered wood thickness can change
that conclusion. The postprocessor consequently displays the 3/8-inch nominal
alternative conditionally, rather than declaring every selected bolt eligible.
A detailed threaded-bearing calculation is another permitted route.

For the first coarse A12 response with twice a 150 lb climber’s downward
force and an additional 300 N rearward force, bolt `lumber_leg_bolt_left_4` carries
1815.11 N laterally. Holding that same demand, wood bearing directions and
conservative reduction terms fixed gives:

| Resistance interpretation | Reference | Demand/reference |
| --- | ---: | ---: |
| 0.298-inch root, inherited group reduction | 722.34 N | 2.513 |
| 0.298-inch root, individually resolved force | 728.52 N | 2.491 |
| Conditional 0.375-inch nominal diameter, individually resolved force | 916.77 N | 1.980 |

Mode II governs these cases. Increasing the assumed bending yield strength from
45 to 90 ksi does not increase their Mode II reference. Consequently, neither
removing the small group reduction nor assuming a stronger bolt alone explains
away this particular response-model demand. This does not prove that the demand
is unavoidable in the installed joint. The force-transfer and compliance
assumptions remain part of the interpretation.

## SPAX geometry and reference

The current ordinary and added kicker attachments retain SPAX XFT08P-2000
screws, a nominal 50.8 mm head-top length and 23/32-inch panels. Gross nominal
wood penetration is therefore 32.54375 mm. The evaluated 1.24-inch thread length,
including the tip under the report's convention, is 31.496 mm and fits within
that nominal penetration by 1.04775 mm. Added kicker screws copy the existing
kicker product and seating geometry; the 52 mm frame translation changes neither
this penetration nor panel thickness.

The existing [documented TR12 calculation](round-structural-screw-calculation.md)
uses the published SPAX root diameter and bending strength, subtracts an ideal
head-cone zone from plywood lateral bearing, and deducts a tapered-tip allowance
from timber lateral bearing. Those conservative geometric assumptions produce
235.68 N lateral reference. They are not a manufacturer's measured capacity for
this entire connection. The direct source is [SPAX TER 2010-02](https://www.drjcertification.org/report/download/1936).
The nominal withdrawal reference is 133 lbf/in times 1.24 inches, or 733.60 N.
The corrected plywood head reference is 120 lbf, or 533.79 N, from the applicable
lower-density plywood column documented in the
[fastener applicability record](reinforced-fastener-applicability.json).

These are single-fastener ASD comparisons with dry, normal-temperature and
normal-duration factors taken as 1.0. They do not use an arbitrary bolt-group
multiplier or divide a total panel load equally among screws. Countersink depth,
actual seating and a gap would change the geometry premise; current sources do
not establish tolerances merely by rendering the nominal fastener. The owner's
accepted panel construction remains the design basis. A concentrated FE screw
force is a reason to examine the modeled transfer of hold load and panel
compliance, not an automatic instruction to replace the plywood or T-nuts.
