"""N15 saved lower-panel/kicker paths; parent executes build(output).

Import is inert. prepare(output) authenticates and joins JSON only, using the
standard library. build(output) reads saved arrays and exact planar recipes;
it does not solve, mesh, change geometry, or evaluate N14 screw resistance.
"""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
import math
import sys
from collections import Counter, defaultdict
from itertools import pairwise
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
BASE = HERE.parent
HYPOTHESES = BASE.parent
RAW = HERE / "rawlocal/kicker-path-completion"
GRAVITY = HERE / "rawlocal/knee-bridge-gravity/attempt01"
ASSESSMENT = GRAVITY / "operator-assessment.json"
COMPARISON = HERE / "rawlocal/knee-bridge-frame/attempt02/response/comparison.json"
RESPONSE = COMPARISON.with_name("response.npz")
MODEL = GRAVITY / "model.json"
INPUTS = GRAVITY / "model-inputs.json"
ROWS = GRAVITY / "row-identities.json"
OPERATORS = GRAVITY / "operators.npz"
MEMBERS = HERE / "rawlocal/knee-bridge-members/attempt01"
PACKAGE = HERE / "rawlocal/knee-bridge-working-package/attempt02"
GEOMETRY = BASE / "member-screen-attempt02/knee-bridge-gravity01/geometry.json"
FEATURES = HYPOTHESES / "current-finished-feature-register-2026-10-01/axis-features.json"
SURFACES = FEATURES.with_name("surfaces.json")
CARRIER = HYPOTHESES / "mvp-acceleration-2026-09-28/current-springa-frame-input-adapter-attempt01/a12-rear/model.json"
CONTACTS = HYPOTHESES / "mvp-acceleration-2026-09-28/reduced-static-attempt01/contact-geometry.json"
CORRECTED = BASE / "top-corner-contact-geometry.json"
SETUP = HERE / "rawlocal/attempt01/setup.json"
MOVED = SETUP.with_name("result.json")
KERF = ROOT / "docs/floor-flush-construction-kerf-right"
OFFICIAL = ROOT / "docs/floor-flush-construction"
WRENCH = BASE / "top_corner_actions.py"
BEARING = ROOT / "scripts/floor_flush_checks.py"
CASES = ("a12-rear", "a12-forward", "a12-left", "k12-right", "k12-rear", "a1-rear")
PANELS = ("main_upper_left", "main_upper_right", "main_lower_left", "main_lower_right", "kicker_left", "kicker_right")
FOCUS = ("main_lower_left", "main_lower_right", "kicker_left", "kicker_right")
AXIAL = "non_qualifying_parametric_screw_withdrawal"
LATERAL = "panel_screw_lateral_plane"
CONTACT = "timber_or_panel_contact"
PINS = {
    ROOT / "current-candidate.json": "f4505746a0a33eac1771708fbc376686b801e2c2af3053d9447fbbc6e22491a4",
    ROOT / "wood-joints-candidate.json": "2d1c43eae6f1515ad9fbb052d208b14648f4bf4f9003f49a7268d2ecb8ec545d",
    ASSESSMENT: "ce69ba58e3c6265d31ab0dfdec1ffac4c019b93fc1106c8f9677ed9b5b2c3f95",
    COMPARISON: "c3a8ff024fb494032d947aedfd6f00cda8698587b8751b2cec66e4b3af243729",
    RESPONSE: "62bd4116cfb577a0846f4de0d43fbeec6bb704bac7feee530ee673ded1820f90",
    MODEL: "c14e93e003da72478e2db777cecab1aab7d5a9f7e3b12bdbd6813337f15572c1",
    INPUTS: "b260af3d53a199e66962caf6c7074086e1d433526e43d263a3f1247ba4c61b99",
    ROWS: "cdf218780bdabdb8774174c79b37d7c9f554abc6be2e1f817999635e56868b27",
    OPERATORS: "7877699053a8285b77621ca0cfcb7b09d22b19e5c20729c193e1e5c3f4840e4f",
    MEMBERS / "checks.json": "0d623eb62605ddac9aa5111e2469a1c63f4857e356fe607741fc425d5ea59e65",
    MEMBERS / "receipt.json": "fa4d5f5568d53c0e4e62a74d31a814738b39a78951a4c27ae6e4c141ef5be794",
    PACKAGE / "manifest.json": "4c0d10a86a6018813b5f8efcd7f438662037e458ef3f2ce535d1e0860ca25bd0",
    PACKAGE / "receipt.json": "5fa8cc849e4a2fa042a1cffa6d2957d4163597c7999dbcef1f57563dfdd83e7b",
    GEOMETRY: "c61139087fac34e8094f2336f15dd6de5c0112d26d37b9535526f47332f453af",
    FEATURES: "bebb4274cdecfb6ad0b0f26850d85a16570c245ea9f7d478c0b05c12b4513e19",
    SURFACES: "33fff67eee4bc4e96ccef5703f6eebd0d4e004541c6114a4b1da4a5332b2f6eb",
    CARRIER: "61f95ec9e670b2bd0e95d426cc14ff381283edfc4f9c87e47c2b344dd4fe50b8",
    CONTACTS: "034067430fff5207cdb40819fa8118a367edeb29a8d83926928cc96a0e87d151",
    CORRECTED: "987af6908d6677165b6a712537ecca0c02827d558ca386ced96f4c1f6436008f",
    SETUP: "00cfa71d30a1d8d789df7c4a40770f9ec46e3e56c0ee9d23018d62e6c11583bc",
    MOVED: "81b75c3fe8dced195d36d3a2a3f1ca69b1e796b89e048870a16e3864bb5a06d9",
    KERF / "manifest.json": "421c4d56a6494319e2b02888c00de68672bcceaa75fce9806be19794b581b879",
    KERF / "stock-profiles.json": "65a4301c639a6eff14cb4365f321d4ab4712746dd3c916ffc14b00645841dfa8",
    OFFICIAL / "stock-profiles.json": "8d02e22de871e04a20e25f253639f360ac974aa71824a40986e0e2a317dfca3d",
    ROOT / "docs/floor-flush-width-option.md": "6fc59af8ff374fc6927ef2e5b7bb75ad2640662f6219576b36e6e9b2fa569224",
    ROOT / "docs/wood-joints-mvp/current-kicker-edge-obligation.md": "094702ceb9a8b5278d6ac1053575c2d0310f2af72244e1ed19a5815a492f082b",
    WRENCH: "bfe51728521b620e54fa23822f4e3b3cee320457503580cf95ab439863327bd5",
    BEARING: "8d756c608bef10b8ce6f5141e58cbb0c08df56b0e422b6fd8baa262cec61e9cf",
}
LIMITS = [
    "The reviewed 104-axis authority is preserved. Fresh ce69/c3a8/62bd forces belong to the unadopted 108-axis proposal; its four internal spine ties are not global receiver rows.",
    "A matched bore or saved cylinder intersection is exact modeled receiver correspondence, not delivered thread engagement, screw strength, installation or bearing support. Historical 50.8 mm occupancy is not purchased 63.5 mm thread length.",
    "N14 owns head/withdrawal/lateral/steel interaction and plywood bending/contact sharing. No screw capacity, panel product, layup or redistribution is invented here.",
    "Geometric edge intervals use exact finite plane-boundary recipes, including complete circular holes. They describe potential direct backing, not active pressure or required continuous backing. Unsupported curves remain null.",
    "The 19.05 mm edge strip is a reported geometric diagnostic, not a new acceptance criterion or a change to a panel or receiver. Its two boundary lines do not prove two-dimensional full-strip support.",
    "Compression means use saved positive cell forces and explicit represented areas. Perpendicular timber bearing uses the existing conditional 625 psi DF-L reference. Oblique, parallel, plywood, local peak and splitting resistance remain unassessed here.",
    "Saved timber references retain original CD1 and conditional CD1.25, seven cumulative peak days, assumed restraints, rectangular torsion and local-opening nulls. A connected graph or a small member reference does not prove complete connection resistance.",
    "Seam contact is panel/panel and unilateral; it supplies no timber-backed tensile seam tie. Post/header seat and post/cleat/header connections are distinct simultaneous routes, not duplicate loads or isolated alternative allocations.",
    "The selected kerf-right shop packet supplies cut outlines only. Its angle-frame passes do not transfer. The official full-width alternative has no matched current wood-joint response/support mechanism in this assessment.",
    "No force/stiffness tuning, geometry/hardware change, floor anchor, native/CAD execution, physical inspection, criterion acceptance or release is established.",
]
FLAGS = {"proposal_adopted": False, "authority_changed": False, "geometry_or_hardware_changed": False,
         "loads_or_stiffness_changed": False, "historical_acceptance_transferred": False,
         "native_or_CAD_or_frame_execution": False, "tests_or_review_run": False,
         "N14_resistance_rebuilt": False, "complete_load_path_resistance": False,
         "formal_criterion_acceptance": False, "physical_release": False, "fabrication_release": False,
         "complete_joint_acceptance": False}


