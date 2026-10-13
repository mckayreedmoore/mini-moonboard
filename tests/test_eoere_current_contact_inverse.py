import copy
import json
from collections import Counter
from types import SimpleNamespace

import numpy as np
import pytest
from test_eoere_current_contact_scope import orchestration_fixture as scope_fixture

from scripts import eoere_current_contact_inverse as inverse


@pytest.fixture(scope="module")
def kernels():
    return inverse.runtime_methods()


def chart_fixture(kernels, *, owner="synthetic-master", offset=0, ndof=12):
    _, method, _, _, _, _ = kernels
    chart = method.toy_row()
    chart["node_dof_indices"] = (np.arange(12)+offset).reshape(2, 6).tolist()
    extent = {"schema": "thin_bolted_finite_reference_domain_box/v1", "owner_id": owner,
        "bounds_xyz_mm": [[-100., 200.], [-100., 100.], [-100., 100.]],
        "source_identity": {"synthetic_known_answer": True}}
    guard = inverse.TrialDomain(owner, chart, extent, ndof, method)
    return chart, guard, np.zeros(ndof)


@pytest.mark.parametrize("x", [-15., 31., 125.])
def test_rigid_known_answer_inverse_and_residual_ball_include_both_endpoint_extensions(kernels, x):
    bedding, method, *_ = kernels
    chart, guard, q = chart_fixture(kernels)
    theta, translation = np.array([.02, -.03, .01]), np.array([1., -2., 3.])
    rotation = method.geometry.so3_exp(theta)
    for center, indices in zip(chart["node_reference_centers_xyz_mm"], chart["node_dof_indices"], strict=True):
        q[indices[:3]] = rotation@center+translation-center
        q[indices[3:]] = 1000.*theta
    timber = bedding.TimberSpatialMap(chart, owner_id=guard.owner, ndof=12, domain_guard=guard.guard)
    known = np.array([x, 2., 3.])
    target = rotation@known+translation
    point, iterations, residual = bedding.implicit.inverse(timber, q, target, known+[.5, -.3, .2])
    observed = timber.jet(q, point, tangent=False)["field"]["value_xyz"]
    certificate = guard.certify_observed_inverse(q, point, target, observed, residual_inf_mm=residual, iterations=iterations)
    np.testing.assert_allclose(point, known, rtol=0., atol=1e-11)
    assert certificate["real_arithmetic_contraction_ball_condition_met"]
    assert certificate["unique_inverse_under_same_exact_map_and_bound_hypotheses"]
    assert not certificate["formal_interval_or_float_roundoff_certificate"]
    assert guard.bound_evaluation_count == 1
    assert certificate["reference_box_margin_mm"] == pytest.approx({-15.: 85., 31.: 97., 125.: 75.}[x])


def test_nonuniform_geodesic_map_inverse_uses_world_chart_and_fresh_interior_motion(kernels):
    bedding, method, *_ = kernels
    rotation = method.geometry.so3_exp([.1, -.2, .05])
    basis = method.geometry.so3_exp([-.07, .12, .04])
    start, stations = np.array([7., -9., 3.]), np.array([0., 17., 53., 100.])
    chart = {"kind": "timber", "reference_start_xyz_mm": start.tolist(), "reference_axis_xyz": rotation[:, 0].tolist(),
        "reference_stations_mm": stations.tolist(), "node_reference_centers_xyz_mm": (start+stations[:, None]*rotation[:, 0]).tolist(),
        "node_dof_indices": np.arange(24).reshape(4, 6).tolist(), "storage_basis_columns_xyz": basis.tolist()}
    extent = {"schema": "thin_bolted_finite_reference_domain_box/v1", "owner_id": "synthetic",
        "bounds_xyz_mm": [[-100., 200.], [-100., 100.], [-100., 100.]], "source_identity": {"synthetic_known_answer": True}}
    guard = inverse.TrialDomain("synthetic", chart, extent, 24, method)
    timber = bedding.TimberSpatialMap(chart, owner_id="synthetic", ndof=24, domain_guard=guard.guard)
    q = np.zeros((4, 6))
    q[:, :3] = np.array([[0., 0., 0.], [0., -1., .4], [.3, .5, -.2], [0., 0., 0.]])@basis
    q[:, 3:] = 1000.*np.array([[0., 0., 0.], [.02, -.01, 0.], [-.01, .01, .02], [0., 0., 0.]])@basis
    q = q.ravel()
    for station in [-12., 8., 31., 71., 115.]:
        known = start+rotation@np.array([station, 2., 3.])
        target = method.geometry.surface_state(chart, q, known, [0., 0., 1.])["position"]
        point, iterations, residual = bedding.implicit.inverse(timber, q, target, known+[.2, -.1, .3])
        observed = timber.jet(q, point, tangent=False)["field"]["value_xyz"]
        result = guard.certify_observed_inverse(q, point, target, observed, residual_inf_mm=residual, iterations=iterations)
        np.testing.assert_allclose(point, known, rtol=0., atol=2e-11)
        assert result["q_canonical_sha256"] == inverse.canonical_sha(q.tolist())
    assert guard.bound_evaluation_count == 1


def test_guard_recomputes_for_in_place_trial_change_and_protects_cached_values(kernels):
    _, guard, q = chart_fixture(kernels)
    original = guard.bound(q)
    original["padded_sufficient_L"] = .9
    assert guard.bound(q)["padded_sufficient_L"] == pytest.approx(1e-10)
    q[7] = -2.
    changed = guard.guard(q, [31., 2., 3.])
    assert changed["padded_sufficient_L"] == pytest.approx(.02+1e-10)
    assert changed["q_canonical_sha256"] == inverse.canonical_sha(q.tolist())
    assert guard.bound_evaluation_count == 2
    q[7] = 0.
    assert np.array_equal(guard.cached_q[7], -2.)
    assert not guard.cached_q.flags.writeable
    guard.guard(q, [31., 2., 3.])
    assert guard.bound_evaluation_count == 3


