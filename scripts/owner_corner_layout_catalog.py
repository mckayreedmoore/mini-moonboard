"""Exact proposed geometry owners for the 24 selected bracket duties.

This catalog proves coverage only. A complete viewer still requires one
collision-screened assembly, installed hardware, and explicit open gates.
"""

from scripts import owner_layout_bottom_center_pair as bottom_center
from scripts import owner_layout_center_header_four as center_header
from scripts import owner_layout_outer_header_pair as outer_header
from scripts import simple_owner_duty_ledger as ledger
from scripts import simple_owner_outer_base_pair as outer_base
from scripts import simple_pb09_owner_layout_screen as rail
from scripts import simple_top_same_side_four as top

FAMILIES = {
    "rail_ten": rail.STATIONS,
    "top_four": top.TARGET_STATIONS,
    "bottom_center_pair": bottom_center.STATIONS,
    "center_header_four": center_header.STATIONS,
    "outer_header_pair": outer_header.STATIONS,
    "outer_base_pair": outer_base.TARGETS,
}


def station_producers():
    """Return one producer per duty, rejecting omissions and duplicates."""
    producers = {}
    for producer, stations in FAMILIES.items():
        for station in stations:
            if station in producers:
                raise ValueError(f"Duplicate owner-layout duty: {station}")
            producers[station] = producer
    expected = set(ledger.selected_duties())
    if set(producers) != expected:
        raise ValueError(
            f"Owner-layout duty mismatch: missing={sorted(expected - set(producers))}, "
            f"unexpected={sorted(set(producers) - expected)}"
        )
    return producers