def require(condition, message):
    if not condition:
        raise ValueError("STOP: " + message)


def sha(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def read(path):
    return json.loads(Path(path).read_text())


def write(path, value):
    Path(path).write_text(json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n")


def bind(pins, path, digest):
    path = Path(path).resolve()
    require(path not in pins or pins[path] == digest, "conflicting source: " + str(path))
    pins[path] = digest


def authenticate(pins):
    for path, digest in pins.items():
        require(sha(path) == digest, "changed frozen source: " + str(path))


def source_map(pins):
    return {p.relative_to(ROOT).as_posix() if p.is_relative_to(ROOT) else str(p): h for p, h in sorted(pins.items())}


def sources():
    """Stdlib identities and saved-result joins only; no geometry calculation."""
    pins = dict(PINS)
    bind(pins, Path(__file__), sha(__file__))
    authenticate(pins)
    documents = {p: read(p) for p in (ASSESSMENT, COMPARISON, MODEL, INPUTS, ROWS, GEOMETRY, FEATURES,
                 CARRIER, CONTACTS, CORRECTED, MOVED, SETUP, MEMBERS / "checks.json", PACKAGE / "manifest.json")}
    for document in documents.values():
        if isinstance(document, dict):
            for field in ("source_sha256", "classifier_source_sha256"):
                for name, digest in document.get(field, {}).items():
                    path = (ROOT / name).resolve()
                    if path in PINS:
                        bind(pins, path, digest)
    for directory in (MEMBERS, PACKAGE):
        receipt = read(directory / "receipt.json")
        for name, digest in receipt["source_sha256"].items():
            path = (ROOT / name).resolve()
            if path in PINS:
                bind(pins, path, digest)
        for name, digest in receipt["output_sha256"].items():
            path = (directory / name).resolve()
            require(path.is_relative_to(directory), "receipt output leaves packet")
            bind(pins, path, digest)
    assessment, comparison, model, inputs, rows = (documents[p] for p in (ASSESSMENT, COMPARISON, MODEL, INPUTS, ROWS))
    for name, digest in assessment["output_sha256"].items():
        bind(pins, GRAVITY / name, digest)
    require(assessment["operator_ready"] is True and tuple(assessment["case_ids"]) == CASES,
            "fresh six-case operators not ready")
    require(comparison["response_sha256"] == pins[RESPONSE]
            and comparison["frame_operator_directory"] == GRAVITY.relative_to(ROOT).as_posix(), "fresh response binding differs")
    for path in (ASSESSMENT, MODEL, ROWS, OPERATORS):
        require(comparison["source_sha256"][path.relative_to(ROOT).as_posix()] == pins[path], "different frame source")
    require(comparison["source_climber_weight_lb"] == 250 and comparison["climber_load_scale"] == 1
            and comparison["comparison_horizontal_force_n"] == 300 and comparison["horizontal_load_scale"] == 1,
            "live loads changed")
    require(comparison["dead_load_factor"] == assessment["dead_load_factor"] == model["dead_load_factor"]
            == 1.1110134616260479 and assessment["planning_accessory_mass_kg"] == 25,
            "fresh gravity/accessory scale differs")
    require(len(rows) == 1888 and [r["row"] for r in rows] == list(range(1888)), "raw-row census differs")
    member_results = documents[MEMBERS / "checks.json"]
    require(member_results["source_comparison_sha256"] == pins[COMPARISON]
            and member_results["source_response_sha256"] == pins[RESPONSE]
            and member_results["source_gravity_assessment_sha256"] == pins[ASSESSMENT], "member forces are stale")
    manifest = documents[PACKAGE / "manifest.json"]
    require(manifest["census"]["Hillman_screws"] == 66 and manifest["census"]["bolts"] == 108
            and manifest["proposal_adopted"] is False, "108 proposal census/authority differs")
    require(manifest["source_load_identity"] == {"source_climber_weight_lb": 250,
            "source_dynamic_factor": 2, "source_hold_lever_mm": 100,
            "source_horizontal_force_magnitude_n": 300}, "original load/lever identity differs")
    authority = read(ROOT / "wood-joints-candidate.json")
    require(authority["release"] is False and all(value is False for value in authority["release_flags"].values()),
            "wood-joint release authority differs")
    for override in manifest["geometry"]["STEP_overrides"]:
        for field in ("current_step", "proposal_step"):
            bind(pins, ROOT / override[field]["path"], override[field]["sha256"])
        reference = override["geometry_reference"]
        bind(pins, ROOT / reference["source"], reference["sha256"])
    screws = [c for c in inputs["connections"] if c.get("kind") == "panel_screw"]
    require(len(screws) == len({s["axis_id"] for s in screws}) == 66, "66 screw map differs")
    features = {a["axis_id"]: a for a in documents[FEATURES]["source_axis_groups"]["panel_kicker_screw_axes"]["axes"]}
    moves = {m["axis_id"]: m for m in model["owner_authorized_screw_movements"]}
    require(len(moves) == 4, "four later upper moves differ")
    matches, row_groups = [], {}
    for screw in screws:
        axis, record = screw["axis_id"], screw["source_record"]
        panel, receiver = record["panel_member"], record["receiver_member"]
        own = [r for r in rows if r["row_id"].split("/")[0] == axis and r["ownership"]["role"] in (AXIAL, LATERAL)]
        require(len(own) == 3 and Counter(r["ownership"]["role"] for r in own) == {AXIAL: 1, LATERAL: 2}
                and all({r["ownership"]["first_body"], r["ownership"]["second_body"]} == {panel, receiver} for r in own),
                "incomplete screw ownership: " + axis)
        row_groups[axis] = [r["row"] for r in own]
        if axis in moves:
            saved = next(r for r in documents[MOVED]["checks"] if r["axis_id"] == axis and r["scenario"] == "after")
            require(saved["receiver_member"] == receiver, "upper receiver differs")
            evidence = {"kind": "saved_exact_cylinder_intersection_after_move", "source": MOVED.relative_to(ROOT).as_posix(),
                        "saved_result": saved}
        else:
            entry = features[axis]
            station = entry["panel_axis_station_reconciliation"]
            require(station["current_axis_origin_global_xyz_mm"] == record["origin_global_xyz_mm"]
                    and station["current_receiver_member"] == receiver, "finished bore station differs: " + axis)
            host = next(m for m in entry["receiver_memberships"] if m["receiver_member_id"] == receiver)
            require(host["match_status"] == "matched_bore_patch", "missing exact modeled backing: " + axis)
            current = documents[GEOMETRY]["members"][receiver]
            original_hash = host["current_finished_step_binding"]["file_sha256"]
            retained = original_hash == current["original_finished_step_sha256"] and not set(
                host["matched_feature_ids"]).intersection(current["replaced_original_bore_features"])
            require(original_hash == current["current_finished_step_sha256"] or retained,
                    "receiver bore identity differs: " + axis)
            evidence = {"kind": "frozen_finite_bore_patch_match", "source": FEATURES.relative_to(ROOT).as_posix(),
                        "receiver_membership": host, "current_geometry_record": {
                            "source": GEOMETRY.relative_to(ROOT).as_posix(),
                            "current_finished_step": current["current_finished_step"],
                            "current_finished_step_sha256": current["current_finished_step_sha256"],
                            "original_finished_step_sha256": current["original_finished_step_sha256"],
                            "replaced_original_bore_features": current["replaced_original_bore_features"]},
                        "retained_original_feature_join": original_hash != current["current_finished_step_sha256"]}
        matches.append({"axis_id": axis, "panel": panel, "receiver": receiver, "raw_rows": row_groups[axis],
                        "source_record": record, "backing_evidence": evidence, "resistance_result": None})
    saved_screws = [json.loads(line) for line in (PACKAGE / "panel-actions.jsonl").read_text().splitlines()]
    require(len(saved_screws) == len({(r["case_id"], r["axis_id"]) for r in saved_screws}) == 396,
            "fresh screw/case census differs")
    # Immutable output leaves carry their own frozen provenance. Replaying
    # unrelated shop-document ancestry would confuse later prose edits with
    # changes to consumed forces/geometry. Bind every consumed finished solid.
    for record in documents[GEOMETRY]["members"].values():
        bind(pins, ROOT / record["current_finished_step"], record["current_finished_step_sha256"])
    for member in inputs["members"]:
        step = member["current_finished_step_binding"]
        if member["member_kind"] == "panel":
            bind(pins, ROOT / step["path"], step["file_sha256"])
    authenticate(pins)
    return pins, documents, matches, saved_screws


def pure_function(path, name, namespace):
    tree = ast.parse(path.read_text(), filename=str(path))
    nodes = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == name]
    require(len(nodes) == 1 and not nodes[0].decorator_list, "pure saved helper differs")
    exec(compile(ast.Module(body=nodes, type_ignores=[]), str(path), "exec"), namespace)  # noqa: S102
    return namespace[name]


def bearing_expression():
    tree = ast.parse(BEARING.read_text(), filename=str(BEARING))
    function = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "face_contact_check")
    expressions = [value for node in ast.walk(function) if isinstance(node, ast.Dict)
                   for key, value in zip(node.keys, node.values, strict=True)
                   if isinstance(key, ast.Constant) and key.value == "wood_bearing_ratio"]
    require(len(expressions) == 1, "saved perpendicular bearing expression differs")
    return compile(ast.Expression(body=expressions[0]), str(BEARING), "eval")


