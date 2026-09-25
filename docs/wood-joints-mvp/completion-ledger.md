# Wood-joint MVP completion ledger

Source commit: `df7f5eca86ae831b35a8bcf9e6dcd7ae8af852bb`

Candidate: `compact-floor-flush-wood-joints-development`

Selected authority remains `current-candidate.json`. Preserved barrel authority
remains `barrel-nut-candidate.json`.

## September 24 execution follow-up

The corrected [access-relief study](hypotheses/wj24-access-relief/README.md)
now records nine connector-only variants with retained local contact and
washer-seat support. It exposes local section losses and separates nominal
LED movement from enlarged clearance envelopes. Wire handling, manufacturing
tolerances, and strength remain unresolved; no relief is selected for cutting.

The current WJ24 [representative STEP export](hypotheses/wj24-patch-reconciliation/README.md)
has completed. Its new five-body mesh contains 89,743 nodes and 46,629 C3D10
elements; independent audits are in progress. The earlier WJ16 mesh and its
surface classification remain historical inputs, pending explicit current
geometry and hardware reconciliation. No native structural response has run.

The complete-layout tool diagnostic screened 100 ordinary stacks and retained
four backer stacks as an unmodeled access-state obligation. Its raw results
require separation of retained geometry and temporary operation envelopes,
followed by removal-order and geometry review. The actual WJ24 backer mechanics
extraction now binds two interfaces, four bolts, and four fixed Hillman load
entry axes; it supplies no demands or accepted connection properties.

The [local viewer and browser evidence](hypotheses/wj24-viewer-review/README.md)
are archived and parent-verified; publication waits for quiet hours to end.
The [conditional bolt-length screen](wj24-bolt-length-screen.md),
[stock yield](wj24-timber-stock-yield.md), and
[partial costs](wj24-development-costs.md) exist, while final hardware fit,
SKU selection, and complete costs remain open. These advances do not close
the stage acceptance gates in the table below.

