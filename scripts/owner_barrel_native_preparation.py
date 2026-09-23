"""Preliminary native topology for the current integrated barrel frame.

This binds real viewer axes and contact faces; stiffnesses are not qualified.
"""

import math
from dataclasses import replace

import cadquery as cq
import numpy as np

from fea import current_response_model as response_model
from fea.current_response_materials import connection_stiffnesses, materials
from fea.floor_flush_mesh import FlushStructure
from fea.floor_flush_run import taper_top_monitors
from fea.floor_uncut_mesh import mesh_member as mesh_actual_prism
from fea.floor_uncut_mesh import panel_offset_attachment, panel_offset_spec
from mini_moonboard.box_frame import Part
from scripts.bolted_kerf_diagnostic_probe import DiagnosticProxy, prepare_diagnostic
from scripts.clear_space_batch import CASES
from scripts.compact_rail_study import bolt_properties
from scripts.export_owner_barrel_scene import build_integrated_viewer_assembly
from scripts.owner_barrel_native_connector_inventory import build_inventory
from scripts.owner_barrel_native_face_contacts import build_report as face_report
from scripts.owner_barrel_retained_interfaces import (
    retained_contact_rows,
    retained_interface_point,
)

SOURCE_ID = "owner-barrel-integrated-native-preparation-v3"
BARREL_RADIAL_CLEARANCE_MM = 0.575
ACTUAL_BEVEL_MEMBERS = (
    "base_principal_center_left",
    "base_principal_center_right",
    "base_side_left",
    "base_side_right",
)


class IntegratedBarrelStructure(FlushStructure):
    """Existing flush mesh plus exact constant-X prisms for four bevel members."""

    def member(self, record, attachment_points=(), size=100.0):
        if "owner_barrel_bevel_geometry" in record:
            return mesh_actual_prism(self, record, attachment_points, size)
        return super().member(record, attachment_points, size)

    def attachment(self, name, point):
        record = self.members[name]["record"]
        if "owner_barrel_bevel_geometry" in record:
            spec = panel_offset_spec(record, point)
            if spec is not None:
                return panel_offset_attachment(self, name, spec)
        return super().attachment(name, point)


def _bevel_record(part, record, panel_offsets=()):
    """Bind one inclined timber record to its actual constant-X CAD prism."""
    shape = part.shape
    bounds = shape.BoundingBox()
    vertices = [vertex.Center().toTuple() for vertex in shape.Vertices()]
    if any(
        min(abs(x - bounds.xmin), abs(x - bounds.xmax)) > 1.0e-6
        for x, _, _ in vertices
    ):
        raise ValueError(f"{part.name}: actual bevel mesh requires a constant-X prism")
    grain = np.asarray(record["axis"], dtype=float)
    stations = [float(np.dot(vertex, grain)) for vertex in vertices]
    for key, station in (("start", min(stations)), ("end", max(stations))):
        point = np.asarray(record[key], dtype=float)
        record[key] = (
            point + grain * (station - float(np.dot(point, grain)))
        ).tolist()
    record["verification_grain_interval_mm"] = [min(stations), max(stations)]
    record["uncut_prism_geometry"] = {
        "side_profile_yz_mm": sorted({(y, z) for _, y, z in vertices}),
        "x_bounds_mm": [bounds.xmin, bounds.xmax],
        "expected_volume_mm3": shape.Volume(),
        "expected_centroid_xyz_mm": shape.Center().toTuple(),
    }
    record["owner_barrel_bevel_geometry"] = {
        "mode": "actual_constant_x_cad_prism_c3d20",
        "source_member": part.name,
        "attachment_rule": "actual mapped-cell interpolation",
    }
    record["panel_midsurface_offsets"] = list(panel_offsets)
    return record


def _prepare_actual_bevel_diagnostic(module, **kwargs):
    """Compose exact bevel prisms with existing kerf-right flush preparation."""
    from fea import floor_flush_mesh

    raw = {part.name: part for part in module.uncut_wood_parts()}
    if set(ACTUAL_BEVEL_MEMBERS) - set(raw):
        raise ValueError("Actual bevel member source is incomplete")
    panel_offsets = {}
    half = response_model.panel_kernel.THICKNESS / 2
    for connection in module.panel_connections():
        receiver = connection.members[1]
        if receiver not in ACTUAL_BEVEL_MEMBERS:
            continue
        panel_offsets.setdefault(receiver, []).append(
            {
                "name": connection.name,
                "point_xyz_mm": (
                    connection.start + connection.direction * half
                ).toTuple(),
                "anchor_xyz_mm": (
                    connection.start + connection.direction * (2 * half)
                ).toTuple(),
                "direction_xyz": connection.direction.toTuple(),
            }
        )
    original_record = response_model.gross_member_record
    original_structure = floor_flush_mesh.FlushStructure

    def revised_record(part, *args, **options):
        record = original_record(part, *args, **options)
        if part.name in ACTUAL_BEVEL_MEMBERS:
            record = _bevel_record(
                raw[part.name], record, panel_offsets.get(part.name, ())
            )
        return record

    try:
        response_model.gross_member_record = revised_record
        floor_flush_mesh.FlushStructure = IntegratedBarrelStructure
        return prepare_diagnostic(module, **kwargs)
    finally:
        response_model.gross_member_record = original_record
        floor_flush_mesh.FlushStructure = original_structure


