# Four-corner splitting and group-resistance applicability

**Decision: APPLICABILITY complete.** NDS 2024 §§3.8.2 and 11.1.2–11.1.3 govern the transverse opening/load-path question. The cached sources provide no numerical resistance for the complete crossed bolt duties. Retain the completed conditional nominal comparisons; splitting capacity remains unassigned and complete-joint acceptance remains false. This is a source/applicability disposition, not a physical failure finding.

## Frozen basis

Read [normal-transfer closure](corner-split-closure.md) and the completed [physical-gravity and grain follow-up](corner-physical-gravity.md) first. Geometry, first-order forces, smooth-shank hypothesis and existing material references are unchanged.

| Frozen checks | SHA-256 |
| --- | --- |
| [Bottom physical gravity and recomputed grain comparisons](rawlocal/corner-physical-gravity/grain-attempt02/checks.json) | `e11c2c469c6ef8a8582f5117231d72cfa148c0780de2e5e0ef9fb8365c2492db` |
| [Top first-order physical forces](rawlocal/corner-first-order/attempt01/checks.json) | `b15b57d3879fdca2dac607d11a2ad127acd1008f6c2a6f546333a1b26c754cfe` |
| [Four-corner nominal group assessment](rawlocal/corner-group-finish/attempt03/checks.json) | `2ae3a84f273823dc6ca751e6fdddab8e0d70425ee7b34e1e38ebc79d5b672f23` |

Top transverse witnesses retain their recorded gravity mapping; no uniform top replacement is adopted. Original mapped-gravity **0.165250430 N** remains historical evidence for its frozen inputs.

## Actual opening direction and existing route

Current physical bottom gravity leaves 100 positive cut limits, all bottom right / A12-rear / `u`-normal. The maximum **0.054537792 N** occurs at `u=1.252397256527047 mm`, before the event. It requires separation resistance along local `u` (global X), perpendicular to grain, across the grain-parallel `v`–grain plane. It is a minimum tensile resultant under unbounded point pressure, not a bolt demand or a resistance comparison.

With plane coordinates `p=v`, `q=grain`, its full signed `[N,Vp,Vq,T,Mp,Mq]` is:

```text
[-2.639141681, -2.290576589, 0.794998442,
 89.176155067, -112.776975093, 122.158257464]  (N, N·mm)
```

The minimizing tensile witnesses sit at `v=-44.45 mm` at both grain ends; compression totals 2.693679473 N at the opposite edge. Actual side bolts run along `u`, at `v≈-16.45/+16.55 mm`, grain station ≈59.85 mm. They cross this plane through the cleat nut washer, shaft, side-host head washer and opposing host/cleat contact route. They are not independent two-washer ties wholly inside the cleat. Rail shafts run along `v` and supply no axial tie crossing this `u`-normal plane.

Existing side-bolt tensions 3.418451131/0.494036973 N and their inward washer reactions are already counted. They are not reserve reinforcement. Restricted tie positions and finite bearing can require more transfer than the hull minimum; any justified redistribution must preserve the simultaneous shears, torque and both bending moments above.

## Published criterion decisions

