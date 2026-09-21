# PB02 corrected `a12-forward` decision record

## Decision

**REVISE; retain PB02 for development.**

The corrected `a12-forward` whole-frame result is numerically converged and
supports retaining PB02 while its geometry and remaining checks are revised. It
is one developmental load case, not a qualified connection design. It does not
release drilling, fabrication, purchasing for construction, or construction.

The active geometry keeps `post_high` at Z202.0 and moves only `cleat_link` from
Z370 to Z328.5. The post pair has 26.0 mm crossed centerline separation and
18.7 mm nominal surface ligament. Its 36.9 mm loaded-end distance exceeds 3.5D
but is below 7D; the conditional reduced factor is `CΔ = 0.83015`. The
upright/link pair now has 27.5 mm centerline separation and 20.2 mm nominal
surface ligament. Existing block sizes and ordinary bolt lengths are unchanged.

## Authenticated evidence

The current-geometry evidence package is:

`fea/results/diagnostics/pb02-corrected-a12-forward-z202-link328p5-v1`

| Artifact | SHA-256 |
| --- | --- |
| `report.json` | `6e5fe950f796e86c17fc575899c4e5b3a3314166e1fc3fafc81c96e530f1c7df` |
| `cycle-10/input.json` | `6a375d8d683b3f77353e6bb82eda91243472c05241cf33cf1b6aacdc6c317e6d` |
| `cycle-10/frame.dat` | `857bf180560491427f5f09ee776713604b466fc5cfc32c7cb4bda68e4b86b2ca` |
| `cycle-10/frame.frd` | `110a3977e07dc21c54cbfdaf6c670c6e5838451806a93b87f13d61cc153bbed8` |
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

The direct shifted-post/base-header bearing carries 99.63 N. All four samples
are compressive. The governing interface remains `rear_block_post`, with a
133.54 N resultant force and approximately 6.03 kN·mm resultant moment. The
largest simultaneous bolt demand is 68.99 N lateral shear and 26.37 N tension,
or 73.86 N combined. Moving the link materially redistributes this one case:
the governing combined bolt decreases by 10.19 N relative to the earlier Z202
result, while four PB02 bolts now carry positive axial tension.

The preliminary conditional DF-L post-high lateral screen reaches 0.1513 after
its reduced `CΔ` factor. Using the smaller thread-root sensitivity increases
that ratio to 0.1605. The separate block/header end-grain screen reaches 0.0746
and 0.0792 for the two root assumptions. These are component screens only; they
do not establish joint resistance or resolve splitting, group action, washer
metal behavior, prying, preload, or member interaction.

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
22.21 N corrected-case demand, a ratio of 0.0792. The 0.189-inch typical-root
sensitivity gives 297.61 N and a ratio of 0.0746. These are component references,
not complete joint values. The post-revision force directions do not form one
NDS row: they are neither mutually parallel nor aligned with the bolt-pair line,
so no two-bolt group factor applies. The isolated-bolt screen uses `Cg = 1.0`
with `n = 1` and `CΔ = 1.0` for this interface. The separate `post_high` member
records conditional `CΔ = 0.83015`. It does not qualify local multiple-fastener
stresses or splitting. This result does not require rotating
the block grain or moving to 4x8 stock solely for the current one-case demand.

The current 18.7 mm ligament between `post_high` and `post_cleat_2`, and the
20.2 mm ligament between `upright` and `cleat_link`, have no directly applicable
2024 NDS resistance equation for their crossed-bore interaction. Individual
dowel-yield, ordinary row-spacing, net-section, Appendix E, and group-action
checks do not represent the local mixed-mode volume between perpendicular
bores from separate connections. The two centerline separations exceed the
project 4D = 25.4 mm target by 0.6 mm and 2.1 mm, respectively. This is not a
claim that the ordinary NDS row rule applies or that local splitting is
qualified. The inclined principal also has only 10.015 mm to one transverse
edge; it passes only the conditional unloaded 1.5D comparison in this case and
has just 0.49 mm nominal reserve before tolerance. A reversed transverse force
would fail the 4D loaded-edge comparison.

The authenticated [upright/link component
screen](simple-center-pb02-individual-component-screen.md) checks those two
single-fastener interfaces with their actual bearing lengths and force angles.
Mode IV governs; its largest conditional lateral ratio is 0.0756. That result
does not qualify the nearby crossed bores or the complete connection.

The [bore-aware net-section screen](simple-center-pb02-bore-net-section-screen.md)
retains axial force, biaxial bending, transverse shear, and separate torsion at
four relevant cuts. Three cuts use exact report rows. The inclined-principal
cut requires a clearly marked 5.691 mm free-body extrapolation below the
report-valid full-section interval, so it is not used as a capacity verdict.

Before any physical release, work still includes:

- resolve the inclined-principal local section and crossed-bore interaction;
- complete the `block_header` local wood checks;
- verify exact delivered bolts, thread-root diameter, nuts, washers, lumber,
  insertion routes, and tool access;
- complete bolt-row/group, perpendicular-tension, bore-aware member,
  washer-metal, preload, and prying checks; and
- run and envelope `a12-rear`, `a12-left`, `k12-right`, `k12-rear`, and
  `a1-rear` with the corrected mapping and revised geometry.

Until those items are completed and reviewed, PB02 remains developmental only:
**no drilling, fabrication, or construction is authorized.**
