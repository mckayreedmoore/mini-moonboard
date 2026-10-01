# Selected-floor normal interval diagnostics

This packet classifies all 100 source floor-normal SPRINGA rows at all seven
printed increments for two already-terminal selected-floor responses. It is a
source-bound compatibility diagnosis for the proposed active/inactive masks.
Both parent terminal assessments remain rejected; this packet does not promote
their forces into corner demands.

The producer validates each case context, selected input/deck, adjacent freeze,
terminal execution, DAT hash, and parent terminal assessment. It uses the
pinned [zero-U response wrapper](../current-springa-zero-u-token-response-audit-attempt01/response_audit.py)
and stable parser. That method gives radius zero only to canonical all-zero
U tokens; nonzero U fields retain their printed-exponent half-last-place
radii, and every RF interval remains unchanged. The linked
[parser proof and fixture replay](../current-springa-zero-u-token-response-audit-attempt01/README.md)
records the CCX 2.23 formatting evidence and known-answer replays.

For each normal row the reports preserve the projected `q` interval, actual
endpoint-length elongation interval with the original subtraction guard,
nonlinear table-force interval, and both numerical endpoint RF component
intervals. `STRICT_POSITIVE_BEARING` requires strictly positive `q`, geometric
elongation, table-force, and projected endpoint-RF intervals, plus the
audited endpoint action/reaction check. `STRICTLY_SEPARATED` requires strictly
negative `q` and geometric elongation, an exactly zero table-force interval,
and endpoint RF component intervals containing zero. All other rows would be
reported as unresolved; none are unresolved in these two reports.

| Case | Proposed mask | Observed at each of 7 states | Stable mask mismatches |
|---|---:|---:|---:|
| K12 rear | 16 bearing / 84 inactive | 21 bearing / 79 separated | 6 inactive rows bear; selected `SPR1311` separates |
| A1 rear | 44 bearing / 56 inactive | 46 bearing / 54 separated | inactive `SPR1131` and `SPR1173` bear |

The detailed, source-grouped rows are in
[`k12-rear-normal-intervals.json`](k12-rear-normal-intervals.json) and
[`a1-rear-normal-intervals.json`](a1-rear-normal-intervals.json). The compact
cross-case register is
[`compatibility-exception-register.json`](compatibility-exception-register.json).
Each file carries source SHA-256 pins. The register lists the six additional
K12 bearing rows (`SPR1074`, `SPR1080`, `SPR1086`, `SPR1092`, `SPR1098`,
`SPR1260`), the selected-but-separated K12 row (`SPR1311`), and the two A1
inactive rows (`SPR1131`, `SPR1173`).

These are compatibility exceptions for the exact recorded input cases, not a
new floor mask, automatic floor iteration, equilibrium result for another
active set, physical failure finding, or accepted support configuration. The
producer does not export physical connector forces, body balance, corner bolt
demands, capacities, or joint acceptance. Its intervals describe printed DAT
representation and arithmetic guards; they do not bound solver residual,
convergence error, pre-format underflow, or the exact continuum solution.
There was no native run, freeze, ledger, geometry, or source-response edit in
this packet.

Reproduce the read-only diagnosis and regenerate only this packet's JSON files
with:

```sh
.venv/bin/python docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/current-springa-selected-floor-normal-interval-diagnostic-attempt01/produce.py
```
