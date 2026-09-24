from __future__ import annotations

from types import SimpleNamespace

import cadquery as cq

from mini_moonboard.wood_joint_panel_machining import RIGHT_PANEL_NAMES
from scripts import wood_joint_wj05_receiver_audit as receiver_audit
from scripts import wood_joints_wj05_center_backer_transfer_probe as transfer


class _Shape:
    def __init__(self, label: str):
        self.label = label

    def cut(self, other):
        return _Shape(f"{self.label}-cut-{other.label}")

    def clean(self):
        return self

    def translate(self, _vector):
        return _Shape(f"{self.label}-translated")

    def BoundingBox(self):
        return SimpleNamespace(xmin=0.0, ymin=0.0)


def test_transfer_candidate_map_uses_shared_right_panel_replacements(
    monkeypatch,
):
    names = RIGHT_PANEL_NAMES | {
        "base_header",
        "base_post_center_left",
        "base_post_center_right",
        "unchanged_member",
    }
    uncut_parts = [
        SimpleNamespace(name=name, shape=_Shape(f"source-{name}"))
        for name in sorted(names)
    ]
    current_parts = [
        SimpleNamespace(name=name, shape=_Shape(f"current-{name}"))
        for name in sorted(names)
    ]
    axes = tuple(object() for _ in range(66))
    model = SimpleNamespace(
        uncut_wood_parts=lambda: uncut_parts,
        parts=lambda: current_parts,
        panel_connections=lambda: axes,
    )
    raw_by_name = {part.name: part for part in uncut_parts}
    replacement_parts = {
        name: SimpleNamespace(name=name, shape=_Shape(f"candidate-{name}"))
        for name in RIGHT_PANEL_NAMES
    }
    calls = []

    def remachine(received_model, *, current_parts, uncut_parts):
        calls.append((received_model, current_parts, uncut_parts))
        assert len(received_model.panel_connections()) == 66
        return replacement_parts

    monkeypatch.setattr(transfer, "variant", lambda _option: model)
    monkeypatch.setattr(transfer, "candidate_panel_replacements", remachine)
    monkeypatch.setattr(transfer, "_box", lambda _bounds: _Shape("backer"))
    monkeypatch.setattr(
        transfer,
        "cq",
        SimpleNamespace(
            Vector=cq.Vector,
            Solid=SimpleNamespace(
                makeCylinder=lambda *_args, **_kwargs: _Shape("cylinder")
            ),
        ),
    )
    monkeypatch.setattr(
        transfer,
        "seated_koken_3305a_7_16_envelope",
        lambda *_args, **_kwargs: SimpleNamespace(
            approach_endpoint_envelope=_Shape("endpoint"),
            external_envelope=_Shape("seated"),
            approach_sweep_envelope=_Shape("sweep"),
        ),
    )

    _, source_wood, candidate_wood, *_ = transfer._source_and_candidate()

    assert calls == [(model, current_parts, uncut_parts)]
    assert len(model.panel_connections()) == 66
    for name in RIGHT_PANEL_NAMES:
        assert source_wood[name] is raw_by_name[name].shape
        assert candidate_wood[name] is replacement_parts[name].shape
    assert source_wood["base_header"] is raw_by_name["base_header"].shape
    assert candidate_wood["unchanged_member"] is raw_by_name["unchanged_member"].shape


def test_receiver_overlay_changes_only_candidate_finished_panels():
    names = RIGHT_PANEL_NAMES | {"base_header", "main_lower_left"}
    raw_shapes = {name: _Shape(f"raw-{name}") for name in names}
    uncut = dict(raw_shapes)
    finished = dict(raw_shapes)
    candidate_wood = dict(raw_shapes)
    replacements = {
        name: _Shape(f"remachined-{name}") for name in RIGHT_PANEL_NAMES
    }
    candidate_wood.update(replacements)

    receiver_audit._overlay_candidate_panel_shapes(finished, candidate_wood)

    assert all(finished[name] is replacements[name] for name in RIGHT_PANEL_NAMES)
    assert finished["base_header"] is raw_shapes["base_header"]
    assert finished["main_lower_left"] is raw_shapes["main_lower_left"]
    assert all(uncut[name] is raw_shapes[name] for name in names)


def test_backer_and_moved_post_screens_pass_remachined_panels_to_hits(monkeypatch):
    names = RIGHT_PANEL_NAMES | {
        "base_header",
        "base_post_center_left",
        "base_post_center_right",
        "other_source_member",
    }
    source_wood = {name: _Shape(f"raw-{name}") for name in names}
    original_source_wood = dict(source_wood)
    replacements = {
        name: _Shape(f"remachined-{name}") for name in RIGHT_PANEL_NAMES
    }
    candidate_wood = dict(source_wood)
    candidate_wood.update(replacements)
    moved_posts = {
        f"base_post_center_{side}": _Shape(f"moved-post-{side}")
        for side in ("left", "right")
    }
    backers = {"backer": _Shape("backer")}
    seen = []

    def record_hits(shape, obstacles):
        seen.append((shape, dict(obstacles)))
        return {}

    monkeypatch.setattr(transfer, "_hits", record_hits)
    source_obstacles, body_hits, moved_post_hits = (
        transfer._backer_post_obstacle_screens(
            backers,
            moved_posts,
            source_wood,
            candidate_wood,
        )
    )

    assert body_hits == {"backer": {}}
    assert moved_post_hits == {name: {} for name in moved_posts}
    assert len(seen) == 3
    assert seen[0][0] is backers["backer"]
    assert all(
        seen[0][1][name] is replacements[name] for name in RIGHT_PANEL_NAMES
    )
    assert all(
        source_obstacles[name] is replacements[name] for name in RIGHT_PANEL_NAMES
    )
    assert all(
        seen[index][1][name] is replacements[name]
        for index in (1, 2)
        for name in RIGHT_PANEL_NAMES
    )
    assert all(name not in seen[1][1] for name in moved_posts)
    assert all(name in seen[0][1] for name in moved_posts)
    assert seen[0][1]["other_source_member"] is source_wood["other_source_member"]
    assert source_wood == original_source_wood


def test_both_wj05_reports_bind_panel_machining_inputs():
    expected = {
        "mini_moonboard/wood_joint_panel_machining.py",
        "mini_moonboard/base_frame.py",
        "mini_moonboard/floor_flush_width.py",
        "mini_moonboard/insert_frame.py",
        "mini_moonboard/panel_grid.py",
        "mini_moonboard/panel_grid_v2.py",
        "docs/panel-insert-reference.json",
    }

    for producer in (transfer, receiver_audit):
        dependencies = {
            path.relative_to(producer.ROOT).as_posix()
            for path in producer.SOURCE_FILES
        }
        assert expected <= dependencies
