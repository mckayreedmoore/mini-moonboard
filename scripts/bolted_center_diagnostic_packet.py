"""Compact, source-bound numerical reference for kerf-right center proxy runs.

Only accepted native runs receive interface wrenches. This is not a bolted
joint demand, connection acceptance, or drilling release.
"""

import argparse
import hashlib
import json
from pathlib import Path

from scripts.bolted_center_demand_extract import extract_files

DEFAULT_CASES = ("a1-rear", "a12-left", "a12-rear", "k12-rear", "k12-right")
FORWARD_SERIES = (
    "proxy-default-v2",
    "proxy-contact10",
    "proxy-contact1000",
    "proxy-one-at-time",
    "proxy-one-per-floor",
    "proxy-seeded-a12rear",
)
SENSITIVITY_SERIES = ("proxy-scale0p1", "proxy-scale10")
SIDES = {
    "left": ("base_principal_center_left", "base_post_center_left"),
    "right": ("base_principal_center_right", "base_post_center_right"),
}
SOURCE_KEYS = (
    "fea/current_response_run.py",
    "mini_moonboard/bolted_floor_flush_width.py",
    "mini_moonboard/compact_floor_flush_bolted_frame.py",
    "mini_moonboard/floor_flush_width.py",
    "scripts/bolted_kerf_diagnostic_probe.py",
    "scripts/bolted_kerf_native_diagnostic.py",
    "scripts/clear_space_batch.py",
    "scripts/compact_rail_study.py",
)
RAW_ROOT = Path("fea/results/diagnostics/kerf-right-center")
OUTPUT = Path("docs/bolted-candidate-prototypes/center-reference-diagnostic.json")


def _sha256(data):
    return hashlib.sha256(data).hexdigest()


