import json
from dataclasses import fields
from pathlib import Path
from types import SimpleNamespace

import cadquery as cq
import pytest

from scripts import wood_joint_top_outer_integration as top

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def inventory():
    return json.loads((ROOT / top.INVENTORY_PATH).read_text())


def _face_rows_and_frame(inventory):
    frames = top._source_frames(inventory)
    rail_frame = frames["base_rail_top"]
    parts = top._part_rows(inventory)
    inward = {
        "base_rail_top": -rail_frame.t,
        "base_side_left": rail_frame.x,
        "base_side_right": -rail_frame.x,
    }
    faces = {
        host: top._face_record(host, parts[host], rail_frame, normal)
        for host, normal in inward.items()
    }
    low_t = rail_frame.coordinates(
        cq.Vector(*faces["base_rail_top"]["center_global_xyz_mm"])
    )[1]
    cleat_frame = top.SourceLocalFrame(
        origin=rail_frame.point(0.0, low_t, 0.0),
        x=rail_frame.x,
        t=rail_frame.t,
        n=rail_frame.n,
    )
    return rail_frame, cleat_frame, parts, faces


def _box(x, y, z, origin=(0, 0, 0)):
    return cq.Solid.makeBox(x, y, z, cq.Vector(*origin))


def test_top_pair_uses_two_source_bound_cleats_and_eight_ordinary_stacks(inventory):
    rail_frame, frame, _, faces = _face_rows_and_frame(inventory)
    duties = top._duty_rows(inventory)
    raw_cleats, stacks, rows = top._build_stack_rows(frame, faces, duties)

    assert set(raw_cleats) == {
        "top_outer_left_cleat",
        "top_outer_right_cleat",
    }
    assert len(stacks) == len(rows) == 8
    assert all(
        shape.Volume() == pytest.approx(88.9 * 88.9 * 119.7, abs=1e-5)
        for shape in raw_cleats.values()
    )

    for part_id, shape in raw_cleats.items():
        local = [frame.coordinates(vertex.Center()) for vertex in shape.Vertices()]
        x_values, t_values, n_values = zip(*local, strict=True)
        assert min(t_values) == pytest.approx(-88.9, abs=1e-5)
        assert max(t_values) == pytest.approx(0.0, abs=1e-5)
        assert min(n_values) == pytest.approx(20.0, abs=1e-5)
        assert max(n_values) == pytest.approx(139.7, abs=1e-5)
        if part_id == "top_outer_left_cleat":
            assert min(x_values) == pytest.approx(0.0, abs=1e-5)
            assert max(x_values) == pytest.approx(88.9, abs=1e-5)
        else:
            assert min(x_values) == pytest.approx(2168.525, abs=1e-5)
            assert max(x_values) == pytest.approx(2257.425, abs=1e-5)

    rail_rows = [row for row in rows.values() if row["interface"] == "cleat_to_base_rail_top"]
    assert len(rail_rows) == 4
    assert sorted(row["local_point_xyz_mm"][0] for row in rail_rows) == pytest.approx(
        [45.45, 45.45, 2211.975, 2211.975]
    )
    right_rail_row = next(
        row
        for row in rail_rows
        if row["station_id"] == "clip_single_top_right_2"
    )
    assert rail_frame.origin.x == pytest.approx(-1130.3, abs=1e-6)
    assert right_rail_row["local_point_xyz_mm"][0] == pytest.approx(2211.975)
    assert right_rail_row["global_point_xyz_mm"][0] == pytest.approx(1081.675)
    transformed_global = frame.point(*right_rail_row["local_point_xyz_mm"])
    assert tuple(transformed_global.toTuple()) == pytest.approx(
        tuple(right_rail_row["global_point_xyz_mm"]), abs=1e-6
    )
    assert sorted(row["local_point_xyz_mm"][2] for row in rail_rows) == pytest.approx(
        [63.35, 63.35, 96.35, 96.35]
    )
    assert {stack.grip_mm for stack in stacks.values()} == {127.0, 177.8}
    assert all(
        set(stack.installed_shapes())
        == {"shaft", "head", "head_washer", "nut_washer", "nut"}
        for stack in stacks.values()
    )
    assert "finished_hosts" not in {field.name for field in fields(top.TopOuterIntegrationGeometry)}