class BarrelBolt:
    """Existing viewer bolt with its one barrel, head, and washer for mass."""

    def __init__(self, source, solids, members):
        self.name = source.name
        self.start = source.start
        self.direction = source.direction
        self.length = source.length
        self.diameter = source.diameter
        self.members = tuple(members)
        self.kind = source.kind
        self.grip = source.grip
        self._solids = tuple(solids)
        if self.kind != "bolt" or len(self._solids) != 4 or len(self.members) != 2:
            raise ValueError(f"{self.name}: incomplete barrel hardware mass envelope")

    def components(self):
        return self._solids


class IntegratedBarrelNative(DiagnosticProxy):
    """46 barrel pairs, 12 retained bolts, 66 fixed screws, no angle proxies."""

    KEY = SOURCE_ID

    def __init__(self):
        super().__init__()
        self.assembly = build_integrated_viewer_assembly()
        self.connector_inventory = build_inventory(assembly=self.assembly)
        self.faces = face_report(self.assembly)
        baseline_wood = {part.name: part for part in self.baseline.uncut_wood_parts()}
        if (
            set(baseline_wood) != set(self.assembly["wood"])
            or len(baseline_wood) != 26
            or self.faces["station_count"] != 24
            or self.faces["bolt_interface_count"] != 46
            or self.faces["trial_cut_cell_face_count"]
            != self.faces["trial_cut_face_count"]
        ):
            raise ValueError("Integrated barrel native timber or face source changed")
        wood = []
        for name, part in baseline_wood.items():
            shape = self.assembly["wood"][name]
            if name.startswith("base_post_center_"):
                box = shape.BoundingBox()
                wood.append(
                    Part(
                        name,
                        shape,
                        (box.zlen, box.ylen, box.xlen),
                        "Integrated seam-side post; provisional geometry and material",
                        1,
                    )
                )
            else:
                wood.append(replace(part, shape=shape))
        self._wood = tuple(wood)
        wood_names = set(baseline_wood)
        cut_source = {part.name: part for part in self.baseline.parts()}
        from scripts.owner_barrel_visual_wood import EXPECTED_TIMBERS, build_visual_wood

        visual = build_visual_wood(
            assembly=self.assembly,
            candidate_service=True,
            candidate_center_cuts=True,
            candidate_all_cuts=True,
        )
        if (
            set(visual["wood"]) != EXPECTED_TIMBERS
            or visual["report"]["excluded_legacy_sds_axes"] != 144
            or visual["report"]["candidate_barrel_pairs_with_cut_wood"] != 46
            or visual["report"]["barrel_drilling_paths_without_cut_wood"]
            or visual["report"]["barrel_path_host_anomalies"]
        ):
            raise ValueError("Integrated visual-only timber cut source changed")
        self._response_wood = tuple(
            replace(
                part,
                shape=(
                    visual["wood"][part.name]
                    if part.name in EXPECTED_TIMBERS
                    else cut_source[part.name].shape
                ),
            )
            for part in self._wood
        )
        self._hardware_parts = tuple(
            part for name, part in cut_source.items()
            if name not in wood_names and name.startswith("hold_tnut_")
        )
        if len(self._hardware_parts) != 142:
            raise ValueError("Fixed hold/T-nut hardware inventory changed")
        self._bolt_face_points = {
            crossing["name"]: cq.Vector(*crossing["point_xyz_mm"])
            for face in self.faces["stations"].values()
            for crossing in face["bolt_face_crossings"]
        }
        self.barrel_bolt_names = frozenset(self.assembly["bolts"])
        barrels = []
        for name, source in self.assembly["bolts"].items():
            stack = self.assembly["stacks"][name]
            barrel_name = name.removesuffix("_bolt")
            if set(stack) != {"shaft", "washer", "head"}:
                raise ValueError(f"{name}: incomplete current viewer stack")
            connector = self.connector_inventory["bolts"][name]
            if connector["entry_member"] == connector["receiving_member"]:
                raise ValueError(f"{name}: barrel entry and receiving members coincide")
            start = cq.Vector(*connector["start_mm"])
            axis = cq.Vector(*connector["direction_xyz"])
            thread_axis = cq.Vector(*connector["provisional_thread_axis_point_mm"])
            if (thread_axis - start).dot(axis) <= 0:
                raise ValueError(f"{name}: barrel axis is behind the bolt start")
            barrels.append(
                BarrelBolt(
                    source,
                    (
                        stack["shaft"],
                        stack["washer"],
                        stack["head"],
                        self.assembly["barrels"][barrel_name],
                    ),
                    (connector["entry_member"], connector["receiving_member"]),
                )
            )
        self._connections = (
            *self.assembly["panel_connections"],
            *self.assembly["frame_connections"],
            *barrels,
        )
        names = {row.name for row in self._connections}
        legacy = {row.name for row in self.assembly["removed_legacy_sds"]}
        if (
            len(self._connections) != len(names)
            or len(names) != 124
            or names & legacy
            or set(self._bolt_face_points) != self.barrel_bolt_names
            or self.assembly["post_placement"] != "integrated"
        ):
            raise ValueError("Integrated barrel connection source changed")
        self.NATIVE_SQUARE_END_MEMBERS = (
            *getattr(self.baseline, "NATIVE_SQUARE_END_MEMBERS", ()),
            "base_post_center_left",
            "base_post_center_right",
        )
        self.ACTUAL_BEVEL_MEMBERS = ACTUAL_BEVEL_MEMBERS
        self.FULL_BEVEL_PROJECTION_MEMBERS = ()

    def uncut_wood_parts(self):
        return self._wood

    def current_response_wood_parts(self):
        return self._response_wood

    def parts(self):
        return (*self._wood, *self._hardware_parts)

    def connections(self):
        return self._connections

    def panel_connections(self):
        return self.assembly["panel_connections"]

    def stations(self):
        """Legacy angle stations do not exist in the barrel candidate."""
        return ()

    def bolt_interface_point(self, connection):
        return self._bolt_face_points.get(connection.name) or retained_interface_point(
            self.assembly, self.baseline, connection
        )


