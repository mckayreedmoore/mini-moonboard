import copy
import json
from itertools import product
from types import SimpleNamespace

import numpy as np
import pytest

from scripts import eoere_current_contact_scope as scope
from scripts import eoere_current_timber_domains as domains


def contact_fixture():
    faces, measures = [], []
    for i, owner in enumerate(["own-a", "own-b", "own-c"]):
        area = 30.*(i+1)
        feature = owner+"/face"
        source = {"finished_raw_file_path": owner+".brep", "finished_raw_file_sha256": owner+"-sha"}
        face = {"owner_id": owner, "source_geometry": source, "topology_sha256": owner+"-topology",
                "closed_boundary_feature": {"feature_id": feature},
                "complete_planar_face": {"face_ordinal_1_based": i+1, "signature_sha256": owner+"-face-sha",
                                         "signature": {"area_mm2": area}}}
        faces.append(face)
        measures.append({"feature_id": feature, "owner_id": owner, "source_geometry": copy.deepcopy(source),
            "topology_sha256": owner+"-topology", "complete_source_face_locator": {
                "face_ordinal_1_based": i+1, "signature_sha256": owner+"-face-sha"},
            "cell_count": 3, "cells": [{"id": feature+f"/cell-{j}", "area_mm2": area/3.} for j in range(3)],
            "full_reference_face_moments": {"area_mm2": area}})
    bindings = [{"first_owner": "own-a", "first_feature_id": "own-a/face", "second_owner": other,
                 "second_feature_id": other+"/face", "source_contact_id": f"contact-{i}",
                 "source_patch_id": "patch-"+other}
                for i, other in enumerate(["own-b", "own-b", "own-c"])]
    return faces, bindings, {"full_faces": measures}


@pytest.mark.parametrize("failure", [None, "missing_measure", "duplicate_face", "owner", "source", "topology", "locator", "cells", "duplicate_row", "foreign_binding"])
def test_registered_plan_keeps_every_cell_and_both_masters_of_one_source_face(failure):
    faces, bindings, measure = contact_fixture()
    if failure == "missing_measure": measure["full_faces"].pop()
    if failure == "duplicate_face": faces[-1] = copy.deepcopy(faces[0])
    if failure in ["owner", "topology"]: measure["full_faces"][0][failure+"_id" if failure == "owner" else "topology_sha256"] = "foreign"
    if failure == "source": measure["full_faces"][0]["source_geometry"]["finished_raw_file_sha256"] = "foreign"
    if failure == "locator": measure["full_faces"][0]["complete_source_face_locator"]["signature_sha256"] = "foreign"
    if failure == "cells": measure["full_faces"][0]["cells"].pop()
    if failure == "duplicate_row": bindings[1]["source_contact_id"] = bindings[0]["source_contact_id"]
    if failure == "foreign_binding": bindings[0]["second_owner"] = "own-c"
    if failure is not None:
        with pytest.raises(ValueError): scope.registered_plan(faces, bindings, measure)
        return
    plan = scope.registered_plan(faces, bindings, measure)
    assert plan["pair_count"] == 2 and plan["selected_full_face_count"] == 1
    assert plan["multiple_master_faces"] == {"own-a/face": ["own-b", "own-c"]}
    assert plan["all_source_contact_ids"] == ["contact-0", "contact-1", "contact-2"]
    assert plan["pair_cell_count"] == 6
    for row in plan["pairs"]:
        assert row["slave_owner"] == "own-a" and row["slave_feature_id"] == "own-a/face"
        assert row["complete_selected_face_area_mm2"] == 30.
        assert row["complete_selected_face_cell_ids"] == [f"own-a/face/cell-{j}" for j in range(3)]
    assert len({r["id"] for r in plan["pairs"]}) == 2
    assert [r["source_contact_ids"] for r in plan["pairs"]] == [["contact-0", "contact-1"], ["contact-2"]]
    # Reversing old first/second roles preserves the deterministic one-sided choice.
    reversed_bindings = [{**r, "first_owner": r["second_owner"], "first_feature_id": r["second_feature_id"],
                          "second_owner": r["first_owner"], "second_feature_id": r["first_feature_id"]} for r in bindings]
    assert scope.registered_plan(faces, reversed_bindings, measure) == plan


