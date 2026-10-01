# BG003 piecewise bearing profile feasibility — attempt01

**Finding:** A constructed, sign-reversing line-bearing field gives a statically
admissible lateral fastener diagram for both source cases and both BG003 bolts.
Each bolt has four contiguous profile zones: the 38.1 mm spine, two 44.45 mm
halves of the 88.9 mm middle member, and the 88.9 mm inner block. The outer
profiles use the opposite force resultant from their adjoining middle profiles.
The conditional diagram has zero lateral shear and bending moment at the two
outboard receiver faces and at the middle center cut, while preserving each
source interface force and moment about its actual datum.

This is an explicit static field, not a verified compatible pressure field or
a strength result. The continuous fastener still carries the source axial tie
force through the middle cut. No capacity, NDS/TR-12 resistance, lower-bound
strength, or connection acceptance is established.

This construction shows that the zero-middle-cut result is not statically
impossible in general; the earlier one-sided reaction-centroid argument only
rules out that restricted pressure model. Geometry alone still does not show
that the constructed field occurs in the actual connection.

## Profile and equilibrium

For each receiver segment of length `ell`, let `R` be the selected signed line
reaction resultant on the bolt and `a = ell / sqrt(2)`. The construction is

```text
q(s) = +q0 * R_hat     for 0 <= s <= a
q(s) = -q0 * R_hat     for a < s <= ell
q0 = |R| / [ell * (sqrt(2) - 1)]
```

The force and first-moment identities are

```text
integral(q ds) = q0 * (2a - ell) * R_hat = R
integral(s cross q ds) = 0.5 * q0 * (2a^2 - ell^2) = 0
```

At each BG003 plane, the source vector `F` is the connector action on the
outer wood receiver. The opposite point force would act on the fastener. The
middle-wood profile has resultant `+F` on the fastener; its equal-and-opposite
force on the wood preserves the source middle-side action. The outer-wood
profile has resultant `-F` on the fastener and preserves the source outer-side
action. The two profiles have equal and opposite equivalent force resultants
at the reported interface and zero local couple. The line-load
profiles replace the idealized point actions; they are not added on top of
them.

For one idealized segment, the fastener shear starts at magnitude `|R|` at
the interface and returns to zero at its remote end. Its conditional maximum
bending moment is `|R| * ell * (sqrt(2) - 1) / 2`, at distance
`ell * (sqrt(2) - 1)` from the interface. The machine-readable report gives
the global shear and moment vectors as well as magnitudes. These are maxima
of the constructed profile diagram, not conservative bounds on an actual
bolt response.

The four axial intervals for either bolt are adjacent and nonoverlapping:

| Receiver zone | Modeled underhead interval (mm) | Length (mm) |
| --- | ---: | ---: |
| `knee_outer_left_spine` | 1.651–39.751 | 38.1 |
| `base_side_left`, plane 37/39 side | 39.751–84.201 | 44.45 |
| `base_side_left`, plane 38/40 side | 84.201–128.651 | 44.45 |
| `knee_outer_left_inner_frame_block` | 128.651–217.551 | 88.9 |

The middle sign switches are at underhead stations 71.182 mm and 97.220 mm.
The outer-profile switches are computed separately from their 38.1 mm and
88.9 mm segment lengths. Interface forces are at global X = -1219.2 mm for
planes 37/39 and -1130.3 mm for planes 38/40; each lies on its reported bolt
axis. The source point actions have no intrinsic interface couple. Their
nonzero moments about the shared shaft datum arise from the axial spacing
between interfaces and are retained by transporting each point resultant.

The report reconstructs every reported per-member force and moment from the
source point actions with zero component error at the serialized precision.
Replacing each interface point action by its matching profile preserves that
member wrench. The profiles also give continuous interface shear and moment,
zero lateral V/M at both outboard modeled receiver faces, and zero lateral V/M
on both sides of the middle cut. This answers the prior geometric concern for
one explicitly constructed field; it does not show that timber/bolt contact
will adopt this field.

## Conditional full-load results

`q_outer` is the maximum line reaction in the adjacent spine or inner-block
profile; `q_middle` is the maximum in the 44.45 mm middle half. Both are in
N/mm. `M_outer` and `M_middle` are conditional fastener bending-moment maxima
in Nmm. `V` is the conditional maximum resultant shear in N.

