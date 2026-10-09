"""Independent synthetic consumer tests; actual reducers and gate stay deferred."""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

OWN = Path(__file__).resolve()
MECH = OWN.parents[2]
ROOT = OWN.parents[7]
TARGET = MECH / "current-component-bridge-v1/consumer-v1"
EXPECTED = {
    TARGET / "consume.py": "f11175782c7b29abbdfbcbf5fbad63f919596bc6a613b4c7a5b65acc1027bad9",
    TARGET / "test_consume.py": "e289bf15565d6fd19d4ee59ff8cc9b11b7db3ac807e5584abe2cc353b254cab5",
    TARGET / "verification.json": "13d897fdb5271aafe1af3c2c1741ff592ae8cee3fba5a995cd8fdd4ddc8a4bc4",
    TARGET.parent / "component_plan.py": "caf5d1307d999843c3ea16f3536f5bdd25edb390ebbab6e624cf5f5a86dc727e",
    MECH / "current-force-bridge-v1/review-fix-v2/bridge.py": "4916532168ba05268e164b28bb634743013b4aa7e062b7f9d345ecfafb954643",
}


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load():
    spec = importlib.util.spec_from_file_location("independent_current_component_testing", TARGET / "consume.py")
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


def controls():
    m = load()
    plan = m._load_plan()
    data = json.loads(plan.checked_bytes(plan.ARTIFACTS["descriptors"]))
    source = {key: copy.deepcopy(data[value]) for key, value in m.DESCRIPTOR_KEYS.items()}
    source.update(parameters=data["parameters"], panel_ids=[r["id"] for r in data["finished_body_observations"]
                  if r["id"] not in {t["name"] for t in data["raw_gross_timber_rows"]}],
                  geometry={"report": plan.ARTIFACTS["geometry"], "source_manifest": plan.ARTIFACTS["manifest"],
                            "cached_source_export": plan.ARTIFACTS["descriptors"]})
    field = {"schema": m.FIELD_SCHEMA, "state_id": "independent-synthetic-state", "case_id": "synthetic-case",
             "accessory_placement": "synthetic-placement", "release": m.RELEASE, "source_inputs": source,
             "current_execution": {"geometry": plan.ARTIFACTS["geometry"]}}
    receipt = {"schema": m.ADMISSION_SCHEMA, m.SUCCESS: True}
    checked = {}
    with tempfile.TemporaryDirectory(prefix="synthetic-fixtures-", dir=OWN.parent) as directory:
        temp = Path(directory)
        fp, rp = temp / "field.json", temp / "receipt.json"
        fp.write_text(json.dumps(field, sort_keys=True))
        rp.write_text(json.dumps(receipt, sort_keys=True))
        kwargs = {"expected_field_sha256": sha(fp), "expected_receipt_sha256": sha(rp)}
        events = []
        axes_expected = plan.indexed(json.loads(plan.checked_bytes(plan.ARTIFACTS["geometry"]))["axes"], "id")
        sentinel = {"synthetic_exceedance": {"index": 2.75, "complete_resistance": None},
                    "unavailable": None, "signed_witness": [-8.0, 3.0]}
        def gate(raw, admitted, *, admission_sha256):
            events.append("synthetic_gate")
            assert raw == fp.read_bytes() and admitted == receipt and admission_sha256 == m.GATE_SHA
            return json.loads(raw), {}
        def reducer(actual, axes, current_plan, pins, samples):
            events.append("synthetic_reducer_after_real_contract")
            assert actual == field and axes == axes_expected and len(axes) == 100 and samples == 3
            assert current_plan.ARTIFACTS == plan.ARTIFACTS
            assert all(pins[ref["path"]] == ref["sha256"] for ref in plan.ARTIFACTS.values())
            return sentinel
        with patch.object(m, "_load_gate", lambda _: SimpleNamespace(require_admitted_payload=gate)), patch.object(m, "_reduce", reducer):
            result = m.consume(fp, rp, samples=3, **kwargs)
            assert events == ["synthetic_gate", "synthetic_reducer_after_real_contract"]
            assert result["component_reductions"] is sentinel and result["component_reductions"] == sentinel
            assert result["complete_joint_resistance"] is None and result["release"] == m.RELEASE
            assert result["source_inputs_canonical_sha256"] == m.canonical(field["source_inputs"])
            checked["real_current_saved_contract_routes_exact100_axes_and_preserves_synthetic_exceedances_nulls"] = True

            events.clear()
            for samples in (True, 2, 3.0, "41"):
                expect(ValueError, lambda samples=samples: m.consume(fp, rp, samples=samples, **kwargs), "three spatial samples")
            assert not events
            checked["invalid_samples_rejected_before_gate_or_reducer"] = True

            damaged = copy.deepcopy(field)
            damaged["source_inputs"]["direct_contacts"][0]["stiffness"] = -1.0
            fp.write_text(json.dumps(damaged, sort_keys=True))
            expect(ValueError, lambda: m.consume(fp, rp, expected_field_sha256=sha(fp), expected_receipt_sha256=sha(rp)), "descriptor join differs: direct_contacts")
            assert events == ["synthetic_gate"]
            fp.write_text(json.dumps(field, sort_keys=True))
            checked["current_contact_metadata_drift_rejected_by_real_contract_before_reducer"] = True

        def mutate_receipt(*_):
            rp.write_text("changed during synthetic reduction")
            return sentinel
        with patch.object(m, "_load_gate", lambda _: SimpleNamespace(require_admitted_payload=gate)), patch.object(m, "_reduce", mutate_receipt):
            expect(ValueError, lambda: m.consume(fp, rp, **kwargs), "exact source/artifact bytes required")
        rp.write_text(json.dumps(receipt, sort_keys=True))
        checked["admission_receipt_byte_change_during_reduction_rejected"] = True

        fake_plan = temp / "tampered-plan.py"
        fake_plan.write_text("raise AssertionError('untrusted plan executed')\n")
        with patch.object(m, "PLAN", fake_plan):
            expect(ValueError, lambda: m.consume(fp, rp, **kwargs), "exact source/artifact bytes required")
        checked["tampered_source_plan_rejected_before_execution"] = True

        fake_own = temp / "isolated-consumer-source.py"
        fake_own.write_text("original fixture bytes\n")
        loaded_sha = sha(fake_own)
        fake_own.write_text("changed fixture bytes\n")
        with patch.object(m, "OWN", fake_own), patch.object(m, "LOADED_SHA", loaded_sha), patch.object(m, "_load_plan", lambda: (_ for _ in ()).throw(AssertionError("plan reached"))):
            expect(ValueError, lambda: m.consume(fp, rp, **kwargs), "exact source/artifact bytes required")
        checked["consumer_self_source_tamper_rejected_before_plan_or_gate"] = True

        out = temp / "already-exists.json"
        out.write_bytes(b"preserved bytes\n")
        with patch.object(m, "consume", lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("producer reached"))):
            expect(FileExistsError, lambda: m.consume_to_file("missing", "missing", out))
        assert out.read_bytes() == b"preserved bytes\n"
        checked["regular_existing_output_preserved_before_intake"] = True

        out = temp / "nonfinite-output.json"
        with patch.object(m, "consume", lambda *_args, **_kwargs: {"schema": "synthetic", "value": float("nan")}):
            expect(ValueError, lambda: m.consume_to_file("unused", "unused", out))
        failure = json.loads(out.read_bytes())
        assert failure["status"] == "FAILED" and failure["release"] == m.RELEASE
        checked["nonfinite_synthetic_result_retains_unreleased_FAILED_receipt"] = True

        assert "cadquery" not in sys.modules
        assert not any(name == "OCP" or name.startswith("OCP.") for name in sys.modules)
        assert not any(name.startswith("eoere_current_coarse_") for name in sys.modules)
        checked["controls_did_not_import_actual_reducers_cadquery_or_OCP"] = True
    return checked


