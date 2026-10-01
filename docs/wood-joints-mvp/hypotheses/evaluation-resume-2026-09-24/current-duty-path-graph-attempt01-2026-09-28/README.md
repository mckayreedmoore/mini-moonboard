# Current duty-path topology graph — attempt 01

This append-only T04 packet records source-bound member, contact-pair, and fastener-axis identities for `led-clearance-2x6-runner-seated-blocks-v1`. It is a topology inventory, not a qualified mechanical path model. The T04 queue remains active and its path/equivalence exit gate remains open.

The deterministic graph covers **24 former duties, 22 reviewed physical stations, 92 candidate bolt axes, 12 retained frame-bolt arrangements, 66 Hillman panel/kicker axes, 50 current member STEP identities, 895 graph nodes, 2168 graph edges, and both center-kicker routes**. It includes `72` source pins, including all 50 current STEP files. See `source-pins.json` for the exact paths, byte counts, and hashes; `duty-path-graph.json` contains the complete machine-readable crosswalk.

## What the sources establish

- The current duty registry and attachment topology identify all 24 former duties and connect them to 22 source-reviewed physical station identities. The two outer-side chains each serve two former duties; that shared topology remains one chain and is not represented as two independent patches.
- The current manifest and topology identify the 92 candidate bolt axes, their modeled raw-wood receiver intervals, the 12 retained bolt arrangements and their recorded members, and the 66 Hillman axes with current panel/receiver assignments. The source inventory records 58 retained Hillman axes and 8 owner-moved axes.
- The current STEP bundle supplies exact identities for 50 members. Referenced pair records are joined to the complete current member-pair geometry graph. Finite opposed planar touch, separated geometry, and reported areas remain CAD geometry observations only.
- The two center-kicker records show the current Hillman axes at `kicker_left/right` to `base_post_center_left/right`, followed by candidate center-post bolt identities to the center-post cleat and candidate header bolt identities to `base_header`. The two previous inner-kicker backer receiver member names (used by four axes) are historical references absent from the current 50-member STEP set.
- Six external load cases identify their hold-panel targets. The dead-load contract and current mass topology map provide modeled input identities. Neither source supplies a current station response or a solver DOF assignment.

## What remains unknown

Every graph edge carries explicit unknowns for behavior, face ownership, solver mapping, force transfer, and response. The graph does not establish active contact, face normals/ownership, connection stiffness/capacity, bolt or screw engagement, physical head-to-nut order, selected grain orientation, station demands, reactions, response ranges, or mechanical equivalence. Modeled hardware role rows have no solver DOF mapping; no graph edge means force can pass between its endpoints.

`interfaces.json` is pinned only as the known stale WJ-03 scope boundary from the prior T04 packet. Its interface records were excluded from graph derivation. The prior station-family classification and independent review are pinned; their geometry-only groupings are not elevated into representative mechanical families here.

## Model changes and next executable action

This inventory identifies **no required geometry or axis change**, and makes none. Before mechanics work, the coordinator must map the frozen 50 member STEP identities and modeled hardware roles into the chosen solver, assign persistent contact/face ownership and material/grain/hardware behavior, and validate how the six load contracts and dead load reach signed station actions. Any changed model is a separate reviewed input and requires a fresh pin set; no solver run is performed by this packet.

Run from this directory:

```sh
python3 verify_packet.py --verify
sha256sum -c SHA256SUMS
```

The verifier reconstructs the graph from its pinned sources and rejects changed inputs, missing axes/pairs, dangling edges, or checksum drift. Packet verification checks bytes and identity joins; it does not validate a mechanical model.
