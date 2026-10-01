# Independent attempt08 test review

**Disposition: REVISE.** The isolated attempt08 focused suite passed all 43 tests, and 25 independent test cases passed. The requested path behaviors work in those cases. The packaged base does not support its advertised replay, and the README misstates the empty-key token.

This review is bound to patch SHA-256 `eaa0b29cd29f3f2c88fc0c63920116c856df30c95e74a675ee9c7fda825a6595`, module SHA-256 `010a883aa9b5d012844bb9ffd631e6a6560c6531e80f95134ad5551374d2e9d6`, and focused-test SHA-256 `e7ed2c7dbd403039bc28752072d1a1086f6d2aa3b7b07b8d5831b405efb3d965`. [Source hashes](source-hashes.json) record every attempt08 packet file and the initially checked related pins. The packet was unchanged at the closing check. The maintained repository files advanced during this review; the tests used the isolated, hash-verified attempt08 copy throughout.

1. **T1 — Packaged base already contains attempt08.** Both files under `current-group-action-method-attempt08/base/` hash to the maintained attempt08 values, not the attempt07 base values declared in `source-pins.json`. Forward replay in a temporary copy with `patch --batch --forward --fuzz=0 -p1` exits 1: all four hunks are recognized as reversed or already applied. This contradicts the packaged-base and replay claims in the subject README line 7 and validation file lines 8–9. See [the observed replay output](packaged-base-replay.json).

   Reverse-patching a separate temporary copy recovers both declared attempt07 base hashes. Forward replay of that recovered copy then succeeds without fuzz and reproduces both attempt08 hashes. This validates the delta against reconstructed base bytes; it does not make the distributed base-plus-patch package reproducible as claimed. Preserve this artifact and package the pinned, unpatched base in a successor, validating the packaged base itself before claiming replay success. See [the diagnostic recovery and replay](diagnostic-recovery-replay.json).

2. **T2 — The documented empty-key token has an extra backslash.** Subject README line 5 places `\\e` in a Markdown code span, which displays two literal backslashes. The API emits `\e`, with one backslash, for an empty object key. `\\e` instead denotes the literal key `\e`. The independent public-API tests accept each correct spelling and reject the swapped spelling with `sensitivity_changed_input_paths_do_not_match_contract`. The successor README should show the single-backslash token for an empty key.

| Check | Observed result |
| --- | --- |
| Declared metadata-file hashes and patch hash | Match |
| Packaged attempt07 base hashes | Both mismatch; both equal attempt08 output hashes |
| Maintained attempt08 file hashes at review start | Match |
| Attempt07 patch/terminal-hash pins and criteria-method-map pin | Match |
| Forward replay of packaged base | Fails, exit 1; all four hunks skipped |
| Diagnostic reverse then forward replay in a separate copy | Both stages pass without fuzz; both sets of declared hashes match |
| Isolated focused suite | 43 passed in 0.08 seconds |
| Independent path probes | 25 passed in 0.09 seconds |

The independent probes exercise four successful declarations for a 12-fastener pitch change: numeric order, lexical order, reversed order, and a duplicate declaration normalized away. The returned index order is explicitly checked as 10, 11, 1, 2, …, 9. Omitting indices 10 or 11, adding unchanged index 0, or declaring the wrong coordinate rejects the contract.

Growth from 10 to 12 fasteners and shrinkage from 12 to 10 both require the list length and whole-item paths for indices 10 and 11. Omitting length or either item fails, as does replacing a whole-item path with a leaf path. Empty-list growth and removal-to-empty are also checked. These are synthetic method inputs and establish no candidate joint performance.

Public-API probes cover dots, both square brackets, backslash, backslash followed by dot, an empty key, and a literal backslash-e key. Each accepts the exact escaped declaration and rejects an alias. A combined change includes literal dotted and bracketed keys alongside actual nesting and arrays, ensuring their paths do not collapse. A separate bounded private-helper census finds 259 distinct encodings for string keys over a six-character alphabet through length three, plus 100 distinct two-segment paths. This is bounded evidence for the requested escaping behavior, not a proof for arbitrary JSON trees.

The bundled attempt08 additions cover a positive 12-fastener example, positive and negative one-item growth, and positive dot-versus-nesting cases. They do not include shrinkage, multiple added or removed items, retaining item paths while omitting length, negative multi-digit-index contracts, bracket/backslash/empty-key cases, or rejecting escaped-path aliases. The [independent probe source](independent-path-probes.py) supplies these cases for this review; adding the relevant regressions to a successor would retain that coverage.

Every independent public-API call asserts `capacity is None` and `criterion_disposition == "pending"`. Successful calls also assert the composite method-only status and the explanation that the ratio is not an adopted criterion demand/capacity ratio. No scoped behavior failure was observed. No candidate capacity, structural criterion pass, joint acceptance, or native mechanics result follows from these tests.

The [focused run record](focused-test-run.json) verifies the imported module came from the temporary replay tree. An empty `mini_moonboard/__init__.py` existed only in that harness to prevent fallback to the repository's editable package. [Independent run details](independent-test-run.json), raw test output, and [the machine-readable review](review.json) are preserved here. Python/pytest execution was offline; no solver, Docker, native mechanics execution, geometry change, or criteria-map edit occurred. Prior review reports were not read.
