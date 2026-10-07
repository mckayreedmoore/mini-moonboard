"""Serialize frozen mechanics states and reuse unchanged prepared operators.

This wrapper changes no constitutive law. It fixes the frozen CLI's NumPy bool
export and retains panel coefficient identities for dependent calculations.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from unittest.mock import patch

import numpy as np

from scripts import thin_bolted_frame_mechanics as frame
from scripts import thin_bolted_panel_mechanics as panel_tools

FRAME_SHA = "05cdf6897645fe7ee1b72b5b5125c04c68d758108f4860f995cef6aa1b676448"


def json_scalar(value):
    """Preserve numerical values and booleans; reject unsupported objects."""
    if isinstance(value, np.generic):
        return value.item()
    if isinstance(value, np.ndarray):
        return value.tolist()
    raise TypeError(f"unsupported mechanics export type: {type(value).__name__}")


def dump(report: dict) -> str:
    return json.dumps(report, separators=(",", ":"), allow_nan=False, default=json_scalar) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cases", nargs="+", default=["a12-rear"])
    parser.add_argument("--accessory", default="retained-original-top-hold")
    parser.add_argument("--intervals", type=int, default=8)
    parser.add_argument("--beam-size", type=float, default=150.)
    parser.add_argument("--clearance", type=float, default=1.5875)
    parser.add_argument("--contact-edge", type=float, default=35.)
    parser.add_argument("--bolt-stiffness", type=float, default=1000.)
    parser.add_argument("--screw-stiffness", type=float, default=1000.)
    parser.add_argument("--fitting-section", choices=("gross", "net"), default="gross")
    parser.add_argument("--floor-tangent-stiffness", type=float, default=100000.)
    parser.add_argument("--out", type=Path)
    parser.add_argument("--out-dir", type=Path)
    args = parser.parse_args()
    if (args.out is None) == (args.out_dir is None) or (args.out and len(args.cases) != 1):
        parser.error("use --out for one case, or --out-dir for multiple cases")
    if len(set(args.cases)) != len(args.cases):
        parser.error("duplicate load cases")
    if frame.sha(Path(frame.__file__)) != FRAME_SHA or frame.LOADED_PRODUCER_SHA256 != FRAME_SHA:
        raise ValueError("preserve the frozen mechanics producer")
    driver_path = Path(__file__)
    driver_sha = frame.sha(driver_path)
    paths = [args.out] if args.out else [args.out_dir / f"compatible-frame-{case}-v4.json" for case in args.cases]
    if any(path.exists() for path in paths):
        raise FileExistsError("preserve prior mechanics states")
    if args.out_dir:
        args.out_dir.mkdir(parents=True, exist_ok=True)
    original_geometry, original_panels, original_assembly = frame.geometry, panel_tools.prepare_panel_models, frame.ElasticAssembly
    cache, counts = {}, {"geometry_preparations": 0, "panel_preparations": 0, "assembly_preparations": 0}

    def geometry(*inputs, **kwargs):
        if "geometry" not in cache:
            cache["geometry"] = original_geometry(*inputs, **kwargs)
            counts["geometry_preparations"] += 1
        return cache["geometry"]

    def panels(*inputs, **kwargs):
        if "panels" not in cache:
            cache["panels"] = original_panels(*inputs, **kwargs)
            counts["panel_preparations"] += 1
        return cache["panels"]

    def assembly(*inputs, **kwargs):
        if "assembly" not in cache:
            cache["assembly"] = original_assembly(*inputs, **kwargs)
            counts["assembly_preparations"] += 1
            cache["K_pin"] = hashlib.sha256(cache["assembly"].K.data.tobytes()).hexdigest()
        return cache["assembly"]

    with (patch.object(frame, "geometry", geometry),
          patch.object(panel_tools, "prepare_panel_models", panels),
          patch.object(frame, "ElasticAssembly", assembly)):
        for case, path in zip(args.cases, paths, strict=True):
            print(f"Calculating {case}; geometry and parameters stay frozen", flush=True)
            report = frame.evaluate_elastic(
                case_id=case, accessory=args.accessory, intervals=args.intervals,
                beam_size=args.beam_size, clearance=args.clearance, contact_edge=args.contact_edge,
                stiffness=args.bolt_stiffness, screw_stiffness=args.screw_stiffness,
                fitting_section=args.fitting_section, floor_tangent_stiffness=args.floor_tangent_stiffness)
            prepared = cache["assembly"]
            if hashlib.sha256(prepared.K.data.tobytes()).hexdigest() != cache["K_pin"]:
                raise ValueError("prepared material stiffness changed during evaluation")
            q = np.asarray(report["response"]["q"])
            report["panel_generalized_coefficients"] = {
                name: {"basis_order_per_direction": panel["basis"].order,
                       "width_mm": panel["basis"].width, "height_mm": panel["basis"].height,
                       "knots_normalized": panel["basis"].knots.tolist(),
                       "coefficient_order": "u,v,outward_w; x-major tensor cubic B-spline coefficients in mm",
                       "global_dof_start": int(prepared.panel_offsets[name][0]),
                       "coefficients_mm": q[prepared.panel_offsets[name]].tolist()}
                for name, panel in prepared.panels.items()}
            report["source_sha256"][str(driver_path.relative_to(frame.ROOT))] = driver_sha
            report["execution_wrapper"] = {
                "command": [sys.executable, "-m", "scripts.run_thin_bolted_mechanics", *sys.argv[1:]],
                "numpy_scalar_serialization_only": True, "constitutive_law_changed": False,
                "reused_preparation_counts": dict(counts), "material_operator_sha256": cache["K_pin"]}
            if frame.sha(driver_path) != driver_sha:
                raise ValueError("wrapper changed during evaluation")
            text = dump(report)
            with path.open("x") as stream:
                stream.write(text)
            print(json.dumps({"case": case, "output": str(path),
                              "usable_conditional_actions": report["usable_conditional_actions"],
                              "response_converged": report["response"]["converged"],
                              "gradient_inf_n": report["response"].get("gradient_inf_n"),
                              "maximum_panel_screw_withdrawal_n": report.get("maximum_panel_screw_withdrawal_n")}), flush=True)


if __name__ == "__main__":
    main()
