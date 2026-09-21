"""Authenticated PB05 A12-forward actions and conditional timber checks; no release."""

import json
import math
from pathlib import Path

from scripts import simple_pb03_quarter_inch_resistance as quarter
from scripts.simple_pb03_first_case_demand import (
    _angle_to_grain,
    _cross,
    _dot,
    _interface_resultants,
    _norm,
    _scale,
    _sha256,
    _subtract,
    _unit,
    _vector,
)
from scripts.simple_pb04_first_case_demand import _direction, _extent
from scripts.simple_pb05_native import SOURCE_ID, screen
from scripts.simple_pb05_native_mechanics import (
    MECHANICS_SOURCE_ID,
    PB05MechanicsNative,
    native_row_inventory,
)

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SUMMARY = (
    ROOT
    / "fea/results/diagnostics/pb05-eight-station-a12-forward-v1/pb05-eight-station-diagnostic.json"
)
DEFAULT_REPORT = (
    DEFAULT_SUMMARY.parent / "attempts/a12-forward-01-all-unseeded/report.json"
)
REPORT_SHA256 = "6b58b7df844b2071f0cfc04e501a2d761c51e0ce12064b9cb6292100eec2cdee"
SUMMARY_SHA256 = "c1302f6911754903459ac93d4652ec24723ed2ea38bd6bd70f77d09d5ad8823e"
SOURCE_SHA256 = {
    "scripts/simple_pb05_native.py": "bc3e7ef5d179bc20ad9ef43e1b3de926b7942491144837f6871f4e8087f59d52",
    "scripts/simple_pb05_native_mechanics.py": "9944cea753b2def38191aaf26d1aa5a66b9662197159b4f507c99fb40324089f",
    "scripts/simple_pb03_lower_center_pair.py": "1f066b08f94d92a22ac38d6bc5bb000e90119f1a4c5a4945d8d176e9f8a6c536",
    "scripts/simple_pb03_native.py": "eba830673353ae11ee52d13d264b1542d566ac1a7c41671925dd099066a469a7",
    "scripts/simple_pb04_native.py": "0131871c47e20a5be2f964fc0ba63fbfed3463e292a9fd082889c977fc7db566",
}
GEOMETRY_FINGERPRINT = (
    "74ec72045345fe59ef1a225e85fcc1f608ccd36e6bfa15d8375b576cb5b943f2"
)
DIAGNOSTIC_FINGERPRINT = (
    "9fc6d74b949ec9f82e933182263c8e219cb09b82a5a885b625f4c32e1ae145e3"
)


