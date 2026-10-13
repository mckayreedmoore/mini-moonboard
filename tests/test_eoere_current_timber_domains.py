import copy
from itertools import combinations
from types import SimpleNamespace

import numpy as np
import pytest

from scripts import eoere_current_timber_domains as domains


def source_cases():
    names = [f"own-timber-{i:02d}" for i in range(22)]
    sources = {"timber_rows": [{"name": n} for n in names],
        "finished_body_observations": [{"id": n, "source": {"path": n+".brep", "sha256": "own-sha"},
                                       "volume_mm3": i+1.} for i, n in enumerate(names)]}
    pairs = list(combinations(names, 2))[:38]
    rows = [{"id": f"contact-{i:03d}", "kind": "timber_face_contact",
             "first": pairs[i % 38][0], "second": pairs[i % 38][1],
             "source_first_face_signature_sha256": "minus", "source_second_face_signature_sha256": "plus",
             "source_patch_id": f"patch-{i % 38}", "direction_xyz": [1., 0., 0.], "point_xyz_mm": [0., 0., 0.]}
            for i in range(332)]
    return [({"case_id": c, "state_id": f"state-{i}", "field": {"path": f"field-{i}", "sha256": f"field-sha-{i}"}},
             {"source_inputs": copy.deepcopy(sources), "reference_interaction_descriptors": copy.deepcopy(rows)}, {})
            for i, c in enumerate(domains.component.SEQUENCE)]


@pytest.mark.parametrize("failure", [None, "old_twenty", "case_order", "changed_contacts", "changed_solids", "duplicate_row"])
def test_current_sources_requires_exact_six_current_geometry_and_contact_ledgers(failure):
    cases = source_cases()
    if failure == "old_twenty":
        for _, field, _ in cases:
            field["source_inputs"]["timber_rows"] = field["source_inputs"]["timber_rows"][:20]
    if failure == "case_order": cases.reverse()
    if failure == "changed_contacts": cases[3][1]["reference_interaction_descriptors"][7]["point_xyz_mm"][1] = 1.
    if failure == "changed_solids": cases[2][1]["source_inputs"]["finished_body_observations"][3]["source"]["sha256"] = "other"
    if failure == "duplicate_row": cases[0][1]["reference_interaction_descriptors"][4]["id"] = "contact-003"
    if failure is not None:
        with pytest.raises(ValueError): domains.current_sources(cases)
    else:
        observations, rows = domains.current_sources(cases)
        assert len(observations) == 22 and len(rows) == 332
        assert len({(r["first"], r["second"]) for r in rows}) == 38


def geometry_fixture(owner, source):
    features, faces = [], []
    for i, (label, normal) in enumerate([("minus", [-1., 0., 0.]), ("plus", [1., 0., 0.])], 1):
        features.append({"feature_id": f"{owner}/face-{i}", "face_ordinal_1_based": i,
                         "surface_type": "PLANE", "face_area_mm2": 1000.})
        faces.append({"face_id": f"{owner}/source-{i}", "face_ordinal_1_based": i,
                      "signature_sha256": label, "signature": {"oriented_normal_xyz": normal,
                          "area_mm2": 1000., "center_xyz_mm": [0., 0., 0.], "full_face_marker": [owner, i]},
                      "_shape": object()})
    features.append({"feature_id": f"{owner}/face-3", "face_ordinal_1_based": 3, "surface_type": "CYLINDER"})
    return SimpleNamespace(owner_id=owner, source_identity=source, topology_sha256=f"topology-{owner}",
        face_records=features), faces


