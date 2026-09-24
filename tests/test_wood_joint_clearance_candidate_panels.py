from __future__ import annotations

import json
from types import SimpleNamespace

import cadquery as cq
import pytest

from mini_moonboard.floor_flush_width import KERF_RIGHT
from mini_moonboard.wood_joint_panel_machining import RIGHT_PANEL_NAMES
from scripts import wood_joint_clearance as clearance


def _box(x: float) -> cq.Shape:
    return cq.Solid.makeBox(10.0, 10.0, 10.0, cq.Vector(x, 0.0, 0.0))


def test_clearance_report_uses_injected_candidate_panels(monkeypatch, tmp_path):
    inventory = tmp_path / "source-inventory.json"
    inventory.write_text(json.dumps({"source_commit": "test-source"}))
    monkeypatch.setattr(clearance, "SOURCE_INVENTORY", inventory)

    raw_parts = [
        SimpleNamespace(name=name, shape=_box(index * 20.0))
        for index, name in enumerate(sorted(RIGHT_PANEL_NAMES))
    ]
    source = SimpleNamespace(
        option=KERF_RIGHT,
        parts=lambda: pytest.fail("injected map must skip remachining inputs"),
        uncut_wood_parts=lambda: raw_parts,
        panel_connections=lambda: [object() for _ in range(66)],
        connections=list,
    )
    replacements = {
        name: SimpleNamespace(name=name, shape=_box(100.0 + index * 20.0))
        for index, name in enumerate(sorted(RIGHT_PANEL_NAMES))
    }
    binding = SimpleNamespace(
        inventory_sha256="inventory",
        runtime_module_sha256="runtime",
        uncut_part_shapes_sha256="parts",
        uncut_host_shape_sha256="hosts",
        fixed_screw_axes_sha256="screws",
        frame_bolt_axes_sha256="bolts",
    )
    node = SimpleNamespace(source_host_parts={}, source_binding=binding)
    seen_wood = []

    monkeypatch.setattr(
        clearance,
        "candidate_panel_replacements",
        lambda *_args, **_kwargs: pytest.fail("injected map must be reused"),
    )
    monkeypatch.setattr(
        clearance,
        "_wj03_protected_inventory",
        lambda received_source: (
            {
                "counts": {},
                "panel_screw_screen": {},
                "retained_frame_bolt_screen": {},
                "retained_legacy_screen": {},
            }
            if received_source is source
            else pytest.fail("clearance report must keep injected source")
        ),
    )

    def capture_screen(_node, wood, _protected):
        seen_wood.append(wood)
        return {
            "nominal_interference_free": True,
            "named_clearances": {
                "local_n_envelopes_mm": {
                    key: {
                        "n_max_mm": 1.0,
                        "span_mm": 1.0,
                        "rearward_projection_mm": 1.0,
                        "rearward_additional_over_ordinary_mm": 0.0,
                    }
                    for key in (
                        "permanent_body_and_installed_hardware",
                        "body_and_bolt_stroke",
                    )
                }
            },
        }

    monkeypatch.setattr(clearance, "_screen_node", capture_screen)

    report = clearance.build_clearance_report(
        {"left": node}, source=source, panel_replacements=replacements
    )

    assert len(seen_wood) == 1
    for name, replacement in replacements.items():
        assert seen_wood[0][name] is replacement.shape
    assert report["source_inventory"]["fixed_panel_kicker_screws"] == 66


def test_clearance_rejects_empty_or_non_kerf_replacement_maps():
    source = SimpleNamespace(option=KERF_RIGHT)
    with pytest.raises(ValueError, match="exactly the three right panels"):
        clearance._validated_panel_replacements(source, {})

    source.option = "official"
    with pytest.raises(ValueError, match="kerf-right source"):
        clearance._validated_panel_replacements(source, {})

    source.option = KERF_RIGHT
    source.panel_connections = lambda: [object() for _ in range(65)]
    replacements = {
        name: SimpleNamespace(name=name, shape=_box(index * 20.0))
        for index, name in enumerate(sorted(RIGHT_PANEL_NAMES))
    }
    with pytest.raises(ValueError, match="retain all panel axes"):
        clearance._validated_panel_replacements(source, replacements)


def test_clearance_producer_hashes_panel_machining_dependency_closure():
    binding = clearance._producer_binding("test command")

    assert set(binding["dependency_sha256"]) == {
        "scripts/wood_joint_clearance.py",
        "docs/panel-insert-reference.json",
        "mini_moonboard/base_frame.py",
        "mini_moonboard/floor_flush_width.py",
        "mini_moonboard/insert_frame.py",
        "mini_moonboard/panel_grid_v2.py",
        "mini_moonboard/wood_joint_frame.py",
        "mini_moonboard/wood_joint_geometry.py",
        "mini_moonboard/wood_joint_panel_machining.py",
        "scripts/owner_layout_protected.py",
    }
