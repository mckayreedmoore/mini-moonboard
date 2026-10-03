"""Parent-run finite opening-section comparisons from fresh knee-bridge actions.

Only build(output) executes arithmetic. Historical producers supply pure
geometry/rectangle helpers; their build/run/main/coupon APIs are never called.
"""

from __future__ import annotations

import gzip
import hashlib
import importlib.util
import json
import platform
import sys
from functools import cache
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
BASE = HERE.parent
RAW = HERE / "rawlocal/knee-bridge-remaining-sections"
FRESH = BASE / "member-screen-attempt02/knee-bridge-gravity01"
GRAVITY = HERE / "rawlocal/knee-bridge-gravity/attempt01"
FRAME = HERE / "rawlocal/knee-bridge-frame/attempt02/response"
CONTRACT = HERE / "rawlocal/header-local-transfer/attempt01"
FEATURES = BASE.parent / "current-finished-feature-register-2026-10-01/surfaces.json"
MATERIAL = BASE.parent / "hardware-material-specification-2026-09-30/material-inputs.json"
ORIGINAL_MATERIAL_RECIPES = BASE / "member-screen-attempt02/four-screw-layout01/member-results.json"
CASES = ("a12-rear", "a12-forward", "a12-left", "k12-right", "k12-rear", "a1-rear")
DEAD_FACTOR = 1.1110134616260479
TOL = 1e-6
METRICS = (
    "normal_reference_sum", "total_tension_over_Ft", "total_compression_over_Fc",
    "absolute_bending_over_Fb", "same_state_shear_bound_over_Fv",
    "transverse_shear_over_Fv", "torsional_shear_over_Fv",
)
PINS = {
    FRESH / "member-results.json": "5178d1a246aa04044429c1c2bc81709214ae9abd713313d07a949a2848de3dd0",
    FRESH / "action-section-arrays.npz": "3be032470253e872690637b09566076256374071adfe7d057ed4d329debef596",
    FRESH / "geometry.json": "c61139087fac34e8094f2336f15dd6de5c0112d26d37b9535526f47332f453af",
    FRESH / "inputs.json": "34219c91e8b23588f76f4e2e2b6c564b25e1b979ccd4106dd0002c9f03cc0457",
    FRAME / "comparison.json": "c3a8ff024fb494032d947aedfd6f00cda8698587b8751b2cec66e4b3af243729",
    FRAME / "response.npz": "62bd4116cfb577a0846f4de0d43fbeec6bb704bac7feee530ee673ded1820f90",
    GRAVITY / "operator-assessment.json": "ce69ba58e3c6265d31ab0dfdec1ffac4c019b93fc1106c8f9677ed9b5b2c3f95",
    CONTRACT / "model.json": "eae4fc005cdd079f90f527be611e45a137aa275b129e16eebf964c422d69ae52",
    CONTRACT / "inputs.json": "cccd8969132c30e996fe5d3509069dbe851720786cec92a46a064cc0f7c0758b",
    CONTRACT / "receipt.json": "3b3afc6924dee426c4f0073077e119d906efddcb5ed03a683ec4a3f16fc189a8",
    FEATURES: "33fff67eee4bc4e96ccef5703f6eebd0d4e004541c6114a4b1da4a5332b2f6eb",
    MATERIAL: "0f33ad8fd517673a4ebbed36c4a30c1cfe07e0d8163165bdc804af91d958fc5a",
    ORIGINAL_MATERIAL_RECIPES: "54f3888581717d2579b0dd6ea7dcd754501ec2890a9f4869059f476f2d0965c5",
    HERE / "header-cleat-net-sections.py": "3e680b2ac439c9c0be1c958dfff730725f3b8da07c1c7c38ab1b8a30d7178d6d",
    HERE / "remaining-net-sections.py": "acd60cee627331fdfeb06eb02321221f09a666bcea7e3997a9e51e616c98c129",
    HERE / "header-net-section.py": "d413a2ae912df6bf56086ad6ddda59526db32cc6325f1b4bf2b71f984d86a328",
    HERE / "corner-net-section.py": "8a60447291161300ec4ee4f4f89c783cdcb565ee771e972c524ffd10f006d0e5",
    HERE / "corner-timber-sections.py": "d0e2c5cb94b056cab71072fcab52cc7be8760fb7d32368c097a45050b3493633",
    BASE / "member_stability.py": "eb70dbe72c1ed3b9518739915193083fd6a07ebd064ba17d0c07f299f6786b72",
}
FLAGS = {
    "formal_qualification": False, "new_resistance_established": False,
    "complete_joint_acceptance": False, "physical_release": False,
    "proposal_adopted": False, "authority_changed": False,
    "historical_load_results_transferred": False,
    "redistributed_top_bottom_or_knee_loads_claimed": False,
    "compatibility_solved": False, "balancing_free_couples_added": 0,
    "native_CAD_or_frame_execution": False, "known_answers_executed": False,
    "original_producer_pipelines_executed": False,
    "tests_run": False, "review_loop_run": False,
}
LIMITS = [
    "Only the six pinned nominal-gap simultaneous cases and existing finite section stations are compared; no continuous-station maximum is certified.",
    "Saved signed point forces act at their saved source points, including contact-cell points, lateral-plane origins, and discrete body-load nodes. Every saved free couple remains at that point. At a coincident station, before excludes the action and after includes it within 1e-6 mm.",
    "This is the original nominal point-placement method. It does not reconstruct annular pressure, bore-wall traction, interior pressure cuts, contact-patch cut fractions, or redistributed top/bottom/knee local joint loads.",
    "Historical header contracts supply finished geometry, grain, section identities and unchanged conditional material references. The original member worksheet supplies conditional material recipes only. Historical forces, mapped traction, peaks and acceptance do not enter demands.",
    "Common longitudinal strain, area-proportional transverse sharing, equal longitudinal shear moduli, common regional twist, nominal free warping and retained grain-end bridges remain hypotheses.",
    "Header-cleat rectangles deliberately omit full strips enclosing longitudinal circular holes; transmitting the full wrench through that subset is not a physical local-stress bound.",
    "No notch/bore concentration, perpendicular-tension resistance, group/splitting qualification, endbridge capacity, stability, delivered-stock inspection or complete-joint resistance is supplied.",
    "The fresh global source retains filled-bore stiffness idealization, hypothetical connector laws, nonunique seating, no-slip floor and the separate 25 kg accessory allowance. Fresh source convergence does not establish acceptance.",
]


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def key(path):
    path = Path(path)
    return str(path.relative_to(ROOT)) if path.is_relative_to(ROOT) else str(path)


