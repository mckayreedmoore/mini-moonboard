"""Tiny genuine cold branches and synthetic writer seams; no candidate K."""

import copy
import hashlib
import json
import sys
from types import SimpleNamespace

import numpy as np
import pytest
from scipy.sparse import csr_matrix

from scripts import run_thin_bolted_cold_fixed_branch_diagnostic as driver


def tiny_branch():
    K = csr_matrix(np.diag([10., 20., 30.]))
    applied = np.array([100010., 200040., 0.])
    contacts = [{"id": f"foot/floor-{i}", "kind": "floor_normal", "first": "foot", "second": "floor",
                 "B": csr_matrix([[1., 0., 0.]]), "stiffness": 25000.} for i in range(4)]
    tangents = [{"id": f"foot/no-slip-{i}", "kind": "floor_tangent", "first": "foot",
                 "B": csr_matrix([row]), "stiffness": 100000.}
                for i, row in enumerate(([0., 1., 0.], [0., 0., 1.]))]
    return K, applied, [], contacts, tangents


def test_cold_bilateral_initialization_reuses_genuine_frozen_engine():
    inputs = tiny_branch()
    solves = []
    numerical = driver.branch.incremental.ORIGINAL_NUMERICAL_SOLVE

    def observe(A, b):
        solves.append((A.copy(), b.copy()))
        return numerical(A, b)

    with pytest.MonkeyPatch.context() as monkeypatch:
        monkeypatch.setattr(driver.branch.incremental, "ORIGINAL_NUMERICAL_SOLVE", observe)
        response = driver.cold_branch_diagnostic(*inputs, mask_id="centroid-mask-1")
    assert len(solves) >= 2  # Both frozen bilateral/gap-correction initialization solves occurred.
    np.testing.assert_allclose(solves[0][0].toarray(), np.diag([100010., 100020., 100030.]))
    np.testing.assert_array_equal(solves[0][1], inputs[1])
    np.testing.assert_allclose(response["diagnostic_last_q"], [1., 2., 0.], atol=1e-12)
    diagnostic = response["cold_fixed_branch_diagnostic_v1"]
    assert diagnostic["fixed_branch_converged"] and diagnostic["self_consistent"]
    assert diagnostic["fresh_original_gradient_inf_n"] < 1e-5
    assert diagnostic["floor_normal_force_n_by_host"] == {"foot": 100000.}
    assert len(diagnostic["floor_normal_port_diagnostics"]) == 4
    assert diagnostic["diagnostic_q_canonical_sha256"] == driver.canonical_sha([1., 2., 0.])
    assert response["converged"] is False
    assert not {"q", "connector_local_force_n", "normal_contact_force_n"} & response.keys()
    assert diagnostic["warm_initialization"] is None
    assert not diagnostic["current_actions_or_acceptance_exported"]
    assert not diagnostic["uniqueness_or_nonexistence_proven"]


def test_mask_inconsistent_equilibrium_is_diagnostic_only():
    response = driver.cold_branch_diagnostic(*tiny_branch(), mask_id="centroid-mask-0")
    diagnostic = response["cold_fixed_branch_diagnostic_v1"]
    np.testing.assert_allclose(response["diagnostic_last_q"], [1., 10002., 0.], atol=1e-9)
    assert diagnostic["fixed_branch_converged"] and not diagnostic["self_consistent"]
    assert diagnostic["demanded_enabled_centroid_xy_hosts"] == ["foot"]
    assert not response["converged"] and "q" not in response


def test_cold_gap_correction_has_a_hand_computed_original_law_answer():
    K, applied, groups, contacts, tangents = tiny_branch()
    #Independent bilateral axial coordinate; circular gap in the x/y plane.
    #n=1 andy=0; x solves20x+100000x+5000(x−1)=200040.
    groups.append({"id": "declared-gap-spring", "kind": "synthetic-coupon",
                   "B": csr_matrix([[1., 0., 0.], [0., 1., 0.], [0., 0., 1.]]),
                   "ka": 0., "kl": 5000., "clearance": 1., "tension_only": False})
    response = driver.cold_branch_diagnostic(K, applied, groups, contacts, tangents, mask_id="centroid-mask-1")
    np.testing.assert_allclose(response["diagnostic_last_q"], [1., 205040. / 105020., 0.], atol=1e-12)
    assert response["cold_fixed_branch_diagnostic_v1"]["fixed_branch_converged"]
    assert response["gradient_inf_n"] < 1e-5 and "q" not in response


