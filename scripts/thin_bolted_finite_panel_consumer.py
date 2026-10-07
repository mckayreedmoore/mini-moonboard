"""Admitted finite-state panel diagnostics from saved JSON coefficients/actions.

No CAD, reference quadrature, stiffness matrix, global assembly or solve.
Only the NEW finite current support/load/wrench gate admits a field. Generic
APA/NDS comparisons remain conditional proxy diagnostics, not Hillman or local
hole/seat/hold capacity qualification.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib
import json
import re
from pathlib import Path

import numpy as np

from scripts import thin_bolted_finite_panel_adapter as adapter
from scripts import thin_bolted_finite_plate as finite
from scripts import thin_bolted_panel_coupled as references
from scripts import thin_bolted_panel_mechanics as method

ADMISSION_MODULE = "scripts.thin_bolted_finite_state_audit"
ADMISSION_PATH = method.ROOT / "scripts/thin_bolted_finite_state_audit.py"
ADMISSION_KEY = "independent_finite_current_support_load_and_equilibrium_checks_pass"
FIELD_SCHEMA = "thin_bolted_finite_frame_response/v1"
MAP_ORDER = "u,v,outward_w;x-major tensor cubic spline"
CORRECTION_KINDS = {"retained_rigid_RHS", "reference_port_alignment"}
BASE_PINS = {**adapter.BASE_PINS,
    "scripts/thin_bolted_finite_frame.py": "68f711549da9e6b52c60db4e4df78235ba8105084ded0d81c9a3430cf5973588",
    "scripts/thin_bolted_finite_panel_adapter.py": "c0e2534158d10ca49e6e1ee20db7b8a7e72b746b49618a18bf5ab08a9526064b",
    "scripts/thin_bolted_panel_coupled.py": "abd6da1911ec79ec25b57fc2a5cc20b9e687057a15b6df2f5e8fb292a42c6bd0",
    "fea/current_response_materials.py": "72af0456272d91282928014d8fde557d347e36df6b7bdf23bcc41ef923d0d135",
    str(method.LAYOUT.relative_to(method.ROOT)): method.LAYOUT_SHA,
    str(method.APA_PDF.relative_to(method.ROOT)): method.APA_SHA,
    str(method.NDS_PDF.relative_to(method.ROOT)): method.NDS_SHA,
    str(method.LEGACY_METHOD.relative_to(method.ROOT)): "7c8aadbc15fe3fca1932c9bf32ee1029bed7e4ac10ccca74368f95c2bf80bde8",
    str(references.ASSESSMENT.relative_to(method.ROOT)): references.ASSESSMENT_SHA,
    str(references.DATUMS.relative_to(method.ROOT)): references.DATUMS_SHA}


class MappedFinitePanel(adapter.FinitePanelAdapter):
    """Replay only frozen port/director/rigid-mode methods on a saved panel map.

    This intentionally omits reference measures, support groups and K. Calling
    an internal response or load-preparation method is rejected. The parent
    admission gate authenticates the full map and source geometry independently.
    """

    def __init__(self, name, mapping, ndof, geometry_source, holes, section=None):
        method.require(mapping["kind"] == "panel" and mapping["coefficient_order"] == MAP_ORDER,
                       "finite panel kind or coefficient order differs")
        order = mapping["basis_order"]
        method.require(isinstance(order, int) and order >= 4, "finite cubic basis order required")
        self.basis = method.SheetBasis(mapping["basis_width_mm"], mapping["basis_height_mm"], order - 3)
        method.require(np.array_equal(self.basis.knots, mapping["basis_knots_normalized"]),
                       "finite panel knots differ")
        self.local_size = 3 * self.basis.size
        self.indices = np.asarray(mapping["global_dof_indices"])
        self.ndof = ndof
        method.require(isinstance(ndof, int) and self.indices.shape == (self.local_size,)
                       and np.issubdtype(self.indices.dtype, np.integer) and np.all(self.indices >= 0)
                       and np.all(self.indices < ndof) and len(set(self.indices.tolist())) == self.local_size,
                       "finite panel global indices differ")
        self.origin = np.asarray(mapping["origin_xyz_mm"], dtype=float)
        self.axes = np.asarray(mapping["axes_columns_xyz"], dtype=float)
        method.require(self.origin.shape == (3,) and self.axes.shape == (3, 3)
                       and np.isfinite([*self.origin, *self.axes.ravel()]).all()
                       and np.linalg.norm(self.axes.T @ self.axes - np.eye(3)) < 1e-8,
                       "finite panel origin/axes differ")
        thickness, twist = section if section is not None else (mapping["thickness_mm"], mapping["twist_scale"])
        method.require(abs(thickness - method.CAT) < 1e-9,
                       "consumer's retained CAT23/32 references do not qualify another thickness")
        self.section = finite.APAProxy(thickness, twist)
        self.source_sha256 = dict(BASE_PINS)
        self.geometry = {"name": name, "origin": self.origin, "axes": self.axes,
                         "inward": -self.axes[:, 2], "front_height": geometry_source["front_height_mm"]}
        self.panel = {"basis": self.basis, "geometry": self.geometry, "holes": holes,
                      "thickness": thickness, "twist_scale": twist,
                      "support_bounds": geometry_source.get("support_footprints", [])}

    def response(self, *args, **kwargs):
        raise ValueError("finite consumer cannot assemble panel stiffness or solve a response")

    internal = response

    def prepare_case_load(self, *args, **kwargs):
        raise ValueError("finite consumer uses admitted saved corrections, without reconstructing loads")


def finite_fields(panel: MappedFinitePanel, xy, q) -> dict:
    """Green/covariant measures and variational force per reference width.

    For local reference-area psi(r_x,r_y,r_xx,r_xy,r_yy), let G be its gradient.
    T_x=G_x-d_x(G_xx)-.5*d_y(G_xy), and similarly T_y. The symmetric split of
    mixed second derivatives recovers the retained linear Q. n dot T is a
    reference-width variational transverse-force diagnostic, not a qualified
    through-thickness rolling stress or an exact local hole-edge resultant.
    """
    points = np.asarray(xy, dtype=float).reshape(-1, 2)
    local_q = panel.local_q(q).reshape(3, panel.basis.size)
    rows = {(dx, dy): panel.basis.values(points, dx, dy)
            for dx, dy in ((1, 0), (0, 1), (2, 0), (1, 1), (0, 2), (3, 0), (2, 1), (1, 2), (0, 3))}
    derivatives = np.stack([rows[d] @ local_q.T for d in ((1, 0), (0, 1), (2, 0), (1, 1), (0, 2))], axis=1)
    derivatives[:, 0, 0] += 1; derivatives[:, 1, 1] += 1
    derivative_x = np.stack([rows[d] @ local_q.T for d in ((2, 0), (1, 1), (3, 0), (2, 1), (1, 2))], axis=1)
    derivative_y = np.stack([rows[d] @ local_q.T for d in ((1, 1), (0, 2), (2, 1), (1, 2), (0, 3))], axis=1)
    fields = {k: [] for k in ("green_strain", "covariant_curvature_per_mm", "normal_local",
        "surface_area_ratio", "section_conjugate_resultants", "variational_force_x_local_n_per_mm",
        "variational_force_y_local_n_per_mm", "variational_transverse_x_n_per_mm",
        "variational_transverse_y_n_per_mm", "principal_green_strains", "principal_curvatures_per_mm",
        "section_energy_per_reference_area_n_per_mm")}
    for d, dx, dy in zip(derivatives, derivative_x, derivative_y, strict=True):
        local = panel.section.local_energy(d)
        gradient = local["local_gradient"].reshape(5, 3)
        gx = (local["local_hessian"] @ dx.ravel()).reshape(5, 3)
        gy = (local["local_hessian"] @ dy.ravel()).reshape(5, 3)
        tx, ty = gradient[0] - gx[2] - .5 * gy[3], gradient[1] - gy[4] - .5 * gx[3]
        n = local["normal"]
        metric = d[:2] @ d[:2].T
        second_form = np.array([[n @ d[2], n @ d[3]], [n @ d[3], n @ d[4]]])
        curvatures = np.linalg.eigvals(np.linalg.solve(metric, second_form))
        method.require(np.max(abs(curvatures.imag)) < 1e-8, "finite curvature eigenvalues are not real")
        values = {"green_strain": local["strain"], "covariant_curvature_per_mm": local["curvature"],
            "normal_local": n, "surface_area_ratio": local["surface_area_ratio"],
            "section_conjugate_resultants": local["conjugate_resultants_n_per_mm_nmm_per_mm"],
            "variational_force_x_local_n_per_mm": tx, "variational_force_y_local_n_per_mm": ty,
            "variational_transverse_x_n_per_mm": n @ tx, "variational_transverse_y_n_per_mm": n @ ty,
            "principal_green_strains": np.linalg.eigvalsh(.5 * (metric - np.eye(2))),
            "principal_curvatures_per_mm": np.sort(curvatures.real),
            "section_energy_per_reference_area_n_per_mm": local["energy_per_reference_area_n_per_mm"]}
        for key, value in values.items():
            fields[key].append(value)
    return {key: np.asarray(value) for key, value in fields.items()}


def reconstruct_load_corrections(panel: MappedFinitePanel, case_id, accessory, integrated, source_load_rows) -> dict:
    """Source-vector check for an independent gate, without energy/K/CAD.

    This optional admission utility reconstructs only the retained MASS
    quadrature, which the consumer's section/action evaluator does not need.
    Callers independently authenticate source load rows and integrated JSON.
    Source points must be the saved original world datums, not current points.
    """
    adapter.verify_pins(BASE_PINS)
    adapter.diagnostics.mass_only_quadrature(panel.panel)
    panel.measure = {"mass_row": panel.panel["mass_row"], "xy_mm": panel.panel["mass_xy"],
                     "mass_weights": panel.panel["mass_weights"]}
    case = next(row for row in method.load_cases(integrated)
                if row["id"] == ("permanent" if case_id == "gravity-only" else case_id))
    loads = adapter.FinitePanelLoads(panel, case, integrated, accessory, source_load_rows)
    return {"retained_rigid_RHS": loads.retained_rigid_correction_n,
            "reference_port_alignment": loads.reference_port_alignment_correction_n,
            "mass_coefficient_row": panel.measure["mass_row"],
            "mass_reference_xy_mm": panel.measure["mass_weights"] @ panel.measure["xy_mm"],
            "uncorrected_reference_force_n": loads.uncorrected_reference_force_n,
            "corrected_reference_force_n": loads.corrected_reference_force_n}


def current_screw_diagnostics(panel, q, source, action) -> dict:
    """Same-state signed forces in a current orthonormal material tangent frame."""
    method.require(action["first"] == source["panel"] == panel.geometry["name"]
                   and action["second"] == source["receiver"] and action["director_owner"] == source["panel"]
                   and action["first_port_kind"] == "projected_ring" and action["interaction_enabled"],
                   "finite screw ownership/port kind differs")
    port = panel.screw_port(q, source, False)
    saved_n, force = np.asarray(action["current_director_xyz"]), np.asarray(action["force_on_second_xyz_n"])
    method.require(saved_n.shape == force.shape == (3,) and np.isfinite([saved_n, force]).all()
                   and abs(np.linalg.norm(saved_n) - 1) < 1e-8,
                   "finite current director/force differs")
    method.require(np.max(abs(port["position_xyz_mm"] - action["point_on_first_xyz_mm"])) < 2e-6
                   and np.max(abs(port["normal_xyz"] - saved_n)) < 2e-8
                   and np.max(abs(force + action["force_on_first_xyz_n"])) < 2e-6,
                   "finite screw current position/director/opposed force differs")
    n = saved_n / np.linalg.norm(saved_n)
    xy = port["material_xy_mm"]
    coefficients = panel.local_q(q).reshape(3, panel.basis.size)
    rx = panel.axes @ (np.array([1., 0., 0.]) + coefficients @ panel.basis.values(xy[None], 1)[0])
    ry = panel.axes @ (np.array([0., 1., 0.]) + coefficients @ panel.basis.values(xy[None], 0, 1)[0])
    ex = rx - n * (rx @ n); ex /= np.linalg.norm(ex)
    ey = np.cross(n, ex)
    if ey @ ry < 0:
        ey *= -1
    signed_tension = float(force @ n)
    tolerance = 2e-6 + 2e-8 * np.linalg.norm(force)
    method.require(signed_tension >= -tolerance
                   and abs(signed_tension - action["axial_scalar_force_n"]) <= tolerance,
                   "finite force projection differs from same-state tensile spring scalar")
    tension = max(0., signed_tension)
    lateral = force - signed_tension * n
    local_force = np.array([tension, force @ ex, force @ ey])
    method.require(abs(np.linalg.norm(local_force[1:]) - np.linalg.norm(lateral)) < tolerance,
                   "finite material tangent projections differ")
    row = {"axis_id": source["axis_id"], "panel": source["panel"], "receiver": source["receiver"],
        **{k: action[k] for k in ("state_id", "case_id", "accessory_placement")},
        "current_point_on_panel_xyz_mm": action["point_on_first_xyz_mm"],
        "current_point_on_receiver_xyz_mm": action["point_on_second_xyz_mm"],
        "force_on_receiver_xyz_n": force.tolist(), "current_outward_unit_director_xyz": n.tolist(),
        "current_material_x_unit_tangent_xyz": ex.tolist(), "current_upslope_unit_tangent_xyz": ey.tolist(),
        "signed_current_axial_n": signed_tension, "withdrawal_n": tension,
        "lateral_n": float(np.linalg.norm(lateral)), "local_force_n": local_force.tolist(),
        "moment_on_panel_at_current_point_xyz_nmm": action["moment_on_first_at_current_point_xyz_nmm"],
        "director_couple_is_a_screw_or_head_capacity": False}
    return references.screw_references(row, panel.section.thickness_mm)


def correction_diagnostics(panel, q, rows) -> dict:
    method.require(len(rows) == 2 and {r["kind"] for r in rows} == CORRECTION_KINDS,
                   "two unique finite generalized corrections required for each panel")
    local_q = panel.local_q(q)
    records = []
    for row in rows:
        force = np.asarray(row["local_generalized_force_n"], dtype=float)
        method.require(row["panel"] == panel.geometry["name"] and force.shape == (panel.local_size,)
                       and np.isfinite(force).all() and np.array_equal(row["global_coefficient_indices"], panel.indices)
                       and row["physical_point_forces_or_pressure_representation"] is False,
                       "finite generalized correction basis/interpretation differs")
        reference = np.asarray(row["wrench_reference_xyz_mm"])
        wrench = panel.current_rigid_modes(q, reference).T @ force
        method.require(np.max(abs(wrench - row["current_equivalent_rigid_wrench_n_nmm"])) < 2e-7,
                       "finite generalized correction current wrench differs")
        potential = float(-force @ local_q)
        if "potential_nmm" in row:
            method.require(abs(potential - row["potential_nmm"]) < 1e-8,
                           "finite generalized correction potential differs")
        records.append({**row, "potential_nmm": potential,
                        "generalized_force_norm_n": float(np.linalg.norm(force)),
                        "current_force_wrench_norm_n": float(np.linalg.norm(wrench[:3])),
                        "current_moment_wrench_norm_nmm": float(np.linalg.norm(wrench[3:]))})
    return {"separate_generalized_terms": records, "sum_potential_nmm": sum(r["potential_nmm"] for r in records),
            "physical_forces_assigned": False}


def section_diagnostics(panel, q, samples=41) -> dict:
    b = panel.basis
    x, y = np.meshgrid(np.linspace(0, b.width, samples), np.linspace(0, b.height, samples), indexing="ij")
    points = np.c_[x.ravel(), y.ravel()]
    keep = points[:, 1] <= panel.geometry["front_height"] + 1e-8
    for hole in panel.panel["holes"]:
        keep &= np.linalg.norm(points - hole["xy_mm"], axis=1) > hole["diameter_mm"] / 2
        if hole["kind"] == "conditional_screw_clearance":
            keep &= np.linalg.norm(points - hole["xy_mm"], axis=1) > 4.5
    points = points[keep]
    method.require(len(points) > 0, "finite intact section sample set empty")
    fields = finite_fields(panel, points, q)
    resultants = fields["section_conjugate_resultants"]
    convert = method.N_PER_LBF / 304.8
    values = {"bending_x": resultants[:, 3], "bending_upslope": resultants[:, 4],
              "variational_transverse_x": fields["variational_transverse_x_n_per_mm"],
              "variational_transverse_upslope": fields["variational_transverse_y_n_per_mm"],
              "membrane_x": resultants[:, 0], "membrane_upslope": resultants[:, 1]}
    denominators = {"bending_x": np.full(len(points), 775 * 25.4 * convert),
        "bending_upslope": np.full(len(points), 455 * 25.4 * convert),
        "variational_transverse_x": np.full(len(points), 350 * convert),
        "variational_transverse_upslope": np.full(len(points), 350 * convert),
        "membrane_x": np.where(resultants[:, 0] >= 0, 5100, 4800) * convert,
        "membrane_upslope": np.where(resultants[:, 1] >= 0, 3400, 2900) * convert}
    witnesses = {}
    for key, vector in values.items():
        indices = np.abs(vector) / denominators[key]
        j = int(indices.argmax())
        witnesses[key] = {"xy_mm": points[j].tolist(), "signed_reference_resultant": float(vector[j]),
            "linear_APA_target_per_reference_mm_width_CD1": float(denominators[key][j]),
            "conditional_reference_constitutive_index_CD1": float(indices[j]),
            "conditional_reference_constitutive_index_CD1p6": float(indices[j] / 1.6),
            "simultaneous_green_strain": fields["green_strain"][j].tolist(),
            "simultaneous_covariant_curvature_per_mm": fields["covariant_curvature_per_mm"][j].tolist(),
            "simultaneous_all_section_conjugate_resultants": resultants[j].tolist(),
            "simultaneous_surface_area_ratio": float(fields["surface_area_ratio"][j])}
    strain_norm = np.max(abs(fields["principal_green_strains"]), axis=1)
    curviness = panel.section.thickness_mm * np.max(abs(fields["principal_curvatures_per_mm"]), axis=1)
    js, jc = int(strain_norm.argmax()), int(curviness.argmax())
    return {"sample_count_per_axis": samples, "intact_full_thickness_sample_count": len(points),
        "excluded_bores_conditional_seats_and_kicker_bevel": True, "section_witnesses": witnesses,
        "maximum_abs_principal_green_strain": float(strain_norm[js]), "strain_witness_xy_mm": points[js].tolist(),
        "maximum_thickness_times_abs_principal_curvature": float(curviness[jc]), "curviness_witness_xy_mm": points[jc].tolist(),
        "finite_plywood_constitutive_or_local_hole_capacity_qualified": False,
        "sampling_or_response_convergence_established": False,
        "status": "FINITE_PROXY_REFERENCE_SECTION_DIAGNOSTIC"}


def validate_admission_receipt(admission, state, field_sha, admission_sha256):
    method.require(isinstance(admission, dict) and admission.get(ADMISSION_KEY) is True,
                   "NEW finite support/load/wrench admission failed")
    method.require(admission.get("field_sha256") == field_sha
                   and all(admission.get(k) == state[k] for k in ("state_id", "case_id", "accessory_placement")),
                   "finite admission receipt belongs to another field/state/case")
    method.require(admission.get("source_sha256", {}).get(str(ADMISSION_PATH.relative_to(method.ROOT))) == admission_sha256,
                   "finite admission receipt carries another audit-source identity")


def evaluate(field_path: Path, samples=41, *, admission_sha256=None) -> dict:
    method.require(isinstance(samples, int) and samples >= 4, "at least four samples per axis required")
    field_path = Path(field_path).resolve()
    payload = field_path.read_bytes()
    field_sha = hashlib.sha256(payload).hexdigest()
    state = json.loads(payload)
    method.require(state.get("schema") == FIELD_SCHEMA, "NEW finite field schema required; reference state rejected")
    method.require(isinstance(admission_sha256, str) and re.fullmatch("[0-9a-f]{64}", admission_sha256) is not None,
                   "explicit frozen NEW finite admission SHA256 required")
    method.require(method.sha(ADMISSION_PATH) == admission_sha256, "NEW finite admission helper changed")
    audit_module = importlib.import_module(ADMISSION_MODULE)
    audit_path = Path(audit_module.__file__).resolve()
    method.require(audit_path == ADMISSION_PATH.resolve(), "NEW finite admission module path differs")
    adapter.verify_pins(BASE_PINS)
    admission = audit_module.audit_finite_state(payload)
    validate_admission_receipt(admission, state, field_sha, admission_sha256)
    adapter.verify_pins(state["source_sha256"])
    method.require(not any(state["release"].values()), "finite field cannot authorize release")
    mapping, q = state["finite_kinematic_map"], np.asarray(state["response"]["q"], dtype=float)
    method.require(q.shape == (mapping["ndof"],) and np.isfinite(q).all()
                   and set(mapping["panels"]) == set(method.PANELS), "finite field q/six-panel map differs")
    assessment = json.loads(references.ASSESSMENT.read_text())
    source_geometry = {r["panel"]: r for r in assessment["panel_geometry"]}
    integrated, layout = json.loads(method.INTEGRATED.read_text()), json.loads(method.LAYOUT.read_text())
    datum_rows = json.loads(references.DATUMS.read_text())
    panels = {}
    for name in method.PANELS:
        row = mapping["panels"][name]
        datum, geometry = datum_rows[name], source_geometry[name]
        method.require(np.array_equal(row["origin_xyz_mm"], datum["origin_xyz_mm"])
                       and np.array_equal(row["axes_columns_xyz"], datum["local_axes_columns_xyz"])
                       and abs(row["basis_width_mm"] - geometry["width_mm"]) < 1e-8
                       and abs(row["basis_height_mm"] - geometry["height_mm"]) < 1e-8,
                       "finite panel geometry differs from frozen reviewed datums")
        g = {"origin": np.asarray(row["origin_xyz_mm"]), "axes": np.asarray(row["axes_columns_xyz"])}
        holes = [{**r, "xy_mm": method.local_xy(r["start_xyz_mm"], g).tolist()}
                 for r in integrated["panel_machining"]["features"] if r["panel"] == name]
        panels[name] = MappedFinitePanel(name, row, mapping["ndof"], geometry, holes)
    all_indices = np.concatenate([p.indices for p in panels.values()])
    method.require(len(set(all_indices.tolist())) == len(all_indices), "finite panel blocks overlap")
    expected = {r["axis_id"]: r for r in layout["screw_axes"]}
    actions = [r for r in state["finite_interaction_actions"] if r["kind"] == "panel_screw"]
    method.require(len(actions) == 66 and {r["id"] for r in actions} == set(expected),
                   "all66 distinct same-state finite screw actions required")
    screws = []
    for row in [*actions, *state["panel_generalized_load_corrections"]]:
        method.require(all(row[k] == state[k] for k in ("state_id", "case_id", "accessory_placement")),
                       "finite case/state/accessory identities mixed")
    for action in actions:
        source = expected[action["id"]]
        screws.append(current_screw_diagnostics(panels[source["panel"]], q, source, action))
    corrections = state["panel_generalized_load_corrections"]
    method.require(len(corrections) == 12, "two corrections for each of six panels required")
    rows = []
    for name, panel in panels.items():
        owned = [r for r in screws if r["panel"] == name]
        rows.append({"panel": name, "state_id": state["state_id"],
            "same_state_head_witness": max(owned, key=lambda r: r["withdrawal_n"]),
            "finite_section_diagnostics": section_diagnostics(panel, q, samples),
            "generalized_correction_diagnostics": correction_diagnostics(panel, q, [r for r in corrections if r["panel"] == name])})
    pins = {**BASE_PINS, **state["source_sha256"], str(audit_path.relative_to(method.ROOT)): admission_sha256,
            str(field_path.relative_to(method.ROOT)): field_sha,
            str(Path(__file__).resolve().relative_to(method.ROOT)): method.sha(Path(__file__))}
    adapter.verify_pins(pins)
    method.require(method.sha(field_path) == field_sha, "finite field changed during consumption")
    return {"schema": "thin_bolted_admitted_finite_panel_diagnostics/v1",
        **{k: state[k] for k in ("candidate", "revision", "state_id", "case_id", "accessory_placement", "parameters")},
        "field_sha256": field_sha, "source_sha256": pins, "finite_admission": admission,
        "panel_diagnostics": rows, "screw_actions_and_generic_references": screws,
        "maximum_head_witness": max(screws, key=lambda r: r["withdrawal_n"]),
        "method": {"finite_q_and_current_actions_only": True, "old_reference_datum_gate_used": False,
            "CAD_rebuilt": False, "reference_quadrature_prepared": False, "K_assembled": False, "response_solved": False},
        "limits": ["Generic head/withdrawal and mean ring pressure are references, not Hillman42605 capacities or measured stiffness.",
            "Finite Green/covariant section measures belong to the conditional APA zero-Poisson energy proxy, not a qualified plywood laminate or full through-thickness finite constitutive law.",
            "Linear APA target indices and variational transverse force per reference width are diagnostics; local hole/seat/hold/contact stress and finite capacity are unresolved.",
            "CD1 is the comparison basis; conditional1.6 is wind/earthquake only. Permanent duration/creep acceptance remains separate.",
            "Finite support/load/wrench admission is distinct from response, quadrature/mesh, contact-footprint, material and resistance qualification."],
        "complete_panel_resistance_established": False, "release": references.RELEASE}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--field", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--samples", type=int, default=41)
    parser.add_argument("--admission-sha256", required=True, help="independently reviewed frozen NEW finite gate hash")
    args = parser.parse_args()
    result = evaluate(args.field, args.samples, admission_sha256=args.admission_sha256)
    with args.out.open("x") as stream:
        stream.write(json.dumps(result, separators=(",", ":"), allow_nan=False) + "\n")
    print(json.dumps({"output": str(args.out), "sha256": method.sha(args.out),
                      "state_id": result["state_id"], "head_n": result["maximum_head_witness"]["withdrawal_n"]}))


if __name__ == "__main__":
    main()
