# Preserved HL35 v7: incomplete coverage followed by failed tip check

**Closed failed input.** The supplemental [complete-tip query](hardware-closure.json)
found eight shaft/angle contacts and four shaft/unrelated-timber contacts.
The zero-clash and wood-support counts below cover the original subset and
receiving wood before the HL35 washer recesses. They do not establish overall
fit. The [v8 assessment](../counterbore-fit-v8/README.md) is current and includes
both missing checks. All releases remain false.


`compact-floor-flush-hl35-development`, revision
`hl35-center-foot-wire-clearance-v7`, is a separate **REVISE / UNQUALIFIED**
proposal. The earlier nominal-fit subset was complete; the supplemental coverage failed;
structural acceptance, actual hardware, machining and physical assembly remain
open. The [contract](../../../../../hl35-candidate.json) does not select this
candidate or change either preserved wood authority.

Open the [interactive model](../../../../../site/index.html?model=hl35-fit-development)
or [static overview](overview.png). The overview omits metal stacks and service
bodies; those remain in the detailed interactive scene. Browser launch was
unavailable in this sandbox, so the preview is a source-bound CAD rendering,
not a browser screenshot or observation of a build.

## Layout and source-duty coverage

The 24 former block duties map to **22 joints** after the two center principals
become one solid center timber. The two former center/header duties become one
paired joint; the two former center/top duties also become one. The contract
maps every former duty to exactly one new joint. A separate kicker seam backer
has two proposed through ties, whose load transfer is unqualified.

There are **30 HL35 envelopes**, **120 flange-hole attachments**, **98 physical
HL35 through-bolt axes**, **12 starting frame-bolt lines** and **2 auxiliary
5/16-inch tie axes**: **112 structural planning axes** in total. Opposing
flanges share their physical through-bolts; attachments are not counted as
independent bolt purchases. Each displayed stack includes shaft, head, nut and
two washers. Products, shank/thread windows and washer strength are unselected.

Eight joints have opposing angles: three principal/header feet, four
header/kicker-post joints and the common center/top joint. Fourteen beam ends
have one angle and a proposed wood compression/contact return path. This does
**not** qualify the manufacturer's bidirectional lateral pair rule. These
single-angle ends need their own complete joint evidence. No unlisted
transverse or moment capacity is supplied anywhere.

| Proposed receiver | Actual planning section and change |
|---|---|
| Two outer rims | Solid 4×6, 88.9 mm across X and 139.7 mm into the board; changed foot/top stations |
| Common center | Solid 6×8 envelope, 190.5 mm across X × 139.7 mm inward; replaces two thin principals |
| Two bottom rails | Solid 6×6 envelope, 139.7 mm along slope × 139.7 mm inward |
| Four service rails and top rail | Solid 4×6 envelope, 88.9 mm along slope × 139.7 mm inward |
| Header | Shaped solid 6×10 stock envelope; 139.7 mm depth; proposed length 2,638.425 mm |
| Four kicker posts | 4×6 envelopes; outer posts shift 19.05 mm outboard and have lower side relief beside the retained runners |
| Kicker seam backer | One 4×4 envelope with a 66 mm top neck and two conditional 5/16-inch through ties |

The service rails move **26.55 mm downslope** at the lower row and **26.9 mm
upslope** at the upper row. This provides 57.8 mm between their facing ends,
clearing the bolt tails and nuts that crossed in v4. The header extends
19.05 mm at each end beyond v3 so both outer kicker angles have full nominal
flange seats. The resulting header projects beyond the retained leg envelope;
this changed rear envelope is proposed, not an inherited room-fit pass.

All panel/kicker outlines, hold/T-nut datums and LED endpoints remain at the
reviewed kerf-right geometry, including G2's existing +5 mm X move. Mounting
holes were reported undrilled by the owner; no inspection or drilling is
claimed. The purchased **66 Hillman 42605 screws** remain, with nominal 63.5 mm
length and owner-measured 9 mm head diameter. Head height remains an unmeasured
3 mm occupancy assumption.

The candidate proposes **eight additional mounting-axis moves**:

- Four upper kicker rim/center screws move from Z192 to Z173.05 mm, clearing
  HL35 post bolts at Z188.1. Their reviewed X coordinates remain.
- Four upper main-panel rim/center screws at the `..._4` stations move
  19.05 mm upslope, clearing the top post shafts. Their X coordinates remain.

Every old and new coordinate is recorded in the assessment. These changes
leave the reviewed wood model untouched and do not authorize physical moves.
The twelve starting bolt lines remain; four front stacks increase from
76.2 to **107.95 mm** grip. Their nominal products and delivered thread windows
must be rechecked. Unchanged lines do not inherit the old joint's resistance.

Three wire proposals retain their LED endpoints: `wire_048_D1_E1`,
`wire_066_F7_F6` and `wire_072_F1_G1`. The nominal shallow doglegs are each
approximately **203.77 mm**, within the recorded approximate 304.8 mm segment
budget. Unused cable slack, connector feeding and actual harness routing are
unmodeled. The final F1–G1 dogleg runs 16 mm below its LED endpoints along the
slope to clear the center-foot angle.

## Bounded checks and results

| Check | Final nominal result |
|---|---:|
| Source block duties mapped | 24 / 24, to 22 new joints |
| Full 88.9 mm receiving-wood probes at flange holes | 120 / 120 |
| Nominal rectangular flange seats supported after service voids | 60 / 60 |
| Angle/angle and angle/timber/panel intersections | 0 |
| Complete planning metal pair intersections | 0 |
| Nonshaft planning metal/timber intersections | 0 |
| Planning metal/purchased screw-shaft intersections | 0 |
| Screw axes with a receiving timber | 66 / 66 |
| Native service bodies authenticated | 405: 132 lights, 131 wires, 142 T-nuts |
| Service-body/timber and service-body/metal intersections | 0 |
| Receiving members disconnected by proposed voids | 0 / 16 |

