"""Rigid-body constraint-rank diagnostic for explicit patch assumptions.

Every supplied body, whether timber or hardware, has six infinitesimal rigid-
body degrees of freedom. Contact normals, declared thread translations, and
explicit directional MPC rows are the only physical constraints included.
This module does not infer contact activity, bolt engagement, support,
stiffness, stability, or capacity.
"""

from __future__ import annotations

import math
from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass
from typing import Any

import numpy as np

Vector = tuple[float, float, float]
DOF_PER_BODY = 6
DOF_ORDER_SCALED = (
    "ux_mm",
    "uy_mm",
    "uz_mm",
    "L_omega_x_mm",
    "L_omega_y_mm",
    "L_omega_z_mm",
)


def _text(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label} must be a nonempty string")
    return value


def _number(value: Any, label: str, *, positive: bool = False) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TypeError(f"{label} must be numeric")
    try:
        result = float(value)
    except OverflowError as error:
        raise ValueError(f"{label} must be finite") from error
    if not math.isfinite(result) or (positive and result <= 0):
        qualifier = "positive and finite" if positive else "finite"
        raise ValueError(f"{label} must be {qualifier}")
    return result


def _vector(value: Any, label: str) -> Vector:
    if isinstance(value, (str, bytes)):
        raise TypeError(f"{label} must be a finite 3-vector")
    try:
        result = tuple(_number(component, label) for component in value)
    except (TypeError, ValueError, OverflowError) as error:
        if isinstance(error, (TypeError, ValueError)) and str(error).startswith(label):
            raise
        raise ValueError(f"{label} must be a finite 3-vector") from error
    if len(result) != 3:
        raise ValueError(f"{label} must be a finite 3-vector")
    return result  # type: ignore[return-value]


def _unit_vector(value: Any, label: str) -> Vector:
    vector = _vector(value, label)
    magnitude = math.sqrt(math.fsum(component * component for component in vector))
    if not math.isfinite(magnitude) or not math.isclose(
        magnitude, 1.0, rel_tol=0.0, abs_tol=1e-8
    ):
        raise ValueError(f"{label} must be a unit vector")
    return vector


def _cross(left: Vector, right: Vector) -> Vector:
    return (
        left[1] * right[2] - left[2] * right[1],
        left[2] * right[0] - left[0] * right[2],
        left[0] * right[1] - left[1] * right[0],
    )


def _subtract(left: Vector, right: Vector) -> Vector:
    return tuple(a - b for a, b in zip(left, right, strict=True))  # type: ignore[return-value]


def _line_mismatch_mm(point_a: Vector, point_b: Vector, direction: Vector) -> float:
    try:
        separation = _subtract(point_b, point_a)
        along = math.fsum(a * b for a, b in zip(separation, direction, strict=True))
        transverse = tuple(
            separation[index] - along * direction[index] for index in range(3)
        )
        return math.sqrt(math.fsum(component * component for component in transverse))
    except OverflowError:
        return math.inf


@dataclass(frozen=True)
class RigidBodyDatum:
    """Reference point for one body's global rigid translation and rotation."""

    body_id: str
    origin_xyz_mm: Vector

    def __post_init__(self) -> None:
        object.__setattr__(self, "body_id", _text(self.body_id, "body id"))
        object.__setattr__(
            self, "origin_xyz_mm", _vector(self.origin_xyz_mm, "body origin")
        )


@dataclass(frozen=True)
class ActiveContactNormal:
    """One normal compatibility row, explicitly assumed active by the caller.

    ``normal_xyz_global`` points from ``body_a`` toward ``body_b``. Reversing
    that direction changes only the row sign. ``point_a_xyz_mm`` and
    ``point_b_xyz_mm`` are independent global application points. Their
    projected tangential mismatch is checked against the caller's declared
    tolerance; active status is not checked here.
    """

    constraint_id: str
    pair_id: str
    interface_id: str
    body_a: str
    body_b: str
    point_a_xyz_mm: Vector
    point_b_xyz_mm: Vector
    normal_xyz_global: Vector

    def __post_init__(self) -> None:
        for name in ("constraint_id", "pair_id", "interface_id", "body_a", "body_b"):
            object.__setattr__(self, name, _text(getattr(self, name), name))
        if self.body_a == self.body_b:
            raise ValueError("contact owners must be different bodies")
        object.__setattr__(
            self, "point_a_xyz_mm", _vector(self.point_a_xyz_mm, "contact point a")
        )
        object.__setattr__(
            self, "point_b_xyz_mm", _vector(self.point_b_xyz_mm, "contact point b")
        )
        object.__setattr__(
            self,
            "normal_xyz_global",
            _unit_vector(self.normal_xyz_global, "contact normal"),
        )


