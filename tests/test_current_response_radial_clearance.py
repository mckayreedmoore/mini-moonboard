"""Coupled circular clearance for candidate barrel-bolt lateral springs."""

from types import SimpleNamespace

import numpy as np
import pytest

from fea import current_response_run as response


def radial_springs(*, active=False, normal=None, stiffness=1000.0):
    rows = []
    for dof in (2, 3):
        row = {
            "name": "bolt__radial_clearance",
            "connector_name": "bolt",
            "nodes": [1, 2],
            "dof": dof,
            "stiffness_n_per_mm": stiffness,
            "bearing_closed_assumption": True,
            "radial_clearance_assumption": True,
            "radial_clearance_mm": 0.575,
            "active": active,
        }
        if normal is not None:
            row["clearance_contact_normal"] = list(normal)
        rows.append(row)
    return rows


def displacements(y, z):
    return {1: np.zeros(3), 2: np.array([0.0, y, z])}


def test_diagonal_motion_switches_coupled_group_despite_both_components_in_gap():
    record = {"springs": radial_springs()}

    rows = response.radial_clearance_state(record, displacements(0.5, 0.4))

    assert len(rows) == 1
    assert rows[0]["radius_mm"] == pytest.approx(np.hypot(0.5, 0.4))
    assert rows[0]["proposed_contact_normal"] == pytest.approx(
        np.array([0.5, 0.4]) / np.hypot(0.5, 0.4)
    )
    assert rows[0]["radial_clearance_assumption_satisfied"] is False


def test_engaged_force_removes_clearance_and_reversal_releases():
    normal = np.array([0.6, 0.8])
    relative = (0.575 + 0.1) * normal
    engaged = response.radial_clearance_state(
        {"springs": radial_springs(active=True, normal=normal)},
        displacements(*relative),
    )[0]

    assert engaged["radial_clearance_assumption_satisfied"] is True
    assert engaged["physical_force_local_n"] == pytest.approx(100.0 * normal)

    reversed_trial = response.radial_clearance_state(
        {"springs": radial_springs(active=True, normal=(1.0, 0.0))},
        displacements(0.5, 0.0),
    )[0]
    assert reversed_trial["proposed_contact_normal"] is None
    assert reversed_trial["physical_force_local_n"] == pytest.approx([-75.0, 0.0])
    assert reversed_trial["radial_clearance_assumption_satisfied"] is False

    opposite_trial = response.radial_clearance_state(
        {"springs": radial_springs(active=True, normal=(1.0, 0.0))},
        displacements(-0.8, 0.0),
    )[0]
    assert opposite_trial["proposed_contact_normal"] is None
    open_trial = response.radial_clearance_state(
        {"springs": radial_springs()}, displacements(-0.8, 0.0)
    )[0]
    assert open_trial["proposed_contact_normal"] == pytest.approx([-1.0, 0.0])


def test_reference_loads_are_balanced_and_absent_while_open():
    structure = SimpleNamespace(springs=radial_springs(), loads={3: np.array([1., 2., 3.])})
    base = {node: force.copy() for node, force in structure.loads.items()}

    assert response.configure_radial_clearance(
        structure, {"bolt__radial_clearance": None}, base
    ) == []
    assert set(structure.loads) == {3}

    corrections = response.configure_radial_clearance(
        structure, {"bolt__radial_clearance": (0.6, 0.8)}, base
    )
    expected = np.array([0.0, 345.0, 460.0])
    assert structure.loads[1] == pytest.approx(-expected)
    assert structure.loads[2] == pytest.approx(expected)
    assert structure.loads[3] == pytest.approx([1.0, 2.0, 3.0])
    assert corrections[0]["force_on_first_local_n"] == pytest.approx(-expected)


