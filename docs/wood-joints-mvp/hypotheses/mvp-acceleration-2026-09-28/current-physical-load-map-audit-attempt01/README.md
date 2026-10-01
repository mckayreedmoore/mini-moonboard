# Physical load-map audit and preserved label correction

The connector projection packet's preserved `source-gravity-nodal-map.json` is a faithful copy of the A12 adapter's `physical_body_loads`, but that source field contains **combined gravity and climber loads**. Its filename and gravity-only description are incorrect. No previously frozen input or evidence is rewritten here.

The mislabeled map has resultant approximately `(0, +300, -4424.926817) N`. The separately verified source decomposition has gravity `(0, 0, -2200.816010) N` and the A12 rear climber load `(0, +300, -2224.110808) N`. The latter two maps sum to the former at every source node.

This audit independently compares all six separated nodal pairs with their actual adapter `physical_body_loads`, checks unique body ownership and physical coordinate coverage, and retains each source/hash and maximum arithmetic discrepancy. Use the six-case [source-load-maps.json](../current-frame-pure-solid-matrix-export-preflight-attempt01/source-load-maps.json) fields `gravity_nodal_map` and `climber_nodal_map` for staged calculations. Gravity settling is `beta*gravity_nodal_map`; climber ramp is `gravity_nodal_map + alpha*climber_nodal_map`. The combined map must not be used as gravity alone.

The unloaded native stiffness export contains no loads and is unaffected. Connector projection rows and six-case operator identity are unchanged. This correction supplies source load semantics, not a physical self-weight distribution, contact state or frame acceptance.

Replay from repository root:

```sh
OPENBLAS_NUM_THREADS=1 .venv/bin/python docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/current-physical-load-map-audit-attempt01/audit.py --verify
```

Audit SHA-256: `eb9d23d996f7d877edea9607e98501b080dc95e8bc888a55c0a43e01de861052`.
