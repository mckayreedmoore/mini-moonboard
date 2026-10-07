"""Independent static known answers for the JSON-only export audit."""

import numpy as np
import pytest

from scripts.thin_bolted_equilibrium_audit import (
    balances,
    vector,
    verify_attachments,
    verify_contacts,
    wrench,
)


def test_point_force_and_free_couple_transport_to_another_reference():
    value = wrench([0., -20., -100.], [2., 3., -10.], [0., 0., 0.], [7., 8., 9.])
    np.testing.assert_allclose(value, [0., -20., -100., -493., 208., -31.])
    moved = wrench([0., -20., -100.], [9., 12., 2.], [7., 9., 12.], [7., 8., 9.])
    np.testing.assert_allclose(moved, value)


def test_equal_opposite_internal_point_actions_leave_only_external_global_wrench():
    loads = [{"body": "one", "point_xyz_mm": [1., 0., 0.], "force_xyz_n": [0., 0., -100.]}]
    actions = [{"first": "one", "second": "two", "point_xyz_mm": [1., 0., 0.],
                "force_on_first_xyz_n": [0., 0., 100.]}]
    floors = [{"first": "two", "point_xyz_mm": [1., 0., 0.], "force_on_first_xyz_n": [0., 0., 100.]}]
    rows, applied, global_residual = balances(["one", "two"], loads, actions, floors, [0., 0., 0.])
    np.testing.assert_allclose(rows["one"], np.zeros(6))
    np.testing.assert_allclose(rows["two"], np.zeros(6))
    np.testing.assert_allclose(global_residual, np.zeros(6))
    np.testing.assert_allclose(applied, [0., 0., -100., 0., 100., 0.])


def test_missing_backing_rows_and_nonfinite_wrenches_are_rejected():
    with pytest.raises(ValueError, match="288"):
        verify_contacts({"raw_fittings": []}, [])
    with pytest.raises(ValueError, match="finite"):
        vector([1., float("nan"), 3.])


@pytest.mark.parametrize("changed", ["force", "moment", "receiver"])
def test_component_export_cannot_use_a_different_attachment_wrench(changed):
    axes, rows = [], []
    for i in range(72):
        port = {"angle_id": str(i), "flange": "beam", "receiver": "wood", "entry_xyz_mm": [i, 0., 0.]}
        axes.append({"id": str(i), "attachments": [port]})
        rows.append({"axis_id": str(i), **port, "point_xyz_mm": port["entry_xyz_mm"],
                     "first": "wood", "second": str(i), "force_on_first_xyz_n": [1., 2., 3.],
                     "force_on_receiver_xyz_n": [1., 2., 3.], "moment_at_point_model_xyz_nmm": [0., 0., 0.],
                     "moment_on_receiver_at_point_xyz_nmm": [0., 0., 0.]})
    verify_attachments({"installed_axes": axes}, rows)
    if changed == "force":
        rows[0]["force_on_receiver_xyz_n"] = [1., 2., 30.]
    elif changed == "moment":
        rows[0]["moment_on_receiver_at_point_xyz_nmm"] = [0., 0., 30.]
    else:
        rows[0]["receiver"] = "another_receiver"
    with pytest.raises(ValueError, match="differ"):
        verify_attachments({"installed_axes": axes}, rows)
