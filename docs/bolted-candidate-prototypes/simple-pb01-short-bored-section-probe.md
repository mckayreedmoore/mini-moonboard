# PB01 six-inch bored-section geometry screen

This is a bounded, source-bound analytical screen of the 152.4 mm
`quarter_short` bolted solid-wood corner block (`cleat` in older machine
identifiers). It calls the maintained
`simple_rail_joint_comparison.compare(quarter_n_length=152.4)` pose producer
and reads its four actual diagnostic bore reports. It does not create a new
variant, move geometry, run a native solve, or alter preserved evidence. The
pose retains all 66 fixed panel/kicker axes.

The block is 139.7 mm in local X, 57.15 mm in local T, and 152.4 mm along
grain N. Its front is N=209.841 mm. The diagnostic bore diameter is 7.5 mm;
this is a CAD envelope, not a drill instruction. `u1` and `u2` run along X
at N=265 and 310 mm, centered across T. `r1` and `r2` run along T at
N=290 mm, at local X=70 and 110 mm. The bores fully penetrate the block in
their respective transverse directions according to the pose producer.

## Grain-normal bore-center cuts

At each bore center, a plane normal to grain N intersects the cylindrical
bore as a full-width rectangular strip. The X-axis bores remove a 7.5 mm
strip through the full X width. The two T-axis bores share one plane and
remove two 7.5 mm strips through the full T depth. These three cuts are the
minimum-area planes in their separate, nonoverlapping N bore bands. Gross
area is 7,983.855 mm². Moments below are centroidal principal second moments
of the remaining planar wood about local X/T directions. The product moment
is zero for these exact symmetric full-span strip profiles. The rail pair's
asymmetric X placement shifts its net centroid to X=67.426 mm.

| N plane, mm | Intersecting bores | Removed, mm² | Net, mm² | Net/gross | Principal I min / max, mm⁴ |
| ---: | :--- | ---: | ---: | ---: | ---: |
| 265 | u1 | 1,047.750 | 6,936.105 | 0.86877 | 2,168,109 / 11,280,471 |
| 290 | r1 + r2 | 857.250 | 7,126.605 | 0.89263 | 1,939,697 / 12,247,620 |
| 310 | u2 | 1,047.750 | 6,936.105 | 0.86877 | 2,168,109 / 11,280,471 |

The smallest net **area** is at either upright bore. The smallest principal
second moment is at the rail pair. Neither observation ranks joint failure
modes or proves an allowable load. This calculation concerns analytical CAD
voids only. It supplies no wood species/grade strength, adjusted design
value, stress demand, combined-stress interaction, or capacity. It also does
not check local remaining walls, bearing, loaded-end tear-out, splitting,
washer pressure, group action, or complete joint equilibrium. Principal
moments describe planar elastic geometry; using them for strength requires
the applicable demand and failure model.

The existing 300 mm and short-block native archives and prior screens remain
historical diagnostic evidence. Their loads are not transferred into this
section result. This screen makes no capacity decision, drilling release, or
construction release. Reproduce the JSON with
`uv run --no-sync python -m scripts.simple_pb01_short_bored_section_probe`.
