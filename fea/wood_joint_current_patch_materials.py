"""Bind proposal-only elastic material scenarios to the current patch mesh.

This module reads the frozen current-patch inventory and attempt-02 mesh report,
checks their source bindings, and emits material/orientation/solid-section cards.
It does not create geometry, contacts, restraints, loads, rigid-body definitions,
or a solver run, and it makes no claim about delivered material properties.
"""

from __future__ import annotations

import hashlib
import json
import math
import re
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from fea import wood_joint_patch_materials as timber_materials
from fea import wood_joint_patch_steel_material as steel_materials

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = "wood_joint_current_patch_material_binding/v1"
STATUS = "proposal_only_current_patch_material_map"
INPUT_SCHEMA = "wood_joint_current_patch_inputs/v1"
INPUT_STATUS = "current_geometry_patch_inputs_only"
MESH_SCHEMA = "wood_joint_current_patch_mesh/v1"
MESH_STATUS = "VERIFIED_C3D10_CURRENT_PATCH_MESH_ONLY_NO_SOLVER"
REVISION_ID = "led-clearance-2x6-runner-seated-blocks-v1"
SOURCE_INVENTORY_PATH = "docs/wood-joints-mvp/source-inventory.json"
WOOD_SCENARIO_NAME = "WOOD_ELASTIC_DIAGNOSTIC"
STEEL_SCENARIO_NAME = "STEEL_ELASTIC_DIAGNOSTIC"
CLEAT_ID = "bottom_center_right_cleat"
CLEAT_SOURCE_FRAME_ID = "base_rail_bottom_right"
EXPECTED_WOOD_IDS = (
    CLEAT_ID,
    "base_rail_bottom_right",
    "base_principal_center_right",
)
RING_CASES = (
    {
        "case_id": "source_transverse_a",
        "helper_case_index": 0,
        "description": (
            "For each member, assign radial R to the first transverse source axis "
            "in the existing X/T/N helper order; the helper signs T for a right-handed frame."
        ),
    },
    {
        "case_id": "source_transverse_b",
        "helper_case_index": 1,
        "description": (
            "For each member, assign radial R to the second transverse source axis "
            "in the existing X/T/N helper order; the helper signs T for a right-handed frame."
        ),
    },
)
NUT_ROLE = "nut"
NUT_GEOMETRY_LIMIT = (
    "The four nut STEP bodies are solid cylindrical viewer envelopes without internal "
    "thread bores; an elastic assignment is only a generic numerical reference, not "
    "physical nut compliance or a response-ready nut model."
)
LIMITATIONS = (
    "Elastic constants are proposal-only diagnostic scenarios, not measured or verified properties of delivered wood or hardware.",
    "No species/grade-specific wood properties, steel grade, yield strength, plasticity, resistance, or capacity are assigned.",
    "No contact, tie, load, restraint, rigid-body definition, native solve, or acceptance result is emitted.",
    "The result maps 19 mesh body ELSETs (3 timber bodies and 16 metal-role envelopes); it does not claim a 19-component physical assembly.",
    NUT_GEOMETRY_LIMIT,
)


def _sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _sha256_file(path: Path) -> str:
    return _sha256_bytes(path.read_bytes())


def _canonical_sha256(value: Mapping[str, Any]) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)
    return _sha256_bytes(encoded.encode("utf-8"))


