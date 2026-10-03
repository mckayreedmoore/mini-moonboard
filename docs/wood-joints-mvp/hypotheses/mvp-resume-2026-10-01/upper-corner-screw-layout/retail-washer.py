"""Screen one Lowe's thick steel washer at the frozen current corner demand."""

from __future__ import annotations

import argparse
import importlib.util
import json
import math
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
EDGE = HERE / "upper-right-washer-edge.py"
CURRENT = HERE / "rawlocal/corner-first-order/attempt01/checks.json"
MODEL = HERE / "operators-attempt02/model.json"
ROWS = HERE / "operators-attempt02/row-identities.json"
INPUTS = HERE / "operators-attempt02/model-inputs.json"
COMPONENT = HERE / "bolted-replay-results/corner-attempt01/component-results.json"
SURFACES = HERE.parents[1] / "current-finished-feature-register-2026-10-01/surfaces.json"
PINS = {
    EDGE: "ffe3db3e8c707851d44f0c60c43e6e6ef4aa4845f753dc6880c64186e3c75e61",
    CURRENT: "b15b57d3879fdca2dac607d11a2ad127acd1008f6c2a6f546333a1b26c754cfe",
    MODEL: "b5f9b87b70c4a9920372a3443a55e37dfe34351fb9ac8210b299c1360fb93626",
    ROWS: "cdf218780bdabdb8774174c79b37d7c9f554abc6be2e1f817999635e56868b27",
    INPUTS: "e2109cabed9fcbc0a14346ef63b707abb1aed358ebf5fa126b2cba216aa771cc",
    COMPONENT: "401b8876dc3a96b553c847f1029a5a9200ba3f45af5493f64edd61fdc6bc42b6",
    SURFACES: "33fff67eee4bc4e96ccef5703f6eebd0d4e004541c6114a4b1da4a5332b2f6eb",
}
PRODUCT = {
    "retailer": "Lowe's", "manufacturer_model": "Hillman 885522", "item": "755754",
    "url": "https://www.lowes.com/pd/Hillman-4-Count-Pack-1-4-in-x-1-in-Zinc-plated-Fender-Washer/999995992",
    "listed_price_usd_per_four": 2.48, "listed_material": "zinc-plated steel",
    "nominal_bolt_size_label_mm": 6.35, "nominal_OD_mm": 25.4,
    "modeled_ID_mm": 8.3058,
    "modeled_ID_basis": "existing generic quarter-inch USS opening hypothesis; not the retail item's actual bore or guaranteed upper bound",
    "modeled_thickness_mm": 2.5,
    "thickness_conflict": "overview 0.13 in=3.302 mm; inch specification 0.125 in=3.175 mm; metric specification 2.5 mm",
    "thickness_basis": "lowest listed nominal, not a guaranteed minimum or measured dimension",
    "numeric_product_yield_mpa": None,
}
WOOD_BORE_RADIUS = 3.75
AXIS_ID = "top_outer/clip_single_top_right_2/rail_1"


def load(edge):
    module, _old_source, pins = edge.load_source()
    for path, digest in PINS.items():
        edge.require(path not in pins or pins[path] == digest, "conflicting source pin")
        pins[path] = digest
    pins[Path(__file__).resolve()] = edge.sha(Path(__file__).resolve())
    module.authenticate(pins)
    document = json.loads(CURRENT.read_text())
    edge.require(document["failure"] is None and len(document["states"]) == 12,
                 "current first-order source incomplete")
    for path, digest in document["source_sha256"].items():
        absolute = ROOT / path
        edge.require(absolute not in pins or pins[absolute] == digest, "current source pin conflicts")
        pins[absolute] = digest
    state = next(s for s in document["states"] if s["case_id"] == "k12-right" and s["side"] == "right")
    bolt = next(b for b in state["hosts"]["base_rail_top"]["state"]["bolts"] if b["axis_id"] == AXIS_ID)
    source = {
        "state_id": edge.STATE_ID, "case_id": state["case_id"], "side": "right",
        "axis_id": AXIS_ID, "end_role": "host", "family": "rail",
        "source_current_checks_sha256": PINS[CURRENT], "T_n": bolt["compatible_T_n"],
        "M_magnitude_nmm": bolt["end_contacts"][0]["moment_nmm"],
        "source_signed_M_vector_in_pair_basis_nmm": bolt["end_moment_vectors_in_transverse_basis_nmm"][0],
        "source_signed_slope_vector_in_pair_basis_rad": bolt["end_slope_vectors_rad"][0],
        "source_moment_on_beam_xyz_nmm": bolt["end_contacts"][0]["moment_on_beam_xyz_nmm"],
        "saved_rigid_contact": bolt["end_contacts"][0],
    }
    module.FAMILIES = {**module.FAMILIES, "rail": {
        "inner_radius_mm": PRODUCT["modeled_ID_mm"] / 2,
        "outer_radius_mm": PRODUCT["nominal_OD_mm"] / 2,
        "head_radius_mm": 5.0, "thickness_mm": PRODUCT["modeled_thickness_mm"],
    }}
    module.authenticate(pins)
    return module, source, pins


