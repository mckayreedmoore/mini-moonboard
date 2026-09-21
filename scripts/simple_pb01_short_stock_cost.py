"""Conditional one-stick PB01 wood yield; never a cut or purchase instruction."""

import json
from decimal import ROUND_FLOOR, Decimal


def decimal(value):
    return Decimal(str(value))


def yield_from_stick(stock_mm, blank_mm, kerf_mm, trim_mm=0):
    """Reserve one crosscut kerf per blank, including its separation from remainder."""
    stock, blank, kerf, trim = map(decimal, (stock_mm, blank_mm, kerf_mm, trim_mm))
    if stock <= 0 or blank <= 0 or kerf < 0 or trim < 0:
        raise ValueError("positive stock/blank and nonnegative kerf/trim required")
    blanks = max(
        0,
        int(((stock - trim) / (blank + kerf)).to_integral_value(rounding=ROUND_FLOOR)),
    )
    used = blanks * (blank + kerf) + trim
    return {
        "blanks": blanks,
        "total_crosscut_kerf_mm": float(blanks * kerf),
        "used_mm": float(used),
        "remainder_mm": float(stock - used),
    }


def report():
    """Give geometric bounds using listed/assumed sections and example blade kerf."""
    final_depth = decimal("57.15")
    final_width = decimal("139.7")
    rip_kerf = decimal("3.2")
    lowes_depth = decimal("3.562") * decimal("25.4")
    lowes_width = decimal("5.625") * decimal("25.4")
    hd_depth = decimal("3.5") * decimal("25.4")
    stock_length = decimal("8") * decimal("12") * decimal("25.4")
    return {
        "assumed_crosscut_and_rip_kerf_mm": float(rip_kerf),
        "length_mm": float(stock_length),
        "short_152_4": yield_from_stick(stock_length, "152.4", rip_kerf),
        "historical_300": yield_from_stick(stock_length, "300", rip_kerf),
        "lowes": {
            "stock_section_mm": [float(lowes_depth), float(lowes_width)],
            "depth_offcut_after_rip_kerf_mm": float(
                lowes_depth - final_depth - rip_kerf
            ),
            "width_to_remove_mm": float(lowes_width - final_width),
        },
        "home_depot_assumed": {
            "stock_section_mm": [float(hd_depth), float(final_width)],
            "depth_offcut_after_rip_kerf_mm": float(hd_depth - final_depth - rip_kerf),
        },
        "volume_reduction_percent": float(
            (1 - decimal("152.4") / decimal("300")) * 100
        ),
        "hardware_change_usd": 0,
        "board_checkout_usd": None,
    }


if __name__ == "__main__":
    print(json.dumps(report(), indent=2, sort_keys=True))
