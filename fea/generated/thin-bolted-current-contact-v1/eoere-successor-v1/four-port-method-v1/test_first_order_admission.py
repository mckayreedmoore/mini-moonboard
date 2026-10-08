"""Independent saved-operator/owned-map coupons; no production preparation."""
import copy
import importlib.util
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest
from scipy.sparse import csr_matrix

PATH = Path(__file__).with_name("first_order_admission.py")
SPEC = importlib.util.spec_from_file_location("eoere_independent_field_gate_fixtures", PATH)
gate = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(gate)
TOY_SPEC = importlib.util.spec_from_file_location("eoere_gate_owned_toy", PATH.with_name("test_first_order_factory.py"))
toy = importlib.util.module_from_spec(TOY_SPEC)
TOY_SPEC.loader.exec_module(toy)


def saved_toy(tmp_path):
    data, panels, integrated = toy.toy()
    p = gate.factory.prepare_synthetic(data, panels, integrated)
    pointer = gate.bundle.snapshot(p, arrays_path=tmp_path/"operators.npz", manifest_path=tmp_path/"operators.json",
        pins=gate.bundle.source_pins(), command=["pure-independent-coupon"])
    return data, p, gate.bundle.read_snapshot(pointer)


def test_genuine_owned_maps_every_interaction_and_all_rigid_modes_without_reassembly(tmp_path, monkeypatch):
    data, p, saved = saved_toy(tmp_path)
    monkeypatch.setattr(gate.frame, "ElasticAssembly", lambda *a, **k: pytest.fail("gate rebuilt assembly/K"))
    maps = gate.OwnedMaps(saved, data)
    result = gate.verify_ports(saved, maps, data)
    assert result["owned_point_ports_independently_replayed"] == len(p.groups)+len(p.contacts)+len(p.tangents)
    for body, point, flange in (("wood-a", [40., -20., 5.], None), ("main_lower_left", [60., 70., -8.], None),
        ("toy-shaft", [65.0875, -5., -25.4], None), ("toy-fitting", [65.0875, 0., -25.4], "arm-x/far-plus"),
        ("toy-fitting", [18., 3., 21.], None)):
        assert np.max(abs((maps.port(body, point, flange)-p.assembly.port(body, point, flange)).data), initial=0.) < 1e-14
    gate.verify_physical_bodies(saved, data)
    checks = gate.verify_load_work(saved, maps, data)
    assert checks["nonpanel_affine_selfweight_and_point_load_projections_replayed"]
    assert checks["distributed_panel_rhs_independently_regenerated"] is False


@pytest.mark.parametrize("mutation", ["source", "duplicate-index", "fitting-ndof", "spin-gauge", "floor-point", "bearing-gap", "drop-contact", "rhs"])
def test_source_chart_port_and_load_mutations_reject(tmp_path, mutation):
    data, _, saved = saved_toy(tmp_path)
    if mutation == "source":
        saved.coordinate_map["timber"]["wood-a"]["source"]["width_mm"] += 1.
    elif mutation == "duplicate-index":
        saved.coordinate_map["timber"]["wood-a"]["index"][0][0] = saved.coordinate_map["timber"]["wood-a"]["index"][0][1]
    elif mutation == "fitting-ndof":
        saved.coordinate_map["fitting_embedding_ndof_by_owner"]["toy-fitting"] += 1
    elif mutation == "spin-gauge":
        saved.coordinate_map["shafts"]["toy-shaft"]["index"][1][3] = -1
    elif mutation == "floor-point":
        next(row for row in saved.contacts if row["kind"] == "floor_normal")["point_xyz_mm"][0] += .1
    elif mutation == "bearing-gap":
        next(row for row in saved.groups if row["kind"] == "common_shaft_bearing")["clearance"] += .001
    elif mutation == "drop-contact":
        saved.contacts.pop()
    else:
        saved.applied[0] += .01
    with pytest.raises(ValueError):
        maps = gate.OwnedMaps(saved, data)
        gate.verify_ports(saved, maps, data)
        gate.verify_load_work(saved, maps, data)


