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
from scripts.simple_rail_joint_comparison import PB01_GROUP_TRIAL_SIZE_MM, compare

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


POSES = {
    "three_eighth": ("cleat_grain_n_4x6_group", 9.525),
    "quarter": ("cleat_grain_n_4x6_group_quarter", 6.35),
    "quarter_short": ("cleat_grain_n_4x6_group_quarter", 6.35),
}


def _trial_bolt_mass_kg(length_mm, shaft_d):
    """Diagnostic steel mass, not a selected product or complete stack fit."""
    washer_od = 25.4
    washer_id = 10.5 if shaft_d == 9.525 else 7.5
    end_d, head_h, nut_h, washer_h = 16.51, 6.8072, 8.5598, 2.5
    area = lambda diameter: math.pi * (diameter / 2) ** 2
    volume = (
        area(shaft_d) * length_mm
        + 2 * (area(washer_od) - area(washer_id)) * washer_h
        + area(end_d) * head_h
        + (area(end_d) - area(shaft_d)) * nut_h
    )
    return volume * 7.85e-6


def _trial(variant: str) -> dict:
    data = (
        compare(quarter_n_length=PB01_GROUP_TRIAL_SIZE_MM[2])
        if variant == "quarter_short"
        else json.loads(DIAGNOSTIC.read_text())
    )
    if data["station"] != STATION or data["physical_width"] != "kerf-right":
        raise ValueError("PB01 diagnostic source identity changed")
    if variant not in POSES:
        raise ValueError("Unknown PB01 diagnostic bolt variant")
    pose_key, diameter = POSES[variant]
    pose = data[pose_key]
    if pose["status"] != "diagnostic_pose_only":
        raise ValueError("PB01 four-bolt pose is not a diagnostic pose")
    if variant in ("quarter", "quarter_short") and (
        pose["nominal_trial_bolt_diameter_mm_not_selected"] != diameter
        or pose["diagnostic_wood_bore_diameter_mm_not_drill_instruction"] != 7.5
    ):
        raise ValueError("Quarter-inch PB01 pose diameter changed")
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
    if not np.allclose((x_width, t_width), PB01_GROUP_TRIAL_SIZE_MM[:2]) or not any(
        math.isclose(n_length, length)
        for length in (300.0, PB01_GROUP_TRIAL_SIZE_MM[2])
    ):
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

    def __init__(self, *, variant: str = "three_eighth"):
        super().__init__()
        self.pose = _trial(variant)
        self.variant = variant
        if variant == "quarter":
            self.KEY = "pb01-kerf-right-cleat-quarter-hybrid-preparation-only"
        elif variant == "quarter_short":
            self.KEY = "pb01-kerf-right-cleat-quarter-short-hybrid-preparation-only"
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


def _face_samples(module, family):
    """Four interior quadrature points on the actual, unbored timber overlap."""
    host_name = UPRIGHT if family == "upright" else RAIL
    shapes = {part.name: part.shape for part in module.uncut_wood_parts()}
    host, cleat = shapes[host_name], shapes[CLEAT]
    normal = -np.array([1.0, 0.0, 0.0]) if family == "upright" else -T
    axes = (T, N) if family == "upright" else (np.array([1.0, 0.0, 0.0]), N)

    def extent(shape, axis):
        values = [
            np.dot(axis, vertex.Center().toTuple()) for vertex in shape.Vertices()
        ]
        return min(values), max(values)

    normal_host = extent(host, normal)[0]
    normal_cleat = extent(cleat, normal)[1]
    if abs(normal_host - normal_cleat) > 1e-5:
        raise ValueError(f"{family}: cleat is not seated at the host face")
    limits = []
    for axis in axes:
        host_low, host_high = extent(host, axis)
        cleat_low, cleat_high = extent(cleat, axis)
        low, high = max(host_low, cleat_low), min(host_high, cleat_high)
        if high - low <= 0:
            raise ValueError(f"{family}: no seated face overlap")
        limits.append((low, high))
    span_a = limits[0][1] - limits[0][0]
    span_b = limits[1][1] - limits[1][0]
    bore_diameter = 7.5 if module.variant in ("quarter", "quarter_short") else 10.5
    net_area = span_a * span_b - 2 * math.pi * (bore_diameter / 2) ** 2
    if net_area <= 0:
        raise ValueError(f"{family}: nonpositive net seated area")
    bolt_centers = []
    for row in module.pose["bolt_groups"][family]:
        direction = np.asarray(row["axis_xyz"], dtype=float)
        direction /= np.linalg.norm(direction)
        bolt_centers.append(
            np.asarray(row["start_xyz_mm"], dtype=float) + direction * 40.6
        )
    samples = []
    for i, fa in enumerate((0.25, 0.75)):
        for j, fb in enumerate((0.25, 0.75)):
            a = limits[0][0] + fa * span_a
            b = limits[1][0] + fb * span_b
            point = normal * normal_host + axes[0] * a + axes[1] * b
            if not host.isInside(cq.Vector(*(point + normal * 0.1)), 0.001):
                raise ValueError(f"{family}: sample outside host")
            if not cleat.isInside(cq.Vector(*(point - normal * 0.1)), 0.001):
                raise ValueError(f"{family}: sample outside cleat")
            for bolt in bolt_centers:
                separation = np.linalg.norm(
                    [np.dot(axis, point - bolt) for axis in axes]
                )
                if separation <= bore_diameter / 2:
                    raise ValueError(f"{family}: sample intersects diagnostic bore")
            samples.append({"point": point, "grid": [i, j], "area_mm2": net_area / 4})
    return {
        "normal": normal,
        "limits_mm": limits,
        "net_area_mm2": net_area,
        "samples": samples,
    }


