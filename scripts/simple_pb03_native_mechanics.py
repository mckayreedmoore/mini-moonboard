"""Bounded PB03 eight-station native mechanics; no solve or release.

The ordinary current-frame preparer already creates the PB03 directional bolt
connectors. This adapter supplies exact interface points, four-cell face-contact
records, explicit block member axes, and a post-prepare unilateral-law gate.
It never creates a second PB03 bolt connector.
"""

import hashlib
import json
import math

import cadquery as cq
import numpy as np

from scripts import simple_rail_joint_comparison as pb01
from scripts.simple_pb03_native import (
    BLOCK_NAMES,
    REPLACED_STATIONS,
    SOURCE_ID,
    PB03Native,
)

MECHANICS_SOURCE_ID = "pb03-eight-station-native-mechanics-v2"
_CONTACT_EPSILON_MM = 0.1
_CONTACT_GRID = (2, 2)


def _unit(vector):
    result = np.asarray(vector, dtype=float)
    length = float(np.linalg.norm(result))
    if not np.isfinite(result).all() or not math.isclose(length, 1.0, abs_tol=1e-9):
        raise ValueError("PB03 mechanics axis must be a finite unit vector")
    return result


def _contact_cells(block, host, inward_into_block, expected_area):
    """Partition one actual rectangular face into four tributary point cells."""
    normal = _unit(inward_into_block)
    block_to_host = -normal
    overlap = block.translate(tuple(block_to_host * _CONTACT_EPSILON_MM)).intersect(
        host
    )
    area = float(overlap.Volume()) / _CONTACT_EPSILON_MM
    if area <= 0 or not math.isclose(area, expected_area, abs_tol=1e-4):
        raise ValueError("PB03 mechanics contact face changed")

    if abs(normal[0]) > 1.0 - 1e-9:
        first_tangent = np.asarray((0.0, *pb01.T))
        second_tangent = np.asarray((0.0, *pb01.N))
    else:
        first_tangent = np.asarray((1.0, 0.0, 0.0))
        second_tangent = np.cross(normal, first_tangent)
    vertices = np.asarray([vertex.Center().toTuple() for vertex in overlap.Vertices()])
    first_bounds = (vertices @ first_tangent).min(), (vertices @ first_tangent).max()
    second_bounds = (vertices @ second_tangent).min(), (vertices @ second_tangent).max()
    rectangle_area = (first_bounds[1] - first_bounds[0]) * (
        second_bounds[1] - second_bounds[0]
    )
    if not math.isclose(rectangle_area, area, abs_tol=1e-4):
        raise ValueError("PB03 mechanics contact is not one rectangular face")

    plane_coordinate = float(np.asarray(overlap.Center().toTuple()) @ normal)
    plane_coordinate += _CONTACT_EPSILON_MM / 2
    cells = []
    for row, first_fraction in enumerate((0.25, 0.75), 1):
        for column, second_fraction in enumerate((0.25, 0.75), 1):
            first = first_bounds[0] + first_fraction * (
                first_bounds[1] - first_bounds[0]
            )
            second = second_bounds[0] + second_fraction * (
                second_bounds[1] - second_bounds[0]
            )
            point = (
                normal * plane_coordinate
                + first_tangent * first
                + second_tangent * second
            )
            cells.append((row, column, point, area / 4))
    return tuple(cells)


def _bolt_face_point(connection, face_point, face_normal):
    """Intersect an existing bolt axis with its exact block/member face plane."""
    axis = _unit(connection.direction.toTuple())
    start = np.asarray(connection.start.toTuple(), dtype=float)
    normal = _unit(face_normal)
    denominator = float(axis @ normal)
    if abs(denominator) < 1.0 - 1e-9:
        raise ValueError("PB03 bolt axis is not normal to its contact face")
    distance = float((np.asarray(face_point) - start) @ normal / denominator)
    return start + distance * axis, axis


