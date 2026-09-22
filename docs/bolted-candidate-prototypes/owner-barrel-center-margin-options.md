# Integrated center principal/header margin study — detached CAD only

`scripts/owner_barrel_center_margin_options.py` source-builds the kerf-right
integrated-4×6 assembly. It changes no frame member, panel, fixed 66/12
axis, maintained producer, or direct cross-dowel joint family. No native
solve or release occurred.

The current pose has only 1.049 mm barrel recess. Its 19.05 mm header
pocket leaves 920.456403 mm³ of the modeled 20 mm driver in header wood
per row. The inherited right-principal service bore intersects row 1's
bolt bore/shaft by 934.510249/544.332475 mm³, and row 2's bore/shaft,
barrel body/cross-bore by 637.936359/331.470825 and
278.801935/297.078603 mm³, respectively. Source cutters were posed and
clipped to active receiving wood for these checks.

Both alternatives use principal X offsets ±12 mm, a 55° bolt axis
`(0, 0.573576, 0.819152)`, perpendicular rear-broad-face barrel axis
`(0, 0.819152, -0.573576)`, 21 mm header pockets starting 15 mm outside
the rear face, and 21 mm × 3 mm barrel-mouth reliefs. The pocket clears
the 20 mm bolt driver; without the mouth relief each 20 mm barrel tool
clips its principal by 54.893 mm³.

| Measure | Deep seat | Shallow 7.5 mm seat |
| --- | ---: | ---: |
| Header entry Z rows 1/2 (mm) | 257.3 / 258.0 | 260.3 / 261.0 |
| Seat / thread-axis depth (mm) | 15.5 / 100 | 7.5 / 108 |
| Minimum barrel recess (mm) | 31.189399 | 29.253670 |
| Minimum all-center tool gap (mm) | 4.003358 | 4.003358 |
| Minimum header pocket edge stock (mm) | 0.090167 | 3.090167 |
| Head / washer in header wood | 100% / 100% | 79.5042% / 79.9113% |
| Barrel radial X ligament (mm) | 2.0462 | 2.0462 |
| Mouth-relief X-side breakout (mm) | 3.45 | 3.45 |
| Disposition | Net section unqualified | Clash: unsupported stack |

Both alternatives have no >1 mm³ protected, retained, inherited-service,
unrelated-wood, installed-pair, or residual driver/tool clashes. Barrel
bodies, joined bore cores, and 4 mm bore extension past nominal bolt tips
remain contained. The oblique barrel cross-bore mouth opens slightly to
air (about 0.998 in-wood fraction); after 1 mm it is fully in principal
wood. The side-breaking mouth relief and 2.0462 mm barrel ligament are
structurally weak, **not** qualified by the clean collision result.

The 7.5 mm seat reduces 5 in nominal tip overshoot past the barrel far
wall from 20.3452 to 12.3452 mm. The 4½ in second tip instead stops
0.3548 mm inside that wall. A common 5 in second bolt is geometrically
contained with the same 4 mm bore-tip extension, but usable thread and
barrel through-exit are unverified. Full support of the 19.05 mm washer
at 55° requires at least `1.651 + 9.525 tan(55°) = 15.2541 mm` of seat
depth, so the whole requested 6.7–8 mm range fails that requirement.

For the same 0.7 mm Z stagger, analytic X-offset sensitivity (only ±12
fully collision-screened) is:

| Offsets | Tool gap (mm) | Barrel X ligament (mm) | Mouth breakout (mm) |
| --- | ---: | ---: | ---: |
| ±11 mm | 2.003663 | 3.0462 | 2.45 |
| ±12 mm | 4.003358 | 2.0462 | 3.45 |
| ±13 mm | 6.003100 | 1.0462 | 4.45 |

At ±12, a verified barrel socket OD ≤13.1 mm would be needed merely to
fit a 0.5 mm-radial-clearance relief inside the principal X side. No
socket is selected, and even that would not size the wood ligament.

Neither pose is integration-worthy or approved for drilling, fabrication,
structural use, or release.
