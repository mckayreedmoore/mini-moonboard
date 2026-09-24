import hashlib
from dataclasses import replace

import cadquery as cq
import pytest

from mini_moonboard.wood_joint_geometry import (
    AccessSweep,
    BoltHardware,
    BoltStack,
    Bore,
    ContactClass,
    ContactDeclaration,
    CutRecord,
    EvidenceRecord,
    FinishedPart,
    GeometryBody,
    LocalFrame,
    StackLayer,
    WasherSeat,
    access_sweep_report,
    bolt_pair_spacing,
    bolt_stack_report,
    classify_contact,
    face_ligament_report,
    linear_bolt_row_report,
    local_extrema,
    representative_worst_corner_fixture,
    screen_clearance,
    validate_bore_host,
    washer_support_report,
)

FRAME = LocalFrame((0, 0, 0), (1, 0, 0), (0, 1, 0), (0, 0, 1))
SOURCE = hashlib.sha256(b"fixture source").hexdigest()


def box_part(part_id="host", *, cut=None):
    uncut = cq.Workplane("XY").box(100, 50, 38.1, centered=(False, False, False)).val()
    modifications = ()
    finished = uncut
    if cut is not None:
        finished = uncut.cut(cut)
        modifications = (CutRecord("service_relief", part_id, "relief", cut, "router"),)
    return FinishedPart(
        part_id,
        "nominal 2x stock",
        (100, 50, 38.1),
        "DF-L No. 2",
        (1, 0, 0),
        FRAME,
        "one person",
        uncut,
        finished,
        modifications,
        SOURCE,
        "sawn and drilled",
    )


def hardware(length=80.0, diameter=9.525):
    return BoltHardware(
        "candidate bolt",
        length,
        diameter,
        diameter + 0.5,
        diameter + 1.0,
        16.0,
        6.0,
        24.0,
        10.0,
        2.0,
        17.0,
        8.0,
        10.0,
        length,
    )


def bolt_stack(length=80.0):
    return BoltStack(
        "B1",
        hardware(length),
        (25, 25, -2),
        (0, 0, 1),
        (StackLayer("lower", 38.1), StackLayer("upper", 38.1)),
        WasherSeat("lower", (25, 25, 0), (0, 0, 1)),
        WasherSeat("upper", (25, 25, 76.2), (0, 0, -1)),
        1.0,
    )


def test_short_bolt_cannot_pass_longer_grip():
    report = bolt_stack_report(bolt_stack(80.0))
    assert report.grip_mm == pytest.approx(76.2)
    assert report.required_under_head_length_mm == pytest.approx(89.2)
    assert report.length_margin_mm == pytest.approx(-9.2)
    assert not report.passes


def test_full_nominal_shaft_and_three_diameters_remain_distinct():
    stack = bolt_stack(100.0)
    installed = stack.installed_shapes()
    assert installed["shaft"].BoundingBox().zmin == pytest.approx(-2.0)
    assert installed["shaft"].BoundingBox().zmax == pytest.approx(98.0)
    assert installed["head"].BoundingBox().zmin == pytest.approx(-8.0)
    assert installed["head_washer"].BoundingBox().zmin == pytest.approx(-2.0)
    assert installed["head_washer"].BoundingBox().zmax == pytest.approx(0.0)
    assert installed["nut_washer"].BoundingBox().zmin == pytest.approx(76.2)
    assert installed["nut"].BoundingBox().zmax == pytest.approx(86.2)
    assert stack.hardware.steel_diameter_mm == pytest.approx(9.525)
    assert stack.hardware.drill_diameter_mm == pytest.approx(10.525)
    assert stack.hardware.cad_occupied_diameter_mm == pytest.approx(10.025)


def test_washer_over_void_gets_no_full_seat_credit():
    host = cq.Workplane("XY").box(60, 60, 20, centered=(True, True, False)).val()
    void = (
        cq.Workplane("XY")
        .box(12, 40, 10, centered=(True, True, False))
        .translate((8, 0, 10))
        .val()
    )
    finished = host.cut(void)
    seat = WasherSeat("host", (0, 0, 20), (0, 0, -1))
    report = washer_support_report(seat, finished, hardware(100))
    assert 0 < report.support_fraction < 1
    assert report.unsupported_area_mm2 > 0
    assert not report.full_seat


