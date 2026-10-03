# Conditional knee-bridge working package

The [producer](knee-bridge-working-package.py) joins the fresh frame, local
actions and existing conditional shop recipe. The parent completed
`rawlocal/knee-bridge-working-package/attempt02` with status
`CONDITIONAL_WORKING_PACKET_BOUND`: **390 source pins and five outputs**.
This is the four-bolt proposal for the wood-joint development lane; the
reviewed 104-axis authority remains unchanged.

## One proposal and one load envelope

The proposal retains **50 bodies / 44 timber blanks / 24 blocks**, the
climbing surface, panel outlines and 66 purchased Hillman panel/kicker screws.
Only the two outer knee spines receive two additional transverse axes each,
at local grain stations 100 and 250 mm. Their modified six-bore STEP solids,
eight washer lands and axis aliases are bound by the existing
[geometry and integration recipe](knee-bridge-integration.md).

The proposed inventory is **108 bolts, 108 nuts, 216 washers and 66 Hillman
screws**. Four new bolts use the conditional 6.5-inch partial-thread Grade 5
recipe; the 8-inch length is a fit bound. No member is added or enlarged.
The [proposal drawing](knee-bridge-proposal.svg) shows the stations and faces.

Loads remain **250 lb × 2 downward, signed 300 N horizontal, original
100 mm hold lever**, recorded gravity and the proportional 25 kg equipment
allowance. Planning mass is **225.197914143181 kg**, including the net
**+0.247958829061 kg** hardware/wood delta. No hold-depth or climber-weight
variant is selected.

## Evidence joined by the package

| Scope | Current source |
| --- | --- |
| Six zero and six nominal frame states | [Fresh gravity/frame](knee-bridge-frame.md) |
| All existing bolt/screw actions | [Fresh demand census](knee-bridge-response.md) |
| Four outer corner transfers and references | [Transfers](knee-bridge-corner-replay.md), [references](knee-bridge-corner-references.md) |
| Four new bolts in two internal pairs | [Two-spine static replay](knee-bridge-joint-replay.md) |
| Other 84 existing axes | [504 lateral-reference states](knee-bridge-other-bolts.md) |
| 42 unchanged timber bodies | [Fresh member references](knee-bridge-members.md) |
| Physical top rail placement | [144 current pressure traces](knee-bridge-top-rail.md) |
| Header and remaining block openings | [4,344 finite limits](knee-bridge-remaining-sections.md) |
| Four existing continuous knee shafts | [Fresh shaft replay and placement export](knee-bridge-continuous-shafts.md) |
| Geometry and hardware fit | [Modified solids](knee-bridge-geometry.md), [saved-scene fit](../assembly-package/knee-bridge-fit.md) |
| Counts, purchase terms and handling | [Order](../assembly-package/knee-bridge-order.md), [shop delta](../assembly-package/knee-bridge-shop.md) |

The parent supplies exact completed receipt hashes. The producer authenticates
consumed source closures and receipt artifacts, retains 50 effective STEP
bindings and joins **648 unique bolt/case records plus 396 screw/case records**.
Corner local allocations remain separate from their fresh global boundary
records. Internal bridge pairs carry no global receiver-interface row. Old
register force authority and record indices are replaced with the current
force records; historical geometry remains referenced with its original scope.

All 24 fresh continuous-shaft states close independent receiver equilibrium.
The placement continuation reused those immutable results, made **zero new
mechanics calls** and found all **96 straight-shaft placements / 96 interface
fits**. Its smooth-steel diagnostic peaks at **192.369 MPa / 0.303269** under
the existing 92 ksi hypothesis. Isolated placements do not establish common
knee-group or full frame displacement compatibility.

All fresh bridge tensions are below the existing 1060.656605 N concentric
M=0 washer envelope. Positive scaling applies only to that fixed geometry,
linear-elastic plate, zero-gap/no-preload contact model. Its conservative
stress index remains 0.697914. No new washer solve is required by that envelope.

## Conditional model and remaining qualification

The frame retains **filled-bore gross compliance**, declared finite contact
laws and the no-slip floor assumption. Local joint replays use rigid timber,
first-order geometry and partial-thread smooth-bearing envelopes. Their finite
force redistribution preserves complete
interface wrenches and does not feed displacement changes back into the frame.
The two bridge pairs are static axial-transfer witnesses; their actual elastic
compatibility and changed-hole stiffness are unqualified.

