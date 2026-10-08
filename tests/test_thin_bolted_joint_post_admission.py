"""Synthetic/stub-admission orchestration checks; no production body proof."""

import copy
import hashlib
import json
import math

import numpy as np
import pytest

from scripts import thin_bolted_joint_post_admission as helper


def admission_fixture(tmp_path, monkeypatch):
    monkeypatch.setattr(helper, "ROOT", tmp_path)
    gate = tmp_path / helper.GATE
    gate.parent.mkdir(parents=True)
    gate.write_text("synthetic source identity only; not a production admission implementation")
    digest = hashlib.sha256(gate.read_bytes()).hexdigest()
    field = {"schema": "thin_bolted_common_shaft_frame/v1", "candidate": helper.unit.CANDIDATE,
        "linear_timber_face_method": "source-bound-linear-finished-paired-wood-compression-v1",
        "layout_report_sha256": helper.unit.LAYOUT_SHA, "geometry_cache_sha256": helper.references.NATIVE_SHA,
        "case_id": "synthetic", "accessory_placement": "synthetic", "parameters": {},
        "response": {"q": [0., 0.], "converged": True}, "counts": {"dofs": 2},
        "usable_conditional_actions": True, "release": dict(helper.unit.RELEASE),
        "source_sha256": {}, "attachment_actions": [], "retained_bolt_actions": []}
    field["state_id"] = helper.references.state_identity(field)
    payload = json.dumps(field).encode()
    receipt = {"schema": helper.ADMISSION_SCHEMA, helper.ADMISSION_SUCCESS: True,
        "field_sha256": hashlib.sha256(payload).hexdigest(),
        "field_canonical_sha256": helper.references.canonical_sha(field),
        "support_search_checks": {"final_q_canonical_sha256": helper.references.canonical_sha([0., 0.])},
        **{key: field[key] for key in helper.IDENTITIES},
        "source_sha256": {helper.GATE: digest}, "release": dict(helper.unit.RELEASE)}
    return payload, field, receipt, digest, gate


def test_one_immutable_payload_receipt_contract(tmp_path, monkeypatch):
    payload, field, receipt, digest, _ = admission_fixture(tmp_path, monkeypatch)
    helper.require_admission(payload, field, receipt, digest)
    with pytest.raises(ValueError, match="immutable"):
        helper.require_admission(bytearray(payload), field, receipt, digest)


@pytest.mark.parametrize("change", ["raw", "canonical", "state", "case", "accessory", "legacy", "success", "gate", "release", "diagnostic", "paired", "final-q"])
def test_unadmitted_or_mixed_identity_never_reaches_reductions(tmp_path, monkeypatch, change):
    payload, field, receipt, digest, gate = admission_fixture(tmp_path, monkeypatch)
    if change == "raw":
        receipt["field_sha256"] = "0"*64
    elif change == "canonical":
        receipt["field_canonical_sha256"] = "0"*64
    elif change in ("state", "case", "accessory"):
        key = {"state": "state_id", "case": "case_id", "accessory": "accessory_placement"}[change]
        receipt[key] = "different"
    elif change == "legacy":
        receipt["schema"] = "thin_bolted_independent_linear_timber_admission/v1"
    elif change == "success":
        receipt[helper.ADMISSION_SUCCESS] = False
    elif change == "gate":
        gate.write_text("changed source")
    elif change == "release":
        receipt["release"]["climbing_released"] = True
    elif change == "final-q":
        receipt["support_search_checks"]["final_q_canonical_sha256"] = "0"*64
    else:
        if change == "diagnostic":
            field["response"]["diagnostic_last_q"] = field["response"].pop("q")
        else:
            field["attachment_actions"] = [{"id": "manufactured-old-plane"}]
        payload = json.dumps(field).encode()
        receipt["field_sha256"] = hashlib.sha256(payload).hexdigest()
        receipt["field_canonical_sha256"] = helper.references.canonical_sha(field)
    calls = []
    monkeypatch.setattr(helper.references, "read_unit", lambda: calls.append("forbidden"))
    with pytest.raises(ValueError):
        helper.post_admission_reductions(payload, receipt, admission_sha256=digest)
    assert calls == []


