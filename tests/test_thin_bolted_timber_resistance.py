"""Known-answer and fail-closed checks for the thin timber resistance adapter."""

from __future__ import annotations

import copy
import json
import math

import pytest

from scripts import thin_bolted_timber_resistance as timber


def test_signed_force_selects_opposite_loaded_ends_and_oblique_angle():
    first = timber.resolved_action([3., 4., 5.], [1., 0., 0.], [0., 0., 1.])
    reverse = timber.resolved_action([-3., -4., -5.], [1., 0., 0.], [0., 0., 1.])
    assert first["lateral_n"] == pytest.approx(5.)
    assert first["axial_signed_n"] == 5.
    assert first["load_to_grain_degrees"] == pytest.approx(math.degrees(math.atan2(4., 3.)))
    assert first["grain_loaded_end"] == "positive"
    assert reverse["grain_loaded_end"] == "negative"
    assert first["cross_grain_loaded_edge"] != reverse["cross_grain_loaded_edge"]
    assert first["oblique_lateral_action"] is True


def test_zero_lateral_and_end_grain_refuse_inapplicable_angle():
    pure_tie = timber.resolved_action([0., 0., 10.], [1., 0., 0.], [0., 0., 1.])
    assert pure_tie["load_to_grain_degrees"] is None
    assert pure_tie["grain_loaded_end"] is None
    with pytest.raises(ValueError, match="end-grain"):
        timber.resolved_action([0., 3., 0.], [1., 0., 0.], [1., 0., 0.])


def test_nds_end_factor_lower_bound_is_not_clamped_to_a_pass():
    below = timber.end_geometry_factor(3.4 * 12.7, 12.7, "softwood_parallel_tension")
    minimum = timber.end_geometry_factor(3.5 * 12.7, 12.7, "softwood_parallel_tension")
    full = timber.end_geometry_factor(7. * 12.7, 12.7, "softwood_parallel_tension")
    assert below["end_factor_only"] is None
    assert below["status"] == "below_minimum"
    assert minimum["end_factor_only"] == pytest.approx(.5)
    assert full["end_factor_only"] == 1.
    assert full["complete_geometry_factor"] is None


def test_reference_uses_all_six_modes_and_explicit_root_scenario():
    axis = {"attachments": [{}], "diameter_mm": 12.7, "grip_mm": 38.1,
            "before_plate_mm": 5.55625, "after_plate_mm": 0.}
    action = timber.resolved_action([100., 0., 0.], [1., 0., 0.], [0., 0., 1.])
    # These artificial material values exercise equations, not the Eaton product.
    scenario = {"scenario_id": "method_test_only", "source": "test input, not actual material",
                "steel_Fe_psi": 87000., "bolt_Fyb_psi": 45000.,
                "full_body_diameter_in": .5, "thread_root_diameter_in": .4,
                "wood_thread_bearing_length_in": 0., "steel_thread_bearing_length_in": 0.}
    body = timber.single_shear_reference(axis, action, scenario)
    assert set(body["mode_values_n"]) == {"Im", "Is", "II", "IIIm", "IIIs", "IV"}
    assert body["mode_values_n"]["Im"] == pytest.approx(.5 * 1.5 * 5600. / 4 * timber.N_PER_LBF)
    assert body["single_fastener_reference_n"] == min(body["mode_values_n"].values())
    root_input = dict(scenario, wood_thread_bearing_length_in=1.5)
    root = timber.single_shear_reference(axis, action, root_input)
    assert root["effective_diameter_in"] == .4
    assert root["single_fastener_reference_n"] < body["single_fastener_reference_n"]
    assert root["adjusted_joint_resistance_n"] is None
    assert root["joint_utilization"] is None


def test_shared_shaft_cannot_be_two_single_shear_ratings():
    action = timber.resolved_action([1., 0., 0.], [1., 0., 0.], [0., 0., 1.])
    actual = timber.single_shear_reference({"attachments": [{}, {}]}, action, None)
    assert actual["status"] == "unavailable_for_this_topology"
    assert actual["resistance_n"] is None
    assert actual["symmetric_double_shear_assumed"] is False


