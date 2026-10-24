"""Reduce the current v6 strength worksheets without running mechanics.

The report keeps conditional reference comparisons separate from geometry
eligibility and complete-frame acceptance. Run only after all six fields and
worksheets exist, with a fresh ignored RAW output path:

    python -m scripts.eoere_v6_report --out fea/generated/.../review-v1.json
"""

from __future__ import annotations

import argparse
import copy
import csv
import hashlib
import itertools
import json
import math
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
WORK = ROOT / "fea/generated/thin-bolted-current-contact-v1/eoere-successor-v1/single-leg-header-integration-v1/coherent-return-paired-foot-v1/frame-completion-v1"
BASE = WORK / "owner-principal-pairs-v6/analysis-v1"
RUN = BASE / "four-hosts"
REVIEW = BASE / "review"
COMPLETE = REVIEW / "complete-v1"
PHYSICAL_GEOMETRY = WORK / "owner-principal-pairs-v6/geometry/geometry.json"
GEOMETRY_RECEIPT = ROOT / "docs/bolted-frame-development/owner-frame-v6/geometry.json"
ANALYSIS_GEOMETRY = BASE / "geometry/geometry.json"
MATERIAL = BASE / "material.json"
INPUTS = RUN / "preparation/inputs.json"
READINESS = BASE / "readiness.json"
ANALYSIS_PRODUCER = ROOT / "scripts/eoere_v6_analysis.py"
CHECKS_PRODUCER = ROOT / "scripts/eoere_v6_checks.py"
ROW_PRODUCER = ROOT / "scripts/eoere_requested_cleat_screen.py"
REPORT_PRODUCER = Path(__file__).resolve()
HARDWARE = ROOT / "docs/wood-joints-mvp/hypotheses/hl35-candidate/thin-frame-comparison/eoere-successor-v1/leg-header-v3/hardware-selection.csv"

CASE_IDS = ("a12-forward", "a12-left", "a12-rear", "k12-right", "k12-rear", "a1-rear")
DEDICATED = {
    *(f"eoere_bolt_{n:03d}" for n in (67, 70, 71, 74, 81, 82, 83, 84)),
    *(f"cleat_post_bolt_{side}_{n}" for side in ("left", "right") for n in (1, 2)),
}

SHAFT_METRICS = {
    "maximum_bearing_index_before_Cdelta": "bearing_reference_index_after_Cdelta",
    "maximum_N_M_index_before_Cdelta": "axial_bending_reference_index_after_Cdelta",
    "maximum_N_M_V_index_before_Cdelta": "axial_bending_shear_reference_index_after_Cdelta",
}
TIMBER_METRICS = (
    "maximum_normal_reference_upper",
    "maximum_shear_torsion_reference_upper",
    "maximum_declared_restraint_normal_reference_upper",
)
PLYWOOD_METRICS = (
    "balanced_pressure_reference_index",
    "minimum_scalar_pressure_reference_index",
    "integrated_force_only_reference_index",
)
LOWER_BOUND_PLYWOOD = {"minimum_scalar_pressure_reference_index", "integrated_force_only_reference_index"}

WORKSHEET_PATHS = {
    "shaft_geometry_Cdelta_adjusted": COMPLETE / "shaft-geometry-adjustments-v3.json",
    "shaft_bearing_statics_Cg_adjusted": COMPLETE / "shaft-bearing-blocks-v1.json",
    "timber_sections": COMPLETE / "timber-sections-v1.json",
    "nominal_38p1_plywood_groups": REVIEW / "nominal38p1-rows-v1.json",
    "credited_36p5_plywood_groups": REVIEW / "bonded-rows-v1.json",
}

HASH_CACHE: dict[str, str] = {}


def rel(path: Path) -> str:
    return path.resolve().relative_to(ROOT).as_posix()


def read_json(path: Path) -> tuple[dict[str, Any], dict[str, str]]:
    raw = path.read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    HASH_CACHE[str(path.resolve())] = digest
    return json.loads(raw), {"path": rel(path), "sha256": digest}


def digest(path: Path) -> str:
    key = str(path.resolve())
    if key not in HASH_CACHE:
        HASH_CACHE[key] = hashlib.sha256(path.read_bytes()).hexdigest()
    return HASH_CACHE[key]


def resolve_ref(value: dict[str, Any], label: str) -> tuple[Path, dict[str, str]]:
    if not isinstance(value, dict) or not isinstance(value.get("path"), str) or not isinstance(value.get("sha256"), str):
        raise TypeError(f"{label}: expected path and sha256 reference")
    given = Path(value["path"])
    path = given if given.is_absolute() else ROOT / given
    actual = digest(path)
    if actual != value["sha256"]:
        raise ValueError(f"{label}: SHA-256 mismatch for {value['path']}")
    return path, {"path": rel(path), "sha256": actual}


def verify_pin(doc: dict[str, Any], path: Path, label: str, *, required: bool = True) -> dict[str, str] | None:
    pins = doc.get("source_sha256", {})
    key = rel(path)
    expected = pins.get(key)
    if expected is None:
        if required:
            raise ValueError(f"{label}: missing active source pin {key}")
        return None
    actual = digest(path)
    if actual != expected:
        raise ValueError(f"{label}: active source pin changed for {key}")
    return {"path": key, "sha256": actual}


def finite(value: Any, label: str) -> float:
    result = float(value)
    if not math.isfinite(result):
        raise ValueError(f"{label}: non-finite value")
    return result


def close(a: Any, b: Any, label: str, *, rel_tol: float = 1e-9, abs_tol: float = 1e-9) -> None:
    if not math.isclose(finite(a, label), finite(b, label), rel_tol=rel_tol, abs_tol=abs_tol):
        raise ValueError(f"{label}: {a!r} != {b!r}")


