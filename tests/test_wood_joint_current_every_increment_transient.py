"""Verify the force-driven current-pilot every-increment derivative."""

from __future__ import annotations

import hashlib
import json

import pytest

from fea import wood_joint_current_timed_transient as timed
from fea.wood_joint_current_every_increment_transient import (
    DESTINATION_NAME,
    EXPECTED_CLOAD_ROWS,
    EXPECTED_ENDPOINT_FORCE_N,
    EXPECTED_OUTPUT_CARDS,
    EXPECTED_SOURCE_ARTIFACTS,
    INITIAL_INCREMENT_SECONDS,
    MINIMUM_INCREMENT_SECONDS,
    SOURCE,
    SOURCE_FREEZE_SHA256,
    STEP_INCREMENT_LIMIT,
    prepare,
)


def _keyword(line: str) -> bool:
    return line.lstrip().startswith("*") and not line.lstrip().startswith("**")


def _blocks(deck: str):
    lines = deck.splitlines()
    starts = [index for index, line in enumerate(lines) if _keyword(line)]
    for offset, start in enumerate(starts):
        end = starts[offset + 1] if offset + 1 < len(starts) else len(lines)
        yield lines, start, end, lines[start]


def _card(deck: str, prefix: str):
    found = [
        (lines, start, end, header)
        for lines, start, end, header in _blocks(deck)
        if header.upper().startswith(prefix.upper())
    ]
    assert len(found) == 1
    return found[0]


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


