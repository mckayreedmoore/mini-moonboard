# Current station family classification — attempt 01

This append-only T04 packet classifies the reviewed
`led-clearance-2x6-runner-seated-blocks-v1` from frozen source geometry and
input metadata. It covers 22 current candidate connection stations, all 24
former duties, 92 candidate bolt axes, 12 retained frame-bolt axes, and all 66
Hillman panel/kicker axes. It does not modify the candidate, geometry,
criteria, load contracts, coordinator queue, or any prior evidence.

The 24 former duties resolve to 22 physical station groups because the two
outer duties on each side reference one shared six-axis chain. The packet
keeps those left and right chains separate. It also preserves axis-level
receiver sets, modeled receiver order, shaft/grip envelopes, finite or
separated CAD pair states, panel-screw receiver mappings, and member STEP
identities. “Modeled order” is not confirmed physical hardware installation.

Two source-supported geometry groupings are recorded at their limited scope:
the 15 common horizontal cleat solids and bore patterns, and the proper-rotation
pair of center-post cleats. These are block-geometry templates only. The prior
family map’s only exact whole-patch match remains
`clip_horizontal_bottom_right_1`. No mechanical representative is proposed:
the pinned loads do not provide station reactions, signed local demands, force
sharing, or response ranges. Other stations remain distinct where receiver
sections, contact areas, bolt orders, cleat geometry, or shared-chain topology
differ. The left and right center-principal blocks are retained as separate
singletons even though their blank dimensions match.

Grain comparisons are conditional source-frame scenarios. The packet records
the candidate-block longitudinal axes and the two transverse alternatives for
each block, plus source longitudinal axes and transverse alternatives for the
frame timbers. No delivered ring orientation, selected material frame,
panel layup, or element assignment is established. Axis-to-grain cosine
values are descriptive geometry only.

The six applied load cases remain panel forces and equivalent global wrenches.
The separate dead-load source lists 778 mass rows and a 25 kg accessory
allowance, but has no implemented solver DOF mapping or station demand. Contact
areas are CAD face measures; they do not establish active bearing, force
transfer, contact pressure, or capacity. Candidate bolt bodies are modeled
roles without a selected/received product or delivered engagement. The 12
retained arrangements still require current-candidate recheck. All 66 screw
rows preserve the Hillman 42605, 63.5 mm nominal purchase policy; eight
owner-moved axes are explicit, and no screw resistance or engagement is
inferred.

`interfaces.json` was inspected and hash-pinned only as a scope boundary. It
describes a WJ-03 mirrored-outer-node interface proposal whose records do not
reconcile to the current 50-member station inventory; none of its interfaces
is transferred here.

## Verification

From this directory, run:

```sh
python3 verify_packet.py --verify
sha256sum -c SHA256SUMS
```

The verifier checks every pinned input and all 50 current finished STEP file
hashes, deterministically reconstructs the classification, checks 24-to-22
duty/station reconciliation and all axis counts, and verifies packet hashes.
It reads source files only and performs no CAD mutation, mesh generation,
native solve, or acceptance update. Source pins are intentionally immutable;
if any input changes, create a new attempt rather than refreshing this one.

The next executable mechanics step is to bind every current member to the
complete solver body/element/DOF map, then freeze station contact and fastener
laws and extract signed local demands for the six applied cases plus the
separate distributed gravity scenarios. Only after those mappings and outputs
exist can candidate station response ranges or mechanical representative
families be evaluated. No T04 criterion or joint is accepted by this packet.
