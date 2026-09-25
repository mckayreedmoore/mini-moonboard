"""Prepare a distinct current-patch C3D10 mesh from authenticated STEP inputs.

The input is the current-patch exporter bundle, not the historical WJ04 or
WJ24 mesh input schema. This is geometry and mesh preparation only: it assigns
no material, contact, tie, load, restraint, strength result, or solver card.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import platform
import re
import tempfile
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from fea import wood_joint_patch_mesh as wood_mesh
from fea.stitch_joint_mesh import validate_ownership

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = "wood_joint_current_patch_mesh/v1"
BUNDLE_SCHEMA = "wood_joint_current_patch_inputs/v1"
BUNDLE_STATUS = "current_geometry_patch_inputs_only"
STATUS_VERIFIED = "VERIFIED_C3D10_CURRENT_PATCH_MESH_ONLY_NO_SOLVER"
EXPORTER_SOURCE_PATH = "scripts/wood_joint_current_patch_inputs.py"
SOURCE_INVENTORY_PATH = "docs/wood-joints-mvp/source-inventory.json"
SOURCE_BASELINE_COMMIT = "df7f5eca86ae831b35a8bcf9e6dcd7ae8af852bb"
SOURCE_INVENTORY_SHA256 = "07af4c3eb642cf3887595fe4415eb65404cdcf74d66c5c7bb182847ef21c2d78"
FROZEN_EXPORTER_SOURCE_SHA256 = "aad61df4d6a7f39dd7d14eac48193f1d94545887f56e50d8f86e6ec4f5dec0bc"
CURRENT_REVISION_ID = "led-clearance-2x6-runner-seated-blocks-v1"
CURRENT_IMPLEMENTATION_REVISION = "b1e8707d"
REVISION_REPORT_PATH = (
    "docs/wood-joints-mvp/hypotheses/"
    "led-clearance-2x6-runner-blocks-2026-09-24/revision.json"
)
VERIFICATION_REPORT_PATH = (
    "docs/wood-joints-mvp/hypotheses/"
    "led-clearance-2x6-runner-blocks-2026-09-24/verification.json"
)
SCENE_SNAPSHOT_PATH = (
    "docs/wood-joints-mvp/hypotheses/"
    "led-clearance-2x6-runner-blocks-2026-09-24/scene.json.snapshot"
)
REVISION_REPORT_SHA256 = "148f97623573558cd6a6c53f8a5399f2b30549d6aa1ed13c326dfe1bc3e9d695"
SCENE_SHA256 = "74845b2e97165488d020d6a26202d2372f09f299cb47c9f28a3ba4642fe628bf"
VERIFIED_CURRENT_SOURCE_HASHES = {
    "scripts/wood_joint_wj24_led_clearance.py": "4c33379985baaf4dd19b0909abbd1a9f361fd8fe50c5d91260167c74425f35a9",
    "scripts/wood_joint_wj24_2x6_outer_blocks.py": "fb7e49e354f1ffe718c86caeeb588c129088a604498ef465028320defd13540e",
    "scripts/export_wood_joint_design_review_scene.py": "02baedfa61f281854da947cd5787b83d10b1c91161aa05c252ef3960c9cf3537",
}

WOOD_BODY_IDS = (
    "bottom_center_right_cleat",
    "base_rail_bottom_right",
    "base_principal_center_right",
)
WOOD_BODY_ROLES = {
    "bottom_center_right_cleat": "finished_candidate_part",
    "base_rail_bottom_right": "finished_source_host",
    "base_principal_center_right": "finished_source_host",
}
AXIS_RECEIVERS = {
    "bottom_center/clip_horizontal_bottom_right_1/rail_1": (
        "bottom_center_right_cleat",
        "base_rail_bottom_right",
    ),
    "bottom_center/clip_horizontal_bottom_right_1/rail_2": (
        "bottom_center_right_cleat",
        "base_rail_bottom_right",
    ),
    "bottom_center/clip_horizontal_bottom_right_1/principal_1": (
        "bottom_center_right_cleat",
        "base_principal_center_right",
    ),
    "bottom_center/clip_horizontal_bottom_right_1/principal_2": (
        "bottom_center_right_cleat",
        "base_principal_center_right",
    ),
}
HARDWARE_ROLES = ("shaft", "head", "head_washer", "nut_washer", "nut")
PHYSICAL_ROLES = ("bolt", "head_washer", "nut_washer", "nut")
EXPECTED_INTERFACE_IDS = (
    "bottom_center_right_cleat_to_base_rail_bottom_right",
    "bottom_center_right_cleat_to_base_principal_center_right",
    "base_rail_bottom_right_to_base_principal_center_right",
)
EXPECTED_INTERFACE_MEMBERS = {
    EXPECTED_INTERFACE_IDS[0]: (
        "bottom_center_right_cleat",
        "base_rail_bottom_right",
    ),
    EXPECTED_INTERFACE_IDS[1]: (
        "bottom_center_right_cleat",
        "base_principal_center_right",
    ),
    EXPECTED_INTERFACE_IDS[2]: (
        "base_rail_bottom_right",
        "base_principal_center_right",
    ),
}
EXPECTED_INTERFACE_AXIS_IDS = {
    EXPECTED_INTERFACE_IDS[0]: sorted(
        axis_id
        for axis_id, receivers in AXIS_RECEIVERS.items()
        if receivers[1] == "base_rail_bottom_right"
    ),
    EXPECTED_INTERFACE_IDS[1]: sorted(
        axis_id
        for axis_id, receivers in AXIS_RECEIVERS.items()
        if receivers[1] == "base_principal_center_right"
    ),
    EXPECTED_INTERFACE_IDS[2]: [],
}
INTERFACE_PLANE_TOLERANCE_MM = 1e-5
INTERFACE_OPPOSED_NORMAL_TOLERANCE = 1e-7

LIMITS = (
    "Current-patch independent C3D10 mesh preparation only; no material, "
    "contact law, interface tie, load, restraint, native solve, strength result, "
    "or release claim."
)
WORKER_SOURCE_PATHS = (
    "fea/wood_joint_current_patch_mesh.py",
    "fea/wood_joint_patch_mesh.py",
    "fea/stitch_joint_mesh.py",
    "fea/floor_contact.py",
    EXPORTER_SOURCE_PATH,
)
CAD_IMPORT_RELATIVE_VOLUME_TOLERANCE = 1e-7
CAD_IMPORT_POSITION_TOLERANCE_MM = 1e-3
RECEIVER_INTERVAL_TOLERANCE_MM = 0.02
UNION_VOLUME_ABSOLUTE_TOLERANCE_MM3 = 1e-5
UNION_VOLUME_RELATIVE_TOLERANCE = 1e-8
SYMMETRIC_DIFFERENCE_ABSOLUTE_TOLERANCE_MM3 = 1e-3
SYMMETRIC_DIFFERENCE_RELATIVE_TOLERANCE = 1e-9


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: str | Path) -> str:
    return sha256_bytes(Path(path).read_bytes())


def write_json(path: str | Path, value: Any) -> None:
    Path(path).write_text(
        json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )


def _is_sha256(value: Any) -> bool:
    return (
        isinstance(value, str)
        and len(value) == 64
        and all(character in "0123456789abcdef" for character in value)
    )


def _finite_number(value: Any, context: str) -> float:
    if isinstance(value, bool):
        raise TypeError(f"{context}: expected a finite number")
    try:
        number = float(value)
    except (TypeError, ValueError, OverflowError) as error:
        raise ValueError(f"{context}: expected a finite number") from error
    if not math.isfinite(number):
        raise ValueError(f"{context}: expected a finite number")
    return number


def _finite_vector(value: Any, length: int, context: str) -> tuple[float, ...]:
    try:
        result = tuple(float(component) for component in value)
    except (TypeError, ValueError, OverflowError) as error:
        raise ValueError(f"{context}: expected {length} finite values") from error
    if len(result) != length or not all(math.isfinite(item) for item in result):
        raise ValueError(f"{context}: expected {length} finite values")
    return result


def _finite_positive(value: Any, context: str) -> float:
    number = _finite_number(value, context)
    if number <= 0:
        raise ValueError(f"{context}: expected a positive value")
    return number


def validate_mesh_configuration(
    global_max_size_mm: float,
    axis_local_size_mm: float,
    axis_refinement_band_mm: float,
) -> dict[str, float]:
    return wood_mesh.validate_mesh_configuration(
        global_max_size_mm, axis_local_size_mm, axis_refinement_band_mm
    )


def _validate_solid_metadata(value: Any, context: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise TypeError(f"{context}: solid metadata must be an object")
    if value.get("solid_count") != 1:
        raise ValueError(f"{context}: expected one source solid")
    _finite_positive(value.get("volume_mm3"), f"{context} volume")
    _finite_vector(value.get("centroid_global_xyz_mm"), 3, f"{context} centroid")
    bounds = _finite_vector(value.get("bounds_xyz_mm"), 6, f"{context} bounds")
    if any(bounds[index] > bounds[index + 1] for index in (0, 2, 4)):
        raise ValueError(f"{context}: inverted bounds")
    if not _is_sha256(value.get("cad_shape_sha256")):
        raise ValueError(f"{context}: invalid CAD shape fingerprint")
    return value


def _solid_signatures_match(
    first: Mapping[str, Any],
    second: Mapping[str, Any],
    context: str,
    *,
    require_shape_hash: bool,
) -> None:
    _validate_solid_metadata(dict(first), f"{context} first signature")
    _validate_solid_metadata(dict(second), f"{context} second signature")
    if require_shape_hash and first["cad_shape_sha256"] != second["cad_shape_sha256"]:
        raise ValueError(f"{context}: CAD shape fingerprints differ")
    volume_a = float(first["volume_mm3"])
    volume_b = float(second["volume_mm3"])
    allowed_volume = 1e-5 + max(volume_a, volume_b) * 1e-7
    if abs(volume_a - volume_b) > allowed_volume:
        raise ValueError(f"{context}: solid volumes differ")
    for field, length in (
        ("centroid_global_xyz_mm", 3),
        ("bounds_xyz_mm", 6),
    ):
        values_a = _finite_vector(first[field], length, f"{context} first {field}")
        values_b = _finite_vector(second[field], length, f"{context} second {field}")
        if any(abs(a - b) > 1e-4 for a, b in zip(values_a, values_b, strict=True)):
            raise ValueError(f"{context}: solid {field} differ")


def _identity_checks_pass(artifact: Mapping[str, Any], context: str) -> None:
    checks = artifact.get("identity_checks")
    if not isinstance(checks, dict) or any(
        checks.get(name) is not True
        for name in ("solid_count", "volume", "centroid", "bounds")
    ):
        raise ValueError(f"{context}: STEP round-trip identity checks are incomplete")
    difference = checks.get("symmetric_difference")
    if not isinstance(difference, dict) or difference.get("passed") is not True:
        raise ValueError(f"{context}: STEP symmetric-difference check did not pass")
    source_only = _finite_number(
        difference.get("source_only_volume_mm3"), f"{context} source-only volume"
    )
    step_only = _finite_number(
        difference.get("step_only_volume_mm3"), f"{context} STEP-only volume"
    )
    observed = _finite_number(
        difference.get("symmetric_difference_volume_mm3"),
        f"{context} symmetric-difference volume",
    )
    allowed = _finite_positive(
        difference.get("allowed_volume_difference_mm3"),
        f"{context} allowed symmetric difference",
    )
    if min(source_only, step_only, observed) < 0 or observed > allowed:
        raise ValueError(f"{context}: STEP symmetric difference exceeds its recorded tolerance")
    if not math.isclose(
        observed, source_only + step_only, rel_tol=1e-8, abs_tol=1e-10
    ):
        raise ValueError(f"{context}: STEP symmetric-difference components disagree")


def _safe_relative_path(value: Any, context: str) -> str:
    if not isinstance(value, str) or not value or "\\" in value:
        raise ValueError(f"{context}: expected a normalized relative path")
    path = Path(value)
    if path.is_absolute() or any(part in {"", ".", ".."} for part in path.parts):
        raise ValueError(f"{context}: unsafe relative path")
    return path.as_posix()


def _validate_live_review_pins(inventory: dict[str, Any]) -> None:
    """Bind the export to the selected current review and live source files."""
    geometry = inventory.get("geometry_binding")
    candidate = inventory.get("candidate")
    if not isinstance(geometry, dict) or not isinstance(candidate, dict):
        raise TypeError("current patch candidate or geometry binding is missing")
    if (
        candidate.get("revision_id") != CURRENT_REVISION_ID
        or candidate.get("implementation_revision") != CURRENT_IMPLEMENTATION_REVISION
        or candidate.get("source_inventory_baseline_commit") != SOURCE_BASELINE_COMMIT
        or candidate.get("source_inventory_sha256") != SOURCE_INVENTORY_SHA256
    ):
        raise ValueError("current patch is not bound to the selected candidate revision")
    if (
        geometry.get("layout_id") != CURRENT_REVISION_ID
        or geometry.get("trial_id") != CURRENT_REVISION_ID
        or geometry.get("status") != "unaccepted_viewer_geometry_revision"
        or geometry.get("source_inventory_sha256") != SOURCE_INVENTORY_SHA256
    ):
        raise ValueError("current patch geometry binding differs from the selected revision")

    try:
        source_inventory_bytes = (ROOT / SOURCE_INVENTORY_PATH).read_bytes()
    except OSError as error:
        raise ValueError("canonical current source inventory is unavailable") from error
    if sha256_bytes(source_inventory_bytes) != SOURCE_INVENTORY_SHA256:
        raise ValueError("canonical current source inventory differs from the selected baseline pin")
    source_inventory = json.loads(source_inventory_bytes)
    if source_inventory.get("source_commit") != SOURCE_BASELINE_COMMIT:
        raise ValueError("canonical source inventory commit differs from the selected baseline")

    try:
        revision_bytes = (ROOT / REVISION_REPORT_PATH).read_bytes()
        verification_bytes = (ROOT / VERIFICATION_REPORT_PATH).read_bytes()
        scene_bytes = (ROOT / SCENE_SNAPSHOT_PATH).read_bytes()
        revision = json.loads(revision_bytes)
        verification = json.loads(verification_bytes)
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError("selected current review archive is incomplete") from error
    if sha256_bytes(revision_bytes) != REVISION_REPORT_SHA256:
        raise ValueError("selected current revision report hash differs from its pin")
    if sha256_bytes(scene_bytes) != SCENE_SHA256:
        raise ValueError("selected current scene snapshot hash differs from its pin")
    if revision.get("revision_id") != CURRENT_REVISION_ID:
        raise ValueError("archived current review names another revision")
    if (
        verification.get("revision_report_sha256") != REVISION_REPORT_SHA256
        or verification.get("scene_sha256") != SCENE_SHA256
        or verification.get("source_files_sha256") != VERIFIED_CURRENT_SOURCE_HASHES
    ):
        raise ValueError("current verification report does not preserve the pinned review inputs")
    for path, expected in VERIFIED_CURRENT_SOURCE_HASHES.items():
        try:
            observed = sha256_file(ROOT / path)
        except OSError as error:
            raise ValueError(f"pinned current source is unavailable: {path}") from error
        if observed != expected:
            raise ValueError(f"pinned current source changed: {path}")

    pins = candidate.get("current_review_pins")
    if not isinstance(pins, dict):
        raise TypeError("current patch has no current-review pin map")
    expected_pin_values = {
        "revision_report": REVISION_REPORT_PATH,
        "revision_report_sha256": REVISION_REPORT_SHA256,
        "verification_report": VERIFICATION_REPORT_PATH,
        "verification_report_sha256": sha256_bytes(verification_bytes),
        "scene_snapshot": SCENE_SNAPSHOT_PATH,
        "scene_sha256": SCENE_SHA256,
        "source_files_sha256": VERIFIED_CURRENT_SOURCE_HASHES,
        "report_claim_boundary": (
            "current viewer geometry review only; no joint evaluation or acceptance"
        ),
    }
    for key, expected in expected_pin_values.items():
        if pins.get(key) != expected:
            raise ValueError(f"current review pin {key} differs from the live review")
    exporter_sha = pins.get("input_adapter_source_sha256")
    exporter_path = ROOT / EXPORTER_SOURCE_PATH
    if (
        exporter_sha != FROZEN_EXPORTER_SOURCE_SHA256
        or not _is_sha256(exporter_sha)
        or not exporter_path.is_file()
    ):
        raise ValueError("current export adapter source pin is missing")
    if sha256_file(exporter_path) != exporter_sha:
        raise ValueError("current export adapter differs from its bundle source pin")

    input_sources = geometry.get("source_inputs_sha256")
    if not isinstance(input_sources, dict) or not input_sources:
        raise ValueError("current geometry has no source-input fingerprint map")
    for relative, digest in input_sources.items():
        safe_path = _safe_relative_path(relative, "current geometry source")
        if not _is_sha256(digest):
            raise ValueError(f"{safe_path}: invalid source-input fingerprint")
        path = ROOT / safe_path
        if not path.is_file() or sha256_file(path) != digest:
            raise ValueError(f"{safe_path}: live geometry source differs from export pin")


def _validate_union_identity(
    metal_row: Mapping[str, Any],
    role_rows: Mapping[tuple[str, str], Mapping[str, Any]],
    axis_id: str,
) -> None:
    solid = metal_row.get("solid")
    union = metal_row.get("union_identity")
    if not isinstance(solid, dict) or not isinstance(union, dict):
        raise TypeError(f"{axis_id}: derived bolt lacks solid or union identity")
    nested = solid.get("physical_bolt_union")
    if not isinstance(nested, dict) or union != nested:
        raise ValueError(f"{axis_id}: bolt union identity is not the solid's recorded proof")
    if (
        union.get("valid") is not True
        or union.get("solid_count") != 1
        or union.get("source_role_ids") != [f"{axis_id}/head", f"{axis_id}/shaft"]
        or union.get("symmetric_difference_passed") is not True
    ):
        raise ValueError(f"{axis_id}: derived bolt is not the one-solid head/shaft union")
    expected_hashes = {
        role: role_rows[(axis_id, role)]["cad_shape"]["cad_shape_sha256"]
        for role in ("head", "shaft")
    }
    if union.get("source_role_shape_sha256") != expected_hashes:
        raise ValueError(f"{axis_id}: derived bolt is not bound to the exact source head and shaft")
    overlap = _finite_number(
        union.get("head_shaft_overlap_volume_mm3"), f"{axis_id} head/shaft overlap"
    )
    expected_volume = _finite_positive(
        union.get("expected_volume_by_inclusion_exclusion_mm3"),
        f"{axis_id} expected union volume",
    )
    observed_volume = _finite_positive(
        union.get("observed_fused_volume_mm3"), f"{axis_id} observed union volume"
    )
    difference = _finite_number(
        union.get("inclusion_exclusion_volume_difference_mm3"),
        f"{axis_id} inclusion-exclusion error",
    )
    symmetric = _finite_number(
        union.get("symmetric_difference_volume_mm3"),
        f"{axis_id} union symmetric difference",
    )
    allowed = _finite_positive(
        union.get("allowed_volume_difference_mm3"),
        f"{axis_id} union volume tolerance",
    )
    if min(overlap, difference, symmetric) < 0:
        raise ValueError(f"{axis_id}: bolt union volume evidence is negative")
    if difference > allowed or symmetric > allowed:
        raise ValueError(f"{axis_id}: bolt union volume evidence exceeds recorded tolerance")
    if not math.isclose(
        expected_volume, observed_volume, rel_tol=0.0, abs_tol=allowed
    ):
        raise ValueError(f"{axis_id}: bolt union inclusion-exclusion identity does not close")
    expected_allowed = UNION_VOLUME_ABSOLUTE_TOLERANCE_MM3 + (
        UNION_VOLUME_RELATIVE_TOLERANCE * max(expected_volume, observed_volume)
    )
    if not math.isclose(allowed, expected_allowed, rel_tol=1e-7, abs_tol=1e-10):
        raise ValueError(f"{axis_id}: bolt union tolerance formula changed")
    _validate_solid_metadata(solid, f"{axis_id} physical bolt")


def _validate_inventory_contract(inventory: dict[str, Any]) -> None:
    if inventory.get("schema") != BUNDLE_SCHEMA or inventory.get("status") != BUNDLE_STATUS:
        raise ValueError("input schema or geometry-only status is not the current-patch contract")
    _validate_live_review_pins(inventory)
    scope = inventory.get("scope")
    if not isinstance(scope, dict):
        raise TypeError("current patch scope is missing")
    expected_scope = {
        "finished_wood_bodies": 3,
        "physical_bolts": 4,
        "modeled_hardware_cad_roles": 20,
        "wood_interfaces": 3,
        "step_artifacts": 27,
        "derived_physical_bolt_unions": 4,
        "physical_metal_bodies": 16,
        "full_finished_members_exported": True,
        "arbitrary_member_cuts": False,
        "meshed": False,
        "native_solve_run": False,
        "contact_law_assigned": False,
        "boundary_method": "pending",
        "strength_or_joint_acceptance_claim": False,
    }
    if any(scope.get(key) != value for key, value in expected_scope.items()):
        raise ValueError("current patch scope or claim boundary changed")
    geometry = inventory["geometry_binding"]
    candidate = inventory["candidate"]
    if (
        candidate.get("revision_id") != geometry.get("layout_id")
        or candidate.get("revision_id") != geometry.get("trial_id")
        or candidate.get("source_inventory_sha256") != geometry.get("source_inventory_sha256")
    ):
        raise ValueError("candidate and geometry binding identities disagree")

    wood_rows = inventory.get("wood_bodies")
    if not isinstance(wood_rows, list) or tuple(
        row.get("part_id") for row in wood_rows if isinstance(row, dict)
    ) != WOOD_BODY_IDS:
        raise ValueError("current patch must contain the exact ordered three finished wood bodies")
    if len(wood_rows) != len(WOOD_BODY_IDS):
        raise ValueError("current patch wood bodies contain malformed or duplicate records")
    for row in wood_rows:
        part_id = row["part_id"]
        if (
            row.get("geometry_role") != WOOD_BODY_ROLES[part_id]
            or row.get("full_finished_member_exported") is not True
            or row.get("arbitrary_patch_cut_applied") is not False
            or row.get("step_artifact_key") != f"wood/{part_id}.step"
        ):
            raise ValueError(f"{part_id}: finished source-member identity changed")
        _validate_solid_metadata(row.get("finished_geometry"), f"{part_id} finished geometry")

    axes = inventory.get("physical_bolts")
    if not isinstance(axes, list) or tuple(
        row.get("physical_bolt_id") for row in axes if isinstance(row, dict)
    ) != tuple(AXIS_RECEIVERS):
        raise ValueError("current patch must contain the four ordered current physical axes")
    if len(axes) != len(AXIS_RECEIVERS):
        raise ValueError("current patch physical axes contain malformed or duplicate records")
    role_rows: dict[tuple[str, str], Mapping[str, Any]] = {}
    for row in axes:
        axis_id = row["physical_bolt_id"]
        expected_receivers = AXIS_RECEIVERS[axis_id]
        if (
            row.get("physical_bolt_count") != 1
            or row.get("physical_bolt_roles") != ["head", "shaft"]
            or row.get("head_and_shaft_are_one_physical_bolt") is not True
            or row.get("receivers_head_to_nut") != list(expected_receivers)
            or row.get("cad_role_count") != len(HARDWARE_ROLES)
        ):
            raise ValueError(f"{axis_id}: physical identity, role count, or receiver order changed")
        origin = _finite_vector(
            row.get("axis_origin_global_xyz_mm"), 3, f"{axis_id} underhead origin"
        )
        direction = _finite_vector(
            row.get("axis_direction_head_to_nut_global_xyz"), 3, f"{axis_id} axis direction"
        )
        if not math.isclose(math.sqrt(math.fsum(v * v for v in direction)), 1.0, abs_tol=1e-8):
            raise ValueError(f"{axis_id}: physical axis direction is not unit length")
        _ = origin
        receiver_intervals = row.get("raw_receiver_projected_intervals")
        if not isinstance(receiver_intervals, list) or len(receiver_intervals) != 2:
            raise ValueError(f"{axis_id}: expected two ordered projected receiver intervals")
        interval_envelopes = []
        for order, (interval, receiver_id) in enumerate(
            zip(receiver_intervals, expected_receivers, strict=True), start=1
        ):
            intervals = interval.get("projected_intervals_from_underhead_datum_mm")
            if not isinstance(intervals, list) or len(intervals) != 1:
                raise ValueError(
                    f"{axis_id}/{receiver_id}: current receiver projection must be one interval"
                )
            values = _finite_vector(
                intervals[0], 2, f"{axis_id}/{receiver_id} projected interval"
            )
            projected = _finite_positive(
                interval.get("projected_material_length_mm"),
                f"{axis_id}/{receiver_id} projected material length",
            )
            gaps = interval.get("projection_gaps_mm")
            if (
                interval.get("member_id") != receiver_id
                or interval.get("receiver_order_head_to_nut") != order
                or interval.get("current_shaft_covers_raw_receiver") is not True
                or gaps != []
                or values[1] <= values[0]
                or abs((values[1] - values[0]) - projected) > 1e-6
            ):
                raise ValueError(f"{axis_id}/{receiver_id}: projected receiver evidence changed")
            probe_difference = _finite_number(
                interval.get("long_probe_minus_current_shaft_volume_mm3"),
                f"{axis_id}/{receiver_id} shaft coverage difference",
            )
            if probe_difference < 0 or probe_difference > 1e-6:
                raise ValueError(f"{axis_id}/{receiver_id}: shaft coverage evidence changed")
            interval_envelopes.append(values)
        if abs(interval_envelopes[1][0] - interval_envelopes[0][1]) > (
            RECEIVER_INTERVAL_TOLERANCE_MM
        ):
            raise ValueError(f"{axis_id}: ordered receiver intervals are not contiguous")

        role_list = row.get("physical_hardware_roles")
        if not isinstance(role_list, list) or tuple(
            item.get("role") for item in role_list if isinstance(item, dict)
        ) != HARDWARE_ROLES:
            raise ValueError(f"{axis_id}: expected the five ordered source CAD roles")
        if len(role_list) != len(HARDWARE_ROLES):
            raise ValueError(f"{axis_id}: source CAD roles contain malformed or duplicate records")
        for role_row in role_list:
            role = role_row["role"]
            if role_row.get("step_artifact_key") != f"hardware/{axis_id}/{role}.step":
                raise ValueError(f"{axis_id}/{role}: source CAD role artifact key changed")
            _validate_solid_metadata(role_row.get("cad_shape"), f"{axis_id}/{role} source role")
            role_rows[(axis_id, role)] = role_row
        expected_physical_ids = [
            f"physical_metal/{axis_id}/{role}"
            for role in PHYSICAL_ROLES
        ]
        if row.get("physical_metal_body_ids") != [
            f"physical_metal/{axis_id}/bolt",
            f"physical_metal/{axis_id}/head_washer",
            f"physical_metal/{axis_id}/nut_washer",
            f"physical_metal/{axis_id}/nut",
        ]:
            raise ValueError(f"{axis_id}: physical-metal body role mapping changed")
        if set(expected_physical_ids) != set(row["physical_metal_body_ids"]):
            raise ValueError(f"{axis_id}: physical-metal component mapping is incomplete")

    metal_rows = inventory.get("physical_metal_bodies")
    expected_metal_ids = tuple(
        f"physical_metal/{axis_id}/{role}"
        for axis_id in AXIS_RECEIVERS
        for role in PHYSICAL_ROLES
    )
    if not isinstance(metal_rows, list) or tuple(
        row.get("physical_body_id") for row in metal_rows if isinstance(row, dict)
    ) != expected_metal_ids:
        raise ValueError("current patch must contain the ordered sixteen physical metal bodies")
    if len(metal_rows) != len(expected_metal_ids):
        raise ValueError("physical-metal rows contain malformed or duplicate records")
    for row in metal_rows:
        physical_id = row["physical_body_id"]
        if not physical_id.startswith("physical_metal/"):
            raise ValueError(f"{physical_id}: malformed physical-metal ID")
        suffix = next(
            (f"/{candidate}" for candidate in PHYSICAL_ROLES if physical_id.endswith(f"/{candidate}")),
            None,
        )
        if suffix is None:
            raise ValueError(f"{physical_id}: unknown physical-metal component role")
        axis_id = physical_id[len("physical_metal/") : -len(suffix)]
        role = suffix[1:]
        if role == "bolt":
            expected_kind = "bolt_head_plus_shaft_union"
            expected_source_roles = [f"{axis_id}/head", f"{axis_id}/shaft"]
            expected_step_key = f"{physical_id}.step"
            _validate_union_identity(row, role_rows, axis_id)
        else:
            expected_kind = role
            expected_source_roles = [f"{axis_id}/{role}"]
            expected_step_key = f"hardware/{axis_id}/{role}.step"
            role_row = role_rows[(axis_id, role)]
            _solid_signatures_match(
                row.get("solid", {}),
                role_row["cad_shape"],
                f"{physical_id} source-role mapping",
                require_shape_hash=True,
            )
        if (
            row.get("axis_id") != axis_id
            or row.get("physical_kind") != expected_kind
            or row.get("source_cad_role_ids") != expected_source_roles
            or row.get("step_artifact_key") != expected_step_key
        ):
            raise ValueError(f"{physical_id}: physical-metal ownership or source roles changed")

    interfaces = inventory.get("wood_interfaces")
    if not isinstance(interfaces, list) or tuple(
        row.get("interface_id") for row in interfaces if isinstance(row, dict)
    ) != EXPECTED_INTERFACE_IDS:
        raise ValueError("current patch must contain the exact three wood interface records")
    if len(interfaces) != len(EXPECTED_INTERFACE_IDS):
        raise ValueError("current patch wood interface list is malformed")
    for interface in interfaces:
        interface_id = interface["interface_id"]
        expected_pair = EXPECTED_INTERFACE_MEMBERS[interface["interface_id"]]
        if (
            interface.get("members") != list(expected_pair)
            or interface.get("bolt_axis_ids") != EXPECTED_INTERFACE_AXIS_IDS[interface_id]
            or interface.get("contact_law_assigned") is not False
            or interface.get("active_pressure_patch_established") is not False
        ):
            raise ValueError(f"{interface_id}: interface input claim or owner mapping changed")
        if interface.get("status") != "finite_opposed_coplanar_patch_extracted":
            raise ValueError(f"{interface_id}: a finite actual wood face-pair patch is unavailable")
        pairs = interface.get("actual_face_pairs")
        if (
            not isinstance(pairs, list)
            or not pairs
            or interface.get("finite_opposed_face_pair_count") != len(pairs)
        ):
            raise ValueError(f"{interface_id}: actual finite face-pair evidence is missing")
        total_area = 0.0
        weighted_centroid = [0.0, 0.0, 0.0]
        for pair in pairs:
            if (
                pair.get("first_member") != expected_pair[0]
                or pair.get("second_member") != expected_pair[1]
            ):
                raise ValueError(f"{interface_id}: actual face-pair member ownership changed")
            area = _finite_positive(pair.get("common_area_mm2"), f"{interface_id} overlap area")
            centroid = _finite_vector(
                pair.get("common_area_centroid_global_xyz_mm"),
                3,
                f"{interface_id} overlap centroid",
            )
            normal_a = _unit(
                pair.get("plane_normal_first_member_global_xyz"),
                f"{interface_id} first face normal",
            )
            normal_b = _unit(
                pair.get("plane_normal_second_member_global_xyz"),
                f"{interface_id} second face normal",
            )
            if _dot(normal_a, normal_b) > -1.0 + INTERFACE_OPPOSED_NORMAL_TOLERANCE:
                raise ValueError(f"{interface_id}: source faces are not opposed")
            gap = _finite_number(
                pair.get("measured_plane_gap_mm"), f"{interface_id} source face gap"
            )
            if gap < 0 or gap > INTERFACE_PLANE_TOLERANCE_MM:
                raise ValueError(f"{interface_id}: source face planes are not coincident")
            for side in ("first_face", "second_face"):
                face = pair.get(side)
                if not isinstance(face, dict):
                    raise TypeError(f"{interface_id}: source face descriptor is missing")
                _finite_positive(face.get("area_mm2"), f"{interface_id} {side} area")
                _finite_vector(
                    face.get("centroid_global_xyz_mm"),
                    3,
                    f"{interface_id} {side} centroid",
                )
                _finite_vector(face.get("normal_global_xyz"), 3, f"{interface_id} {side} normal")
                bounds = _finite_vector(
                    face.get("bounds_xyz_mm"), 6, f"{interface_id} {side} bounds"
                )
                if any(bounds[index] > bounds[index + 1] for index in (0, 2, 4)):
                    raise ValueError(f"{interface_id}: source face bounds are inverted")
                if not _is_sha256(face.get("cad_face_sha256")):
                    raise ValueError(f"{interface_id}: source face fingerprint is missing")
            total_area += area
            for index in range(3):
                weighted_centroid[index] += area * centroid[index]
        total_area = _finite_positive(
            interface.get("finite_overlap_area_mm2"), f"{interface_id} total overlap area"
        )
        pair_area = math.fsum(
            float(pair["common_area_mm2"]) for pair in pairs
        )
        if not math.isclose(total_area, pair_area, rel_tol=1e-9, abs_tol=1e-6):
            raise ValueError(f"{interface_id}: overlap total differs from actual face pairs")
        expected_centroid = tuple(
            weighted_centroid[index] / pair_area for index in range(3)
        )
        observed_centroid = _finite_vector(
            interface.get("finite_overlap_area_centroid_global_xyz_mm"),
            3,
            f"{interface_id} total overlap centroid",
        )
        if any(
            abs(actual - expected) > 1e-6
            for actual, expected in zip(observed_centroid, expected_centroid, strict=True)
        ):
            raise ValueError(f"{interface_id}: total overlap centroid differs from face pairs")


def _artifact_key_from_step_key(step_key: str) -> str:
    if not isinstance(step_key, str) or not step_key.endswith(".step"):
        raise ValueError("STEP artifact path must end in .step")
    return step_key[:-5]


def _expected_artifact_rows(inventory: dict[str, Any]) -> dict[str, dict[str, Any]]:
    rows: dict[str, dict[str, Any]] = {}
    for wood_row in inventory["wood_bodies"]:
        rows[f"wood/{wood_row['part_id']}"] = {
            "path": f"wood/{wood_row['part_id']}.step",
            "shape": wood_row["finished_geometry"],
            "owner": wood_row,
        }
    for axis in inventory["physical_bolts"]:
        for role_row in axis["physical_hardware_roles"]:
            key = _artifact_key_from_step_key(role_row["step_artifact_key"])
            rows[key] = {
                "path": f"{key}.step",
                "shape": role_row["cad_shape"],
                "owner": role_row,
            }
    for metal in inventory["physical_metal_bodies"]:
        key = _artifact_key_from_step_key(metal["step_artifact_key"])
        rows[key] = {"path": f"{key}.step", "shape": metal["solid"], "owner": metal}
    if len(rows) != 27:
        raise ValueError("current patch artifact identities do not resolve to exactly 27 STEP files")
    return rows


def _read_json(path: Path, context: str) -> tuple[bytes, dict[str, Any]]:
    try:
        raw = path.read_bytes()
        value = json.loads(raw)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ValueError(f"{context} is unavailable or invalid JSON") from error
    if not isinstance(value, dict):
        raise TypeError(f"{context} root must be a JSON object")
    return raw, value


def _expected_bundle_file_names() -> set[str]:
    return {"inventory.json"} | {
        f"wood/{part_id}.step" for part_id in WOOD_BODY_IDS
    } | {
        f"hardware/{axis_id}/{role}.step"
        for axis_id in AXIS_RECEIVERS
        for role in HARDWARE_ROLES
    } | {
        f"physical_metal/{axis_id}/bolt.step" for axis_id in AXIS_RECEIVERS
    }


def load_current_patch_bundle(
    directory: str | Path,
    *,
    expected_inventory_sha256: str,
    expected_hash_index_sha256: str,
) -> dict[str, Any]:
    """Authenticate one immutable 27-artifact current-patch STEP bundle."""
    if not _is_sha256(expected_inventory_sha256) or not _is_sha256(
        expected_hash_index_sha256
    ):
        raise ValueError("expected current-bundle inventory and hash-index SHA256s are required")
    source = Path(directory).expanduser().resolve()
    if not source.is_dir():
        raise ValueError(f"current patch input bundle is unavailable: {source}")
    inventory_bytes, inventory = _read_json(source / "inventory.json", "current patch inventory")
    hash_index_bytes, hash_index = _read_json(source / "sha256.json", "current patch hash index")
    inventory_sha = sha256_bytes(inventory_bytes)
    hash_index_sha = sha256_bytes(hash_index_bytes)
    if inventory_sha != expected_inventory_sha256:
        raise ValueError("current patch inventory differs from the parent-frozen SHA256")
    if hash_index_sha != expected_hash_index_sha256:
        raise ValueError("current patch hash index differs from the parent-frozen SHA256")
    if not isinstance(hash_index, dict):
        raise TypeError("current patch hash index must be an object")
    expected_steps = _expected_bundle_file_names() - {"inventory.json"}
    if set(hash_index) != expected_steps | {"inventory.json"}:
        raise ValueError("current patch hash index does not list exactly 27 STEP files and inventory")
    if hash_index.get("inventory.json") != inventory_sha or any(
        not _is_sha256(value) for value in hash_index.values()
    ):
        raise ValueError("current patch hash index contains an invalid or mismatched digest")
    actual_files = {
        path.relative_to(source).as_posix()
        for path in source.rglob("*")
        if path.is_file()
    }
    if actual_files != set(hash_index) | {"sha256.json"}:
        raise ValueError("current patch bundle has missing or undeclared files")
    if any((source / relative).is_symlink() for relative in actual_files):
        raise ValueError("current patch bundle must not contain symbolic-link files")

    _validate_inventory_contract(inventory)
    artifacts = inventory.get("step_artifacts")
    expected_rows = _expected_artifact_rows(inventory)
    if not isinstance(artifacts, dict) or set(artifacts) != set(expected_rows):
        raise ValueError("current patch inventory artifact map differs from the exact 27 STEP files")
    input_file_hashes = {
        "inventory.json": inventory_sha,
        "sha256.json": hash_index_sha,
    }
    for artifact_key, expected in expected_rows.items():
        relative = expected["path"]
        digest = hash_index.get(relative)
        artifact = artifacts[artifact_key]
        target = source / relative
        if not target.is_file() or sha256_file(target) != digest:
            raise ValueError(f"{relative}: missing or changed current patch STEP artifact")
        input_file_hashes[relative] = digest
        if not isinstance(artifact, dict) or artifact.get("file_sha256") != digest:
            raise ValueError(f"{relative}: artifact report and hash index disagree")
        if artifact.get("file") != Path(relative).name:
            raise ValueError(f"{relative}: artifact file name does not match its owned path")
        source_solid = artifact.get("source_solid")
        readback_solid = artifact.get("step_readback_solid")
        _solid_signatures_match(
            source_solid,
            expected["shape"],
            f"{relative} source-to-inventory identity",
            require_shape_hash=True,
        )
        _solid_signatures_match(
            source_solid,
            readback_solid,
            f"{relative} STEP round-trip",
            require_shape_hash=False,
        )
        _identity_checks_pass(artifact, relative)
    return {
        "path": source,
        "inventory": inventory,
        "inventory_sha256": inventory_sha,
        "hash_index_sha256": hash_index_sha,
        "input_file_sha256": input_file_hashes,
        "step_artifacts": expected_rows,
    }


def _safe_mesh_id(kind: str, index: int, suffix: str) -> str:
    prefix = "W" if kind == "wood" else "M"
    result = f"{prefix}{index:02d}_{suffix.upper()}"
    if not re.fullmatch(r"[A-Z][A-Z0-9_]*", result):
        raise ValueError("internal mesh owner ID is not a safe deck identifier")
    return result


def _body_specs(bundle: dict[str, Any]) -> list[dict[str, Any]]:
    inventory = bundle["inventory"]
    specs = []
    for index, row in enumerate(inventory["wood_bodies"]):
        part_id = row["part_id"]
        key = f"wood/{part_id}"
        specs.append(
            {
                "mesh_body_id": _safe_mesh_id("wood", index, part_id),
                "owner_kind": "wood_member",
                "source_body_id": part_id,
                "physical_body_id": None,
                "axis_id": None,
                "component_role": None,
                "source_cad_role_ids": [],
                "source_step_artifact_key": key,
                "source_step_path": f"{key}.step",
                "solid_metadata": row["finished_geometry"],
                "source_row": row,
            }
        )
    for index, row in enumerate(inventory["physical_metal_bodies"]):
        axis_id = row["axis_id"]
        role = row["physical_kind"]
        key = _artifact_key_from_step_key(row["step_artifact_key"])
        safe_suffix = f"A{list(AXIS_RECEIVERS).index(axis_id):02d}_{role}"
        specs.append(
            {
                "mesh_body_id": _safe_mesh_id("metal", index, safe_suffix),
                "owner_kind": "physical_metal",
                "source_body_id": None,
                "physical_body_id": row["physical_body_id"],
                "axis_id": axis_id,
                "component_role": role,
                "source_cad_role_ids": list(row["source_cad_role_ids"]),
                "source_step_artifact_key": key,
                "source_step_path": row["step_artifact_key"],
                "solid_metadata": row["solid"],
                "source_row": row,
            }
        )
    if len(specs) != 19:
        raise ValueError("current patch mesh must own exactly three wood and sixteen metal bodies")
    return specs


def _unit(vector: Sequence[float], context: str) -> tuple[float, float, float]:
    values = _finite_vector(vector, 3, context)
    length = math.sqrt(math.fsum(value * value for value in values))
    if length <= 1e-12:
        raise ValueError(f"{context}: zero vector")
    return tuple(value / length for value in values)  # type: ignore[return-value]


def _dot(first: Sequence[float], second: Sequence[float]) -> float:
    return math.fsum(a * b for a, b in zip(first, second, strict=True))


def _cross(first: Sequence[float], second: Sequence[float]) -> tuple[float, float, float]:
    return (
        first[1] * second[2] - first[2] * second[1],
        first[2] * second[0] - first[0] * second[2],
        first[0] * second[1] - first[1] * second[0],
    )


def _surface_probe_grid(gmsh: Any, tag: int) -> dict[str, Any]:
    try:
        low_raw, high_raw = gmsh.model.getParametrizationBounds(2, tag)
        low = _finite_vector(low_raw, 2, f"CAD surface {tag} low parameter bound")
        high = _finite_vector(high_raw, 2, f"CAD surface {tag} high parameter bound")
        u_values = (low[0] + 0.17 * (high[0] - low[0]), (low[0] + high[0]) / 2,
                    low[0] + 0.83 * (high[0] - low[0]))
        v_values = (low[1] + 0.17 * (high[1] - low[1]), (low[1] + high[1]) / 2,
                    low[1] + 0.83 * (high[1] - low[1]))
        probes = []
        for u in u_values:
            for v in v_values:
                point = _finite_vector(
                    gmsh.model.getValue(2, tag, [u, v]),
                    3,
                    f"CAD surface {tag} analytic point",
                )
                normal = None
                try:
                    normal = list(
                        _unit(
                            gmsh.model.getNormal(tag, [u, v]),
                            f"CAD surface {tag} analytic parameter normal",
                        )
                    )
                except (RuntimeError, TypeError, ValueError):
                    pass
                probes.append(
                    {
                        "uv": [u, v],
                        "xyz_mm": list(point),
                        "parametric_normal_global": normal,
                    }
                )
        return {
            "status": "nine parametric samples from the imported Gmsh CAD surface",
            "parameter_bounds_uv": [list(low), list(high)],
            "normal_orientation": (
                "parametric surface normal only; orientation is not asserted outward"
            ),
            "probes": probes,
        }
    except (RuntimeError, TypeError, ValueError, IndexError) as error:
        return {
            "status": f"unavailable: {type(error).__name__}",
            "parameter_bounds_uv": None,
            "normal_orientation": "unavailable",
            "probes": [],
        }


def _fit_cylinder_from_probes(probes: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    points: list[tuple[float, float, float]] = []
    normals: list[tuple[float, float, float]] = []
    for probe in probes:
        normal = probe.get("parametric_normal_global")
        if normal is None:
            continue
        points.append(_finite_vector(probe.get("xyz_mm"), 3, "cylinder probe point"))  # type: ignore[arg-type]
        normals.append(_unit(normal, "cylinder probe normal"))
    if len(points) < 3:
        return {"status": "insufficient finite point/normal probes"}

    best_axis = None
    best_magnitude = 0.0
    for first_index in range(len(normals)):
        for second_index in range(first_index + 1, len(normals)):
            direction = _cross(normals[first_index], normals[second_index])
            magnitude = math.sqrt(math.fsum(value * value for value in direction))
            if magnitude > best_magnitude:
                best_axis = direction
                best_magnitude = magnitude
    if best_axis is None or best_magnitude < 1e-5:
        # A small angular patch can still expose its axis through equal normals.
        for first_index in range(len(normals)):
            for second_index in range(first_index + 1, len(normals)):
                if abs(_dot(normals[first_index], normals[second_index])) < 1.0 - 1e-7:
                    continue
                delta = tuple(points[second_index][k] - points[first_index][k] for k in range(3))
                magnitude = math.sqrt(math.fsum(value * value for value in delta))
                if magnitude > best_magnitude:
                    best_axis = delta
                    best_magnitude = magnitude
    if best_axis is None or best_magnitude < 1e-8:
        return {"status": "cylinder axis could not be fit from finite probes"}
    axis = _unit(best_axis, "fitted cylinder axis")

    numerator = 0.0
    denominator = 0.0
    for left in range(len(points)):
        for right in range(left + 1, len(points)):
            point_delta = tuple(points[left][k] - points[right][k] for k in range(3))
            normal_delta = tuple(normals[left][k] - normals[right][k] for k in range(3))
            p_perp = tuple(point_delta[k] - _dot(point_delta, axis) * axis[k] for k in range(3))
            n_perp = tuple(normal_delta[k] - _dot(normal_delta, axis) * axis[k] for k in range(3))
            numerator += _dot(p_perp, n_perp)
            denominator += _dot(n_perp, n_perp)
    if denominator < 1e-12:
        return {"status": "cylinder radius could not be fit from finite probes"}
    signed_radius = numerator / denominator
    radius = abs(signed_radius)
    if radius <= 1e-9:
        return {"status": "fitted cylinder radius is nonpositive"}
    corrected_axis_points = [
        tuple(points[index][k] - signed_radius * normals[index][k] for k in range(3))
        for index in range(len(points))
    ]
    axis_point = tuple(
        math.fsum(point[k] for point in corrected_axis_points) / len(corrected_axis_points)
        for k in range(3)
    )
    residuals = []
    for point, normal in zip(points, normals, strict=True):
        station = _dot(tuple(point[k] - axis_point[k] for k in range(3)), axis)
        predicted = tuple(
            axis_point[k] + station * axis[k] + signed_radius * normal[k]
            for k in range(3)
        )
        residuals.append(
            math.sqrt(math.fsum((point[k] - predicted[k]) ** 2 for k in range(3)))
        )
    return {
        "status": "least-squares analytic-cylinder fit from CAD parametric probes",
        "axis_point_global_xyz_mm": list(axis_point),
        "axis_direction_global_xyz_unoriented": list(axis),
        "radius_mm": radius,
        "signed_radius_fit_mm": signed_radius,
        "probe_fit_rms_residual_mm": math.sqrt(
            math.fsum(value * value for value in residuals) / len(residuals)
        ),
        "probe_fit_max_residual_mm": max(residuals),
        "basis": "Gmsh OCC point and parametric-normal samples; axis sign and face orientation are not physical",
    }


def _enrich_surface_geometry(gmsh: Any, body_record: dict[str, Any]) -> None:
    for surface_key, row in body_record["surface_inventory"].items():
        tag = int(surface_key)
        try:
            area = float(gmsh.model.occ.getMass(2, tag))
            centroid = tuple(
                float(value) for value in gmsh.model.occ.getCenterOfMass(2, tag)
            )
            if not math.isfinite(area) or area <= 0 or len(centroid) != 3 or not all(
                math.isfinite(value) for value in centroid
            ):
                raise ValueError("non-finite CAD surface area or centroid")
            row["cad_area_mm2"] = area
            row["cad_centroid_global_xyz_mm"] = list(centroid)
            row["cad_geometry_descriptor_basis"] = (
                "Gmsh OpenCASCADE surface area, center of mass, bounds, and analytic probes"
            )
        except (RuntimeError, TypeError, ValueError, IndexError) as error:
            row["cad_area_mm2"] = row.get("area_mm2")
            row["cad_centroid_global_xyz_mm"] = None
            row["cad_geometry_descriptor_basis"] = (
                f"CAD surface center-of-mass sample unavailable: {type(error).__name__}"
            )
        probe_record = _surface_probe_grid(gmsh, tag)
        row["analytic_surface_probes"] = probe_record
        if row.get("cad_type") == "Plane":
            probes = probe_record["probes"]
            normal = next(
                (
                    probe["parametric_normal_global"]
                    for probe in probes
                    if probe.get("parametric_normal_global") is not None
                ),
                None,
            )
            point = next((probe["xyz_mm"] for probe in probes), None)
            row["analytic_surface_parameters"] = {
                "surface_type": "Plane",
                "sample_point_global_xyz_mm": point,
                "sample_normal_global_xyz": normal,
                "normal_orientation": "parametric normal only; not asserted outward",
                "cad_centroid_global_xyz_mm": row["cad_centroid_global_xyz_mm"],
            }
        elif row.get("cad_type") == "Cylinder":
            row["analytic_surface_parameters"] = {
                "surface_type": "Cylinder",
                **_fit_cylinder_from_probes(probe_record["probes"]),
            }
        else:
            row["analytic_surface_parameters"] = {
                "surface_type": row.get("cad_type"),
                "status": "surface type and parametric samples retained; no analytic fit applied",
            }
        row["tri6_node_ids"] = sorted(set(row.get("tri6_node_ids", ())))


def _write_input_deck(
    path: Path,
    nodes: Mapping[int, tuple[float, float, float]],
    elements: Mapping[int, tuple[int, ...]],
    bodies: Mapping[str, Mapping[str, Any]],
    specs: Sequence[Mapping[str, Any]],
) -> None:
    lines = ["*HEADING", LIMITS, "*NODE"]
    lines.extend(
        f"{node}," + ",".join(repr(float(value)) for value in xyz)
        for node, xyz in sorted(nodes.items())
    )
    for spec in specs:
        mesh_id = str(spec["mesh_body_id"])
        body = bodies[mesh_id]
        lines.append(f"*ELEMENT,TYPE=C3D10,ELSET={body['element_elset_name']}")
        lines.extend(
            f"{element}," + ",".join(str(node) for node in elements[element])
            for element in body["elements"]
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _source_paths() -> dict[str, Path]:
    return {relative: ROOT / relative for relative in WORKER_SOURCE_PATHS}


def snapshot_sources(output: Path) -> dict[str, str]:
    hashes = {}
    for relative, path in _source_paths().items():
        if not path.is_file():
            raise ValueError(f"mesh preparation source is missing: {relative}")
        data = path.read_bytes()
        digest = sha256_bytes(data)
        target = output / "sources" / f"{relative}.snapshot"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
        hashes[relative] = digest
    return hashes


def verify_sources(source_hashes: Mapping[str, str]) -> None:
    for relative, path in _source_paths().items():
        if not path.is_file() or sha256_file(path) != source_hashes[relative]:
            raise ValueError(f"mesh preparation source changed during run: {relative}")


def verify_input_bundle(bundle: dict[str, Any]) -> None:
    current = load_current_patch_bundle(
        bundle["path"],
        expected_inventory_sha256=bundle["inventory_sha256"],
        expected_hash_index_sha256=bundle["hash_index_sha256"],
    )
    if current["input_file_sha256"] != bundle["input_file_sha256"]:
        raise ValueError("current-patch inventory, hash index, or STEP changed during meshing")


def _mesh_one_body(
    gmsh: Any,
    bundle_directory: Path,
    scratch_directory: Path,
    spec: dict[str, Any],
    settings: dict[str, float],
    all_nodes: dict[int, tuple[float, float, float]],
    all_elements: dict[int, tuple[int, ...]],
) -> dict[str, Any]:
    mesh_id = spec["mesh_body_id"]
    source_step = bundle_directory / spec["source_step_path"]
    staged_wood = scratch_directory / "wood"
    staged_wood.mkdir(exist_ok=True)
    staged_step = staged_wood / f"{mesh_id}.step"
    staged_step.symlink_to(source_step)
    mesh_row = {
        "part_id": mesh_id,
        "finished_geometry": spec["solid_metadata"],
    }
    result = wood_mesh._mesh_body(
        gmsh,
        scratch_directory,
        mesh_row,
        settings,
        all_nodes,
        all_elements,
    )
    _enrich_surface_geometry(gmsh, result)
    return result


def prepare_current_patch_mesh(
    bundle_directory: str | Path,
    output_directory: str | Path,
    *,
    expected_inventory_sha256: str,
    expected_hash_index_sha256: str,
    wood_global_max_size_mm: float,
    wood_axis_local_size_mm: float,
    wood_axis_refinement_band_mm: float,
    metal_global_max_size_mm: float,
    metal_axis_local_size_mm: float,
    metal_axis_refinement_band_mm: float,
) -> Path:
    """Mesh three current finished wood solids and sixteen physical metal solids."""
    wood_settings = validate_mesh_configuration(
        wood_global_max_size_mm,
        wood_axis_local_size_mm,
        wood_axis_refinement_band_mm,
    )
    metal_settings = validate_mesh_configuration(
        metal_global_max_size_mm,
        metal_axis_local_size_mm,
        metal_axis_refinement_band_mm,
    )
    source_directory = Path(bundle_directory).expanduser().resolve()
    requested_output = Path(output_directory).expanduser().absolute()
    if requested_output.exists() or requested_output.is_symlink():
        raise FileExistsError(f"mesh output directory already exists: {requested_output}")
    output = requested_output.resolve(strict=False)
    if output.exists() or output.is_symlink():
        raise FileExistsError(f"mesh output directory resolves to an existing path: {output}")
    if (
        output == source_directory
        or output.is_relative_to(source_directory)
        or source_directory.is_relative_to(output)
    ):
        raise ValueError("mesh output and current-patch input bundle must be separate")
    output.mkdir(parents=True, exist_ok=False)

    record: dict[str, Any] = {
        "schema": SCHEMA,
        "status": "PREPARING_CURRENT_PATCH_MESH_ONLY",
        "limits": LIMITS,
        "input_bundle_directory": str(source_directory),
        "configuration": {
            "wood": wood_settings,
            "physical_metal": metal_settings,
        },
        "accepted": False,
        "solved": False,
        "native_solve_run": False,
        "contact_or_interface_classification_assigned": False,
    }
    write_json(output / "mesh.json", record)
    gmsh = None
    initialized = False
    active_body_id: str | None = None
    bodies: dict[str, dict[str, Any]] = {}
    nodes: dict[int, tuple[float, float, float]] = {}
    elements: dict[int, tuple[int, ...]] = {}
    try:
        source_hashes = snapshot_sources(output)
        bundle = load_current_patch_bundle(
            source_directory,
            expected_inventory_sha256=expected_inventory_sha256,
            expected_hash_index_sha256=expected_hash_index_sha256,
        )
        inventory = bundle["inventory"]
        specs = _body_specs(bundle)
        record.update(
            {
                "input_bundle_schema": BUNDLE_SCHEMA,
                "input_bundle_status": BUNDLE_STATUS,
                "input_bundle_inventory_sha256": bundle["inventory_sha256"],
                "input_bundle_hash_index_sha256": bundle["hash_index_sha256"],
                "input_bundle_file_sha256_before": bundle["input_file_sha256"],
                "mesh_worker_source_sha256": source_hashes,
                "current_candidate_binding": {
                    "revision_id": inventory["candidate"]["revision_id"],
                    "implementation_revision": inventory["candidate"]["implementation_revision"],
                    "source_inventory_baseline_commit": inventory["candidate"][
                        "source_inventory_baseline_commit"
                    ],
                    "source_inventory_sha256": inventory["candidate"][
                        "source_inventory_sha256"
                    ],
                    "geometry_binding": inventory["geometry_binding"],
                    "current_review_pins": inventory["candidate"]["current_review_pins"],
                },
                "input_geometry_context": {
                    "scope": inventory["scope"],
                    "wood_bodies": inventory["wood_bodies"],
                    "physical_bolts": inventory["physical_bolts"],
                    "physical_metal_bodies": inventory["physical_metal_bodies"],
                    "wood_interfaces": inventory["wood_interfaces"],
                    "migration_blockers": inventory.get("migration_blockers", []),
                    "contact_classification": (
                        "pending; mesh entities are not assigned to interfaces"
                    ),
                },
                "mesh_body_owner_order": [spec["mesh_body_id"] for spec in specs],
                "mesh_body_count_expected": 19,
            }
        )
        write_json(output / "mesh.json", record)

        import gmsh
        import numpy

        if gmsh.isInitialized():
            raise ValueError("independent Gmsh session required for current-patch meshing")
        gmsh.initialize()
        initialized = True
        gmsh.option.setNumber("General.NumThreads", 1)
        gmsh.option.setNumber("General.Verbosity", 2)
        with tempfile.TemporaryDirectory(prefix="current-patch-mesh-stage-") as temp_name:
            scratch_directory = Path(temp_name)
            for index, spec in enumerate(specs):
                active_body_id = spec["mesh_body_id"]
                source_step_key = spec["source_step_artifact_key"]
                settings = (
                    wood_settings
                    if spec["owner_kind"] == "wood_member"
                    else metal_settings
                )
                body = _mesh_one_body(
                    gmsh,
                    source_directory,
                    scratch_directory,
                    spec,
                    settings,
                    nodes,
                    elements,
                )
                body.update(
                    {
                        "mesh_body_id": active_body_id,
                        "element_elset_name": active_body_id,
                        "owner_kind": spec["owner_kind"],
                        "source_body_id": spec["source_body_id"],
                        "physical_body_id": spec["physical_body_id"],
                        "axis_id": spec["axis_id"],
                        "component_role": spec["component_role"],
                        "source_cad_role_ids": spec["source_cad_role_ids"],
                        "source_step_artifact_key": source_step_key,
                        "source_step_path": spec["source_step_path"],
                        "source_step_sha256": bundle["input_file_sha256"][
                            spec["source_step_path"]
                        ],
                        "source_solid_metadata": spec["solid_metadata"],
                        "element_owner_basis": (
                            "disjoint global element IDs in this body row and its deck ELSET"
                        ),
                        "node_ownership_basis": (
                            "disjoint global node IDs; coincident coordinates are not merged"
                        ),
                    }
                )
                bodies[active_body_id] = body
                record["completed_body_ids"] = list(bodies)
                record["completed_node_count"] = len(nodes)
                record["completed_element_count"] = len(elements)
                record["bodies"] = bodies
                write_json(output / "mesh.json", record)
                gmsh.model.remove()
                active_body_id = None
        record["runtime"] = {
            "python": platform.python_version(),
            "gmsh_version": str(gmsh.__version__),
            "numpy_version": str(numpy.__version__),
        }
        gmsh.finalize()
        initialized = False

        validate_ownership(nodes, elements, bodies)
        if len(bodies) != 19 or sum(
            body["owner_kind"] == "wood_member" for body in bodies.values()
        ) != 3 or sum(
            body["owner_kind"] == "physical_metal" for body in bodies.values()
        ) != 16:
            raise ValueError("mesh ownership is not exactly three wood and sixteen metal bodies")
        verify_input_bundle(bundle)
        verify_sources(source_hashes)
        deck = output / "mesh.inp"
        _write_input_deck(deck, nodes, elements, bodies, specs)
        record.update(
            {
                "status": STATUS_VERIFIED,
                "body_count": len(bodies),
                "wood_body_count": 3,
                "physical_metal_body_count": 16,
                "node_count": len(nodes),
                "element_count": len(elements),
                "bodies": bodies,
                "mesh_input_file": "mesh.inp",
                "mesh_input_sha256": sha256_file(deck),
                "mesh_deck_contract": {
                    "element_type": "C3D10",
                    "node_coordinate_card": "*NODE",
                    "element_connectivity_card": "*ELEMENT,TYPE=C3D10",
                    "body_ownership": {
                        spec["mesh_body_id"]: spec["mesh_body_id"]
                        for spec in specs
                    },
                    "node_ids_global_unique": True,
                    "element_ids_global_unique": True,
                    "coincident_nodes_merged_across_bodies": False,
                    "contains_material_contact_tie_load_or_solver_cards": False,
                },
                "input_bundle_file_sha256_after": bundle["input_file_sha256"],
                "mesh_worker_source_sha256_after": source_hashes,
                "native_solve_run": False,
                "contact_or_interface_classification_assigned": False,
                "output_contains_material_contact_or_solver_cards": False,
            }
        )
        write_json(output / "mesh.json", record)
        return output
    except Exception as error:
        failed_model = None
        if initialized and gmsh is not None and active_body_id is not None:
            try:
                failed_model = wood_mesh.preserve_failed_gmsh_model(
                    gmsh, output, active_body_id
                )
            except Exception as capture_error:  # noqa: BLE001 - retain original failure
                failed_model = {
                    "body_id": active_body_id,
                    "status": "capture_failed",
                    "capture_error": f"{type(capture_error).__name__}: {capture_error}",
                    "file": None,
                    "sha256": None,
                }
        record.update(
            {
                "status": "FAILED_CURRENT_PATCH_MESH_PREPARATION_NO_SOLVER",
                "error": f"{type(error).__name__}: {error}",
                "completed_body_ids": list(bodies),
                "completed_node_count": len(nodes),
                "completed_element_count": len(elements),
                "bodies": bodies,
                "failed_gmsh_model": failed_model,
                "native_solve_run": False,
                "contact_or_interface_classification_assigned": False,
            }
        )
        try:
            write_json(output / "mesh.json", record)
        except Exception as report_error:  # noqa: BLE001 - retain original failure
            error.add_note(
                f"Could not update failure record: {type(report_error).__name__}: {report_error}"
            )
        raise
    finally:
        if initialized and gmsh is not None:
            gmsh.finalize()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("bundle_directory", type=Path)
    parser.add_argument("output_directory", type=Path)
    parser.add_argument("--expected-inventory-sha256", required=True)
    parser.add_argument("--expected-hash-index-sha256", required=True)
    parser.add_argument("--wood-global-max-size-mm", type=float, required=True)
    parser.add_argument("--wood-axis-local-size-mm", type=float, required=True)
    parser.add_argument("--wood-axis-refinement-band-mm", type=float, required=True)
    parser.add_argument("--metal-global-max-size-mm", type=float, required=True)
    parser.add_argument("--metal-axis-local-size-mm", type=float, required=True)
    parser.add_argument("--metal-axis-refinement-band-mm", type=float, required=True)
    args = parser.parse_args()
    output = prepare_current_patch_mesh(
        args.bundle_directory,
        args.output_directory,
        expected_inventory_sha256=args.expected_inventory_sha256,
        expected_hash_index_sha256=args.expected_hash_index_sha256,
        wood_global_max_size_mm=args.wood_global_max_size_mm,
        wood_axis_local_size_mm=args.wood_axis_local_size_mm,
        wood_axis_refinement_band_mm=args.wood_axis_refinement_band_mm,
        metal_global_max_size_mm=args.metal_global_max_size_mm,
        metal_axis_local_size_mm=args.metal_axis_local_size_mm,
        metal_axis_refinement_band_mm=args.metal_axis_refinement_band_mm,
    )
    print(output, flush=True)


if __name__ == "__main__":
    main()
