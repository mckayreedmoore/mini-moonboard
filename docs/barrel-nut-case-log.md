# Barrel-nut native case log

This log records native-solver attempts for the
`compact-floor-flush-bolted-development` candidate. It is an audit trail, not
an acceptance ledger. A run is retained as evidence only when its source
snapshot, inputs, convergence, inventories, equilibrium checks, and diagnostic
scope all pass the candidate acceptance guards.

## 22 September 2026 — A12 rear exploratory smoke

- Case: `a12-rear`
- Conditional stiffnesses: 1000 N/mm barrel axial, 500 N/mm barrel lateral,
  and 100 N/mm3 face-contact penalty
- Contact update: one pivot at a time
- Intended cycle cap: 100
- Disposition: **rejected exploratory attempt; artifacts removed**

The attempt was started only to exercise the new one-case runner. It used the
known-unqualified zero-clearance lateral law, proportional barrel-face cells,
full-section bevel surrogates, and uniform conditional stiffnesses. It was
interrupted after cycle 20 because the active set had not converged and the
producer source changed while the process was running. Panel displacement had
increased from 5.830 mm at cycle 0 to 5.881 mm at cycle 19. No final report was
produced. The incomplete generated solve tree was deleted so it cannot be
mistaken for authenticated evidence.

This attempt supplies no demand, capacity, serviceability, or strength result.
It must not seed an accepted retry. A future attempt starts from a fresh source
snapshot after the bevel geometry, contact cells, clearance law, stiffness
basis, and report guards meet the BN-4 entry gate.
