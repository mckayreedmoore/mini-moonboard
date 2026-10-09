"""Independent stdlib arithmetic/source review of the frozen current shop packet."""
from __future__ import annotations

import csv
import hashlib
import json
import math
import os
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path

OWN = Path(__file__).resolve()
ROOT = next(p for p in OWN.parents if (p / "AGENTS.md").is_file())
PACKET = ROOT / "docs/wood-joints-mvp/hypotheses/hl35-candidate/thin-frame-comparison/eoere-successor-v1/shop-assembly-v1/extended-cleat-followup-v1"
VERIFY_SHA = "38aaa554039e3dd5c5bbcf7545c3dc6b6339b7dd9dc93af6ac9cecc327e9f721"
RESULT_SHA = "0f00a7ba22a08975adac6bf660db370866510c40b5d56e5829bfab9b2ad3f92e"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    return json.loads(Path(path).read_bytes())


def table(name):
    with (PACKET / name).open() as stream:
        return list(csv.DictReader(stream))


def vector(row, prefix, axes="xyz", suffix="mm"):
    return [float(row[f"{prefix}_{a}_{suffix}"]) for a in axes]


def close(a, b, tolerance=1e-6):
    if isinstance(a, (list, tuple)):
        assert len(a) == len(b)
        for x, y in zip(a, b, strict=True):
            close(x, y, tolerance)
    else:
        assert abs(a-b) <= tolerance, (a, b, tolerance)


def dot(a, b):
    return math.fsum(x*y for x, y in zip(a, b, strict=True))


def world(local, p):
    return [p["datum_xyz_mm"][i] + math.fsum(local[j]*p["basis_grain_u_v_xyz"][j][i] for j in range(3)) for i in range(3)]


