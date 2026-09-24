from __future__ import annotations

import json
from types import SimpleNamespace

import cadquery as cq

from scripts import wood_joint_wj03_sequence as sequence


def _box(x: float, y: float, z: float) -> cq.Shape:
    return cq.Solid.makeBox(10.0, 12.0, 14.0, cq.Vector(x, y, z))


def test_retained_obstacles_include_wj03_connectors_and_installed_stacks():
    source_shape = _box(0.0, 0.0, 0.0)
    host_shape = _box(1.0, 0.0, 0.0)
    connector_shape = _box(2.0, 0.0, 0.0)
    bolt_shape = _box(3.0, 0.0, 0.0)
    source_part = SimpleNamespace(name="base_header", shape=source_shape)
    source = SimpleNamespace(
        uncut_wood_parts=lambda: [source_part],
        parts=lambda: [source_part],
    )
    node = SimpleNamespace(
        source_host_parts={
            "base_header": SimpleNamespace(finished_shape=host_shape),
        },
        parts={
            "knee_outer_left_spine": SimpleNamespace(finished_shape=connector_shape),
        },
        stacks={
            "knee_outer_left_post_1": SimpleNamespace(
                installed_shapes=lambda: {"shaft": bolt_shape},
            ),
        },
    )
    protected = {
        "solids": {
            "frame_bolts": {},
            "lights": {},
            "wires": {},
            "tnuts": {},
        },
    }

    obstacles = sequence._host_obstacles(
        source,
        {"left": node},
        protected,
        {"fixed_panel_kicker_screws": [], "legacy_duties": []},
    )

    assert obstacles["wood/base_header"] is host_shape
    assert obstacles["connector/knee_outer_left_spine"] is connector_shape
    assert obstacles["wj03_hardware/knee_outer_left_post_1/shaft"] is bolt_shape


def test_wj05_candidate_solids_include_backer_receivers_and_attachment_stacks():
    backer = _box(0.0, 0.0, 0.0)
    center_post = _box(20.0, 0.0, 0.0)
    bolt = _box(40.0, 0.0, 0.0)
    nut = _box(60.0, 0.0, 0.0)
    solids = sequence._wj05_sequence_solids(
        {
            "inner_kicker_backer_left": backer,
            "inner_kicker_backer_right": _box(10.0, 0.0, 0.0),
            "base_post_center_left": center_post,
            "base_post_center_right": _box(30.0, 0.0, 0.0),
        },
        {"backer_header_left_1": bolt},
        {"backer_header_left_1": {"top_nut": nut}},
    )

    assert solids["wood/inner_kicker_backer_left"] is backer
    assert solids["wood/base_post_center_left"] is center_post
    assert solids["wj05_bolt/backer_header_left_1"] is bolt
    assert solids["wj05_hardware/backer_header_left_1/top_nut"] is nut


def test_wj05_backer_is_resolved_as_named_screw_receiver():
    backer = _box(-15.0, -5.0, -5.0)
    solids = sequence._wj05_sequence_solids(
        {
            "inner_kicker_backer_left": backer,
            "inner_kicker_backer_right": _box(20.0, 0.0, 0.0),
            "base_post_center_left": _box(40.0, 0.0, 0.0),
            "base_post_center_right": _box(60.0, 0.0, 0.0),
        },
        {},
        {},
    )
    result = sequence._screw_screen(
        [
            {
                "axis_id": "kicker_left_backer_axis",
                "panel_member": "kicker_left",
                "candidate_finished_receiver_member": "inner_kicker_backer_left",
                "axis_global_xyz": [1.0, 0.0, 0.0],
                "origin_global_xyz_mm": [0.0, 0.0, 0.0],
                "source_occupied_length_mm": 10.0,
                "shop_purchased_length_mm": 25.0,
                "source_occupied_diameter_mm": 6.35,
            }
        ],
        solids,
        "kicker_left",
    )["kicker_left_backer_axis"]

    receiver = result["intended_receiver_path"]
    assert receiver["obstacle_id"] == "wood/inner_kicker_backer_left"
    assert receiver["present"] is True
    assert receiver["shaft_receiver_intersection_volume_mm3"] > 0.0
    assert receiver["engagement_status"] == "not_assessed"


