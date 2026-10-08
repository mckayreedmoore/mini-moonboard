"""Tiny original-law/replay and nested-writer fixtures; no candidate solve."""
from __future__ import annotations

import copy
import importlib.util
import json
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import numpy as np
import pytest
from scipy.sparse import csr_matrix, diags, eye, vstack

SPEC = importlib.util.spec_from_file_location("complete_timber_a12_runner", Path(__file__).with_name("runner.py"))
R = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(R)


@pytest.fixture
def tiny(tmp_path, monkeypatch):
    monkeypatch.setattr(R, "relative", lambda path: str(Path(path).resolve()))
    K = diags([2., 3., 4.], format="csr")
    applied = np.asarray([1., -2., 3.])
    groups = [{"id": "fixture/group", "kind": "fixture", "first": "wood", "second": "shaft",
        "ka": 5., "kl": 7., "clearance": .25, "tension_only": True, "B": eye(3, format="csr")}]
    contacts = [{"id": "wood/face", "kind": "timber_face_contact", "first": "wood", "second": "neighbor",
        "stiffness": 11., "point_xyz_mm": [0., 0., 0.], "direction_xyz": [1., 0., 0.],
        "B": csr_matrix([[1., 0., 0.]])},
        {"id": "wood/floor", "kind": "floor_normal", "first": "wood", "second": "floor",
         "stiffness": 13., "point_xyz_mm": [0., 0., 0.], "direction_xyz": [0., 0., 1.],
         "B": csr_matrix([[0., 0., 1.]])}]
    tangents = [{"id": "wood/x", "kind": "floor_tangent", "first": "wood", "second": "floor",
                 "stiffness": 100000., "B": csr_matrix([[1., 0., 0.]])},
                {"id": "wood/y", "kind": "floor_tangent", "first": "wood", "second": "floor",
                 "stiffness": 100000., "B": csr_matrix([[0., 1., 0.]])}]
    return tmp_path, K, applied, groups, contacts, tangents


def captured(tiny):
    directory, K, applied, groups, contacts, tangents = tiny
    manifest, arrays, record = R.capture_operators(K, applied, groups, contacts, tangents,
        directory=directory, pins={}, command=["fixture-only"], receipt={"path": "fixture", "sha256": "fixture"})
    return {"directory": directory, "inputs": (K, applied, groups, contacts, tangents),
        "operator_manifest": manifest, "operator_arrays": arrays, "operator_record": record, "pins": {}}


def linear_with_floor(K, tangents, enabled=True):
    result = K.copy()
    if enabled:
        for row in tangents:
            result += row["stiffness"] * (row["B"].T @ row["B"])
    return result


def test_original_fields_has_hand_computed_gradient_energy_and_replay(tiny):
    context = captured(tiny)
    _, K, applied, groups, contacts, tangents = tiny
    q = np.asarray([.5, -.4, .3])
    linear = linear_with_floor(K, tangents)
    C = vstack([r["B"] for r in contacts], format="csr")
    fields = R.KNOWN_ORIGINAL_FIELDS(linear, applied, groups, C, np.asarray([11., 13.]), q, tangent=False)
    np.testing.assert_allclose(fields[0], [50008., -40000.6, 3.15], rtol=0., atol=1e-10)
    assert fields[1] == pytest.approx(20501.27375, abs=1e-10)
    replay = R.admission.replay_original_gradient({"response": {"q": q.tolist(),
        "nonbearing_no_slip_removed": []}}, context["operator_manifest"], context["operator_arrays"],
        observed_enabled_hosts=["wood"], observed_linear_K=linear)
    assert replay["same_state_support_mask_consistent"]
    assert replay["observed_branch"]["gradient_canonical_sha256"] == R.canonical_sha(fields[0].tolist())
    assert replay["demanded_floor_law_branch"] == replay["observed_branch"]
    with np.load(tiny[0] / "operators.npz", allow_pickle=False) as saved:
        assert set(saved.files) == set(context["operator_arrays"])
        for key in saved.files:
            np.testing.assert_array_equal(saved[key], context["operator_arrays"][key])
    assert json.loads((tiny[0] / "operator-inputs.json").read_text()) == context["operator_manifest"]


