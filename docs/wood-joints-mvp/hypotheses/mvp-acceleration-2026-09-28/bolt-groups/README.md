# Candidate bolt geometry groups — 2026-09-28

This packet inventories the 92 candidate bolt axes in attempt04 by source
station and full geometric receiver membership. It is geometry evidence for
local method checks. It does not add acceptance or readiness claims and does
not run a solver or regenerate CAD.

## Reproduce

From the repository root, run:

```sh
python3 docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/bolt-groups/produce.py --verify
```

The script uses only the Python standard library. It checks the three source
pins below, reconstructs every artifact in memory, runs its conservation and
independent geometry checks, then compares all five outputs byte-for-byte.
To write/rewrite the outputs after reviewing those pins, use `--write`.
The script writes only beside itself.

## Pinned inputs

| Input | SHA-256 |
| --- | --- |
| `docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-full-frame-input-manifest-attempt04/current-full-frame-input-manifest.json` | `9e682e28c3d4c3c0594863f82c6b74d19dee2700f3856d34e1a26f69082e4f11` |
| `docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-block-material-frame-map-attempt02/material-frame-map.json` | `8705b8f100a2d3355c236fc19e6798bb7ad4862ba2d51826cf63a88db1285480` |
| `docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-frame-timber-material-frame-map-attempt01/current-frame-timber-material-frame-map.json` | `f867b4926ed23c9f356005c134778e138c8b1230547f0b69be7c3f9bc2a42409` |

Attempt04 supplies the candidate bolt centers, axes, modeled shaft diameters,
receiver intervals, station IDs, full receiver-member sets, and geometric
pair associations. The block map supplies each candidate block's conditional
source-proposed grain direction; the frame map supplies each timber's
conditional source-proposed longitudinal grain direction. Those directions
are proposals, not observations of delivered stock, grain, or ring orientation.

## Grouping and measurements

A two-member geometry group has the same source `station_id` and exact pair of
receiver members. A three-member receiver set stays one three-member stack;
its three member-pair associations are listed as a crosswalk and are not
expanded into three overlapping bolt groups. Of 92 axes, 88 have two receivers
and four belong to the two three-member stacks. The inventory contains 46
groups: 44 two-member groups and two three-member stacks. Each group contains
two axes.

The source leaves `station_id` null on 24 axes. For those rows, the inventory
keeps the null visible and uses `family`, `trial_id`, and the full receiver set
as a grouping fallback. Twelve groups use this fallback; it does not recover
an absent station identifier.

Each candidate axis is recorded once with its center, modeled diameter, and
unit head-to-nut axis. Each axis/receiver incidence reports the unsigned acute
axis-to-proposed-grain angle. The descriptive parallel flag marks angles at
or below 1 degree; this threshold only helps locate geometry for review.
For each two-axis group, the spacing table keeps three geometric quantities
separate. `center_spacing_euclidean_mm` is the Euclidean distance between the
two modeled shaft-center points. `axis_a_reference_signed_component_mm` is
the signed center-delta component along bolt axis A. When the two bolt axes
are parallel or antiparallel within 1e-6 degrees, `perpendicular_inter_axis_pitch_mm`
is the remaining centerline distance in the plane normal to those axes. No
perpendicular pitch is emitted for nonparallel axes. The table also reports
signed and absolute center-delta projections along each receiver's proposed
grain direction, with the residual component normal to that grain direction;
those grain-based components are separate from bolt-axis pitch.

All 46 axis pairs meet the parallel-axis tolerance. The Euclidean shaft-center
distances range from 33.0 mm to 95.93 mm; perpendicular inter-axis pitches
range from 33.0 mm to 93.35 mm. For the left and right knee inner-header
pairs, the modeled axes are antiparallel, the Euclidean center distance is
95.93 mm, the axial center offset is 22.098 mm, and the perpendicular
inter-axis pitch is 93.35 mm. That axial component reflects different modeled
shaft-center positions along the bolts; 95.93 mm is not the perpendicular
hole-axis pitch. The inventory does not verify a physical hole station in
each receiver, so the reported inter-axis pitch remains a model-geometry
measurement and is not an NDS spacing result. Ten other group records contain
sub-micrometre axial residuals (at most 0.0000005 mm) from source-coordinate
roundoff; only the mirrored knee-header pairs exceed the producer's 1e-6 mm
zero tolerance for the axial-offset count.

