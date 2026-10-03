"""Finite normal-force census on the preserved corner cut inventory.

Parent executes this static arithmetic. No timber tensile capacity, new bolt
reaction, preload, contact pressure, crack model or joint acceptance is added.
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import math
from pathlib import Path

ROOT = Path.cwd().resolve()
HERE = (
    ROOT
    / "docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/upper-corner-screw-layout"
)
SOURCE = HERE / "rawlocal/corner-group-finish/attempt03"
RAW = HERE / "rawlocal/corner-split-closure"
PINS = {
    SOURCE
    / "checks.json": "2ae3a84f273823dc6ca751e6fdddab8e0d70425ee7b34e1e38ebc79d5b672f23",
    SOURCE
    / "cuts.jsonl.gz": "a60131eaeff3e5bb46579156d31fbfe3423de2848ac2bbb202901013697a5627",
    SOURCE
    / "receipt.json": "f1d8ad0f204be457f5b8eba2e8185828456251ae7fb67aa945bb7477bacd2f62",
}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def read(path):
    return json.loads(Path(path).read_text())


def dump(path, value):
    Path(path).write_text(
        json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n"
    )


def authenticate(pins):
    for path, digest in pins.items():
        require(sha(path) == digest, f"changed frozen source: {path}")


def path_key(path):
    return str(path.relative_to(ROOT)) if path.is_relative_to(ROOT) else str(path)


def normal_bound(q, bounds):
    """Exact minimum tensile force over an unbounded rectangle support hull.

    Point resultants supply only a normal equilibrium witness. Their pressure
    is unbounded; the returned tensile force is a lower bound for any real tie.
    """
    require(len(q) == 6 and all(math.isfinite(v) for v in q), "invalid full cut wrench")
    center = [(lo + hi) / 2 for lo, hi in bounds]
    half = [(hi - lo) / 2 for lo, hi in bounds]
    require(min(half) > 0, "nonpositive support hull")
    target = [q[0], -q[5], q[4]]
    moments = [(target[j + 1] - center[j] * q[0]) / half[j] for j in range(2)]
    variation = max(abs(q[0]), *[abs(v) for v in moments])
    tension, compression = (variation + q[0]) / 2, (variation - q[0]) / 2
    coordinates = [v / variation if variation else 0.0 for v in moments]
    corners = []
    recovered = [0.0, 0.0, 0.0]
    for sp in (-1, 1):
        for sq in (-1, 1):
            p, r = center[0] + sp * half[0], center[1] + sq * half[1]
            own_t = tension * (1 + sp * coordinates[0]) * (1 + sq * coordinates[1]) / 4
            own_c = (
                compression * (1 - sp * coordinates[0]) * (1 - sq * coordinates[1]) / 4
            )
            force = own_t - own_c
            for j, value in enumerate((force, p * force, r * force)):
                recovered[j] += value
            corners.append(
                {
                    "pq_mm": [p, r],
                    "tensile_normal_point_n": own_t,
                    "compressive_normal_point_n": own_c,
                }
            )
    error = max(abs(a - b) for a, b in zip(recovered, target, strict=True))
    require(error < 1e-7, "normal point-wrench recovery differs")
    require(
        all(
            min(c["tensile_normal_point_n"], c["compressive_normal_point_n"]) >= -1e-12
            for c in corners
        ),
        "negative nonnegative-measure weight",
    )
    return {
        "minimum_tensile_normal_resultant_n": tension,
        "compression_normal_resultant_at_minimum_n": compression,
        "normal_resultant_and_centered_moment_over_halfwidth_n": [q[0], *moments],
        "compression_only_normal_hull_feasible": tension == 0,
        "point_normal_witnesses": corners,
        "maximum_normal_recovery_error_n_nmm": error,
        "retained_full_signed_cut_n_nmm": q,
        "unresolved_shear_shear_torque_n_n_nmm": q[1:4],
        "pressure_or_tie_capacity_assigned": False,
    }


def coupon():
    bounds = [[0.0, 10.0], [-5.0, 5.0]]
    cases = [
        ("center_compression", [-10, 7, -3, 11, 0, 50], 0.0, 10.0),
        ("eccentric_compression_inside_hull", [-10, 7, -3, 11, 0, 90], 0.0, 10.0),
        ("eccentric_compression_outside_hull", [-10, 7, -3, 11, 0, 110], 1.0, 11.0),
        ("pure_normal_bending_couple", [0, 7, -3, 11, 0, 50], 5.0, 5.0),
        ("center_tension", [5, 7, -3, 11, 0, -25], 5.0, 0.0),
    ]
    results = []
    for name, q, t, c in cases:
        result = normal_bound(q, bounds)
        require(
            abs(result["minimum_tensile_normal_resultant_n"] - t) < 1e-12
            and abs(result["compression_normal_resultant_at_minimum_n"] - c) < 1e-12,
            f"normal-hull known answer differs: {name}",
        )
        require(
            result["retained_full_signed_cut_n_nmm"] == q
            and result["unresolved_shear_shear_torque_n_n_nmm"] == [7, -3, 11],
            "coupon discarded tangential components",
        )
        results.append(
            {
                "name": name,
                "expected_tension_n": t,
                "expected_compression_n": c,
                **result,
            }
        )
    return {"known_answers_satisfied": True, "cases": results}


def transverse_hull(geom, axis):
    require(axis in (1, 2), "not a transverse plane")
    length = geom["grain_length_mm"]
    require(
        all(
            b["removed_interval_axis"] in (1, 2)
            and 0 < b["station_mm"] - b["radius_mm"]
            and b["station_mm"] + b["radius_mm"] < length
            for b in geom["bores"]
        ),
        "grain-end corners are not certified retained material",
    )
    bounds = [[0, length], *[[-v / 2, v / 2] for v in geom["width_depth_mm"]]]
    return [bounds[(axis + 1) % 3], bounds[(axis + 2) % 3]]


def build(output):
    require(
        (ROOT / "AGENTS.md").is_file() and HERE.is_dir(), "run from repository root"
    )
    output = Path(output).resolve()
    require(
        output.is_relative_to(RAW) and output != RAW and not output.exists(),
        "fresh owned output child required",
    )
    pins = dict(PINS)
    authenticate(pins)
    source = read(SOURCE / "checks.json")
    for name, digest in source["source_sha256"].items():
        path = ROOT / name
        require(path not in pins or pins[path] == digest, "conflicting source pin")
        pins[path] = digest
    authenticate(pins)
    output.mkdir(parents=True, exist_ok=False)
    (output / ".gitignore").write_text("*\n")
    live_source = Path(__file__).resolve()
    snapshot = output / "producer.py.snapshot"
    snapshot.write_bytes(live_source.read_bytes())
    live_digest = sha(live_source)
    pins[snapshot] = live_digest
    known = coupon()
    states, peak, affine_peak = {}, None, None
    target_peak = source["peak_witnesses"]["perpendicular_opening_normal_mpa"]
    target_key = (
        target_peak["block"],
        target_peak["case_id"],
        target_peak["axis"],
        target_peak["station_mm"],
        target_peak["limit"],
    )
    total = 0
    with gzip.open(SOURCE / "cuts.jsonl.gz", "rt") as stream:
        for line in stream:
            cut = json.loads(line)
            axis = cut["normal_axis_grain_u_v"]
            if axis == 0:
                continue
            key = (cut["block"], cut["case_id"], axis)
            geom = source["geometries"][cut["block"]]
            result = normal_bound(
                cut["signed_internal_n_nmm"], transverse_hull(geom, axis)
            )
            witness = {
                "block": cut["block"],
                "case_id": cut["case_id"],
                "axis": axis,
                "station_mm": cut["station_mm"],
                "limit": cut["limit"],
                "normal_hull_bounds_pq_mm": transverse_hull(geom, axis),
                **result,
                "source_affine_maximum_normal_mpa": cut["normal_field"][
                    "maximum_normal_mpa"
                ],
                "source_opposite_half_disagreement_n_nmm": cut[
                    "opposite_half_disagreement_n_nmm"
                ],
            }
            row = states.setdefault(
                key,
                {
                    "block": key[0],
                    "case_id": key[1],
                    "axis": key[2],
                    "cut_limit_count": 0,
                    "normal_hull_compression_feasible_count": 0,
                    "positive_normal_tensile_bound_count": 0,
                    "normal_tensile_bound_above_1n_count": 0,
                    "positive_affine_but_normal_hull_compression_feasible_count": 0,
                    "maximum_normal_tensile_bound_witness": witness,
                },
            )
            t = result["minimum_tensile_normal_resultant_n"]
            row["cut_limit_count"] += 1
            row["normal_hull_compression_feasible_count"] += t == 0
            row["positive_normal_tensile_bound_count"] += t > 0
            row["normal_tensile_bound_above_1n_count"] += t > 1
            row["positive_affine_but_normal_hull_compression_feasible_count"] += (
                t == 0 and cut["normal_field"]["maximum_normal_mpa"] > 1e-10
            )
            if (
                t
                > row["maximum_normal_tensile_bound_witness"][
                    "minimum_tensile_normal_resultant_n"
                ]
            ):
                row["maximum_normal_tensile_bound_witness"] = witness
            if peak is None or t > peak["minimum_tensile_normal_resultant_n"]:
                peak = witness
            if (*key, cut["station_mm"], cut["limit"]) == target_key:
                affine_peak = witness
            total += 1
    require(
        len(states) == 48
        and total == source["transverse_cut_limit_count"] == 51312
        and affine_peak is not None,
        "incomplete four-corner six-case transverse census",
    )
    authenticate(pins)
    require(
        sha(live_source) == live_digest, "executed producer changed during calculation"
    )
    result = {
        "schema": "corner_normal_hull_census/v1",
        "status": "FINITE_NORMAL_TENSION_CENSUS_COMPLETE",
        "block_count": 4,
        "case_count": 6,
        "block_case_orientation_count": len(states),
        "transverse_cut_limit_count": total,
        "coupon": known,
        "states": [states[key] for key in sorted(states)],
        "maximum_necessary_normal_tensile_resultant_witness": peak,
        "original_affine_opening_peak_hull_result": affine_peak,
        "source_sha256": {path_key(p): digest for p, digest in sorted(pins.items())},
        "executed_producer_sha256": live_digest,
        "limits": [
            "The rectangle is the convex hull of the exact retained section because all transverse bores miss the grain-end corners. Internal circles/strips do not remove those corners.",
            "The minimum normal tensile force is an exact resultant lower bound with unbounded point pressure over that hull, not a capacity, finite pressure proof or bolt allocation.",
            "A zero tensile lower bound establishes unconstrained normal-wrench compression feasibility only; shear, shear and torque remain unresolved in this subcheck.",
            "The original pressure mapping, same-state loads, finite cuts and nonzero source residual are preserved. Very small positive bounds may reflect those retained numerical residuals.",
            "The above-1-N count is an informational census, not a tolerance, design gate or acceptance threshold.",
            "No extra bolt tension, preload, friction, washer capacity, material Ft-perpendicular, fracture or joint capacity is credited.",
        ],
        "Ft_perpendicular_mpa": None,
        "splitting_capacity_n": None,
        "complete_joint_acceptance": False,
        "formal_criterion_acceptance": False,
        "fabrication_release": False,
        "physical_release": False,
    }
    dump(output / "checks.json", result)
    outputs = {p.name: sha(p) for p in output.iterdir()}
    dump(
        output / "receipt.json",
        {"source_sha256": result["source_sha256"], "output_sha256": outputs},
    )
    return {
        "status": result["status"],
        "cut_count": total,
        "maximum_necessary_normal_tensile_resultant_witness": peak,
        "original_affine_opening_peak_hull_result": affine_peak,
        "checks_sha256": outputs["checks.json"],
    }


def finite_band_pressure(q, geom, axis):
    """Two bore-free grain-end rectangles, with exact normal resultants.

    This sufficient construction is not an optimal pressure distribution.
    No joint compatibility, pressure law or tensile resistance is inferred.
    """
    bounds = transverse_hull(geom, axis)
    normal = normal_bound(q, bounds)
    if normal["minimum_tensile_normal_resultant_n"] > 0:
        return {"status": "NECESSARY_NORMAL_TENSION", **normal}
    if q[0] == 0:
        return {"status": "ZERO_NORMAL_WRENCH", "pressure_peak_mpa": 0.0, **normal}
    grain_index = next(i for i in range(2) if (axis + 1 + i) % 3 == 0)
    transverse_index = 1 - grain_index
    centroid = [-q[5] / q[0], q[4] / q[0]]
    length = geom["grain_length_mm"]
    clear = min(
        min(b["station_mm"] - b["radius_mm"], length - b["station_mm"] - b["radius_mm"])
        for b in geom["bores"]
    )
    grain_center, transverse_center = centroid[grain_index], centroid[transverse_index]
    low, high = bounds[transverse_index]
    width = 2 * min(transverse_center - low, high - transverse_center)
    height = min(clear, length / 2, 2 * min(grain_center, length - grain_center))
    if min(width, height) <= 0:
        return {"status": "NO_FINITE_BAND_WITNESS", **normal}
    upper_fraction = (grain_center - height / 2) / (length - height)
    require(-1e-12 <= upper_fraction <= 1 + 1e-12, "negative band compression")
    # Remove roundoff at a band-centroid boundary; do not change the source wrench.
    upper_fraction = min(1.0, max(0.0, upper_fraction))
    patches, recovered = [], [0.0, 0.0, 0.0]
    for end, fraction in enumerate((1 - upper_fraction, upper_fraction)):
        center = list(centroid)
        center[grain_index] = height / 2 if end == 0 else length - height / 2
        force = q[0] * fraction
        for i, value in enumerate((force, force * center[0], force * center[1])):
            recovered[i] += value
        rectangle = [
            [transverse_center - width / 2, transverse_center + width / 2],
            [0.0, height] if end == 0 else [length - height, length],
        ]
        if grain_index == 0:
            rectangle.reverse()
        patches.append(
            {
                "bounds_pq_mm": rectangle,
                "centroid_pq_mm": center,
                "compressive_force_n": -force,
                "area_mm2": width * height,
                "constant_pressure_mpa": -force / (width * height),
            }
        )
    error = max(abs(a - b) for a, b in zip(recovered, [q[0], -q[5], q[4]], strict=True))
    require(error < 1e-7, "finite patch normal-wrench recovery differs")
    return {
        "status": "FINITE_COMPRESSION_BAND_WITNESS",
        "patches": patches,
        "pressure_peak_mpa": max(p["constant_pressure_mpa"] for p in patches),
        "minimum_grain_end_bore_clearance_mm": clear,
        "maximum_normal_recovery_error_n_nmm": error,
        "retained_full_signed_cut_n_nmm": q,
        "unresolved_shear_shear_torque_n_n_nmm": q[1:4],
    }


def band_coupon():
    geom = {
        "grain_length_mm": 10.0,
        "width_depth_mm": [10.0, 10.0],
        "bores": [{"removed_interval_axis": 2, "station_mm": 5.0, "radius_mm": 1.0}],
    }
    results = []
    for name, q, expected in [
        ("centered_compression", [-10, 7, -3, 11, -50, 0], 0.125),
        ("eccentric_compression", [-10, 7, -3, 11, -10, 40], 2.5),
        ("zero_normal_with_nonzero_tangentials", [0, 7, -3, 11, 0, 0], 0.0),
        ("boundary_centroid", [-10, 7, -3, 11, -50, 50], None),
    ]:
        result = finite_band_pressure(q, geom, 1)
        require(
            (expected is None and result["status"] == "NO_FINITE_BAND_WITNESS")
            or (
                expected is not None
                and abs(result["pressure_peak_mpa"] - expected) < 1e-12
            ),
            f"finite band known answer differs: {name}",
        )
        require(
            result["unresolved_shear_shear_torque_n_n_nmm"] == [7, -3, 11],
            "finite pressure discarded tangential components",
        )
        results.append({"name": name, "expected_pressure_peak_mpa": expected, **result})
    return {"known_answers_satisfied": True, "cases": results}


def existing_bridge_trace(source, witness):
    """Describe the existing bottom side-bolt chain, without allocating new load."""
    block = witness["block"]
    geom = source["geometries"][block]
    saved = read(
        HERE / "rawlocal/bottom-corner-transfer/first-order-attempt01/checks.json"
    )
    state = next(
        s
        for s in saved["states"]
        if s["cleat"] == block and s["case_id"] == witness["case_id"]
    )
    require(witness["axis"] == 1, "positive bound is not the expected side-bolt plane")
    bolts = []
    for host, data in state["hosts"].items():
        for bolt in data["state"]["bolts"]:
            if "/side_" not in bolt["axis_id"]:
                continue
            bore = next(b for b in geom["bores"] if b["axis_id"] == bolt["axis_id"])
            ends = [
                {
                    "role": e["physical_outer_role"],
                    "member": e["physical_wood_member"],
                    "existing_wood_pressure_peak_mpa": e["wood_contact"][
                        "pressure_peak_mpa"
                    ],
                    "existing_end_moment_nmm": e["moment_nmm"],
                }
                for e in bolt["end_contacts"]
            ]
            require(
                {e["member"] for e in ends} == {block, host},
                "unexpected bolt anchorage members",
            )
            require(
                -geom["width_depth_mm"][0] / 2
                < witness["station_mm"]
                < geom["width_depth_mm"][0] / 2,
                "side-bolt shaft does not cross witness plane",
            )
            bolts.append(
                {
                    "axis_id": bolt["axis_id"],
                    "host": host,
                    "crosses_u_normal_witness_plane": True,
                    "axis_plane_pq_v_grain_mm": [
                        bore["transverse_center_mm"],
                        bore["station_mm"],
                    ],
                    "existing_compatible_T_n": bolt["compatible_T_n"],
                    "existing_combined_smooth_shank_peak": bolt["peak_stress_witness"],
                    "outer_end_chain": ends,
                }
            )
    require(len(bolts) == 2, "side-bolt crossing count differs")
    return {
        "witness": witness,
        "crossing_bolts": bolts,
        "fixed_action_compression_only_obstacle": True,
        "existing_inward_washer_actions_already_in_timber_cut": True,
        "additional_bolt_force_assigned_n": 0.0,
        "reinforcement_capacity_n": None,
        "reason": "The positive bound is for the timber-only cut after existing washer actions were counted. Existing shaft tension cannot be credited again to remove that bound. A justified redistribution or reinforcement load path remains necessary.",
    }


def build_finite_pressure(output):
    output = Path(output).resolve()
    require(
        output.is_relative_to(RAW) and output != RAW and not output.exists(),
        "fresh owned output child required",
    )
    census_path = RAW / "normal-census-attempt01/checks.json"
    pins = {
        census_path: "49f7c143d5a7cda5ff0f3ac8e9ef8d1d8fdf8d8090db4a31f6090c346cf7e75f"
    }
    authenticate(pins)
    census = read(census_path)
    pins.update({ROOT / p: digest for p, digest in census["source_sha256"].items()})
    authenticate(pins)
    source = read(SOURCE / "checks.json")
    material = read(
        ROOT
        / "docs/wood-joints-mvp/hypotheses/hardware-material-specification-2026-09-30/material-inputs.json"
    )
    fc = (
        material["conditional_DF_L_No2_base_row"]["base_properties"]["Fc_perpendicular"]
        * 0.006894757293168
    )
    output.mkdir(parents=True, exist_ok=False)
    (output / ".gitignore").write_text("*\n")
    live_source = Path(__file__).resolve()
    snapshot = output / "producer.py.snapshot"
    snapshot.write_bytes(live_source.read_bytes())
    digest = sha(live_source)
    pins[snapshot] = digest
    known = band_coupon()
    states, peak, former_affine = {}, None, None
    affine = census["original_affine_opening_peak_hull_result"]
    with gzip.open(SOURCE / "cuts.jsonl.gz", "rt") as stream:
        for line in stream:
            cut = json.loads(line)
            axis = cut["normal_axis_grain_u_v"]
            if axis == 0:
                continue
            key = (cut["block"], cut["case_id"], axis)
            result = finite_band_pressure(
                cut["signed_internal_n_nmm"], source["geometries"][key[0]], axis
            )
            witness = {
                "block": key[0],
                "case_id": key[1],
                "axis": axis,
                "station_mm": cut["station_mm"],
                "limit": cut["limit"],
                **result,
            }
            row = states.setdefault(
                key,
                {
                    "block": key[0],
                    "case_id": key[1],
                    "axis": axis,
                    "count_by_status": {},
                    "finite_pressure_above_reference_count": 0,
                    "maximum_pressure_witness": None,
                },
            )
            counts = row["count_by_status"]
            counts[result["status"]] = counts.get(result["status"], 0) + 1
            if "pressure_peak_mpa" in result:
                witness["pressure_over_conditional_Fc_perp_reference"] = (
                    result["pressure_peak_mpa"] / fc
                )
                row["finite_pressure_above_reference_count"] += (
                    result["pressure_peak_mpa"] > fc
                )
                if (
                    row["maximum_pressure_witness"] is None
                    or result["pressure_peak_mpa"]
                    > row["maximum_pressure_witness"]["pressure_peak_mpa"]
                ):
                    row["maximum_pressure_witness"] = witness
                if (
                    peak is None
                    or result["pressure_peak_mpa"] > peak["pressure_peak_mpa"]
                ):
                    peak = witness
            if all(
                witness[k] == affine[k]
                for k in ["block", "case_id", "axis", "station_mm", "limit"]
            ):
                former_affine = witness
    positive = [
        s["maximum_normal_tensile_bound_witness"]
        for s in census["states"]
        if s["positive_normal_tensile_bound_count"]
    ]
    bridges = [existing_bridge_trace(source, witness) for witness in positive]
    require(
        len(states) == 48
        and sum(sum(s["count_by_status"].values()) for s in states.values()) == 51312
        and former_affine is not None,
        "incomplete finite pressure census",
    )
    authenticate(pins)
    require(sha(live_source) == digest, "executed producer changed during calculation")
    result = {
        "schema": "corner_finite_pressure_and_bridge_trace/v1",
        "status": "FINITE_PRESSURE_AND_EXISTING_BRIDGE_TRACE_COMPLETE",
        "coupon": known,
        "states": [states[k] for k in sorted(states)],
        "conditional_Fc_perpendicular_reference_mpa": fc,
        "maximum_finite_band_pressure_witness": peak,
        "original_affine_peak_finite_pressure_witness": former_affine,
        "positive_normal_lower_bound_existing_bridge_traces": bridges,
        "source_sha256": {path_key(p): d for p, d in sorted(pins.items())},
        "executed_producer_sha256": digest,
        "limits": [
            "End-band pressures are sufficient normal-equilibrium constructions, not optimal pressure fields, compatible elastic solutions or complete stress fields.",
            "An above-reference construction or missing finite-band witness is not proof that every pressure field fails.",
            "Full original shear/shear/torque are retained; earlier shear comparisons do not qualify an opened crack interface.",
            "No existing bolt action is counted twice; no new bolt tension, preload, friction, anchorage capacity or Ft-perpendicular is credited.",
        ],
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
        "maximum_finite_band_pressure_witness": peak,
        "positive_row_count": len(bridges),
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--finite-pressure", action="store_true")
    args = parser.parse_args()
    print(
        json.dumps(
            (build_finite_pressure if args.finite_pressure else build)(args.output),
            allow_nan=False,
        )
    )
