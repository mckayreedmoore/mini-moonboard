"""Same-state timber action and elementary stress screens; no solve or CAD import.

Read the six NOMINAL-GAP responses and corrected physical load operator. Keep
complete signed point actions, free couples, cut wrenches, and whole-member
closure. Finished faces classify bore-free rectangular cuts; saved net sections
are retained only with a matching STEP binding and do not supply resistance.
"""

from __future__ import annotations

import argparse
import copy
import csv
import json
import sys
from pathlib import Path

sys.dont_write_bytecode = True

import numpy as np
import top_corner_actions as accounting

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
FRAME = HERE / "corner-frame-attempt01"
RESPONSE = HERE / "both-corner-frame-attempt01"
EVALUATION = HERE.parent / "evaluation-resume-2026-09-24"
FEATURES = HERE.parent / "current-finished-feature-register-2026-10-01"
BUNDLE = EVALUATION / "current-full-frame-member-solids-attempt01"
PROFILE = EVALUATION / "current-frame-beam-selfweight-profile-attempt01"
BEAM = EVALUATION / "current-frame-member-beam-selfweight-attempt01"
DOFS = (
    accounting.BASE
    / "current-frame-pure-solid-matrix-export-native-attempt01/model.dof"
)
PSI_MPA = 0.006894757293168361
TOL = 1e-5
sha, read, require = accounting.sha, accounting.read, accounting.require


def write(path, value):
    compact = path.name in ("geometry.json", "member-results.json")
    path.write_text(
        json.dumps(
            value,
            indent=None if compact else 2,
            separators=(",", ":") if compact else None,
            allow_nan=False,
        )
        + "\n"
    )


def basis(geometry):
    return np.array([geometry[k] for k in ("axis", "section_u", "section_v")])


def station_interval(feature, record, geometry):
    """Project saved finite face bounds; do not treat a global AABB as a section."""
    stock = record["stock_frame"]
    axis = np.array(stock["basis_columns_global_xyz"][0])
    grain = np.array(geometry["axis"])
    sign = float(axis @ grain)
    require(abs(abs(sign) - 1) < 1e-7, "stock and physical grain disagree")
    offset = float(
        grain @ (np.array(stock["origin_global_xyz_mm"]) - geometry["start"])
    )
    return sorted(offset + sign * x for x in feature["bounds_stock_gqr_mm"][:2])


def rectangle_at(station, geometry, planes, bores):
    """Use saved outward planes at bore-free cuts with axis-aligned boundaries.

    This is a bounded planar-profile interpretation, not a new BRep section.
    Blind-bore caps and every cylindrical patch block the elementary screen
    over their saved finite station bounds. Nonrectangular profiles are refused.
    """
    lo = np.array([-geometry["width_mm"] / 2, -geometry["depth_mm"] / 2])
    hi = -lo
    point = np.array(geometry["start"]) + station * np.array(geometry["axis"])
    frame = basis(geometry)
    blocked = [b["id"] for b in bores if b["lo"] - TOL <= station <= b["hi"] + TOL]
    if blocked:
        return {"status": "NON_APPLICABLE_BORE_OR_PASSAGE", "feature_ids": blocked}
    active = []
    sides = set()
    for plane in planes:
        if not plane["lo"] - TOL <= station <= plane["hi"] + TOL:
            continue
        normal = np.array(plane["normal"])
        n = frame @ normal
        transverse = n[1:]
        rhs = plane["offset"] - float(normal @ point)
        if np.max(abs(transverse)) < 1e-7:
            if rhs < -TOL:
                return {"status": "NON_APPLICABLE_OUTSIDE_FINISHED_PROFILE"}
            continue
        if np.min(abs(transverse)) > 1e-7:
            return {
                "status": "NON_APPLICABLE_NONRECTANGULAR_PROFILE",
                "feature_ids": [plane["id"]],
            }
        i = int(np.argmax(abs(transverse)))
        coordinate = rhs / transverse[i]
        if transverse[i] > 0:
            hi[i] = min(hi[i], coordinate)
            sides.add((i, 1))
        else:
            lo[i] = max(lo[i], coordinate)
            sides.add((i, -1))
        active.append(plane["id"])
    if len(sides) != 4 or np.min(hi - lo) <= TOL:
        return {"status": "NON_APPLICABLE_INCOMPLETE_OR_TERMINAL_PROFILE"}
    width, depth = hi - lo
    center = point + frame[1:].T @ ((lo + hi) / 2)
    full = np.max(abs((hi - lo) - [geometry["width_mm"], geometry["depth_mm"]])) < TOL
    result = {
        "status": "BORE_FREE_FULL_RECTANGLE" if full else "BORE_FREE_PROFILE_RECTANGLE",
        "width_depth_mm": [float(width), float(depth)],
        "bounds_uv_mm": [lo.tolist(), hi.tolist()],
        "centroid_xyz_mm": center.tolist(),
        "area_mm2": float(width * depth),
        "profile_face_ids": active,
        "geometry_scope": "Saved finite outward-plane interpretation; no CAD replay or continuous section authentication.",
    }
    if not full:
        # A point load at a clipped end stays finite as the actual slice tends
        # to zero area. These near-end ratios are not beam stress estimates.
        # Only the explicitly source-bound, full-depth 1:12 recess receives
        # reduced-section arithmetic in this member screen.
        recess = geometry.get("floor_recess_geometry")
        recess_rectangle = (
            recess is not None
            and abs(depth - geometry["depth_mm"]) < TOL
            and width >= abs(np.diff(recess["retained_x_band_mm"])[0]) - TOL
        )
        if not recess_rectangle:
            result["status"] = "NON_APPLICABLE_END_TRIM_POINT_LOAD_DISTRIBUTION"
            result["reason"] = (
                "Lumped member/end-point loads do not establish a traction field through the clipped terminal profile; no elementary stress ratio is assigned."
            )
    return result


def reference_values(body, geometry, materials):
    material = next(m for m in materials["members"] if m["member_id"] == body)
    factors = material["code_Table4A_CF"]
    scenario = "conditional_DF-L_No2_standard_section_CF_only"
    if body in accounting.BLOCK_HOSTS:
        factors = materials["standard_section_scenarios"]["nominal_4x6"]["CF"]
        scenario = "corrected_full_4x6_DF-L_No2_CF_only"
        require(
            np.max(
                abs(
                    np.array([geometry["width_mm"], geometry["depth_mm"]])
                    - [88.9, 139.7]
                )
            )
            < TOL,
            "corrected cleat dimensions changed",
        )
    if factors is None:
        study = next(
            s for s in materials["ripped_section_scenarios"] if body in s["member_ids"]
        )
        factors = dict.fromkeys(
            ("Fb", "Ft_parallel", "Fc_parallel"), study["study_only_CF"]
        )
        scenario = study["scenario_id"]
    base = materials["conditional_DF_L_No2_base_row"]["base_properties"]
    values = {
        key: base[key] * factors.get(key, 1) * PSI_MPA
        for key in ("Fb", "Ft_parallel", "Fc_parallel", "Fv_parallel")
    }
    return {
        "scenario": scenario,
        "CF": factors,
        "CF_only_reference_mpa": values,
        "other_factor_scenario": "Normal duration, dry service, unincised and normal temperature; Cfu=Cr=1; CL and CP are not calculated or credited.",
        "design_resistance_established": False,
    }


