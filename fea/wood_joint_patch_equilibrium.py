"""Signed wrench accounting for future wood-joint patch native results.

Inputs are already-integrated signed point actions from a result extractor. A
row is the force/couple acting on one named timber body, expressed in global
axes at its global point. This module shifts and sums those actions about
source-bound interface or member datums; it does not reconstruct contact
pressure, infer a distribution, or calculate a capacity.
"""

from __future__ import annotations

import math
from collections import defaultdict
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from typing import Any

from fea.wood_joint_patch_wrench import (
    Wrench,
    is_equilibrated,
    shift_wrench,
    to_local,
)

Vector = tuple[float, float, float]
Basis = tuple[Vector, Vector, Vector]


def _vector(value: Any, label: str) -> Vector:
    try:
        result = tuple(float(component) for component in value)
    except (TypeError, ValueError, OverflowError) as error:
        raise ValueError(f"{label} must be a finite 3-vector") from error
    if len(result) != 3 or not all(math.isfinite(component) for component in result):
        raise ValueError(f"{label} must be a finite 3-vector")
    return result  # type: ignore[return-value]


def _name(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label} must be a nonempty string")
    return value


def _add_vectors(left: Vector, right: Vector) -> Vector:
    return tuple(a + b for a, b in zip(left, right, strict=True))  # type: ignore[return-value]


def _add_wrenches(left: Wrench, right: Wrench) -> Wrench:
    return Wrench(
        _add_vectors(left.force_n, right.force_n),
        _add_vectors(left.moment_nmm, right.moment_nmm),
    )


def _sum_wrenches(wrenches: Iterable[Wrench]) -> Wrench:
    rows = tuple(wrenches)
    return Wrench(
        tuple(math.fsum(row.force_n[axis] for row in rows) for axis in range(3)),
        tuple(math.fsum(row.moment_nmm[axis] for row in rows) for axis in range(3)),
    )


@dataclass(frozen=True)
class InterfaceDatum:
    """Named interface moment origin and optional right-handed local axes.

    ``local_basis`` stores local x, y, and z unit axes as vectors expressed in
    global coordinates, matching ``bolted_joint_mechanics.to_local``.
    """

    interface_id: str
    point_xyz_mm: Vector
    local_basis: Basis | None = None

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "interface_id", _name(self.interface_id, "interface id")
        )
        object.__setattr__(
            self, "point_xyz_mm", _vector(self.point_xyz_mm, "interface datum")
        )
        if self.local_basis is not None:
            if len(self.local_basis) != 3:
                raise ValueError("local basis requires three axes")
            basis = tuple(
                _vector(axis, "local basis axis") for axis in self.local_basis
            )
            # Delegate orthonormality and handedness to the shared wrench helper.
            to_local(Wrench((0.0, 0.0, 0.0), (0.0, 0.0, 0.0)), basis)  # type: ignore[arg-type]
            object.__setattr__(self, "local_basis", basis)


@dataclass(frozen=True)
class SignedPointAction:
    """One signed force and optional free couple acting on ``owner_body``.

    ``interface_id`` assigns this action to a physical wood interface. The
    force sign convention is always "force on owner_body". ``source_id`` is
    optional provenance such as a contact-node or connector-action identity;
    when supplied it identifies one row within its interface/owner scope.
    """

    interface_id: str
    owner_body: str
    point_xyz_mm: Vector
    force_xyz_n: Vector
    couple_xyz_nmm: Vector = (0.0, 0.0, 0.0)
    source_id: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "interface_id", _name(self.interface_id, "interface id")
        )
        object.__setattr__(self, "owner_body", _name(self.owner_body, "owner body"))
        object.__setattr__(
            self, "point_xyz_mm", _vector(self.point_xyz_mm, "action point")
        )
        object.__setattr__(
            self, "force_xyz_n", _vector(self.force_xyz_n, "action force")
        )
        object.__setattr__(
            self, "couple_xyz_nmm", _vector(self.couple_xyz_nmm, "action couple")
        )
        if self.source_id is not None:
            object.__setattr__(self, "source_id", _name(self.source_id, "source id"))


