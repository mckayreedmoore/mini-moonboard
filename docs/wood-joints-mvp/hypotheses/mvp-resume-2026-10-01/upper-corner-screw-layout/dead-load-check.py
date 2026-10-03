"""Prepare or execute one frozen permanent-load comparison, with two gap states.

Only the parent executes --run. --sourcepin-only authenticates files without
importing mechanics. All runtime arithmetic reuses the maintained frame,
clearance, member-action, stress and stability helpers.
"""

from __future__ import annotations

import argparse
import csv
import fcntl
import hashlib
import importlib.metadata
import json
import sys
from pathlib import Path

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
PACKET = HERE.parent
ROOT = PACKET.parents[3]
FRAME = HERE / "operators-attempt02"
SOURCE = HERE / "frame-250-attempt02"
MEMBERS = PACKET / "member-screen-attempt02/four-screw-layout01"
STABILITY = PACKET / "member-stability-attempt01/four-screw-layout01/checks.json"
RAW = HERE / "rawlocal/dead-load-check"
CD = 0.9
SEED_CASE = "a12-rear"
CASES = ("a12-rear", "a12-forward", "a12-left", "k12-right", "k12-rear", "a1-rear")
PINS = {
    FRAME / "operator-assessment.json": "1a82cd2adbfece3942bf8c90f593f1e21a150adb65db625135aadd258fd5024a",
    FRAME / "model.json": "b5f9b87b70c4a9920372a3443a55e37dfe34351fb9ac8210b299c1360fb93626",
    FRAME / "row-identities.json": "cdf218780bdabdb8774174c79b37d7c9f554abc6be2e1f817999635e56868b27",
    FRAME / "operators.npz": "c9483639c69c0696b29f3fd69522e6c9a8e673aa7ce82277788103b14c955ba3",
    SOURCE / "comparison.json": "bea6cbc330af3cdb20499d774a8f6bb24481d687c3150adb01ede18e4c1d50ca",
    SOURCE / "response.npz": "0625196497b0dbc7b297724d7b9947f7c7c61bb282cd4d9681705629302c76c7",
    MEMBERS / "member-results.json": "54f3888581717d2579b0dd6ea7dcd754501ec2890a9f4869059f476f2d0965c5",
    MEMBERS / "geometry.json": "c61139087fac34e8094f2336f15dd6de5c0112d26d37b9535526f47332f453af",
    MEMBERS / "action-section-arrays.npz": "ddfa310266661ea5ba6e188d2bf473121d99158d50921c84760744519e2a7caf",
    STABILITY: "aceebc0beaee1cc178450b52b2a16a32924803c3210dc0c115c0fee7a3a7c574",
    PACKET / "simple_frame.py": "3d8c14cccf9306766a4993bad9ea39501bbc9c812af9e79b393875d5d3c09d34",
    PACKET / "right_corner_clearance.py": "93c7727c1c24fb5b7ed725fc4656651fe6e760a36a378d635a97e202b872fb88",
    PACKET / "circular_clearance.py": "0314817effad8d8279e80576ed2cd77012566d0c8252f74e279dc83e366df98b",
    PACKET / "bounded_clearance.py": "35c0ceb7609c7ff77118ddf0a8e9f0da681ae41ad3396e4a95a71792724a9c7b",
    PACKET / "member_screen.py": "5ecbfcebc8ea45bba83961305735f919d5e6caa3862625befec875655dd0b5d9",
    PACKET / "member_stability.py": "eb70dbe72c1ed3b9518739915193083fd6a07ebd064ba17d0c07f299f6786b72",
    PACKET / "bottom_corner_checks.py": "5df7a264354e1488c2a68332820fe927e8dcb1fa9721111ec8fac5c00ad19e26",
    PACKET / "bottom-corner-component-attempt06/producer.py.snapshot": "2afb5a8af006c4ae4818e863bc4300d4e63d070a816dd5e96079718d8ede57c3",
    PACKET / "top_corner_actions.py": "bfe51728521b620e54fa23822f4e3b3cee320457503580cf95ab439863327bd5",
    PACKET / "frame_state_contract.py": "22e1f8b864c03469701010fc856a815b3604a4efde2748531e36d284050266e5",
    PACKET.parent / "upper-left-service-frame-clearance-2026-10-01/check_frame.py": "54ebbd0259fa15a201ba05da035df9fca88d65987ff4473b4322216f8ca42164",
    ROOT / "fea/reinforced_timber_resistance.py": "d4e8302d39beb9f53c70fa264762c59c231f6e6b086cb866906ca39eeab9cfbc",
    ROOT / "scripts/floor_taper_checks.py": "bf15d8983b42d95dda0d0329bc2d8c2664f9c146813f21e1a0cc8f0f6a3bf1c3",
    PACKET.parent / "mvp-acceleration-2026-09-28/current-gravity-settle-climber-ramp-scenario-attempt01/verify_decomposition.py": "9e8a805be97922bb4de7187adcfa349381b19a5060863bfe5bf5ccc25239c699",
    PACKET.parent / "mvp-acceleration-2026-09-28/current-frame-connector-compliance-attempt04-operator-review-attempt01/verify_review.py": "e998750807c3e226470c725d83ee51b428f5baa87f6c544848b80f08aff47e24",
}
FLAGS = dict.fromkeys((
    "full_six_case_frame", "full_frame_acceptance", "complete_member_acceptance",
    "complete_joint_acceptance", "formal_torsion_qualification", "physical_release",
    "native_launch", "CAD_rebuilt", "geometry_changed", "material_laws_changed",
    "hardware_changed", "tests_run", "review_run", "source_acceptance_transferred",
    "rated_cases_replaced", "combined_duration_basis_adopted",
), False)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_text())


