"""Audit issued SHOP bytes only; never import or execute production helpers."""
from __future__ import annotations

import csv
import hashlib
import io
import json
import math
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

OWN = Path(__file__).resolve()
ROOT = next(p for p in OWN.parents if (p / "AGENTS.md").is_file())
SHOP = OWN.parents[1]
OUT = SHOP / "runs-v1/output01"
PINS = {
    "result.json": "a8cacd9cfaf04d92b98ecb32b74908a43d39c3351e9d90cad4e6194188790208",
    "process.json": "465e79f086ec1e0c107dbd8994efe662b76a327f877e0f636d996442b9939c49",
    "reproduce.py": "18dd009a4b6f39eea5fa28a0fa67c15c69f1b9ec815ffe6026da8f818324f3b2",
}
CLOSURE = "9359334ec1453dcd3dc1306a3477d9af2da64a651a258d3e32f12b33d41a20f6"
AXES = {"cleat_post_bolt_"+s+"_"+str(i) for s in ("left", "right") for i in (1, 2)}
HOSTS = {"base_post_outer_left", "base_post_outer_right", "eoere_cleat_left", "eoere_cleat_right"}
DRAWINGS = {"extended-cleats.svg", "member-projections-1.svg", "member-projections-3.svg"}
CANDIDATES = DRAWINGS | {"members.csv", "receiver-holes.csv", "bolt-stacks.csv", "access-sides.csv",
    "current_profiles.json", "source-bindings.json", "hardware-role-locations.json"}
INHERITED = {"member-end-datums.csv", "panel-screw-datums.csv", "panel-machining.csv", "stock-nesting.json", "rear-recesses.json",
    "member-projections-2.svg", "member-projections-4.svg", "rear-recess.svg", "panel-layout-1.svg", "panel-layout-2.svg", "paired-drilling-fixture.svg"}
CAPTIONS = {
    "Both exterior cleats: sloped top / runner seat": "Unadopted Z180 proposal: exterior cleats",
    "Dedicated post shafts stay at Z 200.000 in the reviewed model.": "Proposal only: four dedicated post shafts at Z 180.000 mm.",
    "HOLD those four stations: nominal bore/screw gap only 0.341 mm.": "Unadopted layout; drilling and fabrication remain unreleased.",
    "No axis move, hole diameter or woodworking tolerance adopted here.": "Same nominal 4-inch bolts; no spacer or 4.5-inch substitution.",
}


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def canonical(value):
    return sha(json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode())


def json_value(raw):
    def unique(pairs):
        result = dict(pairs)
        require(len(result) == len(pairs), "duplicate JSON property")
        return result
    def invalid(value):
        raise AssertionError("nonfinite JSON constant: " + value)
    return json.loads(raw, object_pairs_hook=unique, parse_constant=invalid)


def reference(path):
    raw = path.read_bytes()
    return {"path": str(path.relative_to(ROOT)), "sha256": sha(raw), "bytes": len(raw)}


def read_ref(ref):
    path = ROOT / ref["path"]
    raw = path.read_bytes()
    require(sha(raw) == ref["sha256"] and ("bytes" not in ref or len(raw) == ref["bytes"]), "source reference changed: " + ref["path"])
    return raw


def verify(pins):
    for path, expected in pins.items():
        with (ROOT / path).open("rb") as handle:
            require(hashlib.file_digest(handle, "sha256").hexdigest() == expected, "source closure drift: " + path)


def table(raw):
    reader = csv.DictReader(io.StringIO(raw.decode()))
    rows = list(reader)
    require(reader.fieldnames and len(set(reader.fieldnames)) == len(reader.fieldnames), "duplicate CSV column")
    require(all(None not in row and None not in row.values() for row in rows), "CSV width mismatch")
    require(reader.fieldnames[-2:] == ["Actual", "Disposition"], "observation suffix")
    cells = [v for row in rows for k, v in row.items() if k.startswith("Actual") or k == "Disposition"]
    require(all(v == "" for v in cells), "nonblank Actual/Disposition")
    return reader.fieldnames, rows, len(cells)