def test_wrong_host_bore_is_rejected():
    right = box_part("right")
    wrong_shape = (
        cq.Workplane("XY")
        .box(100, 50, 38.1, centered=(False, False, False))
        .translate((0, 100, 0))
        .val()
    )
    wrong = FinishedPart(
        "wrong",
        "nominal 2x stock",
        (100, 50, 38.1),
        "DF-L No. 2",
        (1, 0, 0),
        FRAME,
        "one person",
        wrong_shape,
        wrong_shape,
        (),
        SOURCE,
        "sawn and drilled",
    )
    bore = Bore("bore_1", "wrong", (25, 25, 0), (0, 0, 1), 38.1, 10.5)
    report = validate_bore_host(bore, {"right": right, "wrong": wrong})
    assert report.cutter_containment_fraction == pytest.approx(0)
    assert not report.passes


def test_correct_host_bore_passes_geometric_containment_only():
    host = box_part()
    report = validate_bore_host(
        Bore("bore_1", "host", (25, 25, 0), (0, 0, 1), 38.1, 10.5),
        {"host": host},
    )
    assert report.cutter_containment_fraction == pytest.approx(1)
    assert report.passes


def test_bore_rejects_finished_host_relief_even_when_uncut_stock_contains_it():
    relief = (
        cq.Workplane("XY")
        .box(20, 20, 10, centered=(True, True, False))
        .translate((25, 25, 14))
        .val()
    )
    host = box_part(cut=relief)
    report = validate_bore_host(
        Bore("bore_1", "host", (25, 25, 0), (0, 0, 1), 38.1, 10.5),
        {"host": host},
    )
    assert report.cutter_containment_fraction < 1
    assert not report.passes


def test_three_eighth_screen_does_not_reuse_quarter_inch_end_distance():
    three_eighth = linear_bolt_row_report(
        152.4, (50, 100.159), 9.525, end_distance_multiple=7
    )
    quarter = linear_bolt_row_report(
        152.4, (50, 100.159), 6.35, end_distance_multiple=7
    )
    assert three_eighth.required_end_distance_mm == pytest.approx(66.675)
    assert quarter.required_end_distance_mm == pytest.approx(44.45)
    assert not three_eighth.end_distance_passes
    assert quarter.end_distance_passes


def test_narrow_face_fails_symmetric_25_mm_center_target():
    report = face_ligament_report(38.1, (19.05,), 9.525, 25.0)
    assert report.center_edge_distances_mm == ((19.05, 19.05),)
    assert report.clear_ligaments_mm[0] == pytest.approx((14.2875, 14.2875))
    assert not report.target_passes


def test_pair_spacing_uses_selected_steel_diameter():
    report = bolt_pair_spacing((0, 0, 0), (60, 0, 0), 9.525)
    assert report.center_distance_mm == pytest.approx(60)
    assert report.diameter_multiple == pytest.approx(60 / 9.525)


def test_local_extrema_use_named_rotated_frame():
    body = cq.Workplane("XY").box(10, 20, 30, centered=(False, False, False)).val()
    frame = LocalFrame((0, 0, 0), (0, 1, 0), (-1, 0, 0), (0, 0, 1))
    result = local_extrema(body, frame)
    assert result.x_mm == pytest.approx((0, 20), abs=1e-6)
    assert result.t_mm == pytest.approx((-10, 0), abs=1e-6)
    assert result.n_mm == pytest.approx((0, 30), abs=1e-6)


def test_changed_cut_invalidates_finished_geometry_fingerprint():
    first_cut = (
        cq.Workplane("XY")
        .box(10, 10, 10, centered=(False, False, False))
        .translate((20, 20, 28.1))
        .val()
    )
    second_cut = (
        cq.Workplane("XY")
        .box(10, 10, 10, centered=(False, False, False))
        .translate((30, 20, 28.1))
        .val()
    )
    first = box_part(cut=first_cut)
    repeat = box_part(cut=first_cut)
    changed = box_part(cut=second_cut)
    assert first.finished_fingerprint == repeat.finished_fingerprint
    assert first.finished_fingerprint != changed.finished_fingerprint
    assert first.modifications[0].removed_volume_mm3 == pytest.approx(1000)


