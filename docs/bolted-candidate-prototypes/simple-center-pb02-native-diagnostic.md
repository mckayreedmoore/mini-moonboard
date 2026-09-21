# PB02 corrected `a12-forward` decision record

## Decision

**REVISE; retain PB02 for development.**

The corrected `a12-forward` whole-frame result is numerically converged and
supports retaining PB02 while its geometry and remaining checks are revised. It
is one developmental load case, not a qualified connection design. It does not
release drilling, fabrication, purchasing for construction, or construction.

The active geometry now moves `post_high` from Z = 190.0 mm to Z = 189.4 mm.
The retained pre-revision evidence is superseded for current-geometry demand
comparison by a corrected rerun at Z = 189.4 mm. The move increases
the post upper-end distance from 48.9 mm to 49.5 mm and leaves approximately
6.1 mm of nominal wood ligament at the crossed `post_high`/`post_cleat_2`
bores. That remaining ligament is not structurally qualified.

## Authenticated evidence

The current-geometry evidence package is:

`fea/results/diagnostics/pb02-corrected-a12-forward-z189p4-v1`

| Artifact | SHA-256 |
| --- | --- |
| `report.json` | `fa37447a09679a61d13e6ed065c8d5bfa945b1efb539506b701c3436ad13a87e` |
| `cycle-10/input.json` | `0fc96683d11edf4ad9c47d083b572a364f782e4c803371fbff9d55eff17d7c28` |
| `cycle-10/frame.dat` | `628aed89300b50feeec892e559da23d3ee2cfe45dadc1be41e8069e60027ba0b` |
| `cycle-10/frame.frd` | `5cedc08e03ce31607d033923456627ed9aebbe9e855884f7502e138399ddc801` |
| `cycle-10/frame.12d` | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |

The package also retains the authenticated source-snapshot closure. The
compact copy retains the final cycle but omits prior cycles and other large raw
artifacts, so it does not satisfy the full 389-artifact manifest in the report.
The package README records that scope explicitly. The
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

The direct shifted-post/base-header bearing carries 114.52 N. All four samples
are compressive. The governing interface is `rear_block_post`, with a 155.40 N
resultant force and approximately 5.97 kN·mm resultant moment. The largest
simultaneous bolt demand is 79.93 N lateral shear and 24.70 N tension. Relative
to the pre-revision result, no interface force changed by more than 0.081 N and
no bolt shear changed by more than 0.060 N; the load path is materially
unchanged.

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
33.77 N corrected-case demand, a ratio of 0.1204. The 0.189-inch typical-root
sensitivity gives 297.61 N and a ratio of 0.1135. These are component references,
not final adjusted values: group action, geometry factor, splitting, and the
remaining load cases remain unresolved. This result does not require rotating
the block grain or moving to 4x8 stock solely for the current one-case demand.

Before any physical release, work still includes:

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
