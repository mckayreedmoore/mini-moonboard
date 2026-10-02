"""Complete top-corner action accounting for the six-case static scenario.

Reuse frozen geometry, connector projections and nodal loads. The host
splitting equation is a characteristic reference, not a design resistance.
"""

import csv
import hashlib
import json
import math
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
BASE = ROOT / "docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28"
COMP = BASE / "current-frame-connector-compliance-attempt04"
MODEL = BASE / "current-springa-frame-input-adapter-attempt01/a12-rear/model.json"
LOADS = (
    BASE
    / "current-frame-pure-solid-matrix-export-preflight-attempt01/source-load-maps.json"
)
CONTACTS = BASE / "reduced-static-attempt01/contact-geometry.json"
HOSTS = HERE.parent / "upper-outer-load-path-2026-10-01/host-actions.json"
GEOMETRY = HERE.parent / "upper-block-strength-2026-10-01/geometry.json"
SPLITTING_CACHE = (
    HERE.parent / "upper-outer-load-path-2026-10-01/splitting-source-cache"
)
MATERIALS = (
    HERE.parent / "hardware-material-specification-2026-09-30/material-inputs.json"
)
PINS = {
    MODEL: "61f95ec9e670b2bd0e95d426cc14ff381283edfc4f9c87e47c2b344dd4fe50b8",
    LOADS: "9cd59d7bbafd65c740d2b0200e3dd88a6a49e6dca0bead0a38bc7826e337548c",
    CONTACTS: "034067430fff5207cdb40819fa8118a367edeb29a8d83926928cc96a0e87d151",
    HOSTS: "5ee4c6da1266d9fd06cc26162fbebb9a96e8e907bd283dda25747d9a63516551",
    GEOMETRY: "2ba66f4242b59e73a7dfc14a0b21d20d1f2710b9f835d60fce569eb73353fe91",
    MATERIALS: "0f33ad8fd517673a4ebbed36c4a30c1cfe07e0d8163165bdc804af91d958fc5a",
    SPLITTING_CACHE
    / "EN1995-1-1-2004-AC-2006.pdf": "ff5bd62c586cc714eed9b8b7e557bbe030f36fe7e3ccd29dd10a24db755b03a5",
    SPLITTING_CACHE
    / "EN1995_3_Dietsch.pdf": "20b6cfc83a1b3a1afb124f9c7cc337ab3b23c141ebe3da8c74906a8eece8017d",
}
BLOCK_HOSTS = {
    "top_outer_left_cleat": ("base_rail_top", "base_side_left"),
    "top_outer_right_cleat": ("base_rail_top", "base_side_right"),
}
N_AXIS = np.array([0.0, -0.766044443, 0.642787610])
N_AXIS /= np.linalg.norm(N_AXIS)
LATERAL = "candidate_bolt_lateral_plane"
CONTACT = "timber_or_panel_contact"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_text())


def require(condition, message):
    if not condition:
        raise ValueError(message)


def wrench(actions, datum):
    force = np.zeros(3)
    moment = np.zeros(3)
    for action in actions:
        f = np.array(action["force_n"])
        force += f
        moment += np.cross(np.array(action["point_mm"]) - datum, f)
        moment += np.array(action["free_moment_nmm"])
    return np.r_[force, moment]


def record_wrench(value, geometry):
    basis = np.array([geometry[k] for k in ("axis", "section_u", "section_v")])
    return {
        "force_xyz_n": value[:3].tolist(),
        "moment_xyz_nmm": value[3:].tolist(),
        "force_grain_u_v_n": (basis @ value[:3]).tolist(),
        "moment_grain_u_v_nmm": (basis @ value[3:]).tolist(),
        "force_global_N_n": float(N_AXIS @ value[:3]),
    }


