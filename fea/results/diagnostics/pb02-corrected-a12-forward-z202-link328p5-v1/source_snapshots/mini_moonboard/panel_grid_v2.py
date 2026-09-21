"""Panel-edge datum correction, separate from the frozen historical grid.

Metric template interpretation: lower T-nut rows are measured down from the
lower panel's top edge; upper rows are measured up from the upper panel's bottom.
The 80 mm bottom dimension is T-nut-to-LED spacing, not a T-nut bottom offset.
LED7 belongs to the lower panel, 20 mm below its top edge.

The default adapts that datum policy to actual 48 in (1219.2 mm) panels. All
lower-panel positions, including LED1, retain their top-edge datum, so LED1 is
19.2 mm above the bottom rather than the nominal drawing's 20 mm. This resolves
inconsistent edge dimensions by an explicit stock adaptation, not by claiming
exact compliance with both dimensions. Pass 1220.0 for the nominal metric case.
No coordinate is scaled, and the rounded imperial PDF is not treated as an exact
48 in template. Callers must explicitly opt into this module and regenerate CAD,
service clearances, labels and evidence; old exports remain historical.

Source: https://moonclimbing.com/build-your-moonboard (Mini panel metric PDF and
FAQ confirming 220 mm between rows 6 and 7), inspected 2026-09-07.
"""

from .panel_grid import MAIN_COLUMNS, MAIN_ROWS, kicker_foothold_datums

__all__ = ["kicker_foothold_datums", "main_led_datums", "main_tnut_datums"]

PANEL_HEIGHT_MM = 1219.2
NOMINAL_PANEL_HEIGHT_MM = 1220.0


def _height(panel_height_mm: float) -> float:
    if panel_height_mm not in (PANEL_HEIGHT_MM, NOMINAL_PANEL_HEIGHT_MM):
        raise ValueError("Only 1219.2 mm stock adaptation or 1220 mm nominal template is supported")
    return float(panel_height_mm)


def main_tnut_datums(panel_height_mm: float = PANEL_HEIGHT_MM) -> dict[str, tuple[float, float]]:
    """Return centers from the assembled main face's lower-left, viewed in front."""
    height = _height(panel_height_mm)
    return {
        f"{column}{row}": (200.0 * index,
            height - 1120.0 + 200.0 * (row - 1) if row <= 6
            else height + 100.0 + 200.0 * (row - 7))
        for index, column in enumerate(MAIN_COLUMNS, 1)
        for row in MAIN_ROWS
    }


def main_led_datums(panel_height_mm: float = PANEL_HEIGHT_MM) -> dict[str, tuple[float, float]]:
    """Return paired LED centers, preserving the row1/row7 boundary exceptions."""
    height = _height(panel_height_mm)
    stations = (height - 1200.0,
                *(height - 1020.0 + 200.0 * index for index in range(6)),
                *(height + 200.0 + 200.0 * index for index in range(5)))
    return {f"{column}{row}": (200.0 * index, stations[row - 1])
            for index, column in enumerate(MAIN_COLUMNS, 1) for row in MAIN_ROWS}
