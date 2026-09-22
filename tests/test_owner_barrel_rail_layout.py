"""Direct cross-dowel ten-rail layout is evidence, never a drilling packet."""

from scripts import owner_barrel_rail_layout as barrel


def test_direct_barrel_layout_keeps_fixed_axes_and_reports_each_duty():
    result = barrel.screen()
    assert result["source_id"] == barrel.SOURCE_ID
    assert result["parent_source_id"] == barrel.pb07.SOURCE_ID
    assert result["inventory"] == {
        "rail_duties": 10,
        "panel_kicker_axes": 66,
        "retained_frame_bolt_axes": 12,
        "candidate_brackets": 0,
    }
    assert set(result["stations"]) == set(barrel.STATIONS)
    assert result["protected_inventory_counts"] == {
        "tnuts": 142,
        "hold_hole_and_trial_projection": 142,
        "lights": 132,
        "wires": 131,
        "panel_screws": 66,
        "frame_bolts": 12,
    }
    assert all(row["rail_n_depth_mm"] == 139.7 for row in result["stations"].values())
    assert all(row["fastener_count"] == 2 for row in result["stations"].values())
    assert all(
        row["machine_bore_meets_barrel_bore"]
        for row in result["stations"].values()
        if row["direct_butt_available"]
    )
    assert all(
        result["stations"][name]["compact_alternate"] is not None
        for name in barrel.CENTER_STATIONS
        if not result["stations"][name]["direct_butt_available"]
    )
    assert result["disposition"] == "DEVELOPMENT_REVISE"
    assert result["manufacturer_contacted"] is False
    assert result["strength_qualified"] is False
    assert result["fit_qualified"] is False
    assert result["drilling_released"] is False
    assert result["fabrication_released"] is False


def test_assembly_adapter_uses_supplied_wood_and_distinct_trial_solids(monkeypatch):
    pose = {
        "station": "trial",
        "rows": (
            {
                "name": "trial_barrel_1",
                "wood_seat": "seat",
                "bolt_direction": "direction",
                "bolt": "shaft",
                "barrel": "body",
                "machine_bore": "long_bore",
                "barrel_bore": "cross_bore",
                "bolt_access": "drive",
                "barrel_access": "insert",
            },
        ),
        "spec": type("Spec", (), {"upright_name": "upright", "rail_name": "rail"})(),
        "alternate_block": "visible_cleat",
    }
    supplied = {"upright": "owner_upright", "rail": "owner_rail"}

    def fake_build(wood=None):
        assert wood is supplied
        return {"stations": {"trial": pose}}

    monkeypatch.setattr(barrel, "build_geometry", fake_build)
    monkeypatch.setattr(
        barrel,
        "screen",
        lambda built=None: {
            "stations": {"trial": {"geometry_status": "DIRECT_TRIAL_BLOCKED"}},
            "disposition": "DEVELOPMENT_REVISE",
        },
    )
    monkeypatch.setattr(barrel, "_connection", lambda row, spec: "bolt_axis")
    layout = barrel.build_layout(supplied)
    row = layout["stations"]["trial"]
    assert row["mode"] == "mixed"
    assert row["compact_alternate_block"] == "visible_cleat"
    assert row["axis_offset_mm"] == 8.001
    assert row["disposition"] == "DIRECT_TRIAL_BLOCKED"
    assert row["bolts"] == {"trial_barrel_1_bolt": "bolt_axis"}
    assert row["barrels"] == {"trial_barrel_1": "body"}
    assert row["stacks"] == {"trial_barrel_1_bolt": {"shaft": "shaft"}}
    assert set(row["drilling_paths"]) == {
        "trial_barrel_1/machine_bore",
        "trial_barrel_1/barrel_bore",
    }
    assert set(row["access_paths"]) == {
        "trial_barrel_1/bolt_access",
        "trial_barrel_1/barrel_access",
    }
