"""Compare a lighter climber using the frozen frame and numerical initializer.

Scale vertical and horizontal live force together at the source acceleration.
Gravity, accessory load, geometry and every mechanical law/gate stay fixed.
This comparison does not replace the owner's 250 lb dynamic requirement.
"""

from __future__ import annotations

import argparse
import fcntl
import json
import math
from pathlib import Path

import conic_frame as initialization

SOURCE = initialization.frame_run
ROOT = initialization.ROOT
require, sha, read = initialization.require, initialization.sha, initialization.read
SOURCE_SHA = "27a8a8d2f5d34f1230c86f34385e68a8a895f675683f0dc39199e82c93096bc0"
INITIALIZATION_SHA = "445574a04559e8faa28a3b69bfdbf1a439f6fc25940e0f02837b0927c48f0025"


def run(operators, output, weight_lb):
    require(math.isfinite(weight_lb) and 0 < weight_lb <= 250,
            "comparison weight must be positive and at most 250 lb")
    require(not output.exists(), "preserve completed or stopped calculations")
    pins = {Path(SOURCE.__file__): SOURCE_SHA,
            Path(initialization.__file__): INITIALIZATION_SHA,
            Path(__file__): sha(Path(__file__))}
    for path, expected in pins.items():
        require(sha(path) == expected, "changed frozen producer: " + str(path))
    rows = read(operators / "row-identities.json")
    require(sum(r["ownership"]["role"] == "non_qualifying_parametric_screw_withdrawal"
                for r in rows) == 66, "this comparison retains the 66-screw policy")
    preserved = SOURCE.run

    def configured_run(*args, **kwargs):
        kwargs["climber_load_scale"] = weight_lb / 250
        kwargs["horizontal_load_scale"] = weight_lb / 250
        return preserved(*args, **kwargs)

    SOURCE.run = configured_run
    try:
        initialization.run(output, operators)
    finally:
        SOURCE.run = preserved
        if output.exists():
            target = output / ("comparison.json" if (output / "comparison.json").exists()
                               else "stop.json")
            if target.exists():
                for path, expected in pins.items():
                    require(sha(path) == expected, "producer changed during comparison")
                report = read(target)
                report["source_sha256"].update({str(p.relative_to(ROOT)): h
                                                for p, h in pins.items()})
                report.update(
                    weight_adapter_producer_sha256=sha(Path(__file__)),
                    source_climber_weight_lb=250.0,
                    comparison_climber_weight_lb=float(weight_lb),
                    climber_load_scale=float(weight_lb / 250),
                    comparison_horizontal_force_n=float(300 * weight_lb / 250),
                    weight_comparison_scope="Proportional live loads at source acceleration; dead and accessory unchanged",
                    fixed_300n_horizontal_comparison=False,
                    owner_250lb_dynamic_requirement_replaced=False,
                )
                (output / "weight-producer.py.snapshot").write_bytes(Path(__file__).read_bytes())
                target.write_text(json.dumps(report, indent=2, allow_nan=False) + "\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--operators", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--weight-lb", type=float, required=True)
    args = parser.parse_args()
    lock = ROOT / "docs/wood-joints-mvp/luna-max-native-run-ledger.lock"
    with lock.open("a") as stream:
        fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
        require(read(lock.with_suffix(".json"))["slot"]["state"] == "idle",
                "shared mechanics slot occupied")
        run(args.operators.resolve(), args.output.resolve(), args.weight_lb)