@pytest.mark.parametrize("contaminated", [np.array([1e9, -1e9, 1e9]), np.zeros(3), [float("nan")]])
def test_any_contaminated_or_external_warm_q_is_rejected_before_solver(monkeypatch, contaminated):
    monkeypatch.setattr(driver.branch, "_fixed_branch", lambda *a: pytest.fail("warm contamination reached solver"))
    with pytest.raises(ValueError, match="warm coefficients"):
        driver.cold_branch_diagnostic(*tiny_branch(), mask_id="centroid-mask-1", warm_q=contaminated)


def test_fresh_original_gradient_defeats_a_corrupted_solver_success(monkeypatch):
    original = driver.branch._fixed_branch

    def corrupt(*args):
        response = original(*args)
        response["q"] += 1.
        response["gradient_inf_n"] = 0.
        return response

    monkeypatch.setattr(driver.branch, "_fixed_branch", corrupt)
    response = driver.cold_branch_diagnostic(*tiny_branch(), mask_id="centroid-mask-1")
    assert response["gradient_inf_n"] > 100000.
    diagnostic = response["cold_fixed_branch_diagnostic_v1"]
    assert diagnostic["fixed_branch_solver_converged"]
    assert not diagnostic["fixed_branch_converged"] and not diagnostic["self_consistent"]
    assert "q" not in response


@pytest.mark.parametrize("mask", ["1", "centroid-mask-", "centroid-mask-11", "centroid-mask-x"])
def test_explicit_mask_bits_are_required(mask):
    with pytest.raises(ValueError, match="mask bits"):
        driver.cold_branch_diagnostic(*tiny_branch(), mask_id=mask)


def simple_mapping():
    return {"schema": driver.lean.faces.MAP_SCHEMA, "ndof": 24, "rotation_scale": 1000., "members": [
        {"member": name, "reference_start_xyz_mm": [0., offset, 0.],
         "reference_axis_xyz": [1., 0., 0.], "reference_stations_mm": [0., 10.],
         "node_dof_indices": np.arange(12 * i, 12 * (i + 1)).reshape(2, 6).tolist()}
        for i, (name, offset) in enumerate((("first", 0.), ("second", 1.)))]}


def test_motion_markers_keep_source_port_identities_and_scaled_rotation():
    mapping = simple_mapping()
    q = np.zeros(24)
    q[:3] = [0., 2., 3.]; q[6:9] = [0., 4., 5.]
    q[5] = q[11] = 100.  #0.1rad aboutz; y-offset2mm creates x-reference-arm motion−0.2mm.
    contacts = [{"id": "paired-cell", "kind": "timber_face_contact", "first": "first", "second": "second",
                 "point_xyz_mm": [5., 2., 0.], "direction_xyz": [0., 0., 1.]},
                {"id": "original-foot-corner", "kind": "floor_normal", "first": "first",
                 "point_xyz_mm": [5., 2., 0.]}]
    markers = driver.motion_markers(mapping, contacts, q)
    assert markers["maximum_timber_node_rotation_norm_rad"] == pytest.approx(.1)
    assert markers["maximum_timber_node_translation_norm_mm"] == pytest.approx(np.sqrt(41.))
    assert markers["maximum_face_tangential_motion_norm_mm"] == pytest.approx(np.hypot(.2, 3.))
    face = markers["paired_face_reference_motion_markers"][0]
    assert (face["contact_id"], face["first"], face["second"]) == ("paired-cell", "first", "second")
    assert face["relative_normal_motion_mm"] == 4.
    floor = markers["floor_reference_motion_markers"][0]
    assert floor["contact_id"] == "original-foot-corner"
    np.testing.assert_allclose(floor["reference_port_motion_xyz_mm"], [-.2, 3., 4.])
    assert not markers["deformation_limit_adopted"] and not markers["small_motion_applicability_established"]
    assert not markers["diagnostic_q_is_a_physical_motion_prediction"]


