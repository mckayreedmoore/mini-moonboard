"""CAD-only capacity screen for the two-vertical-bolt principal/header joint.

This is a deliberately bounded screening calculation.  It adapts published
wood-connection methods to the current CAD and compares them with authenticated
old-topology response proxies.  It is not a cross-dowel design value, a fresh
barrel-candidate solve, or a fabrication release.
"""

from __future__ import annotations

import json
import math
from pathlib import Path

import cadquery as cq
import numpy as np
from scipy.spatial import ConvexHull

from mini_moonboard.bolted_timber_checks import dfl_dowel_bearing_psi
from scripts import owner_barrel_candidate_service as service
from scripts import owner_barrel_vertical_center_probe as probe
from scripts import owner_layout_protected as protected
from scripts.owner_barrel_coordinates import T, local_bounds

ROOT = Path(__file__).resolve().parents[1]
PROXY = ROOT / "docs/bolted-candidate-prototypes/center-reference-diagnostic.json"
MATERIAL = ROOT / "docs/bolted-candidate-material-basis.json"
HARDWARE = ROOT / "docs/barrel-nut-selected-hardware.json"

SCHEMA = "owner_barrel_vertical_center_capacity/v1"
N_PER_LBF = 4.4482216152605
MPA_PER_PSI = 0.006894757293168
ROW_PITCH_MM = 80.0
GROUP_Y_MM = -106.0
INTERFACE_Z_MM = 277.0
BARREL_LOAD_TO_GRAIN_DEG = 40.0
EXPECTED_DEFAULT_CASES = {
    "a1-rear",
    "a12-left",
    "a12-rear",
    "k12-rear",
    "k12-right",
}


def _cross(first, second):
    return [
        first[1] * second[2] - first[2] * second[1],
        first[2] * second[0] - first[0] * second[2],
        first[0] * second[1] - first[1] * second[0],
    ]


def _add(first, second):
    return [a + b for a, b in zip(first, second, strict=True)]


def _subtract(first, second):
    return [a - b for a, b in zip(first, second, strict=True)]


def _round(value, digits=6):
    return round(float(value), digits)


def _load_inputs():
    material = json.loads(MATERIAL.read_text())
    hardware = json.loads(HARDWARE.read_text())
    proxy = json.loads(PROXY.read_text())
    values = material["reference_values"]
    barrel = hardware["barrel"]
    washer = hardware["washers"][0]
    bolt = next(row for row in hardware["bolts"] if row["product"] == "1456BHT5")
    if (
        material["species_grade"] != "US Douglas Fir-Larch No. 2 dimension lumber"
        or values["G"]["value"] != 0.5
        or values["Fc_perpendicular"]["value"] != 625
        or values["Ft_parallel"]
        != {
            "value": 575,
            "unit": "psi",
            "adjusted": False,
            "meaning": "tension parallel to grain only",
        }
        or values["Fv_parallel"]
        != {
            "value": 180,
            "unit": "psi",
            "adjusted": False,
            "meaning": "member shear parallel to grain",
        }
        or barrel["product"] != "JCD14201606NL ZN"
        or washer["product"] != "33857"
        or bolt["minimum_proof_psi"] != 85_000
        or proxy["scope"]
        != "Baseline ML24Z/SDS proxy only; no bolted demand, acceptance, or drilling release."
    ):
        raise ValueError("Vertical-center capacity source basis changed")
    return material, hardware, proxy, barrel, washer, bolt


