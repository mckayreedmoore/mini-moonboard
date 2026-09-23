# Later insert option (not this build)

Build with the specified wood screws and the twelve bolt stacks. This note is
only a **later option**: if you take the plywood off often, or a wood screw
wears out, those screw holes can become threaded inserts. Do **not** drill
insert pilots now.

The twelve frame bolts already come apart. They stay bolts.

## What was checked

On `compact-floor-flush-development`, every **wood-screw** axis was screened
against the old E-Z LOK **801420-13** envelope (1/4-20, 13 mm long, 11.5 mm
outside diameter, drawing ±0.635 mm). The insert sits in the timber after the
plywood or after the ML24Z steel. Uncut receivers, current stations.

| Family | Count | Body in the wood | Inserts overlapping each other or a bolt |
| --- | --- | --- | --- |
| Hillman 42605 panel/kicker | 66 | Yes, including max drawing size | None |
| SDS25112 in ML24Z | 144 | Yes, including max drawing size | None |
| Frame bolts | 12 | Not an insert job | — |

Smaller hex inserts in the same family (10-24 **801024-13**, 8-32 **800832-10**)
also fit. Depth is not the limiter: after a 13 mm insert there is still about
126 mm of 2×6 behind every panel/kicker screw, and at least 24 mm behind every
SDS.

The tightest SDS axes are about **12.5 mm** from a wood surface (~6.7 mm of
wood outside a 1/4-20 body). Panel/kicker axes are about **19 mm** from a
surface (~13 mm outside that body). The header kicker row goes into the
**139.7 mm** depth of `base_header`, not through the 38 mm face height.

`tests/test_floor_flush_later_inserts.py` repeats the occupancy screen. Occupancy
is not a strength rating, split check, or machining release.

## Guides and numbers (revisited)

