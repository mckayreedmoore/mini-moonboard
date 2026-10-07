# HL35 current proposal: complete clearance and after-recess wood assessment

`compact-floor-flush-hl35-development`, revision
`hl35-deeper-header-seat-and-bearing-audit-v8`, is a separate **REVISE** proposal.
The overnight candidate-creation and evaluation attempt is complete. It did
**not** produce a build-ready or structurally accepted frame.

See the [contract](../../../../../hl35-candidate.json),
[interactive candidate](../../../../../site/index.html?model=hl35-counterbore-development),
[preview](overview.png), [assessment](fit-assessment.json) and [manifest](manifest.json).
The selected baseline and reviewed wood model remain unchanged.

## Current result

| Check | Result |
|---|---:|
| Former block duties covered | 24, mapped to 22 new joints |
| HL35 envelopes / physical structural bolt axes | 30 / 112 |
| Purchased Hillman panel/kicker screw count | 66 |
| Full 88.9 mm wood probes after washer recesses | **112 / 120** |
| Full nominal flange seats after washer recesses | **52 / 60** |
| Lower corner joints needing geometry revision | **4 / 22** |
| Remaining angle, full metal, screw or service-body clashes | **0** in the enumerated exact-solid checks |
| Receiving timbers disconnected by proposed machining | 0 / 16 |

The affected joints are `principal_header_outer_left/right` and
`kicker_header_outer_left/right`. Eight receiving probes intersect another
joint's washer recess. Four retain about **99.95%** of full probe volume;
four about **99.06%**. These are geometric diagnostic fractions, not effective
thicknesses, allowable deductions or capacity ratios. Eight beam flange seats
retain **85.8–87.4%** of nominal bearing skin. No reduced-area or spanning-steel
resistance is established. These findings stop the affected operation; the
other eighteen joints remain **UNQUALIFIED**, rather than accepted.

The supplemental v7 query found eight bolt-tip/angle contacts and four bolt-tip
contacts with unrelated timber. V8 deepens the 28 conditional header washer
seats from **25.4 to 31.75 mm**, shortens corresponding planning stacks and
includes the missing metal/angle and unrelated-shaft checks. Those clashes
clear, but the after-recess wood check exposes the four failures above.
A clear bolt tip does not establish a supported joint.

The earlier zero-clash result covered a narrower set, and v7's wood probes
preceded the HL35 washer-recess subtraction. Its [failed closure](../final-fit-v7/hardware-closure.json)
and earlier bytes remain preserved. V8 checks receiving wood after **all**
washer recesses and service voids, before intentional shaft/pilot holes;
that avoids misreporting a bolt's own bore as absent stock.

## Recorded changes and limits

The common solid 6×8 center replaces two thin principals and combines two pairs
of former duties. Bottom rails use 6×6 envelopes; service/top rails use 4×6;
the header has a shaped 6×10 envelope, proposed length **2,638.425 mm**. Outer
rims remain solid 4×6 sections with changed foot/top stations. Outer kicker
posts shift 19.05 mm outward and have lower side relief beside retained runners.
One 4×4 seam backer has two proposed 5/16-inch through ties. These are stock/cut
proposals, not approved dimensions. Detailed dimensions and all station moves
are in the assessment and preceding packets.

The 112 axes comprise **98 HL35 through bolts**, **12 starting frame-bolt lines**
and **2 auxiliary ties**. Four front grips change from 76.2 to 107.95 mm.
Products, actual shanks/threads, washer resistance and tools remain unqualified.
Deeper header seats leave axis-center spans of at least approximately **94.8 mm**;
that centerline length does not remedy the eight incomplete full wood probes.

The purchased 66 Hillman 42605 screws remain. Four upper kicker rim/center axes
move from Z192 to Z173.05 mm; four upper main rim/center `..._4` axes move
19.05 mm upslope. Every old/new point and receiver is recorded. Panel outlines,
holds, T-nuts and LED endpoints, including G2, remain unchanged. Heads use the
owner-measured 9 mm diameter and an unmeasured 3 mm height envelope. No inspection
or drilling is claimed. Three approximately **203.77 mm** wire doglegs retain
both endpoints; unused slack, feeding and physical routing remain unqualified.

The 405 source service bodies—132 lights, 131 wires and 142 T-nuts—are checked
against retained asset hashes and bounds before the three route proposals.
Conditional voids clear their nominal occupancy. Curved/enclosed swept voids
do not demonstrate practical machining, assembly or net-member resistance.
The static preview omits metal stacks and service bodies; the interactive
scene retains them. It is CAD, not an observed build or browser screenshot.

At an explicitly assumed **500 kg/m³**, the sixteen finished receivers alone
are **342.2 lb / 155.2 kg**, including roughly **69 lb center** and **62 lb header**.
Legs/runners, plywood, holds, all metal and electrical parts are excluded.
This is not total wall weight or delivered density. Heavy individual pieces
are a substantial transport compromise.

Eight joints have opposing angles; fourteen single-angle ends need a separate
compression/contact return path. They do not inherit bidirectional lateral
pair qualification. Current factory geometry, gauge, provisional 50.8 mm hole
offset and 5 mm flat steel envelope remain explicit; see the
[catalog basis](../README.md#catalog-basis-and-limits). No transverse/moment
capacity, doubled lateral rating or complete joint resistance is supplied.

The original **250 lb / 2× downward / 300 N horizontal / 100 mm lever** envelope
remains. No new frame demands, own-weight reactions or timber/panel resistance
were solved. Preserved panel head/rolling-shear concerns and the unverified
no-slip floor assumption remain. No native solve or release exists.

**Next redesign the four lower interfaces** so bolt tails and washer seats
clear adjacent joints without removing their receiving/bearing wood. Recheck
changed members, bolt groups, screws, services and room/transport envelopes.
Then establish complete signed force/moment paths, actual products, practical
machining/access and candidate-specific demands including dead weight.

## Reproduction and retention

```bash
.venv/bin/python -m scripts.hl35_counterbore_candidate
MPLCONFIGDIR=/tmp/mini-moonboard-matplotlib .venv/bin/python -m scripts.render_hl35_candidate --scene site/hl35-counterbore-scene.json --out docs/wood-joints-mvp/hypotheses/hl35-candidate/counterbore-fit-v8/overview.png
.venv/bin/pytest -q tests/test_hl35_candidate.py tests/test_export_wood_joint_design_review_scene.py
node scripts/check_hl35_scene.mjs /PATH/TO/three.module.js
```

The **10,725,476-byte** delta retains detailed proposed recesses and services,
with repeated metal instances and shared unchanged assets. Exact-solid checks,
known-answer controls and source/release guards are distinct from strength
qualification. The current summary/ledger record verification outcomes.
All distinct failed v1–v7 bytes and dependent helpers remain recoverable.
No source, another agent's file or raw run was pruned. No stage/commit/push
occurred. Archive closed bulky exports only through the verified repository
archive/prune process after checking current consumers.
