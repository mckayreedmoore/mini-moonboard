"""Source-bound PB03 a12-forward demand/direction screen; no release."""

import hashlib
import json
import math
from pathlib import Path

import cadquery as cq

from mini_moonboard.bolted_timber_checks import dfl_axial_wood_bearing_reference_lbf
from mini_moonboard.bolted_wood_wood_yield import (
    dowel_bending_yield_moment_lb_in,
    wood_wood_single_shear_reference,
)
from scripts.simple_pb03_native import (
    BLOCK_GRAIN_AXIS,
    REPLACED_STATIONS,
    SOURCE_ID,
    PB03Native,
)
from scripts.simple_pb03_native_mechanics import (
    MECHANICS_SOURCE_ID,
    native_row_inventory,
)
from scripts.simple_pb03_three_eighths_geometry import build_geometries

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REPORT = ROOT / (
    "fea/results/diagnostics/pb03-eight-station-a12-forward-v1/attempts/"
    "a12-forward-01-all-unseeded/report.json"
)
REPORT_SHA256 = "a2f203541c52cff205e432d4043c722c0b1df4cfc3b850c2fae4dbae9688c93e"
EXPECTED_SOURCE_SHA256 = {
    "scripts/simple_pb03_native.py": (
        "eba830673353ae11ee52d13d264b1542d566ac1a7c41671925dd099066a469a7"
    ),
    "scripts/simple_pb03_native_mechanics.py": (
        "d705e301099aa243da3240517940d1be7e4a1e87cf9a00a0df84e9e7bfa4dfac"
    ),
    "scripts/simple_pb03_three_eighths_geometry.py": (
        "44e483353712f908e476f37accfda1b83f12c3422475415790304e99974a6bfa"
    ),
}
N_PER_LBF = 4.4482216152605
MM_PER_IN = 25.4
MODES = ("Im", "Is", "II", "IIIm", "IIIs", "IV")
DIAMETERS = {
    "quarter_in": {
        "nominal_in": 0.25,
        "root_in": 0.189,
        "bore_mm": 7.5,
        "tensile_area_in2": 0.0318,
        "washer_od_in": 0.734,
        "washer_id_in": 0.312,
    },
    "three_eighths_in": {
        "nominal_in": 0.375,
        "root_in": 0.298,
        "bore_mm": 11.1125,
        "tensile_area_in2": 0.0775,
        "washer_od_in": 1.0,
        "washer_id_in": 13 / 32,
    },
}


