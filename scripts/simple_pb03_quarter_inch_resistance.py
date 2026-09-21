"""Active PB03 quarter-inch component screen for one accepted case; no release."""

import hashlib
import json
import math
from pathlib import Path

import cadquery as cq

from mini_moonboard.bolted_timber_checks import (
    dfl_axial_wood_bearing_reference_lbf,
    dfl_parallel_row_tear_out_reference_lbf,
)
from mini_moonboard.bolted_wood_wood_yield import (
    dowel_bending_yield_moment_lb_in,
    wood_wood_single_shear_reference,
)
from scripts.simple_pb03_native import REPLACED_STATIONS, SOURCE_ID, PB03Native

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REPORT = (
    ROOT / "fea/results/diagnostics/pb03-eight-station-a12-forward-v1/attempts/"
    "a12-forward-01-all-unseeded/report.json"
)
REPORT_SHA256 = "a2f203541c52cff205e432d4043c722c0b1df4cfc3b850c2fae4dbae9688c93e"

MM_PER_IN = 25.4
N_PER_LBF = 4.4482216152605
NOMINAL_DIAMETER_IN = 0.25
SHAFT_DIAMETER_MM = NOMINAL_DIAMETER_IN * MM_PER_IN
BORE_DIAMETER_MM = 7.5
THREAD_ROOT_DIAMETER_IN = 0.189
TENSILE_STRESS_AREA_IN2 = 0.0318
A307_GRADE_A_MINIMUM_TENSILE_PSI = 60_000.0
CONDITIONAL_BENDING_YIELD_PSI = 45_000.0
CONDITIONAL_TENSION_STRESS_PSI = 45_000.0 / 2
CONDITIONAL_SHEAR_STRESS_PSI = 27_000.0 / 2
WASHER_OUTSIDE_DIAMETER_IN = 0.625
MODES = ("Im", "Is", "II", "IIIm", "IIIs", "IV")

