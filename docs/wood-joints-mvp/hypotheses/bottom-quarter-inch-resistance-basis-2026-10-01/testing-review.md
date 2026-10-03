# Independent testing review

Reviewed October 1, 2026. Scope: the conditional 1/4-inch lateral references,
NDS applicability notes, frozen A1/A12/K12 actions and geometry, and the
producer/test regression coverage. No code, model, source report, CAD, or
hardware files were changed.

## Result

No current scoped output or applicability contradiction found. The producer
accepts the three frozen reports and pinned method/material sources. The
critical A1 `side_1` state retains its 197.1248 N signed tie and 661.948743 N
lateral action; its 45 ksi reference is 604.790663 N (ratio 1.094508867) and
its 106 ksi sensitivity is 928.221778 N (ratio 0.713136407). Both remain
unadopted. `Cg`, `Cdelta`, and adjusted resistance remain null. The quarter-inch
boundary test treats exactly 0.25 in as outside both sub-quarter exceptions.

The preserved output contains 84 selected bolt states, 168 member/bolt states,
84 interface wrenches, 21 cleat states, 252 contact-cell states, eight
placements, and four hardware rows. The selected four-axis geometry matches
the corresponding pinned source entries. An independent minimum check found
no governing-mode or selected-reference mismatch in all 336 conditional
results, including both rail mode switches.

## Verification

- README reproduction command completed successfully.
- Focused suite: 7 tests passed.
- Ruff: passed.
- Two in-memory producer replays serialized identically (2,022,953 bytes).
- SHA pins for all three reports, the six-mode helper, hardware requirements,
  and three AWC PDFs matched the producer's pinned values.

## Optional regression coverage

These are test-hardening suggestions, not current handoff failures:

- `test_all_2016_modes_independent_from_vectors_and_grains` compares all six
  mode values, but does not independently select the minimum or compare each
  output `governing_mode` and `reference_lateral_N`. The separate mode-switch
  test calls `p.modes` on one constructed geometry. Checking the minimum from
  the oracle for each result would directly protect the published reference
  selection and the reported rail switches. Current values passed that check.
- `test_all_actions_and_wrenches_preserved_and_no_acceptance` locks the signed
  source rows and complete action arrays, but the independent mode oracle reads
  the producer's emitted geometry map. Comparing that four-axis map directly
  with the pinned reference-report subset would also protect the geometry used
  by the oracle. Current geometry is an exact match.
- `test_changed_frozen_report_rejected` mutates only the reference report. The
  producer currently checks placement and joint report hashes through the same
  path; exercising those two inputs as well would guard those call sites, whose
  full wrenches and complete-joint states are preserved here.
- The tests assert `joint_accepted` and `adopted_capacity` are false, but do
  not assert every result's `Fyb_adopted` flag and the service scenario's
  `observed_or_adopted` flag remain false. Explicit assertions would lock the
  key distinction between the 45/106 ksi arithmetic hypotheses and an adopted
  quarter-inch material value.

## Reviewed-file SHA-256

| File | SHA-256 |
| --- | --- |
| `README.md` | `67fafbd3ed618130a7c93f393ac0732e5045676f409d0aadf7dc6e367b77f202` |
| `produce.py` | `d6ff5c94264af433f0da482970119e1cecb6fffd2e92158c18efaad9cccc8666` |
| `test_basis.py` | `6c07face307dbe30690a54c6ef4f67cec96f69cb4c3e444cc101c4fec023e7b6` |
| `applicability.md` | `a899a41289da46105def694d266ec3121c51a56fd9e0a20677dd127e8b518301` |
| `source-note.md` | `8f450e6603d56206b99a33f1adbbff5fba195d3b70d4be448c652376e1fea577` |
| `source-corrections-for-primary.md` | `461f6a597e29341e837f61765d79a28de1734c8a3fe49ee5269d2292e0edd599` |
