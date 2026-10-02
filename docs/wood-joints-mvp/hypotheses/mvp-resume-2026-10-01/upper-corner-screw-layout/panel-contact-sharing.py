"""Read saved A1-rear panel reactions; no allocation, geometry or solver run."""

import argparse
import csv
import hashlib
import json
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = next(p for p in HERE.parents if (p / "pyproject.toml").exists())
BASE = ROOT / "docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28"
BODY = "main_lower_left"
CASE = "a1-rear"
FRAMES = {
    12: ("panel-width-frame-250-attempt05-conic",
         "5a49b2076e0e32e5fbae90b1da41be6b77973da9057aee860acebaee9cef05f0",
         "ff54c8f662bce93e03b46e47b088408c82471c5956b824e3320afb32b79919ef"),
    20: ("count20-width-grain-frame-attempt01",
         "0a8bcf1ac6679d970d72e11e652d31e3406607699230bcf9915bb009e34e9b88",
         "8271a9e6c3ff15440703f78b704e6f601a545b538611c09009afdeb77393eb7c"),
}
SOURCE = BASE / "current-springa-frame-input-adapter-attempt01/a12-rear/model.json"
CONTACTS = BASE / "reduced-static-attempt01/contact-geometry.json"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_text())


def require(condition, message):
    if not condition:
        raise ValueError(message)


def pin(path, pins, expected=None):
    digest = sha(path)
    require(expected is None or digest == expected, f"Changed input: {path}")
    pins[path] = digest


