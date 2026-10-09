"""Verify the immutable six-case capture without preparing or solving a model.

This final publication check reads actual saved fields and admissions. It
checks their bytes, table/q bindings, residual summaries, floor force closure,
source closure and serial process timestamps. It relies on the separately
issued admission for full operator/work/recovery arithmetic; it does not
replace that audit or establish physical applicability or resistance.
"""

from __future__ import annotations

import argparse
import datetime
import hashlib
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[6]
OWN = Path(__file__).resolve()
ROSTER = OWN.with_name("result-v1.json")
ROSTER_SHA = "99fa0df8393bf5de70a7296fe2beccf0ca2df8270eb3d4b9f8b7c5f424ab7b91"
SEQUENCE = ["a12-forward", "a12-rear", "a12-left", "k12-right", "k12-rear", "a1-rear"]
GEOMETRY = "01ba30abe20c2efec136374b8d9a74a098a19929be3cc784b5ebcf7608e62a2d"
ADMISSION = "4916532168ba05268e164b28bb634743013b4aa7e062b7f9d345ecfafb954643"


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def canonical(value):
    return hashlib.sha256(
        json.dumps(
            value, sort_keys=True, separators=(",", ":"), allow_nan=False
        ).encode()
    ).hexdigest()


def path(name):
    item = Path(name)
    return item if item.is_absolute() else ROOT / item


def check_ref(reference):
    item = path(reference["path"])
    require(
        item.is_file() and sha(item) == reference["sha256"],
        "reference bytes changed: " + str(item),
    )
    if "bytes" in reference:
        require(item.stat().st_size == reference["bytes"], "reference size changed")
    return item


def norm(values):
    require(all(math.isfinite(value) for value in values), "nonfinite residual")
    return math.sqrt(sum(value * value for value in values))


def same(actual, expected, tolerance=1e-12):
    require(math.isfinite(actual) and math.isfinite(expected), "nonfinite comparison")
    require(
        abs(actual - expected) <= tolerance * max(1.0, abs(actual), abs(expected)),
        "scalar summary mismatch",
    )