def test_staged_panel_and_attached_tnut_remain_at_translated_pose():
    panel = _box(0.0, 0.0, 0.0)
    tnut = _box(20.0, 30.0, 40.0)
    retained = {"wood/base_header": _box(100.0, 100.0, 100.0)}

    staged_obstacles = sequence._staged_obstacle_map(
        retained,
        "main_lower_left",
        [("panel", panel), ("tnut/hold_tnut_main_A1", tnut)],
        cq.Vector(4.0, -3.0, 2.0),
    )

    assert set(staged_obstacles) == {
        "wood/base_header",
        "staged/main_lower_left/panel",
        "staged/main_lower_left/tnut/hold_tnut_main_A1",
    }
    for original, staged_id in (
        (panel, "staged/main_lower_left/panel"),
        (tnut, "staged/main_lower_left/tnut/hold_tnut_main_A1"),
    ):
        staged = staged_obstacles[staged_id]
        original_box = original.BoundingBox()
        staged_box = staged.BoundingBox()
        assert staged_box.xmin == original_box.xmin + 4.0
        assert staged_box.ymin == original_box.ymin - 3.0
        assert staged_box.zmin == original_box.zmin + 2.0


def test_reverse_paths_keep_correct_panel_and_tnut_assemblies(monkeypatch):
    lower = _box(0.0, 0.0, 0.0)
    kicker = _box(30.0, 30.0, 30.0)
    baseline_post = _box(90.0, 90.0, 90.0)
    shifted_post = _box(100.0, 100.0, 100.0)
    lower_tnut = _box(50.0, 50.0, 50.0)
    kicker_tnut = _box(70.0, 70.0, 70.0)
    source_parts = [
        SimpleNamespace(name="main_lower_left", shape=lower),
        SimpleNamespace(name="kicker_left", shape=kicker),
        SimpleNamespace(name="base_post_center_left", shape=baseline_post),
    ]
    source = SimpleNamespace(
        uncut_wood_parts=lambda: source_parts,
        parts=lambda: source_parts,
    )
    tnut_shapes = {
        "lower_tnut": lower_tnut,
        "kicker_tnut": kicker_tnut,
    }

    def host_obstacles(_source, _nodes, _protected, _inv, excluded=()):
        excluded = set(excluded)
        obstacles = {
            f"wood/{name}": shape
            for name, shape in (
                ("main_lower_left", lower),
                ("kicker_left", kicker),
            )
            if name not in excluded
        }
        obstacles["wood/base_post_center_left"] = baseline_post
        obstacles.update({f"tnut/{name}": shape for name, shape in tnut_shapes.items()})
        return obstacles

    path_calls = []

    def capture_path(members, obstacles, direction, distance, step):
        path_calls.append((members, obstacles, direction, distance, step))
        return {"passes_sampled_nominal_path": True}

    monkeypatch.setattr(sequence, "_fixed_screw_records", lambda _inv, _panel: [])
    monkeypatch.setattr(sequence, "_host_obstacles", host_obstacles)
    monkeypatch.setattr(sequence, "_screw_screen", lambda *_args: {})
    monkeypatch.setattr(sequence, "_path_screen_group", capture_path)
    monkeypatch.setattr(
        sequence,
        "_closest_surface_distance",
        lambda *_args: {"distance_mm": None},
    )

    sequence._panel_clearance_scenario(
        source,
        {},
        {"solids": {"tnuts": tnut_shapes}},
        {"fixed_panel_kicker_screws": []},
        {"lower_tnut": "main_lower_left", "kicker_tnut": "kicker_left"},
        {"wood/base_post_center_left": shifted_post},
        "left",
    )

    assert len(path_calls) == 5
    lower_extraction, kicker_extraction, staged_kicker, kicker_return, lower_return = (
        path_calls
    )

    assert [name for name, _ in lower_extraction[0]] == ["panel", "tnut/lower_tnut"]
    assert "tnut/lower_tnut" not in lower_extraction[1]
    assert "tnut/kicker_tnut" in lower_extraction[1]
    assert lower_extraction[1]["wood/base_post_center_left"] is shifted_post

    assert [name for name, _ in kicker_extraction[0]] == ["panel", "tnut/kicker_tnut"]
    assert "wood/main_lower_left" in kicker_extraction[1]
    assert "tnut/lower_tnut" in kicker_extraction[1]
    assert "tnut/kicker_tnut" not in kicker_extraction[1]

    assert [name for name, _ in staged_kicker[0]] == ["panel", "tnut/kicker_tnut"]
    assert "staged/main_lower_left/panel" in staged_kicker[1]
    assert "staged/main_lower_left/tnut/lower_tnut" in staged_kicker[1]
    assert "wood/main_lower_left" not in staged_kicker[1]
    assert "tnut/lower_tnut" not in staged_kicker[1]

    assert [name for name, _ in kicker_return[0]] == ["panel", "tnut/kicker_tnut"]
    assert kicker_return[2].toTuple() == (0.0, -1.0, 0.0)
    assert (
        kicker_return[0][0][1].BoundingBox().ymin == kicker.BoundingBox().ymin + 100.0
    )
    assert "staged/main_lower_left/tnut/lower_tnut" in kicker_return[1]

    assert [name for name, _ in lower_return[0]] == ["panel", "tnut/lower_tnut"]
    assert lower_return[2].z > 0.0
    assert lower_return[0][1][1].BoundingBox().zmin != lower_tnut.BoundingBox().zmin
    assert "wood/kicker_left" in lower_return[1]
    assert "tnut/kicker_tnut" in lower_return[1]
    assert "tnut/lower_tnut" not in lower_return[1]


