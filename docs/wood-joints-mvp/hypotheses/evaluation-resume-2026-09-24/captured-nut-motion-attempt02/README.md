# Captured-nut motion probe, attempt02

Status: current-revision CAD motion hypothesis for four axes whose direct
axial nut slides intersect wood. The [motion report](motion.json) is bound to
`led-clearance-2x6-runner-seated-blocks-v1`; it tested four axes against the
1,231-shape live scene in 2.815 seconds. Report SHA-256:
`83c905bec64010695c769a73d7b8923869ef1aef5bda9b8591cdad0d443b21a4`.
No live geometry changed. This is not a tool-access, physical-operation, or
assembly pass.

## Candidate local sequence

The test assumes the nut and washer are captured at their current seats and
the threaded connection can be unthreaded in place. It then checks headward
bolt withdrawal over 151.368 mm, including a 1 mm terminal allowance, followed
by moving the nut and washer together laterally beyond the blocking wood's
global-X bound by 1 mm, then 25 mm nutward.

| Axis | Lateral move `(ΔX, ΔY, ΔZ)` mm | 25 mm nutward move `(ΔX, ΔY, ΔZ)` mm | Two-stage local CAD motion |
| --- | ---: | ---: | --- |
| `bottom_center/clip_horizontal_bottom_left_2/rail_2` | (−50.9623, 0, 0) | (0, −16.0697, −19.1511) | Clear in CAD probe |
| `bottom_center/clip_horizontal_bottom_right_1/rail_2` | (+48.9623, 0, 0) | (0, −16.0697, −19.1511) | Clear in CAD probe |
| `bottom_outer/clip_horizontal_bottom_left_1/rail_2` | (+53.9623, 0, 0) | (0, −16.0697, −19.1511) | Clear in CAD probe |
| `bottom_outer/clip_horizontal_bottom_right_2/rail_2` | (−55.9623, 0, 0) | (0, −16.0697, −19.1511) | Clear in CAD probe |

Nut and washer lateral motion uses exact source-BRep transverse cylinder and
annular-cylinder sweeps. Each selected lateral path and its 25 mm follow-on
has no external scene-object hit; all other live scene shapes remain
obstacles, with the active target-stack roles excluded as listed in the report
and their component pair interactions checked separately. The opposite tested
X direction for each axis intersects the corresponding `base_principal_center_*`
or `base_side_*` wood. The 25 mm
nutward segment is only a bounded local continuation, not full-scene removal
or a verified place where a person can capture or stage the loose parts.

The headward external-scene check reports no hits; the five moving target-stack
roles are excluded there, with listed own-pair checks evaluated separately.
Those checks report zero head/head-washer overlap with the retained nut/washer
pair and zero shaft/washer overlap. The shaft and the modeled boreless nut display
envelope overlap by 181.793976 mm³ both before and during the sweep. The report
treats this as unchanged coaxial occupancy under assumed thread-compatible
unthreading; it does not simulate threads or prove physical passage, clearance,
or fastener compatibility.

## Comparison with attempt01 and limits

[Attempt01](../captured-nut-motion-attempt01/motion.json) used a 20.0246 mm
lateral displacement. All four lateral segments were clear, but the subsequent
25 mm nutward moves hit the original wood. Attempt02 derives the lateral
distance from the blocking wood's X bounds plus 1 mm and tests both signs,
finding one complete two-stage local CAD route per axis.

Actual unthreading, selected tools, counterholding, hand clearance, loose-part
capture, support transfer, thread compatibility and the reverse assembly path
remain unverified. Do not interpret this local path as a complete operation or
as physical access. No geometry was changed and no native mechanics ran.
