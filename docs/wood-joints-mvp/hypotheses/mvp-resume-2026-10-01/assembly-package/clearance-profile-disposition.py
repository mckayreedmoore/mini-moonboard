#!/usr/bin/env python3
"""Disposition the 13 frozen N18 nominal service/profile pairs with stdlib.

Import is inert. Source recipes are parsed, never imported or executed. This
producer loads no CAD, mesh engine, solver, numerical package or test. It
certifies separation of finite primary enclosures only; overlap stays pending.
"""

from __future__ import annotations

import argparse
import ast
import csv
import hashlib
import json
import math
import time
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
RAW = HERE / "rawlocal/clearance-profile-disposition"
H = "docs/wood-joints-mvp/hypotheses"
R = f"{H}/mvp-resume-2026-10-01"
A = f"{R}/assembly-package"
N18 = f"{A}/rawlocal/clearance-tolerance-completion"
BUNDLE = f"{H}/evaluation-resume-2026-09-24/current-full-frame-member-solids-attempt01/bundle"
SOURCES = {
    "setup": (f"{N18}/prepare-attempt02/setup.json", "bcff31877f53ca98f2388c80d4e17283cd5014c31f5c423918096a9d96ed4b8f"),
    "result": (f"{N18}/attempt01/result.json", "4a611a9dac0fb72ab5ee8093f51b5516a9ffa0a8711349f8a1a4dae6d80e7c0e"),
    "receipt": (f"{N18}/attempt01/receipt.json", "84a57bf3f0cc1d3bf0440577119435a276606a1db43bdf73d223206085ee8bed"),
    "exceptions": (f"{N18}/exception-attempt02/exceptions.json", "eafba2afa7bad4670b444333136856438a9ff4e235e76865041454b79d152a27"),
    "plan": (f"{N18}/exception-attempt02/query-plan.json", "fd9846557db76341cca6ef13f0a11eee3208c90ce7d0b47c3cbb3a1fbdbb4718"),
    "exception_receipt": (f"{N18}/exception-attempt02/receipt.json", "46677e744f337d59c342e7ca8f306596381fcc2261ebdbf69ae1d5f9ef4a984f"),
    "n18_py": (f"{A}/clearance-tolerance-completion.py", "9c73c99103ad95ecaf71a0deaa68bc8aa769ce18c36dc6f39a7e021bfa680505"),
    "n18_md": (f"{A}/clearance-tolerance-completion.md", "fd0276ef89bf51ada429a5bd09b77322ea38ddea8a652e7e276f022aac65a742"),
    "solids": (f"{BUNDLE}/current-full-frame-member-solids.json", "8979d678f7b45d3b75fa465e810b0910d72874c5c1c705290d1fcb2bf2b78420"),
    "model": (f"{R}/upper-corner-screw-layout/operators-attempt02/model-inputs.json", "e2109cabed9fcbc0a14346ef63b707abb1aed358ebf5fa126b2cba216aa771cc"),
    "surfaces": (f"{H}/current-finished-feature-register-2026-10-01/surfaces.json", "33fff67eee4bc4e96ccef5703f6eebd0d4e004541c6114a4b1da4a5332b2f6eb"),
    "stock": ("docs/floor-flush-construction-kerf-right/stock-profiles.json", "65a4301c639a6eff14cb4365f321d4ab4712746dd3c916ffc14b00645841dfa8"),
    "shop_manifest": ("docs/floor-flush-construction-kerf-right/manifest.json", "421c4d56a6494319e2b02888c00de68672bcceaa75fce9806be19794b581b879"),
    "panel_axes": ("docs/floor-flush-construction-kerf-right/panel-hole-axes.csv", "a735761d16c105db29ffc2bf897ea3af1764b5f41e87460585b391581a05b563"),
    "wiring": ("docs/round-service-wiring-reference.json", "b335fe3732c89e66625bac0525e959ccc562e2c7cd0e1e1551a4720fc26497f8"),
    "scene": ("site/owner-wood-joints-wj24-scene.json", "74845b2e97165488d020d6a26202d2372f09f299cb47c9f28a3ba4642fe628bf"),
}
RECIPES = {
    "mini_moonboard/panel_grid_v2.py": "666e0e5c5daa70eb08ad9c49312a5b4478bc20e7d4d58cfb5062ad3c4be96fe8",
    "mini_moonboard/round_service_wiring.py": "5404e6075b257138b269fb53edcae0893d9e88f7b1c32a0da9a87bd01c801dc2",
    "mini_moonboard/round_structural_wiring.py": "b802d10f1d73d2865e3a67613db0935ec2eec28d6222abc3b8c8c10dd3bbb5b2",
    "mini_moonboard/model.py": "aa4f80cbb1400d21ba9fa8c74b0773bd95f7c9644e7eecc06f94cd9f712b65ef",
    "mini_moonboard/product_frame.py": "9df692977f7b0a376ada34b7d5959f9ab2625119dd8b818c4ab838d006980f30",
    "mini_moonboard/hold_tnut_reinforcement.py": "62f2ea72f66a014a48423351b786314288a6b82cb6ec6318df7f54294b132390",
    "mini_moonboard/box_frame.py": "69650060048f51b45cf45b6ab916d4ad10a3aa25b8c498c1232d9dfe7aef72e5",
    "mini_moonboard/floor_flush_width.py": "1dc0b6cc6d1bd10ae8cffaaa707fa25bdcd264783dcb9ec59cf8b911a6512de5",
    "mini_moonboard/wood_joint_panel_machining.py": "1928e32ba5b5e75caca99abb42e5d5b01822d6697c6f892dda38650cca302afd",
    "scripts/owner_layout_protected.py": "405db94a8adc2da465d137d3b35bba5848fbe67cbd35d52c0613a01161560e58",
}
PAIRS = tuple(("wood/main_upper_left", f"light_{c}7") for c in "ABCDEF") + tuple(
    ("wood/main_upper_right", f"light_{c}7") for c in "GHIJK"
) + (("wood/wj04_lower_full_stock_cleat", "hold_tnut_main_G6"),
     ("wood/top_center_right_cleat", "hold_tnut_main_G12"))
