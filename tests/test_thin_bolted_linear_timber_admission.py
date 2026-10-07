"""Changed face/map seam only; no response, K/CAD or candidate admission run.

Frozen source geometry is reused. Test vectors and recovered face rows are
synthetic; existing common132-body/source/floor proof is not rerun or stubbed
into a claimed candidate result.
"""

import copy
import json

import numpy as np
import pytest

from scripts import thin_bolted_linear_timber_admission as gate


@pytest.fixture(scope="module")
def sources():
    gate.source_pins()
    cache = json.loads(gate.support.CACHE_PATH.read_bytes())
    proof = json.loads(gate.proof_method.PROOF.read_bytes())
    geometry = gate.spans.read_member_span_geometry()
    return cache, proof, geometry


def fixture(sources, *, translation=0.):
    cache, proof, geometry = sources
    mapping = gate.expected_timber_map(cache, 150., 8000, geometry)
    q = np.zeros(8000)
    patch = proof["patches"][0]
    normal = np.asarray(patch["normal_from_second_to_first_xyz"])
    first = next(r for r in mapping["members"] if r["member"] == patch["first"])
    q[np.asarray(first["node_dof_indices"])[:, :3]] = -translation*normal
    params = {"beam_size_mm": 150., "linear_timber_face_contact_basis": gate.BASIS,
        "linear_timber_face_contact_bedding_n_mm3": 1., "linear_timber_face_contact_scenario_id": "synthetic-declared",
        "linear_timber_face_contact_geometry_sha256": gate.proof_method.PROOF_SHA256,
        "linear_timber_face_contact_cell_mm": proof["method"]["cell_size_mm"]}
    identity = {"state_id": "synthetic", "case_id": "a12-rear", "accessory_placement": "retained-original-top-hold"}
    expected = gate.proof_method.expected_contact_descriptors(proof, 1., "synthetic-declared")
    rows = []
    for descriptor in expected.values():
        point, normal = descriptor["reference_first_point_xyz_mm"], np.asarray(descriptor["reference_director_xyz"])
        closure = -normal @ (gate.point_displacement(mapping, descriptor["first"], point, q)
                            -gate.point_displacement(mapping, descriptor["second"], point, q))
        force = descriptor["axial_stiffness_n_mm"]*max(closure, 0.)
        rows.append({**identity, "id": descriptor["id"], "kind": "timber_face_contact",
            "first": descriptor["first"], "second": descriptor["second"], "point_xyz_mm": copy.deepcopy(point),
            "direction_xyz": normal.tolist(), "source_descriptor": copy.deepcopy(descriptor["source_descriptor"]),
            "relative_closure_mm": float(closure), "compression_n": float(force),
            "penalty_stiffness_n_mm": descriptor["axial_stiffness_n_mm"],
            "cell_area_mm2": descriptor["source_descriptor"]["cell_area_mm2"],
            "force_on_first_xyz_n": (force*normal).tolist(), "force_on_second_xyz_n": (-force*normal).tolist(),
            "moment_at_point_model_xyz_nmm": [0.]*3, "moment_on_first_at_point_xyz_nmm": [0.]*3,
            "moment_on_second_at_point_xyz_nmm": [0.]*3,
            "action_wrench_uses_reference_point_first_order": True, "physical_pressure_or_current_overlap_resolved": False})
    return {**identity, "parameters": params, "linear_timber_face_method": gate.BASIS,
        "linear_timber_coordinate_map": mapping, "counts": {"dofs": 8000}, "response": {"q": q.tolist()},
        "contact_actions": rows, "timber_face_contact_actions": copy.deepcopy(rows)}, patch


@pytest.mark.parametrize("translation", [0., .002, -.002])
def test_all272_zero_closed_and_open_source_cells_replay_original_linear_law(sources, translation):
    cache, proof, geometry = sources
    field, patch = fixture(sources, translation=translation)
    mapping, q = gate.verify_timber_map(field, cache, geometry)
    result = gate.verify_face_actions(field, proof, mapping, q)
    own = [r for r in field["contact_actions"] if r["source_descriptor"]["patch_id"] == patch["id"]]
    assert sum(r["compression_n"] for r in own) == pytest.approx(patch["area_mm2"]*max(translation, 0.))
    assert result["face_cell_count"] == 272 and result["retained_pair_count"] == 6
    assert not result["current_overlap_pressure_or_capacity_established"]