@pytest.mark.parametrize("tie", [False, True])
def test_selected_face_uses_area_before_feature_name_and_deterministic_exact_tie(tie):
    faces, bindings, measure = contact_fixture()
    areas = [100., 100., 100.] if tie else [100., 60., 90.]
    for face, saved, area in zip(faces, measure["full_faces"], areas, strict=True):
        face["complete_planar_face"]["signature"]["area_mm2"] = area
        saved["full_reference_face_moments"]["area_mm2"] = area
    result = scope.registered_plan(faces, bindings, measure)
    choices = [(r["slave_owner"], r["complete_selected_face_area_mm2"], r["complete_selected_face_cell_ids"]) for r in result["pairs"]]
    if tie:
        assert choices == [("own-a", 100., [f"own-a/face/cell-{j}" for j in range(3)])]*2
        assert result["multiple_master_faces"] == {"own-a/face": ["own-b", "own-c"]}
    else:
        assert choices == [("own-b", 60., [f"own-b/face/cell-{j}" for j in range(3)]),
                           ("own-c", 90., [f"own-c/face/cell-{j}" for j in range(3)])]
        assert result["multiple_master_faces"] == {}
        assert result["selected_full_face_count"] == 2


def method():
    return scope.component.load(domains.INJECTIVITY, "contact_scope_known_answer_geodesic")


def box_fixture(mode):
    frozen = method()
    rotation = frozen.geometry.so3_exp([.12, -.18, .07])
    axis, start = rotation[:, 0], np.array([3., -7., 5.])
    stations = np.array([0., 11., 37., 100.])
    basis = frozen.geometry.so3_exp([-.1, .2, -.3])
    chart = {"kind": "timber", "reference_axis_xyz": axis.tolist(), "reference_start_xyz_mm": start.tolist(),
        "reference_stations_mm": stations.tolist(), "node_reference_centers_xyz_mm": (start+stations[:, None]*axis).tolist(),
        "node_dof_indices": np.arange(24).reshape(4, 6).tolist(), "storage_basis_columns_xyz": basis.tolist()}
    box = [[-20., 120.], [-12., 15.], [-8., 30.]]
    extent = {"schema": "thin_bolted_finite_reference_domain_box/v1", "owner_id": "own",
        "bounds_xyz_mm": (np.asarray(box)+[-100., 100.]).tolist(), "source_identity": {
            "genuine_cached_solid_bounds_xyz_mm": box, "finished_raw_file_path": "own.brep",
            "finished_raw_file_sha256": "own-sha", "topology_sha256": "own-topology"}}
    q = np.zeros((4, 6))
    if mode == "translation": q[:, :3] = basis.T@np.array([2., -3., 4.])
    if mode == "deformed":
        q[:, :3] = np.array([[.1, .2, -.1], [-.2, .1, .3], [.4, -.3, .2], [.2, .1, -.2]])@basis
        q[:, 3:] = 1000.*np.array([[.02, -.01, .03], [.01, .02, -.01], [-.02, .01, .02], [.03, -.02, .01]])@basis
    q = q.ravel()
    bound = frozen.sufficient_box_bound(chart, q, owner_id="own", extent=extent)
    assert bound["sufficient_global_one_to_one_criterion_met"]
    return frozen, chart, q, extent, bound


@pytest.mark.parametrize("mode", ["identity", "translation", "deformed"])
def test_containing_boxes_include_exact_geodesic_images_and_both_endpoint_extensions(mode):
    frozen, chart, q, extent, bound = box_fixture(mode)
    row = scope.containing_deformed_box(chart, q, extent, bound)
    original, result = np.asarray(extent["source_identity"]["genuine_cached_solid_bounds_xyz_mm"]), np.asarray(row["bounds_xyz_mm"])
    if mode in ["identity", "translation"]:
        shift = np.zeros(3) if mode == "identity" else np.array([2., -3., 4.])
        np.testing.assert_allclose(result, original+shift[:, None]+[-1e-6, 1e-6], rtol=0., atol=1e-13)
    # Exact frozen interpolation provides an independent sampled inclusion oracle.
    for point in product(*[np.linspace(lo, hi, 9) for lo, hi in original]):
        state = frozen.geometry.surface_state(chart, q, np.asarray(point), [0., 0., 1.])
        actual = np.asarray(state["position"])
        assert np.all(actual >= result[:, 0]) and np.all(actual <= result[:, 1])
    assert all(r["box_axial_overhang_mm"] > 0. for r in row["endpoint_extensions"])
    assert row["formal_interval_arithmetic"] is False