def physical_actions(body, case, f, model, rows, D, body_names, patches):
    ids = sorted(model["physical_body_nodes"][body])
    center = np.mean([model["nodes"][str(n)] for n in ids], axis=0)
    geometry = model["body_geometry"][body]["geometry_record"]
    start, grain = np.array(geometry["start"]), np.array(geometry["axis"])
    index = body_names.index(body)
    projection = D[:, 6 * index : 6 * index + 6]
    actions = []
    for row in rows:
        own = row["ownership"]
        i = row["row"]
        incident = body in (own["first_body"], own["second_body"])
        require(incident or np.max(abs(projection[i])) < 1e-12, "hidden body action")
        if not incident:
            continue
        point = np.array(own["point_mm"])
        value = -projection[i] * f[i]
        force, moment = value[:3], value[3:] * 1000
        free = moment - np.cross(point - center, force)
        station = float(grain @ (point - start))
        footprint = [station, station]
        cell = patches.get(row["row_id"])
        if cell is not None:
            stations = [grain @ (np.array(v) - start) for v in cell["vertices"]]
            footprint = [float(min(stations)), float(max(stations))]
        actions.append(
            {
                "row": i,
                "source_id": row["row_id"],
                "role": own["role"],
                "other_body": own["second_body"]
                if own["first_body"] == body
                else own["first_body"],
                "point_mm": point.tolist(),
                "force_n": force.tolist(),
                "free_moment_nmm": free.tolist(),
                "station_mm": station,
                "footprint_mm": footprint,
                "cell_area_mm2": None if cell is None else cell["area"],
                "scalar_row_force_n": float(f[i]),
            }
        )
    for node in ids:
        key = str(node)
        force = case["gravity_nodal_map"].get(key, [0, 0, 0])
        force = np.array(force) * case["dead_load_factor"]
        force += np.array(case["climber_nodal_map"].get(key, [0, 0, 0]))
        point = np.array(model["nodes"][key])
        station = float(grain @ (point - start))
        actions.append(
            {
                "row": None,
                "source_id": "body_load_node_" + key,
                "role": "discrete_body_load",
                "other_body": None,
                "point_mm": point.tolist(),
                "force_n": force.tolist(),
                "free_moment_nmm": [0.0, 0.0, 0.0],
                "station_mm": station,
                "footprint_mm": [station, station],
                "cell_area_mm2": None,
                "scalar_row_force_n": None,
            }
        )
    return actions, center, geometry


def pair_action(group, actions, datum, geometry):
    bolt_actions = []
    for axis in group["axis_ids"]:
        components = [
            a
            for a in actions
            if a["role"] == LATERAL and a["source_id"].rsplit("/", 1)[0] == axis
        ]
        require(len(components) == 2, "missing paired bolt components")
        point = np.array(components[0]["point_mm"])
        require(
            np.max(abs(point - components[1]["point_mm"])) < 1e-8, "mixed bolt plane"
        )
        w = wrench(components, point)
        bolt_actions.append(
            {
                "axis_id": axis,
                "point_mm": point.tolist(),
                "force_n": w[:3].tolist(),
                "force_resultant_n": float(np.linalg.norm(w[:3])),
                "free_moment_nmm": w[3:].tolist(),
            }
        )
    p1, p2 = [np.array(a["point_mm"]) for a in bolt_actions]
    f1, f2 = [np.array(a["force_n"]) for a in bolt_actions]
    center = (p1 + p2) / 2
    resultant = f1 + f2
    magnitude = np.linalg.norm(resultant)
    require(magnitude > 1e-8, "undefined pair resultant direction")
    pitch = p2 - p1
    along = abs(float(pitch @ (resultant / magnitude)))
    transverse = math.sqrt(max(0.0, float(pitch @ pitch) - along**2))
    cosine = float(f1 @ f2 / (np.linalg.norm(f1) * np.linalg.norm(f2)))
    sources = [a for a in actions if a["role"] == LATERAL]
    return {
        "individual_bolts": bolt_actions,
        "lateral_wrench_about_body_datum": record_wrench(
            wrench(sources, datum), geometry
        ),
        "lateral_moment_about_pair_center_xyz_nmm": wrench(sources, center)[
            3:
        ].tolist(),
        "angle_between_signed_bolt_forces_degrees": math.degrees(
            math.acos(np.clip(cosine, -1, 1))
        ),
        "pair_resultant_n": float(magnitude),
        "sum_individual_magnitudes_n": float(np.linalg.norm(f1) + np.linalg.norm(f2)),
        "pitch_along_resultant_mm": along,
        "pitch_transverse_to_resultant_mm": transverse,
        "staggered_row_merger_geometry_trigger": transverse < along / 4,
        "equal_sharing_assumed": False,
    }


