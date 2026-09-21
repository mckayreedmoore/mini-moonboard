"""Every original bracket duty needs one owner-layout geometry producer."""

from scripts.owner_corner_layout_catalog import station_producers
from scripts.simple_owner_duty_ledger import selected_duties


def test_six_producers_cover_exactly_all_twenty_four_duties():
    producers = station_producers()
    assert set(producers) == set(selected_duties())
    assert len(producers) == 24
    assert {
        source: list(producers.values()).count(source)
        for source in set(producers.values())
    } == {
        "rail_ten": 10,
        "top_four": 4,
        "bottom_center_pair": 2,
        "center_header_four": 4,
        "outer_header_pair": 2,
        "outer_base_pair": 2,
    }
