"""Parent saved-output admission; replay captured operators without preparing K."""
import hashlib
import importlib.util
import json
import sys
import traceback
from pathlib import Path

HERE = Path(__file__).resolve().parent
GATE = HERE.parent / "four-port-method-v1/first_order_admission_v2.py"
EXPECTED_GATE = "bfb984c47372d20387883d11d1d49f8a12d9debda1b0c78f1c024ace01bc2821"
EXPECTED_FIELD = "dad00e84ae98333beeb89a0c2403d48d9f40e9189c4525fc3746b8b3118de598"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


assert sha(GATE) == EXPECTED_GATE
assert sha(HERE / "field.json") == EXPECTED_FIELD
assert not (HERE / "admission.json").exists()
assert not (HERE / "admission-failure.json").exists()
spec = importlib.util.spec_from_file_location("eoere_parent_corrected_admission", GATE)
gate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gate)
try:
    receipt = gate.audit_first_order_state(HERE / "field.json")
except Exception:
    record = {"schema": "eoere_parent_saved_field_admission_failure/v1",
              "command": sys.orig_argv, "gate_sha256": EXPECTED_GATE,
              "field_sha256": EXPECTED_FIELD, "traceback": traceback.format_exc(),
              "accepted_field": False, "physical_release": False}
    with (HERE / "admission-failure.json").open("x") as stream:
        json.dump(record, stream, indent=2, sort_keys=True)
        stream.write("\n")
    raise
with (HERE / "admission.json").open("x") as stream:
    json.dump(receipt, stream, indent=2, sort_keys=True)
    stream.write("\n")
assert sha(HERE / "field.json") == EXPECTED_FIELD
assert sha(GATE) == EXPECTED_GATE
print(json.dumps({"admission_sha256": sha(HERE / "admission.json"),
                  "success": receipt[gate.SUCCESS],
                  "original_law_checks": receipt["original_law_checks"],
                  "motion_diagnostics": receipt["motion_diagnostics"]}, sort_keys=True))
