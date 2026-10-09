"""Bounded testing of saved signed census and separate square-end scenarios."""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import math
import subprocess
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

sys.dont_write_bytecode = True
OWN = Path(__file__).resolve().parent
ROOT = next(p for p in OWN.parents if (p/"AGENTS.md").is_file())
TARGET = ROOT/"fea/generated/thin-bolted-current-contact-v1/eoere-successor-v1/cleat-remedy-v1/current-source-followup-v1/end-geometry-v1"
EXPECTED = {"analyze.py": "fc45c5e990b11c20a3e6e98e9723b25ec366d05a780b229d82cdb639c6dc4ad0", "result.json": "4c66a7f194a747a14291e25c4277ec7288aa95a9bef9eab68233312288e9be9b"}


def sha(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for chunk in iter(lambda: f.read(1048576), b""):
            h.update(chunk)
    return h.hexdigest()


def read(path):
    return json.loads(Path(path).read_bytes())


def load(path):
    spec = importlib.util.spec_from_file_location("frozen_end_inventory", path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def rejects(fn, expected=None):
    try:
        fn()
    except (ValueError, FileExistsError, KeyError) as error:
        assert expected is None or expected in str(error), (expected, str(error))
        return str(error)
    raise AssertionError("invalid fixture accepted")


def near(a, b, tol=1e-10):
    assert math.isfinite(a) and math.isfinite(b) and abs(a-b) < tol, (a, b)


def main():
    assert not (OWN/"receipt-v2.json").exists(), "do not overwrite review evidence"
    preserved_v1 = {'review.py': 'd843f6a9a7da351a7bac42d6eead7c8af84a24c2dc8e1f612f637e03089c3f39', 'receipt.json': '0c7d9c09480f7a250ce4f7a7ea42e3616a8f90db8bde77387a86778f21786c24'}
    assert {n: sha(OWN/n) for n in preserved_v1} == preserved_v1
    assert {n: sha(TARGET/n) for n in EXPECTED} == EXPECTED
    m = load(TARGET/"analyze.py")
    record = read(TARGET/"result.json")
    pins = record["source_sha256"]
    assert len(pins) == 26
    for path, expected in pins.items():
        assert sha(ROOT/path) == expected, path
    summary, source, placement = [read(ROOT/path) for path in (m.SUMMARY, m.INPUT, m.PLACEMENT)]
    geometry_ref = summary["geometry"]["report"]
    geometry = read(ROOT/geometry_ref["path"])
    assert len(geometry["axes"]) == len(source["shafts"]) == 100 and len(source["hillman_rows"]) == 66
    shafts = {r["axis_id"]: r for r in source["shafts"]}
    members = {r["name"]: r for r in source["timber_rows"]}
    axes = {r["id"]: r for r in geometry["axes"]}
    proposed = {r["id"]: r for r in placement["proposed_axes"]}
    surfaces = {(aid, h) for aid in m.IDS for h in axes[aid]["receivers"]}
    assert len(surfaces) == 8
    reports, extracted = {}, record["current_Z200_inventory"]
    nonzero_angles, parallel_count, cross_count, zero_count, oblique_count = [], 0, 0, 0, 0
    for saved, case in zip(extracted["cases"], summary["cases"], strict=True):
        report = read(ROOT/case["rich"]["result"]["path"])
        reports[case["rich"]["result"]["path"]] = report
        assert saved["case_id"] == case["case_id"] == report["case_id"]
        assert saved["state_id"] == report["state_id"] and saved["report"] == case["rich"]["result"]
        assert {(r["axis_id"], r["receiver"]) for r in saved["current_Z200_surfaces"]} == surfaces
        source_rows = {(r["axis_id"], r["receiver"]): r for r in report["findings"]["timber"]["wood_surfaces"] if r["axis_id"] in m.IDS}
        for row in saved["current_Z200_surfaces"]:
            aid = row["axis_id"]
            assert row["current_axis_Z_mm"] == shafts[aid]["point"][2] == axes[aid]["point_xyz_mm"][2] == 200
            signed_points = [p for p in source_rows[aid, row["receiver"]]["own_point_actions"] if p["kind"] == "common_shaft_bearing"]
            assert len(signed_points) == len(row["own_bearings"]) == 2
            for saved_point, point in zip(row["own_bearings"], signed_points, strict=True):
                signed = point["signed_components"]
                assert saved_point["id"] == point["id"] and saved_point["point_xyz_mm"] == point["point_xyz_mm"]
                assert point["id"].startswith(aid+"/bearing-") and point["point_xyz_mm"][2] == 200
                force = signed["force_on_receiver_xyz_n"]
                assert saved_point["force_on_receiver_xyz_n"] == force
                assert members[row["receiver"]]["axis"] == [0., 0., 1.]
                direction = shafts[aid]["basis"][0][0]
                assert direction in (-1, 1) and shafts[aid]["basis"][0][1:] == [0., 0.]
                # For grain +Z and shaft +/-X, cross-grain direction is +/-Y.
                parallel, transverse = force[2], direction*force[1]
                near(saved_point["parallel_grain_signed_n"], parallel)
                near(saved_point["cross_grain_signed_n"], transverse)
                magnitude = math.hypot(force[1], force[2])
                threshold = 1e-10*max(magnitude, 1)
                theta = None if magnitude < threshold else math.degrees(math.atan2(abs(transverse), abs(parallel)))
                if theta is None:
                    assert saved_point["load_to_grain_degrees"] is None
                    zero_count += 1
                else:
                    near(saved_point["load_to_grain_degrees"], theta)
                    nonzero_angles.append(theta)
                oblique = abs(parallel) >= threshold and abs(transverse) >= threshold
                assert saved_point["oblique_lateral_action"] is oblique
                oblique_count += oblique
            parallel = [r["parallel_grain_signed_n"] for r in row["own_bearings"]]
            transverse = [r["cross_grain_signed_n"] for r in row["own_bearings"]]
            reversal, cross_reversal = min(parallel) < 0 < max(parallel), min(transverse) < 0 < max(transverse)
            assert row["bearing_parallel_sign_reversal"] is reversal and row["bearing_crossgrain_sign_reversal"] is cross_reversal
            parallel_count += reversal
            cross_count += cross_reversal
    assert (extracted["case_count"], extracted["wood_surface_count"], extracted["bearing_point_count"]) == (6, 48, 96)
    assert parallel_count == extracted["parallel_sign_reversal_surface_count"] == 39
    assert cross_count == extracted["crossgrain_sign_reversal_surface_count"] == 43
    assert zero_count == extracted["zero_lateral_bearing_points"] == 5
    assert oblique_count == extracted["oblique_bearing_points"] == 91
    assert extracted["nonzero_bearing_angle_range_deg"] == [min(nonzero_angles), max(nonzero_angles)]
    markers = record["separate_unadopted_Z180_square_end_markers"]
    assert {(r["axis_id"], r["receiver"]) for r in markers} == surfaces and len(markers) == 8
    for row in markers:
        assert row["proposed_point_xyz_mm"] == proposed[row["axis_id"]]["point_xyz_mm"] and row["proposed_point_xyz_mm"][2] == 180
        cleat = row["receiver"].startswith("eoere_cleat_")
        near(row["negative_square_end_mm"], 40.3 if cleat else 180)
        if cleat:
            assert row["positive_square_end_mm"] is None and row["sloping_cleat_upper_end_classified"] is False
        else:
            near(row["positive_square_end_mm"], 58.9)
        assert sorted(round(d, 8) for d in row["both_raw_crossgrain_edge_distances_mm"]) == [44.45, 95.25]
        near(row["minimum_raw_edge_minus_perpendicular_loaded4D_mm"], 6.35)
        for label, categories in row["square_end_markers"].items():
            distance = row[label]
            for category, value in categories.items():
                full = 7*9.525 if category == "softwood_parallel_tension" else 4*9.525
                near(value["end_factor_only"], min(1, distance/full))
                assert value["complete_geometry_factor"] is None
        assert row["force_assigned_to_proposal"] is False and row["complete_Cdelta"] is None
        assert row["finished_net_section_or_fracture_qualified"] is False
    assert all(v is False for v in record["release"].values())
    assert record["execution"]["current_Z200_actions_applied_to_Z180_proposal"] is False
    assert record["inherited_source_closures_or_operator_arithmetic_reaudited"] is False

    # Authenticate actual sources separately; semantic controls use small memory-only
    # fixtures and intentionally bypass byte gates to reach downstream branches.
    fixture_source = {
        "shafts": [{k: v for k, v in r.items() if k in ("axis_id", "source_axis", "basis", "point", "surfaces")} if r["axis_id"] in m.IDS else {"axis_id": r["axis_id"]} for r in source["shafts"]],
        "timber_rows": [{k: v for k, v in r.items() if k in ("name", "axis", "raw_profile_source")} if r["name"] in {x[1] for x in surfaces} else {"name": r["name"]} for r in source["timber_rows"]],
        "hillman_rows": [{} for _ in range(66)],
    }
    small_reports = {}
    for path, report in reports.items():
        small = {k: report[k] for k in ("case_id", "state_id", "current_geometry", "raw_field_sha256", "field_admission_receipt_sha256", "complete_joint_resistance", "release")}
        small["findings"] = {"timber": {"wood_surfaces": [r for r in report["findings"]["timber"]["wood_surfaces"] if r["axis_id"] in m.IDS]}}
        small_reports[path] = small
    fixture = {m.SUMMARY: summary, m.INPUT: fixture_source, m.PLACEMENT: placement, geometry_ref["path"]: {"axes": [None]*100}, **small_reports}
    method_bytes = (ROOT/m.METHOD).read_bytes()
    original_checked = m.checked
    def run_fixture(value):
        def memory_checked(path, expected, bound):
            bound[path] = expected
            if path == m.METHOD:
                return method_bytes
            return json.dumps(value[path]).encode() if path in value else b"authenticated byte-gate fixture"
        with patch.object(m, "checked", memory_checked):
            return m.build()
    assert run_fixture(fixture)["current_Z200_inventory"] == extracted
    report_path = summary["cases"][0]["rich"]["result"]["path"]
    def report_rows(f):
        return f[report_path]["findings"]["timber"]["wood_surfaces"]
    mutations = {
        "wrong_case_roster": lambda f: f[m.SUMMARY]["cases"].reverse(),
        "missing_geometry_axis": lambda f: f[geometry_ref["path"]]["axes"].pop(),
        "duplicate_source_owner": lambda f: f[m.INPUT]["shafts"].__setitem__(0, copy.deepcopy(f[m.INPUT]["shafts"][1])),
        "wrong_screw_census": lambda f: f[m.INPUT]["hillman_rows"].pop(),
        "adopted_proposal": lambda f: f[m.PLACEMENT].update(geometry_adopted=True),
        "wrong_proposal_z": lambda f: f[m.PLACEMENT]["proposed_axes"][0]["point_xyz_mm"].__setitem__(2, 190),
        "nonwood_stack": lambda f: next(r for r in f[m.INPUT]["shafts"] if r["axis_id"] in m.IDS)["surfaces"][0].update(kind="steel"),
        "wrong_report_case": lambda f: f[report_path].update(case_id="old-case"),
        "wrong_field_join": lambda f: f[report_path].update(raw_field_sha256="0"*64),
        "wrong_admission_join": lambda f: f[report_path].update(field_admission_receipt_sha256="0"*64),
        "capacity_claim": lambda f: f[report_path].update(complete_joint_resistance=1),
        "release_claim": lambda f: f[report_path]["release"].update(climbing=True),
        "missing_surface": lambda f: report_rows(f).pop(),
        "duplicate_surface": lambda f: report_rows(f).__setitem__(0, copy.deepcopy(report_rows(f)[1])),
        "duplicate_bearing_id": lambda f: report_rows(f)[0]["own_point_actions"][0].update(id=report_rows(f)[0]["own_point_actions"][1]["id"]),
        "signed_force_mismatch": lambda f: report_rows(f)[0]["own_point_actions"][0]["signed_components"]["force_on_receiver_xyz_n"].__setitem__(2, 1),
        "sign_reversal_claim": lambda f: report_rows(f)[0].update(bearing_parallel_sign_reversal=not report_rows(f)[0]["bearing_parallel_sign_reversal"]),
        "complete_Cdelta_claim": lambda f: report_rows(f)[0].update(complete_Cdelta=1),
        "complete_Cg_claim": lambda f: report_rows(f)[0].update(complete_Cg=1),
        "nonvertical_profile": lambda f: next(r for r in f[m.INPUT]["timber_rows"] if r["name"] == "eoere_cleat_left")["raw_profile_source"]["basis_grain_u_v_xyz"].__setitem__(0, [1, 0, 0]),
        "oblique_post_end": lambda f: next(r for r in f[m.INPUT]["timber_rows"] if r["name"] == "base_post_outer_left")["raw_profile_source"]["end_cut_planes"][0].update(normal_to_nominal_grain_deg=1),
        "grain_parallel_to_shaft": lambda f: next(r for r in f[m.INPUT]["timber_rows"] if r["name"] == "eoere_cleat_left").update(axis=[1, 0, 0]),
    }
    controls = []
    for name, mutate in mutations.items():
        candidate = copy.deepcopy(fixture)
        mutate(candidate)
        controls.append({"name": name, "rejection": rejects(lambda candidate=candidate: run_fixture(candidate))})
    original_checked("scripts/thin_bolted_timber_resistance.py", m.PINS[m.METHOD], {})
    source_controls = []
    for path, expected, bound, reason in [(m.METHOD, "0"*64, {}, "source changed"), ("../AGENTS.md", "0"*64, {}, "repository-relative"), (str(ROOT/"AGENTS.md"), "0"*64, {}, "repository-relative"), (m.METHOD, m.PINS[m.METHOD], {m.METHOD: "0"*64}, "conflicting direct pin")]:
        source_controls.append(rejects(lambda path=path, expected=expected, bound=bound: original_checked(path, expected, bound), reason))
    resolved, end = m.methods({})
    direction_fixtures = 0
    for sx in (-1, 1):
        for y, z in ((3, 4), (-3, 4), (3, -4), (-3, -4), (0, 0)):
            answer = resolved([5, y, z], [0, 0, 1], [sx, 0, 0])
            assert answer["parallel_grain_signed_n"] == z and answer["cross_grain_signed_n"] == sx*y
            assert answer["axial_signed_n"] == sx*5
            direction_fixtures += 1
    rejects(lambda: resolved([1, 2, 3], [1, 0, 0], [1, 0, 0]), "different method")
    rejects(lambda: resolved([1, 2, float("nan")], [0, 0, 1], [1, 0, 0]), "finite numbers")
    rejects(lambda: end(-1, 9.525, "perpendicular"), "nonnegative")
    rejects(lambda: end(40, 0, "perpendicular"), "positive")
    rejects(lambda: end(40, 9.525, "oblique"), "unclassified")
    end_fixtures = 0
    for category, minimum, full in (("softwood_parallel_tension", 3.5*9.525, 7*9.525), ("parallel_compression", 2*9.525, 4*9.525), ("perpendicular", 2*9.525, 4*9.525)):
        for distance, expected in ((minimum-.001, None), (minimum, .5), (full, 1.), (full+1, 1.)):
            assert end(distance, 9.525, category)["end_factor_only"] == expected
            end_fixtures += 1

    with tempfile.TemporaryDirectory(prefix="end-inventory-review-") as temporary:
        temp = Path(temporary)
        out = temp/"replay.json"
        p = subprocess.run([sys.executable, "-B", str(TARGET/"analyze.py"), "--out", str(out)], cwd=ROOT, capture_output=True, text=True, timeout=120, check=False)
        assert p.returncode == 0, p.stderr
        assert sha(out) == EXPECTED["result.json"]
        # Existing output is rejected before build, and an intervening writer is
        # preserved by exclusive open; no current source bytes are modified.
        with patch.object(sys, "argv", [str(TARGET/"analyze.py"), "--out", str(out)]), patch.object(m, "build", side_effect=AssertionError("build after occupied output")):
            rejects(m.main, "preserve issued evidence")
        race = temp/"race.json"
        def late_writer():
            race.write_bytes(b"other writer\n")
            return record
        with patch.object(sys, "argv", [str(TARGET/"analyze.py"), "--out", str(race)]), patch.object(m, "build", late_writer):
            rejects(m.main)
        assert race.read_bytes() == b"other writer\n"
        failed = temp/"failed.json"
        with patch.object(sys, "argv", [str(TARGET/"analyze.py"), "--out", str(failed)]), patch.object(m, "build", side_effect=ValueError("controlled source failure")):
            rejects(m.main, "controlled source failure")
        assert not failed.exists()
        ruff = subprocess.run([str(ROOT/".venv/bin/ruff"), "check", "--no-cache", str(TARGET/"analyze.py")], cwd=ROOT, capture_output=True, text=True, check=False)
        assert ruff.returncode == 0, ruff.stdout+ruff.stderr
    assert {n: sha(TARGET/n) for n in EXPECTED} == EXPECTED
    for path, expected in pins.items():
        assert sha(ROOT/path) == expected, path
    assert not any(k in sys.modules for k in ("cadquery", "OCP"))
    own_ruff = subprocess.run([str(ROOT/".venv/bin/ruff"), "check", "--no-cache", str(Path(__file__))], cwd=ROOT, capture_output=True, text=True, check=False)
    assert own_ruff.returncode == 0, own_ruff.stdout+own_ruff.stderr
    assert {n: sha(OWN/n) for n in preserved_v1} == preserved_v1
    receipt = {
        "schema": "eoere_signed_end_inventory_independent_testing_review/v1", "passed": True, "substantial_findings": [],
        "reviewer_ruff_no_cache": True, "preserved_v1_review_records_sha256": preserved_v1,
        "target": {"path": str(TARGET.relative_to(ROOT)), "sha256": EXPECTED}, "reviewer_sha256": sha(__file__),
        "direct_source_pins_checked_before_after": 26, "target_and_all_direct_bytes_unchanged": True,
        "independent_saved_inventory_checks": {k: v for k, v in extracted.items() if k != "cases"},
        "proposed_geometry_only_markers_checked": 8, "own_source_surface_and_bearing_identity_checks": True,
        "semantic_in_memory_controls": controls, "memory_fixture_hash_gate_bypass_is_not_an_admission": True,
        "source_hash_path_and_pin_conflict_controls": source_controls, "direction_fixtures": direction_fixtures,
        "end_boundary_fixtures": end_fixtures, "invalid_helper_input_controls": 5,
        "genuine_CLI_exact_byte_replay": True, "output_controls": ["occupied_output_before_build", "late_writer_preserved", "build_failure_no_output"], "control_outputs_in_tmp_removed": True,
        "ruff_frozen_helper_no_cache": True, "release": record["release"],
        "limits": ["This review authenticates/extracts existing six-case signed reports; existing field admissions and reducer/operator arithmetic are not independently re-audited.", "The96 current Z200 bearings remain separate from eight Z180 geometry-only endpoint rows; no proposal forces, complete Cdelta/Cg or resistance is assigned.", "Classified square-end factors remain scenarios; sloping cleat top, finished void ligaments, group/edge/fracture resistance and actual installation remain unqualified.", "No CAD/BREP/native/global/component solve, genuine field consumption, model adoption, physical work, shared edits, staging or commits occurred."],
    }
    with (OWN/"receipt-v2.json").open("x") as handle:
        json.dump(receipt, handle, indent=2, sort_keys=True, allow_nan=False)
        handle.write("\n")
    print(json.dumps({"passed": True, "findings": 0, "receipt_sha256": sha(OWN/"receipt-v2.json")}))


if __name__ == "__main__":
    main()
