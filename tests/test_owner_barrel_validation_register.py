"""BN-0 register stays source-bound, complete, unsolved, and unreleased."""

import copy
import json
import math
from pathlib import Path

import pytest

from scripts import owner_barrel_validation_register as register_source

ROOT = Path(__file__).resolve().parents[1]
REGISTER = ROOT / "docs/barrel-nut-stations.json"


@pytest.fixture(scope="module")
def register():
    return json.loads(REGISTER.read_text())


def test_checked_register_has_complete_station_inventory(register):
    register_source.validate_register(register)
    stations = register["stations"]
    bolts = {
        name
        for station in stations.values()
        for name in station["bolts"]
    }
    barrels = {
        name
        for station in stations.values()
        for name in station["barrels"]
    }
    drilling = {
        name
        for station in stations.values()
        for name in station["drilling_path_names"]
    }
    access = {
        name
        for station in stations.values()
        for name in station["access_path_names"]
    }
    assert len(stations) == 24
    assert len(bolts) == len(barrels) == 46
    assert register["counts"]["barrel_face_contact_cells"] == 132
    assert len(drilling) == 98
    assert len(access) == 92
    assert all(station["contact"]["bolt_face_crossings"] for station in stations.values())
    for station in stations.values():
        assert set(station["member_grain_axes"]) == set(station["timber_members"])
        for member in station["member_grain_axes"].values():
            assert math.sqrt(sum(value * value for value in member["axis_xyz"])) == pytest.approx(1.0)


def test_register_fails_closed_on_counts_and_approved_revisions(register):
    changed = copy.deepcopy(register)
    changed["counts"]["barrel_pairs"] = 45
    with pytest.raises(ValueError, match="inventory changed"):
        register_source.validate_register(changed)

    changed = copy.deepcopy(register)
    station = next(iter(changed["stations"].values()))
    station["bolts"].pop(next(iter(station["bolts"])))
    with pytest.raises(ValueError, match="inventory changed"):
        register_source.validate_register(changed)

    changed = copy.deepcopy(register)
    changed["approved_revision_regression"]["first_row_trial_n_mm"] = 60.0
    with pytest.raises(ValueError, match="N=42 mm / \\+2 mm"):
        register_source.validate_register(changed)

    changed = copy.deepcopy(register)
    changed["approved_revision_regression"]["extension_mm"] = 0.0
    with pytest.raises(ValueError, match="N=42 mm / \\+2 mm"):
        register_source.validate_register(changed)

    changed = copy.deepcopy(register)
    changed["approved_revision_regression"]["whole_cut_missing_paths"] = [
        "unexpected/machine_bore"
    ]
    with pytest.raises(ValueError, match="N=42 mm / \\+2 mm"):
        register_source.validate_register(changed)

    changed = copy.deepcopy(register)
    changed["approved_revision_regression"]["drilling_released"] = True
    with pytest.raises(ValueError, match="N=42 mm / \\+2 mm"):
        register_source.validate_register(changed)

    changed = copy.deepcopy(register)
    changed["approved_revision_regression"]["changed_cut_intersections"] = {}
    with pytest.raises(ValueError, match="N=42 mm / \\+2 mm"):
        register_source.validate_register(changed)


def test_register_sources_and_render_are_reproducible(register):
    # This is the HEAD observed when the generated artifact was written.  A
    # committed generated file necessarily predates the commit that contains
    # it, so current-HEAD equality would make a clean checkout impossible.
    assert len(register["repository_commit"]) == 40
    assert set(register["repository_commit"]) <= set("0123456789abcdef")
    assert register["source_sha256"] == register_source._source_hashes()
    assert REGISTER.read_text() == register_source.render(register)


def test_six_frozen_cases_include_full_signed_load_inputs(register):
    assert register["load_case_order"] == list(register_source.EXPECTED_CASES)
    expected = {
        name: (hold, list(horizontal))
        for name, (hold, horizontal) in register_source.CASES.items()
    }
    for name, row in register["load_cases"].items():
        hold, horizontal = expected[name]
        assert row["hold"] == hold
        assert row["horizontal_force_xy_n"] == horizontal
        assert row["applied_force_xyz_n"][:2] == horizontal
        assert row["applied_force_xyz_n"][2] == pytest.approx(-2224.11080763025)
        assert row["requested_climber_weight_lbf"] == 250.0
        assert row["dynamic_assumption"]["multiplier"] == 2.0
        assert row["equipment_mass_kg"] == 25.0
        assert row["stand_off_from_panel_front_mm"] == 100.0
        assert row["panel_patch_size_mm"] == 20.0
        assert len(row["application_point_xyz_mm"]) == 3
        assert len(row["moment_at_panel_midplane_nmm"]) == 3
        assert row["preparation"]["barrel_pairs"] == 46
        assert row["preparation"]["retained_bolts"] == 12
        assert row["preparation"]["panel_screws"] == 66
        assert row["preparation"]["face_contact_cells"] == 132
        assert row["preparation"]["retained_face_contact_cells"] == 72
        assert row["preparation"]["conditional_contact_n_per_mm3"] == 100.0
        assert "conditional_contact_n_per_mm2" not in row["preparation"]
        assert row["native_solve"] is False
        assert row["demands_qualified"] is False


def test_release_stays_false(register):
    assert register["release"] is False
    assert register["release_flags"]
    assert not any(register["release_flags"].values())
    assert register["contact_summary"]["native_solve"] is False
    assert register["contact_summary"]["structural_released"] is False
    assert register["contact_summary"]["drilling_released"] is False