@pytest.mark.parametrize("failure", [None, "wrong_owner", "missing_face", "ambiguous_signature", "curved_face", "reversed_side"])
def test_registered_face_bindings_preserve_both_own_full_sides_and_multiple_neighbors(failure):
    geometries, faces = {}, {}
    for owner in ["own-a", "own-b", "own-c"]:
        geometries[owner], faces[owner] = geometry_fixture(owner, {"finished_raw_file_path": owner+".brep"})
    rows = [{"id": f"contact-{i}", "source_patch_id": f"patch-{i}", "first": "own-a", "second": other,
             "source_first_face_signature_sha256": "minus", "source_second_face_signature_sha256": "plus",
             "point_xyz_mm": [0., i+.5, 0.], "direction_xyz": [1., 0., 0.]}
            for i, other in enumerate(["own-b", "own-c"])]
    if failure == "wrong_owner": geometries["own-a"].owner_id = "foreign"
    if failure == "missing_face": rows[1]["source_second_face_signature_sha256"] = "unknown"
    if failure == "ambiguous_signature": faces["own-b"].append(copy.copy(faces["own-b"][0]))
    if failure == "curved_face": geometries["own-c"].face_records[1]["surface_type"] = "CYLINDER"
    if failure == "reversed_side": rows[1]["direction_xyz"] = [-1., 0., 0.]
    if failure is not None:
        with pytest.raises(ValueError): domains.bind_registered_faces(geometries, faces, rows)
    else:
        registered, bindings = domains.bind_registered_faces(geometries, faces, rows)
        assert len(registered) == 3 and len(bindings) == 2
        first = next(r for r in registered if r["owner_id"] == "own-a")
        assert first["registered_opposing_owners"] == ["own-b", "own-c"]
        assert first["registered_source_patch_ids"] == ["patch-0", "patch-1"]
        assert first["complete_planar_face"]["signature"]["area_mm2"] == 1000.
        assert first["complete_planar_face"]["signature"]["full_face_marker"] == ["own-a", 1]
        assert "_shape" not in first["complete_planar_face"]
        for record in registered:
            owner = record["owner_id"]
            geometry = geometries[owner]
            ordinal = record["closed_boundary_feature"]["face_ordinal_1_based"]
            face = next(f for f in faces[owner] if f["face_ordinal_1_based"] == ordinal)
            assert record["complete_planar_face"] == {k: v for k, v in face.items() if k != "_shape"}
            assert record["closed_boundary_feature"] == geometry.face_records[ordinal-1]
            assert record["source_geometry"] == geometry.source_identity
            assert record["topology_sha256"] == geometry.topology_sha256
        assert [b["second_feature_id"] for b in bindings] == ["own-b/face-2", "own-c/face-2"]
        assert all(b["first_feature_id"] == "own-a/face-1" for b in bindings)


