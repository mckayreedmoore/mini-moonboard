"""Prepare or run the finite 48-end retail washer suite; mechanics belong to the parent."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
RETAIL = HERE / "retail-washer.py"
EDGE = HERE / "upper-right-washer-edge.py"
TIMBER = HERE / "rawlocal/corner-timber-sections/attempt02/checks.json"
BASELINE = HERE / "rawlocal/retail-washer/attempt02-fine/checks.json"
BASELINE_PINS = BASELINE.with_name("source-pins.json")
OUTPUT_ROOT = HERE / "rawlocal/retail-washer-suite"
PINS = {
    RETAIL: "894608d5abc879e3d679e8149cbf181c0cda224f2fbb164a0cbdb06f882e246f",
    EDGE: "ffe3db3e8c707851d44f0c60c43e6e6ef4aa4845f753dc6880c64186e3c75e61",
    TIMBER: "8b954edf5743999f427d2b99fcaaf9288578f02dc59a5cf1e632da634aa2e813",
    BASELINE: "c920d85bfdab7a9cbc802a0e4f79f817e2ac68fe8dfaf4ab1f50aa31d8dec5ae",
    BASELINE_PINS: "71e348c521af93f56a0d7941028ec0ac487a8d379692ca12e20029a7089fa355",
}
GATES = {"formal_acceptance": False, "complete_joint_acceptance": False, "physical_release": False}


def imported(path, name):
    sys.dont_write_bytecode = True
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ValueError(f"helper unavailable: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def cleat_support(edge, geometry, source):
    """Read the frozen rectangular exterior land and its saved bore bounds."""
    rows = np.array(geometry["grain_frame_rows_xyz"])
    local = rows @ (np.array(source["nominal_outer_wood_seat_xyz_mm"]) - geometry["start_xyz_mm"])
    width, depth = geometry["width_depth_mm"]
    bounds = np.array([[0.0, -width / 2], [geometry["grain_length_mm"], width / 2]])
    edge.require(np.allclose(rows @ rows.T, np.eye(3), atol=1e-8, rtol=0), "saved cleat frame differs")
    edge.require(abs(abs(local[2]) - depth / 2) < 1e-5, "seat is not on the frozen cleat exterior")
    radius, inner = 12.7, 4.1529
    distances = np.r_[local[:2] - bounds[0], bounds[1] - local[:2]]
    edge.require(min(distances) >= radius, "retail disk leaves frozen cleat rectangle")
    own, holes, absent = [], [], []
    for bore in geometry["bores"]:
        if bore["removed_interval_axis"] == 1:
            distance = float(np.linalg.norm(local[:2] - [bore["station_mm"], bore["transverse_center_mm"]]))
            if bore["axis_id"] == source["axis_id"]:
                edge.require(distance < 1e-5 and bore["radius_mm"] <= inner, "own cleat bore differs")
                own.append(bore)
            else:
                clearance = distance - radius - bore["radius_mm"]
                edge.require(clearance >= 0, "other cleat bore enters retail disk")
                holes.append({**bore, "center_distance_mm": distance, "clearance_from_outer_disk_mm": clearance})
        else:
            edge.require(bore["removed_interval_axis"] == 2, "unknown frozen bore direction")
            clearance = abs(local[2] - bore["transverse_center_mm"]) - bore["radius_mm"]
            edge.require(clearance > 0, "orthogonal bore reaches exterior; no new geometry extraction authorized")
            absent.append({**bore, "clearance_from_seat_plane_mm": float(clearance)})
    edge.require(len(own) == 1 and len(holes) == 1 and len(absent) == 2, "cleat face bore census differs")
    return {"receiver": geometry["block"], "geometry_source_sha256": PINS[TIMBER],
            "saved_geometry": geometry, "axis_local_mm": local.tolist(), "supported_rectangle_bounds_mm": bounds.tolist(),
            "edge_distances_mm": distances.tolist(), "minimum_outer_disk_edge_margin_mm": float(min(distances) - radius),
            "own_saved_bore_radius_mm": own[0]["radius_mm"], "other_face_holes": holes,
            "minimum_other_bore_clearance_mm": min(h["clearance_from_outer_disk_mm"] for h in holes),
            "bores_not_intersecting_exterior": absent, "nominal_supported_annulus_area_mm2": math.pi * (radius**2 - inner**2),
            "scope": "Frozen corrected rectangular timber and four saved through bores; concentric nominal land only."}


def build():
    """Authenticate inputs and prepare records/supports, without assembling or solving mechanics."""
    pins = {**PINS, Path(__file__).resolve(): hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
    for path, digest in pins.items():
        if hashlib.sha256(path.read_bytes()).hexdigest() != digest:
            raise ValueError(f"source pin differs: {path}")
    edge, retail = imported(EDGE, "suite_edge"), imported(RETAIL, "suite_retail")
    module, witness, inherited = retail.load(edge)
    for path, digest in inherited.items():
        edge.require(path not in pins or pins[path] == digest, f"conflicting pin: {path}")
        pins[path] = digest
    timber, baseline, receipt = (json.loads(p.read_text()) for p in (TIMBER, BASELINE, BASELINE_PINS))
    for document in (timber, receipt):
        for relative, digest in document["source_sha256"].items():
            path = ROOT / relative
            edge.require(path not in pins or pins[path] == digest, f"conflicting pin: {path}")
            pins[path] = digest
    for name, digest in receipt["output_sha256"].items():
        pins[BASELINE.parent / name] = digest
    module.authenticate(pins)
    current = json.loads(retail.CURRENT.read_text())
    edge.require(timber["source_first_order_sha256"] == retail.PINS[retail.CURRENT], "cleat geometry leaves current source")
    edge.require(baseline["failure"] is None and baseline["resolution"] == "fine", "fine baseline incomplete")
    settings = {"family": module.FAMILIES["rail"], "resolution": edge.RESOLUTIONS["fine"],
                **{k: getattr(module, attr) for k, attr in (("E_mpa_hypothesis", "ESTEEL"), ("nu_hypothesis", "NU"),
                   ("Fy_mpa_hypothesis", "FY_HYPOTHESIS"), ("Kwood_mpa_per_mm_hypothesis", "KWOOD"), ("Khead_mpa_per_mm_hypothesis", "KHEAD"))}}
    edge.require(all(settings[k] == baseline["model"][k] for k in settings), "fixed retail model or fine resolution differs")
    edge.require(settings["family"] == {"inner_radius_mm": 4.1529, "outer_radius_mm": 12.7, "head_radius_mm": 5.0, "thickness_mm": 2.5}, "retail annulus differs")
    records, supports, ties = [], {}, set()
    for state in current["states"]:
        host = state["hosts"]["base_rail_top"]
        edge.require(len(host["state"]["bolts"]) == 2, "rail bolt census differs")
        for bolt in host["state"]["bolts"]:
            edge.require(bolt["compatible_T_n"] > 0, "unsupported zero-tension/contact state; no fabricated success")
            axis = bolt["axis_id"]
            ties.add((state["case_id"], axis))
            edge.require(len(bolt["end_contacts"]) == 2, "one tie must retain two distinct ends")
            for index, (role, seat_role) in enumerate((("host", "host_head"), ("cleat", "cleat_nut"))):
                contact = bolt["end_contacts"][index]
                seat = [s for s in host["wood_seat_recovery"] if s["axis_id"] == axis and s["end"] == seat_role]
                edge.require(len(seat) == 1, "physical exterior seat is not unique")
                moment = bolt["end_moment_vectors_in_transverse_basis_nmm"][index]
                edge.require(math.isclose(float(np.linalg.norm(moment)), contact["moment_nmm"], abs_tol=1e-7, rel_tol=0), "signed own-end moment differs")
                source = {"state_id": f"{state['case_id']}/{axis}/{role}", "case_id": state["case_id"], "side": state["side"],
                          "axis_id": axis, "axial_tie_row_id": f"{axis}/outer-seat-axial-tie", "end_role": role, "end_index": index, "family": "rail", "T_n": bolt["compatible_T_n"],
                          "M_magnitude_nmm": contact["moment_nmm"], "eccentricity_M_over_T_mm": contact["moment_nmm"] / bolt["compatible_T_n"],
                          "source_current_checks_sha256": retail.PINS[retail.CURRENT], "saved_rigid_contact": contact,
                          "source_signed_M_vector_in_pair_basis_nmm": moment,
                          "source_signed_slope_vector_in_pair_basis_rad": bolt["end_slope_vectors_rad"][index],
                          "source_moment_on_beam_xyz_nmm": contact["moment_on_beam_xyz_nmm"],
                          "source_signed_pressure_frame_columns_xyz": seat[0]["signed_pressure_frame_columns_xyz"],
                          "source_bolt_axis_head_to_nut_xyz": bolt["bolt_axis_head_to_nut_xyz"],
                          "nominal_outer_wood_seat_xyz_mm": seat[0]["nominal_outer_wood_seat_xyz_mm"], "support_id": f"{axis}/{role}"}
                if source["support_id"] not in supports:
                    if role == "host":
                        retail.AXIS_ID = axis
                        support = retail.nominal_support(edge, pins)
                        edge.require(np.allclose(np.array(source["nominal_outer_wood_seat_xyz_mm"]) @ np.array(support["basis_global_xyz"]), support["axis_local_mm"], atol=1e-5, rtol=0), "physical host seat leaves finished-face record")
                    else:
                        support = cleat_support(edge, timber["geometry"][state["side"]], source)
                    supports[source["support_id"]] = {**support, "axis_id": axis, "end_role": role, "seat_xyz_mm": source["nominal_outer_wood_seat_xyz_mm"]}
                edge.require(supports[source["support_id"]]["seat_xyz_mm"] == source["nominal_outer_wood_seat_xyz_mm"], "seat changes across nominal cases")
                records.append(source)
    edge.require(len(records) == len({r["state_id"] for r in records}) == 48 and len(ties) == 24 and len(supports) == 8, "finite suite census differs")
    edge.require(set(module.CASES) == {r["case_id"] for r in records} and len({r["axis_id"] for r in records}) == 4, "case/axis inventory differs")
    reproduced = next(r for r in records if r["state_id"] == witness["state_id"])
    edge.require({k: reproduced[k] for k in witness} == witness == baseline["source"], "host witness is not the exact baseline source")
    module.authenticate(pins)
    return {"edge": edge, "module": module, "records": records, "supports": supports, "pins": pins,
            "baseline": baseline, "baseline_receipt": receipt, "settings": settings}


def preflight(prepared=None):
    """Return a serializable, read-only plan; this does not call any mechanics helper."""
    p = prepared if prepared is not None else build()
    return {"schema": "retail_washer_48_end_preflight/v1", "status": "PREPARED_NOT_EXECUTED", "end_records": p["records"],
            "nominal_support_inventory": p["supports"], "model": p["settings"], "source_sha256": {str(k): v for k, v in sorted(p["pins"].items())},
            "counts": {"end_states": 48, "nominal_cases": 6, "rail_bolts": 4, "exterior_seat_lands": 8, "coupons_requested": 1},
            "maximum_T_source": max(p["records"], key=lambda r: r["T_n"]), "maximum_M_source": max(p["records"], key=lambda r: r["M_magnitude_nmm"]),
            "maximum_eccentricity_source": max(p["records"], key=lambda r: r["eccentricity_M_over_T_mm"]), **GATES}


def metrics(state):
    return {"sampled_stress_proxy_mpa": state["sampled_stress_peak_witness"]["sampled_through_thickness_maximum_proxy_mpa"],
            "elastic_proxy_over_assumed_Fy": state["elastic_proxy_over_assumed_Fy"],
            "wood_pressure_peak_mpa": state["contact_balances"][0]["pressure_peak_mpa"],
            "head_pressure_peak_mpa": state["contact_balances"][1]["pressure_peak_mpa"],
            "absolute_head_closure_mm": abs(state["head_closure_mm"]), "head_tilt_magnitude_rad": float(np.linalg.norm(state["head_tilt_components_rad"])),
            "sampled_absolute_deflection_mm": abs(state["sampled_deflection_peak_witness"]["w_mm"]),
            "non_affine_w_weighted_rms_mm": state["non_affine_w_weighted_rms_mm"], "scaled_gradient_maximum_n": state["scaled_gradient_maximum_n"]}


def run(output):
    """Parent-only serialized execution: one model/coupon, 48 separate same-state ends."""
    output = Path(output).resolve()
    if output.parent != OUTPUT_ROOT.resolve() or output.exists():
        raise ValueError(f"output must be a fresh immediate child of {OUTPUT_ROOT}: {output}")
    p = build()
    edge, module, plan = p["edge"], p["module"], preflight(p)
    output.mkdir(parents=True, exist_ok=False)
    (output / ".gitignore").write_text("*\n")
    (output / "producer.py.snapshot").write_bytes(Path(__file__).read_bytes())
    module.dump(output / "inputs-before.json", plan)
    snapshots = output / "input-snapshots"
    snapshots.mkdir()
    snapshot_manifest = {}
    for i, (path, digest) in enumerate(sorted(p["pins"].items())):
        if path.suffix == ".py" or path in (TIMBER, BASELINE, BASELINE_PINS, HERE / "rawlocal/corner-first-order/attempt01/checks.json"):
            saved = snapshots / f"{i:02d}-{path.name}"
            saved.write_bytes(path.read_bytes())
            edge.require(edge.sha(saved) == digest, f"snapshot differs: {path}")
            snapshot_manifest[str(saved.relative_to(output))] = {"source": str(path), "sha256": digest}
    module.dump(output / "snapshot-manifest.json", snapshot_manifest)
    model, modes, coupon, setup_failure, debug = None, None, None, None, {}
    try:
        model = edge.make_model(module, "fine")
        edge.require(model["family"]["inner_radius_mm"] >= 3.75, "wood foundation credits unsupported bore")
        modes = edge.rigid_modes(model, debug)
        coupon = edge.coupon(model, modes, debug)
    except (ValueError, RuntimeError, OSError, np.linalg.LinAlgError) as error:
        setup_failure = {"error": str(error), "last_accepted_state": debug, "physical_incompatibility_proved": False}
    ends, completed, comparison = [], [], None
    for i, source in enumerate(p["records"]):
        folder = output / f"end-{i:02d}"
        folder.mkdir()
        state, fields, failure, debug = None, None, setup_failure, {}
        if setup_failure is None:
            try:
                edge.STATE_ID = source["state_id"]
                state, fields = edge.solve_state(model, source, debug)
                state["elastic_proxy_over_assumed_Fy"] = state["sampled_stress_peak_witness"]["sampled_through_thickness_maximum_proxy_mpa"] / module.FY_HYPOTHESIS
                state.update(GATES)
            except (ValueError, RuntimeError, OSError, np.linalg.LinAlgError) as error:
                failure = {"error": str(error), "last_accepted_state": debug, "physical_incompatibility_proved": False}
                if "scaled_variables_mm" in debug:
                    fields, partial = edge.recover_fields(model, np.array(debug["scaled_variables_mm"]))
                    failure["partial_sampled_fields"] = partial
        if fields:
            with (folder / "fields.csv").open("w", newline="") as stream:
                module.csv_rows(stream, fields)
        if state is not None:
            completed.append({"state_id": source["state_id"], "source": source, "metrics": metrics(state)})
        module.dump(folder / "checks.json", {"source": source, "status": "STOP" if failure else "FINITE_RETAIL_WASHER_HYPOTHESIS", "state": state, "failure": failure, **GATES})
        ends.append({"state_id": source["state_id"], "status": "STOP" if failure else "FINITE_RETAIL_WASHER_HYPOTHESIS", "checks": str((folder / "checks.json").relative_to(output))})
        if source["state_id"] == p["baseline"]["source"]["state_id"]:
            comparison = {"state_id": source["state_id"], "source_exact": {k: source[k] for k in p["baseline"]["source"]} == p["baseline"]["source"],
                          "state_exact_on_every_baseline_key": state is not None and {k: state[k] for k in p["baseline"]["state"]} == p["baseline"]["state"],
                          "fields_csv_sha256_exact": fields is not None and edge.sha(folder / "fields.csv") == p["baseline_receipt"]["output_sha256"]["fields.csv"],
                          "coupon_exact": coupon == p["baseline"]["engineering_coupon"],
                          "metric_deltas": {k: v - metrics(p["baseline"]["state"])[k] for k, v in metrics(state).items()} if state else None}
        print(json.dumps({"end": i + 1, "of": 48, **ends[-1]}), flush=True)
    after = {str(path): edge.sha(path) for path in sorted(p["pins"])}
    module.dump(output / "inputs-after.json", {"source_sha256": after, "source_pins_unchanged": after == plan["source_sha256"]})
    unchanged = after == plan["source_sha256"]
    exact = comparison is not None and all(comparison[k] for k in ("source_exact", "state_exact_on_every_baseline_key", "fields_csv_sha256_exact", "coupon_exact"))
    status = "FINITE_RETAIL_WASHER_SUITE_HYPOTHESIS" if len(completed) == 48 and unchanged and exact else "STOP"
    envelopes = {k: max(completed, key=lambda r: r["metrics"][k]) for k in completed[0]["metrics"]} if completed else {}
    result = {"schema": "retail_washer_48_end_suite/v1", "status": status, "counts": {**plan["counts"], "completed_end_states": len(completed), "completed_coupons": int(coupon is not None)},
              "ends": ends, "engineering_coupon": coupon, "rigid_mode_diagnostics": modes, "setup_failure": setup_failure,
              "model": p["baseline"]["model"], "runtime": {"python": sys.version.split()[0], "numpy": np.__version__, "scipy": edge.scipy.__version__},
              "baseline_exact_comparison": comparison, "maximum_envelopes": envelopes, "envelope_covers_all_48": len(completed) == 48,
              "source_pins_unchanged": unchanged, "source_sha256": plan["source_sha256"], "nominal_support_inventory": p["supports"],
              "limits": p["baseline"]["limits"] + ["Each envelope retains its own simultaneous end source; independent maxima are not combined into a fabricated state.",
                  "Signed vectors and physical pressure frames are retained. The inherited circular plate uses the own-end moment-aligned magnitude drive.",
                  "An incomplete suite supplies only a partial envelope. Numerical stops do not prove physical incompatibility; no retry or stiffness is added."],
              "actual_washer_stress_mpa": None, "actual_washer_capacity_n": None, **GATES}
    module.dump(output / "checks.json", result)
    module.dump(output / "source-pins.json", {"source_sha256": plan["source_sha256"], "output_sha256": {str(f.relative_to(output)): edge.sha(f) for f in sorted(output.rglob("*")) if f.is_file()}, **GATES})
    module.authenticate(p["pins"])
    print(json.dumps({"status": status, "checks_sha256": edge.sha(output / "checks.json")}), flush=True)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--preflight", action="store_true", help="authenticate and print the plan without mechanics or output writes")
    parser.add_argument("--output", type=Path, help="fresh immediate child of rawlocal/retail-washer-suite")
    args = parser.parse_args()
    if args.preflight:
        print(json.dumps(preflight(), indent=2))
    else:
        if args.output is None:
            parser.error("--output is required for parent execution")
        if run(args.output)["status"] == "STOP":
            raise SystemExit(1)


if __name__ == "__main__":
    main()