def prepared_census():
    mapping = {"members": [{}] * 20, "ndof": 4000}
    groups = [{"id": f"bearing{i}", "kind": "common_shaft_bearing"} for i in range(308)]
    groups.extend({"id": f"screw{i}", "kind": "panel_screw"} for i in range(66))
    contacts = [{"id": f"capture{i}", "kind": "shaft_end_capture"} for i in range(140)]
    for i in range(272):
        pair = i % 6
        contacts.append({"id": f"face{i}", "kind": "timber_face_contact", "first": f"a{pair}", "second": f"b{pair}"})
    tangents = []
    for i in range(8):
        host = f"host{i}"
        contacts.extend({"id": f"floor{i}/{j}", "kind": "floor_normal", "first": host} for j in range(4))
        tangents.extend({"id": f"tangent{i}/{j}", "kind": "floor_tangent", "first": host} for j in range(2))
    return mapping, groups, contacts, tangents


@pytest.mark.parametrize("corruption", ["bearing", "capture", "face_pair", "normal", "tangent", "duplicate", "screw"])
def test_actual_prepared_census_rejects_missing_or_aliased_path(corruption):
    inputs = prepared_census()
    assert driver.verify_prepared_census(*inputs)["own_axial_end_captures"] == 140
    mapping, groups, contacts, tangents = copy.deepcopy(inputs)
    if corruption == "bearing":
        groups.pop(0)
    elif corruption == "screw":
        groups.pop()
    elif corruption == "capture":
        contacts.pop(0)
    elif corruption == "face_pair":
        for row in contacts:
            if row["kind"] == "timber_face_contact":
                row["first"], row["second"] = "a0", "b0"
    elif corruption == "normal":
        contacts.pop()
    elif corruption == "tangent":
        tangents.pop()
    else:
        groups[0]["id"] = contacts[0]["id"]
    with pytest.raises(ValueError):
        driver.verify_prepared_census(mapping, groups, contacts, tangents)


def arguments(tmp_path, **options):
    result = ["cold", "--out", str(tmp_path / "field.json"), "--cold-mask", "centroid-mask-10000001",
              "--cold-method-receipt", "receipt.json", "--cold-method-sha256", "0" * 64]
    for key, value in options.items():
        result.extend(["--" + key.replace("_", "-"), str(value)])
    return result


@pytest.mark.parametrize("extra", [{"warm_start": "prior.json"}, {"beam_size": 100}, {"shaft_segment": 20},
    {"wood_bedding": 2}, {"newton_limit": 301}, {"wall_seconds": 1801}, {"cases": "a12-front"},
    {"floor_tangent_stiffness": 99999}, {"wood_bearing_foundation": 25}, {"shaft_diameter_scale": .9},
    {"accessory": "proportional-six-panel-sensitivity"}, {"fitting_section": "net"}])
def test_scope_rejection_precedes_candidate_preparation(monkeypatch, tmp_path, extra):
    monkeypatch.setattr(sys, "argv", arguments(tmp_path, **extra))
    monkeypatch.setattr(driver.lean, "main", lambda: pytest.fail("candidate prepared"))
    with pytest.raises(SystemExit):
        driver.main()


@pytest.mark.parametrize("suffix", ["", ".interrupted.json"])
def test_existing_fields_and_interruptions_are_preserved(monkeypatch, tmp_path, suffix):
    saved = tmp_path / ("field.json" + suffix)
    saved.write_bytes(b"preserved")
    monkeypatch.setattr(sys, "argv", arguments(tmp_path))
    with pytest.raises(SystemExit):
        driver.main()
    assert saved.read_bytes() == b"preserved"


