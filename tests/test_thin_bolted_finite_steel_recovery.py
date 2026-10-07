"""Current points/directors/couples and reference material-cut recovery fixtures."""

import copy
from types import SimpleNamespace

import numpy as np
import pytest
from scipy.spatial.transform import Rotation

from scripts import thin_bolted_finite_steel_recovery as recovery

STATE = {"state_id": "finite-one", "case_id": "load", "accessory_placement": "rear"}


def pose(mapping, body, point, q, *, flange=None, reference_director=None):
    r = np.array(mapping.get("test_rotation", np.eye(3)))
    t = np.array(mapping.get("test_translation", [0., 0., 0.]))
    return {"position_xyz_mm": r @ point+t,
            "current_vector_xyz": r @ reference_director if reference_director is not None else None}


def fixture(gravity=False):
    shaft = {"axis_id": "one", "body": "shaft/one", "point": [0., 0., 0.], "basis": np.eye(3).tolist(),
        "diameter_mm": 10., "shaft_interval_mm": [0., 10.], "metal_roles": []}
    loads = []
    if gravity:
        role = {"id": "head/one", "center_of_mass_xyz_mm": [-2., 1., 0.], "volume_mm3": 1/(7850e-9*9.80665)}
        shaft["metal_roles"] = [role]
        loads = [{**STATE, "id": "physical-bolt-metal/head/one", "source_load_id": "physical-bolt-metal/head/one",
            "body": "shaft/one", "reference_point_xyz_mm": [-2., 1., 0.], "current_point_xyz_mm": [-2., 1., 0.],
            "force_xyz_n": [0., 0., -1.], "free_spatial_moment_xyz_nmm": [0., 0., 0.]}]
    export = {**STATE, "parameters": {"shaft_diameter_scale": 1.},
        "finite_kinematic_map": {"ndof": 1, "mechanical_bodies": {"shaft/one": {"reference_stations_mm": [0., 10.]}}},
        "finite_body_applied_loads": loads, "finite_interaction_actions": [{**STATE, "id": "one/bearing-0-0",
            "kind": "common_shaft_bearing", "first": "shaft/one", "second": "wood", "reference_first_point_xyz_mm": [3., 0., 0.],
            "point_on_first_xyz_mm": [3., 0., 0.], "force_on_first_xyz_n": [0., 2., 0.],
            "moment_on_first_at_current_point_xyz_nmm": [5., 0., 0.]}]}
    return export, [shaft]


def test_current_cut_retains_head_role_gravity_outside_beam_and_full_free_couple():
    export, specs = fixture(True)
    cuts = recovery.current_shaft_cuts(export, [0.], specs, pose=pose)[0]["cuts"]
    root = cuts[0]
    assert root["local_N_V1_V2_T_M1_M2_n_nmm"] == pytest.approx([0., 0., 1., 1., 2., 0.])
    witness = next(cut for cut in cuts if cut["station_from_axis_point_mm"] == 5.)
    assert witness["local_N_V1_V2_T_M1_M2_n_nmm"] == pytest.approx([0., -2., 1., -4., 7., 4.])
    assert root["lower_material_part_physical_load_ids"] == ["physical-bolt-metal/head/one"]


def test_current_cut_rigid_covariance_uses_reference_material_load_order():
    export, specs = fixture()
    original = recovery.current_shaft_cuts(export, [0.], specs, pose=pose)[0]["cuts"]
    r = Rotation.from_rotvec([0., 0., 2.5]).as_matrix()
    t = np.array([90., -30., 50.])
    export["finite_kinematic_map"].update(test_rotation=r.tolist(), test_translation=t.tolist())
    action = export["finite_interaction_actions"][0]
    for key in ("force_on_first_xyz_n", "moment_on_first_at_current_point_xyz_nmm"):
        action[key] = (r @ action[key]).tolist()
    action["point_on_first_xyz_mm"] = (r @ [3., 0., 0.]+t).tolist()
    rotated = recovery.current_shaft_cuts(export, [0.], specs, pose=pose)[0]["cuts"]
    for first, second in zip(original, rotated, strict=True):
        assert second["local_N_V1_V2_T_M1_M2_n_nmm"] == pytest.approx(first["local_N_V1_V2_T_M1_M2_n_nmm"], abs=2e-12)
        assert second["point_xyz_mm"] == pytest.approx(r @ first["point_xyz_mm"]+t)
    assert rotated[0]["lower_material_part_physical_load_ids"] == []