def main():
    assert sha(PACKET / "verification.json") == VERIFY_SHA
    assert sha(PACKET / "result.json") == RESULT_SHA
    verification, result, spec = (read(PACKET / n) for n in ("verification.json", "result.json", "inputs.json"))
    frozen = {name: ref["sha256"] for name, ref in verification["owned_artifacts"].items()}
    frozen["verification.json"] = VERIFY_SHA
    assert len(frozen) == 26
    for name, digest in frozen.items():
        assert sha(PACKET / name) == digest
    for name, ref in verification["owned_artifacts"].items():
        assert (PACKET / name).stat().st_size == ref["bytes"]
    for path, digest in verification["preserved_original_14_shop_artifact_sha256"].items():
        assert sha(ROOT / path) == digest
    sources = {name: read(ROOT / ref["path"]) for name, ref in spec["sources"].items() if ref["path"].endswith(".json")}
    for ref in spec["sources"].values():
        assert sha(ROOT / ref["path"]) == ref["sha256"]
    ext, base, bottom = (sources[n] for n in ("extension", "base", "bottom"))
    assert ext["axes"] == base["axes"] and ext["screw_axes"] == base["screw_axes"]
    assert spec["optional_extra_grid"] is False
    profiles = read(PACKET / "current_profiles.json")
    members, ends, holes, screws, stacks, access, machining = (table(n) for n in (
        "members.csv", "member-end-datums.csv", "receiver-holes.csv", "panel-screw-datums.csv",
        "bolt-stacks.csv", "access-sides.csv", "panel-machining.csv"))
    assert [len(x) for x in (members, holes, screws, stacks, access, machining)] == [28, 120, 66, 100, 200, 340]
    blank_observations = 0
    for rows in (members, ends, holes, screws, stacks, access, machining):
        for row in rows:
            for key, value in row.items():
                if key.startswith("Actual") or key == "Disposition":
                    assert value == ""
                    blank_observations += 1

    finished = {r["id"]: r for r in [*sources["aligned"]["changed_finished_solids"],
        *sources["aligned"]["unchanged_finished_solids"], *bottom["finished_panel_solids"]]}
    finished.update({r["id"]: r for r in base["changed_finished_solids"] if r["kind"] in {"timber", "panel"}})
    finished.update({r["id"]: r for r in ext["changed_finished_solids"]})
    assert set(finished) == set(profiles)
    end_vertices = {(r["member"], int(r["source_index"])): r for r in ends if r["record_kind"] != "raw_end_plane"}
    vertices_checked, planes_checked = 0, 0
    for row in members:
        name, p = row["member"], profiles[row["member"]]
        assert p["finished"] == finished[name] and p["kind"] == row["kind"]
        close(p["datum_xyz_mm"], vector(row, "datum"))
        close(p["blank_mm"], [float(row[f"nominal_blank_{d}_mm"]) for d in ("length", "depth", "thickness")])
        basis = p["basis_grain_u_v_xyz"]
        for i in range(3):
            close(basis[i], vector(row, "basis_" + "luv"[i], suffix="unitless"))
            for j in range(3):
                close(dot(basis[i], basis[j]), float(i == j), 1e-9)
        for index, vertex in enumerate(p["vertices_luv_mm"]):
            end = end_vertices[name, index]
            close(vertex, vector(end, "point", "luv"))
            close(world(vertex, p), vector(end, "point"))
            vertices_checked += 1
        for plane in p["end_planes"]:
            n = vector(plane, "outward_normal", "luv", "unitless")
            offset = float(plane["plane_offset_from_datum_mm"])
            close(dot(n, n), 1., 1e-9)
            for index in map(int, plane["plane_source_vertex_indices"].split(";")):
                close(dot(n, p["vertices_luv_mm"][index]), offset)
            assert max(dot(n, v)-offset for v in p["vertices_luv_mm"]) < 1e-6
            close(float(plane["normal_to_L_deg"]), math.degrees(math.acos(abs(n[0]))))
            planes_checked += 1
        for index, bounds in enumerate(finished[name].get("bounds_xyz_mm", [])):
            if len(bounds) == 2:
                points = list(p["vertices_luv_mm"])
                if p["kind"] == "panel":
                    points += [[v[0]+p["blank_mm"][0], *v[1:]] for v in points]
                raw = [world(v, p)[index] for v in points]
                assert min(raw) <= bounds[0] + 1e-5 and max(raw) >= bounds[1] - 1e-5, (name, index, min(raw), max(raw), bounds)
    for name in ("eoere_cleat_left", "eoere_cleat_right"):
        p = profiles[name]
        assert sorted([world(v, p)[1:] for v in p["vertices_luv_mm"]]) == sorted(ext["new_cleat_YZ_polygon_mm"] * 2)
        close(p["blank_mm"][0], max(z for _, z in ext["new_cleat_YZ_polygon_mm"]) - min(z for _, z in ext["new_cleat_YZ_polygon_mm"]))

    axes = {a["id"]: a for a in ext["axes"]}
    old_axes = {a["id"]: a for a in bottom["axes"]}
    old_holes = {}
    with (ROOT / spec["sources"]["holes"]["path"]).open() as stream:
        old_holes = {(r["axis_id"], r["receiver"]): r for r in csv.DictReader(stream)}
    grips = Counter()
    for row in holes:
        axis, p = axes[row["axis_id"]], profiles[row["receiver"]]
        prior = old_holes[row["axis_id"], row["receiver"]]
        close(vector(row, "axis_point"), axis["point_xyz_mm"])
        close(vector(row, "axis_direction", suffix="unitless"), axis["direction_xyz"], 1e-8)
        for label in ("entry", "exit"):
            distance = float(row[label + "_from_axis_point_mm"])
            assert row[label + "_from_axis_point_mm"] == prior[label + "_from_axis_point_mm"]
            expected = [x + distance*d for x, d in zip(axis["point_xyz_mm"], axis["direction_xyz"], strict=True)]
            close(world(vector(row, label + "_in_receiver", "luv"), p), expected, 5e-6)
        grips[axis["id"]] += float(row["exit_from_axis_point_mm"]) - float(row["entry_from_axis_point_mm"])
        close(float(row["modeled_bore_envelope_diameter_mm"]), axis["bore_diameter_mm"])
    assert {(r["axis_id"], r["receiver"]) for r in holes} == {(a["id"], host) for a in axes.values() for host in a["receivers"]}
    for name, grip in grips.items():
        close(grip, axes[name]["grip_mm"])
    screw_sources = {r["axis_id"]: r for r in ext["screw_axes"]}
    for row in screws:
        source = screw_sources[row["axis_id"]]
        assert row["panel"] == source["panel"] and row["receiver"] == source["receiver"]
        close(vector(row, "front_axis_origin"), source["origin_xyz_mm"])
        close(vector(row, "axis_direction", suffix="unitless"), source["direction_xyz"], 1e-8)
        for label in ("panel", "receiver"):
            close(world(vector(row, "origin_in_" + label, "luv"), profiles[row[label]]), source["origin_xyz_mm"])
    features = {r["identity"]: r for r in bottom["panel_machining"]["features"]}
    for row in machining:
        source = features[row["identity"]]
        point = screw_sources[row["identity"]]["origin_xyz_mm"] if row["identity"] in screw_sources else source["start_xyz_mm"]
        close(vector(row, "origin"), point)
        close(vector(row, "direction", suffix="unitless"), source["direction_xyz"])
        close(world(vector(row, "origin_in_panel", "luv"), profiles[row["panel"]]), point)
        close(float(row["modeled_diameter_mm"]), source["diameter_mm"])
    assert Counter(r["kind"] for r in machining) == {"tnut": 142, "light": 132, "conditional_screw_clearance": 66}

    stack_by_id = {r["axis_id"]: r for r in stacks}
    short = Counter()
    for row in stacks:
        a, f = axes[row["axis_id"]], lambda key: float(row[key])
        close(f("receiver_grip_mm"), a["grip_mm"])
        close(f("receiver_plus_plate_mm"), a["grip_mm"] + a["before_plate_mm"] + a["after_plate_mm"])
        assert row["receiver_member_ids"].split(";") == a["receivers"]
        close(f("nominal_diameter_mm"), a["diameter_mm"])
        close(f("nominal_underhead_length_mm"), a["nominal_under_head_length_mm"])
        s, w, h, pitch = (f("receiver_plus_plate_mm"), f("model_each_washer_thickness_mm"), f("model_nut_height_mm"), 25.4/f("UNC_threads_per_inch"))
        close(f("model_nut_near_underhead_mm"), s + 2*w)
        close(f("model_tip_projection_mm"), f("nominal_underhead_length_mm") - s - 2*w - h)
        close(f("model_two_tip_pitch_margin_mm"), f("model_tip_projection_mm") - 2*pitch)
        close(f("model_body_to_farthest_bearing_target_mm"), s+w)
        margin = f("catalog_underhead_min_mm") - s - 2*f("catalog_each_washer_max_mm") - f("catalog_nut_height_max_mm") - 2*pitch
        close(f("catalog_min_length_max_stack_two_pitch_margin_mm"), margin)
        close(f("catalog_equal_washer_ceiling_mm"), (f("catalog_underhead_min_mm") - s - f("catalog_nut_height_max_mm") - 2*pitch)/2)
        for label in ("min", "max"):
            close(f("catalog_nut_near_minus_Lg_" + label + "_mm"), s + 2*f("catalog_each_washer_" + label + "_mm") - f("catalog_Lg_max_mm"))
        assert (row["catalog_box_disposition"] == "SHORT_STACK_COMPARISON") == (margin < 0)
        if margin < 0:
            short[(a["diameter_mm"], a["nominal_under_head_length_mm"])] += 1
    assert sorted(short.values()) == [4, 4, 16]
    for row in access:
        a, stack = axes[row["axis_id"]], stack_by_id[row["axis_id"]]
        h = a["hardware_scenario"]
        head_face = -a["before_plate_mm"] - h["washer_thickness_mm"]
        nut_face = a["grip_mm"] + a["after_plate_mm"] + h["washer_thickness_mm"]
        offsets = {"axis_origin_xyz_mm": 0., "nominal_tip_xyz_mm": head_face + a["nominal_under_head_length_mm"],
            "nominal_bearing_face_xyz_mm": head_face if row["side"] == "head" else nut_face,
            "nominal_outboard_face_xyz_mm": head_face-h["head_height_mm"] if row["side"] == "head" else nut_face+h["nut_height_mm"]}
        for key, offset in offsets.items():
            close(list(map(float, row[key].split(";"))), [x+offset*d for x, d in zip(a["point_xyz_mm"], a["direction_xyz"], strict=True)], 2e-5)
        outward = [(-1 if row["side"] == "head" else 1)*d for d in a["direction_xyz"]]
        close(list(map(float, row["nominal_outward_removal_xyz"].split(";"))), outward)
        assert row["current_tool_access_disposition"] == row["current_axial_removal_disposition"] == "UNVERIFIED"
        assert row["prior_140_side_access_pass_transferred"] == "False"

    stock = read(PACKET / "stock-nesting.json")
    placed, board_feet, minimum = [], 0., math.inf
    for stick in stock["sticks"]:
        lengths = [profiles[n]["blank_mm"][0] for n in stick["members"]]
        close(lengths, stick["blank_lengths_mm"])
        consumed = sum(lengths) + len(lengths)*stock["kerf_mm_per_output_piece"] + 2*stock["end_trim_allowance_mm_each"]
        close(stick["consumed_with_kerf_and_trim_mm"], consumed)
        close(stick["remaining_mm"], stick["length_ft"]*304.8-consumed)
        minimum = min(minimum, stick["remaining_mm"])
        board_feet += (2 if stick["nominal_section"] == "4x6" else 1)*stick["length_ft"]
        for name in stick["members"]:
            close(profiles[name]["blank_mm"][1:], [139.7, 88.9 if stick["nominal_section"] == "4x6" else 38.1])
        placed.extend(stick["members"])
    assert len(placed) == len(set(placed)) == 22 and set(placed) == {n for n, p in profiles.items() if p["kind"] == "timber"}
    close(board_feet, 150.)
    close(minimum, 46.05)
    wood = {kind: math.fsum(p["finished"]["volume_mm3"] for p in profiles.values() if p["kind"] == kind)*500e-9 for kind in ("timber", "panel")}
    mass = sources["inventory"]["nominal_mass"]
    nonwood = sum(mass[key] for key in ("22_angles_at_drawing1_46lb_each_kg", "500_nominal_bolt_roles_kg", "66_screws_and142_Tnuts_saved_CAD_kg", "service_accessory_allowance_kg"))
    close(result["nominal_mass"]["conditional_total_kg"], sum(wood.values())+nonwood)
    recesses = read(PACKET / "rear-recesses.json")
    for recess in recesses:
        start, finish = recess["start_from_rear_heel_L_mm"], recess["finish_from_rear_heel_L_mm"]
        close(finish-start, 457.2)
        close((finish-start)/12, 38.1)
        p = profiles[recess["member"]]
        front_foot = min(v[0] for v in p["vertices_luv_mm"] if abs(v[2]+139.7) < 1e-6)
        volume = 38.1*139.7*(start-front_foot/2+(finish-start)/2)
        close(volume, recess["recorded_current_removed_volume_mm3"], 5e-6)
        assert recess["height_reference_is_not_a_cutter_clip"] is True
    assert result["release"] and not any(result["release"].values())
    close(.340625-(11.1125-10.31875)/2, -.05625)
    close(3.175/24, .13229166666666667)
    close(177.8*math.tan(math.radians(.1)), .3103199460705137)
    for name in frozen:
        if name.endswith(".svg"):
            root = ET.parse(PACKET / name).getroot()
            assert root.tag == "{http://www.w3.org/2000/svg}svg"

    # Reuse the producer's five stdlib byte/source rejection controls in a fresh
    # exclusive temporary output. No rendering, CAD library or solve is invoked.
    with tempfile.TemporaryDirectory(prefix="controls-", dir=OWN.parent) as temp:
        completed = subprocess.run([sys.executable, "-B", str(PACKET / "check_packet.py"), "--out", str(Path(temp) / "new")],
            cwd=ROOT, env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"}, capture_output=True, text=True, check=True)
        assert json.loads(completed.stdout)["checks"] == 5
    assert {name: sha(PACKET / name) for name in frozen} == frozen
    return {"schema": "eoere_extended_cleat_shop_independent_correctness_review/v1", "findings": [],
        "target_source_sha256": frozen, "review_helper_sha256": sha(OWN), "preserved_original_shop_files": 14,
        "producer_byte_replay_and_negative_controls": 5, "producer_source_closure_pins_rehashed": result["source_pin_count"],
        "independent_arithmetic": {"profiles": 28, "profile_vertices": vertices_checked, "outward_end_planes": planes_checked,
            "receiver_intervals_and_current_datums": 120, "Hillman_axes_and_local_frames": 66, "panel_machining_datums": 340,
            "complete_hardware_stack_windows": 100, "current_head_nut_recipe_positions_and_directions": 200,
            "unique_nested_timbers": 22, "stock_sticks": 13, "nominal_board_feet": board_feet,
            "minimum_stock_remaining_mm": minimum, "nominal_mass_kg": sum(wood.values())+nonwood,
            "analytic_recess_volumes": 2, "well_formed_SVGs": 9, "blank_observation_cells": blank_observations},
        "limits": ["Saved metadata, stdlib arithmetic and exact byte replay only; no new CAD/BRep queries, browser, native solve or current mechanical field.",
            "Four dedicated cleat/post stations retain HOLD; maximum-hole gap is negative before fabrication errors. Z180 proposal is unadopted.",
            "All200 tool/removal sides remain UNVERIFIED. Actual saw/drill/bit/clamp/fixture dimensions and tolerance budgets are still missing.",
            "Original14 shop files preserved; nominal mass/cost/stock composition transfers no old forces, structural passes or acceptance.",
            "No shared edits, geometry changes, staging, commit, physical observations or fabrication/strength/climbing release."],
        "release": result["release"]}


if __name__ == "__main__":
    receipt = main()
    destination = OWN.with_name("receipt.json")
    with destination.open("x") as stream:
        json.dump(receipt, stream, indent=2, sort_keys=True, allow_nan=False)
        stream.write("\n")
    print(json.dumps({"passed": True, "findings": receipt["findings"], "receipt_sha256": sha(destination),
        "independent_arithmetic": receipt["independent_arithmetic"]}))
