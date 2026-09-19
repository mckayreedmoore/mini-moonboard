"""Complete 24-station A66 prototype records, separate from the AB90 lane."""

from dataclasses import replace

from .bolted_layout_common import FAMILY_STATIONS, _basis, _rows
from .demountable_connections import (
    AssemblyInterfaceRecord,
    FastenerRecord,
    JointRecord,
    a66_prototype_fastener,
)


def family_records(family: str) -> tuple[JointRecord, ...]:
    result = []
    for station in FAMILY_STATIONS[family]:
        rows = _rows(station)
        if len(rows) != 6:
            raise ValueError(f"Expected six structural axes for {station}")
        members = tuple(
            sorted({member for row in rows for member in (row["first_member"], row["second_member"])})
        )
        fasteners = tuple(f"{station}_a66_bolt_{index}" for index in range(1, 5))
        result.append(
            JointRecord(
                joint_id=f"a66_{station}",
                joint_family=family,
                legacy_station_or_axis_ids=tuple(row["name"] for row in rows),
                connected_members=members + (f"{station}_a66_flange_a", f"{station}_a66_flange_b"),
                local_basis=_basis(rows[0]),
                contact_surfaces=("A66 flange A", "timber bearing", "A66 flange B"),
                fastener_ids=fasteners,
                receiver_ids=(f"{station}_a66_flange_a", f"{station}_a66_flange_b"),
                simultaneous_case_wrenches=(),
                capacity_basis_and_edition=None,
                stiffness_and_clearance_basis=(
                    "A66 retail angle; exact factory hole diameter/spacing, washer stack, and access unresolved"
                ),
                required_actions_and_unresolved_actions=(
                    "map each flange to the actual broad or narrow member face",
                    "establish A66 bolt/plate/timber resistance without borrowing nailed ratings",
                    "freeze exact bolt grade, hole tolerance, access, and withdrawal path",
                ),
                assembly_interface_id=f"a66_interface_{station}",
                assessment_status="prototype",
            )
        )
    return tuple(result)


def family_fasteners(family: str) -> tuple[FastenerRecord, ...]:
    result = []
    for joint in family_records(family):
        for index, fastener_id in enumerate(joint.fastener_ids):
            result.append(
                replace(
                    a66_prototype_fastener(fastener_id, "a" if index < 2 else "b"),
                    legacy_mapping=joint.legacy_station_or_axis_ids,
                )
            )
    return tuple(result)


def family_interfaces(family: str) -> tuple[AssemblyInterfaceRecord, ...]:
    return tuple(
        AssemblyInterfaceRecord(
            joint.assembly_interface_id,
            joint.connected_members[:2],
            (),
            joint.fastener_ids,
            "A66 head/nut access and simultaneous wrench clearance unresolved",
            "withdraw four bolts normal to the selected flange faces; exact path unresolved",
            "temporary support required before structural separation",
        )
        for joint in family_records(family)
    )


def all_records() -> tuple[JointRecord, ...]:
    return tuple(joint for family in FAMILY_STATIONS for joint in family_records(family))


def all_fasteners() -> tuple[FastenerRecord, ...]:
    return tuple(fastener for family in FAMILY_STATIONS for fastener in family_fasteners(family))


def all_interfaces() -> tuple[AssemblyInterfaceRecord, ...]:
    return tuple(interface for family in FAMILY_STATIONS for interface in family_interfaces(family))