def test_actual_frozen_map_recovery_uses_bent_centers_and_current_geodesic_directors():
    export, specs = fixture()
    mapping = {"ndof": 12, "panels": {}, "mechanical_bodies": {"shaft/one": {
        "kind": "shaft", "reference_stations_mm": [0., 10.],
        "reference_start_xyz_mm": [0., 0., 0.], "reference_axis_xyz": [1., 0., 0.],
        "node_reference_centers_xyz_mm": [[0., 0., 0.], [10., 0., 0.]],
        "node_dof_indices": np.arange(12).reshape(2, 6).tolist(), "storage_basis_columns_xyz": np.eye(3).tolist()}}}
    q = np.zeros(12)
    q[7], q[11] = 4., 1000*np.pi/3
    export["finite_kinematic_map"] = mapping
    action = export["finite_interaction_actions"][0]
    action["point_on_first_xyz_mm"] = recovery.current_pose(mapping, "shaft/one", [3., 0., 0.], q)["position_xyz_mm"].tolist()
    cuts = recovery.current_shaft_cuts(export, q, specs)[0]["cuts"]
    witness = next(cut for cut in cuts if cut["station_from_axis_point_mm"] == 5.)
    assert witness["point_xyz_mm"] == pytest.approx([5., 2., 0.])
    assert witness["current_basis_axis_tangent1_tangent2_xyz"] == pytest.approx(
        np.array([[np.sqrt(3)/2, .5, 0.], [-.5, np.sqrt(3)/2, 0.], [0., 0., 1.]]))
    assert witness["local_N_V1_V2_T_M1_M2_n_nmm"] == pytest.approx(
        [-1., -np.sqrt(3), 0., -5*np.sqrt(3)/2, 2.5, 4.])


def test_response_coordinate_binding_rejects_another_finite_state():
    export, _ = fixture()
    export["response"] = {"q": [0.]}
    assert recovery.mapped_state(export, [0.]).tolist() == [0.]
    with pytest.raises(ValueError, match="differ"):
        recovery.mapped_state(export, [1e-12])


@pytest.mark.parametrize("mutation", ["missing", "force", "current-point", "role", "reference-point"])
def test_exact_own_gravity_role_or_current_arm_mutations_reject(mutation):
    export, specs = fixture(True)
    row = export["finite_body_applied_loads"][0]
    if mutation == "missing":
        export["finite_body_applied_loads"] = []
    elif mutation == "force":
        row["force_xyz_n"][2] = -2.
    elif mutation == "current-point":
        row["current_point_xyz_mm"][0] += 1.
    elif mutation == "role":
        row["source_load_id"] = "another-role"
    else:
        row["reference_point_xyz_mm"][0] += 1.
    with pytest.raises(ValueError):
        recovery.current_metal_gravity(export, [0.], specs, pose=pose)


def test_actual_finite_producer_serializer_preserves_director_spatial_couple():
    from scripts.thin_bolted_finite_frame import FiniteFramePotential

    descriptor = {"id": "capture", "kind": "shaft_end_capture", "first": "shaft/one", "second": "angle",
        "director_owner": "angle", "source_descriptor": {"axis_id": "one", "end": {"end": "head", "washer_id": "washer-one"}}}
    row = FiniteFramePotential.interaction_action(SimpleNamespace(case=STATE), descriptor,
        {"position_xyz_mm": np.array([1., 2., 3.])}, {"position_xyz_mm": np.array([2., 2., 3.])}, {"value_xyz": [1., 0., 0.]},
        {"moment_on_director_owner_xyz_nmm": np.array([0., 3., 4.]), "force_on_first_xyz_n": np.array([5., 0., 0.]),
         "force_on_second_xyz_n": np.array([-5., 0., 0.]), "pair_spatial_moment_residual_nmm": np.array([0., 3., 4.]),
         "signed_axial_extension_mm": .5, "radial_distance_mm": 0., "axial_scalar_force_n": 5., "energy_nmm": 1.25})
    assert row["moment_on_second_at_current_point_xyz_nmm"] == [0., 3., 4.]
    capture = recovery.current_own_washer_captures({**STATE, "finite_interaction_actions": [row]})[0]
    assert capture["own_capture_model_axial_force_n"] == 5.
    assert capture["model_spatial_couple_on_host_at_support_point_nmm"] == [0., 3., 4.]
    assert capture["director_model_couple_is_actual_washer_pressure_prying_or_capacity"] is False


