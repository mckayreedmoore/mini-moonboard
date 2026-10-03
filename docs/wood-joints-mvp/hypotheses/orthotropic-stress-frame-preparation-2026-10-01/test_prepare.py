import importlib.util
import math
from pathlib import Path

import pytest

spec = importlib.util.spec_from_file_location(
    "stress_frame_prepare", Path(__file__).with_name("prepare.py")
)
prepare = importlib.util.module_from_spec(spec)
spec.loader.exec_module(prepare)


def test_emitted_boundary_values_cover_actual_deck_and_affine_field():
    deck, expected = prepare.prepare()
    section = deck.split("*BOUNDARY\n")[1].split("*STEP\n")[0]
    rows = [line.split(",") for line in section.splitlines()]
    assert len(rows) == 1536
    actual = {(int(row[0]), int(row[1])): float(row[3]) for row in rows}
    assert len(actual) == 1536
    assert all(row[1] == row[2] and len(row[3]) <= 20 for row in rows)
    # Authenticated node 1 is (2.5,0,0), giving the strain tensor's first column.
    assert actual[1, 1] == pytest.approx(5.0e-5)
    assert actual[1, 2] == pytest.approx(1.25e-5)
    assert actual[1, 3] == pytest.approx(1.75e-5)
    assert actual[2, 1] == pytest.approx(2e-5 * 2.30969883128 + 5e-6 * 0.956708580913)
    assert expected["mesh"]["free_dofs"] == 864
    assert expected["native_run_executed"] is False
    assert expected["ready_for_native_run"] is False


def test_three_distinct_identical_element_sets_and_output_frames():
    deck, expected = prepare.prepare()
    for name in ("SGLOBAL", "SLOCAL", "SDEFAULT"):
        assert f"*ELSET,ELSET={name},GENERATE\n1,384,1\n" in deck
    assert "*EL PRINT,ELSET=SGLOBAL,GLOBAL=YES\nS\n" in deck
    assert "*EL PRINT,ELSET=SLOCAL,GLOBAL=NO\nS\n" in deck
    assert "*EL PRINT,ELSET=SDEFAULT\nS\n" in deck
    assert expected["global_stress_tensor_MPa"] != expected["local_stress_tensor_MPa"]
    assert expected["expected_energy_N_mm"] == pytest.approx(0.00376030465, rel=1e-7)
    assert "*CONTACT" not in deck and "*CLOAD" not in deck
    assert "Isotropic linear elastic" not in deck


@pytest.mark.parametrize("value", [math.nan, math.inf, -math.inf, -1e308])
def test_nonfinite_or_overlong_field_refused(value):
    with pytest.raises(ValueError):
        prepare.number(value)


def test_changed_source_refused(monkeypatch):
    monkeypatch.setattr(prepare, "PINS", {"model.inp": "0" * 64})
    with pytest.raises(ValueError, match="changed source"):
        prepare.prepare()
