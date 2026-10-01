# Independent review: timber cut-yield scenario attempt 01

**Review date:** 2026-09-28  
**Scope:** `compact-floor-flush-wood-joints-development`, revision
`led-clearance-2x6-runner-seated-blocks-v1`. Arithmetic and source-validation
review only.

## Result

The current stored packet reproduces correctly: all six declared source hashes
match, the builder's `--check` passes, and an isolated rebuild produces the
same report and verification bytes. An independent Decimal-based stable
first-fit-decreasing calculation matched all 30 scenarios, including bin
membership, used length, remainder, and unfitted IDs. The present inputs
reconcile to 24 distinct block IDs (18 4×4, 4 4×6, 2 2×6); the four specified
4×6 rip IDs remain ungraded and unresolved after remanufacture. The two 4×6
sections, and the 8-ft kiln-dried and 16-ft green 2×6 listing leads, remain
separate. The report's current purchase, price, grade-acceptance, physical-fit,
cutting-authorization, and release claims are false.

I found four validation gaps. They do not change the arithmetic in the current
packet, but they allow inconsistent inputs or verification metadata to pass
after source/packet updates.

## Findings

1. **Revision identity is not joined to two pinned source documents.** The
   builder pins and loads `revision.json`, but never reads its `revision_id`;
   it also checks the source-yield schedule's candidate but not its
   `geometry_revision_id` ([builder lines 89–102](../../../../../scripts/build_current_timber_cut_yield_scenario_attempt01.py#L89)).
   Both current documents contain the expected revision. In an isolated copy,
   changing `revision.json.revision_id` and refreshing that source pin still
   let `build_report()` emit the expected revision. Changing the schedule's
   revision likewise passed after refreshing its source pin and the T08
   source-yield hash reference. The output revision is hard-coded, so it can
   describe a revision that the pinned source records do not describe. Check
   both source fields against `REVISION_ID` before building.

2. **`--check` accepts contradictory verification metadata.**
   `verify_packet()` checks the report hash, source status/count, and scenario
   count, but does not compare the remaining verification fields to the
   expected generated record ([builder lines 410–425](../../../../../scripts/build_current_timber_cut_yield_scenario_attempt01.py#L410)).
   In an isolated packet, I changed `schema`, emptied `source_pins`, replaced
   `scenario_inputs_sha256`, set `blank_count` to 999, and set
   `physical_or_purchase_claims` to true. `verify_packet()` still returned
   successfully; the CLI would then print 999 blanks. Compare the complete
   verification object with its expected values or validate every field.

3. **Non-finite cut-loss inputs pass numeric validation.** The comparisons
   reject negative kerf/trim but accept NaN; the packer also accepts non-finite
   stock, kerf, and trim values ([builder lines 258–269 and 324–327](../../../../../scripts/build_current_timber_cut_yield_scenario_attempt01.py#L258)).
   In an isolated input copy, setting one kerf to NaN produced 15 scenarios
   marked `arithmetic_fit_in_hypothetical_length` with NaN used lengths.
   Python then serializes these as non-standard JSON `NaN`. Require finite
   numeric values before packing and writing.

4. **Manifest ID comparison does not enforce 24 unique manifest rows.** The
   guard verifies 24 unique schedule IDs and set equality, but not manifest
   row count or uniqueness ([builder lines 119–126](../../../../../scripts/build_current_timber_cut_yield_scenario_attempt01.py#L119)).
   Appending a duplicate manifest row and refreshing its source pin still
   passed, while the report asserted
   `exact_ids_match_attempt04_manifest: true`. Require exactly 24 unique
   manifest IDs as well. The current manifest itself has 24 unique rows.

## Reproduction and evidence

- `python3 scripts/build_current_timber_cut_yield_scenario_attempt01.py --check`:
  **PASS**, 6 source pins, 30 scenarios, 24 blanks.
- Isolated `write_packet()` rebuild: report and verification bytes both equal
  the stored packet; report SHA-256
  `a0cb19c890020f58b00c010ffb646d49dcebfd679deb079cfc5754d31fa0a617`.
- Independent Decimal FFD comparison: **30/30 match**, no bin, length,
  remainder, or unfitted-ID differences.
- Representative arithmetic, with 3.2 mm kerf per blank including the last
  blank and 25.4 mm trim per bin:
  - 4×4, 8 ft: 18 blanks total 2140.2 mm; used 2197.8 mm; remainder 215.2 mm.
  - 4×6, 8 ft, section 83.9×139.7 mm: two 134.7 mm blanks; used 275.8 mm;
    remainder 2137.2 mm.
  - 4×6, 8 ft, section 88.9×133.35 mm: two 139.0 mm blanks; used 284.4 mm;
    remainder 2128.6 mm.
  - 2×6, two 276.3 mm blanks: used 559.0 mm; remainders 1854.0 mm at 8 ft
    and 4292.4 mm at 16 ft.
- Edge probes: exact capacity fits; a kerf-over-capacity blank is reported
  unfitted; end trim is charged once per bin; source drift without pin refresh
  fails closed. The four validation gaps above reproduced in isolated copies.
- The focused pytest command could not run because `pytest` is not installed
  in the available `/usr/bin/python3` environment. No repository test or
  source files were changed.

## Reviewed artifact hashes

| Artifact | SHA-256 |
|---|---|
| Builder `scripts/build_current_timber_cut_yield_scenario_attempt01.py` | `491d55b3c57f53a4de9ba162bd9562b5b106e6a1a86d499bd96fb767e7234c54` |
| Focused tests `tests/test_current_timber_cut_yield_scenario_attempt01.py` | `36906352a51dd667c25291b0ecb239f1762a7b08aedec6dc6463d57595cad850` |
| `source-pins.json` | `06358bd404613ceeb646b5a581b78d5214eb8e3084f14ea938e143e91b662ea1` |
| `scenario-inputs.json` | `2b9958d46e1277b51f47e132a3b7e00db3e44cd093ff06ce9ff696a3151130bc` |
| `current-timber-cut-yield-scenarios.json` | `a0cb19c890020f58b00c010ffb646d49dcebfd679deb079cfc5754d31fa0a617` |
| `verification.json` | `85cd80478ff3602ea870be1bda18b1bb20d89f52e9270aae90dd501b15380621` |

All six pinned sources matched their declared hashes: source-yield register
`2c710708d5e775d742375e28fadd323ecfe7f8e81c186c6028704c903a65266c`;
attempt04 manifest
`9e682e28c3d4c3c0594863f82c6b74d19dee2700f3856d34e1a26f69082e4f11`;
grade disposition
`c0e5c0bb9a32403a6fe047a3b995667f2d35df81b1333a68f773c318ed560e86`;
T08 material status
`590e8a52d25db87885699f75c9f33e204a3c611f96f563800e2cbbd42a757`;
geometry revision
`148f97623573558cd6a6c53f8a5399f2b30549d6aa1ed13c326dfe1bc3e9d695`;
selected authority `current-candidate.json`
`f4505746a0a33eac1771708fbc376686b801e2c2af3053d9447fbbc6e22491a4`.

The work is conditional arithmetic only. It establishes no stock selection or
availability, purchase quantity, price, material grade, cut feasibility,
physical fit, fabrication authorization, or candidate/climbing release.
