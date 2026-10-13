import copy
import json
from pathlib import Path

import numpy as np
import pytest
from scipy.spatial.transform import Rotation
from test_eoere_current_contact_inverse import current_fixture
from test_eoere_current_neighbor_enclosures import source_fixture

from scripts import eoere_current_timber_bedding as timber


@pytest.fixture(scope="module")
def kernels():
    return timber.inverse.runtime_methods()


def potential_fixture(kernels, *, extra=False, samples=None, shape_kind="box"):
    base, _extent, geometry, _guard, _map, smooth, *_ = source_fixture(kernels, kind=shape_kind)
    ndof = 36 if extra else 24
    charts, extents, geometries, boxes = {}, {}, {}, {}
    for i, owner in enumerate(["slave", "master"]+(["extra"] if extra else [])):
        shift = np.array([2000., 0., 0.]) if owner == "extra" else np.zeros(3)
        chart = copy.deepcopy(base)
        chart["reference_start_xyz_mm"] = shift.tolist()
        chart["node_reference_centers_xyz_mm"] = [shift.tolist(), (shift+[100., 0., 0.]).tolist()]
        chart["node_dof_indices"] = (np.arange(12)+12*i).reshape(2, 6).tolist()
        chart["storage_basis_columns_xyz"] = np.eye(3).tolist()
        charts[owner] = chart
        identity = {"finished_raw_file_path": owner+".brep", "finished_raw_file_sha256": "synthetic-"+owner}
        g = smooth.reference.ReferenceSolidDistance(geometry.shape.translate(shift.tolist()), owner_id=owner, source_identity=identity)
        geometries[owner] = g
        bounds = g.shape.BoundingBox()
        box = np.array([[bounds.xmin, bounds.xmax], [bounds.ymin, bounds.ymax], [bounds.zmin, bounds.zmax]])
        extents[owner] = {"schema": "thin_bolted_finite_reference_domain_box/v1", "owner_id": owner,
            "bounds_xyz_mm": (box+[-100., 100.]).tolist(),
            "source_identity": {**identity, "topology_sha256": g.topology_sha256, "genuine_cached_solid_bounds_xyz_mm": box.tolist()}}
        boxes[owner] = timber.neighbors.local_reference_box(owner, chart, extents[owner], g, smooth)
    if samples is None:
        samples = [{"id": "pair/cell-0", "pair_id": "pair", "cell_id": "cell-0", "slave": "slave", "master": "master",
            "slave_feature_id": "synthetic-face", "slave_reference_point_xyz_mm": [31., 5., 0.],
            "master_inverse_seed_xyz_mm": [31., 5., 0.], "reference_area_mm2": 7., "bedding_n_mm3": 2.}]
    potential = timber.TimberBedding(charts, extents, geometries, samples, methods=kernels,
        local_boxes=boxes, source_sha256={}, ndof=ndof)
    q = np.zeros(ndof)
    q[[1, 7]] = -.2
    return potential, q


def test_known_compression_retains_force_magnitude_energy_signed_gradient_and_reciprocal_tangent(kernels):
    potential, q = potential_fixture(kernels)
    result = potential.response(q)
    assert result["energy_nmm"] == pytest.approx(.28, abs=1e-12)
    assert result["branch_counts"] == {"closed": 1}
    row = dict(zip(timber.ROW_COLUMNS, result["sample_rows"][0], strict=True))
    np.testing.assert_allclose(row["force_on_slave_xyz_n"], [0., 2.8, 0.], atol=1e-12, rtol=0.)
    np.testing.assert_allclose(row["reference_master_point_xyz_mm"], [31., 4.8, 0.], atol=1e-12, rtol=0.)
    np.testing.assert_allclose(result["gradient_n"][[1, 7, 13, 19]], [-1.932, -.868, 1.932, .868], atol=1e-12, rtol=0.)
    weights = np.array([.69, .31, -.69, -.31])
    block = result["hessian_csr"].toarray()[np.ix_([1, 7, 13, 19], [1, 7, 13, 19])]
    np.testing.assert_allclose(block, 14.*np.outer(weights, weights), atol=1e-10, rtol=0.)
    np.testing.assert_allclose(result["all_owner_wrench_sum"], np.zeros(6), atol=1e-11, rtol=0.)
    np.testing.assert_allclose(result["owner_wrenches_at_world_origin"]["slave"], [0., 2.8, 0., 0., 0., 86.8], atol=1e-11, rtol=0.)
    assert result["complete_extrema"]["max_force_norm_n"]["sample_index"] == 0
    assert result["physical_pressure_stiffness_or_demand_qualified"] is False


