"""Read-only replay of the already-passed native response method coupons.

This runner imports the existing fixture-check functions but never calls their
writer or edits the earlier response-audit packet. Its sole output is this
packet's method_fixture_check.json.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
SERIES = ROOT / "docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28"
STABLE_PACKET = SERIES / "current-springa-frame-response-audit-attempt01"
STABLE_AUDIT = STABLE_PACKET / "response_audit.py"
STABLE_REPLAYER = STABLE_PACKET / "verify_method_fixtures.py"
EXPECTED_AUDIT_SHA256 = "b20dae471e9826a55c40bbeed028375e6d082913e3f3917665514f2763ddd49c"
EXPECTED_REPLAYER_SHA256 = "5d8b5cb7031855b625b6541a8e1054238201a893214f8a6cd890bf6585bc6911"
sys.path.insert(0, str(ROOT))


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot import pinned read-only helper: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> None:
    if _sha(STABLE_AUDIT) != EXPECTED_AUDIT_SHA256:
        raise RuntimeError("Pinned stable response helper changed; review before replay")
    if _sha(STABLE_REPLAYER) != EXPECTED_REPLAYER_SHA256:
        raise RuntimeError("Pinned known-answer replayer changed; review before replay")
    stable = _load("stable_selected_floor_fixture_source", STABLE_REPLAYER)
    checks = [stable.relative_springa_check(), stable.exact_floor_mpc_check(),
              stable.transformed_floor_check()]
    roundoff = stable.small_endpoint_length_roundoff_check()
    if len(checks) != 3 or not all(row.get("passed") is True for row in checks):
        raise AssertionError("A prior native method coupon did not replay successfully")
    if roundoff.get("passed") is not True:
        raise AssertionError("Near-zero SPRINGA endpoint-length guard replay failed")
    result: dict[str, Any] = {
        "schema": "current_springa_selected_floor_method_fixture_replay/v1",
        "status": "PASS_READ_ONLY_METHOD_FIXTURE_REPLAYS",
        "native_solver_launched_by_replayer": False,
        "prior_native_fixtures_replayed": len(checks),
        "stable_response_helper_sha256": EXPECTED_AUDIT_SHA256,
        "stable_fixture_replayer_sha256": EXPECTED_REPLAYER_SHA256,
        "fixtures": checks,
        "near_zero_endpoint_length_roundoff_check": roundoff,
        "limits": [
            "The scalar relative SPRINGA, exact-floor scalar, and transformed-floor coupons are method-only evidence.",
            "These fixtures do not exercise the 17/83 selected-floor complementarity branch or qualify an a12-rear response.",
            "No earlier packet or frozen source is modified by this replay.",
        ],
    }
    (HERE / "method_fixture_check.json").write_text(
        json.dumps(result, indent=2, allow_nan=False) + "\n"
    )
    print(result["status"], result["prior_native_fixtures_replayed"])


if __name__ == "__main__":
    main()
