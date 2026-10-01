"""Conditional connector laws for the frozen reduced wood-joint model.

This is a property producer, not an accepted response model.  It binds the
attempt01 six-case input packet and emits one lateral spring group per actual
wood/wood shear plane, one axial tie per physical through-bolt, and lateral-
only Hillman screw groups.  In particular, the four three-receiver axes stay
four bolts: each has two lateral planes and exactly one outer-seat axial tie.

The lateral values are EC5 service-slip comparisons, not strengths.  Bolt
outer-seat axial values are explicit elastic scenarios using modeled steel
geometry and an idealized local washer-bearing wood column.  No Hillman axial
law is available here; its axial value is intentionally null and blocks a
six-case response run until a supported tension path is supplied.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib
import json
import math
import sys
from collections import Counter
from itertools import pairwise
from pathlib import Path
from typing import Any

import cadquery as cq

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

reduced_material_binder = importlib.import_module("fea.wood_joint_reduced_materials")


DEFAULT_MODEL_INPUTS = (
    ROOT
    / "docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28"
    / "reduced-static-attempt01/model-inputs.json"
)
MATERIAL_SCENARIOS = ROOT / "docs/wood-joints-mvp/current-material-scenarios.md"
PANEL_WITHDRAWAL_PREFLIGHT = (
    ROOT
    / "docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28"
    / "panel-withdrawal-preflight.md"
)

SWEDISH_WOOD_JOINT_SLIP_URL = (
    "https://www.swedishwood.com/siteassets/5-publikationer/pdfer/"
    "sw-design-of-timber-structures-vol2-2022.pdf"
)
HILLMAN_42605_PRODUCT_URL = (
    "https://www.lowes.com/pd/Hillman-10-x-2-1-2-in-Ceramic-Deck-Screws-"
    "50-Count/999995042"
)
ASME_WOOD_SCREW_STANDARD_URL = (
    "https://www.asme.org/codes-standards/find-codes-standards/"
    "b18-6-1-wood-screws"
)

# Conditional model inputs only. The timber and plywood density values are
# model proxies, not measurements of delivered stock or panels.
TIMBER_MEAN_DENSITY_KG_M3 = 500.0
PANEL_MEAN_DENSITY_KG_M3 = 600.0
DENSITY_SENSITIVITY_KG_M3 = (400.0, 500.0, 600.0)
TRANSVERSE_WOOD_E_MPA = {"T_soft": 551.6, "R_stiff": 750.176}
STEEL_E_SENSITIVITY_MPA = (190000.0, 200000.0, 210000.0)
WOOD_COLUMN_DEPTH_FACTORS = (0.5, 1.0, 2.0)
HILLMAN_SIZE_10_MAJOR_DIAMETER_IN = 0.190
INCH_MM = 25.4

AXIS_LINE_TOLERANCE_MM = 1.0e-5
AXIS_ANGLE_TOLERANCE_DEG = 1.0e-5
RADIUS_TOLERANCE_MM = 1.0e-6
INTERVAL_TOLERANCE_MM = 1.0e-5


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _dot(a: list[float], b: list[float]) -> float:
    return sum(x * y for x, y in zip(a, b, strict=True))


def _norm(vector: list[float]) -> float:
    return math.sqrt(_dot(vector, vector))


def _unit(vector: list[float]) -> list[float]:
    magnitude = _norm(vector)
    if not math.isfinite(magnitude) or magnitude <= 0.0:
        raise ValueError("Expected a finite nonzero axis vector")
    return [value / magnitude for value in vector]


def _add(a: list[float], b: list[float]) -> list[float]:
    return [x + y for x, y in zip(a, b, strict=True)]


def _scale(vector: list[float], scalar: float) -> list[float]:
    return [scalar * value for value in vector]


def _distance(a: list[float], b: list[float]) -> float:
    return _norm([x - y for x, y in zip(a, b, strict=True)])


def _kser(rho_mean_kg_m3: float, diameter_mm: float) -> float:
    """EC5 lateral service-slip modulus per fastener per shear plane."""
    if rho_mean_kg_m3 <= 0.0 or diameter_mm <= 0.0:
        raise ValueError("Kser inputs must be positive")
    return rho_mean_kg_m3**1.5 * diameter_mm / 23.0


def _effective_orthotropic_modulus(
    axis_xyz: list[float], material_axes: dict[str, list[float]], constants_mpa: tuple[float, ...]
) -> tuple[float, list[float]]:
    """Return uniaxial-stress Young's modulus along a global axis.

    The compliance is transformed from the pinned L/R/T material frame by
    resolving a uniaxial stress along the bolt axis. This is a local seat
    scenario, not the surrounding member's full contact state.
    """
    e_l, e_r, e_t, nu_lr, nu_lt, nu_rt, g_lr, g_lt, g_rt = constants_mpa
    direction = _unit(axis_xyz)
    components = [
        _dot(direction, _unit(material_axes[name])) for name in ("L", "R", "T")
    ]
    l, r, t = components
    compliance = (
        l**4 / e_l
        + r**4 / e_r
        + t**4 / e_t
        + l**2 * r**2 * (1.0 / g_lr - 2.0 * nu_lr / e_l)
        + l**2 * t**2 * (1.0 / g_lt - 2.0 * nu_lt / e_l)
        + r**2 * t**2 * (1.0 / g_rt - 2.0 * nu_rt / e_r)
    )
    if not math.isfinite(compliance) or compliance <= 0.0:
        raise ValueError("Orthotropic seat compliance must be positive and finite")
    return 1.0 / compliance, components


def _load_member_material_scenarios(
    model: dict[str, Any], verified_sources: dict[str, str]
) -> dict[str, dict[str, Any]]:
    """Read the same pinned L/R/T proposals used by the reduced material binder."""
    relative_path = model.get("member_geometry_artifact")
    if not isinstance(relative_path, str):
        raise TypeError("Reduced input packet does not identify member geometry")
    geometry_path = (ROOT / relative_path).resolve()
    expected_geometry_hash = model["source_sha256"].get(relative_path)
    if expected_geometry_hash is None or _sha256(geometry_path) != expected_geometry_hash:
        raise ValueError("Pinned reduced member geometry changed")
    geometry_doc = json.loads(geometry_path.read_text(encoding="utf-8"))
    if geometry_doc.get("geometry_revision_id") != model.get("revision_id"):
        raise ValueError("Reduced material frames belong to a different geometry revision")

    timber_map, timber_path, timber_hash = reduced_material_binder._source_map(
        geometry_doc, "timber_material_map"
    )
    block_map, block_path, block_hash = reduced_material_binder._source_map(
        geometry_doc, "block_material_map"
    )
    verified_sources[timber_path] = timber_hash
    verified_sources[block_path] = block_hash

    timber_rows = {row["member_id"]: row for row in timber_map["members"]}
    block_rows = {row["part_id"]: row for row in block_map["members"]}
    frame_constants = tuple(reduced_material_binder.response_materials(panel_group_factor=1.0)["timber"])
    block_constants = tuple(
        reduced_material_binder.block_material_scenario()["calculix_engineering_constants"]
    )
    result: dict[str, dict[str, Any]] = {}
    for descriptor in geometry_doc["members"]:
        member_id = descriptor["name"]
        if descriptor["member_kind"] == "timber":
            map_row = timber_rows[member_id]
            cases = reduced_material_binder._timber_ring_alternatives(map_row)
            constants = frame_constants
            map_path = timber_path
        elif descriptor["member_kind"] == "candidate_block":
            map_row = block_rows[member_id]
            cases = reduced_material_binder._block_ring_alternatives(map_row)
            constants = block_constants
            map_path = block_path
        else:
            raise ValueError(f"Unsupported reduced wood member kind: {descriptor['member_kind']}")
        grain = _unit(descriptor["grain_global_xyz"])
        options = []
        for case in cases:
            axes = {
                label: _unit(case["material_axes_global_xyz"][label])
                for label in ("L", "R", "T")
            }
            if abs(_dot(grain, axes["L"])) < 1.0 - 1.0e-7:
                raise ValueError(f"{member_id}: pinned material L axis disagrees with reduced grain")
            options.append(
                {
                    "scenario_id": case["scenario_id"],
                    "source_basis": case["source_basis"],
                    "material_axes_global_xyz": axes,
                }
            )
        if len(options) != 2:
            raise ValueError(f"{member_id}: require two pinned transverse-frame alternatives")
        result[member_id] = {
            "member_kind": descriptor["member_kind"],
            "grain_axis_global_xyz": grain,
            "material_constants_mpa": constants,
            "material_constants_basis": (
                "pinned current-response timber orthotropic elastic scenario" if descriptor["member_kind"] == "timber"
                else "pinned proposal-only block orthotropic elastic diagnostic"
            ),
            "material_map": map_path,
            "frame_scenarios": options,
        }

    for relative in (
        "fea/wood_joint_reduced_materials.py",
        "fea/current_response_materials.py",
        "fea/wood_joint_patch_materials.py",
        "docs/wood-joints-mvp/orthotropic-material-scenario.md",
    ):
        verified_sources[relative] = _sha256(ROOT / relative)
    return result


def _load_pinned_inputs(path: Path) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], dict[str, str]]:
    path = path.resolve()
    model = json.loads(path.read_text(encoding="utf-8"))
    if model.get("schema") != "wood_joint_reduced_static_preparation/v1":
        raise ValueError("Unexpected reduced-static preparation schema")
    if model.get("candidate") != "compact-floor-flush-wood-joints-development":
        raise ValueError("Unexpected wood-joint candidate")
    if model.get("mechanical_acceptance") is not False or model.get("native_solve_run") is not False:
        raise ValueError("Reduced properties require unaccepted, unsolved inputs")

    verified: dict[str, str] = {str(path.relative_to(ROOT)): _sha256(path)}
    for source, expected in model["source_sha256"].items():
        source_path = ROOT / source
        actual = _sha256(source_path)
        if actual != expected:
            raise ValueError(f"Pinned preparation source changed: {source}")
        verified[source] = actual

    topology_candidates = [
        source
        for source in model["source_sha256"]
        if source.endswith("current-mass-topology-map-attempt03/source-topology-map.json")
    ]
    if len(topology_candidates) != 1:
        raise ValueError("Expected one pinned current source-topology map")
    topology_path = topology_candidates[0]
    topology = json.loads((ROOT / topology_path).read_text(encoding="utf-8"))
    if topology.get("revision_id") != model.get("revision_id"):
        raise ValueError("Source-topology map revision differs from reduced inputs")

    # The topology export has its own transitive source pins. Check them before
    # using its component role/centroid map to derive washer seats and areas.
    for source, expected in topology["source_sha256"].items():
        source_path = ROOT / source
        actual = _sha256(source_path)
        if actual != expected:
            raise ValueError(f"Pinned topology source changed: {source}")
        verified[source] = actual

    centroid_candidates = [
        source
        for source in topology["source_sha256"]
        if source.endswith("current-mass-centroids-attempt01/mass-centroids.json")
    ]
    if len(centroid_candidates) != 1:
        raise ValueError("Expected one pinned source mass-centroid inventory")
    centroids_path = centroid_candidates[0]
    centroids = json.loads((ROOT / centroids_path).read_text(encoding="utf-8"))
    if centroids.get("revision_id") != model.get("revision_id"):
        raise ValueError("Source mass-centroid revision differs from reduced inputs")
    return model, topology, centroids, verified


def _component_maps(topology: dict[str, Any], centroids: dict[str, Any]) -> tuple[dict[tuple[str, str], dict[str, Any]], dict[str, dict[str, Any]]]:
    components: dict[tuple[str, str], dict[str, Any]] = {}
    for row in topology["physical_mass_rows"]:
        entity = row["source_mass_entity"]
        axis_id, role = entity.get("axis_id"), entity.get("component_role")
        if axis_id and role:
            key = (axis_id, role)
            if key in components:
                raise ValueError(f"Duplicate physical component role: {key}")
            components[key] = row

    source_rows = {row["name"]: row for row in centroids["rows"]}
    if len(source_rows) != len(centroids["rows"]):
        raise ValueError("Source mass-centroid names are not unique")
    return components, source_rows


def _washer_component(
    axis_id: str,
    role: str,
    components: dict[tuple[str, str], dict[str, Any]],
    source_rows: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    row = components.get((axis_id, role))
    if row is None:
        raise ValueError(f"Missing modeled {role} component for {axis_id}")
    source = source_rows.get(row["inventory_name"])
    if source is None or source.get("volume_mm3") is None:
        raise ValueError(f"Missing modeled component volume for {axis_id}/{role}")
    return {
        "axis_id": axis_id,
        "role": role,
        "center_xyz_mm": list(row["mass_center_global_xyz_mm"]),
        "modeled_volume_mm3": float(source["volume_mm3"]),
        "inventory_name": row["inventory_name"],
    }


def _member_shapes(model: dict[str, Any]) -> tuple[dict[str, dict[str, Any]], dict[str, cq.Shape]]:
    members = {row["member_id"]: row for row in model["members"]}
    shapes: dict[str, cq.Shape] = {}
    return members, shapes


def _cylinder_face_records(shape: cq.Shape) -> list[dict[str, Any]]:
    from OCP.BRepTools import BRepTools

    rows = []
    for face_index, face in enumerate(shape.Faces()):
        if face.geomType() != "CYLINDER":
            continue
        cylinder = face._geomAdaptor().Cylinder()
        axis = cylinder.Axis()
        location = axis.Location()
        direction = axis.Direction()
        rows.append(
            {
                "face_index": face_index,
                "radius_mm": float(cylinder.Radius()),
                "line_point_xyz_mm": [location.X(), location.Y(), location.Z()],
                "axis_xyz": _unit([direction.X(), direction.Y(), direction.Z()]),
                "uv_bounds": list(BRepTools.UVBounds_s(face.wrapped)),
            }
        )
    return rows


def _axis_line_offset(point: list[float], axis: list[float], other: list[float]) -> float:
    delta = [x - y for x, y in zip(other, point, strict=True)]
    along = _dot(delta, axis)
    return _norm([value - along * direction for value, direction in zip(delta, axis, strict=True)])


def _measure_retained_holes(
    retained: list[dict[str, Any]], model: dict[str, Any]
) -> dict[tuple[str, str], dict[str, Any]]:
    members, shape_cache = _member_shapes(model)
    measured: dict[tuple[str, str], dict[str, Any]] = {}
    for connection in retained:
        axis_id = connection["axis_id"]
        axis = _unit(connection["axis_xyz"])
        point = [float(value) for value in connection["source_point_xyz_mm"]]
        diameter = float(connection["source_record"]["source_occupied_diameter_mm"])
        for receiver in connection["receiver_member_ids"]:
            member = members[receiver]
            binding = member["current_finished_step_binding"]
            step_path = ROOT / binding["path"]
            actual_hash = _sha256(step_path)
            if actual_hash != binding["file_sha256"]:
                raise ValueError(f"Pinned retained receiver STEP changed: {receiver}")
            if receiver not in shape_cache:
                shape = cq.importers.importStep(str(step_path)).val()
                solids = shape.Solids()
                if len(solids) != 1 or not solids[0].isValid():
                    raise ValueError(f"Retained receiver STEP must contain one valid solid: {receiver}")
                shape_cache[receiver] = solids[0]
            matches = []
            for face in _cylinder_face_records(shape_cache[receiver]):
                cosine = min(1.0, max(-1.0, abs(_dot(axis, face["axis_xyz"]))))
                angle = math.degrees(math.acos(cosine))
                offset = _axis_line_offset(point, axis, face["line_point_xyz_mm"])
                if angle <= AXIS_ANGLE_TOLERANCE_DEG and offset <= AXIS_LINE_TOLERANCE_MM:
                    v0, v1 = face["uv_bounds"][2:4]
                    axial_ends = [
                        _dot(
                            [
                                face["line_point_xyz_mm"][index]
                                + station * face["axis_xyz"][index]
                                - point[index]
                                for index in range(3)
                            ],
                            axis,
                        )
                        for station in (v0, v1)
                    ]
                    matches.append(
                        {
                            **face,
                            "axis_error_deg": angle,
                            "axis_line_offset_mm": offset,
                            "axis_interval_from_source_point_mm": [
                                min(axial_ends), max(axial_ends)
                            ],
                        }
                    )
            clusters: list[list[dict[str, Any]]] = []
            for face in sorted(matches, key=lambda row: row["radius_mm"]):
                if not clusters or face["radius_mm"] - clusters[-1][0]["radius_mm"] > RADIUS_TOLERANCE_MM:
                    clusters.append([face])
                else:
                    clusters[-1].append(face)
            if len(clusters) != 1:
                raise ValueError(
                    f"Expected one coaxial retained bore radius at {axis_id}/{receiver}; "
                    f"found {len(clusters)}"
                )
            radius = sum(row["radius_mm"] for row in clusters[0]) / len(clusters[0])
            gap = radius - diameter / 2.0
            if gap <= 0.0:
                raise ValueError(f"Nonpositive modeled bore clearance at {axis_id}/{receiver}")
            measured[(axis_id, receiver)] = {
                "receiver_id": receiver,
                "step_path": binding["path"],
                "step_sha256": actual_hash,
                "shaft_diameter_mm": diameter,
                "coaxial_bore_radius_mm": radius,
                "centered_radial_gap_mm": gap,
                "matching_cylindrical_face_count": len(clusters[0]),
                "axis_interval_from_source_point_mm": [
                    min(face["axis_interval_from_source_point_mm"][0] for face in clusters[0]),
                    max(face["axis_interval_from_source_point_mm"][1] for face in clusters[0]),
                ],
                "source": "current finished receiver STEP cylindrical faces",
            }
    return measured


def _retained_interface(
    connection: dict[str, Any],
    measured: dict[tuple[str, str], dict[str, Any]],
) -> dict[str, Any]:
    """Locate the current retained wood/wood boundary from each STEP bore span."""
    axis_id = connection["axis_id"]
    axis = _unit(connection["axis_xyz"])
    origin = [float(value) for value in connection["source_point_xyz_mm"]]
    spans = []
    for receiver in connection["receiver_member_ids"]:
        record = measured[(axis_id, receiver)]
        low, high = record["axis_interval_from_source_point_mm"]
        spans.append({"receiver_id": receiver, "lo_mm": low, "hi_mm": high})
    spans.sort(key=lambda row: (row["lo_mm"], row["hi_mm"], row["receiver_id"]
                                ))
    if len(spans) != 2:
        raise ValueError(f"{axis_id}: retained physical bolt must join two receivers")
    gap_or_overlap = spans[1]["lo_mm"] - spans[0]["hi_mm"]
    if abs(gap_or_overlap) <= INTERVAL_TOLERANCE_MM:
        boundary_station = (spans[0]["hi_mm"] + spans[1]["lo_mm"]) / 2.0
        point = _add(origin, _scale(axis, boundary_station))
        point_status = "resolved_current_finished_STEP_coaxial_bore_interval_boundary"
    else:
        boundary_station = None
        point = list(origin)
        point_status = "unresolved_source_reference_only_not_verified_wood_interface"
    return {
        "receiver_member_ids_head_to_nut": [row["receiver_id"] for row in spans],
        "receiver_span_records": spans,
        "boundary_gap_or_overlap_mm": gap_or_overlap,
        "interface_axis_coordinate_from_source_point_mm": boundary_station,
        "interface_point_xyz_mm": point,
        "point_status": point_status,
        "source": "pinned current finished STEP coaxial bore axial intervals; requires coincident receiver boundary",
    }


def _candidate_spans(connection: dict[str, Any]) -> tuple[list[dict[str, Any]], list[float], list[float]]:
    geometry = connection["source_record"]["geometry"]
    axis = _unit(geometry["axis_head_to_nut_global"])
    center = [float(value) for value in geometry["shaft_center_global_xyz_mm"]]
    length = float(geometry["modeled_underhead_to_tip_mm"])
    underhead = [p - length * a / 2.0 for p, a in zip(center, axis, strict=True)]
    spans = []
    for receiver in geometry["wood_receiver_intervals"]:
        intervals = receiver["current_shaft_intersection_solid_intervals_from_underhead_mm"]
        if len(intervals) != 1:
            raise ValueError(f"{connection['axis_id']}: require one interval per receiver")
        lo, hi = map(float, intervals[0])
        spans.append({"lo_mm": lo, "hi_mm": hi, "receiver_id": receiver["receiver_id"]})
    spans.sort(key=lambda row: (row["lo_mm"], row["hi_mm"], row["receiver_id"]))
    if not spans or any(
        abs(second["lo_mm"] - first["hi_mm"]) > INTERVAL_TOLERANCE_MM
        for first, second in pairwise(spans)
    ):
        raise ValueError(f"{connection['axis_id']}: noncontiguous receiver stack")
    return spans, axis, underhead


def _candidate_axial_geometry(
    connection: dict[str, Any],
    components: dict[tuple[str, str], dict[str, Any]],
    source_rows: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    axis_id = connection["axis_id"]
    geometry = connection["source_record"]["geometry"]
    spans, axis, underhead = _candidate_spans(connection)
    first, last = spans[0], spans[-1]
    head_washer = _washer_component(axis_id, "head_washer", components, source_rows)
    nut_washer = _washer_component(axis_id, "nut_washer", components, source_rows)
    head_station = _dot(
        [x - y for x, y in zip(head_washer["center_xyz_mm"], underhead, strict=True)], axis
    )
    nut_station = _dot(
        [x - y for x, y in zip(nut_washer["center_xyz_mm"], underhead, strict=True)], axis
    )
    thickness_head = 2.0 * abs(head_station)
    thickness_nut = 2.0 * abs(last["hi_mm"] - nut_station)
    if min(thickness_head, thickness_nut) <= 0.0 or abs(thickness_head - thickness_nut) > 1.0e-5:
        raise ValueError(f"{axis_id}: washer thicknesses do not reconcile with raw outer faces")
    thickness = (thickness_head + thickness_nut) / 2.0
    head_area = head_washer["modeled_volume_mm3"] / thickness
    nut_area = nut_washer["modeled_volume_mm3"] / thickness
    if abs(head_area - nut_area) > max(1.0e-5, head_area * 1.0e-6):
        raise ValueError(f"{axis_id}: modeled outer washer annulus areas differ")
    seat_first = _add(underhead, _scale(axis, first["lo_mm"]))
    seat_last = _add(underhead, _scale(axis, last["hi_mm"]))
    expected_members = [first["receiver_id"], last["receiver_id"]]
    if expected_members[0] == expected_members[1]:
        raise ValueError(f"{axis_id}: physical bolt requires two outer receiver bodies")
    return {
        "axis_head_to_nut_xyz": axis,
        "underhead_xyz_mm": underhead,
        "head_washer": head_washer,
        "nut_washer": nut_washer,
        "washer_thickness_mm": thickness,
        "washer_annular_bearing_area_mm2": (head_area + nut_area) / 2.0,
        "washer_area_method": "pinned CAD component volume divided by per-axis measured thickness",
        "outer_receiver_member_ids_head_to_nut": expected_members,
        "outer_seat_points_xyz_mm": [seat_first, seat_last],
        "receiver_span_records": spans,
        "seat_spacing_mm": _distance(seat_first, seat_last),
        "wood_grip_mm": float(geometry["wood_grip_material_length_mm"]),
        "modeled_shaft_diameter_mm": float(geometry["modeled_shaft_diameter_mm"]),
    }


def _retained_axial_geometry(
    connection: dict[str, Any],
    components: dict[tuple[str, str], dict[str, Any]],
    source_rows: dict[str, dict[str, Any]],
    measured: dict[tuple[str, str], dict[str, Any]],
) -> dict[str, Any]:
    axis_id = connection["axis_id"]
    record = connection["source_record"]
    origin = [float(value) for value in record["origin_global_xyz_mm"]]
    stored_axis = _unit(record["axis_global_xyz"])
    head_washer = _washer_component(axis_id, "head_washer", components, source_rows)
    nut_washer = _washer_component(axis_id, "nut_washer", components, source_rows)
    center_delta = [x - y for x, y in zip(nut_washer["center_xyz_mm"], head_washer["center_xyz_mm"], strict=True)]
    head_to_nut = _unit(center_delta)
    if _dot(stored_axis, head_to_nut) < 1.0 - 1.0e-8:
        raise ValueError(f"{axis_id}: modeled washer roles disagree with stored bolt axis")
    head_station = _dot(
        [x - y for x, y in zip(head_washer["center_xyz_mm"], origin, strict=True)], head_to_nut
    )
    thickness = 2.0 * abs(head_station)
    grip = float(record["source_grip_mm"])
    nut_station = _dot(
        [x - y for x, y in zip(nut_washer["center_xyz_mm"], origin, strict=True)], head_to_nut
    )
    if thickness <= 0.0 or abs(nut_station - (grip + 1.5 * thickness)) > 1.0e-5:
        raise ValueError(f"{axis_id}: modeled washer stations do not reconcile with source grip")
    head_area = head_washer["modeled_volume_mm3"] / thickness
    nut_area = nut_washer["modeled_volume_mm3"] / thickness
    if abs(head_area - nut_area) > max(1.0e-5, head_area * 1.0e-6):
        raise ValueError(f"{axis_id}: modeled outer washer annulus areas differ")
    seat_first = _add(origin, _scale(head_to_nut, thickness))
    seat_last = _add(origin, _scale(head_to_nut, thickness + grip))
    interface = _retained_interface(connection, measured)
    return {
        "axis_head_to_nut_xyz": head_to_nut,
        "underhead_xyz_mm": origin,
        "head_washer": head_washer,
        "nut_washer": nut_washer,
        "washer_thickness_mm": thickness,
        "washer_annular_bearing_area_mm2": (head_area + nut_area) / 2.0,
        "washer_area_method": "pinned CAD component volume divided by per-axis washer thickness inferred from component station geometry",
        "outer_receiver_member_ids_head_to_nut": interface["receiver_member_ids_head_to_nut"],
        "outer_seat_points_xyz_mm": [seat_first, seat_last],
        "receiver_span_records": interface["receiver_span_records"],
        "compression_contact_pairs": [
            {
                "receiver_member_ids": interface["receiver_member_ids_head_to_nut"],
                "compression_contact_required": True,
                "interface_point_xyz_mm": interface["interface_point_xyz_mm"],
                "interface_point_status": interface["point_status"],
                "boundary_gap_or_overlap_mm": interface["boundary_gap_or_overlap_mm"],
            }
        ],
        "receiver_interface_geometry": interface,
        "seat_spacing_mm": _distance(seat_first, seat_last),
        "wood_grip_mm": grip,
        "modeled_shaft_diameter_mm": float(record["source_occupied_diameter_mm"]),
        "axis_orientation_basis": "pinned modeled head/nut washer centroids plus sorted current STEP bore intervals",
    }


def _bolt_axial_law(
    connection: dict[str, Any],
    geometry: dict[str, Any],
    interfaces: list[dict[str, Any]],
    member_materials: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    diameter = geometry["modeled_shaft_diameter_mm"]
    bearing_area = geometry["washer_annular_bearing_area_mm2"]
    washer_t = geometry["washer_thickness_mm"]
    seat_spacing = geometry["seat_spacing_mm"]
    # Bolt stretch is taken over wood grip plus the two actual modeled washer
    # thicknesses. Head/nut, thread, bending, preload, and thread runout are not
    # modeled as additional steel compliance.
    steel_length = seat_spacing + 2.0 * washer_t
    steel_area = math.pi * diameter**2 / 4.0
    equivalent_washer_diameter = math.sqrt(4.0 * bearing_area / math.pi)

    def combined(
        wood_e_first_mpa: float,
        wood_e_second_mpa: float,
        depth_factor: float,
        steel_e_mpa: float,
    ) -> dict[str, float]:
        influence_depth = equivalent_washer_diameter * depth_factor
        k_steel = steel_e_mpa * steel_area / steel_length
        k_wood_first = wood_e_first_mpa * bearing_area / influence_depth
        k_wood_second = wood_e_second_mpa * bearing_area / influence_depth
        k_effective = 1.0 / (1.0 / k_steel + 1.0 / k_wood_first + 1.0 / k_wood_second)
        return {
            "first_outer_seat_E_axis_mpa": wood_e_first_mpa,
            "second_outer_seat_E_axis_mpa": wood_e_second_mpa,
            "wood_column_depth_factor_of_equivalent_washer_diameter": depth_factor,
            "wood_column_depth_mm": influence_depth,
            "steel_E_mpa": steel_e_mpa,
            "steel_extension_stiffness_n_per_mm": k_steel,
            "first_outer_wood_seat_stiffness_n_per_mm": k_wood_first,
            "second_outer_wood_seat_stiffness_n_per_mm": k_wood_second,
            "effective_axial_stiffness_n_per_mm": k_effective,
        }

    axis = geometry["axis_head_to_nut_xyz"]
    seat_material_responses = []
    for receiver in geometry["outer_receiver_member_ids_head_to_nut"]:
        material = member_materials[receiver]
        grain_alignment = abs(_dot(axis, material["grain_axis_global_xyz"]))
        if grain_alignment >= 1.0 - 1.0e-7:
            alignment_status = "parallel_to_proposed_grain"
        elif grain_alignment <= 1.0e-7:
            alignment_status = "transverse_to_proposed_grain"
        else:
            alignment_status = "oblique_to_proposed_grain"
        cases = []
        for frame_case in material["frame_scenarios"]:
            e_axis, components_lrt = _effective_orthotropic_modulus(
                axis, frame_case["material_axes_global_xyz"], material["material_constants_mpa"]
            )
            cases.append(
                {
                    "material_frame_scenario_id": frame_case["scenario_id"],
                    "effective_uniaxial_E_axis_mpa": e_axis,
                    "bolt_axis_components_in_LRT": components_lrt,
                    "material_axes_global_xyz": frame_case["material_axes_global_xyz"],
                }
            )
        seat_material_responses.append(
            {
                "receiver_id": receiver,
                "member_kind": material["member_kind"],
                "proposed_grain_axis_global_xyz": material["grain_axis_global_xyz"],
                "bolt_axis_abs_dot_proposed_grain": grain_alignment,
                "grain_alignment_status": alignment_status,
                "material_constants_mpa": material["material_constants_mpa"],
                "material_constants_basis": material["material_constants_basis"],
                "material_map": material["material_map"],
                "frame_scenarios": cases,
            }
        )
    first_cases = seat_material_responses[0]["frame_scenarios"]
    second_cases = seat_material_responses[1]["frame_scenarios"]
    baseline = combined(
        first_cases[0]["effective_uniaxial_E_axis_mpa"],
        second_cases[0]["effective_uniaxial_E_axis_mpa"],
        1.0,
        STEEL_E_SENSITIVITY_MPA[1],
    )
    sensitivity = []
    for first_case in first_cases:
        for second_case in second_cases:
            for depth_factor in WOOD_COLUMN_DEPTH_FACTORS:
                for steel_e in (STEEL_E_SENSITIVITY_MPA[0], STEEL_E_SENSITIVITY_MPA[-1]):
                    sensitivity.append(
                        {
                            "first_outer_seat_frame_scenario_id": first_case["material_frame_scenario_id"],
                            "second_outer_seat_frame_scenario_id": second_case["material_frame_scenario_id"],
                            **combined(
                                first_case["effective_uniaxial_E_axis_mpa"],
                                second_case["effective_uniaxial_E_axis_mpa"],
                                depth_factor,
                                steel_e,
                            ),
                        }
                    )
    softened_transverse = combined(
        TRANSVERSE_WOOD_E_MPA["T_soft"],
        TRANSVERSE_WOOD_E_MPA["T_soft"],
        1.0,
        STEEL_E_SENSITIVITY_MPA[1],
    )
    seats = geometry["outer_seat_points_xyz_mm"]
    point = [(a + b) / 2.0 for a, b in zip(seats[0], seats[1], strict=True)]
    if geometry.get("compression_contact_pairs") is not None:
        interface_pairs = geometry["compression_contact_pairs"]
    elif connection["kind"] == "candidate_bolt":
        matching = [
            row
            for row in interfaces
            if row["axis_id"] == connection["axis_id"]
        ]
        interface_pairs = [
            {
                "receiver_member_ids": row["adjacent_receivers_head_to_nut"],
                "interface_point_xyz_mm": row["axis_point_xyz_mm"],
                "compression_contact_required": True,
            }
            for row in matching
        ]
    else:
        raise ValueError(f"{connection['axis_id']}: retained wood contact geometry is required")
    return {
        "axis_id": connection["axis_id"],
        "spring_name": f"{connection['axis_id']}/outer-seat-axial-tie",
        "physical_fastener_count": 1,
        "first": geometry["outer_receiver_member_ids_head_to_nut"][0],
        "second": geometry["outer_receiver_member_ids_head_to_nut"][1],
        "endpoint_member_ids_head_to_nut": geometry["outer_receiver_member_ids_head_to_nut"],
        "outer_seat_points_xyz_mm": seats,
        "point_xyz_mm": point,
        "axis_head_to_nut_xyz": geometry["axis_head_to_nut_xyz"],
        "wood_seat_material_response": seat_material_responses,
        "local_spring_dof": 1,
        "stiffness_n_per_mm": baseline["effective_axial_stiffness_n_per_mm"],
        "tension_only_assumption": True,
        "initially_active": False,
        "preload_n": 0.0,
        "compression_contact_pairs": interface_pairs,
        "wood_compression_contact_required": True,
        "stiffness_basis": {
            "kind": "conditional steel plus two outer washer-seat wood-column compliance in series",
            "steel_extension_length_mm": steel_length,
            "steel_diameter_mm": diameter,
            "steel_area_mm2": steel_area,
            "steel_area_basis": "modeled smooth-shaft gross area; actual thread length, root area, grade and delivered bolt remain unknown",
            "steel_E_mpa_baseline": STEEL_E_SENSITIVITY_MPA[1],
            "washer_thicknesses_mm": [washer_t, washer_t],
            "washer_modeled_volume_mm3": [
                geometry["head_washer"]["modeled_volume_mm3"],
                geometry["nut_washer"]["modeled_volume_mm3"],
            ],
            "washer_annular_bearing_area_mm2": bearing_area,
            "equivalent_washer_area_diameter_mm": equivalent_washer_diameter,
            "wood_seat_effective_E_axis_mpa_baseline": [
                first_cases[0]["effective_uniaxial_E_axis_mpa"],
                second_cases[0]["effective_uniaxial_E_axis_mpa"],
            ],
            "wood_material_frame_nominal": "ring-case A from the same pinned reduced material binder used for native member orientation; ring-case B and independent seat combinations are emitted as sensitivity",
            "wood_column_depth_mm_baseline": equivalent_washer_diameter,
            "wood_column_idealization": "uniform uniaxial compression in a no-spread column using each outer receiver's orthotropic effective E along the bolt axis and actual modeled washer annulus area; one local column at each outer seat",
            "sensitivity_scenarios": sensitivity,
            "softened_transverse_comparison": {
                "status": "named softened comparison only; not the nominal axis-specific law or a physical lower bound",
                "wood_E_mpa_each_seat": TRANSVERSE_WOOD_E_MPA["T_soft"],
                **softened_transverse,
            },
            "limits": [
                "Elastic stiffness scenario only; not a bolt, washer, timber or joint capacity.",
                "Washer component role geometry is modeled and unverified as delivered hardware.",
                "Local column depth is an explicit uncalibrated influence-depth idealization; depth sensitivity is emitted.",
                "Gross member deformation is expected from the member model; this spring represents local outer washer-seat compliance only.",
                "Head/nut deformation, thread engagement, bolt bending, preload, seating gaps and nonlinear crushing are omitted.",
                "No independent axial tie is emitted for a middle receiver in a three-receiver physical bolt.",
            ],
        },
    }


def _candidate_lateral_rows(
    connections: list[dict[str, Any]], interfaces: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    bolts = {row["axis_id"]: row for row in connections if row["kind"] == "candidate_bolt"}
    rows = []
    for index, interface in enumerate(interfaces, start=1):
        connection = bolts[interface["axis_id"]]
        first, second = interface["adjacent_receivers_head_to_nut"]
        clearances = {
            row["receiver_id"]: float(row["geometry_only_centered_radial_gap_mm"])
            for row in connection["receiver_clearance_geometry"]
            if row["geometry_only_centered_radial_gap_mm"] is not None
        }
        if first not in clearances or second not in clearances:
            raise ValueError(f"Missing measured candidate receiver clearance on {interface['axis_id']}")
        relative_clearance = clearances[first] + clearances[second]
        diameter = float(connection["source_record"]["geometry"]["modeled_shaft_diameter_mm"])
        rows.append(
            {
                "kind": "lateral_shear_plane",
                "source_connection_kind": "candidate_bolt",
                "axis_id": interface["axis_id"],
                "physical_axis_group_id": interface["axis_id"],
                "spring_group_name": f"{interface['axis_id']}/plane-{index}",
                "physical_fastener_count": 1,
                "shear_plane_count_for_this_row": 1,
                "first": first,
                "second": second,
                "receiver_member_ids_head_to_nut": [first, second],
                "point_xyz_mm": list(interface["axis_point_xyz_mm"]),
                "point_status": "pinned candidate adjacent-interface axis point",
                "axis_head_to_nut_xyz": _unit(connection["source_record"]["geometry"]["axis_head_to_nut_global"]),
                "local_lateral_dofs": [2, 3],
                "lateral_stiffness_n_per_mm_per_fastener_per_shear_plane": _kser(
                    TIMBER_MEAN_DENSITY_KG_M3, diameter
                ),
                "radial_clearance_assumption": True,
                "radial_clearance_mm": relative_clearance,
                "receiver_radial_clearance_mm": {first: clearances[first], second: clearances[second]},
                "clearance_rule": "sum of the two independently measured centered radial clearances; clearance deformation is separate from Kser",
                "density_input_kg_m3": TIMBER_MEAN_DENSITY_KG_M3,
                "density_sensitivity_kser_n_per_mm": {
                    str(rho): _kser(rho, diameter) for rho in DENSITY_SENSITIVITY_KG_M3
                },
                "law_status": "conditional EC5 service-slip comparison; not a connection strength or nonlinear bearing law",
            }
        )
    return rows


def _retained_lateral_rows(
    retained: list[dict[str, Any]], measured: dict[tuple[str, str], dict[str, Any]]
) -> list[dict[str, Any]]:
    rows = []
    for connection in retained:
        axis_id = connection["axis_id"]
        interface = _retained_interface(connection, measured)
        pair = interface["receiver_member_ids_head_to_nut"]
        gaps = {receiver: measured[(axis_id, receiver)]["centered_radial_gap_mm"] for receiver in pair}
        diameter = float(connection["source_record"]["source_occupied_diameter_mm"])
        rows.append(
            {
                "kind": "lateral_shear_plane",
                "source_connection_kind": "retained_bolt",
                "axis_id": axis_id,
                "physical_axis_group_id": axis_id,
                "spring_group_name": f"{axis_id}/wood-interface",
                "physical_fastener_count": 1,
                "shear_plane_count_for_this_row": 1,
                "first": pair[0],
                "second": pair[1],
                "receiver_member_ids_head_to_nut": pair,
                "source_point_xyz_mm": list(connection["source_point_xyz_mm"]),
                "point_xyz_mm": interface["interface_point_xyz_mm"],
                "point_status": interface["point_status"],
                "receiver_interface_geometry": interface,
                "axis_source_xyz": _unit(connection["axis_xyz"]),
                "local_lateral_dofs": [2, 3],
                "lateral_stiffness_n_per_mm_per_fastener_per_shear_plane": _kser(
                    TIMBER_MEAN_DENSITY_KG_M3, diameter
                ),
                "radial_clearance_assumption": True,
                "radial_clearance_mm": sum(gaps.values()),
                "receiver_radial_clearance_mm": gaps,
                "clearance_rule": "sum of current finished STEP bore-face measurements from both members; not an as-built hole measurement",
                "density_input_kg_m3": TIMBER_MEAN_DENSITY_KG_M3,
                "density_sensitivity_kser_n_per_mm": {
                    str(rho): _kser(rho, diameter) for rho in DENSITY_SENSITIVITY_KG_M3
                },
                "law_status": "conditional EC5 service-slip comparison; retained connection capacity and installed condition remain unverified",
            }
        )
    return rows


def _hillman_lateral_rows(
    screws: list[dict[str, Any]],
    axial_ratio_grid: tuple[float, ...] | None,
) -> list[dict[str, Any]]:
    diameter = HILLMAN_SIZE_10_MAJOR_DIAMETER_IN * INCH_MM
    rho_pair = math.sqrt(TIMBER_MEAN_DENSITY_KG_M3 * PANEL_MEAN_DENSITY_KG_M3)
    rows = []
    for connection in screws:
        pair = list(connection["receiver_member_ids"])
        source_point = list(connection["source_point_xyz_mm"])
        row = {
                "kind": "lateral_shear_plane",
                "source_connection_kind": "panel_screw",
                "axis_id": connection["axis_id"],
                "physical_axis_group_id": connection["axis_id"],
                "spring_group_name": f"{connection['axis_id']}/panel-wood-interface",
                "physical_fastener_count": 1,
                "shear_plane_count_for_this_row": 1,
                "first": pair[0],
                "second": pair[1],
                "receiver_member_ids": pair,
                "source_point_xyz_mm": source_point,
                "point_xyz_mm": source_point,
                "point_status": "source screw head/front-face point; response assembler must attach at the opposite panel face/wood interface",
                "axis_xyz": _unit(connection["axis_xyz"]),
                "local_lateral_dofs": [2, 3],
                "nominal_size_designation": "#10",
                "nominal_major_diameter_mm": diameter,
                "diameter_source_limit": "#10 size designation converted using ASME B18.6.1 basic wood-screw diameter; not measured delivered thread diameter",
                "lateral_stiffness_n_per_mm_per_fastener_per_shear_plane": _kser(rho_pair, diameter),
                "radial_clearance_assumption": False,
                "radial_clearance_mm": None,
                "clearance_status": "unmeasured; zero-gap engagement is a baseline idealization, not a hole fit finding",
                "density_inputs_kg_m3": {
                    "timber_proxy": TIMBER_MEAN_DENSITY_KG_M3,
                    "panel_proxy": PANEL_MEAN_DENSITY_KG_M3,
                    "pair_rule": "geometric mean for two unlike member mean densities",
                },
                "density_sensitivity_kser_n_per_mm": {
                    str(rho): _kser(math.sqrt(rho * PANEL_MEAN_DENSITY_KG_M3), diameter)
                    for rho in DENSITY_SENSITIVITY_KG_M3
                },
                "lateral_method_applicability_limit": "generic EC5 service-slip comparison only; the Hillman product does not publish this modeled stiffness; owner-selected lead pilot/countersink and delivered hole are not modeled",
                "axial_law": {
                    "stiffness_n_per_mm": None,
                    "status": "disabled_no_credit",
                    "reason": "No source-supported Hillman 42605 withdrawal stiffness, thread penetration law, or applicable product resistance is bound in this model.",
                    "missing_tension_path": True,
                },
            }
        if axial_ratio_grid is not None:
            lateral_kser = row["lateral_stiffness_n_per_mm_per_fastener_per_shear_plane"]
            row["axial_law"]["parametric_axial_sweep"] = {
                "status": "non_qualifying_parametric_diagnostic_only",
                "basis": "user-selected dimensionless multiples of this row's generic lateral EC5 Kser comparison",
                "ratio_to_lateral_kser": list(axial_ratio_grid),
                "axial_stiffness_n_per_mm": [ratio * lateral_kser for ratio in axial_ratio_grid],
                "physical_stiffness_bounds_established": False,
                "product_withdrawal_law": False,
                "adoptable_or_capacity_credit": False,
            }
        rows.append(row)
    return rows


def build(
    model_inputs_path: Path = DEFAULT_MODEL_INPUTS,
    *,
    hillman_axial_ratio_grid: list[float] | tuple[float, ...] | None = None,
) -> dict[str, Any]:
    """Build and validate conditional connector rows from pinned model inputs."""
    normalized_ratio_grid: tuple[float, ...] | None = None
    if hillman_axial_ratio_grid is not None:
        values = tuple(float(value) for value in hillman_axial_ratio_grid)
        if not values or any(not math.isfinite(value) or value <= 0.0 for value in values):
            raise ValueError("Hillman parametric axial ratios must be a nonempty sequence of finite positive values")
        if len(set(values)) != len(values):
            raise ValueError("Hillman parametric axial ratios must be unique")
        normalized_ratio_grid = values
    model, topology, centroids, verified_sources = _load_pinned_inputs(Path(model_inputs_path))
    connections = model["connections"]
    candidate_bolts = [row for row in connections if row["kind"] == "candidate_bolt"]
    retained_bolts = [row for row in connections if row["kind"] == "retained_bolt"]
    screws = [row for row in connections if row["kind"] == "panel_screw"]
    interfaces = model["candidate_bolt_adjacent_interfaces"]
    if (len(candidate_bolts), len(retained_bolts), len(screws), len(interfaces)) != (92, 12, 66, 96):
        raise ValueError("Current reduced connector inventory is not 92/12/66/96")

    components, source_rows = _component_maps(topology, centroids)
    retained_clearances = _measure_retained_holes(retained_bolts, model)
    member_materials = _load_member_material_scenarios(model, verified_sources)
    lateral_rows = (
        _candidate_lateral_rows(connections, interfaces)
        + _retained_lateral_rows(retained_bolts, retained_clearances)
        + _hillman_lateral_rows(screws, normalized_ratio_grid)
    )

    axial_rows = []
    washer_geometry_by_axis: dict[str, dict[str, Any]] = {}
    for connection in candidate_bolts:
        geometry = _candidate_axial_geometry(connection, components, source_rows)
        washer_geometry_by_axis[connection["axis_id"]] = geometry
        axial_rows.append(_bolt_axial_law(connection, geometry, interfaces, member_materials))
    for connection in retained_bolts:
        geometry = _retained_axial_geometry(connection, components, source_rows, retained_clearances)
        washer_geometry_by_axis[connection["axis_id"]] = geometry
        axial_rows.append(_bolt_axial_law(connection, geometry, interfaces, member_materials))

    for record in retained_clearances.values():
        verified_sources[record["step_path"]] = record["step_sha256"]

    candidate_gap_counts = Counter(round(row["radial_clearance_mm"], 6)
                                   for row in lateral_rows if row["axis_id"] in {r["axis_id"] for r in candidate_bolts})
    retained_relative_gaps = Counter(round(row["radial_clearance_mm"], 6)
                                     for row in lateral_rows if row["axis_id"] in {r["axis_id"] for r in retained_bolts})
    leg_bolts = [row for row in retained_bolts if row["axis_id"].startswith("lumber_leg_bolt_")]
    rail_bolts = [row for row in retained_bolts if row["axis_id"].startswith("rail_")]
    triple_axes = [row for row in candidate_bolts if len(row["receiver_member_ids"]) == 3]
    if len(triple_axes) != 4:
        raise ValueError("Expected four physical three-receiver quarter-inch bolts")

    material_hash = _sha256(MATERIAL_SCENARIOS)
    verified_sources[str(MATERIAL_SCENARIOS.relative_to(ROOT))] = material_hash
    verified_sources[str(PANEL_WITHDRAWAL_PREFLIGHT.relative_to(ROOT))] = _sha256(PANEL_WITHDRAWAL_PREFLIGHT)
    for path in (ROOT / "fea/current_response_model.py", ROOT / "fea/current_response_run.py"):
        verified_sources[str(path.relative_to(ROOT))] = _sha256(path)

    result = {
        "schema": "wood_joint_reduced_connector_properties/v1",
        "candidate": model["candidate"],
        "revision_id": model["revision_id"],
        "source_model_inputs": str(Path(model_inputs_path).resolve().relative_to(ROOT)),
        "source_sha256": dict(sorted(verified_sources.items())),
        "mechanical_acceptance": False,
        "native_solve_run": False,
        "ready_for_six_case_response": False,
        "adopted_six_case_response_ready": False,
        "non_qualifying_diagnostic_response_permitted": True,
        "readiness_scope": "readiness flags apply to adopted/source-supported six-case results; the zero-credit omission case and explicit Hillman ratio sweep may be used only for clearly labeled diagnostics",
        "parametric_hillman_axial_ratio_grid": (
            list(normalized_ratio_grid) if normalized_ratio_grid is not None else None
        ),
        "preflight_status": "blocked_missing_panel_screw_withdrawal_path",
        "inventory": {
            "candidate_quarter_inch_physical_bolts": len(candidate_bolts),
            "candidate_bolt_lateral_shear_planes": len([r for r in lateral_rows if r["axis_id"] in {x["axis_id"] for x in candidate_bolts}]),
            "candidate_three_receiver_physical_bolts": len(triple_axes),
            "candidate_three_receiver_lateral_planes": sum(
                1 for row in lateral_rows if row["axis_id"] in {x["axis_id"] for x in triple_axes}
            ),
            "retained_physical_bolts": len(retained_bolts),
            "retained_leg_bolts_1_2_in": len(leg_bolts),
            "retained_rail_bolts_3_8_in": len(rail_bolts),
            "hillman_42605_panel_screw_axes": len(screws),
            "lateral_shear_plane_rows": len(lateral_rows),
            "physical_bolt_axial_ties": len(axial_rows),
        },
        "preflight_blockers": [
            {
                "id": "panel_screw_withdrawal_path_missing",
                "severity": "primary six-case preflight blocker",
                "outward_panel_normal_load_screen_n": [1200.0, 1660.0],
                "finding": "The six climber cases pull outward normal to the panel; lateral-only Hillman laws and rear wood compression contact do not resist this separation.",
                "treatment": "Keep the zero-credit omission case. A caller-selected positive axial/lateral ratio sweep is allowed only as a separately labeled non-qualifying diagnostic. These inputs do not support an adopted six-case response, demand/resistance result, or gate.",
                "rating_status": "no Hillman product rating, withdrawal capacity, or axial stiffness is invented or transferred from SPAX/SDS products",
            }
        ],
        "method": {
            "lateral_reference": {
                "formula": "Kser = rho_m^1.5 * d / 23 N/mm per fastener per shear plane",
                "source": SWEDISH_WOOD_JOINT_SLIP_URL,
                "location": "Swedish Wood, Design of Timber Structures, Vol. 2 (2022), page 33, section 9.2 / Table 9.2",
                "clearance": "entered separately as radial relative slip; for each timber/wood plane sum the two receiver radial allowances",
                "scope_limit": "service-slip comparison only; no capacity, nonlinear bearing, local splitting, screw withdrawal, or product certification",
            },
            "candidate_bolts": {
                "physical_bolt_count": 92,
                "quarter_inch_diameter_mm": 6.35,
                "three_receiver_rule": "Four physical bolts each emit two adjacent lateral-plane rows and one axial tie between the two outer washer seats; no middle-member axial tie is added.",
                "relative_clearance_counts_mm": {str(k): v for k, v in sorted(candidate_gap_counts.items())},
            },
            "retained_bolts": {
                "physical_bolt_count": 12,
                "leg_bolt_count": len(leg_bolts),
                "rail_bolt_count": len(rail_bolts),
                "relative_clearance_counts_mm": {str(k): v for k, v in sorted(retained_relative_gaps.items())},
                "hole_method": "coaxial cylindrical faces measured on each pinned current finished receiver STEP; radius minus modeled shaft radius at each receiver; pair gap is sum of the two receiver clearances",
            },
            "hillman_42605": {
                "source_product": HILLMAN_42605_PRODUCT_URL,
                "product_basis": "Fas-n-Tite / Hillman 42605, #10 x 2-1/2 in ceramic-coated wood-to-wood deck screw per product listing; owner shop policy retains lead pilot plus countersink",
                "nominal_major_diameter_source": ASME_WOOD_SCREW_STANDARD_URL,
                "lateral_law": "conditional EC5 comparison only, using nominal #10 major diameter and a geometric-mean timber/panel density proxy",
                "axial_law": "null in the no-credit baseline; optional positive axial/lateral ratio grid is a non-qualifying diagnostic only, not a product law or physical stiffness bound",
                "withdrawal_preflight_source": str(PANEL_WITHDRAWAL_PREFLIGHT.relative_to(ROOT)),
                "withdrawal_preflight_scope": "No source-supported axial stiffness or physical bounds; any arbitrary ratio sweep may answer sensitivity only and must not feed adopted response or gates.",
                "no_transfer": "No SPAX, SDS, or other proprietary screw withdrawal, stiffness, pilot, or installation rule is imported.",
            },
            "bolt_axial_scenario": {
                "law": "one no-preload tension-only tie per physical through-bolt; explicit wood compression contact is required at the intervening wood interfaces",
                "conditional_stiffness_model": "series combination of gross modeled steel shaft stretch and two local outer washer-seat wood compression columns",
                "washer_geometry": "per physical axis, use actual pinned CAD component volume and measured washer thickness/seat position; do not apply a global washer size to all bolts",
                "wood_column": "uniform no-spread compression under each actual modeled washer annulus; axis-specific uniaxial modulus is transformed from each outer receiver's pinned L/R/T frame, with both ring-frame alternatives and 0.5x/1x/2x depth sensitivity",
                "wood_modulus_source": str(MATERIAL_SCENARIOS.relative_to(ROOT)),
                "wood_modulus_scenarios_mpa": TRANSVERSE_WOOD_E_MPA,
                "steel_modulus_scenarios_mpa": STEEL_E_SENSITIVITY_MPA,
                "limits": "Conditional stiffness only, not measured connector law or capacity; actual washer, bolt alloy/grade, thread runout/root area, seating, preload and local crushing remain unresolved.",
            },
            "response_api": {
                "lateral_rows": "one record per physical fastener per adjacent shear plane; add equal local dof 2 and 3 springs; candidate points are interface-axis points, retained points use matched STEP bore interval boundaries, and Hillman point_xyz_mm is the source front-face reference that the response assembler must move to the opposite panel face/wood interface",
                "axial_rows": "one dof-1 tension-only spring per physical bolt, at point_xyz_mm, between first and second outer receivers; record also preserves both real washer-seat points and axis_head_to_nut_xyz",
                "hillman_axial": "stiffness_n_per_mm remains null and missing_tension_path remains true; optional parametric_axial_sweep values are not connector laws and cannot earn capacity/adoption credit",
                "directional_connector_limit": "Do not call directional_connector once per shear plane for a three-receiver bolt: it would duplicate axial ties. Assemble lateral dofs per plane and the single outer-seat axial tie separately.",
            },
        },
        "retained_hole_measurements": [
            {"axis_id": axis_id, **record}
            for (axis_id, _), record in sorted(retained_clearances.items())
        ],
        "lateral_planes": lateral_rows,
        "bolt_outer_seat_axial_ties": axial_rows,
        "bolt_washer_geometry_by_axis": washer_geometry_by_axis,
        "limit": "Development-only conditional connector inputs for the reduced six-case candidate. Not a solve, a complete load-path finding, capacity, product qualification, inspected hardware/wood, fabrication release, or climbing release.",
    }
    verify(result)
    return result


def verify(result: dict[str, Any]) -> None:
    """Focused inventory, clearance, physical-count and blocker checks."""
    identity_frame = {"L": [1.0, 0.0, 0.0], "R": [0.0, 1.0, 0.0], "T": [0.0, 0.0, 1.0]}
    check_constants = (11032.0, 750.176, 551.6, 0.292, 0.449, 0.390,
                       706.048, 860.496, 77.224)
    for axis, expected in (([1.0, 0.0, 0.0], 11032.0),
                           ([0.0, 1.0, 0.0], 750.176),
                           ([0.0, 0.0, 1.0], 551.6)):
        observed, _ = _effective_orthotropic_modulus(axis, identity_frame, check_constants)
        assert math.isclose(observed, expected, rel_tol=1e-12)

    inventory = result["inventory"]
    assert inventory["candidate_quarter_inch_physical_bolts"] == 92
    assert inventory["candidate_bolt_lateral_shear_planes"] == 96
    assert inventory["candidate_three_receiver_physical_bolts"] == 4
    assert inventory["candidate_three_receiver_lateral_planes"] == 8
    assert inventory["retained_physical_bolts"] == 12
    assert inventory["retained_leg_bolts_1_2_in"] == 4
    assert inventory["retained_rail_bolts_3_8_in"] == 8
    assert inventory["hillman_42605_panel_screw_axes"] == 66
    assert inventory["lateral_shear_plane_rows"] == 174
    assert inventory["physical_bolt_axial_ties"] == 104
    assert result["ready_for_six_case_response"] is False
    assert result["non_qualifying_diagnostic_response_permitted"] is True
    assert result["native_solve_run"] is False
    assert result["preflight_status"] == "blocked_missing_panel_screw_withdrawal_path"

    lateral = result["lateral_planes"]
    assert len({row["spring_group_name"] for row in lateral}) == len(lateral)
    for row in lateral:
        assert row["physical_fastener_count"] == 1
        assert row["local_lateral_dofs"] == [2, 3]
        assert row["lateral_stiffness_n_per_mm_per_fastener_per_shear_plane"] > 0.0
    candidate_gaps = Counter(
        round(row["radial_clearance_mm"], 6)
        for row in lateral
        if row["source_connection_kind"] == "candidate_bolt"
        and row["radial_clearance_assumption"]
    )
    assert candidate_gaps == Counter({1.15: 80, 0.95: 16}), candidate_gaps
    candidate_plane_counts = Counter(
        row["axis_id"] for row in lateral if row["source_connection_kind"] == "candidate_bolt"
    )
    assert len(candidate_plane_counts) == 92
    assert Counter(candidate_plane_counts.values()) == Counter({1: 88, 2: 4})
    retained = [row for row in lateral if row["source_connection_kind"] == "retained_bolt"]
    assert len(retained) == 12
    assert all(math.isclose(row["radial_clearance_mm"], 1.5875, abs_tol=1.0e-6) for row in retained)
    assert all(row["point_status"] == "resolved_current_finished_STEP_coaxial_bore_interval_boundary" for row in retained)
    screws = [row for row in lateral if row["source_connection_kind"] == "panel_screw"]
    assert len(screws) == 66
    assert all(row["point_status"].startswith("source screw head/front-face point") for row in screws)
    assert all(row["axial_law"]["stiffness_n_per_mm"] is None for row in screws)
    assert all(row["axial_law"]["missing_tension_path"] for row in screws)
    ratio_grid = result["parametric_hillman_axial_ratio_grid"]
    for row in screws:
        sweep = row["axial_law"].get("parametric_axial_sweep")
        if ratio_grid is None:
            assert sweep is None
        else:
            assert sweep["ratio_to_lateral_kser"] == ratio_grid
            assert sweep["status"] == "non_qualifying_parametric_diagnostic_only"
            assert sweep["physical_stiffness_bounds_established"] is False
            assert sweep["adoptable_or_capacity_credit"] is False
            assert len(sweep["axial_stiffness_n_per_mm"]) == len(ratio_grid)

    axial = result["bolt_outer_seat_axial_ties"]
    assert len({row["spring_name"] for row in axial}) == 104
    assert len({row["axis_id"] for row in axial}) == 104
    assert all(row["physical_fastener_count"] == 1 for row in axial)
    assert all(row["tension_only_assumption"] and row["preload_n"] == 0.0 for row in axial)
    assert all(row["stiffness_n_per_mm"] > 0.0 for row in axial)
    assert all(len(row["wood_seat_material_response"]) == 2 for row in axial)
    assert all(
        scenario["effective_uniaxial_E_axis_mpa"] > 0.0
        for row in axial
        for seat in row["wood_seat_material_response"]
        for scenario in seat["frame_scenarios"]
    )
    triple_ids = {
        axis_id
        for axis_id, geometry in result["bolt_washer_geometry_by_axis"].items()
        if len(geometry["receiver_span_records"]) == 3
    }
    assert len(triple_ids) == 4
    assert all(sum(row["axis_id"] == axis_id for row in axial) == 1 for axis_id in triple_ids)
    assert all(
        len(result["bolt_washer_geometry_by_axis"][axis_id]["outer_seat_points_xyz_mm"]) == 2
        for axis_id in triple_ids
    )
    assert result["preflight_blockers"][0]["outward_panel_normal_load_screen_n"] == [1200.0, 1660.0]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model-inputs", type=Path, default=DEFAULT_MODEL_INPUTS)
    parser.add_argument(
        "--hillman-axial-ratio-grid",
        type=float,
        nargs="+",
        help="optional non-qualifying ratios k_axial/Kser for Hillman diagnostic rows",
    )
    parser.add_argument("--verify", action="store_true", help="run focused checks and print a compact result")
    arguments = parser.parse_args()
    result = build(arguments.model_inputs, hillman_axial_ratio_grid=arguments.hillman_axial_ratio_grid)
    if arguments.verify:
        print(
            "PASS reduced connector inventory: 92 candidate bolts / 96 shear planes, "
            "12 retained bolts (4 leg + 8 rail), 66 Hillman lateral-only axes; "
            "104 outer-seat bolt ties; adopted response remains blocked by missing Hillman withdrawal path"
        )
    else:
        print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
