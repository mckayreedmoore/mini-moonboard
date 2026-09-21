"""The owner layout must account for every selected-baseline SDS duty."""

from types import SimpleNamespace

from scripts.simple_owner_duty_ledger import inventory_status, selected_duties


def test_selected_duties_are_exact_and_same_side():
    duties = selected_duties()
    assert len(duties) == 24
    assert len({axis for duty in duties.values() for axis in duty["sds_axes"]}) == 144
    assert all(len(duty["sds_axes"]) == 6 for duty in duties.values())
    assert all(
        set(duty["axis_starts_mm"]) == set(duty["sds_axes"]) for duty in duties.values()
    )
    assert sum(duty["layout_class"] == "ordinary" for duty in duties.values()) == 20
    assert {
        name for name, duty in duties.items() if duty["layout_class"] == "exception"
    } == {
        "clip_angle_base_left",
        "clip_angle_base_right",
        "clip_timber_header_outer_left",
        "clip_timber_header_outer_right",
    }
    assert duties["clip_angle_base_left"]["timber"] == ("base_header", "base_side_left")
    assert duties["clip_timber_header_outer_left"]["timber"] == (
        "base_header",
        "base_post_outer_left",
    )
    assert duties["clip_angle_base_left"]["local_axes"]["first"] == (0.0, 0.0, -1.0)
    assert duties["clip_timber_header_outer_left"]["local_axes"]["first"] == (
        0.0,
        0.0,
        1.0,
    )
    assert duties["clip_angle_base_left"]["axis_starts_mm"][
        "clip_angle_base_left_beam_1"
    ] == (-1088.0572600000003, -67.75, 279.55524)
    for family in ("base_center", "header_center"):
        pair = [duty for duty in duties.values() if duty["pb02_center_pair"] == family]
        assert {duty["side"] for duty in pair} == {"left", "right"}
        assert {duty["pb02_displaced"] for duty in pair} == {False, True}
        assert next(duty for duty in pair if duty["pb02_displaced"])["side"] == "right"
    assert all(
        duty["timber"][1].endswith(duty["side"])
        and duty["same_side_corner"] == (duty["family"], duty["side"])
        for duty in duties.values()
    )


def test_prospective_inventory_cannot_complete_with_old_hardware():
    duties = selected_duties()
    replacements = {name: f"new_{name}" for name in duties}
    old_axis = duties["clip_angle_base_left"]["sds_axes"][0]
    assert (
        inventory_status(duties, replacements, [], [SimpleNamespace(name=old_axis)])[
            "inventory_mapped_without_legacy"
        ]
        is False
    )
    assert (
        inventory_status(duties, replacements, ["clip_angle_base_left"], [])[
            "inventory_mapped_without_legacy"
        ]
        is False
    )
    assert (
        inventory_status(duties, {"clip_angle_base_left": "new"}, [], [])[
            "inventory_mapped_without_legacy"
        ]
        is False
    )
    clear = inventory_status(duties, replacements, [], [])
    assert clear["inventory_mapped_without_legacy"] is True
    assert clear["structural_approval"] is False
    assert clear["viewer_clearance_approved"] is False
    assert clear["viewer_gates"] == {
        "protected_holds_3d": "unverified",
        "t_nuts_3d": "unverified",
        "unused_hold_holes_3d": "unverified",
        "hold_bolt_protrusion": "unverified",
        "led_body_and_wiring": "unverified",
        "all_66_panel_screws": "unverified",
        "retained_frame_bolts": "unverified",
    }
