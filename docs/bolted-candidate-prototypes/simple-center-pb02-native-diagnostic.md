# PB02 corrected `a12-forward` decision record

## Decision

**REVISE; retain PB02 for development.**

The corrected `a12-forward` whole-frame result is numerically converged and
supports retaining PB02 while its geometry and remaining checks are revised. It
is one developmental load case, not a qualified connection design. It does not
release drilling, fabrication, purchasing for construction, or construction.

The active geometry now moves `post_high` from Z = 190.0 mm to Z = 189.4 mm.
The retained whole-frame evidence in this record predates that revision and
must be rerun before its demands are attributed to the revised pose. The move
increases
the post upper-end distance from 48.9 mm to 49.5 mm and leaves approximately
6.1 mm of nominal wood ligament at the crossed `post_high`/`post_cleat_2`
bores. That remaining ligament is not structurally qualified.

## Authenticated evidence

The retained evidence package is:

`fea/results/diagnostics/pb02-corrected-a12-forward-v1`

| Artifact | SHA-256 |
| --- | --- |
| `report.json` | `7240026c654cb2b8b417741c0a895234a7c579fc271f9d4a8043cb83fcbb0020` |
| `cycle-10/input.json` | `b153d9dc2600f31004bcc5ce27e5abdd4eda31ba9f6c6c22ff989f727e43a436` |
| `cycle-10/frame.dat` | `1eea3da5d84bed06bcf04f15e260ca633c837a13c3794e8a7fb26c4df0419336` |
| `cycle-10/frame.frd` | `bb4506708ff25d40dd1049bbb21f6f2ceca49a68ae484d2ff2679086fb0b4724` |
| `cycle-10/frame.12d` | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |

The package also retains the authenticated source-snapshot closure. The
corrected mapping reverses the seven canonical PB02 interface contact
directions so compression closes and opening releases each interface. Bolt
axes remain directed from the first member to the second. The four direct
shifted-post/base-header samples remain inward in negative Z and do not credit
backer/post contact.

The case converged in 11 cycles. The report passes the recorded contact and
axial unilateral checks, member and global equilibrium checks, MPC checks, and
positive-load-work gate. All retained artifacts referenced here match the
hashes above. Numerical acceptance does not qualify the modeled demands as
design demands.

## Corrected load path and demand

The applied `a12-forward` load is `[0, -300, -2224.11] N`, in addition to
modeled self-weight. The center-right load travels through three connected
routes:

- base header to shifted post through direct wood bearing and the
  `block_header` to `post_block` path;
- base header to principal through `header_principal_block` and
  `principal_block_principal`; and
- principal to upright to rear cleat to shifted post through the return path.

The direct shifted-post/base-header bearing carries 114.64 N. All four samples
are compressive. The governing interface is `rear_block_post`, with a 155.48 N
resultant force and approximately 5.98 kN·mm resultant moment. The largest
simultaneous bolt demand is 79.96 N lateral shear and 24.66 N tension.

The preliminary conditional DF-L lateral screen reaches a maximum demand ratio
of 0.148. Using the smaller thread-root sensitivity increases that ratio to
0.157. The conditional A307 steel comparator has a maximum linear
axial-plus-shear interaction of 0.0321. The idealized washer-annulus wood
bearing ratio is 0.0256. These are component screens only; they do not establish
joint resistance or resolve splitting, group action, washer metal behavior,
prying, preload, or member interaction.

## Hardware and access

The current PB02 layout uses 10 through-bolts, 10 nuts, and 20 washers:

- three 5-inch bolts;
- three 6-inch bolts; and
- four 8-inch bolts.

The estimated hardware cost is $11.88 allocated or $13.69 at first checkout,
excluding lumber. All modeled bolts have an insertion route, but 7 of 10 are
one-ended access installations. Nominal washer seats and compact socket
envelopes clear in this model. Delivered dimensions and tool access still need
physical verification.

## Required revision and unresolved work

The two `block_header` bolts are an axis-parallel/end-grain case for the current
block grain orientation. A conditional 2024 NDS single-bolt yield calculation,
using DF-L G = 0.50, 45 ksi bolt yield strength, the 0.67 end-grain factor, and
the smaller 0.180-inch thread-root sensitivity, gives 280.50 N versus the
33.71 N corrected-case demand, a ratio of 0.1202. The 0.189-inch typical-root
sensitivity gives 297.61 N and a ratio of 0.1133. These are component references,
not final adjusted values: group action, geometry factor, splitting, and the
remaining load cases remain unresolved. This result does not require rotating
the block grain or moving to 4x8 stock solely for the current one-case demand.

Before any physical release, work still includes:

- rerun the corrected response at the integrated `post_high` Z = 189.4 mm
  geometry;
- resolve the approximately 6.1 mm crossed-bore ligament and local splitting;
- complete the `block_header` group, geometry-factor, and local wood checks;
- verify exact delivered bolts, thread-root diameter, nuts, washers, lumber,
  insertion routes, and tool access;
- complete bolt-row/group, perpendicular-tension, bore-aware member,
  washer-metal, preload, and prying checks; and
- run and envelope `a12-rear`, `a12-left`, `k12-right`, `k12-rear`, and
  `a1-rear` with the corrected mapping and revised geometry.

Until those items are completed and reviewed, PB02 remains developmental only:
**no drilling, fabrication, or construction is authorized.**
