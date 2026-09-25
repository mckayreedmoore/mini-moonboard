# WJ24 development packet index

Status: coordinated development index, updated 2026-09-24. This index organizes the
current WJ24 work into a future reviewable shop packet. It is not a cut list,
drill schedule, assembly procedure, fabrication release, structural acceptance,
or climbing release.

> **Superseded geometry:** The 28-piece, 104-axis composition summarized below
> predates the latest owner-directed viewer revision. The current model has 24
> blocks in seven designs and 92 candidate bolt axes; see the [consolidation
> checkpoint](hypotheses/consolidated-blocks-two-inner-bolts-2026-09-24/README.md). This index
> remains a historical development record, and its detailed counts do not bind
> the current scene.

The machine authority remains
[`wood-joints-candidate.json`](../../wood-joints-candidate.json), which names
`compact-floor-flush-wood-joints-development` as a separate, unreleased
development candidate. It does not replace
[`current-candidate.json`](../../current-candidate.json), the selected
`compact-floor-flush-development` angle-frame authority. Do not transfer its
shop instructions, hardware selections, or evidence to this lane.

## WJ24 scope and counted quantities

WJ24 is the current complete static composition for this lane. It maps all 24
former angle duties to replacement paths and removes their 144 structural SDS
axes from the proposed candidate. The full composition contains sixteen rebuilt
hosts, twenty-eight proposed connector pieces, and 104 proposed structural
bolt axes. It retains the 66 fixed Hillman 42605 panel/kicker screw axes, the
twelve starting frame-bolt arrangements, the kerf-right climbing surface,
panel outlines, hold grid and kicker. Four fixed panel-screw receiver paths
redirect through two modeled backers. These counts describe the model; they do
not accept a connection or authorize shop work. The composition has zero
accepted replacements.

| Quantity | Current basis | Boundary |
| --- | --- | --- |
| 24 duties | All former angle duties have a WJ24 replacement path in the static composition. | Path mapping is not load-path or resistance acceptance. |
| 28 pieces | Modeled connector/backer blanks in the source-bound WJ24 inventory. | Blank shapes and listed model operations are not approved cuts. |
| 104 bolt axes | Proposed new structural bolt stacks in WJ24. | A complete catalog product and delivered-length schedule has not been selected for all axes. |
| 104 nuts and 216 physical washer equivalents | Reconciled with the 104 proposed bolts by the hardware inventory. | Together, 424 proposed individual hardware items; integral bolt heads are not counted separately. |
| 520 CAD hardware roles | Scene/geometry roles associated with installed hardware. | Not a physical purchase quantity; some roles describe portions of one part, and four backer washer roles each represent three physical washers. |
| 12 frame-bolt arrangements | Starting arrangements retained in the integrated composition. | They still need candidate-specific recheck where affected by changed geometry. |
| 66 panel/kicker screws | Fixed purchased Hillman 42605 policy and axes retained. | Separate from structural bolt counts and subject to the existing panel-screw product policy. |
| 144 former SDS axes | Removed from proposed structural duties. | Not WJ24 BOM items; selected-baseline SDS hardware is unaffected. |

## Controlling records

The machine authority identifies the candidate lane. The WJ24 composition and
its matching diagnostic identify the current modeled revision. Downstream
hardware, stock, transport, cost and mechanics records must bind to that same
composition and its source fingerprints. A change to the composition makes
those dependent records stale until reviewed against the revised model.