@pytest.mark.parametrize("failure", ["state_size", "nonfinite", "chart", "extent", "outside", "margin", "folded"])
def test_trial_domain_rejects_unqualified_state_or_domain(kernels, failure):
    _, guard, q = chart_fixture(kernels)
    point = np.array([31., 2., 3.])
    if failure == "state_size": q = q[:-1]
    if failure == "nonfinite": q[0] = np.nan
    if failure == "chart": guard.chart["storage_basis_columns_xyz"][0][0] = 2.
    if failure == "extent": guard.extent["bounds_xyz_mm"][0][0] -= 1.
    if failure == "outside": point[1] = 101.
    if failure == "margin": point[1] = 100.-1e-7
    if failure == "folded": q[6] = -120.
    with pytest.raises(ValueError): guard.guard(q, point)


@pytest.mark.parametrize("key,value", [("owner_id", "foreign"), ("q_canonical_sha256", "foreign"),
    ("row_canonical_sha256", "foreign"), ("extent_canonical_sha256", "foreign"),
    ("sufficient_global_one_to_one_criterion_met", False), ("padded_sufficient_L", 1.)])
def test_trial_domain_rejects_foreign_or_inconclusive_bound(kernels, key, value):
    chart, original, q = chart_fixture(kernels)
    bound = original.bound(q)
    bound[key] = value
    method = SimpleNamespace(sufficient_box_bound=lambda *args, **kwargs: copy.deepcopy(bound))
    guard = inverse.TrialDomain(original.owner, chart, original.extent, 12, method)
    with pytest.raises(ValueError): guard.guard(q, [31., 2., 3.])


def test_residual_ball_uses_euclidean_residual_and_same_trial_lipschitz_bound(kernels):
    _, guard, q = chart_fixture(kernels)
    q[6] = 20.
    observed = np.array([31., 2., 3.])
    target = observed+np.array([3e-12, 4e-12, 0.])
    residual = float(np.max(abs(observed-target)))
    result = guard.certify_observed_inverse(q, observed, target, observed, residual_inf_mm=residual, iterations=2)
    expected = np.linalg.norm(observed-target)/(1.-.2-1e-10)
    assert result["residual_to_root_ball_radius_mm"] == pytest.approx(expected, rel=1e-12, abs=0.)
    assert result["residual_to_root_ball_radius_mm"] > residual/(1.-.2-1e-10)


@pytest.mark.parametrize("failure", ["observed", "target", "reported", "large", "iterations", "ball_escape"])
def test_observed_inverse_rejects_inconsistent_observation_or_escaping_root_ball(kernels, failure):
    _, guard, q = chart_fixture(kernels)
    point = np.array([31., 2., 3.])
    target = observed = point.copy()
    residual, iterations = 0., 2
    if failure == "observed": observed = [31., 2.]
    if failure == "target": target = [31., np.nan, 3.]
    if failure == "reported": target = point+[2e-12, 0., 0.]
    if failure == "large": target = point+[2e-11, 0., 0.]; residual = 2e-11
    if failure == "iterations": iterations = 20
    if failure == "ball_escape":
        point[1] = 100.-1e-6-1e-12
        observed = point.copy(); target = point+[9e-12, 0., 0.]
        residual = float(np.max(abs(observed-target)))
    with pytest.raises(ValueError):
        guard.certify_observed_inverse(q, point, target, observed, residual_inf_mm=residual, iterations=iterations)


def probe_fixture(kernels, *, through_hole=False):
    bedding, method, adapter, smooth, container, _ = kernels
    maps, guards, q = {}, {}, np.zeros(24)
    for owner, offset in [("synthetic-slave", 0), ("synthetic-master", 12)]:
        chart, guard, _ = chart_fixture(kernels, owner=owner, offset=offset, ndof=24)
        guards[owner] = guard
        maps[owner] = bedding.TimberSpatialMap(chart, owner_id=owner, ndof=24, domain_guard=guard.guard)
    cq = smooth.reference.cq
    shape = cq.Solid.makeBox(100., 10., 10., cq.Vector(0., -5., -5.))
    if through_hole:
        shape = shape.cut(cq.Solid.makeCylinder(1., 12., cq.Vector(31., 0., -6.), cq.Vector(0., 0., 1.)))
        shape, _ = container.strict_solid(shape, smooth.reference)
    geometry = smooth.reference.ReferenceSolidDistance(shape, owner_id="synthetic-master", source_identity={"known_answer": True})
    callbacks = {"synthetic-master": adapter.OwnedDistanceCallback(geometry, smooth)}
    boxes = {"synthetic-master": {"bounds_xyz_mm": [[-1e-6, 100.+1e-6], [-5.-1e-6, 5.+1e-6], [-5.-1e-6, 5.+1e-6]]}}
    sample = {"pair_id": "synthetic-pair", "slave": "synthetic-slave", "master": "synthetic-master",
              "cell": {"id": "synthetic-cell", "point_xyz_mm": [31., 5., 0.], "area_mm2": 1.}}
    return maps, guards, q, callbacks, boxes, sample, bedding, adapter, method


@pytest.mark.parametrize("branch,shift,expected", [
    ("outside", 1., "STRICTLY_OUTSIDE_CONTAINING_MASTER_BOX"),
    ("compressed", -.2, "QUALIFIED_ORDINARY_REFERENCE_FEATURE"),
    ("touch", 0., "UNRESOLVED_DISTANCE_FEATURE"),
    ("medial", -5., "UNRESOLVED_DISTANCE_FEATURE"),
    ("void", -5., "STRICT_REFERENCE_OPEN"),
    ("station", -.2, "UNRESOLVED_INVERSE_BRANCH")])
