"""Read-only hash/scalar review. No CAD, solver, browser, or producer rerun."""
import ast
import hashlib
import json
import math
import sys
from pathlib import Path
from types import SimpleNamespace

import numpy as np

ROOT = Path.cwd()
DOC = Path("docs/wood-joints-mvp/hypotheses/hl35-candidate/thin-frame-comparison/eoere-successor-v1/bounded-strength-v1")
RAW = Path("fea/generated/thin-bolted-current-contact-v1/eoere-successor-v1/bounded-strength-v1")
SELF = Path(__file__).resolve().relative_to(ROOT)
OUTPUT = Path(sys.argv[1])


def sha(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read(path):
    return json.loads(Path(path).read_bytes())


def canonical(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest()


def require(ok, message):
    if not ok:
        raise ValueError(message)


def add(a, b):
    return [x + y for x, y in zip(a, b)]


def scale(a, x):
    return [v * x for v in a]


def sub(a, b):
    return add(a, scale(b, -1))


def dot(a, b):
    return math.fsum(x * y for x, y in zip(a, b))


def norm(a):
    return math.sqrt(dot(a, a))


def cross(a, b):
    return [a[1]*b[2] - a[2]*b[1], a[2]*b[0] - a[0]*b[2], a[0]*b[1] - a[1]*b[0]]


files = [SELF]
packets = {}
combined_pins = {}
for name, count, expected in [
    ("revised-base-audit-v1", 1120, "1205472ce4f96626318b42f2ad7578396485d167932f22fc0af387b156c4f875"),
    ("connected-stack-followup-v1", 1126, "d81540a6c69b98f1182a6d2649d9a0d39126756ea94f0b3cd691026de7cb94d1"),
]:
    directory = DOC / name
    files.extend(directory / item for item in ["README.md", "analyze.py", "inputs.json", "result.json", "verification.json"])
    result, verification = read(directory / "result.json"), read(directory / "verification.json")
    assert sha(directory / "result.json") == expected
    raw_path = Path(verification["raw_details"]["path"])
    assert sha(raw_path) == verification["raw_details"]["sha256"]
    details = read(raw_path)
    files.append(raw_path)
    pins = details["complete_source_sha256"]
    assert len(pins) == count == result["source_pin_count"] == verification["checks"]["all_source_pins_verified"]
    assert canonical(pins) == result["complete_source_canonical_sha256"]
    assert len(verification["owned_artifacts"]) == 4
    for path, record in verification["owned_artifacts"].items():
        assert sha(path) == record["sha256"]
        assert Path(path).stat().st_size == record["bytes"]
    for path, digest in pins.items():
        assert path not in combined_pins or combined_pins[path] == digest
        combined_pins[path] = digest
    assert (directory / "result.json").read_bytes() == (raw_path.parent / "result.json").read_bytes()
    assert all(value is False for value in result["execution"].values())
    assert result["fabrication_or_climbing_release"] is False
    for key in ["native_solve", "new_response", "physical_observation"]:
        assert verification[key] is False
    packets[name] = (result, verification, details)
assert len(combined_pins) == 1126
for path, expected in combined_pins.items():
    assert sha(path) == expected, path
source_sha256 = {str(path): sha(path) for path in files}

audit, audit_verification, audit_details = packets["revised-base-audit-v1"]
connected, connected_verification, connected_details = packets["connected-stack-followup-v1"]
assert audit["current_geometry_revision"] == connected["target_geometry_revision_not_evaluated"] == "eoere-midpoint-ready-frame-v3"
assert audit["six_field_geometry_revision"] == connected["source_geometry_revision"] == "eoere-bottom-rail-tnut-clearance-v1"
assert audit["geometry_delta"]["current_response_exists_in_this_packet"] is False
assert len(audit["geometry_delta"]["moved_shafts"]) == 22
assert len(audit["geometry_delta"]["moved_screws"]) == 10
assert len(audit["geometry_delta"]["unchanged_starting_frame_bolt_ids"]) == 12
assert audit["washer_support"]["total_wood_seats"] == 112
assert audit["washer_support"]["fresh_changed_host_probes"] == 36
assert audit["washer_support"]["unchanged_seat_proofs_reused"] == 76
assert audit["washer_support"]["failed_seat_ids"] == []
assert len(audit_details["washer_seat_rows"]) == 112
ring_errors = []
for row in audit_details["washer_seat_rows"]:
    assert row["full_modeled_support"] is True
    if "current_host_support_point_xyz_mm" in row:
        expected = math.pi/4 * (row["bounding_OD_mm"]**2 - row["bounding_inner_diameter_mm"]**2) * row["probe_depth_mm"]
        ring_errors.append(abs(expected - row["expected_probe_volume_mm3"]))
        assert row["old_force_used_as_new_response"] is False
assert len(ring_errors) == 36 and max(ring_errors) < 1e-10
station_errors = []
for member in audit["candidate_member_restraint_paths"]:
    stations = [0.0, *member["candidate_stations_mm"], member["gross_length_mm"]]
    gaps = [b-a for a, b in zip(stations, stations[1:])]
    station_errors.extend(abs(a-b) for a, b in zip(gaps, member["end_and_interior_geometric_gaps_mm"]))
    assert abs(max(gaps) - member["largest_candidate_gap_mm"]) < 1e-10
    assert member["effective_length_adopted"] is False and member["Cp_adopted"] is False
assert len(audit["candidate_member_restraint_paths"]) == 4 and max(station_errors) < 1e-10
assert len(audit_details["unsupported_stack_own_case_ports"]) == 48
assert all(row["complete_joint_reference_n"] is None for row in audit_details["unsupported_stack_own_case_ports"])
assert all(row["complete_joint_reference_n"] is None for row in audit["group_applicability"]["unsupported_shafts"])
assert audit["reused_cleat_component_screens"]["actual_all_mode_current_cleat_resistance_n"] is None

# Extract only pure scalar/fixture functions; avoid producer imports and run().
connected_source = DOC / "connected-stack-followup-v1/analyze.py"
tree = ast.parse(connected_source.read_text())
functions = [node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name in ["line_bound", "bearing_trial", "known_answers"]]
namespace = {"math": math, "np": np, "parent": SimpleNamespace(require=require)}
exec(compile(ast.Module(body=functions, type_ignores=[]), str(connected_source), "exec"), namespace)
fixture_result = namespace["known_answers"]()
assert fixture_result == connected["known_answers"]
assert len(fixture_result["rejection_controls"]) == 7
bound = namespace["line_bound"]
scalar_errors = []
for length in [1.5, 10.0, 38.1, 88.9]:
    for force in [-100.0, 0.0, 100.0]:
        for moment in [-100.0, 0.0, 100.0]:
            q = bound(length, force, moment)
            if q:
                scalar_errors.append(abs(q * length**2/4 - force**2/(4*q) - abs(moment)))
            else:
                assert force == moment == 0
assert max(scalar_errors) < 1e-10

original = read(DOC / "inputs.json")
force_errors, moment_errors, peak_errors, scalar_lower_errors = [], [], [], []
case_axis_keys = set()
for case in original["cases"]:
    manifest = read(case["manifest"]["path"])
    field = read(manifest["field"]["path"])
    shafts = {row["axis_id"]: row for row in field["source_inputs"]["shafts"]}
    ports = {(row["axis_id"], row["surface_index"]): row for key in ["common_shaft_wood_bearing_actions", "common_shaft_steel_port_actions"] for row in field[key]}
    for row in connected_details["member_bearing_trials"]:
        if row["case_id"] != case["case_id"]:
            continue
        key = (row["case_id"], row["axis_id"], row["surface_index"])
        assert key not in case_axis_keys
        case_axis_keys.add(key)
        shaft, port = shafts[row["axis_id"]], ports[row["axis_id"], row["surface_index"]]
        assert row["host"] == port["host"]
        lo, hi = port["surface_interval_mm"]
        assert row["interval_from_axis_point_mm"] == [lo, hi]
        length, g = hi-lo, shaft["basis"][0]
        center = add(shaft["point"], scale(g, (lo+hi)/2))
        full_force = port["force_on_host_xyz_n"]
        force = sub(full_force, scale(g, dot(g, full_force)))
        moment = add(port["moment_on_host_at_point_xyz_nmm"], cross(sub(port["point_xyz_mm"], center), full_force))
        left, right = row["affine_endpoint_line_density_vectors_n_mm"]
        force_errors.append(norm(sub(scale(add(left, right), length/2), force)))
        moment_errors.append(norm(sub(cross(g, scale(sub(right, left), length**2/12)), moment)))
        peak = max(norm(left), norm(right))
        peak_errors.append(abs(peak-row["affine_trial_peak_line_density_n_mm"]))
        first = scale(cross(g, moment), -1)
        directions = list(shaft["basis"][1:])
        directions += [scale(vector, 1/norm(vector)) for vector in [force, first] if norm(vector) > 1e-10]
        lower = max(bound(length, dot(force, direction), dot(first, direction)) for direction in directions)
        scalar_lower_errors.append(abs(lower-row["necessary_directional_peak_line_density_bound_n_mm"]))
        assert peak + 1e-8 >= lower
        assert row["deformation_compatibility_or_yield_capacity_established"] is False
        assert abs(peak / row["bearing_screen_D_mm"] - row["affine_trial_peak_projected_bearing_mpa"]) < 1e-10
        if row["kind"] == "wood":
            assert abs(row["affine_trial_peak_projected_bearing_mpa"] / row["DFL_Fe90_material_parameter_mpa"] - row["affine_peak_over_Fe90_parameter"]) < 1e-10
        else:
            assert row["eoere_product_bearing_resistance_mpa"] is None
assert len(case_axis_keys) == 144 and max(force_errors) < 1e-8 and max(moment_errors) < 1e-5
assert max(peak_errors) < 1e-10 and max(scalar_lower_errors) < 1e-8
assert len(connected_details["connected_stacks"]) == 48
assert len({(row["case_id"], row["axis_id"]) for row in connected_details["connected_stacks"]}) == 48
assert all(row["current_geometry_response_or_joint_capacity"] is None for row in connected_details["connected_stacks"])
assert all(row["adjusted_complete_joint_resistance_n"] is None for row in connected["stacks"])
assert len(connected["stacks"]) == 8
for item in ["result.json", "details.json"]:
    assert (RAW/"connected-stack-followup-v1/attempt02"/item).read_bytes() == (RAW/"connected-stack-followup-v1/replay"/item).read_bytes()
for path, expected in combined_pins.items():
    assert sha(path) == expected, path
for path, expected in source_sha256.items():
    assert sha(path) == expected, path

finding = {"severity": "medium", "category": "testing/provenance",
    "file": str(DOC/"revised-base-audit-v1/verification.json"), "line": 4,
    "description": "Independent saved-solid interval and arithmetic checks are recorded without a retained source-bound checker or reproduction command. The retained analyze.py checks interval translation using the same canonical_interval_shift helper as the geometry producer and does not perform the claimed independent twelve-interval saved-BREP bounds check.",
    "supporting_lines": [11, 12, 13, 19],
    "impact": "The independent 0.000000101-mm interval comparison and arithmetic verification metrics cannot be reproduced or reviewed from the retained implementation; rerunning the documented producer does not recreate that verification layer.",
    "fix": "Retain the small checker in the ignored raw packet and record its hash and exact command in supplemental verification evidence, or narrow claims to checks whose implementation is retained. Preserve frozen packet bytes."}
receipt = {"schema": "eoere_current_geometry_strength_followup_testing_review/v1",
    "status": "PASS_CHEAP_SCALAR_AND_BINDING_CHECKS_WITH_PROVENANCE_FINDING", "findings": [finding],
    "source_sha256": source_sha256,
    "pin_maps": [{"packet": name, "pins": result["source_pin_count"], "canonical_sha256": result["complete_source_canonical_sha256"]} for name, (result, _, _) in packets.items()],
    "unique_source_files_verified_before_and_after": len(combined_pins),
    "checks": {"changed_host_ring_arithmetic_rows": len(ring_errors), "maximum_ring_volume_error_mm3": max(ring_errors),
        "brace_station_paths": 4, "maximum_station_gap_error_mm": max(station_errors),
        "producer_known_answer_fixture_rejections": fixture_result["rejection_controls"],
        "independent_scalar_bound_fixtures": 36, "maximum_scalar_bound_identity_error": max(scalar_errors),
        "independent_saved_endpoint_integrals": len(force_errors), "maximum_endpoint_force_error_n": max(force_errors),
        "maximum_endpoint_moment_error_nmm": max(moment_errors), "maximum_endpoint_density_error_n_mm": max(peak_errors),
        "maximum_directional_lower_bound_error_n_mm": max(scalar_lower_errors), "saved_connected_outputs_byte_equal_to_replay": True,
        "all_eight_complete_joint_resistances_null": True},
    "limits": ["Old six-case fields only; no extended-cleat geometry or current/revised force response evaluated.",
        "No CAD/BRep/native/global/browser runs, producer rerun, dependency install or full suite.",
        "Scalar replay does not establish compatibility, yield, NDS/ASD capacity or physical release; panel remedies remain paused."],
    "runtime": {"python": sys.version.split()[0], "numpy": np.__version__}, "command": sys.argv}
with OUTPUT.open("x") as stream:
    stream.write(json.dumps(receipt, indent=2, sort_keys=True, allow_nan=False)+"\n")
print(json.dumps({"receipt": str(OUTPUT), "sha256": sha(OUTPUT), "findings": len(receipt["findings"]), "pins": len(combined_pins)}))
