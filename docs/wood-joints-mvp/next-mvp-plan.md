# Wood-joint candidate: next plan to MVP-E

Status: execution plan, 2026-09-23. This plan continues the
[`compact-floor-flush-wood-joints-development`](../../wood-joints-candidate.json)
lane from its recorded WJ-03 partial result. The endpoint is **MVP-E**, a
conditional engineering-development and shop-document package under stated
loads, materials, hardware, and floor assumptions. It is not an inspected
build or an unconditional climbing rating. WJ-11 physical receiving and
prototype observations belong to the later MVP-P record.

## Plan-authoring baseline and non-transfer rules

The [completion ledger](completion-ledger.md) records WJ-00 through WJ-02
complete. This plan's initial WJ-03 snapshot recorded four panel-on nut-removal
paths per side blocked, a 1.0 mm minimum nominal tool gap, and a
`revise_named_constraint` result. A later pre-integration geometry snapshot
raised the post-nut tool gap to 19.0 mm and showed nominal detached-hardware
clearance with the kicker removed. Both reports are historical diagnostics;
neither is the current integrated WJ-03 sequence report or an acceptance.
The connector body's last recorded ordinary-envelope excess was 86.018477 mm.
Its 175.948756 mm excess was temporary bolt-stroke workspace, not permanent
depth. See [outer-node result](outer-node-result.md) for the snapshot boundary.

Keep the kerf-right climbing surface, panel outlines, hold grid, kicker,
all 66 purchased panel/kicker screw axes, and panel-screw policy fixed in this
lane. Map all 24 former angle duties and 144 structural SDS axes to complete
replacement paths; recheck the twelve starting frame-bolt arrangements.
Keep ordinary local-N limits and any named exceptions explicit. No primary
member housing is a default; any proposed house needs its own cut and joint
evidence. Preserve individual-member transport and the no-slip floor
assumption without claiming an anchor or extra floor contact.

The selected angle-frame authority in [`current-candidate.json`](../../current-candidate.json)
and the preserved barrel work do not supply new-joint capacities or case passes.
Do not change selected authority to make this development lane appear complete.

## Current diagnostic checkpoint, 2026-09-24

This checkpoint is source and geometry work only. Component tests and nominal
clearance do not close a stage gate.

- **WJ-03:** the current `wj03-sequence-diagnostic.json` includes the WJ-05
  diagnostic backers, shifted posts, bolts, stacks, and four center receiver
  IDs. All 42 nominal screw/tool and withdrawal screens, both 250 mm lower
  panel extractions, and both staged 100 mm kicker extraction/reverse paths
  show no sampled unrelated hits. The earlier pre-helper report at checkpoint
  `0ebf90eb` recorded 35 right-return LED endpoint hits; the current report
  clears them after candidate-only fixed-service-bore machining. The earlier
  mismatch came from the kerf-right panel and its LED bores shifting
  `-KERF_EACH_MM` while electrical parts remained at their fixed source
  datums, with different endpoint sampling on outbound and return. The
  correction is candidate-only; it does not edit the selected baseline or
  source inventory. The left return was already clear. Kicker motion still
  overlaps the lower panel by 1–18 mm when it stays installed, while extraction
  and return pass after the lower panel is staged. No LED disconnection is
  needed or inferred. Both the staged panel at 250 mm and kicker
  at 25 mm have 0 mm nominal gap to base-floor wood. The last body geometry
  report measured 225.718477 mm permanent rear projection, or 86.018477 mm
  beyond the ordinary 139.7 mm reference. These diagnostics do not close a
  gate; retain `revise_named_constraint` pending a dimensioned
  permanent-envelope disposition and support, continuous-motion, and tolerance
  evidence.