def member_contacts(module, *, stiffness_per_area):
    """Conditional compression cells; no precompression or tangential friction."""
    if not math.isfinite(stiffness_per_area) or stiffness_per_area <= 0:
        raise ValueError("Require positive finite conditional areal stiffness")
    rows = []
    for station, face in module.faces["stations"].items():
        outward = cq.Vector(*face["normal_outward_from_first_xyz"])
        inward = (-outward).normalized()
        for cell in face["contact_cells"]:
            rows.append(
                {
                    "name": cell["name"],
                    "station": station,
                    "first": face["first_part"],
                    "second": face["second_part"],
                    "point_xyz_mm": cell["point_xyz_mm"],
                    "normal_xyz": list(inward.toTuple()),
                    "tributary_area_mm2": cell["tributary_area_mm2"],
                    "stiffness_n_per_mm": (
                        stiffness_per_area * cell["tributary_area_mm2"]
                    ),
                    "area_basis": face["contact_cell_area_basis"],
                    "conditional_only": True,
                }
            )
    expected = module.faces["contact_cell_count"]
    if len(rows) != expected or len({row["name"] for row in rows}) != expected:
        raise ValueError("Current integrated contact cell inventory changed")
    return tuple(rows)


def retained_face_contacts(module, *, stiffness_per_area):
    """Keep baseline six face groups at the current kerf-right interfaces."""
    return retained_contact_rows(
        module.assembly,
        module.baseline,
        stiffness_per_area=stiffness_per_area,
    )


