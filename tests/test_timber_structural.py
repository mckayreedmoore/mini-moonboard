"""Lightweight preparation contracts; no CAD construction or solver launch."""
from dataclasses import dataclass
from types import SimpleNamespace

import pytest

from fea import timber_structural as analysis


@dataclass
class Part:
    name: str
    shape: str


@pytest.mark.parametrize("existing", ["generated", "stability"])
def test_preparation_refuses_existing_evidence_before_geometry(monkeypatch, tmp_path, existing):
    directory, stability = tmp_path/"generated", tmp_path/"stability.json"
    if existing == "generated":
        directory.mkdir()
        evidence = directory/"prior.txt"
    else:
        evidence = stability
    evidence.write_text("unchanged")
    monkeypatch.setattr(analysis, "DIRECTORY", directory)
    monkeypatch.setattr(analysis, "STABILITY", stability)
    monkeypatch.setattr(analysis, "locations", lambda: pytest.fail("Geometry should not be reached"))
    with pytest.raises(FileExistsError, match="Refusing to overwrite"):
        analysis.prepare()
    assert evidence.read_text() == "unchanged"


def test_load_locations_follow_corrected_grid_without_constructing_solids():
    from mini_moonboard import box_frame as b
    from mini_moonboard import product_frame as product

    points = {label: (point, normal) for label, point, normal in analysis.locations()}
    assert len(points) == 142
    origin, tangent = b.point(0, 0, 0), b.point(0, 1, 0)-b.point(0, 0, 0)
    for label, x, s in (("A1", 200., 99.2), ("A6", 200., 1099.2),
                        ("A7", 200., 1319.2), ("K12", 2200., 2319.2)):
        point, normal = points[label]
        assert point == pytest.approx(b.point(x-b.HALF, s, -18.25625).toTuple())
        assert normal == pytest.approx((-b.normal()).toTuple())
        assert sum((p-o)*t for p, o, t in zip(point, origin.toTuple(), tangent.toTuple(), strict=True)) == pytest.approx(s)
    assert points["kicker_1"] == (
        (100.-b.HALF, product.KICKER_BACK_Y_MM+product.FACE_THICKNESS_MM, 150.), (0., 1., 0.))


def test_mass_adapter_classifies_current_clips_as_steel_only_in_temporary_input(monkeypatch):
    originals = [Part("base_side_left", "wood"), Part("clip_timber_top_left_1", "steel")]
    seen = []

    def inspect(parts):
        seen.extend(parts)
        return {"mass": sum(7850 if p.name.startswith("clip_mvp_") else 600 for p in parts)}

    monkeypatch.setattr(analysis.common, "mass_state", inspect)
    assert analysis.mass_state(originals) == {"mass": 8450}
    assert seen[0] is originals[0]
    assert seen[1].shape == originals[1].shape
    assert originals[1].name == "clip_timber_top_left_1"
    assert seen[1].name.startswith("clip_mvp_")


def test_bulk_omits_only_face_bores_preserves_pockets_housings_and_gussets():
    names = ("main_lower_left", "kicker_left", "base_side_left", "base_principal_left",
             "base_rail_mid_lower_left", "timber_bottom_backing", "timber_base_gusset_left")
    raw = [Part(name, "raw-"+name) for name in names]
    service = [Part(name, "service-"+name) for name in names]
    calls = []

    def wood_parts(drilled):
        calls.append(drilled)
        return service if drilled else raw

    frame = SimpleNamespace(wood_parts=wood_parts,
                            parts=lambda *_: pytest.fail("Fastener-drilled assembly must not be used"))
    result = analysis.bulk_parts(frame)
    assert calls == [False, True]
    assert tuple(p.name for p in result) == names
    assert [p.shape for p in result[:2]] == [p.shape for p in raw[:2]]
    assert all(p is old for p, old in zip(result[2:], service[2:], strict=True))
    assert all(p.shape.startswith("service-") for p in service)


@pytest.mark.parametrize("fails", [False, True])
def test_solver_context_is_isolated_and_restored_even_after_failure(monkeypatch, fails):
    saved = analysis.solver.KEY, analysis.solver.DIRECTORY, analysis.solver.LIMITS
    calls = []

    def run(size, modulus):
        calls.append((size, modulus))
        assert (analysis.solver.KEY, analysis.solver.DIRECTORY, analysis.solver.LIMITS) == (
            analysis.KEY, analysis.DIRECTORY, analysis.LIMITS)
        if fails:
            raise RuntimeError("simulated solver failure")

    monkeypatch.setattr(analysis.solver, "run", run)
    if fails:
        with pytest.raises(RuntimeError, match="simulated"):
            analysis.run(40., 6000.)
    else:
        analysis.run(40., 6000.)
    assert calls == [(40., 6000.)]
    assert (analysis.solver.KEY, analysis.solver.DIRECTORY, analysis.solver.LIMITS) == saved
