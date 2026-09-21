"""Nominal shared-header topology remains separate from build approval."""

import hashlib
from pathlib import Path

import pytest

from scripts.bolted_center_joint_model import shared_center_joint
from scripts.bolted_kerf_diagnostic_probe import (
    DiagnosticCenterBolted,
    prepare_center_case,
)

SPRING = {"axial_n_per_mm": 10000.0, "lateral_n_per_mm": 10000.0}


def test_shared_model_matches_pinned_baseline():
    source = Path("fea/current_response_model.py").read_bytes()
    assert hashlib.sha256(source).hexdigest() == (
        "40922fddfcda85fd906c068b79f2bb3bfb2ab6c8341b91a67c8da5b30147e50d"
    )


def test_shared_joint_has_distributed_lateral_bearing_and_flange_contacts():
    structure, report = prepare_center_case(
        "a1-rear",
        vertical_spring=SPRING,
        steel_bolt_spring=SPRING,
        wood_bearing_lateral_n_per_mm=10000.,
        flange_contact_n_per_mm=10000.,
    )
    owner = report["connection_ownership"]
    assert report["acceptance"] is False
    assert report["bolted_joint_demands_qualified"] is False
    assert report["legacy_center_hardware_mass_surrogate"] is True
    assert len(report["panel_bounds"]) == 6
    assert len(report["center_joint"]["shared_header_bolts"]) == 2
    module = DiagnosticCenterBolted()
    assert len(module.panel_connections()) == 66
    assert all(
        connection.name in owner
        for connection in module.connections()
        if connection.kind == "bolt"
    )
    assert not any(
        name.startswith(
            ("clip_split_base_center_left_", "clip_split_header_center_left_")
        )
        for name in owner
    )
    for index in range(2):
        stem = f"diagnostic_shared_header_left_{index}"
        branches = [name for name in owner if name.startswith(stem + "_")]
        assert len(branches) == 4
        assert {owner[name]["first"] for name in branches} == {
            "diagnostic_ab205_upper_left",
            "diagnostic_ab205_lower_left",
            "base_header",
        }
        for name in branches:
            springs = [row for row in structure.springs if row["name"] == name]
            if "header_bearing" in name:
                assert [row["dof"] for row in springs] == [1, 2]
            else:
                assert len(springs) == 3
    for angle in report["center_joint"]["angles"]:
        contacts = [name for name in owner if name.startswith(angle["name"] + "_flange_contact_")]
        assert len(contacts) == 4
        assert all(sum(row["name"] == name and row["bearing_closed_assumption"]
                       for row in structure.springs) == 1 for name in contacts)
    assert all(connection.name in owner for connection in module.panel_connections())


def test_joint_requires_explicit_finite_positive_slip_inputs():
    module = DiagnosticCenterBolted()
    for invalid in (0.0, -1.0, float("nan"), float("inf")):
        with pytest.raises(ValueError, match="finite positive"):
            shared_center_joint(
                module,
                vertical_spring=SPRING,
                steel_bolt_spring=SPRING,
                wood_bearing_lateral_n_per_mm=invalid,
                flange_contact_n_per_mm=10000.,
            )
