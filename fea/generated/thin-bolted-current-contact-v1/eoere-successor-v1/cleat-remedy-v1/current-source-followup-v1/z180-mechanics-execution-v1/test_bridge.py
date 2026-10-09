"""Inert source/panel/orchestration controls; never construct candidate inputs."""
from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import pytest

OWN = Path(__file__).resolve()
spec = importlib.util.spec_from_file_location("eoere_z180_execution_inert_fixture", OWN.with_name("bridge.py"))
a = importlib.util.module_from_spec(spec)
spec.loader.exec_module(a)


def fixture():
    authority = a.manifest()
    panel_ids = ["panel_" + str(i) for i in range(6)]
    observations = [{"id": name, "source": {"path": name + ".brep", "sha256": "a"*64},
                     "center_xyz_mm": [1., 2., 3.], "volume_mm3": 100.} for name in panel_ids]
    observations += [{"id": "wood_" + str(i)} for i in range(22)]
    owners = [{"id": name, "kind": "panel", "center_xyz_mm": [1., 2., 3.]} for name in panel_ids]
    owners += [{"id": "owner_" + str(i), "kind": "shaft" if i < 100 else "timber"} for i in range(144)]
    parent = {"source_sha256": {}, "parameters": {"wood_density_kg_m3": 500}, "material_scenario": {"original": True},
        "support": authority["support"], "raw_gross_timber_rows": [], "fitting_poses": [], "fitting_ports": [],
        "all_factory_holes": [], "hillman_rows": [{"source_screw_descriptor": {"id": i}} for i in range(66)],
        "current_panel_machining_descriptors": {"features": [{"id": i} for i in range(340)]},
        "finished_body_observations": observations, "physical_owner_gravity_rows": owners}
    axis_ids = authority["declared_changes"]["axis_ids"] + ["axis_" + str(i) for i in range(96)]
    parent["shafts"] = [{"axis_id": axis_id, "point": [0., 0., 200.],
        "source_axis": {"id": axis_id, "point_xyz_mm": [0., 0., 200.], "nominal_under_head_length_mm": 101.6},
        "metal_roles": [{"id": axis_id + "/" + str(i), "center_of_mass_xyz_mm": [0., 0., 200.], "volume_mm3": 1.} for i in range(5)]}
        for axis_id in axis_ids]
    exported = {**copy.deepcopy(parent), "schema": a.DESCRIPTOR_SCHEMA, "geometry": a.GEOMETRY,
        "manifest": a.SOURCE_MANIFEST, "parent_descriptors": a.PARENT_DESCRIPTOR, "parent_geometry": authority["parent_geometry"],
        "status": "SOURCE_ONLY_UNADOPTED_Z180_DESCRIPTORS_PENDING_INDEPENDENT_REVIEW",
        "source_pins_before_after_unchanged": True, "native_CAD_BREP_import_K_panel_preparation_response_or_solve_performed": False,
        "current_4in_hardware_retained_spacer_proposal_excluded": True,
        "historical_q_forces_operators_or_acceptance_transferred": False, "force_execution_readiness_claimed": False,
        "complete_joint_resistance": None, "release": {"candidate_admitted": False},
        "finished_receiver_wall_queries": [None]*120,
        "direct_contacts": [], "flange_domains": [], "flange_shared_face_patches": [],
        "timber_and_panel_shared_face_patches": [], "shared_pair_query_census": [], "floor_observations": [],
        "geometry_delta_proof": {"counts": {"finished_owners_changed": 4, "shaft_axes_changed": 4,
            "hardware_role_locations_changed": 20, "wall_occurrences_moved": 8, "wall_occurrences_rebound_same_axis": 8,
            "contact_patches_rebuilt": 2, "contact_cells_rebuilt": 12, "physical_owners": 150, "shafts": 100, "Hillman_screws": 66}}}
    exported["source_sha256"] = {ref["path"]: ref["sha256"] for ref in
        (a.GEOMETRY, a.SOURCE_MANIFEST, a.PARENT_DESCRIPTOR, authority["saved_finished_receiver_evidence"])}
    for shaft in exported["shafts"][:4]:
        shaft["point"][2] = shaft["source_axis"]["point_xyz_mm"][2] = 180.
        for role in shaft["metal_roles"]:
            role["center_of_mass_xyz_mm"][2] = 180.
    layout = {"proposed_axes": [row["source_axis"] for row in exported["shafts"][:4]]}
    descriptor_ref = {"path": "synthetic-descriptor.json", "sha256": "d"*64}
    data = {key: copy.deepcopy(exported[source]) for key, source in a.ROW_JOINS.items()}
    data.update(schema=a.INPUT_SCHEMA, optional_2026_extra=False, release=dict(a.RELEASE),
        historical_q=None, old_field=None, geometry={"report": a.GEOMETRY, "source_manifest": a.SOURCE_MANIFEST,
        "cached_source_export": descriptor_ref}, source_sha256={**exported["source_sha256"], descriptor_ref["path"]: descriptor_ref["sha256"]},
        base_bodies=[row for row in exported["physical_owner_gravity_rows"] if row["kind"] != "shaft"],
        floor_footprints={}, parameters=copy.deepcopy(exported["parameters"]), scenario=copy.deepcopy(exported["material_scenario"]),
        panel_ids=sorted(panel_ids), factory_holes=[], case={"case_id": "synthetic-case"},
        panel_operator_source_inputs={"geometry": authority["parent_geometry"]})
    actual_read = a.read_ref
    def read(ref):
        if ref == descriptor_ref:
            return exported
        if ref == a.PARENT_DESCRIPTOR:
            return parent
        if ref == a.GEOMETRY:
            return layout
        return actual_read(ref)
    return parent, exported, data, read


