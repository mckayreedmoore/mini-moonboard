# Bottom-outer bolt adjustment applicability

## Finding

The `1.0945088665` value for
`bottom_outer/clip_horizontal_bottom_left_1/side_1` remains a per-bolt,
unadjusted lateral-demand/reference quotient. It is the lateral component,
not the complete bolt action: the same-state outer-seat tie is separately
nonzero. The tie is not added to this lateral quotient, but the complete
angled-to-axis bolt load still requires evaluation under NDS §12.3.9. It is
not an adopted capacity, joint failure, or joint acceptance. The
quarter-inch scenario is exactly at
the NDS boundary: the automatic group-factor and geometry-factor exceptions
are both for `D < 1/4 in`, so neither exception includes `D = 1/4 in`. This
makes group membership and spacing/end/edge checks live inputs; it does not
by itself assign any factor or carry a rail-group factor onto the flagged
side bolt.

The most consequential current geometry sensitivity is in the cleat receiver
of the rail pair. The rail-axis centers are at proposed cleat grain stations
`G=43.350` and `76.350 mm` in a `119.700 mm` span. For the modeled
`D=6.350 mm` softwood scenario, `rail_1` is only `43.350 mm` from the `G=0`
square-cut end, below the parallel-tension `CΔ=1` threshold `7D=44.450 mm`
but above the `CΔ=0.5` minimum `3.5D=22.225 mm`. If the completed rail-group
load path classifies this as parallel tension toward `G=0`, §12.5.1.2(a)
would give the conditional end-distance factor `43.350/44.450 = 0.975253` for
that rail group. The source A1-full bolt-plane actions on the cleat have a
negative grain-direction sum, but that sum is about `21.396°` off the row
line and excludes the contact-cell actions. Treat the factor as a geometry
sensitivity until the actual NDS group/load direction is established. It
does not transfer to `side_1` unless a complete connection definition shows
the two interfaces belong to one group under the applicable rule.

## Source and geometry basis

The frozen single-shear report is
`/tmp/mini-moonboard-remaining-single-shear-reference-2026-10-01.json`,
SHA-256 `6551861db1112c91b87c5705bbceb3bb26f55f0d7e70029a74d828519425145e`;
its producer is
`remaining-single-shear-reference-2026-10-01/produce.py`, SHA-256
`5f2a7fdca2ef0c56c661fa10e4122189f8a7a1ae0725062cb8c56d95dd911edf`. The
current finished-feature register `current-finished-feature-register-2026-10-01/axis-features.json`
is SHA-256 `bebb4274cdecfb6ad0b0f26850d85a16570c245ea9f7d478c0b05c12b4513e19`.
Its receiver frames are proposed geometry/material coordinates, not observed
stock datums. The frozen source reports bind the conditional frame-grain map
`f867b4926ed23c9f356005c134778e138c8b1230547f0b69be7c3f9bc2a42409` and
block-grain map
`8705b8f100a2d3355c236fc19e6798bb7ad4862ba2d51826cf63a88db1285480`; grain
and section assignments remain conditional.

The four bolts are four individual two-member single-shear planes, arranged
as two pairs on the common cleat. Their modeled diameter is `6.350 mm`
(`0.250 in`). Each pair has `33.000 mm` (`1.29921 in`, `5.19685D`) center
spacing. On `base_side_left`, the side-pair line is parallel to the proposed
grain axis; on the cleat it is perpendicular to the cleat grain. On the
cleat, the rail-pair line is parallel to grain; on `base_rail_bottom_left`
it is perpendicular to grain. These centerline orientations do not alone
establish an NDS “row,” which is defined relative to the load direction.

At A1 full load, the source's receiver-0 force angles to the proposed grain
axes are:

| Axis | Receiver 0 / angle | Receiver 1 / angle |
| --- | --- | --- |
| `side_1` | `base_side_left`, `86.031°` | cleat, `3.969°` |
| `side_2` | `base_side_left`, `74.255°` | cleat, `15.745°` |
| `rail_1` | cleat, `4.792°` | `base_rail_bottom_left`, `85.208°` |
| `rail_2` | cleat, `41.183°` | `base_rail_bottom_left`, `48.817°` |

The signed two-bolt plane-force sums at this state are `(0, 322.7691,
-390.3371) N` for receiver 0 of the side pair and `(-193.4650, 378.2470,
-317.3869) N` for receiver 0 of the rail pair. They are respectively
`79.587°` and `21.396°` from their pair centerlines. These are diagnostics
formed from the four individual plane actions only: they exclude the separate
outer-seat axial ties and all contact-cell forces, and are not complete
interface or joint resultants. The full cleat source-boundary packet keeps
those actions distinct. Load directions vary with state, so an A1-full angle
does not classify all 21 states. At full load, the A12 and K12 bolt-only
plane sums are also oblique: side-pair line angles `32.423°` and `57.191°`,
and rail-pair line angles `60.689°` and `69.395°`, respectively. The parent
independently confirmed that none of these six case-level sums is exactly
aligned with its pair line. These checks still do not include the contact
actions and therefore do not replace a connection-group free body.

