"""Bounded full-layout WJ24 bolt counterhold and shaft-withdrawal probe.

This module consumes an already materialized WJ24 composition. It does not
compose, solve, mutate, or release geometry. The first pass screens only
sampled seated wrench-envelope poses and a conservative continuous linear
translation enclosure for ordinary five-role stacks. Four WJ05 backer stacks
remain ``scope_not_modeled`` until their open/lifted support state and below
access route are supplied.

Catalog dimensions are sourced from the existing ordinary WJ04 prototype
profile. That profile is used as a broad external envelope only; it is not a
selected SKU fit for any WJ24 fastener. The output is diagnostic evidence and
never establishes physical fit, turning, installation, disassembly, support,
or acceptance.
"""

from __future__ import annotations

import hashlib
import json
import math
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import cadquery as cq
from OCP.BRepAdaptor import BRepAdaptor_Surface

from mini_moonboard.wood_joint_wj04_config import WJ04_TRIAL
from scripts import wood_joint_wj04_tool_access as wj04_tools
from scripts import wood_joint_wj12_diagnostic as wj12_diagnostic

ROOT = Path(__file__).resolve().parents[1]
COMPOSITION_PATH = (
    ROOT / "docs/wood-joints-mvp/hypotheses/wj24-integrated-static/composition.json"
)
DIAGNOSTIC_PATH = (
    ROOT / "docs/wood-joints-mvp/hypotheses/wj24-integrated-static/diagnostic.json"
)
INVENTORY_PATH = (
    ROOT / "docs/wood-joints-mvp/hypotheses/wj24-hardware-inventory/inventory.json"
)
SCHEMA = "wood_joint_wj24_tool_operation_probe/v1"
EXPECTED_LAYOUT_ID = "wj24-twenty-four-duty-integrated-static-v1"
EXPECTED_TRIAL_ID = "wj24-wj18-plus-top-center-bottom-pairs-v1"
ORDINARY_ROLES = frozenset({"head", "head_washer", "shaft", "nut", "nut_washer"})
BACKER_ROLES = frozenset(
    {"bottom_head", "bottom_washer", "shaft", "top_nut", "top_washer"}
)
PROTECTED_FAMILY_ALIASES = frozenset(
    {
        # These are duplicated by the canonical maps on WJ24ComposedGeometry.
        "fixed_66_hillman_axes_63p5mm",
        "retained_12_frame_bolt_components",
    }
)
HIT_TOLERANCE_MM3 = wj04_tools.HIT_TOLERANCE_MM3


@dataclass(frozen=True)
class AxisContract:
    axis_id: str
    family: str
    trial_id: str
    station_id: str | None
    receiver_ids: tuple[str, ...]
    role_ids: frozenset[str]


@dataclass(frozen=True)
class WJ24ArchiveContract:
    layout_id: str
    trial_id: str
    source_inventory_sha256: str
    axes: Mapping[str, AxisContract]
    family_trial_ids: Mapping[str, str]
    protected_shape_counts: Mapping[str, int]
    composition_sha256: str
    diagnostic_sha256: str
    inventory_sha256: str


def _archive_payload(
    value: Mapping[str, Any] | None, path: Path, label: str
) -> tuple[dict[str, Any], str]:
    if value is None:
        payload = path.read_bytes()
        parsed = json.loads(payload)
        if not isinstance(parsed, dict):
            raise ValueError(f"archived {label} must contain a JSON object")
        return parsed, hashlib.sha256(payload).hexdigest()
    if not isinstance(value, Mapping):
        raise TypeError(f"archived {label} must be a mapping")
    # Test callers can supply deep-copied archived payloads for mutation checks.
    # Hash the canonical JSON value so the report still fingerprints that input.
    payload = json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    return dict(value), hashlib.sha256(payload).hexdigest()


