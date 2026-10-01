# Independent review: current duty-path topology graph, attempt 01

**Verdict: confirmed with scope limits.** The graph faithfully joins its frozen source identities and remains a topology inventory. It does not establish a mechanical path, solver model, force transfer, joint response, capacity, or acceptance.

The producer verifier (`python3 verify_packet.py --verify`) and its checksum file pass. I independently rehashed all 72 pinned inputs and checked the graph against the duty registry, current attachment topology, current manifest, exact 50-member STEP descriptor/files, complete contact graph, reviewed station classification, load cases, and load datums. The checks reconcile 24 former duties to 22 station identities, 92 candidate bolt axes, 12 retained frame-bolt arrangements, 66 Hillman axes (58 source-station retained and eight owner-moved), 100 current member-pair nodes, six distinct external case IDs, 895 graph nodes, and 2,168 edges. Every node and edge reference resolves.

The two outer side-chain stations each cross-reference two former duties; the shared station topology is not duplicated into independent connection patches. All candidate-axis receiver and pair links, retained-bolt member and pair records, Hillman panel/current-receiver records, and moved-axis identities match their source records. Every current member STEP identity and on-disk hash joins the member-solids descriptor and input manifest. The 100 pair nodes reproduce the source geometry observations and have endpoints in the current member set. Those geometry observations remain geometry only.

Both center-kicker routes resolve the four current center-kicker Hillman axes, candidate center-post bolts, cleat/header identities, and pair references. They also preserve two historical receiver names: `inner_kicker_backer_left` and `inner_kicker_backer_right`, referenced by two moved axes on each side. Those historical names are absent from the current 50-member STEP bundle. Future reporting should call them historical references only; their absence is not evidence of a current-member inventory defect and does not establish that force travels through them. The graph correctly labels both routes identity-only.

All 2,168 edges explicitly leave connection behavior, face ownership, solver mapping, force transfer, and response unresolved. The 520 modeled hardware-role nodes have null solver DOF IDs. The six distinct load case IDs join to the current hold datums and panel targets, while every response remains absent. The stale `interfaces.json` packet is pinned only to record the known WJ-03 scope boundary; its interface records do not contribute to this graph.

No review finding requires a geometry or axis change, and none was made. This review is limited to source-byte and identity joins; it does not independently reproduce CAD, validate contact measurements, run a native solver, or accept any joint or criterion. The machine-readable counts, joins, hashes, findings, and reporting limits are in `review-record.json`.

## Reproduction

From the producer packet directory, run `python3 verify_packet.py --verify` and `sha256sum -c SHA256SUMS`. The review also independently rehashed all source paths pinned by `source-pins.json`; its record identifies the producer packet and key source hashes.