@pytest.mark.parametrize("schema", ["eoere_extended_cleat_cached_source_export/v1", "eoere_lower_cleat_z180_geometry_patch/v1"])
def test_old_or_layout_only_descriptor_rejected_before_source_joins(schema):
    _, exported, _, _ = fixture()
    exported["schema"] = schema
    with pytest.raises(ValueError, match="distinct complete source-only"):
        a.validate_descriptor(exported)


def test_distinct_source_joins_then_old_input_and_mismatched_own_rows_reject():
    _, exported, data, read = fixture()
    with patch.object(a, "read_ref", side_effect=read):
        assert a.require_sources(data)["cached_source_export"] is exported
        changed = copy.deepcopy(data)
        changed["schema"] = "eoere_extended_cleat_first_order_mechanics_inputs/v1"
        with pytest.raises(ValueError, match="distinct own Z180"):
            a.require_sources(changed)
        changed = copy.deepcopy(data)
        changed["shafts"][0]["axis_id"] = "old_axis"
        with pytest.raises(ValueError, match="descriptor join differs: shafts"):
            a.require_sources(changed)
        changed = copy.deepcopy(data)
        changed["geometry"]["report"] = a.manifest()["parent_geometry"]
        with pytest.raises(ValueError, match="exact proposal layout"):
            a.require_sources(changed)


def test_native_relabel_and_missing_proposal_source_pin_rejected():
    _, exported, _, read = fixture()
    with patch.object(a, "read_ref", side_effect=read):
        exported["native_cached_solid_queries_performed"] = True
        with pytest.raises(ValueError, match="relabeled native-current"):
            a.validate_descriptor(exported)
        del exported["native_cached_solid_queries_performed"]
        del exported["source_sha256"][a.SOURCE_MANIFEST["path"]]
        with pytest.raises(ValueError, match="outside source closure"):
            a.validate_descriptor(exported)


def test_original_panel_source_geometry_and_own_sources_COM_apertures_ports():
    _, _, data, read = fixture()
    with patch.object(a, "read_ref", side_effect=read):
        view, proof = a.panel_view(data, data["panel_operator_source_inputs"])
        assert view["geometry"]["report"] == a.manifest()["parent_geometry"]
        assert data["geometry"]["report"] == a.GEOMETRY and proof["apertures"] == 340 and proof["screw_ports"] == 66
        changed = copy.deepcopy(data)
        changed["finished_body_observations"][0]["center_xyz_mm"][0] += 1.
        with pytest.raises(ValueError, match="six unchanged own"):
            a.panel_view(changed, data["panel_operator_source_inputs"])
        changed = copy.deepcopy(data)
        changed["current_panel_machining_descriptors"]["features"].pop()
        with pytest.raises(ValueError, match="unchanged own340"):
            a.panel_view(changed, data["panel_operator_source_inputs"])


def test_missing_own_review_stops_proxy_before_any_bank_callback():
    bank = SimpleNamespace(source_inputs=lambda: pytest.fail("missing review reached bank metadata"))
    with pytest.raises(ValueError, match="own raw source review required"):
        a.PanelProxy(bank).load_panel_dependencies({})


