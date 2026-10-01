# Current group-action method attempt03 — architecture review

**Review scope:** architecture review of the applied four-plus fail-closed patch in `mini_moonboard/nds_2024_group_action.py` and `tests/test_nds_2024_group_action.py`. This report does not assess the structural validity of the method or source interpretation.

**Hash binding:**

| Artifact | SHA-256 |
| --- | --- |
| Pinned patch, `current-group-action-method-attempt02/four-plus-fail-closed.patch` | `3f1607d83e9a57f57293b9525118afd2b64d6da22983561edc4ae9b3079b43fd` |
| Applied module, `mini_moonboard/nds_2024_group_action.py` | `b0c35d60081c222e5dfdf0aa795033afa1b5f795baffe33dae01b61f93e2cfc4` |
| Applied tests, `tests/test_nds_2024_group_action.py` | `5a63579be46d795068e44f77244366d6d2bc411d574eb52e5fe9af9ccf9d0365` |

The applied-file hashes match the isolated candidate hashes recorded in attempt02 `validation.json`; the patch hash matches its terminal hash record. The focused suite result is taken from the supplied attempt02 validation record: 29 passed. No tests or solver runs were performed for this review.

## Assessment

The source ownership and abstraction fit the change. This module owns the narrow `Cg` method and already validates method applicability; placing the new fail-closed scope gate inside `evaluate_group_action_factor()` keeps the decision at the boundary that controls whether a factor is computed. The guard follows validation of the bound member roster and matching shear-plane count, and precedes member-area/stiffness calculations. It preserves the function signature and output contract, returning the existing `pending` form with null factor/capacity and pending criterion disposition. The added four- and five-member tests cover both sides of the rejected scope while the existing two-side-member case preserves the three-total-member boundary.

No substantial ownership, coupling, or abstraction concern was found. Repository search found no non-test direct caller of this evaluator; it remains a focused method library surface, so this guard should not be represented as an integrated current-criterion gate by itself.

## Finding

**Low — The maintained API documentation does not expose the new total-member scope cap.** The module docstring at `mini_moonboard/nds_2024_group_action.py:1-7` names the single-row, wood-to-wood, same-diameter boundary but not the new maximum of three total members. The `evaluate_group_action_factor()` docstring at lines 344-352 also omits it. The runtime reason at lines 410-413 is explicit enough for a caller to diagnose a rejected payload, and the attempt02 README documents the cap, so this is a discoverability issue rather than a fail-open behavior. That README is an isolated-attempt record and says the patch was not applied, which was accurate when recorded but does not document its later adoption.

**Recommended fix:** add the three-total-member limit and the unresolved four-plus interpretation to the maintained module/function docstring or a current consumer-facing method note. Preserve attempt02 as historical evidence; record adoption in a current status artifact rather than rewriting its original validation state.

## Guard placement

Keep the guard at the current validation boundary. The evaluator first proves the supplied roster agrees with the separately supplied source binding and payload digest, then validates the member/plane inventory. At that point it has the facts needed to return a method-scope pending result without duplicating the cap in payload construction, a caller, or a separate policy layer. Moving the guard earlier would not improve cohesion and risks making the source-scope decision depend on an unbound roster; moving it later could allow unsupported cases to enter the factor arithmetic.
