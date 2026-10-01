# Five source-bound SPRINGA frame inputs

This packet prepares the five canonical non-a12-rear cases from fresh `build_case` metadata with the explicit ring A, ratio 1, zero-gap, zero-accessory scenario. Each load map, source wrench ledger, global/body equilibrium source audit, geometry/material binding, carrier law inventory, and emitted deck CLOAD map is case-bound.

The same 200-row all-bearing exact-stick floor tangent branch is retained solely as an input diagnostic. It is conditional on every paired normal bearing at every response state. No a12-rear floor mask, load map, force response, or active state is reused for these cases; no per-case support mask is established here.

Prepared cases:

- `a12-forward`: `a12-forward/model.inp`, `a12-forward/model.json`, `a12-forward/audit.json`
- `a12-left`: `a12-left/model.inp`, `a12-left/model.json`, `a12-left/audit.json`
- `k12-right`: `k12-right/model.inp`, `k12-right/model.json`, `k12-right/audit.json`
- `k12-rear`: `k12-rear/model.inp`, `k12-rear/model.json`, `k12-rear/audit.json`
- `a1-rear`: `a1-rear/model.inp`, `a1-rear/model.json`, `a1-rear/audit.json`

No native solve, freeze, response ledger, or corner demands are included. Each case still requires its own compatible bearing mask and independent physical balance before response use.
