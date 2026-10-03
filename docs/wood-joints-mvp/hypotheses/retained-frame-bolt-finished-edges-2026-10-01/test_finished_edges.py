"""Independent known-answer checks for saved-signature finished-edge rays."""

from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import math
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import pytest

HERE = Path(__file__).resolve().parent


def _load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


method = _load_module("retained_finished_edges_test_method", HERE / "method.py")
producer = _load_module("retained_finished_edges_test_producer", HERE / "produce.py")
oracle = _load_module("retained_finished_edges_test_oracle", HERE / "raw_oracle.py")

OWN_ID = "synthetic/own-bore"
TARGET_MEMBER = "base_floor_left"  # The method deliberately limits queries to these receivers.
TAU = 2.0 * math.pi
UPSTREAM_REPORT_PATHS = (
    Path("/tmp/mini-moonboard-retained-frame-bolt-current-load-path-2026-10-01.json"),
    Path("/tmp/mini-moonboard-retained-frame-bolt-current-load-path-2026-10-01-raw-oracle.json"),
    Path("/tmp/mini-moonboard-retained-frame-bolt-current-resistance-basis-2026-10-01.json"),
)


@pytest.fixture(scope="module")
def frozen_upstream_inputs():
    missing = [str(path) for path in UPSTREAM_REPORT_PATHS if not path.is_file()]
    assert not missing, (
        "Restore the frozen upstream artifacts described in README.md before "
        f"running this packet's integration tests; missing: {missing}"
    )
    return producer.checked_inputs(*UPSTREAM_REPORT_PATHS)


def _dot(a, b):
    return sum(x * y for x, y in zip(a, b, strict=True))


def _add(a, b):
    return [x + y for x, y in zip(a, b, strict=True)]


def _scale(a, amount):
    return [x * amount for x in a]


def _sub(a, b):
    return [x - y for x, y in zip(a, b, strict=True)]


def _norm(a):
    return math.sqrt(_dot(a, a))


def _unit(a):
    length = _norm(a)
    return [x / length for x in a]


def _cross(a, b):
    return [a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]]


def _rotate_z(point, angle):
    c, s = math.cos(angle), math.sin(angle)
    return [c * point[0] - s * point[1], s * point[0] + c * point[1], point[2]]


def _perpendicular(unit_normal):
    helper = [1.0, 0.0, 0.0] if abs(unit_normal[0]) < 0.8 else [0.0, 1.0, 0.0]
    return _unit(_cross(unit_normal, helper))


def _line_edge(start, end):
    delta = _sub(end, start)
    length = _norm(delta)
    direction = _scale(delta, 1.0 / length)
    return {
        "curve_kind": "LINE",
        "length_mm": length,
        "line": {"origin_global_xyz_mm": list(start), "direction_global_xyz": direction},
        "parameter_bounds": [0.0, length],
        "parameter_endpoint_global_xyz_mm": [list(start), list(end)],
        "topological_vertices_global_xyz_mm": [list(start), list(end)],
    }


def _polygon_edges(vertices):
    edges = [_line_edge(vertices[i], vertices[(i + 1) % len(vertices)]) for i in range(len(vertices))]
    # The saved register does not guarantee ordered edge rows.  Rotate the rows
    # and reverse one edge's direction while keeping its parameter record valid.
    if len(edges) > 3:
        edges = edges[2:] + edges[:2]
    if len(edges) > 1:
        edge = edges[1]
        endpoints = edge["parameter_endpoint_global_xyz_mm"]
        vertices = edge["topological_vertices_global_xyz_mm"]
        edge["line"]["origin_global_xyz_mm"] = endpoints[1]
        edge["line"]["direction_global_xyz"] = _scale(edge["line"]["direction_global_xyz"], -1.0)
        edge["parameter_endpoint_global_xyz_mm"] = [endpoints[1], endpoints[0]]
        edge["topological_vertices_global_xyz_mm"] = [vertices[1], vertices[0]]
        edge["line"]["origin_global_xyz_mm"] = endpoints[1]
        edge["parameter_bounds"] = [0.0, edge["length_mm"]]
    return edges


def _circle_edge(center, normal, radius):
    radial = _perpendicular(normal)
    point = _add(center, _scale(radial, radius))
    return {
        "curve_kind": "CIRCLE",
        "length_mm": TAU * radius,
        "circle": {
            "center_global_xyz_mm": list(center),
            "axis_unit_global_xyz": list(normal),
            "radius_mm": radius,
        },
        "parameter_bounds": [0.0, TAU],
        "parameter_endpoint_global_xyz_mm": [point, list(point)],
        "topological_vertices_global_xyz_mm": [list(point)],
    }


