"""Tiny borrowed SCIP/PySCIPOpt selector fixture; no FE/frame operator."""

from __future__ import annotations

import argparse
import hashlib
import json
import time
from fractions import Fraction
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
EVENT_DIR = HERE.parent / "current-coupled-contact-event-reference-fixture-attempt01"
STRUCT_DIR = HERE.parent / "conditional-floor-structural-coupling-fixture-attempt01"
EVENT_INPUT = EVENT_DIR / "fixture.json"
STRUCT_INPUT = STRUCT_DIR / "fixture.json"
COUNTEREXAMPLE = STRUCT_DIR / "parent-reference-counterexample.json"
OUTPUT = HERE / "known-answer.json"

SOURCE_PINS = {
    str(EVENT_INPUT.relative_to(ROOT)): "0e5e5f6953a34be3b2078159cd51eb0f5398cb15ff2f22efd9b1d6e7df75b19e",
    str((EVENT_DIR / "verify.py").relative_to(ROOT)): "858e1326fd057c76d24808fb801996161d70b3484f213a640247d3ac746d4d79",
    str(STRUCT_INPUT.relative_to(ROOT)): "65f1956c02b16e48ae6fa1fc7f112eb3a7564643dbd4dc74365aea4be4479a24",
    str((STRUCT_DIR / "verify_fixture.py").relative_to(ROOT)): "a24fc9f46a072c2b324939728ac26d7084684b99403b91a4965dda1813536ac0",
    str((STRUCT_DIR / "parent-reference-counterexample.md").relative_to(ROOT)): "2af7037f256955c0929d6e228813174b33e0f86d275cc177f6bb63ca7003e115",
    str((STRUCT_DIR / "parent_reference_counterexample.py").relative_to(ROOT)): "7f150f308863f8b36c495b1a04595c7377eb30b3a4ae6810ade1ec90eb7e3015",
    str(COUNTEREXAMPLE.relative_to(ROOT)): "20e1ced882ff50d34b557d0c5a4dfcb4f884b173697a112f51c907181d0bd57c",
}

BALANCE_TOL_N = 1e-7
DISPLACEMENT_TOL_MM = 1e-8
FORCE_TOL_N = 1e-8
TOTAL_WALL_BUDGET_S = 30.0
PER_SOLVE_BUDGET_S = 3.0


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify_source_pins() -> None:
    for rel, expected in SOURCE_PINS.items():
        path = ROOT / rel
        actual = sha256(path)
        assert actual == expected, f"source pin mismatch: {rel}: {actual} != {expected}"


def diag_sign_transform(matrix: list[list[float]], signs: list[float]) -> list[list[float]]:
    return [[signs[i] * matrix[i][j] * signs[j] for j in range(len(signs))]
            for i in range(len(signs))]


def signed_vector(vector: list[float], signs: list[float]) -> list[float]:
    return [signs[i] * vector[i] for i in range(len(signs))]


def as_float(value) -> float:
    return float(Fraction(str(value)))


def make_case(*, name: str, operator: list[list[float]], external: list[float],
              contact_basis_diagonal: list[float], normal_k: float,
              references: list[float], expected_masks: list[list[bool]],
              expected_states: list[dict] | None,
              source_oracle: str, reference_scope: str) -> dict:
    ndof = len(operator)
    assert ndof == len(external) == len(contact_basis_diagonal)
    assert ndof == 2 * len(references)
    assert len(expected_masks) <= 2 ** len(references)
    for row in operator:
        assert len(row) == ndof
    return {
        "id": name,
        "operator_n_per_mm": operator,
        "external_wrench_n": external,
        "contact_basis_diagonal": contact_basis_diagonal,
        "normal_penalty_n_per_mm": normal_k,
        "tangent_reference_mm": references,
        "expected_masks_closed_true": expected_masks,
        "expected_states": expected_states,
        "source_oracle": source_oracle,
        "reference_scope": reference_scope,
    }


