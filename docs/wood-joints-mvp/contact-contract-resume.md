# Contact contract resume checkpoint

The local `fea/wood_joint_patch_contact_contract.py` remains a bounded WJ04
representative-fragment preparer. Its exact source guards are intentionally
retained. It binds a five-body WJ04 patch, eight named bolts in four two-member
interfaces, 32 separate metal solids, and the corresponding 76 explicitly
listed unilateral contact pairs. The manifest labels the result unsolved,
unaccepted, and incomplete; contact classification is not a free-mode or
strength pass.

The focused audit now verifies each source face belongs to the stated body,
rejects repeated source faces, and clips axial TRI6 faces only when all six
face nodes fall inside the interval. It records selected, outside, and
boundary-excluded face counts plus a chord-area coverage estimate. The area
estimate is a mesh-boundary diagnostic, not a contact capacity or response
measure. Any boundary-excluded face or missing clipping audit leaves the
contact fragment unready for response; the omitted area is not treated as
zero. Mechanics and patch inventories also require unique physical bolt IDs.
Receiver records must match the frozen per-stack head-to-nut pair and
the interface's same ordered pair. Raw inventory digests remain compared to
the corresponding mesh report and seat evidence.

There is no current-revision migration in this helper. At
`led-clearance-2x6-runner-seated-blocks-v1` (`b1e8707d`), the geometry has 24
blocks, 92 candidate bolt axes, 12 retained frame-bolt axes, revised bolt
placements, and newly seated exterior blocks on the floor runners. Its contact
network includes the block-to-runner bearing faces. The WJ04 helper instead
requires the old five wood owners, eight specific physical bolts, four named
cleat-to-host interfaces, 127 mm grips, WJ04 hardware profile, and its fixed
source-bound surface mapping. Renaming a revision or replacing a digest cannot
make those owners and duties match.

The migration blocker is the missing complete source-bound mechanics and
contact inventory for the exact resumed revision: finished body ownership,
each bolt's ordered receivers, axes and intervals, physical component
geometry, finite contact faces (including block-to-runner seats), and the
matching raw-hash-bound mesh reports. Preserved WJ16/WJ24 mesh evidence does
not supply that current-revision contract. No native evaluation or contact
acceptance follows from this helper or its lightweight software tests.
