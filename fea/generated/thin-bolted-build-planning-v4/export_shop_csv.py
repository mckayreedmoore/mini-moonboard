"""Export the frozen nominal shop-coordinate join as named, unitful CSVs.

Stdlib formatting only: no source geometry, mechanics, purchases or observations
are created. Parent approves the schema before issuing any export command.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import math
import platform
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
OWN = Path(__file__).resolve()
LOADED_SOURCE_SHA = hashlib.sha256(OWN.read_bytes()).hexdigest()
SOURCE = OWN.parent / "joined-shop-data-final.json"
SOURCE_SHA = "7982d8612014d6d55279f7847798ea3bf87e6c2eca2fa585ef4457daf3787074"
OBSERVATION_COLUMNS = ("Actual", "Disposition")
EXPECTED_COUNTS = {
    "member-datums.csv": 20,
    "member-raw-vertices.csv": 168,
    "member-end-cut-planes.csv": 44,
    "member-end-cut-plane-vertices.csv": 176,
    "bolt-axes-and-stacks.csv": 70,
    "wood-receiver-bearing.csv": 82,
    "steel-bearing-thread-windows.csv": 72,
    "fittings-and-duties.csv": 36,
    "fitting-hole-ownership.csv": 72,
    "Hillman-receiver-axes.csv": 66,
    "washer-receiving-planes.csv": 140,
    "recess-parameters.csv": 2,
    "recess-profile-vertices.csv": 8,
    "reference-tables.csv": 10,
    "source-sha256.csv": 282,
}


def require(ok, message):
    if not ok:
        raise ValueError(message)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def merge_pins(*mappings):
    merged = {}
    for mapping in mappings:
        for path, digest in mapping.items():
            require(path not in merged or merged[path] == digest, "contradictory source pin: " + path)
            merged[path] = digest
    return merged


def verify_pins(pins):
    for relative, digest in pins.items():
        require(sha(ROOT / relative) == digest, "frozen source changed: " + relative)


def vector_columns(prefix, unit="mm", axes="xyz"):
    return [f"{prefix}_{axis}_{unit}" for axis in axes]


def basis_columns(prefix, axes):
    return [name for direction in axes for name in vector_columns(f"{prefix}_{direction}", "unitless")]


def flat_vectors(vectors):
    return [coordinate for vector in vectors for coordinate in vector]


def table(columns, rows):
    require(len(columns) == len(set(columns)), "duplicate column name")
    for row in rows:
        require(len(row) == len(columns), "row/header length differs")
        for cell in row:
            require(isinstance(cell, (str, int, float)) and not isinstance(cell, bool), "scalar CSV cell required")
            require(not isinstance(cell, float) or math.isfinite(cell), "finite CSV number required")
    return {"columns": columns + list(OBSERVATION_COLUMNS), "rows": [row + ["", ""] for row in rows]}


def source_join():
    require(sha(OWN) == LOADED_SOURCE_SHA, "loaded exporter source changed")
    require(sha(SOURCE) == SOURCE_SHA, "exact independently reviewed join required")
    joined = json.loads(SOURCE.read_bytes())
    require(joined["schema"] == "thin_bolted_joined_shop_geometry/v1"
            and joined["candidate"] == "compact-floor-flush-thin-bolted-development"
            and joined["source_pins_before_after_unchanged"] is True
            and len(joined["source_sha256"]) == 280, "reviewed join identity differs")
    pins = merge_pins(joined["source_sha256"], {
        str(SOURCE.relative_to(ROOT)): SOURCE_SHA,
        str(OWN.relative_to(ROOT)): LOADED_SOURCE_SHA,
    })
    verify_pins(pins)
    return joined, pins


def build_tables(joined, pins):
    result = {}
    members = joined["members"]
    member_ids = {member["member"] for member in members}
    axes = joined["axes"]
    axis_ids = {axis["axis_id"] for axis in axes}
    require(len(member_ids) == 20 and len(axis_ids) == 70, "unique own member/bolt identities required")
    result["member-datums.csv"] = table(
        ["member", "nominal_blank_length_mm", "nominal_blank_depth_mm", "nominal_blank_thickness_mm"]
        + vector_columns("datum") + ["datum_source_vertex_index_unitless"]
        + basis_columns("basis", "luv") + vector_columns("raw_source_translation"),
        [[m["member"], *m["blank_mm"], *m["datum_xyz_mm"], m["datum_source_vertex_index"],
          *flat_vectors(m["basis_grain_u_v_xyz"]), *m["raw_source_translation_xyz_mm"]] for m in members])
    result["member-raw-vertices.csv"] = table(
        ["member", "source_vertex_index_unitless"] + vector_columns("raw_vertex", axes="luv"),
        [[m["member"], index, *vertex] for m in members
         for index, vertex in enumerate(m["raw_profile_vertices_luv_mm"])])
    result["member-end-cut-planes.csv"] = table(
        ["member", "end_cut_plane_index_unitless"] + vector_columns("outward_normal", "unitless", "luv")
        + ["plane_offset_from_datum_mm", "normal_to_nominal_grain_deg"],
        [[m["member"], index, *p["outward_normal_luv"], p["offset_from_datum_mm"],
          p["normal_to_nominal_grain_deg"]] for m in members for index, p in enumerate(m["end_cut_planes"])])
    links = []
    for member in members:
        for plane_index, plane in enumerate(member["end_cut_planes"]):
            for order, vertex in enumerate(plane["vertex_indices"]):
                require(type(vertex) is int and 0 <= vertex < len(member["raw_profile_vertices_luv_mm"]),
                        "plane must retain its own source vertex")
                links.append([member["member"], plane_index, order, vertex])
    result["member-end-cut-plane-vertices.csv"] = table(
        ["member", "end_cut_plane_index_unitless", "vertex_order_on_plane_unitless", "source_vertex_index_unitless"], links)
    stack_columns = [
        "modeled_nut_near_underhead_mm", "modeled_tip_beyond_nut_mm", "declared_thread_pitch_mm",
        "conditional_two_tip_threads_minimum_underhead_mm", "comparison_product_id_unitless",
        "comparison_shortest_underhead_mm", "comparison_shortest_tip_thread_count_frozen_stack_unitless",
        "comparison_shortest_tip_thread_count_frozen_washers_nut_max_unitless",
        "comparison_two_tip_margin_frozen_washers_nut_max_mm",
    ]
    stack_keys = [
        "nut_near_underhead_mm", "tip_nominal_mm", "pitch_mm", "minimum_two_tip_thread_length_mm",
        "comparison_product", "comparison_shortest_underhead_mm", "comparison_shortest_tip_threads_frozen_stack",
        "comparison_shortest_tip_threads_frozen_washers_nut_max", "comparison_two_tip_margin_mm_frozen_washers_nut_max",
    ]
    result["bolt-axes-and-stacks.csv"] = table(
        ["axis_id", "axis_source"] + vector_columns("axis_point") + vector_columns("axis_direction", "unitless")
        + vector_columns("own_underhead")
        + ["nominal_shaft_diameter_mm", "modeled_underhead_length_mm", "occupied_bore_envelope_diameter_mm",
           "near_steel_thickness_mm", "far_steel_thickness_mm", "wood_grip_mm",
           "collision_head_height_mm", "collision_nut_height_mm", "collision_across_flats_mm",
           "head_washer_OD_mm", "head_washer_ID_mm", "head_washer_thickness_mm",
           "nut_washer_OD_mm", "nut_washer_ID_mm", "nut_washer_thickness_mm",
           "conditional_ASME_Lbmin_mm", "conditional_ASME_Lgmax_mm",
           "conditional_full_smooth_body_to_cover_every_bearing_mm", "smooth_body_full_thread_nut_reach_gap_mm"]
        + stack_columns,
        [[a["axis_id"], a["source"], *a["point_xyz_mm"], *a["direction_xyz"], *a["own_underhead_xyz_mm"],
          *a["nominal_D_L_bore_mm"], *a["plate_near_far_grip_mm"], *a["modeled_collision_head_H_nut_H_AF_mm"],
          *flat_vectors(a["washers_OD_ID_t_mm"]), *a["conditional_ASME_Lbmin_Lgmax_mm"],
          a["full_smooth_body_to_cover_every_bearing_mm"], a["smooth_body_and_full_thread_nut_reach_gap_mm"],
          *[a["stack"][key] for key in stack_keys]] for a in axes])
    receiver_rows = []
    for r in joined["bearing_rows"]:
        require(r[0] in axis_ids and r[1] in member_ids and len(r[3]) == len(r[4]) == 1,
                "one own wood interval and its own endpoints required")
        clearances = [r[7][direction][sign] for direction in ("grain", "cross_grain") for sign in ("negative", "positive")]
        receiver_rows.append([*r[:3], *r[3][0], *flat_vectors(r[4][0]), r[5], *r[6], *clearances])
    result["wood-receiver-bearing.csv"] = table(
        ["axis_id", "member", "finished_receiver_source_index_unitless", "own_underhead_entry_mm", "own_underhead_exit_mm"]
        + vector_columns("entry", axes="luv") + vector_columns("exit", axes="luv")
        + ["shaft_to_nominal_grain_deg", "bearing_length_mm", "thread_overlap_min_mm", "thread_overlap_max_mm",
           "five_probe_min_grain_negative_boundary_mm", "five_probe_min_grain_positive_boundary_mm",
           "five_probe_min_crossgrain_negative_boundary_mm", "five_probe_min_crossgrain_positive_boundary_mm"], receiver_rows)
    steel_rows = []
    for r in joined["steel_bearing_rows"]:
        require(r[0] in axis_ids and len(r[2]) == 1, "one own steel interval required")
        steel_rows.append([*r[:2], *r[2][0], *r[3]])
    result["steel-bearing-thread-windows.csv"] = table(
        ["axis_id", "own_steel_side", "own_underhead_entry_mm", "own_underhead_exit_mm",
         "bearing_length_mm", "thread_overlap_min_mm", "thread_overlap_max_mm"], steel_rows)
    result["fittings-and-duties.csv"] = table(
        ["fitting_id", "former_angle_duty_id", "beam_member", "post_member"] + vector_columns("origin")
        + basis_columns("fitting_basis", "uvw") + ["used_holes"],
        [[*r[:4], *r[4], *flat_vectors(r[5]), r[6]] for r in joined["fittings"]])
    fitting_ids = {r[0] for r in joined["fittings"]}
    require(len(fitting_ids) == 36 and len({r[1] for r in joined["fittings"]}) == 24, "36 fittings must retain all 24 former duties")
    for row in joined["fitting_hole_rows"]:
        require(row[0] in axis_ids and row[1] in fitting_ids and row[4] in member_ids, "own fitting hole identity required")
    result["fitting-hole-ownership.csv"] = table(
        ["axis_id", "fitting_id", "former_angle_duty_id", "flange", "receiver_member",
         "assumed_outer_corner_hole_offset_mm", "nominal_width_edge_mm"], joined["fitting_hole_rows"])
    result["Hillman-receiver-axes.csv"] = table(
        ["axis_id", "panel", "receiver_member"] + vector_columns("origin") + vector_columns("direction", "unitless")
        + vector_columns("origin_receiver", axes="luv") + vector_columns("direction_receiver", "unitless", "luv")
        + ["nominal_raw_receiver_fraction_unitless"],
        [[*r[:3], *r[3], *r[4], *r[5], *r[6], r[7]] for r in joined["Hillman_axes"]])
    seat_rows = []
    for r in joined["washer_receiving_plane_rows"]:
        require(r[0] in axis_ids and len(r[3]) == 2, "own washer receiver body/flange required")
        seat_rows.append([*r[:3], *r[3], *r[4], *r[5], r[6]])
    require(len({(r[0], r[1]) for r in seat_rows}) == 140, "each physical bolt must retain both own washer roles")
    result["washer-receiving-planes.csv"] = table(
        ["axis_id", "washer_role", "receiving_material", "receiving_body", "receiving_flange"]
        + vector_columns("modeled_pressure_datum") + vector_columns("inward_toward_receiver", "unitless")
        + ["modeled_support_opening_envelope_diameter_mm"], seat_rows)
    result["recess-parameters.csv"] = table(
        ["member"] + vector_columns("grain", "unitless") + vector_columns("normal", "unitless")
        + ["taper_run_mm", "maximum_depth_mm", "top_world_z_mm", "bottom_world_z_mm",
           "nominal_transverse_clearance_mm", "nominal_vertical_clearance_mm"]
        + vector_columns("right_cutter_translation") + ["recorded_removed_volume_mm3"],
        [[r["member"], *r["grain_xyz"], *r["normal_xyz"], *r["taper_run_maxdepth_mm"], *r["top_bottom_world_z_mm"],
          r["nominal_transverse_clearance_mm"], r["nominal_vertical_clearance_mm"],
          *r["right_cutter_translation_xyz_mm"], r["recorded_current_removed_volume_mm3"]] for r in joined["recesses"]])
    result["recess-profile-vertices.csv"] = table(
        ["member", "profile_vertex_index_unitless", "world_x_mm", "global_grain_projection_s_mm"],
        [[r["member"], index, *vertex] for r in joined["recesses"]
         for index, vertex in enumerate(r["cut_profile_world_x_global_grain_s_mm"])])
    references = [[key, *value, pins[value[0]]] for key, value in sorted(joined["reused_tables"].items())]
    references += [[key, str(SOURCE.relative_to(ROOT)), key, SOURCE_SHA] for key in ("Hillman_policy", "nominal_disassembly")]
    result["reference-tables.csv"] = table(["topic", "source_path", "source_key_path", "source_sha256"], references)
    result["source-sha256.csv"] = table(["source_path", "sha256"], [[path, digest] for path, digest in sorted(pins.items())])
    require({name: len(t["rows"]) for name, t in result.items()} == EXPECTED_COUNTS, "frozen export census differs")
    return result


def encode_and_verify(content):
    buffer = io.StringIO(newline="")
    writer = csv.writer(buffer, lineterminator="\n")
    writer.writerow(content["columns"])
    writer.writerows(content["rows"])
    payload = buffer.getvalue()
    decoded = list(csv.reader(io.StringIO(payload, newline="")))
    require(decoded[0] == content["columns"] and len(decoded) == len(content["rows"]) + 1, "CSV header/count roundtrip differs")
    cells = 0
    for original, rendered in zip(content["rows"], decoded[1:], strict=True):
        require(rendered[-2:] == ["", ""], "Actual/Disposition must remain blank")
        for value, cell in zip(original, rendered, strict=True):
            restored = int(cell) if type(value) is int else float(cell) if type(value) is float else cell
            require(restored == value, "CSV field roundtrip differs")
            cells += 1
    return payload.encode("utf-8"), cells


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--schema", action="store_true", help="print approved-scope proposal without writing any output")
    parser.add_argument("--out-dir", type=Path)
    args = parser.parse_args()
    require(args.schema != (args.out_dir is not None), "choose schema inspection or parent-approved output")
    joined, pins = source_join()
    tables = build_tables(joined, pins)
    encoded = {name: encode_and_verify(content) for name, content in tables.items()}
    verify_pins(pins)
    schema = {name: {"row_count": len(t["rows"]), "columns": t["columns"]} for name, t in tables.items()}
    if args.schema:
        print(json.dumps({"schema": "thin_bolted_shop_csv_export_schema/v1", "source_sha256": SOURCE_SHA,
                          "helper_sha256": LOADED_SOURCE_SHA, "files": schema}, sort_keys=True))
        return
    require(not args.out_dir.exists(), "new parent-owned output directory required")
    manifest = {
        "schema": "thin_bolted_shop_csv_export/v1", "candidate": joined["candidate"],
        "source": {"path": str(SOURCE.relative_to(ROOT)), "sha256": SOURCE_SHA},
        "helper": {"path": str(OWN.relative_to(ROOT)), "sha256": LOADED_SOURCE_SHA},
        "source_pin_count": len(pins), "source_pins_before_after_unchanged": True,
        "files": {name: {**schema[name], "sha256": hashlib.sha256(payload).hexdigest(), "bytes": len(payload),
                          "roundtrip_verified_cell_count": cells} for name, (payload, cells) in encoded.items()},
        "datum_convention": joined["datum_convention"],
        "end_cut_plane_equation": "outward_normal_luv dot point_luv_mm = plane_offset_from_datum_mm",
        "scope": "Coordinate and conditional dimensional-envelope export of the reviewed join; every Actual and Disposition cell is blank.",
        "units": "Coordinate/length headers use mm, volume uses mm3, angle uses deg, and directions/counts/indices/fractions use unitless.",
        "limits": joined["claim_limits"],
        "purchased_Hillman_policy_source": "reference-tables.csv: Hillman_policy",
        "stock_access_cost_and_nominal_disassembly": "Referenced existing tables; no stock, routes, quantities or costs remodelled.",
        "observed_parts_cuts_holes_or_floor": False, "drill_bits_or_purchased_bolt_lengths_selected": False,
        "loads_or_capacities_consumed": False, "CAD_geometry_or_native_solve_executed": False,
        "geometry_authority_or_fabrication_release_changed": False,
        "execution": {"sys_orig_argv": list(sys.orig_argv), "sys_argv": list(sys.argv),
                      "python_executable": sys.executable, "python_version": platform.python_version(),
                      "dependencies": "stdlib only"},
    }
    manifest_payload = (json.dumps(manifest, sort_keys=True, indent=2, allow_nan=False) + "\n").encode()
    args.out_dir.mkdir(parents=True)
    for name, (payload, _) in encoded.items():
        (args.out_dir / name).write_bytes(payload)
    (args.out_dir / "manifest.json").write_bytes(manifest_payload)
    verify_pins(pins)
    for name, (payload, _) in encoded.items():
        require((args.out_dir / name).read_bytes() == payload, "written CSV differs: " + name)
    require((args.out_dir / "manifest.json").read_bytes() == manifest_payload, "written manifest differs")
    print(json.dumps({"out_dir": str(args.out_dir), "manifest_sha256": hashlib.sha256(manifest_payload).hexdigest(),
                      "CSV_count": len(tables), "CSV_row_count": sum(EXPECTED_COUNTS.values()),
                      "total_bytes": len(manifest_payload) + sum(len(payload) for payload, _ in encoded.values()),
                      "source_pins_before_after_unchanged": True}, sort_keys=True))


if __name__ == "__main__":
    main()
