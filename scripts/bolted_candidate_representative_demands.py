"""Extract non-transferable archived demand envelopes for three prototype joints."""

import argparse
import hashlib
import json
from pathlib import Path

from mini_moonboard import compact_floor_flush_frame as current

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "docs/floor-runner-mvp-angle-demands.json"
STATIONS = (
    "clip_horizontal_bottom_left_2",
    "clip_split_base_center_left",
    "clip_angle_base_left",
)


def report() -> dict[str, object]:
    """Preserve each peak's own case; never combine independent peak loads."""
    archive = json.loads(SOURCE.read_text())
    cases = archive["case_order"]
    if len(cases) != 6 or set(cases) != set(archive["cases"]):
        raise ValueError("archived six-case envelope is incomplete")
    current_stations = {station[0]: station[1] for station in current.stations()}
    stations = {}
    for name in STATIONS:
        records = [(case, archive["cases"][case]["angles"][name]) for case in cases]
        old = archive["cases"][cases[0]]["native_station_geometry"][name]["origin"]
        now = current_stations[name].toTuple()
        if any(archive["cases"][case]["native_station_geometry"][name]["origin"] != old
               for case in cases):
            raise ValueError(f"inconsistent archived station geometry: {name}")
        flanges = {}
        for flange in ("beam", "upright"):
            force_case, force_record = max(records,
                key=lambda item: item[1]["flanges"][flange]["force_norm_n"])
            moment_case, moment_record = max(records,
                key=lambda item: item[1]["flanges"][flange]["moment_norm_nmm"])
            flanges[flange] = {
                "maximum_force_norm_n": force_record["flanges"][flange]["force_norm_n"],
                "force_case": force_case,
                "force_xyz_n_at_own_peak": force_record["flanges"][flange]["force_xyz_n"],
                "maximum_moment_norm_nmm": moment_record["flanges"][flange]["moment_norm_nmm"],
                "moment_case": moment_case,
                "moment_xyz_nmm_at_own_peak": moment_record["flanges"][flange]["moment_xyz_nmm"],
            }
        stations[name] = {
            "archived_origin_xyz_mm": old,
            "current_origin_xyz_mm": list(now),
            "geometry_reconciled": all(abs(a - b) < 1e-6 for a, b in zip(old, now, strict=True)),
            "archived_to_current_y_shift_mm": round(now[1] - old[1], 4),
            "flanges": flanges,
        }
    return {
        "status": "historical_screen_only",
        "source": str(SOURCE.relative_to(ROOT)),
        "source_sha256": hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
        "case_order": cases,
        "case_count": len(cases),
        "capacity_adopted": False,
        "new_candidate_native_loads_available": False,
        "stations": stations,
        "limit": "Old forces and moments are not simultaneous peaks, not current-center geometry, and not new-candidate demands.",
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.output.write_text(json.dumps(report(), indent=2) + "\n")


if __name__ == "__main__":
    main()
