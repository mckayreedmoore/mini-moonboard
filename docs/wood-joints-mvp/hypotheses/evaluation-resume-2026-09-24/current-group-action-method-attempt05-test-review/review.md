# Independent attempt05 test-coverage review

Review date: 2026-09-28. This review covers maintained attempt05 source and tests, their pinned attempt04 base, and the attempt05 patch. It is a read-only test review; no source or test files were changed, and no solver or Docker process was run.

## Hash binding

| Artifact | SHA-256 |
| --- | --- |
| `AGENTS.md` | `672203b929d51d340d39d770e71dd43b019794ea33172bc9f4f7be469fc20536` |
| `mini_moonboard/nds_2024_group_action.py` (maintained attempt05) | `95305398bf4fc9590f33fe877aafaf0544dce91503b0f09d84db590a938c8122` |
| `tests/test_nds_2024_group_action.py` (maintained attempt05) | `91868751abfef9ceab746927904d7cbab9c0ba0881867980d89e2f2ab0b828e7` |
| attempt04 base module | `d0d8cf193c9fb26206e459e749c176f0ace5b41bb472ffc24217d8a5942874f6` |
| attempt04 base tests | `c0137a5144e135e2bac3a4eb6861e0e85d10750b0b3471eb4fc55df13222c3f2` |
| `attempt05.patch` | `e9f829bab63b6977e9ec071ab6e52e1fee82fa13113841f9b705dae46c7d5c36` |
| `source-pins.json` | `6ef7bd66d0f7fa627d127d407ca25e644ed021a04242044d1a1de6abe3501e34` |
| `terminal-hashes.json` | `2fa27a9decddd8b2118078c0ccca5dddfba87eef703765d22875c02e8050d248` |
| `validation.json` | `381f417f004299761ab7e8952dd65bbf3067ba17e4bcf111c00bd6c9f72c8238` |
| `README.md` | `c31198ebcf7227442a2a9a1ce62f6b5fbf0b2a84257370bd7f22ddf1a54da50e` |
| `docs/wood-joints-mvp/criteria-method-map.md` | `2d9083d4286e328553183e0bb993cfb913985fbe4960717bfe0bb4ef416d32e7` |
| attempt04 `terminal-hashes.json` | `74ef1baf1469d15338b8fdea823ace903c924ba289e6bceb3208a3357ba3f3a0` |

The maintained module and test hashes match `source-pins.json`; its attempt04 hashes match the archived base files. I applied the pinned patch in a temporary directory from those base bytes. It applied cleanly and produced module/test hashes identical to the maintained attempt05 files above.

## Verification

`PYTHONDONTWRITEBYTECODE=1 .venv/bin/pytest -q -p no:cacheprovider tests/test_nds_2024_group_action.py` passed: **36 passed in 1.44s**.

I also exercised the public evaluator with an overflowing-norm diagonal row axis, matching diagonal fastener centers, and aligned large finite load and grain vectors. Attempt05 returned `calculated_method_only` with `Cg = 0.9682525542793202` and pitch `5.65685424949238 in`; the pinned attempt04 base returned `pending` with `not_a_single_straight_row`. This confirms the row-axis path changes as a consequence of the revised normalizer.

## Ranked coverage finding

**P3 — Add a positive-path regression for an overflowing-norm row axis.** The attempt05 tests at `tests/test_nds_2024_group_action.py:479` and `:490` cover the new normalizer through off-row load and oblique-grain cases that must fail closed. The same helper is used for `group_geometry.row_axis_xyz` at `mini_moonboard/nds_2024_group_action.py:245`, but no test locks the corresponding successful geometry path. The public probe above distinguishes attempt05 from the pinned base. A future row-axis-specific regression could therefore leave the new load/grain tests green while rejecting a finite, nonzero row direction. Add a public API assertion for this path if extreme finite direction components remain within the method's declared input range.

No reproduced correctness failure or unsafe calculated result was found in the reviewed attempt05 change. This finding concerns regression coverage for a numerical edge case; it does not qualify candidate inputs, capacity, or a criterion disposition.
