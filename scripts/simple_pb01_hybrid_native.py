"""Preparation-only kerf-right PB01 cleat in an old-connector hybrid frame.

The other 23 ML24Z stations are explicit proxies. This module never runs a
native case, reports V4 demands, selects hardware, or approves capacity.
"""

import json
import math
import threading
from pathlib import Path

import cadquery as cq
import numpy as np

from fea import current_response_model as base
from fea import round_insert_frame as shared
from fea.current_response_materials import connection_stiffnesses, materials
from fea.floor_flush_mesh import FlushStructure, prepare_flush
from fea.floor_flush_run import face_contacts, taper_top_monitors
from fea.horizontal_panel_frame import add_load, panel_kernel
from scripts.bolted_kerf_diagnostic_probe import DiagnosticProxy
from scripts.clear_space_batch import CASES
from scripts.compact_rail_study import bolt_properties

ROOT = Path(__file__).resolve().parents[1]
DIAGNOSTIC = ROOT / "docs/bolted-candidate-prototypes/simple_rail_joint_comparison.json"
STATION = "clip_horizontal_lower_right_1"
CLEAT = "base_cleat_pb01"
UPRIGHT = "base_principal_center_right"
RAIL = "base_rail_service_lower_right"
ANGLE = math.radians(50)
T = np.array([0.0, math.cos(ANGLE), math.sin(ANGLE)])
N = np.array([0.0, -math.sin(ANGLE), math.cos(ANGLE)])
_PREPARE_LOCK = threading.RLock()
_ORIGINAL_GRID = panel_kernel.grid
_ORIGINAL_PRESSURE = panel_kernel.pressure_load
_ORIGINAL_MEMBER = FlushStructure.member


def _trial_bolt_mass_kg(length_mm):
    """Diagnostic steel mass, not a selected product or complete stack fit."""
    shaft_d, washer_od, washer_id = 9.525, 25.4, 10.5
    end_d, head_h, nut_h, washer_h = 16.51, 6.8072, 8.5598, 2.5
    area = lambda diameter: math.pi * (diameter / 2) ** 2
    volume = (
        area(shaft_d) * length_mm
        + 2 * (area(washer_od) - area(washer_id)) * washer_h
        + area(end_d) * head_h
        + (area(end_d) - area(shaft_d)) * nut_h
    )
    return volume * 7.85e-6


def _trial() -> dict:
    data = json.loads(DIAGNOSTIC.read_text())
    if data["station"] != STATION or data["physical_width"] != "kerf-right":
        raise ValueError("PB01 diagnostic source identity changed")
    pose = data["cleat_grain_n_4x6_group"]
    if pose["status"] != "diagnostic_pose_only":
        raise ValueError("PB01 four-bolt pose is not a diagnostic pose")
    if (
        len(pose["bolt_groups"]["upright"]) != 2
        or len(pose["bolt_groups"]["rail"]) != 2
    ):
        raise ValueError("PB01 requires two trial bolts on each serial interface")
    return pose


def _cleat_part(raw_parts, pose):
    by_name = {part.name: part for part in raw_parts}
    upright = by_name[UPRIGHT].shape
    rail = by_name[RAIL].shape
    t_face = max(np.dot(T, v.Center().toTuple()) for v in rail.Vertices())
    n_front = min(np.dot(N, v.Center().toTuple()) for v in rail.Vertices())
    x_width, t_width, n_length = pose["size_local_x_t_n_mm"]
    if not np.allclose((x_width, t_width, n_length), (139.7, 57.15, 300.0)):
        raise ValueError("PB01 trial cleat dimensions changed")
    x = upright.BoundingBox().xmax
    origin = T * t_face + N * n_front
    shape = (
        cq.Solid.makeBox(x_width, t_width, n_length, cq.Vector(x, 0, 0))
        .rotate((0, 0, 0), (1, 0, 0), 50)
        .translate((0, float(origin[1]), float(origin[2])))
    )
    return by_name[UPRIGHT].__class__(
        CLEAT,
        shape,
        (x_width, t_width, n_length),
        "Diagnostic grain-N solid cleat; not a cut list or accepted joint",
        1,
    )


