from __future__ import annotations

import copy
import json
from dataclasses import dataclass, field
from itertools import pairwise
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from scripts import wood_joint_current_geometry as current


def _mock_helpers(events):
    outputs = {}

    def step(name, *, final=False):
        geometry = SimpleNamespace(
            layout_id=current.CURRENT_REVISION_ID if final else f"{name}-geometry"
        )
        report = {
            "revision_id": current.CURRENT_REVISION_ID if final else f"{name}-report"
        }
        outputs[name] = (geometry, report)

        def invoke(*args, **kwargs):
            events.append((name, args, kwargs))
            return outputs[name]

        return invoke

    helpers = SimpleNamespace(
        lower_blocks=SimpleNamespace(
            build_wj24_lower_blocks_below=step("lower")
        ),
        support_up=SimpleNamespace(
            build_wj24_bottom_support_up_one_row=step("raised")
        ),
        above_tnuts=SimpleNamespace(
            build_bottom_support_above_tnuts=step("above")
        ),
        kicker_posts=SimpleNamespace(
            build_kicker_posts_outside_tnuts=step("kicker")
        ),
        center_header=SimpleNamespace(
            build_wj24_center_header_blocks=step("header")
        ),
        inner_frame=SimpleNamespace(
            build_wj24_inner_frame_blocks=step("inner")
        ),
        remove_outer_links=SimpleNamespace(
            REVISION_ID="links-report",
            INPUT_REVISION_ID="inner-report",
            build_wj24_remove_outer_links=step("links"),
        ),
        common_blocks=SimpleNamespace(build_wj24_common_blocks=step("common")),
        second_inner_bolts=SimpleNamespace(
            build_wj24_second_inner_bolts=step("second")
        ),
        bolt_orientation=SimpleNamespace(
            build_wj24_bolt_orientation=step("oriented")
        ),
        led_clearance=SimpleNamespace(build_wj24_led_clearance=step("led")),
        outer_2x6=SimpleNamespace(
            build_wj24_2x6_outer_blocks=step("current", final=True)
        ),
    )
    return helpers, outputs


def _install_mocks(monkeypatch, events):
    helpers, outputs = _mock_helpers(events)
    monkeypatch.setattr(current, "_load_revision_helpers", lambda: helpers)
    audit = {"revision_input": "audited-orientation"}
    monkeypatch.setattr(current, "_load_orientation_audit", lambda: audit)

    def attach_findings(report, **kwargs):
        events.append(("seed_findings", (report,), kwargs))
        report["findings"] = [{"title": "seeded", "detail": "verified"}]
        return {"revision_id": kwargs["expected_revision_id"], "finding_count": 1}

    monkeypatch.setattr(current, "_attach_archived_outer_links_findings", attach_findings)
    return outputs, audit


def test_replays_revision_helpers_in_recorded_order_from_supplied_baseline(monkeypatch):
    events = []
    outputs, audit = _install_mocks(monkeypatch, events)
    baseline = SimpleNamespace(layout_id="historical-wj24")
    progress = Mock()
    compose = Mock(side_effect=AssertionError("provided baseline must be reused"))
    monkeypatch.setattr(current, "_compose_baseline_geometry", compose)

    geometry, report = current.build_current_geometry(baseline, progress=progress)

    event_names = [name for name, _args, _kwargs in events]
    names = [name for name in event_names if name != "seed_findings"]
    assert names == [
        "lower",
        "raised",
        "above",
        "kicker",
        "header",
        "inner",
        "links",
        "common",
        "second",
        "oriented",
        "led",
        "current",
    ]
    by_name = {name: (args, kwargs) for name, args, kwargs in events}
    lower_geometry, lower_report = by_name["raised"][0]
    raised_geometry = by_name["above"][0][2]
    assert by_name["lower"] == ((baseline,), {"progress": progress})
    assert by_name["raised"] == ((lower_geometry, lower_report), {})
    assert by_name["above"][0] == (lower_geometry, lower_report, raised_geometry)
    assert by_name["oriented"][0][2] is audit
    assert event_names.index("seed_findings") == event_names.index("links") + 1
    assert event_names.index("seed_findings") < event_names.index("common")
    for prior_name, next_name in pairwise(names[2:]):
        prior_geometry, prior_report = outputs[prior_name]
        assert by_name[next_name][0][:2] == (prior_geometry, prior_report)
    assert geometry.layout_id == current.CURRENT_REVISION_ID
    assert report["revision_id"] == current.CURRENT_REVISION_ID
    assert report["report_kind"] == "geometry_construction_report"
    assert report["viewer_report_parity"] is False
    assert all(value is False for value in report["release"].values())
    compose.assert_not_called()


