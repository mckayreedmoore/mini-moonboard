# Independent A1 corner export audit

The parent checks the exact signed forces of all 338 mapped interfaces at
each of seven increments against the already authenticated A1 response.
This includes 334 native connection vectors, two released zero-action floor
groups and two active floor-tangent groups. Active floor vectors and their
rounding radii are independently summed from the two audited scalar channels,
which include the source-load correction. They are not inferred from an
uncorrected reference-node RF.

The audit also checks all six physical corner bolts, eight lateral planes
and six axial ties against the existing corner contract and verifies that
the twelve retained original arrangements remain separate. The frozen A1
report additionally binds its five-body balance records and the parent's
independent 50-body/global response audit. This checker adds an independent
exact-force/inventory audit; it does not recompute resistance or accept a joint.

Final report SHA-256:
`2b498383b319aeb31e74c3b329e0758330b8b39d0a8e1b4788437db06453bfce`.

Reproduce from the repository root:

```sh
python3 docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/current-corner-a1-parent-export-audit-attempt01/check.py
```

`audit.json` records the report, response and corner-contract hashes. The
response remains conditional on the recorded proxy-stiffness, zero-gap and
unverified no-slip support scenario. No historical pass is transferred.
