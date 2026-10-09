"""Inert coordinate/type/negative controls plus genuine metadata-only intake.

No genuine build_outputs() call, candidate CSV/SVG, CAD or mechanics execution.
"""
import builtins
import copy
import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location("z180_proposal_shop_adapter", HERE / "adapter.py")
a = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(a)


@pytest.fixture(scope="module")
def inputs():
    return json.loads((HERE / "inputs.json").read_bytes())


@pytest.fixture(scope="module")
def methods(inputs):
    return a.reusable_methods(inputs["sources"])


@pytest.fixture(scope="module")
def prepared(inputs):
    # Genuine byte/metadata authentication is permitted; composition is held.
    original = builtins.__import__

    def guarded(name, *args, **kwargs):
        if name.split(".")[0] in {"cadquery", "OCP", "OCC", "build123d", "numpy", "scipy"}:
            pytest.fail("CAD/mechanics import during source preparation: " + name)
        return original(name, *args, **kwargs)

    before = sorted(p.name for p in HERE.iterdir() if p.suffix in (".svg", ".csv"))
    with pytest.MonkeyPatch.context() as patch:
        patch.setattr(builtins, "__import__", guarded)
        patch.setattr(a, "build_outputs", lambda *_: pytest.fail("genuine output trial is held"))
        result = a.prepare(HERE / "inputs.json", a.digest((HERE / "inputs.json").read_bytes()))
    assert sorted(p.name for p in HERE.iterdir() if p.suffix in (".svg", ".csv")) == before == []
    return result


def test_exact_source_metadata_and_protected_census(prepared):
    assert set(prepared["new_axes"]) == set(prepared["old_axes"])
    assert len(prepared["pins"]) > 1117
    assert len(prepared["scenario"]["wall_queries"]) == 16
    assert sum(w["changed_axis"] for w in prepared["scenario"]["wall_queries"]) == 8
    assert len(a.CHANGED_DRAWINGS) == 3 and len(a.REUSED_DRAWINGS) == 6
    assert not any(prepared["inputs"]["release"].values())
    assert prepared["inputs"]["execution_scope"]["genuine_candidate_output_trial_authorized"] is False
    a.verify(prepared["pins"])


def test_exact_pure_selection_excludes_old_build_and_top_level_execution(methods):
    shop, datum, draw = methods
    assert not hasattr(shop, "build") and not hasattr(shop, "main")
    assert set(vars(shop)) == {"require", "sha", "canonical", "table", "vector", "put", "drawings"}
    assert datum.local([2., 3., 5.], [1., 1., 1.], [[0, 0, 1], [1, 0, 0], [0, 1, 0]]) == [4., 1., 2.]
    tiny = draw.SVG(10, 10)
    tiny.text(1, 2, "<unadopted>")
    assert "&lt;unadopted&gt;" in tiny.render()


def test_source_hash_is_authenticated_before_ast_compilation(inputs, monkeypatch):
    sources = copy.deepcopy(inputs["sources"])
    sources["old_export"]["sha256"] = "0" * 64
    monkeypatch.setattr(a, "selected_functions", lambda *_args, **_kw: pytest.fail("AST compiler reached before hash check"))
    with pytest.raises(ValueError, match="source bytes differ"):
        a.reusable_methods(sources)


def test_input_hash_rejected_before_any_source_or_compiler(monkeypatch):
    monkeypatch.setattr(a, "read_ref", lambda *_: pytest.fail("source touched before input hash check"))
    with pytest.raises(ValueError, match="frozen input bytes differ"):
        a.prepare(HERE / "inputs.json", "0" * 64)


def test_caption_seam_rejects_missing_or_repeated_contract(inputs):
    raw = a.read_ref(inputs["sources"]["old_export"])
    old = next(iter(a.DRAWING_CAPTIONS)).encode()
    with pytest.raises(ValueError, match="exact saved Z200 drawing caption"):
        a.selected_functions(raw.replace(old, b"foreign caption"), ("drawings",), captions=True)
    with pytest.raises(ValueError, match="exact saved Z200 drawing caption"):
        a.selected_functions(b"def drawings():\n    return " + repr(old.decode()).encode() + b", " + repr(old.decode()).encode(), ("drawings",), captions=True)


