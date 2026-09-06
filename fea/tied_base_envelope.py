"""Exact-inventory rigid-body comparison; ties receive no connection credit."""
import hashlib
import json
import math
from dataclasses import asdict
from pathlib import Path

from fea.user_load_envelope import envelope, hold_locations, hull
from mini_moonboard.stability import evaluate_load, load_cases, row_point

WEIGHTS_LB = (150, 200, 250, 300)
SUMMARIES = tuple(Path(f"exports/tied-base/z{height}/summary.json") for height in (100, 275))
OUTPUT = Path("fea/results/tied_base_envelope.json")
SOURCES = ("fea/tied_base_envelope.py", "fea/user_load_envelope.py", "mini_moonboard/stability.py")


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def checked_states(paths=SUMMARIES):
    """Use frozen CAD inventories, never substitute drilled/steel-angle mass."""
    reports, identities, sources = [], {}, {}
    for path, height in zip(paths, (100, 275), strict=True):
        report = json.loads(path.read_text())
        if report["height_mm"] != height or report["candidate"] != f"2x8-foot100-tied-base-z{height}":
            raise ValueError("Wrong published tied-base candidate")
        if "ALL NEW CONNECTIONS UNRESOLVED" not in report["status"]:
            raise ValueError("Unresolved connection basis missing")
        for source, expected in report["source_sha256"].items():
            if digest(Path(source)) != expected:
                raise ValueError(f"Published geometry source changed: {source}")
            if source in sources and sources[source] != expected:
                raise ValueError("Candidate source identities disagree")
            sources[source] = expected
        if not sources or "mini_moonboard/tied_base.py" not in report["source_sha256"]:
            raise ValueError("Missing geometry source identity")
        if set(report["artifact_sha256"]) != {"candidate.step"}:
            raise ValueError("Missing candidate STEP identity")
        for name, expected in report["artifact_sha256"].items():
            artifact = path.parent/name
            if digest(artifact) != expected:
                raise ValueError("Published STEP changed")
            identities[str(artifact)] = expected
        identities[str(path)] = digest(path)
        for name in ("baseline", "candidate_state"):
            state = report[name]
            centre, mass, volume = state["centre_mm"], state["mass_kg"], state["volume_mm3"]
            if len(centre) != 3 or not all(map(math.isfinite, (*centre, mass, volume))) or min(mass, volume) <= 0:
                raise ValueError("Finite positive inventory and three-coordinate centroid required")
            if not math.isclose(mass, volume*600/1e9, rel_tol=1e-12):
                raise ValueError("Inventory differs from timber-only comparison density")
            if hull(state["support_polygon_mm"]) != [tuple(p) for p in state["support_polygon_mm"]]:
                raise ValueError("Published floor hull is not canonical")
        if (report["density_kg_m3"] != 600 or report["baseline"]["part_count"] != 45
                or report["candidate_state"]["part_count"] != 49
                or report["candidate_state"]["support_polygon_mm"] != report["baseline"]["support_polygon_mm"]):
            raise ValueError("Changed exact timber inventory or floor polygon")
        reports.append(report)
    if reports[0]["baseline"] != reports[1]["baseline"]:
        raise ValueError("Published reference inventories disagree")
    states = {"2x8-foot100-timber-only": reports[0]["baseline"]}
    states.update({report["candidate"]: report["candidate_state"] for report in reports})
    return states, identities, sources


def case_summary(cases):
    governing = min(cases, key=lambda row: math.inf if row["governing"]["factor"] is None else row["governing"]["factor"])
    return {"case_count": len(cases), "minimum_factor": governing["governing"]["factor"],
            "governing_inputs": {key: governing[key] for key in ("climber_lb", "weight_multiplier", "mass_scale", "hold_standoff_mm", "horizontal_n")},
            "governing_hold": governing["governing"]["hold"],
            "minimum_net_restoring_nmm": min(row["minimum_net_restoring_nmm"] for row in cases),
            "maximum_translational_friction_demand": max(row["translational_friction_demand"] for row in cases),
            "status_counts": {status: sum(row["status"] == status for row in cases) for status in sorted({row["status"] for row in cases})}}


def build_report(paths=SUMMARIES):
    states, identities, sources = checked_states(paths)
    sources.update({source: digest(Path(source)) for source in SOURCES})
    locations = hold_locations()
    report = {"status": "RIGID-BODY MOMENT SCREEN ONLY; NO CONNECTION, CONTACT OR STRUCTURAL ACCEPTANCE",
              "assumptions": "Exact published undrilled timber at600kg/m3; excludes angles/fasteners/holds/glue/LEDs. New rails/spacers counted only as mass and centroid, not as verified ties or extra floor support. Whole-body rigid assembly is conditional on unresolved connections. One climber250lb intended maximum,150/200 comparisons,300 sensitivity, not ratings. Static/2x force,80/100% uniform mass with fixed CG,0/50/100mm hold offsets,0/300N horizontal worst-case all azimuths. No anchors/pads/ballast; no joint slip, contact distribution, yaw, directional stiffness/strength, or friction safety factor. Six legacy sagittal vectors at row12 retained separately, including exploratory normal directions.",
              "weights_lb": list(WEIGHTS_LB), "source_sha256": sources,
              "input_sha256": identities, "candidates": {}}
    for name, state in states.items():
        screen_state = dict(state, centre_xy_mm=state["centre_mm"][:2])
        cases = envelope(screen_state, locations, WEIGHTS_LB)
        legacy = []
        for load in load_cases():
            y, z = row_point(12)
            result = evaluate_load(mass_kg=state["mass_kg"], centre_y_mm=state["centre_mm"][1],
                                   kicker_toe_y_mm=min(p[1] for p in state["support_polygon_mm"]),
                                   leg_toe_y_mm=max(p[1] for p in state["support_polygon_mm"]),
                                   load_y_mm=y, load_z_mm=z, load=load)
            item = asdict(result)
            if not math.isfinite(item["overturning_factor"]):
                item["overturning_factor"] = None
            legacy.append(dict(item, status=result.status, load_y_mm=y, load_z_mm=z))
        report["candidates"][name] = {"state": state, "cases": cases, "summary": case_summary(cases),
                                     "by_weight_lb": {str(weight): case_summary([row for row in cases if row["climber_lb"] == weight]) for weight in WEIGHTS_LB},
                                     "legacy_row12_cases": legacy}
    return report


def publish(target=OUTPUT):
    if target.exists():
        raise ValueError("Existing envelope must not be overwritten")
    report = build_report()
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("x") as handle:
        handle.write(json.dumps(report, indent=2, allow_nan=False)+"\n")
    return report


if __name__ == "__main__":
    publish()
    print(OUTPUT)
