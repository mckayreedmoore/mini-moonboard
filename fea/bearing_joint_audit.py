"""Current leg-bolt dimensional stacks and unresolved hardware, not capacity."""
import hashlib
import json
import math
from itertools import pairwise
from pathlib import Path

from mini_moonboard.selected_hardware import BoltSpec

OUTPUT = Path("fea/results/bearing-joints/report.json")
LENGTH_UNDER_TOLERANCE_MM = 2.54
ASSUMPTIONS = [
    "Dimensional inspection only: no bolt/wood resistance, load rating or construction approval.",
    "Leg bolts use the selected Conquest 3/8-16 dimensional family and maximum selected nut/washer envelopes.",
    "2.54 mm underlength is the documented project screening assumption for bolts over 4 through 6 inches; actual product tolerance remains to be confirmed.",
    "Actual CAD receiver grip is nominal stock geometry; moisture, compression and manufacturing grip variation are not included.",
    "Two pitches of tip projection do not prove two complete threads or full nut engagement: delivered chamfer, runout and thread length require inspection.",
    "The 25.4 mm reference thread length is not a bound for delivered 5.5-inch bolts; threaded wood-bearing length is a reference estimate only.",
    "No washer bending/bearing, plywood splitting, independent-ply sharing, bolt-group distribution, clamp friction or glue capacity is assigned.",
]


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def bolt_stack(length_mm, grip_mm, underlength_mm=LENGTH_UNDER_TOLERANCE_MM):
    """Maximum hardware stack at nominal grip; not a complete tolerance stack."""
    values = (length_mm, grip_mm, underlength_mm)
    if not all(math.isfinite(v) for v in values) or min(length_mm, grip_mm) <= 0 or underlength_mm < 0:
        raise ValueError("Require positive finite length/grip and nonnegative underlength")
    spec = BoltSpec("Conquest-family inspection", length_mm, grip_mm, underlength_mm)
    washer = spec.washer_thickness_max_mm
    nut = spec.nut_height_max_mm
    projection = length_mm-grip_mm-2*washer-nut
    minimum_projection = projection-underlength_mm
    target = 2*spec.pitch_mm
    # Under-head start is the washer's outer face; wood begins after washer 1.
    wood_start, wood_end = washer, washer+grip_mm
    thread_start = max(0., length_mm-spec.thread_length_reference_mm)
    reference_threaded_wood = max(0., wood_end-max(wood_start, thread_start))
    return {
        "length_mm": length_mm, "nominal_grip_mm": grip_mm,
        "assumed_underlength_mm": underlength_mm,
        "washer_max_thickness_mm": washer, "washer_count": 2,
        "nut_max_height_mm": nut, "pitch_mm": spec.pitch_mm,
        "projection_at_nominal_length_max_hardware_mm": projection,
        "projection_with_assumed_underlength_mm": minimum_projection,
        "two_pitch_target_mm": target,
        "remaining_grip_growth_allowance_mm": minimum_projection-target,
        "dimensional_projection_screen_pass": minimum_projection >= target,
        "reference_thread_length_mm": spec.thread_length_reference_mm,
        "reference_threaded_wood_bearing_length_mm": reference_threaded_wood,
        "thread_configuration_qualified": False,
        "connection_strength_qualified": False,
    }


def inventory(connections):
    """Explicit known provisional families, not a heuristic product classifier."""
    leg = [c for c in connections if c.name.startswith("analysis_leg_wall_bolt_")]
    unresolved = [c for c in connections if c.name.startswith(("wood_kicker_block_", "easy_lower_corner_"))]
    if (len(leg) != 8 or len(unresolved) != 12
            or len({c.name for c in (*leg, *unresolved)}) != 20):
        raise ValueError("Expected eight leg-wall bolts and twelve provisional kicker/corner screws")
    if any(c.kind != "bolt" or not math.isclose(c.diameter, 9.525) for c in leg):
        raise ValueError("Leg-wall bolt family changed")
    if any(c.kind != "screw" or "PROVISIONAL" not in c.product_status for c in unresolved):
        raise ValueError("Provisional screw disposition changed; review the inventory")
    return leg, [{"connection": c.name, "members": list(c.members),
                  "length_mm": c.length, "diameter_mm": c.diameter,
                  "product_status": c.product_status} for c in unresolved]


def validate_receiver_grip(intervals, nominal_grip, head_washer):
    """Require four real, contiguous receiver runs, not summed overlapping stock."""
    if len(intervals) != 4 or any(len(rows) != 1 for rows in intervals.values()):
        raise ValueError("Unexpected leg joint receiver topology")
    ordered = sorted(interval for rows in intervals.values() for interval in rows)
    if any(len(row) != 2 or not all(math.isfinite(v) for v in row) or row[1] <= row[0]
           for row in ordered):
        raise ValueError("Invalid receiver material interval")
    actual_grip = sum(end-start for start, end in ordered)
    if (not math.isclose(actual_grip, nominal_grip, abs_tol=1e-6)
            or not math.isclose(ordered[0][0], head_washer, abs_tol=1e-6)
            or any(not math.isclose(a[1], z[0], abs_tol=1e-6) for a, z in pairwise(ordered))):
        raise ValueError("Nominal grip does not equal contiguous actual receiver material")
    return actual_grip


def main():
    if OUTPUT.exists():
        raise FileExistsError(f"Refusing to overwrite frozen evidence: {OUTPUT}")
    # Keep numeric regression checks free from expensive CAD construction.
    from mini_moonboard import bearing_frame as frame
    from mini_moonboard.connection_geometry import material_intervals

    manifest_path = Path("exports")/frame.KEY/"manifest.json"
    manifest = json.loads(manifest_path.read_text())
    if manifest["design"]["key"] != frame.KEY:
        raise ValueError("Wrong candidate manifest")
    sources = dict(manifest["sources"])
    if not sources or any(digest(path) != sha for path, sha in sources.items()):
        raise ValueError("Published CAD sources differ from current inputs")
    sources.update({name: digest(name) for name in (
        "fea/bearing_joint_audit.py", "mini_moonboard/selected_hardware.py",
        "mini_moonboard/connection_geometry.py")})
    sources[str(manifest_path)] = digest(manifest_path)
    if not sources or any(digest(path) != sha for path, sha in sources.items()):
        raise ValueError("Published sources differ from current inputs")
    raw = {p.name: p for p in frame.parts(False)}
    leg, unresolved = inventory(frame.connections())
    records = []
    for c in leg:
        stack = bolt_stack(c.length, c.grip)
        intervals = {name: material_intervals(raw[name].shape, c.start, c.direction, 0., c.length)
                     for name in c.members}
        actual_grip = validate_receiver_grip(intervals, c.grip, stack["washer_max_thickness_mm"])
        records.append({"connection": c.name, "members": list(c.members),
                        "receiver_intervals_from_under_head_mm": intervals,
                        "actual_raw_receiver_grip_mm": actual_grip, **stack})
    report = {"candidate": frame.KEY, "scope": "Leg-bolt dimensional screen and provisional hardware inventory only",
              "assumptions": ASSUMPTIONS, "leg_bolt_count": len(records), "leg_bolts": records,
              "unselected_kicker_corner_screw_count": len(unresolved),
              "unselected_kicker_corner_screws": unresolved, "source_sha256": sources}
    if any(digest(path) != sha for path, sha in sources.items()):
        raise ValueError("Source changed during audit")
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT.open("x") as stream:
        stream.write(json.dumps(report, indent=2, allow_nan=False)+"\n")
    print(OUTPUT)


if __name__ == "__main__":
    main()