def assert_neighbor_at_actual_point_remains_unresolved(box, point):
    other = {"owner_id": "neighbor", "bounds_xyz_mm": np.column_stack((point-1e-4, point+1e-4)).tolist()}
    pair = scope.screen_pairs({box["owner_id"]: box, "neighbor": other}, set())[0]
    assert pair["possible_new_neighbor_requiring_own_feature_coverage"]
    assert not pair["excluded_by_strict_containing_box_separation"]


@pytest.mark.parametrize("sign", [-1., 1.])
def test_containing_box_keeps_an_interior_only_displacement_extremum(sign):
    frozen, chart, q, extent, _ = box_fixture("identity")
    basis = np.asarray(chart["storage_basis_columns_xyz"])
    q.reshape(4, 6)[1, :3] = basis.T@np.array([0., sign*5., 0.])
    bound = frozen.sufficient_box_bound(chart, q, owner_id="own", extent=extent)
    row = scope.containing_deformed_box(chart, q, extent, bound)
    key = "translation_component_min_mm" if sign < 0. else "translation_component_max_mm"
    assert row[key][1] == pytest.approx(sign*5.)
    axis, start = np.asarray(chart["reference_axis_xyz"]), np.asarray(chart["reference_start_xyz_mm"])
    limit = -12. if sign < 0. else 15.
    point = np.array([0., limit, 10.])
    point[0] = start[0]+(11.-(point[1:]-start[1:])@axis[1:])/axis[0]
    actual = frozen.geometry.surface_state(chart, q, point, [0., 0., 1.])["position"]
    assert actual[1] == pytest.approx(limit+sign*5.)
    assert row["bounds_xyz_mm"][1][0] <= actual[1] <= row["bounds_xyz_mm"][1][1]
    assert_neighbor_at_actual_point_remains_unresolved(row, actual)


def four_node_chart_and_extent(box):
    chart = {"kind": "timber", "reference_axis_xyz": [1., 0., 0.], "reference_start_xyz_mm": [0., 0., 0.],
        "reference_stations_mm": [0., 40., 60., 100.], "node_reference_centers_xyz_mm": [[0., 0., 0.], [40., 0., 0.], [60., 0., 0.], [100., 0., 0.]],
        "node_dof_indices": np.arange(24).reshape(4, 6).tolist(), "storage_basis_columns_xyz": np.eye(3).tolist()}
    extent = {"schema": "thin_bolted_finite_reference_domain_box/v1", "owner_id": "own",
        "bounds_xyz_mm": (np.asarray(box)+[-100., 100.]).tolist(), "source_identity": {
            "genuine_cached_solid_bounds_xyz_mm": box, "finished_raw_file_path": "own.brep",
            "finished_raw_file_sha256": "own-sha", "topology_sha256": "own-topology"}}
    return chart, extent


@pytest.mark.parametrize("profile", ["middle", "later"])
def test_containing_box_keeps_twist_in_each_part_of_chart_without_overhang(profile):
    frozen = method()
    chart, extent = four_node_chart_and_extent([[0., 100.], [-1., 1.], [-2., 2.]])
    angle = .2 if profile == "middle" else .05
    q = np.zeros((4, 6))
    if profile == "middle": q[1:3, 3] = 1000.*angle
    else: q[2:, 3] = 1000.*angle
    q = q.ravel()
    bound = frozen.sufficient_box_bound(chart, q, owner_id="own", extent=extent)
    assert bound["sufficient_global_one_to_one_criterion_met"]
    row = scope.containing_deformed_box(chart, q, extent, bound)
    expected_radius = 2.*np.sin(angle/2.)*np.sqrt(5.)
    assert row["rotation_displacement_norm_bound_mm"] == pytest.approx(expected_radius, abs=1e-14)
    assert all(r["box_axial_overhang_mm"] == 0. for r in row["endpoint_extensions"])
    actual = frozen.geometry.surface_state(chart, q, np.array([40. if profile == "middle" else 60., 1., -2.]), [0., 0., 1.])["position"]
    assert actual[1] == pytest.approx(np.cos(angle)+2.*np.sin(angle), abs=1e-14)
    assert actual[1] > 1.+1e-6 and actual[1] <= row["bounds_xyz_mm"][1][1]
    assert_neighbor_at_actual_point_remains_unresolved(row, actual)


