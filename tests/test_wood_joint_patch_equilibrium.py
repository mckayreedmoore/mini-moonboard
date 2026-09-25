"""Signed point-action aggregation and independent patch equilibrium checks."""

import pytest

from fea.wood_joint_patch_equilibrium import (
    InterfaceDatum,
    SignedPointAction,
    aggregate_interface_wrenches,
    audit_action_reaction,
    audit_member_equilibrium,
)
from fea.wood_joint_patch_wrench import (
    Wrench,
    equilibrium_residual,
    is_equilibrated,
    shift_wrench,
    to_local,
)

DATUM = (10.0, -20.0, 5.0)
ROTATED_BASIS = (
    (0.0, 1.0, 0.0),
    (-1.0, 0.0, 0.0),
    (0.0, 0.0, 1.0),
)
INTERFACE = "g7-right-inner"
OWNERS = ("right_service_rail", "full_stock_cleat")


def _actions():
    # Two independent off-centre point forces and explicit couples give one
    # simultaneous six-component resultant on the first owner.
    rows = (
        SignedPointAction(
            INTERFACE,
            OWNERS[0],
            (13.0, -18.0, 6.0),
            (4.0, -2.0, 5.0),
            (1.0, 0.0, -3.0),
            "contact-cell-a",
        ),
        SignedPointAction(
            INTERFACE,
            OWNERS[0],
            (8.0, -16.0, 9.0),
            (7.0, -5.0, 1.0),
            (0.0, 2.0, 4.0),
            "bolt-transfer-b",
        ),
        SignedPointAction(
            INTERFACE,
            OWNERS[1],
            (13.0, -18.0, 6.0),
            (-4.0, 2.0, -5.0),
            (-1.0, 0.0, 3.0),
            "contact-cell-a-opposite",
        ),
        SignedPointAction(
            INTERFACE,
            OWNERS[1],
            (8.0, -16.0, 9.0),
            (-7.0, 5.0, -1.0),
            (0.0, -2.0, -4.0),
            "bolt-transfer-b-opposite",
        ),
    )
    return rows


def test_off_center_six_component_resultant_and_rotated_local_axes():
    rows = _actions()
    datums = {
        INTERFACE: InterfaceDatum(INTERFACE, DATUM, ROTATED_BASIS),
    }

    result = aggregate_interface_wrenches(rows, datums)
    by_owner = {item.owner_body: item for item in result}

    first = by_owner[OWNERS[0]]
    assert first.datum_xyz_mm == DATUM
    assert first.wrench_global == Wrench((11.0, -7.0, 6.0), (37.0, 21.0, -31.0))
    assert first.wrench_local == Wrench((-7.0, -11.0, 6.0), (21.0, -37.0, -31.0))
    assert by_owner[OWNERS[1]].wrench_global == Wrench(
        (-11.0, 7.0, -6.0), (-37.0, -21.0, 31.0)
    )

    checks = audit_action_reaction(
        rows,
        datums,
        {INTERFACE: OWNERS},
        force_tolerance_n=1e-9,
        moment_tolerance_nmm=1e-9,
    )
    assert len(checks) == 1
    assert checks[0].residual_global == Wrench((0.0, 0.0, 0.0), (0.0, 0.0, 0.0))
    assert checks[0].passed


def test_member_equilibrium_shifts_interface_wrench_to_each_member_datum():
    rows = _actions()
    datums = {INTERFACE: InterfaceDatum(INTERFACE, DATUM, ROTATED_BASIS)}
    member_datums = {
        OWNERS[0]: (0.0, 0.0, 0.0),
        OWNERS[1]: (30.0, 10.0, -2.0),
    }
    # Expected non-interface actions are specified at each member origin.
    # They balance the independently shifted interface resultants.
    other = {
        OWNERS[0]: Wrench((-11.0, 7.0, -6.0), (48.0, -16.0, -119.0)),
        OWNERS[1]: Wrench((11.0, -7.0, 6.0), (-94.0, 218.0, 439.0)),
    }

    checks = audit_member_equilibrium(
        rows,
        datums,
        member_datums,
        other,
        {INTERFACE: OWNERS},
        force_tolerance_n=1e-9,
        moment_tolerance_nmm=1e-9,
    )
    by_body = {item.owner_body: item for item in checks}

    assert by_body[OWNERS[0]].interface_wrench_global == Wrench(
        (11.0, -7.0, 6.0), (-48.0, 16.0, 119.0)
    )
    assert by_body[OWNERS[1]].interface_wrench_global == Wrench(
        (-11.0, 7.0, -6.0), (94.0, -218.0, -439.0)
    )
    assert all(item.passed for item in checks)

    perturbed = dict(other)
    perturbed[OWNERS[0]] = Wrench((-10.5, 7.0, -6.0), (48.0, -16.0, -119.0))
    failed = audit_member_equilibrium(
        rows,
        datums,
        member_datums,
        perturbed,
        {INTERFACE: OWNERS},
        force_tolerance_n=0.1,
        moment_tolerance_nmm=1.0,
    )
    assert not {item.owner_body: item for item in failed}[OWNERS[0]].passed


