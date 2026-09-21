"""Source-bound PB02 local tear-out and splitting screens for crossed-bore pairs."""

import hashlib
import json
import math

from fea.current_response_materials import df_l_no2_post_timber
from fea.wider_leg_wood_checks import joint_local_checks
from scripts import simple_center_pb02_hardware_screen as hardware_screen
from scripts import simple_center_pb02_six_case_evidence as six_case_evidence

CASE_ORDER = list(six_case_evidence.EXPECTED_CASES)
HOLE_DIAMETER_MM = 7.3
TOL = 1e-7

# Each row is one bolt acting on one shared member.  Its orthogonal neighbor is
# geometry only: no neighbor force is added, subtracted, or cancelled.
INCIDENCES = {
    "shifted_right_post/post_cleat_2": {
        "member": "shifted_right_post",
        "connection": "post_block/bolt_2",
        "stack_name": "post_cleat_2",
        "through_axis_source": "section_u",
        "neighbor_connection": "rear_block_post/bolt_2",
        "neighbor_stack_name": "post_high",
    },
    "shifted_right_post/post_high": {
        "member": "shifted_right_post",
        "connection": "rear_block_post/bolt_2",
        "stack_name": "post_high",
        "through_axis_source": "section_v",
        "neighbor_connection": "post_block/bolt_2",
        "neighbor_stack_name": "post_cleat_2",
    },
    "upright_side_cleat/upright": {
        "member": "upright_side_cleat",
        "connection": "principal_upright_block/bolt_1",
        "stack_name": "upright",
        "through_axis_source": "section_u",
        "neighbor_connection": "upright_rear_block/bolt_1",
        "neighbor_stack_name": "cleat_link",
    },
    "upright_side_cleat/cleat_link": {
        "member": "upright_side_cleat",
        "connection": "upright_rear_block/bolt_1",
        "stack_name": "cleat_link",
        "through_axis_source": "section_v",
        "neighbor_connection": "principal_upright_block/bolt_1",
        "neighbor_stack_name": "upright",
    },
}


