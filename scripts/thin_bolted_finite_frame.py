"""Finite frame potential composition over prepared, source-bound adapters.

No CAD, stiffness preparation or equilibrium solve occurs here. Spatial
actions use current physical points and an explicitly owned material director.
Generalized panel load corrections remain separate from physical forces.
"""

from __future__ import annotations

import copy
import inspect
from collections import Counter
from pathlib import Path

import numpy as np
from scipy.sparse import csr_matrix

from scripts import thin_bolted_finite_connectors as connectors
from scripts import thin_bolted_finite_mechanics as mechanical
from scripts import thin_bolted_finite_panel_adapter as panels_method
from scripts import thin_bolted_floor_contact as floor_method
from scripts import thin_bolted_frame_mechanics as frame
from scripts import thin_bolted_isotropic_shaft as isotropic

LOADED_PRODUCER_SHA256 = frame.sha(Path(__file__))
FROZEN_SOURCES = {**mechanical.FROZEN_SOURCES, **panels_method.BASE_PINS, **floor_method.source_pins(),
    "scripts/thin_bolted_finite_connectors.py": "6bf2c5ca9006e474d8b10642e8e4dbbfc657070c0d221b98abfbc1d2d6e03060",
    "scripts/thin_bolted_finite_mechanics.py": "8c2bf2f27538fc1d599db9ddee2efbbb6344687393781bd689de09a4998772a2",
    "scripts/thin_bolted_finite_panel_adapter.py": "c0e2534158d10ca49e6e1ee20db7b8a7e72b746b49618a18bf5ab08a9526064b",
    "scripts/thin_bolted_isotropic_shaft.py": "be8e5277999aa2ce01b4a8d81c0e9124dad9dc6023712c13e91595600c1c027a",
    "scripts/thin_bolted_floor_contact.py": "0852ced82484414621106314531e883f713f5943358541539e8750af243c2e1f",
    str((frame.PACKET / "floor-corner-stick-method-coupons-v4.json").relative_to(frame.ROOT)): "e7569ddc3ea2addb6171b3a3bcccadaa1b004b8c14da94b0eb61320b3982355e",
    "fea/current_response_materials.py": "72af0456272d91282928014d8fde557d347e36df6b7bdf23bcc41ef923d0d135"}


def source_pins(additional=None):
    pins = {**FROZEN_SOURCES, "scripts/thin_bolted_finite_frame.py": LOADED_PRODUCER_SHA256}
    for path, digest in (additional or {}).items():
        if path in pins and pins[path] != digest:
            raise ValueError("contradictory finite frame source pin: " + path)
        pins[path] = digest
    if any(frame.sha(frame.ROOT / path) != digest for path, digest in pins.items()):
        raise ValueError("finite frame composition source/input changed")
    return pins


