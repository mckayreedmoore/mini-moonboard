"""Finite timber-section arithmetic on completed first-order corner actions.

No mechanics, CAD or frame solve runs. Disconnected sections receive no
invented regional load sharing, bending resistance or torsion/splitting limit.
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import importlib.util
import json
import math
import sys
from itertools import pairwise
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
RAW = HERE / "rawlocal/corner-timber-sections"
FIRST = HERE / "rawlocal/corner-first-order/attempt01/checks.json"
GROUP = HERE / "rawlocal/block-group-resistance/attempt02/checks.json"
TRACTION = HERE / "cleat-traction.py"
COMPONENT = HERE / "bolted-replay-results/corner-attempt01/component-results.json"
PROPOSAL = HERE.parent / "top-corner-correction/proposal.json"
MATERIAL = (
    HERE.parents[1] / "hardware-material-specification-2026-09-30/material-inputs.json"
)
PDF = HERE.parents[1] / "upper-block-strength-2026-10-01/source-cache"
CH3_SHA = "205df74e16f632dfe78211e99bfa5dfa8b9f8dd316e9c5fa1316493f795ec644"
CASES = ("a12-rear", "a12-forward", "a12-left", "k12-right", "k12-rear", "a1-rear")
TOL = 1e-6
PSI_MPA = 0.006894757293168361
PINS = {
    FIRST: "b15b57d3879fdca2dac607d11a2ad127acd1008f6c2a6f546333a1b26c754cfe",
    GROUP: "0a69cd84902c9105f5e6b8f3c70e59efaae9ac56bc4c3238935d97a4185d210b",
    TRACTION: "2834a9a9fd25083da16034b498b3356197a4a6b2b53ffb35663077c5f93f7764",
    HERE
    / "cleat-traction.md": "f382740c32bd81eb39c2f52af3e1a5b77ed724a91fb7315075de40ff7658d19c",
    COMPONENT: "401b8876dc3a96b553c847f1029a5a9200ba3f45af5493f64edd61fdc6bc42b6",
    PROPOSAL: "5932768c7a7d91535f69a90787b32222eb4d165ac6353d3e2ed4daf9e248e2b2",
    HERE
    / "operators-attempt02/model-inputs.json": "e2109cabed9fcbc0a14346ef63b707abb1aed358ebf5fa126b2cba216aa771cc",
    HERE.parent
    / "top_corner_correction.py": "6474cbe6aa8306a153b6cbe166c3162001954b41ea7e4da6c6b7fe60031472e9",
    MATERIAL: "0f33ad8fd517673a4ebbed36c4a30c1cfe07e0d8163165bdc804af91d958fc5a",
    HERE.parent
    / "member_screen.py": "5ecbfcebc8ea45bba83961305735f919d5e6caa3862625befec875655dd0b5d9",
    HERE
    / "block-group-resistance.py": "e5df5f81168a0e700948816a5c292c521593b328ab86fb72b1a2e2f0cd98b3b0",
    HERE
    / "block-group-resistance.md": "8bcfbef56e69fb203fcc87a95c16df4d6eb16b7c544d83359dbf0b74c66bab77",
    PDF
    / "appendix-2024-awc-20260911.pdf": "1fa2bcf52803b1bbed8ea30cf13551dd5f76c90bf110ac475b401f81d116ec31",
}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def read(path):
    return json.loads(path.read_text())


def dump(path, record):
    path.write_text(
        json.dumps(record, indent=2, sort_keys=True, allow_nan=False) + "\n"
    )


def authenticate(pins):
    for path, digest in pins.items():
        require(sha(path) == digest, f"changed source: {path}")


def module(path, name):
    sys.dont_write_bytecode = True
    spec = importlib.util.spec_from_file_location(name, path)
    require(spec is not None and spec.loader is not None, "arithmetic module missing")
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


def frame(descriptor):
    g = np.array(descriptor["axis"], dtype=float)
    g /= np.linalg.norm(g)
    u = np.array(descriptor["section_u"], dtype=float)
    u /= np.linalg.norm(u)
    rows = np.array([g, u, np.cross(g, u)])
    require(np.max(abs(rows @ rows.T - np.eye(3))) < 1e-8, "invalid grain frame")
    return rows


def geometry(state, prop, descriptor):
    """Interpret the source's rectangular blank and four disjoint through bores."""
    rows = frame(descriptor)
    center = np.array(state["common_datum_xyz_mm"])
    length = prop["grain_length_mm"]
    width, depth = prop["proposed_section_X_T_mm"]
    require(
        abs(length - 119.7) < TOL and [width, depth] == [88.9, 139.7],
        "geometry differs",
    )
    start = center - length / 2 * rows[0]
    bores = []
    schedule = {a["axis_id"]: a for a in prop["axes"]}
    for host in state["hosts"].values():
        for bolt in host["state"]["bolts"]:
            identity = bolt["axis_id"]
            source = schedule[identity]
            point = np.array(bolt["interface_point_xyz_mm"])
            # Proposal axis points can lie elsewhere along the same bore line.
            direction = np.array(bolt["bolt_axis_head_to_nut_xyz"])
            delta = point - source["proposed_axis_point_mm"]
            require(
                np.linalg.norm(delta - delta @ direction * direction) < TOL,
                "bore line differs",
            )
            xyz = rows @ (point - start)
            transverse = rows @ direction
            plane_axis = 1 if "/rail_" in identity else 2
            require(
                abs(transverse[0]) < TOL and abs(transverse[plane_axis]) < TOL,
                "nontransverse bore",
            )
            require(abs(abs(transverse[3 - plane_axis]) - 1) < TOL, "nonaligned bore")
            bores.append(
                {
                    "axis_id": identity,
                    "station_mm": float(xyz[0]),
                    "transverse_center_mm": float(xyz[plane_axis]),
                    "removed_interval_axis": plane_axis,
                    "radius_mm": source["proposed_CAD_bore_envelope_mm"] / 2,
                }
            )
    require(len(bores) == 4, "four actual bores required")
    removed = sum(
        math.pi
        * b["radius_mm"] ** 2
        * (depth if b["removed_interval_axis"] == 1 else width)
        for b in bores
    )
    require(
        abs(width * depth * length - removed - prop["finished_proposal_volume_mm3"])
        < 0.001,
        "analytic finished volume differs",
    )
    return {
        "block": prop["block"],
        "grain_frame_rows_xyz": rows.tolist(),
        "center_xyz_mm": center.tolist(),
        "start_xyz_mm": start.tolist(),
        "grain_length_mm": length,
        "width_depth_mm": [width, depth],
        "bores": bores,
        "analytic_finished_volume_mm3": width * depth * length - removed,
        "source_finished_volume_mm3": prop["finished_proposal_volume_mm3"],
        "scope": "Source rectangular blank minus four disjoint transverse through cylinders; no CAD replay, house, trim or additional void.",
    }