def polygon_recipe(np, patch):
    """Finite straight outer loop plus full circular holes; no convex hull/AABB."""
    lines = [e for e in patch["boundary_edges"] if e["curve_type"] == "LINE"]
    circles = [e for e in patch["boundary_edges"] if e["curve_type"] == "CIRCLE"]
    if len(lines) < 3 or len(lines) + len(circles) != len(patch["boundary_edges"]):
        return None
    if any(abs(e["circle"]["last_parameter_rad"] - e["circle"]["first_parameter_rad"] - 2 * math.pi) > 1e-7 for e in circles):
        return None
    segments = [(np.array(e["start_xyz_mm"]), np.array(e["end_xyz_mm"])) for e in lines]
    start, end = segments.pop(0)
    points = [start, end]
    while segments:
        candidates = [(i, b if np.linalg.norm(a - points[-1]) < 1e-6 else a)
                      for i, (a, b) in enumerate(segments)
                      if min(np.linalg.norm(a - points[-1]), np.linalg.norm(b - points[-1])) < 1e-6]
        if len(candidates) != 1:
            return None
        i, point = candidates[0]
        segments.pop(i)
        points.append(point)
    if np.linalg.norm(points[-1] - points[0]) > 1e-6:
        return None
    return points[:-1], [e["circle"] for e in circles]