def test_genuine_inverse_and_complete_boundary_probe_keeps_open_touch_medial_void_and_station_distinct(kernels, branch, shift, expected):
    maps, guards, q, callbacks, boxes, sample, bedding, adapter, _ = probe_fixture(kernels, through_hole=branch == "void")
    q[[1, 7]] = shift
    if branch == "station":
        q[[12, 18]] = 31.
        boxes["synthetic-master"]["bounds_xyz_mm"][0] = [31.-1e-6, 131.+1e-6]
    result = inverse.inverse_feature_probe(sample, q, maps, guards, boxes, callbacks, bedding, adapter)
    assert result["disposition"] == expected
    assert result["cell"] == sample["cell"] and result["pair_id"] == sample["pair_id"]
    assert result["current_slave_point_xyz_mm"] == pytest.approx([31., 5.+shift, 0.])
    assert result["force_or_zero_response_supplied"] is False
    if branch == "outside":
        assert result["inverse_or_distance_queried"] is False
        assert guards["synthetic-master"].bound_evaluation_count == 0
    elif branch == "station":
        assert "station kink" in result["reason"] and "inverse_observation" not in result
    else:
        assert result["inverse_observation"]["unique_inverse_under_same_exact_map_and_bound_hypotheses"]
        assert result["master_reference_inverse_xyz_mm"] == pytest.approx([31., 5.+shift, 0.])
        if branch == "compressed":
            assert result["owned_distance_record"]["rho_reference_mm"] == pytest.approx(-.2)
            assert result["owned_distance_record"]["normal_reference_xyz"] == pytest.approx([0., 1., 0.])
        if branch == "void":
            assert result["owned_distance_record"]["rho_reference_mm"] == pytest.approx(1.)
            assert not result["owned_distance_record"]["smooth_feature_qualified"]
        if branch in ["touch", "medial"]:
            flags = result["guarded_native_distance_record"]["branch_flags"]
            assert flags["ON_or_touch_guard"] if branch == "touch" else flags["nonzero_penetration_medial_tie"]


@pytest.mark.parametrize("key,value", [("owner_id", "foreign"), ("reference_point_xyz_mm", [0., 0., 0.]), ("schema", "foreign")])
def test_probe_rejects_foreign_callback_record_instead_of_reporting_a_qualified_feature(kernels, key, value):
    maps, guards, q, callbacks, boxes, sample, bedding, adapter, _ = probe_fixture(kernels)
    q[[1, 7]] = -.2
    genuine = callbacks["synthetic-master"]
    def wrong(point):
        record = genuine(point)
        record[key] = value
        return record
    callbacks["synthetic-master"] = wrong
    with pytest.raises(ValueError): inverse.inverse_feature_probe(sample, q, maps, guards, boxes, callbacks, bedding, adapter)


def test_probe_independently_rechecks_inverse_residual_before_querying_distance(monkeypatch, kernels):
    maps, guards, q, callbacks, boxes, sample, bedding, adapter, _ = probe_fixture(kernels)
    q[[1, 7]] = -.2
    wrong_root = np.array([31., 4.7, 0.])
    target = maps["synthetic-slave"].point_field(q, np.asarray(sample["cell"]["point_xyz_mm"]), tangent=False)["value_xyz"]
    observed = maps["synthetic-master"].jet(q, wrong_root, tangent=False)["field"]["value_xyz"]
    assert np.max(abs(observed-target)) == pytest.approx(.1)
    monkeypatch.setattr(bedding.implicit, "inverse", lambda *args, **kwargs: (wrong_root, 2, 0.))
    distance_calls = []
    genuine_distance = callbacks["synthetic-master"]
    def distance(point):
        distance_calls.append(point.copy())
        return genuine_distance(point)
    callbacks["synthetic-master"] = distance
    result = inverse.inverse_feature_probe(sample, q, maps, guards, boxes, callbacks, bedding, adapter)
    assert result["disposition"] == "UNRESOLVED_INVERSE_BRANCH"
    assert "residual is inconsistent" in result["reason"]
    assert result["force_or_zero_response_supplied"] is False
    assert "inverse_observation" not in result and not distance_calls


def test_probe_certifies_the_master_inverse_under_its_distinct_own_chart_box_and_bound(kernels):
    maps, guards, q, callbacks, boxes, sample, bedding, adapter, method = probe_fixture(kernels)
    master, slave = sample["master"], sample["slave"]
    extent = copy.deepcopy(guards[master].extent)
    extent["bounds_xyz_mm"] = [[-90., 210.], [-80., 90.], [-70., 85.]]
    guards[master] = inverse.TrialDomain(master, maps[master].row, extent, 24, method)
    maps[master] = bedding.TimberSpatialMap(maps[master].row, owner_id=master, ndof=24, domain_guard=guards[master].guard)
    q[[1, 7, 19]] = [-.2, -.4, .1]
    master_bound, slave_bound = guards[master].bound(q), guards[slave].bound(q)
    assert master_bound["padded_sufficient_L"] == pytest.approx(.001+1e-10)
    assert slave_bound["padded_sufficient_L"] == pytest.approx(.002+1e-10)
    result = inverse.inverse_feature_probe(sample, q, maps, guards, boxes, callbacks, bedding, adapter)
    assert result["disposition"] == "QUALIFIED_ORDINARY_REFERENCE_FEATURE"
    np.testing.assert_allclose(result["master_reference_inverse_xyz_mm"], [31., 4.707, 0.], rtol=0., atol=1e-12)
    observation = result["inverse_observation"]
    assert observation["owner_id"] == master
    assert observation["row_canonical_sha256"] == inverse.canonical_sha(maps[master].row)
    assert observation["extent_canonical_sha256"] == inverse.canonical_sha(extent)
    assert observation["q_canonical_sha256"] == inverse.canonical_sha(q.tolist())
    assert observation["trial_bound_canonical_sha256"] == inverse.canonical_sha(master_bound)
    assert observation["padded_sufficient_L"] == master_bound["padded_sufficient_L"]
    assert observation["reference_box_margin_mm"] == pytest.approx(70.)