def test_linear_off_axis_port_known_translation_rotation_and_interpolation():
    mapping = {"members": [{"member": "coupon", "reference_start_xyz_mm": [0., 0., 0.],
        "reference_axis_xyz": [1., 0., 0.], "reference_stations_mm": [0., 100.],
        "node_dof_indices": np.arange(12).reshape(2, 6).tolist()}]}
    q = np.zeros(12); q[:3] = [1., 2., 3.]; q[6:9] = [3., 4., 5.]
    q[3:6] = q[9:12] = [0., 0., 10.]
    # Midspan translation[2,3,4] plus theta_z=.01 crossed with arm[0,20,0].
    np.testing.assert_allclose(gate.point_displacement(mapping, "coupon", [50., 20., 0.], q), [1.8, 3., 4.])


@pytest.mark.parametrize("mutation", ["missing", "order", "indices", "basis", "start", "axis", "stations",
                                      "center", "scale", "dimension", "nonfinite_q"])
def test_changed_timber_coordinate_map_rejects(sources, mutation):
    cache, _, geometry = sources
    field, _ = fixture(sources); mapping = field["linear_timber_coordinate_map"]
    row = mapping["members"][0]
    if mutation == "missing":
        mapping["members"].pop()
    elif mutation == "order":
        mapping["members"][:2] = mapping["members"][1::-1]
    elif mutation == "indices":
        row["node_dof_indices"][1][3:5] = row["node_dof_indices"][1][4:2:-1]
    elif mutation == "basis":
        row["storage_basis_columns_xyz"][0][0] = -1.
    elif mutation in ("start", "axis", "stations", "center"):
        key = {"start": "reference_start_xyz_mm", "axis": "reference_axis_xyz",
               "stations": "reference_stations_mm", "center": "node_reference_centers_xyz_mm"}[mutation]
        if mutation == "center":
            row[key][0][0] += .01
        else:
            row[key][0] += .01
    elif mutation == "scale":
        mapping["rotation_scale"] = 1.
    elif mutation == "dimension":
        mapping["ndof"] -= 1
    else:
        field["response"]["q"][0] = float("nan")
    with pytest.raises(ValueError):
        gate.verify_timber_map(field, cache, geometry)


@pytest.mark.parametrize("mutation", ["missing", "duplicate", "alias", "host", "normal", "point", "area",
    "stiffness", "closure", "force", "dual", "couple", "source", "state", "proof", "grid", "basis", "bedding"])
def test_added_face_source_law_census_and_state_mutations_reject(sources, mutation):
    _, proof, _ = sources
    field, _ = fixture(sources, translation=.002)
    row = field["contact_actions"][0]
    if mutation == "missing":
        field["contact_actions"].pop()
    elif mutation == "duplicate":
        field["contact_actions"][-1] = copy.deepcopy(row)
    elif mutation == "alias":
        field["timber_face_contact_actions"].pop()
    elif mutation == "host":
        row["second"] = "foreign"
    elif mutation in ("normal", "point", "force", "dual", "couple"):
        key = {"normal": "direction_xyz", "point": "point_xyz_mm", "force": "force_on_first_xyz_n",
               "dual": "force_on_second_xyz_n", "couple": "moment_on_second_at_point_xyz_nmm"}[mutation]
        row[key][0] += 1.
    elif mutation in ("area", "stiffness", "closure"):
        row[{"area": "cell_area_mm2", "stiffness": "penalty_stiffness_n_mm", "closure": "relative_closure_mm"}[mutation]] += 1.
    elif mutation == "source":
        row["source_descriptor"]["geometry_proof_sha256"] = "0"*64
    elif mutation == "state":
        row["state_id"] = "other"
    else:
        key = {"proof": "geometry_sha256", "grid": "cell_mm", "basis": "basis", "bedding": "bedding_n_mm3"}[mutation]
        field["parameters"]["linear_timber_face_contact_"+key] = "other" if mutation in ("proof", "basis") else -1.
    # Except for the explicit alias test, mutate both aliases consistently so
    # rejection proves the independent source/law guard, not alias inequality.
    if mutation != "alias":
        field["timber_face_contact_actions"] = copy.deepcopy(field["contact_actions"])
    with pytest.raises(ValueError):
        gate.verify_face_actions(field, proof, field["linear_timber_coordinate_map"], np.asarray(field["response"]["q"]))


