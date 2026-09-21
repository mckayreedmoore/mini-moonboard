"""Developmental PB02 whole-frame adapter; no demand or fabrication release.

The active PB02 geometry replaces the old right-center post and its two legacy
clip stations. All other legacy stations remain explicit response proxies.
Native PB02 springs are sourced from the shared connected-kinematics inventory.
"""

import threading
from dataclasses import replace

import cadquery as cq
import numpy as np

from fea import current_response_model as response
from fea import round_insert_frame as shared
from fea.current_response_materials import connection_stiffnesses, materials
from fea.floor_flush_mesh import FlushStructure, prepare_flush
from fea.floor_flush_run import face_contacts, taper_top_monitors
from fea.horizontal_panel_frame import panel_kernel
from mini_moonboard.box_frame import Part
from scripts.bolted_kerf_diagnostic_probe import DiagnosticProxy
from scripts.clear_space_batch import CASES
from scripts.compact_rail_study import bolt_properties
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
_PREPARE_LOCK = threading.RLock()
_ORIGINAL_GRID = panel_kernel.grid
_ORIGINAL_PRESSURE = panel_kernel.pressure_load
_ORIGINAL_MEMBER = FlushStructure.member


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
        baseline_wood_names = {part.name for part in self.baseline.uncut_wood_parts()}
        finished = {
            part.name: part
            for part in self.baseline.parts()
            if part.name in baseline_wood_names
        }
        if set(finished) != baseline_wood_names:
            raise ValueError("Baseline finished-timber inventory changed")
        self._current_wood = tuple(
            part for name, part in finished.items() if name != REMOVED_POST
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
        return self._current_wood

    def current_response_wood_parts(self):
        """Use the candidate inventory instead of legacy name-prefix filtering."""
        return self._current_wood

    def parts(self):
        baseline_wood = {part.name for part in self.baseline.uncut_wood_parts()}
        hardware = tuple(
            part
            for part in self.baseline.parts()
            if part.name not in baseline_wood and part.name not in REMOVED_STATIONS
        )
        return (*self._current_wood, *hardware)

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


def _shifted_post_header_contacts(module, face_normal_total_n_per_mm):
    """Sample the actual shared horizontal face with normal directed into post."""
    if not np.isfinite(face_normal_total_n_per_mm) or face_normal_total_n_per_mm <= 0:
        raise ValueError("PB02 face stiffness must be positive and finite")
    raw = {part.name: part.shape for part in module.uncut_wood_parts()}
    post = raw["shifted_right_post"].BoundingBox()
    header = raw["base_header"].BoundingBox()
    if abs(post.zmax - header.zmin) > 1.0e-6:
        raise ValueError("Shifted post and header do not share a horizontal face")
    x_low, x_high = max(post.xmin, header.xmin), min(post.xmax, header.xmax)
    y_low, y_high = max(post.ymin, header.ymin), min(post.ymax, header.ymax)
    if x_high <= x_low or y_high <= y_low:
        raise ValueError("Shifted post and header have no face overlap")

    contacts = []
    for i, x_fraction in enumerate((0.25, 0.75), 1):
        for j, y_fraction in enumerate((0.25, 0.75), 1):
            point = [
                x_low + x_fraction * (x_high - x_low),
                y_low + y_fraction * (y_high - y_low),
                post.zmax,
            ]
            contacts.append(
                {
                    "name": f"pb02_shifted_post_header_compression_{i}_{j}",
                    "first": "shifted_right_post",
                    "second": "base_header",
                    "point_xyz_mm": point,
                    "normal_xyz": [0.0, 0.0, -1.0],
                    "stiffness_n_per_mm": face_normal_total_n_per_mm / 4,
                    "tributary_area_mm2": (x_high - x_low) * (y_high - y_low) / 4,
                    "developmental_only": True,
                }
            )
    return tuple(contacts)


def _imprint_points(member_contacts):
    """Place every canonical PB02 path point on both participating meshes."""
    result = {}
    for row in native_row_inventory():
        for member in (row["first_part"], row["second_part"]):
            result.setdefault(member, []).append(row["point_mm"])
    for contact in member_contacts:
        for role in ("first", "second"):
            result.setdefault(contact[role], []).append(contact["point_xyz_mm"])
    return result


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
        # Canonical rows point first-to-second, while normal_contact and its
        # ownership metadata require the contact normal inward into first.
        inward_normal = [-component for component in row["direction"]]
        shared.normal_contact(
            structure,
            row["name"],
            structure.attachment(first, point),
            [structure.attachment(second, point)],
            [1.0],
            list(point),
            inward_normal,
            face_normal_total_n_per_mm / 4,
        )
        ownership[row["name"]] = {
            "first": first,
            "second": second,
            "point": list(point),
            "scalar_normal": inward_normal,
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


def prepare_case(
    case,
    *,
    bolt_axial_n_per_mm,
    bolt_lateral_n_per_mm,
    face_normal_total_n_per_mm,
):
    """Prepare one unsolved PB02 whole frame with explicit trial stiffnesses."""
    if case not in CASES:
        raise ValueError("Unknown unchanged load case")
    trial_stiffnesses = (
        bolt_axial_n_per_mm,
        bolt_lateral_n_per_mm,
        face_normal_total_n_per_mm,
    )
    if any(not np.isfinite(value) or value <= 0 for value in trial_stiffnesses):
        raise ValueError("PB02 trial spring stiffnesses must be positive and finite")

    module = PB02Native()
    raw = {part.name: part for part in module.uncut_wood_parts()}
    panel_names = [name for name in raw if name.startswith(("main_", "kicker_"))]
    if len(panel_names) != 6:
        raise ValueError("PB02 kerf-right candidate requires six panel solids")
    post_header_contacts = _shifted_post_header_contacts(
        module, face_normal_total_n_per_mm
    )
    existing_contacts = tuple(face_contacts(module))
    if any(
        {contact["first"], contact["second"]} == {"backer", "shifted_right_post"}
        for contact in (*existing_contacts, *post_header_contacts)
    ):
        raise ValueError("PB02 preparation must not credit backer/post contact")
    member_contacts = (*existing_contacts, *post_header_contacts)
    extra_points = _imprint_points(post_header_contacts)

    bolts = {
        connection.name: bolt_properties(connection)
        for connection in module.connections()
        if connection.kind == "bolt"
    }
    if not bolts:
        raise ValueError("PB02 whole frame lost its retained bolt inventory")
    stiffnesses = {
        **connection_stiffnesses(),
        "floor": 1.0e5,
        "bearing": 1.0e6,
        "seating_per_area": 100.0,
        "bolt": {**next(iter(bolts.values())), "by_name": bolts},
    }
    original_grid, original_pressure = _ORIGINAL_GRID, _ORIGINAL_PRESSURE
    original_member = _ORIGINAL_MEMBER
    grid_calls = 0

    def kerf_grid(xs, ys):
        nonlocal grid_calls
        if grid_calls >= len(panel_names):
            raise ValueError("Unexpected panel-grid call")
        bounds = raw[panel_names[grid_calls]].shape.BoundingBox()
        xs = list(xs)
        xs[0], xs[-1] = bounds.xmin, bounds.xmax
        grid_calls += 1
        return original_grid(xs, ys)

    def kerf_pressure(nodes, elements, patch, total):
        if patch[0:2] in ((-module.b.HALF, 0.0), (0.0, module.b.HALF)):
            values = [point[0] for point in nodes.values()]
            patch = (min(values), max(values), *patch[2:])
        return original_pressure(nodes, elements, patch, total)

    def joint_member(self, record, attachment_points=(), size=100.0):
        return original_member(
            self,
            record,
            [*attachment_points, *extra_points.get(record["name"], ())],
            size,
        )

    hold, horizontal_force = CASES[case]
    with _PREPARE_LOCK:
        if (
            panel_kernel.grid is not original_grid
            or panel_kernel.pressure_load is not original_pressure
            or FlushStructure.member is not original_member
        ):
            raise RuntimeError("another model preparation has patched shared builders")
        try:
            panel_kernel.grid = kerf_grid
            panel_kernel.pressure_load = kerf_pressure
            FlushStructure.member = joint_member
            structure, metadata = prepare_flush(
                module,
                expected_candidate=module.KEY,
                materials=materials(),
                stiffnesses=stiffnesses,
                hold=hold,
                pounds=250.0,
                horizontal_force=horizontal_force,
                leg_floor_grid=3,
                patch_size=20.0,
                member_contacts=member_contacts,
                clearance_monitors=taper_top_monitors(module),
            )
        finally:
            panel_kernel.grid = original_grid
            panel_kernel.pressure_load = original_pressure
            FlushStructure.member = original_member
    if grid_calls != len(panel_names):
        raise ValueError("Incomplete kerf-right six-panel preparation")

    panel_bounds = {}
    for name, panel in structure.panels.items():
        actual = raw[name].shape.BoundingBox()
        xs = [structure.nodes[node][0] for node in panel["nodes"]]
        if abs(min(xs) - actual.xmin) > 1.0e-6 or abs(max(xs) - actual.xmax) > 1.0e-6:
            raise ValueError(f"{name}: native mesh misses kerf-right panel bounds")
        panel_bounds[name] = [actual.xmin, actual.xmax]
    if set(panel_bounds) != set(panel_names):
        raise ValueError("PB02 panel mesh inventory changed")

    add_native_paths(
        structure,
        metadata,
        bolt_axial_n_per_mm=bolt_axial_n_per_mm,
        bolt_lateral_n_per_mm=bolt_lateral_n_per_mm,
        face_normal_total_n_per_mm=face_normal_total_n_per_mm,
    )
    pb02_bolt_names = {
        row["name"].removesuffix("/tension")
        for row in native_row_inventory()
        if row["kind"] == "bolt_tension"
    }
    pb02_bolt_springs = [
        spring for spring in structure.springs if spring["name"] in pb02_bolt_names
    ]
    canonical_contacts = {
        row["name"]
        for row in native_row_inventory()
        if row["kind"] == "contact_compression"
    }
    canonical_contact_springs = [
        spring for spring in structure.springs if spring["name"] in canonical_contacts
    ]
    if (
        len(pb02_bolt_names) != 10
        or sum(spring["dof"] == 1 for spring in pb02_bolt_springs) != 10
        or sum(spring["dof"] in (2, 3) for spring in pb02_bolt_springs) != 20
        or len(canonical_contact_springs) != 28
        or any(
            not spring["bearing_closed_assumption"]
            for spring in canonical_contact_springs
        )
    ):
        raise ValueError("PB02 native spring inventory changed")

    proxy_stations = sorted(module.legacy_proxy_stations())
    floor_members = metadata.get("extra_floor_bearing_members")
    shifted_contacts = {contact["name"] for contact in post_header_contacts}
    if (
        len(proxy_stations) != 22
        or floor_members != list(module.FLOOR_BEARING_MEMBER_NAMES)
        or not shifted_contacts.issubset(metadata["connection_ownership"])
    ):
        raise ValueError("PB02 proxy, floor, or shifted-post contact inventory changed")
    metadata.update(
        pb02_case=case,
        pb02_load_source="unchanged CASES definition at 250 lb",
        pb02_geometry_source="active_geometry()",
        pb02_canonical_points_imprinted=True,
        pb02_shifted_post_header_contacts={
            "names": sorted(shifted_contacts),
            "sample_count": 4,
            "normal_xyz_into_post": [0.0, 0.0, -1.0],
            "face_normal_total_n_per_mm": face_normal_total_n_per_mm,
            "backer_post_contact_credited": False,
        },
        pb02_principal_header_bearing="preserved automatic current-response bearing",
        kerf_panel_bounds_mm=panel_bounds,
        legacy_proxy_stations=proxy_stations,
        provisional_structural_connectors="22 baseline ML24Z/SDS station proxies",
        pb02_same_case_demand=False,
        solved=False,
        qualified_for_design=False,
        actual_joint_demands_qualified=False,
        acceptance=False,
        drilling_released=False,
        preparation_only=True,
        developmental_only=True,
    )
    return structure, metadata


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
