"""Objective finite-motion plate proxy and exact Kirchhoff point ports.

Flat reference coordinates are physical material-axis distances in mm.
The conditional APA section targets define a reference-area quadratic energy
in exact midsurface Green strains and covariant curvature changes. This is
not a qualified plywood laminate or an exact through-thickness material law.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from scripts.thin_bolted_panel_mechanics import CAT, SheetBasis, material, require


def normal_derivatives(a: np.ndarray, b: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Unit normal and analytic first/second derivatives in [rx,ry]."""
    a, b = np.asarray(a, dtype=float), np.asarray(b, dtype=float)
    require(a.shape == b.shape == (3,) and np.isfinite([a, b]).all(), "finite three-vector tangents required")
    cross = np.cross(a, b)
    length = np.linalg.norm(cross)
    require(length > 1e-12, "collapsed midsurface metric")
    n = cross / length
    dc = np.column_stack([*[np.cross(e, b) for e in np.eye(3)],
                          *[np.cross(a, e) for e in np.eye(3)]])
    ddc = np.zeros((3, 6, 6))
    for i, ei in enumerate(np.eye(3)):
        for j, ej in enumerate(np.eye(3)):
            ddc[:, i, 3 + j] = ddc[:, 3 + j, i] = np.cross(ei, ej)
    dn_dc = (np.eye(3) - np.outer(n, n)) / length
    ddn_dc = np.empty((3, 3, 3))
    identity = np.eye(3)
    for i in range(3):
        for j in range(3):
            for k in range(3):
                ddn_dc[i, j, k] = -(identity[i, j] * n[k] + identity[i, k] * n[j]
                                    + identity[j, k] * n[i] - 3 * n[i] * n[j] * n[k]) / length**2
    dn = dn_dc @ dc
    ddn = np.einsum("ja,ijk,kb->iab", dc, ddn_dc, dc) + np.einsum("ij,jab->iab", dn_dc, ddc)
    return n, dn, ddn


def strain_curvature_derivatives(derivatives: np.ndarray) -> dict:
    """Measures and derivatives in [rx,ry,rxx,rxy,ryy], each three-vector.

    Measures are [Exx,Eyy,engineering_gamma_xy] and
    [-n.rxx,-n.ryy,-2*n.rxy]. Curvatures stay covariant in flat reference
    material coordinates; dividing by current tangent lengths would change
    the stated reference-area energy and is deliberately not performed.
    """
    values = np.asarray(derivatives, dtype=float)
    require(values.shape == (5, 3) and np.isfinite(values).all(), "five finite surface derivative vectors required")
    a, b, *_ = values
    n, dn, ddn = normal_derivatives(a, b)
    strain = np.array([.5 * (a @ a - 1), .5 * (b @ b - 1), a @ b])
    jacobian = np.zeros((6, 15))
    hessian = np.zeros((6, 15, 15))
    jacobian[0, :3], jacobian[1, 3:6] = a, b
    jacobian[2, :3], jacobian[2, 3:6] = b, a
    hessian[0, :3, :3] = np.eye(3)
    hessian[1, 3:6, 3:6] = np.eye(3)
    hessian[2, :3, 3:6] = hessian[2, 3:6, :3] = np.eye(3)
    curvature = []
    for row, index, factor in ((3, 2, -1.), (4, 4, -1.), (5, 3, -2.)):
        second = values[index]
        block = slice(3 * index, 3 * index + 3)
        curvature.append(factor * (n @ second))
        jacobian[row, :6], jacobian[row, block] = factor * (second @ dn), factor * n
        hessian[row, :6, :6] = factor * np.einsum("i,iab->ab", second, ddn)
        hessian[row, :6, block] = factor * dn.T
        hessian[row, block, :6] = factor * dn
    return {"strain": strain, "curvature": np.asarray(curvature), "normal": n,
            "measure_jacobian": jacobian, "measure_hessian": hessian,
            "normal_jacobian": dn, "normal_hessian": ddn,
            "surface_area_ratio": float(np.linalg.norm(np.cross(a, b)))}


@dataclass(frozen=True)
class APAProxy:
    thickness_mm: float = CAT
    twist_scale: float = 1.

    @property
    def section_diagonal(self) -> np.ndarray:
        require(np.isfinite([self.thickness_mm, self.twist_scale]).all()
                and self.thickness_mm > 0 and self.twist_scale > 0, "positive finite section scenarios required")
        ex, ey = material.APA_EA[::-1]
        bx, by = material.APA_EI[::-1]
        return np.array([ex, ey, material.APA_GA, bx, by,
                         material.APA_GA * self.thickness_mm**2 / 12 * self.twist_scale])

    def local_energy(self, derivatives: np.ndarray) -> dict:
        """Reference-area energy, exact analytic gradient and full tangent.

        The tangent includes material and geometric terms; it need not be
        positive definite away from an unloaded reference configuration.
        """
        result = strain_curvature_derivatives(derivatives)
        measures = np.r_[result["strain"], result["curvature"]]
        diagonal = self.section_diagonal
        stress = diagonal * measures
        jacobian = result["measure_jacobian"]
        result.update({"energy_per_reference_area_n_per_mm": float(.5 * measures @ stress),
                       "conjugate_resultants_n_per_mm_nmm_per_mm": stress,
                       "local_gradient": jacobian.T @ stress,
                       "local_hessian": jacobian.T @ (diagonal[:, None] * jacobian)
                                        + np.einsum("i,ijk->jk", stress, result["measure_hessian"])})
        return result


