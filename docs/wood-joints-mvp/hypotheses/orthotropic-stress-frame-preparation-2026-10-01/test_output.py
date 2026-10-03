import importlib.util
import json
import math
from pathlib import Path

import pytest


def module(name):
    spec = importlib.util.spec_from_file_location(
        name, Path(__file__).with_name(name + ".py")
    )
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


prepare = module("prepare")
checker = module("check_output")
constitutive = module("test_constitutive_answer")


def build_fixture():
    deck, expected = prepare.prepare()
    node_lines = deck.split("*NODE\n")[1].split("*ELEMENT")[0].splitlines()
    coords = {
        int(row.split(",")[0]): tuple(map(float, row.split(",")[1:]))
        for row in node_lines
    }
    oracle = json.loads(prepare.ORACLE.read_text())
    strain = oracle["global_strain_tensor"]
    lines = ["displacements (vx,vy,vz) for set ALLNODES and time 1.0"]
    for node, xyz in coords.items():
        u = [math.fsum(strain[d][j] * xyz[j] for j in range(3)) for d in range(3)]
        lines.append(str(node) + " " + " ".join(f"{x:.6E}" for x in u))
    for name in ("SGLOBAL", "SLOCAL", "SDEFAULT"):
        tensor = oracle[
            "global_stress_tensor_MPa"
            if name == "SGLOBAL"
            else "local_stress_tensor_MPa"
        ]
        values = [
            tensor[0][0],
            tensor[1][1],
            tensor[2][2],
            tensor[0][1],
            tensor[0][2],
            tensor[1][2],
        ]
        suffix = "" if name == "SGLOBAL" else " WOODLRT"
        lines.append(
            f"stresses (elem, integ.pnt.,sxx,syy,szz,sxy,sxz,syz) for set {name} and time 1.0"
        )
        for element in range(1, 385):
            for point in range(1, 5):
                lines.append(
                    f"{element} {point} "
                    + " ".join(f"{x:.6E}" for x in values)
                    + suffix
                )
    lines += [
        "total internal energy for set ANNULUS and time 1.0",
        f"{expected['expected_energy_N_mm']:.6E}",
    ]
    return "\n".join(lines), expected, coords, strain


@pytest.fixture
def fixture():
    return build_fixture()


def test_prepare_frame_expectations_match_independent_reciprocal_answer():
    _, expected = prepare.prepare()
    local_stress, global_stress, _, _ = constitutive.independent_answers()
    for key, answer in (
        ("global_stress_tensor_MPa", global_stress),
        ("local_stress_tensor_MPa", local_stress),
    ):
        for actual_row, answer_row in zip(expected[key], answer, strict=True):
            assert actual_row == pytest.approx(answer_row, abs=1e-14, rel=1e-11)


def test_complete_synthetic_output_passes_without_capacity_claim(fixture):
    result = checker.check(*fixture)
    assert result["stress_rows"] == 4608 and result["displacement_rows"] == 800
    assert result["mechanical_acceptance"] is False


def test_swapped_producer_frame_labels_are_refused(monkeypatch):
    deck, expected = prepare.prepare()
    swapped = expected.copy()
    swapped["global_stress_tensor_MPa"], swapped["local_stress_tensor_MPa"] = (
        expected["local_stress_tensor_MPa"],
        expected["global_stress_tensor_MPa"],
    )
    monkeypatch.setattr(prepare, "prepare", lambda: (deck, swapped))
    dat, actual_expected, coords, strain = build_fixture()
    assert actual_expected is swapped
    with pytest.raises(ValueError, match="stress component differs"):
        checker.check(dat, actual_expected, coords, strain)


@pytest.mark.parametrize(
    "mutation",
    [
        "missing_ip",
        "duplicate_ip",
        "bad_frame",
        "bad_stress",
        "missing_u",
        "bad_time",
        "bad_energy",
        "nan",
    ],
)
def test_corrupted_or_incomplete_output_refused(fixture, mutation):
    dat, expected, coords, strain = fixture
    lines = dat.splitlines()
    if mutation == "missing_ip":
        del lines[-3]
    elif mutation == "duplicate_ip":
        lines[-3] = lines[-4]
    elif mutation == "bad_frame":
        lines[-3] = lines[-3].replace("WOODLRT", "WRONGFRAME")
    elif mutation == "bad_stress":
        fields = lines[-3].split()
        fields[2] = "1.0"
        lines[-3] = " ".join(fields)
    elif mutation == "missing_u":
        del lines[1]
    elif mutation == "bad_time":
        lines[0] = lines[0].replace("time 1.0", "time 0.5")
    elif mutation == "bad_energy":
        lines[-1] = "1.0"
    else:
        lines[1] = "1 nan 0 0"
    with pytest.raises(ValueError):
        checker.check("\n".join(lines), expected, coords, strain)