def _proxy_demands(proxy):
    default = proxy["accepted_default_v2"]
    sensitivity = proxy["a1_rear_sensitivity"]
    if {row["case"] for row in default} != EXPECTED_DEFAULT_CASES:
        raise ValueError("Five accepted default proxy cases changed")
    if {row["series"] for row in sensitivity} != {
        "proxy-scale0p1",
        "proxy-scale10",
    }:
        raise ValueError("A1 proxy stiffness sensitivity changed")

    rows = []
    for source_group, cases in (
        ("five_accepted_default_proxies", default),
        ("a1_stiffness_sensitivity", sensitivity),
    ):
        for case in cases:
            for side in probe.SIDES:
                interface = case["sides"][side]["interfaces"]["principal_header"]
                force = interface["on_center_member"]["force_xyz_n"]
                old_moment = interface["on_center_member"]["moment_xyz_nmm"]
                old_origin = interface["origin_xyz_mm"]
                new_origin = [
                    -70.0 if side == "left" else 70.0,
                    GROUP_Y_MM,
                    INTERFACE_Z_MM,
                ]
                moment = _add(
                    old_moment,
                    _cross(_subtract(old_origin, new_origin), force),
                )
                # Two rows can resolve Fz/Mx and Fx/Mz.  Equal Fy sharing is
                # reported, while My is deliberately left unresolved.
                row_actions = (
                    (
                        "rear",
                        force[2] / 2 - moment[0] / ROW_PITCH_MM,
                        force[0] / 2 + moment[2] / ROW_PITCH_MM,
                    ),
                    (
                        "forward",
                        force[2] / 2 + moment[0] / ROW_PITCH_MM,
                        force[0] / 2 - moment[2] / ROW_PITCH_MM,
                    ),
                )
                for row_name, axial, lateral_x in row_actions:
                    resultant = math.sqrt(axial**2 + lateral_x**2 + (force[1] / 2) ** 2)
                    rows.append(
                        {
                            "source_group": source_group,
                            "series": case["series"],
                            "case": case["case"],
                            "side": side,
                            "row": row_name,
                            "axial_n": _round(axial),
                            "assigned_lateral_x_n": _round(lateral_x),
                            "assigned_lateral_y_n": _round(force[1] / 2),
                            "assigned_resultant_n": _round(resultant),
                            "shifted_interface_moment_xyz_nmm": [
                                _round(value) for value in moment
                            ],
                        }
                    )
    maximum_axial = max(rows, key=lambda row: abs(row["axial_n"]))
    maximum_tension = max(rows, key=lambda row: max(0.0, -row["axial_n"]))
    maximum_compression = max(rows, key=lambda row: max(0.0, row["axial_n"]))
    maximum_resultant = max(rows, key=lambda row: row["assigned_resultant_n"])
    maximum_unresolved_my = max(
        abs(row["shifted_interface_moment_xyz_nmm"][1]) for row in rows
    )
    return {
        "rows": rows,
        "maximum_absolute_axial_row_n": abs(maximum_axial["axial_n"]),
        "maximum_axial_row": maximum_axial,
        "maximum_bolt_tension_row_n": max(0.0, -maximum_tension["axial_n"]),
        "maximum_bolt_tension_row": maximum_tension,
        "maximum_face_compression_row_n": max(0.0, maximum_compression["axial_n"]),
        "maximum_face_compression_row": maximum_compression,
        "maximum_assigned_resultant_row_n": maximum_resultant["assigned_resultant_n"],
        "maximum_assigned_resultant_row": maximum_resultant,
        "maximum_unresolved_my_nmm": maximum_unresolved_my,
    }


