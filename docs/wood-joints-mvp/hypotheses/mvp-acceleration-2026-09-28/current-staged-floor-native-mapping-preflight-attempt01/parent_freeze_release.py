"""Parent-only exact freeze of the bounded nonzero-reference release coupon.

Creates a new immutable-input attempt directory; does not launch a solver.
"""
from pathlib import Path
import json
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(HERE))
from prepare import build_nonzero_release_fixture
from fea.wood_joint_reduced_native import freeze, digest


if __name__ == "__main__":
    target = Path(sys.argv[1]).resolve()
    model, _, metadata, deck = build_nonzero_release_fixture()
    metadata["scope"] += " Parent-owned one-launch known-answer test; no automatic retry."
    sources = [HERE / "prepare.py", HERE / "verify_proposal.py",
               HERE / "source-pins.json", HERE / "parent_release_check.py",
               HERE / "coupon-nonzero-release-probe.inp",
               HERE / "release-probe-known-answer.json"]
    if deck != (HERE / "coupon-nonzero-release-probe.inp").read_text():
        raise ValueError("Generated release deck is stale")
    freeze(target, model, metadata, sources, deck_text=deck)
    print(json.dumps({"directory":str(target), "input_freeze_sha256":digest(target / "freeze.json"),
                      "native_solve_executed":False}))
