# WJ-05 center tool-envelope comparison

This is a diagnostic comparison for trial
`wj05-center-node-rear-4x4-upper-l82-wire-relief-v2`. It screens the two
upper-header row-2 stations with catalog-sized external envelopes. It does not
establish tool fit, physical access, an installation/removal sequence, torque,
fastener resistance, or fabrication release. All release flags are false.

The archived JSON is copied byte-for-byte from the run output. Its SHA-256 is
`8fcc506b360e613bfdd8d75bb87e5ce0bdf5e7590df4e90555a268934dca41ee`.
The source fingerprints are recorded in that JSON; principal inputs include:

| Input | SHA-256 |
| --- | --- |
| `scripts/wood_joint_wj05_center_node_probe.py` | `eafffbc95d5989bcc21a7cffed90ff25e917c778bf9758154b915cbba0ec3d173` |
| `scripts/wood_joints_wj05_center_backer_transfer_probe.py` | `3da60ba6931f791e6b877b59aab7157f6e62a7e2b9db276187113e122aa8d062` |
| `docs/wood-joints-mvp/source-inventory.json` | `07af4c3eb642cf3887595fe4415eb65404cdcf74d66c5c7bb182847ef21c2d78` |
| `scripts/wood_joint_wj05_center_tools.py` | `3d14041588fb49c2664e410e8dff9b74ab5a9d026a39e4c24feea0f5501c3723` |

## Modeled tools and limits

- GEARWRENCH 80112 7/16-in socket: published 15.6972 mm outside diameter and
  24.511 mm overall length. The length begins at the installed head bearing
  face and includes the 4.7752 mm head depth; head height is not added again.
- Ko-ken 2760-75 extension: 12.3 mm outside diameter, 75 mm overall length.
- GEARWRENCH 81025 ratchet: 18.542 mm head width, 12.446 mm thickness,
  152.4 mm overall length, with two bounded 5-degree stroke cases.
- FACOM 34 7/16 open-end wrench counterhold: 22 mm head width, 3 mm thickness,
  100 mm overall length. Its modeled pose points inward and is centered within
  the nut hex height.

Catalog pages: [socket](https://www.gearwrench.com/all-tools/ratchets-sockets/chrome-sockets/80112-14-drive-6-point-standard-sae-socket-716),
[extension](https://kokenusa.com/products/extension-bar-1-4-dr-75mm),
[ratchet](https://www.gearwrench.com/all-tools/ratchets-sockets/ratchets-drive-tools/81025-14-drive-72-tooth-quick-release-locking-flex-slim-head-ratchet-6),
[counterhold wrench](https://www.facom.fr/products/34-cles-a-fourches-micromecanique-tetes-inclinees-en-pouces).

The socket and extension mating planes are coincident. Their nominal 1/4-in
drive squares match, but engagement depth, internal geometry, backlash, and
clearance are unknown. The ratchet is a conservative inline envelope; its
flex-head articulation is not modeled. No received hardware or hex engagement
was verified.

## Findings

- At both stations, the extension envelope intersects both same-side lower
  post bolt heads (about 33.677 mm³ per head).
- The inward nut-side wrench envelope intersects the same-side row-1 nut
  (387.669 mm³), shaft (95.008 mm³), and conservative principal timber
  (1,629.499 mm³).
- The left `+5°` ratchet stroke and right `-5°` stroke intersect their inner
  kicker backers (7,440.805 mm³ and 7,155.885 mm³ respectively). The opposite
  signed stroke at each side avoids the backer, but still intersects the
  lower-post head washer (about 5.994 mm³) and post timber (37.048 mm³).
- The socket, extension, and ratchet proxies remain above the analytical floor
  in this pose: their minimum Z values are 212.738, 137.738, and 125.292 mm.
  These nominal gaps are not a floor-clearance or support qualification.
- The obstacle inventory contains 20 retained legacy connector bodies and 120
  retained legacy SDS axes. The 24 SDS axes at the four replaced center duties
  are excluded; the fixed 66 panel/kicker axes and retained 12 frame-bolt
  hardware/axes remain obstacles.

The timber obstacles are raw source-derived frame solids with candidate WJ-05
bores. Some retained source openings may be absent, so timber intersections
are conservative until machining integration. Every collision above is an
external-envelope screen: it neither proves real-tool impossibility nor
establishes a successful fit.

## Bounded next-variant adapter plan

Keep this report and the frozen center producer as the original comparison.
For a separately named trial, use a small adapter over the producer's source
and candidate materialization helpers; do not edit the frozen producer or
copy its member dimensions. Apply one explicit transform set: move the two
posts, lower cleats, and their eight lower axes 10 mm outward; keep upper
cleats, upper axes, fixed 66 axes, and retained 12 frame axes fixed. Rebuild
the lower bore cuts, installed stacks, timber solids, and washer/contact
checks from those transformed axes before running the tool screen.

At each upper-header station, reverse the counterhold heading outward, away
from row 1. Screen the side-dependent ratchet sector that avoids each backer
(right `+5°`, left `-5°` in the current report convention). Require full
body/axis/washer/support checks and fixed-66/retained-12 invariants in that
variant. The adapter result remains a trial only; do not transfer acceptance
from this report or infer any capacity.
