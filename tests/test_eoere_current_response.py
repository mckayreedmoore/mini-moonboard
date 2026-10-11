"""Portable known answers for current spacer intake; no source bank or solve."""

import copy
import hashlib
import math
from types import SimpleNamespace

import pytest

from scripts import check_eoere_current_inputs as input_checker
from scripts import eoere_current_response as current


def test_separate_spacer_and_shifted_nut_preserve_exact_gravity_wrench():
    direction = [0., 0.6, 0.8]
    axis = {"id": "bolt", "point_xyz_mm": [10., 20., 30.], "direction_xyz": direction,
            "grip_mm": 80., "after_plate_mm": 6.35, "nut_side_spacer_mm": 12.7,
            "hardware_scenario": {"washer_thickness_mm": 2.6416}}
    add = lambda a, b: [x+y for x, y in zip(a, b, strict=True)]
    scale = lambda a, s: [s*x for x in a]
    method = SimpleNamespace(unit=lambda d: d, add=add, scale=scale)
    original_nut_center = add(axis["point_xyz_mm"], scale(direction, 93.))
    original_rows = [{"id": "bolt/nut", "kind": "nut", "mass_kg": 0.007,
                      "volume_mm3": 0.007/7850e-9, "center_of_mass_xyz_mm": original_nut_center}]
    rows = current.spacer_roles(axis, method, {}, lambda *_: copy.deepcopy(original_rows))
    assert len(rows) == 2
    nut, spacer = rows
    assert nut["center_of_mass_xyz_mm"] == pytest.approx(add(original_nut_center, scale(direction, 12.7)))
    # Direct integration of an annulus gives its mass and axial first moment.
    volume = math.pi*((19.05/2)**2-(10.31875/2)**2)*12.7
    center = add(axis["point_xyz_mm"], scale(direction, 80.+6.35+2.6416+6.35))
    assert spacer["volume_mm3"] == pytest.approx(volume)
    assert spacer["mass_kg"] == pytest.approx(volume*7850e-9)
    assert spacer["center_of_mass_xyz_mm"] == pytest.approx(center)
    assert original_rows[0]["center_of_mass_xyz_mm"] == original_nut_center


@pytest.mark.parametrize("length", [0., 12.7])
def test_capture_uses_spacer_outer_face_but_same_receiver_support(length):
    axis = {"nut_side_spacer_mm": length}
    ends = [{"pressure_face_s_mm": -9., "support_s_mm": -6.35},
            {"pressure_face_s_mm": 83., "support_s_mm": 80.}]
    result = current.spacer_ends(axis, None, None, lambda *_: copy.deepcopy(ends))
    assert result[0] == ends[0]
    assert result[1]["pressure_face_s_mm"] == 83.+length
    assert result[1]["support_s_mm"] == 80.
    # Equal/opposite axial force at these collinear faces adds no net couple.
    assert result[1]["pressure_face_s_mm"]-result[1]["support_s_mm"] == pytest.approx(3.+length)


def test_sources_reject_changed_bytes(tmp_path, monkeypatch):
    monkeypatch.setattr(current, "ROOT", tmp_path)
    source = tmp_path / "source.json"
    source.write_text('{"value":1}')
    pinned = current.ref(source)
    source.write_text('{"value":2}')
    with pytest.raises(ValueError, match="source changed"):
        current.read(pinned)


def test_pin_union_rejects_conflicting_history():
    with pytest.raises(ValueError, match="source pin conflict"):
        current.join({"body": "old"}, {"body": "current"})


def test_off_sources_exclude_every_extra_grid_override():
    names = ["base_principal_center_right", "kicker_left", "kicker_right", "base_header"]
    old = {"finished_body_observations": [{"id": n, "source": {"id": n, "sha256": n+"-old"}} for n in names]}
    channels = {"changed_finished_solids": [
        {"id": names[0], "sha256": "base-principal", "variant": "base"},
        {"id": names[0], "sha256": "extra-principal", "variant": "extra"},
        {"id": "base_header", "sha256": "extra-header", "variant": "extra"}]}
    geometry = {"changed_finished_solids": [{"id": n, "sha256": n+"-raised"} for n in names[1:3]]}
    sources = current.selected_sources(old, channels, geometry)
    assert sources[names[0]]["sha256"] == "base-principal"
    assert sources["base_header"]["sha256"] == "base_header-old"
    # Missing the base source cannot be replaced by the optional source.
    channels["changed_finished_solids"].pop(0)
    with pytest.raises(ValueError, match="OFF geometry"):
        current.selected_sources(old, channels, geometry)


def test_spacer_role_cannot_move_to_another_axis_or_disappear():
    selected = {str(i): {"nut_side_spacer_mm": 12.7 if i < 8 else 0.} for i in range(100)}
    roles = ["head", "shaft", "nut", "head_washer", "nut_washer"]
    shafts = [{"axis_id": n, "metal_roles": [{"kind": k} for k in roles+(["spacer"] if v["nut_side_spacer_mm"] else [])]}
              for n, v in selected.items()]
    current.validate_metal_roles(shafts, selected)
    shafts[8]["metal_roles"].append(shafts[0]["metal_roles"].pop())
    with pytest.raises(ValueError, match="per-shaft role census"):
        current.validate_metal_roles(shafts, selected)