def load_archived_wj24_contract(
    composition: Mapping[str, Any] | None = None,
    inventory: Mapping[str, Any] | None = None,
    diagnostic: Mapping[str, Any] | None = None,
) -> WJ24ArchiveContract:
    """Validate and join the three frozen WJ24 artifacts by real axis IDs.

    The join deliberately uses the archived axis schedule and per-axis role
    records. Family trial IDs are an axis provenance map; family source
    fingerprints are a separate map with a different documented key set.
    They are never required to have equal keys.
    """
    composition_value, composition_sha = _archive_payload(
        composition, COMPOSITION_PATH, "WJ24 composition"
    )
    inventory_value, inventory_sha = _archive_payload(
        inventory, INVENTORY_PATH, "WJ24 hardware inventory"
    )
    diagnostic_value, diagnostic_sha = _archive_payload(
        diagnostic, DIAGNOSTIC_PATH, "WJ24 diagnostic"
    )

    expected_schemas = (
        (composition_value, "wood_joint_wj24_compositor/v1", "composition"),
        (inventory_value, "wood_joint_wj24_hardware_inventory/v1", "inventory"),
        (diagnostic_value, "wood_joint_wj24_diagnostic/v1", "diagnostic"),
    )
    for payload, schema, label in expected_schemas:
        if payload.get("schema") != schema:
            raise ValueError(f"WJ24 {label} schema must be {schema}")
        layout_id = payload.get("layout_id")
        if label == "diagnostic":
            layout_contract = payload.get("layout_contract", {})
            layout_id = (
                layout_contract.get("layout_id")
                if isinstance(layout_contract, Mapping)
                else None
            )
        if layout_id != EXPECTED_LAYOUT_ID:
            raise ValueError(f"WJ24 {label} layout ID changed")
        if payload.get("trial_id") != EXPECTED_TRIAL_ID:
            raise ValueError(f"WJ24 {label} trial ID changed")

    composition_axes = composition_value.get("candidate_axes")
    inventory_schedule = inventory_value.get("candidate_hardware_axis_schedule")
    if not isinstance(composition_axes, Mapping):
        raise TypeError("WJ24 composition candidate_axes must be a mapping")
    if not isinstance(inventory_schedule, list):
        raise TypeError(
            "WJ24 inventory candidate_hardware_axis_schedule must be a list"
        )
    if len(composition_axes) != 104 or len(inventory_schedule) != 104:
        raise ValueError(
            "WJ24 archive contract must contain exactly 104 candidate axes"
        )

    schedule_by_id: dict[str, Mapping[str, Any]] = {}
    for row in inventory_schedule:
        if not isinstance(row, Mapping):
            raise TypeError("WJ24 inventory schedule rows must be mappings")
        axis_id = row.get("axis_id")
        if not isinstance(axis_id, str) or not axis_id:
            raise ValueError(
                "WJ24 inventory schedule axis_id must be a nonempty string"
            )
        if axis_id in schedule_by_id:
            raise ValueError(f"WJ24 inventory schedule duplicates axis {axis_id!r}")
        schedule_by_id[axis_id] = row
    if set(schedule_by_id) != set(composition_axes):
        raise ValueError("WJ24 composition and inventory axis IDs differ")

    family_trials = composition_value.get("family_trial_ids")
    if not isinstance(family_trials, Mapping) or len(family_trials) != 10:
        raise ValueError("WJ24 composition must retain ten family trial bindings")
    axes: dict[str, AxisContract] = {}
    for axis_id, composed in composition_axes.items():
        if not isinstance(composed, Mapping):
            raise TypeError(f"WJ24 composition axis {axis_id!r} must be a mapping")
        scheduled = schedule_by_id[axis_id]
        family = composed.get("family")
        trial_id = composed.get("trial_id")
        station_id = composed.get("station_id")
        receiver_ids = composed.get("receiver_ids")
        roles = composed.get("installed_role_ids")
        scheduled_receivers = scheduled.get("ordered_receiver_ids_from_candidate_bore")
        scheduled_roles = scheduled.get("installed_cad_role_ids")
        if not isinstance(family, str) or not isinstance(trial_id, str):
            raise TypeError(f"WJ24 axis {axis_id!r} lacks family/trial provenance")
        # The archived family_trial_ids map uses lineage labels that are not
        # always identical to the per-axis family strings (for example
        # ``center_x190`` vs ``wj05_center_x190``). Validate values and exact
        # per-axis schedule joins; do not assume those key spaces coincide.
        if trial_id not in set(family_trials.values()):
            raise ValueError(
                f"WJ24 axis {axis_id!r} trial is absent from family bindings"
            )
        if station_id is not None and (
            not isinstance(station_id, str) or not station_id
        ):
            raise ValueError(
                f"WJ24 axis {axis_id!r} station ID must be nonempty or null"
            )
        if not isinstance(receiver_ids, list) or len(receiver_ids) != 2:
            raise ValueError(f"WJ24 axis {axis_id!r} must name two ordered receivers")
        if not isinstance(roles, list) or not roles:
            raise ValueError(f"WJ24 axis {axis_id!r} must name installed CAD roles")
        if (
            scheduled.get("family") != family
            or scheduled.get("family_trial_id") != trial_id
            or scheduled.get("station_id") != station_id
            or scheduled_receivers != receiver_ids
            or scheduled_roles != roles
            or scheduled.get("cad_role_count") != len(roles)
        ):
            raise ValueError(
                f"WJ24 inventory/composition binding differs for {axis_id!r}"
            )
        role_set = frozenset(roles)
        if role_set not in (ORDINARY_ROLES, BACKER_ROLES):
            raise ValueError(f"WJ24 axis {axis_id!r} has an unsupported role set")
        axes[axis_id] = AxisContract(
            axis_id=axis_id,
            family=family,
            trial_id=trial_id,
            station_id=station_id,
            receiver_ids=tuple(receiver_ids),
            role_ids=role_set,
        )

    diagnostic_counts = diagnostic_value.get("counts_and_ids")
    if not isinstance(diagnostic_counts, Mapping):
        raise TypeError("WJ24 diagnostic counts_and_ids must be a mapping")
    diagnostic_axes = diagnostic_counts.get("candidate_bore_axes")
    diagnostic_hardware = diagnostic_counts.get("candidate_installed_hardware_axes")
    if not isinstance(diagnostic_axes, Mapping) or not isinstance(
        diagnostic_hardware, Mapping
    ):
        raise TypeError("WJ24 diagnostic must report candidate bore and hardware axes")
    axis_ids = set(axes)
    if (
        diagnostic_axes.get("actual") != 104
        or diagnostic_axes.get("expected") != 104
        or diagnostic_axes.get("ids_match_layout") is not True
        or not isinstance(diagnostic_axes.get("ids"), list)
        or len(diagnostic_axes["ids"]) != 104
        or set(diagnostic_axes["ids"]) != axis_ids
    ):
        raise ValueError("WJ24 diagnostic candidate bore axis IDs differ from archive")
    if (
        diagnostic_hardware.get("actual") != 104
        or diagnostic_hardware.get("expected") != 104
        or diagnostic_hardware.get("component_count") != 520
        or diagnostic_hardware.get("expected_component_count") != 520
        or diagnostic_hardware.get("ids_match_candidate_bores") is not True
        or diagnostic_hardware.get("ids_match_layout") is not True
    ):
        raise ValueError(
            "WJ24 diagnostic installed-hardware counts differ from archive"
        )

    composition_counts = composition_value.get("counts")
    inventory_counts = inventory_value.get("counts")
    if not isinstance(composition_counts, Mapping) or not isinstance(
        inventory_counts, Mapping
    ):
        raise TypeError("WJ24 composition and inventory counts must be mappings")
    if (
        composition_counts.get("candidate_bores") != 104
        or composition_counts.get("candidate_installed_hardware_axes") != 104
        or composition_counts.get("candidate_installed_hardware_components") != 520
        or composition_counts.get("candidate_parts") != 28
        or composition_counts.get("target_duties") != 24
        or inventory_counts.get("candidate_bore_axes") != 104
        or inventory_counts.get("installed_candidate_cad_role_shapes") != 520
    ):
        raise ValueError("WJ24 archived composition/inventory count contract changed")

    fingerprint_families = composition_value.get("family_source_fingerprints_sha256")
    if not isinstance(fingerprint_families, Mapping):
        raise TypeError("WJ24 composition family fingerprints must be a mapping")
    # Intentionally no key-equality test here: archived family trials and
    # fingerprints describe different lineage sets (10 versus 9 currently).

    source_inventory_sha = composition_value.get("source", {}).get(
        "source_inventory_sha256"
    )
    diagnostic_binding = diagnostic_value.get("source_binding", {})
    inventory_provenance = inventory_value.get("source_provenance", {})
    inventory_sha_claims = {
        source_inventory_sha,
        diagnostic_binding.get("inventory_sha256"),
        diagnostic_binding.get("binding_inventory_sha256"),
        inventory_provenance.get("source_inventory_sha256"),
        inventory_provenance.get("source_binding_inventory_sha256"),
    }
    if len(inventory_sha_claims) != 1 or not isinstance(source_inventory_sha, str):
        raise ValueError("WJ24 archived source-inventory SHA bindings disagree")

    diagnostic_gates = diagnostic_value.get("diagnostic_gates", {})
    if (
        not isinstance(diagnostic_gates, Mapping)
        or diagnostic_gates.get("movement_or_installation_access_proven") is not False
    ):
        raise ValueError("WJ24 archived static diagnostic must leave access unproven")

    protected_counts = composition_value.get("protected_shape_counts")
    if not isinstance(protected_counts, Mapping):
        raise TypeError("WJ24 protected shape counts must be a mapping")
    return WJ24ArchiveContract(
        layout_id=EXPECTED_LAYOUT_ID,
        trial_id=EXPECTED_TRIAL_ID,
        source_inventory_sha256=source_inventory_sha,
        axes=axes,
        family_trial_ids=dict(family_trials),
        protected_shape_counts={
            key: int(value) for key, value in protected_counts.items()
        },
        composition_sha256=composition_sha,
        diagnostic_sha256=diagnostic_sha,
        inventory_sha256=inventory_sha,
    )


