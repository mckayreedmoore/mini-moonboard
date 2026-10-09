"""Inventory existing signed bearings and separate unadopted square-end markers.

No field, geometry or capacity is produced. The Z200 action inventory is never
applied to the Z180 proposal. Existing admitted reports remain the action source.
"""
from __future__ import annotations

import argparse
import ast
import copy
import hashlib
import json
import math
from pathlib import Path

OWN = Path(__file__).resolve()
ROOT = OWN.parents[7]
BASE = "fea/generated/thin-bolted-current-contact-v1/eoere-successor-v1/"
MECH = BASE + "adjusted-base-mechanics-v1/"
SUMMARY = MECH + "current-component-results-v1/summary-inputs.json"
INPUT = MECH + "current-inputs-v1/attempt01/inputs.json"
PLACEMENT = BASE + "cleat-remedy-v1/current-source-followup-v1/placement.json"
METHOD = "scripts/thin_bolted_timber_resistance.py"
NDS = ("docs/wood-joints-mvp/hypotheses/hardware-material-specification-2026-09-30/"
       "materials-source/AWC_NDS2024_withCommentary_20250328_WebsiteChapter-12-Dowel-type-fasteners.pdf")
PINS = {
    SUMMARY: "ce2ebabc3d3311d77ae8aa00bc063fd7d6e380467fd5d85c7af9b898f636d9fb",
    INPUT: "f0c55ac1d67650eec2de0cedfe4ec383d5b2a04253fbf10c9db9df9251711baa",
    PLACEMENT: "5e131e9f58014b4a9426aa6a976338b930f471221e19b8e0e122ceff105f9b39",
    METHOD: "74d992cfbe4947587a8c6f0e65f7a8b47e0cd1c79f07721620c7137208919c2d",
    NDS: "5fc837523ff10acc097a162718700a9b4ba64e627d2b0023439146d42fe4ee2a",
    MECH + "current-component-results-v1/independent-review-v1/receipt-rich-six-cases.json":
        "71097dfa7d76449e5e46fc0307b53392c6fbd04645898b778fe104d1b20b832e",
}
CASES = ("a12-forward", "a12-rear", "a12-left", "k12-right", "k12-rear", "a1-rear")
IDS = {f"cleat_post_bolt_{side}_{i}" for side in ("left", "right") for i in (1, 2)}
LOADED_SHA = hashlib.sha256(OWN.read_bytes()).hexdigest()


def require(ok, message):
    if not ok:
        raise ValueError(message)


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def checked(relative, expected, pins):
    require(not Path(relative).is_absolute() and ".." not in Path(relative).parts,
            "repository-relative source required")
    require(relative not in pins or pins[relative] == expected, "conflicting direct pin")
    raw = (ROOT / relative).read_bytes()
    require(digest(raw) == expected, "source changed: " + relative)
    pins[relative] = expected
    return raw


def methods(pins):
    tree = ast.parse(checked(METHOD, PINS[METHOD], pins), filename=METHOD)
    wanted = {"vector", "unit", "dot", "cross", "resolved_action", "end_geometry_factor"}
    nodes = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name in wanted]
    require({n.name for n in nodes} == wanted, "exact frozen pure helper census")
    scope = {"math": math, "require": require}
    exec(compile(ast.Module(body=nodes, type_ignores=[]), METHOD, "exec"), scope)  # noqa: S102
    return scope["resolved_action"], scope["end_geometry_factor"]


def markers(member, axis, end):
    raw = member["raw_profile_source"]
    require(raw["basis_grain_u_v_xyz"] == [[0., 0., 1.], [1., 0., 0.], [0., 1., 0.]],
            "this bounded inventory requires the recorded vertical-grain profile")
    vertices = raw["raw_profile_vertices_luv_mm"]
    origin = raw["datum_xyz_mm"]
    lower = origin[2] + min(v[0] for v in vertices)
    upper = origin[2] + max(v[0] for v in vertices)
    ylo = origin[1] + min(v[2] for v in vertices)
    yhi = origin[1] + max(v[2] for v in vertices)
    y, z = axis["point_xyz_mm"][1:]
    is_cleat = member["name"].startswith("eoere_cleat_")
    if is_cleat:
        polygon = raw["finished_YZ_polygon_mm"]
        require(len(polygon) == 4 and polygon[:2] == [[ylo, lower], [yhi, lower]],
                "cleat bottom must be the recorded horizontal finished edge")
        # The sloping upper edge is not classified by this square-end helper.
        upper = None
    else:
        require(len(raw["end_cut_planes"]) == 2 and
                all(p["normal_to_nominal_grain_deg"] == 0 for p in raw["end_cut_planes"]),
                "post ends must be recorded square ends")
    distances = {"negative_square_end_mm": z - lower,
                 "positive_square_end_mm": None if upper is None else upper - z}
    require(all(v is None or v > 0 for v in distances.values()) and ylo < y < yhi,
            "proposal center outside the bounded source profile")
    return {"axis_id": axis["id"], "receiver": member["name"],
            "proposed_point_xyz_mm": axis["point_xyz_mm"], **distances,
            "square_end_markers": {key: {category: end(value, axis["diameter_mm"], category)
                for category in ("softwood_parallel_tension", "parallel_compression", "perpendicular")}
                for key, value in distances.items() if value is not None},
            "both_raw_crossgrain_edge_distances_mm": [y - ylo, yhi - y],
            "minimum_raw_edge_minus_perpendicular_loaded4D_mm": min(y-ylo, yhi-y) - 4*axis["diameter_mm"],
            "sloping_cleat_upper_end_classified": False if is_cleat else None,
            "force_assigned_to_proposal": False, "complete_Cdelta": None,
            "finished_net_section_or_fracture_qualified": False}