def case_row(root, series, case):
    """Read one final report and record; extract only after native acceptance."""
    folder = Path(root) / series / case
    report_path = folder / "report.json"
    report_bytes = report_path.read_bytes()
    report = json.loads(report_bytes)
    cycles = report["contact_cycles"]
    if not cycles:
        raise ValueError(f"No contact cycles: {series}/{case}")
    last = cycles[-1]
    record_path = folder / last["directory"] / "input.json"
    record_bytes = record_path.read_bytes()
    relative = f"{last['directory']}/input.json"
    record_sha256 = _sha256(record_bytes)
    manifest = report.get("artifact_sha256", {}).get(relative)
    if manifest != record_sha256:
        raise ValueError(f"Final record digest mismatch: {series}/{case}")
    record = json.loads(record_bytes)
    scope = report["diagnostic_scope"]
    scope_path = folder / "diagnostic-scope.json"
    scope_bytes = scope_path.read_bytes()
    if (
        report.get("artifact_sha256", {}).get(scope_path.name) != _sha256(scope_bytes)
        or json.loads(scope_bytes) != scope
    ):
        raise ValueError(f"Diagnostic scope sidecar mismatch: {series}/{case}")
    producer_sources = {}
    for source in SOURCE_KEYS:
        digest = report.get("source_sha256", {}).get(source)
        snapshot = folder / "source_snapshots" / source
        if (not digest or not snapshot.is_file()
                or _sha256(snapshot.read_bytes()) != digest
                or report.get("artifact_sha256", {}).get(f"source_snapshots/{source}") != digest):
            raise ValueError(f"Producer source snapshot mismatch: {series}/{case}: {source}")
        producer_sources[source] = digest
    proxy = "baseline ML24Z angles and SDS screws"
    candidate = "bolted-kerf-right-diagnostic-proxy"
    if (
        report.get("candidate") != candidate
        or record.get("candidate") != candidate
        or scope.get("case") != case
        or scope.get("source_geometry")
        != "compact-floor-flush-bolted-development-kerf-right"
        or scope.get("connector_proxy") != proxy
        or scope.get("bolted_joint_demands") is not False
        or scope.get("acceptance") is not False
        or scope.get("drilling_released") is not False
        or record.get("provisional_structural_connectors") != proxy
        or record.get("diagnostic_only") is not True
        or record.get("bolted_joint_demands") is not False
    ):
        raise ValueError(f"Invalid diagnostic scope: {series}/{case}")
    expected_loads = {
        "a1-rear": ("A1", 0, 300),
        "a12-left": ("A12", -300, 0),
        "a12-rear": ("A12", 0, 300),
        "a12-forward": ("A12", 0, -300),
        "k12-rear": ("K12", 0, 300),
        "k12-right": ("K12", 300, 0),
    }
    hold, x_force, y_force = expected_loads[case]
    parameters = report["parameters"]
    force = [x_force, y_force, -2224.11080763025]
    if (
        parameters.get("hold") != hold
        or record.get("hold") != hold
        or parameters.get("pounds") != 250.0
        or parameters.get("force_xyz_n") != force
        or record.get("force_xyz_n") != force
    ):
        raise ValueError(f"Load case mismatch: {series}/{case}")
    accepted = report.get("numerically_accepted") is True
    converged = (
        report.get("contact_active_set_converged") is True
        and last.get("contact_passed") is True
    )
    equilibrium = all(
        report.get(key) is True
        for key in (
            "global_equilibrium_passed",
            "member_equilibrium_passed",
            "mpc_check_passed",
        )
    )
    if accepted and (not converged or not equilibrium):
        raise ValueError(f"Inconsistent acceptance: {series}/{case}")
    if not accepted and converged:
        raise ValueError(f"Inconsistent acceptance: {series}/{case}")
    row = {
        "series": series,
        "case": case,
        "status": "accepted_proxy_reference" if accepted else "nonconverged",
        "source": {
            "report": (RAW_ROOT / series / case / "report.json").as_posix(),
            "record": (RAW_ROOT / series / case / relative).as_posix(),
            "report_sha256": _sha256(report_bytes),
            "record_sha256": record_sha256,
            "record_manifest_sha256": manifest,
            "producer_source_sha256": producer_sources,
        },
        "settings": {
            "diagnostic_scope": scope,
            "hold": parameters["hold"],
            "pounds": parameters["pounds"],
            "force_xyz_n": parameters["force_xyz_n"],
            "standoff_from_front_mm": parameters["standoff_from_front_mm"],
            "leg_bolt_scale": parameters.get("leg_bolt_scale"),
            "leg_floor_grid": parameters.get("leg_floor_grid"),
            "contact_update_strategy": report.get("contact_update_strategy"),
        },
        "convergence": {
            "numerically_accepted": accepted,
            "contact_active_set_converged": report.get("contact_active_set_converged"),
            "global_equilibrium_passed": report.get("global_equilibrium_passed"),
            "member_equilibrium_passed": report.get("member_equilibrium_passed"),
            "mpc_check_passed": report.get("mpc_check_passed"),
            "cycle_count": len(cycles),
            "final_cycle": last,
            "termination": report.get("termination"),
        },
    }
    if accepted:
        row["sides"] = {}
        for side, (principal, post) in SIDES.items():
            extracted = extract_files(report_path, record_path, principal, post)
            interfaces = {
                name: {
                    key: value
                    for key, value in interface.items()
                    if key
                    in (
                        "center_member",
                        "header",
                        "clip",
                        "origin_xyz_mm",
                        "on_center_member",
                        "on_header",
                        "on_center_member_components",
                        "on_header_components",
                        "residual",
                    )
                }
                for name, interface in extracted["interfaces"].items()
            }
            header = extracted["header_free_body"]
            selected = header["selected_interfaces"]
            other = header["other_attachments"]
            row["sides"][side] = {
                "interfaces": interfaces,
                "header_free_body": {
                    key: value
                    for key, value in header.items()
                    if key
                    in (
                        "header",
                        "origin_xyz_mm",
                        "all_connections",
                        "external_load",
                        "residual",
                    )
                }
                | {
                    "selected_interfaces": {
                        "connection_count": len(selected["connection_names"]),
                        "wrench": selected["wrench"],
                    },
                    "other_attachments": {
                        "connection_count": len(other["connection_names"]),
                        "wrench": other["wrench"],
                    },
                },
                "status": extracted["status"],
            }
    return row


def build_packet(root=RAW_ROOT):
    """Collect the fixed reference set; missing raw evidence is an error."""
    defaults = [case_row(root, "proxy-default-v2", case) for case in DEFAULT_CASES]
    failures = [case_row(root, series, "a12-forward") for series in FORWARD_SERIES]
    sensitivities = [case_row(root, series, "a1-rear") for series in SENSITIVITY_SERIES]
    if any(
        row["status"] != "accepted_proxy_reference" for row in defaults + sensitivities
    ):
        raise ValueError("Expected accepted proxy reference")
    if any(row["status"] != "nonconverged" for row in failures):
        raise ValueError("Expected nonconverged a12-forward run")
    return {
        "title": "Kerf-right center numerical reference proxy",
        "scope": "Baseline ML24Z/SDS proxy only; no bolted demand, acceptance, or drilling release.",
        "units": {"force": "N", "moment": "N mm", "position": "mm"},
        "accepted_default_v2": defaults,
        "a12_forward_failures": failures,
        "a1_rear_sensitivity": sensitivities,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=RAW_ROOT)
    parser.add_argument("--output", type=Path, default=OUTPUT)
    args = parser.parse_args()
    packet = build_packet(args.root)
    args.output.write_text(json.dumps(packet, indent=2) + "\n")


if __name__ == "__main__":
    main()
