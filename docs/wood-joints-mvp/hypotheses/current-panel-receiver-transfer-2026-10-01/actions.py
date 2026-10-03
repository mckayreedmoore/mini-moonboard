#!/usr/bin/env python3
"""Join frozen panel screw resultants to their panel and receiver bodies.

This is a source-bound force and MPC generalized-load reconstruction. It does
not establish Hillman screw properties, physical contact pressure, capacity,
or complete-joint acceptance.
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import math
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
CANDIDATE = "compact-floor-flush-wood-joints-development"
REVISION = "led-clearance-2x6-runner-seated-blocks-v1"
CASES = ("a12-rear", "a1-rear", "k12-rear")
LOAD_FACTORS = (0.1, 0.2, 0.3, 0.45, 0.675, 0.925, 1.0)
LATERAL = "panel_screw_lateral_plane"
WITHDRAWAL = "non_qualifying_parametric_screw_withdrawal"
CONTACT = "timber_or_panel_contact"
HILLMAN_DIAGNOSTIC = "non-qualifying diagnostic only"
FORCE_TOL = 1e-7
MOMENT_TOL = 1e-5

UPPER_ACTIONS_PATH = HERE.parent / "upper-outer-load-path-2026-10-01" / "actions.py"
NODAL_TRANSFER_PATH = (
    HERE.parent / "upper-outer-load-path-2026-10-01" / "nodal_transfer.py"
)
INVENTORY_PATH = HERE / "inventory.py"
SHARED_INVENTORY_SOURCE_REPORTS = (
    (
        "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/"
        "current-full-frame-input-manifest-attempt04/current-full-frame-input-manifest.json"
    ),
    (
        "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/"
        "receiver-screen-attempt04.json"
    ),
    (
        "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/"
        "complete-contact-graph-attempt02.json"
    ),
)


class SourceRefusal(ValueError):
    """An input pin, source gate, or cross-source join is not exact."""


def _module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise SourceRefusal(f"cannot import source helper: {path}")
    value = importlib.util.module_from_spec(spec)
    sys.modules[name] = value
    spec.loader.exec_module(value)
    return value


UPPER = _module(UPPER_ACTIONS_PATH, "panel_transfer_upper_actions")
NODAL = _module(NODAL_TRANSFER_PATH, "panel_transfer_nodal_transfer")


def _finite(value: Any, label: str) -> float:
    try:
        return UPPER._finite_number(value, label)
    except UPPER.SourceRefusal as exc:
        raise SourceRefusal(str(exc)) from exc


def _vec(value: Any, label: str) -> list[float]:
    try:
        return UPPER._vector(value, label)
    except UPPER.SourceRefusal as exc:
        raise SourceRefusal(str(exc)) from exc


def _close(a: list[float], b: list[float], tolerance: float, label: str) -> None:
    try:
        UPPER._require_close(a, b, tolerance, label)
    except UPPER.SourceRefusal as exc:
        raise SourceRefusal(str(exc)) from exc


def _load_json(path: Path) -> Any:
    return UPPER.load_json(path)


def _record_pin(
    root: Path, relative: str, expected: str | None = None
) -> dict[str, Any]:
    path = root / relative
    if not path.is_file():
        raise SourceRefusal(f"required source is missing: {relative}")
    raw = path.read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    if expected is not None and digest != expected:
        raise SourceRefusal(f"pinned source changed: {relative}")
    return {"path": relative, "sha256": digest, "size_bytes": len(raw)}


def _pins(root: Path, upper_joints: dict[str, Any]) -> dict[str, Any]:
    rows = [
        _record_pin(root, path, digest)
        for path, digest in sorted(UPPER.PINNED_SHA256.items())
    ]
    for case in CASES:
        source = UPPER._expected_sources(upper_joints, case).get("all_body_audit")
        if not isinstance(source, dict):
            raise SourceRefusal(f"{case} has no pinned independent all-body audit")
        rows.append(_record_pin(root, source["path"], source["sha256"]))
    # These source helpers define the unchanged source gates and MPC mapping.
    for path in (Path(__file__).resolve(), UPPER_ACTIONS_PATH, NODAL_TRANSFER_PATH):
        relative = path.relative_to(ROOT).as_posix()
        rows.append(_record_pin(root, relative))
    by_path: dict[str, dict[str, Any]] = {}
    for row in rows:
        previous = by_path.setdefault(row["path"], row)
        if previous != row:
            raise SourceRefusal(f"conflicting source pin: {row['path']}")
    return {"sources": [by_path[key] for key in sorted(by_path)]}


def _pin_shared_inventory_source_reports(
    root: Path, case: str, model: dict[str, Any]
) -> list[dict[str, Any]]:
    """Check inventory-shared report bytes against each native model snapshot."""
    hashes = model.get("source_geometry_hashes")
    if not isinstance(hashes, dict):
        raise SourceRefusal(f"{case} model has no source_geometry_hashes")
    pins = []
    for relative in SHARED_INVENTORY_SOURCE_REPORTS:
        expected = hashes.get(relative)
        if (
            not isinstance(expected, str)
            or len(expected) != 64
            or any(character not in "0123456789abcdef" for character in expected)
        ):
            raise SourceRefusal(
                f"{case} model has no valid source_geometry_hashes entry for {relative}"
            )
        pins.append(_record_pin(root, relative, expected))
    return pins


def _axes(inventory: dict[str, Any]) -> dict[str, dict[str, Any]]:
    if (
        inventory.get("schema")
        != "wood_joint_current_panel_receiver_transfer_inventory/v1"
        or inventory.get("candidate") != CANDIDATE
        or inventory.get("geometry_revision_id") != REVISION
    ):
        raise SourceRefusal("current panel receiver inventory identity changed")
    rows = inventory.get("axes")
    if not isinstance(rows, list):
        raise SourceRefusal("current panel receiver inventory has no axis list")
    result = {}
    for row in rows:
        axis_id = row.get("axis_id") if isinstance(row, dict) else None
        if not isinstance(axis_id, str) or not axis_id or axis_id in result:
            raise SourceRefusal(
                "current panel receiver inventory has a missing or duplicate axis ID"
            )
        for key in ("panel_member", "receiver_member"):
            if not isinstance(row.get(key), str) or not row[key]:
                raise SourceRefusal(f"axis {axis_id} has no {key}")
        origin = _vec(
            row.get("origin_global_xyz_mm"), f"axis {axis_id} inventory origin"
        )
        direction = _vec(row.get("axis_global_xyz"), f"axis {axis_id} inventory axis")
        if abs(UPPER.norm(direction) - 1.0) > 1e-8:
            raise SourceRefusal(
                f"axis {axis_id} inventory direction is not unit length"
            )
        result[axis_id] = {**row, "origin_global_xyz_mm": origin}
    if len(result) != 66:
        raise SourceRefusal(f"expected 66 current panel/kicker axes, got {len(result)}")
    return dict(sorted(result.items()))


def _scenario(model: dict[str, Any], case: str) -> dict[str, Any]:
    connection = model.get("connection_scenario", {})
    scenario = model.get("scenario", {})
    if connection.get("hillman_physical_stiffness_bounds_established") is not False:
        raise SourceRefusal(
            f"{case} source model changed the Hillman stiffness boundary"
        )
    if scenario.get("hillman_ratio_status") != HILLMAN_DIAGNOSTIC:
        raise SourceRefusal(
            f"{case} source model changed the Hillman diagnostic status"
        )
    ratio = connection.get("hillman_axial_to_lateral_ratio")
    if ratio != 1.0:
        raise SourceRefusal(f"{case} source diagnostic ratio changed")
    return {
        "hillman_physical_stiffness_bounds_established": False,
        "hillman_ratio_status": HILLMAN_DIAGNOSTIC,
        "hillman_axial_to_lateral_ratio_source_value": ratio,
        "ratio_is_not_a_hillman_property": True,
    }


def _target_components(
    model: dict[str, Any],
) -> tuple[dict[str, dict[str, Any]], dict[str, dict[str, Any]]]:
    lateral: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in model.get("springs", []):
        if row.get("role") == LATERAL:
            owner = row.get("physical_owner", {})
            if owner.get("role") != LATERAL:
                raise SourceRefusal("lateral SPRING2 has an incorrect owner role")
            lateral[owner.get("axis_id")].append(row)
    lateral_by_axis = {}
    for axis_id, rows in lateral.items():
        if len(rows) != 2 or {row.get("connector_local_dof") for row in rows} != {2, 3}:
            raise SourceRefusal(
                f"axis {axis_id} does not have local lateral DOFs 2 and 3"
            )
        if any(row.get("intended_law") != "bilateral" for row in rows):
            raise SourceRefusal(f"axis {axis_id} lateral source law changed")
        if len({row.get("name") for row in rows}) != 1:
            raise SourceRefusal(f"axis {axis_id} lateral source names disagree")
        lateral_by_axis[axis_id] = sorted(
            rows, key=lambda item: item["connector_local_dof"]
        )

    withdrawal_by_axis = {}
    for row in model.get("unilateral_springa_bindings", []):
        owner = row.get("physical_owner", {})
        if owner.get("role") != WITHDRAWAL:
            continue
        axis_id = owner.get("axis_id")
        if not isinstance(axis_id, str) or axis_id in withdrawal_by_axis:
            raise SourceRefusal("withdrawal SPRINGA has a missing or duplicate axis ID")
        if (
            row.get("force_law") != "k * max(q_mm, 0)"
            or row.get("source_projection_dof") != 1
        ):
            raise SourceRefusal(
                f"axis {axis_id} withdrawal source law or projection changed"
            )
        withdrawal_by_axis[axis_id] = row
    lateral_ids = [
        row.get("source_row_id") for rows in lateral_by_axis.values() for row in rows
    ]
    withdrawal_ids = [row.get("source_row_id") for row in withdrawal_by_axis.values()]
    if len(lateral_ids) != len(set(lateral_ids)) or len(withdrawal_ids) != len(
        set(withdrawal_ids)
    ):
        raise SourceRefusal(
            "source SPRING2/SPRINGA row IDs are reused across panel axes"
        )
    return lateral_by_axis, withdrawal_by_axis


def _source_signature(
    axis_id: str, lateral: list[dict[str, Any]], withdrawal: dict[str, Any]
) -> dict[str, Any]:
    owner = lateral[0]["physical_owner"]
    axial_owner = withdrawal["physical_owner"]
    if (
        owner.get("axis_id") != axis_id
        or axial_owner.get("axis_id") != axis_id
        or owner.get("first") != axial_owner.get("second")
        or owner.get("second") != axial_owner.get("first")
    ):
        raise SourceRefusal(
            f"axis {axis_id} lateral and withdrawal endpoint owners disagree"
        )
    return {
        "panel_member": owner["first"],
        "receiver_member": owner["second"],
        "lateral_name": lateral[0]["name"],
        "withdrawal_name": withdrawal["name"],
        "lateral_source_row_ids": [row["source_row_id"] for row in lateral],
        "withdrawal_source_row_id": withdrawal["source_row_id"],
        "lateral_point": owner["point"],
        "withdrawal_point": axial_owner["point"],
        "force_basis": owner["force_basis"],
        "withdrawal_scalar_normal": axial_owner["scalar_normal"],
        "lateral_stiffness_n_per_mm": [row["stiffness_n_per_mm"] for row in lateral],
        "withdrawal_stiffness_n_per_mm": withdrawal["stiffness_n_per_mm"],
        "withdrawal_force_law": withdrawal["force_law"],
    }


def _datums(
    axis: dict[str, Any], role: str, point: list[float], direction: list[float]
) -> dict[str, Any]:
    origin = axis["origin_global_xyz_mm"]
    inv_axis = UPPER.unit(_vec(axis["axis_global_xyz"], "inventory screw axis"))
    native_axis = UPPER.unit(_vec(direction, "native screw axis"))
    cosine = UPPER.dot(inv_axis, native_axis)
    if abs(abs(cosine) - 1.0) > 1e-8:
        raise SourceRefusal(
            f"axis {axis['axis_id']} {role} direction differs from current inventory"
        )
    offset = UPPER.sub(point, origin)
    along = UPPER.dot(offset, inv_axis)
    transverse = UPPER.sub(offset, UPPER.scale(inv_axis, along))
    if UPPER.norm(transverse) > 1e-5:
        raise SourceRefusal(
            f"axis {axis['axis_id']} {role} application point is off the axis"
        )
    return {
        "role": role,
        "native_application_point_xyz_mm": point,
        "native_direction_global_xyz": native_axis,
        "native_direction_dot_inventory_axis": cosine,
        "native_minus_inventory_origin_xyz_mm": offset,
        "signed_axial_offset_mm": along,
        "transverse_offset_mm": UPPER.norm(transverse),
    }


def _wrench_at_endpoint(
    row: dict[str, Any], body: str, datum: list[float]
) -> dict[str, Any]:
    point = UPPER._point_for_endpoint(row, body)
    force = UPPER._force_for_endpoint(row, body)
    radius = _vec(row.get("force_rounding_radius_xyz_n"), "connection force radius")
    return {
        "point_xyz_mm": point,
        "force_xyz_n": force,
        "force_radius_xyz_n": radius,
        "wrench_at_body_centroid": UPPER.wrench_at_point(point, force, radius, datum),
    }


def _lateral_components(
    axis_id: str,
    springs: list[dict[str, Any]],
    response_components: dict[str, dict[str, Any]],
    row: dict[str, Any],
) -> tuple[list[dict[str, Any]], list[float], list[float]]:
    expected_ids = [spring["source_row_id"] for spring in springs]
    if (
        set(row.get("source_row_ids", [])) != set(expected_ids)
        or len(row.get("source_row_ids", [])) != 2
    ):
        raise SourceRefusal(f"axis {axis_id} lateral source row membership changed")
    basis = springs[0]["physical_owner"]["force_basis"]
    if len(basis) != 3:
        raise SourceRefusal(f"axis {axis_id} lateral force basis changed")
    basis = [_vec(vector, "lateral source force basis") for vector in basis]
    components = []
    force, radius_vector = [0.0] * 3, [0.0] * 3
    for spring in springs:
        source_id = spring["source_row_id"]
        component = response_components.get(source_id)
        if component is None:
            raise SourceRefusal(
                f"axis {axis_id} is missing lateral source component {source_id}"
            )
        if (
            component.get("source_group") != spring.get("group")
            or component.get("element") != spring.get("element")
            or component.get("source_row_id") != source_id
        ):
            raise SourceRefusal(
                f"axis {axis_id} lateral response component identity changed for {source_id}"
            )
        if (
            component.get("rf_action_reaction_passed") is not True
            or component.get("rf_kdu_intervals_intersect") is not True
        ):
            raise SourceRefusal(
                f"axis {axis_id} lateral source gates changed for {source_id}"
            )
        scalar = _finite(
            component.get("force_on_first_local_N"), f"{source_id} signed lateral force"
        )
        radius = _finite(
            component.get("force_rounding_radius_local_N"),
            f"{source_id} lateral radius",
        )
        if radius < 0:
            raise SourceRefusal(f"axis {axis_id} has a negative lateral radius")
        direction = basis[spring["connector_local_dof"] - 1]
        force = UPPER.add(force, UPPER.scale(direction, scalar))
        radius_vector = UPPER.add(
            radius_vector, [abs(value) * radius for value in direction]
        )
        components.append(
            {
                "source_row_id": source_id,
                "local_dof": spring["connector_local_dof"],
                "source_law": spring["intended_law"],
                "source_stiffness_n_per_mm": spring["stiffness_n_per_mm"],
                "signed_force_on_first_local_n": scalar,
                "force_rounding_radius_local_n": radius,
                "relative_displacement_mm": component["relative_displacement_mm"],
                "bilateral_kdu_n": component["bilateral_kdu_N"],
                "rf_action_reaction_passed": True,
                "rf_kdu_intervals_intersect": True,
            }
        )
    _close(
        force,
        _vec(row["force_on_first_xyz_n"], "lateral row force"),
        FORCE_TOL,
        f"axis {axis_id} local lateral scalars to native vector",
    )
    _close(
        radius_vector,
        _vec(row["force_rounding_radius_xyz_n"], "lateral row radius"),
        1e-10,
        f"axis {axis_id} lateral scalar intervals to native radius",
    )
    return components, force, radius_vector


def _withdrawal_component(
    axis_id: str,
    binding: dict[str, Any],
    response_components: dict[str, dict[str, Any]],
    row: dict[str, Any],
) -> tuple[dict[str, Any], list[float], list[float]]:
    source_id = binding["source_row_id"]
    if row.get("source_row_ids") != [source_id]:
        raise SourceRefusal(f"axis {axis_id} withdrawal source row membership changed")
    component = response_components.get(source_id)
    if component is None:
        raise SourceRefusal(
            f"axis {axis_id} is missing withdrawal source component {source_id}"
        )
    if (
        component.get("source_group") != binding.get("group")
        or component.get("element") != binding.get("source_element")
        or component.get("source_row_id") != source_id
    ):
        raise SourceRefusal(
            f"axis {axis_id} withdrawal response component identity changed"
        )
    gates = (
        "native_endpoint_action_reaction_passed",
        "table_force_interval_intersects_native_rf",
        "inside_table_domain_including_rounding",
        "numerical_ground_rf_excluded_from_physical_balance",
    )
    if component.get("intended_source_law") != "tension_only" or any(
        component.get(key) is not True for key in gates
    ):
        raise SourceRefusal(f"axis {axis_id} withdrawal source law or gates changed")
    scalar = _finite(
        component.get("native_endpoint_internal_force_N"), "withdrawal source force"
    )
    radius = _finite(
        component.get("native_endpoint_internal_radius_N"), "withdrawal force radius"
    )
    if scalar < 0 or radius < 0:
        raise SourceRefusal(
            f"axis {axis_id} withdrawal source force/radius is negative"
        )
    normal = UPPER.unit(
        _vec(binding["physical_owner"]["scalar_normal"], "withdrawal source normal")
    )
    force = UPPER.scale(normal, scalar)
    radius_vector = [abs(value) * radius for value in normal]
    _close(
        force,
        _vec(row["force_on_first_xyz_n"], "withdrawal row force"),
        FORCE_TOL,
        f"axis {axis_id} tension-only scalar to native vector",
    )
    _close(
        radius_vector,
        _vec(row["force_rounding_radius_xyz_n"], "withdrawal row radius"),
        1e-10,
        f"axis {axis_id} withdrawal scalar interval to native radius",
    )
    summary = {
        "source_row_id": source_id,
        "source_law": "tension_only",
        "source_force_law": binding["force_law"],
        "source_stiffness_n_per_mm": binding["stiffness_n_per_mm"],
        "table_domain_mm": binding["table_domain_mm"],
        "force_vs_elongation_table_n_mm": binding["force_vs_elongation_table_N_mm"],
        "native_internal_force_n": scalar,
        "native_internal_radius_n": radius,
        "native_table_force_interval_n": component["native_table_force_interval_N"],
        "native_endpoint_action_reaction_passed": True,
        "table_force_interval_intersects_native_rf": True,
        "numerical_ground_rf_excluded_from_physical_balance": True,
    }
    return summary, force, radius_vector


def _transfer_scalars(
    row: dict[str, Any],
    body: str,
    source_rows: list[dict[str, Any]],
    components: dict[str, dict[str, Any]],
    role: str,
):
    first = row["first"] == body
    if not first and row["second"] != body:
        raise SourceRefusal(f"{body} is not an endpoint of {row.get('name')}")
    sign, position = (1.0, 0) if first else (-1.0, 1)
    result = []
    for source in source_rows:
        component = components[source["source_row_id"]]
        if role == LATERAL:
            node, dof = source["nodes"][position], source["dof"]
            force = component["force_on_first_local_N"]
            radius = component["force_rounding_radius_local_N"]
        else:
            node = source["source_projection_nodes"][position]
            dof = source["source_projection_dof"]
            force = component["native_endpoint_internal_force_N"]
            radius = component["native_endpoint_internal_radius_N"]
        result.append((NODAL.dof_key(node, dof), sign * force, radius))
    return result


def _expand_with_fixed(
    expansion: Any, key: tuple[int, int]
) -> dict[tuple[int, int], float]:
    """Expand a DOF while retaining fixed/unowned terminal keys for diagnostics."""
    cache = getattr(expansion, "_panel_fixed_expansion_cache", None)
    if cache is None:
        cache = {}
        expansion._panel_fixed_expansion_cache = cache
    visiting: set[tuple[int, int]] = set()

    def visit(target: tuple[int, int]) -> dict[tuple[int, int], float]:
        target = NODAL.dof_key(*target)
        if target in cache:
            return cache[target]
        if target in visiting:
            raise SourceRefusal(f"MPC cycle while retaining fixed key {target}")
        visiting.add(target)
        try:
            if target in expansion.fixed:
                result = {target: 1.0}
            elif target in expansion.equations:
                terms = expansion.equations[target]
                pivot = _finite(terms[0][2], "MPC pivot coefficient")
                collected: dict[tuple[int, int], list[float]] = defaultdict(list)
                for node, dof, coefficient in terms[1:]:
                    multiplier = -_finite(coefficient, "MPC coefficient") / pivot
                    for terminal, weight in visit((node, dof)).items():
                        collected[terminal].append(multiplier * weight)
                result = {
                    terminal: math.fsum(values)
                    for terminal, values in collected.items()
                }
                result = {
                    terminal: weight
                    for terminal, weight in result.items()
                    if weight != 0.0
                }
            else:
                result = {target: 1.0}
            cache[target] = result
            return result
        finally:
            visiting.remove(target)

    return visit(key)


def _expand_to_physical_owner(
    expansion: Any, key: tuple[int, int], body: str, owners: dict[int, str]
) -> tuple[dict[tuple[int, int], float], dict[tuple[int, int], float]]:
    """Diagnostic stencil stopping at the first physical-body-owned DOF."""
    cache = getattr(expansion, "_panel_owner_terminal_cache", None)
    if cache is None:
        cache = {}
        expansion._panel_owner_terminal_cache = cache
    visiting: set[tuple[int, int]] = set()

    def visit(target: tuple[int, int]):
        target = NODAL.dof_key(*target)
        cache_key = (body, target)
        if cache_key in cache:
            return cache[cache_key]
        if target in visiting:
            raise SourceRefusal(f"MPC cycle while tracing physical owner from {target}")
        visiting.add(target)
        try:
            owner = owners.get(target[0])
            if owner is not None:
                if owner != body:
                    raise SourceRefusal(
                        f"receiver expansion crosses physical ownership at {target}: {owner}"
                    )
                result = ({target: 1.0}, {})
            elif target in expansion.fixed:
                result = ({}, {target: 1.0})
            elif target in expansion.equations:
                terms = expansion.equations[target]
                pivot = _finite(terms[0][2], "MPC pivot coefficient")
                physical: dict[tuple[int, int], list[float]] = defaultdict(list)
                nonphysical: dict[tuple[int, int], list[float]] = defaultdict(list)
                for node, dof, coefficient in terms[1:]:
                    multiplier = -_finite(coefficient, "MPC coefficient") / pivot
                    child_physical, child_nonphysical = visit((node, dof))
                    for terminal, weight in child_physical.items():
                        physical[terminal].append(multiplier * weight)
                    for terminal, weight in child_nonphysical.items():
                        nonphysical[terminal].append(multiplier * weight)
                result = (
                    {
                        terminal: math.fsum(values)
                        for terminal, values in physical.items()
                    },
                    {
                        terminal: math.fsum(values)
                        for terminal, values in nonphysical.items()
                    },
                )
                result = tuple(
                    {
                        terminal: weight
                        for terminal, weight in group.items()
                        if weight != 0.0
                    }
                    for group in result
                )
            else:
                result = ({}, {target: 1.0})
            cache[cache_key] = result
            return result
        finally:
            visiting.remove(target)

    return visit(key)


def _equation_pivot_trace(
    expansion: Any, key: tuple[int, int]
) -> list[tuple[int, int]]:
    visited: set[tuple[int, int]] = set()
    visiting: set[tuple[int, int]] = set()

    def visit(target: tuple[int, int]):
        target = NODAL.dof_key(*target)
        if target in visiting or target in expansion.fixed:
            return
        terms = expansion.equations.get(target)
        if terms is None:
            return
        visiting.add(target)
        visited.add(target)
        for node, dof, _ in terms[1:]:
            visit((node, dof))
        visiting.remove(target)

    visit(key)
    return sorted(visited)


def _nodal_action_observation(
    model: dict[str, Any],
    expansion: Any,
    row: dict[str, Any],
    body: str,
    scalars: list[tuple[tuple[int, int], float, float]],
    source_rows: list[dict[str, Any]],
    include_stencils: bool,
):
    """Transpose source scalar actions without assuming zero MPC point couples.

    The shared nodal-transfer helper's point-moment assertion is appropriate for
    its reviewed block receiver path, but some panel receiver interpolations
    produce a nonzero couple about the response point. Preserve that result as
    an observation instead of suppressing it or applying the block-only gate.
    """
    terms: dict[tuple[int, int], list[float]] = defaultdict(list)
    radius_terms: dict[tuple[int, int], list[float]] = defaultdict(list)
    fixed_terms: dict[tuple[int, int], list[float]] = defaultdict(list)
    fixed_radius_terms: dict[tuple[int, int], list[float]] = defaultdict(list)
    owner_terms: dict[tuple[int, int], list[float]] = defaultdict(list)
    owner_radius_terms: dict[tuple[int, int], list[float]] = defaultdict(list)
    nonphysical_terms: dict[tuple[int, int], list[float]] = defaultdict(list)
    nonphysical_radius_terms: dict[tuple[int, int], list[float]] = defaultdict(list)
    owners = NODAL.owner_map(model)
    stencil_records = []
    for key, scalar, radius in scalars:
        scalar = _finite(scalar, "MPC source scalar force")
        radius = _finite(radius, "MPC source scalar radius")
        if radius < 0:
            raise SourceRefusal("MPC source scalar radius is negative")
        expanded = _expand_with_fixed(expansion, key)
        physical_expansion, nonphysical_expansion = _expand_to_physical_owner(
            expansion, key, body, owners
        )
        if not expanded:
            raise SourceRefusal(f"source DOF {key} has an empty retained MPC expansion")
        if expanded:
            try:
                shared_free = expansion.receiver(key, body)
            except NODAL.TransferError as exc:
                if expanded.keys() - expansion.fixed:
                    raise SourceRefusal(str(exc)) from exc
                shared_free = {}
            own_free = {
                target: weight
                for target, weight in expanded.items()
                if target not in expansion.fixed
            }
            if shared_free != own_free:
                raise SourceRefusal(
                    f"shared MPCExpansion stencil differs at source DOF {key}"
                )
        for target, weight in expanded.items():
            node, _ = target
            if target in expansion.fixed:
                fixed_terms[target].append(weight * scalar)
                fixed_radius_terms[target].append(abs(weight) * radius)
            else:
                if owners.get(node) != body:
                    raise SourceRefusal(
                        f"MPC expansion for {key} crosses physical ownership at {target}"
                    )
                terms[target].append(weight * scalar)
                radius_terms[target].append(abs(weight) * radius)
        for target, weight in physical_expansion.items():
            owner_terms[target].append(weight * scalar)
            owner_radius_terms[target].append(abs(weight) * radius)
        for target, weight in nonphysical_expansion.items():
            nonphysical_terms[target].append(weight * scalar)
            nonphysical_radius_terms[target].append(abs(weight) * radius)
        if include_stencils:
            pivots = [
                target
                for target in _equation_pivot_trace(expansion, key)
                if owners.get(target[0]) == body
            ]
            stencil_records.append(
                {
                    "source_row_id": source_rows[len(stencil_records)]["source_row_id"],
                    "source_dof_key": list(key),
                    "signed_source_force_n": scalar,
                    "source_force_radius_n": radius,
                    "recursive_terminal_dof_weights": [
                        {
                            "node": target[0],
                            "dof": target[1],
                            "weight": weight,
                            "fixed": target in expansion.fixed,
                            "physical_owner": owners.get(target[0]),
                        }
                        for target, weight in sorted(expanded.items())
                    ],
                    "physical_owner_terminal_dof_weights": [
                        {"node": target[0], "dof": target[1], "weight": weight}
                        for target, weight in sorted(physical_expansion.items())
                    ],
                    "nonphysical_terminal_dof_weights": [
                        {
                            "node": target[0],
                            "dof": target[1],
                            "weight": weight,
                            "fixed": target in expansion.fixed,
                        }
                        for target, weight in sorted(nonphysical_expansion.items())
                    ],
                    "physical_owner_pivot_equations_traversed": [
                        {
                            "node": target[0],
                            "dof": target[1],
                            "physical_owner": owners[target[0]],
                            "terms": [
                                list(term) for term in expansion.equations[target]
                            ],
                        }
                        for target in pivots
                    ],
                }
            )

    def make_cloud(
        force_terms: dict[tuple[int, int], list[float]],
        interval_terms: dict[tuple[int, int], list[float]],
    ) -> list[dict[str, Any]]:
        nodes = sorted({node for node, _ in force_terms})
        return [
            {
                "node": node,
                "point_mm": _vec(model["nodes"][str(node)], "MPC receiver node point"),
                "force_n": [math.fsum(force_terms[node, dof]) for dof in (1, 2, 3)],
                "radius_n": [math.fsum(interval_terms[node, dof]) for dof in (1, 2, 3)],
            }
            for node in nodes
        ]

    cloud = make_cloud(terms, radius_terms)
    fixed_cloud = make_cloud(fixed_terms, fixed_radius_terms)
    owner_cloud = make_cloud(owner_terms, owner_radius_terms)
    nonphysical_cloud = make_cloud(nonphysical_terms, nonphysical_radius_terms)
    side = "first" if row["first"] == body else "second"
    point = _vec(
        row.get(side + "_point", row.get("point")), "MPC response endpoint point"
    )
    force = _vec(row["force_on_" + side + "_xyz_n"], "MPC response endpoint force")
    radius = _vec(row["force_rounding_radius_xyz_n"], "MPC response force radius")
    observed = NODAL.wrench(cloud, point)
    fixed = NODAL.wrench(fixed_cloud, point)
    complete = NODAL.wrench(cloud + fixed_cloud, point)
    owner_observed = NODAL.wrench(owner_cloud, point)
    return (
        cloud,
        {"point_mm": point, "force_n": force, "radius_n": radius},
        observed,
        fixed_cloud,
        fixed,
        complete,
        owner_cloud,
        owner_observed,
        nonphysical_cloud,
        stencil_records,
    )


def _centroids(model: dict[str, Any]) -> dict[str, list[float]]:
    bodies, nodes = model.get("physical_body_nodes", {}), model.get("nodes", {})
    if len(bodies) != 50:
        raise SourceRefusal("source model physical-body inventory changed")
    output = {}
    for body, body_nodes in bodies.items():
        points = [
            _vec(nodes[str(NODAL.node_id(node))], f"{body} node point")
            for node in body_nodes
        ]
        if not points:
            raise SourceRefusal(f"source body {body} has no physical nodes")
        output[body] = [
            math.fsum(point[i] for point in points) / len(points) for i in range(3)
        ]
    return output


def _connection_transfer(
    model: dict[str, Any],
    expansion: Any,
    row: dict[str, Any],
    role: str,
    source_rows: list[dict[str, Any]],
    components: dict[str, dict[str, Any]],
    body: str,
    datum: list[float],
    include_stencils: bool,
) -> tuple[dict[str, Any], list[dict[str, Any]], list[dict[str, Any]]]:
    scalars = _transfer_scalars(row, body, source_rows, components, role)
    (
        cloud,
        point,
        observed,
        fixed_cloud,
        fixed,
        complete,
        owner_cloud,
        owner_observed,
        nonphysical_cloud,
        stencil_records,
    ) = _nodal_action_observation(
        model, expansion, row, body, scalars, source_rows, include_stencils
    )
    action = _wrench_at_endpoint(row, body, datum)
    mapped = NODAL.wrench(cloud, datum)
    expected = action["wrench_at_body_centroid"]
    fixed_at_datum = NODAL.wrench(fixed_cloud, datum)
    complete_at_datum = NODAL.wrench(cloud + fixed_cloud, datum)
    owner_at_datum = NODAL.wrench(owner_cloud, datum)
    force_residual = [
        mapped_value - value
        for mapped_value, value in zip(
            mapped["force_n"], expected["force_n"], strict=True
        )
    ]
    moment_residual = [
        mapped_value - value
        for mapped_value, value in zip(
            mapped["moment_nmm"], expected["moment_nmm"], strict=True
        )
    ]
    complete_force_residual = [
        mapped_value - value
        for mapped_value, value in zip(
            complete["force_n"], point["force_n"], strict=True
        )
    ]
    complete_moment_residual = list(complete["moment_nmm"])
    free_force_matches = (
        max((abs(value) for value in force_residual), default=0.0) <= FORCE_TOL
    )
    free_moment_matches = (
        max((abs(value) for value in observed["moment_nmm"]), default=0.0) <= MOMENT_TOL
    )
    complete_force_matches = (
        max((abs(value) for value in complete_force_residual), default=0.0) <= FORCE_TOL
    )
    complete_moment_matches = (
        max((abs(value) for value in complete_moment_residual), default=0.0)
        <= MOMENT_TOL
    )
    owner_force_residual = [
        value - expected_value
        for value, expected_value in zip(
            owner_at_datum["force_n"], expected["force_n"], strict=True
        )
    ]
    owner_moment_residual = [
        value - expected_value
        for value, expected_value in zip(
            owner_at_datum["moment_nmm"], expected["moment_nmm"], strict=True
        )
    ]
    owner_force_matches = (
        max((abs(value) for value in owner_force_residual), default=0.0) <= FORCE_TOL
    )
    owner_moment_matches = (
        max((abs(value) for value in owner_observed["moment_nmm"]), default=0.0)
        <= MOMENT_TOL
    )
    fixed_force_explains_residual = (
        max(
            (
                abs(value)
                for value in (
                    observed["force_n"][i] + fixed["force_n"][i] - point["force_n"][i]
                    for i in range(3)
                )
            ),
            default=0.0,
        )
        <= FORCE_TOL
    )
    refused = not (free_force_matches and free_moment_matches)
    action.update(
        source_role=role,
        source_name=row["name"],
        source_row_ids=list(row["source_row_ids"]),
    )
    action.update(
        {
            "body": body,
            "common_wrench_datum_xyz_mm": datum,
            "mpc_transfer_wrench_at_common_datum": mapped,
            "response_point_wrench_at_common_datum": expected,
            "mpc_minus_response_point_force_at_common_datum_n": force_residual,
            "mpc_minus_response_point_moment_at_common_datum_nmm": moment_residual,
            "mpc_transfer_wrench_about_response_attachment": observed,
            "response_point_wrench_about_response_attachment": NODAL.wrench(
                [point], point["point_mm"]
            ),
            "fixed_or_unowned_mpc_key_wrench_about_response_attachment": fixed,
            "complete_mpc_expansion_wrench_about_response_attachment": complete,
            "fixed_or_unowned_mpc_key_wrench_at_common_datum": fixed_at_datum,
            "complete_mpc_expansion_wrench_at_common_datum": complete_at_datum,
            "physical_owner_terminal_mapping_wrench_about_response_attachment": owner_observed,
            "physical_owner_terminal_mapping_wrench_at_common_datum": owner_at_datum,
            "physical_owner_terminal_mapping_force_residual_at_common_datum_n": owner_force_residual,
            "physical_owner_terminal_mapping_moment_residual_at_common_datum_nmm": owner_moment_residual,
            "physical_owner_terminal_mapping_force_matches_existing_helper_comparison": owner_force_matches,
            "physical_owner_terminal_mapping_moment_matches_existing_helper_comparison": owner_moment_matches,
            "physical_owner_terminal_mapping_matches_existing_helper_comparison": owner_force_matches
            and owner_moment_matches,
            "physical_owner_terminal_mapping_role": "PHYSICAL_BODY_ENDPOINT_PROJECTION_DIAGNOSTIC_ONLY",
            "fixed_or_unowned_mpc_terminal_count": len(nonphysical_cloud),
            "fixed_or_unowned_mpc_key_force_explains_free_force_residual": fixed_force_explains_residual,
            "mpc_force_matches_existing_helper_comparison": free_force_matches,
            "mpc_attachment_moment_matches_existing_helper_comparison": free_moment_matches,
            "complete_mpc_expansion_force_matches_response_endpoint": complete_force_matches,
            "complete_mpc_expansion_moment_matches_existing_helper_comparison": complete_moment_matches,
            "mpc_transfer_status": "REFUSED_MPC_ENDPOINT_TRANSFER_MISMATCH"
            if refused
            else "REPRODUCED_WITH_EXISTING_HELPER_COMPARISON",
        }
    )
    if refused:
        owners = NODAL.owner_map(model)
        action["refusal_diagnostic"] = {
            "native_endpoint_order": [row["first"], row["second"]],
            "receiver_member": body,
            "response_attachment_point_xyz_mm": point["point_mm"],
            "source_model_application_point_xyz_mm": source_rows[0][
                "physical_owner"
            ].get("point"),
            "common_wrench_datum_xyz_mm": datum,
            "response_endpoint_force_xyz_n": point["force_n"],
            "response_endpoint_force_radius_xyz_n": point["radius_n"],
            "expanded_physical_receiver_nodes": [
                {"node": node["node"], "point_mm": node["point_mm"]} for node in cloud
            ],
            "fixed_or_unowned_mpc_keys_excluded_from_receiver_transfer": [
                {
                    "node": node["node"],
                    "point_mm": node["point_mm"],
                    "physical_owner": owners.get(node["node"]),
                    "force_n": node["force_n"],
                    "radius_n": node["radius_n"],
                }
                for node in fixed_cloud
            ],
            "physical_owner_terminal_receiver_nodes": [
                {
                    "node": node["node"],
                    "point_mm": node["point_mm"],
                    "force_n": node["force_n"],
                    "radius_n": node["radius_n"],
                }
                for node in owner_cloud
            ],
            "nonphysical_recursive_terminal_nodes": [
                {
                    "node": node["node"],
                    "point_mm": node["point_mm"],
                    "force_n": node["force_n"],
                    "radius_n": node["radius_n"],
                }
                for node in nonphysical_cloud
            ],
            "source_mpc_dof_actions": [
                {
                    "source_row_id": source_rows[index]["source_row_id"],
                    "source_dof": source_rows[index].get(
                        "connector_local_dof",
                        source_rows[index].get("source_projection_dof"),
                    ),
                    "source_node": source_rows[index].get(
                        "nodes", source_rows[index].get("source_projection_nodes")
                    )[0 if row["first"] == body else 1],
                    "source_node_xyz_mm": model["nodes"][
                        str(
                            source_rows[index].get(
                                "nodes",
                                source_rows[index].get("source_projection_nodes"),
                            )[0 if row["first"] == body else 1]
                        )
                    ],
                    "receiver_dof_key": list(scalars[index][0]),
                    "signed_source_force_n": scalars[index][1],
                    "source_force_radius_n": scalars[index][2],
                }
                for index in range(len(source_rows))
            ],
            "mpc_minus_response_point_force_at_common_datum_n": force_residual,
            "mpc_minus_response_point_moment_at_common_datum_nmm": moment_residual,
            "mpc_moment_about_response_attachment_nmm": observed["moment_nmm"],
            "mpc_moment_radius_at_common_datum_nmm": mapped["moment_radius_nmm"],
            "response_point_moment_radius_at_common_datum_nmm": expected[
                "moment_rounding_radius_nmm"
            ],
            "mpc_moment_radius_about_response_attachment_nmm": observed[
                "moment_radius_nmm"
            ],
            "fixed_or_unowned_mpc_key_force_explains_free_force_residual": fixed_force_explains_residual,
            "complete_mpc_expansion_force_matches_response_endpoint": complete_force_matches,
            "complete_mpc_expansion_moment_matches_existing_helper_comparison": complete_moment_matches,
            "physical_owner_terminal_mapping_force_residual_at_common_datum_n": owner_force_residual,
            "physical_owner_terminal_mapping_moment_residual_at_common_datum_nmm": owner_moment_residual,
            "physical_owner_terminal_mapping_matches_existing_helper_comparison": owner_force_matches
            and owner_moment_matches,
            "force_comparison_tolerance_n": FORCE_TOL,
            "comparison_tolerance_nmm": MOMENT_TOL,
            "source_coordinate_or_mapping_error_established": False,
            "missing_physical_couple_established": False,
        }
        if include_stencils:
            action["refusal_diagnostic"]["source_mpc_expansion_stencils"] = (
                stencil_records
            )
    if point["point_mm"] != action["point_xyz_mm"]:
        _close(
            point["point_mm"],
            action["point_xyz_mm"],
            1e-9,
            f"{row['name']} native MPC attachment point",
        )
    return action, cloud, owner_cloud


def _screw_record(
    axis: dict[str, Any],
    springs: list[dict[str, Any]],
    binding: dict[str, Any],
    lateral_row: dict[str, Any],
    withdrawal_row: dict[str, Any],
    lateral_response: dict[str, dict[str, Any]],
    withdrawal_response: dict[str, dict[str, Any]],
    model: dict[str, Any],
    expansion: Any,
    centroids: dict[str, list[float]],
    load_factor: float,
    include_stencils: bool,
):
    axis_id = axis["axis_id"]
    panel, receiver = axis["panel_member"], axis["receiver_member"]
    owner = springs[0]["physical_owner"]
    if (owner["first"], owner["second"]) != (panel, receiver):
        raise SourceRefusal(f"axis {axis_id} lateral panel/receiver identity mismatch")
    if (binding["physical_owner"]["first"], binding["physical_owner"]["second"]) != (
        receiver,
        panel,
    ):
        raise SourceRefusal(
            f"axis {axis_id} withdrawal panel/receiver identity mismatch"
        )
    UPPER._check_connection_source(lateral_row["name"], lateral_row, model)
    UPPER._check_connection_source(withdrawal_row["name"], withdrawal_row, model)
    if lateral_row.get("role") != LATERAL or withdrawal_row.get("role") != WITHDRAWAL:
        raise SourceRefusal(f"axis {axis_id} source connection roles changed")
    if lateral_row.get("name") != springs[0].get("name") or withdrawal_row.get(
        "name"
    ) != binding.get("name"):
        raise SourceRefusal(
            f"axis {axis_id} source connection names do not match model components"
        )
    lateral_components, _, _ = _lateral_components(
        axis_id, springs, lateral_response, lateral_row
    )
    if any(
        item.get("intended_law") != "bilateral"
        for item in lateral_row.get("source_inventory_rows", [])
    ):
        raise SourceRefusal(f"axis {axis_id} lateral response inventory law changed")
    withdrawal_component, _, _ = _withdrawal_component(
        axis_id, binding, withdrawal_response, withdrawal_row
    )
    if any(
        item.get("intended_law") != "tension_only"
        for item in withdrawal_row.get("source_inventory_rows", [])
    ):
        raise SourceRefusal(f"axis {axis_id} withdrawal response inventory law changed")
    normal = binding["physical_owner"]["scalar_normal"]
    source_axis = springs[0]["physical_owner"]["force_basis"][0]
    datums = {
        "lateral_model_point": _datums(
            axis, "lateral model point", owner["point"], source_axis
        ),
        "withdrawal_model_point": _datums(
            axis, "withdrawal model point", binding["physical_owner"]["point"], normal
        ),
        "lateral_response_point": _datums(
            axis,
            "lateral response point",
            UPPER._point_for_endpoint(lateral_row, panel),
            source_axis,
        ),
        "withdrawal_response_point": _datums(
            axis,
            "withdrawal response point",
            UPPER._point_for_endpoint(withdrawal_row, panel),
            normal,
        ),
    }
    transfer_rows = []
    nodal = {
        panel: {LATERAL: [], WITHDRAWAL: []},
        receiver: {LATERAL: [], WITHDRAWAL: []},
    }
    physical_projection = {
        panel: {LATERAL: [], WITHDRAWAL: []},
        receiver: {LATERAL: [], WITHDRAWAL: []},
    }
    for role, row, sources, response_components in (
        (LATERAL, lateral_row, springs, lateral_response),
        (WITHDRAWAL, withdrawal_row, [binding], withdrawal_response),
    ):
        sides = {}
        for body, key in ((panel, "panel"), (receiver, "receiver")):
            action, cloud, owner_cloud = _connection_transfer(
                model,
                expansion,
                row,
                role,
                sources,
                response_components,
                body,
                centroids[body],
                include_stencils,
            )
            sides[key] = action
            nodal[body][role].extend(cloud)
            physical_projection[body][role].extend(owner_cloud)
        transfer_rows.append(
            {
                "source_role": role,
                "connection_name": row["name"],
                "source_row_ids": list(row["source_row_ids"]),
                "native_endpoint_order": [row["first"], row["second"]],
                "force_on_first_xyz_n": row["force_on_first_xyz_n"],
                "force_on_second_xyz_n": row["force_on_second_xyz_n"],
                "force_rounding_radius_xyz_n": row["force_rounding_radius_xyz_n"],
                "panel_endpoint": sides["panel"],
                "receiver_endpoint": sides["receiver"],
            }
        )
    panel_wrench = UPPER.sum_wrenches(
        [r["panel_endpoint"]["wrench_at_body_centroid"] for r in transfer_rows]
    )
    receiver_wrench = UPPER.sum_wrenches(
        [r["receiver_endpoint"]["wrench_at_body_centroid"] for r in transfer_rows]
    )
    return (
        {
            "axis_id": axis_id,
            "panel_member": panel,
            "receiver_member": receiver,
            "load_factor": load_factor,
            "geometry_application_datum_differences": datums,
            "lateral_scalar_components": lateral_components,
            "withdrawal_scalar_component": withdrawal_component,
            "withdrawal_law_status": "non-qualifying tension-only source law; not a Hillman property",
            "source_connections": transfer_rows,
            "same_state_panel_screw_wrench_at_panel_centroid": panel_wrench,
            "same_state_receiver_screw_wrench_at_receiver_centroid": receiver_wrench,
            "receiver_wrench_preserves_both_lateral_and_withdrawal": True,
        },
        nodal,
        physical_projection,
    )


def _contact_groups(
    model: dict[str, Any],
    increment: dict[str, Any],
    panel_bodies: set[str],
    centroids: dict[str, list[float]],
):
    groups: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for name, row in increment["physical_connection_forces"].items():
        if row.get("role") != CONTACT or not panel_bodies.intersection(
            (row.get("first"), row.get("second"))
        ):
            continue
        UPPER._check_connection_source(name, row, model)
        for panel in panel_bodies.intersection((row["first"], row["second"])):
            receiver = row["second"] if row["first"] == panel else row["first"]
            groups[(panel, receiver)].append(
                {
                    "source_name": name,
                    "source_row_ids": list(row["source_row_ids"]),
                    "panel_action": _wrench_at_endpoint(row, panel, centroids[panel]),
                    "receiver_action": _wrench_at_endpoint(
                        row, receiver, centroids[receiver]
                    ),
                }
            )
    result = []
    for (panel, receiver), rows in sorted(groups.items()):
        result.append(
            {
                "panel_member": panel,
                "receiver_member": receiver,
                "connection_count": len(rows),
                "source_names": [row["source_name"] for row in rows],
                "source_row_ids": [
                    source_id for row in rows for source_id in row["source_row_ids"]
                ],
                "modeled_contact_actions_on_panel": UPPER.sum_wrenches(
                    [row["panel_action"]["wrench_at_body_centroid"] for row in rows]
                ),
                "modeled_contact_actions_on_receiver": UPPER.sum_wrenches(
                    [row["receiver_action"]["wrench_at_body_centroid"] for row in rows]
                ),
                "physical_contact_pressure_established": False,
            }
        )
    return result


def _audit_snapshot(
    model: dict[str, Any],
    increment: dict[str, Any],
    audit_increment: dict[str, Any],
    affected: set[str],
):
    """Preserve the pinned parent all-body audit, including its original gates."""
    bodies = model.get("physical_body_nodes", {})
    audit_bodies = audit_increment.get("body_equilibrium", {})
    response_bodies = increment.get("physical_balance", {}).get("body_equilibrium", {})
    if (
        len(bodies) != 50
        or set(audit_bodies) != set(bodies)
        or set(response_bodies) != set(bodies)
    ):
        raise SourceRefusal(
            "source body/global audit no longer covers all 50 physical bodies"
        )
    if (
        audit_increment.get("passed") is not True
        or audit_increment.get("body_count") != 50
        or audit_increment.get("load_factor") != increment.get("load_factor")
        or audit_increment.get("time") != increment.get("time")
    ):
        raise SourceRefusal("pinned parent all-body audit gate changed")
    if audit_increment.get("numerical_grounds_counted") != 0:
        raise SourceRefusal(
            "pinned parent audit includes numerical spring ground reactions"
        )
    if set(affected) - set(bodies):
        raise SourceRefusal(
            "an affected screw/contact body is missing from the source audit"
        )
    for body in bodies:
        for source in (audit_bodies[body], response_bodies[body]):
            if (
                source.get("printed_resultants_passed") is not True
                or source.get("interval_resultants_passed") is not True
            ):
                raise SourceRefusal(f"pinned source body audit gate changed for {body}")
    audit_global = audit_increment.get("global_equilibrium", {})
    response_global = increment.get("physical_balance", {}).get(
        "global_equilibrium", {}
    )
    for source in (audit_global, response_global):
        if (
            source.get("printed_resultants_passed") is not True
            or source.get("interval_resultants_passed") is not True
        ):
            raise SourceRefusal("pinned source global audit gate changed")
    return {
        "source_audit_status": "PASS_PARENT_ALL_BODY_RESPONSE_SUMS",
        "source_all_body_count": 50,
        "source_all_body_and_global_gates_passed": True,
        "affected_body_names": sorted(affected),
        "affected_body_equilibrium": {
            body: audit_bodies[body] for body in sorted(affected)
        },
        "global_equilibrium": audit_global,
        "source_physical_tolerances_n_nmm": [0.1, 2.0],
        "source_rounding_radii_and_interval_gates_preserved": True,
        "numerical_ground_reactions_counted": False,
    }


def _state(
    model: dict[str, Any],
    response: dict[str, Any],
    audit: dict[str, Any],
    case: str,
    index: int,
    axes: dict[str, dict[str, Any]],
    signatures: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    inc, audit_inc = response["increments"][index], audit["increments"][index]
    factor = _finite(inc["load_factor"], "load factor")
    if factor != LOAD_FACTORS[index]:
        raise SourceRefusal(f"{case} increment {index} load factor changed")
    for gate in UPPER.INCREMENT_GATES:
        if inc.get(gate) is not True:
            raise SourceRefusal(f"{case} increment {index} failed source gate {gate}")
    scenario = _scenario(model, case)
    lateral_model, withdrawal_model = _target_components(model)
    if set(lateral_model) != set(axes) or set(withdrawal_model) != set(axes):
        raise SourceRefusal(f"{case} model screw role axis inventory changed")
    force_rows = inc.get("physical_connection_forces", {})
    lateral_rows, withdrawal_rows = {}, {}
    for name, source_row in force_rows.items():
        row = {**source_row, "name": name}
        role, axis_id = row.get("role"), row.get("axis_id")
        if role == LATERAL:
            if axis_id in lateral_rows:
                raise SourceRefusal(
                    f"{case} has duplicate lateral response for {axis_id}"
                )
            lateral_rows[axis_id] = row
        elif role == WITHDRAWAL:
            if axis_id in withdrawal_rows:
                raise SourceRefusal(
                    f"{case} has duplicate withdrawal response for {axis_id}"
                )
            withdrawal_rows[axis_id] = row
    if set(lateral_rows) != set(axes) or set(withdrawal_rows) != set(axes):
        raise SourceRefusal(
            f"{case} response does not join all 66 current axes by both roles"
        )
    lateral_components = NODAL.unique(
        inc.get("retained_bilateral_spring2_components", []), "source_row_id"
    )
    withdrawal_components = NODAL.unique(
        inc.get("springa_components", []), "source_row_id"
    )
    centroids = _centroids(model)
    expansion = NODAL.MPCExpansion(
        model["equations"], NODAL.owner_map(model), model["fixed_nodes"]
    )
    records = []
    clouds: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    physical_projection_clouds: dict[tuple[str, str], list[dict[str, Any]]] = (
        defaultdict(list)
    )
    body_axis_ids: dict[str, set[str]] = defaultdict(set)
    affected = set()
    for axis_id, axis in axes.items():
        signature = _source_signature(
            axis_id, lateral_model[axis_id], withdrawal_model[axis_id]
        )
        if signature != signatures[axis_id]:
            raise SourceRefusal(f"{case} source model changed screw identity {axis_id}")
        record, by_endpoint, by_physical_endpoint = _screw_record(
            axis,
            lateral_model[axis_id],
            withdrawal_model[axis_id],
            lateral_rows[axis_id],
            withdrawal_rows[axis_id],
            lateral_components,
            withdrawal_components,
            model,
            expansion,
            centroids,
            factor,
            include_stencils=(index == 0),
        )
        for row in record["source_connections"]:
            for endpoint in (row["panel_endpoint"], row["receiver_endpoint"]):
                diagnostic = endpoint.get("refusal_diagnostic")
                if diagnostic is not None:
                    diagnostic.update(
                        {
                            "case": case,
                            "increment_index": index,
                            "load_factor": factor,
                            "axis_id": axis_id,
                            "source_role": row["source_role"],
                            "source_name": row["connection_name"],
                        }
                    )
        records.append(record)
        panel, receiver = record["panel_member"], record["receiver_member"]
        affected.update((panel, receiver))
        body_axis_ids[panel].add(axis_id)
        body_axis_ids[receiver].add(axis_id)
        for body in (panel, receiver):
            for role in (LATERAL, WITHDRAWAL):
                clouds[(body, role)].extend(by_endpoint[body][role])
                physical_projection_clouds[(body, role)].extend(
                    by_physical_endpoint[body][role]
                )

    panel_members = {row["panel_member"] for row in axes.values()}
    contacts = _contact_groups(model, inc, panel_members, centroids)
    for contact in contacts:
        affected.update((contact["panel_member"], contact["receiver_member"]))
    transfers = []
    for (body, role), cloud in sorted(clouds.items()):
        nodal_wrench = NODAL.wrench(cloud, centroids[body])
        actions = []
        for record in records:
            if body not in (record["panel_member"], record["receiver_member"]):
                continue
            for row in record["source_connections"]:
                if row["source_role"] == role:
                    key = (
                        "panel_endpoint"
                        if body == record["panel_member"]
                        else "receiver_endpoint"
                    )
                    actions.append(row[key])
        point_wrench = UPPER.sum_wrenches(
            [row["wrench_at_body_centroid"] for row in actions]
        )
        force_residual = [
            mapped - point
            for mapped, point in zip(
                nodal_wrench["force_n"], point_wrench["force_n"], strict=True
            )
        ]
        moment_residual = [
            mapped - point
            for mapped, point in zip(
                nodal_wrench["moment_nmm"], point_wrench["moment_nmm"], strict=True
            )
        ]
        group_force_matches = (
            max((abs(value) for value in force_residual), default=0.0) <= FORCE_TOL
        )
        group_moment_matches = (
            max((abs(value) for value in moment_residual), default=0.0) <= MOMENT_TOL
        )
        individual_force_matches = all(
            row["mpc_force_matches_existing_helper_comparison"] for row in actions
        )
        individual_moment_matches = all(
            row["mpc_attachment_moment_matches_existing_helper_comparison"]
            for row in actions
        )
        transfers.append(
            {
                "body": body,
                "endpoint_kind": "panel" if body in panel_members else "receiver",
                "source_role": role,
                "screw_axis_count": len(body_axis_ids[body]),
                "source_connection_count": len(actions),
                "point_action_wrench_at_body_centroid": point_wrench,
                "mpc_nodal_transfer_wrench_at_body_centroid": nodal_wrench,
                "mpc_minus_point_action_force_at_body_centroid_n": force_residual,
                "mpc_minus_point_action_moment_at_body_centroid_nmm": moment_residual,
                "mpc_nodal_action_entry_count": len(cloud),
                "individual_source_force_comparisons_passed": individual_force_matches,
                "individual_source_moment_comparisons_passed": individual_moment_matches,
                "group_force_comparison_passed": group_force_matches,
                "group_moment_comparison_passed": group_moment_matches,
                "whole_wrench_transfer_status": "REPRODUCED_WITH_EXISTING_HELPER_COMPARISON"
                if individual_force_matches
                and individual_moment_matches
                and group_force_matches
                and group_moment_matches
                else "REFUSED_MPC_ENDPOINT_TRANSFER_MISMATCH",
            }
        )
    physical_projection_transfers = []
    for (body, role), cloud in sorted(physical_projection_clouds.items()):
        projected_wrench = NODAL.wrench(cloud, centroids[body])
        actions = []
        for record in records:
            if body not in (record["panel_member"], record["receiver_member"]):
                continue
            for row in record["source_connections"]:
                if row["source_role"] == role:
                    key = (
                        "panel_endpoint"
                        if body == record["panel_member"]
                        else "receiver_endpoint"
                    )
                    actions.append(row[key])
        point_wrench = UPPER.sum_wrenches(
            [row["wrench_at_body_centroid"] for row in actions]
        )
        force_residual = [
            mapped - point
            for mapped, point in zip(
                projected_wrench["force_n"], point_wrench["force_n"], strict=True
            )
        ]
        moment_residual = [
            mapped - point
            for mapped, point in zip(
                projected_wrench["moment_nmm"], point_wrench["moment_nmm"], strict=True
            )
        ]
        force_matches = (
            max((abs(value) for value in force_residual), default=0.0) <= FORCE_TOL
        )
        moment_matches = (
            max((abs(value) for value in moment_residual), default=0.0) <= MOMENT_TOL
        )
        physical_projection_transfers.append(
            {
                "body": body,
                "source_role": role,
                "screw_axis_count": len(body_axis_ids[body]),
                "source_connection_count": len(actions),
                "physical_body_endpoint_projection_wrench_at_body_centroid": projected_wrench,
                "response_point_action_wrench_at_body_centroid": point_wrench,
                "projection_minus_response_force_n": force_residual,
                "projection_minus_response_moment_nmm": moment_residual,
                "force_comparison_passed": force_matches,
                "moment_comparison_passed": moment_matches,
                "mapping_status": "DIAGNOSTIC_MATCHES_EXISTING_TRANSFER_COMPARISON"
                if force_matches and moment_matches
                else "DIAGNOSTIC_MISMATCH_REQUIRES_REVIEW",
                "not_a_qualified_receiver_or_support_reaction": True,
            }
        )
    transfer_refused = any(
        endpoint["mpc_transfer_status"] == "REFUSED_MPC_ENDPOINT_TRANSFER_MISMATCH"
        for record in records
        for row in record["source_connections"]
        for endpoint in (row["panel_endpoint"], row["receiver_endpoint"])
    ) or any(
        row["whole_wrench_transfer_status"] == "REFUSED_MPC_ENDPOINT_TRANSFER_MISMATCH"
        for row in transfers
    )
    audit_snapshot = _audit_snapshot(model, inc, audit_inc, affected)
    return {
        "case": case,
        "increment_index": index,
        "load_factor": factor,
        "source_hillman_scenario": scenario,
        "panel_receiver_mpc_transfer_status": "REFUSED"
        if transfer_refused
        else "REPRODUCED",
        "screw_states": records,
        "panel_receiver_mpc_transfer_summaries": transfers,
        "physical_body_endpoint_projection_summaries": physical_projection_transfers,
        "panel_contact_receiver_summaries": contacts,
        "affected_body_names": sorted(affected),
        "source_response_and_pinned_all_body_global_audit": audit_snapshot,
    }


def _load_inventory(
    root: Path, supplied: dict[str, Any] | None
) -> tuple[dict[str, Any], dict[str, Any]]:
    if supplied is not None:
        return supplied, {"sources": []}
    relative = INVENTORY_PATH.relative_to(ROOT).as_posix()
    path = root / relative
    if not path.is_file():
        raise SourceRefusal("inventory report omitted and inventory.py is unavailable")
    report, pins = _module(path, "panel_transfer_inventory_for_actions").build_report(
        root=root
    )
    return report, pins


def build_report(
    root: Path = ROOT, inventory_report: dict[str, Any] | None = None
) -> tuple[dict[str, Any], dict[str, Any]]:
    root = Path(root).resolve()
    try:
        inventory, inventory_pins = _load_inventory(root, inventory_report)
        axes = _axes(inventory)
        UPPER.verify_pinned_sources(root)
        upper_joints = _load_json(root / UPPER.UPPER_JOINTS)
        geometry = _load_json(root / UPPER.GEOMETRY_JSON)
        UPPER._check_target_inventory(upper_joints, geometry)
        pins = _pins(root, upper_joints)
        pin_rows = {row["path"]: row for row in pins["sources"]}
        for row in inventory_pins.get("sources", []):
            if pin_rows.setdefault(row["path"], row) != row:
                raise SourceRefusal(f"conflicting inventory source pin: {row['path']}")
        pins = {"sources": [pin_rows[key] for key in sorted(pin_rows)]}

        signatures, loaded = {}, {}
        shared_source_pins = []
        for case in CASES:
            sources = UPPER._expected_sources(upper_joints, case)
            model = _load_json(root / sources["model"]["path"])
            shared_source_pins.extend(
                _pin_shared_inventory_source_reports(root, case, model)
            )
            response = _load_json(root / sources["response"]["path"])
            audit_source = sources.get("all_body_audit")
            if not isinstance(audit_source, dict):
                raise SourceRefusal(f"{case} has no independent source all-body audit")
            audit = _load_json(root / audit_source["path"])
            UPPER._check_source_state(upper_joints, geometry, case, model, response)
            if (
                audit.get("status") != "PASS_PARENT_ALL_BODY_RESPONSE_SUMS"
                or audit.get("source_model_sha256") != sources["model"]["sha256"]
                or audit.get("source_response_sha256") != sources["response"]["sha256"]
                or audit.get("physical_tolerances_N_Nmm") != [0.1, 2.0]
                or len(audit.get("increments", [])) != 7
            ):
                raise SourceRefusal(
                    f"{case} parent all-body audit binding or status changed"
                )
            lateral, withdrawal = _target_components(model)
            if set(lateral) != set(axes) or set(withdrawal) != set(axes):
                raise SourceRefusal(
                    f"{case} source model does not preserve the exact current 66 axes"
                )
            for axis_id in axes:
                signature = _source_signature(
                    axis_id, lateral[axis_id], withdrawal[axis_id]
                )
                if (signature["panel_member"], signature["receiver_member"]) != (
                    axes[axis_id]["panel_member"],
                    axes[axis_id]["receiver_member"],
                ):
                    raise SourceRefusal(
                        f"axis {axis_id} inventory/model member join changed"
                    )
                if axis_id in signatures and signatures[axis_id] != signature:
                    raise SourceRefusal(
                        f"axis {axis_id} screw source identity differs between cases"
                    )
                signatures[axis_id] = signature
            loaded[case] = (model, response, audit)

        for row in shared_source_pins:
            previous = pin_rows.setdefault(row["path"], row)
            if previous != row:
                raise SourceRefusal(
                    f"conflicting model-shared source pin: {row['path']}"
                )
        pins = {"sources": [pin_rows[key] for key in sorted(pin_rows)]}

        states = [
            _state(*loaded[case], case, index, axes, signatures)
            for case in CASES
            for index in range(len(LOAD_FACTORS))
        ]
        screw_count = sum(len(state["screw_states"]) for state in states)
        component_count = sum(
            sum(
                len(row["lateral_scalar_components"]) + 1
                for row in state["screw_states"]
            )
            for state in states
        )
        if screw_count != 1386 or component_count != 4158:
            raise SourceRefusal(
                "the 1,386 screw-state / 4,158 scalar-state join is incomplete"
            )
        endpoint_actions = [
            endpoint
            for state in states
            for screw in state["screw_states"]
            for row in screw["source_connections"]
            for endpoint in (row["panel_endpoint"], row["receiver_endpoint"])
        ]
        owner_projection_rows = [
            row
            for state in states
            for row in state["physical_body_endpoint_projection_summaries"]
        ]
        report = {
            "schema": "current_panel_receiver_actions/v1",
            "status": "SOURCE_BOUND_PANEL_SCREW_ACTION_TRANSFER_DIAGNOSTICS_ONLY",
            "panel_receiver_mpc_transfer_status": "REFUSED"
            if any(
                state["panel_receiver_mpc_transfer_status"] == "REFUSED"
                for state in states
            )
            else "REPRODUCED",
            "recursive_reduced_free_dof_mpc_transfer_status": "REFUSED"
            if any(
                state["panel_receiver_mpc_transfer_status"] == "REFUSED"
                for state in states
            )
            else "REPRODUCED",
            "candidate": CANDIDATE,
            "geometry_revision_id": REVISION,
            "inventory_report_sha256": hashlib.sha256(
                json.dumps(
                    inventory, sort_keys=True, separators=(",", ":"), allow_nan=False
                ).encode()
            ).hexdigest(),
            "producer_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            "helper_sha256": {
                "upper_actions.py": hashlib.sha256(
                    UPPER_ACTIONS_PATH.read_bytes()
                ).hexdigest(),
                "nodal_transfer.py": hashlib.sha256(
                    NODAL_TRANSFER_PATH.read_bytes()
                ).hexdigest(),
            },
            "counts": {
                "axes": 66,
                "cases": len(CASES),
                "increments_per_case": len(LOAD_FACTORS),
                "same_state_screw_records": screw_count,
                "same_state_scalar_component_records": component_count,
                "lateral_bilateral_scalar_records": 2772,
                "tension_only_withdrawal_scalar_records": 1386,
                "same_state_receiver_mpc_transfer_groups": sum(
                    len(s["panel_receiver_mpc_transfer_summaries"]) for s in states
                ),
                "same_state_physical_body_endpoint_projection_groups": sum(
                    len(s["physical_body_endpoint_projection_summaries"])
                    for s in states
                ),
                "same_state_panel_contact_receiver_groups": sum(
                    len(s["panel_contact_receiver_summaries"]) for s in states
                ),
                "pinned_all_body_global_audit_states": len(states),
                "recursive_reduced_mpc_endpoint_action_count": len(endpoint_actions),
                "recursive_reduced_mpc_transfer_refusals": sum(
                    endpoint["mpc_transfer_status"]
                    == "REFUSED_MPC_ENDPOINT_TRANSFER_MISMATCH"
                    for endpoint in endpoint_actions
                ),
                "recursive_reduced_mpc_force_refusals": sum(
                    not endpoint["mpc_force_matches_existing_helper_comparison"]
                    for endpoint in endpoint_actions
                ),
                "recursive_reduced_mpc_point_moment_refusals": sum(
                    not endpoint[
                        "mpc_attachment_moment_matches_existing_helper_comparison"
                    ]
                    for endpoint in endpoint_actions
                ),
                "physical_body_endpoint_projection_endpoint_count": len(
                    endpoint_actions
                ),
                "physical_body_endpoint_projection_endpoint_force_refusals": sum(
                    not endpoint[
                        "physical_owner_terminal_mapping_force_matches_existing_helper_comparison"
                    ]
                    for endpoint in endpoint_actions
                ),
                "physical_body_endpoint_projection_endpoint_point_moment_refusals": sum(
                    not endpoint[
                        "physical_owner_terminal_mapping_moment_matches_existing_helper_comparison"
                    ]
                    for endpoint in endpoint_actions
                ),
                "physical_body_endpoint_projection_group_count": len(
                    owner_projection_rows
                ),
                "physical_body_endpoint_projection_group_force_refusals": sum(
                    not row["force_comparison_passed"] for row in owner_projection_rows
                ),
                "physical_body_endpoint_projection_group_point_moment_refusals": sum(
                    not row["moment_comparison_passed"] for row in owner_projection_rows
                ),
            },
            "method_boundary": {
                "lateral": "Retain two signed bilateral SPRING2 source scalars at local DOFs 2 and 3 and reconstruct the native physical endpoint vector using the source force basis.",
                "withdrawal": "Retain one source tension-only SPRINGA scalar and its preserved normal. The source law and stiffness are not qualified Hillman properties.",
                "receiver_transfer": "Preserve response endpoint forces and moments at their same-state points. The recursive reduced-free-DOF MPC mapping remains REFUSED where its force or point-moment comparison fails; report omitted fixed/nonphysical terminal contributions and exact same-state residuals. A separate physical-body endpoint projection stops at first physical-owned DOFs, but remains diagnostic-only and does not establish a support reaction, receiver qualification, or acceptance.",
                "geometry_datum": "Keep source model/response application points separate from current axis inventory origin. Report signed axial offset and reject transverse disagreement.",
                "contact": "Report source modeled panel/contact receiver point actions by body. They are not pressure, physical contact qualification, or a continuous bearing claim.",
                "balance": "Preserve each pinned parent all-body audit bound to its exact model and response, including same-state affected body/global resultants, original 0.1 N / 2 Nmm gates, RF radii and interval flags; no new balance limit is applied.",
                "acceptance": "No capacity, common-strain solve, three-dimensional split, complete-joint acceptance, or release is calculated.",
            },
            "claim_boundary": {
                "hillman_physical_stiffness_established": False,
                "hillman_resistance_established": False,
                "physical_contact_pressure_established": False,
                "capacity_calculated": False,
                "common_strain_calculated": False,
                "three_dimensional_section_split_calculated": False,
                "native_solve_executed_by_this_packet": False,
                "geometry_changed": False,
                "complete_joint_accepted": False,
                "fabrication_or_climbing_release": False,
            },
            "states": states,
        }
        return report, pins
    except SourceRefusal:
        raise
    except (
        UPPER.SourceRefusal,
        NODAL.TransferError,
        KeyError,
        IndexError,
        TypeError,
        OSError,
    ) as exc:
        raise SourceRefusal(str(exc)) from exc