def identity(rows, fields):
    mapped = {tuple(row[k] for k in fields): row for row in rows}
    require(len(mapped) == len(rows), "duplicate saved identity")
    return mapped


def vector(row, prefix, axes="xyz", suffix="mm"):
    return [float(row[f"{prefix}_{c}_{suffix}"]) for c in axes]


def error(actual, expected):
    require(len(actual) == len(expected), "coordinate dimensions")
    require(all(math.isfinite(v) for v in (*actual, *expected)), "nonfinite coordinate")
    return max(abs(a-b) for a, b in zip(actual, expected, strict=True))


def local(point, profile):
    return [math.fsum((p-o)*v for p, o, v in zip(point, profile["datum_xyz_mm"], direction, strict=True))
            for direction in profile["basis_grain_u_v_xyz"]]


def audit_svg(name, old_raw, new_raw, profiles, old_holes, holes, parent_axes, axes):
    """Check persisted XML coordinates and every unchanged element; no renderer."""
    old, new = ET.fromstring(old_raw), ET.fromstring(new_raw)
    require(old.tag == new.tag == "{http://www.w3.org/2000/svg}svg", "SVG namespace/root")
    old_nodes, new_nodes = list(old.iter()), list(new.iter())
    require(len(old_nodes) == len(new_nodes), "SVG element census")
    circles = [i for i, node in enumerate(old_nodes) if node.tag.endswith("}circle")]
    expected_old, expected_new = [], []
    if name.startswith("member-projections"):
        page = int(name.split("-")[2].split(".")[0])-1
        for slot, host in enumerate(sorted(profiles)[page*7:(page+1)*7]):
            points = [(v[0], v[2]) for v in profiles[host]["vertices_luv_mm"]]
            xmin, xmax = min(p[0] for p in points), max(p[0] for p in points)
            zmin, zmax = min(p[1] for p in points), max(p[1] for p in points)
            scale = min(1050/max(xmax-xmin, 1), 78/max(zmax-zmin, 1))
            for rows, expected in ((old_holes, expected_old), (holes, expected_new)):
                for row in rows:
                    if row["receiver"] == host:
                        p = vector(row, "entry_in_receiver", "luv")
                        expected.append((40+(p[0]-xmin)*scale, 155+slot*155+(p[2]-zmin)*scale))
    else:
        for source, expected in ((parent_axes, expected_old), (axes, expected_new)):
            for axis in source.values():
                if "eoere_cleat_left" in axis["receivers"]:
                    _, y, z = axis["point_xyz_mm"]
                    expected.append((80+(y+175.7)*1.2, 535-(z-139.7)*1.2))
    require(len(circles) == len(expected_old) == len(expected_new), "SVG target census")
    geometry = {}
    for index, (x, y), (nx, ny) in zip(circles, expected_old, expected_new, strict=True):
        require(error([float(old_nodes[index].attrib["cx"]), float(old_nodes[index].attrib["cy"])], [x, y]) <= 5.1e-5, "old SVG projection datum")
        geometry[index] = {"cx": nx, "cy": ny}
        geometry[index+1] = {"x1": nx-8, "x2": nx+8, "y1": ny, "y2": ny}
        geometry[index+2] = {"x1": nx, "x2": nx, "y1": ny-8, "y2": ny+8}
        geometry[index+3] = {"x": nx+10, "y": ny-5}
        if name == "extended-cleats.svg":
            geometry[index+4] = {"x1": nx, "y1": ny}
    changes = 0
    for i, (before, after) in enumerate(zip(old_nodes, new_nodes, strict=True)):
        require(before.tag == after.tag and set(before.attrib) == set(after.attrib), "SVG shape/style schema")
        for key, value in before.attrib.items():
            if key in geometry.get(i, {}):
                require(abs(float(after.attrib[key])-geometry[i][key]) <= 5.1e-5, "saved SVG target coordinate")
            else:
                require(after.attrib[key] == value, "unexpected SVG attribute change")
        text = CAPTIONS.get(before.text, before.text)
        if name.startswith("member-projections") and text and text.startswith("Extended-cleat frame: nominal member projections"):
            text = text.replace("Extended-cleat frame", "Unadopted Z180 proposal")
        require(after.text == text and after.tail == before.tail, "SVG caption/text change")
        changes += before.attrib != after.attrib or before.text != after.text
    return {"elements": len(new_nodes), "targets_checked": len(circles), "changed_elements": changes}