def ref_record(path: Path) -> dict[str, str]:
    return {"path": rel(path), "sha256": digest(path)}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def load_field(case_id: str) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any]]:
    folder = RUN / case_id
    field, field_ref = read_json(folder / "field.json")
    replay, replay_file_ref = read_json(folder / "independent-replay.json")
    plywood, plywood_file_ref = read_json(folder / "independent-replay-plywood.json")
    require(field.get("case_id") == case_id, f"{case_id}: field case id mismatch")
    require(field.get("disposition", "").startswith("CONVERGED_"), f"{case_id}: field is not converged")
    require(isinstance(field.get("response"), dict) and field["response"].get("accepted_numerical_steps", 0) > 0,
            f"{case_id}: no computed own force response")
    require(field.get("native_FEA_performed") is False, f"{case_id}: unexpected native FEA flag")
    require(field.get("execution", {}).get("historical_q_used") is False,
            f"{case_id}: a historical force response was used")
    field_release = field.get("release", {})
    for key in ("candidate_accepted", "capacity_established", "climbing_released", "complete_joint_acceptance",
                "fabrication_released", "structural_released"):
        require(field_release.get(key) is False, f"{case_id}: {key} must remain false")

    parameters = field["source_inputs"]["scenario"]["climber_load_parameters"]
    require(parameters["input_weight"] == 250 and parameters["input_unit"] == "lb", f"{case_id}: load weight mismatch")
    close(parameters["downward_multiplier"], 2., f"{case_id}: downward multiplier")
    close(parameters["horizontal_force_n"], 300., f"{case_id}: horizontal load")
    require(parameters.get("standard_load_combination_or_climber_rating") is False,
            f"{case_id}: load incorrectly described as a rating")
    counts = field["counts"]
    for key, expected in (("physical_bodies", 148), ("shaft", 96), ("fitting", 24), ("panel", 6), ("timber", 22)):
        require(counts.get(key) == expected, f"{case_id}: {key} count is not {expected}")
    require(len(field.get("panel_screw_actions", [])) == 66, f"{case_id}: panel/Hillman action census changed")

    field_ref_value = field_ref
    geometry_ref = field.get("trial_parent_geometry")
    require(field.get("source_inputs", {}).get("geometry") == geometry_ref, f"{case_id}: geometry references disagree")
    resolve_ref(geometry_ref, f"{case_id} analysis geometry")
    material_ref = field["source_inputs"].get("plywood_material")
    resolve_ref(material_ref, f"{case_id} material")
    require(material_ref["path"] == rel(MATERIAL), f"{case_id}: wrong material source")
    input_ref = field.get("source_input_review", {}).get("input")
    resolve_ref(input_ref, f"{case_id} prepared inputs")
    require(input_ref["path"] == rel(INPUTS), f"{case_id}: wrong prepared-input source")
    bond = field["source_inputs"]["scenario"]["perfect_bond_analysis"]
    require(bond.get("actual_bond_qualified") is False, f"{case_id}: actual bond must remain unqualified")
    resolve_ref(bond["analysis_geometry"], f"{case_id} perfect-bond geometry")
    resolve_ref(bond["physical_parent"], f"{case_id} physical geometry parent")

    require(replay.get("field") == field_ref_value, f"{case_id}: independent replay is not bound to its field")
    require(replay.get("same_state_declared_fixed_floor_replayed") is True, f"{case_id}: floor replay missing")
    require(replay.get("false_screw_and_floor_forces_rejected") is True, f"{case_id}: false-force controls missing")
    require(replay.get("all_credited_hosts_in_bearing") is True, f"{case_id}: host bearing gate missing")
    require(replay.get("old_switching_law_pass_transferred") is False, f"{case_id}: historical pass transfer")
    require(replay.get("floor_or_bond_capacity_qualified") is False, f"{case_id}: floor/bond capacity must remain unqualified")
    require(replay.get("equilibrium", {}).get("physical_body_count") == 148, f"{case_id}: replay body census mismatch")
    require(finite(replay.get("equilibrium", {}).get("gradient_inf_n"), f"{case_id} replay gradient") < 1e-5,
            f"{case_id}: replay equilibrium check failed")
    require(plywood.get("field") == field_ref_value, f"{case_id}: plywood replay is not bound to its field")
    require(plywood.get("material") == ref_record(MATERIAL), f"{case_id}: plywood replay material mismatch")
    require(len(plywood.get("raw_operator_checks", [])) == 2, f"{case_id}: expected two bonded plywood operators")
    require(plywood.get("field_q_actions_or_operators_changed") is False, f"{case_id}: plywood replay changed field")
    require(plywood.get("physical_stiffness_qualified") is False, f"{case_id}: physical plywood stiffness must remain unqualified")
    require(plywood.get("production_admission_issued") is False, f"{case_id}: plywood replay is not production admission")

    active_paths = (ANALYSIS_PRODUCER, ROOT / "scripts/eoere_leg_header_mechanics.py", ANALYSIS_GEOMETRY, MATERIAL, INPUTS)
    active_field_pins = [verify_pin(field, path, f"{case_id} field") for path in active_paths]
    require(replay.get("producer", {}).get("path") == rel(ANALYSIS_PRODUCER), f"{case_id}: replay producer mismatch")
    resolve_ref(replay["producer"], f"{case_id} replay producer")
    require(plywood.get("source", {}).get("path") == "scripts/replay_eoere_leg_header.py", f"{case_id}: plywood replay producer mismatch")
    resolve_ref(plywood["source"], f"{case_id} plywood replay producer")
    resolve_ref(plywood.get("material"), f"{case_id} plywood replay material")
    return field, replay, plywood, {
        "field": field_ref,
        "independent_replay": replay_file_ref,
        "independent_plywood_replay": plywood_file_ref,
        "active_field_pins_verified": [pin for pin in active_field_pins if pin],
        "field_source_map_entries": len(field.get("source_sha256", {})),
        "inherited_source_closure_verified_at_preparation": field.get("source_input_review", {}).get("source_closure_verified") is True,
    }


def load_worksheet(name: str, path: Path) -> tuple[dict[str, Any], dict[str, str]]:
    data, artifact_ref = read_json(path)
    if "release" in data:
        require(data["release"] is False, f"{name}: release flag must remain false")
    if "structural_acceptance" in data:
        require(data["structural_acceptance"] is False, f"{name}: structural acceptance flag must remain false")
    elif path.parent == COMPLETE:
        raise ValueError(f"{name}: missing structural acceptance flag")
    if "old_force_pass_transferred" in data:
        require(data["old_force_pass_transferred"] is False, f"{name}: historical force-pass transfer flag must remain false")
    elif path.parent == COMPLETE:
        raise ValueError(f"{name}: missing historical force-pass transfer flag")
    require(data.get("duration_factor_CD") == 1., f"{name}: worksheet must explicitly use CD=1")
    if path.parent == COMPLETE:
        for active in (ANALYSIS_PRODUCER, CHECKS_PRODUCER, ANALYSIS_GEOMETRY, MATERIAL, INPUTS):
            verify_pin(data, active, name)
    return data, artifact_ref


def by_case(data: dict[str, Any], label: str, expected: set[str]) -> dict[str, dict[str, Any]]:
    cases = data.get("cases")
    require(isinstance(cases, list), f"{label}: missing case rows")
    mapped = {row["case_id"]: row for row in cases}
    require(len(mapped) == len(cases) and set(mapped) == expected, f"{label}: expected exactly six own cases")
    return mapped


