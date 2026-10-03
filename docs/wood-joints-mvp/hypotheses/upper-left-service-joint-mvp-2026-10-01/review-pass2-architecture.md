# Architecture review pass 2

Reviewed only `check_joint.py`, `test_joint.py`, and `README.md` against the pinned review target and repository instructions. Previous review files and `validation.md` were not consulted. No implementation, CAD, mesh, native, build, or Git work was performed.

## Finding

**P2 — Candidate ownership is reported but not enforced** (`check_joint.py:202-203, 281-284`; `test_joint.py:80-103`). The checker verifies the geometry revision, then copies `action["candidate"]` into its output without requiring the expected `compact-floor-flush-wood-joints-development` candidate named by the README. If the pinned input is later refreshed from another candidate while retaining this revision identifier, the force and component calculations can still run and the frozen-result test has no assertion that the candidate is correct. The output would remain on HOLD, but its candidate-specific evidence could be attributed to the wrong lane. Add an explicit expected-candidate assertion before selecting rows and cover a mismatching candidate in a negative test.

No other substantial architecture, evidence-flow, immutability, maintainability, or repository-consistency findings in the reviewed files.
