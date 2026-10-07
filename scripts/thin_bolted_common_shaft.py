"""Conditional common physical shaft beams for the frozen thin frame.

Existing beam/plate/port algebra is reused. Each own bore has its radial gap;
washer/head/nut capture acts only in axial compression at its actual datums.
No friction or rotational end clamp is supplied. The free common shaft twist
is a numerical gauge, without a torque reaction. Washer pressure/prying and
geometrically nonlinear contact remain separate unresolved methods.
"""

from __future__ import annotations

import argparse
import copy
import json
from collections import defaultdict
from itertools import pairwise
from pathlib import Path

import numpy as np
from scipy.sparse import coo_matrix, csr_matrix, hstack, vstack

from scripts import thin_bolted_frame_mechanics as frame

UNIT = frame.PACKET / "timber-bolt-resistance-v4.json"
UNIT_SHA = "5e78ac49a2db2050caf7ee7d2002d0ebf4f9a92496e857a0e2d652629bd0d848"
LOADED_PRODUCER_SHA256 = frame.sha(Path(__file__))
LEGACY_ELASTIC_ACTIONS = frame.elastic_actions
METHOD_SOURCES = {
    "steel_E_analogy": {"url": "https://www.aisc.org/globalassets/aisc/publications/standards/a360-16-spec-and-commentary_june-2018.pdf",
                        "locator": "ANSI/AISC360-16 symbolsE:200000MPa; generic structural-steel elastic analogy only, not bolt product/strength qualification"},
    "steel_nu_analogy": {"url": "https://tsapps.nist.gov/publication/get_pdf.cfm?pub_id=101043",
                         "locator": "NISTNCSTAR1-6C Fig3-3(b),ambient steelPoisson ratio near0.3; declared scenario,not measuredbolt property"},
    "circular_shear_scenario": {"coefficient": .9,
                                "basis": "Declared approximate circular-section Timoshenko shear factor; analytic coupon uses same assumption,not an independently measured correction"},
}


def shaft_inputs(layout: dict, unit: dict, cache: dict) -> list[dict]:
    """Pure JSON geometry:82finished wood spans,72plate spans and140own washers."""
    wood = defaultdict(list)
    for row in unit["finished_geometry_queries"]["receiver_boundary_geometry"]:
        wood[row["axis_id"]].append(row)
    roles = defaultdict(dict)
    for row in cache["parts"]:
        if row["kind"] in ("shaft", "head", "head_washer", "nut_washer", "nut"):
            roles[row["axis_id"]][row["kind"]] = row
    result = []
    for axis in layout["installed_axes"]:
        p = np.array(axis["point"])
        g = np.array(axis["direction"])
        g /= np.linalg.norm(g)
        basis = frame.connector_basis(g)
        grip, before, after = axis["grip_mm"], axis["before_plate_mm"], axis["after_plate_mm"]
        surfaces = []
        for row in wood[axis["id"]]:
            for interval in row["finished_full_wall_intervals_from_axis_point_mm"]:
                surfaces.append({"host": row["member"], "kind": "wood", "interval_mm": list(interval),
                                 "grain_axis_xyz": row["grain_axis_xyz"]})
        for attachment in axis["attachments"]:
            s = float((np.array(attachment["entry_xyz_mm"]) - p) @ g)
            if abs(s) < 1e-5:
                interval = [-before, 0.]
            elif abs(s - grip) < 1e-5:
                interval = [grip, grip + after]
            else:
                raise ValueError("fitting flange does not occupy either wood-stack face")
            if interval[1] - interval[0] <= 0.:
                raise ValueError("occupied fitting plate has no thickness")
            surfaces.append({"host": attachment["angle_id"], "kind": "steel", "flange": attachment["flange"],
                             "receiver": attachment["receiver"], "interval_mm": interval,
                             "entry_xyz_mm": attachment["entry_xyz_mm"]})
        ends = []
        for end, support_s, role, sign in (("head", -before, "head_washer", -1.),
                                            ("nut", grip + after, "nut_washer", 1.)):
            washer = roles[axis["id"]][role]
            center_s = float((np.array(washer["center_of_mass_xyz_mm"]) - p) @ g)
            thickness = 2. * sign * (center_s - support_s)
            if not 0. < thickness < 10.:
                raise ValueError("own washer thickness is inconsistent with its support face")
            matching = [r for r in surfaces if r["kind"] == "steel" and
                        abs(r["interval_mm"][0 if end == "head" else 1] - support_s) < 1e-5]
            if not matching:
                target = 0. if end == "head" else grip
                matching = [r for r in surfaces if r["kind"] == "wood" and
                            abs(r["interval_mm"][0 if end == "head" else 1] - target) < 1e-5]
            if len(matching) != 1:
                raise ValueError("washer support must have exactly one adjacent actual host")
            ends.append({"end": end, "host": matching[0]["host"], "flange": matching[0].get("flange"),
                         "support_s_mm": support_s, "pressure_face_s_mm": support_s + sign * thickness,
                         "own_washer_thickness_mm": thickness, "direction_on_shaft_xyz": (sign * g).tolist(),
                         "washer_id": washer["id"]})
        start = ends[0]["pressure_face_s_mm"]
        tip = start + axis["nominal_under_head_length_mm"]
        if tip < ends[1]["pressure_face_s_mm"]:
            raise ValueError("nominal shaft does not reach its nut washer pressure plane")
        shaft = roles[axis["id"]]["shaft"]
        center = float((np.array(shaft["center_of_mass_xyz_mm"]) - p) @ g)
        if abs(center - .5 * (start + tip)) > 1e-5:
            raise ValueError("nominal shaft span differs from source-bound metal centroid")
        result.append({"axis_id": axis["id"], "body": "shaft/" + axis["id"], "point": p,
                       "basis": basis, "diameter_mm": axis["diameter_mm"],
                       "bore_diameter_mm": axis["bore_diameter_mm"], "shaft_interval_mm": [start, tip],
                       "surfaces": surfaces, "ends": ends, "metal_roles": list(roles[axis["id"]].values())})
    if len(result) != 70 or sum(r["kind"] == "wood" for a in result for r in a["surfaces"]) != 82:
        raise ValueError("common shaft geometry census differs")
    if sum(r["kind"] == "steel" for a in result for r in a["surfaces"]) != 72:
        raise ValueError("common shaft flange census differs")
    return result


