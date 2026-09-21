"""Authenticated PB04 a12-forward actions and separate development gates; no release."""

import json
import math
from pathlib import Path

import cadquery as cq

from mini_moonboard.bolted_timber_checks import dfl_axial_wood_bearing_reference_lbf
from scripts import simple_pb03_outer_counterbore_revision as pocket
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
from scripts.simple_pb03_native import REPLACED_STATIONS
from scripts.simple_pb04_native import SOURCE_ID, PB04Native
from scripts.simple_pb04_native import screen as geometry_screen
from scripts.simple_pb04_native_mechanics import (
    MECHANICS_SOURCE_ID,
    native_row_inventory,
)

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REPORT = ROOT / (
    "fea/results/diagnostics/pb04-eight-station-a12-forward-v1/attempts/"
    "a12-forward-01-all-unseeded/report.json"
)
REPORT_SHA256 = "23ed26f229d18ca956696f433a40f8d66297a052d5d2b95b7150f2a4830bf1cd"
SOURCE_SHA256 = {
    "scripts/simple_pb04_native.py": "0131871c47e20a5be2f964fc0ba63fbfed3463e292a9fd082889c977fc7db566",
    "scripts/simple_pb04_native_mechanics.py": "89b21168aff804d7871c657365512ab1738dd8d067002115af1d05b0c7e9b302",
    "scripts/simple_pb03_outer_counterbore_revision.py": "b2a171b5afe85255c59de87d8d5b36fc7a7dc296a28266f5b27c6e3f133e2457",
    "scripts/simple_pb03_upper_outer_edge_revision.py": "4c9d138d010018115352abb9015c2df1b0e042bf05180b2a2443e5b6f7a3faf6",
}
# Filled from the checked PB04 CAD source; changing geometry invalidates this decision.
GEOMETRY_FINGERPRINT = (
    "81dd490b2da7618c468d2bebe0eba4f914949b54f28801330b581e31473797a5"
)


def _authenticate(path, report, module, rows, mechanics, geometry):
    if _sha256(path) != REPORT_SHA256:
        raise ValueError("PB04 report SHA-256 changed")
    for name, digest in SOURCE_SHA256.items():
        if (
            _sha256(ROOT / name) != digest
            or report.get("source_sha256", {}).get(name) != digest
        ):
            raise ValueError(f"PB04 source SHA-256 changed: {name}")
    if (
        GEOMETRY_FINGERPRINT is None
        or geometry["source_fingerprint_sha256"] != GEOMETRY_FINGERPRINT
    ):
        raise ValueError("PB04 geometry fingerprint changed")
    scope = report.get("diagnostic_scope", {})
    if (
        report.get("candidate") != SOURCE_ID
        or scope.get("case") != "a12-forward"
        or scope.get("deterministic_input_fingerprint")
        != report.get("pb04_diagnostic_identity")
        or report.get("pb04_mechanics_identity") != mechanics
        or mechanics.get("mechanics_source_id") != MECHANICS_SOURCE_ID
        or mechanics.get("replaced_stations") != list(REPLACED_STATIONS)
        or report.get("artifact_sha256", {}).get("model.pkl")
        != report.get("pb04_model_identity")
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
            )
        )
        or len(rows) != 96
        or len(module.panel_connections()) != 66
        or geometry["combined_geometry_gates_pass"] is not True
    ):
        raise ValueError("PB04 accepted development identity changed")
    return {
        "mechanics_identity": mechanics,
        "geometry_fingerprint_sha256": GEOMETRY_FINGERPRINT,
        "diagnostic_identity": report["pb04_diagnostic_identity"],
        "model_identity": report["pb04_model_identity"],
        "source_sha256": SOURCE_SHA256,
        "fixed_panel_kicker_axes": 66,
    }


def _extent(shape, axis):
    values = [vertex.Center().dot(cq.Vector(*axis)) for vertex in shape.Vertices()]
    return min(values), max(values)