def test_truthful_outer_command_sources_and_identity_precede_genuine_finished_binding():
    identities = []
    for mask in ("centroid-mask-10000001", "centroid-mask-11000000"):
        report = {"state_id": "before", "case_id": "a12-rear", "accessory_placement": "test",
                  "geometry_cache_sha256": "a" * 64, "parameters": {}, "source_sha256": {}, "limits": [],
                  "response": {"converged": False}, "actions": []}
        driver.bind_cold_metadata(report, {"source": "b" * 64}, ["actual", "-m", driver.OWN[:-3].replace("/", ".")],
                                  driver.METHOD_RECEIPT, "c" * 64, mask, {"structural_bodies": 132})
        driver.lean.common.finished.bind_finished_state(report, [], {}, "d" * 64)
        identities.append(report["state_id"])
        execution = report["cold_fixed_branch_execution"]
        assert execution["mask_id"] == mask and execution["warm_initialization"] is None
        assert execution["nested_lean_execution_is_a_reused_internal_call"]
        assert execution["prepared_census"]["structural_bodies"] == 132
        assert not execution["current_actions_or_acceptance_exported"]
    assert identities[0] != identities[1]


def test_delegate_uses_only_cold_entry_restores_patches_and_records_actual_command(monkeypatch, tmp_path):
    captured = {}
    monkeypatch.setattr(driver, "source_pins", lambda *a: ({"cold-source": "a" * 64}, {}))
    monkeypatch.setattr(driver.lean.common, "bind_common_metadata", lambda report, *a: report)
    monkeypatch.setattr(driver.lean.faces, "prepare_linear_timber_faces", lambda *a, **k: {"coordinate_map": {"ndof": 3}})
    monkeypatch.setattr(driver, "verify_prepared_census", lambda *a: {"floor_normal_ports": 32})

    def cold(*a, **options):
        captured["solve_options"] = options
        return {"converged": False, "diagnostic_last_q": np.array([1., 2., 0.])}

    def lean_main():
        captured["inner_argv"] = sys.argv.copy()
        driver.lean.faces.prepare_linear_timber_faces("original")
        response = driver.lean.incremental.compatible_contact_solve(*tiny_branch(), max_iterations=300, warm_q=None)
        with pytest.raises(ValueError, match="one prepared cold branch"):
            driver.lean.incremental.compatible_contact_solve(*tiny_branch())
        report = {"parameters": {}, "source_sha256": {}, "limits": [], "response": response,
                  "counts": {"timber_members": 20, "finite_fittings": 36, "flexible_panels": 6,
                             "physical_bolt_axes": 70, "panel_screw_axes": 66},
                  "usable_conditional_actions": False, "release": driver.frame.RELEASE}
        system = SimpleNamespace(assembly=SimpleNamespace(geo={"bodies": [None] * 132}), shafts=[None] * 70)
        captured["report"] = driver.lean.common.bind_common_metadata(report, system, {}, ["honest-inner"])

    monkeypatch.setattr(driver, "cold_branch_diagnostic", cold)
    monkeypatch.setattr(driver.lean, "main", lean_main)
    old_solver = driver.lean.incremental.compatible_contact_solve
    old_prepare = driver.lean.faces.prepare_linear_timber_faces
    old_metadata = driver.lean.common.bind_common_metadata
    argv = arguments(tmp_path)
    monkeypatch.setattr(sys, "argv", argv)
    driver.main()
    assert sys.argv == argv
    assert driver.lean.incremental.compatible_contact_solve is old_solver
    assert driver.lean.faces.prepare_linear_timber_faces is old_prepare
    assert driver.lean.common.bind_common_metadata is old_metadata
    assert "--cold-mask" not in captured["inner_argv"]
    assert captured["solve_options"]["warm_q"] is None
    execution = captured["report"]["cold_fixed_branch_execution"]
    assert execution["command"][1:3] == ["-m", "scripts.run_thin_bolted_cold_fixed_branch_diagnostic"]
    assert execution["command"][3:] == argv[1:]
    assert execution["prepared_census"]["structural_bodies"] == 132