def current_fixture(monkeypatch, root, kernels, *, diagonal_neighbor=False, piece_neighbor=False, force_ready=False):
    """Small genuine 22-solid recipe with six distinct current-sized vectors."""
    cases, measure, domains, bridge, save = scope_fixture(monkeypatch, root)
    scope, current = inverse.scope, inverse.current
    bedding, method, adapter, smooth, container, _ = kernels
    for name in ["inverse.py", "method-only.py"]: (root/name).write_text("current "+name+"\n")
    monkeypatch.setattr(inverse, "OWN", root/"inverse.py")
    monkeypatch.setattr(inverse, "LOADED_SHA", current.sha(inverse.OWN))
    monkeypatch.setattr(inverse, "SCOPE_PRODUCER", scope.own_ref())
    monkeypatch.setattr(inverse.domains_source, "own_ref", lambda: current.ref(root/"domain.py"))
    saved = domains["current_diagnostic_ambient_injectivity"]
    geometries, face_id_map = {}, {}
    for j, owner_record in enumerate(domains["owners"]):
        owner, path = owner_record["owner_id"], root/owner_record["finished_source"]["path"]
        start = 0. if j == 1 else 1000.*j
        y_offset = 2.2 if diagonal_neighbor and j == 21 else 0.
        if diagonal_neighbor and j == 21: start = 20100.2
        source_rotation = np.eye(3)
        if piece_neighbor and j in [20, 21]:
            source_rotation = method.geometry.so3_exp([0., 0., np.pi/4.])
            start, y_offset = (20000., 0.) if j == 20 else (20000.+110./np.sqrt(2.), 110./np.sqrt(2.))
        chart = saved["charts"][owner]
        chart["reference_start_xyz_mm"] = [start, y_offset, 0.]
        chart["reference_axis_xyz"] = source_rotation[:, 0].tolist()
        chart["node_reference_centers_xyz_mm"] = [[start, y_offset, 0.], (np.array([start, y_offset, 0.])+100.*source_rotation[:, 0]).tolist()]
        solid = smooth.reference.cq.Solid.makeBox(100., 2., 2., smooth.reference.cq.Vector(start, y_offset-1., -1.))
        if piece_neighbor and j in [20, 21]: solid = solid.rotate((start, y_offset, 0.), (start, y_offset, 1.), 45.)
        smooth.reference.cq.Compound.makeCompound([solid]).exportBrep(str(path))
        imported = smooth.reference.cq.Shape.importBrep(str(path))
        solid, wrapper = container.strict_solid(imported, smooth.reference)
        source = current.ref(path)
        identity = {"finished_raw_file_path": source["path"], "finished_raw_file_sha256": source["sha256"]}
        geometry = smooth.reference.ReferenceSolidDistance(solid, owner_id=owner, source_identity=identity)
        geometries[owner] = geometry
        bounds = solid.BoundingBox()
        box = [[bounds.xmin, bounds.xmax], [bounds.ymin, bounds.ymax], [bounds.zmin, bounds.zmax]]
        owner_record.update({"finished_source": {**source, "id": owner, "bytes": path.stat().st_size,
            "volume_mm3": 400., "bounds_xyz_mm": box},
            "strict_container": wrapper, "frozen_constructor_topology": geometry.topology,
            "frozen_constructor_topology_sha256": geometry.topology_sha256})
        extent = saved["extents"][owner]
        extent["schema"] = "thin_bolted_finite_reference_domain_box/v1"
        extent["bounds_xyz_mm"] = (np.asarray(box)+[-100., 100.]).tolist()
        extent["source_identity"].update({**identity, "topology_sha256": geometry.topology_sha256,
                                         "genuine_cached_solid_bounds_xyz_mm": box})
        native_faces = inverse.domains_source.atlas.source_face_records(owner, solid)
        for face in [r for r in measure["registered_complete_own_faces"] if r["owner_id"] == owner]:
            old_feature = face["closed_boundary_feature"]["feature_id"]
            number = face["complete_planar_face"]["face_ordinal_1_based"]
            normal = {1: [0., 1., 0.], 2: [0., 0., 1.], 3: [-1., 0., 0.]}[number]
            normal = source_rotation@normal
            native = next(r for r in native_faces if np.linalg.norm(np.asarray(r["signature"]["oriented_normal_xyz"])-normal) < 1e-8)
            feature = geometry.face_records[native["face_ordinal_1_based"]-1]
            face_id_map[old_feature] = feature["feature_id"]
            face.update({"source_geometry": identity, "topology_sha256": geometry.topology_sha256,
                "closed_boundary_feature": feature, "complete_planar_face": {k: v for k, v in native.items() if k != "_shape"}})
            measured = next(r for r in measure["current_complete_reference_face_measure"]["full_faces"] if r["feature_id"] == old_feature)
            if number == 1: points = [[start+x, y_offset+1., 0.] for x in [25., 50., 75.]]
            elif number == 2: points = [[start+x, y_offset, 1.] for x in [25., 50., 75.]]
            else: points = [[start, y_offset, z] for z in [-.5, 0., .5]]
            origin = np.array([start, y_offset, 0.])
            points = ((np.asarray(points)-origin)@source_rotation.T+origin).tolist()
            area = native["signature"]["area_mm2"]
            measured.update({"feature_id": feature["feature_id"], "source_geometry": identity,
                "topology_sha256": geometry.topology_sha256,
                "complete_source_face_locator": {"face_ordinal_1_based": native["face_ordinal_1_based"], "signature_sha256": native["signature_sha256"]},
                "cells": [{"id": feature["feature_id"]+f"/cell-{i}", "point_xyz_mm": p, "area_mm2": area/3.,
                    "own_inward_material_probe_occupied": True, "reference_centroid_on_full_own_face": True} for i, p in enumerate(points)],
                "full_reference_face_moments": {"area_mm2": area}})
    for row in measure["source_contact_face_bindings"]:
        for side in ["first", "second"]: row[side+"_feature_id"] = face_id_map[row[side+"_feature_id"]]
    for key in ["owners", "registered_complete_own_faces", "source_contact_face_bindings"]:
        if key == "owners": measure[key] = copy.deepcopy(domains[key])
        else: domains[key] = copy.deepcopy(measure[key])
    for data in [measure, domains]:
        data.update({"geometry_revision": "eoere-raised-kicker-screws-v1", "hardware_revision": "eoere-selected-purchase-hardware-v1"})
    original_rows = []
    last = {row["source_patch_id"]: row["source_contact_id"] for row in measure["source_contact_face_bindings"]}
    for binding in measure["source_contact_face_bindings"]:
        first, second = binding["first_owner"], binding["second_owner"]
        is_last = binding["source_contact_id"] == last[binding["source_patch_id"]]
        start = saved["charts"][first]["reference_start_xyz_mm"][0]
        original_rows.append({"id": binding["source_contact_id"], "kind": "timber_face_contact", "first": first, "second": second,
            "point_xyz_mm": [start+(75. if is_last else 25.), 1., 0.], "reference_area_mm2": 100. if is_last else 1.})
        if force_ready:
            original_rows[-1].update({"bedding_n_mm3": 1., "stiffness": original_rows[-1]["reference_area_mm2"]})
    for i, (binding, field, _) in enumerate(cases):
        q = np.asarray(field["response"]["q"])
        q[[12, 18]] += 1000.
        q[[1, 7]] = [-.2, .2, 0., -1., -.05, .05][i]
        if force_ready: q[[1, 7]] = -.1*(i+1)
        if diagonal_neighbor:
            for owner in ["own-20", "own-21"]:
                indices = np.asarray(saved["charts"][owner]["node_dof_indices"])
                q[indices[:, :3]] = 0.
                q[indices[:, 3:]] = [90., 0., 0.]
        if piece_neighbor:
            for owner in ["own-20", "own-21"]:
                indices = np.asarray(saved["charts"][owner]["node_dof_indices"])
                q[indices[:, :3]] = [10., 0., 0.]
                q[indices[:, 3:]] = [0., 0., 100.]
        field["response"] = {"q": q.tolist(), "q_canonical_sha256": inverse.canonical_sha(q.tolist())}
        field["reference_interaction_descriptors"] = copy.deepcopy(original_rows)
        path = root/binding["field"]["path"]
        path.write_text(json.dumps(field))
        binding["field"] = current.ref(path)
        full = np.r_[q, np.zeros(100)]
        saved["cases"][i] = {**binding, "full_diagnostic_q_canonical_sha256": inverse.canonical_sha(full.tolist()),
            "bounds": [method.sufficient_box_bound(chart, full, owner_id=owner, extent=saved["extents"][owner], comparison_padding=1e-10)
                       for owner, chart in saved["charts"].items()]}
    for data in [measure, domains]: data["cases"] = [copy.deepcopy(b) for b, _, _ in cases]
    pins = {p.name: current.sha(p) for p in root.iterdir() if p.is_file() and p.name not in ["domain-only.py", "measure-only.py", "method-only.py", "measure.json", "domains.json"]}
    monkeypatch.setattr(scope.intake_source, "intake", lambda: (cases, copy.deepcopy(pins)))
    save()
    record = scope.run()
    (root/"scope-result.json").write_text(json.dumps(record))
    monkeypatch.setattr(inverse, "CONTACT_SCOPE", current.ref(root/"scope-result.json"))
    method_pins = {"method-only.py": current.sha(root/"method-only.py")}
    monkeypatch.setattr(inverse, "runtime_methods", lambda: (bedding, method, adapter, smooth, container, method_pins))
    return cases, measure, domains, record, bridge


