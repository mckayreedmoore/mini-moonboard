# A12 raw-H row 1586 endpoint recovery runner

This packet prepares a parent-only recovery of the two physical endpoint
fields owned by `left_service_inner_lower_cleat` (60 DOFs) and
`base_rail_service_lower_left` (276 DOFs) for raw-H source row 1586
(`SPR1787`, element 3690). It does not recover either endpoint from the real
stiffness matrix. The raw-H source comparison remains
`STOP_PHYSICAL_OR_SOURCE_COMPARISON_GATE` with all 27 force-interval failures.

The runner reconstructs each exact body rigid basis from the pinned source
mesh-node order and coordinates. It rebuilds the physical projection `B` from
the projection contract and checks `B*R` against the pinned `D`; both target
bodies match exactly. It reconstructs the unchanged A12 rear body loads as
`p = gravity + climber - B.T*f_full`, checks the original all-50-body
component gate, and checks each target load's unmodified `R.T*p` quotient
balance. The current source-only replay confirms 20/92 physical nodes and
60/276 DOFs, with both raw loads inside the existing quotient balance gate.

After a parent reviews and authorizes this exact runner, its sole source mode
will checksum the original `model.sti`, stream its one-based sparse upper
triangle once, and retain only the two selected body blocks. Absent pairs are
valid structural zeros. The parser checks the pinned global count of
2,320,506 unique pairs, 1,051 explicit zero pairs, reconstructed symmetric
nonzero count of 4,601,263, all 37,647 diagonals, exact `.dof` owner/order,
and zero cross-body nonzero pairs. It checks block symmetry and positive
diagonals and records each target block's observed sparse pair count and CSR
digest. Those per-body pair counts are observations from the authorized
stream, not frozen prior expectations. The parser does not build a global
stiffness matrix.

For each body, the runner uses the frozen elastic-quotient and bordered
condensation methods with unmodified `K_b`, `R_b`, and `p_b`. It allows at
most one KKT factorization per body and five existing-method refinement
corrections per body, and stops on the first failed method gate. It then
forms `u_full = u_elastic + R*a` from the saved raw-H rigid-coordinate slice,
evaluates every dependent emitted MPC DOF in the original equation order, and
keeps the exact `B*u` linear projection distinct from original-coordinate
binary64 `dd - dd0` and the emitted SPRINGA table force. Source method success
and comparison to row 1586's unchanged native RF interval are separate
results. A match would not clear the original 27-force STOP or constitute
mechanical acceptance.

The `--verify-preparation` and `--toy-check` modes hash-check the original
`.sti` bytes and the pinned CalculiX 2.23 source archive but do not parse any
stiffness triplets. The archive-member checks pin `springforc_n2f.f` and
`calcspringforc.f`, including the `dd - dd0` displacement and force-table
interpolation sequence used for the SPRINGA endpoint force. The toy mode factors one
small synthetic matrix and checks recovered elastic and physical fields,
recursive MPC endpoint vectors, `B*u` back-projection, finite-span/table
force, sparse selected-block extraction, symmetry, omitted structural zeros,
duplicate and wrong-owner refusal, and cross-body rejection. It performs no
source-K factorization, source body solve, or native run. `output-pin.json`
records the runner, source manifest, and external receipt hashes.

Reproduce the saved source-only and synthetic checks with:

```sh
.venv/bin/python -B docs/wood-joints-mvp/hypotheses/a12-row1586-endpoint-recovery-2026-10-01-attempt01/runner.py --verify-preparation --report /tmp/mini-moonboard-a12-row1586-endpoint-recovery-preparation.json
.venv/bin/python -B docs/wood-joints-mvp/hypotheses/a12-row1586-endpoint-recovery-2026-10-01-attempt01/runner.py --toy-check --report /tmp/mini-moonboard-a12-row1586-endpoint-recovery-toy.json
.venv/bin/ruff check docs/wood-joints-mvp/hypotheses/a12-row1586-endpoint-recovery-2026-10-01-attempt01/runner.py
```

The preceding preflight readiness report has SHA-256
`edcc2fbc8adddfab44e8419db8b297df4c8f6f6a11e905523d1bcb60102d84f7`. The
current runner SHA-256 is
`4e0b1b3892b2a8036ec5ed73f18ea8c228afdc4614c2d009349b186c25a26202`; the
22-input source manifest SHA-256 is
`187fda0ceb9c93d282d1697367aa95ee57b3e205f32fcbbe1ebc6abb644b290e`. The
CalculiX source archive is pinned at
`9c88385c10fb04f5dc6c4e98027a51bebdd8aee3920e05190d6c1dd08357d6e7`; the
runner verifies exact member hashes for `springforc_n2f.f` and
`calcspringforc.f`.
`source-pins.json` contains the exact hashes, including the original stiffness
and DOF files, raw-H response, A12 source model/load maps, physical projection
and ownership map, attempt04 method inputs, emitted deck and native response.

The actual-source CLI refuses to start without an external parent approval
JSON matching all of these exact fields:

```json
{
  "schema": "a12_row1586_endpoint_recovery_parent_approval/v1",
  "approved": true,
  "preparation_readiness_sha256": "edcc2fbc8adddfab44e8419db8b297df4c8f6f6a11e905523d1bcb60102d84f7",
  "runner_sha256": "4e0b1b3892b2a8036ec5ed73f18ea8c228afdc4614c2d009349b186c25a26202",
  "source_pin_manifest_sha256": "187fda0ceb9c93d282d1697367aa95ee57b3e205f32fcbbe1ebc6abb644b290e",
  "scope": "two_target_bodies_row_1586_only"
}
```

No such approval was supplied or consumed here. A refusal check of
`--execute` without `--parent-approval` exited 2 before the recovery runner
was called, and the one-shot marker remained absent. On a later authorized
run, `--execute --parent-approval PATH --report /tmp/REPORT.json` is bounded
to 60 seconds CPU, 60 seconds wall time, 2 GiB address space, one parent run,
two body factorizations maximum, and five method corrections per body. The
one-shot marker is created outside the repository. No correction, gate or
interval change, new state, force adoption, native execution, or physical or
design acceptance is part of this packet.
