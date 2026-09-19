"""LB-05 invariants for the shared physical connection representation."""

import pytest

from mini_moonboard.demountable_connections import (
    AssemblyInterfaceRecord,
    ConnectionRecordError,
    JointRecord,
    LocalBasis,
    a66_prototype_fastener,
    ab90_prototype_fastener,
    validate_records,
)


def interface() -> AssemblyInterfaceRecord:
    return AssemblyInterfaceRecord("i1", ("member_a", "member_b"), ("ab90_proto_m10_1",), (), "open", "straight", "support")


def joint() -> JointRecord:
    return JointRecord(
        "j1", "top", ("station",), ("member_a", "member_b"),
        LocalBasis((0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0)),
        ("a-b bearing",), ("ab90_proto_m10_1",), ("ab90_flange_a", "ab90_flange_b"),
        (), None, "clearance unresolved", ("shear", "bolt resistance"), "i1", "prototype",
    )


def test_ab90_stack_has_more_than_two_participants_and_metal_threads() -> None:
    fastener = ab90_prototype_fastener()
    assert len(fastener.ordered_stack) == 7
    assert fastener.thread_substrate_during_operation == "metal"
    assert fastener.wood_engaging_component_remains_installed is False


def test_a66_stack_keeps_missing_factory_hole_geometry_explicit() -> None:
    fastener = a66_prototype_fastener()
    assert fastener.product_or_design_id == "Simpson-A66-prototype-3/8-through-bolt"
    assert fastener.nominal_diameter_mm == 9.525
    assert fastener.hardware_scope == "structural"
    assert fastener.thread_substrate_during_operation == "metal"
    assert fastener.holes == ()
    assert "hole diameter" in fastener.tool_envelope
    assert [part.component_id for part in fastener.ordered_stack if part.role == "plate"] == ["a66_flange_a"]
    assert next(part for part in fastener.ordered_stack if part.role == "receiver").thickness_mm is None
    assert [part.component_id for part in a66_prototype_fastener(flange="b").ordered_stack if part.role == "plate"] == ["a66_flange_b"]


def test_cross_record_validation_accepts_shared_physical_identity() -> None:
    validate_records((joint(),), (ab90_prototype_fastener(),), (interface(),))


def test_duplicate_physical_ids_are_rejected() -> None:
    fastener = ab90_prototype_fastener()
    with pytest.raises(ConnectionRecordError, match="duplicate physical"):
        validate_records((joint(),), (fastener, fastener), (interface(),))


def test_unknown_scope_and_structural_wood_thread_are_not_silent() -> None:
    with pytest.raises(ConnectionRecordError, match="structural move"):
        fastener = ab90_prototype_fastener()
        object.__setattr__(fastener, "thread_substrate_during_operation", "wood")
        fastener.__post_init__()


def test_retained_and_removed_fastener_overlap_is_rejected() -> None:
    with pytest.raises(ConnectionRecordError, match="retained and removed"):
        AssemblyInterfaceRecord("i1", ("a", "b"), ("f1",), ("f1",), "open", "straight", "support")