def retained(bounds, removed):
    intervals = [list(bounds)]
    for low, high in removed:
        following = []
        for a, b in intervals:
            if high <= a or low >= b:
                following.append([a, b])
            else:
                if low > a:
                    following.append([a, low])
                if high < b:
                    following.append([high, b])
        intervals = following
    return intervals


def section(geom, station):
    width, depth = geom["width_depth_mm"]
    holes = {1: [], 2: []}
    blocked = []
    for b in geom["bores"]:
        distance, radius = abs(station - b["station_mm"]), b["radius_mm"]
        if distance <= radius + TOL:
            blocked.append(b["axis_id"])
        if distance < radius:
            chord = math.sqrt(radius**2 - distance**2)
            holes[b["removed_interval_axis"]].append(
                [b["transverse_center_mm"] - chord, b["transverse_center_mm"] + chord]
            )
    regions = []
    for u in retained([-width / 2, width / 2], holes[1]):
        for v in retained([-depth / 2, depth / 2], holes[2]):
            if min(u[1] - u[0], v[1] - v[0]) > 1e-9:
                regions.append(
                    {
                        "bounds_uv_mm": [u, v],
                        "area_mm2": (u[1] - u[0]) * (v[1] - v[0]),
                        "centroid_uv_mm": [(u[0] + u[1]) / 2, (v[0] + v[1]) / 2],
                    }
                )
    return {
        "station_mm": station,
        "net_area_mm2": sum(r["area_mm2"] for r in regions),
        "material_region_count": len(regions),
        "regions": regions,
        "bore_or_tangency_ids": blocked,
        "elementary_intact_rectangle_applicable": not blocked and len(regions) == 1,
        "region_force_sharing_established": False if blocked else None,
    }


