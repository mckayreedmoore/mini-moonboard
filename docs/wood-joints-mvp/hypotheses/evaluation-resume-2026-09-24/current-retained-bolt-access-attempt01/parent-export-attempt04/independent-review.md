# Independent review of D6 BRep export attempt04

This is a read-only review of the frozen producer, launch record, manifest, source
records, and exported file hashes. No CAD operation, mesh, or native solve was
run.

## Review result

The attempt04 bundle is internally complete and its recorded timber summaries
match the frozen geometry for all 16 finished hosts. The 20 timber identities
are exactly the source-inventory timber set. The four inventory members not
present in the frozen finished-member map are exported from the source shape
map: `base_floor_left`, `base_floor_right`, `lumber_leg_left`, and
`lumber_leg_right`. The remaining 16 IDs match the snapshot's finished-member
records.

For each of those 16 finished members, manifest bounds, volume, and center of
mass match `geometry-snapshot.json`'s `finished` summary to the precision
recorded in the manifest. All 211 manifest rows report one solid and finite,
positive-volume geometry metadata. The category counts are 20 timbers, 60
retained bolt roles (12 stacks × five roles), and 131 modeled wires.

All 211 listed STEP paths are unique, exist, and match their recorded byte size
and SHA-256. There are no unlisted STEP files in the export tree. The
`manifest_payload_sha256` recomputes from the manifest without that field, and
the manifest file SHA-256 matches the parent execution record. The producer
and its attempt04 snapshot both hash to
`12b77a1e53f1a24db9b72f04e2c06b0933dfcfd8574a5eac3abb6986b6b93fd2`; the
manifest hash is
`d90a93440575b7871fc429c3f8cec621877f805a068b7ff09a60fddc4b1e538b`.

## Source binding and fingerprint boundary

The producer validates the frozen snapshot against the live revision and
required axis/component counts; it checks each frozen source-file hash, the
source-inventory file digest bound to the live geometry, and all three
runtime-module hashes supplied by the live source binding. The parent launch
record also pins the raw geometry-snapshot file hash
`0b92357af648604ee8ce42d2f8906e0a4e5498e9e4b835a07938b81dc151d187`. The
source-inventory digest in the manifest matches the current file. The retained
access mapper verifies the 12 source bolt IDs, five physical roles per stack,
role-to-component one-to-one mapping, and source axis metadata before export.

The producer deliberately records
`per_shape_inventory_fingerprint_compared: false`. It reads the inventory's
per-part fingerprint field but does not compare it to a second extraction.
That drops the exact per-member fingerprint equality check; it does not remove
the file-level snapshot, inventory, and runtime-source validation above. The
manifest's own per-shape fingerprints identify the exported in-memory shapes,
but are not a replacement equality test against the inventory fingerprints.
The recorded rationale is that those fingerprints include unrounded planar
face descriptors. The parent separately confirmed repeated-extraction
topology and zero-volume-difference identity for `base_floor_left`; that
corroboration applies to that member only. For the other three unchanged source
members, identity is based on the single `geometry.source.parts()` extraction
under the pinned source binding, rather than an independent per-member BRep
comparison.

The attempt04 manifest does not itself record hashes for imported helper
modules. The paired [retained-access attempt03 execution record](../../retained-access-attempt03/execution.json)
does pin `scripts/wood_joint_current_retained_access.py`,
`scripts/wood_joint_current_access_screen.py`,
`scripts/wood_joint_wj12_diagnostic.py`,
`scripts/wood_joint_wj04_tool_access.py`,
`scripts/wood_joint_wj24_tool_operation_probe.py`, and
`mini_moonboard/wood_joint_frame.py`. The parent confirms that attempt03 and
attempt04 used the same live session; I independently checked that each of
those six current files still matches its attempt03 SHA-256. Thus the helper
source hashes are available in the paired evidence, though they are external
to the D6 manifest itself.

## State and claim limits

The manifest describes a proposed post-D5 removal state: candidate connector
bodies and their 92 bolt stacks, panels and 66 panel-screw axes, holds/T-nuts,
and light bodies are assumed removed beforehand. Modeled wires remain
stationary. Retained bolt removal assumes adjacent timbers are supported, and
member motion assumes its attaching fasteners have already been removed.
Temporary supports and staging surfaces are absent. No member translation or
rotation path, stable staging pose, actual cable route, physical tool envelope,
or delivered hardware is established.

The producer itself does not re-import STEP files. A separate recorded
[`readback-validation.json`](readback-validation.json) does: it pins the same
manifest SHA, imports all 211 files, and checks validity, solid count, volume,
bounds, and center of mass. All rows pass at the recorded tolerances; the
largest errors are 5.53e-5 mm³ in volume, 1.01e-7 mm in bounds, and 6.89e-10 mm
in center of mass. This is geometric-summary readback, not exact Boolean shape
equivalence. The later motion screen separately verifies the hashes of all
211 files and read-backs the 191 shapes used for its target-plus-obstacle
scene. The bundle is therefore a source-bound input set for a nominal motion
screen, not a finding that any member can be removed or that an operation is
safe or practical.