def _sha256(path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _dot(first, second) -> float:
    return sum(a * b for a, b in zip(first, second, strict=True))


def _cross(first, second) -> list[float]:
    return [
        first[1] * second[2] - first[2] * second[1],
        first[2] * second[0] - first[0] * second[2],
        first[0] * second[1] - first[1] * second[0],
    ]


def _subtract(first, second) -> list[float]:
    return [a - b for a, b in zip(first, second, strict=True)]


def _magnitude(vector) -> float:
    return math.sqrt(_dot(vector, vector))


def _unit(vector) -> list[float]:
    length = _magnitude(vector)
    if not math.isfinite(length) or length <= 0:
        raise ValueError("local frame requires a finite nonzero axis")
    return [value / length for value in vector]


def _authenticate_boundary() -> dict:
    result = six_case_evidence.screen()
    source = result.get("source_snapshot_authentication", {})
    if (
        result.get("status")
        != "authenticated_pb02_rear_clear_six_case_development_evidence"
        or result.get("summary", {}).get("accepted_case_count") != 6
        or result.get("summary", {}).get("geometry_fingerprint")
        != six_case_evidence.EXPECTED_GEOMETRY_FINGERPRINT
        or list(result.get("cases", {})) != CASE_ORDER
        or source.get("all_snapshot_hashes_match") is not True
        or result.get("qualified_for_design") is not False
        or result.get("drilling_released") is not False
        or result.get("fabrication_released") is not False
        or result.get("structural_released") is not False
    ):
        raise ValueError("six-case evidence boundary changed")
    return result


def _load_reports(authentication: dict) -> dict:
    reports = {}
    for case in CASE_ORDER:
        authenticated = authentication["cases"][case]
        path = six_case_evidence.SIX_CASE / authenticated["path"] / "report.json"
        if _sha256(path) != authenticated["report_sha256"]:
            raise ValueError(f"{case}: authenticated report changed while loading")
        reports[case] = json.loads(path.read_text())
    return reports


def _member_force(connection: dict, member: str) -> tuple[list[float], str]:
    first = connection.get("first")
    second = connection.get("second")
    if member == first:
        force = connection.get("force_on_first_xyz_n")
        owner = "first"
    elif member == second:
        force = connection.get("force_on_second_xyz_n")
        owner = "second"
    else:
        raise ValueError("incidence member is not owned by connection")
    opposite = connection.get(
        "force_on_second_xyz_n" if owner == "first" else "force_on_first_xyz_n"
    )
    if (
        not isinstance(force, list)
        or not isinstance(opposite, list)
        or len(force) != 3
        or len(opposite) != 3
        or any(not math.isfinite(value) for value in (*force, *opposite))
        or any(abs(a + b) > 1e-8 for a, b in zip(force, opposite, strict=True))
    ):
        raise ValueError("connection action/reaction ownership changed")
    return force, owner


def _build_frame(member: dict, installation_axis: list[float], source: str) -> dict:
    """Map one 3D incidence into helper coordinates X=bolt, Z=grain."""
    grain = _unit(member["axis"])
    through = _unit(installation_axis)
    if abs(_dot(grain, through)) > TOL:
        raise ValueError("bolt axis is not perpendicular to member grain")
    transverse = _unit(_cross(grain, through))
    if (
        abs(_dot(through, transverse)) > TOL
        or abs(_dot(through, grain)) > TOL
        or abs(_dot(transverse, grain)) > TOL
        or _dot(_cross(through, transverse), grain) < 1 - TOL
    ):
        raise ValueError("member-local incidence frame is not orthonormal")

    section_u = _unit(member["section_u"])
    section_v = _unit(member["section_v"])
    expected_through = section_u if source == "section_u" else section_v
    expected_transverse = section_v if source == "section_u" else section_u
    if abs(abs(_dot(through, expected_through)) - 1) > TOL:
        raise ValueError("bolt axis no longer matches its section-axis source")
    if abs(abs(_dot(transverse, expected_transverse)) - 1) > TOL:
        raise ValueError("transverse axis no longer matches the remaining section axis")
    width = member["width_mm"] if source == "section_u" else member["depth_mm"]
    depth = member["depth_mm"] if source == "section_u" else member["width_mm"]
    return {
        "through": through,
        "transverse": transverse,
        "grain": grain,
        "through_axis_source": source,
        "transverse_axis_source": (
            "section_v" if source == "section_u" else "section_u"
        ),
        "through_bolt_width_mm": width,
        "transverse_depth_mm": depth,
    }


def _to_local(vector, frame: dict) -> list[float]:
    return [
        _dot(vector, frame["through"]),
        _dot(vector, frame["transverse"]),
        _dot(vector, frame["grain"]),
    ]


def _point_to_local(point, member: dict, frame: dict) -> list[float]:
    return _to_local(_subtract(point, member["start"]), frame)


def _material() -> dict:
    reference = dict(df_l_no2_post_timber()["reference_override"])
    return {
        "basis": (
            "conservative_conditional_2024_NDS_Table_4D_DF-L_No.2_"
            "Posts_and_Timbers_base_CD_1"
        ),
        "reference_values_mpa": reference,
        "duration_factor_CD": 1.0,
        "size_factor_benefit_used": False,
        "finished_stock_classification_qualified": False,
    }


def _orthogonal_net_section(
    *,
    width: float,
    depth: float,
    active_local: list[float],
    neighbor_local: list[float],
) -> dict:
    """Exact rectangular-strip envelope for two orthogonal through bores.

    At each bore's grain station, one 7.3 mm strip crosses the applicable
    through-thickness.  The stations are farther apart than one diameter, so
    the strips never coexist on one grain-normal cut.  This avoids feeding the
    helper a false same-orientation additional box.
    """
    station_gap = abs(active_local[2] - neighbor_local[2])
    if station_gap <= HOLE_DIAMETER_MM + TOL:
        raise ValueError("orthogonal bore strips overlap in grain station")
    half_hole = HOLE_DIAMETER_MM / 2
    if (
        abs(active_local[1]) + half_hole > depth / 2 + TOL
        or abs(neighbor_local[0]) + half_hole > width / 2 + TOL
    ):
        raise ValueError("orthogonal bore box leaves the member section")
    gross = width * depth
    at_active = width * (depth - HOLE_DIAMETER_MM)
    at_neighbor = (width - HOLE_DIAMETER_MM) * depth
    if min(at_active, at_neighbor) <= 0:
        raise ValueError("orthogonal bore leaves no net section")
    return {
        "method": "exact_two_orthogonal_rectangular_strip_station_envelope",
        "gross_area_mm2": gross,
        "active_bore_station_net_area_mm2": at_active,
        "neighbor_bore_station_net_area_mm2": at_neighbor,
        "minimum_net_area_mm2": min(at_active, at_neighbor),
        "station_separation_mm": station_gap,
        "surface_ligament_mm": station_gap - HOLE_DIAMETER_MM,
        "simultaneous_same_cut_overlap": False,
        "bore_boxes_in_active_incidence_frame": {
            "active_through_x": {
                "axis_local": [1.0, 0.0, 0.0],
                "grain_interval_mm": [
                    active_local[2] - half_hole,
                    active_local[2] + half_hole,
                ],
                "transverse_interval_mm": [
                    active_local[1] - half_hole,
                    active_local[1] + half_hole,
                ],
                "through_interval": "full_member_width",
            },
            "neighbor_through_y": {
                "axis_local_parallel_to": [0.0, 1.0, 0.0],
                "grain_interval_mm": [
                    neighbor_local[2] - half_hole,
                    neighbor_local[2] + half_hole,
                ],
                "through_interval_mm": [
                    neighbor_local[0] - half_hole,
                    neighbor_local[0] + half_hole,
                ],
                "transverse_interval": "full_member_depth",
            },
        },
        "helper_additional_section_boxes_used": False,
        "reason": (
            "The neighbor axis lies in the active grain-normal cut; the helper's "
            "additional boxes assume the same through-thickness orientation."
        ),
    }


def _validate_inventory(report: dict, case: str) -> None:
    physical = report.get("physical_connection_forces", {})
    actual = {name for name in physical if "/bolt_" in name}
    if actual != set(hardware_screen.BOLTS):
        raise ValueError(f"{case}: bolt inventory changed")
    for name, expected in hardware_screen.BOLTS.items():
        row = physical[name]
        for field in ("first", "second", "axis", "edge", "source_rows"):
            if row.get(field) != expected[field]:
                raise ValueError(f"{case}/{name}: bolt inventory changed at {field}")


def _evaluate(case: str, report: dict, name: str, spec: dict) -> dict:
    connection = report["physical_connection_forces"][spec["connection"]]
    neighbor = report["physical_connection_forces"][spec["neighbor_connection"]]
    bolt = hardware_screen.BOLTS[spec["connection"]]
    neighbor_bolt = hardware_screen.BOLTS[spec["neighbor_connection"]]
    if (
        bolt["stack_name"] != spec["stack_name"]
        or neighbor_bolt["stack_name"] != spec["neighbor_stack_name"]
    ):
        raise ValueError(f"{case}/{name}: crossed-bore stack identity changed")

    demand = report.get("member_section_demands", {}).get(spec["member"])
    if demand is None:
        raise ValueError(f"{case}/{name}: member demand inventory changed")
    member = demand["member"]
    if (
        member.get("name") != spec["member"]
        or member.get("qualified_for_design") is not False
        or member.get("retained_area_fraction") != 1.0
        or not math.isclose(
            demand["length_mm"],
            _magnitude(_subtract(member["end"], member["start"])),
            abs_tol=TOL,
        )
    ):
        raise ValueError(f"{case}/{name}: member geometry changed")

    force, owner = _member_force(connection, spec["member"])
    frame = _build_frame(member, connection["axis"], spec["through_axis_source"])
    active_local = _point_to_local(connection["point"], member, frame)
    neighbor_local = _point_to_local(neighbor["point"], member, frame)
    force_local = _to_local(force, frame)
    neighbor_axis_local = _to_local(neighbor["axis"], frame)
    if (
        abs(abs(neighbor_axis_local[1]) - 1) > TOL
        or abs(neighbor_axis_local[0]) > TOL
        or abs(neighbor_axis_local[2]) > TOL
    ):
        raise ValueError(
            f"{case}/{name}: neighbor bore is not orthogonal in local frame"
        )

    material = _material()
    net = _orthogonal_net_section(
        width=frame["through_bolt_width_mm"],
        depth=frame["transverse_depth_mm"],
        active_local=active_local,
        neighbor_local=neighbor_local,
    )
    local = joint_local_checks(
        [active_local],
        [force_local],
        grain=(0.0, 0.0, 1.0),
        centre=(0.0, 0.0, 0.0),
        end_stations_mm=(0.0, demand["length_mm"]),
        depth_mm=frame["transverse_depth_mm"],
        width_mm=frame["through_bolt_width_mm"],
        hole_mm=HOLE_DIAMETER_MM,
        duration_factor=1.0,
        reference_override=material["reference_values_mpa"],
    )
    if len(local["rows"]) != 1 or local["group_tear_out"]:
        raise ValueError(f"{case}/{name}: helper did not retain one-fastener scope")

    parallel_demand = abs(force_local[2])
    net_ratio = parallel_demand / (
        net["minimum_net_area_mm2"] * material["reference_values_mpa"]["Ft_mpa"]
    )
    row_ratio = local["rows"][0]["ratio"]
    nds_modes = {
        "parallel_row_tear_out": row_ratio,
        "orthogonal_bore_net_tension": net_ratio,
    }
    nds_mode = max(nds_modes, key=nds_modes.get)
    split = max(local["splitting"], key=lambda row: row["ratio"])
    transverse = force_local[1]
    loaded_sign = 1 if transverse > TOL else -1 if transverse < -TOL else 0
    loaded_edge = None
    if loaded_sign:
        loaded_edge = {
            "sign": loaded_sign,
            "distance_mm": frame["transverse_depth_mm"] / 2
            - loaded_sign * active_local[1],
            "transverse_force_n": transverse,
        }
        if split["force_sign"] != loaded_sign:
            raise ValueError(f"{case}/{name}: splitting loaded-edge sign changed")

    return {
        "case": case,
        "incidence": name,
        "connection": spec["connection"],
        "member": spec["member"],
        "member_force_owner": owner,
        "signed_force_on_member_xyz_n": force,
        "signed_member_local_force_n": force_local,
        "action_reaction_verified": True,
        "member_local_active_point_mm": active_local,
        "member_local_neighbor_point_mm": neighbor_local,
        "member_local_neighbor_axis": neighbor_axis_local,
        "loaded_transverse_edge": loaded_edge,
        "one_fastener_connection": True,
        "force_count": 1,
        "additional_opening_count": 1,
        "neighbor_force_cancellation_credited": False,
        "orthogonal_net_section": net,
        "nds_appendix_e": {
            "modes": nds_modes,
            "governing_mode": nds_mode,
            "governing_ratio": nds_modes[nds_mode],
            "group_tear_out_applicable": False,
            "one_fastener_row": local["rows"][0],
        },
        "supplemental_ec5_splitting": {
            "governing_ratio": split["ratio"],
            "governing_loaded_edge_sign": split["force_sign"],
            "loaded_edge_distance_he_mm": split["he_mm"],
            "demand_n": split["demand_n"],
            "resistance_n": split["resistance_n"],
            "basis": local["splitting_basis"],
            "separate_from_nds": True,
        },
        "orthogonal_hole_stress_concentration_qualified": False,
        "complete_joint_verdict": False,
    }


def _governing(records: list[dict]) -> dict:
    nds_rows = [
        {
            "family": "NDS_Appendix_E",
            "mode": row["nds_appendix_e"]["governing_mode"],
            "ratio": row["nds_appendix_e"]["governing_ratio"],
            "case": row["case"],
            "incidence": row["incidence"],
        }
        for row in records
    ]
    ec5_rows = [
        {
            "family": "supplemental_EC5_splitting",
            "mode": "directional_splitting",
            "ratio": row["supplemental_ec5_splitting"]["governing_ratio"],
            "case": row["case"],
            "incidence": row["incidence"],
        }
        for row in records
    ]
    nds = max(nds_rows, key=lambda row: row["ratio"])
    ec5 = max(ec5_rows, key=lambda row: row["ratio"])
    return {
        "nds_appendix_e": nds,
        "supplemental_ec5_splitting": ec5,
        "overall": max((nds, ec5), key=lambda row: row["ratio"]),
        "combined_capacity_claim": False,
    }


def screen() -> dict:
    """Evaluate the bounded local mechanism without a complete-joint claim."""
    authentication = _authenticate_boundary()
    reports = _load_reports(authentication)
    cases_by_incidence = {name: {} for name in INCIDENCES}
    records = []
    frames = {}
    neighbors = {}
    material = _material()
    for case in CASE_ORDER:
        report = reports[case]
        _validate_inventory(report, case)
        for name, spec in INCIDENCES.items():
            record = _evaluate(case, report, name, spec)
            cases_by_incidence[name][case] = record
            records.append(record)
            connection = report["physical_connection_forces"][spec["connection"]]
            member = report["member_section_demands"][spec["member"]]["member"]
            frame = _build_frame(
                member, connection["axis"], spec["through_axis_source"]
            )
            if name in frames and frame != frames[name]:
                raise ValueError(f"{case}/{name}: member-local frame changed")
            frames[name] = frame
            net = record["orthogonal_net_section"]
            neighbor_row = {
                "connection": spec["neighbor_connection"],
                "stack_name": spec["neighbor_stack_name"],
                "diameter_mm": HOLE_DIAMETER_MM,
                "station_separation_mm": net["station_separation_mm"],
                "surface_ligament_mm": net["surface_ligament_mm"],
                "force_included": False,
                "represented_in_exact_orthogonal_net_section": True,
                "represented_as_helper_additional_box": False,
            }
            if name in neighbors and neighbor_row != neighbors[name]:
                raise ValueError(f"{case}/{name}: neighboring bore geometry changed")
            neighbors[name] = neighbor_row

    governing = _governing(records)
    decision = "ADVANCE" if governing["overall"]["ratio"] < 1 else "REVISE"
    return {
        "status": "authenticated_six_case_local_wood_envelope",
        "authentication": {
            "six_case_status": authentication["status"],
            "summary_sha256": authentication["summary"]["sha256"],
            "geometry_fingerprint": authentication["summary"]["geometry_fingerprint"],
            "accepted_case_count": authentication["summary"]["accepted_case_count"],
            "source_snapshot_file_count": authentication[
                "source_snapshot_authentication"
            ]["file_count"],
        },
        "case_order": CASE_ORDER,
        "record_count": len(records),
        "hole_diameter_mm": HOLE_DIAMETER_MM,
        "incidences": {
            name: {
                "member": INCIDENCES[name]["member"],
                "connection": INCIDENCES[name]["connection"],
                "member_local_frame": frames[name],
                "neighboring_orthogonal_bore": neighbors[name],
                "material": material,
                "cases": cases_by_incidence[name],
            }
            for name in INCIDENCES
        },
        "governing": governing,
        "disposition": {
            "decision": decision,
            "scope": "local_wood_mechanism_only",
            "criterion": (
                "Maximum separate NDS Appendix E or supplemental EC5 ratio across "
                "24 authenticated case/incidence records."
            ),
            "complete_joint_verdict": False,
        },
        "boundaries": {
            "orthogonal_hole_net_section_evaluated": True,
            "orthogonal_hole_stress_concentration_qualified": False,
            "near_hole_three_dimensional_interaction_qualified": False,
            "complete_joint_verdict": False,
        },
        "qualified_for_design": False,
        "drilling_released": False,
        "fabrication_released": False,
        "structural_released": False,
    }


if __name__ == "__main__":
    print(json.dumps(screen(), indent=2, sort_keys=True, allow_nan=False))