def _build_rows(module):
    parts = {part.name: part.shape for part in module.uncut_wood_parts()}
    rows = []
    for station, geometry in module.pb03_geometries().items():
        interface_data = {}
        for interface, host_name in (
            ("upright", geometry.upright_name),
            ("rail", geometry.rail_name),
        ):
            interface_bolts = [
                bolt
                for bolt in geometry.bolts
                if bolt.members == (host_name, geometry.block_name)
            ]
            if len(interface_bolts) != 2:
                raise ValueError("PB03 mechanics requires two bolts per interface")
            normal = _unit(interface_bolts[0].direction.toTuple())
            if any(
                not np.allclose(
                    _unit(bolt.direction.toTuple()), normal, atol=1e-9, rtol=0
                )
                for bolt in interface_bolts
            ):
                raise ValueError("PB03 interface bolt directions changed")
            cells = _contact_cells(
                geometry.block,
                parts[host_name],
                normal,
                geometry.report["contact_area_mm2"][interface],
            )
            interface_data[interface] = (cells[0][2], normal)
            for grid_row, grid_column, point, tributary_area in cells:
                rows.append(
                    {
                        "name": (
                            f"{geometry.block_name}_{interface}_contact_"
                            f"{grid_row}_{grid_column}"
                        ),
                        "kind": "contact_compression",
                        "station": station,
                        "interface": interface,
                        "first_part": geometry.block_name,
                        "second_part": host_name,
                        "point_mm": point.tolist(),
                        "direction": normal.tolist(),
                        "tributary_area_mm2": tributary_area,
                        "developmental_only": True,
                    }
                )

        for bolt in geometry.bolts:
            if bolt.members[1] != geometry.block_name:
                raise ValueError("PB03 bolt no longer terminates at its timber block")
            interface = (
                "upright"
                if bolt.members[0] == geometry.upright_name
                else "rail"
                if bolt.members[0] == geometry.rail_name
                else None
            )
            if interface is None:
                raise ValueError("PB03 bolt host identity changed")
            face_point, face_normal = interface_data[interface]
            point, axis = _bolt_face_point(bolt, face_point, face_normal)
            rows.append(
                {
                    "name": bolt.name,
                    "kind": "bolt",
                    "station": station,
                    "interface": interface,
                    "first_part": bolt.members[0],
                    "second_part": bolt.members[1],
                    "point_mm": point.tolist(),
                    "direction": axis.tolist(),
                    "developmental_only": True,
                }
            )
    return tuple(rows)