def host_cut(actions, station, geometry, before):
    start, grain = np.array(geometry["start"]), np.array(geometry["axis"])
    datum = start + station * grain
    # Before: points on the plane are inside the group (+ side). After:
    # points on the plane are inside the group (- side), including end faces.
    positive = [
        a
        for a in actions
        if a["station_mm"] > station + 1e-6
        or (before and abs(a["station_mm"] - station) <= 1e-6)
    ]
    positive_ids = {id(a) for a in positive}
    negative = [a for a in actions if id(a) not in positive_ids]
    plus, minus = wrench(positive, datum), wrench(negative, datum)
    require(np.max(abs((plus + minus)[:3])) <= 0.1, "cut force closure")
    require(np.max(abs((plus + minus)[3:])) <= 2, "cut moment closure")
    crossing = sorted(
        {
            a["source_id"]
            for a in actions
            if a["role"] == CONTACT
            and a["footprint_mm"][0] + 1e-6 < station < a["footprint_mm"][1] - 1e-6
        }
    )
    return {
        "station_mm": station,
        "datum_mm": datum.tolist(),
        "internal_on_positive_half": record_wrench(-plus, geometry),
        "internal_on_negative_half": record_wrench(-minus, geometry),
        "whole_body_closure_force_n": (plus + minus)[:3].tolist(),
        "whole_body_closure_moment_nmm": (plus + minus)[3:].tolist(),
        "other_contact_footprints_crossing_cut": crossing,
        "scope": "Equilibrium of point actions, including discrete nodal loads; not integrated solid traction.",
    }


def host_splitting_reference(group, host_actions, host_geometry, sections):
    target = [a for a in host_actions if a["other_body"] == group["block"]]
    lower = min(a["footprint_mm"][0] for a in target)
    upper = max(a["footprint_mm"][1] for a in target)
    length = np.linalg.norm(np.array(host_geometry["end"]) - host_geometry["start"])
    stations = [max(0.0, lower - 1), min(float(length), upper + 1)]
    cuts = []
    for station, side in zip(stations, ("before", "after"), strict=True):
        section = sections[side]
        require(
            abs(station - section["station_mm"]) < 1e-6, "saved section station changed"
        )
        cuts.append(host_cut(host_actions, station, host_geometry, side == "before"))
    demand = max(
        abs(c[side]["force_global_N_n"])
        for c in cuts
        for side in ("internal_on_positive_half", "internal_on_negative_half")
    )
    section = sections["after"]
    sign = 1 if group["host"] == "base_rail_top" else -1
    v_bounds = section["section_local_bounds_mm"]["v"]
    bounds = sorted(sign * x for x in v_bounds)
    h = bounds[1] - bounds[0]
    u_bounds = section["section_local_bounds_mm"]["u"]
    b = u_bounds[1] - u_bounds[0]
    v = np.array(host_geometry["section_v"])
    bolt_points = group["axis_midplane_coordinates_xyz_mm"]
    # Parallel host sections have the same transverse origin; bind distances
    # to the saved finished section rather than the global bounding box.
    bolt_coordinates = [
        sign * float(v @ (np.array(p) - section["plane_origin_xyz_mm"]))
        for p in bolt_points
    ]
    distances = {
        "positive_N_edge": bounds[1] - min(bolt_coordinates),
        "negative_N_edge": max(bolt_coordinates) - bounds[0],
    }
    references = []
    for edge, he in distances.items():
        require(0 < he < h and b > 0, "splitting equation geometry domain")
        references.append(
            {
                "possible_loaded_edge": edge,
                "he_mm": he,
                "h_mm": h,
                "b_mm": b,
                "w": 1.0,
                "F90_Rk_characteristic_n": 14 * b * math.sqrt(he / (1 - he / h)),
            }
        )
    return {
        "target_transfer_footprint_station_bounds_mm": [lower, upper],
        "cuts": cuts,
        "max_abs_section_V_global_N_n": demand,
        "characteristic_references": references,
        "loaded_edge_selected": False,
        "design_resistance_or_utilization": None,
        "limits": "Host plane only. Both edges retained because the group carries a couple. No design-action conversion, off-plane interaction or complete splitting acceptance.",
    }


