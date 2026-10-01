# Independent correctness review — ordinary-joint actuation map binding attempt01

Date: 2026-09-28  
Review result: **SOURCE BINDING CONFIRMED; NO SUBSTANTIVE MISMATCH FOUND**

## Scope

Reviewed the frozen packet at `ordinary-joint-actuation-map-binding-attempt01-2026-09-28/`, its exact A00–A03 map summary against the source-bound inventory and emitted nut-coupling input, and the cited records for the static timeout, known-answer scope, unresolved transient values, T02/T03 execution gates, and false/not-ready flags. This is a bounded source-binding and factual review. No packet source or engineering input was changed. This review does not evaluate or accept mechanics.

## Integrity and map binding

The packet `SHA256SUMS` passed from the packet directory. The packet `SOURCE-SHA256SUMS` passed from the repository root for all 47 listed source files. The source review inventory, `nut-coupling.json`, and `nut-coupling.inp` therefore match the packet’s frozen source pins.

The four draft map summaries match the pinned `current_A09_map_inventory.axes` records field-for-field for axis ID; shaft and nut carrier IDs; global head-to-nut axis; pivot; translation and rotation controls; fit rank and rigid-reproduction error; fit support size; terms per equation; all six dependent node:DOF rows; carrier body, set, node counts and source digest; and shaft source digest. I also parsed the 24 emitted `*EQUATION` cards in `nut-coupling.inp`: each card’s dependent node/DOF and term count match the pinned `nut-coupling.json` equation-card record, and all six rows for each axis match the draft.

| Map | Axis | Head-to-nut direction (global XYZ) | Pivot (mm) | Ref / rotation node | Support / terms per row | Six dependent node:DOF rows |
| --- | --- | --- | --- | --- | ---: | --- |
| A00 | rail 1 | `(-2.2026868862e-16, -0.6427876097, -0.7660444431)` | `(134.5, 1.1784560903, 410.8568890787)` | `116163 / 116164` | `251 / 754` | `61518:3, 61518:1, 60595:1, 57834:3, 59700:1, 61486:2` |
| A01 | rail 2 | `(0, -0.6427876097, -0.7660444431)` | `(134.5, -24.1010105327, 432.0688801977)` | `116165 / 116166` | `258 / 775` | `75714:2, 75714:1, 76786:1, 76786:3, 76671:1, 72989:3` |
| A02 | principal 1 | `(-1, -5.5067172156e-17, -4.4053737725e-16)` | `(48.918, 32.333128244, 473.655024602)` | `116167 / 116168` | `254 / 763` | `93511:3, 91282:2, 90409:2, 93193:1, 90606:3, 93908:1` |
| A03 | principal 2 | `(-1, 0, 8.8107475449e-16)` | `(48.918, 53.545119364, 498.934491225)` | `116169 / 116170` | `259 / 778` | `104120:3, 104774:2, 105674:2, 105030:1, 108657:1, 103937:3` |

This confirms the listed map identities and dependent rows, not cross-axis coefficient equivalence. The packet correctly leaves A01–A03 equivalence or separate qualification unresolved and does not transfer A00 qualification to them.

## Factual checks

- The referenced N+ deck is `*STATIC` with an amplitude from 0 to 1 and a 1.0 step-time endpoint. The execution record says `wallclock_timeout`, `901.047778` seconds elapsed, and return code `137`; the log reaches iteration 33 with contact-spring counts changing. The recorded DAT, 12D, and STA outputs are empty, and no accepted response is recorded. The packet correctly calls this a failed static pilot and carries none of its old closure/work gates into the proposed transient.
- The prior native known-answer result explicitly qualifies only A00/M03 for its small global-Y body-force dynamic history, timestep, and method configuration. It does not qualify A01–A03 or the proposed external-port N+ motion.
- The draft leaves the transient history, numerical balance/work/energy/momentum/rate limits, bore thresholds, map qualification route, case classification, and runtime/solver envelope `UNRESOLVED`. No transient acceptance values are silently inherited from the failed static pilot.
- T02 is described consistently as offline review/parent-audit complete, with production build and native capture coupon still unrun. Pinned runtime, fresh parent readiness, required authorization, and durable run-once tracking remain gates. Its stated scope is capture method only.
- T03 attempt07 is consistently described as an unrun static coupon. The ordinary-joint case remains waiting on T02/T03, a frozen input/history, fresh readiness/authorization, run-once tracking, and a serialized execution slot. A coupon pass is not represented as full-joint acceptance.
- The top-level `NOT_FREEZE_READY`, `native_execution=false`, `mechanical_acceptance=false`, `new_load_case_selected=false`, and `geometry_changed=false` fields agree with the draft’s unresolved decisions and execution state. The report makes no mechanics-acceptance claim.

## Low wording-precision note

The README calls the static amplitude a ramp “over one second.” The pinned deck establishes a unit `*STATIC` step-time interval, but this static step does not establish a physical one-second history. The packet otherwise clearly says this is not the proposed transient and does not use it as such. For precision, describe it as a ramp over the unit static step-time interval.

## Exact hashes

SHA-256 values checked or bound by this review:

- Packet `README.md`: `26e5e233daeabdb38105d1d14b53e97e7c48fae5de501f998b1ddefd098a2e2a`
- Packet `decision-draft.json`: `017dd90ddf0efc9ed0a96df4baa2be90fc971b45a667731684ebe16070d16aba`
- Packet `source-pins.json`: `df132bd2e591b112f5fbf3198d076c321ae66fe2d9c182357b7bc4a259792a6a`
- Packet `SHA256SUMS`: `eab3c5c661be1ba40d9ce6e81c89c25f43ef628ab05f183f778fa906b92bf34a`
- Packet `SOURCE-SHA256SUMS`: `493ad93e9859ed23b3ce8b56a51d0664b706f8757450b4242dbb4ac2daa24578`
- Pinned source-bound inventory: `0c8926b3f8d5dad0bfbe2f6ef4ec72ed3c5b66b8942860e57aa0740bb200b97b`
- Pinned `nut-coupling.inp`: `af5b36dce4e85b19a6a5b4805dd6b00259da88ccc1a849769642db2ecbf62903`
- Pinned `nut-coupling.json`: `568ade2437181bc8e9398f64a2818bbf8bd3f46a64dae9639bf363cb68bec960`
- Pinned static N+ deck: `e94220362d6a4925dc71089b855f84daa540eb477103628291b319b4a9728def`
- Pinned static execution record: `1af13ed1d6d1506f2b15cbf7cfe8ba784ddc27b2372de4b2d3888f172eff27a6`
- Pinned A00 known-answer results: `0b9b773e96c630c3c46e7efd47a546ad6adc8c81cce8212ad169b908294d5347`
- Pinned live status: `691f942be7826dd7b07d178a1ba237b5ce3d9b5e9afe8dc3f81ebcaba1b6d6cd`
- Pinned task queue: `3b913c06143ee59bc7012f4e814ada43a01f7954a9963324dfb93ac85b3873f4`
