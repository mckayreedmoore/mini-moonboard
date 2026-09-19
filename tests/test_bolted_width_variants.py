"""LB-09 width identity and transformation checks."""

from mini_moonboard.bolted_floor_flush_width import KERF_RIGHT, KERF_RIGHT_MM, geometry_screen, variant


def test_both_width_variants_resolve_the_bolted_candidate() -> None:
    official = variant("official")
    kerf = variant(KERF_RIGHT)
    assert official.KEY.endswith("-official")
    assert kerf.KEY.endswith("-kerf-right")
    assert len(official.panel_connections()) == len(kerf.panel_connections()) == 66
    assert len(official.structural_joint_records()) == len(kerf.structural_joint_records()) == 24


def test_kerf_right_translates_right_interfaces_without_claiming_mechanics() -> None:
    result = geometry_screen()
    assert result["right_shift_mm"] == KERF_RIGHT_MM
    assert result["right_shift_consistent"] is True
    assert result["mechanical_evidence_for_kerf_right"] is False
