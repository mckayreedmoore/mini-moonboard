"""Synthetic poses and stubbed admission; no actual132-body field is admitted.

The fixed existing272-cell proof supplies census/source metadata only. Eight
synthetic straight timber maps test orchestration, not the candidate geometry.
No CAD, stiffness, material response or candidate solve runs in these fixtures.
"""

import copy
import json
from types import SimpleNamespace

import numpy as np
import pytest

from scripts import thin_bolted_timber_contact_kinematics as checks


def straight_map(names=("first", "second"), *, start=None, end=None):
    start = np.array([0., 0., 0.]) if start is None else np.asarray(start)
    end = np.array([100., 0., 0.]) if end is None else np.asarray(end)
    length = np.linalg.norm(end-start); axis = (end-start)/length
    bodies = {name: {"kind": "timber", "node_reference_centers_xyz_mm": [start.tolist(), end.tolist()],
        "node_dof_indices": (12*i+np.arange(12)).reshape(2, 6).tolist(),
        "storage_basis_columns_xyz": np.eye(3).tolist(), "reference_start_xyz_mm": start.tolist(),
        "reference_axis_xyz": axis.tolist(), "reference_stations_mm": [0., float(length)]}
        for i, name in enumerate(names)}
    return {"ndof": 12*len(names), "mechanical_bodies": bodies, "panels": {}}


def set_rigid_state(mapping, q, name, rotation, translation):
    row = mapping["mechanical_bodies"][name]
    centers = np.asarray(row["node_reference_centers_xyz_mm"])
    index = np.asarray(row["node_dof_indices"])
    q[index[:, :3]] = centers@(rotation-np.eye(3)).T+translation
    q[index[:, 3:]] = 1000*checks.finite.mechanical.so3_log(rotation)


def simple_cell(mapping, q, point=None):
    point = [50., 20., 0.] if point is None else point
    patch = {"id": "synthetic-patch", "first": "first", "second": "second", "first_outward_normal_xyz": [0., 0., -1.],
             "normal_from_second_to_first_xyz": [0., 0., 1.]}
    cell = {"id": "synthetic-patch/cell-0", "point_xyz_mm": point, "area_mm2": 120.}
    p1 = checks.finite.current_pose_from_map(mapping, "first", point, q, reference_director=[0., 0., -1.])
    p2 = checks.finite.current_pose_from_map(mapping, "second", point, q, reference_director=[0., 0., 1.])
    action = {"id": cell["id"], "first": "first", "second": "second", "director_owner": "second", "first_port_kind": "point",
        "interaction_enabled": True, "reference_first_point_xyz_mm": point, "reference_second_point_xyz_mm": point,
        "point_on_first_xyz_mm": p1["position_xyz_mm"].tolist(), "point_on_second_xyz_mm": p2["position_xyz_mm"].tolist(),
        "current_director_xyz": p2["current_vector_xyz"].tolist(), "source_descriptor": {"cell_id": cell["id"]}}
    return action, patch, cell


def test_zero_and_common_twenty_degree_rigid_motion_preserve_centres_and_inverse():
    mapping = straight_map(); q = np.zeros(mapping["ndof"])
    rotation = checks.finite.mechanical.so3_exp(np.deg2rad(20)*np.array([2., -1., 3.])/np.sqrt(14))
    for R, translation in [(np.eye(3), np.zeros(3)), (rotation, np.array([13., -7., 21.]))]:
        for name in mapping["mechanical_bodies"]:
            set_rigid_state(mapping, q, name, R, translation)
        before = q.copy(); arguments = simple_cell(mapping, q)
        answer = checks.cell_kinematics(mapping, q, *arguments)
        np.testing.assert_allclose(answer["current_first_centre_xyz_mm"], R@np.array([50., 20., 0.])+translation, atol=2e-13)
        assert abs(answer["gap_opening_positive_mm"]) < 1e-13
        assert answer["tangent_slip_norm_mm"] < 1e-13
        assert answer["opposed_material_normal_angle_rad"] < 3e-8
        inverse = answer["local_inverse_approximation"]
        np.testing.assert_allclose(inverse["reference_pullback_xyz_mm"], [50., 20., 0.], atol=2e-13)
        assert inverse["forward_residual_distance_mm"] < 2e-13
        assert inverse["status"] == "LOCAL_INVERSE_APPROXIMATION" and not inverse["exact_current_footprint_established"]
        np.testing.assert_array_equal(q, before)