def _principal_combined_cut_sections(barrel, washer, bolt):
    """Query nominal sections at all four barrel stations from source solids."""
    source, wood, seam = probe._source_geometry()
    post_geometry = probe._post_and_backer_geometry(wood, seam)
    joint = probe._joint_geometry(wood, post_geometry, barrel, washer, bolt)
    inherited = service.candidate_service_cutters(source, wood)
    additional = tuple(source.additional_machining_cutters())
    inventory = protected.inventory()["solids"]
    connections = {row.name: row for row in source.connections()}
    sample_thickness_mm = 0.5
    rows = []
    for side in probe.SIDES:
        member = f"base_principal_center_{side}"
        principal = wood[member]
        cut = principal
        inherited_cutters = [
            shape for host, _name, shape in inherited if host == member
        ]
        additional_cutters = [row[-1] for row in additional if row[0] == member]
        maintained_cutters = []
        for family in ("panel_screws", "frame_bolts"):
            for name, cutter in inventory[family].items():
                if (
                    member in connections[name].members
                    and cutter.intersect(principal).Volume() > 1e-6
                ):
                    maintained_cutters.append(cutter)
        for cutter in (
            *inherited_cutters,
            *additional_cutters,
            *maintained_cutters,
            *joint["cuts"][member],
        ):
            cut = cut.cut(cutter)
        bounds = local_bounds(principal)
        records = [row for row in joint["records"] if row["hosts"][1] == member]
        for record in records:
            y, z = record["thread_axis_xyz_mm"][1:]
            center_t = y * T[0] + z * T[1]
            slab = cq.Solid.makeBox(
                bounds["x"][1] - bounds["x"][0] + 2,
                sample_thickness_mm,
                bounds["n"][1] - bounds["n"][0] + 2,
                cq.Vector(
                    bounds["x"][0] - 1,
                    center_t - sample_thickness_mm / 2,
                    bounds["n"][0] - 1,
                ),
            ).rotate(
                (0, 0, 0),
                (1, 0, 0),
                math.degrees(math.atan2(T[1], T[0])),
            )
            rows.append(
                {
                    "member": member,
                    "bolt": record["name"],
                    "sample_center_t_mm": _round(center_t),
                    "sample_thickness_mm": sample_thickness_mm,
                    "inherited_cut_count": len(inherited_cutters),
                    "additional_machining_cut_count": len(additional_cutters),
                    "maintained_connection_cut_count": len(maintained_cutters),
                    "candidate_cut_count": len(joint["cuts"][member]),
                    "gross_area_mm2": _round(
                        principal.intersect(slab).Volume() / sample_thickness_mm
                    ),
                    "combined_cut_net_area_mm2": _round(
                        cut.intersect(slab).Volume() / sample_thickness_mm
                    ),
                }
            )
    if len(rows) != 4 or any(row["combined_cut_net_area_mm2"] <= 0 for row in rows):
        raise ValueError("Principal combined-cut section query failed")
    return rows


def _principal_raw_ray_distances(barrel, washer, bolt):
    """Query signed grain/cross-grain rays to actual raw principal faces."""
    _source, wood, seam = probe._source_geometry()
    post_geometry = probe._post_and_backer_geometry(wood, seam)
    joint = probe._joint_geometry(wood, post_geometry, barrel, washer, bolt)
    rows = []
    directions = {
        "grain_positive_mm": np.asarray((1.0, 0.0)),
        "grain_negative_mm": np.asarray((-1.0, 0.0)),
        "cross_grain_positive_mm": np.asarray((0.0, 1.0)),
        "cross_grain_negative_mm": np.asarray((0.0, -1.0)),
    }
    for side in probe.SIDES:
        member = f"base_principal_center_{side}"
        principal = wood[member]
        polygon = np.asarray(
            [
                [
                    vertex.Y * T[0] + vertex.Z * T[1],
                    -vertex.Y * T[1] + vertex.Z * T[0],
                ]
                for vertex in principal.Vertices()
            ]
        )
        hull = ConvexHull(polygon)
        records = [row for row in joint["records"] if row["hosts"][1] == member]
        for record in records:
            _x, y, z = record["thread_axis_xyz_mm"]
            center = np.asarray((y * T[0] + z * T[1], -y * T[1] + z * T[0]))
            result = {"member": member, "bolt": record["name"]}
            if (
                max(a * center[0] + b * center[1] + c for a, b, c in hull.equations)
                > 1e-7
            ):
                raise ValueError(
                    f"{record['name']}: barrel center outside raw principal"
                )
            for label, direction in directions.items():
                candidates = []
                for a, b, c in hull.equations:
                    rate = a * direction[0] + b * direction[1]
                    if rate > 1e-9:
                        candidates.append(-(a * center[0] + b * center[1] + c) / rate)
                result[label] = _round(min(candidates))
            rows.append(result)
    if len(rows) != 4 or any(row[label] <= 0 for row in rows for label in directions):
        raise ValueError("Principal raw-face ray query failed")
    return rows