FLAGS = dict.fromkeys(("criterion_closed", "complete_joint_acceptance", "proposal_adopted",
                       "physical_release", "fabrication_release", "machining_margin_qualified",
                       "loaded_clearance_qualified", "delivered_hardware_verified",
                       "geometry_changed", "scene_rebuilt", "native_or_frame_run", "tests_run",
                       "physical_collision_claim", "catalog_clearance_qualified"), False)
# This is the frozen panel-remachining datum/query resolution, not a shop tolerance.
LINEAR_RESOLUTION_MM = 1e-7


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def authenticate(pins):
    for path, expected in pins.items():
        require((ROOT / path).is_file() and sha(ROOT / path) == expected,
                f"Changed frozen source: {path}")


def read(name):
    return json.loads((ROOT / SOURCES[name][0]).read_text())


def write(path, data):
    path.write_text(json.dumps(data, sort_keys=True, indent=2, allow_nan=False) + "\n")


def fresh(output):
    output = Path(output).resolve()
    require(output.parent == RAW.resolve() and not output.exists(),
            "Require a fresh immediate child of rawlocal/clearance-profile-disposition")
    return output


def literal(name, variable):
    tree = ast.parse((ROOT / name).read_text())
    matches = [node.value for node in tree.body if isinstance(node, ast.Assign)
               and any(isinstance(target, ast.Name) and target.id == variable for target in node.targets)]
    require(len(matches) == 1, f"Expected one literal {variable} in {name}")
    return ast.literal_eval(matches[0])


def dot(first, second):
    return sum(a * b for a, b in zip(first, second, strict=True))


def offset(point, origin):
    return [a - b for a, b in zip(point, origin, strict=True)]


def advance(point, direction, length):
    return [p + d * length for p, d in zip(point, direction, strict=True)]


def cylinder_projection(cylinder, direction, origin):
    p = dot(offset(cylinder["start_xyz_mm"], origin), direction)
    axis_dot = dot(cylinder["axis_xyz"], direction)
    z = p + cylinder["length_mm"] * axis_dot
    radial = cylinder["radius_mm"] * math.sqrt(max(0, dot(direction, direction) - axis_dot ** 2))
    return [min(p, z) - radial, max(p, z) + radial]


def cylinder(start, axis, length, radius, role):
    return {"role": role, "start_xyz_mm": start, "axis_xyz": axis,
            "length_mm": length, "radius_mm": radius, "kind": "filled_outer_cylinder_enclosure"}


