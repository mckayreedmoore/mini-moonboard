"""Small genuine integration only; successor/native preparation is prohibited."""
import copy
import importlib.util
from pathlib import Path

import numpy as np
import pytest

from scripts import thin_bolted_panel_mechanics as panel

PATH = Path(__file__).with_name("first_order_factory.py")
SPEC = importlib.util.spec_from_file_location("eoere_first_order_factory_fixtures", PATH)
method = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(method)


def toy():
    members = [{"name": name, "start": [0., y, 0.], "end": [100., y, 0.], "axis": [1., 0., 0.],
                "section_u": [0., 1., 0.], "section_v": [0., 0., 1.], "width_mm": 40., "depth_mm": 100.}
               for name, y in (("wood-a", 0.), ("wood-b", -40.))]
    bodies = [{"id": row["name"], "kind": "timber", "mass_kg": 1., "center_xyz_mm": [50., row["start"][1], 0.]}
              for row in members]
    bodies += [{"id": "toy-fitting", "kind": "fitting", "mass_kg": 1., "center_xyz_mm": [18., 3., 21.]},
               {"id": "main_lower_left", "kind": "panel", "mass_kg": 1., "center_xyz_mm": [50., 50., 0.]}]
    role = {"id": "toy-bolt", "volume_mm3": 1000., "center_of_mass_xyz_mm": [65.0875, -10., -25.4]}
    shaft = {"axis_id": "toy-axis", "body": "toy-shaft", "point": [65.0875, 0., -25.4],
             "basis": [[0., -1., 0.], [1., 0., 0.], [0., 0., 1.]], "diameter_mm": 9.525,
             "bore_diameter_mm": 10.31875, "shaft_interval_mm": [-10., 25.], "metal_roles": [role],
             "surfaces": [{"kind": "steel", "host": "toy-fitting", "interval_mm": [-6.35, 0.], "bore_diameter_mm": 10.,
                           "flange": "arm-x/far-plus", "entry_xyz_mm": [65.0875, 0., -25.4], "receiver": "wood-a"},
                          {"kind": "wood", "host": "wood-a", "interval_mm": [0., 20.], "bore_diameter_mm": 10.31875,
                           "grain_axis_xyz": [1., 0., 0.]}],
             "ends": [{"end": "head", "host": "toy-fitting", "flange": "arm-x/far-plus", "support_s_mm": -6.35,
                       "pressure_face_s_mm": -8., "direction_on_shaft_xyz": [0., -1., 0.]},
                      {"end": "nut", "host": "wood-a", "support_s_mm": 20., "pressure_face_s_mm": 22.,
                       "direction_on_shaft_xyz": [0., 1., 0.]}]}
    loads = [{"id": "self-weight/"+row["id"], "body": row["id"], "point_xyz_mm": row["center_xyz_mm"],
              "force_xyz_n": [0., 0., -row["mass_kg"]*method.frame.GRAVITY]} for row in bodies]
    loads.append({"id": "physical-bolt-metal/toy-bolt", "body": "toy-shaft", "point_xyz_mm": role["center_of_mass_xyz_mm"],
                  "force_xyz_n": [0., 0., -role["volume_mm3"]*7850e-9*method.frame.GRAVITY]})
    data = {"schema": method.SCHEMA, "timber_rows": members, "base_bodies": bodies, "shafts": [shaft],
            "panel_ids": ["main_lower_left"], "fitting_poses": [{"id": "toy-fitting", "origin_xyz_mm": [0., 0., 0.],
                "u_xyz": [1., 0., 0.], "v_xyz": [0., 1., 0.], "w_xyz": [0., 0., 1.]}],
            "case": {"case_id": "gravity-only", "accessory_placement": "retained-original-top-hold",
                     "primary_load_basis": True, "loads": loads},
            "hillman_rows": [{"id": "toy-Hillman", "first": "main_lower_left", "second": "wood-a", "point_xyz_mm": [50., 20., 0.],
                "basis": [[0., 0., 1.], [1., 0., 0.], [0., 1., 0.]], "ka": 1000., "kl": 1000., "clearance": 0., "tension_only": True}],
            "direct_contacts": [{"id": "toy-wood-contact", "kind": "timber_face_contact", "first": "wood-a", "second": "wood-b",
                "point_xyz_mm": [50., -20., 0.], "direction_xyz": [0., 1., 0.], "stiffness": 200.},
                {"id": "toy-panel-contact", "kind": "panel_contact", "first": "main_lower_left", "second": "wood-a",
                 "point_xyz_mm": [50., 20., -9.128125], "direction_xyz": [0., 0., 1.], "stiffness": 100.}],
            "floor_footprints": {"wood-a": [[0., -20., 0.], [100., -20., 0.], [100., 20., 0.], [0., 20., 0.]]},
            "scenario": {"timber_stiffness_basis": "declared-gross-stock-Timoshenko", "fitting_gravity_route": method.guarded.ROUTE,
                "beam_size_mm": 150., "timber_e_mpa": 11031.612, "timber_shear_ratio": .064,
                "metal_density_kg_mm3": 7850e-9, "floor_kn_n_mm": 25000., "floor_kt_n_mm": 100000.,
                "floor_activation_threshold_n": 1e-7, "common_shaft_parameters": {}}}
    basis = panel.SheetBasis(100., 100., 1)
    xy, areas = basis.quadrature()
    p = {"basis": basis, "geometry": {"name": "main_lower_left", "origin": np.zeros(3), "axes": np.eye(3),
        "inward": np.array([0., 0., -1.])}, "thickness": 18.25625,
         "K": panel.plate_matrix(basis, xy, areas), "mass_row": areas @ basis.values(xy)/sum(areas)}
    integrated = {"finished_stock": [{"name": "main_lower_left", "volume_mm3": 2e6, "center_of_mass_xyz_mm": [50., 50., 0.]}],
        "panel_machining": {"features": [{"identity": "hold_tnut_main_"+name, "panel": "main_lower_left",
            "start_xyz_mm": [50., 50., 0.]} for name in ("A12", "A1", "K12")]}}
    return data, {"main_lower_left": p}, integrated