def nominal_support(edge, pins):
    """Check the disk on the saved finished face, including every trimmed hole."""
    rows = json.loads(ROWS.read_text())
    tie = next(row for row in rows if row["row_id"] == AXIS_ID + "/outer-seat-axial-tie")
    normal = np.array(tie["ownership"]["direction_global_xyz"])
    basis = np.column_stack(([1.0, 0.0, 0.0], np.cross(normal, [1.0, 0.0, 0.0]), normal))
    edge.require(np.allclose(basis.T @ basis, np.eye(3), atol=1e-10), "stock support basis differs")
    inputs = json.loads(INPUTS.read_text())
    member = next(row for row in inputs["members"] if row["member_id"] == "base_rail_top")
    record = next(row for row in json.loads(SURFACES.read_text())["records"] if row["member_id"] == "base_rail_top")
    binding = record["step_binding"]
    for key in ("path", "file_sha256"):
        edge.require(binding[key] == member["current_finished_step_binding"][key], "surface register leaves current finished stock")
    pins[ROOT / binding["path"]] = binding["file_sha256"]
    edge.require(edge.sha(ROOT / binding["path"]) == binding["file_sha256"], "finished receiver STEP differs")
    component = json.loads(COMPONENT.read_text())
    seat = np.array(next(row["seat_point_mm"] for row in component["washer_seats"]
                         if row["axis_id"] == AXIS_ID and row["body"] == "base_rail_top"))
    faces = [row for row in record["features"] if row["surface_kind"] == "PLANE"
             and abs(abs(np.dot(row["plane"]["normal_global_xyz"], normal)) - 1) < 1e-8
             and abs(np.dot(row["plane"]["normal_global_xyz"], seat)
                     - row["plane"]["signed_plane_station_global_mm"]) < 1e-5]
    edge.require(len(faces) == 1, "washer seat has no unique saved exterior plane")
    face = faces[0]
    wires = face["trim"]["wires"]
    outer = [wire for wire in wires if len(wire["edges"]) == 4
             and all(item["curve_kind"] == "LINE" for item in wire["edges"])]
    edge.require(len(outer) == 1, "seat outer trim is not one saved rectangle")
    points = np.array([point for item in outer[0]["edges"]
                       for point in item["topological_vertices_global_xyz_mm"]]) @ basis
    center = seat @ basis
    bounds = np.array([points.min(axis=0), points.max(axis=0)])
    distances = np.r_[center[:2] - bounds[0, :2], bounds[1, :2] - center[:2]]
    radius = PRODUCT["nominal_OD_mm"] / 2
    edge.require(np.min(distances) >= radius, "enlarged washer leaves saved exterior face footprint")
    holes, own = [], []
    for wire in wires:
        if wire is outer[0]:
            continue
        edge.require(len(wire["edges"]) == 1 and wire["edges"][0]["curve_kind"] == "CIRCLE",
                     "unmodeled noncircular passage in saved washer face")
        circle = wire["edges"][0]["circle"]
        distance = float(np.linalg.norm((np.array(circle["center_global_xyz_mm"]) @ basis - center)[:2]))
        if distance < 1e-5:
            own.append(circle)
            edge.require(circle["radius_mm"] <= PRODUCT["modeled_ID_mm"] / 2,
                         "declared washer opening credits wood over its own bore")
        else:
            clearance = distance - radius - circle["radius_mm"]
            edge.require(clearance >= 0, "another saved bore enters enlarged washer footprint")
            holes.append({"center_distance_mm": distance, "radius_mm": circle["radius_mm"],
                          "clearance_from_outer_disk_mm": clearance})
    edge.require(len(own) == 1 and len(holes) == 7, "finished seat hole census differs")
    return {
        "receiver": "base_rail_top", "finished_face_id": face["feature_id"], "finished_step_binding": binding,
        "basis_global_xyz": basis.tolist(), "nominal_stock_bounds_local_mm": bounds.tolist(),
        "axis_local_mm": center.tolist(), "edge_distances_mm": distances.tolist(),
        "minimum_outer_disk_edge_margin_mm": float(np.min(distances) - radius),
        "other_face_holes": holes, "minimum_other_bore_clearance_mm": min(row["clearance_from_outer_disk_mm"] for row in holes),
        "own_saved_bore_radius_mm": own[0]["radius_mm"], "face_trim_wire_count": len(wires),
        "wood_bore_diameter_mm": 2 * WOOD_BORE_RADIUS,
        "nominal_supported_annulus_area_mm2": math.pi * (radius**2 - (PRODUCT["modeled_ID_mm"] / 2)**2),
        "scope": "saved finished planar face, rectangular outer trim and all eight circular inner wires; analytic concentric nominal support, not an inspected seat or loaded shift/tilt guarantee",
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--resolution", choices=("coarse", "fine"), required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    output = args.output.resolve()
    if output.exists():
        raise ValueError(f"output already exists: {output}")
    sys.dont_write_bytecode = True
    spec = importlib.util.spec_from_file_location("frozen_retail_washer_edge", EDGE)
    if spec is None or spec.loader is None:
        raise ValueError("frozen edge helper unavailable")
    edge = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(edge)
    module, source, pins = load(edge)
    support = nominal_support(edge, pins)
    output.mkdir(parents=True, exist_ok=False)
    (output / ".gitignore").write_text("*\n")
    (output / "producer.py.snapshot").write_bytes(Path(__file__).read_bytes())
    state, fields, coupon, rigid, failure, debug = None, None, None, None, None, {}
    try:
        model = edge.make_model(module, args.resolution)
        rigid = edge.rigid_modes(model, debug)
        # ponytail: the declared opening clears the timber bore, so reuse contact.
        edge.require(model["family"]["inner_radius_mm"] >= WOOD_BORE_RADIUS,
                     "washer foundation would include unsupported timber bore")
        coupon = edge.coupon(model, rigid, debug)
        debug = {}
        state, fields = edge.solve_state(model, source, debug)
        state["elastic_proxy_over_assumed_Fy"] = state["sampled_stress_peak_witness"]["sampled_through_thickness_maximum_proxy_mpa"] / module.FY_HYPOTHESIS
        module.authenticate(pins)
    except (ValueError, RuntimeError, OSError, np.linalg.LinAlgError) as error:
        failure = {"error": str(error), "last_accepted_state": debug, "physical_incompatibility_proved": False}
    if fields:
        with (output / "fields.csv").open("w", newline="") as stream:
            module.csv_rows(stream, fields)
    result = {
        "schema": "retail_thick_washer_current_end/v1", "status": "STOP" if failure else "FINITE_RETAIL_WASHER_HYPOTHESIS",
        "product": PRODUCT, "resolution": args.resolution, "source": source,
        "state": state, "failure": failure, "engineering_coupon": coupon,
        "rigid_mode_diagnostics": rigid, "nominal_wood_support": support,
        "model": {"family": module.FAMILIES["rail"], "resolution": edge.RESOLUTIONS[args.resolution],
                  "E_mpa_hypothesis": module.ESTEEL, "nu_hypothesis": module.NU,
                  "Fy_mpa_hypothesis": module.FY_HYPOTHESIS, "Kwood_mpa_per_mm_hypothesis": module.KWOOD,
                  "Khead_mpa_per_mm_hypothesis": module.KHEAD,
                  "wood_contact": "washer opening radius 4.1529 mm exceeds timber bore radius 3.75 mm; nominal backed annulus only",
                  "head_contact": "concentric radius 5 mm circle outside declared analytical washer opening; compression only",
                  "primary_energy_source": module.ENERGY_SOURCE},
        "limits": [
            "Retail nominal OD and lowest listed nominal thickness plus declared generic 8.3058 mm opening are hypotheses, not a measured part or supplier tolerance guarantee.",
            "The retail thickness fields conflict; numerical steel yield is unlisted. Generic 250 MPa is only a comparison input.",
            "The saved finished face and every trimmed bore support the declared concentric annulus; loaded shift/tilt and actual washer/head fillet fit are not established.",
            "Plate mechanics exclude contact-edge 3D stresses, sigmaZZ, plasticity, preload, friction and membrane/geometric nonlinearity.",
            "This thicker plate has less separation between thickness and radial span than the original thin washer; the inherited approximation is a screening method.",
            "The same current simultaneous T/M is prescribed. Changed contact compliance and thickness are not fed back into joint/frame response.",
            "Coarse/fine and known-answer coupons do not establish an actual product capacity, complete joint acceptance or physical release.",
        ],
        "source_sha256": {str(path.relative_to(ROOT)): digest for path, digest in sorted(pins.items())},
        "actual_washer_stress_mpa": None, "actual_washer_capacity_n": None,
        "complete_joint_acceptance": False, "physical_release": False,
    }
    hashes = {path.name: edge.sha(path) for path in output.iterdir()}
    result["output_sha256"] = hashes.copy()
    module.dump(output / "checks.json", result)
    hashes["checks.json"] = edge.sha(output / "checks.json")
    module.dump(output / "source-pins.json", {"source_sha256": result["source_sha256"], "output_sha256": hashes})
    module.authenticate(pins)
    print(json.dumps({"status": result["status"], "resolution": args.resolution, "checks_sha256": hashes["checks.json"]}))
    if failure:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
