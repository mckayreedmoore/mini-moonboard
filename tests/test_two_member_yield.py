import pytest

from fea.two_member_yield import build


def test_current_two_member_reference_inventory():
    rows = build()
    assert len(rows) == len({r["connection"] for r in rows}) == 14
    stitch = [r for r in rows if r["connection"].startswith("leg_stitch_")]
    gusset = [r for r in rows if r["connection"].startswith("timber_base_")]
    assert len(stitch) == 6 and len(gusset) == 8
    for row in rows:
        inputs = row["inputs"]
        assert inputs["side_length_in"] == pytest.approx(.75)
        assert inputs["gap_in"] == 0
        assert row["governing_mode"] == "II"
        assert row["reference_lateral_n"] == pytest.approx(row["reference_lateral_lbf"]*4.4482216152605)
    for row in stitch:
        assert row["inputs"]["main_length_in"] == pytest.approx(.75)
        assert row["reference_lateral_lbf"] == pytest.approx(115.2065988147)
    for row in gusset:
        assert row["inputs"]["main_length_in"] == pytest.approx(1.5)
        assert row["reference_lateral_lbf"] == pytest.approx(138.2048785579)