def stresses(value, width, depth, references):
    """N is positive in tension on the negative half's outward +grain cut."""
    n, vu, vv, torque, mu, mv = value
    area = width * depth
    axial = n / area
    bu, bv = 6 * abs(mu) / (width * depth**2), 6 * abs(mv) / (depth * width**2)
    bending = bu + bv
    shear_u, shear_v = 1.5 * abs(vu) / area, 1.5 * abs(vv) / area
    ref = references["CF_only_reference_mpa"]
    tension = max(axial, 0) / ref["Ft_parallel"]
    compression = max(-axial, 0) / ref["Fc_parallel"]
    bending_ratio = bending / ref["Fb"]
    return {
        "signed_mean_parallel_stress_mpa": float(axial),
        "bending_Mu_extreme_mpa": float(bu),
        "bending_Mv_extreme_mpa": float(bv),
        "biaxial_bending_extreme_sum_mpa": float(bending),
        "maximum_tension_extreme_mpa": float(max(0, axial + bending)),
        "maximum_compression_extreme_mpa": float(max(0, bending - axial)),
        "parallel_corner_stresses_mpa": [
            float(
                axial
                + mu * v / (width * depth**3 / 12)
                - mv * u / (depth * width**3 / 12)
            )
            for u, v in (
                (-width / 2, -depth / 2),
                (-width / 2, depth / 2),
                (width / 2, -depth / 2),
                (width / 2, depth / 2),
            )
        ],
        "rectangular_shear_u_mpa": float(shear_u),
        "rectangular_shear_v_mpa": float(shear_v),
        "rectangular_transverse_shear_component_sum_mpa": float(shear_u + shear_v),
        "axial_tension_over_reference": float(tension),
        "axial_compression_over_reference_without_stability": float(compression),
        "biaxial_bending_over_reference_without_stability": float(bending_ratio),
        "linear_normal_reference_sum": float(max(tension, compression) + bending_ratio),
        "transverse_shear_over_reference": float(
            (shear_u + shear_v) / ref["Fv_parallel"]
        ),
        "signed_torque_nmm_no_resistance": float(torque),
        "combined_NDS_design_utilization": None,
    }


def cut_vectors(actions, geometry, stations):
    """Vectorize the same point-action partition used by host_cut."""
    points = np.array([a["point_mm"] for a in actions])
    forces = np.array([a["force_n"] for a in actions])
    couples = np.array([a["free_moment_nmm"] for a in actions])
    source_stations = np.array([a["station_mm"] for a in actions])
    positions = np.repeat(stations, 2)
    before = np.tile([True, False], len(stations))
    delta = source_stations[None, :] - positions[:, None]
    positive = (delta > 1e-6) | (before[:, None] & (abs(delta) <= 1e-6))
    origin_wrenches = np.column_stack(
        [forces, np.cross(points - geometry["start"], forces) + couples]
    )
    plus = positive.astype(float) @ origin_wrenches
    minus = origin_wrenches.sum(axis=0) - plus
    shift = positions[:, None] * np.array(geometry["axis"])
    plus[:, 3:] -= np.cross(shift, plus[:, :3])
    minus[:, 3:] -= np.cross(shift, minus[:, :3])
    return -minus, -plus, positions, before


