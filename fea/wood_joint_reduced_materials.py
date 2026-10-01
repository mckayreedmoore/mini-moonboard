"""Bind proposal-only material frames to the frozen reduced wood/panel mesh.

This consumes the current 20-timber and 24-block source maps after their native
members are meshed.  It assigns no steel/hardware properties, panel product, or
capacity.  The returned orientation points must replace the member orientation
line in the generated deck; `CurrentStructure.deck()` currently uses its mesh
section axes for that line.
"""
from __future__ import annotations

import hashlib
import json
import math
import sys
from collections.abc import Mapping
from pathlib import Path
from typing import Any

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from fea.current_response_materials import materials as response_materials
from fea.wood_joint_patch_materials import material_scenario as block_material_scenario

EXPECTED_CANDIDATE = "compact-floor-flush-wood-joints-development"
EXPECTED_REVISION = "led-clearance-2x6-runner-seated-blocks-v1"
PANEL_IDS = frozenset((
    "kicker_left", "kicker_right", "main_lower_left", "main_lower_right",
    "main_upper_left", "main_upper_right",
))
ATTEMPT_ROOT = Path("docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/reduced-static-attempt01")
DEFAULT_MEMBER_GEOMETRY = ATTEMPT_ROOT / "member-geometry.json"
DEFAULT_MODEL_INPUTS = ATTEMPT_ROOT / "model-inputs.json"
FRAME_AXIS_ORDER = ("X", "T", "N")
PANEL_GROUP_FACTORS = (1.0, 0.83, 0.67, 0.56)
AXIS_TOL = 2e-7


class ReducedMaterialError(ValueError):
    """Raised when source material frames cannot be bound without guessing."""


def _unit(value: Any, context: str) -> np.ndarray:
    vector = np.asarray(value, dtype=float)
    if vector.shape != (3,) or not np.isfinite(vector).all():
        raise ReducedMaterialError(f"{context} must be a finite global XYZ vector")
    length = float(np.linalg.norm(vector))
    if length <= 1e-12:
        raise ReducedMaterialError(f"{context} must have nonzero length")
    return vector / length


def _source_map(root: Mapping[str, Any], key: str) -> tuple[dict[str, Any], str, str]:
    pin = root.get("inputs", {}).get(key)
    if not isinstance(pin, Mapping):
        raise ReducedMaterialError(f"member geometry is missing inputs.{key}")
    relative, expected = pin.get("path"), pin.get("sha256")
    if not isinstance(relative, str) or not isinstance(expected, str) or len(expected) != 64:
        raise ReducedMaterialError(f"member geometry inputs.{key} needs a path and SHA-256")
    path = (ROOT / relative).resolve()
    try:
        path.relative_to(ROOT)
    except ValueError as exc:
        raise ReducedMaterialError(f"Material-map path escapes the repository: {relative}") from exc
    if not path.is_file():
        raise ReducedMaterialError(f"Pinned material map does not exist: {relative}")
    observed = hashlib.sha256(path.read_bytes()).hexdigest()
    if observed != expected:
        raise ReducedMaterialError(f"Material-map SHA-256 mismatch for {relative}")
    document = json.loads(path.read_text())
    if (document.get("candidate") != EXPECTED_CANDIDATE
            or document.get("geometry_revision_id") != EXPECTED_REVISION):
        raise ReducedMaterialError(f"Material map {relative} is for another candidate/revision")
    return document, relative, observed


def _right_handed_frame(longitudinal: np.ndarray, radial: np.ndarray,
                        context: str) -> dict[str, list[float]]:
    longitudinal = _unit(longitudinal, f"{context} L")
    radial = _unit(radial, f"{context} R")
    if abs(float(longitudinal @ radial)) > 1e-7:
        raise ReducedMaterialError(f"{context} L and R axes are not orthogonal")
    tangential = np.cross(longitudinal, radial)
    tangential = _unit(tangential, f"{context} T")
    if float(np.linalg.det(np.column_stack((longitudinal, radial, tangential)))) < 1 - 1e-7:
        raise ReducedMaterialError(f"{context} L/R/T frame is not right-handed")
    return {axis: vector.tolist() for axis, vector in
            zip(("L", "R", "T"), (longitudinal, radial, tangential), strict=True)}