- **WJ-04:** the active config is
  `narrow_x95p25_ordinary_bolt_candidate`: a 95.25 × 38.1 × 119.7 mm cleat,
  grain N, K.L. Jack `25C375HCS5Z` rail and `25C600HCS5Z` principal bolt
  candidates, `25CNFH5Z` nuts, and two Type A Wide washers per stack. The
  current probe is config-bound: the cleat has 0.0 mm nominal ordinary-N
  excess, modeled stacks and washer seats clear locally, a generic 50 mm rail
  tool envelope has 0.764 mm gap, and the temporary nut exit exceeds the
  ordinary limit by 21.872532 mm. Conditional end/edge references remain
  unresolved by signed loading. Mechanics now consumes the probe's finite-probe
  rail contact area (11,401.398713 mm²) and lists the canonical 11,401.425 mm²
  bounding rectangle separately (−0.026287 mm² delta); principal values
  reconcile within rounding. The 95.25 mm X width can be cut from a 2×6,
  but ripping changes the stock grade; post-rip regrade evidence or another
  traceable source is required. The current early mechanics report uses six
  historical angle-demand cases without replay; each has four mismatched
  source files, and no fresh candidate demand/capacity is established. The
  current tool-access report remains `diagnostic_overlap_present`. Its
  corrected placement centers the modeled 3.0 mm wrench slab within the target
  head/nut axial thickness. In the broad 22 mm envelope and two synthetic
  headings, head counterhold clears at both upright stacks and overlaps at
  both rails; the paired-wrench envelope clears at all four. Nut stroke/reindex
  and the full-turn wrench-plus-axial nut-removal bound overlap at all four.
  Separate loose-nut and nut-washer translation sweeps clear at the uprights
  but overlap at the rails. Bolt withdrawal clears at all four, and head-washer
  removal overlaps at the rails but clears at the uprights. These bounds
  establish neither actual access nor impossibility;
  actual jaw fit, handle sweep, and placement remain unverified. The principal
  bolts have 19.05 mm T-edge distance versus a
  conditional 25.4 mm perpendicular-grain loaded-edge 4D reference. Signed
  demands remain unresolved; this is not a universal failure claim, but the
  narrow trial cannot satisfy that criterion if a nonzero ±T lateral component
  governs. The 100 × 53.34 mm pose remains an unbound
  alternative; it has no matching stock, bolt, tool, or mechanics bundle. The
  cataloged FACOM wrench pair is a tool candidate, not proof of installed
  access or working sweep.
- **WJ-05:** fresh transfer and receiver reports remain diagnostic. They keep
  all 66 axes fixed, route 62 into frame timber and four into two separate
  backers, and report 2.959434 mm seated and 1.661248 mm full-sweep nominal
  wire clearance at the repaired right upper socket station. The receiver
  audit remains `blocked_center_receiver_path`: four center structural duties
  and both backer/header attachments lack accepted load paths. The socket
  model omits internal 12-point fit, ratchet/extension space, tolerances, and
  actual access.
- **WJ-06:** the active duty registry still maps 24 duties and 144 former SDS
  axes, preserves 66 Hillman axes and twelve frame-bolt obligations, records
  geometry for 5/24 duties, and accepts zero replacements. Its residual-probe
  entry still has 540 potential generic corridors, none materialized there,
  and replacement complete-stack evidence remains zero. Separate commit
  `b69ca5fa` now materializes installed-state geometry for two far-end right
  rail pairs; right four-duty integration is in progress. This hypothesis does
  not change registry counts or acceptance. Verify complete interfaces and
  stacks before updating any acceptance count.

### Isolated installed-fit hypotheses, 2026-09-24

These follow-up screens do not change the active
`narrow_x95p25_ordinary_bolt_candidate`, selected source pins, or deployed
viewer. None is integrated, promoted, or accepted.

- **WJ-03 compact outer bevel** (`c99751db`,
  [archived probe](hypotheses/wj03-compact-outer-probe.md)) trims the connector
  rear bevel to N = 137.7 mm, leaving 2 mm nominal reserve to the ordinary
  envelope. Installed hardware, timber, and protected-geometry screens clear.
  Its separate [compact access archive](hypotheses/wj03-compact-outer-access.md)
  reports six body-removal translations, 40 shaft/head checks across 20 bolt
  stations, 42 panel-screw tool/withdrawal proxies, and lower-panel-first
  kicker extraction/return clear in sampled geometry. The [outer tool
  archive](hypotheses/wj03-compact-outer-tools.md) reports all 40 coaxial
  socket approaches clear, four socket-plus-nut exits overlapping under-header
  links, two nut-washer slides hitting base rails, and no tool proxy below the
  analytical z = 0 plane. Its broad FACOM full-turn envelope overlaps all 20
  stacks; the report proposes turning/withdrawing the bolt from the head side
  while holding the nut stationary, then removing the nut and washer. These
  operation screens do not establish actual tool fit, continuous motion,
  physical floor clearance, or acceptance; this hypothesis is not integrated.
  A separate outer head-withdrawal study is in progress; no result is available.