def _signed_distance(shape, point, force, axis, loaded_required, unloaded_required):
    minimum, maximum = _extent(shape, axis)
    coordinate = _dot(point, axis)
    component = _dot(force, axis)
    if abs(component) <= 1e-9:
        return {
            "force_component_n": component,
            "sign": "neutral",
            "applicable": False,
            "passes": True,
        }
    positive = component > 0
    loaded = maximum - coordinate if positive else coordinate - minimum
    unloaded = coordinate - minimum if positive else maximum - coordinate
    return {
        "force_component_n": component,
        "sign": "positive" if positive else "negative",
        "applicable": True,
        "loaded_distance_mm": loaded,
        "unloaded_distance_mm": unloaded,
        "loaded_required_mm": loaded_required,
        "unloaded_required_mm": unloaded_required,
        "loaded_margin_mm": loaded - loaded_required,
        "unloaded_margin_mm": unloaded - unloaded_required,
        "passes": loaded + 1e-8 >= loaded_required
        and unloaded + 1e-8 >= unloaded_required,
    }


def _direction(shape, point, force, grain, edge):
    diameter = quarter.SHAFT_DIAMETER_MM
    end = _signed_distance(shape, point, force, grain, 7 * diameter, 4 * diameter)
    side = _signed_distance(shape, point, force, edge, 4 * diameter, 1.5 * diameter)
    return {
        "grain_end": end,
        "cross_grain_edge": side,
        "passes": end["passes"] and side["passes"],
    }


