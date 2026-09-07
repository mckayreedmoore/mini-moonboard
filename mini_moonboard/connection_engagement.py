"""Axial material audit of the top-joint candidate; no resistance calculation."""
import argparse
import hashlib
import json
from pathlib import Path

from . import product_frame, top_joint_frame
from .connection_geometry import material_intervals
from .selected_hardware import BoltSpec, spec_for


def covered_length(intervals, lower, upper):
    return sum(max(0., min(end, upper)-max(start, lower)) for start, end in intervals)


def report():
    raw = {p.name: p for p in top_joint_frame.parts(False)}
    rows = []
    for c in top_joint_frame.connections():
        spec = spec_for(c)
        row = {"connection": c.name, "product": spec.product, "kind": c.kind}
        if isinstance(spec, BoltSpec):
            projection = (spec.length_mm-spec.length_under_tolerance_mm-spec.grip_mm
                          -2*spec.washer_thickness_max_mm-spec.nut_height_max_mm)
            row.update(grip_nominal_mm=spec.grip_mm,
                       tip_projection_catalog_stack_mm=projection,
                       two_pitch_reference_mm=2*spec.pitch_mm,
                       stock_tolerance_included=False,
                       complete_exposed_threads_verified=False)
        else:
            receiver = c.members[-1]
            # All current final screw receivers are backing wood, not face
            # sheets. Face hold/LED bores would need separate reconstruction.
            if receiver.startswith(("main_", "clip_", "angle_", "transition_")) or receiver in ("kicker_left", "kicker_right"):
                raise ValueError(f"Unsupported final screw receiver: {receiver}")
            # Restore only service reliefs, never the screw's own pilot. Raw
            # geometry already retains the predecessor's wire chases/profiles.
            shape = product_frame._backing_reliefs(raw[receiver])
            extent = (shape.Center()-c.start).Length+shape.BoundingBox().DiagonalLength+1
            intervals = material_intervals(shape, c.start, c.direction, 0., extent)
            scenarios = []
            for length in sorted({spec.length_screen_min_mm, spec.length_screen_max_mm}):
                for thread in sorted({spec.thread_length_screen_min_mm, spec.thread_length_screen_max_mm}):
                    scenarios.append({"length_mm": length, "thread_tail_mm": thread,
                        "axial_material_in_thread_tail_including_point_mm":
                            covered_length(intervals, length-thread, length)})
            nominal_tail = covered_length(intervals, spec.length_nominal_mm-spec.thread_length_nominal_mm,
                                          spec.length_nominal_mm)
            containing_tip = [end-spec.length_nominal_mm for start, end in intervals
                              if start <= spec.length_nominal_mm <= end]
            row.update(receiver=receiver, axis_material_intervals_mm=intervals,
                       nominal_axis_material_in_thread_tail_including_point_mm=nominal_tail,
                       nominal_tip_inside_receiver=bool(containing_tip),
                       nominal_axial_cover_beyond_tip_mm=min(containing_tip) if containing_tip else None,
                       product_generation_endpoint_scenarios=scenarios,
                       point_exclusion_mm=None, effective_threaded_embedment_mm=None)
        rows.append(row)
    return {"variant": top_joint_frame.KEY, "qualified_for_design": False,
            "scope": "Axial centerline material, not full thread-circumference bearing. Screw point included; effective embedment unresolved. Bolt projection uses nominal grip and catalog stack only, not measured stock or thread chamfer.",
            "connections": rows}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    manifest = json.loads(Path("exports/top-joint-development/manifest.json").read_text())
    sources = dict(manifest["sources"])
    for name in ("connection_geometry", "connection_engagement"):
        path = Path("mini_moonboard")/(name+".py")
        sources[str(path)] = hashlib.sha256(path.read_bytes()).hexdigest()
    def verify_sources():
        for path, digest in sources.items():
            if hashlib.sha256(Path(path).read_bytes()).hexdigest() != digest:
                raise RuntimeError(f"Source changed or differs from exported candidate: {path}")
    verify_sources()
    result = report()
    verify_sources()
    result["sources"] = sources
    args.output.write_text(json.dumps(result, indent=2, allow_nan=False)+"\n")


if __name__ == "__main__":
    main()