def main():
    raw = {name: (OUT/name).read_bytes() for name in PINS}
    require(all(sha(raw[name]) == expected for name, expected in PINS.items()), "issued trial record changed")
    result, process = json_value(raw["result.json"]), json_value(raw["process.json"])
    inp = json_value((SHOP/"inputs.json").read_bytes())
    require(result["schema"] == "eoere_z180_proposal_nominal_shop/v1"
            and process["schema"] == "eoere_z180_proposal_shop_trial_process/v1"
            and inp["schema"] == "eoere_z180_proposal_shop_frozen_inputs/v1", "exact saved trial schemas")
    require(sha((SHOP/"inputs.json").read_bytes()) == "24168aba426c8a3e65035e877b03fc58347a3c00f450980cba9319f4d6e19918", "frozen inputs changed")
    require(set(result["files"]) == CANDIDATES and set(process["outputs"]) == CANDIDATES | {"result.json"}, "ten-output manifest census")
    for name in CANDIDATES:
        require(not (OUT/name).is_symlink(), "issued output is an alias")
        raw[name] = (OUT/name).read_bytes()
        require(result["files"][name] == {"sha256": sha(raw[name]), "bytes": len(raw[name])}, "issued output hash/size")
        require(reference(OUT/name) == process["outputs"][name], "process output reference")
    require(reference(OUT/"result.json") == process["outputs"]["result.json"] and reference(OUT/"reproduce.py") == process["reproduction_driver"], "trial provenance records")
    require(sum(len(raw[n]) for n in CANDIDATES) == process["candidate_byte_volume"] == 348024
            and sum(len(raw[n]) for n in CANDIDATES | {"result.json"}) == process["candidate_plus_result_byte_volume"] == 528273, "saved byte volume")
    sources = {key: read_ref(value) for key, value in inp["sources"].items()}
    old = {name: read_ref(value) for name, value in inp["saved_files"].items()}
    descriptor, native, parent, layout = (json_value(sources[k]) for k in ("descriptor", "native", "parent_geometry", "layout"))
    old_profiles, profiles = json_value(old["current_profiles.json"]), json_value(raw["current_profiles.json"])
    pins = {str((SHOP/"inputs.json").relative_to(ROOT)): sha((SHOP/"inputs.json").read_bytes())}
    refs = [inp["helper"], *inp["sources"].values(), *inp["saved_files"].values(), *(p["finished"] for p in old_profiles.values())]
    for path, expected in [(r["path"], r["sha256"]) for r in refs] + list(descriptor["source_sha256"].items()):
        require(path not in pins or pins[path] == expected, "source pin conflict")
        pins[path] = expected
    require(pins == result["source_sha256"] and len(pins) == 1141 and canonical(pins) == CLOSURE, "independent source closure join")
    require(process["source_closure_before"] == process["source_closure_after"]
            == {"all_exact": True, "canonical_sha256": CLOSURE, "pin_count": 1141}, "process source closure claims")
    verify(pins)
    reviews = {}
    for lane, value in process["review_receipts"].items():
        review = json_value(read_ref(value))
        require(review["findings"] == [], "prior review finding")
        helper = review.get("helper", review.get("review_helper"))
        if helper is None:
            helper = {"path": review["review_artifacts"]["helper"], "sha256": review["review_artifacts"]["helper_sha256"]}
        read_ref(helper)
        reviews[lane] = {"receipt": value, "helper": helper, "status": review["status"]}
    require(set(reviews) == {"correctness", "testing", "structure"}, "three frozen reviews")
    axes = {s["axis_id"]: s["source_axis"] for s in descriptor["shafts"]}
    parent_axes = {axis["id"]: axis for axis in parent["axes"]}
    require(len(axes) == len(parent_axes) == 100 and {a["id"] for a in layout["proposed_axes"]} == AXES, "axis source census")
    require(result["proposal"] == inp["sources"]["layout"] and result["descriptor"] == inp["sources"]["descriptor"]
            and result["parent_shop_result"] == inp["sources"]["old_result"], "distinct proposal/descriptor/parent namespaces")
    tables = {name: table(raw[name]) for name in CANDIDATES if name.endswith(".csv")}
    prior = {name: table(old[name]) for name in tables}
    require({name: len(value[1]) for name, value in tables.items()} == {"members.csv": 28, "receiver-holes.csv": 120, "bolt-stacks.csv": 100, "access-sides.csv": 200}, "saved CSV census")
    allowed = {
        "members.csv": {"current_finished_source_path", "current_finished_source_sha256"},
        "receiver-holes.csv": {"source"} | {"axis_point_"+c+"_mm" for c in "xyz"}
            | {p+"_in_receiver_"+c+"_mm" for p in ("axis_point", "entry", "exit") for c in "luv"},
        "bolt-stacks.csv": {"geometry_axis_pointer", "current_station_translated"},
        "access-sides.csv": {"axis_origin_xyz_mm", "nominal_bearing_face_xyz_mm", "nominal_outboard_face_xyz_mm", "nominal_tip_xyz_mm", "current_station_translated"},
    }
    changed = {}
    for name, (columns, rows, _) in tables.items():
        require(columns == prior[name][0] and len(rows) == len(prior[name][1]), "protected CSV columns/order")
        changed[name] = []
        for line, (before, after) in enumerate(zip(prior[name][1], rows, strict=True), start=2):
            fields = {key for key in columns if before[key] != after[key]}
            require(fields <= allowed[name], "protected saved field changed")
            if fields:
                changed[name].append(line)
    require(changed["receiver-holes.csv"] == sorted([*range(90, 98), 69, 73, 75, 79, 106, 108, 110, 112])
            and changed["bolt-stacks.csv"] == [86, 87, 88, 89] and changed["access-sides.csv"] == list(range(170, 178)), "exact changed row locations")
    bindings, role_data = json_value(raw["source-bindings.json"]), json_value(raw["hardware-role-locations.json"])
    require(bindings["schema"] == "eoere_z180_proposal_shop_source_bindings/v1"
            and role_data["schema"] == "eoere_z180_proposal_shop_role_locations/v1", "own output schemas")
    scenario = next(s for s in native["scenarios"] if s["scenario"] == "proposed_Z180_modeled")
    observations = {o["id"]: o for o in descriptor["finished_body_observations"]}
    require(set(profiles) == set(old_profiles) and len(profiles) == 28, "28 profile identities")
    require(set(bindings["finished_members"]) == HOSTS, "four finished bindings")
    members = identity(tables["members.csv"][1], ("member",))
    for host, profile in profiles.items():
        require({k: v for k, v in profile.items() if k != "finished"} == {k: v for k, v in old_profiles[host].items() if k != "finished"}, "raw profile/datums changed")
        row = members[host,]
        require(row["profile_source"] == "current_profiles.json#/"+host and row["current_finished_source_path"] == profile["finished"]["path"]
                and row["current_finished_source_sha256"] == profile["finished"]["sha256"], "own member/profile pointer")
        if host not in HOSTS:
            require(profile == old_profiles[host], "unchanged finished profile")
            continue
        body, finished, observation = scenario["finished_bodies"][host], profile["finished"], observations[host]
        require(finished == bindings["finished_members"][host], "finished binding pointer")
        require(finished["id"] == host and all(finished[k] == body[k] for k in ("path", "sha256", "bytes", "volume_mm3", "bounds_xyz_mm")), "saved native geometry facts")
        require(finished["analytic_center_xyz_mm"] == observation["center_xyz_mm"]
                and finished["analytic_center_source"] == {"descriptor": inp["sources"]["descriptor"], "observation_id": host, "native_COM_query_performed": False}
                and not {"center_xyz_mm", "center_of_mass_xyz_mm", "strict_native_geometry"}.intersection(finished), "separate analytic COM claim")
        require(finished["saved_native_geometry_source"] == {"result": inp["sources"]["native"], "scenario": "proposed_Z180_modeled", "receiver": host}, "native geometry provenance")
    holes = identity(tables["receiver-holes.csv"][1], ("axis_id", "receiver"))
    old_holes = identity(prior["receiver-holes.csv"][1], ("axis_id", "receiver"))
    own_keys = {key for key in holes if key[1] in HOSTS}
    require(len(holes) == 120 and set(bindings["receiver_holes"]) == {"|".join(k) for k in own_keys} and len(own_keys) == 16, "16 own wall bindings")
    maximum = {"world_axis_mm": 0., "local_mm": 0., "saved_interval_mm": 0., "access_mm": 0.}
    for key, row in holes.items():
        axis, profile = axes[key[0]], profiles[key[1]]
        maximum["world_axis_mm"] = max(maximum["world_axis_mm"], error(vector(row, "axis_point"), axis["point_xyz_mm"]))
        require(error(vector(row, "axis_direction", suffix="unitless"), axis["direction_xyz"]) <= 1e-6, "installed hole direction")
        for label, scalar in (("axis_point", 0.), ("entry", float(row["entry_from_axis_point_mm"])), ("exit", float(row["exit_from_axis_point_mm"]))):
            point = [p+scalar*d for p, d in zip(axis["point_xyz_mm"], axis["direction_xyz"], strict=True)]
            maximum["local_mm"] = max(maximum["local_mm"], error(vector(row, label+"_in_receiver", "luv"), local(point, profile)))
        if key not in own_keys:
            require(row == old_holes[key], "untouched receiver row")
            continue
        binding = bindings["receiver_holes"]["|".join(key)]
        wall = scenario["wall_queries"][binding["saved_native_wall_query_index"]]
        require(row["source"] == "source-bindings.json#/receiver_holes/"+"|".join(key)
                and (wall["axis_id"], wall["receiver"]) == key and binding["saved_native_result"] == inp["sources"]["native"]
                and binding["scenario"] == "proposed_Z180_modeled" and binding["native_query_performed_now"] is False
                and binding["complete_joint_bearing_or_pressure_qualified"] is False and binding["axis_moved"] == (key[0] in AXES), "wall source pointer/meaning")
        require(binding["parent_csv_line"] == prior["receiver-holes.csv"][1].index(old_holes[key])+2
                and binding["finished_source"] == {k: scenario["finished_bodies"][key[1]][k] for k in ("path", "sha256")}, "wall parent/own body reference")
        interval = [float(row[s+"_from_axis_point_mm"]) for s in ("entry", "exit")]
        maximum["saved_interval_mm"] = max(maximum["saved_interval_mm"], error(interval, wall["full_wall_intervals_mm"][0]))
        require(len(wall["full_wall_intervals_mm"]) == 1 and wall["partial_wall_present"] is False
                and wall["bore_diameter_mm"] == float(row["modeled_bore_envelope_diameter_mm"]), "saved own full wall recipe")
        if key[0] not in AXES:
            require({k: v for k, v in row.items() if k != "source"} == {k: v for k, v in old_holes[key].items() if k != "source"}, "retained wall numeric fact changed")
    stacks = identity(tables["bolt-stacks.csv"][1], ("axis_id",))
    require(len(stacks) == 100 and set(stacks) == {(k,) for k in axes}, "100 stack identities")
    for axis_id in AXES:
        row = stacks[axis_id,]
        prefix, number = row["geometry_axis_pointer"].rsplit("/", 1)
        require(prefix == "proposal#/proposed_axes" and layout["proposed_axes"][int(number)] == axes[axis_id]
                and float(row["nominal_underhead_length_mm"]) == 101.6 and row["head_side_plate_mm"] == row["nut_side_plate_mm"] == "0", "four original4in/no-spacer stack pointers")
    access = identity(tables["access-sides.csv"][1], ("axis_id", "side"))
    old_access = identity(prior["access-sides.csv"][1], ("axis_id", "side"))
    require(len(access) == 200 and set(access) == {(axis, side) for axis in axes for side in ("head", "nut")}, "200 installed sides")
    for key, row in access.items():
        if key[0] in AXES:
            for column in ("axis_origin_xyz_mm", "nominal_bearing_face_xyz_mm", "nominal_outboard_face_xyz_mm", "nominal_tip_xyz_mm"):
                target = [float(v)+shift for v, shift in zip(old_access[key][column].split(";"), [0., 0., -20.], strict=True)]
                maximum["access_mm"] = max(maximum["access_mm"], error(list(map(float, row[column].split(";"))), target))
        else:
            require(row == old_access[key], "unchanged access row")
    roles = role_data["roles"]
    require(len(roles) == len({r["id"] for r in roles}) == 20 and {r["axis_id"] for r in roles} == AXES, "20 own roles")
    for role in roles:
        parts = role["source_pointer"].split("/")
        require(parts[1] == "shafts" and parts[3] == "metal_roles", "role pointer namespace")
        shaft = descriptor["shafts"][int(parts[2])]
        require(role["axis_id"] == shaft["axis_id"] and shaft["source_axis"]["nominal_under_head_length_mm"] == 101.6
                and role["source_descriptor"] == inp["sources"]["descriptor"], "role original4in source")
        require({k: v for k, v in role.items() if k not in {"axis_id", "source_descriptor", "source_pointer", "Actual", "Disposition"}} == shaft["metal_roles"][int(parts[4])]
                and role["Actual"] == role["Disposition"] == "" and role["center_of_mass_xyz_mm"][2] == 180., "role values/observation")
    require(set(result["inherited_files_via_links"]) == INHERITED, "six drawing/five data links")
    for name, value in result["inherited_files_via_links"].items():
        require(value == inp["saved_files"][name] and read_ref(value) == old[name] and not (OUT/name).exists(), "inherited path/hash/namespace changed")
        if name.endswith(".svg"):
            require(ET.fromstring(old[name]).tag == "{http://www.w3.org/2000/svg}svg", "inherited SVG namespace")
        elif name.endswith(".csv"):
            table(old[name])
        else:
            json_value(old[name])
    require(len(table(old["panel-screw-datums.csv"])[1]) == 66 and len(table(old["panel-machining.csv"])[1]) == 340, "protected screw/feature census")
    stock = json_value(old["stock-nesting.json"])
    require(len(stock["sticks"]) == 13 and stock["nominal_board_feet"] == 150., "protected stock census")
    svg = {name: audit_svg(name, old[name], raw[name], profiles, prior["receiver-holes.csv"][1], tables["receiver-holes.csv"][1], parent_axes, axes) for name in DRAWINGS}
    require(b"Dedicated post shafts stay at Z 200.000" in old["extended-cleats.svg"] and b"HOLD those four stations" in old["extended-cleats.svg"], "original Z200 HOLD instruction changed")
    release = inp["release"]
    require(release and not any(release.values()) and all(value["release"] == release for value in (result, process, bindings, role_data)), "false release claims")
    require(result["status"] == "UNADOPTED_NOMINAL_OUTPUTS_REQUIRE_PARENT_REVIEW"
            and process["status"] == "PASS_SAVED_NOMINAL_SHOP_OUTPUT_TRIAL_UNADOPTED"
            and result["old_Z200_build_or_HOLD_contract_relabelled"] is False and process["old_Z200_HOLD_authority_changed"] is False
            and process["spacer_or_4p5in_recipe_adopted"] is False and result["fresh_force_acceptance_or_tool_access_claimed"] is False, "unadopted scope claims")
    require(max(maximum.values()) <= 1e-6 and process["build_outputs_call_count"] == 1, "saved geometry/process census")
    require(sum(value[2] for value in tables.values()) == process["validation"]["candidate_actual_disposition_cells_blank"] == 3296, "blank observation census")
    verify(pins)
    for name, value in raw.items():
        require((OUT/name).read_bytes() == value, "issued bytes drifted during audit")
    for value in process["review_receipts"].values():
        read_ref(value)
    for value in reviews.values():
        read_ref(value["helper"])
    receipt = {"schema": "eoere_z180_proposal_shop_saved_output_independent_review/v1", "status": "independent_saved_nominal_shop_bytes_checks_pass",
        "helper": reference(OWN), "trial_records": {name: reference(OUT/name) for name in PINS}, "outputs": {name: reference(OUT/name) for name in sorted(CANDIDATES)},
        "reused_frozen_reviews": reviews, "findings": [], "source_closure": {"pin_count": len(pins), "canonical_sha256": canonical(pins), "verified_before_after": True, "drift": []},
        "checks": {"candidate_byte_volume": 348024, "candidate_plus_result_byte_volume": 528273, "CSV_counts": {n: len(t[1]) for n, t in tables.items()},
            "blank_candidate_observation_cells": 3296, "blank_role_observation_cells": 40, "all_protected_fields_preserved": True,
            "changed_CSV_lines": changed, "own_wall_pointers": 16, "moved_wall_pointers": 8, "retained_wall_numeric_facts_preserved": 8,
            "access_translations": 8, "original4in_no_spacer_role_pointers": 20, "separate_native_volume_and_analytic_COM_records": 4,
            "inherited_drawings": 6, "inherited_data_links": 5, "preserved_profiles_sticks_board_feet_screws_features": [28, 13, 150, 66, 340],
            "maximum_coordinate_errors_mm": maximum, "saved_SVG_checks": svg, "old_Z200_HOLD_authority_unchanged": True,
            "namespaces": "Own members/proposal/walls/roles resolve to own profiles/layout/bindings/descriptor; unchanged row fields and inherited file references retain their authenticated original Z200 namespace."},
        "release": release, "helper_validation": "Ruff passed before freezing; issued-byte assertions pass without imports or replay",
        "execution": {"prepare_calls": 0, "build_outputs_calls": 0, "reproduce_driver_calls": 0, "CAD_native_global_panel_reducers_or_solve": False},
        "limits": ["Saved bytes audited without generation or replay; process execution counts and equality of unpersisted six drawing intermediates remain the frozen process's recorded claims.",
            "Exact inherited drawing references and all three persisted drawing target projections were independently checked.",
            "An unadopted nominal proposal only; no physical observation, machining/tool access, force/resistance, readiness or acceptance inference."]}
    receipt_path = OWN.with_name("receipt.json")
    if "--issue" in sys.argv:
        with receipt_path.open("xb") as handle:
            handle.write((json.dumps(receipt, sort_keys=True, indent=2, allow_nan=False)+"\n").encode())
    print(json.dumps({"status": receipt["status"], "helper": reference(OWN), "receipt": reference(receipt_path) if receipt_path.exists() else None,
        "source_closure": receipt["source_closure"], "checks": receipt["checks"]}, indent=2))


if __name__ == "__main__":
    main()
