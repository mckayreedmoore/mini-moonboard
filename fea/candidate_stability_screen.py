"""Reproduce the timber-only spacing comparison; no solver or file exports."""
import json
import math

from fea.physical_footprint import evaluate
from fea.tied_base_envelope import case_summary
from mini_moonboard import spacing_frame, tied_base
from mini_moonboard.box_exports import exact_bounds


def build_report():
    inventories = {
        "2x8-foot100-undrilled-timber-only": tied_base.baseline(),
        "screw-spacing-development-drilled-timber-only": tuple(
            p for p in spacing_frame.parts(True)
            if not p.name.startswith(("angle_", "fastener_"))),
    }
    report = {}
    for name, parts in inventories.items():
        state = tied_base.state(parts)
        result = evaluate(dict(state, centre_xy_mm=state["centre_mm"][:2]))
        floor = []
        for part in parts:
            faces = [f for f in part.shape.Faces()
                     if abs(exact_bounds(f).zmin) < 1e-5
                     and abs(exact_bounds(f).zmax) < 1e-5]
            if faces:
                floor.append({"part": part.name, "area_mm2": sum(f.Area() for f in faces)})
        summaries = {"all": case_summary(result["cases"])}
        summaries.update({str(weight): case_summary([
            c for c in result["cases"] if c["climber_lb"] == weight])
            for weight in (150, 200, 250, 300)})
        for summary in summaries.values():
            del summary["maximum_translational_friction_demand"]
        legacy = [{k: v for k, v in row.items() if k != "friction_required"}
                  for row in result["legacy_2d_cases"]]
        report[name] = {"state": state, "floor_contacts": floor,
                        "summaries": summaries, "legacy_row12_cases": legacy}
    return report


def check(report):
    """Frozen comparison regression; a geometry change requires fresh review."""
    baseline, candidate = report.values()
    assert baseline["state"]["part_count"] == 45
    assert candidate["state"]["part_count"] == 47
    assert baseline["state"]["support_polygon_mm"] == candidate["state"]["support_polygon_mm"]
    legs = [p for p in candidate["floor_contacts"] if p["part"].startswith("leg_")]
    assert {p["part"] for p in legs} == {
        f"leg_{side}_{layer}" for side in ("left", "right") for layer in ("inner", "outer")}
    assert all(math.isclose(p["area_mm2"], 3670.2881245686, abs_tol=1e-5) for p in legs)
    for row, mass, factor in ((baseline, 183.96328718899005, 1.714267100607188),
                              (candidate, 194.1001889545372, 1.8121326819440706)):
        assert math.isclose(row["state"]["mass_kg"], mass, abs_tol=1e-6)
        assert math.isclose(row["summaries"]["all"]["minimum_factor"], factor, abs_tol=1e-8)
        assert row["summaries"]["all"]["case_count"] == 96
        assert row["summaries"]["all"]["status_counts"] == {"MEETS MOMENT SCREEN ONLY": 96}
        assert len(row["legacy_row12_cases"]) == 6
        assert [c["name"] for c in row["legacy_row12_cases"] if c["status"] == "UPLIFT"] == [
            "Outward/downward normal", "Inward/upward normal"]


if __name__ == "__main__":
    report = build_report()
    check(report)
    print(json.dumps(report, indent=2, allow_nan=False))
