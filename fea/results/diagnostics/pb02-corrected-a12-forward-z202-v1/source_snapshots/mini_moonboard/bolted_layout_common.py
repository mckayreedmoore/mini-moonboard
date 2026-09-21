"""Shared prototype layout construction for the six AB90 family modules."""

import csv
from dataclasses import replace
from functools import cache
from pathlib import Path

from .demountable_connections import (
    AssemblyInterfaceRecord,
    FastenerRecord,
    JointRecord,
    LocalBasis,
    ab90_prototype_fastener,
)

ROOT = Path(__file__).resolve().parents[1]
AXES = ROOT / "docs/floor-flush-construction/connection-axes.csv"

FAMILY_STATIONS = {
    "top": (
        "clip_single_top_left_1", "clip_single_top_right_2",
        "clip_split_top_center_left", "clip_split_top_center_right",
    ),
    "bottom": (
        "clip_horizontal_bottom_left_1", "clip_horizontal_bottom_left_2",
        "clip_horizontal_bottom_right_1", "clip_horizontal_bottom_right_2",
    ),
    "service": (
        "clip_horizontal_lower_left_1", "clip_horizontal_lower_left_2",
        "clip_horizontal_lower_right_1", "clip_horizontal_lower_right_2",
        "clip_horizontal_upper_left_1", "clip_horizontal_upper_left_2",
        "clip_horizontal_upper_right_1", "clip_horizontal_upper_right_2",
    ),
    "header_post": (
        "clip_timber_header_outer_left", "clip_timber_header_outer_right",
        "clip_split_header_center_left", "clip_split_header_center_right",
    ),
    "center_base": (
        "clip_split_base_center_left", "clip_split_base_center_right",
    ),
    "outer_base": ("clip_angle_base_left", "clip_angle_base_right"),
}


@cache
def axes_rows() -> tuple[dict[str, str], ...]:
    with AXES.open(newline="") as handle:
        return tuple(csv.DictReader(handle))


def _rows(station: str) -> tuple[dict[str, str], ...]:
    return tuple(row for row in axes_rows()
                 if row["first_member"] == station and row["shop_opening_kind"] == "sds_wood")


def _basis(row: dict[str, str]) -> LocalBasis:
    return LocalBasis(
        (float(row["start_x_mm"]), float(row["start_y_mm"]), float(row["start_z_mm"])),
        (1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0),
    )


def family_records(family: str) -> tuple[JointRecord, ...]:
    result = []
    for station in FAMILY_STATIONS[family]:
        rows = _rows(station)
        if len(rows) != 6:
            raise ValueError(f"Expected six structural axes for {station}")
        members = tuple(sorted({member for row in rows for member in (row["first_member"], row["second_member"])}))
        fasteners = tuple(f"{station}_ab90_bolt_{index}" for index in (1, 2))
        result.append(JointRecord(
            joint_id=f"ab90_{station}",
            joint_family=family,
            legacy_station_or_axis_ids=tuple(row["name"] for row in rows),
            connected_members=members + (f"{station}_ab90_flange_a", f"{station}_ab90_flange_b"),
            local_basis=_basis(rows[0]),
            contact_surfaces=("AB90 flange A", "timber bearing", "AB90 flange B"),
            fastener_ids=fasteners,
            receiver_ids=(f"{station}_ab90_flange_a", f"{station}_ab90_flange_b"),
            simultaneous_case_wrenches=(),
            capacity_basis_and_edition=None,
            stiffness_and_clearance_basis="AB90 factory hole nominal; bolt slip/tool access unresolved",
            required_actions_and_unresolved_actions=(
                "legacy SDS duties require new force recovery",
                "bolt steel/timber resistance unresolved",
                "access and withdrawal path unresolved",
            ),
            assembly_interface_id=f"interface_{station}",
            assessment_status="prototype",
        ))
    return tuple(result)


def family_fasteners(family: str) -> tuple[FastenerRecord, ...]:
    result = []
    for joint in family_records(family):
        for fastener_id in joint.fastener_ids:
            prototype = ab90_prototype_fastener(fastener_id)
            result.append(replace(prototype, legacy_mapping=joint.legacy_station_or_axis_ids))
    return tuple(result)


def family_interfaces(family: str) -> tuple[AssemblyInterfaceRecord, ...]:
    result = []
    for joint in family_records(family):
        result.append(AssemblyInterfaceRecord(
            joint.assembly_interface_id,
            joint.connected_members[:2],
            (),
            joint.fastener_ids,
            "AB90 head/nut access unresolved",
            "withdraw bolt normal to factory hole; neighboring hardware unresolved",
            "temporary support required before structural separation",
        ))
    return tuple(result)


def family_machining(family: str) -> tuple[dict[str, object], ...]:
    result = []
    for joint in family_records(family):
        result.append({
            "joint_id": joint.joint_id,
            "operation": "factory AB90 hole alignment; no new wood bore authorized",
            "status": "prototype_only",
            "receiver_ids": joint.receiver_ids,
        })
    return tuple(result)
