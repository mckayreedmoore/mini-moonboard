"""Independent JSON-only thin-frame load, contact and wrench verification.

This performs no solve or CAD query. It verifies exported conditional actions,
not the physical stiffness, component resistance or structural acceptance.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
PACKET = ROOT / "docs/wood-joints-mvp/hypotheses/hl35-candidate/thin-frame-comparison"
PINS = {
    "mixed-offset-rows-shallow-wires-v4.json": "8174841bf64914570397ee6d960c5602f74097e2e412e5910502811bc5b9405c",
    "integrated-model-v4.json": "28bbd2d2fb6f1a93acb441af124c453f04f81e03be551906c633d5acad1d407e",
    "native-geometry-v4.json": "cafdd983a41f2eee15647b28e60e5b2704354a4c5518d120e4c4342001994bb9",
    "access-takeoff-v4.json": "0c5a09879c9b191c39b96ce670d71ad110661bff7dfeab68133f711b32de476c",
}
CASES = {"a12-rear": ("A12", (0., 300.)), "a12-forward": ("A12", (0., -300.)),
         "a12-left": ("A12", (-300., 0.)), "k12-right": ("K12", (300., 0.)),
         "k12-rear": ("K12", (0., 300.)), "a1-rear": ("A1", (0., 300.)),
         "gravity-only": (None, (0., 0.))}


def vector(values) -> np.ndarray:
    result = np.asarray(values, dtype=float)
    if result.shape != (3,) or not np.isfinite(result).all():
        raise ValueError("finite three-component vector required")
    return result


def wrench(force, point, reference, moment=(0., 0., 0.)) -> np.ndarray:
    force = vector(force)
    return np.r_[force, np.cross(vector(point) - vector(reference), force) + vector(moment)]


def balances(body_ids, loads, actions, floors, reference) -> tuple[dict, np.ndarray, np.ndarray]:
    """Point-force dual: opposite body actions cancel exactly in global work."""
    residuals = {name: np.zeros(6) for name in body_ids}
    applied, floor = np.zeros(6), np.zeros(6)
    for row in loads:
        value = wrench(row["force_xyz_n"], row["point_xyz_mm"], reference)
        residuals[row["body"]] += value
        applied += value
    for row in actions:
        value = wrench(row["force_on_first_xyz_n"], row["point_xyz_mm"], reference,
                       row.get("moment_at_point_model_xyz_nmm", (0., 0., 0.)))
        residuals[row["first"]] += value
        residuals[row["second"]] -= value
    for row in floors:
        value = wrench(row["force_on_first_xyz_n"], row["point_xyz_mm"], reference,
                       row.get("moment_at_point_model_xyz_nmm", (0., 0., 0.)))
        residuals[row["first"]] += value
        floor += value
    return residuals, applied, applied + floor


def expected_loads(demand: dict, cache: dict, takeoff: dict, integrated: dict) -> tuple[dict, list]:
    bodies = {row["id"]: row for row in cache["parts"]
              if row["kind"] in {"timber", "panel", "bracket"}}
    if len(bodies) != 62:
        raise ValueError("frozen source needs 62 bodies")
    masses, loads = {}, []
    for name, row in bodies.items():
        mass = (row["volume_mm3"] * 500e-9 if row["kind"] != "bracket" else
                (.78 if name.startswith("B104ZN") else .56) * .45359237)
        masses[name] = mass
        loads.append({"id": "self-weight/" + name, "body": name,
                      "point_xyz_mm": row["center_of_mass_xyz_mm"], "force_xyz_n": [0., 0., -mass * 9.80665]})
    for i, row in enumerate(takeoff["takeoff"]["conditional_metal_gravity_rows"]):
        loads.append({"id": "bolt-weight/" + row["id"] + f"/gravity-share-{i}", "body": row["owner"],
                      "point_xyz_mm": row["centroid_xyz_mm"], "force_xyz_n": [0., 0., -row["mass_kg"] * 9.80665]})
    features = {row["identity"]: row for row in integrated["panel_machining"]["features"]}
    panels = [name for name, row in bodies.items() if row["kind"] == "panel"]
    placement = demand["accessory_placement"]
    if placement == "retained-original-top-hold":
        feature = features["hold_tnut_main_A12"]
        point = (vector(feature["start_xyz_mm"]) + [1019.2, 0., 0.] +
                 vector(feature["direction_xyz"]) * 18.25625)
        for name in panels:
            if name.startswith("main_upper_"):
                loads.append({"id": "accessory/" + name, "body": name,
                              "point_xyz_mm": point.tolist(), "force_xyz_n": [0., 0., -12.5 * 9.80665]})
    elif placement == "proportional-six-panel-sensitivity":
        total = sum(masses[name] for name in panels)
        for name in panels:
            loads.append({"id": "accessory/" + name, "body": name,
                          "point_xyz_mm": bodies[name]["center_of_mass_xyz_mm"],
                          "force_xyz_n": [0., 0., -25. * masses[name] / total * 9.80665]})
    else:
        raise ValueError("unrecognized accessory placement")
    if demand["case_id"] not in CASES:
        raise ValueError("case leaves six-case/permanent coverage")
    hold, horizontal = CASES[demand["case_id"]]
    if hold:
        feature = features["hold_tnut_main_" + hold]
        inward = vector(feature["direction_xyz"])
        inward /= np.linalg.norm(inward)
        loads.append({"id": "climber/" + hold, "body": feature["panel"],
                      "point_xyz_mm": (vector(feature["start_xyz_mm"]) - 100. * inward).tolist(),
                      "force_xyz_n": [*horizontal, -500. * 4.4482216152605]})
    return bodies, loads


def verify_contacts(layout: dict, contacts: list) -> None:
    """Verify the current four-corner flange model without reloading BREP."""
    expected = {}
    for fitting in layout["raw_fittings"]:
        origin, u, v, w = [vector(fitting[key]) for key in ("origin_xyz_mm", "u_xyz", "v_xyz", "w_xyz")]
        for flange, receiver, along, normal, length in (
                ("beam", fitting["beam"], u, v, 104.775),
                ("post", fitting["post"], v, u, 41.275 if fitting["angle_id"].startswith("B103ZN") else 88.9)):
            for corner, (station, width) in enumerate((a, b) for a in (5.55625, length) for b in (-20.6375, 20.6375)):
                expected[fitting["angle_id"] + "/" + flange + f"/contact-{corner}"] = (
                    fitting["angle_id"], flange, receiver, origin + along * station + w * width, normal)
    if len(contacts) != 288 or len({row["id"] for row in contacts}) != 288:
        raise ValueError("all 288 unique flange contact rows, including zero forces, required")
    for row in contacts:
        if row["id"] not in expected:
            raise ValueError("foreign flange contact")
        angle, flange, receiver, point, normal = expected[row["id"]]
        if (row["angle_id"], row["flange"], row["receiver"]) != (angle, flange, receiver):
            raise ValueError("flange contact ownership differs")
        if np.linalg.norm(vector(row["point_xyz_mm"]) - point) > 1e-5:
            raise ValueError("flange contact datum differs")
        if row["first"] != angle or row["second"] != receiver or row["compression_n"] < 0.:
            raise ValueError("flange contact body/sign differs")
        force = vector(row["force_on_first_xyz_n"])
        if np.linalg.norm(force - row["compression_n"] * normal) > 1e-7 or np.linalg.norm(force + vector(row["force_on_receiver_xyz_n"])) > 1e-7:
            raise ValueError("flange contact reaction direction/dual differs")
        if np.linalg.norm(vector(row["moment_at_point_model_xyz_nmm"]) + vector(row["moment_on_receiver_at_point_xyz_nmm"])) > 1e-7:
            raise ValueError("flange contact free-moment dual differs")


def verify_attachments(layout: dict, rows: list) -> None:
    expected = {(axis["id"], port["angle_id"], port["flange"]): port
                for axis in layout["installed_axes"] for port in axis["attachments"]}
    identities = [(row["axis_id"], row["angle_id"], row["flange"]) for row in rows]
    if len(rows) != 72 or len(set(identities)) != 72 or set(identities) != set(expected):
        raise ValueError("all 72 unique frozen attachment identities required")
    for row, identity in zip(rows, identities, strict=True):
        port = expected[identity]
        if (row["receiver"], row["first"], row["second"]) != (port["receiver"], port["receiver"], port["angle_id"]):
            raise ValueError("attachment body/receiver identity differs")
        if np.linalg.norm(vector(row["point_xyz_mm"]) - port["entry_xyz_mm"]) > 1e-5:
            raise ValueError("attachment datum differs")
        if np.linalg.norm(vector(row["force_on_first_xyz_n"]) - vector(row["force_on_receiver_xyz_n"])) > 1e-7:
            raise ValueError("attachment force exports differ")
        if np.linalg.norm(vector(row["moment_at_point_model_xyz_nmm"]) - vector(row["moment_on_receiver_at_point_xyz_nmm"])) > 1e-7:
            raise ValueError("attachment free-moment exports differ")


def audit_state(demand: dict) -> dict:
    """Raise on source/load/export mismatch; return independent closure status."""
    records, pins = {}, {}
    for name, expected in PINS.items():
        path = PACKET / name
        if hashlib.sha256(path.read_bytes()).hexdigest() != expected:
            raise ValueError(f"frozen audit source differs: {name}")
        records[name] = json.loads(path.read_text())
        pins[str(path.relative_to(ROOT))] = expected
    if demand.get("candidate") != records["mixed-offset-rows-shallow-wires-v4.json"]["candidate"]:
        raise ValueError("foreign candidate")
    bodies, loads = expected_loads(demand, records["native-geometry-v4.json"], records["access-takeoff-v4.json"],
                                  records["integrated-model-v4.json"])
    recorded = demand.get("body_applied_loads", [])
    by_id = {row["id"]: row for row in recorded}
    if len(by_id) != len(recorded) or set(by_id) != {row["id"] for row in loads}:
        raise ValueError("recorded load identity/census differs")
    for row in loads:
        supplied = by_id[row["id"]]
        if supplied["body"] != row["body"] or np.linalg.norm(vector(supplied["point_xyz_mm"]) - row["point_xyz_mm"]) > 1e-5:
            raise ValueError("recorded per-body load owner/datum differs")
        if np.linalg.norm(vector(supplied["force_xyz_n"]) - row["force_xyz_n"]) > 1e-7:
            raise ValueError("recorded force differs from retained gravity/climber basis")
    layout = records["mixed-offset-rows-shallow-wires-v4.json"]
    verify_contacts(layout, demand["flange_contact_actions"])
    verify_attachments(layout, demand["attachment_actions"])
    if {row["id"]: row for row in demand["flange_contact_actions"]} != {
            row["id"]: row for row in demand["contact_actions"] if row["kind"] == "flange_contact"}:
        raise ValueError("component flange contacts differ from equilibrium contacts")
    reference = vector(demand["common_wrench_reference_xyz_mm"])
    actions = [row for name in ("attachment_actions", "retained_bolt_actions", "panel_screw_actions", "contact_actions")
               for row in demand[name]]
    if len(demand["attachment_actions"]) != 72 or len(demand["retained_bolt_actions"]) != 12 or len(demand["panel_screw_actions"]) != 66:
        raise ValueError("complete 72/12/66 connection tables required")
    retained = {axis["id"]: axis for axis in layout["installed_axes"] if not axis["attachments"]}
    if len({row["axis_id"] for row in demand["retained_bolt_actions"]}) != 12:
        raise ValueError("retained shaft identities are not unique")
    for row in demand["retained_bolt_actions"]:
        if row["axis_id"] not in retained or [row["first"], row["second"]] != retained[row["axis_id"]]["receivers"]:
            raise ValueError("retained shaft/member identity differs")
    screw_axes = {row["axis_id"]: row for row in layout["screw_axes"]}
    if {row["axis_id"] for row in demand["panel_screw_actions"]} != set(screw_axes):
        raise ValueError("panel screw identities differ")
    for row in demand["panel_screw_actions"]:
        source = screw_axes[row["axis_id"]]
        if (row["panel"], row["first"], row["receiver"], row["second"]) != (source["panel"], source["panel"], source["receiver"], source["receiver"]):
            raise ValueError("panel screw body/receiver identity differs")
        if np.linalg.norm(vector(row["force_on_first_xyz_n"]) + vector(row["force_on_receiver_xyz_n"])) > 1e-7:
            raise ValueError("panel screw reaction exports differ")
    residuals, applied, global_residual = balances(bodies, loads, actions, demand["floor_actions"], reference)
    stored = {row["body"]: row for row in demand["body_equilibrium_residuals"]}
    if len(stored) != 62 or len(demand["body_equilibrium_residuals"]) != 62 or set(stored) != set(bodies):
        raise ValueError("stored residuals need all 62 unique frozen body identities")
    for name, value in residuals.items():
        if np.linalg.norm(value[:3] - vector(stored[name]["force_xyz_n"])) > 1e-7 or np.linalg.norm(value[3:] - vector(stored[name]["moment_about_reference_xyz_nmm"])) > .001:
            raise ValueError("stored body closure differs from reconstructed point actions")
    declared_global = np.r_[vector(demand["global_equilibrium_residual_force_n"]), vector(demand["global_equilibrium_residual_moment_nmm"])]
    # Global residual is exported about world origin; transport it to this reference.
    declared_global[3:] -= np.cross(reference, declared_global[:3])
    if np.linalg.norm(global_residual[:3] - declared_global[:3]) > 1e-7 or np.linalg.norm(global_residual[3:] - declared_global[3:]) > .001:
        raise ValueError("stored global closure differs")
    declared_applied = np.r_[vector(demand["applied_force_xyz_n"]), vector(demand["applied_moment_about_global_origin_xyz_nmm"])]
    declared_applied[3:] -= np.cross(reference, declared_applied[:3])
    if np.linalg.norm(applied - declared_applied) > .001:
        raise ValueError("aggregate applied wrench differs from retained loads")
    force_error = max(np.linalg.norm(value[:3]) for value in [*residuals.values(), global_residual])
    global_origin_moment = global_residual[3:] + np.cross(reference, global_residual[:3])
    moment_error = max(*[np.linalg.norm(value[3:]) for value in residuals.values()], np.linalg.norm(global_origin_moment))
    return {"independent_equilibrium_and_contact_checks_pass": bool(force_error <= 1e-4 and moment_error <= .1),
            "body_count": 62, "load_count": len(loads), "flange_contacts": 288,
            "maximum_body_or_global_force_norm_n": float(force_error),
            "maximum_body_or_global_moment_norm_nmm": float(moment_error),
            "body_moment_reference_xyz_mm": reference.tolist(), "global_moment_reference_xyz_mm": [0., 0., 0.],
            "force_tolerance_n": 1e-4, "moment_tolerance_nmm": .1,
            "source_sha256": pins, "native_or_CAD_execution": False,
            "strength_or_physical_stiffness_acceptance": False}
