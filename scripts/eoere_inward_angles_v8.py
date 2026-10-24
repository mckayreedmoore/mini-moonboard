"""Cumulatively shift the current v7 angle stacks and upper angles by 6 mm.

This is an unadopted geometry proposal. It reuses the frozen v6 inward-angle
builder through a guarded source adapter, applying it to the pinned v7 state.
It does not transfer prior force results or qualify complete joints.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path

from scripts.eoere_paired_frame_basis import ROOT, read, ref, sha
from scripts.eoere_v6_analysis import WORK

OWN = Path(__file__).resolve()
FROZEN_BUILDER = Path("scripts/eoere_inward_angles.py")
FROZEN_BUILDER_SHA256 = (
    "f07afbd16b962577d5df51071e13cb1106cac79d5e9f5fb3ce2bff2652c07fb3"
)
OUTER_PROFILE_HELPER = Path("scripts/eoere_bolt_outer_geometry.py")
OUTER_PROFILE_HELPER_SHA256 = (
    "8a952c7a75a20acd214c52157a9bd69ae9c24dda83f308dca615b946bbd765ec"
)
RECEIPT = Path("docs/bolted-frame-development/owner-frame-v7/geometry.json")
RECEIPT_SHA256 = (
    "ad1dd8f59afc0ec70eaa48d25cd4a59f771f40ca1ceea55c2eadf5868b3ca23e"
)
GEOMETRY_SHA256 = (
    "e53642f2ba30bf04f974b09810b0882e98f3882781458b59972387706325d3e9"
)
CLEARANCE_SHA256 = (
    "a529ac8bb6257a97fcb966ef7dbf1f97df534799d32bf2b15238d84d852821b4"
)
OUTPUT = WORK / "owner-inward-angles-v8/geometry"
REVISION = "eoere-inward-bolts-and-angles-v8"
SHIFT_MM = 6.0
LOADED_SHA256 = sha(OWN)
CONTAINMENT_TOLERANCE_MM = 1e-6


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def _adapt_frozen_builder() -> str:
    _require(
        sha(FROZEN_BUILDER) == FROZEN_BUILDER_SHA256,
        "frozen inward-angle builder differs from the reviewed v6 source",
    )
    source = (ROOT / FROZEN_BUILDER).read_text()
    replacements = (
        (
            '"Build an unadopted six-millimetre inward upper-angle geometry proposal.',
            '"Build the cumulative unadopted v7 inward-bolt and angle proposal.',
        ),
        (
            "from scripts.eoere_v6_analysis import BASE as ANALYSIS_BASE",
            "from scripts.eoere_v6_analysis import WORK as ANALYSIS_WORK",
        ),
        (
            'RECEIPT = Path("docs/bolted-frame-development/owner-frame-v6/geometry.json")',
            'RECEIPT = Path("docs/bolted-frame-development/owner-frame-v7/geometry.json")',
        ),
        (
            '"d2849e0bb7e3751396854556fa0bb411d83f3cf94dec55ec157a582f4f5b6e80"',
            f'"{RECEIPT_SHA256}"',
        ),
        (
            'OUTPUT = ANALYSIS_BASE / "inward-angle-study-v1/geometry"',
            'OUTPUT = ANALYSIS_WORK / "owner-inward-angles-v8/geometry"',
        ),
        (
            'REVISION = "eoere-v6-inward-upper-angle-translation-v1"',
            f'REVISION = "{REVISION}"',
        ),
        (
            '"fresh analysis/inward-angle-study-v1/geometry output required"',
            '"fresh owner-inward-angles-v8 geometry output required"',
        ),
        (
            'source["revision"] == "eoere-flat-cleats-principal-upper-pairs-v6"',
            'source["revision"] == "eoere-inward-exterior-bolts-v7"',
        ),
        (
            '"authenticated current v6 inventory required",',
            '"authenticated current v7 inventory required",',
        ),
        (
            '    g = copy.deepcopy(source)\n',
            (
                '    source_guard = V7_SOURCE_GUARD(receipt, source, pins, WOOD_RECEIVERS)\n'
                '    g = copy.deepcopy(source)\n'
            ),
        ),
        (
            '    g.update(\n        revision=REVISION,',
            (
                '    VERIFY_CUMULATIVE_V7(source, g, original, moved_axes, changed, source_guard)\n'
                '    g.update(\n        revision=REVISION,'
            ),
        ),
        (
            '            "current_full_wall_reboring_proofs": reboring_proofs,\n',
            (
                '            "current_full_wall_reboring_proofs": reboring_proofs,\n'
                '            "original_bore_outer_profile_containment": '
                'source_guard["original_bore_outer_profile_containment"],\n'
                '            "v7_orientation_preserved": '
                'source_guard["v7_orientation_preserved"],\n'
            ),
        ),
    )
    for before, after in replacements:
        _require(
            source.count(before) == 1,
            "frozen builder adapter anchor changed: " + before[:100],
        )
        source = source.replace(before, after)
    _require(
        sha(OUTER_PROFILE_HELPER) == OUTER_PROFILE_HELPER_SHA256,
        "outer-profile source differs from the reviewed v7 proof helper",
    )
    return source


def _flat_cleat_profile_proof(name: str, profile: dict) -> dict:
    import numpy as np
    from scipy.spatial import ConvexHull

    vertices = np.asarray(profile["vertices_luv_mm"], dtype=float)
    _require(
        vertices.ndim == 2
        and vertices.shape[1] == 3
        and np.isfinite(vertices).all(),
        "finite flat-cleat source vertices required: " + name,
    )
    thickness_coordinates = sorted(
        {round(float(v), 8) for v in vertices[:, 1]}
    )
    _require(
        len(thickness_coordinates) == 2,
        "flat cleat must have two physical thickness faces: " + name,
    )
    outlines = []
    for thickness in thickness_coordinates:
        outline = sorted(
            {
                (round(float(row[0]), 8), round(float(row[2]), 8))
                for row in vertices
                if abs(float(row[1]) - thickness) < 1e-8
            }
        )
        _require(
            len(outline) == 4,
            "each flat-cleat thickness face must have four physical perimeter vertices: "
            + name,
        )
        hull = ConvexHull(np.asarray(outline, dtype=float))
        _require(
            len(hull.vertices) == 4,
            "flat-cleat source perimeter must be a convex four-edge outline: " + name,
        )
        outlines.append(outline)
    _require(
        outlines[0] == outlines[1],
        "flat-cleat thickness faces must share one physical outline: " + name,
    )
    return {
        "member": name,
        "thickness_face_coordinates_mm": thickness_coordinates,
        "physical_LV_perimeter_vertices_mm": [list(point) for point in outlines[0]],
        "perimeter_vertex_count": 4,
        "source_blank_approximation_used": False,
    }


def _v7_source_guard(receipt: dict, source: dict, pins: dict, wood_receivers: set[str]) -> dict:
    import cadquery as cq
    import numpy as np

    from scripts import eoere_bolt_outer_geometry as outer

    geometry_ref = {
        "path": "fea/generated/thin-bolted-current-contact-v1/eoere-successor-v1/"
        "single-leg-header-integration-v1/coherent-return-paired-foot-v1/"
        "frame-completion-v1/owner-inward-bolts-v7/geometry/geometry.json",
        "sha256": GEOMETRY_SHA256,
    }
    clearance_ref = {
        "path": "fea/generated/thin-bolted-current-contact-v1/eoere-successor-v1/"
        "single-leg-header-integration-v1/coherent-return-paired-foot-v1/"
        "frame-completion-v1/owner-inward-bolts-v7/geometry/clearance.json",
        "sha256": CLEARANCE_SHA256,
    }
    _require(
        receipt.get("revision") == "eoere-inward-exterior-bolts-v7"
        and receipt.get("checked_geometry") == geometry_ref
        and receipt.get("checked_clearance") == clearance_ref
        and receipt.get("reversed_stacks") == 40
        and receipt.get("side_stacks") == 32
        and receipt.get("top_stacks") == 8
        and receipt.get("bolt_lengths_grades_and_spacer_counts_unchanged") is True
        and receipt.get("holes_members_panels_and_screws_unchanged") is True
        and receipt.get("nominal_geometry_clear") is True
        and receipt.get("current_response_computed") is False
        and receipt.get("complete_conditional_frame_evaluation") is False
        and receipt.get("fabrication_released") is False
        and receipt.get("climbing_released") is False
        and source.get("geometry_adopted") is False
        and source.get("new_response_computed") is False
        and source.get("complete_joint_qualified") is False,
        "pinned, unadopted v7 geometry receipt required",
    )
    orientation_ref = receipt.get("files", {}).get("orientation.json")
    _require(
        isinstance(orientation_ref, dict)
        and orientation_ref.get("path")
        and orientation_ref.get("sha256"),
        "v7 orientation source receipt required",
    )
    orientation = read(orientation_ref["path"], pins, orientation_ref["sha256"])
    _require(
        source.get("revision") == receipt["revision"]
        and len(source.get("axes", [])) == 96
        and len(source.get("fitting_poses", [])) == 24
        and len(source.get("screw_axes", [])) == 66
        and len(source.get("profiles", {})) == 30
        and len(source.get("selected_stack_overrides", [])) == 96,
        "complete current v7 axis, angle, profile and hardware inventory required",
    )
    orientation_updates = orientation.get("axis_updates", [])
    orientation_ids = {row["after"]["id"] for row in orientation_updates}
    _require(
        len(orientation_updates) == 40
        and len(orientation_ids) == 40
        and len(orientation.get("transforms", [])) == 40
        and len(orientation.get("hardware_summary", [])) == 40
        and orientation.get("bolt_lengths_grades_and_spacer_counts_unchanged") is True
        and orientation.get("holes_members_panels_and_screws_unchanged") is True
        and source.get("inward_bolt_revision", {}).get("axis_updates")
        == orientation_updates,
        "v7's forty authenticated inward-stack orientations required",
    )
    axis_rows = {row["id"]: row for row in source["axes"]}
    _require(len(axis_rows) == 96, "unique current v7 bolt axes required")
    for update in orientation_updates:
        after = update["after"]
        _require(
            axis_rows.get(after["id"]) == after,
            "v7 current axis must equal its authenticated inward orientation: "
            + after["id"],
        )

    selected = {row["axis_id"]: row for row in source["selected_stack_overrides"]}
    _require(len(selected) == 96, "all v7 selected stack records must be unique")
    hardware_summary = {row["axis_id"]: row for row in orientation["hardware_summary"]}
    _require(len(hardware_summary) == 40 and set(hardware_summary) == orientation_ids,
             "one frozen length and spacer record per reversed v7 stack required")
    for identity, row in hardware_summary.items():
        choice = selected[identity]
        _require(
            float(choice["selected_underhead_length_mm"])
            == float(row["selected_underhead_length_mm"])
            and int(choice["spacer_piece_count"]) == int(row["spacer_piece_count"])
            and float(choice["nut_side_spacer_mm"]) == float(row["nut_side_spacer_mm"])
            and choice["head_faces"] == row["head_faces"]
            and choice["nut_faces"] == row["nut_faces"],
            "v7 selected length, spacer count or stack orientation differs: " + identity,
        )

    solids = {row["id"]: row for row in source["changed_finished_solids"]}
    _require(
        len(solids) == len(source["changed_finished_solids"]),
        "unique v7 finished-solid descriptors required",
    )
    orientation_part_ids = set(orientation.get("replacement_part_ids", []))
    _require(
        len(orientation_part_ids) == 224,
        "all 224 current v7 reversed-stack solids must be pinned",
    )
    actual_orientation_parts = {
        row["id"]
        for row in solids.values()
        if any(row["id"].startswith(identity + "_") for identity in orientation_ids)
    }
    _require(
        actual_orientation_parts == orientation_part_ids,
        "v7 reversed-stack part IDs must join the current finished-solid registry",
    )
    for identity in sorted(orientation_part_ids):
        row = solids[identity]
        path = Path(row["path"])
        _require(
            sha(path) == row["sha256"],
            "current v7 oriented stack solid changed: " + identity,
        )
        pins[str(path)] = row["sha256"]

    profile_data: dict[str, dict] = {}
    body_bounds: dict[str, list[float]] = {}
    flat_cleat_profiles = {}
    for name in sorted(wood_receivers):
        row = source["profiles"].get(name)
        _require(
            isinstance(row, dict)
            and len(row.get("vertices_luv_mm", [])) >= 4
            and row.get("finished", {}).get("path")
            and row.get("finished", {}).get("sha256"),
            "authenticated original outer-profile source required: " + name,
        )
        profile_data[name] = outer.outer_profile(
            {
                "member": name,
                "basis_grain_u_v_xyz": row["basis_grain_u_v_xyz"],
                "datum_xyz_mm": row["datum_xyz_mm"],
                "raw_profile_vertices_luv_mm": row["vertices_luv_mm"],
            }
        )
        if name.startswith("eoere_cleat_"):
            flat_cleat_profiles[name] = _flat_cleat_profile_proof(name, row)
        body_ref = row["finished"]
        body_path = Path(body_ref["path"])
        _require(
            sha(body_path) == body_ref["sha256"],
            "original receiver BRep changed: " + name,
        )
        pins[str(body_path)] = body_ref["sha256"]
        body = cq.Shape.importBrep(str(ROOT / body_path))
        _require(
            body.isValid() and len(body.Solids()) == 1 and body.Volume() > 0.0,
            "one valid original receiver solid required: " + name,
        )
        box = body.BoundingBox()
        bounds = [getattr(box, axis + end) for axis in "xyz" for end in ("min", "max")]
        local = np.asarray(profile_data[name]["vertices_luv_mm"], dtype=float)
        basis = np.asarray(profile_data[name]["basis_grain_u_v_xyz"], dtype=float)
        datum = np.asarray(profile_data[name]["datum_xyz_mm"], dtype=float)
        world_vertices = local @ basis + datum
        profile_bounds = [
            float(world_vertices[:, i].min())
            for i in range(3)
        ]
        profile_bounds = [
            value
            for i in range(3)
            for value in (profile_bounds[i], float(world_vertices[:, i].max()))
        ]
        _require(
            max(abs(a - b) for a, b in zip(bounds, profile_bounds, strict=True))
            < 1e-5,
            "cached source solid bounds must match its authenticated full outer profile: "
            + name,
        )
        body_bounds[name] = bounds

    containment_rows = []
    for axis in source["axes"]:
        for receiver in axis["receivers"]:
            if receiver not in wood_receivers:
                continue
            direction = np.asarray(axis["direction_xyz"], dtype=float)
            point = np.asarray(axis["point_xyz_mm"], dtype=float)
            _require(
                direction.shape == (3,)
                and point.shape == (3,)
                and np.isfinite(direction).all()
                and np.isfinite(point).all()
                and abs(float(np.linalg.norm(direction)) - 1.0) < 1e-8,
                "finite unit original bolt axis required: " + axis["id"],
            )
            nonzero = np.flatnonzero(np.abs(direction) > 1e-8)
            _require(
                len(nonzero) == 1 and int(nonzero[0]) in (0, 2),
                "original receiver bore must traverse unit X or Z: " + axis["id"],
            )
            axis_index = int(nonzero[0])
            sign = float(np.copysign(1.0, direction[axis_index]))
            bounds = body_bounds[receiver]
            low, high = bounds[2 * axis_index : 2 * axis_index + 2]
            _require(high > low, "positive original receiver wall span required")
            start, end = point.copy(), point.copy()
            start[axis_index] = low if sign > 0.0 else high
            end[axis_index] = high if sign > 0.0 else low
            profile = profile_data[receiver]
            basis = np.asarray(profile["basis_grain_u_v_xyz"], dtype=float)
            datum = np.asarray(profile["datum_xyz_mm"], dtype=float)
            start_local, end_local = basis @ (start - datum), basis @ (end - datum)
            direction_local = basis @ direction
            radius = float(axis["bore_diameter_mm"]) / 2.0
            _require(math.isfinite(radius) and radius > 0.0, "positive original wood bore required")
            plane_margins = []
            for plane in profile["outer_planes"]:
                normal = np.asarray(plane["normal_luv"], dtype=float)
                center_support = max(float(normal @ start_local), float(normal @ end_local))
                radial_support = radius * math.sqrt(
                    max(0.0, 1.0 - float(normal @ direction_local) ** 2)
                )
                margin = float(plane["offset_luv_mm"]) - center_support - radial_support
                plane_margins.append((margin, plane))
            minimum_margin, controlling = min(plane_margins, key=lambda item: item[0])
            _require(
                math.isfinite(minimum_margin)
                and minimum_margin >= -CONTAINMENT_TOLERANCE_MM,
                "original full-wall bore cylinder exits its source outer profile: "
                + axis["id"]
                + " / "
                + receiver,
            )
            containment_rows.append(
                {
                    "axis_id": axis["id"],
                    "receiver": receiver,
                    "centerline_start_xyz_mm": start.tolist(),
                    "centerline_end_xyz_mm": end.tolist(),
                    "direction_xyz": direction.tolist(),
                    "bore_diameter_mm": float(axis["bore_diameter_mm"]),
                    "minimum_radius_aware_profile_margin_mm": minimum_margin,
                    "controlling_profile_plane_normal_luv": controlling["normal_luv"],
                    "source_profile_interpretation": profile["interpretation"],
                }
            )
    _require(
        len(containment_rows) == 78
        and len({(row["axis_id"], row["receiver"]) for row in containment_rows}) == 78,
        "all 78 original wood receiver bore cylinders must be proven",
    )
    _require(
        sha(FROZEN_BUILDER) == FROZEN_BUILDER_SHA256
        and sha(OUTER_PROFILE_HELPER) == OUTER_PROFILE_HELPER_SHA256,
        "geometry proof sources changed during v7 admission",
    )
    pins[str(FROZEN_BUILDER)] = FROZEN_BUILDER_SHA256
    pins[str(OUTER_PROFILE_HELPER)] = OUTER_PROFILE_HELPER_SHA256
    return {
        "v7_orientation_preserved": {
            "orientation_source": orientation_ref,
            "reversed_axis_count": len(orientation_ids),
            "reversed_axis_ids": sorted(orientation_ids),
            "reversed_stack_part_count": len(orientation_part_ids),
            "reversed_stack_part_ids": sorted(orientation_part_ids),
            "selected_stack_record_count": len(selected),
            "all_v7_axis_records_match_orientation_source": True,
            "v7_selected_length_spacer_and_face_metadata_verified": True,
            "untranslated_stack_solids_source_hash_pinned": True,
        },
        "original_bore_outer_profile_containment": {
            "method": "radius-aware cylinder support against convex hull planes from pinned physical outer-profile vertices",
            "receiver_wall_count": len(containment_rows),
            "receiver_member_count": len(profile_data),
            "flat_cleat_profiles": flat_cleat_profiles,
            "minimum_margin_mm": min(
                row["minimum_radius_aware_profile_margin_mm"]
                for row in containment_rows
            ),
            "tolerance_mm": CONTAINMENT_TOLERANCE_MM,
            "all_full_wall_cylinders_contained": True,
            "profile_source_sha256": {
                name: source["profiles"][name]["finished"]["sha256"]
                for name in sorted(profile_data)
            },
            "cylinders": containment_rows,
            "this_proves_outer_profile_containment_only": True,
            "preserves_nonbolt_recesses_or_channels_by_claim": False,
        },
    }


def _verify_cumulative_v7(
    source: dict,
    current: dict,
    original: dict,
    moved_axes: set[str],
    changed_solids: dict,
    source_guard: dict,
) -> None:
    _require(
        current["selected_stack_overrides"] == original["selected_stack_overrides"],
        "v8 must retain all v7 selected hardware lengths, spacers and thread flags",
    )
    source_axes = {row["id"]: row for row in source["axes"]}
    current_axes = {row["id"]: row for row in current["axes"]}
    _require(set(current_axes) == set(source_axes), "v8 axis identities changed")
    for identity, before in source_axes.items():
        after = current_axes[identity]
        _require(
            after["direction_xyz"] == before["direction_xyz"],
            "v8 may not change the current v7 axis direction: " + identity,
        )
        _require(
            {k: v for k, v in after.items() if k not in ("point_xyz_mm", "attachments")}
            == {k: v for k, v in before.items() if k not in ("point_xyz_mm", "attachments")},
            "v8 may not change selected bolt, grade, length, thread or plate metadata: "
            + identity,
        )
        if identity in moved_axes:
            _require(
                after["point_xyz_mm"]
                == [before["point_xyz_mm"][0], before["point_xyz_mm"][1] + SHIFT_MM,
                    before["point_xyz_mm"][2]],
                "moved v7 axes must receive only the cumulative 6 mm translation: "
                + identity,
            )
        else:
            _require(
                after == before,
                "unmoved v7 axis metadata must remain byte-equivalent: " + identity,
            )

    orientation_ids = set(
        source_guard["v7_orientation_preserved"]["reversed_axis_ids"]
    )
    original_solids = {row["id"]: row for row in original["changed_finished_solids"]}
    reversed_part_ids = source_guard["v7_orientation_preserved"][
        "reversed_stack_part_ids"
    ]
    for part_id in reversed_part_ids:
        original_row = original_solids[part_id]
        current_row = changed_solids[part_id]
        axis_id = next(identity for identity in orientation_ids if part_id.startswith(identity + "_"))
        if axis_id not in moved_axes:
            _require(
                current_row == original_row,
                "unmoved v7 reversed-stack solid must remain byte-equivalent: " + part_id,
            )
        else:
            bounds_before = original_row["bounds_xyz_mm"]
            bounds_after = current_row["bounds_xyz_mm"]
            expected_bounds = [
                value + (SHIFT_MM if i in (2, 3) else 0.0)
                for i, value in enumerate(bounds_before)
            ]
            _require(
                max(
                    abs(a - b)
                    for a, b in zip(bounds_after, expected_bounds, strict=True)
                )
                < 1e-6,
                "moved v7 reversed-stack solid must receive only +6 mm world-Y: "
                + part_id,
            )
    _require(
        orientation_ids <= set(source_axes)
        and source_guard["v7_orientation_preserved"]["reversed_axis_count"] == 40
        and source_guard["original_bore_outer_profile_containment"][
            "receiver_wall_count"
        ]
        == 78,
        "v8 must retain all authenticated v7 reversals and bore containment proofs",
    )


def build() -> dict:
    _require(Path.cwd() == ROOT, "run the guarded v8 geometry adapter from repository root")
    _require(
        not OUTPUT.exists(),
        "fresh ignored analysis/owner-inward-angles-v8/geometry output required",
    )
    _require(sha(OWN) == LOADED_SHA256, "v8 producer changed after import")
    source = _adapt_frozen_builder()
    scope = {
        "__name__": "_eoere_inward_angles_v8_adapter",
        "__file__": str(OWN),
        "V7_SOURCE_GUARD": _v7_source_guard,
        "VERIFY_CUMULATIVE_V7": _verify_cumulative_v7,
    }
    exec(compile(source, str(OWN), "exec"), scope)  # noqa: S102 - guarded frozen producer adaptation
    result = scope["build"](OUTPUT)
    _require(sha(OWN) == LOADED_SHA256, "v8 producer changed during geometry build")
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--inspect-adapter", action="store_true")
    args = parser.parse_args()
    if args.inspect_adapter:
        print(
            json.dumps(
                {
                    "frozen_builder": ref(FROZEN_BUILDER),
                    "v7_receipt": ref(RECEIPT),
                    "revision": REVISION,
                    "output": str(OUTPUT),
                    "adapter_sha256": hashlib.sha256(
                        _adapt_frozen_builder().encode("utf-8")
                    ).hexdigest(),
                    "geometry_build_started": False,
                },
                sort_keys=True,
            ),
            flush=True,
        )
    else:
        print(json.dumps(build(), sort_keys=True), flush=True)
