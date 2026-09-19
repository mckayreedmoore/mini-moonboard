"""Export the frozen structural/panel attachment partition for both widths."""

import argparse
import csv
import json
from collections import defaultdict
from pathlib import Path

from mini_moonboard.bolted_layout_common import FAMILY_STATIONS

ROOT = Path(__file__).resolve().parents[1]
SOURCES = {
    "official": "docs/floor-flush-construction/connection-axes.csv",
    "kerf-right": "docs/floor-flush-construction-kerf-right/connection-axes.csv",
}
SHOP_KIND = {
    "sds_wood": ("structural", "replace_at_station"),
    "bolt_clearance": ("structural", "retain_and_reassess"),
    "hillman_panel": ("panel", "retain"),
}
def load_axes(width: str) -> tuple[dict[str, str], ...]:
    if width not in SOURCES:
        raise ValueError(f"unknown width: {width}")
    with (ROOT / SOURCES[width]).open(newline="") as handle:
        return tuple(csv.DictReader(handle))


def classify(row: dict[str, str]) -> dict[str, object]:
    kind = row["shop_opening_kind"]
    if kind not in SHOP_KIND:
        raise ValueError(f"unclassified attachment {row['name']}: {kind}")
    scope, disposition = SHOP_KIND[kind]
    return {
        "axis_id": row["name"],
        "members": [row["first_member"], row["second_member"]],
        "hardware_scope": scope,
        "baseline_attachment": kind,
        "candidate_disposition": disposition,
    }


def panel_axis(row: dict[str, str]) -> dict[str, object]:
    if row["shop_opening_kind"] != "hillman_panel":
        raise ValueError(f"not a panel axis: {row['name']}")
    return {
        "axis_id": row["name"],
        "panel": row["first_member"],
        "receiver": row["second_member"],
        "start_xyz_mm": [float(row[f"start_{axis}_mm"]) for axis in "xyz"],
        "direction_xyz": [float(row[f"direction_{axis}"]) for axis in "xyz"],
        "occupied_diameter_mm": float(row["occupied_diameter_mm"]),
        "modeled_diameter_mm": float(row["modeled_diameter_mm"]),
        "shop_purchased_length_mm": float(row["shop_purchased_length_mm"]),
        "hardware": "Hillman 42605 #10 x 2-1/2 in",
    }


def require_same_panel_axes(
    reference: tuple[dict[str, str], ...], candidate: tuple[dict[str, str], ...]
) -> None:
    expected_rows = [row for row in reference if row["shop_opening_kind"] == "hillman_panel"]
    actual_rows = [row for row in candidate if row["shop_opening_kind"] == "hillman_panel"]
    expected = {row["name"]: panel_axis(row) for row in expected_rows}
    actual = {row["name"]: panel_axis(row) for row in actual_rows}
    if len(expected_rows) != 66 or len(actual_rows) != 66 or len(expected) != 66 or len(actual) != 66 or expected != actual:
        raise ValueError("retained panel axes differ from the matching width source")


def width_contract(width: str, rows: tuple[dict[str, str], ...]) -> dict[str, object]:
    names = [row["name"] for row in rows]
    if len(names) != len(set(names)):
        raise ValueError(f"duplicate attachment axes in {width}")
    scope_by_axis_id = {row["name"]: classify(row)["hardware_scope"] for row in rows}
    by_kind: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        by_kind[row["shop_opening_kind"]].append(row)
    if (len(by_kind["sds_wood"]), len(by_kind["bolt_clearance"]), len(by_kind["hillman_panel"])) != (144, 12, 66):
        raise ValueError(f"wrong attachment inventory in {width}")

    by_station: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in by_kind["sds_wood"]:
        by_station[row["first_member"]].append(row)
    station_family = {station: family for family, stations in FAMILY_STATIONS.items() for station in stations}
    if set(by_station) != set(station_family) or any(len(axes) != 6 for axes in by_station.values()):
        raise ValueError(f"structural station coverage differs from the selected baseline in {width}")
    stations = []
    for family, station_names in FAMILY_STATIONS.items():
        for station in station_names:
            axes = by_station[station]
            receivers = sorted({row["second_member"] for row in axes})
            if len(receivers) != 2 or any(sum(row["second_member"] == member for row in axes) != 3 for member in receivers):
                raise ValueError(f"station {station} lacks three source duties per receiver")
            stations.append({
                "station_id": station,
                "family": family,
                "timber_members": receivers,
                "legacy_sds_axis_ids": [row["name"] for row in axes],
                "candidate_joint_status": "replacement_detail_unresolved",
            })

    timber = sorted({row["second_member"] for row in rows} |
                    {row["first_member"] for row in by_kind["bolt_clearance"]})
    panels = sorted({row["first_member"] for row in by_kind["hillman_panel"]})
    if len(timber) != 20 or len(panels) != 6:
        raise ValueError(f"transport inventory differs from the selected baseline in {width}")
    return {
        "source": SOURCES[width],
        "scope_by_axis_id": scope_by_axis_id,
        "panel_axes": [panel_axis(row) for row in by_kind["hillman_panel"]],
        "structural_stations": stations,
        "retained_frame_bolts": [
            {"axis_id": row["name"], "members": [row["first_member"], row["second_member"]]}
            for row in by_kind["bolt_clearance"]
        ],
        "transport_members": {"timber": timber, "panels": panels},
        "scope_counts": {"structural_sds_to_replace": 144, "structural_frame_bolts_to_reassess": 12,
                         "panel_screws_to_retain": 66, "hold_axes": 0, "service_axes": 0},
        "draft_separation_graph": {
            "structural_joint_station_ids": [row["station_id"] for row in stations],
            "retained_frame_bolt_axis_ids": [row["name"] for row in by_kind["bolt_clearance"]],
            "panel_axis_ids": [row["name"] for row in by_kind["hillman_panel"]],
            "structural_operation": "remove selected metal-threaded structural fasteners; exact detail unresolved",
            "frame_bolt_operation": "remove frame bolt after temporary support",
            "panel_operation": "remove retained Hillman panel/kicker screw",
            "retained_flange_rule": "one timber member maximum per retained flange; actual assignment unresolved",
            "final_disassembly_sequence_ready": False,
        },
        "move_operations": {
            "structural_wood_thread_removals_target": 0,
            "panel_wood_thread_removals_allowed": 66,
            "hold_operations": "unresolved if climbing holds are fitted",
            "service_operations": "unresolved until service hardware is inventoried",
        },
    }


def contracts() -> dict[str, dict[str, object]]:
    return {width: width_contract(width, load_axes(width)) for width in SOURCES}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--panel-output", type=Path, required=True)
    parser.add_argument("--interfaces-output", type=Path, required=True)
    args = parser.parse_args()
    all_widths = contracts()
    panel = json.loads(args.panel_output.read_text())
    interfaces = json.loads(args.interfaces_output.read_text())
    panel["source_commit"] = "7cdd2e37ed2d364b47879a960b9eb15b93c67048"
    panel["normalized_panel_axes_by_width"] = {
        width: data["panel_axes"] for width, data in all_widths.items()
    }
    interfaces["source_commit"] = panel["source_commit"]
    interfaces["classified_by_width"] = {
        width: {key: value for key, value in data.items() if key != "panel_axes"}
        for width, data in all_widths.items()
    }
    args.panel_output.write_text(json.dumps(panel, indent=2) + "\n")
    args.interfaces_output.write_text(json.dumps(interfaces, indent=2) + "\n")


if __name__ == "__main__":
    main()
