"""Source-only saved-table adapter for the unadopted nominal Z180 proposal.

prepare() authenticates saved inputs. build_outputs() is a deferred pure API:
it must not be called on genuine inputs until parent authorizes an output trial.
The old Z200 build/equality/HOLD contract is never invoked or weakened. Only
explicitly selected, authenticated pure functions are reused from its source.
There is no CLI, CAD import, native query, mechanics or physical release.
"""
from __future__ import annotations

import ast
import copy
import csv
import hashlib
import html
import io
import json
from pathlib import Path
from types import SimpleNamespace

OWN = Path(__file__).resolve()
ROOT = next(p for p in OWN.parents if (p / "AGENTS.md").is_file())
INPUT_SCHEMA = "eoere_z180_proposal_shop_frozen_inputs/v1"
SCHEMA = "eoere_z180_proposal_nominal_shop/v1"
AXES = tuple("cleat_post_bolt_"+side+"_"+str(i) for side in ("left", "right") for i in (1, 2))
HOSTS = {"base_post_outer_left", "base_post_outer_right", "eoere_cleat_left", "eoere_cleat_right"}
CHANGED_DRAWINGS = {"member-projections-1.svg", "member-projections-3.svg", "extended-cleats.svg"}
REUSED_DRAWINGS = {"member-projections-2.svg", "member-projections-4.svg", "rear-recess.svg",
    "panel-layout-1.svg", "panel-layout-2.svg", "paired-drilling-fixture.svg"}
UNCHANGED_FILES = {"member-end-datums.csv", "panel-screw-datums.csv", "panel-machining.csv",
    "stock-nesting.json", "rear-recesses.json"}
RELEASE = {key: False for key in ("geometry_adopted", "drilling", "fabrication", "climbing",
    "physical_observations", "complete_joint_acceptance")}
DRAWING_CAPTIONS = {
    "Both exterior cleats: sloped top / runner seat": "Unadopted Z180 proposal: exterior cleats",
    "Dedicated post shafts stay at Z 200.000 in the reviewed model.": "Proposal only: four dedicated post shafts at Z 180.000 mm.",
    "HOLD those four stations: nominal bore/screw gap only 0.341 mm.": "Unadopted layout; drilling and fabrication remain unreleased.",
    "No axis move, hole diameter or woodworking tolerance adopted here.": "Same nominal 4-inch bolts; no spacer or 4.5-inch substitution.",
}
OPEN_INPUTS = [
    "Proposal adoption and its own operation instructions remain absent; current Z200/HOLD instructions keep their source binding.",
    "Own end/edge/net-section and complete-joint resistance remain unresolved; native full walls or analytic COM do not establish strength.",
    "No Z180 admitted load/end-demand packet is consumed here; current Z200 forces and passes are not transferred.",
    "Actual saw/drill/bit/guide/clamp envelopes, supported reach, registration, placement errors and finishing-tool allowances remain unresolved.",
    "Delivered 4-inch bolt shank/runout, washer/nut seating, actual sections and assembled fit remain unobserved; the separate spacer/long-bolt study is excluded.",
    "All 200 installed head/nut tool/removal sides remain unverified. Actual and Disposition cells stay blank.",
]


def require(condition, message):
    if not condition:
        raise ValueError(message)


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def canonical(value):
    return digest(json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode())


def read_ref(ref):
    require(set(ref) == {"path", "sha256"} and not Path(ref["path"]).is_absolute(), "exact relative reference required")
    path = (ROOT / ref["path"]).resolve()
    require(path.is_relative_to(ROOT), "foreign source reference")
    raw = path.read_bytes()
    require(digest(raw) == ref["sha256"], "source bytes differ: " + ref["path"])
    return raw


def verify(pins):
    # Authenticated descriptor closure includes two original absolute paths.
    # Keep their exact spelling/provenance; do not create relative aliases.
    for path, expected in pins.items():
        with (ROOT / path).open("rb") as handle:
            require(hashlib.file_digest(handle, "sha256").hexdigest() == expected, "source closure differs: " + path)


