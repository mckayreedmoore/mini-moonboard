# Current six-case operator-reuse contract, attempt 01

This source-only comparison verifies that the six gravity/climber input cases
share the same physical elastic discretization and connector projection. It
joins `a12-rear` from the current single-case adapter with the other five
cases from the fresh six-case adapter. Their exact model and deck hashes are
listed in `source-pins.json` and are reconciled to the six records in the
pinned gravity decomposition.

The helper parses each emitted `model.inp`; it does not rely on model audit
status alone. It compares all physical node coordinates against the actual
deck records, C3D20 connectivity and ELSET ownership against the deck, and
checks that each physical node and solid element has one body owner. It also
parses the ordered material, elastic, orientation, and solid-section cards
from all six decks and the pinned C11 source deck. The 218-card ordered
sequence is identical across all seven decks: 50 `*MATERIAL`, 50 `*ELASTIC`,
50 `*ORIENTATION`, and 68 `*SOLID SECTION` cards.

The helper recursively expands the permanent MPCs after removing the 200
conditional floor-stick pivot equations, then builds normalized physical
coordinate rows for all 348 bilateral SPRING2 and 1,292 unilateral SPRINGA
source projections. The rows, laws, ownership, qghost bindings, permanent
MPCs, exact conditional floor equations, and normalized 200-row floor
reference inventory match across all six cases. The separate pinned floor
source remains a 200-by-800 matrix with 800 physical masters and rank 200.
Case-specific force corrections are excluded from the normalized floor
reference comparison.

The physical inventory is identical in every case: 12,549 solid nodes,
50 bodies, and 1,903 C3D20 elements. The actual deck coordinates differ from
their model JSON coordinates by at most `1e-10 mm` because the deck writer
rounds coordinate tokens; the six emitted decks agree with each other. Every
normalized source projection closes on physical translational coordinates.
The full per-case equality-group hashes and the ordered property-card content
are recorded in `identity-contract.json`.

This permits reuse of one source-defined pure elastic physical K and the same
linear kinematic projection for the six separate case load maps, if and when a
pinned export method produces that operator. This packet assembles no K or H.
All six physical nodal load maps are distinct and remain case-specific. Do not
reuse a response force, reaction, contact or unilateral active state, floor
bearing mask, equilibrium result, demand, utilization, or case pass.
Each case still needs its own compatible state and physical balance before
any response can be used.

Reproduce the comparison from the repository root:

```sh
uv run --no-sync python3 \
  docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/current-six-case-operator-reuse-contract-attempt01/produce.py \
  --verify
```

`--write` regenerates only this attempt's `identity-contract.json` and
`source-pins.json`. The check reads source files and hashes only; it runs no
solver and does not change geometry, model decks, native controls, or freezes.