def test_deformed_master_retains_full_unnormalized_inverse_distance_covector(kernels):
    potential, q = potential_fixture(kernels)
    q[[13, 19]] = [0., 10.]
    q[[1, 7]] = 2.9
    result = potential.response(q, tangent=False)
    row = dict(zip(timber.ROW_COLUMNS, result["sample_rows"][0], strict=True))
    assert result["energy_nmm"] == pytest.approx(.28, abs=1e-11)
    np.testing.assert_allclose(row["force_on_slave_xyz_n"], [-.28, 2.8, 0.], atol=1e-11, rtol=0.)
    assert np.linalg.norm(row["force_on_slave_xyz_n"]) > 2.8
    assert result["hessian_csr"] is None
    assert row["root_ball_radius_mm"] < 1e-10
    np.testing.assert_allclose(result["all_owner_wrench_sum"], np.zeros(6), atol=1e-10, rtol=0.)


def test_energy_gradient_and_tangent_have_independent_centered_difference_answers(kernels):
    potential, q = potential_fixture(kernels)
    q[[13, 19]] = [0., 10.]
    q[[1, 7]] = 2.9
    result = potential.response(q)
    hessian = result["hessian_csr"].toarray()
    for index in [1, 7, 13, 19, 5, 17]:
        delta = np.eye(len(q))[index]*1e-3
        plus, minus = potential.response(q+delta, tangent=False), potential.response(q-delta, tangent=False)
        assert (plus["energy_nmm"]-minus["energy_nmm"])/.002 == pytest.approx(result["gradient_n"][index], abs=1e-7)
        np.testing.assert_allclose((plus["gradient_n"]-minus["gradient_n"])/.002, hessian[:, index], atol=1e-7, rtol=0.)


def test_common_rigid_motion_preserves_energy_and_rotates_pair_forces(kernels):
    potential, q = potential_fixture(kernels)
    before = potential.response(q, tangent=False)
    rotation, translation = Rotation.from_rotvec([.02, -.03, .01]).as_matrix(), np.array([1., -2., 3.])
    changed = q.copy()
    for chart in potential.charts.values():
        for center, indices in zip(chart["node_reference_centers_xyz_mm"], chart["node_dof_indices"], strict=True):
            changed[indices[:3]] = rotation@(np.asarray(center)+q[indices[:3]])+translation-center
            changed[indices[3:]] = 1000.*Rotation.from_matrix(rotation@Rotation.from_rotvec(q[indices[3:]]/1000.).as_matrix()).as_rotvec()
    after = potential.response(changed, tangent=False)
    assert after["energy_nmm"] == pytest.approx(before["energy_nmm"], abs=1e-10)
    np.testing.assert_allclose(after["sample_rows"][0][6], rotation@before["sample_rows"][0][6], atol=1e-10, rtol=0.)
    np.testing.assert_allclose(after["all_owner_wrench_sum"], np.zeros(6), atol=1e-10, rtol=0.)
    assert after["final_q_canonical_sha256"] != before["final_q_canonical_sha256"]
    assert all(g.bound_evaluation_count == 2 for g in potential.guards.values())


