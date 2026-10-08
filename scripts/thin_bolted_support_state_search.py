"""Search whole-foot centroid support masks using the frozen fixed-branch laws.

Only the discrete support traversal changes. Each branch uses the original
incremental engine, contacts and springs, with one prescribed centroid mask.
A repeated feedback mask selects an unvisited mask; it is not evidence that
the conditional support law has no fixed point. No historical q is accepted.
"""

from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
from unittest.mock import patch

import numpy as np
from scipy.sparse import vstack

from scripts import thin_bolted_frame_mechanics as frame
from scripts import thin_bolted_incremental_step as incremental

INCREMENTAL_SHA256 = "3a3c794bb38352f1cc34d4c736a0812c14a53021d484549dc61d0a634cf83489"
LOADED_PRODUCER_SHA256 = frame.sha(Path(__file__))
FROZEN_INCREMENTAL_SOLVE = incremental.compatible_contact_solve
METHOD = "nonrepeating-whole-foot-centroid-mask-search"
FLOOR_ACTIVATION_THRESHOLD_N = 1e-7


def source_pins():
    pins = incremental.source_pins()
    if pins["scripts/thin_bolted_incremental_step.py"] != INCREMENTAL_SHA256:
        raise ValueError("preserve the frozen incremental branch engine")
    pins[str(Path(__file__).relative_to(frame.ROOT))] = LOADED_PRODUCER_SHA256
    if any(frame.sha(frame.ROOT / name) != digest for name, digest in pins.items()):
        raise ValueError("support-search source differs from its loaded bytes")
    return pins


def _hosts(contacts, tangents):
    hosts = sorted({row["first"] for row in contacts if row["kind"] == "floor_normal"})
    if not 1 <= len(hosts) <= 8:
        raise ValueError("one through eight original physical floor hosts required")
    if ({row["first"] for row in tangents} != set(hosts)
            or any(row["kind"] != "floor_tangent" for row in tangents)
            or any(sum(row["first"] == host for row in tangents) != 2 for host in hosts)):
        raise ValueError("exactly two original centroid tangent rows per floor host required")
    return hosts


def _enabled(hosts, mask):
    return [host for i, host in enumerate(hosts) if mask & (1 << i)]


def _mask_id(hosts, mask):
    return "centroid-mask-" + "".join("1" if mask & (1 << i) else "0" for i in range(len(hosts)))


def _next_mask(current, demanded, visited, total):
    if demanded is not None and demanded not in visited:
        return demanded, "unvisited original whole-foot feedback"
    for i in range(total.bit_length() - 1):
        neighbor = current ^ (1 << i)
        if neighbor not in visited:
            return neighbor, "unvisited one-host neighbor after stopped feedback"
    for mask in range(total):
        if mask not in visited:
            return mask, "deterministic unvisited-mask fallback"
    return None, "all masks visited"


def _fixed_branch(K, applied, groups, contacts, tangents, enabled, max_iterations, warm_q):
    """Disable only legacy mask feedback, preserving all physical operator rows.

    The frozen engine keys its outer update solely on kind == floor_normal.
    Internal copies relabel those metadata fields for this one call; B, k,
    order, port identity and physical hosts remain the original objects.
    The caller's original rows feed fresh force recovery and all body audits.
    """
    internal = [{**row, "kind": "fixed_pattern_floor_normal"}
                if row["kind"] == "floor_normal" else row for row in contacts]
    selected = [row for row in tangents if row["first"] in enabled]
    trace = []
    original_fields = incremental.ORIGINAL_FIELDS

    def fields(*args, **kwargs):
        result = original_fields(*args, **kwargs)
        if kwargs.get("tangent"):
            trace.append(sum(row["kind"] == "floor_normal" and force > 0.
                             for row, force in zip(contacts, result[4], strict=True)))
        return result

    with patch.object(incremental, "ORIGINAL_FIELDS", fields):
        response = FROZEN_INCREMENTAL_SOLVE(K, applied, groups, internal, selected,
                                          max_iterations=max_iterations, warm_q=warm_q)
    if response.get("floor_pattern_iterations", 1) != 1 or response.get("nonbearing_no_slip_removed"):
        raise ValueError("fixed branch engine changed the requested support mask")
    for row in response["iteration_history"]:
        row["active_floor_ports"] = int(trace[row["iteration"]])
    return response


