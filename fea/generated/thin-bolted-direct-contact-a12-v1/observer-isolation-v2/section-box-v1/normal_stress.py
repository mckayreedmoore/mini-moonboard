"""Five saved net-section containing-box normal-stress diagnostics only."""

from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

import numpy as np

from scripts import thin_bolted_timber_finite_checks as coefficients

ROOT = Path(__file__).resolve().parents[5]
OWN = Path(__file__).resolve()
LOADED_SHA = hashlib.sha256(OWN.read_bytes()).hexdigest()
MEMBER = OWN.parent.parent / "member-schema-v1/component_reductions.py"
MEMBER_SHA = "5d3da02c9879e7a364b73f9164120dc8d9129d8b7954c66ff0c76dabfd1f5b40"
GATE = OWN.parent.parent / "admission.py"
GATE_SHA = "4b78722ab407a39d6e00fc9e16be0d370d0c837dea5880e45e7a2e277dd6efb6"
COEFFICIENT_SHA = "c22215fc4016aa618827ec17a78063d7344a01ce335207b9d650cc35b740de83"
KEYS = {("lumber_leg_left", -303.9267207), ("lumber_leg_right", -303.9267207),
        ("base_rail_bottom_right", 173.1875), ("base_rail_service_lower_left", -989.2),
        ("base_principal_center_left", 2419.8241337)}


def load_source(name, path, digest):
    if hashlib.sha256(path.read_bytes()).hexdigest() != digest:
        raise ValueError("reviewed source differs: " + str(path))
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    if hashlib.sha256(path.read_bytes()).hexdigest() != digest:
        raise ValueError("source changed during load")
    return module


member = load_source("member_schema_for_five_section_boxes", MEMBER, MEMBER_SHA)
pure = member.pure


def section_box_bound(properties, wrench):
    """Actual net A/I with a containing-box enclosure, not occupied extrema."""
    basis = np.asarray(properties["basis_u_v_grain_xyz"], dtype=float)
    area = properties["finished_area_mm2"]
    covariance = np.asarray(properties["centroidal_area_moment_matrix_uv_mm4"], dtype=float)
    centroid = pure.unit.vector(properties["centroid_xyz_mm"], "net centroid")
    cut = pure.unit.vector(wrench["cut_point_xyz_mm"], "same-cut point")
    force = pure.unit.vector(wrench["force_on_lower_portion_xyz_n"], "same-cut force")
    moment = pure.unit.vector(wrench["moment_on_lower_portion_about_cut_xyz_nmm"], "same-cut couple")
    pure.unit.require(basis.shape == (3, 3) and np.isfinite(basis).all()
        and np.linalg.norm(basis @ basis.T - np.eye(3)) < 1e-8 and abs(np.linalg.det(basis) - 1.) < 1e-8
        and np.isfinite(area) and area > 0. and covariance.shape == (2, 2)
        and np.isfinite(covariance).all() and np.linalg.norm(covariance - covariance.T) < 1e-6
        and np.linalg.eigvalsh(covariance).min() > 0., "positive net area/inertia and proper section basis required")
    station = properties["station_global_grain_projection_mm"]
    pure.unit.require(abs(float(basis[2] @ cut) - station) < 1e-5
        and abs(float(basis[2] @ centroid) - station) < 1e-5, "wrench and centroid must belong to the exact saved plane")
    # Reuse only the pure coefficient function. Its facade keys are mapped to
    # the linear model's REFERENCE datums; no finite current pose is asserted.
    facade = {"current_finished_section_centroid_xyz_mm": centroid,
        "force_on_lower_material_portion_xyz_n": force,
        "moment_on_lower_material_portion_about_current_cut_xyz_nmm": moment,
        "current_cut_point_xyz_mm": cut, "current_basis_u_v_grain_xyz": basis.tolist(),
        "reference_basis_u_v_grain_xyz": basis.tolist(),
        "local_Vu_Vv_N_TensionPositive_n": (basis @ force).tolist()}
    component = coefficients.centroid_components(facade, properties)
    beta = np.asarray(component["linear_normal_stress_gradient_uv_n_mm3"])
    mean = component["mean_axial_normal_stress_n_mm2"]
    center_uv = np.asarray(properties["centroid_uv_mm"])
    origin = np.asarray(pure.unit.vector(properties["section_origin_xyz_mm"], "saved section origin"))
    bounds = np.asarray([properties["bounds_uv_mm"][key] for key in ("u", "v")], dtype=float)
    pure.unit.require(bounds.shape == (2, 2) and np.isfinite(bounds).all()
        and center_uv.shape == (2,) and np.isfinite(center_uv).all()
        and np.all(bounds[:, 0] <= center_uv) and np.all(center_uv <= bounds[:, 1])
        and np.linalg.norm(origin + basis[:2].T @ center_uv - centroid) < 1e-5,
        "saved containing box and local coordinates must enclose the same centroid")
    corners = []
    for u in bounds[0]:
        for v in bounds[1]:
            uv = np.asarray([u, v])
            point = origin + basis[:2].T @ uv
            corners.append({"box_corner_uv_mm": uv.tolist(), "reference_box_corner_xyz_mm": point.tolist(),
                "signed_linear_normal_stress_mpa": float(mean + beta @ (uv - center_uv)),
                "actual_material_occupancy_at_corner_verified": False})
    return {"signed_same_cut_wrench": wrench, "finished_net_area_mm2": area,
        "reference_finished_centroid_xyz_mm": centroid,
        "moment_about_reference_finished_centroid_xyz_nmm": component["moment_about_current_finished_centroid_xyz_nmm"],
        "mean_axial_normal_stress_mpa": mean, "normal_stress_gradient_uv_n_mm3": beta.tolist(),
        "minimum_signed_normal_stress_box_witness": min(corners, key=lambda row: row["signed_linear_normal_stress_mpa"]),
        "maximum_signed_normal_stress_box_witness": max(corners, key=lambda row: row["signed_linear_normal_stress_mpa"]),
        "reference_linear_Bernoulli_field_enclosed_by_saved_net_section_box": True,
        "finite_current_pose_or_occupied_corner_claimed": False, "actual_trimmed_directional_stress_extrema": None,
        "NDS_component_ratio_or_complete_member_resistance": None, "shear_torsion_fracture_buckling_stability": None}


