# BG045 axis-2-only conditional proposal screen

This packet compares the reviewed BG045 coordinates with a conditional
`+5.4 mm` Y translation of axis 2 alone and with the earlier unapproved
both-Y-face 4D band. It uses the three case-bound rear exports, current BG003
orthogonal-bore/profile evidence, washer-seat screen, and the ten existing
Hillman axes whose receiver is `base_header`. It changes no model or axis,
does not rebuild CAD, and launches no native solver.

The axis-2-only coordinates are `axis 1 y = −62.35 mm` and
`axis 2 y = −150.30 mm`. This is a bounded geometry proposal for review, not
an accepted detail or instruction to move an axis. The source demands below
come from the reviewed coordinates. They serve only as conditional direction
screens; moving a bolt can change stiffness and group force distribution, so
these forces are not claimed as demands for either proposed coordinate set.

## Conditional edge comparisons by authenticated case

For the named smooth `1/4 in` scenario, `D = 6.35 mm`, giving conditional
Table 12.5.1C comparators `4D = 25.4 mm` at the loaded perpendicular-to-grain
edge and `1.5D = 9.525 mm` at the unloaded edge. The source dependency still
marks applicability to the completed end-grain-axis joint as pending. These
are source-envelope comparisons, not an adopted code pass/fail.

The pinned NDS-2024 scope is §12.5.1.3 referring dowels with `D ≥ 1/4 in` to
Tables 12.5.1C/12.5.1D; Table 12.5.1C gives the perpendicular-to-grain
loaded/unloaded edge detail. Section 12.5.2.2's end-grain lateral factor does
not waive those detailing provisions. This screen does not decide how that
tabulated edge direction applies to BG045's oblique, end-grain-axis group.

| Rear case and member/axis | Source direction and current geometric reading | Axis-2-only comparison | Remaining issue |
|---|---|---|---|
| A1-rear, block axis 2 | Block force Y is `−71.224 N` in all 7 increments; source ray first meets `−Y`, 20.0 mm away. | Moving axis 2 `+5.4 mm` changes that `−Y` distance to 25.4 mm; the source ray still meets `−Y` first. This reaches the named conditional 4D comparator for this source direction. | It is not a completed NDS applicability ruling or strength check. Block axis 1 remains at its reviewed position. |
| A1-rear, block axis 1 | Block force Y is `−61.591 N`; loaded `−Y` face is 113.35 mm away. The opposite `+Y` face is 20.0 mm, above conditional `1.5D`. | Axis 1 is unchanged. | No +Y loaded-edge issue is indicated on this case direction; the exact detail applicability remains pending. |
| A1-rear, header axes 1/2 | Header forces point toward `+Y`; axis 1 is 26.35 mm from `+Y`, axis 2 is 119.70 mm. Both full header vectors are oblique to proposed `+X` grain. | Axis 2 becomes 114.30 mm from `+Y`; axis 1 stays 26.35 mm. Neither is below 25.4 mm on the signed-Y component screen. | Oblique header action and exact Table 12.5.1C applicability remain unresolved. |
| A12-rear, block axis 1 | Block force Y is `+14.035 N`; signed `+Y` face component distance is 20.0 mm, while the rectangular-envelope ray first reaches `+X` at 44.45 mm. | Axis 1 stays at 20.0 mm from `+Y`; axis-2-only does not clear this conservative component sensitivity. | Ray-first-face versus signed-component applicability is unresolved; no universal NDS oblique-ray rule is asserted. |
| A12-rear, block axis 2 | Block force Y is `+5.761 N`; `+Y` is 113.35 mm away and the source rectangular ray first reaches `+X`. | The `+Y` component distance becomes 107.95 mm and remains above 25.4 mm. | The force is from reviewed geometry only; no relocation demand is inferred. |
| A12-rear, header axis 2 | Header force is `(-24.272, −5.761, 0) N`; the source ray first reaches `−Y`, 20.0 mm away. The full vector is oblique to `+X` grain. | `−Y` becomes 25.4 mm away; the ray still first reaches `−Y`. This reaches the signed-Y 4D comparator conditionally. | The header vector is oblique, so this component/ray geometry does not settle NDS applicability. Header axis 1 is not moved; its `−Y` distance is 113.35 mm. |
| K12-rear, block axis 1 | Block force Y is `+1.540 N`; `+Y` component distance is 20.0 mm, while the rectangular ray first reaches `+X` at 44.45 mm. | Axis 1 stays at 20.0 mm from `+Y`; axis-2-only does not clear this conservative component sensitivity. | Same unresolved ray/component applicability question as A12-rear. |
| K12-rear, block axis 2 | Block force is `(-14.930, +4.590, 0) N`; `+Y` is 113.35 mm away and the ray first reaches `−X`. | `+Y` becomes 107.95 mm away, still above 25.4 mm. | No change to the current source force is assumed for the proposal. |
| K12-rear, header axis 2 | Header force is `(+14.930, −4.590, 0) N`; the source ray first reaches `−Y`, 20.0 mm away. The full vector is oblique to `+X` grain. | `−Y` becomes 25.4 mm away; this reaches the signed-Y comparator conditionally. | Oblique header applicability remains unresolved. Header axis 1 is not moved; its `−Y` distance is 113.35 mm. |