The pinned source rows at A1 full are rail `SPR1339/1340` and `SPR1341/1342`,
then side `SPR1343/1344` and `SPR1345/1346`. For `side_1`, the report gives
`(approximately 0, 476.4185, -459.5667) N` on receiver 0 (`base_side_left`)
and the opposite on the cleat, plus a separate `197.1248 N` tie. Ties are not
combined with the lateral-plane forces for the Chapter 12 single-shear
reference. The method review records the full plane and tie source linkage.

## Chapter 11 group action

The pinned official AWC 2024 Chapter 11 extract is
`upper-block-strength-2026-10-01/source-cache/chapter11-2024-awc-20260911.pdf`,
SHA-256 `45a3d78de1a4fba573589be0fc776e37bd581e4cedec24e38d63856161092d33`.
Section 11.3.6.1 (printed p. 74) requires `Cg` for dowel-type fasteners with
`D ≤ 1 in` **in a row**; its `Cg = 1.0` exception is only for `D < 1/4 in`.
Sections 11.3.6.2 and 12.1.2.4 define a row as two or more same-diameter
fasteners aligned with the direction of load. Thus a quarter-inch two-bolt
pair is not automatically an NDS row merely because its centers are
collinear. The source A1 bolt-only sums above are far from alignment for the
side pair and oblique for the rail pair. Use the full, same-state connection
free body and moments to establish group loading and row membership for each
receiver; do not treat the bolt-only sums as that result.

Section 11.3.6.2 also merges staggered adjacent rows for `Cg` only when their
cross-row spacing is less than one quarter of the distance between the
closest fasteners measured parallel to those rows (with the stated
even/odd-row treatment). The four cleat axes are two orthogonal interface
pairs, not an already classified parallel-row layout. Any later row layout
must test this threshold from the actual axis coordinates instead of
inferring row count from the four axis labels.

If a pair is established as a row, `Cg` still needs a documented connection
group and main/side-member assignment plus `n`, `s`, `Em`, `Es`, gross `Am`
and `As`, and the equation's `REA` and `m` terms. For the conditional
quarter-inch wood-to-wood scenario, `s=1.29921 in` and
`γ=180,000D^1.5=22,500 lb/in`; these alone do not determine `Cg`. Section
11.3.6.3 requires gross sections, and for a member loaded perpendicular to
grain uses thickness times overall group width (one-row width is the minimum
parallel-to-grain fastener spacing). Table 11.3.6A's tabulated values are
stated conservative for `D<1 in`, `s<4 in`, and `E>1.4 million psi`, but the
appropriate row, section areas, and conditional/actual modulus still must be
shown. No numeric `Cg` is adopted here.

The two side axes and two rail axes are separate single-shear bolt planes;
they are not a single three-member multiple-shear bolt. Section 12.5.1.2's
rule to apply the smallest `CΔ` across shear planes applies to a multiple-
shear or asymmetric three-member connection using the same fasteners. It does
not, by itself, merge these two distinct bolt pairs through their shared
cleat. A complete connection analysis must state whether/how the pairs form
groups before propagating the minimum factor.

## Chapter 12 geometry factors and placement

The pinned official AWC 2024 Chapter 12 source is
`hardware-material-specification-2026-09-30/materials-source/AWC_NDS2024_withCommentary_20250328_WebsiteChapter-12-Dowel-type-fasteners.pdf`,
SHA-256 `5fc837523ff10acc097a162718700a9b4ba64e627d2b0023439146d42fe4ee2a`.
Section 12.5.1.1 (printed p. 97) makes `CΔ=1` automatic only for `D<1/4 in`.
Section 12.5.1.2 (printed pp. 97–98) governs `D≥1/4 in`, including exactly
one quarter inch, when a relevant end distance or row spacing is below its
`CΔ=1` minimum. For `D=6.35 mm`, Table 12.5.1A gives:

| Candidate direction | `CΔ=0.5` minimum | `CΔ=1` minimum |
| --- | ---: | ---: |
| Parallel grain, softwood tension | `3.5D = 22.225 mm` | `7D = 44.450 mm` |
| Parallel grain, compression | `2D = 12.700 mm` | `4D = 25.400 mm` |
| Perpendicular grain | `2D = 12.700 mm` | `4D = 25.400 mm` |

The proposed cleat frame places `side_1` and `side_2` each at `G=59.850 mm`
from both square-cut ends of its `119.700 mm` grain span. Those end distances
exceed `7D`, if a parallel-tension case governs. For the base-side receiver,
the same side axes are at proposed grain stations `284.368` and `317.368 mm`
within a `2570.726 mm` span. The rail pair is at cleat grain stations
`43.350` and `76.350 mm`; if the loaded end is `G=0`, the group minimum is
`43.350 mm`, giving the conditional sensitivity described above. The A1
receiver-0 bolt-only rail sum has a negative component along cleat grain,
toward `G=0`; because its full vector and omitted contact actions are
oblique, this is not by itself the §12.5.1.2 load-direction classification.