def join(pins, additions):
    for path, expected in additions.items():
        require(path not in pins or pins[path] == expected, "source pin conflict: " + path)
        pins[path] = expected


def index(rows, fields):
    result = {tuple(row[k] for k in fields): row for row in rows}
    require(len(result) == len(rows), "duplicate identity: " + "/".join(fields))
    return result


def selected_functions(raw, names, *, captions=False):
    """Called only with bytes just authenticated by read_ref()."""
    tree = ast.parse(raw)
    chosen = [copy.deepcopy(node) for node in tree.body if isinstance(node, (ast.FunctionDef, ast.ClassDef)) and node.name in names]
    require({n.name for n in chosen} == set(names) and len(chosen) == len(names), "exact pure function/class selection required")
    if captions:
        for before, after in DRAWING_CAPTIONS.items():
            matches = [n for node in chosen for n in ast.walk(node) if isinstance(n, ast.Constant) and n.value == before]
            require(len(matches) == 1, "exact saved Z200 drawing caption seam required: " + before)
            matches[0].value = after
    namespace = {"csv": csv, "io": io, "json": json, "hashlib": hashlib, "html": html}
    exec(compile(ast.fix_missing_locations(ast.Module(body=chosen, type_ignores=[])), "authenticated-pure-shop-functions", "exec"), namespace)  # noqa: S102 -- authenticated source, exact selections
    return SimpleNamespace(**{name: namespace[name] for name in names})


def reusable_methods(sources):
    shop = selected_functions(read_ref(sources["old_export"]), ("require", "sha", "canonical", "table", "vector", "put", "drawings"), captions=True)
    datum = selected_functions(read_ref(sources["datum_helper"]), ("require", "dot", "add", "subtract", "scale", "local", "world", "json_bytes", "csv_bytes"))
    draw = selected_functions(read_ref(sources["drawing_helper"]), ("hull", "SVG"))
    return shop, datum, draw


def blank_observations(rows):
    require(all(value == "" for row in rows for key, value in row.items() if key.startswith("Actual") or key == "Disposition"), "actual observation/disposition supplied")


def prepare(inputs_path, inputs_sha256):
    """Authenticate source metadata only; no candidate tables or SVGs created."""
    path = Path(inputs_path).resolve()
    raw = path.read_bytes()
    require(path.is_relative_to(ROOT) and digest(raw) == inputs_sha256, "frozen input bytes differ")
    inp = json.loads(raw)
    require(inp["schema"] == INPUT_SCHEMA and inp["release"] == RELEASE, "distinct unreleased shop input required")
    require(read_ref(inp["helper"]) == OWN.read_bytes() and (ROOT / inp["helper"]["path"]).resolve() == OWN, "exact shop adapter required")
    pins = {str(path.relative_to(ROOT)): inputs_sha256, inp["helper"]["path"]: inp["helper"]["sha256"]}
    encoded, data = {}, {}
    for key, ref in inp["sources"].items():
        encoded[key] = read_ref(ref)
        join(pins, {ref["path"]: ref["sha256"]})
        if ref["path"].endswith(".json"):
            data[key] = json.loads(encoded[key])
    shop, datum, draw = reusable_methods(inp["sources"])
    require(data["old_result"]["schema"] == "eoere_extended_cleat_shop_followup/v1"
            and data["old_result"]["revision"] == "eoere-base-side-edge-cleats-v1"
            and data["old_result"]["helper_sha256"] == inp["sources"]["old_export"]["sha256"]
            and data["old_result"]["inputs_sha256"] == inp["sources"]["old_inputs"]["sha256"], "issued Z200 shop provenance differs")
    require(set(inp["saved_files"]) == set(data["old_result"]["files"])
            == UNCHANGED_FILES | REUSED_DRAWINGS | CHANGED_DRAWINGS
            | {"members.csv", "receiver-holes.csv", "bolt-stacks.csv", "access-sides.csv", "current_profiles.json"}, "exact issued19 saved files required")
    for filename, ref in inp["saved_files"].items():
        raw = read_ref(ref)
        require(digest(raw) == data["old_result"]["files"][filename]["sha256"]
                and len(raw) == data["old_result"]["files"][filename]["bytes"], "saved result/file join differs: " + filename)
        join(pins, {ref["path"]: ref["sha256"]})
        encoded[filename] = raw
    for filename in ("members.csv", "receiver-holes.csv", "bolt-stacks.csv", "access-sides.csv", "panel-screw-datums.csv", "panel-machining.csv"):
        data[filename] = shop.table(encoded[filename])
        blank_observations(data[filename][1])
    data["profiles"] = json.loads(encoded["current_profiles.json"])
    data["stock"] = json.loads(encoded["stock-nesting.json"])
    data["recesses"] = json.loads(encoded["rear-recesses.json"])
    join(pins, data["descriptor"]["source_sha256"])
    for source in data["profiles"].values():
        f = source["finished"]
        join(pins, {f["path"]: f["sha256"]})
    verify(pins)
    bundle = {"inputs": inp, "data": data, "encoded": encoded, "pins": pins, "shop": shop, "datum": datum, "draw": draw}
    validate_join(bundle)
    verify(pins)
    return bundle