@pytest.mark.parametrize("include_injectivity,failure", [
    (mode, failure) for mode in [False, True]
    for failure in [None, "source_drift_before", "source_drift_after", "producer_drift", "atlas_drift", "volume"]
]+[(True, failure) for failure in ["kernel_drift_before", "kernel_drift_after", "preflight_drift_before", "import_test_drift", "loaded_import_test_drift"]])
@pytest.mark.parametrize("include_measure", [False, True])
def test_current_boundary_orchestration_imports_all22_own_sources_and_checks_pins_before_and_after(monkeypatch, tmp_path, failure, include_injectivity, include_measure):
    cases = source_cases()
    current = domains.current
    paths = ["producer.py", "intake.py", "atlas.py", "distance.py", "container.py", "component.py", "canonical.py", "response.py", "uv.lock"]
    optional_paths = ["preflight.json", "injectivity.py", "preflight-source.json", "kernel-source.json", "imported-test.py"] if include_injectivity else []
    if include_measure:
        optional_paths += ["query.py", "plan.py", "plan.json", "test_query.py", "quad-only.py"]
    for path in paths+optional_paths:
        (tmp_path/path).write_text(path)
    def ref(path):
        return {"path": path, "sha256": current.sha(tmp_path/path)}
    monkeypatch.setattr(current, "ROOT", tmp_path)
    monkeypatch.setattr(current, "OWN", tmp_path/"response.py")
    monkeypatch.setattr(current, "LOADED_SHA", current.sha(current.OWN))
    monkeypatch.setattr(domains, "OWN", tmp_path/"producer.py")
    monkeypatch.setattr(domains, "LOADED_SHA", current.sha(domains.OWN))
    monkeypatch.setattr(domains, "ATLAS", tmp_path/"atlas.py")
    monkeypatch.setattr(domains, "ATLAS_SHA", current.sha(domains.ATLAS))
    monkeypatch.setattr(domains, "INTAKE", ref("intake.py"))
    monkeypatch.setattr(domains.intake_source, "OWN", tmp_path/"intake.py")
    monkeypatch.setattr(domains.intake_source, "LOADED_SHA", domains.INTAKE["sha256"])
    monkeypatch.setattr(domains, "DISTANCE", ref("distance.py"))
    monkeypatch.setattr(domains, "CONTAINER", ref("container.py"))
    if include_injectivity:
        (tmp_path/"preflight.json").write_text(domains.json.dumps({"source_sha256": {"preflight-source.json": ref("preflight-source.json")["sha256"]}}))
        monkeypatch.setattr(domains, "PREFLIGHT", ref("preflight.json"))
        monkeypatch.setattr(domains, "INJECTIVITY", ref("injectivity.py"))
        monkeypatch.setattr(domains, "INJECTIVITY_IMPORT_TEST", ref("imported-test.py"))
    if include_measure:
        monkeypatch.setattr(domains, "QUADRATURE", ref("query.py"))
    monkeypatch.setattr(domains.component, "own_ref", lambda: ref("component.py"))
    monkeypatch.setattr(domains.component, "canonical_dependency", lambda: ref("canonical.py"))
    observations = cases[0][1]["source_inputs"]["finished_body_observations"]
    for row in observations:
        (tmp_path/row["source"]["path"]).write_text(row["id"])
        row["source"] = ref(row["source"]["path"])
    for _, field, _ in cases[1:]:
        field["source_inputs"]["finished_body_observations"] = copy.deepcopy(observations)
    pins = {r["source"]["path"]: r["source"]["sha256"] for r in observations}
    pins.update({p: ref(p)["sha256"] for p in paths})
    expected_pins = copy.deepcopy(pins)
    expected_pins.update({p: ref(p)["sha256"] for p in optional_paths})
    monkeypatch.setattr(domains.intake_source, "intake", lambda: (cases, pins))
    calls, checked, wrappers, constructors, validated_solids = [], [], [], [], {}

    def verify(received):
        checked.append(dict(received))
        for path, sha in received.items():
            current.require(current.sha(tmp_path/path) == sha, "source drift: "+path)
        return received

    def import_brep(path):
        owner = (tmp_path/path).read_text()
        calls.append((str(path), owner))
        if failure == "source_drift_after" and not include_measure and len(calls) == 22:
            (tmp_path/observations[-1]["source"]["path"]).write_text("drift")
        if failure == "kernel_drift_after" and len(calls) == 22:
            (tmp_path/"kernel-source.json").write_text("drift")
        return SimpleNamespace(owner=owner)

    def strict_solid(shape, received):
        assert received is reference
        wrappers.append(shape.owner)
        validated_solids[shape.owner] = shape
        return shape, {"owner": shape.owner, "all_original_geometry_preserved": True}

    def constructor(solid, *, owner_id, source_identity, linear_tolerance_mm, tie_tolerance_mm):
        assert solid.owner == owner_id
        own = next(row for row in observations if row["id"] == owner_id)
        assert source_identity == {"finished_raw_file_path": own["source"]["path"],
                                   "finished_raw_file_sha256": own["source"]["sha256"]}
        assert linear_tolerance_mm == 1e-7 and tie_tolerance_mm == 1e-6
        constructors.append(owner_id)
        result, _ = geometry_fixture(owner_id, source_identity)
        result.topology = {"volume_mm3": own["volume_mm3"]+(.1 if failure == "volume" else 0.), "owner_id": owner_id}
        return result

    reference = SimpleNamespace(cq=SimpleNamespace(Shape=SimpleNamespace(importBrep=import_brep)),
        ReferenceSolidDistance=constructor, source_pins=lambda: {"distance.py": domains.DISTANCE["sha256"]},
        tools=lambda: {"fixture_only": True})
    container = SimpleNamespace(strict_solid=strict_solid)
    def source_face_records(owner, solid):
        assert solid is validated_solids[owner] and solid.owner == owner
        return geometry_fixture(owner, {})[1]
    method = SimpleNamespace(source_pins=lambda: {"kernel-source.json": expected_pins["kernel-source.json"]},
        geometry=SimpleNamespace(LOADED_TEST_SHA=domains.INJECTIVITY_IMPORT_TEST["sha256"]))
    quadrature = SimpleNamespace(LOADED_SHA=domains.QUADRATURE["sha256"],
        PLAN_SOURCE="plan.py", PLAN_SOURCE_SHA=expected_pins.get("plan.py"),
        PLAN_OUTPUT="plan.json", PLAN_SHA=expected_pins.get("plan.json"),
        TEST=tmp_path/"test_query.py", LOADED_TEST_SHA=expected_pins.get("test_query.py"),
        INITIAL_PINS={"quad-only.py": expected_pins.get("quad-only.py")},
        EXPECTED_VERSIONS={"geometry": "pinned"}, versions=lambda: {"geometry": "pinned"})
    def load(source, _):
        if source == domains.DISTANCE: return reference
        if source == domains.CONTAINER: return container
        if include_measure and source == domains.QUADRATURE: return quadrature
        assert include_injectivity and source == domains.INJECTIVITY
        return method
    monkeypatch.setattr(domains.component, "load", load)
    def injectivity_checks(received_cases, geometries, received_observations, preflight, received_method, received_pins):
        assert include_injectivity and received_cases is cases and received_method is method
        assert received_observations == {r["id"]: r for r in observations}
        assert list(geometries) == constructors and len(geometries) == 22
        assert preflight == domains.json.loads((tmp_path/"preflight.json").read_bytes())
        assert received_pins == expected_pins
        return {"scope": "orchestration fixture only"}
    monkeypatch.setattr(domains, "injectivity_checks", injectivity_checks)
    def full_face_measure(geometries, faces, received_method, *, progress):
        assert include_measure and received_method is quadrature and progress is None
        assert len(geometries) == 22 and all(f["owner_id"] in geometries for f in faces)
        if failure == "source_drift_after": (tmp_path/"quad-only.py").write_text("drift")
        return {"scope": "whole-face orchestration fixture only"}
    monkeypatch.setattr(domains, "full_face_measure", full_face_measure)
    monkeypatch.setattr(domains.atlas, "source_face_records", source_face_records)
    monkeypatch.setattr(current, "verify", verify)
    monkeypatch.setattr(current, "manifest", lambda: {"release": {"candidate_accepted": False}})
    if failure == "source_drift_before": (tmp_path/("quad-only.py" if include_measure else observations[7]["source"]["path"])).write_text("drift")
    if failure == "producer_drift": domains.OWN.write_text("drift")
    if failure == "atlas_drift": pins["atlas.py"] = "foreign"
    if failure == "kernel_drift_before": (tmp_path/"kernel-source.json").write_text("drift")
    if failure == "preflight_drift_before": (tmp_path/"preflight-source.json").write_text("drift")
    if failure == "import_test_drift": (tmp_path/"imported-test.py").write_text("drift")
    if failure == "loaded_import_test_drift": method.geometry.LOADED_TEST_SHA = "foreign"
    if failure is not None:
        with pytest.raises(ValueError):
            domains.run(include_injectivity=include_injectivity, include_measure=include_measure)
        if failure in ["source_drift_before", "producer_drift", "atlas_drift", "kernel_drift_before", "preflight_drift_before", "import_test_drift", "loaded_import_test_drift"]:
            assert calls == []
    else:
        result = domains.run(include_injectivity=include_injectivity, include_measure=include_measure)
        assert len(calls) == len(wrappers) == len(constructors) == 22
        assert constructors == [r["id"] for r in observations]
        assert [c[1] for c in calls] == constructors
        assert checked == [expected_pins, expected_pins] and result["source_sha256"] == expected_pins
        assert result["counts"]["registered_pairs"] == result["counts"]["registered_patches"] == 38
        assert result["counts"]["registered_contact_rows"] == 332
        assert result["counts"]["boundary_surface_types"] == {"PLANE": 44, "CYLINDER": 22}
        assert len(result["registered_complete_own_faces"]) > 22
        for record in result["registered_complete_own_faces"]:
            owner = record["owner_id"]
            own = next(o for o in observations if o["id"] == owner)
            identity = {"finished_raw_file_path": own["source"]["path"], "finished_raw_file_sha256": own["source"]["sha256"]}
            geometry, own_faces = geometry_fixture(owner, identity)
            ordinal = record["closed_boundary_feature"]["face_ordinal_1_based"]
            assert record["source_geometry"] == identity and record["topology_sha256"] == geometry.topology_sha256
            assert record["closed_boundary_feature"] == geometry.face_records[ordinal-1]
            assert record["complete_planar_face"] == {k: v for k, v in own_faces[ordinal-1].items() if k != "_shape"}
        assert result["all22_current_finished_solids_have_valid_closed_outward_boundary"] is True
        assert result["candidate_distance_query_deformation_quadrature_or_mechanics_run"] is include_measure
        assert result["candidate_inverse_or_contact_force_or_frame_mechanics_run"] is False
        assert result["complete_contact_provider_or_response_qualified"] is False
        assert result["structural_acceptance"] is False
        assert result["current_saved_pose_injectivity_bound_evaluated"] is include_injectivity
        assert result["current_diagnostic_ambient_injectivity"] == ({"scope": "orchestration fixture only"} if include_injectivity else None)
        assert result["current_complete_reference_face_measure"] == ({"scope": "whole-face orchestration fixture only"} if include_measure else None)


