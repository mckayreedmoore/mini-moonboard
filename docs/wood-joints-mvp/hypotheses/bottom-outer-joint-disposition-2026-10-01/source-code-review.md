# Independent source-code review

**Disposition:** No unresolved material source-join finding in the frozen
producer. This review covers source identity, action signs and radii, geometry
and material context, and the cleat free-body boundary. It does not establish
joint resistance or acceptance.

The reviewed [producer](produce.py) is pinned at SHA-256
`a941dceee5c002068e9920cfe41f62270e11ff399367fdf9494c445a06d8a86d`. Its local
output is pinned at `fcf393be26c433daf760a6afcf9fd6260d88f04f43a6234def960bbba4789029`.
The upstream two-receiver register remains pinned to producer
`5f2a7fdca2ef0c56c661fa10e4122189f8a7a1ae0725062cb8c56d95dd911edf` and
register `6551861db1112c91b87c5705bbceb3bb26f55f0d7e70029a74d828519425145e`.

## Source joins

The four selected rail/side bolt axes retain three-case, seven-state coverage:
84 source reference rows across 21 joint states. I compared the nested rows in
the output with the corresponding rows in the pinned upstream register; all
84 are unchanged. For each state, the producer separately rechecks the
current plane's signed force and rounding-radius vector against that prior
row, then rechecks the signed outer-seat tie against its source SPRINGA
component. Plane source ownership, receiver order, component signs, axis
directions, and action/reaction are checked by the pinned plane checker. Ties
remain separate axial actions and are not added to lateral demand.

The three contact pairs are rail/cleat, side/cleat, and rail/side. Their 12
source cells per state produce 252 cell records and 63 pair records. Each
cell is joined to one compression-only SPRINGA binding, raw inventory row,
native component, and exported action. The checker verifies receiver IDs,
element and row identity, area, point, unit normal, signed force and reaction,
and the projected native force-rounding radius. It also checks that the
native force interval intersects the serialized table interval. The
source-bound compression-only law is retained as `k * max(q_mm, 0)`; numerical
ground RF is excluded from physical actions.

The exact contact graph, its verifier and source pins, and the face-pair atlas
are hash-bound. The graph and atlas use the same candidate revision; each of
the three member pairs is recorded as a finite opposed planar touch, with
zero common volume, and its face-atlas area is checked against the graph area.
Across each patch, the four modeled cell areas also sum to that nominal
finished-face area. This supports a geometry/source mapping only; it does not
prove installed contact, pressure distribution, fit, or load sharing.

## Applicability and free-body boundary

The pinned material input record supplies a conditional DF-L No. 2 `Fc⊥` base
value of 625 psi and proposed member grain directions. The model grain
descriptors are checked against those proposed directions. The producer
reports an `Fc⊥` pressure comparison only when a cell is resolved compressive
and its face normal is perpendicular to that member's proposed grain. Open or
rounding-ambiguous cells have null comparison ratios; the parallel-grain rail
at the direct host contact has no `Fc⊥` comparison. All such values remain
unadjusted conditional context, with `bearing_accepted` false. Delivered
species, grade, grain, contact, and material are not observed.

For each state, the complete cleat boundary must equal the exact 16 source
names: eight cleat-side/cleat-rail contact cells, four lateral bolt planes,
and four separate outer-seat ties. The pinned `member_balance` helper sums
these actions and scaled body loads at the recorded cleat descriptor midpoint;
the raw and rounding-interval residuals must pass and match the frozen
all-body cleat residual. The producer includes the separate rail/side host
contact cells in its source records, but it does not calculate complete
rail-host or side-host boundaries or finished-section checks. Its output
explicitly keeps `complete_host_member_boundary_or_finished_section` false.

Two source-join gaps found during review were corrected before this hash was
frozen: open/ambiguous cells no longer receive a pressure/reference ratio,
and contact, bolt-plane, and tie rounding radii are joined to their native
components. The cleat inventory is also checked against the exact expected
set. The parent reports 15 source-corruption tests and Ruff passing on this
version. I inspected the frozen code and output structure but did not rerun
the full producer or the separate numeric verifier.

The result remains additive source attribution and conditional context only.
It does not claim an adopted capacity, fully adjusted ratio, pressure peak,
criterion pass, complete host boundary, geometry change, native solve, or
joint acceptance.