def floor_coupon(*, open_floor=False):
    corners = [[-1., -1., 0.], [1., -1., 0.], [1., 1., 0.], [-1., 1., 0.]]
    contacts = [{"id": "foot/floor-"+str(i), "kind": "floor_normal", "first": "foot", "second": "floor",
        "point_xyz_mm": p, "direction_xyz": [0., 0., 1.], "stiffness": 25000., "B": csr_matrix([[0., 0., -1.]])}
        for i, p in enumerate(corners)]
    tangents = [{"id": "foot/no-slip-"+str(i), "kind": "floor_tangent", "first": "foot", "point_xyz_mm": [0., 0., 0.],
        "direction_xyz": np.eye(3)[i].tolist(), "stiffness": 100000., "B": csr_matrix(np.eye(3)[i:i+1])} for i in (0, 1)]
    q = np.array([.03, .02, .02]) if open_floor else np.array([.001, .002, -.001])
    applied = np.zeros(3) if open_floor else np.array([100., 200., -100.])
    case = {"loads": [{"body": "foot", "id": "known-resultant", "point_xyz_mm": [0., 0., 0.], "force_xyz_n": applied.tolist()}],
        "applied_force_xyz_n": applied.tolist(), "applied_moment_about_global_origin_xyz_nmm": [0., 0., 0.]}
    saved = SimpleNamespace(assembly=SimpleNamespace(ndof=3, K=csr_matrix((3, 3)), geo={"bodies": [{"id": "foot"}]}),
        applied=applied, groups=[], contacts=contacts, tangents=tangents, case=case)
    enabled = [] if open_floor else ["foot"]
    fresh = gate.replay_original(saved, q, enabled)
    floor = [{**gate.core.descriptor(row), "force_on_first_xyz_n": (normal*np.array(row["direction_xyz"])).tolist(),
        "force_on_second_xyz_n": (-normal*np.array(row["direction_xyz"])).tolist(), "compression_n": float(normal)}
        for row, normal in zip(contacts, fresh[4], strict=True)]
    for row in tangents:
        d = float((row["B"]@q)[0])
        force = np.zeros(3) if open_floor else -row["stiffness"]*d*np.array(row["direction_xyz"])
        floor.append({**gate.core.descriptor(row), "second": "floor", "interaction_enabled": not open_floor,
            "tangent_displacement_mm": d, "force_on_first_xyz_n": force.tolist(), "force_on_second_xyz_n": (-force).tolist(), "energy_nmm": 0. if open_floor else .5*row["stiffness"]*d*d})
    response = {"connector_local_force_n": [], "normal_contact_force_n": fresh[4].tolist(),
        "normal_contact_displacement_mm": fresh[5].tolist(), "gradient_n": fresh[0].tolist(),
        "gradient_canonical_sha256": gate.canonical(fresh[0].tolist()), "q_canonical_sha256": gate.canonical(q.tolist()),
        "potential_energy_nmm": fresh[1], "gradient_inf_n": float(np.max(abs(fresh[0])))}
    field = {"response": response, "floor_actions": floor, "panel_screw_actions": [], "common_shaft_bearing_actions": [],
        "contact_actions": [], "shaft_end_capture_actions": [], "attachment_actions": [], "retained_bolt_actions": [],
        "body_equilibrium_residuals": [{"body": "foot", "force_xyz_n": [0., 0., 0.], "moment_about_reference_xyz_nmm": [0., 0., 0.]}],
        "global_equilibrium_residual_force_n": [0., 0., 0.], "global_equilibrium_residual_moment_nmm": [0., 0., 0.]}
    return saved, q, fresh, field


