# Independent review: timber cut-yield scenario attempt 02

**Review date:** 2026-09-28  
**Scope:** `compact-floor-flush-wood-joints-development`, revision
`led-clearance-2x6-runner-seated-blocks-v1`. Review of arithmetic,
source/revision/manifest joins, attempt01 lineage, validator negative controls,
packet integrity, and claim limits.

## Result

**PASS; no actionable findings.** The attempt02 verifier passes all 14 pinned
source hashes and exactly reproduces the stored 30-scenario report and its
verification record. An independent Decimal implementation of stable
first-fit-decreasing length arithmetic matched all 30 stored packing objects,
including scenario identities, bin membership and order, used lengths, trim,
remainders, and unfitted IDs. The packet contains 24 unique block IDs: 18
4x4, four 4x6, and two 2x6 blanks. All four proposed post-rip 4x6 grade
dispositions remain unresolved.

Attempt02 closes the four attempt01 validator gaps identified by the prior
review. Its tests exercise the revision joins, complete verification-object
comparison, non-finite numeric rejection, and exact manifest ID count and
uniqueness. Source and attempt01 review lineage also reproduces. I found no
discrepancy in the current arithmetic or a way for the reviewed mutations to
pass the relevant validators.

This is planning arithmetic only. It establishes no lumber selection,
availability, accepted grade, physical cutting feasibility, purchase quantity,
price, physical fit, fabrication authorization, candidate selection, or
climbing release.

## Evidence

- `.venv/bin/python scripts/build_current_timber_cut_yield_scenario_attempt02.py --check`:
  **PASS**, 14 source pins, 30 scenarios, 24 blanks; attempt01 review and
  arithmetic authenticated.
- `.venv/bin/python -m pytest -q tests/test_current_timber_cut_yield_scenario_attempt02.py`:
  **15 passed**.
- `.venv/bin/ruff check scripts/build_current_timber_cut_yield_scenario_attempt02.py tests/test_current_timber_cut_yield_scenario_attempt02.py`:
  **PASS**.
- Independent recalculation from the pinned schedule and scenario inputs:
  **30/30 packing objects match exactly**. The independent implementation
  used Decimal values parsed from the source numbers, separated exact
  stock-class/cross-section cohorts, charged one kerf per blank, charged
  end trim once per arithmetic bin, sorted longest-first with part ID as the
  tie-breaker, and placed each blank into the first bin with sufficient
  capacity. It did not call either attempt01 or attempt02 packing functions.
- Reproduced representative 3.2 mm kerf / 25.4 mm end-trim results:
  4x4 8-ft cohort, 18 blanks, 2197.8 mm used and 215.2 mm remaining;
  4x6 8-ft cohort at 83.9x139.7 mm, two blanks, 275.8 mm used and
  2137.2 mm remaining; 4x6 8-ft cohort at 88.9x133.35 mm, two blanks,
  284.4 mm used and 2128.6 mm remaining; 2x6 8-ft, two blanks, 559.0 mm
  used and 1854.0 mm remaining; 2x6 16-ft, two blanks, 559.0 mm used and
  4292.4 mm remaining.
- The four source-bound rip IDs are the left/right center principal cleats
  and left/right outer knee inner-frame blocks; the grade status remains
  unresolved after remanufacture in the generated report.

### Validator controls

- Both `current-timber-source-yield.json.geometry_revision_id` and
  `revision.json.revision_id` must equal the reviewed revision. The original
  attempt01 builder also verifies schedule, manifest, grade, material-status,
  selected-authority, and scenario-input identities during the authenticated
  rerun.
- Attempt01's entire verification object is compared against its expected
  record. Tests mutate every existing field, including claim flags; dictionary
  equality also rejects missing or extra fields. Attempt02's full expected
  verification is likewise compared.
- NaN, positive infinity, and negative infinity are rejected for stock length,
  kerf, end trim, source blank length/section, and direct packer arguments.
  Strict JSON parsing rejects non-standard JSON numeric constants, and report
  serialization disallows non-finite values.
- The manifest join requires exactly 24 nonempty, unique IDs on both sides,
  then exact set equality with the 24 unique schedule IDs. Tests cover a
  duplicate replacing a row and a 25th duplicate row.
- Attempt01 source-pin entries match the corresponding attempt02-authenticated
  hashes. Its report rebuilds from the authenticated inputs; its complete
  verification passes; and the frozen attempt01 independent-review hash and
  six reviewed artifact hashes are bound into attempt02. The attempt01 report
  SHA-256 remains
  `a0cb19c890020f58b00c010ffb646d49dcebfd679deb079cfc5754d31fa0a617`, and
  its review SHA-256 is
  `d89adb44501525d6fd459b379afec96698838fcdc83f0f4503907fcc15020ea4`.

## Reviewed artifact hashes

| Artifact | SHA-256 |
|---|---|
| Attempt02 builder `scripts/build_current_timber_cut_yield_scenario_attempt02.py` | `027479a0f082c036da5bba603defea348c4d97ca4be7f76626177a03e077bc7d` |
| Attempt02 focused tests `tests/test_current_timber_cut_yield_scenario_attempt02.py` | `5ddf1e03cd7abbd095aec6368e0026e9bf87bd86f80a2fccbea199e408806866` |
| Attempt02 README | `7491d8fe3531190d92976e9a02ea5d063debb81bd6f5d54b20640fdc6a3c69aa` |
| Attempt02 `source-pins.json` | `e24b70e2c4de79918b7b654a3f789d820b9cf63bbdcc4ae77f41350f6b70e46e` |
| Attempt02 stored scenarios | `df1f4e2df03f1f65870d71f4a63708fbc06a4dd0a5ca9f9f527ff30a63249c30` |
| Attempt02 `verification.json` | `0756de1f74158f9d844f4b71fe1acce40ecf91b6994368d9e2f11fe4909061e8` |
| Attempt01 independent review `REVIEW.md` | `d89adb44501525d6fd459b379afec96698838fcdc83f0f4503907fcc15020ea4` |

The attempt02 source-pin manifest authenticates all 14 declared inputs. The
stored attempt02 report hash is checked by `verification.json`; the
verification record is compared in full with a freshly generated expected
record. The hashes above provide this independent review's frozen references
for the producer, tests, and packet files.

From the repository root, verify this review's frozen files and all 14 source
pins with:

```sh
sha256sum -c docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-timber-cut-yield-scenario-attempt02-independent-review-2026-09-28/SHA256SUMS
```