def _resistance_screen(barrel, washer, bolt, geometry, demand_n, material=None):
    material = _load_inputs()[0] if material is None else material
    ft_parallel_psi = material["reference_values"]["Ft_parallel"]["value"]
    diameter_mm = barrel["nominal_body_od_mm"]
    length_mm = barrel["nominal_body_length_mm"]
    cross_hole_mm = probe.BOLT_BORE_DIAMETER_MM
    fe_psi = dfl_dowel_bearing_psi(diameter_mm / 25.4, BARREL_LOAD_TO_GRAIN_DEG)
    fe_mpa = fe_psi * MPA_PER_PSI
    projected_area = diameter_mm * length_mm - math.pi * cross_hole_mm**2 / 4
    rectangular_area = diameter_mm * (length_mm - cross_hole_mm)
    nds_mode_i_rd = 4 * (1 + 0.25 * BARREL_LOAD_TO_GRAIN_DEG / 90)
    nds_fabbri_reference_n = fe_mpa * projected_area / nds_mode_i_rd
    fpl_rectangular_reference_n = fe_mpa * rectangular_area / 4

    records = geometry["principal_header_joint"]["records"]
    ray_records = _principal_raw_ray_distances(barrel, washer, bolt)
    rays_by_bolt = {row["bolt"]: row for row in ray_records}
    local_centers = {}
    for row in records:
        row_name = "rear" if row["bolt_seat_xyz_mm"][1] == -146.0 else "forward"
        rays = rays_by_bolt[row["name"]]
        local_centers.setdefault(row_name, []).append(
            {
                "end_center_mm": min(
                    rays["grain_negative_mm"], rays["grain_positive_mm"]
                ),
                "edge_center_mm": min(
                    rays["cross_grain_negative_mm"],
                    rays["cross_grain_positive_mm"],
                ),
                "signed_raw_face_rays_mm": {
                    name: value for name, value in rays.items() if name.endswith("_mm")
                },
            }
        )
    if any(len(rows) != 2 for rows in local_centers.values()):
        raise ValueError("Expected matching left/right geometry for both rows")
    provisional_factors = {}
    for row_name, duplicates in local_centers.items():
        datum = duplicates[0]
        end_ratio = min(1.0, datum["end_center_mm"] / (7 * diameter_mm))
        edge_ratio = min(1.0, datum["edge_center_mm"] / (4 * diameter_mm))
        provisional_factors[row_name] = {
            **datum,
            "end_distance_over_7d": _round(end_ratio),
            "edge_distance_over_4d": _round(edge_ratio),
            "provisional_minimum_factor": _round(min(end_ratio, edge_ratio)),
            "status": "SENSITIVITY_NOT_ADOPTED_FOR_ANGLED_LOAD",
        }
    worst_factor = min(
        row["provisional_minimum_factor"] for row in provisional_factors.values()
    )

    washer_area = (
        math.pi
        / 4
        * (washer["od_min_mm"] ** 2 - max(washer["id_max_mm"], cross_hole_mm) ** 2)
    )
    washer_reference_n = 625 * MPA_PER_PSI * washer_area
    bolt_proof_n = (
        hardware_proof_lbf := 0.0318 * bolt["minimum_proof_psi"]
    ) * N_PER_LBF
    section_rows = _principal_combined_cut_sections(barrel, washer, bolt)
    minimum_section = min(row["combined_cut_net_area_mm2"] for row in section_rows)

    def comparison(resistance_n):
        ratio = demand_n / resistance_n
        return {
            "proxy_bolt_tension_demand_n": _round(demand_n),
            "demand_to_reference_ratio": _round(ratio),
            "relation": "ABOVE_PROXY_REFERENCE"
            if ratio <= 1
            else "BELOW_PROXY_REFERENCE",
        }

    return {
        "wood_barrel_bearing": {
            "load_to_grain_angle_deg": BARREL_LOAD_TO_GRAIN_DEG,
            "dfl_dowel_bearing_psi": _round(fe_psi),
            "fabbri_projected_area_mm2": _round(projected_area),
            "nds_mode_i_reduction_term": _round(nds_mode_i_rd),
            "nds_fabbri_nominal_reference_n": _round(nds_fabbri_reference_n),
            "fpl_rectangular_area_mm2": _round(rectangular_area),
            "fpl_divide_by_four_reference_n": _round(fpl_rectangular_reference_n),
            "provisional_distance_factors": provisional_factors,
            "worst_provisional_distance_factor": _round(worst_factor),
            "distance_reduced_nds_fabbri_reference_n": _round(
                nds_fabbri_reference_n * worst_factor
            ),
            "distance_reduced_fpl_reference_n": _round(
                fpl_rectangular_reference_n * worst_factor
            ),
            "comparison": comparison(nds_fabbri_reference_n * worst_factor),
            "limit": (
                "Adapted method only. Cross-dowel capacity is not transferred; "
                "angled-load C_delta and adverse cuts remain unqualified."
            ),
        },
        "header_washer_bearing": {
            "washer_contact_area_mm2": _round(washer_area),
            "fc_perpendicular_psi": 625,
            "nominal_reference_n": _round(washer_reference_n),
            "comparison": comparison(washer_reference_n),
            "limit": (
                "Ideal rigid full-annulus contact with Cb=1; washer flexure, seat "
                "defects, tolerances, and other adjustments are not credited."
            ),
        },
        "bolt_constituent_proof": {
            "stress_area_in2": 0.0318,
            "minimum_proof_psi": bolt["minimum_proof_psi"],
            "minimum_proof_lbf": _round(hardware_proof_lbf),
            "minimum_proof_n": _round(bolt_proof_n),
            "comparison": comparison(bolt_proof_n),
            "limit": "Bolt constituent only; no combined tension/shear/bending credit.",
        },
        "parallel_net_section_sensitivity": {
            "status": "REFERENCE_ONLY",
            "source_built_nominal_sections": section_rows,
            "minimum_nominal_combined_cut_area_mm2": minimum_section,
            "ft_parallel_psi": ft_parallel_psi,
            "unadjusted_reference_n": _round(
                minimum_section * ft_parallel_psi * MPA_PER_PSI
            ),
            "limit": (
                "Nominal CAD section at the rear barrel station; load is oblique, "
                "tension perpendicular to grain is not assigned, and tolerances "
                "are absent."
            ),
        },
        "principal_raw_face_rays": ray_records,
        "unsupported": {
            "barrel_metal_thread_wall_and_flexure": "UNRESOLVED_NO_CONTROLLED_STAFAST_STRENGTH_OR_THREAD_DATA",
            "signed_two_plane_shear_blocks": "NOMINAL_GEOMETRY_MAPPED_SEPARATELY_RESISTANCE_UNRESOLVED",
            "splitting_and_tension_perpendicular_to_grain": "NOMINAL_PLANE_MAPPED_SEPARATELY_RESISTANCE_UNSUPPORTED",
            "complete_lateral_yield_and_combined_action": "UNRESOLVED",
            "joint_stiffness_and_load_sharing": "UNRESOLVED",
            "my_twist_path": "STATIC_PROXY_TOPOLOGY_MAPPED_SEPARATELY_STIFFNESS_UNRESOLVED",
        },
    }