def verify():
    require(sha(ROSTER) == ROSTER_SHA, "issued roster changed")
    roster = json.loads(ROSTER.read_bytes())
    require(roster["case_sequence"] == SEQUENCE, "wrong case roster")
    require(roster["candidate_geometry_sha256"] == GEOMETRY, "wrong geometry")
    require(
        roster["execution_serialized"] is True
        and roster["no_retries_or_alternative_masks"] is True,
        "execution declaration",
    )
    check_ref(roster["capture_helper"])
    sources = dict(roster["exact_pins_before"])
    require(sources == roster["exact_pins_after"], "capture source drift")
    summaries, previous_end = [], None
    field_bytes = operator_bytes = 0
    for case, row in zip(SEQUENCE, roster["cases"], strict=True):
        require(row["case_id"] == case, "case identity")
        references = row["references"]
        for reference in references.values():
            check_ref(reference)
        for phase in row["logs"].values():
            for reference in phase.values():
                check_ref(reference)
        field_path = path(references["field.json"]["path"])
        field = json.loads(field_path.read_bytes())
        admission = json.loads(path(references["admission.json"]["path"]).read_bytes())
        require(
            field["schema"] == "eoere_extended_cleat_fixed_floor_candidate/v1",
            "field schema",
        )
        require(
            admission["schema"]
            == "eoere_extended_cleat_fixed_floor_independent_field_admission/v1",
            "admission schema",
        )
        require(
            field["case_id"] == admission["case_id"] == case
            and field["state_id"] == admission["state_id"] == row["state_id"],
            "own state/case",
        )
        require(
            admission["current_extended_cleat_equilibrium_and_recovery_pass"] is True,
            "admission failed",
        )
        require(admission["admission_source_sha256"] == ADMISSION, "wrong gate")
        require(
            admission["input_raw_sha256"] == references["field.json"]["sha256"],
            "raw admission binding",
        )
        require(
            admission["input_canonical_sha256"] == canonical(field),
            "canonical admission binding",
        )
        for table, digest in admission["table_canonical_sha256"].items():
            require(
                canonical(field[table]) == digest, "own action table binding: " + table
            )
        response = field["response"]
        for name, values in [
            ("q", response["q"]),
            ("gradient", response["gradient_n"]),
        ]:
            require(
                len(values) == 9302 and all(math.isfinite(value) for value in values),
                "invalid saved vector",
            )
            require(
                canonical(values)
                == response[name + "_canonical_sha256"]
                == admission[name + "_canonical_sha256"],
                "own vector binding",
            )
        gradient = max(abs(value) for value in response["gradient_n"])
        same(gradient, response["gradient_inf_n"])
        same(gradient, row["gradient_inf_n"])
        require(
            response["converged"] is True and gradient <= 1e-5, "numerical convergence"
        )
        for key, count in [
            ("body_equilibrium_residuals", 150),
            ("common_shaft_section_cut_actions", 100),
            ("common_shaft_steel_port_actions", 88),
            ("panel_screw_actions", 66),
            ("panel_generalized_coefficients", 6),
            ("shaft_end_capture_actions", 200),
        ]:
            require(len(field[key]) == count, "physical census: " + key)
        force = max(
            norm(body["force_xyz_n"]) for body in field["body_equilibrium_residuals"]
        )
        moment = max(
            norm(body["moment_about_reference_xyz_nmm"])
            for body in field["body_equilibrium_residuals"]
        )
        same(force, row["body_equilibrium"]["maximum_body_force_norm_n"])
        same(
            moment,
            row["body_equilibrium"]["maximum_body_moment_about_reference_norm_nmm"],
        )
        require(force <= 1e-4 and moment <= 0.1, "body residual limits")
        global_residual = (
            field["global_equilibrium_residual_force_n"]
            + field["global_equilibrium_residual_moment_nmm"]
        )
        require(
            global_residual
            == admission["declared_law_checks"]["global_residual_n_nmm"]
            == row["global_residual_n_nmm"],
            "global closure binding",
        )
        same(norm(global_residual[:3]), row["global_force_norm_n"])
        same(norm(global_residual[3:]), row["global_moment_about_reference_norm_nmm"])
        normals = admission["normal_force_n_by_host"]
        require(
            len(normals) == 8 and all(value >= 0 for value in normals.values()),
            "unilateral normals",
        )
        credited = [normals[name] for name in ["lumber_leg_left", "lumber_leg_right"]]
        require(min(credited) > 0, "credited leg unloaded")
        for host, vector in admission["horizontal_force_xyz_n_by_host"].items():
            if host not in ["lumber_leg_left", "lumber_leg_right"]:
                require(vector[:2] == [0.0, 0.0], "uncredited XY reaction")
        applied = admission["applied_load_checks"][
            "applied_wrench_about_reference_n_nmm"
        ]
        same(sum(normals.values()) + applied[2], global_residual[2], tolerance=1e-8)
        for axis in [0, 1]:
            same(
                sum(
                    value[axis]
                    for value in admission["horizontal_force_xyz_n_by_host"].values()
                )
                + applied[axis],
                global_residual[axis],
                tolerance=1e-8,
            )
        require(
            field["current_execution"]["geometry"]["sha256"] == GEOMETRY,
            "actual geometry binding",
        )
        require(
            field["current_execution"]["historical_q_or_forces_used"] is False,
            "historical actions",
        )
        require(
            field["analytical_support_scenario"] == admission["support_contract"],
            "support contract",
        )
        for payload in [field, admission, row, roster]:
            require(
                payload["release"]
                and all(value is False for value in payload["release"].values()),
                "release claim",
            )
        for payload in [field, admission]:
            for name, digest in payload["source_sha256"].items():
                require(
                    name not in sources or sources[name] == digest,
                    "conflicting source identity",
                )
                sources[name] = digest
        producer = json.loads(path(references["process.json"]["path"]).read_bytes())
        audit_process = json.loads(
            path(references["admission-process.json"]["path"]).read_bytes()
        )
        start = datetime.datetime.fromisoformat(producer["started_at_utc"])
        produced = datetime.datetime.fromisoformat(producer["finished_at_utc"])
        audit_start = datetime.datetime.fromisoformat(audit_process["started_at_utc"])
        audit_end = datetime.datetime.fromisoformat(audit_process["finished_at_utc"])
        require(start <= produced <= audit_start <= audit_end, "case phase overlap")
        require(previous_end is None or previous_end <= start, "case overlap")
        previous_end = audit_end
        require(
            producer["exit_code"] == audit_process["exit_code"] == 0,
            "actual process failure",
        )
        field_bytes += references["field.json"]["bytes"]
        operator_bytes += (
            references["operator_arrays"]["bytes"]
            + references["operator_manifest"]["bytes"]
        )
        summaries.append(
            {
                "case_id": case,
                "state_id": field["state_id"],
                "gradient_inf_n": gradient,
                "minimum_credited_leg_normal_n": min(credited),
            }
        )
    for name, digest in sources.items():
        require(sha(path(name)) == digest, "live source mismatch: " + name)
    same(
        max(row["gradient_inf_n"] for row in summaries),
        roster["maxima"]["gradient_inf_n"],
    )
    same(
        min(row["minimum_credited_leg_normal_n"] for row in summaries),
        roster["minimum_credited_leg_normal_n"],
    )
    require(
        field_bytes == roster["total_field_bytes"]
        and operator_bytes == roster["total_operator_bytes"],
        "retained volume",
    )
    require(sha(ROSTER) == ROSTER_SHA, "roster changed during check")
    return {
        "schema": "eoere_current_six_case_parent_publication_verification/v1",
        "status": "PASS_IN_BOUNDED_SAVED_FIELD_SCOPE",
        "roster_sha256": ROSTER_SHA,
        "helper_sha256": sha(OWN),
        "cases": summaries,
        "verified_unique_source_pins": len(sources),
        "numerical_operator_audit_relied_on": ADMISSION,
        "no_preparation_or_solve": True,
        "release": roster["release"],
        "limits": [
            "Full force/work/operator recovery relies on each source-bound genuine admission.",
            "Distributed panel RHS remains source-authenticated capture, not an independent regeneration.",
            "No first-order physical applicability, pressure, floor capacity or complete-joint resistance established.",
            "All raw fields/operators and source inputs remain active; nothing pruned.",
        ],
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    with args.out.open("x") as stream:
        result = verify()
        json.dump(result, stream, sort_keys=True, indent=2, allow_nan=False)
        stream.write("\n")
    print(
        json.dumps(
            {
                "status": result["status"],
                "case_count": len(result["cases"]),
                "verified_unique_source_pins": result["verified_unique_source_pins"],
            }
        )
    )