| Packet subject | Controlling record | Current use and limit |
| --- | --- | --- |
| Candidate identity and gates | [`wood-joints-candidate.json`](../../wood-joints-candidate.json), [`next-mvp-plan.md`](next-mvp-plan.md), [`completion-ledger.md`](completion-ledger.md) | Candidate status is `development_partial_diagnostic_unreleased`; every release flag is false. WJ24 is a diagnostic development revision. MVP-L, mechanics, fresh cases, MVP-E, and physical observation gates remain open. |
| Integrated geometry | [`WJ24 composition`](hypotheses/wj24-integrated-static/composition.json), [`full-scene diagnostic`](hypotheses/wj24-integrated-static/diagnostic.json), [`parent audit`](hypotheses/wj24-integrated-static/parent-audit.json), [`composition report`](hypotheses/wj24-integrated-static/README.md) | Current model of the 24-duty layout. Eighteen implemented static/source checks pass, while the layout remains `REVISE`; this is not joint, tool-access, capacity, or release acceptance. |
| Source members, duties, and fixed axes | [`source-inventory.json`](source-inventory.json) and the WJ24 composition's source bindings | Source anatomy and candidate invariants, including the 66 fixed screw axes and twelve starting frame-bolt arrangements. Not a fabrication schedule. |
| Fixed panel/kicker screw receivers | [`WJ24 fixed-screw receiver audit`](wj24-fixed-screw-receiver-audit.md) | Reconciles all 66 fixed axes: 48 panel and 18 kicker; 62 retain source receivers and four center-kicker axes redirect to the two backers. Nominal material and purchase-cut geometry pass, but support/embedment is unevaluated and receiver-to-frame completion remains false for all 66. Not a screw drill sheet or capacity check. |
| Proposed blanks and hardware counts | [`WJ24 hardware inventory`](hypotheses/wj24-hardware-inventory/README.md) and [`inventory.json`](hypotheses/wj24-hardware-inventory/inventory.json) | Source-bound modeled connector blanks, receiver groups, axes, and physical-piece reconciliation. The inventory says stock is unobserved, prices are null, and SKUs are not selected for groups. |
| Bolt-length development | [`WJ24 center-axis bolt-length screen`](wj24-bolt-length-screen.md) and [`WJ24 hardware inventory`](hypotheses/wj24-hardware-inventory/README.md) | The 16 center axes now have conditional nominal candidates: 4 × 4.75 in, 8 × 5.75 in, and 4 × 7.5 in. The dimensional screen does not select a SKU, supplier, or final stack; delivered body/thread measurements and receiving checks remain conditions. |
| Timber source and yield | [`WJ24 timber stock/yield note`](wj24-timber-stock-yield.md) | Whole-stock and blank-yield planning for the 28 modeled pieces. Scenarios remain planning inputs until actual source stock, grade, dimensions, tool setup and cost are bound. |
| Assembly and transport | [`WJ24 assembly/transport sequence`](wj24-assembly-transport-sequence.md) | WJ24 operation dependencies and unresolved support, tools, service motion and reverse-removal work. Sequence analysis is not an approved shop procedure. |
| Cost | [`WJ24 development cost screen`](wj24-development-costs.md) | Preliminary quantity-based estimate only. Bolt Depot pages were checked 2026-09-24; prices match the repository's 2026-09-23 snapshot, and stock/shipping/tax remain unconfirmed. Its partial by-each subtotal is $71.72 for 84 nominal 6-in/8-in comparison bolts plus all 104 nuts and 216 washers; a $63.96 mixed bag/loose illustration depends on stated pack assumptions. Twenty bolt costs and all 28 stock-blank costs remain open. No product is selected or accepted. |
| Local viewer | [`WJ24 viewer review`](wj24-viewer-review.md), [`final evidence archive`](hypotheses/wj24-viewer-review/README.md), [`archive manifest`](hypotheses/wj24-viewer-review/manifest.json), and [`viewer source`](../../site/wood-joints-wj24-viewer.html) | The compact scene payload is 9,181,070 bytes and the browser review was completed locally. Nothing was published; a screen-reader check remains pending. |
| Criteria and mechanics | [`criteria.json`](criteria.json), [`criteria-method-map.md`](criteria-method-map.md), [`WJ24 mechanics coverage audit`](wj24-mechanics-coverage-audit.md), and the [`center backer load-path contract`](wj24-backer-loadpath-contract.md) | The 36 frozen legacy safety questions and 11 additional candidate obligations remain pending. The backer contract specifies missing WJ24 actions, shared center load paths, resistance and stiffness evidence. Neither record is an accepted mechanics result or fresh six-case solution. |
| Representative physical-steel mesh | [`representative hardware mesh report`](hypotheses/wj04-hardware-patch-mesh/README.md) | The representative WJ04 profile has 32 metal bodies and 62,193 C3D10 elements. An independent 14-point audit recomputed 870,702 positive integration-point Jacobians. No response was run; this mesh does not represent WJ24 or establish WJ24 mechanics. |
| Current WJ24 representative STEP | [`WJ16/WJ24 geometry comparison`](hypotheses/wj24-patch-reconciliation/README.md) and [`source-bound five-body STEP reconciliation`](../../fea/results/diagnostics/wj24-baseline-patch-geometry-v1/reconciliation.json) | Five representative finished solids were exported from current WJ24 geometry. The old WJ16 mesh does not match the changed principal; no WJ24 mesh or response exists yet. |

Historical WJ03, WJ04, WJ16, WJ18 and earlier WJ24 reports can explain how
the current model was developed. They do not supply WJ24 acceptance. In
particular, the selected angle-frame six-case result, barrel candidate
materials, a narrow WJ04 trial, a static pass, or solver convergence cannot
stand in for complete WJ24 joint evidence.

## Open findings that control packet completion

The [WJ24 static report](hypotheses/wj24-integrated-static/diagnostic.json)
still records geometry and access findings that need a named disposition
before this model can serve as the basis for a shop packet:

- The left bottom-center rail face is reduced by the existing service passage;
  the common face measures 10,385.137652 mm² and the contact-slab material
  fraction is 0.984095945. A finite face does not establish bearing adequacy
  or a complete contact model. The [contact supplement](hypotheses/bottom-center-contact-and-hold/README.md)
  attributes the reduction to the E1–E2 passage and preserves its measured area.