def source_setup():
    pins = {path: value for path, value in SOURCES.values()} | RECIPES
    authenticate(pins)
    old, result, receipt = read("setup"), read("result"), read("receipt")
    require(old["source_sha256"] == result["source_sha256"] == receipt["source_sha256"],
            "Original N18 source closures differ")
    require(len(old["source_sha256"]) == 628, "Original N18 closure is not 628 pins")
    for path, value in old["source_sha256"].items():
        require(path not in pins or pins[path] == value, f"Conflicting source pin: {path}")
        pins[path] = value
    pins[Path(__file__).resolve().relative_to(ROOT).as_posix()] = sha(__file__)
    authenticate(pins)
    plan, exceptions = read("plan"), read("exceptions")
    plan_rows = {(row["first"], row["second"]): row for row in plan["required_non_host_profile_queries"]}
    require(len(plan_rows) == 13 and set(plan_rows) == set(PAIRS), "Frozen 13-pair plan changed")
    require(read("exception_receipt")["output_sha256"]["exceptions.json"] == SOURCES["exceptions"][1]
            and read("exception_receipt")["output_sha256"]["query-plan.json"] == SOURCES["plan"][1],
            "Exception receipt output bindings differ")
    bundle, model, surfaces, stock, wiring, scene = (
        read(name) for name in ("solids", "model", "surfaces", "stock", "wiring", "scene"))
    shop = read("shop_manifest")
    for path, value in RECIPES.items():
        require(bundle["source_files_sha256"].get(path) == value,
                f"Primary recipe is not bound by the current saved-solid bundle: {path}")
        if path in shop["source_sha256"]:
            require(shop["source_sha256"][path] == value, f"Primary shop recipe differs: {path}")
    members = {row["member_id"]: row for row in model["members"]}
    bodies = {row["member_id"]: row for row in bundle["members"]}
    features = {row["member_id"]: row for row in surfaces["records"]}
    with (ROOT / SOURCES["panel_axes"][0]).open(newline="") as stream:
        axes = {(row["kind"], row["label"]): row for row in csv.DictReader(stream)}

    height = literal("mini_moonboard/panel_grid_v2.py", "PANEL_HEIGHT_MM")
    angle = math.radians(literal("mini_moonboard/model.py", "ANGLE_FROM_VERTICAL_DEG"))
    tangent, normal = [0, math.sin(angle), math.cos(angle)], [0, -math.cos(angle), math.sin(angle)]
    # The saved rear lower corner includes the current floor-flush translation.
    # No generic model-origin default or reconstructed scene is used.
    rear_corner = min(stock["main_lower_left"]["vertices_world_mm"], key=lambda p: p[1])
    origin = [0, rear_corner[1], rear_corner[2]]
    diameter = wiring["user_measurements"]["maximum_harness_outside_diameter_mm"]
    thickness = stock["main_upper_left"]["stock_blank_allowance_mm"][2]
    rear_projection = wiring["provisional_geometry_mm"]["rear_body_projection"]
    flange_diameter = literal("mini_moonboard/model.py", "V1_SELECTED_TNUT_FLANGE_DIAMETER_MM")
    flange_thickness = literal("mini_moonboard/model.py", "V1_SELECTED_TNUT_FLANGE_THICKNESS_MM")
    barrel_depth = literal("mini_moonboard/model.py", "V1_SELECTED_TNUT_BODY_DEPTH_MM")
    barrel_diameter = literal("mini_moonboard/hold_tnut_reinforcement.py", "PROVISIONAL_BARREL_DIAMETER_MM")
    queries = []
    for first, second in PAIRS:
        pair, body = plan_rows[first, second], first.removeprefix("wood/")
        saved, current = bodies[body], members[body]["current_finished_step_binding"]
        host = pair["effective_host"]
        require(host["sha256"] == saved["step_sha256"] == current["file_sha256"],
                f"Effective STEP binding differs: {body}")
        require(host["path"] == current["path"]
                and current["source_shape_fingerprint_sha256"] == saved["source_shape_fingerprint_sha256"]
                and current["step_roundtrip_checked"] and saved["bounds_and_volume_match_current_manifest"],
                f"Saved STEP/current source signature differs: {body}")
        require(pins[host["path"]] == host["sha256"], f"STEP missing from original closure: {body}")
        mesh = pair["saved_nominal_profile"]
        require(pins[mesh["path"]] == mesh["sha256"] and mesh["scene_translation_xyz_mm"] == [0, 0, 0],
                f"Saved service mesh/pose binding differs: {second}")
        require(second not in scene["revision_report"]["electrical_replacements"]
                and second not in scene["baseline_display_translations_mm"],
                f"Named service has a current replacement/translation: {second}")
        query = {"first": first, "second": second, "original_pair_line": pair["pair_line"],
                 "effective_host": host, "source_shape_fingerprint_sha256": saved["source_shape_fingerprint_sha256"],
                 "shape_summary_sha256": saved["shape_summary_sha256"], "saved_nominal_mesh": mesh,
                 "linear_resolution_mm": LINEAR_RESOLUTION_MM,
                 "catalog_margin_mm": None, "machining_margin_mm": None, "loaded_margin_mm": None,
                 "profile_is_recorded_nominal_model_only": True, **FLAGS}
        if second.startswith("light_"):
            label = second.removeprefix("light_")
            row = axes["LED", label]
            require(row["panel"] == "main_lower_" + body.removeprefix("main_upper_"),
                    f"LED7 panel identity differs: {label}")
            station = float(row["from_bottom_mm"])
            require(abs(station - (height - 20)) <= LINEAR_RESOLUTION_MM,
                    f"LED7 is not at the source row-7 datum: {label}")
            # Piercing and right-panel plug restoration stay within this outline.
            # The pinned panel-remachining recipe clips every restored plug to it.
            vertices = stock[body]["vertices_world_mm"]
            xmin, xmax = min(p[0] for p in vertices), max(p[0] for p in vertices)
            corners = [p for p in vertices if p[0] in (xmin, xmax)]
            s = [dot(offset(p, origin), tangent) for p in corners]
            require(len(corners) == 8 and abs(min(s) - height) <= LINEAR_RESOLUTION_MM
                    and abs(max(s) - 2 * height) <= LINEAR_RESOLUTION_MM,
                    f"Recorded finite upper-panel footprint differs: {body}")
            x = 200 * ("ABCDEFGHIJK".index(label[0]) + 1) - height
            start = advance(advance([x, origin[1], origin[2]], tangent, station), normal, -thickness)
            query.update({"kind": "LED7_upper_panel", "cylinder": cylinder(start, normal, thickness + rear_projection, diameter / 2, "nominal_light"),
                          "board_frame": {"origin_xyz_mm": origin, "tangent_xyz": tangent, "normal_xyz": normal},
                          "primary_panel_footprint_xsn_mm": [[xmin, xmax], [height, 2 * height], [-thickness, 0]],
                          "recorded_outer_corner_s_interval_mm": [min(s), max(s)],
                          "primary_light_s_interval_mm": [station - diameter / 2, station + diameter / 2],
                          "footprint_limit": "Exact current saved panel/source signatures; finite primary outline encloses holes and clipped restored plugs. JSON corner rounding is an identity diagnostic, not a machining interval."})
        else:
            label = second.removeprefix("hold_tnut_main_")
            row = axes["hold", label]
            station = float(row["from_bottom_mm"]) + (height if row["panel"].startswith("main_upper") else 0)
            x = 200 * ("ABCDEFGHIJK".index(label[0]) + 1) - height
            seat = advance([x, origin[1], origin[2]], tangent, station)
            into_panel = [-v for v in normal]
            feature = features[body]
            require(feature["step_binding"]["file_sha256"] == host["sha256"]
                    and feature["step_binding"]["source_shape_fingerprint_sha256"] == saved["source_shape_fingerprint_sha256"],
                    f"Current finished cleat feature binding differs: {body}")
            frame = feature["stock_frame"]
            # Use the enclosing current blank and recorded finished-face extents.
            # Cuts only remove material; a positive gap from this union is sufficient.
            bounds = [[min(0, *(f["bounds_stock_gqr_mm"][2 * i] for f in feature["features"])),
                       max(frame["original_dimensions_gqr_mm"][i], *(f["bounds_stock_gqr_mm"][2 * i + 1] for f in feature["features"]))]
                      for i in range(3)]
            query.update({"kind": "Tnut_cleat", "rear_seat_xyz_mm": seat,
                          "cylinders": [cylinder(seat, normal, flange_thickness, flange_diameter / 2, "filled_flange_enclosure"),
                                        cylinder(seat, into_panel, barrel_depth, barrel_diameter / 2, "filled_barrel_enclosure")],
                          "cleat_frame": frame, "cleat_enclosing_intervals_gqr_mm": bounds,
                          "omitted_profile_cuts": {"smooth_thread_opening_mm": literal("mini_moonboard/hold_tnut_reinforcement.py", "PROVISIONAL_SMOOTH_THREAD_OPENING_MM"),
                                                  "three_flange_retention_holes_mm": literal("mini_moonboard/model.py", "V1_SELECTED_TNUT_FLANGE_SCREW_HOLE_DIAMETER_MM"),
                                                  "retention_triangle_pitch_mm": literal("mini_moonboard/hold_tnut_reinforcement.py", "RETENTION_TRIANGLE_PITCH_MM")},
                          "overlap_method_limit": "Filled flange/barrel enclosures can certify separation only. Overlap requires the pinned saved nominal mesh or authenticated pierced-flange/smooth-bore recipe against the effective finished STEP. No exact T-nut STEP is supplied; clocking/depth/OD remain nominal hypotheses."})
        queries.append(query)
    wires = [row["original_pair"] for row in exceptions["exceptions"]
             if row["interpretation"] == "unresolved_saved_wire_timber_intersection"]
    require(len(wires) == 11 and all(row["exact_query"]["intersection_volume_mm3"] > 0 for row in wires),
            "Original 11 positive wire/timber intersections changed")
    authenticate(pins)
    return {"schema": "clearance_profile_disposition_setup/v1", "source_sha256": dict(sorted(pins.items())),
            "queries": queries, "primary_recipe_sha256": RECIPES, "parent_N18_source_pin_count": 628,
            "preserved_wire_intersections": wires, "original_N18_counts": result["counts"],
            "scope": "Only the 13 named non-host nominal profile pairs; not 274 intended panel interfaces or all N18",
            "status": "PREPARED_FINITE_PRIMARY_GEOMETRY", **FLAGS}