def test_loaded_code_cannot_bind_later_edits(tmp_path, monkeypatch):
    source = tmp_path / "adapter.py"
    source.write_text("old code")
    monkeypatch.setattr(current, "ROOT", tmp_path)
    monkeypatch.setattr(current, "OWN", source)
    monkeypatch.setattr(current, "LOADED_SHA", current.sha(source))
    source.write_text("new code")
    with pytest.raises(ValueError, match="loaded response adapter changed"):
        current.ref(source)


def test_loaded_input_checker_cannot_bind_later_edits(tmp_path, monkeypatch):
    source = tmp_path / "checker.py"
    source.write_text("executed code")
    monkeypatch.setattr(current, "ROOT", tmp_path)
    monkeypatch.setattr(input_checker, "OWN", source)
    monkeypatch.setattr(input_checker, "LOADED_SHA", current.sha(source))
    assert input_checker.loaded_source() == {"path": "checker.py", "sha256": current.sha(source)}
    source.write_text("different code")
    with pytest.raises(ValueError, match="loaded input checker changed"):
        input_checker.loaded_source()


def test_factory_compiler_rejects_changed_read_bytes_with_original_hooks(tmp_path, monkeypatch):
    source = tmp_path / "factory.py"
    original = b"def validate_rows(data):\n    assert len(data) == 500\n    row = data[0]\n    assert len(row['metal_roles']) == 5\n    assert data['force'] < 1e-12\n"
    altered = original.replace(b"1e-12", b"1e12")
    factory = SimpleNamespace(__file__=str(source), LOADED_SHA=hashlib.sha256(original).hexdigest())
    monkeypatch.setattr(current.Path, "read_bytes", lambda _: altered)
    with pytest.raises(ValueError, match="exact loaded factory compiler bytes changed"):
        current.compile_validator(factory, current.OWN)


def test_preflight_review_join_includes_exact_raw_input_pin(tmp_path, monkeypatch):
    monkeypatch.setattr(current, "ROOT", tmp_path)
    source = tmp_path / "inputs.json"
    source.write_text('{"loads": []}')
    args = SimpleNamespace(inputs=source, inputs_sha256=current.sha(source))
    pins = current.preflight_pins(args, lambda extra, **_: extra, {"source": "digest"})
    assert pins == {"inputs.json": args.inputs_sha256, "source": "digest"}
    source.write_text('{"loads": [1]}')
    with pytest.raises(ValueError, match="preflight raw input bytes differ"):
        current.preflight_pins(args, lambda extra, **_: extra)


@pytest.mark.parametrize("mutation", ["omit_auxiliary", "shift_auxiliary", "change_auxiliary_force", "extra_load"])
def test_complete_load_inventory_rejects_auxiliary_errors_even_with_rebalanced_totals(mutation):
    owners = [{"id": "wood", "kind": "timber", "center_xyz_mm": [0., 0., 0.], "mass_kg": 2.}]
    auxiliary = [{"id": "screw/share", "owner": "wood", "center_xyz_mm": [1., 0., 0.], "mass_kg": .01}]
    case = {"case_id": "gravity-only", "accessory_placement": "retained-original-top-hold",
            "primary_load_basis": True, "hold": None,
            "loads": [{"id": "self-weight/wood", "body": "wood", "point_xyz_mm": [0., 0., 0.],
                       "force_xyz_n": [0., 0., -19.6133]},
                      {"id": "bolt-weight/screw/share", "body": "wood", "point_xyz_mm": [1., 0., 0.],
                       "force_xyz_n": [0., 0., -.0980665]}]}
    source_case = copy.deepcopy(case)
    input_checker.verify_load_inventory(case, owners, [], auxiliary, source_case)
    if mutation == "omit_auxiliary":
        case["loads"].pop()
    elif mutation == "shift_auxiliary":
        case["loads"][1]["point_xyz_mm"][0] += 1.
    elif mutation == "change_auxiliary_force":
        # Preserve the total force exactly by moving the omitted action to wood.
        case["loads"][0]["force_xyz_n"][2] -= .05
        case["loads"][1]["force_xyz_n"][2] += .05
    else:
        case["loads"].append({"id": "extra", "body": "wood", "point_xyz_mm": [0., 0., 0.],
                              "force_xyz_n": [0., 0., 0.]})
    with pytest.raises(ValueError):
        input_checker.verify_load_inventory(case, owners, [], auxiliary, source_case)


