"""Tiny synthetic panel charts; never prepare a real current panel bank."""
import copy
import importlib.util
from pathlib import Path

import numpy as np
import pytest

SPEC = importlib.util.spec_from_file_location("current_off_panel_tested", Path(__file__).with_name("panel_operators.py"))
m = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(m)


@pytest.fixture
def sources():
    screws, features, panels, moved = [], [], [], []
    for index, name in enumerate(m.plate.PANELS):
        prefix = {"main_lower_right": "round_panel_lower_right_center_",
                  "main_upper_right": "round_panel_upper_right_center_",
                  "kicker_right": "round_kicker_right_center_"}.get(name)
        move_count = (2 if name == "kicker_right" else 4) if prefix else 0
        for j in range(11):
            identity = prefix+str(j+1) if j < move_count else name+"/screw/"+str(j)
            screws.append({"axis_id": identity, "panel": name,
                "receiver": "base_post_center_right" if name == "kicker_right" else "base_principal_center_right",
                "origin_xyz_mm": [70.+j, 25.+j, 0.], "direction_xyz": [0., 0., -1.]})
            features.append({"identity": identity, "panel": name, "kind": "conditional_screw_clearance",
                "diameter_mm": 5., "start_xyz_mm": screws[-1]["origin_xyz_mm"].copy(), "direction_xyz": [0., 0., -1.]})
            if j < move_count:
                moved.append(identity)
        panels.append({"id": name, "kind": "panel", "path": "fixture/"+name+".brep",
                       "sha256": str(index)*64, "volume_mm3": 210000.})
    for j in range(274):
        features.append({"identity": "tnut/"+str(j), "panel": m.plate.PANELS[j % 6], "kind": "tnut",
            "diameter_mm": .1, "start_xyz_mm": [10.+j % 30, 60.+j % 20, 0.], "direction_xyz": [0., 0., -1.]})
    prior = {"panel_machining": {"features": features, "outlines": [{"panel": n, "panel_thickness_mm": m.plate.CAT}
        for n in m.plate.PANELS]}, "screw_axes": screws, "finished_panel_solids": panels}
    base = {"screw_axes": copy.deepcopy(screws), "axes": [], "moved_panel_screw_axes": sorted(moved),
            "changed_finished_solids": [{**r, "path": "fixture/current/"+r["id"]+".brep", "sha256": "f"*64}
                for r in panels if r["id"] in m.CHANGED]}
    for row in base["screw_axes"]:
        if row["axis_id"] in moved:
            row["origin_xyz_mm"][0] -= 39.2
    extension = {"parent_geometry": {"base": copy.deepcopy(m.BASE_GEOMETRY)}, "only_two_cleat_bodies_changed": True,
        "changed_finished_solids": [{"id": "eoere_cleat_left"}, {"id": "eoere_cleat_right"}],
        "screw_axes": copy.deepcopy(base["screw_axes"]), "axes": []}
    old_inputs = {"hillman_rows": [{"source_screw_descriptor": r} for r in screws]}
    return prior, base, extension, old_inputs


def current_data(sources):
    prior, base, extension, old = sources
    current, moved = m.compose_panel_metadata(prior, base, extension, old)
    plan = {"scenario": {"panel_intervals": 1}, "limits": []}
    data = {"panel_operator_source_inputs": m.input_record(plan, current, moved), "geometry": copy.deepcopy(m.GEOMETRY),
        "panel_ids": list(m.plate.PANELS), "current_panel_machining_descriptors": current["panel_machining"],
        "hillman_rows": [{"source_screw_descriptor": r} for r in current["screw_axes"]],
        "source_sha256": {"fixture": "1"*64}, "finished_body_observations": [
            {"id": r["id"], "source": r, "volume_mm3": r["volume_mm3"], "center_xyz_mm": [60., 50., 0.]}
            for r in current["finished_panel_solids"]]}
    return plan, prior, current, moved, data