def describe_interactions(groups, contacts, tangents):
    """Replace zero-reference linear operators by explicit finite material ports."""
    result = []

    def row(source, normal, owner, *, axial=0., lateral=0., gap=0., sign=1., first_kind="point"):
        first_point = np.asarray(source["point_xyz_mm"], dtype=float)
        second_point = np.asarray(source.get("host_support_point_xyz_mm", first_point), dtype=float)
        projection = sign * float(np.asarray(normal) @ (first_point - second_point))
        value = {"id": source.get("id", source.get("axis_id")), "kind": source["kind"],
            "first": source["first"], "second": source.get("second", "floor"),
            "reference_first_point_xyz_mm": first_point.tolist(), "reference_second_point_xyz_mm": second_point.tolist(),
            "first_port_kind": first_kind, "director_owner": owner, "reference_director_xyz": list(normal),
            "axial_stiffness_n_mm": axial, "lateral_stiffness_n_mm": lateral, "radial_gap_mm": gap,
            "axial_sign": sign, "reference_axial_projection_mm": projection,
            "axial_tension_only": True, "source_descriptor": {k: v for k, v in source.items() if k not in ("B", "basis")}}
        result.append(value)
        return value

    for group in groups:
        if group["kind"] == "common_shaft_bearing":
            value = row(group, group["basis"][0], group["second"], lateral=group["kl"], gap=group["clearance"])
            value["second_flange"] = group["surface"].get("flange")
            value["director_flange"] = value["second_flange"]
        elif group["kind"] == "panel_screw":
            row(group, group["basis"][0], group["first"], axial=group["ka"], lateral=group["kl"],
                first_kind="projected_ring")
        else:
            raise ValueError("finite common frame excludes old independent fitting/retained bolt ports")
    for contact in contacts:
        kind = contact["kind"]
        if kind == "shaft_end_capture":
            value = row(contact, contact["direction_xyz"], contact["second"], axial=contact["stiffness"], sign=-1.)
            value["second_flange"] = contact["end"].get("flange")
            value["director_flange"] = value["second_flange"]
        elif kind == "flange_contact":
            value = row(contact, contact["direction_xyz"], contact["second"], axial=contact["stiffness"], sign=-1.)
            value["first_flange"] = contact["flange"]
        elif kind == "panel_contact":
            row(contact, contact["direction_xyz"], contact["first"], axial=contact["stiffness"], sign=-1.)
        elif kind == "floor_normal":
            row(contact, [0., 0., 1.], "floor", axial=contact["stiffness"], sign=-1.)
        else:
            raise ValueError("unsupported finite normal contact descriptor")
    by_host = {}
    for tangent in tangents:
        host = tangent.get("physical_first", tangent["first"])
        support = tangent.get("floor_support_id")
        by_host.setdefault((host, support), []).append(tangent)
    for (host, support), pair in by_host.items():
        if (len(pair) != 2 or pair[0]["stiffness"] != pair[1]["stiffness"] or
                not np.allclose(pair[0]["point_xyz_mm"], pair[1]["point_xyz_mm"], atol=1e-10, rtol=0.) or
                {tuple(t["direction_xyz"]) for t in pair} != {(1., 0., 0.), (0., 1., 0.)}):
            raise ValueError("two equal co-located orthogonal XY penalties required")
        value = row({"id": (support or host) + "/finite-no-slip-xy", "kind": "floor_tangent_xy", "first": host,
                     "second": "floor", "point_xyz_mm": pair[0]["point_xyz_mm"]}, [0., 0., 1.], "floor",
                    lateral=pair[0]["stiffness"])
        value["source_component_ids"] = [t["id"] for t in pair]
        value["floor_support_id"] = support
        value["normal_contact_id"] = pair[0].get("normal_contact_id", support)
        value["support_model"] = "co-located corner XY fixed-bearing branch" if support else "legacy centroid XY fixed-bearing branch"
    if len({r["id"] for r in result}) != len(result):
        raise ValueError("unique finite interaction IDs required")
    return result


def mechanical_load_ports(assembly, case, panel_names):
    """Retain all point gravity; expand only timber selfweight as frozen2Gauss."""
    result = []
    for load in case["loads"]:
        if load["body"] in panel_names:
            continue
        if load["id"].startswith("self-weight/") and load["body"] in assembly.members:
            member = assembly.members[load["body"]]
            low, high = member["stations"][[0, -1]]
            center, axis = np.asarray(load["point_xyz_mm"]), member["axis"]
            center_s = float((center - member["start"]) @ axis)
            off = center - axis * center_s
            beta = 12. * (center_s - .5 * (low + high)) / (high - low)**2
            if min(1. + beta * (low - .5 * (low + high)), 1. + beta * (high - .5 * (low + high))) < -1e-10:
                raise ValueError("negative affine source timber gravity measure")
            for segment, (a, b) in enumerate(zip(member["stations"][:-1], member["stations"][1:], strict=True)):
                for quad, xi in enumerate((-1. / np.sqrt(3.), 1. / np.sqrt(3.))):
                    s = .5 * (a + b) + .5 * (b - a) * xi
                    fraction = .5 * (b - a) / (high - low) * (1. + beta * (s - .5 * (low + high)))
                    result.append({**load, "id": load["id"] + f"/span-{segment}/gauss-{quad}",
                        "source_load_id": load["id"], "point_xyz_mm": (off + axis * s).tolist(),
                        "force_xyz_n": (np.asarray(load["force_xyz_n"]) * fraction).tolist(),
                        "gravity_model": "source affine2Gauss per frozen beam span", "source_fraction": float(fraction),
                        "source_beam_span_mm": [float(a), float(b)], "source_station_mm": float(s), "quad_index": quad,
                        "source_member_total_force_xyz_n": load["force_xyz_n"],
                        "source_member_mass_kg": float(-load["force_xyz_n"][2] / frame.GRAVITY),
                        "source_member_center_of_mass_xyz_mm": load["point_xyz_mm"]})
        else:
            result.append({**load, "source_load_id": load["id"], "gravity_model": "own source-bound point/metal-role gravity"})
    return result


