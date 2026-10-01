# Current frame carrier law inventory

This input-only map identifies the exact constitutive rows that a verified
native method would have to implement to recover corner demands. It uses the
frozen C11 **input**, not its rejected response or historical active states.
Physical owners, force bases, attachment datums, stiffnesses and node/element
identities are preserved. No deck or native launch is produced.

Run `python3 produce.py` from any directory. The source SHA is pinned in the
producer. The producer verifies complete recorded spring coverage, isolated
auxiliary DOFs, each floor normal's two paired tangential components and
the disjoint 92 new attachment / 12 retained original bolt inventories.

| Intended law | Scalar components |
| --- | ---: |
| Compression only | 1,122 (1,022 timber/panel cells + 100 floor cells) |
| Tension only | 170 (104 bolt outer-seat ties + 66 parametric screw ties) |
| Bilateral lateral | 348 (192 new-bolt + 24 retained-bolt + 132 screw) |
| Conditional all-bearing floor tangents | 200 |

The 192 new-bolt lateral components are 96 shear planes on 92 physical axes;
three-member arrangements retain their two planes and one outer-seat tie per
physical bolt. The 104 bolt ties are exactly the union of the 92 new and 12
retained axes. This inventory reuses original bolt modeling without repeating
its unchanged resistance qualification. It does not accept new demands.

With `delta = u_first - u_second`, intended internal spring force is
`k min(delta,0)` for both the current compression and tension helpers, and `k delta`
for bilateral carriers. Both helpers engage for `u_second-u_first > 0`;
axial ties use the ordered head-to-nut or wood-to-panel projection. The
physical mechanism name does not determine the algebraic branch. This is
checked against `current_response_run.axial_tension_state` and
`horizontal_panel_frame.assess`. Physical force on the first endpoint is the negative
of internal force, transformed by the preserved physical owner basis.
The table-law checks at -0.1, 0 and +0.1 mm are mathematical sign checks,
not native verification.

The floor tangents can only describe a conditional all-bearing branch if the
compatible response gives **strictly positive** normal force at every paired
cell, throughout any history for which stick is claimed. Any opened cell
invalidates that hypothesis. No general release/recontact/reference-capture
algorithm is supplied. The aggregate wrench witness does not establish this
compatibility. The failed nonlinear native coupon remains failed; no frame
readiness, method acceptance, capacity or complete-corner acceptance follows.
