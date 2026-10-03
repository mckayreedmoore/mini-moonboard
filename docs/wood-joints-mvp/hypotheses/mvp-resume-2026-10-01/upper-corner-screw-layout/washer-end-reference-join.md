# Final ordinary washer-end reference join

## Finite scope

This new consumer joins the parent's frozen N10 `two-recovery-attempt01`
packet: 503 completed shaft states, one null shaft state, 1,006 finite washer
ends and two null ends. It consumes all 1,008 ordinary end rows and preserves
the 48 previously completed common-knee rows from
`washer-end-source-completion/attempt02` unchanged. The parent completed
`rawlocal/washer-end-reference-join/attempt01` with status
`FINITE_JOIN_WITH_TWO_NULL_ENDS`: a 1,056-row worksheet with 1,054 finite
own-end sources and two explicit nulls. The worker authenticated 349 source
pins and four output artifacts and confirmed exact record equality for the
48 reused common-knee rows. It did not execute the producer.

## Completed parent result

The join adds current matched nominal support to 48 ordinary rows and recovers
six central supported-ring static trials. All six trial fields are
compression-only under the declared identical-pressure and ductile-metal
assumptions. The maximum trial pressure is 0.9407981411 MPa, or 0.2183219745
of the conditional perpendicular-to-grain base reference, in `k12-right`.
The full central washer annulus and its unsupported crescent receive no credit.
This static trial does not establish elastic contact compatibility or actual
washer first yield.

| Returned same-state witness | Value |
| --- | --- |
| Peak axial tension | `k12-right`, `lumber_leg_bolt_right_2`, head on `base_side_right`: T = 887.6340026 N; own M = 7770.079567 Nmm |
| Peak own-end moment | Same case and bolt, nut on `lumber_leg_right`: M = 7770.079567 Nmm; T = 887.6340026 N |
| Peak eccentricity | `a1-rear`, `lumber_leg_bolt_left_2`, nut: 9.144669007 mm; T = 83.93393230 N; M = 767.5480294 Nmm |
| Maximum applicable bound rigid wood-pressure/reference ratio | `k12-right`, `knee_outer_right_side_2`, head on `knee_outer_right_spine`: 0.8187967191; T = 316.6720803 N; M = 1179.093383 Nmm |

The wood-pressure ratio applies where a nominal land, material reference and
declared rigid contact model are bound; it does not establish complete
resistance coverage of all 1,054 finite sources. Actual material and hardware,
fresh washer metal stress/flexure, loaded support and global frame feedback
remain explicit applicability limits. The actual top-side mean ratio remains
in its separate matched 5/16 packet.

| Completed artifact | SHA256 |
| --- | --- |
| `attempt01/receipt.json` | `8f8b06d4a90b6c9462fb5f21fa398e42582a7d9be337c1fb327324b42d035783` |
| `attempt01/washer-end-reference-join.json` | `3ab64baace0f8374071c28da13fa1cda7d8ac6d0cb347ee88078390cac02e10c` |
| `attempt01/washer-end-states.jsonl` | `b5e3160ec167ee9ef00cd7542a7701912ce43ab4db4673abbaa6291e8d0c717e` |
| Consumed producer snapshot | `0d41353ce6863d7723b13c9e160ae7c8c69cc7ddec0833f04a94bd2217ccfa5e` |

## Remaining two null ends

The remaining null is `a12-left` at
`wj04_g7/upper_g7_clearance_n86p9_reversed_rail_hypothesis/upper_rail_1`:

| End | Receiver | Source disposition |
| --- | --- | --- |
| Head | `wj04_upper_g7_crosscut_full_stock_cleat` | Local equilibrium did not converge within 150 iterations |
| Nut | `base_rail_service_upper_right` | Same unresolved shaft state |

The saved frame tie tension is zero for that state. Its local own-end moments
remain unknown, not zero. The join reports this finite partial result without
waiting for another recovery attempt or transferring acceptance from older
receipts. The preserved 150-iteration method stop is the final limit of this
bounded packet.

## Parent API and execution

Producer: [washer-end-reference-join.py](washer-end-reference-join.py).
Import is inert. The API is `build(output: Path)` with fixed frozen inputs.

