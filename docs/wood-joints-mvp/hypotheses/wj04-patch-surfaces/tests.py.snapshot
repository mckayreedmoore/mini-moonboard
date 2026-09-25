"""Pure contract tests for source-bound WJ04 mesh surface classification."""

from __future__ import annotations

import copy
import json
import math
from pathlib import Path
from typing import Any

import pytest

from fea import wood_joint_patch_classification as classifier
from fea import wood_joint_patch_mesh as mesh_contract

ROOT = Path(__file__).resolve().parents[1]
BUNDLE = ROOT / "fea/results/diagnostics/wj04-full-stock-patch-geometry-v1"
OVERLAP_PATH = (
    ROOT
    / "docs/wood-joints-mvp/hypotheses/wj04-patch-geometry/finite-face-overlap.json"
)


def _source_inputs() -> tuple[dict[str, Any], dict[str, Any]]:
    inventory = json.loads((BUNDLE / "inventory.json").read_text())
    overlap = json.loads(OVERLAP_PATH.read_text())
    return inventory, overlap


def _add(a: tuple[float, ...], b: tuple[float, ...]) -> tuple[float, ...]:
    return tuple(x + y for x, y in zip(a, b, strict=True))


def _sub(a: tuple[float, ...], b: tuple[float, ...]) -> tuple[float, ...]:
    return tuple(x - y for x, y in zip(a, b, strict=True))


def _scale(a: tuple[float, ...], factor: float) -> tuple[float, ...]:
    return tuple(value * factor for value in a)


def _dot(a: tuple[float, ...], b: tuple[float, ...]) -> float:
    return math.fsum(x * y for x, y in zip(a, b, strict=True))


def _unit(a: tuple[float, ...]) -> tuple[float, float, float]:
    length = math.sqrt(_dot(a, a))
    assert length > 0
    return tuple(value / length for value in a)  # type: ignore[return-value]


def _cross(a: tuple[float, ...], b: tuple[float, ...]) -> tuple[float, float, float]:
    return (
        a[1] * b[2] - a[2] * b[1],
        a[2] * b[0] - a[0] * b[2],
        a[0] * b[1] - a[1] * b[0],
    )


def _plane_basis(
    normal: tuple[float, float, float],
) -> tuple[tuple[float, ...], tuple[float, ...]]:
    ref = (1.0, 0.0, 0.0) if abs(normal[0]) < 0.8 else (0.0, 1.0, 0.0)
    u = _unit(_cross(normal, ref))
    return u, _unit(_cross(normal, u))


def _plane_key(
    member_id: str, point: tuple[float, ...], normal: tuple[float, ...]
) -> tuple[Any, ...]:
    canonical = list(_unit(normal))
    first = next(value for value in canonical if abs(value) > 1e-10)
    if first < 0:
        canonical = [-value for value in canonical]
    offset = _dot(tuple(canonical), point)
    return member_id, *(round(value, 7) for value in canonical), round(offset, 6)


def _finite_bounds(points: list[tuple[float, float, float]]) -> list[float]:
    bounds = []
    for axis in range(3):
        bounds.extend(
            (min(point[axis] for point in points), max(point[axis] for point in points))
        )
    return bounds