def line_support(np, p0, p1, patch):
    """Clip an exact line against a planar outer polygon and subtract holes."""
    recipe = polygon_recipe(np, patch)
    if recipe is None:
        return None
    vertices, holes = recipe
    normal = np.array(patch["normal_on_first_xyz"])
    direction = p1 - p0
    length = float(np.linalg.norm(direction))
    unit = direction / length
    transverse = np.cross(normal, unit)
    if abs(normal @ (p0 - vertices[0])) > 1e-6 or abs(normal @ unit) > 1e-7:
        return []
    xy = [(float(unit @ (v - p0)), float(transverse @ (v - p0))) for v in vertices]
    stops = [0.0, length]
    for (x, y), (xx, yy) in zip(xy, xy[1:] + xy[:1], strict=True):
        if abs(y) < 1e-7:
            stops.append(x)
        if y * yy < 0:
            stops.append(x + (xx - x) * (-y) / (yy - y))
    hole_ranges = []
    for hole in holes:
        delta = np.array(hole["center_xyz_mm"]) - p0
        radius, perpendicular = hole["radius_mm"], float(transverse @ delta)
        if abs(perpendicular) < radius:
            center, half = float(unit @ delta), math.sqrt(radius**2 - perpendicular**2)
            hole_ranges.append((center - half, center + half))
            stops.extend((center - half, center + half))
    stops = sorted({max(0.0, min(length, x)) for x in stops})

    def inside(x):
        crossings = 0
        for (a, b), (c, d) in zip(xy, xy[1:] + xy[:1], strict=True):
            if abs(b) < 1e-7 and abs(d) < 1e-7 and min(a, c) - 1e-7 <= x <= max(a, c) + 1e-7:
                return True
            if (b > 0) != (d > 0) and x < a + (c - a) * (-b) / (d - b):
                crossings += 1
        return crossings % 2 == 1

    return [[a, b] for a, b in pairwise(stops) if b - a > 1e-7
            and inside((a + b) / 2) and not any(c < (a + b) / 2 < d for c, d in hole_ranges)]