def _timber_ring_alternatives(row: Mapping[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    grain = row.get("conditional_grain_assignment")
    source = row.get("source_frame")
    if not isinstance(grain, Mapping) or not isinstance(source, Mapping):
        raise ReducedMaterialError(f"Timber map row {row.get('member_id')} lacks its grain/source frame")
    axes_raw = source.get("axes_global_xyz")
    components = source.get("grain_components_in_source_frame")
    if (not isinstance(axes_raw, Mapping) or set(axes_raw) != set(FRAME_AXIS_ORDER)
            or not isinstance(components, Mapping) or set(components) != set(FRAME_AXIS_ORDER)):
        raise ReducedMaterialError(f"Timber map row {row.get('member_id')} lacks X/T/N axes/components")
    axes = {key: _unit(axes_raw[key], f"{row.get('member_id')} source {key}")
            for key in FRAME_AXIS_ORDER}
    for index, first in enumerate(FRAME_AXIS_ORDER):
        for second in FRAME_AXIS_ORDER[index + 1:]:
            if abs(float(axes[first] @ axes[second])) > 1e-7:
                raise ReducedMaterialError(f"{row.get('member_id')} source X/T/N axes are not orthogonal")
    if float(np.linalg.det(np.column_stack([axes[key] for key in FRAME_AXIS_ORDER]))) < 1 - 1e-7:
        raise ReducedMaterialError(f"{row.get('member_id')} source X/T/N frame is not right-handed")
    grain_vector = _unit(grain.get("proposed_global_xyz"), f"{row.get('member_id')} proposed grain")
    rebuilt = sum(float(components[key]) * axes[key] for key in FRAME_AXIS_ORDER)
    rebuilt = _unit(rebuilt, f"{row.get('member_id')} source-frame grain")
    if abs(float(rebuilt @ grain_vector)) < 1 - 1e-7:
        raise ReducedMaterialError(f"{row.get('member_id')} source grain components disagree with global grain")

    aligned = [key for key in FRAME_AXIS_ORDER if abs(float(grain_vector @ axes[key])) > 1 - 1e-7]
    if aligned:
        if len(aligned) != 1:
            raise ReducedMaterialError(f"{row.get('member_id')} has an ambiguous source grain axis")
        transverse = [key for key in FRAME_AXIS_ORDER if key != aligned[0]]
        radial_options = [(f"ring_R_on_source_{key}", axes[key], key) for key in transverse]
    else:
        orthogonal = [key for key in FRAME_AXIS_ORDER if abs(float(grain_vector @ axes[key])) <= 1e-7]
        if len(orthogonal) != 1:
            raise ReducedMaterialError(
                f"{row.get('member_id')} source frame does not define a unique transverse reference axis"
            )
        radial_axis = orthogonal[0]
        other = [key for key in FRAME_AXIS_ORDER if key != radial_axis]
        radial_options = [
            (f"ring_R_on_source_{radial_axis}", axes[radial_axis], radial_axis),
            (f"ring_R_on_source_complement_{other[0]}_{other[1]}",
             np.cross(grain_vector, axes[radial_axis]), f"complement_of_{other[0]}_{other[1]}"),
        ]
    cases = []
    for case_id, radial, radial_source in radial_options:
        frame = _right_handed_frame(grain_vector, radial, str(row.get("member_id")))
        cases.append({"scenario_id": case_id, "source_radial_axis": radial_source,
                      "material_axes_global_xyz": frame, "source_basis": "pinned timber X/T/N frame"})
    return tuple(cases)  # type: ignore[return-value]


def _block_ring_alternatives(row: Mapping[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    source_grain = row.get("conditional_grain_assignment", {}).get("grain_direction_global_xyz")
    cases = row.get("transverse_assignment_cases")
    if not isinstance(cases, list) or len(cases) != 2:
        raise ReducedMaterialError(f"Block map row {row.get('part_id')} must retain two ring cases")
    result = []
    for case in cases:
        axes = case.get("material_axes_global_xyz")
        if not isinstance(axes, Mapping) or set(axes) != {"L", "R", "T"}:
            raise ReducedMaterialError(f"Block {row.get('part_id')} ring case lacks L/R/T axes")
        frame = _right_handed_frame(axes["L"], axes["R"], str(row.get("part_id")))
        mapped_t = _unit(axes["T"], f"{row.get('part_id')} mapped T")
        if abs(float(mapped_t @ np.asarray(frame["T"]))) < 1 - 1e-7:
            raise ReducedMaterialError(f"Block {row.get('part_id')} map T axis is not the right-handed L cross R")
        if abs(float(_unit(source_grain, "block source grain") @ np.asarray(frame["L"]))) < 1 - 1e-7:
            raise ReducedMaterialError(f"Block {row.get('part_id')} ring-case grain disagrees with its map")
        result.append({"scenario_id": case.get("scenario_id"),
                       "source_radial_axis": case.get("radial_axis_local_name"),
                       "material_axes_global_xyz": frame,
                       "source_basis": "pinned block map transverse assignment"})
    return tuple(result)  # type: ignore[return-value]


def _validate_member(mesh_member: Mapping[str, Any], descriptor: Mapping[str, Any]) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    name = descriptor["name"]
    axis = _unit(mesh_member.get("axis"), f"{name} mesh grain axis")
    u = _unit(mesh_member.get("u"), f"{name} mesh section_u")
    v = _unit(mesh_member.get("v"), f"{name} mesh section_v")
    target_axis = _unit(descriptor.get("axis"), f"{name} descriptor axis")
    target_u = _unit(descriptor.get("section_u"), f"{name} descriptor section_u")
    target_v = _unit(descriptor.get("section_v"), f"{name} descriptor section_v")
    if (float(axis @ target_axis) < 1 - AXIS_TOL
            or float(u @ target_u) < 1 - AXIS_TOL
            or float(v @ target_v) < 1 - AXIS_TOL):
        raise ReducedMaterialError(f"{name} CurrentStructure axes differ from the frozen member geometry")
    if (abs(float(axis @ u)) > 1e-7 or abs(float(axis @ v)) > 1e-7
            or abs(float(u @ v)) > 1e-7 or float(np.cross(axis, u) @ v) < 1 - 1e-7):
        raise ReducedMaterialError(f"{name} CurrentStructure member basis is not right-handed")
    return axis, u, v


def _panel_records(structure: Any, descriptors: Mapping[str, Any], assembly: Any | None) -> dict[str, Any]:
    panel_rows = descriptors.get("panels")
    if not isinstance(panel_rows, list) or {row.get("panel_id") for row in panel_rows} != PANEL_IDS:
        raise ReducedMaterialError("Frozen geometry must describe all six current panels")
    panel_by_name = {row["panel_id"]: row for row in panel_rows}
    if set(structure.panels) != PANEL_IDS:
        raise ReducedMaterialError("CurrentStructure must contain exactly the six frozen panels")
    mesh_panels = getattr(assembly, "panels", {}) if assembly is not None else {}
    if assembly is not None and set(mesh_panels) != PANEL_IDS:
        raise ReducedMaterialError("Panel assembly does not contain all six frozen panels")
    global_width = np.array([1.0, 0.0, 0.0])
    result = {}
    for name in sorted(PANEL_IDS):
        row = panel_by_name[name]
        if row.get("layup_axes_properties") != "unassigned":
            raise ReducedMaterialError(f"{name} source layup status changed; review this binder")
        panel = structure.panels[name]
        normal = _unit(panel.get("normal"), f"{name} panel normal")
        if abs(float(normal @ global_width)) > 1e-7:
            raise ReducedMaterialError(f"{name} current deck width axis is not in the panel plane")
        length_axis = _unit(np.cross(normal, global_width), f"{name} assumed panel length axis")
        source_axes_status = "assumed_only_panel_layup_unassigned"
        alignment = None
        if assembly is not None:
            geometry = mesh_panels[name].geometry
            source_u = _unit(geometry.get("axis_u_xyz"), f"{name} STEP broadface width axis")
            source_v = _unit(geometry.get("axis_v_xyz"), f"{name} STEP broadface length axis")
            source_normal = _unit(geometry.get("normal_xyz"), f"{name} STEP broadface normal")
            if abs(float(source_normal @ normal)) < 1 - 1e-7:
                raise ReducedMaterialError(f"{name} structure and STEP panel normals disagree")
            alignment = {"step_width_parallel_global_x": abs(float(source_u @ global_width)),
                         "step_length_parallel_assumed_panel_axis": abs(float(source_v @ length_axis))}
            alignment["geometry_matches_currentresponse_axis_assumption"] = (
                alignment["step_width_parallel_global_x"] > 1 - 1e-7
                and alignment["step_length_parallel_assumed_panel_axis"] > 1 - 1e-7
            )
            source_axes_status = "STEP broadface axes checked; material layup still unassigned"
        result[name] = {
            "panel_product_or_layup_identified": False,
            "source_layup_axes_properties": row["layup_axes_properties"],
            "assumed_apa_direction_1_global_xyz": global_width.tolist(),
            "assumed_apa_direction_2_global_xyz": length_axis.tolist(),
            "panel_normal_global_xyz": normal.tolist(),
            "source_axis_check": alignment,
            "axis_status": source_axes_status,
            "claim_limit": "APA conditional section fit only; actual purchased sheet and face-grain direction unresolved",
        }
    return result


def _load_frozen_geometry(value: Mapping[str, Any] | str | Path) -> tuple[dict[str, Any], str, str]:
    if isinstance(value, Mapping):
        path = ROOT / DEFAULT_MEMBER_GEOMETRY
        document = dict(value)
        pinned = json.loads(path.read_text())
        if pinned != document:
            raise ReducedMaterialError("Supplied geometry mapping differs from the frozen member-geometry.json")
    else:
        path = Path(value).resolve()
        try:
            relative = path.relative_to(ROOT)
        except ValueError as exc:
            raise ReducedMaterialError("Member-geometry path must stay inside the repository") from exc
        if relative != DEFAULT_MEMBER_GEOMETRY:
            raise ReducedMaterialError("Only the frozen reduced-static-attempt01 geometry is supported")
        document = json.loads(path.read_text())
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    return document, str(path.relative_to(ROOT)), digest


def _verify_frozen_body_set(geometry: Mapping[str, Any], geometry_path: str,
                            geometry_sha: str,
                            model_inputs: Mapping[str, Any] | str | Path | None) -> tuple[str, str]:
    path = ROOT / DEFAULT_MODEL_INPUTS
    if model_inputs is not None:
        if isinstance(model_inputs, Mapping):
            document = dict(model_inputs)
            if document != json.loads(path.read_text()):
                raise ReducedMaterialError("Supplied model-input mapping differs from the frozen 50-body artifact")
        else:
            path = Path(model_inputs).resolve()
            try:
                relative = path.relative_to(ROOT)
            except ValueError as exc:
                raise ReducedMaterialError("Model-input path must stay inside the repository") from exc
            if relative != DEFAULT_MODEL_INPUTS:
                raise ReducedMaterialError("Only the frozen reduced-static-attempt01 model-input artifact is supported")
            document = json.loads(path.read_text())
    else:
        document = json.loads(path.read_text())
    raw_hash = hashlib.sha256(path.read_bytes()).hexdigest()
    if (document.get("candidate") != EXPECTED_CANDIDATE
            or document.get("revision_id") != EXPECTED_REVISION
            or document.get("member_geometry_artifact") != geometry_path):
        raise ReducedMaterialError("Frozen 50-body model inputs do not point to this geometry/revision")
    source_pins = document.get("source_sha256")
    if not isinstance(source_pins, Mapping) or source_pins.get(geometry_path) != geometry_sha:
        raise ReducedMaterialError("Frozen model-input artifact does not pin member-geometry.json bytes")
    rows = document.get("members")
    if not isinstance(rows, list) or len(rows) != 50:
        raise ReducedMaterialError("Frozen model-input artifact must contain exactly 50 body records")
    by_name = {row.get("member_id"): row for row in rows}
    geometry_members = {row["name"]: row for row in geometry.get("members", [])}
    geometry_panels = {row["panel_id"]: row for row in geometry.get("panels", [])}
    expected_names = set(geometry_members) | set(geometry_panels)
    if len(by_name) != 50 or set(by_name) != expected_names:
        raise ReducedMaterialError("Frozen model-input body IDs differ from the 44 members plus six panels")
    for name, descriptor in geometry_members.items():
        row = by_name[name]
        if row.get("member_kind") != "timber" or row.get("reduced_geometry_descriptor") != descriptor:
            raise ReducedMaterialError(f"Frozen body record {name} differs from member-geometry.json")
    for name, descriptor in geometry_panels.items():
        row = by_name[name]
        if row.get("member_kind") != "panel" or row.get("reduced_geometry_descriptor") != descriptor:
            raise ReducedMaterialError(f"Frozen panel record {name} differs from member-geometry.json")
    return str(path.relative_to(ROOT)), raw_hash


def bind_reduced_material_scenario(
    structure: Any,
    member_geometry: Mapping[str, Any] | str | Path,
    *,
    ring_case: str = "A",
    panel_group_factor: float = 1.0,
    panel_assembly: Any | None = None,
    model_inputs: Mapping[str, Any] | str | Path | None = None,
) -> dict[str, Any]:
    """Bind one explicit R/T and APA comparison scenario to a meshed structure.

    ``ring_case`` selects the first (A) or second (B) pinned transverse frame
    per timber/block.  This is a paired sensitivity, not a claim that all boards
    share one observed ring orientation.  Call with all four existing APA group
    factors for panel sensitivity.  Must run before ``structure.layered_panels``.
    """
    if ring_case not in ("A", "B"):
        raise ReducedMaterialError("ring_case must be A or B")
    if panel_group_factor not in PANEL_GROUP_FACTORS:
        raise ReducedMaterialError(f"panel_group_factor must be one of {PANEL_GROUP_FACTORS}")
    if getattr(structure, "panel_solid_layers", False):
        raise ReducedMaterialError("Bind panel materials before CurrentStructure.layered_panels()")
    doc, geometry_path, geometry_sha = _load_frozen_geometry(member_geometry)
    if (doc.get("candidate") != EXPECTED_CANDIDATE
            or doc.get("geometry_revision_id") != EXPECTED_REVISION):
        raise ReducedMaterialError("Frozen member geometry belongs to another candidate/revision")
    model_inputs_path, model_inputs_sha = _verify_frozen_body_set(
        doc, geometry_path, geometry_sha, model_inputs)
    timber_map, timber_path, timber_sha = _source_map(doc, "timber_material_map")
    block_map, block_path, block_sha = _source_map(doc, "block_material_map")
    helper = block_map.get("material_helper")
    if (not isinstance(helper, Mapping)
            or helper.get("path") != "fea/wood_joint_patch_materials.py"
            or helper.get("sha256") != hashlib.sha256(
                (ROOT / "fea/wood_joint_patch_materials.py").read_bytes()
            ).hexdigest()):
        raise ReducedMaterialError("Pinned block-map elastic helper is missing or changed")
    frame_material_sha = hashlib.sha256(
        (ROOT / "fea/current_response_materials.py").read_bytes()
    ).hexdigest()
    descriptors = doc.get("members")
    if not isinstance(descriptors, list) or len(descriptors) != 44:
        raise ReducedMaterialError("Frozen geometry must include all 44 timber/block members")
    desc_by_name = {row.get("name"): row for row in descriptors}
    if len(desc_by_name) != 44 or None in desc_by_name:
        raise ReducedMaterialError("Frozen member names must be present and unique")
    if set(structure.members) != set(desc_by_name):
        raise ReducedMaterialError("CurrentStructure must contain exactly the 44 frozen timber/block members")
    timber_rows = {row.get("member_id"): row for row in timber_map.get("members", [])}
    block_rows = {row.get("part_id"): row for row in block_map.get("members", [])}
    if set(timber_rows) != {name for name, row in desc_by_name.items() if row.get("member_kind") == "timber"}:
        raise ReducedMaterialError("Timber map coverage differs from the 20 frozen timber members")
    if set(block_rows) != {name for name, row in desc_by_name.items() if row.get("member_kind") == "candidate_block"}:
        raise ReducedMaterialError("Block map coverage differs from the 24 frozen candidate blocks")

    # Existing source categories remain separate: Table 4A-style dimension
    # lumber basis for frame members, and the pinned block-only DF diagnostic.
    frame_constants = response_materials(panel_group_factor=panel_group_factor)["timber"]
    block_constants = tuple(block_material_scenario()["calculix_engineering_constants"])
    material_input = response_materials(panel_group_factor=panel_group_factor)
    by_member: dict[str, tuple[float, ...]] = {}
    orientations: dict[str, dict[str, Any]] = {}
    alternatives: dict[str, list[dict[str, Any]]] = {}
    for name, descriptor in sorted(desc_by_name.items()):
        mesh = structure.members[name]
        axis, u, v = _validate_member(mesh, descriptor)
        if descriptor.get("member_kind") == "timber":
            if descriptor.get("material_frame_map") != timber_path or descriptor.get("material_frame_map_sha256") != timber_sha:
                raise ReducedMaterialError(f"{name} timber map reference does not match the pinned source map")
            row = timber_rows[name]
            cases = _timber_ring_alternatives(row)
            constants = frame_constants
            category = "current_response_table4a_dimensional_lumber_scenario"
        elif descriptor.get("member_kind") == "candidate_block":
            if descriptor.get("material_frame_map") != block_path or descriptor.get("material_frame_map_sha256") != block_sha:
                raise ReducedMaterialError(f"{name} block map reference does not match the pinned source map")
            row = block_rows[name]
            cases = _block_ring_alternatives(row)
            constants = block_constants
            category = "pinned_block_only_douglas_fir_elastic_diagnostic"
        else:
            raise ReducedMaterialError(f"{name} has unsupported member_kind {descriptor.get('member_kind')!r}")
        # Grain sign is immaterial, but its axis must reproduce the member mesh.
        source_l = _unit(cases[0]["material_axes_global_xyz"]["L"], f"{name} mapped L")
        if abs(float(source_l @ axis)) < 1 - AXIS_TOL:
            raise ReducedMaterialError(f"{name} source grain does not align with its CurrentStructure member axis")
        chosen = cases[0 if ring_case == "A" else 1]
        frame = {key: _unit(value, f"{name} material {key}")
                 for key, value in chosen["material_axes_global_xyz"].items()}
        if float(frame["L"] @ axis) < 0:
            frame["L"] = -frame["L"]
            frame["T"] = -frame["T"]
        if float(frame["L"] @ frame["R"]) > 1e-7 or float(np.cross(frame["L"], frame["R"]) @ frame["T"]) < 1 - 1e-7:
            raise ReducedMaterialError(f"{name} selected material orientation is not right-handed")
        radial_alignment = abs(float(frame["R"] @ u))
        angle = math.degrees(math.acos(min(1.0, max(-1.0, radial_alignment))))
        orientation = {
            "scenario_id": chosen["scenario_id"],
            "material_category": category,
            "material_axes_global_xyz": {key: value.tolist() for key, value in frame.items()},
            "calculix_orientation_values": [*frame["L"].tolist(), *frame["R"].tolist()],
            # CalculiX 2.23 orientations.f reads only the first 20 characters
            # with F20.0. Thirteen significant digits fit even signed E-324.
            "deck_orientation_line": ",".join(format(float(value), ".13g")
                                               for value in (*frame["L"], *frame["R"])),
            "mesh_section_axes_global_xyz": {"grain": axis.tolist(), "u": u.tolist(), "v": v.tolist()},
            "radial_to_mesh_u_abs_dot": radial_alignment,
            "off_axis_from_mesh_u_degrees": angle,
            "native_currentresponse_orientation_matches": radial_alignment > 1 - AXIS_TOL,
            "explicit_orientation_override_required": radial_alignment <= 1 - AXIS_TOL,
            "source_basis": chosen["source_basis"],
            "proposal_only": True,
        }
        by_member[name] = tuple(constants)
        orientations[name] = orientation
        alternatives[name] = [{"scenario_id": case["scenario_id"],
                               "material_axes_global_xyz": case["material_axes_global_xyz"],
                               "source_basis": case["source_basis"]} for case in cases]

    panel_bindings = _panel_records(structure, doc, panel_assembly)
    # Keep current_response_materials() as the source of APA layers/targets;
    # the group factor is explicit and does not identify a purchased sheet.
    structure.materials.update(material_input)
    structure.materials["timber_by_name"] = by_member
    structure.materials["qualified_for_design"] = False
    scenario_id = f"current_nominal_ring_{ring_case.lower()}_apa_group_{PANEL_GROUP_FACTORS.index(panel_group_factor) + 1}"
    return {
        "scenario_id": scenario_id,
        "candidate": EXPECTED_CANDIDATE,
        "geometry_revision_id": EXPECTED_REVISION,
        "source_checks": {
            "member_geometry_revision": EXPECTED_REVISION,
            "frozen_model_inputs": {"path": model_inputs_path, "sha256": model_inputs_sha,
                                    "body_count": 50},
            "timber_material_map": {"path": timber_path, "sha256": timber_sha,
                                     "member_count": len(timber_rows)},
            "block_material_map": {"path": block_path, "sha256": block_sha,
                                    "member_count": len(block_rows)},
            "block_material_helper": {"path": helper["path"], "sha256": helper["sha256"]},
            "current_response_material_helper": {
                "path": "fea/current_response_materials.py", "sha256": frame_material_sha},
            "bound_member_count": len(orientations), "bound_panel_count": len(panel_bindings),
            "unassigned_body_categories": ["structural bolts", "nuts", "washers", "steel hardware"],
        },
        "material_categories": {
            "timber": {"basis": "CurrentResponse existing 1.6 Mpsi DF-L dimensional-lumber/FPL-ratio scenario",
                       "constants_source": "fea.current_response_materials.materials()['timber']",
                       "member_count": 20, "received_properties_observed": False},
            "candidate_block": {"basis": "Pinned block-map Douglas-fir elastic diagnostic",
                                "constants_source": "fea.wood_joint_patch_materials.material_scenario()",
                                "member_count": 24, "received_properties_observed": False},
            "panel": {"basis": "Existing conditional APA Group stiffness / equivalent-layer fit",
                      "group_factor": panel_group_factor,
                      "member_count": 6, "actual_product_or_layup_identified": False,
                      "capacity_or_strength_adopted": False},
        },
        "ring_case": ring_case,
        "ring_sensitivity_limit": "A/B selects the corresponding alternative on every board; individual boards may differ, and neither case is observed stock.",
        "available_alternatives": {"ring_cases": ["A", "B"],
                                    "apa_group_factors": list(PANEL_GROUP_FACTORS),
                                    "paired_comparison_count": 2 * len(PANEL_GROUP_FACTORS)},
        "scenario_role": "first comparison scenario only; no material choice or acceptance",
        "panel_group_factor": panel_group_factor,
        "orientation_overrides": orientations,
        "orientation_alternatives": alternatives,
        "panel_axes": panel_bindings,
        "panel_targets": material_input["panel_targets"],
        "qualified_for_design": False,
        "limitations": [
            "Source grain maps are conditional orientation scenarios, not measurements of delivered members.",
            "Frame lumber and candidate blocks keep their distinct source-category material scenarios.",
            "Explicit member orientation overrides must be applied to the generated deck before solving.",
            "APA equivalent layers match reference section stiffnesses only; actual sheet grade, layup, ring/face axes and capacity are unresolved.",
        ],
    }


def _demo() -> None:
    """Source-bound geometry/material smoke check; no mesh solve or solver call."""
    from fea.current_response_materials import materials
    from fea.current_response_model import CurrentStructure

    path = ROOT / "docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/reduced-static-attempt01/member-geometry.json"
    geometry = json.loads(path.read_text())
    structure = CurrentStructure(materials())
    for row in geometry["members"]:
        structure.members[row["name"]] = {
            "axis": np.asarray(row["axis"], dtype=float),
            "u": np.asarray(row["section_u"], dtype=float),
            "v": np.asarray(row["section_v"], dtype=float),
        }
    for name in PANEL_IDS:
        structure.panels[name] = {"normal": [0.0, 1.0, 0.0], "nodes": []}
    result = bind_reduced_material_scenario(structure, geometry)
    assert result["source_checks"]["bound_member_count"] == 44
    assert result["source_checks"]["bound_panel_count"] == 6
    assert len(structure.materials["timber_by_name"]) == 44
    assert result["material_categories"]["timber"]["member_count"] == 20
    assert result["material_categories"]["candidate_block"]["member_count"] == 24
    header = result["orientation_overrides"]["base_header"]
    assert header["explicit_orientation_override_required"]
    assert header["off_axis_from_mesh_u_degrees"] > 30
    assert all(len(result["orientation_alternatives"][name]) == 2 for name in structure.members)
    print(json.dumps({"scenario_id": result["scenario_id"],
                      "source_checks": result["source_checks"],
                      "base_header_off_axis_degrees": header["off_axis_from_mesh_u_degrees"],
                      "native_solver_run": False}, indent=2))


if __name__ == "__main__":
    _demo()