def source_cases() -> list[dict]:
    event = json.loads(EVENT_INPUT.read_text())
    structural = json.loads(STRUCT_INPUT.read_text())
    counter = json.loads(COUNTEREXAMPLE.read_text())

    event_k = [[float(v) for v in row]
               for row in event["structural_K_N_per_mm"]]
    event_contact_basis = [-1.0, -1.0]
    event_cases = []

    boundary = event["first_held_event_limit"]
    boundary_expected = [{
        "closed": False,
        "u_mm": [as_float(boundary["t_mm"]), as_float(boundary["q_mm"])],
        "tangent_forces_n": [as_float(boundary["T_N"])],
        "normal_forces_n": [as_float(boundary["N_N"])],
    }, {
        "closed": True,
        "u_mm": [as_float(boundary["t_mm"]), as_float(boundary["q_mm"])],
        "tangent_forces_n": [as_float(boundary["T_N"])],
        "normal_forces_n": [as_float(boundary["N_N"])],
    }]
    event_cases.append(make_case(
        name="one_cell_zero_force_event_boundary",
        operator=event_k,
        external=[float(v) for v in boundary["external_Ft_Fq_N"]],
        contact_basis_diagonal=event_contact_basis,
        normal_k=2.0,
        references=[float(boundary["episode_reference_mm"])],
        expected_masks=[[False], [True]],
        expected_states=boundary_expected,
        source_oracle="current-coupled-contact-event-reference-fixture-attempt01/fixture.json:first_held_event_limit",
        reference_scope="Prescribed event reference supplied to the selector; capture is not simulated by this fixture.",
    ))

    held = next(s for s in event["stage_samples"]
                if s["stage"] == "first_ramp_bearing" and s["parameter"] == "1")
    held_expected = [{
        "closed": True,
        "u_mm": [as_float(held["t_mm"]), as_float(held["q_mm"])],
        "tangent_forces_n": [as_float(held["T_N"])],
        "normal_forces_n": [as_float(held["N_N"])],
    }]
    event_cases.append(make_case(
        name="one_cell_nonzero_episode_reference_held",
        operator=event_k,
        external=[float(v) for v in held["external_Ft_Fq_N"]],
        contact_basis_diagonal=event_contact_basis,
        normal_k=2.0,
        references=[float(held["episode_reference_mm"])],
        expected_masks=[[True]],
        expected_states=held_expected,
        source_oracle="current-coupled-contact-event-reference-fixture-attempt01/fixture.json:stage_samples[first_ramp_bearing,parameter=1]",
        reference_scope="Prescribed captured reference -2 mm from the analytic event oracle; capture is not simulated by this fixture.",
    ))

    # The parent one-cell counterexample uses source coordinate z positive
    # away from support and N=-k*z. Transform q=-z so compression is positive.
    source_k = [[float(v) for v in row]
                for row in counter["stiffness_N_per_mm"]]
    one_cell_signs = [1.0, -1.0]
    one_cell_k = diag_sign_transform(source_k, one_cell_signs)
    one_cell_contact_basis = one_cell_signs[:]

    no_load = [float(v) for v in counter["external_tangent_normal_N"]]
    no_expected = []
    event_cases.append(make_case(
        name="one_cell_fixed_reference_no_admissible_state",
        operator=one_cell_k,
        external=signed_vector(no_load, one_cell_signs),
        contact_basis_diagonal=one_cell_contact_basis,
        normal_k=float(counter["normal_penalty_N_per_mm"]),
        references=[float(counter["episode_reference_mm"])],
        expected_masks=[],
        expected_states=no_expected,
        source_oracle="conditional-floor-structural-coupling-fixture-attempt01/parent-reference-counterexample.json:open_branch,bearing_branch",
        reference_scope="Prescribed zero reference from the fixed-reference counterexample; no history is simulated.",
    ))

    mirror = counter["mirrored_load_example"]
    multi_expected = []
    for closed, branch in [(False, mirror["open_branch"]),
                           (True, mirror["bearing_branch"])]:
        x, z = [float(v) for v in branch["q_mm"]]
        forces = [float(v) for v in branch["contact_T_N"]]
        multi_expected.append({
            "closed": closed,
            "u_mm": [x, -z],
            "tangent_forces_n": [forces[0]],
            "normal_forces_n": [forces[1]],
        })
    event_cases.append(make_case(
        name="one_cell_fixed_reference_two_admissible_masks",
        operator=one_cell_k,
        external=signed_vector([float(v) for v in mirror["external_tangent_normal_N"]],
                               one_cell_signs),
        contact_basis_diagonal=one_cell_contact_basis,
        normal_k=float(counter["normal_penalty_N_per_mm"]),
        references=[float(counter["episode_reference_mm"])],
        expected_masks=[[False], [True]],
        expected_states=multi_expected,
        source_oracle="conditional-floor-structural-coupling-fixture-attempt01/parent-reference-counterexample.json:mirrored_load_example",
        reference_scope="Prescribed zero reference from the fixed-reference counterexample; no history is simulated.",
    ))

    # The two-cell fixture stores z-gap coordinates. Apply D=diag(1,-1,...)
    # to both K and W; the transformed normal contact-basis entries change sign.
    model = structural["model"]
    source_operator = [[float(v) for v in row]
                       for row in model["carrier_stiffness_n_per_mm"]]
    signs = [1.0, -1.0, 1.0, -1.0]
    transformed_operator = diag_sign_transform(source_operator, signs)
    transformed_contact_basis = signs[:]
    cases = []
    for stage in structural["stages"]:
        hand = stage["hand_answer"]
        expected = stage["expected"]
        source_u = [float(v) for v in expected["q_mm"]]
        transformed_u = signed_vector(source_u, signs)
        active = set(expected["active_contacts"])
        masks = [["left" in active, "right" in active]]
        cases.append(make_case(
            name=f"two_cell_{stage['id']}",
            operator=transformed_operator,
            external=signed_vector([float(v) for v in hand["external_W_n"]], signs),
            contact_basis_diagonal=transformed_contact_basis,
            normal_k=float(model["normal_penalty_stiffness_n_per_mm"]),
            references=[float(v) for v in hand["episode_references_mm"]],
            expected_masks=masks,
            expected_states=[{
                "closed_mask": masks[0],
                "u_mm": transformed_u,
                "tangent_forces_n": [float(v) for v in expected["tangent_forces_n"]],
                "normal_forces_n": [float(v) for v in expected["normal_forces_n"]],
            }],
            source_oracle=("conditional-floor-structural-coupling-fixture-attempt01/fixture.json:"
                           f"stages[id={stage['id']}]") ,
            reference_scope="Stage references are supplied from the hand-answer oracle, including its recorded re-engagement values; this selector does not generate history or capture events.",
        ))
    return event_cases + cases