@dataclass(frozen=True)
class ThreadConstraint:
    """One caller-declared translational compatibility row for a thread.

    This records a kinematic equality along one declared global direction
    between two engagement points. It is not a bolt model; it has no stiffness,
    capacity, tension-only law, or inferred engagement. Supply a separate row
    for each constrained direction and name the assumed mode explicitly.
    """

    constraint_id: str
    thread_id: str
    body_a: str
    body_b: str
    point_a_xyz_mm: Vector
    point_b_xyz_mm: Vector
    direction_xyz_global: Vector
    declared_mode: str

    def __post_init__(self) -> None:
        for name in ("constraint_id", "thread_id", "body_a", "body_b", "declared_mode"):
            object.__setattr__(self, name, _text(getattr(self, name), name))
        if self.body_a == self.body_b:
            raise ValueError("thread constraint owners must be different bodies")
        object.__setattr__(
            self, "point_a_xyz_mm", _vector(self.point_a_xyz_mm, "thread point a")
        )
        object.__setattr__(
            self, "point_b_xyz_mm", _vector(self.point_b_xyz_mm, "thread point b")
        )
        object.__setattr__(
            self,
            "direction_xyz_global",
            _unit_vector(self.direction_xyz_global, "thread constraint direction"),
        )


@dataclass(frozen=True)
class MpcPointTerm:
    """One weighted point-displacement term in a declared directional MPC.

    ``coefficient`` multiplies the point displacement projected onto the MPC
    direction. For a slave point tied to a quadratic master element, callers
    can preserve the exact interpolation as one ``+1`` slave term and one
    ``-N_i`` term for every master node, including its global coordinate and
    shape weight. Zero-weight nodes may remain for source traceability. Terms
    are not collapsed to a centroid by this helper.
    """

    body_id: str
    global_node_xyz_mm: Vector
    coefficient: float
    source_node_id: str | int | None = None
    source_element_id: str | int | None = None
    interpolation_weight: float | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "body_id", _text(self.body_id, "MPC term body id"))
        object.__setattr__(
            self,
            "global_node_xyz_mm",
            _vector(self.global_node_xyz_mm, "MPC term global node point"),
        )
        coefficient = _number(self.coefficient, "MPC term coefficient")
        object.__setattr__(self, "coefficient", coefficient)
        for name in ("source_node_id", "source_element_id"):
            value = getattr(self, name)
            if value is not None:
                if isinstance(value, bool) or not isinstance(value, (str, int)):
                    raise TypeError(f"{name} must be a nonempty string, integer, or None")
                if isinstance(value, str):
                    object.__setattr__(self, name, _text(value, name))
                elif value <= 0:
                    raise ValueError(f"{name} integer must be positive")
        if self.interpolation_weight is not None:
            object.__setattr__(
                self,
                "interpolation_weight",
                _number(self.interpolation_weight, "MPC interpolation weight"),
            )