- **WJ-04 upper G7 crosscut** (`5555c646`, [archived probe](hypotheses/wj04-upper-g7-crosscut.md)) crosscuts the upper cleat and reverses its upper-rail bolt stack. Bodies, stacks, and all 16 washer seats clear, but all four rail-bolt insertion paths are blocked with neighboring parts retained. The duty-registry workstream is planning rail-plus-cleat subassemblies outside the frame.
- **WJ-04 local +N access** ([refined sampled screen](hypotheses/wj04-pair-access-local-n.md)) tests lower and upper right rail/cleat moves with far-end duties retained. Each move has eight distinct obstacle pairs with sampled exact intersections: three retained outer-duty SDS beams and five service wires. The report remains an unaccepted discrete screen; it proves neither continuous blockage nor a physical route.
- **WJ-05 center wire-relief** ([archived probe](hypotheses/wj05-center-node-relieved.md)) clears the L = 82 mm wire-relief body geometry. The right station is 2.303793 mm from the wire; the mirrored left result is a 9.25 mm bounding-box lower bound. It retains 48 + 18 fixed axes. Two properly seated generic head-tool proxies overlap the center posts at upper-header row 2 (left and right), 1,481.459916 mm³ each. This generic proxy-to-wood screen establishes neither actual wrench access nor a complete operation path; see the catalog-sized comparison below for current tool-envelope evidence.
- **WJ-05 center tool screen** ([catalog-envelope comparison](hypotheses/wj05-center-tools/README.md)) now records overlaps for socket/extension, counterhold, and ratchet proxies at both upper-header row-2 stations. Opposite ratchet strokes still hit lower-post washer/timber. These are external envelopes, not proof of tool fit or impossibility. A separate 10 mm outward post/lower-cleat/axis variant is in progress.
- **WJ-06 right outer paired rails** ([installed-geometry archive](hypotheses/wj06-outer-pair.md), `b69ca5fa`) materializes two far-end right rail-pair geometries and eight provisional bolt stacks. It is static installed geometry only; whether +N insertion needs side release is untested. The next screen tests the rail and two cleats moving +N with principal/side members retained and X bolts absent. Assembly sequence, wrench access, and capacity remain untested. Right four-duty integration is in progress; no replacement is accepted.

Keep these as separate hypotheses. Continue tool, withdrawal, and staged-motion
work against retained obstacles; integrate only after parent review of
source-bound results.

No joint has accepted resistance or capacity. MVP-L, fresh six-case evidence,
and MVP-E remain gated by the work below.

## Critical path