def test_omitted_baseline_lazily_calls_the_reconstruction_entrypoint(monkeypatch):
    events = []
    _install_mocks(monkeypatch, events)
    baseline = SimpleNamespace(layout_id="reconstructed-wj24")
    compose = Mock(return_value=baseline)
    monkeypatch.setattr(current, "_compose_baseline_geometry", compose)

    geometry, report = current.build_current_geometry()

    compose.assert_called_once_with()
    assert geometry.layout_id == current.CURRENT_REVISION_ID
    assert report["revision_id"] == current.CURRENT_REVISION_ID
    assert events[0][1][0] is baseline


class _FakeShape:
    def translate(self, _delta):
        return self


@dataclass(frozen=True)
class _FakeBore:
    axis_id: str
    shape: _FakeShape
    receiver_ids: tuple[str, ...]


@dataclass(frozen=True)
class _FakeGeometry:
    layout_id: str
    trial_id: str
    raw_hosts: dict
    finished_hosts: dict
    raw_candidate_parts: dict
    finished_candidate_parts: dict
    candidate_bores: dict
    candidate_installed_hardware: dict
    fixed_axes: dict
    frame_bolt_records: list
    composition_checks: dict = field(default_factory=dict)


def _fake_common_geometry(common_blocks):
    plan = json.loads((common_blocks.STUDY / "pattern-comparison.json").read_bytes())
    candidate_bores = {}
    changed_parts = []
    for fit in plan["fits"]:
        if fit["max_shift_mm"] < 1e-5:
            continue
        changed_parts.append(fit["part"])
        for pair in fit["pairs"]:
            if pair["center_shift_mm"] < 1e-5:
                continue
            axis = pair["target_axis"]
            candidate_bores[axis] = _FakeBore(axis, _FakeShape(), (fit["part"],))
    assert len(changed_parts) == 7
    assert len(candidate_bores) == 24

    candidate_parts = {name: _FakeShape() for name in changed_parts}
    while len(candidate_parts) < 24:
        candidate_parts[f"unaffected_{len(candidate_parts)}"] = _FakeShape()
    while len(candidate_bores) < 90:
        axis = f"unaffected_axis_{len(candidate_bores)}"
        candidate_bores[axis] = _FakeBore(axis, _FakeShape(), ("unaffected",))
    hardware = {
        axis: {role: _FakeShape() for role in ("shaft", "head", "head_washer", "nut_washer", "nut")}
        for axis in candidate_bores
    }
    return _FakeGeometry(
        layout_id=common_blocks.INPUT_REVISION_ID,
        trial_id=common_blocks.INPUT_REVISION_ID,
        raw_hosts={},
        finished_hosts={},
        raw_candidate_parts=candidate_parts,
        finished_candidate_parts=dict(candidate_parts),
        candidate_bores=candidate_bores,
        candidate_installed_hardware=hardware,
        fixed_axes={f"panel_axis_{index}": _FakeShape() for index in range(66)},
        frame_bolt_records=[{"bolt": index} for index in range(12)],
    )


def test_verified_findings_satisfy_actual_common_block_helper_dependency(monkeypatch):
    from scripts import wood_joint_wj24_common_blocks as common_blocks

    monkeypatch.setattr(
        common_blocks,
        "_rebuild_candidate_part",
        lambda _geometry, _part_id, _bores: (_FakeShape(), {"replayed": True}),
    )
    monkeypatch.setattr(
        common_blocks,
        "_rebuild_host",
        lambda _geometry, _host_id, _bores: (_FakeShape(), {"replayed": True}),
    )

    archive = json.loads(current.OUTER_LINKS_REPORT_PATH.read_text())
    prior_report = {
        key: copy.deepcopy(archive[key])
        for key in current._OUTER_LINKS_GEOMETRY_FIELDS
    }
    provenance = current._attach_archived_outer_links_findings(
        prior_report,
        expected_revision_id=common_blocks.INPUT_REVISION_ID,
        expected_input_revision_id=archive["prior_revision_report"]["revision_id"],
    )
    assert provenance["finding_count"] == len(archive["findings"])
    mismatched = copy.deepcopy(prior_report)
    mismatched["host_replay"]["base_header"]["finished_shape_sha256"] = "stale"
    with pytest.raises(RuntimeError, match="not bound to this geometry replay"):
        current._attach_archived_outer_links_findings(
            mismatched,
            expected_revision_id=common_blocks.INPUT_REVISION_ID,
            expected_input_revision_id=archive["prior_revision_report"]["revision_id"],
        )
    geometry = _fake_common_geometry(common_blocks)

    missing_findings = copy.deepcopy(prior_report)
    del missing_findings["findings"]
    with pytest.raises(KeyError, match="findings"):
        common_blocks.build_wj24_common_blocks(geometry, missing_findings)

    revised, report = common_blocks.build_wj24_common_blocks(geometry, prior_report)
    assert revised.layout_id == common_blocks.REVISION_ID
    assert report["findings"][: len(archive["findings"])] == archive["findings"]
    assert len(report["findings"]) == len(archive["findings"]) + 3
