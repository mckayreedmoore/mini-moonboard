"""Known-answer bookkeeping and refusal of incomplete modeled boundaries."""
import copy
import importlib.util
from pathlib import Path

import boundary as b
import pytest


def raw(name, first="A", second="B", role="timber_or_panel_contact", dof=1):
    return {"name": name, "first_body": first, "second_body": second,
            "physical_owner": {"first": first, "second": second, "role": role,
                               "point": [0., 1., 0.]},
            "role": role, "dof": dof, "group": "SPR_"+name+str(dof), "intended_law": "bilateral"}


def test_inventory_includes_crossing_ports_once_and_internal_endpoints_twice():
    rows = [raw("inside"), raw("outside", "A", "E"), raw("irrelevant", "E", "F")]
    result = b.inventory({"raw_source_carrier_law_inventory_rows": rows}, ("A", "B"))
    assert [r["source_connection_name"] for r in result] == ["inside", "outside"]
    assert [r["source_indices"] for r in result] == [[0], [1]]


def test_inventory_refuses_inconsistent_owner_and_mixed_group():
    r = raw("bad")
    r["first_body"] = "C"
    with pytest.raises(ValueError, match="owner/body"):
        b.inventory({"raw_source_carrier_law_inventory_rows": [r]}, ("A", "B"))
    with pytest.raises(ValueError, match="differing owners"):
        b.inventory({"raw_source_carrier_law_inventory_rows": [raw("same"), raw("same", "A", "E")]}, ("A", "B"))


def test_floor_indices_use_filtered_inventory_without_reusing_nonfloor_index():
    nonfloor = raw("contact")
    f2 = raw("floor", "A", "floor", "assumed_no_slip_floor", 2)
    f3 = raw("floor", "A", "floor", "assumed_no_slip_floor", 3)
    rows = [nonfloor, f2, f3]
    binding = next(r for r in b.inventory({"raw_source_carrier_law_inventory_rows": rows}, ("A",))
                   if r["source_connection_name"] == "floor")
    action = {"source_inventory_rows": [
        {"source_connection_name": "floor", "source_row_original_index": 0, "local_dof": 2},
        {"source_connection_name": "floor", "source_row_original_index": 1, "local_dof": 3}]}
    b.checked_scalar_refs(action, binding, rows)
    action["source_inventory_rows"][1]["source_row_original_index"] = 0
    with pytest.raises(ValueError, match="scalar indices"):
        b.checked_scalar_refs(action, binding, rows)


def test_scalar_identity_and_law_are_bound():
    source = raw("port")
    binding = b.inventory({"raw_source_carrier_law_inventory_rows": [source]}, ("A",))[0]
    row = {"role": source["role"], "source_inventory_rows": [
        {"source_connection_name": "port", "source_inventory_row_index": 0,
         "source_row_id": source["group"], "intended_law": "bilateral"}]}
    b.checked_scalar_refs(row, binding, [source])
    row["source_inventory_rows"][0]["intended_law"] = "tension_only"
    with pytest.raises(ValueError, match="identity/law"):
        b.checked_scalar_refs(row, binding, [source])


def test_signed_moment_transport_and_source_radius_known_answers():
    force, point, datum = [7., -2., 9.], [3., 4., 5.], [1., 1., 1.]
    origin = b.wrench(point, force)
    assert origin == [7., -2., 9., 46., 8., -34.]
    local = b.cross([p-d for p, d in zip(point, datum, strict=True)], force)
    assert local == [35., 10., -25.]
    assert b.add(local, b.cross(datum, force)) == origin[3:]
    assert b.moment_radius([-2., 3., -4.], [.1, .2, .3]) == pytest.approx([1.7, 1., .7])


@pytest.mark.parametrize("value", ([0., 0.], [float("nan"), 0., 0.], [0., float("inf"), 0.]))
def test_nonfinite_and_malformed_points_refused(value):
    with pytest.raises(ValueError):
        b.vector(value)