def publish(output, name, data, started, inputs=None):
    authenticate(data["source_sha256"])
    output.mkdir(parents=True)
    (output / ".gitignore").write_text("*\n")
    (output / "producer.snapshot.py").write_bytes(Path(__file__).read_bytes())
    write(output / name, data)
    authenticate(data["source_sha256"])
    receipt = {"source_sha256": data["source_sha256"], "input_artifacts": inputs or {},
               "output_sha256": {name: sha(output / name), "producer.snapshot.py": sha(output / "producer.snapshot.py")},
               "source_unchanged_after_run": True, "stdlib_runtime_seconds": time.perf_counter() - started,
               "CAD_imports": 0, "exact_geometry_queries": 0, **FLAGS}
    write(output / "receipt.json", receipt)
    return {"status": data["status"], "counts": data["counts"] if "counts" in data else {"prepared_pairs": len(data["queries"])},
            "output_sha256": receipt["output_sha256"], "receipt_sha256": sha(output / "receipt.json"),
            "stdlib_runtime_seconds": receipt["stdlib_runtime_seconds"]}


def prepare(output):
    """Authenticate and join recorded sources; publish a fresh 13-pair setup."""
    started = time.perf_counter()
    output = fresh(output)
    return publish(output, "setup.json", source_setup(), started)


