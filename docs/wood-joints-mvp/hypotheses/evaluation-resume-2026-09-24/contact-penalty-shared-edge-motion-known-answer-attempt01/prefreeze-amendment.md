# Pre-freeze preparation amendment — 2026-09-27

This amendment records a static-preparation audit before any input freeze or
native execution. It does not change the fixture's reviewed 2 mm cube
geometry, material, penalty law, support/gauge pattern, contact-role patterns,
affine endpoint, numerical gates, or serialized deck bytes.

The initial producer (`prepare.py` SHA-256
`353cb20375fd7d0d23f82b99e9fd8dc8fd581a25e9bc44be98182b38ae5630b8`)
was replaced by the exclusive writer and static-audit producer
(`prepare.py` SHA-256
`a6dc236cda3cbe16f4a2ebe5e560ea27ab3a7e9059f662b2912c74cab8e4d3fb`). The
final producer now refuses to overwrite any generated packet artifact, checks
all output paths before writing, and opens outputs exclusively. `--check`
only regenerates in memory and compares bytes.

The amendment also adds: (1) six-node C3D10 face-sextet matching for both
coincident contact interfaces; (2) parsing and auditing of the serialized
`*EQUATION` cards, including the affine residual, both map identities,
deterministic q reconstruction and virtual-work identity; (3) explicit
per-pair CF/CFN/CFS force and origin-moment oracles with a dimensioned
`0.041 Nmm = 0.01×4 N×1 mm + 0.001 Nmm` tolerance; and (4) generator and
preflight hash cross-links in the source/readiness records.

The one authorized regeneration was limited to the six producer-generated
files: the two motion decks, `expected.json`, `source-snapshot.json`,
`preflight.json` and `readiness.json`. The deck bytes remained identical:

| Input | SHA-256 before and after |
| --- | --- |
| `input/shared_slave_motion.inp` | `804f43cc32319d7d89c81b784859b90a9b78542d972987fbc35ec1bb290ecafe` |
| `input/cross_role_motion.inp` | `d63a7090379b8c7b93e1e2c4eeeedf7bfc49b2741a04e7f988ac00e1cc6f1234` |

No native job, input freeze, execution record, or parent readiness decision
was created by this amendment.

## Output-only correction — 2026-09-27

Before freeze or execution, pinned CalculiX 2.23 source inspection found two
output-selection issues. In `noelfiles.f` (archive member SHA-256
`ed85b45d6987882e484f11a0be3dc9c2d716afba07d59483d364e0709107a59f`), the
later `*NODE FILE,NSET=PORT_CONTROLS` changes the shared U-field NSET selector;
it would replace physical-node U coverage, while RF retains the earlier
physical-node selection. The deck now has a single physical `NODE FILE U,RF`
request. Controller U remains in `NODE PRINT` for DAT, and the verifier
reconstructs each port's q from physical cap U rather than requiring
controller FRD rows.

The requested SOF section reports also need nodal stress values. Pinned
`printoutface.f` (SHA-256
`e39d508e431c5ad29556594f7bf82753a8729a836ecf67ebd24a872212f13cbc`, lines
421–504) integrates the stresses extrapolated to face nodes. The deck now adds
`*EL FILE,FREQUENCY=1 / S` for the full physical mesh. `sectionprints.f` is
also pinned in the regenerated source snapshot. The verifier will require the
finite section force and origin-moment reports. These source checks support
the output contract and SOF's bulk-stress interpretation only.

The two deck inputs before this output-only correction were:

| Input | Previous SHA-256 |
| --- | --- |
| `input/shared_slave_motion.inp` | `804f43cc32319d7d89c81b784859b90a9b78542d972987fbc35ec1bb290ecafe` |
| `input/cross_role_motion.inp` | `d63a7090379b8c7b93e1e2c4eeeedf7bfc49b2741a04e7f988ac00e1cc6f1234` |

The generated decks and linked expected, source-snapshot, preflight and
readiness records were regenerated once under the parent's pre-freeze
authorization. No geometry, support, map, contact, loading, oracle or
tolerance was changed. The regenerated deck hashes are recorded in
`expected.json` and `readiness.json`. This packet remains unfrozen and no
native execution was started.

The regenerated output-only producer is `prepare.py` SHA-256
`59c512ab53a5f3f73c1d058e6e2ce67bc75de7f75f979c100e4c1e54b2b37dc2`.
The final regenerated input hashes are:

| Input | Final SHA-256 |
| --- | --- |
| `input/shared_slave_motion.inp` | `2399e3a48580579c410a2899401ec491ce4793c305c9e1b9b7a2717f6d010608` |
| `input/cross_role_motion.inp` | `9e428df69be83c95567ea95439cb3afba7736609d563ece192239f0fb12dbf2d` |
