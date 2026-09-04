from fea.generate_v1_fixed_foot_frame import CLIMBER_LOAD_N, RAIL_DISTANCES, build_deck


def test_fixed_foot_frame_deck_has_all_screen_cases_and_foot_constraints() -> None:
    deck = build_deck()

    assert deck.count("*STEP\n") == 5
    assert "*NSET, NSET=FEET" in deck
    assert deck.count("FEET, 1, 6, 0.") == 5
    assert "** CASE TOP_NORMAL_TO_SUPPORT" in deck
    assert "** CASE TOP_COMBINED" in deck
    assert f"{CLIMBER_LOAD_N * 0.7660444431 / 5:.6f}" in deck
    assert f"R1_{len(RAIL_DISTANCES) - 1}" not in deck  # generated deck is numeric-only