def test_physical_force_aggregates_axial_and_offset_corrected_lateral_components():
    owner = {
        "first": "entry",
        "second": "receiver",
        "point": [1.0, 2.0, 3.0],
        "axis": [1.0, 0.0, 0.0],
        "force_basis": np.eye(3).tolist(),
    }
    record = {
        "springs": [
            {
                "name": "bolt",
                "nodes": [1, 2],
                "dof": 1,
                "stiffness_n_per_mm": 1000.0,
                "active": True,
            },
            *radial_springs(active=True, normal=(0.6, 0.8)),
        ],
        "connection_ownership": {"bolt": owner},
        "radial_clearance_ownership": {
            "bolt__radial_clearance": {
                **owner,
                "connector_name": "bolt",
                "radial_clearance_assumption": True,
            }
        },
    }
    result = {
        "connector_forces": {
            "bolt": {"force_on_first_xyz_n": [10.0, 0.0, 0.0]},
            "bolt__radial_clearance": {
                "force_on_first_xyz_n": [0.0, 405.0, 540.0]
            },
        }
    }

    physical = response.physical_forces(record, result)

    assert set(physical) == {"bolt"}
    assert physical["bolt"]["force_on_first_xyz_n"] == pytest.approx([10., 60., 80.])
    assert physical["bolt"]["axial_along_installation_direction_n"] == pytest.approx(10.)
    assert physical["bolt"]["transverse_shear_n"] == pytest.approx(100.)


def test_initial_active_set_keeps_radial_group_open_and_axial_independent():
    springs = [
        {"name": "face", "dof": 1, "bearing_closed_assumption": True},
        {"name": "bolt", "dof": 1, "bearing_closed_assumption": True,
         "tension_only_assumption": True},
        *radial_springs(),
    ]
    metadata = {
        "connection_ownership": {
            "face": {"first": "wood", "second": "wood"},
            "bolt": {"first": "wood", "second": "wood"},
        }
    }

    active, axial = response.initial_active_set(
        SimpleNamespace(springs=springs), metadata
    )

    assert active == {"face", "bolt"}
    assert axial == {"bolt"}


def test_radial_checkpoint_requires_exact_inventory_and_unit_normals():
    groups = response.radial_clearance_inventory(radial_springs())

    assert response.initial_radial_clearance_state(groups) == {
        "bolt__radial_clearance": None
    }
    assert response.initial_radial_clearance_state(
        groups, {"bolt__radial_clearance": [0.6, 0.8]}
    ) == {"bolt__radial_clearance": [0.6, 0.8]}
    with pytest.raises(ValueError, match="exact inventory"):
        response.initial_radial_clearance_state(groups, {})
    with pytest.raises(ValueError, match="finite unit vector"):
        response.initial_radial_clearance_state(
            groups, {"bolt__radial_clearance": [1.0, 1.0]}
        )


def test_run_activates_supplied_radial_checkpoint_before_cycle_zero(
    tmp_path, monkeypatch
):
    springs = radial_springs()
    structure = SimpleNamespace(springs=springs, loads={})
    radial_name = springs[0]["name"]
    metadata = {
        "candidate": "radial-checkpoint-test",
        "angle_stations": [],
        "connection_ownership": {},
        "radial_clearance_ownership": {},
    }
    captured = {}

    class Captured(Exception):
        pass

    def capture(actual_structure, _metadata, active):
        captured["active"] = set(active)
        captured["loads"] = {
            node: force.copy() for node, force in actual_structure.loads.items()
        }
        raise Captured

    monkeypatch.setattr(response, "source_hashes", dict)
    monkeypatch.setattr(response, "LOADED_SOURCE_SHA256", {})
    monkeypatch.setattr(response.frame, "record_structure", capture)

    with pytest.raises(Captured):
        response.run(
            tmp_path / "run",
            module=object(),
            expected_candidate="radial-checkpoint-test",
            prepare_factory=lambda *_args, **_kwargs: (structure, metadata),
            initial_radial_clearance_states={radial_name: [0.6, 0.8]},
        )

    assert captured["active"] == {radial_name}
    assert captured["loads"][1] == pytest.approx([0.0, -345.0, -460.0])
    assert captured["loads"][2] == pytest.approx([0.0, 345.0, 460.0])


@pytest.mark.parametrize(
    "rows",
    [radial_springs()[:1], radial_springs(stiffness=1000.0)],
)
def test_inventory_rejects_incomplete_or_unequal_groups(rows):
    if len(rows) == 2:
        rows[1]["stiffness_n_per_mm"] = 900.0
    with pytest.raises(ValueError, match="two equal lateral springs"):
        response.radial_clearance_inventory(rows)
