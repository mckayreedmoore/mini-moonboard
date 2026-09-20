"""Preparation-only kerf-right response proxy; no solver or bolted demands."""

import argparse
import json

import cadquery as cq

from fea.current_response_materials import connection_stiffnesses, materials
from fea.floor_flush_mesh import prepare_flush
from fea.floor_flush_run import face_contacts, taper_top_monitors
from fea.horizontal_panel_frame import panel_kernel
from mini_moonboard import bolted_floor_flush_width, floor_flush_width
from scripts.bolted_center_joint_model import shared_center_joint
from scripts.bolted_center_response_adapter import prepare_center
from scripts.clear_space_batch import CASES
from scripts.compact_rail_study import bolt_properties


class DiagnosticProxy:
    """Raw bolted-candidate wood with explicitly provisional baseline ML angles."""

    KEY = "bolted-kerf-right-diagnostic-proxy"

    def __init__(self):
        self.raw = bolted_floor_flush_width.variant("kerf-right")
        self.baseline = floor_flush_width.variant("kerf-right")

    def __getattr__(self, name):
        return getattr(self.baseline, name)

    def uncut_wood_parts(self):
        return self.raw.uncut_wood_parts()

    def parts(self):
        # Baseline ML hardware is a preparation proxy, never a bolted demand model.
        return self.baseline.parts()

    def connections(self):
        return self.baseline.connections()

    def panel_connections(self):
        return self.raw.panel_connections()

    def stations(self):
        shifted = floor_flush_width.TRANSLATE_NAMES
        dx = floor_flush_width.KERF_RIGHT_MM
        return tuple(
            (name, cq.Vector(origin.x - dx, origin.y, origin.z), u, v, beam, upright)
            if beam in shifted or upright in shifted
            else (name, origin, u, v, beam, upright)
            for name, origin, u, v, beam, upright in self.baseline.stations()
        )

    def bolt_interface_point(self, connection):
        return self.baseline.bolt_interface_point(connection)

    def floor_recess_geometry(self):
        rows = self.baseline.floor_recess_geometry()
        right = dict(rows["lumber_leg_right"])
        dx = floor_flush_width.KERF_RIGHT_MM
        right["inner_face_x_mm"] -= dx
        bounds = right["raw_bounds_xyz_mm"]
        right["raw_bounds_xyz_mm"] = (
            (bounds[0][0] - dx, bounds[0][1] - dx),
            *bounds[1:],
        )
        right["cut_profile_xs_mm"] = [
            (x - dx, station) for x, station in right["cut_profile_xs_mm"]
        ]
        for key in ("cut_inner_x_band_mm", "retained_x_band_mm"):
            right[key] = tuple(x - dx for x in right[key])
        return {**rows, "lumber_leg_right": right}


class DiagnosticCenterBolted(DiagnosticProxy):
    """One left-center nominal AB205 topology; all other old clips remain proxies."""

    KEY = "bolted-kerf-right-left-center-ab205-diagnostic"