def _build_synthetic_mesh(
    inventory: dict[str, Any],
    overlap: dict[str, Any],
    *,
    split_bore_walls: bool = False,
) -> tuple[
    dict[str, Any],
    dict[int, tuple[float, float, float]],
    dict[str, dict[int, tuple[int, ...]]],
    dict[str, Any],
]:
    """Create analytic mesh surfaces tied to the real inventory datums/axes."""
    surfaces_by_body: dict[str, list[dict[str, Any]]] = {
        body_id: [] for body_id in mesh_contract.WOOD_BODY_IDS
    }
    selectors: dict[str, Any] = {"plane": {}, "bore": {}, "noncandidate": None}
    overlap_by_id = {row["interface_id"]: row for row in overlap["interfaces"]}
    plane_rows: dict[tuple[Any, ...], dict[str, Any]] = {}

    def add_plane(
        member_id: str,
        point: tuple[float, float, float],
        normal: tuple[float, float, float],
        area: float,
        selector: str,
    ) -> None:
        key = _plane_key(member_id, point, normal)
        if key in plane_rows:
            previous = plane_rows[key]
            assert math.isclose(previous["area_mm2"], area, abs_tol=1e-5)
            selectors["plane"][selector] = (member_id, previous)
            return
        unit_normal = _unit(normal)
        u, v = _plane_basis(unit_normal)
        points = [
            point,
            _add(point, _scale(u, 1.0)),
            _add(point, _scale(v, 1.0)),
            _sub(point, _scale(u, 1.0)),
            _sub(point, _scale(v, 1.0)),
            _add(_add(point, _scale(u, 0.75)), _scale(v, 0.5)),
        ]
        row = {
            "cad_type": "Plane",
            "area_mm2": area,
            "sample_point": point,
            "sample_normal": _scale(unit_normal, -1.0)
            if len(plane_rows) % 2
            else unit_normal,
            "tri6_points": points,
            "analytic_surface_data": {
                "surface_type": "Plane",
                "sample_xyz_mm": list(point),
                "sample_normal_global": list(
                    _scale(unit_normal, -1.0) if len(plane_rows) % 2 else unit_normal
                ),
            },
            "test_semantic": selector,
        }
        plane_rows[key] = row
        surfaces_by_body[member_id].append(row)
        selectors["plane"][selector] = (member_id, row)

    for interface in inventory["wood_interfaces"]:
        interface_id = interface["interface_id"]
        candidate = interface["candidate_cleat_face"]
        host = interface["source_host_face"]
        datum = interface["shear_plane_datum"]
        probe = overlap_by_id[interface_id]
        add_plane(
            candidate["part_id"],
            tuple(datum["origin_global_xyz_mm"]),
            tuple(candidate["plane_normal_global_xyz"]),
            candidate["composed_finished_planar_area_mm2"],
            f"{interface_id}:candidate",
        )
        add_plane(
            host["part_id"],
            tuple(host["center_global_xyz_mm"]),
            tuple(host["normal_global_xyz"]),
            probe["host_planar_area_mm2"],
            f"{interface_id}:host",
        )

    def add_cylinder(
        member_id: str,
        origin: tuple[float, float, float],
        direction: tuple[float, float, float],
        radius: float,
        station_start: float,
        station_end: float,
        selector: str,
        *,
        area_override: float | None = None,
    ) -> None:
        axis = _unit(direction)
        ref = (0.0, 0.0, 1.0) if abs(axis[2]) < 0.8 else (0.0, 1.0, 0.0)
        u = _unit(_cross(axis, ref))
        v = _unit(_cross(axis, u))
        span = station_end - station_start
        stations = [
            station_start + span * fraction
            for fraction in (0.0, 0.2, 0.4, 0.6, 0.8, 1.0)
        ]
        points = []
        for index, station in enumerate(stations):
            angle = 2 * math.pi * index / len(stations)
            radial = _add(_scale(u, math.cos(angle)), _scale(v, math.sin(angle)))
            points.append(
                _add(_add(origin, _scale(axis, station)), _scale(radial, radius))
            )
        sample_station = (station_start + station_end) / 2
        sample_point = _add(
            _add(origin, _scale(axis, sample_station)), _scale(u, radius)
        )
        sample_normal = _scale(u, -1.0) if len(surfaces_by_body[member_id]) % 2 else u
        area = (
            area_override if area_override is not None else 2 * math.pi * radius * span
        )
        row = {
            "cad_type": "Cylinder",
            "area_mm2": area,
            "sample_point": sample_point,
            "sample_normal": sample_normal,
            "tri6_points": points,
            "analytic_surface_data": {
                "surface_type": "Cylinder",
                "sample_xyz_mm": list(sample_point),
                "sample_normal_global": list(sample_normal),
            },
            "test_semantic": selector,
        }
        surfaces_by_body[member_id].append(row)
        if selector.startswith("bore:"):
            selectors["bore"][selector.removeprefix("bore:")] = (member_id, row)
        elif selector == "noncandidate-cylinder":
            selectors["noncandidate"] = (member_id, row)

    for bolt in inventory["physical_bolts"]:
        axis_origin = tuple(bolt["world_axis_origin_xyz_mm"])
        direction = tuple(bolt["world_axis_direction_head_to_nut"])
        radius = math.sqrt(
            bolt["composed_occupancy_bore"]["volume_mm3"]
            / (
                math.pi
                * (bolt["wood_grip_mm"] + 2 * classifier.BORE_EXTENSION_EACH_END_MM)
            )
        )
        station = 0.0
        for receiver in bolt["receivers_head_to_nut"]:
            thickness = receiver["wood_thickness_mm"]
            pieces = (
                (
                    (station, station + thickness / 2),
                    (station + thickness / 2, station + thickness),
                )
                if split_bore_walls
                else ((station, station + thickness),)
            )
            for piece_index, (start, end) in enumerate(pieces):
                suffix = f"{bolt['physical_bolt_id']}::{receiver['member_id']}"
                if len(pieces) > 1:
                    suffix += f"::piece-{piece_index + 1}"
                add_cylinder(
                    receiver["member_id"],
                    axis_origin,
                    direction,
                    radius,
                    start,
                    end,
                    f"bore:{suffix}",
                )
            station += thickness

    add_cylinder(
        mesh_contract.LOWER_RAIL,
        (1500.0, -800.0, 400.0),
        (0.0, 0.0, 1.0),
        5.0,
        0.0,
        12.0,
        "noncandidate-cylinder",
    )

    node_coordinates: dict[int, tuple[float, float, float]] = {}
    elements_by_body: dict[str, dict[int, tuple[int, ...]]] = {}
    mesh_bodies: dict[str, Any] = {}
    next_node = 1
    next_element = 1
    for body_id in mesh_contract.WOOD_BODY_IDS:
        surface_rows: dict[str, Any] = {}
        body_nodes: list[int] = []
        body_elements: list[int] = []
        body_element_rows: dict[int, tuple[int, ...]] = {}
        for tag, surface in enumerate(surfaces_by_body[body_id], start=1):
            tri6_ids = list(range(next_node, next_node + 6))
            points = surface["tri6_points"]
            for node_id, point in zip(tri6_ids, points, strict=True):
                node_coordinates[node_id] = point
            next_node += 6
            # Four extra distinct nodes complete a synthetic C3D10 ownership row.
            extra_points = [
                _add(points[0], (0.01 * index, 0.013 * index, 0.017 * index))
                for index in range(1, 5)
            ]
            extra_ids = list(range(next_node, next_node + 4))
            for node_id, point in zip(extra_ids, extra_points, strict=True):
                node_coordinates[node_id] = point
            next_node += 4
            connectivity = (*tri6_ids, *extra_ids)
            element_id = next_element
            next_element += 1
            body_nodes.extend(connectivity)
            body_elements.append(element_id)
            body_element_rows[element_id] = connectivity
            surface_rows[str(tag)] = {
                "cad_entity_tag": tag,
                "cad_type": surface["cad_type"],
                "area_mm2": surface["area_mm2"],
                "bounds_order": "xmin,xmax,ymin,ymax,zmin,zmax",
                "bounds_xyz_mm": _finite_bounds(points),
                "tri6_node_ids": tri6_ids,
                "tri6_exterior_face_refs": [[element_id, 1]],
                "analytic_surface_data": surface["analytic_surface_data"],
            }
            surface["mesh_tag"] = tag
            surface["mesh_tri6_node_ids"] = tri6_ids
        elements_by_body[body_id] = body_element_rows
        mesh_bodies[body_id] = {
            "nodes": body_nodes,
            "node_count": len(body_nodes),
            "elements": body_elements,
            "element_count": len(body_elements),
            "exterior_tri6_face_count": len(body_elements),
            "surfaces": surface_rows,
            "surface_inventory": surface_rows,
        }

    # Surface selectors point to the matching report rows and node IDs for negative tests.
    for category in ("plane", "bore"):
        for key, (member_id, original) in selectors[category].items():
            tag = original["mesh_tag"]
            selectors[category][key] = (
                member_id,
                str(tag),
                mesh_bodies[member_id]["surface_inventory"][str(tag)],
            )
    if selectors["noncandidate"] is not None:
        member_id, original = selectors["noncandidate"]
        tag = original["mesh_tag"]
        selectors["noncandidate"] = (
            member_id,
            str(tag),
            mesh_bodies[member_id]["surface_inventory"][str(tag)],
        )

    mesh_record = {
        "schema": mesh_contract.SCHEMA,
        "status": "VERIFIED_C3D10_MESH_ONLY_NO_SOLVER",
        "accepted": False,
        "solved": False,
        "output_contains_material_contact_or_solver_cards": False,
        "body_count": len(mesh_bodies),
        "node_count": len(node_coordinates),
        "element_count": next_element - 1,
        "bodies": mesh_bodies,
    }
    return mesh_record, node_coordinates, elements_by_body, selectors


