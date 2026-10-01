# T08 hardware, material, yield and cost closeout

Prepared 2026-09-27 local time for the owner-reviewed candidate
compact-floor-flush-wood-joints-development, revision
led-clearance-2x6-runner-seated-blocks-v1.

## Terminal result

PENDING: source identity, counts, current public price observations and
length-only block sensitivities are reconciled, but T08 is not closed. No
product stack or material source is selected, delivered or accepted; no
current purchase total, cost lower bound, cost range or fastener weight is
supported. The local verifier returns
PASS_SOURCE_BOUND_REGISTER_ONLY_WITH_PENDING_PRODUCT_MATERIAL_PRICE_GATES.

This is a documentary closeout only. It makes no capacity, fit, installation,
wood-property, joint-acceptance or construction claim. T07 owns fit and
transport. Panel-property mapping remains outside this attempt. No geometry,
CAD or native solver files were changed.

## Frozen source state

source-pins.json records 35 local files, each checked against its inventoried
SHA-256 before the registers were written. It includes the live selected
authority, the separate candidate and reviewed revision, current attempt04
inventory, current 92/12/66/144 coverage, candidate bolt catalog screen,
retained-frame sources, Hillman purchase policy, timber source/yield and
price/grade attempts, and current thread-boundary, cost and material status
notes. It also records older cost/hardware attempts as excluded history.
Existing attempts were read-only. The older coverage review is explicitly
noted as stale because it reviewed different MD/JSON hashes than the current
coverage files.

The selected authority remains compact-floor-flush-development. This attempt
keeps the wood-joints candidate separate and preserves its reviewed repository
commit and revision identity.

## Hardware identity and quantity

fastener-axis-register.json is the reproducible per-axis bridge:

- 92 candidate structural bolt axes, each with its catalog-lead IDs, modeled
  envelope only, no selected SKU and pending delivered thread/engagement.
- 12 starting frame-bolt axes retained as selected-baseline references and
  requiring a wood-joints-candidate recheck.
- 104 structural stacks total: 104 bolt/nut roles and 208 separate washer
  roles.
- 66 owner-purchased Hillman/Fas-n-Tite 42605 panel/kicker screws, with the
  owner-selected pilot plus countersink policy; 58 axes are unchanged and
  eight were previously owner-directed moves.
- 144 former SDS25112 axes are explicitly listed as removed historical ML24Z
  duties. They contribute zero current quantity or cost.

The Hillman screw remains separate: no SDS25112 or SPAX strength, stiffness,
pilot, resistance, or installation rule is transferred to it. Its receipt
price is unknown.

The public bolt/nut/washer pages establish only the product-listing fields
recorded in material-cost-register.json: listed nominal size, grade/finish
where stated, standard references, catalog thread-length minima and published
washer/nut dimensions where available. These are not delivered-lot
measurements, certificates or capacities. The reviewed catalog and thread
boundary sources do not bound delivered first-full-thread position, last
scratch/runout, usable plain shank, or the active unchamfered engagement
interval of the actual matched nut. No delivered identity or shank/thread
interval is therefore accepted for any of the 92 candidate axes. The 12
retained arrangements are also pending current fit and source verification.
No catalog-unlisted washer support or wood bearing value is inferred.

## Material, yield and cost

material-cost-register.json carries the 24 proposed block blank identities
and lengths: 18 nominal 4x4 blanks, four 4x6-ripped blanks, and two nominal
2x6 blanks. The 4x6 blanks require traceable source-board identity and
post-rip final-section grade disposition. The 20 preserved frame records are
kept for reconciliation, but 16 hosts were rebuilt; those historical source
lengths are not a current frame purchase or cut list.

The 8-foot checks are only length arithmetic with assumed 3.175 mm crosscut
kerf per block blank and 25.4 mm end trim per stick. They yield one-stick
arithmetic scenarios for each of 4x4, 4x6 and 2x6 block stock, with positive
residual lengths. They omit frame cuts, actual delivered dimensions, defects,
section cleanup, handling and receiving loss; they do not establish board
count, usable yield or a purchase plan.

Every material-cost register line has an explicit inclusion status and
exclusion reason. Directly rechecked Bolt Depot display prices are preserved
as conditional comparisons, not candidate estimates: the 1/4-20 Grade 5
bolt examples are $0.45 (4 in), $0.72 (5-1/2 in), and $0.77 (6 in) each.
Those lengths and SKUs are not selected. The low-carbon alternatives,
indexed/aged Grade 5 listings, alternative carton offer, conditional
1/4-20 nuts and washers, and aged K.L. Jack package prices remain separate,
excluded leads. Mutually exclusive options are not added together.

The 12 retained catalog references have a separate displayed by-each
comparison of $31.12 before tax/freight. It is not included in a WJ24 total
and makes no ownership or received-fit claim. The 66 Hillman receipt amount
is unknown. The 144 removed SDS axes are excluded. WRC fencing listings and
seller-labeled Grade A stock are excluded as material mismatches; local
supplier pages without a matching item quote or location inventory do not
support a price. Historical predecessor totals are explicitly excluded.

## Exact blockers and next actions

1. Obtain the exact proposed bolt, matched nut, washer and any spacer item
   identities from the responsible source. For each delivered lot, obtain
   authoritative item/lot documentation or measurements bounding actual
   shank, first full thread, last thread/runout, nut active unchamfered
   interval, dimensions/tolerances, lot grade/finish and weights. Reconcile
   engagement and supported washer footprint before any product stack can be
   qualified. T07 separately completes tool access, install and transport.
2. Obtain a current local lumber quote/availability record tied to exact
   species group, grade, actual section, treatment, condition, stock lengths,
   quantity, delivery and price. Reconcile it with a current 20-frame cut and
   owner-stock disposition, the 24-block blanks, realistic kerf/trim/defect
   yield, and whole-board quantities.
3. Obtain source-board traceability and post-rip grade/section disposition for
   the four 4x6-derived block blanks. Do not transfer the un-ripped source
   grade or design values.
4. Recover the owner receipt or stock-cost record for the already-purchased
   66 Hillman 42605 screws if historical spend is required. Do not substitute
   a current replacement quote for the unknown receipt amount.
5. After those source records exist, refresh source pins and recompute costs,
   package quantities, surplus, delivery/tax and product-specific weight.
   Keep all still-unverified items pending; a displayed web price is not a
   vendor quote or availability commitment.

## Reproduction

From the repository root:

    python3 docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-hardware-material-cost-closeout-attempt01/build_register.py
    python3 docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-hardware-material-cost-closeout-attempt01/verify.py

The build stops if any pinned source hash has changed. The verifier
recomputes every pinned source hash, checks axis and stock arithmetic,
checks all cost-line inclusion flags and the retained-reference arithmetic,
and writes verification.json. A passing verifier certifies internal
source/register consistency only, not product, material, fit or engineering
acceptance.