def _plane_feature(feature_id, normal, vertices=None, circles=()):
    normal = _unit(normal)
    wires = []
    if vertices is not None:
        vertices = [list(point) for point in vertices]
        edges = _polygon_edges(vertices)
        wires.append({"wire_index_one_based": 1, "edge_count": len(edges), "edges": edges})
        next_index = 2
    else:
        next_index = 1
    for center, radius in circles:
        edge = _circle_edge(center, normal, radius)
        wires.append({"wire_index_one_based": next_index, "edge_count": 1, "edges": [edge]})
        next_index += 1
    assert wires
    witness = vertices[0] if vertices is not None else circles[0][0]
    station = _dot(normal, witness)
    return {
        "feature_id": feature_id,
        "surface_kind": "PLANE",
        "centroid_global_xyz_mm": list(witness),
        "plane": {
            "normal_global_xyz": list(normal),
            "signed_plane_station_global_mm": station,
            "coordinate_equation": "normal · point = signed station",
        },
        "trim": {"wire_count": len(wires), "wires": wires},
    }


def _cylinder_feature(spec):
    center = list(spec["center"])
    axis = _unit(spec.get("axis", [0.0, 0.0, 1.0]))
    low, high = spec.get("interval", [-5.0, 5.0])
    radius = spec["radius"]
    radial = _perpendicular(axis)
    radial_point = _add(center, _scale(radial, radius))
    end_centers = [_add(center, _scale(axis, station)) for station in (low, high)]
    circles = [_circle_edge(point, axis, radius) for point in end_centers]
    seam_start = _add(center, _scale(radial, radius))
    seam_end = _add(seam_start, _scale(axis, high - low))
    seam = _line_edge(seam_start, seam_end)
    # Match the saved surface parameterization: the line origin is at station
    # zero, with finite cylinder end stations as its LINE parameters.
    seam["line"]["origin_global_xyz_mm"] = radial_point
    seam["line"]["direction_global_xyz"] = axis
    seam["parameter_bounds"] = [low, high]
    seam["parameter_endpoint_global_xyz_mm"] = [
        _add(radial_point, _scale(axis, low)),
        _add(radial_point, _scale(axis, high)),
    ]
    seam["topological_vertices_global_xyz_mm"] = copy.deepcopy(seam["parameter_endpoint_global_xyz_mm"])
    seam["length_mm"] = high - low
    mid = (low + high) / 2.0
    normal_sample = _add(_add(center, _scale(axis, mid)), _scale(radial, radius))
    return {
        "feature_id": spec["id"],
        "surface_kind": "CYLINDER",
        "centroid_global_xyz_mm": _add(center, _scale(axis, mid)),
        "cylinder": {
            "axis_origin_global_xyz_mm": center,
            "axis_unit_global_xyz": axis,
            "axis_parameter_interval_mm": [low, high],
            "axis_station_interval_mm": [low, high],
            "radius_mm": radius,
            "material_side_geometry": "bore_like",
            "normal_global_xyz": _scale(radial, -1.0),
            "normal_sample_global_xyz_mm": normal_sample,
            "normal_sample_valid_on_trim": True,
            "radial_normal_dot": -1.0,
        },
        "trim": {
            "surface_parameter_bounds": {"u": [0.0, TAU], "v": [low, high]},
            "wire_count": 1,
            "wires": [{"wire_index_one_based": 1, "edge_count": 3, "edges": [*circles, seam]}],
        },
    }


