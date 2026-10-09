"""Source-only independent review of the frozen v3 replay gate.

Run from the repository root with .venv/bin/python -B PATH/review.py.
No CAD producer, native solve, browser or BREP query is executed.
"""

import contextlib
import hashlib
import importlib.util
import io
import json
import platform
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch


HERE = Path(__file__).resolve().parent
TARGET = Path("scripts/check_eoere_2026_replay_inputs.py")
TARGET_SHA = "d714ccb706443b6ebf4420d8ba5937d4e49612e4290b20538fd4cacaea929c76"
ISSUED = Path(
    "fea/generated/thin-bolted-current-contact-v1/eoere-successor-v1/"
    "2026-adjustments-v10/replay-gate-v2/result.json"
)
ISSUED_SHA = "a8e9efcf59fe0e4435e012c5d64a032d62e8c8a6ba4bb74f124efbaeec133266"
GEOMETRY_REVIEW = ISSUED.parents[2] / "2026-adjustments-v3-review-v1"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require_rejection(call):
    try:
        call()
    except (ValueError, FileNotFoundError) as error:
        return str(error)
    raise AssertionError("negative control was accepted")


def main():
    snapshot = HERE / "reviewed-gate.py"
    assert sha(snapshot) == TARGET_SHA
    assert sha(ISSUED) == ISSUED_SHA
    spec = importlib.util.spec_from_file_location("reviewed_gate", snapshot)
    gate = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(gate)
    frozen, pins = gate.verify()
    issued = json.loads(ISSUED.read_bytes())
    expected = {**pins, str(TARGET.resolve()): TARGET_SHA}
    assert gate.join_pins(issued["source_sha256"]) == expected
    assert len(frozen) == 570 and len(issued["rejected_controls"]) == 26
    assert issued["mode"] == "VERIFY_EXISTING_FROZEN_V3_INPUTS_ONLY"
    assert all(
        issued[name] is False
        for name in (
            "original_v3_execution_used_this_gate",
            "geometry_or_assets_reissued",
            "cad_execution_this_check",
            "native_solver",
        )
    )
    assert gate.controls() == issued["rejected_controls"]

    controls = []
    producer = str(gate.PRODUCER.resolve())
    for mode in ("missing", "changed"):
        changed = dict(frozen)
        if mode == "missing":
            changed.pop(producer)
        else:
            changed[producer] = "0" * 64
        controls.append(
            {
                "mode": mode + "_producer_replay_binding",
                "rejection": require_rejection(
                    lambda: gate.verify_replay_bindings(
                        {"source_sha256": changed}, frozen, HERE
                    )
                ),
            }
        )
    controls.append(
        {
            "mode": "relative_absolute_conflict",
            "rejection": require_rejection(
                lambda: gate.join_pins(
                    {str(gate.PRODUCER): "a" * 64}, {producer: "b" * 64}
                )
            ),
        }
    )
    controls.append(
        {
            "mode": "generated_path_escapes_output",
            "rejection": require_rejection(
                lambda: gate.verify_replay_bindings(
                    {
                        "source_sha256": {
                            **frozen,
                            str(HERE / "fresh" / ".." / "escape.brep"): "0" * 64,
                        }
                    },
                    frozen,
                    HERE / "fresh",
                )
            ),
        }
    )

    orchestration = []
    # Replace only the heavy producer and repeated already-verified input checks.
    # Synthetic reports retain every real frozen input binding. The real main()
    # path guard, post-binding validation and receipt write remain in use.
    with tempfile.TemporaryDirectory(prefix="source-only-", dir=HERE) as temporary:
        root = Path(temporary)
        for label, destination in (
            ("outside_replay", "receipt.json"),
            ("top_report_collision", "replay/geometry.json"),
            ("base_report_collision", "replay/base/geometry.json"),
        ):
            case = root / label
            replay = case / "replay"
            receipt = case / destination
            calls = []
            before = {}

            def producer_stub(command, check):
                assert check is True
                assert command == [
                    sys.executable,
                    "-B",
                    str(gate.PRODUCER),
                    "--out",
                    str(replay),
                ]
                calls.append(command)
                (replay / "base").mkdir(parents=True)
                for path, schema in (
                    (replay / "base/geometry.json", "synthetic_base_geometry"),
                    (replay / "geometry.json", "synthetic_extra_geometry"),
                ):
                    path.write_text(
                        json.dumps({"schema": schema, "source_sha256": frozen}) + "\n"
                    )
                    before[str(path)] = sha(path)

            with (
                patch.object(sys, "argv", [str(TARGET), "--out", str(receipt), "--run-out", str(replay)]),
                patch.object(gate, "verify", side_effect=lambda: (dict(frozen), dict(pins))),
                patch.object(gate, "controls", return_value=issued["rejected_controls"]),
                patch.object(gate.subprocess, "run", side_effect=producer_stub),
                contextlib.redirect_stdout(io.StringIO()),
            ):
                gate.main()
            result = json.loads(receipt.read_bytes())
            mismatches = [
                str(path)
                for path in (replay / "base/geometry.json", replay / "geometry.json")
                if sha(path) != result["source_sha256"][str(path)]
            ]
            assert len(calls) == 1
            assert result["passed"] and result["mode"] == "VERIFIED_REPLAY"
            assert bool(mismatches) == (label != "outside_replay")
            orchestration.append(
                {
                    "case": label,
                    "producer_was_stubbed_no_CAD": True,
                    "gate_returned_passed": True,
                    "generated_geometry_reports_overwritten": len(mismatches),
                    "receipt_geometry_source_hashes_still_match": not mismatches,
                    "final_receipt_schema": result["schema"],
                }
            )

        # Default mode must not invoke the producer.
        receipt = root / "default.json"
        with (
            patch.object(sys, "argv", [str(TARGET), "--out", str(receipt)]),
            patch.object(gate, "verify", return_value=(dict(frozen), dict(pins))),
            patch.object(gate, "controls", return_value=issued["rejected_controls"]),
            patch.object(gate.subprocess, "run", side_effect=AssertionError("unexpected producer execution")),
            contextlib.redirect_stdout(io.StringIO()),
        ):
            gate.main()
        default = json.loads(receipt.read_bytes())
        assert default["cad_execution_this_check"] is False
        assert default["mode"] == "VERIFY_EXISTING_FROZEN_V3_INPUTS_ONLY"

    reused = {}
    for path in (
        GEOMETRY_REVIEW / "correctness/receipt.json",
        GEOMETRY_REVIEW / "correctness/panel-bores.json",
        GEOMETRY_REVIEW / "verification/verification-result-v1.json",
        GEOMETRY_REVIEW / "verification/independent-actual-mesh-check-v1.json",
        GEOMETRY_REVIEW / "structure/receipt.json",
        Path("docs/wood-joints-mvp/README.md"),
        Path("docs/wood-joints-mvp/completion-ledger.md"),
    ):
        reused[str(path)] = sha(path)
    result = {
        "schema": "eoere_v3_replay_gate_independent_correctness/v1",
        "python_version": platform.python_version(),
        "source_sha256": {
            str(TARGET): TARGET_SHA,
            str(ISSUED): ISSUED_SHA,
            str(snapshot): sha(snapshot),
            str(Path(__file__).resolve()): sha(Path(__file__).resolve()),
            **reused,
        },
        "complete_frozen_input_count": len(frozen),
        "joined_authority_pins_excluding_gate": len(pins),
        "issued_receipt_source_bindings_match": True,
        "issued_26_rejection_controls_reproduced": True,
        "source_only_rejection_controls": controls,
        "main_orchestration_controls": orchestration,
        "default_no_CAD_control_passed": True,
        "substantial_findings": [
            {
                "priority": "P2",
                "title": "Reject receipt paths that collide with replay output files",
                "source_lines": ["scripts/check_eoere_2026_replay_inputs.py:172", "scripts/check_eoere_2026_replay_inputs.py:210"],
                "trigger": "--out FRESH_CAD_DIRECTORY/geometry.json --run-out FRESH_CAD_DIRECTORY (or the base/geometry.json report)",
                "observed": "Both paths are initially new. main() verifies and pins the producer's geometry report, then replaces that report with a passed VERIFIED_REPLAY gate receipt. Its saved geometry-source hash no longer matches the overwritten file.",
                "impact": "An allowed fresh-path invocation silently destroys a replay report and emits an internally stale receipt after a potentially expensive CAD run. This does not affect the issued source-only receipt or frozen v3 geometry.",
                "recommendation": "Resolve both paths before execution and reject a receipt inside the replay directory, or at minimum reject every producer-owned output destination. Add a source-only orchestration control before authorizing CAD execution.",
            }
        ],
        "documentation_assessment": {
            "adjusted_base_is_current_geometry_entrypoint": True,
            "unofficial_grid_assumptions_and_revision_limits_are_explicit": True,
            "original_v3_execution_not_attributed_to_gate": True,
            "optional_CAD_replay_not_claimed_run": True,
            "no_extra_substantial_documentation_findings": True,
        },
        "limits": [
            "Source bindings, arithmetic/control flow, path joins and documented entrypoint honesty only.",
            "Geometry, real-mesh and browser proofs reused through source-bound existing review receipts; no BREP query, CAD run, browser, native/global solve or broad test run.",
            "Optional replay orchestration uses a subprocess stub and synthetic source-bound reports, so it does not certify actual CAD execution.",
            "The 570-source map binds inputs; separately bound changed_finished_solids are produced geometry and are not incorrectly treated as missing input pins.",
            "No structural, fabrication, publication or physical release is established.",
        ],
    }
    (HERE / "receipt.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({"frozen_inputs": len(frozen), "findings": len(result["substantial_findings"])}))


if __name__ == "__main__":
    main()
