"""Test a placement-invariant opening requirement in the reviewed knee spines.

This is a necessary-condition test for zero perpendicular timber tension under
the recorded forces. It is not a fracture-capacity or revised host-bypass solve.
Parent owns execution; output must be a fresh ignored child.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
UPPER = HERE.parent
ROOT = next(p for p in HERE.parents if (p / "current-candidate.json").is_file())
CENSUS = HERE / "rawlocal/attempt01/receipt.json"
HELPER = UPPER / "remaining-block-transverse.py"
SPINES = UPPER / "rawlocal/knee-spine-net-sections/attempt02/checks.json"
PINS = {
    CENSUS: "1c037ed5f138cf738f4f4ca8628e377ef2ffbcf332419f496a5b03aab7d759b9",
    HELPER: "b7636729f666633feed74eb274968dc92b5d06620b4806ae697c79160869c9c8",
    SPINES: "6b6c8df94f1ccab859ee980dd1835ba19286718f44e8a36ce6b9d0014064fc85",
}
TOL = 1e-6


def require(condition, message):
    if not condition:
        raise ValueError("STOP: " + message)


def sha(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def read(path):
    return json.loads(Path(path).read_text())


def write(path, value):
    Path(path).write_text(json.dumps(value, indent=2, allow_nan=False) + "\n")


def load(path):
    spec = importlib.util.spec_from_file_location("spine_opening_helper", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def high_force(supports, forces, cut):
    """Sum complete supported fields, refusing a field intersected by the cut."""
    value = 0.0
    for (lo, hi), force in zip(supports, forces, strict=True):
        require(lo <= hi, "reversed support interval")
        require(hi < cut or lo > cut, "cut intersects a force support")
        if lo > cut:
            value += force
    return float(value)


def coupon():
    """Exact force and free-couple bookkeeping; no local stress claim."""
    supports = [(-12.0, -8.0), (8.0, 12.0)]
    required = high_force(supports, [-100.0, 100.0], 0.0)
    spread = high_force(
        [(-12.0, -10.0), (-10.0, -8.0), (8.0, 10.0), (10.0, 12.0)],
        [-40.0, -60.0, 30.0, 70.0],
        0.0,
    )
    require(required == spread == 100.0, "spread-field known answer differs")
    require(
        high_force(supports, [100.0, -100.0], 0.0) == -100.0,
        "compression sign known answer differs",
    )
    stopped = False
    try:
        high_force(supports, [-100.0, 100.0], 9.0)
    except ValueError:
        stopped = True
    require(stopped, "intersected support was accepted")
    points = np.array([[0.0, 0.0, -10.0], [3.0, 2.0, 10.0]])
    forces = np.array([[0.0, 0.0, -100.0], [0.0, 0.0, 100.0]])
    free = np.array([[1.0, 2.0, 3.0], [-4.0, 5.0, -6.0]])
    wrench = np.r_[forces.sum(0), (np.cross(points, forces) + free).sum(0)]
    require(
        np.array_equal(wrench, [0.0, 0.0, 0.0, 197.0, -293.0, -3.0]),
        "free-couple known answer differs",
    )
    return {
        "known_answers_satisfied": True,
        "opening_n": required,
        "spread_opening_n": spread,
        "intersected_support_rejected": stopped,
        "full_wrench_with_free_couples_n_nmm": wrench.tolist(),
    }


def build(output):
    output = Path(output).resolve()
    raw = HERE / "rawlocal/spine-opening"
    require(
        output.is_relative_to(raw) and output != raw and not output.exists(),
        "fresh owned raw child required",
    )
    pins = dict(PINS)
    for path, digest in pins.items():
        require(sha(path) == digest, "changed direct source: " + str(path))
    for relative, digest in read(CENSUS)["source_sha256"].items():
        path = ROOT / relative
        require(path not in pins or pins[path] == digest, "conflicting source pin")
        pins[path] = digest
    for path, digest in pins.items():
        require(sha(path) == digest, "changed inherited source: " + str(path))
    helper = load(HELPER)
    for path, digest in helper.PINS.items():
        require(pins.get(path) == digest, "helper source not census-bound")
    physical, long = (helper.module(p) for p in (helper.PHYSICAL, helper.LONG))
    members = read(helper.MEMBERS / "geometry.json")["members"]
    adapter, masses, current, contacts = (
        read(p) for p in (helper.ADAPTER, helper.MASS, helper.CURRENT, helper.CONTACTS)
    )
    register = read(UPPER / "rawlocal/working-joint-register/attempt03/register.json")
    require(len(register["axes"]) == 104, "reviewed axis authority differs")
    factor = read(UPPER / "frame-250-attempt02/comparison.json")["dead_load_factor"]
    states = []
    with np.load(
        helper.MEMBERS / "action-section-arrays.npz", allow_pickle=False
    ) as arrays:
        for body, geom in sorted(read(SPINES)["geometry"].items()):
            member = members[body]
            own = helper.prepare_body(
                body,
                geom,
                member,
                adapter,
                masses,
                current,
                contacts,
                physical,
                long,
                factor,
            )
            bores = helper.cylinders(geom)
            require(
                len(bores) == 4 and all(b["shaft"] == 1 for b in bores),
                "spine is not the reviewed four-u-bore body",
            )
            ordered = sorted(bores, key=lambda b: b["center"][2])
            gap = [
                ordered[-2]["center"][2] + ordered[-2]["radius"],
                ordered[-1]["center"][2] - ordered[-1]["radius"],
            ]
            require(gap[1] > gap[0] + TOL, "no cut clear of complete bore supports")
            cut = sum(gap) / 2
            supports = [
                [b["center"][2] - b["radius"], b["center"][2] + b["radius"]]
                for b in bores
            ]
            points = arrays[body + "__point_xyz_mm"]
            local = (points - own["start"]) @ own["frame"].T
            roles = member["point_action_roles"]
            gravity = np.array(roles) == "discrete_body_load"
            require(
                np.array_equal(gravity, arrays[body + "__point_rows"] == -1),
                "gravity row ownership differs",
            )
            require(
                abs(own["body_force"][2]) < TOL
                and max(abs(own["hardware"][1][:, 2])) < TOL,
                "physical gravity has normal-v force",
            )
            for case in helper.CASES:
                values = arrays[f"{case}__{body}__point_force_free_couple_xyz"]
                f = values[:, :3] @ own["frame"].T
                bore_forces = np.zeros(4)
                for index, role in enumerate(roles):
                    if role == "candidate_bolt_lateral_plane":
                        matches = [
                            i
                            for i, b in enumerate(bores)
                            if max(
                                abs(
                                    local[index, [0, 2]]
                                    - np.asarray(b["center"])[[0, 2]]
                                )
                            )
                            < TOL
                        ]
                        require(
                            len(matches) == 1, "lateral point not bound to one bore"
                        )
                        bore_forces[matches[0]] += f[index, 2]
                    elif role in (
                        "physical_bolt_outer_seat_tension",
                        "timber_or_panel_contact",
                    ):
                        require(
                            abs(f[index, 2]) < TOL,
                            "non-bore normal-v action needs another physical field",
                        )
                    else:
                        require(role == "discrete_body_load", "unhandled source role")
                mechanical = helper.action_prepared(
                    physical,
                    points[~gravity],
                    values[~gravity],
                    own["frame"],
                    own["start"],
                )
                old_gravity = helper.action_prepared(
                    physical,
                    points[gravity],
                    values[gravity],
                    own["frame"],
                    own["start"],
                )
                require(
                    max(abs(own["full_gravity"] - old_gravity[1].sum(0))) < TOL,
                    "physical gravity changes complete force/free-couple wrench",
                )
                volume, first = own["volume_function"](geom, 2, cut)
                timber = np.r_[
                    volume * own["body_force"],
                    np.cross(
                        np.asarray(first) - [0, 0, cut * volume], own["body_force"]
                    ),
                ]
                applied = physical.point_gravity(mechanical, 2, cut, "before")
                hw = physical.point_gravity(own["hardware"], 2, cut, "before")
                point_cut = -applied - timber - hw
                signed = high_force(supports, bore_forces, cut)
                require(
                    abs(point_cut[2] - signed) < TOL,
                    "two half-body normal balances disagree",
                )
                states.append(
                    {
                        "body": body,
                        "case_id": case,
                        "normal_v_cut_mm": cut,
                        "clear_cut_interval_mm": gap,
                        "bore_v_supports_mm": supports,
                        "signed_bore_v_resultants_n": bore_forces.tolist(),
                        "signed_required_normal_resultant_n": signed,
                        "minimum_required_timber_tension_n": max(0.0, signed),
                        "zero_perpendicular_tension_necessary_condition_pass": signed
                        <= TOL,
                        "original_point_signed_full_cut_n_nmm": point_cut[
                            [2, 0, 1, 5, 3, 4]
                        ].tolist(),
                        "full_cut_placement_scope": "Original mechanical points/free couples and physical gravity; only N is placement-invariant here.",
                        "full_body_residual_n_nmm": (
                            mechanical[1].sum(0) + own["full_gravity"]
                        ).tolist(),
                    }
                )
    require(len(states) == 12, "expected both spines and all six cases")
    known = coupon()
    result = {
        "schema": "reviewed-spine-supported-opening-test/v1",
        "known_answer": known,
        "states": states,
        "failed_zero_tension_states": sum(
            not s["zero_perpendicular_tension_necessary_condition_pass"] for s in states
        ),
        "maximum_required_timber_tension_n": max(
            s["minimum_required_timber_tension_n"] for s in states
        ),
        "recorded_perpendicular_tension_resistance_n": None,
        "splitting_resistance_established": False,
        "complete_joint_acceptance": False,
        "reviewed_geometry_changed": False,
        "proposal_adopted": False,
        "native_CAD_or_frame_run": False,
        "physical_release": False,
    }
    digest = sha(__file__)
    for path, expected in pins.items():
        require(sha(path) == expected, "source changed during execution: " + str(path))
    output.mkdir(parents=True)
    (output / ".gitignore").write_text("*\n!.gitignore\n")
    (output / "producer.py.snapshot").write_bytes(Path(__file__).read_bytes())
    write(output / "checks.json", result)
    require(sha(__file__) == digest, "producer changed during execution")
    write(
        output / "receipt.json",
        {
            "producer_sha256": digest,
            "source_sha256": {
                str(p.relative_to(ROOT)) if p.is_relative_to(ROOT) else str(p): d
                for p, d in sorted(pins.items())
            },
            "output_sha256": {
                n: sha(output / n) for n in ("producer.py.snapshot", "checks.json")
            },
        },
    )
    print(
        json.dumps(
            {
                "states": 12,
                "failed_zero_tension_states": result["failed_zero_tension_states"],
                "maximum_required_timber_tension_n": result[
                    "maximum_required_timber_tension_n"
                ],
            }
        )
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    build(parser.parse_args().output)