def iter_queries(setup):
    """Yield the finite 13 source-bound descriptors, with no shape import."""
    data = setup if isinstance(setup, dict) else json.loads(Path(setup).read_text())
    require(len(data["queries"]) == 13 and {(q["first"], q["second"]) for q in data["queries"]} == set(PAIRS),
            "Require the frozen 13 named pairs")
    yield from data["queries"]


def evaluate(query):
    """Finite primary separation certificate or an explicitly unresolved overlap."""
    result = {**query, "exact_geometry_query_executed": False}
    if query["kind"] == "LED7_upper_panel":
        gap = query["primary_panel_footprint_xsn_mm"][1][0] - query["primary_light_s_interval_mm"][1]
        result.update({"projection_direction_xyz": query["board_frame"]["tangent_xyz"],
                       "finite_projection_lower_bound_mm": max(gap, 0),
                       "signed_s_separation_mm": gap,
                       "status": "NOMINAL_FINITE_FOOTPRINT_CYLINDER_SEPARATION" if gap > LINEAR_RESOLUTION_MM else "PRIMARY_ENCLOSURES_OVERLAP_PROFILE_METHOD_REQUIRED"})
    else:
        witnesses = []
        frame = query["cleat_frame"]
        for component in query["cylinders"]:
            intervals, gaps = [], []
            for basis, host_interval in zip(frame["basis_columns_global_xyz"], query["cleat_enclosing_intervals_gqr_mm"], strict=True):
                interval = cylinder_projection(component, basis, frame["origin_global_xyz_mm"])
                intervals.append(interval)
                gap = max(interval[0] - host_interval[1], host_interval[0] - interval[1], 0)
                gaps.append(gap / math.sqrt(dot(basis, basis)))
            witnesses.append({"role": component["role"], "projection_intervals_gqr_mm": intervals,
                              "axis_separation_lower_bounds_mm": gaps, "separation_lower_bound_mm": max(gaps)})
        gap = min(row["separation_lower_bound_mm"] for row in witnesses)
        result.update({"component_projection_witnesses": witnesses, "finite_projection_lower_bound_mm": gap,
                       "status": "NOMINAL_FINITE_TNUT_ENCLOSURE_SEPARATION" if gap > LINEAR_RESOLUTION_MM else "PRIMARY_ENCLOSURES_OVERLAP_PROFILE_METHOD_REQUIRED"})
    result["nominal_separation_certified"] = result["status"].startswith("NOMINAL_FINITE_")
    return result


