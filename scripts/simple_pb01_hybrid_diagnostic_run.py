"""Reproducible PB-01 hybrid sensitivity run; never a V4 joint verdict."""

import argparse
import hashlib
import json
from pathlib import Path

from fea import current_response_run as native
from fea.reinforced_frame_demand import repository_source_closure
from scripts.clear_space_batch import CASES
from scripts.simple_pb01_hybrid_native import (
    DIAGNOSTIC,
    POSES,
    ROOT,
    HybridPB01,
    prepare_case,
)

PRODUCER_PATHS = tuple(
    repository_source_closure(
        [
            Path(__file__),
            ROOT / "scripts/simple_pb01_hybrid_native.py",
            ROOT / "scripts/simple_rail_joint_comparison.py",
        ],
        packages=("fea", "mini_moonboard", "scripts"),
    )
) + (DIAGNOSTIC,)
LOADED_PRODUCER_SHA256 = native.extra_source_hashes(PRODUCER_PATHS)


def run_case(
    case: str, output: Path, *, variant: str = "three_eighth", max_cycles: int = 30
):
    """Retain a source-fingerprinted old-proxy diagnostic, not design demand."""
    if case not in CASES:
        raise ValueError("Unknown unchanged load case")
    if native.extra_source_hashes(PRODUCER_PATHS) != LOADED_PRODUCER_SHA256:
        raise ValueError("Hybrid producer changed after import; restart the run")
    module = HybridPB01(variant=variant)
    report = native.run(
        output,
        module=module,
        expected_candidate=module.KEY,
        prepare_factory=lambda *args, **kwargs: prepare_case(case, variant=variant),
        extra_source_paths=PRODUCER_PATHS,
        max_cycles=max_cycles,
    )
    scope = {
        "case": case,
        "diagnostic_only": True,
        "old_ml24z_sds_proxy_stations": 23,
        "pb01_cleat_station": "clip_horizontal_lower_right_1",
        "pb01_pose_variant": variant,
        "pb01_nominal_trial_bolt_diameter_mm": POSES[variant][1],
        "variant_native_difference": "trial_stack_mass_only; identical centers and spring stiffness",
        "bore_diameter_changes_mesh": False,
        "v4_same_case_demand": False,
        "qualified_for_design": False,
        "drilling_released": False,
    }
    path = Path(output) / "diagnostic-scope.json"
    path.write_text(json.dumps(scope, indent=2) + "\n")
    report["diagnostic_scope"] = scope
    report["artifact_sha256"][path.name] = hashlib.sha256(path.read_bytes()).hexdigest()
    (Path(output) / "report.json").write_text(json.dumps(report, indent=2) + "\n")
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("case", choices=sorted(CASES))
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--max-cycles", type=int, default=30)
    parser.add_argument("--variant", choices=sorted(POSES), default="three_eighth")
    args = parser.parse_args()
    outcome = run_case(
        args.case, args.output, variant=args.variant, max_cycles=args.max_cycles
    )
    print(
        json.dumps(
            {
                key: outcome[key]
                for key in (
                    "contact_active_set_converged",
                    "global_equilibrium_passed",
                    "member_equilibrium_passed",
                    "numerically_accepted",
                    "termination",
                )
            }
        )
    )
