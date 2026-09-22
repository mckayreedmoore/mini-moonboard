"""Focused preparation checks for optional header bearings and clip-named bolts."""

from dataclasses import replace

from scripts import bolted_kerf_diagnostic_probe as probe


def _prepare_case(monkeypatch, *, implicit_header_bearings=None):
    original = probe.prepare_diagnostic
    captured = {}

    def record(module, **kwargs):
        if implicit_header_bearings is not None:
            kwargs["implicit_header_bearings"] = implicit_header_bearings
        structure, metadata = original(module, **kwargs)
        captured["result"] = structure, metadata
        return structure, metadata

    with monkeypatch.context() as patcher:
        patcher.setattr(probe, "prepare_diagnostic", record)
        probe.prepare_case("a1-rear")
    return captured["result"]


def test_header_bearings_default_on_and_explicitly_skippable(monkeypatch):
    default_structure, default_metadata = _prepare_case(monkeypatch)
    explicit_structure, explicit_metadata = _prepare_case(
        monkeypatch, implicit_header_bearings=True
    )
    without_structure, without_metadata = _prepare_case(
        monkeypatch, implicit_header_bearings=False
    )

    default_bearings = {
        row["name"] for row in default_structure.springs
        if row["name"].startswith("bearing_base_")
    }
    assert default_bearings
    assert default_bearings == {
        name for name in default_metadata["connection_ownership"]
        if name.startswith("bearing_base_")
    }
    assert [row["name"] for row in default_structure.springs] == [
        row["name"] for row in explicit_structure.springs
    ]
    assert default_metadata["header_bearing_assumption"] == explicit_metadata[
        "header_bearing_assumption"
    ]
    assert not any(
        row["name"].startswith("bearing_base_") for row in without_structure.springs
    )
    assert not any(
        name.startswith("bearing_base_")
        for name in without_metadata["connection_ownership"]
    )
    # Seating names include generated node indices, which shift with mesh stations.
    for structure in (default_structure, without_structure):
        assert any(row["name"].startswith("seating_") for row in structure.springs)
    assert {
        row["name"] for row in default_structure.springs
        if not row["name"].startswith(("bearing_base_", "seating_"))
    } == {
        row["name"] for row in without_structure.springs
        if not row["name"].startswith("seating_")
    }
    assert len(without_structure.members["base_header"]["sections"]) < len(
        default_structure.members["base_header"]["sections"]
    )


def test_clip_named_bolt_uses_bolt_path_and_legacy_clip_screws_remain(monkeypatch):
    original_proxy = probe.DiagnosticProxy
    old_name = "rail_front_bolt_left_1"
    new_name = "clip_native_bolt_left_1"

    class ClipBoltProxy(original_proxy):
        def connections(self):
            return tuple(
                replace(connection, name=new_name)
                if connection.name == old_name else connection
                for connection in super().connections()
            )

        def bolt_interface_point(self, connection):
            if connection.name == new_name:
                connection = replace(connection, name=old_name)
            return super().bolt_interface_point(connection)

    with monkeypatch.context() as patcher:
        patcher.setattr(probe, "DiagnosticProxy", ClipBoltProxy)
        structure, metadata = _prepare_case(patcher)

    owner = metadata["connection_ownership"][new_name]
    assert (owner["first"], owner["second"]) == (
        "base_post_outer_left", "base_floor_left"
    )
    assert sum(row["name"] == new_name for row in structure.springs) == 3
    legacy_clip = next(
        name for name in metadata["connection_ownership"]
        if name.startswith("clip_") and name != new_name
    )
    assert metadata["connection_ownership"][legacy_clip]["second"].startswith("clip_")
