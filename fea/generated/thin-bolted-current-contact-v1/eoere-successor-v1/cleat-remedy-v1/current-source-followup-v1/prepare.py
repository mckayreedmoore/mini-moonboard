"""Bind the preserved four-axis Z180 proposal to current 100/66 source records.

Only placement inputs and nominal containing-envelope arithmetic are produced.
The current model and its four drilling holds remain unchanged.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import math
import sys
import types
from pathlib import Path

OWN = Path(__file__).resolve().relative_to(Path.cwd().resolve())
INPUTS = OWN.with_name("inputs.json")
INPUT_SHA = "989a518a33f05c72c38613e9b8c53fc85458fc1aabc94948803ff5f9fe2bbb7f"


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def encode(value):
    return (
        json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n"
    ).encode()


def canonical(value):
    raw = json.dumps(
        value, sort_keys=True, separators=(",", ":"), allow_nan=False
    ).encode()
    return sha(raw)


def require(condition, message):
    if not condition:
        raise ValueError(message)


def summary(comparisons):
    count, positive, minimum, roles = 0, 0, None, {}
    for row in comparisons:
        gap = row["capsule_separation_lower_bound_mm"]
        require(math.isfinite(gap), "finite capsule bound required")
        count += 1
        positive += gap > 0
        if minimum is None or gap < minimum["capsule_separation_lower_bound_mm"]:
            minimum = row
        role = row["first_role"]
        if role not in roles or gap < roles[role]["capsule_separation_lower_bound_mm"]:
            roles[role] = row
    require(count > 0, "empty comparison set")
    return {
        "count": count,
        "positive_bound_count": positive,
        "all_bounds_positive": positive == count,
        "minimum": minimum,
        "minimum_by_lower_role": roles,
    }


def build(inputs, output):
    output.mkdir(parents=True, exist_ok=False)
    snapshots = {}

    def capture(path, expected=None):
        path = Path(path)
        raw = path.read_bytes()
        require(
            expected is None or sha(raw) == expected, "changed source: " + str(path)
        )
        snapshots[path] = sha(raw)
        return raw

    def unchanged():
        for path, expected in snapshots.items():
            require(sha(path.read_bytes()) == expected, "source drift: " + str(path))

    config = json.loads(capture(inputs, INPUT_SHA))
    capture(OWN)
    raw_sources = {
        path: capture(path, expected) for path, expected in config["sources"].items()
    }
    current = json.loads(raw_sources[config["current_geometry"]])
    cache = json.loads(raw_sources[config["current_cached_descriptors"]])
    prior = json.loads(raw_sources[config["prior_review"]])
    require(
        config["current_revision"]
        == current["revision"]
        == "eoere-base-side-edge-cleats-v1"
        and config["optional_2026_extra"] is False,
        "current extended-cleat extra-off inputs required",
    )
    axes = {a["id"]: a for a in current["axes"]}
    screws = {s["axis_id"]: s for s in current["screw_axes"]}
    cached_axes = {s["axis_id"]: s["source_axis"] for s in cache["shafts"]}
    cached_screws = {
        s["id"]: s["source_screw_descriptor"] for s in cache["hillman_rows"]
    }
    require(
        len(current["axes"]) == len(axes) == len(cache["shafts"]) == 100
        and axes == cached_axes,
        "current geometry/descriptor 100-axis identity mismatch",
    )
    require(
        len(current["screw_axes"]) == len(screws) == len(cache["hillman_rows"]) == 66
        and screws == cached_screws,
        "current geometry/descriptor 66-screw identity mismatch",
    )
    ids = set(config["target_axis_ids"])
    expected_ids = {
        f"cleat_post_bolt_{side}_{n}" for side in ("left", "right") for n in (1, 2)
    }
    require(
        ids == expected_ids and len(config["target_axis_ids"]) == 4,
        "exact four target axes required",
    )
    require(
        config["current_Z_mm"] == 200.0 and config["proposed_Z_mm"] == 180.0,
        "preserved Z180 proposal required",
    )
    proposed = copy.deepcopy(current["axes"])
    for axis in proposed:
        if axis["id"] in ids:
            require(
                axis["point_xyz_mm"][2] == config["current_Z_mm"],
                "wrong current target Z",
            )
            axis["point_xyz_mm"][2] = config["proposed_Z_mm"]
    target = [a for a in proposed if a["id"] in ids]
    prior_axes = {a["id"]: a for a in prior["proposed_geometry_inputs"]["axis_rows"]}
    require(
        {a["id"]: a for a in target} == prior_axes,
        "four targets differ from the independently reviewed placement",
    )
    fixed = [a for a in current["axes"] if a["id"] not in ids]
    require(
        fixed == [a for a in proposed if a["id"] not in ids] and len(fixed) == 96,
        "96 current fixed axes must remain exactly unchanged",
    )
    changes = []
    for original, candidate in zip(current["axes"], proposed, strict=True):
        if original != candidate:
            require(
                original["id"] in ids
                and {**original, "point_xyz_mm": candidate["point_xyz_mm"]} == candidate
                and original["point_xyz_mm"][:2] == candidate["point_xyz_mm"][:2],
                "only four Z coordinates may differ",
            )
            changes.append(
                {
                    "axis_id": original["id"],
                    "current_point_xyz_mm": original["point_xyz_mm"],
                    "proposed_point_xyz_mm": candidate["point_xyz_mm"],
                    "translation_xyz_mm": [0.0, 0.0, -20.0],
                }
            )
    require(len(changes) == 4, "exactly four changes required")
    method_path = config["capsule_method"]
    method = types.ModuleType("preserved_capsule_method")
    method.__file__ = method_path
    exec(compile(raw_sources[method_path], method_path, "exec"), method.__dict__)  # noqa: S102 -- captured pinned source only.
    require(method.known_answers() == 4, "preserved capsule fixtures failed")
    recipe = config["screw_envelope_recipe"]
    screw_primitives = [
        method.primitive(
            s["axis_id"], role, s["origin_xyz_mm"], s["direction_xyz"], *span, radius
        )
        for s in current["screw_axes"]
        for role, span, radius in (
            ("screw_body", recipe["body_axis_interval_mm"], recipe["body_radius_mm"]),
            (
                "screw_head_containing_cylinder",
                recipe["head_axis_interval_mm"],
                recipe["head_containing_radius_mm"],
            ),
        )
    ]
    fixed_primitives = [p for a in fixed for p in method.hardware(a, bore=True)]
    screens = []
    for label, rows in (
        ("current_Z200", [axes[k] for k in sorted(ids)]),
        ("proposed_Z180", target),
    ):
        nominal = [p for a in rows for p in method.hardware(a, bore=True)]
        maximum = [
            p
            for a in rows
            for p in method.hardware(
                {**a, "bore_diameter_mm": config["maximum_bore_sensitivity_mm"]},
                bore=True,
            )
        ]
        screens.append(
            {
                "id": label,
                "nominal_bore_vs_66_current_screws": summary(
                    method.pair(a, b) for a in nominal for b in screw_primitives
                ),
                "maximum_bore_vs_66_current_screws": summary(
                    method.pair(a, b) for a in maximum for b in screw_primitives
                ),
                "maximum_bore_vs_96_current_fixed_bolts": summary(
                    method.pair(a, b) for a in maximum for b in fixed_primitives
                ),
                "maximum_bore_vs_other_lower_bolts": summary(
                    method.pair(a, b)
                    for a in maximum
                    for b in maximum
                    if a["id"] < b["id"]
                ),
            }
        )
    for screen, expected_gap in zip(screens, (-0.05625, 3.94375), strict=True):
        actual = screen["maximum_bore_vs_66_current_screws"]["minimum"][
            "capsule_separation_lower_bound_mm"
        ]
        require(
            abs(actual - expected_gap) < 1e-9,
            "independent existing finite-endpoint reference disagrees",
        )
    require(
        screens[1]["maximum_bore_vs_66_current_screws"]["all_bounds_positive"],
        "proposed screw bound is not positive",
    )
    require(
        screens[1]["maximum_bore_vs_96_current_fixed_bolts"]["all_bounds_positive"],
        "proposed fixed-hardware bound is not positive",
    )
    require(
        screens[1]["maximum_bore_vs_other_lower_bolts"]["all_bounds_positive"],
        "proposed lower-hardware bound is not positive",
    )
    placement = {
        "schema": "eoere_current_Z180_placement_proposal/v1",
        "status": "UNADOPTED_CURRENT_SOURCE_PROPOSAL",
        "base_revision": current["revision"],
        "optional_2026_extra": False,
        "proposed_axes": target,
        "changes": changes,
        "retain_96_other_axes_from_current_geometry": True,
        "current_fixed_96_canonical_sha256": canonical(fixed),
        "current_66_screws_canonical_sha256": canonical(current["screw_axes"]),
        "current_100_axes_canonical_sha256": canonical(current["axes"]),
        "proposed_100_axes_canonical_sha256": canonical(proposed),
        "canonical_format": "JSON sorted object keys, compact separators, source list order",
        "current_geometry_source": {
            "path": config["current_geometry"],
            "sha256": config["sources"][config["current_geometry"]],
        },
        "geometry_adopted": False,
    }
    placement_raw = encode(placement)
    result = {
        "schema": "eoere_current_Z180_placement_identity_and_capsules/v1",
        "status": "UNADOPTED_PROPOSAL_CURRENT_HOLD4_RETAINED",
        "source_sha256": {str(p): h for p, h in snapshots.items()},
        "sources_unchanged_before_after": True,
        "placement": {"file": "placement.json", "sha256": sha(placement_raw)},
        "current_revision": current["revision"],
        "identity": {
            "current_geometry_descriptor_axes": 100,
            "current_geometry_descriptor_screws": 66,
            "only_proposed_Z_moves": 4,
            "unchanged_current_axes": 96,
            "unchanged_current_screws": 66,
            "retained_starting_arrangements": 12,
            "comparison_basis": "CURRENT extended-cleat records, including the reviewed v3 changes; not the historical raised-rail list.",
        },
        "method": {
            "path": method_path,
            "sha256": config["sources"][method_path],
            "known_answer_count": 4,
            "reused_functions": ["hardware", "primitive", "pair", "known_answers"],
        },
        "screens": screens,
        "current_drilling_holds": sorted(ids),
        "new_bore_wall_seat_tool_or_response_qualification": False,
        "required_before_adoption": [
            "Parent reviews this current placement input before model changes.",
            "Reconstruct only the four changed receivers from CURRENT authenticated raw profiles and cuts; substitute eight Z180 bores for eight Z200 bores. Do not drill new holes into Z200 finished BREPs.",
            "Check new finished bore material, eight own seats, all current panel/service/angle intersections and affected screw backing using the existing geometry adapter.",
            "Check actual delivered hardware, uncertainty, eight tool sides and continuous removal paths.",
            "After adoption, extract fresh own descriptors/gravity and compatible actions; complete signed end/edge/group/net/splitting checks without transferring old fields.",
        ],
        "limits": [
            "Positive capsule bounds prove separation only of the declared nominal containing primitives; negative bounds are inconclusive.",
            "Maximum wood-bore diameter is a preserved sensitivity, not a bit instruction or adopted fabrication tolerance.",
            "No new coordinate search, solid query, CAD, frame/native solve, force recovery or physical work occurred.",
            "No washer pressure, delivered dimensions, tooling, complete resistance, geometry adoption or fabrication/climbing release is established.",
        ],
        "release": {
            "geometry_adopted": False,
            "mechanics_ready": False,
            "complete_joint_resistance": False,
            "fabrication": False,
            "structural": False,
            "climbing": False,
        },
        "reproduce": f".venv/bin/python -B {OWN} --out NEW_EMPTY_DIRECTORY",
    }
    require(
        not any(k in sys.modules for k in ("cadquery", "OCP")),
        "CAD unexpectedly imported",
    )
    result_raw = encode(result)
    unchanged()
    created = []
    try:
        for name, raw in (
            ("placement.json", placement_raw),
            ("result.json", result_raw),
        ):
            path = output / name
            with path.open("xb") as handle:
                created.append(path)
                handle.write(raw)
                handle.flush()
                unchanged()
    except BaseException:
        for path in created:
            path.unlink()
        raise
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--inputs", type=Path, default=INPUTS)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    record = build(args.inputs, args.out)
    print(
        json.dumps(
            {
                "proposed_moves": 4,
                "fixed_current_bolts": 96,
                "current_screws": 66,
                "placement_sha256": record["placement"]["sha256"],
                "source_pins": len(record["source_sha256"]),
            }
        )
    )