def prepare_case(case, *, module=None, barrel_axial_n_per_mm=1000.0,
                 barrel_lateral_n_per_mm=500.0, contact_n_per_mm3=100.0):
    """Prepare but never solve one signed case with unrated conditional springs."""
    if case not in CASES:
        raise ValueError(f"Unknown signed load case: {case}")
    for value in (barrel_axial_n_per_mm, barrel_lateral_n_per_mm,
                  contact_n_per_mm3):
        if not math.isfinite(value) or value <= 0:
            raise ValueError("Conditional stiffnesses must be positive and finite")
    if module is None:
        module = IntegratedBarrelNative()
    if not isinstance(module, IntegratedBarrelNative):
        raise TypeError("Require current integrated barrel source")
    bolts = {
        row.name: (
            {"axial_n_per_mm": barrel_axial_n_per_mm,
             "lateral_n_per_mm": barrel_lateral_n_per_mm,
             "basis": "Conditional barrel stiffness; no tested fastener or joint rating"}
            if row.name in module.barrel_bolt_names else bolt_properties(row)
        )
        for row in module.connections() if row.kind == "bolt"
    }
    if len(bolts) != 58:
        raise ValueError("Current integrated bolt count changed")
    stiffnesses = {
        **connection_stiffnesses(),
        "floor": 1.0e5,
        "bearing": 1.0e6,
        "seating_per_area": 100.0,
        "bolt": {"axial_n_per_mm": barrel_axial_n_per_mm,
                 "lateral_n_per_mm": barrel_lateral_n_per_mm,
                 "by_name": bolts},
    }
    hold, force = CASES[case]
    barrel_contacts = member_contacts(
        module, stiffness_per_area=contact_n_per_mm3
    )
    retained_contacts = retained_face_contacts(
        module, stiffness_per_area=contact_n_per_mm3
    )
    structure, metadata = _prepare_actual_bevel_diagnostic(
        module,
        expected_candidate=module.KEY,
        materials=materials(),
        stiffnesses=stiffnesses,
        hold=hold,
        pounds=250.0,
        horizontal_force=force,
        leg_floor_grid=3,
        patch_size=20.0,
        member_contacts=(*retained_contacts, *barrel_contacts),
        clearance_monitors=taper_top_monitors(module),
        implicit_header_bearings=False,
    )
    ownership = metadata["connection_ownership"]
    radial_ownership = {}
    for name in module.barrel_bolt_names:
        springs = [row for row in structure.springs if row["name"] == name]
        if len(springs) != 3 or {row["dof"] for row in springs} != {1, 2, 3}:
            raise ValueError(f"{name}: missing barrel directional springs")
        axial = next(row for row in springs if row["dof"] == 1)
        axial["bearing_closed_assumption"] = True
        axial["tension_only_assumption"] = True
        radial_name = f"{name}__radial_clearance"
        lateral = [row for row in springs if row["dof"] in (2, 3)]
        if len(lateral) != 2 or any(
            row["stiffness_n_per_mm"] != barrel_lateral_n_per_mm for row in lateral
        ):
            raise ValueError(f"{name}: unequal or incomplete barrel lateral springs")
        for row in lateral:
            row.update(
                name=radial_name,
                bearing_closed_assumption=True,
                radial_clearance_assumption=True,
                radial_clearance_mm=BARREL_RADIAL_CLEARANCE_MM,
                connector_name=name,
            )
        radial_ownership[radial_name] = {
            **ownership[name],
            "connector_name": name,
            "radial_clearance_assumption": True,
        }
        ownership[name]["developmental_only"] = True
    metadata["radial_clearance_ownership"] = radial_ownership
    metadata["provisional_structural_connectors"] = (
        "46 modeled barrel pairs with conditional stiffness; 12 retained bolts; "
        "66 panel screws; no legacy angle proxies"
    )
    metadata["bolted_joint_demands"] = False
    metadata["barrel_radial_clearance_law"] = {
        "clearance_mm": BARREL_RADIAL_CLEARANCE_MM,
        "state": "coupled local lateral DOFs; open dead zone or engaged circular bearing",
        "engaged_force": "k * (u_lateral - clearance * contact_normal)",
        "preload_n": 0.0,
        "conditional_only": True,
    }
    metadata["acceptance"] = False
    summary = {
        "case": case,
        "hold": hold,
        "horizontal_force_n": force,
        "candidate": module.KEY,
        "barrel_pairs": len(module.barrel_bolt_names),
        "retained_bolts": len(bolts) - len(module.barrel_bolt_names),
        "panel_screws": len(module.panel_connections()),
        "face_contact_cells": len(barrel_contacts),
        "retained_face_contact_cells": len(retained_contacts),
        "implicit_header_bearings": False,
        "actual_mapped_bevel_members": list(module.ACTUAL_BEVEL_MEMBERS),
        "conditional_barrel_axial_n_per_mm": barrel_axial_n_per_mm,
        "conditional_barrel_lateral_n_per_mm": barrel_lateral_n_per_mm,
        "barrel_radial_clearance_mm": BARREL_RADIAL_CLEARANCE_MM,
        "conditional_contact_n_per_mm3": contact_n_per_mm3,
        "native_solve": False,
        "structural_released": False,
    }
    return structure, metadata, summary