@pytest.mark.parametrize("failure", [None, "intake_before", "intake_after", "measure_before", "measure_after",
    "domain_before", "domain_after", "method_before", "method_after", "case", "q", "order", "bridge", "producer"])
def test_current_run_authenticates_all_sources_and_uses_six_distinct_own_states_with_all38_pair_probes(monkeypatch, tmp_path, kernels, failure):
    cases, _measure, _domains, record, bridge = current_fixture(monkeypatch, tmp_path, kernels)
    current = inverse.current
    expected = {p.name: current.sha(p) for p in tmp_path.iterdir() if p.is_file()}
    expected[inverse.scope.DOMAIN_SNAPSHOT] = current.sha(tmp_path/inverse.scope.DOMAIN_SNAPSHOT)
    targets = {"intake": "intake-only.py", "measure": "measure-only.py", "domain": "domain-only.py", "method": "method-only.py"}
    if failure and failure.endswith("_before"):
        (tmp_path/targets[failure.split("_")[0]]).write_text("source changed before queries\n")
    if failure == "case": cases[4][0]["state_id"] = "foreign"
    if failure == "q": cases[4][1]["response"]["q"][0] += 1.
    if failure == "order": cases.reverse()
    if failure == "bridge": bridge.LOADED_SHA = "foreign"
    if failure == "producer": monkeypatch.setattr(inverse, "LOADED_SHA", "foreign")
    geometry_calls, probes, verifies = [], [], []
    original_geometry, original_probe, original_verify = inverse.current_geometries, inverse.inverse_feature_probe, current.verify
    def geometry(*args, **kwargs):
        geometry_calls.append(True)
        return original_geometry(*args, **kwargs)
    def probe(sample, q, *args, **kwargs):
        probes.append((sample["pair_id"], q.copy()))
        result = original_probe(sample, q, *args, **kwargs)
        if failure and failure.endswith("_after") and len(probes) == 228:
            (tmp_path/targets[failure.split("_")[0]]).write_text("source changed during final probe\n")
        return result
    def verify(pins):
        verifies.append(copy.deepcopy(pins))
        original_verify(pins)
    monkeypatch.setattr(inverse, "current_geometries", geometry)
    monkeypatch.setattr(inverse, "inverse_feature_probe", probe)
    monkeypatch.setattr(current, "verify", verify)
    if failure:
        with pytest.raises(ValueError): inverse.run()
        if failure.endswith("_before") or failure in ["case", "q", "order", "bridge", "producer"]:
            assert not geometry_calls and not probes
        if failure.endswith("_after"): assert len(probes) == 228
        return
    result = inverse.run()
    assert len(geometry_calls) == 1 and len(probes) == result["probe_count"] == 228
    assert result["fresh_current_bound_count"] == 132 and result["registered_pair_count"] == 38
    assert result["source_sha256"] == expected == verifies[-1] == verifies[-2]
    assert all(set(pins) <= set(expected) for pins in verifies)
    assert set(result["source_sha256"]) >= set(record["source_sha256"])
    pairs = {r["id"]: r for r in record["registered_plan"]["pairs"]}
    shifts = [-.2, .2, 0., -1., -.05, .05]
    expected_inside = ["QUALIFIED_ORDINARY_REFERENCE_FEATURE", "STRICTLY_OUTSIDE_CONTAINING_MASTER_BOX",
        "UNRESOLVED_DISTANCE_FEATURE", "UNRESOLVED_DISTANCE_FEATURE", "QUALIFIED_ORDINARY_REFERENCE_FEATURE", "STRICTLY_OUTSIDE_CONTAINING_MASTER_BOX"]
    special = next(r["id"] for r in pairs.values() if r["slave_owner"] == "own-00" and r["master_owner"] == "own-01")
    for i, row in enumerate(result["cases"]):
        assert row["case_id"] == inverse.component.SEQUENCE[i] and row["state_id"] == f"state-{i}"
        assert len(row["probes"]) == 38 and {r["pair_id"] for r in row["probes"]} == pairs.keys()
        for j, value in enumerate(row["probes"]):
            pair = pairs[value["pair_id"]]
            assert value["slave"] == pair["slave_owner"] and value["master"] == pair["master_owner"]
            assert value["cell"]["id"].endswith("/cell-2")
            assert value["cell"]["id"] in pair["complete_selected_face_cell_ids"]
            assert value["cell"]["area_mm2"] == pytest.approx(200./3.)
            assert value["original_patch_area_weighted_centroid_xyz_mm"][0] % 1000. > 70.
            q = np.r_[cases[i][1]["response"]["q"], np.zeros(100)]
            np.testing.assert_array_equal(probes[38*i+j][1], q)
            if value["pair_id"] == special:
                assert value["disposition"] == expected_inside[i]
                assert value["current_slave_point_xyz_mm"] == pytest.approx([75.+i, 1.+shifts[i], 0.])
                if "inverse_observation" in value:
                    assert value["master_reference_inverse_xyz_mm"] == pytest.approx([74.9, 1.+shifts[i], 0.])
                    assert value["inverse_observation"]["q_canonical_sha256"] == row["full_diagnostic_q_canonical_sha256"]
            else: assert value["disposition"] == "STRICTLY_OUTSIDE_CONTAINING_MASTER_BOX"
        assert sum(row["disposition_counts"].values()) == 38
    assert not result["all_full_face_cells_or_new_neighbors_or_station_touch_branches_qualified"]
    assert not result["contact_force_or_frame_equilibrium_or_native_FEA_performed"]
    assert not result["structural_acceptance"]


