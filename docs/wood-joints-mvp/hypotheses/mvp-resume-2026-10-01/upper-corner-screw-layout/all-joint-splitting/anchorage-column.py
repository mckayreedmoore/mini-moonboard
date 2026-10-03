"""Build exact static annular-column witnesses for the proposed knee v ties.

Parent owns execution. This postprocessor reads frozen results, reconstructs the
saved washer-contact profile without rerunning its solve, and checks swept
geometry plus force/moment balance. It does not qualify a complete joint.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
import sys
from itertools import pairwise
from pathlib import Path
from types import SimpleNamespace

HERE = Path(__file__).resolve().parent
UPPER = HERE.parent
ROOT = next(path for path in HERE.parents if (path / "current-candidate.json").is_file())
OUTPUT_ROOT = HERE / "rawlocal/anchorage-column"

REPLAY = UPPER / "rawlocal/knee-bridge-joint-replay/attempt01"
NORMAL = UPPER / "rawlocal/knee-spine-reinforcement/attempt01"
WASHER = UPPER / "rawlocal/knee-bridge-washer/attempt02"
EDGE = UPPER / "upper-right-washer-edge.py"

REPLAY_CHECKS_SHA256 = "71980f983dd3466d02eb6c5f838186de4b77dc2ebe04653f66cf3f3598fbe891"
REPLAY_RECEIPT_SHA256 = "10503afef20c8fc69c0f5b4877f8deb2794646c258b05ca63616611443c6c22b"
NORMAL_CHECKS_SHA256 = "c9360e7ca4ab167a5cbc505373b2bd1342aa6a830f72a26113da9f7c4a8ad778"
NORMAL_RECEIPT_SHA256 = "991f6742f6aae386552338b1fea79f02766bd0def09bfa8fabea27560ba13819"
WASHER_CHECKS_SHA256 = "d3ad497f8990bca5f18d691d77cd90646b3d40a09d02331c6adf36aa900a2a9d"
WASHER_RECEIPT_SHA256 = "041067657335395f4b1723a237e11574a0ed0b3efcba4e95f32e25db77d3630f"

DIRECT_PINS = {
    UPPER / "knee-bridge-joint-replay.py": "5f0fae2433ee062144095a06853f61bfa5b4d9ba4ef9560588ce6d3e84dade85",
    UPPER / "knee-bridge-joint-replay.md": "473b8a0b8e2a339432134044633148c0b537f98daa1ccc010011ed65737cea57",
    REPLAY / "checks.json": REPLAY_CHECKS_SHA256,
    REPLAY / "receipt.json": REPLAY_RECEIPT_SHA256,
    UPPER / "knee-spine-reinforcement.py": "2ecd3e799dc9929b2524b3fd17efd853ea2a0c0e57dcd3da5d7506267d7c0741",
    UPPER / "knee-spine-reinforcement.md": "81ee2774b6aa87c0e8c6296889a96bc2fedaf58292f5673631729e20f0555f74",
    NORMAL / "checks.json": NORMAL_CHECKS_SHA256,
    NORMAL / "receipt.json": NORMAL_RECEIPT_SHA256,
    UPPER / "knee-bridge-washer.py": "1cf5476e3787fcf67668cf79a5214526f340f8b2cb27fcc15c77f103b9b4a737",
    UPPER / "knee-bridge-washer.md": "8a27a6e229c6be0854fd4bb4b6dc7a6dc39b66cefe8cb137e354451bf68c5162",
    WASHER / "checks.json": WASHER_CHECKS_SHA256,
    WASHER / "receipt.json": WASHER_RECEIPT_SHA256,
    UPPER / "upper-right-washer-edge.py": "ffe3db3e8c707851d44f0c60c43e6e6ef4aa4845f753dc6880c64186e3c75e61",
}

BODY_IDS = ("knee_outer_left_spine", "knee_outer_right_spine")
CASE_IDS = ("a12-rear", "a12-forward", "a12-left", "k12-right", "k12-rear", "a1-rear")
STOCK_MM = {"g": (0.0, 276.3), "u": (-19.05, 19.05), "v": (-69.85, 69.85)}
WASHER_OD_MM, WASHER_ID_MM, WASHER_THICKNESS_MM = 25.4, 8.3058, 2.5
BORE_RADIUS_MM = 3.75
FC_PERP_MPA = 4.309223308230226
MARGIN = 1.25
FORCE_TOLERANCE_N, MOMENT_TOLERANCE_NMM = 0.001, 0.02


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def sha(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def add_pin(pins: dict[Path, str], path: Path, digest: str) -> None:
    path = Path(path).resolve()
    require(path not in pins or pins[path] == digest, f"conflicting pin: {path}")
    pins[path] = digest


def source_path(name: str) -> Path:
    path = Path(name)
    return path if path.is_absolute() else ROOT / path


def authenticate_inputs() -> tuple[dict[Path, str], dict[str, dict]]:
    pins: dict[Path, str] = {}
    documents: dict[str, dict] = {}
    for path, digest in DIRECT_PINS.items():
        add_pin(pins, path, digest)

    for label, folder, expected_schema, expected_checks in (
        ("replay", REPLAY, "knee-bridge-joint-replay-receipt/v1", REPLAY_CHECKS_SHA256),
        ("normal", NORMAL, "knee-spine-reinforcement-parent-receipt/v1", NORMAL_CHECKS_SHA256),
        ("washer", WASHER, "knee-bridge-washer-parent-receipt/v1", WASHER_CHECKS_SHA256),
    ):
        checks_path, receipt_path = folder / "checks.json", folder / "receipt.json"
        checks, receipt = json.loads(checks_path.read_text()), json.loads(receipt_path.read_text())
        require(receipt["schema"] == expected_schema, f"{label} receipt schema differs")
        require(receipt["output_sha256"].get("checks.json") == expected_checks,
                f"{label} receipt does not bind checks")
        require(checks.get("source_sha256") == receipt.get("source_sha256"),
                f"{label} checks and receipt source maps differ")
        if "sources_authenticated_before_and_after" in receipt:
            require(receipt["sources_authenticated_before_and_after"],
                    f"{label} source authentication was incomplete")
        for name, digest in receipt["source_sha256"].items():
            add_pin(pins, source_path(name), digest)
        for name, digest in receipt["output_sha256"].items():
            add_pin(pins, folder / name, digest)
        documents[label] = checks

    for path, digest in pins.items():
        require(path.is_file() and sha(path) == digest, f"changed or missing frozen input: {path}")
    return pins, documents


def import_helper(path: Path, name: str):
    sys.dont_write_bytecode = True
    spec = importlib.util.spec_from_file_location(name, path)
    require(spec is not None and spec.loader is not None, f"helper unavailable: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def annular_area_mm2(inner_radius_mm: float, outer_radius_mm: float) -> float:
    require(0 < inner_radius_mm < outer_radius_mm, "invalid annular radii")
    return math.pi * (outer_radius_mm**2 - inner_radius_mm**2)


def uniform_column_coupon() -> dict:
    """Analytic known answer for constant annular pressure and two end faces."""
    inner, outer, tension = WASHER_ID_MM / 2, WASHER_OD_MM / 2, 100.0
    area = annular_area_mm2(inner, outer)
    pressure = tension / area  # 1 MPa = 1 N/mm^2.
    recovered_force = pressure * area
    require(abs(area - 452.52575506508134) <= 1e-10, "annulus-area coupon differs")
    require(abs(recovered_force - tension) <= 1e-12, "uniform column force coupon differs")
    return {
        "name": "uniform_annulus_T100_M0",
        "area_mm2": area,
        "tension_n": tension,
        "pressure_mpa": pressure,
        "wrench_order": "[N_v,V_g,V_u,M_v,M_g,M_u] with positive N_v along +v",
        "wrench_reference_origin_local_gu_mm": [0.0, 0.0],
        "lower_face_inward_wrench_n_nmm": [tension, 0.0, 0.0, 0.0, 0.0, 0.0],
        "upper_face_inward_wrench_n_nmm": [-tension, 0.0, 0.0, 0.0, 0.0, 0.0],
        "end_pair_net_wrench_n_nmm": [0.0] * 6,
        "section_stress_resultant_n": [0.0, 0.0, -tension],
        "side_traction": "zero: annular side normals have no v component",
        "equilibrium": "div(sigma)=0; end tractions reproduce the two uniform washer pressures exactly",
    }


def local_point(point_xyz, origin_xyz, frame_rows):
    delta = [point_xyz[j] - origin_xyz[j] for j in range(3)]
    return tuple(sum(row[j] * delta[j] for j in range(3)) for row in frame_rows)


def local_direction(direction_xyz, frame_rows):
    return tuple(sum(row[j] * direction_xyz[j] for j in range(3)) for row in frame_rows)


def bore_segment_local(bore: dict, geometry: dict, washer_lands=()) -> dict:
    global_keys = {"axis_origin_global_xyz_mm", "axis_unit_global_xyz",
                   "saved_axis_parameter_interval_mm"}
    if global_keys <= bore.keys():
        origin = bore["axis_origin_global_xyz_mm"]
        axis = bore["axis_unit_global_xyz"]
        low, high = bore["saved_axis_parameter_interval_mm"]
        start = geometry["start_xyz_mm"]
        frame = geometry["grain_frame_rows_xyz"]
        endpoints = [
            local_point([origin[j] + t * axis[j] for j in range(3)], start, frame)
            for t in (low, high)
        ]
        direction = local_direction(axis, frame)
    else:
        require(not global_keys.intersection(bore), "incomplete global bore schema")
        require("proposed_v_bridge" in bore["axis_id"]
                and bore["removed_interval_axis"] == 1,
                "unrecognized local bore schema")
        lands = [land for land in washer_lands if land["axis_id"] == bore["axis_id"]]
        require(len(lands) == 2 and {land["end_v_sign"] for land in lands} == {-1, 1},
                "local bore lacks both saved washer-end lands")
        endpoints = [tuple(land["seat_center_local_guv_mm"]) for land in lands]
        for land, endpoint in zip(lands, endpoints, strict=True):
            expected = (bore["station_mm"], bore["transverse_center_mm"],
                        land["end_v_sign"] * geometry["width_depth_mm"][1] / 2)
            global_local = local_point(land["seat_center_xyz_mm"],
                                       geometry["start_xyz_mm"],
                                       geometry["grain_frame_rows_xyz"])
            require(len(endpoint) == 3
                    and all(abs(actual - target) < 1e-8
                            for actual, target in zip(endpoint, expected, strict=True))
                    and all(abs(actual - target) < 1e-8
                            for actual, target in zip(endpoint, global_local, strict=True)),
                    "saved local/global washer lands disagree with proposed bore")
        direction = (0.0, 0.0, 1.0)
    varying = [i for i, value in enumerate(direction) if abs(value) > 1e-8]
    require(len(varying) == 1 and abs(abs(direction[varying[0]]) - 1.0) < 1e-8,
            "frozen bore axis is not aligned with local g/u/v")
    intervals = [tuple(sorted((endpoints[0][i], endpoints[1][i]))) for i in range(3)]
    return {"intervals_local_guv_mm": intervals, "axis_index": varying[0],
            "radius_mm": bore["radius_mm"], "axis_id": bore["axis_id"]}


def segment_distance_mm(first: dict, second: dict) -> float:
    """Exact distance for axis-aligned finite segments used by this frozen layout."""
    distance_squared = 0.0
    for (a0, a1), (b0, b1) in zip(
        first["intervals_local_guv_mm"], second["intervals_local_guv_mm"], strict=True
    ):
        gap = max(0.0, b0 - a1, a0 - b1)
        distance_squared += gap**2
    return math.sqrt(distance_squared)


def verify_geometry(normal_checks: dict) -> dict:
    proposals = normal_checks["geometry_proposals"]
    require(set(proposals) == set(BODY_IDS), "spine proposal census differs")
    inner, outer = WASHER_ID_MM / 2, WASHER_OD_MM / 2
    area = annular_area_mm2(inner, outer)
    bore_gap = inner - BORE_RADIUS_MM
    require(bore_gap > 0, "proposed through-bore reaches annular column")
    body_records = []
    for body in BODY_IDS:
        record = proposals[body]
        geometry = record["hypothetical_geometry"]
        length = geometry["grain_length_mm"]
        width, depth = geometry["width_depth_mm"]
        require(all(abs(actual - expected) < 1e-8
                    for actual, expected in zip((length, width, depth),
                                                (276.3, 38.1, 139.7), strict=True)),
                "spine stock differs")
        require(geometry["grain_frame_rows_xyz"] == [[0.0, 0.0, 1.0], [1.0, 0.0, 0.0],
                                                       [0.0, 1.0, 0.0]],
                "spine local frame differs")
        proposed = [bore for bore in geometry["bores"] if "proposed_v_bridge" in bore["axis_id"]]
        originals = [bore for bore in geometry["bores"] if "proposed_v_bridge" not in bore["axis_id"]]
        require(len(proposed) == 2 and len(originals) == 4, "spine bore census differs")
        originals.sort(key=lambda bore: bore["station_mm"])
        expected_old = (
            (31.75, -25.39999999999),
            (73.8, -25.39999999999),
            (191.61555301851, 5.9719133485),
            (226.08755295886, 34.89735578436),
        )
        for bore, (expected_g, expected_v) in zip(originals, expected_old, strict=True):
            require(abs(bore["station_mm"] - expected_g) < 1e-8
                    and abs(bore["transverse_center_mm"] - expected_v) < 1e-8
                    and bore["radius_mm"] == BORE_RADIUS_MM
                    and bore["removed_interval_axis"] == 2,
                    "original u-bore geometry differs")
        clearances = []
        face_margins = []
        for index, (axis, expected_g) in enumerate(zip(proposed, (100.0, 250.0), strict=True), 1):
            require(axis["station_mm"] == expected_g and axis["transverse_center_mm"] == 0.0
                    and axis["radius_mm"] == BORE_RADIUS_MM
                    and axis["removed_interval_axis"] == 1,
                    "proposed v-bore geometry differs")
            g = axis["station_mm"]
            axis_segment = bore_segment_local(axis, geometry, record["washer_lands"])
            intervals = axis_segment["intervals_local_guv_mm"]
            require(axis_segment["axis_index"] == 2
                    and axis_segment["radius_mm"] == BORE_RADIUS_MM
                    and abs(intervals[0][0] - g) < 1e-8
                    and abs(intervals[0][1] - g) < 1e-8
                    and abs(intervals[1][0]) < 1e-8
                    and abs(intervals[1][1]) < 1e-8
                    and abs(intervals[2][0] - STOCK_MM["v"][0]) < 1e-8
                    and abs(intervals[2][1] - STOCK_MM["v"][1]) < 1e-8,
                    "proposed through-bore finite axis interval differs")
            side_margin_g = min(g - outer, length - g - outer)
            side_margin_u = width / 2 - outer
            require(min(side_margin_g, side_margin_u) > 0,
                    "annular column intersects a non-end stock face")
            face_margins.append({"axis_id": axis["axis_id"],
                                 "g_face_margin_mm": side_margin_g,
                                 "u_face_margin_mm": side_margin_u,
                                 "minimum_lateral_face_margin_mm": min(side_margin_g, side_margin_u),
                                 "v_end_faces": "column terminates exactly at both supported washer lands"})
            annular_segment = {
                "intervals_local_guv_mm": [(g, g), (0.0, 0.0), STOCK_MM["v"]],
                "axis_index": 2,
                "radius_mm": outer,
                "axis_id": axis["axis_id"],
            }
            axis_clearance_rows = []
            for bore in originals:
                bore_segment = bore_segment_local(bore, geometry)
                require(bore_segment["axis_index"] == 1, "original void is not a u-axis bore")
                intervals = bore_segment["intervals_local_guv_mm"]
                require(abs(intervals[0][0] - bore["station_mm"]) < 1e-8
                        and abs(intervals[0][1] - bore["station_mm"]) < 1e-8
                        and abs(intervals[1][0] + width / 2) < 1e-8
                        and abs(intervals[1][1] - width / 2) < 1e-8
                        and abs(intervals[2][0] - bore["transverse_center_mm"]) < 1e-8
                        and abs(intervals[2][1] - bore["transverse_center_mm"]) < 1e-8,
                        "original u-bore finite axis interval differs")
                centerline_gap = segment_distance_mm(annular_segment, bore_segment)
                surface_gap = centerline_gap - outer - bore["radius_mm"]
                require(surface_gap > 0, "annular column intersects an original bore")
                axis_clearance_rows.append({"void_axis_id": bore["axis_id"],
                                            "centerline_distance_mm": centerline_gap,
                                            "annular_column_surface_gap_mm": surface_gap})
            clearances.extend({"column_axis_id": axis["axis_id"], **row}
                              for row in axis_clearance_rows)
            own_bore_gap = inner - axis["radius_mm"]
            require(own_bore_gap > 0, "own v bore enters annular column")
            other = proposed[1 if index == 1 else 0]
            neighbor_bore_gap = abs(g - other["station_mm"]) - outer - other["radius_mm"]
            column_gap = abs(g - other["station_mm"]) - 2 * outer
            require(neighbor_bore_gap > 0 and column_gap > 0,
                    "proposed v-bore columns overlap")
        require(len(record["washer_lands"]) == 4, "washer-end land count differs")
        expected_centers = {
            axis["axis_id"]: (axis["station_mm"], axis["transverse_center_mm"])
            for axis in proposed
        }
        for axis_id, expected_center in expected_centers.items():
            matching_lands = [land for land in record["washer_lands"]
                              if land["axis_id"] == axis_id]
            require(len(matching_lands) == 2
                    and {land["end_v_sign"] for land in matching_lands} == {-1, 1}
                    and all(abs(land["seat_center_local_guv_mm"][0] - expected_center[0]) < 1e-8
                            and abs(land["seat_center_local_guv_mm"][1] - expected_center[1]) < 1e-8
                            for land in matching_lands),
                    "washer lands do not match both proposed bore centers and signs")
        require(all(abs(land["supported_annulus_area_mm2"] - area) < 1e-9
                    and land["washer_outer_edge_margin_mm"] > 0
                    and land["original_bore_gap_from_seat_plane_mm"] > 0
                    and land["other_new_bore_gap_from_outer_disk_mm"] > 0
                    and abs(land["seat_center_local_guv_mm"][2]
                            - land["end_v_sign"] * depth / 2) < 1e-8
                    for land in record["washer_lands"]),
                "frozen washer land is unsupported")
        body_records.append({
            "body": body,
            "stock_guv_mm": STOCK_MM,
            "annulus_inner_radius_mm": inner,
            "annulus_outer_radius_mm": outer,
            "annulus_area_mm2": area,
            "own_bore_to_annulus_radial_gap_mm": bore_gap,
            "lateral_face_margins": face_margins,
            "original_perpendicular_bore_clearances": [
                row for row in clearances if row["column_axis_id"].startswith(body + "/")
            ],
            "neighbor_v_hole_to_other_column_outer_gap_mm": (
                abs(proposed[1]["station_mm"] - proposed[0]["station_mm"])
                - outer - BORE_RADIUS_MM
            ),
            "annular_column_to_annular_column_gap_mm": (
                abs(proposed[1]["station_mm"] - proposed[0]["station_mm"]) - 2 * outer
            ),
            "washer_end_land_count": 4,
            "all_voids_and_lateral_faces_clear": True,
        })
    return {
        "certificate_method": "exact finite axis-segment distances plus annular containment in the rectangular prism",
        "body_count": len(body_records),
        "annular_columns": body_records,
        "original_void_clearance_count": len(clearances),
        "minimum_original_void_surface_gap_mm": min(row["annular_column_surface_gap_mm"] for row in clearances),
        "all_new_and_original_voids_clear": True,
    }


def exact_polynomial_extrema(np, coefficients):
    derivative = np.arange(1, len(coefficients), dtype=float) * coefficients[1:]
    candidates = [0.0, 1.0]
    if np.any(np.abs(derivative) > 0):
        for root in np.polynomial.polynomial.polyroots(derivative):
            if abs(float(root.imag)) <= 1e-9 and 0.0 < float(root.real) < 1.0:
                candidates.append(float(root.real))
    values = [(float(x), float(np.polynomial.polynomial.polyval(x, coefficients)))
              for x in candidates]
    return min(values, key=lambda item: item[1]), max(values, key=lambda item: item[1])


def recovered_washer_profile(washer_checks: dict) -> dict:
    """Recover exact radial pressure polynomial of saved M=0 washer model state."""
    import numpy as np

    state = washer_checks["state"]
    model_record = washer_checks["model"]
    require(washer_checks["status"] == "FINITE_KNEE_BRIDGE_WASHER_HYPOTHESIS",
            "saved washer result is incomplete")
    require(state["axis_id"] == "knee_outer_right_spine/proposed_v_bridge_2"
            and state["case_id"] == "k12-right"
            and state["M_magnitude_nmm"] == 0.0
            and state["end_role"] == "both washer ends; one positive-homogeneous envelope"
            and state["source_proposal_checks_sha256"] == NORMAL_CHECKS_SHA256,
            "washer pressure profile is not the concentric M=0 peak envelope")
    require(washer_checks["proposal_adopted"] is False
            and washer_checks["complete_joint_acceptance"] is False
            and washer_checks["physical_release"] is False,
            "washer result claim boundary differs")
    edge = import_helper(EDGE, "anchorage_column_washer_edge")
    family = model_record["family"]
    module = SimpleNamespace(
        FAMILIES={"rail": family},
        ESTEEL=model_record["E_mpa_hypothesis"],
        NU=model_record["nu_hypothesis"],
        KWOOD=model_record["Kwood_mpa_per_mm_hypothesis"],
        KHEAD=model_record["Khead_mpa_per_mm_hypothesis"],
        FY_HYPOTHESIS=model_record["Fy_mpa_hypothesis"],
    )
    model = edge.make_model(module, "fine")
    pose = np.asarray(state["scaled_variables_mm"], dtype=float)
    require(pose.shape == (model["width"],) and np.isfinite(pose).all(),
            "saved washer state vector differs from fine model")
    higher_mode_ids = model["u_indices"][1:]
    higher_mode_ids = higher_mode_ids[higher_mode_ids >= 0]
    nonaxisymmetric_max_mm = float(np.max(np.abs(pose[higher_mode_ids]))) if higher_mode_ids.size else 0.0
    require(nonaxisymmetric_max_mm <= 1e-10, "saved M=0 contact field is not axisymmetric")

    fractions = np.linspace(0.0, 1.0, 5)
    pieces = []
    gauss, weights = np.polynomial.legendre.leggauss(6)
    total_force = 0.0
    global_min = math.inf
    global_max = -math.inf
    for element, (left, right) in enumerate(pairwise(model["edges"])):
        radii = left + (right - left) * fractions
        displacement, *_ = edge.field_values(model, pose, element, radii, np.array([0.0]))
        coefficients = np.polynomial.polynomial.polyfit(fractions, displacement[:, 0], 4)
        reconstructed = np.polynomial.polynomial.polyval(fractions, coefficients)
        residual = float(np.max(np.abs(reconstructed - displacement[:, 0])))
        require(residual <= 1e-10, "saved radial deflection is not quartic in an element")
        low, _high = exact_polynomial_extrema(np, coefficients)
        require(low[1] > 0.0, "saved washer contact profile leaves annulus partly unloaded")
        global_min = min(global_min, low[1])
        local_pressure_coefficients = coefficients * model["Kwood"]
        _, pressure_high = exact_polynomial_extrema(np, local_pressure_coefficients)
        global_max = max(global_max, pressure_high[1])
        s = (gauss + 1) / 2
        r = left + (right - left) * s
        pressure = np.polynomial.polynomial.polyval(s, local_pressure_coefficients)
        total_force += math.pi * (right - left) * float(np.dot(weights * r, pressure))
        pieces.append({
            "element": element,
            "radial_interval_mm": [float(left), float(right)],
            "w_mm_polynomial_in_unit_s_ascending": coefficients.tolist(),
            "pressure_mpa_polynomial_in_unit_s_ascending": local_pressure_coefficients.tolist(),
            "unit_coordinate": "s=(r-left)/(right-left)",
            "minimum_witness_s_mm": [low[0], low[1]],
            "maximum_pressure_witness_s_mpa": [pressure_high[0], pressure_high[1]],
            "quartic_reconstruction_residual_mm": residual,
        })
    expected_tension = float(state["T_n"])
    require(abs(total_force - expected_tension) <= FORCE_TOLERANCE_N,
            "recovered pressure polynomial does not integrate to peak washer T")
    require(abs(global_max - state["contact_balances"][0]["pressure_peak_mpa"]) <= 0.02,
            "recovered continuous pressure differs materially from saved contact peak")
    wood_balance = state["contact_balances"][0]
    require(wood_balance["contact"] == "wood"
            and abs(wood_balance["force_residual_n"]) <= FORCE_TOLERANCE_N
            and max(abs(value) for value in wood_balance["first_moment_residuals_nmm"])
            <= MOMENT_TOLERANCE_NMM
            and abs(wood_balance["active_area_mm2"] - wood_balance["full_area_mm2"]) <= 1e-9,
            "saved washer contact does not support full-annulus force and M=0 map")
    require(global_max <= FC_PERP_MPA,
            "recovered finite-model pressure maximum exceeds Fc-perp reference")
    return {
        "profile_id": "knee-bridge-washer/attempt02/peak-M0-wood-contact",
        "source_peak_tension_n": expected_tension,
        "washer_end_moment_nmm": 0.0,
        "inner_radius_mm": family["inner_radius_mm"],
        "outer_radius_mm": family["outer_radius_mm"],
        "area_mm2": annular_area_mm2(family["inner_radius_mm"], family["outer_radius_mm"]),
        "radial_pressure_profile_mpa": pieces,
        "pressure_independent_of_angle": True,
        "same_profile_on_both_ends": True,
        "full_contact_annulus": True,
        "profile_integral_force_n": total_force,
        "profile_first_moments_about_bolt_axis_nmm": [0.0, 0.0],
        "continuous_finite_model_pressure_max_mpa": global_max,
        "continuous_finite_model_pressure_min_witness_mpa": model["Kwood"] * global_min,
        "fc_perp_reference_mpa": FC_PERP_MPA,
        "peak_pressure_over_fc_perp": global_max / FC_PERP_MPA,
        "maximum_method": "exact stationary-point census of each recovered quartic contact polynomial; exact only for the saved finite washer model",
        "nonaxisymmetric_displacement_coefficient_max_mm": nonaxisymmetric_max_mm,
        "source_contact_pressure_peak_mpa": state["contact_balances"][0]["pressure_peak_mpa"],
        "profile_scope": "saved M=0, zero-gap, no-preload elastic washer/contact model; not measured contact or actual washer/wood capacity",
    }


def fresh_tie_states(replay_checks: dict, normal_checks: dict, profile: dict) -> list[dict]:
    require(replay_checks["schema"] == "knee-bridge-joint-replay/v1"
            and replay_checks["status"] == "FINITE_FRESH_KNEE_STATIC_REPLAY_COMPLETE",
            "fresh knee replay is incomplete")
    require(normal_checks["schema"] == "knee-spine-v-bridge-static-proposal/v1"
            and normal_checks["status"] == "FINITE_PROPOSAL_STATIC_ARITHMETIC_COMPLETE",
            "original normal allocation is incomplete")
    require(abs(normal_checks["existing_Fc_perpendicular_reference_mpa"] - FC_PERP_MPA) < 1e-12
            and abs(replay_checks["existing_Fc_perpendicular_reference_mpa"] - FC_PERP_MPA) < 1e-12,
            "perpendicular-compression reference differs")
    require(profile["source_peak_tension_n"] == 1060.6566047532085,
            "saved washer profile peak tension differs")
    require(len(replay_checks["states"]) == 12 and replay_checks["case_ids"] == list(CASE_IDS),
            "fresh replay does not cover six cases and two spines")
    peak_profile_tension = profile["source_peak_tension_n"]
    original_allocations = []
    for state in normal_checks["states"]:
        for candidate in state["candidates"]:
            if candidate["uniform_case_force_margin"] == MARGIN:
                for index, tension in enumerate(candidate["constant_axial_ties_n"], 1):
                    original_allocations.append((tension, state["block"], state["case_id"], index))
    original_peak = max(original_allocations)
    require(abs(original_peak[0] - peak_profile_tension) <= 1e-9
            and original_peak[1:] == ("knee_outer_right_spine", "k12-right", 2),
            "saved washer model does not bind the original 1.25 allocation peak")
    states = []
    for state in replay_checks["states"]:
        require(state["block"] in BODY_IDS and state["case_id"] in CASE_IDS
                and state["uniform_case_force_margin"] == MARGIN,
                "fresh replay state/margin differs")
        ties = state["constant_axial_ties_n"]
        require(len(ties) == 2 and all(math.isfinite(t) and t >= 0 for t in ties),
                "fresh replay axial tie vector is invalid")
        for index, tension in enumerate(ties, 1):
            scale = tension / peak_profile_tension
            integrated_tension = scale * profile["profile_integral_force_n"]
            require(abs(integrated_tension - tension) <= FORCE_TOLERANCE_N,
                    "scaled washer profile does not integrate to the allocated tie tension")
            pressure_peak = scale * profile["continuous_finite_model_pressure_max_mpa"]
            center_g = (100.0, 250.0)[index - 1]
            center_u = 0.0
            require(pressure_peak <= FC_PERP_MPA,
                    "scaled finite-model annular pressure exceeds Fc-perp reference")
            states.append({
                "body": state["block"],
                "case_id": state["case_id"],
                "proposal_axis_id": f"{state['block']}/proposed_v_bridge_{index}",
                "bolt_index": index,
                "load_induced_tension_in_frozen_1_25_allocation_n": tension,
                "scaled_pressure_profile_integral_n": integrated_tension,
                "additional_preload_n": 0.0,
                "washer_profile_scale_from_frozen_peak": scale,
                "annulus_mean_pressure_mpa": tension / profile["area_mm2"],
                "finite_model_pointwise_pressure_max_mpa": pressure_peak,
                "pressure_peak_over_fc_perp": pressure_peak / FC_PERP_MPA,
                "column_center_local_gu_mm": [center_g, center_u],
                "signed_section_wrench_reference_origin_local_gu_mm": [0.0, 0.0],
                "signed_section_wrench_contribution_order_N_Vg_Vu_Mv_Mg_Mu_n_nmm": [
                    -tension, 0.0, 0.0, 0.0, -center_u * tension, center_g * tension
                ],
                "end_profile_pair": "same radial M=0 profile on both faces; one tension counted once",
                "normal_column_screen_satisfied_under_profile": pressure_peak <= FC_PERP_MPA,
            })
    require(len(states) == 24, "fresh proposed bolt tension census differs")
    maximum = max(states, key=lambda item: item["load_induced_tension_in_frozen_1_25_allocation_n"])
    require(abs(maximum["load_induced_tension_in_frozen_1_25_allocation_n"]
                - 1038.9839065627812) <= 1e-8
            and maximum["case_id"] == "a12-forward"
            and maximum["body"] == "knee_outer_left_spine"
            and maximum["bolt_index"] == 2,
            "fresh replay governing tie differs")
    require(maximum["load_induced_tension_in_frozen_1_25_allocation_n"] <= peak_profile_tension,
            "saved washer pressure profile does not envelope fresh replay tie")
    return states


def build(output: Path) -> dict:
    output = Path(output).resolve()
    require(output.parent == OUTPUT_ROOT.resolve() and not output.exists(),
            f"output must be a fresh child of {OUTPUT_ROOT}: {output}")
    pins, docs = authenticate_inputs()
    geometry = verify_geometry(docs["normal"])
    profile = recovered_washer_profile(docs["washer"])
    ties = fresh_tie_states(docs["replay"], docs["normal"], profile)
    coupon = uniform_column_coupon()

    output.parent.mkdir(parents=True, exist_ok=True)
    output.mkdir(parents=False, exist_ok=False)
    (output / ".gitignore").write_text("*\n")
    (output / "producer.py.snapshot").write_bytes(Path(__file__).read_bytes())
    profile_record = {
        "schema": "annular-column-pressure-profile/v1",
        **profile,
        "stress_field_local_guv_mpa": "sigma_vv(g,u)=-p(sqrt((g-g0)^2+(u-u0)^2)); all other components zero; constant along v",
        "end_tractions_on_wood": {"v_min": "+p(g,u) e_v, inward", "v_max": "-p(g,u) e_v, inward"},
    }
    (output / "pressure-profile.json").write_text(
        json.dumps(profile_record, indent=2, sort_keys=True, allow_nan=False) + "\n"
    )
    report = {
        "schema": "annular-compression-column-anchorage/v1",
        "status": "CONDITIONAL_STATIC_ANNULAR_COLUMN_WITNESS",
        "source_sha256": {str(path.relative_to(ROOT)): digest for path, digest in sorted(pins.items())},
        "counts": {"spines": 2, "proposed_v_axes": 4, "fresh_replay_body_cases": 12,
                   "load_induced_bolt_tensions": 24, "washer_end_tractions": 48},
        "geometry": geometry,
        "pressure_profile": {key: value for key, value in profile_record.items()
                              if key != "radial_pressure_profile_mpa"},
        "load_states": ties,
        "known_answer_coupon": coupon,
        "static_field_theorem": {
            "local_coordinates": "g is grain; u is spine width; v is through-depth bolt axis",
            "section_wrench_order_and_sign": "[N_v,V_g,V_u,M_v,M_g,M_u], positive N_v along +v; moments are about local (g,u)=(0,0)",
            "stress": "sigma(g,u,v)=-p(g,u) e_v tensor e_v inside the swept annulus; zero elsewhere",
            "equilibrium": "p is independent of v, so div(sigma)=0; annular side normals have n_v=0 and zero traction",
            "end_boundary": "the recovered same pressure function p(g,u) acts inward at both washer faces and integrates to T with zero first moment about the bolt axis",
            "section_resultant": "each centered bolt profile carries -T in N_v, zero shear and torque, zero moments about its bolt axis, and signed eccentric moments [-u*T,+g*T] about the stated spine origin",
            "whole_body_pair": "equal/opposite collinear end resultants have zero net force and moment",
            "material_screen": "finite-model pointwise pressure maximum is compared with the existing Fc-perpendicular reference; no mean-only pressure pass is used",
        },
        "joint_integration_contract": [
            "Treat this field as the one normal-transfer component for each existing load-induced T. T already appears in the replay allocation; apply no preload, friction, added capacity, or second 1.25 factor.",
            "In a fresh complete stress model, use the same bounded pressure function on both washer lands. Add this column stress only to complementary stress components that exclude this normal washer transfer; if a model already includes the same tractions, replace or partition that component instead of adding it twice.",
            "At every adopted v-cut, recover the signed full [N_v,V_g,V_u,M_v,M_g,M_u] wrench once about the stated local origin. The column contributes [-T,0,0,0,-u*T,+g*T]; other residual shears, torque, gravity, contacts, and member actions remain in the complete demand.",
            "The existing replay wood_wrench(q,T)=q-T is already the residual after the tie allocation. Do not subtract T again or add this field on top of a pressure witness already representing that full residual.",
            "Compare the combined pointwise stress field at every shared location under the applicable recorded criteria. This local column screen is not a complete-joint result.",
        ],
        "limits": [
            "Exact equilibrium is conditional on the saved M=0 elastic washer/contact pressure profile, equal on both end faces and positive-homogeneous over the replay tension range.",
            "Pressure maximum is exact for the saved finite radial polynomial model only; model assumptions, numerical recovery, delivered washer, installed contact and actual wood are not qualified.",
            "The field has no elastic compatibility proof and carries no shear, torque, bending, or load exit into adjacent members.",
            "No plug-shear or transverse tensile capacity is invented. The only comparison is the existing Fc-perpendicular reference applied to the recovered profile peak.",
            "The result covers the four proposed 108-axis spine v ties only. Existing bolt-host stacks require their own retained geometry and matching pressure profile at both ends; no other joint duty inherits this result.",
            "Proposal remains unadopted; no fabrication, drilling, geometry change, frame/native/CAD solve, or physical release is authorized here.",
        ],
        "proposal_adopted": False,
        "complete_joint_acceptance": False,
        "physical_release": False,
    }
    report_path = output / "checks.json"
    report_path.write_text(json.dumps(report, indent=2, sort_keys=True, allow_nan=False) + "\n")
    outputs = {path.relative_to(output).as_posix(): sha(path)
               for path in sorted(output.rglob("*")) if path.is_file()}
    receipt = {
        "schema": "annular-column-anchorage-receipt/v1",
        "source_sha256": report["source_sha256"],
        "output_sha256": outputs,
        "proposal_adopted": False,
        "complete_joint_acceptance": False,
        "physical_release": False,
    }
    (output / "receipt.json").write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = build(args.output)
    print(json.dumps({"status": report["status"], "output": str(args.output.resolve())}))


if __name__ == "__main__":
    main()