@dataclass
class FinitePlate:
    basis: SheetBasis
    section: APAProxy = APAProxy()

    def derivative_operator(self, point: np.ndarray) -> np.ndarray:
        """15 by 3N map from coefficient increments to surface derivatives."""
        rows = [self.basis.values(np.asarray(point).reshape(1, 2), dx, dy)[0]
                for dx, dy in ((1, 0), (0, 1), (2, 0), (1, 1), (0, 2))]
        operator = np.zeros((15, 3 * self.basis.size))
        for derivative, row in enumerate(rows):
            for component in range(3):
                operator[3 * derivative + component, component * self.basis.size:(component + 1) * self.basis.size] = row
        return operator

    def surface_derivatives(self, q: np.ndarray, point: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        q = np.asarray(q, dtype=float)
        require(q.shape == (3 * self.basis.size,) and np.isfinite(q).all(), "finite coefficient vector required")
        operator = self.derivative_operator(point)
        derivatives = (operator @ q).reshape(5, 3)
        derivatives[0, 0] += 1.
        derivatives[1, 1] += 1.
        return derivatives, operator

    def point_energy(self, q: np.ndarray, point: np.ndarray) -> dict:
        """Energy density with coefficient gradient/tangent at one material point."""
        derivatives, operator = self.surface_derivatives(q, point)
        result = self.section.local_energy(derivatives)
        result.update({"coefficient_gradient": operator.T @ result["local_gradient"],
                       "coefficient_hessian": operator.T @ result["local_hessian"] @ operator})
        return result

    def energy(self, q: np.ndarray, points: np.ndarray, reference_area_weights: np.ndarray) -> dict:
        """Caller-supplied quadrature integration; no candidate assembly/solve.

        Positive/negative weights can reproduce retained aperture subtraction;
        no integration convergence or free hole-boundary qualification follows.
        """
        points, weights = np.asarray(points, dtype=float), np.asarray(reference_area_weights, dtype=float)
        require(points.ndim == 2 and points.shape[1] == 2 and weights.shape == (len(points),)
                and np.isfinite(weights).all(), "finite point/reference-area quadrature required")
        gradient = np.zeros(3 * self.basis.size)
        tangent = np.zeros((len(gradient), len(gradient)))
        energy = 0.
        for point, weight in zip(points, weights, strict=True):
            local = self.point_energy(q, point)
            energy += weight * local["energy_per_reference_area_n_per_mm"]
            gradient += weight * local["coefficient_gradient"]
            tangent += weight * local["coefficient_hessian"]
        return {"energy_nmm": float(energy), "gradient_n": gradient, "hessian_n_per_mm": tangent}

    def point_port(self, q: np.ndarray, point: np.ndarray, z_mm: float = 0., *,
                   origin_xyz_mm=None, axes_columns_xyz=None) -> dict:
        """Exact world position/Jacobian/Hessian of r(x,y)+z*n(x,y).

        z is the complete signed offset from the midsurface. A front-face
        hold point uses t/2+100 mm once; no lever is added inside this API.
        Orthogonal embeddings may have either handedness: local +z always
        maps to the caller's recorded outward director, including left-handed
        panel frames. The reference port is origin+A@[x,y,z].
        """
        require(np.isfinite(z_mm), "finite through-thickness/lever offset required")
        point = np.asarray(point, dtype=float)
        origin = np.zeros(3) if origin_xyz_mm is None else np.asarray(origin_xyz_mm, dtype=float)
        axes = np.eye(3) if axes_columns_xyz is None else np.asarray(axes_columns_xyz, dtype=float)
        require(origin.shape == (3,) and axes.shape == (3, 3) and np.isfinite([*origin, *axes.ravel()]).all()
                and np.max(abs(axes.T @ axes - np.eye(3))) < 1e-8, "orthogonal finite world embedding required")
        derivatives, operator = self.surface_derivatives(q, point)
        n, dn, ddn = normal_derivatives(*derivatives[:2])
        values = self.basis.values(point.reshape(1, 2))[0]
        position_operator = np.zeros((3, len(q)))
        for component in range(3):
            position_operator[component, component * self.basis.size:(component + 1) * self.basis.size] = values
        midsurface = np.r_[point, 0.] + position_operator @ q
        position = origin + axes @ (midsurface + z_mm * n)
        jacobian = axes @ (position_operator + z_mm * dn @ operator[:6])
        hessian = z_mm * np.einsum("ij,jab,ak,bl->ikl", axes, ddn, operator[:6], operator[:6])
        return {"position_xyz_mm": position, "reference_position_xyz_mm": origin + axes @ np.r_[point, z_mm],
                "normal_xyz": axes @ n, "jacobian_xyz_per_coefficient": jacobian,
                "hessian_xyz_per_coefficient_squared": hessian}
