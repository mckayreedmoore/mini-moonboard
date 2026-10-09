"""Independent source/fixture review and the one authorized pure v4 CLI replay."""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import math
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from unittest.mock import patch

OWN = Path(__file__).resolve()
D = OWN.parents[2]
ROOT = OWN.parents[9]
ISSUED = D / "runs-v1/attempt03/descriptor.json"
REPLAY = D / "runs-v1/review-testing01/descriptor.json"
V4 = D / "review-fix-v4/descriptor.py"
INPUT = V4.with_name("inputs.json")
INPUT_SHA = "a359cb1c7c3c30954d6e36204bd523cd0d565c10a9b78f9af09e6ddcbb66b6be"
EXPECTED = {
    D / "descriptor.py": "691f46fd47b2e952e3b8911d61ddf855d9806c20190f77a1d6e0f57ad022a9ac",
    D / "review-fix-v2/descriptor.py": "8ab67c15c544ba1cf1f0209020fb87614072c665a8eaa39dc667a23db5b2823a",
    D / "review-fix-v3/descriptor.py": "b9540ab1612033194c8ae7ac230ab21082813cd63cf824cc77b58cba9bfa6b1b",
    V4: "a7b27b82eb3bafc698d371ce2f4b2e71c89cc4306459cd795ed1ca1c983ae106",
    INPUT: INPUT_SHA,
    ISSUED: "e7a1a56f7c61119445c85f554d534abc5c43f77fede27a7fab42ad252bb275f0",
    D / "result.json": "3b8c2b7849573104a10ca1b0cf827bd9b0055c6edf3ee2ac91feaab88e3357d4",
}


