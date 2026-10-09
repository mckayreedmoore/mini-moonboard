"""Independent saved-metadata/testing review; no CAD, native solve or browser."""
from __future__ import annotations

import collections
import csv
import hashlib
import json
import math
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET

sys.dont_write_bytecode = True
OWN = Path(__file__).resolve().parent
ROOT = next(p for p in OWN.parents if (p / "AGENTS.md").is_file())
DOC = ROOT / "docs/wood-joints-mvp/hypotheses/hl35-candidate/thin-frame-comparison/eoere-successor-v1/shop-assembly-v1/extended-cleat-followup-v1"
EXPECTED = {
    "result.json": "0f00a7ba22a08975adac6bf660db370866510c40b5d56e5829bfab9b2ad3f92e",
    "verification.json": "38aaa554039e3dd5c5bbcf7545c3dc6b6339b7dd9dc93af6ac9cecc327e9f721",
}


def digest(p):
    h = hashlib.sha256()
    with Path(p).open("rb") as f:
        for chunk in iter(lambda: f.read(1048576), b""):
            h.update(chunk)
    return h.hexdigest()


def read(p):
    return json.loads(Path(p).read_text())


def canon(x):
    return hashlib.sha256(json.dumps(x, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest()


def rows(n):
    with (DOC / n).open(newline="") as f:
        return list(csv.DictReader(f))


def vec(r, prefix, axes="xyz", suffix="mm"):
    return [float(r[f"{prefix}_{a}_{suffix}"]) for a in axes]


def dot(a, b):
    return math.fsum(x*y for x, y in zip(a, b, strict=True))


def add(a, b):
    return [x+y for x, y in zip(a, b, strict=True)]


def mul(a, s):
    return [x*s for x in a]


def world(p, profile):
    return [profile["datum_xyz_mm"][i] + math.fsum(p[k]*profile["basis_grain_u_v_xyz"][k][i] for k in range(3)) for i in range(3)]


def local(p, profile):
    d = [x-y for x, y in zip(p, profile["datum_xyz_mm"], strict=True)]
    return [dot(d, a) for a in profile["basis_grain_u_v_xyz"]]


maximum = collections.defaultdict(float)


def near(a, b, label, tolerance=1e-5):
    if isinstance(a, (tuple, list)):
        assert len(a) == len(b), label
        for x, y in zip(a, b, strict=True):
            near(x, y, label, tolerance)
    else:
        error = abs(float(a)-float(b))
        assert math.isfinite(error) and error <= tolerance, (label, a, b, error)
        maximum[label] = max(maximum[label], error)


def command(script, args):
    result = subprocess.run([sys.executable, "-B", str(script), *map(str, args)], cwd=ROOT,
                            capture_output=True, text=True, check=False, timeout=120)
    assert result.returncode == 0, (result.returncode, result.stderr)
    return result.stdout


def main():
    assert not (OWN / "receipt.json").exists(), "do not overwrite a review receipt"
    before = {p.name: digest(p) for p in DOC.iterdir() if p.is_file()}
    assert len(before) == 26 and sum(p.stat().st_size for p in DOC.iterdir() if p.is_file()) == 615144
    assert all(before[n] == h for n, h in EXPECTED.items())
    issued, verification, inputs = (read(DOC / n) for n in ("result.json", "verification.json", "inputs.json"))
    assert len(verification["owned_artifacts"]) == 25
    for name, ref in verification["owned_artifacts"].items():
        assert before[name] == ref["sha256"] and (DOC/name).stat().st_size == ref["bytes"]
    assert sum(r["bytes"] for r in verification["owned_artifacts"].values()) == 606168
    for name, ref in issued["files"].items():
        assert before[name] == ref["sha256"] and (DOC/name).stat().st_size == ref["bytes"]
    assert issued["helper_sha256"] == before["export.py"] and issued["inputs_sha256"] == before["inputs.json"]
    data, pins = {}, {}
    def pin(path, expected):
        assert path not in pins or pins[path] == expected, ("conflicting source", path)
        pins[path] = expected
    for key, ref in inputs["sources"].items():
        p = ROOT/ref["path"]
        assert p.stat().st_size == ref["bytes"] and digest(p) == ref["sha256"]
        pin(ref["path"], ref["sha256"])
        if p.suffix == ".json":
            data[key] = read(p)
    assert inputs["optional_extra_grid"] is False and verification["optional_extra_grid"] is False
    assert inputs["revision"] == issued["revision"] == "eoere-base-side-edge-cleats-v1"
    assert inputs["base_revision"] == "eoere-midpoint-ready-frame-v3"
    assert data["extension"]["axes"] == data["base"]["axes"]
    assert data["extension"]["screw_axes"] == data["base"]["screw_axes"]
    for key in ("aligned", "base", "extension"):
        for path, h in data[key]["source_sha256"].items():
            pin(path, h)
    for ref in data["old_result"]["sources"].values():
        pin(ref["path"], ref["sha256"])
    finished = {r["id"]: r for r in [*data["aligned"]["changed_finished_solids"], *data["aligned"]["unchanged_finished_solids"], *data["bottom"]["finished_panel_solids"]]}
    finished.update({r["id"]: r for r in data["base"]["changed_finished_solids"] if r["kind"] in ("timber", "panel")})
    finished.update({r["id"]: r for r in data["extension"]["changed_finished_solids"]})
    for ref in finished.values():
        pin(ref["path"], ref["sha256"])
    assert len(pins) == 864 == issued["source_pin_count"] == verification["source_pins_checked_before_after"]
    assert canon(pins) == issued["source_map_canonical_sha256"]
    for path, h in pins.items():
        assert digest(ROOT/path) == h, path
    assert len(verification["preserved_original_14_shop_artifact_sha256"]) == 14
    for path, h in verification["preserved_original_14_shop_artifact_sha256"].items():
        assert digest(ROOT/path) == h, path

    profiles = read(DOC/"current_profiles.json")
    members, ends, holes, screws, stacks, access, machining = [rows(n) for n in ("members.csv", "member-end-datums.csv", "receiver-holes.csv", "panel-screw-datums.csv", "bolt-stacks.csv", "access-sides.csv", "panel-machining.csv")]
    assert [len(r) for r in (members, holes, screws, stacks, access, machining)] == [28, 120, 66, 100, 200, 340]
    assert len(profiles) == len(finished) == 28
    for table in (members, ends, holes, screws, stacks, access, machining):
        assert all(value == "" for r in table for k, value in r.items() if k.startswith("Actual") or k == "Disposition")
    assert collections.Counter(p["kind"] for p in profiles.values()) == {"timber": 22, "panel": 6}
    for r in members:
        p = profiles[r["member"]]
        assert p["finished"] == finished[r["member"]]
        near(vec(r, "datum"), p["datum_xyz_mm"], "member_datums")
        near([float(r[f"nominal_blank_{d}_mm"]) for d in ("length", "depth", "thickness")], p["blank_mm"], "blank_table")
        near([vec(r, f"basis_{a}", suffix="unitless") for a in "luv"], p["basis_grain_u_v_xyz"], "basis_table")
        for i, a in enumerate(p["basis_grain_u_v_xyz"]):
            for j, b in enumerate(p["basis_grain_u_v_xyz"]):
                near(dot(a, b), int(i == j), "orthonormal_basis", 1e-8)
        for v in p["vertices_luv_mm"]:
            near(local(world(v, p), p), v, "vertex_roundtrip")
        if p["kind"] == "timber":
            extents = [max(v[i] for v in p["vertices_luv_mm"])-min(v[i] for v in p["vertices_luv_mm"]) for i in range(3)]
            # Header U is its depth; other frames may put thickness on U.
            for extent, blank in zip([extents[0], *sorted(extents[1:])], [p["blank_mm"][0], *sorted(p["blank_mm"][1:])], strict=True):
                assert extent <= blank + 1e-5, r["member"]
        for plane in p["end_planes"]:
            n = vec(plane, "outward_normal", "luv", "unitless")
            offset = float(plane["plane_offset_from_datum_mm"])
            near(dot(n, n), 1, "unit_end_normals")
            near(math.degrees(math.acos(abs(n[0]))), plane["normal_to_L_deg"], "end_normal_angles")
            for i in map(int, str(plane["plane_source_vertex_indices"]).split(";")):
                near(dot(p["vertices_luv_mm"][i], n), offset, "end_plane_vertices")
            assert max(dot(v, n)-offset for v in p["vertices_luv_mm"]) < 1e-5
    for r in ends:
        if r["record_kind"] != "raw_end_plane":
            p = profiles[r["member"]]
            near(vec(r, "point", "luv"), p["vertices_luv_mm"][int(r["source_index"])], "end_vertex_table")
            near(vec(r, "point"), world(vec(r, "point", "luv"), p), "end_world_table")

    axes = {a["id"]: a for a in data["extension"]["axes"]}
    screws_by_id = {a["axis_id"]: a for a in data["extension"]["screw_axes"]}
    assert len(axes) == 100 and len(screws_by_id) == 66
    assert {(r["axis_id"], r["receiver"]) for r in holes} == {(a["id"], r) for a in axes.values() for r in a["receivers"]}
    grips = collections.defaultdict(float)
    for r in holes:
        a, p = axes[r["axis_id"]], profiles[r["receiver"]]
        near(vec(r, "axis_point"), a["point_xyz_mm"], "hole_world_origin")
        near(vec(r, "axis_direction", suffix="unitless"), a["direction_xyz"], "hole_axis_direction")
        for label, t in (("axis_point", 0), ("entry", float(r["entry_from_axis_point_mm"])), ("exit", float(r["exit_from_axis_point_mm"]))):
            near(vec(r, f"{label}_in_receiver", "luv"), local(add(a["point_xyz_mm"], mul(a["direction_xyz"], t)), p), "receiver_coordinates")
        length = float(r["exit_from_axis_point_mm"])-float(r["entry_from_axis_point_mm"])
        assert length > 0
        near(length, r["saved_full_wall_length_mm"], "saved_interval_length")
        near(r["nominal_shaft_diameter_mm"], a["diameter_mm"], "hole_shaft_recipe")
        near(r["modeled_bore_envelope_diameter_mm"], a["bore_diameter_mm"], "hole_bore_recipe")
        grips[r["axis_id"]] += length
    for aid, grip in grips.items():
        near(grip, axes[aid]["grip_mm"], "grip_sum")
    assert {r["axis_id"] for r in screws} == set(screws_by_id)
    for r in screws:
        a = screws_by_id[r["axis_id"]]
        assert (r["panel"], r["receiver"]) == (a["panel"], a["receiver"])
        near(vec(r, "front_axis_origin"), a["origin_xyz_mm"], "screw_world_origin")
        near(vec(r, "axis_direction", suffix="unitless"), a["direction_xyz"], "screw_direction")
        for role in ("panel", "receiver"):
            near(vec(r, f"origin_in_{role}", "luv"), local(a["origin_xyz_mm"], profiles[a[role]]), "screw_local_datums")
    assert collections.Counter(r["kind"] for r in machining) == {"tnut": 142, "light": 132, "conditional_screw_clearance": 66}
    assert len({r["identity"] for r in machining}) == 340
    for r, f in zip(machining, data["bottom"]["panel_machining"]["features"], strict=True):
        assert (r["identity"], r["panel"], r["kind"]) == (f["identity"], f["panel"], f["kind"])
        origin = screws_by_id[r["identity"]]["origin_xyz_mm"] if r["identity"] in screws_by_id else f["start_xyz_mm"]
        near(vec(r, "origin"), origin, "machining_world_datums")
        near(vec(r, "direction", suffix="unitless"), f["direction_xyz"], "machining_directions")
        near(vec(r, "origin_in_panel", "luv"), local(origin, profiles[r["panel"]]), "machining_local_datums")

    stack_by_id = {r["axis_id"]: r for r in stacks}
    assert set(stack_by_id) == set(axes) and len(stack_by_id) == 100
    short = 0
    for r in stacks:
        a = axes[r["axis_id"]]
        assert r["receiver_member_ids"].split(";") == a["receivers"]
        s, w, h, length, pitch = [float(r[k]) for k in ("receiver_plus_plate_mm", "model_each_washer_thickness_mm", "model_nut_height_mm", "nominal_underhead_length_mm", "UNC_threads_per_inch")]
        pitch = 25.4/pitch
        near(s, a["grip_mm"]+a["before_plate_mm"]+a["after_plate_mm"], "stack_wood_and_plate")
        near(length, a["nominal_under_head_length_mm"], "stack_length")
        near(r["model_nut_near_underhead_mm"], s+2*w, "model_nut_seat")
        near(r["model_tip_projection_mm"], length-s-2*w-h, "model_tip")
        near(r["model_two_tip_pitch_margin_mm"], length-s-2*w-h-2*pitch, "model_margin")
        near(r["model_body_to_farthest_bearing_target_mm"], s+w, "model_body_target")
        lmin, wmax, hmax = [float(r[k]) for k in ("catalog_underhead_min_mm", "catalog_each_washer_max_mm", "catalog_nut_height_max_mm")]
        margin = lmin-s-2*wmax-hmax-2*pitch
        near(r["catalog_min_length_max_stack_two_pitch_margin_mm"], margin, "catalog_margin")
        near(r["catalog_equal_washer_ceiling_mm"], (lmin-s-hmax-2*pitch)/2, "catalog_washer_ceiling")
        assert r["catalog_box_disposition"] == ("SHORT_STACK_COMPARISON" if margin < 0 else "NONNEGATIVE_COMPARISON")
        assert r["part_receiving_disposition"] == "UNVERIFIED" and r["geometry_access_disposition"] == "NOMINAL_ONLY"
        short += margin < 0
    assert short == 24
    assert {(r["axis_id"], r["side"]) for r in access} == {(aid, side) for aid in axes for side in ("head", "nut")}
    for r in access:
        a, s = axes[r["axis_id"]], stack_by_id[r["axis_id"]]
        assert r["current_tool_access_disposition"] == r["current_axial_removal_disposition"] == "UNVERIFIED"
        assert r["prior_140_side_access_pass_transferred"] == "False"
        split = lambda key: list(map(float, r[key].split(";")))
        near(split("axis_origin_xyz_mm"), a["point_xyz_mm"], "access_origin")
        near(split("axis_positive_xyz"), a["direction_xyz"], "access_positive_axis")
        inward = mul(a["direction_xyz"], 1 if r["side"] == "head" else -1)
        near(split("nominal_inward_approach_xyz"), inward, "access_inward")
        near(split("nominal_outward_removal_xyz"), mul(inward, -1), "access_removal")
        w = float(s["model_each_washer_thickness_mm"])
        t = -a["before_plate_mm"]-w if r["side"] == "head" else a["grip_mm"]+a["after_plate_mm"]+w
        near(split("nominal_bearing_face_xyz_mm"), add(a["point_xyz_mm"], mul(a["direction_xyz"], t)), "access_bearing")
        outward = t-float(s["model_head_height_mm"]) if r["side"] == "head" else t+float(s["model_nut_height_mm"])
        near(split("nominal_outboard_face_xyz_mm"), add(a["point_xyz_mm"], mul(a["direction_xyz"], outward)), "access_outboard")
        tip = a["nominal_under_head_length_mm"]-a["before_plate_mm"]-w
        near(split("nominal_tip_xyz_mm"), add(a["point_xyz_mm"], mul(a["direction_xyz"], tip)), "access_tip")

    stock = read(DOC/"stock-nesting.json")
    allocation = [name for stick in stock["sticks"] for name in stick["members"]]
    assert len(allocation) == len(set(allocation)) == 22
    assert set(allocation) == {n for n, p in profiles.items() if p["kind"] == "timber"}
    purchase = collections.Counter()
    for stick in stock["sticks"]:
        lengths = [profiles[n]["blank_mm"][0] for n in stick["members"]]
        near(stick["blank_lengths_mm"], lengths, "nested_blanks")
        consumed = math.fsum(lengths)+len(lengths)*3.175+2*12.7
        near(stick["consumed_with_kerf_and_trim_mm"], consumed, "kerf_and_two_trims")
        near(stick["remaining_mm"], stick["length_ft"]*304.8-consumed, "stock_remainder")
        assert stick["remaining_mm"] > 0
        purchase[(stick["nominal_section"], stick["length_ft"])] += 1
        thickness = 88.9 if stick["nominal_section"] == "4x6" else 38.1
        for n in stick["members"]:
            near(profiles[n]["blank_mm"][1:], [139.7, thickness], "stock_section_match")
    assert purchase == {("2x6", 8): 6, ("2x6", 10): 3, ("4x6", 8): 2, ("4x6", 10): 2}
    near(stock["minimum_nominal_remaining_mm"], 46.05, "minimum_stock_spare")
    board_feet = sum(int(section[0])*6*length*quantity/12 for (section, length), quantity in purchase.items())
    near(board_feet, 150, "nominal_board_feet")
    for recess in read(DOC/"rear-recesses.json"):
        start, finish = recess["start_from_rear_heel_L_mm"], recess["finish_from_rear_heel_L_mm"]
        near(finish-start, 457.2, "recess_return")
        front_foot = min(v[0] for v in profiles[recess["member"]]["vertices_luv_mm"] if abs(v[2]+139.7) < 1e-5)
        # Integrate the depth law, subtracting the triangular raw foot bevel.
        volume = 139.7*(38.1*start+38.1*(finish-start)/2-38.1*front_foot/2)
        near(volume, recess["recorded_current_removed_volume_mm3"], "recess_integral", 1e-4)
    near(8-10.31875/2-5/2, .340625, "held_nominal_gap")
    near(8-11.1125/2-5/2, -.05625, "held_maximum_bore_gap")
    near(12-11.1125/2-5/2, 3.94375, "unadopted_Z180_gap")
    near(177.8*math.tan(math.radians(.1)), .310319, "fixture_axis_tilt", 1e-6)
    near(3.175/24, .13229166666666667, "taper_kerf_depth_allowance")
    near([88.9+19.05+6.35, 177.8+19.05+6.35], [114.3, 203.2], "fixture_reach")
    timber_volume = math.fsum(p["finished"]["volume_mm3"] for p in profiles.values() if p["kind"] == "timber")
    panel_volume = math.fsum(p["finished"]["volume_mm3"] for p in profiles.values() if p["kind"] == "panel")
    mass = issued["nominal_mass"]
    near(timber_volume, mass["finished_timber_volume_mm3"], "mass_timber_volume")
    near(panel_volume, mass["finished_panel_volume_mm3"], "mass_panel_volume")
    near((timber_volume+panel_volume)*500e-9+mass["preserved_nominal_nonwood_and_25kg_allowance_kg"], 219.11593970030574, "nominal_mass")
    assert mass["actual_total_kg"] is None and mass["optional_extra_grid_included"] is False
    assert all(value is False for value in issued["release"].values())
    assert issued["execution"]["CAD_or_native_execution"] is False and issued["execution"]["mechanics"] is False

    svg_names = sorted(p.name for p in DOC.glob("*.svg"))
    assert len(svg_names) == 9
    parsed = {n: ET.parse(DOC/n).getroot() for n in svg_names}
    elements = lambda e, name: [x for x in e.iter() if x.tag.split("}")[-1] == name]
    assert sum(len(elements(parsed[n], "circle")) for n in svg_names if n.startswith("member-projections")) == 120
    assert sum(len(elements(parsed[n], "polygon")) for n in svg_names if n.startswith("member-projections")) == 28
    assert sum(len(elements(parsed[n], "circle")) for n in svg_names if n.startswith("panel-layout")) == 340
    assert len(elements(parsed["extended-cleats.svg"], "circle")) == 4
    browser_ref = verification["drawings"]
    assert digest(ROOT/browser_ref["path"]) == browser_ref["sha256"]
    browser = read(ROOT/browser_ref["path"])
    assert browser["passed"] and browser["errors"] == browser["overflow"] == []
    assert browser["checker_sha256"] == before["check-drawings.cjs"]
    assert sorted(r["file"] for r in browser["captures"]) == svg_names
    for capture in browser["captures"]:
        assert capture["sha256"] == before[capture["file"]]
        assert capture["text_count"] == len(elements(parsed[capture["file"]], "text"))
        assert digest(ROOT/capture["screenshot"]["path"]) == capture["screenshot"]["sha256"]
    assert digest(browser["shared_runner"]["path"]) == browser["shared_runner"]["sha256"]
    assert browser["browser_page_code_evaluation"] is False and browser["geometry_or_mechanics_acceptance"] is False
    control_ref = verification["controls"]
    assert digest(ROOT/control_ref["path"]) == control_ref["sha256"]
    controls = read(ROOT/control_ref["path"])
    assert controls["passed"] and len(controls["checks"]) == 5
    assert controls["checker_sha256"] == before["check_packet.py"]
    assert controls["packet_sha256"] == {n: h for n, h in before.items() if n != "verification.json"}
    link_count = 0
    for link in re.findall(r"\]\(([^)]+)\)", (DOC/"README.md").read_text()):
        if "://" not in link and not link.startswith("#"):
            assert (DOC/link.split("#")[0].split("?")[0]).resolve().exists(), link
            link_count += 1
    assert link_count == 25

    with tempfile.TemporaryDirectory(prefix="cheap-checks-", dir=OWN) as temp:
        temp = Path(temp)
        replay = json.loads(command(DOC/"export.py", ["--check"]))
        fresh = temp/"fresh-export"
        command(DOC/"export.py", ["--out", fresh])
        assert {p.name for p in fresh.iterdir()} == {*issued["files"], "result.json"}
        for p in fresh.iterdir():
            assert digest(p) == before[p.name], p.name
        out = temp/"producer-controls"
        command(DOC/"check_packet.py", ["--out", out])
        fresh_controls = read(out/"result.json")
        assert len(fresh_controls["checks"]) == 5 and fresh_controls["passed"]
        assert fresh_controls["packet_sha256"] == before
        control_names = [r["name"] for r in fresh_controls["checks"]]
    assert before == {p.name: digest(p) for p in DOC.iterdir() if p.is_file()}
    for path, h in pins.items():
        assert digest(ROOT/path) == h, ("source changed during review", path)
    receipt = {
        "schema": "eoere_extended_cleat_shop_testing_review/v1", "passed": True, "substantial_findings": [],
        "packet": {"path": str(DOC.relative_to(ROOT)), "files": 26, "bytes": 615144, "sha256": before},
        "reviewer_sha256": digest(Path(__file__)), "source_pins": {"count": len(pins), "canonical_sha256": canon(pins), "before_and_after": True},
        "preserved_original_shop_files_checked": 14, "independent_saved_metadata": {"member_profiles": 28, "end_records": len(ends), "receiver_holes": 120, "screws": 66, "stacks": 100, "tool_sides": 200, "panel_features": 340, "nominal_mass_kg": mass["conditional_total_kg"], "stock_sticks": 13, "minimum_spare_mm": 46.05, "catalog_short_comparisons": 24, "maximum_errors": dict(maximum)},
        "fresh_reproduction": {"generated_files": len(issued["files"])+1, "exact_bytes": True, "export_summary": replay, "producer_checks_rerun": control_names, "temporary_outputs_removed": True},
        "saved_browser_evidence_reused": {"result": browser_ref, "all_svg_and_nine_screenshot_hashes_checked": True, "checker_and_shared_runner_hashes_checked": True, "new_browser_execution": False, "producer_visual_inspection_reused": True, "independent_visual_inspection": False},
        "drawing_metadata": {"svgs": 9, "member_outlines": 28, "receiver_entry_targets": 120, "panel_feature_targets": 340, "cleat_axis_targets": 4, "local_links": link_count},
        "coverage_limits": ["Saved receiver wall intervals are reused, not independently queried against current BREP solids.", "Replay is consistency evidence; independent checks here cover saved coordinates, normals, planes, nominal stack arithmetic, stock/kerf/trim allocation, recess integration and SVG census.", "Browser evidence checks SVG parsing/text bounds and saved capture bindings; it does not qualify drawing dimensions, machining or tools.", "No observed material/tool/hardware dimensions, cut/drill fixtures, physical fit, mass or pricing are established; Actual/Disposition cells stay blank.", "All200 current tool/removal sides stay UNVERIFIED; four lower cleat/post stations stay HOLD; Z180 remains unadopted.", "No CAD/BREP execution, native solve, force-method audit, strength acceptance, browser launch, model edit, staging or commit."],
        "release": issued["release"], "target_and_inherited_bytes_unchanged": True,
    }
    with (OWN/"receipt.json").open("x") as f:
        json.dump(receipt, f, indent=2, sort_keys=True, allow_nan=False)
        f.write("\n")
    print(json.dumps({"passed": True, "receipt_sha256": digest(OWN/"receipt.json"), "findings": 0, "source_pins": len(pins)}))


if __name__ == "__main__":
    main()
