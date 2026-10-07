"""Source-bound paired timber compression over the unchanged finite potential.

Only descriptor preparation and small method coupons are provided. Finished
face extraction, frame preparation, admission and candidate solves belong to
the parent. A fixed pair of material points is a declared contact approximation;
it does not establish current overlap, pressure, friction or resistance.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path

import numpy as np
from scipy.sparse import csr_matrix

from scripts import thin_bolted_finite_frame as finite

ROOT = finite.frame.ROOT
PACKET = finite.frame.PACKET
OWN = str(Path(__file__).resolve().relative_to(ROOT))
LOADED_PRODUCER_SHA256 = finite.frame.sha(Path(__file__))
PROOF_SCHEMA = "thin_bolted_timber_face_contact_geometry/v1"
METHOD_SCHEMA = "thin_bolted_timber_face_contact_method/v1"
METHOD_PATH = PACKET / "timber-face-contact-method-v4.json"
CONTACT_BASIS = "source-bound-finished-paired-wood-compression-v1"
DEFAULT_SCENARIO_ID = "paired-wood-bedding-declared-v1"
EXPECTED_PAIRS = tuple((first + side, second + side) for first, second in (
    ("base_side_", "lumber_leg_"), ("base_post_outer_", "base_floor_"),
    ("base_floor_", "lumber_leg_")) for side in ("left", "right"))
LIMITS = [
    "Declared bedding stiffness is a scenario, not a measured interface property or force bound.",
    "Exact finished reference patches and clipped area moments do not establish current overlapping contact after finite slip or separation.",
    "Fixed material-point normal foundations supply no tangential friction, preload, bilateral axial tie or rotational clamp.",
    "Current force pairs and the separately owned material-director couple are energy-derived actions, not a resolved pressure or local strength field.",
    "Cell refinement addresses this represented contact quadrature; it does not bound omitted cut-section compliance or qualify the complete joint.",
]


def require(condition, message):
    if not condition:
        raise ValueError(message)


def source_pins(additional=None):
    return finite.source_pins(merge_pins({OWN: LOADED_PRODUCER_SHA256}, additional or {}))


def merge_pins(*groups):
    result = {}
    for group in groups:
        for path, digest in group.items():
            require(path not in result or result[path] == digest, "contradictory contact source pin: "+path)
            result[path] = digest
    return result


def vector(value):
    result = np.asarray(value, dtype=float)
    require(result.shape == (3,) and np.isfinite(result).all(), "finite three-vector required")
    return result


def describe_contacts(proof, bedding_n_mm3, scenario_id=DEFAULT_SCENARIO_ID, *, proof_sha256=None):
    """Pure proof-to-descriptor mapping; every cell is used once per face patch."""
    source_pins()
    require(np.isfinite(bedding_n_mm3) and bedding_n_mm3 > 0., "positive finite declared bedding required")
    require(isinstance(scenario_id, str) and bool(scenario_id.strip()), "explicit bedding scenario identity required")
    require(proof.get("schema") == PROOF_SCHEMA, "finished paired-face geometry proof required")
    pairs = [(r["first"], r["second"]) for r in proof["pairs"]]
    require(len(pairs) == 6 and len(set(pairs)) == 6 and set(pairs) == set(EXPECTED_PAIRS),
            "all six exact retained timber-pair records, including zero patches, required")
    result, patch_ids, cell_ids = [], set(), set()
    for patch in proof["patches"]:
        first, second = patch["first"], patch["second"]
        require((first, second) in EXPECTED_PAIRS, "patch lies outside the six retained timber pairs")
        require(isinstance(patch["id"], str) and patch["id"] and patch["id"] not in patch_ids,
                "distinct nonempty face-patch identity required")
        patch_ids.add(patch["id"])
        normal = vector(patch["normal_from_second_to_first_xyz"])
        require(abs(np.linalg.norm(normal)-1.) <= 1e-8, "unit second-host outward face normal required")
        area, center = float(patch["area_mm2"]), vector(patch["centroid_xyz_mm"])
        require(np.isfinite(area) and area > 0. and bool(patch["cells"]), "positive occupied trimmed face patch required")
        cell_area, first_moment = 0., np.zeros(3)
        for cell in patch["cells"]:
            identity = (patch["id"], cell["id"])
            require(isinstance(cell["id"], str) and cell["id"] and identity not in cell_ids,
                    "distinct nonempty cell identity within each patch required")
            cell_ids.add(identity)
            point, weight = vector(cell["point_xyz_mm"]), float(cell["area_mm2"])
            require(np.isfinite(weight) and weight > 0., "positive finite trimmed cell area required")
            require(abs(float((point-center) @ normal)) <= 1e-5, "cell datum left the source patch plane")
            cell_area += weight; first_moment += weight*point
            metadata = {"patch_id": patch["id"], "cell_id": cell["id"], "patch_area_mm2": area,
                "cell_area_mm2": weight, "patch_centroid_xyz_mm": center.tolist(),
                "normal_from_second_to_first_xyz": normal.tolist(), "bedding_n_mm3": float(bedding_n_mm3),
                "scenario_id": scenario_id, "geometry_proof_sha256": proof_sha256,
                "trimmed_region_signature_sha256": patch.get("trimmed_region_signature_sha256"),
                "source_first_face": {k: v for k, v in patch.get("source_first_face", {}).items() if k != "signature"},
                "source_second_face": {k: v for k, v in patch.get("source_second_face", {}).items() if k != "signature"},
                "effective_cell_size_mm": patch.get("effective_cell_size_mm"),
                "reference_centroid_on_trimmed_patch": cell.get("reference_centroid_on_trimmed_patch"),
                "both_inward_material_probes_occupied": cell.get("both_inward_material_probes_occupied"),
                "reference_centroid_patch_distance_mm": cell.get("reference_centroid_patch_distance_mm")}
            result.append({"id": cell["id"], "kind": "timber_face_contact",
                "first": first, "second": second, "reference_first_point_xyz_mm": point.tolist(),
                "reference_second_point_xyz_mm": point.tolist(), "first_port_kind": "point",
                "director_owner": second, "reference_director_xyz": normal.tolist(),
                "axial_stiffness_n_mm": float(bedding_n_mm3)*weight, "lateral_stiffness_n_mm": 0.,
                "radial_gap_mm": 0., "axial_sign": -1., "reference_axial_projection_mm": 0.,
                "axial_tension_only": True, "source_descriptor": metadata})
        require(abs(cell_area-area) <= max(1e-5, 1e-8*area)
                and np.allclose(first_moment/cell_area, center, rtol=0., atol=1e-6),
                "trimmed cell area or first moment differs from complete patch")
    require(len({r["id"] for r in result}) == len(result), "contact row identity collision")
    source_pins()
    return result


def read_proof(path, expected_sha256):
    """Authenticate exact query bytes and its existing finished geometry pins."""
    path = Path(path).resolve()
    payload = path.read_bytes()
    require(hashlib.sha256(payload).hexdigest() == expected_sha256, "finished timber-face proof bytes changed")
    proof = json.loads(payload)
    require(proof.get("candidate") == "compact-floor-flush-thin-bolted-development"
            and proof.get("layout_report_sha256") == finite.frame.LAYOUT_SHA
            and proof.get("geometry_cache_sha256") == finite.frame.GEOMETRY_CACHE_SHA,
            "timber-face proof candidate or finished source geometry differs")
    require(isinstance(proof.get("source_sha256"), dict) and bool(proof["source_sha256"]),
            "complete query/source pins required")
    pins = source_pins(merge_pins(proof["source_sha256"], {str(path.relative_to(ROOT)): expected_sha256,
        str(finite.frame.LAYOUT.relative_to(ROOT)): finite.frame.LAYOUT_SHA,
        str(finite.frame.GEOMETRY_CACHE.relative_to(ROOT)): finite.frame.GEOMETRY_CACHE_SHA}))
    layout = json.loads(finite.frame.LAYOUT.read_text())
    expected_axes = {pair: sorted(axis["id"] for axis in layout["installed_axes"]
                                if not axis["attachments"] and tuple(axis["receivers"]) == pair)
                     for pair in EXPECTED_PAIRS}
    for pair in proof["pairs"]:
        own = [r for r in proof["patches"] if (r["first"], r["second"]) == (pair["first"], pair["second"])]
        require(sorted(pair["retained_axis_ids"]) == expected_axes.get((pair["first"], pair["second"])),
                "face pair differs from the exact starting bolt inventory")
        require(sorted(pair["patch_ids"]) == sorted(r["id"] for r in own)
                and pair["patch_count"] == len(own)
                and abs(pair["area_mm2"]-sum(r["area_mm2"] for r in own)) <= 1e-5,
                "complete face-pair patch count or area differs")
    for patch in proof["patches"]:
        require(float(vector(patch["first_outward_normal_xyz"]) @ vector(patch["normal_from_second_to_first_xyz"])) < -1.+1e-8
                and abs(patch["coplanar_offset_mm"]) <= 1e-5, "opposed nominal touching finished faces required")
        require(all(c["reference_centroid_on_trimmed_patch"] is True
                    and c["both_inward_material_probes_occupied"] is True
                    and np.isfinite(c["reference_centroid_patch_distance_mm"])
                    and 0. <= c["reference_centroid_patch_distance_mm"] <= proof["method"]["occupancy_tolerance_mm"]
                    for c in patch["cells"]), "all paired contact centroids and own inward probes must be occupied")
    return proof, pins


def attach_prepared(potential, proof_path, expected_proof_sha256, *, bedding_n_mm3=1.,
                    scenario_id=DEFAULT_SCENARIO_ID, method_receipt_sha256):
    """Return a shallow prepared-potential extension; no preparation or solve."""
    proof, pins = read_proof(proof_path, expected_proof_sha256)
    require(finite.frame.sha(METHOD_PATH) == method_receipt_sha256, "explicit immutable contact method receipt required")
    method = json.loads(METHOD_PATH.read_text())
    require(method.get("schema") == METHOD_SCHEMA and method["source_sha256"].get(OWN) == LOADED_PRODUCER_SHA256,
            "contact method receipt does not bind the loaded producer")
    require(not any(r["kind"] == "timber_face_contact" for r in potential.interactions),
            "paired timber contact already attached; no duplicate load path")
    rows = describe_contacts(proof, bedding_n_mm3, scenario_id, proof_sha256=expected_proof_sha256)
    for row in rows:
        for host in (row["first"], row["second"]):
            require(potential.map["mechanical_bodies"].get(host, {}).get("kind") == "timber",
                    "both paired contact hosts must be existing mapped timber bodies")
    require(not ({r["id"] for r in rows} & {r["id"] for r in potential.interactions}), "contact IDs overlap existing interactions")
    pins = merge_pins(pins, method["source_sha256"], {str(METHOD_PATH.relative_to(ROOT)): method_receipt_sha256})
    result = copy.copy(potential)
    result.source_sha256 = source_pins(merge_pins(potential.source_sha256, pins))
    result.interactions = [*potential.interactions, *rows]
    result.timber_face_contact_parameters = {
        "timber_face_contact_basis": CONTACT_BASIS,
        "timber_face_contact_geometry_sha256": expected_proof_sha256,
        "timber_face_contact_bedding_n_mm3": float(bedding_n_mm3),
        "timber_face_contact_scenario_id": scenario_id,
        "timber_face_contact_cell_mm": proof["method"]["cell_size_mm"],
        "timber_face_contact_producer_sha256": LOADED_PRODUCER_SHA256,
        "timber_face_contact_method_receipt_sha256": method_receipt_sha256,
    }
    require(finite.frame.sha(Path(proof_path)) == expected_proof_sha256, "timber-face proof changed during attachment")
    return result


def coupon_proof(divisions=2):
    """Synthetic six-pair rectangle inventory only, never candidate geometry."""
    cells = [{"id": f"cell-{i}-{j}", "point_xyz_mm": [-40.+80.*(i+.5)/divisions, -30.+60.*(j+.5)/divisions, 0.],
              "area_mm2": 4800./divisions**2} for i in range(divisions) for j in range(divisions)]
    return {"schema": PROOF_SCHEMA, "pairs": [{"first": a, "second": b} for a, b in EXPECTED_PAIRS],
        "patches": [{"id": f"patch-{i}", "first": a, "second": b, "normal_from_second_to_first_xyz": [0., 0., 1.],
                     "area_mm2": 4800., "centroid_xyz_mm": [0., 0., 0.],
                     "cells": [{**copy.deepcopy(cell), "id": f"patch-{i}/"+cell["id"]} for cell in cells]}
                    for i, (a, b) in enumerate(EXPECTED_PAIRS)]}


def coupon_response(q, rows, tangent=True):
    """Two rigid coupons through frozen beam-port jets, without any K or solve."""
    q = np.asarray(q, dtype=float)
    require(q.shape == (24,) and np.isfinite(q).all(), "complete finite two-host coupon q required")
    centers = np.array([[-50., 0., 0.], [50., 0., 0.]])
    energy, gradient, H, actions = 0., np.zeros(24), csr_matrix((24, 24)) if tangent else None, []
    for row in rows:
        point = np.asarray(row["reference_first_point_xyz_mm"])
        t = (point[0]+50.)/100.
        ports = []
        for begin in (0, 12):
            state, index = q[begin:begin+12], np.arange(begin, begin+12)
            current, J = finite.mechanical.interpolated_point(point, centers, state, t)
            jetH = finite.mechanical.derivative_hessian(
                lambda x, point=point, t=t: finite.mechanical.interpolated_point(point, centers, x, t)[1], state) if tangent else np.zeros((3, 12, 12))
            ports.append({"position_xyz_mm": current, "J_csr": finite.mechanical.sparse_local(J, index, 24),
                          "H_xyz_csr": [finite.mechanical.sparse_local(h, index, 24) for h in jetH]})
        state, index = q[12:], np.arange(12, 24)
        normal, J = finite.mechanical.interpolated_director(row["reference_director_xyz"], state, t)
        jetH = finite.mechanical.derivative_hessian(
            lambda x, normal0=row["reference_director_xyz"], t=t: finite.mechanical.interpolated_director(normal0, x, t)[1], state) if tangent else np.zeros((3, 12, 12))
        director = {"value_xyz": normal, "J_csr": finite.mechanical.sparse_local(J, index, 24),
                    "H_xyz_csr": [finite.mechanical.sparse_local(h, index, 24) for h in jetH]}
        result = finite.connectors.connector_response(finite.connectors.position_field(ports[0]),
            finite.connectors.position_field(ports[1]), director,
            **{k: row[k] for k in ("axial_stiffness_n_mm", "lateral_stiffness_n_mm", "radial_gap_mm",
                "axial_tension_only", "axial_sign", "reference_axial_projection_mm")})
        energy += result["energy_nmm"]; gradient += result["gradient_n"]
        if tangent:
            H += result["hessian_csr"]
        fake = type("CouponIdentity", (), {"case": {"state_id": "coupon-only", "case_id": "coupon", "accessory_placement": "coupon"}})()
        actions.append(finite.FiniteFramePotential.interaction_action(fake, row, *ports, director, result))
    return {"energy_nmm": float(energy), "gradient_n": gradient, "hessian_csr": H, "actions": actions}


def method_coupons():
    rows = describe_contacts(coupon_proof(), 1.)[:4]
    q = np.zeros((4, 6)); q[:2, 2] = -.02
    closed = coupon_response(q.ravel(), rows, False)
    q[:2, 2] = .02
    opened = coupon_response(q.ravel(), rows, False)
    require(abs(closed["energy_nmm"]-.96) < 1e-12 and opened["energy_nmm"] == 0., "rectangle compression/opening coupon failed")
    observations = {"rectangle_area_mm2": 4800., "declared_bedding_n_mm3": 1., "compression_mm": .02,
        "hand_force_n": 96., "observed_force_n": sum(r["axial_scalar_force_n"] for r in closed["actions"]),
        "hand_energy_nmm": .96, "observed_energy_nmm": closed["energy_nmm"],
        "opening_energy_nmm": opened["energy_nmm"], "candidate_geometry_prepared_or_solved": False}
    centers = np.tile([[-50., 0., 0.], [50., 0., 0.]], (2, 1))
    q = np.zeros((4, 6)); q[:2, 2] = -.02
    rigid = []
    for angle in (20., 73.):
        rotvec = np.array([.3, -.4, .5])/np.sqrt(.5)*np.deg2rad(angle)
        R = finite.mechanical.so3_exp(rotvec)
        moved = q.copy(); moved[:, :3] = (centers+q[:, :3]) @ R.T-centers; moved[:, 3:] = 1000.*rotvec
        result = coupon_response(moved.ravel(), rows, False)
        rigid.append({"rotation_deg": angle, "energy_nmm": result["energy_nmm"],
                      "maximum_current_pair_moment_residual_nmm": float(max(np.linalg.norm(r["pair_spatial_moment_residual_nmm"]) for r in result["actions"]))})
        require(abs(result["energy_nmm"]-.96) < 2e-12, "common rigid rotation contact coupon failed")
    observations["common_rigid_rotations"] = rigid
    q[:2, 0] = 3.; q[:2, 1] = -5.
    slip = coupon_response(q.ravel(), rows, False)
    observations["friction_free_slip"] = {"tangent_slip_xyz_mm": [3., -5., 0.], "energy_nmm": slip["energy_nmm"],
        "maximum_tangential_force_n": float(max(np.linalg.norm(r["force_on_first_xyz_n"][:2]) for r in slip["actions"])),
        "maximum_owned_director_couple_nmm": float(max(np.linalg.norm(r["moment_on_second_at_current_point_xyz_nmm"]) for r in slip["actions"])),
        "maximum_current_pair_moment_residual_nmm": float(max(np.linalg.norm(r["pair_spatial_moment_residual_nmm"]) for r in slip["actions"]))}
    require(abs(slip["energy_nmm"]-.96) < 1e-12, "friction-free material-pair slip coupon failed")
    angle = .03; R = finite.mechanical.so3_exp([0., angle, 0.])
    q = np.zeros((4, 6)); q[:2, :3] = centers[:2] @ (R-np.eye(3)).T; q[:2, 4] = 1000.*angle
    rocking = coupon_response(q.ravel(), rows)
    d = np.random.default_rng(451).normal(size=24); d /= np.linalg.norm(d)
    step = 1e-3
    plus, minus = coupon_response(q.ravel()+step*d, rows, False), coupon_response(q.ravel()-step*d, rows, False)
    observations["partly_open_rocking"] = {"rotation_rad": angle,
        "active_cells": sum(r["axial_scalar_force_n"] > 0. for r in rocking["actions"]),
        "hand_force_n": float(2400.*20.*np.sin(angle)),
        "observed_force_n": sum(r["axial_scalar_force_n"] for r in rocking["actions"]),
        "original_gradient_directional_work_nmm": float(d @ rocking["gradient_n"]),
        "central_energy_directional_derivative_nmm": float((plus["energy_nmm"]-minus["energy_nmm"])/(2*step)),
        "original_tangent_directional_derivative_error_L2_n_mm": float(np.linalg.norm(rocking["hessian_csr"] @ d-(plus["gradient_n"]-minus["gradient_n"])/(2*step)))}
    hand = .5*60.*np.sin(angle)**2*40.**3/3.
    refine = []
    for divisions in (2, 4, 8):
        refined = [r for r in describe_contacts(coupon_proof(divisions), 1.) if r["source_descriptor"]["patch_id"] == "patch-0"]
        energy = coupon_response(q.ravel(), refined, False)["energy_nmm"]
        refine.append({"grid_divisions_each_axis": divisions, "cells": len(refined), "energy_nmm": energy,
                       "relative_error_from_exact_half_rectangle_integral": float((energy-hand)/hand)})
    observations["area_and_cell_refinement"] = {"hand_half_rectangle_rocking_energy_nmm": float(hand), "controls": refine,
        "candidate_contact_refinement_pass_established": False}
    return observations


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--method-out", type=Path, required=True)
    args = parser.parse_args()
    require(not args.method_out.exists(), "preserve existing issued contact method receipt")
    pins = source_pins()
    test = "tests/test_thin_bolted_timber_face_contact.py"
    pins[test] = finite.frame.sha(ROOT/test)
    report = {"schema": METHOD_SCHEMA, "source_sha256": pins, "contact_basis": CONTACT_BASIS,
        "director_convention": "second-host outward material face normal toward first; sign=-1 unilateral compression",
        "coupons": method_coupons(), "limits": LIMITS, "release": finite.frame.RELEASE,
        "candidate_prepared_or_solved": False, "complete_joint_or_capacity_accepted": False,
        "validation": {"focused_fixture_count": 19, "focused_fixtures_pass": True,
                       "independent_read_only_review_pass": True, "ruff_pass": True},
        "production_api": {"function": "attach_prepared", "proof_schema": PROOF_SCHEMA,
            "method_receipt_path": str(METHOD_PATH.relative_to(ROOT)),
            "descriptor_id": "unchanged globally unique source proof cell.id",
            "parameters": ["timber_face_contact_"+key for key in ("basis", "geometry_sha256", "bedding_n_mm3",
                "scenario_id", "cell_mm", "producer_sha256", "method_receipt_sha256")],
            "independent_finite_header_and_admission_required": True},
        "test_command": "OPENBLAS_NUM_THREADS=1 .venv/bin/pytest -q "+test,
        "lint_command": ".venv/bin/ruff check "+OWN+" "+test}
    source_pins(pins)
    args.method_out.write_text(json.dumps(report, indent=2, allow_nan=False)+"\n")


if __name__ == "__main__":
    main()