def test_fixed_heterogeneous_cells_sum_every_area_and_keep_all_open_rows(kernels):
    potential, q = potential_fixture(kernels)
    samples = copy.deepcopy(potential.samples)
    second = {**samples[0], "id": "pair/cell-1", "cell_id": "cell-1", "reference_area_mm2": 3., "bedding_n_mm3": 5.,
        "slave_reference_point_xyz_mm": [41., 5., 0.], "master_inverse_seed_xyz_mm": [41., 5., 0.]}
    third = {**samples[0], "id": "pair/cell-2", "cell_id": "cell-2", "slave_reference_point_xyz_mm": [51., 20., 0.]}
    fourth = {**samples[0], "id": "pair/cell-3", "cell_id": "cell-3",
        "slave_reference_point_xyz_mm": [31., 1., 0.], "master_inverse_seed_xyz_mm": [31., 1., 0.]}
    potential, q = potential_fixture(kernels, samples=[*samples, second, third, fourth], shape_kind="bored")
    result = potential.response(q, tangent=True)
    assert result["energy_nmm"] == pytest.approx(.58, abs=1e-11)
    assert result["branch_counts"] == {"closed": 2, "strict-master-box-open": 1, "open": 1}
    assert [r[0] for r in result["sample_rows"]] == [0, 1, 2, 3]
    assert result["sample_rows"][2][2] == 0. and result["sample_rows"][2][6] == [0., 0., 0.]
    assert result["sample_rows"][3][2] == 0. and result["sample_rows"][3][6] == [0., 0., 0.]
    assert result["sample_rows"][3][3] == pytest.approx(.2, abs=1e-12)
    assert result["complete_extrema"]["max_force_norm_n"]["sample_index"] == 1
    np.testing.assert_allclose(result["owner_wrenches_at_world_origin"]["slave"], [0., 5.8, 0., 0., 0., 209.8], atol=1e-11, rtol=0.)
    np.testing.assert_allclose(result["owner_wrenches_at_world_origin"]["master"], [0., -5.8, 0., 0., 0., -209.8], atol=1e-11, rtol=0.)
    indices = [1, 7, 13, 19]
    np.testing.assert_allclose(result["gradient_n"][indices], [-3.702, -2.098, 3.702, 2.098], atol=1e-11, rtol=0.)
    first_weights, second_weights = np.array([.69, .31, -.69, -.31]), np.array([.59, .41, -.59, -.41])
    hessian = result["hessian_csr"].toarray()
    expected = 14.*np.outer(first_weights, first_weights)+15.*np.outer(second_weights, second_weights)
    np.testing.assert_allclose(hessian[np.ix_(indices, indices)], expected, atol=1e-10, rtol=0.)
    for index in [1, 7, 13, 19, 3, 15]:
        delta = np.eye(len(q))[index]*1e-3
        plus, minus = potential.response(q+delta, tangent=False), potential.response(q-delta, tangent=False)
        assert (plus["energy_nmm"]-minus["energy_nmm"])/.002 == pytest.approx(result["gradient_n"][index], abs=1e-7)
        np.testing.assert_allclose((plus["gradient_n"]-minus["gradient_n"])/.002, hessian[:, index], atol=1e-7, rtol=0.)


def test_genuine_cavity_open_inside_master_box_has_zero_response_and_retained_inverse_distance(kernels):
    potential, q = potential_fixture(kernels, shape_kind="bored")
    q[[1, 7]] = -4.2
    result = potential.response(q, tangent=True)
    assert result["branch_counts"] == {"open": 1}
    assert result["energy_nmm"] == 0. and result["hessian_csr"].nnz == 0
    np.testing.assert_array_equal(result["gradient_n"], np.zeros(24))
    row = dict(zip(timber.ROW_COLUMNS, result["sample_rows"][0], strict=True))
    assert row["rho_reference_mm"] == pytest.approx(.2, abs=1e-12)
    np.testing.assert_allclose(row["current_slave_point_xyz_mm"], [31., .8, 0.], atol=1e-12, rtol=0.)
    np.testing.assert_allclose(row["reference_master_point_xyz_mm"], [31., .8, 0.], atol=1e-12, rtol=0.)
    assert row["inverse_iterations"] >= 1 and row["inverse_residual_inf_mm"] < 1e-11
    assert row["root_ball_radius_mm"] < 1e-10
    np.testing.assert_array_equal(row["force_on_slave_xyz_n"], np.zeros(3))
    np.testing.assert_array_equal(result["all_owner_wrench_sum"], np.zeros(6))
    distance = result["complete_extrema"]["max_force_norm_n"]["complete_owned_distance_record"]
    assert row["owned_distance_record_canonical_sha256"] == timber.canonical_sha(distance)
    assert distance["owner_id"] == "master" and distance["strict_closed_solid_open_classification"] is True
    assert distance["rho_reference_mm"] == pytest.approx(.2, abs=1e-12)


