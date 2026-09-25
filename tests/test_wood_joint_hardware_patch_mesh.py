"""Focused contracts for the WJ04 physical-hardware geometry mesher."""

from __future__ import annotations

import copy
import json
import math
import shutil

import pytest

from fea import wood_joint_hardware_patch_mesh as hardware_mesh
from fea import wood_joint_patch_mesh as wood_mesh

BUNDLE = (
    hardware_mesh.ROOT
    / "fea/results/diagnostics/wj04-mechanics-hardware-v1"
)


def _inventory() -> dict:
    return json.loads((BUNDLE / "inventory.json").read_text())


def _profile() -> tuple[dict, dict, dict]:
    inventory = _inventory()
    scenario = next(
        row
        for row in inventory["scenarios"]
        if row["scenario_id"] == "body_to_far_wood_face"
    )
    stack = next(row for row in scenario["stacks"] if row["stack_spec_id"] == "lower_rail_1")
    geometry = {
        **inventory["selected_hardware_geometry"],
        "thread_and_gage_mapping": inventory["thread_and_gage_mapping"],
    }
    return inventory, stack, geometry


def _probes(points, normals):
    return [
        {"xyz_mm": list(point), "normal_global": list(normal)}
        for point, normal in zip(points, normals, strict=True)
    ]


def _cylinder_probe_grid(radius, stations):
    points, normals = [], []
    for index in range(9):
        angle = 2 * math.pi * index / 9
        points.append((radius * math.cos(angle), radius * math.sin(angle), stations[index % len(stations)]))
        normals.append((math.cos(angle), math.sin(angle), 0.0))
    return _probes(points, normals)


def _plane_probe_grid(station, normal):
    points = []
    for index in range(9):
        angle = 2 * math.pi * index / 9
        radius = 4.0 + index / 10
        points.append((radius * math.cos(angle), radius * math.sin(angle), station))
    return _probes(points, [normal] * 9)


def test_archive_pins_both_profiles_and_keeps_physical_solids_separate_from_legacy_roles():
    normal = hardware_mesh.load_hardware_bundle(BUNDLE, "body_to_far_wood_face")
    sensitivity = hardware_mesh.load_hardware_bundle(BUNDLE, "Lb_boundary_root_sensitivity")

    assert normal["inventory_sha256"] == hardware_mesh.HARDWARE_INVENTORY_SHA256
    assert normal["hash_index_sha256"] == hardware_mesh.HARDWARE_HASH_INDEX_SHA256
    assert len(normal["stacks"]) == len(sensitivity["stacks"]) == 8
    assert len(normal["input_file_sha256"]) == 67
    assert len(hardware_mesh._expected_bundle_files()) == 66
    assert len(normal["scenario"]["stacks"]) * len(hardware_mesh.COMPONENT_ROLES) == 32
    assert len(normal["inventory"]["legacy_collision_role_metadata"]) == 40
    assert normal["scenario"]["scenario_id"] != sensitivity["scenario"]["scenario_id"]
    for stack_id, stack in normal["stacks"].items():
        assert set(stack["component_solids"]) == set(hardware_mesh.COMPONENT_ROLES)
        assert tuple(row["member_id"] for row in stack["receivers_head_to_nut"]) == (
            hardware_mesh.EXPECTED_RECEIVERS[stack_id]
        )
        for role in hardware_mesh.COMPONENT_ROLES:
            assert stack["component_solids"][role]["solid_count"] == 1


@pytest.mark.parametrize(
    ("mutate", "message"),
    [
        (
            lambda inventory: inventory["scenarios"][0]["stacks"].pop(),
            "expected exactly eight physical bolt stacks",
        ),
        (
            lambda inventory: inventory["scenarios"][0]["stacks"][0]["component_solids"].pop("nut"),
            "expected four separate physical solids",
        ),
        (
            lambda inventory: inventory["legacy_collision_role_metadata"].pop(),
            "forty nonphysical records",
        ),
        (
            lambda inventory: inventory["scenarios"][0]["stacks"][0].__setitem__(
                "wood_or_washer_tie_assigned", True
            ),
            "grip or no-tie contract changed",
        ),
    ],
)
def test_inventory_contract_fails_closed_on_physical_identity_or_role_changes(mutate, message):
    inventory = copy.deepcopy(_inventory())
    mutate(inventory)

    with pytest.raises((TypeError, ValueError), match=message):
        hardware_mesh._validate_inventory_contract(inventory)


