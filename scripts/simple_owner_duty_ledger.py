"""Selected-baseline structural clip duties; inventory, not strength approval."""

import csv
from pathlib import Path

AXES_CSV = (
    Path(__file__).resolve().parents[1]
    / "docs/floor-flush-construction/connection-axes.csv"
)

# Exact selected-baseline mirrored stations. Side is an owner-layout assignment,
# not inferred from screw order or a replacement candidate's geometry.
PAIRS = (
    ("top_outer", "clip_single_top_left_1", "clip_single_top_right_2"),
    ("top_center", "clip_split_top_center_left", "clip_split_top_center_right"),
    ("bottom_outer", "clip_horizontal_bottom_left_1", "clip_horizontal_bottom_right_2"),
    (
        "bottom_center",
        "clip_horizontal_bottom_left_2",
        "clip_horizontal_bottom_right_1",
    ),
    ("lower_outer", "clip_horizontal_lower_left_1", "clip_horizontal_lower_right_2"),
    ("lower_center", "clip_horizontal_lower_left_2", "clip_horizontal_lower_right_1"),
    ("upper_outer", "clip_horizontal_upper_left_1", "clip_horizontal_upper_right_2"),
    ("upper_center", "clip_horizontal_upper_left_2", "clip_horizontal_upper_right_1"),
    (
        "header_outer_post",
        "clip_timber_header_outer_left",
        "clip_timber_header_outer_right",
    ),
    (
        "header_center",
        "clip_split_header_center_left",
        "clip_split_header_center_right",
    ),
    ("base_center", "clip_split_base_center_left", "clip_split_base_center_right"),
    ("base_outer_side", "clip_angle_base_left", "clip_angle_base_right"),
)
EXCEPTIONS = frozenset(
    {
        "clip_angle_base_left",
        "clip_angle_base_right",
        "clip_timber_header_outer_left",
        "clip_timber_header_outer_right",
    }
)
PB02_CENTER_PAIRS = frozenset({"base_center", "header_center"})
PB02_DISPLACED = frozenset(
    {"clip_split_base_center_right", "clip_split_header_center_right"}
)

# ponytail: these are review gates, not modeled clearances; candidate geometry
# must supply measured 3D evidence before any gate can be marked verified.
VIEWER_GATES = (
    "protected_holds_3d",
    "t_nuts_3d",
    "unused_hold_holes_3d",
    "hold_bolt_protrusion",
    "led_body_and_wiring",
    "all_66_panel_screws",
    "retained_frame_bolts",
)


def _axis(row):
    return tuple(float(row[f"direction_{coordinate}"]) for coordinate in "xyz")


def _start(row):
    return tuple(float(row[f"start_{coordinate}_mm"]) for coordinate in "xyz")


def selected_duties(axes_csv=AXES_CSV):
    """Bind each legacy station to its six actual SDS axes and two timbers."""
    expected = {
        station: (family, side)
        for family, left, right in PAIRS
        for station, side in ((left, "left"), (right, "right"))
    }
    with Path(axes_csv).open(newline="") as source:
        rows = [
            row
            for row in csv.DictReader(source)
            if row["shop_opening_kind"] == "sds_wood"
        ]
    grouped = {}
    for row in rows:
        grouped.setdefault(row["first_member"], []).append(row)
    if set(grouped) != set(expected) or len(rows) != 144:
        raise ValueError("Selected-baseline structural SDS station set changed")
    if len({row["name"] for row in rows}) != 144:
        raise ValueError("Selected-baseline structural SDS axis IDs are not unique")

    duties = {}
    for station, (family, side) in expected.items():
        station_rows = grouped[station]
        beam = [
            row for row in station_rows if row["name"].startswith(f"{station}_beam_")
        ]
        upright = [
            row for row in station_rows if row["name"].startswith(f"{station}_upright_")
        ]
        if (
            len(station_rows) != 6
            or len(beam) != 3
            or len(upright) != 3
            or any(row["kind"] != "screw" for row in station_rows)
            or len({row["second_member"] for row in beam}) != 1
            or len({row["second_member"] for row in upright}) != 1
            or len({_axis(row) for row in beam}) != 1
            or len({_axis(row) for row in upright}) != 1
        ):
            raise ValueError(f"Incomplete or inconsistent six-axis duty: {station}")
        timber = (beam[0]["second_member"], upright[0]["second_member"])
        if not timber[1].endswith(side):
            raise ValueError(f"Station is not on its assigned side: {station}")
        duties[station] = {
            "family": family,
            "side": side,
            "same_side_corner": (family, side),
            "timber": timber,
            "local_axes": {"first": _axis(beam[0]), "second": _axis(upright[0])},
            "sds_axes": tuple(row["name"] for row in station_rows),
            "axis_starts_mm": {row["name"]: _start(row) for row in station_rows},
            "layout_class": "exception" if station in EXCEPTIONS else "ordinary",
            "pb02_center_pair": family if family in PB02_CENTER_PAIRS else None,
            "pb02_displaced": station in PB02_DISPLACED,
        }
    return duties


def _name(item):
    if isinstance(item, str):
        return item
    if isinstance(item, dict):
        return item["name"]
    return item.name


def inventory_status(duties, replacement_by_station, parts, connections):
    """Screen only layout completeness; never imply fabrication/strength approval."""
    mapped = {
        station
        for station, replacement in replacement_by_station.items()
        if replacement
    }
    missing = sorted(set(duties) - mapped)
    unexpected = sorted(set(replacement_by_station) - set(duties))
    old_names = {_name(item) for item in parts} | {_name(item) for item in connections}
    old_clips = sorted(old_names & set(duties))
    old_axes = sorted(
        old_names & {axis for duty in duties.values() for axis in duty["sds_axes"]}
    )
    return {
        # Mapping is necessary for a complete assembly, never sufficient for one.
        "inventory_mapped_without_legacy": not (
            missing or unexpected or old_clips or old_axes
        ),
        "missing_replacements": missing,
        "unexpected_replacements": unexpected,
        "old_clips": old_clips,
        "old_sds_axes": old_axes,
        "viewer_gates": {gate: "unverified" for gate in VIEWER_GATES},
        "viewer_clearance_approved": False,
        "structural_approval": False,
    }
