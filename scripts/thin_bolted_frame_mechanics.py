"""Fresh thin-frame loads, equilibrium witnesses and conditional elastic response.

Rigid statics witnesses and compatible beam/plate/spring scenarios remain
separate. Neither supplies a conservative physical demand bound. Physical shaft
torque is not inferred from point springs. The primary accessory placement
retains the original response-model convention; proportional panel placement
is a named sensitivity.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
from collections import defaultdict
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import scipy
from scipy.linalg import svdvals
from scipy.optimize import linprog
from scipy.sparse import coo_matrix, csr_matrix, hstack, vstack
from scipy.sparse.linalg import spsolve
from scipy.spatial import ConvexHull

ROOT = Path(__file__).resolve().parents[1]
LOADED_PRODUCER_SHA256 = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
PACKET = ROOT / "docs/wood-joints-mvp/hypotheses/hl35-candidate/thin-frame-comparison"
LAYOUT = PACKET / "mixed-offset-rows-shallow-wires-v4.json"
LAYOUT_SHA = "8174841bf64914570397ee6d960c5602f74097e2e412e5910502811bc5b9405c"
EVIDENCE = PACKET / "integrated-model-v4.json"
EVIDENCE_SHA = "28bbd2d2fb6f1a93acb441af124c453f04f81e03be551906c633d5acad1d407e"
OUTPUT = PACKET / "fresh-frame-mechanics-v4.json"
GEOMETRY_CACHE = PACKET / "native-geometry-v4.json"
GEOMETRY_CACHE_SHA = "cafdd983a41f2eee15647b28e60e5b2704354a4c5518d120e4c4342001994bb9"
TAKEOFF = PACKET / "access-takeoff-v4.json"
TAKEOFF_SHA = "0c5a09879c9b191c39b96ce670d71ad110661bff7dfeab68133f711b32de476c"
GRAVITY = 9.80665
ROTATION_SCALE = 1000.0
GENERALIZED_RESIDUAL_TOLERANCE_N = 1e-5
BODY_FORCE_TOLERANCE_N = 1e-4
BODY_MOMENT_TOLERANCE_NMM = .1
REFERENCE = np.array([0.0, 750.0, 1100.0])
CASE_INPUTS = (
    ("a12-rear", "A12", (0.0, 300.0)),
    ("a12-forward", "A12", (0.0, -300.0)),
    ("a12-left", "A12", (-300.0, 0.0)),
    ("k12-right", "K12", (300.0, 0.0)),
    ("k12-rear", "K12", (0.0, 300.0)),
    ("a1-rear", "A1", (0.0, 300.0)),
)
RELEASE = {key: False for key in (
    "candidate_accepted", "complete_joint_acceptance", "capacity_established",
    "fabrication_released", "structural_released", "climbing_released")}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def inputs() -> tuple[dict, dict, dict]:
    contract = json.loads((ROOT / "thin-bolted-candidate.json").read_text())
    pins = {str(LAYOUT.relative_to(ROOT)): LAYOUT_SHA,
            str(EVIDENCE.relative_to(ROOT)): EVIDENCE_SHA,
            **contract["preserved_authorities_sha256"]}
    if TAKEOFF.exists():
        pins[str(TAKEOFF.relative_to(ROOT))] = TAKEOFF_SHA
    if contract["candidate"] != "compact-floor-flush-thin-bolted-development":
        raise ValueError("unexpected candidate authority")
    if any(contract["release"].values()):
        raise ValueError("development authority carries a release")
    for path, expected in pins.items():
        if sha(ROOT / path) != expected:
            raise ValueError(f"frozen input differs: {path}")
    layout, evidence = [json.loads(p.read_text()) for p in (LAYOUT, EVIDENCE)]
    for source in (layout, evidence):
        for path, expected in source["source_sha256"].items():
            if sha(ROOT / path) != expected:
                raise ValueError(f"frozen geometry dependency differs: {path}")
            pins[path] = expected
    if len(layout["installed_axes"]) != 70 or len(layout["screw_axes"]) != 66:
        raise ValueError("physical fastener census differs")
    return layout, evidence, pins


def cross_matrix(vector: np.ndarray) -> np.ndarray:
    x, y, z = vector
    return np.array([[0.0, -z, y], [z, 0.0, -x], [-y, x, 0.0]])


def beam_stiffness(length: float, area: float, inertia_y: float, inertia_z: float,
                   torsion_j: float, elastic_modulus: float, shear_modulus: float,
                   shear_factor: float = 5. / 6.) -> np.ndarray:
    """Local two-node 3D Timoshenko elastic energy, ordinary unscaled rotations.

    Local order=(u,v,w,theta_x,theta_y,theta_z) per node. Uniform rectangular
    section/constant moduli are explicit surrogates. Axial/bending/shear/torsion
    units are N/mm/Nmm. No joint spring or resistance is inferred.
    """
    if min(length, area, inertia_y, inertia_z, torsion_j, elastic_modulus, shear_modulus, shear_factor) <= 0:
        raise ValueError("positive finite beam properties required")
    if not np.isfinite([length, area, inertia_y, inertia_z, torsion_j, elastic_modulus, shear_modulus, shear_factor]).all():
        raise ValueError("finite beam properties required")
    k = np.zeros((12, 12))
    for indices, stiffness in (((0, 6), elastic_modulus * area / length),
                               ((3, 9), shear_modulus * torsion_j / length)):
        k[np.ix_(indices, indices)] += stiffness * np.array([[1., -1.], [-1., 1.]])
    for inertia, indices, signs in ((inertia_z, (1, 5, 7, 11), (1., 1., 1., 1.)),
                                    (inertia_y, (2, 4, 8, 10), (1., -1., 1., -1.))):
        phi = 12. * elastic_modulus * inertia / (shear_factor * shear_modulus * area * length ** 2)
        base = np.array([[12., 6. * length, -12., 6. * length],
                         [6. * length, (4. + phi) * length ** 2, -6. * length, (2. - phi) * length ** 2],
                         [-12., -6. * length, 12., -6. * length],
                         [6. * length, (2. - phi) * length ** 2, -6. * length, (4. + phi) * length ** 2]])
        sign = np.asarray(signs)
        base *= sign[:, None] * sign[None, :]
        k[np.ix_(indices, indices)] += elastic_modulus * inertia / length ** 3 / (1. + phi) * base
    return k


def rectangular_torsion(width: float, depth: float) -> float:
    a, b = max(width, depth), min(width, depth)
    return a * b ** 3 * (1. / 3. - .21 * b / a * (1. - b ** 4 / (12. * a ** 4)))


class ElasticAssembly:
    """Independent timber beams, finite fitting strips and flexible Ritz panels.

    Point ports interpolate translations/rotations linearly between beam nodes
    and retain exact eccentric rigid arms. This interpolation is work-conjugate
    and exactly reproduces rigid motion; refinement tests its flexible response.
    Gross timber and the fitting strip models remain explicit surrogates.
    """

    def __init__(self, layout: dict, geo: dict, panels: dict, beam_size: float = 150.,
                 timber_e: float = 11031.612, shear_ratio: float = .064,
                 fitting_section: str = "gross"):
        from scripts.thin_bolted_steel_resistance import fitting_condensed_stiffness

        self.panels, self.geo, self.layout = panels, geo, layout
        self.members, self.fittings, self.panel_offsets = {}, {}, {}
        self.ndof = 0
        blocks = []
        for member in geo["members"]:
            start, end = np.array(member["start"]), np.array(member["end"])
            length = float(np.linalg.norm(end - start))
            count = max(1, int(np.ceil(length / beam_size)))
            stations = np.linspace(0., length, count + 1)
            index = np.arange(self.ndof, self.ndof + 6 * (count + 1)).reshape(-1, 6)
            self.ndof += index.size
            g, u, v = [np.array(member[k]) for k in ("axis", "section_u", "section_v")]
            rotation = np.array([g, u, v])
            width, depth = member["width_mm"], member["depth_mm"]
            A, Iy, Iz = width * depth, width * depth ** 3 / 12., depth * width ** 3 / 12.
            T = scipy.linalg.block_diag(rotation, rotation / ROTATION_SCALE, rotation, rotation / ROTATION_SCALE)
            elements = []
            for segment in range(count):
                dofs = np.r_[index[segment], index[segment + 1]]
                local = beam_stiffness(stations[segment + 1] - stations[segment], A, Iy, Iz,
                                       rectangular_torsion(width, depth), timber_e, timber_e * shear_ratio)
                stiffness = T.T @ local @ T
                blocks.append((dofs, stiffness))
                elements.append({"dofs": dofs, "K": stiffness, "T": T, "local_K": local,
                                 "start": start + g * stations[segment], "end": start + g * stations[segment + 1]})
            self.members[member["name"]] = {"index": index, "stations": stations, "start": start,
                                             "axis": g, "elements": elements, "source": member}
        for fitting in layout["raw_fittings"]:
            index = np.arange(self.ndof, self.ndof + 12).reshape(2, 6)
            self.ndof += 12
            result = fitting_condensed_stiffness(fitting, beam_stiffness, rectangular_torsion,
                                                 section_scenario=fitting_section)
            stiffness = np.asarray(result["global_port_stiffness_n_mm_rad"])
            scale = np.tile([1., 1., 1., 1. / ROTATION_SCALE, 1. / ROTATION_SCALE, 1. / ROTATION_SCALE], 2)
            blocks.append((index.ravel(), stiffness * scale[:, None] * scale[None, :]))
            self.fittings[fitting["angle_id"]] = {"index": index,
                "points": {r["flange"]: np.array(r["entry_xyz_mm"]) for r in fitting["holes"]}, "source": result}
        for name, panel in panels.items():
            index = np.arange(self.ndof, self.ndof + len(panel["K"]))
            self.ndof += len(index)
            self.panel_offsets[name] = index
            blocks.append((index, panel["K"]))
        rows, cols, values = [], [], []
        for index, block in blocks:
            i, j = np.nonzero(abs(block) > 1e-12)
            rows.extend(index[i]); cols.extend(index[j]); values.extend(block[i, j])
        self.K = coo_matrix((values, (rows, cols)), shape=(self.ndof, self.ndof)).tocsr()

    def embed(self, block: np.ndarray, index: np.ndarray) -> csr_matrix:
        block = np.asarray(block).reshape(-1, len(index))
        row, col = np.nonzero(abs(block) > 1e-14)
        return csr_matrix((block[row, col], (row, index[col])), shape=(len(block), self.ndof))

    def port(self, body: str, point, flange: str | None = None) -> csr_matrix:
        from scripts.thin_bolted_panel_mechanics import (
            point_matrix as panel_point_matrix,
        )

        point = np.asarray(point)
        if body == "floor":
            return csr_matrix((3, self.ndof))
        if body in self.members:
            member = self.members[body]
            s = float((point - member["start"]) @ member["axis"])
            segment = int(np.clip(np.searchsorted(member["stations"], s) - 1, 0, len(member["stations"]) - 2))
            a, b = member["stations"][segment:segment + 2]
            t = np.clip((s - a) / (b - a), 0., 1.)
            center = member["start"] + member["axis"] * (a + t * (b - a))
            block = point_matrix(point, center)
            return self.embed(np.hstack(((1. - t) * block, t * block)),
                              np.r_[member["index"][segment], member["index"][segment + 1]])
        if body in self.fittings:
            fitting = self.fittings[body]
            if flange is None:
                return .5 * (self.port(body, point, "beam") + self.port(body, point, "post"))
            i = 0 if flange == "beam" else 1
            return self.embed(point_matrix(point, fitting["points"][flange]), fitting["index"][i])
        if body in self.panels:
            return self.embed(panel_point_matrix(self.panels[body], point), self.panel_offsets[body])
        raise ValueError(f"elastic port body is missing: {body}")

    def scalar_port(self, body, point, direction, flange=None) -> csr_matrix:
        return csr_matrix(np.asarray(direction).reshape(1, 3)) @ self.port(body, point, flange)

    def panel_rigid_modes(self, name: str) -> np.ndarray:
        panel = self.panels[name]
        basis, geometry = panel["basis"], panel["geometry"]
        greville = np.array([np.mean(basis.knots[i + 1:i + 4]) for i in range(basis.order)])
        x, y = np.meshgrid(greville * basis.width, greville * basis.height, indexing="ij")
        positions = geometry["origin"] + np.c_[x.ravel(), y.ravel()] @ geometry["axes"][:, :2].T
        fields = []
        for component in range(6):
            displacement = np.broadcast_to(np.eye(3)[component], positions.shape) if component < 3 else np.cross(
                np.eye(3)[component - 3], positions - REFERENCE)
            fields.append((displacement @ geometry["axes"]).T.ravel())
        return np.array(fields).T

    def rigid_modes(self) -> np.ndarray:
        result = np.zeros((self.ndof, 6))
        for member in self.members.values():
            for index, station in zip(member["index"], member["stations"], strict=True):
                point = member["start"] + station * member["axis"]
                result[index[:3]] = np.hstack((np.eye(3), -cross_matrix(point - REFERENCE)))
                result[index[3:], 3:] = np.eye(3) * ROTATION_SCALE
        for fitting in self.fittings.values():
            for flange, i in (("beam", 0), ("post", 1)):
                index, point = fitting["index"][i], fitting["points"][flange]
                result[index[:3]] = np.hstack((np.eye(3), -cross_matrix(point - REFERENCE)))
                result[index[3:], 3:] = np.eye(3) * ROTATION_SCALE
        for name, index in self.panel_offsets.items():
            result[index] = self.panel_rigid_modes(name)
        return result


def coupled_load_vector(assembly: ElasticAssembly, case: dict, integrated: dict) -> np.ndarray:
    from scripts.thin_bolted_panel_mechanics import load_cases as panel_cases
    from scripts.thin_bolted_panel_mechanics import panel_case_load

    panel_case = next(c for c in panel_cases(integrated) if c["id"] == ("permanent" if case["case_id"] == "gravity-only" else case["case_id"]))
    result = np.zeros(assembly.ndof)
    for name, panel in assembly.panels.items():
        accessory = "original_top" if case["primary_load_basis"] else "proportional"
        force, _ = panel_case_load(panel, panel_case, integrated, accessory)
        loads = [r for r in case["loads"] if r["body"] == name]
        for load in loads:
            if load["id"].startswith("bolt-weight/"):
                force += np.asarray(assembly.port(name, load["point_xyz_mm"]).T @ load["force_xyz_n"])[assembly.panel_offsets[name]]
        # Preserve the exact source-body/hold/accessory wrench in the discrete
        # plate quadrature. This tiny rigid-motion correction is explicit and
        # does not assert an observed panel gravity distribution.
        desired = sum((wrench(r["force_xyz_n"], r["point_xyz_mm"], REFERENCE) for r in loads), np.zeros(6))
        rigid = assembly.panel_rigid_modes(name)
        correction = desired - rigid.T @ force
        force += rigid @ np.linalg.solve(rigid.T @ rigid, correction)
        result[assembly.panel_offsets[name]] += force
    for load in case["loads"]:
        if load["body"] in assembly.panels:
            continue
        if load["id"].startswith("self-weight/") and load["body"] in assembly.members:
            member = assembly.members[load["body"]]
            low, high = member["stations"][[0, -1]]
            center = np.asarray(load["point_xyz_mm"])
            center_s = float((center - member["start"]) @ member["axis"])
            off = center - member["axis"] * center_s
            beta = 12. * (center_s - .5 * (low + high)) / (high - low) ** 2
            for a, b in zip(member["stations"][:-1], member["stations"][1:], strict=True):
                for abscissa in (-1. / np.sqrt(3.), 1. / np.sqrt(3.)):
                    s = .5 * (a + b) + .5 * (b - a) * abscissa
                    fraction = .5 * (b - a) / (high - low) * (1. + beta * (s - .5 * (low + high)))
                    point = off + member["axis"] * s
                    result += assembly.port(load["body"], point).T @ (np.asarray(load["force_xyz_n"]) * fraction)
        else:
            result += assembly.port(load["body"], load["point_xyz_mm"]).T @ load["force_xyz_n"]
    return result


def connector_basis(axis) -> np.ndarray:
    axis = np.asarray(axis, dtype=float); axis /= np.linalg.norm(axis)
    seed = np.eye(3)[int(np.argmin(abs(axis)))]
    tangent = np.cross(axis, seed); tangent /= np.linalg.norm(tangent)
    return np.array([axis, tangent, np.cross(axis, tangent)])


def spring_constitutive(displacement, axial_stiffness: float, lateral_stiffness: float,
                        radial_gap: float, tension_only: bool) -> tuple[np.ndarray, np.ndarray, float]:
    """Exact force, tangent and energy of the declared local spring law."""
    d = np.asarray(displacement, dtype=float)
    force, tangent = np.zeros(3), np.zeros((3, 3))
    axial = max(d[0], 0.) if tension_only else d[0]
    force[0] = axial_stiffness * axial
    tangent[0, 0] = axial_stiffness if not tension_only or d[0] > 0 else 0.
    energy = .5 * axial_stiffness * axial ** 2
    radius = float(np.linalg.norm(d[1:]))
    if radius > radial_gap:
        force[1:] = lateral_stiffness * (1. - radial_gap / radius) * d[1:]
        tangent[1:, 1:] = lateral_stiffness * ((1. - radial_gap / radius) * np.eye(2) +
                                              radial_gap / radius ** 3 * np.outer(d[1:], d[1:]))
        energy += .5 * lateral_stiffness * (radius - radial_gap) ** 2
    elif radial_gap == 0.:
        tangent[1:, 1:] = np.eye(2) * lateral_stiffness
    return force, tangent, float(energy)


def elastic_connections(assembly: ElasticAssembly, stiffness: float, clearance: float,
                        screw_stiffness: float | None = None,
                        foundation: float = 2., floor_tangent_stiffness: float = 100000.) -> tuple[list, list, list]:
    groups, contacts, tangents = [], [], []
    screw_stiffness = stiffness if screw_stiffness is None else screw_stiffness
    layout = assembly.layout
    for axis in layout["installed_axes"]:
        if axis["attachments"]:
            for attachment in axis["attachments"]:
                point = attachment["entry_xyz_mm"]
                basis = connector_basis(attachment["axis_xyz"])
                B = csr_matrix(basis) @ (assembly.port(attachment["receiver"], point) -
                                           assembly.port(attachment["angle_id"], point, attachment["flange"]))
                groups.append({"id": axis["id"] + "/" + attachment["angle_id"], "axis_id": axis["id"],
                               "kind": "fitting_bolt", "first": attachment["receiver"], "second": attachment["angle_id"],
                               "angle_id": attachment["angle_id"], "flange": attachment["flange"],
                               "point_xyz_mm": point, "basis": basis, "B": B,
                               "ka": stiffness, "kl": stiffness, "clearance": clearance,
                               "tension_only": True})
        else:
            first, second = axis["receivers"]
            # Interface point reconstructed by the statics datum helper.
            point = next(e["point_xyz_mm"] for e in action_edges(layout, assembly.geo) if e["id"] == axis["id"])
            basis = connector_basis(axis["direction"])
            B = csr_matrix(basis) @ (assembly.port(first, point) - assembly.port(second, point))
            groups.append({"id": axis["id"], "axis_id": axis["id"], "kind": "retained_bolt", "first": first,
                           "second": second, "point_xyz_mm": point, "basis": basis, "B": B,
                           "ka": stiffness, "kl": stiffness, "clearance": clearance,
                           "tension_only": False})
    for edge in action_edges(layout, assembly.geo):
        if edge["kind"] != "flange_contact":
            continue
        normal = np.asarray(edge["direction_xyz"])
        row = -(assembly.scalar_port(edge["first"], edge["point_xyz_mm"], normal, edge["flange"]) -
                assembly.scalar_port(edge["second"], edge["point_xyz_mm"], normal))
        contacts.append({**edge, "B": row, "stiffness": 10000.})
    for name, panel in assembly.panels.items():
        geometry = panel["geometry"]
        outward = geometry["axes"][:, 2]
        basis = geometry["axes"].T[[2, 0, 1]]
        for i, screw in enumerate(panel["screws"]):
            # The plate lateral rows are midplane values. Map the receiver
            # to the same physical point so a common rigid rotation produces
            # zero relative slip rather than an artificial thickness couple.
            point = (np.asarray(screw["origin_xyz_mm"]) + geometry["inward"] * panel["thickness"] / 2.).tolist()
            panel_rows = np.array([panel["screw_w"][i], panel["screw_u"][i], panel["screw_v"][i]])
            B = assembly.embed(panel_rows, assembly.panel_offsets[name]) - csr_matrix(basis) @ assembly.port(screw["receiver"], point)
            groups.append({"id": screw["axis_id"], "axis_id": screw["axis_id"], "kind": "panel_screw",
                           "first": name, "second": screw["receiver"], "point_xyz_mm": point,
                           "basis": basis, "B": B, "ka": screw_stiffness, "kl": screw_stiffness,
                           "clearance": 0., "tension_only": True})
        for i, (xy, area, owner) in enumerate(zip(panel["contact_xy"], panel["contact_area"], panel["contact_owner"], strict=True)):
            point = geometry["origin"] + geometry["axes"][:, :2] @ xy - panel["thickness"] / 2. * outward
            row = -(assembly.scalar_port(name, point, outward) - assembly.scalar_port(owner, point, outward))
            contacts.append({"id": name + f"/compression-{i}", "kind": "panel_contact", "first": name, "second": owner,
                             "point_xyz_mm": point.tolist(), "direction_xyz": outward.tolist(),
                             "B": row, "stiffness": foundation * area})
    for name, corners in assembly.geo["floor_footprints"].items():
        for i, point in enumerate(corners):
            contacts.append({"id": name + f"/floor-{i}", "kind": "floor_normal", "first": name, "second": "floor",
                             "point_xyz_mm": point, "direction_xyz": [0., 0., 1.],
                             "B": -assembly.scalar_port(name, point, [0., 0., 1.]), "stiffness": 25000.})
        point = np.mean(corners, axis=0)
        for component in (0, 1):
            tangents.append({"id": name + f"/no-slip-{component}", "kind": "floor_tangent", "first": name,
                             "point_xyz_mm": point.tolist(), "direction_xyz": np.eye(3)[component].tolist(),
                             "B": assembly.scalar_port(name, point, np.eye(3)[component]), "stiffness": floor_tangent_stiffness})
    return groups, contacts, tangents


def compatible_contact_solve(K: csr_matrix, applied: np.ndarray, groups: list, contacts: list,
                             tangents: list, max_iterations: int = 100) -> dict:
    """Convex radial-clearance spring/tension/contact Newton solve.

    A fixed floor-bearing pattern gives a conservative elastic potential.
    Outer updates remove no-slip tangents from nonbearing footprints; a repeated
    pattern is a numerical stop, never a stability or acceptance result.
    """
    C = vstack([c["B"] for c in contacts], format="csr")
    ck = np.array([c["stiffness"] for c in contacts])
    patterns, disabled = [], set()
    q = None
    preconditioner = None
    for floor_iteration in range(10):
        tangent_rows = [t for t in tangents if t["first"] not in disabled]
        linear = K.copy()
        for t in tangent_rows:
            linear += t["stiffness"] * (t["B"].T @ t["B"])

        def fields(state, need_tangent=False, current_linear=linear):
            gradient = current_linear @ state - applied
            energy = .5 * state @ (current_linear @ state) - applied @ state
            H = current_linear.copy() if need_tangent else None
            forces = []
            for group in groups:
                B = group["B"]
                d = np.asarray(B @ state).ravel()
                force, jacobian, spring_energy = spring_constitutive(d, group["ka"], group["kl"],
                                                                    group["clearance"], group["tension_only"])
                energy += spring_energy
                gradient += B.T @ force
                if need_tangent:
                    H += B.T @ csr_matrix(jacobian) @ B
                forces.append(force)
            displacement = np.asarray(C @ state).ravel()
            normal = ck * np.maximum(displacement, 0.)
            gradient += C.T @ normal
            energy += .5 * np.dot(ck, np.maximum(displacement, 0.) ** 2)
            if need_tangent:
                active = displacement > 0.
                H += C[active].T @ scipy.sparse.diags(ck[active]) @ C[active]
            return gradient, float(energy), H, forces, normal, displacement

        if q is None:
            initial = linear + C.T @ scipy.sparse.diags(ck) @ C
            for group in groups:
                initial += group["B"].T @ scipy.sparse.diags([group["ka"], group["kl"], group["kl"]]) @ group["B"]
            q = spsolve(initial.tocsc(), applied)
            # Start just beyond each directed radial gap using the bilateral
            # load direction. This is only initialization: the returned field
            # is still checked against the unmodified circular-gap law.
            initial_force = applied.copy()
            for group in groups:
                displacement = np.asarray(group["B"] @ q).ravel()
                radius = float(np.linalg.norm(displacement[1:]))
                if group["clearance"] > 0. and radius > 1e-14:
                    offset = np.r_[0., group["kl"] * group["clearance"] * displacement[1:] / radius]
                    initial_force += group["B"].T @ offset
            q = spsolve(initial.tocsc(), initial_force)
            preconditioner = scipy.sparse.diags(1. / np.sqrt(np.maximum(abs(initial.diagonal()), 1e-12)))
        converged = False
        descent_fallbacks = 0
        maximum_step_regularization = 0.
        for iteration in range(max_iterations):
            gradient, energy, H, forces, normal, displacement = fields(q, True)
            residual = float(abs(gradient).max())
            if residual < GENERALIZED_RESIDUAL_TOLERANCE_N:
                converged = True
                break
            scaled_H = (preconditioner @ H @ preconditioner).tocsc()
            identity = scipy.sparse.eye(K.shape[0], format="csc")
            accepted = False
            for regularization in (0., 1e-10, 1e-8, 1e-6, 1e-4, 1e-2):
                scaled_step = spsolve(scaled_H + regularization * identity, -preconditioner @ gradient)
                step = np.asarray(preconditioner @ scaled_step).ravel()
                if not np.isfinite(step).all():
                    continue
                # Trust-step size only limits numerical continuation. It is
                # neither a displacement acceptance limit nor a new spring.
                largest = float(abs(step).max())
                if largest > 100.:
                    step *= 100. / largest
                slope = float(gradient @ step)
                if slope >= 0.:
                    continue
                alpha = 1.
                for _ in range(35):
                    candidate = q + alpha * step
                    if fields(candidate)[1] <= energy + 1e-4 * alpha * slope + 1e-8:
                        q = candidate
                        accepted = True
                        maximum_step_regularization = max(maximum_step_regularization, regularization)
                        descent_fallbacks += int(regularization > 0.)
                        break
                    alpha *= .5
                if accepted:
                    break
            if not accepted:
                return {"converged": False, "termination": "energy line search", "gradient_inf_n": residual}
        if not converged:
            return {"converged": False, "termination": "Newton iteration limit", "gradient_inf_n": residual}
        floor_normal = defaultdict(float)
        for c, force in zip(contacts, normal, strict=True):
            if c["kind"] == "floor_normal":
                floor_normal[c["first"]] += force
        next_disabled = {name for name, force in floor_normal.items() if force <= 1e-7}
        if next_disabled == disabled:
            break
        pattern = tuple(sorted(next_disabled))
        if pattern in patterns:
            return {"converged": False, "termination": "repeated floor-bearing pattern", "gradient_inf_n": residual}
        patterns.append(pattern); disabled = next_disabled
    else:
        return {"converged": False, "termination": "floor-bearing iteration limit"}
    return {"converged": True, "q": q, "connector_local_force_n": forces,
            "normal_contact_force_n": normal, "normal_contact_displacement_mm": displacement,
            "gradient_inf_n": residual, "potential_energy_nmm": energy,
            "generalized_residual_tolerance_n": GENERALIZED_RESIDUAL_TOLERANCE_N,
            "newton_iterations": iteration + 1, "floor_pattern_iterations": floor_iteration + 1,
            "descent_fallbacks_in_final_floor_pattern": descent_fallbacks,
            "maximum_transient_scaled_step_regularization": maximum_step_regularization,
            "physical_residual_uses_unmodified_laws": True,
            "nonbearing_no_slip_removed": sorted(disabled), "active_contacts": int(np.count_nonzero(normal > 0.)),
            "termination": "constitutive equilibrium and floor-bearing pattern converged"}


def elastic_method_coupons() -> dict:
    L, width, depth, E, G = 1000., 38.1, 139.7, 11031.612, .064 * 11031.612
    A, Iy, Iz = width * depth, width * depth ** 3 / 12., depth * width ** 3 / 12.
    J = rectangular_torsion(width, depth)
    K = beam_stiffness(L, A, Iy, Iz, J, E, G)
    rows = []
    for dof, expected in ((0, L / (E * A)), (1, L ** 3 / (3. * E * Iz) + L / ((5. / 6.) * G * A)),
                          (2, L ** 3 / (3. * E * Iy) + L / ((5. / 6.) * G * A)), (3, L / (G * J))):
        f = np.eye(6)[dof]
        q = np.linalg.solve(K[6:, 6:], f)
        error = abs(q[dof] - expected)
        if error > 1e-12 * max(1., abs(expected)):
            raise AssertionError("Timoshenko cantilever known answer differs")
        rows.append({"tip_dof": dof, "observed": float(q[dof]), "known_answer": float(expected), "absolute_error": float(error)})
    # The radial gap law responds2N to0.3mm slip with10N/mm and0.1mm gap.
    radius, gap, stiffness = .3, .1, 10.
    force = stiffness * (radius - gap)
    energy = .5 * stiffness * (radius - gap) ** 2
    work = force * radius
    if abs(work - (2. * energy + gap * force)) > 1e-14:
        raise AssertionError("clearance work identity differs")
    return {"cantilever_axial_two_bending_torsion": rows,
            "radial_gap_force_n": force, "radial_gap_elastic_energy_nmm": energy,
            "radial_gap_work_identity_error_nmm": abs(work - (2. * energy + gap * force)),
            "native_solver_used": False}


def elastic_actions(assembly: ElasticAssembly, case: dict, response: dict,
                    groups: list, contacts: list, tangents: list) -> dict:
    q = response["q"]
    attachments, retained, screws, contact_rows, floor_rows = [], [], [], [], []
    for group, local in zip(groups, response["connector_local_force_n"], strict=True):
        force = -group["basis"].T @ local
        common = {"case_id": case["case_id"], "accessory_placement": case["accessory_placement"],
                  "axis_id": group["axis_id"], "point_xyz_mm": group["point_xyz_mm"],
                  "first": group["first"], "second": group["second"],
                  "force_on_first_xyz_n": force.tolist(), "local_force_n": np.asarray(local).tolist(),
                  "moment_at_point_model_xyz_nmm": [0., 0., 0.],
                  "physical_bolt_end_prying_moment_resolved": False,
                  "physical_stiffness_bounded": False}
        if group["kind"] == "fitting_bolt":
            attachments.append({**common, "angle_id": group["angle_id"], "flange": group["flange"],
                                "receiver": group["first"], "force_on_receiver_xyz_n": force.tolist(),
                                "moment_on_receiver_at_point_xyz_nmm": [0., 0., 0.]})
        elif group["kind"] == "panel_screw":
            screws.append({**common, "panel": group["first"], "receiver": group["second"],
                           "force_on_receiver_xyz_n": (-force).tolist(),
                           "withdrawal_n": float(local[0]), "lateral_n": float(np.linalg.norm(local[1:]))})
        else:
            retained.append(common)
    for contact, force in zip(contacts, response["normal_contact_force_n"], strict=True):
        vector = force * np.asarray(contact["direction_xyz"])
        row = {"case_id": case["case_id"], "accessory_placement": case["accessory_placement"],
               "id": contact["id"], "kind": contact["kind"], "first": contact["first"], "second": contact["second"],
               "point_xyz_mm": contact["point_xyz_mm"], "force_on_first_xyz_n": vector.tolist(),
               "compression_n": float(force), "moment_at_point_model_xyz_nmm": [0., 0., 0.]}
        if contact["kind"] == "flange_contact":
            row.update(angle_id=contact["angle_id"], flange=contact["flange"], receiver=contact["second"],
                       force_on_receiver_xyz_n=(-vector).tolist(), moment_on_receiver_at_point_xyz_nmm=[0., 0., 0.])
            contact_rows.append(row)
        elif contact["kind"] == "floor_normal":
            floor_rows.append(row)
        else:
            contact_rows.append(row)
    for tangent in tangents:
        if tangent["first"] in response["nonbearing_no_slip_removed"]:
            continue
        scalar = -tangent["stiffness"] * float((tangent["B"] @ q)[0])
        vector = scalar * np.asarray(tangent["direction_xyz"])
        floor_rows.append({"id": tangent["id"], "kind": "floor_tangent", "first": tangent["first"],
                           "second": "floor", "case_id": case["case_id"], "accessory_placement": case["accessory_placement"],
                           "point_xyz_mm": tangent["point_xyz_mm"], "force_on_first_xyz_n": vector.tolist(),
                           "tangent_displacement_mm": float((tangent["B"] @ q)[0]),
                           "penalty_stiffness_n_mm": tangent["stiffness"]})
    body_balance = {r["id"]: np.zeros(6) for r in assembly.geo["bodies"]}
    for load in case["loads"]:
        body_balance[load["body"]] += wrench(load["force_xyz_n"], load["point_xyz_mm"], REFERENCE)
    for action in [*attachments, *retained, *screws, *contact_rows]:
        value = wrench(action["force_on_first_xyz_n"], action["point_xyz_mm"], REFERENCE)
        body_balance[action["first"]] += value
        body_balance[action["second"]] -= value
    for action in floor_rows:
        body_balance[action["first"]] += wrench(action["force_on_first_xyz_n"], action["point_xyz_mm"], REFERENCE)
    floor_wrench = sum((wrench(r["force_on_first_xyz_n"], r["point_xyz_mm"]) for r in floor_rows), np.zeros(6))
    applied = np.r_[case["applied_force_xyz_n"], case["applied_moment_about_global_origin_xyz_nmm"]]
    residual = floor_wrench + applied
    member_rows = []
    for name, member in assembly.members.items():
        for i, element in enumerate(member["elements"]):
            local = element["local_K"] @ (element["T"] @ q[element["dofs"]])
            member_rows.append({"member": name, "element": i, "start_xyz_mm": element["start"].tolist(),
                                "end_xyz_mm": element["end"].tolist(), "end_actions_local_n_nmm": local.tolist(),
                                "basis_grain_u_v_xyz": [member["source"][k] for k in ("axis", "section_u", "section_v")],
                                "distributed_external_loads_subtracted": False,
                                "scope": "elastic element nodal internal actions; local bore/section resistance not supplied"})
    section_case = {**case, "equilibrium_feasibility_witness": {
        "feasible": True, "point_actions": [*attachments, *retained, *screws],
        "compression_actions": [*contact_rows, *floor_rows]}}
    section_rows = member_sections(section_case, assembly.geo)
    for row in section_rows:
        row["action_source"] = "same-state compatible conditional elastic point/contact forces and affine selfweight"
        row["physical_demand_bounds_established"] = False
    deformation = []
    for name, member in assembly.members.items():
        nodal = q[member["index"]]
        deformation.append({"member": name, "maximum_node_translation_norm_mm": float(np.linalg.norm(nodal[:, :3], axis=1).max()),
                            "maximum_node_rotation_norm_rad": float(np.linalg.norm(nodal[:, 3:] / ROTATION_SCALE, axis=1).max())})
    force_error = max(float(np.linalg.norm(r[:3])) for r in body_balance.values())
    moment_error = max(float(np.linalg.norm(r[3:])) for r in body_balance.values())
    equilibrium_verified = (force_error < BODY_FORCE_TOLERANCE_N and moment_error < BODY_MOMENT_TOLERANCE_NMM
                            and np.linalg.norm(residual[:3]) < BODY_FORCE_TOLERANCE_N
                            and np.linalg.norm(residual[3:]) < BODY_MOMENT_TOLERANCE_NMM)
    return {"attachment_actions": attachments, "retained_bolt_actions": retained,
            "panel_screw_actions": screws, "contact_actions": contact_rows, "floor_actions": floor_rows,
            "member_element_actions": member_rows,
            "member_section_action_samples": section_rows,
            "timber_deformation_diagnostics": deformation,
            "body_applied_loads": case["loads"],
            "body_equilibrium_residuals": [{"body": name, "force_xyz_n": residual[:3].tolist(),
                                            "moment_about_reference_xyz_nmm": residual[3:].tolist()}
                                           for name, residual in body_balance.items()],
            "global_equilibrium_residual_force_n": residual[:3].tolist(),
            "global_equilibrium_residual_moment_nmm": residual[3:].tolist(),
            "equilibrium_verification": {"all_bodies": len(body_balance), "maximum_body_force_norm_n": force_error,
                                         "maximum_body_moment_about_reference_norm_nmm": moment_error,
                                         "force_tolerance_n": BODY_FORCE_TOLERANCE_N, "moment_tolerance_nmm": BODY_MOMENT_TOLERANCE_NMM,
                                         "all_body_and_global_checks_pass": equilibrium_verified},
            "floor_support_summary": {
                "support_resultant_force_xyz_n": floor_wrench[:3].tolist(),
                "required_horizontal_resultant_xy_n": floor_wrench[:2].tolist(),
                "maximum_centroid_xy_penalty_motion_mm": max((abs(r["tangent_displacement_mm"]) for r in floor_rows if r["kind"] == "floor_tangent"), default=0.),
                "maximum_centroid_tangent_component_n": max((float(np.linalg.norm(r["force_on_first_xyz_n"])) for r in floor_rows if r["kind"] == "floor_tangent"), default=0.),
                "normal_reactions_nonnegative": all(r["compression_n"] >= 0. for r in floor_rows if r["kind"] == "floor_normal"),
                "centroid_xy_penalty_is_exact_distributed_no_slip": False,
                "friction_or_anchor_capacity_established": False},
            "maximum_panel_screw_withdrawal_n": max(r["withdrawal_n"] for r in screws)}


def evaluate_elastic(*, case_id="a12-rear", accessory="retained-original-top-hold",
                     intervals=8, beam_size=150., stiffness=1000., screw_stiffness=1000.,
                     clearance=1.5875, fitting_section="gross", contact_edge=35., floor_tangent_stiffness=100000.) -> dict:
    from scripts.thin_bolted_panel_mechanics import prepare_panel_models

    dependency_paths = ("scripts/thin_bolted_frame_mechanics.py", "scripts/thin_bolted_panel_mechanics.py",
                        "scripts/thin_bolted_steel_resistance.py", "fea/current_response_materials.py",
                        str(GEOMETRY_CACHE.relative_to(ROOT)))
    loaded_dependencies = {path: sha(ROOT / path) for path in dependency_paths}
    if loaded_dependencies["scripts/thin_bolted_frame_mechanics.py"] != LOADED_PRODUCER_SHA256:
        raise ValueError("producer differs from the loaded module")
    layout, evidence, pins = inputs()
    geo = geometry(layout, evidence)
    cases, gravity = load_cases(evidence, geo)
    case = next(c for c in cases if c["case_id"] == case_id and c["accessory_placement"] == accessory)
    panels, _, _ = prepare_panel_models(GEOMETRY_CACHE, intervals=intervals, contact_edge=contact_edge)
    assembly = ElasticAssembly(layout, geo, panels, beam_size=beam_size, fitting_section=fitting_section)
    applied = coupled_load_vector(assembly, case, evidence)
    rigid = assembly.rigid_modes()
    desired = sum((wrench(r["force_xyz_n"], r["point_xyz_mm"], REFERENCE) for r in case["loads"]), np.zeros(6))
    load_residual = rigid.T @ applied - desired
    groups, contacts, tangents = elastic_connections(assembly, stiffness, clearance, screw_stiffness,
                                                    floor_tangent_stiffness=floor_tangent_stiffness)
    connector_rigid_error = max(float(abs(group["B"] @ rigid).max()) for group in groups)
    contact_rigid_error = max(float(abs(contact["B"] @ rigid).max()) for contact in contacts if contact["second"] != "floor")
    # Frozen unit directions are serialized to nine decimal places. Their
    # tiny nonorthogonality relative to exact panel tangents propagates over
    # the2.4m body. This guard is3nanometres for a1radian coupon, not a
    # physical connection clearance or permission to omit a thickness arm.
    if max(connector_rigid_error, contact_rigid_error) > 3e-6:
        worst_group = max(groups, key=lambda g: float(abs(g["B"] @ rigid).max()))
        worst_contact = max((c for c in contacts if c["second"] != "floor"), key=lambda c: float(abs(c["B"] @ rigid).max()))
        raise ValueError(f"internal port creates forces under common rigid motion: {connector_rigid_error=} {contact_rigid_error=} group={worst_group['id']} contact={worst_contact['id']}")
    response = compatible_contact_solve(assembly.K, applied, groups, contacts, tangents)
    recovered = elastic_actions(assembly, case, response, groups, contacts, tangents) if response["converged"] else {}
    result = {"schema": "thin_bolted_compatible_elastic_frame/v1", "candidate": layout["candidate"], "revision": layout["revision"],
              "layout_report_sha256": LAYOUT_SHA,
              "disposition": "CONDITIONAL_ELASTIC_SURROGATE", "case_id": case_id, "accessory_placement": accessory,
              "source_sha256": pins, "geometry_cache_sha256": GEOMETRY_CACHE_SHA,
              "method_coupons": elastic_method_coupons(), "gravity": gravity,
              "parameters": {"panel_intervals": intervals, "beam_size_mm": beam_size, "foundation_port_cell_mm": contact_edge,
                             "wood_E_mpa": 11031.612, "wood_G_over_E_clear_DF_analogy": .064,
                             "bolt_axial_lateral_stiffness_n_mm": stiffness, "Hillman_axial_lateral_stiffness_n_mm": screw_stiffness,
                             "relative_bolt_radial_clearance_mm": clearance, "fitting_section": fitting_section,
                             "panel_foundation_n_mm3": 2., "flange_corner_contact_n_mm": 10000.,
                             "floor_corner_contact_n_mm": 25000., "floor_no_slip_xy_penalty_n_mm": floor_tangent_stiffness},
              "counts": {"dofs": assembly.ndof, "timber_members": 20, "finite_fittings": 36, "flexible_panels": 6,
                         "physical_bolt_axes": 70, "bolt_interfaces": 84, "panel_screw_axes": 66,
                         "normal_contacts": len(contacts)},
              "applied_force_xyz_n": case["applied_force_xyz_n"],
              "applied_moment_about_global_origin_xyz_nmm": case["applied_moment_about_global_origin_xyz_nmm"],
              "global_support_equilibrium": support_equilibrium(case, geo["floor_footprints"]),
              "common_wrench_reference_xyz_mm": REFERENCE.tolist(),
              "discrete_load_rigid_work_residual_force_n": load_residual[:3].tolist(),
              "discrete_load_rigid_work_residual_moment_nmm": load_residual[3:].tolist(),
              "material_stiffness_rigid_motion_residual": float(abs(assembly.K @ rigid).max()),
              "connector_common_rigid_motion_error_mm": connector_rigid_error,
              "internal_contact_common_rigid_motion_error_mm": contact_rigid_error,
              "common_rigid_motion_serialized_geometry_tolerance_mm": 3e-6,
              "response": {k: (v.tolist() if isinstance(v, np.ndarray) else v) for k, v in response.items()
                           if k not in ("connector_local_force_n", "normal_contact_force_n", "normal_contact_displacement_mm")},
              **recovered,
              "usable_conditional_actions": bool(response["converged"] and recovered["equilibrium_verification"]["all_body_and_global_checks_pass"]),
              "flange_contact_actions": [r for r in recovered.get("contact_actions", []) if r["kind"] == "flange_contact"],
              "limits": ["Conditional finite spring values and radial-clearance scenario are not measured or guaranteed stiffness bounds.",
                         "Uniform gross timber beams and condensed finite steel strip legs omit local cut stiffness and actual curved heel/hole compliance.",
                         "Retained two-timber bolt axial capture/compression is a bilateral lumped translation surrogate; bolt shaft bending and own washer prying remain unresolved.",
                         "Fourteen shared shafts use two independent attachment spring ports; a common physical shaft axial/bending/contact field is not solved. Both same-state side actions remain separate.",
                         "Bolt rotational springs, clamp friction, historical forces and SPAX stiffness are not credited.",
                         "Linear beam port interpolation requires refinement. Rigid-motion compatibility does not qualify its flexible transfer or local cut mechanics.",
                         "No-slip floor and penalty values are assumed. Normal contact is unilateral; no foot is anchored.",
                         "Local metal gravity routing remains conditional; pads have no mass input. No delivered material, hardware or floor is inspected."],
              "release": RELEASE, "compatible_numerical_mvp_complete": False}
    for path, expected in loaded_dependencies.items():
        if sha(ROOT / path) != expected:
            raise ValueError(f"mechanics dependency edited during evaluation: {path}")
        result["source_sha256"][path] = expected
    identity = {"case_id": case_id, "accessory_placement": accessory, "parameters": result["parameters"],
                "geometry_cache_sha256": GEOMETRY_CACHE_SHA}
    result["state_id"] = "thin-v4-" + hashlib.sha256(json.dumps(identity, sort_keys=True, separators=(",", ":")).encode()).hexdigest()[:24]
    for table in ("attachment_actions", "retained_bolt_actions", "panel_screw_actions", "contact_actions",
                  "flange_contact_actions", "floor_actions", "member_element_actions", "member_section_action_samples"):
        for row in result.get(table, []):
            row["state_id"] = result["state_id"]
    return result


def point_matrix(point: list | np.ndarray, reference=REFERENCE,
                 scale: float = ROTATION_SCALE) -> np.ndarray:
    """Point displacement from q=(u,scale*theta), by direct cross product."""
    if not np.isfinite(scale) or scale <= 0:
        raise ValueError("positive finite rotation scale required")
    return np.hstack((np.eye(3), -cross_matrix(np.asarray(point) - reference) / scale))


def wrench(force, point, reference=(0., 0., 0.), couple=(0., 0., 0.)) -> np.ndarray:
    force = np.asarray(force, dtype=float)
    return np.r_[force, np.asarray(couple) + np.cross(np.asarray(point) - reference, force)]


def geometry(layout: dict, evidence: dict) -> dict:
    """Read original-size CAD datums and reuse the frozen hardware producer.

    No finished CAD export or native solve occurs. CAD is used only for exact
    foot corners, member grain/section datums and gravity volume/centroids.
    """
    if GEOMETRY_CACHE.exists():
        return cached_geometry(layout, evidence)
    import cadquery as cq

    from fea.current_response_model import gross_member_record, level_face_points
    from fea.horizontal_frame_members import axes as member_axes
    from mini_moonboard.floor_flush_width import KERF_RIGHT, variant
    from scripts import thin_bolted_fitting_screen as fitting
    from scripts import thin_bolted_layout_revision as revision

    frame = variant(KERF_RIGHT)
    raw = {p.name: p for p in frame.uncut_wood_parts()}
    adapter = SimpleNamespace(b=frame.b, leg=frame.leg_source)
    floor, members = {}, []
    for name, part in raw.items():
        if name.startswith(("main_", "kicker_")):
            continue
        grain, section = getattr(frame, "MEMBER_AXES", {}).get(name) or member_axes(adapter, name)
        record = gross_member_record(part, grain, section)
        if name.startswith("base_rail_bottom_"):
            delta = np.array([0., np.sin(np.deg2rad(40.)), np.cos(np.deg2rad(40.))]) * 50.8
            record["start"] = (np.asarray(record["start"]) + delta).tolist()
            record["end"] = (np.asarray(record["end"]) + delta).tolist()
        members.append(record)
        if name.startswith(("base_post_", "base_floor_", "lumber_leg_")):
            floor[name] = [p.tolist() for p in level_face_points(part.shape, True)]
    if len(members) != 20 or len(floor) != 8:
        raise ValueError("expected twenty timbers and eight floor footprints")

    body_rows = [{"id": row["name"], "kind": "panel" if row["name"].startswith(("main_", "kicker_")) else "timber",
                  "mass_kg": row["volume_mm3"] * 500e-9,
                  "center_xyz_mm": row["center_of_mass_xyz_mm"]}
                 for row in evidence["finished_stock"]]
    components = []
    for row in layout["raw_fittings"]:
        spec = fitting.FITTINGS["B104ZN"] if row["angle_id"].startswith("B104ZN") else fitting.Fitting(
            "B103ZN", 104.775, 41.275, 2, 1, 3.53, .56)
        origin, u, v, w = [np.array(row[k]) for k in ("origin_xyz_mm", "u_xyz", "v_xyz", "w_xyz")]
        center = fitting.template(spec).Center()
        placed = origin + u * center.x + v * center.y + w * center.z
        body_rows.append({"id": row["angle_id"], "kind": "fitting",
                          "mass_kg": spec.catalog_mass_lb * .45359237,
                          "center_xyz_mm": placed.tolist(),
                          "mass_basis": "catalog mass; conditional nominal CAD centroid"})
    axes = copy.deepcopy(layout["installed_axes"])
    for axis in axes:
        axis["point"], axis["direction"] = cq.Vector(*axis["point"]), cq.Vector(*axis["direction"])
    metal, _ = revision.metal_with_washers(axes)
    by_axis = {row["id"]: row for row in layout["installed_axes"]}
    for shaft, role, shape in metal:
        components.append({"id": shaft + "/" + role,
                           "owner": by_axis[shaft]["receivers"][0],
                           "mass_kg": shape.Volume() * 7850e-9,
                           "center_xyz_mm": list(shape.Center().toTuple()),
                           "basis": "conditional nominal solid metal; first timber owns gravity only"})
    metal_mass = sum(row["mass_kg"] for row in components)
    if abs(metal_mass - evidence["mass_components"]["conditional_bolt_metal_kg_at_7850_kg_m3"]) > 1e-8:
        raise ValueError("fresh bolt-metal gravity differs from integrated model")
    return {"bodies": body_rows, "bolt_gravity_components": components,
            "floor_footprints": floor, "members": members,
            "cadquery_version": cq.__version__}


def cached_geometry(layout: dict, evidence: dict) -> dict:
    import cadquery as cq

    from fea.current_response_model import gross_member_record, level_face_points

    if sha(GEOMETRY_CACHE) != GEOMETRY_CACHE_SHA:
        raise ValueError("exact parent-owned geometry cache differs")
    cache = json.loads(GEOMETRY_CACHE.read_text())
    floor, members = {}, []
    for row in cache["raw_parts"]:
        if sha(ROOT / row["path"]) != row["sha256"]:
            raise ValueError(f"raw beam source differs: {row['id']}")
        name = row["member"]
        shape = cq.Shape.importBrep(str(ROOT / row["path"]))
        grain = cq.Vector(*row["grain_axis_xyz"])
        section = cq.Vector(1., 0., 0.)
        if name.startswith(("base_side_", "base_principal_")):
            section = -section
        elif name.startswith("base_rail_"):
            section = cq.Vector(0., np.sin(np.deg2rad(40.)), np.cos(np.deg2rad(40.)))
        elif name == "base_header":
            section = cq.Vector(0., 1., 0.)
        members.append(gross_member_record(SimpleNamespace(name=name, shape=shape), grain, section))
        if name.startswith(("base_post_", "base_floor_", "lumber_leg_")):
            floor[name] = [point.tolist() for point in level_face_points(shape, True)]
    by_axis = {row["id"]: row for row in layout["installed_axes"]}
    feature_owner = {r["identity"]: r["panel"] for r in evidence["panel_machining"]["features"]}
    screw_owner = {r["axis_id"]: r for r in layout["screw_axes"]}
    bodies, components = [], []
    for row in cache["parts"]:
        kind = row["kind"]
        if kind in ("timber", "panel", "bracket"):
            mass = row["volume_mm3"] * 500e-9 if kind != "bracket" else (.78 if row["id"].startswith("B104ZN") else .56) * .45359237
            bodies.append({"id": row["id"], "kind": "fitting" if kind == "bracket" else kind,
                           "mass_kg": mass, "center_xyz_mm": row["center_of_mass_xyz_mm"]})
        elif kind in ("shaft", "head", "head_washer", "nut_washer", "nut"):
            components.append({"id": row["id"], "owner": by_axis[row["axis_id"]]["receivers"][0],
                               "mass_kg": row["volume_mm3"] * 7850e-9, "center_xyz_mm": row["center_of_mass_xyz_mm"],
                               "basis": "conditional steel envelope; first timber is a conditional local gravity routing"})
        elif row["id"] in feature_owner and kind == "tnut":
            components.append({"id": row["id"], "owner": feature_owner[row["id"]],
                               "mass_kg": row["volume_mm3"] * 7850e-9, "center_xyz_mm": row["center_of_mass_xyz_mm"],
                               "basis": "separate source-bound nominal T-nut steel gravity on its owned panel"})
        elif kind == "screw":
            components.append({"id": row["id"], "owner": screw_owner[row["axis_id"]]["receiver"],
                               "mass_kg": row["volume_mm3"] * 7850e-9, "center_xyz_mm": row["center_of_mass_xyz_mm"],
                               "basis": "separate conditional Hillman steel envelope; receiver-only local routing pending split"})
    if len(bodies) != 62 or len(components) != 350 + 142 + 66:
        raise ValueError("exact geometry gravity census differs")
    if TAKEOFF.exists():
        if sha(TAKEOFF) != TAKEOFF_SHA:
            raise ValueError("source-bound local gravity ownership differs")
        takeoff = json.loads(TAKEOFF.read_text())
        expected_mass = sum(r["mass_kg"] for r in components)
        components = [{"id": row["id"] + f"/gravity-share-{i}", "owner": row["owner"],
                       "mass_kg": row["mass_kg"], "center_xyz_mm": row["centroid_xyz_mm"],
                       "basis": "conditional exact-geometry local ownership: " + row["ownership_method"]}
                      for i, row in enumerate(takeoff["takeoff"]["conditional_metal_gravity_rows"])]
        if abs(sum(r["mass_kg"] for r in components) - expected_mass) > 1e-8:
            raise ValueError("separate local metal gravity ownership changes mass")
    return {"bodies": bodies, "bolt_gravity_components": components, "floor_footprints": floor,
            "members": members, "cadquery_version": cq.__version__,
            "exact_geometry_cache_sha256": GEOMETRY_CACHE_SHA,
            "local_metal_gravity_routing_conditional": True, "pads_modeled": False}


def load_cases(evidence: dict, geo: dict) -> tuple[list, dict]:
    features = {r["identity"]: r for r in evidence["panel_machining"]["features"]}
    panels = [r for r in geo["bodies"] if r["kind"] == "panel"]
    panel_mass = sum(r["mass_kg"] for r in panels)
    permanent = [{"id": "self-weight/" + r["id"], "body": r["id"],
                  "point_xyz_mm": r["center_xyz_mm"], "force_xyz_n": [0., 0., -r["mass_kg"] * GRAVITY]}
                 for r in geo["bodies"]]
    permanent += [{"id": "bolt-weight/" + r["id"], "body": r["owner"],
                   "point_xyz_mm": r["center_xyz_mm"], "force_xyz_n": [0., 0., -r["mass_kg"] * GRAVITY]}
                  for r in geo["bolt_gravity_components"]]
    primary = features["hold_tnut_main_A12"]
    # Original current_response_model: x=0, maximum hold s, at panel rear.
    rear_top = np.asarray(primary["start_xyz_mm"]) + np.array([1019.2, 0., 0.]) + np.asarray(primary["direction_xyz"]) * 18.25625
    cases = []
    for placement in ("retained-original-top-hold", "proportional-six-panel-sensitivity"):
        if placement == "retained-original-top-hold":
            accessory = [{"id": "accessory/" + r["id"], "body": r["id"],
                          "point_xyz_mm": rear_top.tolist(), "force_xyz_n": [0., 0., -12.5 * GRAVITY]}
                         for r in panels if r["id"].startswith("main_upper_")]
        else:
            accessory = [{"id": "accessory/" + r["id"], "body": r["id"],
                          "point_xyz_mm": r["center_xyz_mm"],
                          "force_xyz_n": [0., 0., -25. * r["mass_kg"] / panel_mass * GRAVITY]}
                         for r in panels]
        if abs(sum(r["force_xyz_n"][2] for r in accessory) + 25. * GRAVITY) > 1e-9:
            raise ValueError("accessory gravity does not reconcile")
        for name, hold, horizontal in (*CASE_INPUTS, ("gravity-only", None, (0., 0.))):
            loads = copy.deepcopy(permanent + accessory)
            hold_record = None
            if hold:
                feature = features["hold_tnut_main_" + hold]
                inward = np.asarray(feature["direction_xyz"]); inward /= np.linalg.norm(inward)
                front = np.asarray(feature["start_xyz_mm"])
                point = front - 100. * inward
                force = np.array([*horizontal, -2. * 250. * .45359237 * GRAVITY])
                mid = front + 18.25625 / 2. * inward
                hold_record = {"label": hold, "panel": feature["panel"],
                               "front_xyz_mm": front.tolist(), "load_point_xyz_mm": point.tolist(),
                               "panel_midplane_xyz_mm": mid.tolist(), "force_xyz_n": force.tolist(),
                               "moment_about_panel_midplane_xyz_nmm": np.cross(point - mid, force).tolist()}
                loads.append({"id": "climber/" + hold, "body": feature["panel"],
                              "point_xyz_mm": point.tolist(), "force_xyz_n": force.tolist()})
            total = sum((wrench(r["force_xyz_n"], r["point_xyz_mm"]) for r in loads), np.zeros(6))
            cases.append({"case_id": name, "accessory_placement": placement,
                          "primary_load_basis": placement == "retained-original-top-hold",
                          "hold": hold_record, "loads": loads,
                          "applied_force_xyz_n": total[:3].tolist(),
                          "applied_moment_about_global_origin_xyz_nmm": total[3:].tolist()})
    return cases, {"known_modeled_mass_kg": sum(r["mass_kg"] for r in geo["bodies"]) + sum(r["mass_kg"] for r in geo["bolt_gravity_components"]),
                   "additional_accessory_kg": 25., "primary_accessory_placement": "retained-original-top-hold",
                   "primary_accessory_point_xyz_mm": rear_top.tolist(),
                   "unitemized_accessory_scope": "Original 25 kg holds/hold-bolts/electrical allowance; separate nominal T-nut and Hillman envelope gravity included when exact cache is used. Pads have no mass input. No parts are weighed."}


def equilibrium_operator(bodies: list[str], edges: list[dict], reference=REFERENCE,
                         scale=ROTATION_SCALE) -> csr_matrix:
    """Each column maps a scalar point action to every rigid body's wrench.

    Positive scalar acts on first in direction; equal opposite acts on second.
    Moments are about one common reference and divided by scale. Its transpose
    is the virtual-work compatible displacement-constraint matrix.
    """
    index = {name: i for i, name in enumerate(bodies)}
    rows, cols, values = [], [], []
    for column, edge in enumerate(edges):
        action = wrench(edge["direction_xyz"], edge["point_xyz_mm"], reference)
        action[3:] /= scale
        for body, sign in ((edge["first"], 1.), (edge["second"], -1.)):
            if body == "floor":
                continue
            if body not in index:
                raise ValueError(f"unmapped action body: {body}")
            for component, value in enumerate(sign * action):
                if abs(value) > 1e-14:
                    rows.append(6 * index[body] + component); cols.append(column); values.append(value)
    return csr_matrix((values, (rows, cols)), shape=(6 * len(bodies), len(edges)))


def action_edges(layout: dict, geo: dict) -> list[dict]:
    result = []

    def vector(identifier, first, second, point, **metadata):
        for component, direction in enumerate(np.eye(3)):
            result.append({"id": identifier, "component": component, "first": first, "second": second,
                           "point_xyz_mm": list(point), "direction_xyz": direction.tolist(),
                           "lower": None, "upper": None, **metadata})

    for axis in layout["installed_axes"]:
        if axis["attachments"]:
            for attachment in axis["attachments"]:
                vector(axis["id"] + "/" + attachment["angle_id"], attachment["receiver"],
                       attachment["angle_id"], attachment["entry_xyz_mm"], kind="fitting_bolt",
                       axis_id=axis["id"], angle_id=attachment["angle_id"], flange=attachment["flange"])
        else:
            # The ordinary two-timber bolt transfers at the common face,
            # not at its externally recorded start. The retained start remains
            # provenance for length and axial ordering only.
            first, second = axis["receivers"]
            member = next(r for r in geo["members"] if r["name"] == first)
            p = np.asarray(axis["point"]); d = np.asarray(axis["direction"])
            center = .5 * (np.asarray(member["start"]) + member["end"])
            width = member["width_mm"] if abs(np.dot(member["section_u"], d)) > .999 else member["depth_mm"]
            interface = p + d * (np.dot(center - p, d) + width / 2.)
            vector(axis["id"], first, second, interface, kind="retained_bolt", axis_id=axis["id"])
    for fitting in layout["raw_fittings"]:
        o, u, v, w = [np.asarray(fitting[k]) for k in ("origin_xyz_mm", "u_xyz", "v_xyz", "w_xyz")]
        lengths = (104.775, 41.275 if fitting["angle_id"].startswith("B103ZN") else 88.9)
        for flange, receiver, normal, along, length in (
            ("beam", fitting["beam"], v, u, lengths[0]),
            ("post", fitting["post"], u, v, lengths[1])):
            for corner, (station, width) in enumerate((a, b) for a in (5.55625, length) for b in (-20.6375, 20.6375)):
                result.append({"id": fitting["angle_id"] + "/" + flange + f"/contact-{corner}",
                               "kind": "flange_contact", "first": fitting["angle_id"], "second": receiver,
                               "point_xyz_mm": (o + along * station + w * width).tolist(),
                               "direction_xyz": normal.tolist(), "lower": 0., "upper": None,
                               "angle_id": fitting["angle_id"], "flange": flange})
    for screw in layout["screw_axes"]:
        vector(screw["axis_id"], screw["receiver"], screw["panel"], screw["origin_xyz_mm"],
               kind="panel_screw", axis_id=screw["axis_id"])
    for name, points in geo["floor_footprints"].items():
        for corner, point in enumerate(points):
            result.append({"id": name + f"/floor-{corner}", "kind": "floor_normal", "first": name,
                           "second": "floor", "point_xyz_mm": point, "direction_xyz": [0., 0., 1.],
                           "lower": 0., "upper": None})
        center = np.mean(points, axis=0)
        for component in (0, 1):
            result.append({"id": name + "/no-slip", "component": component, "kind": "floor_tangent",
                           "first": name, "second": "floor", "point_xyz_mm": center.tolist(),
                           "direction_xyz": np.eye(3)[component].tolist(), "lower": None, "upper": None})
    return result


def support_equilibrium(case: dict, footprints: dict) -> dict:
    force, moment = [np.array(case[k]) for k in ("applied_force_xyz_n", "applied_moment_about_global_origin_xyz_nmm")]
    vertical = -force[2]
    points = np.unique(np.array([p[:2] for corners in footprints.values() for p in corners]), axis=0)
    hull = ConvexHull(points)
    cop = np.array([moment[1] / vertical, -moment[0] / vertical])
    reserves = -(hull.equations[:, :2] @ cop + hull.equations[:, 2])
    A = np.vstack((np.ones(len(points)), points.T))
    solution = linprog(np.zeros(len(points)), A_eq=A, b_eq=[vertical, vertical * cop[0], vertical * cop[1]],
                       bounds=(0., None), method="highs")
    return {"normal_equilibrium_possible": bool(solution.success),
            "required_center_of_pressure_xy_mm": cop.tolist(), "support_hull_xy_mm": points[hull.vertices].tolist(),
            "minimum_hull_edge_reserve_mm": float(reserves.min()),
            "horizontal_resultant_required_xyz_n": [-float(force[0]), -float(force[1]), 0.],
            "normal_solution_n": solution.x.tolist() if solution.success else None,
            "normal_solution_points_xy_mm": points.tolist(),
            "floor_no_slip_assumed": True, "floor_no_slip_verified": False,
            "joint_compatibility_checked": False,
            "scope": "necessary global no-slip tipping equilibrium; no floor friction capacity or connection stability"}


def feasibility(case: dict, bodies: list[str], edges: list[dict], operator: csr_matrix) -> dict:
    indices = {name: i for i, name in enumerate(bodies)}
    applied = np.zeros((len(bodies), 6))
    for load in case["loads"]:
        value = wrench(load["force_xyz_n"], load["point_xyz_mm"], REFERENCE)
        value[3:] /= ROTATION_SCALE
        applied[indices[load["body"]]] += value
    n = len(edges)
    Aeq = hstack((operator, csr_matrix((operator.shape[0], 1))), format="csr")
    identity = scipy.sparse.eye(n, format="csr")
    Aub = vstack((hstack((identity, -np.ones((n, 1)))), hstack((-identity, -np.ones((n, 1))))), format="csr")
    strict_bearing = []
    for body in sorted({e["first"] for e in edges if e["kind"] == "floor_normal"}):
        row = np.zeros(n + 1)
        for i, edge in enumerate(edges):
            if edge["kind"] == "floor_normal" and edge["first"] == body:
                row[i] = -1.
        strict_bearing.append(row)
    Aub = vstack((Aub, csr_matrix(strict_bearing)), format="csr")
    b_ub = np.r_[np.zeros(2 * n), -np.ones(len(strict_bearing)) * 1e-4]
    bounds = [(r["lower"], r["upper"]) for r in edges] + [(0., None)]
    disabled = []
    for _ in range(9):
        answer = linprog(np.r_[np.zeros(n), 1.], A_ub=Aub, b_ub=b_ub,
                         A_eq=Aeq, b_eq=-applied.ravel(), bounds=bounds, method="highs")
        if not answer.success:
            return {"feasible": False, "solver_status": answer.message, "disabled_nonbearing_tangent_bodies": disabled,
                    "compatible_strength_demand": False}
        normals = defaultdict(float)
        for edge, scalar in zip(edges, answer.x[:n], strict=True):
            if edge["kind"] == "floor_normal":
                normals[edge["first"]] += scalar
        new = [body for body, reaction in normals.items() if reaction <= 1e-7 and body not in disabled]
        if not new:
            break
        disabled.extend(new)
        for i, edge in enumerate(edges):
            if edge["kind"] == "floor_tangent" and edge["first"] in new:
                bounds[i] = (0., 0.)
    else:
        raise RuntimeError("nonbearing no-slip removal did not terminate")
    values = answer.x[:n]
    recovered = (operator @ values).reshape((-1, 6))
    residual = applied + recovered
    actions, scalars = {}, []
    for edge, value in zip(edges, values, strict=True):
        if "component" in edge:
            row = actions.setdefault(edge["id"], {k: v for k, v in edge.items() if k not in ("component", "direction_xyz", "lower", "upper")})
            row.setdefault("force_on_first_xyz_n", [0., 0., 0.])[edge["component"]] = float(value)
            row["moment_on_first_at_point_xyz_nmm"] = None
        elif abs(value) > 1e-8:
            scalars.append({"id": edge["id"], "kind": edge["kind"], "first": edge["first"], "second": edge["second"],
                            "point_xyz_mm": edge["point_xyz_mm"], "force_on_first_xyz_n": (value * np.asarray(edge["direction_xyz"])).tolist(),
                            "normal_action_n": float(value)})
    maximum_force = float(abs(residual[:, :3]).max())
    maximum_moment = float(abs(residual[:, 3:]).max() * ROTATION_SCALE)
    if maximum_force > 1e-5 or maximum_moment > 1e-2:
        raise ValueError("equilibrium witness does not close")
    return {"feasible": True, "solver_status": answer.message,
            "minimized_maximum_scalar_component_n": float(answer.x[-1]),
            "disabled_nonbearing_tangent_bodies": disabled,
            "strict_bearing_normal_per_foot_n": 1e-4,
            "maximum_body_force_residual_n": maximum_force, "maximum_body_moment_residual_nmm": maximum_moment,
            "body_balance": [{"body": name, "applied_force_xyz_n": applied[i, :3].tolist(),
                              "applied_moment_about_reference_xyz_nmm": (applied[i, 3:] * ROTATION_SCALE).tolist(),
                              "recovered_force_xyz_n": recovered[i, :3].tolist(),
                              "recovered_moment_about_reference_xyz_nmm": (recovered[i, 3:] * ROTATION_SCALE).tolist()}
                             for i, name in enumerate(bodies)],
            "point_actions": list(actions.values()), "compression_actions": scalars,
            "compatible_strength_demand": False, "conservative_force_upper_bound": False,
            "shaft_bending_and_prying_moments_resolved": False}


def method_coupons() -> dict:
    point = np.array([3., 4., 5.]); q = np.array([2., -1., 3., .02, .03, -.01])
    velocity = point_matrix(point, np.zeros(3), 1.) @ q
    expected = q[:3] + np.cross(q[3:], point)
    force = np.array([7., -2., 4.])
    virtual_work = float(force @ velocity)
    dual_work = float(wrench(force, point) @ q)
    if not np.allclose(velocity, expected, rtol=0., atol=1e-14) or abs(virtual_work - dual_work) > 1e-13:
        raise AssertionError("point/wrench virtual work coupon failed")
    # A 100 N load at x=2 on supports x=0,10 has reactions80,20 N.
    beam = linprog([0., 0.], A_eq=[[1., 1.], [0., 10.]], b_eq=[100., 200.], bounds=(0., None), method="highs")
    tipping = linprog([0., 0.], A_eq=[[1., 1.], [0., 10.]], b_eq=[100., 1200.], bounds=(0., None), method="highs")
    if not beam.success or not np.allclose(beam.x, [80., 20.], atol=1e-12) or tipping.success:
        raise AssertionError("unilateral support coupon failed")
    return {"point_displacement_error_mm": float(abs(velocity - expected).max()),
            "virtual_work_error_nmm": abs(virtual_work - dual_work),
            "simple_beam_reactions_n": beam.x.tolist(), "outside_support_load_rejected": not tipping.success,
            "native_solver_behavior_involved": False}


def member_sections(case: dict, geo: dict) -> list[dict]:
    """Sample whole-member section actions from the fresh witness's own loads.

    Wood self-weight has an affine line distribution preserving its exact CAD
    mass and centroid. Other attached weights retain their actual point-load
    application. This is a gross-section action record, never a net-section
    stress, splitting resistance or conservative maximum bound.
    """
    witness = case["equilibrium_feasibility_witness"]
    if not witness["feasible"]:
        return []
    by_body = defaultdict(list)
    for action in [*witness["point_actions"], *witness["compression_actions"]]:
        force = np.asarray(action["force_on_first_xyz_n"])
        for body, sign in ((action["first"], 1.), (action["second"], -1.)):
            if body != "floor":
                by_body[body].append((np.asarray(action["point_xyz_mm"]), sign * force))
    for load in case["loads"]:
        if not load["id"].startswith("self-weight/"):
            by_body[load["body"]].append((np.asarray(load["point_xyz_mm"]), np.asarray(load["force_xyz_n"])))
    body_rows = {r["id"]: r for r in geo["bodies"]}
    result = []
    for member in geo["members"]:
        name = member["name"]
        grain, u, v = [np.asarray(member[key]) for key in ("axis", "section_u", "section_v")]
        start, end = [np.asarray(member[key]) for key in ("start", "end")]
        low, high = float(grain @ start), float(grain @ end)
        length, mid = high - low, .5 * (high + low)
        center = np.asarray(body_rows[name]["center_xyz_mm"])
        center_s = float(grain @ center)
        off_axis = center - grain * center_s
        beta = 12. * (center_s - mid) / length ** 2
        if min(1. + beta * (low - mid), 1. + beta * (high - mid)) < -1e-10:
            raise ValueError(f"affine gravity profile becomes negative: {name}")
        gravity = np.array([0., 0., -body_rows[name]["mass_kg"] * GRAVITY])
        actions = by_body[name]
        stations = list(np.linspace(low, high, 51))
        for point, _ in actions:
            station = float(point @ grain)
            stations.extend((max(low, min(high, station - 1e-5)), max(low, min(high, station + 1e-5))))
        samples = []
        for s in sorted(set(stations)):
            cut = start + grain * (s - low)
            fraction = ((s - low) + .5 * beta * ((s - mid) ** 2 - (low - mid) ** 2)) / length
            first_moment = (.5 * (s ** 2 - low ** 2) + beta * ((s ** 3 - low ** 3) / 3. - .5 * mid * (s ** 2 - low ** 2))) / length
            force = gravity * fraction
            moment = np.cross((off_axis - cut) * fraction + grain * first_moment, gravity)
            for point, action in actions:
                if point @ grain < s:
                    force += action
                    moment += np.cross(point - cut, action)
            # Force/couple on the lower portion from its omitted upper portion.
            samples.append((s, -np.r_[np.array([grain, u, v]) @ force, np.array([grain, u, v]) @ moment]))
        values = np.array([row[1] for row in samples])
        labels = ("axial_n", "shear_u_n", "shear_v_n", "torsion_nmm", "bending_u_nmm", "bending_v_nmm")
        extrema = {}
        for component, label in enumerate(labels):
            i = int(np.argmax(abs(values[:, component])))
            extrema[label] = {"signed_action": float(values[i, component]),
                              "cut_grain_station_mm": float(samples[i][0]),
                              "cut_xyz_mm": (start + grain * (samples[i][0] - low)).tolist()}
        result.append({"member": name, "sampled_cuts": len(samples), "basis_grain_u_v_xyz": [grain.tolist(), u.tolist(), v.tolist()],
                       "sampled_extrema": extrema, "affine_selfweight_preserves_mass_and_centroid": True,
                       "compatible_strength_demand": False, "conservative_upper_bound": False})
    return result


def evaluate() -> dict:
    layout, evidence, pins = inputs()
    geo = geometry(layout, evidence)
    cases, mass = load_cases(evidence, geo)
    bodies = [r["id"] for r in geo["bodies"]]
    edges = action_edges(layout, geo)
    operator = equilibrium_operator(bodies, edges)
    singular = svdvals(operator.toarray())
    threshold = singular[0] * max(operator.shape) * 1e-10
    rank = int(np.count_nonzero(singular > threshold))
    for case in cases:
        case["global_support"] = support_equilibrium(case, geo["floor_footprints"])
        case["equilibrium_feasibility_witness"] = feasibility(case, bodies, edges, operator)
        case["member_section_action_samples"] = member_sections(case, geo)
    pins[str(Path(__file__).relative_to(ROOT))] = sha(Path(__file__))
    if pins[str(Path(__file__).relative_to(ROOT))] != LOADED_PRODUCER_SHA256:
        raise ValueError("producer edited during evaluation; result is not source bound")
    for path in ("fea/current_response_model.py", "fea/horizontal_frame_members.py", "scripts/clear_space_batch.py", "thin-bolted-candidate.json"):
        pins[path] = sha(ROOT / path)
    return {"schema": "thin_bolted_fresh_frame_statics/v1", "candidate": layout["candidate"], "revision": layout["revision"],
            "question": "Can this current geometry supply global unilateral floor equilibrium and a complete rigid-body point-force/contact equilibrium witness under fresh retained loads?",
            "disposition": "CONDITIONAL_EQUILIBRIUM_METHOD_ONLY", "source_sha256": pins,
            "runtime": {"numpy": np.__version__, "scipy": scipy.__version__, "cadquery": geo["cadquery_version"]},
            "method_coupons": method_coupons(), "gravity": mass, "geometry": geo,
            "method": {"force_units": "N", "moment_units": "Nmm", "coordinates": "global XYZ mm",
                       "common_reference_xyz_mm": REFERENCE.tolist(), "rotation_scale_mm": ROTATION_SCALE,
                       "rigid_timber_fittings_and_panels": True, "shaft_rotation_torque_credited": False,
                       "bolt_point_translation_constraints": 3, "ideal_revolute_5_constraint_results_used": False,
                       "flange_contact": "four supported nominal seat corners, compression only; no tangential friction",
                       "bolt_point_force": "bilateral 3D point force; axial capture/compression and bore engagement are idealized, no bending couple",
                       "panel_screw_constraint": "bilateral 3D point force; physical screw stiffness and panel bending not supplied",
                       "floor_contact": "four exact CAD foot corners per8footprints, normal>=0; no-slip XY at footprint centroid only while resultant normal>1e-7N",
                       "optimizer": "HiGHS linear program, minimize maximum absolute scalar action; feasible witness only",
                       "clearance_engagement_checked": False, "stiffness_response_computed": False,
                       "native_finite_element_solve": False, "historical_force_fields_used": False},
            "assembled_all_contacts_closed_rank": {"body_count": len(bodies), "rigid_body_variables": 6 * len(bodies),
                                                   "scalar_action_count": len(edges), "rank": rank,
                                                   "free_motion_count": 6 * len(bodies) - rank,
                                                   "threshold": float(threshold),
                                                   "minimum_singular_value": float(singular[-1]),
                                                   "unilateral_active_set_stability_proved": False},
            "action_columns": edges, "cases": cases,
            "counts": {"timber": 20, "panels": 6, "fittings": 36, "physical_bolt_axes": 70,
                       "flange_bolt_attachments": 72, "retained_bolt_interfaces": 12, "panel_screw_axes": 66,
                       "floor_footprints": 8, "load_states": len(cases)},
            "release": RELEASE,
            "remaining": ["Establish compatible finite timber/panel/connector stiffness, unilateral contact, real bore engagement and rotational restraint.",
                          "Recover physical bolt bending/prying and unequal shared-shaft internal actions; the LP allocation cannot be used as a strength upper bound.",
                          "Bind actual hardware/product geometry, material and complete joint/member/panel resistance; no capability transfers from historical candidates.",
                          "Recorded density/catalog/25kg assumptions are analytical; no wood, parts or floor were inspected."],
            "compatible_numerical_mvp_complete": False}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=OUTPUT)
    parser.add_argument("--elastic", action="store_true", help="Coupled finite timber/fitting/panel conditional response")
    parser.add_argument("--coupons", action="store_true", help="Run inexpensive analytic known-answer coupons only")
    parser.add_argument("--case", choices=[c[0] for c in CASE_INPUTS] + ["gravity-only"], default="a12-rear")
    parser.add_argument("--accessory", choices=("retained-original-top-hold", "proportional-six-panel-sensitivity"), default="retained-original-top-hold")
    parser.add_argument("--intervals", type=int, default=8)
    parser.add_argument("--beam-size", type=float, default=150.)
    parser.add_argument("--bolt-stiffness", type=float, default=1000.)
    parser.add_argument("--screw-stiffness", type=float, default=1000.)
    parser.add_argument("--clearance", type=float, default=1.5875)
    parser.add_argument("--contact-edge", type=float, default=35.)
    parser.add_argument("--floor-tangent-stiffness", type=float, default=100000.)
    parser.add_argument("--fitting-section", choices=("gross", "net_section_full_leg"), default="gross")
    args = parser.parse_args()
    if args.coupons:
        print(json.dumps({"statics": method_coupons(), "elastic": elastic_method_coupons()}, indent=2))
        return
    if args.out.exists():
        raise FileExistsError("preserve prior numerical evidence; use a new explicit output path")
    if args.elastic:
        report = evaluate_elastic(case_id=args.case, accessory=args.accessory, intervals=args.intervals,
                                  beam_size=args.beam_size, stiffness=args.bolt_stiffness,
                                  screw_stiffness=args.screw_stiffness, clearance=args.clearance,
                                  fitting_section=args.fitting_section, contact_edge=args.contact_edge,
                                  floor_tangent_stiffness=args.floor_tangent_stiffness)
        args.out.write_text(json.dumps(report, separators=(",", ":"), allow_nan=False) + "\n")
        print(json.dumps({"counts": report["counts"], "response": {k: v for k, v in report["response"].items() if k != "q"},
                          "global_residual_force_n": report.get("global_equilibrium_residual_force_n"),
                          "global_residual_moment_nmm": report.get("global_equilibrium_residual_moment_nmm"),
                          "maximum_panel_screw_withdrawal_n": report.get("maximum_panel_screw_withdrawal_n"),
                          "compatible_numerical_mvp_complete": False}, indent=2))
        return
    report = evaluate()
    args.out.write_text(json.dumps(report, separators=(",", ":"), allow_nan=False) + "\n")
    print(json.dumps({"counts": report["counts"], "rank": report["assembled_all_contacts_closed_rank"],
                      "global_support_possible": sum(c["global_support"]["normal_equilibrium_possible"] for c in report["cases"]),
                      "equilibrium_witnesses": sum(c["equilibrium_feasibility_witness"]["feasible"] for c in report["cases"]),
                      "compatible_numerical_mvp_complete": False}, indent=2))


if __name__ == "__main__":
    main()