def test_unsorted_source_csr_order_and_exact_floating_replay_are_retained(tiny):
    _, K, applied, groups, contacts, tangents = tiny
    groups[0]["B"] = csr_matrix((np.asarray([.5, 1., -.3, 1., 1.]),
        np.asarray([2, 0, 1, 1, 2]), np.asarray([0, 3, 4, 5])), shape=(3, 3))
    contacts[0]["B"] = csr_matrix((np.asarray([.1, 1.]), np.asarray([2, 0]), np.asarray([0, 2])), shape=(1, 3))
    assert not groups[0]["B"].has_sorted_indices and not contacts[0]["B"].has_sorted_indices
    C = vstack([r["B"] for r in contacts], format="csr")
    context = captured(tiny)
    manifest, arrays = context["operator_manifest"], context["operator_arrays"]
    assert manifest["retained_source_CSR_order"] and manifest["no_operator_numeric_or_sparsity_normalization"]
    for original, descriptor in ((groups[0]["B"], manifest["groups"][0]["B"]), (C, manifest["C"])):
        replayed = R.admission.read_csr(arrays, descriptor)
        assert not replayed.has_sorted_indices
        for name in ("data", "indices", "indptr"):
            np.testing.assert_array_equal(getattr(replayed, name), getattr(original, name))
    q = np.asarray([.5, -.4, .3])
    linear = linear_with_floor(K, tangents)
    actual = R.KNOWN_ORIGINAL_FIELDS(linear, applied, groups, C, np.asarray([11., 13.]), q)
    replay = R.admission.replay_original_gradient({"response": {"q": q.tolist(),
        "nonbearing_no_slip_removed": []}}, manifest, arrays,
        observed_enabled_hosts=["wood"], observed_linear_K=linear)
    assert replay["observed_branch"]["gradient_canonical_sha256"] == R.canonical_sha(actual[0].tolist())
    assert replay["observed_branch"]["potential_energy_nmm"] == actual[1]


@pytest.mark.parametrize("q_kind", ["q", "diagnostic_last_q"])
def test_fresh_final_q_capture_matches_independent_full_vector_and_hashes(tiny, q_kind):
    context = captured(tiny)
    context["last_linear"] = linear_with_floor(tiny[1], tiny[-1])
    report = {"response": {q_kind: [.5, -.4, .3], "gradient_inf_n": 0.},
              "source_sha256": {}, "complete_timber_a12_execution": {}}
    original = R.numerical.physical_fields
    R.final_gradient_capture(report, context)
    assert R.numerical.physical_fields is original
    replay = report["response"]["original_gradient_replay_v1"]
    assert replay["diagnostic_only"] == (q_kind != "q")
    assert replay["observed_branch"]["gradient_inf_n"] == pytest.approx(50008.)
    capture = json.loads((tiny[0] / "final-branch-inputs.json").read_bytes())
    assert capture["controller_claimed_gradient_inf_n"] == 0.
    assert capture["gradient_inf_n"] > 50000.
    assert capture["gradient_canonical_sha256"] == replay["observed_branch"]["gradient_canonical_sha256"]
    with np.load(tiny[0] / "final-branch-operators.npz", allow_pickle=False) as saved:
        np.testing.assert_array_equal(saved["gradient"], capture["full_signed_gradient_n"])
        np.testing.assert_array_equal(saved["q"], report["response"][q_kind])
    for name, digest in report["source_sha256"].items():
        assert R.frame.sha(Path(name)) == digest
    assert not replay["current_action_admission_or_capacity_established"]


def test_failed_q_preserves_actual_and_demanded_floor_patterns(tiny):
    context = captured(tiny)
    context["last_linear"] = tiny[1].copy()
    report = {"response": {"converged": False, "diagnostic_last_q": [.5, -.4, .3]},
              "source_sha256": {}, "complete_timber_a12_execution": {}}
    R.final_gradient_capture(report, context)
    replay = report["response"]["original_gradient_replay_v1"]
    assert replay["observed_enabled_centroid_xy_hosts"] == []
    assert replay["demanded_enabled_centroid_xy_hosts"] == ["wood"]
    assert replay["same_state_support_mask_consistent"] is False
    assert replay["diagnostic_only"]
    assert "q" not in report["response"]
    assert report["response"]["converged"] is False
    assert replay["observed_branch"]["gradient_inf_n"] < 20.
    assert replay["demanded_floor_law_branch"]["gradient_inf_n"] > 50000.


