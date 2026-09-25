"""Focused tests for the frozen current-patch contact-card adapter."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

import pytest

from fea import wood_joint_current_contact_deck as contract


def test_current_patch_fragment_resolves_all_35_frozen_contact_pairs() -> None:
    fragment, manifest = contract.build_current_contact_deck_fragment(
        contract.CLASSIFICATION_PATH,
        contract.MESH_REPORT_PATH,
        contract.MESH_DECK_PATH,
        penalty_n_per_mm3=100_000.0,
    )

    assert manifest["schema"] == "wood_joint_current_contact_deck_fragment/v1"
    assert manifest["status"] == "UNSOLVED_CURRENT_PATCH_CONTACT_CARDS_ONLY"
    assert manifest["accepted"] is False
    assert manifest["response_ready"] is False
    assert manifest["native_solve_run"] is False
    assert manifest["scope"]["contact_pairs"] == 35
    assert manifest["scope"]["contact_surfaces"] == 70
    assert manifest["scope"]["wood_interfaces"] == 3
    assert manifest["scope"]["planar_hardware_seats"] == 16
    assert manifest["scope"]["wood_bore_to_shaft_pairs"] == 8
    assert manifest["scope"]["washer_bore_to_shaft_pairs"] == 8
    assert manifest["scope"]["intentional_nut_bore_omissions"] == 4
    assert len(manifest["intentional_nut_bore_omissions"]) == 4
    assert all(
        row["status"] == "INTENTIONAL_NO_NUT_BORE_CONTACT_PAIR"
        for row in manifest["intentional_nut_bore_omissions"]
    )
    assert manifest["contact_law"]["penalty_n_per_mm3"] == 100_000.0
    assert manifest["contact_law"]["tension_transfer"] is False
    assert manifest["contact_law"]["friction_behavior"].startswith("frictionless")
    assert manifest["pair_category_counts"] == {
        "head_washer_to_head": 4,
        "head_washer_to_first_receiver": 4,
        "nut_washer_to_last_receiver": 4,
        "nut_washer_to_nut": 4,
        "open_bolt_shank_to_wood_bore": 8,
        "open_bolt_shank_to_washer_bore": 8,
        "wood_wood_finite_interface": 3,
    }

    assert (
        fragment.count(
            "*CONTACT PAIR,INTERACTION=WJCP_CURRENT_NUMERICAL_CONTACT,TYPE=SURFACE TO SURFACE"
        )
        == 35
    )
    assert fragment.count("*SURFACE,NAME=") == 70
    assert "*SURFACE BEHAVIOR,PRESSURE-OVERCLOSURE=LINEAR\n100000" in fragment
    assert "\n*FRICTION\n" not in fragment
    assert "TENSION=0" not in fragment
    assert "sigma-infinity default is node-to-face only" in fragment
    assert "Four displayed nut solids have no bore wall" in fragment
    assert "NUT_BORE" not in fragment

    allowed = {
        "*SURFACE INTERACTION,NAME=WJCP_CURRENT_NUMERICAL_CONTACT",
        "*SURFACE BEHAVIOR,PRESSURE-OVERCLOSURE=LINEAR",
    }
    cards = [
        line.upper()
        for line in fragment.splitlines()
        if line.startswith("*") and not line.startswith("**")
    ]
    assert all(
        card in allowed
        or card.startswith(("*NSET,", "*SURFACE,NAME=", "*CONTACT PAIR,"))
        for card in cards
    )
    assert Counter(card.split(",", 1)[0] for card in cards)["*SURFACE"] == 70

    pair_rows = manifest["pairs"]
    assert len(pair_rows) == 35
    assert all(
        row["slave_face_count"] > 0 and row["master_face_count"] > 0
        for row in pair_rows
    )
    radial = [row for row in pair_rows if row["category"].startswith("open_")]
    assert all(row["radial_clearance_mm"] > 0 for row in radial)
    assert all(row["minimum_shaft_outward_radial_alignment"] >= 0.8 for row in radial)
    assert all(row["minimum_bore_inward_radial_alignment"] >= 0.8 for row in radial)


@pytest.mark.parametrize("penalty", [0, -1, float("inf"), float("nan"), True, None])
def test_contact_penalty_must_be_explicit_positive_and_finite(penalty: object) -> None:
    with pytest.raises((TypeError, ValueError), match="penalty_n_per_mm3"):
        contract._positive_penalty(penalty)


def test_classifier_digest_mismatch_fails_before_mesh_load(tmp_path: Path) -> None:
    source = json.loads(contract.CLASSIFICATION_PATH.read_text())
    source["scope"]["wood_members"] = 99
    altered = tmp_path / "classification.json"
    altered.write_text(json.dumps(source))

    with pytest.raises(ValueError, match="classification digest"):
        contract.build_current_contact_deck_fragment(
            altered,
            contract.MESH_REPORT_PATH,
            contract.MESH_DECK_PATH,
            penalty_n_per_mm3=100_000.0,
        )