def build_report():
    material, _hardware, proxy, barrel, washer, bolt = _load_inputs()
    geometry = probe.build_report()
    screws = geometry["panel_screws"]
    if (
        geometry["decision"]["nominal_and_provisional_tolerance_geometry"]
        != "CANDIDATE"
        or screws["source_count"] != 66
        or screws["unchanged_count"] + screws["relocated_count"] != 66
    ):
        raise ValueError("66-screw vertical-center geometry is not a candidate")
    demands = _proxy_demands(proxy)
    resistance = _resistance_screen(
        barrel,
        washer,
        bolt,
        geometry,
        demands["maximum_bolt_tension_row_n"],
        material,
    )
    below_proxy = [
        name
        for name in ("wood_barrel_bearing", "header_washer_bearing")
        if resistance[name]["comparison"]["relation"] == "BELOW_PROXY_REFERENCE"
    ]
    return {
        "schema": SCHEMA,
        "candidate": "compact-floor-flush-bolted-development",
        "scope": "two-vertical-bolt principal/header CAD-only screen",
        "sources": {
            "geometry": "scripts/owner_barrel_vertical_center_probe.py",
            "demand_proxy": str(PROXY.relative_to(ROOT)),
            "material": str(MATERIAL.relative_to(ROOT)),
            "hardware": str(HARDWARE.relative_to(ROOT)),
            "fpl_rp_586": "https://research.fs.usda.gov/download/treesearch/6003.pdf",
            "fabbri_2022": "https://iris.unife.it/retrieve/aaead297-7bcb-4893-b331-847d56b3752f/Fabbri_Tullini_Minghini_2022%20-%20post-print.pdf",
            "awc_2024_nds": "https://awc.org/resources/2024-nds/",
            "nasa_fastener_manual": "https://ntrs.nasa.gov/api/citations/19900009424/downloads/19900009424.pdf",
        },
        "geometry": {
            "row_pitch_mm": ROW_PITCH_MM,
            "barrel_x_ligament_mm": geometry["principal_header_joint"]["records"][0][
                "barrel_x_edge_ligament_mm"
            ],
            "wood_beyond_blind_barrel_bore_mm": geometry["principal_header_joint"][
                "records"
            ][0]["wood_beyond_barrel_bore_mm"],
            "washer_header_edge_reserve_mm": geometry["principal_header_joint"][
                "minimum_max_washer_header_edge_reserve_mm"
            ],
            "panel_kicker_screw_count": screws["source_count"],
            "panel_kicker_axes_unchanged": screws["unchanged_count"],
            "panel_kicker_axes_relocated": screws["relocated_count"],
            "old_2p092_mm_header_pocket_applicable": False,
            "old_header_pocket_disposition": (
                "Eliminated by the flat underside seats of the vertical bolts."
            ),
        },
        "demands": {
            "basis": (
                "Five authenticated old-topology total-interface proxies plus A1 "
                "0.1x/10x stiffness sensitivity; shifted to current group centroid."
            ),
            "fresh_barrel_cases": 0,
            "missing_case": "a12-forward",
            "qualified_demand": False,
            "row_resolution": (
                "This preliminary row split assigns Fz/Mx and Fx/Mz to two rows "
                "and splits Fy equally. It leaves My unresolved locally; the "
                "separate signed face-contact screen supplies a static topology "
                "witness. Positive axial is face compression and negative axial "
                "is bolt tension."
            ),
            **demands,
        },
        "resistance": resistance,
        "decision": {
            "cad_only_adapted_reference_screen": (
                "BELOW_PROXY_IN_AT_LEAST_ONE_REFERENCE"
                if below_proxy
                else "ABOVE_PROXY_ADAPTED_REFERENCES_ONLY"
            ),
            "below_proxy_adapted_references": below_proxy,
            "finite_decision": "EVIDENCE_BLOCKED",
            "physical_joint_failure_proved": False,
            "paper_only_go_available_for_current_stafast_part": False,
            "reason": (
                "Nominal/adapted barrel-bearing, washer-bearing, raw bolt-proof, "
                "and parallel-net-section references exceed the proxy bolt-tension "
                "action. They are not adopted capacities. Actual barrel metal/thread, "
                "splitting resistance, adverse-tolerance shear paths, compatible "
                "My stiffness, and fresh six-case demands remain open."
            ),
            "next_design_action": (
                "Extend nominal breakout and contact maps to adverse tolerances, "
                "obtain controlled STAFAST geometry, thread, material, and proof "
                "evidence, then build a bounded stiffness model."
            ),
            "diy_ready": False,
            "drilling_released": False,
            "fabrication_released": False,
            "structural_released": False,
        },
    }


if __name__ == "__main__":
    print(json.dumps(build_report(), indent=2, sort_keys=True))
