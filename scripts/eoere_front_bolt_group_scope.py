"""Audit the unresolved row/group scope of the current front bolt pairs.

Reuse the admitted cases, finished end/edge evidence and an existing NDS
row-spacing helper. Cardinal-direction markers are component screens, not
adopted geometry factors or a complete oblique, eccentric joint resistance.
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

import numpy as np

from scripts import eoere_current_washer_lands as intake_source

current = intake_source.current
OWN = Path(__file__).resolve()
LOADED_SHA = current.sha(OWN)
PLACEMENT = {"path": "fea/generated/selected-hardware-followup-v1/engineering-closure-v1/current-front-bolt-placement-v1.json",
             "sha256": "5f7c91e5f7640889719c6a95c952877e494046005072e0b8d1542daf0784da1e"}
SPACING = {"path": "fea/leg_bolt_pattern_search.py",
           "sha256": "a2acf8b0a02fc2a5d4d5768b94d214d693a4422c01e53c0bc4f27680b9cd3c7d"}
PRIMARY = [
    {"path": "docs/wood-joints-mvp/hypotheses/upper-block-strength-2026-10-01/source-cache/chapter11-2024-awc-20260911.pdf",
     "sha256": "45a3d78de1a4fba573589be0fc776e37bd581e4cedec24e38d63856161092d33"},
    {"path": "docs/wood-joints-mvp/hypotheses/upper-block-strength-2026-10-01/source-cache/chapter12-2024-awc-20260911.pdf",
     "sha256": "53f6ec05dfd1ceabeccd4d6e88c342111678d3da4631ee7b482b706f77c1780f"},
]
PAIRS = {side: [f"rail_front_bolt_{side}_{i}" for i in (1, 2)] for side in ("left", "right")}


def unit(value):
    a = np.asarray(value, dtype=float)
    current.require(a.shape == (3,) and np.isfinite(a).all() and abs(np.linalg.norm(a)-1.) < 1e-9,
                    "finite unit direction required")
    return a


def pattern(shafts, spacing):
    """Measure both members of one two-wood, transverse-axis physical pair."""
    require = current.require
    require(len(shafts) == 2 and len({s["axis_id"] for s in shafts}) == 2,
            "two distinct physical shafts required")
    direction = unit(shafts[0]["basis"][0])
    require(abs(abs(direction @ unit(shafts[1]["basis"][0]))-1.) < 1e-9,
            "parallel own shaft directions required")
    diameter = shafts[0]["diameter_mm"]
    require(math.isfinite(diameter) and diameter >= 6.35 and diameter == shafts[1]["diameter_mm"],
            "same nominal bolt diameter within NDS row-rule scope required")
    require(all(len(shaft["surfaces"]) == 2 for shaft in shafts), "exactly two own bearing surfaces required")
    surfaces = [{s["host"]: s for s in shaft["surfaces"]} for shaft in shafts]
    require(all(len(s) == 2 and all(v["kind"] == "wood" for v in s.values()) for s in surfaces)
            and surfaces[0].keys() == surfaces[1].keys(), "same two own wood receivers required")
    lengths = [v["interval_mm"][1]-v["interval_mm"][0] for s in surfaces for v in s.values()]
    require(all(math.isfinite(v) and abs(v-spacing.THICKNESS) < 1e-8 for v in lengths),
            "existing helper's 38.1-mm lesser bearing-length scope required")
    lesser_length = min(lengths)
    required_spacing = spacing.cross_row_minimum(diameter)
    rows = []
    for host in sorted(surfaces[0]):
        grain = unit(surfaces[0][host]["grain_axis_xyz"])
        require(np.linalg.norm(grain-unit(surfaces[1][host]["grain_axis_xyz"])) < 1e-9
                and abs(grain @ direction) < 1e-9, "same grain and perpendicular shaft required")
        cross = np.cross(grain, direction)
        points = [np.asarray(s["point"])+unit(s["basis"][0])*sum(v[host]["interval_mm"])/2.
                  for s, v in zip(shafts, surfaces, strict=True)]
        require(all(p.shape == (3,) and np.isfinite(p).all() for p in points), "finite own midpoints required")
        delta = points[1]-points[0]
        g, q = abs(float(delta @ grain)), abs(float(delta @ cross))
        require(math.hypot(g, q) > 1e-8, "coincident transverse pattern refused")
        rows.append({"member": host, "axis_ids": [s["axis_id"] for s in shafts],
                     "grain_axis_xyz": grain.tolist(), "cross_grain_axis_xyz": cross.tolist(),
                     "own_bearing_midpoints_xyz_mm": [p.tolist() for p in points],
                     "grain_separation_mm": g, "cross_grain_separation_mm": q,
                     "diagonal_in_wood_plane_mm": math.hypot(g, q),
                     "lesser_main_or_total_side_bearing_length_mm": lesser_length,
                     "nominal_diameter_mm": diameter, "ell_over_D": lesser_length/diameter,
                     "parallel_to_grain_between_rows_1p5D_marker_mm": 1.5*diameter,
                     "perpendicular_to_grain_between_rows_marker_mm": required_spacing,
                     "parallel_marker_cross_grain_margin_mm": q-1.5*diameter,
                     "perpendicular_marker_grain_margin_mm": g-required_spacing,
                     "perpendicular_marker_is_met": g >= required_spacing-1e-8,
                     "single_grain_aligned_row": q < 1e-8,
                     "single_cross_grain_aligned_row": g < 1e-8,
                     "complete_Cdelta": None, "complete_Cg": None})
    return rows


def action_scope(row, actions):
    """Retain each own signed force/couple and test the actual load alignment."""
    grain, cross = unit(row["grain_axis_xyz"]), unit(row["cross_grain_axis_xyz"])
    delta = np.subtract(*row["own_bearing_midpoints_xyz_mm"])
    row_direction = delta/np.linalg.norm(delta)
    result = []
    for action in actions:
        require = current.require
        require(action["receiver"] == row["member"] and action["axis_id"] in row["axis_ids"],
                "own member/axis action required")
        force = np.asarray(action["own_force_xyz_n"], dtype=float)
        couple = np.asarray(action["own_moment_at_aggregate_xyz_nmm"], dtype=float)
        require(force.shape == couple.shape == (3,) and np.isfinite(force).all() and np.isfinite(couple).all(),
                "finite own complete force and couple required")
        parallel, transverse = float(force @ grain), float(force @ cross)
        lateral = parallel*grain+transverse*cross
        magnitude = float(np.linalg.norm(lateral))
        require(magnitude > 1e-10, "nonzero current lateral direction required")
        sine = float(np.linalg.norm(np.cross(lateral/magnitude, row_direction)))
        result.append({"axis_id": action["axis_id"], "force_xyz_n": force.tolist(),
                       "free_couple_at_own_aggregate_xyz_nmm": couple.tolist(),
                       "parallel_grain_signed_n": parallel, "cross_grain_signed_n": transverse,
                       "lateral_direction_to_physical_pair_sine": sine,
                       "aligned_with_physical_pair": sine < 1e-8,
                       "oblique_to_grain": min(abs(parallel), abs(transverse)) > 1e-8})
    current.require(len(result) == 2 and {a["axis_id"] for a in result} == set(row["axis_ids"]),
                    "both own physical shaft actions required")
    return result


def group_wrench_scope(row, actions):
    """Original signed actions and free couples about the physical pair center."""
    action_scope(row, actions)
    origin = np.mean(row["own_bearing_midpoints_xyz_mm"], axis=0)
    force, moment = np.zeros(3), np.zeros(3)
    for action in actions:
        point = np.asarray(action["own_aggregate_point_xyz_mm"], dtype=float)
        current.require(point.shape == (3,) and np.isfinite(point).all(), "finite own aggregate point required")
        f = np.asarray(action["own_force_xyz_n"])
        force += f
        moment += np.cross(point-origin, f)+action["own_moment_at_aggregate_xyz_nmm"]
    grain, cross = unit(row["grain_axis_xyz"]), unit(row["cross_grain_axis_xyz"])
    lateral = (force @ grain)*grain+(force @ cross)*cross
    delta = np.subtract(*row["own_bearing_midpoints_xyz_mm"])
    magnitude = np.linalg.norm(lateral)
    sine = None if magnitude < 1e-10 else float(np.linalg.norm(np.cross(lateral/magnitude, delta/np.linalg.norm(delta))))
    return {"origin_xyz_mm": origin.tolist(), "force_xyz_n": force.tolist(), "moment_xyz_nmm": moment.tolist(),
            "lateral_resultant_to_physical_pair_sine": sine,
            "lateral_resultant_aligned_with_physical_pair": None if sine is None else sine < 1e-8,
            "complete_Cg": None}


def run():
    cases, pins = intake_source.intake()
    old = current.read(PLACEMENT)
    refs = [PLACEMENT, SPACING, *PRIMARY, current.ref(OWN),
            current.ref(current.ROOT/"tests/test_eoere_front_bolt_group_scope.py")]
    pins = current.join(pins, old["source_sha256"], {r["path"]: r["sha256"] for r in refs})
    current.verify(pins)
    require = current.require
    require(old["geometry_revision"] == "eoere-raised-kicker-screws-v1"
            and old["hardware_revision"] == "eoere-selected-purchase-hardware-v1"
            and old["extra_grid"] is False and old["all_full_value_end_and_outer_edge_screens_pass"] is True,
            "exact passing current end/outer-edge evidence required")
    spacing = intake_source.component.load(SPACING, "current_front_row_spacing")
    require(spacing.cross_row_minimum(6.35) == 31.75
            and spacing.cross_row_minimum(25.4) == 63.5
            and abs(spacing.cross_row_minimum(12.7)-39.6875) < 1e-10,
            "reused piecewise row-spacing known answers fail")
    first = cases[0][1]
    require(len(first["source_inputs"]["shafts"]) == 100, "retained 100-bolt design required")
    shaft_map = {s["axis_id"]: s for s in first["source_inputs"]["shafts"]}
    geometry = [r for ids in PAIRS.values() for r in pattern([shaft_map[i] for i in ids], spacing)]
    result = []
    for binding, field, data in cases:
        require(field["source_inputs"]["shafts"] == first["source_inputs"]["shafts"], "current shaft geometry changed")
        previous = next(c for c in old["cases"] if c["case_id"] == binding["case_id"])
        require(previous["state_id"] == binding["state_id"] and previous["field"] == binding["field"],
                "current end/edge case binding differs")
        rows = []
        for i, r in enumerate(geometry):
            actions = [a for a in data["findings"]["timber"]["wood_surfaces"]
                       if a["receiver"] == r["member"] and a["axis_id"] in r["axis_ids"]]
            rows.append({"geometry_index": i, "member": r["member"],
                         "own_signed_action_scope": action_scope(r, actions),
                         "complete_group_wrench_scope": group_wrench_scope(r, actions)})
        result.append({"case_id": binding["case_id"], "state_id": binding["state_id"],
                       "field": binding["field"], "member_pair_scope": rows})
    for module in tuple(sys.modules.values()):
        file = getattr(module, "__file__", None)
        if file and Path(file).suffix == ".py" and Path(file).resolve().is_relative_to(current.ROOT):
            ref = current.ref(Path(file).resolve())
            pins = current.join(pins, {ref["path"]: ref["sha256"]})
    current.verify(pins)
    require(current.sha(OWN) == LOADED_SHA, "loaded adapter changed")
    return {"schema": "eoere_front_bolt_group_scope/v1", "producer": current.ref(OWN),
            "source_sha256": pins, "all_sources_unchanged": True, "reused_placement": PLACEMENT,
            "spacing_helper": SPACING, "primary_sources": PRIMARY,
            "geometry_revision": old["geometry_revision"], "hardware_revision": old["hardware_revision"],
            "extra_grid": False, "current_bolt_count": 100, "geometry": geometry, "cases": result,
            "perpendicular_cardinal_marker_shortfalls": sum(not r["perpendicular_marker_is_met"] for r in geometry),
            "minimum_perpendicular_cardinal_margin_mm": min(r["perpendicular_marker_grain_margin_mm"] for r in geometry),
            "complete_Cdelta": None, "complete_Cg": None, "complete_joint_resistance": None,
            "structural_acceptance": False, "native_or_frame_solve_CAD_rebuild_geometry_change_or_actual_fit": False,
            "release": old["release"],
            "limits": ["NDS 2024 Table12.5.1D distinguishes row spacing parallel and perpendicular to grain. For the perpendicular branch, rows run with the load across grain and separation is measured along grain, as in Figure12G. The 38.1-mm lesser wood bearing length is used, not the combined 76.2-mm grip.",
                       "The current pair is staggered in both grain and cross-grain coordinates. Its diagonal distance is not a substitute for either projected row spacing.",
                       "The perpendicular cardinal marker shortfall is a recorded geometry-screen result. Current actions are oblique and eccentric; no complete Cdelta, Cg or physical failure is inferred from the marker.",
                       "NDS11.3.6.2 defines a group-action row relative to load direction. The complete signed current forces and free couples are retained; no scalar resultant, equal sharing, universal Cg=1, remedy or design revision is adopted."]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    with current.load("bridge").reserve(args.out) as output:
        output.write(run())
    print(json.dumps(current.ref(args.out)))


if __name__ == "__main__":
    main()
