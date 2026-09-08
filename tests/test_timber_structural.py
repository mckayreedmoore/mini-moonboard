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
             "base_rail_top", "timber_bottom_backing", "timber_base_gusset_left")
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


@pytest.fixture(scope="module")
def actual_bulk():
    from mini_moonboard import timber_frame as frame

    raw = {p.name: p for p in frame.wood_parts(False)}
    service = {p.name: p for p in frame.wood_parts(True)}
    bulk_values = analysis.bulk_parts(frame)
    bulk = {p.name: p for p in bulk_values}
    assert len(bulk) == len(bulk_values)
    return raw, service, bulk


def test_actual_bulk_inventory_and_volume_preserve_physical_material(actual_bulk):
    raw, service, bulk = actual_bulk
    mid_names = {f"base_rail_mid_{level}_{side}"
                 for level in ("lower", "upper") for side in ("left", "right")}
    assert mid_names <= service.keys()
    assert bulk.keys() == (service.keys()-mid_names) | {"bulk_mid_pair_left", "bulk_mid_pair_right"}
    expected_volume = sum((raw[name] if name.startswith(("main_", "kicker_")) else p).shape.Volume()
                          for name, p in service.items())
    assert sum(p.shape.Volume() for p in bulk.values()) == pytest.approx(expected_volume, rel=0, abs=.01)
    for name in service.keys()-mid_names:
        expected = raw[name] if name.startswith(("main_", "kicker_")) else service[name]
        assert bulk[name].shape.cut(expected.shape).Volume() < 1e-5, name
        assert expected.shape.cut(bulk[name].shape).Volume() < 1e-5, name
    # The physical source remains four independent midpoint pieces.
    assert not any(name.startswith("bulk_mid_pair_") for name in service)


@pytest.mark.parametrize("side", ["left", "right"])
def test_canonical_midpoint_is_exact_pair_union_with_service_pockets(actual_bulk, side):
    import cadquery as cq

    from mini_moonboard import box_frame as b
    from mini_moonboard import panel_grid_v2 as grid

    raw, service, bulk = actual_bulk
    lower = service[f"base_rail_mid_lower_{side}"].shape
    upper = service[f"base_rail_mid_upper_{side}"].shape
    merged = bulk[f"bulk_mid_pair_{side}"].shape
    assert merged.isValid() and len(merged.Solids()) == 1
    assert merged.Volume() == pytest.approx(lower.Volume()+upper.Volume(), rel=0, abs=.01)
    # Directional differences establish material placement, not merely equal
    # volume. Sequential cuts avoid recreating the problematic fused topology.
    assert merged.cut(lower).cut(upper).Volume() < .01
    assert lower.cut(merged).Volume() < .01
    assert upper.cut(merged).Volume() < .01
    raw_volume = sum(raw[f"base_rail_mid_{level}_{side}"].shape.Volume()
                     for level in ("lower", "upper"))
    assert raw_volume-merged.Volume() > 1000., "Service pockets must not be filled"
    bounds = merged.BoundingBox()
    tested = 0
    for label, (x, s) in grid.main_led_datums().items():
        if label.endswith("7") and bounds.xmin < x-b.HALF < bounds.xmax:
            pocket = cq.Solid.makeCylinder(19.99, 44.99, b.point(x-b.HALF, s, 0), b.normal())
            assert merged.intersect(pocket).Volume() < 1e-5, label
            tested += 1
    assert tested == 5
