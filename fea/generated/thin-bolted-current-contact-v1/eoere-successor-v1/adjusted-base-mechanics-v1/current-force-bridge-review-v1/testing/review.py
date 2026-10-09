"""Independent tiny/stub bridge review. No candidate construction or solve."""
import contextlib
import copy
import hashlib
import importlib.util
import json
import sys
import tempfile
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

sys.dont_write_bytecode = True
ROOT = Path.cwd()
RAW = Path("fea/generated/thin-bolted-current-contact-v1/eoere-successor-v1/adjusted-base-mechanics-v1/current-force-bridge-v1")
HERE = Path(__file__).resolve().parent
EXPECTED = {"bridge.py": "ddc85386050d97145597dc720bef78634c9b326f0878aced8c02c8df4710c05b",
    "test_bridge.py": "72cdd692b40df93e2a6a194e31d9bd03fe7125baf6fb605a09b66954bbecacf6",
    "source-preflight.json": "4118719a61da4645085f4840b1888ac6df600df2307edc8c0d40ffb79d4eafe0",
    "verification.json": "7ca9a676dd1c7b1ae41a4408caeae6d0d22c0ee57da43095663b8587238d5fab"}


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


for file, expected in EXPECTED.items():
    assert sha(RAW/file) == expected
b = load(RAW/"bridge.py", "independent_bridge_testing")
test = load(RAW/"test_bridge.py", "independent_bridge_pending_fixtures")
verification = json.loads((RAW/"verification.json").read_bytes())
assert verification["production_readiness_claimed"] is False
assert verification["parent_final_source_review_completed"] is False
assert verification["candidate_CAD_panel_K_global_K_q_actions_native_solve_or_admission_performed"] is False
assert b.GEOMETRY["sha256"].startswith("01ba30") and b.SOURCE_MANIFEST["sha256"].startswith("458a")
assert b.PANEL_BANK["sha256"].startswith("014f")
source_files = [Path(__file__).resolve(), *[RAW/name for name in EXPECTED], b.old_gate.OWN, b.old_runner.OWN,
    b.driver.OWN, b.factory.OWN, b.base.OWN, b.bundle.CORE]
source_sha256 = {str(path.resolve().relative_to(ROOT)): sha(path) for path in source_files}

# Exercise actual run_case orchestration with inert dependencies. The invalid
# input review is rejected by its actual preparation-boundary call, after the
# panel dependency stub has already been reached. No panel K is constructed.
events = []
with tempfile.TemporaryDirectory(prefix="readiness-order-", dir=HERE) as temporary:
    temporary = Path(temporary)
    out, dummy = temporary/"field.json", temporary/"stub-input.json"
    args = SimpleNamespace(run=True, case_id="a12-rear", wall_seconds=10., out=out,
        inputs=dummy, inputs_sha256="a"*64, input_review=dummy, input_review_sha256="b"*64,
        method_input=dummy, method_input_sha256="c"*64)
    ref = lambda path, digest: {"path": b.bundle.artifact_path(path.resolve()), "sha256": digest}
    method = {"input": ref(dummy, args.inputs_sha256), "input_review": ref(dummy, args.input_review_sha256),
        "input_record": ref(dummy, args.method_input_sha256)}

    def panels(*_args):
        events.append("panel_dependencies_reached")
        return {}, {}, {}, {}

    def reject(*_args, **_kwargs):
        events.append("independent_input_review_rejected")
        raise ValueError("unreviewed stub input")

    def prepare(data, panels, integrated, *, source_sha256, source_review):
        return b.factory.authenticate_source_review(source_review, data, source_sha256)

    bank = SimpleNamespace(load_panel_dependencies=panels, verify_panel_source_inputs=lambda *_args: {})
    centroidal = SimpleNamespace(correction_context=lambda *_args: contextlib.nullcontext())
    with patch.object(b, "read_method", return_value=method), patch.object(b, "slot_check", return_value={}), \
            patch.object(b, "methods", return_value=(centroidal, bank)), patch.object(b, "source_pins", return_value={}), \
            patch.object(b, "read_inputs", return_value=({}, {})), patch.object(b.driver, "select_case", return_value=({}, {})), \
            patch.object(b, "verify_selected_case", return_value=None), patch.object(b, "authenticate_review", side_effect=reject), \
            patch.object(b.factory, "prepare", side_effect=prepare):
        try:
            b.run_case(args)
        except ValueError as error:
            assert str(error) == "unreviewed stub input"
        else:
            raise AssertionError("invalid review was accepted")
    failure = json.loads(out.with_suffix(".json.failed.json").read_bytes())
    assert failure["accepted_q"] is None and failure["accepted_actions"] is None
    assert not out.exists()
assert events == ["panel_dependencies_reached", "independent_input_review_rejected"]
assert b.factory.SCHEMA == b.ORIGINAL_SCHEMA and b.factory.read_inputs is b.ORIGINAL_READ
assert b.factory.authenticate_source_review is b.ORIGINAL_AUTHENTICATE

# A consumer-only fixture exercises exact byte/table/q/schema joins. It is not
# passed through the physical force auditor and establishes no field admission.
field = copy.deepcopy(test.fixture_field())
field.update(state_id=b.STATE_PREFIX+"synthetic", case_id="a12-rear", accessory_placement="synthetic",
    operator_bundle={"arrays": {"path": "stub.npz", "sha256": "0"*64}, "manifest": {"path": "stub.json", "sha256": "1"*64}},
    original_operator_fingerprint_sha256="2"*64,
    current_method_input={"path": "stub-method.json", "sha256": "3"*64}, source_case_selection={},
    current_panel_operator_preparation={}, source_sha256={})
for key in b.base.TABLES:
    field[key] = []