def test_strict_outside_box_is_zero_without_calling_inverse_or_distance(monkeypatch, kernels):
    potential, q = potential_fixture(kernels)
    q[[1, 7]] = 1000.
    def forbidden(*_args, **_kwargs): raise AssertionError("strict exterior point queried inverse/feature")
    monkeypatch.setattr(potential.bedding, "response", forbidden)
    result = potential.response(q)
    assert result["branch_counts"] == {"strict-master-box-open": 1}
    assert result["energy_nmm"] == 0. and result["hessian_csr"].nnz == 0
    np.testing.assert_array_equal(result["gradient_n"], np.zeros(24))


@pytest.mark.parametrize("failure", ["touch", "medial", "station", "inverse", "callback"])
def test_unresolved_branch_stops_complete_response_instead_of_replacing_a_row_by_zero(monkeypatch, kernels, failure):
    potential, q = potential_fixture(kernels)
    if failure == "touch": q[[1, 7]] = 0.
    if failure == "medial": q[[1, 7]] = -5.
    if failure == "station": q[[12, 18]] = 31.
    if failure == "inverse":
        monkeypatch.setattr(potential.bedding.implicit, "inverse", lambda *_args: (np.array([31., 4.7, 0.]), 1, 0.))
    if failure == "callback":
        genuine = potential.callbacks["master"]
        def foreign(point):
            value = genuine(point)
            value["owner_id"] = "foreign"
            return value
        potential.callbacks["master"] = foreign
    with pytest.raises(ValueError, match="timber sample 0"): potential.response(q, tangent=False)


def test_every_trial_rechecks_unregistered_neighbors_and_rejects_new_overlap(kernels):
    potential, q = potential_fixture(kernels, extra=True)
    first = potential.response(q, tangent=False)
    assert len(first["trial_scope"]["all_pair_screens"]) == 3
    assert first["trial_scope"]["remaining_possible_new_neighbor_count"] == 0
    q[[24, 30]] = -2000.
    with pytest.raises(ValueError, match="unregistered timber neighbors"): potential.response(q, tangent=False)
    assert all(g.bound_evaluation_count == 2 for g in potential.guards.values())


@pytest.mark.parametrize("failure", ["sample", "chart", "extent", "local_box", "pins", "state_size", "nonfinite"])
def test_changed_fixed_sources_or_invalid_states_fail_closed(kernels, failure):
    potential, q = potential_fixture(kernels)
    if failure == "sample": potential.samples[0]["reference_area_mm2"] *= 2.
    if failure == "chart": potential.charts["master"]["reference_start_xyz_mm"][0] += 1.
    if failure == "extent": potential.extents["master"]["bounds_xyz_mm"][0][0] -= 1.
    if failure == "local_box": potential.local_boxes["master"]["padded_local_bounds_mm"][0][0] -= 1.
    if failure == "pins": potential.source_sha256["missing-source"] = "missing"
    if failure == "state_size": q = q[:-1]
    if failure == "nonfinite": q[0] = np.nan
    with pytest.raises((ValueError, FileNotFoundError)): potential.response(q, tangent=False)


@pytest.mark.parametrize("when", ["before", "during"])
def test_source_drift_is_checked_before_and_after_force_evaluation(monkeypatch, tmp_path, kernels, when):
    path = tmp_path/"source.py"
    path.write_text("frozen source\n")
    potential, q = potential_fixture(kernels)
    monkeypatch.setattr(timber.current, "ROOT", tmp_path)
    potential.source_sha256 = {path.name: timber.current.sha(path)}
    potential.descriptor_sha = potential._descriptor_sha()
    if when == "before": path.write_text("changed before\n")
    else:
        genuine = potential.callbacks["master"]
        def drift(point):
            result = genuine(point)
            path.write_text("changed during force query\n")
            return result
        potential.callbacks["master"] = drift
    with pytest.raises(ValueError): potential.response(q, tangent=False)