def require(condition, message):
    if not condition:
        raise ValueError(message)


def write(path, value):
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n")


def authenticate(pins):
    for path, digest in pins.items():
        require(sha(path) == digest, "changed frozen source: " + str(path))


def source_pins():
    """Return the authenticated transitive source binding; no mechanics imports."""
    pins = dict(PINS)
    authenticate(pins)
    # Reuse the already recorded reporting-only adapter, preserving both files.
    old = (PACKET / "bottom-corner-component-attempt06/producer.py.snapshot").read_text()
    before = '"reviewed_geometry_changed": False,'
    after = '"reviewed_geometry_changed": member_report.get("reviewed_geometry_changed", False),'
    require(old.count(before) == 1 and old.replace(before, after)
            == (PACKET / "bottom_corner_checks.py").read_text(), "bottom helper changed beyond its recorded reporting adapter")
    for path in (FRAME / "operator-assessment.json", SOURCE / "comparison.json",
                 MEMBERS / "member-results.json", STABILITY):
        report = read(path)
        additions = {ROOT / name: digest for name, digest in report["source_sha256"].items()}
        if path.parent == FRAME:
            additions.update({FRAME / name: digest for name, digest in report["output_sha256"].items()})
        for source, digest in additions.items():
            if source == PACKET / "bottom_corner_checks.py" and digest == PINS[PACKET / "bottom-corner-component-attempt06/producer.py.snapshot"]:
                continue  # The old source is authenticated by its exact snapshot.
            require(source not in pins or pins[source] == digest, "conflicting source binding: " + str(source))
            pins[source] = digest
    pins[Path(__file__).resolve()] = sha(Path(__file__))
    authenticate(pins)
    return pins


