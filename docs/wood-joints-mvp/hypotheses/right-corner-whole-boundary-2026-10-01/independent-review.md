# Independent review: complete right five-body source boundary

Reviewed October 1, 2026. I found no material calculation, source-join, or
claim-boundary issue in the frozen packet. I reviewed the producer
`produce.py` (SHA-256
`c4547fd3186aff6a59bac032428c42bbbc2e8e8e6f8a144559ad7bc2ffa422b7`),
`README.md` (`5c05b5216b0fe1ca4ec4f32aa4a8a4db7388012f5dd8c32e098722f9b9cfb77d`),
and `source-method-trace.md`
(`6ca5ec5e1ab1e8b89f8a41ba30942760eea449c497dc443b163fdc7b639e880c`). The
parent raw output used for comparison is local-only
`/tmp/mini-moonboard-right-corner-whole-boundary-2026-10-01.json`, SHA-256
`56463f3c6a49a89cf937fe95eced068b4938de4cdf42d66ca487b63a67057f0f`.

## Source selection and floor handling

The producer's five-body set is `base_header`, `base_post_outer_right`,
`base_side_right`, `knee_outer_right_spine`, and
`knee_outer_right_inner_frame_block`. I independently grouped each frozen
model's `raw_source_carrier_law_inventory_rows` by source name and selected
every owner with either endpoint in that set. All three models yield 338
physical interfaces from 392 scalar carrier rows: 42 interfaces internal to
the set and 296 crossing its boundary. The grouped owners match each model's
`connection_ownership` records. Across all 21 increments, every direct
response action maps back to exactly the scalar source inventory indices for
its group; the 334 direct action groups cover 384 scalar rows, and the four
floor tangent groups supply the remaining eight rows through their separate
two-channel records.

I verified the floor tangent selection by group and local DOF. In all seven
A1 and A12 states, tangent groups 1 and 3 are selected, while groups 0 and 2
are released. In all seven K12 states, all four groups are released. Each
selected group has exactly DOFs 2 and 3 and retains its saved endpoint forces
and rounding radii. Each released group retains both zero-action channels,
zero force/radius, the absent native tangent equation/spring flags, and a
carryover RF interval containing zero. The generic helper supplies the
released channels' direction from the pinned owner basis. The four distinct
`floor_normal` connections remain separate; the released tangent rows are
not counted as forces or silently omitted.

I checked the freeze hash
`d4ba1c78eb358d25e32819201e9c59e05d425a06d9e4e5cca3dc09d7139ffd73` and
rehashed every case model, deck, native DAT, response, all-body audit, and
terminal file against the parent raw manifest. All matched. The pinned right
join method is `13989f42845210caadb15c1cf3903a47c2634b866195dc0c5f2156ea9605f2ea`;
the reused generic exporter helper is
`0e6aa1b0ec50e3137d2f431f79365de899d109a5d5c61d37de344c9596681fe8`. Both
hashes match the producer's enforced loader pins.

## Independent boundary and load replay

Without running the producer, I rebuilt the 338 grouped endpoint actions from
the frozen model and response records. I used the five source descriptor
midpoints as reporting datums, summed each incident endpoint force and point
moment, and separately summed each body's source nodal loads scaled by its
increment factor. I recomputed force-rounding radii and the corresponding
moment radii at those fixed coordinates. For all 105 body/state checks, the
reconstructed residuals and radii agree with the pinned all-body audit within
`1e-8 N` and `1e-6 Nmm`; the raw audit's printed and interval gates are true.
Those retained body residual maxima are approximately `0.000218 N` and
`0.295190104 Nmm`.

I also independently regrouped the 296 crossing interfaces into the 62
member/external-receiver/role ports for every increment. Their global-origin
force/couple sums agree with the raw packet. Internal pairs cancel, and the
sum of boundary actions, external loads, and internal cancellation matches
the five source body residuals transported to the origin across all 21
states. The independent component comparisons were within `1e-7 N` and
`1e-7 Nmm`. These are arithmetic comparisons, not new equilibrium gates.

## Claim boundary and validation

The README describes this accurately as the complete **modeled source
interface boundary of the selected five bodies**, not the whole frame, a
finished-section solution, or a resistance result. It distinguishes the
diagnostic selected/released no-slip floor branch from proof of floor friction
or anchorage. The three A1/A12/K12 rear response histories remain conditional;
they do not establish the gravity/event history or a six-case demand
envelope. No force matching here qualifies timber, fasteners, washers,
sections, combined interaction, criterion pass, joint acceptance, inspection,
fabrication, or climbing release. DAT files are pinned but not independently
parsed for RF tokens, and no native solve was run.

The parent reports that `produce.py --check` exited zero and Ruff passed. I
did not rerun either command. My verification was a separate read-only source
endpoint reconstruction; it did not alter model/evidence files or launch a
solver.

One nonblocking provenance detail: the output records `producer_sha256` by
hashing the executing file, but the producer does not assert that digest
against a built-in expected value. The reviewed code digest is therefore an
external review/publication pin; the reusable source methods and frozen
inputs are checked at runtime. This does not change the reviewed output,
whose recorded producer hash matches the code hash above.