class HybridPB01(DiagnosticProxy):
    """One physical PB01 cleat, 23 identified legacy angle proxy stations."""

    KEY = "pb01-kerf-right-cleat-hybrid-preparation-only"

    def __init__(self):
        super().__init__()
        self.pose = _trial()
        self.cleat = _cleat_part(self.raw.uncut_wood_parts(), self.pose)
        self.MEMBER_AXES = {
            **getattr(self.baseline, "MEMBER_AXES", {}),
            CLEAT: (cq.Vector(*N), cq.Vector(1, 0, 0)),
        }
        self.NATIVE_SQUARE_END_MEMBERS = (
            *getattr(self.baseline, "NATIVE_SQUARE_END_MEMBERS", ()),
            CLEAT,
        )

    def uncut_wood_parts(self):
        return (*self.raw.uncut_wood_parts(), self.cleat)

    def parts(self):
        return (
            *(part for part in self.baseline.parts() if part.name != STATION),
            self.cleat,
        )

    def connections(self):
        return tuple(
            connection
            for connection in self.baseline.connections()
            if not (
                connection.name.startswith("clip_") and connection.members[0] == STATION
            )
        )

    def stations(self):
        return tuple(row for row in super().stations() if row[0] != STATION)


def _add_pb01_paths(structure, metadata, module, spring_n_per_mm):
    if not math.isfinite(spring_n_per_mm) or spring_n_per_mm <= 0:
        raise ValueError("Trial spring stiffness must be positive and finite")
    groups = {}
    ownership = metadata["connection_ownership"]
    interface_points = {}
    for family, host in (("upright", UPRIGHT), ("rail", RAIL)):
        groups[family] = []
        interface_points[family] = []
        for row in module.pose["bolt_groups"][family]:
            axis = np.asarray(row["axis_xyz"], dtype=float)
            axis /= np.linalg.norm(axis)
            start = np.asarray(row["start_xyz_mm"], dtype=float)
            # The 2.5-mm extension precedes the actual host bearing length.
            host_length = 38.1
            point = start + axis * (2.5 + host_length)
            name = f"pb01_{family}_{row['name']}"
            owner = {
                "first": host,
                "second": CLEAT,
                "point": point.tolist(),
                "axis": axis.tolist(),
                "diagnostic_only": True,
            }
            base.directional_connector(
                structure,
                structure.attachment(host, point),
                structure.attachment(CLEAT, point),
                {
                    "axial_n_per_mm": spring_n_per_mm,
                    "lateral_n_per_mm": spring_n_per_mm,
                },
                name,
                owner,
            )
            ownership[name] = owner
            groups[family].append(name)
            interface_points[family].append(point)
    contacts = []
    for family, host, normal in (
        ("upright", UPRIGHT, -np.array([1.0, 0.0, 0.0])),
        ("rail", RAIL, -T),
    ):
        # One center sample per actual contact face; no pressure-field claim.
        point = np.mean(interface_points[family], axis=0)
        name = f"pb01_{family}_compression_trial"
        shared.normal_contact(
            structure,
            name,
            structure.attachment(host, point),
            [structure.attachment(CLEAT, point)],
            [1.0],
            point.tolist(),
            normal.tolist(),
            spring_n_per_mm,
        )
        ownership[name] = {
            "first": host,
            "second": CLEAT,
            "point": point.tolist(),
            "scalar_normal": normal.tolist(),
            "diagnostic_only": True,
        }
        contacts.append(name)
    metadata["pb01_bolt_groups"] = groups
    metadata["pb01_contact_names"] = contacts


def _add_trial_bolt_gravity(structure, metadata):
    """Add four explicit diagnostic stack weights at the serial interfaces."""
    rows = []
    member_loads = []
    for family, host, length in (
        ("upright", UPRIGHT, 203.2),
        ("rail", RAIL, 127.0),
    ):
        for name in metadata["pb01_bolt_groups"][family]:
            point = metadata["connection_ownership"][name]["point"]
            mass = _trial_bolt_mass_kg(length)
            host_node = structure.attachment(host, point)
            cleat_node = structure.attachment(CLEAT, point)
            half_weight = -mass * 9.80665 / 2
            add_load(structure, host_node, [0.0, 0.0, half_weight])
            add_load(structure, cleat_node, [0.0, 0.0, half_weight])
            for member in (host, CLEAT):
                member_loads.append(
                    {"member": member, "point": point, "force": [0.0, 0.0, half_weight]}
                )
            rows.append(
                {
                    "name": name,
                    "family": family,
                    "assumed_length_mm": length,
                    "mass_kg": mass,
                    "mass_basis": "diagnostic steel envelope only",
                    "host_node": host_node,
                    "cleat_node": cleat_node,
                    "force_split": "half to host and half to cleat at shared interface",
                }
            )
    total = sum(row["mass_kg"] for row in rows)
    metadata["pb01_trial_bolt_gravity"] = rows
    metadata["additional_member_loads"] = member_loads
    metadata["pb01_trial_bolt_total_mass_kg"] = total
    metadata["modeled_mass_kg"] += total