def test_proxy_authorization_and_explicit_original_identity_precede_bank_load():
    _, _, data, read = fixture()
    events = []
    inputs_ref = {"path": "synthetic-own-input.json", "sha256": "e"*64}
    original_inputs = data["panel_operator_source_inputs"]
    def raw_read(ref):
        return data if ref == inputs_ref else read(ref)
    def authenticate(*_args, **_kwargs):
        events.append("own_review")
    def source_inputs():
        events.append("original_panel_metadata")
        return original_inputs
    def load(view):
        assert view["geometry"]["report"] == original_inputs["geometry"]
        events.append("original_bank_load")
        return {}, {}, {}, {"source_inputs": original_inputs}
    b = SimpleNamespace(driver=SimpleNamespace(select_case=lambda raw, _case: (raw, {"selected": True})),
                        source_pins=lambda pins: pins, authenticate_review=authenticate)
    proxy = a.PanelProxy(SimpleNamespace(source_inputs=source_inputs, load_panel_dependencies=load), b)
    proxy.method = {"input": inputs_ref, "input_review": {"path": "own_review", "sha256": "f"*64}}
    with patch.object(a, "read_ref", side_effect=raw_read):
        _, _, _, proof = proxy.load_panel_dependencies(data)
    assert events == ["own_review", "original_panel_metadata", "original_bank_load"]
    assert proof["reuse"]["proposal_geometry"] == a.GEOMETRY
    assert proof["original_panel_preparation"]["source_inputs"]["geometry"] != a.GEOMETRY


def test_actual_deferred_run_missing_review_rejects_before_methods_and_restores_context(tmp_path):
    w = a.production()
    b = w.frozen()
    dummy = tmp_path / "source.json"
    ref = lambda digest: {"path": b.bundle.artifact_path(dummy), "sha256": digest}
    args = SimpleNamespace(run=True, case_id="a12-rear", wall_seconds=10., out=tmp_path / "field.json",
        inputs=dummy, inputs_sha256="a"*64, input_review=dummy, input_review_sha256="b"*64,
        method_input=dummy, method_input_sha256="c"*64)
    method = {"input": ref(args.inputs_sha256), "input_review": ref(args.input_review_sha256),
              "input_record": ref(args.method_input_sha256)}
    events = []
    def reject_review(*_args, **_kwargs):
        events.append("exact_own_review")
        raise ValueError("own independent review missing")
    with patch.object(a, "read_method", return_value=method), patch.object(a, "source_pins", return_value={}), \
            patch.object(b, "slot_check", return_value={}), \
            patch.object(b, "read_inputs", return_value=({"raw": True}, {})), \
            patch.object(b.driver, "select_case", return_value=({"selected": True}, {"case_id": args.case_id})), \
            patch.object(b, "authenticate_review", side_effect=reject_review), \
            patch.object(a, "methods", side_effect=AssertionError("invalid review reached panel methods")), \
            pytest.raises(ValueError, match="own independent review missing"):
        a.run_case(args)
    assert events == ["exact_own_review"]
    assert b.OWN == w.FROZEN and b.LOADED_SHA == w.FROZEN_SHA
    assert b.factory.SCHEMA == b.ORIGINAL_SCHEMA and b.factory.read_inputs is b.ORIGINAL_READ
    failed = json.loads(args.out.read_bytes())
    assert failed["status"] == "FAILED" and failed["accepted_q"] is None and failed["accepted_actions"] is None


@pytest.mark.parametrize("kind", ["file", "dangling_symlink"])
def test_existing_output_refused_before_frozen_import(tmp_path, kind):
    out = tmp_path / "existing.json"
    out.write_text("preserved") if kind == "file" else out.symlink_to(tmp_path / "absent.json")
    with patch.object(a.production(), "frozen", side_effect=AssertionError("occupied output reached mechanics import")), \
            pytest.raises(FileExistsError):
        a.main(["--out", str(out)])
    assert out.read_text() == "preserved" if kind == "file" else out.is_symlink()


def test_default_preflight_truthful_no_candidate_or_panel_callback(tmp_path):
    w = a.production()
    b = w.frozen()
    def prohibited(*_args, **_kwargs):
        raise AssertionError("source preflight reached candidate work")
    with patch.object(b.factory, "prepare", side_effect=prohibited), patch.object(a, "methods", side_effect=prohibited), \
            patch.object(a, "build_inputs", side_effect=prohibited), patch.object(a, "validate_descriptor", side_effect=prohibited):
        out = tmp_path / "source-only.json"
        assert a.main(["--out", str(out)]) == 0
    result = json.loads(out.read_bytes())
    assert result["missing"] == ["source_export", "inputs", "input_review", "method_input", "source_manifest", "panel_bank"]
    assert result["production_readiness_claimed"] is False and result["complete_joint_resistance"] is None
    assert result["candidate_descriptor_or_input_construction_panel_K_frame_K_q_actions_solve_or_native_work_performed"] is False
    assert result["support"] == b.law.contract() and result["generalized_residual_tolerance_n_inclusive"] == 1e-5
    assert not any(result["release"].values()) and result["unadopted_proposal"] is True