| Stage | Work | Gate to advance |
| --- | --- | --- |
| **1. Repair outer nodes (finish WJ-03)** | Preserve the final candidate-only service-bore correction and lower-panel-first order before kicker extraction/return; kicker motion with the panel installed still overlaps. No LED disconnection is needed or inferred. Resolve the +86.018477 mm permanent rear projection by a dimensioned geometry revision or named exception; verify the separate temporary bolt-stroke workspace. | Both sides have feasible stock/cuts, complete transfer paths, supported washer seats, the required staged removal order, tolerance-aware installed and removal clearances, and a recorded `advance_layout` result. Keep `revise_named_constraint` until the permanent disposition and remaining local sequence checks pass; do not defer required WJ-03 work to WJ-07. |
| **2. Prove one ordinary joint (WJ-04)** | Keep every consumer bound to `narrow_x95p25_ordinary_bolt_candidate` at `clip_horizontal_lower_right_1`. Probe/mechanics contact areas now share the finite-probe basis; the mechanics report lists the canonical rectangle separately as a coordinate audit. The probe's 0.764 mm generic 50 mm rail-tool gap and 21.872532 mm temporary nut-exit excess are unchanged; neither is a tolerance pass. The refreshed tool screen centers its 3.0 mm slab within target head/nut thickness. Paired-wrench and upright counterhold bounds clear; rail counterhold, nut stroke/reindex, and full-turn wrench-plus-axial nut-removal bounds overlap. Loose nut/washer translation sweeps clear at upright stacks and overlap at rails. Replace broad envelopes with source-supported wrench geometry and a bounded operation path; neither clear bounds nor overlaps prove actual access or impossibility. Rebuild mechanics only on fresh candidate actions; the current early screen uses stale angle-demand inputs. Resolve conditional end/edge geometry with signed loads, and use the 2×6 rip only with post-rip grade evidence. | One complete nominal and tolerance-aware joint with a traceable stock/cut route, matched geometry/hardware/tool/mechanics, an evidenced disassembly path, fresh demands, and signed end/edge treatment. List only station families whose geometry can reuse it; screen mirrored and service-different stations independently. |
| **3. Close center and kicker subsystem (WJ-05)** | Preserve the fresh nominal transfer and receiver reports as diagnostics. Complete the four center principal/header and moved-post/header structural duties, both backer/header attachments, and both inner kicker edge supports. Recheck E1/G1, T-nuts, LEDs, wire, and all twelve retained frame-bolt arrangements. | The 66 axes retain supported finished-wood receivers and required embedment; center and edge-support load paths reach the frame through accepted joints. Each backer attachment and complete joint has evidence; socket outside-envelope clearance is not treated as tool fit. |
| **4. Finish whole-frame geometry (WJ-06)** | Assign one accountable replacement owner to every former angle duty. Add residual top, rail, inclined, and splice details only where the actual topology needs them. Generate one source-bound finished-part model and viewer, including all new and retained fasteners and all machining. | Exactly 24 duties and 144 removed SDS axes reconcile with physical interfaces; all 66 fixed screw axes and twelve rechecked frame-bolt arrangements appear; no legacy structural SDS path survives; part, assembly, bolt, and move-operation counts are separate. |
| **5. Close MVP-L (WJ-07)** | Run complete installed, tool, insertion, reverse-removal, same-family, cross-family, protected-service, floor/pad, and tolerance screens on the integrated model. Define manufacturable cut setups, tool needs, and forward/reverse assembly order. | No known unintended collision or unsupported seat; required separations stay positive under stated dimensional bounds; every joint can be assembled and removed without routine structural wood-thread removal. Publish a complete owner-reviewable layout with limits, not a drilling release. |
| **6. Freeze mechanics before final cases (WJ-08)** | For every host and connector interface, define unilateral contact, opening, bolt tension/lateral action, slip, rotational stiffness, reference point, and all three moment components. Check finished wood sections, end/edge/grain directions, splitting, bolt groups, connector internal joints, washers, bolts, retained frame bolts, and any house shoulders. Migrate all 36 frozen legacy safety questions plus the 11 new obligations in [`criteria.json`](criteria.json) with an applicable method or explicit reason. | A fingerprinted, fail-closed candidate and check contract. No unknown resistance or inherited angle capacity is marked pass. Select bounded stiffness/contact sensitivities before solving. |
| **7. Run fresh complete-frame evidence (WJ-09)** | Run the six required cases serially on one frozen candidate. Authenticate geometry, producers, convergence, force sources, simultaneous signed interface actions, monitors, and check outputs. Revise failed joints or methods, then rerun every affected case and check. | All six source-comparable cases meet numerical prerequisites and every applicable adopted/new criterion has a supported disposition. Report governing case, mode, and margin; retain failed and nonconverged runs as diagnostics. |
| **8. Deliver MVP-E packet (WJ-10)** | Generate coordinated cut/drill/hardware, cost, assembly, and inspection documents from the same frozen model. Bind actual proposed stock, hardware SKUs/specifications, delivered-length and tool assumptions, whole-stock yield, quantities, and costs. Leave Actual/Disposition fields blank until observed. Obtain an independent review of the finished geometry, mechanics, evidence, and shop instructions; fix confirmed findings and rerun affected gates. | One internally consistent conditional development packet and completion ledger with no contradictory instruction or unresolved required load path. Record every remaining receiving or physical-observation condition precisely. |

## Avoid a late mechanical dead end

Before copying the WJ-04 workhorse to many stations, run a **bounded
representative mechanics screen** on the WJ-03 and WJ-04 joint topologies.
Use actual interface graphs and load directions, but label old-case actions
as diagnostic until the new full-frame solution exists. Reject an obviously
unworkable split, washer, bolt-group, or connector-body detail early. This
does not replace WJ-08's complete method contract or WJ-09's fresh demands.

## Decision and evidence discipline

- Each stage returns `advance`, `revise_named_constraint`, or `blocked` with
  exact geometry, method, source, and remaining obligation. Do not infer a
  pass from an empty collision list, a single force component, or a favorable
  diagnostic case.
- Select real bolt, nut, washer, stock, and tool dimensions before claiming
  tolerance-aware MVP-L. Until then, label occupied shapes and bores as
  provisional, never as drilling instructions.
- A failed adopted criterion, missing load path, contradictory shop instruction,
  or incompatible delivered part stops the affected operation. Do not add
  external sign-off, floor-friction testing, or unrelated redesign as blanket
  prerequisites.