def test_radial_arm_bound_uses_the_farthest_asymmetric_box_corner():
    frozen = method()
    chart, extent = four_node_chart_and_extent([[0., 100.], [-1., 3.], [-2., 5.]])
    q = np.zeros((4, 6)); q[1:3, 3] = 200.
    q = q.ravel()
    bound = frozen.sufficient_box_bound(chart, q, owner_id="own", extent=extent)
    row = scope.containing_deformed_box(chart, q, extent, bound)
    assert row["reference_radial_arm_radius_bound_mm"] == pytest.approx(np.sqrt(34.), abs=1e-14)
    actual = frozen.geometry.surface_state(chart, q, np.array([40., 3., 5.]), [0., 0., 1.])["position"]
    assert actual[2] == pytest.approx(3.*np.sin(.2)+5.*np.cos(.2), abs=1e-14)
    assert actual[2] > 5.+1e-6 and actual[2] <= row["bounds_xyz_mm"][2][1]
    assert_neighbor_at_actual_point_remains_unresolved(row, actual)


@pytest.mark.parametrize("endpoint", ["first", "last"])
def test_containing_box_keeps_dominant_rigid_overhang_at_each_endpoint(endpoint):
    frozen = method()
    limits = [-40., 100.] if endpoint == "first" else [0., 140.]
    chart, extent = four_node_chart_and_extent([limits, [-1., 1.], [-2., 2.]])
    q = np.zeros((4, 6)); q[0 if endpoint == "first" else -1, 5] = 200.
    q = q.ravel()
    bound = frozen.sufficient_box_bound(chart, q, owner_id="own", extent=extent)
    assert bound["sufficient_global_one_to_one_criterion_met"]
    row = scope.containing_deformed_box(chart, q, extent, bound)
    expected_radius = 2.*np.sin(.1)*np.sqrt(40.**2+5.)
    assert row["rotation_displacement_norm_bound_mm"] == pytest.approx(expected_radius, abs=1e-13)
    extensions = {r["endpoint"]: r for r in row["endpoint_extensions"]}
    assert extensions[endpoint]["box_axial_overhang_mm"] == 40.
    point = [-40., -1., 0.] if endpoint == "first" else [140., 1., 0.]
    actual = frozen.geometry.surface_state(chart, q, np.asarray(point), [0., 0., 1.])["position"]
    expected_y = 40.*np.sin(.2)+np.cos(.2)
    assert actual[1] == pytest.approx(-expected_y if endpoint == "first" else expected_y, abs=1e-13)
    assert np.all(actual >= np.asarray(row["bounds_xyz_mm"])[:, 0])
    assert np.all(actual <= np.asarray(row["bounds_xyz_mm"])[:, 1])


@pytest.mark.parametrize("failure", ["owner", "chart", "state", "extent", "insufficient", "segment", "endpoint", "box", "padding"])
def test_containing_box_rejects_wrong_own_state_domain_or_incomplete_bounds(failure):
    _, chart, q, extent, bound = box_fixture("deformed")
    padding = 1e-6
    if failure == "owner": bound["owner_id"] = "foreign"
    if failure == "chart": chart["reference_start_xyz_mm"][1] += .1
    if failure == "state": q[3] += .1
    if failure == "extent": extent["bounds_xyz_mm"][0][0] -= 1.
    if failure == "insufficient": bound["sufficient_global_one_to_one_criterion_met"] = False
    if failure == "segment": bound["segments"].pop(1)
    if failure == "endpoint": bound["rigid_endpoint_extensions"].reverse()
    if failure == "box":
        extent["source_identity"]["genuine_cached_solid_bounds_xyz_mm"][0][0] = -1000.
        bound["extent_canonical_sha256"] = scope.canonical_sha(extent)
    if failure == "padding": padding = float("nan")
    with pytest.raises(ValueError): scope.containing_deformed_box(chart, q, extent, bound, numerical_padding_mm=padding)


