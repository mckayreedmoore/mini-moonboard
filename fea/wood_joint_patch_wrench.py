"""Small standard-library wrench primitives for wood-joint patch accounting.

This module deliberately does not import ``mini_moonboard``: importing that
package initializes the CAD model and requires CadQuery, which is absent from
the pinned native solver image. Wrenches are immutable, global-axis values;
forces use N, moments use N-mm, and points use mm.
"""

from __future__ import annotations

import math
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from typing import Any

Vector = tuple[float, float, float]
Basis = tuple[Vector, Vector, Vector]


def _vector(value: Any, label: str) -> Vector:
    if isinstance(value, (str, bytes)):
        raise TypeError(f"{label} must be a finite 3-vector")
    try:
        vector = tuple(float(component) for component in value)
    except (TypeError, ValueError, OverflowError) as error:
        raise ValueError(f"{label} must be a finite 3-vector") from error
    if len(vector) != 3 or not all(math.isfinite(component) for component in vector):
        raise ValueError(f"{label} must be a finite 3-vector")
    return vector  # type: ignore[return-value]


def _dot(left: Vector, right: Vector) -> float:
    return sum(a * b for a, b in zip(left, right, strict=True))


def _add(left: Vector, right: Vector) -> Vector:
    return tuple(a + b for a, b in zip(left, right, strict=True))  # type: ignore[return-value]


def _sub(left: Vector, right: Vector) -> Vector:
    return tuple(a - b for a, b in zip(left, right, strict=True))  # type: ignore[return-value]


def cross(left: Vector, right: Vector) -> Vector:
    """Return the right-handed cross product of two three-vectors."""
    a = _vector(left, "left vector")
    b = _vector(right, "right vector")
    return (
        a[1] * b[2] - a[2] * b[1],
        a[2] * b[0] - a[0] * b[2],
        a[0] * b[1] - a[1] * b[0],
    )


@dataclass(frozen=True)
class Wrench:
    """Immutable force and moment, expressed in global axes at one point.

    This is a nominal type boundary for the patch adapter. If another module
    supplies a different Wrench class, copy its numeric components explicitly
    into this class before calling these helpers.
    """

    force_n: Vector
    moment_nmm: Vector

    def __post_init__(self) -> None:
        object.__setattr__(self, "force_n", _vector(self.force_n, "force"))
        object.__setattr__(self, "moment_nmm", _vector(self.moment_nmm, "moment"))


def shift_wrench(reported: Wrench, p_report_mm: Vector, p_joint_mm: Vector) -> Wrench:
    """Move a wrench using ``M_joint = M_report + (p_report-p_joint) x F``."""
    if not isinstance(reported, Wrench):
        raise TypeError("reported wrench must be a wood-joint patch Wrench")
    report = _vector(p_report_mm, "reported point")
    joint = _vector(p_joint_mm, "joint point")
    return Wrench(
        reported.force_n,
        _add(reported.moment_nmm, cross(_sub(report, joint), reported.force_n)),
    )


def to_local(wrench: Wrench, basis: Sequence[Vector]) -> Wrench:
    """Project onto unit, orthogonal, right-handed local axes (tolerance 1e-9)."""
    if not isinstance(wrench, Wrench):
        raise TypeError("wrench must be a wood-joint patch Wrench")
    try:
        if len(basis) != 3:
            raise ValueError("local basis requires u, v, w")
        axes = tuple(_vector(axis, "basis axis") for axis in basis)
    except TypeError as error:
        raise ValueError("local basis requires three finite axes") from error
    tolerance = 1e-9
    if (
        any(abs(_dot(axis, axis) - 1.0) > tolerance for axis in axes)
        or any(
            abs(_dot(axes[i], axes[j])) > tolerance for i, j in ((0, 1), (0, 2), (1, 2))
        )
        or abs(_dot(cross(axes[0], axes[1]), axes[2]) - 1.0) > tolerance
    ):
        raise ValueError("local basis must be orthonormal and right-handed")
    return Wrench(
        tuple(_dot(wrench.force_n, axis) for axis in axes),
        tuple(_dot(wrench.moment_nmm, axis) for axis in axes),
    )


def equilibrium_residual(
    joint: Wrench,
    fastener_forces: Iterable[tuple[Vector, Vector]],
    contact_force: Vector = (0.0, 0.0, 0.0),
    other_force: Vector = (0.0, 0.0, 0.0),
) -> Wrench:
    """Return applied minus recovered force/moment at the joint origin.

    Each fastener row is ``(offset_mm, force_n)``. Contact and other forces
    act at the joint origin; shift them before calling if they act elsewhere.
    """
    if not isinstance(joint, Wrench):
        raise TypeError("joint wrench must be a wood-joint patch Wrench")
    force = _add(
        _vector(contact_force, "contact force"), _vector(other_force, "other force")
    )
    moment: Vector = (0.0, 0.0, 0.0)
    for offset, fastener_force in fastener_forces:
        point = _vector(offset, "fastener offset")
        action = _vector(fastener_force, "fastener force")
        force = _add(force, action)
        moment = _add(moment, cross(point, action))
    return Wrench(_sub(joint.force_n, force), _sub(joint.moment_nmm, moment))


def is_equilibrated(
    residual: Wrench,
    force_tolerance_n: float = 1e-6,
    moment_tolerance_nmm: float = 1e-6,
) -> bool:
    """Test each residual component against its caller-supplied tolerance."""
    if not isinstance(residual, Wrench):
        raise TypeError("residual must be a wood-joint patch Wrench")
    return (
        max(map(abs, residual.force_n)) <= force_tolerance_n
        and max(map(abs, residual.moment_nmm)) <= moment_tolerance_nmm
    )
