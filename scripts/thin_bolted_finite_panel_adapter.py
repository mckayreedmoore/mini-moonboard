"""Sparse finite-panel integration and source-bound constant-world loads.

Consumes existing panel dictionaries; never rebuilds CAD or solves an assembly.
The frozen objective plate proxy supplies all local strain/curvature derivatives.
The retained signed aperture/bevel energy quadrature and explicit generalized
RHS correction remain numerical scenarios, without plywood/product qualification.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass

import numpy as np
from scipy.sparse import coo_matrix, csr_matrix

from scripts import thin_bolted_finite_plate as finite
from scripts import thin_bolted_panel_load_diagnostics as diagnostics
from scripts import thin_bolted_panel_mechanics as method

BASE_PINS = {
    "scripts/thin_bolted_finite_plate.py": "2b0de347d0ef35d08ab7a8d4078fa2e26a50cee6e7c2f708560dd1f0979b9180",
    "scripts/thin_bolted_panel_mechanics.py": "472eef63a8af59367533028008c68e4f7e32780e49891499154ba2950559a3aa",
    "scripts/thin_bolted_panel_load_diagnostics.py": "ff5e0e7b3944e64379181a6b3a1c442b921c197b87d25da3bd20a2d69ec63ebd",
    str(method.INTEGRATED.relative_to(method.ROOT)): method.INTEGRATED_SHA,
}
DERIVATIVES = ((0, 0), (1, 0), (0, 1), (2, 0), (1, 1), (0, 2))


def verify_pins(pins: dict) -> None:
    for path, expected in pins.items():
        method.require(method.sha(method.ROOT / path) == expected,
                       f"finite-panel source differs: {path}")


def reference_measure(panel: dict) -> dict:
    """Retained reference area, with six independently weighted energy measures.

    Full bores remove every measure. The explicit 3 mm conical head scenario
    and kicker bevel remove membrane factors (1-h/t) and bending factors
    (1-(h/t)^3) independently, exactly as the frozen linear K. Mass uses the
    retained bore/bevel measure, normalized to exact source body mass; it does
    not infer a veneer law or a physical countersink mass distribution.
    """
    basis, thickness = panel["basis"], panel["thickness"]
    points, area = basis.quadrature()
    xy, energy, mass = [points], [np.repeat(area[:, None], 6, axis=1)], [area]
    tags = ["rectangle"] * len(area)
    for hole in panel["holes"]:
        center, radius = np.asarray(hole["xy_mm"]), hole["diameter_mm"] / 2
        points, area = method.disk_quadrature(center, radius)
        method.require(np.all(points >= 0) and np.all(points <= [basis.width, basis.height]),
                       "opening crosses rectangular sheet boundary")
        xy.append(points); energy.append(-np.repeat(area[:, None], 6, axis=1)); mass.append(-area)
        tags.extend(["bore"] * len(area))
        if hole["kind"] == "conditional_screw_clearance":
            points, area = method.disk_quadrature(center, 4.5, inner=radius)
            depth = 3 * (4.5 - np.linalg.norm(points - center, axis=1)) / (4.5 - radius)
            factors = np.c_[np.repeat((depth / thickness)[:, None], 3, axis=1),
                            np.repeat((1 - (1 - depth / thickness)**3)[:, None], 3, axis=1)]
            xy.append(points); energy.append(-area[:, None] * factors); mass.append(np.zeros(len(area)))
            tags.extend(["conditional_head_seat"] * len(area))
    points, area, remaining = method.bevel_quadrature(basis, panel["geometry"]["front_height"])
    if len(area):
        factors = np.c_[np.repeat((1 - remaining)[:, None], 3, axis=1),
                        np.repeat((1 - remaining**3)[:, None], 3, axis=1)]
        xy.append(points); energy.append(-area[:, None] * factors); mass.append(-area * (1 - remaining))
        tags.extend(["kicker_bevel"] * len(area))
    xy, energy, mass = np.concatenate(xy), np.concatenate(energy), np.concatenate(mass)
    method.require(mass.sum() > 0, "positive retained mass area required")
    mass /= mass.sum()
    return {"xy_mm": xy, "energy_measure_weights_mm2": energy,
            "mass_weights": mass, "mass_row": mass @ basis.values(xy), "tags": tags}


def _coefficient_indices(nodes: np.ndarray, size: int) -> np.ndarray:
    return np.concatenate([nodes + c * size for c in range(3)])


def _operator(rows: np.ndarray) -> np.ndarray:
    """Point rows [derivative,node] -> [derivative,component] by [component,node]."""
    count = rows.shape[1]
    result = np.zeros((3 * len(rows), 3 * count))
    for c in range(3):
        result[c::3, c * count:(c + 1) * count] = rows
    return result


def _energy_gradient_batch(values, weights, diagonal):
    """Vectorized chain rule of the frozen measures for line evaluations.

    Full tangents still use the frozen local analytic Hessian. This compact
    first-derivative path avoids building unused normal/measure Hessians when
    the caller requests only energy and residual. Directional coupons compare
    it directly with the frozen full tangent path.
    """
    a, b = values[:, 0], values[:, 1]
    cross = np.cross(a, b)
    length = np.linalg.norm(cross, axis=1)
    method.require(np.isfinite(values).all() and np.all(length > 1e-12), "collapsed midsurface metric")
    n = cross / length[:, None]
    dot = lambda x, y: np.einsum("qi,qi->q", x, y)
    measures = np.c_[.5 * (dot(a, a) - 1), .5 * (dot(b, b) - 1), dot(a, b),
                     -dot(n, values[:, 2]), -dot(n, values[:, 4]), -2 * dot(n, values[:, 3])]
    stress = weights * diagonal * measures
    chi = -(stress[:, 3, None] * values[:, 2] + stress[:, 4, None] * values[:, 4]
            + 2 * stress[:, 5, None] * values[:, 3])
    projected = (chi - n * dot(n, chi)[:, None]) / length[:, None]
    gradient = np.empty_like(values)
    gradient[:, 0] = stress[:, 0, None] * a + stress[:, 2, None] * b + np.cross(b, projected)
    gradient[:, 1] = stress[:, 1, None] * b + stress[:, 2, None] * a + np.cross(projected, a)
    gradient[:, 2] = -stress[:, 3, None] * n
    gradient[:, 3] = -2 * stress[:, 5, None] * n
    gradient[:, 4] = -stress[:, 4, None] * n
    return float(.5 * np.sum(measures * stress)), gradient


@dataclass
class _SupportGroup:
    nodes: np.ndarray
    point_indices: np.ndarray
    rows: np.ndarray
    weights: np.ndarray


class FinitePanelAdapter:
    """Existing panel basis/origin, compact local support, optional global map.

    q may be a local [u,v,w] coefficient vector or the full ndof vector.
    response and ports return globally embedded sparse matrices when indices
    are supplied. No panel offsets or original assembly objects are mutated.
    """

    def __init__(self, panel: dict, global_indices=None, ndof=None, source_sha256=None):
        self.panel = dict(panel)
        self.basis, self.geometry = panel["basis"], panel["geometry"]
        self.local_size = 3 * self.basis.size
        self.indices = np.arange(self.local_size) if global_indices is None else np.asarray(global_indices)
        method.require(self.indices.shape == (self.local_size,) and np.issubdtype(self.indices.dtype, np.integer)
                       and np.all(self.indices >= 0) and len(set(self.indices.tolist())) == self.local_size,
                       "distinct nonnegative panel indices required")
        self.indices = self.indices.astype(int)
        self.ndof = int(self.indices.max()) + 1 if ndof is None else int(ndof)
        method.require(self.ndof > self.indices.max(), "global ndof does not contain panel indices")
        self.origin = np.asarray(self.geometry["origin"], dtype=float)
        self.axes = np.asarray(self.geometry["axes"], dtype=float)
        method.require(self.origin.shape == (3,) and self.axes.shape == (3, 3)
                       and np.isfinite([*self.origin, *self.axes.ravel()]).all()
                       and np.max(abs(self.axes.T @ self.axes - np.eye(3))) < 1e-8,
                       "recorded orthogonal midsurface embedding required")
        self.section = finite.APAProxy(panel["thickness"], panel["twist_scale"])
        self.source_sha256 = dict(BASE_PINS)
        for path, digest in (source_sha256 or {}).items():
            method.require(path not in self.source_sha256 or self.source_sha256[path] == digest,
                           "contradictory finite-panel source pin")
            self.source_sha256[path] = digest
        verify_pins(self.source_sha256)
        self.measure = reference_measure(panel)
        self.panel.update(mass_xy=self.measure["xy_mm"], mass_weights=self.measure["mass_weights"],
                          mass_row=self.measure["mass_row"])
        values = np.stack([self.basis.values(self.measure["xy_mm"], dx, dy) for dx, dy in DERIVATIVES], axis=1)
        groups = {}
        for point_index, rows in enumerate(values):
            nodes = tuple(np.flatnonzero(np.any(rows != 0, axis=0)).tolist())
            groups.setdefault(nodes, []).append(point_index)
        self.groups = []
        for nodes, point_indices in groups.items():
            nodes, point_indices = np.asarray(nodes), np.asarray(point_indices)
            self.groups.append(_SupportGroup(nodes, point_indices,
                                              values[point_indices][:, :, nodes],
                                              self.measure["energy_measure_weights_mm2"][point_indices]))

    def local_q(self, q) -> np.ndarray:
        q = np.asarray(q, dtype=float)
        method.require(q.ndim == 1 and np.isfinite(q).all(), "finite panel coefficient vector required")
        if q.shape == (self.local_size,):
            return q
        method.require(q.shape == (self.ndof,), "panel/full coefficient vector length differs")
        return q[self.indices]

    def _embed_gradient(self, local: np.ndarray) -> np.ndarray:
        result = np.zeros(self.ndof); result[self.indices] = local
        return result

    def _embed_matrix(self, local: csr_matrix) -> csr_matrix:
        matrix = local.tocoo()
        return coo_matrix((matrix.data, (self.indices[matrix.row], self.indices[matrix.col])),
                          shape=(self.ndof, self.ndof)).tocsr()

    def _jet_result(self, qindices, position, reference, jacobian, hessian, normal, dn, ddn) -> dict:
        """Embed one compact exact world port without dense panel/global jets."""
        columns = self.indices[qindices]
        rows = np.repeat(np.arange(3), len(columns))
        result = {"position_xyz_mm": position, "reference_position_xyz_mm": reference,
                  "J_csr": coo_matrix((jacobian.ravel(), (rows, np.tile(columns, 3))),
                                       shape=(3, self.ndof)).tocsr(),
                  "normal_xyz": normal,
                  "normal_J_csr": coo_matrix((dn.ravel(), (rows, np.tile(columns, 3))),
                                              shape=(3, self.ndof)).tocsr(),
                  "local_coefficient_indices": qindices, "global_coefficient_indices": columns,
                  "compact_J": jacobian, "compact_normal_J": dn}
        if hessian is None:
            result.update(H_xyz_csr=None, normal_H_xyz_csr=None, compact_H_xyz=None, compact_normal_H_xyz=None)
        else:
            ii, jj = np.repeat(columns, len(columns)), np.tile(columns, len(columns))
            result.update(H_xyz_csr=tuple(coo_matrix((row.ravel(), (ii, jj)), shape=(self.ndof, self.ndof)).tocsr()
                                         for row in hessian),
                          normal_H_xyz_csr=tuple(coo_matrix((row.ravel(), (ii, jj)), shape=(self.ndof, self.ndof)).tocsr()
                                                for row in ddn),
                          compact_H_xyz=hessian, compact_normal_H_xyz=ddn)
        return result

    def response(self, q, tangent=True) -> dict:
        """Objective proxy internal energy/gradient/full tangent on reference area."""
        q = self.local_q(q)
        gradient, energy = np.zeros(self.local_size), 0.
        row_parts, col_parts, value_parts = [], [], []
        diagonal = self.section.section_diagonal
        for group in self.groups:
            indices = _coefficient_indices(group.nodes, self.basis.size)
            compact = q[indices].reshape(3, len(group.nodes))
            derivatives = np.einsum("qdn,cn->qdc", group.rows[:, 1:], compact)
            derivatives[:, 0, 0] += 1; derivatives[:, 1, 1] += 1
            local_gradient, local_hessian = [], []
            if tangent:
                for values, weights in zip(derivatives, group.weights, strict=True):
                    local = finite.strain_curvature_derivatives(values)
                    measures = np.r_[local["strain"], local["curvature"]]
                    stress = weights * diagonal * measures
                    energy += .5 * measures @ stress
                    jac = local["measure_jacobian"]
                    local_gradient.append(jac.T @ stress)
                    local_hessian.append(jac.T @ ((weights * diagonal)[:, None] * jac)
                                         + np.einsum("i,ijk->jk", stress, local["measure_hessian"]))
                local_gradient = np.asarray(local_gradient).reshape(-1, 5, 3)
            else:
                partial_energy, local_gradient = _energy_gradient_batch(derivatives, group.weights, diagonal)
                energy += partial_energy
            gradient[indices] += np.einsum("qdn,qdc->cn", group.rows[:, 1:], local_gradient).ravel()
            if tangent:
                operator = np.stack([_operator(row[1:]) for row in group.rows])
                block = np.einsum("qai,qab,qbj->ij", operator, local_hessian, operator, optimize=True)
                row_parts.append(np.repeat(indices, len(indices))); col_parts.append(np.tile(indices, len(indices)))
                value_parts.append(block.ravel())
        local_h = (coo_matrix((np.concatenate(value_parts), (np.concatenate(row_parts), np.concatenate(col_parts))),
                              shape=(self.local_size, self.local_size)).tocsr() if tangent else None)
        return {"energy_nmm": float(energy), "gradient_n": self._embed_gradient(gradient),
                "hessian_csr": self._embed_matrix(local_h) if tangent else None,
                "local_gradient_n": gradient, "local_hessian_csr": local_h}

    internal = response

    def point_port(self, q, reference_xyz, tangent=True, allow_edge_extension=False) -> dict:
        """Exact r+z*n; optional retained nearest-edge material-tangent extension.

        The origin is the recorded midsurface. A hold point is supplied at its
        actual front+100 mm datum; this function adds no second lever. For the
        original accessory in the center gap only, r_edge+delta_x*r_x+
        delta_y*r_y+z*n_edge is an explicit objective kinematic extension.
        """
        q = self.local_q(q)
        reference = np.asarray(reference_xyz, dtype=float)
        method.require(reference.shape == (3,) and np.isfinite(reference).all(), "finite world port required")
        local = (reference - self.origin) @ self.axes
        xy = np.clip(local[:2], [0., 0.], [self.basis.width, self.basis.height])
        delta = local[:2] - xy
        method.require(np.max(abs(delta)) < 1e-7 or (allow_edge_extension and np.max(abs(delta)) <= 2.),
                       "port outside panel; only explicit two-mm accessory edge extension allowed")
        all_rows = np.stack([self.basis.values(xy[None], dx, dy)[0] for dx, dy in DERIVATIVES])
        nodes = np.flatnonzero(np.any(all_rows != 0, axis=0))
        indices = _coefficient_indices(nodes, self.basis.size)
        compact_q = q[indices]
        rows = all_rows[:, nodes]
        pos_op, first_op = _operator(rows[:1]), _operator(rows[1:3])
        if np.any(delta):
            pos_op += delta[0] * _operator(rows[1:2]) + delta[1] * _operator(rows[2:3])
        derivatives = (first_op @ compact_q).reshape(2, 3)
        derivatives[0, 0] += 1; derivatives[1, 1] += 1
        n, dn, ddn = finite.normal_derivatives(*derivatives)
        normal_j = dn @ first_op
        normal_h = np.einsum("iab,ak,bl->ikl", ddn, first_op, first_op) if tangent else None
        z = local[2]
        position = self.origin + self.axes @ (np.r_[xy + delta, 0.] + pos_op @ compact_q + z * n)
        jac = self.axes @ (pos_op + z * normal_j)
        hessian = np.einsum("ij,jab->iab", self.axes, z * normal_h) if tangent else None
        result = self._jet_result(indices, position, reference, jac, hessian, self.axes @ n,
                                  self.axes @ normal_j,
                                  np.einsum("ij,jab->iab", self.axes, normal_h) if tangent else None)
        result.update(outward_offset_mm=float(z), material_xy_mm=xy, edge_extension_xy_mm=delta,
                      kinematics="midsurface+tangent edge extension+complete signed offset times current outward director")
        return result

    def screw_port(self, q, screw: dict, tangent=True) -> dict:
        """Objective projected-ring extension of retained midpoint/annulus rows.

        p=r_center+n_center*(n_center dot (mean_ring(r)-r_center)). At reference
        J exactly retains midpoint lateral rows and projected9/5mm head-ring
        axial averaging. This is an explicit numerical extension, not a head
        seating/pressure law; no physical screw moment capacity is introduced.
        """
        q = self.local_q(q)
        method.require(screw["panel"] == self.geometry["name"], "screw panel differs")
        center_xy = method.local_xy(screw["origin_xyz_mm"], self.geometry)
        ring, area = method.disk_quadrature(center_xy, 4.5, inner=2.5)
        weights = area / area.sum()
        center_rows = np.stack([self.basis.values(center_xy[None], dx, dy)[0] for dx, dy in DERIVATIVES[:3]])
        mean_row = weights @ self.basis.values(ring)
        nodes = np.flatnonzero(np.any(center_rows != 0, axis=0) | (mean_row != 0))
        indices = _coefficient_indices(nodes, self.basis.size)
        compact_q = q[indices]
        center_op = _operator(center_rows[:1, nodes])
        difference_op = _operator((mean_row - center_rows[0])[None, nodes])
        first_op = _operator(center_rows[1:, nodes])
        derivatives = (first_op @ compact_q).reshape(2, 3)
        derivatives[0, 0] += 1; derivatives[1, 1] += 1
        n, dn, ddn = finite.normal_derivatives(*derivatives)
        nj = dn @ first_op
        nh = np.einsum("iab,ak,bl->ikl", ddn, first_op, first_op) if tangent else None
        center = np.r_[center_xy, 0.] + center_op @ compact_q
        difference = np.r_[weights @ ring - center_xy, 0.] + difference_op @ compact_q
        scalar = n @ difference
        scalar_j = n @ difference_op + difference @ nj
        position = self.origin + self.axes @ (center + n * scalar)
        jac = self.axes @ (center_op + np.outer(n, scalar_j) + scalar * nj)
        if tangent:
            scalar_h = nj.T @ difference_op + difference_op.T @ nj + np.einsum("i,ijk->jk", difference, nh)
            hessian = np.einsum("i,jk->ijk", n, scalar_h) + scalar * nh
            hessian += np.einsum("ij,k->ijk", nj, scalar_j) + np.einsum("j,ik->ijk", scalar_j, nj)
            hessian = np.einsum("ij,jab->iab", self.axes, hessian)
        else:
            hessian = None
        reference = self.origin + self.axes[:, :2] @ center_xy
        result = self._jet_result(indices, position, reference, jac, hessian, self.axes @ n,
                                  self.axes @ nj, np.einsum("ij,jab->iab", self.axes, nh) if tangent else None)
        result.update(axis_id=screw["axis_id"], panel=screw["panel"], receiver=screw["receiver"],
                      center_position_xyz_mm=self.origin + self.axes @ center,
                      ring_mean_position_xyz_mm=self.origin + self.axes @ (center + difference),
                      ring_projected_area_mm2=float(area.sum()), ring_outer_diameter_mm=9., ring_inner_diameter_mm=5.,
                      current_ring_normal_offset_mm=float(scalar), material_xy_mm=center_xy,
                      kinematics="objective projected ring; midpoint lateral/reference annulus axial")
        return result

    def current_rigid_modes(self, q, reference=diagnostics.REFERENCE) -> np.ndarray:
        """Exact coefficient variations under current common world rigid motion."""
        q = self.local_q(q).reshape(3, self.basis.size)
        greville = np.array([np.mean(self.basis.knots[i + 1:i + 4]) for i in range(self.basis.order)])
        x, y = np.meshgrid(greville * self.basis.width, greville * self.basis.height, indexing="ij")
        positions = self.origin + np.c_[x.ravel(), y.ravel()] @ self.axes[:, :2].T + q.T @ self.axes.T
        fields = []
        for c in range(6):
            displacement = np.broadcast_to(np.eye(3)[c], positions.shape) if c < 3 else np.cross(
                np.eye(3)[c - 3], positions - reference)
            fields.append((displacement @ self.axes).T.ravel())
        return np.asarray(fields).T

    def prepare_case_load(self, case: dict, integrated: dict, accessory: str, body_loads: list[dict]):
        return FinitePanelLoads(self, case, integrated, accessory, body_loads)


class FinitePanelLoads:
    """Constant world loads plus the exact retained generalized RHS correction.

    The retained rigid correction remains unchanged. A separately named tiny
    reference-port alignment correction preserves the saved RHS despite the
    recorded axes/datums' finite precision. Both are -delta_f dot q with zero
    Hessian, without invented physical traction/point-force representations.
    Their current rigid-generator wrenches must enter an assembly audit.
    """

    def __init__(self, adapter: FinitePanelAdapter, case, integrated, accessory, body_loads):
        self.adapter, self.accessory = adapter, accessory
        method.require(accessory in ("original_top", "proportional"), "recorded accessory scenario required")
        method.require(integrated == json.loads(method.INTEGRATED.read_text()), "integrated panel load source differs")
        self.loads = [dict(r) for r in body_loads if r["body"] == adapter.geometry["name"]]
        method.require(self.loads and len({r["id"] for r in self.loads}) == len(self.loads), "unique owned body loads required")
        self.case_id = case["id"]
        panel = adapter.panel
        initial, _ = method.panel_case_load(panel, case, integrated, accessory)
        self.uniform_force = sum((np.asarray(r["force_xyz_n"], dtype=float) for r in self.loads
                                  if r["id"].startswith("self-weight/") or
                                  (accessory == "proportional" and r["id"].startswith("accessory/"))), np.zeros(3))
        method.require(np.isfinite(self.uniform_force).all(), "finite uniform gravity required")
        local_force = adapter.axes.T @ self.uniform_force
        self.uniform_generalized = np.concatenate([component * adapter.measure["mass_row"] for component in local_force])
        self.point_loads = [r for r in self.loads if not r["id"].startswith("self-weight/")
                            and not (accessory == "proportional" and r["id"].startswith("accessory/"))]
        for row in self.loads:
            if row["id"].startswith("bolt-weight/"):
                initial += method.point_matrix(panel, row["point_xyz_mm"]).T @ row["force_xyz_n"]
        zero = np.zeros(adapter.local_size)
        reference_force = self.uniform_generalized.copy()
        for row in self.point_loads:
            port = adapter.point_port(zero, row["point_xyz_mm"], tangent=False,
                                      allow_edge_extension=row["id"].startswith("accessory/"))
            reference_force += np.asarray(port["J_csr"].T @ row["force_xyz_n"])[adapter.indices]
        method.require(np.max(abs(reference_force - initial)) < 1e-5,
                       "reference port alignment exceeds retained datum precision scenario")
        self.reference_port_alignment_correction_n = initial - reference_force
        self.uncorrected_reference_force_n = initial
        rigid = diagnostics.rigid_modes(panel)
        desired = diagnostics.load_wrench(self.loads)
        self.retained_rigid_correction_n, self.reference_wrench_correction_n_nmm = diagnostics.rhs_correction(rigid, initial, desired)
        self.correction_n = self.retained_rigid_correction_n + self.reference_port_alignment_correction_n
        self.corrected_reference_force_n = initial + self.retained_rigid_correction_n
        self.source_sha256 = dict(adapter.source_sha256)
        self.metadata = {"case_id": self.case_id, "panel": adapter.geometry["name"], "accessory": accessory,
                         "source_sha256": self.source_sha256, "body_loads": self.loads,
                         "body_loads_sha256": hashlib.sha256(json.dumps(self.loads, sort_keys=True,
                              separators=(",", ":"), allow_nan=False).encode()).hexdigest(),
                         "correction_potential": "-retained generalized RHS correction dot coefficient q; no physical forces assigned",
                         "reference_wrench_correction_n_nmm": self.reference_wrench_correction_n_nmm.tolist(),
                         "reference_rhs_max_abs_difference_n": float(abs(reference_force - initial).max()),
                         "reference_port_alignment_correction_n": self.reference_port_alignment_correction_n.tolist(),
                         "reference_port_alignment_limit": "Fixed generalized term reconciles source-world ports with the old explicitly nominal hold/accessory offsets; it does not move datums or assign physical forces."}

    def external(self, q, tangent=True, reference=diagnostics.REFERENCE) -> dict:
        a = self.adapter
        local_q = a.local_q(q)
        physical_gradient = -self.uniform_generalized.copy()
        potential = float(physical_gradient @ local_q)
        hessian = csr_matrix((a.local_size, a.local_size)) if tangent else None
        mean_xy = a.measure["mass_weights"] @ a.measure["xy_mm"]
        mean_displacement = local_q.reshape(3, a.basis.size) @ a.measure["mass_row"]
        current_mass_center = a.origin + a.axes @ (np.r_[mean_xy, 0.] + mean_displacement)
        physical_wrench = np.r_[self.uniform_force, np.cross(current_mass_center - reference, self.uniform_force)]
        for row in self.point_loads:
            force = np.asarray(row["force_xyz_n"], dtype=float)
            port = a.point_port(local_q, row["point_xyz_mm"], tangent=tangent,
                                allow_edge_extension=row["id"].startswith("accessory/"))
            potential -= force @ (port["position_xyz_mm"] - port["reference_position_xyz_mm"])
            physical_gradient -= np.asarray(port["J_csr"].T @ force)[a.indices]
            physical_wrench += np.r_[force, np.cross(port["position_xyz_mm"] - reference, force)]
            if tangent:
                for component, matrix in zip(force, port["H_xyz_csr"], strict=True):
                    hessian -= component * matrix[a.indices][:, a.indices]
        correction_potential = float(-self.correction_n @ local_q)
        rigid_correction_potential = float(-self.retained_rigid_correction_n @ local_q)
        alignment_potential = float(-self.reference_port_alignment_correction_n @ local_q)
        local_gradient = physical_gradient - self.correction_n
        rigid = a.current_rigid_modes(local_q, reference)
        correction_wrench = rigid.T @ self.correction_n
        generalized_wrench = rigid.T @ -local_gradient
        return {"energy_nmm": potential + correction_potential,
                "physical_load_potential_nmm": potential, "correction_potential_nmm": correction_potential,
                "retained_rigid_correction_potential_nmm": rigid_correction_potential,
                "reference_port_alignment_potential_nmm": alignment_potential,
                "gradient_n": a._embed_gradient(local_gradient),
                "hessian_csr": a._embed_matrix(hessian) if tangent else None,
                "local_gradient_n": local_gradient, "local_hessian_csr": hessian,
                "correction_generalized_force_n": self.correction_n.copy(),
                "retained_rigid_correction_generalized_force_n": self.retained_rigid_correction_n.copy(),
                "reference_port_alignment_generalized_force_n": self.reference_port_alignment_correction_n.copy(),
                "physical_applied_wrench_n_nmm": physical_wrench,
                "generalized_correction_wrench_n_nmm": correction_wrench,
                "retained_rigid_correction_wrench_n_nmm": rigid.T @ self.retained_rigid_correction_n,
                "reference_port_alignment_wrench_n_nmm": rigid.T @ self.reference_port_alignment_correction_n,
                "total_generalized_applied_wrench_n_nmm": generalized_wrench,
                "wrench_residual_n_nmm": generalized_wrench - physical_wrench - correction_wrench,
                "wrench_reference_xyz_mm": np.asarray(reference)}


def prepare_adapters(panels: dict, panel_offsets: dict, ndof: int, source_sha256=None) -> dict:
    """Map existing six panel blocks into an unchanged or enlarged global state."""
    method.require(set(panels) == set(panel_offsets) == set(method.PANELS), "six matching panel blocks required")
    result = {name: FinitePanelAdapter(panel, panel_offsets[name], ndof, source_sha256)
              for name, panel in panels.items()}
    all_indices = np.concatenate([a.indices for a in result.values()])
    method.require(len(set(all_indices.tolist())) == len(all_indices), "panel global indices overlap")
    return result