def test_finished_part_rejects_translated_or_unrecorded_finished_geometry():
    uncut = cq.Workplane("XY").box(100, 50, 38.1, centered=(False, False, False)).val()
    unrecorded_cut = (
        cq.Workplane("XY")
        .box(10, 10, 10, centered=(False, False, False))
        .translate((20, 20, 28.1))
        .val()
    )

    def record(finished, modifications=()):
        return FinishedPart(
            "host",
            "nominal 2x stock",
            (100, 50, 38.1),
            "DF-L No. 2",
            (1, 0, 0),
            FRAME,
            "one person",
            uncut,
            finished,
            modifications,
            SOURCE,
            "sawn and drilled",
        )

    with pytest.raises(ValueError, match="within uncut stock"):
        record(uncut.translate((1, 0, 0)))
    with pytest.raises(ValueError, match="recorded modifications"):
        record(uncut.cut(unrecorded_cut))
    with pytest.raises(ValueError, match="recorded modifications"):
        record(
            uncut,
            (CutRecord("missing_cut", "host", "relief", unrecorded_cut, "router"),),
        )


@pytest.mark.parametrize(
    ("origin", "head_normal", "nut_center", "nut_normal", "message"),
    (
        ((25, 25, 0), (0, 0, 1), (25, 25, 76.2), (0, 0, -1), "under-head datum"),
        ((25, 25, -2), (0, 0, -1), (25, 25, 76.2), (0, 0, -1), "inward normal"),
        ((25, 25, -2), (0, 0, 1), (25, 25, 75.2), (0, 0, -1), "stack grip"),
        ((25, 25, -2), (0, 0, 1), (25, 25, 76.2), (0, 0, 1), "inward normal"),
    ),
)
def test_bolt_stack_rejects_misaligned_washer_seats(
    origin, head_normal, nut_center, nut_normal, message
):
    with pytest.raises(ValueError, match=message):
        BoltStack(
            "B1",
            hardware(100),
            origin,
            (0, 0, 1),
            (StackLayer("lower", 38.1), StackLayer("upper", 38.1)),
            WasherSeat("lower", (25, 25, 0), head_normal),
            WasherSeat("upper", nut_center, nut_normal),
        )


def test_contact_classification_needs_explicit_pair_declaration():
    declaration = ContactDeclaration("bolt", "host", ContactClass.BOLT_IN_OWN_BORE)
    assert (
        classify_contact("host", "bolt", (declaration,))
        == ContactClass.BOLT_IN_OWN_BORE
    )
    assert classify_contact("other", "bolt", (declaration,)) == ContactClass.UNRELATED


def test_known_solid_collision_remains_failure():
    first = GeometryBody("first", "wood", cq.Workplane("XY").box(20, 20, 20).val())
    second = GeometryBody(
        "second", "retained_bolt", cq.Solid.makeCylinder(5, 30, cq.Vector(0, 0, -15))
    )
    row = screen_clearance((first, second))[0]
    assert row.intersection_volume_mm3 > 0
    assert row.classification == ContactClass.UNRELATED
    assert row.failure


def test_declared_intended_contact_is_classified_but_still_measured():
    first = GeometryBody("first", "wood", cq.Workplane("XY").box(20, 20, 20).val())
    second = GeometryBody(
        "second", "wood", cq.Workplane("XY").box(20, 20, 20).translate((0, 0, 10)).val()
    )
    declaration = ContactDeclaration(
        "first", "second", ContactClass.INTENDED_WOOD_CONTACT
    )
    row = screen_clearance((first, second), (declaration,))[0]
    assert row.intersection_volume_mm3 > 0
    assert row.failure


