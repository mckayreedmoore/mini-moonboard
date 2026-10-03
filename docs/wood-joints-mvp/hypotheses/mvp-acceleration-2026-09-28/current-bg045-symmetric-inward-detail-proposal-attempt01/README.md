# BG045 symmetric inward detailing proposal

**Disposition:** conditional proposal for owner review; not an approved axis
change and not ready to implement. If source-backed code interpretation later
requires the two opposite block Y faces to meet the 25.4 mm comparator, the
published symmetric scenario moves axis 1 inward 5.4 mm and axis 2 inward
5.4 mm. It clears that arithmetic band at both block edges, while reducing the
Y pitch and creating a much smaller web to the neighboring BG003 bore.

The proposal reuses the existing axis-2-only screen for its both-face scenario,
BG045 finished-profile edge query, reviewed finished-feature register, and
newer exact current washer-wood support screen. No old producer, native solve,
geometry edit, or moved-BRep query was run. Source pin validation and the
replay below are read-only; `--write` writes only this packet's `proposal.json`.

| Geometry scenario | BG045 block edge distances, axis 1 (+Y) / axis 2 (−Y) | Y pitch | Known BG003 orthogonal-bore minimum web |
|---|---:|---:|---:|
| Current reviewed | 20 / 20 mm | 93.35 mm | 7.453 mm |
| Existing axis-2-only screen | 20 / 25.4 mm | 87.95 mm | 7.453 mm |
| Symmetric inward proposal | 25.4 / 25.4 mm | 82.55 mm | 2.053 mm |

The `4D = 25.4 mm` comparison remains conditional on the applicable bolt,
receiver, grain, and loaded-edge interpretation. The current applicability
packet says the 20.0-versus-25.4 mm deficit is valid arithmetic if the source
`−Y` block face is the required loaded edge in the relevant action state; it
does not settle that interpretation for the end-grain-axis block. A fixed
two-face 4D band is not treated as a universal NDS rule. The finished-profile
query also found that the current modeled planar faces leave the rectangular
20.0 mm block distances unchanged at the five sampled stations; it does not
query any moved geometry.

Both matched receiver bores must move together for each bolt. The source
finished-axis register currently matches axis 1 to `base_header/facet006` and
`knee_outer_left_inner_frame_block/facet010`, and axis 2 to
`base_header/facet014` and `knee_outer_left_inner_frame_block/facet009`; their
modeled radii are 3.75 mm at the existing centers. The proposal translates
both mating receivers by the same per-axis Y shift. No moved bore or through
axis has been generated or verified.

The newer washer packet supersedes the prior screen's missing-support-data
statement. It reports exact OCC support for the full catalog dimensional
annulus at all four current BG045 outer wood seats, with zero modeled tilt.
For the proposal, this packet reports only rectangular boundary and registered
circular-loop separation arithmetic over the published face register. With
the maximum catalog OD radius 9.5123 mm, the nearest block edge margin is
15.8877 mm at both seats; the header margins are 22.2377 mm for axis 1 and
15.8877 mm for axis 2. The minimum catalog opening radius 3.8989 mm exceeds
the modeled 3.75 mm bore radius by 0.1489 mm, and each moved washer ring has
69.2877 mm clearance to the other moved BG045 bore. The header's nearest
unmoved registered circular cut leaves more than 846 mm of this planar
envelope. These are translation scenarios, not relocated OCC/common or full
support proofs. Washer-to-wood support remains separate from head/nut-to-washer
metal contact, actual flatness, fit, and wood resistance.

The known neighboring feature consequence controls this proposal's geometry
screen: the BG045 axis 1 to BG003 orthogonal bore 2 modeled envelope web changes
from 7.4526 mm to 2.0526 mm. The prior ray screen identifies this as the
minimum pair under the symmetric scenario. This is a geometric clearance only;
it is not a splitting, strength, net-section, or cutting criterion. The
existing screen's ten `base_header` Hillman XY projections remain 85.85 mm and
118.5509 mm from axes 1 and 2, respectively. The source register retains all
66 panel/kicker screw axes and this proposal changes none; that ten-axis XY
projection does not establish 3D clearance, backing, or installation.

The proposal remains conditional on resolving the loaded-edge rule for actual
signed grain-relative actions, regenerating and reviewing both receiver
members with the paired bores, re-querying the four washer seats and all nearby
features, and recomputing load sharing on the changed geometry. A supported
complete-joint interaction and group splitting/net-section/shear-out method
also remain open. Existing loads cannot be transferred to relocated axes, and
the 2.0526 mm web is not a capacity check.

For comparison, retaining the current 93.35 mm bolt pitch while giving each
opposite block Y face 25.4 mm to its nearest bolt center takes 5.4 mm of added
width at each face: a 144.15 mm envelope instead of 133.35 mm. This is a
dimension-only sensitivity with the bolt centers unchanged. It is not a request
to enlarge the block or a checked alternative; the altered stock/envelope,
mating fit, washer support/access, and adjoining features would need their own
review.

The structured result and exact pins are in [`proposal.json`](proposal.json)
and [`source-pins.json`](source-pins.json). Replay the local calculation with:

```sh
python3 docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/current-bg045-symmetric-inward-detail-proposal-attempt01/produce.py --verify
```

The replay validates direct input hashes, inherited source-pin maps, reviewed
feature-register source pins, and byte-for-byte output. The proposal JSON SHA-256
is `ef6064e844f5737fdd6fdcb8e004910890cc73b4b6519da3380d81285e43aac4`.
