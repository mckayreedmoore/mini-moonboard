"""Apply the retained-bolt first-stage component checks to two new corner cases."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(ROOT))
from fea.compact_rail_checks import hardware_assumptions
from fea.thick_leg_checks import bolt_check

OUT = Path(__file__).resolve().parent / "affected-demand-screen.json"
BASE = Path("docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28")
REGISTER = BASE / "current-corner-left-leg-onward-transfer-register-attempt01/register.json"
MAP_DIR = BASE / "current-corner-left-leg-baseline-evidence-map-attempt01"
MAP = MAP_DIR / "baseline-evidence-map.json"
CASES = ("a12-rear", "a1-rear")
BOLTS = ("lumber_leg_bolt_left_1", "lumber_leg_bolt_left_2")
ROLES = ("retained_bolt_lateral_plane", "physical_bolt_outer_seat_tension")
LOAD_FACTORS = (0.1, 0.2, 0.3, 0.45, 0.675, 0.925, 1.0)
AXIS = (-1.0, 0.0, 0.0)
RECEIVERS = ("base_side_left", "lumber_leg_left")

# Source pins for the exact register, mapped historical geometry, and existing
# analysis methods. They are inputs/methods only; historical response forces are
# not imported into this calculation.
PINNED = {
    str(REGISTER): "b435f23d059d8b8399bcc5ab4afdbaa71171bac476b3a50953d68f8189cac8b0",
    str(BASE / "current-corner-left-leg-onward-transfer-register-attempt01/produce.py"):
        "df87e51e74fa41f1cc9c355ab6508935157b74c5b5ed0039c22a1243e541ac33",
    str(MAP): "d072c67cfaa3a656b6ad17e83c73af001882a1a283589548fa81d074e78ef9fa",
    str(MAP_DIR / "produce_map.py"):
        "28b191cf6ed5760cf26f18d24389929bfbf9b94775e7a2301f201053b12fa4d2",
    "docs/wood-joints-mvp/current-frame-bolt-review.md":
        "20067540bd318a3639e90278874bf793445a14c34bd316e18c6e508c2a518c89",
    "docs/floor-flush-construction-kerf-right/connection-axes.csv":
        "174033945a2136b094bf99360cb2c6dfa409accef423ab12538ef289b5d36a58",
    "docs/floor-flush-construction-kerf-right/bolt-hardware.csv":
        "a3081ca72f92271ae21967684c5b7a459619dc0cf5c00ac53e7d8cecd748afd8",
    "fea/results/floor-runner-mvp/a12-rear/geometry.json":
        "e62f402f10403e205f279e60fe991ef8d0b9b13ff73efb981ff33090e389e747",
    "fea/results/floor-runner-mvp/a12-rear/checks.json":
        "9ed713df60c1b031984e8e99a4a7f8c0d7dd59c0a81b0f008e14797c09aa2223",
    "fea/results/floor-runner-mvp/a12-rear/manifest.json":
        "5d721fa0b09950853b721b3dced5f0a1d0dc9f83a3af2fbb6b1797df2b02a388",
    "fea/results/floor-runner-mvp/a1-rear/geometry.json":
        "e62f402f10403e205f279e60fe991ef8d0b9b13ff73efb981ff33090e389e747",
    "fea/results/floor-runner-mvp/a1-rear/checks.json":
        "2ffa4998eb208d031805b3eb36817001180a263677096b88d778c4eb9a60fdef",
    "fea/results/floor-runner-mvp/a1-rear/manifest.json":
        "d65a6d63e8e62bb6af6c8b82e4800f98b066a995125b5cfe33be541d40d7b21a",
    "fea/compact_rail_checks.py":
        "0337b5383faffbcd3826506e8429ba1efaca7b70c50fb51c103f7a9eeb52d297",
    "fea/thick_leg_checks.py":
        "0609afebe3664d70b60de9499ffeedaa3fc1cd31991bb95f7ca76d18117cf041",
    "fea/dowel_yield.py":
        "d6c318e75c1a720d0b91f810a892e8309ef89735f66f48820ee853b753f8fe45",
    "fea/reinforced_fastener_checks.py":
        "11eb48b3ddcea64728a43b468f5cf9c6856485cee8fd5c75cf898b55b48436ee",
    "fea/current_response_resistance.py":
        "0054509a15aa2c3f6e420a2396cb6d2a00a9d252853a968fdba352b14080d427",
    "fea/compact_thick_checks.py":
        "036da136ba732d97b20a026ae98f5c78dfe3c9571b2b49b3be188909ba3c3dc4",
    "scripts/clear_space_results.py":
        "66d2e84e3e147aa220b11fa69f64680280a92aa48914ad1e3053d58087832d74",
    "docs/compact-half-inch-hardware.md":
        "471e537a5ba37fe7a4434d380e409c00254421d73580779b39e8c7b7d5bd105f",
}

EXPECTED_LATERAL_MAXIMA_N = {
    ("a12-rear", "lumber_leg_bolt_left_1"): 1183.3318120518184,
    ("a12-rear", "lumber_leg_bolt_left_2"): 1723.0820617128365,
    ("a1-rear", "lumber_leg_bolt_left_1"): 377.51344799784283,
    ("a1-rear", "lumber_leg_bolt_left_2"): 276.0787883005904,
}
EXPECTED_AXIAL_MAXIMA_N = {
    ("a12-rear", "lumber_leg_bolt_left_1"): 262.7068,
    ("a12-rear", "lumber_leg_bolt_left_2"): 529.4394,
    ("a1-rear", "lumber_leg_bolt_left_1"): 71.60235,
    ("a1-rear", "lumber_leg_bolt_left_2"): 178.438,
}


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify_pins() -> dict[str, str]:
    found = {}
    for rel, expected in PINNED.items():
        path = ROOT / rel
        actual = digest(path)
        if expected is None:
            raise SystemExit(f"missing source pin for {rel}")
        if actual != expected:
            raise SystemExit(f"source pin mismatch for {rel}: {actual} != {expected}")
        found[rel] = actual
    return found


def load_json(path: Path):
    return json.loads(path.read_text())


def verify_embedded_pins(pin_map, *, label):
    found = {}
    for raw_path, expected in pin_map.items():
        source = Path(raw_path)
        path = source if source.is_absolute() else ROOT / source
        actual = digest(path)
        if actual != expected:
            raise SystemExit(f"{label} embedded source pin mismatch for {raw_path}: {actual} != {expected}")
        found[str(raw_path)] = actual
    return found


def dot(a, b):
    return sum(x * y for x, y in zip(a, b, strict=True))


def norm(v):
    return math.sqrt(dot(v, v))


def close(a, b, *, atol=1e-8):
    return math.isclose(a, b, rel_tol=1e-10, abs_tol=atol)


def hardware_for(geometry, bolt_name):
    hardware_row = geometry["hardware_by_name"][bolt_name]
    bounds = geometry.get("hardware_resistance_bounds_by_name", {}).get(bolt_name, {})
    return hardware_assumptions(
        hardware_row["diameter_mm"],
        washer_od_mm=bounds.get("washer_od_mm", hardware_row["washer_od_mm"]),
        hole_diameter_mm=bounds.get("washer_hole_diameter_mm", hardware_row["hole_diameter_mm"]),
        washer_thickness_mm=bounds.get("washer_thickness_mm", hardware_row["washer_thickness_mm"]),
    )


def validate_register(register):
    if register.get("status") != "CONDITIONAL_SIGNED_ONWARD_ACTIONS_ONLY":
        raise ValueError("Unexpected parent register status")
    if register.get("retained_original_axes") != list(BOLTS):
        raise ValueError("Parent register bolt inventory changed")
    if register.get("new_block_axes_in_register") != []:
        raise ValueError("Expected only retained original bolt interfaces")
    rows = register.get("rows", [])
    if len(rows) != 56:
        raise ValueError(f"Expected 56 source-bound rows, found {len(rows)}")
    indexed = {}
    for row in rows:
        key = (row["case_id"], row["axis_id"], row["load_factor"], row["role"])
        if key in indexed:
            raise ValueError(f"duplicate parent register row {key}")
        indexed[key] = row
        if row["case_id"] not in CASES or row["axis_id"] not in BOLTS:
            raise ValueError(f"unexpected case or axis in {key}")
        if row["receivers"] != list(RECEIVERS):
            raise ValueError(f"unexpected receiver ownership in {key}")
        if row["role"] not in ROLES:
            raise ValueError(f"unexpected force role in {key}")
        if not any(close(row["load_factor"], factor, atol=1e-12) for factor in LOAD_FACTORS):
            raise ValueError(f"unexpected load factor in {key}")
        first = row["force_on_base_side_left_xyz_N"]
        second = row["force_on_lumber_leg_left_xyz_N"]
        if len(first) != 3 or len(second) != 3 or norm([a + b for a, b in zip(first, second, strict=True)]) > 1e-8:
            raise ValueError(f"action/reaction mismatch in {key}")
        if not close(norm(first), row["force_resultant_N"]):
            raise ValueError(f"resultant mismatch in {key}")
        interface = row.get("source_interface", {})
        if (interface.get("first"), interface.get("second")) != RECEIVERS:
            raise ValueError(f"source interface ownership mismatch in {key}")
        if interface.get("force_on_first_xyz_n") != first:
            raise ValueError(f"nested first action differs from register in {key}")
        if interface.get("force_on_second_xyz_n") != second:
            raise ValueError(f"nested reaction differs from register in {key}")
    for case in CASES:
        for bolt in BOLTS:
            for factor in LOAD_FACTORS:
                for role in ROLES:
                    key = (case, bolt, factor, role)
                    if key not in indexed:
                        raise ValueError(f"missing parent register row {key}")
    return indexed


def validate_baseline_inputs(mapping, geometries, checks):
    if mapping.get("status") != "TWO_CASE_CONDITIONAL_TRANSFER_LINKED_TO_UNQUALIFIED_BASELINE_CHECKS":
        raise ValueError("Unexpected baseline map status")
    if mapping.get("scope", {}).get("new_signed_action_rows_sha256") != PINNED[str(REGISTER)]:
        raise ValueError("Baseline map does not pin the current parent register")
    if mapping.get("scope", {}).get("interfaces") != list(BOLTS):
        raise ValueError("Baseline evidence map bolt inventory changed")
    for case in CASES:
        geometry = geometries[case]
        check = checks[case]
        if geometry.get("candidate") != "compact-floor-flush-development":
            raise ValueError(f"Unexpected historical geometry candidate for {case}")
        if check.get("candidate") != "compact-floor-flush-development" or check.get("qualified_for_design") is not False:
            raise ValueError(f"Historical case must remain explicitly unqualified for {case}")
        if check.get("status") != "LISTED_FIRST_STAGE_SCREENS_MET_WITH_OPEN_LIMITS":
            raise ValueError(f"Unexpected historical case status for {case}")
        for bolt in BOLTS:
            bolt_geometry = geometry["geometries_by_bolt_name"][bolt]
            if not close(bolt_geometry["diameter_mm"], 12.7):
                raise ValueError(f"Changed nominal diameter for {case}/{bolt}")
            if not close(bolt_geometry["bending_yield_psi"], 90000.0):
                raise ValueError(f"Changed bolt-yield basis for {case}/{bolt}")
            if set(bolt_geometry["members"]) != set(RECEIVERS):
                raise ValueError(f"Unexpected old member pair for {case}/{bolt}")
            for member in RECEIVERS:
                data = bolt_geometry["members"][member]
                if not close(data["bearing_length_mm"], 88.9):
                    raise ValueError(f"Changed member bearing length for {case}/{bolt}/{member}")
                if not close(data["specific_gravity"], 0.5) or not close(data["parallel_bearing_psi"], 5600.0):
                    raise ValueError(f"Changed timber basis for {case}/{bolt}/{member}")
            if bolt not in check.get("bolts", {}):
                raise ValueError(f"Historical resistance row missing for {case}/{bolt}")


def directional_angle_deg(lateral, grain):
    demand = norm(lateral)
    if demand <= 0:
        return 0.0
    cosine = min(1.0, abs(dot(lateral, grain)) / demand)
    return math.degrees(math.acos(cosine))


def build_report():
    source_pins = verify_pins()
    register = load_json(ROOT / REGISTER)
    mapping = load_json(ROOT / MAP)
    source_pins.update(verify_embedded_pins(register.get("source_sha256", {}), label="register"))
    source_pins.update(verify_embedded_pins(mapping.get("source_pins_sha256", {}), label="baseline map"))
    indexed = validate_register(register)
    geometries, checks = {}, {}
    for case in CASES:
        case_dir = ROOT / "fea/results/floor-runner-mvp" / case
        geometries[case] = load_json(case_dir / "geometry.json")
        checks[case] = load_json(case_dir / "checks.json")
    validate_baseline_inputs(mapping, geometries, checks)

    results = []
    summaries = []
    method_inputs_by_bolt = {}
    for case in CASES:
        case_geometry = geometries[case]
        for bolt in BOLTS:
            bolt_geometry = case_geometry["geometries_by_bolt_name"][bolt]
            hardware = hardware_for(case_geometry, bolt)
            if bolt not in method_inputs_by_bolt:
                method_inputs_by_bolt[bolt] = {
                    "nominal_diameter_mm": bolt_geometry["diameter_mm"],
                    "bolt_bending_yield_psi": bolt_geometry["bending_yield_psi"],
                    "member_inputs": {
                        member: {
                            key: bolt_geometry["members"][member][key]
                            for key in (
                                "grain", "bearing_length_mm", "specific_gravity",
                                "parallel_bearing_psi", "edge_distances_mm",
                            )
                        }
                        for member in RECEIVERS
                    },
                    "hardware_assumptions": hardware,
                    "selected_hardware_row_is_provisional": case_geometry["hardware_by_name"][bolt]["provisional"],
                }
            states = []
            for factor in LOAD_FACTORS:
                lateral_row = indexed[(case, bolt, factor, "retained_bolt_lateral_plane")]
                axial_row = indexed[(case, bolt, factor, "physical_bolt_outer_seat_tension")]
                lateral_force = lateral_row["force_on_base_side_left_xyz_N"]
                axial_force = axial_row["force_on_base_side_left_xyz_N"]
                lateral_action, axial_action = lateral_row["source_interface"], axial_row["source_interface"]
                for axis_force, role in ((lateral_force, "lateral"), (axial_force, "axial")):
                    if role == "lateral" and (abs(axis_force[0]) > 1e-8):
                        raise ValueError(f"Nontransverse register lateral action for {case}/{bolt}/{factor}")
                    if role == "axial" and (abs(axis_force[1]) > 1e-8 or abs(axis_force[2]) > 1e-8):
                        raise ValueError(f"Nonaxial register tie action for {case}/{bolt}/{factor}")
                tension = dot(axial_force, AXIS)
                signed_recorded = axial_action.get("signed_axis_force_on_first_n")
                if signed_recorded is None or not close(tension, signed_recorded):
                    raise ValueError(f"Outer-seat axial sign mismatch for {case}/{bolt}/{factor}")
                if tension < -1e-8:
                    raise ValueError(f"Expected tensile outer-seat action for {case}/{bolt}/{factor}")
                combined_first = [lateral_force[i] + axial_force[i] for i in range(3)]
                combined_second = [
                    lateral_row["force_on_lumber_leg_left_xyz_N"][i]
                    + axial_row["force_on_lumber_leg_left_xyz_N"][i]
                    for i in range(3)
                ]
                combined_radius = [
                    lateral_action["force_rounding_radius_xyz_n"][i]
                    + axial_action["force_rounding_radius_xyz_n"][i]
                    for i in range(3)
                ]
                demand_row = {
                    "axis": list(AXIS),
                    "first": RECEIVERS[0],
                    "second": RECEIVERS[1],
                    "force_on_first_xyz_n": combined_first,
                    "force_on_second_xyz_n": combined_second,
                }
                result = bolt_check(demand_row, bolt_geometry, hardware)
                lateral = [
                    combined_first[i] - dot(combined_first, AXIS) * AXIS[i]
                    for i in range(3)
                ]
                angles = {
                    member: directional_angle_deg(lateral, bolt_geometry["members"][member]["grain"])
                    for member in RECEIVERS
                }
                if not close(result["lateral_demand_n"], norm(lateral)):
                    raise ValueError(f"Legacy method lateral component disagrees for {case}/{bolt}/{factor}")
                if not close(result["hardware"]["absolute_axial_increment_n"], abs(tension)):
                    raise ValueError(f"Legacy hardware axial component disagrees for {case}/{bolt}/{factor}")
                states.append({
                    "load_factor": factor,
                    "source_connection_names": [lateral_row["source_connection_name"], axial_row["source_connection_name"]],
                    "lateral_force_on_base_side_left_xyz_N": lateral_force,
                    "outer_seat_tension_force_on_base_side_left_xyz_N": axial_force,
                    "signed_outer_seat_tension_N": tension,
                    "combined_per_bolt_force_on_base_side_left_xyz_N": combined_first,
                    "combined_per_bolt_force_on_lumber_leg_left_xyz_N": combined_second,
                    "combined_force_rounding_radius_xyz_N": combined_radius,
                    "lateral_resultant_N": result["lateral_demand_n"],
                    "lateral_load_to_grain_acute_angle_deg": angles,
                    "lateral_reference_N": result["lateral_reference_n"],
                    "lateral_ratio": result["lateral_ratio"],
                    "governing_yield_mode": result["dowel_reference"]["governing_mode"],
                    "all_six_yield_mode_references_lbf": result["dowel_reference"]["reference_values_lbf"],
                    "directional_bearing_psi_by_member": {
                        member: value
                        for member, value in zip(RECEIVERS, result["bearing_psi"], strict=True)
                    },
                    "external_edge_screen_by_member": result["placement"],
                    "direct_steel_interaction_ratio": result["hardware"]["steel_direct_ratio"],
                    "washer_wood_bearing_ratio_by_face": [x["wood_bearing_ratio"] for x in result["hardware"]["washers"]],
                    "washer_elastic_bending_ratio_by_face": [x["elastic_bending_ratio"] for x in result["hardware"]["washers"]],
                    "method_qualified_for_design": result["qualified_for_design"],
                })
            peak_lateral = max(states, key=lambda x: x["lateral_ratio"])
            peak_steel = max(states, key=lambda x: x["direct_steel_interaction_ratio"])
            peak_washer_bearing = max(states, key=lambda x: max(x["washer_wood_bearing_ratio_by_face"]))
            peak_washer_bending = max(states, key=lambda x: max(x["washer_elastic_bending_ratio_by_face"]))
            minimum_edge = min([
                (member, edge, state["external_edge_screen_by_member"][member]["margins_mm"][edge], state["load_factor"])
                for state in states for member in RECEIVERS
                for edge in state["external_edge_screen_by_member"][member]["margins_mm"]
            ], key=lambda x: x[2])
            expected_lateral = EXPECTED_LATERAL_MAXIMA_N[(case, bolt)]
            expected_axial = EXPECTED_AXIAL_MAXIMA_N[(case, bolt)]
            actual_lateral = max(x["lateral_resultant_N"] for x in states)
            actual_axial = max(x["signed_outer_seat_tension_N"] for x in states)
            if not close(actual_lateral, expected_lateral) or not close(actual_axial, expected_axial):
                raise ValueError(f"Parent source-maxima oracle mismatch for {case}/{bolt}")
            summary = {
                "case_id": case,
                "axis_id": bolt,
                "load_factor_count": len(states),
                "peak_lateral_demand_N": actual_lateral,
                "peak_lateral_demand_load_factor": max(states, key=lambda x: x["lateral_resultant_N"])["load_factor"],
                "conditional_original_method_lateral_reference_at_governing_state_N": peak_lateral["lateral_reference_N"],
                "conditional_original_method_lateral_ratio": peak_lateral["lateral_ratio"],
                "lateral_governing_yield_mode": peak_lateral["governing_yield_mode"],
                "peak_axial_tension_N": actual_axial,
                "peak_axial_tension_load_factor": max(states, key=lambda x: x["signed_outer_seat_tension_N"])["load_factor"],
                "peak_direct_steel_interaction_ratio": peak_steel["direct_steel_interaction_ratio"],
                "peak_steel_load_factor": peak_steel["load_factor"],
                "peak_washer_wood_bearing_ratio": max(peak_washer_bearing["washer_wood_bearing_ratio_by_face"]),
                "peak_washer_bending_ratio": max(peak_washer_bending["washer_elastic_bending_ratio_by_face"]),
                "minimum_old_external_edge_screen_margin_mm": minimum_edge[2],
                "minimum_edge_screen_location": {"member": minimum_edge[0], "edge": minimum_edge[1], "load_factor": minimum_edge[3]},
                "individual_screen_metrics_within_existing_bounds": all([
                    peak_lateral["lateral_ratio"] < 1.0,
                    peak_steel["direct_steel_interaction_ratio"] < 1.0,
                    max(peak_washer_bearing["washer_wood_bearing_ratio_by_face"]) < 1.0,
                    max(peak_washer_bending["washer_elastic_bending_ratio_by_face"]) < 1.0,
                    minimum_edge[2] >= 0.0,
                ]),
                "qualified_for_design": False,
                "states": states,
            }
            results.append(summary)
            summaries.append({key: value for key, value in summary.items() if key != "states"})

    return {
        "schema": "current_corner_left_leg_affected_demand_screen/v1",
        "status": "CONDITIONAL_EXISTING_INDIVIDUAL_COMPONENT_METHODS_APPLIED_TO_NEW_FORCES",
        "case_count": 2,
        "bolt_count": 2,
        "per_bolt_state_count": 7,
        "source_pin_sha256": source_pins,
        "method": {
            "lateral": "Reused fea.thick_leg_checks.bolt_check and fea.dowel_yield.single_shear as called by the selected-baseline clear-space checks: one single-shear plane, nominal 12.7 mm diameter, 88.9 mm bearing length in both solid members, gap zero, Fyb 90,000 psi, G 0.5, Fe_parallel 5,600 psi, Fe_perp = 6,100*G^1.45/sqrt(D) with D in inches and bearing strengths in psi, fixed original NDS yield-reduction terms (Im/Is=5, II=4.5, IIIm/IIIs/IV=4), corresponding to the unchanged fixed Ktheta=1.25 branch. No new load-angle Ktheta branch is adopted. Bearing strength and edge direction use each new signed lateral vector against both unchanged member grain directions.",
            "axial_and_hardware": "Reused fea.compact_rail_checks.hardware_assumptions plus fea.thick_leg_checks.hardware_check: provisional 1/2-inch Grade 5 tensile/shear area and steel yield assumptions, with the archived washer dimensional/material bounds. Same-increment outer-seat tie tension and lateral-plane resultant are paired by retained bolt ID for the existing direct steel interaction formula; washer compression and bending remain axial-only component screens.",
            "partial_thread_condition": "Nominal-diameter resistance assumes delivered thread/runout establishes no more than one-quarter threaded bearing in either 88.9 mm member length, per the existing NDS 12.3.7.2 condition. Schedule thread dimensions and purchased length are blank; actual delivery is not established.",
            "edge_screen": "Reused external-boundary rule is 7D at both grain ends, with 4D at the force-directed loaded depth edge and 1.5D at the opposite depth edge. Reported margins are clearance beyond these old rule distances, not absolute bolt-to-edge distances. New adjacent bores are not represented.",
            "thread_sensitivity": "Only the original nominal-diameter branch is applied. Full-thread-root sensitivity is non-adopted and is not transferred into this screen.",
            "force_handling": "At each matching load factor, the signed lateral-plane Y/Z action and the signed outer-seat axial X action for one bolt ID are combined as force components for the existing force-only bolt routine. No moments or prying couple are inferred from separate interface owner-datum wrenches.",
            "screen_scope": "Only the four A12-rear/A1-rear × two retained left LEG bolt combinations and their seven registered states. No group, net-section, splitting, complete-joint or case-acceptance computation.",
        },
        "method_inputs_by_bolt": method_inputs_by_bolt,
        "receiver_change": {
            "new_bores_in_base_side_left": 10,
            "new_bores_in_lumber_leg_left": 0,
            "original_bolt_axes_and_receiver_pair_unchanged": True,
            "implication": "The new bore pattern in base_side_left is the specific changed local section/group/splitting input. The unchanged lumber_leg_left local bore pattern and individual single-bolt method inputs can be reused for the bounded component screen; this does not qualify either receiver as a group.",
        },
        "per_bolt_results": results,
        "four_axis_case_summaries": summaries,
        "joint_accepted": False,
        "qualified_for_design": False,
        "limits": [
            "All values are conditional first-stage component screens using existing assumptions and the newly registered signed forces. Below-one component ratios do not establish acceptance of a joint or candidate.",
            "New bores in base_side_left are not included in the old external-edge rays or individual bolt method. Group spacing, net section, tear-out, local splitting and receiver interaction around the ten added bores remain unresolved for the affected receiver.",
            "The register's lateral plane and outer-seat tension are paired only by matching retained bolt ID and load factor for the legacy force-only method. This does not create a moment, internal bolt bending, prying or preload check.",
            "Axial direct-steel and washer bearing/bending ratios use the existing provisional hardware assumptions. They do not establish wood withdrawal, pull-through, splitting, delivered washer properties or an axial/lateral joint interaction rating.",
            "Nominal 12.7 mm resistance remains conditional on actual partial-thread placement through both timber bearing lengths. Thread runout, purchased length and delivered hardware remain unverified.",
            "Reported edge values are margins beyond the legacy external-boundary screen requirements, not actual bolt-to-edge distances. The local new-hole geometry is excluded.",
            "The non-adopted full-thread-root sensitivity is not transferred into the nominal branch.",
            "The old A12-rear and A1-rear candidate checks remain unqualified with open limits. No historical case pass, group result or candidate-level status is transferred; no blanket qualification of the twelve original arrangements is implied.",
        ],
    }


def write_report(report):
    OUT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")


def verify_output():
    expected = build_report()
    actual = load_json(OUT)
    if actual != expected:
        raise SystemExit("affected-demand-screen.json differs from reproduced source/method calculation")
    print("PASS: pinned inputs and all four case/bolt screens reproduced")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verify", action="store_true", help="reproduce and compare the checked JSON")
    args = parser.parse_args()
    report = build_report()
    if args.verify:
        if load_json(OUT) != report:
            raise SystemExit("affected-demand-screen.json differs from reproduced source/method calculation")
        print("PASS: pinned inputs and all four case/bolt screens reproduced")
    else:
        write_report(report)
        print(OUT.relative_to(ROOT))


if __name__ == "__main__":
    main()
