"""Source-only publication verification, reusing the completed exact replay.

No resistance calculation, CAD query, mechanics run, or library suite is run.
Only derived negative-control manifests and this receipt are written here.
"""

from __future__ import annotations

import ast
import copy
import hashlib
import importlib.util
import json
import math
from collections import Counter
from pathlib import Path

OWN = Path(__file__).resolve().parent
ROOT = next(p for p in OWN.parents if (p / "current-candidate.json").is_file())
BASE = ROOT / (
    "docs/wood-joints-mvp/hypotheses/hl35-candidate/thin-frame-comparison/"
    "eoere-successor-v1/bounded-strength-v1"
)
PACKET = BASE / "resistance-followup-v1"
RAW = ROOT / (
    "fea/generated/thin-bolted-current-contact-v1/eoere-successor-v1/"
    "bounded-strength-v1/resistance-followup-v1/attempt02"
)
REVIEW = OWN.parent / "resistance-followup-review-v1"
CASES = ["a12-rear", "a12-forward", "a12-left", "k12-right", "k12-rear", "a1-rear"]


def require(ok, message):
    if not ok:
        raise ValueError(message)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    return json.loads(Path(path).read_bytes())


def canonical(value):
    return hashlib.sha256(
        json.dumps(
            value, sort_keys=True, separators=(",", ":"), allow_nan=False
        ).encode()
    ).hexdigest()


def snapshot():
    paths = [
        d / n
        for d in (BASE, PACKET)
        for n in (
            "README.md",
            "analyze.py",
            "inputs.json",
            "result.json",
            "verification.json",
        )
    ]
    paths += [
        REVIEW / n
        for n in (
            "review.py",
            "review-result.json",
            "replay/result.json",
            "replay/details.json",
        )
    ]
    paths += [
        ROOT / n
        for n in (
            "tests/test_bolted_timber_checks.py",
            "tests/test_reinforced_timber_resistance.py",
        )
    ]
    return {str(p.relative_to(ROOT)): sha(p) for p in paths}


def refs(value):
    if isinstance(value, dict):
        if isinstance(value.get("path"), str) and isinstance(value.get("sha256"), str):
            yield value["path"], value["sha256"]
        for row in value.values():
            yield from refs(row)
    elif isinstance(value, list):
        for row in value:
            yield from refs(row)


def finite(value):
    if isinstance(value, float):
        return math.isfinite(value)
    if isinstance(value, dict):
        return all(finite(row) for row in value.values())
    if isinstance(value, list):
        return all(finite(row) for row in value)
    return True


def declared_test_count(path):
    count = 0
    for node in ast.parse(Path(path).read_bytes()).body:
        if isinstance(node, ast.FunctionDef) and node.name.startswith("test_"):
            own = 1
            for decorator in node.decorator_list:
                if (
                    isinstance(decorator, ast.Call)
                    and isinstance(decorator.func, ast.Attribute)
                    and decorator.func.attr == "parametrize"
                ):
                    require(
                        isinstance(decorator.args[1], (ast.List, ast.Tuple)),
                        "nonliteral test case list",
                    )
                    own *= len(decorator.args[1].elts)
            count += own
    return count


