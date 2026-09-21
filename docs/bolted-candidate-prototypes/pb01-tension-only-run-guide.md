# PB01 no-preload axial sensitivity: targeted run guide

The bolted solid-wood corner block is called a `cleat` in historical code and
machine keys. The preserved PB01 archive used bilateral axial springs and is
historical only. Its negative axial actions are not physical no-preload bolt
compression demands. Do not relabel or reuse that archive as this sensitivity.

From the repository root, in a frozen checkout with the native solver available,
run these two separate cases with fresh output directories:

```sh
uv run python -m scripts.simple_pb01_hybrid_diagnostic_run a12-left \
  --variant quarter_short --tension-only-axial \
  --output fea/results/diagnostics/pb01-short-tension-a12-left
uv run python -m scripts.simple_pb01_hybrid_diagnostic_run k12-right \
  --variant quarter_short --tension-only-axial \
  --output fea/results/diagnostics/pb01-short-tension-k12-right
```

The switch makes each PB01 axial spring active only in tension, with zero
preload. All four axial states and the compression-only face contacts are
updated from solved displacements; each change triggers a new equilibrium
solve. Transverse PB01 springs and the other 23 legacy station proxies retain
their old behavior. Default runs remain bilateral. The source snapshot and
hash map in each output include the producer and solver; `diagnostic-scope.json`
records the selected law and case. Use the final `report.json` only if
`numerically_accepted`, `contact_active_set_converged`, and
`axial_tension_active_set_converged` are all true. Inspect `axial_tension`,
`bearings`, equilibrium gates, and per-cycle active names. A repeated set or
cycle limit is unresolved, even when its last force table looks plausible.
The `quarter_short` pose is regenerated from the maintained 152.4-mm
dimension record; the preserved `quarter` pose and archive remain 300 mm.

These are two targeted old-proxy hybrid sensitivities, not V4 same-case demand,
capacity, a six-case envelope, a bolt schedule, or drilling approval. The trial
stiffness and 2x2 face contact discretization remain provisional. No native
solve was run while adding this option.