def sha(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def canonical(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest()


def ref(path):
    return {"path": str(path.relative_to(ROOT)), "sha256": sha(path)}


def load(path, label):
    spec = importlib.util.spec_from_file_location(label, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def expect(error_type, action, message=None):
    try:
        action()
    except error_type as error:
        assert message is None or message in str(error), repr(error)
        return
    raise AssertionError(f"expected {error_type.__name__}")


def verify(pins):
    for path, digest in pins.items():
        assert sha(ROOT / path) == digest, f"source changed: {path}"


def verify_nested_refs(value):
    if isinstance(value, dict):
        if set(value) == {"path", "sha256"}:
            assert sha(ROOT / value["path"]) == value["sha256"], value
        for item in value.values():
            verify_nested_refs(item)
    elif isinstance(value, list):
        for item in value:
            verify_nested_refs(item)


def fixtures():
    fixed = load(V4, "independent_z180_v4_testing")
    v3 = fixed.verified_v3()
    v2 = v3.verified_v2()
    base = v2.frozen_module()
    checks = {}
    # Direct numerical integration of six translated cross-section moments,
    # independent of the descriptor's analytic antiderivatives.
    cy, cz, radius, low, high, count = 8., -9., 2.3, 7.3, 9.1, 4000
    totals = [0.] * 6
    for i in range(count + 1):
        y = low + (high - low) * i / count
        h = math.sqrt(radius * radius - (y - cy)**2)
        values = [2*h, 2*h*y, 2*h*cz, 2*h*y*y, 2*h*y*cz, 2*h*cz*cz + 2*h**3/3]
        weight = 1 if i in (0, count) else 4 if i % 2 else 2
        totals = [a + weight*b for a, b in zip(totals, values, strict=True)]
    integrated = [a * (high - low) / (3*count) for a in totals]
    analytic = base.disk_strip_moments(cy, cz, radius, low, high)
    assert all(abs(a-b) < 1e-9 for a, b in zip(analytic, integrated, strict=True))
    checks["all_six_offset_clipped_disk_moments_match_independent_Simpson_integration"] = True
    central = base.yz_central(base.cell_moments([-5., 5., -3., 3.], [(0., 0., 1.)]))
    expected = [[0., 0., 0.], [0., 500.-math.pi/4., 0.], [0., 0., 180.-math.pi/4.]]
    assert all(abs(a-b) < 1e-10 for row, want in zip(central, expected, strict=True) for a, b in zip(row, want, strict=True))
    checks["rectangle_minus_centered_disk_centroidal_second_moments_known_answer"] = True
    center = base.replace_centroid(1000., [2., 3., 10.], 1005., [(30., [60., 90., 450.])], [(25., [50., 75., 125.])])
    assert center == [2010./1005., 3015./1005., 10325./1005.]
    checks["unequal_volume_void_replacement_divides_by_new_volume_and_retains_signed_first_moments"] = True

    with tempfile.TemporaryDirectory(prefix="pure-fixtures-", dir=OWN.parent) as directory:
        temp = Path(directory)
        changed = temp / "untrusted.py"
        changed.write_text("raise AssertionError('untrusted source executed')\n")
        for module, field, action in ((fixed, "V3", fixed.verified_v3), (v3, "V2", v3.verified_v2), (v2, "FROZEN", v2.frozen_module)):
            with patch.object(module, field, changed):
                expect(ValueError, action, "bytes differ")
        checks["all_three_frozen_compiler_layers_reject_tamper_before_execution"] = True

        own = temp / "packet/descriptor.py"
        outside = temp / "outside.json"
        with patch.object(base, "OWN", own), patch.object(base, "load_inputs", side_effect=AssertionError("intake reached")):
            expect(ValueError, lambda: base.write_descriptor("unused", "unused", outside), "runs-v1")
        assert not outside.exists()
        checks["foreign_output_parent_rejected_before_intake"] = True

        out = own.parent / "runs-v1/nonfinite.json"
        with patch.object(base, "OWN", own), patch.object(base, "ROOT", temp), \
             patch.object(base, "load_inputs", return_value={"source_sha256": {}, "root": temp}), \
             patch.object(base, "build_descriptor", return_value={"release": base.RELEASE, "value": float("nan")}), patch.object(base, "verify"):
            expect(ValueError, lambda: base.write_descriptor("unused", "unused", out))
        failure = json.loads(out.read_bytes())
        assert failure["status"] == "FAILED" and failure["accepted_response"] is None and failure["release"] == base.RELEASE
        retained = out.read_bytes()
        with patch.object(base, "OWN", own), patch.object(base, "load_inputs", side_effect=AssertionError("retained attempt reused")):
            expect(FileExistsError, lambda: base.write_descriptor("unused", "unused", out))
        assert out.read_bytes() == retained
        checks["nonfinite_synthetic_output_retains_unreleased_failure_and_cannot_be_reused"] = True

        out = own.parent / "runs-v1/replaced.json"
        def replace_reserved(*_args, **_kwargs):
            replacement = out.with_name("replacement.json")
            replacement.write_bytes(b"replacement preserved\n")
            os.replace(replacement, out)
            raise RuntimeError("synthetic producer interrupted after path replacement")
        with patch.object(base, "OWN", own), patch.object(base, "load_inputs", side_effect=replace_reserved):
            expect(ValueError, lambda: base.write_descriptor("unused", "unused", out), "reserved output identity changed")
        assert out.read_bytes() == b"replacement preserved\n"
        checks["replaced_reserved_inode_is_never_overwritten_by_failure_record"] = True

    helper = load(V4.with_name("test_descriptor.py"), "independent_z180_existing_mixed_fixture")
    current = helper.mixed_fixture()
    view = copy.deepcopy(current)
    view["direct_contacts"][-1]["stiffness"] += 1.
    expect(ValueError, lambda: fixed.verified_patch_contacts(view, current, {}), "contact primitives changed")
    current["direct_contacts"][-1]["source_domain_id"] = current["flange_domains"][0]["id"]
    expect(ValueError, lambda: fixed.verified_patch_contacts(copy.deepcopy(current), current, {}), "original own domain/cell")
    checks["mixed_schema_rejects_preupdate_drift_and_existing_but_foreign_flange_domain"] = True
    assert "cadquery" not in sys.modules and "numpy" not in sys.modules
    assert not any(name == "OCP" or name.startswith("OCP.") for name in sys.modules)
    checks["fixture_process_imported_no_CAD_numpy_or_mechanics"] = True
    return checks


def compact_checks(issued, compact):
    proof = issued["geometry_delta_proof"]
    assert compact["descriptor"] == ref(ISSUED) and compact["descriptor_bytes"] == ISSUED.stat().st_size == 6092178
    assert compact["counts"] == proof["counts"] and compact["contact_reuse"] == issued["mixed_contact_source_contract"]
    assert compact["byte_identical_descriptor_fields"] == proof["byte_identical_descriptor_fields"]
    assert compact["changed_host_inherited_regions"] == proof["changed_host_inherited_regions"]
    assert compact["source_corrections"] == issued["descriptor_source_corrections"]
    assert compact["consumed_source_pins"] == len(issued["source_sha256"]) == 1116
    assert compact["source_closure_canonical_sha256"] == canonical(issued["source_sha256"])
    assert compact["release"] == issued["release"] and all(v is False for v in issued["release"].values())
    assert compact["complete_joint_resistance"] is issued["complete_joint_resistance"] is None
    for key in ("force_execution_readiness_claimed", "historical_q_forces_operators_or_acceptance_transferred",
                "native_CAD_BREP_import_K_panel_preparation_response_or_solve_performed"):
        assert compact[key] is issued[key] is False
    assert compact["original_4in_hardware_retained_spacer_proposal_excluded"] is issued["current_4in_hardware_retained_spacer_proposal_excluded"] is True
    assert compact["frozen_geometry"] == issued["geometry"] and compact["parent_geometry"] == issued["parent_geometry"]
    assert compact["parent_descriptors"] == issued["parent_descriptors"] and compact["source_only_parent_manifest"] == issued["manifest"]
    floors = [r for r in issued["floor_observations"] if "inherited_floor_observation" in r]
    assert compact["changed_host_inherited_floor_observations"] == floors
    assert sorted(r["host"] for r in floors) == sorted(proof["changed_host_inherited_floor_regions"])
    for host, summary in compact["COM"].items():
        own = proof["COM"][host]
        for key in ("new_center_xyz_mm", "new_volume_mm3", "old_center_xyz_mm", "old_volume_mm3"):
            assert summary[key] == own[key]
        assert summary["center_delta_xyz_mm"] == [a-b for a, b in zip(own["new_center_xyz_mm"], own["old_center_xyz_mm"], strict=True)]
        assert summary["native_COM_query_performed"] is own["new_native_COM_query_performed"] is False
        assert summary["new_native_receiver_evidence"] == own["saved_native_receiver_evidence"]
        assert summary["old_COM_source"] == own["old_COM_observation_source"]
    parent = json.loads((ROOT / compact["parent_descriptors"]["path"]).read_bytes())
    before = {p["id"]: p for p in parent["timber_and_panel_shared_face_patches"]}
    after = {p["id"]: p for p in issued["timber_and_panel_shared_face_patches"]}
    patches = {p["id"]: p for p in proof["rebuilt_patches"]}
    for summary in compact["rebuilt_contact_patches"]:
        identity = summary["id"]
        assert all(summary[key] == value for key, value in patches[identity].items())
        for prefix, source in (("old", before[identity]), ("new", after[identity])):
            assert summary[prefix+"_area_mm2"] == source["area_mm2"]
            assert summary[prefix+"_center_xyz_mm"] == source["centroid_xyz_mm"]
        assert summary["analytic_source_region_sha256"] == after[identity]["analytic_source_region_sha256"]
    for key, field in (("flange_domains", "flange_domains"), ("flange_patches", "flange_shared_face_patches")):
        assert compact[key+"_canonical_sha256_before_and_after"] == canonical(parent[field]) == canonical(issued[field])
    rows_before = [r for r in parent["direct_contacts"] if r["kind"] == "flange_contact"]
    rows_after = [r for r in issued["direct_contacts"] if r["kind"] == "flange_contact"]
    assert compact["flange_rows_canonical_sha256_before_and_after"] == canonical(rows_before) == canonical(rows_after)
    maximum = max(p["second_moment_relative_frobenius_error"] for key in
                  ("timber_and_panel_shared_face_patches", "flange_shared_face_patches") for p in issued[key])
    assert compact["sampling_limit"]["maximum_sampled_second_moment_relative_frobenius_error"] == maximum
    verify_nested_refs(compact)
    return {"compact_claims_match_exact_issued_descriptor": True, "compact_nested_refs_exact": True,
            "compact_COM_contacts_floor_and_sampling_claims_join_issued_proofs": True}


def main():
    if "--fixtures" in sys.argv:
        print(json.dumps(fixtures(), sort_keys=True))
        return
    start = time.monotonic()
    verify_existing = "--verify-existing-replay" in sys.argv
    previous = json.loads(OWN.with_name("receipt.json").read_bytes()) if verify_existing else None
    if verify_existing:
        assert previous["one_authorized_pure_CLI_replay"]["replay_attempts"] == 1
        assert previous["one_authorized_pure_CLI_replay"]["output"] == ref(REPLAY)
        assert sha(REPLAY) == EXPECTED[ISSUED]
    else:
        assert not REPLAY.exists() and not REPLAY.is_symlink(), "the single authorized replay path must be fresh"
    fixed = {str(path.relative_to(ROOT)): digest for path, digest in EXPECTED.items()}
    verify(fixed)
    issued = json.loads(ISSUED.read_bytes())
    compact = json.loads((D / "result.json").read_bytes())
    pins = issued["source_sha256"]
    assert len(pins) == 1116
    verify(pins)
    environment = dict(os.environ, PYTHONPATH=str(ROOT))
    test_paths = [D / "test_descriptor.py", *[D / directory / "test_descriptor.py" for directory in
                  ("review-fix-v2", "review-fix-v3", "review-fix-v4")]]
    test_command = [sys.executable, "-B", "-m", "pytest", "--import-mode=importlib", "-q", "-p", "no:cacheprovider",
                    *[str(path.relative_to(ROOT)) for path in test_paths]]
    tests = subprocess.run(test_command, cwd=ROOT, env=environment, capture_output=True, text=True, check=False, timeout=30)
    assert tests.returncode == 0, tests.stdout + tests.stderr
    fixture_run = subprocess.run([sys.executable, "-B", str(OWN), "--fixtures"], cwd=ROOT, env=environment, capture_output=True, text=True, check=False, timeout=30)
    assert fixture_run.returncode == 0, fixture_run.stdout + fixture_run.stderr
    fixture_result = json.loads(fixture_run.stdout)
    compact_result = compact_checks(issued, compact)
    lint_command = [sys.executable, "-B", "-m", "ruff", "check", str((D / "descriptor.py").relative_to(ROOT)),
                    str((D / "test_descriptor.py").relative_to(ROOT)),
                    *[str((D / directory).relative_to(ROOT)) for directory in ("review-fix-v2", "review-fix-v3", "review-fix-v4")],
                    str(OWN.relative_to(ROOT))]
    lint = subprocess.run(lint_command, cwd=ROOT, env=environment, capture_output=True, text=True, check=False, timeout=30)
    assert lint.returncode == 0, lint.stdout + lint.stderr
    verify(pins)
    verify(fixed)
    command = [sys.executable, "-B", str(V4.relative_to(ROOT)), "--inputs", str(INPUT.relative_to(ROOT)),
               "--inputs-sha256", INPUT_SHA, "--out", str(REPLAY.relative_to(ROOT))]
    # Exactly one genuine source-only CLI replay. A later verification only
    # authenticates the retained replay and its saved command; it never retries.
    if verify_existing:
        replay_record = previous["one_authorized_pure_CLI_replay"]
        assert replay_record["command"] == command
    else:
        replay = subprocess.run(command, cwd=ROOT, env=environment, capture_output=True, text=True, check=False, timeout=30)
        replay_record = {"command": command, "exit_code": replay.returncode, "stdout": replay.stdout.strip(),
                         "stderr": replay.stderr, "output": ref(REPLAY), "bytes": REPLAY.stat().st_size,
                         "exact_issued_bytes_equal": REPLAY.read_bytes() == ISSUED.read_bytes(), "replay_attempts": 1}
    success = replay_record["exit_code"] == 0 and REPLAY.read_bytes() == ISSUED.read_bytes()
    verify(pins)
    verify(fixed)
    receipt = {"schema": "eoere_z180_geometry_descriptors_independent_review/v1",
        "independent_z180_descriptor_source_checks_pass": success, "reviewer": "/root/intake_final_testing",
        "scope": "testing; frozen source-only Z180 descriptors and compact result only", "branch": "master",
        "descriptor": ref(ISSUED), "compact_result": ref(D / "result.json"), "source_sha256": fixed,
        "review_source": ref(OWN), "source_closure": {"pins_before_and_after": 1116, "all_bytes_unchanged": True,
            "canonical_sha256": canonical(pins), "absolute_path_spellings_preserved": [p for p in pins if Path(p).is_absolute()]},
        "tests": {"command": test_command, "result": tests.stdout.strip()}, "pure_fixture_checks": fixture_result,
        "ruff": {"command": lint_command, "result": lint.stdout.strip()},
        "compact_result_checks": compact_result,
        "one_authorized_pure_CLI_replay": replay_record, "this_verification_reused_retained_replay": verify_existing,
        "findings": [] if success else [{"impact": "authorized replay differs from exact issued descriptor", "fix": "parent must investigate retained replay; no retry performed"}],
        "release": issued["release"], "all_release_flags_false": all(v is False for v in issued["release"].values()),
        "native_CAD_BREP_query_K_panel_preparation_candidate_inputs_q_forces_solve_or_browser_performed": False,
        "complete_joint_resistance": None, "force_execution_readiness_claimed": False,
        "limits": ["Source-only unadopted geometry descriptors; no candidate readiness, adoption, resistance or acceptance follows.",
                   "Inherited saved native receiver evidence is authenticated by bytes only; no native query was repeated.",
                   "Exact area moments and sampled centroid quadrature remain separate; pressure, rocking and physical applicability remain unresolved.",
                   "Only one pure v4 CLI replay was authorized and executed. Issued descriptors, failures and all frozen sources remain unchanged."],
        "elapsed_seconds": time.monotonic() - start}
    OWN.with_name("receipt.json").write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"pass": success, "tests": tests.stdout.strip(), "pure_controls": len(fixture_result), "replay_sha256": sha(REPLAY)}))
    assert success, "retained replay failed or differs"


if __name__ == "__main__":
    main()
