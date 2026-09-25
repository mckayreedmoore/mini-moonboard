"""Build source-bound response-only hardware solids for the WJ04 WJ16 patch.

This module consumes the frozen five-wood/eight-bolt WJ16 patch inventory and
its mechanics/thread-screen archives. It does not rebuild the wood geometry,
use the forty historical cylinder collision roles as material solids, assign
wood-seat contact, mesh, run a native solve, or establish fastener capacity.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import shutil
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import cadquery as cq

from mini_moonboard.wood_joint_frame import _source_shape_fingerprint

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = "wood_joint_wj04_mechanics_hardware/v1"

PATCH_DIR = ROOT / "fea/results/diagnostics/wj04-full-stock-patch-geometry-v1"
PATCH_INVENTORY_PATH = PATCH_DIR / "inventory.json"
PATCH_HASHES_PATH = PATCH_DIR / "sha256.json"
MECHANICS_DIR = (
    ROOT / "docs/wood-joints-mvp/hypotheses/wj16-full-stock-mechanics-inputs"
)
MECHANICS_PATH = MECHANICS_DIR / "mechanics-inputs.json"
MECHANICS_HASHES_PATH = MECHANICS_DIR / "sha256.json"
MECHANICS_EXECUTION_PATH = MECHANICS_DIR / "execution.json"
THREAD_SCREEN_DIR = (
    ROOT / "docs/wood-joints-mvp/hypotheses/wj04-full-stock-thread-screen"
)
THREAD_SCREEN_PATH = THREAD_SCREEN_DIR / "thread-screen.json"
THREAD_SCREEN_HASHES_PATH = THREAD_SCREEN_DIR / "sha256.json"
HARDWARE_BASIS_PATH = ROOT / "docs/wood-joints-mvp/ordinary-hardware-basis.md"
WOOD_MATERIAL_SCENARIO_PATH = (
    ROOT / "docs/wood-joints-mvp/orthotropic-material-scenario.md"
)

FROZEN_PATCH_INVENTORY_SHA256 = (
    "c208f96bcfcda7a6b089496c9e1c4afe48f874810050f8d0c5cc700f65d5772d"
)
FROZEN_PATCH_HASHES_SHA256 = (
    "e758d733b9ba3169825220a45aea63ea1d1ebc70da0c9e2cb783464e8e4ea91d"
)
FROZEN_MECHANICS_SHA256 = (
    "f21e99f55da92ea60c950eecc6707fe98ca5df47f4d019f344c16fa06b52caf9"
)
FROZEN_MECHANICS_HASHES_SHA256 = (
    "d06981e497979a848e23b155515573f73c9e52de1d58d0904863bf9575d9a547"
)
FROZEN_MECHANICS_EXECUTION_SHA256 = (
    "64090ead266cb6d793a005629c8f4c55e8a0c661efe3686981e4196cf2b05d8d"
)
FROZEN_THREAD_SCREEN_SHA256 = (
    "70892ff5640d9ce01db45806c00f44a1828838adbf669f21e3cbfd806fa45afa"
)
FROZEN_THREAD_SCREEN_HASHES_SHA256 = (
    "369c921866ebe60dd77e3cf5bd383c66a831b26f4a10d7ecdac74614ad33b7de"
)
FROZEN_HARDWARE_BASIS_SHA256 = (
    "b66983d6ed267814289707cc5f3b5503dfe39ce723529b663092544e29ee8bf4"
)
FROZEN_WOOD_MATERIAL_SCENARIO_SHA256 = (
    "f6b723ddfc911284958df7a5348162f6d659396bbc03b83a74fcfbb125b3477f"
)

EXPECTED_BOLT_IDS = tuple(
    "wj04_g7/upper_g7_clearance_n86p9_reversed_rail_hypothesis/" + stack_id
    for stack_id in (
        "lower_rail_1",
        "lower_rail_2",
        "lower_principal_1",
        "lower_principal_2",
        "upper_rail_1",
        "upper_rail_2",
        "upper_principal_1",
        "upper_principal_2",
    )
)
EXPECTED_WOOD_IDS = frozenset(
    {
        "base_rail_service_lower_right",
        "base_rail_service_upper_right",
        "base_principal_center_right",
        "wj04_lower_full_stock_cleat",
        "wj04_upper_g7_crosscut_full_stock_cleat",
    }
)
EXPECTED_ROLE_NAMES = frozenset({"shaft", "head", "head_washer", "nut_washer", "nut"})

GEOMETRY_TOLERANCE_MM = 1e-7
METADATA_TOLERANCE_MM = 2e-6
SYMMETRIC_DIFFERENCE_ABS_TOLERANCE_MM3 = 1e-4
SYMMETRIC_DIFFERENCE_REL_TOLERANCE = 1e-9

# The dimensions below are one explicit response-only geometry choice from the
# local dimensional source note. They are not dimensions of inspected parts.
BOLT_LENGTH_NOMINAL_MM = 152.4
BOLT_LENGTH_LOWER_BOUND_MM = 149.86
BOLT_BODY_DIAMETER_MM = 6.35
BOLT_BODY_DIAMETER_RANGE_MM = (6.223, 6.35)
HEAD_ACROSS_CORNERS_MM = 12.827
HEAD_HEIGHT_MM = 4.1402
HEAD_ACROSS_FLATS_RANGE_MM = (10.8712, 11.1252)
NUT_ACROSS_CORNERS_MM = 12.827
NUT_THICKNESS_MM = 5.7404
NUT_ACROSS_FLATS_RANGE_MM = (10.8712, 11.1252)
WASHER_ID_MM = 8.3058
WASHER_OD_MM = 19.0246
WASHER_THICKNESS_MM = 2.032
WOOD_GRIP_MM = 127.0
LB_MM = 127.0
LG_MM = 133.35
THREAD_ROOT_BASIC_IN = 0.1887
NUT_BORE_BASIC_IN = 0.1959
INCH_MM = 25.4
THREAD_ROOT_BASIC_MM = THREAD_ROOT_BASIC_IN * INCH_MM
NUT_BORE_BASIC_MM = NUT_BORE_BASIC_IN * INCH_MM
WOOD_OCCUPANCY_BORE_DIAMETER_MM = 7.5
STEEL_E_MPA = 200_000.0
STEEL_NU = 0.30

SCENARIOS = (
    {
        "scenario_id": "body_to_far_wood_face",
        "root_transition_basis": "underhead + head washer + actual 127 mm wood grip",
        "transition_kind": "conditional body-through-wood profile",
        "transition_station_mm": WASHER_THICKNESS_MM + WOOD_GRIP_MM,
        "physical_profile_claim": False,
        "interpretation": (
            "A response-only scenario with the selected maximum catalog body "
            "diameter through the far wood face, followed by a smooth-cylinder "
            "basic-thread-root sensitivity segment. It does not claim that the "
            "catalog bolt has this delivered transition."
        ),
    },
    {
        "scenario_id": "Lb_boundary_root_sensitivity",
        "root_transition_basis": "ASME B18.2.1 Lb datum from underhead",
        "transition_kind": "named sensitivity switch, not actual thread start",
        "transition_station_mm": LB_MM,
        "physical_profile_claim": False,
        "interpretation": (
            "A response-only sensitivity that changes to the basic external "
            "minor-diameter cylinder at the 127 mm Lb screen datum. Lb denotes "
            "minimum body length to last thread scratch; it is not the actual "
            "first full-form thread or root transition."
        ),
    },
)

NBS_THREAD_REFERENCE = {
    "title": "Circular of the Bureau of Standards No. 479: Screw Thread Standards",
    "url": (
        "https://www.govinfo.gov/content/pkg/GOVPUB-C13-2edad299c8f39c5cc9909c067728f932/"
        "pdf/GOVPUB-C13-2edad299c8f39c5cc9909c067728f932.pdf"
    ),
    "pdf_sha256": "e31f189b5b24e2ce5832d191e7f4c336d6b789674088b1eb52ea47e990560b34",
    "printed_page": 21,
    "pdf_page_index_zero_based": 30,
    "pdf_page_number_one_based": 31,
    "table": "Table 2, Basic dimensions of the Unified coarse thread series",
    "cached_excerpt_path_in_export": (
        "references/nbs-unified-thread-table2-excerpt.json"
    ),
    "cached_excerpt": (
        "For 0.2500 in, 20 TPI, Table 2 lists 0.1887 in external-thread minor "
        "diameter and 0.1959 in internal-thread minor diameter."
    ),
    "rendered_page_verification": {
        "status": "parent independently confirmed the rendered Table 2 row",
        "page_image_filename": "wj04-nbs-table2-parent-p30.png",
        "page_image_sha256": "bd23d75681c2568ac81f281dbff0834edb9192f2c46d05c1f2607460705c4532",
        "archive_note": "parent will retain the image with the actual geometry run",
    },
    "values_used": {
        "external_minor_diameter_in": THREAD_ROOT_BASIC_IN,
        "external_minor_diameter_mm": THREAD_ROOT_BASIC_MM,
        "internal_minor_diameter_in": NUT_BORE_BASIC_IN,
        "internal_minor_diameter_mm": NUT_BORE_BASIC_MM,
    },
    "limitation": (
        "Basic reference dimensions only; not thread-class limits, root "
        "tolerances, delivered dimensions, or K.L. Jack profile verification."
    ),
}


@dataclass(frozen=True)
class FrozenInputs:
    patch_inventory: dict[str, Any]
    mechanics_manifest: dict[str, Any]
    thread_screen: dict[str, Any]
    input_hashes: dict[str, str]


@dataclass(frozen=True)
class BuiltHardware:
    report: dict[str, Any]
    shapes: dict[str, cq.Shape]


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _sha256_file(path: Path) -> str:
    return _sha256_bytes(path.read_bytes())


def _json_bytes(value: Any) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode("utf-8")


def _load_json(path: Path, expected_sha256: str, context: str) -> tuple[Any, str]:
    if not path.is_file():
        raise ValueError(f"{context}: pinned source is unavailable: {path}")
    data = path.read_bytes()
    digest = _sha256_bytes(data)
    if digest != expected_sha256:
        raise ValueError(f"{context}: pinned SHA-256 changed: {path}")
    try:
        return json.loads(data), digest
    except json.JSONDecodeError as error:
        raise ValueError(f"{context}: invalid JSON: {path}") from error


def load_frozen_inputs() -> FrozenInputs:
    """Load and hash-check the exact WJ16 input bundle and dependent reports."""
    patch_hashes, patch_hashes_sha = _load_json(
        PATCH_HASHES_PATH, FROZEN_PATCH_HASHES_SHA256, "patch archive hash index"
    )
    if patch_hashes.get("inventory.json") != FROZEN_PATCH_INVENTORY_SHA256:
        raise ValueError("patch archive inventory hash index changed")
    patch_inventory, patch_inventory_sha = _load_json(
        PATCH_INVENTORY_PATH,
        FROZEN_PATCH_INVENTORY_SHA256,
        "five-body patch inventory",
    )
    for relative_path, expected_sha in patch_hashes.items():
        path = PATCH_DIR / relative_path
        if not path.is_file() or _sha256_file(path) != expected_sha:
            raise ValueError(f"patch archive artifact hash changed: {relative_path}")

    mechanics_hashes, mechanics_hashes_sha = _load_json(
        MECHANICS_HASHES_PATH,
        FROZEN_MECHANICS_HASHES_SHA256,
        "mechanics archive hash index",
    )
    if mechanics_hashes.get("mechanics-inputs.json") != FROZEN_MECHANICS_SHA256:
        raise ValueError("mechanics archive inventory hash index changed")
    mechanics_manifest, mechanics_sha = _load_json(
        MECHANICS_PATH, FROZEN_MECHANICS_SHA256, "WJ16 mechanics manifest"
    )
    for filename, expected in mechanics_hashes.items():
        path = MECHANICS_DIR / filename
        if not path.is_file() or _sha256_file(path) != expected:
            raise ValueError(f"mechanics source archive changed: {filename}")
    execution_bytes = MECHANICS_EXECUTION_PATH.read_bytes()
    execution_sha = _sha256_bytes(execution_bytes)
    if execution_sha != FROZEN_MECHANICS_EXECUTION_SHA256:
        raise ValueError("WJ16 mechanics execution record hash changed")
    if mechanics_hashes.get("execution.json") != execution_sha:
        raise ValueError("mechanics archive execution hash index changed")

    thread_hashes, thread_hashes_sha = _load_json(
        THREAD_SCREEN_HASHES_PATH,
        FROZEN_THREAD_SCREEN_HASHES_SHA256,
        "thread-screen archive hash index",
    )
    if thread_hashes.get("thread-screen.json") != FROZEN_THREAD_SCREEN_SHA256:
        raise ValueError("thread-screen archive hash index changed")
    thread_screen, thread_sha = _load_json(
        THREAD_SCREEN_PATH,
        FROZEN_THREAD_SCREEN_SHA256,
        "thread-screen report",
    )
    for filename, expected in thread_hashes.items():
        path = THREAD_SCREEN_DIR / filename
        if not path.is_file() or _sha256_file(path) != expected:
            raise ValueError(f"thread-screen source archive changed: {filename}")

    for path, expected, context in (
        (HARDWARE_BASIS_PATH, FROZEN_HARDWARE_BASIS_SHA256, "ordinary hardware basis"),
        (
            WOOD_MATERIAL_SCENARIO_PATH,
            FROZEN_WOOD_MATERIAL_SCENARIO_SHA256,
            "wood material scenario",
        ),
    ):
        if not path.is_file() or _sha256_file(path) != expected:
            raise ValueError(f"{context}: frozen source changed")

    input_hashes = {
        "patch_inventory.json": patch_inventory_sha,
        "patch_sha256.json": patch_hashes_sha,
        "mechanics_inputs.json": mechanics_sha,
        "mechanics_sha256.json": mechanics_hashes_sha,
        "mechanics_execution.json": execution_sha,
        "thread_screen.json": thread_sha,
        "thread_screen_sha256.json": thread_hashes_sha,
        "ordinary_hardware_basis.md": FROZEN_HARDWARE_BASIS_SHA256,
        "orthotropic_material_scenario.md": FROZEN_WOOD_MATERIAL_SCENARIO_SHA256,
    }
    _validate_source_contract(
        patch_inventory, mechanics_manifest, thread_screen, input_hashes
    )
    return FrozenInputs(
        patch_inventory=patch_inventory,
        mechanics_manifest=mechanics_manifest,
        thread_screen=thread_screen,
        input_hashes=input_hashes,
    )


def _finite_vec3(values: Any, context: str) -> tuple[float, float, float]:
    try:
        result = tuple(float(value) for value in values)
    except (TypeError, ValueError) as error:
        raise ValueError(f"{context}: expected a finite 3-vector") from error
    if len(result) != 3 or not all(math.isfinite(value) for value in result):
        raise ValueError(f"{context}: expected a finite 3-vector")
    return result  # type: ignore[return-value]


def _unit(values: Any, context: str) -> tuple[float, float, float]:
    vector = _finite_vec3(values, context)
    magnitude = math.sqrt(sum(value * value for value in vector))
    if magnitude <= 1e-12:
        raise ValueError(f"{context}: zero vector")
    return tuple(value / magnitude for value in vector)  # type: ignore[return-value]


def _dot(left: tuple[float, float, float], right: tuple[float, float, float]) -> float:
    return sum(a * b for a, b in zip(left, right, strict=True))


def _add(
    left: tuple[float, float, float], right: tuple[float, float, float]
) -> tuple[float, float, float]:
    return tuple(a + b for a, b in zip(left, right, strict=True))


def _scale(
    vector: tuple[float, float, float], scalar: float
) -> tuple[float, float, float]:
    return tuple(value * scalar for value in vector)


def _sub(
    left: tuple[float, float, float], right: tuple[float, float, float]
) -> tuple[float, float, float]:
    return tuple(a - b for a, b in zip(left, right, strict=True))


def _norm(vector: tuple[float, float, float]) -> float:
    return math.sqrt(_dot(vector, vector))


def _close_vec(left: Any, right: Any, tolerance: float = METADATA_TOLERANCE_MM) -> bool:
    try:
        a = _finite_vec3(left, "left vector")
        b = _finite_vec3(right, "right vector")
    except ValueError:
        return False
    return _norm(_sub(a, b)) <= tolerance


def _near(left: Any, right: Any, *, tolerance: float = METADATA_TOLERANCE_MM) -> bool:
    try:
        a, b = float(left), float(right)
    except (TypeError, ValueError):
        return False
    return math.isfinite(a) and math.isfinite(b) and abs(a - b) <= tolerance


def _validate_source_contract(
    patch: dict[str, Any],
    mechanics: dict[str, Any],
    thread_screen: dict[str, Any],
    input_hashes: dict[str, str],
) -> None:
    if patch.get("schema") != "wood_joint_wj04_patch_geometry/v1":
        raise ValueError("patch inventory schema changed")
    if patch.get("status") != "source_bound_finished_geometry_export_inputs_only":
        raise ValueError(
            "patch inventory is not the frozen source-bound geometry bundle"
        )
    source_rows = patch.get("wood_bodies")
    if not isinstance(source_rows, list) or len(source_rows) != 5:
        raise ValueError("patch bundle must bind exactly five finished wood bodies")
    if {row.get("part_id") for row in source_rows} != EXPECTED_WOOD_IDS:
        raise ValueError(
            "patch bundle wood IDs differ from the representative WJ04 joint"
        )
    if len({row.get("part_id") for row in source_rows}) != 5:
        raise ValueError("patch bundle contains duplicate wood body IDs")
    if patch.get("composition", {}).get(
        "mechanics_manifest_sha256"
    ) != input_hashes.get("mechanics_inputs.json"):
        raise ValueError("patch bundle and WJ16 mechanics manifest hashes disagree")
    if patch.get("composition", {}).get("wj16_composition_report_sha256") != (
        "c0bc37fdbc364deafcbc86dc04e710d2f5b6809436e560717a97593951f8ebcb"
    ):
        raise ValueError("patch bundle WJ16 composition binding changed")
    fingerprints = patch.get("composition", {}).get(
        "right_g7_source_fingerprints_sha256", {}
    )
    if fingerprints.get("docs/wood-joints-mvp/ordinary-hardware-basis.md") != (
        input_hashes.get("ordinary_hardware_basis.md")
    ):
        raise ValueError("WJ16 source pin does not bind the ordinary hardware basis")
    if mechanics.get("schema") != "wood_joint_wj04_full_stock_mechanics_contract/v1":
        raise ValueError("WJ16 mechanics manifest schema changed")
    if mechanics.get("status") != "bounded_mechanics_inputs_only":
        raise ValueError("WJ16 mechanics manifest status changed")
    if mechanics.get("scope") != (
        "right inner lower and upper full-stock G7 cleat pair; eight physical ordinary-bolt axes"
    ):
        raise ValueError("WJ16 mechanics input scope changed")
    if mechanics.get("physical_inventory") != {
        "ordinary_physical_bolts": 8,
        "modeled_component_shapes_for_these_bolts": 40,
        "physical_interfaces": 4,
        "scope_does_not_cover": mechanics.get("physical_inventory", {}).get(
            "scope_does_not_cover"
        ),
    } or not mechanics.get("physical_inventory", {}).get("scope_does_not_cover"):
        raise ValueError("mechanics manifest counts/limits changed")

    patch_bolts = patch.get("physical_bolts")
    mechanics_bolts = mechanics.get("physical_bolts")
    screen_bolts = thread_screen.get("physical_bolts")
    if not all(
        isinstance(rows, list) for rows in (patch_bolts, mechanics_bolts, screen_bolts)
    ):
        raise ValueError("one or more source archives lack physical bolt rows")
    if any(len(rows) != 8 for rows in (patch_bolts, mechanics_bolts, screen_bolts)):
        raise ValueError("WJ04 response patch requires exactly eight physical bolts")
    if len({row.get("physical_bolt_id") for row in patch_bolts}) != 8:
        raise ValueError("patch bundle contains duplicate physical bolt IDs")
    if {row.get("physical_bolt_id") for row in mechanics_bolts} != set(
        EXPECTED_BOLT_IDS
    ):
        raise ValueError(
            "mechanics manifest does not contain the exact eight six-inch axes"
        )
    if {row.get("physical_bolt_id") for row in patch_bolts} != set(EXPECTED_BOLT_IDS):
        raise ValueError("patch bundle does not contain the exact eight six-inch axes")
    if {row.get("physical_bolt_id") for row in screen_bolts} != set(EXPECTED_BOLT_IDS):
        raise ValueError("thread screen does not bind the same eight physical bolts")
    if (
        thread_screen.get("schema")
        != "wood_joint_wj04_full_stock_thread_bearing_screen/v1"
    ):
        raise ValueError("full-stock thread-screen schema changed")
    if thread_screen.get("source", {}).get(
        "mechanics_inputs_sha256"
    ) != input_hashes.get("mechanics_inputs.json"):
        raise ValueError("thread screen and mechanics input hashes disagree")
    if thread_screen.get("source", {}).get("archive_manifest_sha256") != (
        FROZEN_MECHANICS_HASHES_SHA256
    ):
        raise ValueError("thread screen and mechanics archive hash index disagree")
    if thread_screen.get("source", {}).get("execution_sha256") != (
        FROZEN_MECHANICS_EXECUTION_SHA256
    ):
        raise ValueError("thread screen and mechanics execution record disagree")
    if (
        thread_screen.get("method", {}).get(
            "smooth_body_screen_boundary_Lb_mm_from_underhead"
        )
        != LB_MM
    ):
        raise ValueError("thread screen Lb datum differs from the pinned 127 mm basis")
    if (
        thread_screen.get("method", {}).get(
            "Lg_mm_recorded_but_not_used_as_thread_boundary"
        )
        != LG_MM
    ):
        raise ValueError(
            "thread screen Lg datum differs from the pinned 133.35 mm basis"
        )
    thread_boundary_assumption = thread_screen.get("method", {}).get(
        "thread_boundary_assumption", ""
    )
    if (
        "not measured" not in thread_boundary_assumption
        or "do not read this as an actual thread-transition guarantee"
        not in thread_boundary_assumption
    ):
        raise ValueError(
            "thread screen no longer distinguishes Lb from actual thread start"
        )

    patch_by_id = {row["physical_bolt_id"]: row for row in patch_bolts}
    mechanics_by_id = {row["physical_bolt_id"]: row for row in mechanics_bolts}
    screen_by_id = {row["physical_bolt_id"]: row for row in screen_bolts}
    for bolt_id in EXPECTED_BOLT_IDS:
        patch_row = patch_by_id[bolt_id]
        mechanics_row = mechanics_by_id[bolt_id]
        if patch_row.get("stack_spec_id") != bolt_id.rsplit("/", 1)[-1]:
            raise ValueError(f"{bolt_id}: patch stack ID changed")
        if mechanics_row.get("stack_spec_id") != patch_row.get("stack_spec_id"):
            raise ValueError(f"{bolt_id}: mechanics/patch stack IDs disagree")
        if (
            mechanics_row.get("interface_id")
            != patch_row.get("interface_id", "").split("__")[-1]
        ):
            raise ValueError(f"{bolt_id}: mechanics/patch interface binding disagrees")
        if not _near(patch_row.get("wood_grip_mm"), WOOD_GRIP_MM):
            raise ValueError(f"{bolt_id}: expected the six-inch/127 mm-grip family")
        if not _near(mechanics_row.get("wood_grip_mm"), WOOD_GRIP_MM):
            raise ValueError(
                f"{bolt_id}: mechanics manifest is not the 127 mm-grip family"
            )
        if mechanics_row.get("receivers_head_to_nut") != patch_row.get(
            "receivers_head_to_nut"
        ):
            raise ValueError(f"{bolt_id}: ordered receiver IDs/thicknesses disagree")
        if not _close_vec(
            patch_row.get("world_axis_origin_xyz_mm"),
            mechanics_row.get("world_axis_origin_xyz_mm"),
        ):
            raise ValueError(f"{bolt_id}: head-side wood-face axis datum disagrees")
        if not _close_vec(
            patch_row.get("world_axis_direction_head_to_nut"),
            mechanics_row.get("world_axis_direction_head_to_nut"),
            tolerance=1e-10,
        ):
            raise ValueError(f"{bolt_id}: world axis direction disagrees")
        hardware = mechanics_row.get("hardware", {})
        bolt_data = hardware.get("bolt", {})
        nut_data = hardware.get("nut", {})
        washer_data = hardware.get("washers", {})
        patch_bolt_data = patch_row.get("provisional_hardware", {}).get("bolt", {})
        if (
            bolt_data.get("sku") != "25C600HCS5Z"
            or bolt_data.get("thread") != "1/4-20 UNC"
            or not _near(bolt_data.get("nominal_length_mm"), BOLT_LENGTH_NOMINAL_MM)
            or not _near(bolt_data.get("minimum_smooth_body_Lb_mm"), LB_MM)
            or not _near(bolt_data.get("maximum_grip_gage_Lg_mm"), LG_MM)
            or not _near(bolt_data.get("catalog_length_minus_tolerance_mm"), 2.54)
            or nut_data.get("sku") != "25CNFH5Z"
            or washer_data.get("quantity") != 2
            or patch_bolt_data.get("sku") != "25C600HCS5Z"
            or not _near(
                patch_bolt_data.get("nominal_length_mm"), BOLT_LENGTH_NOMINAL_MM
            )
        ):
            raise ValueError(
                f"{bolt_id}: candidate is not the pinned six-inch 1/4-20 stack"
            )
        if screen_by_id[bolt_id].get("stack_spec_id") != patch_row.get("stack_spec_id"):
            raise ValueError(f"{bolt_id}: thread screen stack identity disagrees")

        role_rows = patch_row.get("physical_hardware_roles")
        if not isinstance(role_rows, list) or len(role_rows) != 5:
            raise ValueError(f"{bolt_id}: missing five historical collision roles")
        if {row.get("role") for row in role_rows} != EXPECTED_ROLE_NAMES:
            raise ValueError(f"{bolt_id}: historical collision role set changed")
        if not all(
            row.get("cad_shape", {}).get("solid_count") == 1 for row in role_rows
        ):
            raise ValueError(f"{bolt_id}: historical collision role metadata malformed")

    interfaces = mechanics.get("physical_interfaces")
    if not isinstance(interfaces, list) or len(interfaces) != 4:
        raise ValueError("WJ04 mechanics input must bind four physical wood interfaces")
    if len(patch.get("wood_interfaces", [])) != 4:
        raise ValueError("patch bundle must bind four wood interfaces")
    if thread_screen.get("physical_bolt_count") != 8:
        raise ValueError("thread screen physical bolt count changed")


def _shape_metadata(shape: cq.Shape, context: str) -> dict[str, Any]:
    if not isinstance(shape, cq.Shape) or shape.isNull() or not shape.isValid():
        raise ValueError(f"{context}: missing or invalid CAD shape")
    solids = shape.Solids()
    volume = float(shape.Volume())
    if len(solids) != 1 or not math.isfinite(volume) or volume <= 0:
        raise ValueError(f"{context}: expected one valid positive-volume solid")
    box = shape.BoundingBox()
    center = shape.Center().toTuple()
    bounds = [
        float(box.xmin),
        float(box.xmax),
        float(box.ymin),
        float(box.ymax),
        float(box.zmin),
        float(box.zmax),
    ]
    if not all(math.isfinite(float(value)) for value in (*center, *bounds)):
        raise ValueError(f"{context}: non-finite geometry metadata")
    return {
        "solid_count": 1,
        "volume_mm3": round(volume, 9),
        "centroid_global_xyz_mm": [round(float(value), 9) for value in center],
        "bounds_xyz_mm": [round(value, 9) for value in bounds],
        "cad_shape_sha256": _source_shape_fingerprint(shape),
    }


def _hex_plane_basis(
    direction: tuple[float, float, float],
) -> tuple[tuple[float, float, float], tuple[float, float, float]]:
    seeds = ((1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0))
    seed = min(seeds, key=lambda vector: abs(_dot(vector, direction)))
    projected = _sub(seed, _scale(direction, _dot(seed, direction)))
    u = _unit(projected, "hex clocking reference")
    cross = (
        direction[1] * u[2] - direction[2] * u[1],
        direction[2] * u[0] - direction[0] * u[2],
        direction[0] * u[1] - direction[1] * u[0],
    )
    v = _unit(cross, "hex transverse axis")
    return u, v


def _hex_prism(
    origin: tuple[float, float, float],
    direction: tuple[float, float, float],
    across_corners_mm: float,
    height_mm: float,
) -> cq.Shape:
    u, _v = _hex_plane_basis(direction)
    plane = cq.Plane(
        origin=cq.Vector(*origin),
        xDir=cq.Vector(*u),
        normal=cq.Vector(*direction),
    )
    return cq.Workplane(plane).polygon(6, across_corners_mm).extrude(height_mm).val()


def _annular_cylinder(
    origin: tuple[float, float, float],
    direction: tuple[float, float, float],
    outer_diameter_mm: float,
    inner_diameter_mm: float,
    thickness_mm: float,
) -> cq.Shape:
    if inner_diameter_mm <= 0 or outer_diameter_mm <= inner_diameter_mm:
        raise ValueError("annular hardware dimensions are not physically ordered")
    start = cq.Vector(*origin)
    axis = cq.Vector(*direction)
    outer = cq.Solid.makeCylinder(outer_diameter_mm / 2, thickness_mm, start, axis)
    through_bore = cq.Solid.makeCylinder(
        inner_diameter_mm / 2,
        thickness_mm + 0.02,
        start - axis.multiply(0.01),
        axis,
    )
    return outer.cut(through_bore).clean()


def _hollow_hex_nut(
    origin: tuple[float, float, float],
    direction: tuple[float, float, float],
) -> cq.Shape:
    outside = _hex_prism(origin, direction, NUT_ACROSS_CORNERS_MM, NUT_THICKNESS_MM)
    axis = cq.Vector(*direction)
    inside = cq.Solid.makeCylinder(
        NUT_BORE_BASIC_MM / 2,
        NUT_THICKNESS_MM + 0.02,
        cq.Vector(*origin) - axis.multiply(0.01),
        axis,
    )
    return outside.cut(inside).clean()


def _one_physical_stack(
    patch_row: dict[str, Any],
    mechanics_row: dict[str, Any],
    scenario: dict[str, Any],
) -> tuple[dict[str, cq.Shape], dict[str, Any]]:
    bolt_id = patch_row["physical_bolt_id"]
    direction = _unit(
        mechanics_row.get("world_axis_direction_head_to_nut"),
        f"{bolt_id} head-to-nut axis",
    )
    wood_head_face = _finite_vec3(
        mechanics_row.get("world_axis_origin_xyz_mm"), f"{bolt_id} first wood face"
    )
    underhead = _sub(wood_head_face, _scale(direction, WASHER_THICKNESS_MM))
    legacy_underhead = _finite_vec3(
        mechanics_row.get("modeled_bolt_under_head_origin_xyz_mm"),
        f"{bolt_id} legacy collision underhead datum",
    )
    legacy_delta = _sub(underhead, legacy_underhead)
    legacy_axial_delta = _dot(legacy_delta, direction)
    legacy_transverse_delta = _sub(legacy_delta, _scale(direction, legacy_axial_delta))

    receiver_rows = mechanics_row.get("receivers_head_to_nut")
    if not isinstance(receiver_rows, list) or len(receiver_rows) != 2:
        raise ValueError(f"{bolt_id}: expected two ordered physical wood receivers")
    grip = sum(float(row["wood_thickness_mm"]) for row in receiver_rows)
    if not _near(grip, WOOD_GRIP_MM):
        raise ValueError(f"{bolt_id}: source receiver layers do not total 127 mm")
    first_face = wood_head_face
    far_face = _add(first_face, _scale(direction, grip))
    underhead_to_far_face = WASHER_THICKNESS_MM + grip
    transition = float(scenario["transition_station_mm"])
    if not (0 < transition < BOLT_LENGTH_NOMINAL_MM):
        raise ValueError(f"{scenario['scenario_id']}: invalid root transition station")
    if transition > underhead_to_far_face + GEOMETRY_TOLERANCE_MM:
        raise ValueError(
            f"{scenario['scenario_id']}: root transition exceeds far wood face"
        )

    underhead_point = cq.Vector(*underhead)
    axis_vector = cq.Vector(*direction)
    root_start = underhead_point + axis_vector.multiply(transition)
    smooth_section = cq.Solid.makeCylinder(
        BOLT_BODY_DIAMETER_MM / 2,
        transition,
        underhead_point,
        axis_vector,
    )
    root_section = cq.Solid.makeCylinder(
        THREAD_ROOT_BASIC_MM / 2,
        BOLT_LENGTH_NOMINAL_MM - transition,
        root_start,
        axis_vector,
    )
    head_origin = _sub(underhead, _scale(direction, HEAD_HEIGHT_MM))
    head = _hex_prism(
        head_origin,
        direction,
        HEAD_ACROSS_CORNERS_MM,
        HEAD_HEIGHT_MM,
    )
    bolt = head.fuse(smooth_section, root_section).clean()
    if not bolt.isValid() or len(bolt.Solids()) != 1:
        raise ValueError(
            f"{bolt_id}: head and shank did not form one continuous bolt solid"
        )

    head_washer_start = underhead
    nut_washer_start = _add(underhead, _scale(direction, underhead_to_far_face))
    nut_start_station = underhead_to_far_face + WASHER_THICKNESS_MM
    nut_start = _add(underhead, _scale(direction, nut_start_station))
    nut_end_station = nut_start_station + NUT_THICKNESS_MM
    tip_station = BOLT_LENGTH_NOMINAL_MM
    if nut_end_station >= tip_station:
        raise ValueError(f"{bolt_id}: selected nut extends beyond the nominal bolt tip")
    head_washer = _annular_cylinder(
        head_washer_start,
        direction,
        WASHER_OD_MM,
        WASHER_ID_MM,
        WASHER_THICKNESS_MM,
    )
    nut_washer = _annular_cylinder(
        nut_washer_start,
        direction,
        WASHER_OD_MM,
        WASHER_ID_MM,
        WASHER_THICKNESS_MM,
    )
    nut = _hollow_hex_nut(nut_start, direction)

    names = {
        "bolt": bolt,
        "head_washer": head_washer,
        "nut_washer": nut_washer,
        "nut": nut,
    }
    shape_metadata = {
        name: _shape_metadata(shape, f"{bolt_id}/{name}")
        for name, shape in names.items()
    }
    for first_name, first_shape in names.items():
        for second_name, second_shape in names.items():
            if first_name >= second_name:
                continue
            overlap = float(first_shape.intersect(second_shape).Volume())
            if not math.isfinite(overlap) or overlap > 1e-6:
                raise ValueError(
                    f"{bolt_id}: hardware solids overlap: {first_name}/{second_name}"
                )

    selected_ac = HEAD_ACROSS_CORNERS_MM
    head_af = selected_ac * math.sqrt(3.0) / 2.0
    nut_af = NUT_ACROSS_CORNERS_MM * math.sqrt(3.0) / 2.0
    if not (
        HEAD_ACROSS_FLATS_RANGE_MM[0] <= head_af <= HEAD_ACROSS_FLATS_RANGE_MM[1]
        and NUT_ACROSS_FLATS_RANGE_MM[0] <= nut_af <= NUT_ACROSS_FLATS_RANGE_MM[1]
    ):
        raise ValueError("selected regular-hex AF/AC pairs exceed catalog bounds")

    root_overlap_start = max(transition, nut_start_station)
    root_overlap_end = min(BOLT_LENGTH_NOMINAL_MM, nut_end_station)
    tie_length = max(0.0, root_overlap_end - root_overlap_start)
    radial_tie_gap = (NUT_BORE_BASIC_MM - THREAD_ROOT_BASIC_MM) / 2
    if not _near(tie_length, NUT_THICKNESS_MM):
        raise ValueError(f"{bolt_id}: root/nut tie does not span full nut thickness")
    if radial_tie_gap <= 0:
        raise ValueError(
            f"{bolt_id}: idealized thread engagement has no positive projection gap"
        )

    stack_id = patch_row["stack_spec_id"]
    record = {
        "physical_bolt_id": bolt_id,
        "stack_spec_id": stack_id,
        "interface_id": patch_row["interface_id"],
        "receivers_head_to_nut": receiver_rows,
        "world_axis_direction_head_to_nut": [round(value, 12) for value in direction],
        "wood_head_face_center_global_xyz_mm": [
            round(value, 9) for value in first_face
        ],
        "wood_far_face_center_global_xyz_mm": [round(value, 9) for value in far_face],
        "underhead_origin_global_xyz_mm": [round(value, 9) for value in underhead],
        "underhead_origin_basis": (
            "pinned first wood-face axis datum minus selected 2.032 mm head washer"
        ),
        "legacy_collision_underhead_origin_global_xyz_mm": [
            round(value, 9) for value in legacy_underhead
        ],
        "new_minus_legacy_underhead_delta_global_xyz_mm": [
            round(value, 9) for value in legacy_delta
        ],
        "new_minus_legacy_underhead_delta_axial_mm": round(legacy_axial_delta, 9),
        "new_minus_legacy_underhead_transverse_delta_mm": round(
            _norm(legacy_transverse_delta), 9
        ),
        "wood_grip_mm": round(grip, 9),
        "underhead_to_far_wood_face_mm": round(underhead_to_far_face, 9),
        "bolt_tip_station_from_underhead_mm": BOLT_LENGTH_NOMINAL_MM,
        "nut_washer_start_station_from_underhead_mm": round(underhead_to_far_face, 9),
        "nut_start_station_from_underhead_mm": round(nut_start_station, 9),
        "nut_end_station_from_underhead_mm": round(nut_end_station, 9),
        "Lg_marker_station_from_underhead_mm": LG_MM,
        "Lb_marker_station_from_underhead_mm": LB_MM,
        "scenario_id": scenario["scenario_id"],
        "smooth_body_transition_station_from_underhead_mm": transition,
        "smooth_body_transition_basis": scenario["root_transition_basis"],
        "root_to_nut_engagement": {
            "method": "projected cylindrical tie; no helical thread geometry",
            "tie_span_mm": round(tie_length, 9),
            "full_nut_thickness_engagement_assumed": True,
            "external_root_basic_reference_diameter_mm": round(THREAD_ROOT_BASIC_MM, 9),
            "nut_internal_minor_basic_reference_bore_mm": round(NUT_BORE_BASIC_MM, 9),
            "diametral_projection_gap_mm": round(
                NUT_BORE_BASIC_MM - THREAD_ROOT_BASIC_MM, 9
            ),
            "radial_projection_gap_mm": round(radial_tie_gap, 9),
            "solver_adjust_or_gap_closure_mm": 0.0,
            "no_adjustment_or_gap_closure": True,
            "physical_thread_profile_or_engagement_verified": False,
        },
        "regular_hex": {
            "across_corners_mm": selected_ac,
            "derived_across_flats_mm": round(head_af, 9),
            "clocking_reference_global_xyz": [
                round(value, 12) for value in _hex_plane_basis(direction)[0]
            ],
            "clocking_is_actual_installed_orientation": False,
        },
        "component_solids": shape_metadata,
        "component_role_count": len(names),
        "component_role_names": sorted(names),
        "wood_or_washer_tie_assigned": False,
        "step_shapes": names,
    }
    return names, record


def _legacy_collision_roles(patch_inventory: dict[str, Any]) -> list[dict[str, Any]]:
    roles = []
    for bolt in patch_inventory["physical_bolts"]:
        for row in bolt["physical_hardware_roles"]:
            roles.append(
                {
                    "physical_bolt_id": bolt["physical_bolt_id"],
                    "stack_spec_id": bolt["stack_spec_id"],
                    "role": row["role"],
                    "cad_shape": row["cad_shape"],
                    "interpretation": "legacy collision envelope metadata only; not a mechanics solid",
                }
            )
    if len(roles) != 40:
        raise ValueError("exactly forty legacy collision role records must be retained")
    return roles


def build_hardware_contract(inputs: FrozenInputs) -> BuiltHardware:
    """Build in-memory scenario solids and a source-bound contract; no file writes."""
    _validate_source_contract(
        inputs.patch_inventory,
        inputs.mechanics_manifest,
        inputs.thread_screen,
        inputs.input_hashes,
    )
    patch_by_id = {
        row["physical_bolt_id"]: row for row in inputs.patch_inventory["physical_bolts"]
    }
    mechanics_by_id = {
        row["physical_bolt_id"]: row
        for row in inputs.mechanics_manifest["physical_bolts"]
    }
    scenarios_report = []
    shapes: dict[str, cq.Shape] = {}
    for scenario in SCENARIOS:
        stack_records = []
        for bolt_id in EXPECTED_BOLT_IDS:
            bolt_shapes, record = _one_physical_stack(
                patch_by_id[bolt_id], mechanics_by_id[bolt_id], scenario
            )
            for role, shape in bolt_shapes.items():
                key = f"{scenario['scenario_id']}/{record['stack_spec_id']}/{role}"
                if key in shapes:
                    raise ValueError(f"duplicate mechanics-solid identity {key}")
                shapes[key] = shape
            stack_records.append(
                {key: value for key, value in record.items() if key != "step_shapes"}
            )
        scenarios_report.append(
            {
                **{key: value for key, value in scenario.items()},
                "physical_bolt_count": len(stack_records),
                "physical_solid_count": len(stack_records) * 4,
                "purchase_count": len(stack_records),
                "stacks": stack_records,
            }
        )

    expected_solid_keys = {
        f"{scenario['scenario_id']}/{stack_id}/{role}"
        for scenario in SCENARIOS
        for stack_id in (bolt_id.rsplit("/", 1)[-1] for bolt_id in EXPECTED_BOLT_IDS)
        for role in ("bolt", "head_washer", "nut_washer", "nut")
    }
    if set(shapes) != expected_solid_keys or len(shapes) != 64:
        raise ValueError(
            "two response scenarios must contain exactly 64 physical solids"
        )

    clearances = {
        "candidate_wood_axis_occupancy_diameter_mm": WOOD_OCCUPANCY_BORE_DIAMETER_MM,
        "selected_smooth_body_diameter_mm": BOLT_BODY_DIAMETER_MM,
        "nominal_radial_shank_to_wood_bore_gap_mm": round(
            (WOOD_OCCUPANCY_BORE_DIAMETER_MM - BOLT_BODY_DIAMETER_MM) / 2, 9
        ),
        "selected_washer_bore_diameter_mm": WASHER_ID_MM,
        "radial_washer_bore_to_smooth_shank_gap_mm": round(
            (WASHER_ID_MM - BOLT_BODY_DIAMETER_MM) / 2, 9
        ),
        "washer_and_wood_are_separate_unilateral_contact_surfaces": True,
        "initial_seat_gap_scenario_mm": 0.0,
        "preload_n": 0.0,
        "friction_coefficient": 0.0,
        "wood_face_or_washer_tie": False,
        "no_adjustment_or_gap_closure_at_wood_or_washer_seats": True,
        "contact_law_assigned": False,
    }
    report = {
        "schema": SCHEMA,
        "status": "conditional_response_hardware_geometry_only",
        "scope": {
            "joint": "actual WJ16 right inner full-stock G7 lower+upper pair",
            "finished_wood_bodies_consumed": 5,
            "unique_physical_bolts": 8,
            "grip_each_bolt_mm": WOOD_GRIP_MM,
            "physical_solids_per_scenario": 32,
            "scenarios": 2,
            "native_solver_run": False,
            "mesh_generated": False,
            "capacity_or_release_claim": False,
        },
        "source_inputs": {
            "sha256": dict(sorted(inputs.input_hashes.items())),
            "frozen_wood_ids": sorted(EXPECTED_WOOD_IDS),
            "frozen_physical_bolt_ids": list(EXPECTED_BOLT_IDS),
            "patch_bundle_path": str(PATCH_DIR.relative_to(ROOT)),
            "mechanics_manifest_path": str(MECHANICS_PATH.relative_to(ROOT)),
            "thread_screen_path": str(THREAD_SCREEN_PATH.relative_to(ROOT)),
        },
        "selected_hardware_geometry": {
            "status": "provisional catalog geometry for conditional response scenarios",
            "bolt": {
                "sku": "25C600HCS5Z",
                "thread_designation": "1/4-20 UNC",
                "grade_label": "Grade 5 catalog designation; strength not modeled or assessed",
                "nominal_length_mm": BOLT_LENGTH_NOMINAL_MM,
                "catalog_lower_length_bound_mm": BOLT_LENGTH_LOWER_BOUND_MM,
                "smooth_body_diameter_mm": BOLT_BODY_DIAMETER_MM,
                "body_diameter_range_mm": list(BOLT_BODY_DIAMETER_RANGE_MM),
                "head_across_corners_mm": HEAD_ACROSS_CORNERS_MM,
                "head_derived_across_flats_mm": round(
                    HEAD_ACROSS_CORNERS_MM * math.sqrt(3.0) / 2, 9
                ),
                "head_across_flats_source_range_mm": list(HEAD_ACROSS_FLATS_RANGE_MM),
                "head_height_mm": HEAD_HEIGHT_MM,
                "Lb_mm": LB_MM,
                "Lg_mm": LG_MM,
            },
            "nut": {
                "sku": "25CNFH5Z",
                "thread_designation": "1/4-20 UNC; catalog class 2B",
                "across_corners_mm": NUT_ACROSS_CORNERS_MM,
                "derived_across_flats_mm": round(
                    NUT_ACROSS_CORNERS_MM * math.sqrt(3.0) / 2, 9
                ),
                "across_flats_source_range_mm": list(NUT_ACROSS_FLATS_RANGE_MM),
                "modeled_thickness_mm": NUT_THICKNESS_MM,
                "catalog_thickness_range_mm": [5.3848, 5.7404],
                "smooth_basic_reference_bore_mm": NUT_BORE_BASIC_MM,
                "bore_is_not_a_received_thread_measurement": True,
            },
            "each_of_two_washers_per_bolt": {
                "candidate": "1/4-in Type A Wide plain steel washer; seller SKU unselected",
                "outside_diameter_mm": WASHER_OD_MM,
                "inside_diameter_mm": WASHER_ID_MM,
                "thickness_mm": WASHER_THICKNESS_MM,
                "source_dimension_ranges": {
                    "outside_diameter_mm": [18.4658, 19.0246],
                    "inside_diameter_mm": [7.7978, 8.3058],
                    "thickness_mm": [1.2954, 2.032],
                },
            },
            "dimension_choice": (
                "Published catalog upper bounds for head, washer, nut, and body "
                "dimensions; 152.4 mm nominal bolt length. Geometric scenario only, "
                "not receipt or conformity evidence."
            ),
            "regular_hex_pairing": (
                "Across-corners selected within source limit; across-flats derived "
                "as AC*sqrt(3)/2 and checked inside source AF range."
            ),
        },
        "thread_reference": NBS_THREAD_REFERENCE,
        "thread_and_gage_mapping": {
            "Lb_mm_from_underhead": LB_MM,
            "Lb_semantics": "minimum body to last thread scratch; not first full-form thread",
            "Lg_mm_from_underhead": LG_MM,
            "Lg_semantics": "maximum grip-gaging criterion; not delivered thread start",
            "thread_transition_observed": False,
            "full_form_thread_or_runout_modeled": False,
            "helical_profile_modeled": False,
            "root_sensitivity_diameter_mm": THREAD_ROOT_BASIC_MM,
            "nut_bore_basic_reference_mm": NUT_BORE_BASIC_MM,
            "root_values_are_manufacturing_limits": False,
        },
        "material_scenario": {
            "wood": {
                "scenario": "DF-L No. 2 mean-E_L orthotropic implementation input proposal",
                "source_path": str(WOOD_MATERIAL_SCENARIO_PATH.relative_to(ROOT)),
                "source_sha256": FROZEN_WOOD_MATERIAL_SCENARIO_SHA256,
                "material_constants_assigned_to_mesh": False,
            },
            "steel": {
                "model": "isotropic linear elastic scenario",
                "E_MPa": STEEL_E_MPA,
                "poisson_ratio": STEEL_NU,
                "status": "explicit analysis assumption; not a catalog or measured material value",
                "yield_or_ultimate_strength_used": False,
                "plating_layer_modeled": False,
            },
        },
        "seat_and_stability_contract": {
            **clearances,
            "head_bolt_continuity": "head and stepped shank are one CAD solid",
            "washer_solids": "separate physical solids; no tie to bolt or wood",
            "nut_solid": "separate hollow hex physical solid",
            "root_nut_tie": "named projected no-slip engagement idealization only",
            "unconstrained_rigid_modes_unresolved": True,
            "possible_free_modes": [
                "washer radial translation before bearing contact",
                "bolt lateral translation within wood-axis clearance",
                "bolt and washer spin about the fastener axis",
                "zero-preload rigid-body modes before seats close",
            ],
            "native_deck_stability_proven": False,
            "future_stabilization_reaction_and_energy_audit_required": True,
            "no_artificial_clearance_closure_or_wood_washer_tie": True,
        },
        "legacy_collision_role_metadata": _legacy_collision_roles(
            inputs.patch_inventory
        ),
        "scenarios": scenarios_report,
        "claim_boundary": [
            "The forty archived CAD roles are collision-envelope metadata, not physical steel solids.",
            "Each response scenario has eight 6-inch candidate bolts, two washers and one nut each; no 8-inch WJ06 stacks are included.",
            "Projected nut engagement is an explicit no-slip tie assumption across the selected basic-reference clearance; full nut-thickness engagement is not observed.",
            "No seat preload, friction, local thread stress, bolt capacity, wood capacity, stable model, actual received part, tool access or installation claim is established.",
        ],
    }
    return BuiltHardware(report=report, shapes=shapes)


def _step_symmetric_difference(
    source: cq.Shape, readback: cq.Shape, context: str
) -> dict[str, Any]:
    try:
        source_only = max(0.0, float(source.cut(readback).Volume()))
        step_only = max(0.0, float(readback.cut(source).Volume()))
    except Exception as error:
        raise ValueError(f"{context}: CAD STEP occupancy comparison failed") from error
    total = source_only + step_only
    allowed = SYMMETRIC_DIFFERENCE_ABS_TOLERANCE_MM3 + (
        SYMMETRIC_DIFFERENCE_REL_TOLERANCE * max(source.Volume(), readback.Volume())
    )
    if not all(math.isfinite(value) for value in (total, allowed)):
        raise ValueError(f"{context}: non-finite STEP occupancy comparison")
    evidence = {
        "source_only_volume_mm3": round(source_only, 12),
        "step_only_volume_mm3": round(step_only, 12),
        "symmetric_difference_volume_mm3": round(total, 12),
        "allowed_volume_difference_mm3": round(allowed, 12),
        "absolute_tolerance_mm3": SYMMETRIC_DIFFERENCE_ABS_TOLERANCE_MM3,
        "relative_tolerance": SYMMETRIC_DIFFERENCE_REL_TOLERANCE,
        "passed": total <= allowed,
    }
    if not evidence["passed"]:
        raise ValueError(f"{context}: STEP solid differs from its generated source")
    return evidence


def _write_step_solid(shape: cq.Shape, path: Path, context: str) -> dict[str, Any]:
    source = _shape_metadata(shape, f"{context} source")
    cq.exporters.export(shape, str(path))
    if not path.is_file() or path.stat().st_size == 0:
        raise ValueError(f"{context}: STEP writer produced no file")
    imported = cq.importers.importStep(str(path)).val()
    readback = _shape_metadata(imported, f"{context} STEP readback")
    if readback["solid_count"] != 1:
        raise ValueError(f"{context}: STEP readback changed the solid count")
    if not math.isclose(
        source["volume_mm3"],
        readback["volume_mm3"],
        rel_tol=1e-9,
        abs_tol=1e-5,
    ):
        raise ValueError(f"{context}: STEP readback volume differs")
    if not _close_vec(
        source["centroid_global_xyz_mm"], readback["centroid_global_xyz_mm"]
    ):
        raise ValueError(f"{context}: STEP readback centroid differs")
    if any(
        abs(float(left) - float(right)) > METADATA_TOLERANCE_MM
        for left, right in zip(
            source["bounds_xyz_mm"], readback["bounds_xyz_mm"], strict=True
        )
    ):
        raise ValueError(f"{context}: STEP readback bounds differ")
    difference = _step_symmetric_difference(shape, imported, context)
    return {
        "file_sha256": _sha256_file(path),
        "source_solid": source,
        "step_readback_solid": readback,
        "identity_checks": {
            "solid_count": True,
            "volume": True,
            "centroid": True,
            "bounds": True,
            "symmetric_difference": difference,
            "face_ordinal_used": False,
        },
    }


def export_hardware_contract(output_dir: str | Path) -> dict[str, Any]:
    """Export both conditional scenarios to a new directory; no model solve."""
    target = Path(output_dir).expanduser().absolute()
    if target.exists() or target.is_symlink():
        raise FileExistsError(f"mechanics hardware output already exists: {target}")
    frozen_before = load_frozen_inputs()
    built = build_hardware_contract(frozen_before)
    target.parent.mkdir(parents=True, exist_ok=True)
    staging = Path(
        tempfile.mkdtemp(prefix=f".{target.name}.stage-", dir=str(target.parent))
    )
    try:
        artifacts: dict[str, dict[str, Any]] = {}
        for key, shape in sorted(built.shapes.items()):
            scenario_id, stack_id, role = key.split("/", 2)
            relative = Path("hardware") / scenario_id / stack_id / f"{role}.step"
            destination = staging / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            artifacts[relative.as_posix()] = _write_step_solid(shape, destination, key)
        built.report["step_artifacts"] = artifacts
        built.report["step_export_contract"] = {
            "step_files": len(artifacts),
            "independent_single_solid_files": True,
            "physical_solids_per_scenario": 32,
            "readback_identity": "volume, centroid, bounds and bidirectional solid difference",
            "symmetric_difference_abs_tolerance_mm3": SYMMETRIC_DIFFERENCE_ABS_TOLERANCE_MM3,
            "symmetric_difference_rel_tolerance": SYMMETRIC_DIFFERENCE_REL_TOLERANCE,
        }
        reference_bytes = _json_bytes(NBS_THREAD_REFERENCE)
        reference_relative = "references/nbs-unified-thread-table2-excerpt.json"
        reference_path = staging / reference_relative
        reference_path.parent.mkdir(parents=True, exist_ok=True)
        reference_path.write_bytes(reference_bytes)
        report_bytes = _json_bytes(built.report)
        (staging / "inventory.json").write_bytes(report_bytes)
        artifact_hashes = {
            "inventory.json": _sha256_bytes(report_bytes),
            reference_relative: _sha256_bytes(reference_bytes),
            **{name: record["file_sha256"] for name, record in artifacts.items()},
        }
        hashes_bytes = _json_bytes(artifact_hashes)
        (staging / "sha256.json").write_bytes(hashes_bytes)
        # Recheck frozen sources after CAD construction/export before publishing.
        frozen_after = load_frozen_inputs()
        if frozen_after.input_hashes != frozen_before.input_hashes:
            raise ValueError(
                "one or more frozen hardware geometry inputs changed during export"
            )
        if target.exists() or target.is_symlink():
            raise FileExistsError(f"output directory appeared during export: {target}")
        os.replace(staging, target)
    except Exception:
        shutil.rmtree(staging, ignore_errors=True)
        raise
    return {
        "output_dir": str(target),
        "inventory_path": str(target / "inventory.json"),
        "inventory_sha256": _sha256_file(target / "inventory.json"),
        "sha256_path": str(target / "sha256.json"),
        "step_files": 64,
        "physical_solids_per_scenario": 32,
        "status": built.report["status"],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--out", required=True, help="new, non-existing output directory"
    )
    args = parser.parse_args()
    print(json.dumps(export_hardware_contract(args.out), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