def _box_member(bores, *, bounds=(-5.0, 10.0, -5.0, 5.0, -5.0, 5.0), rotation=0.0):
    x0, x1, y0, y1, z0, z1 = bounds
    faces = [
        {"id": "box/x-", "normal": [-1, 0, 0], "vertices": [[x0, y0, z0], [x0, y1, z0], [x0, y1, z1], [x0, y0, z1]], "circles": []},
        {"id": "box/x+", "normal": [1, 0, 0], "vertices": [[x1, y0, z0], [x1, y0, z1], [x1, y1, z1], [x1, y1, z0]], "circles": []},
        {"id": "box/y-", "normal": [0, -1, 0], "vertices": [[x0, y0, z0], [x0, y0, z1], [x1, y0, z1], [x1, y0, z0]], "circles": []},
        {"id": "box/y+", "normal": [0, 1, 0], "vertices": [[x0, y1, z0], [x1, y1, z0], [x1, y1, z1], [x0, y1, z1]], "circles": []},
        {"id": "box/z-", "normal": [0, 0, -1], "vertices": [[x0, y0, z0], [x1, y0, z0], [x1, y1, z0], [x0, y1, z0]], "circles": []},
        {"id": "box/z+", "normal": [0, 0, 1], "vertices": [[x0, y0, z1], [x0, y1, z1], [x1, y1, z1], [x1, y0, z1]], "circles": []},
    ]
    caps = []
    for spec in bores:
        axis = _unit(spec.get("axis", [0.0, 0.0, 1.0]))
        low, high = spec.get("interval", [-5.0, 5.0])
        for label, station in (("low", low), ("high", high)):
            point = _add(spec["center"], _scale(axis, station))
            if label in spec.get("cap_normals", {}):
                caps.append((f"{spec['id']}/{label}-cap", point, spec["cap_normals"][label], spec["radius"]))
                continue
            matches = [face for face in faces if abs(_dot(face["normal"], _sub(point, face["vertices"][0]))) < 1.0e-8]
            assert len(matches) == 1, f"bore endpoint {point} must lie on one box face or name a cap"
            matches[0]["circles"].append((point, spec["radius"]))

    features = []
    for face in faces:
        vertices = [_rotate_z(point, rotation) for point in face["vertices"]]
        normal = _rotate_z(face["normal"], rotation)
        circles = [(_rotate_z(center, rotation), radius) for center, radius in face["circles"]]
        features.append(_plane_feature(face["id"], normal, vertices, circles))
    for feature_id, center, normal, radius in caps:
        features.append(_plane_feature(feature_id, _rotate_z(normal, rotation), None,
                                       [(_rotate_z(center, rotation), radius)]))
    for spec in bores:
        rotated = dict(spec)
        rotated["center"] = _rotate_z(spec["center"], rotation)
        rotated["axis"] = _rotate_z(spec.get("axis", [0.0, 0.0, 1.0]), rotation)
        features.append(_cylinder_feature(rotated))
    return {"member_id": TARGET_MEMBER, "features": features}


def _prism_member(outline_xy, bore):
    """Extrude a simple concave XY outline and include every analytic side face."""
    z0, z1 = -5.0, 5.0
    features = []
    for z, normal, label in ((z0, [0, 0, -1], "bottom"), (z1, [0, 0, 1], "top")):
        vertices = [[x, y, z] for x, y in outline_xy]
        center = _add(bore["center"], [0.0, 0.0, z])
        features.append(_plane_feature(f"prism/{label}", normal, vertices, [(center, bore["radius"])]))
    for index, start in enumerate(outline_xy):
        end = outline_xy[(index + 1) % len(outline_xy)]
        dx, dy = end[0] - start[0], end[1] - start[1]
        length = math.hypot(dx, dy)
        normal = [dy / length, -dx / length, 0.0]  # outline is counter-clockwise
        vertices = [[start[0], start[1], z0], [end[0], end[1], z0],
                    [end[0], end[1], z1], [start[0], start[1], z1]]
        features.append(_plane_feature(f"prism/edge-{index}", normal, vertices))
    features.append(_cylinder_feature({**bore, "axis": [0.0, 0.0, 1.0], "interval": [z0, z1]}))
    return {"member_id": TARGET_MEMBER, "features": features}


def _query(member, origin, direction, own_id=OWN_ID):
    return method.query_member_direction(member, own_id, origin, direction)


def _own_bore(center=(0.0, 0.0, 0.0), radius=1.0, axis=(0.0, 0.0, 1.0), interval=(-5.0, 5.0), **extra):
    return {"id": OWN_ID, "center": list(center), "radius": radius, "axis": list(axis), "interval": list(interval), **extra}


def test_through_own_bore_is_filled_for_origin_and_excluded_from_forward_events():
    member = _box_member([_own_bore()])
    row = _query(member, [0.0, 0.0, 0.0], [1.0, 0.0, 0.0])

    assert row["status"] == "ok"
    assert row["origin_membership"]["status"] == "inside_filled_own_bore"
    assert row["first_material_exit"]["distance_mm"] == pytest.approx(10.0)
    assert row["first_exterior_exit"]["feature_id"] == "box/x+"
    assert row["distance_mm"] == pytest.approx(10.0)
    assert all(OWN_ID not in event["feature_ids"] for event in row["events"])


def test_matching_own_planar_hole_loops_are_required_and_filled_for_origin_membership():
    member = _box_member([_own_bore(axis=(1.0, 0.0, 0.0))], bounds=(-5.0, 5.0, -5.0, 5.0, -5.0, 5.0))
    axial = _query(member, [0.0, 0.0, 0.0], [1.0, 0.0, 0.0])
    assert axial["origin_membership"]["status"] == "inside_filled_own_bore"

    missing_loop = copy.deepcopy(member)
    positive_x = next(f for f in missing_loop["features"] if f["feature_id"] == "box/x+")
    positive_x["trim"]["wires"] = [positive_x["trim"]["wires"][0]]
    refused = _query(missing_loop, [0.0, 0.0, 0.0], [1.0, 0.0, 0.0])
    assert refused["status"] == "unsupported"
    assert "matching inner trim loop" in refused["reason"]