def _identity_payload(rows, module):
    fingerprint = hashlib.sha256(
        json.dumps(rows, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    return {
        "mechanics_source_id": MECHANICS_SOURCE_ID,
        "pb03_source_id": SOURCE_ID,
        "pb02_source_fingerprint": module.ACTIVE_FINGERPRINT,
        "replaced_stations": list(REPLACED_STATIONS),
        "legacy_proxy_stations": len(module.legacy_proxy_stations()),
        "fixed_panel_kicker_axes": len(module.panel_connections()),
        "contact_grid": list(_CONTACT_GRID),
        "row_fingerprint_sha256": fingerprint,
    }


def native_row_inventory(module=None):
    """Return source-bound PB03 contact cells and existing bolt-axis rows."""
    module = PB03Native() if module is None else module
    if module.KEY != SOURCE_ID or tuple(module.pb03_geometries()) != REPLACED_STATIONS:
        raise ValueError("PB03 mechanics source identity changed")
    if (
        len(module.legacy_proxy_stations()) != 14
        or len(module.panel_connections()) != 66
    ):
        raise ValueError("PB03 retained legacy or fixed-axis inventory changed")
    rows = _build_rows(module)
    names = [row["name"] for row in rows]
    if (
        len(rows) != 96
        or len(names) != len(set(names))
        or sum(row["kind"] == "contact_compression" for row in rows) != 64
        or sum(row["kind"] == "bolt" for row in rows) != 32
    ):
        raise ValueError("PB03 mechanics row inventory changed")
    return rows, _identity_payload(rows, module)


def native_member_contacts(face_normal_total_n_per_mm, module=None, row_inventory=None):
    """Build four-cell contact records for the ordinary frame preparer."""
    if not np.isfinite(face_normal_total_n_per_mm) or face_normal_total_n_per_mm <= 0:
        raise ValueError("PB03 face stiffness must be positive and finite")
    module = PB03Native() if module is None else module
    rows, identity = (
        native_row_inventory(module) if row_inventory is None else row_inventory
    )
    contacts = [row for row in rows if row["kind"] == "contact_compression"]
    mean_interface_area = sum(row["tributary_area_mm2"] for row in contacts) / 16
    stiffness_per_area = face_normal_total_n_per_mm / mean_interface_area
    records = tuple(
        {
            "name": row["name"],
            "first": row["first_part"],
            "second": row["second_part"],
            "point_xyz_mm": row["point_mm"],
            "normal_xyz": row["direction"],
            "stiffness_n_per_mm": stiffness_per_area * row["tributary_area_mm2"],
            "tributary_area_mm2": row["tributary_area_mm2"],
            "developmental_only": True,
        }
        for row in contacts
    )
    return records, {
        "identity": identity,
        "law": "four equal-area centroid cells per face with common areal density",
        "common_areal_density_n_per_mm3": stiffness_per_area,
        "input_mean_total_per_interface_n_per_mm": face_normal_total_n_per_mm,
        "rotation_and_partial_opening_resolved": True,
    }


def activate_existing_paths(structure, metadata, module=None, row_inventory=None):
    """Mark preparer-owned PB03 axial springs tension-only without duplicating them."""
    module = PB03Native() if module is None else module
    rows, identity = (
        native_row_inventory(module) if row_inventory is None else row_inventory
    )
    ownership = metadata.get("connection_ownership", {})
    before = len(structure.springs)

    for row in (row for row in rows if row["kind"] == "bolt"):
        springs = [
            spring for spring in structure.springs if spring["name"] == row["name"]
        ]
        if len(springs) != 3 or {spring["dof"] for spring in springs} != {1, 2, 3}:
            raise ValueError("PB03 requires exactly one existing directional connector")
        owner = ownership.get(row["name"])
        if (
            owner is None
            or owner.get("first") != row["first_part"]
            or owner.get("second") != row["second_part"]
        ):
            raise ValueError("PB03 existing bolt ownership changed")
        if not np.allclose(
            owner.get("point"), row["point_mm"], atol=1e-7, rtol=0
        ) or not np.allclose(owner.get("axis"), row["direction"], atol=1e-9, rtol=0):
            raise ValueError("PB03 existing bolt point or axis is not exact")
        axial = next(spring for spring in springs if spring["dof"] == 1)
        axial["bearing_closed_assumption"] = True
        axial["tension_only_assumption"] = True
        owner.update(
            station=row["station"], interface=row["interface"], developmental_only=True
        )

    for row in (row for row in rows if row["kind"] == "contact_compression"):
        springs = [
            spring for spring in structure.springs if spring["name"] == row["name"]
        ]
        owner = ownership.get(row["name"])
        if (
            len(springs) != 1
            or springs[0]["dof"] != 1
            or not springs[0]["bearing_closed_assumption"]
        ):
            raise ValueError("PB03 four-cell contact inventory changed")
        if (
            owner is None
            or owner.get("first") != row["first_part"]
            or owner.get("second") != row["second_part"]
        ):
            raise ValueError("PB03 contact ownership changed")
        if not np.allclose(
            owner.get("point"), row["point_mm"], atol=1e-7, rtol=0
        ) or not np.allclose(
            owner.get("scalar_normal"), row["direction"], atol=1e-9, rtol=0
        ):
            raise ValueError("PB03 contact point or normal changed")
        owner.update(
            station=row["station"],
            interface=row["interface"],
            tributary_area_mm2=row["tributary_area_mm2"],
            developmental_only=True,
        )

    if len(structure.springs) != before:
        raise ValueError("PB03 activation must not create connector duplicates")
    metadata.update(
        pb03_candidate=SOURCE_ID,
        pb03_mechanics_identity=identity,
        pb03_native_row_counts={
            "existing_bolt_axes": 32,
            "bolt_tension_only": 32,
            "existing_bolt_lateral": 64,
            "contact_compression_cells": 64,
        },
        qualified_for_design=False,
        acceptance=False,
        drilling_released=False,
        fabrication_released=False,
        developmental_only=True,
    )
    return identity


class PB03MechanicsNative(PB03Native):
    """PB03 geometry with explicit block axes and exact bolt interface points."""

    def __init__(self):
        super().__init__()
        block_grain = cq.Vector(0.0, *pb01.N)
        section_u = cq.Vector(1.0, 0.0, 0.0)
        self.MEMBER_AXES = {
            **self.MEMBER_AXES,
            **{
                block_name: (block_grain, section_u)
                for block_name in BLOCK_NAMES.values()
            },
        }
        self.NATIVE_SQUARE_END_MEMBERS = (
            *self.NATIVE_SQUARE_END_MEMBERS,
            *BLOCK_NAMES.values(),
        )
        self._pb03_interface_points = {
            row["name"]: cq.Vector(*row["point_mm"])
            for row in _build_rows(self)
            if row["kind"] == "bolt"
        }

    def bolt_interface_point(self, connection):
        """Use exact PB03 planes; retain the ordinary point for other bolts."""
        point = self._pb03_interface_points.get(connection.name)
        if point is not None:
            return point
        return connection.start + connection.direction * (2.032 + 38.1)