@pytest.mark.parametrize(
    ("scenario", "expected_transition"),
    [("body_to_far_wood_face", 129.032), ("Lb_boundary_root_sensitivity", 127.0)],
)
def test_profile_keeps_named_transition_and_metal_solid_count_distinct(scenario, expected_transition):
    loaded = hardware_mesh.load_hardware_bundle(BUNDLE, scenario)
    stack = loaded["stacks"]["lower_rail_1"]

    assert stack["smooth_body_transition_station_from_underhead_mm"] == expected_transition
    assert stack["component_role_count"] == 4
    assert stack["wood_or_washer_tie_assigned"] is False


@pytest.mark.parametrize(
    ("global_size", "local_size", "band"),
    [(0, 1, 2), (3, 4, 2), (3, 1, float("inf")), (True, 1, 2)],
)
def test_mesh_configuration_requires_explicit_positive_ordered_sizes(global_size, local_size, band):
    with pytest.raises((TypeError, ValueError)):
        hardware_mesh.validate_mesh_configuration(global_size, local_size, band)


def test_mesh_configuration_preserves_explicit_size_values():
    assert hardware_mesh.validate_mesh_configuration(4, 1.5, 3) == {
        "global_max_size_mm": 4.0,
        "local_min_size_mm": 1.5,
        "surface_refinement_band_mm": 3.0,
    }


def test_analytic_surface_datum_classifier_resolves_axis_radius_and_seat_station():
    _inventory_row, original_stack, geometry = _profile()
    stack = {
        **original_stack,
        "underhead_origin_global_xyz_mm": [0, 0, 0],
        "world_axis_direction_head_to_nut": [0, 0, 1],
    }
    smooth_r = geometry["bolt"]["smooth_body_diameter_mm"] / 2
    cylinder_probes = _cylinder_probe_grid(smooth_r, (5, 70, 120))
    cylinder = hardware_mesh.classify_surface_datum(
        "Cylinder", cylinder_probes, stack, "bolt", geometry
    )
    washer_plane = hardware_mesh.classify_surface_datum(
        "Plane",
        _plane_probe_grid(2.032, (0, 0, 1)),
        stack,
        "head_washer",
        geometry,
    )

    assert cylinder["role_candidates"] == ["bolt_smooth_shank_cylindrical_surface"]
    assert cylinder["station_interval_from_underhead_mm"] == [5.0, 120.0]
    assert washer_plane["role_candidates"] == ["head_washer_wood_seat_face"]


def test_root_sensitivity_surface_uses_the_named_profile_station():
    _inventory_row, original_stack, geometry = _profile()
    stack = {
        **original_stack,
        "underhead_origin_global_xyz_mm": [0, 0, 0],
        "world_axis_direction_head_to_nut": [0, 0, 1],
        "smooth_body_transition_station_from_underhead_mm": 127.0,
    }
    root_radius = geometry["thread_and_gage_mapping"]["root_sensitivity_diameter_mm"] / 2
    probes = _cylinder_probe_grid(root_radius, (130, 140))

    result = hardware_mesh.classify_surface_datum("Cylinder", probes, stack, "bolt", geometry)

    assert result["role_candidates"] == ["bolt_root_sensitivity_cylindrical_surface"]


def test_analytic_surface_datum_classifier_rejects_radius_or_type_mismatch():
    _inventory_row, original_stack, geometry = _profile()
    stack = {
        **original_stack,
        "underhead_origin_global_xyz_mm": [0, 0, 0],
        "world_axis_direction_head_to_nut": [0, 0, 1],
    }
    wrong_radius = _cylinder_probe_grid(3.0, (5, 60))
    unknown_surface = _cylinder_probe_grid(3.175, (5,))

    assert hardware_mesh.classify_surface_datum(
        "Cylinder", wrong_radius, stack, "bolt", geometry
    )["status"] == "unresolved"
    assert hardware_mesh.classify_surface_datum(
        "BSpline surface", unknown_surface, stack, "bolt", geometry
    )["status"] == "unresolved"
    missing_normal = _cylinder_probe_grid(3.175, (5, 60))
    missing_normal[1]["normal_global"] = None
    assert hardware_mesh.classify_surface_datum(
        "Cylinder", missing_normal, stack, "bolt", geometry
    )["status"] == "unresolved"


