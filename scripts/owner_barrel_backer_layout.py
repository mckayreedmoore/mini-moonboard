"""Four source-bound kicker-backer cross-dowel paths for the current viewer.

The supplied assembly is the finished 24-duty viewer composition. This module
adds a diagnostic connection duty; it does not cut timber or qualify hardware.
"""

import cadquery as cq

from mini_moonboard.box_frame import Connection

SOURCE_ID = "owner-barrel-current-viewer-backer-layout-v1"
_BOLT_LENGTH_MM = 76.2  # Detached 3 in trial, not delivered hardware.
_BARREL_AXIS_Z_MM = 205.0
_NO_RELEASE = {
    "retail_fit_approved": False,
    "thread_engagement_verified": False,
    "capacity_verified": False,
    "complete_assembly_sequence_verified": False,
    "drilling_released": False,
    "fabrication_released": False,
    "structural_released": False,
}


def build_layout(assembly):
    """Return four modeled paths from the existing current-viewer assembly.

    `assembly` must contain the actual `wood`, `barrels`, and `stacks` produced
    by `export_owner_barrel_scene.build_viewer_assembly()`. The detached probe
    validates that source and supplies the sole coordinate/collision record.
    """
    # Import here so the parent assembly can import this producer without an
    # assembly -> probe -> exporter -> assembly import cycle.
    from scripts import owner_barrel_backer_attachment_probe as trial

    if "blocks" in assembly or any(
        "corner_block" in name for name in assembly.get("wood", {})
    ):
        raise ValueError("Backer layout requires the barrel-only viewer wood")
    result = trial.probe(
        assembly=assembly,
        nominal_bolt_length_mm=_BOLT_LENGTH_MM,
        barrel_axis_z_mm=_BARREL_AXIS_Z_MM,
    )
    wood = assembly["wood"]
    header_z = wood[trial.HEADER].BoundingBox().zmax
    stations = {}
    for side in ("left", "right"):
        backer_name = f"inner_kicker_backer_{side}"
        station_name = f"backer_attachment_{side}"
        backer_y = wood[backer_name].BoundingBox().ymin
        bolts, barrels, stacks, drilling, access = {}, {}, {}, {}, {}
        for label, _, _, _ in trial.ROWS:
            source_name = f"{backer_name}/{label}"
            candidate = result["candidates"][source_name]
            x, y = candidate["point_xy_mm"]
            axis_z = candidate["barrel_axis_xyz_mm"][2]
            seat = (x, y, header_z)
            shaft_start = (x, y, header_z + trial.WASHER_THICKNESS_MM)
            barrel_name = f"{station_name}_{label}"
            bolt_name = f"{barrel_name}_bolt"
            barrels[barrel_name] = trial._cylinder(
                (x, y - trial.BARREL_LENGTH_MM / 2, axis_z),
                (0, 1, 0),
                trial.BARREL_LENGTH_MM,
                trial.BARREL_DIAMETER_MM,
            )
            bolts[bolt_name] = Connection(
                name=bolt_name,
                start=cq.Vector(*shaft_start),
                direction=cq.Vector(0, 0, -1),
                length=_BOLT_LENGTH_MM,
                diameter=trial.SHAFT_DIAMETER_MM,
                members=(trial.HEADER, backer_name),
                kind="bolt",
            )
            stacks[bolt_name] = {
                "shaft": trial._cylinder(
                    shaft_start, (0, 0, -1), _BOLT_LENGTH_MM, trial.SHAFT_DIAMETER_MM
                ),
                "washer": trial._cylinder(
                    seat,
                    (0, 0, 1),
                    trial.WASHER_THICKNESS_MM,
                    trial.WASHER_DIAMETER_MM,
                ),
                "head": trial._cylinder(
                    shaft_start,
                    (0, 0, 1),
                    trial.HEAD_HEIGHT_MM,
                    trial.HEAD_DIAMETER_MM,
                ),
            }
            drilling[f"{barrel_name}/machine_bore"] = trial._cylinder(
                seat,
                (0, 0, -1),
                _BOLT_LENGTH_MM + trial.BORE_TIP_ALLOWANCE_MM,
                trial.MACHINE_BORE_DIAMETER_MM,
            )
            drilling[f"{barrel_name}/cross_bore"] = trial._cylinder(
                (x, backer_y, axis_z),
                (0, 1, 0),
                y + trial.BARREL_LENGTH_MM / 2 - backer_y,
                trial.BARREL_DIAMETER_MM,
            )
            access[f"{barrel_name}/bolt_tool"] = trial._cylinder(
                (x, y, shaft_start[2] + trial.HEAD_HEIGHT_MM),
                (0, 0, 1),
                trial.TOOL_LENGTH_MM,
                trial.TOOL_DIAMETER_MM,
            )
            access[f"{barrel_name}/barrel_tool"] = trial._cylinder(
                (x, backer_y, axis_z),
                (0, -1, 0),
                trial.TOOL_LENGTH_MM,
                trial.TOOL_DIAMETER_MM,
            )
        stations[station_name] = {
            "mode": "direct",
            "disposition": "REVISE",
            "bolts": bolts,
            "barrels": barrels,
            "stacks": stacks,
            "drilling_paths": drilling,
            "access_paths": access,
        }
    return {
        "source_id": SOURCE_ID,
        "source_probe_schema": result["schema"],
        "source_pose": result["viewer_pose"],
        "fixed_inventory_counts": result["fixed_inventory_counts"],
        "stations": stations,
        "collision_screen": {
            key: result[key]
            for key in (
                "candidates",
                "mutual_candidate_hits_mm3",
                "nonempty_existing_obstacles",
                "finite_clearance_screen_passed",
            )
        },
        "thread_engagement_verified": False,
        "capacity_verified": False,
        "assembly_sequence_verified": False,
        "release_flags": dict(_NO_RELEASE),
        "limits": (
            "Nominal 3 in / Z=205 mm trial only. Thread span, barrel axis tolerance, "
            "delivered fit, wood/metal capacity, tool fit, assembly, drilling and "
            "fabrication are unverified. No corner blocks or fixed-axis edits."
        ),
    }
