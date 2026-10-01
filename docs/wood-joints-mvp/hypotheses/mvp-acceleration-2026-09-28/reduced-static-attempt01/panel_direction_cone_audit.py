"""Read-only sign audit for the upper-panel no-axial-credit force cone.

This checks only the frozen recorded direction set. It does not solve an LP,
run a native solver, or assess a physical fastener, contact, or joint.
"""
from __future__ import annotations

from fractions import Fraction
import hashlib
import json
import math
from pathlib import Path


HERE = Path(__file__).resolve().parent
MODEL_PATH = HERE / "model-inputs.json"
GEOMETRY_PATH = HERE / "contact-geometry.json"
SCREEN_PATH = HERE / "panel-path-screen.json"
SCREEN_SCRIPT_PATH = HERE / "panel_path_screen.py"
PINNED_SHA256 = {
    "model-inputs.json": "178ab4f9352c8b1f11525ffc6680efa5733ba74cedd609874e9a1966624740f9",
    "contact-geometry.json": "034067430fff5207cdb40819fa8118a367edeb29a8d83926928cc96a0e87d151",
    "panel_path_screen.py": "6d2a6323fa7cfc10fc857be8da1011df65174754d15f12f99bb09c18f7d9cb30",
    "panel-path-screen.json": "80b7df4762981479c7f5c080d6207773cea1a2d6d4310f35280849b96400ec2c",
}
PANELS = ("main_upper_left", "main_upper_right")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def exact_dot(left: list[float], right: list[float]) -> Fraction:
    """Treat each serialized binary64 component as its exact rational value."""
    return sum(
        (Fraction.from_float(float(a)) * Fraction.from_float(float(b))
         for a, b in zip(left, right, strict=True)),
        Fraction(0),
    )


def main() -> None:
    paths = {
        "model-inputs.json": MODEL_PATH,
        "contact-geometry.json": GEOMETRY_PATH,
        "panel_path_screen.py": SCREEN_SCRIPT_PATH,
        "panel-path-screen.json": SCREEN_PATH,
    }
    for name, expected in PINNED_SHA256.items():
        observed = sha256(paths[name])
        if observed != expected:
            raise SystemExit(f"FAIL: source pin changed for {name}: {observed}")

    model = json.loads(MODEL_PATH.read_text())
    geometry = json.loads(GEOMETRY_PATH.read_text())
    screen = json.loads(SCREEN_PATH.read_text())
    if (model["candidate"], model["revision_id"]) != (
        "compact-floor-flush-wood-joints-development",
        "led-clearance-2x6-runner-seated-blocks-v1",
    ):
        raise SystemExit("FAIL: candidate or revision changed")
    if model["ready_for_six_case_response"] or model["mechanical_acceptance"] or model["native_solve_run"]:
        raise SystemExit("FAIL: source readiness/acceptance/run boundary changed")
    if screen["source_sha256"] != {
        name: PINNED_SHA256[name]
        for name in ("model-inputs.json", "contact-geometry.json", "panel_path_screen.py")
    }:
        raise SystemExit("FAIL: saved screen does not bind the audited inputs")

    result = {
        "status": "PASS_RECORDED_DIRECTION_SET_SIGN_AUDIT",
        "candidate": model["candidate"],
        "revision_id": model["revision_id"],
        "source_sha256": PINNED_SHA256,
        "panels": {},
        "scope": (
            "Necessary force-equilibrium sign check for the recorded upper-panel "
            "direction set with lateral-only screws and compression-only contacts. "
            "The saved LP remains a floating-point tolerance screen. No compatible "
            "response, per-screw share, strength, or physical acceptance is inferred."
        ),
        "native_solver_run": False,
        "mechanical_acceptance": False,
    }

    for panel in PANELS:
        screws = [
            row for row in model["connections"]
            if row["kind"] == "panel_screw"
            and row["source_record"]["panel_member"] == panel
        ]
        axes = {tuple(float(value) for value in row["axis_xyz"]) for row in screws}
        if len(screws) != 12 or len(axes) != 1:
            raise SystemExit(f"FAIL: expected 12 co-directed screw axes for {panel}")
        axis = list(next(iter(axes)))
        c40, s40 = math.cos(math.radians(40.0)), math.sin(math.radians(40.0))
        if not (
            axis[0] == 0.0
            and axis[1] < 0.0
            and axis[2] > 0.0
            and abs(axis[1] + c40) <= 2e-16
            and abs(axis[2] - s40) <= 2e-16
        ):
            raise SystemExit(f"FAIL: {panel} screw axis is no longer the source 40-degree direction")

        # u points outward, opposite the screw axis. A lateral-only screw law
        # defines each permitted screw force as perpendicular to this axis.
        outward = [-component for component in axis]
        contact_projections: list[Fraction] = []
        contact_count = 0
        for patch in geometry["contact_patches"]:
            if panel not in patch["member_ids"]:
                continue
            panel_index = patch["member_ids"].index(panel)
            normal = [float(value) for value in patch["normal_on_first_xyz"]]
            # Compression acts as -normal_on_first on the first body and
            # +normal_on_first on the second body.
            reaction = [-value for value in normal] if panel_index == 0 else normal
            projection = exact_dot(outward, reaction)
            if projection < 0:
                raise SystemExit(f"FAIL: inward compression projection for {panel}: {patch['member_ids']}")
            contact_projections.append(projection)
            contact_count += 1
        if contact_count != 7:
            raise SystemExit(f"FAIL: expected seven recorded contacts for {panel}, got {contact_count}")

        case_projections = {}
        for case in model["cases"]:
            body = next(
                row for row in case["body_external_wrenches"]
                if row["member_id"] == panel
            )
            projection = exact_dot(
                outward,
                [float(value) for value in body["assigned_external_force_xyz_n"]],
            )
            if projection <= 0:
                raise SystemExit(f"FAIL: nonpositive external outward force for {panel}/{case['case_id']}")
            case_projections[case["case_id"]] = float(projection)

        result["panels"][panel] = {
            "panel_screws": len(screws),
            "screw_axis_xyz": axis,
            "contact_patch_count": contact_count,
            "compression_projection_counts": {
                "positive": sum(value > 0 for value in contact_projections),
                "zero": sum(value == 0 for value in contact_projections),
                "negative": 0,
            },
            "minimum_positive_contact_projection": min(
                (float(value) for value in contact_projections if value > 0),
                default=None,
            ),
            "case_external_outward_force_n": case_projections,
        }

    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