def test_known_rigid_relative_slip_opening_and_projection():
    mapping = straight_map(); q = np.zeros(mapping["ndof"])
    set_rigid_state(mapping, q, "first", np.eye(3), [5., -7., 3.])
    answer = checks.cell_kinematics(mapping, q, *simple_cell(mapping, q))
    assert answer["gap_opening_positive_mm"] == pytest.approx(3.)
    np.testing.assert_allclose(answer["tangent_slip_xyz_mm"], [5., -7., 0.], atol=1e-13)
    assert answer["tangent_slip_norm_mm"] == pytest.approx(np.sqrt(74))
    np.testing.assert_allclose(answer["current_projection_on_second_centre_director_plane_xyz_mm"], [55., 13., 0.], atol=1e-13)
    np.testing.assert_allclose(answer["local_inverse_approximation"]["reference_pullback_xyz_mm"], [55., 13., 0.], atol=1e-13)
    assert answer["local_inverse_approximation"]["forward_residual_distance_mm"] < 1e-13


def test_first_own_normal_tilt_is_distinct_from_second_projection_normal():
    mapping = straight_map(); q = np.zeros(mapping["ndof"])
    angle = .12; R = checks.finite.mechanical.so3_exp([angle, 0., 0.])
    point = np.array([50., 20., 0.])
    set_rigid_state(mapping, q, "first", R, point-R@point)
    answer = checks.cell_kinematics(mapping, q, *simple_cell(mapping, q))
    assert answer["opposed_material_normal_angle_rad"] == pytest.approx(angle, abs=3e-15)
    np.testing.assert_allclose(answer["current_first_own_outward_material_normal_xyz"], R@[0., 0., -1.], atol=1e-14)
    np.testing.assert_allclose(answer["current_second_own_outward_material_normal_xyz"], [0., 0., 1.], atol=1e-14)
    assert abs(answer["gap_opening_positive_mm"]) < 1e-13


def test_nonuniform_bending_inverse_uses_new_station_and_reports_known_residual():
    mapping = straight_map(); q = np.zeros(mapping["ndof"])
    set_rigid_state(mapping, q, "first", np.eye(3), [20., 5., 0.])
    index = np.asarray(mapping["mechanical_bodies"]["second"]["node_dof_indices"])
    q[index[:, 5]] = [-200., 200.]; q[index[1, 1]] = 10.
    answer = checks.cell_kinematics(mapping, q, *simple_cell(mapping, q))
    inverse = answer["local_inverse_approximation"]
    np.testing.assert_allclose(inverse["reference_pullback_xyz_mm"], [70., 20., 0.], atol=1e-13)
    expected_forward = np.array([70., 7., 0.])+checks.finite.mechanical.so3_exp([0., 0., .08])@np.array([0., 20., 0.])
    np.testing.assert_allclose(inverse["forward_replayed_current_xyz_mm"], expected_forward, atol=2e-13)
    residual = expected_forward-np.array([70., 25., 0.])
    np.testing.assert_allclose(inverse["forward_minus_projection_xyz_mm"], residual, atol=2e-13)
    assert inverse["forward_residual_distance_mm"] == pytest.approx(np.linalg.norm(residual), abs=2e-13)
    assert inverse["forward_residual_distance_mm"] > 2.
    assert inverse["pullback_station"]["raw_reference_axial_station_mm"] == pytest.approx(70.)