def test_observed_operator_corruption_cannot_be_called_original(tiny):
    context = captured(tiny)
    context["last_linear"] = tiny[1] + diags([1., 0., 0.], format="csr")
    report = {"response": {"diagnostic_last_q": [0., 0., 0.]}, "source_sha256": {},
              "complete_timber_a12_execution": {}}
    with pytest.raises(ValueError, match="original on/off pattern"):
        R.final_gradient_capture(report, context)
    assert not (tiny[0] / "final-branch-inputs.json").exists()


def test_missing_q_is_an_explicit_unavailable_diagnostic(tiny):
    context = captured(tiny)
    report = {"response": {"converged": False, "diagnostic_last_q": None}}
    R.final_gradient_capture(report, context)
    assert "original_gradient_replay_unavailable" in report["response"]
    assert "original_gradient_replay_v1" not in report["response"]


def test_full_source_geometry_coupon_nested_stamp_has_no_module_recursion():
    assert R.adapter.linear is R.lean.faces
    data, _ = R.adapter.read_inputs()
    grain = R.adapter.grain_geometry(data[R.adapter.FRAME_GEOMETRY], data[R.adapter.ATLAS])
    assembly = R.adapter.geometry_only_coupon_assembly(grain)
    assert not hasattr(assembly, "K")
    prepared = R.adapter.prepare_complete_timber_faces(assembly)
    q = np.zeros(assembly.ndof)
    actions = R.adapter.contact_response(prepared, q)["contact_actions"]
    with patch.object(R.lean.faces, "stamp_recovered_actions", R.stamp_complete_once):
        result = R.lean.faces.stamp_recovered_actions({"contact_actions": actions}, prepared, q)
        assert R.lean.faces.stamp_recovered_actions is R.stamp_complete_once
        assert len(result["timber_face_contact_actions"]) == 584
        assert result["linear_timber_face_method"] == R.adapter.BASIS
        assert len({r["source_descriptor"]["patch_id"] for r in result["timber_face_contact_actions"]}) == 30
    assert R.lean.faces.stamp_recovered_actions is R.KNOWN_ORIGINAL_STAMP


def test_common_constructor_alias_preserves_exact_existing_assembly_preparation():
    data, _ = R.adapter.read_inputs()
    grain = R.adapter.grain_geometry(data[R.adapter.FRAME_GEOMETRY], data[R.adapter.ATLAS])
    assembly = R.adapter.geometry_only_coupon_assembly(grain)
    assert type(assembly) is R.KNOWN_ELASTIC_ASSEMBLY and not hasattr(assembly, "K")
    original_map = R.canonical_sha(R.lean.faces.timber_coordinate_map(assembly))

    def common_constructor(*args, **kwargs):
        pytest.fail("existing coupon must not instantiate or rebuild K")

    with patch.object(R.frame, "ElasticAssembly", common_constructor):
        result = R.prepare_complete_once(assembly, bedding_n_mm3=1.)
        assert R.frame.ElasticAssembly is common_constructor
        assert len(result["contacts"]) == 584
        assert R.canonical_sha(result["coordinate_map"]) == original_map
        assert not hasattr(assembly, "K")
        with pytest.raises(ValueError, match="existing frozen ElasticAssembly"):
            R.prepare_complete_once(SimpleNamespace(), bedding_n_mm3=1.)
    assert R.frame.ElasticAssembly is R.KNOWN_ELASTIC_ASSEMBLY


