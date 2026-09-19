from mini_moonboard.a66_layout_common import all_fasteners, all_interfaces, all_records
from mini_moonboard.bolted_layout_common import FAMILY_STATIONS
from mini_moonboard.demountable_connections import validate_records


def test_a66_parallel_lane_covers_all_24_stations_with_four_bolts_each() -> None:
    joints = all_records()
    fasteners = all_fasteners()
    interfaces = all_interfaces()

    validate_records(joints, fasteners, interfaces)
    assert len(joints) == sum(len(stations) for stations in FAMILY_STATIONS.values()) == 24
    assert len(fasteners) == 96
    assert len(interfaces) == 24
    assert all(joint.assessment_status == "prototype" for joint in joints)
    assert all(not fastener.holes for fastener in fasteners)
    by_id = {fastener.physical_fastener_id: fastener for fastener in fasteners}
    for joint in joints:
        plates = [
            next(part.component_id for part in by_id[fastener_id].ordered_stack if part.role == "plate")
            for fastener_id in joint.fastener_ids
        ]
        assert plates == ["a66_flange_a", "a66_flange_a", "a66_flange_b", "a66_flange_b"]


def test_a66_lane_keeps_structural_threads_in_metal() -> None:
    assert all(
        fastener.thread_substrate_during_operation == "metal"
        for fastener in all_fasteners()
    )
