# Structural insert options (investigation, not selected)

This is a later-option study. The build is still Hillman 42605 and SDS25112. The
twelve bolts stay bolts. No model change yet.

The question is: which **inserts publish strength numbers** and **edge
distances**, and could they sit on this frame if we later adjust geometry?

## Who actually publishes numbers

**Furniture zinc hex (E-Z LOK 801420-13 and kin).** No wood withdrawal, no
edge distance. [E-Z LOK testing](https://www.ezlok.com/testing) says hex-drive
results are not offered. Occupancy on this frame is in
[screw-repair-inserts.md](screw-repair-inserts.md). That path is take-apart
convenience, not a rated joint.

**RAMPA steel inserts, ETA-12/0481 (EAD 130324-00-0603).** This is the product
class that is meant for load-bearing timber and that publishes:

- Characteristic withdrawal `fax,k` = **9 N/mm²** in softwood (glulam, CLT,
  LVL, solid timber), 13 N/mm² in hardwood.
- Steel tensile `ftens,k` by SKU (about 9.8 kN for M5 / D=10 mm, 17 kN for
  M6 / D=12 mm, 37 kN for M8 / D=16 mm).
- Lateral capacity from Eurocode 5 using the **outer** diameter D.
- Tested edge distances, including a reduced **1.5 D** to an unloaded edge
  when the insert is **only axially loaded**.

ETA (English): [RAMPA ETA-12/0481](https://www.rampa.com/media/35/3f/9c/1671462200/ETA120481%20HB%20RAMPA%20r3%202020_22_03_2021.pdf).
Maker summary: [RAMPA ETA page](https://www.rampa.com/eu/en/products/eta)
(they stock BL and SKL; other types on request). North American supply is
specialty (e.g. Spaenaur), not a Lowe’s bin.

**Simpson Timber-SET glued-in rods, ESR-5283.** Published ASD for threaded
rods **epoxied** into timber. The rod does not unscrew from the wood; take-apart
would be a nut on a protruding rod. Different architecture, long embedment,
not a drop-in for SDS holes.

**Keep SDS / use through-bolts.** SDS25112 already has ESR-2236 numbers
(172 lbf/in DF withdrawal, Wmax 170 lbf; steel-side shear on the order of
250 lbf). ML24Z with six SDS is **595 lbf** F1 in DF (L-C-MLZ25). A 1/4 in
bolt through the same wood is NDS, take-apart, and does not need an insert.

Würth ASSY, Rothoblaas, SFS, Eurotec and similar **structural screws** have
ETAs. They are not inserts. Backing them out repeatedly is the original
problem.

## RAMPA wall rules versus this frame

Outer diameter D is the thing that needs wood around it.

| Rule (RAMPA ETA-12/0481, solid timber) | For D = 8 mm (M4) | D = 10 mm (M5) | D = 12 mm (M6) | D = 16 mm (M8) |
| --- | --- | --- | --- | --- |
| Unloaded edge, **axial only** 1.5 D | 12 mm | 15 mm | 18 mm | 24 mm |
| Unloaded edge, general 2.5 D | 20 mm | 25 mm | 30 mm | 40 mm |
| Loaded edge 6 D | 48 mm | 60 mm | 72 mm | 96 mm |
| Spacing along grain 4 D | 32 mm | 40 mm | 48 mm | 64 mm |
| Min thread length 1.2 D | 10 mm | 12 mm | 14 mm | 19 mm |

Our measured axis-to-face:

- **66 panel/kicker:** 19 mm (center of a 38.1 mm 2×6 face). Depth behind the
  plywood ~140 mm.
- **110 SDS:** ≥ 19.5 mm, most ≥ 25 mm.
- **34 SDS** (outer ML24Z holes, front of the 2×6): **12.5 mm**. Depth through
  the 38.1 mm stock ~38 mm.

So, without moving anything:

- **D = 8 mm (SK M4):** 12.5 mm just meets **axial 1.5 D**. It misses 2.5 D
  and 6 D. Only plausible if that hole is treated as axial-only — the angle
  joint is not.
- **D = 10–12 mm:** panel 19 mm meets **axial 1.5 D** (15–18 mm). Misses
  2.5 D (25–30 mm) and 6 D. The 34 SDS holes miss even 1.5 D for D = 10
  (need 15 mm).
- **Loaded-edge 6 D** does not exist on a 38.1 mm face for any ETA size.

Example characteristic withdrawal, softwood `fax,k` = 9 N/mm², one insert,
kax = 1, ρk = 350 kg/m³ (C24; DF-L is denser, so this is conservative):

`Fax,k = 9 × D × lef` (N)

| SKU (examples) | D × lef | Fax,k | vs SDS Wmax 170 lbf ASD |
| --- | --- | --- | --- |
| SK 010 412, M4, L=12, lef~10.5 | 8 × 10.5 | 0.76 kN (~170 lbf char.) | Similar ballpark, different safety basis |
| SK 010 514, M5, L=14, lef~12 | 10 × 12 | 1.08 kN (~240 lbf char.) | |
| SK 010 618, M6, L=18, lef~15 | 12 × 15 | 1.62 kN (~360 lbf char.) | |
| SKL 011 640, M6, L=40, lef~37 | 12 × 37 | 4.0 kN (~900 lbf char.) | Needs ~40 mm of wood along the axis |

Eurocode design values are Fax,k × kmod / γM, not NDS ASD. Do not treat
360 lbf characteristic as 360 lbf allowable. Steel `ftens,k` is much higher
than the wood withdrawal; the wood governs.

Plywood is allowed on the **metric-screw / head** side of a RAMPA joint. That
matches a panel conversion (clearance in the ply, insert in the 2×6).

## Reasonable later paths (still not selected)

**A. Panels only, RAMPA M6 (D=12) or M5 (D=10), axial-edge reading.**
The 19 mm face is the one that matches RAMPA’s **1.5 D axial** rule for M6.
Use SK / SKL long enough that lef ≥ 1.2 D (18–25 mm is easy in 140 mm of
2×6). Treat panel peel as axial. If we later decide panel shear toward that
38.1 mm edge is real, 19 mm is short of 2.5 D and we would move those rows
inboard or accept a thicker rail. This is the first structural-insert
candidate worth a geometry sketch.

**B. Leave SDS. Convert nothing in the angles.**
Keeps 595 lbf F1 and ESR-2236. Matches “take the wall apart at the twelve
bolts and lift the plywood.” Best default.

**C. Replace SDS with through-bolts in the same ML24Z holes (or a new
bolted angle).**
NDS, take-apart, no insert. 12.5 mm is more than **1.5 D of a 1/4 in bolt**
(9.5 mm) and less than **4 D loaded** (25 mm). Same loaded-edge problem as
the fat insert, but the fastener is the catalog 1/4 in we already analyzed
for SDS diameter. Enlarging ML24Z holes or switching to a bolt-pattern
angle is a new connection. Custom fabricated shoes stay off the table.

**D. Move the 34 outer SDS axes so a RAMPA D=10–12 insert sees ≥ 2.5 D
(25–30 mm) or at least 1.5 D (15–18 mm) if we argue axial-only.**
That is a clip-station / member-face change, then fresh geometry and
affected cases. It is the structural-insert version of “adjust the model.”
Do not do it until A/B/C is chosen. 6 D loaded edge still wants ~60 mm and
would force a wider face than a single 2×6.

**E. Glued-in rods (Simpson Timber-SET).**
Published ASD, not a shop conversion of 210 screw holes, not take-apart at
the wood thread.

**F. E-Z Hex on panels only, SDS untouched.**
No published insert strength. Geometry already fits. Fine as a worn-hole
repair; not a rated substitute.

## What would have to change if we picked A or D later

- New candidate module (not another silent overlay).
- Hardware schedule: RAMPA SKU, metric machine screws, pre-drill from the
  ETA (`ddrill,SW` 7–10 mm for M4–M6), plywood clearance on the screw side.
- Edge check against 1.5 D vs 2.5 D vs 6 D, stated as axial vs lateral.
- Do not transfer ML24Z / SDS numbers to RAMPA. Do not transfer SPAX or
  Hillman either.
- Six-case evidence does not move with the hardware.

Until then: build the current packet. This file is a map, not a shopping
list or a machining release.
