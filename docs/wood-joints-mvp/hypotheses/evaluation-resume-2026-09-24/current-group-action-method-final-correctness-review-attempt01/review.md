# Current group-action method final correctness review — attempt01

Review date: 2026-09-27

## Scope and evidence

Fresh read-only review of the maintained evaluator, its focused tests, and the attempt01 method note. No earlier review reports were used. No source or test files were edited. The focused pytest suite was not rerun; the task handoff reports 29 passing tests for the stated command.

SHA-256 hashes of reviewed bytes:

- `mini_moonboard/nds_2024_group_action.py`: `8dac7e4b749d7b9253b5a4801c169d759e486030aac719b8c55dae80d9606488`
- `tests/test_nds_2024_group_action.py`: `5a63579be46d795068e44f77244366d6d2bc411d574eb52e5fe9af9ccf9d0365`
- `docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-group-action-method-attempt01/README.md`: `2b89c8f42d6b1d6464b8d4bfe50a8c13559d5e9e3966fb9fdf61a46e89481a48`

The supported-member-count guard is correctly placed before member-area evaluation: valid inventories with one through three total members continue through the existing method, while four or more total members return `pending`, null `cg`/capacity, and pending criterion disposition. The focused tests exercise both three-member compatibility and four-plus fail-closed behavior. The method note accurately describes the equation inputs, source-binding limits, non-acceptance result semantics, and current-candidate pending status.

## Findings

### 1. Extreme finite JSON values can escape fail-closed validation

**Location:** `mini_moonboard/nds_2024_group_action.py:38-43,275-296,450-492`

`_finite()` calls `math.isfinite()` on arbitrary Python integers, which raises `OverflowError` for sufficiently large JSON integers instead of returning a pending result. Separately, finite coordinate inputs can overflow during center subtraction/projection. `_group_geometry()` does not check derived values for finiteness; with two centers at `[-1e308, 0, 0]` and `[1e308, 0, 0]`, a valid `0.2 in` dowel row reaches the small-diameter shortcut and returns `status="calculated_method_only"`, `cg=1.0`, and `uniform_pitch_in=inf`.

**Impact:** The result contract permits a calculated method result containing a nonfinite geometry output, while oversized but valid JSON integers can raise instead of returning the documented pending disposition. This undermines the finite-input and fail-closed boundary.

**Fix:** Make numeric conversion/finiteness checks catch integer-to-float overflow; check derived relative coordinates, projections, transverse residuals, and pitches for finite values before accepting the row; require every numeric output to be finite before returning a calculated status. Add regressions for an oversized integer and an extreme finite coordinate span on the `D < 1/4 in` branch.

### 2. A blank load-case identity is accepted as a calculated result

**Location:** `mini_moonboard/nds_2024_group_action.py:386-390,473-484`

The case-bound action validation requires only that `case_id` be a string. A whitespace-only value passes, and the evaluator returns `calculated_method_only` with that value in `case_id`. The top-level candidate/revision/group/scenario identities already reject blank strings, and the method documentation describes the action as case-bound.

**Impact:** The returned factor cannot be reliably associated with a named load case, weakening the result's traceability despite the payload digest matching.

**Fix:** Require `case_id.strip()` to be nonempty before evaluating the action and return pending for a missing, empty, or whitespace-only identifier. Add focused regressions for those inputs.
