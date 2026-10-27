# V3 rear-foot marking templates

Use the side-specific V3 file set in `prototype-v3-verified/`. The earlier V2
files and `README.md` are preserved as history; V2's single ribbed part cannot
be rigidly seated on both outside faces. Do not print V2 as a universal
left/right stencil.

## Current rear-foot targets

The geometry and BRep sources are pinned in
[`prototype-result-v3.json`](prototype-v3-verified/prototype-result-v3.json).
The stencil marks only the current rear leg-to-runner axes:

| Side | STL / STEP | Axis | Outside-face mark (mm) | Placement determinant |
| --- | --- | --- | --- | ---: |
| Left | `left-rear-foot-leg-marking-jig.stl` / `.step` | `rail_rear_bolt_left_1` | `(-1308.100, 1556.825893, 70.434911)` | +1 |
| Right | `right-rear-foot-leg-marking-jig.stl` / `.step` | `rail_rear_bolt_right_1` | `(1304.925, 1556.825893, 70.434911)` | +1 |

Both mark locations are `U=88.269485 mm` from the rear-foot vertex and
`W=63.863974 mm` from the rear long edge, measured across the 139.7 mm leg
face. The face plate is 3.2 mm thick, with 5 mm outward ribs and a 2 mm mark
aperture. Each part is 149.31 × 141.30 × 8.2 mm. The STL and STEP files are
separate physical left/right parts. The left STL is mirrored in its local
width coordinate; its placement and the right placement are both proper rigid
transforms. Do not flip one part to substitute for the other.

The verified datum sampling maps the rear edge and sloping foot edge onto the
current finished leg BReps. The outside-face mark maps to the current modeled
bore center. The flat contact skin is at local `z=0`; the ribs point away from
the wood on both sides. These checks establish the CAD placement against the
pinned model only. They do not establish physical lumber dimensions or fit.

## Marking use

1. Select the STL matching the leg side. Print in millimetres at 100% scale,
   with the flat `z=0` contact face on the build plate and ribs upward. Use the
   100 mm check line in `placement-datum-v3.svg` to verify drawing scale.
2. Seat the face plate on the outside face of the leg. Align its sloping edge
   to the finished rear-foot cut and its straight rear edge to the actual rear
   long edge. Confirm the plate sits flat before clamping.
3. Transfer the center through the aperture with an awl or marker. The 2 mm
   aperture is not a drill guide. This packet selects no drill bit, bushing,
   pilot depth, or drilling sequence.

The printed items are provisional marking prototypes. Physical fit,
fabrication, drilling, structural acceptance, and climbing release remain
false. The front-foot runner axes have a different face and two-hole pattern;
they are outside this packet.

## Reproduction

From the repository root, use the source-bound producer and a fresh output
directory:

```sh
uv run python fea/generated/v11-shorter-bolts-v1/build-package/runner-leg-jigs/build_runner_leg_marking_jig_v3.py --out-dir fea/generated/v11-shorter-bolts-v1/build-package/runner-leg-jigs/prototype-v3-verified
```

The result records the producer, geometry, receipt, six-case bank, joint
record, finished leg BReps, side transforms, sampled datum checks, and output
hashes. The producer refuses changed pinned inputs and nonempty output
directories.
