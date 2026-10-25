#!/usr/bin/env python3
"""Assess selected112 NDS group-action applicability without assigning Cg.

The script inventories source-defined fastener-row roles and review-scope
wrenches from the admitted selected112 bank.  It calls the existing NDS group
action evaluator only on the published Caltrans Appendix D Example12 software
benchmark.  MoonBoard row records stay unresolved unless a future, independent
source package establishes every applicability input.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
from collections import defaultdict
from dataclasses import asdict
from pathlib import Path
from typing import Any

from mini_moonboard.serial_row_benchmark import compare_serial_row_to_nds

ROOT = Path(__file__).resolve().parents[1]
PACKET = Path("fea/generated/v10-packer-free-v1")
BASE = PACKET / "mechanics/analysis-v2"
CASE_IDS = ("a12-forward", "a12-left", "a12-rear", "k12-right", "k12-rear", "a1-rear")

SOURCE_PATHS = {
    "response_bank": PACKET / "mechanics/analysis-v2/response-bank.json",
    "prepared_inputs": PACKET / "mechanics/analysis-v2/preparation/inputs.json",
    "analysis_geometry": PACKET / "mechanics/analysis-v2/geometry/geometry.json",
    "physical_geometry": PACKET / "geometry-v1/geometry.json",
    "checked_receipt": PACKET / "geometry-v1/checked-receipt-v1.json",
    "component_graph": Path(
        "fea/generated/v10-packer-free-center-far-row-v1/connections/"
        "method-closure/subassembly-ownership/local-hardware-cleat-component-graph-v1.json"
    ),
    "boundary_wrenches": PACKET
    / "connections/method-closure/local-subassemblies/"
    / "current112-local-subassembly-boundary-wrenches-v1.json",
    "legacy_evaluation": Path(
        "docs/bolted-frame-development/owner-frame-v10/packer-free/evaluation.json"
    ),
    "owner_work_packet": Path(
        "docs/bolted-frame-development/owner-frame-v10/standard-top-stock/"
        "group-effects-replacement-work-packet-v1.txt"
    ),
    "plywood_material": BASE / "material.json",
    "nds_chapter_11": Path(
        "docs/wood-joints-mvp/hypotheses/upper-block-strength-2026-10-01/"
        "source-cache/chapter11-2024-awc-20260911.pdf"
    ),
    "nds_chapter_12": Path(
        "docs/wood-joints-mvp/hypotheses/upper-block-strength-2026-10-01/"
        "source-cache/chapter12-2024-awc-20260911.pdf"
    ),
    "primary_method_closure": Path(
        "docs/bolted-frame-development/owner-frame-v10/packer-free/primary-method-closure.json"
    ),
    "nds_evaluator": Path("mini_moonboard/nds_2024_group_action.py"),
    "serial_row_benchmark": Path("mini_moonboard/serial_row_benchmark.py"),
}

EXPECTED_SOURCE_SHA256 = {
    "response_bank": "976ee8d8ac593f978edf03d9eda028755751fd69b540fb8a01cdd073a242bdc3",
    "prepared_inputs": "1327366f48b68fe385de3dca117c043b44d930ea61d3cfae991c12d2cc89bec9",
    "analysis_geometry": "f187592684eab07c0c17cbf8e835452cb5ebf431510ce8aa8ffe38940807da21",
    "physical_geometry": "9510653b41d2c0c710f4eea02c9867c44367cd2909d6b3af56716c74cfd68bde",
    "checked_receipt": "73b097d9bcc364748ca08f897fca38cc2bdb7869cc04586e6706afb9b9d3d527",
    "component_graph": "d04161605cdbaef3b495b603a051a37cd28353134d0c4ef77f2a79be9d4b7003",
    "boundary_wrenches": "04b437ed42fa18a4bb04b338228eaf5af4dc8f6ec6383a45ed4529a22fd8fc64",
    "legacy_evaluation": "41863a95230b64a67f3b8aeffd6874fcf75cb81891b4872459d0bd7bb87f4017",
    "owner_work_packet": "0584b2ce59f9e66c20d1c09ce0a1c7d3053eb0923263affbb37d68f8d9202961",
    "plywood_material": "0a9829f9d5403639665049f33a2af46377409b5d4c2cad7c9b368c1c493ea51a",
    "nds_chapter_11": "45a3d78de1a4fba573589be0fc776e37bd581e4cedec24e38d63856161092d33",
    "nds_chapter_12": "53f6ec05dfd1ceabeccd4d6e88c342111678d3da4631ee7b482b706f77c1780f",
    "primary_method_closure": "99ec1cb8685c35611c6b4c4b93d9ea30741977048beb6e0cb140eef01f575ca0",
    "nds_evaluator": "121ec9d5399aa3e856b4038232e6d61c628aac42ce2addf8d1ff7e3a0e4c3df9",
    "serial_row_benchmark": "f6118e2d96fbebcb33b5d6f843edb02c4c7891bf6ec794215c4aa1b15c9c7d2e",
}

DEFAULT_OUTPUT = (
    PACKET / "connections/method-closure/group-effects/assessment-v1.json"
)
EXPECTED_CASE_IDS = list(CASE_IDS)
ROW_ROLE_KEYS = ("duty_id", "angle_id", "flange", "row", "receiver", "receivers")
ZERO_TOL = 1.0e-10


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _canonical_sha256(value: Any) -> str:
    data = json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False
    ).encode("utf-8")
    return hashlib.sha256(data).hexdigest()


def validate_sha256_map(
    actual: dict[str, str], expected: dict[str, str]
) -> None:
    """Fail closed on missing or changed source pins."""
    missing = sorted(set(expected) - set(actual))
    changed = sorted(
        key for key, digest in expected.items() if actual.get(key) != digest
    )
    if missing or changed:
        raise ValueError(f"source pin mismatch; missing={missing}, changed={changed}")


def _read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise TypeError(f"expected a JSON object: {path}")
    return value


def load_bound_sources(root: Path = ROOT) -> tuple[dict[str, Any], dict[str, str]]:
    refs: dict[str, str] = {}
    documents: dict[str, Any] = {}
    for name, relative in SOURCE_PATHS.items():
        path = root / relative
        if not path.is_file():
            raise ValueError(f"required bound source is missing: {path}")
        refs[name] = sha256_file(path)
        documents[name] = (
            None
            if name
            in {
                "nds_chapter_11",
                "nds_chapter_12",
                "nds_evaluator",
                "serial_row_benchmark",
                "owner_work_packet",
            }
            else _read_json(path)
        )
    validate_sha256_map(refs, EXPECTED_SOURCE_SHA256)
    return documents, refs


def _unit(vector: list[float] | tuple[float, ...]) -> list[float] | None:
    if len(vector) != 3 or not all(math.isfinite(float(v)) for v in vector):
        return None
    norm = math.hypot(*(float(v) for v in vector))
    if norm <= ZERO_TOL:
        return None
    return [float(v) / norm for v in vector]


def _sub(left: list[float], right: list[float]) -> list[float]:
    return [a - b for a, b in zip(left, right, strict=True)]


def _dot(left: list[float], right: list[float]) -> float:
    return sum(a * b for a, b in zip(left, right, strict=True))


def _norm(vector: list[float]) -> float:
    return math.hypot(*(float(value) for value in vector))


def _cross(left: list[float], right: list[float]) -> list[float]:
    return [
        left[1] * right[2] - left[2] * right[1],
        left[2] * right[0] - left[0] * right[2],
        left[0] * right[1] - left[1] * right[0],
    ]


def _canonical_axis(vector: list[float]) -> list[float] | None:
    result = _unit(vector)
    if result is None:
        return None
    for value in result:
        if abs(value) > ZERO_TOL:
            return [-component for component in result] if value < 0 else result
    return result


def _role_key(attachment: dict[str, Any]) -> tuple[str, ...]:
    return tuple(
        json.dumps(attachment.get(key), sort_keys=True, separators=(",", ":"))
        for key in ROW_ROLE_KEYS
    )


def _member_operator_reference(
    host: str,
    timber_by_name: dict[str, dict[str, Any]],
    wood_e_mpa: float,
    plywood_material: dict[str, Any],
) -> dict[str, Any]:
    row = timber_by_name.get(host)
    if row is None:
        return {
            "gross_FE_axial_EA_reference": None,
            "effective_NDS_group_EA_N": None,
            "status": "unresolved_member_section_source",
        }
    if host.startswith("eoere_cleat_"):
        return {
            "gross_FE_axial_EA_reference": {
                "value": plywood_material.get("properties", {}).get("EA_N"),
                "unit": "N",
                "source": "bound plywood operator material.json#/properties/EA_N",
                "qualification": (
                    "nominal two-leaf perfect-bond, full-width beam operator property; "
                    "direction-specific and physical laminate response are not qualified"
                ),
            },
            "effective_NDS_group_EA_N": None,
            "status": "gross_operator_reference_only",
        }
    area_mm2 = float(row["width_mm"]) * float(row["depth_mm"])
    return {
        "gross_FE_axial_EA_reference": {
            "value": wood_e_mpa * area_mm2,
            "unit": "N",
            "area_mm2": area_mm2,
            "E_mpa": wood_e_mpa,
            "source": "bound prepared inputs: timber_rows width/depth × scenario.timber_e_mpa",
            "qualification": "gross raw-stock Timoshenko model reference, not effective NDS row EA",
        },
        "effective_NDS_group_EA_N": None,
        "status": "gross_operator_reference_only",
    }


def _surface_membership(
    shaft: dict[str, Any],
    timber_by_name: dict[str, dict[str, Any]],
    wood_e_mpa: float,
    plywood_material: dict[str, Any],
) -> list[dict[str, Any]]:
    surfaces = shaft.get("surfaces")
    if not isinstance(surfaces, list):
        return []
    result = []
    for surface in sorted(
        surfaces,
        key=lambda item: (
            float(item.get("interval_mm", [0.0, 0.0])[0]),
            str(item.get("host", "")),
        ),
    ):
        host = str(surface.get("host", ""))
        result.append(
            {
                "host_body_id": host,
                "kind": surface.get("kind"),
                "interval_along_shaft_mm": surface.get("interval_mm"),
                "bore_diameter_mm": surface.get("bore_diameter_mm"),
                "grain_axis_world_xyz": surface.get("grain_axis_xyz"),
                "steel_receiver": surface.get("receiver"),
                "source_axis_id": surface.get("source_axis_id"),
                "member_operator_reference": _member_operator_reference(
                    host, timber_by_name, wood_e_mpa, plywood_material
                )
                if surface.get("kind") == "wood"
                else None,
            }
        )
    return result


def build_physical_row_roles(
    inputs: dict[str, Any],
    hardware_components: list[dict[str, Any]],
    plywood_material: dict[str, Any],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Build source-defined flange-row roles and retain axes without row metadata."""
    shafts = inputs.get("shafts")
    if not isinstance(shafts, list):
        raise TypeError("prepared inputs do not contain the selected shaft inventory")
    shaft_by_id = {str(row.get("axis_id")): row for row in shafts}
    if len(shaft_by_id) != len(shafts):
        raise ValueError("duplicate prepared shaft axis id")
    axis_component: dict[str, str] = {}
    for component in hardware_components:
        for axis_id in component.get("axis_ids", []):
            if axis_id in axis_component:
                raise ValueError(f"hardware graph repeats shaft axis: {axis_id}")
            axis_component[axis_id] = component["component_id"]

    timber_by_name = {
        str(row["name"]): row
        for row in inputs.get("timber_rows", [])
        if isinstance(row, dict) and isinstance(row.get("name"), str)
    }
    wood_e_mpa = float(inputs.get("scenario", {}).get("timber_e_mpa", 0.0))
    groups: dict[tuple[str, ...], list[tuple[str, dict[str, Any]]]] = defaultdict(list)
    unclassified: list[dict[str, Any]] = []
    for axis_id, shaft in shaft_by_id.items():
        if axis_id not in axis_component:
            continue
        source_axis = shaft.get("source_axis", {})
        attachments = source_axis.get("attachments", [])
        if not isinstance(attachments, list):
            raise TypeError(f"malformed attachment rows for {axis_id}")
        if not attachments:
            unclassified.append(
                {
                    "axis_id": axis_id,
                    "shaft_body_id": shaft.get("body"),
                    "review_component_id": axis_component[axis_id],
                    "diameter_mm": shaft.get("diameter_mm"),
                    "source_axis_direction_xyz": source_axis.get("direction_xyz"),
                    "surface_stack": _surface_membership(
                        shaft, timber_by_name, wood_e_mpa, plywood_material
                    ),
                    "row_identity_status": "UNRESOLVED_NO_SOURCE_ATTACHMENT_ROW",
                    "row_ownership_note": (
                        "No source attachment role is emitted for this shaft. Preserve its "
                        "actual wood/steel surface stack; do not infer a row from proximity alone."
                    ),
                }
            )
            continue
        for attachment in attachments:
            if not isinstance(attachment, dict):
                raise TypeError(f"malformed source attachment for {axis_id}")
            groups[_role_key(attachment)].append((axis_id, attachment))

    rows: list[dict[str, Any]] = []
    for role_key, members in sorted(groups.items()):
        first_attachment = members[0][1]
        axes = [axis_id for axis_id, _ in members]
        if len(set(axes)) != len(axes):
            raise ValueError(f"duplicate shaft in source row role {role_key}")
        component_ids = sorted({axis_component.get(axis_id, "") for axis_id in axes})
        centers: dict[str, list[float]] = {}
        shaft_directions: dict[str, list[float] | None] = {}
        axis_records = []
        diameters = []
        for axis_id, attachment in members:
            shaft = shaft_by_id[axis_id]
            source_axis = shaft.get("source_axis", {})
            point = source_axis.get("point_xyz_mm") or shaft.get("point")
            if not isinstance(point, list) or len(point) != 3:
                raise ValueError(f"missing world shaft point for {axis_id}")
            centers[axis_id] = [float(value) for value in point]
            shaft_directions[axis_id] = _unit(
                source_axis.get("direction_xyz", shaft.get("basis", [[None]])[0])
            )
            diameters.append(float(shaft["diameter_mm"]))
            axis_records.append(
                {
                    "axis_id": axis_id,
                    "shaft_body_id": shaft.get("body"),
                    "center_xyz_mm": centers[axis_id],
                    "shaft_direction_xyz": shaft_directions[axis_id],
                    "diameter_mm": shaft.get("diameter_mm"),
                    "bore_diameter_mm": shaft.get("bore_diameter_mm"),
                    "source_attachment": attachment,
                    "surface_stack": _surface_membership(
                        shaft, timber_by_name, wood_e_mpa, plywood_material
                    ),
                }
            )
        row_axis = None
        pitch_mm = None
        straightness_error_mm = None
        if len(axes) >= 2:
            first, second = centers[axes[0]], centers[axes[1]]
            row_axis = _canonical_axis(_sub(second, first))
            if row_axis is not None:
                projections = sorted(
                    _dot(_sub(centers[axis_id], first), row_axis) for axis_id in axes
                )
                pitches = [
                    projections[index + 1] - projections[index]
                    for index in range(len(projections) - 1)
                ]
                pitch_mm = pitches[0] if pitches and all(
                    math.isclose(value, pitches[0], rel_tol=0.0, abs_tol=1e-7)
                    for value in pitches
                ) else None
                straightness_error_mm = max(
                    _norm(
                        _sub(
                            _sub(centers[axis_id], first),
                            [
                                _dot(_sub(centers[axis_id], first), row_axis) * value
                                for value in row_axis
                            ],
                        )
                    )
                    for axis_id in axes
                )
                axis_records.sort(
                    key=lambda record: _dot(
                        _sub(record["center_xyz_mm"], first), row_axis
                    )
                )
        row_id = "row-role:" + ":".join(
            str(first_attachment.get(key) or "none") for key in ROW_ROLE_KEYS[:4]
        ) + ":" + "+".join(str(x) for x in sorted(set(axes)))
        wood_hosts = sorted(
            {
                surface["host_body_id"]
                for record in axis_records
                for surface in record["surface_stack"]
                if surface.get("kind") == "wood"
            }
        )
        all_grains = [
            surface["grain_axis_world_xyz"]
            for record in axis_records
            for surface in record["surface_stack"]
            if surface.get("kind") == "wood"
            and surface.get("grain_axis_world_xyz") is not None
        ]
        grain_angles = []
        if row_axis is not None:
            for grain in all_grains:
                unit_grain = _unit(grain)
                if unit_grain is not None:
                    grain_angles.append(
                        math.degrees(
                            math.acos(min(1.0, max(0.0, abs(_dot(row_axis, unit_grain)))))
                        )
                    )
        reasons = [
            "the attachment role is a geometry grouping, not an established NDS group",
            "effective member EA and NDS-equivalent serial row slip are not source-qualified",
            "the prepared FE uses distributed shaft foundations and interpolated beam ports; NDS-equivalent load-sharing calibration is absent",
            "the six-case local force directions and signed moments do not establish a single force-only NDS group action",
            "a group-action factor would not replace joint capacity, net-section, splitting, fitting, or complete-interaction checks",
        ]
        if any(
            surface.get("kind") == "steel"
            for record in axis_records
            for surface in record["surface_stack"]
        ):
            reasons.append("the row role includes a steel flange interface outside the evaluator's wood-to-wood scope")
        if len(wood_hosts) > 1:
            reasons.append("the fastener path crosses more than one wood receiver or a laminated cleat layer")
        if len(component_ids) != 1:
            reasons.append("the row-role axes do not map to one review component")
        if len(axes) < 2:
            reasons.append("the source-defined attachment role has fewer than two fasteners")
        rows.append(
            {
                "row_id": row_id,
                "row_identity_source": "prepared_inputs.json#/shafts/*/source_axis/attachments",
                "review_component_ids": component_ids,
                "attachment_role": {key: first_attachment.get(key) for key in ROW_ROLE_KEYS},
                "fastener_axis_count": len(axes),
                "fastener_axes": axis_records,
                "row_axis_world_xyz": row_axis,
                "row_basis_units": {"coordinate_frame": "world XYZ", "length": "mm"},
                "uniform_pitch_mm": pitch_mm,
                "row_straightness_error_mm": straightness_error_mm,
                "nominal_fastener_diameter_mm": diameters[0] if len(set(diameters)) == 1 else None,
                "diameter_uniform": len(set(diameters)) == 1,
                "wood_member_body_ids": wood_hosts,
                "row_axis_to_wood_grain_angles_deg": grain_angles,
                "grain_angle_interpretation": (
                    "geometric angle between source row axis and listed wood grain axes; "
                    "not a classification of the actual lateral load direction"
                ),
                "NDS_shear_plane_count": None,
                "NDS_effective_member_EA_N": None,
                "NDS_effective_slip_modulus_N_per_mm": None,
                "formula_gamma_sensitivity_only": (
                    _formula_gamma(diameters[0])
                    if len(set(diameters)) == 1 and len(axes) >= 2
                    else None
                ),
                "six_case_NDS_lateral_resultant_xyz_N": None,
                "actual_Cg": None,
                "complete_Cdelta": None,
                "capacity": None,
                "applicability_status": "UNRESOLVED",
                "reason_codes": reasons,
                "case_action_refs": [],
            }
        )
    return rows, unclassified


