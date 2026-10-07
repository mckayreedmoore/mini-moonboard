"""Mechanics export regression: NumPy booleans must stay real JSON booleans."""

import json

import numpy as np
import pytest

from scripts.run_thin_bolted_mechanics import dump


def test_serializes_numerical_scalars_without_changing_values_or_flags():
    result = json.loads(dump({"accepted": np.bool_(False), "equilibrium": np.bool_(True),
                             "value": np.float64(1.23456789012345), "count": np.int64(62),
                             "forces": np.array([1.5, -2.75, 0.])}))
    assert result == {"accepted": False, "equilibrium": True, "value": 1.23456789012345,
                      "count": 62, "forces": [1.5, -2.75, 0.]}
    assert type(result["accepted"]) is bool


def test_invalid_or_nonfinite_export_stops():
    with pytest.raises(TypeError):
        dump({"not_a_numeric_field": object()})
    with pytest.raises(ValueError):
        dump({"force": np.float64(float("nan"))})
