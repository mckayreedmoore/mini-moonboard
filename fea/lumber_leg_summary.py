"""Separate conditional maxima, with their own governing case identities."""
import argparse
import hashlib
import json
import math
import tarfile
from pathlib import Path


def summarize(path):
    with tarfile.open(path) as archive:
        report = json.load(archive.extractfile("report.json"))
        for name, sha in report["artifact_sha256"].items():
            if hashlib.sha256(archive.extractfile(name).read()).hexdigest() != sha:
                raise ValueError("Native evidence hash differs")
    if not report["passed"] or set(report["runs"]) != {"k100", "k1000", "k10000"}:
        raise ValueError("Require all three accepted native stiffness runs")
    result = []
    for stiffness, run in report["runs"].items():
        rows = run["scenarios"]
        if len(rows) != 216:
            raise ValueError("Require the complete established scenario set")
        for weight in (150, 200, 250, 300):
            selected = [r for r in rows if r["climber_lb"] == weight]
            if len(selected) != 54:
                raise ValueError("Incomplete climber comparison cases")
            def identity(row):
                return {k: row[k] for k in ("hold", "weight_factor", "horizontal_direction_deg", "force_n")}
            hold = max(selected, key=lambda r: r["loaded_displacement_magnitude_mm"])
            values = [(row, name, force) for row in selected
                      for name, force in row["leg_connector_force_on_leg_n"].items()]
            peaks = {}
            for key, measure in (("resultant_n", lambda f: math.hypot(*f)),
                                 ("lateral_n", lambda f: math.hypot(f[1], f[2])),
                                 ("axial_n", lambda f: abs(f[0]))):
                row, name, vector = max(values, key=lambda v: measure(v[2]))
                peaks[key] = {"value": measure(vector), "bolt": name,
                              "simultaneous_force_xyz_n": vector, "case": identity(row)}
            result.append({"stiffness": stiffness, "climber_lb": weight,
                "peak_loaded_hold_displacement_mm": hold["loaded_displacement_magnitude_mm"],
                "displacement_case": identity(hold), "bolt_peaks": peaks})
    return {"archive": str(path), "archive_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            "qualified_for_design": False, "rows": result,
            "limits": "Separate maxima, not a simultaneous combined load. Conditional fixed-floor, "
                      "uncalibrated connector and isotropic-material trial, not physical limits or approval."}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("archive", type=Path)
    print(json.dumps(summarize(parser.parse_args().archive), indent=2, allow_nan=False))
