"""Calculate retained bolt-pair row geometry and declared group-factor scenarios.

This consumes saved nominal-gap forces. The four area combinations are
sensitivities, not an adopted factor for a group carrying oblique forces/couples.
"""

import argparse
import csv
import hashlib
import itertools
import json
import math
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
SOURCE = HERE / "remaining-joint-screen-attempt04/all-two-receiver-92ksi"
REGISTER = Path("/tmp/mini-moonboard-retained-frame-bolt-current-resistance-basis-2026-10-01.json")
CHAPTER = ROOT / "docs/wood-joints-mvp/hypotheses/upper-block-strength-2026-10-01/source-cache/chapter11-2024-awc-20260911.pdf"
REFERENCE_SHA = "5b85139b2acaefd8ff74df916229766438c0caf3bc9c3a1a7b5080f8f393033a"
REGISTER_SHA = "c3250f067c4590ee43f7ec7a5765d056d87e6ff5adb42837ed27710d9b4d4eb1"
E_PSI = 1_600_000.0


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def dot(a, b):
    return sum(x * y for x, y in zip(a, b, strict=True))


def norm(a):
    return math.sqrt(dot(a, a))


def sub(a, b):
    return [x - y for x, y in zip(a, b, strict=True)]


def cross(a, b):
    return [a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]]


def angle(a, b):
    length = norm(a) * norm(b)
    return None if length <= 1e-12 else math.degrees(math.acos(min(1.0, abs(dot(a, b)) / length)))


def group_factor(pitch_mm, diameter_in, main_area_in2, side_area_in2):
    """NDS 2024 Eq. 11.3-1 for a declared two-fastener wood-to-wood row."""
    ea, eb = E_PSI * main_area_in2, E_PSI * side_area_in2
    ratio = min(ea, eb) / max(ea, eb)
    gamma = 180_000 * diameter_in**1.5
    u = 1 + gamma * (pitch_mm / 25.4) / 2 * (1 / ea + 1 / eb)
    m = 1 / (u + math.sqrt(u * u - 1))
    value = m * (1 - m**4) / (2 * ((1 + ratio * m**2) * (1 + m) - 1 + m**4)) * (1 + ratio) / (1 - m)
    if not 0 < value <= 1 + 1e-9:
        raise ValueError("group factor outside its declared domain")
    return min(1.0, value)