def circular_properties(diameter: float) -> tuple[float, float, float]:
    if diameter <= 0. or not np.isfinite(diameter):
        raise ValueError("positive finite circular shaft diameter required")
    return np.pi * diameter**2 / 4., np.pi * diameter**4 / 64., np.pi * diameter**4 / 32.


def reduced_shaft_matrix(stations, diameter, E, G):
    """Local q=(u,v,w,1000theta_x,1000theta_y,1000theta_z);omit first twist."""
    stations = np.array(stations, dtype=float)
    if (len(stations) < 2 or not np.isfinite(stations).all() or np.any(np.diff(stations) <= 0.) or
            not np.isfinite([E, G]).all() or min(E, G) <= 0.):
        raise ValueError("strictly increasing shaft stations required")
    A, I, J = circular_properties(diameter)
    index = np.arange(6 * len(stations)).reshape(-1, 6)
    index[0, 3] = -1
    keep = index >= 0
    index[keep] = np.arange(int(keep.sum()))
    n = int(keep.sum())
    rows, cols, values, elements = [], [], [], []
    scale = np.tile([1., 1., 1., 1. / frame.ROTATION_SCALE, 1. / frame.ROTATION_SCALE, 1. / frame.ROTATION_SCALE], 2)
    for i, L in enumerate(np.diff(stations)):
        k = frame.beam_stiffness(float(L), A, I, I, J, E, G, shear_factor=.9)
        dofs = np.r_[index[i], index[i + 1]]
        selected = dofs >= 0
        block = k * scale[:, None] * scale[None, :]
        ii, jj = np.nonzero(abs(block[np.ix_(selected, selected)]) > 1e-14)
        chosen = dofs[selected]
        rows.extend(chosen[ii]); cols.extend(chosen[jj]); values.extend(block[np.ix_(selected, selected)][ii, jj])
        elements.append({"local_K": k, "dofs": dofs, "stations_mm": stations[i:i + 2], "scale": scale})
    return coo_matrix((values, (rows, cols)), shape=(n, n)).tocsr(), index, elements