def _valid_shape(value: Any, name: str) -> cq.Shape:
    if not isinstance(value, cq.Shape) or not value.isValid() or not value.Solids():
        raise ValueError(f"{name} must be a valid solid CAD shape")
    return value


def _validate_runtime_geometry(geometry: Any, contract: WJ24ArchiveContract) -> None:
    if getattr(geometry, "layout_id", None) != contract.layout_id:
        raise ValueError("tool operation probe requires the fixed WJ24 layout")
    if getattr(geometry, "trial_id", None) != contract.trial_id:
        raise ValueError("tool operation probe requires the fixed WJ24 trial")
    if (
        getattr(geometry, "source_inventory_sha256", None)
        != contract.source_inventory_sha256
    ):
        raise ValueError(
            "WJ24 runtime geometry inventory SHA differs from archived contract"
        )

    bores = getattr(geometry, "candidate_bores", None)
    hardware = getattr(geometry, "candidate_installed_hardware", None)
    if not isinstance(bores, Mapping) or not isinstance(hardware, Mapping):
        raise TypeError("WJ24 geometry must supply bore and installed hardware maps")
    if set(bores) != set(contract.axes) or set(hardware) != set(contract.axes):
        raise ValueError("WJ24 runtime axis IDs differ from archived 104-axis contract")
    if len(getattr(geometry, "finished_hosts", {})) != 16:
        raise ValueError(
            "WJ24 runtime geometry must retain all 16 composed source hosts"
        )
    if len(getattr(geometry, "finished_candidate_parts", {})) != 28:
        raise ValueError("WJ24 runtime geometry must retain all 28 candidate parts")
    if len(getattr(geometry, "fixed_axes", {})) != 66:
        raise ValueError("WJ24 runtime geometry must retain all 66 fixed panel axes")
    if len(getattr(geometry, "frame_bolt_records", ())) != 12:
        raise ValueError("WJ24 runtime geometry must retain all 12 frame-bolt records")
    if len(getattr(geometry, "frame_bolt_shapes", {})) != 72:
        raise ValueError("WJ24 runtime geometry must retain all 72 frame-bolt shapes")

    runtime_family_trials = getattr(geometry, "family_trial_ids", None)
    if not isinstance(runtime_family_trials, Mapping) or dict(
        runtime_family_trials
    ) != dict(contract.family_trial_ids):
        raise ValueError("WJ24 runtime family trial IDs differ from archived bindings")

    for axis_id, axis in contract.axes.items():
        bore = bores[axis_id]
        if (
            getattr(bore, "axis_id", None) != axis_id
            or getattr(bore, "family", None) != axis.family
            or getattr(bore, "trial_id", None) != axis.trial_id
            or getattr(bore, "station_id", None) != axis.station_id
            or tuple(getattr(bore, "receiver_ids", ())) != axis.receiver_ids
        ):
            raise ValueError(f"WJ24 runtime bore provenance differs for {axis_id!r}")
        _valid_shape(getattr(bore, "shape", None), f"candidate_bores/{axis_id}")
        roles = hardware[axis_id]
        if not isinstance(roles, Mapping) or set(roles) != set(axis.role_ids):
            raise ValueError(f"WJ24 runtime hardware roles differ for {axis_id!r}")
        for role, shape in roles.items():
            _valid_shape(shape, f"candidate_installed_hardware/{axis_id}/{role}")

    protected = getattr(geometry, "protected", None)
    if not isinstance(protected, Mapping):
        raise TypeError("WJ24 runtime geometry must retain protected scene maps")
    for family, expected_count in contract.protected_shape_counts.items():
        if family in PROTECTED_FAMILY_ALIASES:
            continue
        shape_map = protected.get(family)
        if not isinstance(shape_map, Mapping) or len(shape_map) != expected_count:
            raise ValueError(
                f"WJ24 runtime protected family {family!r} differs from archived count"
            )
        for shape_id, shape in shape_map.items():
            _valid_shape(shape, f"protected/{family}/{shape_id}")