def unsupported_oblique_axes(field: dict[str, Any]) -> list[dict[str, Any]]:
    profiles = {r["name"]: r.get("raw_profile_source") for r in field["source_inputs"]["timber_rows"]}
    result = []
    for shaft in field["source_inputs"]["shafts"]:
        axis = shaft["basis"][0]
        for surface in shaft["surfaces"]:
            if surface.get("kind") != "wood":
                continue
            profile = profiles.get(surface["host"])
            frame = profile.get("basis_grain_u_v_xyz") if profile else None
            if not frame:
                result.append({"axis_id": shaft["axis_id"], "host": surface["host"], "reason": "missing grain frame"})
                continue
            local = [sum(frame[i][j] * axis[j] for j in range(3)) for i in range(3)]
            aligned = abs(local[0]) < 1e-8 and (
                abs(abs(local[1]) - 1.) < 1e-8 and abs(local[2]) < 1e-8
                or abs(abs(local[2]) - 1.) < 1e-8 and abs(local[1]) < 1e-8
            )
            if not aligned:
                result.append({"axis_id": shaft["axis_id"], "host": surface["host"],
                               "local_LUV_axis": local, "reason": "worksheet supports only grain-orthogonal U/V axes"})
    return result


def axis_geometry_state(case: dict[str, Any], axis_id: str) -> dict[str, Any]:
    surfaces = [s for s in case.get("surfaces", []) if s.get("axis_id") == axis_id]
    pairs = [p for p in case.get("receiver_pairs", []) if axis_id in p.get("axes", [])]
    bad_surfaces = []
    for surface in surfaces:
        if surface.get("end_edge_eligible") is True and surface.get("centered_four_diameter_equivalent_width_eligible") is True:
            continue
        failed_directions = [d for d in surface.get("pressure_directions", []) if d.get("eligible") is not True]
        edges = surface.get("crossgrain_edge_distances_mm") or []
        minimum = min(edges) if edges else None
        reasons = []
        if surface.get("end_edge_eligible") is not True:
            reasons.append("one or more signed end/edge pressure directions fail a minimum")
        if surface.get("centered_four_diameter_equivalent_width_eligible") is not True:
            reasons.append("centered four-diameter equivalent width fails")
        bad_surfaces.append({
            "axis_id": axis_id, "host": surface.get("host"),
            "end_edge_eligible": surface.get("end_edge_eligible"),
            "centered_four_diameter_equivalent_width_eligible": surface.get("centered_four_diameter_equivalent_width_eligible"),
            "grain_end_distances_mm": surface.get("grain_end_distances_mm"),
            "crossgrain_edge_distances_mm": surface.get("crossgrain_edge_distances_mm"),
            "diameter_mm": surface.get("diameter_mm"),
            "centered_width_required_mm": 2 * surface.get("diameter_mm", 0),
            "minimum_crossgrain_edge_distance_mm": minimum,
            "failed_pressure_directions": failed_directions, "reasons": reasons,
        })
    bad_pairs = []
    for pair in pairs:
        if pair.get("eligible") is True:
            continue
        reasons = [key for key in ("parallel_direction_eligible", "perpendicular_direction_eligible",
                                    "edge_for_long_penetration_eligible") if pair.get(key) is not True]
        separation = pair.get("grain_cross_separations_mm") or []
        if len(separation) > 1 and separation[1] > 127. + 1e-5:
            reasons.append("maximum row spacing exceeds 127 mm")
        bad_pairs.append({**pair, "reasons": reasons})
    missing = not surfaces
    eligible = bool(surfaces) and not bad_surfaces and not bad_pairs
    return {"eligible": eligible, "surfaces_found": len(surfaces), "receiver_pairs_found": len(pairs),
            "ineligible_surfaces": bad_surfaces, "ineligible_pairs": bad_pairs,
            "reason": "no wood-bearing geometry row" if missing else None}


def check_adjusted_shafts(adjusted: dict[str, Any], statics: dict[str, Any], expected_ids: set[str],
                          fields: dict[str, dict[str, Any]], unsupported: dict[str, list[dict[str, Any]]]
                          ) -> tuple[dict[tuple[str, str], dict[str, Any]], dict[tuple[str, str], dict[str, Any]]]:
    require(adjusted.get("all6_cases_checked") is True, "shaft geometry worksheet does not attest six-case coverage")
    for data, label in ((adjusted, "adjusted shaft geometry"), (statics, "shaft bearing statics")):
        require(data.get("current_case_count") == 6 and data.get("current_bolt_count") == 96,
                f"{label}: current inventory receipt mismatch")
        require(data.get("current_dedicated_bolt_count") == 12, f"{label}: dedicated inventory receipt mismatch")
    adj_cases, raw_cases = by_case(adjusted, "shaft geometry", set(CASE_IDS)), by_case(statics, "shaft statics", set(CASE_IDS))
    eligibility: dict[tuple[str, str], dict[str, Any]] = {}
    rows: dict[tuple[str, str], dict[str, Any]] = {}
    for case_id in CASE_IDS:
        adj_case, raw_case = adj_cases[case_id], raw_cases[case_id]
        require(adj_case.get("field") == raw_case.get("field"), f"{case_id}: geometry/statics field refs differ")
        require(isinstance(adj_case.get("all_geometry_eligible"), bool), f"{case_id}: missing geometry eligibility flag")
        adj_rows = {r["axis_id"]: r for r in adj_case.get("shafts", [])}
        raw_rows = {r["axis_id"]: r for r in raw_case.get("shafts", [])}
        require(len(adj_rows) == 96 and set(adj_rows) == expected_ids, f"{case_id}: adjusted shaft census mismatch")
        require(len(raw_rows) == 96 and set(raw_rows) == expected_ids, f"{case_id}: statics shaft census mismatch")
        source_ref = adj_case["field"]
        require(source_ref == ref_record(RUN / case_id / "field.json"), f"{case_id}: geometry sheet field binding mismatch")
        require(raw_case.get("field") == source_ref, f"{case_id}: statics field binding mismatch")
        for axis_id in sorted(expected_ids):
            adj_row, raw_row = adj_rows[axis_id], raw_rows[axis_id]
            factor = finite(adj_row.get("Cdelta"), f"{case_id}/{axis_id} Cdelta")
            require(0. < factor <= 1., f"{case_id}/{axis_id}: invalid Cdelta")
            cg = finite(raw_row.get("bounded_Cg"), f"{case_id}/{axis_id} Cg")
            require(0.5 <= cg <= 1., f"{case_id}/{axis_id}: Cg outside the declared 0.5..1.0 range")
            if axis_id in DEDICATED:
                close(cg, 0.5, f"{case_id}/{axis_id} dedicated n<=2 Cg")
            for source_metric in SHAFT_METRICS:
                expected = finite(raw_row.get(source_metric), f"{case_id}/{axis_id}/{source_metric}") / factor
                close(adj_row.get(source_metric), expected, f"{case_id}/{axis_id}/{source_metric} Cdelta adjustment", rel_tol=2e-8, abs_tol=1e-10)
            state = axis_geometry_state(adj_case, axis_id)
            relevant_oblique = [v for v in unsupported[case_id] if v["axis_id"] == axis_id]
            if relevant_oblique:
                state["eligible"] = False
                state["unsupported_oblique_cases"] = relevant_oblique
            eligibility[(case_id, axis_id)] = state
            rows[case_id, axis_id] = {**adj_row, "bounded_Cg": cg}
        expected_eligible = all(eligibility[(case_id, axis_id)]["eligible"] for axis_id in expected_ids)
        if not unsupported[case_id]:
            require(adj_case.get("all_geometry_eligible") is expected_eligible,
                    f"{case_id}: aggregate geometry eligibility disagrees with axis/pair rows")
    return rows, eligibility


