"""Apply the identical native replay/rejection checks to revised geometry."""
from pathlib import Path

import pytest
from test_lumber_leg_native import (  # noqa: F401 -- pytest collects shared audit cases
    load_native,
    test_all_native_bases_and_scenarios_replay,
    test_leg_specific_gates_reject_inconsistent_native_fields,
    test_native_energy_gate_rejects_changed_energy,
)

ARCHIVES = [Path("fea/results/spread-leg-response")/f"{size}-e300-m40-E7000.tar.gz"
            for size in ("2x6", "2x8")]


@pytest.fixture(scope="module", params=ARCHIVES, ids=lambda p: p.stem)
def native(request):
    files, report, value = load_native(request.param)
    assert report["geometry"] == "spread-100x50-top150"
    for leg in value["legs"].values():
        mesh = leg["mesh"]
        assert (mesh["along_leg_pitch_mm"], mesh["along_rim_pitch_mm"],
                mesh["top_extension_mm"]) == (100., 50., 150.)
    return files, report, value