def _scene_obstacles(geometry: Any) -> dict[str, cq.Shape]:
    """Build the retained-scene map without duplicating canonical aliases."""
    _raw_receivers, finished_wood = wj12_diagnostic._composed_wood(geometry)
    result: dict[str, cq.Shape] = {
        f"wood/{name}": shape for name, shape in finished_wood.items()
    }
    result.update(
        {
            f"fixed_panel_axis/{name}": shape
            for name, shape in geometry.fixed_axes.items()
        }
    )
    result.update(
        {
            f"frame_bolt/{name}": shape
            for name, shape in geometry.frame_bolt_shapes.items()
        }
    )
    for family, shapes in geometry.protected.items():
        if family in PROTECTED_FAMILY_ALIASES:
            continue
        for shape_id, shape in shapes.items():
            result[f"protected/{family}/{shape_id}"] = shape
    for axis_id, role_map in geometry.candidate_installed_hardware.items():
        for role, shape in role_map.items():
            result[f"candidate_stack/{axis_id}/{role}"] = shape
    if len(result) < 520:
        raise ValueError("WJ24 retained obstacle scene is unexpectedly incomplete")
    return result


def _vector_unit(value: cq.Vector, name: str) -> cq.Vector:
    if not all(math.isfinite(component) for component in value.toTuple()):
        raise ValueError(f"{name} must be finite")
    if value.Length <= 1e-9:
        raise ValueError(f"{name} must be nonzero")
    return value.normalized()


