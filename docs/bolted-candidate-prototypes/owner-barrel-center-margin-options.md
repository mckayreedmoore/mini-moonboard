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
| Minimum exterior tool-envelope gap (mm) | 4.003358 | 4.003358 |
| Minimum header pocket edge stock (mm) | 0.090167 | 3.090167 |
| Head / washer in header wood | 100% / 100% | 79.5042% / 79.9113% |
| Barrel radial X ligament (mm) | 2.0462 | 2.0462 |
| Mouth-relief X-side breakout (mm) | 3.45 | 3.45 |
| Disposition | Net section unqualified | Clash: unsupported stack |

Both alternatives have no >1 mm³ protected, retained, inherited-service,
unrelated-wood, installed-pair, or residual exterior-mouth/driver clashes. Barrel
bodies, joined bore cores, and 4 mm bore extension past nominal bolt tips
remain contained. The oblique barrel cross-bore mouth opens slightly to
air (about 0.998 in-wood fraction); after 1 mm it is fully in principal
wood. The `barrel_tool` is a 40 mm envelope **outward from the face**; it
does not model tool travel down the 29–31 mm recess, barrel insertion, or
thread-hole orientation. The side-breaking mouth relief and 2.0462 mm barrel ligament are
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

## Reproducible 50° rear-face trial

`build()["fifty_degree_option"]` uses X offsets ±11.25 mm; header-rear
entry Z = 257.7/258.1 mm at Y = -175.7 mm; 13.1 mm seat depth, 100 mm
seat-to-thread depth, 5 in/4½ in bolts, and a 21 mm pocket starting 13 mm
outside the header. Right row 1 entry/seat/thread coordinates (mm) are
`(58.75,-175.7,257.7)`, `(58.75,-167.279482,267.735182)`, and
`(58.75,-103.000721,344.339627)`; row 2 uses X = 81.25 and entry
Z = 258.1. The barrel enters the principal rear broad face normal to it.

The screen finds 41.042477 mm minimum barrel recess, 2.501469 mm
minimum exterior tool-envelope gap, 2.092152 mm minimum header pocket edge stock,
full head/washer containment, and zero external barrel-tool mouth intrusion;
no side-breaking mouth relief is modeled. The 4 mm tip-bore extension is
contained. The barrel X ligament is still only 2.7962 mm and needs sizing.
The barrel is recessed at least 41.042477 mm; its insertion and thread-hole
orientation access were **not** modeled or verified.

**The sole detected collision is electrical service bore**
`bore_base_principal_center_right_072`: right row 1 bolt bore/shaft
overlaps it by 119.637598/50.821424 mm³; right row 2 bolt bore by
6.927263 mm³. No other modeled protected, retained, unrelated-wood,
installed-pair, or external approach-envelope clash was found. Source
record `_072` is a **38.1 mm-diameter** X-axis wiring bore with a 40.1 mm
modeled cutter through the 38.1 mm-thick principal, linking LED datums
F1 and G1; it is not a frame bolt axis. The source still models 132
lights and 131 wire segments, and
this trial's hardware does not hit their modeled solids. That supports a
*conditional inference* that a separately designed F1–G1 passage could
retain LED service duty; no replacement route, feed access, bend radius,
length/slack, or electrical continuity was verified. Active wiring stays
unchanged.

All three poses remain detached findings, not approved for integration,
drilling, fabrication, structural use, or release.
