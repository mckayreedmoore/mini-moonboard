# Slave contact-cell order control

This is an offline source control derived from the frozen
[`native_input_v3`](../native_input_v3/) deck. It reverses only the sequence of
the 95 named `SLAVE` `TRIA6` mesh records. Each record stays intact, including
its label, six-node connectivity and orientation. The 88 `MASTER` records,
`GROUP_MA`/`GROUP_NO` memberships, coordinates, `TETRA10` solids, `.comm`,
`.export`, material, support, displacement history and frozen thresholds are
preserved.

The control asks whether the observed curved-contact method-screen findings
depend on the order in which the slave cells are listed in the mesh. It does
not change geometry or repair the baseline result. Parent-reviewed attempt03
completed, but failed its frozen screen: see the
[candidate-check results](../../../../docs/wood-joints-mvp/hypotheses/code-aster-candidate-checks-2026-09-27/RESULTS.md)
and the [attempt03 all-state contact audit](../../../../docs/wood-joints-mvp/hypotheses/code-aster-candidate-checks-2026-09-27/curved-contact-attempt03/contact-audit.json).
That attempt found a 0.0384464 mm open-state `JEU` discrepancy against the
independent exact-TRIA6 gap oracle at +0.50 mm and RN-to-cut reaction
discrepancies of 10.02–26.82 N. A result from this control can show input-order
sensitivity for this crop; it cannot establish contact accuracy, joint
resistance or candidate acceptance.

Run the source-only preparation and audit with:

```sh
.venv/bin/python fea/code_aster_trial/curved_contact/cell_order_reversal_control/prepare_control.py
```

The script pins all five source hashes from `native_input_v3`, copies its
`.comm`, `.export`, `.mail`, generator and geometry oracle, then reverses the
95 contiguous slave-face lines. Its preflight proves the exact reversal and
checks that all other mesh lines and group memberships are unchanged. It also
verifies the copied `.comm`, `.export` and generator byte-for-byte and
confirms that the copied oracle differs only in the mesh hash and explicit
cell-order-control provenance. The full file hashes and the reversed record
label sequence are in [manifest.json](manifest.json).

The parent-prepared control ran in the same pinned Code_Aster 17.4.0 image as
attempt03, with the exact frozen `.comm`, `.export`, material, loads and support
conditions. The paired audit confirms the 95 slave record lines alone were
reversed. At INST 5, 6, 7 and 11, SCUT/MCUT reaction vectors change by at most
`5.13e-11 N`, and nodal displacements by at most `1.09e-13 mm`; the summed
nodal `RN` changes by `0.984`, `6.998`, `1.025` and `0.984 N`. Both orders
still fail the frozen RN-to-cut screen, with discrepancies of `10.0–26.8 N`
for the baseline and `10.95–33.69 N` for the reversed control. See the
[paired output audit](paired-result-comparison.json) and [control screen](parent-contact-order-control-screen.json).

This establishes order sensitivity of the reported curved nodal field, while
the cut forces and physical displacement remain invariant. It neither
identifies the full cause of the absolute RN mismatch nor qualifies this
contact method, pressure recovery or joint resistance. The parent owns the
remaining source-faithful residual replay and any further serialized native
execution.
