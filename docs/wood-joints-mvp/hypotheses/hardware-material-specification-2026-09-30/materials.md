# Conditional timber material inputs

**Status:** source-backed calculation inputs for the reviewed
`led-clearance-2x6-runner-seated-blocks-v1` geometry. These scenarios do not
identify delivered stock, assign a grade, calculate a member or joint
resistance, adopt a splitting method, or accept a connection.

The explicit scenario is Douglas Fir-Larch (DF-L), No. 2. It can be used for
conditional arithmetic now; species, grade, moisture/service condition,
physical grain, and growth-ring orientation have not been observed. The
machine-readable per-member inputs and pinned hashes are in
[`material-inputs.json`](material-inputs.json).

## Table route and conditional base values

The current inventory has 20 frame timbers and 24 connector blocks. The 16
nominal 2×6 frame members, four nominal 4×6 frame members, 18 full-section
4×4 blocks, and two full-section 2×6 spine blocks are represented by the
visually graded dimension-lumber route in NDS Supplement Table 4A (2–4 in.
thick). None is a Table 4D timber (5×5 in. and larger). The four remaining
blocks are cross-section rips from 4×6 stock and are treated separately below.

Table 4A, printed page 34, gives this conditional DF-L/DF/western-larch No. 2
row for size classification “2 in. & wider.” I visually checked the row in the
source PDF; it is distinct from the adjacent No. 1 and No. 3 rows.

| Reference property | Conditional No. 2 input | Units |
| --- | ---: | --- |
| Bending, `Fb` | 900 | psi |
| Tension parallel to grain, `Ft` | 575 | psi |
| Shear parallel to grain, `Fv` | 180 | psi |
| Compression perpendicular to grain, `Fc⊥` | 625 | psi |
| Compression parallel to grain, `Fc` | 1,350 | psi |
| Modulus of elasticity, `E` | 1,600,000 | psi |
| Minimum modulus of elasticity, `Emin` | 580,000 | psi |
| Specific gravity, `G` | 0.50 | dimensionless |

The stress values are respectively 6.205, 3.964, 1.241, 4.309, and 9.308
MPa; `E` is 11,031.612 MPa and `Emin` is 3,998.959 MPa. Table 4A states
normal load-duration and dry-service reference conditions. This `E` matches
the DF-L No. 2 elastic input already used in
[`current-material-scenarios.md`](../../current-material-scenarios.md).

`G=0.50` is also the DF-L assigned specific gravity in NDS Table 12.3.3A,
printed page 94, and is the conditional dowel-bearing input below. Table 4A
values are not observations of any individual member.

## Standard-section factor inputs

Table 4A adjustment factors are on printed page 32. `CF` modifies only `Fb`,
`Ft`, and `Fc`; it does not modify `Fv`, `Fc⊥`, `E`, `Emin`, or `G`.
`Cfu` is an additional bending-only factor when a member is used flatwise.
Choose factors by the member's actual check and orientation rather than
applying a blanket adjusted-property row.

| Conditional nominal section | Count | Table 4A size category | `CF` for (`Fb`, `Ft`, `Fc`) | `Cfu` if flatwise |
| --- | ---: | --- | --- | --- |
| 2×6 | 18 | 6-in. width; 2-in. thickness | (1.30, 1.30, 1.10) | 1.15 |
| 4×6 | 4 | 6-in. width; 4-in. thickness | (1.30, 1.30, 1.10) | 1.05 |
| 4×4 | 18 | 4-in. width; 4-in. thickness | (1.50, 1.50, 1.15) | 1.00 |

For checks that require only the Table 4A size-factor arithmetic, the
conditional `Fb × CF`, `Ft × CF`, and `Fc × CF` values are:

| Conditional section | `Fb × CF` | `Ft × CF` | `Fc × CF` | Units |
| --- | ---: | ---: | ---: | --- |
| 2×6 or 4×6 | 1,170 | 747.5 | 1,485 | psi |
| 4×4 | 1,350 | 862.5 | 1,552.5 | psi |

These rows contain `CF` only. If bending is flatwise, separately multiply
the size-adjusted `Fb` by its applicable `Cfu`; edgewise `Cfu` is 1.0.
`Cr=1.15` may apply to `Fb` only when all Table 4A repetitive-member
conditions hold (qualifying member use, spacing, count, and load distribution).
No `Cr` credit is assigned here.

If moisture content exceeds 19% for an extended period, Table 4A lists
`CM=(0.85, 1.0, 0.97, 0.67, 0.80, 0.90)` for (`Fb`, `Ft`, `Fv`, `Fc⊥`,
`Fc`, `E/Emin`), subject to its `Fb×CF ≤ 1,150 psi` and `Fc×CF ≤ 750 psi`
exceptions. The standard-section conditional products above exceed both
exception thresholds. No wet-service condition is assigned. Duration,
temperature, treatment/incising, bending stability, and compression stability
factors (`CD`, `Ct`, `Ci`, `CL`, and `CP`) remain check-specific inputs; they
do not prevent use of the named base-row scenario for arithmetic.