def geometry_sources(model, revised, inputs, surfaces, correspondence, proposal):
    """Keep unchanged surfaces; substitute only the source-bound corrected bores."""
    descriptions = {r["member_id"]: r for r in inputs["members"]}
    timber = sorted(
        r["member_id"] for r in inputs["members"] if r["member_kind"] != "panel"
    )
    require(len(timber) == 44, "expected 44 timber members")
    model["nodes"] = revised["physical_node_coordinates_mm"]
    require(
        model["physical_body_nodes"] == revised["body_nodes"],
        "changed physical ownership",
    )
    original_surfaces = {r["member_id"]: r for r in surfaces["records"]}
    original_axes = {
        a["axis_id"]: a
        for a in correspondence["source_axis_groups"]["candidate_bolt_axes"]["axes"]
    }
    pins, records = {}, {}
    for body in timber:
        geometry = model["body_geometry"][body]["geometry_record"]
        record = original_surfaces[body]
        binding = descriptions[body]["current_finished_step_binding"]
        require(
            binding["file_sha256"] == record["step_binding"]["file_sha256"],
            "surface STEP binding changed",
        )
        path = ROOT / binding["path"]
        pins[path] = binding["file_sha256"]
        planes, bores = [], []
        removed = set()
        prop = next((p for p in proposal["proposals"] if p["block"] == body), None)
        side_prop = next(
            (
                p
                for p in proposal["proposals"]
                if "base_side_" + p["block"].split("_")[-2] == body
            ),
            None,
        )
        if prop is not None:
            old_center = (np.array(geometry["start"]) + geometry["end"]) / 2
            new_center = np.mean(
                [model["nodes"][str(n)] for n in revised["body_nodes"][body]], axis=0
            )
            shift = new_center - old_center
            for key in ("start", "end"):
                geometry[key] = (np.array(geometry[key]) + shift).tolist()
            points = np.array(
                [model["nodes"][str(n)] for n in revised["body_nodes"][body]]
            )
            local = (points - geometry["start"]) @ basis(geometry).T
            geometry["width_mm"], geometry["depth_mm"] = np.ptp(local, axis=0)[
                1:
            ].tolist()
            geometry["area_mm2"] = geometry["width_mm"] * geometry["depth_mm"]
            geometry["gross_width_mm"] = geometry["width_mm"]
            geometry["gross_depth_mm"] = geometry["depth_mm"]
            geometry["original_geometry_diagnostics"] = geometry.pop(
                "geometry_diagnostics", {}
            )
            for i, dimension in enumerate(
                (geometry["width_mm"], geometry["depth_mm"]), 1
            ):
                for sign in (-1, 1):
                    normal = sign * basis(geometry)[i]
                    planes.append(
                        {
                            "id": body + f"/corrected_blank_side_{i}_{sign}",
                            "lo": 0.0,
                            "hi": prop["grain_length_mm"],
                            "normal": normal.tolist(),
                            "offset": float(normal @ new_center + dimension / 2),
                        }
                    )
        else:
            if side_prop:
                for axis in side_prop["axes"]:
                    if "/side_" in axis["axis_id"]:
                        membership = next(
                            m
                            for m in original_axes[axis["axis_id"]][
                                "receiver_memberships"
                            ]
                            if m["receiver_member_id"] == body
                        )
                        removed.update(membership["matched_feature_ids"])
            for feature in record["features"]:
                if feature["feature_id"] in removed:
                    continue
                lo, hi = station_interval(feature, record, geometry)
                if "cylinder" in feature:
                    bores.append(
                        {
                            "id": feature["feature_id"],
                            "lo": lo,
                            "hi": hi,
                            "radius_mm": feature["cylinder"]["radius_mm"],
                            "source": "unchanged_saved_trimmed_cylinder_patch",
                        }
                    )
                elif "plane" in feature:
                    plane = feature["plane"]
                    planes.append(
                        {
                            "id": feature["feature_id"],
                            "lo": lo,
                            "hi": hi,
                            "normal": plane["normal_global_xyz"],
                            "offset": plane["signed_plane_station_global_mm"],
                        }
                    )
                else:
                    raise ValueError(
                        "unsupported saved surface: " + feature["feature_id"]
                    )
        correction = prop or side_prop
        if correction:
            for axis in correction["axes"]:
                if side_prop and "/rail_" in axis["axis_id"]:
                    continue
                direction = np.array(
                    original_axes[axis["axis_id"]]["source_axis_fields"][
                        "direction_global_xyz"
                    ]
                )
                require(
                    abs(direction @ np.array(geometry["axis"])) < 1e-7,
                    "corrected bore is not transverse",
                )
                station = float(
                    np.array(geometry["axis"])
                    @ (np.array(axis["proposed_axis_point_mm"]) - geometry["start"])
                )
                radius = axis["proposed_CAD_bore_envelope_mm"] / 2
                bores.append(
                    {
                        "id": axis["axis_id"] + "/corrected_bore",
                        "lo": station - radius,
                        "hi": station + radius,
                        "radius_mm": radius,
                        "source": "hash_bound_correction_proposal_transverse_cylinder",
                    }
                )
            path = HERE / "top-corner-correction" / (body + ".step")
            pins[path] = proposal["proposal_step_sha256"][str(path.relative_to(ROOT))]
        geometry["source_descriptor"]["step_path"] = str(path.relative_to(ROOT))
        geometry["source_descriptor"]["step_sha256"] = pins[path]
        frame = basis(geometry)
        require(
            np.max(abs(frame @ frame.T - np.eye(3))) < 1e-8
            and np.linalg.det(frame) > 0,
            "invalid member frame",
        )
        records[body] = {
            "member_kind": descriptions[body]["member_kind"],
            "geometry": geometry,
            "current_finished_step": str(path.relative_to(ROOT)),
            "current_finished_step_sha256": pins[path],
            "original_finished_step_sha256": binding["file_sha256"],
            "replaced_original_bore_features": sorted(removed),
            "profile_planes": planes,
            "bore_or_passage_intervals": bores,
            "recess_source": geometry.get("floor_recess_geometry"),
        }
    return records, pins


def saved_sections(records):
    """Reuse geometry only; never reuse an earlier load state or acceptance."""
    pins, accepted, refused = {}, [], []
    for folder in (
        "upper-outer-finished-sections-2026-10-01",
        "right-corner-finished-sections-2026-10-01",
    ):
        path = HERE.parent / folder / "sections.json"
        packet = read(path)
        pins[path] = sha(path)
        frames = packet.get("member_frames_and_step_bindings")
        if frames is None:
            plan = HERE.parent / folder / "source-plan.json"
            pins[plan] = sha(plan)
            require(
                pins[plan] == packet["source_plan_sha256"], "saved section plan changed"
            )
            frames = read(plan)["member_frames_and_step_bindings"]
        binding = {f["member_id"]: f["step_sha256"] for f in frames}
        for section in packet["section_properties"]:
            body = section["member_id"]
            if body not in records:
                continue
            geometry = records[body]["geometry"]
            origin = np.array(section["plane_origin_global_xyz_mm"])
            station = float(np.array(geometry["axis"]) @ (origin - geometry["start"]))
            entry = {
                "source_packet": str(path.relative_to(ROOT)),
                "plane_id": section["plane_id"],
                "member": body,
                "station_mm": station,
                "properties": section["properties"],
                "source_step_sha256": binding[body],
            }
            if binding[body] != records[body]["current_finished_step_sha256"]:
                entry["status"] = "NON_APPLICABLE_CHANGED_FINISHED_STEP"
                refused.append(entry)
            else:
                entry["status"] = "SAVED_EXACT_GEOMETRY_ONLY_NO_NET_SECTION_RESISTANCE"
                require(
                    abs(
                        abs(
                            np.array(section["grain_axis_global_xyz"])
                            @ np.array(geometry["axis"])
                        )
                        - 1
                    )
                    < 1e-7,
                    "saved section normal changed",
                )
                rect = rectangle_at(
                    station,
                    geometry,
                    records[body]["profile_planes"],
                    records[body]["bore_or_passage_intervals"],
                )
                if rect["status"].startswith("BORE_FREE_"):
                    require(
                        abs(rect["area_mm2"] - entry["properties"]["area_mm2"]) < 0.002,
                        "profile rectangle disagrees with saved exact area",
                    )
                    require(
                        np.linalg.norm(
                            np.array(rect["centroid_xyz_mm"])
                            - entry["properties"]["centroid_global_xyz_mm"]
                        )
                        < TOL,
                        "profile centroid disagrees with saved exact section",
                    )
                    entry["bore_free_rectangle_crosscheck"] = True
                accepted.append(entry)
    return accepted, refused, pins


def section_stations(actions, record, saved):
    geometry = record["geometry"]
    length = float(np.linalg.norm(np.array(geometry["end"]) - geometry["start"]))
    values = [0.0, length, *np.arange(0, length, 25.0)]
    for action in actions:
        values.extend([action["station_mm"], *action["footprint_mm"]])
    for feature in record["profile_planes"] + record["bore_or_passage_intervals"]:
        for station in (feature["lo"], feature["hi"]):
            values.extend([station - 0.001, station, station + 0.001])
    values.extend(s["station_mm"] for s in saved)
    # Coalesce numerical copies at the host_cut partition tolerance. Keep the
    # same two one-sided traces at each physical action station.
    sorted_values = sorted(
        max(0.0, min(length, float(v))) for v in values if -TOL <= v <= length + TOL
    )
    stations = []
    for value in sorted_values:
        if not stations or value - stations[-1] > 2e-7:
            stations.append(value)
    return np.array(stations)