| Case | Bolt | Plane | `|F|` (N) | `q_outer` | `q_middle` | `M_outer` | `M_middle` |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: |
| A12-rear | 1 | 37 | 483.948 | 30.665 | 26.285 | 3818.718 | 4455.172 |
| A12-rear | 1 | 38 | 65.913 | 1.790 | 3.580 | 1213.579 | 606.789 |
| A12-rear | 2 | 39 | 239.230 | 15.159 | 12.993 | 1887.709 | 2202.327 |
| A12-rear | 2 | 40 | 86.983 | 2.362 | 4.724 | 1601.518 | 800.759 |
| A1-rear | 1 | 37 | 137.900 | 8.738 | 7.490 | 1088.136 | 1269.492 |
| A1-rear | 1 | 38 | 102.535 | 2.784 | 5.569 | 1887.848 | 943.924 |
| A1-rear | 2 | 39 | 59.370 | 3.762 | 3.225 | 468.475 | 546.555 |
| A1-rear | 2 | 40 | 58.865 | 1.599 | 3.197 | 1083.803 | 541.901 |

For the complete four-zone profile, the full-load conditional maxima are:

| Case | Bolt | Peak line reaction (N/mm) | Peak V (N) | Governing M (Nmm) | Governing M segment | Axial tie at middle cut (N) |
| --- | --- | ---: | ---: | ---: | --- | ---: |
| A12-rear | 1 | 30.665 | 483.948 | 4455.172 | plane 37, middle | 95.967 |
| A12-rear | 2 | 15.159 | 239.230 | 2202.327 | plane 39, middle | 43.508 |
| A1-rear | 1 | 8.738 | 137.900 | 1887.848 | plane 38, inner block | 21.794 |
| A1-rear | 2 | 3.762 | 59.370 | 1083.803 | plane 40, inner block | 49.669 |

The source planes are materially unequal and non-collinear. At full load, the
plane-force magnitude ratios / included angles are 7.342 / 37.973° and 2.750 /
119.347° for A12-rear bolts 1 and 2; they are 1.345 / 42.545° and 1.009 /
118.179° for A1-rear. The independent per-plane profiles do not require a
single common lateral direction. All seven response increments for both cases
are included in `profile-check.json`, with source response gates and five-body
balance status pinned and checked.

## Geometry and limits

The geometry packet gives zero modeled interface interval gaps, but it does
not verify an active bearing law, physical head-to-nut order, or delivered
contact. The modeled shaft diameter is 6.35 mm and the profile rays begin at
3.75 mm from the shaft center, a 0.575 mm modeled radial bore clearance. The
modeled outer-seat tie points span 215.9 mm and the modeled fastener shaft
length is 241.3 mm; the 25.4 mm difference does not establish delivered grip,
washer placement, shank length, or thread position. The terminal zero V/M
conditions are imposed by this static field; actual washer/head/nut transverse
restraint is not assessed.

The sign reversal is interpreted as compressive bearing on opposite bore
flanks, not tensile pressure. Radial pressure is assumed aligned with the
resultant, so no friction or tangential force is introduced. Simultaneous
opposite-flank engagement, compatibility with bolt and wood deformation,
contact sequencing, pressure footprint, timber constitutive behavior, and
splitting/shear-plug limits remain unproved. The reported line reactions are
N/mm; absent a bearing-width/contact law they are not converted to N/mm²
stress.

The [AWC TR-12](https://web-media.awc.org/wp-content/uploads/2021/12/17210714/AWC-TR12-1510.pdf)
equations use specified ideally plastic bearing modes and retain their stated
failure and adjustment conditions. This custom distribution is not one of
those equations and does not produce `Z`, `Rd`, or an adjusted resistance. It
is not an NDS lower-bound proof. Zero shear/moment at a cut does not check the
nonzero axial tie interaction, bolt root/thread section, washer-seat bearing,
wood bearing strength, splitting, or complete-joint compatibility. No native
solve, geometry change, optimization, or strength acceptance is part of this
packet.

## Reproduction and source pins

From the repository root:

```sh
python3 docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/current-bg003-piecewise-bearing-profile-feasibility-attempt01/profile_check.py
```

The stdlib-only producer verifies the two passed case-bound demand reports,
the prior cut screen, transfer geometry, bolt inventory, profile query, and
all source hashes embedded in that query. It enumerates 14 increments and 112
profile-segment states, reconstructs 28 per-bolt source wrenches, checks the
force and first-moment identities, verifies the four contiguous intervals,
and writes deterministic JSON. It launches no native run and calculates no
resistance.

Key source pins are A12-rear report
`812a62fa3cd96a8983649c84a8c78a8d176d639465c887b11d1827a3f8f1ee17`, A1-rear
report `2b498383b319aeb31e74c3b329e0758330b8b39d0a8e1b4788437db06453bfce`,
profile query `5c820231ac4434e896ee708c72128672424ff158b3ee4458197cdadc1a4b0854`,
and prior cut screen `4dbf472e7557c5828601e6545fa162b436dda32a8f12e0346f703790625f3324`.
The complete pin set and maximum residuals are recorded in `profile-check.json`.
