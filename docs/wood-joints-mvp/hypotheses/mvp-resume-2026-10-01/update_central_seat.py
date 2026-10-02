"""Reuse the supported central ring with current six-joint simultaneous ties."""

import argparse
import json
import math
from pathlib import Path

import numpy as np
import top_corner_actions as accounting

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
GEOMETRY = HERE / "partial-seat-footprint-attempt02/result.json"
FRAME = HERE / "all-outer-corner-frame-attempt01"
ROWS = HERE / "corner-frame-attempt01/row-identities.json"
sha, read, require = accounting.sha, accounting.read, accounting.require


def run(output):
    require(not output.exists(), "preserve existing central-seat evidence")
    require(
        sha(GEOMETRY)
        == "ffba33b640e3ae00e61049664a603cdb6fe27cf7561f0068a735878ed8e3bf1b",
        "central geometry changed",
    )
    geometry, frame, rows = read(GEOMETRY), read(FRAME / "comparison.json"), read(ROWS)
    require(len(frame["states"]) == 12, "incomplete frame")
    require(
        all(
            s["status"] == "PASS_CONDITIONAL_COUPLED_FRAME_LAWS"
            for s in frame["states"]
        ),
        "failed source state",
    )
    matches = [
        r for r in rows if r["row_id"] == geometry["axis_id"] + "/outer-seat-axial-tie"
    ]
    require(len(matches) == 1 and matches[0]["row"] == 1535, "axial identity changed")
    require(
        all(
            abs(p["supported_fraction"] - 1) < 1e-6 for p in geometry["geometry_probes"]
        ),
        "central ring lacks saved full support",
    )
    pins = {ROOT / p: h for p, h in geometry["source_sha256"].items()}
    pins.update({ROOT / p: h for p, h in frame["source_sha256"].items()})
    pins.update(
        {
            GEOMETRY: sha(GEOMETRY),
            ROWS: sha(ROWS),
            FRAME / "comparison.json": sha(FRAME / "comparison.json"),
            FRAME / "response.npz": frame["response_sha256"],
            Path(__file__): sha(Path(__file__)),
        }
    )
    for path, digest in pins.items():
        require(sha(path) == digest, "changed source: " + str(path))
    area, fc = (
        geometry["central_area_mm2"],
        geometry["conditional_base_Fc_perpendicular_mpa"],
    )
    inner = geometry["declared_outer_inner_diameters_mm"][1] / 2
    states = []
    with np.load(FRAME / "response.npz", allow_pickle=False) as response:
        for source in frame["states"]:
            if source["gap_scale"] != 1:
                continue
            tension = float(response[source["case_id"] + "_gap_raw_force_n"][1535])
            states.append(
                {
                    "case_id": source["case_id"],
                    "signed_tie_n": tension,
                    "central_mean_pressure_mpa": max(tension, 0) / area,
                    "central_mean_pressure_over_Fc_perp": max(tension, 0) / (area * fc),
                    "minimum_equal_area_outer_circle_diameter_mm": 2
                    * math.sqrt(inner**2 + max(tension, 0) / (math.pi * fc)),
                }
            )
    require(len(states) == 6, "six current nominal states required")
    for path, digest in pins.items():
        require(sha(path) == digest, "source changed during calculation")
    report = {
        "schema": "current_partial_seat_supported_central_footprint/v1",
        "source_sha256": {str(p.relative_to(ROOT)): h for p, h in pins.items()},
        "source_geometry_sha256": sha(GEOMETRY),
        "axis_id": geometry["axis_id"],
        "body": geometry["body"],
        "seat_point_mm": geometry["seat_point_mm"],
        "declared_outer_inner_diameters_mm": geometry[
            "declared_outer_inner_diameters_mm"
        ],
        "central_area_mm2": area,
        "geometry_probes_reused": geometry["geometry_probes"],
        "conditional_base_Fc_perpendicular_mpa": fc,
        "states": states,
        "limits": geometry["limits"],
        "reviewed_geometry_changed": False,
        "hardware_selected": False,
        "complete_joint_acceptance": False,
        "physical_release": False,
        "producer_sha256": sha(Path(__file__)),
    }
    output.mkdir()
    (output / "result.json").write_text(
        json.dumps(report, indent=2, allow_nan=False) + "\n"
    )
    (output / "producer.py.snapshot").write_bytes(Path(__file__).read_bytes())
    print(json.dumps(max(states, key=lambda s: s["signed_tie_n"]), indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    run(parser.parse_args().output)