- After MVP-E, make an explicit owner decision whether to select this
  candidate. Selection is not automatic and does not fill unobserved physical
  receiving cells. WJ-11 records delivered parts, actual cuts/holes, assembly,
  disassembly, and deviations if a prototype is built.

## Historical progress and review notes

The following pre-integration snapshots remain as reasoning history; they are
not the current WJ-03 sequence or active WJ-04 probe. The old sequence report
recorded 42 adjacent-panel/kicker screw tool and withdrawal sweeps without
unrelated nominal hits, but lacked the four WJ-05 backers. It sampled direct
kicker hits at 1–18 mm, no sampled hits on a 100 mm path after staging the
lower panel, and 0 mm lower-panel clearance to the base-floor member at the
staged pose. Support, continuous movement, handling, service disconnection,
real tool access, and tolerances were open. Its short nut/washer disengagement
path had no hardware capture or retrieval method. The 86.018477 mm permanent
rear excess and 175.948756 mm temporary bolt-stroke workspace were reported
separately. The old WJ-04 report used a 95.25 × 50.8 × 119.7 mm cleat with a
generic 50 mm tool collision and a 3.652 mm 40 mm-tool gap. It is not evidence
for the current 95.25 × 38.1 mm configuration.

The earlier WJ-03 geometry review found that shortening the under-header link
moved its first header bolt 30.1 mm from the grain end instead of 48.1 mm,
using a provisional 6.35 mm bolt. That is a geometry tradeoff, not a signed
end-distance verdict. The temporary-stroke excess is workspace, not permanent
depth. The historical link geometry still needs a complete integrated tool,
support, service, movement, and tolerance screen before reuse.

## Next decisions and gates

1. **Preserve the integrated records.** The final WJ-03 report includes current
   WJ-05 geometry and the candidate-only service-bore correction. The prior
   right-return endpoint hits are historical; the current return is clear.
   Keep refreshed artifacts bound to their source fingerprints and preserve
   the lower-panel-first kicker order.
2. **Resolve the WJ-03 geometry and sequence gates.** Choose a dimensioned
   geometry revision or a named exception for the 86.018477 mm last-reported
   rear excess against the ordinary 139.7 mm limit. Confirm the separate
   bolt-stroke workspace and positive tolerance margin for both staged poses.
   Keep `revise_named_constraint` until the permanent disposition, support,
   tolerance, and local sequence checks are resolved.
3. **Keep WJ-04 on one matched trial.** The active diagnostic config is
   `narrow_x95p25_ordinary_bolt_candidate`; it uses a 95.25 × 38.1 × 119.7 mm
   cleat, grain N, K.L. Jack 3.75-in rail and 6-in principal candidates, and
   two Type A Wide washers per bolt. The 100 × 53.34 mm pose is unbound until
   stock, bolt grip, delivered thread engagement, tools, tolerances, and
   mechanics all match. The cataloged FACOM `34.7/16` wrench pair is only a
   tool candidate. The updated conservative screen centers its modeled slab
   axially on the fastener and clears paired-wrench/upright counterhold
   envelopes, but remaining overlaps and unsupported jaw/handle geometry leave
   actual install/removal access unproved. The 2×6 rip is only a raw-stock lead
   until post-rip grade evidence exists. No joint or capacity is accepted.
4. **Complete WJ-05 load paths.** Fresh transfer and receiver reports are
   nominal geometry diagnostics. The four center screw receivers terminate in
   separate backers; two provisional bolts per backer do not establish the
   backer/header joint. Complete those two attachments and all four
   principal/header and moved-post/header duties, with tool access and
   mechanics, while retaining all 66 screw axes and rechecking all twelve
   starting frame-bolt arrangements.
5. **Keep the duty registry source-bound.** Current registry covers 24 duties
   and 144 former SDS axes, preserves 66 screw axes and twelve frame-bolt
   obligations, records geometry for 5/24 duties, and accepts zero
   replacements. Its residual-probe entry still lists 540 potential WJ-06
   corridors with none materialized in that registry; its replacement
   complete-stack evidence count remains zero. The separate WJ-06 paired-rail
   geometry remains a hypothesis, outside registry acceptance. Regenerate
   only if a bound input changes; source binding alone does not accept a
   connection.

Only after source-bound geometry, methods, tolerance screens, and complete
joint evidence pass should WJ-08/WJ-09 work begin. Do not launch native
six-case work from component tests, receiver continuity, or nominal clearance
alone.