def validate_join(bundle):
    data, inp = bundle["data"], bundle["inputs"]
    parent, layout, descriptor = (data[k] for k in ("parent_geometry", "layout", "descriptor"))
    require(layout["schema"] == "eoere_lower_cleat_z180_geometry_patch/v1" and layout["revision"] == "eoere-lower-cleat-z180-proposal-v1"
            and layout["optional_2026_extra"] is False and not any(layout["release"].values()), "unadopted OFF proposal required")
    require(descriptor["schema"] == "eoere_z180_geometry_delta_descriptors/v1" and descriptor["geometry"] == inp["sources"]["layout"]
            and descriptor["parent_geometry"] == inp["sources"]["parent_geometry"] == layout["parent_geometry"]
            and descriptor["source_pins_before_after_unchanged"] and not any(descriptor["release"].values())
            and descriptor["current_4in_hardware_retained_spacer_proposal_excluded"], "exact source-only descriptor binding required")
    old_axes = {a["id"]: a for a in parent["axes"]}
    new_axes = {s["axis_id"]: s["source_axis"] for s in descriptor["shafts"]}
    proposed = {a["id"]: a for a in layout["proposed_axes"]}
    require(len(old_axes) == len(parent["axes"]) == len(new_axes) == len(descriptor["shafts"]) == 100
            and len(layout["proposed_axes"]) == len(proposed) == 4 and set(proposed) == set(AXES), "four unique proposal/100shaft join required")
    expected = copy.deepcopy(old_axes)
    for name in AXES:
        expected[name]["point_xyz_mm"][2] -= 20.
        require(proposed[name] == expected[name] and proposed[name]["nominal_under_head_length_mm"] == 101.6
                and proposed[name]["bore_diameter_mm"] == 10.31875 and proposed[name]["attachments"] == [], "only four Z180 axes with original4in recipe permitted")
    require(new_axes == expected, "unchanged96 or translated4 source axes differ")
    profiles = data["profiles"]
    require(len(profiles) == len(data["members.csv"][1]) == 28 and len(data["receiver-holes.csv"][1]) == 120
            and len(data["bolt-stacks.csv"][1]) == 100 and len(data["access-sides.csv"][1]) == 200
            and len(data["panel-screw-datums.csv"][1]) == len(descriptor["hillman_rows"]) == 66
            and len(data["panel-machining.csv"][1]) == 340 and len(data["stock"]["sticks"]) == 13
            and data["stock"]["nominal_board_feet"] == 150., "protected nominal shop census differs")
    observations = {r["id"]: r for r in descriptor["finished_body_observations"]}
    require(len(descriptor["finished_body_observations"]) == len(observations) == 28
            and set(observations) == set(profiles), "28 finished/profile identities differ")
    scenario = next(r for r in data["native"]["scenarios"] if r["scenario"] == "proposed_Z180_modeled")
    require(len(scenario["wall_queries"]) == 16, "16 saved changed-host wall occurrences required")
    for host in HOSTS:
        own = observations[host]
        require(own["source_only_analytic_centroid"] is True and own["provenance"]["new_native_COM_query_performed"] is False
                and own["provenance"]["saved_native_receiver_evidence"]["result"] == inp["sources"]["native"]
                and source_ref(own["source"]) == source_ref(scenario["finished_bodies"][host])
                and source_ref(profiles[host]["finished"]) == own["provenance"]["old_COM_observation_source"]["finished_source"],
                "four finished sources require own native geometry and separate analytic COM")
    for host in set(profiles)-HOSTS:
        require(source_ref(profiles[host]["finished"]) == source_ref(observations[host]["source"]), "unchanged finished source differs")
    bundle.update(old_axes=old_axes, new_axes=new_axes, observations=observations, scenario=scenario)


