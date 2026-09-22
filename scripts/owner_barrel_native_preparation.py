"""Preliminary native topology for the current integrated barrel frame.

This binds real viewer axes and contact faces; stiffnesses are not qualified.
"""

import math
from dataclasses import replace

import cadquery as cq

from mini_moonboard.box_frame import Part
from scripts.bolted_kerf_diagnostic_probe import DiagnosticProxy
from scripts.export_owner_barrel_scene import build_integrated_viewer_assembly
from scripts.owner_barrel_native_face_contacts import build_report as face_report

SOURCE_ID = "owner-barrel-integrated-native-preparation-v1"


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
        self._hardware_parts = tuple(
            part
            for part in self.baseline.parts()
            if part.name not in wood_names and part.name.startswith("hold_tnut_")
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

    def uncut_wood_parts(self):
        return self._wood

    def current_response_wood_parts(self):
        return self._wood

    def parts(self):
        return (*self._wood, *self._hardware_parts)

    def connections(self):
        return self._connections

    def panel_connections(self):
        return self.assembly["panel_connections"]

    def bolt_interface_point(self, connection):
        return self._bolt_face_points.get(connection.name) or self.baseline.bolt_interface_point(
            connection
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