def build(output, setup):
    """Evaluate only 13 stdlib projections; retain overlap/profile method limits."""
    started = time.perf_counter()
    output, setup = fresh(output), Path(setup).resolve()
    require(setup.name == "setup.json" and setup.parent.parent == RAW.resolve(), "Require a prepared setup in this leaf's raw folder")
    preparation = json.loads((setup.parent / "receipt.json").read_text())
    require(sha(setup) == preparation["output_sha256"]["setup.json"], "Prepared setup receipt differs")
    data = json.loads(setup.read_text())
    require(data["source_sha256"] == preparation["source_sha256"] and data["source_sha256"][Path(__file__).resolve().relative_to(ROOT).as_posix()] == sha(__file__),
            "Prepared sources or producer differ")
    authenticate(data["source_sha256"])
    pairs = [evaluate(query) for query in iter_queries(data)]
    report = {"schema": "clearance_profile_disposition_result/v1", "status": "FINITE_NOMINAL_PROFILE_DISPOSITIONS_RECORDED",
              "source_sha256": data["source_sha256"], "setup_sha256": sha(setup), "pairs": pairs,
              "counts": dict(Counter(row["status"] for row in pairs)),
              "specific_nominal_applicability_inventory_complete": True,
              "all_13_nominal_separations_certified": all(row["nominal_separation_certified"] for row in pairs),
              "pending_profile_pairs": [row for row in pairs if not row["nominal_separation_certified"]],
              "preserved_wire_intersections": data["preserved_wire_intersections"],
              "original_N18_counts": data["original_N18_counts"],
              "remaining_basis": ["These finite primary enclosures describe the pinned nominal display geometry only",
                                  "Delivered T-nut barrel OD/depth datum/clocking and electrical body/profile intervals remain unavailable",
                                  "274 intended panel receiver/profile fits retain their separate unsupported basis",
                                  "Machining and same-state relative loaded motion margins remain null; no 7.321 mm expansion",
                                  "Original 11 positive saved wire/timber intersections remain unresolved and unchanged"], **FLAGS}
    return publish(output, "result.json", report, started, {str(setup.relative_to(ROOT)): sha(setup)})


def run(output, setup):
    """Parent CLI spelling for the same finite stdlib build; never invokes CAD."""
    return build(output, setup)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("prepare", "build", "run"))
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--setup", type=Path)
    args = parser.parse_args()
    if args.mode != "prepare" and args.setup is None:
        parser.error("--setup is required for build/run")
    receipt = prepare(args.output) if args.mode == "prepare" else build(args.output, args.setup)
    print(json.dumps(receipt, sort_keys=True))


if __name__ == "__main__":
    main()