- Provisional rear hold-bolt envelopes overlap the bottom-center right cleat at
  G1 by 745.512902 mm³ and the top-center right cleat at G12 by 562.789151 mm³.
  These are access proxies, not selected hold lengths.
- The G7 LED withdrawal sweep intersects the lower full-stock cleat by
  319.657955 mm³ over its modeled 19.25625 mm operation. This does not resolve
  harness feeding, wire support/slack, panel motion, or a different staged
  operation. The separate harness record has twelve cross-panel wires and no
  demonstrated whole-panel disconnect or reverse-feed route. See the
  [LED extraction report](hypotheses/wj24-led-extraction/README.md) and
  [transport sequence](wj24-assembly-transport-sequence.md).
- A durable access-relief attempt 03 now exists, and its canonical README is
  being updated. This index records no outcome from that attempt; the baseline
  G1/G12/G7 findings remain open pending the report and review.
- Local tool, counterhold, timber, contact, tolerance and service findings in
  the integrated diagnostic remain open. Positive nominal clearance and an
  empty intersection report do not establish installation or removal access.
- Candidate-specific rechecks remain for the twelve retained frame-bolt
  arrangements and the complete center-backers-to-header load paths.
- The fixed-receiver audit finds that all 66 candidate axes have receiver
  material and nominal purchase-cut geometry, while support/embedment is not
  evaluated and all 66 receiver-to-frame paths remain incomplete. Its six
  sampled inner-kicker-edge points sit only 0.5 mm from the backer's X edge and
  0.1 mm from its Y edge, so continuous support and tolerance remain open.

The inventory groups bolt axes by modeled grip; the separate center-axis screen
adds conditional nominal lengths for its 16 previously unassigned axes. Neither
selects a bolt family or supplier SKU, and delivered body/thread measurements,
the full stack, tolerance, nut seating and wrench access remain unresolved.
The cost screen prices only part of the comparison: $71.72 at each prices or
$63.96 under its mixed bag/loose assumptions; 20 bolt costs and all 28
stock-blank costs remain open. The bounded stock-yield note is planning only;
delivered stock, grade, availability and price remain unverified.

The compact WJ24 viewer payload is 9,181,070 bytes. Its browser review is
complete on a local server; it has not been published, and a screen-reader
check remains pending. A representative WJ04 physical-steel mesh has 32 bodies
and 62,193 C3D10 elements, with 870,702 independently recomputed positive
14-point Jacobians; this is mesh preparation only, with no response. Five
representative current-WJ24 finished solids have now been exported to STEP, but
there is no WJ24 mesh or response yet. No fresh candidate six-case mechanics
bundle or completed WJ-08 criteria contract exists at this checkpoint. Do not
close a criterion by leaving its result empty or treating missing
demand/capacity as zero.

## Work needed before a shop-ready packet can be issued

1. Resolve each WJ24 geometry, contact, service and access finding against one
   reviewed composition revision. Freeze its part IDs, source hashes, datums,
   cuts, axes, interface graph and affected frame-bolt arrangements.
2. Bind every proposed connector blank to deliverable stock and a documented
   grade/section basis. Complete whole-stock yield and cost, then prepare
   separate marked cut sheets for each finished part with grain direction,
   part-local datum, dimensions, tolerances, saw/tool setup, and cut order.
3. Select source-backed bolt, nut and washer products for every axis. Reconcile
   delivered lengths and thread positions against the actual grip, seats,
   washer thickness, nut engagement and access requirements. State actual
   drilling tools and finished opening dimensions only after the final geometry
   and source evidence support them.
4. Close the integrated forward and reverse operation sequences, including
   real tool approach/stroke, temporary support, independent member transport,
   panel/kicker staging and the complete LED/wire service path. Count screw
   operations separately from structural bolt stacks.
5. Complete the frozen WJ-08 mechanics and criterion contract for every
   applicable physical interface, including contact/opening, bolt actions,
   wood/connector/washer resistance, stiffness, finished sections, frame
   response and all adopted checks. Run and authenticate the fresh six required
   cases serially after those inputs are ready; resolve and rerun affected
   failures.
6. Generate the final purchase list, shop sheets, assembly and inspection
   records from that same frozen candidate. Obtain the independent review
   required by WJ-10 and correct any confirmed finding before describing the
   packet as complete.

No geometric occupancy diameter, modeled axis length, bounding-box extremum,
or model-only machining operation is a drill bit, purchased bolt length, cut
dimension, tolerance, or shop instruction. The selected-baseline construction
folder and angle-frame checklist remain separate. A later WJ24 packet must
carry its own dated, fingerprinted drawings and product-backed tool schedule.

Any future Actual and Disposition columns belong to observations of delivered
material and physical work. Leave them blank until the relevant stock,
hardware, cuts, holes or assembly are physically observed; modeled values do
not fill them.
