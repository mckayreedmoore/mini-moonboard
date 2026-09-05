import hashlib
import json
import math
from pathlib import Path

import pytest

from fea.user_load_envelope import (
    GRAVITY,
    HISTORICAL_OUTPUT,
    edge_screen,
    envelope,
    hull,
    output_path,
)

SQUARE = [(0, 0), (1000, 0), (1000, 1000), (0, 1000)]


def test_shallow_report_cannot_replace_historical_output(tmp_path):
    assert output_path(["2x8"], None) == HISTORICAL_OUTPUT
    assert output_path(["2x8-shallow"], tmp_path/"new.json") == tmp_path/"new.json"
    alias = tmp_path/"historical.json"
    alias.symlink_to(HISTORICAL_OUTPUT.resolve())
    for target in (None, HISTORICAL_OUTPUT, HISTORICAL_OUTPUT.resolve(), alias):
        with pytest.raises(ValueError,match="separate"):
            output_path(["2x8-shallow"], target)


def test_hull_and_invalid_inputs():
    assert hull(SQUARE+[(500, 500), (0, 0)]) == SQUARE
    with pytest.raises(ValueError):
        hull([(0, 0), (1, 1), (2, 2)])
    with pytest.raises(ValueError):
        edge_screen(SQUARE, (1500, 500), 100, (500, 500, 1000), 100, 0)
    with pytest.raises(ValueError):
        edge_screen(SQUARE, (500, 500), 100, (500, 500, 1000), math.nan, 0)


def test_closed_form_edge_moment_and_tipping():
    rows = edge_screen(SQUARE, (500, 500), 100, (500, 500, 1000), 100, 600)
    assert all(r["dead_restoring_nmm"] == pytest.approx(100*GRAVITY*500) for r in rows)
    assert all(r["live_signed_restoring_nmm"] == -550000 for r in rows)
    assert all(r["factor"] == pytest.approx(100*GRAVITY*500/550000) for r in rows)
    assert all(r["net_restoring_nmm"] < 0 for r in rows)


def test_all_azimuth_envelope_bounds_direction_samples():
    polygon = [(0, 0), (1200, 0), (1000, 1000), (100, 900)]
    args = (polygon, (500, 400), 100, (700, 650, 1900), 1200, 300)
    worst = edge_screen(*args)
    for degrees in range(0, 360, 5):
        angle = math.radians(degrees)
        sampled = edge_screen(*args, direction=(math.cos(angle), math.sin(angle)))
        for bound, sample in zip(worst, sampled, strict=True):
            assert bound["net_restoring_nmm"] <= sample["net_restoring_nmm"]+1e-8
    for row in worst:
        exact = edge_screen(*args, direction=row["horizontal_direction_xy"])[row["edge"]]
        assert exact["net_restoring_nmm"] == pytest.approx(row["net_restoring_nmm"])


def test_translation_invariance_and_vertical_force_inside_polygon():
    before = edge_screen(SQUARE, (500, 500), 100, (700, 650, 1900), 1200, 300)
    after = edge_screen([(x+17, y-93) for x, y in SQUARE], (517, 407), 100,
                        (717, 557, 1900), 1200, 300)
    assert [r["factor"] for r in before] == pytest.approx([r["factor"] for r in after])
    assert all(r["factor"] is None for r in edge_screen(SQUARE, (500, 500), 100,
                                                        (500, 500, 1900), 1200, 0))


def test_envelope_mass_weight_offset_monotonicity_and_count():
    state = {"mass_kg": 100, "centre_xy_mm": (500, 500), "support_polygon_mm": SQUARE}
    rows = envelope(state, [("A12", (500, 1050, 1900), (0, 1, 0))])
    assert len(rows) == 48
    def case(lb=250, scale=1, offset=0):
        return next(r for r in rows if r["climber_lb"] == lb and r["mass_scale"] == scale
                    and r["hold_standoff_mm"] == offset and r["weight_multiplier"] == 1
                    and r["horizontal_n"] == 300)
    base = case()["governing"]["factor"]
    assert case(300)["governing"]["factor"] < base
    assert case(scale=.8)["governing"]["factor"] == pytest.approx(.8*base)
    assert case(offset=100)["governing"]["factor"] < base
    assert case()["downward_n"] == pytest.approx(1112.0554038)