@pytest.mark.skipif(
    not (SOURCE / "input-freeze.json").is_file(),
    reason="the archived source solver bundle is intentionally not stored in the repository",
)
def test_every_increment_derivative_preserves_force_model_and_only_changes_time_controls(
    tmp_path,
):
    destination = tmp_path / DESTINATION_NAME
    source_freeze = json.loads((SOURCE / "input-freeze.json").read_text())
    source_deck = (SOURCE / "pilot.inp").read_text()
    report = prepare(destination)
    deck = (destination / "pilot.inp").read_text()

    assert report["schema"] == source_freeze["schema"]
    assert report["status"] == "FROZEN_NOT_EXECUTED"
    assert report["source_input_freeze_sha256"] == SOURCE_FREEZE_SHA256
    assert (
        report["derivative_parent_artifact_sha256"] == source_freeze["artifacts_sha256"]
    )
    assert len(source_freeze["artifacts_sha256"]) == EXPECTED_SOURCE_ARTIFACTS
    assert (destination / "source-input-freeze.json").read_bytes() == (
        SOURCE / "input-freeze.json"
    ).read_bytes()
    assert (destination / "source-pilot.inp").read_text() == source_deck

    normalized = timed.normalize_timed_deck(source_deck)
    normalized_sha = _sha(normalized.encode())
    prior_timepoint_freeze = json.loads(
        (SOURCE / "timing-parent-input-freeze.json").read_text()
    )
    assert normalized_sha == prior_timepoint_freeze["artifacts_sha256"]["pilot.inp"]
    assert report["inverse_normalized_pilot_sha256"] == normalized_sha
    normalized_lines = normalized.splitlines()
    output_lines = deck.splitlines()
    differences = [
        (index + 1, before, after)
        for index, (before, after) in enumerate(
            zip(normalized_lines, output_lines, strict=True)
        )
        if before != after
    ]
    assert len(differences) == 2
    assert differences[0][1].startswith("*STEP,NLGEOM,INC=")
    assert differences[0][2] == f"*STEP,NLGEOM,INC={STEP_INCREMENT_LIMIT}"
    assert differences[1][1] == "2.5000000000000e-03,2.5000000000000e-02,1e-6,2.5e-3"
    assert differences[1][2] == "0.001,0.025,1e-06,0.001"
    assert report["time_control_delta"]["changed_line_count"] == 2
    assert report["initial_increment_seconds"] == INITIAL_INCREMENT_SECONDS
    assert report["maximum_increment_seconds"] == INITIAL_INCREMENT_SECONDS
    assert report["minimum_increment_seconds"] == MINIMUM_INCREMENT_SECONDS
    assert report["end_seconds"] == 0.025
    assert report["direct_fixed_increment"] is False
    assert report["mechanical_acceptance"] is False
    assert report["native_solve_run"] is False

    assert "*DYNAMIC,ALPHA=0\n0.001,0.025,1e-06,0.001" in deck
    assert f"*STEP,NLGEOM,INC={STEP_INCREMENT_LIMIT}" in deck
    assert "DIRECT" not in deck.upper()
    assert "EXPLICIT" not in deck.upper()
    assert "*TIME POINTS" not in deck.upper()
    assert "TIME POINTS=" not in deck.upper()

    source_cload = _card(source_deck, "*CLOAD")
    emitted_cload = _card(deck, "*CLOAD")
    assert source_cload[3] == emitted_cload[3]
    assert (
        source_cload[0][source_cload[1] + 1 : source_cload[2]]
        == emitted_cload[0][emitted_cload[1] + 1 : emitted_cload[2]]
    )
    assert (
        len(
            [
                line
                for line in emitted_cload[0][emitted_cload[1] + 1 : emitted_cload[2]]
                if line.strip()
            ]
        )
        == EXPECTED_CLOAD_ROWS
    )
    source_amplitude = _card(source_deck, "*AMPLITUDE,NAME=RAMP_N")
    emitted_amplitude = _card(deck, "*AMPLITUDE,NAME=RAMP_N")
    assert (
        source_amplitude[0][source_amplitude[1] : source_amplitude[2]]
        == emitted_amplitude[0][emitted_amplitude[1] : emitted_amplitude[2]]
    )
    assert report["cload_reference_scale"] == 100
    assert report["final_amplitude_n"] == EXPECTED_ENDPOINT_FORCE_N
    assert report["force_endpoint_n_per_side"] == EXPECTED_ENDPOINT_FORCE_N
    assert report["force_reference_scale_n"] == 100

    output_cards = [
        header
        for _lines, _start, _end, header in _blocks(deck)
        if header.upper().startswith(
            (
                "*NODE FILE",
                "*NODE PRINT",
                "*EL PRINT",
                "*CONTACT FILE",
                "*CONTACT PRINT",
            )
        )
    ]
    assert len(output_cards) == EXPECTED_OUTPUT_CARDS
    assert report["every_increment_output_cards"] == EXPECTED_OUTPUT_CARDS
    assert all("FREQUENCY=1" in header.upper() for header in output_cards)
    assert all("TIME POINTS=" not in header.upper() for header in output_cards)
    assert "Every accepted increment" in report["output_scope_limit"]
    assert "not guaranteed" in report["ramp_knot_alignment_after_adaptive_cutbacks"]

    for key in (
        "monitor_nodes",
        "rotation_nodes",
        "serialized_unit_load_nodes",
        "sampled_travel_stop_mm",
        "sampled_controller_rotation_stop_rad",
        "sampled_loaded_node_displacement_stop_mm",
        "cload_reference_scale",
        "final_amplitude_n",
        "ramp_interpolation",
    ):
        assert report[key] == source_freeze[key]
    assert "time_points_name" not in report
    assert "time_points_step_seconds" not in report
    assert "time_point_review_sha256" not in report
    assert "TIME POINTS" not in report["output_schedule"]

    for name, expected_hash in source_freeze["artifacts_sha256"].items():
        output_name = "source-pilot.inp" if name == "pilot.inp" else name
        assert _sha((destination / output_name).read_bytes()) == expected_hash
        if name != "pilot.inp":
            assert (destination / name).read_bytes() == (SOURCE / name).read_bytes()
    for name, digest in report["artifacts_sha256"].items():
        assert _sha((destination / name).read_bytes()) == digest
    assert (
        _sha((destination / "every-increment-producer.py.snapshot").read_bytes())
        == report["source_sha256"]["every-increment-producer.py.snapshot"]
    )
    assert (
        _sha((destination / "every-increment-timed-helper.py.snapshot").read_bytes())
        == report["source_sha256"]["every-increment-timed-helper.py.snapshot"]
    )
    assert SOURCE_FREEZE_SHA256 == _sha(
        (destination / "source-input-freeze.json").read_bytes()
    )


def test_destination_must_be_fresh_and_source_freeze_is_pinned(tmp_path):
    existing = tmp_path / "existing"
    existing.mkdir()
    with pytest.raises(FileExistsError, match="destination must be fresh"):
        prepare(existing)

    with pytest.raises(ValueError, match="unexpected current K1e4 source input freeze"):
        prepare(tmp_path / "bad-source", source_dir=tmp_path)
    assert not (tmp_path / "bad-source").exists()