@pytest.mark.parametrize("mutation", ["missing-state", "case", "duplicate"])
def test_mixed_or_duplicate_finite_physical_rows_reject(mutation):
    export, _ = fixture()
    row = export["finite_interaction_actions"][0]
    if mutation == "missing-state":
        row.pop("state_id")
    elif mutation == "case":
        row["case_id"] = "other"
    else:
        export["finite_interaction_actions"].append(copy.deepcopy(row))
    with pytest.raises(ValueError):
        recovery.validate_labels(export)


def port_fixture():
    entry = [84.1375, 0., 0.]
    layout = {"installed_axes": [{"id": "one", "attachments": [{"angle_id": "B104ZN_test", "flange": "beam",
        "receiver": "wood", "entry_xyz_mm": entry}]}], "raw_fittings": [{"angle_id": "B104ZN_test",
        "origin_xyz_mm": [0., 0., 0.], "u_xyz": [1., 0., 0.], "v_xyz": [0., 1., 0.], "w_xyz": [0., 0., 1.]}]}
    actions = []
    for index, y, force, moment in ((0, -2., [0., 0., 4.], [1., 0., 2.]), (1, -1., [0., 0., 6.], [2., 0., 3.])):
        actions.append({**STATE, "id": f"bearing-{index}", "kind": "common_shaft_bearing", "first": "shaft/one", "second": "B104ZN_test",
            "source_descriptor": {"axis_id": "one", "surface": {"kind": "steel", "flange": "beam"}},
            "point_on_second_xyz_mm": [entry[0], y, 0.], "force_on_second_xyz_n": force,
            "moment_on_second_at_current_point_xyz_nmm": moment})
    actions.append({**STATE, "id": "capture", "kind": "shaft_end_capture", "first": "shaft/one", "second": "B104ZN_test",
        "source_descriptor": {"axis_id": "one", "end": {"end": "head", "flange": "beam"}},
        "point_on_second_xyz_mm": [entry[0], -3., 0.], "force_on_second_xyz_n": [0., 20., 0.],
        "moment_on_second_at_current_point_xyz_nmm": [0., 7., 0.]})
    return {**STATE, "finite_interaction_actions": actions, "finite_kinematic_map": {}}, layout


def test_current_steel_entry_transport_retains_full_director_couple_and_rigid_covariance():
    export, layout = port_fixture()
    original = recovery.current_steel_ports(export, [], layout, pose=pose)[0]
    assert original["force_on_steel_xyz_n"] == pytest.approx([0., 20., 10.])
    assert original["moment_on_steel_at_point_xyz_nmm"] == pytest.approx([-11., 7., 5.])
    r = Rotation.from_rotvec([.3, -.4, .6]).as_matrix()
    t = np.array([35., 46., -21.])
    export["finite_kinematic_map"].update(test_rotation=r.tolist(), test_translation=t.tolist())
    for row in export["finite_interaction_actions"]:
        row["point_on_second_xyz_mm"] = (r @ row["point_on_second_xyz_mm"]+t).tolist()
        for key in ("force_on_second_xyz_n", "moment_on_second_at_current_point_xyz_nmm"):
            row[key] = (r @ row[key]).tolist()
    transformed = recovery.current_steel_ports(export, [], layout, pose=pose)[0]
    assert transformed["point_xyz_mm"] == pytest.approx(r @ original["point_xyz_mm"]+t)
    assert transformed["moment_on_steel_at_point_xyz_nmm"] == pytest.approx(r @ original["moment_on_steel_at_point_xyz_nmm"])
    assert layout["installed_axes"][0]["attachments"][0]["entry_xyz_mm"] == [84.1375, 0., 0.]