def analyze(count, pins, cells, patches):
    name, comparison_hash, response_hash = FRAMES[count]
    folder = HERE / name
    pin(folder / "comparison.json", pins, comparison_hash)
    pin(folder / "response.npz", pins, response_hash)
    comparison = read(folder / "comparison.json")
    op = ROOT / comparison["frame_operator_directory"]
    assessment = read(op / "operator-assessment.json")
    pin(op / "operator-assessment.json", pins)
    for filename in ("row-identities.json", "model.json", "model-inputs.json", "operators.npz"):
        pin(op / filename, pins, assessment["output_sha256"][filename])
    rows, model, inputs = [read(op / filename) for filename in
                           ("row-identities.json", "model.json", "model-inputs.json")]
    body_id = model["body_names"].index(BODY)
    block = slice(6 * body_id, 6 * body_id + 6)
    case_index = next(i for i, c in enumerate(inputs["cases"]) if c["case_id"] == CASE)
    case_input = inputs["cases"][case_index]["source_applied_load"]
    with np.load(op / "operators.npz", allow_pickle=False) as data:
        H, D = data["H"].copy(), data["D"].copy()
        e = comparison["dead_load_factor"] * data["e"][:, 2 * case_index] + data["e"][:, 2 * case_index + 1]
        W = comparison["dead_load_factor"] * data["W"][:, 2 * case_index] + data["W"][:, 2 * case_index + 1]
    with np.load(folder / "response.npz", allow_pickle=False) as data:
        f = data[CASE + "_gap_raw_force_n"].copy()
        a = data[CASE + "_gap_rigid_coordinates"].copy()
    coordinates = model["physical_node_coordinates_mm"]
    center = np.mean([coordinates[str(n)] for n in model["body_nodes"][BODY]], axis=0)
    normal = np.array(model["material_binding"]["panel_axes"][BODY]["panel_normal_global_xyz"])
    tangent = np.cross(normal, [1.0, 0.0, 0.0])
    q = D @ a + e - H @ f
    actions = []
    for i, row in enumerate(rows):
        own = row["ownership"]
        incident = BODY in (own["first_body"], own["second_body"])
        require(incident or np.max(abs(D[i, block])) < 1e-12, "Hidden panel action")
        if not incident:
            continue
        value = -D[i, block] * f[i]
        value[3:] *= 1000
        point = np.array(own["point_mm"])
        free = value[3:] - np.cross(point - center, value[:3])
        cell = cells.get(row["row_id"])
        area = None if cell is None else cell["area_mm2"]
        k = row["law"]["stiffness_N_per_mm"]
        actions.append({
            "row_id": row["row_id"], "role": own["role"],
            "other_body": own["second_body"] if own["first_body"] == BODY else own["first_body"],
            "point_xyz_mm": point.tolist(), "scalar_force_n": float(f[i]),
            "force_xyz_n": value[:3].tolist(), "moment_about_panel_datum_xyz_nmm": value[3:].tolist(),
            "free_moment_xyz_nmm": free.tolist(), "panel_normal_force_n": float(normal @ value[:3]),
            "stiffness_n_per_mm": k, "relative_motion_mm": float(q[i]),
            "elastic_self_compliance_mm_per_n": float(H[i, i]),
            "law_force_minus_k_motion_n": float(f[i] - k * max(q[i], 0)) if row["family"] == "unilateral_springa" else None,
            "contact_cell_area_mm2": area,
            "contact_penalty_n_per_mm3": None if area is None else k / area,
            "model_cell_average_pressure_mpa": None if area is None else float(f[i]) / area,
            "source_patch_index": None if cell is None else cell["source_patch_index"],
        })
    roles = {}
    for action in actions:
        roles.setdefault(action["role"], np.zeros(6))
        roles[action["role"]] += np.r_[action["force_xyz_n"], action["moment_about_panel_datum_xyz_nmm"]]
    external = W[block].copy()
    external[3:] *= 1000
    residual = external + sum(roles.values(), np.zeros(6))
    require(max(abs(residual[:3])) <= 0.1 and max(abs(residual[3:])) <= 2,
            "Saved signed panel wrench fails balance")
    screws = [x for x in actions if x["role"] == "non_qualifying_parametric_screw_withdrawal"]
    normal_contacts = [x for x in actions if x["role"] == "timber_or_panel_contact"
                       and x["other_body"] == max(screws, key=lambda x: x["scalar_force_n"])["other_body"]]
    contacts = [x for x in actions if x["role"] == "timber_or_panel_contact"
                and x["panel_normal_force_n"] > 0.01]
    require(len(screws) == count, "Wrong lower-left screw census")
    peak = max(screws, key=lambda x: x["scalar_force_n"])
    for contact in normal_contacts:
        lever = np.array(contact["point_xyz_mm"]) - peak["point_xyz_mm"]
        contact["lever_from_peak_X_T_N_mm"] = [float(lever[0]), float(lever @ tangent), float(lever @ normal)]
        contact["in_plane_distance_from_peak_mm"] = float(np.hypot(lever[0], lever @ tangent))
        contact["peak_tension_moment_about_contact_xyz_nmm"] = np.cross(-lever, peak["force_xyz_n"]).tolist()
    same_receiver = [x for x in contacts if x["other_body"] == peak["other_body"]]
    geometric_nearest = sorted(normal_contacts, key=lambda x: x["in_plane_distance_from_peak_mm"])[:4]
    nearest = sorted(same_receiver, key=lambda x: x["in_plane_distance_from_peak_mm"])[:4]
    strongest = sorted(same_receiver, key=lambda x: x["panel_normal_force_n"], reverse=True)[:4]
    used_patches = sorted({x["source_patch_index"] for x in actions if x["source_patch_index"] is not None})
    patch_reports = []
    for index in used_patches:
        group = [x for x in actions if x["source_patch_index"] == index]
        patch_reports.append({"index": index, "members": patches[index]["member_ids"],
                              "source_area_mm2": patches[index]["area_mm2"],
                              "source_cell_count": len(group),
                              "active_cell_count": sum(x["scalar_force_n"] > 0.01 for x in group),
                              "sampled_area_mm2": sum(x["contact_cell_area_mm2"] for x in group),
                              "compression_scalar_sum_n": sum(x["scalar_force_n"] for x in group)})
    report = {"screws_per_main_panel": count, "case_id": CASE, "gap_scale": 1,
              "panel_datum_xyz_mm": center.tolist(), "panel_normal_xyz": normal.tolist(),
              "source_applied_load": case_input, "dead_load_factor": comparison["dead_load_factor"],
              "external_wrench_xyz_n_and_nmm": external.tolist(),
              "reaction_wrenches_by_role_xyz_n_and_nmm": {k: v.tolist() for k, v in roles.items()},
              "signed_panel_normal_reaction_by_role_n": {k: float(normal @ v[:3]) for k, v in roles.items()},
              "external_panel_normal_force_n": float(normal @ external[:3]),
              "balance_residual_xyz_n_and_nmm": residual.tolist(),
              "total_screw_tension_n": sum(x["scalar_force_n"] for x in screws),
              "total_outward_normal_contact_n": sum(x["panel_normal_force_n"] for x in contacts),
              "peak": peak, "nearest_active_opposing_contacts_same_receiver": nearest,
              "nearest_geometric_contacts_same_receiver_including_open": geometric_nearest,
              "strongest_active_opposing_contacts_same_receiver": strongest,
              "contact_patches": patch_reports, "actions": actions}
    return report, H, rows