def max_item(entries: list[dict[str, Any]], value_key: str = "index") -> dict[str, Any]:
    require(bool(entries), "cannot take maximum of empty metric population")
    return max(entries, key=lambda row: finite(row[value_key], value_key))


def shaft_item(case_id: str, row: dict[str, Any], metric: str, state: dict[str, Any]) -> dict[str, Any]:
    axis_id = row["axis_id"]
    result = {"case_id": case_id, "axis_id": axis_id, "population": "dedicated_12" if axis_id in DEDICATED else "ordinary_84",
              "index": finite(row[metric], metric), "geometry_eligible": state["eligible"],
              "geometry_status": "eligible_reference_only" if state["eligible"] else "geometry_ineligible_no_pass"}
    if "Cdelta" in row:
        result["Cdelta"] = row["Cdelta"]
    return result


def summarize_shafts(rows: dict[tuple[str, str], dict[str, Any]], eligibility: dict[tuple[str, str], dict[str, Any]]) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    maxima: dict[str, Any] = {}
    exceedances: list[dict[str, Any]] = []
    for source_metric, label in SHAFT_METRICS.items():
        records = [shaft_item(case, row, source_metric, eligibility[(case, axis)])
                   for (case, axis), row in rows.items()]
        populations = {
            "all_96": records,
            "ordinary_84": [r for r in records if r["population"] == "ordinary_84"],
            "dedicated_12": [r for r in records if r["population"] == "dedicated_12"],
        }
        summary = {name: max_item(items) for name, items in populations.items()}
        summary["by_case"] = {case: max_item([r for r in records if r["case_id"] == case]) for case in CASE_IDS}
        summary["source_field_name"] = source_metric
        summary["label"] = label
        summary["unit"] = "reference index"
        summary["values_already_divided_by_Cdelta"] = True
        maxima[label] = summary
        for record in records:
            if record["index"] > 1.:
                exceedances.append({**record, "metric": label, "source_field_name": source_metric,
                                    "status": "exceeds_reference" if record["geometry_eligible"] else "exceeds_reference_geometry_ineligible"})
    return maxima, exceedances


def summarize_timber(data: dict[str, Any]) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    cases = by_case(data, "timber sections", set(CASE_IDS))
    max_results: dict[str, Any] = {}
    exceedances = []
    member_sets = []
    for case_id in CASE_IDS:
        members = cases[case_id].get("members", [])
        by_member = {row["member"]: row for row in members}
        require(len(by_member) == 20, f"{case_id}: expected 20 sawn timber section rows")
        member_sets.append(set(by_member))
        require(cases[case_id].get("field") == ref_record(RUN / case_id / "field.json"),
                f"{case_id}: timber sheet field binding mismatch")
        for metric in TIMBER_METRICS:
            for row in members:
                value = finite(row[metric], f"{case_id}/{row['member']}/{metric}")
                if value > 1.:
                    exceedances.append({"case_id": case_id, "member": row["member"], "metric": metric,
                                        "index": value, "geometry_status": "section_reference_only"})
    require(all(names == member_sets[0] for names in member_sets), "timber member inventory differs by case")
    for metric in TIMBER_METRICS:
        records = [{"case_id": case_id, "member": row["member"], "index": finite(row[metric], metric),
                    "section_interval_count": row.get("interval_count")}
                   for case_id in CASE_IDS for row in cases[case_id]["members"]]
        max_results[metric] = {"overall": max_item(records),
                               "by_case": {case: max_item([r for r in records if r["case_id"] == case]) for case in CASE_IDS},
                               "unit": "reference upper index", "source_field_name": metric}
    return max_results, exceedances


def expected_cleat_groups(geometry: dict[str, Any]) -> dict[str, set[frozenset[str]]]:
    hosts = sorted(name for name in geometry.get("profiles", {}) if name.startswith("eoere_cleat_"))
    require(len(hosts) == 2, "analysis geometry must expose exactly two bonded cleat hosts")
    axes = {row["id"]: row for row in geometry["axes"]}
    groups: dict[str, set[frozenset[str]]] = {}
    for host in hosts:
        own = sorted(axis_id for axis_id, row in axes.items() if host in row.get("receivers", []))
        require(len(own) == 4, f"{host}: expected four shaft axes on the bonded host")
        groups[host] = {frozenset(c) for n in range(1, 5) for c in itertools.combinations(own, n)}
        require(len(groups[host]) == 15, f"{host}: four-hole subset census mismatch")
    return groups


def summarize_plywood(data: dict[str, Any], expected_thickness: float, expected_groups: dict[str, set[frozenset[str]]],
                      eligibility: dict[tuple[str, str], dict[str, Any]], label: str) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    cases = by_case(data, label, set(CASE_IDS))
    close(data.get("credited_combined_wall_mm"), expected_thickness, f"{label}: credited wall thickness")
    require(data.get("bores_per_host") == 4 and data.get("subsets_per_case") == 30,
            f"{label}: expected four bores and thirty complete subsets per case")
    all_records: list[dict[str, Any]] = []
    exceedances: list[dict[str, Any]] = []
    for case_id in CASE_IDS:
        case = cases[case_id]
        require(case.get("field") == ref_record(RUN / case_id / "field.json"), f"{case_id}: {label} field binding mismatch")
        groups = case.get("groups", [])
        found: dict[str, set[frozenset[str]]] = {host: set() for host in expected_groups}
        require(len(groups) == 30, f"{case_id}: {label} must contain 30 four-hole groups")
        for row in groups:
            close(row.get("whole_wall_mm"), expected_thickness, f"{case_id}: {label} group wall thickness")
            host = row.get("leaf", row.get("host"))
            axes = frozenset(row.get("axes", []))
            require(host in found and axes in expected_groups[host], f"{case_id}: unexpected {label} plywood group {host}/{sorted(axes)}")
            require(axes not in found[host], f"{case_id}: duplicate {label} plywood group {host}/{sorted(axes)}")
            found[host].add(axes)
            geometry_state = [eligibility[(case_id, axis)] for axis in axes]
            geom_ok = all(state["eligible"] for state in geometry_state)
            identifier = f"{host}:{','.join(sorted(axes))}"
            for metric in PLYWOOD_METRICS:
                value = finite(row[metric], f"{case_id}/{identifier}/{metric}")
                item = {"case_id": case_id, "leaf": host, "axes": sorted(axes), "group_id": identifier,
                        "metric": metric, "index": value, "geometry_eligible": geom_ok,
                        "geometry_status": "eligible_reference_only" if geom_ok else "geometry_ineligible_no_pass",
                        "reference_role": "lower_bound" if metric in LOWER_BOUND_PLYWOOD else "balanced_group_reference"}
                all_records.append(item)
                if value > 1.:
                    status = "exceeds_reference_lower_bound" if metric in LOWER_BOUND_PLYWOOD else "exceeds_reference"
                    if not geom_ok:
                        status += "_geometry_ineligible"
                    exceedances.append({**item, "status": status})
        require(all(found[h] == expected_groups[h] for h in found), f"{case_id}: {label} group set is incomplete")
    maxima = {}
    root_maximum_keys = {
        "balanced_pressure_reference_index": "maximum_balanced_pressure_reference_index",
        "minimum_scalar_pressure_reference_index": "maximum_minimum_scalar_pressure_reference_index",
        "integrated_force_only_reference_index": "maximum_integrated_force_only_reference_index",
    }
    for metric in PLYWOOD_METRICS:
        rows = [r for r in all_records if r["metric"] == metric]
        calculated_maximum = max_item(rows)
        close(data.get(root_maximum_keys[metric]), calculated_maximum["index"], f"{label}: reported root maximum for {metric}")
        maxima[metric] = {"overall": max_item(rows),
                          "by_case": {case: max_item([r for r in rows if r["case_id"] == case]) for case in CASE_IDS},
                          "unit": "reference index", "reference_role": "lower_bound" if metric in LOWER_BOUND_PLYWOOD else "balanced_group_reference"}
    return maxima, exceedances