def kinematic_map(mechanics, panels):
    """No K/CAD required to replay current positions and material directors."""
    bodies = {}
    for name, member in mechanics.members.items():
        centers = member["start"] + np.asarray(member["stations"])[:, None] * member["axis"]
        bodies[name] = {"kind": "timber", "node_reference_centers_xyz_mm": centers.tolist(),
            "node_dof_indices": member["index"].tolist(), "storage_basis_columns_xyz": np.eye(3).tolist(),
            "reference_start_xyz_mm": member["start"].tolist(), "reference_axis_xyz": member["axis"].tolist(),
            "reference_stations_mm": member["stations"].tolist()}
    for name, shaft in mechanics.shafts.items():
        centers = shaft["point"] + np.asarray(shaft["stations"])[:, None] * shaft["basis"][0]
        bodies[name] = {"kind": "shaft", "node_reference_centers_xyz_mm": centers.tolist(),
            "node_dof_indices": shaft["index"].tolist(), "storage_basis_columns_xyz": shaft["storage_basis"].tolist(),
            "reference_start_xyz_mm": shaft["point"].tolist(), "reference_axis_xyz": shaft["basis"][0].tolist(),
            "reference_stations_mm": shaft["stations"].tolist()}
    for name, fitting in mechanics.fittings.items():
        bodies[name] = {"kind": "fitting", "node_reference_centers_xyz_mm": [fitting["points"][f].tolist() for f in ("beam", "post")],
            "node_dof_indices": fitting["index"].tolist(), "storage_basis_columns_xyz": np.eye(3).tolist(),
            "flange_node_map": {"beam": 0, "post": 1}, "gravity_port": "mean of two exact flange rigid-arm ports"}
    panel_map = {name: {"kind": "panel", "global_dof_indices": panel.indices.tolist(),
        "origin_xyz_mm": panel.origin.tolist(), "axes_columns_xyz": panel.axes.tolist(),
        "thickness_mm": float(panel.panel["thickness"]), "twist_scale": float(panel.panel["twist_scale"]),
        "basis_width_mm": panel.basis.width, "basis_height_mm": panel.basis.height, "basis_order": panel.basis.order,
        "basis_knots_normalized": panel.basis.knots.tolist(), "coefficient_order": "u,v,outward_w;x-major tensor cubic spline",
        "mass_reference_xy_mm": (panel.measure["mass_weights"] @ panel.measure["xy_mm"]).tolist(),
        "mass_coefficient_row": panel.measure["mass_row"].tolist()}
        for name, panel in panels.items()}
    return {"ndof": mechanics.ndof, "mechanical_bodies": bodies, "panels": panel_map,
            "mechanical_rotation_coordinates": "storage-basis rotation vector times1000; geodesic nodal interpolation"}


