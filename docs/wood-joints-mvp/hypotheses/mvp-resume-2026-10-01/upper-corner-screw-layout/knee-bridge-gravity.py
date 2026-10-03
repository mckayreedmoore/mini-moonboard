"""Prepare planning-gravity operators from the unadopted knee-bridge manifest.

The parent calls build(output). Import performs no calculations or writes.
Only the two original spine elastic quotients are solved; no frame, native,
CAD, mesh, stiffness assembly, helper pipeline or coupon is run.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import json
import math
import shutil
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
SOURCE = HERE / "operators-attempt02"
RAW = HERE / "rawlocal/knee-bridge-gravity"
INTEGRATION = HERE / "rawlocal/knee-bridge-integration/attempt02"
ASSEMBLY = HERE.parent / "assembly-package"
BASE = ROOT / "docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28"
PARSER = BASE / "current-frame-pure-solid-export-assessment-method-attempt01/assess_matrixstorage.py"
CONDENSATION = BASE / "current-frame-free-body-condensation-preflight-attempt01/condensation.py"
QUOTIENT = BASE / "current-elastic-quotient-method-preflight-attempt02/quotient_method.py"
REFINEMENT = BASE / "current-bordered-refinement-diagnostic-attempt01/bounded_refinement.py"
SOURCE_MODEL = BASE / "current-springa-frame-input-adapter-attempt01/a12-rear/model.json"
NATIVE = BASE / "current-frame-pure-solid-matrix-export-native-attempt01"
WRENCH_METHOD = ROOT / "fea/horizontal_panel_frame.py"
PANEL_DEPENDENCY = ROOT / "fea/vertical_panel_comparison.py"
FIT = ASSEMBLY / "rawlocal/knee-bridge-fit/prepare-attempt02/setup.json"
ORDER = ASSEMBLY / "rawlocal/knee-bridge-order/attempt01/proposal-order.json"
BODIES = ("knee_outer_left_spine", "knee_outer_right_spine")
CASES = ("a12-rear", "a12-forward", "a12-left", "k12-right", "k12-rear", "a1-rear")
G = 9.80665
FORCE_TOL = MOMENT_TOL = 1e-5
MASS_TOL = 1e-12
PINS = {
    INTEGRATION / "manifest.json": "1744bb616354159c06694e99fb239251578dba3a6e860da5391dae19b5d7026c",
    INTEGRATION / "receipt.json": "8a2813419289bee46e2e0985ab702a602a8ff3a0d3aacdd43d1aad841c92c8df",
    HERE / "knee-bridge-integration.py": "46b6966fe215408540acf636afa7e7638c2679d825f687c23eedac47c706ac46",
    SOURCE / "operator-assessment.json": "1a82cd2adbfece3942bf8c90f593f1e21a150adb65db625135aadd258fd5024a",
    REFINEMENT: "ee23cf09dc89b6a4c6581ea86379e0749c2c6559478da1e2f95a8a0b8b599c4e",
    PANEL_DEPENDENCY: "e3079c6d82219ccc255905a38f4b61bb0354bfd52454f490b1590dc8fa0e79ea",
}
FLAGS = {
    "proposal_adopted": False,
    "current_geometry_changed": False,
    "current_global_operator_files_changed": False,
    "authority_changed": False,
    "stiffness_recomputed": False,
    "H_D_B_connector_rows_and_k_unchanged": True,
    "actual_new_hole_stiffness_qualified": False,
    "global_compatibility_acceptance_transferred": False,
    "global_compatibility_asserted": False,
    "compatibility_unsolved": True,
    "physical_release": False,
    "complete_joint_acceptance": False,
    "hardware_capacity_qualified": False,
    "fabrication_authorized": False,
    "new_receiver_interface_added": False,
    "new_internal_bolt_stiffness_rows_added": False,
    "floor_restraint_added": False,
    "native_launch": False,
    "native_solve_run": False,
    "frame_solve_run": False,
    "CAD_run_executed": False,
    "helper_pipelines_or_coupons_run": False,
    "tests_or_review_run": False,
}


def require(condition, message):
    if not condition:
        raise ValueError(f"STOP: {message}")


def sha(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def key(path):
    return Path(path).resolve().relative_to(ROOT).as_posix()


def read(path):
    return json.loads(Path(path).read_text())


def dump(path, record):
    Path(path).write_text(json.dumps(record, indent=2, sort_keys=True, allow_nan=False) + "\n")


def pure_module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    require(spec is not None and spec.loader is not None, f"saved implementation unavailable: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def build(output):
    """Write operator-ready files directly in one fresh immediate RAW child.

    A failed unchanged quotient audit emits a STOP receipt and no updated
    operator files. Original source records are never modified.
    """
    output = Path(output).resolve()
    require(output.parent == RAW.resolve() and not output.exists(), "output must be a fresh immediate child")
    pins = {}

    def pin(path, expected):
        path = Path(path).resolve()
        require(path.is_relative_to(ROOT), f"source leaves repository: {path}")
        require(path not in pins or pins[path] == expected, f"conflicting source pin: {path}")
        require(sha(path) == expected, f"consumed source differs: {path}")
        pins[path] = expected

    def authenticate():
        for path, expected in pins.items():
            require(sha(path) == expected, f"source changed during preparation: {path}")

    def ref(path, pointer=""):
        return {"source": key(path), "sha256": pins[Path(path).resolve()], "record_pointer": pointer}

    for path, expected in PINS.items():
        pin(path, expected)
    pin(Path(__file__), sha(__file__))
    integration, integration_receipt = read(INTEGRATION / "manifest.json"), read(INTEGRATION / "receipt.json")
    source_assessment = read(SOURCE / "operator-assessment.json")
    require(integration["schema"] == "knee-bridge-unadopted-integration/v1"
            and integration["proposal_adopted"] is False, "expected unadopted integration")
    require(integration_receipt["output_sha256"]["manifest.json"] == PINS[INTEGRATION / "manifest.json"]
            and integration_receipt["source_sha256"] == integration["source_sha256"], "integration receipt binding differs")
    require(integration["producer_sha256"] == PINS[HERE / "knee-bridge-integration.py"], "integration producer differs")
    for name, expected in integration_receipt["output_sha256"].items():
        require(Path(name).name == name, "integration artifact leaves its packet")
        pin(INTEGRATION / name, expected)
    require(source_assessment["status"] == "PASS_UPDATED_ELASTIC_FRAME_OPERATORS", "original operators are incomplete")
    require(any("filled-bore gross stiffness" in limit.lower() for limit in source_assessment["limits"]),
            "original filled-bore gross stiffness declaration is missing")
    for name, expected in source_assessment["output_sha256"].items():
        require(Path(name).name == name, "source operator artifact leaves its packet")
        pin(SOURCE / name, expected)
    for path in (PARSER, CONDENSATION, QUOTIENT, SOURCE_MODEL, NATIVE / "model.sti", NATIVE / "model.dof", WRENCH_METHOD):
        require(key(path) in source_assessment["source_sha256"], f"audited implementation/stiffness pin missing: {path}")
        pin(path, source_assessment["source_sha256"][key(path)])
    for path in (FIT, ORDER):
        pin(path, integration["source_sha256"][key(path)])
    for binding in integration["frame_authority_unchanged"].values():
        pin(ROOT / binding["source"], binding["sha256"])
    for binding in integration["authority"]["files_unchanged"]:
        pin(ROOT / binding["source"], binding["sha256"])
    for binding in integration["geometry"]["STEP_overrides"]:
        for field in ("current_step", "proposal_step"):
            pin(ROOT / binding[field]["path"], binding[field]["sha256"])
    for field, path in (("operators_unchanged", SOURCE / "operators.npz"),
                        ("model_inputs_unchanged", SOURCE / "model-inputs.json")):
        binding = integration[field]
        require(binding["source"] == key(path) and binding["sha256"] == pins[path.resolve()], "integration/operator source differs")
    model, inputs, fit, order = [read(path) for path in (SOURCE / "model.json", SOURCE / "model-inputs.json", FIT, ORDER)]
    require(integration["mass_planning_convention"] == order["mass_planning_convention"], "mass convention differs")
    require(integration["source_load_identity"] == {
        "source_climber_weight_lb": 250, "source_dynamic_factor": 2,
        "source_horizontal_force_magnitude_n": 300, "source_hold_lever_mm": 100}, "live-load identity differs")
    require(integration["case_ids"] == [case["case_id"] for case in inputs["cases"]] == list(CASES), "six-case ordering differs")
    require(integration["census"]["new_internal_bolt_axes"] == 4
            and integration["census"]["total_unique_proposal_bolt_axes"] == 108, "integration axis census differs")
    convention = order["mass_planning_convention"]
    require(model["modeled_mass_kg"] == source_assessment["modeled_mass_kg"] == convention["frozen_modeled_frame_mass_kg"],
            "original modeled mass differs")
    require(model["planning_accessory_mass_kg"] == convention["equipment_mass_separate_kg"] == 25, "25 kg allowance differs")
    require(model["dead_load_factor"] == source_assessment["dead_load_factor"], "original deadfactor differs")
    authenticate()
    source_hashes = {key(path): expected for path, expected in sorted(pins.items())}
    output.mkdir(parents=True, exist_ok=False)
    (output / ".gitignore").write_text("*\n")
    (output / "producer.py.snapshot").write_bytes(Path(__file__).read_bytes())
    dump(output / "inputs.json", {"schema": "knee-bridge-gravity-preparation-inputs/v1", "source_sha256": source_hashes,
                                  "integration": ref(INTEGRATION / "manifest.json"),
                                  "source_operator_assessment": ref(SOURCE / "operator-assessment.json"),
                                  "inherited_source_sha256_provenance_only": source_assessment["source_sha256"],
                                  "source_method_records_modified": False, "source_authentication_before_after": True, **FLAGS})
    debug = {"stage": "frozen-inputs", "body_reports": []}
    previous_bytecode, previous_path = sys.dont_write_bytecode, sys.path[:]
    try:
        sys.dont_write_bytecode = True
        sys.path.insert(0, str(ROOT))
        # Import definitions only; no earlier main/build/prepare/audit pipeline.
        import numpy as np
        import scipy
        from scipy import sparse

        wrench_method = pure_module(WRENCH_METHOD, "knee_gravity_wrench_method")
        parser = pure_module(PARSER, "knee_gravity_matrix_parser")
        helper = pure_module(CONDENSATION, "knee_gravity_condensation")
        quotient = pure_module(QUOTIENT, "knee_gravity_quotient")

        def array_sha(array):
            value = np.asarray(array)
            digest = hashlib.sha256(f"{value.dtype.str}:{value.shape}".encode())
            digest.update(value.tobytes(order="C"))
            return digest.hexdigest()

        def fingerprint(value):
            return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest()

        def close(actual, expected, context, tolerance):
            first, second = np.asarray(actual), np.asarray(expected)
            require(first.shape == second.shape and np.isfinite(first).all() and np.isfinite(second).all()
                    and np.max(np.abs(first - second), initial=0) <= tolerance, context)

        def wrench_check(actual, expected, context):
            close(actual[:3], expected[:3], context + ": force differs", FORCE_TOL)
            close(actual[3:], expected[3:], context + ": moment differs", MOMENT_TOL)
            return {"force_error_n": float(np.max(np.abs(actual[:3] - expected[:3]))),
                    "moment_error_nmm": float(np.max(np.abs(actual[3:] - expected[3:]))),
                    "actual_wrench_n_nmm": actual.tolist(), "expected_wrench_n_nmm": expected.tolist()}

        hardware = fit["proposal"]["stock_and_component_envelopes"]
        length = hardware["stock"]["nominal_underhead_length_mm"]
        require(length == 165.1 and convention["steel_density_kg_m3"] == 7850
                and convention["wood_density_kg_m3"] == 600, "declared stock/density convention differs")
        od, inside, washer_t = hardware["washer"]["OD_ID_thickness_mm"]
        head_h, nut_h = hardware["head"]["height_max_mm"], hardware["nut"]["height_range_mm"][1]
        disk = math.pi * 6.35 ** 2 / 4
        hex_area = lambda af: math.sqrt(3) * af ** 2 / 2
        volumes = {
            "one_nominal_shaft_mm3": disk * length,
            "one_full_hex_head_mm3": hex_area(hardware["head"]["across_flats_max_mm"]) * head_h,
            "one_nominal_bored_hex_nut_mm3": (hex_area(hardware["nut"]["across_flats_max_mm"]) - disk) * nut_h,
            "one_annular_washer_mm3": math.pi * (od ** 2 - inside ** 2) / 4 * washer_t,
        }
        for name, volume in volumes.items():
            close([volume], [convention["component_volumes_mm3"][name]], "component volume differs: " + name, 1e-9)
        components = []
        axes = integration["proposed_internal_bolt_axes"]
        require(len(axes) == 4 and {axis["body"] for axis in axes} == set(BODIES), "two-spine/four-stack coverage differs")
        for axis in axes:
            body, axis_id = axis["body"], axis["axis_id"]
            matches = [stack for stack in fit["stacks"] if stack["axis_id"] == axis["fit_axis_id"]
                       and stack["proposed_bore"]["block"] == body
                       and stack["local_center_grain_u_mm"] == axis["center_local_guv_mm"][:2]]
            require(len(matches) == 1, "canonical body/station alias binding differs")
            stack = matches[0]
            direction = np.array(axis["axis_unit_global_xyz"], dtype=float)
            seats = {seat["end_v_sign"]: np.array(seat["center_xyz_mm"]) for seat in axis["end_seats"]}
            require(set(seats) == {-1, 1}, "canonical end seats differ")
            close(direction, stack["nut_direction_global_xyz"], "fit axis direction differs", 1e-12)
            close(seats[-1], stack["head_wood_face_xyz_mm"], "head seat differs", 1e-6)
            close(seats[1], stack["nut_wood_face_xyz_mm"], "nut seat differs", 1e-6)
            underhead = seats[-1] - washer_t * direction
            close(underhead, stack["underhead_xyz_mm"], "underhead coordinate differs", 1e-6)
            specs = (
                ("shaft", "one_nominal_shaft_mm3", underhead + length / 2 * direction, "installed_165.1_mm_stock"),
                ("head", "one_full_hex_head_mm3", underhead - head_h / 2 * direction, "installed"),
                ("head_washer", "one_annular_washer_mm3", seats[-1] - washer_t / 2 * direction, "installed"),
                ("nut_washer", "one_annular_washer_mm3", seats[1] + washer_t / 2 * direction, "installed"),
                ("nut", "one_nominal_bored_hex_nut_mm3", seats[1] + (washer_t + nut_h / 2) * direction, "installed"),
            )
            for role, volume_key, center, operation in specs:
                query_matches = [q for q in fit["queries"] if q["axis_id"] == stack["axis_id"]
                                 and q["component"] == role and q["operation"] == operation]
                require(len(query_matches) == 1, f"installed component is ambiguous: {axis_id}/{role}")
                cylinder = query_matches[0]["cylinder"]
                query_center = np.array(cylinder["start_xyz_mm"]) + cylinder["length_mm"] / 2 * np.array(cylinder["direction_xyz"])
                close(center, query_center, "installed component center differs", 1e-6)
                mass = volumes[volume_key] * convention["steel_density_kg_m3"] / 1e9
                force = np.array([0.0, 0.0, -G * mass])
                components.append({"body": body, "canonical_axis_id": axis_id, "fit_axis_id": stack["axis_id"],
                                   "role": role, "signed_mass_delta_kg": mass, "volume_mm3": volumes[volume_key],
                                   "density_kg_m3": 7850, "center_xyz_mm": center.tolist(), "force_xyz_n": force.tolist(),
                                   "global_origin_wrench_n_nmm": np.r_[force, np.cross(center, force)].tolist()})
            wood_span = axis["nominal_shaft_record"]["wood_span_mm"]
            close(seats[1] - seats[-1], wood_span * direction, "canonical wood span differs", 1e-6)
            close(axis["center_global_xyz_mm"], (seats[-1] + seats[1]) / 2, "bore center differs", 1e-6)
            require(axis["bore_envelope_diameter_mm"] == 7.5, "removed cylinder diameter differs")
            volume = math.pi * (axis["bore_envelope_diameter_mm"] / 2) ** 2 * wood_span
            mass = -volume * convention["wood_density_kg_m3"] / 1e9
            center, force = np.array(axis["center_global_xyz_mm"]), np.array([0.0, 0.0, -G * mass])
            components.append({"body": body, "canonical_axis_id": axis_id, "fit_axis_id": stack["axis_id"],
                               "role": "removed_wood_cylinder", "signed_mass_delta_kg": mass, "volume_mm3": volume,
                               "density_kg_m3": 600, "center_xyz_mm": center.tolist(), "force_xyz_n": force.tolist(),
                               "global_origin_wrench_n_nmm": np.r_[force, np.cross(center, force)].tolist()})
        require(len(components) == 24, "expected 20 hardware components and four removed cylinders")
        steel_mass = math.fsum(row["signed_mass_delta_kg"] for row in components if row["role"] != "removed_wood_cylinder")
        wood_mass = -math.fsum(row["signed_mass_delta_kg"] for row in components if row["role"] == "removed_wood_cylinder")
        mass_delta = steel_mass - wood_mass
        close([steel_mass, wood_mass, mass_delta], [convention["added_hardware_mass_kg"], convention["removed_wood_mass_kg"],
                                                 convention["net_mass_delta_kg"]], "planning mass reconciliation differs", MASS_TOL)
        close([mass_delta], [0.24795882906138145], "declared net planning mass differs", MASS_TOL)
        global_delta = np.sum([row["global_origin_wrench_n_nmm"] for row in components], axis=0)
        body_delta = {body: np.sum([row["global_origin_wrench_n_nmm"] for row in components if row["body"] == body], axis=0)
                      for body in BODIES}
        new_mass = model["modeled_mass_kg"] + mass_delta
        new_deadfactor = (new_mass + 25) / new_mass
        close([model["dead_load_factor"]], [(model["modeled_mass_kg"] + 25) / model["modeled_mass_kg"]],
              "original proportional allowance differs", 1e-14)
        source = parser.load_frame_source_model(SOURCE_MODEL)
        labels = parser.parse_dof_file(NATIVE / "model.dof")
        require(list(source["bodies"]) == model["body_names"], "source stiffness body ordering differs")
        row_for = {label: i for i, label in enumerate(labels)}
        require(len(row_for) == len(labels), "duplicate physical DOF labels")
        owners = np.array([source["owner_by_node"][node] for node, _ in labels])
        coordinates = {int(node): np.array(point) for node, point in model["physical_node_coordinates_mm"].items()}
        parsed = parser.parse_upper_triangle_file(NATIVE / "model.sti", len(labels), owner_by_row=owners, owner_names=model["body_names"])
        parser.require_no_cross_body_coupling(parsed)
        stiffness = parsed["matrix"]
        projection = sparse.load_npz(SOURCE / "B.npz").tocsr()
        with np.load(SOURCE / "operators.npz", allow_pickle=False) as data:
            original = {name: data[name].copy() for name in data.files}
        require(all(name in original for name in ("H", "D", "F", "e", "W")), "source operator arrays missing")
        require(original["F"].shape == (len(labels), 12) and original["e"].shape == (projection.shape[0], 12)
                and original["W"].shape == (6 * len(model["body_names"]), 12)
                and projection.shape[1] == len(labels), "physical/operator dimensions differ")
        operators = {name: value.copy() for name, value in original.items()}
        delta_F = np.zeros_like(original["F"][:, 0])
        delta_e, delta_W = np.zeros_like(original["e"][:, 0]), np.zeros_like(original["W"][:, 0])
        touched = set()
        reports = []
        for body in BODIES:
            debug["stage"], debug["body"] = "two-spine-audited-quotient", body
            body_id = model["body_names"].index(body)
            dofs = np.flatnonzero(owners == body_id)
            body_labels = [labels[int(i)] for i in dofs]
            nodes = sorted({node for node, _ in body_labels})
            require(set(nodes) == set(model["body_nodes"][body]) == source["bodies"][body], "spine node ownership differs")
            require(all(np.array_equal(coordinates[node], source["coordinates"][node]) for node in nodes),
                    "existing audited quotient cannot be reused: spine physical coordinates changed")
            center, rigid, orthonormal = helper.rigid_basis(body_labels, coordinates)
            rigid_error = float(np.max(np.abs(projection[:, dofs] @ rigid - original["D"][:, 6 * body_id:6 * body_id + 6])))
            require(rigid_error < 1e-8, "existing audited quotient cannot be reused: current B/D rigid mapping differs")
            positions = np.array([coordinates[node] for node in nodes])
            nodal = np.zeros((len(nodes), 3))
            # Same least-norm statically equivalent distributor as corner_frame;
            # the component inventory preserves every geometric center/wrench.
            for component in (row for row in components if row["body"] == body):
                force = np.array(component["force_xyz_n"])
                moment = np.cross(np.array(component["center_xyz_mm"]) - center, force)
                nodal += wrench_method.distribute_wrench(positions, force, moment, center)
            local_rows = {label: i for i, label in enumerate(body_labels)}
            raw = np.zeros((len(dofs), 1))
            for node, value in zip(nodes, nodal, strict=True):
                for direction in (1, 2, 3):
                    local = local_rows[node, direction]
                    raw[local, 0] = value[direction - 1]
                    delta_F[row_for[node, direction]] = value[direction - 1]
            mapped = np.r_[nodal.sum(axis=0), np.cross(positions, nodal).sum(axis=0)]
            mapped_check = wrench_check(mapped, body_delta[body], body + " distributed component gravity")
            old_work = rigid.T @ original["F"][dofs, 0::2]
            close(old_work, original["W"][6 * body_id:6 * body_id + 6, 0::2], "original spine W mapping differs", 1e-7)
            elastic = raw - orthonormal @ (orthonormal.T @ raw)
            body_K = stiffness[dofs][:, dofs].tocsr()
            factor, system = helper.factor_bordered(body_K, rigid)
            solved = quotient.solve_quotient_chunk(factor, system, body_K, rigid, elastic)
            audit = {name: value for name, value in solved.items() if name != "displacement_mm"}
            report = {"body": body, "physical_dofs": len(dofs), "quotient_rhs_columns": 1,
                      "datum_xyz_mm": center.tolist(), "current_B_D_rigid_map_error": rigid_error,
                      "old_W_reproduction_error_scaled_n": float(np.max(np.abs(old_work - original["W"][6 * body_id:6 * body_id + 6, 0::2]))),
                      "component_gravity_wrench_check": mapped_check, "quotient_audit": audit}
            reports.append(report)
            debug["body_reports"] = reports
            require(solved["status"] == quotient.PASS_ELASTIC_QUOTIENT_SCREEN,
                    f"existing audited quotient cannot be reused for {body}: {solved['status']}; no updated e/operator emitted")
            displacement = np.asarray(solved["displacement_mm"])
            require(displacement.shape == raw.shape and np.isfinite(displacement).all(), "audited elastic displacement is unavailable")
            delta_e += np.asarray(projection[:, dofs] @ displacement)[:, 0]
            delta_W[6 * body_id:6 * body_id + 6] = (rigid.T @ raw)[:, 0]
            touched.update(int(i) for i in dofs)
            report["elastic_delta_e_maximum_mm"] = float(np.max(np.abs(projection[:, dofs] @ displacement)))
        require(len(reports) == 2, "two-spine quotient coverage differs")
        operators["F"][:, 0::2] += delta_F[:, None]
        operators["e"][:, 0::2] += delta_e[:, None]
        operators["W"][:, 0::2] += delta_W[:, None]
        unchanged = {}
        for name, value in operators.items():
            old, new = (original[name][:, 1::2], value[:, 1::2]) if name in ("F", "e", "W") else (original[name], value)
            require(array_sha(old) == array_sha(new), "unchanged array/live columns differ: " + name)
            unchanged[name + ("/live_columns" if name in ("F", "e", "W") else "")] = array_sha(old)
        untouched_dofs = np.array(sorted(set(range(len(labels))) - touched), dtype=int)
        require(array_sha(original["F"][untouched_dofs]) == array_sha(operators["F"][untouched_dofs]), "gravity outside two spines changed")
        untouched_bodies = [i for i, body in enumerate(model["body_names"]) if body not in BODIES]
        untouched_work = np.array([6 * i + j for i in untouched_bodies for j in range(6)])
        require(array_sha(original["W"][untouched_work]) == array_sha(operators["W"][untouched_work]), "rigid gravity outside two spines changed")

        nodes = sorted({node for node, _ in labels})
        node_dofs = np.array([[row_for[node, d] for d in (1, 2, 3)] for node in nodes])
        positions = np.array([coordinates[node] for node in nodes])
        centers = np.array([np.mean([coordinates[int(node)] for node in sorted(set(model["body_nodes"][body]))], axis=0)
                            for body in model["body_names"]])

        def nodal_wrench(values, column):
            forces = values["F"][node_dofs, column]
            return np.r_[forces.sum(axis=0), np.cross(positions, forces).sum(axis=0)]

        def work_wrench(values, column):
            work = values["W"][:, column].reshape(-1, 6)
            return np.r_[work[:, :3].sum(axis=0), (1000 * work[:, 3:] + np.cross(centers, work[:, :3])).sum(axis=0)]

        global_checks = []
        for i, case in enumerate(CASES):
            old_f, new_f = nodal_wrench(original, 2 * i), nodal_wrench(operators, 2 * i)
            old_w, new_w = work_wrench(original, 2 * i), work_wrench(operators, 2 * i)
            checks = {"case_id": case, "raw_F_delta": wrench_check(new_f - old_f, global_delta, "global gravity F delta"),
                      "raw_W_delta": wrench_check(new_w - old_w, global_delta, "global gravity W delta"),
                      "target_F_W": wrench_check(new_f, new_w, "global gravity F/W"),
                      "new_deadfactor": new_deadfactor,
                      "factored_gravity_global_wrench_n_nmm": (new_deadfactor * new_f).tolist(),
                      "proportional_equipment_global_wrench_n_nmm": ((new_deadfactor - 1) * new_f).tolist()}
            close(old_f[:3], [0, 0, -G * model["modeled_mass_kg"]], "original gravity/modeled mass differs", FORCE_TOL)
            close(new_f[:3], [0, 0, -G * new_mass], "target gravity/modeled mass differs", FORCE_TOL)
            close((new_deadfactor * new_f)[:3], [0, 0, -G * (new_mass + 25)], "factored gravity mass differs", FORCE_TOL)
            checks["factored_total_delta"] = wrench_check(new_deadfactor * new_f - model["dead_load_factor"] * old_f,
                                                         new_deadfactor * (old_f + global_delta) - model["dead_load_factor"] * old_f,
                                                         "factored full global F/M delta")
            global_checks.append(checks)

        seed = {"status": "NUMERICAL_SEED_ONLY", "role": "NUMERICAL_SEED_ONLY",
                "source_comparison": integration["frame_authority_unchanged"]["comparison"],
                "source_response": integration["frame_authority_unchanged"]["response"],
                "source_cases_and_response_are_initial_guesses_only": True,
                "source_modeled_mass_kg": model["modeled_mass_kg"], "source_dead_load_factor": model["dead_load_factor"],
                "target_operator_file": "operators.npz", "target_modeled_mass_kg": new_mass,
                "target_dead_load_factor": new_deadfactor, "accepted_force_source": False,
                "target_gravity_and_deadfactor_must_replace_source_bookkeeping": True,
                "global_compatibility_acceptance_transferred": False, "frame_solve_run": False}
        scope = {"integration_reference": ref(INTEGRATION / "manifest.json"), "mass_convention": convention,
                 "components": components, "net_mass_delta_kg": mass_delta, "global_origin_gravity_delta_n_nmm": global_delta.tolist(),
                 "body_gravity_delta_n_nmm": {body: value.tolist() for body, value in body_delta.items()},
                 "modeled_mass_kg": new_mass, "dead_load_factor": new_deadfactor, "planning_accessory_mass_kg": 25,
                 "stiffness_idealization": "Unchanged FILLED-BORE GROSS elastic approximation; not actual changed-hole stiffness.",
                 "raw_gravity_columns_include_equipment": False,
                 "replay_gravity_rule": "new_dead_load_factor * gravity_column + unchanged_live_column",
                 "proportional_equipment_convention_retained": True,
                 "nodal_mapping": "Existing distribute_wrench on original current spine nodes; component forces and geometric moments retained.",
                 "elastic_method": "Two original native-K bordered quotients with unchanged audit/refinement gates; delta e = current B times audited elastic displacement.",
                 "new_internal_bridge_bolts_have_no_operator_rows": True,
                 "new_geometry_reference": ref(INTEGRATION / "manifest.json", "/geometry"),
                 "global_checks": global_checks, **FLAGS}
        new_model, new_inputs = copy.deepcopy(model), copy.deepcopy(inputs)
        new_model.update(modeled_mass_kg=new_mass, dead_load_factor=new_deadfactor,
                         knee_bridge_planning_gravity=scope, numerical_seed_only=seed)
        new_inputs.update(modeled_mass_kg=new_mass, dead_load_factor=new_deadfactor, planning_accessory_mass_kg=25,
                          knee_bridge_planning_gravity=scope, numerical_seed_only=seed,
                          derived_from_gravity_source_model_inputs_sha256=pins[(SOURCE / "model-inputs.json").resolve()])
        for body in BODIES:
            for component in (row for row in components if row["body"] == body):
                new_inputs["assigned_gravity_by_member"][body].append({
                    "source_name": component["canonical_axis_id"] + "/" + component["role"],
                    "mass_kg": component["signed_mass_delta_kg"], "point_xyz_mm": component["center_xyz_mm"],
                    "force_xyz_n": component["force_xyz_n"], "receiver_member_ids": [body],
                    "source_entity_kind": "unadopted_planning_gravity_delta", "signed_mass_bookkeeping": True})
        # Bind complete case loads to the new operators, carrying the unchanged
        # source live-load definition. Older case metadata remains source provenance.
        for i, case in enumerate(new_inputs["cases"]):
            body_wrenches = []
            for body_id, body in enumerate(model["body_names"]):
                dofs = np.flatnonzero(owners == body_id)
                local_nodes = sorted({labels[int(d)][0] for d in dofs})
                nd = np.array([[row_for[node, d] for d in (1, 2, 3)] for node in local_nodes])
                xyz = np.array([coordinates[node] for node in local_nodes])
                force = operators["F"][nd, 2 * i] + operators["F"][nd, 2 * i + 1]
                body_wrenches.append({"member_id": body, "reference_xyz_mm": centers[body_id].tolist(),
                                      "assigned_external_force_xyz_n": force.sum(axis=0).tolist(),
                                      "assigned_external_moment_xyz_nmm": np.cross(xyz - centers[body_id], force).sum(axis=0).tolist(),
                                      "scope": "Unfactored gravity plus unchanged live nodal loads; equipment enters through new deadfactor."})
            case["body_external_wrenches"] = body_wrenches
            total = nodal_wrench(operators, 2 * i) + nodal_wrench(operators, 2 * i + 1)
            case["including_deferred_hardware_force_xyz_n"] = total[:3].tolist()
            case["including_deferred_hardware_moment_about_origin_xyz_nmm"] = total[3:].tolist()
            case["operator_load_scope"] = "Current retained gravity bookkeeping plus explicit bridge delta; unscaled 25 kg allowance is separate."
            require(case["source_applied_load"] == inputs["cases"][i]["source_applied_load"], "a live-load definition changed")
        for field in ("connections", "members", "finite_contact_candidates", "zero_area_or_unresolved_contacts"):
            require(fingerprint(new_inputs[field]) == fingerprint(inputs[field]), "geometry/connector metadata changed: " + field)
        for field in ("body_nodes", "physical_node_coordinates_mm", "physical_elements", "material_binding", "owner_authorized_screw_movements"):
            require(fingerprint(new_model[field]) == fingerprint(model[field]), "operator geometry/material metadata changed: " + field)
        authenticate()
        debug["stage"] = "write-operator-ready-child"
        np.savez_compressed(output / "operators.npz", **operators)
        for name in ("B.npz", "row-identities.json"):
            shutil.copyfile(SOURCE / name, output / name)
            require(sha(output / name) == pins[(SOURCE / name).resolve()], "unchanged file copy differs: " + name)
        dump(output / "model.json", new_model)
        dump(output / "model-inputs.json", new_inputs)
        result = {"operator_ready": True, "gravity_delta_in_proposal_operators": True,
                  "modeled_mass_kg": new_mass, "dead_load_factor": new_deadfactor, "planning_accessory_mass_kg": 25,
                  "net_mass_delta_kg": mass_delta, "component_count": 24, "gravity_body_quotients": reports,
                  "planning_gravity": scope, "numerical_seed_only": seed,
                  "unchanged_array_sha256": unchanged,
                  "unchanged_file_sha256": {name: sha(output / name) for name in ("B.npz", "row-identities.json")},
                  "runtime": {"python": sys.version.split()[0], "numpy": np.__version__, "scipy": scipy.__version__}}
    except Exception as error:
        # A rejected quotient never gets a rigid-only substitute or ready status.
        failure = {"error": str(error), "last_stage": debug, "operator_ready": False,
                   "gravity_delta_in_proposal_operators": False}
        authenticate()
        failure_files = {p.name: sha(p) for p in output.iterdir() if p.is_file()}
        record = {"schema": "knee-bridge-gravity-operators/v1", "status": "STOP_KNEE_BRIDGE_GRAVITY_PREPARATION",
                  "source_sha256": source_hashes, "output_sha256": failure_files,
                  "failure": failure, "producer_sha256": pins[Path(__file__).resolve()], **FLAGS}
        dump(output / "operator-assessment.json", record)
        failure_files["operator-assessment.json"] = sha(output / "operator-assessment.json")
        dump(output / "receipt.json", {"schema": "knee-bridge-gravity-receipt/v1", "status": record["status"],
                                       "source_sha256": source_hashes, "output_sha256": failure_files,
                                       "sources_authenticated_before_and_after": True, "failure": failure, **FLAGS})
        raise ValueError(f"STOP: knee-bridge gravity preparation failed; see {output / 'operator-assessment.json'}: {error}") from error
    finally:
        sys.dont_write_bytecode = previous_bytecode
        sys.path[:] = previous_path
    authenticate()
    require(sha(output / "producer.py.snapshot") == pins[Path(__file__).resolve()], "producer snapshot differs")
    names = (".gitignore", "producer.py.snapshot", "inputs.json", "operators.npz", "B.npz",
             "row-identities.json", "model.json", "model-inputs.json")
    output_hashes = {name: sha(output / name) for name in names}
    assessment = {"schema": "knee-bridge-gravity-operators/v1", "status": "PASS_UPDATED_ELASTIC_FRAME_OPERATORS",
                  "producer_sha256": pins[Path(__file__).resolve()], "source_sha256": source_hashes,
                  "output_sha256": dict(output_hashes), "derived_from_operator_assessment_schema": source_assessment["schema"],
                  "source_authentication_before_after": True, "case_ids": list(CASES), **result, **FLAGS,
                  "limits": [
                      "H/D/B, connector row identities and constitutive k remain unchanged FILLED-BORE gross approximations; no actual new-hole stiffness is claimed.",
                      "Only raw gravity F/e/W columns change. All live columns and their 250 lb times two, signed 300 N and 100 mm lever remain bitwise equal.",
                      "Twenty geometric hardware-center masses and four removed bore-center masses follow the declared planning convention; actual hardware mass is unmeasured.",
                      "Two unchanged original-native-K quotients retain the full existing audit gates. A failed quotient stops preparation; no rigid-only e substitute is supplied.",
                      "The same proportional 25 kg equipment convention uses the new modeled mass and deadfactor; no equipment placement variant is introduced.",
                      "Old pinned cases/response are NUMERICAL_SEED_ONLY. No frame result, accepted force allocation or global compatibility is transferred.",
                      "Source model-input member descriptors remain inherited provenance; the unadopted effective STEP overlay is bound separately by the integration reference.",
                  ]}
    dump(output / "operator-assessment.json", assessment)
    output_hashes["operator-assessment.json"] = sha(output / "operator-assessment.json")
    authenticate()
    dump(output / "receipt.json", {"schema": "knee-bridge-gravity-receipt/v1", "status": assessment["status"],
                                   "producer_sha256": pins[Path(__file__).resolve()], "source_sha256": source_hashes,
                                   "output_sha256": output_hashes, "sources_authenticated_before_and_after": True,
                                   "modeled_mass_kg": result["modeled_mass_kg"], "dead_load_factor": result["dead_load_factor"],
                                   "net_mass_delta_kg": result["net_mass_delta_kg"], "operator_ready": True, **FLAGS})
    authenticate()
    for name, expected in output_hashes.items():
        require(sha(output / name) == expected, "receipt-bound output changed: " + name)
    return {"status": assessment["status"], "output": str(output), "operator_ready": True,
            "operator_assessment_sha256": output_hashes["operator-assessment.json"], "receipt_sha256": sha(output / "receipt.json"),
            "modeled_mass_kg": result["modeled_mass_kg"], "dead_load_factor": result["dead_load_factor"],
            "net_mass_delta_kg": result["net_mass_delta_kg"], **FLAGS}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    print(json.dumps(build(parser.parse_args().output), sort_keys=True, allow_nan=False))