No Table 4A strength `CF` was included in the historic corner comparison
inputs: the `Fc⊥=625 psi` washer-seat reference is unaffected by `CF`, and the
existing individual-bolt `Fe` references are based on specific gravity,
fastener diameter, and load-to-grain angle rather than Table 4A strength
factors. The old screen also did not apply `CF` to `E` or `Emin`. Do not
multiply those historical references by `CF` again. Where new checks require
`Fb`, `Ft`, or `Fc`, apply the appropriate standard-section factor once to
the unadjusted base row, then add only other applicable factors.

## Four cross-section-ripped blocks

PS 20-25 §7.3.7 states that ripping, resawing, or surfacing remanufactured
lumber negates the original grade, grade mark, and design values. Its Table 3
4×6 dressed-dry dimensions are 3.5×5.5 in.; both proposed rip sections differ
from that standard size. Table 4A's `CF` grid does not identify a nominal
3.3-in. or 3.5-in. thickness class for these final sections, so code `CF`
remains unassigned. No grade or property follows from the original 4×6 stock.

The following rows deliberately provide useful final-section scenarios for
conditional calculations before receiving. `CFstudy=1.0` is an explicit
no-size-increase study assumption only. It is **not** an NDS-assigned factor,
a final-size category, a lower-bound property, a post-rip grade, or a transfer
of source-board values. The hypothetical No. 2 scenario applies only if the
analyst elects to calculate that case; post-rip grade remains unknown.

| Conditional final-section study case | Count / IDs | Proposed final cross section | Grain scenario | Arithmetic input |
| --- | --- | --- | --- | --- |
| Center principal cleats | 2: `center_principal_cleat_left/right` | 83.9 × 139.7 mm | `+Z` | DF-L No. 2 base row above; `CFstudy=1.0`, so `Fb=900`, `Ft=575`, `Fv=180`, `Fc⊥=625`, `Fc=1,350 psi`, `E=1,600,000 psi`, `Emin=580,000 psi`, `G=0.50` |
| Outer inner-frame blocks | 2: `knee_outer_left/right_inner_frame_block` | 88.9 × 133.35 mm | `+Z` | Same explicit hypothetical No. 2 row and `CFstudy=1.0` values |

These are arithmetic inputs, not claims about the four pieces. PS 20-25
§§6.1.6 and 8.1.4 address specified nonstandard sizes and inspection under
applicable certified grading rules. A future grade or design-value claim for
any ripped piece must be tied to that final piece and supported final-section
basis; this record does not make such an assignment or require receiving data
before conditional analysis.

## Primary corner members and grain applicability

The listed unit vectors are proposed longitudinal material axes from the
current frame/block maps. They are not board-grain measurements. Sign reversal
is the same longitudinal axis; physical radial/tangential growth-ring
orientation is unresolved. The block map retains two R/T assignments where
needed for elastic sensitivity. The complete 20-frame and 24-block mapping is
in [`material-inputs.json`](material-inputs.json), pinned to the source maps
listed below. The [corner resistance register](../mvp-acceleration-2026-09-28/current-corner-complete-resistance-register-attempt01/README.md)
is a navigation/context reference for the BG group labels only, not a pinned
material-data source.

| Corner | Member | Conditional section/property case | Proposed longitudinal grain, global XYZ |
| --- | --- | --- | --- |
| BG001 post/spine | `base_post_outer_left` | 2×6, No. 2 scenario | `(0, 0, +1)` |
| BG001 post/spine | `knee_outer_left_spine` | 2×6, No. 2 scenario | `(0, 0, +1)` |
| BG003 spine/side/block | `knee_outer_left_spine` | 2×6, No. 2 scenario | `(0, 0, +1)` |
| BG003 spine/side/block | `base_side_left` | 4×6, No. 2 scenario | `(0, 0.642788, 0.766044)` |
| BG003 spine/side/block | `knee_outer_left_inner_frame_block` | Ripped-block study case; grade unassigned | `(0, 0, +1)` |
| BG045 block/header | `knee_outer_left_inner_frame_block` | Same ripped-block study case | `(0, 0, +1)` |
| BG045 block/header | `base_header` | 2×6, No. 2 scenario | `(+1, 0, 0)` |

For lateral embedment, compute `θ` separately for the direction of load in
each wood receiver and that receiver's proposed longitudinal grain. A bolt
axis or grain vector alone does not assign every member's bearing direction.
At BG045, the source scenario puts the inner-block washer normal parallel to
the proposed block grain, while the header washer normal is perpendicular to
header grain; `Fc⊥` therefore cannot be copied to both seats. If a fastener of
`D ≥ 1/4 in.` is in the end grain of the NDS main member and its axis is
parallel to fibers, §12.3.3.4 specifies `Fe⊥` for that main member. The
BG045 block grain is parallel to global Z, and the bolt axis is parallel to
that grain in the conditional geometry; its directed vector may be `+Z` or
`−Z` depending on receiver ordering. This raises the conditional case only if
the block is in fact the main member under the connection model.

