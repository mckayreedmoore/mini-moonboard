# PB-02 kerf-right center kicker support: one-post offset probe

Status: **nominal geometry trial only**. No connection capacity, purchased
bolt, cut list, assembly sequence, or drilling release is established.

## Concrete trial

Use the current frame CAD's uncut timber solids and the kerf-right stock
profiles and all 66 fixed panel/kicker axes. Leave the left center box post
at X = −89.05…−50.95 mm. Move **only the right center box post** 37.8 mm
outward, from X = 50.95…89.05 to X = 88.75…126.85 mm. Its old upright above
remains at X = 50.95…89.05, so their projected X overlap is 0.30 mm.
That sliver is **not a viable post-to-upright load-transfer detail**; a new
positive connection path is required. The header and both kicker panels
remain in place.

Trial a rectangular solid-wood 4×6 backer with the owner-specified Home Depot
actual section of 139.7 mm X × 88.9 mm Y, grain vertical and cut length
238.9 mm. Its bounds are X = −50.95…88.75, Y = −124.9…−36.0,
Z = 0…238.9 mm. The backer touches the unchanged left post at X = −50.95
and shifted right post at X = 88.75. This avoids the previous nonstandard
140.0 mm width. No glue, half-lap, custom steel, or panel-fastener change
is assumed. Actual stock section and cuts must still be measured.

## Measured results

- Both kerf-right interior kicker edges are at X = −1.5875 mm. The backer
  lies directly behind them from Z = 0…238.9 mm. The unchanged header
  lies behind Z = 238.9…277.0 mm. There is no nominal vertical support gap.
- The input still has 48 main-panel and 18 kicker axes. No start or direction
  was edited. All **18 kicker axes** were screened at their full 63.5 mm
  purchased Hillman screw length, not the historical 50.8 mm CAD length.
  All 18 modeled 4.1402 mm screw envelopes are completely in their named
  receiver (the backer replaces the right-center post for its two axes),
  with the purchased tip inside timber. The other 48 panel axes keep their
  original starts, directions, and receivers because no other member moved.
- The left fixed center kicker screws at X = −70, Z = 60/192 mm still enter
  the left post. The right pair at X = +70, Z = 60/192 mm enter the backer.
  All four tips are at Y = −81.24375 mm; each has 45.24375 mm of receiving
  timber along its axis behind the panel. The backer has 43.65625 mm of
  timber behind the right screw tips before its rear face at Y = −124.9 mm.
  By contrast, the superseded 38.1 mm-deep backer ended at Y = −74.1 mm;
  each purchased right screw would have protruded 7.14375 mm.
- Exact CadQuery intersections of the shifted post and backer with the
  remaining uncut frame solids have 0 mm³ positive-volume overlap. Face
  contacts at posts/header are not counted as interference.
- Two illustrative **10.5 mm-diameter** X-axis bores at Y = −80,
  Z = 105/145 mm pass fully through left post, 139.7 mm backer, and shifted
  right post. Nominal total wood grip is 215.9 mm. Their nearest fixed
  center-screw Z separations are 45/47 mm; the wider diagnostic bores do
  not intersect those screws. For an illustrated nominal 3/8 in (9.525 mm)
  bolt, 10.5 mm is within the 2024 NDS §12.1.3.2 hole interval
  of 10.31875…11.1125 mm. This is **not** a selected bolt, hole, or drill
  size. The backer's Y-axis distances to its front and rear edges are
  44.0 and 44.9 mm, respectively; whether a loaded-edge requirement
  applies and all other NDS conditions remain unassessed. The publicly
  accessible [AWC 2018 §12.1.3.2][awc-2018] has the
  same 1/32…1/16 in oversize wording. The full 2024 text was not accessible
  in this probe, so this is an interval check, not a complete NDS assessment.
- A 20 mm-radius, 20 mm-long straight cylinder outside each post end has
  0 mm³ intersection with other uncut frame solids at both trial bolt
  levels. Its front reaches Y = −60 mm, 24 mm behind the kicker back face.
  Real washer, nut, bolt length, socket, and installation order are untested.

The geometry can therefore preserve direct timber under both interior kicker
edges, the four center kicker screw embedments, and nominal neighboring
clearance **if** the specified 4×6 section is present. It does not prove
positive structural connection: the two long through-bolt paths merely
show a possible way to clamp the backer between both posts. Bolt grade,
thread/shank position, washer size, group spacing, edge/end distances,
wood splitting, slip, load direction, backer/header and post/header load
paths, all changed rail-end duties, and transport access still require
complete PB-02/PB-04 checks. In particular, retaining the old ML24Z/SDS
post/header connection is not assumed. This trial is not a strength or
drilling verdict.

Reproduce with `.venv/bin/python scripts/simple_center_support_offset.py`
and `.venv/bin/python -m pytest -q tests/test_simple_center_support_offset.py`.
Sources: `mini_moonboard/compact_floor_flush_frame.py`,
`docs/floor-flush-construction-kerf-right/stock-profiles.json`, and
`docs/floor-flush-construction-kerf-right/connection-axes.csv`.

[awc-2018]: https://awc.org/wp-content/uploads/2021/10/AWC_NDS2018-withCommentary_20210928_AWCWebsite_Chapter12.pdf
