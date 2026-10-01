# BG003 middle-member half-zone cut feasibility — attempt01

**Finding:** The 88.9 mm `base_side_left` thickness can be divided on paper
into two 44.45 mm lengths. That geometric partition does not establish a
statically admissible zero-shear, zero-moment center cut, and it does not
support an independent-plane lower-bound capacity check. A source-supported
method or a verified stress field is still needed for the coupled bolt and
wood response.

## Bound case and geometry

This screen is bound to the final full-load increment (`load_factor = 1.0`)
of the authenticated A1-rear response report. The source report is a
conditional numerical demand report, not joint acceptance. Its SHA-256 is
`2b498383b319aeb31e74c3b329e0758330b8b39d0a8e1b4788437db06453bfce`.
The existing modeled-profile query is pinned at SHA-256
`5c820231ac4434e896ee708c72128672424ff158b3ee4458197cdadc1a4b0854`.
The reproducible [`screen.json`](screen.json) contains the exact forces,
resultants, force ratios, vector angles, axial ties and profile intervals.

The modeled middle-member interval is `[39.751, 128.651] mm` along the bolt,
or 88.9 mm total. A proposed split gives 44.45 mm to each plane and makes the
two *assigned intervals* abut at the center. It does not create a material
seam: the receiver is one continuous timber member and the bolt is one
continuous through-fastener. The modeled bore/profile has no feature that
delimits each plane's wood-bearing field to its assigned half. The NDS
three-member route instead uses the middle member's full `ℓm = 88.9 mm` as
one bearing length; treating this one member as two half-depth main members is
not the standard connection idealization. Therefore “nonoverlapping bearing
zones” is an additional stress-distribution assumption, not a geometry fact.

At full A1-rear load, the side-1 outer-plane actions have magnitudes 137.900 N
and 102.535 N, a 1.345 ratio and a 42.545° angle. The side-2 actions are
59.370 N and 58.865 N, a 1.009 ratio and a 118.179° angle. Their concurrent
bolt-axis tie actions are 21.794 N and 49.669 N. The lateral vectors are the
integrated actions at the two interfaces from the case-bound exporter; they
are not through-thickness wood-bearing tractions or a recovered bolt shear
and moment diagram.

## Why zero shear and zero moment do not follow from the split

Take one proposed half-zone of length `L = 44.45 mm`, with `s = 0` at its
interface plane and `s = L` at the center cut. Let `V` be that plane's
transverse action on the dowel. In the simple one-sided-bearing construction,
the wood reaction over this half must have resultant `B = −V` for the cut
shear to be zero. If its bearing resultant acts at centroid `s̄`, its moment
about the center cut has magnitude

```text
|M_center| = |V| · s̄
```

because the plane force acts at `s = 0`, while the balancing bearing resultant
acts at `s = s̄`. For a finite one-sided bearing zone, `s̄ > 0`, so a nonzero
`V` leaves nonzero bending moment at the center. A zero moment would require
the reaction to be co-located with the interface force or an additional
opposing contact couple/self-equilibrated pressure field. Neither is
specified by the geometry or recovered by the response report. The recorded
per-plane vectors also differ in direction, so one scalar distribution cannot
serve both halves; each vector and its first moment must be equilibrated.

This does not prove that no conceivable three-dimensional contact field can
produce a zero center moment. It shows that the proposed geometric split alone
does not provide one. Any more complex pressure field would need to satisfy
equilibrium and local wood/bolt yield limits simultaneously, and no such
field or validated lower-bound procedure is present here. In particular,
geometrically nonoverlapping assigned lengths do not prove that stress fields
in adjacent regions of the same wood member or the same dowel act
independently.

The axial seat ties are also simultaneous. Even if a lateral stress
construction could make the transverse shear and moment zero at the center,
the same continuous bolt still carries axial tension through that section.
A lateral-only split would not check combined bolt tension and bending,
thread/root occupancy, or axial washer-seat bearing.

## Source applicability

The current NDS-2024 Chapter 12 basis checked in the prior BG003 method packet
provides the symmetric three-member yield route; its unequal-side-length rule
uses the shorter side bearing length. The multiple-shear procedure is for
four or more members, and does not provide a vector interaction rule for this
three-member stack. The older NDS-2018 commentary is explicit that its
asymmetric three-member simplification assumes equivalent loading of each
side member and that a different distribution may need more complex analysis.
That historical commentary is corroborating context only, not the current
design basis. See the [official 2024 NDS Chapter 12
PDF](https://awc.org/wp-content/uploads/2026/08/AWC_NDS2024_withCommentary_20250328_WebsiteChapter-12-%E2%80%93-Dowel-type-fasteners.pdf)
and [official 2018 NDS Commentary, C12.3.8–C12.3.9](https://awc.org/wp-content/uploads/2021/10/AWC_NDS2018-withCommentary_20200827_AWCWebsite_Commentary.pdf).

The [2026 AWC TR-12](https://awc.org/wp-content/uploads/2026/06/TR-12_2026_formatted.V3.pdf)
§1.2 describes its yield equations as lateral values for single-fastener
connections. Section 1.6 permits treating two-ply members as one member only
when equal-thickness plies are in contact and receive the same load from the
same direction through a common element. That rule does not authorize
subdividing one solid 88.9 mm member into two independent effective members
under these unequal, non-collinear plane actions. TR-12’s equations account
for dowel bearing and fastener moment in their stated connection models; they
do not establish the proposed zero-moment midpoint boundary condition.

## Result and minimum next evidence

The current proposal is **not justified as a simultaneous lower-bound
screen**. The exact missing engineering object is a statically admissible
bolt/wood force field (or a validated conservative method that bounds one)
over both interfaces and the full 88.9 mm middle member, with continuous bolt
shear and bending moment, the actual two transverse vectors, and axial tie
tension acting concurrently. It would also need actual or explicitly
conditional bolt section/thread and wood bearing/yield properties to apply
the interaction constraints.

This finding does not require a detailed FEA specifically; a verified
analytical limit-analysis method could answer it. It does mean that assigning
44.45 mm to each plane and declaring zero internal shear/moment at the
midplane is not itself that method. No plane or bolt capacities are added,
independent, or accepted in this packet.

Reproduce the source-bound arithmetic from the repository root:

```sh
python3 docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/current-bg003-middle-zone-cut-feasibility-attempt01/screen.py
```

The script verifies both input hashes, reads only the pinned response and
profile query, checks each middle-member force against its two interface
actions, and writes `screen.json`. It does not run a native solver, alter a
model, compute capacity, or make an acceptance decision.