def test_negative_precision_bounds_are_refused():
    with pytest.raises(ValueError, match="negative radius"):
        b.moment_radius([1., 2., 3.], [0., -.1, 0.])


def state_fixture():
    # Two endpoints on an axial line are intentionally distinct. Counterloads
    # act at each endpoint; the exact force and moment residuals are zero.
    owner = {"first": "A", "second": "B", "role": "timber_or_panel_contact",
             "point": [0., 1., 0.], "first_point": [0., 1., 0.],
             "second_point": [2., 1., 0.], "scalar_normal": [1., 0., 0.]}
    source = {**raw("tie"), "physical_owner": owner}
    action = {**owner, "force_on_first_xyz_n": [5., 0., 0.],
              "force_on_second_xyz_n": [-5., 0., 0.], "force_rounding_radius_xyz_n": [.1, 0., 0.],
              "source_inventory_rows": [{"source_connection_name": "tie",
                  "source_inventory_row_index": 0, "source_row_id": source["group"],
                  "intended_law": "bilateral"}]}
    model = {"raw_source_carrier_law_inventory_rows": [source],
             "body_geometry": {body: {"geometry_record": {"start": datum, "end": datum}}
                               for body, datum in (("A", [0., 0., 0.]), ("B", [2., 0., 0.]))},
             "physical_body_loads": {"A": {"1": [-5., 0., 0.]}, "B": {"2": [5., 0., 0.]}},
             "nodes": {"1": [0., 1., 0.], "2": [2., 1., 0.]}}
    response = {"load_factor": 1., "physical_connection_forces": {"tie": action}}
    audit = {"load_factor": 1., "body_equilibrium": {
        body: {"reference_xyz_mm": datum, "force_residual_xyz_n": [0., 0., 0.],
               "moment_residual_xyz_nmm": [0., 0., 0.], "force_rounding_radius_xyz_n": [.1, 0., 0.],
               "moment_rounding_radius_xyz_nmm": [0., 0., .1],
               "printed_resultants_passed": True, "interval_resultants_passed": True}
        for body, datum in (("A", [0., 0., 0.]), ("B", [2., 0., 0.]))}}
    path = Path(__file__).resolve().parents[1]/"mvp-acceleration-2026-09-28/current-corner-native-demand-export-attempt03/produce.py"
    spec = importlib.util.spec_from_file_location("synthetic_boundary_export", path)
    method = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(method)
    return method, model, response, audit


def test_whole_state_retains_distinct_endpoints_and_every_nodal_load():
    method, model, response, audit = state_fixture()
    saved = copy.deepcopy(response)
    result = b.checked_state(method, model, response, audit, b.inventory(model, ("A", "B")), ("A", "B"))
    assert result["internal_interface_count"] == 1
    assert result["boundary_interface_count"] == 0
    assert [r["point_xyz_mm"] for r in result["endpoint_actions"]] == [[0., 1., 0.], [2., 1., 0.]]
    assert len(result["body_load_actions"]) == 2
    assert result["internal_cancellation_wrench_N_Nmm"] == [0.]*6
    assert result["combined_residual_wrench_about_origin_N_Nmm"] == [0.]*6
    assert response == saved


def test_common_source_point_is_exposed_for_both_endpoints():
    method, model, response, audit = state_fixture()
    for row in (model["raw_source_carrier_law_inventory_rows"][0]["physical_owner"],
                response["physical_connection_forces"]["tie"]):
        del row["first_point"], row["second_point"]
    result = b.checked_state(method, model, response, audit, b.inventory(model, ("A", "B")), ("A", "B"))
    action = result["interface_actions"]["tie"]
    assert action["first_point"] == action["second_point"] == [0., 1., 0.]


