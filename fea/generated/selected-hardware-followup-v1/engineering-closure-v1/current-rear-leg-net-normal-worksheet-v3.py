"""Current rear-leg staggered-hole net-normal worksheet, no response solve."""
import argparse
import ast
import hashlib
import json
import math
from collections import defaultdict
from itertools import combinations, pairwise, product
from pathlib import Path
from types import SimpleNamespace

import numpy as np

ROOT = Path.cwd()
SUMMARY = Path("docs/wood-joints-mvp/hypotheses/hl35-candidate/thin-frame-comparison/eoere-successor-v1/selected-hardware-v1/current-response-v1/result.json")
HISTORY = Path("docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/upper-corner-screw-layout/corner-net-section.py")
PINS = {
    str(HISTORY): "8a60447291161300ec4ee4f4f89c783cdcb565ee771e972c524ffd10f006d0e5",
    "scripts/thin_bolted_timber_common_shaft_checks.py": "c27d8d0209f2b0a032c490314fe05cee8fbc949f608dabbf813676c044b90cc7",
    "scripts/thin_bolted_timber_demand_checks.py": "1be05e74563d2cc7a7ea5437aa4ff7217e62f8314f9fe011ff273d201f755e20",
    "fea/reinforced_timber_resistance.py": "d4e8302d39beb9f53c70fa264762c59c231f6e6b086cb866906ca39eeab9cfbc",
    "scripts/thin_bolted_timber_resistance.py": "74d992cfbe4947587a8c6f0e65f7a8b47e0cd1c79f07721620c7137208919c2d",
}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def read_bound(path, expected=None):
    path = Path(path)
    data = path.read_bytes()
    digest = hashlib.sha256(data).hexdigest()
    require(expected is None or digest == expected, str(path))
    PINS[str(path)] = digest
    return json.loads(data)


def interval_scale(coefficient, interval):
    return sorted(coefficient * value for value in interval)


def normal_coefficients(props, datum_uv, corner):
    """Ordinary N/A and biaxial M/I about the projected net centroid."""
    center = np.array(props["centroid_uv_mm"])
    uu, uv = props["central_integral_u2_uv_v2_matrix_mm4"][0]
    _, vv = props["central_integral_u2_uv_v2_matrix_mm4"][1]
    determinant = uu * vv - uv * uv
    require(determinant > 0, "positive net section moments")
    offset = np.r_[0., center - datum_uv]
    bending = []
    for unit in np.eye(6):
        moment = unit[3:] - np.cross(offset, unit[:3])
        hu, hv = -moment[2], moment[1]
        beta = np.array([vv * hu - uv * hv, uu * hv - uv * hu]) / determinant
        bending.append(float(beta @ (np.array(corner) - center)))
    return np.array([1. / props["area_mm2"], 0., 0., 0., 0., 0.]), np.array(bending)


