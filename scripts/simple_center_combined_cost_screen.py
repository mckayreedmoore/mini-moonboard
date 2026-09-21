"""Provisional PB-02 right-center cut and purchase arithmetic; no part selection."""

import json
from decimal import ROUND_HALF_UP, Decimal

from scripts.simple_center_stock_yield import FOOT_MM, cut_yield, side_rip


def report():
    """Count only committed right-center bores and price illustrative retail leads."""
    stock_length = 8 * FOOT_MM
    members = {
        "4x4": cut_yield(stock_length, ["238.9", "183", "128.9"]),
        "2x4": cut_yield(stock_length, ["460"]),
        "4x6": cut_yield(stock_length, ["238.9", "145"]),
    }
    counts = {
        "inherited_post": 2,
        "inherited_link": 1,
        "inherited_upright": 1,
        "new_post_to_header_side_cleat": 1,
        "new_side_cleat_to_header": 1,
        "new_header_to_principal_side_cleat": 1,
        "new_principal_side_cleat_to_principal": 1,
        "total_1_4_bolts": 8,
        "nuts": 8,
        "washers": 16,
    }
    # ponytail: this nominal-span basket is a price illustration, not a stack fit.
    bolt_basket = 2 * Decimal("0.62") + 4 * Decimal("0.71") + 2 * Decimal("0.94")
    allocated = bolt_basket + 8 * Decimal("1.98") / 12 + 16 * Decimal("1.98") / 16
    checkout = bolt_basket + Decimal("1.98") + Decimal("1.98")
    money = lambda value: str(value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))
    return {
        "members": members,
        "side_cleat_rip": side_rip(),
        "principal_cleat_rips": {
            "grain_y_cut_length_mm": 145.0,
            "blank_section_mm": [88.9, 139.7],
            "finished_section_mm": [70.95, 103.0],
            "rip_kerf_each_mm": 3.2,
            "x_offcut_mm": 14.75,
            "z_offcut_mm": 33.5,
        },
        "hardware_counts": counts,
        "illustrative_bolt_lengths_qty": {"5_in": 2, "6_in": 4, "8_in": 2},
        "example_hardware_usd": {
            "allocated": money(allocated),
            "first_checkout": money(checkout),
        },
        "wood_allocated_cost_formula": (
            "(560.4/2438.4)*P_4x4 + (463.2/2438.4)*P_2x4 + (390.3/2438.4)*P_4x6"
        ),
        "wood_first_checkout_formula": "P_4x4 + P_2x4 + P_4x6",
    }


if __name__ == "__main__":
    print(json.dumps(report(), indent=2, sort_keys=True))
