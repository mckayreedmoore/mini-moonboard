"""LB-05 invariants for the shared physical connection representation."""

from dataclasses import replace

import pytest

from mini_moonboard.demountable_connections import (
    AssemblyInterfaceRecord,
    ConnectionRecordError,
    JointRecord,
    LocalBasis,
    a66_prototype_fastener,
    ab90_prototype_fastener,
    screen_machine_bolt_stack,
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


def test_machine_bolt_stack_requires_delivered_dimensions() -> None:
    assert screen_machine_bolt_stack(ab90_prototype_fastener()) == "unresolved_delivered_stack_geometry"
    assert screen_machine_bolt_stack(a66_prototype_fastener()) == "unresolved_delivered_stack_geometry"


def test_machine_bolt_stack_exposes_shoulder_engagement_and_bottoming_failures() -> None:
    delivered = replace(
        ab90_prototype_fastener(), length_reference="delivered measured under head to tip",
        smooth_body_mm=(0.0, 44.0), thread_runout_mm=(44.0, 46.0),
        engagement_bounds_mm=(46.0, 100.0),
    )
    assert screen_machine_bolt_stack(delivered) == "nominal_geometry_pass_only"
    assert screen_machine_bolt_stack(replace(delivered, smooth_body_mm=(0.0, 48.0))) == "fail_nut_on_shoulder_or_runout"
    assert screen_machine_bolt_stack(replace(delivered, thread_runout_mm=(43.0, 48.0))) == "fail_nut_on_shoulder_or_runout"
    assert screen_machine_bolt_stack(replace(delivered, thread_runout_mm=(42.0, 46.0))) == "fail_inconsistent_shank_thread_regions"
    assert screen_machine_bolt_stack(replace(delivered, engagement_bounds_mm=(46.0, 50.0))) == "fail_incomplete_full_thread_engagement"
    assert screen_machine_bolt_stack(delivered, closed_nut_depth_mm=20.0) == "fail_closed_nut_bottoming"
    assert screen_machine_bolt_stack(delivered, minimum_projection_mm=50.0) == "fail_insufficient_bolt_projection"


def test_scope_must_be_explicit_at_runtime() -> None:
    with pytest.raises(ConnectionRecordError, match="hardware scope"):
        replace(ab90_prototype_fastener(), hardware_scope="unknown")


def test_cross_record_validation_accepts_shared_physical_identity() -> None:
    validate_records((joint(),), (ab90_prototype_fastener(),), (interface(),))


def test_duplicate_physical_ids_are_rejected() -> None:
    fastener = ab90_prototype_fastener()
    with pytest.raises(ConnectionRecordError, match="duplicate physical"):
        validate_records((joint(),), (fastener, fastener), (interface(),))


def test_same_physical_bolt_cannot_be_counted_twice_in_a_joint() -> None:
    with pytest.raises(ConnectionRecordError, match="counts a physical fastener twice"):
        validate_records((replace(joint(), fastener_ids=("ab90_proto_m10_1", "ab90_proto_m10_1")),),
                         (ab90_prototype_fastener(),), (interface(),))


def test_unknown_scope_and_structural_wood_thread_are_not_silent() -> None:
    with pytest.raises(ConnectionRecordError, match="structural move"):
        fastener = ab90_prototype_fastener()
        object.__setattr__(fastener, "thread_substrate_during_operation", "wood")
        fastener.__post_init__()


def test_retained_and_removed_fastener_overlap_is_rejected() -> None:
    with pytest.raises(ConnectionRecordError, match="retained and removed"):
        AssemblyInterfaceRecord("i1", ("a", "b"), ("f1",), ("f1",), "open", "straight", "support")