@dataclass(frozen=True)
class MpcKinematicConstraint:
    """One explicit scalar directional MPC over body-owned point motions."""

    constraint_id: str
    global_direction_xyz: Vector
    terms: Sequence[MpcPointTerm | Mapping[str, Any]]
    declared_mode: str
    source_pair_id: str | None = None
    source_provenance: Mapping[str, Any] | None = None

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "constraint_id", _text(self.constraint_id, "constraint_id")
        )
        object.__setattr__(
            self,
            "global_direction_xyz",
            _unit_vector(self.global_direction_xyz, "MPC direction"),
        )
        object.__setattr__(self, "declared_mode", _text(self.declared_mode, "declared_mode"))
        if self.source_pair_id is not None:
            object.__setattr__(
                self, "source_pair_id", _text(self.source_pair_id, "source_pair_id")
            )
        if self.source_provenance is not None:
            if not isinstance(self.source_provenance, Mapping):
                raise TypeError("MPC source provenance must be a mapping or None")
            provenance = dict(self.source_provenance)
            if any(not isinstance(key, str) or not key for key in provenance):
                raise ValueError("MPC source provenance keys must be nonempty strings")
            object.__setattr__(self, "source_provenance", provenance)
        if isinstance(self.terms, (str, bytes)) or not isinstance(self.terms, Sequence):
            raise TypeError("MPC terms must be a sequence")
        terms = tuple(
            term
            if isinstance(term, MpcPointTerm)
            else MpcPointTerm(**term)
            if isinstance(term, Mapping)
            else None
            for term in self.terms
        )
        if len(terms) < 2 or any(term is None for term in terms):
            raise ValueError("MPC must contain at least two valid point terms")
        if not any(term.coefficient != 0 for term in terms):
            raise ValueError("MPC must contain at least one nonzero point coefficient")
        object.__setattr__(self, "terms", terms)


@dataclass(frozen=True)
class _ConstraintRow:
    row_id: str
    kind: str
    matrix: tuple[float, ...]


def _coerce_record(value: Any, record_type: type, label: str) -> Any:
    if isinstance(value, record_type):
        return value
    if isinstance(value, Mapping):
        try:
            return record_type(**value)
        except TypeError as error:
            raise ValueError(f"invalid {label} record: {error}") from error
    raise TypeError(f"{label} rows must be {record_type.__name__} records or mappings")


def _body_records(values: Sequence[RigidBodyDatum | Mapping[str, Any]]) -> tuple[RigidBodyDatum, ...]:
    if isinstance(values, (str, bytes)) or not isinstance(values, Sequence) or not values:
        raise ValueError("at least one rigid body datum is required")
    records = tuple(
        _coerce_record(value, RigidBodyDatum, "rigid body") for value in values
    )
    ids = [item.body_id for item in records]
    if len(ids) != len(set(ids)):
        raise ValueError("rigid body ids must be unique")
    return records


def _constraint_records(
    values: Sequence[Any], record_type: type, label: str
) -> tuple[Any, ...]:
    if isinstance(values, (str, bytes)) or not isinstance(values, Sequence):
        raise TypeError(f"{label} rows must be a sequence")
    records = tuple(_coerce_record(value, record_type, label) for value in values)
    ids = [item.constraint_id for item in records]
    if len(ids) != len(set(ids)):
        raise ValueError("constraint ids must be unique across all physical rows")
    return records


def _check_constraint_owners(
    contacts: Sequence[ActiveContactNormal],
    threads: Sequence[ThreadConstraint],
    mpcs: Sequence[MpcKinematicConstraint],
    body_ids: set[str],
) -> None:
    for row in (*contacts, *threads):
        if row.body_a not in body_ids or row.body_b not in body_ids:
            raise ValueError(
                f"constraint {row.constraint_id!r} references an unknown body"
            )
    for row in mpcs:
        unknown = sorted({term.body_id for term in row.terms} - body_ids)
        if unknown:
            raise ValueError(
                f"MPC constraint {row.constraint_id!r} references unknown bodies: {unknown}"
            )


