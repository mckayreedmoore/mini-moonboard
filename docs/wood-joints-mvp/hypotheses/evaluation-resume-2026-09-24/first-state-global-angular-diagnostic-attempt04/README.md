# Streaming DAT selectors for the full-ACC diagnostic

This is a separate proposal based on the corrected attempt03 producer. It
changes only the two selectors that previously loaded the entire CalculiX DAT
file into a list: control-vector extraction and `WJ_ANGULAR` contact-wrench
selection. Both now iterate the file line by line. `STEP` and `INCREMENT`
normalization is gated by the first alphanumeric character, so numeric/CEP
rows bypass the old per-line `re.sub` and regex calls. The monitor table path
also gates case normalization on the native `DISPLACEMENTS` heading prefix.

The contact reader retains selected-state time/value and exact coverage checks.
A selected record with a missing or malformed value line still fails. A final
truncated `WJ_ANGULAR` header in a later, unselected state is ignored and
reported under `contact_wrenches.coverage.ignored_partial_unselected_tail`;
it cannot complete or replace any selected-state row. Contact selection now
runs before C3D10 mass integration, so invalid or incomplete DAT coverage is
reported before the expensive operator call.

Focused tests compare control values from an extracted, hash-bound slice of the
frozen first-state DAT against the preserved pre-streaming parser. Contact
tests compare all 315 event39 records against that parser, exercise the actual
terminal state42 truncated-header bytes after event39, accept the completed
event40 slice, and reject the original incomplete event40 slice and a
truncated selected record. The existing full first-state no-mass preflight
test continues to exercise the real captured files. No terminal DAT was read
in full, and no native solve, CAD operation, or mass integration was run for
this proposal.

Run the focused checks with:

```sh
.venv/bin/pytest -q docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/first-state-global-angular-diagnostic-attempt04/test_reconstruct_full_acc.py
.venv/bin/ruff check docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/first-state-global-angular-diagnostic-attempt04/reconstruct_full_acc.py docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/first-state-global-angular-diagnostic-attempt04/test_reconstruct_full_acc.py
```

`source-pins.json` binds this proposal, its preserved attempt03 parser baseline,
the small actual first-state fragment fixture, and the separate event39/40 and
terminal-tail slices. This attempt has not been used for a mass run.
