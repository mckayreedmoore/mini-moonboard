"""Parent-only exact freeze helper for the scheduled ten-step coupon.

Creates a new immutable-input attempt directory. It never launches CalculiX.
"""
from pathlib import Path
import json
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(HERE))

from prepare import build_fixture
from fea.wood_joint_reduced_native import digest, freeze


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("usage: parent_freeze_staged.py NEW_ATTEMPT_DIRECTORY")
    target = Path(sys.argv[1]).resolve()
    model, _, metadata, deck = build_fixture()
    metadata["scope"] += (
        " Parent-owned one-launch scheduled ten-step known-answer test; "
        "no automatic retry and no frame run."
    )
    sources = [
        HERE / "prepare.py",
        HERE / "verify_proposal.py",
        HERE / "source-pins.json",
        HERE / "coupon-staged.inp",
        HERE / "known-answer.json",
        HERE / "parent_staged_check.py",
    ]
    if deck != (HERE / "coupon-staged.inp").read_text():
        raise ValueError("Generated staged deck is stale")
    freeze(target, model, metadata, sources, deck_text=deck)
    print(json.dumps({
        "directory":str(target),
        "input_freeze_sha256":digest(target / "freeze.json"),
        "native_solve_executed":False,
        "mechanical_acceptance":False,
    }))
