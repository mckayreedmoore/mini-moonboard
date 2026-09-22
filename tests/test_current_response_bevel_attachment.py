"""Analysis-only endpoint coverage for the integrated barrel principal bevel."""

import numpy as np
import pytest

from fea.current_response_model import gross_member_record
from fea.horizontal_frame_members import axes
from fea.horizontal_panel_frame import Structure
from scripts.owner_barrel_native_preparation import IntegratedBarrelNative


@pytest.fixture(scope="module")
def principal():
    module = IntegratedBarrelNative()
    part = next(part for part in module.uncut_wood_parts()
                if part.name == "base_principal_center_left")
    grain, section_u = module.MEMBER_AXES.get(part.name) or axes(module, part.name)
    return module, part, grain, section_u


def test_default_principal_record_still_starts_at_cut_face_centroid(principal):
    _, part, grain, section_u = principal
    record = gross_member_record(part, grain, section_u)
    point = np.array([-70., -159.505377, 277.])

    np.testing.assert_allclose(record["start"], [-70., -132.68003036784785, 277.], atol=1.e-6)
    assert np.dot(point - record["start"], record["axis"]) == pytest.approx(
        -17.24300044, abs=1.e-5)
    assert "bevel_projection" not in record


def test_full_bevel_projection_covers_actual_barrel_face_point(principal):
    _, part, grain, section_u = principal
    baseline = gross_member_record(part, grain, section_u)
    record = gross_member_record(part, grain, section_u, full_bevel_projection=True)
    point = np.array([-70., -159.505377, 277.])
    bottom = [vertex.Center().dot(grain) for vertex in part.shape.Vertices()
              if abs(vertex.Center().z - part.shape.BoundingBox().zmin) < 1.e-6]

    assert np.dot(record["start"], record["axis"]) == pytest.approx(min(bottom))
    assert np.dot(point - record["start"], record["axis"]) > 0.
    assert record["end"] == baseline["end"]
    assert record["verification_grain_interval_mm"] == baseline["verification_grain_interval_mm"]
    assert record["bevel_projection"]["start_extension_mm"] == pytest.approx(
        32.152216716, abs=1.e-6)
    assert "partial bevel" in record["bevel_projection"]["limitation"]
    assert record["qualified_for_design"] is False

    structure = Structure()
    structure.member(record, [point], size=150.)
    assert structure.nodes[structure.attachment(part.name, point)] == pytest.approx(point)


def test_prepare_reads_member_opt_in_from_module(principal, monkeypatch):
    from fea import current_response_model as model

    module, part, _, _ = principal
    monkeypatch.setattr(module, "FULL_BEVEL_PROJECTION_MEMBERS", (part.name,), raising=False)
    monkeypatch.setattr(model, "mass_by_body", lambda *_: ({}, []))

    class ReachedRecord(Exception):
        pass

    original = model.gross_member_record

    def inspect(candidate, *args, **kwargs):
        if candidate.name == part.name:
            assert kwargs["full_bevel_projection"] is True
            raise ReachedRecord
        return original(candidate, *args, **kwargs)

    monkeypatch.setattr(model, "gross_member_record", inspect)
    with pytest.raises(ReachedRecord):
        model.prepare(module, materials={}, stiffnesses={}, expected_candidate=module.KEY)