def source_ref(value):
    return {key: value[key] for key in ("path", "sha256")}


def replacement_finished(host, observation, native_body, descriptor_ref, native_ref):
    require(observation["source_only_analytic_centroid"] is True and observation["provenance"]["new_native_COM_query_performed"] is False
            and source_ref(observation["source"]) == source_ref(native_body), "own analytic COM/source binding required")
    return {"id": host, **{key: copy.deepcopy(native_body[key]) for key in ("path", "sha256", "bytes", "volume_mm3", "bounds_xyz_mm")},
        "analytic_center_xyz_mm": copy.deepcopy(observation["center_xyz_mm"]),
        "analytic_center_source": {"descriptor": descriptor_ref, "observation_id": host, "native_COM_query_performed": False},
        "saved_native_geometry_source": {"result": native_ref, "scenario": "proposed_Z180_modeled", "receiver": host}}


def update_hole(row, axis, profile, wall, *, moved, shop, datum, tolerance):
    require(row["axis_id"] == wall["axis_id"] and row["receiver"] == wall["receiver"]
            and len(wall["full_wall_intervals_mm"]) == 1 and wall["partial_wall_present"] is False
            and wall["matching_cylindrical_faces"] and all(f["full_circumference_wall"] for f in wall["matching_cylindrical_faces"]), "own full saved wall join required")
    interval = [float(row[f"{side}_from_axis_point_mm"]) for side in ("entry", "exit")]
    require(all(abs(a-b) <= tolerance for a, b in zip(interval, wall["full_wall_intervals_mm"][0], strict=True))
            and float(row["modeled_bore_envelope_diameter_mm"]) == wall["bore_diameter_mm"] == axis["bore_diameter_mm"], "saved interval/bore recipe differs")
    require(wall["query_point_xyz_mm"] == axis["point_xyz_mm"] and wall["query_direction_xyz"] == axis["direction_xyz"], "new saved wall point/direction differs")
    require(shop.vector(row, "axis_direction", suffix="unitless") == axis["direction_xyz"]
            and abs(float(row["saved_full_wall_length_mm"])-(interval[1]-interval[0])) <= tolerance
            and abs(wall["full_wall_length_mm"]-(interval[1]-interval[0])) <= tolerance, "saved wall length/direction differs")
    if moved:
        shop.put(row, "axis_point", axis["point_xyz_mm"])
        for label, point in (("axis_point", axis["point_xyz_mm"]), ("entry", datum.add(axis["point_xyz_mm"], datum.scale(axis["direction_xyz"], interval[0]))),
                             ("exit", datum.add(axis["point_xyz_mm"], datum.scale(axis["direction_xyz"], interval[1])))):
            shop.put(row, label+"_in_receiver", datum.local(point, profile["datum_xyz_mm"], profile["basis_grain_u_v_xyz"]), "luv")
    else:
        require(all(abs(a-b) <= tolerance for a, b in zip(shop.vector(row, "axis_point"), axis["point_xyz_mm"], strict=True)), "retained axis point differs")
    row["source"] = "source-bindings.json#/receiver_holes/"+row["axis_id"]+"|"+row["receiver"]