class CommonShaftSystem:
    """Augment one existing frame assembly; create fresh operators only once.

    Call frame.load_cases before augmentation; then remap_bolt_gravity on each
    case. Existing frame.elastic_connections supplies panels/flange/floor;
    replace its fitting_bolt/retained_bolt groups with bearing_groups, and append
    end_captures. Generic constitutive/contact solve and body balance are reused.
    """

    def __init__(self, assembly, shafts: list[dict], *, steel_E_mpa=200000., steel_nu=.3,
                 diameter_scale=1., wood_foundation_n_mm2=1000. / 38.1,
                 plate_foundation_n_mm2=10000. / 5.55625, end_capture_n_mm=1000., max_segment_mm=25.):
        if (min(steel_E_mpa, diameter_scale, wood_foundation_n_mm2, plate_foundation_n_mm2,
                end_capture_n_mm, max_segment_mm) <= 0. or not -.9 < steel_nu < .5 or
                not np.isfinite([steel_E_mpa, steel_nu, diameter_scale, wood_foundation_n_mm2,
                                 plate_foundation_n_mm2, end_capture_n_mm, max_segment_mm]).all()):
            raise ValueError("positive finite scenario properties required")
        self.assembly, self.shafts = assembly, {}
        self.original_port, self.original_rigid_modes = assembly.port, assembly.rigid_modes
        self.parameters = {"shaft_steel_E_mpa": steel_E_mpa, "shaft_steel_nu": steel_nu,
                           "shaft_diameter_scale": diameter_scale, "shaft_max_segment_mm": max_segment_mm,
                           "wood_radial_foundation_n_mm2": wood_foundation_n_mm2,
                           "plate_radial_foundation_n_mm2": plate_foundation_n_mm2,
                           "end_capture_stiffness_n_mm": end_capture_n_mm,
                           "moduli_stiffness_and_diameter_are_measured_or_bounds": False,
                           "shaft_E_nu_basis": "declared ordinary structural-steel elastic scenario, not a measured product property or strength",
                           "circular_shear_factor_basis": "declared0.9Timoshenko circular-section analogy; analytical cantilever coupon only",
                           "washer_rotational_clamp_or_friction": False,
                           "circular_shear_factor_scenario": .9}
        blocks = []
        for source in shafts:
            if (not np.isfinite([source["diameter_mm"], source["bore_diameter_mm"]]).all() or
                    source["diameter_mm"] <= 0. or source["bore_diameter_mm"] < source["diameter_mm"]):
                raise ValueError("positive finite major diameter and nonnegative own bore gap required")
            events = set(source["shaft_interval_mm"])
            for surface in source["surfaces"]:
                a, b = surface["interval_mm"]
                events.update((a, .5 * (a + b), b))
            for end in source["ends"]:
                events.update((end["support_s_mm"], end["pressure_face_s_mm"]))
            coarse = []
            for event in sorted(events):
                if not coarse or event - coarse[-1] > 1e-6:
                    coarse.append(event)
            stations = []
            for a, b in pairwise(coarse):
                stations.extend(np.linspace(a, b, max(1, int(np.ceil((b - a) / max_segment_mm))) + 1)[:-1])
            stations.append(coarse[-1])
            k, index, elements = reduced_shaft_matrix(stations, source["diameter_mm"] * diameter_scale,
                                                       steel_E_mpa, steel_E_mpa / (2 * (1 + steel_nu)))
            offset = assembly.ndof
            assembly.ndof += k.shape[0]
            actual = np.where(index >= 0, index + offset, -1)
            row = {**source, "stations": np.array(stations), "index": actual,
                   "offset": offset, "ndof": k.shape[0], "elements": elements}
            self.shafts[source["body"]] = row
            blocks.append((offset, k))
        extra = assembly.ndof - assembly.K.shape[0]
        assembly.K = vstack((hstack((assembly.K, csr_matrix((assembly.K.shape[0], extra)))),
                            csr_matrix((extra, assembly.ndof))), format="csr")
        for offset, k in blocks:
            coo = k.tocoo()
            assembly.K += coo_matrix((coo.data, (coo.row + offset, coo.col + offset)), shape=assembly.K.shape).tocsr()
        assembly.port, assembly.rigid_modes = self.port, self.rigid_modes
        assembly.geo = copy.deepcopy(assembly.geo)
        for row in self.shafts.values():
            mass = sum(r["volume_mm3"] * 7850e-9 for r in row["metal_roles"])
            center = sum((np.array(r["center_of_mass_xyz_mm"]) * r["volume_mm3"] * 7850e-9
                          for r in row["metal_roles"]), np.zeros(3)) / mass
            assembly.geo["bodies"].append({"id": row["body"], "kind": "shaft_assembly",
                                            "mass_kg": mass, "center_xyz_mm": center.tolist()})
        self.bearing_groups, self.end_captures = [], []
        for row in self.shafts.values():
            p, g = row["point"], row["basis"][0]
            for surface_i, surface in enumerate(row["surfaces"]):
                a, b = surface["interval_mm"]
                foundation = wood_foundation_n_mm2 if surface["kind"] == "wood" else plate_foundation_n_mm2
                for quad, abscissa in enumerate((-1. / np.sqrt(3.), 1. / np.sqrt(3.))):
                    s, weight = .5 * (a + b) + .5 * (b - a) * abscissa, .5 * (b - a)
                    point = p + g * s
                    B = csr_matrix(row["basis"]) @ (self.port(row["body"], point) -
                            self.port(surface["host"], point, surface.get("flange")))
                    self.bearing_groups.append({"id": row["axis_id"] + f"/bearing-{surface_i}-{quad}",
                        "axis_id": row["axis_id"], "kind": "common_shaft_bearing", "first": row["body"],
                        "second": surface["host"], "point_xyz_mm": point.tolist(), "basis": row["basis"],
                        "B": B, "ka": 0., "kl": foundation * weight,
                        "clearance": .5 * (row["bore_diameter_mm"] - row["diameter_mm"]),
                        "tension_only": False, "surface": surface, "surface_index": surface_i,
                        "quad_index": quad, "axis_station_mm": s, "weight_length_mm": weight})
            for end in row["ends"]:
                point, support = p + g * end["pressure_face_s_mm"], p + g * end["support_s_mm"]
                direction = np.array(end["direction_on_shaft_xyz"])
                B = -csr_matrix(direction.reshape(1, 3)) @ (self.port(row["body"], point) -
                        self.port(end["host"], support, end.get("flange")))
                self.end_captures.append({"id": row["axis_id"] + "/" + end["end"] + "-capture",
                    "axis_id": row["axis_id"], "kind": "shaft_end_capture", "first": row["body"],
                    "second": end["host"], "point_xyz_mm": point.tolist(),
                    "host_support_point_xyz_mm": support.tolist(), "direction_xyz": direction.tolist(),
                    "B": B, "stiffness": end_capture_n_mm, "end": end})

    def port(self, body, point, flange=None):
        if body not in self.shafts:
            return self.original_port(body, point, flange)
        row = self.shafts[body]
        point = np.array(point)
        g, basis = row["basis"][0], row["basis"]
        s = float((point - row["point"]) @ g)
        i = int(np.clip(np.searchsorted(row["stations"], s) - 1, 0, len(row["stations"]) - 2))
        a, b = row["stations"][i:i + 2]
        t = float(np.clip((s - a) / (b - a), 0., 1.))
        center = row["point"] + g * (a + t * (b - a))
        block = frame.point_matrix(point, center) @ np.block([[basis.T, np.zeros((3, 3))],
                                                               [np.zeros((3, 3)), basis.T]])
        block = np.hstack(((1 - t) * block, t * block))
        index = np.r_[row["index"][i], row["index"][i + 1]]
        return self.assembly.embed(block[:, index >= 0], index[index >= 0])

    def rigid_modes(self):
        result = self.original_rigid_modes()
        for row in self.shafts.values():
            for index, s in zip(row["index"], row["stations"], strict=True):
                point = row["point"] + row["basis"][0] * s
                local = np.vstack((row["basis"] @ np.hstack((np.eye(3), -frame.cross_matrix(point - frame.REFERENCE))),
                                   np.hstack((np.zeros((3, 3)), row["basis"] * frame.ROTATION_SCALE))))
                local[3] = 0.  # Remove only the unloaded common axial twist.
                result[index[index >= 0]] = local[index >= 0]
        return result

    def remap_bolt_gravity(self, case):
        """Move all350exact metal role masses from conditional hosts to own shaft."""
        result = copy.deepcopy(case)
        role_ids = {r["id"] for s in self.shafts.values() for r in s["metal_roles"]}
        prefix = tuple("bolt-weight/" + i + "/gravity-share-" for i in role_ids)
        result["loads"] = [r for r in result["loads"] if not r["id"].startswith(prefix)]
        for row in self.shafts.values():
            for role in row["metal_roles"]:
                result["loads"].append({"id": "physical-bolt-metal/" + role["id"], "body": row["body"],
                    "point_xyz_mm": role["center_of_mass_xyz_mm"], "force_xyz_n": [0., 0., -role["volume_mm3"] * 7850e-9 * frame.GRAVITY],
                    "conditional_gravity_basis": "exact role steel-volume mass at its CAD centroid; own physical shaft assembly"})
        old = sum((frame.wrench(r["force_xyz_n"], r["point_xyz_mm"]) for r in case["loads"]), np.zeros(6))
        new = sum((frame.wrench(r["force_xyz_n"], r["point_xyz_mm"]) for r in result["loads"]), np.zeros(6))
        if max(abs(new[:3] - old[:3])) > 1e-8 or max(abs(new[3:] - old[3:])) > 1e-5:
            raise ValueError("physical shaft gravity remap changes global wrench")
        result["applied_force_xyz_n"] = new[:3].tolist()
        result["applied_moment_about_global_origin_xyz_nmm"] = new[3:].tolist()
        result["shaft_metal_gravity_remap_residual_n_nmm"] = (new - old).tolist()
        return result

    def recovery(self, q):
        """Actual internal shaft beam actions; no capacity or root-shank adoption."""
        result = []
        for row in self.shafts.values():
            elements = []
            own_q = q[row["offset"]:row["offset"] + row["ndof"]]
            for element in row["elements"]:
                value = np.zeros(12)
                selected = element["dofs"] >= 0
                value[selected] = own_q[element["dofs"][selected]] * element["scale"][selected]
                action = element["local_K"] @ value
                elements.append({"stations_from_axis_point_mm": element["stations_mm"].tolist(),
                                 "local_end_actions_n_nmm": action.tolist(),
                                 "distributed_external_loads_subtracted": False})
            result.append({"axis_id": row["axis_id"], "body": row["body"],
                           "axis_point_xyz_mm": row["point"].tolist(), "axis_direction_xyz": row["basis"][0].tolist(),
                           "shaft_interval_from_axis_point_mm": row["shaft_interval_mm"],
                           "mesh_stations_from_axis_point_mm": row["stations"].tolist(),
                           "basis_axis_tangent1_tangent2_xyz": row["basis"].tolist(), "elements": elements,
                           "elastic_section_diameter_mm": row["diameter_mm"] * self.parameters["shaft_diameter_scale"],
                           "bearing_contact_major_diameter_mm": row["diameter_mm"],
                           "body_root_and_delivered_shank_exposure_adopted": False,
                           "first_element_internal_twist_end_action_nmm": elements[0]["local_end_actions_n_nmm"][3],
                           "common_axial_twist_gauge_is_unloaded_not_a_physical_restraint": True,
                           "washer_end_pressure_and_prying_solved": False,
                           "physical_diameter_or_stiffness_bounds_established": False})
        return result

    def compatible_actions(self, case, response, groups, contacts, tangents):
        """Fresh132-body recovery, with physical wood/steel/shaft paths separate."""
        old_groups = [(i, g) for i, g in enumerate(groups) if g["kind"] != "common_shaft_bearing"]
        old_contacts = [(i, c) for i, c in enumerate(contacts) if c["kind"] != "shaft_end_capture"]
        filtered = {**response,
                    "connector_local_force_n": [response["connector_local_force_n"][i] for i, _ in old_groups],
                    "normal_contact_force_n": np.array([response["normal_contact_force_n"][i] for i, _ in old_contacts])}
        result = LEGACY_ELASTIC_ACTIONS(self.assembly, case, filtered,
                                        [g for _, g in old_groups], [c for _, c in old_contacts], tangents)
        bearings, captures = [], []
        for group, local in zip(groups, response["connector_local_force_n"], strict=True):
            if group["kind"] != "common_shaft_bearing":
                continue
            force = -group["basis"].T @ local
            bearings.append({"id": group["id"], "axis_id": group["axis_id"], "kind": group["kind"],
                "first": group["first"], "second": group["second"], "point_xyz_mm": group["point_xyz_mm"],
                "force_on_first_xyz_n": force.tolist(), "force_on_second_xyz_n": (-force).tolist(),
                "moment_on_first_at_point_xyz_nmm": [0., 0., 0.], "moment_on_second_at_point_xyz_nmm": [0., 0., 0.],
                "surface_index": group["surface_index"], "surface_material": group["surface"]["kind"],
                "host": group["surface"]["host"], "flange": group["surface"].get("flange"),
                "surface_interval_mm": group["surface"]["interval_mm"], "quad_index": group["quad_index"],
                "axis_station_mm": group["axis_station_mm"], "weight_length_mm": group["weight_length_mm"],
                "foundation_spring_n_mm": group["kl"], "own_bore_radial_gap_mm": group["clearance"]})
        for contact, scalar in zip(contacts, response["normal_contact_force_n"], strict=True):
            if contact["kind"] != "shaft_end_capture":
                continue
            force = scalar * np.array(contact["direction_xyz"])
            captures.append({"id": contact["id"], "axis_id": contact["axis_id"], "kind": contact["kind"],
                "first": contact["first"], "second": contact["second"], "point_xyz_mm": contact["point_xyz_mm"],
                "host_support_point_xyz_mm": contact["host_support_point_xyz_mm"],
                "force_on_first_xyz_n": force.tolist(), "force_on_second_xyz_n": (-force).tolist(),
                "moment_on_first_at_point_xyz_nmm": [0., 0., 0.], "moment_on_second_at_point_xyz_nmm": [0., 0., 0.],
                "compression_n": float(scalar), "end": contact["end"], "physical_pressure_or_prying_resolved": False,
                "unilateral_axial_centre_capture_without_rotational_clamp": True})
        actions = [*result["attachment_actions"], *result["retained_bolt_actions"], *result["panel_screw_actions"],
                   *result["contact_actions"], *result["floor_actions"], *bearings, *captures]
        balance = {row["id"]: np.zeros(6) for row in self.assembly.geo["bodies"]}
        for load in case["loads"]:
            balance[load["body"]] += frame.wrench(load["force_xyz_n"], load["point_xyz_mm"], frame.REFERENCE)
        for row in actions:
            balance[row["first"]] += frame.wrench(row["force_on_first_xyz_n"], row["point_xyz_mm"], frame.REFERENCE)
            if row.get("second", "floor") != "floor":
                second_point = row.get("host_support_point_xyz_mm", row["point_xyz_mm"])
                balance[row["second"]] -= frame.wrench(row["force_on_first_xyz_n"], second_point, frame.REFERENCE)
        force_error = max(float(np.linalg.norm(r[:3])) for r in balance.values())
        moment_error = max(float(np.linalg.norm(r[3:])) for r in balance.values())
        result["body_equilibrium_residuals"] = [{"body": name, "force_xyz_n": value[:3].tolist(),
                                                "moment_about_reference_xyz_nmm": value[3:].tolist()}
                                               for name, value in balance.items()]
        result["equilibrium_verification"] = {"all_bodies": len(balance), "maximum_body_force_norm_n": force_error,
            "maximum_body_moment_about_reference_norm_nmm": moment_error, "force_tolerance_n": frame.BODY_FORCE_TOLERANCE_N,
            "moment_tolerance_nmm": frame.BODY_MOMENT_TOLERANCE_NMM,
            "all_body_and_global_checks_pass": bool(force_error < frame.BODY_FORCE_TOLERANCE_N and
                moment_error < frame.BODY_MOMENT_TOLERANCE_NMM and
                np.linalg.norm(result["global_equilibrium_residual_force_n"]) < frame.BODY_FORCE_TOLERANCE_N and
                np.linalg.norm(result["global_equilibrium_residual_moment_nmm"]) < frame.BODY_MOMENT_TOLERANCE_NMM)}
        section_case = {**case, "equilibrium_feasibility_witness": {"feasible": True,
            "point_actions": [*result["panel_screw_actions"], *bearings],
            "compression_actions": [*result["contact_actions"], *result["floor_actions"], *captures]}}
        result["member_section_action_samples"] = frame.member_sections(section_case, self.assembly.geo)
        for row in result["member_section_action_samples"]:
            row["action_source"] = "same-state common shaft bearing/end capture, panel/flange/floor contact and affine selfweight"
            row["physical_demand_bounds_established"] = False
        wood, steel = [], []
        for shaft in self.shafts.values():
            for surface_i, surface in enumerate(shaft["surfaces"]):
                selected = [r for r in bearings if r["axis_id"] == shaft["axis_id"] and r["surface_index"] == surface_i]
                if surface["kind"] == "steel":
                    reference = np.array(surface["entry_xyz_mm"])
                else:
                    reference = shaft["point"] + shaft["basis"][0] * np.mean(surface["interval_mm"])
                own_captures = [r for r in captures if r["axis_id"] == shaft["axis_id"] and r["second"] == surface["host"]]
                force, moment = np.zeros(3), np.zeros(3)
                for row in [*selected, *own_captures]:
                    own_force = np.array(row["force_on_second_xyz_n"])
                    point = np.array(row.get("host_support_point_xyz_mm", row["point_xyz_mm"]))
                    force += own_force
                    moment += np.cross(point - reference, own_force)
                value = {"axis_id": shaft["axis_id"], "host": surface["host"], "surface_index": surface_i,
                    "surface_interval_mm": surface["interval_mm"], "point_xyz_mm": reference.tolist(),
                    "force_on_host_xyz_n": force.tolist(), "moment_on_host_at_point_xyz_nmm": moment.tolist(),
                    "own_bearing_points": [r["id"] for r in selected], "own_end_captures": [r["id"] for r in own_captures],
                    "force_on_opposed_flange_or_other_host_not_inferred": True}
                if surface["kind"] == "steel":
                    value.update(angle_id=surface["host"], flange=surface["flange"], receiver=surface["receiver"],
                                 force_on_steel_xyz_n=force.tolist(), moment_on_steel_at_point_xyz_nmm=moment.tolist())
                    steel.append(value)
                else:
                    value.update(member=surface["host"], grain_axis_xyz=surface["grain_axis_xyz"])
                    wood.append(value)
        result.update(common_shaft_bearing_actions=bearings, shaft_end_capture_actions=captures,
                      common_shaft_wood_bearing_actions=wood, common_shaft_steel_port_actions=steel,
                      common_shaft_element_actions=self.recovery(response["q"]),
                      common_shaft_section_cut_actions=self.section_cut_actions(case, bearings, captures),
                      body_identities=[r["id"] for r in self.assembly.geo["bodies"]],
                      shaft_axial_torque_balance_nmm={s["axis_id"]: float(s["basis"][0] @
                          (balance[s["body"]][3:] - np.cross(s["point"] - frame.REFERENCE, balance[s["body"]][:3])))
                          for s in self.shafts.values()})
        return result

    def section_cut_actions(self, case, bearings, captures):
        """Same-cut complete signed shaft wrenches from physical external rows.

        Internal element nodal actions alone do not resolve cuts through
        interpolated load ports. This recovery uses the exported radial forces,
        end captures and each role's point gravity at its actual own datum.
        """
        result = []
        for shaft in self.shafts.values():
            loads = [(np.array(r["point_xyz_mm"]), np.array(r["force_xyz_n"]))
                     for r in case["loads"] if r["body"] == shaft["body"]]
            loads += [(np.array(r["point_xyz_mm"]), np.array(r["force_on_first_xyz_n"]))
                      for r in [*bearings, *captures] if r["first"] == shaft["body"]]
            lo, hi = shaft["shaft_interval_mm"]
            stations = list(np.linspace(lo, hi, 33)) + shaft["stations"].tolist()
            for point, _ in loads:
                s = float((point - shaft["point"]) @ shaft["basis"][0])
                stations.extend((float(np.clip(s - 1e-7, lo, hi)), float(np.clip(s + 1e-7, lo, hi))))
            cuts = []
            for station in sorted(set(stations)):
                point = shaft["point"] + shaft["basis"][0] * station
                force, moment = np.zeros(3), np.zeros(3)
                for applied_point, value in loads:
                    if float((applied_point - shaft["point"]) @ shaft["basis"][0]) < station:
                        force -= value
                        moment -= np.cross(applied_point - point, value)
                cuts.append({"station_from_axis_point_mm": station, "point_xyz_mm": point.tolist(),
                             "local_N_V1_V2_T_M1_M2_n_nmm": np.r_[shaft["basis"] @ force, shaft["basis"] @ moment].tolist()})
            result.append({"axis_id": shaft["axis_id"], "body": shaft["body"],
                "axis_point_xyz_mm": shaft["point"].tolist(), "axis_direction_xyz": shaft["basis"][0].tolist(),
                "shaft_interval_from_axis_point_mm": shaft["shaft_interval_mm"],
                "mesh_stations_from_axis_point_mm": shaft["stations"].tolist(),
                "basis_axis_tangent1_tangent2_xyz": shaft["basis"].tolist(), "cuts": cuts,
                "sign_convention": "force and couple on the lower-axis-station part from omitted higher-station part",
                "elastic_section_diameter_mm": shaft["diameter_mm"] * self.parameters["shaft_diameter_scale"],
                "bearing_contact_major_diameter_mm": shaft["diameter_mm"],
                "point_gravity_role_centroids_preserved": True,
                "body_root_and_delivered_shank_exposure_adopted": False,
                "physical_demand_bounds_or_second_order_solution": False})
        return result


