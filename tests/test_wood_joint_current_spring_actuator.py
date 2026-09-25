"""Audit the frozen current-joint finite-spring actuator input adapter."""

from __future__ import annotations

import hashlib
import inspect
import json
import re
import shutil
from pathlib import Path

import pytest

from fea.wood_joint_current_spring_actuator import (
    DRIVER_SET,
    DRIVER_SPRING_SET,
    PROXY_NODE,
    TARGET_NODE,
    build_current_spring_actuator,
    write_input_only_bundle,
)

BASE = (
    Path(__file__).resolve().parents[1]
    / "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24"
    / "ordinary-transient-seating-100n-aligned-k1e4-attempt01"
)


def _keyword(line: str) -> bool:
    return line.startswith("*") and not line.startswith("**")


def _blocks(text: str):
    lines = text.splitlines()
    starts = [index for index, line in enumerate(lines) if _keyword(line)]
    for offset, start in enumerate(starts):
        end = starts[offset + 1] if offset + 1 < len(starts) else len(lines)
        yield lines, start, end, lines[start]


def _options(header: str) -> dict[str, str | None]:
    result = {}
    for field in header.split(",")[1:]:
        field = field.strip()
        if "=" in field:
            key, value = field.split("=", 1)
            result[key.strip().upper()] = value.strip().strip("\"'")
        elif field:
            result[field.upper()] = None
    return result


def _read_nset(text: str, name: str) -> set[int]:
    for lines, start, end, header in _blocks(text):
        if not _keyword(header) or header[1:].split(",", 1)[0].upper() != "NSET":
            continue
        if _options(header).get("NSET", "").upper() != name.upper():
            continue
        members = set()
        for line in lines[start + 1 : end]:
            for token in line.split(","):
                token = token.strip()
                if token and re.fullmatch(r"\d+", token):
                    members.add(int(token))
        return members
    raise AssertionError(f"missing NSET {name}")


def _equation(text: str):
    for lines, start, end, header in _blocks(text):
        if header.upper() != "*EQUATION":
            continue
        expected_terms = int(lines[start + 1].strip())
        values = [
            token.strip()
            for line in lines[start + 2 : end]
            for token in line.split(",")
            if token.strip()
        ]
        assert len(values) == 3 * expected_terms
        terms = [
            (int(values[i]), int(values[i + 1]), float(values[i + 2]), values[i + 2])
            for i in range(0, len(values), 3)
        ]
        return expected_terms, terms
    raise AssertionError("missing MPC equation")


def _build(**overrides):
    values = {
        "actuator_stiffness_n_per_mm": 200.0,
        "q_target_max_mm": 1.15,
        "ramp_seconds": 0.1,
        "end_seconds": 0.1,
        "time_increment_seconds": 0.0005,
        "output_interval_seconds": 0.0005,
    }
    values.update(overrides)
    return build_current_spring_actuator(BASE, **values)


