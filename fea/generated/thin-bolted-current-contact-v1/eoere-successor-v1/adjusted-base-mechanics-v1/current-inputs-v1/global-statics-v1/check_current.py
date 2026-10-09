"""Recompute current source-load statics with the preserved support-hull method.

Run from the repository root. The result is a necessary global compression
equilibrium check, not a frame response, compatible reactions or floor capacity.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import math
import platform
import types
from pathlib import Path

BASE = Path("fea/generated/thin-bolted-current-contact-v1/eoere-successor-v1")
CURRENT = BASE / "adjusted-base-mechanics-v1/current-inputs-v1/attempt01/inputs.json"
CURRENT_SHA = "f0c55ac1d67650eec2de0cedfe4ec383d5b2a04253fbf10c9db9df9251711baa"
METHOD = BASE / "floor-practical-resolution-v1/global_statics.py"
METHOD_SHA = "e8042b4a7f82e4d76e2a66abde4452a2d61959359bff4fe2edb261af7e1152d4"
OLD_INPUT = BASE / "raised-rail-mechanics-v1/inputs.json"
OLD_INPUT_SHA = "81e9ad126f806a412a8bcb73ae3d0057ef3568ed0fa45986503f97fb5fb62d9f"
CASE_IDS = (
    "a12-rear",
    "a12-forward",
    "a12-left",
    "k12-right",
    "k12-rear",
    "a1-rear",
    "gravity-only",
)
HOSTS = (
    "base_floor_left",
    "base_floor_right",
    "base_post_center_left",
    "base_post_center_right",
    "base_post_outer_left",
    "base_post_outer_right",
    "lumber_leg_left",
    "lumber_leg_right",
)


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def encoded(value):
    return (
        json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n"
    ).encode()


def strict_json(raw):
    def invalid(value):
        raise ValueError(f"nonfinite JSON constant: {value}")

    return json.loads(raw, parse_constant=invalid)


def close(actual, expected, tolerance, label):
    if (
        not math.isfinite(actual)
        or not math.isfinite(expected)
        or abs(actual - expected) > tolerance
    ):
        raise ValueError(f"{label}: {actual!r} != {expected!r}")


def vector(value, label):
    if not isinstance(value, list) or len(value) != 3:
        raise ValueError(f"{label}: three coordinates required")
    if any(
        isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v)
        for v in value
    ):
        raise ValueError(f"{label}: finite numeric coordinates required")
    return value


def validate(data, old, cache):
    if data["schema"] != "eoere_extended_cleat_first_order_mechanics_inputs/v1":
        raise ValueError("wrong current input schema")
    if (
        data["optional_2026_extra"] is not False
        or data["historical_q"] is not None
        or data["old_field"] is not None
    ):
        raise ValueError("current extra-off source-only inputs required")
    if any(v is not False for v in data["release"].values()):
        raise ValueError("source inputs must not claim acceptance or release")
    footprints = data["floor_footprints"]
    if (
        tuple(sorted(footprints)) != HOSTS
        or tuple(sorted(old["floor_footprints"])) != HOSTS
    ):
        raise ValueError("the eight named support footprints are required")
    observations = cache["floor_observations"]
    observed = {
        r["host"]: r["observed_normal_reference_points_xyz_mm"] for r in observations
    }
    if len(observations) != 8 or observed != footprints:
        raise ValueError(
            "current support points must match the saved current solid observations"
        )
    if any(
        r["own_floor_face_confirmed_from_current_cached_solid"] is not True
        for r in observations
    ):
        raise ValueError("saved current solid floor-face confirmations required")
    points = []
    changed_points = []
    for host in HOSTS:
        corners = footprints[host]
        if len(corners) != 4 or len({tuple(p) for p in corners}) != 4:
            raise ValueError("four distinct corners required for each footprint")
        for index, point in enumerate(corners):
            vector(point, f"{host} corner {index}")
            if point[2] != 0:
                raise ValueError("common Z=0 support plane required")
            old_point = vector(
                old["floor_footprints"][host][index], "legacy support point"
            )
            delta = [a - b for a, b in zip(point, old_point, strict=True)]
            expected = [-39.2, 0, 0] if host == "base_post_center_right" else [0, 0, 0]
            for actual, target in zip(delta, expected, strict=True):
                close(actual, target, 1e-12, "reviewed support point change")
            if point != old_point:
                changed_points.append(
                    {
                        "host": host,
                        "corner_index": index,
                        "old_point_xyz_mm": old_point,
                        "current_point_xyz_mm": point,
                        "delta_xyz_mm": delta,
                    }
                )
            points.append(
                {
                    "index": len(points),
                    "host": host,
                    "corner_index": index,
                    "point_xyz_mm": [float(v) for v in point],
                }
            )
    cases = data["cases"]
    if tuple(c["case_id"] for c in cases) != CASE_IDS:
        raise ValueError("the exact six source cases plus gravity-only are required")
    gravity = cases[-1]
    if gravity["hold"] is not None or len(gravity["loads"]) != 826:
        raise ValueError("gravity-only must have 826 source loads and no climber")
    for case in cases:
        loads = case["loads"]
        ids = [r["id"] for r in loads]
        if any(not isinstance(i, str) or not i for i in ids) or len(set(ids)) != len(
            ids
        ):
            raise ValueError("nonempty unique physical load identifiers required")
        vector(case["applied_force_xyz_n"], "source total force")
        vector(
            case["applied_moment_about_global_origin_xyz_nmm"], "source total moment"
        )
        for row in loads:
            vector(row["point_xyz_mm"], row["id"] + " point")
            vector(row["force_xyz_n"], row["id"] + " force")
        if case is not gravity:
            if len(loads) != 827 or loads[:-1] != gravity["loads"]:
                raise ValueError(
                    "each loaded case must retain the exact gravity rows plus one climber"
                )
            hold, climber = case["hold"], loads[-1]
            if (
                climber["id"] != "climber/" + hold["label"]
                or climber["body"] != hold["panel"]
                or climber["force_xyz_n"] != hold["force_xyz_n"]
                or climber["point_xyz_mm"] != hold["load_point_xyz_mm"]
            ):
                raise ValueError("climber load must match the source hold descriptor")
    if any(
        r["force_xyz_n"][:2] != [0, 0] or r["force_xyz_n"][2] >= 0
        for r in gravity["loads"]
    ):
        raise ValueError("gravity rows must be strictly downward vertical forces")
    g = data["parameters"]["gravity_m_s2"]
    close(g, 9.80665, 0, "recorded gravitational acceleration")
    category_mass = {}
    for category in ("self-weight", "physical-bolt-metal", "bolt-weight", "accessory"):
        category_mass[category] = (
            -math.fsum(
                r["force_xyz_n"][2]
                for r in gravity["loads"]
                if r["id"].startswith(category + "/")
            )
            / g
        )
    total_mass = -math.fsum(r["force_xyz_n"][2] for r in gravity["loads"]) / g
    close(
        math.fsum(category_mass.values()), total_mass, 1e-10, "gravity category closure"
    )
    close(
        category_mass["accessory"],
        data["gravity"]["additional_accessory_kg"],
        1e-10,
        "accessory mass",
    )
    close(
        total_mass,
        data["gravity"]["known_modeled_mass_kg"]
        + data["gravity"]["additional_accessory_kg"],
        1e-10,
        "modeled plus accessory mass",
    )
    close(total_mass, 219.11593970030577, 1e-10, "current source total mass")
    return (
        points,
        changed_points,
        {
            "total_kg": total_mass,
            "load_category_mass_kg": category_mass,
            "known_modeled_kg": data["gravity"]["known_modeled_mass_kg"],
            "accessory_kg": data["gravity"]["additional_accessory_kg"],
            "gravity_m_s2": g,
            "actual_weight_observed": False,
            "scope": data["gravity"]["unitemized_accessory_scope"],
        },
    )


def run(inputs, output):
    if not __debug__:
        raise ValueError(
            "Python assertions must be enabled for the preserved method fixtures"
        )
    if output.exists():
        raise FileExistsError(f"output already exists: {output}")
    snapshots = {}

    def capture(path, expected=None):
        path = Path(path)
        raw = path.read_bytes()
        if expected is not None and digest(raw) != expected:
            raise ValueError(f"source digest mismatch: {path}")
        snapshots[path] = digest(raw)
        return raw

    def unchanged():
        for path, expected in snapshots.items():
            if digest(path.read_bytes()) != expected:
                raise ValueError(f"source changed during calculation: {path}")

    current_raw = capture(inputs, CURRENT_SHA)
    method_raw = capture(METHOD, METHOD_SHA)
    old_raw = capture(OLD_INPUT, OLD_INPUT_SHA)
    own = Path(__file__).resolve().relative_to(Path.cwd().resolve())
    capture(own)
    capture(Path("uv.lock"))
    data, old = strict_json(current_raw), strict_json(old_raw)
    geometry_bytes = {
        key: capture(source["path"], source["sha256"])
        for key, source in data["geometry"].items()
    }
    report = strict_json(geometry_bytes["report"])
    cache = strict_json(geometry_bytes["cached_source_export"])
    if report["revision"] != "eoere-base-side-edge-cleats-v1":
        raise ValueError("current extended-cleat geometry required")
    points, changed_points, mass = validate(data, old, cache)
    # Execute the exact captured legacy source, not a second filesystem read.
    method = types.ModuleType("preserved_global_statics")
    method.__file__ = str(METHOD)
    exec(compile(method_raw, str(METHOD), "exec"), method.__dict__)  # noqa: S102 -- METHOD_SHA authenticates these bytes.
    fixtures = method.fixtures()
    if fixtures != {"passed": True, "known_answer_fixture_count": 7}:
        raise ValueError("preserved known-answer fixtures did not pass")
    results = []
    for case in data["cases"]:
        result = method.assess([p["point_xyz_mm"] for p in points], case["loads"])
        for actual, expected in zip(
            result["applied_force_xyz_n"], case["applied_force_xyz_n"], strict=True
        ):
            close(actual, expected, 1e-8, "source force sum")
        for actual, expected in zip(
            result["applied_moment_xyz_nmm"],
            case["applied_moment_about_global_origin_xyz_nmm"],
            strict=True,
        ):
            close(actual, expected, 1e-6, "source moment sum")
        results.append(
            {
                "case_id": case["case_id"],
                "source_load_count": len(case["loads"]),
                **result,
            }
        )
    old_xy = method.np.asarray(
        [p[:2] for host in HOSTS for p in old["floor_footprints"][host]]
    )
    old_polygon = sorted(old_xy[method.ConvexHull(old_xy).vertices].tolist())
    if any(sorted(r["support_polygon_xy_mm"]) != old_polygon for r in results):
        raise ValueError("current and legacy outer support hulls differ")
    record = {
        "schema": "eoere_current_source_global_statics/v1",
        "status": "GLOBAL_COMPRESSION_EQUILIBRIUM_ONLY",
        "revision": report["revision"],
        "optional_2026_extra": False,
        "input_status_preserved": data["status"],
        "input_readiness_preserved": data["readiness"],
        "source_bindings": {str(p): h for p, h in snapshots.items()},
        "input_recursive_pin_count_declared_not_independently_rehashed_here": len(
            data["source_sha256"]
        ),
        "method": {
            "path": str(METHOD),
            "sha256": METHOD_SHA,
            "reuse": "Unmodified assess() and seven known-answer fixtures; old input used only to compare support points and the outer hull.",
        },
        "runtime": {
            "python": platform.python_version(),
            "numpy": importlib.metadata.version("numpy"),
            "scipy": importlib.metadata.version("scipy"),
        },
        "fixtures": fixtures,
        "mass": mass,
        "support_point_order": points,
        "support_points_identical_to_current_cached_solid_observations": True,
        "legacy_footprint_comparison": {
            "identical_point_count": 32 - len(changed_points),
            "changed_point_count": len(changed_points),
            "changed_points": changed_points,
            "outer_support_hull_identical": True,
        },
        "source_loads_recomputed_not_taken_from_a_response": True,
        "cases": results,
        "summary": {
            "case_count": len(results),
            "compression_feasible_case_count": sum(
                r["compression_equilibrium_possible"] for r in results
            ),
            "minimum_edge_margin_case": min(
                results, key=lambda r: r["minimum_support_polygon_edge_margin_mm"]
            )["case_id"],
            "minimum_edge_margin_mm": min(
                r["minimum_support_polygon_edge_margin_mm"] for r in results
            ),
        },
        "no_frame_or_native_solve_or_CAD": True,
        "release": data["release"],
        "limitations": [
            "This necessary global check does not establish compatible elastic reactions, joint demands or resistance.",
            "Nonnegative normal reactions are equilibrium witnesses, not measured or computed floor pressures.",
            "The aggregate friction ratio omits yaw and local distribution; no friction capacity is assigned.",
            "The floor/no-slip assumption remains unverified; no floor test or anchor is introduced.",
            "Source-input and frame-method admission remain separate; frozen pending-review flags are retained.",
            "No physical parts, tools, floor or weight were observed; no build or climbing release follows.",
        ],
        "reproduce": f".venv/bin/python -B {own} --out NEW_RESULT.json",
    }
    raw = encoded(record)
    unchanged()
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("xb") as handle:
        try:
            handle.write(raw)
            handle.flush()
            unchanged()
        except BaseException:
            output.unlink()
            raise
    return record


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--inputs", type=Path, default=CURRENT)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    result = run(args.inputs, args.out)
    print(json.dumps(result["summary"], sort_keys=True))