def test_report_builds_shared_wj05_candidate_once(monkeypatch, tmp_path):
    input_path = tmp_path / "source-inventory.json"
    input_path.write_text(
        json.dumps(
            {
                "source_runtime_module_hashes_sha256": {},
                "fixed_panel_kicker_screws": [],
            }
        )
    )
    monkeypatch.setattr(sequence, "INPUT", input_path)
    candidate_model = object()
    candidate_wood = {
        "base_post_center_left": _box(0.0, 0.0, 0.0),
        "base_post_center_right": _box(20.0, 0.0, 0.0),
        "inner_kicker_backer_left": _box(40.0, 0.0, 0.0),
        "inner_kicker_backer_right": _box(60.0, 0.0, 0.0),
    }
    candidate_result = (
        candidate_model,
        {},
        candidate_wood,
        {},
        {},
        {},
        {},
        {},
        {},
    )
    # Count shared geometry builds while avoiding the CAD frame and path screens.
    calls = []
    monkeypatch.setattr(
        sequence,
        "build_wj05_center_candidate",
        lambda: calls.append(True) or candidate_result,
    )
    node = SimpleNamespace(
        source_binding=SimpleNamespace(inventory_sha256="source-binding"),
    )
    monkeypatch.setattr(sequence, "build_outer_nodes", lambda: {"left": node})
    monkeypatch.setattr(sequence, "protected_inventory", dict)
    monkeypatch.setattr(sequence.hold_tnuts, "datums", lambda source: [])
    monkeypatch.setattr(
        sequence,
        "_panel_clearance_scenario",
        lambda source, nodes, protected, inv, owners, solids, side: {"side": side},
    )
    monkeypatch.setattr(
        sequence,
        "_short_nut_route",
        lambda nodes, source, protected, inv, solids: {},
    )

    report = sequence.build_report()

    assert calls == [True]
    assert report["authority"]["fixed_panel_kicker_screws"] == 66
    assert report["wj05_retained_geometry"]["members"] == sorted(candidate_wood)
    assert (
        "withdrawal paths are not screened"
        in report["recommended_diagnostic_sequence"][0]
    )
    assert any(
        "removable hold-bolt envelopes" in limitation
        for limitation in report["limitations"]
    )
