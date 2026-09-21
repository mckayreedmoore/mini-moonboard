"""Developmental PB02 whole-frame adapter; no demand or fabrication release.

The active PB02 geometry replaces the old right-center post and its two legacy
clip stations. All other legacy stations remain explicit response proxies.
Native PB02 springs are sourced from the shared connected-kinematics inventory.
"""

from dataclasses import replace

import cadquery as cq
import numpy as np

from fea import current_response_model as response
from fea import round_insert_frame as shared
from mini_moonboard.box_frame import Part
from scripts.bolted_kerf_diagnostic_probe import DiagnosticProxy
from scripts.simple_center_connected_kinematics import (
    EDGES,
    NODE_PARTS,
    constraint_rows,
)
from scripts.simple_center_current_placement_table import GRAIN_AXIS
from scripts.simple_center_pb02_geometry import ACTIVE_FINGERPRINT, active_geometry

CANDIDATE_ID = "pb02-kerf-right-native-development-only"
REMOVED_POST = "base_post_center_right"
REMOVED_STATIONS = frozenset(
    {"clip_split_base_center_right", "clip_split_header_center_right"}
)
NEW_MEMBERS = (
    "shifted_right_post",
    "backer",
    "rear_cleat",
    "upright_side_cleat",
    "header_post_side_cleat",
    "header_side_cleat",
)
RETARGETED_PANEL_CONNECTIONS = frozenset(
    {"round_kicker_right_center_1", "round_kicker_right_center_2"}
)
LOCAL_GRAIN_AXIS = {**GRAIN_AXIS, "backer": "z"}
_AXIS_VECTOR = {
    "x": (cq.Vector(1, 0, 0), cq.Vector(0, 1, 0)),
    "y": (cq.Vector(0, 1, 0), cq.Vector(1, 0, 0)),
    "z": (cq.Vector(0, 0, 1), cq.Vector(1, 0, 0)),
}


def _new_part(name, shape):
    """Wrap an active PB02 solid without implying a fabrication blank."""
    bounds = shape.BoundingBox()
    dimensions = {"x": bounds.xlen, "y": bounds.ylen, "z": bounds.zlen}
    grain = LOCAL_GRAIN_AXIS[name]
    cross = sorted(
        (value for axis, value in dimensions.items() if axis != grain), reverse=True
    )
    blank = (dimensions[grain], *cross)
    return Part(
        name,
        shape,
        blank,
        "Active PB02 developmental solid; blank, machining, resistance, and release "
        "remain unqualified",
        1,
    )


class PB02Native(DiagnosticProxy):
    """Kerf-right PB02 timber with 22 retained legacy connector proxies."""

    KEY = CANDIDATE_ID
    ACTIVE_FINGERPRINT = ACTIVE_FINGERPRINT
    FLOOR_BEARING_MEMBER_NAMES = ("shifted_right_post", "backer", "rear_cleat")

    def __init__(self):
        super().__init__()
        shapes, _, _ = active_geometry()
        source = {part.name: part for part in self.raw.uncut_wood_parts()}
        expected = (set(source) - {REMOVED_POST}) | set(NEW_MEMBERS)
        if set(shapes) != expected:
            raise ValueError("Active PB02 whole-frame timber inventory changed")
        # active_geometry() owns the six changed PB02 solids, but its unchanged
        # frame comes from the official-width model. Preserve every unchanged
        # kerf-right part and overlay only the PB02 replacement/additions.
        self._wood = tuple(
            part for part in source.values() if part.name != REMOVED_POST
        ) + tuple(_new_part(name, shapes[name]) for name in NEW_MEMBERS)
        self.MEMBER_AXES = {
            **getattr(self.baseline, "MEMBER_AXES", {}),
            **{name: _AXIS_VECTOR[LOCAL_GRAIN_AXIS[name]] for name in NEW_MEMBERS},
        }
        self.NATIVE_SQUARE_END_MEMBERS = (
            *getattr(self.baseline, "NATIVE_SQUARE_END_MEMBERS", ()),
            *NEW_MEMBERS,
        )

    def uncut_wood_parts(self):
        return self._wood

    def wood_parts(self):
        """Expose all PB02 timbers for candidate-aware whole-frame consumers."""
        return self._wood

    def current_response_wood_parts(self):
        """Use the candidate inventory instead of legacy name-prefix filtering."""
        return self._wood

    def parts(self):
        baseline_wood = {part.name for part in self.baseline.uncut_wood_parts()}
        hardware = tuple(
            part
            for part in self.baseline.parts()
            if part.name not in baseline_wood and part.name not in REMOVED_STATIONS
        )
        return (*self._wood, *hardware)

    @staticmethod
    def _connection(connection):
        if connection.name in RETARGETED_PANEL_CONNECTIONS:
            if connection.members != ("kicker_right", REMOVED_POST):
                raise ValueError("Right-center kicker receiver identity changed")
            return replace(connection, members=("kicker_right", "backer"))
        return connection

    def connections(self):
        return tuple(
            self._connection(connection)
            for connection in self.baseline.connections()
            if not (
                connection.name.startswith("clip_")
                and connection.members[0] in REMOVED_STATIONS
            )
        )

    def panel_connections(self):
        panel_names = {row.name for row in self.raw.panel_connections()}
        return tuple(row for row in self.connections() if row.name in panel_names)

    def stations(self):
        return tuple(
            row for row in super().stations() if row[0] not in REMOVED_STATIONS
        )

    def legacy_proxy_stations(self):
        return tuple(row[0] for row in self.stations())