def _shape_center(shape: cq.Shape) -> cq.Vector:
    center = shape.Center()
    if not all(math.isfinite(component) for component in center.toTuple()):
        raise ValueError("hardware shape center must be finite")
    return center


def _axis_reference(outward: cq.Vector) -> cq.Vector:
    cardinal = min(
        (cq.Vector(1, 0, 0), cq.Vector(0, 1, 0), cq.Vector(0, 0, 1)),
        key=lambda candidate: abs(candidate.dot(outward)),
    )
    return _vector_unit(cardinal - outward * cardinal.dot(outward), "face reference")


def _projected_vertex_extrema(shape: cq.Shape, axis: cq.Vector) -> tuple[float, float]:
    values = [vertex.Center().dot(axis) for vertex in shape.Vertices()]
    if not values or not all(math.isfinite(value) for value in values):
        raise ValueError("projection requires finite shape vertices")
    return min(values), max(values)


def _exact_cylindrical_translation_sweep(
    shape: cq.Shape, displacement_xyz_mm: Any
) -> cq.Shape | None:
    """Reconstruct an exact straight sweep for a single solid right cylinder.

    The reconstruction is accepted only for one valid solid with one full
    cylindrical side face, two planar end faces normal to the cylinder axis,
    matching volume, and a requested translation parallel to that axis. Other
    shapes return ``None`` for the conservative oriented-box fallback.
    """
    displacement = cq.Vector(displacement_xyz_mm)
    if not all(math.isfinite(value) for value in displacement.toTuple()):
        raise ValueError("shaft translation must be finite")
    if displacement.Length <= 1e-12:
        return shape
    solids = shape.Solids()
    faces = shape.Faces()
    cylindrical_faces = [face for face in faces if face.geomType() == "CYLINDER"]
    planar_faces = [face for face in faces if face.geomType() == "PLANE"]
    if len(solids) != 1 or len(cylindrical_faces) != 1 or len(planar_faces) != 2:
        return None
    surface_cylinder = BRepAdaptor_Surface(
        cylindrical_faces[0].wrapped, True
    ).Cylinder()
    radius = float(surface_cylinder.Radius())
    surface_axis = surface_cylinder.Axis()
    cylinder_direction = _vector_unit(
        cq.Vector(
            surface_axis.Direction().X(),
            surface_axis.Direction().Y(),
            surface_axis.Direction().Z(),
        ),
        "shaft cylinder axis",
    )
    motion_direction = _vector_unit(displacement, "shaft translation direction")
    if abs(cylinder_direction.dot(motion_direction)) < 1.0 - 1e-9:
        return None
    if any(
        abs(
            _vector_unit(face.normalAt(), "shaft end-face normal").dot(
                cylinder_direction
            )
        )
        < 1.0 - 1e-8
        for face in planar_faces
    ):
        return None
    low, high = _projected_vertex_extrema(shape, motion_direction)
    shaft_length = high - low
    if not math.isfinite(radius) or radius <= 0 or shaft_length <= 1e-9:
        return None
    expected_volume = math.pi * radius * radius * shaft_length
    if abs(float(shape.Volume()) - expected_volume) > max(1e-5, expected_volume * 1e-8):
        return None
    location = surface_axis.Location()
    axis_point = cq.Vector(location.X(), location.Y(), location.Z())
    start = axis_point + motion_direction * (low - axis_point.dot(motion_direction))
    result = cq.Solid.makeCylinder(
        radius, shaft_length + displacement.Length, start, motion_direction
    )
    if not result.isValid() or len(result.Solids()) != 1:
        return None
    swept_volume = math.pi * radius * radius * (shaft_length + displacement.Length)
    if abs(float(result.Volume()) - swept_volume) > max(1e-5, swept_volume * 1e-8):
        return None
    return result


def _paired_wrench_pose_overlap(first: cq.Shape, second: cq.Shape) -> float:
    a, b = first.BoundingBox(), second.BoundingBox()
    if (
        a.xmax <= b.xmin
        or b.xmax <= a.xmin
        or a.ymax <= b.ymin
        or b.ymax <= a.ymin
        or a.zmax <= b.zmin
        or b.zmax <= a.zmin
    ):
        return 0.0
    return max(0.0, float(first.intersect(second).Volume()))