@pytest.mark.parametrize("late_drift", [False, True])
def test_all_cell_run_retains_every_pair_cell_and_own_state_with_compact_native_observations(monkeypatch, tmp_path, kernels, late_drift):
    cases, measure, domains, record, _bridge = current_fixture(monkeypatch, tmp_path, kernels)
    expected_bindings = [[p["id"], cell] for p in record["registered_plan"]["pairs"] for cell in p["complete_selected_face_cell_ids"]]
    assert len(expected_bindings) == 114 and len({tuple(row) for row in expected_bindings}) == 114
    expected_pins = {p.name: inverse.current.sha(p) for p in tmp_path.iterdir() if p.is_file()}
    expected_pins[inverse.scope.DOMAIN_SNAPSHOT] = inverse.current.sha(tmp_path/inverse.scope.DOMAIN_SNAPSHOT)
    original = inverse.inverse_feature_probe
    full, verifies = [], []
    genuine_verify = inverse.current.verify
    def probe(sample, q, *args, **kwargs):
        if not full:
            def unresolved(*_args, **_kwargs):
                raise ValueError("controlled inverse branch failure at first full-face cell")
            with monkeypatch.context() as patch:
                patch.setattr(kernels[0].implicit, "inverse", unresolved)
                result = original(sample, q, *args, **kwargs)
        else:
            result = original(sample, q, *args, **kwargs)
        full.append((copy.deepcopy(sample), q.copy(), result))
        if late_drift and len(full) == 684: (tmp_path/"method-only.py").write_text("changed during last full-cell probe\n")
        return result
    def verify(pins):
        verifies.append(copy.deepcopy(pins))
        genuine_verify(pins)
    monkeypatch.setattr(inverse, "inverse_feature_probe", probe)
    monkeypatch.setattr(inverse.current, "verify", verify)
    if late_drift:
        with pytest.raises(ValueError): inverse.run(all_cells=True)
        assert len(full) == 684
        return
    result = inverse.run(all_cells=True)
    assert full[0][2]["disposition"] == "UNRESOLVED_INVERSE_BRANCH"
    assert result["cases"][0]["complete_unresolved_probes"][0] == {
        "sample_index": 0, "complete_probe": full[0][2]}
    assert full[0][2]["reason"] == "controlled inverse branch failure at first full-face cell"
    assert result["source_sha256"] == expected_pins == verifies[-1] == verifies[-2]
    assert result["sample_binding_columns"] == ["pair_id", "cell_id"] and result["sample_bindings"] == expected_bindings
    assert result["probe_count"] == len(full) == 684 and result["fresh_current_bound_count"] == 132
    assert result["all_registered_pair_cells_probed_at_saved_poses"] is True
    assert result["compact_rows_are_contact_force_inputs"] is False
    assert result["complete_unresolved_records_retained"] is True
    expected_columns = ["sample_index", "disposition", "current_slave_point_xyz_mm", "point_to_master_box_axis_separation_mm",
        "master_reference_inverse_xyz_mm", "master_branch", "inverse_iterations", "inverse_residual_inf_mm",
        "residual_to_root_ball_radius_mm", "reference_box_margin_mm", "rho_reference_mm", "solid_classification",
        "boundary_unsigned_distance_mm", "closest_own_features", "active_native_branch_flags",
        "native_record_canonical_sha256", "complete_probe_canonical_sha256"]
    assert result["probe_columns"] == expected_columns
    assert result["closest_own_feature_columns"] == ["feature_id", "closest_support_feature_id", "support_type", "trim_classification", "closest_point_xyz_mm", "distance_mm"]
    charts = domains["current_diagnostic_ambient_injectivity"]["charts"]
    extents = domains["current_diagnostic_ambient_injectivity"]["extents"]
    pair_owners = {p["id"]: (p["slave_owner"], p["master_owner"]) for p in record["registered_plan"]["pairs"]}
    measured_cells = {f["feature_id"]: {c["id"]: copy.deepcopy(c) for c in f["cells"]}
        for f in measure["current_complete_reference_face_measure"]["full_faces"]}
    for case_index, case in enumerate(result["cases"]):
        assert case["case_id"] == inverse.component.SEQUENCE[case_index] and case["state_id"] == f"state-{case_index}"
        raw_rows = full[case_index*114:(case_index+1)*114]
        q = np.r_[cases[case_index][1]["response"]["q"], np.zeros(100)]
        assert case["probe_count"] == len(case["probe_rows"]) == 114
        assert case["disposition_counts"] == dict(Counter(p["disposition"] for _, _, p in raw_rows))
        unresolved = []
        for i, (packed, (sample, observed_q, raw)) in enumerate(zip(case["probe_rows"], raw_rows, strict=True)):
            assert len(packed) == len(expected_columns)
            row = dict(zip(expected_columns, packed, strict=True))
            assert expected_bindings[i] == [sample["pair_id"], sample["cell"]["id"]]
            assert (sample["slave"], sample["master"]) == pair_owners[sample["pair_id"]]
            expected_cell = measured_cells[sample["slave_feature_id"]][sample["cell"]["id"]]
            assert sample["cell"] == expected_cell
            if (sample["slave"], sample["master"]) == ("own-00", "own-01"):
                x = expected_cell["point_xyz_mm"][0]
                shift = [-.2, .2, 0., -1., -.05, .05][case_index]
                assert raw["current_slave_point_xyz_mm"] == pytest.approx([x+case_index, 1.+shift, 0.])
            np.testing.assert_array_equal(observed_q, q)
            assert row["sample_index"] == i and row["disposition"] == raw["disposition"]
            assert row["current_slave_point_xyz_mm"] == raw["current_slave_point_xyz_mm"]
            assert row["point_to_master_box_axis_separation_mm"] == raw.get("point_to_master_box_axis_separation_mm")
            assert row["master_reference_inverse_xyz_mm"] == raw.get("master_reference_inverse_xyz_mm")
            assert row["master_branch"] == raw.get("master_branch")
            assert row["complete_probe_canonical_sha256"] == inverse.canonical_sha(raw)
            observation = raw.get("inverse_observation", {})
            for key in ["inverse_iterations", "inverse_residual_inf_mm", "residual_to_root_ball_radius_mm", "reference_box_margin_mm"]:
                assert row[key] == observation.get(key)
            if observation:
                master = sample["master"]
                assert observation["owner_id"] == master
                assert observation["row_canonical_sha256"] == inverse.canonical_sha(charts[master])
                assert observation["extent_canonical_sha256"] == inverse.canonical_sha(extents[master])
                assert observation["q_canonical_sha256"] == inverse.canonical_sha(q.tolist())
            distance = raw.get("owned_distance_record", {})
            native = distance.get("guarded_native_distance_record", raw.get("guarded_native_distance_record"))
            if native is None:
                assert row["native_record_canonical_sha256"] is None and row["rho_reference_mm"] is None
                assert row["solid_classification"] is None and row["boundary_unsigned_distance_mm"] is None
                assert row["closest_own_features"] == row["active_native_branch_flags"] == []
            else:
                assert row["native_record_canonical_sha256"] == inverse.canonical_sha(native)
                assert row["rho_reference_mm"] == distance.get("rho_reference_mm", native["reference_signed_distance_rho_mm"])
                assert row["solid_classification"] == native["solid_classification"]
                assert row["boundary_unsigned_distance_mm"] == native["boundary_unsigned_distance_mm"]
                assert row["active_native_branch_flags"] == sorted(k for k, v in native["branch_flags"].items() if v)
                assert row["closest_own_features"] == [[f["feature_id"], f["closest_support_feature_id"], f["support_type"],
                    f.get("trim_classification"), f["closest_point_xyz_mm"], f["distance_mm"]] for f in native["complete_near_minimum_own_features"]]
            if raw["disposition"].startswith("UNRESOLVED_"):
                unresolved.append({"sample_index": i, "complete_probe": raw})
        assert case["complete_unresolved_probes"] == unresolved
        observed = [(i, p) for i, (_, _, p) in enumerate(raw_rows) if "inverse_observation" in p]
        if observed:
            extrema = case["complete_extrema"]
            assert extrema["max_inverse_residual_inf_mm"]["comparison_score"] == max(p["inverse_observation"]["inverse_residual_inf_mm"] for _, p in observed)
            assert extrema["max_residual_to_root_ball_radius_mm"]["comparison_score"] == max(p["inverse_observation"]["residual_to_root_ball_radius_mm"] for _, p in observed)
            assert extrema["min_reference_box_margin_mm"]["comparison_score"] == -min(p["inverse_observation"]["reference_box_margin_mm"] for _, p in observed)
            for value in extrema.values(): assert value["complete_probe"] == raw_rows[value["sample_index"]][2]
        compressed = [p["owned_distance_record"]["rho_reference_mm"] for _, _, p in raw_rows if p["disposition"] == "QUALIFIED_ORDINARY_REFERENCE_FEATURE"]
        if compressed:
            assert case["complete_extrema"]["max_compressed_reference_distance_magnitude_mm"]["comparison_score"] == -min(compressed)
    assert not result["all_full_face_cells_or_new_neighbors_or_station_touch_branches_qualified"]
    assert not result["contact_force_or_frame_equilibrium_or_native_FEA_performed"] and not result["structural_acceptance"]


