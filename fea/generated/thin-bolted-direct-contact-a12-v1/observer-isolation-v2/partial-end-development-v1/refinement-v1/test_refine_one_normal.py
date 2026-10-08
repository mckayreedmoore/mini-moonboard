"""One exact JSON join fixture; reuse all 13 original stress fixtures."""

import copy

import pytest
import refine_one_normal as method


def test_exact_one_geometry_request_coarse_join_and_roundoff_only_station():
    class MetadataOnly(dict):
        def __getitem__(self, key):
            assert "wrench" not in key and "signed_local" not in key
            return super().__getitem__(key)

    rows = [MetadataOnly(member="fixture" + str(i), station_global_grain_projection_mm=float(i),
        fully_braced_CD1_normal_reference_enclosure=.5) for i in range(17)]
    rows.append(MetadataOnly(member=method.EXPECTED_KEY[0], station_global_grain_projection_mm=method.EXPECTED_KEY[1],
        fully_braced_CD1_normal_reference_enclosure=2.2, expected_finished_area_mm2=method.EXPECTED_AREA_MM2))
    coarse = {"schema": "thin_bolted_18_partial_end_conditional_affine_normal_findings/v1",
        "counts": {"partial_end_sections": 18, "reference_header_bearing_patch_overlap_witnesses": 12,
            "conditional_normal_bounds_below_one": 17, "conservative_normal_bounds_exceeding_one": 1},
        "source_pins_before_after_unchanged": True, "release": {"fabrication_released": False},
        "18_conditional_partial_end_findings": rows}
    basis = [[1., 0., 0.], [0., 1., 0.], [0., 0., 1.]]
    planned = {"member": method.EXPECTED_KEY[0], "station_global_grain_projection_mm": method.EXPECTED_KEY[1],
        "expected_frozen_same_station_area_mm2": method.EXPECTED_AREA_MM2, "basis_u_v_grain_xyz": basis}
    request = {"schema": "thin_bolted_one_partial_end_geometry_readiness/v1", "candidate": method.pure.unit.CANDIDATE,
        "state_id": None, "request_count": 1, "cached_BREP_count": 1,
        "selection_source": {"sha256": method.COARSE_SHA}, "requests": [planned]}
    properties = {"member": method.EXPECTED_KEY[0], "station_global_grain_projection_mm": method.EXPECTED_KEY[1] + 1e-12,
        "state_id": None, "finished_area_mm2": method.EXPECTED_AREA_MM2 + 2e-7,
        "expected_frozen_same_station_area_mm2": method.EXPECTED_AREA_MM2, "basis_u_v_grain_xyz": basis,
        "linear_normal_stress": None, "bores_or_other_voids_restored": False, "shear_area_method_qualified": False}
    geometry = {"schema": "thin_bolted_one_partial_end_finished_geometry/v1", "candidate": method.pure.unit.CANDIDATE,
        "state_id": None, "selected_cut_count": 1, "cached_finished_BREP_count": 1, "source_pins_before_after_unchanged": True,
        "candidate_response_current_force_pressure_or_strength_consumed": False,
        "other_partial_net_tip_or_lower_subsolid_queries_executed": False,
        "requested_station_global_grain_projection_mm": method.EXPECTED_KEY[1],
        "release": {"fabrication_released": False}, "finished_sections": [properties]}
    before = copy.deepcopy((geometry, request, coarse))
    assert method.join_one(geometry, request, coarse) is properties
    assert (geometry, request, coarse) == before
    bad = copy.deepcopy(request)
    bad["requests"][0]["station_global_grain_projection_mm"] += 1e-12
    with pytest.raises(ValueError, match="exact one requested"):
        method.join_one(geometry, bad, coarse)
    for key, replacement in [("station_global_grain_projection_mm", method.EXPECTED_KEY[1] + 2e-8),
                             ("expected_frozen_same_station_area_mm2", method.EXPECTED_AREA_MM2 + 1e-8),
                             ("state_id", "foreign")]:
        bad = copy.deepcopy(geometry)
        bad["finished_sections"][0][key] = replacement
        with pytest.raises(ValueError, match="exact one requested"):
            method.join_one(bad, request, coarse)