def run(output):
    require(not output.exists(), "Preserve previous result; use a fresh child")
    pins = {}
    pin(SOURCE, pins, "61f95ec9e670b2bd0e95d426cc14ff381283edfc4f9c87e47c2b344dd4fe50b8")
    pin(CONTACTS, pins, "034067430fff5207cdb40819fa8118a367edeb29a8d83926928cc96a0e87d151")
    pin(Path(__file__), pins)
    source = read(SOURCE)
    cells = {r["name"]: r for r in source["contact_cell_ownership"]}
    patches = read(CONTACTS)["contact_patches"]
    old, old_H, old_rows = analyze(12, pins, cells, patches)
    new, new_H, new_rows = analyze(20, pins, cells, patches)
    require(old["source_applied_load"] == new["source_applied_load"]
            and old["external_wrench_xyz_n_and_nmm"] == new["external_wrench_xyz_n_and_nmm"],
            "External panel load changed")
    require(old_rows == new_rows[:len(old_rows)], "Shared row ownership/laws changed")
    old_peak_id = old["peak"]["row_id"]
    same_screw = next(x for x in new["actions"] if x["row_id"] == old_peak_id)
    report = {"schema": "saved_panel_contact_sharing/v1", "status": "SAVED_WRENCHES_BALANCE",
              "source_sha256": {str(p.relative_to(ROOT)): h for p, h in pins.items()},
              "contact_scenario": source["connection_scenario"], "states": [old, new],
              "original_peak_screw_in_count20": same_screw,
              "shared_H_absolute_max_difference_mm_per_n": float(np.max(abs(old_H - new_H[:len(old_H), :len(old_H)]))),
              "limits": ["Saved reactions only; no new force allocation or solve.",
                         "Nearest opposing contacts are geometric diagnostics, not isolated load-sharing pairs.",
                         "Cell pressure is modeled force divided by source cell area, not validated physical pressure or bearing acceptance.",
                         "Contact penalty and screw laws are conditional response assumptions; equilibrium does not calibrate them.",
                         "No geometry, screw inventory, material selection or physical release change."],
              "physical_release": False}
    for path, digest in pins.items():
        require(sha(path) == digest, "Input changed during accounting")
    output.mkdir(parents=True)
    (output / "result.json").write_text(json.dumps(report, indent=2, allow_nan=False) + "\n")
    (output / "producer.py.snapshot").write_bytes(Path(__file__).read_bytes())
    with (output / "signed-panel-actions.csv").open("w", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(["main_screws", "row_id", "role", "other_body", "scalar_n", "normal_n",
                         "Fx_n", "Fy_n", "Fz_n", "Mx_nmm", "My_nmm", "Mz_nmm"])
        for state in (old, new):
            for action in state["actions"]:
                writer.writerow([state["screws_per_main_panel"], action["row_id"], action["role"],
                                 action["other_body"], action["scalar_force_n"], action["panel_normal_force_n"],
                                 *action["force_xyz_n"], *action["moment_about_panel_datum_xyz_nmm"]])
    print("result_sha256", sha(output / "result.json"))
    for state in (old, new):
        print(state["screws_per_main_panel"], state["peak"]["row_id"], state["peak"]["scalar_force_n"])


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    run(parser.parse_args().output.resolve())
