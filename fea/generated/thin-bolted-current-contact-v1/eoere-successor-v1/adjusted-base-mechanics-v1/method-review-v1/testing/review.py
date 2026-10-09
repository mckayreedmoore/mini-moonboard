"""Independent source/synthetic testing review. Never execute real extraction or K loading."""
from __future__ import annotations

import argparse
import concurrent.futures
import copy
import hashlib
import importlib.util
import io
import json
import os
import platform
import subprocess
import sys
import tempfile
import threading
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

sys.dont_write_bytecode = True
ROOT = Path.cwd()
RAW = ROOT / "fea/generated/thin-bolted-current-contact-v1/eoere-successor-v1/adjusted-base-mechanics-v1"
OWN = Path(__file__).resolve()
INTAKE = RAW / "extended-cleat-intake-v1"
PANEL = RAW / "current-panel-bank-v1"
AUTHORITY = RAW / "parent-authority-v1"


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read(path):
    return json.loads(Path(path).read_bytes())


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def verify(pins):
    for path, digest in pins.items():
        require(sha(ROOT / path) == digest, "changed source: " + path)


def rejected(operation, error_type):
    try:
        operation()
    except error_type:
        return
    raise ValueError("negative control did not reject")


def source_checks(x, m):
    manifest = AUTHORITY / "extended-cleat-manifest.json"
    digest = "458a7f0220e5776fdb53b876b9815715bf278c5b22eea7699824a9919dd6bfe6"
    prepared = x.prepare(manifest, digest)
    p, old, report, panels, pins = prepared
    plan = x.source_plan(manifest, digest)
    require(len(pins) == 1076, "extended intake source closure count")
    require(len(report["finished_solids"]) == 22 and len(panels) == 6, "twenty-eight sources")
    require((len(p["physical_owner_gravity_descriptors"]), len(p["shaft_descriptors"]), len(p["fitting_ports"]), len(p["hillman_rows"])) == (150, 100, 88, 66), "current source census")
    require(plan["candidate_K_q_forces_or_acceptance"] is None and plan["native_queries_deferred"] is True, "source-only plan boundary")
    require(plan["serial_slot_API"]["approved_manifest_sha256"] == digest, "exact manifest slot contract")
    source_inputs = m.source_inputs()
    panel_plan, prior, current, moved, panel_pins = m.read_sources()
    require(len(panel_pins) == 840, "panel source closure count")
    require(source_inputs == m.input_record(panel_plan, current, moved), "source inputs exact")
    require(current["panel_machining"] == p["current_panel_machining_descriptors"], "current intake/panel aperture seam")
    require(current["screw_axes"] == [r["source_screw_descriptor"] for r in p["hillman_rows"]], "current intake/panel sixty-six screw seam")
    sources = {r["id"]: m.source_binding(r) for r in panels}
    require(sources == {r["id"]: r for r in current["finished_panel_solids"]}, "current six panel source seam")
    data = {"geometry": copy.deepcopy(x.GEOMETRY), "panel_ids": list(m.plate.PANELS), "panel_operator_source_inputs": source_inputs,
            "current_panel_machining_descriptors": copy.deepcopy(p["current_panel_machining_descriptors"]),
            "hillman_rows": copy.deepcopy(p["hillman_rows"]), "source_sha256": copy.deepcopy(pins)}
    admission = m.verify_panel_source_inputs(data)
    require(admission["metadata_only_no_K_q_or_contact_construction"], "metadata admission")
    bad = copy.deepcopy(data)
    bad["panel_operator_source_inputs"]["optional_2026_extra"] = True
    rejected(lambda: m.verify_panel_source_inputs(bad), ValueError)
    rejected(lambda: m.prepare_panel_operators(data), KeyError)
    return {"intake_pins": len(pins), "panel_pins": len(panel_pins), "current_intake_panel_metadata_seam_matches": True,
            "optional_extra_ON_source_inputs_rejected": True, "missing_observations_reject_before_bank_loading": True,
            "intake_inventory": {"finished_timber_sources": len(report["finished_solids"]), "panels": len(panels), "physical_owners": 150, "shafts": 100, "ports": 88, "screws": 66},
            "current_source_pins": pins, "panel_source_pins": panel_pins}