def _authenticate(path, report, summary, module, rows, mechanics, geometry):
    if _sha256(path) != REPORT_SHA256:
        raise ValueError("PB05 report SHA-256 changed")
    if _sha256(DEFAULT_SUMMARY) != SUMMARY_SHA256:
        raise ValueError("PB05 summary SHA-256 changed")
    for name, digest in SOURCE_SHA256.items():
        if (
            _sha256(ROOT / name) != digest
            or report.get("source_sha256", {}).get(name) != digest
        ):
            raise ValueError(f"PB05 source SHA-256 changed: {name}")
    accepted = summary.get("accepted_cases", {}).get("a12-forward", {})
    scope = report.get("diagnostic_scope", {})
    topology = summary.get("topology_inventory", {})
    if (
        summary.get("accepted_case_count") != 1
        or accepted.get("attempt") != "01-all-unseeded"
        or accepted.get("report_sha256") != REPORT_SHA256
        or accepted.get("numerically_accepted") is not True
        or summary.get("deterministic_input_fingerprint") != DIAGNOSTIC_FINGERPRINT
        or summary.get("loads", {}).get("a12-forward")
        != {"hold": "A12", "horizontal_force_xy_n": [0.0, -300.0]}
        or summary.get("validation", {}).get("accepted_case_equilibrium_audits")
        is not True
        or report.get("candidate") != SOURCE_ID
        or scope.get("case") != "a12-forward"
        or scope.get("contact_update_strategy") != "all"
        or scope.get("search_seed_case") is not None
        or scope.get("deterministic_input_fingerprint") != DIAGNOSTIC_FINGERPRINT
        or report.get("pb05_diagnostic_identity") != DIAGNOSTIC_FINGERPRINT
        or report.get("pb05_mechanics_identity") != mechanics
        or mechanics.get("mechanics_source_id") != MECHANICS_SOURCE_ID
        or mechanics.get("source_fingerprint_sha256") != GEOMETRY_FINGERPRINT
        or geometry.get("source_fingerprint_sha256") != GEOMETRY_FINGERPRINT
        or report.get("artifact_sha256", {}).get("model.pkl")
        != report.get("pb05_model_identity")
        or report.get("parameters", {}).get("hold") != "A12"
        or report.get("parameters", {}).get("force_xyz_n")
        != [0.0, -300.0, -2224.11080763025]
        or any(
            report.get(key) is not True
            for key in (
                "numerically_accepted",
                "global_equilibrium_passed",
                "member_equilibrium_passed",
                "contact_active_set_converged",
                "axial_tension_active_set_converged",
            )
        )
        or any(
            report.get(key) is not False
            for key in (
                "qualified_for_design",
                "actual_joint_demands_qualified",
                "drilling_released",
                "fabrication_released",
                "structural_released",
            )
        )
        or len(rows) != 96
        or sum(row["kind"] == "bolt" for row in rows) != 32
        or sum(row["kind"] == "contact_compression" for row in rows) != 64
        or len(module.panel_connections()) != 66
        or len(module.legacy_proxy_stations()) != 14
        or {
            key: topology.get(key)
            for key in (
                "pb05_tension_only_bolt_count",
                "pb05_contact_cell_count",
                "fixed_panel_kicker_axis_count",
                "legacy_station_count",
            )
        }
        != {
            "pb05_tension_only_bolt_count": 32,
            "pb05_contact_cell_count": 64,
            "fixed_panel_kicker_axis_count": 66,
            "legacy_station_count": 14,
        }
    ):
        raise ValueError("PB05 accepted development identity changed")
    return {
        "mechanics_identity": mechanics,
        "geometry_fingerprint_sha256": GEOMETRY_FINGERPRINT,
        "diagnostic_identity": DIAGNOSTIC_FINGERPRINT,
        "model_identity": report["pb05_model_identity"],
        "source_sha256": SOURCE_SHA256,
        "fixed_panel_kicker_axes": 66,
        "legacy_proxy_stations": 14,
    }