def _check_point_alignment(
    contacts: Sequence[ActiveContactNormal],
    threads: Sequence[ThreadConstraint],
    mpcs: Sequence[MpcKinematicConstraint],
    tolerance_mm: float,
) -> None:
    for item in contacts:
        mismatch = _line_mismatch_mm(
            item.point_a_xyz_mm,
            item.point_b_xyz_mm,
            item.normal_xyz_global,
        )
        if mismatch > tolerance_mm:
            raise ValueError(
                f"contact constraint {item.constraint_id!r} has tangential point "
                f"mismatch {mismatch:.12g} mm, above {tolerance_mm:.12g} mm"
            )
    for item in threads:
        mismatch = _line_mismatch_mm(
            item.point_a_xyz_mm,
            item.point_b_xyz_mm,
            item.direction_xyz_global,
        )
        if mismatch > tolerance_mm:
            raise ValueError(
                f"thread constraint {item.constraint_id!r} has off-axis endpoint "
                f"mismatch {mismatch:.12g} mm, above {tolerance_mm:.12g} mm"
            )
    for item in mpcs:
        coefficient_sum = math.fsum(term.coefficient for term in item.terms)
        coefficient_scale = max(1.0, math.fsum(abs(term.coefficient) for term in item.terms))
        if abs(coefficient_sum) > 1e-10 * coefficient_scale:
            raise ValueError(
                f"MPC constraint {item.constraint_id!r} is not translation-objective: "
                f"coefficient sum {coefficient_sum:.12g}"
            )
        torque_residual = tuple(
            math.fsum(
                term.coefficient
                * _cross(term.global_node_xyz_mm, item.global_direction_xyz)[axis]
                for term in item.terms
            )
            for axis in range(3)
        )
        rotation_mismatch = math.sqrt(
            math.fsum(component * component for component in torque_residual)
        )
        if rotation_mismatch > tolerance_mm:
            raise ValueError(
                f"MPC constraint {item.constraint_id!r} is nonobjective under global "
                f"rotation: residual {rotation_mismatch:.12g} mm, above "
                f"{tolerance_mm:.12g} mm"
            )


def _contact_row(
    item: ActiveContactNormal,
    body_index: Mapping[str, int],
    origins: Mapping[str, Vector],
    body_count: int,
    characteristic_length_mm: float,
) -> _ConstraintRow:
    row = np.zeros(DOF_PER_BODY * body_count, dtype=np.float64)
    normal = item.normal_xyz_global
    for body_id, point, sign in (
        (item.body_a, item.point_a_xyz_mm, 1.0),
        (item.body_b, item.point_b_xyz_mm, -1.0),
    ):
        start = DOF_PER_BODY * body_index[body_id]
        offset = _subtract(point, origins[body_id])
        row[start : start + 3] = sign * np.asarray(normal)
        row[start + 3 : start + 6] = (
            sign
            * np.asarray(_cross(offset, normal))
            / characteristic_length_mm
        )
    return _ConstraintRow(
        row_id=item.constraint_id,
        kind="assumed_active_contact_normal",
        matrix=tuple(float(value) for value in row),
    )


def _thread_row(
    item: ThreadConstraint,
    body_index: Mapping[str, int],
    origins: Mapping[str, Vector],
    body_count: int,
    characteristic_length_mm: float,
) -> _ConstraintRow:
    row = np.zeros(DOF_PER_BODY * body_count, dtype=np.float64)
    direction = item.direction_xyz_global
    for body_id, point, sign in (
        (item.body_a, item.point_a_xyz_mm, 1.0),
        (item.body_b, item.point_b_xyz_mm, -1.0),
    ):
        start = DOF_PER_BODY * body_index[body_id]
        offset = _subtract(point, origins[body_id])
        row[start : start + 3] = sign * np.asarray(direction)
        row[start + 3 : start + 6] = (
            sign
            * np.asarray(_cross(offset, direction))
            / characteristic_length_mm
        )
    return _ConstraintRow(
        row_id=item.constraint_id,
        kind=f"declared_thread_translation:{item.declared_mode}",
        matrix=tuple(float(value) for value in row),
    )


def _mpc_row(
    item: MpcKinematicConstraint,
    body_index: Mapping[str, int],
    origins: Mapping[str, Vector],
    body_count: int,
    characteristic_length_mm: float,
) -> _ConstraintRow:
    row = np.zeros(DOF_PER_BODY * body_count, dtype=np.float64)
    direction = np.asarray(item.global_direction_xyz)
    for term in item.terms:
        start = DOF_PER_BODY * body_index[term.body_id]
        offset = _subtract(term.global_node_xyz_mm, origins[term.body_id])
        row[start : start + 3] += term.coefficient * direction
        row[start + 3 : start + 6] += (
            term.coefficient
            * np.asarray(_cross(offset, item.global_direction_xyz))
            / characteristic_length_mm
        )
    return _ConstraintRow(
        row_id=item.constraint_id,
        kind=f"declared_mpc_kinematic:{item.declared_mode}",
        matrix=tuple(float(value) for value in row),
    )


