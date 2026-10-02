"""Bind retained washer diameters to six saved simultaneous force states.

Pressure is an ideal full-support comparison. Actual seat support and washer
metal resistance remain unresolved; no quarter-inch dimensions are reused.
"""

import argparse
import ast
import csv
import hashlib
import json
import math
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
SOURCE = HERE / "remaining-joint-screen-attempt04/all-two-receiver-92ksi"
REGISTER = Path("/tmp/mini-moonboard-retained-frame-bolt-current-resistance-basis-2026-10-01.json")
FEATURES = HERE.parent / "current-finished-feature-register-2026-10-01/axis-features.json"
HARDWARE = HERE / "assembly-package/hardware_engagement.py"
FIXED = {
    SOURCE / "screen.json": "5b85139b2acaefd8ff74df916229766438c0caf3bc9c3a1a7b5080f8f393033a",
    REGISTER: "c3250f067c4590ee43f7ec7a5765d056d87e6ff5adb42837ed27710d9b4d4eb1",
    FEATURES: "bebb4274cdecfb6ad0b0f26850d85a16570c245ea9f7d478c0b05c12b4513e19",
    HARDWARE: "d8e2a08e46fd9507a89d8e7ecb238ddf229490f4909345cbb641374ee8133295",
}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def main(output):
    output = output.resolve()
    require(output.parent == HERE and output.name.startswith("retained-washer-attempt")
            and not output.exists(), "use a fresh retained-washer-attempt directory")
    for path, digest in FIXED.items():
        require(sha(path) == digest, "changed input: " + str(path))
    report = json.loads((SOURCE / "screen.json").read_text())
    csv_path = SOURCE / "bolt-states.csv"
    require(sha(csv_path) == report["output_sha256"][csv_path.name], "force CSV changed")
    register = json.loads(REGISTER.read_text())["axis_register"]
    features = {r["axis_id"]: r for r in json.loads(FEATURES.read_text())
                ["source_axis_groups"]["retained_frame_bolt_axes"]["axes"]}
    stacks = next(ast.literal_eval(node.value) for node in ast.parse(HARDWARE.read_text()).body
                  if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "STACKS" for t in node.targets))
    with csv_path.open(newline="") as stream:
        forces = [r for r in csv.DictReader(stream) if r["kind"] == "retained_bolt"]
    require(len(forces) == 72 and len({r["axis_id"] for r in forces}) == 12, "incomplete retained force coverage")
    pins = {str(p): h for p, h in FIXED.items()}
    for path in (csv_path, Path(__file__)):
        pins[str(path)] = sha(path)
    seats, states = {}, []
    for force in forces:
        axis = force["axis_id"]
        entry, geometry = register[axis], features[axis]
        diameter = entry["hardware_policy"]["nominal_diameter_in"] * 25.4
        family = "three8" if math.isclose(diameter, 9.525) else "half"
        require(math.isclose(diameter, stacks[family]["diameter_mm"]), "unsupported diameter family")
        washer = stacks[family]["washer"]
        od, inner = min(washer["outside_diameter_mm"]), max(washer["inside_diameter_mm"])
        axis_dir = geometry["source_axis_fields"]["direction_global_xyz"]
        ordered = sorted(entry["finished_receivers"], key=lambda r: r["interval_from_axis_datum_mm"][0])
        for role, receiver in zip(("head", "nut"), ordered, strict=True):
            member = receiver["member"]
            membership = next(r for r in geometry["receiver_memberships"] if r["receiver_member_id"] == member)
            patches = [r for r in membership["cylinder_surface_candidates"] if r["association_status"] == "eligible_bore_patch"]
            require(patches, "no bound bore diameter")
            bore = max(2 * r["cylinder_radius_mm"] for r in patches)
            require(abs(sum(a * b for a, b in zip(axis_dir, receiver["stock_frame"]["basis_columns_global_xyz"][0], strict=True))) < 1e-6,
                    "washer force is not perpendicular to declared grain")
            path = ROOT / receiver["finished_step"]["path"]
            require(sha(path) == receiver["finished_step"]["file_sha256"], "receiver STEP changed")
            pins[str(path)] = receiver["finished_step"]["file_sha256"]
            opening = max(bore, inner)
            require(od > opening, "washer has no ideal bearing annulus")
            area = math.pi * (od**2 - opening**2) / 4
            seat_id = axis + "/" + role
            seat = {"seat_id": seat_id, "axis_id": axis, "role": role, "member": member,
                    "washer_part": washer["part"], "minimum_od_mm": od,
                    "maximum_id_mm": inner, "minimum_thickness_mm": min(washer["thickness_mm"]),
                    "bound_bore_diameter_mm": bore, "unsupported_center_diameter_mm": opening,
                    "ideal_full_support_area_mm2": area, "actual_full_seat_support": None,
                    "actual_supported_area_mm2": None, "washer_yield_mpa": None}
            if seat_id in seats:
                require(seats[seat_id] == seat, "seat geometry changed across force states")
            seats[seat_id] = seat
            tension = float(force["outer_tie_signed_n"])
            require(tension >= -1e-8, "unexpected compressive tie")
            pressure = max(0.0, tension) / area
            states.append({"case_id": force["case_id"], "seat_id": seat_id,
                           "axis_id": axis, "role": role, "member": member,
                           "simultaneous_signed_tie_n": tension,
                           "hypothetical_uniform_full_support_pressure_mpa": pressure,
                           "hypothetical_pressure_over_conditional_fc_perp": pressure / report["wood_reference_mpa"]["Fc_perpendicular"],
                           "actual_pressure_mpa": None, "actual_wood_bearing_acceptance": None,
                           "washer_metal_acceptance": None})
    require(len(seats) == 24 and len(states) == 144, "incomplete washer coverage")
    for path, digest in pins.items():
        require(sha(Path(path)) == digest, "input changed during calculation: " + path)
    result = {"schema": "retained_washer_current_dimensional_reference/v1",
              "source_sha256": pins, "source_force_state_scope": report["source_force_state_scope"],
              "conditional_fc_perp_mpa": report["wood_reference_mpa"]["Fc_perpendicular"],
              "unique_seats": list(seats.values()), "states": states,
              "peak_ideal_state": max(states, key=lambda r: r["hypothetical_pressure_over_conditional_fc_perp"]),
              "limits": ["Actual full-seat support is not established by bound bore diameters or catalog washer dimensions.",
                         "Ideal full-support annulus uses minimum washer OD and maximum of catalog ID and saved bore diameter.",
                         "Pressure assumes concentric uniform compression without preload, eccentricity, tilt or bridging.",
                         "Washer numeric yield and head/nut bearing-face transfer remain unqualified; no metal resistance is assigned.",
                         "Catalog dimensions are conditional inputs, not delivered measurements or hardware selection."],
              "complete_joint_acceptance": False, "hardware_selected": False,
              "reviewed_geometry_changed": False, "physical_release": False}
    output.mkdir()
    (output / ".gitignore").write_text("*\n")
    (output / "retained_washer_checks.py.snapshot").write_bytes(Path(__file__).read_bytes())
    path = output / "checks.json"
    path.write_text(json.dumps(result, indent=2, allow_nan=False) + "\n")
    print(json.dumps({"output": str(path), "sha256": sha(path), "seats": len(seats),
                      "seat_states": len(states), "source_pins": len(pins),
                      "peak_ideal_state": result["peak_ideal_state"]}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    main(parser.parse_args().output)