@pytest.mark.parametrize("mutation,match", [
    ("duplicate", "four unique"), ("4p5in", "original4in"),
    ("xshift", "only four"), ("foreign96", "unchanged96"),
    ("adopted", "unadopted OFF"), ("nativeCOM", "separate analytic COM"),
    ("foreign_source", "separate analytic COM"),
])
def test_proposal_join_negative_controls(prepared, mutation, match):
    bundle = dict(prepared)
    data = copy.deepcopy(prepared["data"])
    bundle["data"] = data
    if mutation == "duplicate":
        data["layout"]["proposed_axes"].append(copy.deepcopy(data["layout"]["proposed_axes"][0]))
    elif mutation == "4p5in":
        data["layout"]["proposed_axes"][0]["nominal_under_head_length_mm"] = 114.3
    elif mutation == "xshift":
        data["layout"]["proposed_axes"][0]["point_xyz_mm"][0] += 1.
    elif mutation == "foreign96":
        data["descriptor"]["shafts"][0]["source_axis"]["point_xyz_mm"][2] += 1.
    elif mutation == "adopted":
        data["layout"]["release"]["geometry_adopted"] = True
    else:
        row = next(r for r in data["descriptor"]["finished_body_observations"] if r["id"] == "eoere_cleat_left")
        if mutation == "nativeCOM":
            row["provenance"]["new_native_COM_query_performed"] = True
        else:
            row["source"]["sha256"] = "0" * 64
    with pytest.raises(ValueError, match=match):
        a.validate_join(bundle)


def fixture_hole():
    axis = {"point_xyz_mm": [0., 10., 180.], "direction_xyz": [1., 0., 0.], "bore_diameter_mm": 10.31875}
    row = {"axis_id": a.AXES[0], "receiver": "eoere_cleat_left", "modeled_bore_envelope_diameter_mm": "10.31875",
        "axis_point_x_mm": "0", "axis_point_y_mm": "10", "axis_point_z_mm": "200",
        "axis_direction_x_unitless": "1", "axis_direction_y_unitless": "0", "axis_direction_z_unitless": "0",
        "entry_from_axis_point_mm": "0", "exit_from_axis_point_mm": "38.1", "saved_full_wall_length_mm": "38.1",
        "source": "original saved observation", "Actual": "", "Disposition": ""}
    profile = {"datum_xyz_mm": [0., 0., 139.7], "basis_grain_u_v_xyz": [[0., 0., 1.], [1., 0., 0.], [0., 1., 0.]]}
    wall = {"axis_id": a.AXES[0], "receiver": row["receiver"], "full_wall_intervals_mm": [[0., 38.1]],
        "full_wall_length_mm": 38.1, "partial_wall_present": False, "matching_cylindrical_faces": [{"full_circumference_wall": True}],
        "bore_diameter_mm": 10.31875, "query_point_xyz_mm": [0., 10., 180.], "query_direction_xyz": [1., 0., 0.]}
    return row, axis, profile, wall


def test_moved_hole_known_answer_keeps_full_interval_and_direction(methods):
    row, axis, profile, wall = fixture_hole()
    shop, datum, _ = methods
    a.update_hole(row, axis, profile, wall, moved=True, shop=shop, datum=datum, tolerance=1e-6)
    assert shop.vector(row, "axis_point") == [0., 10., 180.]
    assert shop.vector(row, "entry_in_receiver", "luv") == pytest.approx([40.3, 0., 10.], abs=1e-12)
    assert shop.vector(row, "exit_in_receiver", "luv") == pytest.approx([40.3, 38.1, 10.], abs=1e-12)
    assert [row["entry_from_axis_point_mm"], row["exit_from_axis_point_mm"]] == ["0", "38.1"]
    assert row["axis_direction_x_unitless"] == "1" and row["Actual"] == row["Disposition"] == ""