def test_other_through_bore_is_first_material_loss_but_not_member_exterior():
    member = _box_member([_own_bore(), {"id": "other/through", "center": [4.0, 0.0, 0.0],
                                       "radius": 1.0, "axis": [0.0, 0.0, 1.0],
                                       "interval": [-5.0, 5.0]}])
    row = _query(member, [0.0, 0.0, 0.0], [1.0, 0.0, 0.0])

    assert row["status"] == "ok"
    assert row["origin_membership"]["status"] == "inside_filled_own_bore"
    assert row["first_material_exit"]["distance_mm"] == pytest.approx(3.0)
    assert row["first_material_exit"]["feature_id"] == "other/through"
    assert row["first_material_exit"]["exterior_classification"] == "bore_wall"
    assert row["first_exterior_exit"]["distance_mm"] == pytest.approx(10.0)
    assert row["first_exterior_exit"]["feature_id"] == "box/x+"
    assert [event["entry_or_exit"] for event in row["events"]] == ["exit", "entry", "exit"]


def test_blind_cap_is_retained_as_material_entry_not_named_exterior():
    blind = {"id": "other/blind", "center": [5.0, 0.0, 0.0], "radius": 1.0,
             "axis": [0.0, 0.0, 1.0], "interval": [-5.0, 0.0],
             "cap_normals": {"high": [0.0, 0.0, -1.0]}}
    member = _box_member([_own_bore(), blind], bounds=(-5.0, 12.0, -5.0, 5.0, -5.0, 5.0))
    direction = [5.0 / math.sqrt(29.0), 0.0, 2.0 / math.sqrt(29.0)]
    row = _query(member, [0.0, 0.0, -2.0], direction)

    cap = next(event for event in row["events"] if event["feature_id"] == "other/blind/high-cap")
    assert row["status"] == "ok"
    assert row["origin_membership"]["status"] == "inside_filled_own_bore"
    assert row["first_material_exit"]["feature_id"] == "other/blind"
    assert row["first_material_exit"]["distance_mm"] == pytest.approx(4.0 * math.sqrt(29.0) / 5.0)
    assert cap["distance_mm"] == pytest.approx(math.sqrt(29.0))
    assert cap["entry_or_exit"] == "entry"
    assert cap["exterior_classification"] == "blind_circular_cap"
    assert row["first_exterior_exit"]["feature_id"] == "box/x+"
    assert row["distance_mm"] == pytest.approx(12.0 * math.sqrt(29.0) / 5.0)


def test_finite_cylinder_endpoint_preserves_ambiguous_rim_event_and_null_distance():
    blind = {"id": "other/blind", "center": [5.0, 0.0, 0.0], "radius": 1.0,
             "axis": [0.0, 0.0, 1.0], "interval": [-5.0, 0.0],
             "cap_normals": {"high": [0.0, 0.0, -1.0]}}
    member = _box_member([_own_bore(), blind], bounds=(-5.0, 12.0, -5.0, 5.0, -5.0, 5.0))
    row = _query(member, [0.0, 0.0, -2.0], [2.0 / math.sqrt(5.0), 0.0, 1.0 / math.sqrt(5.0)])
    rim = next(event for event in row["events"]
               if set(event["feature_ids"]) == {"other/blind", "other/blind/high-cap"})

    assert rim["distance_mm"] == pytest.approx(2.0 * math.sqrt(5.0))
    assert rim["point_global_xyz_mm"] == pytest.approx([4.0, 0.0, 0.0])
    assert rim["surface_kind"] == "SIMULTANEOUS"
    assert rim["corner_ambiguity"] is True
    assert rim["entry_or_exit"] == "ambiguous"
    assert row["status"] == "ambiguous"
    assert row["first_exterior_exit"] is None and row["distance_mm"] is None


def test_rotated_box_preserves_known_ray_distance_and_global_exit_point():
    angle = math.radians(37.0)
    member = _box_member([_own_bore()], rotation=angle)
    direction = [math.cos(angle), math.sin(angle), 0.0]
    row = _query(member, [0.0, 0.0, 0.0], direction)

    assert row["status"] == "ok"
    assert row["distance_mm"] == pytest.approx(10.0)
    assert row["first_exterior_exit"]["point_global_xyz_mm"] == pytest.approx(
        [10.0 * math.cos(angle), 10.0 * math.sin(angle), 0.0]
    )