def _sha256(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _vector(values, label):
    if (
        not isinstance(values, (list, tuple))
        or len(values) != 3
        or any(
            not isinstance(value, (int, float))
            or isinstance(value, bool)
            or not math.isfinite(value)
            for value in values
        )
    ):
        raise ValueError(f"invalid {label}")
    return tuple(float(value) for value in values)


def _dot(first, second):
    return math.fsum(a * b for a, b in zip(first, second, strict=True))


def _norm(vector):
    return math.sqrt(_dot(vector, vector))


def _scale(vector, scalar):
    return tuple(scalar * value for value in vector)


def _subtract(first, second):
    return tuple(a - b for a, b in zip(first, second, strict=True))


def _cross(first, second):
    return (
        first[1] * second[2] - first[2] * second[1],
        first[2] * second[0] - first[0] * second[2],
        first[0] * second[1] - first[1] * second[0],
    )


def _unit(vector, label):
    vector = _vector(vector, label)
    magnitude = _norm(vector)
    if not math.isclose(magnitude, 1.0, abs_tol=1e-8):
        raise ValueError(f"{label} is not a unit vector")
    return tuple(value / magnitude for value in vector)


def _angle_to_grain(force, grain):
    magnitude = _norm(force)
    if magnitude <= 1e-12:
        return 0.0
    cosine = min(1.0, abs(_dot(force, grain)) / magnitude)
    return math.degrees(math.acos(cosine))


def _source_identity(report_path, report, module, mechanics_identity, active, larger):
    if _sha256(report_path) != REPORT_SHA256:
        raise ValueError("PB03 report SHA-256 changed")
    current = {name: _sha256(ROOT / name) for name in EXPECTED_SOURCE_SHA256}
    if current != EXPECTED_SOURCE_SHA256:
        raise ValueError("PB03 analyzer geometry source SHA-256 changed")
    if any(
        report.get("source_sha256", {}).get(name) != expected
        for name, expected in EXPECTED_SOURCE_SHA256.items()
        if name != "scripts/simple_pb03_three_eighths_geometry.py"
    ):
        raise ValueError("PB03 report source identity changed")
    scope = report.get("diagnostic_scope", {})
    if (
        report.get("candidate") != SOURCE_ID
        or scope.get("case") != "a12-forward"
        or report.get("numerically_accepted") is not True
        or report.get("global_equilibrium_passed") is not True
        or report.get("member_equilibrium_passed") is not True
        or report.get("contact_active_set_converged") is not True
        or report.get("axial_tension_active_set_converged") is not True
        or report.get("pb03_mechanics_identity") != mechanics_identity
        or mechanics_identity.get("mechanics_source_id") != MECHANICS_SOURCE_ID
        or report.get("qualified_for_design") is not False
        or report.get("actual_joint_demands_qualified") is not False
        or report.get("drilling_released") is not False
        or report.get("fabrication_released") is not False
    ):
        raise ValueError("PB03 accepted developmental report identity changed")
    if tuple(active) != REPLACED_STATIONS or tuple(larger) != REPLACED_STATIONS:
        raise ValueError("PB03 geometry station identity changed")
    return {
        "report_numerically_accepted": True,
        "diagnostic_input_fingerprint": report["pb03_diagnostic_identity"],
        "model_identity": report["pb03_model_identity"],
        "mechanics_identity": mechanics_identity,
        "source_sha256": current,
        "pb03_bolt_count": 32,
        "pb03_contact_cell_count": 64,
        "active_geometry_station_count": len(active),
        "three_eighths_geometry_station_count": len(larger),
        "fixed_panel_kicker_axes": len(module.panel_connections()),
    }


def _member_axes(member_axes, member, bolt_axis):
    if member not in member_axes:
        raise ValueError(f"missing PB03 report member grain axis: {member}")
    grain = _unit(member_axes[member], member + " grain")
    if (
        member.startswith("pb03_")
        and member.endswith("_block")
        and any(
            not math.isclose(left, right, abs_tol=1e-8)
            for left, right in zip(grain, BLOCK_GRAIN_AXIS.toTuple(), strict=True)
        )
    ):
        raise ValueError(f"{member}: report block grain axis changed")
    if abs(_dot(grain, bolt_axis)) > 1e-7:
        raise ValueError(f"{member}: bolt axis is not transverse to grain")
    edge = _unit(_cross(grain, bolt_axis), member + " edge")
    return grain, edge


def _distances(shape, point, axis):
    positions = [vertex.Center().dot(cq.Vector(*axis)) for vertex in shape.Vertices()]
    coordinate = _dot(point, axis)
    return coordinate - min(positions), max(positions) - coordinate


def _direction_check(shape, point, force, grain, edge, diameter_mm):
    result = {}
    passed = True
    for label, axis, loaded_multiple, unloaded_multiple in (
        ("grain_end", grain, 7.0, 4.0),
        ("cross_grain_edge", edge, 4.0, 1.5),
    ):
        negative, positive = _distances(shape, point, axis)
        component = _dot(force, axis)
        if abs(component) <= 1e-9:
            row = {
                "force_component_n": component,
                "force_sign": "neutral",
                "loaded_distance_mm": None,
                "unloaded_distance_mm": None,
                "loaded_margin_mm": None,
                "unloaded_margin_mm": None,
                "applicable": False,
                "passes": True,
            }
        else:
            positive_force = component > 0
            loaded = positive if positive_force else negative
            unloaded = negative if positive_force else positive
            loaded_margin = loaded - loaded_multiple * diameter_mm
            unloaded_margin = unloaded - unloaded_multiple * diameter_mm
            row = {
                "force_component_n": component,
                "force_sign": "positive" if positive_force else "negative",
                "loaded_distance_mm": loaded,
                "unloaded_distance_mm": unloaded,
                "loaded_margin_mm": loaded_margin,
                "unloaded_margin_mm": unloaded_margin,
                "applicable": True,
                "passes": min(loaded_margin, unloaded_margin) >= -1e-8,
            }
        passed = passed and row["passes"]
        result[label] = row
    return {"coordinates": result, "passes": passed}


def _capacity(diameter, lengths_in, angles):
    nominal = diameter["nominal_in"]
    root = diameter["root_in"]
    factor = 1 + 0.25 * max(angles) / 90
    if root < 0.25:
        reductions = dict.fromkeys(MODES, (10 * root + 0.5) * factor)
    else:
        reductions = dict(zip(MODES, (4, 4, 3.6, 3.2, 3.2, 3.2), strict=True))
        reductions = {name: value * factor for name, value in reductions.items()}
    yield_result = wood_wood_single_shear_reference(
        main_bearing_length_in=lengths_in[0],
        side_bearing_length_in=lengths_in[1],
        main_load_to_grain_degrees=angles[0],
        side_load_to_grain_degrees=angles[1],
        main_bolt_axis_parallel_to_grain=False,
        side_bolt_axis_parallel_to_grain=False,
        bolt_full_body_diameter_in=nominal,
        bolt_thread_root_diameter_in=root,
        main_thread_bearing_length_in=lengths_in[0],
        side_thread_bearing_length_in=lengths_in[1],
        bolt_bending_yield_moment_lb_in=dowel_bending_yield_moment_lb_in(
            bending_yield_strength_psi=45_000, effective_diameter_in=root
        ),
        bolt_bending_yield_strength_psi=45_000,
        gap_in=0.0,
        reduction_terms=reductions,
    )
    area = diameter["tensile_area_in2"]
    return {
        "wood_yield_n": yield_result["reference_lateral_lbf"] * N_PER_LBF,
        "wood_yield_mode": yield_result["governing_mode"],
        "bolt_steel_shear_n": 27_000 / 2 * area * N_PER_LBF,
        "bolt_steel_tension_n": 45_000 / 2 * area * N_PER_LBF,
        "washer_wood_bearing_n": dfl_axial_wood_bearing_reference_lbf(
            diameter["washer_od_in"],
            diameter["bore_mm"] / MM_PER_IN,
            diameter["washer_id_in"],
        )
        * N_PER_LBF,
    }


def _interface_resultants(report, rows):
    physical = report["physical_connection_forces"]
    grouped = {}
    for row in rows:
        grouped.setdefault((row["station"], row["interface"]), []).append(row)
    result = []
    for (station, interface), members in grouped.items():
        contacts = [row for row in members if row["kind"] == "contact_compression"]
        bolts = [row for row in members if row["kind"] == "bolt"]
        centroid = tuple(
            math.fsum(row["point_mm"][index] for row in contacts) / len(contacts)
            for index in range(3)
        )
        actions = []
        for row in members:
            source = physical[row["name"]]
            force_key = (
                "force_on_second_xyz_n"
                if row["kind"] == "bolt"
                else "force_on_first_xyz_n"
            )
            actions.append(
                (
                    _vector(source["point"], row["name"] + " point"),
                    _vector(source[force_key], row["name"] + " force"),
                )
            )
        force = tuple(math.fsum(item[1][i] for item in actions) for i in range(3))
        moment = tuple(
            math.fsum(
                _cross(_subtract(point, centroid), action)[i]
                for point, action in actions
            )
            for i in range(3)
        )
        result.append(
            {
                "station": station,
                "interface": interface,
                "block": bolts[0]["second_part"],
                "host": bolts[0]["first_part"],
                "interface_centroid_xyz_mm": centroid,
                "force_on_block_xyz_n": force,
                "force_magnitude_n": _norm(force),
                "moment_about_interface_centroid_nmm": moment,
                "moment_magnitude_nmm": _norm(moment),
                "connector_count": len(members),
                "bolt_count": len(bolts),
                "contact_cell_count": len(contacts),
            }
        )
    return sorted(
        result,
        key=lambda row: (REPLACED_STATIONS.index(row["station"]), row["interface"]),
    )


def analyze(report_path=DEFAULT_REPORT):
    """Recover the exact first-case PB03 actions and conditional comparisons."""
    report_path = Path(report_path)
    report = json.loads(report_path.read_text())
    module = PB03Native()
    active = module.pb03_geometries()
    larger = build_geometries()
    rows, mechanics_identity = native_row_inventory(module)
    source_identity = _source_identity(
        report_path, report, module, mechanics_identity, active, larger
    )
    parts = {part.name: part.shape for part in module.uncut_wood_parts()}
    member_axes = {
        name: record["member"]["axis"]
        for name, record in report.get("member_section_demands", {}).items()
    }
    bolt_rows = [row for row in rows if row["kind"] == "bolt"]
    physical = report.get("physical_connection_forces", {})
    if {row["name"] for row in rows} - set(physical):
        raise ValueError("PB03 report physical-force inventory is incomplete")

    bolts = []
    for row in bolt_rows:
        source = physical[row["name"]]
        geometry = active[row["station"]]
        if row["name"] not in {item.name for item in geometry.bolts}:
            raise ValueError(f"{row['name']}: active PB03 bolt identity changed")
        axis = _unit(source["axis"], row["name"] + " axis")
        force_host = _vector(
            source["force_on_first_xyz_n"], row["name"] + " host force"
        )
        force_block = _vector(
            source["force_on_second_xyz_n"], row["name"] + " block force"
        )
        if (
            _norm(tuple(a + b for a, b in zip(force_host, force_block, strict=True)))
            > 1e-7
        ):
            raise ValueError(f"{row['name']}: force pair does not close")
        axial = _dot(force_host, axis)
        lateral_host = _subtract(force_host, _scale(axis, axial))
        lateral = _norm(lateral_host)
        if not math.isclose(lateral, source["transverse_shear_n"], abs_tol=1e-6):
            raise ValueError(f"{row['name']}: transverse force changed")

        members = {}
        for member, force in (
            (row["first_part"], lateral_host),
            (row["second_part"], _scale(lateral_host, -1)),
        ):
            grain, edge = _member_axes(member_axes, member, axis)
            members[member] = {
                "lateral_force_xyz_n": force,
                "grain_axis_xyz": grain,
                "edge_axis_xyz": edge,
                "grain_force_n": _dot(force, grain),
                "edge_force_n": _dot(force, edge),
                "load_to_grain_degrees": _angle_to_grain(force, grain),
            }

        point = _vector(row["point_mm"], row["name"] + " point")
        projections = {}
        for member in row["first_part"], row["second_part"]:
            projections[member] = max(
                vertex.Center().dot(cq.Vector(*axis))
                for vertex in parts[member].Vertices()
            ) - min(
                vertex.Center().dot(cq.Vector(*axis))
                for vertex in parts[member].Vertices()
            )
        lengths = tuple(
            projections[name] / MM_PER_IN
            for name in (row["first_part"], row["second_part"])
        )
        angles = tuple(
            members[name]["load_to_grain_degrees"]
            for name in (row["first_part"], row["second_part"])
        )

        diameter_checks = {}
        for key, diameter in DIAMETERS.items():
            geometry = (
                active[row["station"]]
                if key == "quarter_in"
                else larger[row["station"]]
            )
            candidate = next(
                item for item in geometry.bolts if item.name == row["name"]
            )
            checks = {
                member: _direction_check(
                    parts[member] if member != geometry.block_name else geometry.block,
                    point,
                    members[member]["lateral_force_xyz_n"],
                    members[member]["grain_axis_xyz"],
                    members[member]["edge_axis_xyz"],
                    diameter["nominal_in"] * MM_PER_IN,
                )
                for member in (row["first_part"], row["second_part"])
            }
            capacity = _capacity(diameter, lengths, angles)
            axial_tension = max(0.0, axial)
            ratios = {
                "wood_yield": lateral / capacity["wood_yield_n"],
                "bolt_steel_shear": lateral / capacity["bolt_steel_shear_n"],
                "bolt_steel_tension": axial_tension / capacity["bolt_steel_tension_n"],
                "washer_wood_bearing": axial_tension
                / capacity["washer_wood_bearing_n"],
            }
            diameter_checks[key] = {
                "nominal_diameter_mm": candidate.diameter,
                "bore_diameter_mm": geometry.report["bore_diameter_mm"],
                "member_geometry": checks,
                "geometry_passes": all(item["passes"] for item in checks.values()),
                "conditional_component_capacities_n": capacity,
                "component_ratios": ratios,
                "governing_component": max(ratios, key=ratios.get),
                "governing_component_ratio": max(ratios.values()),
            }
        bolts.append(
            {
                "station": row["station"],
                "interface": row["interface"],
                "name": row["name"],
                "members": [row["first_part"], row["second_part"]],
                "point_xyz_mm": point,
                "axis_host_to_block_xyz": axis,
                "force_on_host_xyz_n": force_host,
                "force_on_block_xyz_n": force_block,
                "axial_on_host_n": axial,
                "axial_on_host_xyz_n": _scale(axis, axial),
                "axial_tension_n": max(0.0, axial),
                "lateral_on_host_xyz_n": lateral_host,
                "transverse_shear_n": lateral,
                "member_directions": members,
                "diameter_checks": diameter_checks,
            }
        )

    diameter_summary = {}
    for key in DIAMETERS:
        failed = sorted(
            {
                row["station"]
                for row in bolts
                if not row["diameter_checks"][key]["geometry_passes"]
            },
            key=REPLACED_STATIONS.index,
        )
        governing = max(
            bolts,
            key=lambda row: row["diameter_checks"][key]["governing_component_ratio"],
        )
        diameter_summary[key] = {
            "failed_geometry_stations": failed,
            "geometry_passes": not failed,
            "governing_bolt": governing["name"],
            "governing_component": governing["diameter_checks"][key][
                "governing_component"
            ],
            "maximum_conditional_component_ratio": governing["diameter_checks"][key][
                "governing_component_ratio"
            ],
        }
    maximum_demand = max(
        (row for row in bolts),
        key=lambda row: max(row["transverse_shear_n"], row["axial_tension_n"]),
    )
    maximum_ratio = max(
        item["maximum_conditional_component_ratio"]
        for item in diameter_summary.values()
    )
    both_over = all(
        item["maximum_conditional_component_ratio"] > 1
        for item in diameter_summary.values()
    )
    decision = (
        "REJECT"
        if both_over
        else "REVISE"
        if any(item["failed_geometry_stations"] for item in diameter_summary.values())
        else "ADVANCE"
    )
    return {
        "schema": "simple_pb03_first_case_demand/v1",
        "case": "a12-forward",
        "candidate": SOURCE_ID,
        "report_sha256": REPORT_SHA256,
        "source_identity": source_identity,
        "bolts": bolts,
        "interfaces": _interface_resultants(report, rows),
        "summary": {
            "maximum_demand_n": max(
                maximum_demand["transverse_shear_n"], maximum_demand["axial_tension_n"]
            ),
            "maximum_demand_bolt": maximum_demand["name"],
            "maximum_conditional_component_ratio": maximum_ratio,
            **diameter_summary,
            "decision": decision,
            "decision_scope": "development_only",
            "basis": "one authenticated first case; geometry and component modes remain separate",
        },
        "capacity_aggregation": "prohibited_serial_components_not_combined",
        "developmental_only": True,
        "actual_joint_demands_qualified": False,
        "acceptance": False,
        "qualified_for_design": False,
        "drilling_released": False,
        "fabrication_released": False,
        "structural_released": False,
    }


if __name__ == "__main__":
    print(json.dumps(analyze(), indent=2, sort_keys=True))