def test_genuine_adapter_raw584_rows_survive_npz_and_runtime_contact_subset_hash(tmp_path, monkeypatch):
    monkeypatch.setattr(R, "relative", lambda path: str(Path(path).resolve()))
    data, _ = R.adapter.read_inputs()
    grain = R.adapter.grain_geometry(data[R.adapter.FRAME_GEOMETRY], data[R.adapter.ATLAS])
    assembly = R.adapter.geometry_only_coupon_assembly(grain)
    prepared = R.adapter.prepare_complete_timber_faces(assembly)
    assert assembly.ndof == 240 and not hasattr(assembly, "K")
    rows = prepared["contacts"]
    native = vstack([r["B"] for r in rows], format="csr")
    assert not native.has_sorted_indices
    # Two empty numeric rows stand only for placement within a larger matrix;
    # this240-coordinate coupon is never a production operator or state.
    full = vstack([csr_matrix((1, assembly.ndof)), native, csr_matrix((1, assembly.ndof))], format="csr")
    arrays = {}
    descriptor = R.put_csr(arrays, "C", full)
    record = R.write_arrays(tmp_path / "coupon-only.npz", arrays)
    with np.load(record["path"], allow_pickle=False) as saved:
        runtime = R.admission.read_csr(saved, descriptor)
    subset = runtime[np.arange(1, 585)]
    for key in ("data", "indices", "indptr"):
        np.testing.assert_array_equal(getattr(subset, key), getattr(native, key))
    replayed_rows = [{**row, "B": subset[index]} for index, row in enumerate(rows)]
    assert R.adapter.contact_operator_sha(replayed_rows) == prepared["metadata"]["contact_operator_sha256"]
    assert not hasattr(assembly, "K")


@pytest.mark.parametrize("extra", [["--warm-start", "old.json"], ["--cases", "a12-front"],
    ["--wood-bedding", "2"], ["--wall-seconds", "601"], ["--newton-limit", "301"],
    ["--floor-tangent-stiffness", "1000"], ["--intervals", "16"]])
def test_scope_rejects_changed_physics_or_historical_initialization(extra):
    args = ["--method-input", str(R.PACKET / "method-input.json"), "--method-input-sha256", "fixture",
            "--out", str(R.PACKET / "fixture-field.json"), *extra]
    with pytest.raises((ValueError, SystemExit)):
        R.parse_options(args)


def test_immutable_signature_detects_port_force_and_material_changes(tiny):
    _, *inputs = tiny
    base = R.immutable_operator_signature(*inputs)
    for key in ("material", "load", "group", "contact", "tangent"):
        K, applied, groups, contacts, tangents = copy.deepcopy(inputs)
        if key == "material":
            K.data[0] += 1.
        elif key == "load":
            applied[0] += 1.
        elif key == "group":
            groups[0]["B"].data[0] += 1.
        elif key == "contact":
            contacts[0]["stiffness"] += 1.
        else:
            tangents[0]["B"].data[0] += 1.
        assert R.immutable_operator_signature(K, applied, groups, contacts, tangents) != base


