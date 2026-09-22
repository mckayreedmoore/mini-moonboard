# Current-viewer kicker-backer connection producer

`scripts.owner_barrel_backer_layout.build_layout(assembly)` accepts the
finished **current barrel viewer assembly** from
`export_owner_barrel_scene.build_viewer_assembly()`. It consumes that
assembly's actual `wood`, existing barrels, and bolt stacks. It does not
change the assembly, source members, viewer, exporter, or selected baseline.

The producer uses the detached
`owner_barrel_backer_attachment_probe.probe(assembly=..., nominal_bolt_length_mm=76.2,
barrel_axis_z_mm=205.0)` as its coordinate, source-inventory, and collision
authority. It reconstructs CAD solids from that probe's candidate points and
its shared envelope constants. The import is lazy so the parent assembly can
call this producer without a module-import cycle. It requires the current
−85 mm outer-header viewer pose and unchanged 66 fixed panel/kicker screw
and 12 retained frame-bolt axes; changed backer timber pose fails closed.

The return value has `stations` keyed by `backer_attachment_left` and
`backer_attachment_right`. Each station has two `Connection` bolt axes and
matching barrel solids, `stacks` with shaft/washer/head solids, two machine
bores and two cross-bores, and two bolt-tool and two barrel-tool envelopes.
Bolt `members` identify `base_header` and the corresponding existing
`inner_kicker_backer_*`. Names are unique to these four new duties and do not
replace any of the 24 former structural-angle duties. There are no corner
blocks. The parent can merge these rows after composing the 24-duty assembly;
it must not infer structural acceptance from the merge.

The four trial XY positions, in millimeters, are left rear (−35, −100), left
front (−20, −65), right rear (20, −100), and right front (35, −65). They use a
nominal 3 in shaft from the header top with a 2 mm washer and a provisional
barrel center at Z = 205 mm. Each nominal tip extends 2.2 mm beyond the
assumed barrel thread axis but ends 2.8038 mm before the modeled far wall.
The modeled machine bore extends 4 mm beyond the nominal tip. None is a
drilling dimension or proof of engagement.

`collision_screen` carries the source-bound finite CAD check: candidate
physical hardware, bores and individual tool envelopes against unrelated
wood, protected holds/T-nuts, electrical display envelopes, fixed 66/12
axes, existing viewer hardware, and each other. At the current pose, it
reports no unintended positive-volume intersection above 1 mm³. Driver
envelopes are used sequentially, not simultaneously; driver-vs-driver
overlap is excluded from the mutual screen. Model envelopes do not establish
delivered head/tool fit, wiring movement, tolerance, or service access.

`release_flags` are all false. Thread span, barrel-axis tolerance,
wood/bolt/barrel capacity, assembly and repeated demounting, delivered
retail fit, drilling, fabrication, and climbing acceptance remain open.
This is a source-bound viewer-development connection, not a build release.