def face_fixture():
    identity = {"state_id": "synthetic", "case_id": "synthetic", "accessory_placement": "synthetic"}
    fc = 625.*helper.unit.N_PER_LBF/25.4**2
    rows, members = [], []
    for pair, count in enumerate((46, 46, 45, 45, 45, 45)):
        first, second = f"a{pair}", f"b{pair}"
        members += [{"member": member, "grain_axis_xyz": [0., 0., 1.]} for member in (first, second)]
        for index in range(count):
            area = index+1.
            ratio = 2. if index == 0 else 0. if index == 1 else .5
            rows.append({**identity, "id": f"pair{pair}/cell{index}", "kind": "timber_face_contact",
                "first": first, "second": second, "point_xyz_mm": [0., float(index), 0.],
                "direction_xyz": [1., 0., 0.], "cell_area_mm2": area, "compression_n": area*fc*ratio})
    return {**identity, "contact_actions": rows, "timber_face_contact_actions": copy.deepcopy(rows)}, {"finished_member_sections": members}


def test_face_reference_area_preserves_zeros_both_grains_and_no_CD():
    field, full = face_fixture()
    summaries = helper.face_reference_summaries(field, full)
    assert sum(r["cell_count_including_zeros"] for r in summaries) == 272
    assert sum(r["loaded_cell_count"] for r in summaries) == 266
    for pair in summaries:
        witness = pair["governing_reference_area_cell_witness"]
        assert witness["reference_area_component_ratio"] == pytest.approx(2.)
        assert witness["normal_dot_each_reference_grain"] == {pair["first"]: 0., pair["second"]: 0.}
        assert witness["CD_factor"] == 1.
        assert witness["physical_pressure_or_complete_joint_capacity"] is None


@pytest.mark.parametrize("change", ["duplicate", "alias", "grain", "identity"])
def test_face_reference_rejects_alias_duplication_or_applicability_change(change):
    field, full = face_fixture()
    if change == "duplicate":
        field["contact_actions"][-1] = copy.deepcopy(field["contact_actions"][0])
    elif change == "alias":
        field["timber_face_contact_actions"][0]["compression_n"] += 1.
    elif change == "grain":
        full["finished_member_sections"][0]["grain_axis_xyz"] = [1., 0., 0.]
    else:
        field["contact_actions"][0]["case_id"] = "other"
        field["timber_face_contact_actions"] = copy.deepcopy(field["contact_actions"])
    with pytest.raises(ValueError):
        helper.face_reference_summaries(field, full)


def panel_fixture(tmp_path, monkeypatch):
    method = helper.panel.panel_method
    basis = method.SheetBasis(120., 80., 2)
    identity = {"state_id": "synthetic", "case_id": "synthetic", "accessory_placement": "synthetic"}
    axes = np.array([[1., 0., 0.], [0., math.cos(.3), -math.sin(.3)], [0., math.sin(.3), math.cos(.3)]])
    q = np.zeros(6*3*basis.size)
    state = {**identity, "source_sha256": {"scripts/thin_bolted_panel_mechanics.py": helper.panel.METHOD_SHA},
             "parameters": {"panel_intervals": 2}, "response": {"q": q.tolist()},
             "panel_generalized_coefficients": {}, "panel_screw_actions": []}
    sources, datums, layout = [], {}, {"screw_axes": []}
    for index, name in enumerate(method.PANELS):
        start = index*3*basis.size
        state["panel_generalized_coefficients"][name] = {"width_mm": 120., "height_mm": 80.,
            "basis_order_per_direction": basis.order, "coefficient_order": helper.panel.COEFFICIENT_ORDER,
            "knots_normalized": basis.knots.tolist(), "coefficients_mm": q[start:start+3*basis.size].tolist(),
            "global_dof_start": start}
        sources.append({"panel": name, "width_mm": 120., "height_mm": 80., "front_height_mm": 80., "support_footprints": []})
        datums[name] = {"origin_xyz_mm": [0., 0., 0.], "local_axes_columns_xyz": axes.tolist()}
        for local in range(11):
            axis = f"{name}/screw{local}"
            origin = np.array([10.+local, 20., 0.])
            force = axes[:, [2, 0, 1]]@np.array([17., 3., 4.])
            point = origin-axes[:, 2]*method.CAT/2
            layout["screw_axes"].append({"axis_id": axis, "panel": name, "receiver": "wood", "origin_xyz_mm": origin.tolist()})
            state["panel_screw_actions"].append({**identity, "axis_id": axis, "panel": name, "receiver": "wood",
                "point_xyz_mm": point.tolist(), "force_on_receiver_xyz_n": force.tolist(),
                "local_force_n": [17., 3., 4.], "withdrawal_n": 17., "lateral_n": 5.})
    for attr, value in (("ASSESSMENT", {"panel_geometry": sources}), ("DATUMS", datums)):
        path = tmp_path/(attr+".json")
        path.write_text(json.dumps(value)); monkeypatch.setattr(helper.panel, attr, path)
    integrated = tmp_path/"integrated.json"
    integrated.write_text(json.dumps({"panel_machining": {"features": []}}))
    monkeypatch.setattr(method, "INTEGRATED", integrated)
    # Existing edge mechanics are independently issued; the coupon has no actual
    # backing footprints and explicitly stubs only this unrelated diagnostic.
    monkeypatch.setattr(method, "edge_transfer_diagnostics", lambda *args: {"synthetic_stub_no_backing_proof": True})
    return state, layout