def add_indicator_le(model, expression, mode, *, activeone: bool, name: str) -> None:
    model.addConsIndicator(expression <= 0, binvar=mode, activeone=activeone,
                           name=name)


def build_model(case: dict, excluded_masks: list[list[bool]], max_solve_s: float):
    from pyscipopt import Model, quicksum

    n_contact = len(case["tangent_reference_mm"])
    ndof = 2 * n_contact
    model = Model()
    model.hideOutput()
    model.setParam("limits/time", max_solve_s)
    model.setParam("parallel/maxnthreads", 1)
    model.setParam("numerics/feastol", 1e-9)

    # Explicitly signed, unbounded physical coordinates and contact forces.
    u = [model.addVar(name=f"u_{j}", vtype="C", lb=None, ub=None)
         for j in range(ndof)]
    tangent = [model.addVar(name=f"T_{i}", vtype="C", lb=None, ub=None)
               for i in range(n_contact)]
    normal = [model.addVar(name=f"N_{i}", vtype="C", lb=None, ub=None)
              for i in range(n_contact)]
    closed = [model.addVar(name=f"closed_{i}", vtype="B")
              for i in range(n_contact)]

    # Simultaneous equilibrium: K u - C [T,N] = W. C carries the source
    # fixture's generalized-force sign, including the z -> compression flip.
    k = case["operator_n_per_mm"]
    c = case["contact_basis_diagonal"]
    w = case["external_wrench_n"]
    for row in range(ndof):
        terms = [k[row][col] * u[col] for col in range(ndof)]
        contact_index = row // 2
        if row % 2 == 0:
            terms.append(-c[row] * tangent[contact_index])
        else:
            terms.append(-c[row] * normal[contact_index])
        model.addCons(quicksum(terms) == w[row], name=f"equilibrium_{row}")

    penalty = case["normal_penalty_n_per_mm"]
    refs = case["tangent_reference_mm"]
    for i in range(n_contact):
        ti, qi = 2 * i, 2 * i + 1
        mode = closed[i]

        # Closed: q >= 0, N = k*q >= 0, and tangent displacement equals the
        # supplied episode reference. Each equality is two implications.
        add_indicator_le(model, -u[qi], mode, activeone=True,
                         name=f"closed_q_nonnegative_{i}")
        add_indicator_le(model, normal[i] - penalty * u[qi], mode,
                         activeone=True, name=f"closed_law_upper_{i}")
        add_indicator_le(model, penalty * u[qi] - normal[i], mode,
                         activeone=True, name=f"closed_law_lower_{i}")
        add_indicator_le(model, -normal[i], mode, activeone=True,
                         name=f"closed_normal_nonnegative_{i}")
        add_indicator_le(model, u[ti] - refs[i], mode, activeone=True,
                         name=f"closed_reference_upper_{i}")
        add_indicator_le(model, refs[i] - u[ti], mode, activeone=True,
                         name=f"closed_reference_lower_{i}")

        # Open: q <= 0, N = 0 and T = 0. These are active at binvar == 0.
        add_indicator_le(model, u[qi], mode, activeone=False,
                         name=f"open_q_nonpositive_{i}")
        add_indicator_le(model, normal[i], mode, activeone=False,
                         name=f"open_normal_upper_{i}")
        add_indicator_le(model, -normal[i], mode, activeone=False,
                         name=f"open_normal_lower_{i}")
        add_indicator_le(model, tangent[i], mode, activeone=False,
                         name=f"open_tangent_upper_{i}")
        add_indicator_le(model, -tangent[i], mode, activeone=False,
                         name=f"open_tangent_lower_{i}")

    # Exclude each complete binary mask found on a previous feasibility solve.
    # Rebuilding the tiny model each time avoids in-place postsolve mutation.
    for mask_number, mask in enumerate(excluded_masks):
        assert len(mask) == n_contact
        differs = [((1 - closed[i]) if mask[i] else closed[i])
                   for i in range(n_contact)]
        model.addCons(quicksum(differs) >= 1,
                      name=f"exclude_mask_{mask_number}")
    return model, u, tangent, normal, closed