def cleat_sections(actions, geometry, samples):
    """Carry all six section components; add a beam screen only on intact cuts."""
    output = []
    start = np.array(geometry["start"])
    grain = np.array(geometry["axis"])
    width, depth = geometry["width_mm"], geometry["depth_mm"]
    for sample in samples:
        station = float(grain @ (np.array(sample["plane_origin_xyz_mm"]) - start))
        for before in (True, False):
            cut = host_cut(actions, station, geometry, before)
            item = {
                "sample_id": sample["sample_id"],
                "sample_kind": sample["sample_kind"],
                "saved_finished_area_mm2": sample["area_mm2"],
                "material_components_on_cut": sample["material_component_count"],
                "trace": "approached_from_negative_station"
                if before
                else "approached_from_positive_station",
                "cut": cut,
                "beam_stress_screen": None,
            }
            if sample["sample_kind"] == "between_adjacent_bolt_stations":
                require(
                    sample["material_component_count"] == 1,
                    "intact cut is disconnected",
                )
                area = width * depth
                require(
                    abs(area - sample["area_mm2"]) < 1e-5,
                    "intact section area differs from rectangle",
                )
                value = cut["internal_on_positive_half"]
                axial, vu, vv = value["force_grain_u_v_n"]
                torque, mu, mv = value["moment_grain_u_v_nmm"]
                # Corners bound linear axial + biaxial bending stress over the
                # intact rectangle. No common strain is assigned across the
                # two/three disconnected regions at a bore station.
                bending = 6 * abs(mu) / (width * depth**2) + 6 * abs(mv) / (
                    depth * width**2
                )
                mean = abs(axial) / area
                require(
                    abs(width - depth) < 1e-6,
                    "square torsion screen used on nonsquare section",
                )
                # Classical Saint-Venant square-section maximum torsional
                # shear, T/(0.208*a^3), added to conservative rectangular
                # transverse component maxima. A short joint disturbance
                # and bore stress concentrations are outside this screen.
                transverse = 1.5 * (abs(vu) + abs(vv)) / area
                torsion = abs(torque) / (0.208 * width**3)
                item["beam_stress_screen"] = {
                    "section_mm": [width, depth],
                    "mean_absolute_parallel_normal_stress_mpa": mean,
                    "biaxial_bending_extreme_sum_mpa": bending,
                    "absolute_parallel_normal_stress_bound_mpa": mean + bending,
                    "rectangular_transverse_shear_component_sum_mpa": transverse,
                    "square_Saint_Venant_torsion_shear_mpa": torsion,
                    "transverse_plus_torsion_shear_screen_mpa": transverse + torsion,
                    "limits": "Elementary beam screen at intact midplanes only. Torsion uses a homogeneous isotropic Saint-Venant square proxy; no orthotropic wood torsion field is established. Does not bound local bore stresses, perpendicular-grain tension, crack propagation, short-block disturbance or all finished sections.",
                }
            output.append(item)
    return output


