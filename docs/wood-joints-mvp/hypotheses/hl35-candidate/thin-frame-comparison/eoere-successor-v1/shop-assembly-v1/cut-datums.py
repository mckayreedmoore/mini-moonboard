"""Export nominal shop coordinates from pinned saved records, using stdlib only."""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import sys
from pathlib import Path

OWN = Path(__file__).resolve().parent
ROOT = next(p for p in OWN.parents if (p / "AGENTS.md").is_file())
INPUT = OWN / "cut-datums-inputs.json"


def require(condition, message):
    if not condition:
        raise ValueError(message)


def digest(data):
    return hashlib.sha256(data).hexdigest()


def dot(a, b):
    return sum(x * y for x, y in zip(a, b, strict=True))


def add(a, b):
    return [x + y for x, y in zip(a, b, strict=True)]


def subtract(a, b):
    return [x - y for x, y in zip(a, b, strict=True)]


def scale(a, value):
    return [x * value for x in a]


def cross(a, b):
    return [a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2],
            a[0] * b[1] - a[1] * b[0]]


def local(point, datum, basis):
    return [dot(subtract(point, datum), axis) for axis in basis]


def world(point, datum, basis):
    return add(datum, [sum(point[i] * basis[i][j] for i in range(3)) for j in range(3)])


def vector_names(prefix, axes="xyz", unit="mm"):
    return [f"{prefix}_{axis}_{unit}" for axis in axes]