@dataclass(frozen=True)
class InterfaceWrench:
    """Resultant actions on one body about one interface's declared datum."""

    interface_id: str
    owner_body: str
    datum_xyz_mm: Vector
    wrench_global: Wrench
    wrench_local: Wrench | None = None


@dataclass(frozen=True)
class ActionReactionCheck:
    interface_id: str
    owner_bodies: tuple[str, str]
    owner_wrenches_global: tuple[Wrench, Wrench]
    residual_global: Wrench
    passed: bool


@dataclass(frozen=True)
class MemberEquilibriumCheck:
    owner_body: str
    datum_xyz_mm: Vector
    interface_wrench_global: Wrench
    other_wrench_global: Wrench
    residual_global: Wrench
    passed: bool


def _coerce_action(value: SignedPointAction | Mapping[str, Any]) -> SignedPointAction:
    if isinstance(value, SignedPointAction):
        return value
    if not isinstance(value, Mapping):
        raise TypeError("action rows must be SignedPointAction records or mappings")
    try:
        return SignedPointAction(
            interface_id=value["interface_id"],
            owner_body=value["owner_body"],
            point_xyz_mm=value["point_xyz_mm"],
            force_xyz_n=value["force_xyz_n"],
            couple_xyz_nmm=value.get("couple_xyz_nmm", (0.0, 0.0, 0.0)),
            source_id=value.get("source_id"),
        )
    except KeyError as error:
        raise ValueError(f"action row missing {error.args[0]}") from error


def _coerce_datum(
    key: str, value: InterfaceDatum | Mapping[str, Any]
) -> InterfaceDatum:
    if isinstance(value, InterfaceDatum):
        datum = value
    elif isinstance(value, Mapping):
        declared_id = value.get("interface_id", key)
        if declared_id != key:
            raise ValueError(f"datum key {key!r} disagrees with its interface id")
        try:
            datum = InterfaceDatum(
                interface_id=declared_id,
                point_xyz_mm=value["point_xyz_mm"],
                local_basis=value.get("local_basis"),
            )
        except KeyError as error:
            raise ValueError(f"datum {key!r} missing {error.args[0]}") from error
    else:
        raise TypeError("interface datums must be records or mappings")
    if datum.interface_id != key:
        raise ValueError(f"datum key {key!r} disagrees with its interface id")
    return datum


def _datums(
    values: Mapping[str, InterfaceDatum | Mapping[str, Any]],
) -> dict[str, InterfaceDatum]:
    if not isinstance(values, Mapping) or not values:
        raise ValueError("at least one named interface datum is required")
    return {key: _coerce_datum(key, value) for key, value in values.items()}


def _tolerances(force_tolerance_n: float, moment_tolerance_nmm: float) -> None:
    try:
        finite = math.isfinite(force_tolerance_n) and math.isfinite(
            moment_tolerance_nmm
        )
    except TypeError as error:
        raise ValueError(
            "equilibrium tolerances must be finite and nonnegative"
        ) from error
    if not finite or force_tolerance_n < 0 or moment_tolerance_nmm < 0:
        raise ValueError("equilibrium tolerances must be finite and nonnegative")


