"""Rank barrel-joint investigation using old angle actions only.

The barrel layout changes geometry and stiffness. These six historical ML24Z
flange actions are *not* transferred as its force demands or capacities.
"""

import hashlib
import json
import math
from pathlib import Path

from scripts.simple_owner_duty_ledger import selected_duties

SOURCE = (
    Path(__file__).resolve().parents[1] / "docs/floor-runner-mvp-angle-demands.json"
)
SOURCE_ID = "owner-barrel-legacy-demand-priority-v1"


def _norm3(values, label):
    if len(values) != 3 or not all(math.isfinite(float(value)) for value in values):
        raise ValueError(f"{label}: invalid three-dimensional vector")
    return math.sqrt(sum(float(value) ** 2 for value in values))


def _reported(record, field, label):
    vector_key = "force_xyz_n" if field == "force_norm_n" else "moment_xyz_nmm"
    computed = _norm3(record[vector_key], label)
    reported = float(record[field])
    if not math.isfinite(reported) or not math.isclose(
        computed, reported, rel_tol=1e-8, abs_tol=1e-6
    ):
        raise ValueError(f"{label}: reported {field.replace('_', ' ')} changed")
    return reported


def analyze(payload=None):
    """Aggregate six selected-baseline cases, with explicit non-transfer flags."""
    source_bytes = SOURCE.read_bytes() if payload is None else None
    payload = json.loads(source_bytes) if payload is None else payload
    duties = selected_duties()
    order = payload.get("case_order")
    cases = payload.get("cases", {})
    if (
        payload.get("candidate") != "compact-floor-flush-development"
        or payload.get("status") != "AUDITED_ANGLE_DEMAND_LEDGER_ONLY"
        or payload.get("construction_release") is not False
        or payload.get("connection_resistance_established") is not False
        or not isinstance(order, list)
        or len(order) != 6
        or len(set(order)) != 6
        or set(cases) != set(order)
        or len(duties) != 24
    ):
        raise ValueError("Historical angle-demand source boundary changed")
    families = {
        family: {
            "stations": sorted(
                name for name, duty in duties.items() if duty["family"] == family
            )
        }
        for family in sorted({duty["family"] for duty in duties.values()})
    }
    station_cases = flange_cases = 0
    for case in order:
        angles = cases[case].get("angles", {})
        if set(angles) != set(duties):
            raise ValueError(f"{case}: station set changed")
        for station, angle in angles.items():
            station_cases += 1
            family = duties[station]["family"]
            flanges = angle.get("flanges", {})
            if set(flanges) != {"beam", "upright"}:
                raise ValueError(f"{case}/{station}: flange set changed")
            for flange, record in flanges.items():
                flange_cases += 1
                label = f"{case}/{station}/{flange}"
                for field, output_key in (
                    ("force_norm_n", "max_force_n"),
                    ("moment_norm_nmm", "max_moment_nmm"),
                ):
                    value = _reported(record, field, label)
                    prior = families[family].get(output_key)
                    if prior is None or value > prior["value"]:
                        families[family][output_key] = {
                            "value": round(value, 6),
                            "case": case,
                            "station": station,
                            "flange": flange,
                        }
    if station_cases != 144 or flange_cases != 288 or len(families) != 12:
        raise ValueError("Historical flange-case inventory changed")
    return {
        "source_id": SOURCE_ID,
        "source_path": str(SOURCE.relative_to(SOURCE.parents[1])),
        "source_sha256": hashlib.sha256(source_bytes).hexdigest()
        if source_bytes is not None
        else None,
        "source_candidate": payload["candidate"],
        "inventory": {
            "cases": len(order),
            "stations": len(duties),
            "station_case_records": station_cases,
            "flange_case_records": flange_cases,
            "families": len(families),
        },
        "families": families,
        "force_priority": sorted(
            families,
            key=lambda family: families[family]["max_force_n"]["value"],
            reverse=True,
        ),
        "moment_priority": sorted(
            families,
            key=lambda family: families[family]["max_moment_nmm"]["value"],
            reverse=True,
        ),
        "interpretation": (
            "Historical ML24Z station-flange force/moment magnitudes only. "
            "Independent extrema may occur in different cases; the barrel "
            "topology needs new mechanics, contact and joint-force solves."
        ),
        "new_barrel_joint_forces_solved": False,
        "historical_actions_adopted_for_barrel_design": False,
        "drilling_released": False,
        "fabrication_released": False,
        "structural_released": False,
    }


if __name__ == "__main__":
    print(json.dumps(analyze(), indent=2, sort_keys=True))