def test_source_axis_entry_faces_are_selected_by_start_direction_and_host(inventory):
    frames = top._source_frames(inventory)
    parts = top._part_rows(inventory)
    axes = [
        axis
        for duty in inventory["legacy_duties"]
        if duty["legacy_station_id"] in top.TARGET_DUTY_IDS
        for axis in duty["legacy_sds_axes"]
    ]
    audits = {
        axis["axis_id"]: top._inventory_entry_face(
            axis, axis["members"][1], parts[axis["members"][1]], frames[axis["members"][1]]
        )
        for axis in axes
    }
    assert len(audits) == 12
    assert {row["host_member"] for row in audits.values()} == top.HOST_IDS
    assert all(row["opposing_face_tie_rejected_by_entry_provenance"] for row in audits.values())

    bad_axis = dict(axes[0])
    bad_axis["axis_global_xyz"] = [-value for value in bad_axis["axis_global_xyz"]]
    host = bad_axis["members"][1]
    with pytest.raises(ValueError, match="resolves 0 entry faces"):
        top._inventory_entry_face(bad_axis, host, parts[host], frames[host])


def test_layer_screen_requires_pre_bore_material(inventory):
    hardware = top.wj06_outer._hardware(top.wj06_outer.RAIL_BOLT_LENGTH_MM, side=False)
    stack = top._make_stack(
        axis_id="test/pre_bore_state",
        cleat_id="cleat",
        receiver_id="rail",
        point=cq.Vector(0, 0, 0),
        direction=cq.Vector(1, 0, 0),
        layers=(("cleat", 10.0), ("rail", 10.0)),
        hardware=hardware,
    )
    raw_parts = {
        "cleat": _box(10, 20, 20, (0, -10, -10)),
        "rail": _box(10, 20, 20, (10, -10, -10)),
    }
    pre_bore = top._layer_checks({stack.id: stack}, raw_parts)[stack.id]
    bore = top._through_bore(stack)
    after_bore = {name: shape.cut(bore) for name, shape in raw_parts.items()}
    post_bore = top._layer_checks({stack.id: stack}, after_bore)[stack.id]

    assert pre_bore["all_declared_layers_present"] is True
    assert post_bore["all_declared_layers_present"] is False
    assert all(row["full_declared_layer_present"] for row in pre_bore["layers_head_to_nut"])


def test_interface_support_discounts_only_intended_new_bore_voids():
    frame = top.SourceLocalFrame(
        origin=cq.Vector(0, 0, 0),
        x=cq.Vector(1, 0, 0),
        t=cq.Vector(0, 1, 0),
        n=cq.Vector(0, 0, 1),
    )
    cleat = _box(10, 10, 10, (0, -10, 0))
    host = _box(10, 10, 10, (0, 0, 0))
    hardware = top.wj06_outer._hardware(top.wj06_outer.RAIL_BOLT_LENGTH_MM, side=False)
    stack = top._make_stack(
        axis_id="test/interface_bore",
        cleat_id="cleat",
        receiver_id="base_rail_top",
        point=cq.Vector(5, -10, 5),
        direction=cq.Vector(0, 1, 0),
        layers=(("cleat", 10.0), ("base_rail_top", 10.0)),
        hardware=hardware,
    )
    bore = top._through_bore(stack)
    finished_host = host.cut(bore)
    face_rows = {
        "base_rail_top": {
            "face_id": "test_low_T",
            "center_global_xyz_mm": [5, 0, 5],
        }
    }
    args = (
        {"cleat": cleat},
        {"base_rail_top": finished_host},
        frame,
        face_rows,
        {"base_rail_top": -frame.t},
        {"cleat": ("base_rail_top",)},
        {"cleat": {stack.id: bore}},
        {"cleat": {}},
    )

    supported = top._host_face_checks(*args)["cleat"]["base_rail_top"]
    missing_host_patch = host.cut(_box(2, 0.05, 10, (0, 0, 0)))
    unsupported = top._host_face_checks(
        args[0],
        {"base_rail_top": missing_host_patch.cut(bore)},
        *args[2:],
    )["cleat"]["base_rail_top"]

    assert supported["gross_contact_slab_volume_mm3"] > supported[
        "expected_finished_candidate_contact_slab_volume_mm3"
    ]
    assert supported["intentional_candidate_receiver_voids_discounted"] is True
    assert supported["full_contact_slab_material_present"] is True
    assert unsupported["full_contact_slab_material_present"] is False