def test_nonconvex_recess_wall_is_traced_from_line_loops():
    # The inward slot occupies x in [-1, 1] above y=1.  At x=0, the
    # material path from the own bore reaches the slot floor after exactly 1 mm.
    outline = [(-5, -5), (5, -5), (5, 5), (1, 5), (1, 1), (-1, 1), (-1, 5), (-5, 5)]
    member = _prism_member(outline, {"id": OWN_ID, "center": [0.0, 0.0, 0.0], "radius": 0.75})
    row = _query(member, [0.0, 0.0, 0.0], [0.0, 1.0, 0.0])

    assert row["status"] == "ok"
    assert row["first_material_exit"]["distance_mm"] == pytest.approx(1.0)
    assert row["first_exterior_exit"]["feature_id"] == "prism/edge-4"
    assert row["distance_mm"] == pytest.approx(1.0)


def test_complete_concave_ray_trace_retains_reentry_and_second_exterior_exit():
    # A U-shaped section has two material intervals on y=0.  The bore is
    # in the left arm: the known forward crossings are x=2, 4 and 6.
    outline = [(-5, -5), (6, -5), (6, 5), (4, 5), (4, -2),
               (2, -2), (2, 5), (-5, 5)]
    member = _prism_member(outline, _own_bore(radius=0.75))
    row = _query(member, [0.0, 0.0, 0.0], [1.0, 0.0, 0.0])
    # Add the redundant authenticated-register signatures needed by the
    # independent parser, without changing the fixture's analytic geometry.
    member["stock_frame"] = {"basis_columns_global_xyz": [[1, 0, 0], [0, 1, 0], [0, 0, 1]]}
    for feature in member["features"]:
        feature["trim"]["edge_count"] = sum(len(wire["edges"]) for wire in feature["trim"]["wires"])
        if feature["surface_kind"] == "PLANE":
            plane = feature["plane"]
            plane["stock_origin_global_xyz_mm"] = [0, 0, 0]
            plane["signed_plane_offset_stock_mm"] = plane["signed_plane_station_global_mm"]
            plane["normal_stock_gqr"] = plane["normal_global_xyz"]
    expected = oracle._ray(oracle._parse_member(member), OWN_ID, [0.0, 0.0, 0.0], [1.0, 0.0, 0.0])

    for result in (row, expected):
        assert result["status"] == "ok"
        assert [event["distance_mm"] for event in result["events"]] == pytest.approx([2.0, 4.0, 6.0])
        assert [event["entry_or_exit"] for event in result["events"]] == ["exit", "entry", "exit"]
        assert result["first_material_exit"]["distance_mm"] == pytest.approx(2.0)
        assert result["first_exterior_exit"]["distance_mm"] == pytest.approx(2.0)
    oracle.compare(row["events"], expected["events"], "complete synthetic trace")
    with pytest.raises(oracle.OracleError, match="array length/schema differs"):
        oracle.compare(row["events"][:1], expected["events"], "truncated synthetic trace")


def test_tangent_bore_event_is_explicit_ambiguity_with_null_distance():
    tangent = {"id": "other/tangent", "center": [5.0, 1.0, 0.0], "radius": 1.0,
               "axis": [0.0, 0.0, 1.0], "interval": [-5.0, 5.0]}
    member = _box_member([_own_bore(), tangent])
    row = _query(member, [0.0, 0.0, 0.0], [1.0, 0.0, 0.0])

    event = next(event for event in row["events"] if event["feature_id"] == "other/tangent")
    assert row["status"] == "ambiguous"
    assert row["origin_membership"]["status"] == "ambiguous"
    assert event["distance_mm"] == pytest.approx(5.0)
    assert event["entry_or_exit"] == "tangent"
    assert event["tangent"] is True
    assert row["first_exterior_exit"] is None
    assert row["distance_mm"] is None


def test_simultaneous_box_corner_crossing_is_ambiguous_and_keeps_grouped_event():
    member = _box_member([_own_bore()], bounds=(-5.0, 10.0, -5.0, 10.0, -5.0, 5.0))
    direction = [1.0 / math.sqrt(2.0), 1.0 / math.sqrt(2.0), 0.0]
    row = _query(member, [0.0, 0.0, 0.0], direction)

    corner = next(event for event in row["events"] if len(event["feature_ids"]) > 1)
    assert row["status"] == "ambiguous"
    assert corner["distance_mm"] == pytest.approx(10.0 * math.sqrt(2.0))
    assert set(corner["feature_ids"]) == {"box/x+", "box/y+"}
    assert corner["corner_ambiguity"] is True
    assert row["first_exterior_exit"] is None
    assert row["distance_mm"] is None


@pytest.mark.parametrize(
    ("origin", "reason_fragment"),
    [([0.25, 0.0, 0.0], "off the synthetic/own-bore bore centerline"),
     ([0.0, 0.0, 5.5], "outside the saved finite synthetic/own-bore bore interval")],
)
def test_origin_must_lie_on_mapped_finite_bore_axis(origin, reason_fragment):
    member = _box_member([_own_bore()])
    row = _query(member, origin, [1.0, 0.0, 0.0])
    assert row["status"] == "unsupported"
    assert row["distance_mm"] is None
    assert reason_fragment in row["reason"]


