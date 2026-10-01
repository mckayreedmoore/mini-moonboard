"""Review one frozen same-case zero-gap active-set continuation; never launches."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
from pathlib import Path

from fea import horizontal_panel_frame as frame
from fea.wood_joint_reduced_native import LEDGER, ROOT, digest, verify

TOLERANCE_MM = 1.0e-7
DAT_TRANSITION_METHOD = "dat-displacement-rounding-intervals/v1"
RF_TRANSITION_METHOD = "rf-opening-interval-for-ambiguous-active-normals/v1"
TRANSITION_FIELDS = {
    "scope", "cycle_index", "current_branch", "previous_trial_freeze_sha256",
    "previous_response_sha256", "previous_execution_sha256", "previous_trial_run_id",
    "previous_postrun_review_sha256", "trial_active_groups", "trial_radial_states",
    "radial_clearance_reference_loads", "active_set_transition_method",
    "active_set_transition",
}


def _json(path: Path):
    return json.loads(path.read_text())


def _check(condition, message):
    if not condition:
        raise ValueError(message)


def _authorized_review_binding(current: Path, authorization: dict, freeze_sha: str):
    """Resolve the exact review artifact recorded by the parent launcher."""
    relative = authorization.get("independent_review")
    _check(isinstance(relative, str) and relative,
           "Launch authorization does not name its review artifact")
    review_path = (ROOT / relative).resolve()
    _check(review_path.is_relative_to(ROOT) and review_path.is_file(),
           "Authorized review artifact is missing or outside the repository")
    review_sha = digest(review_path)
    _check(authorization.get("independent_review_sha256") == review_sha,
           "Launch authorization review artifact hash differs")
    review = _json(review_path)
    _check(review.get("input_freeze_sha256") == freeze_sha
           and review.get("ready_for_scoped_native_run") is True,
           "Authorized review artifact is not ready for this exact freeze")

    internal_review_path = (current / "review.json").resolve()
    if review_path != internal_review_path:
        provenance = review.get("provenance", {})
        _check(internal_review_path.is_file()
               and provenance.get("launch_bound_review_path")
                   == str(internal_review_path.relative_to(ROOT))
               and provenance.get("launch_bound_review_sha256") == digest(internal_review_path),
               "External exact-freeze review does not bind the transition review")
    return review_path, review_sha


def _cycle_index(path: Path) -> int:
    match = re.fullmatch(r"cycle-(\d+)(?:-[A-Za-z0-9_.-]+)?", path.name)
    if not match:
        raise ValueError("Trial directory must be named cycle-NN with an optional metadata suffix")
    return int(match.group(1))


def check_active_set_history(previous: Path, candidate_active: set[str]) -> dict:
    """Verify the candidate active set has not appeared in an earlier consumed branch."""
    previous = Path(previous).resolve()
    _check(previous.is_relative_to(ROOT), "Trial history must remain inside the repository")
    previous_model = _json(previous / "model.json")
    previous_index = _cycle_index(previous)
    ledger = _json(LEDGER)
    checked = []

    for row in ledger.get("runs", []):
        if row.get("state") != "consumed_terminal" or row.get("launches_consumed") != 1:
            continue
        relative = Path(row.get("attempt_directory", ""))
        trial = (ROOT / relative).resolve()
        if not trial.is_relative_to(ROOT) or trial.parent != previous.parent:
            continue
        try:
            index = _cycle_index(trial)
        except ValueError:
            continue
        if index > previous_index:
            continue
        model_path = trial / "model.json"
        freeze_path = trial / "freeze.json"
        execution_path = trial / "execution.json"
        if not (model_path.is_file() and freeze_path.is_file() and execution_path.is_file()):
            raise ValueError("Consumed branch lacks its frozen history files: " + row["run_id"])
        packet = _json(freeze_path)
        execution = _json(execution_path)
        model = _json(model_path)
        if (row.get("execution_record_sha256") != digest(execution_path)
                or row.get("input_freeze_sha256") != digest(freeze_path)
                or packet.get("files_sha256", {}).get("model.json") != digest(model_path)
                or execution.get("run_id") != row.get("run_id")
                or execution.get("returncode") != 0
                or execution.get("container_confirmed_terminal") is not True):
            raise ValueError("Consumed branch history hashes or execution do not verify: " + row["run_id"])
        if (model.get("case_id") != previous_model.get("case_id")
                or model.get("scenario") != previous_model.get("scenario")
                or not isinstance(model.get("trial_active_groups"), list)):
            continue
        prior_active = set(model["trial_active_groups"])
        checked.append(row["run_id"])
        if prior_active == set(candidate_active):
            raise ValueError("Candidate active set repeats consumed branch " + row["run_id"])

    return {
        "status": "PASS_NO_REPEATED_ACTIVE_SET",
        "prior_consumed_branch_count": len(checked),
        "prior_run_ids_checked": sorted(checked),
    }


def _normalized_model(model):
    """Remove only documented iteration metadata and the branch active bits."""
    normalized = {key: value for key, value in model.items() if key not in TRANSITION_FIELDS}
    normalized["springs"] = [
        {key: value for key, value in row.items() if key != "active"}
        for row in model["springs"]
    ]
    return normalized


def _rf_active_normal_opening_interval(model, report, name, spring):
    """Recover one active zero-gap normal opening from its audited RF interval."""
    audit = report.get("force_output_recovery_audit", {})
    _check(audit.get("status") == "PASS_ISOLATED_SPRING_RF_ACTION_REACTION_AND_KDU_INTERVALS"
           and audit.get("all_spring_rf_action_reaction_passed") is True
           and audit.get("all_active_spring_rf_matches_kdu_print_intervals") is True,
           "RF contact transition requires a passing isolated-spring recovery audit")

    scenario = model.get("scenario", {})
    _check(scenario.get("bolt_gap_factor") == 0.0
           and model.get("trial_radial_states") == {}
           and not report.get("radial_clearance"),
           "RF opening inversion is limited to the zero-gap, no-radial-state branch")
    _check(spring.get("active") is True and int(spring.get("dof", -1)) == 1,
           "RF opening inversion requires an active scalar normal spring on DOF 1")
    stiffness = float(spring.get("stiffness_n_per_mm", float("nan")))
    _check(math.isfinite(stiffness) and stiffness > 0.0,
           "RF opening inversion requires positive finite spring stiffness")

    owner = model.get("connection_ownership", {}).get(name)
    force = report.get("physical_connection_forces", {}).get(name)
    _check(isinstance(owner, dict) and isinstance(force, dict),
           "Ambiguous active normal lacks source-owned RF force recovery: " + name)
    normal = owner.get("scalar_normal")
    force_vector = force.get("force_on_first_xyz_n")
    force_radius = force.get("force_rounding_radius_xyz_n")
    _check(isinstance(normal, list) and len(normal) == 3
           and isinstance(force_vector, list) and len(force_vector) == 3
           and isinstance(force_radius, list) and len(force_radius) == 3,
           "RF opening inversion requires three-component force, radius and normal vectors: " + name)
    normal = [float(value) for value in normal]
    force_vector = [float(value) for value in force_vector]
    force_radius = [float(value) for value in force_radius]
    _check(all(math.isfinite(value) for value in normal + force_vector + force_radius)
           and all(value >= 0.0 for value in force_radius),
           "RF opening inversion contains a non-finite force interval: " + name)
    normal_length = math.sqrt(sum(value * value for value in normal))
    _check(math.isclose(normal_length, 1.0, rel_tol=0.0, abs_tol=1.0e-8),
           "RF opening inversion requires a unit physical normal: " + name)
    _check(force.get("first") == owner.get("first")
           and force.get("second") == owner.get("second")
           and len(force.get("scalar_normal", [])) == 3
           and all(math.isclose(float(a), float(b), rel_tol=0.0, abs_tol=1.0e-10)
                   for a, b in zip(force["scalar_normal"], normal, strict=True)),
           "RF physical force ownership or normal differs from the frozen model: " + name)

    components = audit.get("components", [])
    matches = [row for row in components if row.get("spring_name") == name]
    _check(len(matches) == 1, "RF recovery audit lacks a unique spring component: " + name)
    component = matches[0]
    _check(component.get("active") is True
           and component.get("spring_element") == spring.get("element")
           and component.get("nodes_first_second") == spring.get("nodes")
           and component.get("dof") == 1
           and component.get("rf_action_reaction_passed") is True
           and component.get("rf_matches_kdu_print_intervals") is True,
           "RF audit component does not verify this active contact spring: " + name)

    scalar_force = sum(a * b for a, b in zip(normal, force_vector, strict=True))
    scalar_radius = sum(abs(a) * b for a, b in zip(normal, force_radius, strict=True))
    _check(math.isclose(scalar_force, float(component["rf_force_on_first_n"]),
                        rel_tol=0.0, abs_tol=1.0e-10)
           and math.isclose(scalar_radius, float(component["rf_force_rounding_radius_n"]),
                            rel_tol=0.0, abs_tol=1.0e-12),
           "Physical RF force interval differs from the audited scalar endpoint result: " + name)
    opening = -scalar_force / stiffness
    radius = scalar_radius / stiffness
    return opening, radius, {
        "scalar_force_on_first_n": scalar_force,
        "scalar_force_rounding_radius_n": scalar_radius,
        "stiffness_n_per_mm": stiffness,
        "opening_mm": opening,
        "opening_rounding_radius_mm": radius,
        "interval_lower_mm": opening - radius,
        "interval_upper_mm": opening + radius,
    }


def _validate_rf_transition_context(model, report):
    """Require the reviewed zero-gap branch and complete spring RF audit."""
    _check(model.get("scenario", {}).get("bolt_gap_factor") == 0.0
           and model.get("trial_radial_states") == {}
           and not report.get("radial_clearance"),
           "RF opening inversion is limited to the zero-gap, no-radial-state branch")
    audit = report.get("force_output_recovery_audit", {})
    _check(audit.get("status") == "PASS_ISOLATED_SPRING_RF_ACTION_REACTION_AND_KDU_INTERVALS"
           and audit.get("all_spring_rf_action_reaction_passed") is True
           and audit.get("all_active_spring_rf_matches_kdu_print_intervals") is True
           and audit.get("all_inactive_spring_rf_matches_zero_within_print_intervals") is True,
           "RF opening inversion requires a complete passing isolated-spring recovery audit")
    _check(isinstance(report.get("physical_connection_forces"), dict),
           "RF opening inversion requires recovered physical connector forces")


def derive_next_active_set(model, report, dat_text, *, use_rf_opening_intervals=False):
    """Recompute zero-gap branches, optionally refining ambiguous active normals with audited RF."""
    if use_rf_opening_intervals:
        _validate_rf_transition_context(model, report)
    springs = {row["name"]: row for row in model["springs"]
               if row.get("bearing_closed_assumption")
               and not row.get("tension_only_assumption")
               and not row["name"].endswith("_friction")}
    tension_springs = {row["name"]: row for row in model["springs"]
                       if row.get("tension_only_assumption")}
    _check(len(springs) == len([r for r in model["springs"]
                                if r.get("bearing_closed_assumption")
                                and not r.get("tension_only_assumption")
                                and not r["name"].endswith("_friction")]),
           "Duplicate contact spring names")
    _check(len(tension_springs) == len([r for r in model["springs"] if r.get("tension_only_assumption")]),
           "Duplicate tension spring names")

    blocks = frame.panel_kernel.read_blocks(dat_text)
    displacement = blocks["displacements"]
    rounding = frame.displacement_roundoff(dat_text)
    expected = set()
    minima = {"normal_margin_minus_rounding_mm": float("inf"),
              "tension_margin_minus_rounding_mm": float("inf")}
    ambiguous = {"normal": [], "tension": []}
    ambiguous_rows = []
    dat_ambiguous_normal_names = []
    rf_opening_resolved_rows = []

    bearings = report.get("bearings", [])
    _check({row.get("name") for row in bearings} == set(springs),
           "Response normal-contact inventory differs from frozen switchable normals")
    for row in bearings:
        spring = springs[row["name"]]
        _check(row.get("active") is spring.get("active"),
               "Response normal active bit differs from previous frozen model: " + row["name"])
        first, second = map(int, spring["nodes"])
        dof = int(spring["dof"]) - 1
        delta = float(displacement[second][dof] - displacement[first][dof])
        opening = -delta
        uncertainty = float(rounding[first][dof] + rounding[second][dof])
        _check(abs(float(row["opening_mm"]) - opening) <= 1.0e-12,
               "Response contact opening disagrees with printed DAT displacement: " + row["name"])
        threshold = TOLERANCE_MM if row["active"] else -TOLERANCE_MM
        margin = abs(opening - threshold) - uncertainty
        minima["normal_margin_minus_rounding_mm"] = min(
            minima["normal_margin_minus_rounding_mm"], margin)
        dat_center_next_active = (opening <= TOLERANCE_MM if row["active"]
                                  else opening < -TOLERANCE_MM)
        next_active = row["active"] if margin <= 0. else dat_center_next_active
        if margin <= 0.:
            dat_ambiguous_normal_names.append(row["name"])
            selected_center = dat_center_next_active
            selected_opening = opening
            selected_radius = uncertainty
            selected_source = "DAT displacement interval"
            rf_interval = None
            if use_rf_opening_intervals and row["active"]:
                rf_opening, rf_radius, rf_interval = _rf_active_normal_opening_interval(
                    model, report, row["name"], spring)
                rf_lower, rf_upper = rf_interval["interval_lower_mm"], rf_interval["interval_upper_mm"]
                selected_center = rf_opening <= TOLERANCE_MM
                selected_opening = rf_opening
                selected_radius = rf_radius
                selected_source = "audited RF-derived opening interval"
                if rf_upper <= TOLERANCE_MM:
                    next_active = True
                elif rf_lower > TOLERANCE_MM:
                    next_active = False
                else:
                    next_active = row["active"]
            resolved_by_rf = rf_interval is not None and (
                rf_interval["interval_upper_mm"] <= TOLERANCE_MM
                or rf_interval["interval_lower_mm"] > TOLERANCE_MM
            )
            evidence = {
                "kind": "normal", "name": row["name"],
                "previous_active": row["active"],
                "dat_center_rule_active": dat_center_next_active,
                "dat_opening_mm": opening,
                "dat_rounding_radius_mm": uncertainty,
                "center_rule_active": selected_center,
                "selected_center_rule_active": selected_center,
                "reviewed_next_active": next_active,
                "decision_threshold_mm": threshold,
                "decision_source": selected_source,
            }
            if rf_interval is not None:
                evidence["rf_interval"] = rf_interval
            if resolved_by_rf:
                rf_opening_resolved_rows.append(evidence)
            else:
                ambiguous["normal"].append(row["name"])
                evidence.update({
                    "opening_mm": selected_opening,
                    "rounding_radius_mm": selected_radius,
                    "interval_lower_mm": selected_opening - selected_radius,
                    "interval_upper_mm": selected_opening + selected_radius,
                })
                ambiguous_rows.append(evidence)
        if next_active:
            expected.add(row["name"])

    tension_rows = report.get("axial_tension", [])
    _check({row.get("name") for row in tension_rows} == set(tension_springs),
           "Response tension inventory differs from frozen switchable ties")
    for row in tension_rows:
        spring = tension_springs[row["name"]]
        _check(row.get("active") is spring.get("active"),
               "Response tension active bit differs from previous frozen model: " + row["name"])
        first, second = map(int, spring["nodes"])
        dof = int(spring["dof"]) - 1
        extension = float(displacement[second][dof] - displacement[first][dof])
        uncertainty = float(rounding[first][dof] + rounding[second][dof])
        _check(abs(float(row["extension_mm"]) - extension) <= 1.0e-12,
               "Response tie extension disagrees with printed DAT displacement: " + row["name"])
        threshold = -TOLERANCE_MM if row["active"] else TOLERANCE_MM
        margin = abs(extension - threshold) - uncertainty
        minima["tension_margin_minus_rounding_mm"] = min(
            minima["tension_margin_minus_rounding_mm"], margin)
        if margin <= 0.:
            ambiguous["tension"].append(row["name"])
        center_next_active = (extension >= -TOLERANCE_MM if row["active"]
                              else extension > TOLERANCE_MM)
        next_active = row["active"] if margin <= 0. else center_next_active
        if margin <= 0.:
            ambiguous_rows.append({"kind": "tension", "name": row["name"],
                "previous_active": row["active"], "center_rule_active": center_next_active,
                "reviewed_next_active": next_active, "extension_mm": extension,
                "rounding_radius_mm": uncertainty, "interval_lower_mm": extension - uncertainty,
                "interval_upper_mm": extension + uncertainty,
                "decision_threshold_mm": threshold})
        if next_active:
            expected.add(row["name"])

    _check(not report.get("radial_clearance"), "Zero-gap iteration unexpectedly reports radial states")
    floor_normals = {name for name, owner in model.get("connection_ownership", {}).items()
                     if owner.get("role") == "floor_normal"}
    floor_tangents = {name for name, owner in model.get("connection_ownership", {}).items()
                      if owner.get("role") == "assumed_no_slip_floor"}
    _check(floor_tangents == {name + "_friction" for name in floor_normals},
           "Floor normal/tangent ownership is not a one-to-one paired inventory")
    _check(floor_normals <= set(springs), "Floor normal is missing from contact response inventory")
    expected.update(name + "_friction" for name in floor_normals if name in expected)
    if minima["normal_margin_minus_rounding_mm"] == float("inf"):
        minima["normal_margin_minus_rounding_mm"] = None
    if minima["tension_margin_minus_rounding_mm"] == float("inf"):
        minima["tension_margin_minus_rounding_mm"] = None
    return expected, {
        "normal_rows": len(bearings), "tension_rows": len(tension_rows),
        "normal_active_next": sum(name in expected for name in springs),
        "tension_active_next": sum(name in expected for name in tension_springs),
        "paired_floor_tangent_groups_next": sum(name + "_friction" in expected for name in floor_normals),
        "threshold_rounding_ambiguous_normal_count": len(ambiguous["normal"]),
        "threshold_rounding_ambiguous_tension_count": len(ambiguous["tension"]),
        "dat_threshold_rounding_ambiguous_normal_count": len(dat_ambiguous_normal_names),
        "rf_opening_resolved_normal_count": len(rf_opening_resolved_rows),
        "rf_opening_resolution_rows": rf_opening_resolved_rows,
        "threshold_rounding_ambiguous_examples": {
            "normal": ambiguous["normal"][:5], "tension": ambiguous["tension"][:5]},
        "threshold_rounding_ambiguous_rows": ambiguous_rows,
        "ambiguous_state_changes_suppressed": sum(
            row["previous_active"] != row["center_rule_active"] for row in ambiguous_rows),
        "ambiguous_state_policy": (
            "For DAT-ambiguous active zero-gap normal contacts, use an audited RF-derived opening interval when available; otherwise retain the previous state. Ties and unsupported contacts use DAT displacement intervals."
            if use_rf_opening_intervals else
            "Retain the previous active state if the DAT displacement interval overlaps its branch-switch threshold"
        ),
        **minima,
        "decision_tolerance_mm": TOLERANCE_MM,
        "method": RF_TRANSITION_METHOD if use_rf_opening_intervals else DAT_TRANSITION_METHOD,
        "rounding_method": (
            "Half-last-place DAT displacement intervals; for ambiguous eligible active normal contacts, project audited endpoint-RF force radii onto the unit contact normal and divide -F_normal by the frozen spring stiffness."
            if use_rf_opening_intervals else
            "Half-last-place interval from each printed endpoint displacement component"
        ),
    }


def _deck_cards(text):
    cards = []
    current = []
    for line in text.splitlines(keepends=True):
        if line.startswith("*"):
            if current:
                cards.append(current)
            current = [line]
        elif current:
            current.append(line)
    if current:
        cards.append(current)
    return cards


def _spring_cards(text):
    elements, properties = {}, {}
    other = []
    for card in _deck_cards(text):
        header = card[0].strip()
        upper = header.upper()
        if upper.startswith("*ELEMENT,TYPE=SPRING2"):
            match = re.search(r"(?:^|,)\s*ELSET\s*=\s*([^,\s]+)", header, re.IGNORECASE)
            _check(match is not None, "Spring element card lacks ELSET")
            group = match.group(1)
            _check(group not in elements, "Duplicate spring element ELSET: " + group)
            rows = [[cell.strip() for cell in line.split(",")]
                    for line in card[1:] if line.strip()]
            _check(len(rows) == 1 and len(rows[0]) >= 3, "Malformed scalar spring element card: " + group)
            elements[group] = (int(rows[0][0]), int(rows[0][1]), int(rows[0][2]))
        elif upper.startswith("*SPRING"):
            match = re.search(r"(?:^|,)\s*ELSET\s*=\s*([^,\s]+)", header, re.IGNORECASE)
            _check(match is not None, "Spring property card lacks ELSET")
            group = match.group(1)
            _check(group not in properties, "Duplicate spring property ELSET: " + group)
            rows = [[cell.strip() for cell in line.split(",")]
                    for line in card[1:] if line.strip()]
            _check(len(rows) == 2 and len(rows[0]) == 2 and len(rows[1]) == 1,
                   "Malformed scalar spring property card: " + group)
            properties[group] = (int(rows[0][0]), int(rows[0][1]), float(rows[1][0]))
        else:
            other.append("".join(card))
    return elements, properties, other


def _check_decks(previous, current, previous_model, current_model, active):
    previous_text = (previous / "model.inp").read_text()
    current_text = (current / "model.inp").read_text()
    old_elements, old_properties, old_other = _spring_cards(previous_text)
    new_elements, new_properties, new_other = _spring_cards(current_text)
    _check(old_other == new_other,
           "Non-spring deck cards changed; loads, constraints, or structural inputs may differ")
    previous_groups = {}
    for row in previous_model["springs"]:
        previous_groups.setdefault(row["group"], []).append(row)
    _check(all(len({bool(row["active"]) for row in rows}) == 1
               for rows in previous_groups.values()),
           "Previous spring ELSET has mixed active states")
    previous_active_groups = {group for group, rows in previous_groups.items()
                              if rows[0]["active"]}
    _check(set(old_elements) == previous_active_groups
           and set(old_properties) == previous_active_groups,
           "Previous deck spring element sets do not match the frozen model")
    for group in previous_active_groups:
        rows = previous_groups[group]
        _check(len(rows) == 1, "Expected one scalar row per previous spring ELSET: " + group)
        row = rows[0]
        _check(old_elements[group] == (int(row["element"]), int(row["nodes"][0]), int(row["nodes"][1])),
               "Previous deck spring element differs from its model: " + group)
        dof1, dof2, stiffness = old_properties[group]
        _check((dof1, dof2) == (int(row["dof"]), int(row["dof"]))
               and abs(stiffness - float(row["stiffness_n_per_mm"]))
               <= max(1.0e-12, abs(float(row["stiffness_n_per_mm"])) * 1.0e-12),
               "Previous deck spring property differs from its model: " + group)

    rows_by_group = {}
    for row in current_model["springs"]:
        rows_by_group.setdefault(row["group"], []).append(row)
    expected_groups = set()
    for group, rows in rows_by_group.items():
        group_active = {not row.get("bearing_closed_assumption") or row["name"] in active
                        for row in rows}
        _check(len(group_active) == 1, "One spring ELSET has mixed active states: " + group)
        is_active = group_active.pop()
        model_rows = current_model["elements"]
        for row in rows:
            element = model_rows.get(str(row["element"]))
            _check(element is not None and element[0] == "SPRING2"
                   and list(map(int, element[1])) == list(map(int, row["nodes"]))
                   and element[2] == group,
                   "Spring inventory differs from frozen element topology: " + row["name"])
        if is_active:
            expected_groups.add(group)
    _check(set(new_elements) == expected_groups,
           "Deck spring element omissions do not match recomputed active groups")
    _check(set(new_properties) == expected_groups,
           "Deck spring property omissions do not match recomputed active groups")
    for group in expected_groups:
        rows = rows_by_group[group]
        _check(len(rows) == 1, "Expected one scalar row per spring ELSET: " + group)
        row = rows[0]
        _check(new_elements[group] == (int(row["element"]), int(row["nodes"][0]), int(row["nodes"][1])),
               "Deck spring element endpoints differ from model: " + group)
        dof1, dof2, stiffness = new_properties[group]
        _check((dof1, dof2) == (int(row["dof"]), int(row["dof"]))
               and abs(stiffness - float(row["stiffness_n_per_mm"]))
               <= max(1.0e-12, abs(float(row["stiffness_n_per_mm"])) * 1.0e-12),
               "Deck spring DOF/stiffness differs from model: " + group)
    return {"non_spring_cards_identical": True,
            "previous_spring_element_sets": len(old_elements),
            "current_expected_spring_element_sets": len(expected_groups),
            "omitted_spring_element_sets": len(old_elements) - len(expected_groups)}


def _check_endpoint_isolation(model):
    endpoint_dofs = []
    for row in model["springs"]:
        for node in row["nodes"]:
            endpoint_dofs.append((int(node), int(row["dof"])))
    _check(len(endpoint_dofs) == len(set(endpoint_dofs)),
           "A scalar spring endpoint node/DOF is shared by another spring")
    equation_counts = {key: 0 for key in endpoint_dofs}
    for equation in model["equations"]:
        for node, dof, coefficient in equation:
            key = (int(node), int(dof))
            if key in equation_counts:
                equation_counts[key] += 1
    bad = [key for key, count in equation_counts.items() if count != 1]
    _check(not bad, "Every spring endpoint DOF must occur in exactly one MPC equation")
    fixed = set(map(int, model["fixed_nodes"]))
    _check(not fixed.intersection(node for node, _ in endpoint_dofs),
           "A spring endpoint node is also fixed")

    corrections = model.get("radial_clearance_reference_loads", [])
    _check(model.get("trial_radial_states") == {} and not corrections,
           "Zero-gap trial must have no radial clearance states or reference-load corrections")
    loads = {int(node): [float(value) for value in force]
             for node, force in model["loads"].items()}
    nonzero_endpoint_loads = {
        node: loads[node] for node, _ in endpoint_dofs
        if node in loads and any(abs(component) > 1.0e-12 for component in loads[node])
    }
    _check(not nonzero_endpoint_loads,
           "Zero-gap spring endpoints carry applied CLOADs outside radial-reference corrections")
    return {"spring_endpoint_dofs": len(endpoint_dofs),
            "unique_mpc_equation_occurrences": len(endpoint_dofs),
            "fixed_endpoint_nodes": 0,
            "radial_reference_correction_count": len(corrections),
            "nonzero_endpoint_cload_count": len(nonzero_endpoint_loads)}


def _check_prior_execution(previous, previous_packet, previous_model, current_packet):
    freeze_path = previous / "freeze.json"
    freeze_sha = digest(freeze_path)
    review_path = previous / "review.json"
    authorization_path = previous / "authorization.json"
    execution_path = previous / "execution.json"
    report_path = previous / "response.json"
    for required in (review_path, authorization_path, execution_path, report_path,
                     previous / "model.dat", previous / "native.stdout", previous / "native.stderr"):
        _check(required.is_file(), "Previous trial lacks required provenance/result: " + required.name)
    review = _json(review_path)
    authorization = _json(authorization_path)
    execution = _json(execution_path)
    report = _json(report_path)
    _check(review.get("input_freeze_sha256") == freeze_sha
           and review.get("ready_for_scoped_native_run") is True,
           "Previous native run lacks a passing exact-freeze pre-run review")
    authorized_review_path, authorized_review_sha = _authorized_review_binding(
        previous, authorization, freeze_sha
    )
    _check(authorization.get("input_freeze_sha256") == freeze_sha
           and authorization.get("native_execution_authorized") is True
           and authorization.get("parent_readiness") is True,
           "Previous execution authorization does not bind its review and freeze")
    _check(execution.get("run_id") == authorization.get("run_id")
           and execution.get("returncode") == 0
           and execution.get("container_confirmed_terminal") is True
           and execution.get("native_solve_executed") is True,
           "Previous native execution is not a terminal successful run")
    ledger = _json(LEDGER)
    matches = [row for row in ledger["runs"] if row.get("run_id") == execution["run_id"]]
    _check(len(matches) == 1, "Previous native execution is not uniquely registered in ledger")
    registered = matches[0]
    _check(registered.get("state") == "consumed_terminal"
           and registered.get("launches_consumed") == 1
           and registered.get("input_freeze_sha256") == freeze_sha
           and registered.get("execution_record_sha256") == digest(execution_path)
           and registered.get("authorization_sha256") == digest(authorization_path)
           and (ROOT / registered.get("attempt_directory", "")).resolve() == previous.resolve(),
           "Ledger does not bind one consumed terminal launch to this freeze and execution")
    outputs = execution.get("outputs_sha256", {})
    _check({"model.inp", "model.dat", "native.stdout", "native.stderr"} <= set(outputs),
           "Previous native execution lacks required output hashes")
    for name, expected in outputs.items():
        _check((previous / name).is_file() and digest(previous / name) == expected,
               "Previous native output hash mismatch: " + name)
    log = (previous / "native.stdout").read_text() + (previous / "native.stderr").read_text()
    _check("*ERROR" not in log.upper()
           and not any("WARNING" in line.upper() for line in log.splitlines()),
           "Previous native logs contain warnings or errors")
    _check(report.get("input_freeze_sha256") == freeze_sha
           and report.get("native_execution_verified") is True
           and report.get("native_solve_executed") is True
           and report.get("all_raw_equilibrium_passed") is True
           and report.get("all_interval_equilibrium_passed") is True
           and report.get("mpc_check_passed") is True
           and report.get("native_warnings") == []
           and report.get("mechanical_acceptance") is False,
           "Previous response lacks required provenance or numerical screening checks")
    recovery = report.get("force_output_recovery_audit", {})
    _check(recovery.get("status") == "PASS_ISOLATED_SPRING_RF_ACTION_REACTION_AND_KDU_INTERVALS"
           and recovery.get("all_spring_rf_action_reaction_passed") is True
           and recovery.get("all_active_spring_rf_matches_kdu_print_intervals") is True
           and recovery.get("all_inactive_spring_rf_matches_zero_within_print_intervals") is True,
           "Previous response lacks the isolated-spring RF recovery check")

    # Current freeze snapshots the response/postprocessor used to prepare the
    # next branch, allowing the prior post-run reassessment to be checked even
    # when its original freeze predates that response helper revision.
    pins = current_packet["source_sha256"]
    expected_sources = {
        previous / "freeze.json": freeze_sha,
        previous / "model.json": digest(previous / "model.json"),
        review_path: digest(review_path), execution_path: digest(execution_path),
        report_path: digest(report_path),
        previous.parent / "prepared-model.pkl": digest(previous.parent / "prepared-model.pkl"),
    }
    for path, expected in expected_sources.items():
        relative = str(path.resolve().relative_to(ROOT))
        _check(pins.get(relative) == expected,
               "Current freeze does not pin the required prior source/checkpoint: " + relative)
    response_path = "fea/wood_joint_reduced_response.py"
    force_path = "fea/wood_joint_reduced_force_output.py"
    _check(report.get("postprocessor_sha256") == pins.get(response_path)
           and report.get("force_output_helper_sha256") == pins.get(force_path),
           "Prior response postprocessor/helper hashes differ from the current freeze pins")
    _check(current_packet["source_sha256"].get(response_path)
           == previous_packet["source_sha256"].get(response_path)
           or report.get("postprocessor_sha256") == current_packet["source_sha256"].get(response_path),
           "Response source is not tied to either the prior freeze or current branch snapshot")
    return {
        "previous_freeze_sha256": freeze_sha,
        "previous_review_sha256": digest(review_path),
        "previous_authorization_sha256": digest(authorization_path),
        "previous_execution_sha256": digest(execution_path),
        "previous_response_sha256": digest(report_path),
        "previous_run_id": execution["run_id"],
        "launch_bound_review_path": str(authorized_review_path.relative_to(ROOT)),
        "launch_bound_review_sha256": authorized_review_sha,
        "transition_review_sha256": digest(review_path),
        "ledger_state": registered["state"],
        "output_hashes_verified": len(outputs),
        "force_output_recovery_status": recovery["status"],
    }


def review_transition(previous: Path, current: Path, *, write=True, allow_authorized=False):
    previous = previous.resolve()
    current = current.resolve()
    _check(previous.is_relative_to(ROOT) and current.is_relative_to(ROOT),
           "Trial directories must remain inside the repository")
    _check(previous.parent == current.parent and _cycle_index(current) == _cycle_index(previous) + 1,
           "Only an immediate same-attempt cycle-N to cycle-(N+1) transition is supported")
    if not allow_authorized:
        _check(not any((current / name).exists() for name in
                       ("authorization.json", "execution.json", "response.json")),
               "Current branch already has a native run; review only fresh unlaunched freezes")
    prior_review_path = current / "review.json"
    if prior_review_path.exists():
        prior_review = _json(prior_review_path)
        _check(prior_review.get("schema") == "wood_joint_reduced_trial_iteration_review/v1"
               and prior_review.get("input_freeze_sha256") == digest(current / "freeze.json"),
               "Refusing to overwrite a different or nonmatching review")

    previous_packet = verify(previous, check_live=False)
    # On the initial pre-run review, require the current checkout to equal the
    # freeze. A postauthorization audit instead verifies the retained source
    # snapshots; later coordinator edits must not invalidate a consumed freeze.
    current_packet = verify(current, check_live=not allow_authorized)
    old_freeze_sha = digest(previous / "freeze.json")
    current_freeze_sha = digest(current / "freeze.json")
    old_model = _json(previous / "model.json")
    model = _json(current / "model.json")
    _check(current_packet.get("native_solve_executed") is False
           and current_packet.get("mechanical_acceptance") is False,
           "Current freeze carries an invalid pre-run scope flag")
    _check(current_packet.get("candidate") == "compact-floor-flush-wood-joints-development"
           and current_packet.get("geometry_revision_id") == "led-clearance-2x6-runner-seated-blocks-v1"
           and model.get("case_id") == "a12-rear"
           and model.get("scenario", {}).get("bolt_gap_factor") == 0.0
           and model.get("scenario", {}).get("accessory_scenario_id") is None
           and model.get("scenario", {}).get("accessory_budget_kg") == 0.0
           and model.get("trial_radial_states") == {},
           "Verifier only supports the reviewed a12-rear, zero-gap, no-accessory, no-radial diagnostic")
    _check(current_packet.get("scope") == model.get("scope")
           and model.get("cycle_index") == _cycle_index(current)
           and model.get("current_branch", {}).get("active_group_count") == len(model["trial_active_groups"]),
           "Current freeze scope/cycle/active count metadata is inconsistent")
    _check(model.get("previous_trial_freeze_sha256") == old_freeze_sha
           and model.get("previous_response_sha256") == digest(previous / "response.json")
           and model.get("previous_execution_sha256") == digest(previous / "execution.json"),
           "Current branch metadata does not reference the immediate previous frozen response")
    _check(model.get("source_model_inputs_sha256") == old_model.get("source_model_inputs_sha256")
           and model.get("source_sha256") == old_model.get("source_sha256")
           and model.get("scenario") == old_model.get("scenario"),
           "Model input/source/scenario pins changed across active-set iteration")
    _check(_normalized_model(old_model) == _normalized_model(model),
           "Model topology, geometry, loads, equations, materials, stiffness, or ownership changed")
    for row in model["springs"]:
        expected_active = (not row.get("bearing_closed_assumption")
                           or row["name"] in set(model["trial_active_groups"]))
        _check(row.get("active") is expected_active,
               "Current model spring active bit disagrees with trial group: " + row["name"])

    prior = _check_prior_execution(previous, previous_packet, old_model, current_packet)
    transition_method = model.get("active_set_transition_method", DAT_TRANSITION_METHOD)
    _check(transition_method in (DAT_TRANSITION_METHOD, RF_TRANSITION_METHOD),
           "Current freeze names an unsupported active-set transition method")
    use_rf_opening_intervals = transition_method == RF_TRANSITION_METHOD
    if use_rf_opening_intervals:
        _check(_cycle_index(previous) == 8 and _cycle_index(current) == 9,
               "RF opening interval transition is currently limited to c08-to-c09")
    expected, transition = derive_next_active_set(
        old_model, _json(previous / "response.json"), (previous / "model.dat").read_text(),
        use_rf_opening_intervals=use_rf_opening_intervals)
    _check(transition["ambiguous_state_changes_suppressed"] == 0,
           "Previous response has a threshold ambiguity that suppresses a selected state change")
    if use_rf_opening_intervals:
        _check(transition["dat_threshold_rounding_ambiguous_normal_count"] == 2
               and transition["rf_opening_resolved_normal_count"] == 2
               and transition["threshold_rounding_ambiguous_normal_count"] == 0,
               "c08-to-c09 RF review did not resolve the two expected normal contacts")
    actual = set(model["trial_active_groups"])
    _check(expected == actual, "Current active groups differ from recomputed previous response transition")
    _check(model.get("trial_radial_states") == {}, "Radial active state added to a zero-gap diagnostic")
    history_check = check_active_set_history(previous, expected)
    if use_rf_opening_intervals:
        preparation = _json(current / "preparation.json")
        _check(model.get("active_set_transition") == transition
               and preparation.get("active_set_transition_method") == transition_method
               and preparation.get("active_set_transition") == transition
               and preparation.get("active_groups") == sorted(expected)
               and preparation.get("active_set_history_check") == history_check,
               "Frozen transition method, preparation record, or active-set history does not match recomputation")
    decks = _check_decks(previous, current, old_model, model, expected)
    endpoint = _check_endpoint_isolation(model)
    expected_hash = hashlib.sha256(json.dumps(sorted(expected), separators=(",", ":")).encode()).hexdigest()

    limits = [
        "This checks an iteration contract and a frozen linear diagnostic branch only; it is not frame stability or joint acceptance.",
        "No contact law, fastener capacity, no-slip floor condition, or mechanical resistance is established.",
        "Parent-owned native readiness and serialized execution remain separate decisions.",
    ]
    if use_rf_opening_intervals:
        limits.append(
            "RF opening inversion was used only for the two active, zero-offset, isolated normal contacts whose DAT displacement intervals overlapped the switch threshold; inactive spring gaps and tension-only ties remain displacement-derived."
        )
    if transition["threshold_rounding_ambiguous_normal_count"] or transition["threshold_rounding_ambiguous_tension_count"]:
        limits.append(
            "Some displacement intervals remain threshold-ambiguous; their prior states were retained where this did not suppress a selected state change."
        )
    result = {
        "schema": "wood_joint_reduced_trial_iteration_review/v1",
        "input_freeze_sha256": current_freeze_sha,
        "previous_freeze_sha256": old_freeze_sha,
        "previous_trial_run_id": prior["previous_run_id"],
        "scope": current_packet["scope"],
        "review_method": "Automated reuse of the independently reviewed same-case zero-gap iteration contract; not a new full model review",
        "ready_for_scoped_native_run": True,
        "native_solve_executed": False,
        "mechanical_acceptance": False,
        "checks": {
            "current_freeze_and_live_source_pins_verified": True,
            "previous_freeze_review_ledger_execution_and_outputs_verified": True,
            "prior_response_rf_recovery_and_equilibrium_checks_verified": True,
            "same_case_scenario_geometry_loads_materials_stiffness_and_ownership_unchanged": True,
            "normal_tension_active_set_recomputed_with_declared_rounding_interval_method": True,
            "rf_opening_interval_method_selected_for_c08_to_c09": use_rf_opening_intervals,
            "prior_active_set_history_checked_for_repetition": history_check["status"] == "PASS_NO_REPEATED_ACTIVE_SET",
            "floor_tangent_groups_paired_to_next_normal_branch": True,
            "deck_only_omits_expected_inactive_spring_groups": True,
            "spring_endpoint_equations_supports_and_applied_loads_checked": True,
        },
        "provenance": prior,
        "active_set_history": history_check,
        "transition": {
            **transition,
            "next_active_group_count": len(expected),
            "expected_active_groups_sha256": expected_hash,
            "freeze_active_groups_match": True,
        },
        "deck": decks,
        "spring_endpoint_isolation": endpoint,
        "reviewer": {
            "path": str(Path(__file__).resolve().relative_to(ROOT)),
            "sha256": digest(__file__),
        },
        "limits": limits,
    }
    if write:
        from fea.wood_joint_reduced_native import write_json
        write_json(current / "review.json", result)
    return result


def audit_consumed_transition(previous: Path, current: Path):
    """Recheck an already-authorized transition without replacing launch review."""
    current = current.resolve()
    transition_review = review_transition(previous, current, write=False, allow_authorized=True)
    freeze_sha = digest(current / "freeze.json")
    current_packet = verify(current, check_live=False)
    live_source_drift = []
    for name, expected in current_packet["source_sha256"].items():
        path = ROOT / name
        if path.is_file() and digest(path) != expected:
            live_source_drift.append(name)
    review_path = current / "review.json"
    authorization_path = current / "authorization.json"
    execution_path = current / "execution.json"
    _check(review_path.is_file() and authorization_path.is_file() and execution_path.is_file(),
           "Consumed transition lacks launch-bound review, authorization, or execution")
    review = _json(review_path)
    authorization = _json(authorization_path)
    execution = _json(execution_path)
    authorized_review_path, authorized_review_sha = _authorized_review_binding(
        current, authorization, freeze_sha)
    _check(review.get("schema") == "wood_joint_reduced_trial_iteration_review/v1"
           and review.get("input_freeze_sha256") == freeze_sha
           and review.get("ready_for_scoped_native_run") is True,
           "Original launch review is not ready and bound to the current freeze")
    _check(authorization.get("input_freeze_sha256") == freeze_sha
           and authorization.get("independent_review_sha256") == authorized_review_sha
           and authorization.get("native_execution_authorized") is True,
           "Launch authorization does not bind the unchanged review and freeze")
    _check(execution.get("run_id") == authorization.get("run_id")
           and execution.get("returncode") == 0
           and execution.get("container_confirmed_terminal") is True,
           "Authorized native execution is not recorded as a successful terminal run")
    ledger = _json(LEDGER)
    rows = [row for row in ledger["runs"] if row.get("run_id") == execution["run_id"]]
    _check(len(rows) == 1, "Consumed native execution is not unique in the ledger")
    row = rows[0]
    _check(row.get("state") == "consumed_terminal" and row.get("launches_consumed") == 1
           and row.get("input_freeze_sha256") == freeze_sha
           and row.get("authorization_sha256") == digest(authorization_path)
           and row.get("execution_record_sha256") == digest(execution_path),
           "Consumed native ledger row differs from the exact authorization/execution")
    outputs = execution.get("outputs_sha256", {})
    _check({"model.inp", "model.dat", "native.stdout", "native.stderr"} <= set(outputs),
           "Consumed execution lacks required output hashes")
    for name, expected in outputs.items():
        _check((current / name).is_file() and digest(current / name) == expected,
               "Consumed native output hash mismatch: " + name)
    result = {
        "schema": "wood_joint_reduced_trial_postauthorization_audit/v1",
        "input_freeze_sha256": freeze_sha,
        "launch_bound_review_path": str(authorized_review_path.relative_to(ROOT)),
        "launch_bound_review_sha256": authorized_review_sha,
        "transition_review_sha256": digest(review_path),
        "launch_authorization_sha256": digest(authorization_path),
        "execution_record_sha256": digest(execution_path),
        "run_id": execution["run_id"],
        "scope": authorization.get("scope"),
        "launch_bound_review_preserved": True,
        "launch_review_reviewer_sha256": review.get("reviewer", {}).get("sha256"),
        "refined_auditor": {"path": str(Path(__file__).resolve().relative_to(ROOT)),
                             "sha256": digest(__file__)},
        "transition_recheck": {
            "checks": transition_review["checks"],
            "provenance": transition_review["provenance"],
            "transition": transition_review["transition"],
            "deck": transition_review["deck"],
            "spring_endpoint_isolation": transition_review["spring_endpoint_isolation"],
        },
        "consumed_run": {"ledger_state": row["state"], "launches_consumed": row["launches_consumed"],
                         "returncode": execution["returncode"],
                         "container_confirmed_terminal": execution["container_confirmed_terminal"],
                         "output_hashes_verified": len(outputs)},
        "live_source_drift_since_freeze": live_source_drift,
        "ready_for_scoped_native_run": None,
        "native_solve_executed": True,
        "mechanical_acceptance": False,
        "limits": [
            "This postauthorization audit leaves the launch-time review bytes untouched and is not a replacement approval.",
            "For c08-to-c09, audited RF opening intervals resolve the two active normals whose DAT displacement intervals cross the branch threshold; all other rows use DAT intervals. This does not establish complementarity.",
            "No frame stability, contact law, fastener capacity, no-slip floor condition, or mechanical resistance is established.",
        ],
    }
    write_path = current / "review-audit.json"
    if write_path.exists():
        old = _json(write_path)
        _check(old.get("schema") == result["schema"]
               and old.get("input_freeze_sha256") == freeze_sha,
               "Refusing to overwrite an unrelated review audit")
    from fea.wood_joint_reduced_native import write_json
    write_json(write_path, result)
    return result


def self_check():
    """Check the known cycle-01 to cycle-02 branch update without native execution."""
    root = ROOT / "docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28"
    attempt = root / "reduced-static-a12-rear-ratio1-gap0-attempt02"
    previous = attempt / "cycle-01-revised-metadata"
    current = attempt / "cycle-02"
    old_model = _json(previous / "model.json")
    report = _json(previous / "response.json")
    active, transition = derive_next_active_set(old_model, report, (previous / "model.dat").read_text())
    _check(len(active) == 580 and transition["normal_active_next"] == 406
           and transition["tension_active_next"] == 133
           and transition["paired_floor_tangent_groups_next"] == 41,
           "Known a12-rear branch transition self-check changed")
    _check(active == set(_json(current / "model.json")["trial_active_groups"]),
           "Known cycle-02 frozen branch differs from recomputed transition")
    return {"passed": True, "next_active_group_count": len(active), **transition}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--previous", type=Path)
    parser.add_argument("--current", type=Path)
    parser.add_argument("--self-check", action="store_true")
    parser.add_argument("--audit-consumed", action="store_true",
                        help="Recheck a transition after authorization; write review-audit.json only")
    args = parser.parse_args()
    if args.self_check:
        print(json.dumps(self_check(), indent=2))
        return
    if args.previous is None or args.current is None:
        parser.error("--previous and --current are required unless --self-check is used")
    if args.audit_consumed:
        result = audit_consumed_transition(args.previous, args.current)
        print(json.dumps({"review_audit_path": str((args.current / "review-audit.json").resolve()),
                          "launch_bound_review_sha256": result["launch_bound_review_sha256"],
                          "launch_authorization_sha256": result["launch_authorization_sha256"],
                          "input_freeze_sha256": result["input_freeze_sha256"]}, indent=2))
        return
    result = review_transition(args.previous, args.current)
    print(json.dumps({"review_path": str((args.current / "review.json").resolve()),
                      "input_freeze_sha256": result["input_freeze_sha256"],
                      "ready_for_scoped_native_run": result["ready_for_scoped_native_run"],
                      "next_active_group_count": result["transition"]["next_active_group_count"]}, indent=2))


if __name__ == "__main__":
    main()