The source report retains each axis’s complete signed lateral force vector at
all seven load increments, its matching equal-and-opposite header vector, and
the case/report hashes. The cases are `A1-rear` (report SHA-256
`2b498383b319aeb31e74c3b329e0758330b8b39d0a8e1b4788437db06453bfce`),
`A12-rear` (`812a62fa3cd96a8983649c84a8c78a8d176d639465c887b11d1827a3f8f1ee17`),
and `K12-rear` (`a78ca15d9d888dbddf6963be34a2f5e57159b0df77ef6b754cf631dbba8c10d0`).
Each report identifies the same reviewed geometry revision, has a full-factor
one endpoint, and records passing response/all-body gates while expressly
withholding joint acceptance.

## Geometry consequences

| Configuration | Axis 1 Y (mm) | Axis 2 Y (mm) | Y pitch (mm) | Minimum modeled BG003/BG045 bore web (mm) |
|---|---:|---:|---:|---:|
| Reviewed current | −62.35 | −155.70 | 93.35 | 7.453 |
| Axis 2 only, conditional | −62.35 | −150.30 | 87.95 | 7.453 |
| Prior both-face 4D band, unapproved | −67.75 | −150.30 | 82.55 | **2.053** |

Axis 2 only keeps axis 1 at the reviewed station and therefore avoids the
2.053 mm nominal web consequence of moving axis 1 toward BG003 orthogonal bore
2. It still moves axis 2 closer to BG003 bore 1: its modeled web reduces from
41.972 to 36.572 mm; the governing pair remains axis 1/BG003 bore 2 at
7.453 mm. In the prior both-face band, the minimum web is 2.053 mm for moved
axis 1/BG003 bore 2. These values are modeled bore-envelope geometry only,
not a strength margin or splitting criterion.

The reviewed profile query samples 72 rays and the section screen supplies
the two BG003 X-bore centers and 7.5 mm modeled bore diameter. This calculation
uses the orthogonal-axis centerline separation at those source coordinates;
it does not re-query the continuous finished profile, tolerances, or a moved
axis. The pitch changes are recorded as geometry only; no row-spacing rule is
inferred.

The ten unchanged Hillman axes entering `base_header` were screened by XY
projection only. In all three geometry scenarios, `kicker_header_left_5` is
nearest: axis 1 remains 85.850 mm away; axis 2 is 122.337 mm at current and
118.551 mm after its proposed move. The both-face proposal has the same
axis-2 projection and an 85.850 mm nearest projection for axis 1. The source
4.1402 mm occupied envelope is a legacy CAD value, not a delivered Hillman
screw diameter. These projections omit Z separation and establish no
clearance, backing, installation, or load-transfer result. Preserve the 66
Hillman screw inventory; this screen covers only the ten identified
`base_header` receiver dependencies.

The existing washer-seat screen still has no selected product, exact finished
support polygon, or opening radius. Translating a seat center with axis 2
cannot establish fit, support, bearing, or access. The pinned BG045
end-grain/helper record is context only; no helper strength result is
transferred to a relocated coordinate.

## Remaining checks and stop boundary

The signed component table is useful for locating which named comparisons
change, but the NDS Table 12.5.1C applicability and direction-selection
convention for this completed end-grain-axis block/header group remain open.
For A12/K12 block axis 1, a +Y signed-component screen is below 4D while the
rectangular ray reaches an X face first. For the header, the lateral vectors
combine along-grain X and cross-grain Y. The ray result is geometric context;
this packet does not create an NDS rule for choosing the ray or component
interpretation.

Before implementing any relocation, resolve the applicable loaded-edge
interpretation and verify actual finished edges/profile and tolerances; check
the affected BG003/BG045 bore union and continuous profile; establish washer
fit/support/access and the ten affected header receivers; then apply a
supported complete-joint bearing, net-section/row tear-out, interaction, and
splitting method. The existing EN 1995-1-1:2004 §8.1.4/Figure 8.1 arrangement
has not been mapped to this topology, and NDS §§3.8.2 and 11.1.3 do not supply
a general equation for this new bolt group. A changed station also requires
case-specific demand review because current source forces cannot be carried
over after relocation.

This screen does not authorize a model edit, axis move, fabrication, or a
design conclusion. Keep the reviewed geometry intact until required changes
are reported and reviewed. The complete source SHA-256 list and calculations
are in [`detail-screen.json`](detail-screen.json); rerun the pinned,
read-only arithmetic with [`produce.py`](produce.py).
