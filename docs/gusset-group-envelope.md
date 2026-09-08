# Conditional two-interface gusset transfer

Each side gusset connects two bolts to the inclined rim and two different bolts
to the vertical post. It is not one four-bolt interface. The actual upper pair
is 80 mm apart; the lower pair is 140 mm apart. Their centroids differ by
90 mm in world Y and 240 mm in world Z.

The conditional in-plane model applies force `(FY,FZ)` and moment `MX` at the
upper pair centroid. It assumes equal lateral stiffness within each pair,
rigid gusset behavior, no other gusset load and no friction. The lower pair
must transmit opposite force and moment
`-MX - 90*FZ + 240*FY` in Nmm. Thus even zero upper-centroid moment generally
requires a lower-interface moment. Both pairs and the whole gusset are checked
for force/moment equilibrium.

Using the unadjusted, conditional [single-bolt reference](two-member-bolt-yield.md),
the first bolt reaches its reference value at these separate basis magnitudes:

| Upper-centroid input, others zero | Conditional basis scale, either side |
| --- | ---: |
| FY | 344.27 N |
| FZ | 537.92 N |
| MX | 49.18 N·m |

These are not simultaneous allowances, actual demands, adjusted group capacities
or a frame rating. The equal-stiffness assumption is not established by measured
joint slip and is not a proven worst-case distribution. Group-action, hole/edge
geometry, splitting, net section, bolt axial action and material/installation
gates remain. The gusset can also exchange forces through contact excluded here.

For combined inputs, superpose the **signed bolt-force vectors** from
`fea.gusset_group_envelope.build()` and then evaluate each resultant. Do not
compare independent component maxima against all three table entries and declare
a pass. The outputs use world Y/Z for both sides; the bolt drilling direction
does not reverse the physical load convention.

The present aggregate base FEA output cannot supply this upper-pair wrench:
it includes bearing and other load paths. Isolate that transfer before making
a demand/resistance claim or resizing the gusset. This calculation changes no
CAD or hardware selection.

```sh
uv run pytest -q tests/test_gusset_group_envelope.py tests/test_two_member_yield.py tests/test_dowel_yield.py
```

Seventeen tests passed September 8, 2026, including hand solutions, actual
interface ownership, centroid offset, mirror consistency and global equilibrium.
