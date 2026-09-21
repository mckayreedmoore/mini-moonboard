"""Exact proposed geometry owners for the 24 selected bracket duties.

This catalog proves coverage only. A complete viewer still requires one
collision-screened assembly, installed hardware, and explicit open gates.
"""

from scripts import simple_owner_duty_ledger as ledger

FAMILY_TO_PRODUCER = {
    "top_outer": "top_four",
    "top_center": "top_four",
    "bottom_outer": "rail_ten",
    "bottom_center": "bottom_center_pair",
    "lower_outer": "rail_ten",
    "lower_center": "rail_ten",
    "upper_outer": "rail_ten",
    "upper_center": "rail_ten",
    "header_outer_post": "outer_header_pair",
    "header_center": "center_header_four",
    "base_center": "center_header_four",
    "base_outer_side": "outer_base_pair",
}


def station_producers():
    """Assign each authenticated duty to one intended geometry family."""
    duties = ledger.selected_duties()
    actual_families = {row["family"] for row in duties.values()}
    if actual_families != set(FAMILY_TO_PRODUCER):
        raise ValueError("Owner-layout duty families changed")
    return {
        station: FAMILY_TO_PRODUCER[row["family"]] for station, row in duties.items()
    }
