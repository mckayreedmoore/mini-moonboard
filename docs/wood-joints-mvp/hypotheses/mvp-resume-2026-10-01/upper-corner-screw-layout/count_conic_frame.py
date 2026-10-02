"""Run the unchanged frame laws for the hypothetical 98-screw grain packet.

Reuse the existing convex initialization wrapper. Adapt only the frozen
frame producer's inventory guard and two saved-force seed comparisons.
All mechanical equations, gates and physical claim limits remain intact.
"""

from __future__ import annotations

import argparse
import fcntl
import inspect
import json
from pathlib import Path

import conic_frame as initialization

SOURCE = initialization.frame_run
ROOT = initialization.ROOT
SOURCE_SHA = "27a8a8d2f5d34f1230c86f34385e68a8a895f675683f0dc39199e82c93096bc0"
INITIALIZATION_SHA = "445574a04559e8faa28a3b69bfdbf1a439f6fc25940e0f02837b0927c48f0025"
require, sha, read = initialization.require, initialization.sha, initialization.read


def run(operators, output):
    require(not output.exists(), "preserve completed and stopped calculations")
    pins = {Path(SOURCE.__file__): SOURCE_SHA,
            Path(initialization.__file__): INITIALIZATION_SHA,
            Path(__file__): sha(Path(__file__))}
    for path, digest in pins.items():
        require(sha(path) == digest, "changed frozen producer: " + str(path))
    assessment = read(operators / "operator-assessment.json")
    rows = read(operators / "row-identities.json")
    inputs = read(operators / "model-inputs.json")
    require(assessment["status"] == "PASS_UPDATED_ELASTIC_FRAME_OPERATORS",
            "operator assessment did not pass")
    require(assessment["old_scalar_row_count"] == 1888
            and assessment["appended_scalar_row_count"] == 96
            and len(rows) == 1984, "unexpected scalar inventory")
    require(sum(r["ownership"]["role"] == "non_qualifying_parametric_screw_withdrawal"
                for r in rows) == 98
            and sum(c["kind"] == "panel_screw" for c in inputs["connections"]) == 98,
            "expected 80 main-panel and 18 kicker screws")
    text = inspect.getsource(SOURCE.run)
    substitutions = {
        "len(screw_lateral) == 132 and len(screw_axial) == 66":
            "len(screw_lateral) == 196 and len(screw_axial) == 98",
        'saved[case_id + "_force_n"]':
            'np.pad(saved[case_id + "_force_n"], (0, 96))',
    }
    require([text.count(site) for site in substitutions] == [1, 2],
            "frozen frame adaptation sites changed")
    for old, new in substitutions.items():
        text = text.replace(old, new)
    namespace = SOURCE.__dict__.copy()
    exec(compile(text, "<98-screw-inventory-frame-run>", "exec"), namespace)  # noqa: S102 -- pinned source and checked substitutions
    preserved_run = SOURCE.run
    SOURCE.run = namespace["run"]
    try:
        initialization.run(output, operators)
    finally:
        SOURCE.run = preserved_run
        if output.exists():
            target = output / ("comparison.json" if (output / "comparison.json").exists()
                               else "stop.json")
            if target.exists():
                for path, digest in pins.items():
                    require(sha(path) == digest, "producer changed during frame run")
                report = read(target)
                report["source_sha256"].update({str(p.relative_to(ROOT)): h
                                                for p, h in pins.items()})
                report.update(
                    count_adapter_producer_sha256=sha(Path(__file__)),
                    hypothetical_panel_screw_total=98,
                    proposed_main_panel_screw_count=20,
                    added_hardware_mass_included=False,
                    count_only_adaptations=substitutions,
                    mechanical_equations_and_gates_changed=False,
                    physical_screw_inventory_adopted=False,
                )
                (output / "count-frame-producer.py.snapshot").write_bytes(Path(__file__).read_bytes())
                (output / "adapted-run.py.snapshot").write_text(text)
                report["count_adapted_run_sha256"] = sha(output / "adapted-run.py.snapshot")
                target.write_text(json.dumps(report, indent=2, allow_nan=False) + "\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--operators", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    lock = ROOT / "docs/wood-joints-mvp/luna-max-native-run-ledger.lock"
    with lock.open("a") as stream:
        fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
        require(read(lock.with_suffix(".json"))["slot"]["state"] == "idle",
                "shared mechanics slot occupied")
        run(args.operators.resolve(), args.output.resolve())