def _plain(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {str(key): _plain(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return [_plain(item) for item in value]
    return value


def _resolve_file(value: str | Path, context: str) -> Path:
    path = Path(value).expanduser()
    if not path.is_absolute():
        cwd_path = Path.cwd() / path
        root_path = ROOT / path
        path = cwd_path if cwd_path.is_file() else root_path
    path = path.resolve()
    if not path.is_file():
        raise FileNotFoundError(f"{context} does not exist: {path}")
    return path


def _display_path(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return str(path.resolve())


def _read_json(path: Path, context: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise ValueError(f"{context} is not readable JSON") from error
    if not isinstance(value, dict):
        raise TypeError(f"{context} must be a JSON object")
    return value


def _vector(value: Any, context: str) -> tuple[float, float, float]:
    if isinstance(value, (str, bytes)) or not isinstance(value, Sequence):
        raise TypeError(f"{context} must be a finite three-vector")
    try:
        vector = tuple(float(component) for component in value)
    except (TypeError, ValueError, OverflowError) as error:
        raise ValueError(f"{context} must be a finite three-vector") from error
    if len(vector) != 3 or not all(math.isfinite(component) for component in vector):
        raise ValueError(f"{context} must be a finite three-vector")
    magnitude = math.sqrt(math.fsum(component * component for component in vector))
    if not math.isclose(magnitude, 1.0, rel_tol=0.0, abs_tol=1e-8):
        raise ValueError(f"{context} must be a unit vector")
    return vector  # type: ignore[return-value]


def _dot(left: Sequence[float], right: Sequence[float]) -> float:
    return math.fsum(a * b for a, b in zip(left, right, strict=True))


def _matching_local_axis(
    grain: tuple[float, float, float], axes: Mapping[str, Sequence[float]], context: str
) -> str:
    alignments = {name: abs(_dot(grain, axes[name])) for name in ("X", "T", "N")}
    matches = [name for name, value in alignments.items() if value >= 1.0 - 1e-8]
    if len(matches) != 1:
        raise ValueError(
            f"{context} grain must align with exactly one source X/T/N axis"
        )
    return matches[0]


def _source_file_binding(
    relative_path: str, *, expected_sha256: str | None = None
) -> dict[str, str]:
    path = ROOT / relative_path
    if not path.is_file():
        raise FileNotFoundError(f"bound source file is missing: {relative_path}")
    actual = _sha256_file(path)
    if expected_sha256 is not None and actual != expected_sha256:
        raise ValueError(f"bound source file hash changed: {relative_path}")
    return {"path": relative_path, "sha256": actual}


def _validate_mesh_deck_elsets(mesh_deck: str, expected: set[str]) -> None:
    found: list[str] = []
    for line in mesh_deck.splitlines():
        if not line.lstrip().upper().startswith("*ELEMENT"):
            continue
        attributes = {}
        for field in line.strip().split(",")[1:]:
            if "=" in field:
                key, value = field.strip().split("=", 1)
                attributes[key.strip().upper()] = value.strip().upper()
        if attributes.get("TYPE") != "C3D10" or "ELSET" not in attributes:
            raise ValueError("attempt-02 mesh deck has an unexpected element-set card")
        found.append(attributes["ELSET"])
    if len(found) != 19 or set(found) != expected or len(set(found)) != len(found):
        raise ValueError(
            "attempt-02 mesh deck does not contain the exact 19 body ELSETs"
        )


def _source_frame_for_wood_body(
    body: Mapping[str, Any], source_parts: Mapping[str, Mapping[str, Any]]
) -> dict[str, Any]:
    part_id = body.get("part_id")
    grain_record = body.get("grain")
    if not isinstance(part_id, str) or not isinstance(grain_record, Mapping):
        raise TypeError("each current patch wood body needs an ID and grain record")
    source_part_id = grain_record.get("source_part_id")
    source_part = source_parts.get(source_part_id)
    if not isinstance(source_part, Mapping):
        raise TypeError(f"{part_id} grain source is missing from the source inventory")
    local_axes = source_part.get("local_axes")
    if not isinstance(local_axes, Mapping) or set(local_axes) != {"X", "T", "N"}:
        raise ValueError(f"{source_part_id} lacks an exact source X/T/N frame")
    axes = {
        name: _vector(local_axes[name], f"{source_part_id} source {name}")
        for name in ("X", "T", "N")
    }
    grain = _vector(grain_record.get("grain_axis_global_xyz"), f"{part_id} grain")
    inferred_name = _matching_local_axis(grain, axes, part_id)
    declared_name = grain_record.get("grain_axis_local_name")
    if declared_name is not None and declared_name != inferred_name:
        raise ValueError(
            f"{part_id} declared grain axis disagrees with source X/T/N frame"
        )

    if part_id == CLEAT_ID:
        if source_part_id != CLEAT_SOURCE_FRAME_ID or inferred_name != "N":
            raise ValueError("current cleat L axis must use bottom-rail source frame N")
    else:
        if source_part_id != part_id:
            raise ValueError(
                f"{part_id} host grain must be sourced from its own inventory frame"
            )
        source_grain = source_part.get("grain_axis_global_xyz")
        if (
            source_grain is None
            or abs(_dot(grain, _vector(source_grain, f"{part_id} source grain")))
            < 1.0 - 1e-8
        ):
            raise ValueError(
                f"{part_id} current grain differs from its source-inventory grain"
            )

    return {
        "part_id": part_id,
        "source_part_id": source_part_id,
        "grain_axis_local_name": inferred_name,
        "grain_axis_global_xyz": grain,
        "local_axes_global_xyz": axes,
        "grain_basis": grain_record.get("grain_basis"),
        "delivered_stock_observed": False,
    }


def _compact_scenario(
    scenario: Mapping[str, Any], *, material_name: str
) -> dict[str, Any]:
    if material_name == WOOD_SCENARIO_NAME:
        return {
            "scenario_id": scenario["scenario_id"],
            "status": scenario["status"],
            "material_basis": scenario["material_basis"],
            "source_document": scenario["source_document"],
            "source_document_sha256": scenario["source_document_sha256"],
            "scenario_sha256": scenario["scenario_sha256"],
            "material_axes": scenario["material_axis_names"],
            "engineering_constants_mpa": scenario["calculix_engineering_constants"],
            "engineering_constant_order": scenario["engineering_constant_order"],
            "units": scenario["units"],
            "stock_properties_measured": scenario["stock_properties_measured"],
            "grade_specific_measured_properties_claim": scenario[
                "grade_specific_measured_properties_claim"
            ],
            "resistance_claim": scenario["resistance_claim"],
            "qualified_for_design": scenario["qualified_for_design"],
        }
    return {
        "scenario_id": scenario["scenario_id"],
        "status": scenario["status"],
        "material_basis": scenario["material_basis"],
        "source_document": scenario["source_document"],
        "source_document_sha256": scenario["source_document_sha256"],
        "scenario_sha256": scenario["scenario_sha256"],
        "source_references": scenario["source_references"],
        "youngs_modulus_mpa": scenario["youngs_modulus_mpa"],
        "poisson_ratio": scenario["poisson_ratio"],
        "derived_shear_modulus_mpa": scenario["derived_shear_modulus_mpa"],
        "calculix_elastic_type": scenario["calculix_elastic_type"],
        "units": scenario["units"],
        "delivered_material_properties_verified": scenario[
            "delivered_material_properties_verified"
        ],
        "steel_grade_assigned": scenario["steel_grade_assigned"],
        "plasticity_defined": scenario["plasticity_defined"],
        "strength_or_resistance_claim": scenario["strength_or_resistance_claim"],
        "qualified_for_design": scenario["qualified_for_design"],
        "current_assignment_scope": (
            "The E=200000 MPa, nu=0.30 baseline is assigned as a generic diagnostic "
            "reference to current patch metal ELSETs; only the numerical values are "
            "reused from the helper scenario, whose earlier body count does not transfer."
        ),
    }


def _render_fragment(
    *,
    wood_material_card: str,
    steel_material_card: str,
    wood_rows: Sequence[Mapping[str, Any]],
    steel_rows: Sequence[Mapping[str, Any]],
    rigid_nuts_reserved: bool,
) -> str:
    nut_rows = [row for row in steel_rows if row["component_role"] == NUT_ROLE]
    if len(nut_rows) != 4:
        raise ValueError("current patch must bind exactly four nut-role ELSETs")
    omitted_nuts = (
        {row["elset_name"] for row in nut_rows} if rigid_nuts_reserved else set()
    )
    lines = [
        "** Current patch elastic material and section assignments; scenario inputs only.",
        "** Select one R/T and one metal branch; do not combine fragments.",
        "** No contact, tie, load, restraint, rigid-body definition, or solve cards are included.",
        "** Nut STEP bodies are solid cylindrical viewer envelopes without internal bores, not physical nut compliance or response-ready geometry.",
        *wood_material_card.splitlines(),
        *steel_material_card.splitlines(),
    ]
    if not rigid_nuts_reserved:
        lines.extend(
            [
                "** Nut elastic sections are generic references only, not physical nut compliance:",
                "** the four source STEP nut bodies are solid cylindrical viewer envelopes without bores.",
            ]
        )
    for wood_row in wood_rows:
        orientation = wood_row["orientation"]
        lines.extend(
            timber_materials.render_orientation_card(
                wood_row["orientation_name"], orientation
            ).splitlines()
        )
    for wood_row in wood_rows:
        lines.append(
            "*SOLID SECTION,ELSET={elset},MATERIAL={material},ORIENTATION={orientation}".format(
                elset=wood_row["elset_name"],
                material=WOOD_SCENARIO_NAME,
                orientation=wood_row["orientation_name"].upper(),
            )
        )
    for steel_row in steel_rows:
        if steel_row["elset_name"] in omitted_nuts:
            continue
        lines.append(
            f"*SOLID SECTION,ELSET={steel_row['elset_name']},MATERIAL={STEEL_SCENARIO_NAME}"
        )
    if rigid_nuts_reserved:
        lines.extend(
            [
                "** Nut ELSETs intentionally have no elastic section in this alternative:",
                "** " + ", ".join(sorted(omitted_nuts)),
                "** A downstream rigid-body branch may consume these ELSETs; no rigid card is emitted here.",
            ]
        )
    return "\n".join(lines) + "\n"


def build_current_patch_materials(
    inventory_path: str | Path, mesh_report_path: str | Path
) -> dict[str, Any]:
    """Build a source-bound material map and `.inp` fragments for one mesh.

    The two global transverse alternatives apply one declared R/T choice per
    timber body. Each is emitted both with generic elastic reference cards for
    all 16 metal-role bodies and with the four nut ELSETs reserved for a
    mutually exclusive downstream rigid-body branch.
    """

    inventory_file = _resolve_file(inventory_path, "current patch inventory")
    mesh_file = _resolve_file(mesh_report_path, "current patch mesh report")
    inventory = _read_json(inventory_file, "current patch inventory")
    mesh = _read_json(mesh_file, "current patch mesh report")
    inventory_sha = _sha256_file(inventory_file)
    mesh_sha = _sha256_file(mesh_file)

    if (
        inventory.get("schema") != INPUT_SCHEMA
        or inventory.get("status") != INPUT_STATUS
    ):
        raise ValueError(
            "input is not the frozen current-patch inventory schema/status"
        )
    candidate = inventory.get("candidate")
    if (
        not isinstance(candidate, Mapping)
        or candidate.get("revision_id") != REVISION_ID
    ):
        raise ValueError(
            "current-patch inventory revision does not match the reviewed candidate"
        )
    if mesh.get("schema") != MESH_SCHEMA or mesh.get("status") != MESH_STATUS:
        raise ValueError(
            "input is not the verified attempt-02 current-patch mesh report"
        )
    if mesh.get("accepted") is not False or mesh.get("solved") is not False:
        raise ValueError("mesh report must remain an unaccepted mesh-only artifact")
    if mesh.get("native_solve_run") is not False:
        raise ValueError("mesh report unexpectedly records a native solve")
    if mesh.get("output_contains_material_contact_or_solver_cards") is not False:
        raise ValueError(
            "mesh input is expected to be geometry-only without solver assignments"
        )
    if (
        mesh.get("input_bundle_schema") != INPUT_SCHEMA
        or mesh.get("input_bundle_status") != INPUT_STATUS
    ):
        raise ValueError(
            "mesh report is not bound to the current-patch inventory contract"
        )
    if mesh.get("input_bundle_inventory_sha256") != inventory_sha:
        raise ValueError(
            "mesh report inventory hash differs from the supplied inventory"
        )
    mesh_candidate = mesh.get("current_candidate_binding")
    if (
        not isinstance(mesh_candidate, Mapping)
        or mesh_candidate.get("revision_id") != REVISION_ID
    ):
        raise ValueError(
            "mesh report candidate binding does not match the current revision"
        )
    if mesh_candidate.get("source_inventory_sha256") != candidate.get(
        "source_inventory_sha256"
    ):
        raise ValueError("mesh and inventory do not share the source-inventory pin")

    source_inventory_path = ROOT / SOURCE_INVENTORY_PATH
    source_inventory_sha = _sha256_file(source_inventory_path)
    if source_inventory_sha != candidate.get("source_inventory_sha256"):
        raise ValueError("current source inventory differs from the input bundle pin")
    if (
        inventory.get("geometry_binding", {}).get("source_inventory_sha256")
        != source_inventory_sha
    ):
        raise ValueError(
            "input geometry binding differs from the current source inventory"
        )
    source_inventory = _read_json(source_inventory_path, "source inventory")
    source_parts = {
        part["part_id"]: part
        for part in source_inventory.get("parts", [])
        if isinstance(part, Mapping) and isinstance(part.get("part_id"), str)
    }

    mesh_input_name = mesh.get("mesh_input_file")
    if (
        not isinstance(mesh_input_name, str)
        or Path(mesh_input_name).is_absolute()
        or ".." in Path(mesh_input_name).parts
    ):
        raise ValueError("mesh report must name a local relative mesh input file")
    mesh_input_file = (mesh_file.parent / mesh_input_name).resolve()
    if not mesh_input_file.is_file():
        raise FileNotFoundError("mesh report's source mesh deck is missing")
    mesh_input_sha = _sha256_file(mesh_input_file)
    if mesh_input_sha != mesh.get("mesh_input_sha256"):
        raise ValueError("mesh deck hash differs from the mesh report")
    mesh_body_order = mesh.get("mesh_body_owner_order")
    mesh_bodies = mesh.get("bodies")
    if (
        not isinstance(mesh_body_order, list)
        or not isinstance(mesh_bodies, Mapping)
        or len(mesh_body_order) != 19
        or set(mesh_body_order) != set(mesh_bodies)
        or len(set(mesh_body_order)) != 19
    ):
        raise ValueError("mesh report must contain an exact 19-body owner order")
    _validate_mesh_deck_elsets(
        mesh_input_file.read_text(encoding="utf-8"),
        {
            str(body.get("element_elset_name", "")).upper()
            for body in mesh_bodies.values()
            if isinstance(body, Mapping)
        },
    )

    if (
        mesh.get("body_count") != 19
        or mesh.get("mesh_body_count_expected") != 19
        or mesh.get("wood_body_count") != 3
        or mesh.get("physical_metal_body_count") != 16
    ):
        raise ValueError(
            "mesh report body counts do not match the current patch contract"
        )

    step_artifacts = inventory.get("step_artifacts")
    if not isinstance(step_artifacts, Mapping):
        raise TypeError("current patch inventory lacks STEP artifact hashes")
    elset_map: list[dict[str, Any]] = []
    wood_mesh_by_part: dict[str, Mapping[str, Any]] = {}
    steel_mesh_rows: list[dict[str, Any]] = []
    seen_elsets: set[str] = set()
    for mesh_body_id in mesh_body_order:
        body = mesh_bodies[mesh_body_id]
        if not isinstance(body, Mapping) or body.get("mesh_body_id") != mesh_body_id:
            raise ValueError("mesh body map contains a malformed body record")
        elset_name = body.get("element_elset_name")
        if not isinstance(elset_name, str) or not re.fullmatch(
            r"[A-Z][A-Z0-9_]{0,79}", elset_name
        ):
            raise ValueError(f"{mesh_body_id} does not contain a safe ELSET name")
        if elset_name in seen_elsets:
            raise ValueError("mesh report contains duplicate body ELSET names")
        seen_elsets.add(elset_name)
        source_key = body.get("source_step_artifact_key")
        expected_source = step_artifacts.get(source_key)
        if not isinstance(expected_source, Mapping):
            raise TypeError(
                f"{mesh_body_id} source STEP key is absent from the inventory"
            )
        if body.get("source_step_sha256") != expected_source.get("file_sha256"):
            raise ValueError(
                f"{mesh_body_id} source STEP hash does not match the input inventory"
            )
        if not isinstance(body.get("element_count"), int) or body["element_count"] <= 0:
            raise ValueError(f"{mesh_body_id} has no positive element count")

        row = {
            "mesh_body_id": mesh_body_id,
            "elset_name": elset_name,
            "owner_kind": body.get("owner_kind"),
            "component_role": body.get("component_role"),
            "source_body_id": body.get("source_body_id"),
            "physical_body_id": body.get("physical_body_id"),
            "source_step_artifact_key": source_key,
            "source_step_sha256": body.get("source_step_sha256"),
            "element_count": body["element_count"],
        }
        if body.get("owner_kind") == "wood_member":
            part_id = body.get("source_body_id")
            if not isinstance(part_id, str) or part_id in wood_mesh_by_part:
                raise ValueError("mesh wood bodies must bind unique source part IDs")
            wood_mesh_by_part[part_id] = {**row, "source_frame_owner": part_id}
        elif body.get("owner_kind") == "physical_metal":
            physical_id = body.get("physical_body_id")
            metal_inputs = {
                item.get("physical_body_id"): item
                for item in inventory.get("physical_metal_bodies", [])
                if isinstance(item, Mapping)
            }
            source_metal = metal_inputs.get(physical_id)
            if source_metal is None or source_metal.get("physical_kind") != body.get(
                "component_role"
            ):
                raise ValueError(
                    f"{mesh_body_id} metal role does not match its input body"
                )
            steel_mesh_rows.append(
                {
                    **row,
                    "material_name": STEEL_SCENARIO_NAME,
                    "scenario_id": f"steel_elastic_diagnostic_baseline_{steel_materials.SCENARIO_DATE}",
                    "delivered_part_properties_verified": False,
                    **(
                        {
                            "generic_assignment_is_physical_nut_compliance": False,
                            "physical_nut_response_ready": False,
                            "representation_limit": NUT_GEOMETRY_LIMIT,
                        }
                        if body.get("component_role") == NUT_ROLE
                        else {}
                    ),
                }
            )
        else:
            raise ValueError(f"{mesh_body_id} has an unsupported owner kind")
        elset_map.append(row)

    if set(wood_mesh_by_part) != set(EXPECTED_WOOD_IDS) or len(wood_mesh_by_part) != 3:
        raise ValueError(
            "current patch mesh does not contain its exact three wood bodies"
        )
    if len(steel_mesh_rows) != 16:
        raise ValueError(
            "current patch mesh does not contain exactly sixteen metal-role bodies"
        )
    steel_ids = [row["physical_body_id"] for row in steel_mesh_rows]
    if len(set(steel_ids)) != 16:
        raise ValueError("current patch metal body IDs are not unique")
    if [row["component_role"] for row in steel_mesh_rows].count(NUT_ROLE) != 4:
        raise ValueError("current patch mesh must contain four nut-role body envelopes")

    inventory_wood = {
        body.get("part_id"): body
        for body in inventory.get("wood_bodies", [])
        if isinstance(body, Mapping)
    }
    if set(inventory_wood) != set(EXPECTED_WOOD_IDS):
        raise ValueError(
            "current patch inventory does not contain the exact three wood bodies"
        )
    wood_rows: list[dict[str, Any]] = []
    body_orientation_cases: dict[str, tuple[dict[str, Any], ...]] = {}
    for mesh_body_id in mesh_body_order:
        mesh_body = mesh_bodies[mesh_body_id]
        if mesh_body.get("owner_kind") != "wood_member":
            continue
        part_id = mesh_body["source_body_id"]
        frame = _source_frame_for_wood_body(inventory_wood[part_id], source_parts)
        cases = timber_materials.material_orientation_cases(frame)
        if len(cases) != 2:
            raise ValueError(f"{part_id} does not yield exactly two R/T alternatives")
        body_orientation_cases[part_id] = cases
        wood_rows.append(
            {
                **wood_mesh_by_part[part_id],
                "part_id": part_id,
                "source_frame_owner": frame["source_part_id"],
                "grain_axis_local_name": frame["grain_axis_local_name"],
                "grain_axis_global_xyz": frame["grain_axis_global_xyz"],
                "local_axes_global_xyz": frame["local_axes_global_xyz"],
                "grain_basis": frame["grain_basis"],
                "delivered_stock_observed": False,
                "material_name": WOOD_SCENARIO_NAME,
                "scenario_id": timber_materials.SCENARIO_ID,
            }
        )

    wood_scenario = timber_materials.material_scenario()
    steel_scenario = steel_materials.material_scenario()
    wood_material_card = timber_materials.render_material_card(WOOD_SCENARIO_NAME)
    steel_material_card = steel_materials.render_material_card(
        STEEL_SCENARIO_NAME, steel_scenario
    )

    alternatives: list[dict[str, Any]] = []
    inp_fragments: dict[str, Any] = {}
    for global_case in RING_CASES:
        alternative_rows: list[dict[str, Any]] = []
        for wood_row in wood_rows:
            orientation = _plain(
                body_orientation_cases[wood_row["part_id"]][
                    global_case["helper_case_index"]
                ]
            )
            orientation_name = (
                f"ORI_{wood_row['mesh_body_id']}_{global_case['case_id']}"
            )
            row = {
                **wood_row,
                "orientation_name": orientation_name,
                "orientation": orientation,
            }
            alternative_rows.append(row)
        alternative = {
            "case_id": global_case["case_id"],
            "description": global_case["description"],
            "selection_policy": "same helper-order alternative is applied to each of the three wood bodies; this is not a measured growth-ring map",
            "body_orientations": alternative_rows,
        }
        alternatives.append(alternative)

        for rigid_nuts_reserved in (False, True):
            metal_branch_id = (
                "nuts_reserved_for_downstream_rigid_body"
                if rigid_nuts_reserved
                else "elastic_reference_all_16_metal_bodies"
            )
            fragment_key = f"{global_case['case_id']}__{metal_branch_id}"
            fragment = _render_fragment(
                wood_material_card=wood_material_card,
                steel_material_card=steel_material_card,
                wood_rows=alternative_rows,
                steel_rows=steel_mesh_rows,
                rigid_nuts_reserved=rigid_nuts_reserved,
            )
            nut_elsets = sorted(
                row["elset_name"]
                for row in steel_mesh_rows
                if row["component_role"] == NUT_ROLE
            )
            inp_fragments[fragment_key] = {
                "wood_orientation_case": global_case["case_id"],
                "metal_branch": metal_branch_id,
                "elastic_section_elset_names": [row["elset_name"] for row in wood_rows]
                + [
                    row["elset_name"]
                    for row in steel_mesh_rows
                    if not (rigid_nuts_reserved and row["component_role"] == NUT_ROLE)
                ],
                "nut_rigid_body_candidate_elsets": nut_elsets
                if rigid_nuts_reserved
                else [],
                "unassigned_nut_elsets": nut_elsets if rigid_nuts_reserved else [],
                "rigid_body_cards_emitted": False,
                "fragment_sha256": _sha256_bytes(fragment.encode("utf-8")),
                "inp_fragment": fragment,
            }

    source_inventory_binding = {
        "path": SOURCE_INVENTORY_PATH,
        "sha256": source_inventory_sha,
        "pinned_by_input_candidate_sha256": candidate["source_inventory_sha256"],
        "pinned_by_geometry_binding_sha256": inventory["geometry_binding"][
            "source_inventory_sha256"
        ],
        "source_commit": source_inventory.get("source_commit"),
    }
    source_documents = {
        timber_materials.SOURCE_DOCUMENT: _source_file_binding(
            timber_materials.SOURCE_DOCUMENT,
            expected_sha256=timber_materials.SOURCE_DOCUMENT_SHA256,
        ),
        steel_materials.SOURCE_DOCUMENT: _source_file_binding(
            steel_materials.SOURCE_DOCUMENT,
            expected_sha256=steel_materials.SOURCE_DOCUMENT_SHA256,
        ),
        timber_materials.CALCULIX_MANUAL_PATH: _source_file_binding(
            timber_materials.CALCULIX_MANUAL_PATH,
            expected_sha256=timber_materials.CALCULIX_MANUAL_SHA256,
        ),
    }
    helper_sources = {
        "fea/wood_joint_current_patch_materials.py": _source_file_binding(
            "fea/wood_joint_current_patch_materials.py"
        ),
        "fea/wood_joint_patch_materials.py": _source_file_binding(
            "fea/wood_joint_patch_materials.py"
        ),
        "fea/wood_joint_patch_steel_material.py": _source_file_binding(
            "fea/wood_joint_patch_steel_material.py"
        ),
    }
    mesh_worker_sources: dict[str, Any] = {}
    reported_worker_hashes = mesh.get("mesh_worker_source_sha256")
    reported_after_hashes = mesh.get("mesh_worker_source_sha256_after")
    if not isinstance(reported_worker_hashes, Mapping) or not isinstance(
        reported_after_hashes, Mapping
    ):
        raise TypeError("mesh report does not bind its worker sources")
    for relative_path, expected_hash in sorted(reported_worker_hashes.items()):
        after_hash = reported_after_hashes.get(relative_path)
        source_path = ROOT / relative_path
        if after_hash != expected_hash or not source_path.is_file():
            raise ValueError(f"mesh worker source is not stable: {relative_path}")
        actual_hash = _sha256_file(source_path)
        if actual_hash != expected_hash:
            raise ValueError(
                f"mesh worker source changed since attempt-02: {relative_path}"
            )
        mesh_worker_sources[relative_path] = {
            "sha256_before": expected_hash,
            "sha256_after": after_hash,
            "sha256_current": actual_hash,
        }
    helper_sources.update(
        {
            relative: {"path": relative, **item}
            for relative, item in mesh_worker_sources.items()
        }
    )

    result = {
        "schema": SCHEMA,
        "status": STATUS,
        "candidate": {
            "revision_id": candidate["revision_id"],
            "implementation_revision": candidate.get("implementation_revision"),
            "mesh_status": mesh["status"],
            "mesh_accepted": mesh["accepted"],
            "solver_run": mesh["native_solve_run"],
        },
        "input_bindings": {
            "inventory": {
                "path": _display_path(inventory_file),
                "sha256": inventory_sha,
            },
            "mesh_report": {"path": _display_path(mesh_file), "sha256": mesh_sha},
            "mesh_input": {
                "path": _display_path(mesh_input_file),
                "sha256": mesh_input_sha,
            },
            "source_inventory": source_inventory_binding,
        },
        "helper_and_source_bindings": {
            "helpers_and_mesh_workers": helper_sources,
            "scenario_source_documents": source_documents,
            "material_helper_expected_source_sha256": {
                "timber_scenario": timber_materials.SOURCE_DOCUMENT_SHA256,
                "steel_scenario": steel_materials.SOURCE_DOCUMENT_SHA256,
                "calculix_manual": timber_materials.CALCULIX_MANUAL_SHA256,
            },
        },
        "material_scenarios": {
            "wood": _compact_scenario(wood_scenario, material_name=WOOD_SCENARIO_NAME),
            "steel": _compact_scenario(
                steel_scenario, material_name=STEEL_SCENARIO_NAME
            ),
        },
        "elset_body_map": elset_map,
        "wood_orientation_alternatives": alternatives,
        "metal_assignment": {
            "body_count": len(steel_mesh_rows),
            "material_name": STEEL_SCENARIO_NAME,
            "scenario_id": steel_scenario["scenario_id"],
            "candidate_metal_bodies": steel_mesh_rows,
            "nut_representation_limit": NUT_GEOMETRY_LIMIT,
            "nut_role_count": 4,
            "nut_elsets": sorted(
                row["elset_name"]
                for row in steel_mesh_rows
                if row["component_role"] == NUT_ROLE
            ),
            "mutually_exclusive_branches": [
                "elastic_reference_all_16_metal_bodies",
                "nuts_reserved_for_downstream_rigid_body",
            ],
        },
        "inp_fragments": inp_fragments,
        "scope": {
            "mesh_body_elset_count": len(elset_map),
            "timber_body_count": len(wood_rows),
            "metal_role_body_count": len(steel_mesh_rows),
            "material_mapping_only": True,
            "delivered_wood_properties_verified": False,
            "delivered_metal_properties_verified": False,
            "strength_or_capacity_claim": False,
            "contact_or_tie_cards_emitted": False,
            "load_or_restraint_cards_emitted": False,
            "rigid_body_cards_emitted": False,
            "native_solve_run": False,
            "limitations": list(LIMITATIONS),
        },
    }
    result = _plain(result)
    result["record_sha256"] = _canonical_sha256(result)
    return result