def json_bytes(value):
    return (json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n").encode()


def csv_bytes(columns, rows):
    require(all(len(row) == len(columns) for row in rows), "CSV column alignment differs")
    buffer = io.StringIO(newline="")
    writer = csv.writer(buffer, lineterminator="\n")
    writer.writerow([*columns, "Actual", "Disposition"])
    writer.writerows([*row, "", ""] for row in rows)
    encoded = buffer.getvalue().encode()
    replay = list(csv.reader(io.StringIO(encoded.decode())))
    require(len(replay) == len(rows) + 1 and all(r[-2:] == ["", ""] for r in replay[1:]),
            "CSV census or blank observation cells differ")
    return encoded


def build():
    spec = json.loads(INPUT.read_bytes())
    sources = spec["sources"]
    payloads = {}
    for key, ref in sources.items():
        data = (ROOT / ref["path"]).read_bytes()
        require((digest(data), len(data)) == (ref["sha256"], ref["bytes"]),
                f"frozen source changed: {ref['path']}")
        if ref["path"].endswith(".json"):
            payloads[key] = json.loads(data)
    raw, geometry, inventory, joined = (payloads[k] for k in
        ("current_inputs", "current_geometry", "current_inventory", "prior_shop_join"))
    require(payloads["current_inputs_review"]["input"]["sha256"] == sources["current_inputs"]["sha256"]
            and payloads["current_inputs_review"]["success"] == "independent_eoere_successor_source_input_checks_pass",
            "independent current input review join differs")
    require(geometry["candidate"] == inventory["candidate"] == spec["candidate"],
            "candidate identity differs")
    require(geometry["revision"] == spec["geometry_revision"], "geometry revision differs")
    require(raw["geometry"]["mirror"]["sha256"] == sources["current_geometry"]["sha256"],
            "current input/geometry join differs")
    require(payloads["prior_shop_manifest"]["source"]["sha256"] == sources["prior_shop_join"]["sha256"],
            "preserved CSV/join identity differs")
    coordinate_limit = spec["verification_arithmetic_limits_not_fabrication_tolerances"]["coordinate_mm"]
    frame_limit = spec["verification_arithmetic_limits_not_fabrication_tolerances"]["unit_frame"]
    maximum = {"coordinate_roundtrip_error_mm": 0.0, "end_plane_vertex_residual_mm": 0.0,
               "panel_front_axis_depth_error_mm": 0.0, "axis_grip_sum_error_mm": 0.0,
               "preserved_profile_translation_error_mm": 0.0}
    profiles, pointers = {}, {}
    old_profiles = {r["member"]: r for r in joined["members"]}
    for index, timber in enumerate(raw["timber_rows"]):
        profile = timber["raw_profile_source"]
        name = profile["member"]
        require(name == timber["name"] and name not in profiles, "member identity repeated")
        profiles[name] = profile
        pointers[name] = f"current_inputs#/timber_rows/{index}/raw_profile_source"
        if name in old_profiles:
            prior = old_profiles[name]
            for key in ("basis_grain_u_v_xyz", "raw_profile_vertices_luv_mm", "end_cut_planes", "blank_mm"):
                require(profile[key] == prior[key], f"preserved local profile changed: {name}/{key}")
            delta = profile.get("raised_rail_datum_change", {}).get("delta_xyz_mm", [0., 0., 0.])
            error = max(abs(v) for v in subtract(profile["datum_xyz_mm"], add(prior["datum_xyz_mm"], delta)))
            maximum["preserved_profile_translation_error_mm"] = max(
                maximum["preserved_profile_translation_error_mm"], error)
            require(error <= coordinate_limit, f"raised datum translation differs: {name}")
        else:
            require(name in {"eoere_cleat_left", "eoere_cleat_right"}, "unexpected new member")
            require(profile["raw_stock_scenario_dimensions_mm"] == [38.1, 139.7, 289.7],
                    "cleat stock dimensions differ")
    require(len(profiles) == 22 and len(old_profiles) == 20, "timber profile census differs")
    panel_profiles = payloads["panel_profiles"]
    panel_rows = geometry["finished_panel_solids"]
    require({r["id"] for r in panel_rows} == set(raw["panel_ids"]) and len(panel_rows) == 6,
            "panel census differs")
    for panel in panel_rows:
        name = panel["id"]
        saved = panel_profiles[name]
        basis = ([[1., 0., 0.], [0., 0., 1.], [0., -1., 0.]] if name.startswith("kicker_") else
                 [[1., 0., 0.], *profiles["base_rail_bottom_left"]["basis_grain_u_v_xyz"][1:]])
        vertices = saved["vertices_world_mm"]
        xmin = min(p[0] for p in vertices)
        section = [(i, p) for i, p in enumerate(vertices) if abs(p[0] - xmin) <= coordinate_limit]
        datum = min((p for _, p in section),
                    key=lambda p: (round(dot(p, basis[1]), 6), -round(dot(p, basis[2]), 6)))
        profiles[name] = {"member": name, "datum_xyz_mm": datum, "basis_grain_u_v_xyz": basis,
                          "blank_mm": saved["stock_blank_allowance_mm"],
                          "raw_profile_vertices_luv_mm": [local(p, datum, basis) for _, p in section],
                          "section_source_vertex_indices": [i for i, _ in section]}
        pointers[name] = f"panel_profiles#/{name}"

    finished = {r["id"]: r for r in [*geometry["finished_solids"], *panel_rows]}
    members, ends = [], []
    member_columns = ["member", "kind", "L_role", "nominal_blank_length_mm", "nominal_blank_depth_mm",
                      "nominal_blank_thickness_mm", *vector_names("datum")]
    member_columns += [c for label in "luv" for c in vector_names(f"basis_{label}", unit="unitless")]
    member_columns += [*vector_names("additional_rail_translation"), "current_finished_source_path",
                       "current_finished_source_sha256", "profile_source"]
    end_columns = ["member", "record_kind", "source_index", *vector_names("point", "luv"),
                   *vector_names("outward_normal", "luv", "unitless"), "plane_offset_from_datum_mm",
                   "normal_to_L_deg", "plane_source_vertex_indices", *vector_names("point"), "source"]
    for name, profile in sorted(profiles.items()):
        datum, basis = profile["datum_xyz_mm"], profile["basis_grain_u_v_xyz"]
        require(max(abs(dot(a, b) - (i == j)) for i, a in enumerate(basis)
                    for j, b in enumerate(basis)) <= frame_limit
                and max(abs(x - y) for x, y in zip(cross(basis[0], basis[1]), basis[2], strict=True)) <= frame_limit,
                f"member frame is not proper orthonormal: {name}")
        panel = name in raw["panel_ids"]
        blank = profile.get("blank_mm", [289.7, 139.7, 38.1])
        delta = profile.get("raised_rail_datum_change", {}).get("delta_xyz_mm", [0., 0., 0.])
        members.append([name, "panel" if panel else "timber", "geometric_width_X" if panel else "nominal_grain",
                        *blank, *datum, *(v for axis in basis for v in axis), *delta,
                        finished[name]["path"], finished[name]["sha256"], pointers[name]])
        points = profile["raw_profile_vertices_luv_mm"]
        for index, point in enumerate(points):
            w = world(point, datum, basis)
            error = max(abs(a - b) for a, b in zip(local(w, datum, basis), point, strict=True))
            maximum["coordinate_roundtrip_error_mm"] = max(maximum["coordinate_roundtrip_error_mm"], error)
            require(error <= coordinate_limit, f"coordinate roundtrip differs: {name}")
            source_index = profile.get("section_source_vertex_indices", list(range(len(points))))[index]
            ends.append([name, "panel_section_vertex" if panel else "raw_profile_vertex", source_index,
                         *point, "", "", "", "", "", "", *w, pointers[name]])
        planes = profile.get("end_cut_planes", [])
        if name.startswith("eoere_cleat_"):
            planes = [{"outward_normal_luv": [sign, 0., 0.], "offset_from_datum_mm": offset,
                       "normal_to_nominal_grain_deg": 0.,
                       "vertex_indices": [i for i, p in enumerate(points) if p[0] == offset]}
                      for sign, offset in [(-1., 0.), (1., 289.7)]]
        for index, plane in enumerate(planes):
            normal, offset = plane["outward_normal_luv"], plane["offset_from_datum_mm"]
            residual = max(abs(dot(points[i], normal) - offset) for i in plane["vertex_indices"])
            maximum["end_plane_vertex_residual_mm"] = max(maximum["end_plane_vertex_residual_mm"], residual)
            require(residual <= coordinate_limit, f"saved end-plane vertices differ: {name}")
            ends.append([name, "raw_end_plane", index, "", "", "", *normal, offset,
                         plane["normal_to_nominal_grain_deg"], ";".join(map(str, plane["vertex_indices"])),
                         "", "", "", pointers[name]])

    axes = {r["id"]: r for r in geometry["axes"]}
    shafts = {r["axis_id"]: r for r in raw["shafts"]}
    require(len(axes) == len(shafts) == 100 and set(axes) == set(shafts), "physical shaft census differs")
    expected_receivers = {(a["id"], r) for a in axes.values() for r in a["receivers"]}
    seen, holes, grip = set(), [], {name: 0. for name in axes}
    hole_columns = ["axis_id", "receiver", "nominal_shaft_diameter_mm", "modeled_bore_envelope_diameter_mm",
                    "modeled_underhead_length_mm", *vector_names("axis_point"),
                    *vector_names("axis_direction", unit="unitless"),
                    *vector_names("axis_point_in_receiver", "luv"),
                    *vector_names("entry_in_receiver", "luv"), *vector_names("exit_in_receiver", "luv"),
                    "entry_from_axis_point_mm", "exit_from_axis_point_mm", "saved_full_wall_length_mm", "source"]
    for index, receiver in enumerate(raw["finished_receiver_wall_queries"]):
        key = receiver["axis_id"], receiver["receiver"]
        require(key in expected_receivers and key not in seen and not receiver["partial_wall_present"],
                "receiver ownership or partial wall differs")
        seen.add(key)
        axis, shaft = axes[key[0]], shafts[key[0]]
        require(shaft["source_axis"] == axis, f"source axis differs: {key[0]}")
        point, direction = shaft["point"], shaft["basis"][0]
        require(point == axis["point_xyz_mm"], "axis point differs")
        ranges = receiver["finished_full_wall_intervals_from_axis_point_mm"]
        require(len(ranges) == 1, "receiver interval census changed")
        a, b = ranges[0]
        profile = profiles[key[1]]
        datum, basis = profile["datum_xyz_mm"], profile["basis_grain_u_v_xyz"]
        entry, exit_point = [add(point, scale(direction, t)) for t in (a, b)]
        require(b > a and abs((b - a) - receiver["full_wall_length_mm"]) <= coordinate_limit,
                "receiver full-wall length differs")
        grip[key[0]] += b - a
        holes.append([*key, axis["diameter_mm"], axis["bore_diameter_mm"], axis["nominal_under_head_length_mm"],
                      *point, *direction, *local(point, datum, basis), *local(entry, datum, basis),
                      *local(exit_point, datum, basis), a, b, receiver["full_wall_length_mm"],
                      f"current_inputs#/finished_receiver_wall_queries/{index}"])
    require(seen == expected_receivers and len(holes) == 120, "120 receiver occurrences not covered")
    for name, value in grip.items():
        error = abs(value - axes[name]["grip_mm"])
        maximum["axis_grip_sum_error_mm"] = max(maximum["axis_grip_sum_error_mm"], error)
        require(error <= coordinate_limit, f"receiver lengths/shaft grip differ: {name}")

    screws, seen = [], set()
    changed = {r["axis_id"]: r for r in geometry["changes"]["Hillman_axes_moved"]}
    screw_inputs = {r["id"]: r["source_screw_descriptor"] for r in raw["hillman_rows"]}
    old_screws = {r["axis_id"]: r for r in payloads["service_layout"]["screw_axes"]}
    thickness = {r["panel"]: r["panel_thickness_mm"] for r in geometry["panel_machining"]["outlines"]}
    screw_columns = ["axis_id", "panel", "receiver", "moved_by_rail_revision", *vector_names("front_axis_origin"),
                     *vector_names("axis_direction", unit="unitless"),
                     *vector_names("origin_in_panel", "luv"), *vector_names("origin_in_receiver", "luv"),
                     "modeled_panel_thickness_mm", "source"]
    for index, screw in enumerate(geometry["screw_axes"]):
        name, panel, receiver = screw["axis_id"], screw["panel"], screw["receiver"]
        require(name not in seen and screw_inputs[name] == screw, "Hillman identity/source differs")
        seen.add(name)
        origin, direction = screw["origin_xyz_mm"], screw["direction_xyz"]
        prior = old_screws[name]
        require(prior["panel"] == panel and prior["receiver"] == receiver
                and prior["direction_xyz"] == direction, "Hillman receiver/direction changed")
        if name in changed:
            require(prior["origin_xyz_mm"] == changed[name]["before_xyz_mm"]
                    and origin == changed[name]["after_xyz_mm"], "moved screw datum differs")
        else:
            require(origin == prior["origin_xyz_mm"], "undeclared screw datum move")
        panel_point = local(origin, profiles[panel]["datum_xyz_mm"], profiles[panel]["basis_grain_u_v_xyz"])
        error = abs(panel_point[2] + thickness[panel])
        maximum["panel_front_axis_depth_error_mm"] = max(maximum["panel_front_axis_depth_error_mm"], error)
        require(error <= coordinate_limit, "panel front-axis depth differs")
        screws.append([name, panel, receiver, name in changed, *origin, *direction, *panel_point,
                       *local(origin, profiles[receiver]["datum_xyz_mm"], profiles[receiver]["basis_grain_u_v_xyz"]),
                       thickness[panel], f"current_geometry#/screw_axes/{index}"])
    require(len(screws) == 66 and len(changed) == 4, "Hillman/moved-axis census differs")
    require(geometry["wire_proposals"] == payloads["service_layout"]["wire_proposals"], "wire routes changed")
    tables = {"members.csv": (member_columns, members), "member-end-datums.csv": (end_columns, ends),
              "receiver-holes.csv": (hole_columns, holes), "panel-screw-datums.csv": (screw_columns, screws)}
    encoded = {name: csv_bytes(columns, rows) for name, (columns, rows) in tables.items()}
    result = {
        "schema": "eoere_raised_rail_nominal_cut_datum_export/v1",
        "candidate": spec["candidate"], "geometry_revision": spec["geometry_revision"],
        "disposition": "PASS_SAVED_NOMINAL_DATUM_EXPORT_AND_COORDINATE_JOINS",
        "sources": sources,
        "inputs": {"path": str(INPUT.relative_to(ROOT)), "sha256": digest(INPUT.read_bytes())},
        "helper": {"path": str((OWN / "cut-datums.py").relative_to(ROOT)),
                   "sha256": digest((OWN / "cut-datums.py").read_bytes())},
        "files": {name: {"sha256": digest(data), "bytes": len(data), "rows": len(tables[name][1]),
                          "columns": [*tables[name][0], "Actual", "Disposition"]} for name, data in encoded.items()},
        "counts": {"timbers": 22, "panels": 6, "physical_bolt_axes": 100, "receiver_bore_occurrences": 120,
                   "Hillman_axes": 66, "moved_Hillman_axes": 4,
                   "translated_structural_stacks": len(geometry["changes"]["bottom_stack_moves"]),
                   "recesses": len(joined["recesses"]), "wire_routes": len(geometry["wire_proposals"]),
                   "raw_end_planes": sum(r[1] == "raw_end_plane" for r in ends),
                   "raw_profile_vertices": sum(r[1] == "raw_profile_vertex" for r in ends),
                   "panel_section_vertices": sum(r[1] == "panel_section_vertex" for r in ends),
                   "blank_Actual_and_Disposition_cells": 2 * sum(len(t[1]) for t in tables.values())},
        "verification": maximum,
        "recess_definitions": {"source": "prior_shop_join#/recesses", "definitions": joined["recesses"],
                               "raw_end_planes_do_not_include_recesses_or_bores": True},
        "panel_miter_definition": {"source": "panel_seam_recipe#panel_outlines",
                                    "definition": "Kicker bounding slab minus unchanged unperforated lower main-panel outline; saved side-section vertices identify the seam profile. Source vertex order is not a boundary traversal or saw setting."},
        "wire_cut_definition": {"source": "service_recipe#front_open_cutter/routed_services",
                                 "routes": "current_geometry#/wire_proposals", "route_count": 131,
                                 "wire_depth_mm": payloads["service_layout"]["inputs"]["wire_depth_mm"],
                                 "wire_sweep_radius_mm": 6.35, "connector_clearance_radius_mm": 9.35,
                                 "definition": "Union of route sweep at recorded depth d with front-plane route sweep radius sqrt(d*d+r*r); retain recorded connector cutters and fixed world endpoints. Recut at fixed routes after rail translation; do not translate finished wire cuts.",
                                 "actual_slack_bend_radius_or_feed_verified": False},
        "nominal_discrepancies": [],
        "delivered_dimensions_and_tolerances": None,
        "release": {"fabrication": False, "climbing": False, "physical_capacity": False,
                    "actual_parts_or_holes_observed": False, "old_access_or_acceptance_transferred": False},
        "execution": {"dependencies": "Python standard library only", "CAD_import_or_rebuild": False,
                      "K_q_or_mechanics_evaluation": False, "physical_tests": False,
                      "python_version": ".".join(map(str, sys.version_info[:3])),
                      "reproduction": f".venv/bin/python {(OWN / 'cut-datums.py').relative_to(ROOT)!s} --check"},
    }
    require(all(result["counts"][key] == value for key, value in spec["expected_counts"].items()),
            "declared packet/source census differs")
    for ref in sources.values():
        data = (ROOT / ref["path"]).read_bytes()
        require((digest(data), len(data)) == (ref["sha256"], ref["bytes"]), "source changed during export")
    return {**encoded, "cut-datums-result.json": json_bytes(result)}, result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument("--write", action="store_true", help="Write only the four owned CSVs and result JSON")
    action.add_argument("--check", action="store_true", help="Replay in memory and compare every issued output byte")
    args = parser.parse_args()
    outputs, result = build()
    for name, data in outputs.items():
        path = OWN / name
        if args.write:
            path.write_bytes(data)
        else:
            require(path.read_bytes() == data, f"saved export bytes differ: {name}")
    print(json.dumps({"disposition": result["disposition"], "counts": result["counts"],
                      "verification": result["verification"], "generated_bytes": sum(map(len, outputs.values()))}, sort_keys=True))


if __name__ == "__main__":
    main()