def _imprint_points(pose):
    result = {UPRIGHT: [], RAIL: [], CLEAT: []}
    for family, host in (("upright", UPRIGHT), ("rail", RAIL)):
        points = []
        for row in pose["bolt_groups"][family]:
            axis = np.asarray(row["axis_xyz"], dtype=float)
            axis /= np.linalg.norm(axis)
            point = np.asarray(row["start_xyz_mm"], dtype=float) + axis * 40.6
            points.append(point)
            result[host].append(point)
            result[CLEAT].append(point)
        center = np.mean(points, axis=0)
        result[host].append(center)
        result[CLEAT].append(center)
    return result


def prepare_case(case: str, *, spring_n_per_mm: float = 1000.0):
    """Prepare one unsolved hybrid; stiffness is a named trial input, not evidence."""
    if case not in CASES:
        raise ValueError("Unknown unchanged load case")
    module = HybridPB01()
    raw = {part.name: part for part in module.uncut_wood_parts()}
    panel_names = [name for name in raw if name.startswith(("main_", "kicker_"))]
    bolts = {
        c.name: bolt_properties(c) for c in module.connections() if c.kind == "bolt"
    }
    stiffnesses = {
        **connection_stiffnesses(),
        "floor": 1.0e5,
        "bearing": 1.0e6,
        "seating_per_area": 100.0,
        "bolt": {**next(iter(bolts.values())), "by_name": bolts},
    }
    original_grid, original_pressure = _ORIGINAL_GRID, _ORIGINAL_PRESSURE
    original_member = _ORIGINAL_MEMBER
    extra = _imprint_points(module.pose)
    calls = 0

    def kerf_grid(xs, ys):
        nonlocal calls
        if calls >= len(panel_names):
            raise ValueError("Unexpected panel-grid call")
        bounds = raw[panel_names[calls]].shape.BoundingBox()
        xs = list(xs)
        xs[0], xs[-1] = bounds.xmin, bounds.xmax
        calls += 1
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
            [*attachment_points, *extra.get(record["name"], ())],
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
                member_contacts=face_contacts(module),
                clearance_monitors=taper_top_monitors(module),
            )
        finally:
            panel_kernel.grid = original_grid
            panel_kernel.pressure_load = original_pressure
            FlushStructure.member = original_member
    if calls != len(panel_names):
        raise ValueError("Incomplete kerf-right six-panel preparation")
    panel_bounds = {}
    for name, panel in structure.panels.items():
        actual = raw[name].shape.BoundingBox()
        xs = [structure.nodes[node][0] for node in panel["nodes"]]
        if abs(min(xs) - actual.xmin) > 1.0e-6 or abs(max(xs) - actual.xmax) > 1.0e-6:
            raise ValueError(f"{name}: native mesh misses kerf-right panel bounds")
        panel_bounds[name] = [actual.xmin, actual.xmax]
    _add_pb01_paths(structure, metadata, module, spring_n_per_mm)
    _add_trial_bolt_gravity(structure, metadata)
    names = sorted(
        {c.members[0] for c in module.connections() if c.name.startswith("clip_")}
    )
    if len(names) != 23 or STATION in names or len(module.panel_connections()) != 66:
        raise ValueError("Hybrid proxy or panel inventory changed")
    metadata.update(
        pb01_pose_source=str(DIAGNOSTIC.relative_to(ROOT)),
        pb01_trial_stiffness_n_per_mm=spring_n_per_mm,
        kerf_panel_bounds_mm=panel_bounds,
        legacy_proxy_stations=names,
        provisional_structural_connectors="23 baseline ML24Z/SDS station proxies",
        pb01_same_case_demand=False,
        qualified_for_design=False,
        acceptance=False,
        drilling_released=False,
        preparation_only=True,
    )
    return structure, metadata
