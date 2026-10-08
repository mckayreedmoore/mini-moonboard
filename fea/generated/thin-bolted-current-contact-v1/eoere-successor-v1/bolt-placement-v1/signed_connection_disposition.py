"""Join admitted own timber actions to frozen geometry reference markers."""
from __future__ import annotations

import argparse
import ast
import hashlib
import importlib.util
import json
import math
import sys
from pathlib import Path

OWN = Path(__file__).resolve()
ROOT = OWN.parents[5]
LEAF = OWN.parent.parent
FIELD = LEAF / "a12-first-order-v2/field.json"
ADMISSION = FIELD.with_name("admission-v3.json")
GATE = LEAF / "four-port-method-v1/first_order_admission_v3.py"
REFERENCE = OWN.with_name("connection-reference-disposition.json")
INPUT = LEAF / "mechanics-inputs-v1/inputs.json"
METHOD = ROOT / "scripts/thin_bolted_timber_resistance.py"
GATE_SHA = "a32992a3a5f4fb8c16a0402ad522b938650d8744200ca4d8a28dfd38e07a0008"
PINS = {
    str(FIELD.relative_to(ROOT)): "dad00e84ae98333beeb89a0c2403d48d9f40e9189c4525fc3746b8b3118de598",
    str(ADMISSION.relative_to(ROOT)): "383772d00e6f6c9207a833f5a9a067b6eaa1ca01279eb367c6ef518e41f77ee0",
    str(GATE.relative_to(ROOT)): GATE_SHA,
    str(REFERENCE.relative_to(ROOT)): "996c623c3904f75d14eafd0d25fd17660196dac778af6a5f9e75c73a47c36115",
    str(INPUT.relative_to(ROOT)): "7a003cb7fe6d14a8644a3030b45caf96a7a4b59618d8c1703c3e3626f267d4b4",
    str(METHOD.relative_to(ROOT)): "74d992cfbe4947587a8c6f0e65f7a8b47e0cd1c79f07721620c7137208919c2d",
    str(OWN.relative_to(ROOT)): hashlib.sha256(OWN.read_bytes()).hexdigest(),
}
SELECTED = ("cleat_post_bolt_left_1", "cleat_post_bolt_left_2", "cleat_post_bolt_right_1", "cleat_post_bolt_right_2",
            "eoere_bolt_067", "eoere_bolt_070", "eoere_bolt_001", "eoere_bolt_002", "eoere_bolt_014", "eoere_bolt_018")


def require(ok, message):
    if not ok:
        raise ValueError(message)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest()


def verify(pins):
    for path, expected in pins.items():
        require(sha(ROOT / path) == expected, "Changed source: " + path)


def exact_methods():
    names = {"vector", "dot", "unit", "cross", "resolved_action", "end_geometry_factor"}
    tree = ast.parse(METHOD.read_text())
    nodes = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name in names]
    require({n.name for n in nodes} == names, "Pinned pure methods missing")
    ns = {"math": math, "require": require}
    exec(compile(ast.fix_missing_locations(ast.Module(body=nodes, type_ignores=[])), str(METHOD), "exec"), ns)  # noqa: S102
    return ns


def near(actual, expected, tolerance):
    error = max(abs(a - b) for a, b in zip(actual, expected, strict=True))
    require(error <= tolerance, "Own action replay differs")
    return error