def comparisons(vector, props, references, width, depth):
    n, vu, vv, torque, mu, mv = vector
    area = props["net_area_mm2"]
    intact = props["elementary_intact_rectangle_applicable"]
    bu, bv = 6 * abs(mu) / (width * depth**2), 6 * abs(mv) / (depth * width**2)
    axial = n / area
    return {
        "signed_mean_parallel_stress_mpa": axial,
        "mean_tension_over_Ft_area_reference": max(axial, 0)
        / references["Ft_parallel"],
        "mean_compression_over_Fc_area_reference": max(-axial, 0)
        / references["Fc_parallel"],
        "mean_scope": "Necessary mean-force reference only; bending, regional sharing and staggered net-section interpretation remain separate.",
        "intact_Mu_bending_mpa": bu if intact else None,
        "intact_Mv_bending_mpa": bv if intact else None,
        "intact_tension_plus_bending_reference": (
            max(axial, 0) / references["Ft_parallel"] + (bu + bv) / references["Fb"]
        )
        if intact and n >= 0
        else None,
        "intact_compression_plus_bending_diagnostic": (
            max(-axial, 0) / references["Fc_parallel"] + (bu + bv) / references["Fb"]
        )
        if intact and n < 0
        else None,
        "intact_transverse_shear_component_references": [
            1.5 * abs(vu) / area / references["Fv_parallel"],
            1.5 * abs(vv) / area / references["Fv_parallel"],
        ]
        if intact
        else None,
        "intact_sum_absolute_transverse_shear_reference": 1.5
        * (abs(vu) + abs(vv))
        / area
        / references["Fv_parallel"]
        if intact
        else None,
        "torque_nmm_no_resistance_assigned": torque,
        "net_bending_or_shear_reference": None
        if not intact
        else "intact rectangle only",
        "scope": "Conditional elementary intact-section screen only; compression sum is not NDS 3.9-3, shear sum is a triangle-inequality screen. No short-block concentration, torque interaction, Ft-perpendicular or full oblique-group capacity.",
    }


def stations(geom, distances):
    events = [0.0, geom["grain_length_mm"], *distances]
    shoulders = [0.0, geom["grain_length_mm"]]
    for b in geom["bores"]:
        events.extend(
            [
                b["station_mm"],
                b["station_mm"] - b["radius_mm"],
                b["station_mm"] + b["radius_mm"],
            ]
        )
        shoulders.extend(
            [b["station_mm"] - b["radius_mm"], b["station_mm"] + b["radius_mm"]]
        )
    shoulders.sort()
    events.extend((a + b) / 2 for a, b in pairwise(shoulders))
    groups = []
    for s in sorted(events):
        require(
            -TOL <= s <= geom["grain_length_mm"] + TOL, "action lies outside grain span"
        )
        if groups and s - groups[-1][0] <= TOL:
            groups[-1].append(float(s))
        else:
            groups.append([float(s)])
    return [sum(g) / len(g) for g in groups]


def cut_records(actions, geom, references):
    rows, start = np.array(geom["grain_frame_rows_xyz"]), np.array(geom["start_xyz_mm"])
    positions = np.array([a["point_xyz_mm"] for a in actions])
    forces = np.array([a["force_xyz_n"] for a in actions])
    distances = (positions - start) @ rows[0]
    order = np.argsort(distances)
    distances = distances[order]
    original = np.c_[forces, np.cross(positions - start, forces)][order]
    cumulative = np.vstack([np.zeros(6), np.cumsum(original, axis=0)])
    for station in stations(geom, distances):
        props = section(geom, station)
        before = int(np.searchsorted(distances, station - TOL, side="left"))
        after = int(np.searchsorted(distances, station + TOL, side="right"))
        for limit, index in (("before", before), ("after", after)):
            own = -cumulative[index].copy()
            opposite = cumulative[-1] - cumulative[index]
            for q in (own, opposite):
                q[3:] -= np.cross(station * rows[0], q[:3])
            vector = np.r_[rows @ own[:3], rows @ own[3:]]
            other = np.r_[rows @ opposite[:3], rows @ opposite[3:]]
            yield {
                "station_mm": station,
                "limit": limit,
                "datum_xyz_mm": (start + station * rows[0]).tolist(),
                "negative_half_internal_grain_u_v_n_nmm": vector.tolist(),
                "same_internal_from_positive_half_grain_u_v_n_nmm": other.tolist(),
                "opposite_half_disagreement_n_nmm": (vector - other).tolist(),
                "action_count_negative_half": index,
                "on_plane_action_count": after - before,
                "section": props,
                "comparisons": comparisons(
                    vector, props, references, *geom["width_depth_mm"]
                ),
            }