def current_pose_from_map(mapping, body, reference_point, q, *, flange=None, reference_director=None,
                          projected_ring=False, allow_edge_extension=False):
    """Positions/directors ONLY from saved maps/q; no K, adapter build, CAD or solve."""
    point, q = np.asarray(reference_point, dtype=float), np.asarray(q, dtype=float)
    if q.shape != (mapping["ndof"],) or not np.isfinite(q).all():
        raise ValueError("finite mapped state required")
    if body == "floor":
        return {"position_xyz_mm": point, "current_vector_xyz": np.asarray(reference_director) if reference_director is not None else None}
    if body in mapping["panels"]:
        p = mapping["panels"][body]
        basis = panels_method.method.SheetBasis(p["basis_width_mm"], p["basis_height_mm"], p["basis_order"] - 3)
        if not np.array_equal(basis.knots, p["basis_knots_normalized"]):
            raise ValueError("saved panel basis differs")
        axes, origin = np.asarray(p["axes_columns_xyz"]), np.asarray(p["origin_xyz_mm"])
        local, coef = (point - origin) @ axes, q[np.asarray(p["global_dof_indices"])].reshape(3, basis.size)
        xy = np.clip(local[:2], [0., 0.], [basis.width, basis.height])
        delta = local[:2] - xy
        if np.max(abs(delta)) > 1e-7 and not (allow_edge_extension and np.max(abs(delta)) <= 2.):
            raise ValueError("mapped panel point outside permitted material domain")
        value = basis.values(xy[None])[0]
        rx = np.array([1., 0., 0.]) + coef @ basis.values(xy[None], 1)[0]
        ry = np.array([0., 1., 0.]) + coef @ basis.values(xy[None], 0, 1)[0]
        n = np.cross(rx, ry); n /= np.linalg.norm(n)
        center = np.r_[xy, 0.] + coef @ value
        if projected_ring:
            ring, area = panels_method.method.disk_quadrature(xy, 4.5, inner=2.5)
            weights = area / area.sum()
            mean = np.r_[weights @ ring, 0.] + coef @ (weights @ basis.values(ring))
            local_position = center + n * float(n @ (mean - center))
        else:
            local_position = center + delta[0] * rx + delta[1] * ry + local[2] * n
        return {"position_xyz_mm": origin + axes @ local_position, "current_vector_xyz": axes @ n}
    row = mapping["mechanical_bodies"][body]
    indices, centers, basis = np.asarray(row["node_dof_indices"]), np.asarray(row["node_reference_centers_xyz_mm"]), np.asarray(row["storage_basis_columns_xyz"])
    if row["kind"] == "fitting":
        if flange is None:
            if reference_director is not None:
                raise ValueError("a material fitting director needs a specific flange")
            ports = [current_pose_from_map(mapping, body, point, q, flange=f)["position_xyz_mm"] for f in ("beam", "post")]
            return {"position_xyz_mm": .5 * (ports[0] + ports[1]), "current_vector_xyz": None}
        i = row["flange_node_map"][flange]
        position = mechanical.rigid_port(point, centers[i], q[indices[i]])[0]
        director = (mechanical.so3_exp(q[indices[i, 3:]] / 1000.) @ reference_director
                    if reference_director is not None else None)
    else:
        stations, axis, start = np.asarray(row["reference_stations_mm"]), np.asarray(row["reference_axis_xyz"]), np.asarray(row["reference_start_xyz_mm"])
        s = float((point - start) @ axis)
        i = int(np.clip(np.searchsorted(stations, s) - 1, 0, len(stations) - 2))
        t = float(np.clip((s - stations[i]) / (stations[i+1] - stations[i]), 0., 1.))
        state = q[indices[i:i+2].ravel()]
        position = mechanical.interpolated_point(point, centers[i:i+2], state, t, basis)[0]
        director = (mechanical.interpolated_director(reference_director, state, t, basis)[0]
                    if reference_director is not None else None)
    return {"position_xyz_mm": position, "current_vector_xyz": director}


def complete_port_hessians(port, ndof):
    """Zeros are computational placeholders ONLY when no H is requested."""
    return {**port, "H_xyz_csr": port.get("H_xyz_csr") or [csr_matrix((ndof, ndof)) for _ in range(3)]}