@pytest.mark.parametrize("mutation", ("missing_action", "shifted_endpoint", "negative_radius", "missing_load_node", "missing_load_body", "wrong_load"))
def test_state_refuses_incomplete_or_incompatible_actions(mutation):
    method, model, response, audit = state_fixture()
    if mutation == "missing_action":
        response["physical_connection_forces"] = {}
    elif mutation == "shifted_endpoint":
        response["physical_connection_forces"]["tie"]["second_point"][1] = 2.
    elif mutation == "negative_radius":
        response["physical_connection_forces"]["tie"]["force_rounding_radius_xyz_n"][0] = -.1
    elif mutation == "missing_load_node":
        del model["nodes"]["2"]
    elif mutation == "missing_load_body":
        del model["physical_body_loads"]["B"]
    elif mutation == "wrong_load":
        model["physical_body_loads"]["B"]["2"][0] = 6.
    with pytest.raises((ValueError, method.ExportBlocked)):
        b.checked_state(method, model, response, audit, b.inventory(model, ("A", "B")), ("A", "B"))


def geometry_fixture():
    graph, bindings, duties = {"edges": []}, [], []
    for side in ("L", "R"):
        post, cleat = "P_"+side, "C_"+side
        duty = {"panel_receiver_post": post}
        for kind, pair, axes in (
            ("direct_post_header_seat", (post, "H"), []),
            ("post_to_cleat_attachment", (post, cleat), ["post_"+side+str(i) for i in (1, 2)]),
            ("cleat_to_header_attachment", (cleat, "H"), ["header_"+side+str(i) for i in (1, 2)]),
        ):
            prefix = kind+side
            duty[kind] = {"member_pair": list(pair), "candidate_bolt_axes": axes}
            graph["edges"].append({"member_ids": list(pair), "geometry_state": "finite_opposed_planar_touch",
                "interface_geometry_state": "finite_planar_face_contact", "broadphase_candidate": True,
                "opposed_planar_face_contact_area_mm2": 1., "minimum_separation_mm": 0.,
                "candidate_bolt_associations": [{"axis_id": a} for a in axes], "current_panel_screw_associations": []})
            for i in range(4):
                bindings.append({"source_connection_name": prefix+str(i), "owner": {
                    "first": pair[0], "second": pair[1], "role": "timber_or_panel_contact"}})
            for axis in axes:
                for channel in ("plane", "axial"):
                    bindings.append({"source_connection_name": axis+channel, "owner": {
                        "first": pair[0], "second": pair[1], "role": channel, "axis_id": axis}})
        duties.append(duty)
    return graph, bindings, duties, ("H", "P_L", "P_R", "C_L", "C_R")


def test_seats_remain_distinct_from_cleat_routes_and_bolts():
    result = b.geometry_ports(*geometry_fixture())
    assert result["incident_pair_count"] == 6
    assert result["unmodeled_geometric_ports"] == []
    for route in result["center_routes"]:
        seat, post, header = route["portions"]
        assert seat["candidate_bolt_axes"] == seat["modeled_bolt_names"] == []
        assert len(seat["modeled_contact_names"]) == 4
        assert len(post["modeled_bolt_names"]) == len(header["modeled_bolt_names"]) == 4
        assert all(port["force_split_calculated"] is False for port in route["portions"])


@pytest.mark.parametrize("mutation", ("missing_contact", "extra_contact_pair", "wrong_axis_pair", "duplicate_graph_pair"))
def test_geometric_port_inventory_refuses_missing_or_incompatible_pairs(mutation):
    graph, bindings, duties, members = geometry_fixture()
    if mutation == "missing_contact":
        del bindings[0]
    elif mutation == "extra_contact_pair":
        bindings.append({"source_connection_name": "extra", "owner": {
            "first": "P_L", "second": "P_R", "role": "timber_or_panel_contact"}})
    elif mutation == "wrong_axis_pair":
        graph["edges"][0]["candidate_bolt_associations"] = [{"axis_id": "header_L1"}]
    elif mutation == "duplicate_graph_pair":
        graph["edges"].append(copy.deepcopy(graph["edges"][0]))
    with pytest.raises(ValueError):
        b.geometry_ports(graph, bindings, duties, members)