def test_current_frozen_weights_drive_proxy_and_target_without_double_drive(tmp_path):
    signature = inspect.signature(build_current_spring_actuator)
    assert all(
        parameter.default is inspect.Parameter.empty
        for parameter in signature.parameters.values()
    )

    prepared = _build()
    output = write_input_only_bundle(prepared, tmp_path / "input-only")
    pilot = (output / "pilot.inp").read_text()
    original_freeze = json.loads((BASE / "input-freeze.json").read_text())
    original_actuator = json.loads((BASE / "actuator.json").read_text())
    driver = json.loads((output / "actuator-driving.json").read_text())
    freeze = json.loads((output / "input-freeze.json").read_text())

    assert freeze["schema"] == "wood_joint_current_spring_actuator_input/v1"
    assert freeze["status"] == "INPUT_ONLY_NOT_SOLVED"
    assert freeze["solver_image"] == original_freeze["solver_image"]
    assert freeze["monitor_nodes"] == original_freeze["monitor_nodes"]
    assert (
        freeze["serialized_unit_load_nodes"]
        == original_freeze["serialized_unit_load_nodes"]
    )
    assert freeze["rotation_nodes"] == original_freeze["rotation_nodes"]
    assert freeze["mechanical_acceptance"] is False
    assert freeze["native_solve_run"] is False
    assert (
        not {"final_amplitude_n", "cload_reference_scale", "source_sha256"}
        & freeze.keys()
    )

    assert "*CLOAD" not in pilot.upper()
    assert "RAMP_N" not in pilot.upper()
    assert "RAMP_KNOTS" not in pilot.upper()
    assert "TIME POINTS=" not in pilot.upper()
    assert "TIME=STEP TIME" not in pilot.upper()
    assert "EXPLICIT" not in pilot.upper()
    assert "*DYNAMIC,ALPHA=0\n0.0005,0.1,1e-06,0.0005" in pilot
    assert "*STEP,NLGEOM,INC=10000" in pilot
    assert f"*SPRING,ELSET={DRIVER_SPRING_SET}\n1,1\n200.0" in pilot

    term_count, mpc_terms = _equation(pilot)
    assert term_count == 663
    assert mpc_terms[0][:3] == (PROXY_NODE, 1, 1.0)
    assert all(len(row[3]) <= 20 for row in mpc_terms)
    assert TARGET_NODE not in {node for node, _dof, _coefficient, _token in mpc_terms}
    expected = {
        (int(node), int(dof)): -float(weight)
        for node, dof, weight in original_actuator["equation"][
            "physical_terms_before_normalization"
        ]
    }
    source_weights = {
        (int(node), int(dof)): float(weight)
        for node, dof, weight in original_actuator["equation"][
            "physical_terms_before_normalization"
        ]
    }
    actual = {
        (node, dof): coefficient for node, dof, coefficient, _token in mpc_terms[1:]
    }
    assert actual.keys() == expected.keys()
    assert max(abs(actual[key] - expected[key]) for key in expected) < 5.1e-17
    emitted_rounding_error = max(
        abs(source_weights[key] + actual[key]) for key in source_weights
    )
    reported_rounding_error = driver["source_unit_pattern"][
        "mpc_coefficient_max_rounding_error"
    ]
    assert reported_rounding_error == pytest.approx(
        emitted_rounding_error, rel=1e-12, abs=1e-30
    )
    assert 0.0 < reported_rounding_error < 5.1e-17
    assert driver["source_unit_pattern"]["terms_count"] == len(expected) == 662
    assert driver["source_unit_pattern"]["source_reference_only"] is True
    assert driver["driver_nodes"]["proxy_is_first_dependent_mpc_term"] is True
    assert driver["driver_nodes"]["target_is_outside_mpc"] is True

    boundaries = [
        (lines, start, end, header)
        for lines, start, end, header in _blocks(pilot)
        if header.upper().startswith("*BOUNDARY")
    ]
    assert len(boundaries) == 2
    unused = [
        line.strip()
        for line in boundaries[0][0][boundaries[0][1] + 1 : boundaries[0][2]]
    ]
    assert unused == [f"{PROXY_NODE},2,3,0", f"{TARGET_NODE},2,3,0"]
    assert boundaries[1][3].upper() == "*BOUNDARY,AMPLITUDE=Q_TARGET_HISTORY"
    assert boundaries[1][0][boundaries[1][1] + 1 : boundaries[1][2]] == [
        f"{TARGET_NODE},1,1,1.15"
    ]

    amplitude = next(
        (lines, start, end)
        for lines, start, end, header in _blocks(pilot)
        if header.upper() == "*AMPLITUDE,NAME=Q_TARGET_HISTORY"
    )
    samples = [
        tuple(map(float, line.split(",")))
        for line in amplitude[0][amplitude[1] + 1 : amplitude[2]]
    ]
    assert len(samples) == 201
    assert samples[0] == pytest.approx((0.0, 0.0))
    assert samples[100] == pytest.approx((0.05, 0.5))
    assert samples[-1] == pytest.approx((0.1, 1.0))
    assert driver["target_history"]["sample_function"].startswith("quintic smoothstep")
    assert driver["target_history"]["native_interpolation"] == (
        "piecewise linear between explicit amplitude samples"
    )

    source_pilot_sets = (BASE / "pilot-sets.inp").read_text()
    generated_pilot_sets = (output / "pilot-sets.inp").read_text()
    physical_nodes = _read_nset(source_pilot_sets, "PILOT_ALL_NODES")
    union_nodes = _read_nset(generated_pilot_sets, "PILOT_ALL_NODES")
    assert union_nodes == physical_nodes | {PROXY_NODE, TARGET_NODE}
    assert _read_nset(pilot + "\n" + generated_pilot_sets, DRIVER_SET) == {
        PROXY_NODE,
        TARGET_NODE,
    }
    assert (
        freeze["source_include_modifications"]["pilot-sets.inp"][
            "physical_membership_preserved"
        ]
        is True
    )

    node_files = [
        (header, lines[start + 1 : end])
        for lines, start, end, header in _blocks(pilot)
        if header.upper().startswith("*NODE FILE")
    ]
    assert len(node_files) == 1
    assert "NSET=PILOT_ALL_NODES" in node_files[0][0]
    assert "FREQUENCY=1" in node_files[0][0]
    assert node_files[0][1] == ["U,V,RF"]
    print_cards = {
        _options(header).get("NSET"): (header, data)
        for header, data in (
            (header, lines[start + 1 : end])
            for lines, start, end, header in _blocks(pilot)
            if header.upper().startswith("*NODE PRINT")
        )
    }
    assert print_cards["PILOT_MONITOR"][0].endswith("FREQUENCY=1")
    assert print_cards["PILOT_MONITOR"][1] == ["U"]
    assert print_cards[DRIVER_SET][0].endswith("FREQUENCY=1")
    assert print_cards[DRIVER_SET][1] == ["U,RF"]
    output_headers = [
        header.upper()
        for _lines, _start, _end, header in _blocks(pilot)
        if header.upper().startswith(("*NODE ", "*EL ", "*CONTACT "))
    ]
    assert output_headers
    assert all("FREQUENCY=1" in header for header in output_headers)
    assert all("TIME POINTS=" not in header for header in output_headers)

    for name in (
        "mesh.inp",
        "materials.inp",
        "nut-coupling.inp",
        "rigid-carriers.inp",
        "contact-fragment.inc",
        "output-sets.inp",
    ):
        assert (output / name).read_bytes() == (BASE / name).read_bytes()
    assert (
        json.loads((output / "source-actuator-reference.json").read_text())
        == original_actuator
    )
    assert (
        driver["source_lineage"]["source_actuator_reference_sha256"]
        == hashlib.sha256((BASE / "actuator.json").read_bytes()).hexdigest()
    )
    assert (
        driver["source_lineage"]["producer_snapshot_sha256"]
        == hashlib.sha256(
            (output / "spring-actuator-producer.py.snapshot").read_bytes()
        ).hexdigest()
    )
    for name, digest in freeze["artifacts_sha256"].items():
        assert hashlib.sha256((output / name).read_bytes()).hexdigest() == digest


