"""Independent source-port and endpoint arithmetic for the saved stack trial."""
import hashlib
import json
import re
from pathlib import Path

import numpy as np

ROOT = Path.cwd()
DOC = ROOT / "docs/wood-joints-mvp/hypotheses/hl35-candidate/thin-frame-comparison/eoere-successor-v1/bounded-strength-v1/connected-stack-followup-v1"
RAW = Path(__file__).resolve().parent
REPLAY = RAW.parent / "replay"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def bound(path):
    return {"path": str(path.relative_to(ROOT)), "sha256": sha(path), "bytes": path.stat().st_size}


result = json.loads((DOC / "result.json").read_text())
details = json.loads((RAW / "details.json").read_text())
inputs = json.loads((DOC / "inputs.json").read_text())
source = json.loads((DOC.parent / "inputs.json").read_text())
fields = {}
for case in source["cases"]:
    manifest = json.loads((ROOT / case["manifest"]["path"]).read_text())
    fields[case["case_id"]] = json.loads((ROOT / manifest["field"]["path"]).read_text())
force_errors, moment_errors, density_errors = [], [], []
for row in details["member_bearing_trials"]:
    field = fields[row["case_id"]]
    shaft = next(r for r in field["source_inputs"]["shafts"] if r["axis_id"] == row["axis_id"])
    port = next(r for key in ("common_shaft_wood_bearing_actions", "common_shaft_steel_port_actions") for r in field[key]
                if r["axis_id"] == row["axis_id"] and r["surface_index"] == row["surface_index"])
    g = np.asarray(shaft["basis"][0])
    lo, hi = port["surface_interval_mm"]
    length = hi - lo
    center = np.asarray(shaft["point"]) + (lo + hi) / 2 * g
    f = np.asarray(port["force_on_host_xyz_n"])
    lateral = f - g * (g @ f)
    moment = np.asarray(port["moment_on_host_at_point_xyz_nmm"]) + np.cross(np.asarray(port["point_xyz_mm"]) - center, f)
    left, right = np.asarray(row["affine_endpoint_line_density_vectors_n_mm"])
    # Endpoint integration uses the trapezoidal force and its exact moment;
    # it does not call the producer's formula or quadrature.
    integral_f = (left + right) * length / 2
    integral_m = np.cross(g, (right - left) * length**2 / 12)
    force_errors.append(float(np.linalg.norm(integral_f - lateral)))
    moment_errors.append(float(np.linalg.norm(integral_m - moment)))
    density_errors.append(abs(max(np.linalg.norm(left), np.linalg.norm(right)) - row["affine_trial_peak_line_density_n_mm"]))
assert len(force_errors) == 144 and max(force_errors) < 1e-8 and max(moment_errors) < 1e-5
assert max(density_errors) < 1e-10
assert result["stack_case_count"] == 48 and len(details["connected_stacks"]) == 48
assert all(r["adjusted_complete_joint_resistance_n"] is None for r in result["stacks"])
assert not any(result["execution"].values()) and not result["fabrication_or_climbing_release"]
for name in ("result.json", "details.json"):
    assert (RAW / name).read_bytes() == (REPLAY / name).read_bytes()
assert (DOC / "result.json").read_bytes() == (RAW / "result.json").read_bytes()
for path, expected in details["complete_source_sha256"].items():
    assert sha(ROOT / path) == expected, path
preserved = []
for directory in (DOC.parent, DOC.parent / "resistance-followup-v1", DOC.parent / "revised-base-audit-v1"):
    verification = directory / "verification.json"
    old = json.loads(verification.read_text())
    owned = old.get("owned_artifacts", old.get("owned_files", {}))
    assert len(owned) == 4, (str(directory), list(old))
    for path, record in owned.items():
        assert sha(ROOT / path) == record["sha256"], path
    preserved.append(bound(verification))
destinations = []
for target in re.findall(r"\]\(([^)]+)\)", (DOC / "README.md").read_text()):
    if target.startswith("https://"):
        continue
    path = (DOC / target.split("#")[0]).resolve()
    if path.name == "verification.json":
        continue
    assert path.exists(), str(path)
    destinations.append(str(path.relative_to(ROOT)))
value = {
    "schema": "eoere_connected_stack_bearing_statics_verification/v1",
    "status": "VERIFIED_PRESCRIBED_ACTION_STATICS_ONLY",
    "checks": {"all_source_pins_verified": len(details["complete_source_sha256"]),
               "independent_endpoint_integrals": len(force_errors),
               "maximum_independent_force_error_n": max(force_errors),
               "maximum_independent_moment_error_nmm": max(moment_errors),
               "maximum_independent_peak_density_error_n_mm": max(density_errors),
               "known_answers_and_seven_rejections": result["known_answers"],
               "both_raw_JSON_outputs_byte_reproduced": True,
               "all_eight_complete_joint_resistances_remain_null": True,
               "local_destinations": destinations},
    "independent_check_scope": "Same-agent independent endpoint/source-port arithmetic, not an independent engineering review.",
    "owned_artifacts": {str((DOC / name).relative_to(ROOT)): bound(DOC / name)
                        for name in ("README.md", "analyze.py", "inputs.json", "result.json")},
    "raw_details": bound(RAW / "details.json"),
    "independent_checker": bound(Path(__file__).resolve()),
    "preserved_packets": preserved,
    "commands": [
        f"uv run python {DOC.relative_to(ROOT)}/analyze.py --out {REPLAY.relative_to(ROOT)} --compare {RAW.relative_to(ROOT)}",
        f"uv run python {Path(__file__).resolve().relative_to(ROOT)}",
        f"uv run ruff check {DOC.relative_to(ROOT)}/analyze.py",
        f"uv run ruff format --check {DOC.relative_to(ROOT)}/analyze.py"],
    "native_solve": False, "geometry_changed": False, "new_response": False,
    "physical_observation": False,
    "retention": "Five compact permanent files; detailed trials and checker in ignored attempt02. No archive or prune."}
(DOC / "verification.json").write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")
print(json.dumps(value["checks"]))