def test_real_saved_six_panel_slices_and_rotated_world_local_ports(tmp_path, monkeypatch):
    field, layout = panel_fixture(tmp_path, monkeypatch)
    result = helper.panel_reductions(field, layout, 3)
    assert len(result["panel_diagnostics"]) == 6
    assert len(result["screw_actions_and_generic_references"]) == 66
    assert result["all66_world_local_signed_screw_projections_verified"] is True
    assert all(r["same_axis_simultaneous_lateral_n"] == 5. for r in result["screw_actions_and_generic_references"])
    assert result["complete_panel_or_Hillman_product_resistance"] is None


@pytest.mark.parametrize("change", ["projection-sign", "slice", "datum", "mixed-state"])
def test_panel_projection_or_global_slice_tampering_fails(tmp_path, monkeypatch, change):
    field, layout = panel_fixture(tmp_path, monkeypatch)
    row = field["panel_screw_actions"][0]
    if change == "projection-sign":
        row["local_force_n"][1] *= -1.  # Same scalar magnitude, incorrect sign.
    elif change == "slice":
        field["response"]["q"][0] = 1.
    elif change == "datum":
        row["point_xyz_mm"][0] += 1.
    else:
        row["state_id"] = "different"
    with pytest.raises(ValueError):
        helper.panel_reductions(field, layout, 3)


def test_torsion_composition_uses_own_same_cut_vectors_without_old_receipt(monkeypatch):
    identity = {"state_id": "synthetic", "case_id": "synthetic", "accessory_placement": "synthetic"}
    fittings, rows = [], []
    force, moment = [100., 20., 30.], [40., 50., 60.]
    for index in range(36):
        angle = f"synthetic-angle{index}"
        fittings.append({"angle_id": angle})
        for flange in ("beam", "post"):
            rows.append({**identity, "angle_id": angle, "flange": flange, "external_point_actions_on_steel": [{"synthetic_own_port": True}]})
    received = []
    def synthetic_sections(fitting, flange, own):
        received.append((fitting["angle_id"], flange, own))
        return {"sections": [{"station_from_assumed_corner_mm": 10.,
            "area_mm2": (helper.torsion.frozen.WIDTH-5.)*helper.torsion.frozen.THICKNESS,
            "force_local_n": force, "moment_local_nmm": moment}]}
    monkeypatch.setattr(helper.torsion.frozen, "flange_reference", synthetic_sections)
    result = helper.flange_torsion_reductions(identity, {"fresh_flange_component_comparison": {"flange_comparisons": rows}}, {"raw_fittings": fittings})
    assert len(result) == len(received) == 72
    for row in result:
        for witness in row["sampled_scenario_witnesses"].values():
            assert witness["same_section_force_N_V1_V2_n"] == force
            assert witness["same_section_moment_T_M1_M2_nmm"] == moment
            expected = abs(moment[0])*witness["torsion_rectangle"]["short_side_mm"]/witness["torsion_rectangle"]["J_lower_mm4"]
            if witness["section_scenario"] == "two_ligament_equal_twist_proxy":
                expected /= 2.
            assert witness["nominal_torsion_shear_norm_bound_mpa"] == pytest.approx(expected)
            assert witness["physical_fitting_strength_or_complete_joint_acceptance"] is False


