"""Bind twelve end-grain references and a separate stock/grain proposal.

Read the selected saved nominal-gap forces only. Do not solve, import STEP,
change source geometry/materials, or establish adjusted joint resistance.
"""

import argparse
import sys

sys.dont_write_bytecode = True

from collections import defaultdict
from pathlib import Path

import frame_state_contract as frame_contract
import numpy as np
import remaining_joint_screen as screen

HERE, ROOT = screen.HERE, screen.ROOT
FRAME = screen.FRAME
DEFAULT_CLEARANCE = HERE / "top-and-service-frame-attempt02"
DEFAULT_OUTPUT = HERE / "end-grain-route-attempt01"
FEATURES = HERE.parent / "current-finished-feature-register-2026-10-01/surfaces.json"
CLEARANCE_PINS = {
    "top-and-service-frame-attempt02": {
        "comparison.json": "4aa32390c80f803faee4fceeb6460c05b665dd8e970beaef89b40985b0b9555b",
        "response.npz": "227b9381a6ff19286ba4b46c81bc5852bb3b536735ac5c74f727f6869a5f40d6",
    },
    "all-outer-corner-frame-attempt01": {
        "comparison.json": "ec69b49c821a56fdde76d94148405f9f743e4f72add17c89d35af512be76f6a3",
        "response.npz": "aa70480aa18c33bb1cbd7d3a53ff582a0c7a90c93487f92721619474ec251901",
    },
}
PINS = {
    FEATURES: "33fff67eee4bc4e96ccef5703f6eebd0d4e004541c6114a4b1da4a5332b2f6eb",
    screen.local.actions_method.MATERIALS: "0f33ad8fd517673a4ebbed36c4a30c1cfe07e0d8163165bdc804af91d958fc5a",
    **screen.lateral.PINS,
    **screen.local.PINS,
}
read, require, sha, unit = screen.read, screen.require, screen.sha, screen.local.unit
CASES = screen.CASES
FYB = {"45ksi": 45000, "92ksi": 92000, "106ksi": 106000}
CEG, D = 0.67, 6.35
PROPOSED_GRAIN = np.array([0.0, 1.0, 0.0])