def evaluate():
    verify(PINS)
    field_bytes, receipt_bytes = FIELD.read_bytes(), ADMISSION.read_bytes()
    require(hashlib.sha256(field_bytes).hexdigest() == PINS[str(FIELD.relative_to(ROOT))]
            and hashlib.sha256(receipt_bytes).hexdigest() == PINS[str(ADMISSION.relative_to(ROOT))], "Released bytes changed while reading")
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))
    spec = importlib.util.spec_from_file_location("eoere_actual_signed_connection_admission_v3", GATE)
    gate = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = gate
    spec.loader.exec_module(gate)
    field, admitted_pins = gate.require_admitted_payload(field_bytes, json.loads(receipt_bytes), admission_sha256=GATE_SHA)
    # No action or material vector is read until genuine unchanged-byte admission.
    ref, inp = json.loads(REFERENCE.read_bytes()), json.loads(INPUT.read_bytes())
    verify(ref["source_sha256"])
    require(inp == field["source_inputs"], "Admitted source inputs differ from frozen geometry references")
    methods = exact_methods()
    dot, cross, unit = (methods[k] for k in ("dot", "cross", "unit"))
    resolved, end_factor = (methods[k] for k in ("resolved_action", "end_geometry_factor"))
    identity = {k: field[k] for k in ("state_id", "case_id", "accessory_placement")}
    sources = {r["axis_id"]: r for r in inp["shafts"]}
    members = {r["name"]: r for r in inp["timber_rows"]}
    wood = field["common_shaft_wood_bearing_actions"]
    require(len(wood) == 120 and len({(r["axis_id"], r["member"], r["surface_index"]) for r in wood}) == 120, "Own wood census differs")
    bearings = {r["id"]: r for r in field["common_shaft_bearing_actions"]}
    captures = {r["id"]: r for r in field["shaft_end_capture_actions"]}
    rim = {(r["axis_id"], r["receiver"]): r for r in ref["rim_short_edge_branches"]}
    records, max_force_error, max_moment_error = [], 0., 0.
    for row in wood:
        if row["axis_id"] not in SELECTED:
            continue
        require(all(row[k] == v for k, v in identity.items()), "Own aggregate identity differs")
        aid, name = row["axis_id"], row["member"]
        source, member = sources[aid], members[name]
        surface = source["surfaces"][row["surface_index"]]
        require(surface["kind"] == "wood" and surface["host"] == name and surface["interval_mm"] == row["surface_interval_mm"], "Own bearing interval source differs")
        near(row["grain_axis_xyz"], member["axis"], 1e-10)
        require(len(row["own_bearing_points"]) == 2 and len(set(row["own_bearing_points"])) == 2, "Both own Gauss points required")
        own = [(bearings[k], bearings[k]["point_xyz_mm"]) for k in row["own_bearing_points"]]
        own += [(captures[k], captures[k]["host_support_point_xyz_mm"]) for k in row["own_end_captures"]]
        force, moment, own_points = [0., 0., 0.], [0., 0., 0.], []
        for action, point in own:
            require(action["axis_id"] == aid and action["second"] == name and all(action[k] == v for k, v in identity.items()), "Another host's action entered own reduction")
            f = action["force_on_second_xyz_n"]
            arm = [a - b for a, b in zip(point, row["point_xyz_mm"], strict=True)]
            transported = cross(arm, f)
            for i in range(3):
                force[i] += f[i]
                moment[i] += transported[i] + action["moment_on_second_at_point_xyz_nmm"][i]
            own_points.append({"id": action["id"], "kind": action["kind"], "host_point_xyz_mm": point,
                               "force_on_own_member_xyz_n": f,
                               "signed_components": resolved(f, member["axis"], source["basis"][0])})
        force_error = near(force, row["force_on_host_xyz_n"], 1e-8)
        moment_error = near(moment, row["moment_on_host_at_point_xyz_nmm"], 1e-6)
        max_force_error, max_moment_error = max(max_force_error, force_error), max(max_moment_error, moment_error)
        action = resolved(force, member["axis"], source["basis"][0])
        g, p = unit(member["axis"]), row["point_xyz_mm"]
        ends = {"negative": dot([a - b for a, b in zip(p, member["start"], strict=True)], g),
                "positive": dot([a - b for a, b in zip(member["end"], p, strict=True)], g)}
        is_rim = (aid, name) in rim
        square = not is_rim and (name.startswith("eoere_cleat_") or all(abs(e["normal_to_nominal_grain_deg"]) < 1e-8 for e in member["raw_profile_source"]["end_cut_planes"]))
        end_marker = None
        if square and action["grain_loaded_end"] is not None:
            toward = action["grain_loaded_end"]
            opposite = "positive" if toward == "negative" else "negative"
            end_marker = {"own_parallel_component_acts_toward_end": toward,
                "toward_selected_square_raw_end_only": end_factor(ends[toward], source["diameter_mm"], "softwood_parallel_tension"),
                "acts_away_from_opposite_square_raw_end": opposite,
                "away_from_opposite_end_only": end_factor(ends[opposite], source["diameter_mm"], "parallel_compression"),
                "scalar_applied_to_actual_oblique_action": None}
        edge_marker = None
        if is_rim:
            r = rim[(aid, name)]
            near(action["cross_grain_axis_xyz"], r["crossgrain_axis_xyz"], 1e-8)
            toward_short = (1 if action["cross_grain_signed_n"] > 0 else -1) == r["short_edge_direction_sign"]
            edge_marker = {"own_crossgrain_component_points_toward_short_edge": toward_short,
                "raw_short_edge_mm": r["raw_short_edge_distance_mm"],
                "perpendicular_loaded_edge_4D_margin_mm": r["raw_short_edge_distance_mm"] - 4 * source["diameter_mm"] if toward_short else r["other_raw_edge_distance_mm"] - 4 * source["diameter_mm"],
                "unloaded_edge_1p5D_margin_mm": (r["other_raw_edge_distance_mm"] if toward_short else r["raw_short_edge_distance_mm"]) - 1.5 * source["diameter_mm"],
                "formal_perpendicular_edge_acceptance": None,
                "applicability": "Actual resultant is oblique; these are signed component markers, not a pure perpendicular-load code disposition. Short raw end is beveled; equivalent finished shear area remains unresolved."}
        point_parallel = [p["signed_components"]["parallel_grain_signed_n"] for p in own_points if p["kind"] == "common_shaft_bearing"]
        records.append({**identity, "axis_id": aid, "member": name, "surface_index": row["surface_index"], "surface_interval_mm": row["surface_interval_mm"],
            "reference_aggregate_point_xyz_mm": p, "force_on_own_member_xyz_n": force, "moment_on_own_member_at_aggregate_xyz_nmm": moment,
            "own_signed_components": action, "own_point_actions": own_points,
            "own_bearing_parallel_component_reverses_along_span": min(point_parallel) < 0 < max(point_parallel),
            "square_raw_end_distances_mm": ends if square else None, "signed_end_marker": end_marker, "signed_rim_edge_marker": edge_marker,
            "complete_Cdelta": None, "complete_group_or_splitting_resistance_n": None, "classical_single_resultant_Z_applicability": None,
            "own_force_replay_error_n": force_error, "own_moment_replay_error_nmm": moment_error})
    require(len(records) == 16 and {r["axis_id"] for r in records} == set(SELECTED), "Selected own member census differs")
    verify(PINS)
    verify(admitted_pins)
    verify(ref["source_sha256"])
    require(FIELD.read_bytes() == field_bytes and ADMISSION.read_bytes() == receipt_bytes, "Released bytes changed during reduction")
    return {"schema": "eoere_actual_signed_timber_connection_markers/v1", **identity, "source_sha256": PINS,
        "admitted_source_closure": {"receipt_path": str(ADMISSION.relative_to(ROOT)), "receipt_sha256": PINS[str(ADMISSION.relative_to(ROOT))],
            "authenticated_source_count": len(admitted_pins), "authenticated_source_map_canonical_sha256": canonical(admitted_pins)},
        "actual_v3_cheap_admission_passed_before_vectors": True, "source_bytes_unchanged_before_after": True,
        "record_count": len(records), "max_own_force_replay_error_n": max_force_error, "max_own_moment_replay_error_nmm": max_moment_error,
        "records": records, "all_actual_selected_resultants_oblique_to_grain": all(r["own_signed_components"]["oblique_lateral_action"] for r in records),
        "hole_installation_scope": ref["hole_installation_scope"],
        "limits": ["Each own member aggregate is independently replayed from its two distributed bore actions and own-host captures. Opposite member force is never inferred.",
            "All vectors and point moments are same-state first-order reference-coordinate actions. Current finite poses, annular pressure/prying and a physical demand bound are not established.",
            "End factors are signed component markers on square raw reference ends; arbitrary oblique resultants and spanwise sign-changing distributed bearing/free moments do not automatically inherit classical ASD Z or scalar Cdelta.",
            "Rim end/edge rays remain the frozen raw source diagnostics; no finished-boundary, local fracture, group, net-section, splitting or complete-resistance acceptance is supplied.",
            "NDS requires the smallest applicable factor across the actual group/shear-plane inventory. Nominal steel-hole installation mismatch is separate and not waived by reduction factors.",
            "No CAD/query, q pose evaluation, K/operator replay, assembly, native solve, geometry change or predecessor force transfer occurred."],
        "execution": {"actual_orig_argv": sys.orig_argv},
        "release": dict.fromkeys(("complete_joint_resistance", "fabrication", "structural", "climbing"), False)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    require(not args.out.exists(), "Preserve existing evidence")
    result = evaluate()
    with args.out.open("x") as stream:
        json.dump(result, stream, sort_keys=True, indent=2, allow_nan=False)
        stream.write("\n")
    print(json.dumps({"path": str(args.out), "sha256": sha(args.out), "bytes": args.out.stat().st_size,
                      "state_id": result["state_id"], "record_count": result["record_count"]}))


if __name__ == "__main__":
    main()