def clean(value: float) -> float:
    value = float(value)
    if abs(value) < 5e-12:
        return 0.0
    return round(value, 12)


def validate_solution(case: dict, state: dict) -> None:
    u = state["u_mm"]
    tangent = state["tangent_forces_n"]
    normal = state["normal_forces_n"]
    mask = state["closed_mask"]
    n_contact = len(mask)
    assert len(u) == len(case["operator_n_per_mm"])
    assert len(tangent) == len(normal) == n_contact

    residuals = []
    for row, row_values in enumerate(case["operator_n_per_mm"]):
        ku = sum(row_values[col] * u[col] for col in range(len(u)))
        index = row // 2
        reaction = case["contact_basis_diagonal"][row] * (
            tangent[index] if row % 2 == 0 else normal[index])
        residuals.append(case["external_wrench_n"][row] - ku + reaction)
    assert max(abs(x) for x in residuals) <= BALANCE_TOL_N, (case["id"], residuals)

    for i, is_closed in enumerate(mask):
        t, q = u[2 * i], u[2 * i + 1]
        if is_closed:
            assert q >= -DISPLACEMENT_TOL_MM
            assert normal[i] >= -FORCE_TOL_N
            assert abs(normal[i] - case["normal_penalty_n_per_mm"] * q) <= FORCE_TOL_N
            assert abs(t - case["tangent_reference_mm"][i]) <= DISPLACEMENT_TOL_MM
        else:
            assert q <= DISPLACEMENT_TOL_MM
            assert abs(normal[i]) <= FORCE_TOL_N
            assert abs(tangent[i]) <= FORCE_TOL_N
    state["max_equilibrium_residual_n"] = clean(max(abs(x) for x in residuals))