def test_retained_hole_rebinds_source_without_relabeling_numeric_observation(methods):
    row, axis, profile, wall = fixture_hole()
    row["axis_point_z_mm"] = "180"
    old = copy.deepcopy(row)
    shop, datum, _ = methods
    a.update_hole(row, axis, profile, wall, moved=False, shop=shop, datum=datum, tolerance=1e-6)
    assert {k for k in row if row[k] != old[k]} == {"source"}
    assert row["source"].startswith("source-bindings.json#/receiver_holes/")


@pytest.mark.parametrize("mutation,match", [("partial", "full saved wall"), ("arc", "full saved wall"),
    ("interval", "interval/bore"), ("diameter", "interval/bore"), ("direction", "point/direction"), ("old_direction", "length/direction")])
def test_saved_wall_negative_controls(methods, mutation, match):
    row, axis, profile, wall = fixture_hole()
    if mutation == "partial":
        wall["partial_wall_present"] = True
    elif mutation == "arc":
        wall["matching_cylindrical_faces"][0]["full_circumference_wall"] = False
    elif mutation == "interval":
        wall["full_wall_intervals_mm"][0][1] -= 1.
    elif mutation == "diameter":
        wall["bore_diameter_mm"] = 11.1125
    elif mutation == "direction":
        wall["query_direction_xyz"] = [-1., 0., 0.]
    else:
        row["axis_direction_x_unitless"] = "-1"
    shop, datum, _ = methods
    with pytest.raises(ValueError, match=match):
        a.update_hole(row, axis, profile, wall, moved=True, shop=shop, datum=datum, tolerance=1e-6)


@pytest.mark.parametrize("axis_id", a.AXES)
@pytest.mark.parametrize("side", ("head", "nut"))
def test_eight_access_sides_translate_without_mirroring_roles(methods, axis_id, side):
    direction = [1., 0., 0.] if "left" in axis_id else [-1., 0., 0.]
    old_axis = {"point_xyz_mm": [3., 10., 200.], "direction_xyz": direction, "receivers": ["cleat", "post"]}
    new_axis = {**old_axis, "point_xyz_mm": [3., 10., 180.], "nominal_under_head_length_mm": 101.6}
    row = {"axis_id": axis_id, "side": side, "scene_role_id": axis_id+"_"+side, "axis_positive_xyz": str(direction),
        "nominal_inward_approach_xyz": "own side direction", "nominal_outward_removal_xyz": "own opposite direction",
        "axis_origin_xyz_mm": "3;10;200", "nominal_bearing_face_xyz_mm": "5;10;200",
        "nominal_outboard_face_xyz_mm": "7;10;200", "nominal_tip_xyz_mm": "9;10;200",
        "current_station_translated": "False", "Actual": "", "Disposition": ""}
    old = copy.deepcopy(row)
    a.shift_access(row, old_axis, new_axis, methods[1])
    assert row["axis_origin_xyz_mm"] == "3;10;180"
    assert row["nominal_bearing_face_xyz_mm"] == "5;10;180"
    assert row["nominal_outboard_face_xyz_mm"] == "7;10;180" and row["nominal_tip_xyz_mm"] == "9;10;180"
    allowed = {"axis_origin_xyz_mm", "nominal_bearing_face_xyz_mm", "nominal_outboard_face_xyz_mm", "nominal_tip_xyz_mm", "current_station_translated"}
    assert all(row[k] == v for k, v in old.items() if k not in allowed)


def test_separate_native_geometry_and_analytic_COM():
    host = "eoere_cleat_left"
    native = {"path": "inert/new.brep", "sha256": "a"*64, "bytes": 10, "volume_mm3": 12., "bounds_xyz_mm": [[0., 1.]]*3}
    observation = {"source": native, "center_xyz_mm": [1., 2., 3.25], "source_only_analytic_centroid": True,
                   "provenance": {"new_native_COM_query_performed": False}}
    row = a.replacement_finished(host, observation, native, {"path": "inert/own-descriptor", "sha256": "b"*64}, {"path": "inert/saved-native-result", "sha256": "c"*64})
    assert row["analytic_center_xyz_mm"] == observation["center_xyz_mm"]
    assert row["analytic_center_source"]["native_COM_query_performed"] is False
    assert row["volume_mm3"] == native["volume_mm3"]
    assert "center_xyz_mm" not in row and "strict_native_geometry" not in row
    assert row["saved_native_geometry_source"]["scenario"] == "proposed_Z180_modeled"


