"""Reuse the frozen frame with continuous shafts and finished floor footprints.

One assembly serves all unchanged load-case parameters. The published geometry
and existing material/spring laws remain explicit conditional inputs; this
driver replaces independent bolt ports with physical shaft bearing/capture.
"""

from __future__ import annotations

import argparse
import copy
import sys
from pathlib import Path
from unittest.mock import patch

from scripts import run_thin_bolted_finished_floor as finished
from scripts import thin_bolted_common_shaft as shafts
from scripts import thin_bolted_frame_mechanics as frame

METHOD_BASIS = "continuous-circular-shafts-distributed-own-bore-bearing-axial-end-capture"
COMMON_TABLES = (
    "common_shaft_bearing_actions", "shaft_end_capture_actions",
    "common_shaft_wood_bearing_actions", "common_shaft_steel_port_actions",
    "common_shaft_element_actions", "common_shaft_section_cut_actions",
)


class UnsolvedCommonState(Exception):
    """Retain a failed response without inventing coefficients or force rows."""

    def __init__(self, report):
        super().__init__(report["response"].get("termination", "no coefficient field"))
        self.report = report


def case_with_shaft_gravity(case: dict, system) -> dict:
    """Remap each physical shaft once, before all recovery and load assembly."""
    if "shaft_metal_gravity_remap_residual_n_nmm" in case:
        raise ValueError("physical shaft gravity was already remapped")
    replacement = system.remap_bolt_gravity(case)
    case.clear()
    case.update(replacement)
    return case


def bind_common_metadata(report: dict, system, pins: dict, command: list[str]) -> dict:
    """Keep the new force paths distinct from the former paired-point arrows."""
    if report.get("attachment_actions") or report.get("retained_bolt_actions"):
        raise ValueError("old independent bolt actions must not survive a shaft state")
    report["schema"] = "thin_bolted_common_shaft_frame/v1"
    report["disposition"] = "CONDITIONAL_COMMON_SHAFT_ELASTIC_SURROGATE"
    unused = {}
    for key in ("bolt_axial_lateral_stiffness_n_mm", "relative_bolt_radial_clearance_mm"):
        if key in report["parameters"]:
            unused[key] = report["parameters"].pop(key)
    report["inactive_legacy_bolt_port_parameters"] = unused
    report["parameters"].update(system.parameters)
    report["parameters"]["bolt_connection_method"] = METHOD_BASIS
    report["parameters"]["own_bore_clearance_basis"] = "half the nominal bore minus nominal shaft major diameter; independent on each host"
    report["common_shaft_method_sources"] = copy.deepcopy(shafts.METHOD_SOURCES)
    report["source_sha256"].update(pins)
    state_fields = {key: report[key] for key in ("state_id", "case_id", "accessory_placement")}
    # Finished-floor binding runs afterward and changes every shared ID once.
    for table in COMMON_TABLES:
        for row in report.get(table, []):
            row.update(state_fields)
            for nested in row.get("cuts", []) + row.get("elements", []):
                nested.update(state_fields)
    counts = report["counts"]
    counts.pop("bolt_interfaces", None)
    counts.update({"physical_shaft_bodies": 70, "structural_bodies": 132,
                   "finished_wood_bearing_spans": 82, "steel_bore_spans": 72,
                   "radial_bearing_quadrature_ports": len(system.bearing_groups),
                   "own_axial_end_captures": len(system.end_captures),
                   "independent_lumped_frame_bolt_ports": 0})
    obsolete = ("Retained two-timber bolt axial capture/compression", "Fourteen shared shafts use two independent")
    report["limits"] = [limit for limit in report["limits"] if not limit.startswith(obsolete)]
    report["limits"].extend([
        "All seventy shafts use circular beam fields; each own bore has a separate radial-clearance spring scenario. Local three-dimensional bearing pressure and physical stiffness bounds are not established.",
        "Own end captures act at washer pressure planes in axial compression only. Washer bending, pressure, prying and delivered seating remain unresolved; no frictional or rotational clamp is credited.",
        "Metal-role gravity moves to its own shaft assembly with exact mass/centroid and global wrench conservation; panel/screw/T-nut sources are retained.",
        "Timber, shaft, fitting and plate kinematics remain first order. Objective finite-motion method coupons do not qualify this state without applicable integration or error evidence.",
    ])
    report["common_shaft_execution"] = {
        "command": command, "connection_method": METHOD_BASIS,
        "geometry_rebuilt": False, "new_physical_shaft_load_path": True,
        "frozen_writer_and_frame_producer_preserved": True,
        "reused_spring_constitutive_law": True,
        "shaft_body_ids": list(system.shafts),
        "independent_132_body_audit_required": True,
        "physical_demand_bounds_established": False,
    }
    return report


