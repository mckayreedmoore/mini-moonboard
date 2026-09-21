"""Same-case checkpoints initialize normal and axial active sets independently."""

from types import SimpleNamespace

import pytest

from fea import current_response_run as response


def spring(name, *, bearing=True, axial=False, dof=1):
    return {
        "name": name,
        "bearing_closed_assumption": bearing,
        "tension_only_assumption": axial,
        "dof": dof,
    }


@pytest.fixture
def checkpoint_model():
    structure = SimpleNamespace(
        springs=[
            spring("floor_left_0"),
            spring("floor_left_friction"),
            spring("floor_right_0"),
            spring("floor_right_friction"),
            spring("bolt_1", axial=True),
            spring("bolt_2", axial=True),
            spring("always_on", bearing=False),
        ]
    )
    ownership = {
        "floor_left_0": {"first": "left", "second": "floor"},
        "floor_left_friction": {"first": "left", "second": "floor"},
        "floor_right_0": {"first": "right", "second": "floor"},
        "floor_right_friction": {"first": "right", "second": "floor"},
        "bolt_1": {"first": "first", "second": "second"},
        "bolt_2": {"first": "first", "second": "second"},
    }
    metadata = {
        "candidate": "checkpoint-test",
        "angle_stations": [],
        "connection_ownership": ownership,
    }
    return structure, metadata


def test_omitted_checkpoint_preserves_all_closed_springs(checkpoint_model):
    structure, metadata = checkpoint_model

    active, axial = response.initial_active_set(structure, metadata)

    assert active == {
        "floor_left_0",
        "floor_left_friction",
        "floor_right_0",
        "floor_right_friction",
        "bolt_1",
        "bolt_2",
    }
    assert axial == {"bolt_1", "bolt_2"}


def test_checkpoint_regenerates_friction_and_allows_empty_axial_set(checkpoint_model):
    structure, metadata = checkpoint_model

    active, _ = response.initial_active_set(
        structure,
        metadata,
        initial_contact_names=["floor_left_0"],
        initial_axial_tension_names=[],
    )

    assert active == {"floor_left_0", "floor_left_friction"}


def test_contact_only_checkpoint_preserves_all_active_axials(checkpoint_model):
    structure, metadata = checkpoint_model

    active, _ = response.initial_active_set(
        structure, metadata, initial_contact_names=["floor_left_0"]
    )

    assert active == {
        "floor_left_0",
        "floor_left_friction",
        "bolt_1",
        "bolt_2",
    }


@pytest.mark.parametrize("invalid", ["floor_left_friction", "bolt_1", "missing"])
def test_checkpoint_rejects_non_normal_contact_names(checkpoint_model, invalid):
    structure, metadata = checkpoint_model

    with pytest.raises(ValueError, match="actual normal contacts"):
        response.initial_active_set(
            structure, metadata, initial_contact_names=[invalid]
        )


@pytest.mark.parametrize("invalid", ["floor_left_0", "floor_left_friction", "missing"])
def test_checkpoint_rejects_non_axial_names(checkpoint_model, invalid):
    structure, metadata = checkpoint_model

    with pytest.raises(ValueError, match="tension-only axial springs"):
        response.initial_active_set(
            structure, metadata, initial_axial_tension_names=[invalid]
        )


def test_run_passes_exact_checkpoint_active_set_to_cycle_zero(
    tmp_path, monkeypatch, checkpoint_model
):
    structure, metadata = checkpoint_model
    captured = {}

    class CycleZeroCaptured(Exception):
        pass

    def prepare(*args, **kwargs):
        return structure, metadata

    def capture_record(actual_structure, actual_metadata, active):
        captured["structure"] = actual_structure
        captured["metadata"] = actual_metadata
        captured["active"] = set(active)
        raise CycleZeroCaptured

    monkeypatch.setattr(response, "source_hashes", dict)
    monkeypatch.setattr(response, "LOADED_SOURCE_SHA256", {})
    monkeypatch.setattr(response.frame, "record_structure", capture_record)

    with pytest.raises(CycleZeroCaptured):
        response.run(
            tmp_path / "run",
            module=object(),
            expected_candidate="checkpoint-test",
            prepare_factory=prepare,
            initial_contact_names=["floor_left_0"],
            initial_axial_tension_names=["bolt_2"],
        )

    assert captured == {
        "structure": structure,
        "metadata": metadata,
        "active": {"floor_left_0", "floor_left_friction", "bolt_2"},
    }


def test_run_records_both_supplied_initial_inventories(
    tmp_path, monkeypatch, checkpoint_model
):
    structure, metadata = checkpoint_model

    def prepare(*args, **kwargs):
        return structure, metadata

    monkeypatch.setattr(response, "source_hashes", dict)
    monkeypatch.setattr(response, "LOADED_SOURCE_SHA256", {})

    report = response.run(
        tmp_path / "run",
        max_cycles=0,
        module=object(),
        expected_candidate="checkpoint-test",
        prepare_factory=prepare,
        initial_contact_names=["floor_right_0", "floor_left_0"],
        initial_axial_tension_names=[],
    )

    assert report["initial_contact_names"] == ["floor_left_0", "floor_right_0"]
    assert report["initial_axial_tension_names"] == []
