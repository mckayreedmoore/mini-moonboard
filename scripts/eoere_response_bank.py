"""Verify and index a frozen six-case bank without recomputing its response."""

from __future__ import annotations

import argparse
import importlib.metadata
import json
import platform
from pathlib import Path

from scripts.eoere_paired_frame_basis import CASES, ROOT, read, ref, sha

OWN = Path(__file__).resolve()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def summarize(readiness_path, readiness_sha256, public_path):
    readiness_path = Path(readiness_path).resolve()
    public_path = Path(public_path).resolve()
    require(
        readiness_path.is_relative_to(ROOT / "fea/generated"),
        "generated readiness required",
    )
    require(
        public_path.is_relative_to(ROOT / "docs/bolted-frame-development")
        and not public_path.exists(),
        "fresh public bank index required",
    )
    pins = {ref(OWN)["path"]: sha(OWN)}
    ready = read(readiness_path, pins, readiness_sha256)
    for name in (
        "receipt",
        "physical_geometry",
        "physical_clearance",
        "analysis_geometry",
        "material",
        "inputs",
        "method_readiness",
    ):
        read(ready[name]["path"], pins, ready[name]["sha256"])
    inputs = read(ready["inputs"]["path"], pins, ready["inputs"]["sha256"])
    require(
        inputs["geometry"] == ready["analysis_geometry"]
        and inputs["plywood_material"] == ready["material"],
        "own prepared geometry/material required",
    )
    require(
        ready["historical_force_pass_transferred"] is False
        and ready["complete_joint_or_frame_qualified"] is False,
        "conditional own-bank intake required",
    )
    require(
        ready["load_contract"]
        == {
            "weight_lb": 250,
            "downward_multiplier": 2,
            "horizontal_force_N": 300,
            "accessory_mass_kg": 25,
            "duration_factor_CD": 1,
        },
        "recorded load recipe required",
    )
    pins.update(ready["source_sha256"])
    rows = []
    for case in CASES:
        folder = readiness_path.parent / "four-hosts" / case
        references = {
            name: ref(folder / filename)
            for name, filename in (
                ("field", "field.json"),
                ("independent_replay", "independent-replay.json"),
                ("independent_plywood_replay", "independent-replay-plywood.json"),
            )
        }
        field = read(references["field"]["path"], pins, references["field"]["sha256"])
        replay = read(
            references["independent_replay"]["path"],
            pins,
            references["independent_replay"]["sha256"],
        )
        plywood = read(
            references["independent_plywood_replay"]["path"],
            pins,
            references["independent_plywood_replay"]["sha256"],
        )
        require(
            field["case_id"] == replay["case_id"] == case
            and replay["field"] == plywood["field"] == references["field"],
            "own case/replays required",
        )
        require(
            field["trial_parent_geometry"] == ready["analysis_geometry"]
            and field["source_inputs"]["geometry"] == ready["analysis_geometry"]
            and field["source_inputs"]["plywood_material"] == ready["material"],
            "current field intake required",
        )
        require(
            field["counts"]["physical_bodies"] == 148
            and field["counts"]["shaft"] == 96
            and len(field["panel_screw_actions"]) == 66,
            "current response census required",
        )
        require(
            replay["false_screw_and_floor_forces_rejected"]
            and replay["same_state_declared_fixed_floor_replayed"]
            and replay["all_credited_hosts_in_bearing"]
            and replay["equilibrium"]["physical_body_count"] == 148
            and replay["equilibrium"]["gradient_inf_n"] < 1e-5
            and len(plywood["raw_operator_checks"]) == 2,
            "unchanged independent admission gates required",
        )
        require(
            all(value is False for value in field["release"].values()),
            "no release follows from convergence",
        )
        for path, digest in field["source_sha256"].items():
            require(
                path not in pins or pins[path] == digest,
                "case source maps disagree: " + path,
            )
            pins[path] = digest
        rows.append(
            {
                "case_id": case,
                **references,
                "gradient_inf_N": replay["equilibrium"]["gradient_inf_n"],
                "physical_bodies": 148,
                "shafts": 96,
                "panels": 6,
                "Hillman_axes": 66,
                "both_independent_replays_admitted": True,
            }
        )
    for path, digest in pins.items():
        require(sha(path) == digest, "active bank source changed: " + path)
    record = {
        "schema": "eoere_own_response_bank/v1",
        "geometry_revision": json.loads((ROOT / ready["receipt"]["path"]).read_bytes())[
            "revision"
        ],
        "analysis_revision": ready["analysis_revision"],
        "physical_geometry": ready["receipt"],
        "physical_geometry_raw": ready["physical_geometry"],
        "analysis_geometry": ready["analysis_geometry"],
        "material": ready["material"],
        "inputs": ready["inputs"],
        "readiness": ref(readiness_path),
        "producer": ref(OWN),
        "load_contract": ready["load_contract"],
        "cases": rows,
        "all_six_cases_admitted": True,
        "maximum_gradient_inf_N": max(row["gradient_inf_N"] for row in rows),
        "admission_gate_N": 1e-5,
        "active_source_pins_reverified": len(pins),
        "versions": {
            "python": platform.python_version(),
            **{
                name: importlib.metadata.version(name)
                for name in ("cadquery", "numpy", "scipy")
            },
        },
        "nominal_metal_role_gravity": ready["metal_role_gravity"],
        "historical_force_pass_transferred": False,
        "physical_force_bounds_established": False,
        "complete_joint_or_frame_qualified": False,
        "structural_acceptance": False,
        "fabrication_released": False,
        "climbing_released": False,
        "qualification_limits": [
            "Numerical equilibrium and independent replay do not establish resistance or complete joint acceptance.",
            "Perfect bonding of two nominal19.05mm plywood leaves per corner, the139.7mm uniform beam approximation, generic panel/screw stiffness and four-host no-slip floor remain unqualified analytical scenarios.",
            "The raw physical geometry retains inherited provenance pins. Active response/input pins are checked here; this does not claim reconstruction of all historical geometry producers.",
            "Different hardware must receive an explicit input, gravity, seat and thread-window applicability review; no later-candidate force pass is implied.",
        ],
    }
    snapshot = readiness_path.parent / "checks/response-bank-v1"
    require(not snapshot.exists(), "fresh bank verification snapshot required")
    snapshot.mkdir(parents=True)
    (snapshot / "producer-snapshot.py").write_bytes(OWN.read_bytes())
    (snapshot / "active-source-pins.json").write_text(
        json.dumps(pins, indent=2, sort_keys=True) + "\n"
    )
    record["active_source_pin_record"] = ref(snapshot / "active-source-pins.json")
    with public_path.open("x") as stream:
        json.dump(record, stream, indent=2, sort_keys=True, allow_nan=False)
        stream.write("\n")
    return record


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--readiness", type=Path, required=True)
    parser.add_argument("--readiness-sha256", required=True)
    parser.add_argument("--public", type=Path, required=True)
    args = parser.parse_args()
    value = summarize(args.readiness, args.readiness_sha256, args.public)
    print(
        json.dumps(
            {
                "bank": ref(args.public),
                "cases": len(value["cases"]),
                "maximum_gradient_inf_N": value["maximum_gradient_inf_N"],
            }
        )
    )


if __name__ == "__main__":
    main()