def injectivity_fixture(tmp_path):
    cases = source_cases()
    geometries, observations, timber = {}, {}, {}
    for i, row in enumerate(cases[0][1]["source_inputs"]["timber_rows"]):
        owner = row["name"]
        row.update(start=[10.*i, -3., 5.], axis=[0., .6, .8], end=[10.*i, 57., 85.])
        indices = (np.arange(24).reshape(4, 6)+24*i).tolist()
        timber[owner] = {"start": row["start"], "axis": row["axis"], "stations": [0., 17., 61., 100.],
                         "index": indices, "source": copy.deepcopy(row)}
        observation = {"id": owner, "source": {"path": owner+".brep", "sha256": "own-sha"},
                       "bounds_xyz_mm": [[10.*i-1., 10.*i+1.], [-4., 58.], [4., 86.]]}
        observations[owner] = observation
        box = SimpleNamespace(xmin=10.*i-1., xmax=10.*i+1., ymin=-4., ymax=58., zmin=4., zmax=86.)
        geometries[owner] = SimpleNamespace(owner_id=owner,
            source_identity={"finished_raw_file_path": owner+".brep", "finished_raw_file_sha256": "own-sha"},
            topology_sha256=owner+"-topology", shape=SimpleNamespace(BoundingBox=lambda own=box: own))
    pins, preflight = {}, {"case_sequence": domains.component.SEQUENCE, "cases": []}
    for i, (binding, field, _) in enumerate(cases):
        field["source_inputs"]["timber_rows"] = copy.deepcopy(cases[0][1]["source_inputs"]["timber_rows"])
        field["original_operator_fingerprint_sha256"] = f"own-operator-{i}"
        q = np.zeros(9350)
        for j, row in enumerate(timber.values()):
            q[row["index"][1][1]] = .002*(i+1)*(j+1)
            q[row["index"][2][3]] = .01*(i+1)*(j+1)
        field["response"] = {"q": q.tolist(), "q_canonical_sha256": domains.canonical_sha(q.tolist())}
        path = tmp_path/f"operator-{i}.json"
        bundle = {"original_operator_fingerprint_sha256": f"own-operator-{i}",
                  "coordinate_map": {"final_ndof": 9350, "rotation_scale": 1000., "timber": timber}}
        path.write_text(domains.json.dumps(bundle))
        source = {"path": path.name, "sha256": domains.current.sha(path)}
        field["operator_bundle"] = {"manifest": source}
        pins[path.name] = source["sha256"]
        preflight["cases"].append({**binding, "operator_manifest": source,
            "coordinate_ownership": {"first_order_ndof": 9350, "prospective_full_ndof": 9450}})
    return cases, geometries, observations, preflight, pins