def output_controls(x, m, temporary):
    output = temporary / "dangling-output.json"
    absent = temporary / "absent-target.json"
    output.symlink_to(absent)
    calls = []

    def native_stub(*_):
        calls.append("native_export_stub")
        return {"schema": "REVIEW_STUB_ONLY"}

    argv = ["export.py", "--manifest", "unused", "--manifest-sha256", "unused", "--out", str(output), "--extract"]
    with patch.object(sys, "argv", argv), patch.object(x, "export_native", native_stub):
        rejected(x.main, FileExistsError)
    require(calls == ["native_export_stub"] and output.is_symlink() and not absent.exists(), "dangling native control")

    def source_stub():
        calls.append("panel_source_stub")
        raise RuntimeError("entered source stub before output reservation")

    with patch.object(m, "read_sources", source_stub):
        rejected(lambda: m.main(["--out", str(output)]), RuntimeError)
    require(calls == ["native_export_stub", "panel_source_stub"], "dangling panel source control")

    race_output = temporary / "competing-output.json"
    barrier = threading.Barrier(2)
    race_calls = []

    def racing_stub(*_):
        race_calls.append("native_export_stub")
        barrier.wait(timeout=10)
        return {"schema": "REVIEW_RACE_STUB_ONLY"}

    def invoke():
        try:
            x.main()
        except FileExistsError:
            return "collision"
        return "success"

    race_argv = ["export.py", "--manifest", "unused", "--manifest-sha256", "unused", "--out", str(race_output), "--extract"]
    stdout = io.StringIO()
    with patch.object(sys, "argv", race_argv), patch.object(x, "export_native", racing_stub), redirect_stdout(stdout):
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
            results = sorted(executor.map(lambda _: invoke(), (0, 1)))
    require(results == ["collision", "success"] and len(race_calls) == 2, "both competing calls reached native stub")
    require(read(race_output)["schema"] == "REVIEW_RACE_STUB_ONLY", "exclusive write still preserves winner")
    return {"dangling_output": {"intake_native_export_stub_calls_before_final_FileExistsError": 1,
            "panel_source_stub_calls_before_final_output_creation": 1, "link_preserved": True, "link_target_created": False},
            "competing_intake_calls": {"outcomes": results, "native_export_stub_calls": len(race_calls), "winner_output_preserved": True},
            "actual_native_extraction_executed": False}