def current_force_fixture(monkeypatch, tmp_path, kernels):
    cases, measure, domains, scope_record, _bridge = current_fixture(monkeypatch, tmp_path, kernels,
        diagonal_neighbor=True, force_ready=True)
    neighbor_path, producer = tmp_path/"neighbor-result.json", tmp_path/"neighbor.py"
    producer.write_text("neighbor producer\n")
    monkeypatch.setattr(timber.neighbors, "OWN", producer)
    monkeypatch.setattr(timber.neighbors, "LOADED_SHA", timber.current.sha(producer))
    neighbors = timber.neighbors.run()
    neighbor_path.write_text(json.dumps(neighbors))
    producer = tmp_path/"timber-bedding.py"
    producer.write_text("timber bedding producer\n")
    monkeypatch.setattr(timber, "OWN", producer)
    monkeypatch.setattr(timber, "LOADED_SHA", timber.current.sha(producer))
    monkeypatch.setattr(timber, "NEIGHBORS", timber.current.ref(neighbor_path))
    monkeypatch.setattr(timber, "NEIGHBOR_PRODUCER", neighbors["producer"])
    monkeypatch.setattr(timber, "INVERSE_PRODUCER", timber.inverse.own_ref())
    for i, (binding, _field, _source) in enumerate(cases):
        binding.update(gradient_inf_n=1e-9*(i+1), current_equilibrium_and_recovery_pass=True,
                       frozen_admission_note="Saved first-order status only")
    return cases, measure, domains, scope_record, neighbors, neighbor_path


def test_full_current_six_case_force_run_retains_all_bindings_and_distinct_known_answers(monkeypatch, tmp_path, kernels):
    cases, measure, domains, scope_record, _neighbors, _path = current_force_fixture(monkeypatch, tmp_path, kernels)
    expected = {p.name: timber.current.sha(p) for p in tmp_path.iterdir() if p.is_file()}
    expected[timber.scope.DOMAIN_SNAPSHOT] = timber.current.sha(tmp_path/timber.scope.DOMAIN_SNAPSHOT)
    result = timber.run()
    assert result["source_sha256"] == expected
    assert len(result["fixed_samples"]) == 114 and len(result["cases"]) == 6
    first_pair = scope_record["registered_plan"]["pairs"][0]
    assert [(r["pair_id"], r["cell_id"]) for r in result["fixed_samples"]] == [
        (p["id"], key) for p in scope_record["registered_plan"]["pairs"] for key in p["complete_selected_face_cell_ids"]]
    faces = {f["feature_id"]: f for f in measure["current_complete_reference_face_measure"]["full_faces"]}
    pairs = {p["id"]: p for p in scope_record["registered_plan"]["pairs"]}
    originals = {r["id"]: r for r in cases[0][1]["reference_interaction_descriptors"]}
    for sample in result["fixed_samples"]:
        pair = pairs[sample["pair_id"]]
        cell = next(c for c in faces[pair["slave_feature_id"]]["cells"] if c["id"] == sample["cell_id"])
        assert sample == {"id": pair["id"]+"/"+cell["id"], "pair_id": pair["id"], "cell_id": cell["id"],
            "slave": pair["slave_owner"], "master": pair["master_owner"], "slave_feature_id": pair["slave_feature_id"],
            "slave_reference_point_xyz_mm": cell["point_xyz_mm"], "master_inverse_seed_xyz_mm": cell["point_xyz_mm"],
            "reference_area_mm2": cell["area_mm2"], "bedding_n_mm3": originals[pair["source_contact_ids"][0]]["bedding_n_mm3"]}
    for i, row in enumerate(result["cases"]):
        binding, field, _ = cases[i]
        assert all(row[k] == binding[k] for k in ["case_id", "state_id", "field"])
        assert row["saved_first_order_source"] == binding
        assert not {"gradient_inf_n", "current_equilibrium_and_recovery_pass", "frozen_admission_note"} & row.keys()
        assert row["final_q_canonical_sha256"] == timber.canonical_sha([*field["response"]["q"], *np.zeros(100)])
        assert row["energy_nmm"] == pytest.approx(float((i+1)**2), abs=1e-10)
        assert row["branch_counts"] == {"closed": 3, "strict-master-box-open": 111}
        assert [r[0] for r in row["sample_rows"]] == list(range(114))
        assert len(row["trial_scope"]["all_pair_screens"]) == 231
        assert row["trial_scope"]["remaining_possible_new_neighbor_count"] == 0
        assert row["trial_scope"]["own_bounds"] == domains["current_diagnostic_ambient_injectivity"]["cases"][i]["bounds"]
        owner = first_pair["slave_owner"]
        np.testing.assert_allclose(row["owner_wrenches_at_world_origin"][owner],
            [0., 20.*(i+1), 0., 0., 0., (50.+i)*20.*(i+1)], atol=1e-10, rtol=0.)
        np.testing.assert_allclose(row["owner_wrenches_at_world_origin"][first_pair["master_owner"]],
            [0., -20.*(i+1), 0., 0., 0., -(50.+i)*20.*(i+1)], atol=1e-10, rtol=0.)
        np.testing.assert_allclose(np.asarray(row["gradient_n"])[[1, 7, 13, 19]],
            np.array([-10., -10., 10.02, 9.98])*(i+1), atol=1e-10, rtol=0.)
        np.testing.assert_allclose(row["all_owner_wrench_sum"], np.zeros(6), atol=1e-9, rtol=0.)
    assert result["all_fixed_registered_cells_retained_including_open_zero_rows"] is True
    assert result["force_and_gradient_evaluated"] is True
    assert result["full_current_tangent_evaluated"] is False
    assert result["finite_frame_equilibrium_or_native_FEA_performed"] is False
    assert result["physical_stiffness_or_demand_or_strength_qualified"] is False
    assert result["structural_acceptance"] is False