def analyze(report_path=DEFAULT_REPORT):
    """Recover PB05's one accepted case; no result here rates a complete joint."""
    report_path = Path(report_path)
    if _sha256(report_path) != REPORT_SHA256:
        raise ValueError("PB05 report SHA-256 changed")
    report = json.loads(report_path.read_text())
    summary = json.loads(DEFAULT_SUMMARY.read_text())
    module = PB05MechanicsNative()
    rows, mechanics = native_row_inventory(module)
    geometry = screen(module)
    source = _authenticate(
        report_path, report, summary, module, rows, mechanics, geometry
    )
    physical = report.get("physical_connection_forces", {})
    if {row["name"] for row in rows} - set(physical):
        raise ValueError("PB05 physical-force inventory incomplete")
    parts = {part.name: part.shape for part in module.uncut_wood_parts()}
    axes = report["member_section_demands"]
    bolts = []
    for row in rows:
        if row["kind"] != "bolt":
            continue
        name = row["name"]
        force = physical[name]
        axis = _unit(force["axis"], name + " axis")
        host = _vector(force["force_on_first_xyz_n"], name + " host force")
        block = _vector(force["force_on_second_xyz_n"], name + " block force")
        point = _vector(force["point"], name + " point")
        if _norm(tuple(a + b for a, b in zip(host, block, strict=True))) > 1e-7:
            raise ValueError(f"{name}: action/reaction mismatch")
        axial_signed = _dot(host, axis)
        lateral = _subtract(host, _scale(axis, axial_signed))
        shear = _norm(lateral)
        if not math.isclose(shear, force["transverse_shear_n"], abs_tol=1e-6):
            raise ValueError(f"{name}: transverse demand changed")
        members = (row["first_part"], row["second_part"])
        directions, signed, lengths, angles = {}, {}, [], []
        for index, member in enumerate(members):
            grain = _unit(axes[member]["member"]["axis"], member + " grain")
            if abs(_dot(grain, axis)) > 1e-7:
                raise ValueError(f"{member}: bolt not transverse to grain")
            edge = _unit(_cross(grain, axis), member + " edge")
            member_force = lateral if index == 0 else _scale(lateral, -1)
            angle = _angle_to_grain(member_force, grain)
            directions[member] = {
                "lateral_force_xyz_n": member_force,
                "grain_axis_xyz": grain,
                "edge_axis_xyz": edge,
                "grain_force_n": _dot(member_force, grain),
                "edge_force_n": _dot(member_force, edge),
                "load_to_grain_degrees": angle,
            }
            signed[member] = _direction(parts[member], point, member_force, grain, edge)
            lo, hi = _extent(parts[member], axis)
            lengths.append((hi - lo) / quarter.MM_PER_IN)
            angles.append(angle)
        wood = quarter._wood_yield(tuple(lengths), tuple(angles))
        bolts.append(
            {
                "station": row["station"],
                "interface": row["interface"],
                "name": name,
                "members": list(members),
                "point_xyz_mm": point,
                "axis_host_to_block_xyz": axis,
                "force_on_host_xyz_n": host,
                "force_on_block_xyz_n": block,
                "axial_on_host_n": axial_signed,
                "axial_tension_n": max(0.0, axial_signed),
                "lateral_on_host_xyz_n": lateral,
                "transverse_shear_n": shear,
                "member_directions": directions,
                "signed_end_edge": {
                    "members": signed,
                    "passes": all(x["passes"] for x in signed.values()),
                    "scope": "signed orthogonal geometry only; oblique shear area open",
                },
                "wood_yield_bearing_sensitivity": {
                    **wood,
                    "effective_member_bearing_lengths_in": lengths,
                    "demand_n": shear,
                    "ratio": shear / wood["capacity_n"],
                    "qualified": False,
                    "limit": "Gross PB05 solid lengths only; group action, splitting and oblique shear area unresolved.",
                },
            }
        )
    contacts = []
    for row in rows:
        if row["kind"] != "contact_compression":
            continue
        name = row["name"]
        force = physical[name]
        first = _vector(force["force_on_first_xyz_n"], name + " first force")
        second = _vector(force["force_on_second_xyz_n"], name + " second force")
        if _norm(tuple(a + b for a, b in zip(first, second, strict=True))) > 1e-7:
            raise ValueError(f"{name}: contact action/reaction mismatch")
        contacts.append(
            {
                "station": row["station"],
                "interface": row["interface"],
                "name": name,
                "point_xyz_mm": _vector(force["point"], name + " point"),
                "force_on_first_xyz_n": first,
                "force_on_second_xyz_n": second,
            }
        )
    interfaces = _interface_resultants(report, rows)
    return {
        "schema": "simple_pb05_first_case_demand/v1",
        "case": "a12-forward",
        "candidate": SOURCE_ID,
        "report_sha256": REPORT_SHA256,
        "summary_sha256": SUMMARY_SHA256,
        "source_identity": source,
        "bolts": bolts,
        "contacts": contacts,
        "interfaces": interfaces,
        "uncomputed_joint_modes": {
            "group_action": False,
            "net_section": False,
            "splitting": False,
            "oblique_shear_area": False,
            "end_distance_adjusted_yield": False,
            "bolt_steel_shear": False,
            "bolt_steel_tension": False,
            "washer_seat_and_bending": False,
            "washer_wood_bearing": False,
            "bolt_steel_shear_tension_interaction": False,
            "contact_slip_and_clamp_friction": False,
            "other_load_cases": False,
        },
        "scope": "one_authenticated_case_development_only",
        "actual_joint_demands_qualified": False,
        "qualified_for_design": False,
        "drilling_released": False,
        "fabrication_released": False,
        "structural_released": False,
    }


if __name__ == "__main__":
    print(json.dumps(analyze(), indent=2, sort_keys=True))