The fresh Hillman nominal head demand remains **1871.246 N**, above the
declared favorable generic head references **930.222–984.128 N**. This is an
exception of the analytical reference comparison; no measured product failure
or climber rating is established. Actual screw properties, plywood/contact
sharing and complete resistance remain unverified; see the
[head-reference worksheet](head-reference-basis.md).

Existing duration, nominal ligament sharing, hardware, group/splitting and
installation limits remain explicit. Permanent-load evidence retains its
original frame scope. Delivered thread profiles, actual tool operation, wood,
floor and build observations remain unrecorded. The shop Actual/Disposition
cells stay blank.

**No physical candidate is selected by this package. All 47 formal criteria
remain pending; all eight release flags remain false.** The package supplies
conditional planning records, with no drilling, fabrication or climbing release.
Historical runs, source packets, foreign workspace changes and temporary
evidence remain preserved. No software tests or agent review loop are required
or claimed by this binding operation.

## Reproduction and saved artifacts

The parent ran the producer's `build(output, knee_receipt, knee_sha256,
worksheets)` API with the exact completed receipts shown in the command
below. It only authenticates and joins saved data. Use a fresh output child;
the completed child is `attempt02`.

```bash
task_packet=docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/upper-corner-screw-layout
.venv/bin/python -B "$task_packet/knee-bridge-working-package.py" \
  --output "$task_packet/rawlocal/knee-bridge-working-package/fresh-replay" \
  --knee-receipt "$task_packet/rawlocal/knee-bridge-joint-replay/attempt01/receipt.json" \
  --knee-sha256 10503afef20c8fc69c0f5b4877f8deb2794646c258b05ca63616611443c6c22b \
  --worksheet "$task_packet/rawlocal/knee-bridge-other-bolts/attempt01/receipt.json" ee67b7e042a8fcf88d1c37eaaaaac8aebcb815e2cf73b8f1a22a61f44283da83 \
  --worksheet "$task_packet/rawlocal/knee-bridge-members/attempt01/receipt.json" fa4d5f5568d53c0e4e62a74d31a814738b39a78951a4c27ae6e4c141ef5be794 \
  --worksheet "$task_packet/rawlocal/knee-bridge-top-rail/attempt02/receipt.json" 80ed0f8af4dee1e9cf4d006728a33fdb049c97b3bc0d4ccb904610e7b6b679a1 \
  --worksheet "$task_packet/rawlocal/knee-bridge-corner-references/attempt01/receipt.json" fcd986b018bb121df464292449cedcb23f1c069bd5ec611dd49b654c6d840288 \
  --worksheet "$task_packet/rawlocal/knee-bridge-remaining-sections/attempt01/receipt.json" e1796242c3ede025927db911af73b69d226ddd7b7e03aa621f77a548a4f322d0 \
  --worksheet "$task_packet/rawlocal/knee-bridge-continuous-shafts/attempt02/receipt.json" 5496190db02ec1ed8fca6ced59f7538526503ab6735f946e651394ab225d1ffa
```

| Artifact in `rawlocal/knee-bridge-working-package/attempt02` | SHA-256 |
| --- | --- |
| `manifest.json` | `4c0d10a86a6018813b5f8efcd7f438662037e458ef3f2ce535d1e0860ca25bd0` |
| `receipt.json` | `5fa8cc849e4a2fa042a1cffa6d2957d4163597c7999dbcef1f57563dfdd83e7b` |
| `bolt-actions.jsonl` | `eb58325b404def753db6c7edf9d2675a13841e040c5bc152ce9d59789e260cea` |
| `panel-actions.jsonl` | `180fd06af021ea79fea9d694a7e4e8ecc13c6753bb6bf56e87df6a622847c3fb` |

The first binding attempt stopped before publication because an effective
STEP reference uses `path`, while the producer initially requested `source`.
Its source snapshot and metadata STOP remain in `attempt01`. Correcting that
field caused no mechanics, CAD, native, frame or washer rerun. Final source,
artifact, inventory and link authentication and targeted Ruff passed; no
software tests or agent review loop ran.

The proposal packet and reviewed 104-axis packet remain active references
with separate authority. Older force variants and failed attempts remain
recoverable history; consumed raw records stay in place. This closure prunes
no source, temporary evidence or other owner's files.