def toy_bank(prior):
    panels = {}
    for name in m.plate.PANELS:
        panel = {"basis": m.plate.SheetBasis(120., 100., 1), "thickness": m.plate.CAT, "twist_scale": 1.,
            "geometry": {"origin": np.zeros(3), "axes": np.eye(3), "inward": np.array([0., 0., -1.]), "front_height": 100.}}
        panel["holes"] = [{**r, "xy_mm": r["start_xyz_mm"][:2]} for r in prior["panel_machining"]["features"] if r["panel"] == name]
        panel["K"] = m.raised.direct_reference_matrix(panel)
        panel.update(contact_w="discard", contact_owner="discard", support_bounds="discard", q="discard")
        panels[name] = panel
    return panels


def test_actual_metadata_three_changed_three_unchanged_without_K(monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError("source-only current check cannot load a real panel bank")
    monkeypatch.setattr(m.raised, "prepare_panel_operators", forbidden)
    monkeypatch.setattr(m.raised.saved, "reuse_panel_operators", forbidden)
    record = m.source_inputs()
    assert record["geometry"] == m.GEOMETRY and record["base_geometry"] == m.BASE_GEOMETRY
    assert len(record["changed_feature_ids"]) == 10 and len(record["screw_axis_ids"]) == 66
    assert set(record["aperture_updated_K_panels"]) == m.CHANGED
    assert len(record["unchanged_K_panels"]) == 3 and record["optional_2026_extra"] is False


@pytest.mark.parametrize("mutation", ["unchanged_source", "wrong_owner", "extra_aperture", "duplicate", "outline", "extension_screw"])
def test_synthetic_source_contract_rejects(sources, mutation):
    prior, base, extension, old = sources
    current, moved = m.compose_panel_metadata(prior, base, extension, old)
    if mutation == "unchanged_source":
        next(r for r in current["finished_panel_solids"] if r["id"] == "main_upper_left")["sha256"] = "f"*64
    elif mutation == "wrong_owner":
        current["screw_axes"][0]["panel"] = "main_upper_left"
    elif mutation == "extra_aperture":
        current["panel_machining"]["features"][-1]["diameter_mm"] += .1
    elif mutation == "duplicate":
        current["panel_machining"]["features"].append(current["panel_machining"]["features"][0])
    elif mutation == "outline":
        current["panel_machining"]["outlines"][0]["panel_thickness_mm"] += 1.
    else:
        extension["screw_axes"][0]["origin_xyz_mm"][0] += 1.
        with pytest.raises(ValueError, match="protected"):
            m.compose_panel_metadata(prior, base, extension, old)
        return
    with pytest.raises(ValueError):
        m.audit_panel_metadata(prior, current, moved)


def test_tiny_six_chart_delta_direct_rigid_work_and_unchanged_K(sources):
    _, prior, current, moved, _ = current_data(sources)
    panels = toy_bank(prior)
    old_K = {n: p["K"].copy() for n, p in panels.items()}
    old_moments = {}
    for n, panel in panels.items():
        xy, area = m.mass.mass_only_quadrature(panel)
        old_moments[n] = area@xy
    rows = m.refresh_bank(panels, current, moved)
    for name, panel in panels.items():
        if name in m.CHANGED:
            assert not np.array_equal(panel["K"], old_K[name])
            direct = m.raised.direct_reference_matrix(panel)
            assert np.max(abs(panel["K"]-direct)) < 2e-10*max(1., float(abs(direct).max()))
        else:
            assert np.array_equal(panel["K"], old_K[name])
        assert not any(k.startswith("contact_") or k in {"q", "support_bounds"} for k in panel)
        rigid = m.mass.rigid_modes(panel, reference=np.zeros(3))
        for i, screw in enumerate(panel["screws"]):
            rows_local = np.vstack([panel[k][i] for k in ("screw_u", "screw_v", "screw_w")])
            point, force = np.asarray(screw["origin_xyz_mm"]), np.array([3., -2., 4.])
            assert rigid.T@rows_local.T@force == pytest.approx(np.r_[force, np.cross(point, force)], abs=1e-10)
        xy, area = m.mass.mass_only_quadrature(panel)
        count = sum(r["axis_id"] in moved for r in panel["screws"])
        assert area@xy-old_moments[name] == pytest.approx([count*39.2*np.pi*2.5**2, 0.], abs=1e-8)
        assert panel["mass_row"].sum() == pytest.approx(1., abs=1e-13)
    assert sum(r["screw_count"] for r in rows) == 66
    assert sum(r["K_route"] == "exact_raised_K" for r in rows) == 3


@pytest.fixture
def synthetic_api(sources, monkeypatch):
    plan, prior, current, moved, data = current_data(sources)
    pins = {"fixture": "1"*64}
    monkeypatch.setattr(m, "read_sources", lambda: (plan, prior, current, moved, pins))
    monkeypatch.setattr(m.raised, "verify", lambda p: None)
    return prior, data, pins


def test_admission_projection_and_missing_observation_before_K(synthetic_api, monkeypatch):
    prior, data, pins = synthetic_api
    def forbidden(*args, **kwargs):
        raise AssertionError("real K must not load in source admission")
    monkeypatch.setattr(m.raised, "prepare_panel_operators", forbidden)
    assert m.verify_panel_source_inputs(data)["metadata_only_no_K_q_or_contact_construction"]
    projected = m.load_projection_inputs(data)
    assert len(projected["finished_stock"]) == 6 and len(projected["screw_axes"]) == 66
    data["finished_body_observations"].pop()
    with pytest.raises(ValueError, match="six current own"):
        m.prepare_panel_operators(data)


@pytest.mark.parametrize("mutation", ["geometry", "source", "volume", "COM", "pins", "aperture", "screw"])
def test_projection_source_rejects(synthetic_api, mutation):
    _, data, _ = synthetic_api
    if mutation == "geometry":
        data["geometry"]["sha256"] = "0"*64
    elif mutation == "source":
        data["finished_body_observations"][0]["source"] = {**data["finished_body_observations"][0]["source"], "sha256": "e"*64}
    elif mutation == "volume":
        data["finished_body_observations"][0]["volume_mm3"] += 1.
    elif mutation == "COM":
        data["finished_body_observations"][0]["center_xyz_mm"][0] = float("nan")
    elif mutation == "pins":
        data["source_sha256"]["fixture"] = "2"*64
    elif mutation == "aperture":
        data["current_panel_machining_descriptors"] = copy.deepcopy(data["current_panel_machining_descriptors"])
        data["current_panel_machining_descriptors"]["features"][0]["diameter_mm"] += 1.
    else:
        data["hillman_rows"] = copy.deepcopy(data["hillman_rows"])
        data["hillman_rows"][0]["source_screw_descriptor"]["origin_xyz_mm"][0] += 1.
    with pytest.raises(ValueError):
        m.load_projection_inputs(data)


def test_runtime_API_only_uses_synthetic_K_and_no_release(synthetic_api, monkeypatch):
    prior, data, pins = synthetic_api
    monkeypatch.setattr(m.raised, "prepare_panel_operators", lambda: (toy_bank(prior), pins, {}))
    panels, projection, returned, proof = m.load_panel_dependencies(data)
    assert len(panels) == len(projection["finished_stock"]) == 6 and returned == pins
    assert m.verify_panel_source_inputs(data, proof)["passed"]
    assert not any(proof["release"].values()) and proof["fresh_contact_extractor_required"]
    data["finished_body_observations"][0]["center_xyz_mm"][0] += 1.
    with pytest.raises(ValueError, match="projection proof"):
        m.verify_panel_source_inputs(data, proof)
    data["finished_body_observations"][0]["center_xyz_mm"][0] -= 1.
    proof["source_inputs"]["optional_2026_extra"] = True
    with pytest.raises(ValueError, match="proof"):
        m.verify_panel_source_inputs(data, proof)


def test_source_pin_and_fresh_output_reject_before_work(tmp_path, monkeypatch):
    with pytest.raises(ValueError, match="source differs"):
        m.raised.verify({str(m.OWN.relative_to(m.ROOT)): "0"*64})
    out = tmp_path/"existing.json"
    out.write_text("preserved")
    def forbidden():
        raise AssertionError("existing output must reject before source preparation")
    monkeypatch.setattr(m, "read_sources", forbidden)
    with pytest.raises(ValueError, match="preserve prior"):
        m.main(["--out", str(out)])
    assert out.read_text() == "preserved"
