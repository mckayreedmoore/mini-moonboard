# Structural-only bolted candidate plan

This document establishes the separate `compact-floor-flush-bolted-development`
lane from the v2 Luna handoff. It does not promote the candidate, qualify a
connector, or authorize fabrication.

## Binding scope

- Replace the connection duties of 144 structural SDS attachments at 24 ML24Z
  stations with a separately evidenced structural connection system.
- Retain the twelve existing frame-bolt arrangements as the starting layout;
  recheck their changed stacks, loads, and interference later.
- Preserve all 48 main-panel and 18 kicker screws. Panel removal is permitted;
  panel inserts, panel through-bolts, and new panel hardware are excluded.
- Target zero routine structural wood-thread removals per move. This is not a
  whole-board zero and does not remove the 66 panel screw operations.
- Preserve the selected baseline and its historical evidence. No new candidate
  result may overwrite or authenticate an old result.

## Gates and sequence

`LB-00 -> LB-01 -> (LB-02A, LB-02B) -> (LB-03A, LB-03B, LB-03C) -> LB-04`

After architecture selection: shared connection model, candidate geometry,
six layout families, integration, width adapter, mechanics, resistance checks,
native producer contract, and G2 review precede any native case. Native cases
run serially from `a12-left` through `a1-rear`; final exports and independent
review do not change repository authority automatically.

## Current gate status

The G0 source and scope partition is now exported from the official and
kerf-right connection-axis packets. The normalized panel records, all 222
classified attachments per width, 24 station duties, twelve retained frame
bolts, and draft separation references are in the panel and interface
contracts. These are baseline records, not candidate bolt geometry.

G1 remains open. A66 is a common-retail prototype priority, but the current
family modules are AB90 inventory sketches. No representative joint has a
complete applicable fit/load-path record or 24-station architecture assignment.
The bounded retail follow-ups found no substitute with published bolted loads
applicable to the preserved single-2x6 thickness. The exact A66 manufacturer
information request is in `docs/bolted-candidate-g1-decision.json`; it has not
been sent, and a response would still need the three representative fit checks.
The user's suggested outward center-support shift is screened separately in
`docs/bolted-candidate-prototypes/center-support-solid-screen.json`. At 5, 10,
and 15 mm per side, all 20 frozen panel axes intersect the translated raw
center timber, but the nominal bore-edge material falls to 11.98, 6.98, and
1.98 mm respectively. All six center-adjacent bottom/service rail inner ends
would also need recutting; at those sample offsets their twelve retained panel
screw cylinders still intersect the nominal recut rail solids. This is only a
geometry screen; connector stack clearance, timber resistance, and panel edge
support remain unresolved. No offset is selected. G2 remains closed, and no
bolted-candidate native case has run. The task ledger marks incomplete
construction and engineering tasks as such rather than using prototype counts
as completion evidence.

## Current nonblocking owner checkpoints

The owner reported structural frame stock is uncut and undrilled and selected
the kerf-right physical width from two 4×8 sheets, recorded in
`docs/bolted-candidate-owner-inputs.json`. Both kicker blanks in that packet
are 1/16 in narrower too. Physical receiving inspection and measurements
remain shop gates. Preliminary work may use a fresh-stock model without
treating the owner's report as a measured inspection. The eventual candidate
mechanical evidence must cover kerf-right; official-width cases do not transfer. Custom
steel, larger/doubled members, permanently wood-screwed detachable connectors,
or retained paired principal members require a specific decision at the
architecture gate.

## Baseline producer inventory

| Role | Path |
| --- | --- |
| Authority | `current-candidate.json` |
| Model | `mini_moonboard/compact_floor_flush_frame.py` |
| Viewer producer | `scripts/floor_flush_exports.py` |
| Construction producer | `scripts/floor_flush_construction.py` |
| Criteria/checks | `scripts/floor_flush_checks.py` |
| Official construction manifest | `docs/floor-flush-construction/manifest.json` |
| Official/kerf width adapter | `mini_moonboard/floor_flush_width.py` |

The exact baseline snapshot is recorded in
`docs/bolted-candidate-baseline-audit.json`; this plan is not a substitute for
the source hashes or for fresh native evidence.
