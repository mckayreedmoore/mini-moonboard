"""Source-bound ideal N/V/M/T diagnostics for the saved 62-body A12 field.

Use the unchanged old field and signed flange point actions. Do not construct
a current common-shaft receipt or infer actual angle or joint capacity.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import sys
from pathlib import Path

import numpy as np

from scripts import thin_bolted_flange_torsion as torsion
from scripts import thin_bolted_steel_resistance as steel
from scripts.thin_bolted_finished_support_audit import audit_finished_state

ROOT = steel.ROOT
OLD_REPORT = steel.PACKET / "steel-demands-a12-rear-finished-floor-v4.json"
OLD_FIELD = steel.PACKET / "compatible-frame-a12-rear-finished-floor-v4.json"
TORSION_METHOD = steel.PACKET / "flange-torsion-method-v4.json"
GUARD_TESTS = ROOT / "tests/test_thin_bolted_saved_flange_torsion.py"
EXPECTED = {
    str(OLD_REPORT.relative_to(ROOT)): "f19a645475b139db110679414fa95022560198bd7cba6672d3a08d9d83e02f5f",
    str(OLD_FIELD.relative_to(ROOT)): "8d90941f9d1cb20d938ddc65992b2db7b0fe0c38420bf6bfc10fc0684281256d",
    str(steel.LAYOUT.relative_to(ROOT)): steel.LAYOUT_SHA,
    "scripts/thin_bolted_steel_resistance.py": "5a41c7d4a46bf1857e4c756fb35c12cc4253d2fd74f49de01a95c275a8c80602",
    "scripts/thin_bolted_flange_torsion.py": "48e3181f65772cb2d21be6687a011eaeba6a35491b6299cd179759f66ffc6871",
    str(TORSION_METHOD.relative_to(ROOT)): "5cd68b0b712495deda57478b7c3d3c8f7838851453923c7e1374f65ce826635c",
}
SCENARIOS = ("gross_filled_rectangle", "unperforated_gross_only", "two_ligament_equal_twist_proxy")


def require(condition, message):
    if not condition:
        raise ValueError(message)


def canonical_sha(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest()


def gather_pins(value, pins, counts):
    if isinstance(value, dict):
        for key, child in value.items():
            if "sha256" in key and isinstance(child, dict):
                for relative, expected in child.items():
                    if isinstance(expected, str) and len(expected) == 64 and ("/" in relative or "." in relative):
                        if relative in pins and pins[relative] != expected:
                            raise ValueError("contradictory source pin: " + relative)
                        pins[relative] = expected
                        counts[0] += 1
            gather_pins(child, pins, counts)
    elif isinstance(value, list):
        for child in value:
            gather_pins(child, pins, counts)


def verify_pins(pins):
    observed = {relative: steel.sha(ROOT / relative) for relative in pins}
    for relative, expected in pins.items():
        if observed[relative] != expected:
            raise ValueError("frozen input changed: " + relative)
    return observed


def point_actions_from_field(field):
    # ponytail: exact source projection only; this creates no foreign admission receipt.
    grouped = {}
    for table in ("attachment_actions", "flange_contact_actions"):
        for row in field[table]:
            require(all(row.get(key) == field[key] for key in ("state_id", "case_id", "accessory_placement")), "source actions mix states or cases")
            key = (row["angle_id"], row["flange"])
            point = steel.vector(row["point_xyz_mm"], "source load point").tolist()
            force = steel.vector(row["force_on_receiver_xyz_n"], "source receiver force")
            moment = steel.vector(row["moment_on_receiver_at_point_xyz_nmm"], "source receiver moment")
            grouped.setdefault(key, []).append({
                "point_xyz_mm": point,
                "force_on_steel_xyz_n": (-force).tolist(),
                "moment_on_steel_at_point_xyz_nmm": (-moment).tolist(),
            })
    require(len(field["attachment_actions"]) == 72 and len(field["flange_contact_actions"]) == 288, "complete72 attachment and288 contact actions required")
    return grouped


def validate_inputs(report, field, layout):
    """Validate saved shapes and actual source action identity before reduction."""
    require(report.get("schema") == "thin_bolted_finished_floor_steel_demands/v1", "old finished-floor steel report required")
    require(field.get("schema") == "thin_bolted_compatible_elastic_frame/v1", "old62-body field schema required")
    identity = {key: field[key] for key in ("case_id", "accessory_placement", "parameters", "geometry_cache_sha256")}
    require(field["state_id"] == "thin-v4-" + canonical_sha(identity)[:24] == "thin-v4-84ad844f63afddc032cf922c", "original saved parameter state required")
    require(all(report["state"][key] == field[key] for key in (*identity, "state_id")), "report identity differs from saved field")
    require(report["candidate"] == field["candidate"] == layout["candidate"], "saved candidate differs from occupied source")
    require(field["source_sha256"].get(str(steel.LAYOUT.relative_to(ROOT))) == steel.LAYOUT_SHA, "saved field must bind original occupied layout")
    require(report["independent_finished_support_and_equilibrium_audit"]["independent_finished_support_and_equilibrium_checks_pass"] is True, "old finished-support gate required")
    require(report["independent_equilibrium_and_contact_audit"]["body_count"] == 62, "old62-body source required")
    fittings = {row["angle_id"]: row for row in layout["raw_fittings"]}
    actions = point_actions_from_field(field)
    rows = report["fresh_demand_comparison"]["flange_comparisons"]
    expected_ports = {(key, flange) for key in fittings for flange in ("beam", "post")}
    require(len(rows) == len({(row["angle_id"], row["flange"]) for row in rows}) == 72, "all72 unique saved flange rows required")
    require(set(actions) == expected_ports == {(row["angle_id"], row["flange"]) for row in rows}, "saved flange census leaves original layout")
    for row in rows:
        require(all(row[key] == field[key] for key in ("case_id", "accessory_placement")), "report flange mixes cases or placements")
        require(row["external_point_actions_on_steel"] == actions[(row["angle_id"], row["flange"])], "saved flange actions differ from actual field")
    return identity, fittings, rows


def replay_cuts(fitting, row):
    """Require exact old nominal count/index and witness before extending cuts."""
    cuts = steel.flange_reference(fitting, row["flange"], row["external_point_actions_on_steel"])["sections"]
    require(len(cuts) == row["section_count"], "saved nominal section count differs")
    nominal = max(cuts, key=lambda cut: cut["nominal_first_yield_index"])
    require(nominal["nominal_first_yield_index"] == row["sampled_maximum_nominal_first_yield_index"], "saved nominal maximum replay differs")
    require(nominal == row["sampled_stress_witness"], "saved nominal same-cut witness replay differs")
    return cuts, nominal


def calculate():
    verify_pins(EXPECTED)
    report = json.loads(OLD_REPORT.read_bytes())
    field = json.loads(OLD_FIELD.read_bytes())
    layout = json.loads(steel.LAYOUT.read_bytes())
    identity, fittings, rows = validate_inputs(report, field, layout)
    pins, binding_count = {}, [0]
    for source in (report, field):
        gather_pins(source, pins, binding_count)
    original_unique = len(pins)
    original_bindings = binding_count[0]
    method = json.loads(TORSION_METHOD.read_bytes())
    require(method["schema"] == "thin_bolted_flange_torsion_method/v1", "issued ideal-rectangle method receipt required")
    gather_pins(method, pins, binding_count)
    pins.update(EXPECTED)
    pins[str(Path(__file__).resolve().relative_to(ROOT))] = steel.sha(Path(__file__))
    pins[str(GUARD_TESTS.relative_to(ROOT))] = steel.sha(GUARD_TESTS)
    before = verify_pins(pins)
    support = audit_finished_state(field)
    require(support["independent_finished_support_and_equilibrium_checks_pass"] is True, "old support/body equilibrium replay failed")
    totals = {sku: {"flange_count": 0, "cut_count": 0, "original_nominal_governing_witness": None,
                    "scenarios": {scenario: {"sample_count": 0, "flange_count": 0, "sampled_reference_exceedances": 0,
                                               "flanges_with_sampled_reference_exceedance": 0, "governing_same_cut_witness": None}
                                  for scenario in SCENARIOS}}
              for sku in ("B104ZN", "B103ZN")}
    nominal_error = 0.
    for row in rows:
        angle, flange = row["angle_id"], row["flange"]
        cuts, nominal = replay_cuts(fittings[angle], row)
        error = abs(nominal["nominal_first_yield_index"] - row["sampled_maximum_nominal_first_yield_index"])
        nominal_error = max(nominal_error, error)
        sku = angle.split("_", 1)[0]
        total = totals[sku]
        total["flange_count"] += 1
        total["cut_count"] += len(cuts)
        old_witness = {"angle_id": angle, "flange": flange, **nominal}
        previous = total["original_nominal_governing_witness"]
        if previous is None or nominal["nominal_first_yield_index"] > previous["nominal_first_yield_index"]:
            total["original_nominal_governing_witness"] = old_witness
        flange_samples = {scenario: [] for scenario in SCENARIOS}
        for cut in cuts:
            chord = max(0., steel.WIDTH - cut["area_mm2"] / steel.THICKNESS)
            common = {"width_mm": steel.WIDTH, "thickness_mm": steel.THICKNESS, "removed_center_width_mm": chord,
                      "force_local_n": cut["force_local_n"], "moment_local_nmm": cut["moment_local_nmm"], "fy_mpa": steel.FY_CATALOG}
            station = {"angle_id": angle, "flange": flange, "station_from_assumed_corner_mm": cut["station_from_assumed_corner_mm"]}
            gross = {**station, **torsion.simultaneous_section_bound(**common, scenario="gross_rectangle")}
            flange_samples["gross_filled_rectangle"].append(gross)
            if chord <= 1e-8:
                flange_samples["unperforated_gross_only"].append(gross)
            else:
                flange_samples["two_ligament_equal_twist_proxy"].append({**station,
                    **torsion.simultaneous_section_bound(**common, scenario="two_ligament_equal_twist_proxy")})
        for scenario, samples in flange_samples.items():
            summary = total["scenarios"][scenario]
            require(bool(samples), "missing declared flange scenario samples")
            maximum = max(samples, key=lambda cut: cut["simultaneous_nominal_first_yield_bound_index"])
            exceedances = sum(cut["simultaneous_nominal_first_yield_bound_index"] > 1. for cut in samples)
            summary["sample_count"] += len(samples)
            summary["flange_count"] += 1
            summary["sampled_reference_exceedances"] += exceedances
            summary["flanges_with_sampled_reference_exceedance"] += bool(exceedances)
            previous = summary["governing_same_cut_witness"]
            if previous is None or maximum["simultaneous_nominal_first_yield_bound_index"] > previous["simultaneous_nominal_first_yield_bound_index"]:
                summary["governing_same_cut_witness"] = maximum
    require(sum(row["cut_count"] for row in totals.values()) == 18474, "saved18474-cut denominator differs")
    require(totals["B104ZN"]["flange_count"] == 48 and totals["B103ZN"]["flange_count"] == 24, "saved SKU flange census differs")
    after = verify_pins(pins)
    require(before == after, "source bindings changed during reduction")
    return {
        "schema": "thin_bolted_saved_scope_flange_torsion/v1", "status": "OLD_62_BODY_SAVED_FIELD_IDEAL_SECTION_DIAGNOSTICS_ONLY",
        "candidate": field["candidate"], "state_id": field["state_id"], "case_id": field["case_id"], "accessory_placement": field["accessory_placement"],
        "source_sha256": EXPECTED | {str(Path(__file__).resolve().relative_to(ROOT)): steel.sha(Path(__file__)),
            str(GUARD_TESTS.relative_to(ROOT)): steel.sha(GUARD_TESTS)},
        "input_proof": {
            "old_report_raw_sha256": steel.sha(OLD_REPORT), "old_report_canonical_sha256": canonical_sha(report),
            "old_field_raw_sha256": steel.sha(OLD_FIELD), "old_field_canonical_sha256": canonical_sha(field),
            "state_identity_canonical_sha256": canonical_sha(identity), "bound_pin_table_entries": binding_count[0],
            "original_field_and_steel_report_bound_pin_entries": original_bindings,
            "original_unique_bound_paths": original_unique, "verified_unique_paths_including_method_and_self": len(pins),
            "all_bound_pins_verified_before_and_after": True, "verified_pin_map_canonical_sha256": canonical_sha(pins),
            "saved_external_point_actions_exactly_reconstructed_from_field": True,
            "saved_nominal_comparison_max_absolute_replay_error": nominal_error,
            "all72_nominal_counts_indices_and_same_cut_witnesses_replay_exactly": True,
            "original_schema_and_state_retained": True,
        },
        "existing_support_gate_replay": {"independent_finished_support_and_equilibrium_checks_pass": True,
            "body_count": support["equilibrium"]["body_count"], "finished_host_count": support["support"]["finished_host_count"],
            "normal_port_count": support["support"]["normal_port_count"], "tangent_port_count": support["support"]["tangent_port_count"]},
        "tools": {"python": platform.python_version(), "numpy": np.__version__, "platform": platform.platform(),
                  "python_executable": sys.executable, "uv_lock_sha256": steel.sha(ROOT / "uv.lock")},
        "reproduction_command": "OPENBLAS_NUM_THREADS=1 .venv/bin/python -m scripts.thin_bolted_saved_flange_torsion --out docs/wood-joints-mvp/hypotheses/hl35-candidate/thin-frame-comparison/saved-flange-torsion-a12-rear-v4.json",
        "method": {"cut_recovery_api": "scripts.thin_bolted_steel_resistance.flange_reference",
            "section_bound_api": "scripts.thin_bolted_flange_torsion.simultaneous_section_bound",
            "series_terms": 64, "bound_formula": "VM <= hypot(sigma_N_M_envelope, sqrt(3)*(tau_V_envelope + abs(T)*t/J_lower))",
            "unperforated_selection_removed_chord_tolerance_mm": 1e-8, "specified_fy_mpa_scenario": steel.FY_CATALOG,
            "reused_method_receipt": str(TORSION_METHOD.relative_to(ROOT)),
            "reused_method_fixture_count": method["validation"]["fixtures_passed"],
            "unchanged_rectangle_method_fixtures_rerun": False,
            "new_guard_test_command": "OPENBLAS_NUM_THREADS=1 .venv/bin/pytest -q tests/test_thin_bolted_saved_flange_torsion.py"},
        "counts": {"flanges": 72, "sampled_cut_stations": 18474}, "sku_results": totals,
        "limits": [
            "Every witness retains simultaneous signed N,V1,V2,T,M1,M2 from one saved cut; component envelope maxima need not coincide spatially.",
            "Filled-gross rectangles replace openings with steel; unperforated-gross selects zero-removed-chord cuts only; neither is an actual perforated-angle strength bound.",
            "The two-ligament proxy assumes two freely warping prismatic rectangles at equal twist, with the frozen nominal transverse-shear allocation. Actual hole sharing and concentrations are unqualified.",
            "Sampled station extrema are not continuous extrema. Actual flat-start/heel geometry, short-leg restrained warping, bimoment, bend and load-introduction effects remain open.",
            "Original contact/prying, spring allocation, bolt own-end/shaft behavior, product dimensions/tolerances/thickness/material conformance and complete failure paths remain unqualified.",
            "The old 62-body field, its floor allocation and these indices do not transfer to the changed 132-body model or establish complete fitting/joint capacity.",
        ],
        "full_sample_export_written": False, "native_or_CAD_execution": False, "K_assembly_or_candidate_solve": False,
        "geometry_changed": False, "current_132_body_force_field_admitted": False, "complete_joint_acceptance": False,
        "fabrication_release": False, "climbing_release": False,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    if args.out.exists():
        raise FileExistsError("preserve the saved replay result")
    result = calculate()
    result["execution_command_argv"] = sys.orig_argv
    result["execution_environment"] = {"OPENBLAS_NUM_THREADS": os.environ.get("OPENBLAS_NUM_THREADS")}
    args.out.write_text(json.dumps(result, indent=2, allow_nan=False) + "\n")
    print(json.dumps({"output": str(args.out), "bytes": args.out.stat().st_size,
        "sku_maxima": {sku: {scenario: value["governing_same_cut_witness"]["simultaneous_nominal_first_yield_bound_index"]
                            for scenario, value in row["scenarios"].items()} for sku, row in result["sku_results"].items()},
        "input_proof": result["input_proof"]}, indent=2))


if __name__ == "__main__":
    main()
