"""Reuse the earlier cleat references with current signed actions and geometry.

NDS reduced-depth shear and the historical transverse-tension hypothesis are
separate references. Neither is silently promoted to complete cleat resistance.
No new bolt, geometry revision, frame solve or native fracture run is introduced.
"""
from __future__ import annotations

import argparse
import ast
import json
import math
from pathlib import Path

import numpy as np

from scripts import eoere_cleat_transverse_wrench as cleat
from scripts import eoere_current_washer_lands as intake_source

current = intake_source.current
OWN = Path(__file__).resolve()
LOADED_SHA = current.sha(OWN)
DEMAND = {"path": "fea/generated/selected-hardware-followup-v1/engineering-closure-v1/current-cleat-transverse-wrench-v1.json",
          "sha256": "7d6df246082753bf17ff1289ff7c0166f1c3e91236e9edfec07ad0180449fe8b"}
HYPOTHESIS_SOURCE = {"path": "docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/upper-corner-screw-layout/all-joint-splitting/splitting-capacity-completion.py",
                     "sha256": "c0a96a62bb9a8e4e949f8cc5aa7b8bc08e14329821845fe10f4703a20df8c028"}
PRIOR_RESULT = {"path": str((current.DOC/"bounded-strength-v1/resistance-followup-v1/result.json").relative_to(current.ROOT)),
                "sha256": "f6ae2d1bbf5528f0027c74bfd2de13fa444b8bc567afaa079d66a295ab04b36b"}


def rear_face(polygon, station):
    """Actual left silhouette of the frozen convex Y/Z extrusion."""
    require = current.require
    require(len(polygon) == 4 and all(len(p) == 2 and np.isfinite(p).all() for p in polygon)
            and math.isfinite(station), "finite quadrilateral and grain station required")
    turns = []
    for i in range(4):
        a, b, c = (np.asarray(polygon[j % 4]) for j in (i, i+1, i+2))
        u, v = b-a, c-b
        turns.append(u[0]*v[1]-u[1]*v[0])
    require(min(turns) > 0 or max(turns) < 0, "strictly convex quadrilateral required")
    intersections = []
    for (y0, z0), (y1, z1) in zip(polygon, [*polygon[1:], polygon[0]], strict=True):
        if min(z0, z1) <= station <= max(z0, z1):
            if z0 == z1:
                intersections.extend((y0, y1))
            else:
                intersections.append(y0+(y1-y0)*(station-z0)/(z1-z0))
    require(len(intersections) >= 2, "station outside own cleat profile")
    return min(intersections), max(intersections)


def group_geometry(profile, group, bore_radius, margin=1e-4):
    """Bind actual loaded edge, group centers and the full bore-support band."""
    require = current.require
    require(len(group) == 2 and len({a["point_xyz_mm"][2] for a in group}) == 1
            and math.isfinite(bore_radius) and bore_radius > 0 and margin > 0,
            "two own bores at one grain station and positive band required")
    polygon = profile["finished_YZ_polygon_mm"]
    require(profile["basis_grain_u_v_xyz"] == [[0., 0., 1.], [1., 0., 0.], [0., 1., 0.]],
            "this reference is for the existing Z-grain, X-thick cleat")
    ys = [a["point_xyz_mm"][1] for a in group]
    station = group[0]["point_xyz_mm"][2]
    forces = [a["force_xyz_n"][1] for a in group]
    require(all(math.isfinite(v) for v in (*ys, station, *forces)), "finite own group geometry and forces required")
    active = [v for v in forces if abs(v) > 1e-7]
    require(active and (min(active) > 0 or max(active) < 0),
            "opposing or negligible forces cannot select one loaded edge")
    sign = 1 if sum(forces) > 0 else -1
    stations = [station-bore_radius-margin, station, station+bore_radius+margin]
    sections = []
    stock_depth = profile["raw_stock_scenario_dimensions_mm"][1]
    for z in stations:
        rear, front = rear_face(polygon, z)
        require(rear < min(ys) <= max(ys) < front, "own fastener centers must stay inside the section")
        engaged = front-min(ys) if sign > 0 else max(ys)-rear
        sections.append({"station_mm": z, "rear_y_mm": rear, "front_y_mm": front,
                         "local_depth_mm": front-rear, "engaged_depth_mm": engaged})
    low = min(p[1] for p in polygon)
    # Actual grain-positive ends are evaluated at each own bolt Y, not at
    # the rectangular blank's taller corner or another receiver's end.
    end_distances = []
    for y in ys:
        tops = []
        for (y0, z0), (y1, z1) in zip(polygon, [*polygon[1:], polygon[0]], strict=True):
            if y0 != y1 and min(y0, y1) <= y <= max(y0, y1):
                tops.append(z0+(z1-z0)*(y-y0)/(y1-y0))
        require(tops and max(tops) > station > low, "own grain end must bound the bolt center")
        end_distances.extend((station-low, max(tops)-station))
    return {"station_mm": station, "loaded_Y_sign": sign, "group_y_forces_n": forces,
            "bore_radius_mm": bore_radius, "sections": sections,
            "stock_depth_mm": stock_depth, "minimum_engaged_depth_over_band_mm": min(s["engaged_depth_mm"] for s in sections),
            "nearest_actual_grain_end_mm": min(end_distances),
            "constant_full_stock_depth_over_band": all(abs(s["local_depth_mm"]-stock_depth) < 1e-7 for s in sections)}