def _gauge_rows(body_id: str, body_index: Mapping[str, int], body_count: int) -> tuple[_ConstraintRow, ...]:
    rows = []
    start = DOF_PER_BODY * body_index[body_id]
    for local_index, dof_name in enumerate(DOF_ORDER_SCALED):
        row = np.zeros(DOF_PER_BODY * body_count, dtype=np.float64)
        row[start + local_index] = 1.0
        rows.append(
            _ConstraintRow(
                row_id=f"global_gauge:{body_id}:{dof_name}",
                kind="global_coordinate_gauge",
                matrix=tuple(float(value) for value in row),
            )
        )
    return tuple(rows)


def _global_rigid_motion_check(
    rows: Sequence[_ConstraintRow],
    body_ids: Sequence[str],
    origins: Mapping[str, Vector],
    characteristic_length_mm: float,
    point_alignment_tolerance_mm: float,
) -> dict[str, Any]:
    """Show the six common rigid motions against physical rows before gauge."""
    body_count = len(body_ids)
    dof_count = DOF_PER_BODY * body_count
    modes = np.zeros((dof_count, 6), dtype=np.float64)
    axes: tuple[Vector, ...] = (
        (1.0, 0.0, 0.0),
        (0.0, 1.0, 0.0),
        (0.0, 0.0, 1.0),
    )
    for body_index, body_id in enumerate(body_ids):
        start = DOF_PER_BODY * body_index
        for axis_index, axis in enumerate(axes):
            modes[start : start + 3, axis_index] = axis
            modes[start : start + 3, axis_index + 3] = np.asarray(
                _cross(axis, origins[body_id])
            )
            modes[start + 3 : start + 6, axis_index + 3] = (
                characteristic_length_mm * np.asarray(axis)
            )
    matrix = np.asarray([row.matrix for row in rows], dtype=np.float64)
    if not rows:
        matrix = np.zeros((0, dof_count), dtype=np.float64)
    residuals = matrix @ modes
    if not np.isfinite(modes).all() or not np.isfinite(residuals).all():
        raise ValueError("global rigid-motion check contains nonfinite values")
    return {
        "evaluated_before_global_gauge": True,
        "mode_ids": [
            "global_translation_x",
            "global_translation_y",
            "global_translation_z",
            "global_rotation_x",
            "global_rotation_y",
            "global_rotation_z",
        ],
        "row_ids": [row.row_id for row in rows],
        "residuals_mm_by_row_and_mode": residuals.tolist(),
        "maximum_absolute_rotation_residual_mm_by_row": [
            float(value)
            for value in (
                np.max(np.abs(residuals[:, 3:]), axis=1)
                if rows
                else np.zeros(0, dtype=np.float64)
            )
        ],
        "rotation_residual_within_declared_point_tolerance_by_row": [
            bool(value <= point_alignment_tolerance_mm + 1e-12)
            for value in (
                np.max(np.abs(residuals[:, 3:]), axis=1)
                if rows
                else np.zeros(0, dtype=np.float64)
            )
        ],
        "maximum_absolute_residual_mm_by_mode": [
            float(value)
            for value in (
                np.max(np.abs(residuals), axis=0)
                if rows
                else np.zeros(6, dtype=np.float64)
            )
        ],
    }


