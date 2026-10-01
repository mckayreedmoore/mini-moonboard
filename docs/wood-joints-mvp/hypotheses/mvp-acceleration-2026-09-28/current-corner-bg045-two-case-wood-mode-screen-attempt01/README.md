# BG045 two-case signed wood-mode screen

Status: **source-bound conditional direction and component screen only**. This
packet screens the two BG045 bolts in the separately accepted numerical
`a12-rear` and `a1-rear` responses. It is not a wood design check, full-joint
acceptance, or fabrication/climbing release.

Reproduce the values and check all source hashes from the repository root:

```sh
python3 docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/current-corner-bg045-two-case-wood-mode-screen-attempt01/produce.py --write
python3 docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/current-corner-bg045-two-case-wood-mode-screen-attempt01/produce.py --verify
```

The first command writes [`screen.json`](screen.json); the second verifies it
against the pinned demand reports, models, case response audits, geometry,
grain maps, and reviewed NDS/TR12 helper sources. Both response reports pass
their case gates and contain seven audited increments; each final increment
reaches load factor 1.0 and closes all five corner bodies. The underlying reports
remain numerical demand inputs only; neither accepts the joint.

## Signed force and geometry result

The source-proposed header grain is +X. The inner block grain and BG045 bolt
axes are +Z. Thus every lateral BG045 action is entirely across the block
grain. On the header, the A12 components point toward −X and −Y at both bolts.
In A1, the bolts oppose in X and both act toward +Y; their group resultant is
mostly across the header grain. The block receives the equal-and-opposite
actions.

| Case / axis | Header lateral action (N) | Header angle to grain | Header envelope boundary selected by force component | Block lateral action (N) | Block selected X/Y edge distances | Block comparison to conditional 4D = 25.4 mm | Conditional Mode IV reference after Ceg; resultant ratio |
|---|---:|---:|---|---:|---:|---|---:|
| A12 / `inner_header_1` | (−89.016, −14.035, 0) | 8.960° | −X end 133.35 mm; −Y edge 113.35 mm | (+89.016, +14.035, 0) | +X 44.45; +Y 20.00 mm | +X first ray face: 44.45; +Y component face: 20.00, below 4D | 401.080 N; 0.22468 |
| A12 / `inner_header_2` | (−24.272, −5.761, 0) | 13.353° | −X end 133.35 mm; −Y edge 20.00 mm | (+24.272, +5.761, 0) | +X 44.45; +Y 113.35 mm | +X first ray face: 44.45; other component face: 113.35 | 400.416 N; 0.06230 |
| A1 / `inner_header_1` | (+17.472, +61.591, 0) | 74.163° | +X end 2301.875 mm; +Y edge 26.35 mm | (−17.472, −61.591, 0) | −X 44.45; −Y 113.35 mm | −Y first ray face: 113.35; both component faces at or above 4D | 381.921 N; 0.16763 |
| A1 / `inner_header_2` | (−50.096, +71.224, 0) | 54.879° | −X end 133.35 mm; +Y edge 119.70 mm | (+50.096, −71.224, 0) | +X 44.45; −Y 20.00 mm | −Y first ray face: 20.00, below 4D by 5.4 mm | 387.093 N; 0.22495 |

Distances are to the source model's rectangular envelope, from each exported
axis center. They are not verified finished cut or edge distances and are not
an NDS minimum-distance pass. The A12 header group lateral resultant is
115.004 N at 9.912° to its proposed grain; A1 is 136.763 N at 76.199°. Those
group sums are descriptive only and are not group capacities or complete
member-section forces.

## Conditional NDS end/edge detailing comparison