| Chunk | Status | Evidence | Remaining work |
|---|---|---|---|
| WJ-00 | Complete | `wood-joints-candidate.json`, `plan.md`, `decision-log.md`, `criteria.json`; `authority-integrity.json` and `scripts/wood_joint_authority_integrity.py` reproduce exact selected/barrel authority and all 725 kerf-right export bytes from the reviewed handoff commit; all release flags false | None within WJ-00 |
| WJ-01 | Complete | `source-inventory.json`, `source-inventory-summary.md`, `scripts/wood_joint_inventory.py`; 24 duties, 144 SDS axes, 66 fixed screw axes, twelve frame-bolt arrangements, six source contacts, two unresolved receiver obligations, source faces, grain axes, and local transforms | Receiver attachments and replacement interfaces remain unresolved by design |
| WJ-02 | Complete | `mini_moonboard/wood_joint_geometry.py`; typed finished-part, interface, bolt-stack, evidence, bore, contact, clearance, and access records; focused negative tests; source-bound WJ-03 fixture persists face, grip, installed-envelope, and access reports | No connection resistance or strength pass is established by the primitives |
| WJ-03 | Partial; current sampled sequence diagnostic, support, envelope, and tolerance gates open | `mini_moonboard/wood_joint_frame.py`, candidate-only `mini_moonboard/wood_joint_panel_machining.py`, `scripts/wood_joint_wj03_sequence.py`, and final `wj03-sequence-diagnostic.json` (`b547a604…7e0f4`) include WJ-05 diagnostic backers, shifted posts, bolts, stacks, and four center receiver IDs. The corrected candidate service bores clear the 35 right-return LED hits reported at the earlier pre-helper checkpoint `0ebf90eb`; the left return was already clear. Kicker motion with the lower panel retained still overlaps by 1–18 mm; extraction and return pass when the lower panel is staged first. No LED disconnection is needed or inferred. Other paths/tools are unchanged. Both staged poses have 0 mm nominal gap to base-floor wood; permanent rear projection remains +86.018477 mm beyond the ordinary envelope, and the 315.648756 mm bolt-stroke reach remains separate temporary workspace. | Resolve support, continuous motion, tolerance, and permanent-envelope disposition; complete interfaces and stacks before updating acceptance. No sequence, layout, or capacity acceptance. |
| WJ-04 | Diagnostic revise; bound probe, early mechanics, and tool-access reports current | `wj04-probe.json` binds `narrow_x95p25_ordinary_bolt_candidate` at configuration hash `d1c63e1f…206c0e`; the cleat has 0.0 mm nominal excess beyond the ordinary N envelope, modeled stacks/seats clear locally, generic 50 mm rail-tool gap is 0.764 mm, and temporary nut exit extends 21.872532 mm beyond the ordinary limit. `wj04-tool-access.json/.md` reports `diagnostic_overlap_present`; conservative envelopes overlap solids during several counterhold/stroke/reindex/removal operations, but the report neither proves physical access nor impossibility. `wj04-early-mechanics.json/.md` binds six historical angle-demand cases but does not replay them; four source files mismatch per case, so capacity remains unresolved. Mechanics consumes the probe's finite-probe rail contact area (11,401.398713 mm²) and reports the canonical bounding rectangle separately (11,401.425 mm²; −0.026287 mm² delta); principal values reconcile within rounding. The 2×6 rip in `stock-and-cut-basis.md` needs post-rip regrading. | Refine and physically bound tool paths; verify delivered grade, bolt/thread transitions and nut engagement, actual wrench motion, tolerances, signed end/edge treatment, fresh candidate demand, integrated WJ-03 geometry, and complete joint resistance. No capacity or WJ-04 acceptance is established. |
| WJ-05 | Diagnostic partial; fresh nominal reports | `wj05-center-backer-transfer.json/.md` reports `nominal_geometry_clear_diagnostic`; `wj05-receiver-audit.json/.md` reports `blocked_center_receiver_path`. All 66 axes stay fixed: 62 enter frame timber and four enter two separate 4×4 backers with 45.24375 mm nominal receiver length. The repaired right upper socket proxy has 2.959434 mm seated wire clearance and 1.661248 mm along the full approach sweep. | Four center structural duties and two backer/header attachments remain unaccepted; long through-bolt/thread engagement, bearing, splitting, washer/contact, tool fit, ratchet access, service motion, and tolerances remain open. Complete receiver-to-frame paths and joint mechanics; physical observations remain blank. |
| WJ-06 | Complete diagnostic composition; 0 accepted replacements | The [full WJ24 layout](hypotheses/wj24-integrated-static/README.md) contains sixteen rebuilt hosts, twenty-eight connector pieces, 104 proposed bolt axes, 520 CAD roles and all 144 removed SDS axes. No legacy angles/SDS or source-only overlays remain. All 66 fixed axes, four backer redirects, shifted center posts and twelve frame bolts reconcile; the parent independently matched all fourteen retained raw-host records and 68 source-input hashes. | Resolve G1/G12 provisional hold clearance, reduced bottom-center bearing face, tools, tolerances and mechanics for every duty. Publish the complete diagnostic viewer after quiet hours; no joint is accepted. |
| WJ-07 | Diagnostic partial; no MVP-L acceptance | [Full WJ24 static diagnostic](hypotheses/wj24-integrated-static/README.md): all eighteen implemented static/source-tracking gates pass. [Individual LED extraction](hypotheses/wj24-led-extraction/README.md) tests 132 continuous rearward sweeps against 842 stationary shapes; G7 intersects the lower full-stock cleat by 319.657955 mm³. Earlier wired rail hits and unwired zero-gap contacts remain preserved. | Resolve G7 extraction and G1/G12 hold access, supported panel/wiring staging, whole-strand feeding, local tool conflicts, tolerances, assembly and reverse removal. Static fit and 131 clear LED sweeps do not prove transport. |
| WJ-08 | Diagnostic partial; no mechanics acceptance | `criteria.json` contains planning migration only. [Backer unit-wrench witnesses](hypotheses/wj12-backer-unit-statics/README.md) close 24 signed synthetic cases with finite patches checked in both finished members; [sampled sections](hypotheses/wj12-sampled-sections/README.md) quantify named local cuts. [Full-stock input extraction](hypotheses/wj16-full-stock-mechanics-inputs/README.md) binds eight WJ16 bolts and four contact planes with explicit grain and hardware datums. The [full-stock thread-bearing screen](hypotheses/wj04-full-stock-thread-screen/README.md) covers eight bolts and 256 member/corner fractions; the maximum beyond the recorded Lb boundary is 7.8549%, below the conditional one-quarter geometry limit. None supplies actual demand or resistance. | Complete connection mechanics, actual demands, critical sections, bearing/wood/washer resistance, and the evidence-bound criteria contract. |
| WJ-09 | Preparation partial; execution authorized, model/method readiness pending | Owner authorized native mechanics on 2026-09-24; decision recorded in `docs/history/decision-log.md`. The [representative five-body coarse mesh](hypotheses/wj04-patch-mesh/README.md) has 91,089 independent nodes and 47,469 quadratic tetrahedra and passes implemented geometry/ownership audits; two failed preparation attempts are preserved. The [surface classification](hypotheses/wj04-patch-surfaces/README.md) binds four wood interfaces and sixteen bore/member pairs, with independently verified outward planar normals. No fresh structural response or candidate cases run | Complete hardware/contact mechanics and numerical sensitivities. Freeze the complete candidate, cases, and methods, then run native cases serially. Fresh same-configuration six-case evidence remains required; historical actions cannot replace it. |
| WJ-10 | Inventory partial; no shop-package acceptance | [Complete-layout inventory](hypotheses/wj24-hardware-inventory/README.md) reconciles 104 proposed bolts, 104 nuts and 216 washers, 52 ordered receiver pair groups and 28 connector blanks. Retained frame bolts and Hillman screws remain separate. | Assign sixteen remaining bolt lengths; verify all hardware fit and specifications, stock yield, prices, tools and coordinated instructions. Complete independent review and the conditional MVP-E packet. |
| WJ-11 | Owner/shop | None | Physical receiving and observed prototype records; MVP-P |

