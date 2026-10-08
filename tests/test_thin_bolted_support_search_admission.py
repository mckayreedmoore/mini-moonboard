"""Fresh provenance/mask/q guards with synthetic ports and stubbed body audit.

These coupons admit no candidate, execute no response or CAD/K assembly, and
never relabel a historical receipt. Full frozen mechanics remain separate.
"""

import copy
import hashlib
import json

import numpy as np
import pytest

from scripts import thin_bolted_support_search_admission as gate


def payload(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def synthetic_field():
    hosts = sorted(gate.support.FLOOR_HOSTS)
    q = np.zeros(12 * len(hosts))
    mapping, floors = {"members": []}, []
    for i, host in enumerate(hosts):
        indices = np.arange(12 * i, 12 * (i + 1)).reshape(2, 6)
        q[indices[:, :3]] = [.002, -.003, -.00001]
        mapping["members"].append({"member": host, "reference_start_xyz_mm": [0., 0., 1.],
            "reference_axis_xyz": [1., 0., 0.], "reference_stations_mm": [0., 1.],
            "node_dof_indices": indices.tolist()})
        for corner, point in enumerate(([.1, -.1, 0.], [.9, -.1, 0.], [.9, .1, 0.], [.1, .1, 0.])):
            floors.append({"id": host + f"/floor-{corner}", "kind": "floor_normal", "first": host,
                "point_xyz_mm": point, "compression_n": .25, "force_on_first_xyz_n": [0., 0., .25]})
        for component, displacement in enumerate((.002, -.003)):
            floors.append({"id": host + f"/no-slip-{component}", "kind": "floor_tangent", "first": host,
                "point_xyz_mm": [.5, 0., 0.], "tangent_displacement_mm": displacement,
                "penalty_stiffness_n_mm": 100000.,
                "force_on_first_xyz_n": (-100000. * displacement * np.eye(3)[component]).tolist()})
    row = {"pattern_index": 0, "mask_id": "centroid-mask-11111111", "enabled_centroid_xy_hosts": hosts,
        "disabled_centroid_xy_hosts": [], "initialization_from_previous_fresh_branch_only": False,
        "fixed_branch_converged": True, "fresh_original_gradient_inf_n": 1e-6,
        "floor_normal_force_n_by_host": dict.fromkeys(hosts, 1.), "demanded_enabled_centroid_xy_hosts": hosts,
        "self_consistent": True, "disabled_xy_force_exactly_zero": True, "disabled_xy_force_n_by_host": {},
        "termination": "synthetic original-law fixed branch"}
    search = {"schema": gate.SEARCH_SCHEMA, "method": gate.METHOD, "floor_activation_threshold_n": 1e-7,
        "host_order": hosts, "mask_budget": 64, "total_possible_masks": 256, "tested_masks": [row],
        "accepted_pattern_index": 0, "accepted_enabled_centroid_xy_hosts": hosts,
        "accepted_disabled_centroid_xy_hosts": [], "final_mask_id": row["mask_id"],
        "final_q_canonical_sha256": gate.canonical_sha(q.tolist()), "all_masks_visited": False,
        "complete_enumeration": False, "no_fixed_point_proven": False, "old_field_initialization_used": False,
        "physical_laws_changed": False, "near_threshold_diagnostic_is_a_normal_force_error_bound": False,
        "body_global_and_export_admission_required": True}
    field = {"schema": "thin_bolted_common_shaft_frame/v1", "case_id": "a12-rear",
        "accessory_placement": "retained-original-top-hold", "geometry_cache_sha256": "synthetic-geometry",
        "usable_conditional_actions": True, "counts": {"dofs": len(q)}, "floor_actions": floors,
        "parameters": {"support_state_search_mask_budget": 64}, "source_sha256": {},
        "response": {"converged": True, "gradient_inf_n": 1e-6, "generalized_residual_tolerance_n": 1e-5,
            "physical_residual_uses_unmodified_laws": True, "q": q.tolist(), "nonbearing_no_slip_removed": [],
            "support_state_search_v1": search}, "release": dict.fromkeys(gate.RELEASE_KEYS, False)}
    return field, mapping, q


def add_execution(field, receipt_path, args):
    command = ["synthetic-python", "-m", "scripts.run_thin_bolted_support_search_frame",
        "--support-method-receipt", str(receipt_path), "--support-method-sha256", args["method_receipt_sha256"],
        "--out", "synthetic-output.json"]
    field["support_state_search_execution"] = {"command": command,
        "loaded_driver_sha256": args["driver_sha256"], "loaded_method_sha256": args["search_sha256"],
        "method_receipt_path": str(receipt_path.relative_to(gate.ROOT)),
        "method_receipt_sha256": args["method_receipt_sha256"], "mask_budget": 64,
        "warm_initialization": None, "one_case_per_invocation": True, "frozen_floor_law_reused": True,
        "old_forces_or_acceptance_transferred": False, "new_solver_framework": False,
        "nested_lean_execution_is_a_reused_internal_call": True}
    field["parameters"].update({"support_state_search_driver_sha256": args["driver_sha256"],
        "support_state_search_method_sha256": args["search_sha256"],
        "support_state_search_method_receipt_sha256": args["method_receipt_sha256"],
        "linear_timber_frame_driver_sha256": gate.linear.DRIVER_SHA256,
        "linear_timber_face_contact_producer_sha256": gate.linear.METHOD_SHA256,
        "linear_timber_face_contact_bedding_n_mm3": 1., "beam_size_mm": 150., "shaft_max_segment_mm": 25.,
        "panel_intervals": 8, "foundation_port_cell_mm": 70., "floor_corner_contact_n_mm": 25000.,
        "floor_no_slip_xy_penalty_n_mm": 100000., "shaft_steel_E_mpa": 200000., "shaft_steel_nu": .3,
        "shaft_diameter_scale": 1., "end_capture_stiffness_n_mm": 1000.,
        "Hillman_axial_lateral_stiffness_n_mm": 1000., "fitting_section": "gross",
        "lean_case_wall_time_limit_seconds": 1800., "numerical_newton_iteration_limit_per_floor_pattern": 300,
        "wood_radial_foundation_n_mm2": 1000. / 38.1, "plate_radial_foundation_n_mm2": 10000. / 5.55625})
    bind_identity(field)


def bind_identity(field):
    value = {key: field[key] for key in ("case_id", "accessory_placement", "parameters", "geometry_cache_sha256")}
    field["state_id"] = "thin-v4-" + gate.canonical_sha(value)[:24]


@pytest.fixture
def sources(tmp_path, monkeypatch):
    """An isolated synthetic source graph exercises the real pin reader."""
    monkeypatch.setattr(gate, "ROOT", tmp_path)
    paths = (gate.OWN, gate.DRIVER, gate.SEARCH, gate.SEARCH_TEST, gate.LINEAR_GATE,
             gate.linear.DRIVER, gate.linear.METHOD)
    pins = {}
    for name in paths:
        path = tmp_path / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("synthetic source: " + name)
        pins[name] = gate.support.digest(path)
    monkeypatch.setattr(gate, "LOADED_PRODUCER_SHA256", pins[gate.OWN])
    monkeypatch.setattr(gate, "LINEAR_GATE_SHA256", pins[gate.LINEAR_GATE])
    monkeypatch.setattr(gate.linear, "DRIVER_SHA256", pins[gate.linear.DRIVER])
    monkeypatch.setattr(gate.linear, "METHOD_SHA256", pins[gate.linear.METHOD])
    monkeypatch.setattr(gate.linear, "source_pins", dict)
    receipt_path = tmp_path / "receipt.json"
    receipt = {"schema": gate.METHOD_SCHEMA, "method_checks_pass": True, "released": False,
        "release": dict.fromkeys(gate.RELEASE_KEYS, False), "source_sha256": pins}
    receipt_path.write_bytes(payload(receipt))
    monkeypatch.setattr(gate, "METHOD_RECEIPT", receipt_path)
    args = {"driver_sha256": pins[gate.DRIVER], "search_sha256": pins[gate.SEARCH],
        "method_receipt_path": receipt_path, "method_receipt_sha256": gate.support.digest(receipt_path)}
    return receipt_path, args


def test_original_linear_floor_q_laws_and_exact_mask_hash():
    field, mapping, q = synthetic_field()
    before = copy.deepcopy(field)
    checks = gate.verify_support_search(field)
    assert checks["final_mask_id"] == "centroid-mask-11111111"
    assert checks["final_q_canonical_sha256"] == gate.canonical_sha(q.tolist())
    assert checks["independent_numerical_gradient_reassembly"] is False
    assert gate.verify_floor_q_laws(field, mapping, q)["original_linear_q_normal_and_centroid_laws_replayed"]
    assert field == before


def apply_final_normal_state(field, q, normal_by_host, enabled, history):
    """Make synthetic final ports, q and mask records agree independently."""
    hosts = sorted(gate.support.FLOOR_HOSTS)
    for i, host in enumerate(hosts):
        indices = np.arange(12 * i, 12 * (i + 1)).reshape(2, 6)
        q[indices[:, 2]] = -normal_by_host[host] / 100000.
    field["floor_actions"] = [row for row in field["floor_actions"]
        if row["kind"] == "floor_normal" or row["first"] in enabled]
    for row in field["floor_actions"]:
        if row["kind"] == "floor_normal":
            row["compression_n"] = normal_by_host[row["first"]] / 4.
            row["force_on_first_xyz_n"] = [0., 0., row["compression_n"]]
    response = field["response"]
    response["q"] = q.tolist()
    response["nonbearing_no_slip_removed"] = sorted(set(hosts) - set(enabled))
    response["support_state_search_v1"].update(tested_masks=history,
        accepted_pattern_index=len(history) - 1, accepted_enabled_centroid_xy_hosts=sorted(enabled),
        accepted_disabled_centroid_xy_hosts=response["nonbearing_no_slip_removed"],
        final_mask_id=history[-1]["mask_id"], final_q_canonical_sha256=gate.canonical_sha(q.tolist()))


def branch_row(field, enabled, normals, index):
    hosts = sorted(gate.support.FLOOR_HOSTS)
    disabled = sorted(set(hosts) - set(enabled))
    demanded = sorted(host for host in hosts if normals[host] > 1e-7)
    return {**copy.deepcopy(field["response"]["support_state_search_v1"]["tested_masks"][0]),
        "pattern_index": index, "mask_id": "centroid-mask-" + "".join("1" if host in enabled else "0" for host in hosts),
        "enabled_centroid_xy_hosts": sorted(enabled), "disabled_centroid_xy_hosts": disabled,
        "initialization_from_previous_fresh_branch_only": index != 0,
        "floor_normal_force_n_by_host": normals, "demanded_enabled_centroid_xy_hosts": demanded,
        "self_consistent": sorted(enabled) == demanded,
        "disabled_xy_force_n_by_host": {host: [0., 0.] for host in disabled}}


@pytest.mark.parametrize("normal", [1e-7, 1.0001e-7])
def test_centroid_release_uses_strict_wholefoot_threshold_and_retains_zero_ports(normal):
    field, mapping, q = synthetic_field()
    hosts = sorted(gate.support.FLOOR_HOSTS)
    normals = {host: normal if host == hosts[0] else 1. for host in hosts}
    enabled = [host for host in hosts if normals[host] > 1e-7]
    history = [branch_row(field, hosts, normals, 0)]
    if enabled != hosts:
        history.append(branch_row(field, enabled, normals, 1))
    apply_final_normal_state(field, q, normals, enabled, history)
    checks = gate.verify_support_search(field)
    assert checks["bearing_hosts"] == enabled
    assert sum(row["kind"] == "floor_normal" for row in field["floor_actions"]) == 32
    assert gate.verify_floor_q_laws(field, mapping, q)["original_linear_q_normal_and_centroid_laws_replayed"]


def test_repeated_feedback_can_escape_to_a_new_mask_and_admit_only_the_final_branch():
    field, mapping, q = synthetic_field()
    hosts = sorted(gate.support.FLOOR_HOSTS)
    first, second = hosts[:2]
    masks = [hosts, [host for host in hosts if host != first],
        [host for host in hosts if host != second], hosts[2:]]
    demanded = [masks[1], masks[2], masks[1], masks[3]]
    history = []
    for index, (enabled, demand) in enumerate(zip(masks, demanded, strict=True)):
        normals = {host: 1. if host in demand else 0. for host in hosts}
        history.append(branch_row(field, enabled, normals, index))
    apply_final_normal_state(field, q, normals, masks[-1], history)
    checks = gate.verify_support_search(field)
    assert checks["accepted_pattern_index"] == 3 and checks["tested_mask_count"] == 4
    assert checks["bearing_hosts"] == hosts[2:]
    assert gate.verify_floor_q_laws(field, mapping, q)["original_linear_q_normal_and_centroid_laws_replayed"]


@pytest.mark.parametrize("mutation", ["failed", "missing-q", "diagnostic", "loose-residual", "too-large",
    "q-hash", "mask-hash", "different-normals", "wholefoot-mask", "repeat", "wrong-pattern",
    "old-warm", "physical-change", "threshold", "unresolved", "false-enumeration", "zero-row-loss"])
def test_unaccepted_or_inconsistent_search_never_supplies_admission(mutation):
    field, _, _ = synthetic_field()
    response, search = field["response"], field["response"]["support_state_search_v1"]
    row = search["tested_masks"][0]
    if mutation == "failed":
        response["converged"] = False
    elif mutation == "missing-q":
        response.pop("q")
    elif mutation == "diagnostic":
        response["diagnostic_last_q"] = response["q"]
    elif mutation == "loose-residual":
        response["generalized_residual_tolerance_n"] = 1e-4
    elif mutation == "too-large":
        response["gradient_inf_n"] = 1.1e-5
    elif mutation == "q-hash":
        response["q"][0] += 1.
    elif mutation == "mask-hash":
        search["final_mask_id"] = "centroid-mask-00000000"
    elif mutation == "different-normals":
        field["floor_actions"][0]["compression_n"] += 1.
    elif mutation == "wholefoot-mask":
        row["floor_normal_force_n_by_host"][search["host_order"][0]] = 1e-7
    elif mutation == "repeat":
        search["tested_masks"].append(copy.deepcopy(row))
        search["tested_masks"][-1].update(pattern_index=1, initialization_from_previous_fresh_branch_only=True)
        search["accepted_pattern_index"] = 1
    elif mutation == "wrong-pattern":
        search["accepted_pattern_index"] = -1
    elif mutation == "old-warm":
        search["old_field_initialization_used"] = True
    elif mutation == "physical-change":
        search["physical_laws_changed"] = True
    elif mutation == "threshold":
        search["floor_activation_threshold_n"] = 1e-5
    elif mutation == "unresolved":
        row.update(fixed_branch_converged=False, self_consistent=False)
    elif mutation == "false-enumeration":
        search["complete_enumeration"] = True
    else:
        field["floor_actions"].pop(0)
    with pytest.raises(ValueError):
        gate.verify_support_search(field)


@pytest.mark.parametrize("mutation", ["normal", "normal-force", "tangent-q", "tangent-force", "stiffness"])
def test_same_hash_and_mask_cannot_substitute_floor_forces_inconsistent_with_q(mutation):
    field, mapping, q = synthetic_field()
    if mutation == "normal":
        field["floor_actions"][0]["compression_n"] += 1.
    elif mutation == "normal-force":
        field["floor_actions"][0]["force_on_first_xyz_n"][2] += 1.
    elif mutation == "tangent-q":
        field["floor_actions"][4]["tangent_displacement_mm"] += .1
    elif mutation == "tangent-force":
        field["floor_actions"][4]["force_on_first_xyz_n"][0] += 1.
    else:
        field["floor_actions"][4]["penalty_stiffness_n_mm"] += 1.
    with pytest.raises(ValueError):
        gate.verify_floor_q_laws(field, mapping, q)


def test_new_method_receipt_pins_are_checked_and_frozen_source_change_is_rejected(sources):
    receipt_path, args = sources
    pins = gate.source_pins(**args)
    assert pins[gate.OWN] == gate.LOADED_PRODUCER_SHA256
    assert pins[str(receipt_path.relative_to(gate.ROOT))] == args["method_receipt_sha256"]
    (gate.ROOT / gate.SEARCH).write_text("changed after method review")
    with pytest.raises(ValueError, match="source changed"):
        gate.source_pins(**args)


@pytest.mark.parametrize("mutation", ["legacy-command", "wrong-driver", "wrong-method", "wrong-receipt",
    "old-forces", "external-warm", "budget", "parameter", "case", "beam", "bedding", "newton", "wall"])
def test_actual_command_and_loaded_provenance_cannot_be_historical_aliases(sources, mutation):
    receipt_path, args = sources
    field, _, _ = synthetic_field()
    add_execution(field, receipt_path, args)
    execution = field["support_state_search_execution"]
    if mutation == "legacy-command":
        execution["command"][2] = "scripts.run_thin_bolted_linear_timber_frame"
    elif mutation == "wrong-driver":
        execution["loaded_driver_sha256"] = "0" * 64
    elif mutation == "wrong-method":
        execution["loaded_method_sha256"] = "0" * 64
    elif mutation == "wrong-receipt":
        execution["command"][6] = "0" * 64
    elif mutation == "old-forces":
        execution["old_forces_or_acceptance_transferred"] = True
    elif mutation == "external-warm":
        execution["command"] += ["--warm-start", "old.json"]
    elif mutation == "budget":
        execution["mask_budget"] = 65
    elif mutation == "parameter":
        field["parameters"]["linear_timber_face_contact_bedding_n_mm3"] = 2.
    else:
        flag, value = {"case": ("--cases", "a12-front"), "beam": ("--beam-size", "100"),
            "bedding": ("--wood-bedding", "2"), "newton": ("--newton-limit", "301"),
            "wall": ("--wall-seconds", "1801")}[mutation]
        execution["command"] += [flag, value]
    with pytest.raises(ValueError):
        gate.verify_execution(field, **args)


def orchestration(sources, monkeypatch):
    """Stub only the already frozen full mechanics for synthetic gate flow."""
    receipt_path, args = sources
    field, mapping, q = synthetic_field()
    add_execution(field, receipt_path, args)
    proof_path = gate.ROOT / "proof.json"
    proof_path.write_bytes(payload({"source_sha256": {}}))
    monkeypatch.setattr(gate.linear.proof_method, "PROOF", proof_path)
    monkeypatch.setattr(gate.linear.proof_method, "PROOF_SHA256", gate.support.digest(proof_path))
    operator, datum = gate.ROOT / "operator.npz", gate.ROOT / "datums.json"
    for path in (operator, datum):
        path.write_text("synthetic saved source")
    monkeypatch.setattr(gate.linear.panel_sources, "OPERATORS", operator)
    monkeypatch.setattr(gate.linear.panel_sources, "OPERATORS_SHA", gate.support.digest(operator))
    monkeypatch.setattr(gate.linear.panel_sources.coupled, "DATUMS", datum)
    monkeypatch.setattr(gate.linear.panel_sources.coupled, "DATUMS_SHA", gate.support.digest(datum))
    field["source_sha256"] = {**gate.source_pins(**args), "proof.json": gate.support.digest(proof_path),
        "operator.npz": gate.support.digest(operator), "datums.json": gate.support.digest(datum)}
    monkeypatch.setattr(gate.common, "read_sources", lambda: (None, {}, None, {}, None, None, {}))
    monkeypatch.setattr(gate.linear.proof_method, "verify_patch_inventory", lambda *_: {"synthetic": True})
    monkeypatch.setattr(gate.linear.spans, "read_member_span_geometry", dict)
    monkeypatch.setattr(gate.linear, "verify_timber_map", lambda *_: (mapping, q))
    monkeypatch.setattr(gate.linear, "verify_face_actions", lambda *_: {"synthetic": True})
    monkeypatch.setattr(gate.linear, "panel_contact_sources", dict)
    monkeypatch.setattr(gate.linear, "verify_action_census", lambda *_: {"synthetic": True})
    monkeypatch.setattr(gate.linear, "audit_linear_timber_state", lambda *_: pytest.fail("historical admission invoked"))
    monkeypatch.setattr(gate.common_export, "audit_common_shaft_state", lambda _: {
        gate.common_export.ACCEPTANCE_KEY: True, "source_sha256": {}, "synthetic_body_audit": True})
    return field, args


def test_fresh_gate_receipt_binds_exact_immutable_bytes_and_all_false_release(sources, monkeypatch):
    field, args = orchestration(sources, monkeypatch)
    raw = payload(field) + b"\n"
    result = gate.audit_support_search_state(raw, **args)
    assert result["schema"] == gate.SCHEMA and result[gate.SUCCESS] is True
    assert result["field_sha256"] == hashlib.sha256(raw).hexdigest()
    assert result["field_canonical_sha256"] == gate.canonical_sha(field)
    assert result["state_id"] == field["state_id"]
    assert result["source_sha256"][gate.OWN] == gate.LOADED_PRODUCER_SHA256
    assert result["native_CAD_K_or_response_execution"] is False
    assert all(value is False for value in result["release"].values())
    assert gate.canonical_sha(field) == result["field_canonical_sha256"]


@pytest.mark.parametrize("mutation", ["parsed-field", "raw-file", "source", "body-audit", "release", "identity"])
def test_changes_or_failed_checks_cannot_issue_a_fresh_receipt(sources, monkeypatch, mutation):
    field, args = orchestration(sources, monkeypatch)
    path = gate.ROOT / "field.json"
    if mutation == "release":
        field["release"]["fabrication_released"] = True
    if mutation == "identity":
        field["state_id"] = "historical-state"
    path.write_bytes(payload(field))

    def audit(parsed):
        if mutation == "parsed-field":
            parsed["case_id"] = "another-case"
        elif mutation == "raw-file":
            path.write_bytes(path.read_bytes() + b"\n")
        elif mutation == "source":
            (gate.ROOT / gate.SEARCH).write_text("source changed inside audit")
        return {gate.common_export.ACCEPTANCE_KEY: mutation != "body-audit", "source_sha256": {}}

    monkeypatch.setattr(gate.common_export, "audit_common_shaft_state", audit)
    with pytest.raises(ValueError):
        gate.audit_support_search_state(path, **args)


def test_canonical_only_dict_and_missing_expected_producer_pins_are_rejected(sources):
    _, args = sources
    with pytest.raises(ValueError, match="immutable field bytes"):
        gate.audit_support_search_state(synthetic_field()[0], **args)
    with pytest.raises(TypeError, match="driver_sha256"):
        gate.audit_support_search_state(b"{}")