def _snapshot(
    rows: Sequence[_ConstraintRow],
    body_ids: Sequence[str],
    relative_tolerance: float,
) -> dict[str, Any]:
    body_count = len(body_ids)
    dof_count = DOF_PER_BODY * body_count
    matrix = np.asarray([row.matrix for row in rows], dtype=np.float64)
    if not rows:
        matrix = np.zeros((0, dof_count), dtype=np.float64)
        singular_values = np.zeros((0,), dtype=np.float64)
        right_vectors = np.eye(dof_count, dtype=np.float64)
    else:
        if not np.isfinite(matrix).all():
            raise ValueError("constraint matrix contains nonfinite coefficients")
        _, singular_values, right_vectors = np.linalg.svd(matrix, full_matrices=True)
    leading = float(singular_values[0]) if singular_values.size else 0.0
    threshold = relative_tolerance * leading
    rank = int(np.count_nonzero(singular_values > threshold))
    nullspace = right_vectors[rank:, :]

    mode_participation = []
    body_energy = {body_id: 0.0 for body_id in body_ids}
    body_translation_energy = {body_id: 0.0 for body_id in body_ids}
    body_rotation_energy = {body_id: 0.0 for body_id in body_ids}
    for mode_index, mode in enumerate(nullspace):
        by_body = {}
        for body_index, body_id in enumerate(body_ids):
            start = DOF_PER_BODY * body_index
            components = mode[start : start + DOF_PER_BODY]
            translation = float(np.linalg.norm(components[:3]))
            rotation_scaled = float(np.linalg.norm(components[3:]))
            participation = math.sqrt(translation**2 + rotation_scaled**2)
            by_body[body_id] = {
                "translation_component_norm": translation,
                "scaled_rotation_component_norm": rotation_scaled,
                "combined_component_norm": participation,
            }
            body_energy[body_id] += participation**2
            body_translation_energy[body_id] += translation**2
            body_rotation_energy[body_id] += rotation_scaled**2
        mode_participation.append(
            {"mode_index": mode_index, "by_body": by_body}
        )
    nullity = int(nullspace.shape[0])
    participation_fraction = {
        body_id: (energy / nullity if nullity else 0.0)
        for body_id, energy in body_energy.items()
    }

    return {
        "matrix_shape": [int(matrix.shape[0]), int(matrix.shape[1])],
        "row_ids": [row.row_id for row in rows],
        "row_kinds": [row.kind for row in rows],
        "dimensionless_constraint_matrix": matrix.tolist(),
        "singular_values": [float(value) for value in singular_values],
        "relative_rank_tolerance": relative_tolerance,
        "rank_threshold": threshold,
        "rank": rank,
        "nullity": nullity,
        "nullspace_basis_scaled_coordinates": nullspace.tolist(),
        "dof_order_scaled_coordinates": [
            {"body_id": body_id, "components": list(DOF_ORDER_SCALED)}
            for body_id in body_ids
        ],
        "per_mode_body_participation": mode_participation,
        "nullspace_body_participation_fraction": participation_fraction,
        "nullspace_translation_participation_fraction": {
            body_id: (energy / nullity if nullity else 0.0)
            for body_id, energy in body_translation_energy.items()
        },
        "nullspace_scaled_rotation_participation_fraction": {
            body_id: (energy / nullity if nullity else 0.0)
            for body_id, energy in body_rotation_energy.items()
        },
    }


