# PB01 short block: signed oblique two-bolt decomposition

Status: **source-bound diagnostic force algebra, not a capacity calculation,
joint utilization, selected layout, or drilling release.** Run
`PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m
scripts.simple_pb01_short_oblique_distribution` from the repository root. It
prints JSON and writes no files.

The script calls the existing [short tension-only archive reader and
comparison](simple-pb01-short-tension-component-comparison.md). That reader
verifies both retained ZIP digests, report and final-cycle sources, signed
connector ownership, equilibrium, and the comparison digest. Each case is a
numerically accepted 152.4-mm `quarter_short` hybrid with **23 legacy
ML24Z/SDS proxy stations**. These are provisional model forces, not qualified
full-V4 joint demands. The script derives each pair's pitch and local axes
from archived bolt points and installation axes; force values are read afresh
from the archived signed host-side vectors. Small pose-coordinate rounding is
removed by orthogonalizing the local axes, and any remaining out-of-plane
lateral force is checked.

The upright and rail are **separate serial interfaces**, with two bolts per
face. On each host, `along` points from bolt 1 to bolt 2; `across` is the
perpendicular in-plane direction. With signed lateral vectors `f1`, `f2`
and recorded pitch `p`, define

```text
R = f1 + f2                       pair resultant
H = (f2 - f1)/2                  pair half-difference
f1 = R/2 - H;  f2 = R/2 + H      exact force reconstruction
M_bolts = p H_across             signed bolt couple about pair midpoint
L_envelope = |f1| + |f2|         no-cancellation demand indicator
```

`M_bolts` contains only the *lateral bolt forces*. It excludes face-contact
moments and is not the complete interface moment. `H_along` records unequal
along-row forces but produces no in-plane couple about the pair midpoint.
The script checks exact in-plane reconstruction to numerical precision.

Rounded script output (N; moment N·mm):

| Case / face | Pitch mm | R along / across | H along / across | Bolt couple | L envelope |
| --- | ---: | ---: | ---: | ---: | ---: |
| A12-left / upright | 45.000 | -6.708 / -7.417 | -0.190 / -12.565 | -565.442 | 26.060 |
| A12-left / rail | 40.000 | +14.565 / +1.060 | +0.007 / -10.431 | -417.240 | 25.451 |
| K12-right / upright | 45.000 | -11.471 / +4.798 | -0.450 / -14.110 | -634.950 | 30.579 |
| K12-right / rail | 40.000 | +62.831 / +5.826 | -0.247 / -13.621 | -544.840 | 68.676 |

For a subsequent conservative strength screen, retain each **simultaneous**
bolt's complete lateral vector and axial force, plus face-contact actions.
As a concentration envelope, the sum of the two lateral magnitudes on one
face may be compared against **one fully adjusted, specified single-bolt
resistance**, with no cancellation or two-bolt capacity credit. It is a
conditional screen of these modeled forces, not a verified physical upper
bound: the provisional spring/contact law controls their distribution.
Evaluate direction-specific dowel bearing in each wood member, applicable
single-shear yield modes, adjustments and geometry, bolt/washer axial action,
and local wood stresses including bored sections, splitting and tear-out.
The rail r1 modeled host axial tensions are 20.495 N (A12-left) and
19.668 N (K12-right); they are separate from the lateral envelope.

The actual forces are oblique to both pair lines. Neither the measured pitch
nor the decomposition supplies an aligned-row group factor `C_g`, a final
geometry factor `C_delta`, or a complete resistance. The output deliberately
leaves adjusted resistance, group utilization, joint utilization and design
pass `null`, with drilling release false. The 2024 NDS provisions for row
alignment, dowel bearing, geometry, multiple-fastener loading and local
stresses are in [AWC Chapter 11](https://web-media.awc.org/wp-content/uploads/2021/12/17205958/AWC_NDS2024_20250124_AWCWebsite_Chapter11.pdf),
[AWC Chapter 12](https://awc.org/wp-content/uploads/2026/08/AWC_NDS2024_withCommentary_20250328_WebsiteChapter-12-%E2%80%93-Dowel-type-fasteners.pdf),
and the [2024 NDS errata](https://awc.org/wp-content/uploads/2026/03/2024-NDS-Errata-and-Addenda-03.23.26.pdf).
