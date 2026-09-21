"""Default current-response preparation remains semantically baseline-safe."""

from scripts import bolted_kerf_diagnostic_probe as probe

EXPECTED_MEMBERS = [
    "base_side_left",
    "base_side_right",
    "base_rail_top",
    "base_header",
    "base_post_outer_left",
    "base_post_outer_right",
    "lumber_leg_left",
    "lumber_leg_right",
    "base_principal_center_left",
    "base_post_center_left",
    "base_principal_center_right",
    "base_post_center_right",
    "base_rail_bottom_left",
    "base_rail_service_lower_left",
    "base_rail_service_upper_left",
    "base_rail_bottom_right",
    "base_rail_service_lower_right",
    "base_rail_service_upper_right",
    "base_floor_left",
    "base_floor_right",
]
EXPECTED_FLOOR_BODIES = {
    "base_floor_left",
    "base_floor_right",
    "base_post_center_left",
    "base_post_center_right",
    "base_post_outer_left",
    "base_post_outer_right",
    "lumber_leg_left",
    "lumber_leg_right",
}


def test_default_prepare_preserves_member_and_floor_support_semantics(monkeypatch):
    """Exercise the real unsolved preparer without candidate-only opt-ins."""
    prepare = probe.prepare_diagnostic
    captured = {}

    def record_metadata(module, **kwargs):
        structure, metadata = prepare(module, **kwargs)
        captured["metadata"] = metadata
        return structure, metadata

    monkeypatch.setattr(probe, "prepare_diagnostic", record_metadata)
    probe.prepare_case("a1-rear")
    metadata = captured["metadata"]

    assert [row["name"] for row in metadata["members"]] == EXPECTED_MEMBERS
    assert "extra_floor_bearing_members" not in metadata
    assert metadata["floor_rail_support"] == {
        "members": ["base_floor_left", "base_floor_right"],
        "grid_yx": [7, 2],
        "normal_penalty_per_body_n_per_mm": 400000.0,
        "scope": (
            "Equal-area midpoint normal contacts at actual member stations; "
            "unchanged total normal penalty per body; centroid no-slip spring "
            "conditional on bearing. No floor property qualification."
        ),
    }
    floor_rows = [
        row
        for row in metadata["connection_ownership"].values()
        if row.get("second") == "floor"
    ]
    assert len(floor_rows) == 70
    assert {row["first"] for row in floor_rows} == EXPECTED_FLOOR_BODIES