def preserved_force_fixture(monkeypatch, tmp_path, kernels):
    """Build a real six-case coupon, then emulate the former serialization."""
    cases, *_ = current_force_fixture(monkeypatch, tmp_path, kernels)
    source = Path(timber.__file__).read_bytes()
    prior_source = source+b"\n# preserved producer version\n"
    timber.OWN.write_bytes(prior_source)
    monkeypatch.setattr(timber, "LOADED_SHA", timber.current.sha(timber.OWN))
    original = timber.run()
    original["schema"] = "eoere_current_reference_material_timber_bedding/v1"
    original.pop("force_law_source_sha256")
    for row, (binding, _field, _source) in zip(original["cases"], cases, strict=True):
        row.pop("saved_first_order_source")
        row.update(binding)
    raw, snapshot = tmp_path/"preserved-force.json", tmp_path/"preserved-producer.py"
    raw.write_text(json.dumps(original))
    snapshot.write_bytes(prior_source)
    monkeypatch.setattr(timber, "PRESERVED_FORCE", timber.current.ref(raw))
    monkeypatch.setattr(timber, "PRESERVED_PRODUCER", timber.current.ref(snapshot))
    timber.OWN.write_bytes(source)
    monkeypatch.setattr(timber, "LOADED_SHA", timber.current.sha(timber.OWN))
    return original, raw, snapshot


def test_guarded_reexport_changes_only_case_status_namespace_and_provenance(monkeypatch, tmp_path, kernels):
    original, raw, snapshot = preserved_force_fixture(monkeypatch, tmp_path, kernels)
    before = raw.read_bytes(), snapshot.read_bytes()
    def forbidden(*_args, **_kwargs): raise AssertionError("metadata correction repeated geometry or force work")
    monkeypatch.setattr(timber, "prepare_current", forbidden)
    monkeypatch.setattr(timber.inverse, "current_geometries", forbidden)
    monkeypatch.setattr(timber.TimberBedding, "response", forbidden)
    result = timber.reexport_preserved()
    assert result["schema"] == "eoere_current_reference_material_timber_bedding/v2"
    assert result["preserved_force_evaluation"]["numerical_evaluation_repeated"] is False
    assert result["preserved_force_evaluation"]["constitutive_ast_unchanged"] is True
    assert result["force_law_source_sha256"] == {**original["source_sha256"],
        result["producer"]["path"]: result["producer"]["sha256"]}
    assert result["source_sha256"] == {**result["force_law_source_sha256"],
        timber.PRESERVED_FORCE["path"]: timber.PRESERVED_FORCE["sha256"],
        timber.PRESERVED_PRODUCER["path"]: timber.PRESERVED_PRODUCER["sha256"]}
    assert result["fixed_samples"] == original["fixed_samples"]
    for old, new in zip(original["cases"], result["cases"], strict=True):
        binding = new["saved_first_order_source"]
        assert all(old[k] == v for k, v in binding.items())
        assert not {"gradient_inf_n", "current_equilibrium_and_recovery_pass"} & new.keys()
        assert new["fixed_sample_descriptor_sha256"] != old["fixed_sample_descriptor_sha256"]
        assert {k: v for k, v in new.items() if k not in [*binding, "saved_first_order_source", "fixed_sample_descriptor_sha256"]} == {
            k: v for k, v in old.items() if k not in [*binding, "fixed_sample_descriptor_sha256"]}
    assert before == (raw.read_bytes(), snapshot.read_bytes())


