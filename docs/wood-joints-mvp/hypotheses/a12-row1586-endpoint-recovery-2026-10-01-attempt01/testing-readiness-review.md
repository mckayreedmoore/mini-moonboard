# Independent testing and readiness review

Reviewed `parent-input-freeze-02.json` at SHA-256
`a4f0ba75a5a3d46b047880ea4b6feae7df40470be1ca921ef78da398261b537a`, runner
SHA-256 `4e0b1b3892b2a8036ec5ed73f18ea8c228afdc4614c2d009349b186c25a26202`,
and the frozen 22-input manifest at SHA-256
`187fda0ceb9c93d282d1697367aa95ee57b3e205f32fcbbe1ebc6abb644b290e`.

**Disposition: technically ready for the parent’s separate one-shot launch
decision, with the process-bound conditions below. This review does not
authorize that launch.** The freeze explicitly records
`parent_launch_authorized: false`. No source `.sti` triplets were parsed, no
source stiffness was factored, no source endpoint state was recovered, and no
native run was made here. The original raw-H disposition remains
`STOP_PHYSICAL_OR_SOURCE_COMPARISON_GATE` with all 27 force-interval failures.

## Checks and coverage

I ran the runner’s `--toy-check` to an external `/tmp` report. It passed as
`PASS_SYNTHETIC_RUNNER_CORE_ONLY`: the prescribed elastic and physical fields,
recursive MPC endpoint vectors, `B*u`, finite-span displacement, and table
force all reproduced with maximum reported errors from `8.9e-16` to
`3.2e-15`. The report confirms one synthetic factorization and zero source
triplet parses, source factorizations, source states, or native runs. It did
read and verify the pinned source checksums, including the `.sti` checksum, and
the pinned CalculiX 2.23 SPRINGA source members.

I also exercised `filter_upper_triangle` with a separate five-DOF synthetic
stream containing two selected bodies, a non-target body, within-body
off-diagonals, and three explicit cross-body zeros. Both independently known
2×2 blocks and the ten-pair accounting total matched. The runner’s saved
synthetic checks additionally cover omitted structural zeros, mirrored
reconstruction, duplicate-pair rejection, incorrect target ownership, and
nonzero cross-body refusal. The saved output pin records the earlier
source-only preparation and Ruff checks. The parent’s current source-only
replay was still underway during this review and should finish cleanly before
the one-shot launch decision.

The preparation path pins both target DOF sets and reconstructs the physical
projection against the saved `D` operator. The recovery path forms each raw
body load from the saved gravity, climber, and `-B.T*f` terms; it checks load
closure and balance without repairing the physical load. The synthetic known
answer then exercises the same body solve core and downstream reconstruction.
It does not establish the conditioning, pair counts, or runtime of either real
source block.

## Source extraction and comparison behavior

The source parser enforces the pinned one-based upper-triangle form, finite
values, in-range indices, unique pairs, and presence of every diagonal. It
checks the frozen total of 2,320,506 unique pairs, 1,051 explicit zeros, and
4,601,263 reconstructed symmetric nonzeros. Cross-body nonzeros stop parsing;
explicit cross-body zeros are accounted separately. Omitted pairs remain
structural zeros. Only the two owner-selected blocks are assembled, zero
entries are removed, and each block’s CSR digest and observed pair count are
reported. The duplicate bitmap is 88,583,391 bytes at the frozen dimension,
well within the 2 GiB address-space budget before the small selected blocks
and method work.

The symmetry check confirms the blocks built by mirroring upper-triangle
entries are symmetric. It is not an independent lower-triangle comparison,
because the pinned export contains only the upper triangle. This matches the
frozen matrix format and does not require a global matrix rebuild.

The recovery report keeps the physical linear projection `B*u`, the original
coordinate binary64 `dd - dd0`, and the emitted SPRINGA table force as separate
quantities. The row comparison uses the recovered table force against the
unchanged inclusive native endpoint RF interval and separately reports the
unchanged native table-force interval. The interval calculation is simple and
unchanged in the reviewed code, but the synthetic toy does not exercise either
interval boundary or the final row-match status; that part was reviewed
statically. The code retains the 27-failure STOP and does not adopt a force or
change an interval.

## Parent launch conditions

The CLI refuses `--execute` without an external parent approval before it
enters `run_actual`; the saved output pin records exit code 2 and an absent
one-shot marker for that refusal. I did not repeat that command. The approval
must match the runner’s checked fields: preflight readiness hash, exact
runner SHA, source manifest SHA, and two-body row-1586 scope. This review and
the parent freeze remain separate review artifacts; neither is embedded in
that approval schema. The marker is created atomically outside the repository
after approval validation and before source extraction, so a failure after
consumption must not be retried under this same attempt.

The runner applies CPU and address-space limits and a 60-second wall timer,
and sets the common BLAS/OpenMP thread variables before importing NumPy and
SciPy. For a strict process-wide 60-second wall/CPU/address-space ceiling, the
parent should also enforce the deadline and limits from process launch: the
runner installs its limits after interpreter and numerical-library startup,
and its wall timer raises a Python exception rather than independently
terminating a process held inside a long native call. The parent should retain
the invocation’s external stdout/stderr and exit status; a parse error, hard
limit, or timeout after marker consumption can stop safely without writing a
JSON result. This is operational evidence capture, not permission to retry.

On the authorized invocation, preserve one serialized run, no more than two
body factorizations, five existing-method corrections per body, and immediate
stop at the first failed gate. A method pass or row-1586 interval match remains
only a bounded endpoint-recovery result; it does not clear the original
27-force STOP or establish mechanical acceptance.