def payload(value):
    return json.dumps(value, sort_keys=True, allow_nan=False).encode()


def receipt_for(value):
    return {"schema": b.ADMISSION_SCHEMA, b.SUCCESS: True, "input_raw_sha256": hashlib.sha256(payload(value)).hexdigest(),
        "input_canonical_sha256": b.canonical(value), "admission_source_sha256": b.LOADED_SHA,
        "support_contract": b.law.contract(), "source_path": b.bundle.artifact_path(b.OWN), "release": b.core.RELEASE,
        **{key: value[key] for key in ["state_id", "case_id", "accessory_placement"]},
        "q_canonical_sha256": value["response"]["q_canonical_sha256"],
        "gradient_canonical_sha256": value["response"]["gradient_canonical_sha256"],
        "declared_law_checks": {"full_signed_gradient_canonical_sha256": value["response"]["gradient_canonical_sha256"],
            "gradient_inf_n": value["response"]["gradient_inf_n"], "floor_force_and_declared_fixed_rear_leg_mask_replayed": True},
        "normal_force_n_by_host": value["response"]["fixed_floor_support_v1"]["normal_force_n_by_host"],
        "operator_bundle": copy.deepcopy(value["operator_bundle"]),
        "original_operator_fingerprint_sha256": value["original_operator_fingerprint_sha256"],
        "method_input": value["current_method_input"], "source_case_selection": value["source_case_selection"],
        "current_panel_operator_preparation_sha256": b.canonical(value["current_panel_operator_preparation"]),
        "table_canonical_sha256": {key: b.canonical(value[key]) for key in b.base.TABLES}, "source_sha256": {}}


receipt = receipt_for(field)
controls = [
    ("old receipt schema", lambda f, r: r.update(schema=b.old_gate.SCHEMA)),
    ("old field schema", lambda f, r: f.update(schema=b.old_runner.FIELD_SCHEMA)),
    ("wrong q receipt", lambda f, r: r.update(q_canonical_sha256="f"*64)),
    ("wrong gradient receipt", lambda f, r: r.update(gradient_canonical_sha256="f"*64)),
    ("wrong operator receipt", lambda f, r: r["operator_bundle"].update(extra=True)),
    ("wrong action table receipt", lambda f, r: r["table_canonical_sha256"].update({b.base.TABLES[0]: "f"*64})),
    ("wrong method receipt", lambda f, r: r.update(method_input={})),
    ("release", lambda f, r: r.update(release={"structural_released": True})),
    ("foreign state", lambda f, r: r.update(state_id="foreign")),
]
rejected = []
with patch.object(b, "source_pins", return_value={}), patch.object(b, "read_method", return_value={}):
    accepted, pins = b.require_admitted_payload(payload(field), receipt, admission_sha256=b.LOADED_SHA)
    assert accepted == field and pins == {}
    for label, mutate in controls:
        changed, observed = copy.deepcopy(field), copy.deepcopy(receipt)
        mutate(changed, observed)
        try:
            b.require_admitted_payload(payload(changed), observed, admission_sha256=b.LOADED_SHA)
        except (ValueError, KeyError):
            rejected.append(label)
        else:
            raise AssertionError(label)
    for label, raw, gate_sha in [
        ("byte whitespace tamper", payload(field)+b" ", b.LOADED_SHA),
        ("foreign gate source", payload(field), "f"*64),
    ]:
        try:
            b.require_admitted_payload(raw, receipt, admission_sha256=gate_sha)
        except ValueError:
            rejected.append(label)
        else:
            raise AssertionError(label)
assert len(rejected) == 11
for path, expected in source_sha256.items():
    assert sha(path) == expected
finding = {"severity": "medium", "category": "testing/readiness", "file": str(RAW/"bridge.py"), "line": 384,
    "description": "Deferred run_case loads current panel dependencies before authenticating the exact independent input review. Authentication occurs only inside factory.prepare at line 390.",
    "impact": "An invalid or mismatched review can trigger current panel K preparation before its source-readiness rejection. Existing tests do not invoke run_case, so their rejection-before-work checks do not cover this path.",
    "observed_stub_event_order": events,
    "fix": "Authenticate the raw/selected input review before bank.load_panel_dependencies, retain the preparation-time check, and add a sentinel test requiring invalid reviews to reject before panel dependency loading."}
result = {"schema": "eoere_current_force_bridge_independent_testing_review/v1", "source_sha256": source_sha256,
    "status": "ONE_CONFIRMED_READINESS_ORDERING_FINDING", "findings": [finding],
    "existing_tests": {"command": ".venv/bin/python -m pytest -q "+str(RAW/"test_bridge.py"), "passed": 17},
    "new_checks": {"actual_run_case_stub_order_exercised": True, "failed_stub_field_not_published": True,
        "factory_hooks_restored_after_stub_failure": True, "consumer_byte_join_positive_fixture": True,
        "consumer_join_rejections": rejected},
    "limits": ["All producer dependencies replaced by inert stubs for ordering review; no current descriptor, CAD/BRep, panel K, frame solve, q recovery or native execution.",
        "Consumer positive fixture tests joins only; it was not independently audited as a physical field.",
        "Full raw-field force/recovery audit remains unexecuted. Production input/export, input review, method readiness and serial slot remain missing.",
        "All frozen target/source files preserved. No hardware, panel remedy, structural or physical release."],
    "command": sys.argv, "python": sys.version.split()[0]}
with (HERE/"receipt.json").open("x") as stream:
    stream.write(json.dumps(result, indent=2, sort_keys=True, allow_nan=False)+"\n")
print(json.dumps({"receipt": str((HERE/"receipt.json").relative_to(ROOT)), "sha256": sha(HERE/"receipt.json"), "findings": 1, "consumer_rejections": len(rejected)}))
