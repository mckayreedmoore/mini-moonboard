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
| Avoid opening under the recorded forces | Supported force placement and a complete simultaneous timber transfer field requiring no perpendicular tension; retain shear and torque | The new [spine test](spine-opening.md) tests a necessary condition. The [header boundary map](header-boundary.md) studies whether spreading changes the apparent opening. Compression at selected cuts is only a normal subcheck. |
| Carry opening with a mechanical tie | Actual split-plane coverage, supported end anchorage, simultaneous steel/lateral checks and matching complete timber transfer | The [annular column](anchorage-column.md) establishes a conditional prescribed-pressure anchorage component for the four proposed ties. Its force is already counted in the proposal; no reserve or second subtraction is available. Other bolts cannot inherit this geometry/pressure result. |
| Apply a matching unreinforced fracture method | Material fracture/splitting inputs and an applicable connection/group action map | Not established for the current crossed/opposing three-dimensional duties. |

The [Franke–Quenneville CIB-W18 mixed-mode paper](https://www.irbnet.de/daten/iconda/CIB_DC31328.pdf)
offers a numerical method combining opening and sliding fracture energies
for eligible transverse dowel groups. It needs matched Mode-I and Mode-II
material inputs and does not automatically cover axial washer anchorage or
an entire crossed timber joint.

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
| Six header-related cleats | Corrected `header-boundary/attempt06` and `header-v-cuts/attempt02`: 500 fields, 36 body/case pairs and 3,024 `v` limits | The header-interface integration has no unsupported field or body-scope stop, but other-interface actions remain source points and a corresponding `u` comparison is absent. Positive normal bounds remain; no splitting capacity or full-body field is established. Fresh 108-axis forces need their own adapter. |
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
