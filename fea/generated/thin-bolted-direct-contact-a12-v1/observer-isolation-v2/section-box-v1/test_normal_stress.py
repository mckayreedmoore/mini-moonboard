"""Independent asymmetric hand answer and admission-before-vector seams."""

import copy
import hashlib
import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

PATH = Path(__file__).with_name("normal_stress.py")
SPEC = importlib.util.spec_from_file_location("five_section_box_coupon", PATH)
helper = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(helper)


def fixture():
    properties = {"basis_u_v_grain_xyz": [[1., 0., 0.], [0., 1., 0.], [0., 0., 1.]],
        "finished_area_mm2": 2., "centroidal_area_moment_matrix_uv_mm4": [[7., 2.], [2., 5.]],
        "centroid_xyz_mm": [2., 3., 0.], "centroid_uv_mm": [2., 3.],
        "station_global_grain_projection_mm": 0., "section_origin_xyz_mm": [0., 0., 0.],
        "bounds_uv_mm": {"u": [1., 4.], "v": [2., 5.]}}
    wrench = {"cut_point_xyz_mm": [0., 0., 0.], "force_on_lower_portion_xyz_n": [1., 2., 10.],
        "moment_on_lower_portion_about_cut_xyz_nmm": [16., -33., 18.]}
    return properties, wrench


def test_unsymmetric_net_inertia_eccentric_centroid_and_signed_box_hand_answer():
    prop, wrench = fixture()
    before = copy.deepcopy((prop, wrench))
    out = helper.section_box_bound(prop, wrench)
    assert out["moment_about_reference_finished_centroid_xyz_nmm"] == pytest.approx([-14., -13., 17.])
    assert out["mean_axial_normal_stress_mpa"] == 5.
    assert out["normal_stress_gradient_uv_n_mm3"] == pytest.approx([3., -4.])
    assert out["minimum_signed_normal_stress_box_witness"]["box_corner_uv_mm"] == [1., 5.]
    assert out["minimum_signed_normal_stress_box_witness"]["signed_linear_normal_stress_mpa"] == pytest.approx(-6.)
    assert out["maximum_signed_normal_stress_box_witness"]["box_corner_uv_mm"] == [4., 2.]
    assert out["maximum_signed_normal_stress_box_witness"]["signed_linear_normal_stress_mpa"] == pytest.approx(15.)
    assert out["actual_trimmed_directional_stress_extrema"] is None
    assert out["NDS_component_ratio_or_complete_member_resistance"] is None
    assert out["finite_current_pose_or_occupied_corner_claimed"] is False
    assert (prop, wrench) == before


def test_centroidal_axial_force_has_no_invented_bending():
    prop, wrench = fixture()
    wrench["moment_on_lower_portion_about_cut_xyz_nmm"] = [30., -20., 1.]
    out = helper.section_box_bound(prop, wrench)
    assert out["normal_stress_gradient_uv_n_mm3"] == pytest.approx([0., 0.])
    assert out["minimum_signed_normal_stress_box_witness"]["signed_linear_normal_stress_mpa"] == 5.
    assert out["maximum_signed_normal_stress_box_witness"]["signed_linear_normal_stress_mpa"] == 5.


@pytest.mark.parametrize("change", ["station", "centroid_plane", "basis", "inertia", "area", "box"])
def test_wrong_plane_geometry_or_box_rejected(change):
    prop, wrench = fixture()
    if change == "station": wrench["cut_point_xyz_mm"][2] = 1.
    elif change == "centroid_plane": prop["centroid_xyz_mm"][2] = 1.
    elif change == "basis": prop["basis_u_v_grain_xyz"][0][0] = 2.
    elif change == "inertia": prop["centroidal_area_moment_matrix_uv_mm4"] = [[1., 2.], [2., 1.]]
    elif change == "area": prop["finished_area_mm2"] = 0.
    else: prop["bounds_uv_mm"]["u"] = [3., 4.]
    with pytest.raises(ValueError): helper.section_box_bound(prop, wrench)


def test_only_five_frozen_geometry_inputs_read_without_force_or_CAD():
    rows, pins = helper.read_properties()
    assert len(rows) == 5 and {(x["member"], x["station_global_grain_projection_mm"]) for x in rows} == helper.KEYS
    assert all(x["state_id"] is None and x["linear_normal_stress"] is None for x in rows)
    assert pins and all(hashlib.sha256((helper.ROOT / path).read_bytes()).hexdigest() == digest for path, digest in pins.items())


@pytest.mark.parametrize("wrong", ["raw", "gate"])
def test_wrong_raw_hash_or_gate_stops_before_admission(tmp_path, monkeypatch, wrong):
    path = tmp_path / "unadmitted.json"
    path.write_bytes(b"{}")
    monkeypatch.setattr(helper, "load_source", lambda *a: pytest.fail("gate loaded before raw pin"))
    with pytest.raises(ValueError, match="released bytes"):
        helper.consume(path, {}, expected_field_sha256="0" * 64 if wrong == "raw" else hashlib.sha256(b"{}").hexdigest(),
                       admission_sha256=helper.GATE_SHA if wrong == "raw" else "0" * 64)


def test_failed_admission_stops_before_aliases_geometry_or_vectors(tmp_path, monkeypatch):
    payload = b"{}"
    path = tmp_path / "unadmitted.json"
    path.write_bytes(payload)
    receipt = {"explicit_rejected_stub_not_body_admission": True}
    seen = []

    def reject(same_bytes, same_receipt, *, admission_sha256):
        assert same_bytes == payload and same_receipt is receipt and admission_sha256 == helper.GATE_SHA
        seen.append(True)
        raise ValueError("explicit admission rejection")

    monkeypatch.setattr(helper, "load_source", lambda *a: SimpleNamespace(require_admitted_payload=reject))
    monkeypatch.setattr(helper.member, "verify_alias_state_labels", lambda *a: pytest.fail("unadmitted vectors accessed"))
    with pytest.raises(ValueError, match="admission rejection"):
        helper.consume(path, receipt, expected_field_sha256=hashlib.sha256(payload).hexdigest(), admission_sha256=helper.GATE_SHA)
    assert seen == [True] and path.read_bytes() == payload
    assert json.dumps(receipt) == '{"explicit_rejected_stub_not_body_admission": true}'


def test_real_new_validator_rejects_old_receipt_before_vector_recovery(tmp_path, monkeypatch):
    payload = b"{}"
    path = tmp_path / "unadmitted.json"
    path.write_bytes(payload)
    receipt = {"schema": "thin_bolted_independent_complete_timber_admission/v1"}
    monkeypatch.setattr(helper.member, "verify_alias_state_labels", lambda *a: pytest.fail("unadmitted vectors accessed"))
    with pytest.raises(ValueError, match="actual complete-field admission"):
        helper.consume(path, receipt, expected_field_sha256=hashlib.sha256(payload).hexdigest(), admission_sha256=helper.GATE_SHA)
    assert path.read_bytes() == payload and receipt == {"schema": "thin_bolted_independent_complete_timber_admission/v1"}
