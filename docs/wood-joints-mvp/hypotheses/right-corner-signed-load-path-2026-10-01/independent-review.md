# Independent review: right-corner signed load path

Reviewed October 1, 2026. I reviewed the terminal producer
`produce.py` (SHA-256
`13989f42845210caadb15c1cf3903a47c2634b866195dc0c5f2156ea9605f2ea`),
`source-trace.md` (`c5569b42f3b57bab8249cbc6dbf099ab1252225a91bf3948ffe84c3deca76481`),
and `README.md`
(`7ecaf13f81e0ed906a17454d134f5c78c2d1ab5ec7adea44248d0c120c4f6312`).
The parent raw result used for comparison was local-only
`/tmp/mini-moonboard-right-corner-parent-2026-10-01.json`, SHA-256
`48b68ab78d24febd79cb2e12bbec761209c6c1ac6fffa24075c22bbbcac12cbf`.
I found no material code or claim issue.

## Source and scope check

The source trace pins the ignored three-case freeze
(`freeze.json`, SHA-256
`d4ba1c78eb358d25e32819201e9c59e05d425a06d9e4e5cca3dc09d7139ffd73`).
It selects only A1-rear, A12-rear, and K12-rear, whose response hashes are
`257b5b743369fcc2242537b7ccfe81f2efba0a195ef044624d7b67da6a09678c`,
`892dadeed0b20d809ce5250d3cd1c3deb31697f69208d8bbefb5f702160e1274`, and
`42ffb135d47bd3bd28874e886682b4f07175ee060fb383b6e3c128e5102073c6`.
Each has seven accepted conditional response increments. The same freeze
pins the source models, decks, DATs, all-body audits and terminal records.
This is three-case coverage, not a six-case envelope.

I confirmed the six selected right axes and exact plane mapping: header 1/2
use planes 41/42, post 1/2 use 43/44, and side 1/2 use planes 45/46 and
47/48. Each state has six separate axial ties and eight lateral planes. The
two right-side axes remain continuous through
`knee_outer_right_spine` → `base_side_right` →
`knee_outer_right_inner_frame_block`; their ties connect only the outer
receivers and the middle member gets its two interface-plane actions. The
producer neither inserts a middle washer nor transfers left-corner forces,
capacities, or acceptance.

The source guards are meaningful for this bounded join. The code pins the
shared acceptance/geometry method, freeze and each case file; checks
candidate/revision/case identity and all-body raw and interval balance; and
requires source response gates. Each SPRING2 plane is joined to its source
inventory, element, bilateral law, DOFs 2 and 3, endpoint RF signs and
rounding radii. The reconstructed global force from the two local RF
components and recorded basis must match the exported first/second receiver
actions. Each SPRINGA tie is checked by the shared signed-tie function against
its source binding, tension-only RF gate, installation direction, named
outer receivers and geometry seat points. Receiver-plane order and station
are also checked against the pinned source geometry.

The producer pins native DAT files but does not independently parse their RF
tokens; it states this boundary in `claim_limits`. It cross-checks the
recovered component records in the pinned response JSON against each plane
vector. The result therefore does not claim an independent native-token
recovery. Its reference is the source model's head-seat point, not an
inspection of delivered hardware, washer contact, or actual seat flatness.
The propagated radii are source RF-token precision at fixed coordinates;
they are not fabrication or physical tolerances.

## Independent numeric replay

I independently replayed the three response JSONs without rerunning the
producer. For every one of the 21 states, I joined the six ties and eight
planes by source axis and receiver, retained the signed force on each named
endpoint, and computed each receiver wrench about the tie's fixed modeled
head-seat point:

`F = Σ Fᵢ`, `M = Σ ((pᵢ − p_head-seat) × Fᵢ)`.

I independently summed the force-component and couple-component rounding
radii at those same fixed points. The replay covered 126 bolt states, 168
plane states, and 294 receiver wrenches. Every force, moment and radius
component matched the frozen parent JSON exactly at the serialized values
(maximum component difference `0`). The K12-rear full-load result for
`knee_outer_right_side_1` on middle receiver `base_side_right` is
`F = (0, 281.455314, −444.268160) N` and
`M = (0, −22584.938320, −10420.708648) Nmm` about the modeled head-seat
datum. This is a receiver wrench transported to a common point; it is not an
internal bolt bending moment or a bound on steel stress.

The existing attempt04 case-register, three-case axial-seat register,
signed-plane register, bolt-group inventory, and three-member receiver-order
verifiers passed in read-only mode. The producer README records the parent
`--check`, rejection fixtures, and Ruff results; I did not rerun those
commands or any native solve. The review supports only the source-join and
internal bookkeeping result. Full-body boundary transfer, member sections,
resistance, combined interaction, six-case acceptance, and joint acceptance
remain outside this packet.