def test_preparation_interruption_is_source_bound_diagnostic_sidecar(monkeypatch, tmp_path):
    monkeypatch.setattr(driver, "source_pins", lambda *a: ({"cold-source": "a" * 64}, {}))

    def lean_main():
        driver.lean.write_interruption(tmp_path / "field.json", ["inner"], {}, {}, {"phase": "preparation"})

    monkeypatch.setattr(driver.lean, "main", lean_main)
    monkeypatch.setattr(sys, "argv", arguments(tmp_path))
    driver.main()
    sidecar = json.loads((tmp_path / "field.json.interrupted.json").read_bytes())
    assert sidecar["command"][2] == "scripts.run_thin_bolted_cold_fixed_branch_diagnostic"
    assert sidecar["source_sha256"]["cold-source"] == "a" * 64
    assert sidecar["mask_id"] == "centroid-mask-10000001"
    assert sidecar["warm_initialization"] is None
    assert "q" not in sidecar["response"] and not sidecar["accepted_field_exported"]
    assert not any(sidecar["release"].values())


def test_original_common_failure_writer_preserves_diagnostic_without_recovery(monkeypatch, tmp_path):
    common = driver.lean.common
    output = tmp_path / "diagnostic.json"
    response = driver.cold_branch_diagnostic(*tiny_branch(), mask_id="centroid-mask-1")
    motion = driver.motion_markers(simple_mapping(), [], np.zeros(24))
    response["cold_fixed_branch_diagnostic_v1"]["motion_applicability_diagnostics"] = motion
    report = {"state_id": "previous", "case_id": "a12-rear", "accessory_placement": "coupon",
              "geometry_cache_sha256": "a" * 64, "parameters": {}, "source_sha256": {}, "limits": [],
              "response": response, "usable_conditional_actions": False, "release": driver.frame.RELEASE,
              "counts": {"structural_bodies": 132, "timber_members": 20, "finite_fittings": 36,
                         "flexible_panels": 6, "physical_shaft_bodies": 70},
              "body_identities": [f"synthetic-body-{i}" for i in range(132)],
              "body_applied_loads": [{"body": f"synthetic-body-{i}", "point_xyz_mm": [0., 0., 0.],
                                      "force_xyz_n": [0., 0., -1.]} for i in range(132)]}
    driver.bind_cold_metadata(report, {"cold-source": "b" * 64},
        [sys.executable, "-m", "scripts.run_thin_bolted_cold_fixed_branch_diagnostic"],
        driver.METHOD_RECEIPT, "c" * 64, "centroid-mask-1", {"structural_bodies": 132, "physical_shaft_bodies": 70})
    before_id = report["state_id"]

    def unsolved_only():
        raise common.UnsolvedCommonState(report)

    monkeypatch.setattr(common.shafts, "read_inputs", dict)
    monkeypatch.setattr(common.shafts, "source_pins", dict)
    monkeypatch.setattr(common.finished, "main", unsolved_only)
    monkeypatch.setattr(common.finished, "read_finished_footprints", lambda: ({}, [], {}))
    monkeypatch.setattr(driver.frame, "evaluate_elastic", lambda *a, **k: pytest.fail("candidate response requested"))
    monkeypatch.setattr(driver.frame, "elastic_actions", lambda *a, **k: pytest.fail("diagnostic actions recovered"))
    monkeypatch.setattr(sys, "argv", ["common-coupon", "--out", str(output)])
    common.main()  #Actual frozen unsolved export, binder and writer.
    saved = json.loads(output.read_bytes())
    assert saved["state_id"] != before_id
    assert saved["failed_response_without_recovered_actions"] is True
    assert saved["usable_conditional_actions"] is False
    assert saved["response"]["converged"] is False
    assert "q" not in saved["response"]
    assert not any(saved.get(key) for key in common.COMMON_TABLES)
    np.testing.assert_array_equal(saved["response"]["diagnostic_last_q"], [1., 2., 0.])
    assert saved["cold_fixed_branch_execution"]["mask_id"] == "centroid-mask-1"
    assert saved["cold_fixed_branch_execution"]["prepared_census"]["structural_bodies"] == 132
    assert len(saved["body_identities"]) == len(saved["body_applied_loads"]) == 132
    assert saved["response"]["cold_fixed_branch_diagnostic_v1"]["motion_applicability_diagnostics"] == motion
    assert not any(saved["release"].values())
    original = output.read_bytes()
    with pytest.raises(FileExistsError):
        common.main()
    assert output.read_bytes() == original