def _fresh_fields(K, applied, groups, contacts, tangents, enabled, q):
    linear = K.copy()
    for row in tangents:
        if row["first"] in enabled:
            linear += row["stiffness"] * (row["B"].T @ row["B"])
    C = vstack([row["B"] for row in contacts], format="csr")
    ck = np.array([row["stiffness"] for row in contacts])
    return incremental.ORIGINAL_FIELDS(linear, applied, groups, C, ck, q)


def compatible_contact_solve(K, applied, groups, contacts, tangents, max_iterations=300, *,
                             mask_budget=64, warm_q=None, branch_observer=None):
    """Find an original-law support fixed point within a finite branch budget.

    A fresh preceding branch q may initialize the next branch; its equilibrium
    and actions never transfer. Success supplies a candidate field for the
    existing independent body/global/export gates, not structural acceptance.
    Exhaustion or unresolved branches never establish physical instability or
    nonexistence of a fixed point. Observers receive detached small dictionaries.
    """
    source_pins()
    hosts = _hosts(contacts, tangents)
    total = 1 << len(hosts)
    if (type(mask_budget) is not int or not 1 <= mask_budget <= total
            or type(max_iterations) is not int or max_iterations <= 0):
        raise ValueError("positive fixed-branch iteration and finite mask budgets required")
    if warm_q is not None:
        raise ValueError("historical or external q is not an authorized search initialization")
    diagnostics = {"schema": "thin_bolted_support_state_search/v1", "method": METHOD,
                   "floor_activation_threshold_n": FLOOR_ACTIVATION_THRESHOLD_N,
                   "host_order": hosts, "mask_budget": mask_budget, "total_possible_masks": total,
                   "tested_masks": [], "accepted_pattern_index": None,
                   "accepted_enabled_centroid_xy_hosts": None, "accepted_disabled_centroid_xy_hosts": None,
                   "final_mask_id": None, "final_q_canonical_sha256": None,
                   "all_masks_visited": False, "complete_enumeration": False, "no_fixed_point_proven": False,
                   "old_field_initialization_used": False, "physical_laws_changed": False,
                   "near_threshold_diagnostic_is_a_normal_force_error_bound": False,
                   "body_global_and_export_admission_required": True}
    history, visited = [], set()
    current, choice = total - 1, "original all-host initial mask"
    guess, last_response = None, {}
    accepted_steps, rejected_trials, maximum_damping = 0, 0, 0.

    def notify(event):
        if branch_observer is not None:
            branch_observer(copy.deepcopy(event))

    for pattern_index in range(mask_budget):
        if current in visited:
            raise ValueError("support search attempted a repeated mask")
        visited.add(current)
        enabled = _enabled(hosts, current)
        disabled = sorted(set(hosts) - set(enabled))
        row = {"pattern_index": pattern_index, "mask_id": _mask_id(hosts, current),
               "enabled_centroid_xy_hosts": enabled, "disabled_centroid_xy_hosts": disabled,
               "selection_reason": choice, "initialization_from_previous_fresh_branch_only": guess is not None}
        notify({"phase": "branch_start", **row})
        result = _fixed_branch(K, applied, groups, contacts, tangents, set(enabled), max_iterations, guess)
        last_response = result
        accepted_steps += result["accepted_numerical_steps"]
        rejected_trials += result["rejected_numerical_trials"]
        maximum_damping = max(maximum_damping, result["maximum_transient_scaled_step_regularization"])
        for entry in result["iteration_history"]:
            history.append({**entry, "floor_pattern": pattern_index})
        q = result.get("q") if result["converged"] else result.get("diagnostic_last_q")
        demanded = None
        row.update(fixed_branch_converged=False, self_consistent=False,
                   fresh_original_gradient_inf_n=None, floor_normal_force_n_by_host=None,
                   demanded_enabled_centroid_xy_hosts=None, near_threshold_diagnostic_hosts=[],
                   termination=result["termination"])
        if q is not None:
            q = np.asarray(q, dtype=float)
            if q.shape != (K.shape[0],) or not np.isfinite(q).all():
                raise ValueError("branch diagnostic q must be finite with unchanged degrees of freedom")
            gradient, energy, _, forces, normal, displacement = _fresh_fields(
                K, applied, groups, contacts, tangents, set(enabled), q)
            residual = float(abs(gradient).max())
            normals = dict.fromkeys(hosts, 0.)
            for contact, force in zip(contacts, normal, strict=True):
                if contact["kind"] == "floor_normal":
                    normals[contact["first"]] += float(force)
            demanded = sum(1 << i for i, host in enumerate(hosts)
                           if normals[host] > FLOOR_ACTIVATION_THRESHOLD_N)
            fixed = bool(result["converged"] and np.isfinite(residual)
                         and residual < frame.GENERALIZED_RESIDUAL_TOLERANCE_N)
            row.update(fixed_branch_converged=fixed, fresh_original_gradient_inf_n=residual,
                       floor_normal_force_n_by_host=normals,
                       demanded_enabled_centroid_xy_hosts=_enabled(hosts, demanded),
                       self_consistent=bool(fixed and current == demanded),
                       disabled_xy_force_exactly_zero=True,
                       disabled_xy_force_n_by_host={host: [0., 0.] for host in disabled},
                       near_threshold_diagnostic_hosts=[host for host in hosts
                           if abs(normals[host] - FLOOR_ACTIVATION_THRESHOLD_N)
                           <= frame.GENERALIZED_RESIDUAL_TOLERANCE_N])
            guess = q.copy()
            last_response = {**result, "gradient_inf_n": residual, "potential_energy_nmm": float(energy)}
        else:
            guess = None
        diagnostics["tested_masks"].append(row)
        diagnostics["all_masks_visited"] = len(visited) == total
        diagnostics["complete_enumeration"] = (diagnostics["all_masks_visited"]
            and all(item["fixed_branch_converged"] for item in diagnostics["tested_masks"]))
        notify({"phase": "branch_end", **row})
        if row["self_consistent"]:
            diagnostics.update(accepted_pattern_index=pattern_index,
                               accepted_enabled_centroid_xy_hosts=enabled,
                               accepted_disabled_centroid_xy_hosts=disabled,
                               final_mask_id=row["mask_id"],
                               final_q_canonical_sha256=hashlib.sha256(json.dumps(
                                   q.tolist(), sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest())
            source_pins()
            return {**result, "q": q, "connector_local_force_n": forces,
                    "normal_contact_force_n": normal, "normal_contact_displacement_mm": displacement,
                    "gradient_inf_n": residual, "potential_energy_nmm": float(energy),
                    "nonbearing_no_slip_removed": disabled, "floor_pattern_iterations": len(visited),
                    "iteration_history": history, "accepted_numerical_steps": accepted_steps,
                    "rejected_numerical_trials": rejected_trials,
                    "maximum_transient_scaled_step_regularization": maximum_damping,
                    "support_state_search_v1": diagnostics, "numerical_step_strategy": METHOD,
                    "termination": "original constitutive equilibrium and same-state whole-foot support mask converged"}
        current, choice = _next_mask(current, demanded if row["fixed_branch_converged"] else None, visited, total)
        if current is None:
            break
    source_pins()
    return {"converged": False,
            "termination": "support-mask search exhausted" if current is None else "support-mask search budget",
            "gradient_inf_n": last_response.get("gradient_inf_n"),
            "potential_energy_nmm": last_response.get("potential_energy_nmm"),
            "diagnostic_last_q": guess, "diagnostic_last_q_is_a_converged_or_accepted_force_field": False,
            "generalized_residual_tolerance_n": frame.GENERALIZED_RESIDUAL_TOLERANCE_N,
            "physical_residual_uses_unmodified_laws": True,
            "original_force_tolerance_or_physical_laws_changed": False,
            "floor_pattern_iterations": len(visited), "iteration_history": history,
            "accepted_numerical_steps": accepted_steps, "rejected_numerical_trials": rejected_trials,
            "maximum_transient_scaled_step_regularization": maximum_damping,
            "support_state_search_v1": diagnostics, "numerical_step_strategy": METHOD}