For each two-receiver axis, separated receiver intervals measured from the
modeled underhead provide a head-to-nut geometric ordering proposal. All 88
two-receiver axes have a non-overlapping interval proposal. This ordering does
not establish physical head-to-nut order for delivered hardware. No ordering
is emitted for the four axes in the three-member stacks.

The 12 retained frame-bolt axes are excluded from candidate grouping and are
reported in their own JSON collection and CSV. Their current-candidate recheck
remains required.

## Findings and limits

There are 188 candidate axis/receiver incidences. Twelve incidences are exactly
parallel to their receiver's source-proposed grain direction (0 degrees),
covering 12 distinct axes. They occur in `wj03_outer` (four axes) and
`wj05_center_x190` (eight axes):

- `knee_outer_left_inner_header_1`, `knee_outer_left_inner_header_2`,
  `knee_outer_right_inner_header_1`, and `knee_outer_right_inner_header_2`,
  aligned with the corresponding `knee_outer_*_inner_frame_block` grain.
- `center_post_header_left_1`, `center_post_header_left_2`,
  `center_post_header_right_1`, `center_post_header_right_2`,
  `center_principal_header_left_1`, `center_principal_header_left_2`,
  `center_principal_header_right_1`, and `center_principal_header_right_2`,
  aligned with the corresponding center cleat grain.

For each of these axes, the other receiver's proposed grain is perpendicular
to the axis (90 degrees). The other 176 incidences are also perpendicular.
These are geometric relationships to source-proposed grain directions. They
identify parallel-to-grain axis cases for explicit local mechanics/method
coverage review; they do not establish delivered end-grain conditions,
resistance, or acceptance. This geometry-only inventory does not claim that
such an orientation is categorically excluded by code or evaluate any
end-grain design route.

The group key describes shared geometry and receiver membership. An NDS bolt
row is load-aligned and depends on the governing load direction and member
force transfer. This inventory supplies neither. It does not assign an NDS
row, calculate group factor `Cg`, infer force or load share, or report a pass.
No arbitrary spacing scalar from these tables constitutes an NDS check or
pass. The geometry remains conditional evidence and must not be used as a
capacity or fabrication instruction.

The independent arithmetic checks in the JSON recompute the left and right
knee inner-header pairs directly from pinned source centers and bolt axes.
Each check reproduces the nonzero 22.098 mm axial center offset and 93.35 mm
perpendicular inter-axis pitch, then compares those values and the Euclidean
center distance with the emitted spacing record. It also independently
recomputes the proposed-grain projections. The producer verifies that all 92 unique candidate axes
are represented once, receiver IDs exist in the two pinned maps, pair
associations match each complete receiver set, all four three-member axes
remain in two explicit stack groups, and the 12 retained axes remain outside
candidate grouping.

## Outputs

- `bolt-groups.json`: complete source-pinned inventory, limitations, summary,
  per-axis and per-receiver records, spacing records, and separate retained
  frame bolts.
- `bolt-groups.csv`: one row per geometry group, including exact receiver
  membership and source-station availability.
- `bolt-group-axis-receivers.csv`: one row per candidate axis/receiver with
  center, diameter, unit axis, proposed grain vector, and angle.
- `bolt-group-axis-spacings.csv`: one row per within-group axis pair with
  center spacing and projections along every receiver's proposed grain.
- `retained-frame-bolt-axes.csv`: the 12 excluded retained axes and their
  receiver-specific axis-to-grain geometry.