def _counterhold_screen(
    axis_id: str,
    roles: Mapping[str, cq.Shape],
    obstacles: Mapping[str, cq.Shape],
    tool_candidate: Any,
) -> dict[str, Any]:
    head_key = f"candidate_stack/{axis_id}/head"
    nut_key = f"candidate_stack/{axis_id}/nut"
    shaft_key = f"candidate_stack/{axis_id}/shaft"
    head = roles["head"]
    nut = roles["nut"]
    outward = _vector_unit(_shape_center(head) - _shape_center(nut), f"{axis_id} axis")
    nut_outward = -outward
    axis_point = (_shape_center(head) + _shape_center(nut)) * 0.5
    head_center = wj04_tools._seated_tool_center(
        axis_point.toTuple(), outward, head, tool_candidate.head_thickness_mm
    )
    nut_center = wj04_tools._seated_tool_center(
        axis_point.toTuple(), nut_outward, nut, tool_candidate.head_thickness_mm
    )
    reference = _axis_reference(outward)
    headings = tuple(float(value) for value in tool_candidate.head_offsets_degrees)
    head_tools: dict[float, cq.Shape] = {}
    nut_tools: dict[float, cq.Shape] = {}
    head_checks = {}
    nut_checks = {}
    for heading in headings:
        head_tool = wj04_tools.build_catalog_wrench_envelope(
            head_center,
            outward.toTuple(),
            reference.toTuple(),
            tool_candidate,
            offset_degrees=heading,
        )
        nut_tool = wj04_tools.build_catalog_wrench_envelope(
            nut_center,
            nut_outward.toTuple(),
            reference.toTuple(),
            tool_candidate,
            offset_degrees=heading,
        )
        head_tools[heading] = head_tool
        nut_tools[heading] = nut_tool
        head_checks[str(heading)] = wj04_tools.collision_report(
            {"head_seated_pose": head_tool},
            obstacles,
            excluded_target_ids=(head_key, shaft_key),
            exclusion_scope=(
                "The active target head and its own shaft are excluded to permit "
                "nominal intended head contact. Both washers and all other scene "
                "geometry remain obstacles."
            ),
        )
        nut_checks[str(heading)] = wj04_tools.collision_report(
            {"nut_seated_pose": nut_tool},
            obstacles,
            excluded_target_ids=(nut_key, shaft_key),
            exclusion_scope=(
                "The active target nut and its own shaft are excluded to permit "
                "nominal intended nut contact. Both washers and all other scene "
                "geometry remain obstacles."
            ),
        )

    paired = []
    for head_heading, head_tool in head_tools.items():
        for nut_heading, nut_tool in nut_tools.items():
            overlap = _paired_wrench_pose_overlap(head_tool, nut_tool)
            paired.append(
                {
                    "head_heading_sample_degrees": head_heading,
                    "nut_heading_sample_degrees": nut_heading,
                    "external_envelope_overlap_mm3": round(overlap, 6),
                    "envelopes_overlap": overlap > HIT_TOLERANCE_MM3,
                }
            )

    return {
        "status": "sampled_seated_envelopes_only",
        "method": "two_sampled_static_poses_per_end; four paired combinations",
        "heading_samples_degrees": list(headings),
        "head_pose_collision_screens": head_checks,
        "nut_pose_collision_screens": nut_checks,
        "paired_wrench_pose_overlaps": paired,
        "paired_counterhold_and_turning_established": False,
        "turning_stroke_screened": False,
        "reindex_or_reseat_screened": False,
        "jaw_fit_and_contact_established": False,
        "physical_tool_access_established": False,
    }