def test_partial_arc_and_inconsistent_saved_edge_signature_are_refused():
    member = _box_member([_own_bore()])
    partial = copy.deepcopy(member)
    own = next(feature for feature in partial["features"] if feature["feature_id"] == OWN_ID)
    own["trim"]["surface_parameter_bounds"]["u"] = [0.0, math.pi]
    partial_result = _query(partial, [0.0, 0.0, 0.0], [1.0, 0.0, 0.0])
    assert partial_result["status"] == "unsupported"
    assert "partial-turn" in partial_result["reason"]

    inconsistent = copy.deepcopy(member)
    plane = next(feature for feature in inconsistent["features"] if feature["feature_id"] == "box/x+")
    plane["trim"]["wires"][0]["edges"][0]["parameter_endpoint_global_xyz_mm"][0][1] += 0.25
    invalid_result = _query(inconsistent, [0.0, 0.0, 0.0], [1.0, 0.0, 0.0])
    assert invalid_result["status"] == "unsupported"
    assert "LINE endpoints disagree" in invalid_result["reason"]


def test_saved_current_surface_signature_matches_independent_numeric_oracle():
    records = method.load_authenticated_surface_records()
    member = records["base_floor_left"]
    # This authenticated receiver's ray is the global +y direction from the
    # saved bore center (-1238.25, 1551, 69).  Its first crossing is facet003.
    # The independently reconstructed plane intersection is 71.95185978252302 mm.
    row = _query(member, [-1238.25, 1551.0, 69.0], [0.0, 1.0, 0.0],
                 own_id="base_floor_left/facet007")

    assert row["status"] == "ok"
    assert row["origin_membership"]["status"] == "inside_filled_own_bore"
    assert row["first_material_exit"]["feature_id"] == "base_floor_left/facet003"
    assert row["first_exterior_exit"]["feature_id"] == "base_floor_left/facet003"
    assert row["distance_mm"] == pytest.approx(71.95185978252302, abs=1.0e-9)


def test_signed_component_selector_reverses_sign_and_preserves_zero_crossing():
    basis = [1.0, 0.0, 0.0]
    positive = producer.signed_selection([5.0, 0.0, 0.0], [0.2, 0.1, 0.1], basis, "g")
    negative = producer.signed_selection([-5.0, 0.0, 0.0], [0.2, 0.1, 0.1], basis, "g")
    crossing = producer.signed_selection([0.5, 0.0, 0.0], [0.5, 0.0, 0.0], basis, "g")

    assert positive["interval_n"] == pytest.approx([4.8, 5.2])
    assert positive["sign"] == 1 and positive["direction_name"] == "g+"
    assert negative["interval_n"] == pytest.approx([-5.2, -4.8])
    assert negative["sign"] == -1 and negative["direction_name"] == "g-"
    assert crossing["interval_n"] == pytest.approx([0.0, 1.0])
    assert crossing["sign"] is None
    assert crossing["selection_status"] == "sign_interval_contains_zero"
    assert crossing["direction_name"] is None


def test_current_receiver_query_state_census_keeps_geometry_and_applicability_distinct(frozen_upstream_inputs):
    report = producer.produce(*UPSTREAM_REPORT_PATHS)

    assert report["counts"]["retained_axes"] == 12
    assert report["counts"]["receiver_memberships"] == 24
    assert report["counts"]["finished_members"] == 8
    assert report["counts"]["directional_queries"] == 288
    assert report["counts"]["query_statuses"] == {"ok": 288, "ambiguous": 0, "unsupported": 0}
    assert report["counts"]["signed_bolt_states"] == 252
    assert report["counts"]["signed_receiver_states"] == 504
    assert report["counts"]["signed_component_selections"] == 1008
    assert len(report["memberships"]) == 24
    assert len(report["queries"]) == 288
    assert len(report["receiver_state_rows"]) == 504
    assert len({(row["case_id"], row["increment_index"], row["axis_id"], row["receiver_side"])
                for row in report["receiver_state_rows"]}) == 504

    assert all(member["through_depth_minimum_mm"] is None for member in report["memberships"].values())
    assert all(query["through_depth_minimum_mm"] is None for query in report["queries"].values())
    assert all(query["stock_box_role"].startswith("separate proposed envelope locator")
               for query in report["queries"].values())
    assert any(abs(query["stock_box_distance_mm"] - query["finished_geometry"]["distance_mm"]) > 1.0e-6
               for query in report["queries"].values())
    assert all(row["Cdelta"] is None and row["Cg"] is None
               and row["splitting_acceptance"] is None
               and row["through_depth_minimum_mm"] is None
               and row["joint_accepted"] is False
               for row in report["receiver_state_rows"])
    assert report["criteria_status"] == "all_47_pending_unchanged"
    assert report["engineering_mvp_complete"] is False
    assert report["joint_accepted"] is False and report["fabrication_release"] is False


