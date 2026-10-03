# Bottom-outer section validation record

The source-bound producer and independent raw-source verifier cover four
bottom-left axes, eight receiver memberships, three unchanged finished STEP
solids, six bore planes, 63 whole-body states and 252 two-trace cut states.
The code and synthetic tests run locally. The full source extraction was run
twice with byte-identical output, and the parent ran the independent verifier
successfully. No native mechanics solve, model change or resistance adoption
was part of these checks.

The first review pass found a meaningful regression-test gap: the producer's
complete artifact assembly was covered by the frozen-input replay, but lacked
a synthetic integration test. `test_integration.py` now exercises the complete
producer with temporary inputs, all case/member/plane/trace identities and
claim limits, deterministic output and representative source-gate/frame/STEP
corruption. The original [testing review](testing-review.md) records that
finding. The separate [calculation review](independent-calculation-review.md)
and [architecture review](architecture-review.md) distinguish source
reconstruction from geometry and deliberate local-only raw evidence.

The next testing review identified a second gap: the integration fixture
asserted identities and nonzero demand but lacked independent expected emitted
numbers. The final fixture now places a force exactly on a bore plane and
checks a hand-calculated whole-body wrench, rounding bounds, both emitted
cut traces, centroid transports and local components. Its expected numbers
do not call the producer's arithmetic helpers. The current twenty-test suite
passes after this correction.

Twenty focused tests pass, and Ruff and format checks pass. The same twenty
tests also pass in a temporary source-only workspace with this packet's
Python files and the two reused helpers, without frozen JSON or STEP files.
Parent additionally checked six
corrupted local reports: altered force, altered transported moment, duplicate
body, duplicate cut, unsupported criterion acceptance and an off-plane section
centroid. The independent verifier rejected each one. Its own small known
answer checks force/couple and uncertainty transport without importing the
producer or its reused arithmetic helpers.

The parent's final Ruff formatting of the independent verifier preserved its
parsed Python AST exactly. The original calculation-review receipt remains
the record of the pre-format bytes; the final code identity is listed below.
The parent reran the formatted verifier successfully against the same full
raw report. Producer and raw report bytes did not change.

| Artifact | SHA-256 |
| --- | --- |
| `produce.py` | `662404918c93bb9d96fa48b0b9f02237aaf260b8db1c510dfe866334017e4da7` |
| `test_sections.py` | `2632083c4e393b0d212426522405463f642f11cf488155a50617579eb6517aad` |
| `test_integration.py` | `739ec1d1b01ed2c85dc23e5254369ce88d660d3bfb515564161d72758827714c` |
| `parent_verify.py` | `7b1ceeaf8e68a6f92c6d78e993d781be792e73a31a5b35d0a781195e88cebb0e` |
| Reused `host_actions.py` | `39b3af2bdd468d20db868454cb81cce1ad2d3af30059c4204aa2284892cd390b` |
| Reused `section_geometry.py` | `8672daac3cef4aa55641a3e1bf6cee636d779be48145858282ffb0ed4d76f8d3` |
| Local full report, both byte-identical runs | `4303d229d154708a0356924d42b9daab8df78314f40d3e2d8d165ad209cbf6b8` |

The final-review entry points are
[correctness](final-correctness-review.md),
[testing](final-testing-review.md) and
[architecture](final-architecture-review.md). All three closing reviews found
no substantial unresolved finding. Both confirmed test gaps are fixed; the
receipt-index follow-up is resolved. The final testing reviewer reran the
twenty tests and Ruff/format checks successfully, and the correctness/testing
reviewers independently reconstructed the new hand-calculated expectations.
The reviewer snapshots precede this final status/index update; no code or
source response was changed by adding the receipts.

| Closing review receipt | SHA-256 |
| --- | --- |
| `final-correctness-review.md` | `07529a56e0a5ee4be4495ef9d53803a63b88070a3f4e95099ba50e5a39af2e67` |
| `final-testing-review.md` | `fa755e58622d30eb64f44a7be6b9f21575dba17be3f4968e2d6f48bd9a4a9c6a` |
| `final-architecture-review.md` | `a78df76e0e3fc9c0f05a7b2f7ae68f269e6444d8ae875ab2546e0d8b785b3515` |

The packet is complete for its frozen geometry and point-action demand-join
scope. Actual traction, regional compatibility, resistance and complete
joint/criterion acceptance remain open as the
[resistance disposition](resistance-disposition.md) records. Raw results
remain outside the published packet; synthetic tests and lint do not require
those inputs. Publication waits for the repository quiet-hours window to end.