For a named **conditional** smooth 1/4-in bolt (`D = 6.35 mm`), NDS-2024
§12.5.1.3 sends `D ≥ 1/4 in` dowels to Table 12.5.1C/12.5.1D. Table
12.5.1C gives a 4D loaded edge and 1.5D unloaded edge for loading
perpendicular to grain; here those are 25.4 mm and 9.525 mm. The block's
entire lateral action is perpendicular to its proposed +Z grain, so this
directional table category is relevant to the block in this scenario.
Section 12.5.2.2's `Ceg = 0.67` lateral-reference adjustment does not waive
the §12.5.1.3 detailing provisions.

The source-envelope block comparison emits both signed component faces for
each axis and the first face intersected by each signed rectangular ray. The
ray is geometry context, not a prescribed NDS selection rule for an oblique
force. A1 axis 2 and the A1 two-axis group resultant both point toward −Y;
that face is 20.0 mm from the axis, or 3.1496D, 5.4 mm below conditional 4D.
This is the strongest potential conditional detailing shortfall in the four
axis/case combinations. A12 axis 1 also has a +Y component toward a 20.0 mm
face, below 4D, but its per-axis and group rectangular rays first meet +X at
44.45 mm. The +Y value is retained as a conservative component-face
sensitivity; it is not treated as an independent second NDS loaded edge.
Neither comparison is an adopted joint failure, a verified finished-distance
finding, or an instruction to change the geometry. Actual applicable edges
and distances require the completed joint's force/detail interpretation and
finished profile. The 5.4 mm is only the normal-distance gap to this named
conditional 4D comparison; it specifies neither a bolt-axis offset nor an
edge increase and directs no geometry change.

The header comparisons remain component sensitivities because both full
header lateral vectors are oblique to +X grain. Its isolated Y component
points toward a 20.0 mm edge for A12 axis 2 (below 4D) and 26.35 mm for A1
axis 1 (0.95 mm above 4D); these do not establish a complete mixed-action
Table 12.5.1C check. The conditional parallel-to-grain end comparison is
also emitted: all source-envelope X end distances toward the signed X
components are at least 133.35 mm, above the 44.45 mm 7D parallel-softwood
tension scenario and 25.4 mm 4D compression scenario. Action classification
and delivered geometry remain conditional, so this is not a pass for the
header or joint.

The one-bolt lateral references reuse the reviewed six-mode NDS/TR12 method
with the conditional end-grain roles: inner block as main member, header as
side member, 1/4-in smooth full-body bolt, 139 mm/38.1 mm bearing lengths,
zero gap, `Fyb = 45 ksi`, conditional DF-L No. 2 `SG = 0.50`, angle-dependent
bearing values, and `Ceg = 0.67` applied once. Mode IV governs each result.
The largest component ratio is 0.22495 for A1 axis 2. It is an individual-bolt
component comparison; the packet does not sum bolts, assert load-sharing or
mixed-direction interaction, apply other design factors, or accept the joint.

## Seats, contact, and failure-mode fit

Each positive bolt-tie demand loads its two washers in compression: the force
on the base header is +Z, perpendicular to its proposed +X grain; the force on
the block is −Z, parallel to its +Z grain. This distinction is material:
`Fc_perp` does not apply to the block washer seat. The block has no assigned
parallel-compression strength here.

For the header seats only, the JSON carries a comparable what-if using the
existing minimum-annulus dimensional scenario for a Type A Wide 25NWUS lead
(213.628 mm², not selected or delivered) and the conditional unadjusted
DF-L No. 2 `Fc_perp = 625 psi` reference (920.570 N). The resulting ratios are
A12: 0.12964 and 0.02160; A1: 0.01035 and 0.10694. This assumes a fully
supported washer annulus and uniform average pressure. It does not check
washer steel bending, support geometry, real pressure distribution, or
adjusted resistance.

The four modeled header/block contact cells carry zero normal force in A12.
In A1, one carries 76.938 N of compression: the action on the header is −Z,
perpendicular to header grain, and the equal/opposite force on the block is
+Z, parallel to block grain. Its reported 0.02615 MPa is only a model-area
average over 2941.614 mm², not a local wood stress or resistance.

The applicability screen reaches these bounded findings:

- NDS §§12.1 and 12.5.1 end/edge detailing is relevant. The conditional
  1/4-in/Table 12.5.1C comparison identifies the A1 axis-2/block −Y face as
  20.0 mm versus 25.4 mm (4D), a potential 5.4 mm source-envelope shortfall.
  The A12 axis-1/+Y component also falls below 4D but is only a conservative
  face sensitivity because the geometric ray reaches +X first. The oblique
  header comparisons are component sensitivities. These are not adopted
  failure/pass findings because finished geometry, bolt, bore, and
  applicable loaded-edge interpretation remain conditional.
- A12 has a substantial header-grain-parallel component and a smaller
  cross-grain component. A parallel-group component could be screened only
  under explicit Appendix E geometry/action assumptions; the bolt pair is
  spaced across header grain, and the source does not establish a pure
  parallel group or its critical net section. A1's axis actions oppose in X
  and the group resultant is cross-grain-dominant. Appendix E.1–E.3 net
  tension and row tear-out are therefore not calculated as BG045 capacities
  for either case. A header E.2 candidate would also need a demonstrated
  parallel tensile member action, the complete net section through all bores
  and cuts, and adjusted `F't`.
- On the block, BG045 lateral forces are fully cross-grain and its ties are
  parallel-grain compression. Neither supplies an Appendix E parallel
  tension or row-tearout action. The inherited local-wood screen's 11,766.458
  mm² block candidate net section is geometry only; it is not a signed tension
  demand. Simultaneous BG003 and other section actions remain necessary for
  any member net-section assessment.
- Cross-grain splitting remains an unresolved mode for both receivers. The
  action vector is not itself a tension-perpendicular splitting demand. The
  reviewed basis finds no general NDS splitting equation for this altered
  end-grain block/header topology; the existing EC5 Figure 8.1 source screen
  also does not establish that layout's applicability. No splitting
  resistance or pass/fail is assigned.

## Sources and limits

The report inherits the official AWC NDS-2024 Chapter 12 PDF pin
`5fc837523ff10acc097a162718700a9b4ba64e627d2b0023439146d42fe4ee2a` and the
official Appendix E PDF pin
`99b0a54e7133b3cf6dd156d8fe864c1717c951487bf5baa99c34da9a68a6bbb7` from the
reviewed local packets. See the [AWC 2024 NDS page](https://awc.org/resources/2024-nds/),
[official Chapter 12 PDF](https://awc.org/wp-content/uploads/2026/08/AWC_NDS2024_withCommentary_20250328_WebsiteChapter-12-%E2%80%93-Dowel-type-fasteners.pdf),
and [official Appendix PDF](https://web-media.awc.org/wp-content/uploads/2021/12/17210019/AWC_NDS2024_withCommentary_20240719_AWCWebsite_Appendix.pdf).
The Chapter 12 PDF bytes were locally checked against the pinned digest and
printed pages 98–100 (§§12.1.2.1, 12.1.3.4, 12.5.1.3, Tables 12.5.1A/C,
and §12.5.2.2) were reviewed for the comparisons above. The text defines edge
distance normal to grain and the loaded edge for perpendicular loading, but
does not state a universal ray-intersection formula for an oblique in-plane
force.
The Appendix E scope and precedent calculation are recorded in the
[source-pinned BG001 screen](../current-bg001-appendix-e-parallel-row-screen-attempt01/README.md).
The grain and net-section limits are recorded in the
[local wood geometry screen](../current-corner-local-wood-screen-attempt01/README.md)
and [wood limit-state basis](../../../wood-limit-state-basis.md).

All results are conditional on the source-proposed grain and modeled member
geometry. Actual timber grade/species/condition, cuts, bore fit, fasteners,
washers, bearing support, service factors, and full joint resistance remain
unverified. The twelve original LEG/FLOOR-RUNNER arrangements and BG001/BG003
resistance work are outside this BG045-only screen.