@pytest.mark.parametrize("failure", [None, "foreign_source", "changed_end", "wrong_start", "duplicate_index", "negative_index", "unordered_stations"])
def test_current_timber_chart_keeps_world_storage_indices_and_oblique_grain(failure, tmp_path):
    cases, _, _, _, _ = injectivity_fixture(tmp_path)
    source = cases[0][1]["source_inputs"]["timber_rows"][3]
    bundle = domains.json.loads((tmp_path/"operator-0.json").read_bytes())
    row = bundle["coordinate_map"]["timber"][source["name"]]
    if failure == "foreign_source": row["source"]["name"] = "foreign"
    if failure == "changed_end": source["end"][2] += .1
    if failure == "wrong_start": row["start"][1] += 1.
    if failure == "duplicate_index": row["index"][1][0] = row["index"][0][0]
    if failure == "negative_index": row["index"][1][0] = -1
    if failure == "unordered_stations": row["stations"] = [100., 0.]
    if failure:
        with pytest.raises(ValueError): domains.timber_chart(row, source)
    else:
        result = domains.timber_chart(row, source)
        np.testing.assert_allclose(result["node_reference_centers_xyz_mm"], [[30., -3., 5.], [30., 7.2, 18.6], [30., 33.6, 53.8], [30., 57., 85.]], atol=1e-13)
        np.testing.assert_array_equal(result["node_dof_indices"], np.arange(72, 96).reshape(4, 6))
        assert result["reference_stations_mm"] == [0., 17., 61., 100.]
        np.testing.assert_array_equal(result["storage_basis_columns_xyz"], np.eye(3))
        assert result["reference_axis_xyz"] == [0., .6, .8]


@pytest.mark.parametrize("failure", [None, "wrong_owner", "wrong_source", "foreign_box", "flat_box"])
def test_ambient_extent_queries_own_solid_and_contains_full_padded_world_bounds(failure, tmp_path):
    _, geometries, observations, _, _ = injectivity_fixture(tmp_path)
    owner = "own-timber-04"
    geometry, observation = geometries[owner], observations[owner]
    if failure == "wrong_owner": geometry.owner_id = "foreign"
    if failure == "wrong_source": geometry.source_identity["finished_raw_file_sha256"] = "foreign"
    if failure == "foreign_box": observation["bounds_xyz_mm"][1][1] += 1.
    if failure == "flat_box":
        geometry.shape.BoundingBox = lambda: SimpleNamespace(xmin=40., xmax=40., ymin=-4., ymax=58., zmin=4., zmax=86.)
    if failure:
        with pytest.raises(ValueError): domains.ambient_extent(owner, geometry, observation)
    else:
        result = domains.ambient_extent(owner, geometry, observation)
        np.testing.assert_allclose(result["bounds_xyz_mm"], [[-61.000001, 141.000001], [-104.000001, 158.000001], [-96.000001, 186.000001]], atol=1e-12)
        assert result["source_identity"]["topology_sha256"] == owner+"-topology"
        assert result["source_identity"]["genuine_cached_solid_bounds_xyz_mm"] == observation["bounds_xyz_mm"]


