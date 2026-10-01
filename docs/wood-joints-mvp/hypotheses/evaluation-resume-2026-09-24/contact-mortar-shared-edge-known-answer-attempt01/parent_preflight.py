"""Synthetic, no-solver preflight for the shared-edge known-answer verifier."""

from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import tempfile

import verifier


HERE = Path(__file__).resolve().parent
EXPECTED = verifier.read_json(HERE / "expected.json")
TIME = 1.0


def synthetic_fields(deck):
    """Return independent linear oracle U and balanced uniform face reactions."""
    fixture = EXPECTED["fixture"]
    groups = fixture["body_node_groups"]
    nodes = deck["nodes"]
    displacement = {node: [0.0, 0.0, 0.0] for node in nodes}
    for node in groups["CENTRAL"]:
        x, _, z = nodes[node]
        displacement[node][0] = -3e-5 - 1e-5 * x
        displacement[node][2] = -3e-5 - 1e-5 * z
    for node in groups["LEFT"]:
        x, _, _ = nodes[node]
        displacement[node][0] = -1e-5 * (x + 2.0)
    for node in groups["LOWER"]:
        _, _, z = nodes[node]
        displacement[node][2] = -1e-5 * (z + 2.0)

    reactions = {node: [0.0, 0.0, 0.0] for node in nodes}
    support_groups = EXPECTED["load_and_reaction_oracle"][
        "support_reaction_dof_groups"]
    for name in ("LEFT_REMOTE_NORMAL", "LOWER_REMOTE_NORMAL"):
        group = support_groups[name]
        force = group["expected_sum_N"] / len(group["nodes"])
        dof = group["dof"] - 1
        for node in group["nodes"]:
            reactions[node][dof] += force
    return {
        (TIME, "displacements"): {
            node: tuple(values) for node, values in displacement.items()
        },
        (TIME, "forces"): {
            node: tuple(values) for node, values in reactions.items()
        },
    }


def call_known_answer(case, deck, fields, expected):
    return verifier.audit_known_answer(
        case,
        {"step": 1, "increment": 1, "total": TIME},
        deck,
        expected,
        fields,
    )


def rejected(call, expected_text):
    try:
        call()
    except Exception as exc:
        return expected_text in str(exc), str(exc)
    return False, "unexpected pass"


def parser_rejections(node_ids):
    results = {}
    for label, value, phrase in (
        ("missing_node", "0.0", "Incomplete DAT node coverage"),
        ("nonfinite", "nan", "Nonfinite numeric evidence"),
    ):
        with tempfile.TemporaryDirectory(prefix="shared-edge-preflight-") as temp:
            path = Path(temp) / "synthetic.dat"
            rows = []
            omitted = max(node_ids)
            for node in sorted(node_ids):
                if label == "missing_node" and node == omitted:
                    continue
                row = value if label == "nonfinite" and node == min(node_ids) else "0.0"
                rows.append(f"{node} {row} 0.0 0.0")
            path.write_text(
                "displacements for set ALLNODES and time 1.000000E+00\n"
                + "\n".join(rows)
                + "\n"
            )
            ok, detail = rejected(
                lambda: verifier.parse_dat(path, set(node_ids)), phrase
            )
            results[label] = {"rejected_as_expected": ok, "detail": detail}
    return results


def run():
    reports = {}
    errors = []
    key = "normal_compliance_relative_tolerance"
    # Derive these already-declared numeric tolerances only for the perturbation
    # tests; the frozen expected.json itself remains untouched.
    synthetic_expected = deepcopy(EXPECTED)
    synthetic_expected["analytical_known_answer"].setdefault(key, 0.01)
    synthetic_expected["analytical_known_answer"].setdefault(
        "normal_compliance_absolute_tolerance_mm3_per_N", 1e-10
    )

    for case in EXPECTED["case_order"]:
        spec = EXPECTED["cases"][case]
        deck = verifier.audit_deck(case, spec, EXPECTED)
        fields = synthetic_fields(deck)
        report = {
            "deck_audit": "PASS",
            "shared_node_roles": deck["role_checks"],
        }
        try:
            call_known_answer(case, deck, fields, EXPECTED)
            report["known_answer_original_expected"] = "PASS"
        except Exception as exc:
            report["known_answer_original_expected"] = f"FAIL: {exc}"
            errors.append(f"{case} original expected: {exc}")

        try:
            call_known_answer(case, deck, fields, synthetic_expected)
            report["known_answer_with_declared_gate_values"] = "PASS"
        except Exception as exc:
            report["known_answer_with_declared_gate_values"] = f"FAIL: {exc}"
            errors.append(f"{case} declared gates: {exc}")

        bad_u = deepcopy(fields)
        target_node = min(EXPECTED["fixture"]["body_node_groups"]["CENTRAL"])
        bad_u[(TIME, "displacements")][target_node] = tuple(
            value + (2e-7 if dof == 0 else 0.0)
            for dof, value in enumerate(
                bad_u[(TIME, "displacements")][target_node]
            )
        )
        ok, detail = rejected(
            lambda: call_known_answer(case, deck, bad_u, synthetic_expected),
            "Normal displacement profile exceeds",
        )
        report["over_tolerance_displacement_rejected"] = {
            "rejected_as_expected": ok,
            "detail": detail,
        }

        bad_rf = deepcopy(fields)
        node = synthetic_expected["load_and_reaction_oracle"][
            "support_reaction_dof_groups"
        ]["LEFT_REMOTE_NORMAL"]["nodes"][0]
        vector = list(bad_rf[(TIME, "forces")][node])
        vector[0] += 0.05
        bad_rf[(TIME, "forces")][node] = tuple(vector)
        ok, detail = rejected(
            lambda: call_known_answer(case, deck, bad_rf, synthetic_expected),
            "Support reaction group LEFT_REMOTE_NORMAL differs",
        )
        report["over_tolerance_force_rejected"] = {
            "rejected_as_expected": ok,
            "detail": detail,
        }
        for name in ("over_tolerance_displacement_rejected",
                     "over_tolerance_force_rejected"):
            if not report[name]["rejected_as_expected"]:
                errors.append(f"{case} {name}: {report[name]['detail']}")
        reports[case] = report

    parser = parser_rejections(
        {int(node) for node in EXPECTED["fixture"]["node_coordinates_mm"]}
    )
    for name, report in parser.items():
        if not report["rejected_as_expected"]:
            errors.append(f"{name}: {report['detail']}")

    result = {
        "classification": "synthetic_parser_and_arithmetic_checks_only",
        "native_execution": False,
        "verifier_sha256": verifier.sha(Path(verifier.__file__)),
        "cases": reports,
        "parser_negative_checks": parser,
        "errors": errors,
        "status": "PASS_PREFLIGHT" if not errors else "BLOCKED_BY_VERIFIER",
    }
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(run())