def peak_trace(
    actions, record, negative, positions, before, rectangles, references, metric, intact
):
    geometry = record["geometry"]
    candidates = []
    for index, value in enumerate(negative):
        station = positions[index]
        rectangle = rectangles[index // 2]
        if intact and not rectangle["status"].startswith("BORE_FREE_"):
            continue
        frame = basis(geometry)
        local = np.r_[frame @ value[:3], frame @ value[3:]]
        if intact:
            datum = np.array(geometry["start"]) + station * frame[0]
            local[3:] -= frame @ np.cross(
                np.array(rectangle["centroid_xyz_mm"]) - datum, value[:3]
            )
            width, depth = rectangle["width_depth_mm"]
        else:
            width, depth = geometry["width_mm"], geometry["depth_mm"]
        stress = stresses(local, width, depth, references)
        candidates.append((stress[metric], index, local, stress))
    if not candidates:
        return None
    _, index, local, stress = max(candidates, key=lambda x: x[0])
    cut = accounting.host_cut(
        actions, float(positions[index]), geometry, bool(before[index])
    )
    reference = cut["internal_on_negative_half"]
    require(
        np.max(abs(np.array(reference["force_xyz_n"]) - negative[index, :3])) < 1e-7
        and np.max(abs(np.array(reference["moment_xyz_nmm"]) - negative[index, 3:]))
        < 1e-6,
        "vectorized cut differs from host_cut",
    )
    return {
        "cut_array_index": index,
        "station_mm": float(positions[index]),
        "trace": "before" if before[index] else "after",
        "finished_section": rectangles[index // 2],
        "centroid_shift_applied": intact,
        "signed_force_N_Vu_Vv_n_and_couple_T_Mu_Mv_nmm": local.tolist(),
        "elementary_stresses_and_reference_sums": stress,
        "complete_signed_cut": cut,
    }


def run(output, clearance):
    owned = [
        HERE / name for name in ("member-screen-attempt01", "member-screen-attempt02")
    ]
    require(
        any(output == path or path in output.parents for path in owned),
        "output outside owned directory",
    )
    require(
        not output.exists(),
        "preserve the existing calculation; use an owned child directory for a changed attempt",
    )
    output.mkdir(parents=True)
    (output / "producer.py.snapshot").write_bytes(Path(__file__).read_bytes())
    comparison = read(clearance / "comparison.json")
    operator = read(FRAME / "operator-assessment.json")
    baseline = read(FRAME / "frame-results.json")
    selected = [s for s in comparison["states"] if s["gap_scale"] == 1.0]
    case_ids = [c["case_id"] for c in baseline["cases"]]
    require(
        len(set(case_ids)) == 6 and [s["case_id"] for s in selected] == case_ids,
        "six-case NOMINAL-GAP identity mismatch",
    )
    require(
        all(s["status"] == "PASS_CONDITIONAL_COUPLED_FRAME_LAWS" for s in selected),
        "incomplete NOMINAL-GAP source",
    )
    require(
        comparison["dead_load_factor"] == baseline["dead_load_factor"],
        "dead-load factors disagree",
    )
    pins = {
        ROOT / p: h
        for p, h in {**operator["source_sha256"], **comparison["source_sha256"]}.items()
    }
    pins.update({FRAME / p: h for p, h in operator["output_sha256"].items()})
    pins[clearance / "response.npz"] = comparison["response_sha256"]
    for path in (
        clearance / "comparison.json",
        FRAME / "operator-assessment.json",
        FRAME / "frame-results.json",
        accounting.MODEL,
        accounting.CONTACTS,
        accounting.MATERIALS,
        DOFS,
        accounting.BASE / "reduced-static-attempt01/model-inputs.json",
        FEATURES / "surfaces.json",
        FEATURES / "axis-features.json",
        BUNDLE / "bundle/current-full-frame-member-solids.json",
        PROFILE / "beam-selfweight-profile.json",
        PROFILE / "README.md",
        BEAM / "produce.py",
        HERE / "top-corner-correction/proposal.json",
        HERE / "top-corner-contact-geometry.json",
        Path(accounting.__file__),
        Path(__file__),
    ):
        digest = sha(path)
        require(
            path not in pins or pins[path] == digest,
            "conflicting source binding: " + str(path),
        )
        pins[path] = digest
    model = copy.deepcopy(read(accounting.MODEL))
    revised = read(FRAME / "model.json")
    inputs = read(accounting.BASE / "reduced-static-attempt01/model-inputs.json")
    materials = read(accounting.MATERIALS)
    records, step_pins = geometry_sources(
        model,
        revised,
        inputs,
        read(FEATURES / "surfaces.json"),
        read(FEATURES / "axis-features.json"),
        read(HERE / "top-corner-correction/proposal.json"),
    )
    pins.update(step_pins)
    accepted, refused, section_pins = saved_sections(records)
    pins.update(section_pins)
    for path, digest in pins.items():
        require(sha(path) == digest, "changed source: " + str(path))
    write(
        output / "inputs.json",
        {
            "producer_sha256": sha(Path(__file__)),
            "source_sha256": {str(p.relative_to(ROOT)): h for p, h in pins.items()},
            "selected_force_keys": [c + "_gap_raw_force_n" for c in case_ids],
            "source_model_revision": revised["development_revision"],
            "same_state_dead_load_factor": baseline["dead_load_factor"],
            "missing_historical_artifacts": [
                str((BEAM / "member-beam-selfweight.json").relative_to(ROOT))
            ]
            if not (BEAM / "member-beam-selfweight.json").exists()
            else [],
        },
    )
    rows = read(FRAME / "row-identities.json")
    labels = [
        tuple(map(int, line.split(".")))
        for line in DOFS.read_text().splitlines()
        if line.strip()
    ]
    old_contact = read(accounting.CONTACTS)
    patches = {
        c["name"]: {
            "area": c["area_mm2"],
            "vertices": old_contact["contact_patches"][c["source_patch_index"]][
                "vertices_xyz_mm"
            ],
        }
        for c in model["contact_cell_ownership"]
        if c["kind"] == accounting.CONTACT
    }
    prepared = read(HERE / "top-corner-contact-geometry.json")
    for row in rows:
        if "contact_area_mm2" in row:
            own = row["ownership"]
            cleat = next(
                c for c in prepared["cleats"] if c["block"] == own["second_body"]
            )
            face = next(f for f in cleat["faces"] if f["host"] == own["first_body"])
            patches[row["row_id"]] = {
                "area": row["contact_area_mm2"],
                "vertices": face["corners_mm"],
            }
    arrays, cases, csv_rows = {}, [], []
    with (
        np.load(FRAME / "operators.npz", allow_pickle=False) as operators,
        np.load(clearance / "response.npz", allow_pickle=False) as response,
    ):
        D, F, W = [operators[k] for k in ("D", "F", "W")]
        require(
            len(labels) == F.shape[0] and F.shape[1] == 12, "load operator DOF mismatch"
        )
        require(
            len(set(labels)) == len(labels) and all(d in (1, 2, 3) for _, d in labels),
            "invalid physical DOF labels",
        )
        for case_index, case_id in enumerate(case_ids):
            maps = []
            for column in (2 * case_index, 2 * case_index + 1):
                mapping = {}
                for (node, dof), value in zip(labels, F[:, column], strict=True):
                    if value != 0:
                        mapping.setdefault(str(node), [0.0, 0.0, 0.0])[dof - 1] = float(
                            value
                        )
                maps.append(mapping)
            case = {
                "gravity_nodal_map": maps[0],
                "climber_nodal_map": maps[1],
                "dead_load_factor": baseline["dead_load_factor"],
            }
            force = response[case_id + "_gap_raw_force_n"]
            require(
                force.shape == (len(rows),) and np.isfinite(force).all(),
                "invalid same-state connector forces",
            )
            body_results = []
            for body, record in records.items():
                actions, datum, geometry = accounting.physical_actions(
                    body, case, force, model, rows, D, revised["body_names"], patches
                )
                closure = accounting.wrench(actions, datum)
                require(
                    np.max(abs(closure[:3])) <= 0.1 and np.max(abs(closure[3:])) <= 2,
                    "whole-member action imbalance: " + case_id + "/" + body,
                )
                body_index = revised["body_names"].index(body)
                loads = [a for a in actions if a["role"] == "discrete_body_load"]
                load_wrench = accounting.wrench(loads, datum)
                expected_load = (
                    case["dead_load_factor"]
                    * W[6 * body_index : 6 * body_index + 6, 2 * case_index]
                    + W[6 * body_index : 6 * body_index + 6, 2 * case_index + 1]
                )
                require(
                    np.max(
                        abs(load_wrench - expected_load * [1, 1, 1, 1000, 1000, 1000])
                    )
                    < 1e-6,
                    "F/W member load mismatch",
                )
                own_saved = [s for s in accepted if s["member"] == body]
                stations = section_stations(actions, record, own_saved)
                rectangles = [
                    rectangle_at(
                        float(s),
                        geometry,
                        record["profile_planes"],
                        record["bore_or_passage_intervals"],
                    )
                    for s in stations
                ]
                negative, positive, positions, before = cut_vectors(
                    actions, geometry, stations
                )
                frame = basis(geometry)
                prefix = case_id + "__" + body
                arrays[prefix + "__internal_negative_grain_u_v"] = np.column_stack(
                    [negative[:, :3] @ frame.T, negative[:, 3:] @ frame.T]
                )
                arrays[prefix + "__internal_positive_grain_u_v"] = np.column_stack(
                    [positive[:, :3] @ frame.T, positive[:, 3:] @ frame.T]
                )
                arrays[prefix + "__point_force_free_couple_xyz"] = np.array(
                    [a["force_n"] + a["free_moment_nmm"] for a in actions]
                )
                if case_index == 0:
                    record["stations_mm"] = stations.tolist()
                    record["rectangle_at_station"] = rectangles
                    record["point_action_ids"] = [a["source_id"] for a in actions]
                    record["point_action_roles"] = [a["role"] for a in actions]
                    record["point_action_other_bodies"] = [
                        a["other_body"] for a in actions
                    ]
                    arrays[body + "__point_xyz_mm"] = np.array(
                        [a["point_mm"] for a in actions]
                    )
                    arrays[body + "__point_stations_mm"] = np.array(
                        [a["station_mm"] for a in actions]
                    )
                    arrays[body + "__point_footprints_mm"] = np.array(
                        [a["footprint_mm"] for a in actions]
                    )
                    arrays[body + "__point_rows"] = np.array(
                        [-1 if a["row"] is None else a["row"] for a in actions]
                    )
                else:
                    require(
                        stations.tolist() == record["stations_mm"]
                        and [a["source_id"] for a in actions]
                        == record["point_action_ids"],
                        "member action/cut inventory changed between cases",
                    )
                references = reference_values(body, geometry, materials)
                result = {
                    "member": body,
                    "array_prefix": prefix,
                    "point_action_count": len(actions),
                    "cut_trace_count": len(positions),
                    "whole_member_balance": accounting.record_wrench(closure, geometry),
                    "mapped_body_load_wrench_about_node_mean": accounting.record_wrench(
                        load_wrench, geometry
                    ),
                    "conditional_material": references,
                    "transfer_wrenches_about_node_mean": [],
                }
                for other, role in sorted(
                    {(str(a["other_body"]), a["role"]) for a in actions}
                ):
                    subset = [
                        a
                        for a in actions
                        if str(a["other_body"]) == other and a["role"] == role
                    ]
                    result["transfer_wrenches_about_node_mean"].append(
                        {
                            "other_body": None if other == "None" else other,
                            "role": role,
                            "action_count": len(subset),
                            "wrench": accounting.record_wrench(
                                accounting.wrench(subset, datum), geometry
                            ),
                        }
                    )
                # Reuse the earlier beam/self-weight first-moment convention as
                # a diagnostic only. The frozen F loads remain in every cut.
                gravity_actions = [
                    dict(
                        a,
                        force_n=(
                            np.array(
                                maps[0].get(
                                    a["source_id"].removeprefix("body_load_node_"),
                                    [0, 0, 0],
                                )
                            )
                            * case["dead_load_factor"]
                        ).tolist(),
                    )
                    for a in loads
                ]
                line_center = (np.array(geometry["start"]) + geometry["end"]) / 2
                gravity_wrench = accounting.wrench(gravity_actions, line_center)
                length = float(
                    np.linalg.norm(np.array(geometry["end"]) - geometry["start"])
                )
                result["equivalent_gravity_diagnostic_only"] = {
                    "line_center_mm": line_center.tolist(),
                    "line_force_n_per_mm": (gravity_wrench[:3] / length).tolist(),
                    "first_moment_correction_couple_nmm": gravity_wrench[3:].tolist(),
                    "substituted_into_section_actions": False,
                    "limits": "Includes frozen mapped dead loads and proportional allowance; not a new timber-only density or gravity distribution.",
                }
                for scope, intact in (
                    ("gross_rectangle_proxy", False),
                    ("bore_free_rectangle_screen", True),
                ):
                    result[scope] = {
                        name: peak_trace(
                            actions,
                            record,
                            negative,
                            positions,
                            before,
                            rectangles,
                            references,
                            metric,
                            intact,
                        )
                        for name, metric in (
                            ("normal_governing", "linear_normal_reference_sum"),
                            ("shear_governing", "transverse_shear_over_reference"),
                        )
                    }
                result["saved_finished_section_count"] = len(own_saved)
                result["saved_disconnected_sections_no_force_allocation"] = [
                    s["plane_id"]
                    for s in own_saved
                    if s["properties"]["disconnected_ligaments"]
                ]
                body_results.append(result)
                csv_row = {
                    "case": case_id,
                    "member": body,
                    "member_kind": record["member_kind"],
                    "force_residual_max_n": float(np.max(abs(closure[:3]))),
                    "moment_residual_max_nmm": float(np.max(abs(closure[3:]))),
                }
                for scope in ("gross_rectangle_proxy", "bore_free_rectangle_screen"):
                    for name, metric in (
                        ("normal_governing", "linear_normal_reference_sum"),
                        ("shear_governing", "transverse_shear_over_reference"),
                    ):
                        trace = result[scope][name]
                        label = scope + "_" + name
                        csv_row[label + "_ratio"] = (
                            None
                            if trace is None
                            else trace["elementary_stresses_and_reference_sums"][metric]
                        )
                        csv_row[label + "_station_mm"] = (
                            None if trace is None else trace["station_mm"]
                        )
                csv_rows.append(csv_row)
            cases.append(
                {
                    "case_id": case_id,
                    "source_force_key": case_id + "_gap_raw_force_n",
                    "members": body_results,
                }
            )
            print(
                case_id,
                "44 whole-member balances and signed member screens complete",
                flush=True,
            )
    for section in accepted:
        body = section["member"]
        station = section["station_mm"]
        section["cut_indices_before_after"] = [
            2 * int(np.argmin(abs(np.array(records[body]["stations_mm"]) - station)))
            + i
            for i in (0, 1)
        ]
        require(
            abs(
                records[body]["stations_mm"][
                    section["cut_indices_before_after"][0] // 2
                ]
                - station
            )
            < 1e-6,
            "saved section cut station lost",
        )
    for path, digest in pins.items():
        require(
            sha(path) == digest, "source changed during member screen: " + str(path)
        )
    np.savez_compressed(output / "action-section-arrays.npz", **arrays)
    write(
        output / "geometry.json",
        {
            "members": records,
            "saved_matching_finished_sections": accepted,
            "saved_non_applicable_finished_sections": refused,
            "cut_trace_order": "Two traces per station: before, after. Wrenches at start + s*grain, on negative and positive halves separately; N>0 is tension on the negative half.",
        },
    )
    with (output / "member-results.csv").open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(csv_rows[0]))
        writer.writeheader()
        writer.writerows(csv_rows)
    report = {
        "schema": "same_state_six_case_timber_member_screen/v1",
        "status": "COMPLETE_CONDITIONAL_ELEMENTARY_MEMBER_SCREENS_NOT_QUALIFICATION",
        "producer_sha256": sha(Path(__file__)),
        "clearance_input_directory": str(clearance.relative_to(ROOT)),
        "clearance_joint_hosts": comparison.get(
            "clearance_joint_hosts", accounting.BLOCK_HOSTS
        ),
        "source_frame_assumptions": comparison["limits"],
        "same_state_dead_load_factor": baseline["dead_load_factor"],
        "source_sha256": {str(p.relative_to(ROOT)): h for p, h in pins.items()},
        "counts": {
            "cases": 6,
            "timber_members": 44,
            "whole_member_balances": len(csv_rows),
            "cut_traces": sum(
                r["cut_trace_count"] for c in cases for r in c["members"]
            ),
            "matching_saved_sections": len(accepted),
            "non_applicable_changed_STEP_sections": len(refused),
        },
        "open_checks_by_member": {
            body: {
                "bore_passage_geometry_intervals": len(
                    record["bore_or_passage_intervals"]
                ),
                "all_bore_or_passage_sections": "Finished-section normal/local shear, concentrations and ligament transfer remain open at the named geometry.json intervals; no force division to disconnected regions.",
                "terminal_trim_profile_stations_no_stress_ratio": [
                    s
                    for s, rect in zip(
                        record["stations_mm"],
                        record["rectangle_at_station"],
                        strict=True,
                    )
                    if rect["status"]
                    == "NON_APPLICABLE_END_TRIM_POINT_LOAD_DISTRIBUTION"
                ],
                "rear_recess_local_check": None
                if record["recess_source"] is None
                else "Use exact 1:12 recess/runout with current cuts for notch/connection shear and splitting; reduced rectangle arithmetic is not a local qualification.",
                "torsion_and_joint_disturbance": "Signed torque and six interface components are available; orthotropic shear/torsion and short connection zones remain open.",
                "bending_compression_stability": "Unsupported lengths, restraint, CL and CP remain unspecified for acceptance.",
            }
            for body, record in records.items()
        },
        "array_convention": "Point arrays: Fx,Fy,Fz,Cx,Cy,Cz; C is the free couple at the saved point. Cut arrays: N,Vu,Vv,T,Mu,Mv in grain/u/v, N in N and couples in N mm. Geometry lists stations; before then after. Rectangle stress traces shift moments to that rectangle's centroid.",
        "method_limits": [
            "Same-state NOMINAL-GAP responses only. No separate connector peaks, earlier frame forces, gravity substitution, or new equilibrium solve.",
            "All incident connector rows, released zero actions, body nodal loads and free couples are retained. Whole-member and cut closure use 0.1 N and 2 N mm limits.",
            "Gross rectangles are elementary beam proxies even where finished geometry removes material. They are not finished-member resistances.",
            "Bore-free rectangle screens use saved finite outward planes and matching correction metadata. Bore/passages, unsupported profiles and clipped end zones are non-applicable: point loads do not supply a traction distribution as the terminal slice tends to zero area. Only the source-bound full-depth 1:12 rear recess receives reduced-rectangle arithmetic. Matching saved exact sections carry area, centroid, covariance and connectivity only; disconnected regions receive no invented common strain or force share.",
            "25 mm interior samples, every point-action station and finite feature/footprint boundary are included. Gross point-action extrema are covered by one-sided action cuts; variable-profile stress extrema are sampled, not continuously bounded.",
            "Normal sum = max(Nt/(A Ft), Nc/(A Fc)) + (|Mu|/Su + |Mv|/Sv)/Fb. This is a declared linear reference sum, not the NDS combined-load equation or buckling check.",
            "Transverse screen = 1.5 (|Vu|+|Vv|)/A/Fv. It is a rectangular component-sum proxy; connection/notch shear provisions and orthotropic combined shear/torque remain unqualified.",
            "Signed torque is retained without an invented torsion resistance. CL, CP, unsupported lengths, panel restraint and local connection-zone/disturbance behavior are open.",
            "All material values are conditional DF-L No.2 scenarios. Four ripped blocks use the existing hypothetical final-product CF=1 study; no original grade transfers. Corrected top cleats use the 4x6 size factors.",
        ],
        "cases": cases,
        "native_launch": False,
        "CAD_rebuilt": False,
        "tests_run": False,
        "review_run": False,
        "complete_member_acceptance": False,
        "complete_joint_acceptance": False,
        "reviewed_geometry_changed": False,
        "physical_release": False,
        "output_sha256": {
            name: sha(output / name)
            for name in (
                "inputs.json",
                "geometry.json",
                "action-section-arrays.npz",
                "member-results.csv",
                "producer.py.snapshot",
            )
        },
    }
    write(output / "member-results.json", report)
    document(output, report, records, csv_rows)
    print(report["status"], report["counts"], flush=True)


def document(output, report, records, rows):
    def governing(subset, scope, kind):
        key = scope + "_" + kind + "_governing_ratio"
        valid = [r for r in subset if r[key] is not None]
        return max(valid, key=lambda r: r[key]) if valid else None

    rel = output.relative_to(HERE)
    lines = [
        "# Same-state six-case timber member screens",
        "",
        f"The six NOMINAL-GAP cases in `{Path(report['clearance_input_directory']).name}/response.npz` have been screened using the corrected physical operators and loads in `corner-frame-attempt01/`. This packet supplies complete signed member actions and elementary stress references for the conditional shop model. It does not establish finished-member, local wood, stability, or complete-joint acceptance.",
        "",
        f"**Result:** {report['counts']['whole_member_balances']} whole-member balances across 20 frame timbers and 24 connector blocks; {report['counts']['cut_traces']:,} two-sided section traces. All source SHA-256 bindings and whole-member action closures meet the recorded arithmetic limits.",
        "",
        f"The largest absolute whole-member residuals are **{max(r['force_residual_max_n'] for r in rows):.6g} N** and **{max(r['moment_residual_max_nmm'] for r in rows):.6g} N·mm**; limits are 0.1 N and 2 N·mm. Both cut halves, every point force and free couple, contact footprints, and the source zero-force rows are retained in the saved arrays.",
        "",
        "## Six-case results",
        "",
        "These are dimensionless conditional reference sums. The normal sum includes signed axial force and both bending components in the same cut. The shear sum includes both transverse components. A value below one is an elementary arithmetic result; it does not clear buckling, torsion, notches, bores, or connection-zone failure.",
        "",
        "| Case | Governing gross normal / member | Governing gross shear / member | Governing bore-free normal / member | Governing bore-free shear / member |",
        "| --- | --- | --- | --- | --- |",
    ]
    for case in report["cases"]:
        subset = [r for r in rows if r["case"] == case["case_id"]]
        cells = []
        for scope, kind in (
            ("gross_rectangle_proxy", "normal"),
            ("gross_rectangle_proxy", "shear"),
            ("bore_free_rectangle_screen", "normal"),
            ("bore_free_rectangle_screen", "shear"),
        ):
            winner = governing(subset, scope, kind)
            key = scope + "_" + kind + "_governing_ratio"
            cells.append(
                "not applicable"
                if winner is None
                else f"{winner[key]:.4f} / `{winner['member']}`"
            )
        lines.append("| " + " | ".join([case["case_id"], *cells]) + " |")
    normal = governing(rows, "bore_free_rectangle_screen", "normal")
    shear = governing(rows, "bore_free_rectangle_screen", "shear")
    if normal is not None and shear is not None:
        lines.extend(
            [
                "",
                f"The governing applicable normal reference is **{normal['bore_free_rectangle_screen_normal_governing_ratio']:.6f}**, `{normal['member']}` in `{normal['case']}` at **{normal['bore_free_rectangle_screen_normal_governing_station_mm']:.3f} mm**. The governing transverse reference is **{shear['bore_free_rectangle_screen_shear_governing_ratio']:.6f}**, `{shear['member']}` in `{shear['case']}` at **{shear['bore_free_rectangle_screen_shear_governing_station_mm']:.3f} mm**. These locate the first member checks to integrate; their bore/connector-zone, torque and restraint checks remain open.",
            ]
        )
    lines.extend(
        [
            "",
            "## Member envelope across the six cases",
            "",
            "Every envelope entry points to one simultaneous case and cut; component maxima from different states are not added. The JSON preserves the signed force/couple vector, section dimensions, centroid shift and contact footprints for each governing cut.",
            "",
            "| Member | Gross normal | Gross shear | Bore-free normal | Bore-free shear | Governing bore-free case and station (normal / shear) |",
            "| --- | ---: | ---: | ---: | ---: | --- |",
        ]
    )
    for body in records:
        subset = [r for r in rows if r["member"] == body]
        winners = [
            governing(subset, scope, kind)
            for scope, kind in (
                ("gross_rectangle_proxy", "normal"),
                ("gross_rectangle_proxy", "shear"),
                ("bore_free_rectangle_screen", "normal"),
                ("bore_free_rectangle_screen", "shear"),
            )
        ]
        cells, locations = [], []
        for i, (scope, kind) in enumerate(
            (
                ("gross_rectangle_proxy", "normal"),
                ("gross_rectangle_proxy", "shear"),
                ("bore_free_rectangle_screen", "normal"),
                ("bore_free_rectangle_screen", "shear"),
            )
        ):
            winner = winners[i]
            key = scope + "_" + kind + "_governing"
            cells.append("N/A" if winner is None else f"{winner[key + '_ratio']:.4f}")
            if i >= 2:
                locations.append(
                    "N/A"
                    if winner is None
                    else f"{winner['case']}, {winner[key + '_station_mm']:.3f} mm"
                )
        lines.append(
            "| " + " | ".join([f"`{body}`", *cells, " / ".join(locations)]) + " |"
        )
    lines.extend(
        [
            "",
            "## Geometry applicability and open checks",
            "",
            f"{report['counts']['matching_saved_sections']} prior exact section planes still match the current finished STEP bytes; {report['counts']['non_applicable_changed_STEP_sections']} planes have a changed STEP binding and are explicitly non-applicable. Earlier three-case forces and accepted-state labels are never imported. Matching saved net sections retain their actual area, centroid, covariance and disconnected-ligament flag without assigning a common strain, invented resistance, or force division to disconnected regions.",
            "",
            "The finite surface register supplies every cylinder/passages interval and outward planar face. Bore-free full rectangles and the source-bound full-depth rear-leg 1:12 recess are screened with their calculated width, depth and centroid. An intersecting bore or passage makes the rectangular stress screen non-applicable. Clipped end profiles retain their geometry and signed cuts, but have no stress ratio: the source lumped end loads do not define the local traction field through a section tending to zero area. The two corrected top blocks and two side hosts use only their hash-bound correction geometry; former bore slices on those bodies are not transferred.",
            "",
            "The first saved runs in `member-screen-attempt01/` (top corners only) and `member-screen-attempt02/` (four joints) are preserved. They included mechanically inapplicable terminal-profile ratios; use the corrected child packet linked below for integration. Its changed applicability interpretation is explicit and does not change the frozen response or physical model.",
            "",
            "The exact remaining checks are:",
            "",
            "- At every listed bore/passages interval, recover the finished connected section and its load transfer, including the 32 preserved LED/service patches and the revised top-corner bores. `geometry.json` identifies each member, feature and station interval. The signed six-case cuts are available; bore concentrations, ligament sharing, net normal resistance and local shear are not supplied by a gross rectangle.",
            "- At rear-leg recess/runout cuts, use the actual cut profile and centroid with the signed six-case actions, then apply the connection/notch shear and local splitting provisions. The bore-free profile arithmetic does not accept the notch or its stress concentration.",
            "- At clipped runner ends, inclined side/principal bases and rear-leg tips, replace the lumped point-load beam interpretation with an applicable local end/load-transfer description. Their exact station lists are in `open_checks_by_member`; terminal-profile arithmetic is excluded rather than reported as a wood-resistance failure.",
            "- Resolve simultaneous orthotropic shear/torque and short-block connection-zone disturbance. All torques and interface free couples are retained; no torsional resistance or local wood qualification is inferred.",
            "- Specify member unsupported lengths and effective restraint for compression and bending stability, including the header, inclined sides/principals and rear legs. No CL, CP or buckling acceptance is calculated from these gross beam proxies.",
            "- Keep the four remanufactured blocks on the existing hypothetical final-piece DF-L No.2, CF=1 study scenario until their final-product grade/size-factor basis is supplied. No source grade transfers. Conditional Hillman spring laws, proportional accessory placement and unverified no-slip support remain inherited model assumptions.",
            "",
            "## Material and arithmetic",
            "",
            "The current conditional material packet provides DF-L No.2 base values: Fb=900 psi, Ft=575 psi, Fc=1350 psi and Fv=180 psi. Standard 2×6/4×6 sections use CF=(1.3, 1.3, 1.1) for Fb/Ft/Fc; standard 4×4 blocks use (1.5, 1.5, 1.15). The two corrected 88.9×139.7 mm (3½×5½ in.) top cleats use 4×6 factors. The four ripped blocks retain the source CF=1 hypothetical study. Normal duration, dry service, unincised wood and normal temperature are declared; Cfu=Cr=1. The references include no CL or CP stability credit and are not fully adjusted NDS design resistances.",
            "",
            "On the negative half's outward +grain cut, N>0 is tension. A rectangular section uses σ=N/A + Mu·v/Iu − Mv·u/Iv; the four corner stresses bound its linear normal field. The reported normal sum is max(Nt/(A·Ft), Nc/(A·Fc)) + (|Mu|/Su+|Mv|/Sv)/Fb. The transverse screen is 1.5(|Vu|+|Vv|)/(A·Fv), a component-sum proxy. Neither is adopted as an NDS combined-load or local connection criterion.",
            "",
            f"All actions remain the source point actions, including the corrected F load operator and dead-load factor {report['same_state_dead_load_factor']:.16g}. The old beam-selfweight producer's line-resultant/first-moment convention is reused only as a load diagnostic. Its `member-beam-selfweight.json` is absent locally; the saved 20-member finite-bin profile and exact member-solid packet remain bound as geometry/self-weight evidence. Their older 600 kg/m³ distribution is not substituted into this model or counted twice. No OBB extraction, CAD rebuilding, test, review, frame solve or native run is performed.",
            "",
            "## Files and reproduction",
            "",
            f"- [member-results.json]({rel}/member-results.json): 264 member results, complete transfer wrenches and governing stress cuts, source/output hashes and claim limits.",
            f"- [member-results.csv]({rel}/member-results.csv): all six cases and 44 members in a compact integration table.",
            f"- [geometry.json]({rel}/geometry.json): actual bore/profile applicability, matching and refused saved section planes, source member/STEP bindings and point-action identities.",
            f"- [action-section-arrays.npz]({rel}/action-section-arrays.npz): signed point forces/free couples and both cut-half wrenches; units and indexing are in the result JSON.",
            f"- [inputs.json]({rel}/inputs.json) and [producer.py.snapshot]({rel}/producer.py.snapshot): frozen source bindings, force keys and executed producer.",
            "",
            "```sh",
            "PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 \\",
            "  .venv/bin/python docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/member_screen.py \\",
            f"  --clearance {report['clearance_input_directory']} \\",
            f"  --output {output.relative_to(ROOT)}",
            "```",
            "",
            "The producer accepts `--clearance` (alias `--input-dir`) for a saved response directory and preserves an existing attempt. A changed calculation may use a new child under `member-screen-attempt01/` or `member-screen-attempt02/`. These small outputs remain active for parent integration. Earlier failed/frozen inputs and `/tmp` are preserved; no archive or prune operation is performed. Authority, other owners' files, staging and commits are outside this packet.",
        ]
    )
    (HERE / "member-checks.md").write_text("\n".join(lines) + "\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=HERE / "member-screen-attempt01")
    parser.add_argument(
        "--clearance",
        "--input-dir",
        type=Path,
        default=RESPONSE,
        help="Saved same-physical-model comparison.json and response.npz directory",
    )
    args = parser.parse_args()
    output = args.output.resolve()
    try:
        run(output, args.clearance.resolve())
    except Exception as error:
        if (
            output.is_dir()
            and not (output / "member-results.json").exists()
            and (output / "producer.py.snapshot").exists()
        ):
            failure = output / "failure.json"
            if not failure.exists():
                write(
                    failure,
                    {
                        "status": "STOP_MEMBER_SCREEN",
                        "exception": str(error),
                        "producer_sha256": sha(output / "producer.py.snapshot"),
                        "physical_release": False,
                    },
                )
        raise