def test_current_fitting_cut_basis_preserves_local_full_actions_under_rigid_rotation():
    export, layout = port_fixture()
    ports = recovery.current_steel_ports(export, [], layout, pose=pose)
    original = recovery.current_flange_sections(export, [], layout, ports, pose=pose)[0]
    r = Rotation.from_rotvec([.3, -.4, .6]).as_matrix()
    t = np.array([35., 46., -21.])
    export["finite_kinematic_map"].update(test_rotation=r.tolist(), test_translation=t.tolist())
    for row in export["finite_interaction_actions"]:
        row["point_on_second_xyz_mm"] = (r @ row["point_on_second_xyz_mm"]+t).tolist()
        for key in ("force_on_second_xyz_n", "moment_on_second_at_current_point_xyz_nmm"):
            row[key] = (r @ row[key]).tolist()
    transformed_ports = recovery.current_steel_ports(export, [], layout, pose=pose)
    transformed = recovery.current_flange_sections(export, [], layout, transformed_ports, pose=pose)[0]
    first, second = original["sections"][0], transformed["sections"][0]
    assert second["force_local_n"] == pytest.approx(first["force_local_n"], abs=1e-12)
    assert second["moment_local_nmm"] == pytest.approx(first["moment_local_nmm"], abs=3e-12)
    assert second["current_point_xyz_mm"] == pytest.approx(r @ first["current_point_xyz_mm"]+t)
    assert second["gross_rectangle_torsion_bound"]["simultaneous_nominal_vm_bound_mpa"] == pytest.approx(
        first["gross_rectangle_torsion_bound"]["simultaneous_nominal_vm_bound_mpa"])
    assert transformed["opposed_flange_same_rigid_pose_assumed"] is False


def test_fitting_mean_load_port_exact_derivative_uses_two_distinct_current_flange_points():
    mapping = {"ndof": 12, "panels": {}, "mechanical_bodies": {"angle": {"kind": "fitting",
        "node_reference_centers_xyz_mm": [[0., 0., 0.], [0., 0., 0.]],
        "node_dof_indices": np.arange(12).reshape(2, 6).tolist(), "storage_basis_columns_xyz": np.eye(3).tolist(),
        "flange_node_map": {"beam": 0, "post": 1}, "gravity_port": "mean of two exact flange rigid-arm ports"}}}
    q = np.zeros(12)
    q[0], q[7], q[5] = 1., 2., 1000*np.pi/6
    reference, force = np.array([3., 4., 0.]), np.array([0., 0., -10.])
    mean = recovery.current_pose(mapping, "angle", reference, q)["position_xyz_mm"]
    export = {"finite_kinematic_map": mapping, "finite_body_applied_loads": [{"id": "angle-gravity", "body": "angle",
        "source_load_id": "angle-gravity", "reference_point_xyz_mm": reference.tolist(), "current_point_xyz_mm": mean.tolist(),
        "force_xyz_n": force.tolist(), "free_spatial_moment_xyz_nmm": [0., 0., 0.]}]}
    beam, post = [recovery.fitting_source_leg_loads(export, q, "angle", flange)[0] for flange in ("beam", "post")]
    assert beam["point_xyz_mm"] == pytest.approx([1+3*np.sqrt(3)/2-2, 1.5+2*np.sqrt(3), 0.])
    assert post["point_xyz_mm"] == pytest.approx([3., 6., 0.])
    parts = [recovery.common.transport_wrench(row["force_on_steel_xyz_n"], row["moment_on_steel_at_point_xyz_nmm"],
                                             row["point_xyz_mm"], [0., 0., 0.]) for row in (beam, post)]
    assert parts[0][0]+parts[1][0] == pytest.approx(force)
    assert parts[0][1]+parts[1][1] == pytest.approx(np.cross(mean, force))
    assert beam["source_load_id"] == "angle-gravity"
    assert beam["assumed_physical_gravity_equal_sharing"] is False


def test_fitting_leg_section_includes_own_mean_port_gravity_derivative():
    export, layout = port_fixture()
    export["finite_kinematic_map"] = {"mechanical_bodies": {"B104ZN_test": {"gravity_port": "mean of two exact flange rigid-arm ports"}}}
    export["finite_body_applied_loads"] = [{"id": "angle-gravity", "source_load_id": "angle-gravity", "body": "B104ZN_test",
        "reference_point_xyz_mm": [50., 0., 0.], "current_point_xyz_mm": [50., 0., 0.],
        "force_xyz_n": [0., 0., -10.], "free_spatial_moment_xyz_nmm": [0., 0., 0.]}]
    ports = recovery.current_steel_ports(export, [], layout, pose=pose)
    sections = recovery.current_flange_sections(export, [], layout, ports, pose=pose)[0]
    assert sections["sections"][0]["force_local_n"] == pytest.approx([0., 5., -20.])
    assert sections["external_current_point_actions_on_steel"][-1]["source_load_id"] == "angle-gravity"
