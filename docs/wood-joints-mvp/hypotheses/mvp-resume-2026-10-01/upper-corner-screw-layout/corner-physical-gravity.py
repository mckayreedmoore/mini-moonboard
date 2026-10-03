"""Replace equivalent nodal gravity in saved bottom-corner cuts only.

Parent executes this arithmetic. Current wall/washer/contact actions and whole
gravity wrenches stay fixed. Top corrected geometry is not remassed here.
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import importlib.machinery
import importlib.util
import json
import math
import sys
from pathlib import Path

import numpy as np

ROOT = Path.cwd().resolve()
HERE = (
    ROOT
    / "docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/upper-corner-screw-layout"
)
RAW = HERE / "rawlocal/corner-physical-gravity"
FINISHED = HERE / "rawlocal/corner-group-finish/attempt03"
NORMAL = HERE / "rawlocal/corner-split-closure/finite-pressure-attempt01"
HELPER = NORMAL / "producer.py.snapshot"
ADAPTER = (
    ROOT
    / "docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/current-springa-frame-input-adapter-attempt01/a12-rear/model.json"
)
MASS = (
    ROOT
    / "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-mass-centroids-attempt01/mass-centroids.json"
)
BOTTOM = HERE / "rawlocal/bottom-corner-transfer/first-order-attempt01/checks.json"
COMPARISON = HERE / "frame-250-attempt02/comparison.json"
CURRENT_MODEL = HERE / "operators-attempt02/model.json"
TOL = 1e-6
PINS = {
    NORMAL
    / "checks.json": "5676849306531c7b506990a5f82e82558f371afadcf7c2dc90bbe24d15c1655c",
    HELPER: "e090270a3bea195800ed3b04b806fe4ea0c5e221ae57faf01f602c8dba769d5e",
    MASS: "4c107b76d42d2a6f49b81c4857ba20bb236920932a7c34392c63e70d0882099a",
}


def math_helper():
    sys.dont_write_bytecode = True
    if hashlib.sha256(HELPER.read_bytes()).hexdigest() != PINS[HELPER]:
        raise ValueError("frozen normal/pressure helper changed")
    loader = importlib.machinery.SourceFileLoader(
        "frozen_corner_normal_math", str(HELPER)
    )
    spec = importlib.util.spec_from_loader(loader.name, loader)
    module = importlib.util.module_from_spec(spec)
    loader.exec_module(module)
    return module


def grain_helpers(pins, helper):
    modules = []
    for filename in ("corner-timber-sections.py", "corner-net-section.py"):
        path = HERE / filename
        helper.require(path in pins, "grain helper missing from frozen source closure")
        spec = importlib.util.spec_from_file_location(filename.replace("-", "_"), path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        modules.append(module)
    sections, net = modules
    helper.require(
        net.TORSION_SOURCE in pins,
        "torsion helper missing from frozen source closure",
    )
    return sections, net


def disk_segment(radius, offset):
    """Circle area and first moment about its center, on x <= offset."""
    if offset <= -radius:
        return 0.0, 0.0
    if offset >= radius:
        return math.pi * radius**2, 0.0
    root = math.sqrt(max(0.0, radius**2 - offset**2))
    return (
        radius**2 * (math.asin(offset / radius) + math.pi / 2) + offset * root,
        -2 * root**3 / 3,
    )


def volume_first(geom, axis, station):
    """Exact retained volume and local first moments of an axis-negative half.

    Saved geometry is one rectangular blank minus disjoint full transverse
    cylinders. Clipping a cylinder gives either a shorter cylinder or a disk
    segment extruded along its shaft axis; no CAD or discretization is used.
    """
    bounds = [
        [0.0, geom["grain_length_mm"]],
        *[[-d / 2, d / 2] for d in geom["width_depth_mm"]],
    ]
    station = min(bounds[axis][1], max(bounds[axis][0], station))
    own = [list(b) for b in bounds]
    own[axis][1] = station
    volume = math.prod(b - a for a, b in own)
    first = np.array([(a + b) / 2 for a, b in own]) * volume
    for bore in geom["bores"]:
        shaft = 3 - bore["removed_interval_axis"]
        center = np.zeros(3)
        center[0] = bore["station_mm"]
        center[bore["removed_interval_axis"]] = bore["transverse_center_mm"]
        if axis == shaft:
            removed = math.pi * bore["radius_mm"] ** 2 * (station - bounds[axis][0])
            center[axis] = (station + bounds[axis][0]) / 2
            moment = removed * center
        else:
            area, offset_first = disk_segment(bore["radius_mm"], station - center[axis])
            length = bounds[shaft][1] - bounds[shaft][0]
            removed = area * length
            moment = removed * center
            moment[axis] += offset_first * length
        volume -= removed
        first -= moment
    if abs(volume) < 1e-8:
        volume = 0.0
    if volume < 0:
        raise ValueError("negative retained half volume")
    return volume, first


def geometric_coupon(require):
    geom = {
        "grain_length_mm": 20.0,
        "width_depth_mm": [8.0, 10.0],
        "bores": [
            {
                "station_mm": 6.0,
                "transverse_center_mm": -2.0,
                "removed_interval_axis": 2,
                "radius_mm": 1.0,
            },
            {
                "station_mm": 14.0,
                "transverse_center_mm": 2.0,
                "removed_interval_axis": 2,
                "radius_mm": 1.0,
            },
            {
                "station_mm": 10.0,
                "transverse_center_mm": 1.0,
                "removed_interval_axis": 1,
                "radius_mm": 0.5,
            },
            {
                "station_mm": 12.0,
                "transverse_center_mm": -1.0,
                "removed_interval_axis": 1,
                "radius_mm": 0.5,
            },
        ],
    }
    results = []
    for name, axis, station, expected_v, expected_first in [
        ("full", 0, 20.0, 1600 - 21 * math.pi, [16000 - 215 * math.pi, 0.0, 0.0]),
        ("shorter_cylinders", 1, 0.0, 800 - 10.5 * math.pi, None),
        ("half_disk_segment", 0, 6.0, 480 - 4 * math.pi, None),
        ("empty", 0, 0.0, 0.0, [0.0, 0.0, 0.0]),
    ]:
        volume, first = volume_first(geom, axis, station)
        error = abs(volume - expected_v)
        if expected_first is not None:
            error = max(error, float(np.max(abs(first - expected_first))))
        if name == "shorter_cylinders":
            error = max(error, abs(first[1] - (-1600 + 18.5 * math.pi)))
        if name == "half_disk_segment":
            error = max(error, abs(first[0] - (1440 - 24 * math.pi + 16 / 3)))
        require(error < 1e-9, f"volume/first-moment known answer differs: {name}")
        results.append(
            {
                "name": name,
                "volume_mm3": volume,
                "first_moment_grain_u_v_mm4": first.tolist(),
                "error": error,
            }
        )
    return {"known_answers_satisfied": True, "cases": results}


def prepare_points(actions, frame, start, factor=1.0):
    points = (np.array([a["point_xyz_mm"] for a in actions]) - start) @ frame.T
    forces = np.array([a["force_xyz_n"] for a in actions]) @ frame.T * factor
    couples = (
        np.array([a.get("free_couple_xyz_nmm", [0.0, 0.0, 0.0]) for a in actions])
        @ frame.T
        * factor
    )
    return points, np.c_[forces, np.cross(points, forces) + couples]


def point_gravity(prepared, axis, station, limit):
    points, wrenches = prepared
    included = (
        points[:, axis] < station - TOL
        if limit == "before"
        else points[:, axis] <= station + TOL
    )
    value = wrenches[included].sum(axis=0)
    value[3:] -= np.cross(np.eye(3)[axis] * station, value[:3])
    return value


def build(output):
    helper = math_helper()
    require, read, dump, sha = helper.require, helper.read, helper.dump, helper.sha
    output = Path(output).resolve()
    require(
        output.is_relative_to(RAW) and output != RAW and not output.exists(),
        "fresh owned output child required",
    )
    pins = dict(PINS)
    helper.authenticate(pins)
    prior = read(NORMAL / "checks.json")
    pins.update({ROOT / p: digest for p, digest in prior["source_sha256"].items()})
    helper.authenticate(pins)
    sections, net = grain_helpers(pins, helper)
    finished, bottom, adapter, masses, comparison, current_model = [
        read(p)
        for p in [
            FINISHED / "checks.json",
            BOTTOM,
            ADAPTER,
            MASS,
            COMPARISON,
            CURRENT_MODEL,
        ]
    ]
    factor = comparison["dead_load_factor"]
    members_path = (
        HERE.parent / "member-screen-attempt02/four-screw-layout01/member-results.json"
    )
    require(
        members_path in pins, "material references missing from frozen source closure"
    )
    member_refs = {
        m["member"]: m["conditional_material"]["CF_only_reference_mpa"]
        for m in read(members_path)["cases"][0]["members"]
    }
    source_rows = {
        r["body"]: r for r in adapter["gravity_load_audits"]["member_self_weight_rows"]
    }
    mass_rows = {r["name"]: r for r in masses["rows"]}
    geom_records, whole_matches, mapped_points = {}, [], {}
    state_map = {(s["cleat"], s["case_id"]): s for s in bottom["states"]}
    for block in sorted({s["cleat"] for s in bottom["states"]}):
        geom = finished["geometries"][block]
        frame, start = (
            np.array(geom["grain_frame_rows_xyz"]),
            np.array(geom["start_xyz_mm"]),
        )
        volume, first = volume_first(geom, 0, geom["grain_length_mm"])
        source = source_rows[block]
        center = start + frame.T @ (first / volume)
        density = source["source_mass_kg"] / volume * 1e9
        require(
            abs(density - mass_rows[block]["density_kg_m3"]) < TOL,
            "physical timber density does not match source",
        )
        require(
            np.max(abs(center - source["source_centroid_xyz_mm"])) < TOL,
            "physical timber centroid does not match source",
        )
        require(
            abs(volume - geom["analytic_finished_volume_mm3"]) < TOL,
            "physical timber volume differs",
        )
        hardware = [
            {
                "point_xyz_mm": r["application_point_xyz_mm"],
                "force_xyz_n": r["force_xyz_n"],
                "free_couple_xyz_nmm": r["couple_xyz_nmm_about_application_point"],
                "source_name": r["source_name"],
            }
            for r in adapter["gravity_load_audits"]["hardware_receiver_point_loads"]
            if r["receiver_body"] == block
        ]
        require(len(hardware) == 12, "bottom hardware receiver count differs")
        body_force = frame @ np.array(source["gravity_force_xyz_n"]) * factor / volume
        full_physical = np.r_[body_force * volume, np.cross(first, body_force)]
        hardware_points = prepare_points(hardware, frame, start, factor)
        full_physical += hardware_points[1].sum(axis=0)
        for key, state in state_map.items():
            if key[0] != block:
                continue
            mapped_points[key] = prepare_points(
                state["own_weight_actions_once"], frame, start
            )
            mapped = mapped_points[key][1].sum(axis=0)
            error = full_physical - mapped
            require(
                np.max(abs(error[:3])) < TOL and np.max(abs(error[3:])) < TOL,
                "whole gravity wrench changed",
            )
            whole_matches.append(
                {
                    "block": block,
                    "case_id": key[1],
                    "source_total_gravity_wrench_at_grain_start_n_nmm": mapped.tolist(),
                    "physical_minus_mapped_n_nmm": error.tolist(),
                }
            )
        geom_records[block] = {
            "geometry": geom,
            "frame": frame,
            "start": start,
            "body_force": body_force,
            "hardware_points": hardware_points,
            "density_kg_m3": density,
            "centroid_xyz_mm": center.tolist(),
            "volume_mm3": volume,
        }
    top_mismatch = []
    current_deltas = {r["body"]: r for r in current_model["wood_mass_changes"]}
    for block in ["top_outer_left_cleat", "top_outer_right_cleat"]:
        geom = finished["geometries"][block]
        volume, first = volume_first(geom, 0, geom["grain_length_mm"])
        frame, start = (
            np.array(geom["grain_frame_rows_xyz"]),
            np.array(geom["start_xyz_mm"]),
        )
        source = source_rows[block]
        delta = current_deltas[block]
        current_mass = source["source_mass_kg"] + delta["wood_mass_change_kg"]
        timber_origin = np.r_[
            source["gravity_force_xyz_n"],
            source["gravity_moment_about_global_origin_xyz_nmm"],
        ]
        timber_origin += delta["gravity_wrench_change_about_global_origin_n_nmm"]
        center = start + frame.T @ (first / volume)
        uniform_origin = np.r_[timber_origin[:3], np.cross(center, timber_origin[:3])]
        top_mismatch.append(
            {
                "block": block,
                "corrected_geometry_centroid_xyz_mm": (
                    start + frame.T @ (first / volume)
                ).tolist(),
                "saved_source_centroid_xyz_mm": source_rows[block][
                    "source_centroid_xyz_mm"
                ],
                "source_base_mass_kg": source["source_mass_kg"],
                "current_corrected_timber_mass_kg": current_mass,
                "current_corner_delta": delta,
                "current_timber_gravity_origin_wrench_n_nmm": timber_origin.tolist(),
                "uniform_same_mass_minus_current_timber_origin_wrench_n_nmm": (
                    uniform_origin - timber_origin
                ).tolist(),
                "corrected_volume_mm3": volume,
                "current_density_if_uniform_over_corrected_stock_kg_m3": current_mass
                / volume
                * 1e9,
                "physical_gravity_replacement_adopted": False,
            }
        )
    output.mkdir(parents=True, exist_ok=False)
    (output / ".gitignore").write_text("*\n")
    snapshot = output / "producer.py.snapshot"
    snapshot.write_bytes(Path(__file__).read_bytes())
    digest = sha(Path(__file__))
    pins[snapshot] = digest
    known = geometric_coupon(require)
    states, count, peak, peak_pressure, witness_updates = {}, 0, None, None, []
    grain_states, grain_peaks = {}, {}
    deciding_keys = {
        (
            b["witness"]["block"],
            b["witness"]["case_id"],
            b["witness"]["axis"],
            b["witness"]["station_mm"],
            b["witness"]["limit"],
        )
        for b in prior["positive_normal_lower_bound_existing_bridge_traces"]
    }
    with (
        gzip.open(FINISHED / "cuts.jsonl.gz", "rt") as source_stream,
        gzip.open(output / "cuts.jsonl.gz", "wt") as target_stream,
    ):
        for line in source_stream:
            cut = json.loads(line)
            block = cut["block"]
            if block not in geom_records:
                continue
            own = geom_records[block]
            axis, station, limit = (
                cut["normal_axis_grain_u_v"],
                cut["station_mm"],
                cut["limit"],
            )
            mapped = point_gravity(
                mapped_points[(block, cut["case_id"])],
                axis,
                station,
                limit,
            )
            volume, first = volume_first(own["geometry"], axis, station)
            body = np.r_[
                volume * own["body_force"],
                np.cross(first - np.eye(3)[axis] * station * volume, own["body_force"]),
            ]
            physical = body + point_gravity(
                own["hardware_points"],
                axis,
                station,
                limit,
            )
            perm = [axis, (axis + 1) % 3, (axis + 2) % 3]
            change = mapped - physical
            q = (
                np.array(cut["signed_internal_n_nmm"])
                + np.r_[change[:3][perm], change[3:][perm]]
            ).tolist()
            record = {
                "block": block,
                "case_id": cut["case_id"],
                "axis": axis,
                "station_mm": station,
                "limit": limit,
                "original_signed_internal_n_nmm": cut["signed_internal_n_nmm"],
                "physical_gravity_signed_internal_n_nmm": q,
                "mapped_gravity_negative_half_n_nmm": np.r_[
                    mapped[:3][perm], mapped[3:][perm]
                ].tolist(),
                "physical_gravity_negative_half_n_nmm": np.r_[
                    physical[:3][perm], physical[3:][perm]
                ].tolist(),
            }
            count += 1
            if axis == 0:
                own_section = sections.section(own["geometry"], station)
                nominal = net.nominal_section(
                    q, own_section["regions"], member_refs[block]
                )
                corners = [
                    c
                    for region in nominal["regions"]
                    for c in region["longitudinal_corners"]
                ]
                metrics = {
                    "grain_tension_over_Ft": max(
                        c["comparisons"]["total_tension_over_Ft"] for c in corners
                    ),
                    "grain_compression_over_Fc": max(
                        c["comparisons"]["total_compression_over_Fc"] for c in corners
                    ),
                    "grain_bending_over_Fb": max(
                        c["comparisons"]["absolute_bending_over_Fb"] for c in corners
                    ),
                    "grain_axial_plus_bending_reference_sum": max(
                        c["comparisons"]["axial_plus_bending_reference_sum"]
                        for c in corners
                    ),
                    "grain_regional_shear_torsion_over_Fv": max(
                        r["same_state_shear_bound_over_Fv"] for r in nominal["regions"]
                    ),
                }
                record["nominal_grain_regions"] = nominal["regions"]
                record["nominal_grain_metrics"] = metrics
                grain_key = (block, cut["case_id"])
                grain_row = grain_states.setdefault(
                    grain_key,
                    {
                        "block": block,
                        "case_id": cut["case_id"],
                        "cut_count": 0,
                        "peak_witnesses": {},
                    },
                )
                grain_row["cut_count"] += 1
                for name, value in metrics.items():
                    witness = {
                        "value": value,
                        "block": block,
                        "case_id": cut["case_id"],
                        "station_mm": station,
                        "limit": limit,
                        "signed_cut_n_nmm": q,
                    }
                    for peaks in (grain_row["peak_witnesses"], grain_peaks):
                        if name not in peaks or value > peaks[name]["value"]:
                            peaks[name] = witness
                target_stream.write(json.dumps(record, allow_nan=False) + "\n")
                continue
            target_stream.write(json.dumps(record, allow_nan=False) + "\n")
            normal = helper.normal_bound(
                q, helper.transverse_hull(own["geometry"], axis)
            )
            pressure = helper.finite_band_pressure(q, own["geometry"], axis)
            witness = {
                **record,
                "normal_hull": normal,
                "finite_band_pressure": pressure,
            }
            key = (block, cut["case_id"], axis)
            row = states.setdefault(
                key,
                {
                    "block": block,
                    "case_id": key[1],
                    "axis": axis,
                    "cut_count": 0,
                    "positive_normal_tensile_bound_count": 0,
                    "finite_pressure_count": 0,
                    "maximum_normal_tensile_bound_witness": witness,
                },
            )
            row["cut_count"] += 1
            t = normal["minimum_tensile_normal_resultant_n"]
            row["positive_normal_tensile_bound_count"] += t > 0
            row["finite_pressure_count"] += "pressure_peak_mpa" in pressure
            if (
                t
                > row["maximum_normal_tensile_bound_witness"]["normal_hull"][
                    "minimum_tensile_normal_resultant_n"
                ]
            ):
                row["maximum_normal_tensile_bound_witness"] = witness
            if (
                peak is None
                or t > peak["normal_hull"]["minimum_tensile_normal_resultant_n"]
            ):
                peak = witness
            if "pressure_peak_mpa" in pressure and (
                peak_pressure is None
                or pressure["pressure_peak_mpa"]
                > peak_pressure["finite_band_pressure"]["pressure_peak_mpa"]
            ):
                peak_pressure = witness
            if (block, cut["case_id"], axis, station, limit) in deciding_keys:
                witness_updates.append(witness)
    helper.authenticate(pins)
    require(sha(Path(__file__)) == digest, "executed producer changed")
    require(
        len(states) == 24 and len(witness_updates) == 2 and len(grain_states) == 12,
        "incomplete bottom six-case/transverse/grain comparison",
    )
    result = {
        "schema": "bottom_corner_physical_gravity/v1",
        "status": "BOTTOM_PHYSICAL_GRAVITY_SUBCUT_COMPARISON_COMPLETE",
        "coupon": known,
        "all_bottom_cut_count": count,
        "states": [states[k] for k in sorted(states)],
        "updated_grain_nominal_comparisons": {
            "cut_count": sum(r["cut_count"] for r in grain_states.values()),
            "states": [grain_states[k] for k in sorted(grain_states)],
            "peak_witnesses": grain_peaks,
            "conditional_CF_only_reference_mpa": {
                b: member_refs[b] for b in sorted(geom_records)
            },
            "all_computed_reference_ratios_below_one": all(
                r["value"] < 1 for r in grain_peaks.values()
            ),
            "hypotheses": net.ASSUMPTIONS,
            "scope": "Established nominal longitudinal stress and regional shear/torsion comparisons recomputed from changed full grain cuts; not a new interaction law, compatible 3D stress field, transverse splitting capacity or complete-joint acceptance.",
        },
        "whole_gravity_matches": whole_matches,
        "bottom_uniform_density_and_centroid": {
            b: {k: g[k] for k in ["density_kg_m3", "centroid_xyz_mm", "volume_mm3"]}
            for b, g in geom_records.items()
        },
        "top_corrected_geometry_mapping_mismatch": top_mismatch,
        "maximum_normal_tensile_bound_witness": peak,
        "maximum_finite_pressure_witness": peak_pressure,
        "original_positive_peak_witness_updates": witness_updates,
        "source_sha256": {helper.path_key(p): d for p, d in sorted(pins.items())},
        "executed_producer_sha256": digest,
        "limits": [
            "Only the two bottom blocks receive physical uniform timber gravity; all saved wall, washer and contact loads are retained.",
            "Allocated hardware receiver point forces/free couples remain the original unexpanded source approximation; this does not qualify their spatial transfer route.",
            "The exact total gravity force and moment are checked unchanged, with original dead-load factor and source density/centroid.",
            "Only the original finite cut stations are compared; new hardware-point events, continuous maxima, full stress compatibility and joint capacity are not inferred.",
            "Top metadata includes the current corrected-frame corner delta as well as the older base selfweight. Uniform-gravity applicability is recorded without changing top force, mass or moment.",
            "Established grain-normal nominal resistance comparisons are recomputed on changed full cuts using the original references and hypotheses; no transverse splitting capacity or new interaction law is assigned.",
        ],
        "additional_bolt_tension_n": 0.0,
        "splitting_capacity_n": None,
        "complete_joint_acceptance": False,
        "formal_criterion_acceptance": False,
        "fabrication_release": False,
        "physical_release": False,
    }
    dump(output / "checks.json", result)
    dump(
        output / "receipt.json",
        {
            "source_sha256": result["source_sha256"],
            "output_sha256": {p.name: sha(p) for p in output.iterdir()},
        },
    )
    return {
        "status": result["status"],
        "checks_sha256": sha(output / "checks.json"),
        "maximum_normal_tensile_bound_witness": peak,
        "all_bottom_cut_count": count,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    print(json.dumps(build(parser.parse_args().output), allow_nan=False))