def test_shared_host_preview_removes_only_declared_old_axes_before_new_bores():
    raw = _box(30, 20, 20, (0, -10, -10))
    target_cut = cq.Solid.makeCylinder(2, 30, cq.Vector(5, 0, 0), cq.Vector(1, 0, 0))
    retained_cut = cq.Solid.makeCylinder(2, 30, cq.Vector(20, 0, 0), cq.Vector(1, 0, 0))
    new_bore = cq.Solid.makeCylinder(2, 30, cq.Vector(12, 0, 0), cq.Vector(1, 0, 0))
    geometry = SimpleNamespace(replaced_source_axis_ids=frozenset(), candidate_bores={})
    raw_hosts = {"host": raw}
    native = {"host": {"replace-me": target_cut, "keep-me": retained_cut}}
    purchase = {"host": {}}
    pre_bore = top._preview_shared_hosts(
        geometry,
        raw_hosts,
        native,
        purchase,
        frozenset({"replace-me"}),
        {},
    )["host"]
    after_bore = top._preview_shared_hosts(
        geometry,
        raw_hosts,
        native,
        purchase,
        frozenset({"replace-me"}),
        {"host": {"new-axis": new_bore}},
    )["host"]
    expected = pre_bore.cut(new_bore).clean()

    assert top._shape_difference_volume(pre_bore, raw.cut(retained_cut).clean()) == pytest.approx(
        0.0, abs=1e-5
    )
    assert top._shape_difference_volume(after_bore, expected) == pytest.approx(0.0, abs=1e-5)


def test_candidate_scene_uses_all_six_panels_and_replacement_overlay():
    panels = {name: _box(1, 1, 1, (index * 3, 0, 0)) for index, name in enumerate(sorted(top.PANEL_NAMES))}
    hosts = {name: _box(2, 2, 2, (index * 5, 5, 0)) for index, name in enumerate(top.HOST_IDS)}

    class Source:
        def parts(self):
            return [SimpleNamespace(name=name, shape=shape) for name, shape in {**panels, **hosts}.items()]

    replacement = _box(1, 1, 1, (50, 0, 0))
    geometry = SimpleNamespace(
        finished_hosts={},
        additional_finished_source_parts={},
        panel_replacements={"main_upper_right": replacement},
    )
    scene = top._candidate_scene(geometry, Source(), hosts)

    assert set(top.PANEL_NAMES) <= scene.keys()
    assert top._shape_difference_volume(scene["main_upper_right"], replacement) == pytest.approx(
        0.0, abs=1e-8
    )
    assert scene["main_lower_left"] is panels["main_lower_left"]


