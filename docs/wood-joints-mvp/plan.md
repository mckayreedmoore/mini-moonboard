# Wood-joint MVP plan

For the next bounded execution sequence from the WJ-03 partial result through
MVP-E, see [next MVP plan](next-mvp-plan.md).

## Authority and endpoint

`compact-floor-flush-wood-joints-development` is a separate development lane.
It does not replace `current-candidate.json`, alter the selected
`compact-floor-flush-development` package, or promote the preserved barrel-nut
work in `barrel-nut-candidate.json`. The source snapshot is repository commit
`df7f5eca86ae831b35a8bcf9e6dcd7ae8af852bb`, which matches the handoff's
reviewed commit.

The implementation endpoint is MVP-E: one frozen, complete wood-connector and
ordinary-through-bolt frame with justified joint methods and inputs, fresh
complete-frame cases, resolved applicable checks, and a coherent costed shop
package. MVP-L is the preceding complete-layout gate. MVP-P requires later
physical receiving, assembly, disassembly, and observation records. None is
complete at WJ-00.

## Frozen scope

- Preserve the kerf-right climbing surface, panel outlines, hold grid, kicker
  geometry, service function, and all 66 panel/kicker screw axes: 48 main-panel
  and 18 kicker axes. Keep the purchased Hillman 42605 policy separate from
  structural bolts.
- Start from all 24 legacy ML24Z duties, 144 structural SDS attachments, and
  twelve frame-bolt arrangements. A replacement must map every duty and recheck
  every changed host, stack, action, and access condition.
- Use wood connector bodies and ordinary through-bolts with metal nuts and
  suitable washers. A connector may be a realizable one-piece solid body, a
  mechanically complete multi-piece assembly, or an explicitly qualified
  structural-plywood body. Its stock, grain or layup, internal interfaces, and
  fabrication must be visible. Glue-dependent composite action is not assumed.
- Begin with connector-side shaping and no notch or housing in a primary frame
  member. A primary-member housing may be investigated only for a named benefit
  after its exact cut, fabrication, remaining section, splitting, bearing, and
  complete joint behavior are checked. No house is approved to cut.
- Preserve the ordinary 139.7 mm local-N envelope. Every station report must
  name its datum and give connector N-min/N-max, complete installed hardware
  projection, and tool envelope. Rear-face placement creates no automatic
  exception. Any exception request must name the station and extra projection.
- Preserve individual-member transport and eliminate routine removal of
  structural wood-engaging threads. Count the retained 66 panel screw
  operations separately.
- Preserve the conditional no-slip floor assumption. Do not add connector
  floor support, an anchor claim, or a floor-friction test requirement.
- Do not replace actual member stock globally with nominal 2x6. Hidden member
  changes require exact receiver, edge-support, connection, transport, and
  full-frame checks.
- Exclude custom steel, a new steel-angle architecture, barrel nuts, half-laps,
  other interlocking primary-member joinery, and unqualified capacities.

## Bounded implementation sequence

| Chunk | Result | Depends on | Gate state |
|---|---|---|---|
| WJ-00 | Lane authority, source snapshot, scope decisions, criteria seed, and untouched baseline | None | Complete |
| WJ-01 | Exact 24-duty, 144-SDS, 66-axis, receiver, contact, frame-bolt, member-face, and local-datum inventory | WJ-00 | Complete |
| WJ-02 | Finished-part, interface, bolt-stack, evidence, extrema, bore, clearance, and access primitives | WJ-01 | Complete |
| WJ-03 | Complete mirrored outer nodes replacing each same-side header-outer/base-outer duty pair | WJ-02 | Partial: final sequence report `b547a604…7e0f4` clears the 35 right-return LED hits recorded in the earlier pre-helper report at checkpoint `0ebf90eb`; candidate-only fixed-service-bore machining restores the source datums. The left return was already clear. Kicker motion still overlaps the lower panel by 1–18 mm if that panel remains installed; with the panel staged, extraction and return pass. No LED disconnection is needed or inferred. Both staged poses have 0 mm nominal base-floor gap; permanent rear excess remains +86.018477 mm. Keep `revise_named_constraint` while permanent envelope, support, tolerance, and complete interfaces remain open. |
| WJ-04 | No-primary-notch ordinary workhorse at `clip_horizontal_lower_right_1`, then related instances | WJ-02 and WJ-03 priority result | Diagnostic revise: current probe binds the 95.25 × 38.1 × 119.7 mm grain-N cleat and K.L. Jack 3.75-in rail / 6-in principal candidates. Local body excess is 0 mm; stacks clear, but generic 50 mm rail-tool gap is 0.764 mm and temporary nut exit extends 21.872532 mm past the ordinary limit. Early mechanics binds historical angle actions with four mismatched source files per case and no fresh demands. Mechanics uses the probe's finite-probe contact area and reports the canonical bounding rectangle separately. Tool-access report has conservative external envelope overlaps and establishes neither physical access nor impossibility. The 2×6 rip needs post-rip regrading; 100 × 53.34 mm remains unbound. |
| WJ-05 | Complete center principal/header, moved-post/header, kicker receiver, inner-edge, and receiver-to-frame paths | Relevant WJ-01 through WJ-04 interfaces | Diagnostic partial: fresh transfer and receiver reports preserve all 66 axes; 62 enter frame timber and four enter two diagnostic backers. The right upper socket proxy has 2.959434 mm seated clearance and 1.661248 mm full-sweep wire clearance. Four center structural duties and both backer/header attachments remain unaccepted; this is not a tool-fit or resistance pass. |
| WJ-06 | Remaining duties and one integrated candidate | WJ-03 through WJ-05 | Current source-bound duty registry maps 24 duties / 144 former SDS axes, retains all 66 panel/kicker screw axes and twelve frame-bolt obligations, and accepts zero replacements. It records 540 potential WJ-06 corridors with none materialized or fully stacked, plus four provisional WJ-05 axes with no complete stacks. |
| WJ-07 | Finished-solid clearance, manufacturability, assembly, and reverse-disassembly closure: MVP-L | WJ-06 | Planned |
| WJ-08 | Complete-joint resistance, stiffness/contact model, and authenticated criterion contract | WJ-07 | Planned |
| WJ-09 | Fresh six-case complete-frame evidence and declared bounded sensitivities | WJ-08 | Planned |
| WJ-10 | Costed coherent development and shop package: MVP-E | WJ-09 | Planned |
| WJ-11 | Delivered-part receiving and observed assembly, disassembly, and move record: MVP-P | WJ-10 plus physical work | Owner/shop |

Geometry work begins with the combined outer node, then the representative
ordinary workhorse. Six-case solves wait until one complete geometry and its
applicable connection/stiffness inputs exist. Failed layouts remain evidence;
hard-coded status, hidden clashes, or reduced collision scopes do not establish
completion.

## Evidence and claims

Every evidence record must bind candidate, geometry, source fingerprints,
producer command, artifact hash, applicability, status, result, governing case,
and limits. Statuses distinguish `unverified`, `failed`,
`passed_under_recorded_assumptions`, and `not_applicable_with_reason`. Actual
observation values remain null until observed.

No WJ-00 record establishes layout acceptance, strength, drilling, fabrication,
structural release, inspected construction, floor verification, or climbing
rating.