def contract(pins):
    source, assessment = read(SOURCE / "comparison.json"), read(FRAME / "operator-assessment.json")
    require(source["frame_operator_directory"] == str(FRAME.relative_to(ROOT)), "source/operator mismatch")
    require(source["response_sha256"] == PINS[SOURCE / "response.npz"], "source response mismatch")
    require({(s["case_id"], s["gap_scale"]) for s in source["states"]}
            == {(case, gap) for case in CASES for gap in (0.0, 1.0)}
            and len(source["states"]) == 12, "original six-case source census changed")
    require(source["climber_load_scale"] == 1.0 and source["comparison_climber_weight_lb"] == 250.0
            and source.get("horizontal_load_scale", 1.0) == 1.0, "rated source loads changed")
    mass, factor = assessment["modeled_mass_kg"], source["dead_load_factor"]
    require(mass == source["modeled_mass_kg"] and factor == assessment["dead_load_factor"]
            and abs(factor - (mass + 25.0) / mass) < 1e-14, "original equipment allowance changed")
    return {
        "schema": "frozen_dead_only_frame_contract/v1",
        "producer_sha256": sha(Path(__file__)),
        "source_sha256": {str(p.relative_to(ROOT)): digest for p, digest in pins.items()},
        "api": "run(output: pathlib.Path) -> comparison dict; source_pins() -> authenticated pins",
        "frame_api": "simple_frame.lump_floor(H,D,e,W,rows); right_corner_clearance.solve(H,D,e,W,k,uni,normals,tangents,targets,gaps,seed,circular_clearance)",
        "adapter": "Historical Frame fixes 1840 rows/four gaps; use its maintained current-size helper, 1888 rows/88 gap planes. No changes to solver equations or gates.",
        "load_case": "dead-only", "gap_scales": [0.0, 1.0],
        "load_columns": {"gravity": 0, "live": None},
        "modeled_mass_kg": mass, "equipment_mass_kg": 25.0, "dead_load_factor": factor,
        "original_gravity_multiplier": 1.0, "additional_dead_load_multiplier": 1.0,
        "live_gravity_scale": 0.0, "live_horizontal_scale": 0.0, "live_moment_scale": 0.0,
        "wood_strength_CD": CD, "elastic_or_hardware_duration_factor": 1.0,
        "bottom_helper_adapter": "The frozen old snapshot and current helper differ only in reviewed_geometry_changed reporting; saved_actions is unchanged.",
        "engineering_oracles_executed": False, "frame_solve": False,
        **FLAGS,
    }


def owned_output(output):
    output = output.resolve()
    require(RAW.resolve() in output.parents, "output must be a fresh child of rawlocal/dead-load-check")
    require(not output.exists(), "preserve completed or stopped output; choose a fresh child")
    output.mkdir(parents=True)
    return output


def load_helpers():
    sys.path[:0] = [str(PACKET), str(ROOT)]
    import bounded_clearance
    import circular_clearance
    import member_stability
    import right_corner_clearance
    import simple_frame

    return simple_frame, right_corner_clearance, circular_clearance, bounded_clearance, member_stability


def solve_state(helper, disk, bounds, matrices, targets, gaps, seed, gap_scale):
    """Keep the original rank exception and its existing bounded-seating scope."""
    H, D, e, W, k, uni, normals, tangents = matrices
    certificate = None
    try:
        f, q, a, audit = helper.solve(H, D, e, W, k, uni, normals, tangents,
                                      targets, gap_scale * gaps, seed, disk)
    except ValueError as error:
        if gap_scale != 1.0 or str(error) != "unrestrained rigid coordinate":
            raise
        trace, local = error.__traceback__, {}
        while trace is not None:
            if trace.tb_frame.f_code is helper.solve.__code__:
                local = trace.tb_frame.f_locals
            trace = trace.tb_next
        f, q, a, audit = (local[name] for name in ("f", "q", "a", "audit"))
        certificate, _ = bounds.finite_clearance_certificate(
            D, q, f, k, uni, normals, tangents, targets, gap_scale * gaps, W)
        require(certificate["bounded"], "unbounded fixed-force clearance motion")
    return f, q, a, audit, certificate