def test_cleat_body_screen_includes_existing_candidate_hardware():
    cleat = _box(10, 10, 10)
    existing_shaft = cq.Solid.makeCylinder(1, 8, cq.Vector(5, 5, 1), cq.Vector(0, 0, 1))
    protected = {
        "fixed_66_hillman_axes_63p5mm": {},
        "retained_12_frame_bolt_components": {},
        "retained_12_frame_bolt_tools_withdrawals": {},
        "retained_legacy_clips": {},
        "retained_legacy_sds_axes": {},
        "tnuts": {},
        "hold_hole_and_provisional_projection": {},
        "lights": {},
        "wires": {},
    }
    geometry = SimpleNamespace(
        source_inventory={"legacy_duties": []},
        protected=protected,
        candidate_installed_hardware={"existing/axis": {"shaft": existing_shaft}},
        panel_replacements={},
    )
    context = {"protected": protected, "frame_shapes": {}}

    body_checks, _, _ = top._source_and_candidate_screens(
        geometry,
        context,
        timber={},
        candidate_parts={"new_cleat": cleat},
        raw_cleats={"new_cleat": cleat},
        finished_cleats={"new_cleat": cleat},
        stacks={},
        installed={},
        access={},
        frame_proxies={},
    )

    check = body_checks["new_cleat"]
    assert check["existing_candidate_hardware_hits_mm3"]
    assert check["static_body_conflicts_absent"] is False


def test_top_duty_protected_clips_and_sds_are_removed_but_other_legacy_obstacles_remain(
    inventory,
):
    target_axes = {
        axis["axis_id"]
        for duty in inventory["legacy_duties"]
        if duty["legacy_station_id"] in top.TARGET_DUTY_IDS
        for axis in duty["legacy_sds_axes"]
    }
    box = _box(1, 1, 1)
    protected = {
        "fixed_66_hillman_axes_63p5mm": {},
        "retained_12_frame_bolt_components": {f"installed/{i}": box for i in range(60)},
        "retained_12_frame_bolt_tools_withdrawals": {f"access/{i}": box for i in range(36)},
        "retained_legacy_clips": {name: box for name in [*top.TARGET_DUTY_IDS, "unreplaced_clip"]},
        "retained_legacy_sds_axes": {name: box for name in [*target_axes, "unreplaced_sds"]},
        "tnuts": {},
        "hold_hole_and_provisional_projection": {},
        "lights": {},
        "wires": {},
    }
    frame_ids = [row["axis_id"] for row in inventory["starting_frame_bolts"]]
    frame_shapes = {
        **{f"frame/{i}/installed_component_{j}": box for i in frame_ids for j in range(5)},
        **{f"frame/{i}/source_occupied_axis": box for i in frame_ids},
    }
    fake_context = {"protected": protected, "frame_shapes": frame_shapes}
    fake_geometry = SimpleNamespace(source_inventory=inventory)

    physical, access, proxies = top._physical_and_access_maps(fake_context, fake_geometry)

    assert not any(name.startswith("retained_legacy_clips/clip_single_top_") for name in physical)
    assert not any(name.removeprefix("retained_legacy_sds_axes/") in target_axes for name in physical)
    assert "retained_legacy_clips/unreplaced_clip" in physical
    assert "retained_legacy_sds_axes/unreplaced_sds" in physical
    assert len(proxies) == 12
    assert not any("source_occupied_axis" in name for name in physical)
    assert len(access) == 36


