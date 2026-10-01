# Current corner timber contact pressure screen

This bounded screen extracts modeled average contact-cell pressure and signed
pair force/moment resultants for seven timber interfaces among the five left
outer-corner bodies. It uses the authenticated `a12-rear`, `a1-rear`, and
`k12-rear` exports selected by the
[current six-case register](../current-six-case-corner-response-register-attempt04/register.json).
Each case contributes its seven recorded increments. The output contains 588
cell states and 147 four-cell pair resultants.

The [source pins](source-pins.json) freeze the register, its producer, the
three case models, responses, corner exports, input decks, native DAT files,
and execution records by SHA-256. The replay checks these hashes against the
register before reading forces. For each cell it also checks the model owner,
source row ID, area, point, normal, exported force, native SPRINGA scalar end
force, and opposite endpoint force. It checks the four-cell areas and scalar
force sums against the authenticated corner report.

For a cell, the reported modeled average pressure is the native SPRINGA
compression force divided by the source modeled contact area. This is a
discrete spring-cell average, not a resolved pressure field. Each cell retains
the scalar force and its rounded interval, q elongation and interval, both
physical end-force vectors and their component intervals, and its active,
open, or ambiguous state. A zero force with a wholly negative q interval and
zero native force-table interval is classified as open. A positive force
interval is active; unresolved contact at the rounded boundary remains
ambiguous.

Pair forces sum the four source end-force vectors on each member. Pair moments
sum `(contact point − datum) × force`; the common datum is global XYZ
`[0, 0, 0]` mm. The JSON retains signed wrench components on both members and
rounding intervals propagated from the native force output. Moment values are
therefore transported to that global datum and include the coordinate lever
arm.

Across the 588 cell states, 182 are force-resolved active, 406 are open, and
none are ambiguous at the stored rounding precision. The largest cell average
is **0.513415586831 MPa** (rounded interval
`[0.513415549255, 0.513415624407] MPa`) at `a1-rear`, load factor 1.0,
`header-post/contact_10_0` (SPR41): 683.1726 N over 1330.6425 mm². At that
same increment the header-post resultant on `base_header` is
`[0, 0, 1125.1053] N` with moment about the declared datum
`[-110667.09, 1339578.50, 0] N·mm`; the `base_post_outer_left` wrench is equal
and opposite. These are conditional numerical demands for this model and
load case, not allowable limits.

No contact-pressure peak or wood-strength acceptance is calculated. The
candidate blocks have no sourced bearing-strength basis. Actual member grade
and properties, built contact faces and support area, fit or gaps, local
pressure distribution, and a complete bearing/crushing resistance method are
missing. The screen does not establish that any actual wood or interface
matches the modeled inputs, and it does not accept a joint or the candidate.
The three load cases also remain conditional on their stated support branches.

Rebuild the saved output or verify it from the repository root:

```sh
python3 docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/current-corner-timber-contact-pressure-screen-attempt01/replay.py --write
python3 docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/current-corner-timber-contact-pressure-screen-attempt01/replay.py --verify
```

`screen.json` contains every cell force, average pressure, rounding interval,
state, and pair wrench for all 147 pair/load-increment combinations across 21
case increments. The replay
does not launch a native solver or change source model geometry.