def replay_members(method, operators, raw_states, pins):
    """Replay the frozen point/cut census, replacing forces and nodal loads only."""
    import numpy as np

    member, accounting = method.member, method.accounting
    model = read(FRAME / "model.json")
    records = read(MEMBERS / "geometry.json")["members"]
    checks = {r["member"]: r for r in read(STABILITY)["members"]}
    materials = read(accounting.MATERIALS)
    labels = [tuple(map(int, line.split("."))) for line in member.DOFS.read_text().splitlines() if line.strip()]
    F, D, W = (operators[name] for name in ("F", "D", "W"))
    require(F.shape == (len(labels), 12) and D.shape == (1888, 300), "physical operator census changed")
    require(len(records) == 44 and set(records) == set(checks), "44-member replay census changed")
    gravity, original_load = {}, {}
    factor = read(SOURCE / "comparison.json")["dead_load_factor"]
    for (node, dof), dead, live in zip(labels, F[:, 0], F[:, 1], strict=True):
        gravity.setdefault(str(node), [0.0, 0.0, 0.0])[dof - 1] = factor * float(dead)
        original_load.setdefault(str(node), [0.0, 0.0, 0.0])[dof - 1] = factor * float(dead) + float(live)
    traces, summaries, balances, arrays = [], [], [], {}
    with (np.load(MEMBERS / "action-section-arrays.npz", allow_pickle=False) as saved,
          np.load(SOURCE / "response.npz", allow_pickle=False) as source_response):
        for body, record in records.items():
            geometry, frozen = record["geometry"], checks[body]
            require(sha(ROOT / record["current_finished_step"]) == record["current_finished_step_sha256"], "finished STEP changed: " + body)
            pins[ROOT / record["current_finished_step"]] = record["current_finished_step_sha256"]
            basis = member.basis(geometry)
            binding, base = method.references(body, geometry, materials)
            require(base == frozen["references"], "material reference changed: " + body)
            adjusted = {key: value * CD if key in ("Fb_star_mpa", "Ft_mpa", "Fc_star_mpa", "Fv_mpa") else value
                        for key, value in base.items()}
            short, long = frozen["minimum_intact_rectangle_short_long_mm"]
            length, bay = frozen["length_mm"], frozen["maximum_candidate_weak_bay_mm"]
            kernels = {name: method.stability_kernel(short, long, length, weak, adjusted)
                       for name, weak in (("end_supported_only", length), ("existing_timber_weak_restraints", bay))}
            for name, kernel in kernels.items():
                prior = frozen["stability_kernels"][name]
                require(kernel["FcE_strong_weak_mpa"] == prior["FcE_strong_weak_mpa"]
                        and kernel["FbE_mpa"] == prior["FbE_mpa"], "duration changed Euler references")
            orientation = model["material_binding"]["orientation_overrides"][body]
            require(orientation == frozen["frozen_elastic_orientation"], "elastic grain frame changed")
            require(np.max(abs(np.array(orientation["material_axes_global_xyz"]["L"]) - basis[0])) < 1e-8, "grain axis changed")
            radial = np.array(orientation["material_axes_global_xyz"]["R"])
            ru, rv = abs(float(radial @ basis[1])), abs(float(radial @ basis[2]))
            aligned, ratio = max(ru, rv) > 1 - 1e-7, .064 / .078 if ru > rv else .078 / .064
            index = model["body_names"].index(body)
            body_slice = slice(6 * index, 6 * index + 6)
            datum = np.mean([model["physical_node_coordinates_mm"][str(n)] for n in model["body_nodes"][body]], axis=0)
            body_traces = []
            for tag, raw in raw_states.items():
                actions = method.bottom.saved_actions(body, SEED_CASE, record, saved)
                for action in actions:
                    row, point = action["row"], np.array(action["point_mm"])
                    if row < 0:
                        require(action["role"] == "discrete_body_load", "unsupported external point action")
                        node = action["source_id"].removeprefix("body_load_node_")
                        require(np.max(abs(np.array(action["force_n"]) - original_load[node])) < 1e-7
                                and np.max(abs(np.array(action["free_moment_nmm"]))) == 0, "saved F action mismatch")
                        action["force_n"] = gravity[node]
                        continue
                    expected = -D[row, body_slice] * source_response[SEED_CASE + "_gap_raw_force_n"][row]
                    prior = accounting.wrench([action], datum)
                    require(np.max(abs(prior[:3] - expected[:3])) < 1e-7
                            and np.max(abs(prior[3:] - 1000 * expected[3:])) < 1e-5, "saved point action/operator mismatch")
                    current = -D[row, body_slice] * raw[row]
                    action["force_n"] = current[:3].tolist()
                    action["free_moment_nmm"] = (1000 * current[3:] - np.cross(point - datum, current[:3])).tolist()
                closure = accounting.wrench(actions, datum)
                require(np.max(abs(closure[:3])) < .1 and np.max(abs(closure[3:])) < 2, "dead-only member imbalance: " + body)
                load_wrench = accounting.wrench([a for a in actions if a["row"] < 0], datum)
                require(np.max(abs(load_wrench - factor * W[body_slice, 0] * [1, 1, 1, 1000, 1000, 1000])) < 1e-6, "dead F/W member mismatch")
                balances.append({"state": tag, "member": body, "residual_xyz_n_nmm": closure.tolist()})
                minus, plus, positions, _ = member.cut_vectors(actions, geometry, np.array(record["stations_mm"]))
                negative = np.c_[minus[:, :3] @ basis.T, minus[:, 3:] @ basis.T]
                positive = np.c_[plus[:, :3] @ basis.T, plus[:, 3:] @ basis.T]
                require(np.max(abs(negative + positive)) < 1e-6, "opposite cut sides disagree")
                arrays[tag + "__" + body + "__internal_negative_grain_u_v"] = negative
                arrays[tag + "__" + body + "__point_force_free_couple_xyz"] = np.array([a["force_n"] + a["free_moment_nmm"] for a in actions])
                for i, value in enumerate(negative):
                    rectangle = record["rectangle_at_station"][i // 2]
                    if not rectangle["status"].startswith("BORE_FREE_"):
                        continue
                    value = value.copy()
                    width, depth = rectangle["width_depth_mm"]
                    offset = basis @ (np.array(rectangle["centroid_xyz_mm"]) - np.array(geometry["start"]) - positions[i] * basis[0])
                    value[3:] -= np.cross(offset, value[:3])
                    stress = member.stresses(value, width, depth, binding)
                    normal = {name: method.normal_check(value, width, depth, kernel, adjusted) for name, kernel in kernels.items()}
                    # The unchanged helper checks its 180 psi reference internally.
                    # Recover stress at CD=1, then apply CD=.9 to strength ratios.
                    shear = method.shear_check(value, width, depth, base["Fv_mpa"], aligned, ratio)
                    trace = {"state": tag, "member": body, "station_mm": float(positions[i]),
                             "trace": "before" if i % 2 == 0 else "after", "section_status": rectangle["status"],
                             **dict(zip(("N_n", "Vu_n", "Vv_n", "T_nmm", "Mu_nmm", "Mv_nmm"), map(float, value), strict=True)),
                             "width_mm": width, "depth_mm": depth,
                             "maximum_tension_stress_mpa": stress["maximum_tension_extreme_mpa"],
                             "maximum_compression_stress_mpa": stress["maximum_compression_extreme_mpa"],
                             "normal_reference_sum_cd0_9": stress["linear_normal_reference_sum"] / CD,
                             "end_only_normal_ratio_cd0_9": normal["end_supported_only"]["interaction_ratio"],
                             "end_only_domain_ok": normal["end_supported_only"]["ratio_qualified_inside_declared_stability_domain"],
                             "timber_braced_normal_ratio_cd0_9": normal["existing_timber_weak_restraints"]["interaction_ratio"],
                             "timber_braced_domain_ok": normal["existing_timber_weak_restraints"]["ratio_qualified_inside_declared_stability_domain"],
                             "timber_braced_normal_exceeds": bool(normal["existing_timber_weak_restraints"]["ratio_exceeds_one"]),
                             "timber_braced_stability_3_9_4": normal["existing_timber_weak_restraints"]["stability_3_9_4_ratio"],
                             "transverse_shear_u_mpa": shear["transverse_shear_u_v_max_mpa"][0],
                             "transverse_shear_v_mpa": shear["transverse_shear_u_v_max_mpa"][1],
                             "torsional_shear_u_mpa": shear["torsional_shear_u_v_max_mpa"][0],
                             "torsional_shear_v_mpa": shear["torsional_shear_u_v_max_mpa"][1],
                             "shear_face_ratio_cd1": shear["face_lower_bound_ratio"],
                             "shear_face_ratio_cd0_9": shear["face_lower_bound_ratio"] / CD,
                             "shear_component_bound_cd0_9": shear["component_rectangle_upper_bound_ratio"] / CD,
                             "coefficient5_sensitivity_cd0_9": shear["coefficient5_isotropic_sensitivity_ratio"] / CD,
                             "RT_swap_sensitivity_cd0_9": shear.get("RT_swap_fixed_action_face_ratio", 0.0) / CD if aligned else None,
                             "shear_allowance_cd0_9_mpa": base["Fv_mpa"] * CD}
                    traces.append(trace)
                    body_traces.append(trace)
            summaries.append({"member": body, "references_cd1": base, "references_cd0_9": adjusted,
                              "stability_kernels_cd0_9": kernels,
                              "normal_peak": method.peak(body_traces, "timber_braced_normal_ratio_cd0_9"),
                              "shear_face_peak": method.peak(body_traces, "shear_face_ratio_cd0_9"),
                              "applicable_trace_count": len(body_traces),
                              "braced_normal_domain_or_strength_exceptions": sum(not t["timber_braced_domain_ok"] or t["timber_braced_normal_exceeds"] for t in body_traces),
                              "excluded_traces_per_state": sum(not r["status"].startswith("BORE_FREE_") for r in record["rectangle_at_station"]) * 2,
                              "complete_member_acceptance": False})
    require(len(balances) == 88 and traces, "two-state/44-member replay incomplete")
    return traces, summaries, balances, arrays


def run(output):
    """Parent-only mechanics entry point; output must be fresh and owned."""
    pins = source_pins()
    report = contract(pins)
    output = owned_output(output)
    (output / "producer.py.snapshot").write_bytes(Path(__file__).read_bytes())
    write(output / "inputs.json", report)
    states, responses, raw_states = [], {}, {}
    helper = None
    try:
        import numpy as np

        report["runtime_versions"] = {name: importlib.metadata.version(name) for name in ("numpy", "scipy", "osqp")}
        frame, helper, disk, bounds, member = load_helpers()
        member.frame_contract.force_state_scope(read(SOURCE / "comparison.json"))
        report["engineering_oracles"] = {"floor": frame.known_answer()}
        offset, coupon = disk.clearance_offsets(np.array([3.0, 4.0]), 2 * np.eye(2), 1.0)
        require(np.max(abs(offset - [.6, .8])) < 1e-8, "inherited disk known answer failed")
        report["engineering_oracles"]["disk"] = {"offset": offset.tolist(), **coupon}
        report["engineering_oracles_executed"] = True
        with np.load(FRAME / "operators.npz", allow_pickle=False) as data:
            operators = {key: data[key].copy() for key in ("H", "D", "e", "W", "F")}
        # Source gravity maps are case-specific floating decompositions, not
        # byte-identical columns. Compare at explicit inherited absolute guards;
        # retain the original column-zero e/W/F without averaging or repair.
        guards = {"e": helper.GAP_TOL, "W": 1.0e-12, "F": 1.0e-9}
        report["gravity_column_checks"] = {}
        for key, tolerance in guards.items():
            gravity = operators[key][:, ::2]
            require(np.isfinite(gravity).all(), "nonfinite gravity columns: " + key)
            differences = np.max(abs(gravity - gravity[:, :1]), axis=0)
            report["gravity_column_checks"][key] = {
                "case_ids": list(CASES), "source_columns": list(range(0, 12, 2)),
                "maximum_absolute_difference_by_case": differences.tolist(),
                "absolute_tolerance": tolerance, "relative_tolerance": 0.0,
                "units": "mm" if key == "e" else "scaled_N" if key == "W" else "N",
                "selected_original_column": 0, "column_values_modified": False,
            }
            require(float(differences.max()) <= tolerance, "gravity columns differ beyond inherited guard: " + key)
        rows = read(FRAME / "row-identities.json")
        H, D, e, W, k, uni, normals, tangents, transform, footprints = frame.lump_floor(
            *[operators[name] for name in ("H", "D", "e", "W")], rows)
        source = read(SOURCE / "comparison.json")
        require(footprints == source["floor_footprints"], "floor footprint contract changed")
        retained = [r for r in rows if r["ownership"]["second_body"] != "floor"]
        by_id = {}
        for i, row in enumerate(retained):
            by_id.setdefault(row["row_id"], []).append(i)
        pairs = [by_id[p["plane_id"]] for p in source["clearance_planes"]]
        require(all(len(pair) == 2 and pair[1] == pair[0] + 1 for pair in pairs),
                "clearance plane requires both adjacent signed components")
        targets = np.array([i for pair in pairs for i in pair])
        gaps = np.array([p["relative_radial_gap_mm"] for p in source["clearance_planes"]])
        require(len(rows) == 1888 and len(targets) == 176 and len(gaps) == 88, "current frame/gap census changed")
        for pair in targets.reshape(-1, 2):
            require(all(retained[i]["ownership"]["role"] == "candidate_bolt_lateral_plane" for i in pair)
                    and retained[pair[0]]["row_id"] == retained[pair[1]]["row_id"], "clearance pair identity mismatch")
        require(sum(r["ownership"]["role"] == "non_qualifying_parametric_screw_withdrawal" for r in retained) == 66, "Hillman census changed")
        matrices = ((H + H.T) / 2, D, report["dead_load_factor"] * e[:, 0],
                    report["dead_load_factor"] * W[:, 0], k, uni, normals, tangents)
        with np.load(SOURCE / "response.npz", allow_pickle=False) as saved:
            for gap_scale, suffix in ((0.0, "zero"), (1.0, "gap")):
                tag = "dead-only_" + suffix
                seed = transform @ saved[SEED_CASE + "_" + suffix + "_raw_force_n"]
                report["frame_solve"] = True
                f, q, a, audit, certificate = solve_state(helper, disk, bounds, matrices, targets, gaps, seed, gap_scale)
                raw = transform.T @ f
                raw_states[tag] = raw
                responses.update({tag + "_raw_force_n": raw, tag + "_lumped_q_mm": q, tag + "_rigid_coordinates": a})
                states.append({"case_id": "dead-only", "gap_scale": gap_scale, "audit": audit,
                               "status": "PASS_CONDITIONAL_LAWS_WITH_BOUNDED_SEATING" if certificate else "PASS_CONDITIONAL_COUPLED_FRAME_LAWS",
                               "fixed_force_clearance_certificate": certificate, **FLAGS})
                print(tag, "force balance N", audit["force_balance_n"], "moment balance N mm", audit["moment_balance_nmm"], flush=True)
        traces, summaries, balances, arrays = replay_members(member, operators, raw_states, pins)
        authenticate(pins)
        np.savez_compressed(output / "response.npz", **responses)
        np.savez_compressed(output / "member-actions.npz", **arrays)
        with (output / "same-cut-states.csv").open("w", newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=list(traces[0]))
            writer.writeheader()
            writer.writerows(traces)
        write(output / "body-balances.json", balances)
        report.update(status="COMPLETED_CONDITIONAL_DEAD_ONLY_COMPARISON", states=states, members=summaries,
                      applicable_cut_trace_count=len(traces), member_balance_count=len(balances),
                      engineering_oracles_executed=True, frame_solve=True,
                      source_sha256={str(p.relative_to(ROOT)): digest for p, digest in pins.items()},
                      output_sha256={name: sha(output / name) for name in ("response.npz", "member-actions.npz", "same-cut-states.csv", "body-balances.json", "producer.py.snapshot")})
        write(output / "comparison.json", report)
        return report
    except Exception as error:
        import numpy as np

        trace, terminal = error.__traceback__, {}
        while trace is not None:
            if helper is not None and trace.tb_frame.f_code is helper.solve.__code__:
                terminal = trace.tb_frame.f_locals
            trace = trace.tb_next
        np.savez_compressed(output / "unaccepted-iterate.npz",
                            **{name: terminal[name] for name in ("f", "q", "a") if name in terminal})
        np.savez_compressed(output / "partial-response.npz", **responses)
        write(output / "stop.json", {**report, "status": "STOP_DEAD_ONLY_COMPARISON",
                                    "terminal_exception": str(error), "completed_states": states,
                                    "audit_if_available": terminal.get("audit"),
                                    "partial_states_acceptance_transferred": False})
        raise


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--sourcepin-only", action="store_true")
    mode.add_argument("--run", action="store_true", help="parent-owned serialized execution")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.sourcepin_only:
        pins = source_pins()
        output = owned_output(args.output)
        write(output / "api-freeze.json", contract(pins))
        (output / "producer.py.snapshot").write_bytes(Path(__file__).read_bytes())
        print("PASS_SOURCEPINS_ONLY", sha(Path(__file__)), "pins", len(pins))
        return
    lock = ROOT / "docs/wood-joints-mvp/luna-max-native-run-ledger.lock"
    with lock.open("r") as stream:
        fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
        require(read(lock.with_suffix(".json"))["slot"]["state"] == "idle", "shared mechanics slot occupied")
        run(args.output)


if __name__ == "__main__":
    main()
