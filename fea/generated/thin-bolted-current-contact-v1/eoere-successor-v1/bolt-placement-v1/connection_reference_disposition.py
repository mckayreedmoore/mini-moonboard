"""Reuse pinned NDS geometry rules; no actions, CAD or mechanics are evaluated."""
from __future__ import annotations

import argparse
import ast
import hashlib
import json
import math
import sys
from pathlib import Path

OWN = Path(__file__).resolve()
ROOT = OWN.parents[5]
LEAF = OWN.parent.parent
INPUT = LEAF / "mechanics-inputs-v1/inputs.json"
PLAN = LEAF / "cleat-corners-v1/plan.json"
LOWER = LEAF / "cleat-corners-v1/lower-bolt-z-v2.json"
METHOD = ROOT / "scripts/thin_bolted_timber_resistance.py"
NDS = ROOT / "docs/wood-joints-mvp/hypotheses/hardware-material-specification-2026-09-30/materials-source/AWC_NDS2024_withCommentary_20250328_WebsiteChapter-12-Dowel-type-fasteners.pdf"
PINS = {
    str(INPUT.relative_to(ROOT)): "7a003cb7fe6d14a8644a3030b45caf96a7a4b59618d8c1703c3e3626f267d4b4",
    str(PLAN.relative_to(ROOT)): "810f8cc24f477ff8c1ea8010cda96e5664113fadb50fd32d137b766964873f6c",
    str(LOWER.relative_to(ROOT)): "a615cb247cf48426f139cc3149ff658d38a96861c3166d0fa27e5912d650c04b",
    str(METHOD.relative_to(ROOT)): "74d992cfbe4947587a8c6f0e65f7a8b47e0cd1c79f07721620c7137208919c2d",
    str(NDS.relative_to(ROOT)): "5fc837523ff10acc097a162718700a9b4ba64e627d2b0023439146d42fe4ee2a",
    str(OWN.relative_to(ROOT)): hashlib.sha256(OWN.read_bytes()).hexdigest(),
}


def require(ok, message):
    if not ok:
        raise ValueError(message)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify(pins):
    for path, expected in pins.items():
        require(sha(ROOT / path) == expected, "Changed source: " + path)


def dot(a, b):
    return math.fsum(x * y for x, y in zip(a, b, strict=True))


def end_method():
    """Compile only the unchanged scalar method, without old candidate selectors."""
    tree = ast.parse(METHOD.read_text())
    nodes = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "end_geometry_factor"]
    require(len(nodes) == 1, "Pinned scalar end method missing")
    ns = {"math": math, "require": require}
    exec(compile(ast.fix_missing_locations(ast.Module(body=nodes, type_ignores=[])), str(METHOD), "exec"), ns)  # noqa: S102
    return ns["end_geometry_factor"]