def shift_access(row, old_axis, new_axis, datum):
    require(float(new_axis["nominal_under_head_length_mm"]) == 101.6 and new_axis["receivers"] == old_axis["receivers"]
            and new_axis["direction_xyz"] == old_axis["direction_xyz"], "unchanged4in access recipe required")
    require(list(map(float, row["axis_origin_xyz_mm"].split(";"))) == old_axis["point_xyz_mm"], "old access origin differs")
    delta = datum.subtract(new_axis["point_xyz_mm"], old_axis["point_xyz_mm"])
    require(delta == [0., 0., -20.], "exact Z180 translation required")
    for key in ("axis_origin_xyz_mm", "nominal_bearing_face_xyz_mm", "nominal_outboard_face_xyz_mm", "nominal_tip_xyz_mm"):
        row[key] = ";".join(format(v, ".12g") for v in datum.add(list(map(float, row[key].split(";"))), delta))
    row["current_station_translated"] = "True"


def rendering_inputs(screw_table, machining_table):
    """Restore saved CSV scalar types for the original pure renderer only."""
    screw_columns, saved_screws = screw_table
    require(screw_columns[-2:] == ["Actual", "Disposition"], "saved screw observation columns differ")
    screws = copy.deepcopy(saved_screws)
    for row in screws:
        require(row["moved_by_rail_revision"] in ("True", "False"), "saved screw boolean differs")
        row["moved_by_rail_revision"] = row["moved_by_rail_revision"] == "True"
    columns, saved_machining = machining_table
    require(columns == ["identity", "panel", "kind", "modeled_diameter_mm", "origin_x_mm", "origin_y_mm", "origin_z_mm",
        "direction_x_unitless", "direction_y_unitless", "direction_z_unitless", "origin_in_panel_l_mm", "origin_in_panel_u_mm",
        "origin_in_panel_v_mm", "source", "Actual", "Disposition"], "exact saved machining columns required")
    machining = [[float(row[key]) if 3 <= i <= 12 else row[key] for i, key in enumerate(columns[:-2])] for row in saved_machining]
    return screws, machining


def permitted_changes(before, after, identity, changed, allowed):
    """Enforce source-joined row edits and preserve every other saved field."""
    require(before[0] == after[0] and len(before[1]) == len(after[1]), "saved table schema/census differs")
    actual = set()
    for old, new in zip(before[1], after[1], strict=True):
        key = tuple(old[k] for k in identity)
        require(set(old) == set(new) and tuple(new[k] for k in identity) == key, "saved row identity/order differs")
        fields = {field for field in old if old[field] != new[field]}
        require(not fields or key in changed and fields <= allowed, "unexpected saved field edit: " + repr(key))
        if fields:
            actual.add(key)
    require(actual == changed, "exact declared changed rows required")


def verify_table_reuse(data, tables, profiles):
    members = {(host,) for host in HOSTS}
    moved = {(row["axis_id"], row["receiver"]) for row in data["receiver-holes.csv"][1] if row["axis_id"] in AXES}
    rebound = {(row["axis_id"], row["receiver"]) for row in data["receiver-holes.csv"][1] if row["receiver"] in HOSTS}-moved
    require(len(moved) == len(rebound) == 8, "eight moved/eight retained source joins required")
    permitted_changes(data["members.csv"], tables["members.csv"], ("member",), members,
                      {"current_finished_source_path", "current_finished_source_sha256"})
    holes = data["receiver-holes.csv"]
    permitted_changes(holes, tables["receiver-holes.csv"], ("axis_id", "receiver"), moved | rebound,
        {"source"} | {"axis_point_"+axis+"_mm" for axis in "xyz"}
        | {point+"_in_receiver_"+axis+"_mm" for point in ("axis_point", "entry", "exit") for axis in "luv"})
    old_by_key = index(holes[1], ("axis_id", "receiver"))
    new_by_key = index(tables["receiver-holes.csv"][1], ("axis_id", "receiver"))
    for key in rebound:
        require({k: v for k, v in old_by_key[key].items() if k != "source"}
                == {k: v for k, v in new_by_key[key].items() if k != "source"}, "retained hole numeric facts changed")
    permitted_changes(data["bolt-stacks.csv"], tables["bolt-stacks.csv"], ("axis_id",), {(axis,) for axis in AXES},
                      {"geometry_axis_pointer", "current_station_translated"})
    permitted_changes(data["access-sides.csv"], tables["access-sides.csv"], ("axis_id", "side"),
        {(axis, side) for axis in AXES for side in ("head", "nut")},
        {"axis_origin_xyz_mm", "nominal_bearing_face_xyz_mm", "nominal_outboard_face_xyz_mm", "nominal_tip_xyz_mm", "current_station_translated"})
    require(set(profiles) == set(data["profiles"]), "profile identities differ")
    for name, old in data["profiles"].items():
        require({k: v for k, v in profiles[name].items() if k != "finished"} == {k: v for k, v in old.items() if k != "finished"}, "raw profile/datums changed")
        if name not in HOSTS:
            require(profiles[name] == old, "unchanged finished profile differs")


