"""Run one provisional AB205 left-center topology; never a resistance or drilling release."""

import argparse
import hashlib
import json
from pathlib import Path

from fea import current_response_run as native
from fea.floor_flush_run import face_contacts, taper_top_monitors
from scripts import bolted_center_joint_model
from scripts import bolted_kerf_diagnostic_probe as probe
from scripts.clear_space_batch import CASES
from scripts.compact_rail_study import bolt_properties

ORIGINAL_SOURCES = native.source_hashes


def _sources():
    result = ORIGINAL_SOURCES()
    for path in (
        Path(__file__),
        Path(probe.__file__),
        Path(bolted_center_joint_model.__file__),
        Path(face_contacts.__code__.co_filename),
        Path("scripts/clear_space_batch.py"),
        Path("scripts/compact_rail_study.py"),
        Path("scripts/bolted_candidate_ab205_center_fit.py"),
        Path("docs/floor-flush-construction-kerf-right/connection-axes.csv"),
    ):
        resolved = path.resolve()
        result[str(resolved.relative_to(Path.cwd().resolve()))] = hashlib.sha256(
            resolved.read_bytes()
        ).hexdigest()
    return result


LOADED_SOURCES = _sources()


def run_case(
    case, output, *, spring_n_per_mm, max_cycles=30, contact_update_strategy="all"
):
    """Keep the old surrounding frame, but replace the actual left-center topology."""
    if case not in CASES or not 0 < spring_n_per_mm <= 1e12:
        raise ValueError("Require a known case and finite positive provisional spring")
    if (
        _sources() != LOADED_SOURCES
        or ORIGINAL_SOURCES() != native.LOADED_SOURCE_SHA256
    ):
        raise ValueError("Producer sources changed after import; restart diagnostic")
    module = probe.DiagnosticCenterBolted()
    spring = {"axial_n_per_mm": spring_n_per_mm, "lateral_n_per_mm": spring_n_per_mm}
    joint = bolted_center_joint_model.shared_center_joint(
        module,
        vertical_spring=spring,
        steel_bolt_spring=spring,
        wood_bearing_lateral_n_per_mm=spring_n_per_mm,
        flange_contact_n_per_mm=spring_n_per_mm,
    )
    retained = {
        c.name: bolt_properties(c) for c in module.connections() if c.kind == "bolt"
    }
    hold, force = CASES[case]
    old = native.source_hashes, native.LOADED_SOURCE_SHA256
    try:
        native.source_hashes = _sources
        native.LOADED_SOURCE_SHA256 = LOADED_SOURCES
        report = native.run(
            output,
            module=module,
            expected_candidate=module.KEY,
            prepare_factory=probe.prepare_diagnostic,
            member_contacts=face_contacts(module),
            clearance_monitors=taper_top_monitors(module),
            bolt_stiffness={**next(iter(retained.values())), "by_name": retained},
            max_cycles=max_cycles,
            contact_update_strategy=contact_update_strategy,
            diagnostic_center_joint=joint,
            hold=hold,
            pounds=250.0,
            horizontal_force=force,
            leg_floor_grid=3,
            patch_size=20.0,
        )
    finally:
        native.source_hashes, native.LOADED_SOURCE_SHA256 = old
    scope = {
        "case": case,
        "source_geometry": module.raw.KEY,
        "connector_topology": "two nominal left-center AB205 rigid angles with two shared header bolt bodies",
        "remaining_connectors": "baseline ML24Z/SDS proxy",
        "spring_n_per_mm": spring_n_per_mm,
        "shaft_idealization": "free rigid shaft with two tilt DOFs; two lateral-only bore branches",
        "flange_contact": "four sampled compression-only contacts per angle; no preload",
        "legacy_center_hardware_mass_surrogate": True,
        "contact_update_strategy": contact_update_strategy,
        "numerically_converged": report["numerically_accepted"],
        "qualified_bolted_joint_demands": False,
        "resistance_checked": False,
        "acceptance": False,
        "drilling_released": False,
    }
    scope_path = Path(output) / "diagnostic-scope.json"
    scope_path.write_text(json.dumps(scope, indent=2) + "\n")
    report["diagnostic_scope"] = scope
    report["artifact_sha256"][scope_path.name] = hashlib.sha256(
        scope_path.read_bytes()
    ).hexdigest()
    (Path(output) / "report.json").write_text(
        json.dumps(report, indent=2, allow_nan=False) + "\n"
    )
    return {**scope, "native_report": report}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("case", choices=CASES)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--spring-n-per-mm", type=float, required=True)
    parser.add_argument("--max-cycles", type=int, default=30)
    parser.add_argument(
        "--contact-update-strategy",
        choices=("all", "one_per_floor_body", "one_at_a_time"),
        default="all",
    )
    args = parser.parse_args()
    result = run_case(
        args.case,
        args.output,
        spring_n_per_mm=args.spring_n_per_mm,
        max_cycles=args.max_cycles,
        contact_update_strategy=args.contact_update_strategy,
    )
    print(
        json.dumps(
            {key: value for key, value in result.items() if key != "native_report"},
            indent=2,
        )
    )
    if not result["numerically_converged"]:
        raise SystemExit(1)
