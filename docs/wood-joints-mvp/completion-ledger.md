# Wood-joint MVP completion ledger

Source commit: `df7f5eca86ae831b35a8bcf9e6dcd7ae8af852bb`

Candidate: `compact-floor-flush-wood-joints-development`

Selected authority remains `current-candidate.json`. Preserved barrel authority
remains `barrel-nut-candidate.json`.

| Chunk | Status | Evidence | Remaining work |
|---|---|---|---|
| WJ-00 | Complete | `wood-joints-candidate.json`, `plan.md`, `decision-log.md`, `criteria.json`; `authority-integrity.json` and `scripts/wood_joint_authority_integrity.py` reproduce exact selected/barrel authority and all 725 kerf-right export bytes from the reviewed handoff commit; all release flags false | None within WJ-00 |
| WJ-01 | Complete | `source-inventory.json`, `source-inventory-summary.md`, `scripts/wood_joint_inventory.py`; 24 duties, 144 SDS axes, 66 fixed screw axes, twelve frame-bolt arrangements, six source contacts, two unresolved receiver obligations, source faces, grain axes, and local transforms | Receiver attachments and replacement interfaces remain unresolved by design |
| WJ-02 | Complete | `mini_moonboard/wood_joint_geometry.py`; typed finished-part, interface, bolt-stack, evidence, bore, contact, clearance, and access records; focused negative tests; source-bound WJ-03 fixture persists face, grip, installed-envelope, and access reports | No connection resistance or strength pass is established by the primitives |
| WJ-03 | Partial; integrated sequence diagnostic current, endpoint and permanent envelope open | `mini_moonboard/wood_joint_frame.py` describes the mirrored outer nodes; `scripts/wood_joint_wj03_sequence.py` and `wj03-sequence-diagnostic.json` include the WJ-05 diagnostic backers, shifted posts, bolts, stacks, and four center receiver IDs. Forty-two screw/tool and shank-withdrawal screens, both lower-panel extractions, and staged kicker extraction/reverse paths have no sampled unrelated hits. The left lower-panel return clears; the right return hits fixed LEDs G1–K7 only at the 250 mm terminal pose. This is an inherited source-pose mismatch: the kerf-right panel is shifted by `-KERF_EACH_MM` while electrical parts remain fixed; outbound samples omit installed zero and reverse samples include it. The issue is not caused by the WJ-05 backers. Both 250 mm panel and 25 mm kicker staged poses have 0 mm nominal gap to base-floor wood. | Resolve the candidate service-bore pose convention and regenerate both paths; no LED removal or disconnection is prescribed as a fix. Also resolve support, continuous motion, tolerances, and +86.018477 mm permanent N excess against the ordinary envelope. The 315.648756 mm bolt-stroke reach remains a separate temporary workspace issue. No sequence, layout, or capacity acceptance. |
| WJ-04 | Diagnostic revise; bound probe, early mechanics, and tool-access reports current | `wj04-probe.json` binds `narrow_x95p25_ordinary_bolt_candidate` at configuration hash `d1c63e1f…206c0e`; the cleat has 0.0 mm nominal excess beyond the ordinary N envelope, modeled stacks/seats clear locally, generic 50 mm rail-tool gap is 0.764 mm, and temporary nut exit extends 21.872532 mm beyond the ordinary limit. `wj04-tool-access.json/.md` reports `diagnostic_overlap_present`; conservative envelopes overlap solids during several counterhold/stroke/reindex/removal operations, but the report neither proves physical access nor impossibility. `wj04-early-mechanics.json/.md` binds six historical angle-demand cases but does not replay them; four source files mismatch per case, so capacity remains unresolved. Mechanics consumes the probe's finite-probe rail contact area (11,401.398713 mm²) and reports the canonical bounding rectangle separately (11,401.425 mm²; −0.026287 mm² delta); principal values reconcile within rounding. The 2×6 rip in `stock-and-cut-basis.md` needs post-rip regrading. | Refine and physically bound tool paths; verify delivered grade, bolt/thread transitions and nut engagement, actual wrench motion, tolerances, signed end/edge treatment, fresh candidate demand, integrated WJ-03 geometry, and complete joint resistance. No capacity or WJ-04 acceptance is established. |
| WJ-05 | Diagnostic partial; fresh nominal reports | `wj05-center-backer-transfer.json/.md` reports `nominal_geometry_clear_diagnostic`; `wj05-receiver-audit.json/.md` reports `blocked_center_receiver_path`. All 66 axes stay fixed: 62 enter frame timber and four enter two separate 4×4 backers with 45.24375 mm nominal receiver length. The repaired right upper socket proxy has 2.959434 mm seated wire clearance and 1.661248 mm along the full approach sweep. | Four center structural duties and two backer/header attachments remain unaccepted; long through-bolt/thread engagement, bearing, splitting, washer/contact, tool fit, ratchet access, service motion, and tolerances remain open. Complete receiver-to-frame paths and joint mechanics; physical observations remain blank. |
| WJ-06 | Diagnostic registry current; 0 accepted replacements | `duty-registry.json` is source-bound to current inputs and maps 24 duties / 144 former SDS axes, while preserving 66 Hillman axes and twelve frame-bolt obligations. It records four WJ-03 owners, one WJ-04 diagnostic owner, four blocked WJ-05 proposals, and fifteen unmaterialized WJ-06 proposals. The absent WJ-06 report leaves 540 potential corridors, zero materialized, and zero full stacks; WJ-05 has four provisional axes and zero full stacks. | Implement and verify every duty with complete interfaces and stacks; keep all replacement acceptance claims at zero until each duty has complete evidence. Do not infer acceptance from owner mapping. |
| WJ-07 | Planned | None | Close full clearance, manufacture, assembly, and reverse-removal; MVP-L |
| WJ-08 | Planned | `criteria.json` contains planning migration only | Complete connection mechanics and evidence-bound criteria contract |
| WJ-09 | Planned | None | Fresh same-configuration six-case evidence and bounded sensitivities |
| WJ-10 | Planned | None | Costed coherent development/shop package; MVP-E |
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

WJ-00 through WJ-02 are complete. WJ-03 establishes a source-bound nominal
outer-node topology and returns `revise_named_constraint`; it does not establish
layout acceptance, selected hardware, tolerance feasibility, connection
resistance, a native solve, shop dimensions, observed material, or release.
