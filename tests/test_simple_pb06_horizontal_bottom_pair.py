"""PB06 bottom-center detached trial remains source-bound and unreleased."""

from scripts import simple_pb06_horizontal_bottom_pair as trial


def test_signed_projection_preserves_negative_outside_margin():
    import cadquery as cq

    shape = cq.Solid.makeBox(10, 10, 10)
    margins = trial._margin(shape, (-1, 5, 5), "t")
    assert margins["x_low"] == -1


def test_bottom_pair_trial():
    report = trial.screen()
    assert report["target_stations"] == list(trial.TARGET_STATIONS)
    assert report["inventory"] == {
        "existing_blocks": 10,
        "candidate_blocks": 2,
        "candidate_bolts": 8,
        "target_sds_axes_retained": 12,
        "other_sds_axes_retained": 60,
        "frame_axes": 12,
        "panel_kicker_axes": 66,
    }
    assert len(report["pb06_source_fingerprint_sha256"]) == 64
    assert report["decision"] == "REVISE"
    assert len(report["binding_constraints"]) >= 3
    assert (
        sum("incomplete nominal bore" in row for row in report["binding_constraints"])
        == 2
    )
    assert any("upright_side_cleat" in row for row in report["binding_constraints"])
    assert all(
        report[field] is False
        for field in (
            "strength_checked",
            "exact_retail_hardware_selected",
            "drilling_released",
            "fabrication_released",
        )
    )