def census_fixture(sources):
    field, _ = fixture(sources)
    identity = {k: field[k] for k in gate.IDENTITIES}
    panel = gate.panel_contact_sources()
    field["parameters"].update(panel_intervals=8, foundation_port_cell_mm=70.)
    field["contact_actions"].extend({**identity, "id": name, "kind": "panel_contact", **copy.deepcopy(row),
        "compression_n": 0., "force_on_first_xyz_n": [0.]*3} for name, row in panel.items())
    field["contact_actions"].extend({**identity, "id": f"synthetic-flange/{i}", "kind": "flange_contact"} for i in range(288))
    for name, count in (("panel_screw_actions", 66), ("common_shaft_bearing_actions", 308),
                         ("shaft_end_capture_actions", 140), ("common_shaft_wood_bearing_actions", 82),
                         ("common_shaft_steel_port_actions", 72), ("common_shaft_section_cut_actions", 70)):
        field[name] = [{**identity, "id": f"{name}/{i}", "axis_id": f"synthetic-axis-{i}",
            "surface_index": i, "angle_id": f"synthetic-angle-{i}", "flange": "beam"} for i in range(count)]
    field["floor_actions"] = [{"id": f"synthetic-floor/{i}", "kind": "floor_normal"} for i in range(32)]
    field["body_identities"] = [f"synthetic-host/{i}" for i in range(62)]+[f"shaft/synthetic-{i}" for i in range(70)]
    field["counts"].update(normal_contacts=1262, timber_members=20, finite_fittings=36, flexible_panels=6,
        physical_bolt_axes=70, physical_shaft_bodies=70, structural_bodies=132, panel_screw_axes=66,
        finished_wood_bearing_spans=82, steel_bore_spans=72, radial_bearing_quadrature_ports=308,
        own_axial_end_captures=140, independent_lumped_frame_bolt_ports=0,
        paired_timber_interfaces=6, paired_timber_compression_cells=272)
    return field, panel


def test_complete_source_contact_census_and_zero_panel_rows(sources):
    field, panels = census_fixture(sources)
    receipt = gate.verify_action_census(field, panels)
    assert receipt["normal_contact_count"] == 1262 and receipt["contact_action_count"] == 1090
    assert receipt["panel_contact_count"] == 530
    assert receipt["unchanged_panel_contact_q_law_independently_replayed"] is False


@pytest.mark.parametrize("mutation", ["unknown", "missing_panel", "duplicate_panel", "count", "panel_owner",
                                      "panel_point", "panel_force", "aggregate", "aggregate_state"])
def test_foreign_missing_or_false_complete_contact_census_rejects(sources, mutation):
    field, panels = census_fixture(sources)
    panel = next(r for r in field["contact_actions"] if r["kind"] == "panel_contact")
    if mutation == "unknown":
        panel["kind"] = "invented_constraint"
    elif mutation == "missing_panel":
        field["contact_actions"].remove(panel)
    elif mutation == "duplicate_panel":
        other = next(r for r in field["contact_actions"] if r["kind"] == "panel_contact" and r["id"] != panel["id"])
        other["id"] = panel["id"]
    elif mutation == "count":
        field["counts"]["normal_contacts"] -= 1
    elif mutation == "panel_owner":
        panel["second"] = "foreign"
    elif mutation == "panel_point":
        panel["point_xyz_mm"][0] += 1.
    elif mutation == "panel_force":
        panel["force_on_first_xyz_n"][0] = 1.
    elif mutation == "aggregate":
        field["common_shaft_wood_bearing_actions"].pop()
    else:
        field["common_shaft_steel_port_actions"][0]["state_id"] = "old"
    with pytest.raises(ValueError):
        gate.verify_action_census(field, panels)


def test_unissued_extension_cannot_admit_any_production_field(monkeypatch):
    monkeypatch.setattr(gate, "METHOD_SHA256", "UNISSUED")
    with pytest.raises(ValueError, match="must be frozen"):
        gate.audit_linear_timber_state({})