| Primary criterion | Decision for these duties |
| --- | --- |
| [NDS 2024 §3.8.2, p.24](https://web-media.awc.org/wp-content/uploads/2021/12/17210019/AWC_NDS2024_withCommentary_20240718_AWCWebsite_Chapter-3-Design-Provisions-and-Equations.pdf) | Applicable to the necessary perpendicular opening. It directs avoidance where possible and consideration of sufficient mechanical reinforcement where unavoidable; it supplies no sawn-lumber `Ft_perp` or universal through-bolt reinforcement capacity. |
| [NDS §§11.1.2–11.1.3, p.70](https://awc.org/wp-content/uploads/2026/09/AWC_NDS2024_withCommentary_20260911_Website_Chapter-11-Mechanical-Connections.pdf) | Applicable to local multiple-fastener mechanics and eccentric connections inducing perpendicular tension. An appropriate engineering procedure can establish the route; the clause does not require a new physical test in every case or supply a scalar splitting capacity. |
| [NDS Appendix E.1–E.3, pp.174–175](https://awc.org/wp-content/uploads/2026/09/AWC_NDS2024_withCommentary_20260911_Website-Appendix.pdf) | Applicable only to the recorded longitudinal channel comparisons: `Z'RT,i=n_i Fv' Acritical/2`, using two shear lines once. The rail pair is one grain row; side bolts are separate rows. Existing grain/net-section and E.3 comparisons remain conditional nominal results, not resistance to `u`-normal opening. |
| [Appendix E.4, Eq. E.4-1 and E.4.1](https://awc.org/wp-content/uploads/2026/09/AWC_NDS2024_withCommentary_20260911_Website-Appendix.pdf) | Parallel-grain group tear-out uses half each bounding-row resistance plus `Ft' Agroup-net`, checking alternate critical groups for unequal row spacing. No qualifying common group-net path/action assignment for all four orthogonal bolts is established. Summing E.3 channels supplies neither that assignment nor a transverse capacity; obtaining an area alone would not resolve the direction/interaction mismatch. |
| [NDS §11.3.6, p.74](https://awc.org/wp-content/uploads/2026/09/AWC_NDS2024_withCommentary_20260911_Website_Chapter-11-Mechanical-Connections.pdf) | `Cg` adjusts lateral resistance for applicable same-diameter rows aligned with load. Preserve existing component use; it is not a splitting resistance or an additional four-bolt redistribution rule. |
| [EC5 §8.1.4, AC:2006 correction, p.4](https://cms.sia.ch/en/api/getMedia/559), corroborated by [JRC connection slides 63–64](https://eurocodes.jrc.ec.europa.eu/sites/default/files/2022-06/EN1995_5_Leijten.pdf) | `F90,Rk=14 b w sqrt(he/(1-he/h))` is a Figure 8.1 beam-connection scenario with demand from the maximum section shear on either side. For possible rail-induced `u` opening, the candidate Figure plane is grain–`u`, normal to rail axis `v`: `h` follows `u`, `b` follows `v`, and demand would use the `u` shear on grain-normal cuts bracketing the connection. The 0.054537792 N normal-cut bound is not that demand. |

The complete crossed block simultaneously receives orthogonal bore forces, axial washer actions, face contacts and couples. Those actions do not establish one EC5 Figure 8.1 loaded edge/`he` or an independent beam-splitting duty. The cache contains a corrigendum and official training reproductions, not the complete normative clause; these give no combined crossed-group rule. Thus the EC5 scalar is **inapplicable as the complete-block criterion under the recorded assumptions**; short grain length alone is not the exclusion. No characteristic-to-design conversion is adopted.

## Finite missing resistance and disposition

The unresolved quantity is supported resistance to separation across the actual bottom-right `u`-normal timber path under the recorded simultaneous tangential actions, or supported existing-side-bolt/host reaction redistribution that removes that timber opening requirement. For the latter, the missing datum is an admissible reaction allocation at the actual bolt/washer/contact positions, with its combined bolt and anchorage resistance. Present fixed reactions and hull points supply neither. Comparing 0.0545 N with existing bolt tension would double-count; requesting an NDS `Ft_perp` would request a value the source does not publish.

This finite capacity/path gap remains an explicit unqualified local-cracking assumption for the simpler conditional MVP. All recorded longitudinal reference comparisons, including the recomputed bottom grain results, remain below one within their stated hypotheses. Compression witnesses establish normal equilibrium only; they establish neither elastic compatibility nor crack shear/torque resistance. No complete crossed-group pass or physical qualification follows, and no blanket new prerequisite is added.

The cited PDFs were read from existing caches and their frozen digests matched the existing [AWC source bounds](../../upper-block-strength-2026-10-01/source-cache/source-bounds.json) and [EC5 source pins](../../upper-outer-load-path-2026-10-01/splitting-source-cache/source-pins.json); Chapter 3 matched `205df74e16f632dfe78211e99bfa5dfa8b9f8dd316e9c5fa1316493f795ec644`. No new models, capacities, preload, friction, SPAX transfer, tests or runs were introduced. Existing evidence remains active; this note adds no raw artifacts to archive. Remaining-20 applicability belongs to its separate task.
