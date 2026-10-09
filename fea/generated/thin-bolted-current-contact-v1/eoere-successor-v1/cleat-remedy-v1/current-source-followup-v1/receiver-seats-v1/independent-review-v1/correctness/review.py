"""Independent analytic/source review; no producer, CAD or mechanics imports.

Run with python3 -B PATH/TO/review.py [--out NEW_RECEIPT].
Continuous convex containment and parallel through-cut separation are checked
from source profile vertices and axes, without executing the target helpers.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import math
import os
from pathlib import Path

OWN = Path(__file__).resolve()
ROOT = next(p for p in OWN.parents if (p / "AGENTS.md").is_file())
TARGET = OWN.parents[2]
EXPECTED = {
    "inputs.json": "e3fda210640db0bc395d808c90625d65e8049da315c0872da12077731e6f0e41",
    "calculate.py": "5f6d088a836f1ac198c2cc7c8355b3a6ca8a20034a863ab813e4e33fa4a3fa03",
    "result.json": "a21c25d6693a86f2617655cec1e82aa51c182b153e19baf8f5d1431afa381443",
    "verify.py": "1ab517d0e2b874fc43c9c4f78fce1cda80dd6dbda2a70f9e37ebdce2edffc51c",
    "verification-v1.json": "ae0c5dd215fd2bddaa6c2b0fcf46fa51038ac672d8611722ee34b4b4d6afded6",
}


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    return json.loads(Path(path).read_bytes())


def authenticate():
    pins = {str((TARGET / name).relative_to(ROOT)): value for name, value in EXPECTED.items()}
    assert all(sha(ROOT / path) == value for path, value in pins.items())
    result, inputs = read(TARGET / "result.json"), read(TARGET / "inputs.json")
    control = TARGET / "controls01/frozen-packet.json"
    frozen = read(control)
    assert len(frozen["final_files"]) == len(frozen["retained_development_files"]) == 5
    for row in frozen["final_files"]:
        assert pins[row["path"]] == row["sha256"]
    for addition in (inputs["source_sha256"], result["source_sha256"],
                     {r["path"]: r["sha256"] for r in frozen["retained_development_files"]},
                     {str(control.relative_to(ROOT)): sha(control)}):
        for path, value in addition.items():
            assert path not in pins or pins[path] == value
            pins[path] = value
    assert all(sha(ROOT / path) == value for path, value in pins.items())
    return pins, inputs, result


def close(actual, expected, tolerance=2e-8):
    assert math.isfinite(actual) and abs(actual-expected) <= tolerance, (actual, expected)


def turn(a, b, c):
    return (b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0])


def hull(points):
    def half(rows):
        result = []
        for point in rows:
            while len(result) > 1 and turn(result[-2], result[-1], point) <= 0:
                result.pop()
            result.append(point)
        return result
    rows = sorted(set(points))
    return half(rows)[:-1]+half(rows[::-1])[:-1]


def interval(axis):
    x, d = axis["point_xyz_mm"][0], axis["direction_xyz"][0]
    assert abs(d) == 1 and axis["direction_xyz"][1:] == [0, 0]
    return sorted((x-d, x+d*(axis["grip_mm"]+1)))


def check(inputs, result):
    sources = {key: read(ROOT / ref["path"]) for key, ref in inputs["sources"].items() if ref["path"].endswith(".json")}
    geometry, cache, profiles = sources["geometry"], sources["cache"], sources["profiles"]
    axes = {a["id"]: a for a in geometry["axes"]}
    proposed = {a["id"]: a for a in result["proposed_axes"]}
    assert len(axes) == 100 and len(geometry["screw_axes"]) == 66
    assert set(proposed) == set(inputs["axis_ids"]) and len(proposed) == 4
    assert set(result["affected_members"]) == set(inputs["receivers"])
    assert geometry["axes"] == sources["base"]["axes"]
    assert geometry["screw_axes"] == sources["base"]["screw_axes"]
    assert {s["axis_id"]: s["source_axis"] for s in cache["shafts"]} == axes
    for key, proposal in proposed.items():
        old = copy.deepcopy(axes[key])
        assert old["point_xyz_mm"][2] == 200
        old["point_xyz_mm"][2] = 180
        assert proposal == old
    profiles2d = {}
    for name, member in result["affected_members"].items():
        source = profiles[name]
        world = {tuple(source["datum_xyz_mm"][j]+sum(p[i]*source["basis_grain_u_v_xyz"][i][j] for i in range(3))
                       for j in range(3)) for p in source["vertices_luv_mm"]}
        xs, polygon = sorted({p[0] for p in world}), hull([p[1:] for p in world])
        assert len(xs) == 2 and len(polygon) == 4 and len(world) == 8
        assert world == {(x, *p) for x in xs for p in polygon}
        assert member["X_interval_mm"] == xs and {tuple(p) for p in member["YZ_polygon_mm"]} == set(polygon)
        close(xs[1]-xs[0], 38.1)
        own = [a for a in axes.values() if name in a["receivers"]]
        assert len(own) == 4 and set(member["current_own_bore_axis_ids"]) == {a["id"] for a in own}
        for axis in own:
            span = interval(axis)
            assert span[0] < xs[0] and span[1] > xs[1]
        for revision in ("bottom", "aligned", "base"):
            assert not any(c["receiver"] == name for c in sources[revision]["service_cuts"])
        observation = next(r for r in cache["finished_body_observations"] if r["id"] == name)
        assert observation["source"]["path"] == source["finished"]["path"]
        assert observation["source"]["sha256"] == source["finished"]["sha256"]
        area = sum(a[0]*b[1]-a[1]*b[0] for a, b in zip(polygon, polygon[1:]+polygon[:1], strict=True))/2
        void = sum(math.pi*a["bore_diameter_mm"]**2*(xs[1]-xs[0])/4 for a in own)
        close(area*(xs[1]-xs[0])-void, source["finished"]["volume_mm3"], 1e-5)
        profiles2d[name] = (xs, polygon)
    summaries, rows_checked = [], 0
    assert len(result["scenarios"]) == 4
    for scenario in result["scenarios"]:
        maximum = scenario["bore_scenario"] == "all_affected_wood_bores_max11p1125"
        replace = scenario["void_inventory"] == "replace_eight_Z200_receiver_voids_from_raw_profiles"
        assert len(scenario["bore_occurrences"]) == len(scenario["nominal_annular_seats"]) == 8
        minima = {key: math.inf for key in ("bore_edge", "bore_cut", "seat_edge", "seat_cut")}
        for kind, rows in (("bore", scenario["bore_occurrences"]), ("seat", scenario["nominal_annular_seats"])):
            for row in rows:
                axis, name = proposed[row["axis_id"]], row["receiver"]
                xs, polygon = profiles2d[name]
                y, z = axis["point_xyz_mm"][1:]
                diameter = inputs["maximum_affected_wood_bore_diameter_mm"] if maximum else axis["bore_diameter_mm"]
                radius = diameter/2 if kind == "bore" else axis["hardware_scenario"]["washer_od_mm"]/2
                edge = min(turn(a, b, (y, z))/math.dist(a, b) for a, b in zip(polygon, polygon[1:]+polygon[:1], strict=True))-radius
                assert edge > 0
                field = "bore_to_raw_profile_edge_lower_bound_mm" if kind == "bore" else "annular_outer_edge_to_raw_profile_lower_bound_mm"
                close(row[field], edge)
                cuts = [a for a in axes.values() if name in a["receivers"] and not (replace and a["id"] in proposed)]
                cuts += [a for a in proposed.values() if name in a["receivers"] and a is not axis]
                gaps = []
                for cut in cuts:
                    span = interval(cut)
                    assert span[0] < xs[0] and span[1] > xs[1]
                    cut_radius = (inputs["maximum_affected_wood_bore_diameter_mm"] if maximum else cut["bore_diameter_mm"])/2
                    gaps.append(math.dist((y, z), cut["point_xyz_mm"][1:])-radius-cut_radius)
                assert len(gaps) == row["other_cut_comparisons"] == (3 if replace else 5)
                assert min(gaps) > 0
                close(row["minimum_other_cut_separation"]["capsule_separation_lower_bound_mm"], min(gaps))
                if kind == "seat":
                    direction = axis["direction_xyz"][0]
                    station = 0 if row["end"] == "head" else axis["grip_mm"]
                    x = axis["point_xyz_mm"][0]+station*direction
                    inward = direction if row["end"] == "head" else -direction
                    close(x, xs[0 if inward > 0 else 1])
                    assert xs[0] <= x+inward*inputs["annular_inward_skin_mm"] <= xs[1]
                    close(row["own_bore_to_annular_inner_radius_margin_mm"], (axis["hardware_scenario"]["washer_id_mm"]-diameter)/2)
                    assert row["own_bore_to_annular_inner_radius_margin_mm"] >= 0
                    assert row["physical_contact_or_strength_qualified"] is False
                minima[kind+"_edge"] = min(minima[kind+"_edge"], edge)
                minima[kind+"_cut"] = min(minima[kind+"_cut"], min(gaps))
                rows_checked += 1
        for source, key in (("bore_edge", "minimum_raw_profile_bore_margin_mm"), ("bore_cut", "minimum_bore_to_other_cut_lower_bound_mm"),
                            ("seat_edge", "minimum_raw_profile_annular_outer_margin_mm"), ("seat_cut", "minimum_annular_disk_to_other_cut_lower_bound_mm")):
            close(scenario[key], minima[source])
        summaries.append({"maximum_hole": maximum, "replace_old_voids": replace, **minima})
    assert rows_checked == 64
    assert result["complete_joint_resistance"] is None and all(v is False for v in result["release"].values())
    assert result["current_geometry_adopted_or_changed"] is False and result["optional_2026_extra"] is False
    return summaries


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=OWN.with_name("receipt.json"))
    args = parser.parse_args()
    assert not os.path.lexists(args.out), "preserve issued review evidence"
    before, inputs, result = authenticate()
    summaries = check(inputs, result)
    after, _, _ = authenticate()
    assert before == after
    receipt = {"schema": "eoere_Z180_receiver_seats_independent_correctness_review/v1",
        "status": "NO_SUBSTANTIAL_FINDINGS_WITHIN_SOURCE_RECIPE_ANALYTIC_SCOPE", "findings": [],
        "checks": ["All four source convex hulls, full-X cutter spans and source/cache/current-axis identities checked without importing the producer or verifier.",
                   "All 64 bore/seat rows and four summary scenarios independently reproduce via continuous half-space and direct transverse disk separation.",
                   "External head/nut receiver-face ownership, inward skin and own-bore/washer-ID margins checked.",
                   "Four own recorded cuts per receiver and no recorded service cuts; raw-minus-cylinders volume is checked only as source consistency.",
                   "Final five files, all five development records and frozen manifest remain unchanged."],
        "source_sha256": before, "source_pins_exact_before_after_unchanged": True,
        "review_script": {"path": str(OWN.relative_to(ROOT)), "sha256": sha(OWN)},
        "independent_checked_rows": 64, "scenario_minima_mm": summaries,
        "limits": ["Current axes remain Z200; Z180 is an unadopted source-recipe proposal.",
                   "No independent topology reconstruction, finished BREP query, tool/installation pass, material capacity or physical observation is supplied.",
                   "Screw pilots/countersinks are omitted from the modeled timber; nominal washer and declared maximum-hole scenarios do not bound delivered parts or fit.",
                   "No native/CAD/global/current-component execution, shared/index edit, staging, commit, archive or pruning occurred."],
        "complete_joint_resistance": None, "release": result["release"]}
    with args.out.open("x") as stream:
        json.dump(receipt, stream, indent=2, sort_keys=True, allow_nan=False)
        stream.write("\n")
    print(json.dumps({"status": receipt["status"], "source_files": len(before), "receipt_sha256": sha(args.out)}))


if __name__ == "__main__":
    main()