def paths(actions, geom, finished, fv):
    grain = np.array(geom["grain_frame_rows_xyz"])[0]
    output = []
    for bore in geom["bores"]:
        identity = bore["axis_id"]
        own = [
            a
            for a in actions
            if a["kind"] == "bore_station_resultant" and a["identity"] == identity
        ]
        require(len(own) == 24, "cleat bore station count differs")
        values = np.array([np.array(a["force_xyz_n"]) @ grain for a in own])
        for sign in (-1, 1):
            saved = finished[(identity, sign)]
            require(
                abs(saved["bolt_grain_station_mm"] - bore["station_mm"]) < TOL,
                "finished path station differs",
            )
            demand = float(np.sum(np.maximum(sign * values, 0)))
            reference = fv * saved["minimum_finished_one_plane_area_mm2"]
            output.append(
                {
                    "axis_id": identity,
                    "grain_direction_sign": sign,
                    "same_state_directional_bore_parallel_n": demand,
                    "signed_net_bore_parallel_n": float(np.sum(values)),
                    "minimum_finished_one_plane_area_mm2": saved[
                        "minimum_finished_one_plane_area_mm2"
                    ],
                    "parallel_channel_reference_n": reference,
                    "parallel_channel_over_finished_path_reference": demand / reference,
                    "interval_boundary": saved["interval_boundary"],
                    "critical_distance_mm": saved["critical_distance_mm"],
                    "source_finished_path": saved,
                    "scope": "Existing Appendix E.3 single-fastener parallel channel and finished tangent paths only; no pair/group resistance, opposite-force cancellation, normal/bending/torque sharing or oblique-bore qualification.",
                }
            )
    return output