@pytest.mark.parametrize("failure", [None, "one_inconclusive", "foreign_field", "foreign_operator", "old_full_ndof", "bad_saved_q", "foreign_bound_state", "foreign_bound_box", "shared_indices", "changed_chart"])
def test_all132_injectivity_checks_use_own_current_state_chart_box_and_full_map(monkeypatch, tmp_path, failure):
    cases, geometries, observations, preflight, pins = injectivity_fixture(tmp_path)
    monkeypatch.setattr(domains.current, "ROOT", tmp_path)
    if failure == "foreign_field": preflight["cases"][2]["field"] = preflight["cases"][1]["field"]
    if failure == "foreign_operator": preflight["cases"][2]["operator_manifest"] = preflight["cases"][1]["operator_manifest"]
    if failure == "old_full_ndof": preflight["cases"][3]["coordinate_ownership"]["prospective_full_ndof"] = 8088
    if failure == "bad_saved_q": cases[2][1]["response"]["q"][0] += 1.
    if failure in ["shared_indices", "changed_chart"]:
        for case_index in range(6) if failure == "shared_indices" else [2]:
            path = tmp_path/f"operator-{case_index}.json"
            bundle = domains.json.loads(path.read_bytes())
            rows = list(bundle["coordinate_map"]["timber"].values())
            if failure == "shared_indices": rows[1]["index"][1][1] = rows[0]["index"][1][1]
            else: rows[1]["stations"] = [0., 19., 61., 100.]
            path.write_text(domains.json.dumps(bundle))
            digest = domains.current.sha(path)
            cases[case_index][1]["operator_bundle"]["manifest"]["sha256"] = digest
            preflight["cases"][case_index]["operator_manifest"]["sha256"] = digest
            pins[path.name] = digest
    calls = []
    def bound(chart, q, *, owner_id, extent, comparison_padding):
        i, j = divmod(len(calls), 22)
        assert owner_id == f"own-timber-{j:02d}" and len(q) == 9450
        np.testing.assert_array_equal(q[:9350], cases[i][1]["response"]["q"])
        np.testing.assert_array_equal(q[9350:], np.zeros(100))
        assert chart["node_dof_indices"] == (np.arange(24).reshape(4, 6)+24*j).tolist()
        assert chart["reference_stations_mm"] == [0., 17., 61., 100.]
        np.testing.assert_allclose(chart["node_reference_centers_xyz_mm"], [[10.*j, -3., 5.], [10.*j, 7.2, 18.6], [10.*j, 33.6, 53.8], [10.*j, 57., 85.]], atol=1e-13)
        assert extent["source_identity"]["finished_raw_file_path"] == owner_id+".brep"
        assert comparison_padding == 1e-10
        # Interior-only displacement and rotation cannot be replaced by the
        # unchanged endpoints. This stub checks routing, not the frozen law.
        assert q[24*j+7] == .002*(i+1)*(j+1) and q[24*j+15] == .01*(i+1)*(j+1)
        value = abs(q[24*j+7]-q[24*j+1])/17.+comparison_padding
        if failure == "one_inconclusive" and (i, j) == (3, 7): value = 1.2
        calls.append((i, j, float(value)))
        return {"owner_id": owner_id, "row_canonical_sha256": domains.canonical_sha(chart),
                "q_canonical_sha256": "foreign" if failure == "foreign_bound_state" else domains.canonical_sha(q.tolist()),
                "extent_canonical_sha256": "foreign" if failure == "foreign_bound_box" else domains.canonical_sha(extent),
                "sufficient_global_one_to_one_criterion_met": bool(value < 1.), "padded_sufficient_L": value}
    args = (cases, geometries, observations, preflight, SimpleNamespace(sufficient_box_bound=bound), pins)
    if failure not in [None, "one_inconclusive"]:
        message = {"shared_indices": "current timber charts share source indices",
                   "changed_chart": "current timber charts differ between six own fields"}.get(failure)
        with pytest.raises(ValueError, match=message): domains.injectivity_checks(*args)
        if failure == "shared_indices": assert calls == []
        if failure == "changed_chart": assert len(calls) == 44 and all(i < 2 for i, _, _ in calls)
    else:
        result = domains.injectivity_checks(*args)
        assert len(calls) == result["bound_count"] == 132
        assert result["sufficient_count"] == (131 if failure else 132)
        assert result["all132_sufficient_on_own_ambient_box"] is (failure is None)
        assert result["maximum_padded_sufficient_L"] == (1.2 if failure else .264/17.+1e-10)
        assert result["reference_ndof"] == 9350 and result["full_ndof"] == 9450
        assert result["actual_inverse_or_target_image_membership_or_contact_query"] is False
        for i, row in enumerate(result["cases"]):
            binding = cases[i][0]
            assert all(row[k] == binding[k] for k in ["case_id", "state_id", "field"])
            assert row["operator_manifest"] == cases[i][1]["operator_bundle"]["manifest"]
            assert [b["owner_id"] for b in row["bounds"]] == list(geometries)


