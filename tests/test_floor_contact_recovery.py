import pytest

from fea.floor_contact import SOURCE
from fea.floor_contact_recovery import CONTROLS, recovery_deck, validate_context


def test_recovery_changes_only_controls_and_diagnostic_output():
    base = "*BOUNDARY\nGROUND_LEFT,1,3,0\n" + 2 * "*STEP,NLGEOM\n*STATIC\n0.05,1,1e-6,0.1\n*DLOAD\nTIMBER,GRAV,9806.65,0,0,-1\n*END STEP\n"
    result = recovery_deck(base, {"LEFT": []})
    output = "*CONTACT PRINT\nCDIS,CSTR\n*CONTACT PRINT,SLAVE=SLAVE_LEFT,MASTER=MASTER_LEFT\nCF,CFN,CFS\n"
    assert result.count(CONTROLS) == 2
    assert result.count(output) == 2
    assert result.replace(CONTROLS, "").replace(output, "") == base


@pytest.mark.parametrize("volume,centre", [(float("nan"), [0, 0, 0]), (0, [0, 0, 0]),
                                         (1, [0, float("inf"), 0]), (1, [0, 0])])
def test_invalid_cad_context_is_rejected(volume, centre):
    with pytest.raises(ValueError, match="CAD volume"):
        validate_context({"cad_volume_mm3": volume, "cad_centre_mm": centre}, {}, "digest")


def test_source_summary_and_preparation_must_agree():
    info = {"cad_volume_mm3": 1, "cad_centre_mm": [0, 0, 0], "source_sha256": "same",
            "geometry_source_sha256": {"geometry.py": "hash"}}
    summary = {"evidence_sha256": {SOURCE.name: "same"},
               "frozen_geometry": {"geometry_source_sha256": {"geometry.py": "hash"}}}
    validate_context(info, summary, "same")
    with pytest.raises(ValueError, match="mesh provenance"):
        validate_context(info, summary, "changed")
    summary["evidence_sha256"][SOURCE.name] = "changed"
    with pytest.raises(ValueError, match="mesh provenance"):
        validate_context(info, summary, "same")
    summary["evidence_sha256"][SOURCE.name] = "same"
    summary["frozen_geometry"]["geometry_source_sha256"] = {}
    with pytest.raises(ValueError, match="geometry provenance"):
        validate_context(info, summary, "same")