def test_known_nonzero_floor_gradient_force_moment_and_disabled_zero_law():
    for opened in (False, True):
        saved, q, fresh, field = floor_coupon(open_floor=opened)
        normals, checks = gate.verify_actions(field, saved, q, fresh)
        assert normals == {"foot": 0. if opened else 100.}
        assert checks["gradient_inf_n"] == 0.
        assert checks["maximum_body_force_norm_n"] == 0.
        assert checks["maximum_body_moment_about_reference_norm_nmm"] < 1e-9


@pytest.mark.parametrize("mutation", ["disabled-tiny-shear", "disabled-energy", "gradient", "pair", "moment", "duplicate", "body-residual"])
def test_force_gradient_and_body_closure_mutations_reject(mutation):
    saved, q, fresh, field = floor_coupon(open_floor=mutation.startswith("disabled"))
    if mutation == "disabled-tiny-shear":
        field["floor_actions"][-1]["force_on_first_xyz_n"][1] = 5e-8
    elif mutation == "disabled-energy":
        field["floor_actions"][-1]["energy_nmm"] = 1e-15
    elif mutation == "gradient":
        field["response"]["gradient_n"][0] += 1e-12
    elif mutation == "pair":
        field["floor_actions"][0]["force_on_second_xyz_n"][2] += 1.
    elif mutation == "moment":
        field["floor_actions"][0]["moment_at_point_model_xyz_nmm"] = [1e-12, 0., 0.]
    elif mutation == "duplicate":
        field["floor_actions"].append(copy.deepcopy(field["floor_actions"][0]))
    else:
        field["body_equilibrium_residuals"][0]["force_xyz_n"][0] = 1.
    with pytest.raises(ValueError):
        gate.verify_actions(field, saved, q, fresh)


def search_response(q, normal=100.):
    enabled = ["foot"] if normal > 1e-7 else []
    row = {"pattern_index": 0, "mask_id": "centroid-mask-1", "selection_reason": "original all-host initial mask",
        "enabled_centroid_xy_hosts": ["foot"], "disabled_centroid_xy_hosts": [],
        "initialization_from_previous_fresh_branch_only": False, "fixed_branch_converged": True,
        "self_consistent": bool(enabled), "fresh_original_gradient_inf_n": 0., "floor_normal_force_n_by_host": {"foot": normal},
        "demanded_enabled_centroid_xy_hosts": enabled, "disabled_xy_force_exactly_zero": True, "disabled_xy_force_n_by_host": {}}
    diag = {"schema": "thin_bolted_support_state_search/v1", "method": gate.core.search.METHOD,
        "host_order": ["foot"], "total_possible_masks": 2, "floor_activation_threshold_n": 1e-7,
        "mask_budget": 2, "old_field_initialization_used": False, "physical_laws_changed": False, "no_fixed_point_proven": False,
        "near_threshold_diagnostic_is_a_normal_force_error_bound": False, "body_global_and_export_admission_required": True,
        "tested_masks": [row], "accepted_pattern_index": 0, "accepted_enabled_centroid_xy_hosts": enabled,
        "accepted_disabled_centroid_xy_hosts": [], "final_q_canonical_sha256": gate.canonical(q.tolist()), "final_mask_id": row["mask_id"],
        "all_masks_visited": False, "complete_enumeration": False}
    return {"support_state_search_v1": diag, "nonbearing_no_slip_removed": [], "gradient_inf_n": 0.}


def test_final_same_q_original_support_search_acceptance_and_threshold():
    _, q, _, _ = floor_coupon()
    response = search_response(q)
    result = gate.verify_search(response, ["foot"], q, {"foot": 100.}, 2)
    assert result["final_q_canonical_sha256"] == gate.canonical(q.tolist())
    for n in (1e-7, 0.):
        with pytest.raises(ValueError):
            gate.verify_search(search_response(q, n), ["foot"], q, {"foot": n}, 2)