def test_source_pin_conflict_not_silently_replaced():
    with pytest.raises(ValueError, match="proposal source pin conflict"):
        a.source_pins(None, None, {a.GEOMETRY["path"]: "0"*64})


def test_own_method_rejects_missing_descriptor_review_before_authentication():
    _, _, data, read = fixture()
    input_ref = {"path": "synthetic-own-input.json", "sha256": "e"*64}
    record = {"parent_execution_bridge_readiness_pass": True, "unchanged_panel_reuse_independently_reviewed": True,
              "input": input_ref, "source_export": data["geometry"]["cached_source_export"]}
    b = SimpleNamespace(z180_original_read_method=lambda *_args: record,
                        authenticate_review=lambda *_args: pytest.fail("missing descriptor review reached input authentication"))
    with patch.object(a, "read_ref", side_effect=lambda ref: data if ref == input_ref else read(ref)), \
            pytest.raises(ValueError, match="own independent proposal descriptor review required"):
        a.read_method(b, Path("synthetic-method.json"), "f"*64)


def test_own_pending_identity_and_unchanged_inclusive_force_tolerance():
    w = a.production()
    b = w.frozen()
    with a.context(w, b):
        pending = b.admission_functions()["require_pending_field"]
        normals = dict.fromkeys(b.law.RESTRAINED_HOSTS, 1.)
        field = {"schema": a.FIELD_SCHEMA, "release": dict(a.RELEASE),
            "disposition": "CONVERGED_CANDIDATE_PENDING_INDEPENDENT_ADMISSION", "independent_admission_required": True,
            "usable_conditional_actions": True, "analytical_support_scenario": b.law.contract(), "response": {
                "converged": True, "q": [0.], "gradient_n": [1e-5], "q_canonical_sha256": b.canonical([0.]),
                "gradient_canonical_sha256": b.canonical([1e-5]), "gradient_inf_n": 1e-5,
                "original_floor_switching_law_used": False, "original_joint_and_normal_laws_used": True,
                "physical_residual_uses_unmodified_laws": False, "physical_residual_uses_declared_support_scenario": True,
                "generalized_residual_tolerance_n": 1e-5, "legacy_nonbearing_key_means_disabled_xy_hosts": True,
                "fixed_floor_support_v1": {**b.law.contract(), "normal_force_n_by_host": normals, "both_credited_legs_in_bearing": True}}}
        pending(field)
        changed = copy.deepcopy(field)
        changed["schema"] = "eoere_extended_cleat_fixed_floor_candidate/v1"
        with pytest.raises(ValueError, match="distinct converged pending"):
            pending(changed)
        changed = copy.deepcopy(field)
        changed["response"]["gradient_n"] = [1.00000001e-5]
        changed["response"]["gradient_inf_n"] = 1.00000001e-5
        changed["response"]["gradient_canonical_sha256"] = b.canonical([1.00000001e-5])
        with pytest.raises(ValueError, match="tolerance differ"):
            pending(changed)


def test_gravity_Z_translation_wrench_invariant_and_X_translation_rejects():
    original = {"floor_footprints": {"leg": [[0., 0., 0.]]}, "cases": [{"case_id": "known-answer", "loads": [
        {"point_xyz_mm": [2., 3., 4.], "force_xyz_n": [0., 0., -10.]},
        {"point_xyz_mm": [5., 6., 7.], "force_xyz_n": [20., 30., -40.]}]}]}
    own = copy.deepcopy(original)
    own["cases"][0]["loads"][0]["point_xyz_mm"][2] -= 20.
    with patch.object(a, "read_ref", return_value=original):
        proof = a.input_reuse_checks(own)
        assert proof["absolute_errors"]["known-answer"] == [0.]*6 and proof["same_floor_points"] is True
        own["cases"][0]["loads"][0]["point_xyz_mm"][0] += 1.
        with pytest.raises(ValueError, match="fresh source applied wrench changed"):
            a.input_reuse_checks(own)