class FiniteFramePotential:
    def __init__(self, mechanics, panels, panel_loads, interactions, nonpanel_loads, *, case=None,
                 source_sha256=None, shaft_replacement=None):
        self.mechanics, self.panels, self.panel_loads = mechanics, dict(panels), dict(panel_loads)
        self.ndof = mechanics.ndof
        if set(self.panels) != set(self.panel_loads) or any(p.ndof != self.ndof for p in panels.values()):
            raise ValueError("panel internal/load adapters and whole-state maps differ")
        self.interactions, self.nonpanel_loads = copy.deepcopy(interactions), copy.deepcopy(nonpanel_loads)
        self.case = {key: (case or {}).get(key) for key in ("state_id", "case_id", "accessory_placement")}
        self.shaft_replacement = shaft_replacement
        pins = dict(source_sha256 or {})
        for adapter in [mechanics, *panels.values(), *panel_loads.values()]:
            for path, digest in getattr(adapter, "source_sha256", {}).items():
                if path in pins and pins[path] != digest:
                    raise ValueError("prepared adapters carry contradictory source pins")
                pins[path] = digest
        if shaft_replacement is not None:
            path = str(Path(inspect.getfile(type(shaft_replacement))).resolve().relative_to(frame.ROOT))
            if path not in pins and path not in FROZEN_SOURCES:
                raise ValueError("replacement shaft producer needs an explicit immutable source pin")
        self.source_sha256 = source_pins(pins)
        self.map = kinematic_map(mechanics, self.panels)
        self.screw_by_id = {row["axis_id"]: row for panel in self.panels.values() for row in panel.panel.get("screws", [])}

    @classmethod
    def from_prepared(cls, assembly, common_system, case, integrated, groups, contacts, tangents, *,
                      source_sha256=None, shaft_replacement=None, derivative_step_mm=1e-3):
        mechanics = mechanical.FiniteMechanicsAdapter(assembly, common_system, derivative_step_mm=derivative_step_mm,
                                                       source_sha256=source_sha256)
        panels = panels_method.prepare_adapters(assembly.panels, assembly.panel_offsets, mechanics.ndof, source_sha256)
        panel_case = next(row for row in panels_method.method.load_cases(integrated)
                          if row["id"] == ("permanent" if case["case_id"] == "gravity-only" else case["case_id"]))
        accessory = "original_top" if case["primary_load_basis"] else "proportional"
        loads = {name: panel.prepare_case_load(panel_case, integrated, accessory, case["loads"]) for name, panel in panels.items()}
        interactions = describe_interactions(groups, contacts, tangents)
        counts = Counter(row["kind"] for row in interactions)
        if (counts["common_shaft_bearing"], counts["shaft_end_capture"], counts["panel_screw"],
                counts["flange_contact"], counts["floor_normal"], counts["floor_tangent_xy"]) != (308, 140, 66, 288, 32, 32):
            raise ValueError("candidate finite interaction census differs")
        normals = {row["id"]: row for row in interactions if row["kind"] == "floor_normal"}
        xy = [row for row in interactions if row["kind"] == "floor_tangent_xy"]
        if ({row["floor_support_id"] for row in xy} != set(normals) or any(
                row["normal_contact_id"] != row["floor_support_id"] or
                row["first"] != normals[row["floor_support_id"]]["first"] or
                row["reference_first_point_xyz_mm"] != normals[row["floor_support_id"]]["reference_first_point_xyz_mm"]
                for row in xy)):
            raise ValueError("candidate XY sticking must share every own normal corner and physical host")
        nonpanel = mechanical_load_ports(assembly, case, panels)
        if sum(row["id"].startswith("physical-bolt-metal/") for row in nonpanel) != 350:
            raise ValueError("complete own-shaft metal gravity required; no duplicate shaft selfweight")
        if shaft_replacement is None:
            shaft_replacement = isotropic.IsotropicShaftAdapter(mechanics, common_system, source_sha256=source_sha256)
        elif callable(shaft_replacement):
            shaft_replacement = shaft_replacement(mechanics, common_system)
        return cls(mechanics, panels, loads, interactions, nonpanel, case=case, source_sha256=source_sha256,
                   shaft_replacement=shaft_replacement)

    def port(self, body, point, q, flange=None, tangent=True, kind="point", axis_id=None):
        if body in self.panels:
            panel = self.panels[body]
            port = (panel.screw_port(q, self.screw_by_id[axis_id], tangent) if kind == "projected_ring"
                    else panel.point_port(q, point, tangent=tangent))
        else:
            port = self.mechanics.port(body, point, q, flange, tangent)
        return complete_port_hessians(port, self.ndof)

    def director(self, descriptor, q, first, second, tangent):
        owner = descriptor["director_owner"]
        if owner in self.panels:
            port = first if owner == descriptor["first"] else second
            return {"value_xyz": port["normal_xyz"], "J_csr": port["normal_J_csr"],
                    "H_xyz_csr": port["normal_H_xyz_csr"] or [csr_matrix((self.ndof, self.ndof)) for _ in range(3)]}
        point = descriptor["reference_first_point_xyz_mm"] if owner == descriptor["first"] else descriptor["reference_second_point_xyz_mm"]
        field = self.mechanics.director(owner, point, q, descriptor["reference_director_xyz"],
                                        descriptor.get("director_flange"), tangent)
        return {"value_xyz": field["current_vector_xyz"], "J_csr": field["J_csr"],
                "H_xyz_csr": field["H_xyz_csr"] or [csr_matrix((self.ndof, self.ndof)) for _ in range(3)]}

    def response(self, q, tangent=True, disabled_floor_hosts=(), recover_actions=False, *, disabled_floor_support_ids=()):
        source_pins(self.source_sha256)
        q = np.asarray(q, dtype=float)
        if q.shape != (self.ndof,) or not np.isfinite(q).all():
            raise ValueError("finite complete finite-frame state required")
        if recover_actions and any(value is None for value in self.case.values()):
            raise ValueError("current-action recovery needs explicit state/case/accessory identity")
        internal = (self.shaft_replacement.replacement_response(q, tangent) if self.shaft_replacement is not None
                    else self.mechanics.response(q, tangent))
        energy, gradient = float(internal["energy_nmm"]), np.array(internal["gradient_n"], copy=True)
        H = internal["hessian_csr"].copy() if tangent else None
        components = {"mechanical": energy, "panels": 0., "connections": 0., "nonpanel_loads": 0., "panel_loads": 0.}
        actions, load_rows, corrections = [], [], []
        floor_normal, floor_xy_enabled = {}, []
        for name, panel in self.panels.items():
            result = panel.response(q, tangent)
            energy += result["energy_nmm"]; components["panels"] += result["energy_nmm"]
            gradient += result["gradient_n"]
            if tangent:
                H += result["hessian_csr"]
            external = self.panel_loads[name].external(q, tangent, frame.REFERENCE)
            energy += external["energy_nmm"]; components["panel_loads"] += external["energy_nmm"]
            gradient += external["gradient_n"]
            if tangent:
                H += external["hessian_csr"]
            if recover_actions:
                loads, delta = self.panel_load_actions(name, q, external)
                load_rows.extend(loads); corrections.extend(delta)
        for descriptor in self.interactions:
            enabled = not (descriptor["kind"] == "floor_tangent_xy" and
                           (descriptor["first"] in disabled_floor_hosts or descriptor.get("floor_support_id") in disabled_floor_support_ids))
            if not enabled and not recover_actions:
                continue
            jet_tangent = tangent and enabled
            first = self.port(descriptor["first"], descriptor["reference_first_point_xyz_mm"], q,
                              descriptor.get("first_flange"), jet_tangent, descriptor["first_port_kind"],
                              descriptor["source_descriptor"].get("axis_id"))
            second = self.port(descriptor["second"], descriptor["reference_second_point_xyz_mm"], q,
                               descriptor.get("second_flange"), jet_tangent)
            director = self.director(descriptor, q, first, second, jet_tangent)
            parameters = {key: descriptor[key] for key in ("axial_stiffness_n_mm", "lateral_stiffness_n_mm", "radial_gap_mm",
                                                           "axial_tension_only", "axial_sign", "reference_axial_projection_mm")}
            if not enabled:
                parameters.update(axial_stiffness_n_mm=0., lateral_stiffness_n_mm=0.)
            result = connectors.connector_response(connectors.position_field(first), connectors.position_field(second), director,
                                                    **parameters)
            if descriptor["kind"] == "floor_normal":
                floor_normal[descriptor["id"]] = float(result["axial_scalar_force_n"])
            if descriptor["kind"] == "floor_tangent_xy" and enabled:
                floor_xy_enabled.append(descriptor.get("floor_support_id") or descriptor["first"])
            energy += result["energy_nmm"]; components["connections"] += result["energy_nmm"]
            gradient += result["gradient_n"]
            if tangent:
                H += result["hessian_csr"]
            if recover_actions:
                action = self.interaction_action(descriptor, first, second, director, result)
                action["interaction_enabled"] = enabled
                actions.append(action)
        for load in self.nonpanel_loads:
            port = self.port(load["body"], load["point_xyz_mm"], q, tangent=tangent)
            force = np.asarray(load["force_xyz_n"])
            potential = -float(force @ (port["position_xyz_mm"] - np.asarray(load["point_xyz_mm"])))
            energy += potential; components["nonpanel_loads"] += potential
            gradient -= np.asarray(port["J_csr"].T @ force).ravel()
            if tangent:
                for component, matrix in zip(force, port["H_xyz_csr"], strict=True):
                    H -= component * matrix
            if recover_actions:
                load_rows.append({**load, "reference_point_xyz_mm": load["point_xyz_mm"],
                    "current_point_xyz_mm": port["position_xyz_mm"].tolist(), "free_spatial_moment_xyz_nmm": [0., 0., 0.]})
        result = {"energy_nmm": float(energy), "gradient_n": gradient, "hessian_csr": H,
            "component_potential_energies_nmm": components, "source_sha256": self.source_sha256,
            "tangent_requested": bool(tangent), "zero_jet_h_placeholders_are_a_physical_tangent": False,
            "all_spatial_actions_use_current_points": True, "physical_or_numerical_shaft_twist_support_added": False,
            "shaft_elasticity_replaced_without_double_count": self.shaft_replacement is not None,
            "candidate_strength_or_release_established": False, "floor_normal_reactions_n": floor_normal,
            "floor_xy_enabled_support_ids": sorted(floor_xy_enabled),
            "disabled_floor_support_ids": sorted(disabled_floor_support_ids),
            "floor_contact_basis": floor_method.SUPPORT_BASIS,
            "floor_normal_activation_threshold_n": floor_method.NORMAL_ACTIVATION_THRESHOLD_N,
            "floor_no_slip_or_contact_stability_qualified": False}
        if recover_actions:
            for row in [*load_rows, *corrections]:
                row.update(self.case)
            result.update(finite_interaction_actions=actions, finite_body_applied_loads=load_rows,
                panel_generalized_load_corrections=corrections, finite_kinematic_map=self.map,
                reference_interaction_descriptors=self.interactions, identity=self.case,
                wrench_reference_xyz_mm=frame.REFERENCE.tolist(), release=frame.RELEASE)
        source_pins(self.source_sha256)
        return result

    def interaction_action(self, descriptor, first, second, director, result):
        couple = result["moment_on_director_owner_xyz_nmm"]
        first_m = couple if descriptor["director_owner"] == descriptor["first"] else np.zeros(3)
        second_m = couple if descriptor["director_owner"] == descriptor["second"] else np.zeros(3)
        return {**descriptor, **{key: self.case[key] for key in ("state_id", "case_id", "accessory_placement") if key in self.case},
            "point_on_first_xyz_mm": first["position_xyz_mm"].tolist(), "point_on_second_xyz_mm": second["position_xyz_mm"].tolist(),
            "current_director_xyz": np.asarray(director["value_xyz"]).tolist(),
            "force_on_first_xyz_n": result["force_on_first_xyz_n"].tolist(),
            "force_on_second_xyz_n": result["force_on_second_xyz_n"].tolist(),
            "moment_on_first_at_current_point_xyz_nmm": first_m.tolist(),
            "moment_on_second_at_current_point_xyz_nmm": second_m.tolist(),
            "moment_on_director_owner_xyz_nmm": couple.tolist(),
            "pair_spatial_moment_residual_nmm": result["pair_spatial_moment_residual_nmm"].tolist(),
            "signed_axial_extension_mm": result["signed_axial_extension_mm"], "radial_distance_mm": result["radial_distance_mm"],
            "axial_scalar_force_n": result["axial_scalar_force_n"], "energy_nmm": result["energy_nmm"],
            "director_couple_is_a_washer_prying_or_strength_capacity": False}

    def panel_load_actions(self, name, q, external):
        panel, loads = self.panels[name], self.panel_loads[name]
        local = panel.local_q(q)
        xy = panel.measure["mass_weights"] @ panel.measure["xy_mm"]
        mass_reference = panel.origin + panel.axes @ np.r_[xy, 0.]
        mass_current = mass_reference + panel.axes @ (local.reshape(3, panel.basis.size) @ panel.measure["mass_row"])
        rows = []
        point_ids = {r["id"] for r in loads.point_loads}
        for row in loads.loads:
            if row["id"] in point_ids:
                port = panel.point_port(q, row["point_xyz_mm"], tangent=False, allow_edge_extension=row["id"].startswith("accessory/"))
                reference, current, model = port["reference_position_xyz_mm"], port["position_xyz_mm"], "exact physical source-world point port"
            else:
                reference, current, model = mass_reference, mass_current, "uniform reference-mass-measure resultant; not a local point traction"
            rows.append({**row, "source_reference_point_xyz_mm": row["point_xyz_mm"], "reference_point_xyz_mm": reference.tolist(),
                "current_point_xyz_mm": current.tolist(), "free_spatial_moment_xyz_nmm": [0., 0., 0.], "finite_load_model": model})
        corrections = []
        for kind, force, key in (("retained_rigid_RHS", loads.retained_rigid_correction_n, "retained_rigid_correction_wrench_n_nmm"),
                                  ("reference_port_alignment", loads.reference_port_alignment_correction_n, "reference_port_alignment_wrench_n_nmm")):
            corrections.append({"id": name + "/" + kind, "panel": name, "kind": kind,
                "global_coefficient_indices": panel.indices.tolist(), "local_generalized_force_n": force.tolist(),
                "current_equivalent_rigid_wrench_n_nmm": external[key].tolist(), "wrench_reference_xyz_mm": frame.REFERENCE.tolist(),
                "physical_point_forces_or_pressure_representation": False})
        return rows, corrections