def test_twenty_own_original_hardware_roles_are_source_metadata(prepared):
    shafts = [s for s in prepared["data"]["descriptor"]["shafts"] if s["axis_id"] in a.AXES]
    assert len(shafts) == 4 and all(len(s["metal_roles"]) == 5 for s in shafts)
    assert len({role["id"] for s in shafts for role in s["metal_roles"]}) == 20
    assert all(s["source_axis"]["nominal_under_head_length_mm"] == 101.6 for s in shafts)
    assert all(role["center_of_mass_xyz_mm"][2] == 180. for s in shafts for role in s["metal_roles"])


def test_saved_rendering_types_are_restored_without_mutating_tables(methods):
    screws = (["axis_id", "moved_by_rail_revision", "Actual", "Disposition"],
        [{"axis_id": "old", "moved_by_rail_revision": "False", "Actual": "", "Disposition": ""},
         {"axis_id": "moved", "moved_by_rail_revision": "True", "Actual": "", "Disposition": ""}])
    columns = ["identity", "panel", "kind", "modeled_diameter_mm", "origin_x_mm", "origin_y_mm", "origin_z_mm",
        "direction_x_unitless", "direction_y_unitless", "direction_z_unitless", "origin_in_panel_l_mm", "origin_in_panel_u_mm",
        "origin_in_panel_v_mm", "source", "Actual", "Disposition"]
    row = dict(zip(columns, ["id", "panel", "tnut"]+[str(i) for i in range(10)]+["honest source", "", ""], strict=True))
    render_screws, machining = a.rendering_inputs(screws, (columns, [row]))
    assert [r["moved_by_rail_revision"] for r in render_screws] == [False, True]
    assert screws[1][0]["moved_by_rail_revision"] == "False"
    assert machining[0] == ["id", "panel", "tnut"]+list(map(float, range(10)))+["honest source"]
    assert row["Actual"] == row["Disposition"] == ""


def test_rendering_rejects_ambiguous_boolean():
    with pytest.raises(ValueError, match="saved screw boolean"):
        a.rendering_inputs((["Actual", "Disposition"], [{"moved_by_rail_revision": "false"}]), ([], []))


def test_recipe_and_inherited_field_preservation_guard():
    old = (["id", "length", "source"], [{"id": "four_inch", "length": "101.6", "source": "old"}, {"id": "fixed", "length": "200", "source": "old"}])
    new = copy.deepcopy(old)
    new[1][0]["source"] = "own proposal source"
    a.permitted_changes(old, new, ("id",), {("four_inch",)}, {"source"})
    new[1][0]["length"] = "114.3"
    with pytest.raises(ValueError, match="unexpected saved field edit"):
        a.permitted_changes(old, new, ("id",), {("four_inch",)}, {"source"})
    new = copy.deepcopy(old)
    new[1][1]["source"] = "foreign inheritance"
    with pytest.raises(ValueError, match="unexpected saved field edit"):
        a.permitted_changes(old, new, ("id",), {("four_inch",)}, {"source"})


@pytest.mark.parametrize("column", ["Actual", "Actual_thread_runout", "Disposition"])
def test_observed_or_disposition_cells_are_rejected(column):
    with pytest.raises(ValueError, match="actual observation/disposition"):
        a.blank_observations([{column: "accepted"}])


def test_duplicate_join_identity_rejected():
    with pytest.raises(ValueError, match="duplicate identity"):
        a.index([{"id": "same"}, {"id": "same"}], ("id",))


