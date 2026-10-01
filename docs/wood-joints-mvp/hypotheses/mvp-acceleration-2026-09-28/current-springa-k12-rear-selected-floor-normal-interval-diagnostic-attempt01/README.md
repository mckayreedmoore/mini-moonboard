# K12-rear attempt02 normal-interval diagnosis

This packet replays the pinned K12-rear attempt02 DAT through the current
zero-U token interval method. It classifies all 100 source floor-normal
SPRINGA rows at all seven printed load factors (0.1, 0.2, 0.3, 0.45, 0.675,
0.925, and 1.0). The source input proposed 21 active and 79 released floor
cells. The observed strict-positive set is stable at 23 cells for all seven
states; the remaining 77 are strictly separated, with no unresolved
classification.

The strict rejection is a stable active/inactive branch mismatch, not an
interval ambiguity. Two proposed inactive rows bear strictly at every printed
state: `SPR1104` (`floor_base_floor_left_27`) and `SPR1110`
(`floor_base_floor_left_29`). The parent strict auditor reports the first as
the rejection trigger, `SPR1104`. No proposed active cell separates.

For `SPR1104`, the projected-q interval stays positive from
`[5.7613915e-7, 5.7613925e-7] mm` at load factor 0.1 to
`[5.7613905e-6, 5.7613915e-6] mm` at load factor 1.0. Its geometric
elongation interval stays positive from
`[5.76138795076455e-7, 5.761396056191949e-7] mm` to
`[5.761390139236176e-6, 5.7613918497789535e-6] mm`. The nonlinear table-force
interval stays positive from `[0.10488171780167883, 0.10488186535486506] N`
to `[1.048817576411525, 1.048817887802923] N`. At full load, the q-endpoint
RF z interval is `[1.0488175, 1.0488185] N`; the numerical ground RF z
interval is `[-1.0488185, -1.0488175] N`. The same-direction signs and
strictly positive q, geometric, and force intervals persist at all seven
states. These are numerical constitutive endpoint records, not physical floor
reactions.

`SPR1110` independently has positive q and geometric intervals at all seven
states: its q interval ranges from `[3.5408485e-7, 3.5408495e-7] mm` to
`[3.5408485e-6, 3.5408495e-6] mm`, and its table-force interval ranges from
`[0.06445840959001753, 0.06445855714320343] N` to
`[0.644584670209471, 0.644584981600866] N`.

The complete 700 row classifications and exact intervals are in
[`k12-rear-normal-intervals.json`](k12-rear-normal-intervals.json). The
producer pins the original attempt02 model, deck, DAT, execution, freeze,
authorization, case context, parent serialized-input audit, context check,
readiness review, terminal assessment, native logs, response auditor/writer,
and interval method. [`source-pins.json`](source-pins.json) records the
producer and report hashes plus all bound source hashes.

This diagnosis does not accept the proposed floor branch, provide a response
for a different contact set, export physical connector forces or corner
demands, or infer physical failure. It makes no new floor mask and does not
authorize another native run or automatic iteration. It makes no mechanical
or joint acceptance claim.

Reproduce the read-only interval replay with:

```sh
.venv/bin/python docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/current-springa-k12-rear-selected-floor-normal-interval-diagnostic-attempt01/produce.py
```