def expected_matches(case: dict, state: dict) -> None:
    expected_states = case["expected_states"]
    if expected_states is None:
        return
    if "closed_mask" in expected_states[0]:
        expected = next(item for item in expected_states
                        if item["closed_mask"] == state["closed_mask"])
    else:
        expected = next(item for item in expected_states
                        if item["closed"] == state["closed_mask"][0])
    assert len(expected["u_mm"]) == len(state["u_mm"])
    assert all(abs(a - b) <= DISPLACEMENT_TOL_MM
               for a, b in zip(expected["u_mm"], state["u_mm"], strict=True))
    assert all(abs(a - b) <= FORCE_TOL_N
               for a, b in zip(expected["tangent_forces_n"],
                               state["tangent_forces_n"], strict=True))
    assert all(abs(a - b) <= FORCE_TOL_N
               for a, b in zip(expected["normal_forces_n"],
                               state["normal_forces_n"], strict=True))


def zero_boundary_ambiguity(case: dict, states: list[dict]) -> bool:
    if len(states) < 2:
        return False
    for left_index in range(len(states)):
        for right_index in range(left_index + 1, len(states)):
            left, right = states[left_index], states[right_index]
            differing = [i for i, (a, b) in enumerate(zip(left["closed_mask"],
                                                          right["closed_mask"],
                                                          strict=True)) if a != b]
            if not differing:
                continue
            if any(abs(a - b) > DISPLACEMENT_TOL_MM
                   for a, b in zip(left["u_mm"], right["u_mm"], strict=True)):
                continue
            if any(abs(a - b) > FORCE_TOL_N for a, b in zip(
                    left["tangent_forces_n"] + left["normal_forces_n"],
                    right["tangent_forces_n"] + right["normal_forces_n"],
                    strict=True)):
                continue
            if all(abs(left["u_mm"][2 * i + 1]) <= DISPLACEMENT_TOL_MM
                   and abs(left["tangent_forces_n"][i]) <= FORCE_TOL_N
                   and abs(left["normal_forces_n"][i]) <= FORCE_TOL_N
                   and abs(left["u_mm"][2 * i] - case["tangent_reference_mm"][i])
                   <= DISPLACEMENT_TOL_MM for i in differing):
                return True
    return False


