"""Build a source-bound translation-only clearance witness for the ordinary patch.

This is geometry bookkeeping for the frozen three-wood/four-bolt patch. It
does not build CAD, mesh, assign mechanics, constrain member rotations, or run
a solver. Its summed receiver clearances describe ideal freely translating
pins only.
"""

from __future__ import annotations

import hashlib
import json
import math
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
RESUME = Path("docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24")
DEFAULT_INVENTORY = ROOT / RESUME / "ordinary-patch-inputs-attempt01/inventory.json"
DEFAULT_CLASSIFICATION = (
    ROOT
    / RESUME
    / "ordinary-patch-contact-classification-attempt01/classification.json"
)
DEFAULT_MATERIAL_MAP = (
    ROOT / RESUME / "ordinary-patch-materials-attempt01/material-map.json"
)
SOURCE_INVENTORY = ROOT / "docs/wood-joints-mvp/source-inventory.json"

SCHEMA = "wood_joint_current_clearance_seating_witness/v1"
STATUS = "GEOMETRY_ONLY_TRANSLATION_CLEARANCE_WITNESS"
REVISION_ID = "led-clearance-2x6-runner-seated-blocks-v1"
IMPLEMENTATION_REVISION = "b1e8707d"
CLEAT_ID = "bottom_center_right_cleat"
RAIL_ID = "base_rail_bottom_right"
PRINCIPAL_ID = "base_principal_center_right"
WOOD_IDS = (CLEAT_ID, RAIL_ID, PRINCIPAL_ID)
INTERFACE_PATH = (
    "bottom_center_right_cleat_to_base_rail_bottom_right",
    "bottom_center_right_cleat_to_base_principal_center_right",
)
DIRECT_INTERFACE_ID = "base_rail_bottom_right_to_base_principal_center_right"
EXPECTED_BOLTS = {
    "bottom_center/clip_horizontal_bottom_right_1/rail_1",
    "bottom_center/clip_horizontal_bottom_right_1/rail_2",
    "bottom_center/clip_horizontal_bottom_right_1/principal_1",
    "bottom_center/clip_horizontal_bottom_right_1/principal_2",
}
EXPECTED_CLEARANCE_MM = 0.575
GEOMETRY_TOLERANCE_MM = 1e-5
VECTOR_TOLERANCE = 1e-6


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _canonical_sha256(value: Mapping[str, Any]) -> str:
    payload = json.dumps(
        value, sort_keys=True, separators=(",", ":"), allow_nan=False
    ).encode("utf-8")
    return _sha256_bytes(payload)


def _file_sha256(path: Path) -> str:
    return _sha256_bytes(path.read_bytes())


def _read_json(path: str | Path, context: str) -> tuple[dict[str, Any], Path, str]:
    source = Path(path).resolve()
    try:
        raw = source.read_bytes()
        value = json.loads(raw)
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError(
            f"{context} is unavailable or invalid JSON: {source}"
        ) from error
    if not isinstance(value, dict):
        raise TypeError(f"{context} must be a JSON object")
    return value, source, _sha256_bytes(raw)