def union_intervals(intervals, length):
    merged = []
    for a, b in sorted(intervals):
        if merged and a <= merged[-1][1] + 1e-6:
            merged[-1][1] = max(merged[-1][1], b)
        else:
            merged.append([a, b])
    gaps, previous = [], 0.0
    for a, b in merged:
        if a > previous + 1e-6:
            gaps.append([previous, a])
        previous = b
    if previous < length - 1e-6:
        gaps.append([previous, length])
    return merged, gaps


def edge_geometry(np, documents):
    patches = documents[CONTACTS]["contact_patches"]
    model = documents[MODEL]
    outputs = []
    for panel in FOCUS:
        normal = np.array(model["material_binding"]["panel_axes"][panel]["panel_normal_global_xyz"])
        pair = ["kicker_left", "kicker_right"] if panel.startswith("kicker") else ["main_lower_left", "main_lower_right"]
        seam_index, seam = next((i, p) for i, p in enumerate(patches) if p["member_ids"] == pair)
        seam_lines = [(np.array(e["start_xyz_mm"]), np.array(e["end_xyz_mm"]))
                      for e in seam["boundary_edges"] if e["curve_type"] == "LINE" and e["length_mm"] > 200]
        a, b = min(seam_lines, key=lambda ab: float(normal @ ((ab[0] + ab[1]) / 2)))
        inward = np.array([-1.0, 0, 0]) if panel.endswith("left") else np.array([1.0, 0, 0])
        if panel.startswith("kicker"):
            p0, p1 = sorted((a, b), key=lambda p: p[2])
            label = "inner_kicker_backface_edge"
        else:
            tangent = -np.array(model["material_binding"]["panel_axes"][panel]["assumed_apa_direction_2_global_xyz"])
            p1 = min((a, b), key=lambda p: float(tangent @ p))
            side = "base_side_left" if panel.endswith("left") else "base_side_right"
            face = next(p for p in patches if set(p["member_ids"]) == {panel, side})
            corners = [e[key] for e in face["boundary_edges"] if e["curve_type"] == "LINE" for key in ("start_xyz_mm", "end_xyz_mm")]
            x = min(v[0] for v in corners) if panel.endswith("left") else max(v[0] for v in corners)
            p0 = np.array([x, *p1[1:]])
            inward = tangent
            label = "lower_panel_bottom_backface_edge"
        length = float(np.linalg.norm(p1 - p0))
        probes = []
        for strip_offset in (0.0, 19.05):
            q0, q1 = p0 + strip_offset * inward, p1 + strip_offset * inward
            contacts, unsupported = [], []
            for i, patch in enumerate(patches):
                if panel not in patch["member_ids"]:
                    continue
                other = next(body for body in patch["member_ids"] if body != panel)
                if other not in documents[GEOMETRY]["members"]:
                    continue
                intervals = line_support(np, q0, q1, patch)
                if intervals is None:
                    unsupported.append(i)
                elif intervals:
                    contacts.append({"receiver": other, "patch_index": i, "intervals_mm": intervals,
                                     "area_mm2": patch["area_mm2"], "source_face_indices": patch["source_face_indices"]})
            merged, gaps = union_intervals([x for c in contacts for x in c["intervals_mm"]], length)
            probes.append({"inward_offset_mm": strip_offset, "start_xyz_mm": q0.tolist(), "end_xyz_mm": q1.tolist(),
                           "receiver_intervals": contacts, "covered_intervals_mm": merged, "gaps_mm": gaps,
                           "unsupported_recipe_patch_indices": unsupported, "complete_support_result": None})
        cantilever = None
        if panel.startswith("kicker"):
            receiver = "base_post_center_left" if panel.endswith("left") else "base_post_center_right"
            patch = next(p for p in patches if set(p["member_ids"]) == {panel, receiver})
            vertices = [e[key] for e in patch["boundary_edges"] if e["curve_type"] == "LINE"
                        for key in ("start_xyz_mm", "end_xyz_mm")]
            inner_x = max(v[0] for v in vertices) if panel.endswith("left") else min(v[0] for v in vertices)
            cantilever = {"receiver": receiver, "exact_face_boundary_inner_x_mm": inner_x,
                          "seam_x_mm": float(p0[0]), "seam_to_post_inner_boundary_mm": abs(float(p0[0]) - inner_x),
                          "face_vertical_interval_mm": [min(v[2] for v in vertices), max(v[2] for v in vertices)],
                          "support_mechanism": "Panel transfer across this finite gap remains N14; the seam is not directly post-backed."}
        outputs.append({"panel": panel, "edge": label, "edge_length_mm": length,
                        "source_seam_patch_index": seam_index, "plane_recipe_source": CONTACTS.relative_to(ROOT).as_posix(),
                        "boundary_probes": probes, "inner_post_gap": cantilever,
                        "panel_bending_or_seam_resistance": None})
    return outputs