def enumerate_masks(case: dict, deadline: float) -> dict:
    n_contact = len(case["tangent_reference_mm"])
    possible_masks = 2 ** n_contact
    excluded: list[list[bool]] = []
    states = []
    status_sequence = []
    complete = False
    stop_reason = None

    while len(status_sequence) < possible_masks + 1:
        remaining = deadline - time.monotonic()
        if remaining <= 0.02:
            stop_reason = "global_wall_budget_exhausted"
            break
        model, u, tangent, normal, closed = build_model(
            case, excluded, min(PER_SOLVE_BUDGET_S, remaining))
        model.optimize()
        status = model.getStatus()
        status_sequence.append(status)
        if status == "infeasible":
            complete = True
            stop_reason = "remaining_masks_proven_infeasible_after_no_good_exclusions"
            break
        if status != "optimal" or model.getNSols() < 1:
            stop_reason = f"solver_status_{status}"
            break

        solution = model.getBestSol()
        mask = [model.getSolVal(solution, item) >= 0.5 for item in closed]
        if mask in excluded:
            stop_reason = "solver_returned_previously_excluded_mask"
            break
        state = {
            "closed_mask": mask,
            "u_mm": [clean(model.getSolVal(solution, item)) for item in u],
            "tangent_forces_n": [clean(model.getSolVal(solution, item))
                                 for item in tangent],
            "normal_forces_n": [clean(model.getSolVal(solution, item))
                                for item in normal],
        }
        validate_solution(case, state)
        expected_matches(case, state)
        states.append(state)
        excluded.append(mask)
        if len(excluded) == possible_masks:
            complete = True
            stop_reason = "every_binary_mask_returned_once"
            break

    if not complete and stop_reason is None:
        stop_reason = "per_case_solver_call_budget_exhausted"
    states.sort(key=lambda item: tuple(item["closed_mask"]))
    if not complete:
        classification = "BUDGET_OR_SOLVER_STOP"
    elif not states:
        classification = "NO_ADMISSIBLE_STATE"
    elif zero_boundary_ambiguity(case, states):
        classification = "AMBIGUOUS_ZERO_BOUNDARY_MASKS"
    elif len(states) > 1:
        classification = "MULTIPLE_ADMISSIBLE_MASKS"
    else:
        classification = "ONE_ADMISSIBLE_MASK"

    expected_masks = sorted(case["expected_masks_closed_true"])
    actual_masks = sorted(state["closed_mask"] for state in states)
    if complete:
        assert actual_masks == expected_masks, (case["id"], actual_masks, expected_masks)
    else:
        assert all(mask in expected_masks for mask in actual_masks), (
            case["id"], actual_masks, expected_masks)
    return {
        "id": case["id"],
        "selector_input": {
            "operator_n_per_mm": case["operator_n_per_mm"],
            "external_wrench_n": case["external_wrench_n"],
            "contact_basis_diagonal": case["contact_basis_diagonal"],
            "normal_penalty_n_per_mm": case["normal_penalty_n_per_mm"],
            "tangent_reference_mm": case["tangent_reference_mm"],
            "analytic_expected_masks_closed_true": case["expected_masks_closed_true"],
        },
        "classification": classification,
        "candidate_masks": states,
        "solver_status_sequence": status_sequence,
        "all_binary_masks_proven_exhausted": complete,
        "stop_reason": stop_reason,
        "possible_binary_masks": possible_masks,
        "reference_scope": case["reference_scope"],
        "source_oracle": case["source_oracle"],
        "oracle_mask_count": len(expected_masks),
    }