def _add_pb01_paths(
    structure,
    metadata,
    module,
    bolt_axial_n_per_mm,
    bolt_lateral_n_per_mm,
    face_normal_total_n_per_mm,
    faces,
    tension_only_axial=False,
):
    for value in (
        bolt_axial_n_per_mm,
        bolt_lateral_n_per_mm,
        face_normal_total_n_per_mm,
    ):
        if not math.isfinite(value) or value <= 0:
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
                    "axial_n_per_mm": bolt_axial_n_per_mm,
                    "lateral_n_per_mm": bolt_lateral_n_per_mm,
                },
                name,
                owner,
            )
            if tension_only_axial:
                axial = [spring for spring in structure.springs
                         if spring["name"] == name and spring["dof"] == 1]
                if len(axial) != 1:
                    raise ValueError("Expected one PB01 axial spring per bolt")
                axial[0]["bearing_closed_assumption"] = True
                axial[0]["tension_only_assumption"] = True
            ownership[name] = owner
            groups[family].append(name)
            interface_points[family].append(point)
    contacts = []
    for family, host in (("upright", UPRIGHT), ("rail", RAIL)):
        face = faces[family]
        normal = face["normal"]
        for sample in face["samples"]:
            point = sample["point"]
            name = f"pb01_{family}_compression_{sample['grid'][0]}_{sample['grid'][1]}"
            shared.normal_contact(
                structure,
                name,
                structure.attachment(host, point),
                [structure.attachment(CLEAT, point)],
                [1.0],
                point.tolist(),
                normal.tolist(),
                face_normal_total_n_per_mm / 4,
            )
            ownership[name] = {
                "first": host,
                "second": CLEAT,
                "point": point.tolist(),
                "scalar_normal": normal.tolist(),
                "tributary_net_area_mm2": sample["area_mm2"],
                "diagnostic_only": True,
            }
            contacts.append(name)
    metadata["pb01_bolt_groups"] = groups
    metadata["pb01_axial_law"] = (
        "tension_only_no_preload" if tension_only_axial else "bilateral_historical"
    )
    metadata["pb01_contact_names"] = contacts
    metadata["pb01_contact_faces"] = {
        family: {"limits_mm": face["limits_mm"], "net_area_mm2": face["net_area_mm2"]}
        for family, face in faces.items()
    }


def _add_trial_bolt_gravity(structure, metadata, diameter_mm):
    """Add four explicit diagnostic stack weights at the serial interfaces."""
    rows = []
    member_loads = []
    for family, host, length in (
        ("upright", UPRIGHT, 203.2),
        ("rail", RAIL, 127.0),
    ):
        for name in metadata["pb01_bolt_groups"][family]:
            point = metadata["connection_ownership"][name]["point"]
            mass = _trial_bolt_mass_kg(length, diameter_mm)
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
                    "assumed_shaft_diameter_mm": diameter_mm,
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


def _imprint_points(pose, faces):
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
        for sample in faces[family]["samples"]:
            result[host].append(sample["point"])
            result[CLEAT].append(sample["point"])
    return result


def prepare_case(
    case: str,
    *,
    variant: str = "three_eighth",
    bolt_axial_n_per_mm: float = 1000.0,
    bolt_lateral_n_per_mm: float = 1000.0,
    face_normal_total_n_per_mm: float = 1000.0,
    tension_only_axial: bool = False,
):
    """Prepare one unsolved hybrid; stiffness is a named trial input, not evidence."""
    if case not in CASES:
        raise ValueError("Unknown unchanged load case")
    module = HybridPB01(variant=variant)
    faces = {family: _face_samples(module, family) for family in ("upright", "rail")}
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
    extra = _imprint_points(module.pose, faces)
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
    _add_pb01_paths(
        structure,
        metadata,
        module,
        bolt_axial_n_per_mm,
        bolt_lateral_n_per_mm,
        face_normal_total_n_per_mm,
        faces,
        tension_only_axial=tension_only_axial,
    )
    diameter_mm = POSES[variant][1]
    _add_trial_bolt_gravity(structure, metadata, diameter_mm)
    names = sorted(
        {c.members[0] for c in module.connections() if c.name.startswith("clip_")}
    )
    if len(names) != 23 or STATION in names or len(module.panel_connections()) != 66:
        raise ValueError("Hybrid proxy or panel inventory changed")
    metadata.update(
        pb01_pose_source=(
            "scripts/simple_rail_joint_comparison.py:PB01_GROUP_TRIAL_SIZE_MM"
            if variant == "quarter_short"
            else str(DIAGNOSTIC.relative_to(ROOT))
        ),
        pb01_pose_variant=variant,
        pb01_trial_bolt_diameter_mm=diameter_mm,
        pb01_trial_stiffness_n_per_mm={
            "bolt_axial": bolt_axial_n_per_mm,
            "bolt_lateral": bolt_lateral_n_per_mm,
            "face_normal_total_per_interface": face_normal_total_n_per_mm,
        },
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
