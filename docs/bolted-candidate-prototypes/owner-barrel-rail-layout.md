# Direct barrel-nut ten-rail viewer layout (Track A)

This is a detached, source-distinct kerf-right development concept built on
the selected kerf-right member geometry and 24-duty ledger. It replaces ten
historical angle/SDS duties *only in this study* with two direct
rail-end-to-upright cross-dowel stacks each. The candidate includes **zero
legacy brackets**. All 66 existing panel/kicker axes and 12 retained
frame-bolt axes are read unchanged. The
owner-approved ±180 mm center **posts** are moved in the model; the rail
duties instead meet the distinct center **principal** members, so all ten
actual rail/principal or rail/side butt mismatches are 0 mm. The 139.7 mm
rearward rail envelope is retained.

Each station exposes real cut rail/upright wood and two perpendicular bore
pairs: a 7.5 mm trial machine-bolt bore along the rail grain and a 10.0076 mm
trial blind barrel bore through rail thickness. The modeled bore intersections
are 408.385–408.396 mm³ per row, and both provisional barrel bodies remain
within their rail. Rows are 60 and 92.25 mm from the rail N front; the rear
7D marker reserve is 3.0 mm. Opposite rail T faces are used for barrel entry.
Generic bolt, barrel, bolt-drive, and barrel-insertion/access solids are
exposed by `build_geometry()`. The `build_layout(wood)` assembly adapter uses
the caller's exact owner-frame wood pose and returns named bolt axes, barrel
solids, shaft-only stacks, both drilling paths, and both access paths per row.
Blocked direct trials remain `mode="direct"` with a `REVISE` disposition. Their
bolt and barrel axes remain visible as diagnostics; there is no alternate
wood block or fallback joint in this layout. No catalog drilling diameter,
tool path, installation sequence, or delivered fit is established.
The whole-frame assembly's rail10 producer map must name
`scripts.owner_barrel_rail_layout`; an older draft expects
`scripts.owner_barrel_rail10`.
The generator derives rail/upright hosts from the selected-baseline duty ledger,
and rail-end direction from the actual kerf-right member bounds. Its parent
source is `compact-floor-flush-kerf-right`; it imports no corner-block or PB
geometry module. The three barrel producers share only neutral 50° coordinate
math in `scripts/owner_barrel_coordinates.py`.

The provisional pose reuses `simple_cross_dowel_continuation.py`:
Hillman 880543 nominal 0.394-in OD and 0.630-in length, 1/4-20 thread,
5-in bolt, and 0.065-in washer sensitivity. The thread axis is **assumed** at
the nominal body center, 8.001 mm from either end. The 6–10 mm axis-offset
sensitivity remains open. Lowe's 3012559 and Home Depot Internet 202242356
identify the retail part, not its controlled geometry, material strength,
thread engagement, or complete wood-joint capacity. No manufacturer was
contacted.

A readback of the direct screen gave these station dispositions:

| Duty | Direct trial | Protected / unrelated wood |
| --- | --- | --- |
| Lower center left | Geometry-only | 0 / 0 hits |
| Lower center right | **Blocked** | 1 / 0 hits |
| Lower outer left/right | Geometry-only | 0 / 0 hits each |
| Upper outer left/right | Geometry-only | 0 / 0 hits each |
| Upper center left | Geometry-only | 0 / 0 hits |
| Upper center right | **Blocked** | 1 / 0 hits |
| Bottom outer left/right | Geometry-only | 0 / 0 hits each |

The exact protected-solid names and volumes are returned by each station's
`protected_hits_mm3` dictionary. The two blocked right-center duties remain
direct barrel poses labeled REVISE in the assembly adapter. The screen retains
their protected-volume collisions and bore geometry; there is no cleared
relocation or alternate joint. Their service access, load path, and stock
hardware remain to be developed.

Overall disposition: **DEVELOPMENT_REVISE**. Even eight geometry-only poses
are not fit or structural passes. Generic access cylinders and finite T-nut,
hold-hole/protrusion, LED/wire, panel-screw, and retained frame-bolt solids
are screened, but actual tool wall/approach, installed screw heads, delivered
bolt/washer/barrel dimensions, thread engagement, and physical assembly are
unverified. No native solve, drilling, fabrication, or climbing release.
The standalone screen shifts the two center posts but does not add the
separate kicker backers; `build_layout(wood)` consumes the assembly's exact
wood dictionary, including those backers. Whole-frame integration may find
additional interactions and must keep the REVISE label.
