"""Independent rational wrench/support-edge/witness check; no frame mechanics."""
from __future__ import annotations

import hashlib
import itertools
import json
import math
import os
import subprocess
import sys
import tempfile
from fractions import Fraction as Q
from pathlib import Path

OWN = Path(__file__).resolve()
ROOT = next(p for p in OWN.parents if (p / "AGENTS.md").is_file())
TARGET = OWN.parent.parent.parent / "global-statics-v1"
HASHES = {
    "check_current.py": "c2c32d1fdadae374b5d7f7d192d979e52954011bc041171980cc6e63a0aeceaa",
    "verify.py": "68e27a587cadc08b64923cbe76fdf5db36c35ca0cca6d8789ac3f3b44be7862d",
    "result.json": "f05f81d17a80b1fc1e2a0df106a60ac34f6253a1bb0b664a7241e63cc3702c24",
    "verification.json": "2278f49ebd516bb3cc10fc1fffa53bdda989008c66429eeb4e55c2952404b203",
}


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    return json.loads(Path(path).read_bytes())


def cross(a, b, c):
    return (b[0]-a[0])*(c[1]-a[1]) - (b[1]-a[1])*(c[0]-a[0])


def near(a, b, limit):
    assert math.isfinite(a) and math.isfinite(float(b)) and abs(a-float(b)) <= limit, (a, b, limit)