def aggregate_interface_wrenches(
    actions: Iterable[SignedPointAction | Mapping[str, Any]],
    datums: Mapping[str, InterfaceDatum | Mapping[str, Any]],
) -> tuple[InterfaceWrench, ...]:
    """Sum signed point actions by interface and timber owner.

    Every point force is shifted to the source-bound interface datum using
    ``M_datum = M_point + (point - datum) x F``; an optional point couple is
    retained. A non-null ``source_id`` may appear only once for one interface
    owner. If a datum declares local axes, the same global resultant is also
    projected into those axes. Result ordering is deterministic.
    """
    normalized_datums = _datums(datums)
    totals: dict[tuple[str, str], list[Wrench]] = defaultdict(list)
    seen_source_ids: set[tuple[str, str, str]] = set()
    for raw_action in actions:
        action = _coerce_action(raw_action)
        if action.interface_id not in normalized_datums:
            raise ValueError(
                f"action references unknown interface {action.interface_id!r}"
            )
        if action.source_id is not None:
            source_key = (action.interface_id, action.owner_body, action.source_id)
            if source_key in seen_source_ids:
                raise ValueError(
                    "duplicate source id for one interface owner: "
                    f"{action.interface_id!r}/{action.owner_body!r}/{action.source_id!r}"
                )
            seen_source_ids.add(source_key)
        datum = normalized_datums[action.interface_id]
        at_point = Wrench(action.force_xyz_n, action.couple_xyz_nmm)
        totals[(action.interface_id, action.owner_body)].append(
            shift_wrench(at_point, action.point_xyz_mm, datum.point_xyz_mm)
        )

    result = []
    for (interface_id, owner_body), wrenches in sorted(totals.items()):
        datum = normalized_datums[interface_id]
        global_wrench = _sum_wrenches(wrenches)
        local_wrench = (
            to_local(global_wrench, datum.local_basis)
            if datum.local_basis is not None
            else None
        )
        result.append(
            InterfaceWrench(
                interface_id=interface_id,
                owner_body=owner_body,
                datum_xyz_mm=datum.point_xyz_mm,
                wrench_global=global_wrench,
                wrench_local=local_wrench,
            )
        )
    return tuple(result)


def _owner_pairs(
    owner_pairs: Mapping[str, Sequence[str]], datum_ids: set[str]
) -> dict[str, tuple[str, str]]:
    if not isinstance(owner_pairs, Mapping):
        raise TypeError("owner pairs must be keyed by interface id")
    if set(owner_pairs) != datum_ids:
        raise ValueError("owner pairs must cover exactly the declared interfaces")
    result: dict[str, tuple[str, str]] = {}
    for interface_id, raw_pair in owner_pairs.items():
        if isinstance(raw_pair, (str, bytes)) or not isinstance(raw_pair, Sequence):
            raise TypeError(f"interface {interface_id!r} requires two owner bodies")
        if len(raw_pair) != 2:
            raise ValueError(f"interface {interface_id!r} requires two owner bodies")
        first, second = (
            _name(raw_pair[0], "owner body"),
            _name(raw_pair[1], "owner body"),
        )
        if first == second:
            raise ValueError(f"interface {interface_id!r} owner bodies must differ")
        result[interface_id] = (first, second)
    return result


def _require_owner_coverage(
    aggregated: Sequence[InterfaceWrench],
    owner_pairs: Mapping[str, tuple[str, str]],
) -> None:
    by_interface: dict[str, set[str]] = defaultdict(set)
    for item in aggregated:
        by_interface[item.interface_id].add(item.owner_body)
    for interface_id, pair in owner_pairs.items():
        observed = by_interface.get(interface_id, set())
        if observed != set(pair):
            raise ValueError(
                f"interface {interface_id!r} action owners {sorted(observed)} "
                f"do not match {sorted(pair)}"
            )


def audit_action_reaction(
    actions: Iterable[SignedPointAction | Mapping[str, Any]],
    datums: Mapping[str, InterfaceDatum | Mapping[str, Any]],
    owner_pairs: Mapping[str, Sequence[str]],
    *,
    force_tolerance_n: float,
    moment_tolerance_nmm: float,
) -> tuple[ActionReactionCheck, ...]:
    """Check equal/opposite member resultants for each named interface.

    Rows must include actions on both members named by each ordered pair. This
    catches missing ownership output instead of treating an absent member as
    an implicit zero. The check sums all forces and moments about their common
    declared datum; it does not compare or prescribe the spatial distribution.
    """
    _tolerances(force_tolerance_n, moment_tolerance_nmm)
    normalized_datums = _datums(datums)
    normalized_pairs = _owner_pairs(owner_pairs, set(normalized_datums))

    aggregated = aggregate_interface_wrenches(actions, normalized_datums)
    _require_owner_coverage(aggregated, normalized_pairs)
    by_interface: dict[str, dict[str, Wrench]] = defaultdict(dict)
    for item in aggregated:
        by_interface[item.interface_id][item.owner_body] = item.wrench_global

    checks = []
    for interface_id, pair in sorted(normalized_pairs.items()):
        observed = by_interface.get(interface_id, {})
        if set(observed) != set(pair):
            raise ValueError(
                f"interface {interface_id!r} action owners {sorted(observed)} do not match {sorted(pair)}"
            )
        owner_wrenches = (observed[pair[0]], observed[pair[1]])
        residual = _sum_wrenches(owner_wrenches)
        checks.append(
            ActionReactionCheck(
                interface_id=interface_id,
                owner_bodies=pair,
                owner_wrenches_global=owner_wrenches,
                residual_global=residual,
                passed=is_equilibrated(
                    residual, force_tolerance_n, moment_tolerance_nmm
                ),
            )
        )
    return tuple(checks)