These are native CadQuery solid intersections with bounding boxes used only
to skip disjoint pairs. The 88.9 mm probes and nominal flange skins are checked
on receiving wood **after service subtraction but before the intentional bolt
holes**. A hole in its own bolt line must not be misreported as absent stock.
Actual line/surface intersections determine local bolt grips at the shaped
header; an entire-member projected thickness would place washers above the
real surface. Header exit washer seats are conditional 38.1 mm spotfaces.
Auxiliary tie washers use a 31.75 mm OD planning envelope instead of the
overlapping 38.1 mm v4 envelopes.

Bolt/screw poses remain exactly those of the authenticated v5 negative metal
checks. Later service subtraction cannot create new solid timber interference;
the final service bodies and angle seats are checked again. The v6 clash and
its lost center-foot bearing are preserved, rather than replaced with a pass.

The **5 mm ideal HL35 steel envelope**, provisional flange-hole offset of
50.8 mm, occupied bores, round circumscribed head/nut allowances and display
quantization are explicit assumptions. The current factory geometry, actual
steel gauge, bend radius, coating, delivered products and tolerance stack are
unverified. This is a conditional nominal-fit result, not physical hardware
qualification. Exact current catalog and factory drawings remain needed before
capacity comparison; see the [catalog basis](../README.md#catalog-basis-and-limits).

## Engineering disposition and transport implication

The manufacturer's listed uplift/F1 directions do not supply an arbitrary
six-component joint resistance. The single-angle ends have no qualified
bidirectional lateral resistance. Complete joint compression/contact, transverse
force, moments, bolt groups, loaded wood edges, splitting, net sections,
washers, hardware threads and tools remain **unqualified**. Local bolt diameter
and minimum stock thickness are not substitutes for those checks.

The additional planning bores, spotfaces and service voids remove roughly
0.4–2.7% of the evaluated receiver-profile volumes. Remaining volume is
not a strength calculation. The swept clearance envelopes are not a demonstrated
machining method: some passages are curved/enclosed. A practical cut/feed/removal
plan must be established and its real section effects checked before machining.

At a declared **500 kg/m³ timber-density sensitivity**, the sixteen finished
receiving members total approximately **155.3 kg / 342.4 lb**. The common center
is about **68.6 lb** and the shaped header about **62.2 lb**. Retained legs and
runners, plywood, holds, T-nuts, screws, bolts, HL35s and electrical hardware
are excluded. This is not total wall mass, delivered density or measured
transport weight. The heavier stock is a significant compromise for the owner's
individual-member disassembly goal. A member inventory with actual material
and hardware selection must precede any complete mass/cost claim.

The original **250 lb climber / 2× downward / 300 N horizontal / 100 mm hold
lever** basis remains. No new frame reactions, joint force fields, timber
resistance or own-weight reactions were solved. The preserved panel head and
rolling-shear concerns are not resolved by exchanging structural connectors.
The no-slip floor assumption is still unverified. No native solve was ready
or run, and no fabrication, structural or climbing release exists.

Next work is to establish the complete joint architecture and real product
geometry, settle a practical service/assembly method, then compute candidate-
specific forces including dead weight and assess every changed joint, member
and panel path. If those gates fail, revise the layout or connector mix; do
not enlarge a catalog rating or transfer an old model pass.

## Evidence, checks and retention

The [assessment](fit-assessment.json) records every station, hole, screw move,
stack, service authentication, proposed route and remaining material volume.
The [manifest](manifest.json) binds the frozen parents, reproduction helpers,
preceding failed input and exact scene/report bytes. The source-bound delta
contains **10,716,636 bytes**, dominated by the new receiving-stock bores and
service surfaces. Unchanged baseline meshes remain shared; repeated steel and
hardware use template instances.

```bash
.venv/bin/python -m scripts.hl35_candidate_finalize
MPLCONFIGDIR=/tmp/mini-moonboard-matplotlib .venv/bin/python -m scripts.render_hl35_candidate --scene site/hl35-final-scene.json --out docs/wood-joints-mvp/hypotheses/hl35-candidate/final-fit-v7/overview.png
.venv/bin/pytest -q tests/test_hl35_candidate.py tests/test_export_wood_joint_design_review_scene.py
node scripts/check_hl35_scene.mjs /PATH/TO/three.module.js
```

Known-answer controls cover ideal angle volume, true solid rather than
projection overlap, incomplete receiving thickness, opposed-axis deduplication,
local line intersections through a wedge and washer overlap from the circular
lens formula. The actual Three.js adapter check loads the source-bound scenes,
counts all 112 stacks/66 screws/405 services, and rejects release flags,
corrupt bindings, duplicate roles and geometry-distorting transforms.

Two frozen failed-method helpers retain harmless lint-only unused bindings/import
ordering. A narrowly scoped `ruff.toml` exemption preserves those hashed bytes
and the source-pinned `pyproject.toml`; active successor helpers remain linted.
The maintained development summary/ledger record final check outcomes.

Closed: this v7 input and its failed supplemental coverage check. Active: the v8 proposal and remaining engineering gates.
Closed v1–v6 evidence is recoverable and must not be repeated at unchanged
inputs. Their source-bound helpers remain dependencies; historical viewer
choices and original authorities stay intact. Closed bulky scenes may be
externally archived later using the repository's verified archive/prune process,
after checking consumers and ownership. No source, raw run or another agent's
file was pruned, and no commit/push occurred in this overnight task.
