"""Independent JSON-only load and body-wrench audit for physical common shafts.

The 132-body method must supply separate distributed shaft/host bearing and
end-capture actions. The frozen 62-body connection audit is not invoked.
No CAD query, stiffness assembly or response solve occurs here.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from scripts import thin_bolted_equilibrium_audit as arithmetic
from scripts import thin_bolted_finished_support_audit as support

ROOT, PACKET = arithmetic.ROOT, arithmetic.PACKET
METAL_KINDS = {"shaft", "head", "head_washer", "nut_washer", "nut"}
UNIT_PATH = PACKET / "timber-bolt-resistance-v4.json"
UNIT_SHA = "5e78ac49a2db2050caf7ee7d2002d0ebf4f9a92496e857a0e2d652629bd0d848"
COMMON_PRODUCER = ROOT / "scripts/thin_bolted_common_shaft.py"
COMMON_PRODUCER_SHA = "0ff8c52a36f168cba0bd3fed2d592daa9e5d9de5facbc650b151f64c2f23f4eb"
SUPPORT_AUDIT_SHA = "0a37e67ed20e3fd1eed8b8b4d0d12889df6fd9a6fb33d6f8f68a0c6768f5ada0"
COMMON_METHOD_BASIS = "continuous-circular-shafts-distributed-own-bore-bearing-axial-end-capture"


def expected_common_loads(demand, cache, takeoff, integrated):
    """Reuse retained loads; move each exact bolt role once onto its own shaft."""
    bodies, original = arithmetic.expected_loads(demand, cache, takeoff, integrated)
    roles = [row for row in cache["parts"] if row["kind"] in METAL_KINDS]
    by_axis = {}
    for role in roles:
        by_axis.setdefault(role["axis_id"], {})[role["kind"]] = role
    if len(roles) != 350 or len(by_axis) != 70 or any(set(rows) != METAL_KINDS for rows in by_axis.values()):
        raise ValueError("all 350 unique metal roles and 70 own physical shafts required")
    ids = {row["id"] for row in roles}
    if len(ids) != 350:
        raise ValueError("physical metal role identities are not unique")
    prefix = tuple("bolt-weight/" + name + "/gravity-share-" for name in ids)
    loads = [row for row in original if not row["id"].startswith(prefix)]
    for axis_id, group in by_axis.items():
        name = "shaft/" + axis_id
        mass = sum(row["volume_mm3"] * 7850e-9 for row in group.values())
        center = sum((arithmetic.vector(row["center_of_mass_xyz_mm"]) * row["volume_mm3"] * 7850e-9
                      for row in group.values()), np.zeros(3)) / mass
        bodies[name] = {"id": name, "kind": "shaft_assembly", "mass_kg": mass,
                        "center_xyz_mm": center.tolist()}
        for role in group.values():
            loads.append({"id": "physical-bolt-metal/" + role["id"], "body": name,
                          "point_xyz_mm": role["center_of_mass_xyz_mm"],
                          "force_xyz_n": [0., 0., -role["volume_mm3"] * 7850e-9 * 9.80665]})
    old = sum((arithmetic.wrench(row["force_xyz_n"], row["point_xyz_mm"], [0., 0., 0.])
               for row in original), np.zeros(6))
    new = sum((arithmetic.wrench(row["force_xyz_n"], row["point_xyz_mm"], [0., 0., 0.])
               for row in loads), np.zeros(6))
    if np.linalg.norm(old[:3] - new[:3]) > 1e-8 or np.linalg.norm(old[3:] - new[3:]) > 1e-5:
        raise ValueError("physical shaft gravity remap fails whole-frame force/moment conservation")
    return bodies, loads, new - old


def common_balances(body_ids, loads, actions, floors, reference):
    """Reconstruct both body wrenches at the actual, possibly distinct, datums."""
    residuals = {name: np.zeros(6) for name in body_ids}
    applied, floor = np.zeros(6), np.zeros(6)
    for row in loads:
        value = arithmetic.wrench(row["force_xyz_n"], row["point_xyz_mm"], reference)
        residuals[row["body"]] += value
        applied += value
    for row in actions:
        force = arithmetic.vector(row["force_on_first_xyz_n"])
        first_moment = arithmetic.vector(row.get("moment_on_first_at_point_xyz_nmm",
                                               row.get("moment_at_point_model_xyz_nmm", [0., 0., 0.])))
        if "moment_at_point_model_xyz_nmm" in row and np.linalg.norm(first_moment - arithmetic.vector(row["moment_at_point_model_xyz_nmm"])) > 1e-7:
            raise ValueError("first-body free moment aliases differ")
        second_point = row.get("host_support_point_xyz_mm", row["point_xyz_mm"])
        second_moment = arithmetic.vector(row.get("moment_on_second_at_point_xyz_nmm", -first_moment))
        first = arithmetic.wrench(force, row["point_xyz_mm"], reference, first_moment)
        second = arithmetic.wrench(-force, second_point, reference, second_moment)
        if np.linalg.norm(first[:3] + second[:3]) > 1e-7 or np.linalg.norm(first[3:] + second[3:]) > .001:
            raise ValueError("distinct-datum internal actions do not cancel globally")
        residuals[row["first"]] += first
        residuals[row["second"]] += second
    for row in floors:
        value = arithmetic.wrench(row["force_on_first_xyz_n"], row["point_xyz_mm"], reference,
                                  row.get("moment_at_point_model_xyz_nmm", [0., 0., 0.]))
        residuals[row["first"]] += value
        floor += value
    return residuals, applied, applied + floor


def verify_load_table(recorded, expected):
    indexed = {row["id"]: row for row in recorded}
    if len(indexed) != len(recorded) or set(indexed) != {row["id"] for row in expected}:
        raise ValueError("132-body applied load identity/census differs")
    for source in expected:
        row = indexed[source["id"]]
        if row["body"] != source["body"] or np.linalg.norm(arithmetic.vector(row["point_xyz_mm"]) - source["point_xyz_mm"]) > 1e-5:
            raise ValueError("physical shaft/host load owner or datum differs")
        if np.linalg.norm(arithmetic.vector(row["force_xyz_n"]) - source["force_xyz_n"]) > 1e-7:
            raise ValueError("physical shaft/host load differs from retained mass and climber basis")


def verify_body_closure(demand, bodies, loads, actions):
    reference = arithmetic.vector(demand["common_wrench_reference_xyz_mm"])
    residuals, applied, global_value = common_balances(bodies, loads, actions, demand["floor_actions"], reference)
    stored = {row["body"]: row for row in demand["body_equilibrium_residuals"]}
    if len(stored) != 132 or len(demand["body_equilibrium_residuals"]) != 132 or set(stored) != set(bodies):
        raise ValueError("all 132 unique host and shaft residuals required")
    for name, actual in residuals.items():
        if (np.linalg.norm(actual[:3] - arithmetic.vector(stored[name]["force_xyz_n"])) > 1e-7
                or np.linalg.norm(actual[3:] - arithmetic.vector(stored[name]["moment_about_reference_xyz_nmm"])) > .001):
            raise ValueError("stored host/shaft wrench differs from independent paired-datum reconstruction")
    declared_global = np.r_[arithmetic.vector(demand["global_equilibrium_residual_force_n"]),
                            arithmetic.vector(demand["global_equilibrium_residual_moment_nmm"])]
    declared_global[3:] -= np.cross(reference, declared_global[:3])
    if (np.linalg.norm(declared_global[:3] - global_value[:3]) > 1e-7
            or np.linalg.norm(declared_global[3:] - global_value[3:]) > .001):
        raise ValueError("stored global residual differs from physical shaft/host reconstruction")
    declared_applied = np.r_[arithmetic.vector(demand["applied_force_xyz_n"]),
                             arithmetic.vector(demand["applied_moment_about_global_origin_xyz_nmm"])]
    declared_applied[3:] -= np.cross(reference, declared_applied[:3])
    if np.linalg.norm(applied - declared_applied) > .001:
        raise ValueError("aggregate applied wrench differs from reconstructed gravity remap")
    global_origin_moment = global_value[3:] + np.cross(reference, global_value[:3])
    force = max(np.linalg.norm(row[:3]) for row in [*residuals.values(), global_value])
    moment = max(*[np.linalg.norm(row[3:]) for row in residuals.values()], np.linalg.norm(global_origin_moment))
    return {"all_132_body_and_global_wrench_checks_pass": bool(force <= 1e-4 and moment <= .1),
            "body_count": 132, "shaft_body_count": 70, "load_count": len(loads),
            "maximum_body_or_global_force_norm_n": float(force), "maximum_body_or_global_moment_norm_nmm": float(moment),
            "force_tolerance_n": 1e-4, "moment_tolerance_nmm": .1,
            "body_moment_reference_xyz_mm": reference.tolist(), "global_moment_reference_xyz_mm": [0., 0., 0.]}


def read_sources():
    contact, cache, pins = support.read_authenticated_sources()
    if support.digest(UNIT_PATH) != UNIT_SHA:
        raise ValueError("frozen finished bearing geometry differs")
    unit = json.loads(UNIT_PATH.read_text())
    layout = json.loads((PACKET / "mixed-offset-rows-shallow-wires-v4.json").read_text())
    takeoff = json.loads((PACKET / "access-takeoff-v4.json").read_text())
    integrated = json.loads((PACKET / "integrated-model-v4.json").read_text())
    pins[str(UNIT_PATH.relative_to(ROOT))] = UNIT_SHA
    return contact, cache, unit, layout, takeoff, integrated, pins


def verify_common_actions(demand, shaft_specs):
    """Check every radial quadrature path and every actual end pressure plane."""
    state = demand["state_id"]
    expected_bearings, expected_captures = {}, {}
    for shaft in shaft_specs:
        p = arithmetic.vector(shaft["point"])
        g = arithmetic.vector(shaft["basis"][0])
        for surface_index, surface in enumerate(shaft["surfaces"]):
            low, high = surface["interval_mm"]
            for quad, abscissa in enumerate((-1. / np.sqrt(3.), 1. / np.sqrt(3.))):
                station = (low + high) / 2. + (high - low) / 2. * abscissa
                identity = shaft["axis_id"] + f"/bearing-{surface_index}-{quad}"
                expected_bearings[identity] = (shaft, surface, p + g * station)
        for end in shaft["ends"]:
            identity = shaft["axis_id"] + "/" + end["end"] + "-capture"
            expected_captures[identity] = (shaft, end, p + g * end["pressure_face_s_mm"],
                                          p + g * end["support_s_mm"])
    tables = (("common_shaft_bearing_actions", expected_bearings),
              ("shaft_end_capture_actions", expected_captures))
    if len(expected_bearings) != 308 or len(expected_captures) != 140:
        raise ValueError("source requires 308 bearing and 140 end-capture points")
    for name, expected in tables:
        rows = demand.get(name, [])
        indexed = {row["id"]: row for row in rows}
        if len(indexed) != len(rows) or set(indexed) != set(expected):
            raise ValueError("complete unique distributed bearing/end-capture census required")
        for identity, row in indexed.items():
            values = expected[identity]
            shaft, feature, point = values[:3]
            if (row["state_id"], row["case_id"], row["accessory_placement"]) != (
                    state, demand["case_id"], demand["accessory_placement"]):
                raise ValueError("physical shaft action mixes states or loads")
            if (row["axis_id"], row["first"], row["second"]) != (shaft["axis_id"], shaft["body"], feature["host"]):
                raise ValueError("physical shaft action ownership differs")
            if np.linalg.norm(arithmetic.vector(row["point_xyz_mm"]) - point) > 1e-5:
                raise ValueError("physical shaft action differs from actual bearing/pressure plane")
            force = arithmetic.vector(row["force_on_first_xyz_n"])
            if any(np.linalg.norm(arithmetic.vector(row[key])) > 1e-7 for key in
                   ("moment_at_point_model_xyz_nmm", "moment_on_first_at_point_xyz_nmm") if key in row):
                raise ValueError("current centered radial/axial point model supplies no free shaft couple")
            if np.linalg.norm(arithmetic.vector(row.get("moment_on_second_at_point_xyz_nmm", [0., 0., 0.]))) > 1e-7:
                raise ValueError("current point model supplies no free host couple")
            if "force_on_second_xyz_n" not in row or np.linalg.norm(force + arithmetic.vector(row["force_on_second_xyz_n"])) > 1e-7:
                raise ValueError("physical shaft/host exported force dual differs")
            if name == "common_shaft_bearing_actions":
                if row["kind"] != "common_shaft_bearing" or abs(force @ shaft["basis"][0]) > 1e-6:
                    raise ValueError("shaft bore foundation must act radially")
                surface_index, quad = [int(value) for value in identity.split("/bearing-")[1].split("-")]
                if (row["surface_index"], row["quad_index"], row["surface_material"], row["host"], row["flange"]) != (
                        surface_index, quad, feature["kind"], feature["host"], feature.get("flange")):
                    raise ValueError("bearing component metadata differs from its authenticated path")
                if np.linalg.norm(np.asarray(row["surface_interval_mm"]) - feature["interval_mm"]) > 1e-5:
                    raise ValueError("bearing interval metadata differs from actual bore wall")
                station = float((point - shaft["point"]) @ shaft["basis"][0])
                if (abs(support.finite_scalar(row["axis_station_mm"]) - station) > 1e-5
                        or abs(support.finite_scalar(row["weight_length_mm"]) - np.diff(feature["interval_mm"])[0] / 2.) > 1e-5):
                    raise ValueError("bearing station or quadrature weight differs")
                if "host_support_point_xyz_mm" in row and np.linalg.norm(arithmetic.vector(row["host_support_point_xyz_mm"]) - point) > 1e-5:
                    raise ValueError("radial shaft and bore ports must share their actual datum")
            else:
                compression = support.finite_scalar(row["compression_n"])
                direction = arithmetic.vector(feature["direction_on_shaft_xyz"])
                if row["kind"] != "shaft_end_capture" or compression < 0. or np.linalg.norm(force - compression * direction) > 1e-6:
                    raise ValueError("end capture must be unilateral compression along its own axis")
                if row["end"] != feature["end"]:
                    raise ValueError("capture end metadata differs from its actual washer side")
                if np.linalg.norm(arithmetic.vector(row["host_support_point_xyz_mm"]) - values[3]) > 1e-5:
                    raise ValueError("capture host action differs from actual washer support face")
                if np.linalg.norm(np.cross(point - values[3], force)) > .001:
                    raise ValueError("distinct capture datums introduce an unexplained free couple")
    return {"physical_shaft_count": 70, "wood_bearing_surfaces": 82, "steel_bearing_surfaces": 72,
            "radial_quadrature_actions": 308, "unilateral_end_capture_actions": 140,
            "physical_washer_pressure_or_prying_resolved": False}


def audit_common_shaft_state(demand):
    """Require the issued common-shaft producer, source loads and all body actions."""
    if COMMON_PRODUCER_SHA == "UNISSUED" or support.digest(COMMON_PRODUCER) != COMMON_PRODUCER_SHA:
        raise ValueError("common-shaft producer must be frozen before numerical consumption")
    if support.digest(Path(support.__file__)) != SUPPORT_AUDIT_SHA:
        raise ValueError("preserve the frozen finished-floor geometry gate")
    if (demand.get("schema") != "thin_bolted_common_shaft_frame/v1"
            or demand.get("parameters", {}).get("bolt_connection_method") != COMMON_METHOD_BASIS):
        raise ValueError("source-bound continuous physical-shaft method identity required")
    contact, cache, unit, layout, takeoff, integrated, pins = read_sources()
    for name, expected in demand.get("source_sha256", {}).items():
        if support.digest(ROOT / name) != expected:
            raise ValueError(f"physical common-shaft state dependency differs: {name}")
    required = {str((PACKET / name).relative_to(ROOT)): expected for name, expected in arithmetic.PINS.items()}
    required.update({str(support.CONTACT_PATH.relative_to(ROOT)): support.CONTACT_SHA,
                     str(UNIT_PATH.relative_to(ROOT)): UNIT_SHA})
    if any(demand.get("source_sha256", {}).get(name) != expected for name, expected in required.items()):
        raise ValueError("physical common-shaft state omits an authenticated geometry/load source")
    relative = str(COMMON_PRODUCER.relative_to(ROOT))
    if demand.get("source_sha256", {}).get(relative) != COMMON_PRODUCER_SHA:
        raise ValueError("state does not bind the issued physical common-shaft producer")
    from scripts.thin_bolted_common_shaft import shaft_inputs

    shafts = shaft_inputs(layout, unit, cache)
    geometry = verify_common_actions(demand, shafts)
    finished = support.verify_finished_support(demand, contact, cache)
    bodies, loads, remap = expected_common_loads(demand, cache, takeoff, integrated)
    if len(demand.get("body_identities", [])) != 132 or set(demand["body_identities"]) != set(bodies):
        raise ValueError("explicit body identity list requires all 62 hosts and 70 shafts")
    verify_load_table(demand["body_applied_loads"], loads)
    if demand.get("attachment_actions") or demand.get("retained_bolt_actions"):
        raise ValueError("old paired wood/flange arrows are not a physical common-shaft action table")
    arithmetic.verify_contacts(layout, demand["flange_contact_actions"])
    if {row["id"]: row for row in demand["flange_contact_actions"]} != {
            row["id"]: row for row in demand["contact_actions"] if row["kind"] == "flange_contact"}:
        raise ValueError("component flange contact aliases differ from equilibrium actions")
    axes = {row["axis_id"]: row for row in layout["screw_axes"]}
    screws = demand["panel_screw_actions"]
    if len(screws) != 66 or len({row["axis_id"] for row in screws}) != 66 or {row["axis_id"] for row in screws} != set(axes):
        raise ValueError("all 66 retained panel screw actions required")
    for row in screws:
        source = axes[row["axis_id"]]
        if (row["panel"], row["first"], row["receiver"], row["second"]) != (
                source["panel"], source["panel"], source["receiver"], source["receiver"]):
            raise ValueError("panel screw body/receiver identity differs")
        if np.linalg.norm(arithmetic.vector(row["force_on_first_xyz_n"]) + arithmetic.vector(row["force_on_receiver_xyz_n"])) > 1e-7:
            raise ValueError("panel screw exported force dual differs")
    actions = [row for name in ("common_shaft_bearing_actions", "shaft_end_capture_actions", "panel_screw_actions", "contact_actions")
               for row in demand[name]]
    for row in actions:
        if (row["state_id"], row["case_id"], row["accessory_placement"]) != (
                demand["state_id"], demand["case_id"], demand["accessory_placement"]):
            raise ValueError("132-body action mixes states or loads")
    closure = verify_body_closure(demand, bodies, loads, actions)
    response = demand["response"]
    tolerance, residual = [support.finite_scalar(response[key]) for key in
                           ("generalized_residual_tolerance_n", "gradient_inf_n")]
    if (response.get("converged") is not True or response.get("physical_residual_uses_unmodified_laws") is not True
            or demand.get("usable_conditional_actions") is not True or not 0. < tolerance <= 1e-5 or not 0. <= residual <= tolerance):
        raise ValueError("physical common-shaft state fails bounded unmodified-law convergence")
    pins[relative] = COMMON_PRODUCER_SHA
    pins[str(Path(support.__file__).relative_to(ROOT))] = SUPPORT_AUDIT_SHA
    if support.digest(COMMON_PRODUCER) != COMMON_PRODUCER_SHA:
        raise ValueError("physical common-shaft producer changed during audit")
    return {"independent_common_shaft_support_load_and_equilibrium_checks_pass":
            bool(finished["finished_support_geometry_checks_pass"] and closure["all_132_body_and_global_wrench_checks_pass"]),
            "shaft_geometry": geometry, "finished_support": finished, "equilibrium": closure,
            "gravity_remap_residual_force_n": remap[:3].tolist(), "gravity_remap_residual_moment_nmm": remap[3:].tolist(),
            "source_sha256": pins, "native_or_CAD_execution": False,
            "physical_stiffness_bounds_or_structural_acceptance": False}
