# Upper outer host splitting: source and path applicability

Status: **limited source-bound method route; no candidate splitting calculation**.
This note advances the prior source-gap packets by tracing the actual two-group
load path separately through each outer cleat and its three host members. It
selects first-generation EN 1995-1-1:2004 §8.1.4, corrected by AC:2006, only as
a named, non-regulatory characteristic-resistance scenario for a host-member
screen. It does not claim EC5 compliance, a design resistance, a utilization,
or a pass. Cleat-block interaction remains without an applicable method.

## Method source and exact scope

The authenticated primary source available here is [EN 1995-1-1:2004/AC:2006](https://cms.sia.ch/en/api/getMedia/559), the CEN corrigendum retrieved from
the Swiss SIA standards mirror. The local PDF is the German part, seven pages;
on PDF p. 4 (printed p. 4), it corrects §8.1.4 Eq. (8.4) and changes the
Eq. (8.3) legend to define `Fv,Ed,1` and `Fv,Ed,2` as design shear forces on
both sides of the connection (referring to Figure 8.1). It also states that
`F90,Rd` is derived from `F90,Rk` according to §2.4.3. The corrected Eq. (8.4)
is:

```text
F90,Rk = 14 b w sqrt(he / (1 - he/h))    N
```

For softwood and the arrangement of Figure 8.1, the official JRC-hosted [2008
Dietsch workshop deck](https://eurocodes.jrc.ec.europa.eu/sites/default/files/2022-06/EN1995_3_Dietsch.pdf),
PDF slides 29–30, reproduces Eq. (8.4), Eq. (8.5), its variable definitions,
and Figure 8.1. The official JRC-hosted [2008 Leijten workshop
deck](https://eurocodes.jrc.ec.europa.eu/sites/default/files/2022-06/EN1995_5_Leijten.pdf),
PDF slides 63–64, reproduces the figure and confirms that clause 8.1.4(3) is
formulated as a maximum shear-force criterion on either side. Both decks are
explanatory training reproductions, not the full normative clause. Their
function here is to corroborate the figure and English transcription; they do
not replace authenticated standard text.

The complete first-generation standard, including the full §8.1.4, Figure 8.1,
and §2.4.3 conversion text, was not available from an authenticated public
primary source in this search. The [BSI catalogue record](https://knowledge.bsigroup.com/products/eurocode-5-design-of-timber-structures-general-common-rules-and-rules-for-buildings)
identifies a current-under-review national adoption with preview/purchase
access; an unauthenticated repost or secondary transcription is not adopted.
The scenario named here is therefore limited to the corrected
characteristic equation and definitions visible in the CEN corrigendum, with
the figure corroborated by JRC training material. It does not assert that
later amended national editions or second-generation EN 1995-1-1:2025 contain
or retain identical provisions.

The source-defined geometry terms are:

| Symbol | Figure 8.1 meaning | Required candidate mapping |
| --- | --- | --- |
| `he` | Distance from the loaded timber edge to the center of the most distant fastener; for punched metal plates, to the plate edge | Signed, direction-specific distance in the selected splitting plane, using the finished member edge and the farthest bolt center in that group. The plate alternative is inapplicable to these bolt groups. |
| `h` | Timber member height | The section depth in the selected Figure plane; not automatically the longest member dimension or whichever cross-section dimension is larger. |
| `b` | Member thickness | The finished section dimension orthogonal to `h` in that same Figure plane. |
| `w` | Modification factor: `1` for all fasteners other than punched metal plates | Candidate value is `1` for the through-bolt groups if the group is represented by the source's ordinary-fastener case. |
| `Fv,Ed,1/2` | Design shear forces on the two sides of the connection, per the CEN correction to Eq. (8.3) | Internal member-section shear resultants immediately outside the transfer footprint, on both sides, in a justified Figure plane. They are not sums of individual bolt cross-grain components. |

The JRC figure shows a connection force `FEd` at angle `α` to the grain and
section shear forces `Fv,Ed,1/2` on either side. The signed force component
perpendicular to grain can identify the candidate loaded edge for that
idealized action; it is not automatically the scalar `Fv,Ed` and does not by
itself map a coupled group action. For a three-dimensional action, the
candidate must first identify a
physical two-dimensional splitting plane and obtain the section shear in that
plane. Do not combine two transverse shear components into an arbitrary
resultant, or use a nodal resultant, bolt force, receiver resultant, or couple
as a substitute for the two source-defined section shears.

## Applicability by member and path

The reviewed [outer action packet](../upper-frame-joint-review-2026-09-30/README.md)
and [upper-block geometry packet](../upper-block-strength-2026-10-01/geometry.md)
bind the current groups and conditional grain frames. Each block has two
distinct 33.0 mm-pitch, two-bolt groups. On the left, `rail_1/rail_2` transfer
through `base_rail_top` and `side_1/side_2` through `base_side_left`; the right
counterparts transfer through `base_rail_top` and `base_side_right`. In each
block, rail-pair pitch is parallel to conditional block grain and side-pair
pitch is perpendicular; these relations reverse in the corresponding host.
These pitch facts classify physical layouts only; they create no resistance
or interaction factors.

| Member/path | Figure 8.1 status | Why |
| --- | --- | --- |
| `base_rail_top`, left and right outer interfaces | **Conditional host-only Figure-plane shear subcheck; full splitting coverage is open.** | The physically motivated plane is X–N, normal to the rail pair's common bolt axis T (bolt direction is −T): grain is ±X, candidate depth N (`h=139.7 mm`), thickness T (`b=38.1 mm`), and the Figure-plane internal shear is signed `V_N` (local rail `Vv`). The shared rail also receives the other outer-cleat group and other frame transfers. Use whole-member cuts on both sides of each transfer; retain `V_T`, normal force, axial bolt action, all moments, torsion, contacts, and concurrent groups. Those off-plane effects are outside this 2D screen. |
| `base_side_left`, left outer interface | **Conditional host-only Figure-plane shear subcheck; full splitting coverage is open.** | The physically motivated plane is T–N, normal to the side pair's common bolt axis X: grain is ±T, candidate depth N (`h=139.7 mm`), thickness X (`b=88.9 mm`), and the Figure-plane internal shear is signed global `V_N` (local side `Vv` is along −N, so `V_N=−Vv`). The full transfer also includes two bolt planes, axial ties, finite contact, and eccentricity; retain `V_X`, normal force, all moments and torsion as off-plane diagnostics. |
| `base_side_right`, right outer interface | **Conditional host-only Figure-plane shear subcheck; full splitting coverage is open.** | Mirrored host path and same conditional section dimensions as the left; use its own T–N plane, signed global `V_N=−Vv`, loaded edge, and both-side cuts. Retain `V_X` and other off-plane actions. Do not mirror a left-side `he` or force sign into this member. |
| `top_outer_left_cleat` block | **Not covered as a combined block by the available §8.1.4 rule.** | One solid block receives the rail and side groups simultaneously on orthogonal faces. The full receiver wrench includes contact cells, both axial bolt ties, and both lateral bolt planes. The source gives no rule for combining two orthogonal groups, the resulting force couple, shared crack paths, or group/contact interaction. Two separate `F90,Rk` values cannot be added or treated as independent block capacities. |
| `top_outer_right_cleat` block | **Not covered as a combined block by the available §8.1.4 rule.** | Same two-group topology with mirrored orientation and its own signed block action. The same missing three-dimensional interaction rule applies. |

Conditional source-section frames and fastener-axis geometry support one
physically motivated candidate plane per host group: the plane contains the
member's grain axis and the cross-grain N direction and is normal to that
group's common through-bolt axis. The pinned current frame map records the
global source-frame axes `X=(1,0,0)`,
`T=(0,0.642787610,0.766044443)`, and
`N=(0,−0.766044443,0.642787610)`. It records
`base_rail_top` grain along ±X, section axes T/N with dimensions T=38.1 mm and
N=139.7 mm, and rail-pair bolt axis −T. Its candidate Figure plane is X–N,
with `h=N=139.7 mm`, `b=T=38.1 mm`, and signed cross-grain section shear
`V_N` (local rail `Vv`). The same map records `base_side_left/right` grain
along ±T, section axes N/X with dimensions N=139.7 mm and X=88.9 mm, and
side-pair bolt axis X. Their candidate Figure plane is T–N, with
`h=N=139.7 mm`, `b=X=88.9 mm`, and signed cross-grain section shear
`V_N=−Vv` in the side extractor's local `v=−N` convention. The mapped source
frames and matching current STEP files support those modeled orientations;
the grain assignment remains a conditional stock scenario and actual stock
is unobserved. These are candidate Figure planes and candidate `h`/`b`
dimensions, not method coverage of the full host action. Preserve the other
transverse component (`V_T` for rail, `V_X` for sides), force normal to the
Figure plane, moments, torsion, and contact/group actions: §8.1.4 Figure 8.1
provides no combination rule for those out-of-plane effects. If those actions
can activate an additional splitting path, that path remains open rather than
being merged into a scalar Figure shear.

For both hosts and blocks, `he` cannot be bound from an unsigned outer-box
distance. It is the Figure-plane distance from the loaded timber edge to the
farthest bolt center of the particular group. The N direction defines the two
candidate edges here, but the host section-shear sign alone does not establish
which edge is loaded in tension perpendicular to grain when the two-bolt
group also carries a force couple and contact action. Preserve the concurrent
signed group force, its application points, and moments; select an edge only
if the source Figure action can be mapped to that group without inventing a
distribution. Otherwise retain both signed-edge geometries as unresolved.
Exact bores, block seats, nearby cuts, and other nearer finished edges must be
included; the existing outer-box comparators exclude them. The `h`/`b` axis
selection and `he` need to be recomputed for each candidate plane and loaded
edge.

The existing action report covers only A1-rear, A12-rear, and K12-rear at
seven sampled increments each; it does not establish a six-case envelope. Its
`receiver_actions_on_block` records are complete interface wrenches at the
block datum, sourced from four finite contact cells, two axial ties, and two
lateral bolt planes per interface. In left A12-rear at full load, for example,
the rail interface wrench on the block is
`F=(-391.9, 765.1, -538.3) N`,
`M=(-20.04, -14.52, 3.05) kN·mm`; the side-interface wrench is nearly opposite
in force and moment. This is evidence of a coupled multi-face transfer, not
an `Fv,Ed` value and not a basis for summing cross-grain bolt components. The
[host-section extractor](host_actions.py) has produced local-only
`host-actions.json`: 21 sampled states, four interfaces/84 interface-state
records, and 672 target-group point-action rows. It brackets each target
footprint and retains same-state one-sided cuts, target point actions, and
whole-host balance. Each target-group wrench retains eight incident point
sources: two bolt-plane rows, two outer-seat ties, and four finite-contact
quadrature points; its transverse-force candidate is not a bolt-only sum. Its
current signed axes are `Vu=+T, Vv=+N` for
`base_rail_top`, and `Vu=+X, Vv=−N` for both side hosts; therefore the
candidate Figure-plane projections are rail `Vv` and side `−Vv`. Its
`candidate_transverse_loaded_edge` fields give signed group-force and
edge-to-farthest-fastener geometry candidates, explicitly labeled as
geometric only, with no Figure-plane, `he`, or resistance adoption. The cut
resultants are equilibrium results of the point-action model, not integrated
FE stress/traction results. Preserve axial force, orthogonal shear, all
moments, torsion, contact footprint, and adjacent groups as diagnostics.

## Next executable calculation and factors

For the four host interfaces, use the candidate planes fixed by the modeled
bolt-normal/member frames above: `base_rail_top` uses signed global internal
shear `V_N` (local rail `Vv`) in its X–N Figure plane; `base_side_left/right`
use signed global `V_N=−Vv` in their T–N Figure planes. This is a **host-only characteristic scenario** and
conditional plane subcheck, not full host splitting coverage:

1. For each saved case/increment and each bolt-group footprint, use the two
   same-state source cut shears on opposite sides. Preserve the host extractor's
   full-signed `Vu/Vv` components and local-axis map (`Vu=+T,Vv=+N` on rail;
   `Vu=+X,Vv=−N` on sides); use `UVnorm` only as a resultant diagnostic.
   Resolve signed global `V_N` as local rail `Vv` and as negative local side
   `Vv`. Calculate the raw envelope
   `Vplane,max = max(|Vplane,1|, |Vplane,2|)`. Do not call this `Fv,Ed` until
   the design-action basis is established, and do not add bolt forces or the
   two host demands.
2. For each host group, use its concurrent signed point-force/couple/contact
   action to identify the Figure-loaded edge, if the group action admits that
   source mapping. Do not choose the N-edge from the sign of section `V_N`
   alone. Measure `he` along N from the identified N-edge to the center of
   the farthest bolt in that group, including exact finished holes, seats, and
   cuts. If the two-bolt coupled action has no supported loaded-edge mapping,
   carry both edge geometries as unresolved. Rebind `he` if another
   plane/boundary is implicated.
3. For an explicitly named softwood scenario and `w=1`, calculate only the
   source-corrected characteristic reference
   `F90,Rk = 14 b sqrt(he / (1 - he/h))` in N. Check dimensional and equation
   bounds from the authenticated clause before producing candidate values.
4. Report the raw section shear envelope and characteristic reference
   separately. The saved FE cases are conditional analysis states, not a
   documented set of EN 1990 design actions. Do not compare `Fv,Ed` or declare
   a ratio until the action basis and full design conversion are supported.

This is not yet an executable resistance result. The candidate source cut
records are now available, but their signed component must still be resolved
to the Figure-plane demand and kept separate from the other actions. The
host-action extractor's signed edge-distance fields remain geometric
candidates, not adopted Figure `he` values: the source method does not supply
a reduction for the simultaneous two-bolt force couple, finite contact, and
other concurrent groups. Point actions, nodal cuts, and full interface
wrenches do not by themselves establish design `Fv,Ed` or a unique loaded
Figure edge.
The candidate Figure planes above are geometrically motivated, but they remain
a conditional subcheck because out-of-plane actions and multi-group effects
are not covered. The equation itself is not the blocker. For a
design check, the CEN correction points to §2.4.3 but does not reproduce its
full conversion route; the full authenticated §2.4.3 and relevant factor
values, plus a valid design-action basis, are not bound here. Do not import
`kmod`, `gammaM`, strength class, load-duration or service factors from an
example or another jurisdiction. A declared characteristic scenario needs no
jurisdiction claim and creates no new physical-test prerequisite, but it also
does not replace the missing design factors or establish compliance.

Leijten's [2014 WCTE paper on multiple connections along a beam
span](https://pure.tue.nl/ws/portalfiles/portal/3910148/580752898430977.pdf)
reports that one-connection models are not automatically predictive for
multiple connections and that its three-connection tests were not explained
by an available model at the time. It provides no method for the orthogonal
cleat groups or their shared block paths.

The related 2018 paper is Leijten, “Splitting of timber beams caused by
perpendicular to grain forces of multiple connections,” *Engineering
Structures* 171 (2018), pp. 10–14, DOI
[10.1016/j.engstruct.2018.05.059](https://doi.org/10.1016/j.engstruct.2018.05.059).
The TU/e [peer-reviewed article record](https://research.tue.nl/en/publications/splitting-of-timber-beams-caused-by-perpendicular-to-grain-forces/)
states the study covers beams with up to five connections along the span and
proposes an adjustment to the EC5 fracture model for that multiple-connection
effect. The full author version was inaccessible during this search; its
abstract and metadata do not establish applicability to the current oblique
3D cleat wrenches or to two orthogonal connection groups acting on one block.
It is an adjacent host-beam method lead, not a usable factor here. No
multiple-group factor is used to multiply or add separate host/group
capacities.

## Parallel-grain Appendix E route

The existing [NDS Appendix E source-bound note](../upper-block-strength-2026-10-01/local-stresses.md)
identifies E.2-1 net parallel tension and E.3-2/E.4-1 parallel row/group
tear-out. That is a potentially useful, separate member-path check only when
the actual path is a single fastener or qualifying closely spaced group
loaded parallel to grain, with its actual finished row/group geometry and
section demand mapped. It is not an alternative perpendicular-grain splitting
rule. There are geometrical candidates only: the outer rail-pair pitch is
parallel to cleat grain, and the side-pair pitch is parallel to the
corresponding side-host grain. But the saved full actions are oblique and
carry couples; neither pitch relation proves that the actual qualifying
failure path is loaded parallel to grain or establishes its Appendix E force
distribution. A parallel-only projection would leave the cross-grain splitting
path open. No Appendix E candidate resistance or demand is calculated here.

## Source cache and replay boundary

| Source/evidence | Checked location | SHA-256 | Use and limit |
| --- | --- | --- | --- |
| CEN EN 1995-1-1:2004/AC:2006 corrigendum, German | [SIA-hosted PDF](https://cms.sia.ch/en/api/getMedia/559), 7 pages, PDF p. 4 | `ff5bd62c586cc714eed9b8b7e557bbe030f36fe7e3ccd29dd10a24db755b03a5` | Primary correction to Eq. (8.4) and Eq. (8.3) definitions; not the full standard or conversion clause. |
| JRC Dietsch workshop slides, 2008 | [JRC PDF](https://eurocodes.jrc.ec.europa.eu/sites/default/files/2022-06/EN1995_3_Dietsch.pdf), 38 pages, slides 29–30 | `20b6cfc83a1b3a1afb124f9c7cc337ab3b23c141ebe3da8c74906a8eece8017d` | Official training reproduction of clause Eq. (8.4)/(8.5), definitions, and Figure 8.1; not normative text. |
| JRC Leijten workshop slides, 2008 | [JRC PDF](https://eurocodes.jrc.ec.europa.eu/sites/default/files/2022-06/EN1995_5_Leijten.pdf), 70 pages, slides 63–64 | `b3d6a181479e7b07ae1a7a86e85ffe99d848f85af708225428b8d24d4194689d` | Official training reproduction; slide 63 describes maximum shear on either side. |
| Leijten, WCTE 2014, multiple connections along beam span | [TU/e portal PDF](https://pure.tue.nl/ws/portalfiles/portal/3910148/580752898430977.pdf), 7 pages, PDF pp. 2–6 | `719670c579c3240746d1e394b007f0df00ad69660a63fe60b65044e79ee83ba8` | Primary research paper; method/experiment context only, not these cleats. TU/e permits a private research copy; cached locally, not redistributed. |
| Leijten, *Engineering Structures* 171 (2018), multiple connections | [TU/e peer-reviewed article record](https://research.tue.nl/en/publications/splitting-of-timber-beams-caused-by-perpendicular-to-grain-forces/), abstract/metadata; full author PDF inaccessible in search | n/a | Adjacent along-span factor lead; not adopted without full method/source-scope review. |
| Upper current interface actions | `../upper-frame-joint-review-2026-09-30/upper-joints.json` (local-only ignored raw JSON) | `0fc5f9ce9c92effcb01d3213c38b33282c281539dab9d48cb06f33e15c1994a6` | Source wrenches for A1/A12/K12, seven increments each; not a six-case envelope. |
| Upper finished-section/group geometry | `../upper-block-strength-2026-10-01/geometry.json` (local-only ignored raw JSON) | `2ba66f4242b59e73a7dfc14a0b21d20d1f2710b9f835d60fce569eb73353fe91` | Two-group layout, dimensions and geometry-linked STEP digests. |
| Current frame timber grain/section map | `../evaluation-resume-2026-09-24/current-frame-timber-material-frame-map-attempt01/current-frame-timber-material-frame-map.json` (local-only ignored raw JSON) | `f867b4926ed23c9f356005c134778e138c8b1230547f0b69be7c3f9bc2a42409` | Conditional host grain frames and section orientation; delivered grain is not observed. |
| Host finished STEP solids | Rail `base_rail_top.step`; sides `base_side_left.step`, `base_side_right.step`, under `../evaluation-resume-2026-09-24/current-full-frame-member-solids-attempt01/bundle/members/` | rail `79b4f7f66f35928ed383d0e396ce221d9a4302136b088a7bcd41749c52a10a60`; left `237c3fa6aa0b52c39124580810d048e38919b99b9a1fb5db5a2423e7eda62fdf`; right `ddb6ac20f1f50a9036448eb5680fdc486532ff3826ce52d566baf685a800a59f` | Exact reviewed geometry solids; not physical measurements of delivered members. |

Cached PDFs and ignored local pins are under `splitting-source-cache/`; the
machine-readable source pin record is local-only at
`splitting-source-cache/source-pins.json`. The current action and geometry
JSONs named above are likewise local-only ignored evidence. The maintained
summaries are [upper-joints README](../upper-frame-joint-review-2026-09-30/README.md),
[upper-block geometry](../upper-block-strength-2026-10-01/geometry.md), and
[conditional host material-frame map](../evaluation-resume-2026-09-24/current-frame-timber-material-frame-map-attempt01/README.md).

No splitting or tear-out capacity, code check, pass, physical inspection,
drilling/fabrication release, six-case envelope, or structural release is
established. No native solve or geometry edit was performed.