def test_material_absence_produces_categorical_missing_inputs():
    action = timber.resolved_action([1., 0., 0.], [1., 0., 0.], [0., 0., 1.])
    actual = timber.single_shear_reference({"attachments": [{}]}, action, None)
    assert actual["status"] == "material_inputs_unavailable"
    assert "bolt_Fyb_psi" in actual["missing"]
    assert actual["resistance_n"] is None


def test_frozen_census_and_wood_vs_steel_washer_paths():
    layout, _, raw, _ = timber.source_inputs()
    rows = timber.geometry_rows(layout)
    assert len(rows) == 70
    assert sum(r["metal_side_pattern"] == "single_steel_side" for r in rows) == 44
    assert sum(r["metal_side_pattern"] == "two_steel_sides_actions_not_assumed_symmetric" for r in rows) == 14
    refs = timber.geometry_references(layout, raw)
    assert len(refs) == 58
    assert all(r["actual_finished_net_section_reference_n"] is None for r in refs)
    washers = timber.washer_rows(layout)
    assert len(washers) == 140
    for washer in washers:
        assert (washer["ideal_full_contact_wood_annulus_reference_n"] is not None) == (washer["support_material"] == "wood")
        assert washer["complete_axial_resistance_n"] is None


def test_foreign_or_duplicate_attachment_force_is_rejected():
    layout, _, _, _ = timber.source_inputs()
    axis = layout["installed_axes"][0]
    attachment = axis["attachments"][0]
    source = {"candidate": timber.CANDIDATE, "layout_sha256": timber.LAYOUT_SHA, "state_id": "method_fixture_only",
              "attachment_actions": [{"case_id": "test-witness", "axis_id": axis["id"],
                  "angle_id": attachment["angle_id"], "flange": attachment["flange"],
                  "receiver": attachment["receiver"], "point_xyz_mm": attachment["entry_xyz_mm"],
                  "force_on_receiver_xyz_n": [100., 0., 0.],
                  "moment_on_receiver_at_point_xyz_nmm": [0., 0., 0.]}]}
    checked = timber.compare_actions(layout, source)
    assert len(checked) == 1 and checked[0]["compatible_force_field_accepted"] is False
    duplicate = copy.deepcopy(source)
    duplicate["attachment_actions"].append(duplicate["attachment_actions"][0])
    with pytest.raises(ValueError, match="duplicate"):
        timber.compare_actions(layout, duplicate)
    foreign = copy.deepcopy(source)
    foreign["attachment_actions"][0]["receiver"] = "foreign_member"
    with pytest.raises(ValueError, match="foreign flange/member"):
        timber.compare_actions(layout, foreign)
    changed = dict(source, layout_sha256="0" * 64)
    with pytest.raises(ValueError, match="independently bound"):
        timber.compare_actions(layout, changed)
    separate = copy.deepcopy(source)
    separate["attachment_actions"][0]["state_id"] = "first_state"
    separate["attachment_actions"].append(dict(separate["attachment_actions"][0], state_id="second_state"))
    assert len(timber.compare_actions(layout, separate)) == 2