def _display_path(path: Path) -> str:
    try:
        return path.relative_to(ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def _vec3(value: Any, context: str) -> tuple[float, float, float]:
    try:
        vector = tuple(float(item) for item in value)
    except (TypeError, ValueError, OverflowError) as error:
        raise ValueError(f"{context}: expected a finite XYZ vector") from error
    if len(vector) != 3 or not all(math.isfinite(item) for item in vector):
        raise ValueError(f"{context}: expected a finite XYZ vector")
    return vector  # type: ignore[return-value]


def _dot(a: Sequence[float], b: Sequence[float]) -> float:
    return math.fsum(left * right for left, right in zip(a, b, strict=True))


def _norm(a: Sequence[float]) -> float:
    return math.sqrt(_dot(a, a))


def _unit(value: Sequence[float], context: str) -> tuple[float, float, float]:
    vector = _vec3(value, context)
    magnitude = _norm(vector)
    if magnitude <= 0.0:
        raise ValueError(f"{context}: zero-length direction")
    return tuple(component / magnitude for component in vector)  # type: ignore[return-value]


def _rounded(value: float) -> float:
    return round(float(value), 12)


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def build_current_clearance_seating_witness(
    inventory_path: str | Path = DEFAULT_INVENTORY,
    classification_path: str | Path = DEFAULT_CLASSIFICATION,
    material_map_path: str | Path = DEFAULT_MATERIAL_MAP,
) -> dict[str, Any]:
    """Derive clear receiver-gap travel and the cleat-grain chain from frozen data."""
    inventory, inventory_file, inventory_sha = _read_json(
        inventory_path, "ordinary-patch inventory"
    )
    classification, classification_file, classification_sha = _read_json(
        classification_path, "ordinary-patch contact classification"
    )
    material_map, material_file, material_sha = _read_json(
        material_map_path, "ordinary-patch material map"
    )

    _require(
        inventory.get("schema") == "wood_joint_current_patch_inputs/v1",
        "unexpected ordinary-patch inventory schema",
    )
    candidate = inventory.get("candidate", {})
    _require(
        candidate.get("revision_id") == REVISION_ID
        and candidate.get("implementation_revision") == IMPLEMENTATION_REVISION,
        "inventory is not the owner-reviewed current revision",
    )
    _require(
        inventory.get("status") == "current_geometry_patch_inputs_only",
        "inventory is outside the geometry-only input scope",
    )
    _require(
        classification.get("schema")
        == "wood_joint_current_patch_contact_classification/v1",
        "unexpected contact-classification schema",
    )
    _require(
        classification.get("status")
        == "CURRENT_PATCH_CONTACT_GEOMETRY_INCOMPLETE_RESPONSE_UNREADY",
        "contact classification is not the frozen geometry-only result",
    )
    class_binding = classification.get("candidate_binding", {})
    _require(
        class_binding.get("inventory_sha256") == inventory_sha
        and class_binding.get("revision_id") == REVISION_ID
        and class_binding.get("implementation_revision") == IMPLEMENTATION_REVISION,
        "classification does not bind the supplied frozen inventory",
    )
    _require(
        material_map.get("schema") == "wood_joint_current_patch_material_binding/v1",
        "unexpected material-map schema",
    )
    material_inventory_binding = material_map.get("input_bindings", {}).get(
        "inventory", {}
    )
    _require(
        material_inventory_binding.get("sha256") == inventory_sha
        and material_map.get("candidate", {}).get("revision_id") == REVISION_ID,
        "material map does not bind the supplied frozen inventory",
    )
    _require(
        SOURCE_INVENTORY.is_file()
        and _file_sha256(SOURCE_INVENTORY) == candidate.get("source_inventory_sha256"),
        "pinned source inventory is missing or changed",
    )

    wood_rows = {row["part_id"]: row for row in inventory.get("wood_bodies", [])}
    _require(set(wood_rows) == set(WOOD_IDS), "inventory wood-body identities changed")
    _require(
        len(inventory.get("physical_bolts", [])) == 4
        and len(inventory.get("wood_interfaces", [])) == 3,
        "inventory is not the three-wood/four-bolt ordinary patch",
    )
    _require(
        {row.get("physical_bolt_id") for row in inventory["physical_bolts"]}
        == EXPECTED_BOLTS,
        "ordinary-patch bolt axes changed",
    )

    # The cleat local N axis is the chain's declared transverse-displacement
    # direction. The stock/grain metadata remains proposal-only.
    grain = {}
    for body_id in WOOD_IDS:
        grain_record = wood_rows[body_id].get("grain", {})
        grain[body_id] = _vec3(
            grain_record.get("grain_axis_global_xyz"), f"{body_id} grain axis"
        )
    direction_n = _unit(grain[CLEAT_ID], "cleat grain N")
    for body_id in WOOD_IDS:
        _require(
            abs(_norm(grain[body_id]) - 1.0) <= VECTOR_TOLERANCE,
            f"{body_id} grain axis is not a unit vector",
        )

    # Verify that the exact material-map long-axis vectors used for this patch
    # agree with the frozen input grain record for both R/T alternatives.
    alternatives = material_map.get("wood_orientation_alternatives", [])
    _require(
        {row.get("case_id") for row in alternatives}
        == {"source_transverse_a", "source_transverse_b"},
        "material-map ring alternatives changed",
    )
    grain_local_names: dict[str, str] = {}
    for alternative_index, alternative in enumerate(alternatives):
        body_orientations = {
            row["part_id"]: row for row in alternative.get("body_orientations", [])
        }
        _require(
            set(body_orientations) == set(WOOD_IDS), "material-map body set changed"
        )
        for body_id in WOOD_IDS:
            mapped = _vec3(
                body_orientations[body_id].get("grain_axis_global_xyz"),
                f"{alternative['case_id']} {body_id} grain axis",
            )
            _require(
                _norm(tuple(a - b for a, b in zip(mapped, grain[body_id], strict=True)))
                <= VECTOR_TOLERANCE,
                f"material-map grain axis differs for {body_id}",
            )
            local_name = str(body_orientations[body_id]["grain_axis_local_name"])
            if alternative_index == 0:
                grain_local_names[body_id] = local_name
            else:
                _require(
                    grain_local_names[body_id] == local_name,
                    f"material-map grain-axis label differs for {body_id}",
                )

    inventory_interfaces = {
        row["interface_id"]: row for row in inventory.get("wood_interfaces", [])
    }
    class_interfaces = {
        row["interface_id"]: row for row in classification.get("wood_interfaces", [])
    }
    _require(
        set(inventory_interfaces) == set(class_interfaces)
        and set(INTERFACE_PATH) | {DIRECT_INTERFACE_ID} == set(inventory_interfaces),
        "wood-interface identities changed",
    )

    interface_records: dict[str, dict[str, Any]] = {}
    for interface_id, inventory_interface in inventory_interfaces.items():
        classified = class_interfaces[interface_id]
        _require(
            classified.get("load_transfer_law_assigned") is False
            and classified.get("active_pressure_claim") is False,
            f"{interface_id}: classification now claims active contact response",
        )
        source_pairs = inventory_interface.get("actual_face_pairs", [])
        _require(
            len(source_pairs) == 1,
            f"{interface_id}: expected one source finite face pair",
        )
        source_pair = source_pairs[0]
        face_records = []
        for side, member_field in (
            ("first_face", "first_member"),
            ("second_face", "second_member"),
        ):
            face = classified.get(side, {})
            body_id = face.get("body_id")
            normal_raw = face.get("outward_normal_global_xyz")
            normal = _unit(normal_raw, f"{interface_id} {side} outward normal")
            source_face = source_pair[side]
            source_normal = _unit(
                source_face.get("normal_global_xyz"),
                f"{interface_id} source {side} normal",
            )
            _require(
                body_id == source_pair[member_field]
                and face.get("face_sha256") == source_face.get("cad_face_sha256")
                and _dot(normal, source_normal) >= 1.0 - VECTOR_TOLERANCE,
                f"{interface_id} {side}: classifier face no longer matches inventory",
            )
            alignment = _dot(normal, direction_n)
            _require(
                abs(alignment) <= VECTOR_TOLERANCE,
                f"{interface_id}: face normal is not transverse to cleat-grain N",
            )
            face_records.append(
                {
                    "body_id": body_id,
                    "mesh_body_id": face.get("mesh_body_id"),
                    "source_cad_face_sha256": source_face["cad_face_sha256"],
                    "classified_face_sha256": face["face_sha256"],
                    "outward_normal_global_xyz": list(normal_raw),
                    "unit_normal_dot_cleat_N": _rounded(alignment),
                    "normal_only_face_contact_resists_cleat_N": False,
                }
            )
        _require(
            _dot(
                _unit(face_records[0]["outward_normal_global_xyz"], "first normal"),
                _unit(face_records[1]["outward_normal_global_xyz"], "second normal"),
            )
            <= -1.0 + VECTOR_TOLERANCE,
            f"{interface_id}: opposed interface normals are not antiparallel",
        )
        source_face = inventory_interface.get("actual_face_pairs", [{}])[0]
        _require(
            source_face.get("measured_plane_gap_mm") == 0.0
            or abs(float(source_face.get("measured_plane_gap_mm", math.inf)))
            <= GEOMETRY_TOLERANCE_MM,
            f"{interface_id}: source faces are no longer coincident",
        )
        interface_records[interface_id] = {
            "members": list(inventory_interface.get("members", [])),
            "source_finite_overlap_area_mm2": _rounded(
                float(inventory_interface["finite_overlap_area_mm2"])
            ),
            "source_finite_overlap_centroid_global_xyz_mm": list(
                inventory_interface["finite_overlap_area_centroid_global_xyz_mm"]
            ),
            "opposed_face_normals": face_records,
            "contact_law_assigned": False,
            "active_pressure_established": False,
        }

    bolt_rows = {
        row["physical_bolt_id"]: row for row in inventory.get("physical_bolts", [])
    }
    bore_pairs = {
        row["physical_bolt_id"]: row
        for row in classification.get("bolt_receiver_bore_pairs", [])
    }
    _require(
        set(bore_pairs) == EXPECTED_BOLTS, "classified bolt receiver pairs changed"
    )

    bolt_records: dict[str, dict[str, Any]] = {}
    for bolt_id in sorted(EXPECTED_BOLTS):
        bolt = bolt_rows[bolt_id]
        pair = bore_pairs[bolt_id]
        axis_raw = bolt["axis_direction_head_to_nut_global_xyz"]
        axis = _unit(axis_raw, f"{bolt_id} axis")
        axis_n_dot = _dot(axis, direction_n)
        _require(
            abs(axis_n_dot) <= VECTOR_TOLERANCE,
            f"{bolt_id}: bolt axis is not transverse to cleat-grain N",
        )
        _require(
            pair.get("radial_gap_is_explicitly_open") is True
            and pair.get("contact_active") is False
            and pair.get("bolt_to_wood_bearing_law_assigned") is False,
            f"{bolt_id}: receiver gap is no longer the unengaged geometry case",
        )
        receivers = pair.get("receiver_bore_walls", [])
        _require(len(receivers) == 2, f"{bolt_id}: expected two receiver bores")
        _require(
            {row.get("receiver_id") for row in receivers}
            == set(bolt.get("receivers_head_to_nut", [])),
            f"{bolt_id}: receiver membership differs from inventory",
        )
        receiver_rows = []
        gap_sums = []
        for receiver in receivers:
            clearance = float(receiver["radial_clearance_mm"])
            bore_radius = float(receiver["fitted_bore_radius_mm"])
            shaft_radius = float(receiver["shaft_radius_mm"])
            line_distance = float(receiver["fitted_bore_axis_line_distance_mm"])
            _require(
                abs(clearance - EXPECTED_CLEARANCE_MM) <= GEOMETRY_TOLERANCE_MM
                and abs((bore_radius - shaft_radius) - clearance)
                <= GEOMETRY_TOLERANCE_MM,
                f"{bolt_id}/{receiver['receiver_id']}: receiver radial gap changed",
            )
            _require(
                receiver.get("radial_status") == "OPEN_RADIAL_CLEARANCE"
                and receiver.get("status")
                == "CYLINDRICAL_BORE_WALL_BOUND_TO_DECLARED_AXIS"
                and abs(float(receiver.get("fitted_bore_axis_alignment", 0.0)) - 1.0)
                <= VECTOR_TOLERANCE
                and line_distance <= GEOMETRY_TOLERANCE_MM,
                f"{bolt_id}/{receiver['receiver_id']}: receiver axis fit changed",
            )
            receiver_rows.append(
                {
                    "receiver_id": receiver["receiver_id"],
                    "radial_clearance_mm": _rounded(clearance),
                    "bore_radius_mm": _rounded(bore_radius),
                    "shaft_radius_mm": _rounded(shaft_radius),
                    "fitted_bore_axis_alignment": _rounded(
                        float(receiver["fitted_bore_axis_alignment"])
                    ),
                    "fitted_bore_axis_line_distance_mm": _rounded(line_distance),
                }
            )
            gap_sums.append(clearance)
        free_travel = math.fsum(gap_sums)
        interface_id = next(
            (
                interface
                for interface, data in inventory_interfaces.items()
                if bolt_id in data.get("bolt_axis_ids", [])
            ),
            None,
        )
        _require(
            interface_id in INTERFACE_PATH,
            f"{bolt_id}: bolt is outside chain interfaces",
        )
        _require(
            set(pair.get("bore_receiver_membership", []))
            == set(inventory_interfaces[interface_id].get("members", [])),
            f"{bolt_id}: bolt receivers do not match wood interface",
        )
        # Each fastener axis must be normal to its own wood contact face, and
        # transverse to the N translation being screened.
        contact_normals = interface_records[interface_id]["opposed_face_normals"]
        _require(
            all(
                abs(
                    _dot(
                        axis,
                        _unit(face["outward_normal_global_xyz"], "interface normal"),
                    )
                )
                >= 1.0 - VECTOR_TOLERANCE
                for face in contact_normals
            ),
            f"{bolt_id}: axis does not follow its classified face normal",
        )
        bolt_records[bolt_id] = {
            "interface_id": interface_id,
            "receivers": list(bolt.get("receivers_head_to_nut", [])),
            "axis_origin_global_xyz_mm": list(bolt["axis_origin_global_xyz_mm"]),
            "axis_direction_head_to_nut_global_xyz": list(axis_raw),
            "unit_axis_dot_cleat_N": _rounded(axis_n_dot),
            "axis_parallel_to_wood_interface_normal": True,
            "receiver_bores": receiver_rows,
            "freely_floating_pin_relative_center_travel_mm": _rounded(free_travel),
        }

    per_interface = []
    for interface_id in INTERFACE_PATH:
        axes = inventory_interfaces[interface_id].get("bolt_axis_ids", [])
        _require(len(axes) == 2, f"{interface_id}: expected two current bolt axes")
        bolt_travels = [
            bolt_records[axis]["freely_floating_pin_relative_center_travel_mm"]
            for axis in axes
        ]
        interface_travel = min(bolt_travels)
        _require(
            max(bolt_travels) - min(bolt_travels) <= GEOMETRY_TOLERANCE_MM,
            f"{interface_id}: two bolts do not permit a common translation disk",
        )
        per_interface.append(
            {
                "interface_id": interface_id,
                "members": list(inventory_interfaces[interface_id]["members"]),
                "bolt_axis_ids": list(axes),
                "individual_bolt_center_separation_mm": bolt_travels,
                "common_translation_only_free_travel_mm": _rounded(interface_travel),
                "interpretation": (
                    "Each receiver contributes its 0.575 mm radial disk; freely translating "
                    "pins give the 1.15 mm wood-center-axis separation disk."
                ),
            }
        )

    direct = interface_records[DIRECT_INTERFACE_ID]
    direct_face_tangent = all(
        abs(float(face["unit_normal_dot_cleat_N"])) <= VECTOR_TOLERANCE
        for face in direct["opposed_face_normals"]
    )
    _require(
        direct_face_tangent,
        "direct rail-principal wood face now has N-normal component",
    )
    chain_travel = math.fsum(
        row["common_translation_only_free_travel_mm"] for row in per_interface
    )

    result: dict[str, Any] = {
        "schema": SCHEMA,
        "status": STATUS,
        "candidate": {
            "revision_id": REVISION_ID,
            "implementation_revision": IMPLEMENTATION_REVISION,
            "ordinary_patch_wood_body_count": len(wood_rows),
            "ordinary_patch_physical_bolt_count": len(bolt_rows),
        },
        "input_bindings": {
            "inventory": {
                "path": _display_path(inventory_file),
                "sha256": inventory_sha,
            },
            "classification": {
                "path": _display_path(classification_file),
                "sha256": classification_sha,
            },
            "material_map": {
                "path": _display_path(material_file),
                "sha256": material_sha,
            },
            "source_inventory": {
                "path": _display_path(SOURCE_INVENTORY),
                "sha256": candidate["source_inventory_sha256"],
            },
        },
        "producer_binding": {
            "path": _display_path(Path(__file__).resolve()),
            "sha256": _file_sha256(Path(__file__).resolve()),
        },
        "direction": {
            "name": "cleat longitudinal grain N",
            "global_unit_vector": list(direction_n),
            "source_grain_axis_global_xyz": list(grain[CLEAT_ID]),
            "basis": wood_rows[CLEAT_ID]["grain"]["grain_basis"],
            "stock_observed": False,
        },
        "member_grain_axes": {
            body_id: {
                "grain_axis_local_name": grain_local_names[body_id],
                "grain_axis_global_xyz": list(grain[body_id]),
                "unit_dot_cleat_N": _rounded(
                    _dot(_unit(grain[body_id], body_id), direction_n)
                ),
                "source_basis": wood_rows[body_id]["grain"]["grain_basis"],
            }
            for body_id in WOOD_IDS
        },
        "bolts": bolt_records,
        "wood_interfaces": interface_records,
        "chain": {
            "direction_name": "cleat longitudinal grain N",
            "route_member_order": [RAIL_ID, CLEAT_ID, PRINCIPAL_ID],
            "bolted_interfaces_in_order": per_interface,
            "translation_only_freely_floating_pin_travel_mm": _rounded(chain_travel),
            "direct_rail_to_principal_face_interface_id": DIRECT_INTERFACE_ID,
            "direct_face_normals_are_tangent_to_N": True,
            "direct_wood_face_normal_contact_resists_N": False,
            "direct_face_limitation": (
                "The direct rail-principal planar faces have normals +/-global X, orthogonal "
                "to cleat N. Normal-only face contact therefore supplies no N resistance; "
                "friction/contact pressure is unassigned."
            ),
            "interpretation": (
                "The two independently clearanced bolt interfaces are in series; their "
                "translation-only freely floating travel sums to 2.30 mm. This is a "
                "conditional seating-travel calculation, not stiffness or an assembly bound."
            ),
        },
        "scope": {
            "geometry_and_seating_travel_only": True,
            "center_axis_disk_clearance_only": True,
            "member_translations_screened": True,
            "member_rotations_included": False,
            "member_rotations_constrained_or_accepted": False,
            "pin_translation_is_unrestrained_by_washers_or_nuts": True,
            "friction_or_preload_assigned": False,
            "contact_law_assigned": False,
            "stiffness_assigned": False,
            "loads_assigned": False,
            "capacity_claim": False,
            "native_solve_run": False,
            "cad_or_mesh_created": False,
            "limitations": [
                "The values are for ideal freely translating pins and two receiver bores each with the classified radial clearance.",
                "The calculation omits member rotations; it neither pins rotations nor establishes free travel for the full deformable assembly.",
                "Actual washer restraint, preload, friction, tolerances, timber contact law, and bolt response are not represented.",
                "Only the three source-classified wood-face interfaces are checked; no other edge-contact or interference response is inferred.",
                "Source grain directions are geometry metadata proposals and are not observations of delivered stock.",
                "This witness assigns no force transfer, stiffness, response, or resistance.",
            ],
        },
    }
    result["record_sha256"] = _canonical_sha256(result)
    return result
