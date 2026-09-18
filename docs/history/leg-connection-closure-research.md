# Independent leg-connection completion research

This note supports the explicitly conditional leg assessment. It does not
represent a hardware substitution already made in CAD or installed, and does
not transfer qualification from the fabricated-shoe candidate to the selected
frame. The parent assessment must identify its actual geometry and assumptions.

## Smooth-shank bolt sensitivity

Using the existing four-bolt points, 4,071.702 N compression, dry Douglas
Fir–Larch bearing values, normal duration, and the existing conservative group
factor, the TR12 single-shear equations give:

| Bolt section through both wood members | Group reference at zero sagittal moment |
| --- | ---: |
| 0.298-inch thread-root section, 45 ksi bending yield | 3.306 kN |
| 0.375-inch smooth section, 45 ksi bending yield | 4.424 kN |

Smooth-shank lateral utilization is 0.9204. The separately applied sagittal
moment interval is approximately −19.812 to +19.812 N·m. At 6 N·m the ratio is
0.9423; at 12 N·m it is 0.9662. These moment values are explicit inputs, not
moments recovered from actual frame stiffness.

Mode II, involving wood bearing and dowel rotation, governs the smooth-shank
case. Raising bolt bending yield to 90 or 105 ksi does not raise this reference.
A higher bolt grade cannot substitute for keeping threads out of the effective
wood bearing lengths. The purchase and assembled stack must guarantee at least
76.2 mm of effective smooth shank through the two wood members. Standard bolt
length alone does not establish this; thread runout and washer placement matter.

The primary design basis is [AWC NDS 2024 Chapter 12](https://awc.org/wp-content/uploads/2026/08/AWC_NDS2024_withCommentary_20250328_WebsiteChapter-12-%E2%80%93-Dowel-type-fasteners.pdf),
with the existing TR12 implementation and source records in the timber report.
Table 12A uses full-body bolts with 45 ksi bending yield. The value remains an
explicit bolt material requirement; A307 identification alone does not prove it.

## Explicit prying and plate-washer screen

A deliberately conservative eccentricity allocation assigns the entire
38.1 mm separation between wood-member centroids to the bolt group's axial
couple. The signed elastic axial group is resolved using the full two-dimensional
Y/Z covariance matrix, preserving both components of the eccentric couple.
Compression represents contact between the wood faces; positive bolt forces
are then multiplied by an explicit prying factor of two. This is an assumed
design screen, not a proven upper bound from nonlinear contact analysis.

At 4,071.702 N, this produces 2,216.17 N maximum bolt tension. A proposed round
A36 plate washer, 38.1 mm diameter × 6.35 mm thick with an 11.1125 mm hole,
has 1,043.10 mm² net wood-bearing area. Pressure is 2.125 MPa, giving 0.493
utilization against the 625 psi dry DF-L perpendicular-bearing reference.

For plate bending, radial cantilever wedges are fixed at the inscribed
14.2875 mm head/nut bearing circle. The outer annulus carries uniform wood
pressure; beneficial circumferential plate action is omitted. For inner radius
`a`, overhang `c`, pressure `q` and thickness `t`:

```text
moment per unit inner circumference = q (c²/2 + c³/(3a))
bending stress = 6 moment / t²
```

Stress is 47.31 MPa, versus the explicit A36 service bending criterion
`36 ksi / 1.67 = 148.63 MPa`, ratio 0.318. This screen does not include bolt
preload, establishes no tightening torque, and does not replace the bolt's
own tensile/combined-action check. Compression contact and snug, flat plates
are required assumptions.

## Foot and joint moment limitation

No-slip alone does not determine the horizontal foot reaction. With forces
on a leg, sagittal equilibrium contains

```text
M_top = (Y_foot − Y_top) R_z + Z_top R_y + gravity term
```

A nominal two-force model chooses the reaction direction to cancel the first
two terms. It is a conventional modeling assumption, not a consequence of
having four bolts or a no-slip foot. Allowing arbitrary foot reaction directions
would admit much greater joint moments. Even retaining an axial resultant but
moving the foot pressure centroid across the full approximately 145 mm foot
length would generate moments far above the ±19.8 N·m bolt interval.

A conditional design can explicitly adopt nominally pinned sagittal behavior
and a centered foot resultant, then state the numerical moment sensitivity.
It cannot claim that the calculation has independently verified those assumed
restraints. A connection designed to act as a physical pin would instead need
an actual revised detail. The current calculation also does not resolve
perpendicular-grain splitting in the receiving rim: passing bolt edge and end
distances is not that check. [AWC's connection design guidance](https://web-media.awc.org/wp-content/uploads/2022/01/17210413/AWC-2018-Manual-1810.pdf)
identifies avoiding cross-grain tension as a connection design concern.

## Reproduction

`fea/leg_smooth_bolt_check.py` contains the smooth-shank lateral group, moment
interval, explicit prying screen, and radial plate check. Its small focused
tests verify force/moment recovery, criterion crossings, prying amplification
both prying-couple components, and plate thickness scaling. They verify arithmetic and implementation, not
installed joint behavior.
