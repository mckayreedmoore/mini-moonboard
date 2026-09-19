"""Run an explicitly provisional kerf-right baseline-connector diagnostic.

This is not an AB205/bolted model, resistance check, or drilling release.
"""

import argparse
import hashlib
import json
from pathlib import Path

from fea import current_response_run as native
from fea.floor_flush_run import face_contacts, taper_top_monitors
from scripts import bolted_kerf_diagnostic_probe as probe
from scripts.clear_space_batch import CASES
from scripts.compact_rail_study import bolt_properties

ORIGINAL_SOURCES = native.source_hashes
FACE_CONTACTS_PATH = Path(face_contacts.__code__.co_filename)


def _sources():
    result = ORIGINAL_SOURCES()
    for path in (Path(__file__), Path(probe.__file__), FACE_CONTACTS_PATH,
                 Path("scripts/clear_space_batch.py"), Path("scripts/compact_rail_study.py")):
        resolved = path.resolve()
        result[str(resolved.relative_to(Path.cwd().resolve()))] = hashlib.sha256(resolved.read_bytes()).hexdigest()
    return result


LOADED_SOURCES = _sources()


def run_case(case, output, *, connection_scale=1., contact_stiffness_per_area=100.,
             max_cycles=30, frame_size=150., contact_update_strategy="all"):
    """Solve unchanged loading with old ML24Z/SDS connectors on kerf-right wood."""
    if case not in CASES:
        raise ValueError(f"Unknown unchanged load case: {case}")
    if _sources() != LOADED_SOURCES or ORIGINAL_SOURCES() != native.LOADED_SOURCE_SHA256:
        raise ValueError("Producer sources changed after import; restart diagnostic")
    module = probe.DiagnosticProxy()
    bolts = {c.name: bolt_properties(c) for c in module.connections() if c.kind == "bolt"}
    if not bolts:
        raise ValueError("No retained frame-bolt arrangements")
    hold, force = CASES[case]
    old = native.source_hashes, native.LOADED_SOURCE_SHA256
    try:
        native.source_hashes = _sources
        native.LOADED_SOURCE_SHA256 = LOADED_SOURCES
        report = native.run(
            output, module=module, expected_candidate=module.KEY,
            prepare_factory=probe.prepare_diagnostic,
            member_contacts=face_contacts(module, stiffness_per_area=contact_stiffness_per_area),
            clearance_monitors=taper_top_monitors(module),
            bolt_stiffness={**next(iter(bolts.values())), "by_name": bolts},
            connection_scale=connection_scale, max_cycles=max_cycles, frame_size=frame_size,
            contact_update_strategy=contact_update_strategy,
            hold=hold, pounds=250., horizontal_force=force, leg_floor_grid=3, patch_size=20.,
        )
    finally:
        native.source_hashes, native.LOADED_SOURCE_SHA256 = old
    scope = {
        "case": case, "source_geometry": module.raw.KEY,
        "connector_proxy": "baseline ML24Z angles and SDS screws",
        "connection_scale": connection_scale,
        "contact_stiffness_per_area_n_per_mm3": contact_stiffness_per_area,
        "contact_update_strategy": contact_update_strategy,
        "numerically_converged": report["numerically_accepted"],
        "bolted_joint_demands": False, "acceptance": False, "drilling_released": False,
    }
    scope_path = Path(output) / "diagnostic-scope.json"
    scope_path.write_text(json.dumps(scope, indent=2) + "\n")
    report["diagnostic_scope"] = scope
    report["artifact_sha256"][scope_path.name] = hashlib.sha256(scope_path.read_bytes()).hexdigest()
    (Path(output) / "report.json").write_text(json.dumps(report, indent=2, allow_nan=False) + "\n")
    return {**scope, "native_report": report}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("case", choices=CASES)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--connection-scale", type=float, default=1.)
    parser.add_argument("--contact-stiffness-per-area", type=float, default=100.)
    parser.add_argument("--max-cycles", type=int, default=30)
    parser.add_argument("--frame-size", type=float, default=150.)
    parser.add_argument("--contact-update-strategy",
                        choices=("all", "one_per_floor_body", "one_at_a_time"), default="all")
    args = parser.parse_args()
    result = run_case(args.case, args.output, connection_scale=args.connection_scale,
                      contact_stiffness_per_area=args.contact_stiffness_per_area,
                      max_cycles=args.max_cycles, frame_size=args.frame_size,
                      contact_update_strategy=args.contact_update_strategy)
    print(json.dumps({key: value for key, value in result.items() if key != "native_report"}, indent=2))
    if not result["numerically_converged"]:
        raise SystemExit(1)