For a qualifying row in the parallel-grain-loading category, each pair's
`33.000 mm` spacing exceeds the `3D` minimum and `4D=25.400 mm` `CΔ=1`
spacing. For perpendicular-grain loading, Table 12.5.1B lists `3D=19.050 mm`
minimum and the “required spacing for attached members” as the `CΔ=1`
spacing. Each pair crosses grain in one member at its interface; that
attached-member criterion and the direction/category for an oblique group
must be resolved before claiming `CΔ=1`. The source plane vectors are lateral
components perpendicular to the bolt axes; each bolt also has a separate,
nonzero outer-seat axial tie. Therefore the plane rows alone do not establish
a 90-degree complete bolt action. Section 12.3.9.1 (printed p. 96) says the
component perpendicular to the axis shall not exceed adjusted `Z′` for the
single-shear reference connection with member thicknesses `ts=ℓs` and
`tm=ℓm`, and ample bearing area shall resist the component parallel to the
axis. For `D≥1/4 in`, §12.5.1.2(b) and Figure 12E also prescribe an
equivalent shear-area geometry factor when the applied load is at an angle to
the fastener. The complete force vector, effective shear area, and required
parallel-axis bearing area remain to be evaluated from the same-state source
and geometry. No numeric `CΔ` from (b), bearing area, or capacity is adopted
here. These bolt-axis provisions are distinct from the per-receiver
load-to-grain angles used in `Kθ`.

Section 12.5.1.3 (printed pp. 98–99) separately requires edge distances and
between-row spacing for `D≥1/4 in`; these are not values of `CΔ`. Table
12.5.1C uses the lesser of `ℓm/D` and `ℓs/D`; the source intervals give
`ℓ/D=14` on each side plane and `14` / `6` for the cleat / rail members in a
rail plane. The applicable edge category depends on member load direction,
loaded versus unloaded edge, and row spacing. Table 12.5.1D supplies the
between-row limits, and §12.5.1.3 limits perpendicular-to-grain distance
between outermost fasteners to `5 in` unless special detailing accommodates
cross-grain shrinkage. Exact finished locations are available, but a
member-by-member loaded-edge and row map for every state has not been adopted
by this note. The geometry packet's conditional bearing-area results do not
replace these bolt-placement checks.

Sections 12.6.2–.3 (printed p. 100) require the gravity axis of each member
in an angled-to-grain multiple-fastener connection to pass through the
group's center of resistance for uniform distribution, and require local
connection stresses to be evaluated by engineering mechanics. NDS
§11.1.2 (printed p. 70) states the same local-stress obligation. The
existing `Kθ` in the Chapter 12 lateral-yield reference scenario addresses
its stated angle-to-grain reduction; it does not supply `Cg`, `CΔ`, a row
load distribution, or the local member checks.

## Service assumptions and bounded next calculation

The raw reference producer marks adjustments unapplied and has no selected
`CD`, `CM`, or `Ct`. The separate material packet's `Fc⊥=625 psi` No. 2
comparison is explicitly a conditional dry-service / normal-duration material
scenario; that does not silently set connection factors for this lateral
check. Chapter 11 §§11.3.2–.4 (printed pp. 72–73) bases `CD` on actual ASD
load duration, `CM` on seasoning/moisture/service, and `Ct` on sustained
temperature. A declared normal-duration ASD, seasoned dry (≤19%) and
≤100°F scenario would use the applicable unity factors; those assumptions
must be stated for this connection calculation. Do not substitute a favorable
load-duration factor or other service condition to make the quotient pass. No
observed moisture, temperature or load-duration facts are inferred.

The next conditional calculation can use the frozen 21-state plane forces,
separate ties, contact-cell forces, moments and finished-member frames to:

1. Define each receiver's actual NDS fastener group, main/side role, and any
   row direction from its complete same-state free body; retain all signed
   bolt actions and moments. Keep the lateral plane component and axial tie
   separate for the lateral reference comparison, then evaluate the full
   angled-to-axis bolt action under §12.3.9. Do not count contact compression
   as bolt capacity.
2. Compute `Cg` only for a demonstrated row, using conditional or supported
   `E`, gross areas and all equation inputs. Decide the connection boundary
   before applying a minimum `CΔ` to other axes.
3. Resolve the oblique load direction in each timber; check end, edge,
   within-row and between-row criteria against the exact proposed stations
   and the applicable NDS category. Report any unassigned condition without
   substituting a favorable factor.
4. Apply only stated service/material assumptions and supported hardware
   properties to the individual reference modes, then evaluate local member
   stresses and the complete joint. The quarter-inch `Fyb=45 ksi` remains an
   arithmetic scenario only; Chapter 12 Table 12A's 45-ksi table entry starts
   at `D=1/2 in`, and this note adopts no resistance.

This analysis resolves which standard checks are triggered and their
conditional geometric inputs; it does not calculate a final `Cg`, complete
adjusted capacity or adopted `DCR`. It does not infer strength acceptance
from force fidelity, a satisfied spacing threshold, or the conditional
`CΔ=0.975253` sensitivity.