@pytest.mark.parametrize("order", [[10, 20, 30, 40, 50, 60, 70], [70, 60, 50, 40, 30, 20, 10], [30, 50, 10, 70, 20, 60, 40]])
def test_extrema_keep_independent_heterogeneous_worst_values_and_first_tied_full_witness(order):
    values = {10: (2e-12, 3e-12, 40., -.5), 20: (5e-12, 4e-12, 80., -.1),
        30: (3e-12, 7e-12, 60., -1.2), 40: (4e-12, 2e-12, 15., -.3),
        50: (5e-12, 4e-12, 80., -.1), 60: (8e-12, 8e-12, 90., 1.5)}
    probes = {i: {"disposition": "STRICT_REFERENCE_OPEN" if i == 60 else "QUALIFIED_ORDINARY_REFERENCE_FEATURE",
        "inverse_observation": dict(zip(["inverse_residual_inf_mm", "residual_to_root_ball_radius_mm", "reference_box_margin_mm"], row[:3], strict=True)),
        "owned_distance_record": {"rho_reference_mm": row[3]}, "witness": [i]} for i, row in values.items()}
    probes[70] = {"disposition": "STRICTLY_OUTSIDE_CONTAINING_MASTER_BOX", "witness": [70]}
    extrema, seen = {}, []
    for i in order:
        inverse.record_extrema(extrema, i, probes[i])
        seen.append(i)
        inverse_indices = [j for j in seen if j in values]
        compressed_indices = [j for j in inverse_indices if j != 60]
        expected = {}
        if inverse_indices:
            for name, column, choose in [("max_inverse_residual_inf_mm", 0, max),
                ("max_residual_to_root_ball_radius_mm", 1, max), ("min_reference_box_margin_mm", 2, min)]:
                witness = choose(inverse_indices, key=lambda j: values[j][column])
                expected[name] = (witness, (-1. if column == 2 else 1.)*values[witness][column])
        if compressed_indices:
            witness = min(compressed_indices, key=lambda j: values[j][3])
            expected["max_compressed_reference_distance_magnitude_mm"] = (witness, -values[witness][3])
        assert extrema.keys() == expected.keys()
        for name, (witness, score) in expected.items():
            assert extrema[name] == {"comparison_score": score, "sample_index": witness, "complete_probe": probes[witness]}
    snapshots = copy.deepcopy(extrema)
    for probe in probes.values(): probe["witness"].append("caller mutation")
    assert extrema == snapshots