def test_neighbor_screen_keeps_touching_overlapping_and_unregistered_pairs_without_contact_claim():
    boxes = {name: {"owner_id": name, "bounds_xyz_mm": box} for name, box in {
        "a": [[0., 1.], [0., 1.], [0., 1.]],
        "b": [[1., 2.], [0., 1.], [0., 1.]],
        "c": [[.5, 1.5], [.5, 1.5], [.5, 1.5]],
        "d": [[2.01, 3.], [0., 1.], [0., 1.]]}.items()}
    result = scope.screen_pairs(boxes, {("a", "b")})
    assert len(result) == 6
    pairs = {(r["first"], r["second"]): r for r in result}
    assert pairs["a", "b"]["registered_source_pair"]
    assert not pairs["a", "b"]["excluded_by_strict_containing_box_separation"]
    assert not pairs["a", "b"]["possible_new_neighbor_requiring_own_feature_coverage"]
    assert pairs["a", "c"]["possible_new_neighbor_requiring_own_feature_coverage"]
    for pair in [("a", "d"), ("b", "d"), ("c", "d")]:
        assert pairs[pair]["excluded_by_strict_containing_box_separation"]
        assert not pairs[pair]["possible_new_neighbor_requiring_own_feature_coverage"]
    boxes["c"]["owner_id"] = "foreign"
    with pytest.raises(ValueError): scope.screen_pairs(boxes, set())


def test_historical_domain_pin_resolution_preserves_original_receipt_and_exact_snapshot(monkeypatch, tmp_path):
    monkeypatch.setattr(scope.current, "ROOT", tmp_path)
    path = tmp_path/scope.DOMAIN_SNAPSHOT
    path.parent.mkdir(parents=True)
    path.write_text("exact historical producer\n")
    ref = scope.current.ref(path)
    old = {"path": scope.DOMAIN_PRODUCER, "sha256": ref["sha256"]}
    record = {"producer": old, "source_sha256": {old["path"]: old["sha256"], "unchanged": "digest"}}
    before = copy.deepcopy(record)
    pins, resolution = scope.resolved_domain_pins(record)
    assert record == before and resolution["original"] == old and resolution["preserved_source"] == ref
    assert pins == {scope.DOMAIN_SNAPSHOT: ref["sha256"], "unchanged": "digest"}
    path.write_text("wrong replacement\n")
    with pytest.raises(ValueError): scope.resolved_domain_pins(record)