def test_finished_section_and_first_cut_boundary_known_answer(tmp_path, monkeypatch):
    import cadquery as cq

    raw = cq.Solid.makeBox(100., 139.7, 38.1)
    own = cq.Solid.makeCylinder(14.2875 / 2., 38.1, cq.Vector(50., 69.85, 0.))
    # Full-width front-open cut, 10 mm deep; its exact area loss is 1397 mm².
    slot = cq.Solid.makeBox(10., 139.7, 10., cq.Vector(30., 0., 0.))
    finished = raw.cut(own).cut(slot).clean()
    raw_path, finished_path = tmp_path / "raw.brep", tmp_path / "finished.brep"
    raw.exportBrep(str(raw_path))
    finished.exportBrep(str(finished_path))
    parts = []
    for index in range(20):
        for kind, shape, path in (("raw_timber", raw, raw_path), ("finished_timber", finished, finished_path)):
            parts.append({"id": f"member_{index}", "kind": kind, "path": str(path),
                          "sha256": timber.sha(path), "volume_mm3": shape.Volume(),
                          "grain_axis_xyz": [1., 0., 0.]})
    cache = tmp_path / "cache.json"
    cache.write_text(json.dumps({"candidate": timber.CANDIDATE, "layout_sha256": timber.LAYOUT_SHA,
                                 "parts": parts}))
    # Redirect the artifact root only for this method coupon; no production data.
    monkeypatch.setattr(timber, "ROOT", tmp_path)
    layout = {"installed_axes": [{"id": "method_coupon", "point": [50., 69.85, 0.],
                                  "direction": [0., 0., 1.], "grip_mm": 38.1,
                                  "bore_diameter_mm": 14.2875, "receivers": ["member_0"]}]}
    result = timber.exact_finished_geometry(cache, layout)
    boundary = result["receiver_boundary_geometry"][0]
    assert boundary["finished_full_wall_length_mm"] == pytest.approx(38.1)
    assert boundary["sampled_minimum_distances_to_first_finished_boundary_mm"]["grain"]["negative"] == pytest.approx(10.)
    rows = result["finished_member_sections"][0]["sampled_sections"]
    slot_row = next(r for r in rows if abs(r["station_global_grain_projection_mm"] - 35.) < 1e-6)
    assert slot_row["finished_area_mm2"] == pytest.approx(139.7 * (38.1 - 10.), abs=1e-5)
    bore_row = next(r for r in rows if abs(r["station_global_grain_projection_mm"] - 50.) < 1e-6)
    assert bore_row["finished_area_mm2"] == pytest.approx((139.7 - 14.2875) * 38.1, abs=1e-5)
    assert boundary["formal_NDS_end_edge_acceptance"] is False


def test_own_bore_restoration_preserves_larger_housed_receiver_recess():
    import cadquery as cq

    raw = cq.Solid.makeBox(100., 139.7, 88.9)
    point, axis = cq.Vector(50., 69.85, 0.), cq.Vector(0., 0., 1.)
    bore = cq.Solid.makeCylinder(11.1125 / 2., 88.9, point)
    # The first 38.1 mm of nominal grip is another member's housed region.
    recess = cq.Solid.makeBox(100., 139.7, 38.1)
    finished = raw.cut(recess).cut(bore).clean()
    audit = timber.finished_bore_wall_intervals(finished, point, axis, 11.1125 / 2.)
    assert audit["full_wall_length_mm"] == pytest.approx(50.8)
    assert audit["full_wall_intervals_mm"][0] == pytest.approx([38.1, 88.9])
    low, high = audit["full_wall_intervals_mm"][0]
    own = cq.Solid.makeCylinder(11.1125 / 2., high - low, point + axis.multiply(low))
    restored = finished.fuse(own.intersect(raw)).clean()
    assert not any(s.isInside(cq.Vector(50., 69.85, 20.), 1e-6) for s in restored.Solids())
    assert any(s.isInside(cq.Vector(50., 69.85, 50.), 1e-6) for s in restored.Solids())


def test_partial_cylinder_wall_is_not_promoted_to_full_bearing_length():
    import cadquery as cq

    raw = cq.Solid.makeBox(100., 139.7, 38.1)
    point, axis = cq.Vector(50., 69.85, 0.), cq.Vector(0., 0., 1.)
    bore = cq.Solid.makeCylinder(14.2875 / 2., 38.1, point)
    # Cut into one side of the bore over only an interior axial band. A min/max
    # projection of the remaining cylindrical wall would wrongly fill the cut.
    channel = cq.Solid.makeBox(50., 139.7, 10., cq.Vector(0., 0., 10.))
    finished = raw.cut(bore).cut(channel).clean()
    audit = timber.finished_bore_wall_intervals(finished, point, axis, 14.2875 / 2.)
    assert audit["partial_wall_present"] is True
    assert audit["full_wall_intervals_mm"] == []
    assert audit["full_wall_length_mm"] == 0.
    assert audit["qualified_directional_bearing_length_mm"] is None


