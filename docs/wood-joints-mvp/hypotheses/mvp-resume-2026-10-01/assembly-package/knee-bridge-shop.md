# Four-bolt knee bridge: conditional shop delta

This finite addendum records the completed four-bolt proposal for the two outer
knee spines. Read with the [current shop guide](shop-guide.md), [current-joint
addendum](current-joint-addendum.md), [proposal](../upper-corner-screw-layout/knee-spine-reinforcement.md),
[geometry](../upper-corner-screw-layout/knee-bridge-geometry.md),
[hardware profile](../upper-corner-screw-layout/knee-bridge-hardware.md),
[order reconciliation](knee-bridge-order.md) and [saved-scene fit](knee-bridge-fit.md).
The proposal remains unadopted. Current 104-axis layout and shop guide remain
authority. This addendum is not a drill or fabrication release.

## Proposed local stations

Use the lower square-cut end as proposed grain datum zero and the midpoint of
the 38.1 mm width as `u=0`. Measure 100 and 250 mm upward along grain. Each
spine keeps its four existing `u` bores and adds two `v` axes through 139.7 mm:

| Spine | Canonical proposed axis | Local station `(grain,u)`, mm |
| --- | --- | ---: |
| `knee_outer_left_spine` | `knee_outer_left_spine/proposed_v_bridge_1` | `(100,0)` |
| `knee_outer_left_spine` | `knee_outer_left_spine/proposed_v_bridge_2` | `(250,0)` |
| `knee_outer_right_spine` | `knee_outer_right_spine/proposed_v_bridge_1` | `(100,0)` |
| `knee_outer_right_spine` | `knee_outer_right_spine/proposed_v_bridge_2` | `(250,0)` |

The 7.5 mm diameter is CAD occupancy only; it does not specify a shop drill
diameter or bit. No drill size or physical hole is released here. Both frozen
spine bases map positive local `v` to world `+Y`: put each head and washer on
the `−v` face, with its nut and washer on the `+v` (`+Y`) face.

## Conditional hardware and counts

Planning hardware for the four proposed stacks:

- Four 1/4-20 × 6.5 in partial-thread Grade 5 bolts, K.L. Jack `25C650HCS5Z`.
- Four matched 1/4-20 Grade 5 metal nuts, `25CNFH5Z`.
- Eight declared washers, 25.4/8.3058/2.5 mm OD/ID/thickness.

The 8 in bolt length remains a conservative fit bound only. The assumed partial-
thread delivered profile, full-form thread position, nut engagement and actual
part conformity are unverified; nominal length does not establish them. See the
[hardware profile](../upper-corner-screw-layout/knee-bridge-hardware.md) for
conditional fit details.

| Inventory | Current guide | If proposal is later adopted |
| --- | ---: | ---: |
| Bolts / nuts / washers | 104 / 104 / 208 | 108 / 108 / 216 |
| Hillman panel/kicker screws | 66 | 66 |

These four stacks add no member, do not alter panel outlines or panel/kicker
screw stations, and connect only the two faces of each spine. The current
inventory and blank Actual/Disposition records remain unchanged.

## Conditional handling sequence

If later adopted, support each spine separately with both `v` faces accessible.
At each proposed axis, seat the head-side washer and bolt on `−v`, pass the bolt
through toward `+v`, then fit the second washer and nut on `+v`. Hand-start only
with a compatible thread; do not pull misaligned wood together. This gives
logical stack order only. Actual wrench turning, head counterhold, tool clearance
and handling have not been established; no torque or preload is specified.

For removal, support the spine, remove the `+v` nut and washer, withdraw the bolt
toward `−v`, and recover the head-side washer. The stacks may remain in their
spine during individual-member transport or be removed with their metal nuts.
They join no other transport members; keep each spine an individual body.

## Shop facts still unrecorded

- Actual cuts and layout against the proposed lower-end/width-center datums.
- Selected drill diameter, bit, drilling setup and backing method; the CAD
  occupancy value supplies none of these.
- Received bolt shank/thread transition and full-form interval, matched nut fit,
  and confirmation of the declared washer dimensions.
- Actual wrench access, nut turning, head counterhold, handling and straight
  withdrawal clearance at the installed stations.

The existing [shop guide](shop-guide.md), authority, and blank Actual/Disposition
cells are unchanged. This note records a conditional proposal only: no drilling,
fabrication, physical selection or climbing release is authorized.