@pytest.mark.parametrize("failure", ["duplicate_cell", "duplicate_pair", "missing_cell", "unoccupied", "zero_area", "nonfinite", "foreign_owner"])
def test_registered_full_cell_selection_rejects_incomplete_duplicate_or_invalid_measure(monkeypatch, tmp_path, kernels, failure):
    cases, measure, _domains, record, _bridge = current_fixture(monkeypatch, tmp_path, kernels)
    plan = copy.deepcopy(record["registered_plan"])
    face = next(f for f in measure["current_complete_reference_face_measure"]["full_faces"] if f["feature_id"] == plan["pairs"][0]["slave_feature_id"])
    if failure == "duplicate_cell":
        face["cells"].append(copy.deepcopy(face["cells"][0]))
        for pair in plan["pairs"]:
            if pair["slave_feature_id"] == face["feature_id"]: pair["complete_selected_face_cell_ids"] = [c["id"] for c in face["cells"]]
        plan["pair_cell_count"] = sum(len(p["complete_selected_face_cell_ids"]) for p in plan["pairs"])
    if failure == "duplicate_pair": plan["pairs"].append(copy.deepcopy(plan["pairs"][0]))
    if failure == "missing_cell": face["cells"].pop()
    if failure == "unoccupied": face["cells"][0]["own_inward_material_probe_occupied"] = False
    if failure == "zero_area": face["cells"][0]["area_mm2"] = 0.
    if failure == "nonfinite": face["cells"][0]["point_xyz_mm"][0] = np.nan
    if failure == "foreign_owner": face["owner_id"] = "foreign"
    with pytest.raises(ValueError):
        inverse.registered_cells(plan, measure, cases[0][1]["reference_interaction_descriptors"], all_cells=True)