def produce() -> dict:
    verify_source_pins()
    try:
        import pyscipopt
        from pyscipopt import Model
    except ImportError as exc:
        raise RuntimeError(
            "PySCIPOpt missing; replay with `uv run --no-project --with pyscipopt==6.2.0 python select_states.py --verify`"
        ) from exc

    probe = Model()
    probe.hideOutput()
    solver_version = {
        "pyscipopt": pyscipopt.__version__,
        "scip": f"{probe.getMajorVersion()}.{probe.getMinorVersion()}.{probe.getTechVersion()}",
    }
    del probe
    deadline = time.monotonic() + TOTAL_WALL_BUDGET_S
    cases = source_cases()
    results = [enumerate_masks(case, deadline) for case in cases]
    any_budget = any(item["classification"] == "BUDGET_OR_SOLVER_STOP"
                     for item in results)
    expected_classifications = [
        "AMBIGUOUS_ZERO_BOUNDARY_MASKS",
        "ONE_ADMISSIBLE_MASK",
        "NO_ADMISSIBLE_STATE",
        "MULTIPLE_ADMISSIBLE_MASKS",
        "ONE_ADMISSIBLE_MASK",
        "ONE_ADMISSIBLE_MASK",
        "ONE_ADMISSIBLE_MASK",
        "ONE_ADMISSIBLE_MASK",
    ]
    assert len(results) == len(expected_classifications)
    for result, expected in zip(results, expected_classifications, strict=True):
        if result["classification"] != "BUDGET_OR_SOLVER_STOP":
            assert result["classification"] == expected

    return {
        "schema": "current_coupled_indicator_selector_fixture/v1",
        "status": "BOUNDED_BUDGET_STOP" if any_budget else "ALL_TINY_FIXTURES_REPLAYED",
        "scope": "Tiny borrowed linear contact-state selector fixtures only; no FE kernel, current-frame operator, geometry, native CalculiX run, or design response.",
        "candidate": "none; method-only synthetic fixture",
        "geometry_revision_id": None,
        "solver": solver_version,
        "formulation": {
            "continuous_variables": "All generalized displacements, tangent forces T, and normal forces N are created with lb=None and ub=None; no user-supplied finite big-M or guessed displacement/force bound.",
            "normal_closed": "binary closed => q >= 0, N = k*q, N >= 0",
            "normal_open": "binary open => q <= 0, N = 0",
            "tangent_closed": "binary closed => tangent coordinate equals supplied episode reference; signed T remains unbounded",
            "tangent_open": "binary open => T = 0",
            "equilibrium": "All coordinates are balanced simultaneously in each MILP using the source-pinned K, W, and transformed contact-basis signs.",
            "indicators": "Each active inequality is a PySCIPOpt linear indicator. Every equality is represented by its two opposite indicator inequalities. A binary mode selects exactly one branch; a no-good row excludes each previously found complete mask.",
            "zero_boundary": "Closed and open use weak q sign inequalities. When both masks satisfy the same state at q=N=T=0 and the supplied reference, the result is explicitly classified as zero-boundary ambiguity.",
            "limits": {
                "total_wall_budget_seconds": TOTAL_WALL_BUDGET_S,
                "per_solver_call_seconds": PER_SOLVE_BUDGET_S,
                "max_solver_calls_per_case": "2^contact_count + 1",
                "budget_result": "BUDGET_OR_SOLVER_STOP; no uniqueness or infeasibility claim is made unless every binary mask is enumerated or the final no-good model is proven infeasible.",
            },
        },
        "source_pins": SOURCE_PINS,
        "results": results,
        "interpretation_limits": [
            "This checks a borrowed mixed-integer linear selector on the exact tiny owner fixtures only.",
            "The analytic episode references are supplied inputs to the selector; the solver does not discover event times, capture references, or reproduce load history.",
            "Enumeration is exhaustive only over the 2^n masks in each small fixture. It says nothing about 100 contacts or current-frame scalability.",
            "No current-frame operator was assembled; operator retrieval and reduction remain separately owned.",
            "No gravity/frame compatibility, contact-state admissibility, gauge, structural acceptance, or physical behavior is established.",
        ],
        "native_calculix_solve_executed": False,
        "geometry_changed": False,
        "joint_accepted": False,
        "producer_sha256": sha256(Path(__file__).resolve()),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--exercise-zero-budget-stop", action="store_true")
    args = parser.parse_args()
    if args.exercise_zero_budget_stop:
        case = source_cases()[0]
        result = enumerate_masks(case, time.monotonic() - 1.0)
        assert result["classification"] == "BUDGET_OR_SOLVER_STOP"
        assert not result["all_binary_masks_proven_exhausted"]
        assert result["stop_reason"] == "global_wall_budget_exhausted"
        assert result["candidate_masks"] == []
        print("PASS_EXPLICIT_ZERO_BUDGET_STOP_NO_COMPLETENESS_CLAIM")
        return
    payload = json.dumps(produce(), indent=2, sort_keys=True, allow_nan=False) + "\n"
    if args.verify:
        assert OUTPUT.read_text() == payload, "known-answer.json is stale; regenerate and review"
        print("PASS_TINY_COUPLED_INDICATOR_SELECTOR_KNOWN_ANSWER")
    else:
        OUTPUT.write_text(payload)
        print(f"Wrote {OUTPUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