def main():
    results_path = HERE / "simple-frame-results.json"
    results = read(results_path)
    response_path = HERE / "simple-frame-response.npz"
    require(sha(response_path) == results["response_sha256"], "changed static response")
    for name, digest in results["source_sha256"].items():
        PINS[COMP / name] = digest
    for path, digest in PINS.items():
        require(sha(path) == digest, "changed source: " + str(path))
    require(
        len(results["cases"]) == 6
        and all(
            c["status"] == "PASS_STATIC_SCENARIO_BALANCE_AND_LAWS"
            for c in results["cases"]
        ),
        "incomplete static scenario",
    )
    model, contacts = read(MODEL), read(CONTACTS)
    saved_hosts, geometry_inventory = read(HOSTS), read(GEOMETRY)
    material_base = read(MATERIALS)["conditional_DF_L_No2_base_row"]["base_properties"]
    rows, assessment = (
        read(COMP / "row-identities.json"),
        read(COMP / "assessment.json"),
    )
    groups = [
        g for g in geometry_inventory["two_bolt_groups"] if g["block"] in BLOCK_HOSTS
    ]
    block_samples = {
        b["block"]: b["sampled_sections"]
        for b in geometry_inventory["block_exact_sections"]
        if b["block"] in BLOCK_HOSTS
    }
    require(len(groups) == 4, "expected four corner interfaces")
    patches = {
        c["name"]: {
            "area": c["area_mm2"],
            "vertices": contacts["contact_patches"][c["source_patch_index"]][
                "vertices_xyz_mm"
            ],
        }
        for c in model["contact_cell_ownership"]
        if c["kind"] == CONTACT
    }
    bodies = set(BLOCK_HOSTS) | {h for hosts in BLOCK_HOSTS.values() for h in hosts}
    for body in bodies:
        descriptor = model["body_geometry"][body]["geometry_record"][
            "source_descriptor"
        ]
        path = ROOT / descriptor["step_path"]
        require(sha(path) == descriptor["step_sha256"], "changed finished STEP")
        PINS[path] = descriptor["step_sha256"]
    load_cases = {c["case_id"]: c for c in read(LOADS)["cases"]}
    report_cases, summary_rows = [], []
    with (
        np.load(COMP / "operators.npz", allow_pickle=False) as operators,
        np.load(response_path, allow_pickle=False) as response,
    ):
        D, W = operators["D"], operators["W"]
        body_names = assessment["body_names_in_rigid_column_order"]
        for result in results["cases"]:
            case_id = result["case_id"]
            case = dict(
                load_cases[case_id], dead_load_factor=results["dead_load_factor"]
            )
            force = response[case_id + "_force_n"]
            actions_by_body, body_records = {}, []
            column = next(
                c["column"]
                for c in assessment["load_columns"]
                if c["case_id"] == case_id and c["kind"] == "gravity_nodal_map"
            )
            for body in sorted(bodies):
                actions, datum, geometry = physical_actions(
                    body, case, force, model, rows, D, body_names, patches
                )
                actions_by_body[body] = (actions, datum, geometry)
                index = body_names.index(body)
                external = wrench(
                    [a for a in actions if a["role"] == "discrete_body_load"], datum
                )
                expected = (
                    W[6 * index : 6 * index + 6, column] * results["dead_load_factor"]
                    + W[6 * index : 6 * index + 6, column + 1]
                )
                expected[3:] *= 1000
                require(
                    np.max(abs(external - expected)) < 1e-6,
                    "nodal loads do not reproduce W",
                )
                closure = wrench(actions, datum)
                require(
                    np.max(abs(closure[:3])) <= 0.1 and np.max(abs(closure[3:])) <= 2,
                    "complete body balance",
                )
                body_records.append(
                    {
                        "body": body,
                        "datum_mm": datum.tolist(),
                        "incident_scalar_connector_rows": sum(
                            a["row"] is not None for a in actions
                        ),
                        "discrete_load_nodes": sum(
                            a["role"] == "discrete_body_load" for a in actions
                        ),
                        "force_residual_n": closure[:3].tolist(),
                        "moment_residual_nmm": closure[3:].tolist(),
                        "max_connector_free_moment_nmm": max(
                            np.max(np.abs(a["free_moment_nmm"])) for a in actions
                        ),
                        "external_load_wrench": record_wrench(external, geometry),
                    }
                )
            sections_by_block = {}
            for block, hosts in BLOCK_HOSTS.items():
                actions, datum, geometry = actions_by_body[block]
                receiver_total = wrench(
                    [a for a in actions if a["other_body"] in hosts], datum
                )
                other_connections = [
                    a
                    for a in actions
                    if a["row"] is not None and a["other_body"] not in hosts
                ]
                require(not other_connections, "unaccounted cleat receiver")
                body_load = wrench(
                    [a for a in actions if a["role"] == "discrete_body_load"], datum
                )
                require(
                    np.max(abs((receiver_total + body_load)[:3])) < 0.1,
                    "rail-to-cleat-to-side force closure",
                )
                require(
                    np.max(abs((receiver_total + body_load)[3:])) < 2,
                    "rail-to-cleat-to-side moment closure",
                )
                sections_by_block[block] = cleat_sections(
                    actions, geometry, block_samples[block]
                )
            interfaces = []
            for group in groups:
                block, host = group["block"], group["host"]
                actions, datum, geometry = actions_by_body[block]
                target = [a for a in actions if a["other_body"] == host]
                require(
                    len(target) == 10,
                    "expected four contact, four lateral and two axial rows",
                )
                modes = {
                    role: record_wrench(
                        wrench([a for a in target if a["role"] == role], datum),
                        geometry,
                    )
                    for role in sorted({a["role"] for a in target})
                }
                pair = pair_action(group, target, datum, geometry)
                cells = [a for a in target if a["role"] == CONTACT]
                densities = [
                    max(0.0, a["scalar_row_force_n"]) / a["cell_area_mm2"]
                    for a in cells
                ]
                host_actions, _, host_geometry = actions_by_body[host]
                sections = saved_hosts["host_geometry_and_source_station_inventories"][
                    host
                ]["finished_step_bracket_sections"][block]
                splitting = host_splitting_reference(
                    group, host_actions, host_geometry, sections
                )
                interface = {
                    "block": block,
                    "host": host,
                    "datum_mm": datum.tolist(),
                    "complete_receiver_wrench_on_block": record_wrench(
                        wrench(target, datum), geometry
                    ),
                    "receiver_wrench_by_role": modes,
                    "individual_source_actions_on_block": target,
                    "lateral_bolt_pair": pair,
                    "maximum_contact_cell_reaction_density_n_per_mm2": max(densities),
                    "contact_density_limit": "Four conditional spring cells, not resolved peak contact pressure or a resistance check.",
                    "host_splitting_plane_scenario": splitting,
                }
                interfaces.append(interface)
                summary_rows.append(
                    {
                        "case_id": case_id,
                        "block": block,
                        "host": host,
                        "pair_net_n": pair["pair_resultant_n"],
                        "sum_bolt_magnitudes_n": pair["sum_individual_magnitudes_n"],
                        "signed_bolt_force_angle_degrees": pair[
                            "angle_between_signed_bolt_forces_degrees"
                        ],
                        "pair_center_couple_norm_nmm": float(
                            np.linalg.norm(
                                pair["lateral_moment_about_pair_center_xyz_nmm"]
                            )
                        ),
                        "max_contact_cell_density_mpa": max(densities),
                        "max_host_section_V_N_n": splitting[
                            "max_abs_section_V_global_N_n"
                        ],
                        "positive_edge_F90_Rk_n": splitting[
                            "characteristic_references"
                        ][0]["F90_Rk_characteristic_n"],
                        "negative_edge_F90_Rk_n": splitting[
                            "characteristic_references"
                        ][1]["F90_Rk_characteristic_n"],
                    }
                )
            report_cases.append(
                {
                    "case_id": case_id,
                    "complete_body_balance": body_records,
                    "interfaces": interfaces,
                    "cleat_section_traces": sections_by_block,
                }
            )
    for path, digest in PINS.items():
        require(sha(path) == digest, "source changed during calculation: " + str(path))
    require(
        sha(response_path) == results["response_sha256"],
        "static response changed during calculation",
    )
    csv_path = HERE / "top-corner-case-summary.csv"
    with csv_path.open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(summary_rows[0]))
        writer.writeheader()
        writer.writerows(summary_rows)
    report = {
        "schema": "simple_static_top_corner_actions/v1",
        "candidate": results["candidate"],
        "revision_id": results["revision_id"],
        "source_sha256": {str(p.relative_to(ROOT)): d for p, d in PINS.items()},
        "static_results_sha256": sha(results_path),
        "static_response_sha256": sha(response_path),
        "producer_sha256": sha(Path(__file__)),
        "summary_csv_sha256": sha(csv_path),
        "counts": {
            "cases": 6,
            "interfaces": 4,
            "interface_states": len(summary_rows),
            "body_balance_states": len(report_cases) * len(bodies),
            "cleat_section_traces": 120,
            "intact_midplane_beam_screens": 48,
        },
        "method": {
            "physical_interface_action": "-D_row_body*f; scaled rotational columns multiplied by 1000 mm. Nodal loads independently reproduce the W wrench.",
            "host_splitting_reference": "EN 1995-1-1:2004/AC:2006 Eq. 8.4, F90,Rk = 14*b*sqrt(he/(1-he/h)), ordinary bolts w=1. Both possible loaded edges; no design conversion.",
            "section_demand": "Maximum absolute global N shear immediately outside each complete finite transfer footprint. All concurrent host connectors and discrete nodal loads included.",
            "pair_sharing": "Individual same-state bolt forces and their couple retained; no equal sharing or replacement by net force.",
            "cleat_sections": "Two one-sided traces at each of the five saved exact finished cuts. Elementary rectangular normal/shear/torsion screens only at intact interstation midplanes; no stress allocation across bore-section components.",
            "square_torsion_source": "MIT 1.050 Solid Mechanics, Fall 2004, Problem Set 8 solutions, PDF p.3; k2=0.208 for the homogeneous square shaft, https://ocw.mit.edu/courses/1-050-solid-mechanics-fall-2004/731b245ebecfef588f5002a94cbf667f_pset04_8soln.pdf . Isotropic proxy only, not an adopted timber torsion method.",
        },
        "conditional_material_base_references_mpa": {
            key: material_base[key] * 0.006894757293168361
            for key in (
                "Fb",
                "Ft_parallel",
                "Fv_parallel",
                "Fc_perpendicular",
                "Fc_parallel",
            )
        },
        "cases": report_cases,
        "complete_joint_acceptance": False,
        "physical_release": False,
        "reviewed_geometry_changed": False,
        "native_run": False,
    }
    (HERE / "top-corner-actions.json").write_text(
        json.dumps(report, indent=2, allow_nan=False) + "\n"
    )
    print("Computed 24 complete corner interface states and 30 whole-body balances.")
    for group in groups:
        values = [
            r
            for r in summary_rows
            if r["block"] == group["block"] and r["host"] == group["host"]
        ]
        peak = max(values, key=lambda r: r["max_host_section_V_N_n"])
        print(
            group["group_id"],
            peak["case_id"],
            "host shear N",
            round(peak["max_host_section_V_N_n"], 1),
            "characteristic references N",
            round(peak["positive_edge_F90_Rk_n"], 1),
            round(peak["negative_edge_F90_Rk_n"], 1),
        )


if __name__ == "__main__":
    main()