@pytest.fixture
def inert_bundle(methods):
    """Synthetic full-row boundary fixture; no genuine candidate composition."""
    shop, datum, draw = methods
    hosts = sorted(a.HOSTS)
    def ref(label):
        return {"path": "inert/"+label, "sha256": "a"*64}
    def table(rows):
        return list(rows[0]), rows
    source_row, axis, profile, wall = fixture_hole()
    profiles = {host: {**copy.deepcopy(profile), "finished": ref("old-"+host)} for host in hosts}
    observations, bodies = {}, {}
    for host in hosts:
        bodies[host] = {"id": host, **ref("new-"+host), "bytes": 123, "volume_mm3": 456., "bounds_xyz_mm": [[0., 1.]]*3}
        observations[host] = {"source": bodies[host], "center_xyz_mm": [1., 2., 3.], "source_only_analytic_centroid": True,
                             "provenance": {"new_native_COM_query_performed": False}}
    members = [{"member": host, "current_finished_source_path": profiles[host]["finished"]["path"],
        "current_finished_source_sha256": profiles[host]["finished"]["sha256"], "Actual": "", "Disposition": ""} for host in hosts]
    for i in range(24):
        host = "fixed_member_"+str(i)
        profiles[host] = {**copy.deepcopy(profile), "finished": ref(host)}
        members.append({"member": host, "current_finished_source_path": ref(host)["path"],
                        "current_finished_source_sha256": ref(host)["sha256"], "Actual": "", "Disposition": ""})
    holes = []
    moved_locations = {line: (axis_id, hosts[2*(i//2)+j]) for i, axis_id in enumerate(a.AXES) for j, line in enumerate((90+2*i, 91+2*i))}
    retained_locations = {line: ("retained_"+str(i), hosts[i//2]) for i, line in enumerate((69, 73, 75, 79, 106, 108, 110, 112))}
    old_axes, new_axes, walls = {}, {}, []
    for line in range(2, 122):
        identity, host = (moved_locations | retained_locations).get(line, ("fixed_axis_"+str(line), "fixed_member_0"))
        moved = line in moved_locations
        row = {**copy.deepcopy(source_row), "axis_id": identity, "receiver": host, "axis_point_z_mm": "200" if moved else "180"}
        for point in ("axis_point", "entry", "exit"):
            for direction in "luv":
                row[point+"_in_receiver_"+direction+"_mm"] = "saved scalar"
        holes.append(row)
        new_axes[identity] = {**copy.deepcopy(axis), "receivers": ["cleat", "post"], "nominal_under_head_length_mm": 101.6}
        old_axes[identity] = copy.deepcopy(new_axes[identity])
        old_axes[identity]["point_xyz_mm"][2] = 200. if moved else 180.
        if host in a.HOSTS:
            walls.append({**copy.deepcopy(wall), "axis_id": identity, "receiver": host})
    stacks = [{"axis_id": axis_id, "nominal_underhead_length_mm": "101.6", "geometry_axis_pointer": "old geometry",
               "current_station_translated": "False", "Actual": "", "Disposition": ""} for axis_id in a.AXES]
    access = []
    for axis_id in a.AXES:
        for side in ("head", "nut"):
            access.append({"axis_id": axis_id, "side": side, "axis_origin_xyz_mm": "0;10;200",
                "nominal_bearing_face_xyz_mm": "1;10;200", "nominal_outboard_face_xyz_mm": "2;10;200", "nominal_tip_xyz_mm": "3;10;200",
                "current_station_translated": "False", "Actual": "", "Disposition": ""})
    descriptor = {"shafts": [{"axis_id": axis_id, "metal_roles": [{"id": axis_id+"_role_"+str(i), "center_of_mass_xyz_mm": [0., 10., 180.]} for i in range(5)]} for axis_id in a.AXES]}
    screw_table = (["axis_id", "moved_by_rail_revision", "Actual", "Disposition"],
                   [{"axis_id": "fixed_screw", "moved_by_rail_revision": "False", "Actual": "", "Disposition": ""}])
    machining_columns = ["identity", "panel", "kind", "modeled_diameter_mm", "origin_x_mm", "origin_y_mm", "origin_z_mm",
        "direction_x_unitless", "direction_y_unitless", "direction_z_unitless", "origin_in_panel_l_mm", "origin_in_panel_u_mm",
        "origin_in_panel_v_mm", "source", "Actual", "Disposition"]
    data = {"inert_only": True, "profiles": profiles, "members.csv": table(members), "receiver-holes.csv": table(holes),
        "bolt-stacks.csv": table(stacks), "access-sides.csv": table(access), "panel-screw-datums.csv": screw_table,
        "panel-machining.csv": (machining_columns, []), "native_inputs": {"tolerances": {"coordinate_mm": 1e-6}},
        "layout": {"proposed_axes": [{"id": axis_id} for axis_id in a.AXES]}, "descriptor": descriptor,
        "parent_geometry": {"new_cleat_YZ_polygon_mm": []}, "recesses": []}
    encoded = {name: b"saved inherited drawing" for name in a.REUSED_DRAWINGS}
    def renderer(_draw, _profiles, _holes, screws, machining, _view, _recesses):
        assert screws[0]["moved_by_rail_revision"] is False and machining == []
        return {**encoded, **{name: b"Extended-cleat frame: nominal member projections" if name.startswith("member") else b"inert proposal caption" for name in a.CHANGED_DRAWINGS}}
    return {"data": data, "inputs": {"sources": {name: ref(name) for name in ("descriptor", "native", "layout", "old_result")},
        "saved_files": {name: ref(name) for name in a.UNCHANGED_FILES | a.REUSED_DRAWINGS | {"current_profiles.json"}}},
        "shop": SimpleNamespace(**{**vars(shop), "drawings": renderer}), "datum": datum, "draw": draw, "encoded": encoded, "pins": {},
        "old_axes": old_axes, "new_axes": new_axes, "observations": observations, "scenario": {"finished_bodies": bodies, "wall_queries": walls}}


def test_deferred_composition_boundary_with_inert_rows_only(inert_bundle, monkeypatch):
    monkeypatch.setattr(a, "validate_join", lambda b: a.require(b["data"].get("inert_only"), "only inert fixture allowed"))
    outputs, result = a.build_outputs(inert_bundle)
    assert set(outputs) == a.CHANGED_DRAWINGS | {"members.csv", "receiver-holes.csv", "bolt-stacks.csv", "access-sides.csv", "current_profiles.json", "source-bindings.json", "hardware-role-locations.json"}
    assert set(result["inherited_files_via_links"]) == a.REUSED_DRAWINGS | a.UNCHANGED_FILES
    assert result["changed_receiver_lines"] == list(range(90, 98))
    assert result["retained_receiver_source_rebinding_lines"] == [69, 73, 75, 79, 106, 108, 110, 112]
    bindings = json.loads(outputs["source-bindings.json"])
    assert len(bindings["receiver_holes"]) == 16
    assert sum(r["axis_moved"] for r in bindings["receiver_holes"].values()) == 8
    assert all(r["native_query_performed_now"] is False for r in bindings["receiver_holes"].values())
    roles = json.loads(outputs["hardware-role-locations.json"])["roles"]
    assert len(roles) == 20 and all(r["Actual"] == r["Disposition"] == "" for r in roles)
    assert all(name not in outputs for name in a.REUSED_DRAWINGS)
    assert not any(result["release"].values()) and result["old_Z200_build_or_HOLD_contract_relabelled"] is False
    for name in ("member-projections-1.svg", "member-projections-3.svg"):
        assert b"Unadopted Z180 proposal" in outputs[name]


def test_changed_inherited_drawing_rejected_in_inert_composition(inert_bundle, monkeypatch):
    monkeypatch.setattr(a, "validate_join", lambda b: a.require(b["data"].get("inert_only"), "only inert fixture allowed"))
    # Keep the renderer's saved-byte reference and supplied expected bytes distinct.
    inert_bundle["encoded"] = {**inert_bundle["encoded"], "panel-layout-1.svg": b"foreign datums"}
    with pytest.raises(ValueError, match="unchanged drawing datums/bytes differ"):
        a.build_outputs(inert_bundle)