def source_fixture(monkeypatch):
    geometry = {"path": "geometry", "sha256": "g"}
    hardware = {"path": "hardware", "sha256": "h"}
    source_manifest = {"path": "manifest", "sha256": "m"}
    export_ref = {"path": "export", "sha256": "e"}
    releases = {"structural_released": False}
    config = {"references": {"geometry": geometry, "hardware": hardware, "prior_export": "prior"}, "release": releases}
    exported = {"schema": current.EXPORT_SCHEMA, "hardware_model": hardware, "geometry": geometry,
                "manifest": source_manifest, "source_pins_before_after_unchanged": True,
                "native_cached_solid_queries_performed": True, "fresh_contact_domains_not_copied_from_old_field": True,
                "native_nominal_flat_reference_flange_masks_created": 88,
                "candidate_CAD_rebuild_mesh_K_assembly_factorization_q_forces_load_cases_or_native_solve_performed": False,
                "release": releases, "material_scenario": {}, "source_sha256": {"body": "b"},
                "physical_owner_gravity_rows": [{"id": "panel", "kind": "panel"}],
                "all_factory_holes": [{"angle_id": "angle", "holes": [{"installed_bolt_axis_id": "bolt"}]}],
                "floor_observations": [{"host": "foot", "observed_normal_reference_points_xyz_mm": [[0., 0., 0.]]}],
                "parameters": {}}
    for key in ("raw_gross_timber_rows", "fitting_ports", "fitting_poses", "shafts", "finished_receiver_wall_queries",
                "finished_body_observations", "direct_contacts", "hillman_rows", "current_panel_machining_descriptors",
                "flange_domains", "flange_shared_face_patches", "timber_and_panel_shared_face_patches", "shared_pair_query_census"):
        exported[key] = []
    data = {"schema": current.INPUT_SCHEMA, "optional_2026_extra": False, "release": releases,
            "geometry": {"report": geometry, "source_manifest": source_manifest, "cached_source_export": export_ref},
            **{k: copy.deepcopy(v) for k, v in exported.items() if k in ("parameters", "physical_owner_gravity_rows",
                "all_factory_holes", "fitting_poses", "shafts", "finished_receiver_wall_queries", "finished_body_observations",
                "direct_contacts", "hillman_rows", "current_panel_machining_descriptors", "flange_domains",
                "flange_shared_face_patches", "timber_and_panel_shared_face_patches", "shared_pair_query_census")},
            "timber_rows": [], "fitting_port_bindings": [], "base_bodies": [{"id": "panel", "kind": "panel"}],
            "panel_ids": ["panel"], "factory_holes": [{"installed_bolt_axis_id": "bolt", "angle_id": "angle", "used": True}],
            "scenario": {}, "floor_footprints": {"foot": [[0., 0., 0.]]},
            "source_sha256": {"body": "b", "geometry": "g", "manifest": "m", "export": "e"}}
    monkeypatch.setattr(current, "manifest", lambda: config)
    monkeypatch.setattr(current, "ref", lambda _: source_manifest)
    monkeypatch.setattr(current, "read", lambda r: {"material_scenario": {}} if r == "prior" else exported)
    monkeypatch.setattr(current, "verify", lambda p: p)
    return data, exported


@pytest.mark.parametrize("field,value", [
    ("geometry", {"path": "foreign", "sha256": "foreign"}),
    ("manifest", {"path": "foreign", "sha256": "foreign"}),
    ("source_pins_before_after_unchanged", False), ("native_cached_solid_queries_performed", False),
    ("fresh_contact_domains_not_copied_from_old_field", False),
    ("native_nominal_flat_reference_flange_masks_created", 87),
    ("candidate_CAD_rebuild_mesh_K_assembly_factorization_q_forces_load_cases_or_native_solve_performed", True),
])
def test_source_contract_rejects_each_foreign_or_unverified_export(monkeypatch, field, value):
    data, exported = source_fixture(monkeypatch)
    current.require_current_sources(data)
    exported[field] = value
    with pytest.raises(ValueError, match="current own selected-hardware export"):
        current.require_current_sources(data)


@pytest.mark.parametrize("change", ["missing_export_pin", "wrong_hole", "wrong_panel"])
def test_source_contract_rejects_omitted_reference_and_same_count_substitutions(monkeypatch, change):
    data, _ = source_fixture(monkeypatch)
    current.require_current_sources(data)
    if change == "missing_export_pin":
        del data["source_sha256"]["export"]
    elif change == "wrong_hole":
        data["factory_holes"][0]["installed_bolt_axis_id"] = "other"
    else:
        data["panel_ids"] = ["other"]
    with pytest.raises(ValueError):
        current.require_current_sources(data)


def test_output_refuses_overwrite_and_dangling_symlink(tmp_path, monkeypatch):
    monkeypatch.setattr(current, "RAW", tmp_path)
    target = tmp_path / "receipt.json"
    target.write_text("preserved")
    with pytest.raises(FileExistsError):
        current.write(target, {})
    assert target.read_text() == "preserved"
    link = tmp_path / "link.json"
    link.symlink_to(tmp_path / "absent.json")
    # resolve() follows links; reject every occupied final pathname explicitly.
    with pytest.raises((ValueError, FileExistsError)):
        current.write(link, {})
    assert not (tmp_path / "absent.json").exists()