@pytest.mark.parametrize("failure", ["raw", "snapshot", "source", "law", "producer", "binding", "descriptor", "scope"])
def test_reexport_rejects_drift_or_different_law_before_any_numerical_work(monkeypatch, tmp_path, kernels, failure):
    original, raw, snapshot = preserved_force_fixture(monkeypatch, tmp_path, kernels)
    if failure == "raw": raw.write_text(raw.read_text()+" ")
    if failure == "snapshot": snapshot.write_text(snapshot.read_text()+"# changed\n")
    if failure == "source": (tmp_path/"method-only.py").write_text("changed force source\n")
    if failure == "law":
        timber.OWN.write_text(timber.OWN.read_text().replace('"energy_nmm": energy, "gradient_n": gradient',
            '"energy_nmm": 2.*energy, "gradient_n": gradient'))
        monkeypatch.setattr(timber, "LOADED_SHA", timber.current.sha(timber.OWN))
    if failure == "producer": original["producer"]["sha256"] = "foreign"
    if failure == "binding": original["cases"][4]["state_id"] = "foreign"
    if failure == "descriptor": original["cases"][4]["fixed_sample_descriptor_sha256"] = "foreign"
    if failure == "scope": original["cases"][4]["trial_scope"]["own_bounds"] = []
    if failure in ["producer", "binding", "descriptor", "scope"]:
        raw.write_text(json.dumps(original))
        monkeypatch.setattr(timber, "PRESERVED_FORCE", timber.current.ref(raw))
    def forbidden(*_args, **_kwargs): raise AssertionError("invalid receipt reached numerical work")
    monkeypatch.setattr(timber, "prepare_current", forbidden)
    monkeypatch.setattr(timber.inverse, "current_geometries", forbidden)
    monkeypatch.setattr(timber.TimberBedding, "response", forbidden)
    with pytest.raises(ValueError): timber.reexport_preserved()


@pytest.mark.parametrize("changed", ["raw", "snapshot", "law_source"])
def test_reexport_rejects_source_drift_during_the_last_case(monkeypatch, tmp_path, kernels, changed):
    _original, raw, snapshot = preserved_force_fixture(monkeypatch, tmp_path, kernels)
    targets = {"raw": raw, "snapshot": snapshot, "law_source": tmp_path/"method-only.py"}
    genuine, calls = timber.case_source, []
    def change_late(binding):
        calls.append(binding["case_id"])
        if len(calls) == 6:
            target = targets[changed]
            target.write_bytes(target.read_bytes()+b"\n")
        return genuine(binding)
    monkeypatch.setattr(timber, "case_source", change_late)
    def forbidden(*_args, **_kwargs): raise AssertionError("metadata correction repeated numerical work")
    monkeypatch.setattr(timber, "prepare_current", forbidden)
    monkeypatch.setattr(timber.inverse, "current_geometries", forbidden)
    monkeypatch.setattr(timber.TimberBedding, "response", forbidden)
    with pytest.raises(ValueError): timber.reexport_preserved()
    assert calls == timber.inverse.component.SEQUENCE