@pytest.fixture
def synthetic_inputs() -> tuple[Any, ...]:
    inventory, overlap = _source_inputs()
    mesh, nodes, elements, selectors = _build_synthetic_mesh(inventory, overlap)
    return mesh, nodes, elements, inventory, overlap, selectors


def _classify(fixture: tuple[Any, ...]) -> dict[str, Any]:
    mesh, nodes, elements, inventory, overlap, _selectors = fixture
    return classifier.classify_surfaces(
        mesh, nodes, inventory, overlap, elements_by_body=elements
    )


def test_classifies_four_contact_pairs_and_all_sixteen_member_bores(
    synthetic_inputs: tuple[Any, ...],
) -> None:
    result = _classify(synthetic_inputs)

    assert len(result["wood_contact_pairs"]) == 4
    assert len(result["candidate_bore_member_pairs"]) == 16
    assert result["unclassified_cylindrical_surface_count"] == 1
    assert result["accepted"] is False
    assert result["native_solve_run"] is False
    assert result["contact_law_assigned"] is False
    assert result["active_contact_pressure_established"] is False
    assert result["physical_bolt_bore_contact"]["status"] == "not_modeled"
    assert (
        result["physical_bolt_bore_contact"]["initial_lateral_contact_or_seating"]
        == "not represented"
    )
    assert all(
        row["mesh_outward_normal_verified"] is False
        for row in result["wood_contact_pairs"]
    )
    assert all(
        row["contact_or_strength_result"] is False
        for row in result["candidate_bore_member_pairs"]
    )
    assert all(
        row["host_trimmed_surface_area_mm2"] > row["archived_finite_common_area_mm2"]
        for row in result["wood_contact_pairs"]
    )
    assert all(
        row["candidate_common_area_fraction"] == pytest.approx(1.0)
        for row in result["wood_contact_pairs"]
    )