def _formula_gamma(diameter_mm: float) -> dict[str, Any]:
    diameter_in = diameter_mm / 25.4
    gamma = 180_000.0 * diameter_in**1.5
    return {
        "value": gamma,
        "unit": "lbf/in",
        "formula": "180000 * nominal_diameter_in**1.5",
        "nominal_diameter_in": diameter_in,
        "status": "formula scenario only; not measured or calibrated current FE slip",
        "source": "NDS-2024 Eq. 11.3-1 input; see bound Chapter 12 source",
    }


def _negate_wrench(wrench: dict[str, Any]) -> dict[str, Any]:
    result = dict(wrench)
    for key in ("force_xyz_n", "moment_about_global_origin_xyz_nmm"):
        if key in result:
            result[key] = [-float(value) for value in result[key]]
    return result


def _case_component_wrenches(
    case_record: dict[str, Any],
    source_path: str,
    source_sha256: str,
    case_index: int,
    source_component_index: int | None = None,
) -> list[dict[str, Any]]:
    results = []
    for local_component_index, component in enumerate(
        case_record.get("hardware_cleat_components", [])
    ):
        component_index = (
            source_component_index
            if source_component_index is not None
            else local_component_index
        )
        body_id = component["component_id"]
        point_action_references = {"boundary_ports": [], "internal_actions": []}
        for family, references in point_action_references.items():
            for action_index, action in enumerate(component.get(family, [])):
                sides = action.get("sides", [])
                references.append(
                    {
                        "source_family": action.get("source_family"),
                        "source_id": action.get("source_id"),
                        "kind": action.get("kind"),
                        "axis_id": action.get("axis_id"),
                        "component_body": action.get("component_body"),
                        "external_body": action.get("external_body"),
                        "side_body_ids": [side.get("body") for side in sides],
                        "json_pointer": (
                            f"/cases/{case_index}/hardware_cleat_components/"
                            f"{component_index}/{family}/{action_index}"
                        ),
                    }
                )
        result = {
            "case_id": case_record["case_id"],
            "component_id": body_id,
            "body_load_wrench_about_global_origin": component.get(
                "body_load_wrench_about_global_origin"
            ),
            "external_boundary_wrench_on_component_about_global_origin": component.get(
                "external_boundary_wrench_on_component_about_global_origin"
            ),
            "boundary_port_wrench_totals": [],
            "internal_action_wrench_net_about_global_origin": component.get(
                "internal_action_wrench_net_about_global_origin"
            ),
            "reconstructed_component_balance_about_global_origin": component.get(
                "reconstructed_component_balance_about_global_origin"
            ),
            "saved_component_residual_corrected_to_global_origin": component.get(
                "saved_component_residual_corrected_to_global_origin"
            ),
            "reconstructed_minus_corrected_saved_residual": component.get(
                "reconstructed_minus_corrected_saved_residual"
            ),
            "source_action_counts_by_family": component.get("source_action_counts_by_family"),
            "full_signed_point_action_source": {
                "path": source_path,
                "sha256": source_sha256,
                "json_pointer": f"/cases/{case_index}/hardware_cleat_components/{component_index}",
                "note": "Exact point actions and free couples remain in this frozen source record.",
            },
            "signed_point_action_references": point_action_references,
        }
        for total in component.get("boundary_port_wrench_totals", []):
            result["boundary_port_wrench_totals"].append(
                {
                    **total,
                    "wrench_on_receiver": _negate_wrench(total["wrench_on_component"]),
                    "wrench_on_component": total["wrench_on_component"],
                }
            )
        results.append(result)
    return results