def audit_member_equilibrium(
    actions: Iterable[SignedPointAction | Mapping[str, Any]],
    interface_datums: Mapping[str, InterfaceDatum | Mapping[str, Any]],
    member_datums: Mapping[str, Sequence[float]],
    other_wrenches: Mapping[str, Wrench],
    owner_pairs: Mapping[str, Sequence[str]],
    *,
    force_tolerance_n: float,
    moment_tolerance_nmm: float,
) -> tuple[MemberEquilibriumCheck, ...]:
    """Audit each timber body's interface actions plus supplied other actions.

    ``other_wrenches`` contains already-signed applied-load, support-reaction,
    or other non-interface resultants, each expressed globally about that
    member's explicit datum. Supply an entry for every member, including an
    explicit zero wrench when there is no other action. ``owner_pairs`` maps
    each interface to its ordered pair of timber owners; action rows must cover
    both owners for every interface. All wrench components are forces on the
    owner body. For each member, interface resultants are shifted from their
    named interface datums to the member datum before summing. A zero residual
    is static equilibrium; no stiffness or resistance is inferred.
    """
    _tolerances(force_tolerance_n, moment_tolerance_nmm)
    if not isinstance(member_datums, Mapping) or not member_datums:
        raise ValueError("at least one member datum is required")
    normalized_member_datums = {
        _name(body, "member datum body"): _vector(point, f"datum for {body}")
        for body, point in member_datums.items()
    }
    if not isinstance(other_wrenches, Mapping):
        raise TypeError("other wrenches must be keyed by owner body")
    normalized_other: dict[str, Wrench] = {}
    for body, wrench in other_wrenches.items():
        body = _name(body, "other-wrench body")
        if body not in normalized_member_datums:
            raise ValueError(f"other wrench references unknown body {body!r}")
        if not isinstance(wrench, Wrench):
            raise TypeError("other wrenches must be Wrench values at the member datum")
        normalized_other[body] = wrench

    normalized_interfaces = _datums(interface_datums)
    normalized_pairs = _owner_pairs(owner_pairs, set(normalized_interfaces))
    expected_members = {body for pair in normalized_pairs.values() for body in pair}
    if set(normalized_member_datums) != expected_members:
        raise ValueError(
            "member datums must cover exactly the declared interface owners"
        )
    if set(normalized_other) != expected_members:
        raise ValueError("other wrenches must explicitly cover every declared member")
    aggregated = aggregate_interface_wrenches(actions, normalized_interfaces)
    _require_owner_coverage(aggregated, normalized_pairs)
    interface_rows: dict[str, list[Wrench]] = defaultdict(list)
    for item in aggregated:
        if item.owner_body not in normalized_member_datums:
            raise ValueError(
                f"interface action references unknown body {item.owner_body!r}"
            )
        interface_rows[item.owner_body].append(
            shift_wrench(
                item.wrench_global,
                item.datum_xyz_mm,
                normalized_member_datums[item.owner_body],
            )
        )

    checks = []
    for owner_body, member_datum in sorted(normalized_member_datums.items()):
        interface_wrench = _sum_wrenches(interface_rows.get(owner_body, ()))
        other_wrench = normalized_other[owner_body]
        residual = _add_wrenches(interface_wrench, other_wrench)
        checks.append(
            MemberEquilibriumCheck(
                owner_body=owner_body,
                datum_xyz_mm=member_datum,
                interface_wrench_global=interface_wrench,
                other_wrench_global=other_wrench,
                residual_global=residual,
                passed=is_equilibrated(
                    residual, force_tolerance_n, moment_tolerance_nmm
                ),
            )
        )
    return tuple(checks)