def prepare_diagnostic(module, **kwargs):
    """Preparation factory for the proxy; never invokes a native solver."""
    if (
        not isinstance(module, DiagnosticProxy)
        or kwargs.get("expected_candidate", module.KEY) != module.KEY
    ):
        raise ValueError("Require the diagnostic kerf-right proxy candidate")
    center_joint = kwargs.pop("diagnostic_center_joint", None)
    if isinstance(module, DiagnosticCenterBolted) != (center_joint is not None):
        raise ValueError("Center-bolted diagnostic requires its explicit joint spec")
    raw = {part.name: part for part in module.uncut_wood_parts()}
    if {part.name for part in module.baseline.uncut_wood_parts()} != set(raw):
        raise ValueError(
            "Provisional baseline and candidate raw member inventories differ"
        )
    # The current preparer hardcodes official X bounds for all six panels.
    panel_names = [name for name in raw if name.startswith(("main_", "kicker_"))]
    if module.panel_edge_cutouts():
        raise ValueError(
            "Kerf-right diagnostic proxy does not adapt edge-cutout panels"
        )
    original_grid, original_pressure = panel_kernel.grid, panel_kernel.pressure_load
    calls = 0

    def kerf_grid(xs, ys):
        nonlocal calls
        if calls >= len(panel_names):
            raise ValueError("Unexpected grid call outside six-panel sequence")
        bounds = raw[panel_names[calls]].shape.BoundingBox()
        xs = list(xs)
        xs[0], xs[-1] = bounds.xmin, bounds.xmax
        calls += 1
        return original_grid(xs, ys)

    def kerf_pressure(nodes, elements, patch, total):
        if patch[0:2] in ((-module.b.HALF, 0.0), (0.0, module.b.HALF)):
            xs = [point[0] for point in nodes.values()]
            patch = (min(xs), max(xs), *patch[2:])
        return original_pressure(nodes, elements, patch, total)

    try:
        panel_kernel.grid = kerf_grid
        panel_kernel.pressure_load = kerf_pressure
        structure, metadata = (
            prepare_center(module, center_joint, **kwargs)
            if center_joint is not None else prepare_flush(module, **kwargs)
        )
        if calls != len(panel_names):
            raise ValueError("Incomplete six-panel grid sequence")
    finally:
        panel_kernel.grid, panel_kernel.pressure_load = original_grid, original_pressure
    panel_bounds = {}
    for name, panel in structure.panels.items():
        actual = raw[name].shape.BoundingBox()
        xs = [structure.nodes[node][0] for node in panel["nodes"]]
        panel_bounds[name] = {
            "actual_x_mm": [actual.xmin, actual.xmax],
            "mesh_x_mm": [min(xs), max(xs)],
        }
        if abs(min(xs) - actual.xmin) > 1e-6 or abs(max(xs) - actual.xmax) > 1e-6:
            raise ValueError(f"{name}: mesh X bounds do not match raw kerf-right panel")
    metadata["diagnostic_only"] = True
    metadata["provisional_structural_connectors"] = (
        "two nominal left-center AB205 angles and shared bolts; other stations baseline ML24Z/SDS"
        if center_joint
        else "baseline ML24Z angles and SDS screws"
    )
    metadata["bolted_joint_demands"] = False
    metadata["acceptance"] = False
    metadata["kerf_panel_bounds"] = panel_bounds
    return structure, metadata


def prepare_case(case):
    """Build one unsolved case from the unchanged six-case definitions."""
    if case not in CASES:
        raise ValueError(f"Unknown unchanged load case: {case}")
    module = DiagnosticProxy()
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
    hold, force = CASES[case]
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
        member_contacts=face_contacts(module),
        clearance_monitors=taper_top_monitors(module),
    )
    report = {
        "case": case,
        "hold": hold,
        "horizontal_force_n": force,
        "candidate_raw": module.raw.KEY,
        "diagnostic_only": True,
        "provisional_structural_connectors": "baseline ML24Z angles and SDS screws",
        "bolted_joint_demands": False,
        "acceptance": False,
        "panel_connections": [c.name for c in module.panel_connections()],
        "panel_bounds": metadata["kerf_panel_bounds"],
        "prepared_candidate": metadata["candidate"],
    }
    return structure, report


def prepare_center_case(case, *, vertical_spring, steel_bolt_spring,
                        wood_bearing_lateral_n_per_mm, flange_contact_n_per_mm):
    """Prepare actual center bolt/angle topology with explicit provisional slip."""
    if case not in CASES:
        raise ValueError(f"Unknown unchanged load case: {case}")
    module = DiagnosticCenterBolted()
    joint = shared_center_joint(
        module,
        vertical_spring=vertical_spring,
        steel_bolt_spring=steel_bolt_spring,
        wood_bearing_lateral_n_per_mm=wood_bearing_lateral_n_per_mm,
        flange_contact_n_per_mm=flange_contact_n_per_mm,
    )
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
    hold, force = CASES[case]
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
        diagnostic_center_joint=joint,
        member_contacts=face_contacts(module),
        clearance_monitors=taper_top_monitors(module),
    )
    return structure, {
        "case": case,
        "candidate": module.KEY,
        "diagnostic_only": True,
        "provisional_structural_connectors": metadata[
            "provisional_structural_connectors"
        ],
        "center_joint": joint,
        "legacy_center_hardware_mass_surrogate": True,
        "bolted_joint_demands_qualified": False,
        "acceptance": False,
        "drilling_released": False,
        "panel_bounds": metadata["kerf_panel_bounds"],
        "connection_ownership": metadata["connection_ownership"],
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("case", choices=CASES)
    args = parser.parse_args()
    _, result = prepare_case(args.case)
    print(json.dumps(result, indent=2))