def native_row_inventory():
    """Return the authoritative PB02 spring rows without solver-only matrices."""
    rows = constraint_rows(closed=tuple(EDGES))
    result = []
    for row in rows:
        result.append(
            {key: value for key, value in row.items() if key != "row"}
            | {
                "first_part": NODE_PARTS[row["first"]],
                "second_part": NODE_PARTS[row["second"]],
            }
        )
    counts = {
        kind: sum(row["kind"] == kind for row in result)
        for kind in ("bolt_shear", "bolt_tension", "contact_compression")
    }
    if counts != {
        "bolt_shear": 20,
        "bolt_tension": 10,
        "contact_compression": 28,
    }:
        raise ValueError("PB02 connected-kinematics row inventory changed")
    return tuple(result)


def add_native_paths(
    structure,
    metadata,
    *,
    bolt_axial_n_per_mm,
    bolt_lateral_n_per_mm,
    face_normal_total_n_per_mm,
):
    """Add PB02 developmental springs to an already meshed whole frame."""
    values = (
        bolt_axial_n_per_mm,
        bolt_lateral_n_per_mm,
        face_normal_total_n_per_mm,
    )
    if any(not np.isfinite(value) or value <= 0 for value in values):
        raise ValueError("PB02 trial spring stiffnesses must be positive and finite")

    rows = native_row_inventory()
    ownership = metadata.setdefault("connection_ownership", {})
    tension_rows = [row for row in rows if row["kind"] == "bolt_tension"]
    contacts = [row for row in rows if row["kind"] == "contact_compression"]

    for row in tension_rows:
        name = row["name"].removesuffix("/tension")
        point = row["point_mm"]
        first, second = row["first_part"], row["second_part"]
        owner = {
            "first": first,
            "second": second,
            "point": list(point),
            "axis": list(row["direction"]),
            "edge": row["edge"],
            "source_rows": [
                item["name"] for item in rows if item["name"].startswith(f"{name}/")
            ],
            "developmental_only": True,
        }
        response.directional_connector(
            structure,
            structure.attachment(first, point),
            structure.attachment(second, point),
            {
                "axial_n_per_mm": bolt_axial_n_per_mm,
                "lateral_n_per_mm": bolt_lateral_n_per_mm,
            },
            name,
            owner,
        )
        axial = [
            spring
            for spring in structure.springs
            if spring["name"] == name and spring["dof"] == 1
        ]
        if len(axial) != 1:
            raise ValueError("Expected one PB02 axial spring per bolt")
        axial[0]["bearing_closed_assumption"] = True
        axial[0]["tension_only_assumption"] = True
        ownership[name] = owner

    for row in contacts:
        point = row["point_mm"]
        first, second = row["first_part"], row["second_part"]
        shared.normal_contact(
            structure,
            row["name"],
            structure.attachment(first, point),
            [structure.attachment(second, point)],
            [1.0],
            list(point),
            list(row["direction"]),
            face_normal_total_n_per_mm / 4,
        )
        ownership[row["name"]] = {
            "first": first,
            "second": second,
            "point": list(point),
            "scalar_normal": list(row["direction"]),
            "edge": row["edge"],
            "developmental_only": True,
        }

    metadata.update(
        pb02_candidate=CANDIDATE_ID,
        pb02_active_fingerprint=ACTIVE_FINGERPRINT,
        pb02_native_row_counts={
            "bolt_shear": 20,
            "bolt_tension_only": 10,
            "contact_compression": 28,
        },
        pb02_trial_stiffness_n_per_mm={
            "bolt_axial": bolt_axial_n_per_mm,
            "bolt_lateral": bolt_lateral_n_per_mm,
            "face_normal_total_per_interface": face_normal_total_n_per_mm,
        },
        qualified_for_design=False,
        acceptance=False,
        drilling_released=False,
        developmental_only=True,
    )


def screen():
    """Lightweight source-bound inventory check; does not prepare or solve FEA."""
    module = PB02Native()
    panels = module.panel_connections()
    baseline_panels = {row.name: row for row in module.raw.panel_connections()}
    current_panels = {row.name: row for row in panels}
    moved_axes = [
        name
        for name in baseline_panels
        if (
            current_panels[name].start != baseline_panels[name].start
            or current_panels[name].direction != baseline_panels[name].direction
            or current_panels[name].length != baseline_panels[name].length
        )
    ]
    changed_receivers = {
        name
        for name in baseline_panels
        if current_panels[name].members != baseline_panels[name].members
    }
    rows = native_row_inventory()
    result = {
        "candidate": CANDIDATE_ID,
        "active_fingerprint": ACTIVE_FINGERPRINT,
        "timber_count": len(module.uncut_wood_parts()),
        "removed_post": REMOVED_POST,
        "new_members": list(NEW_MEMBERS),
        "panel_kicker_axis_count": len(panels),
        "moved_panel_kicker_axes": moved_axes,
        "changed_panel_kicker_receivers": sorted(changed_receivers),
        "right_center_receivers": {
            name: current_panels[name].members[1]
            for name in sorted(RETARGETED_PANEL_CONNECTIONS)
        },
        "removed_legacy_stations": sorted(REMOVED_STATIONS),
        "legacy_proxy_station_count": len(module.legacy_proxy_stations()),
        "native_rows": {
            kind: sum(row["kind"] == kind for row in rows)
            for kind in ("bolt_shear", "bolt_tension", "contact_compression")
        },
        "developmental_only": True,
        "qualified_for_design": False,
        "drilling_released": False,
    }
    if (
        result["panel_kicker_axis_count"] != 66
        or moved_axes
        or changed_receivers != RETARGETED_PANEL_CONNECTIONS
        or set(result["right_center_receivers"].values()) != {"backer"}
        or result["legacy_proxy_station_count"] != 22
    ):
        raise ValueError("PB02 whole-frame candidate inventory changed")
    return result


if __name__ == "__main__":
    import json

    print(json.dumps(screen(), indent=2))