def _row_case_action_refs(
    row: dict[str, Any], component_case: dict[str, Any]
) -> dict[str, Any]:
    axis_ids = {record["axis_id"] for record in row["fastener_axes"]}
    receiver_ids = set(row["attachment_role"].get("receivers") or [])
    if row["attachment_role"].get("receiver"):
        receiver_ids.add(row["attachment_role"]["receiver"])
    selected = []
    for total in component_case["boundary_port_wrench_totals"]:
        body = total.get("component_body", "")
        axis_id = body.removeprefix("shaft/") if body.startswith("shaft/") else None
        if axis_id in axis_ids and total.get("external_body") in receiver_ids:
            selected.append(
                {
                    "axis_id": axis_id,
                    "receiver_body_id": total["external_body"],
                    "source_family": total["source_family"],
                    "action_count": total["action_count"],
                    "force_on_receiver_xyz_N": total["wrench_on_receiver"]["force_xyz_n"],
                    "moment_on_receiver_about_global_origin_xyz_Nmm": total[
                        "wrench_on_receiver"]["moment_about_global_origin_xyz_nmm"],
                    "full_local_action_source": component_case["full_signed_point_action_source"],
                }
            )
    by_receiver: dict[str, dict[str, Any]] = {}
    for action in selected:
        receiver = action["receiver_body_id"]
        total = by_receiver.setdefault(
            receiver,
            {
                "receiver_body_id": receiver,
                "force_xyz_N": [0.0, 0.0, 0.0],
                "moment_about_global_origin_xyz_Nmm": [0.0, 0.0, 0.0],
                "axis_action_count": 0,
                "source_families": set(),
            },
        )
        for i in range(3):
            total["force_xyz_N"][i] += action["force_on_receiver_xyz_N"][i]
            total["moment_about_global_origin_xyz_Nmm"][i] += action[
                "moment_on_receiver_about_global_origin_xyz_Nmm"
            ][i]
        total["axis_action_count"] += action["action_count"]
        total["source_families"].add(action["source_family"])
    clean_totals = []
    for total in by_receiver.values():
        force = total["force_xyz_N"]
        force_norm = _norm(force)
        clean_totals.append(
            {
                **total,
                "resultant_direction_xyz": [value / force_norm for value in force]
                if force_norm > ZERO_TOL
                else None,
                "source_families": sorted(total["source_families"]),
                "interpretation": (
                    "signed sum of this row-role's receiver boundary actions only; "
                    "not an independent NDS force-only group action"
                ),
            }
        )
    row_point_action_refs = {"boundary_ports": [], "internal_actions": []}
    for family, refs in component_case.get(
        "signed_point_action_references", {"boundary_ports": [], "internal_actions": []}
    ).items():
        for reference in refs:
            axis_id = reference.get("axis_id")
            if axis_id is None:
                source_id = str(reference.get("source_id", ""))
                axis_id = next(
                    (
                        axis
                        for axis in axis_ids
                        if source_id.startswith(f"{axis}/")
                    ),
                    None,
                )
            matches_receiver = (
                reference.get("external_body") in receiver_ids
                or bool(receiver_ids.intersection(reference.get("side_body_ids", [])))
            )
            if axis_id in axis_ids and matches_receiver:
                row_point_action_refs[family].append(reference)
    return {
        "case_id": component_case["case_id"],
        "receiver_wrenches": clean_totals,
        "signed_axis_receiver_wrench_rows": selected,
        "signed_point_action_references": row_point_action_refs,
        "missing_or_internal_receivers": sorted(receiver_ids - set(by_receiver)),
        "component_case_wrench_ref": component_case["full_signed_point_action_source"],
    }