def orchestration_fixture(monkeypatch, root):
    current = scope.current
    monkeypatch.setattr(current, "ROOT", root)
    for name in ["producer.py", "intake.py", "intake-only.py", "response.py", "component.py", "canonical.py", "bridge.py", "domain.py", "domain-only.py", "measure-only.py", "uv.lock"]:
        (root/name).write_text("current "+name+"\n")
    monkeypatch.setattr(scope, "OWN", root/"producer.py")
    monkeypatch.setattr(scope, "LOADED_SHA", current.sha(scope.OWN))
    monkeypatch.setattr(current, "OWN", root/"response.py")
    monkeypatch.setattr(current, "LOADED_SHA", current.sha(current.OWN))
    monkeypatch.setattr(scope.intake_source, "OWN", root/"intake.py")
    monkeypatch.setattr(scope.intake_source, "LOADED_SHA", current.sha(scope.intake_source.OWN))
    monkeypatch.setattr(scope, "INTAKE", current.ref(scope.intake_source.OWN))
    monkeypatch.setattr(scope, "DOMAIN_PRODUCER", "domain.py")
    monkeypatch.setattr(scope, "DOMAIN_SNAPSHOT", "snapshots/domain.py")
    (root/"snapshots").mkdir()
    (root/scope.DOMAIN_SNAPSHOT).write_text("exact old domain producer\n")
    monkeypatch.setattr(component := scope.component, "own_ref", lambda: current.ref(root/"component.py"))
    monkeypatch.setattr(component, "canonical_dependency", lambda: current.ref(root/"canonical.py"))
    bridge = SimpleNamespace(OWN=root/"bridge.py", LOADED_SHA=current.sha(root/"bridge.py"))
    manifest = {"references": {"bridge": current.ref(bridge.OWN)}, "release": {"structural_released": False}}
    manifest_path = root/"manifest.json"
    manifest_path.write_text(json.dumps(manifest))
    monkeypatch.setattr(current, "MANIFEST", manifest_path)
    monkeypatch.setattr(current, "manifest", lambda: manifest)
    monkeypatch.setattr(current, "load", lambda key: bridge)
    owners, charts, extents, faces, measures = [], {}, {}, [], []
    for i in range(22):
        owner = f"own-{i:02d}"
        path = root/(owner+".brep")
        path.write_text(owner+" original solid\n")
        source, topology = current.ref(path), owner+"-topology"
        identity = {"finished_raw_file_path": source["path"], "finished_raw_file_sha256": source["sha256"]}
        owners.append({"owner_id": owner, "finished_source": {**source, "id": owner, "bytes": path.stat().st_size,
            "volume_mm3": 100., "bounds_xyz_mm": [[1000.*i, 1000.*i+100.], [-1., 1.], [-1., 1.]]},
            "frozen_constructor_topology_sha256": topology})
        start = np.array([1000.*i, 0., 0.])
        charts[owner] = {"kind": "timber", "reference_axis_xyz": [1., 0., 0.], "reference_start_xyz_mm": start.tolist(),
            "reference_stations_mm": [0., 100.], "node_reference_centers_xyz_mm": [start.tolist(), (start+[100., 0., 0.]).tolist()],
            "node_dof_indices": (np.arange(12)+12*i).reshape(2, 6).tolist(), "storage_basis_columns_xyz": np.eye(3).tolist()}
        box = [[1000.*i, 1000.*i+100.], [-1., 1.], [-1., 1.]]
        extents[owner] = {"owner_id": owner, "bounds_xyz_mm": (np.asarray(box)+[-100., 100.]).tolist(),
            "source_identity": {**identity, "topology_sha256": topology, "genuine_cached_solid_bounds_xyz_mm": box}}
        for j in range(3 if i < 7 else 2):
            feature = owner+f"/face-{j}"
            faces.append({"owner_id": owner, "source_geometry": identity, "topology_sha256": topology,
                "closed_boundary_feature": {"feature_id": feature}, "complete_planar_face": {
                    "face_ordinal_1_based": j+1, "signature_sha256": feature+"-sha", "signature": {"area_mm2": 30.*(i+1)}}})
            measures.append({"feature_id": feature, "owner_id": owner, "source_geometry": identity, "topology_sha256": topology,
                "complete_source_face_locator": {"face_ordinal_1_based": j+1, "signature_sha256": feature+"-sha"}, "cell_count": 3,
                "cells": [{"id": feature+f"/cell-{c}"} for c in range(3)], "full_reference_face_moments": {"area_mm2": 30.*(i+1)}})
    names = sorted(charts)
    pair_names = list(scope.combinations(names, 2))[:38]
    bindings = [{"source_contact_id": f"contact-{i:03d}", "source_patch_id": f"patch-{i % 38}",
        "first_owner": pair_names[i % 38][0], "second_owner": pair_names[i % 38][1],
        "first_feature_id": pair_names[i % 38][0]+"/face-0", "second_feature_id": pair_names[i % 38][1]+"/face-0"} for i in range(332)]
    cases, source_cases, bound_cases = [], [], []
    for i, case in enumerate(component.SEQUENCE):
        q = np.zeros(9350)
        for j, chart in enumerate(charts.values()):
            shift = -1000. if j in [1, 21] else 0.
            q[np.asarray(chart["node_dof_indices"])[:, 0]] = i+.1*j+shift
        field = {"response": {"q": q.tolist(), "q_canonical_sha256": scope.canonical_sha(q.tolist())}}
        path = root/f"field-{i}.json"
        path.write_text(json.dumps(field))
        binding = {"case_id": case, "state_id": f"state-{i}", "field": current.ref(path)}
        cases.append((binding, field, {})); source_cases.append(binding)
        qsha = scope.canonical_sha(np.r_[q, np.zeros(100)].tolist())
        bounds = []
        for owner, chart in charts.items():
            bounds.append({"owner_id": owner, "row_canonical_sha256": scope.canonical_sha(chart), "q_canonical_sha256": qsha,
                "extent_canonical_sha256": scope.canonical_sha(extents[owner]), "sufficient_global_one_to_one_criterion_met": True,
                "segments": [{"segment_index": 0, "station_interval_mm": [0., 100.], "absolute_geodesic_angle_upper_rad": 0.}],
                "rigid_endpoint_extensions": [{"endpoint": "first", "station_mm": 0., "rigid_endpoint_extension_L": 0.},
                    {"endpoint": "last", "station_mm": 100., "rigid_endpoint_extension_L": 0.}]})
        bound_cases.append({**binding, "bounds": bounds, "full_diagnostic_q_canonical_sha256": qsha})
    pins = {p.name: current.sha(p) for p in root.iterdir() if p.is_file()}
    common = {"owners": owners, "registered_complete_own_faces": faces, "source_contact_face_bindings": bindings,
        "cases": source_cases, "case_sequence": component.SEQUENCE, "counts": {"timber_owners": 22, "registered_full_faces": 51},
        "geometry_revision": "current-geometry", "hardware_revision": "current-hardware", "extra_grid": False}
    measure = {**copy.deepcopy(common), "source_sha256": {"domain.py": pins["domain.py"], "measure-only.py": pins["measure-only.py"]},
               "current_complete_reference_face_measure": {"full_faces": measures}}
    old = {"path": "domain.py", "sha256": current.sha(root/scope.DOMAIN_SNAPSHOT)}
    domains_record = {**copy.deepcopy(common), "producer": old,
        "source_sha256": {"domain.py": old["sha256"], "domain-only.py": pins["domain-only.py"]},
        "current_diagnostic_ambient_injectivity": {"all132_sufficient_on_own_ambient_box": True,
            "charts": charts, "extents": extents, "cases": bound_cases}}
    monkeypatch.setattr(scope.intake_source, "intake", lambda: (cases, {k: v for k, v in pins.items() if k not in ["domain-only.py", "measure-only.py"]}))
    def save():
        for key, data, filename in [("MEASURE", measure, "measure.json"), ("DOMAINS", domains_record, "domains.json")]:
            (root/filename).write_text(json.dumps(data))
            monkeypatch.setattr(scope, key, current.ref(root/filename))
    save()
    return cases, measure, domains_record, bridge, save