def run(args):
    output = args.output.resolve()
    require(
        output.is_relative_to(RAW) and not output.exists(),
        "fresh owned output required",
    )
    pins = dict(PINS)
    pins[args.nds_chapter3.resolve()] = CH3_SHA
    pins[Path(__file__).resolve()] = sha(Path(__file__))
    first = read(FIRST)
    for relative, digest in first["source_sha256"].items():
        path = ROOT / relative
        require(path not in pins or pins[path] == digest, "conflicting first-order pin")
        pins[path] = digest
    authenticate(pins)
    require(
        first["failure"] is None
        and len(first["states"]) == 12
        and not first["geometric_shortening_and_preload_stiffness"]
        and first["balancing_free_couples_added"] == 0,
        "first-order source incomplete",
    )
    traction = module(TRACTION, "timber_section_frozen_arithmetic")
    pins[traction.DOF] = traction.PINS[traction.DOF]
    pins[traction.PARSER] = traction.PINS[traction.PARSER]
    authenticate(pins)
    parser = module(traction.PARSER, "timber_section_dof_labels")
    labels = parser.parse_dof_file(traction.DOF)
    model, inputs, comparison = (
        read(p) for p in (traction.MODEL, traction.INPUTS, traction.COMPARISON)
    )
    proposal, material, component, group = (
        read(p) for p in (PROPOSAL, MATERIAL, COMPONENT, GROUP)
    )
    for relative, digest in proposal["proposal_step_sha256"].items():
        if Path(relative).name.startswith("top_outer_"):
            pins[ROOT / relative] = digest
    authenticate(pins)
    base, cf = (
        material["conditional_DF_L_No2_base_row"]["base_properties"],
        material["standard_section_scenarios"]["nominal_4x6"]["CF"],
    )
    references = {
        k: base[k] * cf.get(k, 1) * PSI_MPA
        for k in ("Ft_parallel", "Fc_parallel", "Fb", "Fv_parallel")
    }
    require(
        abs(
            references["Fv_parallel"]
            - component["component_references_mpa"]["Fv_parallel"]
        )
        < 1e-12,
        "finished-path material reference differs",
    )
    finished = {
        (p["axis_id"], p["grain_direction_sign"]): p
        for p in component["finished_paths"]
    }
    output.mkdir(parents=True, exist_ok=False)
    (output / ".gitignore").write_text("*\n")
    (output / "producer.py.snapshot").write_bytes(Path(__file__).read_bytes())
    states, geometries, census = (
        [],
        {},
        {
            "cut_records": 0,
            "intact_records": 0,
            "bore_or_tangency_records": 0,
            "reused_exterior_host_cuts": 0,
        },
    )
    metrics = (
        "mean_tension_over_Ft_area_reference",
        "mean_compression_over_Fc_area_reference",
        "intact_tension_plus_bending_reference",
        "intact_compression_plus_bending_diagnostic",
        "intact_sum_absolute_transverse_shear_reference",
    )
    with (
        np.load(traction.OPERATORS, allow_pickle=False) as operators,
        (output / "cut-records.jsonl.gz").open("wb") as packed,
        gzip.GzipFile(filename="", mode="wb", fileobj=packed, mtime=0) as stream,
    ):
        F, W = operators["F"], operators["W"]
        for state in first["states"]:
            side, case = state["side"], state["case_id"]
            body = f"top_outer_{side}_cleat"
            index = CASES.index(case)
            require(inputs["cases"][index]["case_id"] == case, "load order differs")
            prop = next(p for p in proposal["proposals"] if p["block"] == body)
            descriptor = next(
                m["reduced_geometry_descriptor"]
                for m in inputs["members"]
                if m["member_id"] == body
            )
            geom = geometry(state, prop, descriptor)
            if side in geometries:
                require(geom == geometries[side], "case geometry differs")
            geometries[side] = geom
            nodes = sorted(set(model["body_nodes"][body]))
            node_forces = {n: np.zeros(3) for n in nodes}
            for row, (node, direction) in enumerate(labels):
                if node in node_forces:
                    node_forces[node][direction - 1] = (
                        comparison["dead_load_factor"] * F[row, 2 * index]
                        + F[row, 2 * index + 1]
                    )
            weights = [
                traction.action(
                    "original_current_mapped_W_node",
                    str(n),
                    model["physical_node_coordinates_mm"][str(n)],
                    node_forces[n],
                )
                for n in nodes
            ]
            require(len(weights) == 20, "twenty nodal weights required")
            datum = np.array(state["common_datum_xyz_mm"])
            nodal_W = traction.wrench(weights, datum)
            body_index = model["body_names"].index(body)
            original_W = (
                comparison["dead_load_factor"]
                * W[6 * body_index : 6 * body_index + 6, 2 * index]
                + W[6 * body_index : 6 * body_index + 6, 2 * index + 1]
            )
            original_W[3:] *= 1000
            require(
                np.max(abs(nodal_W - state["current_weight_once_n_nmm"])) < 1e-7
                and np.max(abs(nodal_W - original_W)) < 1e-7,
                "original W differs",
            )
            actions = [*state["physical_cleat_actions"], *weights]
            closure = traction.wrench(actions, datum)
            require(
                np.max(abs(closure - state["physical_whole_cleat_residual_n_nmm"]))
                < 1e-7,
                "independent closure differs",
            )
            peaks, critical, count = {}, {}, 0
            for cut in cut_records(actions, geom, references):
                count += 1
                census["cut_records"] += 1
                intact = cut["section"]["elementary_intact_rectangle_applicable"]
                census["intact_records" if intact else "bore_or_tangency_records"] += 1
                for key in metrics:
                    value = cut["comparisons"][key]
                    if value is not None and (
                        key not in peaks or value > peaks[key]["comparisons"][key]
                    ):
                        peaks[key] = cut
                if not intact:
                    vector = np.array(cut["negative_half_internal_grain_u_v_n_nmm"])
                    score = float(np.linalg.norm(vector[4:]))
                    if not critical or score > critical["bending_moment_resultant_nmm"]:
                        critical = {"bending_moment_resultant_nmm": score, "cut": cut}
                stream.write(
                    (
                        json.dumps(
                            {"side": side, "case_id": case, **cut},
                            sort_keys=True,
                            allow_nan=False,
                        )
                        + "\n"
                    ).encode()
                )
            selected = []
            for b in geom["bores"]:
                own = min(
                    (
                        c
                        for c in cut_records(actions, geom, references)
                        if c["limit"] == "after"
                    ),
                    key=lambda c: abs(c["station_mm"] - b["station_mm"]),
                )
                selected.append({"axis_id": b["axis_id"], "cut": own})
            exterior = []
            for host, result in state["hosts"].items():
                old = next(
                    r
                    for r in group["host_states"]
                    if r["block"] == body and r["host"] == host and r["case_id"] == case
                )
                current = traction.wrench(result["physical_host_actions"], datum)
                delta = current - old["compatible_interface_wrench_on_host_n_nmm"]
                require(
                    np.max(abs(delta[:3])) < 0.002 and np.max(abs(delta[3:])) < 0.6,
                    "exterior host equilibrium reuse differs",
                )
                cuts = old["exterior_complete_host_cut_replay"]
                require(
                    all(c["exterior_transfer_demand_reusable"] for c in cuts),
                    "saved exterior cut inapplicable",
                )
                census["reused_exterior_host_cuts"] += len(cuts)
                exterior.append(
                    {
                        "host": host,
                        "current_minus_saved_interface_wrench_n_nmm": delta.tolist(),
                        "saved_cut_count": len(cuts),
                        "source_pointer": f"block-group-resistance/attempt02:host_states:{body}:{host}:{case}",
                        "scope": "Reuse saved exterior complete-host equilibrium totals within recorded tolerances; no intersecting host section, mechanics or component replay.",
                    }
                )
            states.append(
                {
                    "side": side,
                    "case_id": case,
                    "cut_record_count": count,
                    "point_action_count": len(actions),
                    "current_weight_once_n_nmm": nodal_W.tolist(),
                    "physical_whole_cleat_residual_n_nmm": closure.tolist(),
                    "conditional_cut_witnesses": peaks,
                    "deciding_unallocated_bore_section_witness": critical,
                    "bolt_center_sections": selected,
                    "finished_parallel_path_channels": paths(
                        actions, geom, finished, references["Fv_parallel"]
                    ),
                    "reused_exterior_complete_host_cuts": exterior,
                }
            )
    authenticate(pins)
    result = {
        "schema": "first_order_actual_corner_timber_sections/v1",
        "source_first_order_sha256": pins[FIRST],
        "conditional_CF_only_reference_mpa": references,
        "material_scenario": "DF-L No.2 nominal 4x6; normal duration, dry, unincised, normal temperature; Cfu=Cr=1. CL/CP, short-block stress distribution and R/T shear applicability not established by this screen.",
        "geometry": geometries,
        "summary": census,
        "states": states,
        "source_sha256": {
            str(p.relative_to(ROOT)) if p.is_relative_to(ROOT) else str(p): d
            for p, d in sorted(pins.items())
        },
        "runtime": {"python": sys.version.split()[0], "numpy": np.__version__},
        "limits": [
            "Finite reference-geometry grain-plane accounting of saved point/distributed samples and original nodal W included once; no frame or local mechanics solve.",
            "Connected bore-free rectangles receive elementary linear axial/bending and translational-shear references only. Near-load three-dimensional concentration, torsion and stability are not supplied.",
            "Physical through-bore sections have two or three disconnected material regions. Mean N/area is a necessary scalar reference, not a regional stress or net-group acceptance; bending/shear comparisons are withheld.",
            "The 3.1.2.2 staggered-array interpretation for orthogonal bores, interacting finished paths and complete oblique group are not established. No common strain or arbitrary force allocation is supplied.",
            "No Ft-perpendicular, EN F90 design conversion, arbitrary resistance, independent peak combination or balancing free couple is added.",
        ],
        "complete_joint_acceptance": False,
        "physical_release": False,
    }
    dump(output / "checks.json", result)
    dump(
        output / "receipt.json",
        {
            "source_sha256": result["source_sha256"],
            "output_sha256": {
                name: sha(output / name)
                for name in (
                    "checks.json",
                    "cut-records.jsonl.gz",
                    "producer.py.snapshot",
                )
            },
        },
    )
    print(json.dumps({"checks_sha256": sha(output / "checks.json"), "summary": census}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--nds-chapter3", required=True, type=Path)
    run(parser.parse_args())