def test_genuine_timber_panel_four_port_common_shaft_once_and_full_rigid_wrench():
    data, panels, integrated = toy()
    prepared = method.prepare_synthetic(data, panels, integrated)
    assert prepared.synthetic_only and prepared.counts["physical_bodies"] == 5
    assert len(prepared.assembly.fittings) == 0 and len(prepared.fittings) == 1
    assert prepared.counts["bearings"] == 4 and prepared.counts["end_captures"] == 2
    assert prepared.counts["floor_normals"] == 4 and prepared.counts["floor_xy_components"] == 2
    assert np.max(abs(np.asarray(prepared.applied_wrench_work_error_n_nmm))) < 1e-8
    rigid = prepared.assembly.rigid_modes()*1e-6
    assert np.max(abs(prepared.assembly.K @ rigid)) < 1e-7
    for group in prepared.groups:
        assert np.max(abs(group["B"] @ rigid)) < 1e-12
    for contact in prepared.contacts:
        if contact["kind"] != "floor_normal":
            assert np.max(abs(contact["B"] @ rigid)) < 1e-12


def test_fresh_k_geometry_and_inputs_not_mutated_or_old_fitting_nodes_added():
    data, panels, integrated = toy()
    before = copy.deepcopy(data)
    p = method.prepare_synthetic(data, panels, integrated)
    assert data == before
    el = p.fittings["toy-fitting"]
    assert len(el.indices) == 24
    assert p.system.shafts["toy-shaft"]["offset"] > max(el.indices)
    assert len(p.system.shafts) == 1
    assert all(row["kind"] not in {"fitting_bolt", "retained_bolt"} for row in p.groups)
    steel = [row for row in p.system.bearing_groups if row["surface"]["kind"] == "steel"]
    wood = [row for row in p.system.bearing_groups if row["surface"]["kind"] == "wood"]
    assert all(row["clearance"] == pytest.approx(.2375, abs=1e-14) for row in steel)
    assert all(row["clearance"] == pytest.approx(.396875, abs=1e-14) for row in wood)


@pytest.mark.parametrize("mutation", ["history", "duplicate-axis", "duplicate-load", "missing-role", "floor-law", "old-stock-basis"])
def test_changed_source_contract_mutations_reject_before_assembly(mutation, monkeypatch):
    data, panels, integrated = toy()
    if mutation == "history":
        data["historical_q"] = [1.]
    elif mutation == "duplicate-axis":
        data["shafts"].append(copy.deepcopy(data["shafts"][0]))
    elif mutation == "duplicate-load":
        data["case"]["loads"].append(copy.deepcopy(data["case"]["loads"][0]))
    elif mutation == "missing-role":
        data["case"]["loads"].pop()
    elif mutation == "floor-law":
        data["scenario"]["floor_activation_threshold_n"] = .001
    else:
        data["scenario"]["timber_stiffness_basis"] = "old-profile"
    monkeypatch.setattr(method.frame, "ElasticAssembly", lambda *a, **k: pytest.fail("invalid rows reached assembly"))
    with pytest.raises(ValueError):
        method.prepare_synthetic(data, panels, integrated)


def test_toy_escape_cannot_prepare_production_or_missing_dependencies():
    data, panels, integrated = toy()
    with pytest.raises(ValueError, match="150-body"):
        method.prepare(data, panels, integrated, source_sha256=method.source_pins())
    data["missing_dependencies"] = ["current receiver bank"]
    with pytest.raises(ValueError, match="complete successor"):
        method.prepare_synthetic(data, panels, integrated)


def test_reference_area_priors_preserve_total_and_reject_old_corner_or_swapped_bedding():
    rows = [{"kind": "flange_contact", "reference_area_mm2": area,
             "nominal_full_holed_flange_area_mm2": 100., "stiffness": 40000.*area/100.}
            for area in (20., 30., 50.)]
    rows += [{"kind": "timber_face_contact", "reference_area_mm2": 7., "bedding_n_mm3": 1., "stiffness": 7.},
             {"kind": "panel_contact", "reference_area_mm2": 11., "bedding_n_mm3": 2., "stiffness": 22.}]
    method.validate_contact_coefficients(rows)
    assert sum(row["stiffness"] for row in rows[:3]) == 40000.
    clipped = copy.deepcopy(rows[:2])
    method.validate_contact_coefficients(clipped)
    assert sum(row["stiffness"] for row in clipped) == 20000.
    bad = copy.deepcopy(rows)
    bad[0]["stiffness"] = 10000.
    with pytest.raises(ValueError, match="area-weighted"):
        method.validate_contact_coefficients(bad)
    bad = copy.deepcopy(rows)
    bad[-1]["bedding_n_mm3"] = 1.
    with pytest.raises(ValueError, match="timber1/panel2"):
        method.validate_contact_coefficients(bad)