def stress_range(coefficient, branch, s0, s1, row, gravity):
    """Bound one scalar cut stress over a fixed point-action interval.

    Point wrenches are affine in cut station. Affine selfweight has a
    nonnegative density; bound its mass fraction and first-moment integral
    separately. Their interval product is conservative, with no fitted field.
    """
    frame = np.array([row[k] for k in ("axis", "section_u", "section_v")])
    grain, start, end = frame[0], np.array(row["start"]), np.array(row["end"])
    low, high = float(grain @ start), float(grain @ end)
    center, weight = map(np.array, gravity)
    length, mid = high - low, (low + high) / 2
    center_s = float(grain @ center)
    beta = 12 * (center_s - mid) / length**2
    require(min(1 + beta * (low - mid), 1 + beta * (high - mid)) >= -1e-10, "nonnegative affine weight")
    force = sum((np.array(a) for _, a, _ in branch), np.zeros(3))
    about_origin = sum((np.cross(p, a) + free for p, a, free in branch), np.zeros(3))
    point_values = []
    for station in (s0, s1):
        point = start + grain * (station - low)
        local = np.r_[frame @ -force, frame @ (-about_origin + np.cross(point, force))]
        point_values.append(float(coefficient @ local))

    def fraction(s):
        return ((s - low) + beta * ((s - mid)**2 - (low - mid)**2) / 2) / length

    def first(s):
        return ((s*s - low*low) / 2 + beta * ((s**3 - low**3) / 3 - mid * (s*s - low*low) / 2)) / length

    fractions = [fraction(s0), fraction(s1)]
    require(-1e-9 <= fractions[0] <= fractions[1] <= 1 + 1e-9, "monotone weight fraction")
    first_values = [first(s0), first(s1)]
    if s0 < 0 < s1:
        first_values.append(first(0.))
    first_interval = [min(first_values), max(first_values)]
    product_interval = [(s0 - low) * fractions[0], (s1 - low) * fractions[1]]
    relative_first = [first_interval[0] - product_interval[1], first_interval[1] - product_interval[0]]
    off_axis = center - grain * center_s
    fixed_arm = off_axis - start
    fraction_wrench = np.r_[frame @ -weight, frame @ -np.cross(fixed_arm, weight)]
    first_wrench = np.r_[np.zeros(3), frame @ -np.cross(grain, weight)]
    a = interval_scale(float(coefficient @ fraction_wrench), fractions)
    b = interval_scale(float(coefficient @ first_wrench), relative_first)
    bounds = [min(point_values) + a[0] + b[0], max(point_values) + a[1] + b[1]]
    guard = 1e-8 * (1 + max(map(abs, bounds)))
    return [bounds[0] - guard, bounds[1] + guard]