def main(clearance=DEFAULT_CLEARANCE, output=DEFAULT_OUTPUT, *, frame_dir=FRAME,
         metadata_seed_dir=None):
    source = screen.bind_frame_sources(frame_dir, clearance, metadata_seed_dir)
    FRAME, RESPONSE, OUTPUT = source["frame_dir"], source["clearance_dir"], output.resolve()
    require(
        OUTPUT.is_relative_to(HERE)
        and OUTPUT.relative_to(HERE).parts
        and OUTPUT.relative_to(HERE).parts[0].startswith("end-grain-route-attempt"),
        "output must be inside an end-grain-route-attempt directory",
    )
    require(not OUTPUT.exists(), "preserve the recorded output; attempt already exists")
    comparison, force_scope = source["comparison"], source["force_scope"]
    expected = CLEARANCE_PINS.get(RESPONSE.name, {})
    pins = {
        **PINS,
        **source["pins"],
        Path(__file__): sha(Path(__file__)),
        RESPONSE / "comparison.json": expected.get("comparison.json", sha(RESPONSE / "comparison.json")),
        RESPONSE / "response.npz": expected.get("response.npz", comparison["response_sha256"]),
    }
    for path in (HERE / "lateral_reference.py", HERE / "top_corner_local.py"):
        pins[path] = comparison["source_sha256"][str(path.relative_to(ROOT))]
    require(comparison["response_sha256"] == pins[RESPONSE / "response.npz"], "mixed response")
    require(comparison["schema"] in ("coupled_top_and_service_frame_clearance/v1", "coupled_outer_corner_frame_clearance/v1", frame_contract.BOUNDED_SCHEMA), "wrong frame scope")
    require(
        len(comparison["states"]) == 12
        and {(s["case_id"], s["gap_scale"]) for s in comparison["states"]}
        == {(c, g) for c in CASES for g in (0.0, 1.0)}
        ,
        "missing or failed saved frame states",
    )
    inputs, model = read(screen.lateral.INPUTS), source["model"]
    require(inputs["revision_id"] == model["source_revision"], "mixed geometry revision")
    require(inputs["candidate"] == model["candidate"], "mixed candidate")
    members = {m["member_id"]: m["reduced_geometry_descriptor"] for m in inputs["members"] if m["member_kind"] != "panel"}
    bolts = {b["axis_id"]: b for b in inputs["connections"] if b["kind"] == "candidate_bolt"}
    end_grain = {}
    for axis, bolt in bolts.items():
        if len(bolt["receiver_member_ids"]) != 2:
            continue
        parallel = [b for b in bolt["receiver_member_ids"] if abs(unit(bolt["axis_xyz"]) @ unit(members[b]["axis"])) > 1 - 1e-8]
        if parallel:
            require(len(parallel) == 1 and "base_header" in bolt["receiver_member_ids"], "end-grain census changed")
            end_grain[axis] = parallel[0]
    blocks = set(end_grain.values())
    require(len(end_grain) == 12 and len(blocks) == 6, "expected twelve axes in six blocks")
    for body in blocks | {"base_header"}:
        descriptor = members[body]
        orientation = model["material_binding"]["orientation_overrides"][body]["material_axes_global_xyz"]["L"]
        require(abs(unit(orientation) @ unit(descriptor["axis"])) > 1 - 1e-8, "source material grain differs")
        pins[ROOT / descriptor["step_path"]] = descriptor["step_sha256"]
    material = read(screen.local.actions_method.MATERIALS)
    require(material["conditional_DF_L_No2_base_row"]["base_properties"]["G_for_dowel_bearing"] == 0.5, "species scenario changed")
    require(read(screen.local.FASTENERS)["material_boundaries"]["sae_j429_grade5_1_4_through_1_in"]["machine_test_yield_ksi_min"] * 1000 == FYB["92ksi"], "Grade 5 scenario changed")
    for path, digest in pins.items():
        require(sha(path) == digest, "changed consumed source: " + str(path))

    rows = source["rows"]
    require(len(rows) == 1888 and [r["row"] for r in rows] == list(range(1888)), "row order changed")
    planes, ties = defaultdict(list), {}
    for row in rows:
        axis = row["row_id"].rsplit("/", 1)[0]
        if axis not in end_grain:
            continue
        if row["ownership"]["role"] == "candidate_bolt_lateral_plane":
            planes[axis].append(row)
        elif row["ownership"]["role"] == "physical_bolt_outer_seat_tension":
            require(axis not in ties and row["law"]["intended_law"] == "tension_only", "invalid outer tie")
            ties[axis] = row
    require(set(planes) == set(ties) == set(end_grain), "incomplete force census")

    features = {r["member_id"]: r for r in read(FEATURES)["records"]}
    stock, bounds = [], {}
    for block in sorted(blocks):
        record, descriptor = features[block], members[block]
        require(record["step_binding"]["file_sha256"] == descriptor["step_sha256"], "finished bounds binding differs")
        boxes = np.array([f["bounds_global_xyz_mm"] for f in record["features"]])
        lo, hi = boxes[:, ::2].min(axis=0), boxes[:, 1::2].max(axis=0)
        size = hi - lo
        require(np.max(abs(unit(descriptor["axis"]) - [0, 0, 1])) < 1e-8, "unexpected stock orientation")
        require(np.max(abs(size - [descriptor["width_mm"], descriptor["depth_mm"], descriptor["length_mm"]])) < 1e-6, "finished envelope differs")
        require(size[0] <= 88.9 + 1e-6 and size[2] <= 139.7 + 1e-6, "Y-grain blank does not fit nominal 4x6")
        bounds[block] = (lo, hi)
        stock.append({
            "member_id": block, "finished_xyz_envelope_mm": size.tolist(),
            "bounds_xyz_mm": [lo.tolist(), hi.tolist()], "current_grain_xyz": [0, 0, 1],
            "proposed_grain_xyz": PROPOSED_GRAIN.tolist(),
            "nominal_4x6_actual_cross_section_xz_mm": [88.9, 139.7],
            "minimum_finished_along_grain_cut_y_mm": float(size[1]),
            "transverse_total_trim_xz_mm": [float(88.9 - size[0]), float(139.7 - size[2])],
            "stock_fit": True, "grade_scenario": "conditional DF-L No.2; final piece condition unobserved",
        })

    affected = []
    for axis, bolt in sorted(bolts.items()):
        touched = blocks.intersection(bolt["receiver_member_ids"])
        if not touched:
            continue
        block = next(iter(touched))
        require(len(touched) == 1, "two proposed blocks on one bolt")
        direction = unit(bolt["axis_xyz"])
        require(abs(direction @ PROPOSED_GRAIN) < 1e-8, "proposal creates another end-grain axis")
        lo, hi = bounds[block]
        y = bolt["source_point_xyz_mm"][1]
        affected.append({
            "axis_id": axis, "reoriented_receiver": block,
            "receiver_count": len(bolt["receiver_member_ids"]), "axis_xyz": direction.tolist(),
            "receiver_grain_directions": [{
                "member_id": b, "current_grain_xyz": unit(members[b]["axis"]).tolist(),
                "proposed_grain_xyz": (PROPOSED_GRAIN if b == block else unit(members[b]["axis"])).tolist(),
                "current_bolt_grain_abs_dot": float(abs(direction @ unit(members[b]["axis"]))),
                "proposed_bolt_grain_abs_dot": float(abs(direction @ (PROPOSED_GRAIN if b == block else unit(members[b]["axis"])))),
            } for b in bolt["receiver_member_ids"]],
            "proposed_block_minus_plus_grain_end_distances_mm": [float(y - lo[1]), float(hi[1] - y)],
            "perpendicular_bolt_after_proposal": True,
            "method_limit": "asymmetric three-receiver bolt remains separate" if len(bolt["receiver_member_ids"]) == 3 else "two-receiver lateral reference only",
        })
    require(len(affected) == 24, "affected bolt census changed")
    axis_geometry = {r["axis_id"]: r for r in affected}

    records, knee_comparators = [], []
    with np.load(RESPONSE / "response.npz", allow_pickle=False) as data:
        for case in CASES:
            force = data[case + "_gap_raw_force_n"]
            require(force.shape == (1888,) and np.isfinite(force).all(), "invalid saved force")
            for axis, block in sorted(end_grain.items()):
                components, bolt, tie = planes[axis], bolts[axis], ties[axis]
                require(len(components) == 2, "expected one single-shear plane")
                own = components[0]["ownership"]
                require(all(r["row_id"] == components[0]["row_id"] and all(r["ownership"][k] == own[k] for k in ("first_body", "second_body", "point_mm")) for r in components), "mixed plane")
                require({own["first_body"], own["second_body"]} == set(bolt["receiver_member_ids"]), "foreign receiver")
                basis = np.array([r["ownership"]["direction_global_xyz"] for r in components])
                require(np.max(abs(basis @ basis.T - np.eye(2))) < 1e-8 and np.max(abs(basis @ unit(bolt["axis_xyz"]))) < 1e-8, "invalid lateral basis")
                values = force[[r["row"] for r in components]]
                shear = values @ basis
                block_shear = shear if own["first_body"] == block else -shear
                require(abs(block_shear @ unit(members[block]["axis"])) < 1e-7, "non-transverse end-grain force")
                tension = float(force[tie["row"]])
                require(tension >= -1e-8, "compressive tension-only tie")
                intervals = {r["receiver_id"]: r["current_shaft_intersection_solid_intervals_from_underhead_mm"] for r in bolt["source_record"]["geometry"]["wood_receiver_intervals"]}
                require(all(len(v) == 1 for v in intervals.values()) and set(intervals) == {block, "base_header"}, "ambiguous bearing intervals")
                lengths = [intervals[b][0][1] - intervals[b][0][0] for b in (block, "base_header")]
                require(abs(intervals[block][0][0] - intervals["base_header"][0][1]) < 1e-7 or abs(intervals["base_header"][0][0] - intervals[block][0][1]) < 1e-7, "nonzero interface gap")
                geometry = bolt["source_record"]["geometry"]
                require(abs(geometry["modeled_shaft_diameter_mm"] - D) < 1e-8, "bolt diameter differs")
                header_angle = screen.lateral.angle(shear, unit(members["base_header"]["axis"]))
                record = {
                    "case_id": case, "axis_id": axis, "plane_id": components[0]["row_id"],
                    "first_body": own["first_body"], "second_body": own["second_body"],
                    "component_rows": [r["row"] for r in components], "component_directions_xyz": basis.tolist(),
                    "signed_component_1_n": float(values[0]), "signed_component_2_n": float(values[1]),
                    "force_on_first_xyz_n": shear.tolist(), "force_on_second_xyz_n": (-shear).tolist(),
                    "force_on_end_grain_main_xyz_n": block_shear.tolist(),
                    "shear_resultant_n": float(np.linalg.norm(shear)), "outer_tie_row": tie["row"],
                    "outer_tie_signed_n": tension, "outer_tie_first_body": tie["ownership"]["first_body"],
                    "outer_tie_second_body": tie["ownership"]["second_body"], "outer_tie_direction_xyz": tie["ownership"]["direction_global_xyz"],
                    "main_member": block, "side_member": "base_header", "main_side_bearing_lengths_mm": lengths,
                    "main_side_load_grain_angles_deg": [90.0, header_angle], "main_Fe_psi": 4450.0,
                    "side_Fe_theta_psi": screen.lateral.bearing(header_angle), "Ceg": CEG,
                    "Cdelta_Cg_and_local_transfer_established": False,
                }
                for name, fyb in FYB.items():
                    ref = screen.lateral.reference(lengths, [90.0, header_angle], fyb)
                    z = ref["reference_lateral_lbf"] * screen.lateral.N_PER_LBF
                    record["yield_mode_" + name] = ref["governing_mode"]
                    record["six_mode_Z_n_" + name] = z
                    record["Ceg_Z_n_" + name] = CEG * z
                    record["V_over_Ceg_Z_" + name] = record["shear_resultant_n"] / (CEG * z)
                # The fallback keeps this saved force only as a diagnostic.
                ends = axis_geometry[axis]["proposed_block_minus_plus_grain_end_distances_mm"]
                record["proposed_Y_grain_end_distances_mm"] = ends
                record["proposed_Y_grain_conservative_7D_Cdelta_comparator"] = min(1.0, min(ends) / (7 * D))
                toward = (block_shear[1] < -1e-8 and ends[0] < 3.5 * D - 1e-6) or (block_shear[1] > 1e-8 and ends[1] < 3.5 * D - 1e-6)
                record["proposed_Y_grain_parallel_component_below_3_5D_comparator"] = bool(toward)
                if toward:
                    knee_comparators.append({"case_id": case, "axis_id": axis, "block_force_y_n": float(block_shear[1]), "toward_end_distance_mm": float(ends[0] if block_shear[1] < 0 else ends[1])})
                records.append(record)

    require(len(records) == 72, "end-grain saved-state census changed")
    for path, digest in pins.items():
        require(sha(path) == digest, "source changed during calculation: " + str(path))
    peaks = [max((r for r in records if r["axis_id"] == axis), key=lambda r: r["V_over_Ceg_Z_92ksi"]) for axis in sorted(end_grain)]
    result = {
        "schema": "current_end_grain_method_and_stock_proposal/v1",
        "candidate": model["candidate"], "source_revision": model["source_revision"],
        "development_revision": model["development_revision"],
        "status": "SUPPORTED_NDS_END_GRAIN_INDIVIDUAL_REFERENCE_WITH_UNRESOLVED_JOINT_DETAILING",
        "clearance_schema": comparison["schema"],
        "source_force_state_scope": force_scope,
        "frame_directory": str(FRAME.relative_to(ROOT)),
        "metadata_seed_directory": str(source["metadata_seed_dir"].relative_to(ROOT)),
        "metadata_seed_scope": "Case order and inherited seed provenance only; no old force vectors or acceptance transferred.",
        "clearance_joint_hosts": comparison["clearance_joint_hosts"],
        "force_source": str((RESPONSE / "response.npz").relative_to(ROOT)),
        "force_key": "case_id + '_gap_raw_force_n'", "gap_scale": 1.0,
        "case_ids": list(CASES), "axis_count": 12, "state_count": len(records),
        "clauses": ["NDS-2024 12.3.1 / Tables 12.3.1A-B", "12.3.3.4: end-grain main member Fe perpendicular", "12.3.4: side-member bearing angle", "12.3.5: bearing length", "12.5.2.2: Ceg=0.67", "12.3.9.1: separate axial bearing", "11.1.2-3 / 12.6.3: local/eccentric stresses"],
        "source_sha256": {str(p.relative_to(ROOT)): d for p, d in pins.items()},
        "producer_sha256": sha(Path(__file__)), "python_version": sys.version.split()[0], "numpy_version": np.__version__,
        "peaks_at_92ksi": peaks,
        "maximum_ratios": {name: max(r["V_over_Ceg_Z_" + name] for r in records) for name in FYB},
        "stock_proposal": stock, "affected_axes": affected,
        "stock_Y_grain_signed_parallel_component_comparators_below_3_5D": knee_comparators,
        "limits": [
            "Ceg is applied once after the minimum yield mode; these are not Z-prime joint resistances.",
            "45/92/106 ksi retain the parent's conditional Fyb hypotheses, not product-qualified bending capacities.",
            "Finished end/edge/spacing and Cdelta, Cg, splitting, washer, member, contact/couple and steel/axial checks are not completed here.",
            "Full smooth-body bearing diameter and zero adjacent-face gap are declared scenarios, not observations.",
            "NDS 12.4 lag/wood-screw withdrawal interaction is not applied to through bolts.",
            "Y-grain stock proposal changes six material orientations; saved forces are not forces for that changed stiffness model.",
            "3.5D/7D fallback comparisons are explicit parallel-component/conservative comparators, not an invented intermediate-angle NDS interpolation.",
            "Four continuous three-receiver companion bolts remain outside the two-member route.",
            force_scope["force_scope"],
            force_scope["motion_scope"],
        ],
        "native_solve_run": False, "frame_solve_run": False, "CAD_rebuilt": False,
        "tests_run": False, "review_run": False,
        "reviewed_geometry_changed": bool(model.get("owner_authorized_screw_movements")),
        "material_or_stiffness_changed": False, "complete_joint_acceptance": False, "physical_release": False,
    }
    OUTPUT.mkdir()
    (OUTPUT / ".gitignore").write_text("*\n")
    screen.write_csv(OUTPUT / "six-case-signed-states.csv", records)
    screen.write_json(OUTPUT / "stock-grain-proposal.json", {"members": stock, "affected_axes": affected, "signed_parallel_component_comparators": knee_comparators})
    (OUTPUT / "producer.py.snapshot").write_bytes(Path(__file__).read_bytes())
    result["output_sha256"] = {name: sha(OUTPUT / name) for name in ("six-case-signed-states.csv", "stock-grain-proposal.json", "producer.py.snapshot")}
    screen.write_json(OUTPUT / "route.json", result)
    print(f"{len(end_grain)} axes / {len(records)} states; supported end-grain component route, no complete joint acceptance.")
    print("Maximum V/(Ceg Z):", {k: round(v, 6) for k, v in result["maximum_ratios"].items()})
    print(f"Y-grain 4x6 envelopes fit all six blocks; {len(knee_comparators)} saved knee-state parallel-component placement comparators below 3.5D.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--frame", type=Path, default=FRAME,
                        help="Physical operator directory; defaults to the historical corrected frame.")
    parser.add_argument("--metadata-seed", type=Path,
                        help="Case metadata directory; defaults to --frame. No seed force arrays are consumed.")
    parser.add_argument("--clearance", type=Path, default=DEFAULT_CLEARANCE)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    main(args.clearance, args.output, frame_dir=args.frame,
         metadata_seed_dir=args.metadata_seed)