def test_action_reaction_rejects_missing_owner_or_unbalanced_resultant():
    datum = {INTERFACE: InterfaceDatum(INTERFACE, DATUM)}
    with pytest.raises(ValueError, match="action owners"):
        audit_action_reaction(
            _actions()[:2],
            datum,
            {INTERFACE: OWNERS},
            force_tolerance_n=0.1,
            moment_tolerance_nmm=1.0,
        )

    unbalanced = list(_actions())
    unbalanced[-1] = SignedPointAction(
        INTERFACE,
        OWNERS[1],
        (8.0, -16.0, 9.0),
        (-6.5, 5.0, -1.0),
        (0.0, -2.0, -4.0),
    )
    check = audit_action_reaction(
        unbalanced,
        datum,
        {INTERFACE: OWNERS},
        force_tolerance_n=0.1,
        moment_tolerance_nmm=1.0,
    )[0]
    assert check.residual_global.force_n == pytest.approx((0.5, 0.0, 0.0))
    assert not check.passed


@pytest.mark.parametrize(
    "bad_action",
    [
        {
            "interface_id": "unknown",
            "owner_body": "a",
            "point_xyz_mm": (0, 0, 0),
            "force_xyz_n": (1, 0, 0),
        },
        {
            "interface_id": INTERFACE,
            "owner_body": "a",
            "point_xyz_mm": (0, 0, 0),
            "force_xyz_n": (1, float("nan"), 0),
        },
    ],
)
def test_aggregation_rejects_unknown_interface_and_nonfinite_action(bad_action):
    with pytest.raises(ValueError):
        aggregate_interface_wrenches(
            [bad_action], {INTERFACE: InterfaceDatum(INTERFACE, DATUM)}
        )


def test_member_equilibrium_requires_named_datums_and_tolerances():
    datums = {INTERFACE: InterfaceDatum(INTERFACE, DATUM)}
    member_datums = {body: (0.0, 0.0, 0.0) for body in OWNERS}
    zero_other = {body: Wrench((0.0, 0.0, 0.0), (0.0, 0.0, 0.0)) for body in OWNERS}

    with pytest.raises(ValueError, match="explicitly cover every declared member"):
        audit_member_equilibrium(
            _actions(),
            datums,
            member_datums,
            {},
            {INTERFACE: OWNERS},
            force_tolerance_n=1.0,
            moment_tolerance_nmm=1.0,
        )

    with pytest.raises(ValueError, match="action owners"):
        audit_member_equilibrium(
            _actions()[:2],
            datums,
            member_datums,
            zero_other,
            {INTERFACE: OWNERS},
            force_tolerance_n=1.0,
            moment_tolerance_nmm=1.0,
        )


def test_explicit_zero_actions_and_wrenches_are_valid_zero_load_evidence():
    zero = (0.0, 0.0, 0.0)
    zero_actions = (
        SignedPointAction(INTERFACE, OWNERS[0], DATUM, zero, source_id="owner-a-zero"),
        SignedPointAction(INTERFACE, OWNERS[1], DATUM, zero, source_id="owner-b-zero"),
    )
    zero_wrench = Wrench(zero, zero)

    checks = audit_member_equilibrium(
        zero_actions,
        {INTERFACE: InterfaceDatum(INTERFACE, DATUM)},
        {body: DATUM for body in OWNERS},
        {body: zero_wrench for body in OWNERS},
        {INTERFACE: OWNERS},
        force_tolerance_n=0.0,
        moment_tolerance_nmm=0.0,
    )

    assert len(checks) == 2
    assert all(check.passed for check in checks)


def test_duplicate_source_id_within_interface_owner_is_rejected():
    duplicated = (*_actions(), _actions()[0])
    with pytest.raises(ValueError, match="duplicate source id"):
        aggregate_interface_wrenches(
            duplicated, {INTERFACE: InterfaceDatum(INTERFACE, DATUM)}
        )


def test_wrench_primitives_match_historical_helper_when_cad_is_available():
    try:
        import mini_moonboard.bolted_joint_mechanics as historical
    except ModuleNotFoundError as error:
        if error.name == "cadquery":
            pytest.skip("historical mini_moonboard import requires CadQuery")
        raise

    wrench = Wrench((11.0, -7.0, 6.0), (37.0, 21.0, -31.0))
    old_wrench = historical.Wrench(wrench.force_n, wrench.moment_nmm)
    shifted = shift_wrench(wrench, (13.0, -18.0, 6.0), DATUM)
    old_shifted = historical.shift_wrench(old_wrench, (13.0, -18.0, 6.0), DATUM)
    basis = ROTATED_BASIS
    local = to_local(shifted, basis)
    old_local = historical.to_local(old_shifted, basis)

    assert shifted.force_n == old_shifted.force_n
    assert shifted.moment_nmm == pytest.approx(old_shifted.moment_nmm)
    assert local.force_n == pytest.approx(old_local.force_n)
    assert local.moment_nmm == pytest.approx(old_local.moment_nmm)

    residual = equilibrium_residual(
        wrench,
        (((0.0, 2.0, 0.0), (10.0, 0.0, 0.0)),),
        contact_force=(0.0, 0.0, 2.0),
        other_force=(-1.0, 0.0, 0.0),
    )
    old_residual = historical.equilibrium_residual(
        old_wrench,
        (((0.0, 2.0, 0.0), (10.0, 0.0, 0.0)),),
        contact_force=(0.0, 0.0, 2.0),
        other_force=(-1.0, 0.0, 0.0),
    )
    assert residual.force_n == pytest.approx(old_residual.force_n)
    assert residual.moment_nmm == pytest.approx(old_residual.moment_nmm)
    assert is_equilibrated(residual) == historical.is_equilibrated(old_residual)