def test_optional_lighter_cases_and_weight_validation():
    state = {"mass_kg": 100, "centre_xy_mm": (500, 500), "support_polygon_mm": SQUARE}
    locations = [("A12", (500, 1050, 1900), (0, 1, 0))]
    rows = envelope(state, locations, (150, 200, 250, 300))
    assert len(rows) == 96
    assert {row["climber_lb"] for row in rows} == {150, 200, 250, 300}
    assert next(row for row in rows if row["climber_lb"] == 150 and row["weight_multiplier"] == 1)["downward_n"] == pytest.approx(667.23324228)
    assert next(row for row in rows if row["climber_lb"] == 200 and row["weight_multiplier"] == 1)["downward_n"] == pytest.approx(889.64432304)
    for weights in ((), (0,), (-150,), (math.nan,), (math.inf,)):
        with pytest.raises(ValueError, match="weight"):
            envelope(state, locations, weights)


def test_published_cases_reproduce_from_frozen_state():
    from fea.user_load_envelope import hold_locations
    record = json.loads(Path("fea/results/hybrid/user_load_envelope.json").read_text())
    assert set(record["candidates"]) == {"2x8", "2x10", "2x12"}
    for path, digest in record["source_sha256"].items():
        if path == "fea/user_load_envelope.py":
            # Historical report at 0499598 predates separate shallow candidates.
            assert digest == "8508f57cb7fbe72ce24fb2f4bd5963d25671c6744882a0dc61205ee480c9c637"
            continue
        assert hashlib.sha256(Path(path).read_bytes()).hexdigest() == digest
    for candidate in record["candidates"].values():
        state = candidate["state"]
        if state["baseline"]:
            assert hashlib.sha256(Path(state["baseline"]["path"]).read_bytes()).hexdigest() == state["baseline"]["sha256"]
        # Normalize tuples to JSON arrays for the durable evidence comparison.
        assert json.loads(json.dumps(envelope(state, hold_locations()))) == candidate["cases"]


def test_separate_candidate_dispatch_preserves_drilling(monkeypatch):
    import sys
    from types import SimpleNamespace

    import mini_moonboard
    from fea.prepare_hybrid_frame import candidate_parts
    sentinel = object()
    calls = []
    def parts(*, drilled):
        calls.append(drilled)
        return sentinel
    module = SimpleNamespace(parts=parts)
    monkeypatch.setitem(sys.modules, "mini_moonboard.shallow_frame", module)
    monkeypatch.setattr(mini_moonboard, "shallow_frame", module, raising=False)
    assert candidate_parts("2x8-shallow", False) is sentinel
    assert candidate_parts("2x8-shallow", True) is sentinel
    assert calls == [False, True]


def test_shallow_published_envelope_is_current_and_reproducible():
    from fea.user_load_envelope import hold_locations
    record = json.loads(Path("fea/results/hybrid/shallow_user_load_envelope.json").read_text())
    assert set(record["candidates"]) == {"2x8-shallow"}
    assert record["climber_weights_lb"] == [150, 200, 250, 300]
    for path, digest in record["source_sha256"].items():
        if path == "fea/prepare_hybrid_frame.py":
            # Frozen dc1659a dispatcher, before separate foot100 candidate.
            assert digest == "06e0b2bde3e6f57fbb56b6737c4e7a9b85006ed86478a6e7aa271b09b25b8ee1"
            continue
        assert hashlib.sha256(Path(path).read_bytes()).hexdigest() == digest
    candidate = record["candidates"]["2x8-shallow"]
    baseline = candidate["state"]["baseline"]
    assert baseline["path"] == "fea/results/hybrid/2x8-shallow/stability.json"
    assert hashlib.sha256(Path(baseline["path"]).read_bytes()).hexdigest() == baseline["sha256"]
    assert len(candidate["cases"]) == 96
    assert json.loads(json.dumps(envelope(candidate["state"], hold_locations(), record["climber_weights_lb"]))) == candidate["cases"]


def test_footprint_candidate_dispatch_preserves_extension_and_drilling(monkeypatch):
    from fea.prepare_hybrid_frame import candidate_parts
    from mini_moonboard import footprint_frame
    calls = []
    sentinel = object()
    def parts(extension, *, drilled):
        calls.append((extension, drilled))
        return sentinel
    monkeypatch.setattr(footprint_frame, "parts", parts)
    assert candidate_parts("2x8-foot100", False) is sentinel
    assert candidate_parts("2x8-foot100", True) is sentinel
    assert calls == [(100, False), (100, True)]