def pytest_checks(temporary):
    intake_code = """import builtins,sys,pytest
from unittest.mock import patch
original=builtins.__import__
def guarded(name,*args,**kwargs):
    if name.split('.')[0] in {'cadquery','OCP'}: raise AssertionError('CAD import blocked in intake fixtures')
    return original(name,*args,**kwargs)
with patch.object(builtins,'__import__',guarded):
    code=pytest.main(sys.argv[1:])
raise SystemExit(code)
"""
    panel_code = """import sys,pytest,cadquery as cq
from unittest.mock import patch
from scripts import run_thin_bolted_finite_frame as saved
def forbidden(*args,**kwargs): raise AssertionError('genuine BRep/real saved bank blocked in panel fixtures')
with patch.object(saved,'reuse_panel_operators',forbidden), patch.object(cq.Shape,'importBrep',staticmethod(forbidden)):
    code=pytest.main(sys.argv[1:])
raise SystemExit(code)
"""
    batches = [("intake", 25, intake_code, [INTAKE / "test_extended_intake.py", RAW / "current-source-export-v1/test_export.py"]),
               ("panel", 18, panel_code, [PANEL / "test_panel_operators.py"])]
    records = []
    for label, count, code, paths in batches:
        argv = [sys.executable, "-B", "-c", code, "-q", "-p", "no:cacheprovider", "--basetemp", str(temporary / label), *map(str, paths)]
        environment = {**os.environ, "PYTEST_DISABLE_PLUGIN_AUTOLOAD": "1", "PYTHONDONTWRITEBYTECODE": "1"}
        completed = subprocess.run(argv, cwd=ROOT, env=environment, capture_output=True, text=True, check=False)
        require(completed.returncode == 0, "supplied " + label + " tests failed:\n" + completed.stdout + completed.stderr)
        require(f"{count} passed" in completed.stdout, "supplied test count differs")
        records.append({"argv": argv, "stdout": completed.stdout, "stderr": completed.stderr, "passed": count})
    return {"batches": records, "passed": 43, "real_saved_panel_bank_loader_blocked": True,
            "intake_cadquery_or_OCP_import_blocked": True, "panel_CAD_library_imported_without_BREP_import_or_query": True}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, default=OWN.with_name("receipt.json"))
    args = parser.parse_args()
    with args.out.open("xb") as receipt_stream:
        exact = {INTAKE / "export.py": "bdfa95b4da8dfcb3d183dcaf59574afdb2f42e938f8e535680739fa0637696bb",
                 INTAKE / "verification.json": "e5b8451c7b6d23822b8909378f2df98e6132e16384900ac20b5c3522b5193544",
                 PANEL / "panel_operators.py": "014f867eac1e9286dee188024544b5853e5cda2aa1cd11037d7aee5a2b29966b",
                 PANEL / "method-receipt.json": "72f1d047ddf567fd2053911157be02288c1357477ee3ca429223bb85f9acc0e2",
                 AUTHORITY / "adjusted-base-manifest.json": "27220ec69ebe96e0c637d02d74aea1a7732f68d111b9918c973fa8ee954b48c2",
                 AUTHORITY / "extended-cleat-manifest.json": "458a7f0220e5776fdb53b876b9815715bf278c5b22eea7699824a9919dd6bfe6"}
        verify({str(path.relative_to(ROOT)): digest for path, digest in exact.items()})
        files = [*exact, INTAKE / "test_extended_intake.py", PANEL / "test_panel_operators.py", OWN]
        source_sha256 = {str(path.relative_to(ROOT)): sha(path) for path in files}
        for record in (read(INTAKE / "verification.json"), read(PANEL / "method-receipt.json")):
            verify(record["source_sha256"])
        os.environ.setdefault("PYTHONPATH", ".")
        x = load(INTAKE / "export.py", "independent_method_intake_review")
        m = load(PANEL / "panel_operators.py", "independent_method_panel_review")
        import cadquery as cq
        def forbidden(*_, **__):
            raise AssertionError("genuine BRep import/real saved panel bank blocked")
        with patch.object(m.raised.saved, "reuse_panel_operators", forbidden), patch.object(cq.Shape, "importBrep", staticmethod(forbidden)):
            sources = source_checks(x, m)
        with tempfile.TemporaryDirectory(prefix="eoere-method-testing-") as directory:
            temporary = Path(directory)
            controls = output_controls(x, m, temporary)
            pytest_result = pytest_checks(temporary)
        verify(source_sha256)
        verify(sources["current_source_pins"])
        verify(sources["panel_source_pins"])
        finding = {"severity": "medium", "category": "testing/correctness", "file": str((INTAKE / "export.py").relative_to(ROOT)), "line": 243,
            "also_affected": [{"file": str((PANEL / "panel_operators.py").relative_to(ROOT)), "line": 251},
                              {"file": str((INTAKE / "test_extended_intake.py").relative_to(ROOT)), "line": 183},
                              {"file": str((PANEL / "test_panel_operators.py").relative_to(ROOT)), "line": 202}],
            "description": "Output tests cover an existing regular file but miss dangling symlinks and reservation races. Path.exists() accepts a dangling symlink, and exclusive file creation occurs only after source/extraction work. Two competing fresh calls can both finish the extraction callback before one receives FileExistsError.",
            "impact": "A doomed output can still enter the separately gated native extraction route; duplicate invocations can spend the serialized extraction work twice for a single output. Exclusive writing preserves existing bytes, but the claimed stop-before-source/native boundary is not enforced for these cases.",
            "fix": "Reserve the output exclusively before source/authentication/extraction (using xb/x, keeping failed attempts reserved), then write through the reserved handle. Add dangling-output-link and competing same-output tests that assert source/native callbacks are never reached by the rejected call. Preserve the frozen reusable exporter."}
        receipt = {"schema": "eoere_adjusted_method_independent_testing_review/v1", "status": "SUPPLIED_TESTS_PASS_WITH_ONE_CONFIRMED_OUTPUT_GUARD_FINDING", "findings": [finding],
            "command": [sys.executable, "-B", str(OWN.relative_to(ROOT)), "--out", str(args.out)], "runtime": {"python": platform.python_version()},
            "source_sha256": source_sha256, "source_checks": {k: v for k, v in sources.items() if not k.endswith("source_pins")},
            "source_closures_verified_before_after": {"intake": len(sources["current_source_pins"]), "panel": len(sources["panel_source_pins"])},
            "independent_output_controls": controls, "supplied_tests": pytest_result,
            "limits": ["Only source metadata, supplied fake-solid fixtures and tiny 48-DOF panel charts were executed.",
                       "Intake fixtures block CAD module imports. Panel frozen imports load the CAD library but genuine BRep importing and the real saved panel-bank loader were replaced with failure sentinels during metadata/tests.",
                       "The output defect was demonstrated only with native/source stubs; no genuine BRep extraction, real panel/frame K, q, load cases, native solve, browser or current-force bridge ran.",
                       "All frozen target/source bytes remained unchanged. Temporary outputs belonged to this review and were removed by their TemporaryDirectory."]}
        receipt_stream.write((json.dumps(receipt, indent=2, sort_keys=True, allow_nan=False) + "\n").encode())
    print(json.dumps({"status": receipt["status"], "tests": pytest_result["passed"], "receipt_sha256": sha(args.out)}))


if __name__ == "__main__":
    main()