def test_factory_routes_heterogeneous_pair_bedding_and_each_complete_measured_cell(monkeypatch, tmp_path, kernels):
    cases, measure, _domains, record, _bridge = current_fixture(monkeypatch, tmp_path, kernels, force_ready=True)
    rows = copy.deepcopy(cases[0][1]["reference_interaction_descriptors"])
    originals = {r["id"]: r for r in rows}
    faces = {f["feature_id"]: f for f in measure["current_complete_reference_face_measure"]["full_faces"]}
    for face in faces.values():
        area = sum(c["area_mm2"] for c in face["cells"])
        for cell, fraction in zip(face["cells"], [.25, .5, .25], strict=True):
            cell["area_mm2"] = area*fraction
    expected = []
    for i, pair in enumerate(record["registered_plan"]["pairs"]):
        bedding = .5+.1*i
        for source_id in pair["source_contact_ids"]:
            source = originals[source_id]
            source.update(bedding_n_mm3=bedding, stiffness=bedding*source["reference_area_mm2"])
        for cell in faces[pair["slave_feature_id"]]["cells"]:
            expected.append({"id": pair["id"]+"/"+cell["id"], "pair_id": pair["id"], "cell_id": cell["id"],
                "slave": pair["slave_owner"], "master": pair["master_owner"], "slave_feature_id": pair["slave_feature_id"],
                "slave_reference_point_xyz_mm": cell["point_xyz_mm"], "master_inverse_seed_xyz_mm": cell["point_xyz_mm"],
                "reference_area_mm2": cell["area_mm2"], "bedding_n_mm3": bedding})
    assert len({r["reference_area_mm2"] for r in expected}) > 1
    assert timber.force_samples(record["registered_plan"], measure, rows) == expected


@pytest.mark.parametrize("failure", ["producer", "neighbor_producer", "inverse_producer", "case", "q", "hardware", "version", "source"])
def test_current_force_factory_rejects_wrong_evidence_or_drift_before_boundary_queries(monkeypatch, tmp_path, kernels, failure):
    _cases, _measure, _domains, _scope_record, record, path = current_force_fixture(monkeypatch, tmp_path, kernels)
    if failure == "producer": monkeypatch.setattr(timber, "LOADED_SHA", "foreign")
    if failure == "neighbor_producer": record["producer"]["sha256"] = "foreign"
    if failure == "inverse_producer": record["current_inverse_producer"]["sha256"] = "foreign"
    if failure == "case": record["cases"][4]["state_id"] = "foreign"
    if failure == "q": record["cases"][4]["full_diagnostic_q_canonical_sha256"] = "foreign"
    if failure == "hardware": record["hardware_revision"] = "foreign"
    if failure == "version": monkeypatch.setattr(timber.neighbors, "version", lambda _name: "foreign")
    if failure == "source": (tmp_path/"method-only.py").write_text("changed source\n")
    path.write_text(json.dumps(record))
    monkeypatch.setattr(timber, "NEIGHBORS", timber.current.ref(path))
    def forbidden(*_args, **_kwargs): raise AssertionError("bad evidence reached source geometry")
    monkeypatch.setattr(timber.inverse, "current_geometries", forbidden)
    with pytest.raises(ValueError): timber.prepare_current()


@pytest.mark.parametrize("failure", ["zero", "nonfinite", "unequal", "stiffness"])
def test_full_cell_force_samples_reject_unstated_or_inconsistent_source_bedding(monkeypatch, tmp_path, kernels, failure):
    cases, measure, _domains, record, _bridge = current_fixture(monkeypatch, tmp_path, kernels, force_ready=True)
    rows = copy.deepcopy(cases[0][1]["reference_interaction_descriptors"])
    if failure == "zero": rows[0]["bedding_n_mm3"] = 0.
    if failure == "nonfinite": rows[0]["bedding_n_mm3"] = np.nan
    if failure == "unequal": rows[0].update({"bedding_n_mm3": 2., "stiffness": 2.*rows[0]["reference_area_mm2"]})
    if failure == "stiffness": rows[0]["stiffness"] *= 2.
    with pytest.raises(ValueError): timber.force_samples(record["registered_plan"], measure, rows)
