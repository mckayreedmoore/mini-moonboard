# NDS-2024 group-action method architecture review

Review attempt: `current-group-action-method-final-architecture-review-attempt01`
Review date: 2026-09-27
Outcome: one medium integration concern; no source or test changes made.

## Hash binding

This review is bound to the following worktree content (SHA-256):

- `mini_moonboard/nds_2024_group_action.py`: `8dac7e4b749d7b9253b5a4801c169d759e486030aac719b8c55dae80d9606488`
- `tests/test_nds_2024_group_action.py`: `5a63579be46d795068e44e77244366d6d2bc411d574eb52e5fe9af9ccf9d0365`
- `docs/wood-joints-mvp/criteria-method-map.md`: `2ab30c154d75306cb83c88fdde98f7af8082b3c57089a9fdf587c5b3b9818182`
- `mini_moonboard/__init__.py`: `ddca6b543ee77144e10ec73f6dcd3ca6ae5693cfa7ca5a881697ded0c6782f12`

Repository `HEAD` at review: `c7c91fd02dc0daec9619b2fa933c4f6daf2d9041`.
The evaluator and focused test file were untracked worktree files when reviewed.

## Assessment

The implementation has a coherent owner: one standalone NDS group-action method module contains the input-binding checks, supported geometry checks, Cg calculation, and paired-scenario sensitivity calculation. Its pure-Python boundary does not pull in CAD generation or solver execution. The package root currently exports board-model helpers; direct module imports are used by the focused tests, so I found no reason to add this engineering method to the package root.

The result boundary matches the repository’s engineering claims. A successful factor is labeled `calculated_method_only`, keeps `capacity` null and `criterion_disposition` pending, and says the caller-supplied manifest’s authority is not verified by the method (`mini_moonboard/nds_2024_group_action.py:340-355, 473-495`). Sensitivity is separately labeled method-only and explicitly excludes criterion demand/capacity interpretation (`:533-550, 681-696`). The unsupported four-or-more-total-member case returns pending with no Cg or capacity (`:412-415`); tests assert that boundary (`tests/test_nds_2024_group_action.py:204-233`). The tests also include published-table known-answer checks and synthetic input fixtures (`:22-91, 104-121`).

The task states that the focused 29-test suite passes. I inspected the tests but did not rerun them.

## Finding

### P2 — The caller contract is not discoverable from the maintained method register

`evaluate_group_action_factor` requires an independently supplied binding map and payload digest; its implementation enforces four named source roles and member identities (`mini_moonboard/nds_2024_group_action.py:163-228, 340-379`). The docstring explains that the coordinator owns those bindings, but the exact input record, binding shape, digest handoff, and output interpretation are otherwise available only by reading implementation and synthetic test helpers (`tests/test_nds_2024_group_action.py:22-91`).

The maintained producer register does not list this module. It describes M2’s existing reference components at `docs/wood-joints-mvp/criteria-method-map.md:27`, and the `additional_group_reduction_sensitivity` row names generic dependencies without identifying the new partial method at `:45`. The row correctly remains pending, since this module does not supply actual candidate groups, accepted actions, capacities, or criterion dispositions.

Impact: the next coordinator or producer author must reverse-engineer a safety-relevant data contract from Python and test fixtures. The code’s fail-closed checks reduce the risk of a silent acceptance, but they do not make the interface easy to discover or implement consistently.

Recommended fix: add a short versioned input/output contract document and link it from the producer register. Describe the supported uniform-row and member-count boundary, units, required independent manifest inputs and digest semantics, reason/status fields, and a minimal call example. Identify this as a method-only producer while keeping `additional_group_reduction_sensitivity` pending until candidate groups and case-bound actions are joined to it.

## Review limits

This is an architecture and integration review of the named implementation and tests. It does not validate NDS equation applicability, calculate candidate values, qualify a capacity, or change any repository evidence or criterion status.