def test_output_directory_is_fresh_and_cannot_overlap_input_bundle(tmp_path):
    existing = tmp_path / "existing"
    existing.mkdir()
    with pytest.raises(FileExistsError, match="already exists"):
        hardware_mesh.prepare_hardware_patch_mesh(
            BUNDLE,
            existing,
            scenario_id="body_to_far_wood_face",
            global_max_size_mm=4,
            local_min_size_mm=1.5,
            surface_refinement_band_mm=3,
        )
    with pytest.raises(ValueError, match="must be separate"):
        hardware_mesh.prepare_hardware_patch_mesh(
            BUNDLE,
            BUNDLE / "mesh-attempt",
            scenario_id="body_to_far_wood_face",
            global_max_size_mm=4,
            local_min_size_mm=1.5,
            surface_refinement_band_mm=3,
        )


def test_bundle_rejects_changed_step_bytes_and_preserves_preflight_failure(tmp_path):
    copied = tmp_path / "bundle"
    shutil.copytree(BUNDLE, copied)
    step = copied / "hardware/body_to_far_wood_face/lower_rail_1/bolt.step"
    step.write_bytes(step.read_bytes() + b"tampered")
    with pytest.raises(ValueError, match="missing or changed"):
        hardware_mesh.load_hardware_bundle(copied, "body_to_far_wood_face")

    output = tmp_path / "failed-mesh"
    with pytest.raises(ValueError, match="missing or changed"):
        hardware_mesh.prepare_hardware_patch_mesh(
            copied,
            output,
            scenario_id="body_to_far_wood_face",
            global_max_size_mm=4,
            local_min_size_mm=1.5,
            surface_refinement_band_mm=3,
        )
    record = json.loads((output / "mesh.json").read_text())
    assert record["status"] == "FAILED_PHYSICAL_HARDWARE_MESH_PREPARATION_NO_SOLVER"
    assert "missing or changed" in record["error"]
    assert not (output / "mesh.inp").exists()


def test_reused_mesh_helpers_still_enforce_disjoint_body_ownership():
    nodes = {
        1: (0.0, 0.0, 0.0),
        2: (1.0, 0.0, 0.0),
        3: (0.0, 1.0, 0.0),
        4: (0.0, 0.0, 1.0),
        5: (0.5, 0.0, 0.0),
        6: (0.5, 0.5, 0.0),
        7: (0.0, 0.5, 0.0),
        8: (0.0, 0.0, 0.5),
        9: (0.5, 0.0, 0.5),
        10: (0.0, 0.5, 0.5),
    }
    elements = {1: tuple(nodes)}
    all_nodes: dict[int, tuple[float, float, float]] = {}
    all_elements: dict[int, tuple[int, ...]] = {}
    bodies = {}
    for body_id in ("lower_rail_1__bolt", "lower_rail_1__head_washer"):
        node_map, element_map = hardware_mesh.append_body(
            all_nodes, all_elements, nodes, elements
        )
        bodies[body_id] = {"nodes": sorted(node_map.values()), "elements": sorted(element_map.values())}

    assert len(all_nodes) == 20
    assert set(bodies["lower_rail_1__bolt"]["nodes"]).isdisjoint(
        bodies["lower_rail_1__head_washer"]["nodes"]
    )
    hardware_mesh.validate_ownership(all_nodes, all_elements, bodies)
    with pytest.raises(ValueError, match="overlaps or is incomplete"):
        bodies["lower_rail_1__head_washer"]["nodes"].append(
            bodies["lower_rail_1__bolt"]["nodes"][0]
        )
        hardware_mesh.validate_ownership(all_nodes, all_elements, bodies)


def test_integrated_volume_and_c3d10_contract_are_shared_with_wood_mesh_worker():
    audit = wood_mesh.audit_mesh_volume(
        1.0,
        determinants=[1.0, 1.0],
        quadrature_weights=[0.5, 0.5],
        sampled_jacobians=[0.9],
        element_count=1,
    )
    assert audit["relative_volume_error"] == 0.0
    assert hardware_mesh.GMSH_TO_CCX == (0, 1, 2, 3, 4, 5, 6, 7, 9, 8)
