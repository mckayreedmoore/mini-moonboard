"""PB-02 one-post/two-cleat stock-length sidecar; no fabrication release."""

import json
from decimal import Decimal

INCH_MM = Decimal("25.4")
FOOT_MM = 12 * INCH_MM
KERF_MM = Decimal("3.2")  # Example crosscut blade allowance, not a tool specification.
END_TRIM_MM = Decimal(0)  # No damaged-end or squaring allowance is modeled.


def cut_yield(
    stock_length_mm, cut_lengths_mm, kerf_mm=KERF_MM, end_trim_mm=END_TRIM_MM
):
    """Account for one full kerf per separated part, including the last offcut."""
    stock = Decimal(str(stock_length_mm))
    cuts = [Decimal(str(value)) for value in cut_lengths_mm]
    kerf = Decimal(str(kerf_mm))
    trim = Decimal(str(end_trim_mm))
    if stock <= 0 or not cuts or any(length <= 0 for length in cuts):
        raise ValueError("stock and cut lengths must be positive")
    if kerf < 0 or trim < 0:
        raise ValueError("kerf and end trim must be nonnegative")
    consumed = sum(cuts) + len(cuts) * kerf + trim
    remainder = stock - consumed
    return {
        "stock_length_mm": float(stock),
        "cut_lengths_mm": [float(length) for length in cuts],
        "crosscuts": len(cuts),
        "kerf_per_crosscut_mm": float(kerf),
        "total_crosscut_kerf_mm": float(len(cuts) * kerf),
        "end_trim_mm": float(trim),
        "remainder_mm": float(remainder),
        "length_feasible": remainder >= 0,
    }


def side_rip(
    blank_depth_mm=Decimal("88.9"), finished_depth_mm=Decimal("56.8"), kerf_mm=KERF_MM
):
    """Compute nominal side-cleat rip offcut after one blade kerf."""
    blank = Decimal(str(blank_depth_mm))
    finished = Decimal(str(finished_depth_mm))
    kerf = Decimal(str(kerf_mm))
    offcut = blank - finished - kerf
    return {
        "blank_depth_mm": float(blank),
        "finished_depth_mm": float(finished),
        "rip_kerf_mm": float(kerf),
        "offcut_width_mm": float(offcut),
        "section_feasible": finished > 0 and kerf >= 0 and offcut >= 0,
    }


def report():
    """Calculate the bounded current trial, with a published shorter 2x4 minimum."""
    return {
        "example_assumptions": {
            "crosscut_kerf_mm": float(KERF_MM),
            "rip_kerf_mm": float(KERF_MM),
            "end_trim_mm": float(END_TRIM_MM),
        },
        "four_by_four_8ft": cut_yield(8 * FOOT_MM, ["238.9", "183"]),
        "two_by_four_8ft": cut_yield(8 * FOOT_MM, ["460"]),
        "two_by_four_lowes_kd_min_7_72ft": cut_yield(
            Decimal("7.72") * FOOT_MM, ["460"]
        ),
        "side_rip_nominal_88_9_to_56_8": side_rip(),
    }


if __name__ == "__main__":
    print(json.dumps(report(), indent=2, sort_keys=True))
