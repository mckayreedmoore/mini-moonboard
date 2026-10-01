# BG001 knee outer left post pair — source-only check dependencies

**Finished-profile update:** the [48-ray STEP query](current-knee-finished-profile-attempt01/README.md)
now verifies the relevant grain-terminal faces as square at all three sampled
receiver-depth stations. It supersedes the descriptor-only oblique-end
characterization below and supplies conditional end-distance branches; no
continuous-minimum, physical receiving or joint acceptance is implied.

**Scope:** `BG001`, axes `knee_outer_left_post_1/2`, between
`base_post_outer_left` and `knee_outer_left_spine`, in the attempt04 reviewed
development geometry. This is a local input map, not a joint check or a
full-frame result. The bolt-group inventory explicitly records the NDS
load-aligned row as `not_assessed`.

## Geometry that is available

Both modeled axes are 6.35 mm diameter and point approximately global `+X`.
Their centers are `(-1208.151, -137.6, 171.45)` and
`(-1208.151, -137.6, 213.5)` mm. They are 42.05 mm apart, or 6.62 nominal
diameters, along both receivers’ source-proposed `+Z` grain direction. Each
axis is 90° to each proposed grain direction. The frame grain comes from the
conditional frame map; the spine grain is a conditional block-layout proposal.
Neither is an observation of delivered stock.

The reduced member descriptors give these center-to-section/end-coordinate
distances:

| Receiver | To nearest Y section edge | To +Z terminal coordinate, axes 1 / 2 | To −Z start coordinate, axes 1 / 2 |
| --- | ---: | ---: | ---: |
| `base_post_outer_left` | 38.10 mm (6D) | 67.45 / 25.40 mm (10.62D / 4D) | 171.45 / 213.50 mm |
| `knee_outer_left_spine` | 44.45 mm (7D) | 244.55 / 202.50 mm to descriptor end | 31.75 / 73.80 mm to descriptor start |

The spine’s end is oblique. Its z-endpoint arithmetic is only to the member
descriptor, not a cut-aware end distance; no exact signed-grain ray to its
finished end was measured for these axes. The Y values are nominal section
distances from the reported center/depth. Do not treat them as cut-aware NDS
distances or as drilled-hole instructions.

For the post, the closer axis is 25.40 mm (4D) from the +Z terminal
coordinate. The existing NDS-2024 method note gives 7D (44.45 mm at this
nominal D) for softwood parallel-grain tension and 4D for the stated
compression/perpendicular-end cases. Thus the post geometry raises a specific
direction-dependent check: if that square-cut end is the loaded end in
parallel-grain tension, axis 2 is short of the 7D reference. The force sign,
member role/material applicability, and source end condition are not resolved
here, so this is not a failure finding. BG001 geometry does not itself define
an NDS row, `Cg`, or force allocation. The group’s 42.05 mm pitch is a
candidate along-grain spacing only if the eventual load-aligned row is along
`+Z`.

The source contact map records a 13,139.96 mm² coincident post/spine face at
`x = -1219.2 mm`, with opposite face normals. This is geometric contact area;
it supplies no bearing, opening, slip, or clamp/preload law. The reduced
assembly map binds these axes to lateral springs only. It provides no axial
bolt/nut transfer law.

## Hardware and transfer dependencies

The attempt04 axis record gives 101.6 mm modeled underhead-to-tip length and
76.2 mm modeled timber grip. The geometric receiver intervals are spine
1.651–39.751 mm and post 39.751–77.851 mm from underhead; the proposed order
is not verified for delivered hardware. The 1.651 mm underhead-to-first-wood
offset is dimensionally within the conditional K.L. Jack 25NWUS washer lead’s
1.30–2.03 mm thickness range. The register assigns two separate washer roles
per axis, but no washer is selected or received and no washer footprint/seat
contact is checked. The dimensional match does not establish a seat or force
transfer.

Both axes remain `pending_no_delivered_lot_or_matched_functional_thread_interval`:
no selected bolt, delivered shank bounds, delivered full-thread interval, or
matched nut active-thread interval is recorded. Catalog leads are HiStrength
104-035, Tanner 25C400HCS5Z, and K.L. Jack 25C400HCS5Z, with a conditional
K.L. Jack 25CNFH5Z nut. The 4 in / 1/4-20 labels are catalog leads, not
delivered stack evidence. A source-based check still needs the actual matched
lot’s usable shank across the two receiver planes and active thread overlap at
the nut, plus confirmed washer seats and the applicable axial/lateral transfer
law. The acceleration NDS reference screen’s 567.848–796.262 N values are
unadjusted individual-fastener scenarios; it excludes group action, geometry,
threads in bearing, axial/combined loading, washer behavior, and current joint
demands, so none is a BG001 demand or capacity.

## Connected path that must remain in view

The source crosswalk shows another spine route at `BG003`: two axes in one
three-member stack containing `knee_outer_left_spine`, `base_side_left`, and
`knee_outer_left_inner_frame_block`. Preserve it as a three-member stack; do
not split it into independent pairwise groups. The inner-frame block then
meets `base_header` at `BG045`; its modeled axes are parallel to the block’s
conditional `+Z` grain proposal, so that end-grain-axis method branch remains
separate and unassessed. These routes can be concurrent. No force sharing or
complete spine-to-frame transfer follows from the geometric crosswalk.

**Next bounded inputs:** signed member/joint actions for the BG001 and linked
rows; cut-aware finished-profile distances at the spine axes; confirmed
member/material and load direction for the NDS row; delivered bolt/nut/washer
identity and thread/shank intervals; and a supported bearing/opening/slip and
axial-transfer model for these interfaces. Until then BG001 is a geometry
screen with conditional check leads, not a pass.

## Pinned sources

- [`bolt-groups.json`](bolt-groups/bolt-groups.json), SHA-256
  `4a8b8f78db190d2e9841e5ad266356f0f0c5a402072d371938ad0760da0accb4`.
- [`member-geometry.json`](reduced-static-attempt01/member-geometry.json),
  SHA-256 `121f1940d0180367f953a1f92443964ded901ca775536750a9b028e37d6c8187`;
  [`contact-geometry.json`](reduced-static-attempt01/contact-geometry.json),
  SHA-256 `034067430fff5207cdb40819fa8118a367edeb29a8d83926928cc96a0e87d151`.
- Attempt04 manifest:
  [`current-full-frame-input-manifest.json`](../evaluation-resume-2026-09-24/current-full-frame-input-manifest-attempt04/current-full-frame-input-manifest.json),
  SHA-256 `9e682e28c3d4c3c0594863f82c6b74d19dee2700f3856d34e1a26f69082e4f11`.
- Hardware register:
  [`fastener-axis-register.json`](../evaluation-resume-2026-09-24/current-hardware-material-cost-closeout-attempt01/fastener-axis-register.json),
  SHA-256 `c1e53e9a08599d13a992fc11a493853c1695f697f3fe99b45af20795c430240a`.
- Existing method references: [`NDS screen`](nds-screen/README.md) and the
  [finished end/edge method note](../evaluation-resume-2026-09-24/ordinary-finished-end-edge-query-attempt01/README.md).