def inspect_unsupported_axes(fields: dict[str, dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    return {case_id: unsupported_oblique_axes(fields[case_id]) for case_id in CASE_IDS}


def hardware_grade_counts(geometry: dict[str, Any]) -> dict[str, int]:
    with HARDWARE.open(newline="") as stream:
        prior = {row["axis_id"]: row for row in csv.DictReader(stream)}
    overrides = {row["axis_id"]: row for row in geometry.get("selected_stack_overrides", [])}
    result: dict[str, int] = {}
    ids = {row["id"] for row in geometry["axes"]}
    require(ids.issubset(prior) and ids.issubset(overrides), "hardware selection rows do not cover all current axes")
    for axis_id in ids:
        row = {**prior[axis_id], **overrides[axis_id]}
        grade = str(row.get("selected_bolt_grade", ""))
        group = "A574" if "A574" in grade else "Grade 5" if "Grade 5" in grade else "other"
        result[group] = result.get(group, 0) + 1
    require(result == {"A574": 12, "Grade 5": 84}, f"current selected bolt grade census is {result}")
    return result


def cg_factor_inventory(rows: dict[tuple[str, str], dict[str, Any]], axis_ids: set[str]) -> dict[str, Any]:
    result = {}
    for name, subset in (("ordinary_84", axis_ids - DEDICATED), ("dedicated_12", DEDICATED)):
        by_case = {}
        all_factors = []
        for case_id in CASE_IDS:
            factors = {axis: finite(rows[(case_id, axis)]["bounded_Cg"], f"{case_id}/{axis} Cg") for axis in subset}
            counts: dict[str, int] = {}
            for factor in factors.values():
                key = format(factor, ".12g")
                counts[key] = counts.get(key, 0) + 1
            by_case[case_id] = {"factor_counts": counts, "minimum": min(factors.values()), "maximum": max(factors.values())}
            all_factors.extend(factors.values())
            if name == "dedicated_12":
                require(all(value == 0.5 for value in factors.values()),
                        f"{case_id}: dedicated shafts must use the current n<=2 conservative Cg bound")
        result[name] = {"axis_count_per_case": len(subset), "by_case": by_case,
                        "minimum_all_cases": min(all_factors), "maximum_all_cases": max(all_factors)}
    return result


def _compact_surface_witness(case_id: str, surface: dict[str, Any], direction: dict[str, Any]) -> dict[str, Any]:
    actual_end = surface.get("grain_end_distances_mm") or []
    actual_edge = surface.get("crossgrain_edge_distances_mm") or []
    required_end = direction.get("end_minimum_mm") or []
    required_edge = direction.get("edge_required_mm") or []
    end_shortfalls = [max(0., float(required) - float(actual))
                      for required, actual in zip(required_end, actual_end)]
    edge_shortfalls = [max(0., float(required) - float(actual))
                       for required, actual in zip(required_edge, actual_edge)]
    return {
        "case_id": case_id,
        "local_line_force_N_per_mm": direction.get("local_line_force_N_per_mm"),
        "required_end_minimum_mm": required_end,
        "actual_end_distances_mm": actual_end,
        "required_edge_mm": required_edge,
        "actual_edge_distances_mm": actual_edge,
        "maximum_end_shortfall_mm": max(end_shortfalls, default=0.),
        "maximum_edge_shortfall_mm": max(edge_shortfalls, default=0.),
        "Cdelta_end": direction.get("Cdelta_end"),
    }


def public_summary(report: dict[str, Any], full_ref: dict[str, str]) -> dict[str, Any]:
    """Return a compact public copy without changing values or source claims."""
    result = copy.deepcopy(report)
    raw_geometry = report["geometry_eligibility"]
    case_order = {case: i for i, case in enumerate(report["case_ids"])}

    surfaces: dict[tuple[str, str], dict[str, Any]] = {}
    for item in raw_geometry.get("ineligible_surfaces", []):
        key = (item["axis_id"], item["host"])
        entry = surfaces.setdefault(key, {
            "axis_id": item["axis_id"], "host": item["host"], "eligible": False,
            "diameter_mm": item.get("diameter_mm"),
            "grain_end_distances_mm": item.get("grain_end_distances_mm"),
            "crossgrain_edge_distances_mm": item.get("crossgrain_edge_distances_mm"),
            "centered_four_diameter_equivalent_width_eligible": item.get("centered_four_diameter_equivalent_width_eligible"),
            "centered_width_required_mm": item.get("centered_width_required_mm"),
            "minimum_crossgrain_edge_distance_mm": item.get("minimum_crossgrain_edge_distance_mm"),
            "case_ids": set(), "reasons": set(), "failed_signed_minimum_witnesses": [],
        })
        case_id = item["case_id"]
        entry["case_ids"].add(case_id)
        entry["reasons"].update(item.get("reasons", []))
        failed = [row for row in item.get("failed_pressure_directions", []) if row.get("eligible") is not True]
        if failed:
            witness = max((_compact_surface_witness(case_id, item, direction) for direction in failed),
                          key=lambda row: row["maximum_end_shortfall_mm"] + row["maximum_edge_shortfall_mm"])
            entry["failed_signed_minimum_witnesses"].append(witness)
    compact_surfaces = []
    for key in sorted(surfaces):
        entry = surfaces[key]
        entry["case_ids"] = sorted(entry["case_ids"], key=case_order.__getitem__)
        entry["reasons"] = sorted(entry["reasons"])
        entry["failed_signed_minimum_witnesses"].sort(key=lambda row: case_order[row["case_id"]])
        compact_surfaces.append(entry)

    pairs: dict[tuple[str, tuple[str, ...]], dict[str, Any]] = {}
    for item in raw_geometry.get("ineligible_receiver_pairs", []):
        key = (str(item.get("host")), tuple(sorted(item.get("axes", []))))
        entry = pairs.setdefault(key, {
            "host": key[0], "axes": list(key[1]), "eligible": False,
            "grain_cross_separations_mm": item.get("grain_cross_separations_mm"),
            "perpendicular_between_row_minimum_mm": item.get("perpendicular_between_row_minimum_mm"),
            "parallel_direction_eligible": item.get("parallel_direction_eligible"),
            "perpendicular_direction_eligible": item.get("perpendicular_direction_eligible"),
            "edge_for_long_penetration_eligible": item.get("edge_for_long_penetration_eligible"),
            "Cdelta_spacing": item.get("Cdelta_spacing"),
            "case_ids": set(), "reasons": set(),
        })
        entry["case_ids"].add(item["case_id"])
        entry["reasons"].update(item.get("reasons", []))
    compact_pairs = []
    for key in sorted(pairs):
        entry = pairs[key]
        entry["case_ids"] = sorted(entry["case_ids"], key=case_order.__getitem__)
        entry["reasons"] = sorted(entry["reasons"])
        compact_pairs.append(entry)

    result["geometry_eligibility"] = {
        "all_geometry_eligible": raw_geometry["all_geometry_eligible"],
        "eligible_axis_count_by_case": copy.deepcopy(raw_geometry["eligible_axis_count_by_case"]),
        "ineligible_axes": [{key: row[key] for key in ("case_id", "axis_id", "population", "status")}
                            | {"eligible": False} for row in raw_geometry.get("ineligible_axes", [])],
        "ineligible_surfaces": compact_surfaces,
        "ineligible_receiver_pairs": compact_pairs,
        "unsupported_oblique_cases": copy.deepcopy(raw_geometry.get("unsupported_oblique_cases", {})),
        "no_pass_when_geometry_ineligible": raw_geometry["no_pass_when_geometry_ineligible"],
        "shaft_geometry_metric_semantics": raw_geometry["shaft_geometry_metric_semantics"],
    }
    result["source_bindings"]["full_raw_report"] = copy.deepcopy(full_ref)
    result.pop("field_limits_by_case", None)
    result.pop("worksheet_limits", None)
    result["material_derivation_applicability"].pop("inherited_derivation_text", None)
    result["material_derivation_applicability"]["inherited_derivation_text_retained_in_full_report"] = True
    source_map_limits = result["source_map_limits"]
    source_map_limits.pop("field_source_map_entries_by_case", None)
    inherited_checks = source_map_limits.pop("inherited_source_closure_verified_at_preparation_by_case", {})
    source_map_limits["all_inherited_source_closure_receipts_verified_at_preparation"] = all(inherited_checks.values())
    source_map_limits.pop("note", None)
    result["public_compaction"] = {
        "full_raw_report": copy.deepcopy(full_ref),
        "omits_repeated_detail_lists": True,
        "geometry_compaction": "Surfaces unique by axis/host with signed witnesses; receiver pairs unique by host/axes with case coverage.",
    }
    return result


def build_report(out_path: Path) -> dict[str, Any]:
    receipt, receipt_ref = read_json(GEOMETRY_RECEIPT)
    physical, physical_ref = read_json(PHYSICAL_GEOMETRY)
    analysis_geometry, analysis_ref = read_json(ANALYSIS_GEOMETRY)
    material, material_ref = read_json(MATERIAL)
    readiness, readiness_ref = read_json(READINESS)
    physical_checked_ref = receipt.get("checked_geometry")
    resolve_ref(physical_checked_ref, "v6 geometry receipt physical geometry")
    require(physical_checked_ref == physical_ref, "v6 geometry receipt does not bind current physical geometry")
    require(receipt.get("revision") == "eoere-flat-cleats-principal-upper-pairs-v6", "physical geometry receipt revision mismatch")
    require(physical.get("revision") == receipt.get("revision"), "physical geometry revision mismatch")
    require(len(physical.get("axes", [])) == 96 and len(physical.get("screw_axes", [])) == 66,
            "physical geometry inventory mismatch")
    require(analysis_geometry.get("parent_owner_geometry") == physical_ref, "analysis geometry parent does not bind v6 physical geometry")
    require(analysis_geometry.get("perfect_bond_analysis") is True, "expected declared perfect-bond analytical geometry")
    require(analysis_geometry.get("actual_bond_qualified") is False, "actual adhesive bond must remain unqualified")
    require(analysis_geometry.get("analytical_laminated_bodies") == 2 and analysis_geometry.get("physical_plywood_leaves") == 4,
            "expected two analytical hosts built from four physical plywood leaves")
    require(len(analysis_geometry.get("axes", [])) == 96 and len({r["id"] for r in analysis_geometry["axes"]}) == 96,
            "analysis geometry shaft census mismatch")
    axis_ids = {r["id"] for r in analysis_geometry["axes"]}
    require(len(DEDICATED) == 12 and DEDICATED.issubset(axis_ids), "dedicated 12-bolt classification mismatch")
    require(len(axis_ids - DEDICATED) == 84, "ordinary bolt count mismatch")
    require(len(analysis_geometry.get("screw_axes", [])) == 66, "panel/Hillman geometry census mismatch")
    require(material.get("current_envelope_width_mm") == 139.7 and material.get("nominal_combined_thickness_mm") == 38.1,
            "current plywood approximation dimensions changed")
    require(material.get("physical_qualification") is False and material.get("release") is False,
            "material qualification/release must remain false")
    require(receipt.get("complete_conditional_frame_evaluation") is False
            and receipt.get("fabrication_released") is False and receipt.get("climbing_released") is False,
            "physical geometry receipt release/evaluation flags must remain false")
    require(receipt.get("panel_Hillman_resolution_deferred") is True, "geometry receipt must keep panel/Hillman resolution deferred")
    require(analysis_geometry.get("geometry_adopted") is False and analysis_geometry.get("complete_joint_qualified") is False,
            "analytical geometry must remain unadopted and unqualified")
    require(readiness.get("new_force_response_computed") is False,
            "readiness is expected to remain the frozen pre-response receipt")
    for key, value in (("bodies", 148), ("shafts", 96), ("wood_walls", 112), ("fitting_ports", 96), ("screws", 66), ("cases", 6)):
        require(readiness.get(key) == value, f"readiness {key} count mismatch")
    require(readiness.get("complete_joint_or_frame_qualified") is False, "readiness must not claim complete qualification")
    for ref_key, expected in (("physical_geometry", physical_ref), ("analysis_geometry", analysis_ref),
                              ("material", material_ref), ("inputs", ref_record(INPUTS))):
        require(readiness.get(ref_key) == expected, f"readiness {ref_key} binding mismatch")

    fields: dict[str, dict[str, Any]] = {}
    field_bindings = {}
    for case_id in CASE_IDS:
        field, _, _, binding = load_field(case_id)
        fields[case_id] = field
        field_bindings[case_id] = binding
        require(field["trial_parent_geometry"] == analysis_ref, f"{case_id}: field does not use current analysis geometry")
        require(field["source_inputs"]["scenario"]["perfect_bond_analysis"]["physical_parent"] == physical_ref,
                f"{case_id}: field physical geometry binding mismatch")
    require(len(CASE_IDS) == 6, "current case inventory must contain six cases")

    worksheet_data = {}
    worksheet_refs = {}
    for name, path in WORKSHEET_PATHS.items():
        worksheet_data[name], worksheet_refs[name] = load_worksheet(name, path)
    for name in ("nominal_38p1_plywood_groups", "credited_36p5_plywood_groups"):
        data = worksheet_data[name]
        for active in (CHECKS_PRODUCER, ROW_PRODUCER, ANALYSIS_GEOMETRY):
            verify_pin(data, active, name)
        for case_id, binding in field_bindings.items():
            for role in ("field", "independent_replay", "independent_plywood_replay"):
                current_ref = binding[role]
                require(data.get("source_sha256", {}).get(current_ref["path"]) == current_ref["sha256"],
                        f"{name}: missing or stale {case_id} {role} source pin")
        close(data.get("duration_factor_CD"), 1., f"{name}: explicit CD")
        require(data.get("complete_conditional_frame_evaluation") is False, f"{name}: complete-frame flag must remain false")
        require(data.get("fabrication_released") is False and data.get("climbing_released") is False,
                f"{name}: plywood row-set release flags must remain false")
        require(data.get("nominal38p1_perfect_bond_response_recomputed") is True,
                f"{name}: nominal perfect-bond response receipt missing")
        expected_recomputed = name == "nominal_38p1_plywood_groups"
        require(data.get("credited_wall_response_recomputed") is expected_recomputed,
                f"{name}: credited-wall response-recompute flag mismatch")
    active_geometry_pins = [
        verify_pin(analysis_geometry, ANALYSIS_PRODUCER, "analysis geometry"),
        verify_pin(analysis_geometry, GEOMETRY_RECEIPT, "analysis geometry"),
        verify_pin(analysis_geometry, PHYSICAL_GEOMETRY, "analysis geometry"),
        verify_pin(material, ANALYSIS_PRODUCER, "material"),
    ]
    unsupported = inspect_unsupported_axes(fields)
    shaft_rows, eligibility = check_adjusted_shafts(
        worksheet_data["shaft_geometry_Cdelta_adjusted"], worksheet_data["shaft_bearing_statics_Cg_adjusted"], axis_ids, fields, unsupported)
    cg_inventory = cg_factor_inventory(shaft_rows, axis_ids)

    # Confirm that every plywood group uses geometry-qualified axes; the group
    # value itself remains a worksheet comparison, never a joint pass.
    expected_groups = expected_cleat_groups(analysis_geometry)
    shaft_maxima, shaft_exceedances = summarize_shafts(shaft_rows, eligibility)
    timber_maxima, timber_exceedances = summarize_timber(worksheet_data["timber_sections"])
    plywood_nominal_maxima, plywood_nominal_exceedances = summarize_plywood(
        worksheet_data["nominal_38p1_plywood_groups"], 38.1, expected_groups, eligibility, "nominal38p1")
    plywood_credited_maxima, plywood_credited_exceedances = summarize_plywood(
        worksheet_data["credited_36p5_plywood_groups"], 36.5, expected_groups, eligibility, "bonded36p5")

    ineligible_axes = []
    ineligible_surfaces = []
    ineligible_pair_map: dict[tuple[str, str, tuple[str, ...]], dict[str, Any]] = {}
    eligible_counts = {}
    for case_id in CASE_IDS:
        states = {axis: eligibility[(case_id, axis)] for axis in axis_ids}
        eligible_counts[case_id] = sum(state["eligible"] for state in states.values())
        for axis_id, state in states.items():
            if not state["eligible"]:
                ineligible_axes.append({"case_id": case_id, "axis_id": axis_id,
                                        "population": "dedicated_12" if axis_id in DEDICATED else "ordinary_84",
                                        "status": "ineligible_no_pass", **state})
                ineligible_surfaces.extend({"case_id": case_id, **row} for row in state["ineligible_surfaces"])
                for row in state["ineligible_pairs"]:
                    pair_key = (case_id, str(row.get("host")), tuple(sorted(row.get("axes", []))))
                    ineligible_pair_map[pair_key] = {"case_id": case_id, **row}

    active_bindings = {
        "physical_geometry_receipt": receipt_ref,
        "physical_geometry": physical_ref,
        "analysis_geometry": analysis_ref,
        "material": material_ref,
        "prepared_inputs": ref_record(INPUTS),
        "frozen_readiness_receipt": readiness_ref,
        "analysis_producer": ref_record(ANALYSIS_PRODUCER),
        "worksheet_adapter": ref_record(CHECKS_PRODUCER),
        "cleat_row_producer": ref_record(ROW_PRODUCER),
        "report_producer": ref_record(REPORT_PRODUCER),
        "hardware_selection": ref_record(HARDWARE),
        "analysis_geometry_active_pins_verified": [pin for pin in active_geometry_pins if pin],
        "fields_and_replays": field_bindings,
        "worksheets": worksheet_refs,
    }
    report = {
        "schema": "eoere_current96_exceedance_review/v1",
        "geometry_revision": "eoere-flat-cleats-principal-upper-pairs-v6",
        "physical_geometry": receipt_ref,
        "analysis_geometry": analysis_ref,
        "material": material_ref,
        "material_properties": material.get("properties"),
        "material_derivation_applicability": {
            "active_material_ref": material_ref,
            "active_current_envelope_width_mm": material["current_envelope_width_mm"],
            "active_properties_source_pin_verified": True,
            "current_producer": ref_record(ANALYSIS_PRODUCER),
            "explanation": "The frozen material.properties and 139.7 mm current_envelope_width_mm are the active, source-bound values used by the six fields. The inherited material.derivation prose still describes the former 203.2 mm (8 in) operator; it is historical explanatory text, superseded by the current analysis producer's plywood_properties(139.7). Frozen material and input bytes remain source-bound.",
            "inherited_derivation_text": material.get("derivation"),
        },
        "case_count": 6,
        "case_ids": list(CASE_IDS),
        "current_response_computed": True,
        "load_contract": {"input_weight": 250, "input_unit": "lb", "downward_multiplier": 2.0,
                           "horizontal_force_n": 300.0, "duration_factor_CD": 1.0},
        "inventory": {"current_bolts": 96, "ordinary_bolts": 84, "dedicated_bolts": 12,
                      "selected_bolt_grades": hardware_grade_counts(analysis_geometry),
                      "bounded_Cg_factors_by_population": cg_inventory,
                      "sawn_timber_members": 20, "bonded_plywood_hosts": 2,
                      "physical_plywood_leaves": 4, "analytical_laminated_bodies": 2,
                      "physical_bodies": 148, "wood_bearing_walls": 112,
                      "four_port_fittings": 24, "panel_screws_deferred": 66},
        "source_bindings": active_bindings,
        "source_map_limits": {
            "field_source_map_entries_by_case": {c: field_bindings[c]["field_source_map_entries"] for c in CASE_IDS},
            "active_field_source_pins_reverified": True,
            "inherited_source_closure_verified_at_preparation_by_case": {
                c: field_bindings[c]["inherited_source_closure_verified_at_preparation"] for c in CASE_IDS},
            "inherited_historical_source_maps_reexecuted": False,
            "note": "The reducer rehashes current direct geometry, material, input, producer, field, replay, and worksheet bindings. It preserves inherited source-closure receipts and historical maps; it does not claim to rerun every historical dependency.",
        },
        "metric_maxima": {"shafts_Cdelta_adjusted": shaft_maxima,
                           "timber_sections": timber_maxima,
                           "plywood_nominal_38p1": plywood_nominal_maxima,
                           "plywood_credited_36p5": plywood_credited_maxima},
        "exceedances": {"shaft_metric_exceedances": shaft_exceedances,
                        "timber_member_metric_exceedances": timber_exceedances,
                        "plywood_nominal_38p1_group_metric_exceedances": plywood_nominal_exceedances,
                        "plywood_credited_36p5_group_metric_exceedances": plywood_credited_exceedances},
        "geometry_eligibility": {"all_geometry_eligible": not ineligible_axes,
                                 "eligible_axis_count_by_case": eligible_counts,
                                 "ineligible_axes": ineligible_axes,
                                 "ineligible_surfaces": ineligible_surfaces,
                                 "ineligible_receiver_pairs": list(ineligible_pair_map.values()),
                                 "unsupported_oblique_cases": unsupported,
                                 "no_pass_when_geometry_ineligible": True,
                                 "shaft_geometry_metric_semantics": "The worksheet's maximum_*_index_before_Cdelta keys are already divided by its computed Cdelta; the reducer validates against the Cg-adjusted statics rows and reports them as after_Cdelta."},
        "qualification": {"complete_conditional_frame_evaluation": False,
                           "physical_demand_bounds_established": False,
                           "structural_acceptance": False,
                           "fabrication_released": False,
                           "climbing_released": False,
                           "panel_Hillman_resolution_deferred": True,
                           "physical_bond_qualified": False,
                           "physical_floor_qualified": False,
                           "complete_joint_qualified": False},
        "limitations": [
            "Own six 250 lb fields use a uniform 139.7 mm full-width plywood beam approximation for the actual trapezoidal cleats; it is not a physical demand bound.",
            "The two bonded analytical hosts represent four physical plywood leaves with perfect compatibility; actual adhesive bond and plywood stiffness are unqualified.",
            "Four-host floor support and no-slip boundary behavior are analytical assumptions; the physical floor is unverified and no anchor capacity is established.",
            "The 66 panel/Hillman screw duties remain deferred and are not a strength pass or complete load path.",
            "The 12 dedicated shafts and 84 ordinary shafts are summarized separately. All values are conditional reference comparisons; no historical force or strength pass is transferred.",
            "A reference index at or below 1 is not a pass when geometry is ineligible, and no index establishes complete-joint or frame acceptance.",
            "This report does not establish actual material, hardware, adhesive, installation, floor, physical demand, or climber qualification.",
        ],
        "worksheet_limits": {name: {"limits": data.get("limits", []), "schema": data.get("schema")}
                             for name, data in worksheet_data.items()},
        "field_limits_by_case": {case_id: fields[case_id].get("limits", []) for case_id in CASE_IDS},
        "release": False,
    }
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", required=True, type=Path, help="fresh ignored RAW JSON output path; existing files are never overwritten")
    parser.add_argument("--public-summary", type=Path,
                        help="optionally write the fresh public summary to docs/bolted-frame-development/owner-frame-v6/engineering-review.json")
    args = parser.parse_args()
    out_path = args.out if args.out.is_absolute() else ROOT / args.out
    out_path = out_path.resolve()
    require(out_path.is_relative_to(ROOT / "fea/generated"), "--out must remain under ignored fea/generated RAW storage")
    require(out_path.suffix == ".json", "--out must use a .json suffix")
    require(not out_path.exists(), f"refusing to overwrite existing report: {out_path}")
    public_path = None
    if args.public_summary is not None:
        expected_public = ROOT / "docs/bolted-frame-development/owner-frame-v6/engineering-review.json"
        public_path = args.public_summary if args.public_summary.is_absolute() else ROOT / args.public_summary
        public_path = public_path.resolve()
        require(public_path == expected_public.resolve(), "--public-summary only accepts the exact v6 engineering-review.json path")
        require(not public_path.exists(), f"refusing to overwrite existing public summary: {public_path}")
        require(public_path != out_path, "RAW report and public summary paths must differ")
    report = build_report(out_path)
    raw_bytes = (json.dumps(report, indent=2, sort_keys=True, allow_nan=False) + "\n").encode()
    full_ref = {"path": rel(out_path), "sha256": hashlib.sha256(raw_bytes).hexdigest()}
    public_bytes = None
    if public_path is not None:
        public = public_summary(report, full_ref)
        public_bytes = (json.dumps(public, indent=2, sort_keys=True, allow_nan=False) + "\n").encode()
        require(len(public_bytes) <= 120 * 1024, f"public summary is {len(public_bytes)} bytes; compact export must be at most 120 KiB")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("xb") as stream:
        stream.write(raw_bytes)
    if public_path is not None and public_bytes is not None:
        with public_path.open("xb") as stream:
            stream.write(public_bytes)
    result = {"schema": report["schema"], "case_count": report["case_count"],
              "shafts": report["inventory"]["current_bolts"], "out": rel(out_path)}
    if public_path is not None and public_bytes is not None:
        result["public_summary"] = rel(public_path)
        result["public_summary_bytes"] = len(public_bytes)
    print(json.dumps(result))


if __name__ == "__main__":
    main()