def _wrench_from_action_side(side: dict[str, Any]) -> dict[str, Any]:
    force = [float(value) for value in side["force"]]
    point = [float(value) for value in side["point"]]
    couple = [float(value) for value in side.get("couple", [0.0, 0.0, 0.0])]
    moment = [
        a + b
        for a, b in zip(_cross(point, force), couple, strict=True)
    ]
    return {
        "force_xyz_N": force,
        "free_couple_at_point_xyz_Nmm": couple,
        "moment_about_global_origin_xyz_Nmm": moment,
    }


def build_wood_only_geometry_descriptors(
    inputs: dict[str, Any],
    graph_scopes: list[dict[str, Any]],
    wrench_cases: list[dict[str, Any]],
    plywood_material: dict[str, Any],
    wrench_path: str,
    wrench_sha: str,
) -> list[dict[str, Any]]:
    """Expose the six graph scopes' actual axis and two-receiver geometry."""
    shaft_by_id = {row["axis_id"]: row for row in inputs["shafts"]}
    timber_by_name = {row["name"]: row for row in inputs["timber_rows"]}
    wood_e_mpa = float(inputs["scenario"]["timber_e_mpa"])
    case_by_id = {row["case_id"]: row for row in wrench_cases}
    output = []
    for scope in graph_scopes:
        axis_rows = []
        centers: dict[str, list[float]] = {}
        for axis_id in scope["axis_ids"]:
            shaft = shaft_by_id[axis_id]
            source_axis = shaft["source_axis"]
            point = source_axis.get("point_xyz_mm") or shaft.get("point")
            centers[axis_id] = [float(value) for value in point]
            axis_rows.append(
                {
                    "axis_id": axis_id,
                    "shaft_body_id": shaft["body"],
                    "center_xyz_mm": centers[axis_id],
                    "shaft_direction_xyz": source_axis.get("direction_xyz"),
                    "diameter_mm": shaft["diameter_mm"],
                    "bore_diameter_mm": shaft["bore_diameter_mm"],
                    "surface_stack": _surface_membership(
                        shaft, timber_by_name, wood_e_mpa, plywood_material
                    ),
                }
            )
        pair_axis = None
        spacing_mm = None
        straightness_error_mm = None
        if len(axis_rows) >= 2:
            first_id, second_id = scope["axis_ids"][:2]
            delta = _sub(centers[second_id], centers[first_id])
            pair_axis = _canonical_axis(delta)
            if pair_axis is not None:
                spacing_mm = _norm(delta)
                first_direction = _unit(axis_rows[0]["shaft_direction_xyz"] or [])
                second_direction = _unit(axis_rows[1]["shaft_direction_xyz"] or [])
                if first_direction and second_direction:
                    alignment = abs(_dot(first_direction, second_direction))
                    row_plane_cosine = abs(_dot(pair_axis, first_direction))
                    if alignment < 1.0 - 1.0e-8 or row_plane_cosine > 1.0e-8:
                        straightness_error_mm = None
                    else:
                        straightness_error_mm = 0.0
        member_rows = []
        for host in scope["receiver_body_ids"]:
            member_surface_records = [
                {
                    "axis_id": axis["axis_id"],
                    **surface,
                }
                for axis in axis_rows
                for surface in axis["surface_stack"]
                if surface["host_body_id"] == host and surface["kind"] == "wood"
            ]
            timber = timber_by_name.get(host)
            member_rows.append(
                {
                    "member_body_id": host,
                    "source_section": {
                        "width_mm": timber.get("width_mm") if timber else None,
                        "depth_mm": timber.get("depth_mm") if timber else None,
                        "source": "prepared_inputs.json#/timber_rows by member name",
                    },
                    "gross_FE_axial_EA_reference": _member_operator_reference(
                        host, timber_by_name, wood_e_mpa, plywood_material
                    )["gross_FE_axial_EA_reference"],
                    "effective_NDS_group_EA_N": None,
                    "axis_surface_records": member_surface_records,
                }
            )
        case_results = []
        for case_id in CASE_IDS:
            matches = [
                row
                for row in case_by_id[case_id].get("wood_only_joint_scopes", [])
                if row.get("scope_id") == scope["scope_id"]
            ]
            if len(matches) != 1:
                raise ValueError(f"missing wood-only source wrenches {case_id}/{scope['scope_id']}")
            source_case = matches[0]
            receiver_sums: dict[str, dict[str, Any]] = {}
            for action in source_case.get("boundary_actions", []):
                receiver_side = action["action_on_receiver_body"]
                receiver = action["receiver_body"]
                record = _wrench_from_action_side(receiver_side)
                total = receiver_sums.setdefault(
                    receiver,
                    {
                        "force_xyz_N": [0.0, 0.0, 0.0],
                        "moment_about_global_origin_xyz_Nmm": [0.0, 0.0, 0.0],
                        "action_count": 0,
                    },
                )
                for index in range(3):
                    total["force_xyz_N"][index] += record["force_xyz_N"][index]
                    total["moment_about_global_origin_xyz_Nmm"][index] += record[
                        "moment_about_global_origin_xyz_Nmm"
                    ][index]
                total["action_count"] += 1
            for receiver, total in receiver_sums.items():
                magnitude = _norm(total["force_xyz_N"])
                total["resultant_direction_xyz"] = (
                    [value / magnitude for value in total["force_xyz_N"]]
                    if magnitude > ZERO_TOL
                    else None
                )
                total["receiver_body_id"] = receiver
            case_results.append(
                {
                    "case_id": case_id,
                    "scope_id": scope["scope_id"],
                    "receiver_resultant_wrenches": receiver_sums,
                    "source_record_ref": {
                        "path": wrench_path,
                        "sha256": wrench_sha,
                        "case_id": case_id,
                        "scope_id": scope["scope_id"],
                        "meaning": "full signed shaft/receiver action rows and local points/couples in bound collector record",
                    },
                }
            )
        output.append(
            {
                "scope_id": scope["scope_id"],
                "scope_rule": scope.get("scope_rule"),
                "geometric_candidate_row_only": True,
                "fastener_count": len(axis_rows),
                "fastener_axes": axis_rows,
                "row_axis_world_xyz": pair_axis,
                "row_spacing_mm": spacing_mm,
                "row_straightness_error_mm": straightness_error_mm,
                "member_ownership": member_rows,
                "modeled_receiver_member_count": len(scope["receiver_body_ids"]),
                "conditional_geometric_shear_plane_count": (
                    len(scope["receiver_body_ids"]) - 1
                    if len(scope["receiver_body_ids"]) == 2
                    else None
                ),
                "NDS_shear_plane_count_adopted": None,
                "effective_NDS_group_EA_N": None,
                "effective_NDS_group_slip_modulus_N_per_mm": None,
                "formula_gamma_sensitivity_only": (
                    _formula_gamma(axis_rows[0]["diameter_mm"])
                    if len(axis_rows) >= 2
                    else None
                ),
                "case_wrenches": case_results,
                "actual_Cg": None,
                "complete_Cdelta": None,
                "capacity": None,
                "applicability_status": "UNRESOLVED",
                "unresolved_reason_codes": [
                    "geometric candidate rows do not establish design group membership or bearing/slip qualification",
                    "actual NDS member EA/effective group area and connector slip are not source-qualified",
                    "the frozen FE row actions retain signed force and moment but do not establish force-only applicability or NDS-equivalent slip distribution",
                    "for single-fastener scopes the multi-fastener group-action equation is not applicable; no Cg is assigned",
                ],
            }
        )
    return output


