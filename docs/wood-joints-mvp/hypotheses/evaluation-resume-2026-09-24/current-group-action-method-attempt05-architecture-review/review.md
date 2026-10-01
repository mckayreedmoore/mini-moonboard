# Architecture and integration review — group-action method attempt05

Review date: 2026-09-28  
Scope: read-only review of the attempt05 package, its maintained source and tests, and the maintained wood-joint criteria/method/coverage documents. No solver, Docker, or test command was run. The repository was already dirty on `master`; findings are bound to the hashes below.

## Assessment

The method-to-acceptance boundary is explicit and consistent across the implementation, method map, coverage register, and attempt record. The helper emits only a method result, leaves `capacity` null and `criterion_disposition` pending, and identifies the limit of its provenance. The maintained criteria still show all 47 rows pending; group-factor evidence and fresh group actions remain open. The versioned attempt’s recorded hashes agree with the included base, patch, maintained source/tests, and pinned method map, and the patch passes a read-only dry-run against the included base.

The specific attempt05 trail is not linked from the maintained criteria or coverage views. The method itself is discoverable by module and function name, and the acceptance status is clear, but the rationale and reproducible patch/validation bundle require separate discovery under `hypotheses/`.

## Ranked finding

### P3 — Maintained criteria views do not link to the attempt05 evidence bundle

`criteria-method-map.md:45` names the method producer and carefully limits its scope, while `current-criteria-coverage.md:41` and the corresponding JSON row keep `additional_group_reduction_sensitivity` pending with no candidate group factors or bolt-group actions. These are good acceptance boundaries. However, none of the maintained criteria, coverage, next-plan, or completion-ledger sources links to `current-group-action-method-attempt05/README.md`; the attempt README, overflow-normalization change, and its hash/validation envelope are discoverable only by browsing the hypotheses directory. This weakens traceability for maintainers trying to connect the current method implementation to its versioned change and review state, but does not obscure the pending criterion or make the method look accepted.

Recommended follow-up: add a direct link from the maintained group-action method entry or a maintained method-history index to the attempt README. Keep the link informational and preserve attempt05’s existing hash envelope; if the pinned method map is changed, record that new map version in a subsequent append-only attempt record.

## Boundary and artifact checks

- **Method-only behavior:** `mini_moonboard/nds_2024_group_action.py:494-514` returns `calculated_method_only`, `capacity: None`, `criterion_disposition: pending`, and an explicit Eq. 11.3-1-only scope. Its provenance field says that matching caller-supplied bindings does not verify their authority.
- **Acceptance separation:** `criteria-method-map.md:45` states that the producer does not provide resistance, per-bolt force distribution, demand/capacity comparison, or criterion disposition. `current-criteria-coverage.md:3` says all 47 criteria remain pending; its group-reduction row states there are no current candidate group factors or bolt-group actions. `criteria.json:19` retains the criterion as pending with no evidence, while `current-criteria-coverage.json:227-232` records pending status and `historical_result_transferred: false`.
- **Attempt scope:** `validation.json` records no candidate capacity/pass, current-joint run, solver, or Docker invocation and limits tests to synthetic/published-table method fixtures. Its 36-test result is recorded metadata; this review did not rerun that command.
- **Hash consistency:** the two archived base files match `base_attempt04_sha256_by_file`; current maintained source and tests match `maintained_attempt05_sha256_by_file`; the attempt patch hash agrees across `attempt05.patch`, `source-pins.json`, and `validation.json`; the criteria-method-map hash matches both attempt pins. Every sibling entry in `terminal-hashes.json` matches the corresponding file hash.
- **Patch replay check:** `patch --dry-run -p1` against the included `base/` completed for both files without a reported hunk offset or fuzz. No file was changed by that check.
- **External execution evidence:** the hash envelope binds the recorded validation text to the attempt files; it does not independently attest that the recorded pytest command ran. The result remains reproducible from the included source, patch, and tests, but was not independently exercised in this review.

## Exact reviewed hashes

Hashes are SHA-256 over the inspected working-tree bytes.

| File | SHA-256 |
| --- | --- |
| `AGENTS.md` | `672203b929d51d340d39d770e71dd43b019794ea33172bc9f4f7be469fc20536` |
| `docs/wood-joints-mvp/criteria-method-map.md` | `2d9083d4286e328553183e0bb993cfb913985fbe4960717bfe0bb4ef416d32e7` |
| `docs/wood-joints-mvp/current-criteria-coverage.md` | `ccda149cf7add227a7a038311625595764331c57a43af6b23de973a88d1b6e0a` |
| `docs/wood-joints-mvp/current-criteria-coverage.json` | `c07c786c37a745aec1c28f917ec6d326cef09b73fa9b14b0d76fb9d06c0d059c` |
| `docs/wood-joints-mvp/criteria.json` | `fd1df5f106b944d21bc237d0ff789eb30437640ce81cb3e059c7e21f3a531784` |
| `docs/wood-joints-mvp/next-mvp-plan.md` | `453b2ceed4e0216f191e6725c258486c61afe7f77199875d69e8ff83fce60582` |
| `docs/wood-joints-mvp/completion-ledger.md` | `696346b92863cba2b7dc89721d5c9338e0d067a024f57d18c15534356348c161` |
| `docs/wood-joints-mvp/artifact-manifest.json` | `23b4ff7086c26dd8570df9b651f34181a9c6158282d3c8c800c80924cb277dd9` |
| `docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-group-action-method-attempt05/README.md` | `c31198ebcf7227442a2a9a1ce62f6b5fbf0b2a84257370bd7f22ddf1a54da50e` |
| `docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-group-action-method-attempt05/attempt05.patch` | `e9f829bab63b6977e9ec071ab6e52e1fee82fa13113841f9b705dae46c7d5c36` |
| `docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-group-action-method-attempt05/source-pins.json` | `6ef7bd66d0f7fa627d127d407ca25e644ed021a04242044d1a1de6abe3501e34` |
| `docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-group-action-method-attempt05/terminal-hashes.json` | `2fa27a9decddd8b2118078c0ccca5dddfba87eef703765d22875c02e8050d248` |
| `docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-group-action-method-attempt05/validation.json` | `381f417f004299761ab7e8952dd65bbf3067ba17e4bcf111c00bd6c9f72c8238` |
| `docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-group-action-method-attempt05/base/mini_moonboard/nds_2024_group_action.py` | `d0d8cf193c9fb26206e459e749c176f0ace5b41bb472ffc24217d8a5942874f6` |
| `docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-group-action-method-attempt05/base/tests/test_nds_2024_group_action.py` | `c0137a5144e135e2bac3a4eb6861e0e85d10750b0b3471eb4fc55df13222c3f2` |
| `mini_moonboard/nds_2024_group_action.py` | `95305398bf4fc9590f33fe877aafaf0544dce91503b0f09d84db590a938c8122` |
| `tests/test_nds_2024_group_action.py` | `91868751abfef9ceab746927904d7cbab9c0ba0881867980d89e2f2ab0b828e7` |