@pytest.mark.parametrize("failure", [None, "before", "after", "measure_before", "measure_after", "intake_before", "intake_after", "case", "q", "geometry", "bound_state", "bridge", "producer", "snapshot", "order"])
def test_current_orchestration_checks_all22_owners_six_own_states_and231_pairs_before_and_after(monkeypatch, tmp_path, failure):
    cases, measure, records, bridge, save = orchestration_fixture(monkeypatch, tmp_path)
    expected_closure = {p.name: scope.current.sha(p) for p in tmp_path.iterdir() if p.is_file()}
    expected_closure[scope.DOMAIN_SNAPSHOT] = scope.current.sha(tmp_path/scope.DOMAIN_SNAPSHOT)
    if failure == "before": (tmp_path/"domain-only.py").write_text("changed before query\n")
    if failure == "measure_before": (tmp_path/"measure-only.py").write_text("changed measure source before query\n")
    if failure == "intake_before": (tmp_path/"intake-only.py").write_text("changed intake source before query\n")
    if failure == "case": records["cases"][4]["state_id"] = "foreign"
    if failure == "q": cases[4][1]["response"]["q"][0] += 1.
    if failure == "geometry": records["current_diagnostic_ambient_injectivity"]["extents"]["own-21"]["source_identity"]["finished_raw_file_sha256"] = "foreign"
    if failure == "bound_state": records["current_diagnostic_ambient_injectivity"]["cases"][5]["bounds"][-1]["q_canonical_sha256"] = "foreign"
    if failure == "bridge": bridge.LOADED_SHA = "foreign"
    if failure == "producer": monkeypatch.setattr(scope, "LOADED_SHA", "foreign")
    if failure == "snapshot": (tmp_path/scope.DOMAIN_SNAPSHOT).write_text("changed old source\n")
    if failure == "order": cases.reverse()
    save()
    for ref in [scope.MEASURE, scope.DOMAINS]: expected_closure[ref["path"]] = ref["sha256"]
    calls, verifies = [], []
    original = scope.screen_pairs
    original_verify = scope.current.verify
    def verify(pins):
        verifies.append(dict(pins))
        assert pins == expected_closure
        return original_verify(pins)
    monkeypatch.setattr(scope.current, "verify", verify)
    expected_registry = {tuple(sorted((r["first_owner"], r["second_owner"])))
                         for r in measure["source_contact_face_bindings"]}
    def screen(boxes, registered):
        assert registered == expected_registry
        result = original(boxes, registered)
        calls.append(set(boxes))
        if failure == "after" and len(calls) == 6:
            (tmp_path/"domain-only.py").write_text("changed during final screen\n")
        if failure == "measure_after" and len(calls) == 6:
            (tmp_path/"measure-only.py").write_text("changed measure source during final screen\n")
        if failure == "intake_after" and len(calls) == 6:
            (tmp_path/"intake-only.py").write_text("changed intake source during final screen\n")
        return result
    monkeypatch.setattr(scope, "screen_pairs", screen)
    if failure is not None:
        with pytest.raises(ValueError): scope.run()
        if failure in ["before", "measure_before", "intake_before"]: assert not calls
        if failure in ["after", "measure_after", "intake_after"]: assert len(calls) == 6
        return
    result = scope.run()
    assert len(verifies) == 2 and verifies[0] == verifies[1] == result["source_sha256"] == expected_closure
    assert len(calls) == len(result["cases"]) == 6
    assert all(owners == {f"own-{i:02d}" for i in range(22)} for owners in calls)
    assert result["registered_plan"]["all_source_contact_ids"] == sorted(r["source_contact_id"] for r in measure["source_contact_face_bindings"])
    assert {tuple(sorted((r["slave_owner"], r["master_owner"]))) for r in result["registered_plan"]["pairs"]} == expected_registry
    for i, row in enumerate(result["cases"]):
        assert row["case_id"] == scope.component.SEQUENCE[i] and row["state_id"] == f"state-{i}"
        assert len(row["containing_deformed_boxes"]) == 22 and len(row["all231_pair_screens"]) == 231
        assert row["excluded_pair_count"] == 229 and row["possible_new_neighbor_pair_count"] == 1
        pairs = {(r["first"], r["second"]): r for r in row["all231_pair_screens"]}
        assert len(pairs) == 231
        for pair, data in pairs.items():
            assert data["registered_source_pair"] == (pair in expected_registry)
        for pair in [("own-00", "own-01"), ("own-20", "own-21")]:
            assert not pairs[pair]["excluded_by_strict_containing_box_separation"]
        assert not pairs["own-00", "own-01"]["possible_new_neighbor_requiring_own_feature_coverage"]
        assert pairs["own-20", "own-21"]["possible_new_neighbor_requiring_own_feature_coverage"]
        for j, box in enumerate(row["containing_deformed_boxes"]):
            assert box["owner_id"] == f"own-{j:02d}"
            shift = -1000. if j in [1, 21] else 0.
            assert box["translation_component_min_mm"][0] == pytest.approx(i+.1*j+shift)
    assert result["source_sha256"]["domain-only.py"] == scope.current.sha(tmp_path/"domain-only.py")
    assert result["source_sha256"]["measure-only.py"] == scope.current.sha(tmp_path/"measure-only.py")
    assert result["source_sha256"]["intake-only.py"] == scope.current.sha(tmp_path/"intake-only.py")
    assert result["source_sha256"][scope.DOMAIN_SNAPSHOT] == records["producer"]["sha256"]
    assert result["source_sha256"]["domain.py"] == scope.current.sha(tmp_path/"domain.py")
    assert result["distance_inverse_contact_force_or_frame_solve_performed"] is False
    assert result["structural_acceptance"] is False
