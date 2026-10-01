"""Create and verify the refreshed source-bound WJ24 input manifest."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(ROOT))

from scripts import wood_joint_current_full_frame_manifest as source_manifest


OUTPUT = Path(
    "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/"
    "current-full-frame-input-manifest-attempt02/current-full-frame-input-manifest.json"
)
MANIFEST_ID = OUTPUT.parent.name
PRODUCER_PATH = Path(__file__).resolve().relative_to(ROOT).as_posix()


def _canonical_json(value: Any) -> bytes:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), allow_nan=False
    ).encode("utf-8")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def build_manifest() -> dict[str, Any]:
    """Derive a distinctly named attempt from the shared read-only producer."""
    manifest = source_manifest.build_manifest(ROOT)
    base_producer = manifest["producer"]
    manifest["manifest_id"] = MANIFEST_ID
    manifest["base_manifest_producer"] = base_producer
    manifest["producer"] = {
        "path": PRODUCER_PATH,
        "sha256": _sha256(Path(__file__).resolve()),
    }
    manifest.pop("manifest_sha256", None)
    manifest["manifest_sha256"] = hashlib.sha256(
        _canonical_json(manifest)
    ).hexdigest()
    return manifest


def verify_manifest(output: Path = OUTPUT) -> dict[str, Any]:
    """Verify the attempt identity, canonical digest, and current source replay."""
    output = Path(output)
    expected_output = (ROOT / OUTPUT).resolve()
    if output.is_absolute():
        actual_output = output.resolve()
    else:
        actual_output = (ROOT / output).resolve()
    if actual_output != expected_output:
        raise ValueError("output must be this attempt02 manifest path")

    saved = json.loads(actual_output.read_text(encoding="utf-8"))
    payload = dict(saved)
    saved_hash = payload.pop("manifest_sha256", None)
    if saved_hash != hashlib.sha256(_canonical_json(payload)).hexdigest():
        raise ValueError("manifest content hash differs")
    expected = build_manifest()
    if saved != expected:
        raise ValueError("saved manifest does not match current source inputs")
    if saved.get("readiness", {}).get("inventory_complete") is not True:
        raise ValueError("source inventory is not complete")
    if saved.get("readiness", {}).get("inputs_ready") is not False:
        raise ValueError("manifest must not claim solver inputs are ready")
    if saved.get("independent_cross_checks", {}).get("all_pass") is not True:
        raise ValueError("independent source/case cross-checks did not all pass")
    if saved.get("readiness", {}).get("native_solve_executed") is not False:
        raise ValueError("manifest unexpectedly claims a native solve")

    return {
        "status": "verified",
        "manifest_path": OUTPUT.as_posix(),
        "manifest_sha256": saved_hash,
        "inventory_complete": True,
        "inputs_ready": False,
        "physical_member_count": saved["inventory_counts"][
            "full_physical_member_nodes"
        ],
        "candidate_bolt_axes": saved["inventory_counts"]["candidate_bolt_axes"],
        "retained_frame_bolt_axes": saved["inventory_counts"][
            "retained_starting_frame_bolt_axes"
        ],
        "panel_kicker_screw_axes": saved["inventory_counts"][
            "panel_kicker_screw_axes"
        ],
        "load_case_count": saved["inventory_counts"][
            "current_applied_load_cases"
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--write", action="store_true")
    mode.add_argument("--verify", action="store_true")
    args = parser.parse_args()
    destination = ROOT / OUTPUT

    if args.verify:
        result = verify_manifest()
    else:
        manifest = build_manifest()
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(
            json.dumps(manifest, indent=2, sort_keys=True, allow_nan=False) + "\n",
            encoding="utf-8",
        )
        result = {
            "status": "written",
            "manifest_path": OUTPUT.as_posix(),
            "manifest_sha256": manifest["manifest_sha256"],
            "inventory_complete": manifest["readiness"]["inventory_complete"],
            "inputs_ready": manifest["readiness"]["inputs_ready"],
            "physical_member_count": manifest["inventory_counts"][
                "full_physical_member_nodes"
            ],
            "candidate_bolt_axes": manifest["inventory_counts"][
                "candidate_bolt_axes"
            ],
            "retained_frame_bolt_axes": manifest["inventory_counts"][
                "retained_starting_frame_bolt_axes"
            ],
            "panel_kicker_screw_axes": manifest["inventory_counts"][
                "panel_kicker_screw_axes"
            ],
            "load_case_count": manifest["inventory_counts"][
                "current_applied_load_cases"
            ],
        }
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