def test_split_cylindrical_entities_are_aggregated_by_axis_and_layer() -> None:
    inventory, overlap = _source_inputs()
    mesh, nodes, elements, _selectors = _build_synthetic_mesh(
        inventory, overlap, split_bore_walls=True
    )

    result = classifier.classify_surfaces(
        mesh, nodes, inventory, overlap, elements_by_body=elements
    )

    assert len(result["candidate_bore_member_pairs"]) == 16
    assert all(
        len(pair["matched_surfaces"]) == 2
        for pair in result["candidate_bore_member_pairs"]
    )
    assert len(result["unclassified_cylindrical_surfaces"]) == 1


def test_rejects_contact_host_area_drift_without_equating_it_to_common_area(
    synthetic_inputs: tuple[Any, ...],
) -> None:
    mesh, nodes, elements, inventory, overlap, _selectors = synthetic_inputs
    changed_overlap = copy.deepcopy(overlap)
    changed_overlap["interfaces"][0]["host_planar_area_mm2"] += 1.0

    with pytest.raises(ValueError, match="host mesh plane area differs from archive"):
        classifier.classify_surfaces(
            mesh, nodes, inventory, changed_overlap, elements_by_body=elements
        )


def test_rejects_invalid_finite_face_distance_record(
    synthetic_inputs: tuple[Any, ...],
) -> None:
    mesh, nodes, elements, inventory, overlap, _selectors = synthetic_inputs
    changed_overlap = copy.deepcopy(overlap)
    changed_overlap["interfaces"][0]["minimum_pair_distance_mm"] = -0.01

    with pytest.raises(
        ValueError, match="source face pair is outside pinned plane tolerance"
    ):
        classifier.classify_surfaces(
            mesh, nodes, inventory, changed_overlap, elements_by_body=elements
        )


