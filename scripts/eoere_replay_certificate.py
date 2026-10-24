"""Validate issued plywood replay results without reading files or solving."""

from __future__ import annotations

import math
import re
from collections.abc import Mapping
from pathlib import PurePosixPath
from typing import Any

SCHEMA = "eoere_leg_header_plywood_raw_operator_audit/v1"
BONDED_MEMBERS = frozenset(("eoere_cleat_left", "eoere_cleat_right"))
FLAGS = {
    "all_unchanged_owner_map_checks_retained": True,
    "field_q_actions_or_operators_changed": False,
    "physical_stiffness_qualified": False,
    "production_admission_issued": False,
}
CERTIFICATE_KEYS = frozenset(("schema", "field", "material", "source", "captured_launcher",
                              "raw_operator_checks", *FLAGS))


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def validate_reference(binding: Mapping[str, Any]) -> None:
    """Require the minimal repository-relative path/SHA record; do no I/O."""
    require(isinstance(binding, Mapping) and set(binding) == {"path", "sha256"},
            "minimal path/SHA reference required")
    path, digest = binding["path"], binding["sha256"]
    require(isinstance(path, str) and bool(PurePosixPath(path).parts)
            and not PurePosixPath(path).is_absolute() and ".." not in PurePosixPath(path).parts
            and "\\" not in path and str(PurePosixPath(path)) == path,
            "canonical repository-relative reference required")
    require(isinstance(digest, str) and re.fullmatch(r"[a-f0-9]{64}", digest) is not None,
            "lowercase SHA-256 reference required")


def bonded_plywood_dofs(operator_manifest: Mapping[str, Any]) -> dict[str, int]:
    """Derive expected audit sizes from an already hash-bound captured manifest.

    The caller authenticates the manifest bytes against its field before using
    this pure helper. This checks the two bonded analysis hosts, not physical
    plywood stiffness or the numerical entries of the captured operator.
    """
    require(isinstance(operator_manifest, Mapping)
            and operator_manifest.get("schema") == "eoere_first_order_original_operator_bundle/v1",
            "issued captured operator manifest required")
    coordinates = operator_manifest.get("coordinate_map")
    require(isinstance(coordinates, Mapping)
            and coordinates.get("schema") == "eoere_first_order_owned_coordinate_map/v1",
            "issued captured coordinate map required")
    timber = coordinates.get("timber")
    require(isinstance(timber, Mapping)
            and {name for name in timber if isinstance(name, str) and name.startswith("eoere_cleat_")}
            == BONDED_MEMBERS, "exact two bonded plywood maps required")
    ndof = operator_manifest.get("final_ndof")
    require(type(ndof) is int and ndof > 0, "captured operator DOF census required")
    result, occupied = {}, set()
    for member in sorted(BONDED_MEMBERS):
        row = timber[member]
        require(isinstance(row, Mapping), "captured plywood map required: " + member)
        source, index = row.get("source"), row.get("index")
        require(isinstance(source, Mapping) and source.get("name") == member
                and isinstance(source.get("explicit_plywood_operator"), Mapping)
                and bool(source["explicit_plywood_operator"]),
                "own explicit plywood source required: " + member)
        require(isinstance(index, list) and len(index) >= 2
                and all(isinstance(node, list) and len(node) == 6 for node in index),
                "six captured coordinates per plywood station required: " + member)
        flattened = [dof for node in index for dof in node]
        require(all(type(dof) is int and 0 <= dof < ndof for dof in flattened),
                "valid captured plywood DOF indices required: " + member)
        require(len(set(flattened)) == len(flattened) and occupied.isdisjoint(flattened),
                "distinct captured plywood DOF indices required: " + member)
        occupied.update(flattened)
        result[member] = len(flattened)
    return result


def validate_plywood_replay(
    certificate: Mapping[str, Any],
    *,
    field_ref: Mapping[str, Any],
    material_ref: Mapping[str, Any],
    expected_dofs: Mapping[str, int],
) -> None:
    """Admit the issued certificate for one explicit field and material."""
    require(isinstance(certificate, Mapping) and set(certificate) == CERTIFICATE_KEYS,
            "exact issued plywood replay fields required")
    require(certificate.get("schema") == SCHEMA, "issued plywood replay schema required")
    for binding in (field_ref, material_ref, *(certificate[key] for key in
                     ("field", "material", "source", "captured_launcher"))):
        validate_reference(binding)
    require(certificate.get("field") == field_ref, "plywood replay field binding differs")
    require(certificate.get("material") == material_ref, "plywood replay material binding differs")
    for flag, expected in FLAGS.items():
        require(certificate[flag] is expected, "plywood replay claim changed: " + flag)
    require(
        isinstance(expected_dofs, Mapping)
        and set(expected_dofs) == BONDED_MEMBERS
        and all(type(count) is int and count > 0 for count in expected_dofs.values()),
        "exact expected bonded-member DOF mapping required",
    )
    rows = certificate.get("raw_operator_checks")
    require(isinstance(rows, list) and len(rows) == len(expected_dofs),
            "one plywood operator check per bonded member required")
    seen = set()
    for row in rows:
        require(isinstance(row, Mapping) and set(row) == {"member", "dofs", "maximum_K_entry_error"},
                "exact issued plywood operator check required")
        member = row.get("member")
        require(isinstance(member, str) and member in expected_dofs and member not in seen,
                "distinct expected plywood operator members required")
        require(type(row.get("dofs")) is int and row["dofs"] == expected_dofs[member],
                "plywood operator DOFs differ from captured manifest: " + member)
        error = row.get("maximum_K_entry_error")
        require(type(error) in (int, float) and 0 <= error < 1e-6 and math.isfinite(error),
                "finite nonnegative plywood operator error below 1e-6 required: " + member)
        seen.add(member)