def read_inputs():
    for path, expected in ((UNIT, UNIT_SHA), (frame.GEOMETRY_CACHE, frame.GEOMETRY_CACHE_SHA),
                           (frame.LAYOUT, frame.LAYOUT_SHA)):
        if frame.sha(path) != expected:
            raise ValueError("frozen common-shaft input differs")
    layout, unit, cache = [json.loads(path.read_text()) for path in (frame.LAYOUT, UNIT, frame.GEOMETRY_CACHE)]
    return shaft_inputs(layout, unit, cache)


def source_pins():
    if frame.sha(Path(__file__)) != LOADED_PRODUCER_SHA256:
        raise ValueError("common-shaft producer edited after import")
    pins = {"scripts/thin_bolted_common_shaft.py": LOADED_PRODUCER_SHA256,
            "scripts/thin_bolted_frame_mechanics.py": frame.LOADED_PRODUCER_SHA256,
            str(UNIT.relative_to(frame.ROOT)): UNIT_SHA,
            str(frame.GEOMETRY_CACHE.relative_to(frame.ROOT)): frame.GEOMETRY_CACHE_SHA,
            str(frame.LAYOUT.relative_to(frame.ROOT)): frame.LAYOUT_SHA}
    for path, expected in pins.items():
        if frame.sha(frame.ROOT / path) != expected:
            raise ValueError("common-shaft source changed during evaluation: " + path)
    return pins