def test_pullback_station_is_flagged_before_frozen_pose_clips_it():
    mapping = straight_map(); q = np.zeros(mapping["ndof"])
    set_rigid_state(mapping, q, "first", np.eye(3), [80., 0., 0.])
    answer = checks.cell_kinematics(mapping, q, *simple_cell(mapping, q))
    domain = answer["local_inverse_approximation"]["pullback_station"]
    assert domain["raw_reference_axial_station_mm"] == pytest.approx(130.)
    assert not domain["inside_mapped_axial_station_domain"] and domain["pose_provider_station_clipping_used"]
    assert domain["raw_segment_fraction"] == pytest.approx(1.3) and domain["pose_provider_segment_fraction"] == 1.
    assert not domain["station_domain_is_trimmed_face_or_solid_occupancy"]


@pytest.mark.parametrize("mutation", ["point", "director", "first_normal", "shape", "reference", "host"])
def test_cell_reference_shape_and_admitted_current_pose_mutations_reject(mutation):
    mapping = straight_map(); q = np.zeros(mapping["ndof"])
    action, patch, cell = simple_cell(mapping, q)
    if mutation == "point":
        action["point_on_second_xyz_mm"][1] += .1
    elif mutation == "director":
        action["current_director_xyz"] = [0., 1., 0.]
    elif mutation == "first_normal":
        patch["first_outward_normal_xyz"] = [0., 1., 0.]
    elif mutation == "shape":
        action["point_on_first_xyz_mm"] = [0., 0.]
    elif mutation == "reference":
        action["reference_first_point_xyz_mm"] = [51., 20., 0.]
    else:
        action["director_owner"] = "first"
    with pytest.raises(ValueError):
        checks.cell_kinematics(mapping, q, action, patch, cell)


def proof_and_synthetic_field():
    proof = json.loads(checks.PROOF.read_bytes())
    hosts = sorted({host for row in proof["pairs"] for host in (row["first"], row["second"])})
    mapping = straight_map(hosts, start=[0., 0., -10000.], end=[0., 0., 10000.])
    identity = {"state_id": "synthetic-census-not-a132-body-proof", "case_id": "synthetic", "accessory_placement": "synthetic"}
    rows = []
    for patch in proof["patches"]:
        for cell in patch["cells"]:
            point = cell["point_xyz_mm"]
            rows.append({"id": cell["id"], "kind": "timber_face_contact", "first": patch["first"], "second": patch["second"],
                "director_owner": patch["second"], "first_port_kind": "point", "interaction_enabled": True,
                "reference_first_point_xyz_mm": point, "reference_second_point_xyz_mm": point,
                "point_on_first_xyz_mm": point, "point_on_second_xyz_mm": point,
                "current_director_xyz": patch["normal_from_second_to_first_xyz"], "axial_scalar_force_n": 0.,
                "source_descriptor": {"cell_id": cell["id"], "patch_id": patch["id"], "cell_area_mm2": cell["area_mm2"],
                    "patch_area_mm2": patch["area_mm2"], "geometry_proof_sha256": checks.PROOF_SHA256}, **identity})
    field = {"schema": checks.FIELD_SCHEMA, "candidate": "compact-floor-flush-thin-bolted-development", "revision": "synthetic",
        **identity, "response": {"q": [0.]*mapping["ndof"], "converged": True}, "usable_conditional_actions": True,
        "finite_kinematic_map": mapping, "finite_interaction_actions": rows,
        "parameters": {"timber_face_contact_geometry_sha256": checks.PROOF_SHA256},
        "source_sha256": {}, "release": {"fabrication_released": False}}
    return proof, field


