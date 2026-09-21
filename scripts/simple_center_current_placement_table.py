"""Source-bound nominal placement inventory for the current PB-02 center trial.

Markers are conditional comparisons, not selected NDS requirements or a drill plan.
"""

import argparse
import json
from collections import defaultdict

import cadquery as cq

from scripts import simple_center_combined_cleats_probe as combined
from scripts import simple_center_post_header_two_bolt_probe as current
from scripts import simple_center_second_bolt_tolerance_probe as prior
from scripts import simple_center_wide_post_probe as wide

DIAMETER_MM = 6.35
FABRICATION_ALLOWANCE_MM = 5.0  # One project target, not an NDS addition.
GRAIN_AXIS = {
    "shifted_right_post": "z",
    "header_post_side_cleat": "z",
    "base_header": "x",
    "header_side_cleat": "y",
    "rear_cleat": "z",
    "upright_side_cleat": "z",
}
AXES = {
    "header_cleat": "z",
    "cleat_principal": "x",
    "post_low": "y",
    "post_high": "y",
    "upright": "x",
    "cleat_link": "y",
    "post_cleat_1": "x",
    "post_cleat_2": "x",
    "cleat_header_1": "z",
    "cleat_header_2": "z",
}


def _center(bore, axis):
    bounds = wide.bounds(bore)
    return {
        letter: round((bounds[2 * i] + bounds[2 * i + 1]) / 2, 5)
        for i, letter in enumerate("xyz")
    }


def _centerline_gap(first, first_axis, second, second_axis):
    """Shortest distance between two finite, axis-aligned bore centerlines."""
    first_bounds, second_bounds = wide.bounds(first), wide.bounds(second)
    first_center, second_center = (
        _center(first, first_axis),
        _center(second, second_axis),
    )
    square = 0.0
    for i, axis in enumerate("xyz"):
        first_low, first_high = (
            first_bounds[2 * i : 2 * i + 2]
            if axis == first_axis
            else (first_center[axis],) * 2
        )
        second_low, second_high = (
            second_bounds[2 * i : 2 * i + 2]
            if axis == second_axis
            else (second_center[axis],) * 2
        )
        gap = max(first_low - second_high, second_low - first_high, 0)
        square += gap * gap
    return square**0.5


def _geometry():
    """Apply the selected short two-bolt post/header variant to the tolerance pose."""
    parts, bores, _ = prior._geometry()
    bottom, post_y, post_z, vertical_x = current.VARIANTS["shorter_8in_trial"]
    old = wide.bounds(parts["header_post_side_cleat"])
    old_post_bore = wide.bounds(bores["post_cleat"])
    old_vertical_bore = wide.bounds(bores["cleat_header"])
    parts["header_post_side_cleat"] = cq.Solid.makeBox(
        old[1] - old[0],
        old[3] - old[2],
        old[5] - bottom,
        cq.Vector(old[0], old[2], bottom),
    )
    bores.pop("post_cleat")
    bores.pop("cleat_header")
    for index, z in enumerate(post_z, 1):
        bores[f"post_cleat_{index}"] = combined.cylinder(
            wide.BORE_RADIUS,
            old_post_bore[1] - old_post_bore[0],
            (old_post_bore[0], post_y, z),
            (1, 0, 0),
        )
    for index, x in enumerate(vertical_x, 1):
        bores[f"cleat_header_{index}"] = combined.cylinder(
            wide.BORE_RADIUS,
            old_vertical_bore[5] - bottom,
            (x, (old_vertical_bore[2] + old_vertical_bore[3]) / 2, bottom),
            (0, 0, 1),
        )
    owners = combined.INTENDED | {
        "post_low": ("rear_cleat", "shifted_right_post"),
        "post_high": ("rear_cleat", "shifted_right_post"),
        "upright": ("base_principal_center_right", "upright_side_cleat"),
        "cleat_link": ("rear_cleat", "upright_side_cleat"),
    }
    for prefix in ("post_cleat", "cleat_header"):
        for index in (1, 2):
            owners[f"{prefix}_{index}"] = owners[prefix]
        owners.pop(prefix)
    if set(bores) != set(AXES) or set(bores) != set(owners):
        raise ValueError(
            "Center bore inventory changed; update placement classifications"
        )
    return parts, bores, owners


