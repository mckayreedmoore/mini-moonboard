"""Bind the kerf-right source geometry to the wood-joint MVP inventory.

This module records existing geometry and unresolved replacement obligations. It
does not select a joint, prove a receiver path, or release fabrication.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import subprocess
from pathlib import Path

from mini_moonboard.floor_flush_width import KERF_RIGHT, variant
from scripts.simple_owner_duty_ledger import selected_duties

ROOT = Path(__file__).resolve().parents[1]
OFFICIAL_AXES = ROOT / "docs/floor-flush-construction/connection-axes.csv"
KERF_AXES = ROOT / "docs/floor-flush-construction-kerf-right/connection-axes.csv"
KERF_STOCK = ROOT / "docs/floor-flush-construction-kerf-right/stock.csv"
KERF_PROFILES = ROOT / "docs/floor-flush-construction-kerf-right/stock-profiles.json"
DEFAULT_OUTPUT = ROOT / "docs/wood-joints-mvp/source-inventory.json"
SOURCE_COMMIT = "df7f5eca86ae831b35a8bcf9e6dcd7ae8af852bb"
SOURCE_MODULES = (
    ROOT / "mini_moonboard/floor_flush_width.py",
    ROOT / "mini_moonboard/compact_floor_flush_frame.py",
    ROOT / "scripts/simple_owner_duty_ledger.py",
)

ANGLE_RADIANS = math.radians(50.0)
ASSEMBLY_BASIS = (
    (1.0, 0.0, 0.0),
    (0.0, math.cos(ANGLE_RADIANS), math.sin(ANGLE_RADIANS)),
    (0.0, -math.sin(ANGLE_RADIANS), math.cos(ANGLE_RADIANS)),
)
CENTER_RECEIVER_AXES = {
    "left": ("round_kicker_left_center_1", "round_kicker_left_center_2"),
    "right": ("round_kicker_right_center_1", "round_kicker_right_center_2"),
}
CONTACT_BEHAVIOR = "compression_only_no_tangential_restraint"


def _dot(first, second):
    return sum(a * b for a, b in zip(first, second, strict=True))


def _cross(first, second):
    return (
        first[1] * second[2] - first[2] * second[1],
        first[2] * second[0] - first[0] * second[2],
        first[0] * second[1] - first[1] * second[0],
    )


def _norm(vector):
    return math.sqrt(_dot(vector, vector))


def _unit(vector):
    length = _norm(vector)
    if not math.isfinite(length) or length <= 0:
        raise ValueError("local axis must have finite positive length")
    return tuple(value / length for value in vector)


def _vector(value):
    return tuple(float(component) for component in value.toTuple())


def _sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _canonical_sha256(value):
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def _assert_pinned_data(path):
    relative = str(path.relative_to(ROOT))
    result = subprocess.run(
        ["git", "-C", str(ROOT), "show", f"{SOURCE_COMMIT}:{relative}"],
        check=True,
        capture_output=True,
        timeout=10,
    )
    if result.stdout != path.read_bytes():
        raise ValueError(f"working source differs from pinned commit: {relative}")


def _planar_faces(shape):
    records = []
    for face in shape.Faces():
        if face.geomType() != "PLANE":
            continue
        vertices = [_vector(vertex.Center()) for vertex in face.Vertices()]
        normal = _unit(_vector(face.normalAt()))
        records.append(
            {
                "area_mm2": face.Area(),
                "center_global_xyz_mm": _vector(face.Center()),
                "normal_global_xyz": normal,
                "spans_local_mm": {
                    axis: max(_dot(point, basis) for point in vertices)
                    - min(_dot(point, basis) for point in vertices)
                    for axis, basis in zip(
                        ("X", "T", "N"), ASSEMBLY_BASIS, strict=True
                    )
                },
            }
        )
    records.sort(
        key=lambda row: (
            tuple(round(value, 8) for value in row["center_global_xyz_mm"]),
            tuple(round(value, 8) for value in row["normal_global_xyz"]),
            round(row["area_mm2"], 8),
        )
    )
    return [
        {"face_id": f"planar_face_{index:02d}", **record}
        for index, record in enumerate(records, 1)
    ]


def _shape_fingerprint(shape, planar_faces):
    return _canonical_sha256(
        {
            "volume_mm3": round(shape.Volume(), 7),
            "vertices_mm": sorted(
                tuple(round(value, 7) for value in _vector(vertex.Center()))
                for vertex in shape.Vertices()
            ),
            "planar_faces": planar_faces,
        }
    )


def _csv_by_name(path):
    with path.open(newline="", encoding="utf-8-sig") as source:
        rows = list(csv.DictReader(source))
    result = {row["name"]: row for row in rows}
    if len(result) != len(rows):
        raise ValueError(f"duplicate connection name in {path}")
    return result


def _grain_axis(name, source):
    """Return source material direction without treating it as local T."""
    if name.startswith("base_rail_") or name == "base_header":
        return (1.0, 0.0, 0.0)
    if name.startswith("base_post_"):
        return (0.0, 0.0, 1.0)
    if name.startswith(("base_side_", "base_principal_")):
        return _unit(_vector(source.axes()[4]))
    if name.startswith("lumber_leg_"):
        return _unit(_vector(source.axes()[2]))
    if name.startswith("base_floor_"):
        return (0.0, 1.0, 0.0)
    raise ValueError(f"no authenticated timber grain rule for {name}")


def _part_record(part, source, profiles_hash):
    vertices = [_vector(vertex.Center()) for vertex in part.shape.Vertices()]
    if not vertices:
        raise ValueError(f"source part has no vertices: {part.name}")
    origin = min(
        vertices,
        key=lambda point: (
            _dot(point, ASSEMBLY_BASIS[2]),
            _dot(point, ASSEMBLY_BASIS[1]),
            _dot(point, ASSEMBLY_BASIS[0]),
        ),
    )
    local = [
        tuple(
            _dot(tuple(point[i] - origin[i] for i in range(3)), axis)
            for axis in ASSEMBLY_BASIS
        )
        for point in vertices
    ]
    extents = [
        [min(point[index] for point in local), max(point[index] for point in local)]
        for index in range(3)
    ]
    matrix = [
        [ASSEMBLY_BASIS[column][row] for column in range(3)] + [origin[row]]
        for row in range(3)
    ] + [[0.0, 0.0, 0.0, 1.0]]
    is_panel = part.name.startswith(("main_", "kicker_"))
    planar_faces = _planar_faces(part.shape)
    record = {
        "part_id": part.name,
        "kind": "plywood_panel" if is_panel else "timber",
        "transport_owner": part.name,
        "source_blank_dimensions_mm": list(part.blank),
        "source_geometry_status": "uncut_source_shape",
        "local_datum": "actual_vertex_minimum_N_then_T_then_X",
        "local_axes": {
            "X": ASSEMBLY_BASIS[0],
            "T": ASSEMBLY_BASIS[1],
            "N": ASSEMBLY_BASIS[2],
        },
        "local_to_global_transform": matrix,
        "actual_shape_extents_local_mm": {
            axis: extents[index] for index, axis in enumerate(("X", "T", "N"))
        },
        "actual_planar_faces": planar_faces,
        "source_shape_record_sha256": profiles_hash,
        "source_shape_sha256": _shape_fingerprint(part.shape, planar_faces),
        "delivered_stock_observed": False,
    }
    if is_panel:
        broad_face = max(planar_faces, key=lambda face: face["area_mm2"])
        broad_normal = broad_face["normal_global_xyz"]
        first_axis = ASSEMBLY_BASIS[0]
        if abs(_dot(broad_normal, first_axis)) > 1e-8:
            raise ValueError(f"panel width axis is not tangent: {part.name}")
        second_axis = _unit(_cross(broad_normal, first_axis))
        record.update(
            {
                "stock_product": "23/32 CAT-face plywood source geometry",
                "plywood_layup": "unverified",
                "broad_face_id": broad_face["face_id"],
                "broad_face_normal_global_xyz": broad_normal,
                "panel_strength_axes_global_xyz": [first_axis, second_axis],
            }
        )
    else:
        section = sorted(float(value) for value in part.blank)[0:2]
        record.update(
            {
                "stock_product": "solid sawn timber",
                "species_grade_basis": "DF-L No. 2",
                "actual_source_section_mm": section,
                "grain_axis_global_xyz": _grain_axis(part.name, source),
            }
        )
    return record


def _connection_record(connection, source_row):
    start = _vector(connection.start)
    direction = _unit(_vector(connection.direction))
    csv_start = tuple(float(source_row[f"start_{axis}_mm"]) for axis in "xyz")
    csv_direction = tuple(float(source_row[f"direction_{axis}"]) for axis in "xyz")
    if any(
        abs(first - second) > 1e-8
        for first, second in zip(start, csv_start, strict=True)
    ):
        raise ValueError(f"source variant/CSV start mismatch: {connection.name}")
    if any(
        abs(first - second) > 1e-8
        for first, second in zip(direction, csv_direction, strict=True)
    ):
        raise ValueError(f"source variant/CSV direction mismatch: {connection.name}")
    return {
        "axis_id": connection.name,
        "members": list(connection.members),
        "origin_global_xyz_mm": start,
        "axis_global_xyz": direction,
        "source_occupied_length_mm": float(source_row["occupied_length_mm"]),
        "source_occupied_diameter_mm": float(source_row["occupied_diameter_mm"]),
        "shop_opening_kind": source_row["shop_opening_kind"],
    }


def _duty_records(duties, connections, rows):
    result = []
    for station, duty in duties.items():
        axes = []
        for axis_id in duty["sds_axes"]:
            record = _connection_record(connections[axis_id], rows[axis_id])
            record["axis_role"] = "beam" if "_beam_" in axis_id else "upright"
            axes.append(record)
        result.append(
            {
                "legacy_station_id": station,
                "legacy_family": duty["family"],
                "side": duty["side"],
                "legacy_host_members": list(duty["timber"]),
                "legacy_sds_axes": axes,
                "replacement_owner": None,
                "replacement_interface_path": [],
                "replacement_path_complete": False,
            }
        )
    return result


def _panel_screw_records(source, connections, rows):
    center_to_side = {
        axis_id: side
        for side, axis_ids in CENTER_RECEIVER_AXES.items()
        for axis_id in axis_ids
    }
    result = []
    for connection in source.panel_connections():
        record = _connection_record(connection, rows[connection.name])
        side = center_to_side.get(connection.name)
        source_receiver = connection.members[1]
        candidate_receiver = f"inner_kicker_backer_{side}" if side else source_receiver
        record.update(
            {
                "panel_member": connection.members[0],
                "source_finished_receiver_member": source_receiver,
                "candidate_finished_receiver_member": candidate_receiver,
                "shop_purchased_length_mm": float(
                    rows[connection.name]["shop_purchased_length_mm"]
                ),
                "candidate_receiver_geometry_status": (
                    "required_receiver_volume_unmodeled_in_source_variant"
                    if side
                    else "source_member_bound_candidate_recheck_required"
                ),
                "receiver_to_frame_path": (
                    "attachment_to_structural_frame_unresolved"
                    if side
                    else "source_structural_member; replacement interfaces remain unqualified"
                ),
                "receiver_to_frame_path_complete": False,
            }
        )
        result.append(record)
    return result


def _frame_bolt_records(connections, rows):
    result = []
    for connection in connections.values():
        if connection.kind != "bolt":
            continue
        record = _connection_record(connection, rows[connection.name])
        record.update(
            {
                "source_nominal_length_mm": connection.length,
                "source_grip_mm": connection.grip,
                "candidate_recheck_status": "required",
            }
        )
        result.append(record)
    return sorted(result, key=lambda record: record["axis_id"])


def _existing_contacts(frame_bolts):
    groups = {}
    for bolt in frame_bolts:
        pair = tuple(bolt["members"])
        groups.setdefault(pair, []).append(bolt["axis_id"])
    return [
        {
            "interface_id": "source_contact__" + "__".join(pair),
            "members": list(pair),
            "retained_frame_bolt_axis_ids": sorted(axis_ids),
            "source_behavior": CONTACT_BEHAVIOR,
            "new_candidate_acceptance": False,
        }
        for pair, axis_ids in sorted(groups.items())
    ]


def _span(part, axis):
    low, high = part["actual_shape_extents_local_mm"][axis]
    return high - low


def _face_with_normal(part, target):
    matches = [
        face
        for face in part["actual_planar_faces"]
        if _dot(face["normal_global_xyz"], target) > 1.0 - 1e-8
    ]
    if not matches:
        raise ValueError(
            f"part has no physical face at requested normal: {part['part_id']}"
        )
    return max(matches, key=lambda face: face["area_mm2"])


def _clusters(duties_by_name, parts_by_name):
    outer = []
    for side in ("left", "right"):
        stations = [f"clip_timber_header_outer_{side}", f"clip_angle_base_{side}"]
        outer.append(
            {
                "cluster_id": f"outer_node_{side}",
                "kind": "combined_outer_node_inventory",
                "legacy_station_ids": stations,
                "source_host_members": sorted(
                    {
                        member
                        for station in stations
                        for member in duties_by_name[station]["legacy_host_members"]
                    }
                ),
                "candidate_status": "combined_node_unmodeled",
            }
        )
    station = "clip_horizontal_lower_right_1"
    rail = parts_by_name["base_rail_service_lower_right"]
    upright = parts_by_name["base_principal_center_right"]
    rail_rear = _face_with_normal(rail, ASSEMBLY_BASIS[2])
    upright_rear = _face_with_normal(upright, ASSEMBLY_BASIS[2])
    workhorse = {
        "cluster_id": "ordinary_workhorse_lower_center_right",
        "kind": "ordinary_workhorse_inventory",
        "legacy_station_ids": [station],
        "source_host_members": duties_by_name[station]["legacy_host_members"],
        "presented_face": "rear_N_max",
        "source_stock_and_face_widths_mm": {
            "base_rail_service_lower_right": {
                "stock_section": rail["actual_source_section_mm"],
                "rear_face_id": rail_rear["face_id"],
                "rear_face_local_T_width": rail_rear["spans_local_mm"]["T"],
                "rear_projection_local_N": _span(rail, "N"),
            },
            "base_principal_center_right": {
                "stock_section": upright["actual_source_section_mm"],
                "rear_face_id": upright_rear["face_id"],
                "rear_face_local_X_width": upright_rear["spans_local_mm"]["X"],
                "rear_projection_local_N": _span(upright, "N"),
            },
        },
        "candidate_status": "reference_station_only; joint unmodeled",
    }
    center_stations = [
        "clip_split_header_center_left",
        "clip_split_header_center_right",
        "clip_split_base_center_left",
        "clip_split_base_center_right",
    ]
    center = {
        "cluster_id": "center_node",
        "kind": "center_and_kicker_receiver_inventory",
        "legacy_station_ids": center_stations,
        "source_host_members": sorted(
            {
                member
                for station in center_stations
                for member in duties_by_name[station]["legacy_host_members"]
            }
        ),
        "source_post_center_x_mm": {"left": -70.0, "right": 70.0},
        "owner_starting_post_center_x_mm": {"left": -180.0, "right": 180.0},
        "receiver_obligation_ids": [
            "center_kicker_receiver_left",
            "center_kicker_receiver_right",
        ],
        "candidate_status": "receiver attachments and complete node unresolved",
    }
    constraints = [
        {
            "constraint_id": "workhorse_rail_rear_face_local_T",
            "member": "base_rail_service_lower_right",
            "physical_face_id": rail_rear["face_id"],
            "width_mm": rail_rear["spans_local_mm"]["T"],
            "status": "source_geometry_only",
        },
        {
            "constraint_id": "workhorse_principal_rear_face_local_X",
            "member": "base_principal_center_right",
            "physical_face_id": upright_rear["face_id"],
            "width_mm": upright_rear["spans_local_mm"]["X"],
            "status": "source_geometry_only",
        },
    ]
    return [*outer, workhorse, center], constraints


def _receiver_obligations():
    return [
        {
            "obligation_id": f"center_kicker_receiver_{side}",
            "side": side,
            "fixed_screw_axis_ids": list(CENTER_RECEIVER_AXES[side]),
            "source_receiver_member": f"base_post_center_{side}",
            "required_candidate_receiver_member": f"inner_kicker_backer_{side}",
            "inner_kicker_edge_support_required": True,
            "receiver_attachment_to_frame_status": "unresolved",
            "edge_support_path_status": "unresolved",
            "complete": False,
        }
        for side in ("left", "right")
    ]


def build_inventory():
    """Build exact source inventory and explicit unresolved candidate obligations."""
    for path in (OFFICIAL_AXES, KERF_AXES, KERF_STOCK, KERF_PROFILES):
        _assert_pinned_data(path)
    source = variant(KERF_RIGHT)
    source_connections = tuple(source.connections())
    connections = {connection.name: connection for connection in source_connections}
    rows = _csv_by_name(KERF_AXES)
    if len(connections) != len(source_connections) or set(connections) != set(rows):
        raise ValueError(
            "kerf-right source variant and connection CSV identities differ"
        )

    duties = selected_duties(KERF_AXES)
    official_duties = selected_duties(OFFICIAL_AXES)
    identity = lambda rows: {
        station: (duty["timber"], duty["sds_axes"]) for station, duty in rows.items()
    }
    if identity(duties) != identity(official_duties):
        raise ValueError("official and kerf-right duty identities differ")
    duty_records = _duty_records(duties, connections, rows)
    profiles_hash = _sha256(KERF_PROFILES)
    part_records = [
        _part_record(part, source, profiles_hash) for part in source.uncut_wood_parts()
    ]
    parts_by_name = {part["part_id"]: part for part in part_records}
    duty_by_name = {duty["legacy_station_id"]: duty for duty in duty_records}
    panel_screws = _panel_screw_records(source, connections, rows)
    frame_bolts = _frame_bolt_records(connections, rows)
    clusters, envelope_constraints = _clusters(duty_by_name, parts_by_name)
    timber = sorted(
        part["part_id"] for part in part_records if part["kind"] == "timber"
    )
    panels = sorted(
        part["part_id"] for part in part_records if part["kind"] == "plywood_panel"
    )
    inventory = {
        "schema": "wood_joint_source_inventory/v1",
        "candidate": "compact-floor-flush-wood-joints-development",
        "source_candidate": "compact-floor-flush-development",
        "source_commit": SOURCE_COMMIT,
        "source_binding": (
            "Connection, stock, and profile records are byte-matched to the pinned "
            "commit. Runtime source-module and generated part-shape hashes bind the "
            "CAD extraction without claiming a clean working tree."
        ),
        "width_variant": KERF_RIGHT,
        "source_hashes_sha256": {
            str(path.relative_to(ROOT)): _sha256(path)
            for path in (OFFICIAL_AXES, KERF_AXES, KERF_STOCK, KERF_PROFILES)
        },
        "source_runtime_module_hashes_sha256": {
            str(path.relative_to(ROOT)): _sha256(path) for path in SOURCE_MODULES
        },
        "source_part_shapes_sha256": _canonical_sha256(
            {
                part["part_id"]: part["source_shape_sha256"]
                for part in part_records
            }
        ),
        "official_kerf_identity_crosscheck": {
            "station_host_pairs_identical": True,
            "legacy_sds_axis_ids_identical": True,
        },
        "coordinate_contract": {
            "units": "mm",
            "basis_order": ["X", "T", "N"],
            "basis_columns_global_xyz": ASSEMBLY_BASIS,
            "right_handed": True,
            "grain_is_separate_from_local_T": True,
        },
        "legacy_duties": duty_records,
        "fixed_panel_kicker_screws": panel_screws,
        "starting_frame_bolts": frame_bolts,
        "existing_contact_interfaces": _existing_contacts(frame_bolts),
        "parts": part_records,
        "transport_decomposition": {"timber": timber, "panels": panels},
        "receiver_obligations": _receiver_obligations(),
        "candidate_clusters": clusters,
        "two_narrowest_named_envelope_constraints": envelope_constraints,
        "claim": "Source identity and geometry inventory only; no new joint or receiver path is accepted.",
        "candidate_layout_complete": False,
        "candidate_engineering_mvp_complete": False,
        "drilling_released": False,
        "fabrication_released": False,
        "structural_released": False,
    }
    validate_inventory(inventory)
    return inventory


def _basis_from_transform(transform):
    return tuple(
        tuple(transform[row][column] for row in range(3)) for column in range(3)
    )


def _determinant(basis):
    return _dot(basis[0], _cross(basis[1], basis[2]))


def validate_inventory(inventory):
    """Fail closed when WJ-01 source counts or geometry contracts drift."""
    duties = inventory["legacy_duties"]
    duty_names = [duty["legacy_station_id"] for duty in duties]
    sds = [axis for duty in duties for axis in duty["legacy_sds_axes"]]
    panels = inventory["fixed_panel_kicker_screws"]
    bolts = inventory["starting_frame_bolts"]
    parts = {part["part_id"]: part for part in inventory["parts"]}
    if len(duties) != 24 or len(set(duty_names)) != 24:
        raise ValueError("WJ-01 requires exactly 24 unique legacy duties")
    if len(sds) != 144 or len({axis["axis_id"] for axis in sds}) != 144:
        raise ValueError("WJ-01 requires exactly 144 unique legacy SDS axes")
    if any(len(duty["legacy_sds_axes"]) != 6 for duty in duties):
        raise ValueError("every legacy duty must retain six source SDS axes")
    if len(panels) != 66 or len({axis["axis_id"] for axis in panels}) != 66:
        raise ValueError("WJ-01 requires exactly 66 unique panel/kicker screw axes")
    if len(bolts) != 12 or len({axis["axis_id"] for axis in bolts}) != 12:
        raise ValueError("WJ-01 requires exactly twelve starting frame bolts")
    if any(float(axis["shop_purchased_length_mm"]) != 63.5 for axis in panels):
        raise ValueError("retained purchased panel/kicker screw length changed")
    if any(not set(duty["legacy_host_members"]).issubset(parts) for duty in duties):
        raise ValueError("legacy duty has an unbound source host")
    if any(
        not math.isfinite(value)
        for axis in (*sds, *panels, *bolts)
        for value in (*axis["origin_global_xyz_mm"], *axis["axis_global_xyz"])
    ):
        raise ValueError("source connection coordinate is not finite")
    if any(
        not math.isclose(_norm(axis["axis_global_xyz"]), 1.0, abs_tol=1e-8)
        for axis in (*sds, *panels, *bolts)
    ):
        raise ValueError("source connection direction is not unit length")
    for part in parts.values():
        basis = _basis_from_transform(part["local_to_global_transform"])
        if any(not math.isclose(_norm(axis), 1.0, abs_tol=1e-9) for axis in basis):
            raise ValueError(f"non-unit local transform: {part['part_id']}")
        if any(
            not math.isclose(_dot(basis[i], basis[j]), 0.0, abs_tol=1e-9)
            for i in range(3)
            for j in range(i + 1, 3)
        ):
            raise ValueError(f"non-orthogonal local transform: {part['part_id']}")
        if not math.isclose(_determinant(basis), 1.0, abs_tol=1e-9):
            raise ValueError(f"left-handed local transform: {part['part_id']}")
    for stem in (
        "base_side",
        "lumber_leg",
        "base_floor",
        "base_post_outer",
        "base_post_center",
        "base_principal_center",
        "main_lower",
        "main_upper",
        "kicker",
    ):
        left, right = parts[f"{stem}_left"], parts[f"{stem}_right"]
        if _basis_from_transform(
            left["local_to_global_transform"]
        ) != _basis_from_transform(right["local_to_global_transform"]):
            raise ValueError(f"mirrored local orientation semantics changed: {stem}")
        if (
            left["kind"] == "timber"
            and left["grain_axis_global_xyz"] != right["grain_axis_global_xyz"]
        ):
            raise ValueError(f"mirrored grain orientation changed: {stem}")
    obligations = inventory["receiver_obligations"]
    if {row["side"] for row in obligations} != {"left", "right"} or len(
        obligations
    ) != 2:
        raise ValueError("both center receiver obligations must be explicit")
    if any(
        row["complete"] or row["edge_support_path_status"] != "unresolved"
        for row in obligations
    ):
        raise ValueError("unmapped center edge support cannot be marked complete")
    if any(axis["receiver_to_frame_path_complete"] for axis in panels):
        raise ValueError("WJ-01 cannot mark a candidate receiver path complete")
    if len(inventory["existing_contact_interfaces"]) != 6:
        raise ValueError("source frame must retain six existing contact interfaces")
    if (
        len(inventory["transport_decomposition"]["timber"]) != 20
        or len(inventory["transport_decomposition"]["panels"]) != 6
    ):
        raise ValueError(
            "transport decomposition must remain 20 timber pieces and six panels"
        )
    if any(
        inventory[flag]
        for flag in (
            "candidate_layout_complete",
            "candidate_engineering_mvp_complete",
            "drilling_released",
            "fabrication_released",
            "structural_released",
        )
    ):
        raise ValueError("source inventory cannot release the candidate")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    inventory = build_inventory()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(inventory, indent=2, allow_nan=False) + "\n")
    print(
        f"Bound 24 duties, 144 SDS axes, 66 panel/kicker axes, and 12 frame bolts to {args.output}."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