def composition_fixture(tmp_path, monkeypatch, mutation=None):
    """Dispatch seam only: all domain/source reductions explicitly stubbed."""
    payload, field, receipt, digest, _ = admission_fixture(tmp_path, monkeypatch)
    field.update({key: [] for key in ("common_shaft_wood_bearing_actions", "common_shaft_steel_port_actions",
                                      "common_shaft_section_cut_actions", "member_element_actions")})
    payload = json.dumps(field).encode()
    receipt.update(field_sha256=hashlib.sha256(payload).hexdigest(), field_canonical_sha256=helper.references.canonical_sha(field))
    monkeypatch.setattr(helper, "PINS", {})
    monkeypatch.setattr(helper, "verify_pins", lambda _: None)
    monkeypatch.setattr(helper, "PACKET", tmp_path)
    helper_source = tmp_path/"synthetic-reducer.py"
    helper_source.write_text("synthetic dispatch source stub")
    monkeypatch.setattr(helper, "__file__", str(helper_source))
    unit_path = tmp_path/"unit.json"
    unit_path.write_text("{}")
    monkeypatch.setattr(helper.references, "UNIT", unit_path)
    detail = tmp_path/"detail.json"
    detail.write_text(json.dumps({"finished_geometry_queries": {"synthetic_stub": True, "receiver_boundary_geometry": []}}))
    packet = {"source_sha256": {}, "reproducible_detail_artifact": {"path": "detail.json", "sha256": "0"*64}}
    monkeypatch.setattr(helper.references, "read_unit", lambda: (packet, {}, {"installed_axes": [{}]*70}))
    for attribute in ("METHODS", "HEAD"):
        path = tmp_path/(attribute+".json")
        path.write_text(json.dumps({"source_sha256": {}}))
        monkeypatch.setattr(helper.steel.methods, attribute, path)
    property_path = tmp_path/"synthetic-properties.json"
    property_path.write_text(json.dumps({"state_id": None, "candidate": helper.unit.CANDIDATE,
        "release": dict(helper.unit.RELEASE), "source_sha256": {}, "finished_sections": [{}]*5}))
    monkeypatch.setattr(helper, "PROPERTY_PINS", {property_path.name: "0"*64})
    monkeypatch.setattr(helper.references, "read_duration_sources", lambda: {
        "authenticated_primary_sources": [], "source_metadata_path": "synthetic-duration", "source_metadata_sha256": "0"*64})
    monkeypatch.setattr(helper.references, "standard_thread_window", lambda *_: {"synthetic_thread_stub": True})
    monkeypatch.setattr(helper.timber, "read_member_span_geometry", dict)
    monkeypatch.setattr(helper.timber, "verify_member_span_geometry", lambda *_: {"synthetic_span_stub": True})
    calls = []
    def wood_reduction(layout, packet, demand):
        calls.append(("wood", id(demand)))
        return [{}]*82
    monkeypatch.setattr(helper.timber, "aggregate_wood_bearings", wood_reduction)
    monkeypatch.setattr(helper.timber, "bearing_parameter_diagnostics", lambda *_: [{}]*164)
    monkeypatch.setattr(helper.timber, "own_wood_washer_references", lambda *_: [
        {"own_model_capture_over_ideal_annulus_component_ratio": .6, "own_capture_id": "own-capture"}]*68)
    wrench = {"synthetic_simultaneous_six_vector": [1., 2., 3., 4., 5., 6.],
        "tension_average_area_reference": {"CD1_same_state_component_ratio": .2},
        "compression_average_area_reference": {"CD1_same_state_component_ratio": .4}}
    def cuts(demand, full, spans):
        calls.append(("cuts", id(demand)))
        return [{"maximum_tension_average_area_witness": copy.deepcopy(wrench),
                 "maximum_compression_average_area_witness": copy.deepcopy(wrench)} for _ in range(20)]
    monkeypatch.setattr(helper.timber, "replay_existing_member_cuts", cuts)
    monkeypatch.setattr(helper, "face_reference_summaries", lambda *_: [
        {"governing_reference_area_cell_witness": {"reference_area_component_ratio": .8, "id": "face-stub"}}]*6)
    def metal(demand, caller):
        calls.append(("metal", id(demand)))
        if mutation == "field":
            demand["case_id"] = "changed-inside-reduction"
        elif mutation == "receipt":
            receipt["case_id"] = "changed-inside-reduction"
        return {"shaft_same_section_references": [{"axis_id": "own-axis", "section_scenarios": [{
            "section_scenario": {"id": "elastic_model_circle"},
            "sampled_governing_section": {"same_section_nominal_first_yield_index": .7}}]}]*70}
    monkeypatch.setattr(helper.steel, "component_values", metal)
    monkeypatch.setattr(helper, "flange_torsion_reductions", lambda *_: [
        {"sampled_scenario_witnesses": {key: {"simultaneous_nominal_first_yield_bound_index": value}
         for key, value in (("gross_rectangle", .9), ("two_ligament_equal_twist_proxy", 1.1))}}]*72)
    def sheets(demand, layout, samples):
        calls.append(("panels", id(demand)))
        return {"screw_actions_and_generic_references": [{"generic_head_ratio_CD1": .3}]*66,
            "panel_diagnostics": [{"panel": "synthetic", "integrated_net_section_diagnostics": {
                "simultaneous_signed_cut_witnesses": {key: {key: .5} for key in (
                    "mean_net_bending_ratio_CD1", "mean_net_rolling_shear_ratio_CD1", "mean_net_axial_ratio_CD1")}}}]*6}
    monkeypatch.setattr(helper, "panel_reductions", sheets)
    def forbidden_wrapper(*_, **__):
        raise AssertionError("legacy wrappers must not be called")
    for module, name in ((helper.timber, "consume"), (helper.steel, "consume"), (helper.panel, "evaluate")):
        monkeypatch.setattr(module, name, forbidden_wrapper)
    return payload, receipt, digest, calls