def main() -> None:
    full_arguments = sys.argv[1:]
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--shaft-E", type=float, default=200000.)
    parser.add_argument("--shaft-nu", type=float, default=.3)
    parser.add_argument("--shaft-diameter-scale", type=float, default=1.)
    parser.add_argument("--wood-bearing-foundation", type=float, default=1000. / 38.1)
    parser.add_argument("--steel-bearing-foundation", type=float, default=10000. / 5.55625)
    parser.add_argument("--end-capture-stiffness", type=float, default=1000.)
    parser.add_argument("--shaft-segment", type=float, default=25.)
    custom, remainder = parser.parse_known_args(full_arguments)
    inputs = shafts.read_inputs()
    pins = shafts.source_pins()
    driver = Path(__file__)
    driver_sha = frame.sha(driver)
    pins[str(driver.relative_to(frame.ROOT))] = driver_sha
    command = [sys.executable, "-m", "scripts.run_thin_bolted_common_shaft_frame", *full_arguments]
    original_assembly = frame.ElasticAssembly
    original_load = frame.coupled_load_vector
    original_connections = frame.elastic_connections
    original_evaluate = frame.evaluate_elastic
    prepared = {}

    def assembly(*args, **kwargs):
        if prepared:
            raise ValueError("the serialization wrapper must reuse its one prepared assembly")
        actual = original_assembly(*args, **kwargs)
        prepared["system"] = shafts.CommonShaftSystem(
            actual, inputs, steel_E_mpa=custom.shaft_E, steel_nu=custom.shaft_nu,
            diameter_scale=custom.shaft_diameter_scale,
            wood_foundation_n_mm2=custom.wood_bearing_foundation,
            plate_foundation_n_mm2=custom.steel_bearing_foundation,
            end_capture_n_mm=custom.end_capture_stiffness, max_segment_mm=custom.shaft_segment)
        return actual

    def load(actual, case, integrated):
        case_with_shaft_gravity(case, prepared["system"])
        prepared["last_case"] = copy.deepcopy(case)
        return original_load(actual, case, integrated)

    def connections(*args, **kwargs):
        groups, contacts, tangents = original_connections(*args, **kwargs)
        groups = [g for g in groups if g["kind"] not in {"fitting_bolt", "retained_bolt"}]
        system = prepared["system"]
        return [*groups, *system.bearing_groups], [*contacts, *system.end_captures], tangents

    def actions(actual, case, response, groups, contacts, tangents):
        if actual is not prepared["system"].assembly:
            raise ValueError("response assembly differs from common-shaft preparation")
        return prepared["system"].compatible_actions(case, response, groups, contacts, tangents)

    def evaluate(*args, **kwargs):
        report = original_evaluate(*args, **kwargs)
        if shafts.source_pins() != {key: value for key, value in pins.items() if key != str(driver.relative_to(frame.ROOT))}:
            raise ValueError("common-shaft source identities changed")
        if frame.sha(driver) != driver_sha:
            raise ValueError("common-shaft driver changed during evaluation")
        report = bind_common_metadata(report, prepared["system"], pins, command)
        if "q" not in report["response"]:
            report["body_applied_loads"] = copy.deepcopy(prepared["last_case"]["loads"])
            report["body_identities"] = [r["id"] for r in prepared["system"].assembly.geo["bodies"]]
            raise UnsolvedCommonState(report)
        return report

    old_argv = copy.copy(sys.argv)
    try:
        sys.argv = [old_argv[0], *remainder]
        with (patch.object(frame, "ElasticAssembly", assembly),
              patch.object(frame, "coupled_load_vector", load),
              patch.object(frame, "elastic_connections", connections),
              patch.object(frame, "elastic_actions", actions),
              patch.object(frame, "evaluate_elastic", evaluate)):
            finished.main()
    except UnsolvedCommonState as failure:
        # The frozen serialization wrapper requires a solved q. Preserve an
        # unsolved experiment separately instead of manufacturing that field.
        _, proof, floor_pins = finished.read_finished_footprints()
        report = finished.bind_finished_state(failure.report, proof, floor_pins,
                                              frame.sha(Path(finished.__file__)))
        report["failed_response_without_recovered_actions"] = True
        output_parser = argparse.ArgumentParser(add_help=False)
        output_parser.add_argument("--out", type=Path)
        output_parser.add_argument("--out-dir", type=Path)
        output, _ = output_parser.parse_known_args(remainder)
        path = output.out or output.out_dir / f"compatible-frame-{report['case_id']}-v4.json"
        with path.open("x") as stream:
            stream.write(finished.writer.dump(report))
        print(finished.writer.dump({"case": report["case_id"], "output": str(path),
                                   "response_converged": False,
                                   "usable_conditional_actions": False,
                                   "failure": report["response"]}), flush=True)
    finally:
        sys.argv = old_argv


if __name__ == "__main__":
    main()
