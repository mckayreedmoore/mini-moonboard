# Three-member receiver order — attempt01

## Engineering result and stop condition

This supplement resolves the modeled underhead-to-tip receiver interval order
for the four axes in the two three-member candidate bolt stacks. It can unlock
member-specific input setup for later bolt/wood connection checks, because the
three receivers on each modeled axis can now be identified in sequence. Stop
if a source pin changes, any receiver has multiple axial intervals, intervals
overlap by more than 1e-6 mm or leave a gap greater than 1e-6 mm, or the two
axes in a stack disagree.
The result is only a geometric ordering proposal. It does not establish
delivered hardware orientation, installed clamping, action transfer, force
sharing, or capacity.

## Result

The verifier finds exactly four axes in two stacks. Both axes in each stack
have the same unique sequence from the model's underhead datum:

- Left outer-knee stack: knee_outer_left_spine → base_side_left →
  knee_outer_left_inner_frame_block.
- Right outer-knee stack: knee_outer_right_spine → base_side_right →
  knee_outer_right_inner_frame_block.

The receiver intervals are contiguous within the 1e-6 mm geometry tolerance.
The first receiver begins 1.651 mm from the modeled underhead datum; that
offset is preserved as geometry and does not establish washer seating. The
final modeled wood interval ends at about 217.551 mm from underhead. Both bolt
axes within each stack agree. Detailed intervals, axes, and source pins are in
[receiver-stack-order.json](receiver-stack-order.json).

Reproduce the integrity and reconstruction check from the repository root:

    python3 docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/bolt-groups/three-member-stack-order-attempt01/verify_stack_order.py --verify

Use --write only after inspecting its fixed source pins to regenerate the
record. The verification path is read-only.

## Limits and applicability

The ordering comes from the current attempt04 modeled shaft/receiver
intersection intervals, measured from each modeled underhead in its recorded
axis direction. The source geometry is an analysis envelope:
it does not establish purchased bolt length, washer/nut location, installed
hole position, physical head-to-nut orientation, or a cut/drill instruction.
In particular, the first receiver's 1.651 mm offset from underhead is not
interpreted as bearing, clearance, or a hardware allowance.

This closes only the receiver sequence for four candidate axes. The source
groups omit station IDs for both stacks; their family/trial/full-receiver
fallback remains visible. The work does not generate load-aligned NDS rows,
determine whether bolts in the stack share load, calculate `Cg`, identify
simultaneous signed actions, prove the block/frame load path, or provide wood
or steel resistance. No geometry was changed and no CAD, mesh, or solver was
run. The other 88 two-receiver axes and all 12 retained frame-bolt
arrangements are outside this supplement.

## Source pins

| Source | SHA-256 |
|---|---|
| [Attempt04 current full-frame manifest](../../../../../../docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-full-frame-input-manifest-attempt04/current-full-frame-input-manifest.json) | `9e682e28c3d4c3c0594863f82c6b74d19dee2700f3856d34e1a26f69082e4f11` |
| [Existing candidate bolt-group geometry inventory](../bolt-groups.json) | `4a8b8f78db190d2e9841e5ad266356f0f0c5a402072d371938ad0760da0accb4` |

Local artifact integrity is recorded in [SHA256SUMS](SHA256SUMS).