def main():
    if "--controls" in sys.argv:
        print(json.dumps(controls(), sort_keys=True))
        return
    start = time.monotonic()
    before = {str(path.relative_to(ROOT)): sha(path) for path in EXPECTED}
    assert all(sha(path) == digest for path, digest in EXPECTED.items())
    environment = dict(os.environ, PYTHONPATH=str(ROOT))
    command = [sys.executable, "-B", "-m", "pytest", "-q", "-p", "no:cacheprovider", str((TARGET / "test_consume.py").relative_to(ROOT))]
    tests = subprocess.run(command, cwd=ROOT, env=environment, capture_output=True, text=True, check=False, timeout=40)
    assert tests.returncode == 0, tests.stdout + tests.stderr
    result = subprocess.run([sys.executable, "-B", str(OWN), "--controls"], cwd=ROOT, env=environment, capture_output=True, text=True, check=False, timeout=40)
    assert result.returncode == 0, result.stdout + result.stderr
    checked = json.loads(result.stdout)
    lint_command = [sys.executable, "-B", "-m", "ruff", "check", str(TARGET.relative_to(ROOT)), str(OWN.relative_to(ROOT))]
    lint = subprocess.run(lint_command, cwd=ROOT, env=environment, capture_output=True, text=True, check=False, timeout=30)
    assert lint.returncode == 0, lint.stdout + lint.stderr
    assert before == {str(path.relative_to(ROOT)): sha(path) for path in EXPECTED}
    receipt = {"schema": "independent_current_component_consumer_testing_review/v1",
               "status": "PASS_NO_SUBSTANTIAL_TESTING_FINDINGS", "reviewer": "/root/intake_final_testing",
               "branch": "master", "frozen_target_sha256": before, "frozen_target_bytes_unchanged": True,
               "review_source_sha256": {str(OWN.relative_to(ROOT)): sha(OWN)},
               "existing_tests": {"command": command, "result": tests.stdout.strip()},
               "isolated_synthetic_and_saved_metadata_controls": checked,
               "ruff": {"command": lint_command, "result": lint.stdout.strip()},
               "substantial_findings": [], "elapsed_seconds": time.monotonic() - start,
               "actual_field_or_admission_pair_actual_gate_reducers_CAD_K_native_frame_browser_executed": False,
               "limits": ["The successful saved-contract control uses synthetic admission and a synthetic reducer; its values are not current component findings.",
                          "Actual reducer/admission composition still needs the parent-authorized genuine fresh pair. No resistance, release or old acceptance transfers."]}
    OWN.with_name("receipt.json").write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"status": receipt["status"], "isolated_controls": len(checked), "tests": tests.stdout.strip(), "ruff": lint.stdout.strip()}))


if __name__ == "__main__":
    main()