def test_all272_zero_and_positive_alias_cells_six_pairs_and_areas_are_retained():
    proof, field = proof_and_synthetic_field()
    # This positive alias is only a synthetic census label; no force law or
    # equilibrium is claimed. The geometric reader must never filter by it.
    field["finite_interaction_actions"][-1]["axial_scalar_force_n"] = 123.
    before = checks.canonical_sha({"proof": proof, "field": field})
    report = checks.recover_centres(field, proof)
    assert report["retained_contact_cell_count"] == 272 and report["own_pair_count"] == 6
    assert {row["id"] for row in report["contact_centre_rows"]} == {row["id"] for row in field["finite_interaction_actions"]}
    for pair in report["own_pair_summaries"]:
        source = next(p for p in proof["pairs"] if p["id"] == pair["id"])
        assert pair["retained_reference_cell_area_total_mm2"] == pytest.approx(source["area_mm2"], abs=2e-8)
        assert pair["pullback_outside_mapped_axial_station_domain_count"] == 0
        witness = pair["coherent_kinematic_witnesses"]["largest_tangent_slip"]
        assert (witness["first"], witness["second"]) == (pair["first"], pair["second"])
        assert witness["tangent_slip_norm_mm"] == 0.
    assert checks.canonical_sha({"proof": proof, "field": field}) == before


def test_replayed_numpy_q_mutation_is_rejected_even_when_original_JSON_list_is_unchanged(monkeypatch):
    proof, field = proof_and_synthetic_field()
    original = checks.cell_kinematics
    last = field["finite_interaction_actions"][-1]["id"]

    def mutate(mapping, q, action, patch, cell):
        result = original(mapping, q, action, patch, cell)
        if action["id"] == last:
            q[0] = 17.
        return result

    monkeypatch.setattr(checks, "cell_kinematics", mutate)
    with pytest.raises(ValueError, match="mutated"):
        checks.recover_centres(field, proof)
    assert field["response"]["q"][0] == 0.


@pytest.mark.parametrize("mutation", ["drop_zero", "duplicate", "foreign_id", "area", "state", "q_shape", "map_shape", "station_order", "overlapping_indices"])
def test_zero_census_reference_identity_and_map_shape_mutations_reject(mutation):
    proof, field = proof_and_synthetic_field()
    row = field["finite_interaction_actions"][0]
    host = row["first"]; mapping = field["finite_kinematic_map"]["mechanical_bodies"][host]
    if mutation == "drop_zero":
        assert row["axial_scalar_force_n"] == 0.
        field["finite_interaction_actions"].pop(0)
    elif mutation == "duplicate":
        field["finite_interaction_actions"][-1] = copy.deepcopy(row)
    elif mutation == "foreign_id":
        row["id"] = "unbound-cell"
    elif mutation == "area":
        row["source_descriptor"]["cell_area_mm2"] += 1.
    elif mutation == "state":
        row["state_id"] = "other-state"
    elif mutation == "q_shape":
        field["response"]["q"].pop()
    elif mutation == "map_shape":
        mapping["node_dof_indices"][0].pop()
    elif mutation == "station_order":
        mapping["reference_stations_mm"].reverse()
    else:
        other = next(name for name in field["finite_kinematic_map"]["mechanical_bodies"] if name != host)
        mapping["node_dof_indices"] = copy.deepcopy(field["finite_kinematic_map"]["mechanical_bodies"][other]["node_dof_indices"])
    with pytest.raises(ValueError):
        checks.recover_centres(field, proof)


def stub_admission(tmp_path, monkeypatch, mutation=None):
    _proof, field = proof_and_synthetic_field()
    payload = json.dumps(field).encode(); path = tmp_path/"synthetic-field.json"; path.write_bytes(payload)
    sha = checks.digest(payload); seen = []

    def audit(data):
        assert isinstance(data, bytes) and data == payload
        seen.append(data)
        receipt = {"schema": checks.GATE_SCHEMA, checks.GATE_KEY: True, "field_sha256": sha,
            "field_canonical_sha256": checks.canonical_sha(field), "source_sha256": {checks.GATE_SOURCE: checks.GATE_SHA256},
            **{key: field[key] for key in checks.IDENTITY_KEYS}}
        if mutation:
            mutation(receipt, path)
        return receipt

    gate = SimpleNamespace(__file__=str(checks.ROOT/checks.GATE_SOURCE), LOADED_PRODUCER_SHA256=checks.GATE_SHA256,
                           audit_timber_contact_state=audit)
    monkeypatch.setattr(checks.importlib, "import_module", lambda module: gate if module == checks.GATE_MODULE
                        else (_ for _ in ()).throw(AssertionError("legacy admission fallback attempted")))
    return path, sha, field, seen, gate