```sh
uv run --no-sync python docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/upper-corner-screw-layout/washer-end-reference-join.py --output docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/upper-corner-screw-layout/rawlocal/washer-end-reference-join/attempt01
```

Use a fresh, unaliased immediate child of the specified raw folder. The parent
owns the call. It runs saved-source arithmetic only: no shaft, contact, plate,
frame, CAD, native mechanics, software test or review execution. Success means
the declared 1,006 finite and two null ordinary rows were joined faithfully;
it does not mean all mechanics or resistance checks passed.

The consumer reuses `join_row`, support normalization and the central ring
trial from the unchanged
[washer-end-source-completion.py](washer-end-source-completion.py), SHA256
`dbf242d54ae501c0bf8d4241447837dcf08e7e4d2d108703f43a2fc0e1c078c9`,
and its frozen N09 reader. It does not rerun the original common-knee traction
recovery or import a numerical solver.

## Identity, support and reference checks

Every ordinary end joins by case, physical axis, head/nut role and receiver.
The existing helper checks the common frame comparison and response identities,
fresh axial-force source and row, signed head-to-nut convention, own-seat datum,
moment magnitude, transverse moment and independent pressure-resultant balance.
Original support applicability remains in its original fields.

The completed generic 120-probe packet is reused for current nominal support
credit only where its physical end, annulus radii, current point and inward
normal match the recovered N10 end. New current-support and rigid-pressure
reference fields are separate from historical support flags. A supported ring
may identify the existing quarter-inch fine plate method as a candidate; no
plate stress or capacity is computed. The larger retained washer families do
not inherit quarter-inch or actual top-side results.

The central receiver retains its supported-ring static trial. That trial can
report a compression-only pressure field or an inadmissible affine field; it
does not establish elastic compatibility, first yield or an actual capacity.
The producer retains separate case/end witnesses for tension, own moment,
eccentricity and the applicable current rigid wood-pressure ratio, with the
same state's tension and moment beside each peak. The reused common-knee
pressure reference is included without modifying its source rows.

The completed actual top-side 5/16 washer support/mean packet is authenticated
and referenced separately. Its 48 demand rows and the 48 existing retail
quarter-inch plate rows are not appended to or confused with the ordinary
1,008-row population.

## Historical producer bindings

The final N10 receipt names the maintained bolt producer at its consumed hash.
This consumer authenticates that identity through the exact
`two-recovery-attempt01/producer.py.snapshot`, retaining an explicit record of
the original path, original hash and snapshot path. It also authenticates the
N01 `a007`, full-run `f5` and first-recovery `509` snapshots declared by the
final receipt. It does not edit a historical receipt, substitute a new source
hash inside one or rerun historical producers. Future changes to the maintained
bolt producer therefore do not impersonate the older consumed source.

## Frozen input receipts

All paths below are under the current `upper-corner-screw-layout/rawlocal/`
folder; artifact hashes and their source pins are authenticated before and
after the join.

| Input | SHA256 |
| --- | --- |
| `washer-end-source-completion/attempt02/receipt.json` | `d974544f39a670bde1d9a493754224b199fe10f5126fc266f9914101d5fcbe00` |
| `bolt-reference-completion/two-recovery-attempt01/receipt.json` | `353f5890dd8cccc8db5cbf29bd7f2daa1de8877e3031825343a807a47421aa22` |
| N10 final `summary.json` | `776f597ec63e31be4c45a87302f0d849222cc6f4346361dda6d2bf8df04c43b0` |
| `washer-land-completion/attempt01/receipt.json` | `7d541cef4b05b03a6d501243759dd1ea435eeb42be4ce2d71eda27cd9ea78679` |
| `washer-land-reference-completion/attempt01/receipt.json` | `0218731514788a808ea8cb313945fe1000cbf63b51c181c9415b366ab374a46a` |

Output contains the producer snapshot, joined JSONL, concise result JSON and
source/artifact receipt in an ignored raw folder. Existing packets, reviewed
geometry, source authority and all joint/release HOLD boundaries are preserved.
Ordinary first-order end equilibrium, a nominal support check and a conditional
rigid-pressure reference remain distinct from complete load transfer, washer
flexure, loaded contact, common-host compatibility and actual hardware strength.