## Dowel embedment input equations

For solid wood members, NDS-2024 Chapter 12 §12.3.3 and Table 12.3.3, printed
page 93, give the following specific-gravity and diameter relationships. With
the conditional DF-L value `G=0.50`:

| Diameter scenario | `Fe∥` | `Fe⊥` | Units |
| --- | ---: | ---: | --- |
| `D ≥ 0.25 in.`; `D=0.25 in.` example | `11200G = 5,600` | `6100G^1.45/√D = 4,465.461` raw; table-rounded 4,450 | psi |
| `D < 0.25 in.` | `16600G^1.84 = 4,636.742` raw; table-rounded 4,650 | `16600G^1.84 = 4,636.742` raw; table-rounded 4,650 | psi |

For `D<0.25 in.`, the two displayed directional cells repeat Table 12.3.3's
single common `Fe` entry; the standard does not tabulate separate parallel and
perpendicular values for that diameter category.

For an angle to grain, §12.3.4 Equation 12.3-11 (printed page 95) is
`Feθ = (Fe∥ Fe⊥) / (Fe∥ sin²θ + Fe⊥ cos²θ)`, where `θ` is measured between
load direction and the member's longitudinal grain (`0°` parallel,
`90°` perpendicular). At `G=0.50`, `D=0.25 in.`, and `θ=45°`, the equation
gives `Feθ=4,968.790 psi` using the unrounded formula inputs. These are
embedment inputs, not lateral-yield resistance or joint-capacity results.

The `D=0.25 in. (6.35 mm)` example is the conditional smooth/full-body
scenario used by prior corner component screens, not a delivered bolt
measurement. Under §12.3.7.1, a threaded or reduced-body fastener generally
uses root/reduced diameter `Dr`; §12.3.7.2 permits full-body `D` for a
threaded full-body fastener only within its stated thread-bearing-length
condition, or a separately supported detailed analysis. Bind physical
diameter and grain-relative loading before using these inputs in a connection
method.

The legacy component references use unadjusted `G/Fe` inputs; the current
corner register already identifies combined actions, group behavior,
continuous three-receiver response, bearing distribution, and splitting as
separate open questions. No general splitting, net-tension, row-tear-out,
group, or complete-joint resistance method is adopted here. `Fe` does not
resolve those failure modes.

## Source record and limits

The official 2024 NDS Supplement and Chapter 12 files are cached under
[`materials-source/`](materials-source/). The Chapter 12 download's filename
contains “withCommentary,” but the inspected 46-page file contains the
specification text only; no missing Commentary statement is attributed to it.
The official Supplement errata/addendum file is also cached; its 2024 addendum
does not change this DF-L Table 4A row.

| Source | Used provisions / printed pages | Local SHA-256 |
| --- | --- | --- |
| [AWC 2024 NDS Supplement, Chapter 4](https://awc.org/wp-content/uploads/2026/08/AWC_NDS2024-Supplement_20240719_Chapter-4-Reference-Design-Values_Website-1.pdf) ([AWC resource page](https://awc.org/resources/2024-nds-supplement/)) | Table 4A base values p.34; Table 4A adjustments p.32 | `1f65975633f111c308944c470b6cc10e9207b6c45e8a0804b8bdec3378bbc71b` |
| [AWC NDS-2024 Chapter 12, dowel-type fasteners](https://awc.org/wp-content/uploads/2026/08/AWC_NDS2024_withCommentary_20250328_WebsiteChapter-12-%E2%80%93-Dowel-type-fasteners.pdf) | §§12.3.3–12.3.4, Tables 12.3.3/12.3.3A pp.93–95; §§12.3.3.4, 12.3.7.1–.2 | `5fc837523ff10acc097a162718700a9b4ba64e627d2b0023439146d42fe4ee2a` |
| [NIST Voluntary Product Standard PS 20-25](https://www.nist.gov/document/ps-20-25-final) | Table 3; §§6.1.6, 7.3.7, 8.1.4 (printed pp. 4, 18, 21–22) | `8868066272130bf7a6621b7fda6f9539bf2e26e57975f2c6c00489b6613f51ca` |
| [AWC 2024 NDS Supplement updates and errata](https://awc.org/wp-content/uploads/2024/02/2024NDS-Supplement-Updates-Errata_20240212.pdf) | Cached cross-check; no DF-L Table 4A correction identified | `c69c14ec2c441e93d8b492624b213ff958e693ea0f75d29d86f6a2bd1df14262` |

The exact source-map pins and their scopes are recorded in
[`material-inputs.json`](material-inputs.json). The source frame maps propose
grain axes only; species, grade, moisture, treatment, physical dimensions,
grain/ring orientation, and fastener diameter remain unobserved. These
unknowns do not prevent the stated conditional calculations. No stock
inspection, grade inheritance, capacity, joint acceptance, fabrication
release, or climbing release is claimed.