def test_reader_calls_fixed_new_gate_once_with_original_bytes_then_reuses_centres(tmp_path, monkeypatch):
    path, sha, field, seen, _ = stub_admission(tmp_path, monkeypatch)
    selected = []

    def recover(saved, proof):
        selected.append(copy.deepcopy(saved["response"]["q"]))
        return {"contact_centre_rows": [], "own_pair_summaries": [], "retained_contact_cell_count": 272, "own_pair_count": 6}

    monkeypatch.setattr(checks, "recover_centres", recover)
    result = checks.consume(path, sha, admission_sha256=checks.GATE_SHA256)
    assert len(seen) == 1 and selected == [field["response"]["q"]]
    assert result["field_sha256"] == sha and result["source_sha256"][checks.GATE_SOURCE] == checks.GATE_SHA256
    assert result["method"]["pullback"] == "LOCAL_INVERSE_APPROXIMATION"
    assert not any(result["release"].values()) and not result["method"]["potential_H_or_response_evaluated"]


@pytest.mark.parametrize("mutation", ["fail", "raw_sha", "canonical_sha", "state", "gate_source", "schema", "changed_path"])
def test_wrong_admission_or_changed_payload_rejects_before_any_contact_replay(tmp_path, monkeypatch, mutation):
    def mutate(receipt, path):
        if mutation == "fail":
            receipt[checks.GATE_KEY] = False
        elif mutation == "raw_sha":
            receipt["field_sha256"] = "0"*64
        elif mutation == "canonical_sha":
            receipt["field_canonical_sha256"] = "0"*64
        elif mutation == "state":
            receipt["state_id"] = "same-case-other-state"
        elif mutation == "gate_source":
            receipt["source_sha256"][checks.GATE_SOURCE] = "0"*64
        elif mutation == "schema":
            receipt["schema"] = "thin_bolted_independent_finite_admission/v1"
        else:
            field = json.loads(path.read_bytes()); field["response"]["q"][0] = 99.
            path.write_text(json.dumps(field))
    path, sha, _, _, _ = stub_admission(tmp_path, monkeypatch, mutate)
    monkeypatch.setattr(checks, "recover_centres", lambda *_: (_ for _ in ()).throw(AssertionError("failed admission reached contact replay")))
    with pytest.raises(ValueError):
        checks.consume(path, sha, admission_sha256=checks.GATE_SHA256)


@pytest.mark.parametrize("mutation", ["missing_raw_sha", "wrong_raw_sha", "wrong_gate_sha", "old_field", "failed_field", "release", "proof_identity", "loaded_gate"])
def test_explicit_raw_gate_schema_release_and_proof_guards(tmp_path, monkeypatch, mutation):
    path, sha, field, _, gate = stub_admission(tmp_path, monkeypatch)
    pin = checks.GATE_SHA256
    if mutation == "missing_raw_sha":
        sha = None
    elif mutation == "wrong_raw_sha":
        sha = "0"*64
    elif mutation == "wrong_gate_sha":
        pin = "0"*64
    elif mutation == "loaded_gate":
        gate.LOADED_PRODUCER_SHA256 = "0"*64
    else:
        if mutation == "old_field":
            field["schema"] = "thin_bolted_frame_response/v1"
        elif mutation == "failed_field":
            field["response"]["converged"] = False
        elif mutation == "release":
            field["release"]["fabrication_released"] = True
        else:
            field["parameters"]["timber_face_contact_geometry_sha256"] = "0"*64
        payload = json.dumps(field).encode(); path.write_bytes(payload); sha = checks.digest(payload)
    with pytest.raises(ValueError):
        checks.consume(path, sha, admission_sha256=pin)