def disposition():
    verify(PINS)
    raw = INPUT.read_bytes()
    require(hashlib.sha256(raw).hexdigest() == PINS[str(INPUT.relative_to(ROOT))], "Input changed during read")
    inp, plan, lower = json.loads(raw), json.loads(PLAN.read_bytes()), json.loads(LOWER.read_bytes())
    verify(inp["source_sha256"])
    require(inp["geometry"]["report"]["sha256"] == "05baab7ffdd329c3240a1770cf3539e321ab47d5cd2bc6354f8fceb6db8a0efd", "Not final successor geometry")
    require(lower["common_Z_mm"] == 200. and lower["conditional_end_reference"]["post_top_end_mm"] == 38.9, "Different cleat revision")
    rows = {r["name"]: r for r in inp["timber_rows"]}
    factor, diameter = end_method(), 9.525
    cleats = []
    for shaft in inp["shafts"]:
        a = shaft["source_axis"]
        if not a["id"].startswith("cleat_post_bolt_"):
            continue
        first, second = a["receivers"]
        require(first.startswith("eoere_cleat_") and second.startswith("base_post_outer_") and a["point_xyz_mm"][2] == 200., "Changed own cleat pair")
        members = []
        for name in (first, second):
            r = rows[name]
            require(r["axis"] == [0., 0., 1.] and abs(a["direction_xyz"][2]) < 1e-12, "Different grain/shaft pattern")
            z = a["point_xyz_mm"][2]
            ends = {"negative": z - r["start"][2], "positive": r["end"][2] - z}
            members.append({"member": name, "grain_axis_xyz": r["axis"], "square_raw_end_distances_mm": ends,
                            "toward_end_factors_only": {s: factor(d, diameter, "softwood_parallel_tension") for s, d in ends.items()},
                            "away_or_perpendicular_end_factors_only": {s: factor(d, diameter, "parallel_compression") for s, d in ends.items()}})
        toward = min(members[0]["toward_end_factors_only"]["negative"]["end_factor_only"],
                     members[1]["toward_end_factors_only"]["positive"]["end_factor_only"])
        reverse = min(members[0]["toward_end_factors_only"]["positive"]["end_factor_only"],
                      members[1]["toward_end_factors_only"]["negative"]["end_factor_only"])
        cleats.append({"axis_id": a["id"], "point_xyz_mm": a["point_xyz_mm"], "shaft_direction_xyz": a["direction_xyz"], "members": members,
                       "conditional_pure_parallel_pair_branches": {
                           "force_on_first_cleat_Fz_negative": {"first_loaded_end": "negative", "second_loaded_end": "positive", "minimum_end_factor_only": toward},
                           "force_on_first_cleat_Fz_positive": {"first_loaded_end": "positive", "second_loaded_end": "negative", "minimum_end_factor_only": reverse}},
                       "actual_signed_action": None, "complete_Cdelta": None, "complete_joint_resistance_n": None})
    require(len(cleats) == 4, "Four current cleat shafts required")
    rim = []
    for r in plan["raw_own_receiver_end_edge_screens"]:
        short = [e for e in r["edge_rays"] if abs(e["distance_mm"] - 29.108028271441356) < 1e-7]
        if not short:
            continue
        matches = [s["source_axis"] for s in inp["shafts"] if r["receiver"] in s["source_axis"]["receivers"]
                   and math.dist(r["wood_entry_xyz_mm"], s["source_axis"]["point_xyz_mm"]) < 1e-6]
        require(len(matches) == 1, "Raw rim diagnostic does not join a unique current physical shaft")
        a = matches[0]
        q, g = r["crossgrain_edge_direction_xyz"], r["nominal_grain_xyz"]
        require(abs(dot(q, g)) < 1e-8 and abs(dot(a["direction_xyz"], g)) < 1e-8, "Changed rim frame")
        sign, distance = short[0]["direction_sign"], short[0]["distance_mm"]
        rim.append({"axis_id": a["id"], "receiver": r["receiver"], "raw_source_screen_id": r["id"],
                    "grain_axis_xyz": g, "crossgrain_axis_xyz": q, "short_edge_direction_sign": sign,
                    "raw_short_edge_distance_mm": distance, "raw_short_edge_square_to_crossgrain_ray": short[0]["square_to_ray"],
                    "other_raw_edge_distance_mm": next(e["distance_mm"] for e in r["edge_rays"] if e["direction_sign"] != sign),
                    "perpendicular_load_toward_short_edge": {"force_selection": "sign(dot(own_lateral_force,q)) equals short_edge_direction_sign; pure perpendicular-to-grain applicability required",
                        "minimum_mm": 4 * diameter, "raw_margin_mm": distance - 4 * diameter, "edge_geometry_factor": None,
                        "disposition": "Below Table12.5.1C loaded-edge minimum if this branch is applicable; no interpolated Cdelta remedies an edge shortfall."},
                    "perpendicular_load_away_from_short_edge": {"short_edge_is_unloaded_minimum_mm": 1.5 * diameter,
                        "raw_margin_mm": distance - 1.5 * diameter},
                    "parallel_load": {"base_minimum_edge_mm": 1.5 * diameter,
                        "ell_over_D_and_full_row_inventory": None, "conditional_ell_gt6_rule": "max(1.5D,half spacing between actual rows)", "formal_acceptance": False},
                    "raw_end_ray_notes": [{"direction_sign": e["direction_sign"], "distance_mm": e["distance_mm"], "square_to_ray": e["square_to_ray"]} for e in r["end_rays"]],
                    "finished_boundary_distance_or_oblique_shear_area": None, "actual_signed_action": None, "complete_Cdelta": None})
    require(len(rim) == 2 and {r["axis_id"] for r in rim} == {"eoere_bolt_067", "eoere_bolt_070"}, "Two current short rim-edge witnesses required")
    bore = {"nominal_bolt_D_mm": diameter, "NDS12p1p3p2_minimum_hole_mm": diameter + 25.4 / 32,
            "NDS12p1p3p2_maximum_hole_mm": diameter + 25.4 / 16,
            "wood_hole_mm": 10.31875, "wood_diametral_oversize_mm": 10.31875 - diameter,
            "wood_nominal_installation_range_only": True, "steel_hole_mm": 10., "steel_diametral_oversize_mm": 10. - diameter,
            "steel_shortfall_from_stated_minimum_mm": diameter + 25.4 / 32 - 10.,
            "steel_nominal_installation_range_only": False, "authenticated_smaller_steel_hole_exception": None,
            "action": "Verify the delivered factory bore and applicable installation basis; report any required change before reaming or substituting hardware. A Cdelta reduction does not waive installation provisions."}
    verify(PINS)
    verify(inp["source_sha256"])
    require(INPUT.read_bytes() == raw, "Input bytes changed")
    return {"schema": "eoere_conditional_connection_geometry_reference/v1", "source_sha256": PINS,
            "authenticated_input_source_count": len(inp["source_sha256"]), "source_bytes_unchanged_before_after": True,
            "scope": "Final05ba successor geometry and saved nominal raw datums only. No accepted successor actions exist in this calculation.",
            "material": "Declared DF-L No.2 softwood, not inspected stock.",
            "primary_source": {"url": "https://awc.org/resources/2024-nds/", "path": str(NDS.relative_to(ROOT)), "sha256": PINS[str(NDS.relative_to(ROOT))],
                "locators": ["12.1.2.1-.5 /12.1.3.1-.4: printed81, PDF3", "12.3.4-.7: printed95, PDF17", "12.3.9: printed96, PDF18", "12.5.1.2/Table12.5.1A-B: printed97-98, PDF19-20", "12.5.1.3/Table12.5.1C-D: printed98-99, PDF20-21", "12.6: printed100, PDF22"]},
            "square_end_reference_summary": {"D_mm": diameter, "softwood_toward_end_minimum_3p5D_mm": 3.5 * diameter, "softwood_full_7D_mm": 7 * diameter,
                "away_or_perpendicular_minimum_2D_mm": 2 * diameter, "away_or_perpendicular_full_4D_mm": 4 * diameter,
                "post38p9_toward_end_factor_only": factor(38.9, diameter, "softwood_parallel_tension"),
                "cleat60p3_toward_end_factor_only": factor(60.3, diameter, "softwood_parallel_tension"),
                "main65p0875_toward_square_end_factor_only": factor(65.0875, diameter, "softwood_parallel_tension"),
                "away_or_perpendicular_all_three_end_factors_only": [factor(d, diameter, "parallel_compression") for d in (38.9, 60.3, 65.0875)]},
            "cleat_pair_branches": cleats, "rim_short_edge_branches": rim, "hole_installation_scope": bore,
            "required_next_inputs": ["Admitted same-state own receiver forces and couples, with axial and lateral components separated and each member's grain/sign retained.",
                "Classified square/oblique finished end and edge faces, service cuts/neighbor holes, applicable equivalent shear area and actual group/row inventory.",
                "Minimum applicable Cdelta across the complete connection/group and shear planes; separate group action, net-section, tearout and splitting checks.",
                "Delivered shank/root/thread window and bolt Fyb, exact metal applicability/materials, own washer/seat pressure and installation conformity."],
            "limits": ["Table12.5.1A permits end-factor reduction between the stated minimum and full end distances; 7D shortfall alone is not rejection.",
                "12.5.1.2 requires the smallest applicable factor for all fasteners in a group and all relevant shear planes of multiple-shear/asymmetric three-member connections. End-only numbers are not completeCdelta or capacity.",
                "Table12.5.1C edge minima are mandatory placement conditions; no edge-distance interpolation is supplied by12.5.1.2.",
                "Pure parallel/perpendicular branch conditions are not assigned to arbitrary oblique loading. Oblique grain Fe uses12.3.4; inclined load/fastener shear area and axial bearing use12.3.9/12.5.1.2b separately.",
                "An end distance is defined from a square-cut member end. The rim negative end is oblique; its grain ray cannot be relabeled a formal square-end Cdelta.",
                "Rows follow the actual load direction. Do not automatically treat the rim factory pair as a grain/cross-grain row; its pair direction is oblique to rim grain.",
                "Geometry distances are nominal/raw source diagnostics and do not certify continuous finished boundaries, local fracture, support pressure or complete resistance.",
                "Placement and hole dimensions use nominal boltD; do not reduce placementD by using the thread-root sensitivity diameter.",
                "No q, actions, preceding candidate demands, CAD imports/queries, assembly, K, native solve or source edits were used."],
            "execution": {"actual_orig_argv": sys.orig_argv},
            "release": dict.fromkeys(("candidate_admitted", "joint_resistance", "fabrication", "structural", "climbing"), False)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    require(not args.out.exists(), "Preserve existing evidence")
    result = disposition()
    with args.out.open("x") as stream:
        json.dump(result, stream, sort_keys=True, indent=2, allow_nan=False)
        stream.write("\n")
    print(json.dumps({"path": str(args.out), "sha256": sha(args.out), "bytes": args.out.stat().st_size,
                      "post_end_factor": result["square_end_reference_summary"]["post38p9_toward_end_factor_only"]["end_factor_only"]}))


if __name__ == "__main__":
    main()
