MAIN_COLUMNS = "ABCDEFGHIJK"
MAIN_ROWS = range(1, 13)


def main_tnut_datums() -> dict[str, tuple[float, float]]:
    """Return metric-template T-nut centers from the main surface lower-left."""
    return {
        f"{column}{row}": (200.0 * column_index, 80.0 + 200.0 * (row - 1))
        for column_index, column in enumerate(MAIN_COLUMNS, start=1)
        for row in MAIN_ROWS
    }


def main_led_datums() -> dict[str, tuple[float, float]]:
    """Return LED centers paired with the T-nut labels in the metric template."""
    return {label: (x, y - 100.0) for label, (x, y) in main_tnut_datums().items()}