def test_nested_frozen_lean_seam_records_outer_command_before_identity_and_restores(tiny, monkeypatch):
    directory, K, applied, groups, contacts, tangents = tiny
    contacts = copy.deepcopy(contacts)
    contacts[0]["kind"] = "panel_contact"
    original_connections = lambda *a, **k: (groups, contacts, tangents)
    extra = [{**contacts[0], "id": "extra/face", "kind": "timber_face_contact"}]
    prepared = {"contacts": extra, "source_sha256": {}, "coordinate_map": {"fixture": True},
        "metadata": {"method": R.adapter.BASIS, "parameters": {
            "linear_timber_face_contact_basis": R.adapter.BASIS,
            "complete_timber_face_contact_physical_signature_sha256": "fixture-signature"}}}
    monkeypatch.setattr(R.frame, "elastic_connections", original_connections)
    monkeypatch.setattr(R, "prepare_complete_once", lambda *a, **k: prepared)
    monkeypatch.setattr(R.lean.saved_panels, "reuse_panel_operators", lambda: ({}, {}, {"fixture": True}))
    monkeypatch.setattr(R.common, "bind_common_metadata", lambda report, *_: report)
    monkeypatch.setattr(R, "verify_complete_census", lambda *a: None)
    monkeypatch.setattr(R.admission.linear, "verify_pins", lambda _: None)
    seen = {}

    def frozen_solver(material, rhs, actual_groups, actual_contacts, actual_tangents, *, max_iterations, warm_q):
        assert warm_q is None and max_iterations == 300
        assert (directory / "operators.npz").exists()
        C = vstack([r["B"] for r in actual_contacts], format="csr")
        ck = np.asarray([r["stiffness"] for r in actual_contacts])
        q = np.asarray([.5, -.4, .3])
        linear = linear_with_floor(material, actual_tangents)
        fields = R.incremental.ORIGINAL_FIELDS(linear, rhs, actual_groups, C, ck, q, tangent=True)
        return {"converged": False, "diagnostic_last_q": q.tolist(), "gradient_inf_n": float(abs(fields[0]).max())}

    def frozen_binder(report, proof, pins, driver_sha):
        assert report["counts"]["paired_timber_interfaces"] == 30
        assert report["counts"]["paired_timber_compression_cells"] == 584
        assert report["counts"]["normal_contacts"] == 1574
        assert report["parameters"]["complete_timber_a12_driver_sha256"] == R.LOADED_SHA256
        assert report["complete_timber_a12_execution"]["command"] == outer_command
        assert report["response"]["original_gradient_replay_v1"]["diagnostic_only"]
        assert report["complete_contact_admission_pending"]
        assert not report["complete_joint_acceptance"]
        assert report["usable_conditional_actions"] is False
        return R.common.finished.__test_original_binder(report, proof, pins, driver_sha)

    def frozen_main():
        R.lean.panel_tools.prepare_panel_models(R.frame.GEOMETRY_CACHE)
        actual_groups, actual_contacts, actual_tangents = R.frame.elastic_connections(SimpleNamespace())
        assert actual_contacts == contacts + extra
        response = R.incremental.compatible_contact_solve(K, applied, actual_groups, actual_contacts,
            actual_tangents, max_iterations=300, warm_q=None)
        report = {"parameters": {}, "source_sha256": {}, "counts": {"dofs": 8018, "structural_bodies": 132},
            "response": response, "limits": [], "release": copy.deepcopy(R.frame.RELEASE),
            "case_id": "a12-rear", "accessory_placement": "rear", "state_id": "fixture-old",
            "geometry_cache_sha256": "fixture-only", "usable_conditional_actions": False}
        report = R.common.bind_common_metadata(report, None, {}, [])
        # The lean wrapper initially writes6/272; outer finish must correct it.
        assert report["counts"]["paired_timber_interfaces"] == 6
        seen["field"] = R.common.finished.bind_finished_state(report, [], {}, "fixture-driver")

    monkeypatch.setattr(R.incremental, "compatible_contact_solve", frozen_solver)
    monkeypatch.setattr(R.lean.reused, "main", frozen_main)
    monkeypatch.setattr(R.common.finished, "__test_original_binder", R.common.finished.bind_finished_state, raising=False)
    monkeypatch.setattr(R.common.finished, "bind_finished_state", frozen_binder)
    options = SimpleNamespace(out=directory / "field.json", method_input=directory / "method.json",
        method_input_sha256="fixture-receipt", wall_seconds=600.)
    arguments = ["--out", str(options.out), "--method-input", str(options.method_input)]
    outer_command = [sys.executable, str(Path(R.__file__).resolve()), *arguments]
    old_argv = sys.argv.copy()
    original_fields = R.incremental.ORIGINAL_FIELDS
    R.run_case(options, arguments, {"source_sha256": {}})
    assert sys.argv == old_argv
    assert R.frame.elastic_connections is original_connections
    assert R.incremental.compatible_contact_solve is frozen_solver
    assert R.incremental.ORIGINAL_FIELDS is original_fields
    assert R.common.finished.bind_finished_state is frozen_binder
    report = seen["field"]
    identity = {key: report[key] for key in ("case_id", "accessory_placement", "parameters", "geometry_cache_sha256")}
    assert report["state_id"] == "thin-v4-" + R.canonical_sha(identity)[:24]
    assert report["state_id"] != "fixture-old"