def build_outputs(bundle):
    """DEFERRED: parent must separately authorize a genuine output trial."""
    data, inp, shop, datum, draw = (bundle[k] for k in ("data", "inputs", "shop", "datum", "draw"))
    validate_join(bundle)
    profiles = copy.deepcopy(data["profiles"])
    observations, scenario = bundle["observations"], bundle["scenario"]
    tables = {name: copy.deepcopy(data[name]) for name in ("members.csv", "receiver-holes.csv", "bolt-stacks.csv", "access-sides.csv")}
    bindings = {"schema": "eoere_z180_proposal_shop_source_bindings/v1", "receiver_holes": {}, "finished_members": {}, "release": RELEASE}
    for host in HOSTS:
        profiles[host]["finished"] = replacement_finished(host, observations[host], scenario["finished_bodies"][host], inp["sources"]["descriptor"], inp["sources"]["native"])
        bindings["finished_members"][host] = profiles[host]["finished"]
    for row in tables["members.csv"][1]:
        if row["member"] in HOSTS:
            finished = profiles[row["member"]]["finished"]
            row.update(current_finished_source_path=finished["path"], current_finished_source_sha256=finished["sha256"])
    wall_index = index(scenario["wall_queries"], ("axis_id", "receiver"))
    coordinate_tolerance = data["native_inputs"]["tolerances"]["coordinate_mm"]
    require(coordinate_tolerance == 1e-6, "recorded coordinate tolerance differs")
    moved, rebound = [], []
    for number, row in enumerate(tables["receiver-holes.csv"][1], start=2):
        if row["receiver"] not in HOSTS:
            continue
        key = row["axis_id"], row["receiver"]
        own = wall_index[key]
        is_moved = row["axis_id"] in AXES
        update_hole(row, bundle["new_axes"][row["axis_id"]], profiles[row["receiver"]], own, moved=is_moved, shop=shop, datum=datum, tolerance=coordinate_tolerance)
        bindings["receiver_holes"]["|".join(key)] = {"parent_csv_line": number, "axis_moved": is_moved,
            "saved_native_result": inp["sources"]["native"], "scenario": "proposed_Z180_modeled",
            "saved_native_wall_query_index": scenario["wall_queries"].index(own), "finished_source": source_ref(scenario["finished_bodies"][row["receiver"]]),
            "native_query_performed_now": False, "complete_joint_bearing_or_pressure_qualified": False}
        (moved if is_moved else rebound).append(number)
    require(moved == list(range(90, 98)) and rebound == [69, 73, 75, 79, 106, 108, 110, 112], "exact eight moved/eight retained source rows differ")
    proposal_indices = {a["id"]: i for i, a in enumerate(data["layout"]["proposed_axes"])}
    for row in tables["bolt-stacks.csv"][1]:
        if row["axis_id"] in AXES:
            require(float(row["nominal_underhead_length_mm"]) == 101.6, "4in stack recipe differs")
            row.update(geometry_axis_pointer="proposal#/proposed_axes/"+str(proposal_indices[row["axis_id"]]), current_station_translated="True")
    for row in tables["access-sides.csv"][1]:
        if row["axis_id"] in AXES:
            shift_access(row, bundle["old_axes"][row["axis_id"]], bundle["new_axes"][row["axis_id"]], datum)
    roles = [{"axis_id": shaft["axis_id"], **copy.deepcopy(role), "source_descriptor": inp["sources"]["descriptor"],
        "source_pointer": f"/shafts/{si}/metal_roles/{ri}", "Actual": "", "Disposition": ""}
        for si, shaft in enumerate(data["descriptor"]["shafts"]) if shaft["axis_id"] in AXES for ri, role in enumerate(shaft["metal_roles"])]
    require(len(roles) == 20 and len({r["id"] for r in roles}) == 20, "twenty unique original hardware roles required")
    verify_table_reuse(data, tables, profiles)
    outputs = {}
    for filename, (columns, rows) in tables.items():
        blank_observations(rows)
        outputs[filename] = datum.csv_bytes(columns[:-2], [[r[k] for k in columns[:-2]] for r in rows])
    outputs.update({"current_profiles.json": datum.json_bytes(profiles), "source-bindings.json": datum.json_bytes(bindings),
        "hardware-role-locations.json": datum.json_bytes({"schema": "eoere_z180_proposal_shop_role_locations/v1", "roles": roles, "release": RELEASE})})
    # This argument is a raw-profile rendering view, never a native geometry report.
    view = {"new_cleat_YZ_polygon_mm": data["parent_geometry"]["new_cleat_YZ_polygon_mm"], "axes": list(bundle["new_axes"].values())}
    screw_rendering, machining_rendering = rendering_inputs(data["panel-screw-datums.csv"], data["panel-machining.csv"])
    drawings = shop.drawings(draw, profiles, tables["receiver-holes.csv"][1], screw_rendering, machining_rendering, view, data["recesses"])
    for name in REUSED_DRAWINGS:
        require(drawings[name] == bundle["encoded"][name], "unchanged drawing datums/bytes differ: " + name)
    for name in CHANGED_DRAWINGS:
        raw = drawings[name]
        if name.startswith("member-projections-"):
            before = b"Extended-cleat frame: nominal member projections"
            require(raw.count(before) == 1, "exact member drawing title seam required")
            raw = raw.replace(before, b"Unadopted Z180 proposal: nominal member projections")
        outputs[name] = raw
    verify(bundle["pins"])
    return outputs, {"schema": SCHEMA, "status": "UNADOPTED_NOMINAL_OUTPUTS_REQUIRE_PARENT_REVIEW",
        "proposal": inp["sources"]["layout"], "parent_shop_result": inp["sources"]["old_result"], "descriptor": inp["sources"]["descriptor"],
        "source_sha256": bundle["pins"], "changed_receiver_lines": moved, "retained_receiver_source_rebinding_lines": rebound,
        "changed_stack_lines": [86, 87, 88, 89], "changed_access_lines": list(range(170, 178)),
        "inherited_files_via_links": {name: inp["saved_files"][name] for name in sorted(UNCHANGED_FILES | REUSED_DRAWINGS)},
        "inherited_file_meaning": "Exact saved Z200 files at their original paths; relative source pointers retain the original packet namespace. Same nominal datums/geometry are proved, without rebinding old observations to new solids.",
        "same_datum_geometry_reuse": {"parent_profiles": inp["saved_files"]["current_profiles.json"],
            "all28_raw_profile_fields_exact_except_finished": True,
            "six_inherited_drawing_bytes_replayed_equal": True,
            "four_new_finished_records_have_separate_analytic_COM": True},
        "files": {name: {"sha256": digest(raw), "bytes": len(raw)} for name, raw in outputs.items()},
        "station_translation_flags": "Historical raised-to-Z200 flags retained; only four additional Z200-to-Z180 stations marked. Source datums stay distinct.",
        "unchanged_28_raw_profiles_13_sticks_150bf_100_recipes_66_screws": True,
        "old_Z200_build_or_HOLD_contract_relabelled": False, "native_CAD_BREP_or_mechanics_execution": False,
        "fresh_force_acceptance_or_tool_access_claimed": False, "open_inputs": OPEN_INPUTS, "release": RELEASE}
