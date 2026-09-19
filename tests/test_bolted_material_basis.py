"""The bolted candidate keeps reference lumber data separate from actual stock."""

import json
from pathlib import Path

import pytest

from fea.reinforced_timber_resistance import PRIMARY_PDF_SHA256, adjusted_reference


def test_candidate_dfl_material_record_is_source_bound_and_conditional():
    record = json.loads(Path("docs/bolted-candidate-material-basis.json").read_text())
    assert record["species_grade"] == "US Douglas Fir-Larch No. 2 dimension lumber"
    assert record["actual_stock"]["grade_stamp_verified"] is False
    assert record["actual_stock"]["moisture_verified"] is False
    assert record["engineering_disposition"] == "conditional_reference_only"
    assert record["source"]["edition"] == "2024 NDS and 2024 NDS Supplement"
    assert record["source"]["supplement_ch4_sha256"] == PRIMARY_PDF_SHA256[
        "NDS2024_supplement_ch4"
    ]

    reference = record["reference_values"]
    for name, expected in {
        "Fb": 900, "Ft_parallel": 575, "Fv_parallel": 180,
        "Fc_parallel": 1350, "Fc_perpendicular": 625,
        "E": 1600000, "Emin": 580000,
    }.items():
        assert reference[name]["value"] == expected
        assert reference[name]["unit"] == "psi"
        assert reference[name]["adjusted"] is False
    assert reference["G"]["value"] == pytest.approx(0.5)
    assert reference["G"]["unit"] == "dimensionless"
    assert record["nominal_2x6_size_factor_only"]["Ft_parallel"] == 1.3
    assert adjusted_reference(139.7)["Ft_mpa"] / 0.006894757293168361 == pytest.approx(
        reference["Ft_parallel"]["value"] * 1.3
    )
    assert record["fabrication_release"] is False