def analyze(report_path=DEFAULT_REPORT):
    """Recover one simultaneous PB04 case; conditional modes never form a joint rating."""
    report_path = Path(report_path)
    if _sha256(report_path) != REPORT_SHA256:
        raise ValueError("PB04 report SHA-256 changed")
    report = json.loads(report_path.read_text())
    module = PB04Native()
    rows, mechanics = native_row_inventory(module)
    geometry = geometry_screen(module)
    source = _authenticate(report_path, report, module, rows, mechanics, geometry)
    physical = report.get("physical_connection_forces", {})
    if {row["name"] for row in rows} - set(physical):
        raise ValueError("PB04 physical-force inventory incomplete")
    parts = {part.name: part.shape for part in module.uncut_wood_parts()}
    machined = {part.name: part.shape for part in module.wood_parts()}
    axes = report.get("member_section_demands", {})
    steel_shear = (
        quarter.CONDITIONAL_SHEAR_STRESS_PSI
        * quarter.TENSILE_STRESS_AREA_IN2
        * quarter.N_PER_LBF
    )
    steel_tension = (
        quarter.CONDITIONAL_TENSION_STRESS_PSI
        * quarter.TENSILE_STRESS_AREA_IN2
        * quarter.N_PER_LBF
    )
    washer = (
        dfl_axial_wood_bearing_reference_lbf(
            pocket.WASHER_OUTSIDE_DIAMETER_MM / quarter.MM_PER_IN,
            quarter.BORE_DIAMETER_MM / quarter.MM_PER_IN,
            quarter.NOMINAL_DIAMETER_IN,
        )
        * quarter.N_PER_LBF
    )
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
        directions = {}
        length_in = []
        angles = []
        signed = {}
        for index, member in enumerate(members):
            grain = _unit(axes[member]["member"]["axis"], member + " grain")
            if abs(_dot(grain, axis)) > 1e-7:
                raise ValueError(f"{member}: bolt not transverse to grain")
            edge = _unit(_cross(grain, axis), member + " edge")
            member_force = lateral if index == 0 else _scale(lateral, -1)
            directions[member] = {
                "lateral_force_xyz_n": member_force,
                "grain_axis_xyz": grain,
                "edge_axis_xyz": edge,
                "grain_force_n": _dot(member_force, grain),
                "edge_force_n": _dot(member_force, edge),
                "load_to_grain_degrees": _angle_to_grain(member_force, grain),
            }
            signed[member] = _direction(parts[member], point, member_force, grain, edge)
            if index == 1 and name in {
                "pb03_upper_outer_left_rail_1",
                "pb03_upper_outer_right_rail_1",
            }:
                end = signed[member]["grain_end"]
                # ponytail: classify only the two authenticated short BLOCK ends.
                minimum = 3.5 * quarter.SHAFT_DIAMETER_MM
                full = 7 * quarter.SHAFT_DIAMETER_MM
                if end["force_component_n"] >= 0:
                    raise ValueError(f"{name}: BLOCK short-end action changed sign")
                end.update(
                    minimum_loaded_mm=minimum,
                    full_value_loaded_mm=full,
                    full_value_attained=end["loaded_distance_mm"] >= full,
                    loaded_required_mm=minimum,
                    loaded_margin_mm=end["loaded_distance_mm"] - minimum,
                    passes=end["loaded_distance_mm"] >= minimum
                    and end["unloaded_distance_mm"] >= end["unloaded_required_mm"],
                    classification="softwood tension component; oblique lateral action",
                    oblique_shear_area_qualified=False,
                )
                signed[member]["passes"] = (
                    end["passes"] and signed[member]["cross_grain_edge"]["passes"]
                )
            lo, hi = _extent(parts[member], axis)
            effective = hi - lo
            if (
                index == 1
                and row["station"] in pocket.TARGET_STATIONS
                and row["interface"] == "upright"
            ):
                effective -= pocket._required_depth_mm()
            length_in.append(effective / quarter.MM_PER_IN)
            angles.append(directions[member]["load_to_grain_degrees"])
        wood = quarter._wood_yield(tuple(length_in), tuple(angles))
        axial = max(0.0, axial_signed)
        checks = {
            "wood_yield_bearing_sensitivity": {
                **wood,
                "effective_member_bearing_lengths_in": length_in,
                "demand_n": shear,
                "ratio": shear / wood["capacity_n"],
                "qualified": False,
                "limit": "Pocket-reduced axial length for upright block; gross rail bearing remains sensitivity only; local pocket net-section and splitting unqualified.",
            },
            "bolt_shear": {
                "demand_n": shear,
                "conditional_capacity_n": steel_shear,
                "ratio": shear / steel_shear,
            },
            "bolt_tension": {
                "demand_n": axial,
                "conditional_capacity_n": steel_tension,
                "ratio": axial / steel_tension,
            },
            "washer_wood_bearing_sensitivity": {
                "demand_n": axial,
                "conditional_full_annulus_n": washer,
                "ratio": axial / washer,
                "qualified": False,
                "limit": "Ideal full-contact pocket-seat annulus only; net block, washer bending, and seat flatness unresolved.",
            },
            "signed_end_edge": {
                "members": signed,
                "passes": all(item["passes"] for item in signed.values()),
                "scope": "signed orthogonal components only; oblique shear-area check open",
            },
        }
        if name in {
            "pb03_upper_outer_left_rail_1",
            "pb03_upper_outer_right_rail_1",
        }:
            end = signed[members[1]]["grain_end"]
            factor = min(1.0, end["loaded_distance_mm"] / end["full_value_loaded_mm"])
            reference = wood["capacity_n"] * factor
            checks["wood_yield_bearing_sensitivity"][
                "conditional_block_end_distance"
            ] = {
                "provision": "2024 NDS 12.5.1.2(a), Table 12.5.1A; softwood tension end component; 12.5.1.2(b) oblique shear area still open",
                "geometry_factor": factor,
                "conditional_reference_n": reference,
                "demand_n": shear,
                "conditional_ratio": shear / reference,
                "geometry_scope": "initial_authenticated_PB04_only",
                "joint_rating": False,
                "oblique_shear_area_qualified": False,
                "limit": "End-distance factor on isolated yield reference only; oblique action, other geometry factors, group transfer, pockets, and splitting remain unqualified.",
            }
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
                "axial_tension_n": axial,
                "lateral_on_host_xyz_n": lateral,
                "transverse_shear_n": shear,
                "member_directions": directions,
                "separate_checks": checks,
            }
        )
    bolts.sort(key=lambda row: (REPLACED_STATIONS.index(row["station"]), row["name"]))
    interfaces = _interface_resultants(report, rows)
    ligaments = geometry["minimum_clearances_mm"]
    local = []
    for station in pocket.TARGET_STATIONS:
        block_name = module.pb03_geometries()[station].block_name
        gross = parts[block_name]
        cut = machined[block_name]
        upright_interface = next(
            row
            for row in interfaces
            if row["station"] == station and row["interface"] == "upright"
        )
        upright = [
            row
            for row in bolts
            if row["station"] == station and row["interface"] == "upright"
        ]
        local.append(
            {
                "station": station,
                "block": block_name,
                "pocket_count": len(upright),
                "gross_block_length_mm": pocket.lower.BLOCK_X_MM,
                "remaining_axial_wood_mm": pocket.lower.BLOCK_X_MM
                - pocket._required_depth_mm(),
                "gross_block_volume_mm3": gross.Volume(),
                "machined_block_volume_mm3": cut.Volume(),
                "pocket_to_outer_edge_ligament_mm": pocket.lower.BLOCK_T_MM / 2
                - pocket.FORSTNER_DIAMETER_MM / 2,
                "between_pockets_ligament_mm": abs(
                    pocket.lower.UPRIGHT_N_OFFSETS_MM[0]
                    - pocket.lower.UPRIGHT_N_OFFSETS_MM[1]
                )
                - pocket.FORSTNER_DIAMETER_MM,
                "upright_pair_force_on_block_xyz_n": tuple(
                    math.fsum(row["force_on_block_xyz_n"][i] for row in upright)
                    for i in range(3)
                ),
                "upright_interface_force_on_block_xyz_n": upright_interface[
                    "force_on_block_xyz_n"
                ],
                "upright_interface_moment_nmm": upright_interface[
                    "moment_about_interface_centroid_nmm"
                ],
                "net_section_capacity_qualified": False,
                "bolt_group_qualified": False,
                "splitting_qualified": False,
            }
        )
    ratios = {
        key: max(row["separate_checks"][key]["ratio"] for row in bolts)
        for key in (
            "wood_yield_bearing_sensitivity",
            "bolt_shear",
            "bolt_tension",
            "washer_wood_bearing_sensitivity",
        )
    }
    failed = [
        row["name"]
        for row in bolts
        if not row["separate_checks"]["signed_end_edge"]["passes"]
    ]
    over = [name for name, ratio in ratios.items() if ratio > 1]
    reason = (
        "Conditional separate component comparator exceeds unity."
        if over
        else "Signed minimum edge/end geometry fails in this case."
        if failed
        else "Two BLOCK ends require reduced C_delta; counterbore net-section, paired-bolt group action, and splitting remain unqualified; one case is not an envelope."
    )
    if over:
        revision = (
            "Revise the governing component geometry/material and rerun this same "
            "case before extending the load envelope."
        )
    elif failed:
        revision = "Resolve the failed signed minimum geometry before proceeding."
    else:
        revision = (
            "For initial PB04 geometry, check both 1-inch pockets in each outer "
            "block as a cut-net-section, two-bolt group, and splitting system "
            "under simultaneous interface force/moment, then run the other five cases. "
            "Any altered geometry needs its own screen and same-case solve."
        )
    return {
        "schema": "simple_pb04_first_case_demand/v1",
        "case": "a12-forward",
        "candidate": SOURCE_ID,
        "report_sha256": REPORT_SHA256,
        "source_identity": source,
        "bolts": bolts,
        "interfaces": interfaces,
        "counterbore_local_gates": {
            "stations": local,
            "minimum_cad_clearances_mm": ligaments,
            "net_section_qualified": False,
            "group_action_qualified": False,
            "splitting_qualified": False,
            "limit": "Positive CAD ligaments and an isolated dowel-yield comparator do not rate a counterbored joint.",
        },
        "summary": {
            "maximum_transverse_shear_n": max(
                row["transverse_shear_n"] for row in bolts
            ),
            "maximum_axial_tension_n": max(row["axial_tension_n"] for row in bolts),
            "maximum_separate_component_ratios": ratios,
            "failed_signed_edge_end_bolts": failed,
            "development_decision": "REJECT" if over else "REVISE",
            "reason": reason,
            "exact_next_physical_revision_or_gate": revision,
            "scope": "one_authenticated_case_development_only",
            "altered_geometry_assessed": False,
        },
        "capacity_aggregation": "prohibited_serial_components_not_combined",
        "actual_joint_demands_qualified": False,
        "qualified_for_design": False,
        "drilling_released": False,
        "fabrication_released": False,
        "structural_released": False,
    }


if __name__ == "__main__":
    print(json.dumps(analyze(), indent=2, sort_keys=True))