def _build_caltrans_example12_benchmark() -> dict[str, Any]:
    result = compare_serial_row_to_nds(
        fastener_count=3,
        diameter_in=0.625,
        pitch_in=2.5,
        elastic_modulus_main_psi=1_600_000.0,
        area_main_in2=144.0,
        elastic_modulus_side_psi=1_600_000.0,
        area_side_in2=10.88,
    )
    expected_cg = 0.9806318451462117
    if not result.matches_within_tolerance or not math.isclose(
        result.nds_cg, expected_cg, rel_tol=1.0e-12
    ):
        raise ValueError("NDS group-action evaluator failed the Caltrans Example12 control")
    return {
        "status": "PASS_METHOD_BENCHMARK_ONLY",
        "source": {
            "citation": "Caltrans Falsework Manual, Appendix D, Example 12, printed D-12-4/5",
            "url": "https://dot.ca.gov/-/media/dot-media/programs/engineering/documents/structureconstruction/fw-appendixd-ex12-a11y.pdf",
            "edition_note": "Published reference example; benchmark inputs copied from the owner work packet.",
        },
        "inputs": {
            "fastener_count": 3,
            "diameter_in": 0.625,
            "pitch_in": 2.5,
            "main_E_psi": 1_600_000.0,
            "main_A_in2": 144.0,
            "side_E_psi": 1_600_000.0,
            "side_A_in2": 10.88,
            "nominal_gamma_lbf_per_in": 180_000.0 * 0.625**1.5,
        },
        "result": {
            "NDS_Cg_method_only": result.nds_cg,
            "serial_row_distribution": asdict(result.distribution),
            "distribution_Cg": result.distribution.cg_from_distribution,
            "gamma_lbf_per_in": result.nds_gamma_lbf_per_in,
            "Cg_difference": result.cg_difference,
            "matches_within_tolerance": result.matches_within_tolerance,
            "capacity": None,
            "criterion_disposition": "pending",
            "scope": result.comparison_scope,
        },
        "expected_published_rounded_Cg": 0.98,
        "interpretation": (
            "This checks the existing evaluator against a published example. "
            "Its synthetic caller manifest is a software fixture; it is not a "
            "MoonBoard source binding or candidate factor."
        ),
    }


