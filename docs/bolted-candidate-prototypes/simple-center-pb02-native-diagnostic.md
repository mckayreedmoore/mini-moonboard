# PB02 corrected `a12-forward` decision record

## Decision

**REVISE THE CONTACT DISCRETIZATION; retain PB02 for development.**

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

## Archived pre-contact-cell-correction evidence

The original current-geometry evidence package is retained only as historical
pre-contact-cell-correction evidence:

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

That historical case converged in 11 cycles. The report passes the recorded contact and
axial unilateral checks, member and global equilibrium checks, MPC checks, and
positive-load-work gate. All retained artifacts referenced here match the
hashes above. Numerical acceptance does not qualify the modeled demands as
design demands.

## Contact-cell correction and bounded reruns complete

A subsequent exact-face audit found that `principal_upright_block/contact_1`
lies 0.791 mm outside the true principal/cleat overlap while carrying 17.18 N.
The old four equal interface springs also had no tributary areas and used equal
stiffness regardless of actual face polygon. That result remains an
authenticated numerical record, but its force distribution is not current
joint-demand evidence.

The current adapter now intersects the two true CAD faces at each of the seven
canonical interfaces, subtracts the exact circular bolt-hole footprints, and
partitions the remaining face into finite tributary cells. It verifies positive
cell area, complete net-area coverage, exact first moments, contained cell
centroids, deterministic ordering, and a source-bound partition fingerprint.
Every canonical spring uses one common areal stiffness calibrated so the mean
interface total equals the selected developmental input. The unequal interface
totals are therefore explicit consequences of unequal net face areas. The four
direct shifted-post/header samples remain a separate equal-total contact law.

Both 2x2 and 4x4 native partitions are selectable without changing source. The
4x4 source partition has 110 positive components. At the inclined principal
end, two 2x2 parent tiles are each represented by one area-weighted spring
because their individual fine-cell centroids fall outside the retained beam
centerline end. This produces 104 native contact springs while preserving exact
area and first moments and without extending fictional timber. A coalesced tile
reports one average pressure; it cannot resolve partial opening or a local
pressure peak inside that tile.

An 8x8 partition is generated deterministically for the required fallback
refinement check. Perforated fine cells recursively subdivide only when a face
centroid would fall inside a bore footprint; unsupported inclined-end cells are
promoted to their containing 2x2 coarse parent tile. The 8x8 native inventory
contains 410 contact springs and preserves the same exact net areas and first
moments.

The runner authenticates partition identity, area-derived stiffness, cell
ownership, physical force direction, and per-interface force, moment, active
area, and peak cell-average pressure. Physical opening/closing tests and 2x2,
4x4, and 8x8 partition tests pass. All three corrected `a12-forward` grids are
numerically accepted. From 4x4 to 8x8, force changes at most 3.287%, moment at
most 8.186%, maximum bolt demand 0.697%, and panel displacement 0.000242%.
The 8x8 result is retained for developmental global force and moment demand.
Active area and peak cell-average pressure remain grid-sensitive by 48.195%
and 21.091%, so neither is locally qualified.

At 8x8, the 0.5x/1x/2x contact-density range changes the governing combined
bolt force from 60.32 N through 80.76 N to 99.50 N. Maximum interface-force and
moment ratios are 1.738 and 5.083. The density is not qualified; the 2x case is
used only as the current bounded same-case component screen. The authenticated
[evidence package](../../fea/results/diagnostics/pb02-contact-refinement-a12-forward-v1/README.md)
preserves all five runs. The older archived forces and dependent screens remain
pre-contact-cell-correction history.

## Corrected load path and current bounded demand

The applied `a12-forward` load is `[0, -300, -2224.11] N`, in addition to
modeled self-weight. The center-right load travels through three connected
routes:

- base header to shifted post through direct wood bearing and the
  `block_header` to `post_block` path;
- base header to principal through `header_principal_block` and
  `principal_block_principal`; and
- principal to upright to rear cleat to shifted post through the return path.

The archived equal-spring result reported 99.63 N at the direct bearing,
133.54 N and approximately 6.03 kN·mm at `rear_block_post`, and a governing
73.86 N combined bolt demand. Those values are historical only and are not
current component demands.

The current bounded component screens use the corrected-contact 8x8
density-2x `a12-forward` sensitivity. Its governing bolt is
`rear_block_post/bolt_2`, with 97.92 N lateral shear and 17.66 N tension, or
99.50 N combined. Four bolts carry positive axial tension. The current
principal/upright and upright/rear single-fastener lateral-yield ratios are
0.1158 and 0.0925 at the smaller-root sensitivity. The current
`block_header` end-grain ratios are 0.1203 for the typical root and 0.1277 for
the smaller root. These are unqualified same-case component sensitivities, not
design demands or complete joint resistance.

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
35.81 N density-2x demand, a ratio of 0.1277. The 0.189-inch typical-root
sensitivity gives 297.61 N and a ratio of 0.1203. These are component references,
not complete joint values. The current force directions do not form one
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
Mode IV governs; its largest conditional lateral ratio is 0.1158. That result
does not qualify the nearby crossed bores or the complete connection.

The [bore-aware net-section screen](simple-center-pb02-bore-net-section-screen.md)
retains axial force, biaxial bending, transverse shear, and separate torsion at
four relevant cuts. Three cuts use exact report rows. The inclined-principal
cut requires a clearly marked 5.691 mm free-body extrapolation below the
report-valid full-section interval, so it is not used as a capacity verdict.

The authenticated [hardware screen](simple-center-pb02-hardware-screen.md)
checks all ten one-case demands against the existing conditional A307 direct-
shaft comparator. Its governing linear ratio is 0.2269. The idealized 20 mm
washer-envelope wood-bearing sensitivity reaches 0.01505, but no actual washer
ID, thickness, material, or bending resistance is established.

Before any physical release, work still includes:

- resolve the inclined-principal local section and crossed-bore interaction;
- complete the `block_header` local wood checks;
- verify exact delivered bolts, thread-root diameter, nuts, washers, lumber,
  insertion routes, tool access, and the steel long-grip method's applicability;
- complete bolt-row/group, perpendicular-tension, bore-aware member,
  washer-metal, preload, and prying checks; and
- run and envelope `a12-rear`, `a12-left`, `k12-right`, `k12-rear`, and
  `a1-rear` with the corrected mapping and revised geometry.

Until those items are completed and reviewed, PB02 remains developmental only:
**no drilling, fabrication, or construction is authorized.**
