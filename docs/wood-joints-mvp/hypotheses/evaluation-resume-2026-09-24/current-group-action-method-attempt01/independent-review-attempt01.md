# Independent review — current group-action method attempt01

Review date: 2026-09-27. Scope: read-only check of the frozen method packet, with emphasis on the full-content sensitivity-contract digest correction. No source, candidate, criteria, or native-solver changes were made.

## Disposition

**PASS for the sensitivity-contract digest fix and the stated method-only/pending boundary.** The retained method computes no current-candidate result. One future applicability boundary remains: do not rely on its unrestricted side-member count for four-or-more-member stacks until the applicable 2024 multi-shear interpretation is confirmed and represented plane by plane.

## Frozen bytes and reproduction

The packet's `terminal-hashes.json` matches the files on disk. Rechecked SHA-256 values:

| Artifact | SHA-256 |
| --- | --- |
| `mini_moonboard/nds_2024_group_action.py` | `2fb1a905a2e65a7ad9d2e6f8199b682e9b50a423474654301c825f13802d200e` |
| `tests/test_nds_2024_group_action.py` | `29f5f5cbf52be2df3eaca26505c282a597262bd405c232bdea32a369f90c1085` |
| `README.md` | `2b89c8f42d6b1d6464b8d4bfe50a8c13559d5e9e3966fb9fdf61a46e89481a48` |
| `source-pins.json` | `2fe859edc569179b2f8bc4f366f80ca828cf139f8c69cd6b5bffe2182392fef6` |
| `current-group-action-pending.json` | `77e05edeb8ebdf118dc50fc431c08cea28d0aec9b548c2db0b5895981d0f0f14` |

All eight local source-pinned files also match their recorded hashes. I fetched the exact official AWC Chapter 11 PDF and consolidated errata named by `source-pins.json`; their SHA-256 values match the packet's pins (`774d13c8…8f027d` and `b3f4f8b3…e473c0`). The official March 2026 errata confirms the corrected exponent `D^1.5` for the §11.3.6.1 `γ` equations ([AWC errata PDF](https://awc.org/wp-content/uploads/2026/03/2024-NDS-Errata-and-Addenda-03.23.26.pdf)).

I reran the focused suite with `.venv/bin/pytest -q -p no:cacheprovider tests/test_nds_2024_group_action.py`: **27 passed**. Independently evaluating the published Table 11.3.6A example gives `Cg = 0.9766839378238344`, `0.9163482162668575`, and `0.8371926373880905` for `N=2,3,4`, matching the test values and rounded table values `0.98`, `0.92`, and `0.84`. The quarter-inch threshold is handled as documented: `D < 0.25 in` returns 1; `D = 0.25 in` uses the equation. The two mixed-diameter permutations straddling that boundary return pending.

## Sensitivity-contract integrity

`canonical_sensitivity_contract_sha256()` hashes the complete strict-JSON contract after removing only its root `sha256` member. The canonical byte rule is explicit: sorted string keys, compact JSON separators, UTF-8, no non-finite numbers, and no Python-only tuple or non-string-key values. The evaluator recomputes that digest, compares it to the contract declaration, and separately requires the supplied coordinator binding to match the contract ID, source ID, digest, and reviewed status. It then verifies the baseline/sensitivity identities and that the contract's changed-input paths match the actual payload differences (with root scenario ID and source-binding changes treated as metadata).

The adversarial regression changes `changed_input_paths` while preserving both the contract digest and separate binding digest. Evaluation returns `pending` with `sensitivity_contract_content_digest_mismatch`; it does not emit a ratio, capacity, or acceptance. The complete group payload independently has a separate expected digest, and mutation tests cover geometry, diameter, modulus, and load action. I found no bypass in the requested digest path.

These checks establish byte/content equality only. They cannot authenticate who supplied the separate expected digest or whether a `coordinator_reviewed` assertion is authoritative. The README states that limit, and the test contract is explicitly synthetic.

## Equation scope and remaining boundary

The implemented equation uses the stated wood-to-wood `γ = 180000 D^1.5`, `R_E = min(E_s A_s / E_m A_m, E_m A_m / E_s A_s)`, `u`, stable equivalent `m = 1/(u + sqrt(u²−1))`, and the Eq. 11.3-1 factor. The implementation uses gross areas, rejects mixed diameters and out-of-range diameter, checks a uniform straight row and row-aligned lateral resultant, and requires an independently bound member/fastener/action manifest. Parallel and perpendicular grain cases are separated; the perpendicular branch requires thickness, group width, and an equivalent area matching their product. Multi-row/staggered, oblique, nonwood, and mismatched inputs fail closed. I found no discrepancy in the implemented N=2–4 known answer or these declared single-row checks.

The API currently accepts any positive number of `side_members`, sums their areas into one `E_s A_s`, and checks that they share a modulus. The regression covers a single-shear case and a three-member/two-plane case, but not a four-or-more-member stack. AWC's older official commentary states that for four or more members each shear plane is evaluated as a single-shear connection for group action; NDS §12.3.9 also treats four-or-more-member reference lateral values plane by plane ([AWC 2018 commentary source](https://awc.org/wp-content/uploads/2021/10/AWC_NDS2018-withCommentary_20200827_AWCWebsite_Commentary.pdf), [AWC NDS 2018 Chapter 12](https://web-media.awc.org/wp-content/uploads/2021/10/AWC_NDS2018-withCommentary_20210928_AWCWebsite_Chapter12.pdf)). Those are not the pinned 2024 Commentary, so this review does not assert the exact 2024 treatment. Before using this branch with four or more plies, bind the 2024 rule and either represent each plane's main/adjacent-side section and compute the controlling factor, or make such cases pending. This boundary does not change this packet's current status: its current-revision record reports no group payloads or results and keeps `Cg`, capacity, and demand/capacity ratio null.

## Current-pending boundary

`current-group-action-pending.json` remains accurate and hash-pinned: current disposition is pending; no candidate group factors, capacities, or demand/capacity ratios have been emitted; 92 axes and 460 hardware components are not a complete grouped-row/load manifest. Inputs still needed include group membership/centers, actual sections and grain, fastener products, signed case actions, independent complete-payload digests, a real reviewed sensitivity contract, and separate resistance/demand evaluation. Nothing in the synthetic method tests or sensitivity contract resolves those requirements.

No native solver was run for this review.
