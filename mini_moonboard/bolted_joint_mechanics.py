"""Mechanics semantics for the AB90 prototype, without resistance claims.

Vectors use (x, y, z), forces are N, moments are N-mm, and coordinates are mm.
The functions describe accounting and contact behavior; they do not calculate
allowable bolt, timber, or plate capacity.
"""

from dataclasses import dataclass
import math


Vector = tuple[float, float, float]


def _add(a: Vector, b: Vector) -> Vector:
    return tuple(x + y for x, y in zip(a, b, strict=True))


def _sub(a: Vector, b: Vector) -> Vector:
    return tuple(x - y for x, y in zip(a, b, strict=True))


def _dot(a: Vector, b: Vector) -> float:
    return sum(x * y for x, y in zip(a, b, strict=True))


def cross(a: Vector, b: Vector) -> Vector:
    return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])


def _finite(vector: Vector, label: str) -> None:
    if len(vector) != 3 or not all(math.isfinite(value) for value in vector):
        raise ValueError(f"{label} must be a finite 3-vector")


@dataclass(frozen=True)
class Wrench:
    force_n: Vector
    moment_nmm: Vector

    def __post_init__(self) -> None:
        _finite(self.force_n, "force")
        _finite(self.moment_nmm, "moment")


def shift_wrench(reported: Wrench, p_report_mm: Vector, p_joint_mm: Vector) -> Wrench:
    """Move a wrench using M_joint = M_report + (p_report-p_joint) x F."""
    _finite(p_report_mm, "reported point")
    _finite(p_joint_mm, "joint point")
    return Wrench(reported.force_n, _add(reported.moment_nmm, cross(_sub(p_report_mm, p_joint_mm), reported.force_n)))


def to_local(wrench: Wrench, basis: tuple[Vector, Vector, Vector]) -> Wrench:
    """Transform global force/moment vectors into a supplied local basis."""
    if len(basis) != 3:
        raise ValueError("local basis requires u, v, w")
    return Wrench(tuple(_dot(wrench.force_n, axis) for axis in basis), tuple(_dot(wrench.moment_nmm, axis) for axis in basis))


def equilibrium_residual(
    joint: Wrench,
    fastener_forces: tuple[tuple[Vector, Vector], ...],
    contact_force: Vector = (0.0, 0.0, 0.0),
    other_force: Vector = (0.0, 0.0, 0.0),
) -> Wrench:
    """Return applied minus recovered force/moment at the joint origin.

    Each fastener pair is ``(offset_mm, force_n)``. Contact and other force
    terms act at the joint origin; callers must shift them before use when they
    act elsewhere.
    """
    force = _add(contact_force, other_force)
    moment = (0.0, 0.0, 0.0)
    for offset, fastener_force in fastener_forces:
        _finite(offset, "fastener offset")
        _finite(fastener_force, "fastener force")
        force = _add(force, fastener_force)
        moment = _add(moment, cross(offset, fastener_force))
    return Wrench(_sub(joint.force_n, force), _sub(joint.moment_nmm, moment))


def is_equilibrated(residual: Wrench, force_tolerance_n: float = 1e-6, moment_tolerance_nmm: float = 1e-6) -> bool:
    return max(map(abs, residual.force_n)) <= force_tolerance_n and max(map(abs, residual.moment_nmm)) <= moment_tolerance_nmm


def compression_only_contact(force_n: Vector, normal: Vector) -> Vector:
    """Project contact force onto a normal and remove opening tension.

    Positive normal projection is the adopted compression convention. A force
    trying to open the interface returns zero contact force rather than an
    artificial tensile tie.
    """
    _finite(force_n, "contact force")
    _finite(normal, "contact normal")
    length = math.sqrt(_dot(normal, normal))
    if length == 0:
        raise ValueError("contact normal must be nonzero")
    unit = tuple(value / length for value in normal)
    compression = max(0.0, _dot(force_n, unit))
    return tuple(compression * value for value in unit)


def clearance_response(force_n: float, stiffness_n_per_mm: float, clearance_mm: float) -> float:
    """Return bearing displacement after a declared free-clearance gap."""
    if stiffness_n_per_mm <= 0 or clearance_mm < 0 or not math.isfinite(force_n):
        raise ValueError("invalid clearance/stiffness input")
    return max(0.0, abs(force_n) / stiffness_n_per_mm - clearance_mm)


def require_unique_physical_fasteners(fastener_ids: tuple[str, ...]) -> None:
    if len(fastener_ids) != len(set(fastener_ids)):
        raise ValueError("shared physical fastener cannot be duplicated in one load path")