def assess(output, documents, matches, saved_screws):
    import numpy as np  # Parent-only numerical dependency.

    wrench = pure_function(WRENCH, "wrench", {"np": np})
    expression = bearing_expression()
    model, rows = documents[MODEL], documents[ROWS]
    bodies = model["body_names"]
    centers = {body: np.mean([model["physical_node_coordinates_mm"][str(n)]
                             for n in sorted(set(model["body_nodes"][body]))], axis=0) for body in bodies}
    require(len(bodies) == 50 and set(bodies) - set(documents[GEOMETRY]["members"]) == set(PANELS), "50-body partition differs")
    timber_refs = {m["member"]: m for m in documents[MEMBERS / "checks.json"]["members"]}
    focus_receivers = {m["receiver"] for m in matches if m["panel"] in FOCUS}
    # Export existing paths to the frame/floor without truncating a cleat route
    # at an adjacent body. All views refer to the one canonical raw-row leaf.
    path_bodies = set(documents[GEOMETRY]["members"])
    old_cells = {c["name"]: c for c in documents[CARRIER]["contact_cell_ownership"]}
    cells = dict(old_cells)
    for cleat in documents[CORRECTED]["cleats"]:
        for i, c in enumerate(cleat["rows"]):
            if c["kind"] == "contact":
                cells[f"{cleat['block']}/contact-cell-{i}"] = {"area_mm2": c["area_mm2"], "point_xyz_mm": c["point_mm"]}
    saved = {(s["case_id"], s["axis_id"]): s for s in saved_screws}
    group_states, screw_states, receiver_states, bearing_states, balances = [], [], [], [], []
    with np.load(OPERATORS, allow_pickle=False) as operators, np.load(RESPONSE, allow_pickle=False) as response, \
            (output / "signed-rows.jsonl").open("w") as stream:
        D, W = operators["D"], operators["W"]
        require(D.shape == (1888, 300) and W.shape == (300, 12), "saved operator shape differs")
        for case_index, case in enumerate(CASES):
            raw = response[case + "_gap_raw_force_n"]
            require(raw.shape == (1888,) and np.isfinite(raw).all(), "fresh nominal force vector differs")
            actions = {body: [] for body in bodies}
            for row in rows:
                i, own = row["row"], row["ownership"]
                sides = {}
                for body in bodies:
                    k = bodies.index(body)
                    value = -D[i, 6 * k:6 * k + 6] * raw[i] * [1, 1, 1, 1000, 1000, 1000]
                    if body not in (own["first_body"], own["second_body"]):
                        require(np.max(abs(D[i, 6 * k:6 * k + 6])) < 1e-12, "hidden connector ownership")
                        continue
                    force, moment = value[:3], value[3:]
                    point = np.array(own["point_mm"])
                    free = moment - np.cross(point - centers[body], force)
                    action = {"row": i, "source_id": row["row_id"], "role": own["role"],
                              "other_body": own["second_body"] if body == own["first_body"] else own["first_body"],
                              "point_mm": point.tolist(), "force_n": force.tolist(), "free_moment_nmm": free.tolist()}
                    actions[body].append(action)
                    sides[body] = wrench([action], np.zeros(3)).tolist()
                if len(sides) == 2:
                    require(np.max(abs(np.sum(list(sides.values()), axis=0))) < 1e-5, "signed row is not reciprocal")
                stream.write(json.dumps({"case_id": case, "row": i, "row_id": row["row_id"], "role": own["role"],
                             "point_xyz_mm": own["point_mm"], "scalar_n": float(raw[i]),
                             "signed_wrenches_about_global_origin_n_nmm": sides}, allow_nan=False) + "\n")
            for k, body in enumerate(bodies):
                external = (model["dead_load_factor"] * W[6*k:6*k+6, 2*case_index] + W[6*k:6*k+6, 2*case_index+1])
                external = external * [1, 1, 1, 1000, 1000, 1000]
                balance = wrench(actions[body], centers[body]) + external
                require(np.max(abs(balance[:3])) <= .1 and np.max(abs(balance[3:])) <= 2, "saved body does not balance: " + body)
                if body in path_bodies or body in PANELS:
                    balances.append({"case_id": case, "body": body, "datum_xyz_mm": centers[body].tolist(),
                                     "external_n_nmm": external.tolist(), "residual_n_nmm": balance.tolist()})
            for match in matches:
                axis, panel, receiver = match["axis_id"], match["panel"], match["receiver"]
                own = [a for a in actions[panel] if a["row"] in match["raw_rows"]]
                axial = next(i for i in match["raw_rows"] if rows[i]["ownership"]["role"] == AXIAL)
                lateral = [i for i in match["raw_rows"] if rows[i]["ownership"]["role"] == LATERAL]
                prior = saved[(case, axis)]
                require(abs(float(raw[axial]) - prior["signed_axial_n"]) < 1e-7
                        and abs(float(np.linalg.norm(raw[lateral])) - prior["peak_interface_lateral_n"]) < 1e-7,
                        "fresh saved screw state differs: " + axis)
                screw_states.append({"case_id": case, "axis_id": axis, "panel": panel, "receiver": receiver,
                     "raw_rows": match["raw_rows"], "signed_axial_n": float(raw[axial]),
                     "simultaneous_lateral_n": float(np.linalg.norm(raw[lateral])),
                     "panel_wrench_about_global_origin_n_nmm": wrench(own, np.zeros(3)).tolist(),
                     "receiver_wrench_about_global_origin_n_nmm": wrench([a for a in actions[receiver] if a["row"] in match["raw_rows"]], np.zeros(3)).tolist(),
                     "per_screw_resistance_result": None})
            for panel in PANELS:
                by_receiver = defaultdict(list)
                for action in actions[panel]:
                    if action["role"] in (AXIAL, LATERAL, CONTACT):
                        by_receiver[action["other_body"]].append(action)
                for receiver, all_own in sorted(by_receiver.items()):
                    own = [a for a in all_own if a["role"] in (AXIAL, LATERAL)]
                    contact = [a for a in all_own if a["role"] == CONTACT]
                    group_states.append({"case_id": case, "panel": panel, "receiver": receiver,
                        "receiver_kind": "timber" if receiver in documents[GEOMETRY]["members"] else "panel",
                        "screw_raw_rows": [a["row"] for a in own], "contact_raw_rows": [a["row"] for a in contact],
                        "screw_wrench_about_global_origin_n_nmm": wrench(own, np.zeros(3)).tolist(),
                        "contact_wrench_about_global_origin_n_nmm": wrench(contact, np.zeros(3)).tolist(),
                        "combined_wrench_about_global_origin_n_nmm": wrench(own + contact, np.zeros(3)).tolist()})
            for body in sorted(path_bodies):
                by_pair = defaultdict(list)
                for action in actions[body]:
                    by_pair[(action["other_body"], action["role"])].append(action)
                receiver_states.append({"case_id": case, "receiver": body, "datum_xyz_mm": centers[body].tolist(),
                    "direct_lower_panel_or_kicker_screw_receiver": body in focus_receivers,
                    "connection_groups": [{"other_body": other, "role": role, "raw_rows": [a["row"] for a in own],
                        "signed_wrench_at_receiver_datum_n_nmm": wrench(own, centers[body]).tolist(),
                        "signed_wrench_about_global_origin_n_nmm": wrench(own, np.zeros(3)).tolist(),
                        "complete_connection_resistance": None} for (other, role), own in sorted(by_pair.items())],
                    "saved_member_reference": timber_refs.get(body),
                    "modified_spine_member_reference_missing_here": body not in timber_refs})
                contact_groups = defaultdict(list)
                for a in actions[body]:
                    if a["role"] == CONTACT:
                        cell = cells[a["source_id"]]
                        identity = cell.get("source_patch_index", a["source_id"].rsplit("/contact-cell-", 1)[0])
                        contact_groups[(a["other_body"], str(identity))].append(a)
                for (other, identity), own in sorted(contact_groups.items()):
                    active = [a for a in own if raw[a["row"]] > 0]
                    require(all(raw[a["row"]] >= -1e-7 for a in own), "negative unilateral contact")
                    area = sum(cells[a["source_id"]]["area_mm2"] for a in active)
                    compression = sum(float(raw[a["row"]]) for a in active)
                    grain = np.array(documents[GEOMETRY]["members"][body]["geometry"]["axis"])
                    normal = np.array(rows[own[0]["row"]]["ownership"]["direction_global_xyz"])
                    perpendicular = abs(float(grain @ normal)) < 1e-7
                    ratio = float(eval(expression, {"__builtins__": {"max": max}},
                                       {"compression": compression, "area": area})) if perpendicular and area > 0 else None
                    bearing_states.append({"case_id": case, "receiver": body, "other_body": other,
                        "face_identity": identity, "raw_rows": [a["row"] for a in own],
                        "active_area_mm2": area, "compression_n": compression, "normal_grain_dot_abs": abs(float(grain @ normal)),
                        "timber_perpendicular_mean_ratio": ratio, "ratio_exceeds_one": None if ratio is None else ratio > 1,
                        "method_applicability": "CONDITIONAL_PERPENDICULAR_MEAN" if perpendicular and area > 0
                        else "NO_ACTIVE_AREA" if area == 0 else "PARALLEL_OR_OBLIQUE_METHOD_NOT_SUPPLIED",
                        "plywood_or_complete_connection_resistance": None})
    for name, values in (("screw-wrenches.json", screw_states), ("panel-receiver-groups.json", group_states),
                         ("receiver-connections.json", receiver_states), ("contact-bearing.json", bearing_states),
                         ("body-balances.json", balances), ("edge-support.json", edge_geometry(np, documents))):
        write(output / name, values)
    require(len(screw_states) == 396, "complete simultaneous screw extraction differs")
    return {"status": "COMPLETE_SAVED_PATH_ASSESSMENT_WITH_EXPLICIT_RESISTANCE_LIMITS",
            "numerical_arithmetic_run": True, "counts": {"screw_case_wrenches": len(screw_states),
                "panel_receiver_group_states": len(group_states), "path_timber_bodies": len(path_bodies),
                "path_receiver_case_states": len(receiver_states), "bearing_states": len(bearing_states),
                "body_balances": len(balances), "exact_edge_recipes": 4},
            "runtime": {"python": sys.version.split()[0], "numpy": np.__version__}}


