# Independent review: group-action method attempt02

Status: **PASS for the stated fail-closed scope change; no candidate criterion is decided.** This is a read-only review of the isolated patch and source audit. The patch was not applied to the maintained source, and no candidate groups, factors, resistances, or capacities were evaluated.

## Reviewed artifacts and identity

The exact proposal is [`four-plus-fail-closed.patch`](../current-group-action-method-attempt02/four-plus-fail-closed.patch), SHA-256 `3f1607d83e9a57f57293b9525118afd2b64d6da22983561edc4ae9b3079b43fd`. Its diff has exactly two paths: `mini_moonboard/nds_2024_group_action.py` (four inserted lines) and `tests/test_nds_2024_group_action.py` (32 inserted lines); it contains no deletions. `git apply --check` passed against the current working tree. The current maintained module and focused test bytes match the base pins, `2fb1a905a2e65a7ad9d2e6f8199b682e9b50a423474654301c825f13802d200e` and `29f5f5cbf52be2df3eaca26505c282a597262bd405c232bdea32a369f90c1085`.

I independently recomputed all hashes referenced by attempt02 `source-pins.json`, its `terminal-hashes.json`, and the multishear audit terminal record. All matched. The bound attempt01 readme/source-pins/pending-inventory and terminal record also matched. I downloaded the three official AWC PDFs to temporary storage and confirmed their SHA-256 values match the pins:

| Official AWC source | SHA-256 | Reviewed scope |
| --- | --- | --- |
| [NDS-2024, Chapter 11](https://web-media.awc.org/wp-content/uploads/2021/12/17205958/AWC_NDS2024_20250124_AWCWebsite_Chapter11.pdf) | `774d13c8a92cb8bfa876c45044fc40e8c3a90b1e3513075ed64626d5988f027d` | Printed p. 72, §§11.3.6.1–.3; p. 73 Table 11.3.6A |
| [NDS-2024 consolidated errata, March 23, 2026](https://awc.org/wp-content/uploads/2026/03/2024-NDS-Errata-and-Addenda-03.23.26.pdf) | `b3f4f8b3b2e2ffa5eb618de9e1182614c329d9e4a135096667364dc9a8e473c0` | January 2025 correction to the §11.3.6.1 gamma exponent, PDF p. 7 |
| [NDS-2024, Chapter 12](https://awc.org/wp-content/uploads/2026/08/AWC_NDS2024_withCommentary_20250328_WebsiteChapter-12-%E2%80%93-Dowel-type-fasteners.pdf) | `5fc837523ff10acc097a162718700a9b4ba64e627d2b0023439146d42fe4ee2a` | Printed pp. 95–96, §12.3.8 |

## Source boundary

The audit accurately separates the two provisions. Chapter 11 defines the group-action equation, lists `A_s` as the sum of gross side-member areas, and describes a row as same-diameter dowels loaded in single or multiple shear. The March 2026 errata confirms the corrected `D^1.5` exponent for gamma. Chapter 12 §12.3.8 gives separate even- and odd-member procedures for the connection reference lateral value `Z`; it does not state in that section how a plane-specific or whole-stack `C_g` is to be combined with those procedures.

AWC's [2024 NDS resource page](https://awc.org/resources/2024-nds/) says the current Commentary is part of the store package and offers a view-only option. The audited source set does not contain a bound official Chapter 11 Commentary file. The review therefore treats the four-plus `C_g` integration as an unresolved method-applicability question. This is a conservative evaluator restriction: the bound normative wording does not expressly prohibit aggregate `A_s` use for four-plus stacks, so the patch must not be described as proving that aggregate use is contrary to NDS or that a four-plus connection fails.

The guard is count-only, so it also returns pending for any four-plus payload that may not meet §12.3.8's stated opposing-force condition. That is a broad method-scope hold, not a claim that every four-plus topology requires the same resistance procedure.

## Patch behavior and reproduction

The guard is placed after member inventory and shear-plane consistency checks and before the aggregate member stiffness/factor calculation. Any otherwise valid payload with `1 + len(side_members) >= 4` therefore returns the evaluator's pending result with reason `four_or_more_member_plane_method_not_source_bound`; it cannot emit a `C_g` or capacity through this path. Because the added condition is false for one or two side members, the existing two- and three-total-member paths execute the same calculations as before.

I applied the exact diff only to a fresh `/tmp` copy of the pinned module and test file. The patched copy hashes were `b0c35d60081c222e5dfdf0aa795033afa1b5f795baffe33dae01b61f93e2cfc4` and `5a63579be46d795068e44f77244366d6d2bc411d574eb52e5fe9af9ccf9d0365`, matching the validation record. The focused command passed: **29 passed**. The new four- and five-total-member controls both require pending, null `cg`, null capacity and pending criterion disposition; the existing one-side and two-side cases still pass, including the multiple-shear aggregate-side-area regression and Table 11.3.6A examples. The temporary run made no repository changes.

## Disposition boundary

PASS applies only to exact patch integrity, tested evaluator behavior, and the claim that this change narrows supported inputs pending a source-bound method decision. It does not add a four-plus-member algorithm, choose between plane-specific and whole-stack treatment, or resolve the official Commentary question. All current candidate group inputs and capacities remain pending. No candidate or criteria files were changed and no native solver was run.
