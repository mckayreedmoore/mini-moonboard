"""Support-envelope sensitivity only: no altered CAD or new FEA claim."""
import hashlib
import json
import math
from pathlib import Path

from mini_moonboard.stability import evaluate_load, load_cases, row_point

SOURCE = Path("fea/results/hybrid/2x12/stability.json")
OPTIONS = (("current", 0, 0), ("leg +150", 0, 150),
           ("leg +300", 0, 300), ("both +300", 300, 300),
           ("both +600", 600, 600))


def toe_threshold(mass, centre, y, z, load, target):
    """Required interval point T: a <= T <= b, for W-target*Fz > 0.

    This rearranges both dead-restoring/live-overturning inequalities. It is
    not a physical foot location or a required structural member dimension.
    """
    values = (mass, centre, y, z, load.force_y_n, load.force_z_n, target)
    if not all(math.isfinite(v) for v in values) or mass <= 0 or z < 0 or target < 1:
        raise ValueError("finite inputs, positive mass, nonnegative height and target >=1 required")
    weight = mass*9.80665
    denominator = weight-target*load.force_z_n
    if denominator <= 0:
        raise ValueError("threshold formula requires W-target*Fz > 0")
    return (weight*centre-target*y*load.force_z_n+target*z*load.force_y_n)/denominator


def sweep(source, kicker_extension, leg_extension):
    """Freeze mass/centroid; shift extreme support toes, not foot centres."""
    if any(not math.isfinite(v) or v < 0 for v in (kicker_extension, leg_extension)):
        raise ValueError("extensions must be finite and nonnegative")
    results = []
    for load in load_cases():
        samples = []
        for row in range(1, 13):
            y, z = row_point(row)
            case = evaluate_load(mass_kg=source["mass_kg"],
                centre_y_mm=source["centre_y_mm"],
                kicker_toe_y_mm=source["kicker_toe_y_mm"]-kicker_extension,
                leg_toe_y_mm=source["leg_toe_y_mm"]+leg_extension,
                load_y_mm=y, load_z_mm=z, load=load)
            samples.append((row, case))
        row, worst = min(samples, key=lambda item: item[1].overturning_factor)
        results.append({"case": load.name, "basis": load.basis,
            "force_y_n": load.force_y_n, "force_z_n": load.force_z_n,
            "governing_row": row,
            "minimum_factor": worst.overturning_factor if math.isfinite(worst.overturning_factor) else None,
            "minimum_kicker_reaction_n": min(c.kicker_reaction_n for _, c in samples),
            "minimum_leg_reaction_n": min(c.leg_reaction_n for _, c in samples),
            "friction_required_all_rows": None if any(c.friction_required is None for _, c in samples)
                else max(c.friction_required for _, c in samples),
            "status": worst.status})
    return results


def report():
    source = json.loads(SOURCE.read_text())
    options = [{"name": name, "kicker_extension_mm": a, "leg_extension_mm": b,
        "support_span_mm": source["leg_toe_y_mm"]-source["kicker_toe_y_mm"]+a+b,
        "cases": sweep(source, a, b)} for name, a, b in OPTIONS]
    thresholds = []
    for target in (1.0, 1.5):
        for load in load_cases():
            points = [toe_threshold(source["mass_kg"], source["centre_y_mm"],
                *row_point(row), load, target) for row in range(1, 13)]
            thresholds.append({"case": load.name, "target": target,
                "maximum_kicker_toe_y_mm": min(points), "minimum_leg_toe_y_mm": max(points),
                "kicker_extension_mm": max(0, source["kicker_toe_y_mm"]-min(points)),
                "leg_extension_mm": max(0, max(points)-source["leg_toe_y_mm"])})
    return {"source": str(SOURCE), "source_sha256": hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
        "mass_kg": source["mass_kg"], "centre_y_mm": source["centre_y_mm"],
        "assumptions": "Frozen 2x12 mass/centroid; massless rigid support extensions. All 12 main rows; no hold stand-off. Not changed leg CAD, joint analysis, lateral stability, contact FEA or build approval. No friction coefficient assumed.",
        "options": options, "thresholds": thresholds}


if __name__ == "__main__":
    target = Path("fea/results/hybrid/footprint_sensitivity.json")
    target.write_text(json.dumps(report(), indent=2, allow_nan=False)+"\n")
    print(target)