def test_existing_operator_export_cannot_be_overwritten(tiny):
    captured(tiny)
    before = (tiny[0] / "operators.npz").read_bytes()
    with pytest.raises(FileExistsError):
        captured(tiny)
    assert (tiny[0] / "operators.npz").read_bytes() == before


def test_method_freeze_and_runtime_reject_changed_source_or_unreviewed_checks(tmp_path, monkeypatch):
    pins = {"fixture-only-source": "a" * 64}
    monkeypatch.setattr(R, "method_sources", lambda: pins.copy())
    reviewed = {"focused_fixtures_pass": True, "independent_readiness_review_pass": True,
        "runner_sha256": R.LOADED_SHA256, "admission_sha256": R.admission.LOADED_PRODUCER_SHA256}
    for key in ("focused_fixtures_pass", "independent_readiness_review_pass"):
        with pytest.raises(ValueError, match="parent-supplied"):
            R.freeze_method_inputs(tmp_path / (key + ".json"), reviewed_checks={**reviewed, key: False})
    path = tmp_path / "method-input.json"
    receipt = R.freeze_method_inputs(path, reviewed_checks=reviewed)
    assert receipt["method_checks_pass"]
    assert not receipt["execution_authorization_supplied_by_receipt"]
    assert R.read_method_inputs(path, R.frame.sha(path)) == receipt
    pins["fixture-only-source"] = "b" * 64
    with pytest.raises(ValueError, match="parent-frozen method inputs differ"):
        R.read_method_inputs(path, R.frame.sha(path))
    with pytest.raises(ValueError, match="method-input bytes differ"):
        R.read_method_inputs(path, "0" * 64)


def test_census_guard_accepts_only_the_complete_current_row_counts():
    # Dimensions/counts only, no matrix entries, member operators or solve.
    K = csr_matrix((8018, 8018))
    groups = [{"kind": "common_shaft_bearing"}] * 308 + [{"kind": "panel_screw"}] * 66
    contacts = [{"id": f"{kind}/{i}", "kind": kind} for kind, count in (
        ("timber_face_contact", 584), ("shaft_end_capture", 140), ("floor_normal", 32),
        ("flange_contact", 288), ("panel_contact", 530)) for i in range(count)]
    tangents = [{"first": f"floor-{i // 2}"} for i in range(16)]
    R.verify_complete_census(K, groups, contacts, tangents)
    for modified in (contacts[:-1], [*contacts, contacts[0]],
                     [{**contacts[0], "kind": "shaft_end_capture"}, *contacts[1:]]):
        with pytest.raises(ValueError, match="current operator census differs"):
            R.verify_complete_census(K, groups, modified, tangents)
    with pytest.raises(ValueError, match="current operator census differs"):
        R.verify_complete_census(K, [{"kind": "fitting_bolt"}] * 374, contacts, tangents)


def test_exception_restores_all_nested_patch_targets_and_argv(tmp_path, monkeypatch):
    monkeypatch.setattr(R, "relative", lambda path: str(Path(path).resolve()))
    error = ValueError("fixture stop before any candidate preparation")

    def stop():
        raise error

    monkeypatch.setattr(R.lean, "main", stop)
    targets = [(R.lean.faces, "prepare_linear_timber_faces"), (R.lean.faces, "stamp_recovered_actions"),
        (R.incremental, "compatible_contact_solve"), (R.incremental, "ORIGINAL_FIELDS"),
        (R.common, "bind_common_metadata"), (R.common.finished, "bind_finished_state"),
        (R.lean, "write_interruption")]
    original = [getattr(module, name) for module, name in targets]
    argv = sys.argv.copy()
    options = SimpleNamespace(out=tmp_path / "field.json", method_input=tmp_path / "receipt.json",
        method_input_sha256="fixture", wall_seconds=600.)
    with pytest.raises(ValueError, match="fixture stop"):
        R.run_case(options, [], {"source_sha256": {}})
    assert sys.argv == argv
    assert all(getattr(module, name) is value for (module, name), value in zip(targets, original, strict=True))
    assert not list(tmp_path.iterdir())