@pytest.mark.parametrize("status", ["ambiguous", "unsupported"])
def test_producer_preserves_null_finished_distances_through_signed_selection(
    frozen_upstream_inputs, monkeypatch, status,
):
    load, surfaces, manifest, _ = frozen_upstream_inputs
    refused = {"status": status, "events": [], "first_material_exit": None,
               "first_exterior_exit": None, "distance_mm": None}
    # Inject the method's refusal contract at the assembly boundary. Every
    # named ray refuses, so all selected signed candidates must preserve NULL.
    injected_method = SimpleNamespace(query_member_direction=lambda *args: copy.deepcopy(refused))
    monkeypatch.setattr(producer, "checked_inputs", lambda *args: (load, surfaces, manifest, injected_method))
    report = producer.produce(*UPSTREAM_REPORT_PATHS)

    assert report["counts"]["query_statuses"][status] == 288
    assert report["counts"]["query_statuses"]["ok"] == 0
    assert report["counts"]["unresolved_component_signs"] == 0
    for query in report["queries"].values():
        assert query["finished_geometry"]["distance_mm"] is None
        assert query["finished_geometry"]["first_exterior_exit"] is None
        assert query["grain_normal_planar_boundary"] is None
        assert math.isfinite(query["stock_box_distance_mm"])
    candidates = [candidate for row in report["receiver_state_rows"]
                  for candidate in row["loaded_direction_geometric_candidates"].values()]
    assert len(candidates) == 1008
    for candidate in candidates:
        assert candidate["direction_name"] is not None
        for sample in candidate["samples"].values():
            assert sample["query_id"] is not None
            assert sample["finished_exterior_distance_mm"] is None
            assert sample["first_material_exit_distance_mm"] is None


def test_output_alias_guard_rejects_producer_script_path_before_writing():
    stub_report = {"source_pins": {}, "rechecked_load_input_pins": {}}
    argv = ["produce.py", "--output", str(Path(producer.__file__).resolve())]
    with (patch.object(producer, "produce", return_value=stub_report),
          patch.object(sys, "argv", argv),
          pytest.raises(ValueError, match="output aliases an input")):
        producer.main()


def _existing_alias(target, alias, kind):
    if kind == "same":
        return target
    if kind == "hardlink":
        alias.hardlink_to(target)
    else:
        alias.symlink_to(target)
    return alias


def _reviewed_oracle_args():
    return ["--expected-oracle-sha256", hashlib.sha256(Path(oracle.__file__).read_bytes()).hexdigest()]


@pytest.mark.parametrize("kind", ["same", "symlink", "hardlink"])
def test_producer_cli_rejects_inode_and_path_aliases_without_truncation(tmp_path, monkeypatch, kind):
    source = tmp_path / "load.json"
    original = b"protected load bytes\n"
    source.write_bytes(original)
    output = _existing_alias(source, tmp_path / "alias.json", kind)
    stub_report = {"source_pins": {}, "rechecked_load_input_pins": {}, "counts": {}}
    monkeypatch.setattr(producer, "produce", lambda *args: stub_report)
    monkeypatch.setattr(sys, "argv", ["produce.py", "--load-report", str(source), "--output", str(output)])

    with pytest.raises(ValueError, match="output aliases an input"):
        producer.main()
    assert source.read_bytes() == original
    assert output.read_bytes() == original


@pytest.mark.parametrize("kind", ["same", "symlink", "hardlink"])
@pytest.mark.parametrize("target_name", ["report", "pinned_source"])
def test_oracle_cli_rejects_report_and_source_aliases_without_truncation(
    tmp_path, monkeypatch, capsys, kind, target_name,
):
    report_path = tmp_path / "report.json"
    source = tmp_path / "protected-source.txt"
    report_bytes = b"protected report bytes\n"
    source_bytes = b"protected source bytes\n"
    report_path.write_bytes(report_bytes)
    source.write_bytes(source_bytes)
    target = report_path if target_name == "report" else source
    output = _existing_alias(target, tmp_path / "alias.json", kind)
    stub_report = {"source_pins": {source.name: {}}, "rechecked_load_input_pins": {}}
    stub_receipt = {"receipt_sha256": "stub", "report_sha256": "stub", "verification": {}}
    monkeypatch.setattr(oracle, "ROOT", tmp_path)
    monkeypatch.setattr(oracle, "verify_report", lambda *args: stub_receipt)
    monkeypatch.setattr(oracle, "read_json", lambda *args: (stub_report, report_bytes))
    # A bypassed guard must reach the real write, rather than fail on a stub's
    # missing numerical fields before exercising the regression.
    monkeypatch.setattr(oracle, "_seal_receipt", lambda value: value)
    monkeypatch.setattr(sys, "argv", ["raw_oracle.py", "--report", str(report_path),
                                     "--expected-report-sha256", "0" * 64, "--output", str(output),
                                     *_reviewed_oracle_args()])

    assert oracle.main() == 2
    assert "output aliases" in capsys.readouterr().err
    assert report_path.read_bytes() == report_bytes
    assert source.read_bytes() == source_bytes


