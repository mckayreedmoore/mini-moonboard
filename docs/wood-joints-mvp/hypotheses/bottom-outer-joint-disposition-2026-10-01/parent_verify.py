#!/usr/bin/env python3
"""Independent source and arithmetic verification for the bottom-outer join."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
PACKETS = HERE.parent
PRODUCER = HERE / "produce.py"
PRODUCER_SHA = "a941dceee5c002068e9920cfe41f62270e11ff399367fdf9494c445a06d8a86d"
REPORT_SHA = "fcf393be26c433daf760a6afcf9fd6260d88f04f43a6234def960bbba4789029"
SOURCE_REPORT_SHA = "6551861db1112c91b87c5705bbceb3bb26f55f0d7e70029a74d828519425145e"
SOURCE_REPORT_DEFAULT = Path("/tmp/mini-moonboard-remaining-single-shear-reference-2026-10-01.json")
REPORT_DEFAULT = Path("/tmp/mini-moonboard-bottom-outer-joint-2026-10-01.json")
FREEZE = PACKETS / "upper-frame-joint-review-2026-09-30/freeze.json"
FREEZE_SHA = "d4ba1c78eb358d25e32819201e9c59e05d425a06d9e4e5cca3dc09d7139ffd73"
GRAPH_DIR = PACKETS / "evaluation-resume-2026-09-24/current-geometric-interface-map-attempt02-2026-09-28"
GRAPH = GRAPH_DIR / "complete-contact-graph.json"
GRAPH_SHA = "7806242ac48b198becf5db97b16b6a5605021b8d86b964f0f02adb6806aeec26"
GRAPH_VERIFIER = GRAPH_DIR / "verify_packet.py"
GRAPH_VERIFIER_SHA = "f839cfe233155bcd5ab56fea943cc2a13d211053d4876e98f4cb48dfdb3c3e43"
ATLAS = PACKETS / "evaluation-resume-2026-09-24/current-geometric-interface-face-atlas-attempt01-2026-09-28/face-pair-atlas.json"
ATLAS_SHA = "d455b374b238039a509bc9254fd7ea36cfbf6078af52468fbe20b31ec72e3ee9"
MATERIALS = PACKETS / "hardware-material-specification-2026-09-30/material-inputs.json"
MATERIALS_SHA = "0f33ad8fd517673a4ebbed36c4a30c1cfe07e0d8163165bdc804af91d958fc5a"
BALANCE_SOURCE = PACKETS / "mvp-acceleration-2026-09-28/current-corner-native-demand-export-attempt03/produce.py"
BALANCE_SOURCE_SHA = "0e6aa1b0ec50e3137d2f431f79365de899d109a5d5c61d37de344c9596681fe8"
CLEAT = "bottom_outer_left_cleat"
SIDE = "base_side_left"
RAIL = "base_rail_bottom_left"
PAIR_PATCH = {(RAIL, CLEAT): 58, (SIDE, CLEAT): 88, (RAIL, SIDE): 56}
AXES = {f"bottom_outer/clip_horizontal_bottom_left_1/{role}_{i}"
        for role in ("rail", "side") for i in (1, 2)}
FACTORS = (0.1, 0.2, 0.3, 0.45, 0.675, 0.925, 1.0)
PSI_TO_MPA = 0.006894757293168361

# These are the source pins embedded in the frozen producer, repeated here so
# the verifier checks the report's source registry independently of its code.
SOURCE_PINS = {
    "previous_producer": ("docs/wood-joints-mvp/hypotheses/remaining-single-shear-reference-2026-10-01/produce.py",
                          "5f2a7fdca2ef0c56c661fa10e4122189f8a7a1ae0725062cb8c56d95dd911edf"),
    "contact_graph": (GRAPH.relative_to(ROOT).as_posix(), GRAPH_SHA),
    "contact_graph_pins": ((GRAPH_DIR / "source-pins.json").relative_to(ROOT).as_posix(),
                            "590112932d73dc57da015382a8ebf6e0fc85a8c5e8338549f381b8bd7732ba5c"),
    "contact_graph_verifier": (GRAPH_VERIFIER.relative_to(ROOT).as_posix(), GRAPH_VERIFIER_SHA),
    "face_atlas": (ATLAS.relative_to(ROOT).as_posix(), ATLAS_SHA),
    "material_inputs": (MATERIALS.relative_to(ROOT).as_posix(), MATERIALS_SHA),
    "balance_method": (BALANCE_SOURCE.relative_to(ROOT).as_posix(), BALANCE_SOURCE_SHA),
    "remaining_demand_producer": ("docs/wood-joints-mvp/hypotheses/remaining-candidate-washer-demands-2026-10-01/produce.py",
                                   "0c58a7dc6c82ccc2624ee9d3355e2840f738be01961ddaf3f64486700e89e6c9"),
    "right_plane_checker": ("docs/wood-joints-mvp/hypotheses/right-corner-signed-load-path-2026-10-01/produce.py",
                            "13989f42845210caadb15c1cf3903a47c2634b866195dc0c5f2156ea9605f2ea"),
    "frame_grain_map": ("docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-frame-timber-material-frame-map-attempt01/current-frame-timber-material-frame-map.json",
                        "f867b4926ed23c9f356005c134778e138c8b1230547f0b69be7c3f9bc2a42409"),
    "block_grain_map": ("docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-block-material-frame-map-attempt02/material-frame-map.json",
                        "8705b8f100a2d3355c236fc19e6798bb7ad4862ba2d51826cf63a88db1285480"),
    "single_bolt_method": ("docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/nds-screen/produce.py",
                           "21d3b2b254b1ceb9a6cf777b98eb492b52f989cc019afa2209b92be3e4a3cdb0"),
    "single_bolt_scenarios": ("docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/nds-screen/single-bolt-scenarios.json",
                              "130041246af11fc8e3568a7091f585d0d75581b2e1fbb3a3f4b97b750d68a7ea"),
    "single_shear_helper": ("fea/dowel_yield.py",
                            "d6c318e75c1a720d0b91f810a892e8309ef89735f66f48820ee853b753f8fe45"),
    "dowel_bearing_helper": ("mini_moonboard/bolted_timber_checks.py",
                              "a1414547d9eaa3d60e81482b4a2cac2d49e88f31aafa341dca5be9ec8ef4aa13"),
}


def require(ok: bool, message: str) -> None:
    if not ok:
        raise ValueError(message)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def close(a: float, b: float, *, atol: float = 1e-8, rtol: float = 1e-10) -> bool:
    return math.isfinite(float(a)) and math.isfinite(float(b)) and math.isclose(
        float(a), float(b), rel_tol=rtol, abs_tol=atol)


def vector(values, label: str) -> list[float]:
    require(len(values) == 3 and all(math.isfinite(float(v)) for v in values),
            f"invalid vector: {label}")
    return [float(v) for v in values]


def finite_list(values, length: int, label: str) -> list[float]:
    require(len(values) == length and all(math.isfinite(float(v)) for v in values),
            f"invalid numeric list: {label}")
    return [float(v) for v in values]


def check_vector(actual, expected, label: str, atol: float = 1e-8) -> None:
    a, b = vector(actual, label), vector(expected, label)
    require(all(close(x, y, atol=atol) for x, y in zip(a, b, strict=True)), label)


def add(a, b):
    return [x + y for x, y in zip(a, b, strict=True)]


def scale(s, a):
    return [s * x for x in a]


def dot(a, b):
    return math.fsum(x * y for x, y in zip(a, b, strict=True))


def unit(a):
    n = math.sqrt(dot(a, a))
    require(n > 0 and math.isfinite(n), "zero/nonfinite direction")
    return [x / n for x in a]


def cross(a, b):
    return [a[1]*b[2] - a[2]*b[1],
            a[2]*b[0] - a[0]*b[2],
            a[0]*b[1] - a[1]*b[0]]


def moment(point, force, datum):
    return cross([p-d for p, d in zip(point, datum, strict=True)], force)


def moment_radius(point, radius, datum):
    r = [p-d for p, d in zip(point, datum, strict=True)]
    return [abs(r[1])*radius[2] + abs(r[2])*radius[1],
            abs(r[2])*radius[0] + abs(r[0])*radius[2],
            abs(r[0])*radius[1] + abs(r[1])*radius[0]]


def self_test() -> None:
    # Known-answer fixtures exercise the same wrench and interval arithmetic
    # used below for the 21 source states.
    require(moment([3, 4, 5], [7, -2, 9], [1, 1, 1]) == [35, 10, -25],
            "known-answer moment fixture failed")
    require(moment_radius([3, 4, 5], [5, 7, 11], [1, 1, 1]) == [61, 42, 29],
            "known-answer moment-radius fixture failed")
    f, datum_a, datum_b = [7, -2, 9], [1, 1, 1], [-2, 3, 0]
    m_a = moment([3, 4, 5], f, datum_a)
    shift = cross([b-a for a, b in zip(datum_a, datum_b, strict=True)], f)
    check_vector(moment([3, 4, 5], f, datum_b), [x-y for x, y in zip(m_a, shift, strict=True)],
                 "known-answer wrench transport fixture failed")


def load_json(path: Path):
    return json.loads(path.read_text())


def imported_graph_check():
    require(sha(GRAPH_VERIFIER) == GRAPH_VERIFIER_SHA, "graph verifier pin changed")
    spec = importlib.util.spec_from_file_location("independent_bottom_graph_check", GRAPH_VERIFIER)
    require(spec is not None and spec.loader is not None, "graph verifier unavailable")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    result = module.verify(ROOT)
    require(result.get("result") == "PASS", "finished graph/source verification failed")
    return result


def check_source_pins(report):
    require(report["source_pins"] == {
        name: {"path": path, "sha256": digest}
        for name, (path, digest) in SOURCE_PINS.items()}, "output source registry differs from pinned sources")
    for path, digest in SOURCE_PINS.values():
        require(sha(ROOT / path) == digest, f"source pin changed: {path}")
    require(sha(FREEZE) == FREEZE_SHA, "case freeze changed")
    require(sha(GRAPH) == GRAPH_SHA and sha(ATLAS) == ATLAS_SHA and sha(MATERIALS) == MATERIALS_SHA,
            "geometry/material source pin changed")


def check_geometry(report):
    graph = load_json(GRAPH)
    atlas = load_json(ATLAS)
    require(graph["revision_id"] == atlas["revision_id"] == report["geometry_revision_id"],
            "geometry revision mismatch")
    edges = {tuple(row["member_ids"]): row for row in graph["edges"]}
    faces = {tuple(row["member_ids"]): row for row in atlas["finite_opposed_interfaces"]}
    require(set(report["nominal_pair_geometry"]) == {"|".join(pair) for pair in PAIR_PATCH},
            "nominal pair coverage differs")
    areas = {}
    for pair in PAIR_PATCH:
        key = tuple(sorted(pair))
        edge, face = edges[key], faces[key]
        require(edge["geometry_state"] == "finite_opposed_planar_touch"
                and edge["common_volume_mm3"] == 0, f"pair is not a planar zero-volume touch: {pair}")
        require(abs(edge["finite_shared_planar_face_area_mm2"]
                    - face["reconstructed_opposed_area_mm2"]) < 1e-6,
                f"contact graph/atlas areas disagree: {pair}")
        saved = report["nominal_pair_geometry"]["|".join(pair)]
        require(saved["graph_edge"] == edge and saved["face_atlas"] == face,
                f"reported source face rows differ: {pair}")
        areas[pair] = float(edge["finite_shared_planar_face_area_mm2"])
    return areas


def check_model_source_files(report):
    freeze = load_json(FREEZE)
    require(report["case_sources"] == freeze["cases"], "frozen case file bindings differ")
    for case, files in freeze["cases"].items():
        for label, pin in files.items():
            path = ROOT / pin["path"]
            require(sha(path) == pin["sha256"], f"frozen {case}/{label} changed")
    return freeze


def source_inventory(model):
    rows = model["raw_source_carrier_law_inventory_rows"]
    ids = [r["group"] for r in rows]
    require(len(set(ids)) == len(ids), "duplicate raw source-row identity")
    return rows


def verify_source_component_row(model, response_inc, action, binding, role):
    source_id = binding["source_row_id"]
    require(action["role"] == role and action["source_row_ids"] == [source_id],
            f"wrong {role} action/source identity")
    index = binding["source_inventory_row_index"]
    inventory = source_inventory(model)
    row = inventory[index]
    require(row["group"] == source_id and row["name"] == binding["name"]
            and row["physical_owner"] == binding["physical_owner"],
            "native source inventory/binding differs")
    require(action["source_inventory_rows"] == [{
        "source_inventory_row_index": index,
        "source_row_id": source_id,
        "source_connection_name": binding["name"],
        "intended_law": row["intended_law"],
    }], "physical action inventory differs")
    component = {r["source_row_id"]: r for r in response_inc["springa_components"]}.get(source_id)
    require(component is not None and component["source_row_id"] == source_id
            and component["source_inventory_row_index"] == index
            and component["element"] == binding["source_element"], "native unilateral component differs")
    return row, component


def verify_bilateral_plane(model, inc, output, old, materials):
    action_name = old["lateral_plane_source_name"]
    action = inc["physical_connection_forces"][action_name]
    inventory = source_inventory(model)
    spring_by_id = {r["source_row_id"]: r for r in model["springs"]}
    native_by_id = {r["source_row_id"]: r for r in inc["retained_bilateral_spring2_components"]}
    ids = old["lateral_plane_source_row_ids"]
    require(len(ids) == 2 and action["source_row_ids"] == ids
            and len(set(ids)) == 2, "lateral plane source IDs differ")
    expected_receiver = RAIL if "/rail_" in old["axis_id"] else SIDE
    require(action["role"] == "candidate_bolt_lateral_plane"
            and action["axis_id"] == old["axis_id"]
            and {action["first"], action["second"]} == {CLEAT, expected_receiver},
            "lateral plane receiver/sign convention differs")
    force, radius, dofs = [0.0]*3, [0.0]*3, []
    for source_id, source_record in zip(ids, action["source_inventory_rows"], strict=True):
        spring, native = spring_by_id[source_id], native_by_id[source_id]
        row_index = spring["source_inventory_row_index"]
        source = inventory[row_index]
        require(source_record["source_inventory_row_index"] == row_index
                and source_record["source_row_id"] == source_id
                and source_record["source_connection_name"] == spring["name"]
                and source_record["intended_law"] == spring["intended_law"] == source["intended_law"] == "bilateral"
                and spring["group"] == source_id
                and source["group"] == source_id
                and spring["physical_owner"] == source["physical_owner"],
                "bilateral native source mapping/law differs")
        require(native["element"] == spring["element"] == source["element"]
                and native["source_group"] == source_id
                and native["rf_action_reaction_passed"] is True
                and native["rf_kdu_intervals_intersect"] is True,
                "native bilateral response gates differ")
        rf = finite_list(native["endpoint_rf_N"], 2, "bilateral endpoint RF")
        rf_radius = finite_list(native["endpoint_rf_radius_N"], 2, "bilateral RF radius")
        scalar = float(native["force_on_first_local_N"])
        scalar_radius = float(native["force_rounding_radius_local_N"])
        require(close(scalar, -rf[0]) and close(scalar, rf[1])
                and close(rf_radius[0], rf_radius[1]) and close(scalar_radius, rf_radius[0]),
                "native endpoint RF sign/radius differs")
        dof = spring["connector_local_dof"]
        require(dof == spring["dof"] == source["dof"] and dof in (2, 3),
                "unexpected lateral plane DOF")
        dofs.append(dof)
        direction = vector(action["force_basis"][dof - 1], "lateral source basis")
        force = add(force, scale(scalar, direction))
        radius = add(radius, scale(scalar_radius, [abs(x) for x in direction]))
    require(sorted(dofs) == [2, 3], "lateral force plane does not use its two transverse axes")
    check_vector(action["force_on_first_xyz_n"], force, "native lateral force reconstruction")
    check_vector(action["force_on_second_xyz_n"], scale(-1, force), "lateral equal/opposite force")
    check_vector(action["force_rounding_radius_xyz_n"], radius, "native lateral interval reconstruction")
    check_vector(action["point"], old["lateral_plane_point_xyz_mm"], "lateral action point")
    check_vector(output["actual_lateral_force_on_receiver_0_N"], force,
                 "old/native first-receiver signed force")
    check_vector(output["actual_lateral_force_on_receiver_1_N"], scale(-1, force),
                 "old/native second-receiver signed force")
    check_vector(output["actual_lateral_force_rounding_radius_N"], radius,
                 "old/native lateral rounding radius")
    magnitude = math.sqrt(dot(force, force))
    require(close(output["actual_lateral_resultant_N"], magnitude), "lateral resultant magnitude differs")
    for member, angle in output["actual_lateral_angle_to_grain_deg_by_receiver"].items():
        grain = next(row["source_proposed_longitudinal_grain_global_xyz"]
                     for row in materials["members"] if row["member_id"] == member)
        cosine = min(1.0, max(0.0, abs(dot(unit(force), unit(grain)))))
        require(close(angle, math.degrees(math.acos(cosine)), atol=1e-6),
                f"lateral/grain angle differs for {member}")
    # The historical reference row is copied intact; check the appended ratio
    # remains a simple demand/reference quotient, not an adopted capacity.
    for scenario in output["single_shear_reference_assignments"]["scenarios"]:
        require(close(scenario["actual_resultant_to_governing_reference"],
                      magnitude / scenario["governing_unadjusted_reference_N"]),
                "single-shear reference ratio differs")
    return action


def verify_unilateral_action(model, inc, name):
    bindings = {b["name"]: b for b in model["unilateral_springa_bindings"]}
    binding = bindings[name]
    action = inc["physical_connection_forces"][name]
    row, comp = verify_source_component_row(model, inc, action, binding,
                                             "physical_bolt_outer_seat_tension" if name.endswith("outer-seat-axial-tie")
                                             else "timber_or_panel_contact")
    owner = binding["physical_owner"]
    require(row["physical_owner"] == owner and action["first"] == owner["first"]
            and action["second"] == owner["second"], f"unilateral owner differs: {name}")
    force = float(comp["native_endpoint_internal_force_N"])
    force_radius = float(comp["native_endpoint_internal_radius_N"])
    require(math.isfinite(force) and force >= 0 and math.isfinite(force_radius) and force_radius >= 0,
            f"invalid unilateral native force/radius: {name}")
    n = unit(vector(action["scalar_normal"], "unilateral scalar normal"))
    require(close(dot(n, n), 1.0, atol=1e-12), "nonunit unilateral axis")
    check_vector(action["force_on_first_xyz_n"], scale(force, n), f"native unilateral force: {name}")
    check_vector(action["force_on_second_xyz_n"], scale(-force, n), f"unilateral action/reaction: {name}")
    check_vector(action["force_rounding_radius_xyz_n"],
                 scale(force_radius, [abs(x) for x in n]), f"native unilateral interval: {name}")
    require(comp["native_endpoint_action_reaction_passed"] is True
            and comp["numerical_ground_rf_excluded_from_physical_balance"] is True
            and comp["inside_table_domain_including_rounding"] is True
            and comp["table_force_interval_intersects_native_rf"] is True,
            f"unilateral native/source-law gate failed: {name}")
    table = comp["native_table_force_interval_N"]
    require(len(table) == 2 and all(math.isfinite(float(v)) for v in table)
            and 0 <= table[0] <= table[1]
            and table[0] <= force + force_radius and force - force_radius <= table[1],
            f"unilateral source/native force intervals do not overlap: {name}")
    q = float(comp["q_relative_projection_mm"])
    qr = float(comp["q_relative_projection_radius_mm"])
    require(math.isfinite(q) and math.isfinite(qr) and qr >= 0, f"invalid unilateral q interval: {name}")
    return action, binding, comp, force, force_radius, q, qr


def verify_tie(model, inc, old, bolt_output):
    name = old["axis_id"] + "/outer-seat-axial-tie"
    action, binding, _comp, force, _force_radius, _q, _qr = verify_unilateral_action(model, inc, name)
    source = source_inventory(model)[binding["source_inventory_row_index"]]
    require(binding["force_law"] == "k * max(q_mm, 0)"
            and source["intended_law"] == "tension_only"
            and binding["physical_owner"]["axis_id"] == old["axis_id"]
            and binding["physical_owner"]["role"] == "physical_bolt_outer_seat_tension",
            "outer-seat tension tie law/owner differs")
    require(old["same_state_tie_source_row_ids"] == [binding["source_row_id"]]
            and close(old["same_state_signed_outer_tie_N_once"], force)
            and bolt_output["same_state_signed_outer_tie_N_once"] == old["same_state_signed_outer_tie_N_once"],
            "outer-seat tie is not the same-state signed axial force")
    return action


def verify_contact(model, inc, name, expected_pair, material_by_member):
    action, binding, comp, force, radius, q, qr = verify_unilateral_action(model, inc, name)
    source = source_inventory(model)[binding["source_inventory_row_index"]]
    require(binding["force_law"] == "k * max(q_mm, 0)"
            and source["intended_law"] == "compression_only"
            and binding["physical_owner"]["role"] == "timber_or_panel_contact"
            and [action["first"], action["second"]] == list(expected_pair),
            f"wrong compression-only contact source/receivers: {name}")
    owner = binding["physical_owner"]
    area = float(owner["source_area_mm2"])
    require(math.isfinite(area) and area > 0 and close(area, action["source_area_mm2"]),
            f"invalid contact area: {name}")
    check_vector(action["point"], owner["point"], f"contact source point: {name}")
    check_vector(action["scalar_normal"], owner["scalar_normal"], f"contact source normal: {name}")
    require(comp["intended_source_law"] == "compression_only"
            and comp["native_endpoint_internal_force_N"] == force
            and comp["native_endpoint_internal_radius_N"] == radius,
            f"wrong compression source law/force: {name}")
    if force - radius > 0:
        state = "active_resolved"
        require(q - qr >= 0, f"resolved compressive native force has an open q interval: {name}")
    elif force == 0 and q + qr < 0 and max(abs(x) for x in comp["native_table_force_interval_N"]) == 0:
        state = "open_resolved"
    else:
        state = "ambiguous_at_rounded_boundary"
    pressure = force / area
    pressure_interval = [max(0.0, force-radius)/area, (force+radius)/area]
    dot_class = {}
    for member in expected_pair:
        grain = unit(material_by_member[member]["source_proposed_longitudinal_grain_global_xyz"])
        alignment = abs(dot(unit(action["scalar_normal"]), grain))
        classification = ("perpendicular" if alignment <= 1e-6 else
                           "parallel" if alignment >= 1-1e-6 else "oblique")
        perpendicular = classification == "perpendicular"
        applicable = perpendicular and state == "active_resolved"
        context = inc["_report_context_by_name"][name][member]
        require(context["normal_to_proposed_grain"] == classification
                and close(context["absolute_normal_grain_dot"], alignment, atol=1e-10),
                f"contact/grain orientation differs: {name}/{member}")
        require(context["unadjusted_Fc_perpendicular_psi"] == (625.0 if perpendicular else None)
                and context["compression_reference_comparison_applicable"] is applicable
                and context["cell_average_to_unadjusted_Fc_perpendicular_ratio"] ==
                    (pressure / (625.0 * PSI_TO_MPA) if applicable else None),
                f"conditional Fc reference context differs: {name}/{member}")
        exclusion = ("different_grain_direction_requires_separate_applicable_method" if not perpendicular
                     else "source_cell_not_resolved_compressive" if not applicable else None)
        require(context["reference_exclusion"] == exclusion
                and context["fully_adjusted_ratio"] is False
                and context["bearing_accepted"] is False,
                f"conditional Fc exclusion/claim boundary differs: {name}/{member}")
        dot_class[member] = classification
    return {
        "name": name, "source_row_id": binding["source_row_id"], "area_mm2": area,
        "point_xyz_mm": action["point"], "normal_xyz": unit(action["scalar_normal"]),
        "native_compression_force_N": force, "native_force_radius_N": radius,
        "source_q_mm": q, "source_q_radius_mm": qr, "contact_state": state,
        "modeled_cell_average_pressure_MPa": pressure,
        "compression_average_pressure_interval_MPa": pressure_interval,
        "normal_to_grain": dot_class,
    }


def compare_load_wrench(model, datum):
    loads = model["physical_body_loads"][CLEAT]
    require(len(loads) == 20, "physical cleat body-load node count changed")
    node_xyz = model["nodes"]
    f, m_datum, m_origin = [0.0]*3, [0.0]*3, [0.0]*3
    for node_id, values in loads.items():
        force = vector(values, "physical cleat body load")
        point = vector(node_xyz[str(node_id)], "physical load node coordinate")
        f = add(f, force)
        m_datum = add(m_datum, cross([p-d for p, d in zip(point, datum, strict=True)], force))
        m_origin = add(m_origin, cross(point, force))
    stored = model["physical_body_wrenches"][CLEAT]
    check_vector(stored["force_xyz_n"], f, "source physical body-load resultant")
    check_vector(stored["moment_about_global_origin_xyz_nmm"], m_origin,
                 "source physical body-load moment about origin", atol=1e-6)
    return f, m_datum


def verify_joint_balance(report_state, model, response_inc, audit_inc, load_factor, datum):
    boundary = report_state["cleat_complete_boundary_actions"]
    body_inventory = source_inventory(model)
    names_from_inventory = {r["name"] for r in body_inventory
                            if CLEAT in (r["physical_owner"]["first"], r["physical_owner"]["second"])}
    axes_names = {axis + "/outer-seat-axial-tie" for axis in AXES}
    plane_names = {r["lateral_plane_source_name"] for r in report_state["bolt_reference_rows"]}
    contact_names = {f"contact_{patch}_{i}" for patch in (58, 88) for i in range(4)}
    expected = axes_names | plane_names | contact_names
    require(len(expected) == 16 and names_from_inventory == expected
            and set(boundary) == expected, "cleat's 16-source interface boundary is incomplete/overinclusive")
    force_sum, moment_sum = [0.0]*3, [0.0]*3
    force_radius_sum, moment_radius_sum = [0.0]*3, [0.0]*3
    for name in sorted(expected):
        action = boundary[name]
        native_action = response_inc["physical_connection_forces"][name]
        require(action == native_action, f"reported interface action differs from native response: {name}")
        first, second = action["first"], action["second"]
        require((first == CLEAT) ^ (second == CLEAT), f"interface action is not a cleat boundary: {name}")
        side = "first" if first == CLEAT else "second"
        point = action.get(side + "_point", action["point"])
        f_side = vector(action["force_on_" + side + "_xyz_n"], "cleat boundary force")
        rho = vector(action["force_rounding_radius_xyz_n"], "cleat boundary force radius")
        force_sum = add(force_sum, f_side)
        moment_sum = add(moment_sum, moment(point, f_side, datum))
        force_radius_sum = add(force_radius_sum, rho)
        moment_radius_sum = add(moment_radius_sum, moment_radius(point, rho, datum))
    f0, m0 = compare_load_wrench(model, datum)
    external_force, external_moment = scale(load_factor, f0), scale(load_factor, m0)
    total_force = add(external_force, force_sum)
    total_moment = add(external_moment, moment_sum)
    balance = report_state["cleat_source_balance"]
    check_vector(balance["datum_global_xyz_mm"], datum, "cleat balance datum")
    check_vector(balance["external_load_wrench"]["force_xyz_n"], external_force,
                 "reported external source-body resultant")
    check_vector(balance["external_load_wrench"]["moment_xyz_nmm"], external_moment,
                 "reported external source-body moment", atol=1e-6)
    check_vector(balance["interface_action_wrench"]["force_xyz_n"], force_sum,
                 "reported cleat interface resultant")
    check_vector(balance["interface_action_wrench"]["moment_xyz_nmm"], moment_sum,
                 "reported cleat interface moment", atol=1e-6)
    check_vector(balance["combined_residual_wrench"]["force_xyz_n"], total_force,
                 "independent cleat residual force")
    check_vector(balance["combined_residual_wrench"]["moment_xyz_nmm"], total_moment,
                 "independent cleat residual moment", atol=1e-6)
    check_vector(audit_inc["reference_xyz_mm"], datum, "all-body audit datum")
    check_vector(audit_inc["force_residual_xyz_n"], total_force,
                 "source all-body force residual", atol=1e-7)
    check_vector(audit_inc["moment_residual_xyz_nmm"], total_moment,
                 "source all-body moment residual", atol=1e-6)
    check_vector(audit_inc["force_rounding_radius_xyz_n"], force_radius_sum,
                 "all-body versus interface force rounding radius", atol=1e-10)
    check_vector(audit_inc["moment_rounding_radius_xyz_nmm"], moment_radius_sum,
                 "all-body versus interface moment rounding radius", atol=1e-9)
    interval_force_excess = [max(0.0, abs(x)-r) for x, r in zip(total_force, force_radius_sum, strict=True)]
    interval_moment_excess = [max(0.0, abs(x)-r) for x, r in zip(total_moment, moment_radius_sum, strict=True)]
    check_vector(balance["rounding_interval_excess_force_xyz_n"], interval_force_excess,
                 "cleat force interval excess")
    check_vector(balance["rounding_interval_excess_moment_xyz_nmm"], interval_moment_excess,
                 "cleat moment interval excess")
    force_gate = all(abs(x) <= 0.1 for x in total_force)
    moment_gate = all(abs(x) <= 2.0 for x in total_moment)
    interval_gate = (all(x <= 0.1 for x in interval_force_excess)
                     and all(x <= 2.0 for x in interval_moment_excess))
    require(balance["raw_balance_passed"] is (force_gate and moment_gate)
            and balance["rounding_interval_balance_passed"] is interval_gate
            and audit_inc["printed_resultants_passed"] is (force_gate and moment_gate)
            and audit_inc["interval_resultants_passed"] is interval_gate,
            "cleat raw/interval source thresholds or reported result differ")
    return total_force, total_moment, force_radius_sum, moment_radius_sum


def verify(report_path: Path, source_report_path: Path):
    self_test()
    require(sha(PRODUCER) == PRODUCER_SHA, "producer changed from reviewed freeze")
    require(sha(report_path) == REPORT_SHA, "bottom-outer report changed from reviewed freeze")
    require(sha(source_report_path) == SOURCE_REPORT_SHA, "52-axis source report changed")
    report, source_report = load_json(report_path), load_json(source_report_path)
    require(report["schema"] == "bottom_outer_joint_disposition/v1"
            and report["producer_sha256"] == PRODUCER_SHA
            and report["source_report_sha256"] == SOURCE_REPORT_SHA,
            "bottom-outer output identity differs")
    require(report["claim_limits"] == {
        "joint_accepted": False, "adopted_capacity": False, "fully_adjusted_ratios": False,
        "actual_pressure_peak_established": False, "physical_contact_or_stiffness_qualified": False,
        "complete_host_member_boundary_or_finished_section": False, "native_solve": False,
        "geometry_changed": False, "criterion_pass": False,
    }, "output claim boundary changed")
    check_source_pins(report)
    freeze = check_model_source_files(report)
    graph_verification = imported_graph_check()
    areas = check_geometry(report)
    materials = load_json(MATERIALS)
    require(materials["candidate"] == report["candidate"]
            and materials["geometry_revision"] == report["geometry_revision_id"]
            and materials["conditional_DF_L_No2_base_row"]["base_properties"]["Fc_perpendicular"] == 625,
            "conditional material reference/candidate differs")
    for source in materials["source_pins"]:
        require(sha(ROOT / source["path"]) == source["sha256"], "material source row changed")
    material_by_member = {row["member_id"]: row for row in materials["members"]}
    old_rows = {(r["case_id"], r["increment_index"], r["axis_id"]): r
                for r in source_report["state_rows"] if r["axis_id"] in AXES}
    require(source_report["producer_sha256"] == SOURCE_PINS["previous_producer"][1]
            and len(old_rows) == 84, "prior four-axis reference source differs")
    states = report["joint_states"]
    require(len(states) == 21 and report["counts"] == {
        "joint_states": 21, "bolt_reference_rows": 84, "contact_cell_states": 252,
        "contact_pair_states": 63, "complete_cleat_balance_states": 21,
    }, "21-state report counts differ")
    require(set(report["case_sources"]) == set(freeze["cases"]), "source case cohort differs")
    expected_states = {(case, i, factor) for case in freeze["cases"]
                       for i, factor in enumerate(FACTORS)}
    got_states = {(r["case_id"], r["increment_index"], r["load_factor"]) for r in states}
    require(got_states == expected_states, "case/increment state coverage differs")
    cell_by_key = {(r["case_id"], r["increment_index"], r["name"]): r
                   for r in report["contact_cell_states"]}
    pair_by_key = {(tuple(r["member_pair"]), r["case_id"], r["increment_index"]): r
                   for r in report["contact_pair_states"]}
    require(len(cell_by_key) == 252 and len(pair_by_key) == 63, "duplicate/missing contact rows")
    activity = {"active_resolved": 0, "open_resolved": 0, "ambiguous_at_rounded_boundary": 0}
    max_force_residual = max_moment_residual = max_force_interval_excess = max_moment_interval_excess = 0.0
    native_checked = 0
    pair_names = {pair: [f"contact_{patch}_{i}" for i in range(4)]
                  for pair, patch in PAIR_PATCH.items()}
    for case, files in freeze["cases"].items():
        model = load_json(ROOT / files["model"]["path"])
        response = load_json(ROOT / files["response"]["path"])
        audit = load_json(ROOT / files["all_body_audit"]["path"])
        require(model["candidate"] == response["candidate"] == report["candidate"]
                and model["geometry_revision_id"] == response["geometry_revision_id"] == report["geometry_revision_id"]
                and model["case_id"] == response["case_id"] == case
                and tuple(row["load_factor"] for row in response["increments"]) == FACTORS
                and tuple(row["load_factor"] for row in audit["increments"]) == FACTORS,
                f"frozen model/response identity differs: {case}")
        require(audit["source_model_sha256"] == files["model"]["sha256"]
                and audit["source_response_sha256"] == files["response"]["sha256"]
                and audit["physical_tolerances_N_Nmm"] == [0.1, 2.0],
                f"all-body audit provenance/gates differ: {case}")
        source_inventory(model)
        bindings = {b["name"]: b for b in model["unilateral_springa_bindings"]}
        require(len(bindings) == len(model["unilateral_springa_bindings"]), "duplicate unilateral binding")
        contacts = {row["name"]: row for row in model["contact_cell_ownership"]
                    if (row["first"], row["second"]) in PAIR_PATCH}
        require(set(contacts) == {name for names in pair_names.values() for name in names},
                "source contact ownership coverage differs")
        geometry_record = model["body_geometry"][CLEAT]["geometry_record"]
        datum = [(a+b)/2 for a, b in zip(geometry_record["start"], geometry_record["end"], strict=True)]
        for member in (CLEAT, SIDE, RAIL):
            grain_record = model["body_geometry"][member]["geometry_record"]["source_descriptor"]["grain_global_xyz"]
            proposed = material_by_member[member]["source_proposed_longitudinal_grain_global_xyz"]
            require(abs(abs(dot(unit(grain_record), unit(proposed))) - 1) < 1e-8,
                    f"proposed/material grain axis mismatch: {member}")
        for index, inc in enumerate(response["increments"]):
            report_state = next(s for s in states if s["case_id"] == case and s["increment_index"] == index)
            require(report_state["load_factor"] == inc["load_factor"]
                    and all(inc[g] is True for g in (
                        "mpc_interval_checks_passed", "retained_bilateral_checks_passed",
                        "springa_law_checks_passed", "selected_floor_complementarity_passed",
                        "inactive_floor_tangent_no_restraint_or_reaction_passed", "raw_balance_passed",
                        "rounding_interval_balance_passed")),
                    "native response gate or state factor differs")
            # Stash only the joined contexts for the formula checker; native input remains read-only.
            inc["_report_context_by_name"] = {
                row["name"]: row["grain_reference_context"] for row in report["contact_cell_states"]
                if row["case_id"] == case and row["increment_index"] == index}
            for pair, names in pair_names.items():
                cell_rows = []
                for name in names:
                    row = cell_by_key[(case, index, name)]
                    cell = verify_contact(model, inc, name, pair, material_by_member)
                    for field in ("name", "source_row_id", "area_mm2", "point_xyz_mm", "normal_xyz",
                                  "native_compression_force_N", "native_force_radius_N", "source_q_mm",
                                  "source_q_radius_mm", "contact_state", "modeled_cell_average_pressure_MPa",
                                  "compression_average_pressure_interval_MPa"):
                        actual, expected = row[field], cell[field]
                        if isinstance(actual, list):
                            require(len(actual) == len(expected)
                                    and all(close(a, b, atol=1e-10)
                                            for a, b in zip(actual, expected, strict=True)),
                                    f"contact output formula {name}/{field}")
                        elif isinstance(actual, (int, float)):
                            require(close(actual, expected, atol=1e-10), f"contact output formula {name}/{field}")
                        else:
                            require(actual == expected, f"contact output formula {name}/{field}")
                    activity[cell["contact_state"]] += 1
                    cell_rows.append(cell)
                    native_action = inc["physical_connection_forces"][name]
                    require(native_action["source_row_ids"] == [row["source_row_id"]],
                            f"output cell source identity differs: {name}")
                    native_checked += 1
                area_sum = math.fsum(c["area_mm2"] for c in cell_rows)
                force_sum = math.fsum(c["native_compression_force_N"] for c in cell_rows)
                pair_state = pair_by_key[(pair, case, index)]
                require(pair_state["source_cell_names"] == names
                        and close(pair_state["finished_shared_area_mm2"], areas[pair], atol=1e-6)
                        and close(pair_state["modeled_cell_area_sum_mm2"], area_sum, atol=1e-8)
                        and close(pair_state["finished_shared_area_mm2"], area_sum, atol=1e-6)
                        and close(pair_state["total_native_compression_force_N"], force_sum, atol=1e-8)
                        and pair_state["joint_accepted"] is False,
                        f"contact pair aggregate differs: {case}/{index}/{pair}")
            report_bolts = {(r["case_id"], r["increment_index"], r["axis_id"]): r
                            for r in report_state["bolt_reference_rows"]}
            require(set(report_bolts) == {(case, index, axis) for axis in AXES}, "four bolt rows missing")
            for axis in AXES:
                key = (case, index, axis)
                old = old_rows[key]
                output = report_bolts[key]
                require(output == old and output["joint_accepted"] is False,
                        f"prior same-state single-shear reference was altered: {key}")
                plane = verify_bilateral_plane(model, inc, output, old, materials)
                tie = verify_tie(model, inc, old, output)
                require(plane["axis_id"] == tie["axis_id"] == axis,
                        f"lateral plane/tie axis binding differs: {axis}")
                native_checked += 3
            independent = verify_joint_balance(
                report_state, model, inc, audit["increments"][index]["body_equilibrium"][CLEAT],
                                               inc["load_factor"], datum)
            native_force_residual = independent[0]
            native_moment_residual = independent[1]
            max_force_residual = max(max_force_residual, *(abs(x) for x in native_force_residual))
            max_moment_residual = max(max_moment_residual, *(abs(x) for x in native_moment_residual))
            max_force_interval_excess = max(max_force_interval_excess,
                                            *(max(0.0, abs(x)-r) for x, r in zip(native_force_residual, independent[2], strict=True)))
            max_moment_interval_excess = max(max_moment_interval_excess,
                                             *(max(0.0, abs(x)-r) for x, r in zip(native_moment_residual, independent[3], strict=True)))
            require(report_state["joint_accepted"] is False, "joint acceptance flag changed")
    require(sum(activity.values()) == 252 and native_checked == 252 + 84*3,
            "independent native/source coverage differs")
    return {
        "result": "PASS_INDEPENDENT_SOURCE_JOIN_AND_NUMERIC_ORACLE",
        "producer_sha256": sha(PRODUCER), "report_sha256": sha(report_path),
        "source_report_sha256": sha(source_report_path), "freeze_sha256": sha(FREEZE),
        "counts": {"states": len(states), "bolt_rows": 84, "contact_cells": 252,
                   "contact_pairs": 63, "cleat_boundary_actions_per_state": 16,
                   "native_unilateral_or_plane_force_checks": native_checked},
        "contact_activity": activity,
        "maximum_componentwise_cleat_residual_force_N": max_force_residual,
        "maximum_componentwise_cleat_residual_moment_Nmm": max_moment_residual,
        "maximum_rounding_interval_excess_force_N": max_force_interval_excess,
        "maximum_rounding_interval_excess_moment_Nmm": max_moment_interval_excess,
        "geometry_check": graph_verification.get("result"),
        "interpretation": "source-bound geometry and arithmetic only; no capacity or joint acceptance",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", type=Path, default=REPORT_DEFAULT)
    parser.add_argument("--source-report", type=Path, default=SOURCE_REPORT_DEFAULT)
    args = parser.parse_args()
    print(json.dumps(verify(args.report, args.source_report), indent=2, allow_nan=False))


if __name__ == "__main__":
    main()