def test_required_fyb_inverts_governing_yield_and_refuses_fixed_bearing_ceiling():
    axis = {"attachments": [{}], "diameter_mm": 12.7, "grip_mm": 38.1,
            "before_plate_mm": 5.55625, "after_plate_mm": 0.}
    action = {"load_to_grain_degrees": 45., "lateral_n": 1.}
    material = {"scenario_id": "coupon", "source": "artificial known-answer input",
                "steel_Fe_psi": 49500., "bolt_Fyb_psi": 5000.,
                "full_body_diameter_in": .5, "thread_root_diameter_in": .4,
                "wood_thread_bearing_length_in": 0., "steel_thread_bearing_length_in": 0.}
    initial = timber.single_shear_reference(axis, action, material)
    assert initial["governing_mode"] in {"IIIm", "IIIs", "IV"}
    target = initial["single_fastener_reference_n"]
    required = timber.required_fyb_for_single_shear(axis, action, material, target)
    assert required["required_Fyb_psi"] == pytest.approx(5000., rel=1e-10)
    above = 2. * min(initial["mode_values_n"]["Im"], initial["mode_values_n"]["Is"])
    impossible = timber.required_fyb_for_single_shear(axis, action, material, above)
    assert impossible["status"] == "fixed_bearing_geometry_cannot_carry_target"
    assert impossible["required_Fyb_psi"] is None
    intermediate = timber.required_fyb_for_single_shear(
        axis, dict(action, load_to_grain_degrees=0.), material, 3000.)
    assert intermediate["bearing_ceiling_governing_mode"] == "II"
    # Solve the rigid bolt's force-equilibrium quadratic independently: ModeII
    # remains fixed even as Fyb tends to infinity.
    qm, qs, lm, ls = 5600. * .5, 49500. * .5, 1.5, 7. / 32.
    aa = 1. / (4. * qs) + 1. / (4. * qm)
    bb = (lm + ls) / 2.
    cc = -qs * ls**2 / 4. - qm * lm**2 / 4.
    rigid_force = -2. * cc / (bb + math.sqrt(bb**2 - 4. * aa * cc))
    assert intermediate["bearing_ceiling_reference_n"] == pytest.approx(rigid_force / 3.6 * timber.N_PER_LBF)
    assert intermediate["bearing_ceiling_reference_n"] < intermediate["Fyb_independent_mode_ceilings_n"]["Im"]


def test_retained_reference_uses_both_actual_bearing_lengths_and_grains():
    axis = {"id": "retained_coupon", "attachments": [], "receivers": ["runner", "leg"],
            "direction": [1., 0., 0.], "diameter_mm": 12.7}
    geometry = {"receiver_boundary_geometry": [
        {"axis_id": axis["id"], "member": "runner", "grain_axis_xyz": [0., 1., 0.],
         "finished_full_wall_length_mm": 38.1},
        {"axis_id": axis["id"], "member": "leg", "grain_axis_xyz": [0., 0., 1.],
         "finished_full_wall_length_mm": 50.8}]}
    body, root = timber.retained_wood_wood_curves({"installed_axes": [axis]}, geometry)["curves"]
    parallel = next(r for r in body["opposed_same_state_force_directions"]
                    if r["orientation_about_first_member_grain_degrees"] == 0.)
    assert [r["bearing_length_in"] for r in parallel["members"]] == pytest.approx([1.5, 2.])
    assert [r["load_to_grain_degrees"] for r in parallel["members"]] == pytest.approx([0., 90.])
    assert set(parallel["mode_values_n"]) == {"Im", "Is", "II", "IIIm", "IIIs", "IV"}
    assert parallel["mode_values_n"]["Im"] == pytest.approx(.5 * 1.5 * 5600. / 5. * timber.N_PER_LBF)
    assert root["effective_diameter_in"] == pytest.approx(.4)
    assert body["historical_result_transferred"] is False


