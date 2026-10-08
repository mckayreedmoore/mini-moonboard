"""Independent source/count/cost audit; no geometry or mechanics execution."""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import os
import platform
import sys
from collections import Counter
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
OWN = Path(__file__).resolve()
LOADED_SHA = hashlib.sha256(OWN.read_bytes()).hexdigest()
PACKET = OWN.parent
BASE = "docs/wood-joints-mvp/hypotheses/hl35-candidate/thin-frame-comparison"
INPUTS = {
    f"{BASE}/eoere-successor-v1/owner-stations.json": "f7bd4c803ac149f927d85163a0a9ca2d52eff95abf9901f2c462faa54296ebe5",
    f"{BASE}/eoere-successor-v1/product-inputs-final.json": "dd662e681871576d0a76666e9370d4359f7e96e0a2ad5f9710553895f53a5309",
    "fea/generated/thin-bolted-build-planning-v4/joined-shop-data-final.json": "7982d8612014d6d55279f7847798ea3bf87e6c2eca2fa585ef4457daf3787074",
    f"{BASE}/build-planning-v4/manifest.json": "13a24c62ed4e51f63961096858b0e61b727d01c24ce90e0a7ef2c29cf985777a",
    f"{BASE}/access-takeoff-v4.json": "0c5a09879c9b191c39b96ce670d71ad110661bff7dfeab68133f711b32de476c",
    "fea/generated/thin-bolted-build-planning-v4/price-observations.json": "fa2cbf1008c2454154f5cd7bb9a2885d8f602b3320a85b951fd92902fa6209aa",
}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def merge_pins(pins: dict[str, str], additions: dict[str, str]) -> None:
    for path, expected in additions.items():
        require(path not in pins or pins[path] == expected, f"conflicting pin: {path}")
        pins[path] = expected


def verify(pins: dict[str, str]) -> None:
    for path, expected in pins.items():
        require(sha(ROOT / path) == expected, f"changed source: {path}")


