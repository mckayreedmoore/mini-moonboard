"""Define diagnostic six-component WJ16 ordinary-joint unit cases.

This module authenticates the four source-bound WJ16 interface datums and
emits 48 independent signed wrench definitions. Its optional nodal
distribution helper consumes caller-selected nodes and tributary areas; it
does not select restraints, mesh patches, contact states, or run CalculiX.
Cases are method diagnostics only, with no stiffness, capacity, fresh-case,
or release claim.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from fea.wood_joint_patch_equilibrium import (
    ActionReactionCheck,
    InterfaceDatum,
    SignedPointAction,
    aggregate_interface_wrenches,
    audit_action_reaction,
)
from fea.wood_joint_patch_wrench import (
    Wrench,
    cross,
    is_equilibrated,
    shift_wrench,
    to_local,
)

ROOT = Path(__file__).resolve().parents[1]
MECHANICS_MANIFEST_PATH = "docs/wood-joints-mvp/hypotheses/wj16-full-stock-mechanics-inputs/mechanics-inputs.json"
RESPONSE_CONTRACT_PATH = "docs/wood-joints-mvp/representative-unit-response-contract.md"
SCHEMA = "wood_joint_patch_unit_cases/v1"
STATUS = "diagnostic_case_definitions_only_no_native_solve"
MECHANICS_MANIFEST_SHA256 = (
    "f21e99f55da92ea60c950eecc6707fe98ca5df47f4d019f344c16fa06b52caf9"
)
SOURCE_INVENTORY_SHA256 = (
    "07af4c3eb642cf3887595fe4415eb65404cdcf74d66c5c7bb182847ef21c2d78"
)
CANONICAL_WJ04_CONFIG_SHA256 = (
    "d1c63e1fa5617999e8af68d683cc0f3074fb84f518b048a087ec5ed276206c0e"
)

# The right-handed, common WJ04 global frame authenticated by the WJ16 input
# contract. Wrenches remain global-axis values; local components are projected
# using the same ordered axes.
WJ04_BASIS_GLOBAL: tuple[tuple[float, float, float], ...] = (
    (1.0, 0.0, 0.0),
    (0.0, 0.6427876096865394, 0.766044443118978),
    (0.0, -0.766044443118978, 0.6427876096865394),
)
COMPONENTS = ("FX", "FT", "FN", "MX", "MT", "MN")
FORCE_UNIT_N = 1.0
MOMENT_UNIT_NMM = 1.0
CASE_SIGNS = (1, -1)
EXPECTED_OWNER_PAIRS: dict[str, tuple[str, str]] = {
    "clip_horizontal_lower_right_1__rail_to_cleat": (
        "base_rail_service_lower_right",
        "wj04_lower_full_stock_cleat",
    ),
    "clip_horizontal_lower_right_1__principal_to_cleat": (
        "base_principal_center_right",
        "wj04_lower_full_stock_cleat",
    ),
    "clip_horizontal_upper_right_1__rail_to_cleat": (
        "base_rail_service_upper_right",
        "wj04_upper_g7_crosscut_full_stock_cleat",
    ),
    "clip_horizontal_upper_right_1__principal_to_cleat": (
        "base_principal_center_right",
        "wj04_upper_g7_crosscut_full_stock_cleat",
    ),
}
DEFAULT_FORCE_TOLERANCE_N = 1e-9
DEFAULT_MOMENT_TOLERANCE_NMM = 1e-8
DEFAULT_RANK_RELATIVE_TOLERANCE = 1e-12

Vector = tuple[float, float, float]
NodeId = int | str


def _vector(value: Any, label: str) -> Vector:
    if isinstance(value, (str, bytes)):
        raise TypeError(f"{label} must be a finite 3-vector")
    try:
        result = tuple(float(component) for component in value)
    except (TypeError, ValueError, OverflowError) as error:
        raise ValueError(f"{label} must be a finite 3-vector") from error
    if len(result) != 3 or not all(math.isfinite(component) for component in result):
        raise ValueError(f"{label} must be a finite 3-vector")
    return result  # type: ignore[return-value]


def _finite_positive(value: Any, label: str) -> float:
    if isinstance(value, bool):
        raise TypeError(f"{label} must be a positive finite number")
    try:
        result = float(value)
    except (TypeError, ValueError, OverflowError) as error:
        raise ValueError(f"{label} must be a positive finite number") from error
    if not math.isfinite(result) or result <= 0.0:
        raise ValueError(f"{label} must be a positive finite number")
    return result


def _finite_nonnegative(value: Any, label: str) -> float:
    if isinstance(value, bool):
        raise TypeError(f"{label} must be a finite nonnegative number")
    try:
        result = float(value)
    except (TypeError, ValueError, OverflowError) as error:
        raise ValueError(f"{label} must be a finite nonnegative number") from error
    if not math.isfinite(result) or result < 0.0:
        raise ValueError(f"{label} must be a finite nonnegative number")
    return result


def _owner_name(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label} must be a nonempty string")
    return value


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _unit(vector: Vector, label: str) -> Vector:
    norm = math.sqrt(math.fsum(component * component for component in vector))
    if not math.isfinite(norm) or norm <= 1e-12:
        raise ValueError(f"{label} must be nonzero")
    return tuple(component / norm for component in vector)  # type: ignore[return-value]


def _negate(wrench: Wrench) -> Wrench:
    return Wrench(
        tuple(0.0 if value == 0.0 else -value for value in wrench.force_n),
        tuple(0.0 if value == 0.0 else -value for value in wrench.moment_nmm),
    )


def _local_basis_wrench(component: str, sign: int) -> Wrench:
    axis_index = {"X": 0, "T": 1, "N": 2}[component[-1]]
    amount = sign * (FORCE_UNIT_N if component.startswith("F") else MOMENT_UNIT_NMM)
    axis = WJ04_BASIS_GLOBAL[axis_index]
    vector = tuple(0.0 if value == 0.0 else amount * value for value in axis)
    if component.startswith("F"):
        return Wrench(vector, (0.0, 0.0, 0.0))
    return Wrench((0.0, 0.0, 0.0), vector)


@dataclass(frozen=True)
class UnitWrenchCase:
    """One signed, single-component action/reaction diagnostic."""

    case_id: str
    interface_id: str
    component: str
    sign: int
    host_body: str
    cleat_body: str
    datum_xyz_mm: Vector
    host_wrench_global: Wrench
    cleat_wrench_global: Wrench
    host_wrench_local: Wrench

    def __post_init__(self) -> None:
        for field_name in ("case_id", "interface_id", "component"):
            _owner_name(getattr(self, field_name), field_name)
        if self.component not in COMPONENTS:
            raise ValueError(f"unknown unit-wrench component {self.component!r}")
        if type(self.sign) is not int or self.sign not in CASE_SIGNS:
            raise ValueError("unit-wrench case sign must be +1 or -1")
        host = _owner_name(self.host_body, "host body")
        cleat = _owner_name(self.cleat_body, "cleat body")
        if host == cleat:
            raise ValueError("host and cleat owner bodies must differ")
        object.__setattr__(self, "host_body", host)
        object.__setattr__(self, "cleat_body", cleat)
        object.__setattr__(self, "datum_xyz_mm", _vector(self.datum_xyz_mm, "datum"))
        if not isinstance(self.host_wrench_global, Wrench):
            raise TypeError("host wrench must use the canonical patch Wrench type")
        if not isinstance(self.cleat_wrench_global, Wrench):
            raise TypeError("cleat wrench must use the canonical patch Wrench type")
        if not isinstance(self.host_wrench_local, Wrench):
            raise TypeError("local wrench must use the canonical patch Wrench type")

    @property
    def owner_bodies(self) -> tuple[str, str]:
        return (self.host_body, self.cleat_body)


@dataclass(frozen=True)
class UnitCasePlan:
    """Authenticated, source-bound definitions for the 48 diagnostic cases."""

    source_manifest_sha256: str
    source_inventory_sha256: str
    canonical_wj04_config_sha256: str
    composition_id: str
    response_contract_sha256: str
    interface_datums: tuple[InterfaceDatum, ...]
    owner_pairs: tuple[tuple[str, tuple[str, str]], ...]
    cases: tuple[UnitWrenchCase, ...]

    def __post_init__(self) -> None:
        for name in (
            "source_manifest_sha256",
            "source_inventory_sha256",
            "canonical_wj04_config_sha256",
            "response_contract_sha256",
        ):
            value = getattr(self, name)
            if (
                not isinstance(value, str)
                or len(value) != 64
                or any(character not in "0123456789abcdef" for character in value)
            ):
                raise ValueError(f"{name} must be a lowercase SHA-256 digest")
        _owner_name(self.composition_id, "composition id")
        datum_ids = [datum.interface_id for datum in self.interface_datums]
        if len(datum_ids) != len(set(datum_ids)) or set(datum_ids) != set(
            EXPECTED_OWNER_PAIRS
        ):
            raise ValueError("plan datums must cover the four expected interfaces once")
        if len(self.cases) != 48 or len({case.case_id for case in self.cases}) != 48:
            raise ValueError("plan must contain 48 unique signed unit-wrench cases")


@dataclass(frozen=True)
class PatchNodeWeight:
    """One caller-selected mesh node and its positive surface tributary area."""

    node_id: NodeId
    point_xyz_mm: Vector
    tributary_area_mm2: float

    def __post_init__(self) -> None:
        if isinstance(self.node_id, bool) or not isinstance(self.node_id, (int, str)):
            raise TypeError("node id must be a positive integer or nonempty string")
        if isinstance(self.node_id, int) and self.node_id <= 0:
            raise ValueError("integer node id must be positive")
        if isinstance(self.node_id, str) and not self.node_id.strip():
            raise ValueError("string node id must be nonempty")
        object.__setattr__(
            self, "point_xyz_mm", _vector(self.point_xyz_mm, "node point")
        )
        object.__setattr__(
            self,
            "tributary_area_mm2",
            _finite_positive(self.tributary_area_mm2, "tributary area"),
        )


@dataclass(frozen=True)
class NodalForce:
    """One global nodal force in an exact-resultant owner distribution."""

    node_id: NodeId
    point_xyz_mm: Vector
    force_xyz_n: Vector
    tributary_area_mm2: float

    def __post_init__(self) -> None:
        if isinstance(self.node_id, bool) or not isinstance(self.node_id, (int, str)):
            raise TypeError("node id must be a positive integer or nonempty string")
        if isinstance(self.node_id, int) and self.node_id <= 0:
            raise ValueError("integer node id must be positive")
        if isinstance(self.node_id, str) and not self.node_id.strip():
            raise ValueError("string node id must be nonempty")
        object.__setattr__(
            self, "point_xyz_mm", _vector(self.point_xyz_mm, "node point")
        )
        object.__setattr__(
            self, "force_xyz_n", _vector(self.force_xyz_n, "nodal force")
        )
        object.__setattr__(
            self,
            "tributary_area_mm2",
            _finite_positive(self.tributary_area_mm2, "tributary area"),
        )


@dataclass(frozen=True)
class OwnerWrenchDistribution:
    owner_body: str
    target_wrench_global: Wrench
    nodal_forces: tuple[NodalForce, ...]
    reconstructed_wrench_global: Wrench
    residual_global: Wrench
    characteristic_length_mm: float
    scaled_gram_relative_pivot: float


@dataclass(frozen=True)
class DistributedUnitCase:
    """A unit case loaded on its two declared owners and checked for closure."""

    case: UnitWrenchCase
    owner_distributions: tuple[OwnerWrenchDistribution, ...]
    action_reaction_check: ActionReactionCheck


def _validate_manifest_shape(
    manifest: Any,
) -> tuple[tuple[InterfaceDatum, ...], tuple[tuple[str, tuple[str, str]], ...], str]:
    if not isinstance(manifest, Mapping):
        raise TypeError("WJ16 mechanics manifest must be an object")
    if manifest.get("schema") != "wood_joint_wj04_full_stock_mechanics_contract/v1":
        raise ValueError("unexpected WJ16 mechanics input schema")
    composition = manifest.get("composition")
    if not isinstance(composition, Mapping):
        raise TypeError("WJ16 mechanics input is missing composition identity")
    if composition.get("source_inventory_sha256") != SOURCE_INVENTORY_SHA256:
        raise ValueError("WJ16 source inventory fingerprint changed")
    if composition.get("canonical_wj04_config_sha256") != CANONICAL_WJ04_CONFIG_SHA256:
        raise ValueError("canonical WJ04 composition fingerprint changed")
    composition_id = composition.get("trial_id")
    if not isinstance(composition_id, str) or not composition_id.strip():
        raise ValueError("WJ16 composition trial id is missing")

    physical_inventory = manifest.get("physical_inventory")
    if not isinstance(physical_inventory, Mapping):
        raise TypeError("WJ16 physical inventory is missing")
    if physical_inventory.get("physical_interfaces") != 4:
        raise ValueError("WJ16 input must bind exactly four physical interfaces")
    if physical_inventory.get("ordinary_physical_bolts") != 8:
        raise ValueError("WJ16 input must bind exactly eight physical bolts")

    interface_rows = manifest.get("physical_interfaces")
    if isinstance(interface_rows, (str, bytes)) or not isinstance(
        interface_rows, Sequence
    ):
        raise TypeError("WJ16 physical interface records are missing")
    if len(interface_rows) != 4:
        raise ValueError("WJ16 input must contain exactly four physical interfaces")

    rows_by_id: dict[str, Mapping[str, Any]] = {}
    for row in interface_rows:
        if not isinstance(row, Mapping):
            raise TypeError("each WJ16 interface record must be an object")
        interface_id = _owner_name(row.get("interface_id"), "interface id")
        if interface_id in rows_by_id:
            raise ValueError(f"duplicate WJ16 interface {interface_id!r}")
        rows_by_id[interface_id] = row
    if set(rows_by_id) != set(EXPECTED_OWNER_PAIRS):
        raise ValueError(
            "WJ16 interface IDs changed from the authenticated four-interface set"
        )

    datums: list[InterfaceDatum] = []
    owner_pairs: list[tuple[str, tuple[str, str]]] = []
    for interface_id, expected_owner_pair in EXPECTED_OWNER_PAIRS.items():
        row = rows_by_id[interface_id]
        head_to_nut = row.get("members_head_to_nut")
        if (
            isinstance(head_to_nut, (str, bytes))
            or not isinstance(head_to_nut, Sequence)
            or len(head_to_nut) != 2
        ):
            raise ValueError(
                f"interface {interface_id!r} must name two ordered members"
            )
        members = tuple(_owner_name(value, "interface member") for value in head_to_nut)
        if members[0] == members[1]:
            raise ValueError(f"interface {interface_id!r} repeats a member owner")

        source_face = row.get("source_host_face")
        candidate_face = row.get("candidate_cleat_face")
        if not isinstance(source_face, Mapping) or not isinstance(
            candidate_face, Mapping
        ):
            raise TypeError(
                f"interface {interface_id!r} is missing its two face records"
            )
        host_body = _owner_name(source_face.get("part_id"), "source host owner")
        if host_body not in members:
            raise ValueError(
                f"interface {interface_id!r} host is not an ordered member"
            )
        cleat_body = next(member for member in members if member != host_body)
        if (host_body, cleat_body) != expected_owner_pair:
            raise ValueError(f"interface {interface_id!r} owner pair changed")

        host_normal = _unit(
            _vector(source_face.get("normal_global_xyz"), "host face normal"),
            "host face normal",
        )
        cleat_normal = _unit(
            _vector(
                candidate_face.get("plane_normal_global_xyz"),
                "cleat face normal",
            ),
            "cleat face normal",
        )
        if (
            sum(a * b for a, b in zip(host_normal, cleat_normal, strict=True))
            > -1.0 + 1e-7
        ):
            raise ValueError(f"interface {interface_id!r} face normals are not opposed")

        raw_datum = row.get("shear_plane_datum")
        if not isinstance(raw_datum, Mapping):
            raise TypeError(f"interface {interface_id!r} lacks its shear-plane datum")
        point = _vector(raw_datum.get("origin_global_xyz_mm"), "shear-plane datum")
        datum_normal = _unit(
            _vector(
                raw_datum.get("normal_head_to_nut_global_xyz"),
                "datum head-to-nut normal",
            ),
            "datum head-to-nut normal",
        )
        if (
            not isinstance(raw_datum.get("location_basis"), str)
            or not raw_datum["location_basis"].strip()
        ):
            raise ValueError(
                f"interface {interface_id!r} datum location basis is missing"
            )
        # The datum normal is an authenticated reference and must remain a unit
        # vector; it is not substituted for the common component basis.
        if abs(math.sqrt(sum(value * value for value in datum_normal)) - 1.0) > 1e-9:
            raise ValueError(
                f"interface {interface_id!r} datum normal is not unit length"
            )
        datums.append(InterfaceDatum(interface_id, point, WJ04_BASIS_GLOBAL))
        owner_pairs.append((interface_id, (host_body, cleat_body)))

    return tuple(datums), tuple(owner_pairs), composition_id


def _build_case_plan(
    manifest: Mapping[str, Any],
    *,
    manifest_sha256: str,
    response_contract_sha256: str,
) -> UnitCasePlan:
    datums, owner_pairs, composition_id = _validate_manifest_shape(manifest)
    datum_by_id = {datum.interface_id: datum for datum in datums}
    owners_by_id = dict(owner_pairs)
    cases: list[UnitWrenchCase] = []

    # Preserve the authenticated interface source order; each result remains
    # one isolated interface case, never a cross-interface sum.
    for datum in datums:
        host_body, cleat_body = owners_by_id[datum.interface_id]
        for component in COMPONENTS:
            for sign in CASE_SIGNS:
                host_global = _local_basis_wrench(component, sign)
                cleat_global = _negate(host_global)
                host_local = to_local(
                    host_global, datum.local_basis or WJ04_BASIS_GLOBAL
                )
                expected_local = Wrench(
                    tuple(
                        sign * FORCE_UNIT_N if component == f"F{axis}" else 0.0
                        for axis in ("X", "T", "N")
                    ),
                    tuple(
                        sign * MOMENT_UNIT_NMM if component == f"M{axis}" else 0.0
                        for axis in ("X", "T", "N")
                    ),
                )
                if host_local != expected_local:
                    raise ValueError(
                        f"component basis projection failed for {datum.interface_id}/{component}"
                    )
                direction = "plus" if sign > 0 else "minus"
                case_id = f"{datum.interface_id}__{component.lower()}_{direction}"
                cases.append(
                    UnitWrenchCase(
                        case_id=case_id,
                        interface_id=datum.interface_id,
                        component=component,
                        sign=sign,
                        host_body=host_body,
                        cleat_body=cleat_body,
                        datum_xyz_mm=datum.point_xyz_mm,
                        host_wrench_global=host_global,
                        cleat_wrench_global=cleat_global,
                        host_wrench_local=host_local,
                    )
                )

    # Validate every case's exact two-owner and common-moment-datum reference
    # through the same accounting primitives used by response extraction.
    if len(cases) != 48:
        raise ValueError("expected exactly 48 independent unit-wrench cases")
    if set(datum_by_id) != set(owners_by_id):
        raise ValueError("case plan owner and moment-datum interface sets disagree")
    for case in cases:
        if owners_by_id[case.interface_id] != case.owner_bodies:
            raise ValueError(f"case {case.case_id!r} has incomplete owner coverage")
        if datum_by_id[case.interface_id].point_xyz_mm != case.datum_xyz_mm:
            raise ValueError(f"case {case.case_id!r} moment datum changed")
        residual = Wrench(
            tuple(
                case.host_wrench_global.force_n[i] + case.cleat_wrench_global.force_n[i]
                for i in range(3)
            ),
            tuple(
                case.host_wrench_global.moment_nmm[i]
                + case.cleat_wrench_global.moment_nmm[i]
                for i in range(3)
            ),
        )
        if residual != Wrench((0.0, 0.0, 0.0), (0.0, 0.0, 0.0)):
            raise ValueError(f"case {case.case_id!r} is not self-equilibrated")

    return UnitCasePlan(
        source_manifest_sha256=manifest_sha256,
        source_inventory_sha256=SOURCE_INVENTORY_SHA256,
        canonical_wj04_config_sha256=CANONICAL_WJ04_CONFIG_SHA256,
        composition_id=composition_id,
        response_contract_sha256=response_contract_sha256,
        interface_datums=datums,
        owner_pairs=owner_pairs,
        cases=tuple(cases),
    )


def load_wj16_unit_case_plan(
    manifest_path: str | Path | None = None,
) -> UnitCasePlan:
    """Load the exact authenticated mechanics input and define 48 cases.

    Any byte change to the pinned manifest fails closed. The response-method
    document is also hashed into the emitted plan so the output identifies the
    authored six-component contract it implements.
    """

    selected_path = (
        ROOT / MECHANICS_MANIFEST_PATH if manifest_path is None else Path(manifest_path)
    )
    data = selected_path.read_bytes()
    manifest_sha256 = _sha256_bytes(data)
    if manifest_sha256 != MECHANICS_MANIFEST_SHA256:
        raise ValueError(
            "WJ16 mechanics manifest does not match the pinned full-stock input digest"
        )
    try:
        manifest = json.loads(data)
    except (json.JSONDecodeError, UnicodeDecodeError) as error:
        raise ValueError("WJ16 mechanics manifest is not valid JSON") from error
    contract_path = ROOT / RESPONSE_CONTRACT_PATH
    try:
        contract_sha256 = _sha256_bytes(contract_path.read_bytes())
    except OSError as error:
        raise ValueError("representative unit-response contract is missing") from error
    return _build_case_plan(
        manifest,
        manifest_sha256=manifest_sha256,
        response_contract_sha256=contract_sha256,
    )


def _solve_linear_6x6(
    matrix: Sequence[Sequence[float]],
    right: Sequence[float],
    *,
    relative_pivot_tolerance: float,
) -> tuple[tuple[float, ...], float]:
    if len(matrix) != 6 or len(right) != 6 or any(len(row) != 6 for row in matrix):
        raise ValueError("scaled wrench system must be 6 by 6")
    augmented = [
        list(map(float, matrix[row])) + [float(right[row])] for row in range(6)
    ]
    matrix_scale = max(abs(value) for row in matrix for value in row)
    if not math.isfinite(matrix_scale) or matrix_scale <= 0.0:
        raise ValueError("force distribution patch has a zero wrench Gram matrix")
    minimum_relative_pivot = math.inf
    for column in range(6):
        pivot_row = max(range(column, 6), key=lambda row: abs(augmented[row][column]))
        pivot_abs = abs(augmented[pivot_row][column])
        relative_pivot = pivot_abs / matrix_scale
        minimum_relative_pivot = min(minimum_relative_pivot, relative_pivot)
        if (
            not math.isfinite(relative_pivot)
            or relative_pivot <= relative_pivot_tolerance
        ):
            raise ValueError(
                "force distribution patch is rank-deficient at the scale-aware "
                "six-wrench tolerance; supply at least three non-collinear nodes"
            )
        if pivot_row != column:
            augmented[column], augmented[pivot_row] = (
                augmented[pivot_row],
                augmented[column],
            )
        pivot = augmented[column][column]
        for index in range(column, 7):
            augmented[column][index] /= pivot
        for row in range(6):
            if row == column:
                continue
            factor = augmented[row][column]
            if factor == 0.0:
                continue
            for index in range(column, 7):
                augmented[row][index] -= factor * augmented[column][index]
    solution = tuple(augmented[row][6] for row in range(6))
    if not all(math.isfinite(value) for value in solution):
        raise ValueError("force distribution produced a non-finite solution")
    return solution, minimum_relative_pivot


def _cross_matrix(vector: Vector) -> tuple[tuple[float, float, float], ...]:
    x, y, z = vector
    return (
        (0.0, -z, y),
        (z, 0.0, -x),
        (-y, x, 0.0),
    )


def _patch_nodes(values: Any, owner_body: str) -> tuple[PatchNodeWeight, ...]:
    if isinstance(values, (str, bytes)) or not isinstance(values, Sequence):
        raise TypeError(f"node patch for {owner_body!r} must be a sequence")
    if len(values) < 3:
        raise ValueError(f"node patch for {owner_body!r} needs at least three nodes")
    nodes: list[PatchNodeWeight] = []
    seen: set[tuple[type, int | str]] = set()
    for value in values:
        if isinstance(value, PatchNodeWeight):
            node = value
        elif isinstance(value, Mapping):
            try:
                node = PatchNodeWeight(
                    node_id=value["node_id"],
                    point_xyz_mm=value["point_xyz_mm"],
                    tributary_area_mm2=value["tributary_area_mm2"],
                )
            except KeyError as error:
                raise ValueError(
                    f"node patch row for {owner_body!r} lacks {error.args[0]}"
                ) from error
        else:
            raise TypeError(
                f"node patch rows for {owner_body!r} must be PatchNodeWeight records or mappings"
            )
        key = (type(node.node_id), node.node_id)
        if key in seen:
            raise ValueError(
                f"duplicate node id {node.node_id!r} in {owner_body!r} patch"
            )
        seen.add(key)
        nodes.append(node)
    return tuple(nodes)


def distribute_wrench_to_nodes(
    nodes: Sequence[PatchNodeWeight | Mapping[str, Any]],
    datum_xyz_mm: Sequence[float],
    target_wrench_global: Wrench,
    *,
    owner_body: str = "unspecified",
    rank_relative_tolerance: float = DEFAULT_RANK_RELATIVE_TOLERANCE,
    force_tolerance_n: float = DEFAULT_FORCE_TOLERANCE_N,
    moment_tolerance_nmm: float = DEFAULT_MOMENT_TOLERANCE_NMM,
) -> OwnerWrenchDistribution:
    """Distribute one global wrench over supplied non-collinear mesh nodes.

    For tributary areas ``A_i``, the solution minimizes
    ``sum(norm(f_i)**2 / A_i)`` subject to exact global force and moment
    resultants about ``datum_xyz_mm``. Moment rows are divided by the
    area-centroid radius before the rank test and solve, avoiding the force
    (N) versus moment (N-mm) scale mismatch. The output is independently
    reconstructed about the caller's original datum.
    """

    owner_body = _owner_name(owner_body, "owner body")
    if not isinstance(target_wrench_global, Wrench):
        raise TypeError("target wrench must use the canonical patch Wrench type")
    datum = _vector(datum_xyz_mm, "wrench datum")
    force_tolerance_n = _finite_nonnegative(force_tolerance_n, "force tolerance")
    moment_tolerance_nmm = _finite_nonnegative(moment_tolerance_nmm, "moment tolerance")
    rank_relative_tolerance = _finite_positive(
        rank_relative_tolerance, "rank relative tolerance"
    )
    if rank_relative_tolerance >= 1.0:
        raise ValueError("rank relative tolerance must be less than one")
    patch = _patch_nodes(nodes, owner_body)

    total_area = math.fsum(node.tributary_area_mm2 for node in patch)
    centroid = tuple(
        math.fsum(node.tributary_area_mm2 * node.point_xyz_mm[axis] for node in patch)
        / total_area
        for axis in range(3)
    )
    radius = max(
        math.sqrt(
            math.fsum(
                (node.point_xyz_mm[axis] - centroid[axis]) ** 2 for axis in range(3)
            )
        )
        for node in patch
    )
    if not math.isfinite(radius) or radius <= 1e-12:
        raise ValueError(
            f"node patch for {owner_body!r} is coincident or rank-deficient"
        )

    # Shift the target moment to the patch area centroid, then scale the three
    # moment equations by a characteristic in-patch radius in millimetres.
    target_at_centroid = shift_wrench(
        target_wrench_global,
        datum,
        centroid,  # type: ignore[arg-type]
    )
    scaled_rhs = (
        *target_at_centroid.force_n,
        *(value / radius for value in target_at_centroid.moment_nmm),
    )

    cross_blocks: list[tuple[tuple[float, float, float], ...]] = []
    gram = [[0.0] * 6 for _ in range(6)]
    for node in patch:
        relative = tuple(
            (node.point_xyz_mm[axis] - centroid[axis]) / radius for axis in range(3)
        )
        skew = _cross_matrix(relative)  # map force to scaled moment at centroid
        block = (
            (1.0, 0.0, 0.0),
            (0.0, 1.0, 0.0),
            (0.0, 0.0, 1.0),
            skew[0],
            skew[1],
            skew[2],
        )
        cross_blocks.append(block)
        area = node.tributary_area_mm2
        for row in range(6):
            for column in range(6):
                gram[row][column] += area * math.fsum(
                    block[row][axis] * block[column][axis] for axis in range(3)
                )

    multipliers, minimum_relative_pivot = _solve_linear_6x6(
        gram,
        scaled_rhs,
        relative_pivot_tolerance=rank_relative_tolerance,
    )
    nodal_forces: list[NodalForce] = []
    for node, block in zip(patch, cross_blocks, strict=True):
        force = tuple(
            node.tributary_area_mm2
            * math.fsum(block[row][axis] * multipliers[row] for row in range(6))
            for axis in range(3)
        )
        nodal_forces.append(
            NodalForce(node.node_id, node.point_xyz_mm, force, node.tributary_area_mm2)
        )

    reconstructed_force = tuple(
        math.fsum(row.force_xyz_n[axis] for row in nodal_forces) for axis in range(3)
    )
    moment_terms: list[list[float]] = [[], [], []]
    for row in nodal_forces:
        lever = tuple(row.point_xyz_mm[axis] - datum[axis] for axis in range(3))
        moment = cross(lever, row.force_xyz_n)
        for axis in range(3):
            moment_terms[axis].append(moment[axis])
    reconstructed_moment = tuple(math.fsum(terms) for terms in moment_terms)
    reconstructed = Wrench(reconstructed_force, reconstructed_moment)
    residual = Wrench(
        tuple(
            target_wrench_global.force_n[axis] - reconstructed.force_n[axis]
            for axis in range(3)
        ),
        tuple(
            target_wrench_global.moment_nmm[axis] - reconstructed.moment_nmm[axis]
            for axis in range(3)
        ),
    )
    if not is_equilibrated(residual, force_tolerance_n, moment_tolerance_nmm):
        raise ArithmeticError(
            f"nodal force distribution for {owner_body!r} did not close its target wrench"
        )

    return OwnerWrenchDistribution(
        owner_body=owner_body,
        target_wrench_global=target_wrench_global,
        nodal_forces=tuple(nodal_forces),
        reconstructed_wrench_global=reconstructed,
        residual_global=residual,
        characteristic_length_mm=radius,
        scaled_gram_relative_pivot=minimum_relative_pivot,
    )


def distribute_unit_case_to_nodes(
    case: UnitWrenchCase,
    nodes_by_owner: Mapping[str, Sequence[PatchNodeWeight | Mapping[str, Any]]],
    *,
    rank_relative_tolerance: float = DEFAULT_RANK_RELATIVE_TOLERANCE,
    force_tolerance_n: float = DEFAULT_FORCE_TOLERANCE_N,
    moment_tolerance_nmm: float = DEFAULT_MOMENT_TOLERANCE_NMM,
) -> DistributedUnitCase:
    """Load one case on exactly its host and cleat node patches and audit it.

    Node sets and tributary areas are caller supplied. Missing, extra, or
    mismatched owners fail closed. This helper never combines different
    interfaces or cases and does not add restraints, ties, preload, or
    stabilization.
    """

    if not isinstance(case, UnitWrenchCase):
        raise TypeError("case must be a UnitWrenchCase")
    if not isinstance(nodes_by_owner, Mapping):
        raise TypeError("node patches must be keyed by owner body")
    if set(nodes_by_owner) != set(case.owner_bodies):
        raise ValueError(
            f"case {case.case_id!r} node-patch owners must match exactly "
            f"{case.owner_bodies!r}"
        )

    targets = {
        case.host_body: case.host_wrench_global,
        case.cleat_body: case.cleat_wrench_global,
    }
    owner_distributions = tuple(
        distribute_wrench_to_nodes(
            nodes_by_owner[owner],
            case.datum_xyz_mm,
            targets[owner],
            owner_body=owner,
            rank_relative_tolerance=rank_relative_tolerance,
            force_tolerance_n=force_tolerance_n,
            moment_tolerance_nmm=moment_tolerance_nmm,
        )
        for owner in case.owner_bodies
    )

    datum = InterfaceDatum(
        case.interface_id,
        case.datum_xyz_mm,
        WJ04_BASIS_GLOBAL,
    )
    actions = tuple(
        SignedPointAction(
            interface_id=case.interface_id,
            owner_body=distribution.owner_body,
            point_xyz_mm=row.point_xyz_mm,
            force_xyz_n=row.force_xyz_n,
            source_id=str(row.node_id),
        )
        for distribution in owner_distributions
        for row in distribution.nodal_forces
    )
    datums = {case.interface_id: datum}
    observed = aggregate_interface_wrenches(actions, datums)
    by_owner = {row.owner_body: row.wrench_global for row in observed}
    if set(by_owner) != set(case.owner_bodies):
        raise ValueError(
            f"case {case.case_id!r} lost an owner during wrench aggregation"
        )
    for owner, target in targets.items():
        recovered = by_owner[owner]
        owner_residual = Wrench(
            tuple(target.force_n[i] - recovered.force_n[i] for i in range(3)),
            tuple(target.moment_nmm[i] - recovered.moment_nmm[i] for i in range(3)),
        )
        if not is_equilibrated(owner_residual, force_tolerance_n, moment_tolerance_nmm):
            raise ArithmeticError(
                f"case {case.case_id!r} owner {owner!r} moment/datum reference did not close"
            )

    action_reaction = audit_action_reaction(
        actions,
        datums,
        {case.interface_id: case.owner_bodies},
        force_tolerance_n=force_tolerance_n,
        moment_tolerance_nmm=moment_tolerance_nmm,
    )[0]
    if not action_reaction.passed:
        raise ArithmeticError(f"case {case.case_id!r} host/cleat actions do not close")
    return DistributedUnitCase(case, owner_distributions, action_reaction)


def _wrench_record(wrench: Wrench) -> dict[str, Vector]:
    return {
        "force_xyz_n": wrench.force_n,
        "moment_xyz_nmm": wrench.moment_nmm,
    }


def unit_case_plan_payload(plan: UnitCasePlan) -> dict[str, Any]:
    """Return deterministic JSON-compatible, authenticated case definitions."""

    if not isinstance(plan, UnitCasePlan):
        raise TypeError("plan must be a UnitCasePlan")
    datums_by_id = {datum.interface_id: datum for datum in plan.interface_datums}
    return {
        "schema": SCHEMA,
        "status": STATUS,
        "source": {
            "manifest_path": MECHANICS_MANIFEST_PATH,
            "manifest_sha256": plan.source_manifest_sha256,
            "source_inventory_sha256": plan.source_inventory_sha256,
            "canonical_wj04_config_sha256": plan.canonical_wj04_config_sha256,
            "composition_trial_id": plan.composition_id,
            "response_contract_path": RESPONSE_CONTRACT_PATH,
            "response_contract_sha256": plan.response_contract_sha256,
        },
        "coordinate_convention": {
            "point_units": "mm",
            "force_units": "N",
            "moment_units": "N*mm",
            "component_basis_global_xyz": {
                axis_name: WJ04_BASIS_GLOBAL[index]
                for index, axis_name in enumerate(("X", "T", "N"))
            },
            "positive_action_owner": "source_host_face.part_id",
            "opposite_action_owner": "other member in members_head_to_nut",
        },
        "unit_amplitudes": {
            "force_n": FORCE_UNIT_N,
            "moment_nmm": MOMENT_UNIT_NMM,
        },
        "counts": {
            "interfaces": len(plan.interface_datums),
            "signed_cases": len(plan.cases),
            "cases_per_interface": 12,
        },
        "interfaces": [
            {
                "interface_id": interface_id,
                "host_body": owner_pair[0],
                "cleat_body": owner_pair[1],
                "datum_xyz_mm": datums_by_id[interface_id].point_xyz_mm,
                "local_basis_global_xyz": datums_by_id[interface_id].local_basis,
            }
            for interface_id, owner_pair in plan.owner_pairs
        ],
        "cases": [
            {
                "case_id": case.case_id,
                "interface_id": case.interface_id,
                "component": case.component,
                "sign": case.sign,
                "host_body": case.host_body,
                "cleat_body": case.cleat_body,
                "datum_xyz_mm": case.datum_xyz_mm,
                "host_wrench_global": _wrench_record(case.host_wrench_global),
                "cleat_wrench_global": _wrench_record(case.cleat_wrench_global),
                "host_wrench_local_x_t_n": _wrench_record(case.host_wrench_local),
            }
            for case in plan.cases
        ],
        "limitations": [
            "Definitions only: this producer does not prepare or solve a native model.",
            "Each case is one isolated interface and one signed wrench component.",
            "Zero-preload clearances may expose internal free modes; no restraint is synthesized.",
            "No response stiffness, capacity, fresh six-case demand, or release is inferred.",
            "Nodal force distributions require caller-supplied common-footprint nodes and tributary areas.",
        ],
    }


def distributed_unit_case_payload(distributed: DistributedUnitCase) -> dict[str, Any]:
    """Serialize computed nodal forces and their independently closed wrenches."""

    if not isinstance(distributed, DistributedUnitCase):
        raise TypeError("distributed result must be a DistributedUnitCase")
    case = distributed.case
    return {
        "schema": "wood_joint_patch_distributed_unit_case/v1",
        "status": "nodal_loads_closed_diagnostic_only_no_solver_or_capacity_claim",
        "case_id": case.case_id,
        "interface_id": case.interface_id,
        "owners": case.owner_bodies,
        "datum_xyz_mm": case.datum_xyz_mm,
        "owner_distributions": [
            {
                "owner_body": row.owner_body,
                "target_wrench_global": _wrench_record(row.target_wrench_global),
                "nodal_loads": [
                    {
                        "node_id": load.node_id,
                        "point_xyz_mm": load.point_xyz_mm,
                        "tributary_area_mm2": load.tributary_area_mm2,
                        "force_xyz_n": load.force_xyz_n,
                    }
                    for load in row.nodal_forces
                ],
                "reconstructed_wrench_global": _wrench_record(
                    row.reconstructed_wrench_global
                ),
                "residual_global": _wrench_record(row.residual_global),
                "characteristic_length_mm": row.characteristic_length_mm,
                "scaled_gram_relative_pivot": row.scaled_gram_relative_pivot,
            }
            for row in distributed.owner_distributions
        ],
        "action_reaction": {
            "owner_bodies": distributed.action_reaction_check.owner_bodies,
            "residual_global": _wrench_record(
                distributed.action_reaction_check.residual_global
            ),
            "passed": distributed.action_reaction_check.passed,
        },
    }


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Emit authenticated WJ16 signed unit-wrench case definitions only."
    )
    parser.add_argument(
        "--compact",
        action="store_true",
        help="write compact JSON (default: indented JSON)",
    )
    args = parser.parse_args(argv)
    payload = unit_case_plan_payload(load_wj16_unit_case_plan())
    json.dump(
        payload,
        sys.stdout,
        indent=None if args.compact else 2,
        sort_keys=True,
        allow_nan=False,
    )
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