@pytest.mark.parametrize("tool", ["producer", "oracle"])
@pytest.mark.parametrize("kind", ["same", "symlink", "hardlink"])
def test_cli_protects_unpinned_packet_evidence_files(tmp_path, monkeypatch, capsys, tool, kind):
    here = tmp_path / "owned-packet"
    here.mkdir()
    source = here / "validation.md"
    original = b"independent validation evidence\n"
    source.write_bytes(original)
    output = _existing_alias(source, tmp_path / "alias.json", kind)
    stub_report = {"source_pins": {}, "rechecked_load_input_pins": {}, "counts": {}}
    module = producer if tool == "producer" else oracle
    monkeypatch.setattr(module, "HERE", here)
    if tool == "producer":
        monkeypatch.setattr(producer, "produce", lambda *args: stub_report)
        monkeypatch.setattr(sys, "argv", ["produce.py", "--output", str(output)])
        with pytest.raises(ValueError, match="output aliases an input"):
            producer.main()
    else:
        stub_receipt = {"receipt_sha256": "stub", "report_sha256": "stub", "verification": {}}
        monkeypatch.setattr(oracle, "verify_report", lambda *args: stub_receipt)
        monkeypatch.setattr(oracle, "read_json", lambda *args: (stub_report, b"{}"))
        monkeypatch.setattr(oracle, "_seal_receipt", lambda value: value)
        monkeypatch.setattr(sys, "argv", ["raw_oracle.py", "--expected-report-sha256", "0" * 64,
                                         "--output", str(output), *_reviewed_oracle_args()])
        assert oracle.main() == 2
        assert "output aliases" in capsys.readouterr().err
    assert source.read_bytes() == original


@pytest.mark.parametrize("mode", ["report", "receipt"])
@pytest.mark.parametrize("pin", [None, "0" * 64])
def test_oracle_cli_refuses_missing_or_foreign_reviewed_code_pin_before_replay(
    tmp_path, monkeypatch, capsys, mode, pin,
):
    def unexpected_replay(*args):
        pytest.fail("code pin must be checked before opening or replaying an artifact")

    monkeypatch.setattr(oracle, "verify_report", unexpected_replay)
    monkeypatch.setattr(oracle, "verify_receipt", unexpected_replay)
    argv = ["raw_oracle.py"]
    if mode == "receipt":
        argv += ["--check-receipt", str(tmp_path / "unopened-receipt.json")]
    else:
        argv += ["--expected-report-sha256", "0" * 64, "--output", str(tmp_path / "output.json")]
    if pin is not None:
        argv += ["--expected-oracle-sha256", pin]
    monkeypatch.setattr(sys, "argv", argv)

    assert oracle.main() == 2
    message = capsys.readouterr().err
    assert ("requires the reviewed" if pin is None else "externally supplied reviewed digest") in message
    assert not (tmp_path / "output.json").exists()


def test_changed_source_pin_is_rejected_before_frozen_reports_are_opened(tmp_path, monkeypatch):
    root = tmp_path / "root"
    here = root / "owned"
    root.mkdir()
    here.mkdir()
    pinned = root / "mutable-source.txt"
    pinned.write_bytes(b"frozen source")
    pin = {"sha256": hashlib.sha256(pinned.read_bytes()).hexdigest(), "size_bytes": pinned.stat().st_size}
    manifest_bytes = json.dumps({"pins": {"mutable-source.txt": pin}}, sort_keys=True).encode()
    (here / "source-pins.json").write_bytes(manifest_bytes)
    monkeypatch.setattr(producer, "HERE", here)
    monkeypatch.setattr(producer, "ROOT", root)
    monkeypatch.setattr(producer, "MANIFEST_SHA", hashlib.sha256(manifest_bytes).hexdigest())
    pinned.write_bytes(b"mutated source")

    with pytest.raises(ValueError, match="changed source: mutable-source.txt"):
        producer.checked_inputs(Path("not-opened-load.json"), Path("not-opened-raw.json"),
                                Path("not-opened-resistance.json"))