def test_rejects_incompatible_output_interval_before_building(tmp_path):
    with pytest.raises(ValueError, match="output interval must equal dt"):
        build_current_spring_actuator(
            BASE,
            actuator_stiffness_n_per_mm=200.0,
            q_target_max_mm=1.15,
            ramp_seconds=0.1,
            end_seconds=0.1,
            time_increment_seconds=0.0005,
            output_interval_seconds=0.001,
        )


def test_rejects_tampered_frozen_source_component(tmp_path):
    source_freeze = json.loads((BASE / "input-freeze.json").read_text())
    damaged = tmp_path / "damaged-source"
    damaged.mkdir()
    for name in source_freeze["artifacts_sha256"]:
        shutil.copy2(BASE / name, damaged / name)
    shutil.copy2(BASE / "input-freeze.json", damaged / "input-freeze.json")
    pilot_path = damaged / "pilot.inp"
    pilot = pilot_path.read_text()
    cload = re.search(r"(?im)^\*CLOAD[^\n]*\n([^\n]+)", pilot)
    assert cload is not None
    first = cload.group(1)
    fields = first.split(",")
    fields[2] = str(float(fields[2]) + 0.01)
    pilot_path.write_text(
        pilot[: cload.start(1)] + ",".join(fields) + pilot[cload.end(1) :]
    )

    with pytest.raises(ValueError, match="frozen source artifact changed.*pilot.inp"):
        build_current_spring_actuator(
            damaged,
            actuator_stiffness_n_per_mm=200.0,
            q_target_max_mm=1.15,
            ramp_seconds=0.1,
            end_seconds=0.1,
            time_increment_seconds=0.0005,
            output_interval_seconds=0.0005,
        )
