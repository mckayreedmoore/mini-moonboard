"""Run the saved frame equations with an explicit hypothetical screw count.

Keep the frozen producer untouched. The adapted function changes only its
inventory guard and pads numerical force guesses/reference differences with
zeros for appended rows. No constitutive or equilibrium equation changes.
"""

import argparse
import fcntl
import inspect
import json
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import both_corner_frame as source


def run(operators, output):
    old_count = source.read(operators / "operator-assessment.json")["old_scalar_row_count"]
    rows = source.read(operators / "row-identities.json")
    count = sum(r["ownership"]["role"] == "non_qualifying_parametric_screw_withdrawal" for r in rows)
    appended = len(rows) - old_count
    source.require(count == 98 and appended == 96, "unexpected proposed screw count")
    function_text = inspect.getsource(source.run)
    replacements = {
        "len(screw_lateral) == 132 and len(screw_axial) == 66": "len(screw_lateral) == 196 and len(screw_axial) == 98",
        'saved[case_id + "_force_n"]': 'np.pad(saved[case_id + "_force_n"], (0, 96))',
    }
    counts = [function_text.count(text) for text in replacements]
    source.require(counts == [1, 2], "frozen producer adaptation sites changed")
    adapted_text = function_text
    for original, replacement in replacements.items():
        adapted_text = adapted_text.replace(original, replacement)
    namespace = source.__dict__.copy()
    exec(compile(adapted_text, "<count-only-adapted-frame-run>", "exec"), namespace)
    namespace["run"](output, service_joints=True, bottom_corners=True,
        all_two_receiver_clearances=True, bounded_freeplay=True,
        frame_directory=operators, connection_inputs=operators / "model-inputs.json")
    record = source.read(output / "comparison.json")
    record.update(
        producer_sha256=source.sha(Path(__file__)),
        frozen_equation_producer_sha256=source.sha(Path(source.__file__)),
        hypothetical_panel_screw_total=count,
        count_only_adaptations=replacements,
        count_only_equations_preserved=True,
    )
    (output / "comparison.json").write_text(json.dumps(record, indent=2, allow_nan=False) + "\n")
    (output / "producer.py.snapshot").write_bytes(Path(__file__).read_bytes())
    (output / "adapted-run.py.snapshot").write_text(adapted_text)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--operators", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    with (source.ROOT / "docs/wood-joints-mvp/luna-max-native-run-ledger.lock").open("a") as stream:
        fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
        source.require(source.read(source.ROOT / "docs/wood-joints-mvp/luna-max-native-run-ledger.json")["slot"]["state"] == "idle", "shared mechanics slot occupied")
        run(args.operators.resolve(), args.output.resolve())