def _shaft_withdrawal_screen(
    axis: AxisContract,
    roles: Mapping[str, cq.Shape],
    obstacles: Mapping[str, cq.Shape],
    finished_wood: Mapping[str, cq.Shape],
) -> dict[str, Any]:
    head, head_washer, shaft = roles["head"], roles["head_washer"], roles["shaft"]
    nut = roles["nut"]
    outward = _vector_unit(
        _shape_center(head) - _shape_center(nut), f"{axis.axis_id} withdrawal axis"
    )
    missing_receivers = [
        receiver for receiver in axis.receiver_ids if receiver not in finished_wood
    ]
    if missing_receivers:
        raise ValueError(
            f"{axis.axis_id}: receiver parts missing from finished scene: {missing_receivers}"
        )
    receiver_max = max(
        _projected_vertex_extrema(finished_wood[receiver], outward)[1]
        for receiver in axis.receiver_ids
    )
    shaft_min, _shaft_max = _projected_vertex_extrema(shaft, outward)
    travel_mm = receiver_max - shaft_min
    if not math.isfinite(travel_mm) or travel_mm <= 0:
        raise ValueError(
            f"{axis.axis_id}: computed shaft withdrawal distance is not positive"
        )
    displacement = outward * travel_mm
    sweeps = {
        f"{role}_translation_enclosure": wj04_tools.translation_sweep(
            shape, displacement.toTuple()
        )
        for role, shape in (("head", head), ("head_washer", head_washer))
    }
    shaft_sweep = _exact_cylindrical_translation_sweep(shaft, displacement.toTuple())
    shaft_sweep_method = "exact_coaxial_cylinder_translation_sweep"
    if shaft_sweep is None:
        shaft_sweep = wj04_tools.translation_sweep(shaft, displacement.toTuple())
        shaft_sweep_method = "conservative_oriented_box_translation_enclosure"
    sweeps[f"shaft_{shaft_sweep_method}"] = shaft_sweep
    excluded_ids = (
        f"candidate_stack/{axis.axis_id}/head",
        f"candidate_stack/{axis.axis_id}/head_washer",
        f"candidate_stack/{axis.axis_id}/shaft",
        f"candidate_stack/{axis.axis_id}/nut",
        f"candidate_stack/{axis.axis_id}/nut_washer",
    )
    collision = wj04_tools.collision_report(
        sweeps,
        obstacles,
        excluded_target_ids=excluded_ids,
        exclusion_scope=(
            "Prerequisite state: nut and nut washer have already been fully "
            "unthreaded and captured. Head, head washer, and shaft are the active "
            "co-moving parts, each screened in a separate sweep so the wide head "
            "is not carried through the shaft path. Those three roles plus the "
            "removed nut and nut washer are excluded from this phase. All other "
            "candidate hardware, receiver wood, frame hardware, fixed panel axes, "
            "service proxies, panels, and protected shapes remain."
        ),
    )
    return {
        "status": "screened_continuous_translation_enclosure",
        "method": (
            "continuous linear translation; per-role head and head-washer "
            "oriented-box enclosures plus exact coaxial cylindrical shaft sweep "
            "when primitive reconstruction validates"
        ),
        "moving_roles": ["head", "head_washer", "shaft"],
        "shaft_sweep_method": shaft_sweep_method,
        "head_and_washer_sweep_method": "separate conservative oriented-box translation enclosures",
        "preconditions": [
            "nut and nut_washer are fully unthreaded",
            "nut and nut_washer are captured and absent from the moving phase",
            "support and member restraint remain adequate throughout withdrawal",
        ],
        "axis_direction_toward_head_xyz": [
            round(value, 9) for value in outward.toTuple()
        ],
        "derived_translation_distance_mm": round(travel_mm, 6),
        "distance_basis": (
            "projection of the archived receiver solids and modeled shaft envelope; "
            "no extra physical clearance allowance is asserted"
        ),
        "terminal_clearance_margin_mm": 0.0,
        "terminal_state": "shaft envelope ends flush with the farthest receiver projection",
        "sweep_collision_screen": collision,
        "nut_or_nut_washer_removal_path_screened": False,
        "loose_part_capture_path_screened": False,
        "support_transfer_established": False,
        "reverse_installation_path_screened": False,
        "physical_removal_established": False,
        "broad_enclosure_is_exact_bolt_sweep": False,
    }


def _family_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    counts: dict[str, dict[str, int]] = {}
    for row in rows:
        family = row["family"]
        entry = counts.setdefault(
            family, {"axes": 0, "counterhold_screened": 0, "withdrawal_screened": 0}
        )
        entry["axes"] += 1
        entry["counterhold_screened"] += (
            row["operations"]["installed_counterhold"]["status"] != "scope_not_modeled"
        )
        entry["withdrawal_screened"] += (
            row["operations"]["shaft_withdrawal"]["status"] != "scope_not_modeled"
        )
    return {family: counts[family] for family in sorted(counts)}