def execute(output, numerical):
    output = Path(output).resolve()
    require(output.parent == RAW.resolve() and not output.exists(), "use a fresh immediate owned RAW child")
    pins, documents, matches, saved_screws = sources()
    bearing_expression()  # Authenticate the existing expression; do not evaluate it in prepare.
    output.mkdir(parents=True)
    report = {"schema": "kicker-path-completion/v1", "mode": "build" if numerical else "prepare",
              "status": "PREPARED_NOT_NUMERICALLY_RUN", "case_ids": list(CASES), "gap_scale": 1,
              "numerical_arithmetic_run": False, "source_sha256": source_map(pins), "producer_sha256": sha(__file__),
              "API": {"prepare": "prepare(output): stdlib frozen identity and saved-result joins only",
                      "build": "build(output): parent-only saved NumPy wrench/plane arithmetic; no solve",
                      "output": "fresh immediate child of rawlocal/kicker-path-completion"},
              "force_scope": "250 lb x2 downward, signed 300 N, original 100 mm lever, fresh gravity plus proportional 25 kg",
              "reviewed_authority_axes": 104, "unadopted_proposal_axes": 108, "current_screw_axes": 66,
              "backing_match_count": len(matches), "fresh_saved_screw_state_count": len(saved_screws),
              "backing_matches_are_resistance": False, "limits": LIMITS, **FLAGS}
    report["grouping_views_are_references_not_additional_loads"] = True
    report["upstream_ancestry_policy"] = "Frozen document source maps are preserved as lineage; only consumed leaves and saved-result outputs are authenticated. Unused historical shop prose is not replayed."
    write(output / "backing-identities.json", matches)
    write(output / "saved-screw-states.json", saved_screws)
    write(output / "saved-member-reference-join.json", documents[MEMBERS / "checks.json"])
    write(output / "cut-authority.json", {"selected_machine_authority": "current-candidate.json",
          "wood_joint_authority": "wood-joints-candidate.json", "current_reviewed_revision": "led-clearance-2x6-runner-seated-blocks-v1",
          "selected_kerf_shop_packet": str(KERF.relative_to(ROOT)), "historical_angle_passes_transferred": False,
          "current_plane_recipe": CONTACTS.relative_to(ROOT).as_posix(),
          "separate_unadopted_spine_STEP_overrides": documents[PACKAGE / "manifest.json"]["geometry"]["STEP_overrides"],
          "kerf_right_cut_outlines": {p: read(KERF / "stock-profiles.json")[p] for p in FOCUS},
          "official_alternate_cut_outlines": {p: read(OFFICIAL / "stock-profiles.json")[p] for p in FOCUS},
          "alternate_cut_mechanism_result": None,
          "alternate_cut_missing_input": "Exact full-width current wood-joint receiver/support recipe and matching six-case simultaneous actions; selected angle-frame evidence is not applicable."})
    (output / "producer.py.snapshot").write_bytes(Path(__file__).read_bytes())
    try:
        if numerical:
            report.update(assess(output, documents, matches, saved_screws))
        authenticate(pins)
        report["sources_unchanged_before_and_after"] = True
        write(output / "report.json", report)
    except Exception as exc:
        report.update(status="STOP", terminal_exception=f"{type(exc).__name__}: {exc}")
        write(output / "report.json", report)
        write(output / "receipt.json", {"status": "STOP", "source_sha256": source_map(pins),
              "output_sha256": {p.name: sha(p) for p in output.iterdir() if p.is_file()}, **FLAGS})
        raise
    write(output / "receipt.json", {"status": report["status"], "producer_sha256": sha(__file__),
          "source_sha256": source_map(pins), "sources_unchanged_before_and_after": True,
          "numerical_arithmetic_run": numerical,
          "output_sha256": {p.name: sha(p) for p in sorted(output.iterdir()) if p.is_file()}, **FLAGS})
    return report


def prepare(output):
    return execute(output, numerical=False)


def build(output):
    return execute(output, numerical=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--prepare", action="store_true")
    args = parser.parse_args()
    result = prepare(args.output) if args.prepare else build(args.output)
    print(json.dumps({"status": result["status"], "producer_sha256": result["producer_sha256"], "output": str(args.output)}))