E-Z LOK’s own hex-drive page is for furniture, drawer pulls, display cases and
crating. Their [testing page](https://www.ezlok.com/testing) states that
results for hex-drive inserts **are not offered**; they send samples. There is
therefore **no published withdrawal, lateral, or edge-distance allowable** for
801420-13 in Douglas-fir. Metal-insert tensile tests (bolt breaks in aluminum
at about 5,000 lbf for 1/4-20) are not wood values.

What *is* published, and how our walls sit:

**Furniture (Woodcraft brass-insert guide, 2013).** Cross-grain: centerline at
least **2 × pilot diameter** from an edge. For their 1/4-20 (pilot 3/8 in) that
is **19.05 mm**. End grain: 1 × pilot. Spacing 4 × pilot. That guide is
knock-down furniture, not a climbing frame.

**Structural timber inserts (EOTA EAD 130324-00-0603).** Load-bearing inserts
are **steel**, outer thread 8–40 mm, outer length at least **1.2 d**, tip
penetration **3 d**, pre-drill 0.5–1 mm over the *inner* thread. Edge distances
default to Eurocode 5 Table 8.2 for **pre-drilled nails**, using the **outer**
diameter: unloaded edge **3 d**, loaded edge **(3+4 sin α) d**. For d = 11.5 mm
that is **34.5 mm** unloaded and up to **80 mm** loaded. A 13 mm zinc hex is
not that product (too short, wrong metal, inner/outer ratio ~0.55 vs the EAD
0.75–0.94 band). The EAD is the closest *structural* insert document; it does
not qualify this SKU.

**NDS analogue (dowel-type, D = insert OD).** Bolts/lags: unloaded edge
**1.5 D**, loaded edge perpendicular to grain **4 D**. For 11.5 mm that is
**17.3 mm** and **46 mm**. Wood screws smaller than 1/4 in have no NDS table;
commentary C12.1.5.7 suggests **2.5 D** edge when prebored. NDS 12.1.5.7 for
wood screws is “sufficient to prevent splitting.”

**What the SDS already is.** Simpson SDS25112 in DF: reference withdrawal
**172 lbf/in** of thread, **Wmax 170 lbf** for the 1-1/2 in screw (ESR-2236 /
C-F catalog). Steel-side shear about **250 lbf** (ESR-2236) to a few hundred
pounds depending on plate thickness. The **ML24Z** with six of those screws is
rated **595 lbf** F1 in DF (L-C-MLZ25). Those numbers apply to the SDS in that
angle, not to an insert.

**Our stations versus those rules (1/4-20, OD 11.5 mm, pilot 23/64 in):**

| Station | Axis to face | vs Woodcraft 2×pilot (19 mm) | vs NDS 1.5 D (17 mm) | vs EC5 3 d (35 mm) | vs NDS 4 D (46 mm) |
| --- | --- | --- | --- | --- | --- |
| 66 panel/kicker | **19 mm** | Meets | Meets | No 2×6 face can | No |
| 110 SDS | ≥19.5 mm (most ≥25 mm) | Meets | Meets | 86 of 144 meet 3 d | No |
| **34 SDS** (outer ML24Z holes, front of 2×6) | **12.5 mm** | Miss | Miss | Miss | Miss |

Pilot clearance is not the issue: even at 12.5 mm there is ~8 mm of wood
outside the 23/64 in bit. The 34 tight SDS holes leave ~6.8 mm of fir outside
a 1/4-20 *body*. That is enough for occupancy, not enough for the furniture
2×pilot rule or a timber 1.5 D / 3 d wall. An 8-32 hex (OD 6.9 mm) is the
only size in this family that meets Woodcraft 2×pilot at those 34; it still
misses EC5 3 d.

So: panel conversion at 19 mm matches the only published *furniture* edge
rule for this insert size. SDS conversion has no catalog strength, drops the
Simpson joint, and at 34 holes does not have the wall those guides want for a
1/4-20 body. Do not move the frame for this. Leave SDS as SDS unless you
accept an unrated angle joint and, on those 34, a smaller insert.

Inserts that **publish** timber strengths and edge distances (RAMPA
ETA-12/0481 and related paths) are sketched in
[structural-insert-options.md](structural-insert-options.md). That study does
not change this build.

## If you convert later

1. **Bolts:** replace the bolt.
2. **Hillman (66):** take the plywood off. Open the plywood hole to a machine-screw
   clearance (the old study used 7 mm; that is a size check, not a bit call).
   Drill the timber to the insert pilot (23/64 in for 801420-13, 9/32 in for
   801024-13, 15/64 in for 800832-10). Seat the insert in the timber, slightly
   below the wood face. Use a 1/4-20, 10-24, or 8-32 machine screw through the
   plywood into the insert. Measure the real edge before driving an 11.5 mm
   body at a 19 mm row.
3. **SDS (144):** leave the ML24Z holes as they are (**6.731 mm**). Do not
   enlarge the steel. A 1/4-20 screw (major diameter up to 6.32 mm) is a snug
   pass through that hole; 10-24 or 8-32 pass more easily. The insert goes in
   the timber under the angle. This is **not** a Simpson SDS25112 joint any
   more: listed ML24Z values do not apply to an insert plus a machine screw.
   At the 34 outer-hole stations with only 12.5 mm to the front of the 2×6,
   do not use 1/4-20 if you care about insert wall; 8-32 is the size that
   meets the furniture 2×pilot rule there.

Do not mix leftover Hillman or SDS into an insert hole. Do not pre-drill
insert pilots “just in case” while you are still using wood screws.

## What this does not do

It does not install inserts, pick a repair kit, or give torque, engagement, or
allowable load. The old `round-insert-development` study used 56 panel screws
on a different frame; do not copy its counts or resistance. Repeated assembly
of the **angles** is a different connection once the SDS are gone. Whole-wall
moves should still separate at the twelve bolts and lift the plywood; you do
not have to convert SDS in order to move.

Inserts that **publish** timber strengths and edge distances are sketched in
[structural-insert-options.md](structural-insert-options.md). That study does
not change this build.