def build_wj24_tool_operation_report(
    geometry: Any,
    *,
    contract: WJ24ArchiveContract | None = None,
) -> dict[str, Any]:
    """Build nominal counterhold and withdrawal records for all archived axes.

    ``geometry`` must be the parent-materialized WJ24 composition. This
    function does not call a materializer or any native solve.
    """
    contract = contract or load_archived_wj24_contract()
    _validate_runtime_geometry(geometry, contract)
    _raw_receivers, finished_wood = wj12_diagnostic._composed_wood(geometry)
    obstacles = _scene_obstacles(geometry)
    tool_candidate = WJ04_TRIAL.fasteners.tools[0]
    rows = []
    for axis_id in sorted(contract.axes):
        axis = contract.axes[axis_id]
        roles = geometry.candidate_installed_hardware[axis_id]
        if axis.role_ids == BACKER_ROLES:
            unsupported = {
                "status": "scope_not_modeled",
                "reason": (
                    "WJ05 backer head-side below-access route depends on an "
                    "open/lifted support state that this composed geometry does not represent"
                ),
                "required_state": "frame open or lifted with below access and support transfer defined",
                "local_tool_clearance_transferred": False,
            }
            rows.append(
                {
                    "axis_id": axis.axis_id,
                    "family": axis.family,
                    "family_trial_id": axis.trial_id,
                    "station_id": axis.station_id,
                    "receiver_ids": list(axis.receiver_ids),
                    "modeled_role_ids": sorted(axis.role_ids),
                    "hardware_selection_status": "provisional geometry envelope; no SKU or delivered part selected",
                    "operations": {
                        "installed_counterhold": dict(unsupported),
                        "shaft_withdrawal": dict(unsupported),
                    },
                }
            )
            continue

        counterhold = _counterhold_screen(axis_id, roles, obstacles, tool_candidate)
        withdrawal = _shaft_withdrawal_screen(axis, roles, obstacles, finished_wood)
        rows.append(
            {
                "axis_id": axis.axis_id,
                "family": axis.family,
                "family_trial_id": axis.trial_id,
                "station_id": axis.station_id,
                "receiver_ids": list(axis.receiver_ids),
                "modeled_role_ids": sorted(axis.role_ids),
                "hardware_selection_status": "provisional geometry envelope; no SKU or delivered part selected",
                "operations": {
                    "installed_counterhold": counterhold,
                    "shaft_withdrawal": withdrawal,
                },
            }
        )

    screened_counterholds = sum(
        row["operations"]["installed_counterhold"]["status"] != "scope_not_modeled"
        for row in rows
    )
    screened_withdrawals = sum(
        row["operations"]["shaft_withdrawal"]["status"] != "scope_not_modeled"
        for row in rows
    )
    return {
        "schema": SCHEMA,
        "status": "bounded_full_layout_nominal_envelope_diagnostic",
        "layout_id": contract.layout_id,
        "trial_id": contract.trial_id,
        "source_inventory_sha256": contract.source_inventory_sha256,
        "input_artifact_sha256": {
            "composition": contract.composition_sha256,
            "diagnostic": contract.diagnostic_sha256,
            "hardware_inventory": contract.inventory_sha256,
        },
        "profile_source": {
            "trial_id": WJ04_TRIAL.trial_id,
            "manufacturer": tool_candidate.manufacturer,
            "candidate_id": tool_candidate.candidate_id,
            "description": tool_candidate.description,
            "wrench_size_in": tool_candidate.wrench_size_in,
            "head_width_mm": tool_candidate.head_width_mm,
            "head_thickness_mm": tool_candidate.head_thickness_mm,
            "overall_length_mm": tool_candidate.overall_length_mm,
            "heading_samples_degrees": list(tool_candidate.head_offsets_degrees),
            "source_urls": list(tool_candidate.source_urls),
            "published_dimension_tolerances": tool_candidate.published_dimension_tolerances,
            "handle_sweep_verified": tool_candidate.handle_sweep_verified,
            "profile_status": tool_candidate.status,
            "profile_is_WJ24_SKU_or_fit_selection": False,
            "jaw_fit_contact_torque_and_delivered_profile_established": False,
            "heading_samples_are_actual_catalog_jaw_orientation": False,
        },
        "counts": {
            "candidate_axes": len(rows),
            "installed_counterhold_axes_screened": screened_counterholds,
            "shaft_withdrawal_axes_screened": screened_withdrawals,
            "scope_not_modeled_axes_per_operation": len(rows) - screened_counterholds,
            "candidate_axes_with_forward_and_reverse_operation_complete": 0,
        },
        "family_counts": _family_summary(rows),
        "axes": rows,
        "method_contract": {
            "installed_counterhold": (
                "Two fixed seated wrench external-envelope poses at each end, "
                "using the two WJ04 synthetic planar heading samples (not the "
                "catalog jaw-to-handle orientation); paired pose overlap is "
                "checked. No approach, turn stroke, reindex, "
                "installation, or jaw engagement is modeled."
            ),
            "shaft_withdrawal": (
                "After an explicit captured-nut/captured-nut-washer prerequisite, "
                "head, head washer, and shaft translate together toward the head "
                "side. A continuous linear translation is enclosed by the "
                "existing conservative oriented bounding sweep."
            ),
            "retained_scene": (
                "Finished source and candidate wood, three panel replacements, "
                "all 66 fixed panel axes, all 12 frame-bolt arrangements and "
                "their tool/withdrawal proxies, all 104 candidate stacks, and "
                "all nonduplicated protected T-nut, hold, light, and wire maps."
            ),
        },
        "claim_boundary": {
            "prior_partial_scene_clearance_transferred": False,
            "complete_installation_or_removal_route_established": False,
            "continuous_tool_motion_established": False,
            "physical_tool_fit_or_access_established": False,
            "support_or_capture_established": False,
            "hardware_SKUs_selected": False,
            "physical_dimensions_inferred_from_CAD_envelopes": False,
            "capacity_or_joint_acceptance_established": False,
            "fabrication_or_drilling_released": False,
        },
    }