def read(path):
    return json.loads(Path(path).read_text())


def dump(path, value):
    Path(path).write_text(json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n")


def line(stream, value):
    stream.write(json.dumps(value, separators=(",", ":"), allow_nan=False) + "\n")


def bind(pins, path, digest):
    path = Path(path)
    require(path not in pins or pins[path] == digest, f"conflicting source pin: {key(path)}")
    pins[path] = digest


def authenticate(pins):
    for path, digest in pins.items():
        require(sha(path) == digest, f"changed frozen source: {key(path)}")


def helper(filename):
    """Import inert definitions under a private name, with bytecode disabled."""
    path = HERE / filename
    require(sha(path) == PINS[path], f"changed helper: {filename}")
    spec = importlib.util.spec_from_file_location("remaining_replay_" + path.stem.replace("-", "_"), path)
    require(spec is not None and spec.loader is not None, f"missing helper loader: {filename}")
    module = importlib.util.module_from_spec(spec)
    previous = sys.dont_write_bytecode
    try:
        sys.dont_write_bytecode = True
        spec.loader.exec_module(module)
    finally:
        sys.dont_write_bytecode = previous
    return module


def difference(actual, expected, label, force_tol=1e-7, moment_tol=1e-5):
    delta = np.asarray(actual, dtype=float) - np.asarray(expected, dtype=float)
    require(delta.shape == (6,) and np.isfinite(delta).all(), f"invalid {label}")
    require(max(abs(delta[:3])) < force_tol and max(abs(delta[3:])) < moment_tol,
            f"{label}: {delta.tolist()}")
    return delta.tolist()


def source_context(pins):
    fresh, inputs, comparison, assessment = [read(p) for p in (
        FRESH / "member-results.json", FRESH / "inputs.json",
        FRAME / "comparison.json", GRAVITY / "operator-assessment.json",
    )]
    require(inputs["source_sha256"] == fresh["source_sha256"], "fresh source receipt differs")
    for name, digest in fresh["source_sha256"].items():
        bind(pins, ROOT / name, digest)
    for name, digest in assessment["output_sha256"].items():
        bind(pins, GRAVITY / name, digest)
    for name in ("inputs.json", "geometry.json", "action-section-arrays.npz"):
        require(fresh["output_sha256"][name] == pins[FRESH / name], "fresh output receipt differs")
    for path in (FRAME / "comparison.json", FRAME / "response.npz", GRAVITY / "operator-assessment.json"):
        require(fresh["source_sha256"][key(path)] == pins[path], "fresh action/load binding differs")
    require(comparison["source_sha256"][key(GRAVITY / "operator-assessment.json")]
            == pins[GRAVITY / "operator-assessment.json"], "frame/gravity binding differs")
    require(comparison["response_sha256"] == pins[FRAME / "response.npz"], "frame response binding differs")
    require(tuple(c["case_id"] for c in fresh["cases"]) == CASES
            and inputs["selected_force_keys"] == [c + "_gap_raw_force_n" for c in CASES]
            and all(c["source_force_key"] == c["case_id"] + "_gap_raw_force_n" for c in fresh["cases"]),
            "six nominal fresh force keys required")
    require(fresh["counts"]["timber_members"] == 44
            and fresh["counts"]["whole_member_balances"] == 264, "fresh member extraction incomplete")
    require(ROOT / fresh["frame_operator_directory"] == GRAVITY
            and ROOT / fresh["clearance_input_directory"] == FRAME
            and ROOT / comparison["frame_operator_directory"] == GRAVITY, "fresh directories differ")
    nominal = [s for s in comparison["states"] if s["gap_scale"] == 1.0]
    require(tuple(s["case_id"] for s in nominal) == CASES and all(
        s["status"] in ("PASS_CONDITIONAL_COUPLED_FRAME_LAWS", "PASS_CONDITIONAL_LAWS_WITH_BOUNDED_SEATING")
        for s in nominal), "fresh nominal frame cases incomplete")
    require(comparison["climber_load_scale"] == comparison["horizontal_load_scale"] == 1.0
            and comparison["comparison_climber_weight_lb"] == 250.0
            and comparison["comparison_horizontal_force_n"] == 300.0, "fixed load magnitudes differ")
    require(inputs["same_state_dead_load_factor"] == fresh["same_state_dead_load_factor"]
            == comparison["dead_load_factor"] == assessment["dead_load_factor"] == DEAD_FACTOR,
            "fresh dead factor differs")
    require(assessment["operator_ready"] and comparison["modeled_mass_kg"] == assessment["modeled_mass_kg"],
            "fresh gravity source incomplete")
    authenticate(pins)
    model, rows, load_inputs = [read(GRAVITY / name) for name in
                               ("model.json", "row-identities.json", "model-inputs.json")]
    require(tuple(c["case_id"] for c in load_inputs["cases"]) == CASES, "load case order differs")
    for case in load_inputs["cases"]:
        applied = case["source_applied_load"]
        ci = applied["case_inputs"]
        lever = np.asarray(applied["force_application_point_global_xyz_mm"]) - applied["patch_center_global_xyz_mm"]
        require(ci["pounds"] == 250.0 and ci["dynamic_factor"] == 2.0
                and abs(np.linalg.norm(ci["horizontal_force_global_xy_n"]) - 300) < TOL
                and abs(np.linalg.norm(lever) - 100) < TOL, "fixed load/100 mm lever differs")
    return fresh, model, rows, assessment


def actions_for(case, body, member, arrays, response, D, W, model, rows, header):
    """Restore fresh actions and independently bind mechanical F/M to row forces."""
    source = next(m for m in case["members"] if m["member"] == body)
    prefix = source["array_prefix"]
    require(prefix == case["case_id"] + "__" + body, "fresh action prefix differs")
    ids, roles, others = [member[k] for k in
                          ("point_action_ids", "point_action_roles", "point_action_other_bodies")]
    points = arrays[body + "__point_xyz_mm"]
    stations = arrays[body + "__point_stations_mm"]
    point_rows = arrays[body + "__point_rows"]
    values = arrays[prefix + "__point_force_free_couple_xyz"]
    count = source["point_action_count"]
    require(len(ids) == len(roles) == len(others) == len(stations) == len(point_rows) == count
            and points.shape == (count, 3) and values.shape == (count, 6)
            and np.isfinite(points).all() and np.isfinite(values).all() and np.isfinite(stations).all(),
            "fresh action shape/value differs")
    g = member["geometry"]
    frame = np.asarray([g[k] for k in ("axis", "section_u", "section_v")])
    require(np.max(abs(frame @ frame.T - np.eye(3))) < 1e-8
            and abs(np.linalg.det(frame) - 1) < 1e-8, "invalid right-handed grain frame")
    require(np.max(abs((points - g["start"]) @ frame[0] - stations)) < TOL,
            "point partition stations differ")
    body_index = model["body_names"].index(body)
    own_nodes = model["body_nodes"][body]
    node_points = model["physical_node_coordinates_mm"]
    center = np.mean([node_points[str(n)] for n in own_nodes], axis=0)
    projection = D[:, 6 * body_index:6 * body_index + 6]
    forces = response[case["source_force_key"]]
    require(forces.shape == (len(rows),) and np.isfinite(forces).all(), "invalid fresh row force vector")
    incident = {r["row"] for r in rows if body in (r["ownership"]["first_body"], r["ownership"]["second_body"])}
    mechanical_rows = [int(r) for r in point_rows if r >= 0]
    require(set(mechanical_rows) == incident and len(mechanical_rows) == len(incident),
            "lost or duplicate mechanical source action")
    actions, mechanical_deltas = [], []
    for i, (identity, role, other, point, station, raw_row, value) in enumerate(zip(
        ids, roles, others, points, stations, point_rows, values, strict=True
    )):
        row_number = int(raw_row)
        require(row_number == raw_row, "noninteger action row")
        if row_number == -1:
            require(role == "discrete_body_load" and other is None, "unknown nonmechanical action")
            require(identity.startswith("body_load_node_"), "body-load node identity missing")
            node = int(identity.removeprefix("body_load_node_"))
            require(node in own_nodes and np.max(abs(point - node_points[str(node)])) < TOL
                    and max(abs(value[3:])) < 1e-10, "body-load placement/couple differs")
        else:
            require(0 <= row_number < len(rows) and role != "discrete_body_load", "invalid mechanical row")
            row = rows[row_number]
            own = row["ownership"]
            side = 0 if own["first_body"] == body else 1
            require(row["row"] == row_number and row["row_id"] == identity and own["role"] == role
                    and (own["first_body"], own["second_body"])[side] == body
                    and (own["second_body"], own["first_body"])[side] == other
                    and np.max(abs(point - own["point_mm"])) < TOL, "row ownership/point differs")
            unit = -projection[row_number].copy()
            unit[3:] *= 1000
            sign = 1.0 if side == 0 else -1.0
            require(max(abs(unit[:3] - sign * np.asarray(own["direction_global_xyz"]))) < TOL,
                    "row ownership sign differs")
            unit[3:] -= np.cross(point - center, unit[:3])
            mechanical_deltas.append(difference(value, forces[row_number] * unit, "fresh row/action F/M binding"))
        actions.append({"point_index": i, "source_id": identity, "role": role,
                        "other_body": other, "row": row_number, "point_mm": point.tolist(),
                        "station_mm": float(station), "force_n": value[:3].tolist(),
                        "free_moment_nmm": value[3:].tolist()})
    negative = arrays[prefix + "__internal_negative_grain_u_v"]
    positive = arrays[prefix + "__internal_positive_grain_u_v"]
    shape = (2 * len(member["stations_mm"]), 6)
    require(negative.shape == positive.shape == shape and source["cut_trace_count"] == shape[0]
            and np.isfinite(negative).all() and np.isfinite(positive).all(), "fresh cut arrays differ")
    opposed = np.max(abs(negative + positive), axis=0)
    require(max(opposed[:3]) <= 0.1 and max(opposed[3:]) <= 2, "source opposed-half balance failed")
    whole = header.wrench(actions, center)
    require(np.isfinite(whole).all() and max(abs(whole[:3])) <= 0.1 and max(abs(whole[3:])) <= 2,
            "source whole-body balance failed")
    saved = source["whole_member_balance"]
    whole_delta = difference(whole, saved["force_xyz_n"] + saved["moment_xyz_nmm"], "fresh whole balance receipt")
    loads = [a for a in actions if a["role"] == "discrete_body_load"]
    load_wrench = header.wrench(loads, center)
    ci = CASES.index(case["case_id"])
    expected_load = DEAD_FACTOR * W[6 * body_index:6 * body_index + 6, 2 * ci] + W[6 * body_index:6 * body_index + 6, 2 * ci + 1]
    load_delta = difference(load_wrench, expected_load * [1, 1, 1, 1000, 1000, 1000], "fresh mapped gravity/live load", TOL, TOL)
    saved_load = source["mapped_body_load_wrench_about_node_mean"]
    difference(load_wrench, saved_load["force_xyz_n"] + saved_load["moment_xyz_nmm"], "fresh load receipt")
    audit = {"case_id": case["case_id"], "body": body, "source_force_key": case["source_force_key"],
             "array_prefix": prefix, "point_action_count": count, "mechanical_row_count": len(mechanical_rows),
             "node_mean_datum_xyz_mm": center.tolist(), "whole_body_wrench_xyz_n_nmm": whole.tolist(),
             "whole_body_receipt_delta_n_nmm": whole_delta, "opposed_half_max_abs_n_nmm": opposed.tolist(),
             "mapped_body_load_wrench_xyz_n_nmm": load_wrench.tolist(), "load_operator_delta_n_nmm": load_delta,
             "row_action_max_abs_delta_n_nmm": np.max(abs(np.asarray(mechanical_deltas)), axis=0).tolist()}
    return source, actions, negative, audit


def material_for(source, material, net, old_material=None):
    binding = source["conditional_material"]
    require(binding["design_resistance_established"] is False, "reference claim boundary differs")
    if old_material is not None:
        require(binding == old_material, "original conditional material scenario differs")
    refs = binding["CF_only_reference_mpa"]
    require(set(refs) == {"Ft_parallel", "Fc_parallel", "Fb", "Fv_parallel"}, "reference keys differ")
    base = material["conditional_DF_L_No2_base_row"]["base_properties"]
    for name, value in refs.items():
        require(abs(value - base[name] * binding["CF"].get(name, 1) * net.PSI_MPA) < 1e-12,
                "existing CF-only material reference differs")
    return binding, refs


def layouts_for(family, members, surfaces, model, pins, cleat, remaining, header, timber, net):
    """Return the original finite section recipes, never old cut forces."""
    layouts, area_checks = {}, []
    if family == "header_paired_bores":
        require(callable(getattr(header, "section_geometry", None)), "missing header section_geometry API")
        body = "base_header"
        require(model["bodies"][body]["member_geometry"] == members[body]
                and model["bodies"][body]["finished_surface_record"] == surfaces[body], "header geometry changed")
        g = members[body]["geometry"]
        require(np.max(abs(np.asarray([g[k] for k in ("axis", "section_u", "section_v")]) - np.eye(3))) < 1e-8,
                "header X/Y/Z frame differs")
        require(model["bodies"][body]["grain_override"]["material_axes_global_xyz"]["L"] == g["axis"],
                "header longitudinal grain differs")
        sections = [s for s in model["saved_header_sections"] if s["properties"]["disconnected_ligaments"]]
        require(len(sections) == 6, "six paired-bore header section recipes required")
        own = []
        for section in sections:
            require(section["source_step_sha256"] == members[body]["current_finished_step_sha256"],
                    "header section STEP binding differs")
            layout = header.section_geometry(model, section, net)
            station_index = int(np.argmin(abs(np.asarray(members[body]["stations_mm"]) - layout["station_mm"])))
            require(abs(members[body]["stations_mm"][station_index] - layout["station_mm"]) < TOL,
                    "header recipe station missing from fresh arrays")
            own.append({**layout, "saved_station_index": station_index,
                        "net_area_mm2": section["properties"]["area_mm2"],
                        "material_region_count": len(layout["regions"])})
        require({s["duty"] for s in own} == set(cleat.BLOCKS), "six header duties differ")
        layouts[body] = own
        return layouts, area_checks
    blocks = cleat.BLOCKS if family == "header_cleats" else remaining.BLOCKS
    for body in blocks:
        member = members[body]
        bind(pins, ROOT / member["current_finished_step"], member["current_finished_step_sha256"])
        if family == "header_cleats":
            require(callable(getattr(cleat, "opening_geometry", None))
                    and callable(getattr(cleat, "subset_section", None)), "missing header-cleat geometry API")
            frozen = model["bodies"][body]
            require(frozen["member_geometry"] == member and frozen["finished_surface_record"] == surfaces[body],
                    "header-cleat recipe geometry changed")
            geom = cleat.opening_geometry(body, member, surfaces[body], frozen["grain_override"], pins)
            sections = [{"saved_station_index": i, **cleat.subset_section(geom, float(s), timber)}
                        for i, s in enumerate(member["stations_mm"])]
        else:
            require(callable(getattr(remaining, "geometry", None)) and callable(getattr(timber, "section", None)),
                    "missing remaining-block geometry API")
            geom = remaining.geometry(body, member, surfaces[body])
            sections = [{"saved_station_index": i, **timber.section(geom, float(s))}
                        for i, s in enumerate(member["stations_mm"])]
            sections = [s for s in sections if s["bore_or_tangency_ids"]]
            require({b["axis_id"] for b in geom["bores"]} == {
                identity for s in sections for identity in s["bore_or_tangency_ids"]}, "opening coverage differs")
        require(sections, "no finite opening section recipes")
        layouts[body] = {"geometry": geom, "sections": sections}
    return layouts, area_checks


def evaluate_family(family, output, context, arrays, response, D, W, model, rows,
                    pins, geometries, surfaces, contract, old_materials, material,
                    cleat, remaining, header, timber, net):
    layouts, area_checks = layouts_for(family, geometries["members"], surfaces, contract,
                                      pins, cleat, remaining, header, timber, net)
    summaries, audits, witnesses = [], [], []
    worksheet = output / (family + "-cuts.jsonl.gz")
    action_file = output / (family + "-actions.jsonl.gz")
    completed_states = []
    with gzip.open(worksheet, "wt", encoding="utf-8") as cuts_stream, gzip.open(action_file, "wt", encoding="utf-8") as action_stream:
        for body, recipes in layouts.items():
            member = geometries["members"][body]
            sections = recipes if family == "header_paired_bores" else recipes["sections"]
            if family == "header_cleats":
                for saved in geometries["saved_matching_finished_sections"]:
                    if saved["member"] != body:
                        continue
                    section = min(sections, key=lambda s: abs(s["station_mm"] - saved["station_mm"]))
                    require(abs(section["station_mm"] - saved["station_mm"]) < TOL
                            and saved["source_step_sha256"] == member["current_finished_step_sha256"],
                            "saved exact cleat section binding differs")
                    delta = section["actual_opening_area_mm2"] - saved["properties"]["area_mm2"]
                    require(abs(delta) < 0.001, "cleat physical opening area differs from exact section")
                    area_checks.append({"body": body, "plane_id": saved["plane_id"],
                                        "station_mm": section["station_mm"], "analytic_minus_saved_area_mm2": delta})
            for case in context["cases"]:
                source, actions, negative, audit = actions_for(case, body, member, arrays, response, D, W, model, rows, header)
                require(source["point_action_count"] == (394 if body == "base_header" else 40), "original action census differs")
                binding, refs = material_for(source, material, net, old_materials[body])
                audits.append(audit)
                line(action_stream, {"audit": audit, "actions": actions, "conditional_material": binding})
                state_count = 0
                for section in sections:
                    si = section["saved_station_index"]
                    station = section["station_mm"]
                    original_datum = np.asarray(member["geometry"]["start"]) + member["stations_mm"][si] * np.asarray(member["geometry"]["axis"])
                    datum = np.asarray(section["datum_xyz_mm"]) if body == "base_header" else original_datum
                    frame = np.asarray([member["geometry"][k] for k in ("axis", "section_u", "section_v")])
                    for index in (2 * si, 2 * si + 1):
                        before = index % 2 == 0
                        # Direct action restoration uses the original station/limit
                        # convention. Header moments then shift to its saved actual net centroid.
                        direct = cleat.action_cut(actions, member["geometry"], member["stations_mm"][si], before)
                        action_delta = difference(direct, negative[index], "fresh full action cut restoration")
                        q = negative[index].copy()
                        q[3:] -= np.cross(frame @ (datum - original_datum), q[:3])
                        included = [a for a in actions if a["station_mm"] - member["stations_mm"][si] <= TOL
                                    and not (before and abs(a["station_mm"] - member["stations_mm"][si]) <= TOL)]
                        global_direct = -header.wrench(included, datum)
                        placement_delta = difference(np.r_[frame @ global_direct[:3], frame @ global_direct[3:]], q,
                                                     "fresh point cut at actual datum")
                        nominal = net.nominal_section(q, section["regions"], refs)
                        nominal["references"] = refs
                        require(abs(nominal["net_section_integrals"]["area_mm2"] - section["net_area_mm2"]) < 1e-7,
                                "retained net area differs")
                        difference(nominal["reconstructed_signed_cut_n_nmm"], q, "regional wrench recovery", 1e-7, 1e-6)
                        summary = remaining.cut_summary(case["case_id"], body, index, section, nominal)
                        summary.update(family=family, source_force_key=case["source_force_key"], array_prefix=source["array_prefix"])
                        for name in ("duty", "plane_id", "actual_opening_area_mm2", "omitted_sound_wood_area_mm2",
                                     "omitted_sound_wood_fraction_of_actual_net_area"):
                            if name in section:
                                summary[name] = section[name]
                        cut = {"summary": summary, "section": section, "conditional_material": binding,
                               "grain_frame_rows_xyz": frame.tolist(), "source_array_datum_xyz_mm": original_datum.tolist(),
                               "cut_datum_xyz_mm": datum.tolist(), "source_array_signed_cut_n_nmm": negative[index].tolist(),
                               "fresh_action_cut_delta_n_nmm": action_delta, "actual_datum_cut_delta_n_nmm": placement_delta,
                               "included_source_point_indices": [a["point_index"] for a in included],
                               "nominal_section": nominal}
                        line(cuts_stream, cut)
                        summaries.append(summary)
                        state_count += 1
                        if body == "base_header" and case["case_id"] == "a1-rear" and abs(station - 133.35) < TOL:
                            require(section["duty"] == "knee_outer_left_inner_frame_block", "A1 torque duty differs")
                            cut["source_signed_cut_by_role_n_nmm"] = {
                                role: (-header.wrench([a for a in included if a["role"] == role], datum)).tolist()
                                for role in sorted({a["role"] for a in included})}
                            witnesses.append(cut)
                completed_states.append({"body": body, "case_id": case["case_id"], "evaluated_limit_count": state_count})
    expected = {"header_cleats": 1968, "remaining_12_blocks": 2304, "header_paired_bores": 72}[family]
    require(len(summaries) == expected, f"original finite census differs: {family}")
    if family == "header_paired_bores":
        require(len(witnesses) == 2 and {w["summary"]["limit"] for w in witnesses} == {"before", "after"},
                "full fresh A1-rear torque witness missing")
    peaks = {metric: max(summaries, key=lambda s: s[metric]) for metric in METRICS}
    return {"status": "COMPLETE_FRESH_FINITE_NOMINAL_COMPARISONS", "expected_limit_count": expected,
            "evaluated_limit_count": len(summaries), "body_ids": list(layouts),
            "completed_body_case_states": completed_states, "source_balances": audits,
            "geometry_recipes": layouts, "saved_exact_area_crosschecks": area_checks,
            "cut_summaries": summaries, "same_state_peaks": peaks,
            "per_body_peaks": {body: {m: max((s for s in summaries if s["block"] == body), key=lambda s: s[m])
                                     for m in METRICS} for body in layouts},
            "finite_index_counts_above_one": {m: sum(bool(s[m] > 1) for s in summaries) for m in METRICS},
            "all_evaluated_nominal_reference_indices_below_one": all(s[m] <= 1 for s in summaries for m in METRICS),
            "full_A1_rear_133_35mm_torque_witness": witnesses,
            "worksheets": [worksheet.name, action_file.name], "unsupported_or_missing_API": [], **FLAGS}


def build(output: str | Path) -> dict:
    """Parent API: write one new immediate child of the owned ignored raw folder."""
    output = Path(output).resolve()
    require(output.parent == RAW.resolve() and not output.exists(), "fresh immediate owned raw output child required")
    producer = Path(__file__).resolve()
    pins = {**PINS, producer: sha(producer)}
    authenticate(pins)
    fresh, model, rows, assessment = source_context(pins)
    geometries, surfaces_packet, contract, contract_inputs, material = [read(p) for p in (
        FRESH / "geometry.json", FEATURES, CONTRACT / "model.json", CONTRACT / "inputs.json", MATERIAL,
    )]
    receipt = read(CONTRACT / "receipt.json")
    for name in ("model.json", "inputs.json"):
        require(receipt["output_sha256"][name] == pins[CONTRACT / name], "historical recipe receipt differs")
    surfaces = {r["member_id"]: r for r in surfaces_packet["records"]}
    original = read(ORIGINAL_MATERIAL_RECIPES)
    require(tuple(c["case_id"] for c in original["cases"]) == CASES, "original material recipe case census differs")
    old_materials = {m["member"]: m["conditional_material"] for m in original["cases"][0]["members"]}
    for case in original["cases"]:
        require(all(m["conditional_material"] == old_materials[m["member"]] for m in case["members"]),
                "original conditional material recipes differ by case")
    for body, binding in contract_inputs["existing_header_evidence"]["conditional_material"].items():
        require(old_materials[body] == binding, "original/header material recipes differ")
    cleat, remaining, header, timber, net = [helper(name) for name in (
        "header-cleat-net-sections.py", "remaining-net-sections.py", "header-net-section.py",
        "corner-timber-sections.py", "corner-net-section.py",
    )]
    require(net.TORSION_SOURCE == BASE / "member_stability.py", "rectangle torsion dependency differs")
    net.rectangle_torsion = cache(net.rectangle_torsion)
    bind(pins, ROOT / geometries["members"]["base_header"]["current_finished_step"],
         geometries["members"]["base_header"]["current_finished_step_sha256"])
    authenticate(pins)
    output.mkdir(parents=True, exist_ok=False)
    (output / ".gitignore").write_text("*\n")
    (output / "producer.py.snapshot").write_bytes(producer.read_bytes())
    families = {}
    with np.load(FRESH / "action-section-arrays.npz", allow_pickle=False) as arrays, \
         np.load(FRAME / "response.npz", allow_pickle=False) as response, \
         np.load(GRAVITY / "operators.npz", allow_pickle=False) as operators:
        D, W = operators["D"], operators["W"]
        require(D.shape == (len(rows), 6 * len(model["body_names"]))
                and W.shape == (6 * len(model["body_names"]), 12)
                and np.isfinite(D).all() and np.isfinite(W).all(), "fresh operator shape/value differs")
        for family in ("header_cleats", "remaining_12_blocks", "header_paired_bores"):
            try:
                families[family] = evaluate_family(
                    family, output, fresh, arrays, response, D, W, model, rows, pins,
                    geometries, surfaces, contract, old_materials, material,
                    cleat, remaining, header, timber, net,
                )
            except (ValueError, KeyError, AttributeError, StopIteration) as error:
                # Preserve failed family files as partial evidence. Other finite
                # families remain independently computable, without inventing an API.
                families[family] = {"status": "GAP_NO_COMPLETED_FAMILY_COMPARISON",
                                    "unsupported_or_missing_API": [{"error_type": type(error).__name__, "reason": str(error)}],
                                    "partial_worksheets_are_accepted_results": False, **FLAGS}
    authenticate(pins)
    source_hashes = {key(p): h for p, h in sorted(pins.items())}
    complete = all(f["status"] == "COMPLETE_FRESH_FINITE_NOMINAL_COMPARISONS" for f in families.values())
    result = {"schema": "knee-bridge-remaining-finite-opening-sections/v1",
              "status": "COMPLETE_FRESH_FINITE_NOMINAL_COMPARISONS" if complete else "PARTIAL_WITH_EXPLICIT_FAMILY_GAPS",
              "case_ids": list(CASES), "fixed_loads": "250 lb x 2; signed 300 N; 100 mm hold lever",
              "dead_load_factor": DEAD_FACTOR, "modeled_mass_kg": assessment["modeled_mass_kg"],
              "fresh_load_source_paths": [key(p) for p in (FRESH / "member-results.json", FRAME / "comparison.json",
                                                           FRAME / "response.npz", GRAVITY / "operator-assessment.json")],
              "source_sha256": source_hashes, "producer_sha256": pins[producer],
              "source_force_state_scope": fresh["source_force_state_scope"],
              "source_frame_assumptions": fresh["source_frame_assumptions"],
              "fresh_member_method_limits": fresh["method_limits"],
              "historical_missing_artifacts": read(FRESH / "inputs.json")["missing_historical_artifacts"],
              "working_hypotheses": list(remaining.ASSUMPTIONS), "applicability_limits": LIMITS,
              "unavailable_design_resistances": contract_inputs["unavailable_design_resistances"],
              "runtime": {"python": platform.python_version(), "numpy": np.__version__},
              "families": families, "sources_authenticated_before_and_after": True, **FLAGS}
    dump(output / "checks.json", result)
    dump(output / "sources.json", {"source_sha256": source_hashes,
                                   "fresh_load_authority": result["fresh_load_source_paths"],
                                   "historical_contract_role": "geometry, grain, section identities and conditional material recipes only",
                                   "historical_member_worksheet_role": "conditional material recipes only",
                                   "historical_traction_map_consumed": False})
    authenticate(pins)
    dump(output / "receipt.json", {"schema": "knee-bridge-remaining-sections-receipt/v1",
        "status": result["status"], "producer_sha256": pins[producer], "source_sha256": source_hashes,
        "output_sha256": {p.name: sha(p) for p in sorted(output.iterdir()) if p.is_file() and p.name != "receipt.json"},
        "family_statuses": {name: family["status"] for name, family in families.items()},
        "family_limit_counts": {name: family.get("evaluated_limit_count") for name, family in families.items()},
        "sources_authenticated_before_and_after": True, **FLAGS})
    authenticate(pins)
    return {"status": result["status"], "output": str(output), "families": {
        name: {k: family[k] for k in ("status", "unsupported_or_missing_API")}
        | {"evaluated_limit_count": family.get("evaluated_limit_count"), "same_state_peaks": family.get("same_state_peaks")}
        for name, family in families.items()},
        "checks_sha256": sha(output / "checks.json"), "receipt_sha256": sha(output / "receipt.json")}