def test_shared_shaft_requires_equal_vectors_and_retains_external_moment():
    axis = {"id": "shared_coupon", "attachments": [
                {"angle_id": "one", "flange": "a", "receiver": "wood", "entry_xyz_mm": [0., 0., 0.]},
                {"angle_id": "two", "flange": "b", "receiver": "wood", "entry_xyz_mm": [0., 0., 38.1]}],
            "point": [0., 0., 0.],
            "direction": [0., 0., 1.], "grip_mm": 38.1, "diameter_mm": 12.7,
            "before_plate_mm": 5.55625, "after_plate_mm": 5.55625}
    first = {"case_id": "one", "state_id": "first_state", "axis_id": axis["id"],
             "angle_id": "one", "flange": "a", "receiver": "wood", "grain_axis_xyz": [1., 0., 0.],
             "point_xyz_mm": [0., 0., 0.],
             "force_on_receiver_xyz_n": [100., 0., 0.],
             "free_attachment_moment_xyz_nmm": [0., 0., 0.],
             "load_to_grain_degrees": 0.}
    second = dict(first, angle_id="two", flange="b", point_xyz_mm=[0., 0., 38.1],
                  force_on_receiver_xyz_n=[0., 100., 0.], load_to_grain_degrees=90.)
    failed = timber.shared_shaft_reference(axis, [first, second], None)
    assert failed["equal_vector_side_actions_established"] is False
    assert failed["four_mode_reference_n"] is None
    assert failed["combined_external_moment_about_axis_point_xyz_nmm"] == pytest.approx([-3810., 0., 0.])
    material = {"scenario_id": "artificial", "source": "method test only",
                "steel_Fe_psi": 49500., "bolt_Fyb_psi": 45000.,
                "full_body_diameter_in": .5, "thread_root_diameter_in": .4,
                "wood_thread_bearing_length_in": 0.,
                "steel_side_a_thread_bearing_length_in": 0.,
                "steel_side_b_thread_bearing_length_in": 0.}
    second["force_on_receiver_xyz_n"] = first["force_on_receiver_xyz_n"]
    second["load_to_grain_degrees"] = 0.
    actual = timber.shared_shaft_reference(axis, [first, second], material)
    assert actual["equal_vector_side_actions_established"] is True
    assert set(actual["mode_values_n"]) == {"Im", "Is", "IIIs", "IV"}
    assert actual["two_single_shear_references_added"] is False
    assert actual["joint_utilization"] is None
    with pytest.raises(ValueError, match="one explicit state identity"):
        timber.shared_shaft_reference(axis, [first, dict(second, state_id="another_state")], material)
    with pytest.raises(ValueError, match="foreign flange"):
        timber.shared_shaft_reference(axis, [first, dict(second, angle_id="foreign")], material)


def test_geometry_reuse_requires_recorded_producer_and_unchanged_source(tmp_path, monkeypatch):
    marker = tmp_path / "input.txt"
    marker.write_text("unchanged geometry input")
    producer = tmp_path / "producer.py"
    producer.write_text(timber.Path(timber.__file__).read_text())
    prior = tmp_path / "prior.json"
    prior.write_text(json.dumps({"candidate": timber.CANDIDATE,
        "layout_report_sha256": timber.LAYOUT_SHA,
        "source_sha256": {"scripts/thin_bolted_timber_resistance.py": timber.sha(producer),
                          marker.name: timber.sha(marker)},
        "finished_geometry_queries": {"known_fixture": "preserved"}}))
    monkeypatch.setattr(timber, "ROOT", tmp_path)
    result, provenance = timber.reused_finished_geometry(prior, producer)
    assert result == {"known_fixture": "preserved"}
    assert provenance["metadata"]["CAD_section_queries_repeated"] is False
    marker.write_text("changed geometry input")
    with pytest.raises(ValueError, match="reusable source differs"):
        timber.reused_finished_geometry(prior, producer)
    producer.write_text("different producer")
    with pytest.raises(ValueError, match="does not recover"):
        timber.reused_finished_geometry(prior, producer)