HARDWARE_LEADS = {
    "five_inch": {
        "product": "Everbilt 805426",
        "retailer": "Home Depot",
        "nominal_size": "1/4-20 x 5 in",
        "form": "factory_hex_bolt",
        "listing_basis": "ASTM A307; fully threaded product lead",
        "selected": False,
        "scope_procurement_gate": False,
    },
    "eight_inch": {
        "product": "Everbilt 800696",
        "retailer": "Home Depot",
        "nominal_size": "1/4-20 x 8 in",
        "form": "factory_hex_bolt",
        "listing_basis": "ASTM A307; six-inch listed thread length",
        "selected": False,
        "scope_procurement_gate": False,
    },
    "outer_ten_inch_sensitivity": {
        "product": "National Hardware N179-416",
        "retailer": "Lowe's product-data lead; current ordinary-store availability unverified",
        "nominal_size": "1/4-20 x 24 in threaded rod cut to 10 in",
        "form": "cut_threaded_rod_sensitivity",
        "listing_basis": "ASTM A307 Grade A product lead",
        "selected": False,
        "scope_procurement_gate": True,
        "current_ordinary_store_availability_verified": False,
        "limits": (
            "Not a factory hex bolt and not a selection; current Lowe's/Home Depot "
            "availability, cutting, end finishing, nut engagement, provenance, and "
            "user-approved scope remain gates."
        ),
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


def _scale(vector, factor):
    return tuple(factor * value for value in vector)


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
    return _scale(vector, 1 / magnitude)


def _extent(shape, axis):
    positions = [vertex.Center().dot(cq.Vector(*axis)) for vertex in shape.Vertices()]
    return min(positions), max(positions)


def _member_axes(report, member, bolt_axis):
    try:
        grain = _unit(
            report["member_section_demands"][member]["member"]["axis"],
            member + " grain axis",
        )
    except KeyError as exc:
        raise ValueError(f"{member}: missing retained member axis") from exc
    if abs(_dot(grain, bolt_axis)) > 1e-7:
        raise ValueError(f"{member}: bolt axis is not transverse to grain")
    edge = _unit(_cross(grain, bolt_axis), member + " edge axis")
    return grain, edge


def _load_angle(force, grain):
    magnitude = _norm(force)
    if magnitude <= 1e-12:
        return 0.0
    cosine = min(1.0, abs(_dot(force, grain)) / magnitude)
    return math.degrees(math.acos(cosine))


def _direction_coordinate(shape, point, force, axis, loaded_d, unloaded_d):
    minimum, maximum = _extent(shape, axis)
    coordinate = _dot(point, axis)
    component = _dot(force, axis)
    if abs(component) <= 1e-9:
        return {
            "force_component_n": component,
            "direction": "neutral",
            "applicable": False,
            "loaded_distance_mm": None,
            "unloaded_distance_mm": None,
            "loaded_required_mm": loaded_d,
            "unloaded_required_mm": unloaded_d,
            "maximum_geometry_ratio": 0.0,
            "passes": True,
        }
    if component > 0:
        loaded, unloaded, direction = (
            maximum - coordinate,
            coordinate - minimum,
            "positive",
        )
    else:
        loaded, unloaded, direction = (
            coordinate - minimum,
            maximum - coordinate,
            "negative",
        )
    ratio = max(loaded_d / loaded, unloaded_d / unloaded)
    return {
        "force_component_n": component,
        "direction": direction,
        "applicable": True,
        "loaded_distance_mm": loaded,
        "unloaded_distance_mm": unloaded,
        "loaded_required_mm": loaded_d,
        "unloaded_required_mm": unloaded_d,
        "loaded_margin_mm": loaded - loaded_d,
        "unloaded_margin_mm": unloaded - unloaded_d,
        "maximum_geometry_ratio": ratio,
        "passes": ratio <= 1 + 1e-10,
    }


def _end_edge(shape, point, force, grain, edge):
    end = _direction_coordinate(
        shape, point, force, grain, 7 * SHAFT_DIAMETER_MM, 4 * SHAFT_DIAMETER_MM
    )
    cross_edge = _direction_coordinate(
        shape,
        point,
        force,
        edge,
        4 * SHAFT_DIAMETER_MM,
        1.5 * SHAFT_DIAMETER_MM,
    )
    return {
        "grain_end": end,
        "cross_grain_edge": cross_edge,
        "maximum_geometry_ratio": max(
            end["maximum_geometry_ratio"], cross_edge["maximum_geometry_ratio"]
        ),
        "passes": end["passes"] and cross_edge["passes"],
    }


def _wood_yield(lengths_in, angles):
    angle_factor = 1 + 0.25 * max(angles) / 90
    reduction = (10 * THREAD_ROOT_DIAMETER_IN + 0.5) * angle_factor
    result = wood_wood_single_shear_reference(
        main_bearing_length_in=lengths_in[0],
        side_bearing_length_in=lengths_in[1],
        main_load_to_grain_degrees=angles[0],
        side_load_to_grain_degrees=angles[1],
        main_bolt_axis_parallel_to_grain=False,
        side_bolt_axis_parallel_to_grain=False,
        bolt_full_body_diameter_in=NOMINAL_DIAMETER_IN,
        bolt_thread_root_diameter_in=THREAD_ROOT_DIAMETER_IN,
        main_thread_bearing_length_in=lengths_in[0],
        side_thread_bearing_length_in=lengths_in[1],
        bolt_bending_yield_moment_lb_in=dowel_bending_yield_moment_lb_in(
            bending_yield_strength_psi=CONDITIONAL_BENDING_YIELD_PSI,
            effective_diameter_in=THREAD_ROOT_DIAMETER_IN,
        ),
        bolt_bending_yield_strength_psi=CONDITIONAL_BENDING_YIELD_PSI,
        gap_in=0.0,
        reduction_terms=dict.fromkeys(MODES, reduction),
    )
    return {
        "capacity_n": result["reference_lateral_lbf"] * N_PER_LBF,
        "governing_mode": result["governing_mode"],
        "effective_bearing_diameter_in": result["effective_bearing_diameter_in"],
        "load_to_grain_degrees": list(angles),
        "bearing_psi": [result["main_bearing_psi"], result["side_bearing_psi"]],
        "nds_basis": "2024 NDS Chapter 12 with January 2025 sub-1/4-inch-root erratum",
    }


def _hardware_class(grip_mm):
    if math.isclose(grip_mm, 95.25, abs_tol=1e-6):
        return "five_inch"
    if math.isclose(grip_mm, 177.8, abs_tol=1e-6):
        return "eight_inch"
    if math.isclose(grip_mm, 228.6, abs_tol=1e-6):
        return "outer_ten_inch_sensitivity"
    raise ValueError(f"unsupported PB03 quarter-inch grip: {grip_mm}")


def _authenticate(report_path, report, module, connections):
    if _sha256(report_path) != REPORT_SHA256:
        raise ValueError("PB03 report SHA-256 changed")
    scope = report.get("diagnostic_scope", {})
    if (
        report.get("candidate") != SOURCE_ID
        or scope.get("case") != "a12-forward"
        or report.get("numerically_accepted") is not True
        or report.get("global_equilibrium_passed") is not True
        or report.get("member_equilibrium_passed") is not True
        or report.get("qualified_for_design") is not False
        or report.get("actual_joint_demands_qualified") is not False
        or report.get("drilling_released") is not False
        or report.get("fabrication_released") is not False
    ):
        raise ValueError("PB03 retained developmental report identity changed")
    if (
        len(connections) != 32
        or len(module.pb03_geometries()) != 8
        or len(module.panel_connections()) != 66
        or any(
            not math.isclose(row.diameter, SHAFT_DIAMETER_MM, abs_tol=1e-9)
            for row in connections
        )
    ):
        raise ValueError("active quarter-inch PB03 geometry identity changed")
    return {
        "report_numerically_accepted": True,
        "bolt_count": len(connections),
        "station_count": len(module.pb03_geometries()),
        "fixed_panel_kicker_axes": len(module.panel_connections()),
        "shaft_diameter_mm": SHAFT_DIAMETER_MM,
        "bore_diameter_mm": BORE_DIAMETER_MM,
        "report_force_residual_n": report["force_residual_n"],
        "report_moment_residual_nmm": report["moment_residual_nmm"],
    }


def _group_rows(bolts, parts):
    grouped = {}
    for bolt in bolts:
        for member, direction in bolt["member_directions"].items():
            grouped.setdefault((bolt["station"], bolt["interface"], member), []).append(
                (bolt, direction)
            )
    rows = []
    for (station, interface, member), items in grouped.items():
        if len(items) != 2:
            raise ValueError(f"{station}/{interface}/{member}: expected two-bolt row")
        grain = items[0][1]["grain_axis_xyz"]
        points = [item[0]["point_xyz_mm"] for item in items]
        coordinates = [_dot(point, grain) for point in points]
        pitch_mm = abs(coordinates[1] - coordinates[0])
        individual_parallel = [item[1]["grain_force_n"] for item in items]
        total_parallel = math.fsum(individual_parallel)
        shape = parts[member]
        minimum, maximum = _extent(shape, grain)
        if total_parallel >= 0:
            end_distance_mm = maximum - max(coordinates)
            loaded_end = "positive"
        else:
            end_distance_mm = min(coordinates) - minimum
            loaded_end = "negative"
        axis = items[0][0]["axis_host_to_block_xyz"]
        axis_min, axis_max = _extent(shape, axis)
        thickness_in = (axis_max - axis_min) / MM_PER_IN
        parallel_row_applicable = pitch_mm > 1e-8
        if parallel_row_applicable:
            capacity_n = (
                dfl_parallel_row_tear_out_reference_lbf(
                    thickness_in, 2, end_distance_mm / MM_PER_IN, pitch_mm / MM_PER_IN
                )
                * N_PER_LBF
            )
            ratio = abs(total_parallel) / capacity_n
            sensitivity = "two_bolt_parallel_to_grain_row"
        else:
            individual = []
            for point, demand in zip(points, individual_parallel, strict=True):
                coordinate = _dot(point, grain)
                distance = maximum - coordinate if demand >= 0 else coordinate - minimum
                capacity = (
                    dfl_parallel_row_tear_out_reference_lbf(
                        thickness_in, 1, distance / MM_PER_IN
                    )
                    * N_PER_LBF
                )
                individual.append((capacity, abs(demand) / capacity))
            capacity_n = min(item[0] for item in individual)
            ratio = max(item[1] for item in individual)
            sensitivity = "individual_boundary_rows_pair_is_cross_grain"
        rows.append(
            {
                "station": station,
                "interface": interface,
                "member": member,
                "bolt_names": [item[0]["name"] for item in items],
                "parallel_force_sum_n": total_parallel,
                "loaded_end": loaded_end,
                "loaded_end_distance_mm": end_distance_mm,
                "pitch_mm": pitch_mm,
                "parallel_row_applicable": parallel_row_applicable,
                "sensitivity_basis": sensitivity,
                "conditional_parallel_row_tear_out_n": capacity_n,
                "separate_ratio": ratio,
                "limits": (
                    "Appendix E row tear-out sensitivity only; load sharing, group "
                    "factor, splitting, net section, and full joint action unresolved."
                ),
            }
        )
    return sorted(
        rows,
        key=lambda row: (
            REPLACED_STATIONS.index(row["station"]),
            row["interface"],
            row["member"],
        ),
    )


def screen(report_path=DEFAULT_REPORT):
    """Return separate conditional comparisons for the active quarter-inch layout."""
    report_path = Path(report_path)
    report = json.loads(report_path.read_text())
    module = PB03Native()
    connections = tuple(
        row for row in module.connections() if row.name.startswith("pb03_")
    )
    source = _authenticate(report_path, report, module, connections)
    physical = report.get("physical_connection_forces", {})
    parts = {part.name: part.shape for part in module.uncut_wood_parts()}

    steel_shear_n = CONDITIONAL_SHEAR_STRESS_PSI * TENSILE_STRESS_AREA_IN2 * N_PER_LBF
    steel_tension_n = (
        CONDITIONAL_TENSION_STRESS_PSI * TENSILE_STRESS_AREA_IN2 * N_PER_LBF
    )
    washer_n = (
        dfl_axial_wood_bearing_reference_lbf(
            WASHER_OUTSIDE_DIAMETER_IN,
            BORE_DIAMETER_MM / MM_PER_IN,
            NOMINAL_DIAMETER_IN,
        )
        * N_PER_LBF
    )

    bolts = []
    for connection in connections:
        try:
            force = physical[connection.name]
        except KeyError as exc:
            raise ValueError(
                f"{connection.name}: retained physical force missing"
            ) from exc
        if force.get("station") not in REPLACED_STATIONS:
            raise ValueError(f"{connection.name}: retained station changed")
        axis = _unit(force["axis"], connection.name + " axis")
        host_force = _vector(force["force_on_first_xyz_n"], connection.name + " force")
        axial = max(0.0, _dot(host_force, axis))
        lateral_host = _subtract(host_force, _scale(axis, _dot(host_force, axis)))
        shear = _norm(lateral_host)
        if not math.isclose(shear, force["transverse_shear_n"], abs_tol=1e-6):
            raise ValueError(f"{connection.name}: retained transverse demand changed")
        point = _vector(force["point"], connection.name + " point")

        member_directions = {}
        lengths_in = []
        angles = []
        for index, member in enumerate(connection.members):
            member_force = lateral_host if index == 0 else _scale(lateral_host, -1)
            grain, edge = _member_axes(report, member, axis)
            angle = _load_angle(member_force, grain)
            member_directions[member] = {
                "lateral_force_xyz_n": member_force,
                "grain_axis_xyz": grain,
                "edge_axis_xyz": edge,
                "grain_force_n": _dot(member_force, grain),
                "edge_force_n": _dot(member_force, edge),
                "load_to_grain_degrees": angle,
            }
            minimum, maximum = _extent(parts[member], axis)
            lengths_in.append((maximum - minimum) / MM_PER_IN)
            angles.append(angle)
        if not math.isclose(
            math.fsum(lengths_in) * MM_PER_IN, connection.grip, abs_tol=1e-5
        ):
            raise ValueError(f"{connection.name}: active bearing lengths changed")

        wood = _wood_yield(tuple(lengths_in), tuple(angles))
        geometry_members = {
            member: _end_edge(
                parts[member],
                point,
                direction["lateral_force_xyz_n"],
                direction["grain_axis_xyz"],
                direction["edge_axis_xyz"],
            )
            for member, direction in member_directions.items()
        }
        geometry_ratio = max(
            row["maximum_geometry_ratio"] for row in geometry_members.values()
        )
        hardware_class = _hardware_class(connection.grip)
        bolts.append(
            {
                "station": force["station"],
                "interface": force["interface"],
                "name": connection.name,
                "members": list(connection.members),
                "point_xyz_mm": point,
                "axis_host_to_block_xyz": axis,
                "transverse_shear_n": shear,
                "axial_tension_n": axial,
                "member_directions": member_directions,
                "hardware_length_class": hardware_class,
                "hardware_selected": HARDWARE_LEADS[hardware_class]["selected"],
                "separate_checks": {
                    "wood_yield_bearing": {
                        **wood,
                        "demand_n": shear,
                        "ratio": shear / wood["capacity_n"],
                    },
                    "bolt_shear": {
                        "demand_n": shear,
                        "capacity_n": steel_shear_n,
                        "ratio": shear / steel_shear_n,
                        "basis": "A307 conditional ASD threaded-area comparator",
                    },
                    "bolt_tension": {
                        "demand_n": axial,
                        "capacity_n": steel_tension_n,
                        "ratio": axial / steel_tension_n,
                        "basis": "A307 conditional ASD tensile-stress-area comparator",
                    },
                    "washer_wood_bearing": {
                        "demand_n": axial,
                        "capacity_n": washer_n,
                        "ratio": axial / washer_n,
                        "basis": (
                            "Ideal full-contact DF-L Fc-perp annulus for 5/8-inch "
                            "OD sensitivity; actual washer and metal bending unqualified"
                        ),
                    },
                    "end_edge_direction": {
                        "members": geometry_members,
                        "maximum_geometry_ratio": geometry_ratio,
                        "passes": all(
                            row["passes"] for row in geometry_members.values()
                        ),
                    },
                },
            }
        )

    bolts.sort(key=lambda row: (REPLACED_STATIONS.index(row["station"]), row["name"]))
    group_rows = _group_rows(bolts, parts)
    maxima = {
        "wood_yield_bearing": max(
            row["separate_checks"]["wood_yield_bearing"]["ratio"] for row in bolts
        ),
        "bolt_shear": max(
            row["separate_checks"]["bolt_shear"]["ratio"] for row in bolts
        ),
        "bolt_tension": max(
            row["separate_checks"]["bolt_tension"]["ratio"] for row in bolts
        ),
        "washer_wood_bearing": max(
            row["separate_checks"]["washer_wood_bearing"]["ratio"] for row in bolts
        ),
        "end_edge_geometry": max(
            row["separate_checks"]["end_edge_direction"]["maximum_geometry_ratio"]
            for row in bolts
        ),
        "parallel_row_tear_out_sensitivity": max(
            row["separate_ratio"] for row in group_rows
        ),
    }
    gates = []
    if maxima["end_edge_geometry"] > 1 + 1e-10:
        gates.append(
            "A12-forward assigns at least one deficient loaded-edge/end direction."
        )
    gates.append(
        "Outer 9-inch grips have no verified ordinary Lowe's/Home Depot factory "
        "hex bolt; the cut threaded-rod item is sensitivity-only and unavailable "
        "for selection."
    )
    gates.append(
        "One accepted case does not establish a six-case envelope, group action, "
        "or adjusted design values."
    )
    component_over = any(
        maxima[name] > 1
        for name in (
            "wood_yield_bearing",
            "bolt_shear",
            "bolt_tension",
            "washer_wood_bearing",
            "parallel_row_tear_out_sensitivity",
        )
    )
    verdict = "REJECT" if component_over else "REVISE" if gates else "ADVANCE"
    return {
        "schema": "simple_pb03_quarter_inch_resistance/v1",
        "case": "a12-forward",
        "candidate": SOURCE_ID,
        "report_sha256": REPORT_SHA256,
        "source": source,
        "conditional_inputs": {
            "nominal_diameter_in": NOMINAL_DIAMETER_IN,
            "thread_root_diameter_in": THREAD_ROOT_DIAMETER_IN,
            "tensile_stress_area_in2": TENSILE_STRESS_AREA_IN2,
            "astm_a307_grade_a_minimum_tensile_psi": A307_GRADE_A_MINIMUM_TENSILE_PSI,
            "conditional_bending_yield_psi": CONDITIONAL_BENDING_YIELD_PSI,
            "conditional_tension_stress_psi": CONDITIONAL_TENSION_STRESS_PSI,
            "conditional_shear_stress_psi": CONDITIONAL_SHEAR_STRESS_PSI,
            "washer_outside_diameter_in": WASHER_OUTSIDE_DIAMETER_IN,
            "limits": (
                "A307 material inputs and published thread geometry are conditional; "
                "delivered dimensions, bending yield, washers, nuts, and adjustments remain open."
            ),
        },
        "hardware_leads": HARDWARE_LEADS,
        "bolts": bolts,
        "group_effects": {
            "rows": group_rows,
            "load_sharing_qualified": False,
            "group_factor_qualified": False,
            "capacity_aggregation_prohibited": True,
        },
        "summary": {
            "maximum_transverse_shear_n": max(
                row["transverse_shear_n"] for row in bolts
            ),
            "maximum_axial_tension_n": max(row["axial_tension_n"] for row in bolts),
            "maximum_separate_ratios": maxima,
            "development_verdict": verdict,
            "verdict_scope": "development_only",
            "gates": gates,
            "basis": (
                "One authenticated accepted A12-forward case; component ratios, "
                "geometry, and group sensitivity remain separate."
            ),
        },
        "capacity_aggregation": "prohibited_serial_components_not_combined",
        "qualified_for_design": False,
        "drilling_released": False,
        "fabrication_released": False,
        "structural_released": False,
    }


if __name__ == "__main__":
    print(json.dumps(screen(), indent=2, sort_keys=True))
