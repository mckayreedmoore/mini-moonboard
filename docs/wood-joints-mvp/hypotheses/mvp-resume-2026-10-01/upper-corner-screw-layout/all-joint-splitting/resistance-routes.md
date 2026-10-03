# Numerical splitting-resistance routes and material limits

## Recorded basis

The current conditional DF-L No. 2 inputs are parallel tension, parallel
compression, bending, shear and perpendicular compression. They contain no
perpendicular tensile design value, characteristic splitting parameter, or
Mode-I/Mode-II fracture energy. Analytic mass density is not characteristic
strength density, and NDS specific gravity is not automatically that density.

[NDS 2024 Chapter 3, §3.8.2](https://web-media.awc.org/wp-content/uploads/2021/12/17210019/AWC_NDS2024_withCommentary_20240718_AWCWebsite_Chapter-3-Design-Provisions-and-Equations.pdf)
directs avoiding perpendicular tension or providing sufficient mechanical
reinforcement. The [USFS timber bridge manual, Chapter 5, p.5-88](https://www.dot.state.mn.us/bridge/pdf/insp/USFS-TimberBridgeManual/em7700_8_chapter05.pdf)
supports checking bolt tension and net washer bearing against perpendicular
compression. Neither provides a general short-cleat washer-plug or crossed
joint fracture capacity from the presently recorded strengths.

## Finite alternatives

| Route | Evidence needed | Current use |
| --- | --- | --- |
| Avoid opening under the recorded forces | Supported force placement and applicable mechanics demonstrating that the simultaneous timber duties require no perpendicular tension; retain shear and torque | The new [spine test](spine-opening.md) tests a necessary condition. The [header boundary map](header-boundary.md) studies whether spreading changes the apparent opening. Compression at selected cuts is only a normal subcheck. A complete stress field is one possible proof route, not a blanket prerequisite. |
| Carry opening with a mechanical tie | Actual split-plane coverage, supported end anchorage, simultaneous steel/lateral checks and matching complete timber transfer | The [annular column](anchorage-column.md) establishes a conditional prescribed-pressure anchorage component for the four proposed ties. Its force is already counted in the proposal; no reserve or second subtraction is available. Other bolts cannot inherit this geometry/pressure result. |
| Apply a matching unreinforced fracture method | Material fracture/splitting inputs and an applicable connection/group action map | Not established for the current crossed/opposing three-dimensional duties. |

The [Franke–Quenneville CIB-W18 mixed-mode paper](https://www.irbnet.de/daten/iconda/CIB_DC31328.pdf)
offers a numerical method combining opening and sliding fracture energies
for eligible transverse dowel groups. It needs matched Mode-I and Mode-II
material inputs and does not automatically cover axial washer anchorage or
an entire crossed timber joint.

## Minimum reinforcement checks and method scope

[NDS 2024 §§11.1.2–11.1.3](https://awc.org/wp-content/uploads/2026/09/AWC_NDS2024_withCommentary_20260911_Website_Chapter-11-Mechanical-Connections.pdf),
printed p.70, calls for applicable engineering mechanics and appropriate
procedures or tests for eccentric connections inducing perpendicular tension.
It does not prescribe a full three-dimensional stress reconstruction for
every joint. A supported simpler equilibrium or local mechanics calculation
can close its applicable component. All simultaneous duties still need an
applicable path and resistance check before complete numerical qualification.

NDS 2024 specification §3.8.2, printed p.24 of the authenticated Chapter 3
PDF, permits sufficient mechanical reinforcement where perpendicular tension
cannot be avoided. That PDF contains 12 specification pages and no C3.8.2
commentary. The [historical 2018 Commentary](https://awc.org/wp-content/uploads/2021/10/AWC_NDS2018-withCommentary_20200827_AWCWebsite_Commentary.pdf),
C3.8.2 at printed p.208, discusses reinforcement as context; current 2024
C3.8.2 wording remains unverified. The [primary reference-scope note](../splitting-reference-scope.md#nds-and-commentary-a-matching-asd-component-route)
also identifies the NDS §3.4.4.1 reduced-depth shear route for a matching
rectangular bending-member component. It is not a universal short-cleat
splitting capacity. No `Ft_perp = Fv/3` value or EC5 capacity-to-cut-hull
comparison is adopted. The [USFS tension-connection procedure](https://www.dot.state.mn.us/bridge/pdf/insp/USFS-TimberBridgeManual/em7700_8_chapter05.pdf),
§5.8, printed p.5-88, supplies axial bolt tension and net washer-area wood
bearing against perpendicular compression. It states that NDS gives no
tension-only bolt distance or spacing rule; this is not an unlimited spacing
approval or a short-cleat fracture capacity. Its historical A307 stress cannot
be substituted for the project's bolt material properties.

A finite mechanical-reinforcement assessment needs:

1. Actual tie coverage of the relevant split plane, carrying the simultaneous
   opening force and couple without subtracting an already counted tie twice.
2. Both end anchorages and the complete host/contact path where an end lies
   on another timber, with actual supported washer lands.
3. Steel tension and simultaneous applicable metal actions, plus washer metal
   bending/yield checks under the selected pressure distribution.
4. Peak wood bearing under both end washers against the applicable adjusted
   perpendicular-compression reference.
5. The remaining shear, torque and moments through their supported paths,
   including a demonstration that the reinforcement does not introduce an
   unresolved perpendicular-tension or anchorage failure mode.

The [annular-column result](anchorage-column.md) is a local prescribed-pressure
mechanics proof for the four proposed spine ties. It closes that compressive
anchorage component under its recorded geometry and pressure assumptions.
It does not establish every joint's complete transfer, an arbitrary washer
plug/pull-through strength, or a capacity for another tie placement. A bolt
with one cleat washer and one host washer also cannot inherit a cleat-only
two-end proof without its separate host and contact checks.

The independently hashed primary PDFs are Chapter 3
`205df74e16f632dfe78211e99bfa5dfa8b9f8dd316e9c5fa1316493f795ec644`
at `../rawlocal/profile-method-completion/sources/nds2024-chapter3.pdf`, and
Chapter 11 `45a3d78de1a4fba573589be0fc776e37bd581e4cedec24e38d63856161092d33`
at `../../../upper-block-strength-2026-10-01/source-cache/chapter11-2024-awc-20260911.pdf`.
Both caches contain specification pages only despite their filenames.
Historical 2018 C11.1.3 commentary provides context, not a new adopted 2024
numerical resistance. No unverified draft head-strength equation is used.

The [Tokyo compact-tension study](https://www.jstage.jst.go.jp/article/jwrs/63/6/63_269/_article/-char/en)
tested Douglas fir among other species. Those species-test results do not
establish DF-L No. 2 characteristic design properties. The [2012 CIB
analysis](https://ltu.diva-portal.org/smash/get/diva2%3A1013109/FULLTEXT01.pdf)
also cautions against treating the old Eurocode softwood constant as a
universal Douglas-fir value. No species/grade transfer is adopted here.

## New Eurocode research: no capacity adopted

The [public 2023 committee-draft text](https://www.scribd.com/document/708925492/Borrador-Eurocodigo-20XX)
contains reinforcement, combined bolt action and head-pull-through routes.
These require applicable group actions, tie depth/anchorage, characteristic
density or matched material parameters, and simultaneous checks. They are
potential calculation routes, not accepted capacities for this project.
[BSI](https://knowledge.bsigroup.com/products/eurocode-5-design-of-timber-structures-general-rules-and-rules-for-buildings)
confirms a final 2025 edition exists; its detailed text was not verified here.

**Head-strength equation transcription remains unverified.** The accessible
draft extraction loses the grouping of the density term relative to the
exponential. An initial density-in-exponent interpretation and its numerical
sensitivities were withdrawn. No numerical head/pull-through value is adopted
from that extraction. Verify the rendered equation and its final scope before
any numerical use; this is a specific source limitation, not a requirement to
replace the existing conditional material/hardware evidence wholesale.

## Qualification boundary

A test result may be a supported pass, a failed adopted condition, or a
specific unresolved resistance/method. Complete numerical assessment does
not require every result to pass. A joint is not structurally qualified while
its applicable splitting resistance remains unresolved. The published
30-duty/44-timber census remains intact; these new leaves add bounded evidence
and do not change the reviewed 104-axis authority or adopt the 108-axis
proposal.

## Coverage of the force-placement route

The published all-joint census assesses 30 duties and 44 timbers with 528
body/case/transverse-orientation states. Its 62,376 reused cleat cuts and
25,212 receiver cuts are not a complete physical boundary-field proof. In
particular, retaining six signed wrench components in a cut record does not
establish a simultaneous stress-transfer field inside the timber.

The following inventory concerns the reviewed 104-axis layout. It identifies
the missing evidence for the avoidance/transfer-field route above; it does
not require this particular route if a different applicable resistance method
is established.

| Timber scope | Existing spatial evidence | Remaining force-placement gap |
| --- | --- | --- |
| Four outer-corner cleats | Saved bore-wall pressure, washer/contact measures and 51,312 signed transverse cut limits in `corner-group-finish/attempt03`; later bottom physical-gravity correction | Preserve the top mapped-gravity limitation. These measures and cut diagnostics still do not establish fracture resistance or a complete timber stress field. |
| Six header-related cleats | Corrected historical `header-boundary/attempt06` and `header-v-cuts/attempt02`: 500 fields, 36 body/case pairs and 3,024 `v` limits; separately completed fresh `header-fresh-force-adapter/attempt02`: 36 states and 1,368 newly derived `v` limits | The fresh header mappings have zero unsupported physical rows and retain full integrated accounting. Other-interface actions remain source points and a corresponding `u` comparison is absent. Positive normal bounds remain; no splitting capacity or complete physical body boundary is established. Historical force/cut results were not transferred into the fresh adapter. |
| Two outer-knee spines | Complete point wrench and a supported-spreading-invariant opening force at one plane in `spine-opening/attempt02` | No complete reviewed-layout boundary field or both-orientation cut integration. The 108-axis bridge and annular-column evidence remain separate. |
| Twelve other cleats | Saved original-point signed cuts and normal-hull/pressure diagnostics | No complete spatial washer/contact/bore mapping. These are the two bottom-center, two top-center, four left-service, two WJ04 and two WJ06 cleats. |
| Header and top-rail receivers | Partial header-interface mapping and top-rail grain-direction pressure cuts | No complete all-interface transverse `u`/`v` field-cut result. |
| Two side and two bottom-rail receivers | Corner-interface washer/contact measures and axial bore-station resultants | The station resultants are not radial bore-wall pressure fields; no complete receiver transverse field-cut result is available. |
| Fourteen other receivers | Original-point signed cuts, plus any existing nominal group/seat checks | No complete cut-capable mapped boundary fields. These are both floors, both center posts, both outer posts, both center principals, four service rails and both lumber legs. |

The smallest next implementation reuses the existing station catalogs and
washer, contact and bore integrators. Each missing body/interface field needs
its original row ID, case, signed force/free couple, supported geometry and
exact residual at the original point. Both the interface and whole-body
six-component wrenches must recover before cut comparison. Shared knee shafts
must retain their distinct receiver interfaces without duplicating an axis.
This is postprocessing of saved actions, not authorization for a new load,
geometry or frame solve, and not a splitting qualification by itself.

The archived artifact identities below were checked directly after the
read-only inventory. The original snapshots and results remain unchanged.

| Archived artifact | SHA256 |
| --- | --- |
| Four-corner `cuts.jsonl.gz` | `a60131eaeff3e5bb46579156d31fbfe3423de2848ac2bbb202901013697a5627` |
| All-joint `receiver-cuts.jsonl` | `9ed12678cc317fac8e0797d295ee8c986e0c7033707fd27361f2c64252077381` |
| Header boundary 06 `result.json` | `7316c7bda88727c0509d5071e8a49f2b79345734f2a910d17a29c6c59f2ca9c8` |
| Header v comparison 02 `result.json` | `977f25094bf979db9aff9e234674a050b9644de2d1f40698b114808e8ef77ef8` |

## Fresh source coverage and next joins

The fresh source remains **104 global connector axes and 66 screws**, with
gravity updated for the unadopted 108-bolt planning inventory. The four added
internal `v` ties have separate static allocations and no global connector
rows. Do not describe this as a coupled 108-axis response. The authenticated
gravity assessment is `ce69ba58e3c6265d31ab0dfdec1ffac4c019b93fc1106c8f9677ed9b5b2c3f95`;
the frame comparison and response are respectively
`c3a8ff024fb494032d947aedfd6f00cda8698587b8751b2cec66e4b3af243729`
and `62bd4116cfb577a0846f4de0d43fbeec6bb704bac7feee530ee673ded1820f90`.

| Fresh archive | Proven coverage | Splitting-use limit |
| --- | --- | --- |
| `../rawlocal/knee-bridge-members/attempt01/` | 42 unchanged timbers: 20 frame receivers and 22 cleats, six cases, 252 body balances and 53,784 signed grain-normal cut traces | These are longitudinal cuts, not both transverse directions or a timber stress field. This archive explicitly records 19,872 unsupported local-section traces. |
| `rawlocal/header-fresh-force-adapter/attempt02/` | Six header-related cleats in all six cases: 36 states, 360 header boundary-action records, 1,368 finite `v` limits and zero unsupported physical rows; full integrated accounting passes | Only header interfaces are mapped; other actions retain source points. No complete physical body boundary, continuous-station envelope or splitting resistance is established. The saved normal-hull diagnostics contain 1,360 positive bounds and eight compression-only feasible results. See [the fresh results and authenticated identities](header-fresh-force-adapter.md#completed-fresh-run). |
| `../rawlocal/knee-bridge-joint-replay/attempt01/` | The two proposal spines, including full signed actions, changed six-bore geometry, grain cuts and local-`v` cuts | Its event loop covers local axes 0 and 2; local `u`/axis 1 is absent. Its 24 tie allocations and 48 ends remain separate static hypotheses. |
| `../rawlocal/remaining-block-transverse/attempt01/` | Historical all-local-axis cut records for 20 blocks | This binds the old response and old gravity factor. Reuse station/method definitions only; do not transfer its force or qualification results into the fresh source. |

For the unchanged bodies, fresh `geometry.json` and
`action-section-arrays.npz` in
`../../member-screen-attempt02/knee-bridge-gravity01/` contain the member
geometry, action IDs/roles/owners, point rows and per-case force/free-couple
arrays. The existing `actions_for` method binds those arrays to fresh scalar
reactions and complete owned `-D` rows. Its original sign and full-wrench
guards must remain active. The floor-row metadata direction requires the
separately authenticated original orientation contract when those rows are
consumed; an arbitrary sign inferred from the observed action is not evidence.

The immediate force-placement work therefore needs fresh actions joined to
applicable physical transverse stations. `remaining-block-transverse.py`
offers a station builder for rectangular stock with exactly four disjoint
cylinders; that geometry contract does not cover every receiver or the
changed six-bore spines. No generic rectangle or old cut catalog may silently
replace an unsupported finished section. A matching resistance method could
close a duty without this field route, but none is established by these joins.

Finite fields should reproduce the complete integrated action/interface/body
wrench. Their partial-cut wrenches can differ from the original point-load
cuts when a plane intersects a washer, contact cell or bore-pressure domain.
Record that signed difference; equality at every partial cut is not a valid
condition for spreading a point action onto its physical surface.

The following fresh files were hashed directly during this coverage update;
this identity check is not a producer run or a resistance test.

| Artifact | SHA256 |
| --- | --- |
| Fresh 42-body `checks.json` | `0d623eb62605ddac9aa5111e2469a1c63f4857e356fe607741fc425d5ea59e65` |
| Fresh 42-body `receipt.json` | `fa4d5f5568d53c0e4e62a74d31a814738b39a78951a4c27ae6e4c141ef5be794` |
| Fresh 42-body `same-cut-states.jsonl` | `b516e2f7e69699d5767d90563e697ca6b91f6fce1b32ecd13e0b447b1a80d7e7` |
| Fresh proposal-spine `checks.json` | `71980f983dd3466d02eb6c5f838186de4b77dc2ebe04653f66cf3f3598fbe891` |
| Fresh proposal-spine `receipt.json` | `10503afef20c8fc69c0f5b4877f8deb2794646c258b05ca63616611443c6c22b` |
| Fresh proposal-spine `mechanical-actions.jsonl` | `cfc1beb4eb94318c5d7f8ec4a6ea2cea933bc150f376c11af5d2a0408e4ab872` |
| Fresh proposal-spine `normal-cuts.jsonl.gz` | `153ba0e65a02295bfb87b57d3fb4c292d1661ed8cc46e0cf239354ef608d2d69` |
| Fresh proposal-spine `allocations.jsonl` | `5428cf793ba59c0ca1d75dbfedb62036518f29d31cefe63101df9b3d0a5bdb17` |

## Read-only six-cleat geometry options

The static header contract records all six header-related cleats with current
grain `g=+Z`, `u=+X` and `v=+Y`. Their two header bores run through `g`; their
two other-host bores run through `u`. No option below changes the reviewed
model or establishes that new hardware is required. Missing perpendicular
tension data or a point-cut bound alone cannot prescribe a physical change.

| Cleat pair | Finished `u × v × g`, mm | Header bore centers in current `v`, mm | Current outer `v` faces, mm |
| --- | --- | --- | --- |
| Center-post | 88.9 × 88.9 × 128.9 | −17.5, +17.5 | ±44.45 |
| Center-principal | 83.9 × 139.7 × 134.7 | −34.15, +30.85 | ±69.85 |
| Inner knee | 88.9 × 133.35 × 139.0 | −46.675, +46.675 | ±66.675 |

Choosing stock with grain along current `v` is geometrically meaningful. Its
new transverse section would be current `g × u`: these sections fit the
nominal 139.7 × 88.9 mm 4×6 envelope, with only 0.7 mm nominal allowance for
the knee's 139 mm dimension. The post would no longer fit 88.9-square stock.
No available or delivered stock dimension is established. All four bores
would then be cross-grain. Existing signed end/edge/spacing branches, grain
cuts, washer bearing, eccentric splitting, member resistance and size-factor
classifications need their own new evaluation. Neither the former code
size-factor assignment nor the ripped-block `CF=1` sensitivity transfers to
that orientation. This is an option for a separate study, not a solution or
an adopted reorientation.

Both current host-contact families extend along `v` at shared interface
planes. That does not create a full `v` receiver or establish washer lands,
nut access or a bore route. A cleat-only `v` bolt would have its two washers
on cleat faces; it cannot inherit a host-anchored bolt's load path. Any new
`v` axis must be checked against the existing full-`g` and full-`u` shafts.
No seam-groove detail or proposed new station is selected here, and the
separate spine annular-column result does not qualify any of these six
cleats. Required geometry/material changes must be reported before changing
the reviewed model.

The factual geometry source is the authenticated
`../rawlocal/header-local-transfer/attempt01/model.json`, SHA256
`eae4fc005cdd079f90f527be611e45a137aa275b129e16eebf964c422d69ae52`.
Its `.bodies.<cleat>.member_geometry.geometry` and
`.finished_surface_record.features` record the frames, stock and bore axes;
`.contact_patches_by_global_source_index` records the interface planes.
This geometry audit executes no producer, strength calculation, native solve
or CAD change and supplies no acceptance transfer.