def test_rejects_plane_node_off_authenticated_analytic_plane(
    synthetic_inputs: tuple[Any, ...],
) -> None:
    mesh, nodes, elements, _inventory, _overlap, selectors = synthetic_inputs
    interface = next(iter(mesh_contract.EXPECTED_INTERFACE_STACKS))
    _member_id, _tag, row = selectors["plane"][f"{interface}:candidate"]
    node_id = row["tri6_node_ids"][0]
    normal = row["analytic_surface_data"]["sample_normal_global"]
    nodes[node_id] = tuple(
        value + 0.01 * normal[index] for index, value in enumerate(nodes[node_id])
    )

    with pytest.raises(ValueError, match="analytic contact planes were not found"):
        classifier.classify_surfaces(
            mesh, nodes, _inventory, _overlap, elements_by_body=elements
        )


def test_rejects_bore_nodes_that_do_not_follow_authenticated_axis(
    synthetic_inputs: tuple[Any, ...],
) -> None:
    mesh, nodes, elements, inventory, overlap, selectors = synthetic_inputs
    pair_id = next(iter(selectors["bore"]))
    _member_id, _tag, row = selectors["bore"][pair_id]
    node_id = row["tri6_node_ids"][0]
    nodes[node_id] = (nodes[node_id][0] + 0.02, nodes[node_id][1], nodes[node_id][2])

    with pytest.raises(ValueError, match="no cylinder wall matches"):
        classifier.classify_surfaces(
            mesh, nodes, inventory, overlap, elements_by_body=elements
        )


def test_rejects_receiver_thickness_or_order_drift(
    synthetic_inputs: tuple[Any, ...],
) -> None:
    mesh, nodes, elements, inventory, overlap, _selectors = synthetic_inputs
    changed_inventory = copy.deepcopy(inventory)
    bolt = changed_inventory["physical_bolts"][0]
    bolt["receivers_head_to_nut"][0]["wood_thickness_mm"] = 89.0
    bolt["receivers_head_to_nut"][1]["wood_thickness_mm"] = 38.0

    with pytest.raises(
        ValueError, match="receiver thicknesses differ from pinned members"
    ):
        classifier.classify_surfaces(
            mesh, nodes, changed_inventory, overlap, elements_by_body=elements
        )

    changed_inventory = copy.deepcopy(inventory)
    bolt = changed_inventory["physical_bolts"][0]
    bolt["receivers_head_to_nut"].reverse()
    with pytest.raises(ValueError, match="ordered receiver pair changed"):
        classifier.classify_surfaces(
            mesh, nodes, changed_inventory, overlap, elements_by_body=elements
        )


def test_rejects_surface_refs_that_escape_body_ownership(
    synthetic_inputs: tuple[Any, ...],
) -> None:
    mesh, nodes, elements, inventory, overlap, _selectors = synthetic_inputs
    body_id = mesh_contract.WOOD_BODY_IDS[0]
    row = next(iter(mesh["bodies"][body_id]["surface_inventory"].values()))
    row["tri6_exterior_face_refs"][0][0] = (
        max(element for rows in elements.values() for element in rows) + 1
    )

    with pytest.raises(ValueError, match="face ref has wrong body IDs"):
        classifier.classify_surfaces(
            mesh, nodes, inventory, overlap, elements_by_body=elements
        )