def audit_rigid_modes(
    bodies: Sequence[RigidBodyDatum | Mapping[str, Any]],
    active_contact_normals: Sequence[ActiveContactNormal | Mapping[str, Any]],
    thread_constraints: Sequence[ThreadConstraint | Mapping[str, Any]],
    *,
    mpc_constraints: Sequence[MpcKinematicConstraint | Mapping[str, Any]] = (),
    assumed_active_set_id: str,
    characteristic_length_mm: float,
    point_alignment_tolerance_mm: float,
    global_gauge_body_id: str | None = None,
    relative_rank_tolerance: float = 1e-10,
) -> dict[str, Any]:
    """Build contact/thread constraint rows and report their rigid-mode rank.

    Scaled coordinates are ``(u_x,u_y,u_z,L*omega_x,L*omega_y,L*omega_z)``
    for each body, where ``L`` is the explicit characteristic length in mm.
    A normal row at point ``p`` is
    ``n·[(u_a + omega_a×(p_a-o_a)) - (u_b + omega_b×(p_b-o_b))] = 0``.
    A thread row uses its declared direction and separate engagement points.
    An MPC row sums direction-projected point motions using each explicit term
    coefficient. This retains nodal master-element shape weights when supplied.
    Contact points must lie on a common line parallel to the contact normal,
    and thread endpoints on a common line parallel to their declared direction,
    within ``point_alignment_tolerance_mm``. MPC coefficients must preserve
    global translation and their weighted points must preserve global rotation
    within the same declared tolerance. The output still reports all six
    pre-gauge global rigid-motion residuals.

    ``physical_only`` excludes global gauge rows. ``with_global_gauge`` adds
    six coordinate-fixing rows for the named gauge body, if supplied. Those
    rows remove global coordinate freedom for analysis; they are not physical
    supports. An empty contact/thread set is valid and exposes free modes.
    """
    body_records = _body_records(bodies)
    contacts = _constraint_records(
        active_contact_normals, ActiveContactNormal, "active contact normal"
    )
    threads = _constraint_records(thread_constraints, ThreadConstraint, "thread constraint")
    mpcs = _constraint_records(
        mpc_constraints, MpcKinematicConstraint, "MPC kinematic constraint"
    )
    all_ids = [item.constraint_id for item in (*contacts, *threads, *mpcs)]
    if len(all_ids) != len(set(all_ids)):
        raise ValueError("constraint ids must be unique across contact and thread rows")

    active_set_id = _text(assumed_active_set_id, "assumed active-set id")
    characteristic_length = _number(
        characteristic_length_mm, "characteristic length", positive=True
    )
    point_alignment_tolerance = _number(
        point_alignment_tolerance_mm, "point-alignment tolerance"
    )
    if point_alignment_tolerance < 0:
        raise ValueError("point-alignment tolerance must be nonnegative")
    rank_rtol = _number(relative_rank_tolerance, "relative rank tolerance", positive=True)
    if rank_rtol >= 1.0:
        raise ValueError("relative rank tolerance must be less than one")

    body_ids = tuple(item.body_id for item in body_records)
    body_index = {body_id: index for index, body_id in enumerate(body_ids)}
    origins = {item.body_id: item.origin_xyz_mm for item in body_records}
    _check_constraint_owners(contacts, threads, mpcs, set(body_ids))
    _check_point_alignment(contacts, threads, mpcs, point_alignment_tolerance)
    if global_gauge_body_id is not None:
        global_gauge_body_id = _text(global_gauge_body_id, "global gauge body id")
        if global_gauge_body_id not in body_index:
            raise ValueError("global gauge body must be in the rigid-body inventory")

    physical_rows = tuple(
        [
            _contact_row(item, body_index, origins, len(body_ids), characteristic_length)
            for item in contacts
        ]
        + [
            _thread_row(item, body_index, origins, len(body_ids), characteristic_length)
            for item in threads
        ]
        + [
            _mpc_row(item, body_index, origins, len(body_ids), characteristic_length)
            for item in mpcs
        ]
    )
    gauge_rows = (
        _gauge_rows(global_gauge_body_id, body_index, len(body_ids))
        if global_gauge_body_id is not None
        else ()
    )
    with_gauge_rows = (*physical_rows, *gauge_rows)

    return {
        "schema": "wood_joint_patch_rigid_modes/v1",
        "status": "capacity_independent_kinematic_diagnostic_only",
        "claim_boundary": (
            "Rank and nullspace apply only to the caller-declared contact normals, "
            "thread translation directions, MPC terms, body datums, characteristic length, "
            "and optional coordinate gauge. Activity, geometry coincidence, "
            "nonlinear contact stability, tangential/friction transfer, bolt "
            "stiffness, material response, strength, and capacity are not inferred."
        ),
        "assumed_active_set_id": active_set_id,
        "body_ids_in_coordinate_order": list(body_ids),
        "body_origins_xyz_mm": {key: list(value) for key, value in origins.items()},
        "characteristic_length_mm": characteristic_length,
        "point_alignment_tolerance_mm": point_alignment_tolerance,
        "dof_order_scaled_coordinates": list(DOF_ORDER_SCALED),
        "rotation_coordinate_definition": "scaled_rotation = characteristic_length_mm * angular_rotation_rad",
        "relative_rank_tolerance": rank_rtol,
        "active_contact_normal_assumptions": [asdict(item) for item in contacts],
        "thread_constraint_assumptions": [asdict(item) for item in threads],
        "mpc_kinematic_assumptions": [asdict(item) for item in mpcs],
        "global_gauge_body_id": global_gauge_body_id,
        "global_gauge_interpretation": (
            "six coordinate-fixing rows; gauge only, not a physical support"
            if global_gauge_body_id is not None
            else "none supplied; common global rigid modes remain in physical-only nullspace"
        ),
        "physical_only": _snapshot(physical_rows, body_ids, rank_rtol),
        "with_global_gauge": _snapshot(with_gauge_rows, body_ids, rank_rtol),
        "global_rigid_motion_check_before_gauge": _global_rigid_motion_check(
            physical_rows,
            body_ids,
            origins,
            characteristic_length,
            point_alignment_tolerance,
        ),
    }