def main():
    before = snapshot()
    inputs, result, verification, peer = [
        read(p)
        for p in (
            PACKET / "inputs.json",
            PACKET / "result.json",
            PACKET / "verification.json",
            REVIEW / "review-result.json",
        )
    ]
    original = read(ROOT / inputs["original_inputs"]["path"])
    details = read(RAW / "details.json")
    pins = details["complete_source_sha256"]
    binding = {
        "pin_count": len(pins),
        "canonical_sha256": canonical(pins),
        "verified_before_after": True,
    }
    require(
        binding
        == result["source_binding"]
        == verification["source_binding"]
        == peer["source_binding"],
        "source-map identities differ",
    )
    require(len(pins) == 1071, "source pin count differs")
    source_bytes = 0
    for path, digest in pins.items():
        require(sha(ROOT / path) == digest, "source mismatch before review: " + path)
        source_bytes += (ROOT / path).stat().st_size
    require(
        sha(REVIEW / "review.py") == peer["review_source_sha256"],
        "independent review source differs",
    )
    require(
        peer["confirmed_blockers"] == []
        and peer["once_only_original_replay"]["exact_bytes"],
        "existing review/replay failed",
    )
    for path, digest in peer[
        "preserved_original_packet_review_and_followup_sha256_before_after"
    ].items():
        require(sha(ROOT / path) == digest, "previous review snapshot differs: " + path)
    for path, artifact in verification["owned_artifacts"].items():
        require(
            sha(ROOT / path) == artifact["sha256"]
            and (ROOT / path).stat().st_size == artifact["bytes"],
            "owned artifact binding differs",
        )
    artifact_bindings = {}
    for name, artifact in verification["artifacts"].items():
        actual = ROOT / artifact["path"]
        require(actual == RAW / name, "issued output path differs")
        require(
            sha(actual) == artifact["sha256"]
            and actual.stat().st_size == artifact["bytes"],
            "issued output binding differs",
        )
        require(
            actual.read_bytes() == (REVIEW / "replay" / name).read_bytes(),
            "existing exact replay bytes differ",
        )
        require(
            artifact["recomputed_serialized_bytes_identical"] is True,
            "original reproduction assertion absent",
        )
        artifact_bindings[name] = {
            "path": artifact["path"],
            "sha256": sha(actual),
            "bytes": actual.stat().st_size,
            "existing_replay_bytes_identical": True,
        }
    require(
        (PACKET / "result.json").read_bytes() == (RAW / "result.json").read_bytes(),
        "published compact result differs from issued output",
    )
    for value in (
        inputs,
        original,
        {"washers": details["washers"], "cleats": details["cleats"]},
    ):
        for path, digest in refs(value):
            require(
                pins.get(path) == digest, "direct or used-solid pin absent: " + path
            )
    required = [
        "mini_moonboard/bolted_timber_checks.py",
        "fea/reinforced_timber_resistance.py",
        "scripts/thin_bolted_timber_common_shaft_checks.py",
        "scripts/thin_bolted_steel_resistance.py",
        "scripts/thin_bolted_timber_demand_checks.py",
        "pyproject.toml",
        "uv.lock",
    ]
    require(
        all(path in pins for path in required),
        "required shared code or dependency pin missing",
    )
    require(
        result["case_ids"] == CASES == [r["case_id"] for r in original["cases"]],
        "case closure differs",
    )
    current, old = [
        read(ROOT / original[k]["path"]) for k in ("current_geometry", "old_geometry")
    ]
    require(
        current["revision"]
        == result["current_geometry"]
        == "eoere-grid-aligned-wire-cutouts-v1",
        "local revision differs",
    )
    require(
        old["revision"] == "eoere-bottom-rail-tnut-clearance-v1"
        and result["response_geometry"] == original["old_geometry"],
        "force revision differs",
    )
    require(
        current["mechanics_ready"] is False
        and current["axes"] == old["axes"]
        and current["screw_axes"] == old["screw_axes"],
        "geometry/response boundary differs",
    )
    require(
        result["load_contract"] == original["load_contract"], "load contract differs"
    )
    manifests, case_closure, issuance_metadata = [], [], {}
    for spec in original["cases"]:
        manifest = read(ROOT / spec["manifest"]["path"])
        manifests.append(manifest)
        field_bytes = (ROOT / manifest["field"]["path"]).read_bytes()
        field = json.loads(field_bytes)
        receipt = read(ROOT / manifest["admission"]["path"])
        for kind in ("field", "admission", "gate", "geometry"):
            path, digest = manifest[kind]["path"], manifest[kind]["sha256"]
            require(pins.get(path) == digest, "intake manifest reference absent: " + path)
        for kind in ("issuer", "reused_reference_helper"):
            row = manifest[kind]
            require(sha(ROOT / row["path"]) == row["sha256"], "issuance metadata source differs")
            issuance_metadata[row["path"]] = row["sha256"]
        require(
            set(manifest["expected"]) == {"state_id", "case_id", "accessory_placement"},
            "manifest expected contract differs",
        )
        for key, value in manifest["expected"].items():
            require(
                field[key] == receipt[key] == value,
                "field/receipt/manifest identity differs",
            )
        require(field["case_id"] == spec["case_id"], "own case differs")
        require(
            receipt["declared_fixed_floor_equilibrium_and_recovery_pass"] is True,
            "issued admission missing",
        )
        require(
            receipt["input_raw_sha256"]
            == hashlib.sha256(field_bytes).hexdigest()
            == manifest["field"]["sha256"],
            "raw receipt field binding differs",
        )
        require(
            receipt["input_canonical_sha256"] == canonical(field),
            "canonical receipt field binding differs",
        )
        require(
            receipt["source_path"] == manifest["gate"]["path"]
            and receipt["admission_source_sha256"] == manifest["gate"]["sha256"],
            "genuine gate identity differs",
        )
        require(
            field["source_inputs"]["geometry"]["report"]
            == manifest["geometry"]
            == original["old_geometry"],
            "field source geometry differs",
        )
        for table, digest in receipt["table_canonical_sha256"].items():
            require(
                canonical(field[table]) == digest, "signed action table binding differs"
            )
        for source in (field["source_sha256"], receipt["source_sha256"]):
            require(
                all(pins.get(path) == digest for path, digest in source.items()),
                "case source closure incomplete",
            )
        require(
            not any(field["release"].values()) and not any(receipt["release"].values()),
            "source acceptance released",
        )
        for kind in ("timber", "washers"):
            report = read(ROOT / spec["reports"][kind]["path"])
            require(report["case_id"] == spec["case_id"], "cross-case report")
            require(
                report["source_sha256"].get(manifest["field"]["path"])
                == manifest["field"]["sha256"],
                "report own-field binding absent",
            )
            require(
                all(
                    pins.get(path) == digest
                    for path, digest in report["source_sha256"].items()
                ),
                "report source closure incomplete",
            )
        case_closure.append(
            {
                "case_id": spec["case_id"],
                "state_id": field["state_id"],
                "field_sha256": manifest["field"]["sha256"],
                "admission_sha256": manifest["admission"]["sha256"],
                "signed_action_tables": len(receipt["table_canonical_sha256"]),
                "field_source_pins": len(field["source_sha256"]),
                "admission_source_pins": len(receipt["source_sha256"]),
            }
        )
    require(
        finite(result) and finite(details), "nonfinite serialized calculation value"
    )
    known = result["known_answers"]
    require(
        known
        == verification["known_answers"]
        == peer["known_answers_reused_in_original_replay"],
        "known-answer receipts differ",
    )
    require(
        known["near_and_exact_5d_references_n"] == [5.0, 20.0]
        and known["invalid_input_rejections"] == 3,
        "reduced-depth controls differ",
    )
    require(
        abs(known["independent_washer_area_reference_lbf"] - 625 * math.pi / 4 * 0.75)
        < 1e-10,
        "independent annulus known answer differs",
    )
    require(
        all(
            abs(actual - expected) < 1e-12
            for actual, expected in zip(
                known["full_gap_clipped_probe_fractions"], [1, 0, 0.5], strict=True
            )
        ),
        "CAD control known answers differ",
    )
    rows = details["washers"]["own_case_component_rows"]
    seats = details["washers"]["seat_geometry"]
    require(
        Counter(r["case_id"] for r in rows) == Counter({case: 560 for case in CASES}),
        "washer six-case row coverage differs",
    )
    require(
        len(seats) == len({r["capture_id"] for r in seats}) == 112
        and all(r["full_modeled_support"] for r in seats),
        "washer unique/full support census differs",
    )
    require(
        sum("solid_source" in r for r in seats) == 44
        and sum("byte-identical" in r["proof"] for r in seats) == 60
        and sum(r["host"].startswith("eoere_cleat") for r in seats) == 8,
        "washer proof split differs",
    )
    require(
        Counter(r["case_id"] for r in details["cleats"]["reduced_depth_shear"])
        == Counter({case: 4 for case in CASES}),
        "cleat section row closure differs",
    )
    require(
        Counter(
            r["case_id"] for r in details["cleats"]["parallel_single_bolt_row_tearout"]
        )
        == Counter({case: 8 for case in CASES}),
        "cleat bolt row closure differs",
    )
    require(
        result["bolt_yield_components"]["reused_issued_component_rows"] == 552,
        "inherited bolt comparison count differs",
    )
    require(
        not any(result["release"].values())
        and result["cleat_member_components"][
            "actual_all_mode_current_cleat_resistance_n"
        ]
        is None
        and result["bolt_yield_components"][
            "adjusted_oblique_group_or_shared_stack_reference_n"
        ]
        is None,
        "complete resistance/release boundary changed",
    )
    tests = {
        path: {
            "sha256": sha(ROOT / path),
            "declared_cases": declared_test_count(ROOT / path),
        }
        for path in (
            "tests/test_bolted_timber_checks.py",
            "tests/test_reinforced_timber_resistance.py",
        )
    }
    require(
        sum(r["declared_cases"] for r in tests.values())
        == verification["checks"]["passed"]
        == 52
        and verification["checks"]["failed"] == 0,
        "library test census/assertion differs",
    )
    # Genuine pure intake is used only to reject altered identity/path/receipt inputs.
    module_path = ROOT / original["helpers"]["admission"]
    spec = importlib.util.spec_from_file_location(
        "publication_negative_intake", module_path
    )
    intake = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(intake)
    negatives = []
    bad_path = OWN / "_negative_manifest.json"
    alterations = []
    bad = copy.deepcopy(manifests[0])
    bad["field"]["sha256"] = "0" * 64
    alterations.append(
        ("wrong exact field hash", bad, "exact manifest artifact required: field")
    )
    bad = copy.deepcopy(manifests[0])
    bad["field"]["path"] = "/tmp/outside-resistance-publication-review.json"
    alterations.append(
        ("absolute artifact path", bad, "manifest paths must be repository-relative")
    )
    bad = copy.deepcopy(manifests[0])
    bad["admission"] = copy.deepcopy(manifests[1]["admission"])
    alterations.append(
        (
            "other case's genuine admission receipt",
            bad,
            "source-bound actual fixed-floor field/receipt pair required",
        )
    )
    bad = copy.deepcopy(manifests[0])
    bad["expected"]["case_id"] = "k12-right"
    alterations.append(
        ("wrong expected own case", bad, "manifest own field identity differs: case_id")
    )
    try:
        for label, altered, expected_message in alterations:
            bad_path.write_text(json.dumps(altered, sort_keys=True) + "\n")
            try:
                intake.load_admitted(bad_path)
            except ValueError as exc:
                require(
                    str(exc) == expected_message,
                    "negative control failed for unintended reason: " + label,
                )
                negatives.append(
                    {"control": label, "rejected": True, "message": str(exc)}
                )
            else:
                raise ValueError("invalid intake accepted: " + label)
    finally:
        bad_path.unlink(missing_ok=True)
    for path, digest in pins.items():
        require(sha(ROOT / path) == digest, "source mismatch after review: " + path)
    for path, digest in issuance_metadata.items():
        require(sha(ROOT / path) == digest, "issuance metadata source changed during review")
    require(snapshot() == before, "existing source/output/test bytes changed")
    receipt = {
        "schema": "eoere_resistance_publication_source_verification/v1",
        "status": "PASS_NO_CONFIRMED_SUBSTANTIAL_VERIFICATION_OR_SOURCE_INTAKE_OMISSION",
        "scope": "Six fixed old raised-rail fields and preserved aligned-wire local geometry only; adjusted base, unofficial 2026 grid, actual complete joint resistance and release are excluded.",
        "confirmed_findings": [],
        "source_binding": binding,
        "source_bytes_verified_twice": source_bytes,
        "artifact_bindings": artifact_bindings,
        "case_closure": case_closure,
        "descriptive_issuance_sources_sha256_verified_before_after": issuance_metadata,
        "known_answers_reused_from_once_only_exact_replay": known,
        "new_genuine_source_intake_negative_controls": negatives,
        "library_tests": {
            "saved_result_reused": {
                "passed": 52,
                "failed": 0,
                "command": verification["checks"]["command"],
            },
            "current_named_test_source_census": tests,
            "rerun": False,
        },
        "independent_replay": {
            "path": str((REVIEW / "review-result.json").relative_to(ROOT)),
            "sha256": sha(REVIEW / "review-result.json"),
            "review_source_sha256": sha(REVIEW / "review.py"),
            "full_replay_repeated": False,
        },
        "coverage": {
            "direct_input_and_used_solid_pins": True,
            "required_helper_and_dependency_pins": required,
            "admission_action_table_bindings": 66,
            "own_timber_and_washer_report_bindings": 12,
            "unique_wood_washer_seats": 112,
            "washer_rows": len(rows),
            "cleat_shear_rows": 24,
            "cleat_tearout_rows": 48,
            "cleat_reused_net_tension_section_rows": len(
                details["cleats"]["net_parallel_tension"]
            ),
            "inherited_bolt_comparisons": 552,
            "finite_outputs": True,
            "null_complete_resistance_and_false_release_preserved": True,
        },
        "limits": [
            "Known CAD/full-gap-edge and mechanical arithmetic controls are reused from the authenticated once-only replay; no CAD probes or calculation replay are repeated.",
            "The saved 52-pass library assertion is reused. This review additionally inspects the present test sources and independently counts 43+9 cases; it does not claim a fresh execution.",
            "MTC application precedent remains descriptive primary-source context, not an adopted product capacity or calculation input.",
        ],
        "preserved_files_sha256_before_after": before,
        "review_source_sha256": sha(__file__),
        "execution": {
            "CAD_query_or_rebuild": False,
            "native_or_global_solve": False,
            "mechanical_calculation_replay": False,
            "global_or_library_test_run": False,
            "source_only_negative_control_manifests_created_then_removed": len(
                negatives
            ),
            "target_or_shared_document_edits": False,
            "git_mutation": False,
            "archive_or_prune": False,
        },
        "retention": "Only this compact helper and receipt are new ignored review evidence. Existing issued details, once-only replay, source cache and frozen packet stay active; nothing is pruned.",
    }
    (OWN / "review-result.json").write_text(
        json.dumps(receipt, indent=2, sort_keys=True, allow_nan=False) + "\n"
    )
    print(
        json.dumps(
            {
                "status": receipt["status"],
                "source_pins": len(pins),
                "negative_controls": len(negatives),
                "review_source_sha256": sha(__file__),
                "review_receipt_sha256": sha(OWN / "review-result.json"),
            }
        )
    )


if __name__ == "__main__":
    main()