def build():
    pins = dict(PINS)
    pins[str(OWN.relative_to(ROOT))] = LOADED_SHA
    for p, sha in list(pins.items()):
        checked(p, sha, pins)
    summary = json.loads(checked(SUMMARY, PINS[SUMMARY], pins))
    source = json.loads(checked(INPUT, PINS[INPUT], pins))
    placement = json.loads(checked(PLACEMENT, PINS[PLACEMENT], pins))
    geometry_ref = summary["geometry"]["report"]
    geometry = json.loads(checked(geometry_ref["path"], geometry_ref["sha256"], pins))
    require(geometry_ref["sha256"] == "01ba30abe20c2efec136374b8d9a74a098a19929be3cc784b5ebcf7608e62a2d"
            and len(geometry["axes"]) == len(source["shafts"]) == 100
            and len(source["hillman_rows"]) == 66, "current geometry census/identity changed")
    shafts = {s["axis_id"]: s for s in source["shafts"]}
    members = {m["name"]: m for m in source["timber_rows"]}
    require(len(shafts) == 100 and len(members) == 22, "duplicate source owner")
    require(placement["geometry_adopted"] is False and placement["current_geometry_source"] == geometry_ref,
            "unadopted current-source proposal required")
    proposed = {a["id"]: a for a in placement["proposed_axes"]}
    require(set(proposed) == IDS, "exact four proposed axes required")
    resolved, end = methods(pins)
    known = [(33.3375, "softwood_parallel_tension", .5), (66.675, "softwood_parallel_tension", 1.),
             (33., "softwood_parallel_tension", None), (19.05, "perpendicular", .5),
             (38.1, "parallel_compression", 1.), (18., "parallel_compression", None)]
    for distance, category, expected in known:
        observed = end(distance, 9.525, category)["end_factor_only"]
        require(observed == expected, "frozen square-end known-answer failure")
    geometry_rows = []
    for aid in sorted(IDS):
        current = shafts[aid]["source_axis"]
        expected = copy.deepcopy(current)
        expected["point_xyz_mm"][2] = 180.
        require(current["point_xyz_mm"][2] == 200. and proposed[aid] == expected,
                "proposal differs beyond its declared Z change")
        for surface in shafts[aid]["surfaces"]:
            require(surface["kind"] == "wood", "dedicated two-wood stack required")
            geometry_rows.append(markers(members[surface["host"]], proposed[aid], end))
    require(tuple(c["case_id"] for c in summary["cases"]) == CASES, "exact six-case roster/order required")
    cases, all_angles = [], []
    for case in summary["cases"]:
        ref = case["rich"]["result"]
        report = json.loads(checked(ref["path"], ref["sha256"], pins))
        for ref2 in (case["field"], case["admission"]):
            checked(ref2["path"], ref2["sha256"], pins)
        require(report["case_id"] == case["case_id"] and report["current_geometry"] == geometry_ref
                and report["raw_field_sha256"] == case["field"]["sha256"]
                and report["field_admission_receipt_sha256"] == case["admission"]["sha256"]
                and report["complete_joint_resistance"] is None and not any(report["release"].values()),
                "existing own-case report identity/release changed")
        rows = [r for r in report["findings"]["timber"]["wood_surfaces"] if r["axis_id"] in IDS]
        require(len(rows) == len({(r["axis_id"], r["receiver"]) for r in rows}) == 8,
                "all eight distinct current wood surfaces required")
        selected = []
        for row in rows:
            shaft, member = shafts[row["axis_id"]], members[row["receiver"]]
            pts = [p for p in row["own_point_actions"] if p["kind"] == "common_shaft_bearing"]
            require(len(pts) == 2 and len({p["id"] for p in pts}) == 2, "two own bearing points required")
            actions = []
            for point in pts:
                signed = point["signed_components"]
                replay = resolved(signed["force_on_receiver_xyz_n"], member["axis"], shaft["basis"][0])
                require(replay == signed, "existing signed decomposition does not replay")
                theta = signed["load_to_grain_degrees"]
                if theta is not None:
                    all_angles.append(theta)
                actions.append({"id": point["id"], "point_xyz_mm": point["point_xyz_mm"],
                    "force_on_receiver_xyz_n": signed["force_on_receiver_xyz_n"],
                    "parallel_grain_signed_n": signed["parallel_grain_signed_n"],
                    "cross_grain_signed_n": signed["cross_grain_signed_n"],
                    "load_to_grain_degrees": theta, "oblique_lateral_action": signed["oblique_lateral_action"]})
            parallel = [a["parallel_grain_signed_n"] for a in actions]
            cross = [a["cross_grain_signed_n"] for a in actions]
            reversal = min(parallel) < 0 < max(parallel)
            cross_reversal = min(cross) < 0 < max(cross)
            require(reversal == row["bearing_parallel_sign_reversal"] and
                    cross_reversal == row["bearing_crossgrain_sign_reversal"] and
                    row["complete_Cdelta"] is None and row["complete_Cg"] is None,
                    "signed reversal or qualification marker differs")
            selected.append({"axis_id": row["axis_id"], "receiver": row["receiver"],
                "current_axis_Z_mm": shaft["point"][2], "own_bearings": actions,
                "bearing_parallel_sign_reversal": reversal, "bearing_crossgrain_sign_reversal": cross_reversal})
        cases.append({"case_id": case["case_id"], "state_id": report["state_id"], "report": ref,
                      "current_Z200_surfaces": selected})
    all_rows = [r for c in cases for r in c["current_Z200_surfaces"]]
    bearings = [p for r in all_rows for p in r["own_bearings"]]
    for p, sha in list(pins.items()):
        checked(p, sha, pins)
    return {"schema": "eoere_current_signed_end_inventory_and_separate_proposal_markers/v1",
        "question": "Can net one-way forces or full4D end markers close the four lower-joint holds?",
        "answer": "No. Current bearing signs reverse; proposal square-end markers are only geometry scenarios. Complete group/end/edge/fracture resistance remains unknown.",
        "source_sha256": pins, "direct_sources_unchanged_before_after": True,
        "inherited_source_closures_or_operator_arithmetic_reaudited": False,
        "execution": {"CAD_native_global_or_component_solve": False,
                      "current_Z200_actions_applied_to_Z180_proposal": False,
                      "square_end_helper_known_answer_fixtures": len(known)},
        "current_Z200_inventory": {"cases": cases, "case_count": len(cases), "wood_surface_count": len(all_rows),
            "bearing_point_count": len(bearings),
            "zero_lateral_bearing_points": sum(p["load_to_grain_degrees"] is None for p in bearings),
            "oblique_bearing_points": sum(p["oblique_lateral_action"] for p in bearings),
            "nonzero_bearing_angle_range_deg": [min(all_angles), max(all_angles)],
            "parallel_sign_reversal_surface_count": sum(r["bearing_parallel_sign_reversal"] for r in all_rows),
            "crossgrain_sign_reversal_surface_count": sum(r["bearing_crossgrain_sign_reversal"] for r in all_rows)},
        "separate_unadopted_Z180_square_end_markers": geometry_rows,
        "primary_source": {"path": NDS, "sha256": PINS[NDS], "edition": "NDS2024",
            "locators": "printed97–100 / PDF19–22:12.5.1.2a–c, Tables12.5.1A–D and12.6",
            "reading_command": "uv run --no-project --with 'pypdf[crypto]==6.1.0' python; PdfReader(path).pages[18:22]",
            "interpretation": "A classified square-end value may be reduced between stated minimum and full-value distances. The smallest applicable factor governs the entire group/shear planes. End markers do not qualify edges, local fracture or arbitrary oblique/finished group geometry.",
            "2024_commentary_text_in_this_46_page_chapter": False},
        "limits": ["Current six-case bearing actions are extracted from existing authenticated reports; no fresh admission is claimed.",
                   "The proposal has no assigned force or capacity. Raw side-edge benchmarks are not an oblique edge rule.",
                   "The square cleat bottom and square post ends are classified only as stated scenarios; the sloping cleat top and finished void ligaments are outside this helper.",
                   "Both short ends exceed3.5D and4D but do not both reach7D. This neither rejects the layout automatically nor establishes its complete Cdelta.",
                   "The separate bore/washer-seat study is required for proposed material geometry; actual parts/tools and tolerances remain unobserved."],
        "release": dict.fromkeys(("geometry_adopted", "complete_joint_resistance", "fabrication", "structural", "climbing"), False)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    require(not args.out.exists(), "preserve issued evidence")
    result = build()
    with args.out.open("x") as f:
        json.dump(result, f, sort_keys=True, indent=2, allow_nan=False)
        f.write("\n")
    print(json.dumps({"path": str(args.out), "sha256": digest(args.out.read_bytes()),
                      "direct_sources": len(result["source_sha256"]),
                      "inventory": {k: v for k, v in result["current_Z200_inventory"].items() if k != "cases"}}))


if __name__ == "__main__":
    main()
