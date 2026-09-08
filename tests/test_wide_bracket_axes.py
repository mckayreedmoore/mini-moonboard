"""Current placements, handedness and grain assumptions are explicit."""
import cadquery as cq
import pytest

from mini_moonboard import box_frame as b
from scripts import wide_bracket_axes as audit


def test_all_brackets_and_screws_have_reversible_axes():
    records = audit.rows()
    assert len(records) == 18
    screws = [s for r in records for s in r["screws"]]
    assert len(screws) == len(set(screws)) == 108
    upper = 0
    for r in records:
        u, v, w = [cq.Vector(*r[k]) for k in ("u_world", "v_world", "bend_axis_world")]
        assert [a.Length for a in (u, v, w)] == pytest.approx([1, 1, 1])
        assert u.dot(v) == pytest.approx(0, abs=1e-12)
        assert (u.cross(v)-w).Length < 1e-12
        force = cq.Vector(137, -219, 411)
        assert (u*force.dot(u)+v*force.dot(v)+w*force.dot(w)-force).Length < 1e-8
        expected = cq.Vector(0, 1, 0) if r["beam_member"] == "base_header" else b.normal()
        assert abs(w.dot(expected)) == pytest.approx(1)
        upper += r["beam_member"] != "base_header"
        for key in ("bend_dot_beam_grain_abs", "bend_dot_upright_grain_abs",
                    "beam_screw_dot_grain_abs", "upright_screw_dot_grain_abs"):
            assert r[key] == pytest.approx(0, abs=1e-12)
        assert [x*25.4 for x in r["origin_world_in"]] == pytest.approx(r["origin_world_mm"])
    assert upper == 12


def test_published_axes_replay():
    assert audit.OUTPUT.read_text() == audit.build()


def test_unknown_grain_fails_closed():
    with pytest.raises(ValueError, match="Unclassified"):
        audit.grain("unknown")