def test_outer_patch_restoration_on_failure(monkeypatch, tmp_path):
    monkeypatch.setattr(driver, "source_pins", lambda *a: ({}, {}))

    def fail():
        raise RuntimeError("synthetic preparation interruption")

    monkeypatch.setattr(driver.lean, "main", fail)
    original_functions = (driver.lean.faces.prepare_linear_timber_faces,
                          driver.lean.incremental.compatible_contact_solve,
                          driver.lean.common.bind_common_metadata, driver.lean.write_interruption)
    argv = arguments(tmp_path)
    monkeypatch.setattr(sys, "argv", argv)
    with pytest.raises(RuntimeError, match="synthetic preparation"):
        driver.main()
    assert sys.argv == argv
    assert original_functions == (driver.lean.faces.prepare_linear_timber_faces,
                                  driver.lean.incremental.compatible_contact_solve,
                                  driver.lean.common.bind_common_metadata, driver.lean.write_interruption)


def test_current_explicit_arguments_pass_actual_frozen_parser_chain_before_preparation(monkeypatch, tmp_path):
    class ParserChainReached(RuntimeError):
        pass

    def no_preparation(**options):
        assert options["case_id"] == "a12-rear" and options["intervals"] == 8
        assert options["beam_size"] == 150. and options["contact_edge"] == 70.
        assert options["floor_tangent_stiffness"] == 100000.
        raise ParserChainReached("all frozen command parsers accepted explicit current flags")

    monkeypatch.setattr(driver, "source_pins", lambda *a: ({}, {}))
    monkeypatch.setattr(driver.lean.common.shafts, "read_inputs", dict)
    monkeypatch.setattr(driver.frame, "evaluate_elastic", no_preparation)
    argv = arguments(tmp_path, cases="a12-rear", intervals=8, beam_size=150, contact_edge=70,
                     shaft_segment=25, wood_bearing_foundation="26.2467191601",
                     steel_bearing_foundation="1799.77502812", end_capture_stiffness=1000,
                     wood_bedding=1, newton_limit=300, wall_seconds=1770)
    monkeypatch.setattr(sys, "argv", argv)
    with pytest.raises(ParserChainReached, match="frozen command parsers accepted"):
        driver.main()  #Actual lean→incremental→continuation→common→finished→writer parsers.
    assert sys.argv == argv
    assert not (tmp_path / "field.json").exists()


def test_method_receipt_exclusive_input_and_raw_source_pins(monkeypatch, tmp_path):
    receipt_path = tmp_path / "method.json"
    source = tmp_path / "source.py"
    source.write_bytes(b"loaded frozen source")
    sources = {"source.py": hashlib.sha256(source.read_bytes()).hexdigest()}
    monkeypatch.setattr(driver, "METHOD_RECEIPT", receipt_path)
    monkeypatch.setattr(driver.frame, "ROOT", tmp_path)
    monkeypatch.setattr(driver, "method_sources", lambda: sources)
    driver.write_method_input_receipt(receipt_path, validation={"checks_pass": True, "passed_tests": 2, "command": ["pytest", "coupon"]})
    raw = receipt_path.read_bytes()
    pins, _ = driver.source_pins(receipt_path, hashlib.sha256(raw).hexdigest())
    assert pins["source.py"] == sources["source.py"]
    with pytest.raises(FileExistsError):
        driver.write_method_input_receipt(receipt_path, validation={"checks_pass": True, "passed_tests": 2, "command": ["pytest"]})
    source.write_bytes(b"changed")
    with pytest.raises(ValueError, match="input changed"):
        driver.source_pins(receipt_path, hashlib.sha256(raw).hexdigest())
    assert receipt_path.read_bytes() == raw