def _validate_artifact_shapes(
    inputs: dict[str, Any],
    bank: dict[str, Any],
    graph: dict[str, Any],
    wrenches: dict[str, Any],
    legacy: dict[str, Any],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    if bank.get("schema") != "eoere_v10_own_response_bank/v1":
        raise ValueError("selected112 response bank schema changed")
    if bank.get("case_ids") != EXPECTED_CASE_IDS or bank.get("all_six_cases_admitted") is not True:
        raise ValueError("selected112 response bank case set or admission changed")
    if bank.get("admission_gate_N") != 1.0e-5 or bank.get("historical_force_pass_transferred") is not False:
        raise ValueError("selected112 bank gate or historical-transfer declaration changed")
    if inputs.get("schema") != "eoere_v10_first_order_inputs/v1":
        raise ValueError("selected112 prepared-input schema changed")
    if len(inputs.get("shafts", [])) != 112 or len(inputs.get("timber_rows", [])) != 22:
        raise ValueError("selected112 input shaft/timber census changed")
    if graph.get("schema") != "v10_local_hardware_cleat_subassembly_graph/v1":
        raise ValueError("selected112 graph schema changed")
    if wrenches.get("schema") != "v10_selected112_local_subassembly_boundary_wrenches/v1":
        raise ValueError("selected112 boundary-wrench schema changed")
    selected = graph.get("selected112", {})
    components = selected.get("components", [])
    hardware_components = [
        row
        for row in components
        if row.get("component_kind") != "unfitted_wood_only_shaft_vertex"
    ]
    wood_scopes = selected.get("wood_only_joint_scopes", [])
    if len(components) != 30 or len(hardware_components) != 20 or len(wood_scopes) != 6:
        raise ValueError("selected112 graph review-scope census changed")
    graph_hardware_axes: set[str] = set()
    for component in hardware_components:
        axes = set(component.get("axis_ids", []))
        body_axes = {
            body.removeprefix("shaft/")
            for body in component.get("body_ids", [])
            if body.startswith("shaft/")
        }
        if axes != body_axes or graph_hardware_axes & axes:
            raise ValueError(f"graph axis/body membership mismatch: {component.get('component_id')}")
        graph_hardware_axes.update(axes)
    wood_axes: set[str] = set()
    for scope in wood_scopes:
        axes = set(scope.get("axis_ids", []))
        bodies = {
            body.removeprefix("shaft/")
            for body in scope.get("shaft_body_ids", [])
            if body.startswith("shaft/")
        }
        if axes != bodies or len(scope.get("receiver_body_ids", [])) != 2:
            raise ValueError(f"invalid wood-only scope: {scope.get('scope_id')}")
        wood_axes.update(axes)
    all_axes = {row["axis_id"] for row in inputs["shafts"]}
    if graph_hardware_axes & wood_axes or graph_hardware_axes | wood_axes != all_axes:
        raise ValueError("selected112 graph does not partition all shaft axes")
    if len(graph_hardware_axes) != 102 or len(wood_axes) != 10:
        raise ValueError("selected112 hardware/wood-only axis census changed")
    bank_case_ids = [row.get("case_id") for row in bank.get("cases", [])]
    wrench_case_ids = [row.get("case_id") for row in wrenches.get("cases", [])]
    if set(bank_case_ids) != set(EXPECTED_CASE_IDS) or set(wrench_case_ids) != set(EXPECTED_CASE_IDS):
        raise ValueError("selected112 bank/wrench case membership changed")
    if len(wrenches.get("field_and_replay_bindings", [])) != 6:
        raise ValueError("selected112 wrench field/replay bindings are incomplete")
    bank_case_by_id = {row["case_id"]: row for row in bank["cases"]}
    wrench_bindings_by_id = {
        row["case_id"]: row for row in wrenches["field_and_replay_bindings"]
    }
    if set(bank_case_by_id) != set(wrench_bindings_by_id):
        raise ValueError("selected112 bank and wrench replay case ids differ")
    for case_id, bank_case in bank_case_by_id.items():
        if bank_case.get("both_independent_replays_admitted") is not True:
            raise ValueError(f"bank independent replays are not admitted: {case_id}")
        source_case = wrench_bindings_by_id[case_id]
        if len(source_case.get("both_independent_replays", [])) != 2:
            raise ValueError(f"missing independent replay binding: {source_case.get('case_id')}")
        bank_replays = {
            "independent_replay": bank_case.get("independent_replay"),
            "independent_plywood_replay": bank_case.get("independent_plywood_replay"),
        }
        collector_replays = {
            row.get("kind"): {"path": row.get("path"), "sha256": row.get("sha256")}
            for row in source_case["both_independent_replays"]
        }
        if source_case.get("field") != bank_case.get("field") or collector_replays != bank_replays:
            raise ValueError(f"bank/wrench field or replay binding mismatch: {case_id}")
    if legacy.get("response_bank", {}).get("sha256") != EXPECTED_SOURCE_SHA256["response_bank"]:
        raise ValueError("legacy diagnostic source does not bind selected112 bank")
    if legacy.get("actual_Cg_adopted") is not None or legacy.get("actual_Cdelta_adopted") is not None:
        raise ValueError("legacy diagnostic source unexpectedly adopts Cg or Cdelta")
    if len(legacy.get("bearing_diagnostic_rows", [])) != 15:
        raise ValueError("legacy receiver-signature diagnostic row count changed")
    load_contract = bank.get("load_contract", {})
    expected_loads = {
        "weight_lb": 250,
        "downward_multiplier": 2,
        "horizontal_force_N": 300,
        "accessory_mass_kg": 25,
        "duration_factor_CD": 1,
    }
    if load_contract != expected_loads:
        raise ValueError("selected112 load contract changed")
    if inputs.get("historical_q") is not None or inputs.get("old_field") is not None:
        raise ValueError("selected112 prepared inputs contain an old force/q state")
    return hardware_components, wood_scopes


def _build_review_components(
    hardware_components: list[dict[str, Any]],
    wrench_cases: list[dict[str, Any]],
    wrench_path: str,
    wrench_sha: str,
) -> list[dict[str, Any]]:
    by_case = {}
    case_index_by_id = {}
    for case_index, case in enumerate(wrench_cases):
        case_index_by_id[case["case_id"]] = case_index
        indexed_components = {
            component["component_id"]: (component_index, component)
            for component_index, component in enumerate(
                case.get("hardware_cleat_components", [])
            )
        }
        if len(indexed_components) != len(case.get("hardware_cleat_components", [])):
            raise ValueError(f"duplicate component record in wrench case: {case['case_id']}")
        by_case[case["case_id"]] = indexed_components
    output = []
    for component in hardware_components:
        component_id = component["component_id"]
        case_results = []
        for case_id in CASE_IDS:
            indexed_component = by_case[case_id].get(component_id)
            if indexed_component is None:
                raise ValueError(f"component missing or duplicated in case: {case_id}/{component_id}")
            component_index, source_component = indexed_component
            case_results.extend(
                row
                for row in _case_component_wrenches(
                    {"case_id": case_id, "hardware_cleat_components": [source_component]},
                    wrench_path,
                    wrench_sha,
                    case_index=case_index_by_id[case_id],
                    source_component_index=component_index,
                )
            )
        output.append(
            {
                "component_id": component_id,
                "component_kind": component.get("component_kind"),
                "review_scope_only": True,
                "not_an_NDS_fastener_group": True,
                "body_ids": component.get("body_ids"),
                "axis_ids": component.get("axis_ids"),
                "shaft_body_ids": component.get("shaft_body_ids"),
                "fitting_body_ids": component.get("fitting_body_ids"),
                "cleat_body_ids": component.get("cleat_body_ids"),
                "sawn_wood_boundary_port_ids": component.get("sawn_wood_boundary_port_ids"),
                "case_wrenches": case_results,
                "actual_Cg": None,
                "complete_Cdelta": None,
                "capacity": None,
                "applicability_status": "UNRESOLVED",
            }
        )
    return output


def _build_wood_only_scopes(
    graph_scopes: list[dict[str, Any]], wrench_cases: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    by_case = {row["case_id"]: row for row in wrench_cases}
    results = []
    for scope in graph_scopes:
        per_case = []
        for case_id in CASE_IDS:
            matching = [
                row
                for row in by_case[case_id].get("wood_only_joint_scopes", [])
                if row.get("scope_id") == scope["scope_id"]
            ]
            if len(matching) != 1:
                raise ValueError(f"wood-only scope missing or duplicated: {case_id}/{scope['scope_id']}")
            per_case.append(matching[0])
        results.append(
            {
                **scope,
                "review_scope_only": True,
                "not_an_NDS_fastener_group": True,
                "case_wrenches": per_case,
                "actual_Cg": None,
                "complete_Cdelta": None,
                "capacity": None,
                "applicability_status": "UNRESOLVED",
                "unresolved_reason_codes": [
                    "no_source-qualified effective NDS member EA and no calibrated equivalent row slip",
                    "six-case signed force/moment actions are preserved; force-only row applicability is not established",
                    "existing finite-element shaft foundation law has not been calibrated to NDS group-action distribution",
                ],
            }
        )
    return results


def build_assessment(
    documents: dict[str, Any],
    source_refs: dict[str, str],
    *,
    source_paths: dict[str, str] | None = None,
) -> dict[str, Any]:
    inputs = documents["prepared_inputs"]
    bank = documents["response_bank"]
    graph = documents["component_graph"]
    wrenches = documents["boundary_wrenches"]
    legacy = documents["legacy_evaluation"]
    geometry = documents["analysis_geometry"]
    plywood_material = documents["plywood_material"]
    hardware_components, wood_scopes = _validate_artifact_shapes(
        inputs, bank, graph, wrenches, legacy
    )
    if len(geometry.get("axes", [])) != 112:
        raise ValueError("analysis geometry does not contain exactly112 axes")
    if geometry.get("revision") != "eoere-v10-perfect-bond-four-host-analysis-v1":
        raise ValueError("prepared analysis geometry revision changed")
    if "packer-free" not in str(geometry.get("scope", "")).lower():
        raise ValueError("prepared analysis geometry is not the packer-free revision")
    if bank.get("physical_geometry", {}).get("sha256") != source_refs["checked_receipt"]:
        raise ValueError("response bank no longer binds the checked geometry receipt")
    if bank.get("analysis_geometry", {}).get("sha256") != source_refs["analysis_geometry"]:
        raise ValueError("response bank no longer binds current analysis geometry")
    graph_refs = graph.get("source_bindings", {})
    expected_graph_refs = {
        "selected112_prepared_inputs": source_refs["prepared_inputs"],
        "selected112_physical_geometry": source_refs["physical_geometry"],
        "selected112_analysis_geometry": source_refs["analysis_geometry"],
    }
    for key, digest in expected_graph_refs.items():
        if graph_refs.get(key, {}).get("sha256") != digest:
            raise ValueError(f"component graph binding mismatch: {key}")
    for key, digest in {
        "fea/generated/v10-packer-free-v1/mechanics/analysis-v2/response-bank.json": source_refs[
            "response_bank"
        ],
        "fea/generated/v10-packer-free-v1/mechanics/analysis-v2/preparation/inputs.json": source_refs[
            "prepared_inputs"
        ],
        "fea/generated/v10-packer-free-v1/mechanics/analysis-v2/geometry/geometry.json": source_refs[
            "analysis_geometry"
        ],
        "fea/generated/v10-packer-free-v1/geometry-v1/geometry.json": source_refs[
            "physical_geometry"
        ],
    }.items():
        if wrenches.get("source_sha256", {}).get(key) != digest:
            raise ValueError(f"boundary-wrench source binding mismatch: {key}")

    row_roles, unclassified_axes = build_physical_row_roles(
        inputs, hardware_components, plywood_material
    )
    component_cases = {row["case_id"]: row for row in wrenches["cases"]}
    component_reports = _build_review_components(
        hardware_components,
        wrenches["cases"],
        str((source_paths or {}).get("boundary_wrenches", SOURCE_PATHS["boundary_wrenches"])),
        source_refs["boundary_wrenches"],
    )
    rows_by_case_component = {
        (case_id, row["component_id"]): row
        for case_id, case_row in component_cases.items()
        for row in _case_component_wrenches(
            case_row,
            str((source_paths or {}).get("boundary_wrenches", SOURCE_PATHS["boundary_wrenches"])),
            source_refs["boundary_wrenches"],
            case_index=CASE_IDS.index(case_id),
        )
    }
    for row in row_roles:
        component_id = row["review_component_ids"][0] if len(row["review_component_ids"]) == 1 else None
        if component_id is None:
            continue
        row["case_action_refs"] = [
            _row_case_action_refs(row, rows_by_case_component[(case_id, component_id)])
            for case_id in CASE_IDS
        ]

    # Check that row-role membership plus unclassified rows accounts for every
    # hardware shaft, while retaining the 10 wood-only axes in their own scopes.
    row_axes = {record["axis_id"] for row in row_roles for record in row["fastener_axes"]}
    unclassified_ids = {row["axis_id"] for row in unclassified_axes}
    hardware_axes = {axis for comp in hardware_components for axis in comp.get("axis_ids", [])}
    if row_axes & unclassified_ids or row_axes | unclassified_ids != hardware_axes:
        raise ValueError("row-role and topology-only shaft census does not cover hardware graph")

    wood_reports = _build_wood_only_scopes(wood_scopes, wrenches["cases"])
    wood_geometry_candidates = build_wood_only_geometry_descriptors(
        inputs,
        wood_scopes,
        wrenches["cases"],
        plywood_material,
        str((source_paths or {}).get("boundary_wrenches", SOURCE_PATHS["boundary_wrenches"])),
        source_refs["boundary_wrenches"],
    )
    legacy_rows = [dict(row) for row in legacy["bearing_diagnostic_rows"]]
    legacy_record = {
        "status": "LEGACY_DIAGNOSTIC_ONLY",
        "source": {
            "path": str((source_paths or {}).get("legacy_evaluation", SOURCE_PATHS["legacy_evaluation"])),
            "sha256": source_refs["legacy_evaluation"],
        },
        "row_count": len(legacy_rows),
        "rows": legacy_rows,
        "interpretation": (
            "Preserved receiver-signature 1/n decomposition values. They are not an NDS "
            "requirement, universal conservative bound, actual Cg, capacity, or failure criterion."
        ),
    }
    source_map = {
        name: {
            "path": str((source_paths or {}).get(name, path)),
            "sha256": source_refs[name],
        }
        for name, path in SOURCE_PATHS.items()
    }
    input_material = inputs.get("scenario", {}).get("timber_e_mpa")
    wood_foundation = inputs.get("scenario", {}).get("common_shaft_parameters", {}).get(
        "wood_foundation_n_mm2"
    )
    benchmark = _build_caltrans_example12_benchmark()
    direct_contact_sources = []
    for case_index, case_record in enumerate(wrenches["cases"]):
        direct_rows = case_record.get("direct_timber_to_timber_contacts_separate_channel", [])
        if len(direct_rows) != case_record.get("direct_timber_to_timber_contact_count"):
            raise ValueError(f"separate direct-contact count mismatch: {case_record['case_id']}")
        direct_contact_sources.append(
            {
                "case_id": case_record["case_id"],
                "action_count": len(direct_rows),
                "source": {
                    "path": str(
                        (source_paths or {}).get(
                            "boundary_wrenches", SOURCE_PATHS["boundary_wrenches"]
                        )
                    ),
                    "sha256": source_refs["boundary_wrenches"],
                    "json_pointer": f"/cases/{case_index}/direct_timber_to_timber_contacts_separate_channel",
                },
                "action_ids": [row.get("id") for row in direct_rows],
                "interpretation": "separate external timber-to-timber contact channel; not unioned into hardware/cleat review scopes",
            }
        )
    return {
        "schema": "eoere_v10_group_effects_assessment/v1",
        "status": "UNRESOLVED",
        "candidate_id": "compact-floor-flush-bolted-development",
        "revision_id": "v10-packer-free-flush-return-far-row-only-v1",
        "authority_scope": "selected112 current admitted response bank; candidate Cg not assigned",
        "source_bindings": source_map,
        "current_input_contract": {
            "response_bank_case_ids": list(CASE_IDS),
            "all_six_admitted": bank.get("all_six_cases_admitted"),
            "unchanged_admission_gate_N": bank.get("admission_gate_N"),
            "both_independent_replays_bound_per_case": True,
            "load_contract": bank.get("load_contract"),
            "historical_force_pass_transferred": False,
            "physical_shaft_count": len(inputs["shafts"]),
            "analysis_axis_count": len(geometry["axes"]),
            "hardware_cleat_review_component_count": len(component_reports),
            "wood_only_review_scope_count": len(wood_reports),
            "hardware_graph_shaft_count": len(hardware_axes),
            "wood_only_graph_shaft_count": len(wood_scopes) and sum(
                len(scope.get("axis_ids", [])) for scope in wood_scopes
            ),
            "shafts_without_fitting_attachment_role": len(unclassified_axes),
            "physical_attachment_row_role_count": len(row_roles),
        },
        "method_benchmark": benchmark,
        "primary_method_sources": {
            "NDS_2024_chapter_11": source_map["nds_chapter_11"],
            "NDS_2024_chapter_12": source_map["nds_chapter_12"],
            "group_action_gamma_errata": {
                "title": "2024 NDS Errata and Addenda, March 28 2025",
                "url": "https://web-media.awc.org/wp-content/uploads/2025/03/31134949/2024-NDS-Errata-and-Addenda-03.28.25.pdf",
                "scope": "official errata to NDS-2024 §11.3.6.1 gamma exponent notation; referenced by the bound owner work packet",
                "local_pdf_sha256": None,
                "local_copy_status": "not copied into this packet; source URL and pinned NDS Chapter 11/evaluator are recorded",
            },
            "maintained_NDS_evaluator": source_map["nds_evaluator"],
            "serial_row_benchmark_helper": source_map["serial_row_benchmark"],
            "owner_work_packet": source_map["owner_work_packet"],
            "pinned_method_closure_summary": source_map["primary_method_closure"],
        },
        "current_operator_context": {
            "sawn_wood_E_mpa": input_material,
            "sawn_wood_E_unit": "N/mm^2",
            "sawn_wood_modulus_source": "prepared inputs scenario.timber_e_mpa; nominal gross-stock operator assumption",
            "gross_member_EA_unit": "N",
            "effective_NDS_group_EA": None,
            "effective_NDS_group_EA_status": "UNRESOLVED",
            "effective_NDS_group_slip_modulus": None,
            "effective_NDS_group_slip_modulus_unit": "N/mm",
            "effective_NDS_group_slip_modulus_status": "UNRESOLVED",
            "current_FE_wood_foundation_parameter": {
                "value": wood_foundation,
                "unit": "N/mm^2",
                "source": "prepared inputs scenario.common_shaft_parameters.wood_foundation_n_mm2",
                "interpretation": "distributed shaft foundation parameter, not NDS serial-row gamma",
            },
            "current_FE_foundation_and_beam_load_sharing_equivalence_to_NDS": "UNRESOLVED",
            "source_qualification_gaps": [
                "NDS effective group areas/EA are not source-qualified for these multi-member local rows.",
                "No matched calibration establishes equivalence between FE distributed shaft foundations/interpolated ports and NDS serial row slip.",
                "Physical row ownership, shear planes, grain/loading applicability, and force-only versus local-moment effects are not established for an NDS Cg input.",
                "The 150 mm beam segmentation exceeds the 41–67 mm row pitch range, so port interpolation is not a discrete serial-bolt-row model.",
            ],
        },
        "physical_row_role_inventory": {
            "row_role_count": len(row_roles),
            "unique_fastener_axes_with_source_row_roles": len(row_axes),
            "row_role_membership_count": sum(len(row["fastener_axes"]) for row in row_roles),
            "axes_repeated_in_multiple_fitting_roles": sorted(
                axis
                for axis in row_axes
                if sum(axis in {r["axis_id"] for r in row["fastener_axes"]} for row in row_roles) > 1
            ),
            "topology_only_hardware_axis_count": len(unclassified_axes),
            "topology_only_hardware_axes": unclassified_axes,
            "rows": row_roles,
            "interpretation": (
                "These are source-defined attachment/flange row roles. Shared shafts can occur "
                "in multiple roles; roles are not disjoint NDS groups and their wrenches must not be summed across roles."
            ),
        },
        "hardware_cleat_review_components": component_reports,
        "wood_only_review_scopes": wood_reports,
        "wood_only_geometric_candidate_rows": wood_geometry_candidates,
        "separate_direct_timber_contact_channel": direct_contact_sources,
        "legacy_receiver_signature_diagnostics": legacy_record,
        "candidate_Cg": None,
        "candidate_Cdelta": None,
        "complete_joint_capacity": None,
        "criterion_disposition": "UNRESOLVED",
        "structural_acceptance": False,
        "climbing_released": False,
        "fabrication_released": False,
        "purchase_authorized": False,
        "release": False,
        "ndsgroup_candidate_payloads_routed_to_evaluator": 0,
        "qualification": {
            "candidate_factor_assigned": False,
            "capacity_computed": False,
            "criterion_acceptance": False,
            "physical_hardware_or_bond_verified": False,
            "component_graph_is_a_fastener_group": False,
            "separate_direct_wood_to_wood_contact_channel_retained": True,
            "authority_note": (
                "A review component or attachment role is not automatically an NDS group. "
                "The benchmark checks the equation implementation only."
            ),
        },
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT, help="repository root")
    parser.add_argument("--out", type=Path, default=ROOT / DEFAULT_OUTPUT)
    args = parser.parse_args(argv)
    root = args.root.resolve()
    documents, hashes = load_bound_sources(root)
    rel_paths = {name: path.as_posix() for name, path in SOURCE_PATHS.items()}
    report = build_assessment(documents, hashes, source_paths=rel_paths)
    script_path = root / Path(__file__).resolve().relative_to(ROOT)
    report["producer"] = {
        "path": script_path.relative_to(root).as_posix(),
        "sha256": sha256_file(script_path),
        "invocation": "uv run python -m scripts.assess_v10_group_effects --out <ignored-path>",
    }
    out = args.out if args.out.is_absolute() else root / args.out
    out.parent.mkdir(parents=True, exist_ok=True)
    if out.exists():
        raise ValueError(f"refusing to overwrite existing assessment: {out}")
    out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"status": report["status"], "output": str(out), "sha256": sha256_file(out)}))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (KeyError, TypeError, ValueError, OSError) as exc:
        print(f"assess_v10_group_effects: {exc}", file=sys.stderr)
        raise SystemExit(2) from exc