def shear_at(actions, station):
    """Signed section Y shear from all own actions above a grain-normal cut.

    Current uniform self-weight acts only in Z and contributes zero Y shear.
    Source free couples remain separate simultaneous duties, not force terms.
    """
    selected = [a for a in actions if a["point_xyz_mm"][2] > station]
    return {"station_mm": station, "Y_shear_n": math.fsum(a["force_xyz_n"][1] for a in selected),
            "selected_action_ids": [a["id"] for a in selected]}


def historical_hypothesis(path):
    """Read the prior literal declaration without executing a fracture driver."""
    tree = ast.parse(path.read_text())
    assignments = [n for n in tree.body if isinstance(n, ast.Assign)
                   and any(isinstance(t, ast.Name) and t.id == "ASSUMPTIONS" for t in n.targets)]
    current.require(len(assignments) == 1, "one original fracture assumption declaration required")
    assumptions = ast.literal_eval(assignments[0].value)
    current.require(assumptions["Ft90_mpa"] == .5 and assumptions["Gc_all_modes_n_per_mm"] == .1,
                    "original material hypotheses changed")
    return {k: assumptions[k] for k in ("Ft90_mpa", "Gc_all_modes_n_per_mm", "property_status")}


def run():
    cases, pins = intake_source.intake()
    source = current.read(DEMAND)
    hypothesis_path = current.ROOT/HYPOTHESIS_SOURCE["path"]
    refs = [DEMAND, PRIOR_RESULT, intake_source.PROBE, current.ref(OWN), current.ref(Path(cleat.__file__)),
            HYPOTHESIS_SOURCE, current.ref(current.ROOT/"tests/test_eoere_cleat_reference_audit.py")]
    pins = current.join(pins, source["source_sha256"], {r["path"]: r["sha256"] for r in refs})
    current.verify(pins)
    current.read(PRIOR_RESULT)
    require = current.require
    require(source["geometry_revision"] == "eoere-raised-kicker-screws-v1"
            and source["hardware_revision"] == "eoere-selected-purchase-hardware-v1"
            and source["extra_grid"] is False and len(source["cases"]) == 12,
            "exact retained current cleat evidence required")
    previous = intake_source.component.load(intake_source.PROBE, "cleat_reduced_depth_reuse")
    # Reuse the old pure NDS equation. The published 5d fixture is checked
    # without running its unrelated CAD washer coupons or historical driver.
    require(previous.reduced_depth_shear(2., 3., 10., 5., 49.999)["reference_n"] == 5.
            and previous.reduced_depth_shear(2., 3., 10., 5., 50.)["reference_n"] == 20., "reused 5d known answer fails")
    hypothesis = historical_hypothesis(hypothesis_path)
    from fea.reinforced_timber_resistance import adjusted_reference

    fv = adjusted_reference(139.7)["Fv_mpa"]
    require(abs(fv-180.*.006894757293168361) < 1e-12, "existing CD1 DF-L No.2 shear basis differs")
    joins = {(c["case_id"], c["member"]): c for c in source["cases"]}
    require(len(joins) == 12, "unique current own member/case records required")
    rows, normal = [], []
    for binding, field, data in cases:
        shafts = {s["axis_id"]: s for s in field["source_inputs"]["shafts"]}
        for member in cleat.MEMBERS:
            saved = joins[(binding["case_id"], member)]
            require(saved["state_id"] == binding["state_id"] and saved["field"] == binding["field"], "own saved field join differs")
            geometry = source["geometry"][member]
            actions, gravity = cleat.member_actions(field, data, member, geometry)
            require(actions == saved["complete_saved_exterior_point_actions"] and gravity[1] == 0.,
                    "complete current own action or gravity join differs")
            profile = next(t["raw_profile_source"] for t in field["source_inputs"]["timber_rows"] if t["name"] == member)
            bores = [a for a in actions if a["id"].endswith("/complete-wood-wrench")]
            require(len(bores) == 4 and all(a["force_xyz_n"][1] == 0. for a in actions if a not in bores),
                    "current Y transfer includes an unaccounted non-bore action")
            require(abs(math.fsum(a["force_xyz_n"][1] for a in actions)) < 1e-5, "current complete Y force does not balance")
            for station in sorted({a["point_xyz_mm"][2] for a in bores}):
                group = [a for a in bores if a["point_xyz_mm"][2] == station]
                radius = max(shafts[a["id"].split("/")[0]]["bore_diameter_mm"] for a in group)/2.
                g = group_geometry(profile, group, radius)
                cuts = [shear_at(actions, g["sections"][i]["station_mm"]) for i in (0, 2)]
                demand = max(abs(c["Y_shear_n"]) for c in cuts)
                width, depth, _ = profile["raw_stock_scenario_dimensions_mm"]
                ref = previous.reduced_depth_shear(fv, width, depth, g["minimum_engaged_depth_over_band_mm"], g["nearest_actual_grain_end_mm"])
                rows.append({"case_id": binding["case_id"], "member": member, "geometry": g,
                             "adjacent_grain_normal_shear_cuts": cuts, "maximum_Y_shear_n": demand,
                             "retained_stock_depth_band_reference": ref,
                             "conditional_component_reference_index": demand/ref["reference_n"],
                             "reference_role": "rectangular bending-component reference" if g["constant_full_stock_depth_over_band"]
                             else "nonrectangular band parameter sensitivity; complete applicability unqualified",
                             "complete_cleat_resistance": None})
            for trace in saved["traces"]:
                field_ref = trace["affine_normal_equilibrium_field"]
                peak = field_ref["maximum_tension_mpa"]
                normal.append({"case_id": binding["case_id"], "member": member,
                               "include_boundary": trace["boundary_point_actions_in_high_trace"],
                               "full_source_wrench_n_nmm": trace["required_cut_on_low_portion_n_nmm"],
                               "nominal_affine_tension_mpa": peak, "historical_hypothesis_mpa": hypothesis["Ft90_mpa"],
                               "conditional_hypothesis_index": peak/hypothesis["Ft90_mpa"],
                               "grade_specific_allowable_or_fracture_resistance": None})
    current.verify(pins)
    require(current.sha(OWN) == LOADED_SHA and len(rows) == 24 and len(normal) == 24, "source drift or incomplete current scope")
    return {"schema": "eoere_retained_cleat_reference_audit/v1", "producer": current.ref(OWN),
            "current_cleat_demand": DEMAND, "source_sha256": pins, "all_sources_unchanged": True,
            "NDS_reduced_depth_method": intake_source.PROBE, "historical_material_hypotheses": hypothesis,
            "historical_hypothesis_source": HYPOTHESIS_SOURCE, "historical_component_result": PRIOR_RESULT,
            "material_Fv_CD1_mpa": fv, "current_shear_comparisons": rows, "current_normal_hypothesis_comparisons": normal,
            "maximum_conditional_shear_index": max(r["conditional_component_reference_index"] for r in rows),
            "maximum_conditional_normal_hypothesis_index": max(r["conditional_hypothesis_index"] for r in normal),
            "geometry_revision": source["geometry_revision"], "hardware_revision": source["hardware_revision"], "extra_grid": False,
            "current_bolt_count": 100, "rejected_cross_tie_proposal_used": False, "native_or_frame_solve_or_geometry_change": False,
            "cleat_transverse_resistance": None, "complete_joint_resistance": None, "physical_demand_bounds_established": False,
            "structural_acceptance": False, "release": source["release"],
            "limits": ["The NDS shear equation is source-backed for its rectangular bending-member component. Current signed adjacent section Y shears are used; a Y-normal opening force or moment is never substituted as that shear demand.",
                       "The upper bore band intersects a sloping end. The minimum engaged depth with original stock depth is a conservative parameter sensitivity, not an adopted complete nonrectangular cleat resistance.",
                       "The historical Ft90=.5MPa/Gc=.1N/mm are explicitly unmeasured hypotheses. Their numerical comparison does not qualify those properties for current DF-L No.2 timber; no duration factor or characteristic-to-design conversion is invented.",
                       "Complete simultaneous normal/shear/torsion, local fracture, group and response/compatibility qualifications stay separate. No new tie, native solve, material measurement or actual-fit observation is introduced."]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    with current.load("bridge").reserve(args.out) as output:
        output.write(run())
    print(json.dumps(current.ref(args.out)))


if __name__ == "__main__":
    main()
