"""Independent signed census and separate square-end-marker source review."""
from __future__ import annotations

import hashlib
import importlib.util
import json
import math
import os
import subprocess
import sys
import tempfile
from pathlib import Path

OWN = Path(__file__).resolve()
ROOT = next(p for p in OWN.parents if (p / "AGENTS.md").is_file())
TARGET = OWN.parent.parent.parent
HASHES = {"analyze.py": "fc45c5e990b11c20a3e6e98e9723b25ec366d05a780b229d82cdb639c6dc4ad0",
          "result.json": "4c66a7f194a747a14291e25c4277ec7288aa95a9bef9eab68233312288e9be9b"}


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    return json.loads(Path(path).read_bytes())


def near(a, b, tolerance=1e-10):
    assert math.isfinite(a) and math.isfinite(b) and abs(a-b) <= tolerance, (a, b)


def main():
    os.chdir(ROOT)
    assert {name: sha(TARGET / name) for name in HASHES} == HASHES
    issued = read(TARGET / "result.json")
    pins = issued["source_sha256"]
    assert len(pins) == 26
    for path, digest in pins.items():
        assert sha(ROOT / path) == digest
    module_spec = importlib.util.spec_from_file_location("independent_end_inventory_target", TARGET / "analyze.py")
    target = importlib.util.module_from_spec(module_spec)
    module_spec.loader.exec_module(target)
    source, summary, placement = (read(ROOT / path) for path in (target.INPUT, target.SUMMARY, target.PLACEMENT))
    report_ref = summary["geometry"]["report"]
    geometry = read(ROOT / report_ref["path"])
    assert source["geometry"] == summary["geometry"]
    assert geometry["revision"] == "eoere-base-side-edge-cleats-v1"
    assert report_ref["sha256"] == "01ba30abe20c2efec136374b8d9a74a098a19929be3cc784b5ebcf7608e62a2d"
    assert placement["geometry_adopted"] is False and placement["current_geometry_source"] == report_ref
    axes, shafts = ({a["id"]: a for a in geometry["axes"]}, {s["axis_id"]: s for s in source["shafts"]})
    members = {m["name"]: m for m in source["timber_rows"]}
    proposed = {a["id"]: a for a in placement["proposed_axes"]}
    assert set(proposed) == target.IDS
    for name in target.IDS:
        assert shafts[name]["source_axis"] == axes[name]
        current = axes[name]
        assert current["point_xyz_mm"][2] == 200.
        assert proposed[name] == {**current, "point_xyz_mm": [*current["point_xyz_mm"][:2], 180.]}
    assert len(geometry["axes"]) == len(shafts) == 100 and len(source["hillman_rows"]) == 66
    census = issued["current_Z200_inventory"]
    case_rows = census["cases"]
    assert tuple(c["case_id"] for c in case_rows) == tuple(c["case_id"] for c in summary["cases"]) == target.CASES
    surfaces, point_count, parallel_reversals, cross_reversals, zero, oblique, angles = 0, 0, 0, 0, 0, 0, []
    for case, selected in zip(summary["cases"], case_rows, strict=True):
        report = read(ROOT / case["rich"]["result"]["path"])
        admission = read(ROOT / case["admission"]["path"])
        assert report["case_id"] == selected["case_id"] == admission["case_id"] == case["case_id"]
        assert report["state_id"] == selected["state_id"] == admission["state_id"]
        assert selected["report"] == case["rich"]["result"]
        assert report["current_geometry"] == report_ref
        assert report["raw_field_sha256"] == admission["input_raw_sha256"] == case["field"]["sha256"]
        assert report["field_admission_receipt_sha256"] == case["admission"]["sha256"]
        assert report["complete_joint_resistance"] is None and not any(report["release"].values())
        assert admission["current_extended_cleat_equilibrium_and_recovery_pass"] is True
        report_rows = {(r["axis_id"], r["receiver"]): r for r in report["findings"]["timber"]["wood_surfaces"] if r["axis_id"] in target.IDS}
        expected_surface_ids = {(name, surface["host"]) for name in target.IDS for surface in shafts[name]["surfaces"]}
        assert len(report_rows) == len(selected["current_Z200_surfaces"]) == 8 and set(report_rows) == expected_surface_ids
        for row in selected["current_Z200_surfaces"]:
            key = row["axis_id"], row["receiver"]
            original = report_rows[key]
            member, shaft = members[row["receiver"]], shafts[row["axis_id"]]
            assert member["axis"] == [0., 0., 1.]
            sign = shaft["basis"][0][0]
            assert shaft["basis"][0] == [sign, 0., 0.] and sign in (-1., 1.)
            assert row["current_axis_Z_mm"] == shaft["point"][2] == 200.
            source_points = {p["id"]: p for p in original["own_point_actions"] if p["kind"] == "common_shaft_bearing"}
            assert len(source_points) == len(row["own_bearings"]) == 2
            parallel, transverse = [], []
            for point in row["own_bearings"]:
                raw = source_points[point["id"]]
                signed = raw["signed_components"]
                assert point["point_xyz_mm"] == raw["point_xyz_mm"]
                assert point["point_xyz_mm"][1:] == axes[row["axis_id"]]["point_xyz_mm"][1:]
                force = point["force_on_receiver_xyz_n"]
                assert force == signed["force_on_receiver_xyz_n"]
                # For these exact vertical-grain/X-shaft members, Fz is the
                # independent parallel component, and signed Fy is transverse.
                near(point["parallel_grain_signed_n"], force[2])
                near(point["cross_grain_signed_n"], sign*force[1])
                magnitude = math.hypot(force[1], force[2])
                threshold = 1e-10*max(magnitude, 1.)
                theta = None if magnitude < threshold else math.degrees(math.atan2(abs(force[1]), abs(force[2])))
                if theta is None:
                    assert point["load_to_grain_degrees"] is None
                    zero += 1
                else:
                    near(point["load_to_grain_degrees"], theta)
                    angles.append(theta)
                is_oblique = abs(force[1]) >= threshold and abs(force[2]) >= threshold
                assert point["oblique_lateral_action"] is is_oblique
                oblique += is_oblique
                parallel.append(force[2])
                transverse.append(sign*force[1])
                point_count += 1
            reversal, cross_reversal = min(parallel) < 0 < max(parallel), min(transverse) < 0 < max(transverse)
            assert row["bearing_parallel_sign_reversal"] is reversal
            assert row["bearing_crossgrain_sign_reversal"] is cross_reversal
            assert original["complete_Cdelta"] is original["complete_Cg"] is None
            parallel_reversals += reversal
            cross_reversals += cross_reversal
            surfaces += 1
    assert surfaces == census["wood_surface_count"] == 48
    assert point_count == census["bearing_point_count"] == 96
    assert parallel_reversals == census["parallel_sign_reversal_surface_count"] == 39
    assert cross_reversals == census["crossgrain_sign_reversal_surface_count"] == 43
    assert zero == census["zero_lateral_bearing_points"] == 5
    assert oblique == census["oblique_bearing_points"] == 91
    near(min(angles), census["nonzero_bearing_angle_range_deg"][0])
    near(max(angles), census["nonzero_bearing_angle_range_deg"][1])

    marker_rows = issued["separate_unadopted_Z180_square_end_markers"]
    assert len(marker_rows) == 8
    end_values = 0
    for row in marker_rows:
        ident, member = row["axis_id"], members[row["receiver"]]
        raw, axis = member["raw_profile_source"], proposed[ident]
        lower = raw["datum_xyz_mm"][2] + min(v[0] for v in raw["raw_profile_vertices_luv_mm"])
        upper = raw["datum_xyz_mm"][2] + max(v[0] for v in raw["raw_profile_vertices_luv_mm"])
        ylow = raw["datum_xyz_mm"][1] + min(v[2] for v in raw["raw_profile_vertices_luv_mm"])
        yhigh = raw["datum_xyz_mm"][1] + max(v[2] for v in raw["raw_profile_vertices_luv_mm"])
        near(row["negative_square_end_mm"], 180.-lower)
        if row["receiver"].startswith("eoere_cleat_"):
            assert row["positive_square_end_mm"] is None and row["sloping_cleat_upper_end_classified"] is False
            near(row["negative_square_end_mm"], 40.3)
        else:
            near(row["positive_square_end_mm"], upper-180.)
            near(row["positive_square_end_mm"], 58.9)
        edges = [axis["point_xyz_mm"][1]-ylow, yhigh-axis["point_xyz_mm"][1]]
        for a, b in zip(row["both_raw_crossgrain_edge_distances_mm"], edges, strict=True):
            near(a, b)
        near(row["minimum_raw_edge_minus_perpendicular_loaded4D_mm"], min(edges)-4*axis["diameter_mm"])
        for key, categories in row["square_end_markers"].items():
            for category, value in categories.items():
                low, full = (3.5, 7.) if category == "softwood_parallel_tension" else (2., 4.)
                distance, diameter = row[key], axis["diameter_mm"]
                near(value["actual_distance_mm"], distance)
                near(value["minimum_distance_mm"], low*diameter)
                near(value["full_value_distance_mm"], full*diameter)
                near(value["end_factor_only"], min(1., distance/(full*diameter)))
                assert value["complete_geometry_factor"] is None
                end_values += 1
        assert row["force_assigned_to_proposal"] is row["finished_net_section_or_fracture_qualified"] is False
        assert row["complete_Cdelta"] is None
    assert end_values == 36
    _, end = target.methods(dict(pins))
    for distance, category, expected in ((33.3375, "softwood_parallel_tension", .5), (66.675, "softwood_parallel_tension", 1.),
        (33., "softwood_parallel_tension", None), (19.05, "perpendicular", .5), (38.1, "parallel_compression", 1.), (18., "parallel_compression", None)):
        assert end(distance, 9.525, category)["end_factor_only"] == expected
    assert issued["inherited_source_closures_or_operator_arithmetic_reaudited"] is False
    assert issued["execution"]["current_Z200_actions_applied_to_Z180_proposal"] is False
    assert not any(issued["release"].values())
    with tempfile.TemporaryDirectory(prefix="replay-", dir=OWN.parent) as temp:
        output = Path(temp) / "result.json"
        command = [sys.executable, "-B", str(TARGET / "analyze.py"), "--out", str(output)]
        process = subprocess.run(command, cwd=ROOT, env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"}, capture_output=True, text=True, check=True)
        assert json.loads(process.stdout)["direct_sources"] == 26
        assert output.read_bytes() == (TARGET / "result.json").read_bytes()
        refused = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, check=False)
        assert refused.returncode != 0 and "preserve issued evidence" in refused.stderr
        assert output.read_bytes() == (TARGET / "result.json").read_bytes()
    assert {name: sha(TARGET / name) for name in HASHES} == HASHES
    for path, digest in pins.items():
        assert sha(ROOT / path) == digest
    return {"schema": "eoere_signed_end_inventory_independent_correctness_review/v1", "findings": [],
        "target_source_sha256": HASHES, "review_helper_sha256": sha(OWN), "direct_sources_rehashed": 26,
        "independent_checks": {"current_report_admission_identity_joins": 6, "current_Z200_wood_surfaces": surfaces,
            "independent_signed_X_shaft_vertical_grain_point_decompositions": point_count,
            "parallel_sign_reversal_surfaces": parallel_reversals, "crossgrain_sign_reversal_surfaces": cross_reversals,
            "zero_lateral_points": zero, "oblique_points": oblique, "separate_Z180_geometry_rows": 8,
            "separate_square_end_factors": end_values, "square_end_known_answers": 6,
            "byte_exact_CLI_replay": True, "occupied_output_preserved": True},
        "primary_source_review": {"path": target.NDS, "sha256": target.PINS[target.NDS],
            "pages_zero_based": [18, 19, 20, 21], "printed_pages": [97, 98, 99, 100],
            "reader": "uv run --no-project --with pypdf[crypto]==6.1.0 python; PdfReader.pages[18:22]",
            "checked": "NDS2024 12.5.1.2a-c, Tables12.5.1A-D and12.6; individual square-end ratios and entire-group/shear-plane minimum semantics only."},
        "limits": ["Existing current rich reports and issued admissions were source/identity checked; underlying admission/operator/reducer arithmetic was not independently re-audited.",
            "CurrentZ200 signed bearings remain separate from unadoptedZ180 raw square-end scenarios; no proposed force assignment or new capacity/admission.",
            "Sloping cleat top, oblique/finished edge rules, finished net/fracture/group/shear behavior and complete Cdelta/Cg remain unqualified.",
            "No CAD/native/global/new component solve, new field consumption, geometry adoption, physical observation or fabrication/climbing release.",
            "Frozen target/prior/source bytes preserved; only exclusive review helper/receipt retained."],
        "release": issued["release"]}


if __name__ == "__main__":
    receipt = main()
    destination = OWN.with_name("receipt.json")
    with destination.open("x") as stream:
        json.dump(receipt, stream, indent=2, sort_keys=True, allow_nan=False)
        stream.write("\n")
    print(json.dumps({"passed": True, "findings": receipt["findings"], "receipt_sha256": sha(destination),
        "checks": receipt["independent_checks"]}))