@pytest.mark.parametrize("mutation", ["external-warm", "q", "mask", "duplicate", "selector", "enumeration"])
def test_mask_history_and_final_q_mutations_reject(mutation):
    _, q, _, _ = floor_coupon()
    response = search_response(q)
    diag = response["support_state_search_v1"]
    if mutation == "external-warm":
        diag["old_field_initialization_used"] = True
    elif mutation == "q":
        diag["final_q_canonical_sha256"] = "0"*64
    elif mutation == "mask":
        diag["accepted_enabled_centroid_xy_hosts"] = []
    elif mutation == "duplicate":
        diag["tested_masks"].append(copy.deepcopy(diag["tested_masks"][0]))
    elif mutation == "selector":
        diag["tested_masks"][0]["selection_reason"] = "old history selection"
    else:
        diag["complete_enumeration"] = True
    with pytest.raises(ValueError):
        gate.verify_search(response, ["foot"], q, {"foot": 100.}, 2)


def test_genuine_loaded_heel_and_all_owned_surface_recovery_without_candidate(tmp_path):
    data, p, saved = saved_toy(tmp_path)
    q = np.random.default_rng(13).normal(size=p.assembly.ndof)*.001
    fresh = gate.replay_original(saved, q, ["wood-a"])
    response = {"converged": True, "q": q, "connector_local_force_n": fresh[3], "normal_contact_force_n": fresh[4],
        "nonbearing_no_slip_removed": [], "support_state_search_v1": {"accepted_enabled_centroid_xy_hosts": ["wood-a"]}}
    # Component coupon only: this arbitrary q is not claimed in equilibrium.
    recovered = gate.core.recover(p, response)
    recovered["source_inputs"] = data
    maps = gate.OwnedMaps(saved, data)
    checks = gate.verify_fitting_and_alias_recovery(recovered, saved, maps, q)
    assert checks["loaded_root_recoveries_replayed"] == 1
    assert checks["own_surface_aggregate_recoveries_replayed"] == 2
    assert checks["own_signed_external_action_shaft_cut_recoveries_replayed"] == 1
    assert checks["fitting_gravity_condensation_potential_constant_nmm"] < 0.
    recovered["four_port_fitting_actions"][0]["loaded_heel_q_mm_rad"][0] += 1e-3
    with pytest.raises(ValueError):
        gate.verify_fitting_and_alias_recovery(recovered, saved, maps, q)


def actual_command():
    return ["python", str(gate.DRIVER), "--inputs", "inputs.json", "--inputs-sha256", "a"*64,
            "--input-review", "review.json", "--input-review-sha256", "b"*64, "--out", "out.json", "--run"]


def test_true_outer_command_default_limits_and_exclusive_argv():
    parsed = gate.parse_command(actual_command())
    assert (parsed.mask_budget, parsed.max_iterations, parsed.wall_seconds) == (64, 300, 1770.)


@pytest.mark.parametrize("mutation", ["old-driver", "external-q", "unknown-physics", "mask", "iterations", "wall", "no-run"])
def test_actual_outer_command_mutations_reject_before_sources(mutation):
    command = actual_command()
    if mutation == "old-driver":
        command[1] = str(gate.bundle.CORE)
    elif mutation == "external-q":
        command.extend(["--warm-start", "old.json"])
    elif mutation == "unknown-physics":
        command.extend(["--floor-kt", "1"])
    elif mutation == "mask":
        command.extend(["--mask-budget", "257"])
    elif mutation == "iterations":
        command.extend(["--max-iterations", "301"])
    elif mutation == "wall":
        command.extend(["--wall-seconds", "1801"])
    else:
        command.remove("--run")
    with pytest.raises(ValueError):
        gate.parse_command(command)


def test_real_cheap_consumer_rejects_old_receipt_and_foreign_action_identity():
    with pytest.raises(ValueError, match="receipt"):
        gate.require_admitted_payload(b'{"schema":"old"}', {"schema": "old", gate.SUCCESS: True}, admission_sha256=gate.LOADED_SHA)
    field = {"state_id": "new", "case_id": "a12-rear", "accessory_placement": "retained-original-top-hold",
             "four_port_fitting_actions": [{"state_id": "old"}]}
    with pytest.raises(ValueError, match="foreign"):
        gate.identities(field)