def main():
    os.chdir(ROOT)
    assert {name: sha(TARGET / name) for name in HASHES} == HASHES
    record, verification = (read(TARGET / n) for n in ("result.json", "verification.json"))
    direct = record["source_bindings"]
    assert len(direct) == 8
    for path, digest in verification["source_bindings"].items():
        assert sha(ROOT / path) == digest
    current_path = next(p for p in direct if p.endswith("current-inputs-v1/attempt01/inputs.json"))
    old_path = next(p for p in direct if p.endswith("raised-rail-mechanics-v1/inputs.json"))
    data, old = read(ROOT / current_path), read(ROOT / old_path)
    cache = read(ROOT / data["geometry"]["cached_source_export"]["path"])
    assert record["input_status_preserved"] == data["status"] == "CURRENT_SOURCE_ROWS_PENDING_INDEPENDENT_REVIEW"
    assert record["input_readiness_preserved"] == data["readiness"] == {
        "complete_reference_contact_inventory": False, "source_joins_independently_reviewed": False}
    assert record["input_recursive_pin_count_declared_not_independently_rehashed_here"] == len(data["source_sha256"]) == 1086
    assert data["optional_2026_extra"] is False and data["historical_q"] is data["old_field"] is None
    assert record["release"] == data["release"] and not any(record["release"].values())
    assert {r["host"]: r["observed_normal_reference_points_xyz_mm"] for r in cache["floor_observations"]} == data["floor_footprints"]
    rows = record["support_point_order"]
    ordered = [(host, i, p) for host in sorted(data["floor_footprints"]) for i, p in enumerate(data["floor_footprints"][host])]
    assert len(rows) == len(ordered) == 32
    changed = []
    for index, (host, corner, point) in enumerate(ordered):
        assert rows[index] == {"index": index, "host": host, "corner_index": corner, "point_xyz_mm": point}
        assert point[2] == 0
        previous = old["floor_footprints"][host][corner]
        delta = [Q(str(x))-Q(str(y)) for x, y in zip(point, previous, strict=True)]
        assert delta == ([Q("-39.2"), 0, 0] if host == "base_post_center_right" else [0, 0, 0])
        if point != previous:
            changed.append((host, corner))
    assert len(changed) == record["legacy_footprint_comparison"]["changed_point_count"] == 4

    # Enumerate supporting oriented lines directly, without a hull library or
    # the producer verifier's monotone-chain algorithm. Keep full extreme edges.
    points = sorted({tuple(Q(str(x)) for x in p[:2]) for _, _, p in ordered})
    edges = []
    for a, b in itertools.permutations(points, 2):
        signed = [cross(a, b, p) for p in points]
        if any(value < 0 for value in signed):
            continue
        length_squared = sum((y-x)**2 for x, y in zip(a, b, strict=True))
        if any(not 0 <= sum((p[i]-a[i])*(b[i]-a[i]) for i in range(2)) <= length_squared
               for p, value in zip(points, signed, strict=True) if value == 0):
            continue
        edges.append((a, b))
    assert len(edges) == 6
    vertices = sorted({p for edge in edges for p in edge})
    max_force = max_moment = max_margin = max_saved_witness = 0.
    triangle_witnesses, case_rows = 0, []
    gravity = data["cases"][-1]
    assert len(gravity["loads"]) == 826 and gravity["hold"] is None
    for source, saved in zip(data["cases"], record["cases"], strict=True):
        assert source["case_id"] == saved["case_id"] and saved["source_load_count"] == len(source["loads"])
        if source is not gravity:
            assert len(source["loads"]) == 827 and source["loads"][:-1] == gravity["loads"]
        force, moment = [Q(0)]*3, [Q(0)]*3
        for load in source["loads"]:
            assert not any("moment" in key for key in load)
            p, f = ([Q(str(v)) for v in load[key]] for key in ("point_xyz_mm", "force_xyz_n"))
            for i, j, k in ((0, 1, 2), (1, 2, 0), (2, 0, 1)):
                force[i] += f[i]
                moment[i] += p[j]*f[k] - p[k]*f[j]
        for i in range(3):
            max_force = max(max_force, abs(saved["applied_force_xyz_n"][i]-float(force[i])))
            max_moment = max(max_moment, abs(saved["applied_moment_xyz_nmm"][i]-float(moment[i])))
            near(saved["applied_force_xyz_n"][i], force[i], 1e-8)
            near(saved["applied_moment_xyz_nmm"][i], moment[i], 1e-6)
            near(source["applied_force_xyz_n"][i], force[i], 1e-8)
            near(source["applied_moment_about_global_origin_xyz_nmm"][i], moment[i], 1e-6)
        normal = -force[2]
        assert normal > 0
        cop = (moment[1]/normal, -moment[0]/normal)
        distances = [float(cross(a, b, cop))/math.hypot(float(b[0]-a[0]), float(b[1]-a[1])) for a, b in edges]
        margin = min(distances)
        near(saved["minimum_support_polygon_edge_margin_mm"], margin, 1e-9)
        max_margin = max(max_margin, abs(saved["minimum_support_polygon_edge_margin_mm"]-margin))
        assert saved["compression_equilibrium_possible"] is True and margin > 0
        assert sorted(tuple(Q(str(x)) for x in p) for p in saved["support_polygon_xy_mm"]) == vertices
        for a, b in zip(saved["required_center_of_pressure_xy_mm"], cop, strict=True):
            near(a, b, 1e-9)
        near(saved["total_normal_reaction_n"], normal, 1e-8)
        near(saved["required_reaction_yaw_moment_nmm"], -moment[2], 1e-6)
        near(saved["minimum_aggregate_friction_ratio_ignoring_yaw_and_distribution"], math.hypot(float(force[0]), float(force[1]))/float(normal), 1e-12)
        witness = saved["normal_reaction_witness_n"]
        assert len(witness) == 32 and all(math.isfinite(n) and n >= 0 for n in witness)
        residual = [math.fsum(witness)-float(normal),
            math.fsum(p[1]*n for (_, _, p), n in zip(ordered, witness, strict=True))+float(moment[0]),
            -math.fsum(p[0]*n for (_, _, p), n in zip(ordered, witness, strict=True))+float(moment[1])]
        near(residual[0], 0, 1e-8)
        for value in residual[1:]:
            near(value, 0, 1e-4)
            max_saved_witness = max(max_saved_witness, abs(value))
        # Construct an entirely separate rational three-point normal witness.
        for a, b, c in itertools.combinations(vertices, 3):
            area = cross(a, b, c)
            if not area:
                continue
            weights = [cross(cop, b, c)/area, cross(a, cop, c)/area, cross(a, b, cop)/area]
            if min(weights) < 0:
                continue
            assert sum(weights) == 1
            assert sum(w*p[0] for w, p in zip(weights, (a, b, c), strict=True))*normal == moment[1]
            assert sum(w*p[1] for w, p in zip(weights, (a, b, c), strict=True))*normal == -moment[0]
            triangle_witnesses += 1
            break
        else:
            raise AssertionError("no independent three-point compression witness")
        assert saved["elastic_joint_demands_or_floor_capacity_established"] is False
        case_rows.append({"case_id": source["case_id"], "independent_edge_margin_mm": margin})
    near(record["mass"]["total_kg"], -Q(str(gravity["applied_force_xyz_n"][2]))/Q(str(data["parameters"]["gravity_m_s2"])), 1e-10)
    worst = min(case_rows, key=lambda row: row["independent_edge_margin_mm"])
    assert record["summary"]["minimum_edge_margin_case"] == worst["case_id"]
    near(record["summary"]["minimum_edge_margin_mm"], worst["independent_edge_margin_mm"], 1e-9)

    with tempfile.TemporaryDirectory(prefix="source-controls-", dir=OWN.parent) as temp:
        process = subprocess.run([sys.executable, "-B", str(TARGET / "verify.py"), "--out", str(Path(temp) / "fresh")],
            cwd=ROOT, env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"}, capture_output=True, text=True, check=True)
        assert json.loads(process.stdout) == {"passed": True, "controls": 7, "independent_cases": 7}
    assert {name: sha(TARGET / name) for name in HASHES} == HASHES
    for path, digest in verification["source_bindings"].items():
        assert sha(ROOT / path) == digest
    return {"schema": "eoere_current_global_statics_independent_correctness_review/v1", "findings": [],
        "target_source_sha256": HASHES, "review_helper_sha256": sha(OWN), "direct_source_pins_rehashed": len(direct),
        "recursive_1086_input_pins_not_admitted_or_rehashed": True, "known_answer_fixtures": 7,
        "producer_replay_guard_controls": 7, "producer_Decimal_numerical_checks": 7,
        "independent_rational_checks": {"source_load_wrenches": 5788, "current_floor_points": 32,
            "old_identical_floor_points": 28, "shifted_right_center_post_points": 4, "supporting_extreme_edges": 6,
            "constructed_three_point_compression_witnesses": triangle_witnesses, "cases": case_rows,
            "maximum_force_error_n": max_force, "maximum_moment_error_nmm": max_moment,
            "maximum_edge_margin_error_mm": max_margin, "maximum_saved_witness_moment_residual_nmm": max_saved_witness},
        "limits": ["Necessary global compression/pitch/roll equilibrium only; no frame/global stiffness assembly, native solve, CAD/BRep query or browser.",
            "Nonnegative reactions are equilibrium witnesses; elastic reactions, horizontal/yaw distribution, floor/friction and joint capacity remain unestablished.",
            "Exact current input direct bytes authenticated; its1086 recursive sources and independent input/frame admission are outside this review.",
            "Frozen pending-input status/readiness retained; no old forces/pass, physical observations, fabrication or climbing release.",
            "Only exclusive review.py/receipt.json retained; temporary source/output controls used copied modules and left frozen sources unchanged."],
        "release": record["release"]}


if __name__ == "__main__":
    receipt = main()
    destination = OWN.with_name("receipt.json")
    with destination.open("x") as stream:
        json.dump(receipt, stream, indent=2, sort_keys=True, allow_nan=False)
        stream.write("\n")
    print(json.dumps({"passed": True, "findings": receipt["findings"], "receipt_sha256": sha(destination),
        "independent": receipt["independent_rational_checks"]}))