@pytest.mark.parametrize("failure", [None, "missing_face", "duplicate_feature", "foreign_owner", "foreign_source", "foreign_topology", "foreign_feature", "wrong_orientation", "void_sample"])
def test_full_face_measure_retains_all51_own_sources_cells_and_native_moments(failure):
    geometries, faces, native_faces = {}, [], {}
    for i in range(51):
        owner, ordinal = f"owner-{i % 22:02d}", i//22+1
        if owner not in geometries:
            geometries[owner] = SimpleNamespace(owner_id=owner, shape=object(),
                source_identity={"path": owner+".brep", "sha256": owner+"-sha"},
                topology_sha256=owner+"-topology", face_records=[])
        geometry = geometries[owner]
        feature = {"feature_id": f"{owner}/face-{ordinal}", "face_ordinal_1_based": ordinal}
        geometry.face_records.append(feature)
        saved = {"face_ordinal_1_based": ordinal, "signature_sha256": f"signature-{i}",
                 "signature": {"oriented_normal_xyz": [0., .6, .8]}}
        faces.append({"owner_id": owner, "source_geometry": copy.deepcopy(geometry.source_identity),
            "topology_sha256": geometry.topology_sha256, "closed_boundary_feature": copy.deepcopy(feature),
            "complete_planar_face": saved, "registered_opposing_owners": [f"opponent-{i}"],
            "registered_source_patch_ids": [f"patch-{i}"]})
        normal = SimpleNamespace(normalized=lambda: SimpleNamespace(toTuple=lambda: (0., .6, .8)))
        native_faces[(owner, ordinal)] = SimpleNamespace(fixture_index=i, normalAt=lambda n=normal: n,
            Area=lambda n=i: n+2., Center=lambda n=i: SimpleNamespace(toTuple=lambda: (2.*n, -3.*n, n+1.)))
    if failure == "missing_face": faces.pop()
    if failure == "duplicate_feature": faces[-1]["closed_boundary_feature"]["feature_id"] = faces[-2]["closed_boundary_feature"]["feature_id"]
    if failure == "foreign_owner": geometries["owner-00"].owner_id = "foreign"
    if failure == "foreign_source": faces[0]["source_geometry"]["sha256"] = "foreign"
    if failure == "foreign_topology": faces[0]["topology_sha256"] = "foreign"
    if failure == "foreign_feature": faces[0]["closed_boundary_feature"]["face_ordinal_1_based"] = 99
    if failure == "wrong_orientation": faces[0]["complete_planar_face"]["signature"]["oriented_normal_xyz"] = [0., -.6, -.8]
    selected, partitioned, moments_calls, progress = [], [], [], []
    expected_partitions, expected_attempts = {}, {}
    for i in range(51):
        center = np.array([2.*i, -3.*i, i+1.])
        fractions, offsets = ([.2, .3, .5], [-3., 2., 0.]) if i % 2 == 0 else ([1/3, 2/3], [-2., 1.])
        expected_partitions[i] = [{"point_xyz_mm": (center+[offset, 0., 0.]).tolist(),
            "area_mm2": (i+2.)*fraction, "reference_centroid_on_full_own_face": True,
            "own_inward_material_probe_occupied": True, "own_reference_face_distance_mm": (i+1.)*1e-13}
            for fraction, offset in zip(fractions, offsets, strict=True)]
        expected_attempts[i] = [{"refinement_level": level, "effective_cell_size_mm": 25./2**level,
            "cell_count": len(expected_partitions[i]), "void_or_own_probe_failures": int(level < (2 if i >= 49 else 0))}
            for level in range(3 if i >= 49 else 1)]
    def select(shape, locator, saved):
        i = len(selected); expected = faces[i]; owner = expected["owner_id"]
        assert shape is geometries[owner].shape and saved is expected["complete_planar_face"]
        assert locator == {"face_ordinal_1_based": i//22+1, "signature_sha256": f"signature-{i}"}
        selected.append(owner)
        return native_faces[(owner, i//22+1)]
    def cells(native, shape, normal, *, cell_size_mm, maximum_refinements):
        i = native.fixture_index
        assert shape is geometries[f"owner-{i % 22:02d}"].shape
        np.testing.assert_array_equal(normal, [0., .6, .8])
        assert cell_size_mm == 25. and maximum_refinements == 6
        partitioned.append(i)
        result = copy.deepcopy(expected_partitions[i])
        if failure == "void_sample": result[-1]["own_inward_material_probe_occupied"] = False
        return result, copy.deepcopy(expected_attempts[i])
    def second(native): return np.diag([native.fixture_index+1., 2., 3.])
    def moments(received, area, center, exact):
        i = len(moments_calls)
        assert area == i+2. and received == expected_partitions[i]
        assert sum(c["area_mm2"] for c in received) == pytest.approx(area)
        np.testing.assert_allclose(sum((c["area_mm2"]*np.array(c["point_xyz_mm"]) for c in received), np.zeros(3)), area*center, atol=1e-10)
        np.testing.assert_array_equal(center, [2.*i, -3.*i, i+1.])
        np.testing.assert_array_equal(exact, np.diag([i+1., 2., 3.]))
        moments_calls.append(i)
        return {"area_mm2": area, "second_moment_relative_frobenius_error": (i+1.)/1000.,
                "exact_second": exact.tolist(), "own_centroid": center.tolist()}
    method = SimpleNamespace(select_native_face=select, own_occupied_cells=cells,
        moment_report=moments, geometry=SimpleNamespace(centroidal_second_moments=second),
        OCCUPANCY_TOL_MM=1e-7, PROBE_DEPTH_MM=.05)
    if failure is not None:
        with pytest.raises(ValueError): domains.full_face_measure(geometries, faces, method)
        assert moments_calls == []
    else:
        result = domains.full_face_measure(geometries, faces, method, progress=progress.append)
        assert len(selected) == len(partitioned) == len(moments_calls) == len(progress) == 51
        assert result["area_cell_count"] == 128 and result["full_face_count"] == 51
        assert result["full_reference_area_mm2"] == sum(range(2, 53))
        assert result["maximum_second_moment_relative_frobenius_error"] == .051
        assert result["all51_complete_own_faces_measured_once"] is True
        assert result["opposing_body_clipping_or_occupancy_cell_discard_or_slave_selection"] is False
        assert result["geometry_measure_parameters"] == {"initial_cell_size_mm": 25., "maximum_whole_grid_refinements": 6,
            "minimum_divisions": 2, "numerical_cell_area_cutoff_mm2": 1e-8, "own_face_occupancy_tolerance_mm": 1e-7,
            "own_inward_probe_depth_mm": .05, "whole_face_area_absolute_tolerance_mm2": 1e-5,
            "whole_face_area_relative_tolerance": 1e-8, "whole_face_centroid_tolerance_mm": 1e-6}
        assert result["deformed_contact_measure_or_pressure_energy_convergence_qualified"] is False
        for i, (actual, source) in enumerate(zip(result["full_faces"], faces, strict=True)):
            assert actual["owner_id"] == source["owner_id"] and actual["feature_id"] == source["closed_boundary_feature"]["feature_id"]
            assert actual["source_geometry"] == source["source_geometry"] and actual["topology_sha256"] == source["topology_sha256"]
            assert actual["registered_opposing_owners"] == source["registered_opposing_owners"]
            assert actual["registered_source_patch_ids"] == source["registered_source_patch_ids"]
            assert actual["cell_count"] == len(actual["cells"]) == len(expected_partitions[i])
            assert [{k: v for k, v in c.items() if k != "id"} for c in actual["cells"]] == expected_partitions[i]
            assert [c["id"] for c in actual["cells"]] == [actual["feature_id"]+f"/full-area-cell-{j:06d}" for j in range(len(expected_partitions[i]))]
            assert actual["partition_attempts"] == expected_attempts[i]
            assert sum(c["area_mm2"] for c in actual["cells"]) == pytest.approx(i+2.)
            center = np.array([2.*i, -3.*i, i+1.])
            np.testing.assert_allclose(sum((c["area_mm2"]*np.array(c["point_xyz_mm"]) for c in actual["cells"]), np.zeros(3)), (i+2.)*center, atol=1e-10)
            assert actual["full_reference_face_moments"]["own_centroid"] == [2.*i, -3.*i, i+1.]
        assert len({c["id"] for r in result["full_faces"] for c in r["cells"]}) == 128


@pytest.mark.parametrize("failure", [None, "loaded_query", "tools", "conflicting_import_pin"])
def test_quadrature_execution_sources_include_imported_plan_output_and_mandatory_test_file(monkeypatch, tmp_path, failure):
    source = {"path": "query.py", "sha256": "query-sha"}
    monkeypatch.setattr(domains, "QUADRATURE", source)
    monkeypatch.setattr(domains.current, "ROOT", tmp_path)
    method = SimpleNamespace(LOADED_SHA="query-sha", PLAN_SOURCE="plan.py", PLAN_SOURCE_SHA="plan-sha",
        PLAN_OUTPUT="plan.json", PLAN_SHA="plan-output-sha", TEST=tmp_path/"test_query.py", LOADED_TEST_SHA="test-sha",
        INITIAL_PINS={"imported-library.py": "library-sha"}, EXPECTED_VERSIONS={"native": "pinned"}, versions=lambda: {"native": "pinned"})
    if failure == "loaded_query": method.LOADED_SHA = "foreign"
    if failure == "tools": method.versions = lambda: {"native": "foreign"}
    if failure == "conflicting_import_pin": method.INITIAL_PINS["plan.py"] = "foreign"
    if failure:
        with pytest.raises(ValueError): domains.quadrature_sources(method)
    else:
        assert domains.quadrature_sources(method) == {"query.py": "query-sha", "plan.py": "plan-sha",
            "plan.json": "plan-output-sha", "test_query.py": "test-sha", "imported-library.py": "library-sha"}