def evaluate() -> dict:
    pins = dict(INPUTS)
    merge_pins(pins, {str(OWN.relative_to(ROOT)): LOADED_SHA})
    question_path = PACKET / "question.json"
    merge_pins(pins, {str(question_path.relative_to(ROOT)): sha(question_path)})
    verify(pins)
    station, product, joined, manifest, access, prices = (
        json.loads((ROOT / path).read_text()) for path in INPUTS
    )
    question = json.loads(question_path.read_text())
    for source in (joined, access, product):
        merge_pins(pins, source.get("source_sha256", {}))
    table_checks = []
    for name, metadata in manifest["files"].items():
        path = f"{BASE}/build-planning-v4/{name}"
        merge_pins(pins, {path: metadata["sha256"]})
        raw = (ROOT / path).read_bytes()
        require(hashlib.sha256(raw).hexdigest() == metadata["sha256"], path)
        reader = csv.DictReader(io.StringIO(raw.decode()))
        require(reader.fieldnames == metadata["columns"], f"columns: {name}")
        rows = list(reader)
        require(len(rows) == metadata["row_count"], f"rows: {name}")
        require(all(r["Actual"] == r["Disposition"] == "" for r in rows), name)
        if name == "source-sha256.csv":
            merge_pins(pins, {r["source_path"]: r["sha256"] for r in rows})
        table_checks.append({"table": name, "rows": len(rows), "actual_disposition_blank_cells": 2 * len(rows)})
    verify(pins)
    duties = {s["duty_id"] for s in station["main_stations"]}
    require(len(duties) == station["main_station_count"] == 16, "main station count")
    main_fittings = [f for f in joined["fittings"] if f[1] in duties]
    fitting_ids = {f[0] for f in main_fittings}
    holes = [r for r in joined["fitting_hole_rows"] if r[1] in fitting_ids]
    shafts = sorted({r[0] for r in holes})
    fitting_types = dict(Counter(f[0].split("_")[0] for f in main_fittings))
    require(fitting_types == {"B104ZN": 16, "B103ZN": 12}, "predecessor main fitting census")
    require(len(holes) == 56 and len(shafts) == 44, "predecessor main hole/shaft census")
    starting = [a["axis_id"] for a in joined["axes"] if a["source"] == "original_starting_frame_axis"]
    require(len(starting) == 12, "starting shaft census")
    require(len(joined["Hillman_axes"]) == 66 and len(joined["members"]) == 20, "reuse input census")
    require(len(station["remaining_base_header_starting_stations"]) == 8, "starting base/header duties")
    D = Decimal
    mass_each = D("1.46") * D(product["unit_constants"]["kg_per_pound_exact"])
    old_mass = access["takeoff"]["mass"]
    old_angles = sum(D(str(line["cost_usd"])) for line in prices["angles"])
    require(old_angles == D("177.00"), "old angle snapshot")
    scenarios = []
    for count in [16, *question["owner_updates_after_station_handoff"]["illustrative_total_angle_counts"]]:
        packs = (count + 3) // 4
        installed_mass = D(count) * mass_each
        scenarios.append({
            "installed_angle_count_scenario": count,
            "final_quantity": False,
            "active_hole_attachments_before_coincidences": 4 * count,
            "factory_holes_retained": 8 * count,
            "four_packs": packs,
            "purchased_pieces": 4 * packs,
            "spare_angle_pieces": 4 * packs - count,
            "installed_drawing_mass_lb": str(D(count) * D("1.46")),
            "installed_drawing_mass_kg": str(installed_mass),
            "purchased_drawing_mass_kg_excluding_packaging": str(D(4 * packs) * mass_each),
            "angle_pack_cost_usd": None,
            "angle_pack_cost_formula": f"{packs}*C4 + shipping + tax; C4 unknown",
            "same_angle_only_snapshot_cost_at_C4_usd": str(old_angles / D(packs)),
            "installed_angle_only_mass_change_from_old_range_kg": [
                str(installed_mass - D(str(old_mass["angle_mass_kg_catalog_upper"]))),
                str(installed_mass - D(str(old_mass["angle_mass_kg_SKU_lower"]))),
            ],
            "unique_physical_shafts": None,
        })
    result = {
        "schema": "eoere_successor_reuse_cost_assembly_dependency_audit/v1",
        "question": question,
        "predecessor_source_census": joined["counts"],
        "main_replacement": {"duties": sorted(duties), "old_fitting_types": fitting_types,
                             "old_fitting_hole_ownerships": len(holes), "old_distinct_main_shafts": len(shafts),
                             "old_main_shafts": shafts, "new_main_angles": 16,
                             "new_main_active_hole_attachments_before_coincidences": 64,
                             "opposite_B103_retained": False},
        "starting_axes_preserve_and_recheck": starting,
        "successor_physical_shaft_count_contract": "Resolve 4*N active angle holes into physical axes, join/recheck 12 starting shafts and add any block/cleat-only bolts. No default sharing or 4*N+12 adoption.",
        "table_checks": table_checks,
        "table_count": len(table_checks),
        "table_row_count": sum(t["rows"] for t in table_checks),
        "blank_actual_disposition_cells": sum(t["actual_disposition_blank_cells"] for t in table_checks),
        "angle_count_cost_mass_scenarios": scenarios,
        "comparison_limits": {
            "old_angle_only_cost_usd": str(old_angles),
            "old_price_snapshot_america_denver": prices["observed_date_america_denver"],
            "old_partial_hardware_usd": prices["known_partial_hardware_comparison_usd"],
            "old_whole_board_conditional_mass_range_kg": old_mass["dead_mass_with_original_25kg_accessory_allowance_range"],
            "new_total_cost_or_mass": None,
            "reason": "New hardware dimensions/quantities, changed bore volumes and four new wood pieces are unresolved. Substituting angle price/mass into the old partial/whole-board totals is invalid.",
            "old_nominal_stock_board_feet": access["takeoff"]["stock"]["nominal_board_feet"],
            "tightest_old_stock_remainder_mm": joined["dimensional_issues"]["tightest_nominal_stock_remainder_mm"],
            "four_new_pieces_fit_old_offcuts": None,
            "steel_yield_grade_or_heel_geometry_adopted": False,
        },
        "source_sha256": pins,
        "source_pin_count": len(pins),
        "before_after_source_authentication_pass": True,
        "execution": {"sys_argv": list(sys.argv), "sys_orig_argv": list(sys.orig_argv),
                      "python": platform.python_version(), "executable": sys.executable,
                      "PYTHONPATH": os.environ.get("PYTHONPATH"), "dependencies": "stdlib only"},
        "scope": {"new_geometry_or_BREP_consumed": False, "CAD_or_native_query": False,
                  "K_or_response_solve": False, "old_or_new_force_field_consumed": False,
                  "old_admission_or_capacity_transferred": False},
    }
    verify(pins)
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", required=True, type=Path)
    options = parser.parse_args()
    require(not options.out.exists(), "preserve existing audit output")
    result = evaluate()
    with options.out.open("x") as handle:
        json.dump(result, handle, indent=2, sort_keys=True)
        handle.write("\n")
    print(json.dumps({"path": str(options.out), "sha256": sha(options.out),
                      "bytes": options.out.stat().st_size, "source_pin_count": result["source_pin_count"],
                      "tables": result["table_count"], "rows": result["table_row_count"]}))


if __name__ == "__main__":
    main()