def test_declared_face_contact_and_hardware_relationships_are_not_clashes():
    first = GeometryBody("first", "wood", cq.Workplane("XY").box(20, 20, 20).val())
    face_touch = GeometryBody(
        "face_touch",
        "wood",
        cq.Workplane("XY").box(20, 20, 20).translate((0, 0, 20)).val(),
    )
    bolt = GeometryBody(
        "bolt", "bolt", cq.Solid.makeCylinder(5, 20, cq.Vector(0, 0, -10))
    )
    washer = GeometryBody(
        "washer", "washer", cq.Solid.makeCylinder(8, 2, cq.Vector(0, 0, 10))
    )
    declarations = (
        ContactDeclaration("first", "face_touch", ContactClass.INTENDED_WOOD_CONTACT),
        ContactDeclaration("first", "bolt", ContactClass.BOLT_IN_OWN_BORE),
        ContactDeclaration("first", "washer", ContactClass.WASHER_ON_DECLARED_HOST),
    )
    rows = {
        frozenset((row.first_id, row.second_id)): row
        for row in screen_clearance((first, face_touch, bolt, washer), declarations)
    }
    assert not rows[frozenset(("first", "face_touch"))].failure
    assert not rows[frozenset(("first", "bolt"))].failure
    assert not rows[frozenset(("first", "washer"))].failure


def test_declared_washer_host_relationship_rejects_buried_washer():
    host = GeometryBody("host", "wood", cq.Workplane("XY").box(20, 20, 20).val())
    buried = GeometryBody(
        "washer", "washer", cq.Solid.makeCylinder(8, 2, cq.Vector(0, 0, -1))
    )
    declaration = ContactDeclaration(
        "host", "washer", ContactClass.WASHER_ON_DECLARED_HOST
    )
    row = screen_clearance((host, buried), (declaration,))[0]
    assert row.intersection_volume_mm3 > 0
    assert row.failure


def evidence_record():
    digest = hashlib.sha256(b"evidence").hexdigest()
    return EvidenceRecord(
        digest,
        digest,
        (("source.py", digest),),
        "test producer",
        "uv run producer",
        digest,
        "geometry-only fixture",
        "unverified",
        None,
        "No strength result",
        (),
    )


@pytest.mark.parametrize(
    ("field", "value"),
    (
        ("producer", ""),
        ("command", " "),
        ("applicability", ""),
        ("result", ""),
    ),
)
def test_evidence_record_requires_descriptive_fields(field, value):
    with pytest.raises(ValueError, match="producer, command, applicability and result"):
        replace(evidence_record(), **{field: value})


@pytest.mark.parametrize(
    "sources",
    (
        (),
        (("", "a" * 64),),
        ((" ", "a" * 64),),
        (("source.py", ""),),
    ),
)
def test_evidence_record_requires_nonempty_named_sources(sources):
    with pytest.raises(ValueError, match="nonempty named source fingerprints"):
        replace(evidence_record(), source_fingerprints=sources)


def test_evidence_record_rejects_unknown_runtime_status():
    with pytest.raises(ValueError, match="Unknown evidence status"):
        replace(evidence_record(), status="complete")


def test_representative_fixture_has_all_required_obstacle_classes_and_known_access_clash():
    fixture = representative_worst_corner_fixture()
    assert {body.category for body in fixture.bodies} == {
        "finished_wood",
        "neighboring_wood",
        "retained_screw",
        "hold_tnut",
        "light",
        "wire",
        "retained_bolt",
    }
    report = access_sweep_report(fixture.access, fixture.bodies)
    assert not report.passes
    assert any(
        row.failure and "retained_bolt" in (row.first_id, row.second_id)
        for row in report.collisions
    )


def test_access_sweep_clears_distant_obstacle():
    obstacle = GeometryBody(
        "distant",
        "wood",
        cq.Workplane("XY").box(10, 10, 10).translate((100, 0, 0)).val(),
    )
    report = access_sweep_report(
        AccessSweep("tool", (0, 0, 0), (0, 0, 1), 20, 30, 30), (obstacle,)
    )
    assert report.passes
    assert report.minimum_clearance_mm > 80