def test_retained_context_census_validates_g16_services_frame_and_hardware(inventory):
    box = _box(1, 1, 1)
    panel_ids = {row["axis_id"] for row in inventory["fixed_panel_kicker_screws"]}
    frame_ids = {row["axis_id"] for row in inventory["starting_frame_bolts"]}
    target_duties = [
        row
        for row in inventory["legacy_duties"]
        if row["legacy_station_id"] in top.TARGET_DUTY_IDS
    ]
    target_axes = {
        axis["axis_id"] for duty in target_duties for axis in duty["legacy_sds_axes"]
    }
    other_duties = [
        row
        for row in inventory["legacy_duties"]
        if row["legacy_station_id"] not in top.TARGET_DUTY_IDS
    ][:6]
    retained_clips = {
        row["legacy_station_id"]: box for row in [*target_duties, *other_duties]
    }
    other_axes = [
        axis["axis_id"]
        for duty in other_duties
        for axis in duty["legacy_sds_axes"]
    ][:36]
    retained_sds = {axis_id: box for axis_id in target_axes | set(other_axes)}
    roles = ("shaft", "head_washer", "nut_washer", "head", "nut")
    protected = {
        "fixed_66_hillman_axes_63p5mm": {axis_id: box for axis_id in panel_ids},
        "retained_12_frame_bolt_components": {
            f"{axis_id}/{role}": box for axis_id in frame_ids for role in roles
        },
        "retained_12_frame_bolt_tools_withdrawals": {
            f"access/{index}": box for index in range(36)
        },
        "retained_legacy_clips": retained_clips,
        "retained_legacy_sds_axes": retained_sds,
        "tnuts": {f"tnut/{index}": box for index in range(142)},
        "hold_hole_and_provisional_projection": {
            f"hold/{index}": box for index in range(142)
        },
        "lights": {f"light/{index}": box for index in range(132)},
        "wires": {f"wire/{index}": box for index in range(131)},
    }
    frame_records = tuple(
        {"axis_id": axis_id, "installed_component_count": 5} for axis_id in sorted(frame_ids)
    )
    frame_shapes = {
        **{
            f"{axis_id}/installed_component_{index}": box
            for axis_id in frame_ids
            for index in range(1, 6)
        },
        **{f"{axis_id}/source_occupied_axis": box for axis_id in frame_ids},
    }
    candidate_ids = set(top.wj16.EXPECTED_CANDIDATE_AXIS_IDS)
    fake_geometry = SimpleNamespace(
        trial_id=top.wj16.TRIAL_ID,
        layout_id=top.wj16.LAYOUT_ID,
        target_station_ids=tuple(top.wj16.EXPECTED_TARGET_DUTY_IDS),
        fixed_axes={axis_id: box for axis_id in panel_ids},
        frame_bolt_records=frame_records,
        frame_bolt_shapes=frame_shapes,
        protected=protected,
        candidate_bores={axis_id: object() for axis_id in candidate_ids},
        candidate_installed_hardware={
            axis_id: {
                role: box
                for role in (
                    top.BACKER_COMPONENT_ROLES
                    if axis_id in top.BACKER_AXIS_IDS
                    else top.ORDINARY_COMPONENT_ROLES
                )
            }
            for axis_id in candidate_ids
        },
    )

    context = top._context_contract(fake_geometry, inventory)

    assert context["context_variant"] == "wj16"
    assert context["candidate_axis_ids"] == top.wj16.EXPECTED_CANDIDATE_AXIS_IDS
    assert context["counts"]["retained_candidate_axes"] == 72
    assert context["counts"]["retained_candidate_installed_components"] == 360
    assert context["counts"]["frame_installed_components"] == 60
    assert context["counts"]["frame_source_occupied_proxies"] == 12
    assert context["counts"]["target_legacy_clips_excluded_from_obstacles"] == 2
    assert context["counts"]["target_legacy_sds_axes_excluded_from_obstacles"] == 12
    assert context["counts"]["hold_tnuts"] == 142
    assert context["counts"]["lights"] == 132
    assert context["counts"]["wires"] == 131

    missing_axis_geometry = SimpleNamespace(**vars(fake_geometry))
    missing_axis = next(iter(candidate_ids))
    missing_axis_geometry.candidate_bores = {
        axis_id: bore
        for axis_id, bore in fake_geometry.candidate_bores.items()
        if axis_id != missing_axis
    }
    missing_axis_geometry.candidate_installed_hardware = {
        axis_id: roles
        for axis_id, roles in fake_geometry.candidate_installed_hardware.items()
        if axis_id != missing_axis
    }
    with pytest.raises(ValueError, match="exact WJ12/WJ16 contract"):
        top._context_contract(missing_axis_geometry, inventory)

    bad_backer_roles = SimpleNamespace(**vars(fake_geometry))
    backer_axis = next(iter(top.BACKER_AXIS_IDS))
    bad_backer_roles.candidate_installed_hardware = dict(
        fake_geometry.candidate_installed_hardware
    )
    bad_backer_roles.candidate_installed_hardware[backer_axis] = {
        role: box for role in top.ORDINARY_COMPONENT_ROLES
    }
    with pytest.raises(ValueError, match="family schema"):
        top._context_contract(bad_backer_roles, inventory)
