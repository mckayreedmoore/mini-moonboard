"""Validate batch-result identity, not resistance or native-model correctness.

Keep this module dependency-free so archive-label checks can run without CAD,
Docker or a solver. The explicit legacy no-slip scope is emitted by
fea.current_response_run.assess. A new support formulation needs its own
reviewed producer/consumer contract; a label alone never authenticates physics.
"""
import math
from collections.abc import Mapping, Sequence
from typing import Any

NO_SLIP_SCOPE = (
    'Conditional no sliding; normal contact may open; no friction coefficient qualification'
)


def _mapping(value: Any, label: str) -> Mapping:
    if not isinstance(value, Mapping):
        raise ValueError(f'{label} must be an object')  # noqa: TRY004 -- invalid report value
    return value


def _number(value: Any, label: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(  # noqa: TRY004 -- invalid report value
            f'{label} must be a finite number, not a boolean'
        )
    try:
        result = float(value)
    except (ValueError, OverflowError) as exc:
        raise ValueError(f'{label} must be a finite number') from exc
    if not math.isfinite(result):
        raise ValueError(f'{label} must be a finite number')
    return result


def _vector(value: Any, size: int, label: str) -> tuple[float, ...]:
    if (not isinstance(value, Sequence) or isinstance(value, (str, bytes))
            or len(value) != size):
        raise ValueError(f'{label} must contain {size} numbers')
    return tuple(_number(v, label) for v in value)


def validate_floor_model(report: Mapping, friction_mu: float | None = None) -> None:
    """Reject finite-friction/no-slip substitution before seeding or archiving.

    This checks the declared formulation only. It does not validate reactions,
    contact activity, geometry, source snapshots or native solver artifacts.
    """
    report = _mapping(report, 'report')
    parameters = _mapping(report.get('parameters'), 'parameters')
    basis = parameters.get('floor_friction_assumption')
    law = report.get('floor_friction_law')
    if friction_mu is None:
        if basis is not None or law is not None:
            raise ValueError('No-slip request cannot consume finite-friction evidence')
        if report.get('floor_scope') != NO_SLIP_SCOPE:
            raise ValueError('Require the explicit supported no-slip floor scope')
        return
    mu = _number(friction_mu, 'requested friction coefficient')
    if mu <= 0:
        raise ValueError('Requested friction coefficient must be positive')
    basis = _mapping(basis, 'floor_friction_assumption')
    actual_mu = _number(basis.get('mu'), 'reported friction coefficient')
    # An exact scenario parameter match is intentional, as in the existing runner.
    if (actual_mu != mu or basis.get('per_cell_coulomb') is not True
            or basis.get('centroid_tangent_springs_removed') is not True):
        raise ValueError('Require the requested distributed-cell friction law and mu')
    law = _mapping(law, 'floor_friction_law')
    _mapping(law.get('feet'), 'floor_friction_law.feet')


def validate_case_identity(
    report: Mapping,
    *,
    expected_candidate: str,
    expected_hold: str,
    expected_pounds: float,
    expected_horizontal_force: Sequence[float],
    friction_mu: float | None = None,
) -> None:
    """Bind a solved/reused report to its requested batch case before publication.

    Forces use the current runner's world X/Y horizontal axes. The vertical
    force must be finite but is not independently reconstructed here; the native
    load definition and equilibrium checks remain authoritative for that duty.
    The 1e-9 absolute comparison is serialization tolerance, not a fabrication or
    physical load tolerance. No relative tolerance masks a changed scenario.
    """
    report = _mapping(report, 'report')
    if not expected_candidate or not expected_hold:
        raise ValueError('Expected candidate and hold must be explicit')
    if report.get('numerically_accepted') is not True:
        raise ValueError('Cannot reuse a numerically rejected response')
    if report.get('candidate') != expected_candidate:
        raise ValueError('Case candidate does not match requested candidate')
    parameters = _mapping(report.get('parameters'), 'parameters')
    if parameters.get('hold') != expected_hold:
        raise ValueError('Case hold does not match requested hold')
    expected_weight = _number(expected_pounds, 'requested pounds')
    actual_weight = _number(parameters.get('pounds'), 'reported pounds')
    if expected_weight <= 0 or actual_weight <= 0:
        raise ValueError('Case pounds must be positive')
    if not math.isclose(actual_weight, expected_weight, rel_tol=0., abs_tol=1.e-9):
        raise ValueError('Case pounds do not match requested load')
    actual_force = _vector(parameters.get('force_xyz_n'), 3, 'force_xyz_n')
    expected_force = _vector(expected_horizontal_force, 2, 'horizontal force')
    if any(not math.isclose(a, b, rel_tol=0., abs_tol=1.e-9)
           for a, b in zip(actual_force[:2], expected_force, strict=True)):
        raise ValueError('Case horizontal force does not match requested direction/load')
    validate_floor_model(report, friction_mu)
