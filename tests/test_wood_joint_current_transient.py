"""Tests for solver serialization and the run-stopping observation boundary."""

import tracemalloc

import pytest

from fea.wood_joint_current_transient import load_pattern, numeric
from fea.wood_joint_current_transient_launch import IncrementalMonitor, observations


def test_serialized_load_work_and_wrench():
    actuator = {
        "owner_unit_wrench_distributions": [
            {
                "nodal_forces": [
                    {
                        "node_id": 1,
                        "force_xyz_n": [1 / 3, 0, 0],
                        "point_xyz_mm": [0, 0, 0],
                    }
                ]
            },
            {
                "nodal_forces": [
                    {
                        "node_id": 2,
                        "force_xyz_n": [-1 / 3, 0, 0],
                        "point_xyz_mm": [5, 0, 0],
                    }
                ]
            },
        ]
    }
    cards, nodes, force, moment = load_pattern(actuator)
    terms = [line.split(",") for line in cards.splitlines()[1:]]
    assert all(len(t[2]) <= 20 for t in terms)
    assert sum(
        float(t[2]) * {1: 2.5, 2: -0.5}[int(t[0])] for t in terms
    ) == pytest.approx(1)
    assert force == [0, 0, 0] and moment == [0, 0, 0]
    actuator["owner_unit_wrench_distributions"][1]["nodal_forces"][0][
        "point_xyz_mm"
    ] = [0, 1, 0]
    with pytest.raises(ValueError, match="wrench"):
        load_pattern(actuator)
    assert len(nodes) == 2


@pytest.mark.parametrize("value", [float("nan"), float("inf"), -1e-101])
def test_unrepresentable_fields_rejected(value):
    with pytest.raises(ValueError):
        numeric(value)


@pytest.fixture
def freeze():
    return {
        "monitor_nodes": [1, 2, 3],
        "rotation_nodes": [3],
        "serialized_unit_load_nodes": {
            "1": {"force_xyz_n": [1, 0, 0]},
            "2": {"force_xyz_n": [-1, 0, 0]},
        },
        "sampled_travel_stop_mm": 3,
        "sampled_controller_rotation_stop_rad": 0.01,
        "sampled_loaded_node_displacement_stop_mm": 5,
    }


def test_partial_dat_tail_and_motion_limit(freeze):
    header = " displacements (vx,vy,vz) for set PILOT_MONITOR and time 0.1E-02\n\n"
    block = header + "1 2 0 0\n2 -2 0 0\n3 0 0 0\n"
    assert observations(header + "1 2 0 0\n", freeze) == []
    assert observations(header + "1 2 0 0\n2 -2 0 0\n3 0 0 1.2E", freeze) == []
    result = observations(block + "\n" + header + "1 0 0 0\n", freeze)
    assert len(result) == 1
    assert result[0]["q_mm"] == 4
    assert result[0]["stop_reasons"] == ["relative_travel"]


def test_duplicate_or_nonfinite_native_motion_rejected(freeze):
    header = "displacements (vx,vy,vz) for set PILOT_MONITOR and time 1\n"
    for rows in ("1 0 0 0\n1 0 0 0\n", "1 NaN 0 0\n"):
        with pytest.raises(ValueError):
            observations(header + rows, freeze)


def test_monitor_does_not_expand_unrelated_contact_history(freeze):
    header = "displacements (vx,vy,vz) for set PILOT_MONITOR and time 1\n"
    block = header + "1 0.2 0 0\n2 -0.2 0 0\n3 0 0 0\n"
    text = block + ("unrelated contact output\n" * 100_000)
    text += block.replace("time 1", "time 2")
    tracemalloc.start()
    try:
        result = observations(text, freeze)
        _, peak = tracemalloc.get_traced_memory()
    finally:
        tracemalloc.stop()
    assert [row["time_seconds"] for row in result] == [1, 2]
    assert all(row["q_mm"] == pytest.approx(0.4) for row in result)
    # Parsing a few monitor rows must not allocate a list of all contact rows.
    assert peak < len(text) // 2


@pytest.mark.parametrize("chunk_size", [1, 7, 53, 1000])
def test_incremental_monitor_matches_complete_parser_across_partial_writes(
    freeze, tmp_path, chunk_size
):
    header = " displacements (vx,vy,vz) for set PILOT_MONITOR and time 1\n\n"
    block = header + "1 2 0 0\n2 -2 0 0\n3 0 0 1.2E-03\n"
    text = (
        "unrelated output\n"
        + block
        + "contact output\n"
        + block.replace("time 1", "time 2")
    )
    text += header + "1 0 0 0\n2 0 0 0\n3 0 0 1.2E"
    path = tmp_path / "pilot.dat"
    monitor = IncrementalMonitor(freeze)
    assert monitor.poll(path) == []
    for start in range(0, len(text), chunk_size):
        with path.open("ab") as stream:
            stream.write(text[start : start + chunk_size].encode())
        assert monitor.poll(path) == observations(text[: start + chunk_size], freeze)
    assert monitor.offset == len(text)
    assert monitor.poll(path) == observations(text, freeze)
    with path.open("ab") as stream:
        stream.write(b"-02\n")
    assert monitor.poll(path) == observations(text + "-02\n", freeze)


@pytest.mark.parametrize("mutation", ["truncate", "replace", "remove"])
def test_incremental_monitor_rejects_lost_output(freeze, tmp_path, mutation):
    path = tmp_path / "pilot.dat"
    path.write_text("unrelated output\n")
    monitor = IncrementalMonitor(freeze)
    monitor.poll(path)
    if mutation == "truncate":
        path.write_text("")
    elif mutation == "replace":
        replacement = tmp_path / "replacement.dat"
        replacement.write_text("replacement native output\n")
        replacement.replace(path)
    else:
        path.unlink()
    with pytest.raises(ValueError):
        monitor.poll(path)


@pytest.mark.parametrize("rows", ["1 0 0 0\n1 0 0 0\n", "1 NaN 0 0\n"])
def test_incremental_monitor_rejects_invalid_motion(freeze, tmp_path, rows):
    path = tmp_path / "pilot.dat"
    path.write_text(
        "displacements (vx,vy,vz) for set PILOT_MONITOR and time 1\n" + rows
    )
    with pytest.raises(ValueError):
        IncrementalMonitor(freeze).poll(path)


@pytest.mark.parametrize("sample_time", ["NaN", "Inf", "-Inf"])
def test_nonfinite_time_rejected_by_both_monitors(freeze, tmp_path, sample_time):
    text = (
        f"displacements (vx,vy,vz) for set PILOT_MONITOR and time {sample_time}\n"
        "1 0 0 0\n2 0 0 0\n3 0 0 0\n"
    )
    with pytest.raises(ValueError, match="nonfinite native sample time"):
        observations(text, freeze)
    path = tmp_path / "pilot.dat"
    path.write_text(text)
    with pytest.raises(ValueError, match="nonfinite native sample time"):
        IncrementalMonitor(freeze).poll(path)
