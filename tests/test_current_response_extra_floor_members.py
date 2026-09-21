"""Candidate-declared floor members are explicit and baseline-safe."""

import pytest

from fea.current_response_model import (
    CurrentModule,
    additional_floor_member_names,
)


class Module:
    FLOOR_BEARING_MEMBER_NAMES = ("shifted_post", "backer")


def test_additional_floor_members_require_distinct_nonlegacy_timbers():
    by_name = {"shifted_post": object(), "backer": object(), "base_header": object()}

    assert additional_floor_member_names(Module(), by_name, ()) == (
        "shifted_post",
        "backer",
    )

    Module.FLOOR_BEARING_MEMBER_NAMES = ("shifted_post", "shifted_post")
    with pytest.raises(ValueError, match="distinct"):
        additional_floor_member_names(Module(), by_name, ())

    Module.FLOOR_BEARING_MEMBER_NAMES = ("missing",)
    with pytest.raises(ValueError, match="existing non-panel"):
        additional_floor_member_names(Module(), by_name, ())

    Module.FLOOR_BEARING_MEMBER_NAMES = ("base_post_center_right",)
    with pytest.raises(ValueError, match="automatic foot"):
        additional_floor_member_names(
            Module(), by_name | {"base_post_center_right": object()}, ()
        )

    Module.FLOOR_BEARING_MEMBER_NAMES = ("backer",)
    with pytest.raises(ValueError, match="floor rail"):
        additional_floor_member_names(Module(), by_name, ("backer",))


def test_baseline_without_explicit_extra_floor_members_is_unchanged():
    module = object()
    assert additional_floor_member_names(module, {"base_header": object()}, ()) == ()


class InventoryModule:
    hardware = object()
    timber = object()
    leg_source = object()

    def __init__(self, custom=None):
        self.custom = custom

    def parts(self):
        return (
            type("Part", (), {"name": "base_header"})(),
            type("Part", (), {"name": "ignored_hardware"})(),
        )

    def current_response_wood_parts(self):
        return self.custom


class BaselineInventoryModule:
    hardware = object()
    timber = object()
    leg_source = object()

    def parts(self):
        return (
            type("Part", (), {"name": "base_header"})(),
            type("Part", (), {"name": "ignored_hardware"})(),
        )


def test_custom_response_inventory_is_opt_in_and_rejects_duplicates():
    first = type("Part", (), {"name": "shifted_post"})()
    second = type("Part", (), {"name": "backer"})()
    wrapped = CurrentModule(InventoryModule((first, second)))
    assert wrapped.wood_parts() == (first, second)

    duplicate = type("Part", (), {"name": "shifted_post"})()
    with pytest.raises(ValueError, match="unique names"):
        CurrentModule(InventoryModule((first, duplicate))).wood_parts()

    baseline = BaselineInventoryModule()
    assert [part.name for part in CurrentModule(baseline).wood_parts()] == [
        "base_header"
    ]
