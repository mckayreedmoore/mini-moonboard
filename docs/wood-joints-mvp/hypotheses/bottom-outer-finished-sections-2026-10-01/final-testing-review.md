# Final testing review

## Outcome

No substantial testing defect remains in the reviewed bounded geometry and point-action demand join. The current integration test closes the prior coverage gap with a hand-calculated oracle over the producer's emitted whole-body and cut-state values.

For the full-load cleat body, I independently summed the three fixture actions. The expected force is `(0, -2, -2) N`, the origin moment is `(30, 160, -134) Nmm`, and the propagated force and moment rounding radii are `(0.02, 0.02, 0.02) N` and `(0.6, 0.98, 0.78) Nmm`; these agree with the test's assertions.

The two traces at the 10 mm bore plane also agree with independent hand calculations. The negative-station approach assigns the on-plane action to positive-side material and yields positive-side cut force `(0, 2, 2) N` and cut moment `(-30, -140, 114) Nmm`. The positive-station approach assigns it to the negative side and yields `(0, 3, 2) N` and `(-50, -140, 114) Nmm` for the positive side. The asserted centroid transports, moment radii, local projections, and opposite-side force/moment are consistent with the fixture frame and centroid. The oracle does not reuse the producer's host-action helpers.

The integration checks still cover deterministic output, all 4 axes/8 bore memberships/6 planes, all 63 body identities and 252 two-trace cut identities, negative acceptance flags, and source-gate/frame/STEP corruption. The standalone unit tests cover malformed bore inputs, source-pin changes, point-force jumps, centroid transport, contact-footprint handling, and an actual small CadQuery section-area oracle. The independent parent verifier rebuilds expected report values from raw inputs without importing the producer or its helpers.

The integration fixture mocks STEP import and section-property extraction. This keeps it suitable for public checkouts; the small geometry unit oracle exercises the actual section helper. I did not run a native solve, full CAD extraction, or private raw-source replay during this closing review.

## Checks run

- `.venv/bin/pytest -q docs/wood-joints-mvp/hypotheses/bottom-outer-finished-sections-2026-10-01` — **20 passed**.
- `.venv/bin/ruff check --no-cache docs/wood-joints-mvp/hypotheses/bottom-outer-finished-sections-2026-10-01` — **passed**.
- `.venv/bin/ruff format --check docs/wood-joints-mvp/hypotheses/bottom-outer-finished-sections-2026-10-01` — **15 files already formatted**.

## Reviewed SHA-256 identities

| File | SHA-256 |
| --- | --- |
| `produce.py` | `662404918c93bb9d96fa48b0b9f02237aaf260b8db1c510dfe866334017e4da7` |
| `parent_verify.py` | `7b1ceeaf8e68a6f92c6d78e993d781be792e73a31a5b35d0a781195e88cebb0e` |
| `test_sections.py` | `2632083c4e393b0d212426522405463f642f11cf488155a50617579eb6517aad` |
| `test_integration.py` | `739ec1d1b01ed2c85dc23e5254369ce88d660d3bfb515564161d72758827714c` |
| `README.md` | `e51fa673635d68f8674d7bdbbeaa00309f11f9412735afab430260aa6353334f` |
| `validation.md` | `75da22785f3c4476168abceddbe330b7b1e9e803e5103db1dc817fe03c5d6ca2` |
| `resistance-disposition.md` | `39945e0cd3cfc2cc904d3880ae3019db6a92bd0512af075d0316700e937ae066` |
