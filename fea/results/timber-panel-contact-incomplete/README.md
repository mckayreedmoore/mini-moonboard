# Incomplete first timber panel/leg contact attempt

The 600-second solver limit expired on 2026-09-08. The process exited with a
`TimeoutExpired`/`RuntimeError`; five increments had converged, ending at load
factor **0.228125**, not the required 1.0. No `execution.json` success record was
created, and the accepted-result publisher was not run. This is neither a
full-load result nor evidence that the structure failed.

The last complete increment sequence is 0.025, 0.05, 0.0875, 0.14375, 0.228125,
with 8, 8, 7, 7 and 8 iterations respectively. Contact-search/iteration cost
prevented completion within the initial time budget. Do not extrapolate these
partial nonlinear responses to full load or apply the old linear superposition.

`attempt.tar.gz` preserves the exact input metadata, solver deck, partial DAT,
log, status and convergence output, launch record, and launcher source. SHA-256:

`dde03df1a09dbccc0dc57e50a47788c5cab3c0c92be0a48500b533c6ce9cbd5c`

The larger FRD and auxiliary files remain in the original local directory
`fea/generated/timber-panel-contact`; they are not included in this compact
archive. The launcher source is included so this rejected attempt remains
identifiable even if future runtime controls change. No evidence was deleted.

The model is the preserved narrow timber candidate, not the current wider
candidate. The [contact plan](../../../docs/timber-contact-plan.md) records its
physical and numerical limits. Completing contact recovery still requires a
full direct load history, contact/equilibrium audit and sensitivity check; this
archive does not close that work. Current-candidate asymmetric evidence and
the auditable handoff take priority before extending this experiment.