def method_coupons():
    """Small executable known answers and authenticated geometry, without CAD/FE solves."""
    L, d, E, G = 1000., 12.7, 200000., 200000. / 2.6
    A, I, _ = circular_properties(d)
    K, index, _ = reduced_shaft_matrix([0., L], d, E, G)
    free = index[-1]
    rows = []
    for dof in range(3):
        expected = L / (E * A) if dof == 0 else L**3 / (3 * E * I) + L / (.9 * G * A)
        observed = np.linalg.solve(K.toarray()[np.ix_(free, free)], np.eye(6)[dof])[dof]
        rows.append({"dof": dof, "unit_force_n": 1., "expected_tip_translation_mm": expected,
                     "observed_tip_translation_mm": float(observed), "relative_error": float(abs(observed / expected - 1.))})
    K, index, elements = reduced_shaft_matrix([0., 100., 200., 300.], d, E, G)
    applied, q = np.zeros(K.shape[0]), np.zeros(K.shape[0])
    applied[index[1, 1]], applied[index[2, 1]] = 4., -3.
    free = index[1:].ravel()
    q[free] = np.linalg.solve(K.toarray()[np.ix_(free, free)], applied[free])
    actions = []
    for element in elements:
        value = np.zeros(12)
        selected = element["dofs"] >= 0
        value[selected] = q[element["dofs"][selected]] * element["scale"][selected]
        actions.append((element["local_K"] @ value).tolist())
    shafts = read_inputs()
    test = frame.ROOT / "tests/test_thin_bolted_common_shaft.py"
    field = frame.PACKET / "compatible-frame-a12-rear-finished-floor-v4.json"
    return {"schema": "thin_bolted_common_shaft_method_coupons/v1", "source_sha256": source_pins(),
        "method_sources": METHOD_SOURCES, "circular_known_answers": rows,
        "unequal_opposed_load_coupon": {"applied_shear_resultant_n": 1., "middle_span_shear_n": actions[1][1],
            "root_bending_moment_nmm": actions[0][5], "all_element_actions_n_nmm": actions},
        "geometry_census": {"physical_shafts": len(shafts), "wood_bore_spans": 82, "steel_bore_spans": 72,
            "radial_gauss_ports": 308, "own_axial_captures": 140, "physical_metal_roles": 350},
        "validation": {"tests_path": str(test.relative_to(frame.ROOT)), "tests_sha256": frame.sha(test),
            "test_command": "OPENBLAS_NUM_THREADS=1 .venv/bin/pytest -q tests/test_thin_bolted_common_shaft.py",
            "expected_test_count": 17, "lint_command": ".venv/bin/ruff check scripts/thin_bolted_common_shaft.py tests/test_thin_bolted_common_shaft.py",
            "gravity_fixture_input_path": str(field.relative_to(frame.ROOT)), "gravity_fixture_input_sha256": frame.sha(field),
            "coverage": ["circular axial/two-bending/shear known answers", "unequal opposed shaft loads and internal span shear",
                "two separate bore gaps and host compliances", "unloaded twist gauge", "common rigid-body port invariance",
                "actual82wood/72steel spans and each own washer", "350metal-role gravity conservation with274screw/Tnut shares retained",
                "distinct capture datums and transported steel-hole wrenches", "complete external-force section cut recovery",
                "nonfinite scenario inputs and negative own radial gap rejection", "elastic diameter independent of nominal bearing gap"]},
        "limits": ["Two Gauss points per bearing span and linear beam/port interpolation are explicit discretization scenarios; local pressure and stiffness bounds are not established.",
            "Elastic diameter scaling does not alter nominal major-diameter bore clearance or adopt delivered body/root exposure.",
            "Own axial captures do not solve washer pressure, bending, prying, actual seating or rotational friction.",
            "These small coupons validate method algebra only; no coupled candidate state, geometric nonlinear applicability, strength acceptance or physical release is implied."],
        "release_flags": {"structural_acceptance": False, "fabrication_release": False, "climbing_release": False}}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=frame.PACKET / "common-shaft-method-coupons-v4.json")
    args = parser.parse_args()
    report = method_coupons()
    args.output.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"output": str(args.output), "sha256": frame.sha(args.output),
                      "producer_sha256": LOADED_PRODUCER_SHA256}))


if __name__ == "__main__":
    main()
