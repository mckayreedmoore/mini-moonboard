# Additional backing on the unchanged twelve-screw panel

This is a bounded **additional-backed Moon-like sensitivity**, using the
upper-left panel and A12-rear load. It preserves the current AC-fir material,
twelve screw stations, all 36 screw force components, Hillman stiffness laws,
normal contact penalty and source loads. The current candidate's 66 axes,
geometry and whole-frame force packets are unchanged. The parent's frozen
paired calculation completed and its source hashes, output hashes and fields
were independently authenticated. Added backing reduces the governing head
tension by **0.1383%** under these fixed-receiver laws; the conditional head
references remain exceeded. This completes the stated numerical sensitivity,
not complete panel acceptance or a candidate change.

The question is whether additional face backing materially changes elastic
panel bending and the concentration of screw tension. This calculation does
not assign a Moon or Hillman capacity, adopt a different panel material, or
repeat the earlier twenty-screw or grain-direction experiments.

## Reference and supported stations

The official [Mini guide, printed page 2](https://moonclimbing.com/media/moonboard-pdf/How-to-build-a-MoonBoard_v2.3.pdf)
specifies four uprights spaced 813 mm apart. Its filename says v2.3; its
internal version is 2.2, July 2023. The [build instructions](https://eu.moonclimbing.com/build-your-moonboard)
also call for horizontal bracing across panel joints. The [exact Mini panel
SKU](https://eu.moonclimbing.com/mini-moonboard-diy-panels.html) specifies birch
and says mounting holes are not predrilled. No verified twelve-screw mounting
prescription, support width, fixed-receiver stiffness or particular panel
fastener is inferred from these sources. The published 5 mm screws of 50/60 mm
length concern hold pinning, not an authenticated panel mounting specification.

A literal replacement of this candidate's backing with four uprights would
leave its center-column screw stations unsupported. Accordingly, the paired
branches retain all existing screw receivers and backing; the second adds an
interior upright and a brace at the horizontal panel joint. They are declared
fixed analysis supports, with no fabricated member, attachment, installation
or whole-frame load path claimed.

| Item | Frozen / declared position and law |
| --- | --- |
| Solved body | `main_upper_left`, 1217.6125 × 1219.2 × 18.25625 mm |
| Existing screw components | Twelve axial and 24 signed lateral rows, all at their current source stations |
| Original normal backing | 96 frozen contact cells on patches 43, 75, 82 and 95; rim, center principal, top rail and service rail |
| Conceptual four upright centerlines | Global X = −1219.2, −406.2, 406.8, 1219.8 mm; first line at the frozen left panel edge, three exact 813 mm spaces |
| Added upright in solved panel | X = −406.2 mm, declared 38.1 mm face width, full panel slope interval |
| Added joint brace | At local direction-2 = −1419.8241337741295 mm; 19.05 mm of its declared 38.1 mm face width lies inside this upper panel |
| New normal contact law | Same source penalty: 100 N/mm³ times each remaining cell area; zero initial gap, compression only |
| Receiver boundary | All screw receivers and face supports fixed; no receiver rotations, timber flexibility or floor/bolt-clearance state |

Only the upper-left panel is solved. The four centerlines describe a spacing
reference and datum, not a full replacement frame; the fourth line and the
right-hand panels are outside this benchmark. The 38.1 mm face width is this
analysis hypothesis, using the current rail-face width, not a Moon prescription.
The old upper-top 65.95 mm mismatch is already removed by the four authorized
current screw moves; no obsolete station is substituted here.

The new support rectangle union is partitioned into nonoverlapping pieces.
Existing backing rectangles, including their small source screw cavities, are
reserved so the new pressure springs do not double the old backing. Added
cells span at most 90 mm per in-plane direction. Their areas and centroids
remove the current back-face circular bores, using the frozen geometry and
existing `radius_at` / `union_length` helpers with recorded quadrature error.
No centroid may lie in a physical bore. Gross added area is approximately
63,598.663 mm²; approximately 1,238.403 mm² of back-face openings is removed.
The preparation records every actual cell and area. This is a declared
discretization, not a converged continuous contact-pressure envelope.

## Frozen mechanics and audits

[panel-backing-comparison.py](panel-backing-comparison.py) reuses the original
upper-left native matrix, C3D20 point interpolation, bordered free-body
factorization, audited elastic quotient, source full-vector loads and existing
QP helper. It launches no native solver or CAD. It reads the original 73 MB
native stiffness export once and factors only this panel's 6,567 physical DOFs.
The original material axes and assigned layer constants remain unchanged; no
strong-X or birch operator is substituted.

The physical point projection is `B`, the six source rigid columns are `R`
(rotations scaled by 1000 mm), and `D = B R`. Recovered force/couple identities
must reproduce the retained source rows and every new contact station.
The panel load is the original nodal gravity column times 1.1111358300342407
plus the A12-rear live column. The source live force is
`(0, 300, −2224.11080763025) N`, with the original 100 mm front-face lever and
hold/load footprint. It is the same 250 lb ×2 downward action; it is not a
force copied from a panel screw or a load reduced to obtain a pass.

The elastic quotient supplies panel-only `H` and `e`. Both branches solve
`Dᵀ f = Rᵀ F`, with `q = D a + e − H f`: signed lateral screws obey `f=kq`,
while axial screws and normal contacts obey `f=k max(q,0)`. A single active
mask from the existing QP seeds an original linear KKT refinement. Inactive
forces have their defining zero value; no terminal force vector is clipped,
and no alternate force law or mask search supplies an acceptance claim. The
all-row signed-motion and original-law audits decide whether that branch is
usable. A failing branch stops and retains its input snapshot and reason.

Required numerical gates are force balance ≤0.1 N, moment balance ≤2 Nmm,
spring-law reconstruction ≤1e−4 N, physical nodal equilibrium ≤1e−4 N,
physical-projection motion difference ≤1e−8 mm and positive spring motion
≤10 mm. A negative axial result is not clipped into a head comparison.
Compliance reciprocity and positive-semidefinite checks also apply. The
recomputed original panel-normal compliance must match the earlier saved
panel-only block to relative 1e−7. These are numerical consistency gates,
not complete panel or fastener resistance criteria.

Preparation runs only source authentication, contact geometry arithmetic and
small coupons: centered/eccentric four-tie reactions, loaded/open unilateral
ties, exact rectangle overlap subtraction, C3D20 constant/affine fields, and
point force/couple work. It opens no source response arrays or stiffness
matrix. Build is parent-owned and serialized through the existing ledger lock.
The existing environment is frozen at NumPy 2.5.2, SciPy 1.18.1 and OSQP 1.0.4;
commands use `--no-sync` and do not alter shared dependencies.

## Outputs and interpretation

Each new branch exports all twelve screws' **same-state** tension, signed
lateral components, opening, force vector and panel/connector self compliance;
all contact forces, areas, pressures and closures; all physical displacement
and nodal load vectors; and 3×3×3 Gauss-point strain/stress fields for each
original C3D20 element. The field axes, sample count and component maxima are
explicit. The reduced operator, physical projection and row identities are
also saved, so compatible force sharing and the reconstructed panel field
can be audited together.

The inherited generic favorable head references are 930.222–984.128 N with
explicit `G=.50`, nominal 9.017 mm head and `CD=1.6` hypotheses. The
[AWC research](https://web-media.awc.org/wp-content/uploads/2021/12/17210650/2018-nds-head-pull-through-paper.pdf)
includes flush countersunk heads and distinguishes design allowances from
research ultimate loads. They remain conditional ASD references, not
delivered Hillman strengths. Local 360 psi face pressure/deformation and
unrolled-strip punching comparisons reuse the frozen resistance helpers and
are labeled provisional; neither is an empirical screw-head failure rating.
Gross filled-bore native stresses likewise do not resolve the countersink,
loaded-hole contact, crack initiation or actual veneer failure.

Three earlier contexts stay separate from the new paired force basis:

| Context, same A12-rear question | Saved peak axial force | Scope |
| --- | ---: | --- |
| Earlier normal-only rigid panel | 396.794 N | Three panel-normal/bending balance coordinates; omitted in-plane reactions, receiver motion and panel seams |
| Earlier normal-only elastic panel | 2130.507 N | Same reduced normal basis and source elastic response; not a full-vector whole-frame state |
| Compatible current whole frame | 1868.993 N, simultaneous lateral 719.961 N | Saved nominal A12-rear witness; frame/joint compatibility and its independent twelve accepted / two excluded state inventory |

The earlier rigid/elastic results are read from their frozen comparison, not
rerun. Their spring-law gate was 0.1 N and their reported load projection
discarded in-plane rigid wrench components. The new full-vector branches use
the stricter gates above; none of these values is relabeled as another
branch's result or a Moon performance measurement. The numerical comparison
answers only the added-backing sensitivity under its stated laws and boundary.

## Authenticated paired result

The parent executed the frozen build below with exit 0 in **18.794 seconds**.
The [receipt](rawlocal/panel-backing-comparison/attempt01/receipt.json) and
[summary](rawlocal/panel-backing-comparison/attempt01/summary.json) report
`COMPLETED_CONDITIONAL_ADDITIONAL_BACKING_PANEL_COMPARISON` and
`numerical_comparison_complete: true`. Independent read-only authentication
verified all **50 source and 16 output hashes**, the 24 same-state screw
records, 222 contact records and **21,600 Gauss-point field records**. The
[field audit](rawlocal/panel-backing-comparison/audit01/result-field-audit.json)
recomputes the response census and field maxima from the actual outputs.

| Same-state quantity | Unchanged backing | Additional backing |
| --- | ---: | ---: |
| Governing screw tension | 1972.464876 N | 1969.737115 N |
| Simultaneous lateral force at that screw | 844.211518 N | 842.175004 N |
| Governing screw opening | 0.733345879 mm | 0.732331720 mm |
| Total screw tension | 2956.588475 N | 3014.545748 N |
| Total face compression | 1180.952806 N | 1238.910079 N |
| Largest contact force | 794.601883 N | 792.396673 N |
| Largest sampled contact pressure | 0.445130245 MPa | 0.443894902 MPa |
| Maximum lateral force across all screws | 1051.987398 N | 1050.874827 N |
| Generic favorable head-reference ratio | 2.00428–2.12042 | 2.00151–2.11749 |
| Provisional face-pressure ratio, `CD=1` | 17.44014 | 17.41602 |
| Provisional unrolled-strip punching ratio, `CD=1` | 15.70577 | 15.68405 |
| Maximum physical nodal displacement norm | 8.314491865 mm | 8.315417796 mm |

Both governing head records identify `round_panel_upper_left_edge_2`, receiver
`base_rail_top`, at global **(−835.075, 1523.339404, 2141.899800) mm**. Its
tension drops by **2.727761 N**. The largest contact remains `contact_82_17`
on the top rail, area 1785.099738 mm², at
**(−800.964043, 1529.482913, 2149.221350) mm**. Its spring stiffness is
178509.973828 N/mm and its panel self compliance is 0.023780614547 mm/N.
Seven of the 30 added cells engage, carrying **110.706108 N** in total; the
largest new-cell force is 48.263464 N. The other 23 added cells stay open.

The unchanged and augmented sums both give **1775.635669 N** outward normal
resultant: additional backing increases total tension and compression by the
same 57.957273 N. All six wrench components balance. The common external
force is `(approximately 0, 300, −2404.872640) N`; its moment is
`(−891157.199399, −751731.696444, −103031.629455) Nmm` about the panel datum
`(−675.761235, 1182.398699, 1721.381649) mm`. Thus the added contact force
cannot be read as an equal reduction in the governing head force.

Maximum residuals across both states are **9.10e−13 N** force balance,
**7.96e−10 Nmm** moment balance, **9.90e−9 N** original spring-law error,
**9.47e−8 N** physical nodal equilibrium and **6.73e−11 mm** projected versus
physical motion. Original panel-normal compliance agrees to relative
**1.61e−12**; reciprocity error is 1.29e−12 and the minimum compliance
eigenvalue is −1.79e−17 mm/N, within numerical tolerance. The single fixed-mask
KKT refinement changes the QP seed by at most 3.403390 / 4.635945 N,
respectively; the final accepted vectors, rather than the approximate seeds,
satisfy the unchanged strict laws and gates.

The gross equivalent-layer fields also change little. Absolute local stress
component maxima, ordered `(11, 22, 33, 12, 13, 23)`, are
`(19.39632, 31.71920, 13.56749, 4.93098, 3.88565, 9.12124) MPa` and
`(19.39529, 31.71861, 13.56748, 4.92748, 3.88549, 9.12132) MPa`.
The largest absolute component in both states is `sigma_22` at element 1516,
`main_upper_left_layer_3`, at the same Gauss point. The largest engineering
strain component is `gamma_23`, **0.1181182 / 0.1181192**. These are fields of
the declared linear equivalent material and gross filled-bore mesh; their
magnitudes do not establish actual material linearity or a physical crack
location. The saved displacement field does not improve uniformly.

This bounded test finds that the specified extra compression-only backing
does little to relieve this head concentration. It does not establish the
behavior of a complete Moon frame, a different screw pattern or material,
flexible new backing attachments, or a measured Hillman installation. Both
the generic head references and provisional local comparisons remain
conditional; reference exceedance alone is not an empirical breaking load.
The `complete_panel_acceptance`, `whole_frame_force_allocation_replaced`,
`Moon_assembly_or_capacity_qualified`, `reference_layout_adopted`,
`candidate_geometry_or_screw_policy_changed` and `physical_release` flags
remain **false**.

| Frozen numerical evidence | SHA-256 |
| --- | --- |
| [Build receipt](rawlocal/panel-backing-comparison/attempt01/receipt.json) | `c050d8bfbc8848dd7b779c9b3a3c63c3ad8e33b717274ce1e81bd3890acbfc7d` |
| [Build summary](rawlocal/panel-backing-comparison/attempt01/summary.json) | `956f46cf58810e912c2394d4a2fb0279c5c2c9efed6d86f36412190b17841c36` |
| [Executed producer snapshot](rawlocal/panel-backing-comparison/attempt01/producer.py.snapshot) | `f7db8bf1625506f5ffaf551fadbbc794ea64af2d310161a2451c28ee862f70d7` |
| [Panel operators](rawlocal/panel-backing-comparison/attempt01/panel-operators.npz) | `34a60329a670fc9e9311e930c978775e861b5c4080ebe092402b289f5e4379a1` |
| [Physical projection](rawlocal/panel-backing-comparison/attempt01/panel-projection.npz) | `3d4649a4cf9a35e53eaa491c89c6054d52997d92462228338bc0f54541a1b8d2` |
| [Independent field audit](rawlocal/panel-backing-comparison/audit01/result-field-audit.json) | `fa681a65a1c1d46aa49ed5de35e968ad40ed90043ba6b80f131e90d01d3d99e2` |

## Reproduction and retention

The owned ignored subtree is `rawlocal/panel-backing-comparison/`. One official
guide is retained in its shared source cache, SHA-256
`2f3d1563cf405a6dd297bf5ca61592806b39d56a024bce260e496305d88917c2`,
1,248,505 bytes; attempts reuse it and existing native/source assets. No copied
solver installation, mesh, CAD export or native stiffness matrix is added.
Raw preparations, STOPs and numerical results remain active reproduction
evidence; none is proposed for pruning. The completed build adds 12,441,180
bytes of raw evidence, including the two compressed field exports. Source
native assets are shared, not copied into this attempt.

The parent freezes the preparation receipt and producer before the build.
Use fresh output directories; earlier attempts cannot be overwritten:

```sh
PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 \
uv run --no-sync python \
  docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/upper-corner-screw-layout/panel-backing-comparison.py prepare \
  --output docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/upper-corner-screw-layout/rawlocal/panel-backing-comparison/preparation01

PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 \
uv run --no-sync python \
  docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/upper-corner-screw-layout/panel-backing-comparison.py build \
  --preparation docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/upper-corner-screw-layout/rawlocal/panel-backing-comparison/preparation01 \
  --receipt-sha256 52db2996f6f15a7f7dbd54f353f951de3cdc3936f2738a462ff190e4ad3238e3 \
  --output docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/upper-corner-screw-layout/rawlocal/panel-backing-comparison/attempt01
```

The preparation command above completed with exit 0 in **2.376 seconds**.
Independent authentication verified **45 source and four output hashes**.
The [receipt](rawlocal/panel-backing-comparison/preparation01/receipt.json),
SHA-256 `52db2996f6f15a7f7dbd54f353f951de3cdc3936f2738a462ff190e4ad3238e3`,
has status `READY_SOURCE_AND_LAYOUT_ONLY_NOT_NUMERICAL_COMPARISON`.
The producer and executed [snapshot](rawlocal/panel-backing-comparison/preparation01/producer.py.snapshot)
are byte-identical, SHA-256
`f7db8bf1625506f5ffaf551fadbbc794ea64af2d310161a2451c28ee862f70d7`.
The [layout](rawlocal/panel-backing-comparison/preparation01/layout.json),
SHA-256 `6fd9a4a9ebcb8f906c8cf1d12bb66c02d2a5f513863c8b9c025b6661df89f1b6`,
contains 96 original / 30 additional normal contact cells, net added area
**62,360.260015160326 mm²**, and removed back-face bore area
**1,238.4031098388825 mm²**. Its largest recorded contact-area quadrature
error estimate is **6.18e−8 mm²**. The [known-answer record](rawlocal/panel-backing-comparison/preparation01/known-answer.json)
passes all five stated coupons, SHA-256
`8b639ff6cb4985a324ab0219f9b0d3ee9ddb5939b5e3b53d2704f2a2c9bdeafb`.

The preparation remains source/layout evidence; the separately authenticated
build supplies the paired result above. The parent owns integration into the
root summary/index. Neither command changes candidate geometry, screw policy
or the compatible whole-frame force allocation.
