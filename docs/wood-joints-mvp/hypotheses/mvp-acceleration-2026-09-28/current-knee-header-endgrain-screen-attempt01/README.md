# Current knee block/header end-grain lateral screen

BG045 is the left outer knee's onward block/header connection, containing
`knee_outer_left_inner_header_1/2`. It is separate from the post/spine pair
BG001 and the three-member spine/side/block stack BG003. This source-bound
screen addresses the missing end-grain lateral method branch. It supplies no
accepted case demand, joint capacity, or fabrication instruction.

The modeled shafts are 6.35 mm. Both have 139 mm bearing length in the inner
frame block and 38.1 mm in the header. Their head directions are opposite;
head direction does not determine structural main/side roles. The proposed
block grain is parallel to the bolt axes; header grain is perpendicular.

Under the explicit scenario that the block is the eligible NDS main-member
end-grain receiver and the header the side member, reuse the reviewed
[NDS method](../nds-screen/README.md): §12.3.3.4 uses perpendicular-grain main
bearing, and §12.5.2.2 applies `Ceg = 0.67`. Assumed full-body quarter-inch
bolts have 45,000 psi bending yield; rounded bearing strengths are 4,450 psi
perpendicular and 5,600 psi parallel. These are conditional inputs, not
delivered properties. The original perpendicular-to-both-grains screen
excluded this branch; that exclusion did not establish a prohibition.

| Lateral direction | Single-bolt reference before Ceg | Reference with Ceg only |
| --- | ---: | ---: |
| Global X, parallel to header grain | 599.457 N | 401.636 N |
| Global Y, perpendicular to header grain | 567.848 N | 380.458 N |

Mode IV governs both scenarios. The producer checks all six yield modes using
the reviewed TR12 helper and independently checks the mode-IV closed form.
It verifies both modeled receiver lengths, grain relationships, and upstream
geometry hashes. Other adjustments, group sharing, spacing/end/edge effects,
splitting, axial actions, washer seats, actual shank occupancy and complete
transfer remain unassessed. Do not multiply either value by two or treat
opposite modeled bolt orientations as independent joint capacities.

The exact next demand input is the signed full wrench on this block/header
interface for each case, expressed at a stated datum with action/reaction
signs, together with its simultaneous BG003 actions. Those inputs determine
whether either pure lateral screen applies and what combined or axial checks
are needed. The known end-grain-axis geometry alone is neither a pass nor a
physical failure finding.

Reproduce from the repository root:

```sh
python3 docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/current-knee-header-endgrain-screen-attempt01/produce.py --verify
```

The JSON pins the reviewed helper, scenario source and geometry inventory and
retains the official NDS Chapter 12 URL/PDF hash from the reviewed source
packet. No geometry, native solve, mesh, criteria or release state changed.

Parent checked the local primary-source PDF on September 29: its SHA-256
matched `5fc837523ff10acc097a162718700a9b4ba64e627d2b0023439146d42fe4ee2a`,
and extracted §§12.3.3.4 and 12.5.2.2 directly. Their diameter, main-member
axis/grain and Ceg conditions match the stated scenario. The online PDF
reader was unavailable; no claim of a fresh remote-byte comparison is made.