def main(output):
    output = output.resolve()
    if output.parent != HERE or not output.name.startswith("retained-group-attempt") or output.exists():
        raise ValueError("use a fresh retained-group-attempt directory in this packet")
    report_path, csv_path = SOURCE / "screen.json", SOURCE / "bolt-states.csv"
    if sha(report_path) != REFERENCE_SHA or sha(REGISTER) != REGISTER_SHA:
        raise ValueError("saved force or receiver register changed")
    source = json.loads(report_path.read_text())
    if sha(csv_path) != source["output_sha256"]["bolt-states.csv"]:
        raise ValueError("saved force CSV differs from its report")
    register = json.loads(REGISTER.read_text())["axis_register"]
    with csv_path.open(newline="") as stream:
        records = [r for r in csv.DictReader(stream) if r["kind"] == "retained_bolt"]
    if len(records) != 72 or len({r["axis_id"] for r in records}) != 12:
        raise ValueError("expected twelve retained bolts across six nominal states")
    pins = {str(p): sha(p) for p in (report_path, csv_path, REGISTER, CHAPTER, Path(__file__))}
    grouped = defaultdict(list)
    for record in records:
        grouped[(record["duty_id"], record["case_id"])].append(record)
    groups, axis_states = [], []
    for (duty, case), pair in sorted(grouped.items()):
        pair.sort(key=lambda r: r["axis_id"])
        if len(pair) != 2:
            raise ValueError("retained duty does not contain exactly two bolts")
        points = [[float(r[f"point_{a}_mm"]) for a in "xyz"] for r in pair]
        delta = sub(points[1], points[0])
        pitch = norm(delta)
        row_unit = [x / pitch for x in delta]
        datum = [(a + b) / 2 for a, b in zip(*points, strict=True)]
        diameter = register[pair[0]["axis_id"]]["hardware_policy"]["nominal_diameter_in"]
        areas, receivers = [], []
        for receiver in register[pair[0]["axis_id"]]["finished_receivers"]:
            name, frame = receiver["member"], receiver["stock_frame"]
            for r in pair:
                other = next(x for x in register[r["axis_id"]]["finished_receivers"] if x["member"] == name)
                if other["stock_frame"] != frame:
                    raise ValueError("paired receiver stock frames differ")
                path = ROOT / other["finished_step"]["path"]
                if sha(path) != other["finished_step"]["file_sha256"]:
                    raise ValueError("receiver STEP changed")
                pins[str(path)] = sha(path)
            lengths = [next(x for x in register[r["axis_id"]]["finished_receivers"] if x["member"] == name)
                       ["interval_from_axis_datum_mm"] for r in pair]
            thickness = min(end - start for start, end in lengths)
            grain_pitch = abs(dot(delta, frame["basis_columns_global_xyz"][0]))
            gross = math.prod(frame["original_dimensions_gqr_mm"][1:]) / 25.4**2
            equivalent = thickness * grain_pitch / 25.4**2
            if min(gross, equivalent) <= 0:
                raise ValueError("declared equivalent area is not positive")
            areas.append({"gross": gross, "declared_perpendicular_width": equivalent})
            receivers.append({"member": name, "gross_area_in2": gross,
                              "minimum_saved_bearing_length_mm": thickness,
                              "pair_projection_on_grain_mm": grain_pitch,
                              "declared_equivalent_area_in2": equivalent})
        scenarios = [{"main_area_basis": first, "side_area_basis": second,
                      "factor": group_factor(pitch, diameter, areas[0][first], areas[1][second])}
                     for first, second in itertools.product(areas[0], areas[1])]
        factor = min(s["factor"] for s in scenarios)
        forces, total_forces = [], []
        for r in pair:
            force = [float(r[f"shear_{a}_n"]) for a in "xyz"]
            forces.append(force)
            tie_direction = json.loads(r["tie_direction_xyz"])
            tie = float(r["outer_tie_signed_n"])
            sign = 1 if r["tie_first_body"] == r["first_body"] else -1
            total_forces.append([f + sign * tie * d for f, d in zip(force, tie_direction, strict=True)])
            projection = abs(dot(delta, [x / norm(force) for x in force])) if norm(force) > 1e-12 else None
            transverse = math.sqrt(max(0.0, pitch**2 - projection**2)) if projection is not None else None
            axis_states.append({"case_id": case, "duty_id": duty, "axis_id": r["axis_id"],
                                "saved_shear_xyz_n": force, "saved_outer_tie_signed_n": tie,
                                "force_to_pair_line_deg": angle(force, row_unit),
                                "pair_spacing_parallel_to_this_force_mm": projection,
                                "pair_spacing_transverse_to_this_force_mm": transverse,
                                "quarter_spacing_proximity_trigger": None if projection is None else transverse < projection / 4,
                                "actual_oblique_group_Cg": None,
                                "minimum_declared_row_factor": factor,
                                "unadjusted_reference_ratio_92ksi": float(r["ratio_92ksi"]),
                                "ratio_divided_by_declared_factor": float(r["ratio_92ksi"]) / factor})
        resultant = [sum(f[i] for f in forces) for i in range(3)]
        moments = [cross(sub(point, datum), force) for point, force in zip(points, total_forces, strict=True)]
        groups.append({"duty_id": duty, "case_id": case, "axis_ids": [r["axis_id"] for r in pair],
                       "pitch_mm": pitch, "row_unit_xyz": row_unit, "diameter_in": diameter,
                       "receivers": receivers, "area_scenarios": scenarios,
                       "lateral_resultant_to_pair_line_deg": angle(resultant, row_unit),
                       "bolt_force_wrench_datum_mm": datum,
                       "bolt_force_wrench_n_nmm": [sum(f[i] for f in total_forces) for i in range(3)] +
                                                  [sum(m[i] for m in moments) for i in range(3)],
                       "wrench_scope": "Signed bolt shear and outer tie forces only; face contact, free couples and other joint actions are not included."})
    if len(groups) != 36:
        raise ValueError("expected six retained pairs across six nominal states")
    changed = [p for p, digest in pins.items() if sha(Path(p)) != digest]
    if changed:
        raise ValueError(f"inputs changed: {changed}")
    output.mkdir()
    (output / ".gitignore").write_text("*\n")
    (output / "producer.py.snapshot").write_bytes(Path(__file__).read_bytes())
    result = {"schema": "retained_bolt_group_sensitivity/v1", "source_sha256": pins,
              "source_force_state_scope": source["source_force_state_scope"],
              "counts": {"pairs": 6, "pair_states": 36, "axis_states": 72}, "E_psi": E_PSI,
              "groups": groups, "axis_states": axis_states,
              "peak": max(axis_states, key=lambda r: r["ratio_divided_by_declared_factor"]),
              "limits": ["The four gross/equivalent area combinations are row sensitivities, not a bound or adopted Cg for the actual oblique group.",
                         "The equivalent width is the saved pair projection on grain; no minimum spacing or finished-edge acceptance is inferred.",
                         "Per-force proximity flags describe geometry only; unequal force directions and couples remain explicit.",
                         "The NDS row load/slip modulus is used only in Eq.11.3-1, not as a replacement frame spring stiffness.",
                         "Only six saved nominal-gap states are consumed; other sources and physical fit are not included."],
              "frame_solve_run": False, "native_solve_run": False, "hardware_selected": False,
              "reviewed_geometry_changed": False, "complete_joint_acceptance": False, "physical_release": False}
    (output / "checks.json").write_text(json.dumps(result, indent=2, allow_nan=False) + "\n")
    print(json.dumps({"output": str(output), "sha256": sha(output / "checks.json"), "counts": result["counts"], "peak": result["peak"]}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    main(parser.parse_args().output)
