"""Prepare and validate the AB90 candidate's future native-run contract.

This module does not invoke CalculiX or any native load case. The existing
flush runner is recorded as the producer, while its candidate-specific contact
and mesh adapter remains an explicit prerequisite.
"""

import argparse
import hashlib
import json
from pathlib import Path

from mini_moonboard import compact_floor_flush_bolted_frame as candidate
from scripts.clear_space_batch import CASES

ROOT = Path(__file__).resolve().parents[1]
CANONICAL_CASES = tuple(CASES)
SOURCE_FILES = (
    "mini_moonboard/compact_floor_flush_frame.py",
    "mini_moonboard/floor_flush_width.py",
    "mini_moonboard/compact_floor_flush_bolted_frame.py",
    "mini_moonboard/bolted_floor_flush_width.py",
    "mini_moonboard/bolted_joint_mechanics.py",
    "mini_moonboard/bolted_layout_common.py",
    "mini_moonboard/demountable_connections.py",
    "mini_moonboard/bolted_steel_checks.py",
    "mini_moonboard/bolted_timber_checks.py",
    "mini_moonboard/a66_layout_common.py",
    "mini_moonboard/a66_geometry_screen.py",
    "mini_moonboard/bolted_layouts/__init__.py",
    "mini_moonboard/bolted_layouts/top.py",
    "mini_moonboard/bolted_layouts/bottom.py",
    "mini_moonboard/bolted_layouts/service.py",
    "mini_moonboard/bolted_layouts/header_post.py",
    "mini_moonboard/bolted_layouts/center_base.py",
    "mini_moonboard/bolted_layouts/outer_base.py",
    "fea/floor_flush_mesh.py",
    "fea/floor_flush_run.py",
    "fea/user_load_envelope.py",
    "scripts/clear_space_batch.py",
    "scripts/bolted_candidate_geometry_checks.py",
    "docs/floor-flush-construction/connection-axes.csv",
    "docs/floor-flush-construction-kerf-right/connection-axes.csv",
    "docs/bolted-candidate-owner-inputs.json",
)


def digest(path: str) -> str:
    return hashlib.sha256((ROOT / path).read_bytes()).hexdigest()


def validate_contract() -> dict[str, object]:
    connections = candidate.connections()
    structural_screws = [connection.name for connection in connections
                         if connection.kind == "screw" and connection.name not in {item.name for item in candidate.panel_connections()}]
    return {
        "candidate": candidate.KEY,
        "baseline_candidate": candidate.BASELINE_KEY,
        "native_producer": "fea.floor_flush_run.run",
        "mesh_producer": "fea.floor_flush_mesh.prepare_flush",
        "load_case_source": "scripts.clear_space_batch.CASES",
        "canonical_cases": list(CANONICAL_CASES),
        "case_count": len(CANONICAL_CASES),
        "structural_screw_macros_remaining": structural_screws,
        "panel_connection_count": len(candidate.panel_connections()),
        "owner_physical_width_scope": "kerf-right",
        "candidate_geometry_width_scope": "official prototype pending kerf-right native adapter",
        "candidate_geometry_contract": {
            "joint_records": len(candidate.structural_joint_records()),
            "fastener_records": len(candidate.fastener_stack_records()),
            "mechanics_module": "mini_moonboard.bolted_joint_mechanics",
        },
        "source_sha256": {path: digest(path) for path in SOURCE_FILES},
        "native_ready": False,
        "native_blocker": "candidate-specific mesh/contact adapter and resistance freeze are not complete",
        "planned_result_root": "fea/results/bolted-candidate/compact-floor-flush-bolted-development",
        "required_artifacts_per_case": ["inputs.json", "geometry.json", "report.json.gz", "checks.json", "run.log", "manifest.json"],
        "no_native_cases_run": True,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.output.write_text(json.dumps(validate_contract(), indent=2) + "\n")


if __name__ == "__main__":
    main()
