# BG001 outer-spine hole-row cut: local action distribution gap

This bounded screen identifies why the existing a12-rear result cannot yet
support a net-section or splitting check at the first BG001 row. It does not
reopen the completed whole-body response audit or compute a resistance.

The candidate geometric cut is the global XY plane at `z = 171.45 mm` through
the `knee_outer_left_spine` X-bore center for
`knee_outer_left_post_1`. The pinned section-geometry row gives gross area
`5322.57 mm²`, candidate net area `5036.82 mm²`, and a uniform axial-stress
coefficient `1 / A_net = 0.0001985379664 MPa/N`. That is geometry only. The
same source labels the plane “XY at each distinct modeled X-bore center;
normal to proposed +Z grain.”

At full a12-rear load (`time=1`, `load_factor=1`), the exported connector row
`knee_outer_left_post_1/plane-35` (`SPR1391`, `SPR1392`) applies
`Fz = -260.9994 N` to the spine at `[-1219.2, -137.6, 171.45] mm`—exactly in
that candidate cut plane. The outer-seat tie `SPR1771` is also represented as
a point action in the same plane. The solid model records this member as
`GROSS_RECTANGULAR_C3D20` with `gross_cut_and_bore_stiffness_modeled=false`.
So the model contains neither a bore-resolved stress field nor a distributed
bolt-bearing traction through the timber that could be integrated across this
cut.

The reproducible check forms the lower-spine free body from its source nodal
loads and exported interface point actions. Including the actions exactly on
the plane gives `sum(Fz_external) = -54.379094 N`, hence a one-sided section
resultant `+54.379094 N`; excluding the plane actions gives
`sum(Fz_external) = +206.620306 N`, hence `-206.620306 N`. The `260.9994 N`
change equals the unresolved point connector's normal component and reverses
the inferred sign. These are two bookkeeping sides of a concentrated load,
not two physical section-demand estimates. Assigning the connector wholly to
either side would invent the bearing distribution at the bore.

The minimum next input for this cut is a load-transfer representation that
resolves bolt/bore bearing over the timber thickness (or an independently
audited section-resultant/stress output from a model with the cut geometry and
that transfer resolved). Only then could the local section action be matched
to the candidate net plane. The existing local-wood screen names NDS-2024
Appendix E.2's net-tension component `Z'_NT = F'_t A_net` only if applicability
to the actual member action and net plane is demonstrated. A resistance
comparison would additionally need the selected member's applicable adjusted
`F'_t` and a supported method for combined section actions; the current
geometry screen expressly leaves those unset. No splitting capacity is
inferred from the area or point forces.

The source pins and calculations are in `check.py` / `check.json`. Reproduce
from the repository root with:

```sh
python3 docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/current-bg001-spine-hole-row-cut-gap-attempt01/check.py
```

Status is a bounded local-action distribution finding only. It is not a joint
acceptance, member-strength check, fabrication release, or climbing release.