def read_properties():
    properties, pins = [], {}
    for name, digest in pure.PROPERTY_PINS.items():
        path = pure.PACKET / name
        pure.verify_pins({str(path.relative_to(ROOT)): digest})
        report = json.loads(path.read_bytes())
        pure.unit.require(report["state_id"] is None and report["candidate"] == pure.unit.CANDIDATE
            and not any(report["release"].values()), "only frozen geometry-only section properties allowed")
        pins[str(path.relative_to(ROOT))] = digest
        for key, value in report["source_sha256"].items():
            pure.unit.require(key not in pins or pins[key] == value, "section source contradiction")
            pins[key] = value
        properties.extend(report["finished_sections"])
    pure.unit.require(len(properties) == 5
        and {(row["member"], row["station_global_grain_projection_mm"]) for row in properties} == KEYS,
        "only the five existing exact saved planes allowed")
    pure.verify_pins(pins)
    return properties, pins


def consume(field_path, admission, *, expected_field_sha256, admission_sha256):
    """NEW admission first, then recover just five same-cut reference wrenches."""
    path = Path(field_path).resolve()
    payload = path.read_bytes()
    pure.unit.require(hashlib.sha256(payload).hexdigest() == expected_field_sha256
        and admission_sha256 == GATE_SHA, "exact released bytes and reviewed new gate SHA required")
    before = pure.references.canonical_sha(admission)
    gate = load_source("observer_admission_for_five_section_boxes", GATE, GATE_SHA)
    demand, verified = gate.require_admitted_payload(payload, admission, admission_sha256=admission_sha256)
    field_before = pure.references.canonical_sha(demand)
    pure.unit.require(field_before == pure.references.canonical_sha(json.loads(payload)), "validator changed admitted field")
    member.verify_alias_state_labels(demand)
    pins = dict(pure.PINS)
    additional = {**verified, str(MEMBER.relative_to(ROOT)): MEMBER_SHA,
        str(Path(coefficients.__file__).relative_to(ROOT)): COEFFICIENT_SHA,
        str(GATE.relative_to(ROOT)): GATE_SHA, str(OWN.relative_to(ROOT)): LOADED_SHA,
        str(path.relative_to(ROOT)): expected_field_sha256}
    for key, value in additional.items():
        pure.unit.require(key not in pins or pins[key] == value, "admitted source contradicts a reused method")
        pins[key] = value
    pure.verify_pins(pins)
    properties, extra = read_properties()
    for key, value in extra.items():
        pure.unit.require(key not in pins or pins[key] == value, "saved property/source contradiction")
        pins[key] = value
    spans = pure.timber.read_member_span_geometry()
    span_receipt = pure.timber.verify_member_span_geometry(demand, spans)
    points, gravity = pure.timber.member_point_inputs(demand)
    results = []
    for prop in properties:
        name, station = prop["member"], prop["station_global_grain_projection_mm"]
        grain = prop["basis_u_v_grain_xyz"][2]
        span = spans[name]
        pure.unit.require(np.linalg.norm(np.asarray(grain) - span["basis_grain_u_v_xyz"][0]) < 1e-8, "saved section grain differs")
        start = span["start_xyz_mm"]
        low, high = (pure.unit.dot(grain, span[key]) for key in ("start_xyz_mm", "end_xyz_mm"))
        cut = pure.references.add(start, pure.references.scale(grain, station - low))
        center, weight = gravity[name]
        wrench = pure.references.member_cut_wrench(grain, low, high, cut, center, weight, points[name])
        results.append({**{key: demand[key] for key in pure.IDENTITIES}, "member": name,
            "station_global_grain_projection_mm": station, **section_box_bound(prop, wrench)})
    pure.unit.require(path.read_bytes() == payload and pure.references.canonical_sha(demand) == field_before
        and pure.references.canonical_sha(admission) == before, "admitted inputs changed during five-section reduction")
    pure.verify_pins(pins)
    return {"schema": "thin_bolted_five_saved_section_box_normal_stress/v1",
        **{key: demand[key] for key in pure.IDENTITIES}, "field_sha256": expected_field_sha256,
        "field_canonical_sha256": field_before, "source_sha256": pins, "independent_new_admission": admission,
        "independent_member_span_geometry": span_receipt, "five_same_cut_section_box_bounds": results,
        "gravity_scope": "unchanged affine member selfweight preserving total force and centroid; not finite discrete gravity",
        "all584_faces_collected_once_from_contact_actions": True, "CAD_native_K_or_response_executed": False,
        "complete_joint_resistance_or_acceptance": None, "release": dict(pure.unit.RELEASE)}
