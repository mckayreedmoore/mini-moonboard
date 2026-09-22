"""Preliminary native topology for the current integrated barrel frame.

This binds real viewer axes and contact faces; stiffnesses are not qualified.
"""

import math
from dataclasses import replace

import cadquery as cq

from fea.current_response_materials import connection_stiffnesses, materials
from fea.floor_flush_run import taper_top_monitors
from mini_moonboard.box_frame import Part
from scripts.bolted_kerf_diagnostic_probe import DiagnosticProxy, prepare_diagnostic
from scripts.clear_space_batch import CASES
from scripts.compact_rail_study import bolt_properties
from scripts.export_owner_barrel_scene import build_integrated_viewer_assembly
from scripts.owner_barrel_native_face_contacts import build_report as face_report
from scripts.owner_barrel_retained_interfaces import (
    retained_contact_rows,
    retained_interface_point,
)

SOURCE_ID = "owner-barrel-integrated-native-preparation-v3"


class BarrelBolt:
    """Existing viewer bolt with its one barrel, head, and washer for mass."""

    def __init__(self, source, solids):
        self.name = source.name
        self.start = source.start
        self.direction = source.direction
        self.length = source.length
        self.diameter = source.diameter
        self.members = source.members
        self.kind = source.kind
        self.grip = source.grip
        self._solids = tuple(solids)
        if self.kind != "bolt" or len(self._solids) != 4:
            raise ValueError(f"{self.name}: incomplete barrel hardware mass envelope")

    def components(self):
        return self._solids


class IntegratedBarrelNative(DiagnosticProxy):
    """46 barrel pairs, 12 retained bolts, 66 fixed screws, no angle proxies."""

    KEY = SOURCE_ID

    def __init__(self):
        super().__init__()
        self.assembly = build_integrated_viewer_assembly()
        self.faces = face_report(self.assembly)
        baseline_wood = {part.name: part for part in self.baseline.uncut_wood_parts()}
        if (
            set(baseline_wood) != set(self.assembly["wood"])
            or len(baseline_wood) != 26
            or self.faces["station_count"] != 24
            or self.faces["bolt_interface_count"] != 46
            or self.faces["trial_cut_cell_face_count"] != 2
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
            barrels.append(
                BarrelBolt(
                    source,
                    (
                        stack["shaft"],
                        stack["washer"],
                        stack["head"],
                        self.assembly["barrels"][barrel_name],
                    ),
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
        self.FULL_BEVEL_PROJECTION_MEMBERS = (
            "base_principal_center_left",
            "base_principal_center_right",
            "base_side_left",
            "base_side_right",
        )

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
    if len(rows) != 120 or len({row["name"] for row in rows}) != 120:
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
                 barrel_lateral_n_per_mm=500.0, contact_n_per_mm2=100.0):
    """Prepare but never solve one signed case with unrated conditional springs."""
    if case not in CASES:
        raise ValueError(f"Unknown signed load case: {case}")
    for value in (barrel_axial_n_per_mm, barrel_lateral_n_per_mm,
                  contact_n_per_mm2):
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
        module, stiffness_per_area=contact_n_per_mm2
    )
    retained_contacts = retained_face_contacts(
        module, stiffness_per_area=contact_n_per_mm2
    )
    structure, metadata = prepare_diagnostic(
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
    for name in module.barrel_bolt_names:
        springs = [row for row in structure.springs if row["name"] == name]
        if len(springs) != 3 or {row["dof"] for row in springs} != {1, 2, 3}:
            raise ValueError(f"{name}: missing barrel directional springs")
        axial = next(row for row in springs if row["dof"] == 1)
        axial["bearing_closed_assumption"] = True
        axial["tension_only_assumption"] = True
        ownership[name]["developmental_only"] = True
    metadata["provisional_structural_connectors"] = (
        "46 modeled barrel pairs with conditional stiffness; 12 retained bolts; "
        "66 panel screws; no legacy angle proxies"
    )
    metadata["bolted_joint_demands"] = False
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
        "analysis_only_full_bevel_members": list(module.FULL_BEVEL_PROJECTION_MEMBERS),
        "conditional_barrel_axial_n_per_mm": barrel_axial_n_per_mm,
        "conditional_barrel_lateral_n_per_mm": barrel_lateral_n_per_mm,
        "conditional_contact_n_per_mm2": contact_n_per_mm2,
        "native_solve": False,
        "structural_released": False,
    }
    return structure, metadata, summary