def test_top_level_dispatch_retains_same_state_witnesses_and_all_null_capacity(tmp_path, monkeypatch):
    payload, receipt, digest, calls = composition_fixture(tmp_path, monkeypatch)
    result = helper.post_admission_reductions(payload, receipt, admission_sha256=digest, samples=3)
    assert [name for name, _ in calls] == ["wood", "cuts", "metal", "panels"]
    assert len({identity for _, identity in calls}) == 1
    assert result["field_sha256"] == hashlib.sha256(payload).hexdigest()
    assert result["method"]["legacy_consumers_called"] is False
    assert result["complete_joint_resistance"] is None
    assert result["complete_joint_acceptance"] is False
    assert not any(result["release"].values())
    summary = result["governing_conditional_reference_dispositions"]
    assert len(summary) == 11
    assert summary["flange_two_ligament_equal_twist_proxy_torsion_bound_Fy33ksi"]["reference_index_above_one"] is True
    assert summary["timber_average_tension_CD1"]["coherent_witness"]["synthetic_simultaneous_six_vector"] == [1., 2., 3., 4., 5., 6.]
    assert all(row["adopted_complete_resistance_or_joint_pass"] is None for row in summary.values())


@pytest.mark.parametrize("mutation", ["field", "receipt"])
def test_top_level_input_mutation_prevents_issuance(tmp_path, monkeypatch, mutation):
    payload, receipt, digest, _ = composition_fixture(tmp_path, monkeypatch, mutation)
    with pytest.raises(ValueError, match="input changed"):
        helper.post_admission_reductions(payload, receipt, admission_sha256=digest, samples=3)