## WJ-00 acceptance record

- New candidate identity is distinct and does not replace selected authority.
- Selected and preserved barrel authority files were read and left unchanged.
- `authority-integrity.json` reproduces both authority-file SHA-256 values and
  the aggregate SHA-256 of all 725 kerf-right export paths and STL bytes from
  the handoff commit; its source script fails if any byte differs.
- Starting repository commit equals handoff reviewed commit.
- Kerf-right physical surface and 66 screw axes are fixed.
- Ordinary 139.7 mm local-N envelope has an explicit datum/reporting policy.
- No primary-member notch is the default; bounded housed investigation requires
  complete cut and joint evidence.
- Connector construction options and exclusions are explicit.
- Imported legacy criteria remain pending; no pass or capacity is inherited.
- Layout, engineering, prototype, drilling, fabrication, structural, and
  climbing release flags are false.

## Current claim boundary

The narrow WJ04 and original WJ03 entries preserve the active registry's
historical reports. Current development geometry is the complete WJ24
diagnostic in WJ-06, including compact outer nodes and full-stock ordinary
cleats; neither registry promotion nor joint acceptance has occurred.
The [physical hardware export](hypotheses/wj04-mechanics-hardware/README.md)
and [parent seat audit](hypotheses/wj04-mechanics-hardware/seat-and-envelope-audit/README.md)
now establish nominal representative hardware geometry and finite bearing
faces. They do not establish contact response, resistance or native readiness.

WJ-00 through WJ-02 are complete. WJ-03 establishes a source-bound nominal
outer-node topology and returns `revise_named_constraint`; it does not establish
layout acceptance, selected hardware, tolerance feasibility, connection
resistance, a native solve, shop dimensions, observed material, or release.