def _row(bolt, member, kind, feature, distance, marker, source):
    return {
        "bolt": bolt,
        "member": member,
        "kind": kind,
        "feature": feature,
        "nominal_distance_mm": round(distance, 5),
        "marker_mm": marker,
        "marker_source": source,
        "marker_status": "conditional" if marker is not None else "unknown",
        "fabrication_allowance_mm": FABRICATION_ALLOWANCE_MM
        if marker is not None
        else None,
        "reserve_mm": round(distance - marker - FABRICATION_ALLOWANCE_MM, 5)
        if marker is not None
        else None,
        "classification_complete": False,
    }


def table():
    parts, bores, owners = _geometry()
    centers = {name: _center(bore, AXES[name]) for name, bore in bores.items()}
    rows = []
    member_bolts = defaultdict(list)
    for bolt, members in owners.items():
        for member in members:
            member_bolts[member].append(bolt)
            bounds = wide.bounds(parts[member])
            grain = GRAIN_AXIS.get(member)
            for i, axis in enumerate("xyz"):
                if axis == AXES[bolt]:
                    continue
                low, high = bounds[2 * i : 2 * i + 2]
                kind = "grain_end" if axis == grain else "transverse_edge"
                if grain is None:
                    kind = "unclassified_oblique_member"
                marker = (
                    round((7 if kind == "grain_end" else 4) * DIAMETER_MM, 5)
                    if grain
                    else None
                )
                source = (
                    (
                        "project conditional 7D tension-end comparator"
                        if kind == "grain_end"
                        else "project conditional 4D reversible-edge comparator"
                    )
                    if grain
                    else ("inclined principal: no axis-aligned marker adopted")
                )
                for side, distance in (
                    ("low", centers[bolt][axis] - low),
                    ("high", high - centers[bolt][axis]),
                ):
                    rows.append(
                        _row(
                            bolt,
                            member,
                            kind,
                            f"{axis}_{side}",
                            distance,
                            marker,
                            source,
                        )
                    )
    for member, bolts in member_bolts.items():
        for i, bolt in enumerate(bolts):
            for other in bolts[i + 1 :]:
                if AXES[bolt] == AXES[other]:
                    distance = (
                        sum(
                            (centers[bolt][axis] - centers[other][axis]) ** 2
                            for axis in "xyz"
                            if axis != AXES[bolt]
                        )
                        ** 0.5
                    )
                    marker = round(4 * DIAMETER_MM, 5)
                    source = "project conditional 4D neighboring-bolt comparator"
                    kind = "parallel_neighbor"
                else:
                    # Orthogonal axes need a member-specific arrangement check.
                    distance = _centerline_gap(
                        bores[bolt], AXES[bolt], bores[other], AXES[other]
                    )
                    marker = None
                    source = "orthogonal axes: finite centerline gap only; classification unknown"
                    kind = "orthogonal_neighbor"
                rows.append(_row(bolt, member, kind, other, distance, marker, source))
    conditional = [r for r in rows if r["marker_mm"] is not None]
    return {
        "source_pose": "simple_center_second_bolt_tolerance_probe.POSE",
        "post_header_variant": "simple_center_post_header_two_bolt_probe.VARIANTS.shorter_8in_trial",
        "bolt_count": len(bores),
        "member_count": len(member_bolts),
        "conditional_subset_minimum_reserve_mm": min(
            r["reserve_mm"] for r in conditional
        ),
        "whole_center_classification_complete": False,
        "rows": rows,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--format", choices=("json", "markdown"), default="markdown")
    args = parser.parse_args()
    result = table()
    if args.format == "json":
        print(json.dumps(result, indent=2))
    else:
        print(
            "| Bolt | Member | Kind / feature | Nominal mm | Marker mm | Allowance mm | Reserve mm |"
        )
        print("| --- | --- | --- | ---: | ---: | ---: | ---: |")
        for row in result["rows"]:
            values = (
                row["bolt"],
                row["member"],
                f"{row['kind']} {row['feature']}",
                row["nominal_distance_mm"],
                row["marker_mm"],
                row["fabrication_allowance_mm"],
                row["reserve_mm"],
            )
            print(
                "| "
                + " | ".join(
                    "unknown" if value is None else str(value) for value in values
                )
                + " |"
            )