def run():
    buffers = {path: Path(path).read_bytes() for path in PINS}
    for path, data in buffers.items():
        require(hashlib.sha256(data).hexdigest() == PINS[path], path)

    def selected(path, names, namespace, constants=()):
        nodes = []
        found = set()
        for node in ast.parse(buffers[path]).body:
            if isinstance(node, ast.FunctionDef) and node.name in names:
                nodes.append(node)
                found.add(node.name)
            elif isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name) and node.targets[0].id in constants:
                namespace[node.targets[0].id] = ast.literal_eval(node.value)
        require(found == set(names) and all(name in namespace for name in constants), "selected existing definitions: " + path)
        exec(compile(ast.Module(body=nodes, type_ignores=[]), path, "exec"), namespace)  # noqa: S102 -- captured authenticated scalar definitions only
        return SimpleNamespace(**namespace)

    unit = selected("scripts/thin_bolted_timber_resistance.py", {"require", "vector", "dot", "cross"}, {"math": math})
    previous = selected("scripts/thin_bolted_timber_demand_checks.py", {"add", "scale", "free_moment", "member_cut_wrench"}, {"unit": unit})
    cuts = selected("scripts/thin_bolted_timber_common_shaft_checks.py", {"member_point_inputs"}, {"unit": unit, "previous": previous, "defaultdict": defaultdict})
    nds = selected("fea/reinforced_timber_resistance.py", {"adjusted_reference"}, {"math": math}, {"PSI_MPA", "SIZE_FACTORS"})
    history = selected(str(HISTORY), {"area_properties"}, {"np": np, "math": math, "combinations": combinations, "require": require})
    area_properties = history.area_properties
    check = area_properties([{"bounds_uv_mm": [[-2., 2.], [-3., 3.]]}])
    require(abs(check["area_mm2"] - 24) < 1e-12 and np.allclose(check["central_integral_u2_uv_v2_matrix_mm4"], [[32., 0.], [0., 72.]]), "rectangle known answer")
    summary = read_bound(SUMMARY)
    require(summary["all_six_saved_field_admissions_pass"] and not summary["extra_grid"], "current admitted six cases")
    reference = nds.adjusted_reference(139.7)
    results = []
    for case in summary["cases"]:
        field = read_bound(case["field"]["path"], case["field"]["sha256"])
        require(field["case_id"] == case["case_id"] and field["state_id"] == case["state_id"], "same current state")
        actions, gravity = cuts.member_point_inputs(field)
        members = {r["name"]: r for r in field["source_inputs"]["timber_rows"]}
        for name in ("lumber_leg_left", "lumber_leg_right"):
            row = members[name]
            observation = next(r for r in field["source_inputs"]["finished_body_observations"] if r["id"] == name)
            PINS[observation["source"]["path"]] = observation["source"]["sha256"]
            raw = row["raw_profile_source"]
            frame = np.array(raw["basis_grain_u_v_xyz"])
            datum = np.array(raw["datum_xyz_mm"])
            start = np.array(row["start"])
            require(np.max(abs(frame - np.array([row[k] for k in ("axis", "section_u", "section_v")]))) < 1e-9, "same profile and action basis")
            datum_uv = (frame @ (start - datum))[1:]
            bore_rows = []
            for shaft in field["source_inputs"]["shafts"]:
                for surface in shaft["surfaces"]:
                    if surface["host"] != name:
                        continue
                    axis = np.array(shaft["basis"][0])
                    require(abs(frame[0] @ axis) < 1e-9 and abs(abs(frame[1] @ axis) - 1) < 1e-9, "transverse full-width bore")
                    point = np.array(shaft["point"]) + axis * np.mean(surface["interval_mm"])
                    bore_rows.append({"axis_id": shaft["axis_id"], "local_luv_mm": (frame @ (point - datum)).tolist(), "bolt_diameter_mm": shaft["diameter_mm"], "bore_diameter_mm": surface["bore_diameter_mm"]})
            require(len(bore_rows) == 4, "four current leg bores")
            for kind, bores in [("recessed_foot_pair", [b for b in bore_rows if b["axis_id"].startswith("rail_rear_")]), ("upper_leg_pair", [b for b in bore_rows if b["axis_id"].startswith("lumber_leg_")])]:
                require(len(bores) == 2, "two staggered holes per critical section")
                gap = abs(bores[0]["local_luv_mm"][0] - bores[1]["local_luv_mm"][0])
                require(gap < 4 * min(b["bolt_diameter_mm"] for b in bores), "NDS3.1.2.2 concurrent deduction")
                u0, u1 = ((0., 50.8) if name.endswith("left") else (38.1, 88.9)) if kind == "recessed_foot_pair" else (0., 88.9)
                holes = sorted((b["local_luv_mm"][2] - b["bore_diameter_mm"] / 2 - 1e-6, b["local_luv_mm"][2] + b["bore_diameter_mm"] / 2 + 1e-6) for b in bores)
                require(-139.7 < holes[0][0] < holes[0][1] < holes[1][0] < holes[1][1] < 0., "separated projected bore strips")
                regions = [{"bounds_uv_mm": [[u0 + 1e-6, u1 - 1e-6], [a, b]]} for a, b in [(-139.7 + 1e-6, holes[0][0]), (holes[0][1], holes[1][0]), (holes[1][1], -1e-6)]]
                props = area_properties(regions)
                corners = [p for region in regions for p in product(*region["bounds_uv_mm"])]
                coefficients = [normal_coefficients(props, datum_uv, corner) for corner in corners]
                lo = min(b["local_luv_mm"][0] - b["bore_diameter_mm"] / 2 - 1e-6 for b in bores) + float(frame[0] @ datum)
                hi = max(b["local_luv_mm"][0] + b["bore_diameter_mm"] / 2 + 1e-6 for b in bores) + float(frame[0] @ datum)
                stations = sorted({lo, hi, *(float(frame[0] @ p) for p, _, _ in actions[name] if lo < frame[0] @ p < hi)})
                intervals = []
                for s0, s1 in pairwise(stations):
                    branch = [(np.array(p), np.array(a), np.array(free)) for p, a, free in actions[name] if frame[0] @ p <= s0]
                    axial = stress_range(coefficients[0][0], branch, s0, s1, row, gravity[name])
                    bending = [stress_range(c[1], branch, s0, s1, row, gravity[name]) for c in coefficients]
                    if s1 - s0 > 1e-6:
                        station = (s0 + s1) / 2
                        low, high = [float(frame[0] @ np.array(row[k])) for k in ("start", "end")]
                        point = start + frame[0] * (station - low)
                        original = previous.member_cut_wrench(frame[0].tolist(), low, high, point.tolist(), *gravity[name], actions[name])
                        q = np.r_[frame @ original["force_on_lower_portion_xyz_n"], frame @ original["moment_on_lower_portion_about_cut_xyz_nmm"]]
                        require(axial[0] - 1e-7 <= coefficients[0][0] @ q <= axial[1] + 1e-7, "axial bound vs existing same-cut helper")
                        for (_, coefficient), bound in zip(coefficients, bending, strict=True):
                            require(bound[0] - 1e-7 <= coefficient @ q <= bound[1] + 1e-7, "bending bound vs existing same-cut helper")
                    axial_upper = max(0., axial[1]) / reference["Ft_mpa"] + max(0., -axial[0]) / reference["Fc_star_mpa"]
                    bend_upper = max(abs(x) for pair in bending for x in pair) / reference["Fb_star_mpa"]
                    intervals.append({"grain_station_interval_mm": [s0, s1], "point_action_count": len(branch), "axial_stress_interval_mpa": axial, "bending_stress_interval_mpa": [min(p[0] for p in bending), max(p[1] for p in bending)], "linear_axial_plus_bending_reference_upper": axial_upper + bend_upper})
                results.append({"member": name, "case_id": case["case_id"], "state_id": case["state_id"], "detail": kind, "bores": bores, "parallel_spacing_mm": gap, "four_bolt_diameters_mm": 4 * min(b["bolt_diameter_mm"] for b in bores), "projected_net_section": props, "cut_origin_uv_mm": datum_uv.tolist(), "intervals": intervals, "nominal_net_normal_reference_upper": max(p["linear_axial_plus_bending_reference_upper"] for p in intervals)})
    require(len(results) == 24, "two pairs, two legs, six cases")
    for path, digest in PINS.items():
        require(hashlib.sha256(Path(path).read_bytes()).hexdigest() == digest, "source changed: " + path)
    return {"schema": "eoere_rear_leg_projected_net_normal_worksheet/v1", "geometry_revision": summary["geometry_revision"], "hardware_revision": summary["hardware_revision"], "extra_grid": False, "reference": reference, "source_sha256": PINS, "results": results, "maximum_nominal_net_normal_reference_upper": max(r["nominal_net_normal_reference_upper"] for r in results), "all_named_net_normal_references_below_one": all(r["nominal_net_normal_reference_upper"] < 1 for r in results), "limits": ["NDS2024 3.1.2.1-.2 projected concurrent staggered-hole deductions and compatible nominal linear normal sections only.", "Current outer foot/profile coordinates and four transverse full-width bores are the geometry basis; source geometry remains unchanged.", "Every current point force, free couple and affine selfweight is retained; independent interval extrema give conservative nominal-reference bounds, not a simultaneous stress witness.", "DF-L No.2 dry unincised CD1 references; no CP/CL, local notch shear/splitting, torsion, joint resistance, physical restraint or demand qualification.", "No source response producer, native solve, optimization, inverse, CAD rebuild or design change."], "complete_rear_recess_or_member_resistance": None, "structural_acceptance": False, "actual_observations": None}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    result = run()
    result["reproduction_source"] = {"path": str(Path(__file__).resolve().relative_to(ROOT)), "sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
    with args.out.open("x") as output:
        output.write(json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n")
    print(json.dumps({"output": str(args.out), "comparisons": len(result["results"]), "maximum_nominal_net_normal_reference_upper": result["maximum_nominal_net_normal_reference_upper"], "all_named_net_normal_references_below_one": result["all_named_net_normal_references_below_one"]}))
