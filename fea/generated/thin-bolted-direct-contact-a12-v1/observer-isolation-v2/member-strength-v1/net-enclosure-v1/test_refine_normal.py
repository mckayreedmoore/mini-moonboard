"""New serialized requested-ID join seam; stress math reuses13 frozen fixtures."""

import copy
import json

import pytest
import refine_normal as method


def test_serialized_46cut_join_accepts_only_projection_roundoff_and_own_schema():
    basis = [[1., 0., 0.], [0., 1., 0.], [0., 0., 1.]]
    planned, measured, old = [], [], []
    for index in range(46):
        planned.append({"member": "synthetic", "station_global_grain_projection_mm": float(index),
                        "expected_frozen_same_station_area_mm2": 10., "basis_u_v_grain_xyz": basis})
        properties = {"station_global_grain_projection_mm": float(index) + 2e-14,
            "finished_area_mm2": 10. + 1e-7, "expected_frozen_same_station_area_mm2": 10.,
            "basis_u_v_grain_xyz": basis, "linear_normal_stress": None,
            "bores_or_other_voids_restored": False, "shear_area_method_qualified": False}
        measured.append({"member": "synthetic", "requested_station_global_grain_projection_mm": float(index),
                         "finished_section_properties": properties})
        old.append({"member": "synthetic", "station_global_grain_projection_mm": float(index),
                    "fully_braced_CD1_normal_reference_enclosure": 2.})
    request = {"schema": "thin_bolted_46_selected_net_geometry_query_readiness/v1",
        "candidate": method.pure.unit.CANDIDATE, "state_id": None, "request_count": 46, "requests": planned}
    geometry = {"schema": "thin_bolted_46_selected_net_finished_geometry/v1", "candidate": method.pure.unit.CANDIDATE,
        "state_id": None, "selected_cut_count": 46, "cached_finished_BREP_count": 5,
        "source_pins_before_after_unchanged": True, "candidate_response_or_current_field_consumed": False,
        "five_existing_exact_sections_requeried": False, "release": {"capacity": False}, "finished_sections": measured}
    # Match the real producer/consumer join through JSON, preserving types.
    geometry, request, old = json.loads(json.dumps((geometry, request, old)))
    before = copy.deepcopy((geometry, request, old))
    joined = method.join46(geometry, request, old)
    assert len(joined) == 46 and ("synthetic", 0.) in joined
    assert (geometry, request, old) == before
    for problem in ("requested_id", "computed_plane", "response_schema", "expected_area"):
        wrong = copy.deepcopy(geometry)
        if problem == "requested_id":
            wrong["finished_sections"][0]["requested_station_global_grain_projection_mm"] += .001
        elif problem == "computed_plane":
            wrong["finished_sections"][0]["finished_section_properties"]["station_global_grain_projection_mm"] += .001
        elif problem == "response_schema":
            wrong["candidate_response_or_current_field_consumed"] = True
        else:
            wrong["finished_sections"][0]["finished_section_properties"]["expected_frozen_same_station_area_mm2"] += .001
        with pytest.raises(ValueError):
            method.join46(wrong, request, old)
